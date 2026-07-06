#!/usr/bin/env python3
"""ingestion/router.py — sources.yaml tier 라우팅 + 폴백 체인.

사용법:
    python ingestion/router.py --dry-run              # 실제 수집 없이 경로만 출력
    python ingestion/router.py --source imf_blog      # 특정 소스만
    python ingestion/router.py --tier 1               # 특정 tier만
    python ingestion/router.py --sector ai_semis      # 특정 섹터만
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 — `python3 ingestion/router.py` 직접 실행 지원
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import yaml

ROOT = Path(__file__).resolve().parent.parent

# ── sources.yaml 로드 ─────────────────────────────────────────────────────────

def load_sources(yaml_path: Path | None = None) -> list[dict]:
    path = yaml_path or ROOT / "ingestion" / "sources.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    defaults = data.get("defaults", {})
    sources = []
    for s in data.get("sources", []):
        merged = {**defaults, **s}
        sources.append(merged)
    return sources


def filter_sources(
    sources: list[dict],
    source_id: str | None = None,
    tier: int | None = None,
    sector: str | None = None,
    active_only: bool = True,
) -> list[dict]:
    result = sources
    if active_only:
        result = [s for s in result if s.get("active", True)]
    if source_id:
        result = [s for s in result if s["id"] == source_id]
    if tier is not None:
        result = [s for s in result if s.get("tier") == tier]
    if sector:
        result = [s for s in result if sector in s.get("sector_tags", [])]
    return result


# ── raw_source 저장 ────────────────────────────────────────────────────────────

def _save_raw_source(article: dict, blob_url: str = "") -> str | None:
    """raw_sources + sources(pending) 동시 INSERT. 중복이면 skip, 성공 시 UUID 반환."""
    from ingestion.dedupe import normalize_url, content_hash, is_duplicate
    from ingestion.db import db_conn

    url = article["url"]
    url_norm = normalize_url(url)
    raw_text = article.get("raw_text", "")
    hash_val = content_hash(raw_text or url)

    if is_duplicate(url_norm, hash_val):
        print(f"  → skip (중복): {url[:80]}")
        return None

    blob = blob_url or article.get("blob_url", "")
    issuer = article.get("issuer", "")
    published_at = article.get("published_at", "")
    title = article.get("title", "")
    content_text = article.get("content_text", raw_text or "")
    sector_tags = article.get("sector_tags", [])

    with db_conn() as conn:
        with conn.cursor() as cur:
            # Stage 1: raw_sources 저장
            cur.execute(
                """
                INSERT INTO raw_sources
                  (url, url_normalized, content_hash, raw_content, blob_url,
                   source_yaml_id, issuer, fetched_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
                """,
                (
                    url, url_norm, hash_val,
                    (raw_text or "")[:8000],
                    blob,
                    article.get("source_yaml_id", ""),
                    issuer,
                ),
            )
            row = cur.fetchone()
            if not row:
                return None
            raw_id = str(row["id"])

            # Stage 2: sources 승격 — issuer + published_at + title 필수 (Hard Rule)
            if issuer and published_at and title:
                cur.execute(
                    """
                    INSERT INTO sources
                      (raw_source_id, title, url, issuer, published_at,
                       sector_tags, content_text, blob_url, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        raw_id, title, url, issuer, published_at,
                        sector_tags,
                        content_text[:50000],
                        blob,
                    ),
                )
            else:
                missing = [f for f in ("issuer","published_at","title") if not article.get(f)]
                print(f"  [WARN] sources 승격 거부 (누락: {missing}): {url[:60]}")

            return raw_id


# ── 채널별 수집 ───────────────────────────────────────────────────────────────

def _run_rss(source: dict, dry_run: bool, limit: int | None = None) -> int:
    from ingestion.channels import rss
    articles = rss.fetch(source, max_items=limit or 20)
    if dry_run:
        for a in articles:
            print(f"  [DRY] {a['title'][:60]} ({a['published_at']})")
        return len(articles)
    saved = 0
    for a in articles:
        raw_id = _save_raw_source(a)
        if raw_id:
            saved += 1
    return saved


def _run_scraper(source: dict, dry_run: bool, limit: int | None = None) -> int:
    from ingestion.channels.scrapers import SCRAPER_REGISTRY
    from ingestion.blob import upload, make_blob_filename

    scraper_cls = SCRAPER_REGISTRY.get(source["id"])
    if not scraper_cls:
        print(f"  [WARN] 스크래퍼 미등록: {source['id']}")
        return 0

    scraper = scraper_cls(source)
    stubs = scraper.fetch_list()
    if limit:
        stubs = stubs[:limit]
    if dry_run:
        for s in stubs:
            print(f"  [DRY] {s['title'][:60]} ({s.get('published_at')})")
        return len(stubs)

    saved = 0
    for stub in stubs:
        content, raw_bytes = scraper.fetch_article(stub["url"])
        article = scraper.normalize(stub, content)

        # Blob 업로드 (Hard Rule: 파싱 전 원본 보존)
        blob_url = ""
        if raw_bytes:
            published = article.get("published_at") or datetime.date.today().isoformat()
            filename = make_blob_filename(published, article["issuer"], stub["url"])
            try:
                blob_url = upload(raw_bytes, filename)
            except Exception as e:
                print(f"  [WARN] Blob 실패: {e}")

        raw_id = _save_raw_source(article, blob_url)
        if raw_id:
            saved += 1
    return saved


def _run_reader(source: dict, dry_run: bool, limit: int | None = None) -> int:
    """Tier 2 reader — 소스에 url_list 필드가 있어야 함."""
    from ingestion.channels import reader
    urls = source.get("url_list", [source.get("url")])
    if not urls:
        return 0
    articles = reader.fetch_list(source, [u for u in urls if u])
    if dry_run:
        for a in articles:
            print(f"  [DRY] {a['title'][:60]}")
        return len(articles)
    saved = 0
    for a in articles:
        raw_id = _save_raw_source(a)
        if raw_id:
            saved += 1
    return saved


def _run_pdf(source: dict, dry_run: bool, limit: int | None = None) -> int:
    from ingestion.pdf.parse import fetch_pdf, parse

    url = source.get("url")
    if not url:
        print(f"  [WARN] PDF 소스 URL 없음: {source['id']}")
        return 0
    if dry_run:
        print(f"  [DRY] PDF: {url}")
        return 1
    pdf_bytes = fetch_pdf(url)
    article = parse(pdf_bytes, source, url)
    raw_id = _save_raw_source(article, article.get("blob_url", ""))
    return 1 if raw_id else 0


# ── 폴백 체인 ─────────────────────────────────────────────────────────────────

def _run_with_fallback(source: dict, dry_run: bool, limit: int | None = None) -> int:
    method = source.get("method", "rss")
    tier = source.get("tier", 1)

    dispatch = {
        "rss":     _run_rss,
        "scraper": _run_scraper,
        "reader":  _run_reader,
        "pdf":     _run_pdf,
    }

    fn = dispatch.get(method)
    if not fn:
        print(f"  [WARN] 지원하지 않는 method: {method}")
        return 0

    try:
        return fn(source, dry_run, limit)
    except Exception as e:
        print(f"  [ERROR] {source['id']} ({method}) 실패: {e}")
        # Tier 3 폴백: crawl
        if tier <= 2:
            print(f"  → Tier 3 crawl 폴백 시도: {source['id']}")
            try:
                return _crawl_fallback(source, dry_run)
            except Exception as e2:
                print(f"  [ERROR] crawl 폴백도 실패: {e2}")
        return 0


def _crawl_fallback(source: dict, dry_run: bool) -> int:
    from ingestion.channels import crawl
    url = source.get("url")
    if not url:
        return 0
    if dry_run:
        print(f"  [DRY] crawl fallback: {url}")
        return 0
    article = crawl.fetch_url(url, source)
    if not article:
        return 0
    raw_id = _save_raw_source(article)
    return 1 if raw_id else 0


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Research Wiki 수집 라우터")
    parser.add_argument("--dry-run", action="store_true", help="실제 저장 없이 경로만 출력")
    parser.add_argument("--source", metavar="ID", help="특정 소스 ID만 실행")
    parser.add_argument("--tier", type=int, help="특정 tier만 실행")
    parser.add_argument("--sector", metavar="TAG", help="특정 섹터 태그 소스만 실행")
    parser.add_argument("--sources-file", metavar="PATH", help="sources.yaml 경로 오버라이드")
    parser.add_argument("--limit", type=int, help="소스당 최대 수집 건수 (검증용)")
    args = parser.parse_args()

    sources_path = Path(args.sources_file) if args.sources_file else None
    all_sources = load_sources(sources_path)
    targets = filter_sources(all_sources, args.source, args.tier, args.sector)

    if not targets:
        print("수집 대상 소스 없음 (active=false 이거나 조건 미일치)")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"수집 시작 {'[DRY-RUN]' if args.dry_run else ''}")
    print(f"대상 소스: {len(targets)}개")
    print(f"{'='*60}\n")

    total_saved = 0
    for source in targets:
        print(f"[{source['id']}] tier={source.get('tier')} method={source.get('method')} — {source['name']}")
        n = _run_with_fallback(source, args.dry_run, args.limit)
        print(f"  → {'기록됨' if not args.dry_run else '예상'}: {n}건\n")
        total_saved += n

    print(f"{'='*60}")
    print(f"완료 — 총 {total_saved}건 {'저장' if not args.dry_run else '(dry-run)'}")


if __name__ == "__main__":
    main()

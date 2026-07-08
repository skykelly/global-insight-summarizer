#!/usr/bin/env python3
"""ingestion/seed_equity_blog.py — equity-research-blog 아티클 시드 import.

equity-research-blog(https://github.com/skykelly/equity-research-blog)의
data/articles.json을 가져와 raw_sources → sources(pending)로 삽입한다.
이미 존재하는 URL/hash는 자동 skip(멱등).

사용법:
    python3 ingestion/seed_equity_blog.py --dry-run   # DB 쓰기 없이 예상 결과만 출력
    python3 ingestion/seed_equity_blog.py --no-fetch  # summary_ko만 사용 (빠름)
    python3 ingestion/seed_equity_blog.py             # 원문 body fetch + summary_ko 폴백
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import requests

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

# .env.local 자동 로드 (로컬 실행 시)
def _load_dotenv() -> None:
    import re
    env_path = _ROOT / ".env.local"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r'^([A-Z_][A-Z0-9_]*)=(.+)$', line)
            if m and m.group(1) not in os.environ:
                os.environ[m.group(1)] = m.group(2).strip('"').strip("'")

_load_dotenv()

from ingestion.router import _save_raw_source

ARTICLES_URL = (
    "https://raw.githubusercontent.com/skykelly/equity-research-blog"
    "/main/data/articles.json"
)

SOURCE_NAME_MAP: dict[str, str] = {
    "goldman-sachs":  "Goldman Sachs",
    "j-p-morgan":     "J.P. Morgan",
    "morgan-stanley": "Morgan Stanley",
    "blackrock-bii":  "BlackRock",
    "jefferies":      "Jefferies",
}

SOURCE_YAML_ID_MAP: dict[str, str] = {
    "goldman-sachs":  "gs_insights",
    "j-p-morgan":     "jpm_insights",
    "morgan-stanley": "ms_ideas",
    "blackrock-bii":  "blackrock_bii",
    "jefferies":      "jefferies",
}

_MACRO_KW    = {"macro", "rates", "rate", "credit", "fx", "currency", "bond", "fixed income"}
_POWER_KW    = {"energy", "power", "utility", "utilities", "infrastructure", "renewable", "grid"}
_SEMIS_KW    = {"technology", "tech", "semiconductor", "semis", "ai", "chip", "chips", "compute"}


def _map_sector(category: str) -> list[str]:
    cat = category.lower()
    words = set(cat.replace("&", " ").replace(",", " ").split())
    if words & _MACRO_KW:
        return ["macro"]
    if words & _POWER_KW:
        return ["power_equipment"]
    if words & _SEMIS_KW:
        return ["ai_semis"]
    return ["power_equipment", "ai_semis"]


def _fetch_body(url: str) -> str:
    """원문 URL에서 기사 본문 추출. 실패 시 빈 문자열 반환."""
    from ingestion.channels.scrapers.base import extract_body, _DEFAULT_HEADERS
    from bs4 import BeautifulSoup
    try:
        resp = requests.get(url, headers=_DEFAULT_HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        return extract_body(soup)
    except Exception as e:
        print(f"  [WARN] body fetch 실패 ({url[:60]}): {e}")
        return ""


def run(dry_run: bool = False, no_fetch: bool = False) -> None:
    print(f"equity-research-blog 아티클 fetch: {ARTICLES_URL}")
    resp = requests.get(ARTICLES_URL, timeout=30)
    resp.raise_for_status()
    articles = resp.json()
    print(f"  총 {len(articles)}건 로드")

    stats = {"total": 0, "inserted": 0, "skip": 0, "rejected": 0, "error": 0}

    for raw in articles:
        stats["total"] += 1
        source_id   = raw.get("source_id", "")
        issuer      = SOURCE_NAME_MAP.get(source_id, raw.get("source_name", ""))
        yaml_id     = SOURCE_YAML_ID_MAP.get(source_id, source_id)
        title       = raw.get("title", "").strip()
        url         = raw.get("url", "").strip()
        published   = raw.get("published_date", "").strip()
        summary_ko  = raw.get("summary_ko", "").strip()
        category    = raw.get("category", "")
        sector_tags = _map_sector(category)

        if not url or not title or not published or not issuer:
            missing = [f for f, v in [("url",url),("title",title),("published_date",published),("issuer",issuer)] if not v]
            print(f"  [SKIP] 필수 필드 누락 {missing}: {title[:40] or url[:40]}")
            stats["rejected"] += 1
            continue

        if dry_run:
            print(f"  [DRY] {issuer:<20} {published}  {title[:55]}")
            stats["inserted"] += 1
            continue

        # body fetch
        body = ""
        if not no_fetch:
            body = _fetch_body(url)
            if body:
                print(f"  [OK ] body {len(body)}자: {title[:50]}")
            time.sleep(0.3)  # 과도한 요청 방지

        content = body or summary_ko

        article_dict = {
            "url":            url,
            "title":          title,
            "issuer":         issuer,
            "published_at":   published,
            "raw_text":       content,
            "content_text":   content,
            "sector_tags":    sector_tags,
            "source_yaml_id": yaml_id,
            "blob_url":       "",
        }

        try:
            raw_id = _save_raw_source(article_dict)
            if raw_id:
                stats["inserted"] += 1
            else:
                stats["skip"] += 1
        except Exception as e:
            print(f"  [ERR] {url[:60]}: {e}")
            stats["error"] += 1

    print()
    print("=" * 60)
    print(f"완료 {'(dry-run)' if dry_run else ''}")
    print(f"  총 {stats['total']}건  inserted {stats['inserted']}건  "
          f"skip(중복) {stats['skip']}건  rejected {stats['rejected']}건  "
          f"error {stats['error']}건")
    if not dry_run:
        print()
        print("다음 단계: python3 knowledge/gate1_filter.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="equity-research-blog 시드 import")
    parser.add_argument("--dry-run",  action="store_true", help="DB 쓰기 없이 예상 결과만 출력")
    parser.add_argument("--no-fetch", action="store_true", help="본문 fetch 없이 summary_ko만 사용")
    args = parser.parse_args()
    run(dry_run=args.dry_run, no_fetch=args.no_fetch)

#!/usr/bin/env python3
"""knowledge/generate_wiki.py — 섹터별 wiki 합성 (Sonnet).

claims + summaries를 4구성으로 합성:
  (a) 컨센서스 뷰  (b) 상충 뷰  (c) 뷰 변화(supersedes 체인)  (d) 핵심 수치 테이블

모든 주장에 [issuer, YYYY-MM] 인라인 표기 필수.
valid_until 경과 claims → '과거 뷰' 섹션으로 강등.
출력: kb/wiki/{sector}.md (Obsidian + Next.js 렌더링 양용)

트리거:
  - 섹터별 신규 claims 5건 누적 후 자동 호출 (daily-ingest.yml)
  - 주 1회 강제 (weekly-digest.yml)
  - 직접 실행: python3 knowledge/generate_wiki.py --sector power_equipment
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import anthropic

from knowledge.db import db_conn

_ROOT = Path(__file__).resolve().parent.parent
_WIKI_DIR = _ROOT / "kb" / "wiki"
_CLIENT = anthropic.Anthropic()

SECTORS = ["power_equipment", "ai_semis"]

SECTOR_LABELS = {
    "power_equipment": "전력기기 (Power Equipment)",
    "ai_semis": "AI 반도체 (AI Semiconductors)",
}


def _fetch_claims(sector: str) -> tuple[list[dict], list[dict]]:
    """활성 claims와 만료 claims를 분리해서 반환."""
    today = date.today().isoformat()
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.issuer, c.sector, c.entities, c.claim_ko,
                       c.direction, c.horizon, c.metrics, c.published_at,
                       c.valid_until, c.supersedes, c.outcome,
                       s.title as source_title, s.url as source_url
                FROM claims c
                JOIN sources s ON s.id = c.source_id
                WHERE c.sector = %s
                  AND s.status IN ('auto_accepted', 'accepted')
                ORDER BY c.published_at DESC
                """,
                (sector,),
            )
            all_claims = cur.fetchall()

    active = [c for c in all_claims if not c["valid_until"] or str(c["valid_until"]) >= today]
    expired = [c for c in all_claims if c["valid_until"] and str(c["valid_until"]) < today]
    return active, expired


def _fetch_summaries(sector: str, limit: int = 10) -> list[dict]:
    """최근 요약 목록 (컨텍스트용)."""
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.issuer, s.published_at, s.title, sm.content_ko
                FROM sources s JOIN summaries sm ON sm.source_id = s.id
                WHERE s.status IN ('auto_accepted', 'accepted')
                  AND s.sector_tags @> ARRAY[%s]
                ORDER BY s.published_at DESC
                LIMIT %s
                """,
                (sector, limit),
            )
            return cur.fetchall()


def _fmt_claim(c: dict) -> str:
    """claim dict → 프롬프트용 1줄 표현."""
    pub = str(c["published_at"])[:7]  # YYYY-MM
    direction = c["direction"] or "neutral"
    horizon = f", horizon: {c['horizon']}" if c["horizon"] else ""
    metrics_str = ""
    if c["metrics"]:
        m = c["metrics"] if isinstance(c["metrics"], dict) else json.loads(c["metrics"])
        vals = [f"{k}={v['value']}" for k, v in m.items() if isinstance(v, dict)]
        if vals:
            metrics_str = f" [{', '.join(vals)}]"
    return f"- [{c['issuer']}, {pub}] ({direction}{horizon}){metrics_str}: {c['claim_ko']}"


def _synthesize(sector: str, active: list[dict], expired: list[dict], summaries: list[dict]) -> str:
    label = SECTOR_LABELS.get(sector, sector)
    today = date.today().isoformat()

    active_lines = "\n".join(_fmt_claim(c) for c in active) or "없음"
    expired_lines = "\n".join(_fmt_claim(c) for c in expired) or "없음"

    summary_ctx = ""
    if summaries:
        summary_ctx = "\n\n## 최근 요약 (참고용)\n"
        for sm in summaries[:5]:
            pub = str(sm["published_at"])[:7]
            summary_ctx += f"\n### [{sm['issuer']}, {pub}] {sm['title']}\n"
            summary_ctx += sm["content_ko"][:500] + "...\n"

    system = f"""\
당신은 글로벌 기관 리서치를 섹터 wiki로 합성하는 애널리스트입니다.

아래 claims 목록을 분석하여 **{label}** 섹터 wiki를 작성하세요.

필수 규칙:
1. 모든 주장에 [발행처, YYYY-MM] 인라인 표기 필수 — 없으면 작성하지 마세요
2. 직접 만든 주장은 절대 포함하지 마세요 (claims에 있는 내용만)
3. 상충하는 뷰는 둘 다 공정하게 병기
4. 수치는 claims의 metrics에서만 가져오고, 없으면 '구체 수치 없음'으로 표기

출력 포맷 (마크다운, frontmatter 포함):
---
sector: {sector}
updated_at: {today}
---

# {label} — 리서치 wiki

> 최종 업데이트: {today}

## 컨센서스 뷰
(여러 발행처가 공통적으로 지지하는 주요 방향성. 없으면 "아직 컨센서스 형성되지 않음" 기재)

## 상충 뷰
(같은 주제에 대해 bullish/bearish가 갈리는 논점. 없으면 해당 섹션 생략)

## 뷰 변화 (시간 흐름)
(기존 뷰에서 달라진 포지션. 최신 → 이전 순으로. 없으면 해당 섹션 생략)

## 핵심 수치 테이블
(metrics가 있는 claims에서 발췌. 없으면 해당 섹션 생략)

| 지표 | 수치 | 발행처 | 발행월 | 출처 |
|------|------|--------|--------|------|

## 과거 뷰 (valid_until 경과)
(만료된 claims. 없으면 해당 섹션 생략)
"""

    user_msg = f"""## 활성 Claims ({len(active)}건)
{active_lines}

## 만료 Claims ({len(expired)}건)
{expired_lines}
{summary_ctx}"""

    msg = _CLIENT.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return msg.content[0].text


def _count_new_claims_since(sector: str, since_iso: str) -> int:
    """since 이후 추가된 claims 건수."""
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS cnt FROM claims c
                JOIN sources s ON s.id = c.source_id
                WHERE c.sector = %s
                  AND s.status IN ('auto_accepted', 'accepted')
                  AND c.created_at >= %s::timestamptz
                """,
                (sector, since_iso),
            )
            return cur.fetchone()["cnt"]


def run(sectors: list[str], force: bool = False, new_claims_threshold: int = 5) -> dict[str, str]:
    """지정 섹터 wiki 생성. 반환값: {sector: output_path}."""
    _WIKI_DIR.mkdir(parents=True, exist_ok=True)
    results = {}

    for sector in sectors:
        wiki_path = _WIKI_DIR / f"{sector}.md"

        if not force:
            # 마지막 생성 이후 신규 claims가 threshold 미만이면 건너뜀
            last_updated = "1970-01-01T00:00:00+00:00"
            if wiki_path.exists():
                # frontmatter에서 updated_at 파싱
                content = wiki_path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if line.startswith("updated_at:"):
                        last_updated = line.split(":", 1)[1].strip() + "T00:00:00+00:00"
                        break

            new_count = _count_new_claims_since(sector, last_updated)
            if new_count < new_claims_threshold:
                print(f"[wiki] {sector}: 신규 claims {new_count}건 < threshold {new_claims_threshold}, 건너뜀")
                continue

        print(f"[wiki] {sector} 합성 중...")
        active, expired = _fetch_claims(sector)
        summaries = _fetch_summaries(sector)

        if not active and not expired:
            print(f"[wiki] {sector}: claims 없음, 플레이스홀더 유지")
            continue

        content = _synthesize(sector, active, expired, summaries)
        wiki_path.write_text(content, encoding="utf-8")
        print(f"[wiki] {sector} → {wiki_path} (active={len(active)}, expired={len(expired)})")
        results[sector] = str(wiki_path)

    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--sector", choices=SECTORS + ["all"], default="all")
    p.add_argument("--force", action="store_true", help="threshold 무시하고 강제 생성")
    p.add_argument("--threshold", type=int, default=5, help="신규 claims 최소 건수")
    args = p.parse_args()

    target = SECTORS if args.sector == "all" else [args.sector]
    result = run(target, force=args.force, new_claims_threshold=args.threshold)
    if result:
        print(f"완료: {list(result.keys())}")
    else:
        print("생성할 섹터 없음 (threshold 미달 또는 claims 없음)")

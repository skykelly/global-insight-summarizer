#!/usr/bin/env python3
"""knowledge/weekly_digest.py — 주간 Obsidian 호환 digest 생성.

지난 7일의 신규 claims + 뷰 변화 하이라이트를 Obsidian frontmatter 포함 마크다운으로 출력.
Actions artifact로도 업로드됨 (weekly-digest.yml).

출력: output/weekly-{YYYY-MM-DD}.md
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.db import db_conn
from knowledge.generate_wiki import SECTORS, SECTOR_LABELS, _fmt_claim

_ROOT = Path(__file__).resolve().parent.parent
_OUTPUT_DIR = _ROOT / "output"


def _fetch_new_claims(since: str) -> dict[str, list[dict]]:
    """섹터별 신규 claims."""
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.sector, c.issuer, c.claim_ko, c.direction, c.horizon,
                       c.metrics, c.published_at, c.valid_until, c.supersedes,
                       s.title as source_title
                FROM claims c
                JOIN sources s ON s.id = c.source_id
                WHERE s.status IN ('auto_accepted', 'accepted')
                  AND c.created_at >= %s::timestamptz
                ORDER BY c.sector, c.published_at DESC
                """,
                (since + "T00:00:00+00:00",),
            )
            rows = cur.fetchall()

    by_sector: dict[str, list[dict]] = {s: [] for s in SECTORS}
    for row in rows:
        if row["sector"] in by_sector:
            by_sector[row["sector"]].append(row)
    return by_sector


def _fetch_view_changes(since: str) -> list[dict]:
    """supersedes가 채워진 최신 claims — 뷰 변화."""
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.issuer, c.sector, c.claim_ko, c.direction,
                       c.published_at, c.supersedes,
                       prev.claim_ko as prev_claim_ko,
                       prev.direction as prev_direction,
                       prev.published_at as prev_published_at
                FROM claims c
                LEFT JOIN claims prev ON prev.id = c.supersedes
                JOIN sources s ON s.id = c.source_id
                WHERE c.supersedes IS NOT NULL
                  AND s.status IN ('auto_accepted', 'accepted')
                  AND c.created_at >= %s::timestamptz
                ORDER BY c.published_at DESC
                """,
                (since + "T00:00:00+00:00",),
            )
            return cur.fetchall()


def _synthesize_digest(
    today: str,
    since: str,
    new_claims: dict[str, list[dict]],
    view_changes: list[dict],
) -> str:
    total = sum(len(v) for v in new_claims.values())

    # 프롬프트 없이 구조화 출력 (LLM 비용 절약 — 단순 집계라 구조화로 충분)
    lines = [
        "---",
        f"date: {today}",
        f"type: weekly-digest",
        f"week_ending: {today}",
        f"sectors: [{', '.join(SECTORS)}]",
        f"new_claims: {total}",
        f"view_changes: {len(view_changes)}",
        "---",
        "",
        f"# Research Wiki 주간 요약 — {today}",
        "",
        f"> 기간: {since} ~ {today} | 신규 claims {total}건 | 뷰 변화 {len(view_changes)}건",
        "",
    ]

    # 섹터별 신규 claims
    for sector in SECTORS:
        label = SECTOR_LABELS[sector]
        claims = new_claims.get(sector, [])
        lines.append(f"## {label} ({len(claims)}건)")
        if not claims:
            lines.append("이번 주 신규 claims 없음.")
        else:
            for c in claims:
                lines.append(_fmt_claim(c))
        lines.append("")

    # 뷰 변화 하이라이트
    lines.append("## 뷰 변화 하이라이트")
    if not view_changes:
        lines.append("이번 주 뷰 변화 없음.")
    else:
        for ch in view_changes:
            pub = str(ch["published_at"])[:7]
            prev_pub = str(ch["prev_published_at"])[:7] if ch.get("prev_published_at") else "?"
            prev_dir = ch.get("prev_direction") or "?"
            new_dir = ch.get("direction") or "?"
            lines.append(
                f"- **[{ch['issuer']}, {pub}]** {prev_dir} → {new_dir}: "
                f"{ch['claim_ko']}"
            )
            if ch.get("prev_claim_ko"):
                lines.append(
                    f"  - _(이전 뷰 [{ch['issuer']}, {prev_pub}]: {ch['prev_claim_ko']})_"
                )
    lines.append("")
    lines.append("---")
    lines.append(f"_자동 생성: {today} | Research Wiki_")

    return "\n".join(lines)


def run() -> str | None:
    """주간 digest 생성. 반환값: 출력 파일 경로."""
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    since = (date.today() - timedelta(days=7)).isoformat()

    new_claims = _fetch_new_claims(since)
    view_changes = _fetch_view_changes(since)

    total = sum(len(v) for v in new_claims.values())
    print(f"[digest] 신규 claims {total}건, 뷰 변화 {len(view_changes)}건 (since {since})")

    content = _synthesize_digest(today, since, new_claims, view_changes)

    out_path = _OUTPUT_DIR / f"weekly-{today}.md"
    out_path.write_text(content, encoding="utf-8")
    print(f"[digest] → {out_path}")
    return str(out_path)


if __name__ == "__main__":
    run()

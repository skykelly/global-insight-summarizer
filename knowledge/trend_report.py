#!/usr/bin/env python3
"""knowledge/trend_report.py — Weekly Trend Memory Update 리포트.

docs/ib_asset_manager_sector_trend_seed.md §14.1 포맷.
knowledge/scoring.py + knowledge/anomaly.py 실행 결과(trend_scores, anomalies)를
사람이 읽는 마크다운으로 합성한다. LLM 호출 없음 — 구조화 집계로 충분.

실행 순서: scoring.py → anomaly.py → trend_report.py (weekly-digest.yml)

출력: output/trend-report-{YYYY-MM-DD}.md
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.db import db_conn
from knowledge.taxonomy import concept_by_id, sector_label

_ROOT = Path(__file__).resolve().parent.parent
_OUTPUT_DIR = _ROOT / "output"


def _fetch_sector_scores(period_start: str, period_end: str) -> list[dict]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT target_id, mention_score, importance_score, mention_count, source_diversity
                FROM trend_scores
                WHERE target_type='sector' AND period_start=%s AND period_end=%s
                ORDER BY mention_score DESC NULLS LAST
                """,
                (period_start, period_end),
            )
            return cur.fetchall()


def _fetch_concept_scores(period_start: str, period_end: str, limit: int = 10) -> list[dict]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT target_id, mention_score, importance_score, mention_count
                FROM trend_scores
                WHERE target_type='concept' AND period_start=%s AND period_end=%s
                ORDER BY mention_score DESC NULLS LAST
                LIMIT %s
                """,
                (period_start, period_end, limit),
            )
            return cur.fetchall()


def _fetch_open_anomalies(period_start: str, period_end: str) -> list[dict]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT anomaly_type, title, description, severity, related_sectors
                FROM anomalies
                WHERE status='open' AND detected_at >= %s::timestamptz
                ORDER BY CASE severity WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, detected_at DESC
                """,
                (period_start + "T00:00:00+00:00",),
            )
            return cur.fetchall()


def _quadrant(mention: float | None, importance: float | None) -> str:
    """2축 매트릭스 분류 (Observatory §14.1 4구간)."""
    m, i = mention or 0, importance or 0
    if m >= 60 and i >= 60:
        return "High Mention / High Importance"
    if m >= 60 and i < 60:
        return "High Mention / Low Importance"
    if m < 40 and i >= 60:
        return "Low Mention / High Importance"
    return "Emerging Weak Signal"


def synthesize(period_start: str, period_end: str) -> str:
    sectors = _fetch_sector_scores(period_start, period_end)
    concepts = _fetch_concept_scores(period_start, period_end)
    anomalies = _fetch_open_anomalies(period_start, period_end)

    lines = [
        "---",
        f"type: weekly-trend-memory-update",
        f"period_start: {period_start}",
        f"period_end: {period_end}",
        f"sector_count: {len(sectors)}",
        f"anomaly_count: {len(anomalies)}",
        "---",
        "",
        f"# Weekly Trend Memory Update — {period_end}",
        "",
        f"> 기간: {period_start} ~ {period_end}",
        "",
        "## 섹터 스코어보드 (Mention · Importance)",
        "",
        "| 섹터 | Mention | Importance | 언급 건수 | 커버 기관 |",
        "|---|---:|---:|---:|---:|",
    ]
    for s in sectors:
        lines.append(
            f"| {sector_label(s['target_id'])} | {s['mention_score'] or 0} | "
            f"{s['importance_score'] or 0} | {s['mention_count']} | {s['source_diversity']} |"
        )
    if not sectors:
        lines.append("| _데이터 없음_ | | | | |")
    lines.append("")

    lines.append("## 2축 매트릭스")
    lines.append("")
    for s in sectors:
        q = _quadrant(s["mention_score"], s["importance_score"])
        lines.append(f"- **{sector_label(s['target_id'])}** — {q} (M{s['mention_score']}·I{s['importance_score']})")
    if not sectors:
        lines.append("_데이터 없음_")
    lines.append("")

    lines.append("## 많이 언급되는 컨셉 Top 10")
    lines.append("")
    for c in concepts:
        concept = concept_by_id(c["target_id"])
        name = concept["canonical_name"] if concept else c["target_id"]
        lines.append(f"- {name} — Mention {c['mention_score']} · Importance {c['importance_score']} ({c['mention_count']}건)")
    if not concepts:
        lines.append("_이번 기간 컨셉 매칭 claims 없음_")
    lines.append("")

    lines.append("## 이상 징후 후보 (review_required)")
    lines.append("")
    if not anomalies:
        lines.append("이번 기간 신규 이상 징후 없음.")
    else:
        for a in anomalies:
            sectors_str = ", ".join(sector_label(s) for s in (a["related_sectors"] or []))
            lines.append(f"- **[{a['severity']}] {a['anomaly_type']}** — {a['title']} ({sectors_str})")
            lines.append(f"  - {a['description']}")
    lines.append("")

    lines.append("---")
    lines.append(f"_자동 생성: {period_end} | Market Signal IQ_")

    return "\n".join(lines)


def run(period: str = "weekly") -> str:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today()
    days = {"daily": 1, "weekly": 7, "monthly": 30}.get(period, 7)
    period_start = (today - timedelta(days=days)).isoformat()
    period_end = today.isoformat()

    content = synthesize(period_start, period_end)
    out_path = _OUTPUT_DIR / f"trend-report-{period_end}.md"
    out_path.write_text(content, encoding="utf-8")
    print(f"[trend_report] → {out_path}")
    return str(out_path)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--period", choices=["daily", "weekly", "monthly"], default="weekly")
    args = p.parse_args()
    run(args.period)

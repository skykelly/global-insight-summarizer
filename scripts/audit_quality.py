#!/usr/bin/env python3
"""
scripts/audit_quality.py — R2 주간 품질 감사 데이터 수집
GitHub Actions quality-audit.yml에서 호출 / Claude Routine R2 보조

출력: JSON (stdout) — GitHub Actions에서 이슈 본문으로 가공
"""

import json
import os
import sys
from datetime import datetime, timezone

import psycopg


def main() -> dict:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("DATABASE_URL 환경변수 없음")

    conn = psycopg.connect(db_url)
    cur = conn.cursor()

    # ── 지난 7일 review_log ──────────────────────────────────────────────────
    cur.execute("""
        SELECT rl.reason_tag, rl.decision, s.url, s.quality::text
        FROM review_log rl
        JOIN sources s ON s.id = rl.source_id
        WHERE rl.created_at >= NOW() - INTERVAL '7 days'
        ORDER BY rl.created_at DESC
    """)
    review_rows = cur.fetchall()

    from collections import Counter
    reason_dist = Counter(r[0] for r in review_rows if r[0])
    decision_dist = Counter(r[1] for r in review_rows)

    # ── 소스별 30일 반려율 ────────────────────────────────────────────────────
    cur.execute("""
        SELECT s.url,
            ROUND(COUNT(*) FILTER (WHERE rl.decision='reject') * 100.0 / COUNT(*), 1) AS reject_rate,
            COUNT(*) AS total
        FROM sources s
        JOIN review_log rl ON rl.source_id = s.id
        WHERE rl.created_at >= NOW() - INTERVAL '30 days'
        GROUP BY s.url
        HAVING COUNT(*) >= 3
        ORDER BY reject_rate DESC
        LIMIT 10
    """)
    source_rates = [{"url": r[0], "reject_rate": float(r[1]), "total": r[2]} for r in cur.fetchall()]
    high_reject = [s for s in source_rates if s["reject_rate"] >= 40.0]

    # ── 지난 7일 소스 상태 분포 ──────────────────────────────────────────────
    cur.execute("""
        SELECT status, COUNT(*) FROM sources
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY status ORDER BY status
    """)
    status_dist = {r[0]: r[1] for r in cur.fetchall()}
    total_week = sum(status_dist.values())
    queue_pct = round(status_dist.get("queued", 0) * 100 / total_week, 1) if total_week else 0

    # ── auto_accept 5건 샘플 ──────────────────────────────────────────────────
    cur.execute("""
        SELECT id::text, title, url, quality::text, gate_note
        FROM sources
        WHERE status = 'auto_accepted'
        ORDER BY RANDOM() LIMIT 5
    """)
    auto_accept_sample = [
        {"id": r[0], "title": r[1], "url": r[2], "quality": r[3], "gate_note": r[4]}
        for r in cur.fetchall()
    ]

    # ── auto_reject 5건 샘플 ─────────────────────────────────────────────────
    cur.execute("""
        SELECT id::text, title, url, gate_note
        FROM sources
        WHERE status = 'rejected'
        ORDER BY RANDOM() LIMIT 5
    """)
    auto_reject_sample = [
        {"id": r[0], "title": r[1], "url": r[2], "gate_note": r[3]}
        for r in cur.fetchall()
    ]

    conn.close()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "review_7d": {
            "total": len(review_rows),
            "reason_distribution": dict(reason_dist),
            "decision_distribution": dict(decision_dist),
        },
        "source_reject_rates_30d": source_rates,
        "high_reject_sources": high_reject,
        "status_distribution_7d": status_dist,
        "queue_pct": queue_pct,
        "auto_accept_sample": auto_accept_sample,
        "auto_reject_sample": auto_reject_sample,
    }


def render_issue_body(data: dict) -> str:
    r = data["review_7d"]
    status = data["status_distribution_7d"]
    total = sum(status.values()) or 1

    lines = [
        f"# 주간 품질 리포트 {datetime.now(timezone.utc).strftime('%Y-W%V')}",
        "",
        "## 7일 review_log 요약",
        f"- 총 {r['total']}건 검토",
        "- **reason_tag 분포**: " + ", ".join(f"{k}={v}" for k, v in r["reason_distribution"].items()) if r["reason_distribution"] else "- reason_tag 기록 없음",
        "- **판정 결과**: " + ", ".join(f"{k}={v}" for k, v in r["decision_distribution"].items()),
        "",
        "## 7일 소스 상태 분포",
    ]
    for s, cnt in status.items():
        pct = round(cnt * 100 / total, 1)
        lines.append(f"- {s}: {cnt}건 ({pct}%)")
    lines.append(f"- **review_queue 비율**: {data['queue_pct']}% (감소 추이면 게이트 학습 중)")
    lines.append("")

    if data["high_reject_sources"]:
        lines += [
            "## ⚠️ 반려율 40%+ 소스 (비활성화 검토)",
            *[f"- {s['url']} — 반려율 {s['reject_rate']}% ({s['total']}건)" for s in data["high_reject_sources"]],
            "",
        ]

    lines += [
        "## auto_accept 스팟체크 (5건)",
        *([f"- `{s['id'][:8]}` {s['title'] or s['url']} | quality: {s['quality']}" for s in data["auto_accept_sample"]] or ["(샘플 없음)"]),
        "",
        "## auto_reject 스팟체크 (5건)",
        *([f"- `{s['id'][:8]}` {s['title'] or s['url']} | gate_note: {s['gate_note']}" for s in data["auto_reject_sample"]] or ["(샘플 없음)"]),
        "",
        "---",
        "_R2 자동 생성 — 반려율 40%+ 소스는 sources.yaml active: false 검토 필요_",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    data = main()
    if "--json" in sys.argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_issue_body(data))

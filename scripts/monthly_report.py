#!/usr/bin/env python3
"""
scripts/monthly_report.py — R4 월간 비용·용량·게이트 통과율 리포트
GitHub Actions monthly-report.yml에서 호출 / Claude Routine R4 보조

집계와 보고만 — 수정 시도 금지
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone


def get_actions_stats(repo: str) -> dict:
    """gh CLI로 지난달 daily-ingest 실행 결과 집계"""
    try:
        result = subprocess.run(
            [
                "gh", "run", "list",
                "--workflow=daily-ingest.yml",
                f"--repo={repo}",
                "--limit=31",
                "--json=createdAt,status,conclusion",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        runs = json.loads(result.stdout) if result.returncode == 0 else []
    except Exception:
        runs = []

    if not runs:
        return {"total": 0, "success": 0, "failure": 0, "success_pct": None}

    total = len(runs)
    success = sum(1 for r in runs if r.get("conclusion") == "success")
    failure = total - success
    return {
        "total": total,
        "success": success,
        "failure": failure,
        "success_pct": round(success * 100 / total, 1) if total else 0,
    }


def get_db_stats(db_url: str) -> dict:
    import psycopg

    conn = psycopg.connect(db_url)
    cur = conn.cursor()

    # 지난달 소스 상태별
    cur.execute("""
        SELECT status, COUNT(*) FROM sources
        WHERE created_at >= date_trunc('month', NOW() - INTERVAL '1 month')
          AND created_at < date_trunc('month', NOW())
        GROUP BY status ORDER BY status
    """)
    status_dist = {r[0]: r[1] for r in cur.fetchall()}
    total_sources = sum(status_dist.values()) or 1

    # 지난달 claims
    cur.execute("""
        SELECT COUNT(*) FROM claims
        WHERE created_at >= date_trunc('month', NOW() - INTERVAL '1 month')
          AND created_at < date_trunc('month', NOW())
    """)
    claims_count = cur.fetchone()[0]

    # DB 크기
    cur.execute("SELECT pg_database_size(current_database()) / 1024.0 / 1024 AS mb")
    db_mb = float(cur.fetchone()[0])

    # 임베딩 수
    cur.execute("SELECT COUNT(*) FROM knowledge_embeddings")
    embedding_count = cur.fetchone()[0]

    # 게이트 통과율
    auto_accept = status_dist.get("auto_accepted", 0)
    queued = status_dist.get("queued", 0) + status_dist.get("accepted", 0)
    rejected = status_dist.get("rejected", 0)

    conn.close()

    return {
        "status_distribution": status_dist,
        "auto_accept_pct": round(auto_accept * 100 / total_sources, 1),
        "queue_pct": round(queued * 100 / total_sources, 1),
        "reject_pct": round(rejected * 100 / total_sources, 1),
        "claims_count": claims_count,
        "db_mb": db_mb,
        "db_warning": db_mb > 400,
        "embedding_count": embedding_count,
    }


def render_issue_body(month: str, actions: dict, db: dict) -> str:
    warn = " ⚠️ 경고: 0.4GB 초과!" if db["db_warning"] else ""
    lines = [
        f"# 월간 운영 리포트 {month}",
        "",
        "## GitHub Actions",
        f"- daily-ingest 실행: {actions['total']}회",
        f"- 성공: {actions['success']}회 / 실패: {actions['failure']}회",
        f"- 성공률: {actions['success_pct']}%" if actions["success_pct"] is not None else "- (데이터 없음)",
        "",
        "## 소스 게이트 통과율",
        f"- auto_accept: {db['auto_accept_pct']}%",
        f"- review_queue: {db['queue_pct']}%",
        f"- auto_reject: {db['reject_pct']}%",
        "",
        "## 지식 베이스",
        f"- 신규 claims: {db['claims_count']}건",
        f"- 임베딩 벡터: {db['embedding_count']}개",
        "",
        "## 인프라",
        f"- DB 스토리지: {db['db_mb']:.1f} MB{warn}",
        "- Vercel Blob: 대시보드 수동 확인 필요",
        "",
        "## 권고사항",
    ]

    recommendations = []
    if db["db_warning"]:
        recommendations.append("⚠️ DB 스토리지 0.4GB 초과 — 오래된 임베딩 정리 또는 Neon 플랜 업그레이드 검토")
    if actions.get("failure", 0) > 5:
        recommendations.append(f"파이프라인 실패 {actions['failure']}회 — R1 정비공 점검 필요")
    if db["reject_pct"] > 60:
        recommendations.append("auto_reject 비율 60%+ — 트리아지 임계값(triage_config.yaml) 완화 검토")
    if not recommendations:
        recommendations.append("이상 없음")

    lines += [f"- {r}" for r in recommendations]
    lines += ["", "---", "_R4 자동 생성 — 집계 전용, 수정 시도 없음_"]
    return "\n".join(lines)


if __name__ == "__main__":
    repo = os.environ.get("GITHUB_REPOSITORY", "skykelly/global-insight-summarizer")
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("DATABASE_URL 환경변수 없음")

    month = datetime.now(timezone.utc).strftime("%Y-%m")
    # 월초 실행이므로 지난달
    from datetime import timedelta
    last_month = (datetime.now(timezone.utc).replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    actions = get_actions_stats(repo)
    db = get_db_stats(db_url)
    body = render_issue_body(last_month, actions, db)

    if "--json" in sys.argv:
        print(json.dumps({"month": last_month, "actions": actions, "db": db}, ensure_ascii=False, indent=2))
    else:
        print(body)

#!/usr/bin/env python3
"""knowledge/anomaly.py — 이상 징후(anomaly) 감지 규칙.

KNOWLEDGE_MODEL.md §2.3 / docs/ib_asset_manager_sector_trend_seed.md §11.
Anomaly는 확정 판단이 아니라 사람이 검토할 후보로 저장한다(§2.5 트리아지와 동일 원칙).

knowledge/scoring.py가 계산한 이번 기간 trend_scores를 입력으로 받아 판정한다
(scoring.py 실행 이후에 실행해야 함 — pipeline 순서: scoring → anomaly).

구현 규칙 (7종 중 visual_only_signal은 비주얼 asset 파이프라인 부재로 스코프 제외):
  mention_spike               — mention_count가 직전 기간 대비 2배 이상 + 최소 건수
  source_diversity_jump       — source_diversity가 직전 기간 대비 2 이상 증가
  high_importance_low_mention — importance_score>=75 AND mention_score<=35
  counter_signal               — 기간 내 item_type='counter_signal' claims 존재
  metric_divergence            — 동일 sector/concept 내 동일 지표명의 수치가 소스별로 1.5배 이상 차이
  new_concept_emergence        — concepts.status='candidate' 이면서 이번 기간 처음 발견

사용법:
    python3 knowledge/anomaly.py --period weekly
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.db import db_conn

MENTION_SPIKE_MULTIPLIER = 2.0
MENTION_SPIKE_MIN_COUNT = 3
SOURCE_DIVERSITY_JUMP_MIN = 2
HIGH_IMPORTANCE_MIN = 75.0
LOW_MENTION_MAX = 35.0
METRIC_DIVERGENCE_RATIO = 1.5

_NUMBER_RE = re.compile(r"[-+]?\d[\d,]*\.?\d*")


def _period(period: str, since: str | None, until: str | None) -> tuple[str, str]:
    if since and until:
        return since, until
    today = date.today()
    days = {"daily": 1, "weekly": 7, "monthly": 30}.get(period, 7)
    return (today - timedelta(days=days)).isoformat(), today.isoformat()


def _exists_open(conn, anomaly_type: str, target_sectors: list[str]) -> bool:
    """동일 type + target 조합의 open anomaly가 이미 있으면 중복 생성 skip."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM anomalies
            WHERE anomaly_type = %s AND status = 'open'
              AND related_sectors && %s
            LIMIT 1
            """,
            (anomaly_type, target_sectors),
        )
        return cur.fetchone() is not None


def _insert_anomaly(
    conn, anomaly_type: str, title: str, description: str,
    related_sectors: list[str], related_concepts: list[str],
    related_claim_ids: list[str], severity: str,
    previous_period: dict, current_period: dict,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO anomalies
              (anomaly_type, title, description, related_concepts, related_sectors,
               related_claim_ids, previous_period, current_period, severity,
               review_required, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,true,'open')
            """,
            (
                anomaly_type, title, description, related_concepts, related_sectors,
                related_claim_ids, json.dumps(previous_period), json.dumps(current_period),
                severity,
            ),
        )


# ── 규칙 1~3: trend_scores 기반 ───────────────────────────────────────────────

def _detect_score_based(conn, period_start: str, period_end: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT target_type, target_id, mention_score, importance_score,
                   mention_count, source_diversity, score_details
            FROM trend_scores
            WHERE period_start = %s AND period_end = %s
            """,
            (period_start, period_end),
        )
        rows = cur.fetchall()

    count = 0
    for row in rows:
        target_type, target_id = row["target_type"], row["target_id"]
        sectors = [target_id] if target_type == "sector" else []
        concepts = [target_id] if target_type == "concept" else []
        details = row["score_details"]
        if isinstance(details, str):
            details = json.loads(details)
        prev_count = (details or {}).get("mention", {}).get("prev_period_count", 0)
        cur_count = row["mention_count"]

        # mention_spike
        if cur_count >= MENTION_SPIKE_MIN_COUNT and prev_count > 0 and cur_count >= prev_count * MENTION_SPIKE_MULTIPLIER:
            if not _exists_open(conn, "mention_spike", sectors or concepts):
                delta = f"+{round((cur_count / prev_count - 1) * 100)}%"
                _insert_anomaly(
                    conn, "mention_spike",
                    f"{target_id} 언급 급증 ({delta})",
                    f"{target_type} '{target_id}' — 이번 기간 {cur_count}건, 직전 기간 {prev_count}건",
                    sectors, concepts, [], "high" if cur_count >= prev_count * 3 else "medium",
                    {"mention_count": prev_count}, {"mention_count": cur_count},
                )
                count += 1

        # source_diversity_jump
        prev_diversity = (details or {}).get("mention", {}).get("source_diversity_prev", None)
        # scoring.py는 prev diversity를 별도 저장하지 않으므로, 최근 trend_scores 이전 레코드에서 조회
        prev_row = _prev_trend_score(conn, target_type, target_id, period_start)
        if prev_row is not None:
            prev_div = prev_row["source_diversity"] or 0
            cur_div = row["source_diversity"] or 0
            if cur_div - prev_div >= SOURCE_DIVERSITY_JUMP_MIN:
                if not _exists_open(conn, "source_diversity_jump", sectors or concepts):
                    _insert_anomaly(
                        conn, "source_diversity_jump",
                        f"{target_id} 커버 기관 확대",
                        f"{target_type} '{target_id}' — 커버 기관 {prev_div}개 → {cur_div}개",
                        sectors, concepts, [], "medium",
                        {"source_diversity": prev_div}, {"source_diversity": cur_div},
                    )
                    count += 1

        # high_importance_low_mention
        if row["importance_score"] is not None and row["mention_score"] is not None:
            if row["importance_score"] >= HIGH_IMPORTANCE_MIN and row["mention_score"] <= LOW_MENTION_MAX:
                if not _exists_open(conn, "high_importance_low_mention", sectors or concepts):
                    _insert_anomaly(
                        conn, "high_importance_low_mention",
                        f"{target_id} 저커버·고중요",
                        f"{target_type} '{target_id}' — Importance {row['importance_score']} vs Mention {row['mention_score']}",
                        sectors, concepts, [], "medium",
                        {}, {"importance_score": row["importance_score"], "mention_score": row["mention_score"]},
                    )
                    count += 1

    return count


def _prev_trend_score(conn, target_type: str, target_id: str, before: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source_diversity FROM trend_scores
            WHERE target_type=%s AND target_id=%s AND period_start < %s
            ORDER BY period_start DESC LIMIT 1
            """,
            (target_type, target_id, before),
        )
        return cur.fetchone()


# ── 규칙 4: counter_signal ────────────────────────────────────────────────────

def _detect_counter_signals(conn, period_start: str, period_end: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.sector, c.core_concept, c.issuer, c.claim_ko
            FROM claims c
            JOIN sources s ON s.id = c.source_id
            WHERE s.status IN ('auto_accepted', 'accepted')
              AND c.item_type = 'counter_signal'
              AND c.published_at >= %s AND c.published_at < %s
            """,
            (period_start, period_end),
        )
        rows = cur.fetchall()

    count = 0
    for row in rows:
        sectors = [row["sector"]] if row["sector"] else []
        if _exists_open(conn, "counter_signal", sectors):
            continue
        _insert_anomaly(
            conn, "counter_signal",
            f"{row['sector']} 반대 신호 — {row['issuer']}",
            row["claim_ko"],
            sectors, [row["core_concept"]] if row["core_concept"] else [],
            [str(row["id"])], "medium", {}, {},
        )
        count += 1
    return count


# ── 규칙 5: metric_divergence ─────────────────────────────────────────────────

def _extract_number(span_or_value: str) -> float | None:
    m = _NUMBER_RE.search((span_or_value or "").replace(",", ""))
    return float(m.group(0)) if m else None


def _detect_metric_divergence(conn, period_start: str, period_end: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.sector, c.core_concept, c.metrics
            FROM claims c
            JOIN sources s ON s.id = c.source_id
            WHERE s.status IN ('auto_accepted', 'accepted')
              AND c.metrics IS NOT NULL
              AND c.published_at >= %s AND c.published_at < %s
            """,
            (period_start, period_end),
        )
        rows = cur.fetchall()

    # (sector, metric_name) -> [values]
    by_key: dict[tuple[str, str], list[tuple[float, str]]] = {}
    for row in rows:
        metrics = row["metrics"]
        if isinstance(metrics, str):
            metrics = json.loads(metrics)
        if not isinstance(metrics, dict):
            continue
        for metric_name, v in metrics.items():
            if not isinstance(v, dict):
                continue
            val = _extract_number(str(v.get("value", "")))
            if val is None or val == 0:
                continue
            key = (row["sector"], metric_name)
            by_key.setdefault(key, []).append((val, str(row["id"])))

    count = 0
    for (sector, metric_name), values in by_key.items():
        if len(values) < 2:
            continue
        nums = [v for v, _ in values]
        ratio = max(nums) / min(nums) if min(nums) > 0 else 0
        if ratio >= METRIC_DIVERGENCE_RATIO:
            sectors = [sector] if sector else []
            if _exists_open(conn, "metric_divergence", sectors):
                continue
            claim_ids = [cid for _, cid in values]
            _insert_anomaly(
                conn, "metric_divergence",
                f"{sector} '{metric_name}' 수치 소스별 상이",
                f"'{metric_name}' 값이 소스별로 {min(nums)}~{max(nums)} 범위 (비율 {round(ratio, 1)}x) — 사람 검토 필요",
                sectors, [], claim_ids, "low",
                {}, {"values": nums, "ratio": round(ratio, 2)},
            )
            count += 1
    return count


# ── 규칙 6: new_concept_emergence ─────────────────────────────────────────────

def _detect_new_concepts(conn, period_start: str, period_end: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT slug, canonical_name, related_sectors
            FROM concepts
            WHERE status = 'candidate'
              AND first_seen_at >= %s AND first_seen_at < %s
            """,
            (period_start, period_end),
        )
        rows = cur.fetchall()

    count = 0
    for row in rows:
        sectors = row["related_sectors"] or []
        if _exists_open(conn, "new_concept_emergence", sectors):
            continue
        _insert_anomaly(
            conn, "new_concept_emergence",
            f"신규 컨셉 후보: {row['canonical_name']}",
            f"taxonomy.yaml에 없는 컨셉 '{row['slug']}'이 claims 추출 중 발견됨 — "
            f"taxonomy 승격 검토 또는 기존 컨셉 alias 병합 검토",
            sectors, [row["slug"]], [], "low", {}, {},
        )
        count += 1
    return count


def run(period: str = "weekly", since: str | None = None, until: str | None = None) -> dict:
    period_start, period_end = _period(period, since, until)
    print(f"[anomaly] 기간 {period_start} ~ {period_end}")

    with db_conn() as conn:
        stats = {
            "score_based": _detect_score_based(conn, period_start, period_end),
            "counter_signal": _detect_counter_signals(conn, period_start, period_end),
            "metric_divergence": _detect_metric_divergence(conn, period_start, period_end),
            "new_concept": _detect_new_concepts(conn, period_start, period_end),
        }

    total = sum(stats.values())
    print(f"[anomaly] 신규 anomaly {total}건: {stats}")
    return stats


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--period", choices=["daily", "weekly", "monthly"], default="weekly")
    p.add_argument("--since", help="YYYY-MM-DD")
    p.add_argument("--until", help="YYYY-MM-DD")
    args = p.parse_args()
    run(args.period, args.since, args.until)

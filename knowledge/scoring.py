#!/usr/bin/env python3
"""knowledge/scoring.py — Mention/Importance 2축 트렌드 스코어링.

KNOWLEDGE_MODEL.md §2.2 / docs/ib_asset_manager_sector_trend_seed.md §13.
LLM 호출 없이 claims 테이블 집계 + 규칙 기반 heuristic으로 계산한다
(weekly_digest.py와 동일 원칙 — 단순 집계는 구조화로 충분, LLM 비용 가드).

Mention Score  — 얼마나 언급되는가 (claims 건수·소스 다양성·최근성·모멘텀)
Importance Score — 숫자 근거로 볼 때 얼마나 중요한가 (metrics·키워드 heuristic)
둘은 합산하지 않는다 — 단일 스칼라는 변별력을 잃는다(Hard Rule과 동일 원칙).

MVP heuristic이므로 완벽한 정밀도를 목표하지 않는다. 계산 근거는 score_details에
스냅샷으로 남겨 감사 가능하게 한다.

사용법:
    python3 knowledge/scoring.py --period weekly
    python3 knowledge/scoring.py --since 2026-07-01 --until 2026-07-08
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.db import db_conn
from knowledge.taxonomy import all_sectors

# issuer 신뢰도 가중치 — IB 리서치 > 국제기구·중앙은행 > 컨설팅 > 기타.
# 모르는 issuer는 기본값(0.6) 적용.
_ISSUER_WEIGHT = {
    "Goldman Sachs": 1.0, "J.P. Morgan": 1.0, "JPMorgan": 1.0,
    "Morgan Stanley": 1.0, "Jefferies": 0.9, "BlackRock": 0.9,
    "McKinsey": 0.85, "IMF": 0.95, "BIS": 0.95, "World Bank": 0.9,
    "OECD": 0.85, "IEA": 0.85,
}
_DEFAULT_ISSUER_WEIGHT = 0.6

# Importance heuristic 키워드 (claim_ko 한국어 + 원문 영문 혼재 대비 양쪽 매칭)
_BOTTLENECK_KW = re.compile(r"병목|지연|공급망\s*차질|부족|제약|bottleneck|shortage|constraint|delay", re.I)
_POLICY_KW = re.compile(r"정책|보조금|예산|규제|국방비|policy|subsidy|budget|regulation|defense spending", re.I)
_SUPPLY_CHAIN_KW = re.compile(r"공급망|전략적|리쇼어링|프렌드쇼어링|supply chain|critical|strategic|reshoring|friendshoring", re.I)
_GROWTH_KW = re.compile(r"CAGR|성장률|배로?\s*증가|급증|growth|double|triple", re.I)
_MARKET_SIZE_RE = re.compile(r"\$\s*\d+(\.\d+)?\s*(B|billion|T|trillion|조|억)", re.I)


def _period(period: str | None, since: str | None, until: str | None) -> tuple[str, str]:
    if since and until:
        return since, until
    today = date.today()
    days = {"daily": 1, "weekly": 7, "monthly": 30}.get(period or "weekly", 7)
    return (today - timedelta(days=days)).isoformat(), today.isoformat()


def _fetch_claims(period_start: str, period_end: str) -> list[dict]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.sector, c.related_sectors, c.core_concept, c.issuer,
                       c.claim_ko, c.item_type, c.metrics, c.evidence, c.time_horizon,
                       c.published_at
                FROM claims c
                JOIN sources s ON s.id = c.source_id
                WHERE s.status IN ('auto_accepted', 'accepted')
                  AND c.published_at >= %s AND c.published_at < %s
                """,
                (period_start, period_end),
            )
            return cur.fetchall()


def _fetch_prev_count(target_type: str, target_id: str, prev_start: str, prev_end: str) -> int:
    """모멘텀 계산용 — 직전 동일 길이 기간의 claims 건수."""
    col = "sector" if target_type == "sector" else "core_concept"
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) AS cnt FROM claims c
                JOIN sources s ON s.id = c.source_id
                WHERE s.status IN ('auto_accepted', 'accepted')
                  AND c.{col} = %s
                  AND c.published_at >= %s AND c.published_at < %s
                """,
                (target_id, prev_start, prev_end),
            )
            return cur.fetchone()["cnt"]


# ── Mention Score ────────────────────────────────────────────────────────────

def _normalize(value: float, max_value: float) -> float:
    """0~max_value → 0~100, 상한 클램프."""
    if max_value <= 0:
        return 0.0
    return min(100.0, round(value / max_value * 100, 1))


def _recency_score(items: list[dict], period_end: str) -> float:
    """published_at이 기간 끝에 가까울수록 높음 (기간 내 평균 위치)."""
    if not items:
        return 0.0
    end = date.fromisoformat(period_end)
    total = 0.0
    for it in items:
        pub = it["published_at"]
        pub_date = pub if isinstance(pub, date) else date.fromisoformat(str(pub))
        days_from_end = (end - pub_date).days
        total += max(0.0, 100.0 - days_from_end * 10)  # 10일 이전이면 0
    return round(total / len(items), 1)


def mention_score(
    target_type: str, target_id: str, items: list[dict],
    period_start: str, period_end: str,
) -> dict:
    """단일 target(섹터/컨셉)의 Mention Score + 구성요소. score_details에 근거 저장."""
    mention_count = len(items)
    issuers = {it["issuer"] for it in items if it["issuer"]}
    source_diversity = len(issuers)

    weighted = sum(_ISSUER_WEIGHT.get(it["issuer"], _DEFAULT_ISSUER_WEIGHT) for it in items)
    weighted_source_score = _normalize(weighted, mention_count * 1.0 or 1)

    recency = _recency_score(items, period_end)

    cross_sector = sum(1 for it in items if it.get("related_sectors"))
    cross_sector_spread_score = _normalize(cross_sector, mention_count or 1)

    days = max(1, (date.fromisoformat(period_end) - date.fromisoformat(period_start)).days)
    prev_start = (date.fromisoformat(period_start) - timedelta(days=days)).isoformat()
    prev_count = _fetch_prev_count(target_type, target_id, prev_start, period_start)
    if prev_count == 0:
        momentum_score = 100.0 if mention_count > 0 else 0.0
    else:
        momentum_score = _normalize(max(0, mention_count - prev_count), prev_count)

    normalized_mention_count = _normalize(mention_count, 20)  # 기간당 20건이면 만점 기준(MVP 임계)
    source_diversity_score = _normalize(source_diversity, 6)  # 6개 기관 커버면 만점(seed 소스 수 기준)

    score = round(
        0.30 * normalized_mention_count
        + 0.20 * source_diversity_score
        + 0.15 * weighted_source_score
        + 0.15 * recency
        + 0.10 * cross_sector_spread_score
        + 0.10 * momentum_score,
        1,
    )

    return {
        "score": score,
        "mention_count": mention_count,
        "source_diversity": source_diversity,
        "momentum_score": momentum_score,
        "details": {
            "normalized_mention_count": normalized_mention_count,
            "source_diversity_score": source_diversity_score,
            "weighted_source_score": weighted_source_score,
            "recency_score": recency,
            "cross_sector_spread_score": cross_sector_spread_score,
            "momentum_score": momentum_score,
            "prev_period_count": prev_count,
        },
    }


# ── Importance Score (MVP heuristic) ─────────────────────────────────────────

_TIME_HORIZON_SCORE = {
    "near_term": 30.0, "mid_term": 60.0, "long_term": 85.0, "structural": 100.0,
}


def importance_score(items: list[dict]) -> dict:
    """단일 target의 Importance Score. 완전 자동 정밀 계산 대신 MVP heuristic
    (docs/ib_asset_manager_sector_trend_seed.md §13.2 요소별 근사).
    """
    if not items:
        return {"score": 0.0, "metric_count": 0, "evidence_quality": 0.0, "details": {}}

    n = len(items)
    market_size_hits = 0
    growth_hits = 0
    capex_hits = 0  # metrics 자체가 capex/investment 근거 — metrics 보유 여부로 근사
    bottleneck_hits = 0
    policy_hits = 0
    supply_chain_hits = 0
    metric_count = 0
    evidence_count = 0
    horizon_total = 0.0

    for it in items:
        text = it.get("claim_ko") or ""
        metrics = it.get("metrics")
        if isinstance(metrics, str):
            try:
                metrics = json.loads(metrics)
            except (TypeError, ValueError):
                metrics = None
        if metrics:
            metric_count += 1
            capex_hits += 1
            spans = " ".join(str(v.get("span", "")) for v in metrics.values() if isinstance(v, dict))
            if _MARKET_SIZE_RE.search(spans) or _MARKET_SIZE_RE.search(text):
                market_size_hits += 1
        if it.get("evidence"):
            evidence_count += 1
        if _GROWTH_KW.search(text):
            growth_hits += 1
        if _BOTTLENECK_KW.search(text):
            bottleneck_hits += 1
        if _POLICY_KW.search(text):
            policy_hits += 1
        if _SUPPLY_CHAIN_KW.search(text):
            supply_chain_hits += 1
        horizon_total += _TIME_HORIZON_SCORE.get(it.get("time_horizon") or "", 50.0)

    market_size_score = _normalize(market_size_hits, n)
    growth_rate_score = _normalize(growth_hits, n)
    capex_score = _normalize(capex_hits, n)
    bottleneck_score = _normalize(bottleneck_hits, n)
    policy_support_score = _normalize(policy_hits, n)
    supply_chain_criticality_score = _normalize(supply_chain_hits, n)
    evidence_quality_score = _normalize(evidence_count + metric_count, n * 2)
    time_horizon_score = round(horizon_total / n, 1)

    score = round(
        0.20 * market_size_score
        + 0.15 * growth_rate_score
        + 0.15 * capex_score
        + 0.15 * bottleneck_score
        + 0.10 * policy_support_score
        + 0.10 * supply_chain_criticality_score
        + 0.10 * evidence_quality_score
        + 0.05 * time_horizon_score,
        1,
    )

    return {
        "score": score,
        "metric_count": metric_count,
        "evidence_quality": evidence_quality_score,
        "details": {
            "market_size_score": market_size_score,
            "growth_rate_score": growth_rate_score,
            "capex_score": capex_score,
            "bottleneck_score": bottleneck_score,
            "policy_support_score": policy_support_score,
            "supply_chain_criticality_score": supply_chain_criticality_score,
            "evidence_quality_score": evidence_quality_score,
            "time_horizon_score": time_horizon_score,
        },
    }


# ── trend_scores upsert ───────────────────────────────────────────────────────

def _upsert_trend_score(
    conn, target_type: str, target_id: str,
    period_start: str, period_end: str,
    m: dict, i: dict, novelty_score: float, anomaly_score: float,
) -> None:
    details = {"mention": m["details"], "importance": i["details"]}
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO trend_scores
              (period_start, period_end, target_type, target_id,
               mention_score, importance_score, momentum_score, novelty_score,
               anomaly_score, mention_count, source_diversity, metric_count,
               evidence_quality, score_details)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (target_type, target_id, period_start) DO UPDATE SET
              mention_score = EXCLUDED.mention_score,
              importance_score = EXCLUDED.importance_score,
              momentum_score = EXCLUDED.momentum_score,
              novelty_score = EXCLUDED.novelty_score,
              anomaly_score = EXCLUDED.anomaly_score,
              mention_count = EXCLUDED.mention_count,
              source_diversity = EXCLUDED.source_diversity,
              metric_count = EXCLUDED.metric_count,
              evidence_quality = EXCLUDED.evidence_quality,
              score_details = EXCLUDED.score_details
            """,
            (
                period_start, period_end, target_type, target_id,
                m["score"], i["score"], m["momentum_score"], novelty_score,
                anomaly_score, m["mention_count"], m["source_diversity"],
                i["metric_count"], i["evidence_quality"], json.dumps(details),
            ),
        )
    # UNIQUE 제약이 없으면 ON CONFLICT가 실패하므로, 없을 경우를 대비해 아래 run()에서
    # 사전 DELETE 후 INSERT 하는 방식은 쓰지 않는다 — 마이그레이션에 이미 UNIQUE index 존재.


def run(period: str = "weekly", since: str | None = None, until: str | None = None) -> dict:
    period_start, period_end = _period(period, since, until)
    claims = _fetch_claims(period_start, period_end)
    print(f"[scoring] 기간 {period_start} ~ {period_end} — claims {len(claims)}건")

    stats = {"sectors": 0, "concepts": 0}

    with db_conn() as conn:
        # 섹터별
        for s in all_sectors():
            sid = s["id"]
            items = [c for c in claims if c["sector"] == sid or sid in (c.get("related_sectors") or [])]
            if not items:
                continue
            m = mention_score("sector", sid, items, period_start, period_end)
            i = importance_score(items)
            _upsert_trend_score(conn, "sector", sid, period_start, period_end, m, i, 0.0, 0.0)
            stats["sectors"] += 1
            print(f"  [sector] {sid}: mention={m['score']} importance={i['score']} (n={len(items)})")

        # 컨셉별
        concept_ids = {c["core_concept"] for c in claims if c.get("core_concept")}
        for cid in concept_ids:
            items = [c for c in claims if c.get("core_concept") == cid]
            m = mention_score("concept", cid, items, period_start, period_end)
            i = importance_score(items)
            _upsert_trend_score(conn, "concept", cid, period_start, period_end, m, i, 0.0, 0.0)
            stats["concepts"] += 1
            print(f"  [concept] {cid}: mention={m['score']} importance={i['score']} (n={len(items)})")

    return stats


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--period", choices=["daily", "weekly", "monthly"], default="weekly")
    p.add_argument("--since", help="YYYY-MM-DD (until과 함께 지정 시 --period 무시)")
    p.add_argument("--until", help="YYYY-MM-DD")
    args = p.parse_args()
    result = run(args.period, args.since, args.until)
    print(f"스코어링 완료 — 섹터 {result['sectors']}건, 컨셉 {result['concepts']}건")

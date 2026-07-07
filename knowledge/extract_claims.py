#!/usr/bin/env python3
"""knowledge/extract_claims.py — Gate 3: Sonnet claims 추출.

원문 → claims JSON (issuer/sector/direction/horizon/metrics/published_at 필수).
원문에 없는 수치 생성 금지. 불확실하면 빈 배열.
claims 결과가 triage 입력으로 재활용된다 (Gate 3 겸용).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.db import db_conn
from knowledge.llm_client import CircuitBreaker, LLMCallError, call_json

_SYSTEM = """\
당신은 투자 리서치 문서에서 구조화된 주장(claim)을 추출하는 전문가입니다.

추출 규칙:
1. 각 claim은 반드시 포함: issuer, sector, claim_ko, published_at
2. claim_ko: 한국어 1문장. 주장의 핵심을 간결하게.
3. direction: bullish / bearish / neutral 중 하나
4. horizon: 시간 범위 ('2027', 'H2 2026', 'long-term', '12개월' 등)
5. metrics: {"지표명": {"value": "수치", "span": "원문 그대로"}} — span은 원문 발췌 필수
6. entities: 언급된 기업·제품명 배열
7. 원문에 없는 수치·사실 생성 절대 금지
8. 불확실하거나 추출할 만한 주장이 없으면 빈 배열 [] 반환
9. 문서당 최대 10건 (중요도 순 선별)
10. 섹터: 'power_equipment' 또는 'ai_semis' 중 가장 적합한 것

JSON 배열만 반환 (다른 텍스트 없음):
[
  {
    "issuer": "Goldman Sachs",
    "sector": "ai_semis",
    "entities": ["NVIDIA", "HBM"],
    "claim_ko": "GS는 HBM 수요가 2027년까지 연 40% 성장할 것으로 전망",
    "direction": "bullish",
    "horizon": "2027",
    "metrics": {"HBM CAGR": {"value": "40%", "span": "HBM demand grows ~40% CAGR through 2027"}},
    "published_at": "2026-01-15"
  }
]"""


def _extract(source_id: str, title: str, issuer: str, published_at: str, content: str) -> list[dict[str, Any]]:
    claims = call_json(
        model="claude-sonnet-4-6",
        system=_SYSTEM,
        user_content=f"발행처: {issuer}\n발행일: {published_at}\n제목: {title}\n\n본문:\n{content[:6000]}",
        max_tokens=2048,
    )
    if not isinstance(claims, list):
        return []
    return claims


def _validate_claim(c: dict) -> bool:
    """필수 필드 존재 여부 검증."""
    return all(c.get(f) for f in ("issuer", "sector", "claim_ko", "published_at"))


def _save_claims(source_id: str, claims: list[dict]) -> int:
    saved = 0
    with db_conn() as conn:
        with conn.cursor() as cur:
            for c in claims:
                if not _validate_claim(c):
                    print(f"  [claims] 필수 필드 누락, 건너뜀: {c.get('claim_ko','?')[:40]}")
                    continue
                cur.execute(
                    """
                    INSERT INTO claims
                      (source_id, issuer, sector, entities, claim_ko, direction,
                       horizon, metrics, published_at, valid_until)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        source_id,
                        c["issuer"],
                        c["sector"],
                        c.get("entities"),
                        c["claim_ko"],
                        c.get("direction"),
                        c.get("horizon"),
                        json.dumps(c["metrics"]) if c.get("metrics") else None,
                        c["published_at"],
                        c.get("valid_until"),
                    ),
                )
                saved += 1
    return saved


def run(source_ids: list[str] | None = None, backfill: bool = False) -> dict[str, int]:
    """pending 소스에서 claims 추출 및 저장."""
    stats = {"processed": 0, "total_claims": 0, "errors": 0}

    with db_conn() as conn:
        with conn.cursor() as cur:
            if backfill:
                # 이미 done/auto_accepted/accepted 상태이지만 claims가 없는 소스
                cur.execute(
                    """
                    SELECT s.id, s.title, s.issuer, s.published_at, s.content_text
                    FROM sources s
                    WHERE s.status IN ('auto_accepted','accepted','done')
                      AND NOT EXISTS (SELECT 1 FROM claims c WHERE c.source_id = s.id)
                    """
                )
            elif source_ids:
                cur.execute(
                    "SELECT id, title, issuer, published_at, content_text FROM sources WHERE status='pending' AND id = ANY(%s)",
                    (source_ids,),
                )
            else:
                cur.execute(
                    "SELECT id, title, issuer, published_at, content_text FROM sources WHERE status='pending'"
                )
            rows = cur.fetchall()

    breaker = CircuitBreaker(threshold=5)

    for row in rows:
        sid = str(row["id"])
        title = row["title"] or ""
        issuer = row["issuer"] or ""
        published_at = str(row["published_at"] or "")
        content = row["content_text"] or ""

        if not content.strip():
            print(f"[claims] {title[:50]} — content_text 없음, 건너뜀")
            stats["errors"] += 1
            continue

        try:
            claims = _extract(sid, title, issuer, published_at, content)
            count = _save_claims(sid, claims)
            print(f"[claims] {title[:50]} → {count}건 추출")
            stats["processed"] += 1
            stats["total_claims"] += count
            breaker.record_success()
        except LLMCallError as e:
            print(f"[claims] {sid} 오류: {e}")
            stats["errors"] += 1
            breaker.record_failure(str(e))
        except Exception as e:
            print(f"[claims] {sid} 오류: {e}")
            stats["errors"] += 1

    return stats


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--backfill", action="store_true")
    p.add_argument("--source-ids", nargs="*")
    args = p.parse_args()
    result = run(args.source_ids, args.backfill)
    print(f"claims 완료 — 처리: {result['processed']}건, 추출: {result['total_claims']}건, 오류: {result['errors']}건")

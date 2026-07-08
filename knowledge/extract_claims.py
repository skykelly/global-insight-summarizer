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
from knowledge.llm_client import MODEL_MAIN, CircuitBreaker, LLMCallError, call_json
from knowledge.taxonomy import concept_by_id, concept_ids, sector_prompt_block

_ITEM_TYPES = (
    "concept", "claim", "trend", "metric", "risk",
    "weak_signal", "counter_signal", "visual_insight", "sector_shift",
)


def _system_prompt() -> str:
    concepts_hint = ", ".join(concept_ids())
    return f"""\
당신은 투자 리서치 문서에서 구조화된 지식 단위(item)를 추출하는 전문가입니다.

대상 섹터 (1차 구현 대상):
{sector_prompt_block()}

추출 규칙:
1. 각 item은 반드시 포함: issuer, sector, item_type, claim_ko, published_at
2. item_type: {", ".join(_ITEM_TYPES)} 중 하나
   - claim: 구체적 주장/전망 (기본값)
   - concept: 새로 부상하는 개념/용어 자체
   - trend: 추세·동향 서술
   - metric: 숫자 근거 중심 항목 (metrics 필수)
   - risk: 하방 리스크·불확실성
   - weak_signal: 아직 약하지만 관찰 가치 있는 초기 신호
   - counter_signal: 기존 컨센서스에 반하는 신호
   - visual_insight: 표·차트에서만 발견되는 수치/구조
   - sector_shift: 섹터 간 자금·관심 이동
3. claim_ko: 한국어 1문장. 핵심을 간결하게.
4. core_concept: 아래 컨셉 목록 중 가장 관련 있는 id 하나 (없으면 생략).
   컨셉 목록: {concepts_hint}
5. direction: bullish / bearish / neutral 중 하나 (투자 관점, 선택)
6. trend_direction: rising / falling / stable / mixed / uncertain 중 하나 (관측 관점, 선택)
7. horizon: 자유형 시간 범위 ('2027', 'H2 2026', 'long-term', '12개월' 등, 선택)
8. time_horizon: near_term / mid_term / long_term / structural 중 하나 (선택)
9. metrics: {{"지표명": {{"value": "수치", "span": "원문 그대로"}}}} — span은 원문 발췌 필수
10. evidence: {{"evidence_type": "text|table|chart|image|transcript", "evidence_summary": "1줄 요약"}} (선택)
11. entities: 언급된 기업·제품명 배열
12. related_sectors: 이 item이 함께 걸치는 다른 섹터 id 배열 (교차 신호, 선택)
13. 원문에 없는 수치·사실 생성 절대 금지
14. 불확실하거나 추출할 만한 항목이 없으면 빈 배열 [] 반환
15. 문서당 최대 10건 (중요도 순 선별)

JSON 객체만 반환 (다른 텍스트 없음). claims 키에 배열을 담으세요:
{{
  "claims": [
    {{
      "issuer": "Goldman Sachs",
      "sector": "semi",
      "item_type": "claim",
      "core_concept": "hbm_cycle",
      "entities": ["NVIDIA", "HBM"],
      "claim_ko": "GS는 HBM 수요가 2027년까지 연 40% 성장할 것으로 전망",
      "direction": "bullish",
      "trend_direction": "rising",
      "horizon": "2027",
      "time_horizon": "mid_term",
      "metrics": {{"HBM CAGR": {{"value": "40%", "span": "HBM demand grows ~40% CAGR through 2027"}}}},
      "evidence": {{"evidence_type": "text", "evidence_summary": "GS 리서치 노트 본문 서술"}},
      "published_at": "2026-01-15"
    }}
  ]
}}
추출할 항목이 없으면 {{"claims": []}} 를 반환하세요."""


def _extract(source_id: str, title: str, issuer: str, published_at: str, content: str) -> list[dict[str, Any]]:
    result = call_json(
        model=MODEL_MAIN,
        system=_system_prompt(),
        user_content=f"발행처: {issuer}\n발행일: {published_at}\n제목: {title}\n\n본문:\n{content[:6000]}",
        max_tokens=2048,
    )
    # response_format=json_object 대응: {"claims": [...]} 언랩. 방어적으로 배열도 허용.
    if isinstance(result, list):
        return result
    claims = result.get("claims") if isinstance(result, dict) else None
    return claims if isinstance(claims, list) else []


def _validate_claim(c: dict) -> bool:
    """필수 필드 존재 여부 검증."""
    return all(c.get(f) for f in ("issuer", "sector", "claim_ko", "published_at"))


def _upsert_concept(conn, slug: str, sector: str, published_at: str) -> None:
    """core_concept 발견 시 concepts에 upsert.
    taxonomy.yaml에 정의된 컨셉이면 first/last_seen_at만 갱신,
    없으면 status='candidate'로 신규 후보 등록 (사람이 taxonomy.yaml 승격 검토).
    """
    known = concept_by_id(slug)
    canonical_name = known["canonical_name"] if known else slug
    related_sectors = known["related_sectors"] if known else [sector]
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO concepts (slug, canonical_name, related_sectors, status, first_seen_at, last_seen_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (slug) DO UPDATE SET
              last_seen_at = GREATEST(concepts.last_seen_at, EXCLUDED.last_seen_at),
              updated_at = NOW()
            """,
            (slug, canonical_name, related_sectors, "active" if known else "candidate", published_at, published_at),
        )


def _save_claims(source_id: str, claims: list[dict]) -> int:
    saved = 0
    with db_conn() as conn:
        with conn.cursor() as cur:
            for c in claims:
                if not _validate_claim(c):
                    print(f"  [claims] 필수 필드 누락, 건너뜀: {c.get('claim_ko','?')[:40]}")
                    continue
                item_type = c.get("item_type") if c.get("item_type") in _ITEM_TYPES else "claim"
                cur.execute(
                    """
                    INSERT INTO claims
                      (source_id, issuer, sector, related_sectors, item_type, core_concept,
                       entities, claim_ko, direction, trend_direction, horizon, time_horizon,
                       metrics, evidence, published_at, valid_until)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        source_id,
                        c["issuer"],
                        c["sector"],
                        c.get("related_sectors"),
                        item_type,
                        c.get("core_concept"),
                        c.get("entities"),
                        c["claim_ko"],
                        c.get("direction"),
                        c.get("trend_direction"),
                        c.get("horizon"),
                        c.get("time_horizon"),
                        json.dumps(c["metrics"]) if c.get("metrics") else None,
                        json.dumps(c["evidence"]) if c.get("evidence") else None,
                        c["published_at"],
                        c.get("valid_until"),
                    ),
                )
                saved += 1
                if c.get("core_concept"):
                    _upsert_concept(conn, c["core_concept"], c["sector"], c["published_at"])
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

#!/usr/bin/env python3
"""knowledge/gate2_rubric.py — Gate 2: Sonnet 4차원 루브릭 평가.

relevance / density / authority / novelty 각 1~5점. 합산 금지.
앵커 예시는 knowledge/prompts/rubric_anchors.md에서 로드 (하드코딩 금지).
novelty 판정에 기존 임베딩 top-5 유사도를 컨텍스트로 제공.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.db import db_conn
from knowledge.llm_client import CircuitBreaker, LLMCallError, call_json

_ROOT = Path(__file__).resolve().parent.parent
_ANCHORS_PATH = _ROOT / "knowledge" / "prompts" / "rubric_anchors.md"


def _load_anchors() -> str:
    return _ANCHORS_PATH.read_text(encoding="utf-8")


def _get_similar_titles(content: str, limit: int = 5) -> list[str]:
    """기존 임베딩에서 유사 제목 top-k를 가져온다. 임베딩 없으면 빈 목록."""
    try:
        from openai import OpenAI
        oc = OpenAI()
        emb = oc.embeddings.create(model="text-embedding-3-small", input=content[:2000]).data[0].embedding
        emb_str = json.dumps(emb)

        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ke.content
                    FROM knowledge_embeddings ke
                    ORDER BY ke.embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (emb_str, limit),
                )
                rows = cur.fetchall()
        return [r["content"][:100] for r in rows]
    except Exception:
        return []


def _call_sonnet(title: str, issuer: str, content: str, similar: list[str], anchors: str) -> dict:
    similar_ctx = "\n".join(f"- {s}" for s in similar) if similar else "없음 (첫 수집)"

    system = f"""\
당신은 리서치 품질 평가자입니다. 아래 4차원으로 문서를 평가합니다.

차원 정의:
- relevance (1~5): 전력기기(power_equipment) 또는 AI 반도체(ai_semis) 섹터 적합도
- density (1~5): 신규 수치·주장·데이터의 밀도 (추상적 문장만이면 낮음)
- authority (1~5): 발행처·저자 신뢰도 (IB리서치>컨설팅>언론>블로그)
- novelty (1~5): 기존 지식베이스 대비 신규성 (아래 유사 문서 목록 참고)

중요 규칙:
- 각 차원을 독립적으로 평가. 합산 점수 계산 금지.
- 앵커 예시를 기준으로 캘리브레이션하세요.

{anchors}

기존 유사 문서 (novelty 판정용):
{similar_ctx}

JSON만 반환 (다른 텍스트 없음):
{{"relevance": 1~5, "density": 1~5, "authority": 1~5, "novelty": 1~5, "note": "판정 근거 1줄 (한국어)"}}"""

    return call_json(
        model="claude-sonnet-4-6",
        system=system,
        user_content=f"발행처: {issuer}\n제목: {title}\n\n본문:\n{content[:2000]}",
        max_tokens=256,
    )


def run(source_ids: list[str] | None = None) -> dict[str, int]:
    """pending 소스 Gate 2 평가. quality + gate_note 업데이트."""
    stats = {"evaluated": 0, "errors": 0}
    anchors = _load_anchors()

    with db_conn() as conn:
        with conn.cursor() as cur:
            if source_ids:
                cur.execute(
                    "SELECT id, title, issuer, content_text FROM sources WHERE status='pending' AND id = ANY(%s)",
                    (source_ids,),
                )
            else:
                cur.execute(
                    "SELECT id, title, issuer, content_text FROM sources WHERE status='pending'"
                )
            rows = cur.fetchall()

    breaker = CircuitBreaker(threshold=5)

    for row in rows:
        sid = row["id"]
        title = row["title"] or ""
        issuer = row["issuer"] or ""
        content = row["content_text"] or ""

        try:
            similar = _get_similar_titles(content)
            scores = _call_sonnet(title, issuer, content, similar, anchors)

            quality = {k: scores[k] for k in ("relevance", "density", "authority", "novelty")}
            note = scores.get("note", "")

            with db_conn() as conn2:
                with conn2.cursor() as cur2:
                    cur2.execute(
                        "UPDATE sources SET quality=%s, gate_note=%s, updated_at=NOW() WHERE id=%s",
                        (json.dumps(quality), f"Gate2: {note}", str(sid)),
                    )
            print(f"[gate2] {title[:50]} → {quality}")
            stats["evaluated"] += 1
            breaker.record_success()

        except LLMCallError as e:
            print(f"[gate2] {sid} 오류: {e}")
            stats["errors"] += 1
            breaker.record_failure(str(e))
        except Exception as e:
            print(f"[gate2] {sid} 오류: {e}")
            stats["errors"] += 1

    return stats


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--source-ids", nargs="*")
    args = p.parse_args()
    result = run(args.source_ids)
    print(f"Gate2 완료 — 평가: {result['evaluated']}건, 오류: {result['errors']}건")

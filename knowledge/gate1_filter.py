#!/usr/bin/env python3
"""knowledge/gate1_filter.py — Gate 1: Haiku 하드필터.

명백한 탈락만 제거한다. 판단이 애매하면 통과시켜 Gate 2로 넘긴다.
거부 조건: 섹터 완전 무관 | 목차·광고 페이지 | 명백 중복
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.db import db_conn
from knowledge.llm_client import MODEL_FILTER, CircuitBreaker, LLMCallError, call_json
from knowledge.taxonomy import sector_prompt_block


def _system_prompt() -> str:
    return f"""\
당신은 리서치 인텔리전스 시스템의 1차 관련성 필터입니다.
대상 섹터는 다음과 같습니다 (1차 구현 대상):
{sector_prompt_block()}

규칙: 명백하게 탈락인 경우만 거부하세요. 애매하면 반드시 통과시키세요.

거부 조건(이 경우에만 pass:false):
- 위 섹터와 완전히 무관한 주제 (소비재, 스포츠, 엔터테인먼트 등, AI/에너지 각도 없음)
- 목차·인덱스 페이지 (실질 콘텐츠 없음)
- 순수 홍보·광고 (분석·데이터 없음)
- 명백한 중복 (제목+날짜가 기존과 동일)

JSON만 반환하세요 (다른 텍스트 없음):
{{"pass": true, "reason": "한 줄 판정 근거 (한국어)"}}"""


def _call_haiku(title: str, content_preview: str) -> dict:
    return call_json(
        model=MODEL_FILTER,
        system=_system_prompt(),
        user_content=f"제목: {title}\n\n본문 앞부분:\n{content_preview[:800]}",
        max_tokens=128,
    )


def _update_status(sid: str, status: str, note: str) -> None:
    """레코드별 즉시 커밋 — LLM 호출 사이에 트랜잭션을 열어두지 않는다."""
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sources SET status=%s, gate_note=%s, updated_at=NOW() WHERE id=%s",
                (status, note, str(sid)),
            )


def run(source_ids: list[str] | None = None) -> dict[str, int]:
    """pending 소스를 Gate 1으로 필터링. 반환값: {passed, rejected} 카운트."""
    stats = {"passed": 0, "rejected": 0}

    # SELECT만 수행하고 즉시 커밋·연결 종료 — LLM 호출 중 idle-in-transaction 방지
    with db_conn() as conn:
        with conn.cursor() as cur:
            if source_ids:
                cur.execute(
                    "SELECT id, title, content_text, issuer FROM sources WHERE status='pending' AND id = ANY(%s)",
                    (source_ids,),
                )
            else:
                cur.execute(
                    "SELECT id, title, content_text, issuer FROM sources WHERE status='pending'"
                )
            rows = cur.fetchall()
    # 커넥션은 여기서 이미 닫힘 — 아래 API 호출 루프 동안 DB 트랜잭션을 열어두지 않는다.
    # 이후 상태 변경은 _update_status()가 레코드별 짧은 커넥션으로 처리한다.

    breaker = CircuitBreaker(threshold=5)

    for row in rows:
        sid = row["id"]
        title = row["title"] or ""
        content = row["content_text"] or ""

        if not content.strip():
            print(f"[gate1] {title[:50]} — content 없음, 거부")
            _update_status(str(sid), "rejected", "Gate1: content_text 없음")
            stats["rejected"] += 1
            continue

        # 100자 미만은 LLM 판단 불가 — 통과 처리(Gate2에서 밀도 심사)
        if len(content.strip()) < 100:
            stats["passed"] += 1
            continue

        try:
            result = _call_haiku(title, content)
        except LLMCallError as e:
            print(f"[gate1] {sid} API 오류: {e} — 통과 처리")
            stats["passed"] += 1
            breaker.record_failure(str(e))
            continue

        breaker.record_success()
        if result.get("pass", True):
            stats["passed"] += 1
        else:
            reason = result.get("reason", "Gate1 탈락")
            _update_status(str(sid), "rejected", f"Gate1: {reason}")
            print(f"[gate1] REJECT {title[:50]} — {reason}")
            stats["rejected"] += 1

    return stats


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--source-ids", nargs="*")
    args = p.parse_args()
    result = run(args.source_ids)
    print(f"Gate1 완료 — 통과: {result['passed']}건, 거부: {result['rejected']}건")

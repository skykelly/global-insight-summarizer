#!/usr/bin/env python3
"""knowledge/gate1_filter.py — Gate 1: Haiku 하드필터.

명백한 탈락만 제거한다. 판단이 애매하면 통과시켜 Gate 2로 넘긴다.
거부 조건: 섹터 완전 무관 | 목차·광고 페이지 | 명백 중복
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import anthropic

from knowledge.db import db_conn

_CLIENT = anthropic.Anthropic()

_SYSTEM = """\
당신은 리서치 인텔리전스 시스템의 1차 관련성 필터입니다.
대상 섹터는 두 가지입니다:
1. 전력기기(power_equipment): 전력망 인프라, 변압기, HVDC, ESS, 신재생에너지 인프라 등
2. AI 반도체(ai_semis): GPU, HBM, CoWoS, AI 가속기, 데이터센터 칩, AI 인프라 투자 등

규칙: 명백하게 탈락인 경우만 거부하세요. 애매하면 반드시 통과시키세요.

거부 조건(이 경우에만 pass:false):
- 두 섹터와 완전히 무관한 주제 (소비재, 스포츠, 엔터테인먼트 등, AI/에너지 각도 없음)
- 목차·인덱스 페이지 (실질 콘텐츠 없음)
- 순수 홍보·광고 (분석·데이터 없음)
- 명백한 중복 (제목+날짜가 기존과 동일)

JSON만 반환하세요 (다른 텍스트 없음):
{"pass": true, "reason": "한 줄 판정 근거 (한국어)"}"""


def _call_haiku(title: str, content_preview: str) -> dict:
    msg = _CLIENT.messages.create(
        model="claude-haiku-4-5",
        max_tokens=128,
        system=_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"제목: {title}\n\n본문 앞부분:\n{content_preview[:800]}"
        }],
    )
    return json.loads(msg.content[0].text)


def run(source_ids: list[str] | None = None) -> dict[str, int]:
    """pending 소스를 Gate 1으로 필터링. 반환값: {passed, rejected} 카운트."""
    stats = {"passed": 0, "rejected": 0}

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

        for row in rows:
            sid = row["id"]
            title = row["title"] or ""
            content = row["content_text"] or ""

            if not content.strip():
                print(f"[gate1] {title[:50]} — content 없음, 거부")
                with db_conn() as conn2:
                    with conn2.cursor() as cur2:
                        cur2.execute(
                            "UPDATE sources SET status='rejected', gate_note=%s, updated_at=NOW() WHERE id=%s",
                            ("Gate1: content_text 없음", str(sid)),
                        )
                stats["rejected"] += 1
                continue

            try:
                result = _call_haiku(title, content)
            except Exception as e:
                print(f"[gate1] {sid} API 오류: {e} — 통과 처리")
                stats["passed"] += 1
                continue

            if result.get("pass", True):
                stats["passed"] += 1
            else:
                reason = result.get("reason", "Gate1 탈락")
                with db_conn() as conn2:
                    with conn2.cursor() as cur2:
                        cur2.execute(
                            "UPDATE sources SET status='rejected', gate_note=%s, updated_at=NOW() WHERE id=%s",
                            (f"Gate1: {reason}", str(sid)),
                        )
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

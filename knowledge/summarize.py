#!/usr/bin/env python3
"""knowledge/summarize.py — 한국어 6섹션 요약 (auto_accepted / accepted 문서만).

Hard Rule: 원문 구조 모방 금지. 항상 6섹션 고정 포맷 사용.
6섹션: 핵심 주장 / 주요 수치 및 전망 / 근거 및 분석 방법론 /
        리스크 및 불확실성 / 시사점 (한국 시장 관련) / 출처 정보
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.db import db_conn
from knowledge.llm_client import MODEL_MAIN, call_text

_SYSTEM = """\
당신은 글로벌 기관 리서치를 한국어로 지식화하는 애널리스트입니다.

아래 6섹션 고정 포맷으로 요약을 작성하세요.
원문의 순서나 구조를 그대로 따르지 마세요 (Hard Rule: 원문 구조 모방 금지).
각 섹션은 리서치 인사이트 중심으로 재구성합니다.

## 1. 핵심 주장
핵심 투자 주제와 가장 중요한 전망을 2~3문장으로.

## 2. 주요 수치 및 전망
구체적 수치, CAGR, 시장 규모, 가격 전망 등을 불릿으로. 근거가 없는 수치는 포함 금지.

## 3. 근거 및 분석 방법론
주장의 논리적 근거, 데이터 소스, 분석 방법론을 간략히.

## 4. 리스크 및 불확실성
문서에서 명시하거나 암시하는 하방 리스크와 불확실 요인.

## 5. 시사점 (한국 시장 관련)
전력기기 또는 AI 반도체 한국 기업·시장에 미치는 영향이나 투자 시사점.
원문에 명시되지 않은 경우 "원문에서 직접 언급 없음"으로 표기 후 추론 가능한 시사점만.

## 6. 출처 정보
발행처 | 발행일 | 원문 URL"""


def _summarize(title: str, issuer: str, published_at: str, content: str) -> str:
    return call_text(
        model=MODEL_MAIN,
        system=_SYSTEM,
        user_content=f"발행처: {issuer}\n발행일: {published_at}\n제목: {title}\n\n원문:\n{content[:8000]}",
        max_tokens=2000,
    )


def run(source_ids: list[str] | None = None) -> dict[str, int]:
    """auto_accepted/accepted 소스에 대해 요약 생성."""
    stats = {"summarized": 0, "skipped": 0, "errors": 0}

    with db_conn() as conn:
        with conn.cursor() as cur:
            if source_ids:
                cur.execute(
                    """SELECT s.id, s.title, s.issuer, s.published_at, s.url, s.content_text
                       FROM sources s
                       WHERE s.status IN ('auto_accepted','accepted')
                         AND NOT EXISTS (SELECT 1 FROM summaries sm WHERE sm.source_id = s.id)
                         AND s.id = ANY(%s)""",
                    (source_ids,),
                )
            else:
                cur.execute(
                    """SELECT s.id, s.title, s.issuer, s.published_at, s.url, s.content_text
                       FROM sources s
                       WHERE s.status IN ('auto_accepted','accepted')
                         AND NOT EXISTS (SELECT 1 FROM summaries sm WHERE sm.source_id = s.id)"""
                )
            rows = cur.fetchall()

    for row in rows:
        sid = str(row["id"])
        title = row["title"] or ""
        content = row["content_text"] or ""

        if not content.strip():
            print(f"[summarize] {title[:50]} — content_text 없음, 건너뜀")
            stats["skipped"] += 1
            continue

        try:
            summary = _summarize(
                title,
                row["issuer"] or "",
                str(row["published_at"] or ""),
                content,
            )

            with db_conn() as conn2:
                with conn2.cursor() as cur2:
                    cur2.execute(
                        "INSERT INTO summaries (source_id, content_ko, model) VALUES (%s, %s, %s)",
                        (sid, summary, MODEL_MAIN),
                    )
            print(f"[summarize] 완료: {title[:50]}")
            stats["summarized"] += 1

        except Exception as e:
            print(f"[summarize] {sid} 오류: {e}")
            stats["errors"] += 1

    return stats


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--source-ids", nargs="*")
    args = p.parse_args()
    result = run(args.source_ids)
    print(f"요약 완료 — 생성: {result['summarized']}건, 건너뜀: {result['skipped']}건, 오류: {result['errors']}건")

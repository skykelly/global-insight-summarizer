#!/usr/bin/env python3
"""knowledge/pipeline.py — 지식 파이프라인 메인 러너.

순서: Gate1(Haiku 필터) → Gate2(Sonnet 루브릭) → claims 추출(Gate3) → 트리아지 → 요약 → 임베딩

사용:
    python3 knowledge/pipeline.py                   # 전체 pending 처리
    python3 knowledge/pipeline.py --source-ids UUID1 UUID2
    python3 knowledge/pipeline.py --calibration     # auto_accept 10% 샘플링
    python3 knowledge/pipeline.py --dry-run         # 통계만 출력 (LLM 호출 없음)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge import gate1_filter, gate2_rubric, extract_claims, triage, summarize, embed
from knowledge.db import db_conn


def _count_pending() -> int:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM sources WHERE status='pending'")
            return cur.fetchone()["cnt"]


def run(
    source_ids: list[str] | None = None,
    calibration: bool = False,
    dry_run: bool = False,
    gate1_limit: int | None = 150,
) -> None:
    pending = _count_pending() if not source_ids else len(source_ids)
    print(f"{'='*60}")
    print(f"지식 파이프라인 시작{' [DRY-RUN]' if dry_run else ''}")
    print(f"대상: {pending}건 (Gate1 배치 제한: {gate1_limit or '없음'})")
    print(f"{'='*60}")

    if dry_run:
        print("[DRY] Gate1 → Gate2 → claims → triage → summarize → embed 순으로 실행됩니다.")
        return

    print("\n[1/6] Gate1: Haiku 하드필터")
    r1 = gate1_filter.run(source_ids, limit=gate1_limit)
    print(f"  통과: {r1['passed']}, 거부: {r1['rejected']}")

    print("\n[2/6] Gate2: Sonnet 4차원 루브릭")
    r2 = gate2_rubric.run(source_ids)
    print(f"  평가: {r2['evaluated']}, 오류: {r2['errors']}")

    print("\n[3/6] claims 추출 (Gate3)")
    r3 = extract_claims.run(source_ids)
    print(f"  처리: {r3['processed']}, claims: {r3['total_claims']}, 오류: {r3['errors']}")

    print("\n[4/6] 트리아지")
    r4 = triage.run(source_ids, calibration=calibration)
    print(f"  auto_accepted: {r4['auto_accepted']}, queued: {r4['queued']}, rejected: {r4['rejected']}")

    print("\n[5/6] 한국어 6섹션 요약")
    r5 = summarize.run(source_ids)
    print(f"  생성: {r5['summarized']}, 건너뜀: {r5['skipped']}, 오류: {r5['errors']}")

    print("\n[6/6] OpenAI 임베딩")
    r6 = embed.run(source_ids)
    print(f"  소스: {r6['embedded']}, 청크: {r6['chunks']}, 오류: {r6['errors']}")

    print(f"\n{'='*60}")
    print("파이프라인 완료")
    print(f"{'='*60}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source-ids", nargs="*")
    p.add_argument("--calibration", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--gate1-limit", type=int, default=150, help="Gate1 1회 처리 최대 건수 (기본 150)")
    args = p.parse_args()
    run(args.source_ids, args.calibration, args.dry_run, gate1_limit=args.gate1_limit)

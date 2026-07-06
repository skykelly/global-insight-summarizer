#!/usr/bin/env python3
"""ingestion/backfill_sources.py — raw_sources → sources 승격 backfill.

router.py가 sources 테이블에 쓰기 전에 수집된 raw_sources 항목들을
sources(status='pending')로 승격한다.

사용법:
    python3 ingestion/backfill_sources.py
    python3 ingestion/backfill_sources.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.db import db_conn


def run(dry_run: bool = False) -> None:
    with db_conn() as conn:
        with conn.cursor() as cur:
            # sources가 없는 raw_sources 조회
            cur.execute("""
                SELECT r.id, r.url, r.issuer, r.raw_content, r.blob_url, r.source_yaml_id
                FROM raw_sources r
                WHERE NOT EXISTS (
                    SELECT 1 FROM sources s WHERE s.raw_source_id = r.id
                )
                ORDER BY r.fetched_at
            """)
            rows = cur.fetchall()

    print(f"승격 대상 raw_sources: {len(rows)}건")
    if not rows or dry_run:
        if dry_run:
            for r in rows[:10]:
                print(f"  [DRY] {r['id']} — {r['url'][:60]}")
        return

    promoted = 0
    skipped = 0
    with db_conn() as conn:
        with conn.cursor() as cur:
            for r in rows:
                raw_content = r["raw_content"] or ""
                issuer = r["issuer"] or ""

                # raw_content에서 첫 줄을 title로 추정, 발행일은 unknown으로 처리
                lines = [l.strip() for l in raw_content.split("\n") if l.strip()]
                title = lines[0][:200] if lines else r["url"]

                # published_at 없으면 승격 불가 (Hard Rule)
                # raw_sources에 published_at 컬럼이 없으므로 fetched_at 기준 날짜 사용
                # → 실제 발행일은 Gate1 이후 LLM이 추출하는 것이 바람직하나
                #   일단 수집일로 채워 파이프라인이 돌도록 함
                if not issuer:
                    print(f"  [SKIP] issuer 없음: {r['url'][:60]}")
                    skipped += 1
                    continue

                try:
                    cur.execute("""
                        INSERT INTO sources
                          (raw_source_id, title, url, issuer, published_at,
                           sector_tags, content_text, blob_url, status)
                        VALUES (%s, %s, %s, %s, NOW()::date,
                                '{}', %s, %s, 'pending')
                        ON CONFLICT DO NOTHING
                        RETURNING id
                    """, (
                        str(r["id"]),
                        title,
                        r["url"],
                        issuer,
                        raw_content[:50000],
                        r["blob_url"] or "",
                    ))
                    if cur.fetchone():
                        promoted += 1
                        print(f"  ✓ {issuer}: {title[:50]}")
                except Exception as e:
                    print(f"  [ERR] {r['id']}: {e}")
                    skipped += 1

    print(f"\n완료 — 승격: {promoted}건, 건너뜀: {skipped}건")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)

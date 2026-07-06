#!/usr/bin/env python3
"""knowledge/triage.py — §2.5 트리아지 3분류.

Gate 2 점수 + claims 건수 기반으로 분류:
  auto_accepted: 전 차원 >= AUTO_ACCEPT_MIN AND claims >= AUTO_ACCEPT_CLAIMS
  rejected:      어느 차원 <= AUTO_REJECT_MAX OR claims == 0
  queued:        그 외 경계 구간

임계값은 triage_config.yaml에서 로드 (하드코딩 금지).
캘리브레이션 모드: auto_accept의 CALIBRATION_SAMPLE_RATE 비율도 queued에 병행 등록.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from knowledge.db import db_conn

_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _ROOT / "knowledge" / "triage_config.yaml"


def _load_config() -> dict:
    return yaml.safe_load(_CONFIG_PATH.read_text())


def _count_claims(source_id: str) -> int:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM claims WHERE source_id=%s", (source_id,))
            return cur.fetchone()["cnt"]


def _decide(quality: dict, claims_count: int, cfg: dict) -> str:
    min_val = min(quality.get(d, 0) for d in ("relevance", "density", "authority", "novelty"))
    all_dims_ok = all(quality.get(d, 0) >= cfg["auto_accept_min"] for d in ("relevance", "density", "authority", "novelty"))

    if min_val <= cfg["auto_reject_max"] or claims_count == 0:
        return "rejected"
    if all_dims_ok and claims_count >= cfg["auto_accept_claims"]:
        return "auto_accepted"
    return "queued"


def run(
    source_ids: list[str] | None = None,
    calibration: bool = False,
) -> dict[str, int]:
    """pending 소스 트리아지 실행. status 업데이트."""
    cfg = _load_config()
    stats = {"auto_accepted": 0, "queued": 0, "rejected": 0, "skipped": 0}

    with db_conn() as conn:
        with conn.cursor() as cur:
            if source_ids:
                cur.execute(
                    "SELECT id, title, quality FROM sources WHERE status='pending' AND id = ANY(%s)",
                    (source_ids,),
                )
            else:
                cur.execute(
                    "SELECT id, title, quality FROM sources WHERE status='pending'"
                )
            rows = cur.fetchall()

    for row in rows:
        sid = str(row["id"])
        title = row["title"] or ""
        quality_raw = row["quality"]

        if not quality_raw:
            print(f"[triage] {title[:50]} — quality 없음 (Gate2 미실행), 건너뜀")
            stats["skipped"] += 1
            continue

        quality = quality_raw if isinstance(quality_raw, dict) else json.loads(quality_raw)
        claims_count = _count_claims(sid)
        decision = _decide(quality, claims_count, cfg)

        with db_conn() as conn2:
            with conn2.cursor() as cur2:
                cur2.execute(
                    "UPDATE sources SET status=%s, updated_at=NOW() WHERE id=%s",
                    (decision, sid),
                )

        print(f"[triage] {title[:50]} → {decision} (claims={claims_count}, quality={quality})")
        stats[decision] += 1

        # 캘리브레이션: auto_accepted 중 일부를 queued에도 병행 등록 (샘플 체크용)
        if calibration and decision == "auto_accepted":
            if random.random() < cfg.get("calibration_sample_rate", 0.10):
                # gate_note에 캘리브레이션 샘플임을 기록
                with db_conn() as conn3:
                    with conn3.cursor() as cur3:
                        cur3.execute(
                            "UPDATE sources SET gate_note = COALESCE(gate_note,'') || ' [CAL-SAMPLE]' WHERE id=%s",
                            (sid,),
                        )
                print(f"  → 캘리브레이션 샘플로 표시됨")

    return stats


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--source-ids", nargs="*")
    p.add_argument("--calibration", action="store_true", help="auto_accept의 일부를 queued 병행 등록")
    args = p.parse_args()
    result = run(args.source_ids, args.calibration)
    print(f"트리아지 완료 — auto_accepted: {result['auto_accepted']}, queued: {result['queued']}, rejected: {result['rejected']}, skipped: {result['skipped']}")

"""knowledge/taxonomy.py — configs/taxonomy.yaml 로더.

섹터·컨셉의 단일 진실은 configs/taxonomy.yaml. gate1_filter/gate2_rubric/
extract_claims의 프롬프트, generate_wiki의 섹터 목록이 전부 여기서 로드한다.
하드코딩 금지 — 새 섹터·컨셉 추가는 이 yaml 수정만으로 전파되어야 한다.
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parent.parent
_TAXONOMY_PATH = _ROOT / "configs" / "taxonomy.yaml"


@functools.lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return yaml.safe_load(_TAXONOMY_PATH.read_text(encoding="utf-8"))


def all_sectors() -> list[dict]:
    """전체 10개 섹터 (active 여부 무관)."""
    return _load()["sectors"]


def active_sectors() -> list[dict]:
    """1차 구현 대상 섹터만 (active: true)."""
    return [s for s in all_sectors() if s.get("active")]


def sector_ids(active_only: bool = False) -> list[str]:
    sectors = active_sectors() if active_only else all_sectors()
    return [s["id"] for s in sectors]


def sector_label(sector_id: str) -> str:
    for s in all_sectors():
        if s["id"] == sector_id:
            return s["name"]
    return sector_id


def all_concepts() -> list[dict]:
    return _load()["concepts"]


def concept_ids() -> list[str]:
    return [c["id"] for c in all_concepts()]


def concept_by_id(concept_id: str) -> dict | None:
    for c in all_concepts():
        if c["id"] == concept_id:
            return c
    return None


def concepts_for_sector(sector_id: str) -> list[dict]:
    return [c for c in all_concepts() if sector_id in c.get("related_sectors", [])]


def sector_prompt_block(active_only: bool = True) -> str:
    """LLM 프롬프트에 삽입할 섹터 목록 텍스트.
    예: "1. AI 인프라·데이터센터(ai_dc): AI CapEx의 물리 인프라 확산 ..."
    """
    sectors = active_sectors() if active_only else all_sectors()
    lines = [
        f"{i}. {s['name']}({s['id']}): {s['description']}"
        for i, s in enumerate(sectors, start=1)
    ]
    return "\n".join(lines)

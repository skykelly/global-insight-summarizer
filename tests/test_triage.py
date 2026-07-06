"""트리아지 로직 단위 테스트.

LLM/DB 없이 _decide() 함수의 경계 케이스를 검증한다.
claims=0 승격 차단 + 저밀도 홍보 문서 auto_reject가 핵심 검증 대상.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# triage._decide를 직접 임포트해서 DB/LLM 없이 테스트
from knowledge.triage import _decide

# 기본 config (triage_config.yaml 기본값과 동일)
DEFAULT_CFG = {
    "auto_accept_min": 4,
    "auto_accept_claims": 2,
    "auto_reject_max": 2,
}


class TestAutoAccept:
    """전 차원 ≥4 AND claims ≥2 → auto_accepted."""

    def test_all_scores_4_claims_2(self):
        q = {"relevance": 4, "density": 4, "authority": 4, "novelty": 4}
        assert _decide(q, 2, DEFAULT_CFG) == "auto_accepted"

    def test_all_scores_5_claims_5(self):
        q = {"relevance": 5, "density": 5, "authority": 5, "novelty": 5}
        assert _decide(q, 5, DEFAULT_CFG) == "auto_accepted"

    def test_mixed_high_scores_claims_3(self):
        q = {"relevance": 5, "density": 4, "authority": 4, "novelty": 4}
        assert _decide(q, 3, DEFAULT_CFG) == "auto_accepted"


class TestAutoReject:
    """어느 차원 ≤2 OR claims=0 → rejected."""

    def test_claims_zero_rejects(self):
        """claims=0이면 점수와 무관하게 반드시 rejected (Hard Rule)."""
        q = {"relevance": 5, "density": 5, "authority": 5, "novelty": 5}
        assert _decide(q, 0, DEFAULT_CFG) == "rejected"

    def test_low_relevance_rejects(self):
        q = {"relevance": 2, "density": 4, "authority": 4, "novelty": 4}
        assert _decide(q, 3, DEFAULT_CFG) == "rejected"

    def test_low_density_rejects(self):
        q = {"relevance": 4, "density": 2, "authority": 4, "novelty": 4}
        assert _decide(q, 3, DEFAULT_CFG) == "rejected"

    def test_low_authority_rejects(self):
        q = {"relevance": 4, "density": 4, "authority": 1, "novelty": 4}
        assert _decide(q, 3, DEFAULT_CFG) == "rejected"

    def test_low_novelty_rejects(self):
        q = {"relevance": 4, "density": 4, "authority": 4, "novelty": 2}
        assert _decide(q, 3, DEFAULT_CFG) == "rejected"

    def test_zero_score_any_dim_rejects(self):
        """점수 0은 누락된 경우 — 반드시 rejected."""
        q = {"relevance": 4, "density": 4, "authority": 4, "novelty": 0}
        assert _decide(q, 3, DEFAULT_CFG) == "rejected"

    def test_promo_doc_pattern_rejects(self):
        """저밀도 홍보 문서 패턴: authority=2, density=1, claims=0."""
        q = {"relevance": 2, "density": 1, "authority": 2, "novelty": 1}
        assert _decide(q, 0, DEFAULT_CFG) == "rejected"


class TestQueued:
    """경계 구간 → queued."""

    def test_claims_1_below_threshold(self):
        """claims=1 < auto_accept_claims(2) → queued (점수 충분해도)."""
        q = {"relevance": 4, "density": 4, "authority": 4, "novelty": 4}
        assert _decide(q, 1, DEFAULT_CFG) == "queued"

    def test_one_score_3(self):
        """한 차원이 3 (reject_max=2 초과, accept_min=4 미달) → queued."""
        q = {"relevance": 3, "density": 4, "authority": 4, "novelty": 4}
        assert _decide(q, 3, DEFAULT_CFG) == "queued"

    def test_boundary_novelty_3(self):
        """novelty=3 경계 케이스 (gc05 패턴)."""
        q = {"relevance": 4, "density": 3, "authority": 4, "novelty": 3}
        assert _decide(q, 1, DEFAULT_CFG) == "queued"

    def test_all_3_claims_2(self):
        """전 차원 3점, claims 충분 → queued."""
        q = {"relevance": 3, "density": 3, "authority": 3, "novelty": 3}
        assert _decide(q, 2, DEFAULT_CFG) == "queued"


class TestClaimsZeroHardRule:
    """claims=0이면 어떤 점수에서도 knowledge_items 승격 경로가 없음을 증명."""

    @pytest.mark.parametrize("scores", [
        {"relevance": 5, "density": 5, "authority": 5, "novelty": 5},
        {"relevance": 4, "density": 4, "authority": 4, "novelty": 4},
        {"relevance": 3, "density": 3, "authority": 3, "novelty": 3},
    ])
    def test_claims_zero_never_auto_accepted(self, scores: dict):
        """claims=0 문서는 절대 auto_accepted가 되지 않는다."""
        result = _decide(scores, 0, DEFAULT_CFG)
        assert result != "auto_accepted", \
            f"claims=0인데 auto_accepted 판정: scores={scores}"
        assert result == "rejected"


class TestConfigOverride:
    """임계값 조정 시 동작 확인 (R2 루틴이 config 수정하는 시나리오)."""

    def test_stricter_config(self):
        """더 엄격한 config — auto_accept_min=5로 올리면 4점은 queued."""
        strict_cfg = {**DEFAULT_CFG, "auto_accept_min": 5}
        q = {"relevance": 4, "density": 4, "authority": 4, "novelty": 4}
        assert _decide(q, 3, strict_cfg) == "queued"

    def test_looser_reject_config(self):
        """auto_reject_max=1로 낮추면 2점 차원도 통과 가능."""
        loose_cfg = {**DEFAULT_CFG, "auto_reject_max": 1}
        q = {"relevance": 4, "density": 4, "authority": 4, "novelty": 2}
        # novelty=2 > auto_reject_max=1, 전 차원 4 이상 아님 → queued
        assert _decide(q, 3, loose_cfg) == "queued"

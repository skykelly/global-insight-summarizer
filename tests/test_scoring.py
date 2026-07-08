"""scoring/anomaly/trend_report 핵심 로직 테스트 — DB 없이 순수 함수 대상."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge import scoring, anomaly, trend_report


# ── scoring.importance_score (순수 함수, DB 불요) ────────────────────────────

class TestImportanceScore:
    def test_empty_items_returns_zero(self):
        result = scoring.importance_score([])
        assert result["score"] == 0.0
        assert result["metric_count"] == 0

    def test_metrics_boost_market_size_and_capex(self):
        items = [{
            "claim_ko": "AI 데이터센터 투자가 2027년까지 $800B 규모로 성장",
            "metrics": {"시장규모": {"value": "$800B", "span": "$800 billion market"}},
            "evidence": {"evidence_type": "text"},
            "time_horizon": "long_term",
        }]
        result = scoring.importance_score(items)
        assert result["metric_count"] == 1
        assert result["details"]["market_size_score"] > 0
        assert result["details"]["capex_score"] > 0
        assert result["score"] > 0

    def test_bottleneck_keyword_detected(self):
        items = [{"claim_ko": "공급망 병목으로 수주잔고 지연", "metrics": None, "evidence": None, "time_horizon": None}]
        result = scoring.importance_score(items)
        assert result["details"]["bottleneck_score"] == 100.0
        assert result["details"]["supply_chain_criticality_score"] == 100.0

    def test_structural_horizon_scores_higher_than_near_term(self):
        near = scoring.importance_score([{"claim_ko": "x", "metrics": None, "evidence": None, "time_horizon": "near_term"}])
        structural = scoring.importance_score([{"claim_ko": "x", "metrics": None, "evidence": None, "time_horizon": "structural"}])
        assert structural["details"]["time_horizon_score"] > near["details"]["time_horizon_score"]

    def test_score_bounded_0_100(self):
        items = [{
            "claim_ko": "병목 공급망 정책 예산 CAGR 급증 성장률",
            "metrics": {"m": {"value": "$1T", "span": "$1 trillion"}},
            "evidence": {"evidence_type": "table"},
            "time_horizon": "structural",
        }] * 5
        result = scoring.importance_score(items)
        assert 0 <= result["score"] <= 100


# ── scoring._normalize ────────────────────────────────────────────────────────

class TestNormalize:
    def test_zero_max_returns_zero(self):
        assert scoring._normalize(5, 0) == 0.0

    def test_clamped_at_100(self):
        assert scoring._normalize(50, 10) == 100.0

    def test_proportional(self):
        assert scoring._normalize(5, 10) == 50.0


# ── scoring.mention_score (DB 호출 mock) ─────────────────────────────────────

class TestMentionScore:
    def test_mention_score_with_mocked_prev_count(self):
        items = [
            {"issuer": "Goldman Sachs", "related_sectors": ["power"], "published_at": "2026-07-05"},
            {"issuer": "McKinsey", "related_sectors": None, "published_at": "2026-07-06"},
        ]
        with patch.object(scoring, "_fetch_prev_count", return_value=1):
            result = scoring.mention_score("sector", "ai_dc", items, "2026-07-01", "2026-07-08")
        assert result["mention_count"] == 2
        assert result["source_diversity"] == 2
        assert 0 <= result["score"] <= 100

    def test_zero_prev_count_gives_full_momentum(self):
        items = [{"issuer": "GS", "related_sectors": None, "published_at": "2026-07-05"}]
        with patch.object(scoring, "_fetch_prev_count", return_value=0):
            result = scoring.mention_score("sector", "pm", items, "2026-07-01", "2026-07-08")
        assert result["momentum_score"] == 100.0


# ── anomaly._extract_number ───────────────────────────────────────────────────

class TestExtractNumber:
    def test_extracts_dollar_amount(self):
        assert anomaly._extract_number("$800B") == 800.0

    def test_extracts_percentage(self):
        assert anomaly._extract_number("35%") == 35.0

    def test_extracts_with_comma(self):
        assert anomaly._extract_number("1,200") == 1200.0

    def test_none_when_no_number(self):
        assert anomaly._extract_number("no digits here") is None


# ── trend_report._quadrant ────────────────────────────────────────────────────

class TestQuadrant:
    def test_high_high(self):
        assert trend_report._quadrant(80, 80) == "High Mention / High Importance"

    def test_high_mention_low_importance(self):
        assert trend_report._quadrant(78, 40) == "High Mention / Low Importance"

    def test_low_mention_high_importance(self):
        assert trend_report._quadrant(30, 82) == "Low Mention / High Importance"

    def test_weak_signal_default(self):
        assert trend_report._quadrant(20, 30) == "Emerging Weak Signal"

    def test_none_values_treated_as_zero(self):
        assert trend_report._quadrant(None, None) == "Emerging Weak Signal"

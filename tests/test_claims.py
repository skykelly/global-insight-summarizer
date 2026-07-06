"""golden_claims 픽스처 스키마 검증 테스트.

LLM 호출 없이 픽스처 JSON의 구조와 필수 필드를 검증한다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "golden_claims"
REQUIRED_CLAIM_FIELDS = {"issuer", "sector", "claim_ko", "published_at"}
VALID_DIRECTIONS = {"bullish", "bearish", "neutral"}
VALID_SECTORS = {"power_equipment", "ai_semis"}


def load_fixtures() -> list[tuple[str, dict]]:
    return [(f.stem, json.loads(f.read_text())) for f in sorted(FIXTURES_DIR.glob("*.json"))]


class TestFixtureStructure:
    """픽스처 파일 자체의 구조 검증."""

    @pytest.mark.parametrize("name,fixture", load_fixtures())
    def test_has_meta(self, name: str, fixture: dict):
        assert "_meta" in fixture, f"{name}: _meta 섹션 없음"
        assert "issuer" in fixture["_meta"]
        assert "published_at" in fixture["_meta"]

    @pytest.mark.parametrize("name,fixture", load_fixtures())
    def test_has_expected_claims(self, name: str, fixture: dict):
        assert "expected_claims" in fixture, f"{name}: expected_claims 섹션 없음"

    @pytest.mark.parametrize("name,fixture", load_fixtures())
    def test_has_validation_rules(self, name: str, fixture: dict):
        assert "validation_rules" in fixture, f"{name}: validation_rules 섹션 없음"


class TestClaimSchema:
    """각 expected_claims 항목의 스키마 검증."""

    @pytest.mark.parametrize("name,fixture", load_fixtures())
    def test_required_fields(self, name: str, fixture: dict):
        for i, claim in enumerate(fixture.get("expected_claims", [])):
            missing = REQUIRED_CLAIM_FIELDS - set(claim.keys())
            assert not missing, f"{name}[{i}]: 필수 필드 누락 {missing}"

    @pytest.mark.parametrize("name,fixture", load_fixtures())
    def test_direction_values(self, name: str, fixture: dict):
        for i, claim in enumerate(fixture.get("expected_claims", [])):
            if "direction" in claim and claim["direction"]:
                assert claim["direction"] in VALID_DIRECTIONS, \
                    f"{name}[{i}]: 잘못된 direction '{claim['direction']}'"

    @pytest.mark.parametrize("name,fixture", load_fixtures())
    def test_sector_values(self, name: str, fixture: dict):
        for i, claim in enumerate(fixture.get("expected_claims", [])):
            assert claim.get("sector") in VALID_SECTORS, \
                f"{name}[{i}]: 잘못된 sector '{claim.get('sector')}'"

    @pytest.mark.parametrize("name,fixture", load_fixtures())
    def test_metrics_have_span(self, name: str, fixture: dict):
        rules = fixture.get("validation_rules", {})
        if not rules.get("metrics_have_span", False):
            return
        for i, claim in enumerate(fixture.get("expected_claims", [])):
            for metric_name, metric_val in (claim.get("metrics") or {}).items():
                assert isinstance(metric_val, dict), \
                    f"{name}[{i}].metrics.{metric_name}: dict 아님"
                assert "span" in metric_val, \
                    f"{name}[{i}].metrics.{metric_name}: span 없음"
                assert len(metric_val["span"]) > 0, \
                    f"{name}[{i}].metrics.{metric_name}: span 빈 문자열"

    @pytest.mark.parametrize("name,fixture", load_fixtures())
    def test_published_at_format(self, name: str, fixture: dict):
        import re
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for i, claim in enumerate(fixture.get("expected_claims", [])):
            val = claim.get("published_at", "")
            assert pattern.match(val), \
                f"{name}[{i}]: published_at 형식 오류 '{val}'"


class TestValidationRules:
    """validation_rules 내 최소/최대 claims 건수 검증."""

    def test_gc03_promo_has_zero_claims(self):
        """홍보 보도자료 픽스처는 claims 0건이어야 한다."""
        fixture = json.loads((FIXTURES_DIR / "gc03_shallow_promo.json").read_text())
        assert fixture["expected_claims"] == [], "홍보 문서는 claims 빈 배열이어야 함"
        assert fixture["validation_rules"]["max_claims"] == 0

    def test_gc01_has_multiple_claims(self):
        """GS AI 인프라 픽스처는 claims 2건 이상이어야 한다."""
        fixture = json.loads((FIXTURES_DIR / "gc01_gs_ai_infra.json").read_text())
        assert len(fixture["expected_claims"]) >= fixture["validation_rules"]["min_claims"]

    def test_gc04_has_bearish_claim(self):
        """전력기기 약세 픽스처는 bearish direction 포함해야 한다."""
        fixture = json.loads((FIXTURES_DIR / "gc04_bearish_power.json").read_text())
        directions = [c.get("direction") for c in fixture["expected_claims"]]
        assert "bearish" in directions, "gc04에 bearish claim 없음"

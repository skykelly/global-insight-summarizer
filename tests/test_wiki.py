"""wiki 생성 + digest 구조 테스트.

LLM/DB 없이 출력 포맷과 필수 요소를 검증한다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.generate_wiki import SECTORS, SECTOR_LABELS, _fmt_claim
from knowledge.weekly_digest import _synthesize_digest

# ── _fmt_claim 테스트 ────────────────────────────────────────────────────────

class TestFmtClaim:
    """_fmt_claim 출력 포맷 검증."""

    def _make_claim(self, **kwargs) -> dict:
        return {
            "issuer": "Goldman Sachs",
            "sector": "semi",
            "claim_ko": "HBM 수요 급증 전망",
            "direction": "bullish",
            "horizon": "2027",
            "metrics": {"HBM CAGR": {"value": "40%", "span": "원문"}},
            "published_at": "2026-03-15",
            "valid_until": None,
            "supersedes": None,
            "entities": ["NVIDIA"],
            "outcome": None,
            "source_title": "Test",
            "source_url": "https://example.com",
            **kwargs,
        }

    def test_issuer_date_tag_present(self):
        """[issuer, YYYY-MM] 태그 필수."""
        line = _fmt_claim(self._make_claim())
        assert "[Goldman Sachs, 2026-03]" in line

    def test_direction_present(self):
        line = _fmt_claim(self._make_claim())
        assert "bullish" in line

    def test_horizon_present(self):
        line = _fmt_claim(self._make_claim())
        assert "2027" in line

    def test_metrics_value_present(self):
        line = _fmt_claim(self._make_claim())
        assert "40%" in line

    def test_claim_ko_present(self):
        line = _fmt_claim(self._make_claim())
        assert "HBM 수요 급증 전망" in line

    def test_no_metrics_still_works(self):
        line = _fmt_claim(self._make_claim(metrics=None))
        assert "[Goldman Sachs, 2026-03]" in line
        assert "HBM 수요 급증 전망" in line

    def test_bearish_direction(self):
        line = _fmt_claim(self._make_claim(direction="bearish"))
        assert "bearish" in line

    def test_neutral_direction(self):
        line = _fmt_claim(self._make_claim(direction="neutral"))
        assert "neutral" in line


# ── _synthesize_digest 테스트 ────────────────────────────────────────────────

class TestSynthesizeDigest:
    """_synthesize_digest 출력 구조 검증."""

    def _make_claim(self, sector="power", direction="bullish"):
        return {
            "issuer": "IMF",
            "sector": sector,
            "claim_ko": "테스트 주장",
            "direction": direction,
            "horizon": "2027",
            "metrics": None,
            "published_at": "2026-07-01",
            "valid_until": None,
            "supersedes": None,
            "source_title": "Test",
        }

    def _run(self, new_claims=None, view_changes=None):
        nc = new_claims or {"power": [], "semi": []}
        vc = view_changes or []
        return _synthesize_digest("2026-07-06", "2026-06-29", nc, vc)

    def test_has_frontmatter(self):
        out = self._run()
        assert out.startswith("---")
        assert "type: weekly-digest" in out
        assert "date: 2026-07-06" in out

    def test_has_sector_headings(self):
        out = self._run()
        for label in SECTOR_LABELS.values():
            assert label.split(" (")[0] in out  # 한글 이름만 체크

    def test_has_view_change_section(self):
        out = self._run()
        assert "뷰 변화 하이라이트" in out

    def test_claim_appears_in_output(self):
        nc = {"power": [self._make_claim("power")], "semi": []}
        out = self._run(new_claims=nc)
        assert "테스트 주장" in out
        assert "[IMF, 2026-07]" in out

    def test_view_change_rendered(self):
        vc = [{
            "issuer": "Goldman Sachs",
            "sector": "semi",
            "claim_ko": "새로운 뷰",
            "direction": "bearish",
            "published_at": "2026-07-05",
            "prev_claim_ko": "이전 뷰",
            "prev_direction": "bullish",
            "prev_published_at": "2026-01-01",
        }]
        out = self._run(view_changes=vc)
        assert "bullish → bearish" in out
        assert "새로운 뷰" in out

    def test_total_count_in_summary(self):
        nc = {
            "power": [self._make_claim("power")] * 3,
            "semi": [self._make_claim("semi")] * 2,
        }
        out = self._run(new_claims=nc)
        assert "5건" in out  # total 5건

    def test_empty_week_message(self):
        out = self._run()
        assert "없음" in out  # 빈 주간 메시지


# ── wiki 플레이스홀더 파일 존재 확인 ──────────────────────────────────────────

class TestWikiPlaceholders:
    """kb/wiki/ 플레이스홀더 파일이 존재하는지 확인."""

    def test_placeholders_exist(self):
        wiki_dir = Path(__file__).resolve().parent.parent / "kb" / "wiki"
        for sector in SECTORS:
            path = wiki_dir / f"{sector}.md"
            assert path.exists(), f"kb/wiki/{sector}.md 없음"

    def test_placeholders_have_frontmatter(self):
        wiki_dir = Path(__file__).resolve().parent.parent / "kb" / "wiki"
        for sector in SECTORS:
            content = (wiki_dir / f"{sector}.md").read_text()
            assert content.startswith("---"), f"{sector}.md frontmatter 없음"
            assert f"sector: {sector}" in content


# ── generate_wiki SECTORS/LABELS 상수 검증 ──────────────────────────────────

class TestSectorConstants:
    def test_all_sectors_have_labels(self):
        for s in SECTORS:
            assert s in SECTOR_LABELS, f"SECTOR_LABELS에 {s} 없음"

    def test_labels_are_nonempty(self):
        for s, label in SECTOR_LABELS.items():
            assert label.strip(), f"{s}의 label 비어있음"

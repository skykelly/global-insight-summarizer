"""스크래퍼 파싱 테스트 — 라이브 HTTP 호출 없이 fixtures HTML 대상."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures" / "scrapers"
sys.path.insert(0, str(ROOT))

from ingestion.channels.scrapers.base import BaseScraper
from ingestion.channels.scrapers.blackrock import BlackRockScraper
from ingestion.channels.scrapers.gs import GSScraper
from ingestion.channels.scrapers.jefferies import JefferiesScraper
from ingestion.channels.scrapers.jpm import JPMScraper
from ingestion.channels.scrapers.ms import MSScraper


# ── 공통 소스 config ──────────────────────────────────────────────────────────

def _source(src_id: str, name: str, issuer: str) -> dict:
    return {
        "id": src_id,
        "name": name,
        "issuer": issuer,
        "sector_tags": ["power", "semi"],
    }


# ── GS ───────────────────────────────────────────────────────────────────────

class TestGSScraper:
    def setup_method(self):
        self.source = _source("gs_insights", "Goldman Sachs Insights", "Goldman Sachs")
        self.scraper = GSScraper(self.source)
        self.html = (FIXTURES / "gs_sample.html").read_text()
        self.soup = BeautifulSoup(self.html, "lxml")

    def test_extracts_articles_from_fixture(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        assert len(stubs) >= 2

    def test_title_from_gs_card(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        titles = [s["title"] for s in stubs]
        assert any("AI and Power Demand" in t for t in titles)

    def test_date_from_gs_card_meta(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        dated = [s for s in stubs if s.get("published_at")]
        assert len(dated) >= 1
        assert dated[0]["published_at"] == "2025-05-15"

    def test_skips_index_link(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        urls = [s["url"] for s in stubs]
        assert not any(u.rstrip("/") == "https://www.goldmansachs.com/insights" for u in urls)

    def test_normalize_returns_required_fields(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        article = self.scraper.normalize(stubs[0], "Sample content")
        assert article["issuer"] == "Goldman Sachs"
        assert article["source_yaml_id"] == "gs_insights"
        assert "sector_tags" in article


# ── JPM ──────────────────────────────────────────────────────────────────────

class TestJPMScraper:
    def setup_method(self):
        self.source = _source("jpm_insights", "J.P. Morgan Insights", "JPMorgan")
        self.scraper = JPMScraper(self.source)
        self.html = (FIXTURES / "jpm_sample.html").read_text()
        self.soup = BeautifulSoup(self.html, "lxml")

    def test_extracts_articles_from_fixture(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        assert len(stubs) >= 2

    def test_title_from_heading(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        titles = [s["title"] for s in stubs]
        assert any("Power Grid" in t for t in titles)

    def test_skips_bare_index_link(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        urls = [s["url"] for s in stubs]
        assert not any(u.rstrip("/") == "https://www.jpmorgan.com/insights" for u in urls)

    def test_jsonld_date_extraction(self):
        soup = BeautifulSoup((FIXTURES / "jpm_sample.html").read_text(), "lxml")
        date = JPMScraper._jsonld_date(soup)
        assert date == "2025-05-20"


# ── MS ───────────────────────────────────────────────────────────────────────

class TestMSScraper:
    def setup_method(self):
        self.source = _source("ms_ideas", "Morgan Stanley Ideas", "Morgan Stanley")
        self.scraper = MSScraper(self.source)
        self.html = (FIXTURES / "ms_sample.html").read_text()
        self.soup = BeautifulSoup(self.html, "lxml")

    def test_extracts_articles_from_fixture(self, monkeypatch):
        def fake_get(url):
            return self.soup
        self.scraper._get = fake_get
        stubs = self.scraper.fetch_list()
        assert len(stubs) >= 2

    def test_aria_label_title_priority(self, monkeypatch):
        self.scraper._get = lambda url: self.soup
        stubs = self.scraper.fetch_list()
        titles = [s["title"] for s in stubs]
        assert any("Power Equipment Transformation" in t for t in titles)

    def test_heading_fallback_title(self, monkeypatch):
        self.scraper._get = lambda url: self.soup
        stubs = self.scraper.fetch_list()
        titles = [s["title"] for s in stubs]
        assert any("AI Semiconductor" in t for t in titles)

    def test_jsonld_date_extraction(self):
        soup = BeautifulSoup((FIXTURES / "ms_sample.html").read_text(), "lxml")
        date = MSScraper._jsonld_date(soup)
        assert date == "2025-05-10"


# ── BlackRock BII ────────────────────────────────────────────────────────────

class TestBlackRockScraper:
    def setup_method(self):
        self.source = _source("blackrock_bii", "BlackRock Investment Institute", "BlackRock")
        self.scraper = BlackRockScraper(self.source)
        self.html = (FIXTURES / "blackrock_sample.html").read_text()
        self.soup = BeautifulSoup(self.html, "lxml")

    def test_extracts_articles_from_fixture(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        assert len(stubs) >= 3

    def test_category_prefix_stripped_from_title(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        titles = [s["title"] for s in stubs]
        assert any(t == "Energy security in a world shaped" for t in titles)
        # 카테고리 prefix("Geopolitics")가 제목에 남아있으면 안 됨
        assert not any(t.startswith("Geopolitics") for t in titles)

    def test_date_parsed_from_anchor_text(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        by_title = {s["title"]: s["published_at"] for s in stubs}
        assert by_title["Energy security in a world shaped"] == "2026-06-23"
        assert by_title["Demographic divergence"] == "2025-07-24"

    def test_skips_non_publication_link(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        urls = [s["url"] for s in stubs]
        assert not any(u.endswith("/about-us") for u in urls)

    def test_normalize_returns_required_fields(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        article = self.scraper.normalize(stubs[0], "Sample content")
        assert article["issuer"] == "BlackRock"
        assert article["source_yaml_id"] == "blackrock_bii"

    def test_parse_anchor_static(self):
        title, date = BlackRockScraper._parse_anchor(
            "Geopolitics Energy security in a world shaped June 23, 2026 By BlackRock Investment Institute"
        )
        assert title == "Energy security in a world shaped"
        assert date == "2026-06-23"


# ── Jefferies ────────────────────────────────────────────────────────────────

class TestJefferiesScraper:
    def setup_method(self):
        self.source = _source("jefferies_insights", "Jefferies Insights", "Jefferies")
        self.scraper = JefferiesScraper(self.source)
        self.html = (FIXTURES / "jefferies_sample.html").read_text()
        self.soup = BeautifulSoup(self.html, "lxml")

    def test_extracts_articles_from_fixture(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        assert len(stubs) >= 3

    def test_title_from_heading(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        titles = [s["title"] for s in stubs]
        assert any("Five Trends Shaping the Future of Power and Utilities" in t for t in titles)

    def test_aria_label_fallback_title(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        titles = [s["title"] for s in stubs]
        assert any("Infrastructure Secondaries Hit Their Stride" in t for t in titles)

    def test_skips_category_hub_and_index(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        urls = [s["url"] for s in stubs]
        assert not any(u.rstrip("/").endswith("/insights/markets") for u in urls)
        assert not any(u.rstrip("/").endswith("/insights") for u in urls)

    def test_date_from_date_span(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        by_title = {s["title"]: s["published_at"] for s in stubs}
        assert by_title["Five Trends Shaping the Future of Power and Utilities"] == "2026-06-04"

    def test_normalize_returns_required_fields(self, monkeypatch):
        monkeypatch.setattr(self.scraper, "_get", lambda url: self.soup)
        stubs = self.scraper.fetch_list()
        article = self.scraper.normalize(stubs[0], "Sample content")
        assert article["issuer"] == "Jefferies"
        assert article["source_yaml_id"] == "jefferies_insights"

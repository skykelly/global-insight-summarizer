"""중복 제거 유틸 단위 테스트."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.dedupe import normalize_url, content_hash


class TestNormalizeUrl:
    def test_strips_utm_params(self):
        url = "https://example.com/article?utm_source=email&utm_medium=blast"
        assert "utm_source" not in normalize_url(url)
        assert "utm_medium" not in normalize_url(url)

    def test_preserves_real_params(self):
        url = "https://example.com/search?q=power+equipment&page=2"
        norm = normalize_url(url)
        assert "q=power" in norm
        assert "page=2" in norm

    def test_removes_trailing_slash(self):
        assert normalize_url("https://example.com/a/b/") == normalize_url("https://example.com/a/b")

    def test_lowercases_host(self):
        norm = normalize_url("https://WWW.Example.COM/path")
        assert "www.example.com" in norm

    def test_sorts_params(self):
        url1 = "https://example.com/?b=2&a=1"
        url2 = "https://example.com/?a=1&b=2"
        assert normalize_url(url1) == normalize_url(url2)

    def test_strips_fbclid(self):
        url = "https://example.com/article?fbclid=IwAR1234"
        assert "fbclid" not in normalize_url(url)


class TestContentHash:
    def test_deterministic(self):
        assert content_hash("hello world") == content_hash("hello world")

    def test_different_for_different_content(self):
        assert content_hash("aaa") != content_hash("bbb")

    def test_returns_32_chars(self):
        assert len(content_hash("test")) == 32

    def test_handles_unicode(self):
        result = content_hash("한국어 텍스트 테스트")
        assert len(result) == 32

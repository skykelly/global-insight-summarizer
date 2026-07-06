"""BaseScraper — IB 스크래퍼 공통 인터페이스.
fetch_list → fetch_article → normalize 3단계.
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup


_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class BaseScraper(ABC):
    """모든 IB 스크래퍼의 공통 인터페이스."""

    source_yaml_id: str   # sources.yaml id와 매핑
    issuer: str           # "Goldman Sachs" 등 정식 발행 기관명
    sector_tags: list[str] = []

    def __init__(self, source: dict):
        self.source = source
        self.source_yaml_id = source["id"]
        self.issuer = source.get("issuer", source["name"])
        self.sector_tags = source.get("sector_tags", [])
        self.headers = source.get("headers", _DEFAULT_HEADERS)

    @abstractmethod
    def fetch_list(self) -> list[dict]:
        """기사 목록 페이지를 파싱, {url, title, published_at} stub 목록 반환."""

    def fetch_article(self, url: str) -> tuple[str, bytes]:
        """기사 본문 가져오기. (text_content, raw_html_bytes) 반환.
        서브클래스에서 오버라이드 가능.
        """
        try:
            resp = requests.get(url, headers=self.headers, timeout=20)
            resp.raise_for_status()
            raw_bytes = resp.content
            text = self._extract_body(BeautifulSoup(resp.text, "lxml"))
            return text, raw_bytes
        except Exception as e:
            print(f"[{self.source_yaml_id}] fetch_article 실패 {url}: {e}")
            return "", b""

    def normalize(self, stub: dict, content: str) -> dict:
        """stub + content → raw_source 레코드 형식."""
        return {
            "url":            stub["url"],
            "title":          stub["title"],
            "published_at":   stub.get("published_at"),
            "raw_text":       content,
            "issuer":         self.issuer,
            "sector_tags":    self.sector_tags,
            "source_yaml_id": self.source_yaml_id,
        }

    # ── 공통 유틸 ────────────────────────────────────────────────────

    def _get(self, url: str) -> Optional[BeautifulSoup]:
        try:
            resp = requests.get(url, headers=self.headers, timeout=20)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            print(f"[{self.source_yaml_id}] GET 실패 {url}: {e}")
            return None

    def _extract_body(self, soup: BeautifulSoup, char_limit: int = 6000) -> str:
        for tag in soup(["nav", "footer", "script", "style", "header", "aside"]):
            tag.decompose()
        for sel in ["article", "main", '[class*="content"]', '[class*="article"]']:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(separator=" ", strip=True)
                if len(text) > 200:
                    return text[:char_limit]
        paras = soup.find_all("p")
        return " ".join(
            p.get_text(strip=True) for p in paras if len(p.get_text(strip=True)) > 50
        )[:char_limit]

    @staticmethod
    def _parse_date(text: str) -> Optional[str]:
        if not text:
            return None
        for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%Y-%m-%d",
                    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(text.strip()[:20], fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
        m = re.search(
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s*\d{4}",
            text, re.I,
        )
        if m:
            try:
                return datetime.strptime(m.group(0).replace(",", ""), "%B %d %Y").strftime("%Y-%m-%d")
            except ValueError:
                pass
        return None

    @staticmethod
    def _jsonld_date(soup: BeautifulSoup) -> Optional[str]:
        for s in soup.find_all("script", type="application/ld+json"):
            try:
                d = json.loads(s.string)
                for item in [d] + d.get("@graph", []):
                    val = item.get("datePublished") or item.get("dateCreated")
                    if val and re.match(r"\d{4}-\d{2}-\d{2}", str(val)):
                        return str(val)[:10]
            except Exception:
                pass
        return None

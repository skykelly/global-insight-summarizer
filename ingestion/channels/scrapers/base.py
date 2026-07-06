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


def extract_body(soup: BeautifulSoup, char_limit: int = 6000) -> str:
    """HTML에서 기사 본문 텍스트 추출. rss/crawl 채널에서도 공용."""
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
        기사 페이지에서 발행일도 추출해 normalize에서 백필한다.
        서브클래스에서 오버라이드 가능.
        """
        self._last_page_date: Optional[str] = None
        try:
            resp = requests.get(url, headers=self.headers, timeout=20)
            resp.raise_for_status()
            raw_bytes = resp.content
            soup = BeautifulSoup(resp.text, "lxml")
            self._last_page_date = self.extract_page_date(soup)
            text = self._extract_body(soup)
            return text, raw_bytes
        except Exception as e:
            print(f"[{self.source_yaml_id}] fetch_article 실패 {url}: {e}")
            return "", b""

    def normalize(self, stub: dict, content: str) -> dict:
        """stub + content → raw_source 레코드 형식.
        인덱스 카드에 날짜가 없으면 기사 페이지에서 추출한 날짜로 백필.
        """
        return {
            "url":            stub["url"],
            "title":          stub["title"],
            "published_at":   stub.get("published_at") or getattr(self, "_last_page_date", None),
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
        return extract_body(soup, char_limit)

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
            for fmt in ("%B %d %Y", "%b %d %Y"):  # 풀네임(June)·약어(Jun) 모두 지원
                try:
                    return datetime.strptime(m.group(0).replace(",", ""), fmt).strftime("%Y-%m-%d")
                except ValueError:
                    pass
        return None

    @classmethod
    def extract_page_date(cls, soup: BeautifulSoup) -> Optional[str]:
        """기사 페이지에서 발행일 추출: JSON-LD → meta → <time> 순."""
        date = cls._jsonld_date(soup)
        if date:
            return date
        for sel in ('meta[property="article:published_time"]',
                    'meta[name="publish_date"]',
                    'meta[name="publication_date"]',
                    'meta[name="date"]'):
            meta = soup.select_one(sel)
            if meta and meta.get("content"):
                m = re.match(r"\d{4}-\d{2}-\d{2}", meta["content"])
                if m:
                    return m.group(0)
        t = soup.select_one("time[datetime]")
        if t:
            m = re.match(r"\d{4}-\d{2}-\d{2}", t.get("datetime", ""))
            if m:
                return m.group(0)
        t = soup.find("time")
        if t:
            date = cls._parse_date(t.get_text(strip=True))
            if date:
                return date
        # 최후 폴백: 본문 상단 텍스트에서 사람이 읽는 날짜 (MS·JPM은 구조화 마크업 없음)
        # nav 메뉴 텍스트가 앞부분을 차지하므로 15000자까지 탐색 (실측: MS 10.3K, JPM 5.5K 지점)
        return cls._parse_date(soup.get_text(" ", strip=True)[:15000])

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

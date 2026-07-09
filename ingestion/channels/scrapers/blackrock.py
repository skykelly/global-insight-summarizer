"""BlackRock Investment Institute (BII) 스크래퍼.

파싱 전략: 인덱스 앵커가 "카테고리 제목 By BlackRock Investment Institute 날짜"
형태로 텍스트 하나에 뭉쳐 있음 — 별도 title/date 요소가 없다. 정규식으로 분해한다.
로직 출처: ingestion/channels/scrapers/core_scraper.py(equity-research-blog 이월분)의
UniversalScraper._bii_parse_anchor — BaseScraper 인터페이스로 포팅.
"""
from __future__ import annotations

import re
from typing import Optional

from .base import BaseScraper

_CAT_PREFIX = re.compile(
    r"^(Publications|Geopolitics|Market\s+trends?|Demographics?|Outlook|"
    r"Global\s+insights?|Economy|Asset\s+classes?|Themes?|"
    r"\d{4}\s+INVESTMENT\s+OUTLOOK)\s*",
    re.I,
)
_DATE_RE = re.compile(
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s*\d{4}",
    re.I,
)


class BlackRockScraper(BaseScraper):
    INDEX_URLS = [
        "https://www.blackrock.com/corporate/insights/blackrock-investment-institute",
    ]

    def fetch_list(self) -> list[dict]:
        stubs: list[dict] = []
        seen: set[str] = set()

        for index_url in self.INDEX_URLS:
            soup = self._get(index_url)
            if not soup:
                continue
            for a in soup.find_all("a", href=True):
                href: str = a["href"]
                if "/blackrock-investment-institute/publications" not in href:
                    continue
                full_url = href if href.startswith("http") else f"https://www.blackrock.com{href}"
                if full_url in seen:
                    continue
                seen.add(full_url)

                text = re.sub(r"\s+", " ", a.get_text()).strip()
                title, published_at = self._parse_anchor(text)
                if len(title) < 10:
                    continue
                stubs.append({"url": full_url, "title": title, "published_at": published_at})

        print(f"[blackrock] 목록 {len(stubs)}건")
        return stubs[:20]

    @staticmethod
    def _parse_anchor(text: str) -> tuple[str, Optional[str]]:
        """앵커 텍스트("카테고리 제목 By BlackRock Investment Institute 날짜")를 분리."""
        text = re.sub(r"\|?By.*$", "", text, flags=re.I).strip()
        text = re.sub(r"^BlackRock\s+Investment\s+Institute.*?\)\s*", "", text).strip()
        date_match = _DATE_RE.search(text)
        if date_match:
            published_at = BaseScraper._parse_date(date_match.group(0))
            title = text[: date_match.start()].strip()
        else:
            published_at = None
            title = text
        title = _CAT_PREFIX.sub("", title).strip()
        return title, published_at

    # fetch_article/normalize는 BaseScraper 공통 구현 사용
    # (기사 페이지 JSON-LD·meta·<time>에서 날짜 백필, 인덱스에서 날짜 못 뽑은 경우 보완)

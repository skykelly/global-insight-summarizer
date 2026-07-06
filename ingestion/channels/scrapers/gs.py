"""Goldman Sachs Insights 스크래퍼.
파싱 전략: data-gs-uitk-component="card-title" 로 제목, card-meta 로 날짜.
"""
from __future__ import annotations

from .base import BaseScraper


class GSScraper(BaseScraper):
    INDEX_URL = "https://www.goldmansachs.com/insights/"

    def fetch_list(self) -> list[dict]:
        soup = self._get(self.INDEX_URL)
        if not soup:
            return []

        stubs: list[dict] = []
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if "/insights/" not in href or href.rstrip("/") == "/insights":
                continue
            full_url = href if href.startswith("http") else f"https://www.goldmansachs.com{href}"
            # 제목: gs_card 전략
            title_el = a.select_one('[data-gs-uitk-component="card-title"]')
            if not title_el:
                title_el = a.find(["h2", "h3", "h4"])
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if len(title) < 10:
                continue
            # 날짜: gs_card 전략
            meta_el = a.select_one('[data-gs-uitk-component="card-meta"]')
            date = self._parse_date(meta_el.get_text(strip=True)) if meta_el else None
            stubs.append({"url": full_url, "title": title, "published_at": date})

        print(f"[gs] 목록 {len(stubs)}건")
        return stubs[:20]

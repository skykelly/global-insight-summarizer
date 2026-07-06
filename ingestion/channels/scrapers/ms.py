"""Morgan Stanley Ideas 스크래퍼.
파싱 전략: aria-label 우선, 없으면 heading (aria_label_then_heading).
"""
from __future__ import annotations

from .base import BaseScraper


class MSScraper(BaseScraper):
    INDEX_URLS = [
        "https://www.morganstanley.com/ideas",
        "https://www.morganstanley.com/ideas/research",
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
                if "/ideas/" not in href:
                    continue
                full_url = href if href.startswith("http") else f"https://www.morganstanley.com{href}"
                if full_url in seen:
                    continue
                seen.add(full_url)
                # 제목: aria-label 우선, 없으면 heading
                title = a.get("aria-label", "").strip()
                if not title:
                    h = a.find(["h2", "h3", "h4", "h1"])
                    if h:
                        title = h.get_text(strip=True)
                    else:
                        text = a.get_text(strip=True)
                        title = text if len(text) > 20 else ""
                if len(title) < 10:
                    continue
                stubs.append({"url": full_url, "title": title, "published_at": None})

        print(f"[ms] 목록 {len(stubs)}건")
        return stubs[:20]

    def fetch_article(self, url: str) -> tuple[str, bytes]:
        """날짜는 article 페이지 JSON-LD에서 추출."""
        import requests
        from bs4 import BeautifulSoup

        try:
            resp = requests.get(url, headers=self.headers, timeout=20)
            resp.raise_for_status()
            raw_bytes = resp.content
            soup = BeautifulSoup(resp.text, "lxml")
            self._last_jsonld_date = self._jsonld_date(soup)
            text = self._extract_body(soup)
            return text, raw_bytes
        except Exception as e:
            print(f"[ms] fetch_article 실패 {url}: {e}")
            return "", b""

    def normalize(self, stub: dict, content: str) -> dict:
        result = super().normalize(stub, content)
        if not result["published_at"] and hasattr(self, "_last_jsonld_date"):
            result["published_at"] = self._last_jsonld_date
        return result

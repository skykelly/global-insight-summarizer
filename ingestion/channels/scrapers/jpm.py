"""J.P. Morgan Insights 스크래퍼.
파싱 전략: heading 으로 제목, article_jsonld 로 날짜.
"""
from __future__ import annotations

from .base import BaseScraper


class JPMScraper(BaseScraper):
    INDEX_URL = "https://www.jpmorgan.com/insights"

    def fetch_list(self) -> list[dict]:
        soup = self._get(self.INDEX_URL)
        if not soup:
            return []

        stubs: list[dict] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if "/insights/" not in href and "/research/" not in href:
                continue
            full_url = href if href.startswith("http") else f"https://www.jpmorgan.com{href}"
            if full_url in seen:
                continue
            seen.add(full_url)
            # 제목: heading 전략
            h = a.find(["h2", "h3", "h4", "h1"])
            if not h:
                aria = a.get("aria-label", "").strip()
                if len(aria) > 10:
                    title = aria
                else:
                    continue
            else:
                title = h.get_text(strip=True)
            if len(title) < 10:
                continue
            stubs.append({"url": full_url, "title": title, "published_at": None})

        print(f"[jpm] 목록 {len(stubs)}건")
        return stubs[:20]

    def fetch_article(self, url: str) -> tuple[str, bytes]:
        """날짜는 기사 페이지 JSON-LD에서 추출."""
        import requests
        from bs4 import BeautifulSoup

        try:
            resp = requests.get(url, headers=self.headers, timeout=20)
            resp.raise_for_status()
            raw_bytes = resp.content
            soup = BeautifulSoup(resp.text, "lxml")
            # JSON-LD에서 날짜 추출 — BaseScraper.normalize 호출 시 published_at override
            self._last_jsonld_date = self._jsonld_date(soup)
            text = self._extract_body(soup)
            return text, raw_bytes
        except Exception as e:
            print(f"[jpm] fetch_article 실패 {url}: {e}")
            return "", b""

    def normalize(self, stub: dict, content: str) -> dict:
        result = super().normalize(stub, content)
        if not result["published_at"] and hasattr(self, "_last_jsonld_date"):
            result["published_at"] = self._last_jsonld_date
        return result

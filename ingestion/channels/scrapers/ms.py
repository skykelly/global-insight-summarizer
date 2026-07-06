"""Morgan Stanley Ideas 스크래퍼.
파싱 전략: aria-label 우선, 없으면 heading (aria_label_then_heading).
"""
from __future__ import annotations

from .base import BaseScraper


class MSScraper(BaseScraper):
    # 2026-07 사이트 개편: 기사가 /ideas/* → /insights/articles/* 로 이동
    INDEX_URLS = [
        "https://www.morganstanley.com/ideas",
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
                if "/ideas/" not in href and "/insights/articles" not in href:
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

    # fetch_article/normalize는 BaseScraper 공통 구현 사용
    # (기사 페이지 JSON-LD·meta·<time>에서 날짜 백필)

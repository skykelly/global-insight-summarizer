"""Jefferies Insights 스크래퍼.

파싱 전략: heading 우선 → aria-label → anchor 텍스트(20자 이상).
URL 구조가 /insights/{category}/{slug}/ 이므로, 카테고리 허브 페이지
(/insights/, /insights/{category}/)는 path segment 부족으로 걸러진다.
"""
from __future__ import annotations

from .base import BaseScraper


class JefferiesScraper(BaseScraper):
    INDEX_URLS = [
        "https://www.jefferies.com/insights/",
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
                if "/insights/" not in href:
                    continue
                full_url = href if href.startswith("http") else f"https://www.jefferies.com{href}"

                # 카테고리 허브·인덱스 자체 제외: /insights/{category}/{slug}/ 형태만 통과
                path = full_url.split("jefferies.com", 1)[-1]
                segments = [s for s in path.split("/") if s]
                if len(segments) < 3:
                    continue

                if full_url in seen:
                    continue
                seen.add(full_url)

                title = ""
                h = a.find(["h1", "h2", "h3", "h4"])
                if h:
                    title = h.get_text(strip=True)
                if not title:
                    title = a.get("aria-label", "").strip()
                if not title:
                    text = a.get_text(strip=True)
                    title = text if len(text) > 20 else ""
                if len(title) < 10:
                    continue

                published_at = None
                date_el = a.select_one(".date, time")
                if date_el:
                    published_at = self._parse_date(date_el.get("datetime") or date_el.get_text(strip=True))

                stubs.append({"url": full_url, "title": title, "published_at": published_at})

        print(f"[jefferies] 목록 {len(stubs)}건")
        return stubs[:20]

    # fetch_article/normalize는 BaseScraper 공통 구현 사용
    # (기사 페이지 JSON-LD·meta·<time>에서 날짜 백필)

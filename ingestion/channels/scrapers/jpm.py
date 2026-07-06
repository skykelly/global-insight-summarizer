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
            # 섹션 허브 제외: /insights/<article> 이상 깊이만 (기사: /insights/<섹션>/<기사>)
            path = href.split("//")[-1].split("/", 1)[-1] if href.startswith("http") else href.lstrip("/")
            if len([p for p in path.split("/") if p]) < 3:
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
            # nav 링크의 접근성 라벨("links to ...", "opens ...") 제외
            if title.lower().startswith(("links to", "link to", "opens ")):
                continue
            stubs.append({"url": full_url, "title": title, "published_at": None})

        print(f"[jpm] 목록 {len(stubs)}건")
        return stubs[:20]

    # fetch_article/normalize는 BaseScraper 공통 구현 사용
    # (기사 페이지 JSON-LD·meta·<time>에서 날짜 백필)

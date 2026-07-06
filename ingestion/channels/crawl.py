"""Tier 3 Crawl4AI 채널.
Tier 1/2 실패 시 폴백. Crawl4AI가 설치되어 있어야 함 (requirements Phase 1+).
"""
from __future__ import annotations

import os


def is_available() -> bool:
    try:
        import crawl4ai  # noqa: F401
        return True
    except ImportError:
        return False


def fetch_url(url: str, source: dict) -> dict | None:
    """Crawl4AI로 단일 URL 크롤링."""
    if not is_available():
        print(f"[crawl:{source['id']}] crawl4ai 미설치 — pip install crawl4ai")
        return None

    import asyncio
    from crawl4ai import AsyncWebCrawler

    issuer = source.get("issuer", source["name"])
    sector_tags = source.get("sector_tags", [])
    source_yaml_id = source["id"]

    async def _run():
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(url=url)
            return result

    try:
        result = asyncio.run(_run())
        if not result.success:
            return None
        raw_text = (result.markdown or result.cleaned_html or "")[:8000]
        title = url.split("/")[-1].replace("-", " ")
        published_at = _extract_date(result.cleaned_html or result.html or "")
        if not published_at:
            print(f"[crawl:{source_yaml_id}] 발행일 추출 실패 — sources 승격 불가 (Hard Rule)")
        return {
            "url":            url,
            "title":          title,
            "published_at":   published_at,
            "raw_text":       raw_text,
            "issuer":         issuer,
            "sector_tags":    sector_tags,
            "source_yaml_id": source_yaml_id,
        }
    except Exception as e:
        print(f"[crawl:{source_yaml_id}] {url} 실패: {e}")
        return None


def _extract_date(html: str) -> str | None:
    """JSON-LD datePublished 또는 article:published_time 메타에서 발행일 추출."""
    if not html:
        return None
    from bs4 import BeautifulSoup
    from ingestion.channels.scrapers.base import BaseScraper

    soup = BeautifulSoup(html, "lxml")
    date = BaseScraper._jsonld_date(soup)
    if date:
        return date
    meta = soup.select_one('meta[property="article:published_time"]')
    if meta and meta.get("content"):
        import re
        m = re.match(r"\d{4}-\d{2}-\d{2}", meta["content"])
        if m:
            return m.group(0)
    return None

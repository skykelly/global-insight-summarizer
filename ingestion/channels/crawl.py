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
        return {
            "url":            url,
            "title":          title,
            "published_at":   None,
            "raw_text":       raw_text,
            "issuer":         issuer,
            "sector_tags":    sector_tags,
            "source_yaml_id": source_yaml_id,
        }
    except Exception as e:
        print(f"[crawl:{source_yaml_id}] {url} 실패: {e}")
        return None

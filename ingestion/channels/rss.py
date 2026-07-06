"""Tier 1 RSS 채널.
feedparser로 피드를 파싱해 표준 RawArticle dict 목록 반환.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING

import feedparser

if TYPE_CHECKING:
    pass


def _parse_date(entry: feedparser.FeedParserDict) -> str | None:
    if entry.get("published_parsed"):
        try:
            return datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
        except Exception:
            pass
    raw = entry.get("published") or entry.get("updated") or ""
    if raw:
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


def fetch(source: dict, max_items: int = 20) -> list[dict]:
    """RSS 피드를 파싱해 RawArticle 목록 반환.

    Args:
        source: sources.yaml 항목 (id, name, url, issuer, sector_tags 등)
        max_items: 소스당 최대 수집 건수

    Returns:
        list of {url, title, published_at, raw_text, issuer, sector_tags, source_yaml_id}
    """
    feed_url = source["url"]
    issuer = source.get("issuer", source["name"])
    sector_tags = source.get("sector_tags", [])
    source_yaml_id = source["id"]

    try:
        feed = feedparser.parse(
            feed_url,
            request_headers={"User-Agent": "ResearchWiki/1.0 (+https://github.com)"},
        )
    except Exception as e:
        print(f"[rss:{source_yaml_id}] 피드 파싱 실패: {e}")
        return []

    if feed.bozo and not feed.entries:
        print(f"[rss:{source_yaml_id}] 피드 오류: {feed.bozo_exception}")
        return []

    articles: list[dict] = []
    for entry in feed.entries[:max_items]:
        url = entry.get("link", "").strip()
        if not url:
            continue
        title = entry.get("title", "").strip()
        if not title or len(title) < 8:
            continue
        raw_body = (
            entry.get("summary", "")
            or (entry.get("content") or [{}])[0].get("value", "")
        )
        raw_text = _strip_html(raw_body)[:4000]
        published_at = _parse_date(entry)
        articles.append({
            "url":             url,
            "title":           title,
            "published_at":    published_at,
            "raw_text":        raw_text,
            "issuer":          issuer,
            "sector_tags":     sector_tags,
            "source_yaml_id":  source_yaml_id,
        })

    print(f"[rss:{source_yaml_id}] {len(articles)}건 수집")
    return articles

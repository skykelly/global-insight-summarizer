"""Tier 1 RSS 채널.
feedparser로 피드를 파싱한 뒤 각 entry의 원문 페이지를 fetch해 본문을 보강한다.
원문 fetch 실패 시 RSS summary로 폴백.
"""
from __future__ import annotations

import re
from datetime import datetime

import feedparser
import requests
from bs4 import BeautifulSoup

from ingestion.channels.scrapers.base import _DEFAULT_HEADERS, extract_body

_FULLTEXT_TIMEOUT = 20
_FULLTEXT_MIN_CHARS = 300  # 이보다 짧으면 summary가 더 낫다고 판단


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


def _fetch_fulltext(url: str) -> str:
    """entry 원문 페이지에서 본문 추출. 실패 시 빈 문자열."""
    try:
        resp = requests.get(url, headers=_DEFAULT_HEADERS, timeout=_FULLTEXT_TIMEOUT)
        resp.raise_for_status()
        return extract_body(BeautifulSoup(resp.text, "lxml"))
    except Exception:
        return ""


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
            agent=_DEFAULT_HEADERS["User-Agent"],
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
        summary_text = _strip_html(raw_body)[:4000]

        # 본문 보강: 원문 페이지 fetch, 유의미한 길이면 채택
        fulltext = _fetch_fulltext(url)
        raw_text = fulltext if len(fulltext) >= max(_FULLTEXT_MIN_CHARS, len(summary_text)) else summary_text

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

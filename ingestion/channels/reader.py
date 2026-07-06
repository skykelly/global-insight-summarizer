"""Tier 2 Jina Reader 채널.
Jina AI Reader API로 URL → 마크다운 변환. 재시도 3회.
"""
from __future__ import annotations

import os
import time
from urllib.parse import quote

import requests

JINA_BASE = "https://r.jina.ai"
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2.0


def fetch_url(url: str, source: dict) -> dict | None:
    """단일 URL의 콘텐츠를 Jina Reader로 가져옴.

    Returns:
        {url, title, published_at, raw_text, issuer, sector_tags, source_yaml_id} or None
    """
    issuer = source.get("issuer", source["name"])
    sector_tags = source.get("sector_tags", [])
    source_yaml_id = source["id"]

    headers = {
        "Accept": "text/plain",
        "User-Agent": "ResearchWiki/1.0",
    }
    api_key = os.environ.get("JINA_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    jina_url = f"{JINA_BASE}/{url}"
    last_err: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(jina_url, headers=headers, timeout=TIMEOUT)
            if resp.status_code == 429:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            resp.raise_for_status()
            raw_text = resp.text[:8000]
            # 첫 줄을 제목으로 추출 (Jina 응답 포맷: "Title: ...")
            title = ""
            for line in raw_text.split("\n")[:5]:
                if line.startswith("Title:"):
                    title = line[6:].strip()
                    break
            if not title:
                title = url.split("/")[-1].replace("-", " ").replace("_", " ")

            return {
                "url":            url,
                "title":          title,
                "published_at":   None,  # reader로는 날짜 추출 안됨 — scraper가 담당
                "raw_text":       raw_text,
                "issuer":         issuer,
                "sector_tags":    sector_tags,
                "source_yaml_id": source_yaml_id,
            }
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))

    print(f"[reader:{source_yaml_id}] {url} 실패 ({MAX_RETRIES}회): {last_err}")
    return None


def fetch_list(source: dict, urls: list[str]) -> list[dict]:
    """URL 목록을 Jina Reader로 순차 수집."""
    results = []
    for url in urls:
        item = fetch_url(url, source)
        if item:
            results.append(item)
    return results

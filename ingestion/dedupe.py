"""URL 정규화 + SHA256 해시 기반 중복 제거.
동일 content_hash 가 raw_sources 에 이미 있으면 skip.
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl


# 트래킹 파라미터 제거 목록
_STRIP_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "ref", "source", "mc_cid", "mc_eid", "fbclid", "gclid", "msclkid",
})


def normalize_url(url: str) -> str:
    """URL을 정규화: 소문자 host, 트래킹 파라미터 제거, trailing slash 제거."""
    url = url.strip()
    parsed = urlparse(url)
    # 소문자 host, scheme
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    # 트래킹 파라미터 제거 후 정렬
    params = sorted(
        (k, v) for k, v in parse_qsl(parsed.query)
        if k.lower() not in _STRIP_PARAMS
    )
    query = urlencode(params)
    normalized = urlunparse((parsed.scheme, netloc, path, parsed.params, query, ""))
    return normalized


def content_hash(text: str) -> str:
    """SHA256 hex digest (앞 32자)."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:32]


def is_duplicate(url_normalized: str, hash_val: str) -> bool:
    """DB에 동일 URL 또는 content_hash가 있으면 True."""
    from ingestion.db import execute
    rows = execute(
        """
        SELECT 1 FROM raw_sources
        WHERE url_normalized = %s OR content_hash = %s
        LIMIT 1
        """,
        (url_normalized, hash_val),
    )
    return len(rows) > 0

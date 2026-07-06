"""Vercel Blob 원본 아카이브 업로드.
원문은 파싱 전 Blob에 업로드 후 URL을 raw_sources에 기록 — Hard Rule.
파일명: {published_date}_{issuer_slug}_{url_slug}.{ext}
"""
from __future__ import annotations

import hashlib
import os
import re

import requests


def _slug(text: str, max_len: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:max_len]


def make_blob_filename(published_date: str, issuer: str, url: str, ext: str = "html") -> str:
    url_hash = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"{published_date}_{_slug(issuer)}_{url_hash}.{ext}"


def upload(content: bytes, filename: str, content_type: str = "text/html; charset=utf-8") -> str:
    """Vercel Blob REST API로 업로드. 업로드된 공개 URL 반환."""
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        raise RuntimeError("BLOB_READ_WRITE_TOKEN 환경변수 미설정")

    resp = requests.put(
        f"https://blob.vercel-storage.com/{filename}",
        data=content,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
            "x-content-type": content_type,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("url") or data.get("downloadUrl", "")

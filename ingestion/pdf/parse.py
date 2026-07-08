"""PDF 파서. Docling(표 보존) 1순위, 실패 시 OpenAI PDF 입력 폴백.
원본은 파싱 전 Vercel Blob 업로드 후 URL을 raw_sources에 기록 (Hard Rule).
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import requests


def _parse_with_docling(pdf_bytes: bytes) -> str:
    """Docling으로 PDF → 마크다운. 표 구조 보존 (D6)."""
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        raise RuntimeError("docling 미설치 — pip install docling")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        converter = DocumentConverter()
        result = converter.convert(tmp_path)
        return result.document.export_to_markdown()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _parse_with_openai(pdf_bytes: bytes) -> str:
    """OpenAI PDF 입력 폴백. Docling 실패 시 사용 (Responses API file input)."""
    import base64

    from openai import OpenAI

    from knowledge.llm_client import MODEL_MAIN

    client = OpenAI()
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    resp = client.responses.create(
        model=MODEL_MAIN,
        input=[{
            "role": "user",
            "content": [
                {
                    "type": "input_file",
                    "filename": "document.pdf",
                    "file_data": f"data:application/pdf;base64,{pdf_b64}",
                },
                {
                    "type": "input_text",
                    "text": (
                        "이 PDF 문서의 전체 내용을 마크다운 형식으로 추출하세요. "
                        "표, 수치, 섹션 제목을 포함한 모든 텍스트를 보존하세요."
                    ),
                },
            ],
        }],
    )
    return resp.output_text


def fetch_pdf(url: str) -> bytes:
    """URL에서 PDF 다운로드."""
    resp = requests.get(
        url,
        headers={"User-Agent": "ResearchWiki/1.0"},
        timeout=60,
        stream=True,
    )
    resp.raise_for_status()
    return resp.content


def parse(
    pdf_bytes: bytes,
    source: dict,
    url: str,
) -> dict:
    """PDF 바이트 → raw_source dict.

    1. Vercel Blob 업로드 (Hard Rule: 파싱 전에 원본 보존)
    2. Docling 파싱 시도
    3. 실패 시 Claude 폴백
    """
    from ingestion.blob import upload, make_blob_filename
    from ingestion.dedupe import content_hash

    issuer = source.get("issuer", source["name"])
    published_at = source.get("manual_date")  # Tier 4는 sources.yaml에 수동 날짜
    source_yaml_id = source["id"]
    sector_tags = source.get("sector_tags", [])

    # 1. Blob 업로드 (파싱 전)
    filename = make_blob_filename(
        published_at or "undated", issuer, url, ext="pdf"
    )
    blob_url = ""
    try:
        blob_url = upload(pdf_bytes, filename, content_type="application/pdf")
        print(f"[pdf:{source_yaml_id}] Blob 업로드 완료: {blob_url}")
    except Exception as e:
        print(f"[pdf:{source_yaml_id}] Blob 업로드 실패 (계속 진행): {e}")

    # 2. Docling 파싱
    raw_text = ""
    try:
        raw_text = _parse_with_docling(pdf_bytes)
        print(f"[pdf:{source_yaml_id}] Docling 파싱 성공 ({len(raw_text)}자)")
    except Exception as e:
        print(f"[pdf:{source_yaml_id}] Docling 실패, OpenAI 폴백: {e}")
        try:
            raw_text = _parse_with_openai(pdf_bytes)
            print(f"[pdf:{source_yaml_id}] OpenAI 폴백 성공 ({len(raw_text)}자)")
        except Exception as e2:
            print(f"[pdf:{source_yaml_id}] OpenAI 폴백도 실패: {e2}")

    return {
        "url":            url,
        "title":          source.get("name", ""),
        "published_at":   published_at,
        "raw_text":       raw_text[:8000],
        "issuer":         issuer,
        "sector_tags":    sector_tags,
        "source_yaml_id": source_yaml_id,
        "blob_url":       blob_url,
    }

#!/usr/bin/env python3
"""knowledge/embed.py — OpenAI text-embedding-3-small (1536d) 임베딩.

knowledge_items 생성 → knowledge_embeddings 적재.
metadata에 published_at, sector, issuer 포함 (시점 가중 RAG 필수).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import OpenAI

from knowledge.db import db_conn

_OC = OpenAI()
_EMBED_MODEL = "text-embedding-3-small"
_CHUNK_SIZE = 1500  # 청크당 최대 문자 수


def _chunk_text(text: str, size: int = _CHUNK_SIZE) -> list[str]:
    """텍스트를 청크로 분할. 문단 경계 우선."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) > size and current:
            chunks.append(current.strip())
            current = para
        else:
            current += "\n\n" + para if current else para
    if current:
        chunks.append(current.strip())
    return chunks or [text[:size]]


def _embed_texts(texts: list[str]) -> list[list[float]]:
    resp = _OC.embeddings.create(model=_EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def _save_knowledge_item(conn, source_id: str, chunk: str, item_type: str,
                          published_at: str, sector: str, issuer: str) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO knowledge_items
               (source_id, content, item_type, published_at, sector, issuer)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (source_id, chunk, item_type, published_at, sector, issuer),
        )
        return str(cur.fetchone()["id"])


def run(source_ids: list[str] | None = None) -> dict[str, int]:
    """auto_accepted/accepted 소스의 요약을 임베딩."""
    stats = {"embedded": 0, "chunks": 0, "errors": 0}

    with db_conn() as conn:
        with conn.cursor() as cur:
            if source_ids:
                cur.execute(
                    """SELECT s.id, s.issuer, s.published_at, sm.id as sum_id, sm.content_ko,
                              s.sector_tags
                       FROM sources s JOIN summaries sm ON sm.source_id = s.id
                       WHERE s.status IN ('auto_accepted','accepted') AND s.id = ANY(%s)
                         AND NOT EXISTS (
                           SELECT 1 FROM knowledge_embeddings ke
                           JOIN knowledge_items ki ON ki.id = ke.ref_id
                           WHERE ki.source_id = s.id
                         )""",
                    (source_ids,),
                )
            else:
                cur.execute(
                    """SELECT s.id, s.issuer, s.published_at, sm.id as sum_id, sm.content_ko,
                              s.sector_tags
                       FROM sources s JOIN summaries sm ON sm.source_id = s.id
                       WHERE s.status IN ('auto_accepted','accepted')
                         AND NOT EXISTS (
                           SELECT 1 FROM knowledge_embeddings ke
                           JOIN knowledge_items ki ON ki.id = ke.ref_id
                           WHERE ki.source_id = s.id
                         )"""
                )
            rows = cur.fetchall()

    for row in rows:
        sid = str(row["id"])
        issuer = row["issuer"] or ""
        published_at = str(row["published_at"] or "")
        content = row["content_ko"] or ""
        sector_tags = row["sector_tags"] or []
        sector = sector_tags[0] if sector_tags else "general"

        try:
            chunks = _chunk_text(content)
            embeddings = _embed_texts(chunks)

            with db_conn() as conn2:
                for chunk, emb in zip(chunks, embeddings):
                    ki_id = _save_knowledge_item(
                        conn2, sid, chunk, "summary", published_at, sector, issuer
                    )
                    meta = json.dumps({
                        "published_at": published_at,
                        "sector": sector,
                        "issuer": issuer,
                        "knowledge_item_id": ki_id,
                    })
                    with conn2.cursor() as cur2:
                        cur2.execute(
                            """INSERT INTO knowledge_embeddings
                               (ref_type, ref_id, content, embedding, metadata)
                               VALUES ('knowledge_item', %s, %s, %s::vector, %s)""",
                            (ki_id, chunk, json.dumps(emb), meta),
                        )
                    stats["chunks"] += 1

            print(f"[embed] {issuer} ({published_at}) → {len(chunks)}청크 임베딩 완료")
            stats["embedded"] += 1

        except Exception as e:
            print(f"[embed] {sid} 오류: {e}")
            stats["errors"] += 1

    return stats


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--source-ids", nargs="*")
    args = p.parse_args()
    result = run(args.source_ids)
    print(f"임베딩 완료 — 소스: {result['embedded']}건, 청크: {result['chunks']}건, 오류: {result['errors']}건")

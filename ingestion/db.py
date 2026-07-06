"""Neon Postgres 접근 헬퍼 (Python raw SQL).
스키마 단일 진실은 db/schema.ts(Drizzle). Python은 raw SQL로만 접근.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg.rows import dict_row


def _url() -> str:
    url = os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL_UNPOOLED (또는 DATABASE_URL) 환경변수 미설정")
    return url


@contextmanager
def db_conn() -> Generator[psycopg.Connection, None, None]:
    """커밋 + 롤백을 관리하는 컨텍스트 매니저."""
    conn = psycopg.connect(_url(), row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(sql: str, params: tuple | list | dict | None = None) -> list[dict]:
    """단발 쿼리 실행 후 결과 반환."""
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description:
                return cur.fetchall()
            return []

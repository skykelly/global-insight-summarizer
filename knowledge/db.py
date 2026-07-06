"""knowledge/db.py — ingestion.db 헬퍼 재수출. 단일 진실."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.db import db_conn, execute  # noqa: F401  re-export

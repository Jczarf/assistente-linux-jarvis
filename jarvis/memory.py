from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from jarvis.config import settings


def _db_path():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings.data_dir / "memory.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.execute(
        """CREATE TABLE IF NOT EXISTS facts (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )"""
    )
    return conn


def save_fact(key: str, value: str) -> str:
    if not settings.memory_enabled:
        return "Memória persistente está desativada."
    key = key.strip().lower()[:80]
    value = value.strip()[:1000]
    if not key or not value:
        return "Chave e valor são obrigatórios."

    with _connect() as conn:
        conn.execute(
            """INSERT INTO facts(key, value, updated_at) VALUES (?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (key, value, datetime.now(timezone.utc).isoformat()),
        )
    return f"Informação '{key}' salva localmente."


def list_facts() -> dict[str, str]:
    if not settings.memory_enabled:
        return {}
    with _connect() as conn:
        rows = conn.execute("SELECT key, value FROM facts ORDER BY key").fetchall()
    return {key: value for key, value in rows}

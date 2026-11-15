"""
db/database.py
Opens the SQLite database, runs the schema DDL, and provides
get_db() as a FastAPI dependency.

All code here is synchronous — do not add async/await.
"""

import sqlite3
from pathlib import Path

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Module-level connection set once by main.py lifespan.
_db_connection: sqlite3.Connection | None = None


def init_db(db_path: str = "claims.db") -> sqlite3.Connection:
    """
    Open (or create) the SQLite database, apply schema DDL, return connection.
    Pass ':memory:' for in-memory database (used in tests).
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()
    return conn


def set_db(conn: sqlite3.Connection) -> None:
    """Store the shared connection. Called from main.py lifespan."""
    global _db_connection
    _db_connection = conn


def get_db():
    """
    FastAPI dependency — yields the shared DB connection.
    Override in tests to inject an in-memory connection.
    """
    if _db_connection is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    yield _db_connection

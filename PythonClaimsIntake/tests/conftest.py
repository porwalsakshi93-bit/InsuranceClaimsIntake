"""
tests/conftest.py
Shared pytest fixtures for unit, property, and integration tests.

Key rules (enforced by steering):
- All tests use in-memory SQLite (:memory:) — never create or read claims.db.
- The `db_conn` fixture provides a fresh in-memory DB with schema + seed data.
- The `client` fixture overrides the FastAPI `get_db` dependency to use db_conn.
"""

import os

# ---------------------------------------------------------------------------
# Force DATABASE_PATH=:memory: BEFORE main is imported.
# main.py reads os.getenv("DATABASE_PATH", "claims.db") at module import time,
# so this must be set early (conftest is the first file pytest loads) to stop
# the app lifespan from creating a claims.db file on disk.
# ---------------------------------------------------------------------------
os.environ["DATABASE_PATH"] = ":memory:"

import pytest

from db.database import init_db
from db.seed import seed


# ---------------------------------------------------------------------------
# db_conn — in-memory SQLite with schema + sample policies
# ---------------------------------------------------------------------------
@pytest.fixture
def db_conn():
    """In-memory SQLite with schema + seed data. Never touches claims.db."""
    conn = init_db(":memory:")  # creates schema from schema.sql
    seed(conn)                   # inserts 7 sample policies
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# client — httpx TestClient with get_db overridden to use in-memory db_conn
# ---------------------------------------------------------------------------
@pytest.fixture
def client(db_conn):
    """TestClient with get_db overridden. Never touches claims.db.

    DATABASE_PATH is already set to :memory: (module level above), so the
    app lifespan's init_db() call creates an in-memory database rather than
    a claims.db file. The dependency override below makes every request use
    the fixture's db_conn instead of the lifespan's throwaway connection.
    """
    from fastapi.testclient import TestClient
    from main import app
    from db.database import get_db

    def override_get_db():
        yield db_conn

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

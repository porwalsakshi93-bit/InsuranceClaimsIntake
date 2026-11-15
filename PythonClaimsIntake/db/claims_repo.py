"""
db/claims_repo.py
All database access functions for claims and policies.

Rules (enforced by steering):
- This is the ONLY file that writes SQL queries.
- All functions are synchronous.
- All SQL uses parameterised ? placeholders — no string interpolation.
"""

import sqlite3
from datetime import datetime, timezone


def generate_claim_id(conn: sqlite3.Connection) -> str:
    """
    Generate the next CLM-YYYYMMDD-NNNN for today (UTC).
    Must be called inside the same transaction as insert_claim.
    """
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"CLM-{today}-"
    row = conn.execute(
        "SELECT COUNT(*) FROM claims WHERE claim_id LIKE ?",
        (f"{prefix}%",),
    ).fetchone()
    return f"{prefix}{(row[0] or 0) + 1:04d}"


def insert_claim(conn: sqlite3.Connection, data: dict) -> str:
    """
    Generate a claim ID and insert the claim in a single transaction.
    Returns the generated claim_id.
    """
    with conn:
        claim_id = generate_claim_id(conn)
        conn.execute(
            """
            INSERT INTO claims (
                claim_id, policy_number, first_name, last_name, phone, email,
                incident_date, loss_type, incident_description,
                estimated_loss_amount, incident_location, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Draft')
            """,
            (
                claim_id,
                data["policy_number"],
                data["first_name"],
                data["last_name"],
                data["phone"],
                data.get("email"),
                str(data["incident_date"]),
                data["loss_type"],
                data["incident_description"],
                data.get("estimated_loss_amount"),
                data.get("incident_location"),
            ),
        )
    return claim_id


def find_claim_by_id(conn: sqlite3.Connection, claim_id: str) -> dict | None:
    """Fetch a single claim by exact claim_id. Returns dict or None."""
    row = conn.execute(
        "SELECT * FROM claims WHERE claim_id = ?", (claim_id,)
    ).fetchone()
    return dict(row) if row else None


def search_claims(conn: sqlite3.Connection, query: str) -> list[dict]:
    """
    Search by exact claim_id OR case-insensitive partial last_name.
    Results capped at 50, ordered newest first.
    """
    rows = conn.execute(
        """
        SELECT claim_id, first_name, last_name, policy_number,
               loss_type, incident_date, status
        FROM claims
        WHERE claim_id = ? OR last_name LIKE ?
        ORDER BY created_at DESC
        LIMIT 50
        """,
        (query, f"%{query}%"),
    ).fetchall()
    return [dict(r) for r in rows]


def find_policy_by_number(conn: sqlite3.Connection, policy_number: str) -> dict | None:
    """Fetch a policy by exact policy_number. Returns dict or None."""
    row = conn.execute(
        "SELECT * FROM policies WHERE policy_number = ?", (policy_number,)
    ).fetchone()
    return dict(row) if row else None

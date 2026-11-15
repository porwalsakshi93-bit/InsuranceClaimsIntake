"""
db/seed.py
Seeds the policies table with sample records.
Safe to run multiple times — uses INSERT OR IGNORE.

Usage:
    python -m db.seed
"""

import sqlite3
import sys
from db.database import init_db

SAMPLE_POLICIES = [
    ("POL-001", "Alice Johnson",   "Home"),
    ("POL-002", "Bob Martinez",    "Auto"),
    ("POL-003", "Carol Williams",  "Home"),
    ("POL-004", "David Chen",      "Commercial"),
    ("POL-005", "Emily Thompson",  "Life"),
    ("POL-006", "Frank Nguyen",    "Auto"),
    ("POL-007", "Grace Patel",     "Home"),
]


def seed(conn: sqlite3.Connection) -> int:
    """Insert sample policies. Returns count of newly inserted rows."""
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT OR IGNORE INTO policies (policy_number, holder_name, policy_type) VALUES (?, ?, ?)",
        SAMPLE_POLICIES,
    )
    inserted = cursor.rowcount
    conn.commit()
    return inserted


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "claims.db"
    conn = init_db(db_path)
    count = seed(conn)
    print(f"Seeded {count} new policy record(s) into '{db_path}'.")
    conn.close()

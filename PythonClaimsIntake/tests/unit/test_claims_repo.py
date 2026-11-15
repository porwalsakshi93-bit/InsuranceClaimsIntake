"""
tests/unit/test_claims_repo.py
Unit tests for db/claims_repo.py using in-memory SQLite.
Never touches claims.db.
"""

import sqlite3
import pytest
from db.database import init_db
from db.seed import seed
from db import claims_repo


@pytest.fixture
def conn():
    """Fresh in-memory DB with schema and seed data for each test."""
    c = init_db(":memory:")
    seed(c)
    yield c
    c.close()


# ---------------------------------------------------------------------------
# insert_claim
# ---------------------------------------------------------------------------

def test_insert_claim_returns_claim_id(conn):
    data = {
        "policy_number": "POL-001",
        "first_name": "Jane",
        "last_name": "Smith",
        "phone": "5551234567",
        "email": "jane@example.com",
        "incident_date": "2026-10-01",
        "loss_type": "Fire",
        "incident_description": "Kitchen fire caused significant damage.",
        "estimated_loss_amount": 15000.0,
        "incident_location": "123 Main St",
    }
    claim_id = claims_repo.insert_claim(conn, data)
    assert claim_id.startswith("CLM-")
    assert len(claim_id) == 17  # CLM-YYYYMMDD-NNNN = 4 + 8 + 1 + 4


def test_insert_claim_persists_all_fields(conn):
    data = {
        "policy_number": "POL-002",
        "first_name": "Bob",
        "last_name": "Jones",
        "phone": "5559876543",
        "incident_date": "2026-09-15",
        "loss_type": "Flood",
        "incident_description": "Basement flooded after heavy rain.",
    }
    claim_id = claims_repo.insert_claim(conn, data)
    result = claims_repo.find_claim_by_id(conn, claim_id)
    assert result["first_name"] == "Bob"
    assert result["last_name"] == "Jones"
    assert result["loss_type"] == "Flood"
    assert result["status"] == "Draft"
    assert result["email"] is None


def test_insert_claim_default_status_is_draft(conn):
    data = {
        "policy_number": "POL-001",
        "first_name": "A", "last_name": "B", "phone": "1234567890",
        "incident_date": "2026-01-01", "loss_type": "Theft",
        "incident_description": "Items stolen from vehicle.",
    }
    claim_id = claims_repo.insert_claim(conn, data)
    result = claims_repo.find_claim_by_id(conn, claim_id)
    assert result["status"] == "Draft"


# ---------------------------------------------------------------------------
# generate_claim_id — sequence
# ---------------------------------------------------------------------------

def test_generate_claim_id_sequential_same_day(conn):
    data = {
        "policy_number": "POL-001",
        "first_name": "X", "last_name": "Y", "phone": "1234567890",
        "incident_date": "2026-01-01", "loss_type": "Fire",
        "incident_description": "First fire incident description here.",
    }
    id1 = claims_repo.insert_claim(conn, data)
    id2 = claims_repo.insert_claim(conn, data)
    # Both share the same date prefix
    assert id1[:13] == id2[:13]  # CLM-YYYYMMDD-
    # Sequence numbers differ by 1
    seq1 = int(id1.split("-")[-1])
    seq2 = int(id2.split("-")[-1])
    assert seq2 == seq1 + 1


# ---------------------------------------------------------------------------
# find_claim_by_id
# ---------------------------------------------------------------------------

def test_find_claim_by_id_not_found(conn):
    assert claims_repo.find_claim_by_id(conn, "CLM-00000000-9999") is None


def test_find_claim_by_id_found(conn):
    data = {
        "policy_number": "POL-003",
        "first_name": "Carol", "last_name": "Williams", "phone": "5550001111",
        "incident_date": "2026-06-01", "loss_type": "Accident",
        "incident_description": "Car accident on the highway near exit 5.",
    }
    claim_id = claims_repo.insert_claim(conn, data)
    result = claims_repo.find_claim_by_id(conn, claim_id)
    assert result is not None
    assert result["claim_id"] == claim_id


# ---------------------------------------------------------------------------
# search_claims
# ---------------------------------------------------------------------------

def test_search_by_last_name_case_insensitive(conn):
    data = {
        "policy_number": "POL-001",
        "first_name": "Dana", "last_name": "Nguyen", "phone": "5551112222",
        "incident_date": "2026-05-01", "loss_type": "Theft",
        "incident_description": "Laptop and phone stolen from office.",
    }
    claims_repo.insert_claim(conn, data)
    results = claims_repo.search_claims(conn, "nguy")
    assert any(r["last_name"] == "Nguyen" for r in results)


def test_search_by_exact_claim_id(conn):
    data = {
        "policy_number": "POL-002",
        "first_name": "Eve", "last_name": "Brown", "phone": "5553334444",
        "incident_date": "2026-04-01", "loss_type": "Flood",
        "incident_description": "Ground floor flooded due to burst pipe.",
    }
    claim_id = claims_repo.insert_claim(conn, data)
    results = claims_repo.search_claims(conn, claim_id)
    assert len(results) == 1
    assert results[0]["claim_id"] == claim_id


def test_search_returns_max_50(conn):
    for i in range(55):
        claims_repo.insert_claim(conn, {
            "policy_number": "POL-001",
            "first_name": "Test", "last_name": "User", "phone": "1234567890",
            "incident_date": "2026-01-01", "loss_type": "Fire",
            "incident_description": "Test incident description for bulk insert.",
        })
    results = claims_repo.search_claims(conn, "User")
    assert len(results) == 50


# ---------------------------------------------------------------------------
# find_policy_by_number
# ---------------------------------------------------------------------------

def test_find_policy_found(conn):
    result = claims_repo.find_policy_by_number(conn, "POL-001")
    assert result is not None
    assert result["holder_name"] == "Alice Johnson"


def test_find_policy_not_found(conn):
    assert claims_repo.find_policy_by_number(conn, "POL-999") is None

"""
tests/integration/test_policies_api.py
Integration tests for the policies API — happy paths and error paths.

Uses the `client` fixture from conftest.py (httpx TestClient against the
FastAPI app with an in-memory SQLite database seeded with 7 sample policies).
Never touches claims.db.

Validates AC-19 (known policy returns 200 with details) and AC-20
(unknown policy returns 404 {"error": "Policy not found"}).
"""

import pytest


# ---------------------------------------------------------------------------
# Shared data — the 7 sample policies seeded by db.seed.seed()
# ---------------------------------------------------------------------------

SEEDED_POLICIES = [
    ("POL-001", "Alice Johnson", "Home"),
    ("POL-002", "Bob Martinez", "Auto"),
    ("POL-003", "Carol Williams", "Home"),
    ("POL-004", "David Chen", "Commercial"),
    ("POL-005", "Emily Thompson", "Life"),
    ("POL-006", "Frank Nguyen", "Auto"),
    ("POL-007", "Grace Patel", "Home"),
]


# ---------------------------------------------------------------------------
# Happy path — known policy returns 200 with full details (AC-19)
# ---------------------------------------------------------------------------

def test_get_known_policy_returns_200(client):
    """AC-19: GET /api/policies/POL-001 returns 200 with holder_name and policy_type."""
    resp = client.get("/api/policies/POL-001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["policy_number"] == "POL-001"
    assert body["holder_name"] == "Alice Johnson"
    assert body["policy_type"] == "Home"


@pytest.mark.parametrize(
    "policy_number, holder_name, policy_type",
    SEEDED_POLICIES,
    ids=[p[0] for p in SEEDED_POLICIES],
)
def test_get_each_seeded_policy_returns_200(
    client, policy_number, holder_name, policy_type
):
    """AC-19: every seeded policy (POL-001 .. POL-007) is retrievable with correct details."""
    resp = client.get(f"/api/policies/{policy_number}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["policy_number"] == policy_number
    assert body["holder_name"] == holder_name
    assert body["policy_type"] == policy_type


# ---------------------------------------------------------------------------
# Error path — unknown policy returns 404 (AC-20)
# ---------------------------------------------------------------------------

def test_get_unknown_policy_returns_404(client):
    """AC-20: GET /api/policies/UNKNOWN returns 404 with {"error": "Policy not found"}."""
    resp = client.get("/api/policies/UNKNOWN")
    assert resp.status_code == 404
    assert resp.json() == {"error": "Policy not found"}


def test_get_nonexistent_policy_returns_404(client):
    """AC-20: GET /api/policies/POL-999 returns 404 with {"error": "Policy not found"}."""
    resp = client.get("/api/policies/POL-999")
    assert resp.status_code == 404
    assert resp.json() == {"error": "Policy not found"}

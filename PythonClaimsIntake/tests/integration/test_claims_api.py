"""
tests/integration/test_claims_api.py
Integration tests for the claims API — happy paths and all error paths.

Uses the `client` fixture from conftest.py (httpx TestClient against the
FastAPI app with an in-memory SQLite database). Never touches claims.db.

Two 422 response shapes are exercised:
  - Pydantic validation errors (missing field, wrong Literal) -> {"detail": [...]}
  - Custom validation errors (phone, email, date, amount, description,
    unknown policy) -> {"error": "Validation failed", "fields": {...}}
"""

import re
from datetime import datetime, timedelta, timezone

import pytest


# ---------------------------------------------------------------------------
# Helpers and shared data
# ---------------------------------------------------------------------------

# CLM-YYYYMMDD-NNNN — 4-digit year, 2-digit month/day, 4-digit daily sequence.
_CLAIM_ID_RE = re.compile(r"^CLM-\d{8}-\d{4}$")


def _past_date(days_ago: int = 30) -> str:
    """ISO date string safely in the past (UTC)."""
    return (datetime.now(timezone.utc).date() - timedelta(days=days_ago)).isoformat()


def _future_date(days_ahead: int = 30) -> str:
    """ISO date string safely in the future (UTC)."""
    return (datetime.now(timezone.utc).date() + timedelta(days=days_ahead)).isoformat()


# A fully valid claim payload used as the base for most tests.
VALID_CLAIM = {
    "first_name": "John",
    "last_name": "Smith",
    "phone": "1234567890",
    "email": "john@example.com",
    "policy_number": "POL-001",
    "incident_date": _past_date(30),
    "loss_type": "Fire",
    "incident_description": "Kitchen fire caused significant damage to the property.",
    "estimated_loss_amount": 5000.0,
    "incident_location": "123 Main St",
}


def _valid_claim(**overrides) -> dict:
    """Return a fresh copy of VALID_CLAIM with optional field overrides."""
    return {**VALID_CLAIM, **overrides}


def _create_claim(client, claim=None) -> str:
    """POST a valid claim and return the generated claim_id."""
    resp = client.post("/api/claims", json=claim or _valid_claim())
    assert resp.status_code == 201, resp.text
    return resp.json()["claim_id"]


def _assert_pydantic_error(response, field_name: str) -> None:
    """Assert FastAPI's default 422 (Pydantic) error mentions the given field."""
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(d["loc"][-1] == field_name for d in detail), detail


def _assert_field_error(response, field_name: str) -> None:
    """Assert a custom 422 validation error with a fields dict."""
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "Validation failed"
    assert field_name in body["fields"], body


# ---------------------------------------------------------------------------
# Happy path tests
# ---------------------------------------------------------------------------

def test_post_valid_claim_returns_201(client):
    """AC-01: valid submission returns 201 with a CLM-YYYYMMDD-NNNN claim_id."""
    resp = client.post("/api/claims", json=_valid_claim())
    assert resp.status_code == 201
    body = resp.json()
    assert "claim_id" in body
    assert _CLAIM_ID_RE.match(body["claim_id"])


def test_post_valid_claim_minimal_fields(client):
    """Submitting only mandatory fields (no email/amount/location) succeeds."""
    minimal = {
        "first_name": "Jane",
        "last_name": "Doe",
        "phone": "5551234567",
        "policy_number": "POL-002",
        "incident_date": _past_date(10),
        "loss_type": "Flood",
        "incident_description": "Basement flooded after a heavy storm passed.",
    }
    resp = client.post("/api/claims", json=minimal)
    assert resp.status_code == 201
    assert _CLAIM_ID_RE.match(resp.json()["claim_id"])


def test_get_claim_by_id_returns_200(client):
    """AC: after creating a claim, GET by id returns 200 with all fields."""
    claim_id = _create_claim(client)
    resp = client.get(f"/api/claims/{claim_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["claim_id"] == claim_id
    assert body["first_name"] == "John"
    assert body["last_name"] == "Smith"
    assert body["phone"] == "1234567890"
    assert body["email"] == "john@example.com"
    assert body["policy_number"] == "POL-001"
    assert body["loss_type"] == "Fire"
    assert body["estimated_loss_amount"] == 5000.0
    assert body["incident_location"] == "123 Main St"
    assert body["status"] == "Draft"  # AC-02: new claims get Draft status


def test_search_claims_by_last_name(client):
    """AC-14: search by partial last name returns matching claims."""
    claim_id = _create_claim(client)
    resp = client.get("/api/claims", params={"q": "Smi"})
    assert resp.status_code == 200
    results = resp.json()
    matches = [r for r in results if r["claim_id"] == claim_id]
    assert matches, "created claim not found in search results"
    match = matches[0]
    # AC-15: each result shows id, name, policy number, loss type, date, status
    assert match["last_name"] == "Smith"
    assert match["loss_type"] == "Fire"
    assert match["policy_number"] == "POL-001"
    assert match["status"] == "Draft"


def test_get_claim_summary_returns_200(client):
    """AC-16: summary endpoint returns 200 with full claim record."""
    claim_id = _create_claim(client)
    resp = client.get(f"/api/claims/{claim_id}/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["claim_id"] == claim_id
    assert body["status"] == "Draft"


# ---------------------------------------------------------------------------
# Error path — missing mandatory fields (Pydantic 422 with detail array)
# ---------------------------------------------------------------------------

def test_post_missing_first_name_returns_422(client):
    """AC-04: missing first_name returns 422."""
    claim = _valid_claim()
    del claim["first_name"]
    resp = client.post("/api/claims", json=claim)
    _assert_pydantic_error(resp, "first_name")


def test_post_missing_last_name_returns_422(client):
    """AC-04: missing last_name returns 422."""
    claim = _valid_claim()
    del claim["last_name"]
    resp = client.post("/api/claims", json=claim)
    _assert_pydantic_error(resp, "last_name")


def test_post_missing_phone_returns_422(client):
    """AC-05: missing phone returns 422."""
    claim = _valid_claim()
    del claim["phone"]
    resp = client.post("/api/claims", json=claim)
    _assert_pydantic_error(resp, "phone")


def test_post_missing_policy_number_returns_422(client):
    """AC-07: missing policy_number returns 422."""
    claim = _valid_claim()
    del claim["policy_number"]
    resp = client.post("/api/claims", json=claim)
    _assert_pydantic_error(resp, "policy_number")


def test_post_missing_incident_date_returns_422(client):
    """AC-09: missing incident_date returns 422."""
    claim = _valid_claim()
    del claim["incident_date"]
    resp = client.post("/api/claims", json=claim)
    _assert_pydantic_error(resp, "incident_date")


def test_post_missing_loss_type_returns_422(client):
    """AC-09: missing loss_type returns 422."""
    claim = _valid_claim()
    del claim["loss_type"]
    resp = client.post("/api/claims", json=claim)
    _assert_pydantic_error(resp, "loss_type")


def test_post_missing_incident_description_returns_422(client):
    """AC-09: missing incident_description returns 422."""
    claim = _valid_claim()
    del claim["incident_description"]
    resp = client.post("/api/claims", json=claim)
    _assert_pydantic_error(resp, "incident_description")


# ---------------------------------------------------------------------------
# Error path — invalid field values
# ---------------------------------------------------------------------------

def test_post_invalid_loss_type_returns_422(client):
    """AC-11: loss_type not in the allowed Literal set returns 422."""
    claim = _valid_claim(loss_type="InvalidType")
    resp = client.post("/api/claims", json=claim)
    _assert_pydantic_error(resp, "loss_type")


def test_post_invalid_phone_returns_422(client):
    """AC-05: phone too short returns 422 with a phone field error."""
    claim = _valid_claim(phone="123")
    resp = client.post("/api/claims", json=claim)
    _assert_field_error(resp, "phone")


def test_post_invalid_email_returns_422(client):
    """AC-06: malformed email returns 422 with an email field error."""
    claim = _valid_claim(email="notanemail")
    resp = client.post("/api/claims", json=claim)
    _assert_field_error(resp, "email")


def test_post_future_incident_date_returns_422(client):
    """AC-10: incident_date in the future returns 422 with field error."""
    claim = _valid_claim(incident_date=_future_date(30))
    resp = client.post("/api/claims", json=claim)
    _assert_field_error(resp, "incident_date")


def test_post_unknown_policy_number_returns_422(client):
    """AC-08: policy_number not in the policies table returns 422."""
    claim = _valid_claim(policy_number="POL-999")
    resp = client.post("/api/claims", json=claim)
    _assert_field_error(resp, "policy_number")


@pytest.mark.parametrize("amount", [0, -100])
def test_post_loss_amount_not_positive_returns_422(client, amount):
    """AC-12: estimated_loss_amount <= 0 returns 422 with field error."""
    claim = _valid_claim(estimated_loss_amount=amount)
    resp = client.post("/api/claims", json=claim)
    _assert_field_error(resp, "estimated_loss_amount")


def test_post_short_description_returns_422(client):
    """Description shorter than 10 chars returns 422 with field error."""
    claim = _valid_claim(incident_description="short")
    resp = client.post("/api/claims", json=claim)
    _assert_field_error(resp, "incident_description")


# ---------------------------------------------------------------------------
# Error path — not found
# ---------------------------------------------------------------------------

def test_get_nonexistent_claim_returns_404(client):
    """AC-18: unknown claim id returns 404 with Claim not found."""
    resp = client.get("/api/claims/CLM-00000000-9999")
    assert resp.status_code == 404
    assert resp.json() == {"error": "Claim not found"}


def test_get_nonexistent_claim_summary_returns_404(client):
    """AC-18: unknown claim id on summary endpoint returns 404."""
    resp = client.get("/api/claims/CLM-00000000-9999/summary")
    assert resp.status_code == 404
    assert resp.json() == {"error": "Claim not found"}

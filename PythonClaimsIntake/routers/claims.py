"""
routers/claims.py
HTTP handlers for the claims API.

Rules (enforced by steering):
- Thin HTTP handlers: validate -> repo -> return response. No business logic.
- Use def, not async def — DB calls are synchronous.
- Error responses: {"error": string, "fields"?: {snake_case_field: message}}
"""

import sqlite3

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from db.claims_repo import (
    find_claim_by_id,
    find_policy_by_number,
    insert_claim,
    search_claims,
)
from db.database import get_db
from middleware.validate import (
    validate_description,
    validate_email,
    validate_incident_date,
    validate_loss_amount,
    validate_phone,
)
from models.claim import ClaimCreate, ClaimResponse, ClaimSearchResult

router = APIRouter(prefix="/api/claims", tags=["claims"])


def _validate_claim_fields(claim: ClaimCreate, conn: sqlite3.Connection) -> dict:
    """Run all custom validators plus the policy-existence check.

    Returns a dict mapping field_name -> message for every failed check.
    An empty dict means the payload is valid.
    """
    fields: dict[str, str] = {}

    result = validate_phone(claim.phone)
    if not result["valid"]:
        fields["phone"] = result["message"]

    result = validate_email(claim.email)
    if not result["valid"]:
        fields["email"] = result["message"]

    result = validate_incident_date(str(claim.incident_date))
    if not result["valid"]:
        fields["incident_date"] = result["message"]

    result = validate_loss_amount(claim.estimated_loss_amount)
    if not result["valid"]:
        fields["estimated_loss_amount"] = result["message"]

    result = validate_description(claim.incident_description)
    if not result["valid"]:
        fields["incident_description"] = result["message"]

    if find_policy_by_number(conn, claim.policy_number) is None:
        fields["policy_number"] = "Unknown policy number"

    return fields


def _claim_or_404(conn: sqlite3.Connection, claim_id: str) -> ClaimResponse | JSONResponse:
    """Fetch a claim by id; return a ClaimResponse or a 404 JSONResponse."""
    row = find_claim_by_id(conn, claim_id)
    if row is None:
        return JSONResponse(status_code=404, content={"error": "Claim not found"})
    return ClaimResponse(**row)


@router.post("", status_code=201)
def create_claim(claim: ClaimCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Register a new claim. Returns 201 with the generated claim_id."""
    fields = _validate_claim_fields(claim, conn)
    if fields:
        return JSONResponse(
            status_code=422,
            content={"error": "Validation failed", "fields": fields},
        )
    claim_id = insert_claim(conn, claim.model_dump())
    return {"claim_id": claim_id}


@router.get("", response_model=list[ClaimSearchResult])
def search_claims_endpoint(
    q: str | None = None, conn: sqlite3.Connection = Depends(get_db)
):
    """Search claims by exact claim_id or partial last name (max 50)."""
    if not q:
        return []
    return search_claims(conn, q)


@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(claim_id: str, conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve a single claim by its claim_id."""
    return _claim_or_404(conn, claim_id)


@router.get("/{claim_id}/summary", response_model=ClaimResponse)
def get_claim_summary(claim_id: str, conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve a claim for the read-only summary view."""
    return _claim_or_404(conn, claim_id)

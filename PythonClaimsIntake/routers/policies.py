"""
routers/policies.py
HTTP handlers for the policies API.

Rules (enforced by steering):
- Thin HTTP handlers: validate -> repo -> return response. No business logic.
- Use def, not async def — DB calls are synchronous.
- Error responses: {"error": string, "fields"?: {snake_case_field: message}}
"""

import sqlite3

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from db.claims_repo import find_policy_by_number
from db.database import get_db
from models.claim import PolicyResponse

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.get("/{policy_number}", response_model=PolicyResponse)
def get_policy(
    policy_number: str, conn: sqlite3.Connection = Depends(get_db)
):
    """Look up a policy by its policy number."""
    row = find_policy_by_number(conn, policy_number)
    if row is None:
        return JSONResponse(
            status_code=404, content={"error": "Policy not found"}
        )
    return PolicyResponse(**row)

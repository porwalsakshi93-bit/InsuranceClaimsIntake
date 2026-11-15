"""
models/claim.py
Pydantic v2 models for the insurance claims intake API.

Rules (enforced by steering):
- This module contains models only — no logic, no DB calls.
- Pydantic v2 syntax with Python 3.11+ union style (str | None).
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class ClaimCreate(BaseModel):
    """Inbound payload for registering a new claim."""

    first_name: str
    last_name: str
    phone: str
    email: str | None = None
    policy_number: str
    incident_date: date
    loss_type: Literal["Fire", "Flood", "Theft", "Accident", "Other"]
    incident_description: str
    estimated_loss_amount: float | None = None
    incident_location: str | None = None


class ClaimResponse(BaseModel):
    """Full claim record as returned by the API. incident_date is str
    because SQLite stores it as TEXT."""

    claim_id: str
    policy_number: str
    first_name: str
    last_name: str
    phone: str
    email: str | None
    incident_date: str
    loss_type: str
    incident_description: str
    estimated_loss_amount: float | None
    incident_location: str | None
    status: str
    created_at: str


class ClaimSearchResult(BaseModel):
    """Compact result row for search listings."""

    claim_id: str
    first_name: str
    last_name: str
    policy_number: str
    loss_type: str
    incident_date: str
    status: str


class PolicyResponse(BaseModel):
    """Policy details returned by the policy lookup endpoint."""

    policy_number: str
    holder_name: str
    policy_type: str

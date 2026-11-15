"""
middleware/validate.py
Pure validation functions for claim field values.

Rules (enforced by steering):
- Pure functions only — no DB access, no HTTP context.
- Never import from db/ or routers/.
- Each function returns {"valid": bool, "message": str}.
"""

import re
from datetime import datetime, timezone


# Standard email pattern: local@domain.tld where the TLD is at least 2 letters.
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_phone(phone: str) -> dict:
    """Digits only, 10-15 characters.

    Non-digit characters are stripped before the length check, so a
    formatted number such as "555-123-4567" is reduced to its digits.
    Returns {"valid": False, "message": "Phone must be 10-15 digits"} when
    the resulting digit count falls outside 10-15.
    """
    if not phone:
        return {"valid": False, "message": "Phone must be 10-15 digits"}
    digits = re.sub(r"\D", "", phone)
    if 10 <= len(digits) <= 15:
        return {"valid": True, "message": ""}
    return {"valid": False, "message": "Phone must be 10-15 digits"}


def validate_email(email: str | None) -> dict:
    """Standard email format. None/empty is valid (email is optional).

    Returns {"valid": False, "message": "Invalid email format"} when a
    non-empty value does not match the email pattern.
    """
    if not email:
        return {"valid": True, "message": ""}
    if _EMAIL_RE.match(email):
        return {"valid": True, "message": ""}
    return {"valid": False, "message": "Invalid email format"}


def validate_incident_date(date_str: str) -> dict:
    """Date must not be in the future (compared against server UTC date).

    Expects ISO format YYYY-MM-DD. Returns an error message for unparseable
    input or for dates later than today (UTC).
    """
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return {"valid": False, "message": "Invalid date format"}
    today = datetime.now(timezone.utc).date()
    if parsed > today:
        return {"valid": False, "message": "Incident date cannot be in the future"}
    return {"valid": True, "message": ""}


def validate_loss_amount(amount: float | None) -> dict:
    """Must be greater than 0 if provided.

    None is valid (the field is optional). Zero or negative values are
    rejected with "Estimated loss amount must be greater than 0".
    """
    if amount is None:
        return {"valid": True, "message": ""}
    if amount <= 0:
        return {"valid": False, "message": "Estimated loss amount must be greater than 0"}
    return {"valid": True, "message": ""}


def validate_description(text: str) -> dict:
    """Must be 10-2000 characters.

    Returns "Description must be at least 10 characters" when too short and
    "Description must not exceed 2000 characters" when too long.
    """
    if not isinstance(text, str) or len(text) < 10:
        return {"valid": False, "message": "Description must be at least 10 characters"}
    if len(text) > 2000:
        return {"valid": False, "message": "Description must not exceed 2000 characters"}
    return {"valid": True, "message": ""}

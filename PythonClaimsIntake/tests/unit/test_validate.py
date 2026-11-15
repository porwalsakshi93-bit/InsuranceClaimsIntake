"""
tests/unit/test_validate.py
Unit tests for middleware/validate.py — pure validation functions.

Covers each of the 5 validators with 3+ valid inputs, 3+ invalid inputs,
and boundary values. No DB access, no HTTP context, never touches claims.db.
"""

from datetime import datetime, timezone, timedelta, date

import pytest

from middleware.validate import (
    validate_phone,
    validate_email,
    validate_incident_date,
    validate_loss_amount,
    validate_description,
)


# Helpers ---------------------------------------------------------------------

def _today_utc():
    return datetime.now(timezone.utc).date()


# ---------------------------------------------------------------------------
# validate_phone
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "phone",
    [
        "5551234567",          # exactly 10 digits
        "555123456789012",     # exactly 15 digits
        "555-123-4567",        # formatted, strips to 10 digits
        "(555) 123-4567",      # parentheses/spaces stripped
    ],
)
def test_validate_phone_valid(phone):
    assert validate_phone(phone)["valid"] is True


@pytest.mark.parametrize(
    "phone",
    [
        "",                    # empty
        "123456789",           # 9 digits — too short
        "1234567890123456",    # 16 digits — too long
        "abcdef",              # no digits at all
    ],
)
def test_validate_phone_invalid(phone):
    result = validate_phone(phone)
    assert result["valid"] is False
    assert result["message"]


def test_validate_phone_boundary_9_digits_invalid():
    assert validate_phone("123456789")["valid"] is False


def test_validate_phone_boundary_10_digits_valid():
    assert validate_phone("1234567890")["valid"] is True


def test_validate_phone_boundary_15_digits_valid():
    assert validate_phone("123456789012345")["valid"] is True


def test_validate_phone_boundary_16_digits_invalid():
    assert validate_phone("1234567890123456")["valid"] is False


# ---------------------------------------------------------------------------
# validate_email
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "email",
    [
        None,                          # optional field — None is valid
        "",                             # empty is valid (optional)
        "user@example.com",            # simple valid
        "first.last@sub.example.co.uk",  # complex valid with subdomain + multi-TLD
        "a_b.c%d-e+1@mail-domain.org",  # valid special chars in local part
    ],
)
def test_validate_email_valid(email):
    assert validate_email(email)["valid"] is True


@pytest.mark.parametrize(
    "email",
    [
        "notanemail",       # no @ at all
        "@nodomain.com",    # missing local part
        "user@",            # missing domain
        "user@@example.com",  # multiple @ — domain part has invalid char
    ],
)
def test_validate_email_invalid(email):
    result = validate_email(email)
    assert result["valid"] is False
    assert result["message"]


def test_validate_email_boundary_empty_valid():
    assert validate_email("")["valid"] is True


def test_validate_email_boundary_simple_valid():
    assert validate_email("user@example.com")["valid"] is True


def test_validate_email_boundary_complex_valid():
    assert validate_email("first.last@sub.example.co.uk")["valid"] is True


def test_validate_email_boundary_notanemail_invalid():
    assert validate_email("notanemail")["valid"] is False


def test_validate_email_boundary_no_local_invalid():
    assert validate_email("@nodomain.com")["valid"] is False


def test_validate_email_boundary_no_domain_invalid():
    assert validate_email("user@")["valid"] is False


# ---------------------------------------------------------------------------
# validate_incident_date
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "date_str",
    [
        _today_utc().isoformat(),                          # today (UTC)
        (_today_utc() - timedelta(days=1)).isoformat(),    # yesterday
        "2000-01-01",                                       # far past date
        "1999-12-31",                                       # another past date
    ],
)
def test_validate_incident_date_valid(date_str):
    assert validate_incident_date(date_str)["valid"] is True


@pytest.mark.parametrize(
    "date_str",
    [
        (_today_utc() + timedelta(days=1)).isoformat(),    # tomorrow — future
        "invalid-date",                                     # unparseable
        "2026/01/01",                                       # wrong separator
        "2026-13-01",                                       # impossible month
    ],
)
def test_validate_incident_date_invalid(date_str):
    result = validate_incident_date(date_str)
    assert result["valid"] is False
    assert result["message"]


def test_validate_incident_date_boundary_today_valid():
    assert validate_incident_date(_today_utc().isoformat())["valid"] is True


def test_validate_incident_date_boundary_yesterday_valid():
    yesterday = (_today_utc() - timedelta(days=1)).isoformat()
    assert validate_incident_date(yesterday)["valid"] is True


def test_validate_incident_date_boundary_tomorrow_invalid():
    tomorrow = (_today_utc() + timedelta(days=1)).isoformat()
    result = validate_incident_date(tomorrow)
    assert result["valid"] is False
    assert "future" in result["message"].lower()


def test_validate_incident_date_boundary_invalid_format():
    result = validate_incident_date("invalid-date")
    assert result["valid"] is False


def test_validate_incident_date_boundary_far_past_valid():
    assert validate_incident_date(date(1900, 1, 1).isoformat())["valid"] is True


def test_validate_incident_date_none_invalid():
    # None raises TypeError inside strptime → caught and reported invalid.
    result = validate_incident_date(None)
    assert result["valid"] is False


# ---------------------------------------------------------------------------
# validate_loss_amount
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "amount",
    [
        None,        # optional — None is valid
        0.01,        # just above zero
        1000000,     # large value
        99.99,       # fractional value
    ],
)
def test_validate_loss_amount_valid(amount):
    assert validate_loss_amount(amount)["valid"] is True


@pytest.mark.parametrize(
    "amount",
    [
        0,       # zero — not greater than 0
        -1,      # negative
        -0.01,   # small negative
    ],
)
def test_validate_loss_amount_invalid(amount):
    result = validate_loss_amount(amount)
    assert result["valid"] is False
    assert result["message"]


def test_validate_loss_amount_boundary_none_valid():
    assert validate_loss_amount(None)["valid"] is True


def test_validate_loss_amount_boundary_zero_invalid():
    assert validate_loss_amount(0)["valid"] is False


def test_validate_loss_amount_boundary_negative_invalid():
    assert validate_loss_amount(-1)["valid"] is False


def test_validate_loss_amount_boundary_small_positive_valid():
    assert validate_loss_amount(0.01)["valid"] is True


def test_validate_loss_amount_boundary_large_valid():
    assert validate_loss_amount(1000000)["valid"] is True


# ---------------------------------------------------------------------------
# validate_description
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "1234567890",                    # exactly 10 chars
        "x" * 2000,                      # exactly 2000 chars
        "A complete incident description goes here.",  # normal sentence
    ],
)
def test_validate_description_valid(text):
    assert validate_description(text)["valid"] is True


@pytest.mark.parametrize(
    "text",
    [
        "123456789",                     # 9 chars — too short
        "x" * 2001,                      # 2001 chars — too long
        None,                            # not a string
    ],
)
def test_validate_description_invalid(text):
    result = validate_description(text)
    assert result["valid"] is False
    assert result["message"]


def test_validate_description_boundary_9_chars_invalid():
    result = validate_description("123456789")
    assert result["valid"] is False
    assert "10" in result["message"]


def test_validate_description_boundary_10_chars_valid():
    assert validate_description("1234567890")["valid"] is True


def test_validate_description_boundary_2000_chars_valid():
    assert validate_description("x" * 2000)["valid"] is True


def test_validate_description_boundary_2001_chars_invalid():
    result = validate_description("x" * 2001)
    assert result["valid"] is False
    assert "2000" in result["message"]

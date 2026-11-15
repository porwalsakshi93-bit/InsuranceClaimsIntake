"""
tests/property/test_validation_properties.py
Property-based tests for middleware/validate.py using hypothesis.

Each property runs at least 100 examples (@settings(max_examples=100)).
The validators are pure functions — no DB access, no HTTP context, and these
tests never touch claims.db.
"""

from hypothesis import given, settings, strategies as st

from middleware.validate import (
    validate_phone,
    validate_email,
    validate_loss_amount,
    validate_description,
)


# Digit-only alphabet for phone number generation.
_DIGITS = st.characters(min_codepoint=ord("0"), max_codepoint=ord("9"))


# ---------------------------------------------------------------------------
# Phone — validate_phone
# ---------------------------------------------------------------------------

@given(st.text(alphabet=_DIGITS, min_size=1, max_size=20))
@settings(max_examples=100)
def test_phone_valid_iff_digit_count_in_range(phone):
    """**Validates: AC-05** — A phone is valid exactly when it has 10-15 digits.

    The strategy yields digit-only strings of length 1-20. The validator
    strips non-digits (a no-op here) and rejects falsy values (excluded by
    min_size=1), so validity depends solely on the digit count being within
    the inclusive [10, 15] range.
    """
    result = validate_phone(phone)
    if 10 <= len(phone) <= 15:
        assert result["valid"] is True, (
            f"expected valid for {len(phone)} digits: {phone!r}"
        )
    else:
        assert result["valid"] is False, (
            f"expected invalid for {len(phone)} digits: {phone!r}"
        )


# ---------------------------------------------------------------------------
# Email — validate_email
# ---------------------------------------------------------------------------

@given(st.text(min_size=1, max_size=50).filter(lambda s: "@" not in s))
@settings(max_examples=100)
def test_email_without_at_is_invalid(email):
    """**Validates: AC-06** — A non-empty email string without '@' is invalid.

    The required pattern contains a literal '@', so any non-empty string
    lacking one can never match and must be rejected.
    """
    result = validate_email(email)
    assert result["valid"] is False, f"expected invalid for '@'-less string: {email!r}"


# ---------------------------------------------------------------------------
# Loss amount — validate_loss_amount
# ---------------------------------------------------------------------------

@given(st.floats(min_value=-10000, max_value=10000))
@settings(max_examples=100)
def test_loss_amount_sign_property(amount):
    """**Validates: AC-12** — A loss amount is valid iff it is strictly > 0.

    The strategy generates finite floats (NaN/inf excluded by the bounded
    range). None is valid but is exercised by the unit tests; here every
    generated float must be accepted when positive and rejected when zero
    or negative (including -0.0, which compares equal to 0.0).
    """
    result = validate_loss_amount(amount)
    if amount > 0:
        assert result["valid"] is True, f"expected valid for positive amount: {amount!r}"
    else:
        assert result["valid"] is False, (
            f"expected invalid for non-positive amount: {amount!r}"
        )


# ---------------------------------------------------------------------------
# Description — validate_description
# ---------------------------------------------------------------------------

@given(st.text(min_size=1, max_size=3000))
@settings(max_examples=100)
def test_description_length_property(text):
    """**Validates: AC-09** — A description is valid iff its length is in [10, 2000].

    Every generated value is a str, so the isinstance check passes and
    validity is determined entirely by the 10-2000 character bounds.
    """
    result = validate_description(text)
    if 10 <= len(text) <= 2000:
        assert result["valid"] is True, f"expected valid for {len(text)} chars"
    else:
        assert result["valid"] is False, f"expected invalid for {len(text)} chars"

---
inclusion: always
---

# Security & Testing Expectations

## SQL Security
- All SQL queries MUST use parameterised statements (? placeholders).
- String interpolation into SQL is NEVER acceptable, even for trusted values.
- Foreign-key enforcement must be enabled: `PRAGMA foreign_keys = ON`.

## Input Validation
- Every field must be validated server-side before any DB write — Pydantic + middleware/validate.py.
- Client-side validation (static/js/validate.js) is a UX convenience only; never trust it as security.
- Reject unknown `loss_type` values via Pydantic `Literal` type.

## Secrets & Configuration
- Never hard-code DB paths, secrets, or environment-specific values in source files.
- Use `.env` (excluded from git) and `python-dotenv` for all config.
- `.env` and `claims.db` must be listed in `.gitignore`.

## Error Handling
- Never expose raw exception messages or stack traces to the client.
- All unhandled exceptions return generic `{"error": "Internal server error"}` with HTTP 500.
- Log errors server-side (print to stderr is acceptable for this project scope).

## Testing Expectations
- Every validator function must have unit tests covering: valid inputs, invalid inputs, and boundary values.
- Every repo function must have a unit test using in-memory SQLite.
- Integration tests must verify both success and all documented error cases (422, 404).
- Property-based tests must run at least 100 examples per property (`@settings(max_examples=100)`).
- Test files must never import or touch `claims.db`.
- Test coverage must include the happy path and all validation error branches.

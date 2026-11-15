---
inclusion: always
---

# Architecture & Module Conventions

## Folder Responsibilities
- `db/` — ONLY place that executes SQL. All functions synchronous.
- `models/` — Pydantic models only; no logic, no DB calls.
- `middleware/` — pure validation functions; no DB access, no HTTP context.
- `routers/` — thin HTTP handlers: validate → repo → return response. No business logic.
- `templates/` — Jinja2 HTML. No inline business logic.
- `static/js/` — frontend modules. `api.js` is sole file making fetch() calls.
- `tests/` — three layers: unit, property, integration.

## Claim ID Format
`CLM-YYYYMMDD-NNNN` — e.g. `CLM-20261106-0001`
Generated inside the insert transaction in `generate_claim_id()`.

## Dependency Flow
```
HTTP Request
  → FastAPI router (routers/)
    → middleware/validate.py  (pure validation)
    → db/claims_repo.py       (SQL queries)
      → SQLite
```

## Error Response Contract
Always: `{ "error": string, "fields"?: { snake_case_field: message } }`
HTTP 422 for validation errors. HTTP 404 for not found. HTTP 500 for unexpected.

## Test Isolation Rule
All tests use in-memory SQLite via `get_db` dependency override in `conftest.py`.
The file `claims.db` must never be created or read during test runs.

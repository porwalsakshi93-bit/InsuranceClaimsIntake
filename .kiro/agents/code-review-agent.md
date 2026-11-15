# Code Review Agent — Insurance Claims Intake

## Purpose
A specialised agent that reviews Python source files in this project for:
1. Security issues (SQL injection, exposed secrets, unvalidated input)
2. Test coverage gaps (missing unit tests, untested error branches)
3. Coding standard violations (async in DB layer, ORM usage, missing parameterisation)
4. Business rule compliance (claim ID format, mandatory field enforcement, atomic transactions)

## How to Invoke
In Kiro chat, type:
```
@code-review-agent review db/claims_repo.py
@code-review-agent review middleware/validate.py
@code-review-agent review routers/claims.py
```

## Review Checklist

### Security
- [ ] All SQL uses `?` placeholders — no f-strings or `.format()` in SQL
- [ ] `PRAGMA foreign_keys = ON` is set in `database.py`
- [ ] No secrets, DB paths, or credentials hard-coded in source
- [ ] Route handlers return generic error messages — no raw exception text exposed
- [ ] Input validated server-side before any DB write

### DB Layer (`db/`)
- [ ] No `async`/`await` anywhere in `db/` folder
- [ ] `generate_claim_id` and `insert_claim` share one transaction
- [ ] All functions accept `conn: sqlite3.Connection` as first argument
- [ ] `row_factory = sqlite3.Row` set so results are accessible by column name

### Models (`models/`)
- [ ] `loss_type` uses `Literal[...]` — not bare `str`
- [ ] Optional fields have `= None` default
- [ ] `incident_date` typed as `date`, not `str`

### Validation (`middleware/validate.py`)
- [ ] Each function returns `{"valid": bool, "message": str}`
- [ ] No DB calls or HTTP context in validators
- [ ] `validate_incident_date` compares against UTC, not local time

### Routers (`routers/`)
- [ ] Handlers use `def`, not `async def`, when calling DB functions
- [ ] Policy existence checked before `insert_claim` is called
- [ ] All 422 responses include `"fields"` map with snake_case keys

### Tests
- [ ] Unit tests cover valid input, invalid input, and boundary values for each validator
- [ ] `test_claims_repo.py` uses in-memory SQLite — no file path to `claims.db`
- [ ] Property tests decorated with `@settings(max_examples=100)` or higher
- [ ] Integration tests verify 422 on missing field, future date, unknown policy
- [ ] `conftest.py` overrides `get_db` dependency — does not call `init_db("claims.db")`

## Output Format
For each issue found, report:
```
FILE: routers/claims.py
LINE: 34
SEVERITY: HIGH | MEDIUM | LOW
ISSUE: Raw exception message exposed in error response
FIX: Return {"error": "Internal server error"} instead of str(e)
```

If no issues are found, confirm: `✅ No issues found in <filename>`

---
name: claim-reviewer
description: Review any Python source file in the Insurance Claims Intake project for security issues, coding standard violations, and test coverage gaps. Use when you have edited db/, middleware/, models/, routers/, or tests/ files and want instant feedback before committing.
metadata:
  author: Kiro
  version: 1.0.0
  project: Insurance Claims Intake
---

## What this skill does

Runs `scripts/review.py` against a target file and reports:

- **Security issues** — SQL injection risk, exposed secrets, unvalidated input
- **Coding standard violations** — async in DB layer, ORM usage, missing parameterisation
- **Architecture violations** — SQL outside `db/`, HTTP context in `middleware/`
- **Test coverage gaps** — missing boundary tests, wrong DB path, missing dependency override

## How to invoke

```
/claim-reviewer db/claims_repo.py
/claim-reviewer middleware/validate.py
/claim-reviewer routers/claims.py
/claim-reviewer tests/integration/test_claims_api.py
```

Or just say: **"review routers/claims.py with the claim-reviewer skill"**

## Execution steps

When invoked with a file path argument, Kiro will:

1. Run the bundled review script against the specified file:
   ```bash
   py .kiro/skills/claim-reviewer/scripts/review.py <file_path>
   ```
   The script is run from the `PythonClaimsIntake/` directory.

2. Read the script output — it lists every finding with FILE / LINE / SEVERITY / ISSUE / FIX.

3. For each HIGH severity finding, show the corrected code inline.

4. Summarise: total findings by severity, and a final ✅ or ❌ verdict.

## Output format

Each finding:
```
[HIGH]   routers/claims.py:34  — async def used for DB-calling handler
         FIX: change `async def create_claim` → `def create_claim`

[MEDIUM] middleware/validate.py:12  — email validator called with positional bool
         FIX: return {"valid": False, "message": "..."} not (False, "...")
```

Clean file:
```
✅ db/claims_repo.py — 0 findings. All rules pass.
```

## Rules checked

| Rule | Applies to |
|------|-----------|
| All SQL uses `?` placeholders | `db/` |
| No `async`/`await` in `db/` | `db/` |
| `generate_claim_id` + `insert_claim` in one transaction | `db/claims_repo.py` |
| Each validator returns `{"valid": bool, "message": str}` | `middleware/` |
| No DB/HTTP imports in `middleware/` | `middleware/` |
| `loss_type` uses `Literal[...]` | `models/claim.py` |
| Route handlers use `def` not `async def` when calling DB | `routers/` |
| 422 errors include `"fields"` dict | `routers/` |
| Tests use `:memory:` not `claims.db` path | `tests/` |
| `@settings(max_examples=100)` on property tests | `tests/property/` |
| `conftest.py` overrides `get_db` dependency | `tests/` |

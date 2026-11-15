# Design — Python Insurance Claims Intake

## System Architecture

```
Browser
 ├── GET /  /intake  /summary  /search  →  Jinja2 HTML (templates/)
 ├── GET /static/css  /static/js         →  FastAPI StaticFiles
 └── /api/* JSON
       │
       ▼
  FastAPI app (main.py)
       ├── APIRouter /api/claims    → routers/claims.py
       │       ├── middleware/validate.py   (pure validation)
       │       └── db/claims_repo.py        (SQL)
       │                └── SQLite (claims.db / :memory:)
       └── APIRouter /api/policies  → routers/policies.py
               └── db/claims_repo.py → SQLite
```

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS policies (
    policy_number TEXT PRIMARY KEY,
    holder_name   TEXT NOT NULL,
    policy_type   TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id              TEXT PRIMARY KEY,
    policy_number         TEXT NOT NULL REFERENCES policies(policy_number),
    first_name            TEXT NOT NULL,
    last_name             TEXT NOT NULL,
    phone                 TEXT NOT NULL,
    email                 TEXT,
    incident_date         TEXT NOT NULL,
    loss_type             TEXT NOT NULL,
    incident_description  TEXT NOT NULL,
    estimated_loss_amount REAL,
    incident_location     TEXT,
    status                TEXT NOT NULL DEFAULT 'Draft',
    created_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_claims_last_name   ON claims(last_name);
CREATE INDEX IF NOT EXISTS idx_claims_policy      ON claims(policy_number);
CREATE INDEX IF NOT EXISTS idx_claims_created_at  ON claims(created_at);
```

## API Contract

| Method | Path | Success | Error |
|---|---|---|---|
| POST | /api/claims | 201 `{"claim_id":"CLM-..."}` | 422 `{"error":..,"fields":{..}}` |
| GET | /api/claims?q= | 200 list of ClaimSearchResult | — |
| GET | /api/claims/{id} | 200 ClaimResponse | 404 |
| GET | /api/claims/{id}/summary | 200 ClaimResponse | 404 |
| GET | /api/policies/{number} | 200 PolicyResponse | 404 |

## Pydantic Models (`models/claim.py`)

```python
class ClaimCreate(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str | None = None
    policy_number: str
    incident_date: date
    loss_type: Literal["Fire","Flood","Theft","Accident","Other"]
    incident_description: str
    estimated_loss_amount: float | None = None
    incident_location: str | None = None

class ClaimResponse(BaseModel):
    claim_id: str; policy_number: str
    first_name: str; last_name: str; phone: str; email: str | None
    incident_date: str; loss_type: str; incident_description: str
    estimated_loss_amount: float | None; incident_location: str | None
    status: str; created_at: str

class ClaimSearchResult(BaseModel):
    claim_id: str; first_name: str; last_name: str
    policy_number: str; loss_type: str; incident_date: str; status: str

class PolicyResponse(BaseModel):
    policy_number: str; holder_name: str; policy_type: str
```

## Validation Functions (`middleware/validate.py`)

| Function | Rule | Returns |
|---|---|---|
| `validate_phone(phone)` | digits only, 10–15 chars | `{valid, message}` |
| `validate_email(email)` | standard email regex | `{valid, message}` |
| `validate_incident_date(date_str)` | not in the future (UTC) | `{valid, message}` |
| `validate_loss_amount(amount)` | > 0 | `{valid, message}` |
| `validate_description(text)` | 10–2000 chars | `{valid, message}` |

## Claim ID Algorithm

```python
def generate_claim_id(conn):
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"CLM-{today}-"
    row = conn.execute(
        "SELECT COUNT(*) FROM claims WHERE claim_id LIKE ?", (f"{prefix}%",)
    ).fetchone()
    return f"{prefix}{(row[0] or 0) + 1:04d}"
```
Runs inside the insert transaction — race-condition safe.

## Testing Strategy

| Layer | File | Tool | Focus |
|---|---|---|---|
| Unit | tests/unit/test_validate.py | pytest | each validator, valid/invalid/boundary |
| Unit | tests/unit/test_claims_repo.py | pytest | insert, find, search, ID seq — in-memory |
| Property | tests/property/test_validation_properties.py | hypothesis | 100+ random inputs per rule |
| Integration | tests/integration/test_claims_api.py | httpx TestClient | all HTTP paths + error cases |
| Integration | tests/integration/test_policies_api.py | httpx TestClient | policy lookup + 404 |

`tests/conftest.py`: `db_conn` fixture (in-memory SQLite + schema + seed), `client` fixture (TestClient with `get_db` override).

---
inclusion: always
---

# Tech Stack & Coding Standards

## Runtime & Framework
- **Python 3.11+** — server runtime
- **FastAPI** — HTTP server and routing; use `APIRouter` for each resource
- **Pydantic v2** — request/response validation and models
- **Jinja2** — server-rendered HTML templates
- **python-dotenv** — environment config via `.env` file
- **sqlite3** — Python stdlib synchronous driver; NO async/await in DB layer

## Frontend
- Vanilla HTML / CSS / JavaScript — no framework, no bundler
- JS split into single-responsibility modules loaded via `<script>` tags

## Testing Tools
- **pytest** — unit and integration tests (`pytest --tb=short -v`)
- **hypothesis** — property-based tests; minimum `@settings(max_examples=100)` per property
- **httpx TestClient** — HTTP integration tests against FastAPI app
- In-memory SQLite (`:memory:`) for all DB tests — never touch `claims.db`

## Key Coding Constraints
- `sqlite3` is synchronous — never use `async`/`await` in `db/` layer
- Route handlers that call DB must use `def`, not `async def`
- No ORM — raw parameterised SQL only in `db/claims_repo.py`
- No frontend build step — `static/` served directly via FastAPI `StaticFiles`
- All error responses: `{ "error": string, "fields"?: { field_name: message } }`
- All API endpoints prefixed `/api`

## Common Commands
```bash
pip install -r requirements.txt    # install dependencies
uvicorn main:app --reload           # start server (from PythonClaimsIntake/)
python -m db.seed                   # seed sample policies
pytest --tb=short -v                # run all tests
```

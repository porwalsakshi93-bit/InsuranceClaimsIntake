# Implementation Plan: Python Insurance Claims Intake

## Overview
A Python/FastAPI web app for insurance First Notice of Loss (FNOL) intake. 24 tasks across 6 phases: scaffold, data layer, models & validation, API layer, frontend, and verification. The app lets insurance staff and customers register claims with a unique CLM-YYYYMMDD-NNNN ID, validate data server-side, search/retrieve claims, and view printable summaries.

## Task Dependency Graph

```json
{
  "waves": [
    ["TASK-01"],
    ["TASK-02", "TASK-07", "TASK-08"],
    ["TASK-03", "TASK-09", "TASK-10"],
    ["TASK-04", "TASK-05"],
    ["TASK-06", "TASK-11", "TASK-12", "TASK-14"],
    ["TASK-13"],
    ["TASK-15", "TASK-16", "TASK-17", "TASK-21", "TASK-22"],
    ["TASK-18", "TASK-19", "TASK-20"],
    ["TASK-23"],
    ["TASK-24"]
  ],
  "dependencies": {
    "TASK-01": [],
    "TASK-02": ["TASK-01"],
    "TASK-03": ["TASK-02"],
    "TASK-04": ["TASK-03"],
    "TASK-05": ["TASK-03"],
    "TASK-06": ["TASK-05"],
    "TASK-07": ["TASK-01"],
    "TASK-08": ["TASK-01"],
    "TASK-09": ["TASK-08"],
    "TASK-10": ["TASK-08"],
    "TASK-11": ["TASK-05", "TASK-07", "TASK-08"],
    "TASK-12": ["TASK-05", "TASK-07"],
    "TASK-13": ["TASK-11", "TASK-12"],
    "TASK-14": ["TASK-03", "TASK-05"],
    "TASK-15": ["TASK-11", "TASK-13", "TASK-14"],
    "TASK-16": ["TASK-12", "TASK-13", "TASK-14"],
    "TASK-17": ["TASK-13"],
    "TASK-18": ["TASK-13", "TASK-17"],
    "TASK-19": ["TASK-13", "TASK-17"],
    "TASK-20": ["TASK-13", "TASK-17"],
    "TASK-21": ["TASK-13"],
    "TASK-22": ["TASK-13"],
    "TASK-23": ["TASK-06", "TASK-09", "TASK-10", "TASK-15", "TASK-16", "TASK-18", "TASK-19", "TASK-20", "TASK-21", "TASK-22"],
    "TASK-24": ["TASK-23"]
  }
}
```

## Notes
- All DB code synchronous (sqlite3 stdlib) - no async/await in db/ layer
- Tests use in-memory SQLite (:memory:) - never touch claims.db
- Raw parameterised SQL only - no ORM, no string interpolation
- Frontend is vanilla JS/HTML/CSS - no build step, no framework
- All error responses: {"error": string, "fields"?: {field_name: message}}
- Claim ID format: CLM-YYYYMMDD-NNNN, daily sequence resets each UTC day
- Foreign-key enforcement: PRAGMA foreign_keys = ON

## Tasks

## Phase 1 - Scaffold
- [x] TASK-01: Project files - requirements.txt, .gitignore, .env.example, all __init__.py
- [x] TASK-02: db/schema.sql - policies + claims tables + 3 indexes
- [x] TASK-03: db/database.py - init_db(), set_db(), get_db()
- [x] TASK-04: db/seed.py - 7 sample policies, INSERT OR IGNORE

## Phase 2 - Data Layer
- [x] TASK-05: db/claims_repo.py - generate_claim_id, insert_claim, find_claim_by_id, search_claims, find_policy_by_number
- [x] TASK-06: tests/unit/test_claims_repo.py - insert, find, search, ID sequence, max 50

## Phase 3 - Models & Validation
- [x] TASK-07: models/claim.py - ClaimCreate, ClaimResponse, ClaimSearchResult, PolicyResponse
- [x] TASK-08: middleware/validate.py - 5 validator functions returning {valid, message}
- [x] TASK-09: tests/unit/test_validate.py - 3+ valid, 3+ invalid, boundary per validator
- [x] TASK-10: tests/property/test_validation_properties.py - 4 properties, 100 iterations each

## Phase 4 - API Layer
- [x] TASK-11: routers/claims.py - POST + 3x GET endpoints
- [x] TASK-12: routers/policies.py - GET policy endpoint
- [x] TASK-13: main.py - app, lifespan, routers, static, templates, page routes, 500 handler
- [x] TASK-14: tests/conftest.py - db_conn + client fixtures
- [x] TASK-15: tests/integration/test_claims_api.py - all happy + error paths
- [x] TASK-16: tests/integration/test_policies_api.py - 200 + 404

## Phase 5 - Frontend
- [x] TASK-17: static/js/validate.js + static/js/api.js
- [x] TASK-18: templates/intake.html + static/js/intake.js (4-step form)
- [x] TASK-19: templates/summary.html + static/js/summary.js
- [x] TASK-20: templates/search.html + static/js/search.js
- [x] TASK-21: templates/index.html (landing page)
- [x] TASK-22: static/css/styles.css

## Phase 6 - Verify
- [x] TASK-23: pytest --tb=short -v - all tests pass
- [x] TASK-24: README.md - setup, seed, start, test commands + Kiro capabilities used

# Requirements — Python Insurance Claims Intake

## User Stories

### US-01 Register a Claim
As an insurance staff member,
I want to submit a multi-step intake form with customer, policy, and incident details,
So that a new claim is registered with a unique ID and status of Draft.

**Acceptance Criteria:**
- AC-01: A valid submission returns HTTP 201 and a claim ID in format `CLM-YYYYMMDD-NNNN`
- AC-02: The claim is persisted with status `Draft`
- AC-03: All fields are written in a single atomic transaction — no partial saves

### US-02 Capture Customer Information
As a user filling in the intake form,
I want to enter my name, phone number, and email,
So that the insurer can contact me about my claim.

**Acceptance Criteria:**
- AC-04: `first_name` and `last_name` are mandatory; missing either returns 422 with field error
- AC-05: `phone` is mandatory; non-digit or wrong length returns 422 with field error
- AC-06: `email` is optional; if provided must be valid format or returns 422 with field error

### US-03 Capture Policy Information
As a user,
I want to enter my policy number,
So that the claim is linked to my policy.

**Acceptance Criteria:**
- AC-07: `policy_number` is mandatory; missing returns 422 with field error
- AC-08: An unrecognised `policy_number` returns 422 with a `policy_number` field error

### US-04 Capture Incident Information
As a user,
I want to describe what happened — date, type of loss, and description,
So that the insurer has enough detail to begin processing my claim.

**Acceptance Criteria:**
- AC-09: `incident_date`, `loss_type`, `incident_description` are mandatory
- AC-10: `incident_date` in the future returns 422 with `incident_date` field error
- AC-11: `loss_type` must be one of `Fire`, `Flood`, `Theft`, `Accident`, `Other`
- AC-12: `estimated_loss_amount`, if provided, must be > 0

### US-05 Retrieve Existing Claims
As an insurance staff member,
I want to search for claims by Claim ID or claimant last name,
So that I can quickly find and review a specific claim.

**Acceptance Criteria:**
- AC-13: Search by exact Claim ID returns one result or empty list
- AC-14: Search by last name returns all partial matches (case-insensitive), max 50 results
- AC-15: Each result shows: Claim ID, name, policy number, loss type, incident date, status

### US-06 Generate a Claim Summary
As an insurance staff member,
I want to view a read-only summary of all claim fields,
So that I can review or print it for the claimant.

**Acceptance Criteria:**
- AC-16: All fields are displayed; missing optional fields show "Not Provided"
- AC-17: The page is printable as a PDF via the browser print dialog
- AC-18: Unknown claim ID returns 404

### US-07 Policy Lookup
As the system,
I want to verify a policy number exists before accepting a claim,
So that claims are always linked to valid policies.

**Acceptance Criteria:**
- AC-19: `GET /api/policies/{policy_number}` returns 200 with policy details for a known number
- AC-20: Unknown policy number returns 404 `{"error": "Policy not found"}`

---

## Non-Functional Requirements

- Python 3.11+, FastAPI, SQLite via `sqlite3` stdlib, Pydantic v2, Jinja2
- DB layer fully synchronous — no `async`/`await`
- Raw parameterised SQL only — no ORM, no string interpolation
- Tests use in-memory SQLite; never touch `claims.db`
- pytest + hypothesis (≥100 iterations) + httpx TestClient
- All unhandled errors return `{"error": "Internal server error"}` — no stack traces to client

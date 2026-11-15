---
inclusion: always
---

# Product Context — Insurance Claims Intake

## What This App Does
A lightweight Python web app that guides insurance staff and customers through
the First Notice of Loss (FNOL) process.

## Core Features
- **Register a claim** — multi-step form; generates unique `CLM-YYYYMMDD-NNNN` ID on submit
- **Validate data** — mandatory fields + format rules enforced client-side and server-side
- **Retrieve claims** — search by Claim ID (exact) or last name (partial); max 50 results
- **Claim summary** — read-only view of all fields; missing optional fields show "Not Provided"; printable

## Mandatory Fields
`first_name`, `last_name`, `phone`, `policy_number`, `incident_date`, `loss_type`, `incident_description`

## Business Rules
- Every new claim gets status `Draft`
- `policy_number` must exist in the policies table before a claim is accepted
- `incident_date` cannot be in the future (validated against server UTC date)
- `estimated_loss_amount` must be > 0 if provided
- `loss_type` must be one of: `Fire`, `Flood`, `Theft`, `Accident`, `Other`
- All DB writes use a single atomic SQLite transaction — no partial saves
- Claim ID daily sequence resets each UTC calendar day
- Search results capped at 50 records

## Sample Policies (pre-seeded)
POL-001 Alice Johnson (Home), POL-002 Bob Martinez (Auto),
POL-003 Carol Williams (Home), POL-004 David Chen (Commercial),
POL-005 Emily Thompson (Life), POL-006 Frank Nguyen (Auto), POL-007 Grace Patel (Home)

## Out of Scope
Authentication, claim adjudication, document uploads, external integrations,
multi-currency, multi-language, mobile native apps.

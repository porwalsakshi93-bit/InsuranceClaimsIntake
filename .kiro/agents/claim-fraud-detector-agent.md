# Claim Fraud Detector Agent

## Purpose
A specialised agent that scans submitted insurance claims for fraud risk indicators
before adjudication. It detects patterns such as duplicate contact details, unusually
high loss amounts, repeated policies, suspiciously short descriptions, and claim bursts.

## How to Invoke
In Kiro chat, type any of these:

```
@claim-fraud-detector-agent run
@claim-fraud-detector-agent check CLM-20261106-0001
@claim-fraud-detector-agent report
```

## Agent Capabilities

### 1. Duplicate Contact Detection
Queries `claims.db` for phone numbers that appear on three or more distinct claims.
Flags those claims as HIGH risk — a single person filing multiple claims is a common
fraud pattern.

### 2. High Loss Amount Detection
Flags any claim where `estimated_loss_amount` exceeds $50,000.
These require additional manual verification before payout.

### 3. Repeated Policy in Time Window
Detects when the same `policy_number` is used to file two or more claims within a
30-day rolling window. Legitimate policyholders rarely file multiple claims in a month.

### 4. Suspiciously Short Description
Flags claims where `incident_description` is under 20 characters.
Genuine incident descriptions are typically detailed; very short ones may indicate
auto-submitted or fraudulent claims.

### 5. Claim Burst Detection
Detects when five or more claims are submitted on the same UTC calendar day.
A sudden burst of claims can indicate a coordinated fraud attempt.

## Execution Instructions

Run the bundled skill script from `PythonClaimsIntake/`:

```bash
py ../.kiro/skills/claim-fraud-detector/scripts/fraud_check.py <command> [claim_id]
```

Commands:
- `py fraud_check.py run` — scan all claims
- `py fraud_check.py check CLM-20261106-0001` — scan one claim
- `py fraud_check.py report` — full fraud risk summary

## Output Format

### Per Finding
```
[FRAUD-CHECK]  Duplicate phone
[CLAIM]        CLM-20261106-0003
[RISK]         HIGH
[DETAIL]       Phone 555-0100 appears on 4 claims
[ACTION]       Flag for manual review before adjudication
```

### Summary
```
Fraud scan complete: 2 HIGH, 1 MEDIUM, 0 LOW risk claims found.
```

## Risk Levels

| Level | Meaning |
|-------|---------|
| HIGH | Strong fraud indicator — manual review required |
| MEDIUM | Unusual pattern — worth investigating |
| LOW | Minor anomaly — monitor only |

## Project Context

- Database   : `PythonClaimsIntake/claims.db` (SQLite)
- Schema     : `PythonClaimsIntake/db/schema.sql`
- Loss types : Fire, Flood, Theft, Accident, Other
- Claim ID   : `CLM-YYYYMMDD-NNNN`
- Status     : Only `Draft` claims are scanned (not yet adjudicated)

---
name: claim-fraud-detector
description: Analyse submitted insurance claims in claims.db for fraud indicators including duplicate contacts, unusually high loss amounts, suspicious incident descriptions, repeated policy numbers, and clustering of claims by date. Use when you want a fraud risk report before adjudication.
metadata:
  author: Kiro
  version: 1.0.0
  project: Insurance Claims Intake
---

## What this skill does

Runs `scripts/fraud_check.py` against `claims.db` and flags claims with fraud risk indicators across five checks.

## How to invoke

```
/claim-fraud-detector run
/claim-fraud-detector check CLM-20261106-0001
/claim-fraud-detector report
```

Or in Kiro chat: **"run the claim-fraud-detector skill"**

## Execution steps

Run from the `PythonClaimsIntake/` directory:

```bash
py ../.kiro/skills/claim-fraud-detector/scripts/fraud_check.py <command> [claim_id]
```

| Command | What it does |
|---------|-------------|
| `run` | Runs all fraud checks across every claim in claims.db |
| `check <claim_id>` | Runs all checks for a single claim |
| `report` | Produces a full fraud risk summary with counts and recommendations |

## Fraud checks performed

| Check | Rule |
|-------|------|
| Duplicate phone | Same phone number on 3+ claims |
| High loss amount | estimated_loss_amount > 50000 |
| Duplicate policy in window | Same policy_number filed 2+ times within 30 days |
| Short description | incident_description under 20 characters |
| Claim burst | 5+ claims submitted in a single UTC day |

## Output format

```
[FRAUD-CHECK]  Duplicate phone
[CLAIM]        CLM-20261106-0003
[RISK]         HIGH | MEDIUM | LOW
[DETAIL]       Phone 555-0100 appears on 4 claims
[ACTION]       Flag for manual review before adjudication
```

Final line:
```
Fraud scan complete: 2 HIGH, 1 MEDIUM, 0 LOW risk claims found.
```

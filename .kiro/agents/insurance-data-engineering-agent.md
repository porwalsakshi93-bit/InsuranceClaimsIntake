# Insurance Data Engineering Agent

## Purpose
A specialised agent for the Insurance Claims Intake project that handles
data engineering tasks: schema analysis, data quality checks, query
optimisation, migration scripts, and pipeline health reporting.

## How to Invoke
In Kiro chat, type any of these:

```
@insurance-data-engineering-agent analyze schema
@insurance-data-engineering-agent check data quality
@insurance-data-engineering-agent optimize queries
@insurance-data-engineering-agent generate migration add_adjuster_column
@insurance-data-engineering-agent pipeline report
```

## Agent Capabilities

### 1. Schema Analysis
Reads `db/schema.sql` and `db/claims_repo.py`, then reports:
- Table definitions, column types, constraints
- Foreign key relationships
- Index coverage and any missing indexes
- Compliance with project rules (parameterised SQL, PRAGMA foreign_keys)

### 2. Data Quality Check
Queries the live `claims.db` database and checks:
- Mandatory fields are never NULL (first_name, last_name, phone, etc.)
- `incident_date` is never in the future
- `loss_type` is always one of: Fire, Flood, Theft, Accident, Other
- `estimated_loss_amount` is always > 0 when present
- `policy_number` always references a valid policy in the policies table
- `claim_id` format matches `CLM-YYYYMMDD-NNNN`
- Daily sequence numbers are gapless

### 3. Query Optimisation
Reviews every SQL statement in `db/claims_repo.py` and reports:
- Missing indexes for frequent query patterns
- N+1 query risks
- Queries that could benefit from covering indexes
- EXPLAIN QUERY PLAN output for each query

### 4. Migration Script Generation
When asked to add/modify schema, generates a safe migration script:
- Always uses `ALTER TABLE … ADD COLUMN` with a default value
- Never drops columns (SQLite limitation)
- Includes rollback comment
- Saves to `db/migrations/` with a timestamp prefix

### 5. Pipeline Health Report
Runs the full analysis suite and produces a single report covering:
- Schema compliance ✅ / ❌
- Data quality pass/fail per rule
- Query performance summary
- Recommendations with priority (HIGH / MEDIUM / LOW)

## Execution Instructions

For each capability, run the bundled skill script and interpret the output:

```bash
py .kiro/skills/insurance-data-engineer/scripts/analyze.py <command> [args]
```

Commands:
- `py analyze.py schema`
- `py analyze.py quality`
- `py analyze.py queries`
- `py analyze.py migration <column_spec>`
- `py analyze.py report`

## Output Format

### Finding
```
[RULE]     claim_id format
[STATUS]   ✅ PASS  /  ❌ FAIL  /  ⚠️  WARN
[DETAIL]   All 9 claim IDs match CLM-YYYYMMDD-NNNN
[ACTION]   None required
```

### Migration Script (example)
```sql
-- Migration: add adjuster_id column
-- Generated: 2026-11-06
-- Rollback: SQLite does not support DROP COLUMN; restore from backup
ALTER TABLE claims ADD COLUMN adjuster_id TEXT DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_claims_adjuster ON claims(adjuster_id);
```

## Project Context

- Database  : `PythonClaimsIntake/claims.db` (SQLite)
- Schema    : `PythonClaimsIntake/db/schema.sql`
- Repo      : `PythonClaimsIntake/db/claims_repo.py`
- Rules     : See `.kiro/steering/security.md` and `.kiro/steering/structure.md`
- Claim ID  : `CLM-YYYYMMDD-NNNN` — 4-digit daily sequence, resets per UTC day
- Loss types: Fire, Flood, Theft, Accident, Other
- Status    : New claims always start as `Draft`

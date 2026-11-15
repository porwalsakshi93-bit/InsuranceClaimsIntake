---
name: insurance-data-engineer
description: Insurance Data Engineering skill for the Claims Intake project. Use when you need to analyze the database schema, check data quality, review query performance, generate migration scripts, or produce a full pipeline health report.
metadata:
  author: Kiro
  version: 1.0.0
  project: Insurance Claims Intake
---

## What this skill does

Runs `scripts/analyze.py` against the live `claims.db` and project source files to perform five data engineering tasks.

## How to invoke

```
/insurance-data-engineer schema
/insurance-data-engineer quality
/insurance-data-engineer queries
/insurance-data-engineer migration add_adjuster_id TEXT
/insurance-data-engineer report
```

## Execution steps

Run the bundled script from the `PythonClaimsIntake/` directory:

```bash
py ../.kiro/skills/insurance-data-engineer/scripts/analyze.py <command>
```

| Command | What it does |
|---------|-------------|
| `schema` | Parses schema.sql and claims_repo.py — reports tables, indexes, FK constraints |
| `quality` | Queries claims.db for data quality violations (nulls, bad formats, FK breaks) |
| `queries` | Runs EXPLAIN QUERY PLAN on every SQL in claims_repo.py |
| `migration <spec>` | Generates a safe ALTER TABLE migration script |
| `report` | Runs all of the above and prints a combined pipeline health report |

## Output format

Each check prints:
```
[RULE]    <rule name>
[STATUS]  ✅ PASS | ❌ FAIL | ⚠️  WARN
[DETAIL]  <what was found>
[ACTION]  <what to do if not PASS>
```

Final summary line:
```
Pipeline health: ✅ ALL PASS  or  ❌ N issues found
```

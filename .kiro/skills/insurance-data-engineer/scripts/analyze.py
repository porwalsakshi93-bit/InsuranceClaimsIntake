"""
insurance-data-engineer/scripts/analyze.py
===========================================
Bundled script for the Insurance Data Engineering Agent / Skill.

Usage (run from PythonClaimsIntake/ directory):
    py ../.kiro/skills/insurance-data-engineer/scripts/analyze.py schema
    py ../.kiro/skills/insurance-data-engineer/scripts/analyze.py quality
    py ../.kiro/skills/insurance-data-engineer/scripts/analyze.py queries
    py ../.kiro/skills/insurance-data-engineer/scripts/analyze.py migration "adjuster_id TEXT"
    py ../.kiro/skills/insurance-data-engineer/scripts/analyze.py report

Exit codes:
    0  — all checks pass
    1  — one or more FAIL findings
    2  — usage / file-not-found error
"""

import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── resolve project paths ─────────────────────────────────────────────────────
HERE     = Path(__file__).resolve().parent
PROJECT  = HERE.parent.parent.parent.parent / "PythonClaimsIntake"
DB_PATH  = PROJECT / "claims.db"
SCHEMA   = PROJECT / "db" / "schema.sql"
REPO     = PROJECT / "db" / "claims_repo.py"
MIGS_DIR = PROJECT / "db" / "migrations"

VALID_LOSS_TYPES = {"Fire", "Flood", "Theft", "Accident", "Other"}
CLAIM_ID_RE      = re.compile(r"^CLM-\d{8}-\d{4}$")

findings = []   # list of (rule, status, detail, action)

# ── output helpers ────────────────────────────────────────────────────────────

def record(rule, status, detail, action="None required."):
    findings.append((rule, status, detail, action))
    icon = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}.get(status, "[INFO]")
    print(f"[RULE]    {rule}")
    print(f"[STATUS]  {icon}")
    print(f"[DETAIL]  {detail}")
    print(f"[ACTION]  {action}")
    print()

def separator(title):
    print("-" * 62)
    print(f"  {title}")
    print("-" * 62)
    print()

# ── DB connection ─────────────────────────────────────────────────────────────

def get_conn():
    if not DB_PATH.exists():
        print(f"ERROR: claims.db not found at {DB_PATH}", file=sys.stderr)
        print("Run the app first (uvicorn main:app) to create the database.",
              file=sys.stderr)
        sys.exit(2)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ── command: schema ───────────────────────────────────────────────────────────

def cmd_schema():
    separator("SCHEMA ANALYSIS")

    # 1. schema.sql exists
    if not SCHEMA.exists():
        record("schema.sql present", "FAIL", f"Not found at {SCHEMA}",
               "Create db/schema.sql with the policies and claims DDL.")
        return
    record("schema.sql present", "PASS", str(SCHEMA))

    sql = SCHEMA.read_text(encoding="utf-8")

    # 2. PRAGMA foreign_keys
    if "PRAGMA foreign_keys" in sql:
        record("PRAGMA foreign_keys = ON", "PASS",
               "Found in schema.sql — FK enforcement enabled on every connection.")
    else:
        record("PRAGMA foreign_keys = ON", "FAIL",
               "Missing from schema.sql",
               "Add: PRAGMA foreign_keys = ON; at the top of schema.sql")

    # 3. Both tables present
    for table in ("policies", "claims"):
        if re.search(rf"CREATE TABLE IF NOT EXISTS {table}", sql, re.IGNORECASE):
            record(f"Table '{table}' defined", "PASS",
                   f"CREATE TABLE IF NOT EXISTS {table} found in schema.sql")
        else:
            record(f"Table '{table}' defined", "FAIL",
                   f"Table '{table}' not found in schema.sql",
                   f"Add a CREATE TABLE IF NOT EXISTS {table} (...) block.")

    # 4. Required indexes
    for idx in ("idx_claims_last_name", "idx_claims_policy", "idx_claims_created_at"):
        if idx in sql:
            record(f"Index '{idx}'", "PASS", f"Found in schema.sql")
        else:
            record(f"Index '{idx}'", "FAIL",
                   f"Index '{idx}' missing from schema.sql",
                   f"Add: CREATE INDEX IF NOT EXISTS {idx} ON claims(...);")

    # 5. FK reference in claims table
    if "REFERENCES policies" in sql:
        record("claims.policy_number FK", "PASS",
               "claims.policy_number REFERENCES policies(policy_number) found.")
    else:
        record("claims.policy_number FK", "FAIL",
               "Foreign key reference not found in claims table definition.",
               "Add: policy_number TEXT NOT NULL REFERENCES policies(policy_number)")

    # 6. claims_repo.py uses ? placeholders
    if not REPO.exists():
        record("claims_repo.py present", "WARN", f"Not found at {REPO}")
        return
    repo_src = REPO.read_text(encoding="utf-8")
    if re.search(r'\.execute\s*\(\s*f["\']|\.format\s*\(', repo_src):
        record("Parameterised SQL", "FAIL",
               "String interpolation found in claims_repo.py SQL queries.",
               "Replace f-strings/.format() with ? placeholders.")
    else:
        record("Parameterised SQL", "PASS",
               "No string interpolation in SQL — all queries use ? placeholders.")

    # 7. No async in DB layer
    if re.search(r"\basync\s+def\b|\bawait\b", repo_src):
        record("No async/await in db/", "FAIL",
               "async or await keyword found in claims_repo.py.",
               "Remove async/await — sqlite3 is synchronous.")
    else:
        record("No async/await in db/", "PASS",
               "No async/await in claims_repo.py — DB layer is fully synchronous.")

# ── command: quality ──────────────────────────────────────────────────────────

def cmd_quality():
    separator("DATA QUALITY CHECK")
    conn = get_conn()

    total = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    if total == 0:
        print("  No claims in the database yet. Submit a claim via the app first.")
        print()
        return
    record("Claims in database", "PASS", f"{total} claim(s) found.")

    # 1. Mandatory non-null fields
    for col in ("first_name", "last_name", "phone", "policy_number",
                "incident_date", "loss_type", "incident_description"):
        n = conn.execute(
            f"SELECT COUNT(*) FROM claims WHERE {col} IS NULL OR {col} = ''"
        ).fetchone()[0]
        if n == 0:
            record(f"Mandatory field: {col}", "PASS",
                   f"All {total} rows have a non-empty {col}.")
        else:
            record(f"Mandatory field: {col}", "FAIL",
                   f"{n} row(s) have NULL or empty {col}.",
                   f"Investigate and back-fill {col} for those claim IDs.")

    # 2. loss_type values
    bad_types = conn.execute(
        "SELECT claim_id, loss_type FROM claims WHERE loss_type NOT IN "
        "('Fire','Flood','Theft','Accident','Other')"
    ).fetchall()
    if not bad_types:
        record("loss_type values", "PASS",
               f"All {total} rows have a valid loss_type (Fire/Flood/Theft/Accident/Other).")
    else:
        detail = ", ".join(f"{r['claim_id']}={r['loss_type']}" for r in bad_types[:5])
        record("loss_type values", "FAIL",
               f"{len(bad_types)} row(s) with invalid loss_type: {detail}",
               "Correct these values — only Fire, Flood, Theft, Accident, Other allowed.")

    # 3. incident_date not in the future
    today = datetime.now(timezone.utc).date().isoformat()
    future = conn.execute(
        "SELECT COUNT(*) FROM claims WHERE incident_date > ?", (today,)
    ).fetchone()[0]
    if future == 0:
        record("incident_date not future", "PASS",
               f"No rows have incident_date after today ({today}).")
    else:
        record("incident_date not future", "FAIL",
               f"{future} row(s) have incident_date in the future.",
               "These were inserted without server-side validation — remove or correct.")

    # 4. estimated_loss_amount > 0 when present
    bad_amount = conn.execute(
        "SELECT COUNT(*) FROM claims WHERE estimated_loss_amount IS NOT NULL "
        "AND estimated_loss_amount <= 0"
    ).fetchone()[0]
    if bad_amount == 0:
        record("estimated_loss_amount > 0", "PASS",
               "All provided estimated_loss_amount values are positive.")
    else:
        record("estimated_loss_amount > 0", "FAIL",
               f"{bad_amount} row(s) have estimated_loss_amount <= 0.",
               "Correct these values — amounts must be strictly positive.")

    # 5. FK integrity — every policy_number exists in policies
    orphans = conn.execute(
        "SELECT COUNT(*) FROM claims c "
        "LEFT JOIN policies p ON c.policy_number = p.policy_number "
        "WHERE p.policy_number IS NULL"
    ).fetchone()[0]
    if orphans == 0:
        record("FK integrity: policy_number", "PASS",
               "Every claim's policy_number exists in the policies table.")
    else:
        record("FK integrity: policy_number", "FAIL",
               f"{orphans} claim(s) reference a policy_number not in policies.",
               "Seed missing policies or correct the claim records.")

    # 6. claim_id format
    ids = conn.execute("SELECT claim_id FROM claims").fetchall()
    bad_ids = [r["claim_id"] for r in ids if not CLAIM_ID_RE.match(r["claim_id"])]
    if not bad_ids:
        record("claim_id format CLM-YYYYMMDD-NNNN", "PASS",
               f"All {total} claim IDs match the expected format.")
    else:
        record("claim_id format CLM-YYYYMMDD-NNNN", "FAIL",
               f"{len(bad_ids)} malformed IDs: {bad_ids[:5]}",
               "Investigate how these were inserted — generate_claim_id() should always be used.")

    # 7. status values
    bad_status = conn.execute(
        "SELECT COUNT(*) FROM claims WHERE status NOT IN ('Draft','Open','Closed')"
    ).fetchone()[0]
    if bad_status == 0:
        record("status values", "PASS",
               "All status values are valid (Draft / Open / Closed).")
    else:
        record("status values", "WARN",
               f"{bad_status} row(s) have unexpected status values.",
               "Check the status field — new claims should start as Draft.")

    conn.close()

# ── command: queries ──────────────────────────────────────────────────────────

def cmd_queries():
    separator("QUERY PERFORMANCE ANALYSIS")
    conn = get_conn()

    queries = {
        "generate_claim_id (COUNT by prefix)":
            "SELECT COUNT(*) FROM claims WHERE claim_id LIKE 'CLM-20261106-%'",
        "find_claim_by_id":
            "SELECT * FROM claims WHERE claim_id = 'CLM-20261106-0001'",
        "search_claims (exact ID)":
            "SELECT claim_id, first_name, last_name, policy_number, loss_type, "
            "incident_date, status FROM claims "
            "WHERE claim_id = 'CLM-20261106-0001' OR last_name LIKE '%Smith%' "
            "ORDER BY created_at DESC LIMIT 50",
        "find_policy_by_number":
            "SELECT * FROM policies WHERE policy_number = 'POL-001'",
    }

    for name, sql in queries.items():
        plan = conn.execute(f"EXPLAIN QUERY PLAN {sql}").fetchall()
        # SEARCH = index lookup (good), SCAN without INDEX = full table scan (bad)
        plan_details = " ".join(str(r) for r in plan)
        uses_index = (
            "SEARCH" in plan_details
            or "USING INDEX" in plan_details
            or "USING COVERING INDEX" in plan_details
            or "USING INTEGER PRIMARY KEY" in plan_details
        )
        is_full_scan = "SCAN" in plan_details and "USING" not in plan_details
        plan_str = " | ".join(str(dict(r)) for r in plan)
        # SEARCH = index seek (best), SCAN USING = covering index (good),
        # SCAN without USING = full table scan (slow)
        is_fast   = "SEARCH" in plan_details or "USING" in plan_details
        is_slow   = "SCAN" in plan_details and "USING" not in plan_details
        if is_fast:
            record(f"Query: {name}", "PASS",
                   f"Uses index. Plan: {plan_str[:120]}")
        elif is_slow:
            record(f"Query: {name}", "WARN",
                   f"Full table scan. Plan: {plan_str[:120]}",
                   "Consider adding an index if this query runs frequently.")
        else:
            record(f"Query: {name}", "PASS",
                   f"Plan: {plan_str[:120]}")

    # Check for missing useful indexes
    existing_indexes = [
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
    ]
    recommended = {
        "idx_claims_last_name": "claims(last_name) — used by search_claims LIKE query",
        "idx_claims_policy":    "claims(policy_number) — used by FK joins",
        "idx_claims_created_at":"claims(created_at) — used by ORDER BY created_at DESC",
    }
    for idx, reason in recommended.items():
        if idx in existing_indexes:
            record(f"Index present: {idx}", "PASS", f"Index on {reason}")
        else:
            record(f"Index missing: {idx}", "WARN",
                   f"Recommended index not found: {idx}",
                   f"Add: CREATE INDEX IF NOT EXISTS {idx} ON {reason.split(' — ')[0]};")

    conn.close()

# ── command: migration ────────────────────────────────────────────────────────

def cmd_migration(column_spec: str):
    separator("MIGRATION SCRIPT GENERATOR")

    if not column_spec:
        print("Usage: analyze.py migration \"<column_name> <type> [DEFAULT value]\"")
        print("Example: analyze.py migration \"adjuster_id TEXT\"")
        sys.exit(2)

    parts      = column_spec.strip().split()
    col_name   = parts[0]
    col_type   = parts[1] if len(parts) > 1 else "TEXT"
    col_default = " ".join(parts[2:]) if len(parts) > 2 else "DEFAULT NULL"
    if "DEFAULT" not in col_default.upper():
        col_default = f"DEFAULT NULL"

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename  = f"{timestamp}_add_{col_name}.sql"

    MIGS_DIR.mkdir(parents=True, exist_ok=True)
    migration_path = MIGS_DIR / filename

    migration_sql = f"""-- ============================================================
-- Migration  : add_{col_name}
-- Generated  : {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")} UTC
-- Author     : Insurance Data Engineering Agent
-- Description: Add '{col_name}' column to the claims table
--
-- Apply with:
--     sqlite3 claims.db < db/migrations/{filename}
--
-- Rollback:
--     SQLite does not support DROP COLUMN (< v3.35).
--     To rollback: restore from backup, or recreate the table without this column.
-- ============================================================

PRAGMA foreign_keys = ON;

-- Step 1: Add the new column (safe — ALTER TABLE ADD COLUMN never locks)
ALTER TABLE claims
    ADD COLUMN {col_name} {col_type} {col_default};

-- Step 2: Add an index if this column will be queried frequently
-- Uncomment the line below if needed:
-- CREATE INDEX IF NOT EXISTS idx_claims_{col_name} ON claims({col_name});

-- Step 3: Verify
SELECT COUNT(*) AS total_claims,
       SUM(CASE WHEN {col_name} IS NULL THEN 1 ELSE 0 END) AS null_count
FROM claims;
"""

    migration_path.write_text(migration_sql, encoding="utf-8")

    print(f"Migration script generated:")
    print(f"  File   : {migration_path}")
    print(f"  Column : {col_name} {col_type} {col_default}")
    print()
    print(migration_sql)

    record("Migration generated", "PASS",
           f"Saved to db/migrations/{filename}",
           f"Apply with: sqlite3 claims.db < db/migrations/{filename}")

# ── command: report ───────────────────────────────────────────────────────────

def cmd_report():
    print("=" * 62)
    print("  INSURANCE DATA ENGINEERING AGENT — PIPELINE HEALTH REPORT")
    print(f"  Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 62)
    print()

    cmd_schema()
    cmd_quality()
    cmd_queries()

    # Summary
    passes = sum(1 for _, s, _, _ in findings if s == "PASS")
    fails  = sum(1 for _, s, _, _ in findings if s == "FAIL")
    warns  = sum(1 for _, s, _, _ in findings if s == "WARN")

    print("=" * 62)
    print("  SUMMARY")
    print("=" * 62)
    print(f"  Total checks : {len(findings)}")
    print(f"  ✅ PASS      : {passes}")
    print(f"  ❌ FAIL      : {fails}")
    print(f"  ⚠️  WARN      : {warns}")
    print()

    if fails == 0 and warns == 0:
        print("  >> Pipeline health: ALL PASS - database is fully compliant.")
    elif fails == 0:
        print(f"  >> Pipeline health: {warns} WARNING(S) - review recommended.")
    else:
        print(f"  >> Pipeline health: {fails} FAILURE(S) found - action required.")

    print("=" * 62)

    if fails > 0:
        print()
        print("  HIGH PRIORITY actions:")
        for rule, status, detail, action in findings:
            if status == "FAIL":
                print(f"  • [{rule}] {action}")
    print()

# ── entry point ───────────────────────────────────────────────────────────────

COMMANDS = {
    "schema":    (cmd_schema,    "Analyse schema.sql and claims_repo.py"),
    "quality":   (cmd_quality,   "Check live claims.db for data quality violations"),
    "queries":   (cmd_queries,   "Run EXPLAIN QUERY PLAN on every SQL query"),
    "migration": (cmd_migration, "Generate a safe ALTER TABLE migration script"),
    "report":    (cmd_report,    "Full pipeline health report (schema+quality+queries)"),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Insurance Data Engineering Agent")
        print()
        print("Usage: py analyze.py <command> [args]")
        print()
        for cmd, (_, desc) in COMMANDS.items():
            print(f"  {cmd:<12} {desc}")
        print()
        print("Examples:")
        print('  py analyze.py report')
        print('  py analyze.py quality')
        print('  py analyze.py migration "adjuster_id TEXT"')
        sys.exit(2)

    cmd = sys.argv[1]
    if cmd == "migration":
        column_spec = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        cmd_migration(column_spec)
    elif cmd == "report":
        cmd_report()
    else:
        COMMANDS[cmd][0]()

    has_fail = any(s == "FAIL" for _, s, _, _ in findings)
    sys.exit(1 if has_fail else 0)

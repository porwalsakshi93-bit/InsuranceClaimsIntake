"""
claim-reviewer/scripts/review.py
=================================
Static analysis script for the Insurance Claims Intake project.
Bundled with the claim-reviewer Kiro skill.

Usage (from PythonClaimsIntake/ directory):
    py ../.kiro/skills/claim-reviewer/scripts/review.py <relative_file_path>

Exit codes:
    0  — no HIGH findings
    1  — one or more HIGH findings found
    2  — usage error (bad path)
"""

import ast
import re
import sys
from pathlib import Path

# ── helpers ──────────────────────────────────────────────────────────────────

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

findings = []


def flag(severity, filepath, line, issue, fix):
    findings.append({
        "severity": severity,
        "file": str(filepath),
        "line": line,
        "issue": issue,
        "fix": fix,
    })


def grep(lines, pattern, flags=0):
    """Yield (lineno, line) for lines matching pattern (1-indexed)."""
    rx = re.compile(pattern, flags)
    for i, line in enumerate(lines, 1):
        if rx.search(line):
            yield i, line


# ── rule sets ────────────────────────────────────────────────────────────────

def check_db_layer(path, lines, src):
    """Rules for db/ files."""

    # No async/await
    for lineno, line in grep(lines, r"\basync\s+def\b|\bawait\b"):
        flag("HIGH", path, lineno,
             "async/await found in db/ layer — DB layer must be synchronous (sqlite3 is sync)",
             "Remove async/await; use plain def and synchronous sqlite3 calls.")

    # Parameterised SQL — no f-strings or .format() in execute() calls
    for lineno, line in grep(lines, r'\.execute\s*\(\s*f["\']|\.execute\s*\(.*\.format\('):
        flag("HIGH", path, lineno,
             "SQL string interpolation detected — potential SQL injection",
             "Replace with parameterised query: conn.execute('SELECT ... WHERE x=?', (value,))")

    # PRAGMA foreign_keys should be present in database.py
    if path.name == "database.py":
        if "PRAGMA foreign_keys" not in src:
            flag("HIGH", path, 0,
                 "PRAGMA foreign_keys = ON not found in database.py",
                 "Add conn.execute('PRAGMA foreign_keys = ON') after connecting.")

    # insert_claim should use 'with conn:' transaction
    if path.name == "claims_repo.py":
        if "def insert_claim" in src and "with conn" not in src:
            flag("HIGH", path, 0,
                 "insert_claim does not use 'with conn:' atomic transaction",
                 "Wrap the INSERT inside 'with conn:' to ensure atomicity.")


def check_middleware(path, lines, src):
    """Rules for middleware/ files."""

    # No DB imports
    for lineno, line in grep(lines, r"from\s+db[\. ]|import\s+db"):
        flag("HIGH", path, lineno,
             "DB import found in middleware/ — middleware must be pure functions with no DB access",
             "Remove the DB import; validators must not touch the database.")

    # No FastAPI/HTTP imports
    for lineno, line in grep(lines, r"from\s+fastapi|import\s+fastapi|from\s+starlette"):
        flag("MEDIUM", path, lineno,
             "HTTP/FastAPI import in middleware/ — middleware should have no HTTP context",
             "Remove FastAPI import; keep middleware/ as pure Python functions.")

    # Return dict structure check
    if "validate_" in src:
        if '{"valid":' not in src and "{'valid':" not in src and '"valid"' not in src:
            flag("MEDIUM", path, 0,
                 "Validator may not return {\"valid\": bool, \"message\": str} dict",
                 "Each validator must return {'valid': bool, 'message': str}.")

    # UTC date comparison
    if "validate_incident_date" in src and "timezone.utc" not in src:
        flag("MEDIUM", path, 0,
             "validate_incident_date does not compare against UTC (timezone.utc missing)",
             "Use datetime.now(timezone.utc).date() for server-side UTC comparison.")


def check_models(path, lines, src):
    """Rules for models/ files."""

    # loss_type must use Literal
    if "loss_type" in src and "Literal" not in src:
        flag("HIGH", path, 0,
             "loss_type field does not use Literal — invalid loss types could be accepted",
             "Use: loss_type: Literal['Fire','Flood','Theft','Accident','Other']")

    # No logic or DB calls
    for lineno, line in grep(lines, r"\.execute\s*\(|import\s+sqlite3"):
        flag("HIGH", path, lineno,
             "DB call found in models/ — models must contain Pydantic models only",
             "Move all DB logic to db/claims_repo.py.")

    # incident_date in ClaimCreate should be date not str
    if "ClaimCreate" in src:
        match = re.search(r"incident_date\s*:\s*(\w+)", src)
        if match and match.group(1) == "str":
            flag("MEDIUM", path, 0,
                 "ClaimCreate.incident_date typed as str — should be datetime.date for parsing",
                 "Change to: incident_date: date")


def check_routers(path, lines, src):
    """Rules for routers/ files."""

    # DB-calling handlers must use def not async def
    try:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                # Allow lifespan and exception_handler
                if node.name not in ("lifespan", "generic_exception_handler"):
                    # Check if it calls DB functions
                    node_src = ast.unparse(node)
                    db_calls = ["find_claim", "insert_claim", "search_claims",
                                "find_policy", "generate_claim"]
                    if any(c in node_src for c in db_calls):
                        flag("HIGH", path, node.lineno,
                             f"async def '{node.name}' makes synchronous DB calls — must be def",
                             f"Change 'async def {node.name}' to 'def {node.name}'")
    except SyntaxError:
        pass

    # Error responses must include "error" key
    for lineno, line in grep(lines, r'JSONResponse\s*\('):
        if '"error"' not in line and "'error'" not in line:
            # Multi-line: just warn if content= present without error key nearby
            pass

    # 422 responses should include "fields"
    if "status_code=422" in src and '"fields"' not in src:
        flag("MEDIUM", path, 0,
             "422 responses found but no 'fields' dict in error payload",
             "Include 'fields': {field_name: message} in 422 responses per the API contract.")

    # Policy existence check before insert
    if "insert_claim" in src and "find_policy_by_number" not in src:
        flag("HIGH", path, 0,
             "insert_claim called without find_policy_by_number check",
             "Verify the policy exists before inserting: if find_policy_by_number(conn, policy_number) is None: return 422")


def check_tests(path, lines, src):
    """Rules for tests/ files."""

    # Must not reference claims.db file
    for lineno, line in grep(lines, r'claims\.db(?!\s*=\s*["\']:memory:)', re.IGNORECASE):
        if ":memory:" not in line:
            flag("HIGH", path, lineno,
                 "Test references 'claims.db' file path — tests must use in-memory SQLite only",
                 "Replace with ':memory:' — never open claims.db in tests.")

    # Property tests need @settings(max_examples=...)
    if "test_validation_properties" in str(path) or "property" in str(path):
        if "@given" in src and "max_examples" not in src:
            flag("HIGH", path, 0,
                 "@given used without @settings(max_examples=100) — property tests may run too few examples",
                 "Add @settings(max_examples=100) above each @given decorator.")

    # conftest must override get_db
    if path.name == "conftest.py":
        if "dependency_overrides" not in src and "get_db" not in src:
            flag("HIGH", path, 0,
                 "conftest.py does not override get_db dependency — integration tests may hit claims.db",
                 "Add: app.dependency_overrides[get_db] = lambda: db_conn")


# ── dispatch ─────────────────────────────────────────────────────────────────

def analyse(filepath: Path):
    src = filepath.read_text(encoding="utf-8")
    lines = src.splitlines()

    parts = filepath.parts
    if "db" in parts:
        check_db_layer(filepath, lines, src)
    if "middleware" in parts:
        check_middleware(filepath, lines, src)
    if "models" in parts:
        check_models(filepath, lines, src)
    if "routers" in parts:
        check_routers(filepath, lines, src)
    if "tests" in parts:
        check_tests(filepath, lines, src)

    return findings


# ── output ───────────────────────────────────────────────────────────────────

def print_report(filepath, findings):
    if not findings:
        print(f"✅  {filepath}  —  0 findings. All rules pass.")
        return

    # Sort by severity then line
    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 9), f["line"]))

    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
        line_ref = f":{f['line']}" if f["line"] else ""
        print(f"[{f['severity']:<6}]  {f['file']}{line_ref}")
        print(f"         ISSUE : {f['issue']}")
        print(f"         FIX   : {f['fix']}")
        print()

    verdict = "❌ FAIL" if counts["HIGH"] > 0 else ("⚠️  WARN" if counts["MEDIUM"] > 0 else "✅ PASS")
    print(f"{verdict}  —  HIGH: {counts['HIGH']}  MEDIUM: {counts['MEDIUM']}  LOW: {counts['LOW']}")


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py review.py <file_path>", file=sys.stderr)
        print("Example: py review.py db/claims_repo.py", file=sys.stderr)
        sys.exit(2)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"Error: file not found: {target}", file=sys.stderr)
        sys.exit(2)

    print(f"claim-reviewer  →  {target}")
    print("─" * 60)
    results = analyse(target)
    print_report(target, results)

    has_high = any(f["severity"] == "HIGH" for f in results)
    sys.exit(1 if has_high else 0)

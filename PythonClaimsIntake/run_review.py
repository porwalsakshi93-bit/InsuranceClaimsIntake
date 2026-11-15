"""
run_review.py
Runs the claim-reviewer skill against every source file in the project.
Demonstrates the custom skill working end-to-end.

Usage:
    py run_review.py
"""
import subprocess
import sys
from pathlib import Path

BASE     = Path(__file__).parent
SCRIPT   = BASE.parent / ".kiro" / "skills" / "claim-reviewer" / "scripts" / "review.py"
PYTHON   = sys.executable

FILES = [
    "models/claim.py",
    "db/claims_repo.py",
    "db/database.py",
    "db/seed.py",
    "middleware/validate.py",
    "routers/claims.py",
    "routers/policies.py",
    "tests/conftest.py",
    "tests/unit/test_claims_repo.py",
    "tests/unit/test_validate.py",
    "tests/property/test_validation_properties.py",
    "tests/integration/test_claims_api.py",
    "tests/integration/test_policies_api.py",
]

print("=" * 65)
print("  claim-reviewer skill  —  full project scan")
print("=" * 65)
print()

total_files  = 0
total_high   = 0
total_medium = 0
all_clean    = []

for rel in FILES:
    filepath = BASE / rel
    if not filepath.exists():
        print(f"SKIP (not found): {rel}")
        continue

    result = subprocess.run(
        [PYTHON, str(SCRIPT), str(filepath)],
        capture_output=True, text=True
    )
    output = result.stdout.strip()
    print(output)
    print()

    total_files += 1
    if "[HIGH]" in output:
        total_high += 1
    if "[MEDIUM]" in output:
        total_medium += 1
    if "0 findings" in output:
        all_clean.append(rel)

print("=" * 65)
print(f"  SCAN COMPLETE  —  {total_files} files reviewed")
print(f"  Files with HIGH findings   : {total_high}")
print(f"  Files with MEDIUM findings : {total_medium}")
print(f"  Fully clean files          : {len(all_clean)}")
if total_high == 0 and total_medium == 0:
    print()
    print("  ✅  All files pass every rule. Project is compliant.")
else:
    print()
    print("  ❌  Issues found — see findings above.")
print("=" * 65)
sys.exit(1 if total_high > 0 else 0)

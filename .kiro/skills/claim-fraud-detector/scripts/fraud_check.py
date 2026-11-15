# -*- coding: utf-8 -*-
import sqlite3, sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent.parent.parent / "PythonClaimsIntake" / "claims.db"
DUPLICATE_PHONE_THRESHOLD = 3
HIGH_LOSS_THRESHOLD = 50000
REPEAT_POLICY_DAYS = 30
SHORT_DESC_CHARS = 20
BURST_THRESHOLD = 5

def connect():
    if not DB_PATH.exists():
        print(f"[ERROR] Database not found at {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def fetch_claims(conn, claim_id=None):
    if claim_id:
        return conn.execute("SELECT * FROM claims WHERE claim_id = ?", (claim_id,)).fetchall()
    return conn.execute("SELECT * FROM claims").fetchall()

def check_duplicate_phone(claims):
    findings, phone_map = [], defaultdict(list)
    for c in claims:
        phone_map[c["phone"]].append(c["claim_id"])
    for phone, ids in phone_map.items():
        if len(ids) >= DUPLICATE_PHONE_THRESHOLD:
            for cid in ids:
                findings.append({"check":"Duplicate phone","claim_id":cid,"risk":"HIGH",
                    "detail":f"Phone {phone} appears on {len(ids)} claims",
                    "action":"Flag for manual review before adjudication"})
    return findings

def check_high_loss(claims):
    findings = []
    for c in claims:
        amt = c["estimated_loss_amount"]
        if amt and float(amt) > HIGH_LOSS_THRESHOLD:
            findings.append({"check":"High loss amount","claim_id":c["claim_id"],"risk":"MEDIUM",
                "detail":f"Estimated loss ${float(amt):,.2f} exceeds ${HIGH_LOSS_THRESHOLD:,}",
                "action":"Require additional supporting documentation"})
    return findings

def check_repeat_policy(claims):
    findings, policy_dates = [], defaultdict(list)
    for c in claims:
        policy_dates[c["policy_number"]].append((c["incident_date"], c["claim_id"]))
    for policy, entries in policy_dates.items():
        entries.sort(key=lambda x: x[0])
        for i in range(len(entries)):
            for j in range(i+1, len(entries)):
                try:
                    d1 = datetime.strptime(entries[i][0], "%Y-%m-%d")
                    d2 = datetime.strptime(entries[j][0], "%Y-%m-%d")
                    if abs((d2-d1).days) <= REPEAT_POLICY_DAYS:
                        for cid in [entries[i][1], entries[j][1]]:
                            already = any(f["claim_id"]==cid and f["check"]=="Repeated policy in window" for f in findings)
                            if not already:
                                findings.append({"check":"Repeated policy in window","claim_id":cid,"risk":"MEDIUM",
                                    "detail":f"Policy {policy} used 2+ times within {REPEAT_POLICY_DAYS} days",
                                    "action":"Verify policy terms allow multiple claims"})
                except ValueError:
                    pass
    return findings

def check_short_description(claims):
    findings = []
    for c in claims:
        desc = c["incident_description"] or ""
        if len(desc.strip()) < SHORT_DESC_CHARS:
            findings.append({"check":"Short incident description","claim_id":c["claim_id"],"risk":"LOW",
                "detail":f"Description only {len(desc.strip())} chars (min {SHORT_DESC_CHARS})",
                "action":"Request fuller incident description from claimant"})
    return findings

def check_claim_burst(claims):
    findings, date_map = [], defaultdict(list)
    for c in claims:
        day = (c["created_at"] or "")[:10]
        date_map[day].append(c["claim_id"])
    for day, ids in date_map.items():
        if len(ids) >= BURST_THRESHOLD:
            for cid in ids:
                findings.append({"check":"Claim burst","claim_id":cid,"risk":"HIGH",
                    "detail":f"{len(ids)} claims submitted on {day}",
                    "action":"Investigate for coordinated fraud attempt"})
    return findings

def run_all_checks(claims):
    findings = []
    for fn in [check_duplicate_phone, check_high_loss, check_repeat_policy, check_short_description, check_claim_burst]:
        findings += fn(claims)
    return findings

def print_finding(f):
    print("[FRAUD-CHECK]  " + str(f["check"]))
    print("[CLAIM]        " + str(f["claim_id"]))
    print("[RISK]         " + str(f["risk"]))
    print("[DETAIL]       " + str(f["detail"]))
    print("[ACTION]       " + str(f["action"]))
    print()

def print_summary(findings):
    h = sum(1 for f in findings if f["risk"]=="HIGH")
    m = sum(1 for f in findings if f["risk"]=="MEDIUM")
    l = sum(1 for f in findings if f["risk"]=="LOW")
    if findings:
        print(f"Fraud scan complete: {h} HIGH, {m} MEDIUM, {l} LOW risk claims found.")
    else:
        print("Fraud scan complete: no risk indicators found.")

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: fraud_check.py run | check <claim_id> | report"); sys.exit(1)
    cmd, conn = args[0].lower(), connect()
    claims = fetch_claims(conn)
    if cmd == "run":
        findings = run_all_checks(claims) if claims else []
        [print_finding(f) for f in findings] if findings else print("No fraud indicators found.")
        print_summary(findings)
    elif cmd == "check":
        if len(args) < 2: print("Usage: fraud_check.py check <claim_id>"); sys.exit(1)
        if not fetch_claims(conn, args[1]): print(f"Claim {args[1]} not found."); sys.exit(1)
        cf = [f for f in run_all_checks(claims) if f["claim_id"]==args[1]]
        [print_finding(f) for f in cf] if cf else print(f"No fraud indicators for {args[1]}.")
        print_summary(cf)
    elif cmd == "report":
        findings = run_all_checks(claims) if claims else []
        sep = "=" * 60
        print(sep); print("FRAUD RISK REPORT -- Insurance Claims Intake"); print(sep)
        print(f"Total claims scanned : {len(claims)}")
        print(f"Findings             : {len(findings)}"); print()
        for f in sorted(findings, key=lambda x: ["HIGH","MEDIUM","LOW"].index(x["risk"])): print_finding(f)
        print(sep); print_summary(findings)
    else:
        print(f"Unknown command: {cmd}"); sys.exit(1)

if __name__ == "__main__":
    main()

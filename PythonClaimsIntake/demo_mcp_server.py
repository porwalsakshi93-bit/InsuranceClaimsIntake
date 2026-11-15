"""
test_mcp_server.py — Smoke test for the Insurance Claims MCP server.

Demonstrates every registered tool running against the live claims.db.

Run with:
    py test_mcp_server.py
"""
import sys
sys.path.insert(0, ".")

import mcp_server as srv

print("=" * 60)
print("Insurance Claims MCP Server — Smoke Test")
print("=" * 60)

# ── 1. Show registered tools ──────────────────────────────────────────────
tools = srv.mcp._tool_manager.list_tools()
print(f"\n[1] Registered tools ({len(tools)} total)")
for t in tools:
    desc = (t.description or "")[:65]
    print(f"    • {t.name:<22} {desc}")

# ── 2. list_policies ─────────────────────────────────────────────────────
policies = srv.list_policies()
print(f"\n[2] list_policies  →  {len(policies)} records")
for p in policies:
    print(f"    {p['policy_number']}  {p['holder_name']:<18}  {p['policy_type']}")

# ── 3. claims_summary ────────────────────────────────────────────────────
summary = srv.claims_summary()
print(f"\n[3] claims_summary  →")
print(f"    total_claims         : {summary['total_claims']}")
print(f"    by_loss_type         : {summary['by_loss_type']}")
print(f"    by_status            : {summary['by_status']}")
print(f"    total_estimated_loss : ${summary['total_estimated_loss']:,.2f}")

# ── 4. list_claims ───────────────────────────────────────────────────────
claims = srv.list_claims(limit=5)
print(f"\n[4] list_claims(limit=5)  →  {len(claims)} rows returned")
for c in claims:
    print(f"    {c['claim_id']}  {c['last_name']:<12}  {c['loss_type']:<10}  {c['status']}")

# ── 5. get_claim ─────────────────────────────────────────────────────────
if claims:
    cid = claims[0]["claim_id"]
    detail = srv.get_claim(cid)
    print(f"\n[5] get_claim('{cid}')  →")
    if "error" not in detail:
        print(f"    Name     : {detail['first_name']} {detail['last_name']}")
        print(f"    Policy   : {detail['policy_number']}")
        print(f"    Loss     : {detail['loss_type']}")
        print(f"    Desc     : {str(detail['incident_description'])[:60]}...")
        amt = detail.get("estimated_loss_amount") or 0
        print(f"    Amount   : ${amt:,.2f}")
        print(f"    Status   : {detail['status']}")
    else:
        print(f"    {detail}")

# ── 6. get_claim — not found ──────────────────────────────────────────────
missing = srv.get_claim("CLM-00000000-9999")
print(f"\n[6] get_claim('CLM-00000000-9999')  →  {missing}")

# ── 7. query_claims_db — custom SELECT ───────────────────────────────────
rows = srv.query_claims_db(
    "SELECT loss_type, COUNT(*) AS claims, "
    "ROUND(SUM(estimated_loss_amount),2) AS total_loss "
    "FROM claims GROUP BY loss_type ORDER BY total_loss DESC"
)
print(f"\n[7] query_claims_db (loss breakdown with totals)  →")
for r in rows:
    print(f"    {r['loss_type']:<10}  claims={r['claims']}  total=${r['total_loss'] or 0:,.2f}")

# ── 8. query_claims_db — blocked write ───────────────────────────────────
blocked = srv.query_claims_db("DELETE FROM claims WHERE 1=1")
print(f"\n[8] query_claims_db (DELETE blocked)  →  {blocked}")

print("\n" + "=" * 60)
print("All MCP tool demos completed successfully.")
print("=" * 60)
print("\nTo use in Kiro:")
print("  1. .kiro/mcp.json is already configured")
print("  2. Reload Kiro / open MCP panel to see 'insurance-claims-db'")
print("  3. Ask Kiro: 'How many claims are in the database?' or")
print("               'List all Flood claims using the MCP tool'")

"""
mcp_web.py — MCP Web Explorer for Insurance Claims
===================================================
A browser-friendly web UI that exposes all 5 MCP tool functions as
REST endpoints with an HTML dashboard at http://localhost:8002

This is NOT a replacement for the MCP server — it's a visual demo
layer that calls the same tool functions from mcp_server.py directly.

Start:
    py mcp_web.py

Then open:  http://localhost:8002
"""

import sys
sys.path.insert(0, ".")          # so mcp_server is importable

import json
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
import mcp_server as mcp_tools   # re-use the 5 tool functions directly

app = FastAPI(
    title="Insurance Claims — MCP Tool Explorer",
    description="Browser UI for the insurance-claims-db MCP server tools.",
    version="1.0.0",
)

# ── REST wrappers around the 5 MCP tools ─────────────────────────────────────

@app.get("/api/summary", summary="claims_summary tool")
def api_summary():
    """Aggregate stats: total claims, breakdown by loss type and status, total loss amount."""
    return mcp_tools.claims_summary()


@app.get("/api/claims", summary="list_claims tool")
def api_list_claims(limit: int = Query(default=20, ge=1, le=50,
                                       description="Number of records (1-50)")):
    """Most recent N claims from the database."""
    return mcp_tools.list_claims(limit=limit)


@app.get("/api/claims/{claim_id}", summary="get_claim tool")
def api_get_claim(claim_id: str):
    """Full detail for a single claim ID (e.g. CLM-20261106-0001)."""
    return mcp_tools.get_claim(claim_id)


@app.get("/api/policies", summary="list_policies tool")
def api_list_policies():
    """All seeded policies (policy_number, holder_name, policy_type)."""
    return mcp_tools.list_policies()


@app.get("/api/query", summary="query_claims_db tool")
def api_query(sql: str = Query(description="SELECT statement to run",
                                example="SELECT loss_type, COUNT(*) AS n FROM claims GROUP BY loss_type")):
    """Run a read-only SELECT query. Only SELECT permitted."""
    return mcp_tools.query_claims_db(sql)


# ── HTML dashboard ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Insurance Claims — MCP Tool Explorer</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f4f8;color:#222}
  header{background:#1e3a5f;color:#fff;padding:1rem 2rem}
  header h1{font-size:1.4rem}
  header p{font-size:.85rem;color:#bfdbfe;margin-top:.3rem}
  main{max-width:960px;margin:2rem auto;padding:0 1rem}
  h2{font-size:1rem;font-weight:600;margin-bottom:.6rem;color:#1e3a5f}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem}
  .card{background:#fff;border-radius:8px;padding:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,.1)}
  .card-full{grid-column:1/-1}
  .stat{font-size:2rem;font-weight:700;color:#2563eb}
  .label{font-size:.8rem;color:#666;margin-top:.2rem}
  table{width:100%;border-collapse:collapse;font-size:.85rem}
  th{background:#f9fafb;text-align:left;padding:.5rem .7rem;font-weight:600;font-size:.75rem;text-transform:uppercase;border-bottom:2px solid #e5e7eb}
  td{padding:.5rem .7rem;border-bottom:1px solid #f3f4f6}
  tr:hover td{background:#f9fafb}
  .badge{display:inline-block;padding:.15rem .5rem;border-radius:9999px;font-size:.75rem;font-weight:600;background:#dbeafe;color:#1d4ed8}
  textarea,input{width:100%;padding:.5rem;border:1px solid #d1d5db;border-radius:4px;font-size:.9rem;font-family:monospace}
  button{padding:.4rem 1rem;background:#2563eb;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:.9rem;margin-top:.5rem}
  button:hover{background:#1d4ed8}
  pre{background:#1e1e2e;color:#cdd6f4;padding:1rem;border-radius:6px;overflow:auto;font-size:.8rem;max-height:300px;white-space:pre-wrap}
  .pill{display:inline-block;padding:.1rem .5rem;border-radius:4px;font-size:.75rem;margin:.1rem}
  .pill-fire{background:#fee2e2;color:#b91c1c}
  .pill-flood{background:#dbeafe;color:#1d4ed8}
  .pill-theft{background:#fef3c7;color:#92400e}
  .pill-accident{background:#f3e8ff;color:#6b21a8}
  .pill-other{background:#f1f5f9;color:#475569}
  .tool-name{font-size:.75rem;background:#e0f2fe;color:#0369a1;padding:.1rem .4rem;border-radius:3px;font-family:monospace}
</style>
</head>
<body>
<header>
  <h1>🔌 Insurance Claims — MCP Tool Explorer</h1>
  <p>Live view of the <code>insurance-claims-db</code> MCP server &nbsp;|&nbsp; 5 tools running on Python (no uvx / Node)</p>
</header>
<main>

  <!-- Summary cards -->
  <div class="grid" id="summary-grid">
    <div class="card"><div class="stat" id="s-total">…</div><div class="label">Total Claims</div><div class="tool-name" style="margin-top:.5rem">claims_summary</div></div>
    <div class="card"><div class="stat" id="s-loss">…</div><div class="label">Total Estimated Loss ($)</div><div class="tool-name" style="margin-top:.5rem">claims_summary</div></div>
    <div class="card"><div id="s-by-type"></div><div class="label" style="margin-top:.4rem">By Loss Type</div></div>
    <div class="card"><div id="s-by-status"></div><div class="label" style="margin-top:.4rem">By Status</div></div>
  </div>

  <!-- Claims table -->
  <div class="card card-full" style="margin-bottom:1.5rem">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem">
      <h2>Recent Claims &nbsp;<span class="tool-name">list_claims</span></h2>
      <select id="limit-sel" style="width:auto;padding:.3rem" onchange="loadClaims()">
        <option value="5">5</option><option value="10" selected>10</option>
        <option value="20">20</option><option value="50">50</option>
      </select>
    </div>
    <table id="claims-table">
      <thead><tr><th>Claim ID</th><th>Name</th><th>Policy</th><th>Loss Type</th><th>Date</th><th>Status</th></tr></thead>
      <tbody id="claims-body"><tr><td colspan="6">Loading…</td></tr></tbody>
    </table>
  </div>

  <!-- Policies table -->
  <div class="card card-full" style="margin-bottom:1.5rem">
    <h2 style="margin-bottom:.8rem">Policies &nbsp;<span class="tool-name">list_policies</span></h2>
    <table id="policies-table">
      <thead><tr><th>Policy Number</th><th>Holder Name</th><th>Type</th></tr></thead>
      <tbody id="policies-body"><tr><td colspan="3">Loading…</td></tr></tbody>
    </table>
  </div>

  <!-- SQL query box -->
  <div class="card card-full">
    <h2 style="margin-bottom:.8rem">Ad-hoc SQL Query &nbsp;<span class="tool-name">query_claims_db</span></h2>
    <textarea id="sql-input" rows="3">SELECT loss_type, COUNT(*) AS claims, ROUND(SUM(estimated_loss_amount),2) AS total_loss FROM claims GROUP BY loss_type ORDER BY total_loss DESC</textarea>
    <button onclick="runQuery()">Run Query</button>
    <pre id="sql-result" style="margin-top:.8rem">Results appear here…</pre>
  </div>

</main>
<script>
const pill = t => {
  const cls = {Fire:'pill-fire',Flood:'pill-flood',Theft:'pill-theft',Accident:'pill-accident',Other:'pill-other'}[t] || 'pill-other'
  return `<span class="pill ${cls}">${t}</span>`
}

async function loadSummary() {
  const d = await fetch('/api/summary').then(r=>r.json())
  document.getElementById('s-total').textContent = d.total_claims
  document.getElementById('s-loss').textContent = '$' + d.total_estimated_loss.toLocaleString()
  document.getElementById('s-by-type').innerHTML = Object.entries(d.by_loss_type)
    .map(([t,n])=>`${pill(t)} <b>${n}</b>`).join('  ')
  document.getElementById('s-by-status').innerHTML = Object.entries(d.by_status)
    .map(([s,n])=>`<span class="badge">${s}</span> <b>${n}</b>`).join('  ')
}

async function loadClaims() {
  const limit = document.getElementById('limit-sel').value
  const rows  = await fetch(`/api/claims?limit=${limit}`).then(r=>r.json())
  const tbody = document.getElementById('claims-body')
  if (!rows.length) { tbody.innerHTML='<tr><td colspan="6">No claims yet.</td></tr>'; return }
  tbody.innerHTML = rows.map(c=>`
    <tr>
      <td><a href="/api/claims/${c.claim_id}" target="_blank" style="font-family:monospace">${c.claim_id}</a></td>
      <td>${c.first_name} ${c.last_name}</td>
      <td>${c.policy_number}</td>
      <td>${pill(c.loss_type)}</td>
      <td>${c.incident_date}</td>
      <td><span class="badge">${c.status}</span></td>
    </tr>`).join('')
}

async function loadPolicies() {
  const rows = await fetch('/api/policies').then(r=>r.json())
  document.getElementById('policies-body').innerHTML = rows.map(p=>`
    <tr><td style="font-family:monospace">${p.policy_number}</td>
        <td>${p.holder_name}</td>
        <td>${p.policy_type}</td></tr>`).join('')
}

async function runQuery() {
  const sql = document.getElementById('sql-input').value.trim()
  if (!sql) return
  const result = await fetch('/api/query?sql='+encodeURIComponent(sql)).then(r=>r.json())
  document.getElementById('sql-result').textContent = JSON.stringify(result, null, 2)
}

loadSummary(); loadClaims(); loadPolicies();
</script>
</body>
</html>
""")


if __name__ == "__main__":
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8002)
    args = parser.parse_args()
    print("Insurance Claims — MCP Web Explorer")
    print(f"  Dashboard : http://localhost:{args.port}")
    print(f"  API docs  : http://localhost:{args.port}/docs")
    print()
    uvicorn.run(app, host="127.0.0.1", port=args.port)

"""
mcp_server.py — Insurance Claims MCP Server
============================================
Exposes the claims SQLite database to Kiro via the Model Context Protocol
(MCP). Kiro can then call these tools directly in chat to answer questions
like "how many claims were filed today?" or "list all Flood claims".

No uvx or Node required — pure Python, uses the mcp SDK (>=2.0).

Start the server:
    py mcp_server.py

Register with Kiro by adding .kiro/mcp.json (already created).

Tools
-----
  query_claims_db   Run any SELECT against claims.db
  list_claims       Most recent N claims (max 50)
  get_claim         Full detail for one claim ID
  list_policies     All seeded policies
  claims_summary    Aggregate stats: totals, by loss type, by status
"""

import os
import sqlite3
from pathlib import Path

from mcp.server.mcpserver import MCPServer

# ── locate claims.db relative to this file ──────────────────────────────────
DB_PATH = Path(__file__).parent / os.getenv("DATABASE_PATH", "claims.db")

mcp = MCPServer(
    name="insurance-claims-db",
    instructions=(
        "Tools for querying the Insurance Claims Intake SQLite database. "
        "Use query_claims_db for ad-hoc SQL, and the helper tools for "
        "common lookups. Only SELECT queries are permitted."
    ),
)


# ── helper ───────────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


# ── tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def query_claims_db(sql: str) -> list[dict]:
    """
    Run a read-only SELECT query against the claims database.

    Only SELECT statements are permitted — any other statement returns an error.
    Column names and values are returned as a list of dicts.

    Example:
        SELECT loss_type, COUNT(*) AS n FROM claims GROUP BY loss_type
    """
    sql_stripped = sql.strip()
    if not sql_stripped.upper().startswith("SELECT"):
        return [{"error": "Only SELECT queries are permitted."}]
    conn = _conn()
    try:
        rows = conn.execute(sql_stripped).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        return [{"error": str(exc)}]
    finally:
        conn.close()


@mcp.tool()
def list_claims(limit: int = 20) -> list[dict]:
    """
    Return the most recent claims from the database (newest first).

    Each row contains: claim_id, first_name, last_name, policy_number,
    loss_type, incident_date, status.

    limit: number of rows to return (1–50, default 20).
    """
    limit = min(max(1, limit), 50)
    conn = _conn()
    try:
        rows = conn.execute(
            """
            SELECT claim_id, first_name, last_name, policy_number,
                   loss_type, incident_date, status
            FROM   claims
            ORDER  BY created_at DESC
            LIMIT  ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@mcp.tool()
def get_claim(claim_id: str) -> dict:
    """
    Fetch every field of a single claim by its Claim ID.

    Returns all 13 fields, or {"error": "Claim not found"} if unknown.
    Claim ID format: CLM-YYYYMMDD-NNNN  (e.g. CLM-20261106-0001)
    """
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT * FROM claims WHERE claim_id = ?", (claim_id,)
        ).fetchone()
        if row is None:
            return {"error": f"Claim '{claim_id}' not found."}
        return dict(row)
    finally:
        conn.close()


@mcp.tool()
def list_policies() -> list[dict]:
    """
    List all policies in the database (policy_number, holder_name, policy_type).

    The seven pre-seeded policies are:
    POL-001 Alice Johnson (Home) … POL-007 Grace Patel (Home)
    """
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT policy_number, holder_name, policy_type "
            "FROM policies ORDER BY policy_number"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@mcp.tool()
def claims_summary() -> dict:
    """
    Return aggregate statistics for all claims in the database:

      total_claims          — total number of claims
      by_loss_type          — count per loss type {Fire: N, Flood: N, …}
      by_status             — count per status    {Draft: N, …}
      total_estimated_loss  — sum of estimated_loss_amount (0 if none provided)
    """
    conn = _conn()
    try:
        total = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]

        by_type = {
            r["loss_type"]: r["n"]
            for r in conn.execute(
                "SELECT loss_type, COUNT(*) AS n FROM claims GROUP BY loss_type"
            ).fetchall()
        }

        by_status = {
            r["status"]: r["n"]
            for r in conn.execute(
                "SELECT status, COUNT(*) AS n FROM claims GROUP BY status"
            ).fetchall()
        }

        total_loss = conn.execute(
            "SELECT COALESCE(SUM(estimated_loss_amount), 0) FROM claims"
        ).fetchone()[0]

        return {
            "total_claims": total,
            "by_loss_type": by_type,
            "by_status": by_status,
            "total_estimated_loss": round(total_loss, 2),
        }
    finally:
        conn.close()


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Insurance Claims MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="Transport mode. Use 'streamable-http' or 'sse' to expose on the web (default: stdio for Kiro).",
    )
    parser.add_argument("--port", type=int, default=8001,
                        help="Port for HTTP transports (default: 8001).")
    args = parser.parse_args()

    print(f"Insurance Claims MCP Server")
    print(f"  Database  : {DB_PATH}")
    print(f"  Transport : {args.transport}")
    print(f"  Tools     : query_claims_db | list_claims | get_claim | list_policies | claims_summary")

    if args.transport == "stdio":
        print(f"  Mode      : Kiro integration (stdio)")
        mcp.run(transport="stdio")
    elif args.transport == "streamable-http":
        print(f"  URL       : http://localhost:{args.port}/mcp")
        print(f"  Explorer  : http://localhost:{args.port}/docs  (via FastAPI)")
        mcp.run(transport="streamable-http", port=args.port)
    elif args.transport == "sse":
        print(f"  URL       : http://localhost:{args.port}/sse")
        mcp.run(transport="sse", port=args.port)

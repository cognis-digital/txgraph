"""TXGRAPH MCP server — exposes scan() as an MCP tool for Cognis.Studio."""
from __future__ import annotations
from txgraph.core import scan, to_json

def serve() -> int:
    """Start an MCP stdio server. Requires the optional 'mcp' extra:
        pip install "cognis-txgraph[mcp]"
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception:
        print("Install the MCP extra: pip install 'cognis-txgraph[mcp]'")
        return 1
    app = FastMCP("txgraph")

    @app.tool()
    def txgraph_scan(target: str) -> str:
        """Builds a transaction graph from ledger/account data and surfaces structuring, layering, and mule-network patterns for AML triage.. Returns JSON findings."""
        return to_json(scan(target))

    app.run()
    return 0

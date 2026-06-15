"""TXGRAPH MCP server — exposes scan() as an MCP tool for Cognis.Studio."""
from __future__ import annotations

import sys
from txgraph.core import scan, to_json


def serve() -> int:
    """Start an MCP stdio server. Requires the optional 'mcp' extra:
        pip install "cognis-txgraph[mcp]"
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print(
            "error: MCP package not installed.\n"
            "Install the MCP extra: pip install 'cognis-txgraph[mcp]'",
            file=sys.stderr,
        )
        return 1

    app = FastMCP("txgraph")

    @app.tool()
    def txgraph_scan(target: str) -> str:
        """Build a transaction graph from a CSV path and return JSON AML findings.

        Surfaces structuring, layering, and mule-network patterns for AML triage.
        Returns JSON findings.
        """
        try:
            return to_json(scan(target))
        except (FileNotFoundError, IsADirectoryError, PermissionError) as exc:
            return to_json({"error": f"cannot read file: {exc}"})
        except ValueError as exc:
            return to_json({"error": f"invalid input: {exc}"})

    app.run()
    return 0

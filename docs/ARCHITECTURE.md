# TXGRAPH — Architecture

> Builds a transaction graph from ledger/account data and surfaces structuring, layering, and mule-network patterns for AML triage.

```
input ──▶ collect ──▶ rules/analyzers ──▶ score ──▶ findings ──▶ table · json
                              │                          │
                         (this repo)                 MCP tool (agents)
```

- **collect** normalizes the target (file/dir/API) into records.
- **rules/analyzers** apply the heuristics shipped in `txgraph/core.py`.
- **score** ranks by severity.
- **MCP server** (`txgraph mcp`) exposes `scan` for Cognis.Studio agents.

Extend by adding a rule + a test + a `demos/NN-*/SCENARIO.md`. See [CONTRIBUTING.md](../CONTRIBUTING.md).

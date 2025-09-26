"""Command-line interface for TXGRAPH.

Examples:
  # Scan a CSV and print a findings table
  txgraph scan demos/01-basic/transactions.csv

  # Emit JSON for a CI gate (exits non-zero when findings exist)
  txgraph scan transactions.csv --format json > findings.json

  # Print the SAR narrative
  txgraph scan transactions.csv --sar

  # Custom structuring threshold
  txgraph scan transactions.csv --threshold 5000
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from txgraph import TOOL_NAME, TOOL_VERSION
from txgraph.core import (
    load_transactions,
    build_graph,
    analyze,
    sar_summary,
    DEFAULT_REPORT_THRESHOLD,
)


def _render_table(findings, graph) -> str:
    if not findings:
        return (f"No suspicious activity in {len(graph.txs)} transactions "
                f"/ {len(graph.accounts)} accounts.")
    rows = [("#", "KIND", "SEV", "AMOUNT", "DETAIL")]
    for i, f in enumerate(findings, 1):
        rows.append((str(i), f.kind, f.severity, f"${f.amount:,.2f}", f.detail))
    widths = [max(len(r[c]) for r in rows) for c in range(len(rows[0]))]
    # cap the detail column so the table stays readable
    widths[-1] = min(widths[-1], 70)
    out = []
    for ri, r in enumerate(rows):
        cells = []
        for c, cell in enumerate(r):
            if c == len(r) - 1 and len(cell) > widths[c]:
                cell = cell[:widths[c] - 1] + "…"
            cells.append(cell.ljust(widths[c]))
        out.append("  ".join(cells).rstrip())
        if ri == 0:
            out.append("  ".join("-" * widths[c] for c in range(len(r))))
    summary = (f"\n{len(findings)} finding(s); "
               f"{sum(1 for f in findings if f.severity == 'high')} high.")
    return "\n".join(out) + "\n" + summary


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Build a transaction graph and surface AML "
                    "structuring / layering / mule patterns from a CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--version", action="version",
                   version=f"{TOOL_NAME} {TOOL_VERSION}")
    sub = p.add_subparsers(dest="command", metavar="COMMAND")

    scan = sub.add_parser(
        "scan",
        help="Scan a transaction CSV for suspicious patterns.",
        description="Scan a transaction CSV for AML patterns. "
                    "Exits non-zero when any finding is detected (CI gate).",
    )
    scan.add_argument("csv", help="Path to the transaction CSV "
                                  "(columns: tx_id,src,dst,amount,timestamp).")
    scan.add_argument("--format", choices=("table", "json"), default="table",
                      help="Output format (default: table).")
    scan.add_argument("--threshold", type=float, default=DEFAULT_REPORT_THRESHOLD,
                      help="Reporting threshold for structuring detection "
                           f"(default: {DEFAULT_REPORT_THRESHOLD:g}).")
    scan.add_argument("--sar", action="store_true",
                      help="Print the SAR narrative instead of the table.")
    scan.add_argument("--fail-on", choices=("any", "high", "none"),
                      default="any",
                      help="Severity that triggers a non-zero exit "
                           "(default: any).")
    return p


def _exit_code(findings, fail_on: str) -> int:
    if fail_on == "none":
        return 0
    if fail_on == "high":
        return 1 if any(f.severity == "high" for f in findings) else 0
    return 1 if findings else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command != "scan":
        parser.print_help()
        return 2

    try:
        txs = load_transactions(args.csv)
    except FileNotFoundError:
        print(f"error: file not found: {args.csv}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    graph = build_graph(txs)
    findings = analyze(graph, threshold=args.threshold)

    if args.format == "json":
        payload = {
            "tool": TOOL_NAME,
            "version": TOOL_VERSION,
            "transactions": len(graph.txs),
            "accounts": len(graph.accounts),
            "finding_count": len(findings),
            "findings": [f.to_dict() for f in findings],
        }
        print(json.dumps(payload, indent=2))
    elif args.sar:
        print(sar_summary(findings, graph))
    else:
        print(_render_table(findings, graph))

    return _exit_code(findings, args.fail_on)

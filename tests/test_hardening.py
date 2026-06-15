"""Hardening tests: error/edge-case paths added to TXGRAPH."""
from __future__ import annotations

import io
import os
import tempfile

import pytest

from txgraph.core import (
    load_transactions,
    build_graph,
    analyze,
    detect_structuring,
    scan,
    to_json,
    TOOL_NAME,
    TOOL_VERSION,
)
from txgraph.cli import main


# ---------------------------------------------------------------------------
# TOOL_NAME / TOOL_VERSION now live in core (not just as a fallback in __init__)
# ---------------------------------------------------------------------------

def test_tool_identity_from_core():
    assert TOOL_NAME == "txgraph"
    # version must look like x.y.z
    parts = TOOL_VERSION.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


# ---------------------------------------------------------------------------
# load_transactions: missing file -> FileNotFoundError (not a traceback)
# ---------------------------------------------------------------------------

def test_load_missing_file_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_transactions("/nonexistent/path/transactions.csv")


# ---------------------------------------------------------------------------
# load_transactions: path is a directory -> IsADirectoryError
# ---------------------------------------------------------------------------

def test_load_directory_raises_is_a_directory():
    with pytest.raises(IsADirectoryError):
        load_transactions(tempfile.gettempdir())


# ---------------------------------------------------------------------------
# load_transactions: malformed CSV (missing required column)
# ---------------------------------------------------------------------------

def test_load_missing_required_column_raises_value_error():
    csv_text = "tx_id,src,amount\n1,A,5\n"
    with pytest.raises(ValueError, match="missing required column"):
        load_transactions(io.StringIO(csv_text))


# ---------------------------------------------------------------------------
# load_transactions: completely empty file (no header)
# ---------------------------------------------------------------------------

def test_load_empty_csv_raises_value_error():
    with pytest.raises(ValueError, match="empty CSV"):
        load_transactions(io.StringIO(""))


# ---------------------------------------------------------------------------
# load_transactions: negative amount -> clear ValueError
# ---------------------------------------------------------------------------

def test_load_negative_amount_raises():
    csv_text = (
        "tx_id,src,dst,amount,timestamp\n"
        "t1,A,B,-100,2026-01-01T00:00:00Z\n"
    )
    with pytest.raises(ValueError, match="negative amount"):
        load_transactions(io.StringIO(csv_text))


# ---------------------------------------------------------------------------
# detect_structuring: zero threshold -> ValueError (no silent div-by-zero)
# ---------------------------------------------------------------------------

def test_structuring_zero_threshold_raises():
    g = build_graph([])
    with pytest.raises(ValueError, match="threshold must be positive"):
        detect_structuring(g, threshold=0)


def test_structuring_negative_threshold_raises():
    g = build_graph([])
    with pytest.raises(ValueError, match="threshold must be positive"):
        detect_structuring(g, threshold=-500)


# ---------------------------------------------------------------------------
# analyze: returns empty list for empty graph (no division/crash)
# ---------------------------------------------------------------------------

def test_analyze_empty_graph_returns_no_findings():
    g = build_graph([])
    assert analyze(g) == []


# ---------------------------------------------------------------------------
# scan() + to_json(): convenience helpers behave correctly
# ---------------------------------------------------------------------------

def test_scan_returns_expected_keys():
    csv_text = (
        "tx_id,src,dst,amount,timestamp\n"
        "a,X,Y,50,2026-01-01T00:00:00Z\n"
        "b,Y,Z,12,2026-01-02T00:00:00Z\n"
    )
    result = scan(io.StringIO(csv_text))
    assert result["tool"] == "txgraph"
    assert result["transactions"] == 2
    assert result["finding_count"] == 0
    assert isinstance(result["findings"], list)


def test_to_json_produces_valid_json():
    import json
    result = scan(io.StringIO(
        "tx_id,src,dst,amount,timestamp\n"
        "a,X,Y,10,2026-01-01\n"
    ))
    text = to_json(result)
    parsed = json.loads(text)
    assert parsed["tool"] == "txgraph"


def test_scan_missing_file_propagates():
    with pytest.raises(FileNotFoundError):
        scan("/does/not/exist.csv")


# ---------------------------------------------------------------------------
# CLI: missing file -> exit code 2, message on stderr (not a traceback)
# ---------------------------------------------------------------------------

def test_cli_missing_file_exits_2(capsys):
    rc = main(["scan", "/nonexistent/path.csv"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "not found" in err.lower() or "error" in err.lower()


# ---------------------------------------------------------------------------
# CLI: negative/zero threshold -> exit code 2, message on stderr
# ---------------------------------------------------------------------------

def test_cli_negative_threshold_exits_2(capsys):
    demo = os.path.join(
        os.path.dirname(__file__), "..", "demos", "01-basic", "transactions.csv"
    )
    rc = main(["scan", demo, "--threshold", "-1"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "threshold" in err.lower()


def test_cli_zero_threshold_exits_2(capsys):
    demo = os.path.join(
        os.path.dirname(__file__), "..", "demos", "01-basic", "transactions.csv"
    )
    rc = main(["scan", demo, "--threshold", "0"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "threshold" in err.lower()


# ---------------------------------------------------------------------------
# CLI: no subcommand -> exit code 2
# ---------------------------------------------------------------------------

def test_cli_no_subcommand_exits_2():
    rc = main([])
    assert rc == 2


# ---------------------------------------------------------------------------
# mcp_server: module now imports cleanly (no ImportError from core)
# ---------------------------------------------------------------------------

def test_mcp_server_imports_without_error():
    """mcp_server.py must not raise ImportError at module import time."""
    import importlib
    mod = importlib.import_module("txgraph.mcp_server")
    assert hasattr(mod, "serve")

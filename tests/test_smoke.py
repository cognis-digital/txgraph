"""Smoke tests for TXGRAPH. No network. Runs against the shipped demo."""
import io
import os

import pytest

from txgraph import (
    load_transactions,
    build_graph,
    analyze,
    detect_structuring,
    detect_layering,
    detect_mules,
    sar_summary,
    TOOL_NAME,
    TOOL_VERSION,
)
from txgraph.cli import main

DEMO = os.path.join(os.path.dirname(__file__), "..", "demos", "01-basic",
                    "transactions.csv")


def _graph():
    txs = load_transactions(DEMO)
    return txs, build_graph(txs)


def test_metadata():
    assert TOOL_NAME == "txgraph"
    assert TOOL_VERSION.count(".") == 2


def test_load_parses_all_rows():
    txs = load_transactions(DEMO)
    assert len(txs) == 19
    # sorted ascending by time
    assert all(txs[i].epoch() <= txs[i + 1].epoch() for i in range(len(txs) - 1))
    assert txs[0].currency == "USD"


def test_graph_aggregates():
    _, g = _graph()
    assert "MULE_X" in g.accounts
    assert g.total_in("MULE_X") == pytest.approx(21000.0)
    assert g.total_out("MULE_X") == pytest.approx(20000.0)


def test_detect_structuring():
    _, g = _graph()
    fs = detect_structuring(g)
    assert any(f.kind == "structuring" for f in fs)
    smurf = [f for f in fs if "ACCT_SMURF" in f.accounts]
    assert smurf
    assert smurf[0].amount >= 10000.0
    assert len(smurf[0].tx_ids) >= 3


def test_detect_layering():
    _, g = _graph()
    fs = detect_layering(g)
    assert any(f.kind == "layering" for f in fs)
    chain = [f for f in fs if "ORIG_A" in f.accounts][0]
    assert chain.accounts[:2] == ["ORIG_A", "HOP_1"]
    assert "DEST_Z" in chain.accounts
    assert len(chain.tx_ids) >= 3


def test_detect_mules():
    _, g = _graph()
    fs = detect_mules(g)
    mule = [f for f in fs if f.accounts[0] == "MULE_X"]
    assert mule
    assert mule[0].amount == pytest.approx(21000.0)


def test_analyze_finds_all_three_kinds():
    _, g = _graph()
    kinds = {f.kind for f in analyze(g)}
    assert {"structuring", "layering", "mule"} <= kinds


def test_benign_only_has_no_findings():
    csv = ("tx_id,src,dst,amount,timestamp\n"
           "a,X,Y,50,2026-01-01T00:00:00Z\n"
           "b,Y,Z,12,2026-01-02T00:00:00Z\n")
    g = build_graph(load_transactions(io.StringIO(csv)))
    assert analyze(g) == []


def test_header_aliases_accepted():
    csv = ("id,from,to,value,date\n"
           "x,A,B,100,2026-01-01\n")
    txs = load_transactions(io.StringIO(csv))
    assert txs[0].src == "A" and txs[0].dst == "B" and txs[0].amount == 100.0


def test_missing_column_raises():
    with pytest.raises(ValueError):
        load_transactions(io.StringIO("tx_id,src,amount\n1,A,5\n"))


def test_sar_summary_text():
    _, g = _graph()
    text = sar_summary(analyze(g), g)
    assert "SUSPICIOUS ACTIVITY REPORT" in text
    assert "STRUCTURING" in text.upper()


def test_cli_exits_nonzero_on_findings():
    assert main(["scan", DEMO]) != 0


def test_cli_json_exit_and_clean(capsys):
    rc = main(["scan", DEMO, "--format", "json"])
    assert rc != 0
    out = capsys.readouterr().out
    import json
    payload = json.loads(out)
    assert payload["tool"] == "txgraph"
    assert payload["finding_count"] >= 3


def test_cli_fail_on_none_is_zero():
    assert main(["scan", DEMO, "--fail-on", "none"]) == 0

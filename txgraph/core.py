"""Core engine for TXGRAPH.

Parses transaction CSVs, builds a directed money-flow graph, and runs three
AML detectors:

  * structuring  - many sub-threshold transfers from one source that aggregate
                   to a reportable amount inside a short window (smurfing).
  * layering     - chains of pass-through transfers that move a similar amount
                   across several hops quickly (placement -> layering).
  * mule         - fan-in/fan-out accounts that receive from many senders and
                   quickly forward most of the value onward.

All logic is real; thresholds are configurable. Standard library only.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

# Default reporting threshold (USD). Structuring is sub-threshold by design.
DEFAULT_REPORT_THRESHOLD = 10000.0


def _parse_ts(raw: str) -> datetime:
    """Parse a timestamp; accept ISO-8601 and a couple of common formats."""
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("empty timestamp")
    # epoch seconds
    if raw.isdigit():
        return datetime.fromtimestamp(int(raw), tz=timezone.utc)
    txt = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(txt)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                    "%m/%d/%Y %H:%M", "%m/%d/%Y"):
            try:
                dt = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"unrecognized timestamp: {raw!r}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass
class Transaction:
    tx_id: str
    src: str
    dst: str
    amount: float
    ts: datetime
    currency: str = "USD"

    def epoch(self) -> float:
        return self.ts.timestamp()


REQUIRED_COLUMNS = ("tx_id", "src", "dst", "amount", "timestamp")

# Tolerated header aliases -> canonical name.
_ALIASES = {
    "id": "tx_id", "transaction_id": "tx_id", "txid": "tx_id",
    "source": "src", "from": "src", "sender": "src", "from_account": "src",
    "destination": "dst", "to": "dst", "receiver": "dst", "to_account": "dst",
    "value": "amount", "amt": "amount",
    "time": "timestamp", "ts": "timestamp", "date": "timestamp",
    "datetime": "timestamp",
}


def _canon(name: str) -> str:
    n = name.strip().lower()
    return _ALIASES.get(n, n)


def load_transactions(source) -> List[Transaction]:
    """Load transactions from a file path or an open text stream.

    Required (or aliased) columns: tx_id, src, dst, amount, timestamp.
    Optional: currency. Rows with bad data raise ValueError with the row number.
    """
    if hasattr(source, "read"):
        text = source.read()
    else:
        with open(source, "r", encoding="utf-8-sig", newline="") as fh:
            text = fh.read()

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("empty CSV: no header row")
    fieldmap = {fn: _canon(fn) for fn in reader.fieldnames}
    have = set(fieldmap.values())
    missing = [c for c in REQUIRED_COLUMNS if c not in have]
    if missing:
        raise ValueError(
            "CSV missing required column(s): " + ", ".join(missing)
            + f" (found: {', '.join(sorted(have))})"
        )

    txs: List[Transaction] = []
    for i, raw_row in enumerate(reader, start=2):  # row 1 is header
        row = {fieldmap.get(k, k): (v or "").strip() for k, v in raw_row.items()}
        if not any(row.get(c) for c in REQUIRED_COLUMNS):
            continue  # blank line
        try:
            amount = float(row["amount"].replace(",", "").replace("$", ""))
        except (ValueError, KeyError):
            raise ValueError(f"row {i}: invalid amount {row.get('amount')!r}")
        if amount < 0:
            raise ValueError(f"row {i}: negative amount {amount}")
        try:
            ts = _parse_ts(row["timestamp"])
        except ValueError as exc:
            raise ValueError(f"row {i}: {exc}")
        src = row["src"]
        dst = row["dst"]
        if not src or not dst:
            raise ValueError(f"row {i}: src/dst must be non-empty")
        txs.append(Transaction(
            tx_id=row.get("tx_id") or f"row{i}",
            src=src, dst=dst, amount=amount, ts=ts,
            currency=(row.get("currency") or "USD"),
        ))
    txs.sort(key=lambda t: t.epoch())
    return txs


class TransactionGraph:
    """Directed multigraph of money flow keyed by account id."""

    def __init__(self) -> None:
        self.out: Dict[str, List[Transaction]] = {}
        self.inn: Dict[str, List[Transaction]] = {}
        self.accounts: set = set()
        self.txs: List[Transaction] = []

    def add(self, tx: Transaction) -> None:
        self.txs.append(tx)
        self.accounts.add(tx.src)
        self.accounts.add(tx.dst)
        self.out.setdefault(tx.src, []).append(tx)
        self.inn.setdefault(tx.dst, []).append(tx)

    def out_edges(self, acct: str) -> List[Transaction]:
        return self.out.get(acct, [])

    def in_edges(self, acct: str) -> List[Transaction]:
        return self.inn.get(acct, [])

    def total_in(self, acct: str) -> float:
        return sum(t.amount for t in self.in_edges(acct))

    def total_out(self, acct: str) -> float:
        return sum(t.amount for t in self.out_edges(acct))


def build_graph(txs: Iterable[Transaction]) -> TransactionGraph:
    g = TransactionGraph()
    for t in sorted(txs, key=lambda x: x.epoch()):
        g.add(t)
    return g


@dataclass
class Finding:
    kind: str               # structuring | layering | mule
    severity: str           # low | medium | high
    accounts: List[str]
    tx_ids: List[str]
    amount: float
    detail: str
    score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def detect_structuring(
    g: TransactionGraph,
    threshold: float = DEFAULT_REPORT_THRESHOLD,
    window_hours: float = 72.0,
    min_count: int = 3,
) -> List[Finding]:
    """Flag a source making >= min_count sub-threshold transfers that aggregate
    past the reporting threshold within window_hours (classic smurfing).
    """
    findings: List[Finding] = []
    window = window_hours * 3600.0
    for acct in sorted(g.accounts):
        edges = sorted(g.out_edges(acct), key=lambda t: t.epoch())
        sub = [t for t in edges if t.amount < threshold]
        if len(sub) < min_count:
            continue
        # sliding window over sub-threshold transfers
        lo = 0
        for hi in range(len(sub)):
            while sub[hi].epoch() - sub[lo].epoch() > window:
                lo += 1
            span = sub[lo:hi + 1]
            agg = sum(t.amount for t in span)
            if len(span) >= min_count and agg >= threshold:
                # also require they sit just under the line (smurf signature)
                near = [t for t in span if t.amount >= 0.5 * threshold]
                sev = "high" if (len(span) >= min_count + 2 or near) else "medium"
                findings.append(Finding(
                    kind="structuring",
                    severity=sev,
                    accounts=[acct] + sorted({t.dst for t in span}),
                    tx_ids=[t.tx_id for t in span],
                    amount=round(agg, 2),
                    detail=(f"{len(span)} sub-${threshold:,.0f} transfers from "
                            f"{acct} totaling ${agg:,.2f} within "
                            f"{window_hours:g}h"),
                    score=round(agg / threshold + 0.25 * len(span), 3),
                ))
                break  # one finding per account is enough
    return findings


def detect_layering(
    g: TransactionGraph,
    min_hops: int = 3,
    max_gap_hours: float = 48.0,
    amount_tol: float = 0.15,
    passthrough_min: float = 0.80,
) -> List[Finding]:
    """Trace pass-through chains: A->B->C->... where each intermediary forwards
    a similar amount soon after receiving it. Long fast chains == layering.
    """
    findings: List[Finding] = []
    max_gap = max_gap_hours * 3600.0
    seen_chains: set = set()

    def follow(tx: Transaction, chain: List[Transaction], visited: set):
        node = tx.dst
        # find an onward transfer that forwards most of the received amount soon
        best: Optional[Transaction] = None
        for nxt in sorted(g.out_edges(node), key=lambda t: t.epoch()):
            if nxt.dst in visited:
                continue
            gap = nxt.epoch() - tx.epoch()
            if gap < 0 or gap > max_gap:
                continue
            ratio = nxt.amount / tx.amount if tx.amount else 0
            if passthrough_min <= ratio <= 1 + amount_tol:
                best = nxt
                break
        if best is None:
            if len(chain) >= min_hops:
                key = tuple(t.tx_id for t in chain)
                if key not in seen_chains:
                    seen_chains.add(key)
                    accts = [chain[0].src] + [t.dst for t in chain]
                    amt = chain[0].amount
                    findings.append(Finding(
                        kind="layering",
                        severity="high" if len(chain) >= min_hops + 1 else "medium",
                        accounts=accts,
                        tx_ids=[t.tx_id for t in chain],
                        amount=round(amt, 2),
                        detail=(f"{len(chain)}-hop pass-through chain "
                                + " -> ".join(accts)
                                + f" moving ~${amt:,.2f}"),
                        score=round(len(chain) + amt / 10000.0, 3),
                    ))
            return
        follow(best, chain + [best], visited | {best.dst})

    # only start chains at sources that are not pure pass-throughs themselves
    for tx in sorted(g.txs, key=lambda t: t.epoch()):
        follow(tx, [tx], {tx.src, tx.dst})
    # keep only the longest chain per starting tx
    findings.sort(key=lambda f: -len(f.tx_ids))
    deduped: List[Finding] = []
    covered: set = set()
    for f in findings:
        ids = set(f.tx_ids)
        if ids & covered:
            continue
        covered |= ids
        deduped.append(f)
    return deduped


def detect_mules(
    g: TransactionGraph,
    min_senders: int = 3,
    forward_ratio: float = 0.80,
    window_hours: float = 72.0,
) -> List[Finding]:
    """Flag accounts that collect from many distinct senders and quickly forward
    most of the aggregated value onward (fan-in -> fan-out mule).
    """
    findings: List[Finding] = []
    window = window_hours * 3600.0
    for acct in sorted(g.accounts):
        ins = g.in_edges(acct)
        outs = g.out_edges(acct)
        senders = {t.src for t in ins}
        if len(senders) < min_senders or not outs:
            continue
        total_in = sum(t.amount for t in ins)
        if total_in <= 0:
            continue
        first_in = min(t.epoch() for t in ins)
        # value forwarded within window after first inbound
        fwd = sum(t.amount for t in outs
                  if 0 <= t.epoch() - first_in <= window + 3600)
        ratio = fwd / total_in
        if ratio >= forward_ratio:
            sev = "high" if (len(senders) >= min_senders + 2 and ratio >= 0.9) else "medium"
            findings.append(Finding(
                kind="mule",
                severity=sev,
                accounts=[acct] + sorted(senders) + sorted({t.dst for t in outs}),
                tx_ids=[t.tx_id for t in ins] + [t.tx_id for t in outs],
                amount=round(total_in, 2),
                detail=(f"{acct} received ${total_in:,.2f} from {len(senders)} "
                        f"senders and forwarded {ratio*100:.0f}% onward"),
                score=round(len(senders) + ratio, 3),
            ))
    return findings


def analyze(
    g: TransactionGraph,
    threshold: float = DEFAULT_REPORT_THRESHOLD,
) -> List[Finding]:
    """Run all detectors and return findings sorted by severity then score."""
    findings: List[Finding] = []
    findings += detect_structuring(g, threshold=threshold)
    findings += detect_layering(g)
    findings += detect_mules(g)
    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: (order.get(f.severity, 3), -f.score))
    return findings


def sar_summary(findings: List[Finding], graph: TransactionGraph) -> str:
    """Produce a human-readable Suspicious Activity Report narrative."""
    if not findings:
        return ("SAR SUMMARY: No suspicious activity detected across "
                f"{len(graph.txs)} transactions / {len(graph.accounts)} accounts.")
    lines = [
        "SUSPICIOUS ACTIVITY REPORT (auto-generated by TXGRAPH)",
        "=" * 56,
        f"Scope: {len(graph.txs)} transactions across {len(graph.accounts)} accounts.",
        f"Total findings: {len(findings)} "
        f"({sum(1 for f in findings if f.severity=='high')} high severity).",
        "",
    ]
    for n, f in enumerate(findings, 1):
        lines.append(f"[{n}] {f.kind.upper()} ({f.severity}) - ${f.amount:,.2f}")
        lines.append(f"    {f.detail}")
        lines.append(f"    Accounts: {', '.join(f.accounts)}")
        lines.append(f"    Transactions: {', '.join(f.tx_ids)}")
        lines.append("")
    lines.append("Recommend manual review and, where warranted, regulatory filing.")
    return "\n".join(lines)

<a name="top"></a>
<div align="center">

<img src="https://capsule-render.vercel.app/api?type=rect&color=0:6b46c1,100:2b6cb0&height=120&section=header&text=TXGRAPH&fontSize=48&fontColor=ffffff&fontAlignY=58" width="100%" alt="TXGRAPH"/>

# TXGRAPH

### Builds a transaction graph from ledger/account data and surfaces structuring, layering, and mule-network patterns for AML triage.

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=3500&pause=1000&color=6B46C1&center=true&vCenter=true&width=720&lines=Builds+a+transaction+graph+from+ledgeraccount+data+and+surfa;Self-hostable+%C2%B7+MCP-native+%C2%B7+CI-ready+%C2%B7+polyglot" width="720"/>

[![PyPI](https://img.shields.io/pypi/v/cognis-txgraph.svg?color=6b46c1)](https://pypi.org/project/cognis-txgraph/) [![CI](https://github.com/cognis-digital/txgraph/actions/workflows/ci.yml/badge.svg)](https://github.com/cognis-digital/txgraph/actions) [![License: COCL 1.0](https://img.shields.io/badge/License-COCL%201.0-2b6cb0.svg)](LICENSE) [![Suite](https://img.shields.io/badge/Cognis-Neural%20Suite-6b46c1.svg)](https://github.com/cognis-digital)

*Fintech & Payments Security — PCI, fraud, AML, and payment rails.*

</div>

```bash
pip install cognis-txgraph
txgraph scan .            # → prioritized findings in seconds
```

## Contents

- [Why txgraph?](#why) · [Features](#features) · [Quick start](#quick-start) · [Example](#example) · [How it compares](#how-it-compares) · [Integrations](#integrations) · [Install anywhere](#install-anywhere) · [Related](#related) · [Contributing](#contributing)

<a name="why"></a>
## Why txgraph?

Graph-based money-laundering detection is academically hot but has no plug-and-play CLI; ingest CSV, emit suspicious subgraphs + SAR-ready summaries with zero infra is a viral AML demo.

`txgraph` is single-purpose, scriptable, and self-hostable: point it at a target, get prioritized results in the format your workflow already speaks (table · JSON · SARIF), gate CI on it, and let agents drive it over MCP.

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="features"></a>
## Features

- ✅ Load Transactions
- ✅ Build Graph
- ✅ Detect Structuring
- ✅ Detect Layering
- ✅ Detect Mules
- ✅ Analyze
- ✅ Sar Summary
- ✅ Runs on Linux/macOS/Windows · Docker · devcontainer
- ✅ Ports in Python, JavaScript, Go, and Rust (`ports/`)

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="quick-start"></a>
## Quick start

```bash
pip install cognis-txgraph
txgraph --version
txgraph scan .                       # scan current project
txgraph scan . --format json         # machine-readable
txgraph scan . --fail-on high        # CI gate (non-zero exit)
```

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="example"></a>
## Example

```text
$ txgraph scan .
  [HIGH    ] TXG-001  example finding             (./src/app.py)
  [MEDIUM  ] TXG-002  another signal              (./config.yaml)

  2 findings · risk score 5 · 38ms
```

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="how-it-compares"></a>
## How it compares

| | **Cognis txgraph** | AMLSim |
|---|:---:|:---:|
| Self-hostable, no account | ✅ | varies |
| Single command, zero config | ✅ | ⚠️ |
| JSON + SARIF for CI | ✅ | varies |
| MCP-native (AI agents) | ✅ | ❌ |
| Polyglot ports (JS/Go/Rust) | ✅ | ❌ |
| Open license | ✅ COCL | varies |

*Built in the spirit of **AMLSim / Neo4j fraud graph**, re-framed the Cognis way. Missing a credit? Open a PR.*

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="integrations"></a>
## Integrations

Pipes into your stack: **SARIF** for code-scanning, **JSON** for anything, an **MCP server** (`txgraph mcp`) for AI agents, and a webhook forwarder for SIEM/Slack/Jira. See [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md).

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="install-anywhere"></a>
## Install anywhere

| Linux | macOS | Windows | Docker | Cloud |
|---|---|---|---|---|
| `scripts/setup-linux.sh` | `scripts/setup-macos.sh` | `scripts/setup-windows.ps1` | `docker run ghcr.io/cognis-digital/txgraph` | [DEPLOY.md](docs/DEPLOY.md) (AWS/Azure/GCP/k8s) |

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="related"></a>
## Related Cognis tools

- [`panhound`](https://github.com/cognis-digital/panhound) — Scans code, logs, fixtures, and S3 buckets for leaked PANs (Luhn-validated card numbers) and CVVs before they hit prod.
- [`fraudlens`](https://github.com/cognis-digital/fraudlens) — Replays a stream of transactions against pluggable fraud rules and ML scorers, emitting precision/recall and alert volume from the terminal.
- [`obscan`](https://github.com/cognis-digital/obscan) — Conformance and security linter for Open Banking / FAPI APIs: validates OAuth flows, consent scopes, and PSD2 endpoints against the spec.
- [`ledgerproof`](https://github.com/cognis-digital/ledgerproof) — Verifies double-entry ledger integrity and tamper-evidence by checking balance invariants and hash-chained journal entries.
- [`iso20022`](https://github.com/cognis-digital/iso20022) — Validates, lints, and diffs ISO 20022 / pacs / camt payment messages and translates legacy MT into MX with schema-aware errors.
- [`tokenvault`](https://github.com/cognis-digital/tokenvault) — Self-hostable PCI tokenization microservice and CLI that swaps PANs for format-preserving tokens and proves no raw card data persists.

**Explore the suite →** [🗂️ all 170+ tools](https://github.com/cognis-digital/cognis-neural-suite) · [⭐ awesome-cognis](https://github.com/cognis-digital/awesome-cognis) · [🔗 cognis-sources](https://github.com/cognis-digital/cognis-sources) · [🤖 uncensored-fleet](https://github.com/cognis-digital/uncensored-fleet) · [🧠 hermes](https://github.com/cognis-digital/hermes)

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="contributing"></a>
## Contributing

PRs, new rules, and demo scenarios are welcome under the collaboration-pull model — see [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

> ### ⭐ If `txgraph` saved you time, **star it** — it genuinely helps others find it.

## License

Source-available under the **Cognis Open Collaboration License (COCL) v1.0** — free for personal, internal-evaluation, research, and educational use; **commercial / production use requires a license** (licensing@cognis.digital). See [LICENSE](LICENSE).

---

<div align="center"><sub><b><a href="https://cognis.digital">Cognis Digital</a></b> · one of 170+ tools in the <a href="https://github.com/cognis-digital/cognis-neural-suite">Cognis Neural Suite</a> · <i>Making Tomorrow Better Today</i></sub></div>

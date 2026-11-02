# Quanto

Quanto is a private quantitative research desk under construction. It combines deterministic calculations, recorded experiments, independent criticism, and a local interface for understanding the work. A separate trading service is planned after research and operational checks.

**Current state:** the synthetic research engine, private artifact store, registered exploration, interactive dashboard, contextual assistants, and local website supervisor exist. A bounded Alpaca historical pilot now passes evidence-bound split/dividend calculation, exact three-scenario replay and independent accounting comparison. Actual Fable and Opus council reviews have run through local Claude Code. Protected holdouts, persistent research roles, paper trading and live execution remain incomplete. No strategy is validated and nothing is trading.

## Run locally

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). From this repository:

```sh
uv sync --extra dev --locked
PYTHONPATH=src .venv/bin/python -m quanto demo
PYTHONPATH=src .venv/bin/python -m quanto status
PYTHONPATH=src .venv/bin/python -m pytest -q
.venv/bin/ruff check .
```

The demo runs synthetic prices through the actual engine and journal. Its results test software, not investment performance. Local records are ignored under `runtime/` and `artifacts/`.

The operator dashboard reads an explicit `runtime/status.json` observation snapshot. It refuses missing or invalid snapshots instead of inventing progress. With a recorded snapshot present, start it with:

```sh
PYTHONPATH=src .venv/bin/python -m quanto serve --port 8766
```

Open [the local desk](http://127.0.0.1:8766/). For macOS background supervision, inspect and install the project-owned LaunchAgent using the commands in [Operations](docs/OPERATIONS.md). Keep the project downloaded if its directory is synchronized with iCloud. Sleep, shutdown and logout interrupt local operation; this is not hosted 24/7 infrastructure.

## Data and registered exploration

For private historical acquisition, create keys in the Alpaca paper-account dashboard and save them through hidden prompts:

```sh
.venv/bin/python scripts/configure_alpaca.py
PYTHONPATH=src .venv/bin/python -m quanto acquire-bars --request examples/requests/alpaca-bars.json
PYTHONPATH=src .venv/bin/python -m quanto acquire-calendar --request examples/requests/alpaca-calendar.json
PYTHONPATH=src .venv/bin/python -m quanto submissions --limit 20
```

The helper preserves existing settings and writes `.env` with owner-only permissions. The adapter allows only specific historical-data, calendar and corporate-action reads. Downloaded data remains inspection-only until the separate admission checks pass. The historical-accounting software and bounded D007 pilot passed independent review; both earlier admission refusals remain preserved. Each deliberate acquisition is a new recorded attempt; no automatic retry or feed substitution occurs. See [Data sources](docs/DATA_SOURCES.md) for coverage and rights limitations.

Run a separate synthetic example to compare two lookbacks over identical evaluation dates, repeat one candidate under another name, and retain a malformed request:

```sh
PYTHONPATH=src .venv/bin/python examples/synthetic_exploration.py --root /tmp/quanto-synthetic-example
```

The example creates that directory and records all work there. It provides engineering evidence only. [Provenance](docs/PROVENANCE.md) explains artifact verification and retention; [Research protocol](docs/RESEARCH_PROTOCOL.md) explains development exposure, candidate counts and the remaining final-evaluation controls.

The event-accounting increment passed independent software review. Its separate example
uses invented prices to reconcile a two-for-one split and cash dividend:

```sh
PYTHONPATH=src .venv/bin/python examples/synthetic_actions.py
```

Both fixture portfolios finish with 20 shares at 50 and 10 cash, or 1,010 equity
from 1,000 starting cash. This validates the example's arithmetic, not a trading
strategy. [Accounting](docs/ACCOUNTING.md) records the numerical and payment
policies. [Action sources](docs/ACTION_SOURCES.md) documents the new bounded
`acquire-actions` command; `admit-dataset` checks preserved evidence before a
historical study can run. The bounded actual historical pilot passed; [its evidence report](docs/reviews/D007-historical-pilot.md) preserves source and development-exposure limits.

The D007 workflow also requires `register-split-review` for an independent review
of the exact event interpretation, `register-policy-revision` for the complete
plan/refusal history, and `register-suite` before the three frozen cost scenarios
can run. `run-suite` preserves every outcome and records a deliberate replay as a
new invocation. See [policy revisions](docs/POLICY_REVISIONS.md) and
[study suites](docs/STUDY_SUITES.md). These controls and the bounded actual historical pilot passed separate criticism,
quality and scope review. They do not establish a trading edge.

D008 adds a [bounded development workflow](docs/RESEARCH_WORKFLOW.md): issued roles,
authorized failure retrieval, strict model packets, shared spending controls and a
model-selected registered calculation. Synthetic integration has been independently
reviewed. Actual historical model operation and its trace review remain pending;
protected evaluation and unattended research are separate unfinished stages.

## Conversations and costs

Council reviews use the owner's existing Claude Code terminal login for exact
Fable and Opus models. Sanitized packets, visible responses and responding model
identities are retained. The council runner does not load the project's API key;
CLI cost estimates are not invoices. Website conversations use the separate API
configuration below.

Specialist conversations use new Haiku contextual assistants, while the desk helper uses Opus. Both answer from a bounded selection of saved project evidence. They cannot execute commands or trade. A separate worker inbox records questions for the actual original workers; replies require the lead to route the question and record a real answer with provenance.

Set `ANTHROPIC_API_KEY` only in the ignored local `.env` copied from `.env.example`, and restrict that file to its owner (`chmod 600 .env`). Never put keys in chat or committed files. Chat remains unavailable without this credential. The models are pinned to `claude-haiku-5-5` and `claude-opus-5-5`, with no silent fallback.

Cooperating Quanto requests share a USD 20 per America/Los_Angeles day ceiling. Reservations include uncertain calls and prohibit automatic paid retries. Conversations have a separate USD 18 conservative allowance; incident diagnosis is limited to USD 0.50. Healthy website checks cost nothing. UI amounts are conservative usage estimates, not invoices, and unrelated clients of the same API account are outside this ledger. No subscriptions are purchased.

## Project records

- [Context](docs/CONTEXT.md): objective and confirmed constraints.
- [Status](docs/STATUS.md): verified progress and open issues.
- [Requirements](docs/REQUIREMENTS.md): complete outcome and evidence requirements.
- [Roadmap](docs/ROADMAP.md): work still needed.
- [Decisions](docs/DECISIONS.md): reasoning, outside criticism and dispositions.
- [Design](docs/DESIGN.md): interface behavior and evidence boundaries.
- [Operations](docs/OPERATIONS.md): service controls and recovery limits.
- [Handoff](docs/HANDOFF.md): continuation checkpoint.

## Repository boundary

The repository remains private. Reusable code, documentation and synthetic tests belong here; credentials, licensed data, private strategies, portfolios, conversations and runtime records do not. A future public release requires a deliberate license choice and history/content review. See [Contributing](CONTRIBUTING.md) and [Security](SECURITY.md).

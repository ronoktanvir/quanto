# Contributing

Read AGENTS.md and the project context before changing scope or architecture.

## Development

Use Python 3.11 or newer. Create a virtual environment, install with `pip install -e '.[dev]'`, then run `pytest` and `ruff check .`. The dependency lock is maintained with uv. Tests must run without network access, API keys, or market-data purchases.

Use a feature branch and a focused pull request. Describe the behavior changed, why it matters, the evidence used to validate it, and any limitations. Keep commits coherent; do not rewrite shared history. Fix review findings in follow-up commits. CI and independent review are evidence, not substitutes for checking the affected behavior.

## Research and data

Synthetic fixtures belong in tests and must be labeled. Real-data artifacts, portfolios, credentials, and private strategy research belong in ignored local storage. Do not add fetched datasets to pull requests. Record provenance and permissions before introducing a provider.

Financial calculation changes need independent reference cases, timing checks, and accounting reconciliation. A new data field or metric must declare its meaning and unavailable/undefined cases.

## Publication

The owner has authorized a private repository. A future public release requires a license decision, dependency/data rights review, secret/history scan, and reproducible clean-checkout examples. No public publication is implied by a merged PR.

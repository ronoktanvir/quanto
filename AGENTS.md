# Quanto contributor instructions

Read docs/CONTEXT.md, docs/STATUS.md, docs/ROADMAP.md, and docs/DECISIONS.md before work. Read docs/HANDOFF.md when resuming. The user instruction is authoritative; do not redefine the objective to match the implemented subset.

## Objective and boundaries

Build a private research and eventual trading operation for the owner's own account. The complete target includes data ingestion, deterministic research, five bounded research roles, independent criticism, quality validation, scope review, durable failure memory, reliable scheduling, and separately gated execution. A prototype is not the complete operation. No subscription purchases. Outside-model API work is authorized through an existing account with a shared maximum of USD 20 per America/Los_Angeles calendar day. Do not claim that a local ledger controls spending by unrelated clients of that account.

Owner update on November2: renting Runpod network storage at roughly USD5/month is explicitly authorized for external checkpoints. The owner subsequently confirmed the key is ready and authorized up to USD50 total Runpod setup spending; treat this as a cumulative ceiling, not a monthly increase. This is a narrow exception to the no-purchase constraint, separate from the unchanged model-spending ceiling; it does not authorize GPU/CPU compute rental or unrelated subscriptions. Prepare the concrete storage/backup plan before transferring project data. Credentials stay in ignored local files and must never enter chat, logs or Git.

Research must not place live broker orders. Live promotion requires a concrete reviewed strategy, operational checks, and explicit owner approval. Keep research workers separate from execution credentials. Do not fabricate market data, model reviews, test results, benchmark claims, or completed milestones.

## Collaboration

The lead integrates work. Delegate isolated files/modules and state ownership. Use smaller models for bounded lower-complexity work, stronger reasoning for design and criticism. Significant architecture, scope, data, cost, or execution decisions require five independently briefed perspectives, staged when concurrency is limited, plus an actual outside-model review when access is available. Record unavailable cross-model review as pending, never as satisfied. Reversible work can continue while access is pending.

Criticism, quality validation, and no-drift review are separate roles. A producer cannot certify its own work as independent review. Reviewers must identify the exact revision/artifacts inspected. Preserve objections and fixes. Routine implementation choices within an approved decision do not need a new five-agent panel.

The owner's latest council preference is to invoke Fable and Opus through the existing local Claude Code terminal session, not through direct Anthropic API calls. Use the signed-in CLI route, keep review packets sanitized, record the actual responding model and terminal outcome, and do not silently replace an unavailable model. Do not load the project's API key into council CLI processes. Existing dashboard chats are a separate API-backed feature; this council preference does not request changing them. No new subscription or credit purchase is authorized.

## Evidence and engineering

Use explicit evidence kinds: synthetic_fixture, historical_market_data, prospective_paper, live_execution. Tests on synthetic fixtures validate software, not investment performance. Record every attempted experiment, including invalid, failed, and rejected runs. Persist code/specification/data identities and assumptions. Do not call SQLite immutable: use append-only application records and tested tamper evidence with a documented threat model.

Fail closed on unsupported financial assumptions. No same-close execution from a completed-close signal. No silent price filling, data substitution, or adjustment mixing. Holdout exposure must be tracked; later strategy changes do not restore an exposed holdout. External calls require conservative atomic budget reservations, bounded responses, and no unbudgeted retries.

## Context and GitHub hygiene

Update STATUS and HANDOFF after each integrated, verified increment. Update ROADMAP and DECISIONS when evidence changes the work. Record required future work explicitly. Keep docs/REQUIREMENTS.md traceable to evidence, with incomplete items marked incomplete.

Use small coherent commits and feature branches/PRs after bootstrap. Run relevant tests, lint, and clean-checkout checks. Never commit secrets, raw licensed data, private strategies, personal portfolios, local databases, or runtime outputs. Keep repository private until the owner requests publication and history/content review passes. Do not adopt an open-source license or make profitability claims without a deliberate decision.

## Communication

Lead with the outcome or decision and explain the reason and unresolved tradeoff. Ask questions asynchronously and continue independent work. Stop only dependent work at an actual gate. Do not repeat approvals already granted. Prefer concrete prose over promotional claims. Report what was executed separately from what is planned.

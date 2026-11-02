# Project context

## Governing objective

The owner asked the lead agent to create a persistent private quantitative research and eventual trading operation for the owner's own account. The lead should orchestrate implementation and independent reviewers, maintain contextualization files, make routine decisions autonomously, discuss significant dilemmas, and continue until the full operation is created and verified.

The original inspiration is QuantGPT: market history, deterministic backtests, multiple research roles, failure memory, and separated execution. The target is an independent implementation, not extraction of proprietary datasets or a copied product.

## Confirmed constraints

- Private own-account operation, not managing outside capital.
- No new subscriptions or paid hosting/data purchases.
- Existing outside-model API account use is permitted up to USD 20 per day; use America/Los_Angeles calendar days and a shared reservation ledger.
- Exact Claude Opus 5.5 is requested for outside-model criticism when available. Official model ID verified: claude-opus-5-5. Do not silently substitute.
- Five independent perspectives on substantive decisions; bounded lower-level tasks may use smaller models.
- Distinct criticism, quality validation, and no-drift oversight.
- GitHub repository initially private, healthy commits and PR practice, prepared for possible future public release.
- A clean localhost dashboard must visualize actual agent assignments, work, reviews, and progress, with truthful freshness and evidence.
- Asynchronous questions; independent work continues while answers or credentials are pending.

## Current interaction and operation design

The operator requested a Google DeepMind-inspired local interface, distinct agent icons, planned/active/completed work, conversations about each role, a larger desk helper, and continuous website supervision. Role chats use new contextual Haiku assistants; the desk helper uses Opus. Original worker inquiries use a separate durable inbox and only actual worker responses may be recorded. Assistants have no tools or trading authority. The local service runs while this Mac is awake and signed in.

The Anthropic credential is now configured in the ignored local .env. Two actual Opus reviews were received, totaling $0.309208 in calculated usage charges before interactive tests. Both requested model IDs were confirmed by the provider model listing. The starting-environment section below is historical.

## Verified starting environment

On 2026-11-01, the workspace was empty. Python 3.11.9, uv, git, and authenticated GitHub CLI were available. ANTHROPIC_API_KEY, Alpaca keys, and FRED_API_KEY were absent from the task environment. No Claude/Anthropic plugin was returned by the plugin search. No paid model request or subscription purchase occurred.

The full objective remains active. Credentials and live trading approval are future dependency gates, not reasons to stop building independent components.

## Personal dashboard and diagrams

The owner rejected a company-landing-page appearance. The local interface is a compact personal management workspace, with work and operations first. It must include an interactive milestone dependency diagram that updates from the same recorded progress as the board. Arrows represent recorded prerequisites, not actual inter-agent messages or automatic promotion decisions.

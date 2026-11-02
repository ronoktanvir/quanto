# D008 bounded CLI council budget review

Recommendation: a useful Fable5.1/Opus5.5 pair can conservatively fit the stated remaining **$2.020721**, conditional on the packet and dispatch limits below. Do not reuse D007's $3.50-per-model reservations, release existing uncertain holds, or describe this estimate as a guaranteed billing cap. If these limits cannot be met, defer the pair; reversible independent work can continue.

## Inspected evidence and limits

Reviewed repository governance/context/status/roadmap/decisions/handoff and `runtime/council-cli/d007/run_d007.py` (SHA-256 `d598fb97bc9e94caf40c6a5045fb06877108ff981bfa4e4f4bb9dee2a30470ab`); inspected installed CLI help without starting inference. Official CLI, environment-variable and cost documentation was checked on 2026-11-02 UTC. No credentials, private provider data, raw council responses or new D008 adviser reports were inspected. No paid calls, budget changes or implementation edits occurred. The lead supplied the $17 existing uncertain CLI holds, $0.979279 settled usage, 47,688-byte adviser aggregate and approximately 8,000-byte proposal estimate; these were not independently reconciled.

Use the lead-verified conservative prices per million tokens: Fable input $10/output $50/one-hour cache write $20; Opus input $4/output $20/cache write $8. Price every input token at the higher one-hour write rate, without assuming a warm cache. CLI cost figures are local estimates and do not reconcile subscription billing. [Official cost documentation](https://code.claude.com/docs/en/costs).

## Concrete envelope

Prepare one identical sanitized packet for both reviewers, at most **20,000 UTF-8 bytes**. Include the complete concrete proposal, five separately attributed faithful adviser summaries, material disagreements, unresolved objections and a manifest of source hashes. Keep the replacement system prompt at most **1,000 UTF-8 bytes**. Check exact byte sizes and hashes before reserving anything. Roughly 10,000–11,000 bytes remain for summaries and manifest when the proposal is 8,000 bytes; never omit a material objection merely to meet this limit.

Account at one token per supplied byte, plus a separate **10,000-token allowance** for client framing, attribution and other injected material: **31,000 input tokens per model**. This deliberately avoids the optimistic English characters-to-token ratio. The framing allowance is an operational assumption, not a measured or guaranteed maximum. The existing empty-directory, replacement-system-prompt, disabled-customization/tool/MCP route makes it plausible; unexpected loaded context or policy additions require deferral or a new calculation.

Set `CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192`, retain high effort, and request a focused final critique of approximately 600–800 words addressing consequential defects, fixes and acceptance conditions. Budget all 8,192 output tokens, including reasoning, rather than only visible prose. Set `CLAUDE_CODE_MAX_TURNS=1`, retries zero and no watchdog, fallback, resume, continuation, structured-output repair or automatic retry. Keep D007's 240-second request and 300-second process timeouts, credential exclusion, nonessential-traffic disablement and sanitized OAuth route. Do not use `--bare` with this OAuth route.

The documented output variable applies to most requests; turn and retry variables are documented controls, not evidence that billing is intrinsically bounded. Preserve disabled tools/MCP and verify one-turn exact-model outcomes. [Environment reference](https://code.claude.com/docs/en/env-vars).

| Model | Input at cache-write rate | Maximum output | Estimated envelope | New reservation |
| --- | ---: | ---: | ---: | ---: |
| Fable5.1 | $0.620000 | $0.409600 | $1.029600 | $1.400000 |
| Opus5.5 | $0.248000 | $0.163840 | $0.411840 | $0.600000 |
| Pair | $0.868000 | $0.573440 | $1.441440 | $2.000000 |

These reservations leave $0.558560 above the modeled envelope and $0.020721 unallocated. Reserve both allowances atomically before the first dispatch, with no intervening cooperating paid work. Recheck the Los Angeles day and current ledger first. The ledger cannot govern unrelated account clients. Client spend thresholds of $1.00/$0.40 may provide additional stop signals but are not reservation amounts: the official CLI reference explicitly permits threshold overshoot. [CLI reference](https://code.claude.com/docs/en/cli-reference).

## Review usefulness and disposition

The complete proposal plus faithful attributed summaries supports substantive policy criticism. It does not support claiming either model inspected the full adviser reports. Record exact packet/hash, actual responding model, terminal completion and any truncation. Preserve objections. An unavailable model, incomplete critique, unexpected turn or accounting uncertainty leaves the relevant outside review pending, without an unbudgeted retry. Retain both new holds as uncertain absent authoritative reconciliation; do not use low CLI estimates to free headroom.

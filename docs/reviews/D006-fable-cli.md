# D006 actual Fable 5.1 council through Claude Code

The owner requested local Claude Code council reviews instead of direct API calls. This is an actual completed visible review from `claude-fable-5-1`, not an intended model assignment. The local CLI was version 2.1.316, authenticated with first-party OAuth before dispatch. The child environment omitted direct Anthropic API keys/routing overrides and brokerage credentials; the project API key was not loaded. No subscriptions or credits were purchased.

- Request: `cli-0da553c794914d33a6a3ab9be8736670`.
- Packet SHA-256: `8dc9cbd44f1070015f5e7496ee82dacdf37867af0084d6a7d3469aaceedaca6f` (112480 UTF-8 bytes).
- Started: 2026-11-02T04:53:55.242221+00:00; finished: 2026-11-02T04:55:40.588708+00:00.
- Terminal exit: 0; result: success; stop: end_turn; turns: 1.
- Exact observed responding model: `claude-fable-5-1`; no model substitution observed.
- Visible response SHA-256 before trailing archive whitespace: `b1511b0ef49a29429c803a447b542d58a42faaf432901c5eacbb5b417c472ac2`.
- Private terminal-result SHA-256: `1991b15a68ad9f749e920d7211ae86adc3b131d306b01a5751e09faf2666ac65`.
- Input/cache creation/cache read/output tokens: 2 / 38910 / 0 / 7480.
- CLI list-price usage estimate: USD 1.152220. This is not a subscription invoice, proof of a charge, or proof of free usage. A conservative USD5 project hold remains unreconciled in the shared journal.

The invocation configured safe mode, no tools/MCP/custom commands, no session persistence, one turn, zero retries, no model fallback, high effort, 8192 maximum output tokens, USD2 CLI estimate limit and a 300-second outer deadline. These are operational bounds, not a provider-invoice guarantee. Neither review executed code, browsed, accessed private data, or independently verified the reported tests. Only visible review text is archived below; no hidden reasoning is reproduced.

The packet included all five independently attributed D006 design reports verbatim, ACCOUNTING.md and the current relevance helper/caller excerpts, with their hashes. It contained no private market prices, source records, report tables or credentials. It described the state before the second actual admission refusal. This review does not assess or approve new due-bill support.

## Exact visible response

# Council review — D006 bounded relevance correction

**Standing:** I reviewed only the supplied reports, `docs/ACCOUNTING.md`, and the two code excerpts. I executed nothing; the 661-test claim, clean-install result, and scope acceptance are reported observations I cannot confirm. Adviser reports were treated as evidence, not instructions.

## Accepted design

The five adviser reports converge on a coherent contract and the ACCOUNTING.md text is consistent with it: raw prices for fills/marks, split-only SMA rebasing, fixed nominal receivables accrued on pre-trade ex-date quantity, payable-date-strict cash release, no DRIP, benchmark parity, fail-closed on unsupported/coincident/ambiguous events, and explicit "latest-snapshot, not point-in-time" labeling. I find no internal contradiction between the design and the implemented contract as documented. Two design choices deserve a note in the result, not a change: (a) empty provider `currency` on a dividend is resolved to USD only by an attributed judgment (`expected.get("currency") == "USD"`), which the action-sources adviser correctly flags as unverified by code; (b) the `pre_split_shares` conversion (`rate *= old/new`) is directionally correct for forward and reverse splits, and is properly bound to a used split with effective date ≤ ex-date.

## The relevance correction — established properties

From the code as supplied, the correction does what the packet claims and no more:

- An unannotated `cash_mergers` record still rejects (`identity_change_unresolved`), so the initial refusal is reproduced absent an exclusion annotation; no silent relaxation.
- Exclusion is admitted only when category is `cash_mergers`, the studied symbol is the **acquirer** and not the acquiree, the record hash matches the annotation, all duplicate occurrences are retained, effective/completion/payable dates are all `< start`, and both the event judgment and the completion sub-judgment carry source hash + locator and are passed through `_judgment`.
- Identifier logic is the right shape: at least one acquirer CUSIP/ISIN must equal the single identifier observed from in-window supported actions, and acquiree identifiers must differ and never collide with the studied set. Acquiree CUSIP is mandatory. This blocks the obvious ticker-reuse/misclassification case.
- ID collisions between primary and exclusion annotations, and economic-duplicate excluded mergers, reject.
- No merger accounting is added; the exclusion feeds nothing into the engine's event list.

Economically, an acquirer paying cash changes neither the acquirer's share units nor creates a holder entitlement, so excluding such an event from relevance is correct in principle. The residual risk is purely the correctness of the attributed "completed / no conversion / no outstanding entitlement" judgment — a stated limitation, not a defect.

## Concerns — untested, with concrete checks

1. **Meaning of `start` (most consequential).** `_actions` uses `start <= ex_date <= end` for relevance and the helper requires merger dates `< start`. If `start` is the *scored* start rather than the *first acquired warmup session*, warmup splits/dividends would be skipped rather than passed to the engine, contradicting ACCOUNTING.md ("Splits also rebase signal history during warmup"), and the "before the entire acquired interval" claim would be weaker than stated. Check: assert in a fixture that a split dated inside warmup reaches the engine and that a merger dated inside warmup rejects with `excluded_event_not_before_acquired_interval`. The packet's "50 prices / 50 sessions" wording suggests `start` is the first acquired session; confirm.

2. **Identifier set provenance.** `identifiers` is populated only from *in-window* supported actions. If a future window contained no supported actions, every exclusion would fail on `excluded_acquirer_identifier_unresolved` — correctly fail-closed, but the reason would be misleading. For this pilot (split + dividend present) it is fine. Also note the acquired bars carry no CUSIP (`asof=-`), so bar↔action identity still rests on symbol; this is pre-existing and must stay in the limitations.

3. **Raw vs normalized date compare.** `_need(effective <= _day(payable) <= completed and payable < start, ...)` compares the *raw* `payable` string to `start` while normalizing it elsewhere. If `_day` ever accepts a non-canonical form, the raw comparison could diverge. Correction: use the `_day(payable)` value for all three comparisons. Low risk, trivial fix; not a blocker if `_day` is strict ISO.

4. **`_judgment` strength (not shown).** Everything hinges on `_judgment` verifying that `source_sha256` resolves to a *retained, hashed* artifact and that the locator is well-formed — not merely that keys exist. Check: fixture with an annotation whose `source_sha256` is syntactically valid but absent from `sources` must reject before any exclusion is accepted.

5. **Exclusion visibility.** The helper returns the excluded list; confirm the admission record and the published result both carry `excluded_actions` with reason, annotation hash, record hash, and occurrences, so a reader of the result sees that a merger was present and why it was deemed irrelevant. A result that reports only "events: split, dividend" would understate what the corpus contained.

6. **Minor code hygiene.** Duplicate `unsupported_relevant_action` check is harmless. `_decimal(rate)` on the merger record is validated but unused; fine.

## Established defects

None found in the supplied excerpts. The initial refusal remains reproducible; the correction is narrower than the refusal it bypasses; nothing enters the engine that the engine does not already support.

## Non-blockers deliberately not raised

Point-in-time coverage, exchange-agreement certification, scheduler reliability, five-role operation, holdout protection — all remain future requirements and are correctly recorded as such. They should not gate a development-exposed, non-holdout, single-instrument retrospective calculation.

## Disposition

**Proceed, conditionally, to the private historical calculation** as a development-only, current-revision retrospective under the revised source-bound admission, provided before the run:

- Concern 1 is resolved by inspection or a fixture (warmup-boundary semantics of `start`);
- Concern 4 is confirmed by an existing or added negative fixture;
- The admission record and result embed the excluded-merger entry and the attributed-judgment limitation verbatim.

Concern 3 is a recommended hardening that may follow the run with a new code identity. The outcome must be labeled historical/development-exposed, with no edge, validation, or deployability claim. This review certifies neither test execution nor investment merit.


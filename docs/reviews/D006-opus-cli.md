# D006 actual Opus 5.5 council through Claude Code

The owner requested local Claude Code council reviews instead of direct API calls. This is an actual completed visible review from `claude-opus-5-5`, not an intended model assignment. The local CLI was version 2.1.316, authenticated with first-party OAuth before dispatch. The child environment omitted direct Anthropic API keys/routing overrides and brokerage credentials; the project API key was not loaded. No subscriptions or credits were purchased.

- Request: `cli-f3397873c55b4058a984ff5182b0e908`.
- Packet SHA-256: `8dc9cbd44f1070015f5e7496ee82dacdf37867af0084d6a7d3469aaceedaca6f` (112480 UTF-8 bytes).
- Started: 2026-11-02T04:55:40.595830+00:00; finished: 2026-11-02T04:56:53.028871+00:00.
- Terminal exit: 0; result: success; stop: end_turn; turns: 1.
- Exact observed responding model: `claude-opus-5-5`; no model substitution observed.
- Visible response SHA-256 before trailing archive whitespace: `450c6594f83f7f077a38de43d6fcb37768889699d0acf2a6aeda84252e574848`.
- Private terminal-result SHA-256: `48ef23b9bde120c3bd969c6705a3ee03381c6d25204f45b636bc624fed659a89`.
- Input/cache creation/cache read/output tokens: 2 / 38887 / 0 / 7025.
- CLI list-price usage estimate: USD 0.451604. This is not a subscription invoice, proof of a charge, or proof of free usage. A conservative USD5 project hold remains unreconciled in the shared journal.

The invocation configured safe mode, no tools/MCP/custom commands, no session persistence, one turn, zero retries, no model fallback, high effort, 8192 maximum output tokens, USD2 CLI estimate limit and a 300-second outer deadline. These are operational bounds, not a provider-invoice guarantee. Neither review executed code, browsed, accessed private data, or independently verified the reported tests. Only visible review text is archived below; no hidden reasoning is reproduced.

The packet included all five independently attributed D006 design reports verbatim, ACCOUNTING.md and the current relevance helper/caller excerpts, with their hashes. It contained no private market prices, source records, report tables or credentials. It described the state before the second actual admission refusal. This review does not assess or approve new due-bill support.

## Exact visible response

# Council review: Quanto D006 post-acquisition cash-merger relevance correction

**Scope.** I reviewed only the supplied text and code excerpts. I executed nothing, and the reported results (661 tests plus 12 subtests, the critic/quality/scope acceptances, 50/50 bar-calendar match) are observations I have not verified. The other adviser reports are inputs I assessed, not instructions.

## 1. Accepted design

The five adviser reports agree with each other and with `ACCOUNTING.md` on the main points:
- raw prices for fills and marks, and a split-neutral SMA that keeps dividend drops;
- dividend receivables recognized on the ex-date, with conservative release of payment cash;
- no automatic dividend reinvestment, and a benchmark built with matching treatment;
- rejection of unsupported or ambiguous coincident events;
- separate status states for acquisition, coverage and admission.

I found no consequential conflict between the design and the accounting contract as written. Neither the advisers nor the contract treat universal completeness or point-in-time data as a prerequisite. I agree.

One tension is resolved by wording. The accounting adviser says to reject "unsupported … merger" for the whole study, but qualifies it as "relevant unsupported actions throughout warmup/evaluation." The admission adviser says "refuse … mergers … unless supported." A merger where the studied security is the acquirer, paid in cash, and completed before the first acquired bar is arguably not relevant. So the correction fits the advisers' relevance language and does not override them, as long as the action stays recorded and visible rather than dropped. The helper does keep it, returning the record hash and occurrences.

## 2. The relevance correction

The economic rationale is sound. When the studied issuer pays cash for another company, its own share units do not change and its own holders gain no entitlement. If the deal completed before any acquired bar, it cannot affect raw-price accounting or the signal.

The helper is appropriately fail-closed:
- **Category:** cash mergers only. Stock and mixed mergers fall through to `identity_change_unresolved`, assuming `cash_mergers ∈ IDENTITY_EVENTS`, which the preserved initial refusal implies.
- **Fields and binding:** exact field allowlists, record-hash binding, and a provider-ID/category match.
- **Roles:** the studied symbol must be the acquirer, the acquiree must be a different symbol, an acquiree CUSIP is required, and acquiree identifiers must not collide with the studied security.
- **Dates:** effective date ≤ completion date < start.
- **Payment:** if a payable date exists, it must fall within the effective-to-completion span.
- **Coverage:** no exclusion annotation may be left unmatched.
- **Ordering:** same-ID conflicts are checked across the entire corpus before any exclusion is applied.

## 3. Items to confirm before the private calculation

None of these is an established defect. Each is an untested concern with a concrete check.

**1. Meaning of `start` (the most consequential).** The correction claims "strictly before the *entire acquired interval*." Whether `effective < start` and `completed < start` deliver that depends on what the caller passes as `start`:
- If it is the first **warmup** session, the claim holds. This is also consistent with the `start <= ex_date <= end` filter, given that warmup splits must rebase the signal.
- If it is the first **evaluation** session, two failures follow: a merger during warmup could be excluded, and warmup splits would be silently skipped by the relevance filter. That second effect would be a real signal defect.
- **Check:** confirm at the call site that `start` equals the first acquired, admitted bar. Add a fixture with a warmup-date cash merger, and one with a warmup split, asserting rejection or application respectively.

**2. Source of the identifier anchor.** The acquirer-identity check (`observed == {own}`) compares against identifiers taken only from in-window supported actions, not from the frozen instrument identity evidence. It fails closed when no in-window CUSIP/ISIN exists. However, it does not tie the merger to the identity behind the price bars.
- **Check:** the admission record should also require the matched acquirer identifier to equal the instrument's frozen identity evidence. At minimum, record that the anchor came from action records.

**3. Date comparison consistency.** `payable < start` uses the raw record string, while other comparisons use `_day(...)`. This is safe only if `_day` enforces canonical ISO and returns strings. The `"9999"` sentinel elsewhere suggests it does.
- **Check:** use the parsed value consistently. Add a fixture for a payable date exactly on `start`.

**4. Branch coverage of the new helper.** The reported test count does not show which rejection paths are covered. Confirm a fixture exists for each of these:
- the studied security as acquiree;
- a stock merger and a stock-and-cash merger;
- effective date equal to `start`;
- completion date on or after `start`;
- a payable date after completion;
- no acquirer CUSIP or ISIN;
- an ISIN-only match;
- an acquiree CUSIP that is in the observed set;
- two IDs with the same economic merger;
- an exclusion annotation pointing at a supported or in-window record;
- an exclusion ID absent from the corpus;
- an altered record hash;
- missing completion keys, and the `no_*` flags being `False` or non-boolean.

**5. Disclosure and forking-path risk.** The rule was written after the action corpus, and possibly the prices, were seen. That is acceptable for a development-exposed accounting pilot only if the following are recorded:
- the result binds to the corrected rule's code hash;
- the initial `identity_change_unresolved` refusal is linked as a prior attempt;
- the report lists the excluded action, its attributed AI judgment (source hash and locator), and the fact that completion and no-entitlement were judged rather than verified by code;
- the rule is not described as preregistered.

Any later use of this exclusion rule on other instruments or windows should be treated as a versioned admission policy, not inherited silently.

## 4. Remaining limitations (not blockers for this pilot)

- AI-extracted source facts; the `True` flags are bound to sources but not verified by code.
- A latest-revision, non-point-in-time vendor snapshot.
- Uncertified account and exchange terms.
- Immediate availability of sale proceeds.
- Fractional quantities.
- An assumed open-price fill.

All of these are already disclosed. Protected evaluation, the five-role research cycle, failure retrieval, scheduling, paper trading and live execution remain future gates. They should not block this calculation.

## 5. Disposition

**Limited conditional proceed.** The bounded relevance correction is economically coherent, narrow and fail-closed in the code supplied. I identify no established defect that blocks it.

Run the private historical calculation only after:
1. confirming item 1 (`start` is the first acquired warmup bar);
2. confirming the item 4 rejection fixtures exist, or adding them;
3. binding the admission record to the disclosures in item 5.

Items 2 and 3 are recommended hardening.

The outcome should be described only as a development-exposed, current-revision, retrospective accounting and provenance calculation. It is not an edge claim, not validation, and not trading readiness.


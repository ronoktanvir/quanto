# D011 Fable CLI critique

Actual responding model: `claude-fable-5-1`. One signed-in local Claude Code turn completed on November 4, 2026 (Los Angeles), with exit 0 and an accepted terminal. The reviewer received the complete proposal and attributed lead summaries of five independent perspectives, not full reports, implementation or private observations. Packet SHA-256 `29c52dc46c15b8a04757be40142a0dcdb1a84cb73529cff11f1e3ecc9e42bac7`; visible response SHA-256 `b429755727151f757f7a7ed8f6137a4bd461f2538094df656842b611a54e326e`. Tools, MCP, fallback and retries were disabled; available terminal counters reported no tools/subagents. This is observed terminal evidence, not privileged process attestation.

The CLI estimated USD 0.295910; the full USD 1.40 reservation remains uncertain because provider billing is unreconciled. Outer process handle 90287 completed in terminal chunk `c9ede7`, exit 0. The invocation is consumed and cannot be retried.

## Full visible response

# Independent critique of D011

**Overall judgment.** The staged protocol is sound in direction: a finite, registered, one-family development screen now; no edge claim; unseen evaluation deferred until exposure is reconciled or a future interval is precommitted. The defects below are mostly places where the text leaves discretion that a later reader could exploit, or where an "honest" result is unverifiable as written.

## Consequential objections and fixes

**1. The pre-acquisition freeze is unverifiable.** The manifest lives outside Git, so "frozen before acquisition" rests on assertion. *Fix:* commit a hash of the private manifest plus a registration timestamp in-repo before the first acquisition receipt; acquisition receipts must reference that hash. The manifest itself stays private.

**2. "Indistinguishable" and the selection cost case are undefined.** "Favor simpler candidates when indistinguishable" is a discretionary tie-break that can rescue a preferred lookback. Nine traces also permit choosing the cost case per candidate. *Fix:* the manifest names one selection cost case, one numeric criterion on the validation block, a numeric tolerance (or fixed ordering: shortest lookback wins ties), and a no-candidate floor. Other cost cases are reported, never used for selection.

**3. Trial counting is incomplete for bugfix reruns.** If the engine is corrected after a slot executes, rerunning silently converts a consumed slot into a fresh one. *Fix:* any code change affecting a scored trace creates a new campaign version with explicit lineage; prior results are retained and labelled superseded, not deleted. Diagnostic variants and manual revisions count toward the trial maximum.

**4. Cash and dividend conventions bias both sides and should be disclosed by direction.** Zero-interest cash understates a long/cash strategy during high-rate regimes (conservative for the strategy), while idle dividends understate buy-and-hold (favorable to the strategy). *Fix:* state both directions explicitly; add one disclosed constant-rate sensitivity for cash and label the benchmark "price-plus-idle-distributions," never "total return."

**5. Capital-gains distributions.** Acquisition retains them; admission does not support them. "Fail on unknown relevant actions" may silently exclude years or the instrument. *Fix:* decide in the manifest whether such actions fail the slot or are restricted to a pre-specified handling; record the decision before data is seen.

**6. Power and episode concentration will likely dominate.** A slow-SMA long/cash rule on one ETF over the available span (Alpaca history is limited) produces a handful of trades; results are typically driven by one or two drawdown episodes. *Fix:* the manifest states expected trade count; the report includes an episode attribution (share of excess return from the top-k exits) and warmup aligned to the longest lookback so all candidates share identical scored dates.

**7. The future interval should be the primary unseen route, not a fallback.** For a liquid, well-known ETF, any model-authored candidate is contaminated by public-history knowledge regardless of local separation; historical "protected" reconciliation cannot repair this. *Fix:* precommit the future-interval plan now (start, end, candidate hash, benchmark, cost, sample plan, release rule), and present it honestly as a falsification check with low power, not confirmation. Early visible paper monitoring consumes the affected observations.

**8. Inferential plan risks.** Paired daily strategy-minus-benchmark differences are heteroskedastic and heavy-tailed; a block bootstrap with an uncalibrated block length can be either optimistic or vacuous. The power computation may show the campaign uninformative. *Fix:* require the power result to be stated before data acquisition and accept "uninformative by design" as a legitimate recorded outcome.

**9. Exposure controls at the boundary.** Dashboard and website summaries can leak instrument identity or parameters via charts or filenames. *Fix:* the schema for approved summaries whitelists fields; instrument and lookbacks are rendered as opaque slot labels.

## Minor corrections

- Replace "no cost model" with "generic per-fill cost scenarios are assumptions" in the result header, not only in prose.
- Report Sharpe only as unannualized daily with denominator rule stated; undefined when zero variance.
- Ensure the benchmark trace uses the same prior-boundary-wealth block reduction.
- The lead's single-family decision is acceptable but should be recorded as a limitation: the screen cannot speak to volatility overlays or reversal.

## Acceptance conditions

**Development screen (acceptable now)** if: manifest hash committed before first receipt; ≤3 candidates × ≤3 cost cases, one selection cost case and numeric criterion; all slots reported (executed, failed, unattempted); identical scored dates; independent reconciliation of equity components; benchmark conventions labelled by bias direction; `investment_validation=false`, `protected_evaluation=false` enforced; episode attribution and trade count present.

**Protected/statistical acceptance (not now)** requires: evidence-backed scope reconciliation or a precommitted future interval; estimand, worthwhile-effect threshold, dependence calibration, power stated before observation; selector/reviewer separation; explicit acknowledgment that model public-history knowledge remains unmitigated for historical routes.

Not acceptable under any outcome: using assessment blocks to choose; relabelling a rerun as fresh; flipping the access-registry flags; inferring "no edge" from a failed criterion.

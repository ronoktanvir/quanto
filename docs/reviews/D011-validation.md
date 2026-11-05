# D011 independent perspective: evaluation and costs

Reviewer: `/root/queue_validation`. Inspected base revision `94e0df5a79234f3423cabe137377efb796fe9cd0` in the isolated strategy-research worktree; initially inspected the same engine/access modules at root revision `60fe9299ab44cbd34962944fcc8039f1376435da`. Read contributor instructions, current context/status/roadmap/decisions/handoff, D008 policy/proposal and evaluation advice, and the public research, event-engine, explorer, scenario-suite, comparison and evaluation-registry APIs. No private data, credentials, database, actual research, model dispatch or financial result was inspected or executed. This is a design recommendation, not implementation or strategy acceptance.

## Decision

Run a small, frozen historical screening batch now, and report its results as development evidence. In parallel, build the separately reserved future evaluation required by D008. The smallest useful batch needs three or fewer simple candidate specifications, one mechanically chosen instrument/universe scope, one buy-and-hold comparator, all declared cost scenarios and chronological diagnostics. Large parameter grids, volatility targeting, multiasset optimization and machine learning are unnecessary for the first informative result.

The current repository cannot honestly certify an unseen strategy test. `Supervisor.protected_acquire()` expressly refuses, and the existing development control store remains legacy-unknown. Choosing a new directory, ticker or historical split does not repair exposure history. A chronologically held-back calculation is useful, but describe it as historical assessment with unknown prior owner/model knowledge. D008's genuinely final campaign freezes before future observations begin. Do not delay historical screening merely because future observations take calendar time.

## A finite first screening batch

1. Freeze the candidate roster and all parameters in a private manifest before acquisition or calculation. Recommend at most three supported, fixed trend specifications for this increment; parameter values and exact instruments belong outside tracked files. Record every proposal, failed registration, rejected candidate, cost case and calculation attempt. Freeze the eligibility rule, source/feed, calendar, accounting policy, start/end, warmup, split dates, benchmark, costs, candidate-selection rule and code identity. Select instruments from documented eligibility, not subsequent returns.
2. Define three contiguous chronological blocks: development, validation and later historical assessment. Dates follow a mechanical calendar rule declared in advance. Development can inform a bounded proposal before its final freeze. Validation selects at most one champion using a fixed criterion and tie-break; the later block never changes the selection. If multiple champions are later compared, that is a new declared multiple-test family rather than a hidden extension.
3. Execute each frozen candidate once across the full admitted history for each declared cost case. Retain continuous holdings, cash, dividend claims and benchmark wealth when calculating block metrics. A block's first return uses the prior boundary wealth. Do not concatenate independently restarted backtests and call the result a continuously investable strategy. Three candidates by three costs produce nine traces and 27 block summaries, not 27 independent experiments. The unchanged fixed rules need only trailing warmup; fitting, overlapping forward labels or outcome-dependent features require a separately specified training/label boundary.
4. Select the champion deterministically from validation results at the primary cost case, with a predeclared downside constraint and deterministic simpler-rule tie-break. Permit `none`: no candidate is required to pass. The historical assessment report includes the selected champion's result and all roster outcomes so losses cannot disappear, but it remains development evidence after release. No extra parameter variant may be added to rescue a bad result.

This is feasible incrementally: retain `StrategySpec` and `run_event_backtest()` for supported SMA rules and next-open execution; add a versioned registered batch adapter and a pure metric reducer over the verified equity/trade trace. The adapter must respect new admission and access controls. Existing `study_suite.COSTS=(0,10,25)` and policy-bound suite membership cannot silently become a general strategy search API. Register a new policy/adapter instead of rewriting old artifacts or replaying consumed D008 controllers.

## Cost interpretation and benchmarks

The existing 0/10/25-basis-point cases can immediately answer how sensitive each candidate is to a fixed charge per fill. They cannot establish realistic execution costs: `event_engine.py` explicitly excludes spread, market impact, executable-open guarantees, interest and taxes. Label zero as gross diagnostic, one nonzero case as the frozen primary scenario and the other as stress. Record fees as money and fraction of equity, turnover, traded notional, exposure, position changes and the concentration of returns in individual periods. Scenarios are correlated sensitivity checks, never independent confirmations.

Before an execution-relevant claim, calibrate a conservative cost envelope from authorized quote/execution evidence at the intended trade size and time. Include commission/regulatory charges, crossing spread and slippage/impact without double counting. Daily OHLC alone cannot identify these components. The minimum next implementation can report break-even *assumed* per-fill cost and the exact tested scenarios, with no claim that the market supplies those fills. The historical evidence that costs can erase higher-turnover anomalies supports this priority, not a universal basis-point estimate. [Novy-Marx and Velikov](https://www.nber.org/papers/w20721).

Benchmark and strategy must share capital, timestamps, action treatment, cash-return assumption and terminal marking. Existing accounting retains dividends as cash and does not reinvest them while continuously held; it must not be labeled a standard reinvested-total-return index. Idle-cash interest is currently zero, and risk-adjusted reporting must say so. Use the identical admitted security's buy-and-hold first. Exposure-matched or investable cash benchmarks can be secondary, frozen comparisons; do not switch to whichever one the strategy beats.

## Metrics, uncertainty and adequacy

Compute actual elapsed-time CAGR from initial/final net wealth with a specified day-count convention; first/last session labels alone do not establish intraday elapsed time. Report duration and decline to annualize tiny samples. Report maximum drawdown from the full wealth trace, including starting capital, and both block and continuous results. Do not annualize a daily Sharpe with an unexplained square-root multiplier. Serial dependence changes the appropriate interpretation and uncertainty. [Lo](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=377260).

For the later formal campaign, recommend one primary estimand: mean daily **net strategy-minus-benchmark return** under the primary cost assumption, with a frozen positive worthwhile-effect threshold. This is an arithmetic return-difference objective; it is not CAGR or causal alpha. Report CAGR and Sharpe differences separately. A risk-reduction objective requires its own specification before results, not a switch after growth disappoints.

Implement dependence-aware uncertainty as a separately tested reducer, initially a fully specified HAC long-run variance estimate for the paired return differences. Fix the kernel, lag-selection rule, centering, variance divisor, finite-sample qualification and degenerate-input handling. Validate against independent arithmetic examples and null/alternative simulations with autocorrelation, heteroskedasticity and heavy tails. A block-bootstrap sensitivity may follow; choosing its block length after seeing favorable answers is another search. Neither method repairs nonstationarity or model-prior leakage. No statistical certification should be produced merely because the reducer returns a number.

There is no universal sufficient count of days or trades. Freeze a sample plan using development-only variance/dependence estimates and a stated alternative **strictly above** the worthwhile-effect threshold; report planned power and assumptions. The old short event pilot is accounting evidence, not adequate trading-performance evidence. Include duration, number of exposure transitions, effective dependence horizon, uncertainty width and subperiod concentration in the adequacy record. Zero variance, a candidate with no meaningful changes in exposure, invalid calendar/action coverage, or a sample too weak to distinguish the declared effect must remain inconclusive. Do not extend the final horizon after looking until significance appears.

## Selection, final evaluation and verdicts

Retain a complete application search roster; separately disclose that model training and outside human searches are not fully observable. Deflated Sharpe is a possible supplementary diagnostic only with its assumptions and a defensible search count. It is not a probability that the strategy is true, and it cannot repair a leaked holdout. [Bailey and López de Prado](https://davidhbailey.com/dhbpapers/deflated-sharpe.pdf).

Before one final champion is frozen, review the exact estimand, cost basis, horizon, uncertainty method and campaign error allocation. The D008 adviser sequence `alpha_j=0.05/2^j` is a simple candidate allocation, not an accepted guarantee; approximate tests need calibration and the ledger must not reset on renaming. One champion and one primary test avoid choosing the most favorable final result. Consume the opportunity before final observation access; preserve failures and diagnostic reruns. Release no interim performance to selectors.

Keep separate output fields rather than one promotional verdict:

| Field | Meaning |
| --- | --- |
| Integrity | Valid calculation, invalid inputs/lineage, or exposed assessment. |
| Cost finding | Survives the declared assumptions, fails the declared cost criterion, or cost realism unverified. |
| Benchmark finding | Above/below comparator on each declared metric; mixed growth/risk results stay mixed. |
| Statistical finding | Criterion met under stated assumptions, evidence against the worthwhile effect, or inconclusive. Failure to reject is not proof of no edge. |
| Readiness | Development only, prospective evidence pending, or separately reviewed operational status. No live authorization follows. |

The immediate deliverable should be a reproducible table of actual net historical results with these limits, not another claimed successful strategy. The final deliverable requires observations that were genuinely reserved, independent numerical checks, and distinct criticism/quality/scope review.

## Concrete implementation gaps

- `research.Performance` and `event_engine` have wealth, return, drawdown, trades and fees but no CAGR, Sharpe, uncertainty or block reducer.
- `StrategySpec` expresses one SMA long/cash family. Volatility sizing, cross-asset allocation, shorts, borrowing and rate-bearing cash are unsupported and should not be smuggled into labels.
- `research_comparison.evaluate()` checks three frozen accounting predicates, not strategy efficacy or benchmark inference.
- `study_suite` permits only the exact three-cost, common-specification D007 roster. New candidate registration needs a new explicit scope.
- `evaluation_registry.reserve()` creates preparation state only; `protected_acquire()` refuses. Protected performance claims remain unavailable until the separate evaluator is implemented and witnessed.

No calculation or test result is claimed by this report. The primary-source search found the cited papers' abstracts/full text; a direct NBER/SSRN fetch returned access errors and the Ledoit-Wolf repository denied access, so no inaccessible paper detail is relied on here.

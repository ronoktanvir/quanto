# D011 independent perspective: a small strategy queue

Recommendation: begin with one slow trend specification, evaluate a separately counted volatility overlay, and reserve one short-horizon reversal challenger for a later admission check. The supplied quant-theory sheet is a topic map. It supplies neither a complete statistical method nor evidence that these particular implementations work. This report recommends research; it does not admit data, freeze a private strategy, authorize an experiment, or report a performance result.

## Scope and inspected evidence

Prepared November 4, 2026 by the independently briefed `queue_hypotheses` agent. Inspected the root checkout at `60fe9299ab44cbd34962944fcc8039f1376435da`, the project instructions, CONTEXT, STATUS, ROADMAP, DECISIONS, HANDOFF, D008 policy, and the public research/event-engine interfaces. The report is delivered in the separate queue worktree based on `94e0df5a79234f3423cabe137377efb796fe9cd0`; the unfinished D010 work is preserved in the original checkout.

Relevant inspected identities:

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/research.py` | `186e6a9aa95a484e94d71cbd71f276c053b923e96e030fa6eea0adcfc53223ca` |
| `src/quanto/event_engine.py` | `cb1a61985ebb08089eab50d00d1e78f09a83fdea6754587af7e871e177175ffc` |
| `docs/D008_POLICY.md` | `91bd473d6972355c8cba447fff7b1e66e9b77bddf9712097ebd0f95bafc07aa7` |

No private data, credentials, runtime stores, protected observations, or actual result values were inspected. No real research, paid model call, trade, or source-code change was executed. This is a design perspective, not independent quality certification. Primary-author and publisher material below was searched; several direct publisher/PDF opens failed, so the report does not claim a full replication-method audit of every paper.

## Candidate priority and what each test can establish

| Priority | Candidate family | Proposed mechanism and comparison | Main reason to reject or defer |
| --- | --- | --- | --- |
| First | Slow moving-average trend, long or cash | Test whether delayed response to a sustained price trend improves the declared net outcome relative to holding the same admitted instrument. Reuse the existing strict-crossing and next-open semantics where possible. | Whipsaw costs, missed rebounds, or a nominal improvement caused only by reduced equity exposure. |
| Second | The same trend with an unlevered volatility overlay | Hold the signal fixed and test whether lagged risk sizing improves the declared risk/return objective after its additional turnover. Compare directly with the unsized trend as well as the benchmark. | Full-sample scaling, unstable estimates, cash drag, or extra turnover removes the improvement. Partial rebalancing requires new reviewed accounting; it is not supported by the current all-in/all-out engine. |
| Challenger | Short-horizon reversal, long or cash | Test whether a predefined negative price move predicts a subsequent recovery that remains available at a later executable price. | Apparent profits disappear between the signal close and next open, depend on illiquid names, or fail cost stress. A new signal/exit policy is required. |

Published trend evidence justifies the first hypothesis, with a substantial transfer limitation. Moskowitz, Ooi and Pedersen studied 58 futures/forward instruments and a long/short time-series momentum construction. Their evidence does not establish profitability for long-only US ETFs, a moving-average rule, or this provider's historical bars. [Author-associated original-paper description and dataset](https://www.aqr.com/Insights/Datasets/Time-Series-Momentum-Original-Paper-Data).

Faber's author-maintained description supports moving-average timing as a simple candidate family. It also explicitly distinguishes a monthly update convention from daily trading and emphasizes dividends/income. A daily-bars adaptation with next-open fills is a different test; we must not describe it as an exact replication. [Author's model description](https://mebfaber.com/timing-model/).

Volatility management belongs in the queue as a contested sizing hypothesis. Moreira and Muir report improved performance for multiple factor portfolios. Cederburg and coauthors subsequently find that volatility-managed portfolios do not systematically outperform unmanaged counterparts in direct comparisons and emphasize poor implementable out-of-sample performance. This disagreement favors a prespecified paired test, not an assumption that risk scaling must help. [Moreira–Muir](https://www.nber.org/papers/w22208) · [Cederburg and coauthors](https://www.sciencedirect.com/science/article/pii/S0304405X2030132X).

Reversal is lower priority because its mechanism and implementation costs are tightly connected. De Groot, Huij and Zhou report that restricting their equity universe and reducing turnover changes net reversal results. That is evidence for testing the cost sensitivity, not evidence that a long-only ETF dip-buying adaptation inherits the result. [Authors' accepted-paper repository](https://repub.eur.nl/pub/25718/). More generally, Novy-Marx and Velikov find that transaction costs reduce anomaly profitability and that higher-turnover strategies are especially vulnerable. [Original working paper](https://www.nber.org/papers/w20721.pdf).

## Finite search and execution semantics

The initial campaign should admit at most three candidate specifications: one trend, one paired volatility overlay, and one reversal challenger. An unsupported candidate stays deferred; it does not earn an arbitrary substitute. A fixed three-case cost sensitivity would produce at most nine candidate calculations per declared instrument/window configuration, not nine independent discoveries. Benchmarks and mandatory diagnostic calculations are separately registered. Additional instruments, windows, parameter choices, execution conventions, and signal variants all expand the search record; the three-template limit must not conceal a large grid beneath it.

Private parameters, instrument identities, dates, objective thresholds, and source-specific cost assumptions must be frozen in an ignored campaign specification before observing the relevant outcomes. The public queue records only method families and lifecycle state. Choose the instrument set by a documented ex ante eligibility rule rather than by the prettiest historical chart. A fixed set of today's surviving ETFs supports a claim about that set only; it does not establish a survivorship-free market-wide strategy.

For every candidate, information available through the completed session forms a target for the following exchange session. There is no same-close fill. The next open is a reference-price execution assumption with explicit spread/slippage charges, not proof that an actual order could obtain the bar's opening print. Missing sessions or unavailable executions produce a declared refusal/handling outcome; they are not silently shifted to the next convenient bar.

The trend retains strict threshold comparisons and a defined equality rule. The overlay may use only lagged volatility observations, a prespecified estimator, a no-leverage cap, and frozen behavior for zero/invalid estimates. Any normalization constant must be fixed from development data, never calibrated with final-window volatility. The reversal candidate needs explicit entry, exit, maximum holding period, overlapping-signal handling, and position limits before launch. Those exact selections remain private and are not supplied by this review.

## Data, costs, and rejection conditions

Require admitted raw prices, the exchange calendar, stable instrument identity, split/distribution records, complete pagination/coverage, and an explicit signal adjustment convention. Keep the price basis used for signals consistent through time; adding cash dividends to an already total-return-adjusted tradable price series can double count income. ETF history introduces distribution types and closure events that the existing common-stock pilot may not support. Reject unsupported accounting rather than borrowing a superficially similar rule.

Charge turnover on actual traded notional, including initial purchases and every resize. Record whether a quoted cost is one-way or round-trip; avoid charging half-spread twice or treating zero commission as zero cost. Use a documented base cost and conservative stress cases, retaining the same strategy decisions across cost comparisons unless the frozen policy explicitly makes decisions cost-aware. Show breakeven cost as a descriptive sensitivity. Without suitable quote/fill evidence, fixed-basis-point assumptions support conditional results only, not a verified retail execution claim.

Benchmark and candidate must share valuation conventions, fee treatment, available cash assumptions, and scored dates. Report exposure, turnover, cash time, and concentration alongside net growth and risk-adjusted return. A lower drawdown caused by spending more time in cash is a potential tradeoff, not automatically forecasting skill. Personal tax effects remain outside a pre-tax study unless a separately specified tax model exists.

Fail the experiment as invalid for timing leakage, unsupported corporate actions, missing coverage, unexplained discrepancies with the independent arithmetic oracle, or a breached evaluation boundary. Reject the stated net-outperformance hypothesis when its prespecified criteria fail; keep an inconclusive category for inadequate precision or power. A near-zero Sharpe, short quiet sample, or a favorable point estimate alone cannot decide efficacy. Reviewers must not move costs, horizons, or success criteria after seeing results.

## Unseen-data boundary and next action

The existing historical pilot is explicitly development-exposed, and its control store remains legacy-unknown. No new filename, random split, fresh model context, or shifted strategy parameter makes those observations unseen. Freeze the campaign before an isolated evaluator accesses an eligible chronological interval, with exposure reconciliation and all acquisition paths covered. Use development-only checks meanwhile. Public historical results may also be present in model training, so describe the actual researcher's/evaluator's exposure controls rather than promising absolute historical ignorance.

My recommendation is to implement and verify the first trend campaign's data/accounting/evaluation path before broadening the engine. Use the overlay and reversal to test different explanations only after their additional financial semantics are admitted. The separate statistical perspective should select the estimand, multiplicity correction, sample requirement, and uncertainty method; this report does not substitute an arbitrary universal Sharpe threshold for that review. Options, order-book imbalance, HMM regime switches, and learned predictors are later work because their data and selection burden would obscure the first answer.

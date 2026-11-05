# Strategy research queue

The owner resumed Quanto on November 4, 2026 and asked for agents to test which strategies survive costs and unseen data. The supplied quant-theory sheet guides the topics. Its formulas and “pays” labels are not accepted evidence of profitability.

## Current queue

| Candidate family | Work now | Status and limit |
| --- | --- | --- |
| Slow long/cash trend | Freeze a small finite roster; compare continuous historical traces against the same admitted instrument's buy-and-hold under all declared cost cases. | Protocol, metrics and bounded process supervision implemented and reviewed. Actual launch is blocked on reviewed restart recovery; no new historical result yet. Related lookback choices are multiple trials, not independent strategies. |
| Unlevered volatility sizing | Compare sizing against its identical unsized signal; account for every rebalance and idle cash. | Deferred: the existing engine has no partial-sizing accounting. Published results conflict and do not establish this adaptation. |
| Short-horizon reversal | Test whether the effect survives delayed execution, turnover and conservative cost stress. | Deferred: new entry/exit semantics and stronger execution evidence are needed. |

Options, market making, learned predictors and regime switching remain later candidates. They require different observations and accounting. Adding complexity before the first reproducible comparison would make its failures harder to diagnose.

## What constitutes evidence

The first deliverable is a finite **historical development screen**, with the whole roster and every failure retained. Each candidate/cost trace runs continuously; chronological summaries preserve boundary wealth, holdings, cash and dividend claims. Report growth, drawdown, exposure, turnover, cost sensitivity and explicitly qualified risk measures. The cost cases are assumptions until calibrated against suitable execution evidence.

The second deliverable is an **independently protected evaluation** of a frozen candidate. Current access controls deliberately refuse protected acquisition, and legacy exposure is unresolved. A new historical split or worktree does not make old observations unseen. Complete the evaluator and scope reconciliation; use a precommitted future interval if historical non-exposure cannot be established. A future test requires elapsed market time.

The two deliverables must have separate labels. A favorable development screen is a candidate for further testing, not a validated trading strategy. A null or inconclusive answer is acceptable. No result authorizes live orders.

## Agent responsibilities

- The hypothesis adviser identifies mechanisms and bounded candidate families from primary research.
- The data adviser checks source coverage, corporate actions, instrument identity and exposure history.
- The engineer implements deterministic registered calculations and a complete attempt record.
- Independent criticism challenges timing, costs, selection and unsupported claims.
- Independent quality recomputes numerical results and tests failure behavior; separate scope review checks the owner's full objective.

The dashboard records actual assignments and observed outcomes. Its five-minute capture timestamp is not evidence that an agent or experiment progressed. Exact private instruments, dates and rule parameters belong in the ignored campaign manifest, not in public-ready documentation.

See [D011 proposal](D011_PROPOSAL.md), [hypotheses](reviews/D011-hypotheses.md), [data](reviews/D011-data.md), and [validation](reviews/D011-validation.md). The separate D010 client implementation remains preserved on `codex/registered-research-client`.

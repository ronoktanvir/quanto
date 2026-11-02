# D006 independent design advice — financial accounting

Author: Codex accounting adviser, independently briefed as `/root/d006_accounting_adviser` by the lead. Prepared 2026-11-02 UTC. This is one financial-accounting perspective, not an independent implementation certification, investment recommendation, outside-model review, or five-perspective consensus. No implementation was changed or tests executed. No `.env`, runtime ledger, private dataset, account, provider endpoint, or paid-model endpoint was read or called. Public primary-source documentation was browsed.

## Recommendation and inspected state

Implement a bounded **raw-price event-accounting engine** for one identified US security, long/cash positions, ordinary USD cash dividends, and simple forward/reverse splits. Admit a documented historical source snapshot for descriptive development research once its bounded data, calendar, identity, action coverage, permitted use, and accounting requirements pass. Keep execution prices raw; use split-neutral prices for the SMA. Do not make universal point-in-time history or complete survivorship-free coverage prerequisites for this explicitly limited research mode. Those remain limitations and later requirements for stronger conclusions. The alternative of leaving every historical dataset permanently inspection-only does not satisfy the operation's objective.

The inspected revision is `fffc374ba14e74d6cf801f409efb8cb5d4b44990` (D005 merged baseline). `research.py` currently rejects adjusted prices and every nonempty action sequence. It can calculate a raw historical series when called directly, but places responsibility for action absence on its caller; that boundary should become structured validation. `explorer.py` registers historical datasets as `inspection_only`, records exposure before refusal, and always rejects their calculation with `historical_admission_not_implemented`. It cannot yet transport historical evidence classification through a successful calculation. These are observations from code, not claims about private pilot contents.

Read artifacts and SHA-256 identities:

| Artifact | SHA-256 |
| --- | --- |
| `AGENTS.md` | `0f3a1577fb417c2434383f426895aad1fcd540feed7e81aa4a2362a4d9fefc86` |
| `docs/CONTEXT.md` | `9a6ea5a4ea276f38073c56533013feac8cbe369d7ab1167e3a181b799236698e` |
| `docs/STATUS.md` | `d7bef4193172a604ffb7895e74b5cb8e090f8f978c58233233ee4731e956cac1` |
| `docs/ROADMAP.md` | `471c604e8b5a89b952b86751f67d87618f86d78b75989c3af07ddbb81e1b17bf` |
| `docs/DECISIONS.md` | `0ad2cf27c048a21e3db048b01f3ee423a5b9353d2939f0d5fc25474577107b7b` |
| `docs/HANDOFF.md` | `5c912a96d58d8e8e825007a5b0a74758537863f7e53d8352d81cd67ed8435617` |
| `src/quanto/research.py` | `186e6a9aa95a484e94d71cbd71f276c053b923e96e030fa6eea0adcfc53223ca` |
| `src/quanto/explorer.py` | `47a9d6b6921418f997e8cdbc1f52f820a4e991dda52b7bc58704c2065c0e0808` |

These identities are the artifacts inspected for this advice. Subsequent implementation needs separate criticism, quality validation, and scope review at its own exact hashes.

## The financial distinction that controls the design

A dividend entitlement is an asset before it is spendable cash. For an ordinary cash dividend, purchases on or after the designated ex-date do not receive that dividend; an investor who buys beforehand does. The ex-date follows market rules, not a calculation from the price series. [SEC Investor.gov, ex-dividend dates](https://www.investor.gov/introduction-investing/investing-basics/glossary/ex-dividend-dates-when-are-you-entitled-stock-and).

Use that entitlement rule to recognize a fixed nominal receivable at the start of the ex-session based on shares held immediately before that session's trades. A sale at the ex-session open retains the receivable; a purchase at that open earns none. At payment, move the same amount from receivable to cash, without a second income recognition. This is a proposed research accounting convention, not a claim about GAAP financial statements or a broker's exact posting time. It prevents both omission after a sale and double-counting at payment.

Never derive historical ex-dates by applying today's settlement rule backward. FINRA's current rule was amended effective May 28, 2024, and provides separate treatment for distributions at least 25% of security value and late information. A large distribution can have its ex-date after its payable date. Use authoritative event dates and reject due-bill or other irregular entitlement structures in the first increment. The January 2024 pilot predates that rule change. [FINRA Rule 11140](https://www.finra.org/rules-guidance/rulebooks/finra-rules/11140).

A split changes share units, not wealth by itself. A two-for-one transformation doubles quantity while halving the price unit; market movements around the event remain real returns. [SEC Investor.gov, stock split](https://www.investor.gov/introduction-investing/investing-basics/glossary/stock-split). Transform holdings at the first session traded on the new basis, before using that session's raw open. Preserve a pending long/cash target through the transformation; calculate its eventual quantity in the current share unit. A record date or distribution date is not automatically the first post-split trading session.

## Proposed minimum accounting contract

### Events, coverage, and identity

Each accepted event must have a stable event identity, source artifact hash and retrieval time, instrument/share-class identity, type, status/revision, and authoritative relevant dates. A cash dividend needs USD amount per share, explicit pre/post-split share basis, ex-date, record date, and payable date. A split needs a strictly positive rational new-shares/old-shares ratio and first trading session on that basis. Preserve declared dates separately from normalized effective session. Record source announcement/publication time when available; unknown means unknown.

The admission artifact must state coverage from the first warmup bar through the last evaluation session for **all relevant action types**, not only accepted dividend/split types. It must also include payment information after evaluation for entitlements created before its end. Filtering a source to supported types would hide exactly the mergers and spinoffs that must reject the study. An event whose payment is outside the evaluation interval is valid; an earned dividend with missing payment terms is unsupported in this minimum contract.

Require explicit evidence for the bounded coverage assessment: exact receipts, complete pagination, query semantics, issuer/exchange corroboration for event terms, and a recorded reviewer conclusion. An empty response or equal raw/adjusted bars is not proof of no actions. Provider coverage and acquisition-time limitations remain visible even after admission. Alpaca documents that incomplete events may be excluded by its default quality filter, processed events may still lack fields, and publication can be delayed. Those facts justify inspecting all statuses and rejecting unresolved relevant events; the option name `complete` is not a completeness certificate. [Alpaca corporate-actions reference](https://docs.alpaca.markets/us/reference/corporateactions-1).

The action source must identify the same economic share class as the raw bars. Keep provider symbol/as-of mapping and identity evidence in the manifest. Resolve or reject ticker changes and identifier collisions; a ticker alone is insufficient. A narrow, explicitly selected continuing security supports conditional historical research, not a historical universe or survivorship-free strategy-selection claim.

### Portfolio state and daily order

Maintain cash, share quantity, event-keyed outstanding receivables, and a journal of split applications, dividend accruals, payment transfers, trades, fees, and marks. Each event is applied exactly once per portfolio. Mark daily equity as:

`equity = cash + quantity * raw_close + sum(outstanding_dividend_receivables)`

Receivables are carried at nominal USD with no discounting or default haircut. This assumption is acceptable only for the supported ordinary short-dated dividend class and must appear in the report. Dividend cancellation, revision conflicts, distress, contested payment, and non-cash consideration require an explicit new model or rejection.

For an evaluation session, perform these steps:

1. Bring prior calendar-day payment transfers into cash under the timing policy below; retain their event trace even when payment falls on a non-session day.
2. Apply a split effective for this trading session to existing quantity and the signal's price-unit history. A same-session split/dividend pair must have unambiguous ordering and share basis; reject ambiguous pairs in the first increment.
3. Accrue an ordinary dividend's ex-session receivable from pre-trade entitled quantity in its declared share basis.
4. Execute the previous completed-session target at this session's raw open using available cash only, with configured fees. No same-close fill is permitted.
5. Process any modeled payment release effective after today's open, then mark raw close plus cash and remaining receivables. Form the next-session signal after the close.

Keep payment availability conservative and reproducible: a dividend is modeled as cash at the end of its stated calendar payable date and becomes eligible for trading at the first session open strictly later than that date. If the pay date is a weekend, the following session may use it; if it is a trading day, that day's open may not. This is an explicit daily research convention. It is not a broker credit guarantee: Alpaca says actual credits can arrive after the payable date when DTC cash arrives later. Later paper-forward execution must use observed credits and reconcile them. [Alpaca daily processes and reconciliation](https://docs.alpaca.markets/us/v1.4.2/docs/daily-processes-and-reconcilations).

The current simulation also treats sale proceeds as immediately available. Preserve that as a named research assumption or add settlement accounting separately; do not label it a compliant cash-account simulation. No borrowing against dividends, taxes, withholding, cash interest, securities lending, margin, spread, impact, auction priority, or real fractional-share processing is established by this increment. Display costs and open-price assumptions as model inputs, not execution evidence.

### Signals and reinvestment

Define the initial strategy as an SMA on **split-neutral price**, with ordinary cash-dividend ex-date drops retained. When a split becomes effective, rescale prior observations still in the rolling lookback to the current share unit. Do this even during warmup and while the portfolio is flat. Do not reset the SMA, treat a split as a price crash, or rewrite past signals using future event knowledge. The execution and valuation series remain raw. A dividend-neutral or total-return SMA is a different strategy specification and needs a distinct identity and trial record.

Choose **no automatic dividend reinvestment** for the first increment. Paid dividends sit in cash while a position remains long. A later ordinary entry invests then-available cash; a receivable never funds an entry. The benchmark buys once at the same first eligible raw open with the same starting capital and fee rate, retains its split-transformed shares, and retains dividend proceeds in cash. Both finish at the same close and include unpaid earned receivables. Call it “buy-and-hold with cash dividends retained,” not a dividend-reinvested index.

This choice produces an attainable, internally comparable accounting model with no undocumented DRIP timing or fee assumption. Its tradeoff is idle-cash drag and a long state that can coexist with cash. If reinvestment is required later, specify a common policy such as purchases at the first eligible open after modeled cash release, with the same costs and eligibility for strategy and benchmark. Do not silently top up one portfolio alone. Nasdaq's published total-return index example reinvests on the ex-date, illustrating that an index convention differs from this cash-availability model. [Nasdaq International Dividend Achievers methodology](https://indexes.nasdaq.com/docs/methodology_DAT.pdf).

### Start, warmup, and end boundaries

Warmup creates signals only: both portfolios start the scored interval with initial cash, zero shares, and no inherited dividend claims. A dividend ex-date in warmup creates no receivable even if its payment is in evaluation. A dividend ex-date on the first evaluation session creates no entitlement for the first-open buyer. A split in warmup still changes the lookback's share units; a split on the first evaluation session changes the new open's unit and any applicable signal history, not nonexistent inherited holdings.

Carry each accrual's dollar amount unchanged through later splits. A split after an ex-date does not multiply an already-fixed receivable. An event after the final evaluation session must not alter earlier signals, holdings, or prices. At period end, report marked shares, cash, outstanding receivables, total equity and fees separately. No forced liquidation, exit fee, collection after the window, or projected return is implied. A payable date after the window does not erase an earned claim. Unknown, disputed, or cancelled claims are not silently valued at par.

## Raw events versus an adjusted-price research proxy

| Criterion | Raw prices plus events | Provider-adjusted research proxy |
| --- | --- | --- |
| Accounting fidelity | Separates actual share units, entitlements, receivables and modeled cash release; compatible with later reconciliation | Can describe a normalized return/signal series but does not establish cash availability, event entitlements, or share quantities |
| Cost and effort | More implementation and bounded action review; no subscription is inherently required | Fewer initial calculations, but validation of adjustment definitions, versions and coverage is still required |
| Reproducibility | Freeze raw bytes, action bytes, normalization decisions and engine/spec hashes | Freeze exact adjusted bytes and source semantics; later retrieval may produce a different historical series |
| Main failure mode | Missing/misordered/misidentified events, wrong share basis, premature cash, double income | Hidden treatment of reinvestment, future restatements, unsupported actions and mistaken adjusted fills |

Prefer raw-event accounting as the primary attainable path. Alpaca's bar reference says `all` includes split, cash-dividend, and spinoff adjustments. Therefore the acquired `all` series is not merely a harmless split normalization; feeding it to an engine that also books events can double-count value, and its inclusion of spinoffs exceeds the proposed one-security contract. [Alpaca historical bars](https://docs.alpaca.markets/us/reference/stockbars).

A separate adjusted-series proxy can be useful as a diagnostic or an expressly different exploratory method, once its actual adjustment formula and reinvestment assumptions are documented. The inspected public bar reference does not establish that the provider's `all` ratios equal this proposed raw-event portfolio's returns. Do not demand exact equality, infer accounting correctness from equality, treat adjusted opens as executable raw prices, or use cash dividends twice. Future common multiplicative scaling can leave an SMA inequality unchanged, but that algebra is not a general defense of opaque cash-dividend/spinoff adjustments or revised event data.

## Decisive acceptance criteria and reference fixtures

These are proposed checks, not executed results. Synthetic fixtures establish software accounting; primary-source event examples establish source semantics; acquired historical results establish only the stated historical evidence kind.

| Fixture or check | Required result |
| --- | --- |
| Pure two-for-one split, 10 shares at 100 becoming 20 at 50 | Equity stays 1,000 with zero fees and unchanged cash; split alone generates no return or fee |
| One-for-four reverse split with exact rational units | Quantity divides by four and price unit multiplies by four; no rounding windfall; broker cash-in-lieu remains outside the fractional research assumption |
| Split in the SMA window while flat, long, or warming up | Same economic trend and pending target survive the unit change; past emitted signals remain unchanged |
| 10 shares, ordinary dividend 1, pre-ex close 100, ex close 99, no other moves | Market value 990 plus receivable 10 equals equity 1,000; no assumed law that actual market prices must drop by exactly 1 |
| Sell all 10 at ex-open 99 before payment | Cash 990 plus receivable 10 persists; payment later transfers 10 with zero payment-day return absent other moves |
| Buy 10 at ex-open 99 | No dividend claim from that purchase |
| Pay date after evaluation end | Ending equity includes the 10 receivable; ending spendable cash excludes it; later payment does not alter frozen earlier marks |
| Pay date on session/weekend, payment already accrued | Eligible only at next session open strictly after the stated date; payment transfer preserves total equity |
| Ex-date before start, in warmup, or first evaluation day | No inherited claim for an initially cash portfolio; warmup does not generate P&L |
| Split between ex-date and pay date | Accrued nominal dollar receivable remains fixed; later split does not multiply it |
| Same-day split plus dividend, duplicate/revised event, currency conflict, missing date | Apply only with an explicit unambiguous normalized contract; otherwise record invalid result and fixed rejection reason |
| Unsupported spinoff, merger, delisting/worthless-removal, rights or irregular due bill | Reject the entire affected study before reported performance, including benchmark, rather than skipping the event or inventing a sale |
| Prefix invariance | Appending future bars/actions cannot change already-reported signals, trades or marks, except a separately identified corrected-source rerun with a new input identity |
| No-action series | Existing arithmetic and fees remain equivalent under the new raw-event engine within documented numerical tolerances |
| Comparator parity | Same first eligible open, final close, cash timing, action rules and fee rate; benchmark differences arise from the frozen holding rule |
| End-to-end admitted historical submission | Record historical evidence kind, exact action/data/code identities, rejection/attempt history and whole-range development exposure; do not retain hard-coded synthetic labels |

Use NVIDIA's 2024 split/dividend FAQ as a primary-source normalization reference: it distinguishes distribution after June 7 close, first post-split trading on June 10, ex-dividend June 11, and payment June 28 at 0.01 per post-split share. The dates and amount can validate event normalization without inventing market-price outcomes. The same issuer FAQ warns that fractional-share handling depends on the broker. [NVIDIA June 2024 stock-split FAQ](https://s201.q4cdn.com/141608511/files/doc_downloads/2024/06/nvidia-2024-stock-split_faq_investors.pdf).

Apple provides an additional date-semantics trap: its FAQ calls August 28, 2020 the split date, while its announcement says trading on the four-for-one basis begins August 31. A normalizer must preserve both meanings rather than choose whichever date field looks convenient. [Apple FAQ](https://investor.apple.com/faq/default.aspx), [Apple July 2020 results announcement](https://www.apple.com/ae/newsroom/2020/07/apple-reports-third-quarter-results/). These source examples are not acquired price fixtures or evidence that a backtest already passed.

## Objections, unresolved limits, and attainable next increment

**A fully realistic account is not yet attainable from daily bars alone.** The recommended minimum is a descriptive research model with named timing, fractional-share, settlement, fee and payment assumptions. It must not claim exact auction fills, actual broker credits, information available to a historical trader, or feasible capacity. The bar's daily timestamp is a session label, not proof of completed-data availability before an executable next open. Protected final evaluation and prospective paper reconciliation remain separate work.

**Missing actions are more dangerous than imperfect arithmetic.** A correct event engine with an incomplete action set still produces false returns. Admit only the bounded corpus whose event coverage and unresolved cases have explicit evidence and review; lack of universal coverage is a visible limitation, while a known relevant unsupported event or missing term is a rejection. Coverage confidence should never be relabeled proof. New source corrections require new artifact identities and a recorded rerun; they do not repair previous study exposure.

**Rejecting only periods when a position is held is insufficient for this first contract.** Unsupported actions can contaminate warmup, signals, the benchmark, identity continuity and the evaluation window itself. Reject relevant unsupported actions throughout warmup/evaluation until their effects are implemented. Do not remove the security from a historical universe and describe the remainder as unbiased; no such universe is built here.

The next coherent increment should freeze this narrow accounting specification; implement split units, ordinary dividend receivables and payment transfers; add transparent report fields and rejection reasons; verify the hand-computable fixtures; and replace the unconditional historical gate with a versioned, evidence-backed admission record. The lead can then obtain bounded action and calendar receipts through separately reviewed fixed GET routes or explicit local primary-source ingestion, corroborate the selected development interval, and run a registered historical study with the benchmark and all limitations shown. This adviser made no such acquisition and cannot certify the existing pilot as eligible.

Completion of that increment means a successful reproducible **historical research calculation**, not a validated strategy or the completed private operation. If action access is unavailable, raw-event engine implementation and its independent checks can proceed, while actual historical admission remains specifically pending source evidence. An opaque adjusted-price shortcut does not satisfy that pending requirement.

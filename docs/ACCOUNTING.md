# D006 raw-event accounting contract

`quanto.event_engine.run_event_backtest` calculates a single-security long/cash
path from validated raw daily bars, a `StrategySpec`, and canonical corporate
actions. It does not establish source rights, event coverage, source accuracy,
instrument continuity, historical admission, or execution feasibility. The
registered admission workflow must establish its own evidence-bound conditions
before calling this pure function with historical data. The existing synthetic
engine in `research.py` remains unchanged.

## Inputs and numerical meaning

The first `lookback` supplied sessions are warmup only. Both portfolios start the
following session with `starting_cash`, zero shares and no receivables. Callers
must select exactly the declared preceding warmup and evaluation sessions;
supplying an expected calendar checks equality but does not certify that calendar.
No missing session, price or action date is filled or shifted.

Prices arrive through the existing `Bar`, whose numeric inputs are Python
integers/floats. Conversion uses `str(validated_normalized_price)`. A provider
decimal converted to a float earlier can already have lost source precision;
neither Fraction nor Decimal reconstructs that lost precision. This engine
claims exact signal comparisons over those normalized decimal representations,
not arbitrary precision over original provider text. Canonical action rates
remain decimal strings and never pass through floats.
Each event rate is limited to 100 characters and an absolute adjusted decimal
exponent of 100 before conversion to Fraction. These bounds match admission and
prevent unbounded integer allocation through direct pure-engine calls.

Signal arithmetic uses exact `Fraction` values, including split ratios and
thresholds. Portfolio operations use a new local Decimal context with precision
34, ROUND_HALF_EVEN, exponent bounds -999999 through 999999, and traps for invalid
operation, division by zero, overflow and underflow. Caller precision, rounding
and traps do not alter this context. `policy_identity()` reads numerical settings
from the context actually used and describes the operation order. The registered
workflow must bind this policy and the loaded engine/helper identities.

Each entry quantity is `cash / (raw_open * (1 + cost_bps / 10000))`.
Gross value is `quantity * raw_open`; fee is `gross * fee_rate`. The buy allocates
all available cash and sets the cash balance to zero. Rounded Decimal products
can leave a tiny signed difference between cash and gross-plus-fee. Each trade
therefore discloses `rounding_residual = cash_before - (gross + fee)`; it is an
explicit precision artifact, not a fee or broker cash balance. Quantities,
prices, money and returns in reports are decimal strings, possibly using
scientific notation. There is no cent rounding. Split quantities use the stated
left-to-right Decimal operations `quantity * new_rate / old_rate`; no claim of
exact rational portfolio quantities is made.

## Supported event contracts

A split contains exactly `kind="split"`, a nonempty `event_id`, ISO
`effective_date`, and positive decimal-string `new_rate` and `old_rate`.
The ratio is new shares divided by old shares. Forward and reverse splits retain
fractional quantities; no cash-in-lieu or actual broker fractional processing is
modeled. Admission must establish the first session traded in the new units.

An ordinary cash dividend contains exactly `kind="cash_dividend"`, a nonempty
`event_id`, ISO `ex_date` and `payable_date`, a positive decimal-string `rate`,
`currency="USD"`, and `share_basis="ex_date_shares"`. Admission must establish
the rate per share outstanding at the ex-date boundary from preserved evidence;
the engine cannot verify an issuer judgment from a string. A payable date before
the ex-date rejects, because due-bill and irregular distributions are unsupported.
Same-day ordinary ex-date and payable-date are mechanically supported.

Duplicate event IDs, identical economic events with different IDs, and multiple
actions on the same relevant session reject. This includes simultaneous split
and dividend ex-date, multiple splits, or multiple separately identified cash
dividends; this increment does not guess whether they are distinct economic
events. Exact provider duplicates may be collapsed upstream only while retaining
all source occurrences. Unknown kinds, extra/missing fields, invalid dates,
unknown currency, unresolved share basis and nonpositive rates reject.

Valid effective/ex dates before the first supplied warmup session or after the
final score session do not affect accounting or signals. Relevant dates inside
that range must exactly match a supplied session. Payable dates may be weekends
or after the final score session. Malformed or unsupported inputs reject even
outside the selected range; source-level relevance judgments belong to admission.

## Session sequence and entitlement

Each scored session applies these operations in order to both portfolios:

1. Release existing claims whose payable date is strictly before the session
   into cash. A weekend payment is first observed by the calculation at the next
   supplied session, with the original payable date preserved in its flow.
2. Apply the effective split to existing shares and to previous closes in the
   rolling signal window. Splits also rebase signal history during warmup.
3. Accrue ex-date dividends on shares held before the session's trade. An ex-date
   seller retains this claim; an ex-date buyer receives none.
4. Fill the prior completed-session target at this session's raw open. Buying
   uses available cash only. Selling credits gross less fees **in addition to**
   existing cash, and preserves outstanding dividend claims.
5. Release claims payable on this session at its modeled end. This cash cannot
   fund the same session's open.
6. Mark `cash + quantity * raw_close + nominal_unpaid_claims`, then form the next
   target from the completed close.

An accrued dividend is a fixed nominal USD claim. A later split never scales
it, and payment only moves its value into cash. Claims payable beyond the end
remain in ending equity and are separately disclosed; the engine neither
collects them beyond the window nor discounts them. Warmup dividends create no
inherited entitlement, regardless of when their payment falls.

## Signals, benchmark and reporting

The SMA includes the current and preceding `lookback - 1` closes, rebased only
for splits already effective at the signal date. Above the entry level targets
long; below the exit level targets cash; equality preserves current holdings.
Initial holdings are zero, so an initial exact tie remains cash. The frozen
D006 pilot uses zero thresholds. A start-above-SMA state can buy at the first
scored open. Cash-dividend price drops remain in the signal; this is not a
dividend-neutral or total-return signal. Later bars/actions cannot rewrite an
earlier signal or mark. Full input hashes change when inputs change, even where
earlier numerical outputs remain identical.

No automatic dividend reinvestment occurs while the strategy holds shares.
Dividend cash may fund a later ordinary entry after an exit. The benchmark buys
once at the same first eligible open, applies the same fees and event treatment,
and never redeploys dividend cash. Both mark at the same final close without a
forced sale or invented exit fee.

Each portfolio reports initial and ending equity/cash/shares/claims, daily marks
and next targets, trades, fees, total return, maximum drawdown, and event flows.
Drawdown includes starting cash as the initial peak; the first daily return
uses starting cash as denominator, including the first entry fee. Flows record
split share changes, ex-date entitled quantities and claims, and payment phase.

This is a theoretical research model. Sale proceeds are immediately available;
there is no cash-account settlement-compliance claim. The model omits taxes,
withholding, cash interest, lending, margin, spread, impact and actual broker
credit timing. Synthetic fixtures test software accounting and refusal behavior,
not investment performance. A historical label records the input evidence kind
and does not confer admission or establish a deployable strategy.

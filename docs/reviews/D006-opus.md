# D006 actual outside-model critiques

Both requests used the exact requested Claude Opus 5.5 through the existing shared reservation ledger. They reviewed design material, not implementation or private market data. The first response hit its output limit and remains incomplete. A separate, deliberately requested focused follow-up completed. Neither report certifies tests, data rights or investment results. Only visible response text is reproduced below.

## Incomplete review — opus-294bc96767dd4e5385e3b0d07f5249e9

Provider response: `msg_011CgdSGUJNfar3XtfjfQcBX`. Model: `claude-opus-5-5`. Observed: `2026-11-02T04:04:06.311256+00:00`. Packet SHA-256: `e3275fc182e7823c224460da03769a5eb496b7dc4dbb8e3d0b811ce4e4ecffc7`. Usage: 33,815 input and 8,192 output tokens. Calculated cost: $0.299100. Stop reason: `max_tokens`.

# D006 Adversarial Review: NVDA Split/Dividend Pilot and Admission Design

**Basis and limits.** I reviewed the proposal text and five adviser reports as supplied. I executed no code and inspected no repository, provider response or private data. I verified no hashes. Session counts below come from the standard NYSE holiday schedule and must be rechecked against the preserved Alpaca calendar. Nothing here certifies profitability, data correctness or legal permission.

**Overall.** The direction is sound: raw-price event accounting, an evidence-bound admission record, scoped "no observed event" semantics, and limitations that are not hidden behind disclaimers. The main risks are not conceptual. Several rules are still loose enough that the lead would have to choose them **after** seeing the acquired data. That would undercut the "frozen before acquisition" claim, and a few rules could quietly turn into permanent blockers.

---

## Blocking findings (resolve before any new acquisition)

### B1. Pilot warmup and signal specification are internally inconsistent and underspecified (confirmed)

**Evidence: session count.** The acquisition starts 2024-05-01. The scored window starts 2024-06-03 with "exactly 20 preceding warmup sessions."
- May 2024 has 23 weekdays. Memorial Day (May 27) removes one, leaving **22 sessions** before June 3.
- So either two acquired sessions are silently unused, or the warmup is not 20.

**Evidence: strict-cross semantics.** A strict cross needs SMA values at both t and t−1.
- With only 20 warmup closes, SMA20 first exists at the May 31 close.
- The earliest possible cross is then the June 3 close, so the earliest strategy fill is June 4.
- With 22 closes, a June 3 fill is possible.

**Further unspecified items:**
- whether the SMA includes the current close;
- tie handling at the zero threshold;
- whether a flat portfolio enters when price is already above the SMA at the start without a fresh cross;
- the fill-quantity formula under fees, i.e. `cash/(open·(1+fee))` versus fee taken from proceeds.

Each is a degree of freedom that could be resolved after data inspection.

**Check.** Write the specification as executable pseudocode. Hash it. Run it on two hand-built synthetic series, one with a start-above-SMA case and one with an exact tie, before acquisition.

**Correction.**
- Freeze the warmup count consistently with the acquisition start, and state the earliest possible strategy fill date.
- Define the cross formula, ties, initial-

## Completed review — opus-7c2f4e320a03437f8ffbae7cbfd4b594

Provider response: `msg_011CgdSeyjZJqoi19M1oKeg5`. Model: `claude-opus-5-5`. Observed: `2026-11-02T04:08:37.024559+00:00`. Packet SHA-256: `64f1e2324b3aa8a6717e4c67d8624e22de844701ff55cd787985c749f5663b0c`. Usage: 3,488 input and 5,104 output tokens. Calculated cost: $0.116032. Stop reason: `end_turn`.

# D006 Focused Design Critique: NVDA Split/Dividend Pilot

**Scope:** This critique covers design only. I executed no code, ran no tests, and inspected no data. It does not certify implementation, data adequacy, or profitability. The prior review (opus-294bc967…) remains INCOMPLETE and is not superseded as approval.

## Blocking findings (resolve before any actual calculation)

**B-A1. The dividend rate basis around the split is undefined (confirmed design gap).**
- **Evidence:**
  - The split is effective June 10 and the ex-date is June 11, so the "pretrade quantity" at the ex-session is the post-split share count.
  - The source adviser warns the ordinary rate and split basis need issuer reconciliation. The issuer declared the dividend in a way that ties the per-share amount to the split.
  - The design stores "decimal normalized rate strings" but does not say which share basis the rate applies to.
  - A pre-split-basis rate times the post-split quantity overstates the claim tenfold.
- **Check:** Add a synthetic fixture with a 10:1 split at session S and a dividend ex at S+1, under two variants: a provider rate on the pre-split basis and one on the post-split basis. Expected result: exactly one variant is admitted, or both reject.
- **Correction:**
  - Pre-register the rule: the claim equals the rate expressed per share outstanding at the ex/record boundary, times the pretrade quantity.
  - Admission must record the provider-reported rate, the issuer-reported rate, the stated basis, and any attributed conversion judgment.
  - If the basis cannot be established from issuer bytes, reject. Never infer the basis from price behaviour.

**B-A2. Intra-open event ordering is implied but not specified (confirmed ambiguity).**
- **Evidence:** Several components act at the same open: the split transform at the effective open, dividend accrual "before trades", cash release "first open strictly after pay date", and the fill at the open. Their relative order is never fixed. Different orders change the sell quantity, the claim quantity, and the buy cash.
- **Correction:** Freeze this order in the spec hash:
  1. Release receivables whose pay date is strictly before this session into tradable cash.
  2. Apply splits effective this session to holdings.
  3. Accrue ordinary dividends with ex-date equal to this session on the post-step-2 pretrade quantity.
  4. Execute the signal fill at the raw open.
  5. Mark at the raw close.

  Apply the identical sequence to the benchmark. Add a fixture in which all four events coincide, and a fixture with a Friday pay date followed by a Monday open.

**B-A3. Arithmetic and tie semantics are not exact (confirmed ambiguity).**
- **Evidence:**
  - "Exact tie preserves state" depends on representation.
  - Rebasing by a non-integer ratio (e.g. 3:2) produces non-terminating decimals.
  - Buy quantity cash/[open·(1+f)] is also non-terminating.
  - Replay determinism therefore depends on an unstated precision and rounding context.
- **Correction:**
  - Evaluate the signal comparison in exact rationals, e.g. 20·close[t]·Π(ratios) versus Σ(close·applicable ratios), with no rounding before comparison.
  - Freeze the decimal context (precision, rounding mode) for quantities and cash, and include it in the engine hash.
  - Add tie fixtures where floating point and rational arithmetic would disagree.

**B-A4. Terminal valuation and the benchmark end state are unspecified (confirmed gap).**
- **Evidence:**
  - Costs are 0/10/25 bps.
  - The benchmark pays an entry cost only, unless it is liquidated.
  - The strategy may end long or flat.
  - Mark-only versus terminal liquidation changes the relative result asymmetrically.
- **Correction:**
  - Pre-register one policy applied identically to both legs. Recommended: mark at the July 12 raw close, with no terminal liquidation, and unpaid claims counted at nominal value.
  - Define the starting equity point as 10,000 cash before the June 3 open fill.
  - Specify the reported metrics (ending equity, number of trades, total fees) before acquisition.

**B-AD1. Relevance and classification criteria must be frozen before acquisition (research-integrity blocker).**
- **Evidence:**
  - Rejection depends on whether "economic relevance cannot be excluded" and on a "scoped coverage assessment".
  - The process envelope (2016 to the acquisition date) will return many out-of-window records.
  - Without a pre-written relevance predicate, these judgments are made after seeing the data.
- **Correction:** Freeze a predicate in the spec. An action is relevant if either:
  - its effective/ex-date falls between the first warmup session and the score end, or
  - it is an entitlement with ex-date inside that range, with any pay date.

  Then:
  - Ex-dates before warmup are irrelevant, since no inherited positions or claims exist.
  - Unknown categories and records with null dates are relevant unless the record carries fields that exclude them.

  Record the predicate version in the admission registry. Judgments outside the predicate force rejection, not discretion.

**B-AD2. The split effective-date source and the duplicate/conflict rule are undefined.**
- **Evidence:**
  - "Effective no later than t" does not say which provider field supplies the date (ex_date, process_date, or payable_date).
  - The same event may appear twice (an id change, a revision, or a cross-category listing).
- **Correction:**
  - Split effectiveness is the ex_date field. A null ex_date rejects.
  - Records are de-duplicated only if their economic terms are identical. Any conflicting duplicate (rate, ratio, or dates) rejects the study.
  - The diagnostic raw-price discontinuity check stays diagnostic. However, a gross inconsistency with the ratio (pre-registered tolerance) counts as a "known contradiction" under item 6 and rejects.

## Material but non-blocking corrections

1. **Settlement assumption.** US T+1 has been in effect since May 28, 2024, so ex-date equals record date. State that ex-date governs entitlement in the model and that the "ex seller keeps claim" rule depends on this. Add an assertion that the record and ex dates match for in-window events, or log the discrepancy.
2. **Fractional splits and cash-in-lieu.** Fractional retention after the split is already listed as an assumption. Add explicitly that cash-in-lieu is not modelled.
3. **Warmup isolation fixture.** Add a fixture showing that a split effective inside warmup rebases earlier warmup closes. It must also show that a split after t does not alter the signal at t (a "future cannot rewrite past" replay test with a truncated action list).
4. **Benchmark dividend cash.** State in the result header that the cash-retaining benchmark never redeploys dividend cash, while the strategy can on a new entry. This asymmetry is intended but affects comparison.
5. **Admission dependency drift.**
   - Bind the bars request parameters (`adjustment=raw`, `feed=sip`, the "-" as-of value, currency) into the registry hash.
   - Treat any change to the parameter-set hash as a re-admission event.
   - Keep the SIP entitlement/agreement uncertainty as a recorded limitation. It is not resolved by admission.
6. **Cost control.** The 8-page/8 MiB caps and the no-retry rule are adequate. Additionally, record a terminal "truncated at cap" status that forces rejection rather than partial admission.

## Hypotheses (unconfirmed; check during acquisition)

- The provider may report the June 2024 dividend on the pre-split basis. This is a specific instance of B-A1.
- The process-date envelope may miss actions whose process date falls outside the window but are economically relevant. The 2016 floor makes this unlikely, but completeness is not certified, as already noted.

## Conclusion (design only)

The bounded design is coherent and close to sufficient for a private engineering pilot.

Six items must be written into the frozen, hashed specification and covered by synthetic fixtures before any provider data is acquired:
- dividend-rate share basis (B-A1)
- intra-open ordering (B-A2)
- exact arithmetic and ties (B-A3)
- terminal valuation (B-A4)
- pre-registered relevance predicate (B-AD1)
- split-date field and conflict rule (B-AD2)

Until these are resolved, results would rest on post-hoc choices.

This is not approval of implementation, data, or any investment conclusion. The protected holdout, operational roles, scheduling, and paper/live work remain out of scope and outstanding.

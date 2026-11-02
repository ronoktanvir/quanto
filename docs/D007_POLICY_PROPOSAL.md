# D007 proposal: regular-way economic split entitlement

Status: proposed after acquisition, before any historical portfolio calculation. Five independent perspectives are complete. Fable and Opus terminal council assessment and lead disposition are pending. The D006 refusal remains effective until a decision and affected-code verification are recorded.

## Decision and alternatives

Permit one narrow, evidence-bound representation of a domestic common-stock integer forward split: transform economic old-unit holdings once at the first split-adjusted regular-session open. Do not create a separate stock receivable, transform at a record/payment/redemption date, or infer entitlement from price movements. Existing broker settlement, delivery availability, short/borrow, when-issued, derivative and multi-asset limitations remain.

Continuing blanket refusal would leave ordinary split accounting unavailable even where entitlement transfer is documented. A settlement ledger would answer a different, later operational question. Simply ignoring a due-bill field would erase evidence. The proposed alternative preserves it and requires a fixed economic-field authority rule with explicit source judgments and discrepancy disclosures. It is useful for retrospective economic-value research and does not establish executable inventory or buying power.

The five reports are `D007-accounting`, `D007-sources`, `D007-integrity`, `D007-operations` and `D007-scope` under `docs/reviews`. They are distinct advisory perspectives, not the future five operational research roles. Their common recommendation is conditional; implementation criticism, independent quality and final scope inspection remain separate.

## Fixed economic boundary

The new path applies only to a single identified domestic common-stock forward split of the same issuer/share class, with a fixed integer new/old ratio at least two. It applies only when a nonempty due-bill redemption field would otherwise cause refusal. The initial profile requires redemption to equal the independently established first adjusted session; that equality is a deliberately narrow guard, not evidence of economic equivalence. Other due-bill shapes remain unsupported. Existing no-due-bill split paths are unchanged.

Issuer evidence must establish record date R, after-close distribution date P, first split-adjusted regular session E, ratio, security and ordinary pre-E entitlement transfer. Require R <= P < E and E to be the next retained provider-calendar session after P. P and E must both lie within the acquired sessions for this initial profile. Preserve legal effective time separately if stated; the engine's `effective_date` means trading-unit transition, not legal effectiveness. Retain expected-versus-observed wording from sources; do not convert expected trading or issuer availability into verified broker delivery.

Evidence must establish that the old-unit regular-way share includes its attached split interest: a pre-E sale transfers that interest, a pre-E purchase obtains it, and the continuing holder receives the new units. A source-based inference from direct issuer seller treatment plus event-specific terms and applicable rules is permitted only when explicitly attributed as an inference. Missing or contradictory economic entitlement refuses.

Raw regular-way bars must correspond to old units through P close and new units from E open under the admitted source interpretation. Existing raw/SIP/asof/calendar/identity checks remain. A price discontinuity is neither entitlement proof nor a source of the ratio. No separate entitlement market, election, additional asset/cash claim or ambiguous conversion can be normalized into this event. The existing theoretical fractional-ownership assumption is retained; this is not issuer fractional issuance or cash-in-lieu modeling.

The pure engine remains unchanged unless implementation evidence identifies a genuine arithmetic defect. At E open it converts holdings q to r*q before the prior-close target trade; zero holdings stay zero. Prior closes are rebased only once the split is effective. A pre-E seller carries no orphan split claim. An E-open buyer buys already adjusted units and receives no extra award. Cash-dividend dates, share basis and receivable accounting continue to require their separate evidence; no coincident-action restriction is relaxed.

## Source authority and unresolved discrepancies

The controlling facts are event/security identity, ratio, first adjusted session, ordinary entitlement transfer and absence of an additional modeled economic asset or cash flow. Primary issuer terms govern them, with provider ex-date/ratio/identity agreement and a second event-specific primary corroboration where available. Retain the pinned provider schema and applicable rule evidence. Current source retrieval does not establish point-in-time availability.

Provider record and payable dates remain separate from issuer record and distribution dates. Preserve presence/null/empty/value distinctions for all provider date fields. Compare both dates explicitly. An unequal field must be marked `unresolved_ancillary_date_discrepancy` unless an actual source explains the difference. Do not invent a vendor error, alternate convention or reconciliation.

This explicit qualification is permitted only under the fixed economic package interpretation above: the disputed field never selects the transition, entitlement or any cash flow, and the reviewed source evidence establishes those facts despite the discrepancy. Any evidence that either interpretation indicates a different event, different trading units/boundary, detached entitlement, additional claim or unsupported market treatment causes refusal. Merely saying the engine ignores a field is insufficient. Sources and reviewer attribution must explain the economic conclusion. Arbitrary approval flags and unbound narratives cannot replace this evidence.

## Evidence and admission contract

Add an optional strictly validated `regular_way_split` object to a relevant split's primary-facts annotation; a due-bill event requires it and a new policy-revision reference. It contains:

- Profile/version, provider ID/category and canonical hash of the complete normalized source record. Preserve every source occurrence and the original raw pages.
- Exact provider date-field presence/value map, including ex, record, payable, process and due-bill redemption fields. Validate dates without rewriting them.
- Source-bound issuer identity/class, integer ratio, record/distribution/first-adjusted dates, after-close boundary, and legal timing if stated. Each fact group carries source hash, locator and attributed judgment. Required sources must be retained and rechecked; source extraction is not mechanically proven by these fields.
- Source-bound entitlement interpretation identifying regular-way economic holdings, pre-E seller/purchaser/continuing-holder treatment, and no separate modeled entitlement/cash flow. Explicitly identify direct statements versus attributed inference.
- Provider schema/rule source references and explicit discrepancy dispositions for record/payable comparisons. Derive the observed comparison mechanically; require a source-bound explanation for the economic-model treatment of each unresolved difference.

Admission retains canonical engine event plus full original-record identity, annotation, occurrences, source references and discrepancy dispositions. All extra/missing fields, unsupported profile/category, mismatched record bindings, malformed dates, unbound source judgments, changed/tombstoned bytes, contradictory economic facts, duplicate conflicts and unmatched annotations refuse. The exception does not support cash-dividend due bills, reverse/noninteger splits, ADRs, rights, stock dividends, mergers or ambiguous simultaneous events.

The new admission policy is versioned independently from D006-v1.1; old admissions do not silently acquire new meaning. Existing actual refusals remain immutable application history, subject to the documented local-owner threat model.

## Post-acquisition plan binding

The new path requires a registered, content-addressed `post_acquisition_policy_revision` artifact referenced by the admission request. It binds the accepted decision bytes and review artifacts, actual creation timestamp, predecessor plan and its successful plan-registration submission, triggering refused admission and exact retained request bytes, dataset/acquisition identities and unchanged study definition. Its registration must precede the new admission. Verify every artifact byte and original submission relationship; preserve links in the new admission dependencies and experiment fingerprint.

The previous refused request must be an actual recorded `invalid/unsupported_due_bill` admission with matching request hash, dataset and acquisition receipts. Facts may change under the new policy but the prior facts remain referenced. The predecessor plan's instrument, raw basis, acquired/scored windows, lookback, thresholds, starting cash, signal/accounting/benchmark choices and cost scenarios must match the revised frozen study. New metadata must not claim earlier registration or restore unseen status.

For this pilot, registered studies under the new admission must match that frozen evaluation range and strategy, and choose exactly one of the predeclared 0/10/25 bps scenarios. Changing these requires a new honestly recorded plan rather than silently reusing this admission. Full acquired coverage remains development-exposed, including rows outside the calculation subset. This plan binding is a retrospective pilot constraint, not protected final-access enforcement.

The old generic plan artifact format can be retained as the predecessor; validate the needed fields rather than rewriting it. A current source-bound decision document records governance; hashes do not authenticate the author or prove independent agreement. Those claims remain grounded in the actual archived reviews and orchestration record.

## Verification and private result

Use focused synthetic cases: pre-record buy/pre-E sale; post-record/pre-E buy; E-open sell after exactly one conversion; E-open entry without extra award; pre-E terminal valuation without a split claim; subsequent dividend at post-split units; unchanged prior nominal dividend claims; warmup-only conversion; no artificial signal from the unit change; future-prefix invariance. Existing exact arithmetic, source corruption, loaded-code drift, duplicate, incomplete publication and replay checks need not be copied without a changed risk.

Negative cases must include equal ex/redemption with absent entitlement evidence, wrong primary first-session/ratio/identity, substituted legal/distribution date, nonmatching redemption under this profile, missing source or record binding, unresolved controlling conflict, unsupported market/asset/ratio, ancillary discrepancy without the required interpretation, false prior-attempt/plan lineage, changed study windows/costs and source tombstones. Model target holdings are not persistent broker orders; broker GTC adjustment/cancellation mechanics remain outside this daily-open research model.

The private historical result must include an inspectable admission evidence summary, accepted action treatments, all exclusions and unresolved discrepancies, policy/plan lineage and both old refusal references, while retaining exact artifact dependencies. Do not leave the source qualification discoverable only by an unexplained hash. No private source values or data-bearing result tables enter Git or external-model packets.

After affected-code criticism and quality checks, re-admit the already acquired exact bytes, then run the three frozen scenarios. Compare each locally with the preserved independent rational oracle and verify identical registered replay artifacts/fingerprints. Actual pilot success requires this observed numerical evidence; policy adoption or fixture success is insufficient. No edge, protected holdout, general warehouse, paper/live readiness or full-operation completion follows. The broader roadmap remains required.

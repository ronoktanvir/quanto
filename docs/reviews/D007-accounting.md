# D007 independent financial-accounting perspective

## Recommendation and inspected evidence

Support a narrowly admitted **regular-way economic entitlement abstraction** for documented forward splits. The existing engine's single conversion at the first split-adjusted open can represent this abstraction without a separate stock receivable. This is conditional approval of a design, not admission of the acquired pilot, certification of provider facts, or implementation validation. A due-bill redemption date equal to the ex-date does not establish the required economics.

Independent adviser, 2026-11-02 UTC. Read AGENTS, CONTEXT, STATUS, ROADMAP, DECISIONS, HANDOFF and ACCOUNTING; inspected relevant admission and engine sections at HEAD `9c6b42e704af1f6763bc61c3932f69a91e4a1c67`. SHA256: `src/quanto/event_engine.py` = `cb1a61985ebb08089eab50d00d1e78f09a83fdea6754587af7e871e177175ffc`; `src/quanto/admission.py` = `7cd34c3244b7f87496827f933606e4000d52f4408438304ef14f27d1434cd953`; `docs/ACCOUNTING.md` = `3a45f81bbf05af25f207431a67bff890a9f6bbb96998ae034dae00e0097777cc`. No private data, runtime files or credentials were inspected; no tests or historical calculation were run. This adviser did not dispatch outside models.

## Evidence and economic mechanism

The [NVIDIA FAQ](https://s201.q4cdn.com/141608511/files/doc_downloads/2024/06/nvidia-2024-stock-split_faq_investors.pdf), questions 5, 10, 12, 15 and 18, documents a ten-for-one split, June 6 record date, distribution after June 7 close, and June 10 split-adjusted trading. It explicitly says sellers through June 7 do not retain additional shares regardless of settlement date. Broker availability may vary; NVIDIA does not issue fractional shares. It separately identifies June 11 cash-dividend ex-date, June 28 payment and $0.01 per post-split share. These issuer terms support the proposed economic interpretation but do not certify acquired provider records or brokerage delivery.

[FINRA 11140](https://www.finra.org/rules-guidance/rulebooks/finra-rules/11140) distinguishes designated ex-dates from record dates; paragraph (b)(2) normally puts distributions of at least 25% on the first business day after payment. Its current page identifies the amendment effective May 28, 2024. Do not apply current small-dividend conventions indiscriminately to earlier history or derive this event's ex-date solely from a generic settlement rule.

[FINRA 11630](https://www.finra.org/rules-guidance/rulebooks/finra-rules/11630), paragraphs (a), (c), (e) and (f), describes seller obligations, due-bills for pre-ex sales delivered too late for record-date transfer, redemption, and failures to deliver. It also describes prorating contract payment for covered stock distributions. Thus entitlement, delivery and payment timing are distinct. The proposed model deliberately abstracts from those settlement cash flows and failures; the rule does not prove they are economically irrelevant to an executable strategy.

My accounting inference is that a regular-way old-unit share before the split boundary represents one tradable economic package, including its attached distribution entitlement. The record holder may initially receive the issuer allocation while owing its delivery onward. Selling the package before ex transfers that economic entitlement; buying after record but before ex acquires it. A record-date snapshot alone therefore gives the wrong portfolio ownership.

Let `q` be economic old-unit holdings immediately before ex and `r` the new/old ratio. At ex, `q → rq`, with no additional independent asset. Before ex, raw cum-entitlement price already values the package. After ex, raw price values each new unit. This is a unit representation, not a claim that prices actually fall by exactly `1/r`; genuine overnight market returns remain in the calculation.

Adding a stock receivable at record/payment while retaining the full raw pre-ex position double counts entitlement. Retaining such a claim after a pre-ex sale creates an orphan asset. Multiplying holdings again on redemption double counts delivery. Conversely, treating a post-record buyer as ineligible loses its attached entitlement. The current engine avoids these defects if admission establishes the package semantics.

## Narrow allow/refuse predicate

For the new exception only, require all conditions below; missing or conflicting evidence retains refusal:

1. A single identified domestic common-stock forward split, same issuer and share class, with a fixed integer ratio of at least two. This deliberately narrower starting scope excludes reverse/noninteger splits, ADRs, spinoffs, elections, mixed/cash distributions and cash-in-lieu accounting. Existing unrelated supported paths need not expand.
2. Bound primary-source judgments establish the ratio, record date `R`, after-close distribution date `P`, first split-adjusted regular session `E`, and the transfer of all attached split entitlement with regular-way sales through the final pre-ex session. Require `R ≤ P < E`, with `E` the next supplied trading session after `P`. Preserve legal effective date separately when it differs from the engine's trading-unit effective date.
3. Bind the exact provider record, identity, dates, units and source occurrences. Preserve the nonempty redemption field and its source meaning. As a conservative initial boundary, require its parsed date to equal `E`, but never treat that equality as proof of conditions 1–2. Unresolved economic contradictions, uncertain field semantics affecting the modeled package, or an additional financial effect reject. Ancillary date discrepancies require the explicit treatment below. An expected trading date in a source is not proof of actual broker availability.
4. The admitted bars describe the same regular-way market: raw old units through the last pre-ex close and raw new units from `E` open. Exclude when-issued, ex-distribution parallel markets and separate trading of entitlement. No supported session may occur after distribution but before conversion under this narrow boundary. Do not infer unit consistency merely from a plausible price jump.
5. Apply the existing flat-start, long/cash, fractional theoretical ownership and next-open assumptions. Explicitly identify quantities as economic units, not legally registered, settled or broker-available inventory. No failures, delayed delivery, restricted sales or settlement-funded buying are simulated.
6. Preserve current duplicate/conflict, unsupported-action and coincident-action refusals. Independently reconcile any subsequent cash dividend's ex-date share basis. A split abstraction must not waive dividend evidence or permit same-session ambiguity.

The implementation change belongs primarily in admission, policy identity, evidence and disclosures. The inspected engine already converts existing shares before ex-open trading, changes prior signal closes only when the split becomes effective, and leaves nominal cash claims unchanged. It requires numerical changes only if the accepted scope adds independently held entitlements, separate tradable instruments, delayed economic conversion, settlement cash restrictions, or actual delivery inventory. Those would require a new accounting state model, not another permissive Boolean.

### Disagreement over ancillary dates

Provider record/payable dates need not equal issuer record/distribution dates for this economic representation to be valid. Neither record nor distribution date independently changes its holdings, signals or cash. If the same event's ratio, `E`, unit basis and complete regular-way entitlement transfer are independently corroborated, a disagreement can remain explicitly unresolved metadata. Use the primary evidence for the narrow economic predicate; retain both values, field names, source hashes and an attributed explanation of why the discrepancy does not alter any modeled entitlement. Do not invent a vendor typo, alternative date meaning, reconciliation or broker delivery outcome.

A record-date mismatch alone does not change who economically owns the package after a pre-ex trade. A payable-date mismatch also need not change economic ownership, even though actual delivery and availability can differ. But it becomes a blocking uncertainty if either interpretation could identify a different action, change `E` or raw units, detach a separately owned/tradable distribution, create an additional asset/cash flow, or undermine the explicit entitlement-transfer evidence. Chronology inconsistency is therefore a reason to inspect those consequences, not an automatic numerical date-equality test. A bare assertion that the engine ignores the field is insufficient: the review must establish its lack of economic effect within the admitted market and strategy scope. If that cannot be established, refuse.

## Hand-derived synthetic fixtures

These are proposed mathematical expectations, not executed tests or historical prices. Use `R=Thursday`, after-close `P=Friday`, `E=Monday`, `r=10`, pre-ex raw price $1,000 and ex raw price $100; force suitable prior-session signals when testing the engine. Zero costs unless specified.

| Boundary case | Expected economic result |
| --- | --- |
| Buy two units before record; sell both Friday open | $2,000 proceeds, zero units and zero split claims on Monday. Record-date ownership must not restore shares. |
| Start flat; buy two Friday open after record | Twenty Monday units, value $2,000. No separate claim or payment-date multiplier. |
| Hold two through Friday; sell Monday open | Convert to twenty first, then sell for $2,000. With 10 bps selling cost, fee $2 and proceeds $1,998. |
| Start flat; buy Monday open with $2,000 | Buy twenty new units, not two and not two hundred. Zero held units at conversion generate no entitlement. |
| End calculation Friday close holding two | Equity $2,000 in old-unit economic packages; no extra stock receivable. Do not report delivery inventory. |
| Tuesday ordinary ex-date, $0.01 per new share, later payment | Twenty pretrade units accrue $0.20. Tuesday seller retains the claim; Tuesday buyer gets none. Payment changes cash/claim composition, not equity by itself. |
| Earlier cash claim of $0.20 remains unpaid across split | Claim remains $0.20; converting shares must not make it $2.00. |

Also check warmup-only splits with zero inherited position/claims; exact-once conversion despite retained redemption metadata; constant economically equivalent closes producing no split-only signal; and explicit refusal for missing transfer evidence, unequal redemption/ex dates under this narrow policy, conflicting duplicates, separate trading, noninteger ratios and coincident split/dividend ex-dates.

## Opposing case and full-scope consequences

The strongest objection is that selling economically owned shares at ex-open can be impossible when a broker has not credited them, while immediate proceeds/reinvestment can overstate usable cash. That objection defeats an execution-feasibility claim. It does not defeat a clearly labeled theoretical economic-value calculation whose documented market terms attach the entitlement to every relevant trade. If the objective becomes available-inventory or cash-account compliance, retain refusal until settlement, delivery and reconciliation are modeled.

Preserve both prior invalid admissions. Any accepted D007 policy creates a new versioned attempt and must receive the five perspectives, actual requested CLI council responses, and separate criticism, quality and scope inspection. The frozen prices, windows, strategy and cost scenarios remain unchanged; all acquired data stays development-exposed. D007 can enable the missing historical accounting pilot, exact replay and independent oracle comparison. It does not supply an unseen evaluation, profitability evidence, operational research roles, reliable unattended operation, prospective paper evidence or permission for live orders.

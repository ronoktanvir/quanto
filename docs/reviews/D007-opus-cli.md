# D007 actual Opus5.5 terminal council

Actual completed review through local Claude Code2.1.316, using the existing first-party OAuth login. The child environment excluded direct API/routing and brokerage credentials; no project API key, model fallback, tool use or subscription purchase was involved. The five advisers are separately briefed AI processes under one lead, with correlated model-family reasoning; their agreement is not statistical independence or five human confirmations. All recorded invocation times below are UTC; the owner's Los Angeles date was still November1.

- Request `cli-046d8e00f62f4140b4674350f778c112`; exact responding model `claude-opus-5-5`.
- Packet SHA256 `8162c5f381167eda562c54d1492632651c21aaf0c6efa635d5723c347a3b5f8d`, 64894 UTF-8 bytes; proposal plus five full independently attributed reports, no private vendor records, prices or result tables.
- Started 2026-11-02T05:15:00.120075+00:00; finished 2026-11-02T05:16:04.846654+00:00.
- Exit0; success; end_turn; one turn; no substitution observed.
- Input/cache-creation/cache-read/output tokens: 2/21976/0/6139.
- CLI list-price usage estimate USD0.298596; not a reconciled subscription charge. Conservative USD3.50 hold remains in the shared journal.
- Visible response SHA256 before trailing archive whitespace `8e250fc5aaa8833371895e04700211a00e3249cb36eec96edbee1bac7df6f037`; private terminal-result SHA256 `8b2c060ee41c9f9819abb911fc0ab7c65beabbc9729106f17cdb7cc9153c1f32`.

Configured bounds: safe mode, no tools/MCP/custom commands/session persistence, explicit model, zero retries, one turn, high effort,12288maximum output tokens, USD2CLI estimate limit and300-second outer deadline. These are client controls, not an account-invoice guarantee. Neither reviewer executed tests, inspected actual private sources or certified admission. Their objections require lead disposition and affected-code/source review. Only visible response text is archived.

## Exact visible response

# D007 Council Review: Regular-Way Split Entitlement Policy

**Scope of this review.** I reviewed only the proposal text and the five adviser excerpts supplied. I verified no hashes, sources, code or data, and ran no tests. My findings concern internal consistency and the adequacy of the evidence contract. They are not certification of the NVDA event or of any implementation.

## Consequential blockers

**1. Provider ex-date agreement may read as optional.**
- The proposal says issuer terms govern "with provider ex-date/ratio/identity agreement and a second event-specific primary corroboration *where available*."
- One reading makes provider agreement conditional. The integrity report instead makes provider `ex_date == E` a hard requirement.
- The engine's `effective_date` must come from one source. If that source silently differs from the issuer-derived E, the conversion lands in the wrong session.
- **Correction:**
  - Provider `ex_date`, ratio and identity must each equal the issuer-derived values, or admission refuses.
  - "Where available" applies only to the second primary corroboration.
  - State which value populates `effective_date`, and assert equality in code.

**2. The session-adjacency test uses the retained calendar.**
- "E is the next retained provider-calendar session after P" passes if the provider omitted a real trading session between P and E.
- **Correction:**
  - E must be the next exchange session under a pinned, independent exchange calendar.
  - E must also be present in the retained bars.
  - No exchange session may be missing between P and E.
- The accounting report's "next supplied trading session" has the same flaw.

**3. The redemption field itself gets no discrepancy disposition.**
- Discrepancy handling covers only provider record/payable fields. The redemption-equals-E guard is a validity check, not an explanation.
- The excerpts suggest due-bill redemption is normally tied to settlement of ex-date trades. Alpaca's own SRE example shows redemption one day *after* ex.
- Redemption equal to ex may therefore be a vendor convention or anomaly needing the same source-bound disposition as record/payable.
- The guard was also chosen after the observed record was seen. It is tailored, not conservative.
- **Correction:**
  - Require an explicit disposition for the redemption field.
  - Disclose in the result that the profile's shape matches the triggering record.

**4. Plan lineage omits the earlier post-acquisition change.**
- The scope report records an initial `identity_change_unresolved` refusal and a "corrected narrow merger exclusion" before the due-bill refusal. That makes D007 at least the second policy change informed by this data.
- The revision artifact binds only the `unsupported_due_bill` attempt as its trigger.
- **Correction:**
  - Bind the full chain: every refusal, every policy revision and every plan predecessor.
  - Count all post-acquisition revisions in the result disclosure, so cumulative data-informed accommodation is visible rather than one hop at a time.

**5. "Facts may change under the new policy" is unbounded.**
- Re-admission may alter the primary-facts annotation beyond adding `regular_way_split`. Nothing requires those changes to be shown.
- **Correction:**
  - Require a mechanically derived diff between the old and new facts/annotation.
  - Each non-additive change needs a source-bound justification.
  - Refuse any unexplained edit to previously asserted facts.

**6. Cost-scenario reporting allows selective disclosure.**
- Each registered study "chooses exactly one" of 0/10/25 bps. The proposal then says to run all three, but never requires all three to be registered and reported.
- **Correction:** Pre-register all three studies under the revision artifact. Report every outcome, including failed or refused runs.

## Concrete corrections (lower severity, still needed before admission)

- **Ratio arithmetic.** "Integer ratio ≥ 2" must be tested exactly on the provider's decimal-string `new_rate`/`old_rate`, with no floats. Specify:
  - whether non-unit `old_rate` (for example 20/2) is accepted or refused;
  - the issuer ratio must equal it exactly.
- **One discrepancy code.** The proposal uses `unresolved_ancillary_date_discrepancy`, while the sources report uses `unresolved_provider_issuer_discrepancy_outside_modeled_terms`. A strictly validated schema needs a single enumerated value.
- **Reviewer attribution.** The integrity report requires reviewer identity and a timezone-aware review timestamp for each judgment. The proposal's object lists "attributed judgment" but no fields for these. Add them.
- **Timestamp ambiguity.** The adviser reports are dated 2026-11-02 UTC, while this session's local date is 2026-11-01. This may be consistent across time zones. Still, store "actual creation timestamp" values timezone-aware and order them by journal sequence rather than self-reported time. Registration-precedes-admission should be verified by journal sequence; content hashes cannot prove ordering in owner-controlled storage.
- **New-artifact failure coverage.** The proposal says generic failure tests "need not be copied without a changed risk." The `post_acquisition_policy_revision` registration is a new risk, so it needs its own tests for:
  - submission-before-validation;
  - interrupted publication;
  - tombstoning;
  - registration-ordering failures.
- **Signal/target units fixture.** Add a fixture where the P-close (old-unit) signal produces a target executed at E open. It should show the target is weight- or dollar-denominated, or correctly rebased, never an old-unit share count applied to new units. The accounting table implies this but does not test the signal path.
- **Adjacent dividend.** The issuer dividend ex-date (June 11) is one session after E, so it is not coincident. Its per-share basis ($0.01 per *post-split* share) must be checked against the provider's dividend record. Refuse if the provider amount is pre-split-denominated or carries its own due bill. The current "separate evidence" language should name this check explicitly.
- **Corroboration gap.** Second-source corroboration of E is an OCC options memo plus the 8-K; no exchange common-stock notice was found. Record this as a stated limitation, not as satisfied "exchange" corroboration.

## Evidence and independence caveats

- **Inherited outcome claims.** The integrity adviser states that the refusal outcomes come from checkpoint records, not independent journal inspection. The required lineage verification must actually confirm them.
- **Common briefing.** All five perspectives were briefed by the same lead. At least two came from the same model family (Codex). Their agreement is correlated advice, not independent confirmation; the proposal's own wording ("hashes do not authenticate… independent agreement") is appropriate and should carry into the result.
- **Economic logic.** The single-conversion model at E is well supported by the issuer seller-treatment statement and FINRA 11140/11630 as excerpted. I found no arithmetic objection to leaving the engine unchanged.

## Disposition

**Conditionally acceptable as a policy direction for implementation and review. Not acceptable as written for admission.**

- Before any re-admission, resolve blockers 1–6 in the decision text and verify them in affected code.
- D006 refusals remain effective and correct under the policy then in force.
- Policy adoption, fixtures or an admission receipt do not close the actual-pilot requirement. Closure requires an admitted historical run, reconciled against the independent oracle with exact replay, that exercises both split and dividend paths.
- Results remain retrospective development evidence:
  - no holdout status;
  - no edge claim;
  - no execution, settlement or inventory readiness;
  - no full-operation completion.

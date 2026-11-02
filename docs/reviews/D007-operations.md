# D007 independent advice — operations, failure handling, and replay

Author: Codex operations adviser, independently briefed by the lead. Prepared 2026-11-02 UTC. This is one bounded operations perspective, not financial-policy authority, an implementation review, or evidence of five-perspective consensus. I made no code edits, ran no tests, accessed no runtime or market data, and invoked no outside model.

## Recommendation

Keep the present `unsupported_due_bill` refusal active until the D007 decision and required reviews are complete. If the reviewed policy permits the proposed narrow abstraction, implement it as a new, versioned admission rule whose output is derived from reconciled source facts: security identity, split ratio, first split-adjusted trading session, and transfer treatment for regular-way trades made before ex-date. Preserve each raw vendor field, source occurrence, and attributed source judgment. A conflict or missing controlling fact must refuse admission. A nonempty ancillary record/payable discrepancy may remain unresolved only when the policy names it as a disclosed, non-calculation input and no source evidence indicates that it changes a controlling fact. Neither an approval Boolean nor equality of redemption and ex dates should bypass the refusal.

This is an admission abstraction, not a change to the portfolio engine. Keep the D006 strategy, evaluation window, and 0/10/25 bps cost scenarios frozen. No portfolio result exists; fixture success would establish software behavior only.

## Failure invariants

**Bind policy and code to a new admission identity.** The revised admission artifact should retain a new policy version, exact normalized controlling facts, raw occurrence hashes, issuer/source hashes and locators, disclosure of each unresolved ancillary field, and the current validation/accounting identity. Current loaded policy and helpers must be rechecked at calculation time, as D006 already does for admission dependencies. A changed source, annotation, normalization, predicate, helper, or policy invalidates the old admission for calculation and requires a fresh recorded admission. Never mutate the previous `invalid/unsupported_due_bill` submission or make an old success appear to reflect the new rule.

**Record attempts before semantic validation and preserve their outcomes.** Match the existing submission boundary: once bounded request bytes are accepted, journal the attempt before parsing or validating them. Invalid inputs, conflicting sources, unsupported action combinations, and changed dependencies need stable safe reason codes and durable outcomes. Do not store arbitrary exception text or turn a failure into an empty or partially accepted action set. A request too large or unserializable to cross the existing boundary remains outside the submission-receipt guarantee; do not imply otherwise.

**Publish admission atomically enough to avoid false success.** Before returning success, verify all referenced source and raw/normalized vendor artifacts and publish the admission record. If publication is interrupted, return the established safe pending/interrupted outcome and preserve the attempt; do not return an admission hash that cannot be reloaded and verified. Orphan content-addressed objects after rollback are acceptable if unclaimed and harmless. At calculation, verify the same dependency graph again before consuming evidence.

**Make replay equality include evidence and not only numbers.** With identical request, dataset, source bytes, facts, policy, and loaded code, a repeated admission and historical run should reproduce the same admission/result hashes and fingerprint. Changed bytes or code must produce a refusal/new identity even if the numerical portfolio path happens to be unchanged. Preserve input and policy hashes in the experiment fingerprint. Later bars/actions must not rewrite earlier signals; a future-prefix fixture should verify that adding later sessions leaves earlier event-engine outputs unchanged while changing the full input identity.

**Expose exclusions and failures in the private result.** A successful result should surface the retained admission version, controlling facts and their source references, all accepted and excluded action dispositions, every unresolved ancillary discrepancy and its “not an input” status, and the original refusal record/reference. The existing result may reference the admission by hash rather than duplicate its entire content, but a private consumer must be able to inspect all dispositions from the result view. Do not allow a later pass to erase or overwrite a prior refusal. A failed historical attempt must retain `historical_market_data` classification and its fixed reason in the journal.

## Focused synthetic fixture matrix

Add these as small admission/engine boundary cases; they do not need provider access or realistic return simulations:

| Fixture | Required result |
| --- | --- |
| Record-date to ex-date buyer purchases regular-way shares; trade date and settlement/transfer source evidence agree | Buyer’s eligible split-unit treatment follows the reviewed predicate; exact source references are retained. |
| Record-date to ex-date seller disposes of shares regular-way; source confirms transfer treatment | Seller/buyer allocation matches the policy; no double allocation. |
| Open order crossing ex-date, including a documented adjusted/cancelled status and an unresolved status | Apply only explicit policy-supported status; unresolved order treatment refuses or remains outside calculation with a visible reason. Do not infer execution from order presence. |
| Same split represented by a raw due-bill field and a corroborated economic split event | One economic share-unit change at the first adjusted session; retain both representations and occurrences. |
| Duplicate identical records versus conflicting same-ID records, and distinct IDs for one economic split | Collapse only exact duplicates while preserving each occurrence; reject conflicts/ambiguous multiplicity. Never apply ratio twice. |
| Redemption/payable discrepancy with no controlling-fact conflict versus one tied to transfer, ratio, identity, or first session | First can proceed only as disclosed and excluded from calculation; second refuses. |
| Changed issuer source, raw vendor occurrence, primary-facts annotation, loaded predicate, or code hash after admission | Existing admission refuses; a new admission is recorded. |
| Injected parse, validation, artifact read, journal finish, and partial publication failures | Each leaves a durable failed/pending state where storage permits, never a false success; private details stay out of safe responses. |
| Exact replay, then later-session prefix extension | Exact replay hashes match; prefix extension preserves prior calculations and changes the full input identity. |

The tests should explicitly assert that semantic failures have a preceding submission, that the original refusal remains queryable after any later successful admission, and that every result disposition can be traced to retained evidence. Existing D006 coverage for malformed requests, corrupt/tombstoned dependencies, current-policy changes, failed attempts, replay equality, and pending publication is a strong base; D007 tests should target the new controlling-fact boundary rather than duplicate those generic cases.

## Checks not needed for this increment

Do not add network acquisition, model calls, broad corporate-action support, live-order simulations, benchmarks, random stress matrices, or checks for every arbitrary Boolean field. Do not assert that vendor action data is universally complete or that source-attributed judgments are mechanically proven. The decisive operational test is narrow: source-bound controlling facts either reproduce the same permitted split-unit treatment or cause a preserved refusal. Accounting ambiguities belong to the accounting and source reviewers; operations should not resolve them by inventing provider semantics.

## Exact inspected revision

Checked out commit: `9c6b42e704af1f6763bc61c3932f69a91e4a1c67`. The current admission implementation digest is `7cd34c3244b7f87496827f933606e4000d52f4408438304ef14f27d1434cd953` (the assigned `7cd34c32` revision); test file digest is `e2111f2d8e84adc088e44666a7cc512e04cd12c0bf2fabba7b518b5dcf1312fb`.

Other inspected artifact digests: `src/quanto/explorer.py` `58d3e5508cc967210ebe41fb0b07200d32090652534fb87df5749647c9f81ddd`; `src/quanto/event_engine.py` `cb1a61985ebb08089eab50d00d1e78f09a83fdea6754587af7e871e177175ffc`; `docs/ACCOUNTING.md` `3a45f81bbf05af25f207431a67bff890a9f6bbb96998ae034dae00e0097777cc`; `docs/RESEARCH_PROTOCOL.md` `a0ab1a620f92fe08da39004b78bf85d2a5b1bf8327117a08990a9c47ec6a924c`; `docs/DECISIONS.md` `00de06501caeb9bc20840a377d5749e0d2019a63fffb489ccc38fbc88d9ae082`. Context/status/roadmap/handoff were also read. Any later implementation or policy revision needs a new review against its exact hashes.

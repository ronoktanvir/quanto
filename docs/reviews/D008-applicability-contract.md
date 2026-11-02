# D008 failure-context contract review

**Disposition: implement a qualified historical relationship within accepted D008, subject to separate implementation criticism, quality execution and scope review.** Exact membership in the currently bound D007 revision's verified refusal lineage is a narrower claim than correction or current applicability. It can clarify existing authorized failure metadata without changing financial policy, granting data access or requiring a model to proceed. This review approves that bounded contract, not uninspected implementation or another paid attempt.

Reviewer: `/root/d008_applicability_contract`, separately briefed contract adviser. Inspected branch `feat/failure-applicability`, HEAD `92ec9bad31d1a240bb220211cd29cabd2e49294d`, the contributor/context/status/roadmap/decision/handoff documents, D008_POLICY, revised-operational critic/quality/scope reports and the five source files identified below. No runtime, private data, environment file, network, model call, financial calculation or test was accessed or executed. The actual-attempt observations are attributed to the retained review reports, not independently reproduced here. The only owned output is this report.

## Observations and the limit of the inference

`FailureMemory._disposition` emits `state="unresolved"` both when no disposition exists and when an unresolved disposition was appended. Its ID distinguishes those cases. A corrected disposition is an attributed claim linked to bytes, not independent certification. `query` additionally retains `provisional`, failure artifact availability, disposition artifact availability and truncation. The broker currently transmits only alias, code, status and disposition, losing those qualifications. This is an observed information loss; it does not establish the cause of either actual stop.

The broker retrieves authorized failures only during the hypothesis stage and reuses their projected facts in later packets. Its current per-packet suite observation revalidates the suite, but does not bind or recheck these cached failure facts. Extending the packet without extending the proof would therefore permit a true-looking relation or disposition to be paired with the wrong retrieval, suite or later state.

`study_suite._verified` rederives the complete roster through current admission and policy validation. `policy_revision.validate_revision` rederives exact refused request bytes, registered outcomes, journal positions, acquisition/source dependencies, additive fact changes and the accepted policy chain. Its `lineage.prior_refusals` is an appropriate local basis for a historical membership relation. A raw stored revision, shared refusal code or later successful run is not an equivalent basis.

The revised trace reports two actual responses followed by a hypothesis stop, with zero financial work. Its corrected packet bindings passed trace inspection. Neither that observation nor the original engineer stop isolates failure-memory wording as the cause. The original refusals remain valid historical outcomes under their respective declared policies.

## Exact outbound semantics

Each failure entry has exactly these nine fields; retain the existing maximum of 16 and deterministic run-local aliases:

| Field | Allowed value and meaning |
| --- | --- |
| `alias` | Existing `failure-1` through `failure-16`, with unique exact private mapping to `(source, id)` |
| `code` | Existing approved failure vocabulary; preserve the original approved code, or existing `other_refusal` projection for an undisclosed code |
| `status` | Existing approved status vocabulary, preserving the original observed status |
| `disposition` | `unresolved` or `corrected`, preserving the memory claim/default; never derived from the new relation |
| `disposition_recorded` | Boolean derived from the verified presence of a disposition ID, not from the disposition string |
| `provisional` | Exactly `true`, preserving the memory service's qualification |
| `artifact_state` | Exactly one of `none`, `not_allowed`, `verified`, `unavailable`, `verification_bound`, from the failure evidence check |
| `disposition_artifact_state` | The same finite vocabulary, from the disposition evidence check |
| `relation` | Exactly `prior_refusal_in_bound_revision` or `no_relation_established` |

Enforce consistency: an absent claim has `disposition_recorded=false`, `disposition="unresolved"` and `disposition_artifact_state="none"`. A corrected claim requires `disposition_recorded=true`, a disposition artifact state other than `none`, and a status other than `pending`, matching the current memory writer's required fix reference and original-outcome checks. A positive D007 relation requires original status `invalid`; identity and source remain the broker proof's responsibility. A recorded corrected claim remains a provisional claim even when its approved artifact bytes are available. No extra keys, raw IDs, hashes, dates, source identifiers, parameters, values, predicate truth or diagnostic prose enter these fields. Keep original outcomes and disposition records unchanged. Do not append dispositions merely to support this projection.

`prior_refusal_in_bound_revision` means only: at this packet's local verification, this exact authorized submission, original request identity and original invalid outcome matched an entry in the fully revalidated policy revision bound through the current suite and admission. It does not mean the refusal was mistaken, corrected, superseded, irrelevant, harmless or cleared for financial execution. Only `source="submission"` can match this D007 lineage. An attempt with a coincident ID or matching code cannot match.

`no_relation_established` means the exact authorized record did not match that verified lineage. It establishes neither current applicability nor non-applicability. Invalid or unavailable current revision dependencies must refuse preparation; they must not be converted to this negative relation. An ordinary nonmember can receive this relation after successful verification of the current basis.

Artifact states describe the memory service's approved reference subset. In particular, `not_allowed` means the service did not verify those references under its artifact allowlist; it does not mean the bytes do not exist. `verified` does not establish the truth of the evidence, an independent review, or completeness of all underlying references. The current broker grants no artifact references to FailureMemory, so successful separate lineage verification must not silently upgrade the memory artifact state. Retain the distinct qualifications.

Add fixed program-text explanations of these meanings to the system prompt. Explain that missing claims do not prove current applicability and lineage membership does not prove correction. Preserve the existing meaningful model choice and unrestricted stop/block decisions. Do not direct the model to discount a refusal or prefer a predicate. This change supplies provenance context, not economic motivation for choosing a diagnostic condition.

Freeze the revised exact packet schema and prompt under their own source/contract identities. Historical packets keep their original bytes and interpretation. No permissive parser fallback should silently accept both the old four-field and new nine-field entries as the same proof contract.

## Minimal producer and proof interface

Use a private retained failure basis as the handoff between the retrieval producer and per-packet proof helper. The following are interface contracts, not mandatory function names:

1. `retrieve_failure_basis(store, authorized_failure_ids) -> basis_sha256` runs only inside the already issued hypothesis `query_failures` effect. It retains exact successful query receipt references, the exact authorized and returned `(source, id)` sets, deterministic alias mappings and the relevant private record/disposition/evidence state. No relation is accepted from caller input. An empty authorized set performs no unrestricted query and produces an explicitly empty basis.
2. `verify_failure_context(store, configuration_sha256, role, basis_sha256) -> observation_sha256` reads that private basis, validates its receipt and exact authorization, verifies unchanged current failure/disposition/evidence state, and fully revalidates the current suite/revision. It returns a retained private observation containing the derived nine-field facts and their evidence bindings. This is supervisor validation of already authorized records, not another worker query or a broader memory search. The director has no failure basis and sends an empty failure list; later roles cannot silently omit an available hypothesis basis.
3. The packet producer takes failure facts only from this verified observation. The existing predispatch binder checks exact equality between packet failures and the observation's facts, in addition to configuration, role, assignment, fence, method, packet digest and unique planned model request ID. The same planned ID must later join the actual dispatch hold and request-body digest. Persist the private observation/binding before the paid effect, including paths whose response never returns.

The existing `_method_verification` may own the combined observation to avoid a second independent suite validation. Reuse is safe only inside the same verified preparation with exact suite/configuration/revision bindings; a helper must not accept an arbitrary caller-supplied dictionary merely because it has a policy-revision kind. Otherwise call the existing validators independently. No change to `policy_revision.py`, `study_suite.py`, financial rules or pinned financial identities is needed merely to expose the relation.

## Private proof and freshness requirements

The observation must retain enough evidence to recompute the exact safe packet facts. Bind the following privately, either directly or through hash-verified retained artifacts with exact equality checks:

- Current configuration, authorized failure set, role, preparation time, implementation/prompt/schema identities, suite manifest and registration request, common admission and policy revision identities.
- Successful original memory query submissions and receipts, exact returned set, `provisional=true`, `truncated=false`, alias-to-`(source,id)` mapping and the full relevant safe memory projection. Count equality alone is insufficient; reject duplicates, missing records, extra records and wrong-source substitution.
- Each original failure's submission/attempt identity, request identity when available, unchanged original status/code and exact outcome/event evidence. For a positive D007 relation, also bind the original request-byte artifact and exact validated `prior_refusals` entry, including its checked request identity and journal positions. For unrelated generic failures whose original request bytes were never retained, do not invent a byte-availability claim; bind their recorded request digest/outcome and project `no_relation_established`.
- Latest disposition identity or verified absence, its state/code/fix reference, its checked evidence availability and the corresponding original retrieval state. Bind exact identities even if two consecutive dispositions happen to have identical visible values.
- The current validator-derived dependency identity set, including the suite/admission/revision and their retained request, source, policy, review and lineage references. Re-read/hash required bytes through existing validation; an old dependency-list hash alone is not current availability evidence. Keep all source and data identities private.

At every dependent packet, revalidate the original retrieval basis against current relevant records and rederive the relation from the current bound suite. If a disposition identity, outcome, relevant availability state, authorization, suite or dependency changed, refuse that packet rather than silently refreshing the basis or widening the query. A newly needed retrieval is a separately registered workflow decision, not an automatic paid retry. A fresh observation is required even when the outward facts happen to be unchanged.

Prevent observation substitution at binding: a valid old observation for the same role is not automatically valid for a new assignment/request. Bind its exact preparation and private basis to this assignment/fence/request, and reject reuse or mismatched facts. Keep validation and binding adjacent; the binder should check the current relevant basis in its live-lease transaction, or compare an independently refreshed exact basis there. Do not claim the whole journal head must remain fixed: normal workflow/budget events advance it. What must remain valid is the specific evidence on which the outbound assertion depends.

The transmitted meaning is verification at packet preparation, not a perpetual certificate or a promise of all filesystem states during the later network request. Application transactions, content hashes and checked bindings protect cooperating execution; the privileged database/filesystem owner remains outside the threat model. Preserve the existing final dispatch authorization, lease/deadline/budget checks and no-retry behavior.

## Required review evidence and policy boundary

Independent implementation criticism and quality should specifically exercise absent versus explicitly unresolved claims; corrected claims with available, disallowed and unavailable fix evidence; changed latest disposition with identical outward state; wrong-source and same-code nonmembers; wrong suite/revision/admission/configuration; forged lineage JSON; missing or corrupted dependencies; truncated or incomplete retrieval; extra/duplicate returned IDs; stale proof reuse; packet/proof fact mismatch; changed evidence between retrieval, preparation and binding; and dispatch failure after binding. Verify refusal before paid dispatch where the precondition fails and preservation of attempted-work records. These are requested checks, not tests executed by this adviser.

Privacy checks must inspect complete rendered outbound packets and all new proof alias paths, ensuring that private proof IDs, requests, dependency hashes, dates, values and diagnostics never escape. The proof must remain available for failed responses without becoming an outbound artifact alias. Separate scope review should confirm that the relation did not become a clearance assertion, a default predicate or a model-pressure instruction. Acceptance must identify exact implementation artifacts; this contract report cannot certify future code.

This remains routine implementation of accepted D008's authorized failure retrieval, strict egress and exact evidence binding, provided the above limits hold. It needs separate critic/quality/scope inspection, but not a new five-perspective financial-policy council merely to expose verified lineage membership. A significant review is required if the change instead grants new evidence access, declares failures corrected/inapplicable, relaxes admission, changes the frozen calculation, expands automatic retries/spending, or redesigns the role objective beyond the accepted bounded diagnostic choice. Such a review would require the prescribed five perspectives and actual Fable/Opus CLI route when available; this report does not substitute for it.

The next acceptance question is whether the implemented packet says exactly what its verified evidence supports. Whether that context changes a model's decision remains untested. Neither favorable model wording nor this correction alone completes the actual workflow, R14, protected evaluation, persistent scheduling/restore, paper operation or separately gated live readiness.

## Inspected source identities

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/failure_memory.py` | `ee8200079cc0e091b06d60be6fe4ccb3d4886eb1ea986ee626db65ae7f9f7ee7` |
| `src/quanto/policy_revision.py` | `eb7ac89bbf1c85cf276f614bd296ad82f2d22f94d723788a3718c42ff5b12625` |
| `src/quanto/study_suite.py` | `c3e552ef9998e72ae6f69b55bf43750d51f94522faf98a26ecbb624042f46360` |
| `src/quanto/research_broker.py` | `d26ca8496ab50cb7536b28e2623fd4d8902d67ba3a3c7a93da9be01349924630` |
| `src/quanto/research_packets.py` | `acdab795bbb47c2002d50cf4872bd9c58775bafd832ace5f0903ed2649d92dde` |
| `docs/D008_POLICY.md` | `91bd473d6972355c8cba447fff7b1e66e9b77bddf9712097ebd0f95bafc07aa7` |

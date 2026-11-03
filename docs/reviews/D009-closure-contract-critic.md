# D009 nested evidence closure: independent contract criticism

**Recommendation: add a finite, read-only structural edge inventory before attempting complete nested evidence closure.** A digest's role comes from its producer and referring field, not its spelling. The smallest coherent increment can classify a bounded set of dataset/suite/result objects, preserve inline request identities, and report unsupported historical/external evidence without constructors, current-domain validation or replay. Full recovery must remain false.

**Plan disposition: no remaining contract blocker was found in the corrected proposal at SHA-256 `5e7d52797e62224aaf8c4b22fccf72b76995566927ac47529701c2f2b984df9f`.** This accepts the bounded implementation contract, not uninspected code, actual payload coverage or completed recovery.

Reviewer: `/root/d009_v2_critic_finish`, separate from the producer. Public-source inspection began at `a49bc0a7441f20f7382e85117a61c7a90cf090d0`. I read the accepted D009 policy and relevant public producer/consumer source only. I did not inspect actual payloads, databases, runtime receipts, keys, credentials, accounts or captured objects, and did not invoke any constructor, financial runner, provider, council, network operation or actual capture. The scenarios below are implementation requirements, not executed tests.

## Four edge meanings must remain separate

| Classification | Evidence in public source | Safe offline treatment |
| --- | --- | --- |
| Required stored object | `store.put_json`/`put_bytes`, verified references before publication, or a typed producer field declaring stored source/roster/result bytes | Verify digest/size against the captured inventory and tombstones. Missing live required bytes or malformed recognized structure block that supported coverage claim. Do not fetch or recreate bytes. |
| Inline or digest-only identity | Suite-member `request_sha256`, broker code/specification hashes, provider body hashes, and generic submission request digests | Preserve the identity. Recompute from the explicitly identified inline value or exact retained bytes only when the producer contract defines that relationship. Do not demand an unrelated object at that digest. |
| Historical availability observation | Failure-basis `request_availability`, `reference_availability`, memory `artifact_state` and disposition availability | Preserve what was observed then. Report current captured availability separately; a historically unavailable request/fix is not a promise that current bytes must exist. Do not rewrite historical state or promote `not_allowed` into verified availability. |
| External source/audit evidence | Legacy `artifacts/synthetic` outcomes, outside-model report paths/digests, historical source identities and runtime audit sidecars | Record the bounded category and supplied identity as unsupported/omitted. Never interpret an embedded path or URL as permission to open/fetch it. A digest alone does not preserve the external bytes. |

The earlier suite-launch defect demonstrates the consequence of collapsing these categories: a valid inline request was rejected because its identity was treated as a standalone object. The new layer should encode the category explicitly for every supported edge, with the referring object/record, field path, expected target role, profile version and digest. Optional values need typed null/absence rules rather than generic hash scanning.

An unavailable dependency may limit verification of an old claim without invalidating the fact that the claim was historically recorded. Tombstones remain authoritative exclusions: do not read a physically present tombstoned object to improve coverage. The report must distinguish missing live required bytes, unavailable tombstoned evidence, historical unavailable observations and simply unimplemented reference semantics.

## Classification needs producer context

Copied object bytes include raw vendor pages, private response text, normalized data, unpublished/orphan objects and application documents. A self-reported `kind`, `schema_version` or field named `artifact_refs` is insufficient authority to choose an application profile. Vendor JSON or a quoted historical record may use those names without declaring a current dependency. Begin from captured database/event roles and propagate explicit expected roles through the finite registry; do not assign authority to every copied JSON object.

Recognized profiles need strict field/type/version checks. A malformed recognized object must refuse that profile rather than quietly fall back to an opaque leaf. Unknown versions, extra reference-bearing structure and unrecognized origin/role combinations remain explicit unsupported coverage. Legitimate raw bytes and data-only values can be named leaf roles whose format supplies no application edges; that designation must come from the parent contract, not a global rule that arbitrary JSON contains no references.

The same digest can be reached as an opaque byte payload and as a typed document. A digest-only visited set can incorrectly suppress the later typed check. Track traversal work by digest plus expected role/profile, retain edge provenance, and bound depth, unique objects, role visits, edges, per-document JSON and aggregate bytes. Cycles must terminate without inventing a missing-object error or declaring unchecked branches complete. All malformed/unbounded paths fail with fixed categories, without printing payloads or private paths.

## Current validators are unsuitable closure parsers

`research_failure_context._current_basis` compares a historical basis with current `_identities`, current dispositions and current availability. `_evidence` invokes current suite/admission/policy validators; `verify_failure_context` publishes a new observation. Failure-memory querying also records a new receipt. Reusing those entrypoints would change the question from “which bytes and relationships were retained?” to “would today's research system accept this?” and can mutate state.

Admission and policy validators also rederive current rules, source identities and registered chronology. Even an adapter that suppresses writes would not remove those current-source assumptions. The new layer must implement pure versioned structural extraction and exact hash/inline relationships, without importing domain validators as its semantic authority. An old source hash is a historical identity, not a requirement that the current installation match it; a separately retained historical-source copy remains missing until actually included and verified.

`exploratory_result` uses `result_kind`, not `kind`, and embeds `admission_evidence` and `study_suite` snapshots. Its field named `frozen_request` is the derived strategy/evaluation specification built for experiment registration, not the original submitted request envelope. Hashing that value against `provenance_submissions.request_sha256` would create another false identity failure. Those embedded snapshots are historical values, not invitations to re-admit the data or execute a member. The outer known object references and explicitly specified inline identity relationships can be supported while those larger embedded schemas remain unchecked. No numerical engine or result recomputation belongs in this increment.

## Root inventory must include interrupted work

The frozen capture's direct database references are a partial starting point, not the complete root contract. Public broker source binds stored packet/proof/context/basis bytes in `workflow_broker_packet_bound` and `workflow_broker_failure_basis_bound` events before dispatch or terminal publication. Pending acquisition records likewise retain prepared request/page objects through events. A terminal-outcome-only walk can omit the very evidence needed to explain a failed or uncertain effect.

Add explicit root-extractor entries for these supported event meanings, with their actual field names and nullable director-basis case. Preserve consumed intent/dispatch identities and chronology as recorded; do not call broker binding routines or reinterpret a missing terminal record as permission to retry. Conversely, `external_review_requested.packet_sha256` is a packet identity. Its external response is written under `runtime/reviews` and bound by a separate review record; neither that event hash nor a report path implies a content-store object. Generic review `artifact_hash` also does not universally identify a stored object.

Unknown event families and external evidence roots must be counted/named as uncovered categories, not silently considered reference-free. Root extraction itself is versioned and partial. It can improve the visible coverage boundary without claiming all historical schema families have been understood.

## Smallest coherent next implementation

The bounded first extension should consume an already verified offline candidate and construct a read-only edge report. It should preserve the existing capture format and leave the frozen capture code/tests unchanged until an explicitly reviewed implementation requires otherwise. Dataset and suite families provide a useful finite core:

- `explorer_dataset`: stored source and normalized-bar objects, plus nullable parent dataset, selected through the registered dataset role.
- `study_suite`: stored registration-request bytes and declared artifact references, with member requests treated as inline values and their member digests as inline identities.
- `study_suite_run_roster`: stored suite/run-request bytes and inline member requests; no standalone member-request object requirement.
- `study_suite_summary`: stored suite/roster and explicitly declared result references, preserving pending/failed/not-started members rather than rerunning or re-admitting them.
- `exploratory_result`: outer dataset and nullable admission references, the inline derived specification without equating it to the submitted request digest, and named unsupported embedded admission/suite/source evidence until dedicated profiles exist.

Acquisition receipts, admission/policy lineage, failure-context snapshots, broker packets/proofs/private responses and external audit evidence need precise source mappings now, but need not all be implemented together. They remain named unsupported blockers to complete coverage. This is preferable to a broad recursive parser that gives every hash the same meaning. Current-byte availability and structural extraction success must be reported independently of claim truth, investment merit, model access or historical source rights.

Acceptance tests should cover each supported profile's required/optional fields; inline hashes without standalone objects; unavailable historical request/fix observations; registered raw/vendor JSON containing misleading application keys; the same digest reached under two roles; cycles and bounds; malformed recognized schemas; extra/unknown reference-bearing fields; pending packet/basis/page events; tombstoned dependencies; missing external sidecars; and byte-for-byte inert verification with constructors/domain validators/provider/replay entrypoints replaced by refusal sentinels. All would be synthetic software evidence. No actual-data inspection is implied by this contract.

## Inspected identities

| Public artifact | SHA-256 |
| --- | --- |
| Accepted `docs/D009_POLICY.md` | `68eea41a20a171681e53368b98954fefa8e65e7513ec21b6dc482dfc25851c61` |
| `src/quanto/provenance.py` | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |
| `src/quanto/explorer.py` | `6a3f02d27f0c062d993ee3d112f0e76b88221fc8653305b84be62b822bcb9745` |
| `src/quanto/study_suite.py` | `c3e552ef9998e72ae6f69b55bf43750d51f94522faf98a26ecbb624042f46360` |
| `src/quanto/research_workflow.py` | `64ca63f155a2417021bb8632673f14ec12ff7d497881aa13a95d7330911ab02b` |
| `src/quanto/research_dispatch.py` | `120834deb63abebeeb54a14f8cf470ad43fd9ac1f44979ee96fe9c88ba20c1f1` |
| `src/quanto/research_broker.py` | `aa4f9e93f9fc471273bf2e6c1a0d67acb74583228618cecd17aa9ec513419e34` |
| `src/quanto/failure_memory.py` | `ee8200079cc0e091b06d60be6fe4ccb3d4886eb1ea986ee626db65ae7f9f7ee7` |
| `src/quanto/research_failure_context.py` | `b99af35355b14d638770c069791124a8d72774346e5a9677ac74d607bc777208` |
| `src/quanto/policy_revision.py` | `eb7ac89bbf1c85cf276f614bd296ad82f2d22f94d723788a3718c42ff5b12625` |
| `src/quanto/admission.py` | `5b1d5aa7d9aea6488ba96ac8a89a597d37e78ad28be0175699f6032abb8787c1` |
| `src/quanto/alpaca_data.py` | `9182307746567e349ed1b936eb35949fac7684430336279968f02d6f35ab0c76` |
| `src/quanto/alpaca_actions.py` | `f6804b8717a3dd60ff77fcf934581170b762cf82f77b5dd229c349c127205cc7` |
| `src/quanto/critic.py` | `ff50f8f22d5968e61d5372fdb180cdd2f6203a09c21bf2b72737f1c83472b6c3` |

## Exact proposal review and corrections

I read the initial producer proposal `docs/reviews/D009-closure-implementation-plan.md` at SHA-256 `c0f893d4aa726740e0d7fa78d05c28aaadc5e1e5d26ab926d747760071d7008a`, then the retained correction appendix at final file SHA-256 `5e7d52797e62224aaf8c4b22fccf72b76995566927ac47529701c2f2b984df9f`. The producer received the risk findings above directly. The initial proposal's core scope matched the recommended finite registry and dataset/suite/result subset; four concrete clarifications were required before implementation:

1. Use actual stored event selectors `workflow_broker_packet_bound` and `workflow_broker_failure_basis_bound`, not the unprefixed names passed locally to `ResearchWorkflow._event`. That method adds `workflow_`; the incorrect selector would silently miss pending evidence.
2. Name the actual broker producer `research_broker.run_workflow`, rather than the nonexistent `run_broker`, so the source contract is traceable.
3. Refuse malformed records that claim a recognized supported profile. Preserve well-formed unsupported versions/families/origins as explicit incomplete coverage; an unknown kind alone does not prove malformed bytes.
4. Key graph visits by digest plus expected role/profile so an earlier opaque visit cannot suppress a later typed check of the same bytes.

The dated appendix explicitly adopts all four, preserves the initial proposal identity, and keeps every stronger acceptance flag false. It also incorporates the distinction between an exploratory result's derived `frozen_request` specification and the original submitted request envelope. No additional contract blocker emerged from the corrected plan read.

The accepted next subset is a new inert closure module and synthetic tests, using the existing verified snapshot as input and recording its own manifest/profile identity. Acquisition/admission/policy/failure/broker/source-audit families remain mapped but unsupported internally; their independently required target bytes and unresolved external requirements stay visible. Required audit evidence is not renamed chat continuity or erased because the first snapshot omitted it. Current-domain validation, constructors, source substitution, provider fetches, research replay and actual capture remain outside this work.

This is routine implementation within D009's already accepted evidence/restore boundary, not a new financial policy or revised freshness threat model. Independent implementation criticism and quality execution are still required. No product code was changed, no test was run, and no actual state, private payload, key or network was accessed by this critic for this contract review.

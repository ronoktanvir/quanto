# D009 versionless event profiles: independent compatibility plan

**The frozen inspector applies the newest broker-packet reference requirements to a versionless event that has two documented writer generations.** A narrow correction should recognize those generations explicitly, preserve strict current-profile requirements, and keep uncertain origin/legacy evidence incomplete. Blanket optional fields, source-data rewriting and a fresh full-inspector retry are not justified by the current evidence. No product source or tests changed in this review.

Reviewer: `/root/d009_v2_critic_finish`, source-only criticism plus permitted safe diagnostic metadata. Actual candidate execution and receipt checks remain lead-attributed. I read no actual candidate, private receipt, database/object payload, IDs, keys or accounts. Exact historical writer bytes were read from local public Git history and retained in the ignored synthetic-review area.

## What is observed, and what remains unestablished

The lead executed root-only diagnostic `5baa87582ce6f2f73489f4082121819eb09c965f6053d3a8c9e11bacac8cfb6a` once. Its permitted `rootshape-result.json` reports `diagnostic_completed=True`, `root_registry_completed=False`, `malformed_supported_profile`, and exact frozen code locations `_need:43` and `_Reader.roots:356`, with predicate `recognized_event_has_required_reference_field`. The frozen manifest/database digest and schema guards passed before/after. Neither the full inspector nor graph walk ran. Those facts isolate a missing whitelisted reference field at that registry predicate; they do not identify the event kind, missing field or producer generation. Aggregate observations are not a completed graph. The consumed earlier attempts remain preserved.

A distinct key-shape survey may identify counts for only the fixed broker-packet/failure-basis event names and whitelisted field-presence/type patterns. It must expose no row IDs, digests, values, arbitrary keys or roles. It must retain exact manifest/database/schema guards and existing limits, with no full inspector/roots/walk or product change. A legacy-compatible key pattern alone does not prove historical writer identity or diagnose the older generic closure failure.

## Exact public writer history

| Writer revision | Observed event behavior |
| --- | --- |
| `6d278f0023abaa9307f76813ce261ec49e255c7f` | No `broker_packet_bound` or `broker_failure_basis_bound` emission exists in this broker source. It is not evidence for a packet-binding profile lacking verification. |
| `038714dfb47e30bf0ad506cfe79bd93ca51a651c` | Introduces `_bind_model_packet` and packet-binding event together, including `configuration_sha256`, `packet_sha256` and `verification_sha256`. Both failure fields are absent. |
| `eb47a7203107bcd9b91439ab5b7fd2808d38246a` | Retains that packet reference shape while changing review-summary behavior elsewhere. |
| `9edfa86ea37ec89616ee0218cb31ac187a78665c` | Adds packet `failure_context_sha256` and `failure_basis_sha256`; introduces the separate failure-basis binding event with `configuration_sha256` and `basis_sha256`. |

`ResearchWorkflow._event` prefixes stored kinds with `workflow_`; use exact stored selectors `workflow_broker_packet_bound` and `workflow_broker_failure_basis_bound`. The packet metadata keys common to both writer generations are `parent_submission_id`, `assignment_id`, `role`, `fence` and `request_id`. The newer writer requires the failure context and includes the basis key even when its value is null for the director; its non-director path requires the bound basis. Absence and explicit null are different observations. The older profile never had either failure field. All three base references, including verification, remain required in every documented packet profile.

The frozen inspector's `EVENT_REFS` instead requires all five packet reference keys unconditionally. Thus a correctly retained038714/eb47-shaped packet will reach the missing-field predicate despite being valid under that writer's field contract. This source history establishes a compatibility defect for that synthetic historical shape; the actual affected shape remains subject to the separate survey.

## Smallest enforceable correction

Keep finite, named legacy/current packet profiles and the separate current failure-basis profile. A profile selector must distinguish documentary compatibility from established producer origin. Event timestamps, increasing event IDs, today's source code and absent fields cannot establish which writer produced a record. In particular, a damaged current event with both failure fields removed can resemble the older packet shape.

The strongest narrow selector uses already retained bindings: event parent/configuration to its `research_broker_runs` row, the exact configuration object, its recorded `code_identity`, and agreement between the row's `code_sha256` and the canonical identity hash. An explicit reviewed allowlist of historical broker source digests then selects the relevant reference-field profile; the workflow source identity must also agree with the reviewed stored-kind convention. This is finite structural origin checking, not executing historical code, accepting a current-source substitute or certifying every configuration semantic. Missing/contradictory bindings must never silently select a legacy profile.

If that origin selector is deferred, the honest smaller fallback is an explicit **unresolved/legacy-compatible event gap**, with only already unambiguous present references inventoried. Do not label that event a verified legacy/current profile. The report must preserve the unresolved origin and missing modern evidence, and cannot claim that current requirements were satisfied. A known-current origin missing either required failure key must still refuse; a known older origin missing configuration, packet or verification must refuse. Partial failure pairs, invalid digests and unsupported mixed shapes must not become benign omissions. Unknown producer/profile families remain explicit unsupported coverage rather than guessed compatibility.

For a selected older profile, require each documented base digest, register its exact required-object edges and record that modern failure context/basis is unavailable in that historical event contract. Never manufacture those objects, infer them from later successful stages, rewrite the event or claim modern failure-context semantics. For a selected current profile, retain all required keys and digest checks; treat the explicit nullable basis according to the documented current contract. Preserve the separate failure-basis event's required configuration/basis references. Existing event-chain, snapshot digest, required-object/tombstone and traversal safeguards remain intact.

This correction remains finite closure inventory. Producer-source binding is cooperating-process evidence, not hostile-process attestation or full replay. Broker semantics, external/runtime/source evidence and other unsupported families remain incomplete. `typed_closure_complete`, `full_recovery_accepted`, historical replay and execution stay false; no actual capture/copy/full inspection, scheduler revival or model/provider call is authorized by this plan.

## Synthetic regression contract

Before any distinct actual inspection, freeze corrected source/tests and independently verify:

- Exact source-shaped038714 and eb47 packets retain three base edges, a legacy/profile gap and false full flags. Exact9ed packets retain all applicable references; explicit null and absent basis are tested separately.
- A known-current event cannot downgrade by dropping both failure fields; a known-legacy packet missing verification also refuses. Test partial pairs, malformed/null mandatory digests, contradictory producer binding, unknown source identity and arbitrary extra SHA-like fields.
- Unknown/unbound origin is reported as unresolved, never promoted to verified legacy solely because of key presence. If only the fallback is implemented, its narrower claim and unresolved count are mandatory.
- Pending events with no completed stages remain roots. Stored `workflow_` names are exact. No row/ID/path/digest values escape the safe projection; unknown fields are not recursively scanned.
- Snapshot bytes/manifest/head and code identities remain fixed, with the original graph/node/JSON/deadline bounds and inertness preserved. No producer constructors or domain validators run. Existing same-digest role, inline-hash, tombstone, unsupported-family and failure-history regressions remain applicable.

The proposed event-key survey is diagnostic evidence only. Any later product acceptance needs exact corrected hashes and separate criticism/quality/scope; the consumed full inspector and root-shape diagnostic must never be rerun or relabeled successful closure.

## Retained public-source evidence

Exact source copies/diffs are under ignored `runtime/recovery-event-profile-critic/`; `writer-evidence.json` SHA-256 is `6029c26a89f4a32f899649a8f02961c498c1137575deb9f659f318ce3af7f0d2`. Broker source hashes:6d278 `ad8fe8f46103c85fdf77dd4ade94449f504d449ed5e01d580934312d6b8bd6b4`;038714 `c59a3801d41a68811231d640bc9dbd69e8a7ce933ab855e8f011f969d4654af7`;eb47 `d26ca8496ab50cb7536b28e2623fd4d8902d67ba3a3c7a93da9be01349924630`;9ed `aa4f9e93f9fc471273bf2e6c1a0d67acb74583228618cecd17aa9ec513419e34`. Workflow source at all four revisions hashes to `64ca63f155a2417021bb8632673f14ec12ff7d497881aa13a95d7330911ab02b`. Retained6d→038 and038→9ed broker diffs hash to `2641136fd6dccddfc568461cb441fcd1588276adcf181e4cd3f1e0396f3da510` and `f357efccf04931e9861df6790ac3ef1d3be22df6d2cb3e45e99852f542e77edd` respectively. These are original public-history bytes, not reconstructed candidate evidence.

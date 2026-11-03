# D008 protected-access criticism: frozen producer candidate

**Do not accept the frozen candidate yet. Four reproduced defects leave preparation reservations incomplete or unusable.** The implementation adds durable starts beneath raw transport/content calls and keeps actual protected eligibility disabled, but classification and publication still allow observations to escape the intended accounting boundary. These findings concern invented preparation scopes, not an actual protected-data breach or trading result.

Reviewer: `/root/protected_access_critic`, separate from producer, quality and scope. I verified all 24 supplied public source/test bytes against manifest `3b9fbb9c95c5718727fe8928f5e84f9ad5b56f6c0abc1d3848f0786507baf22a`, then exported committed base `96d1f67ae7b1bb4087ca818220e25cb44e01212b` and overlaid only those files. The export is retained under ignored `runtime/protected-access-critic/frozen-v1/`. All probes imported that export, used fresh resolved temporary roots, invented content/credentials and fake transports, with socket connection/resolution calls refused. No actual project store, recovery candidate, credential, provider, model, protected observation or financial calculation was accessed.

The inspected contract is `7f6a8e44449c82afd0e9c667cf1a387022751932ea136d99dea78e67e05bb835`. Registry source is `4815144aecac18b18dbd69c858046b4d700debf1abf6138cf417c7bd24789cee`; provenance is `ceba0b408788d099e7bcac53037ada81c4be93305249488e8357590e2319e2f7`; bars transport is `b115e822677761b7ae4177ca4135a5c28c359b48ce42d5aa0f11841dd6ecb9ff`; actions is `bb3106dc40da289566df55200fd870248fc70c2f71417db6a9aa4563a95c58a4`. The complete map remains retained rather than inferred from a later working tree.

## Required corrections

### C1: ordinary intent can assign unproven content coverage

`AccessIntent.bind_object` at frozen `evaluation_registry.py:659–669` looks up an issued intent, copies its request coverage and calls the administrative classifier for any supplied digest. It does not establish that the digest came from that intent's actual effect or trusted producer. A caller-chosen request is not evidence of a retained object's origin.

The independent probe reserves synthetic security BBB, publishes an unclassified byte object and confirms that its ordinary read is refused. It then calls ordinary `session.acquisition` for disjoint AAA and `intent.bind_object(digest)` without dispatching any provider effect. The same read succeeds afterward; no reservation invalidation is recorded. No direct `Supervisor.classify`, private attribute alteration or malicious filesystem operation was used. This recreates the caller-selected-coverage problem through another public helper.

**Required:** make classification/publication authority supervisor-owned and tied to the actual prepared request, received output or derived artifact and its retained effect/lineage. An arbitrary live intent must not certify arbitrary bytes or a result after rejection. Merely calling this method “trusted producer” in a docstring does not enforce the ordinary-call boundary. Test an unrelated digest, no effect, wrong effect, rejected intent, changed relation and actual valid producer paths. If a deliberately trusted administrative operation remains, ordinary intent capabilities must not expose it as a shortcut.

### C2: corporate-action responses retain the requested security scope without checking actual coverage

Frozen `alpaca_actions.py:194–209` publishes and classifies raw response bytes before parsing them, and never invokes a coverage-widening path. `_page` preserves arbitrary action records and their other-security fields. Therefore a resolved requested security is not sufficient evidence that every retained observation concerns only that security.

With BBB reserved, the probe makes an AAA action request and returns a fake page containing a BBB cash-dividend record within the reserved interval. The raw page is classified as AAA with unknown dates; invalidations remain zero. A subsequent ordinary `read_bytes` returns those BBB bytes. The acquisition itself returns `pending`, due to C4 below; that outcome does not undo the already published, incorrectly classified page. A contrasting bars wrong-symbol response invokes the existing widening path and produces one invalidation, showing that the fixture can observe the intended conservative mechanism.

**Required:** derive conservative action response coverage before ordinary publication/classification, including malformed/unknown records and multi-security actions. If full security coverage is unresolved, retain unknown coverage and invalidate conflicting preparation protection. Process dates still must not become economic dates. Do not treat request-symbol equality alone as evidence that mergers, spin-offs or other multi-party records disclose no other security. Extend producer and independent cases to malformed responses, other-security records and mixed participants.

### C3: fresh generic imports leave no reservation-conflicting observation

Frozen `Provenance._publish` at `provenance.py:463–498` routes deduplication through guarded reads, but its new-file branch publishes arbitrary bytes without recording a control intent, exposure or conservative unknown coverage. Bootstrap's legacy marker does not cover bytes written afterward.

The probe bootstraps an empty controlled root, publishes an invented BBB observation with `put_json`, and then successfully reserves BBB's overlapping interval. There are zero control intents. The returned reservation still correctly says `protected_eligible=False`; nevertheless its claimed preparation overlap accounting omitted an ordinary import that the accepted contract requires it to consider. The producer's `test_denied_read_never_opens_unclassified_bytes` explicitly permits a reservation after such a write and therefore cannot test this property.

**Required:** account for generic publication/import conservatively before it can coexist with conflicting preparation reservations, including dedup, raced publication and uncertain outcomes. Trusted producer outputs may carry narrower, evidence-bound coverage through a separate controlled path, but callers cannot obtain that path by selecting metadata. Preserve unknown/import exposure after rollback or failed publication where access may already have occurred. Test both publication-before-reservation and reservation-before-publication, plus a genuinely disjoint known producer path.

### C4: final acquisition receipt lacks coverage, so unrelated reservations break permitted acquisition

Frozen `alpaca_data.py:595–600` and `alpaca_actions.py:260–265` publish the final receipt without binding its coverage, then `Provenance.finish` verifies it through a mandatory read. That read sees unknown coverage and conflicts with every existing reservation, including one that is demonstrably disjoint from the allowed acquisition.

The positive fixture reserves BBB, then obtains valid invented AAA daily bars through one fake request. Its requested/actual coverage is AAA and no invalidation occurs, but the return is `pending` / `storage_unavailable`; the control history contains an unknown-content reservation refusal. A working intent-level non-overlap predicate does not establish a working end-to-end allowed acquisition.

**Required:** assign the final receipt a supervisor-derived conservative coverage/lineage before its mandatory read, including any widened response uncertainty, without restoring arbitrary caller classification. Require successful end-to-end bars, calendar and actions receipt publication for valid compatible scopes, as well as unchanged refusal for incompatible or unknown coverage. Do not solve this by suppressing final artifact verification.

## Executed evidence and limits

The first three-case probe passed the generic-import and bars-control observations, but its action case incorrectly expected a successful acquisition instead of the actual `pending` outcome. That harness assertion failed; the original script/output are retained. A distinct four-case v2 corrected the expectation, verified readable cross-security raw bytes and added the valid-disjoint receipt check; all four finding reproductions passed in 0.125 seconds. A distinct v3 added the direct `bind_object` bypass; all five finding/control reproductions passed in 0.294 seconds. These “passes” reproduce defects and one positive control; they do not certify the product.

| Artifact | SHA-256 |
| --- | --- |
| Original v1 probe | `6001a399ef7356e8ecec5f2605096b78e70ef476a66367e64f9aba046fe30e4e` |
| Original v1 output, including harness failure | `0900f7c48c3ff91b62bcbabda8846f080510ef8db4261fcfb54ae31b1d581a52` |
| Corrected v2 probe | `5ab24104283b1bd683a52395ed16a41fa3ea8d0f48e5793307054b25b4fd16e6` |
| v2 output | `c983a871cf926511cfc3c004e0c9c4b25348a1ef96b1e64f32802bde63f6a0bd` |
| v3 five-case probe | `28151c206f239b04d03f264877ca46f9d27703b14c582e580c3f5e0a2ebc0126` |
| v3 output | `7b14048eeaf52356d2afbde2695eec8f296b23e41f3c2a50e00631c849585031` |
| v3 bounded observations | `0955cbe3f03840c642f072f13cac753e8d5d3a1a8f87ab24599e55bf5a4615c2` |

The producer's 237 focused final checks and earlier 1,089-test integration result remain separately attributed, not rerun or claimed as independent evidence here. This criticism used targeted reproduction instead of duplicating the separate quality run. No clean-install/full-suite acceptance is claimed. Frozen D009 files and unrelated root work were not changed.

The source also shows the intended guard order and durable starts, append-only private records, conservative action time semantics, principal/revision checks and mandatory raw helpers. Those mechanisms are useful but do not neutralize the reproduced publication/classification defects. Broader evaluator isolation, real legacy reconciliation, cross-process rollout, complete multi-store recovery, release scheduling, statistical planning and actual protected-pilot evidence remain outside this preparation increment. The cooperative application threat model is preserved; no malicious-owner or arbitrary Python-memory isolation claim is substituted.

A corrected exact revision needs independent retesting of these four findings and relevant positive paths before this critic can clear the increment. Current disposition: **changes required**.

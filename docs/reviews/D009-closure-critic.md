# D009 closure subset: independent implementation criticism

**All three reproduced findings are closed at corrected product SHA-256 `3618457a9170f0533efe0b4081478a3662dfd7f6031525dce24f488a28cd8981`; no remaining code blocker was found within this bounded structural subset.** The initial source, objections and outputs remain preserved below. Separate quality and scope acceptance are distinct; actual payload coverage, complete closure, replay and recovery are not accepted here.

Reviewer: `/root/d009_v2_critic_finish`, separate from the producer and execution-quality reviewer. Contract: corrected closure plan SHA-256 `5e7d52797e62224aaf8c4b22fccf72b76995566927ac47529701c2f2b984df9f`, with separate contract criticism in `D009-closure-contract-critic.md`. Initial frozen product: `src/quanto/recovery_closure.py` SHA-256 `a3d48b4d09867c237b1ff79c96d9d4dde21c6449ab4367473e25e5bf70a122ef`; producer tests SHA-256 `4bd80d2ae5a25688f11501d27eff6899b3a18c4ccd52a07525329756de28c4bc`. Exact byte copies were retained before correction as `runtime/recovery-closure-critic/initial-closure.py` and `initial-test-closure.py`.

I inspected public source and executed only synthetic temporary-store probes after receiving that exact freeze. No actual candidate, research payload, production database, account, key, credential, private runtime receipt or financial result was read. No provider/network call, council, research replay or actual capture occurred. Synthetic fixture construction used existing local storage code; the capture product itself was not modified or independently re-certified here. I did not run the producer tests or count their reported passes as my own.

## P2, closed: generic ledger dictionaries are not typed evidence records

`Journal.finish_attempt` accepts arbitrary bounded finite JSON as its result, and `record_review` accepts arbitrary bounded finite JSON findings. The initial closure root extractor nevertheless assigns external-reference meaning to any non-explorer outcome dictionary containing `artifact_sha256`, and to any review-findings dictionary containing `report_sha256`, before establishing the corresponding producer/shape.

Independent probes reproduce both consequences. A legitimate generic failed outcome containing `{"artifact_sha256":"ordinary note"}` and a generic review containing `{"report_sha256":7}` refuse with `invalid_reference`. Replacing each value with an arbitrary valid64-hex string makes the report accept and invent an external-evidence edge from that metadata. The value's spelling has supplied authority that the origin-bound contract requires from a recorded producer. Scope independently identified the same source issue; these executions were this critic's own probes.

Required correction: interpret those fields only under a recognized recorded outcome/review origin and its supported shape. Unknown generic dictionaries, like generic scalar/list values, remain unsupported metadata without induced edges or malformed-reference refusal. The review row's separate `artifact_hash` is different: the ledger enforces its digest form. It can remain an unresolved reviewed identity without claiming that it is an available object or that generic findings describe an external report.

## P2, closed: JSON depth does not bound graph traversal depth

The worklist initially carries only `(digest, role)`. `ClosureLimits.depth` is checked while walking one decoded JSON value, but no graph-hop count is propagated when a dataset points to its parent.

My fixture creates nine valid-shape dataset documents linked through `parent_dataset_sha256`, sharing the same source and bar wrapper, with only the newest dataset registered as a root. Each document's own JSON nesting is below4. Inspection with `depth=4` accepts all nine dataset nodes. Node and edge caps still bound aggregate work, so this is not a claim of unbounded execution; it is a failure to enforce the agreed traversal-depth dimension.

Required correction: make graph hops an explicit separately validated limit and track a deterministic root distance while preserving role-aware visitation. Check the exact boundary and an over-bound chain; repeated visits/cycles must terminate rather than accumulating fictitious hop depth, and an opaque-role visit must not suppress a later typed-role visit.

## P2, closed: late source checksum does not bind loaded implementation

The report initially computes `inspector_sha256` using `Path(__file__).read_bytes()` only at return. The lead raised whether that accurately binds the implementation used. An independent disposable-copy probe loads the exact frozen module, changes only that owned copy's executable `PROFILE` assignment on disk from v1 to v99 without reloading, and then inspects a synthetic candidate. The report still uses loaded profile v1 but its inspector digest identifies the changed v99 source. A separate first probe also confirmed that the loaded function code object remained unchanged after an on-disk update.

This finding affects exact-revision attribution, not the demonstrated integrity of the candidate bytes and not historical financial replay. A raw source checksum is a legitimate observation when named as such; it is not proof that those bytes produced the loaded functions and constants. The current `recovery` dependency's loaded behavior is also absent from that single-file attribution.

Required correction: distinguish raw source identities from a pure loaded-code/default/constants identity for both the closure inspector and its recovery dependency, record the relevant runtime facts, and check the stated stability boundary. Do not require historical research artifacts to match today's source or turn this implementation identity into a replay claim. The code must remain inert and the public projection must continue to expose only bounded identities/counts/flags.

## Retained independent evidence

| Artifact in ignored `runtime/recovery-closure-critic/` | SHA-256 |
| --- | --- |
| `initial-closure.py` | `a3d48b4d09867c237b1ff79c96d9d4dde21c6449ab4367473e25e5bf70a122ef` |
| `initial-test-closure.py` | `4bd80d2ae5a25688f11501d27eff6899b3a18c4ccd52a07525329756de28c4bc` |
| `probe-initial.py` | `1450596ad0dac08af73225fdef18da3b5256d1ab7250cc4338cef9d567a057c4` |
| `initial-output.txt` | `10665a4e32fa9221fff14bb0218b88181bfc878696705ea02fea0d1d20922863` |
| `probe-source-identity.py` | `7e52e4c9fd83367ee3deef497bceba8d948892f6c5cc295b579c0612cdef76c2` |
| `source-identity-output.txt` | `ebef0133cca7034392b37aa909f94c10d0e783c9eb9cf8a3670eb70ce37fac6d` |

These are `synthetic_fixture` observations and source-copy experiments. The initial probe covers two malformed-origin values, two digest-shaped generic values, a parent-chain depth case and a loaded/source identity case; the stronger second source-copy probe changes an executable profile constant. No claim is made that these probes certify every profile or replace separate execution quality.

The producer received the reproductions and prepared an authorized corrected freeze. The original source/test bytes and findings remain preserved. The corrected-source recheck follows; no actual inspection, upload, complete closure, historical replay or recovery has been accepted by this report.

## Corrected-source inspection and independent rechecks

I inspected the corrected product at SHA-256 `3618457a9170f0533efe0b4081478a3662dfd7f6031525dce24f488a28cd8981` and producer tests at `2ba696117cd60c503f642fbb739ec28386688c223b04a3503952e07db6c20e57`. Exact byte copies were saved before further changes as `corrected-closure.py` and `corrected-test-closure.py` in the ignored critic directory. No product or test file was edited by this critic.

The origin correction leaves unrecognized ledger outcomes and review findings unsupported without scanning their arbitrary dictionary keys. The separate ledger-enforced review `artifact_hash` remains a recorded identity, rather than an inferred available object/external report. My text, integer and digest-shaped generic metadata cases now all return incomplete coverage with no invented file edges. Zero supported nodes remain reported as zero, and `supported_profiles_verified` is false in both the private report and public projection. Generic findings, including any future outside-report shape not yet supported, remain explicitly unparsed evidence; the correction does not claim that external audit requirements are satisfied.

The traversal correction introduces `graph_hops` independently of JSON `depth`, with all recorded roots at hop0 and breadth-first shortest distances keyed by digest/role. My nine-document parent chain now refuses at graph limit4 and accepts the exact eight-hop boundary. Adding a second recorded root in the middle allows that same graph at limit4, retains deterministic output, and visits the shared bar-wrapper role only once. Repeated role encounters do not inflate hop distance, while distinct roles remain separate checks.

The identity correction records separate raw-source and loaded-code identities for the inspector and `recovery` dependency, plus Python/implementation/SQLite/marshal-version facts. The loaded fingerprint covers owned functions/classes, code/defaults/closures and declared constants, and normalizes code filenames. Import-time raw-source pins and before/after loaded-state comparisons close the demonstrated late-checksum misattribution. They are cooperating-process identities, not hostile same-process or operating-system attestation, nor proof of a reproducible historical environment.

My disposable inspector and dependency copies now each refuse a source edit after import with `implementation_source_changed`. Changing a loaded inspector constant before a call changes its loaded identity while its raw-source and dependency identities remain unchanged. A loaded constant changed during inspection refuses with `loaded_implementation_changed`. These cases use only owned source copies or temporary process-local instrumentation; the frozen product files and actual application state were untouched.

The retained `probe-corrected.py` reports nine focused cases: three generic metadata variants, over/exact graph boundaries, a second-root shortest-distance case, separate inspector/dependency source-drift cases, a pre-call loaded-constant identity case and a during-call loaded-state refusal. It completed successfully with every assertion passing. This is my defect-focused execution, not a run of the producer suite or an independent native Python3.11 qualification; the separate quality reviewer owns those broader checks.

Source inspection also confirms the accepted remaining boundaries: exact stored `workflow_broker_*` event names supply pending roots; unknown families/versions are incomplete while recognized malformed structures refuse; role-based leaves do not interpret vendor/model tags; inline request hashes are checked without demanding standalone files; historical availability inside unsupported failure-basis records is not promoted into live object obligations; the original snapshot is checked before and after traversal; and all full-closure/recovery/replay/execution flags remain false. The public projection excludes private graph origins, field values and payloads.

| Corrected artifact in ignored `runtime/recovery-closure-critic/`, except product paths | SHA-256 |
| --- | --- |
| `src/quanto/recovery_closure.py` / retained `corrected-closure.py` | `3618457a9170f0533efe0b4081478a3662dfd7f6031525dce24f488a28cd8981` |
| `tests/test_recovery_closure.py` / retained `corrected-test-closure.py` | `2ba696117cd60c503f642fbb739ec28386688c223b04a3503952e07db6c20e57` |
| Independent `probe-corrected.py` | `375ee0804f161835e0b5cad2f540d0ac04d605f67f74ce2060198c5bc41b72b1` |
| Retained `corrected-output.txt` | `f9118e45e5ac29b942d921c32db7543e99b8ce3d3a64ae810fe6052979550348` |

Hashes were checked after the rechecks. The frozen capture implementation/tests were not changed or re-certified by this review. Unknown nested profiles, historical source/environment bytes, external audits and custody/transfer/restore evidence remain required future work. No actual candidate was inspected and no operational authority was revived.

## One-shot existing-candidate controller: static review

**No controller-source blocker was found at `runtime/recovery-closure-actual/inspect-existing-snapshot.py` SHA-256 `6857ce823c4028eb7ec215768901b33715d6c0fdf2334a16fa16ed4505cd1bc6`.** I read and hashed only that explicitly permitted operational source. I did not execute it or read its pinned private receipts, destination, graph, candidate bytes, credentials or keys.

The controller pins the final closure source/tests above, unchanged capture source `5f7f2526da8d82d5f648c42a3135af3f44dadbafe0be2f40e8888b923d856883` and tests `6edb1e99f37f28eda64fcbe233c12693ae4fd5917130edda63663cff081a0e8a`, and exact earlier capture-result/destination receipt digests. It validates the prior verified status, fixed manifest/head and expected sibling destination shape before exclusively consuming and fsyncing a new attempt. Those private receipt identities are supplied by the lead and checked by the source; they were not independently inspected by this critic.

After installing ordinary socket/name-resolution refusal guards, the controller invokes only the read-only closure API once, bound to the fixed expected manifest and event head. It requires incomplete status and false full-closure/recovery/replay/execution flags, rechecks all pins and its own source, then writes a bounded mode0600 private graph and a separate safe result. Displayed output comes from the fixed public projection plus lifecycle/digest/flag metadata; raw graph origins, payloads and private destination paths are excluded. An existing attempt/report/result/failure refuses, and failures retain consumed intent without retry, capture, upload or replay.

The lead specifies a minimal PATH/LANG/LC_ALL environment, absolute isolated-Python invocation, disabled stdin, exclusive private stdout/stderr and a120-second launcher timeout. This review does not attest that launcher execution occurred. The socket patch is a defensive application guard, not a network boundary against arbitrary replacement code. Actual inspection remains contingent on separate final quality/scope acceptance and the lead's authorized launch; this static disposition supplies no stronger recovery or operational approval.

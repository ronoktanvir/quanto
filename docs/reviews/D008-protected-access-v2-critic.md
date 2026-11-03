# D008 protected-access v2: independent criticism

**Changes are still required.** The corrected candidate closes the four original reproduced paths, but malformed pagination metadata can still retain narrow security coverage, and rejected generic inputs can escape exposure accounting. A separate lifecycle check also shows that an already-issued publication permit survives its intent's terminal rejection. These are synthetic preparation-boundary findings; no actual protected observation, provider request or trading result was involved.

Reviewer: `/root/access_v2_critic`, separate from the producer, quality and scope roles. I verified frozen manifest `db655d591229db3bb0f75ef9e90018fd967e09ea50b09069b856fdfc6c65f1a6`, exported public base `45053742d0f7cca1a68a237781cd81c347648246`, and overlaid only its 24 exact source/test files. The isolated export and invented probes are retained under ignored `runtime/protected-access-v2-critic/`. All imports were checked against that export. Socket connection/resolution calls were disabled; fixtures used fresh resolved temporary roots, synthetic authorities, invented credentials and fake transports. No actual project store, recovery candidate, key, model, provider or financial calculation was accessed. Only this report and ignored synthetic evidence were written.

## Exact inspected candidate

| Artifact | SHA-256 |
| --- | --- |
| Frozen 24-file manifest | `db655d591229db3bb0f75ef9e90018fd967e09ea50b09069b856fdfc6c65f1a6` |
| Producer contract | `2a308335e4385741ee45b330630013f04d9c2cd431718ea48f3386fda376c525` |
| `evaluation_registry.py` | `c75c224f60d5b922592ffd4367bff90f97b8a50ae4dfa16fd08cf204da2ade11` |
| `provenance.py` | `e4dd618f573e27cf3a1f9dbd9ee422f5f21b13f514e73218059210f85187c55b` |
| `alpaca_data.py` | `4cc3f6d40b2d050483c5be898b606f8373792484be4cbb0a12b8eb80fb14da16` |
| `alpaca_actions.py` | `7383bd169d55d4500f8a7ee756b7d80057e6842a7c6f8a18d136155f673d0453` |

All 24 exported identities still matched after the probes. The prior [v1 critic report](D008-protected-access-critic.md) and its original objections remain separate historical evidence. The producer's 261-test result is attributed producer evidence, not this reviewer's execution or a full-suite pass.

## Corrections independently reproduced

Ordinary `bind_object` now refuses and cannot make an unrelated existing digest readable. A foreign-security action response widens coverage, invalidates the conflicting reservation and cannot be retrieved through ordinary publication. Valid generic imports are recorded as consumed before a later reservation; publication after a reservation refuses while its exposure survives research rollback. Valid disjoint bars, actions and calendar acquisitions now publish receipts that pass their mandatory reads. These checks close the original C1–C4 witnesses on this exact candidate.

Additional positive probes confirm that absent or unrelated response origins cannot obtain response/normalization permits, and a fabricated publication label cannot hide an already supplied observation. The administrative `Supervisor.producer` method remains a trusted supervisor operation, not an ordinary worker capability. This review does not reinterpret Python object access as hostile-process isolation.

## C5: malformed pagination metadata bypasses response-coverage widening

At `alpaca_data.py:460` and `alpaca_actions.py:110`, the coverage observers require the `next_page_token` field but do not validate its value. Both paths can accept an object there, even though the later acquisition loop requires a bounded token string or null. Raw response publication occurs before that later check.

The independent witness reserves invented security BBB, requests disjoint AAA, and returns an otherwise valid page whose token is an object containing an invented BBB observation. Both bars and actions classify the raw page as AAA. Their acquisitions subsequently fail pagination, but an ordinary content read still returns the raw bytes; there are zero widenings and zero reservation invalidations. A direct `_dispatch` call without a publisher also returns the malformed response without widening. No arbitrary supervisor classification, private-attribute mutation or actual provider data is used.

**Required:** validate every response-envelope field needed to justify the finite scope, including exact nullable token type and accepted token bounds, in the mandatory coverage observer before raw publication or return. Any unsupported envelope must widen to unknown. Keep later pagination completeness/repetition checks; they serve a different purpose. Add bars/actions regressions for object/list/boolean/numeric/invalid-string tokens, direct dispatch and the raw HTTP boundary, alongside valid null/string controls. This is access classification, not permission to infer new financial semantics from malformed responses.

## C6: validation rejects supplied generic observations before accounting for them

`Provenance.put_bytes` at `provenance.py:452` checks type/size before reaching `authorize_publication`; `put_json` at line511 serializes before reaching that boundary. Consequently supplied observations that fail those preliminary checks have no `content_import` intent or effect. The v2 contract explicitly says already supplied bytes remain observations even when publication refuses.

One witness passes a byte value one byte above the existing 16 MiB limit. Publication correctly refuses, but a subsequent overlapping reservation succeeds with zero intents and effects. The reverse order also leaves the existing reservation uninhibited, with zero invalidations. Another witness supplies an invented observation in a JSON value containing NaN; serialization refuses, then the reservation likewise succeeds with zero exposure records. These witnesses do not require storing or retaining the rejected content. They show that publication validity and prior observation are currently conflated.

**Required:** retain a bounded conservative unknown observation when an ordinary input has already reached the import API but cannot be validated or encoded. Do not weaken artifact limits, serialize unbounded invalid values, store rejected payloads, or classify such attempts as rejected-before-access. Use the valid installed authority/control journal and preserve the record across research rollback. Test both reservation orders, malformed JSON, oversized bytes, deduplication and failed publication while retaining the valid producer path's exact lineage. Missing or unsafe control authority still must refuse and cannot invent a durable record.

## C7: terminal intent rejection does not fence an issued publication permit

`PublicationPermit.consume` at `evaluation_registry.py:918` rechecks principal, revision, current coverage and one-use publication state, but not the originating intent's terminal state. An independently constructed valid request publication permit can be issued, followed by `intent.reject_before_access()`, and then successfully consumed through `store.put_bytes`. The control store records both `rejected_before_access` and a completed publication/classification from that same intent, with no effect starts.

The witness publishes only the reconstructed request document; it does **not** establish a market-data exposure escape. Its consequence is narrower: terminal rejection fails to revoke previously issued authority, contradicting the one-lifetime capability contract and leaving inconsistent lifecycle evidence.

**Required:** atomically recheck the current originating intent's issued/open state when consuming publication authority, including rejection after permit issuance. Preserve the existing conservative fallback for bytes already supplied through an invalid permit. Add a race or deterministic interleaving test and retain successful publication for an unchanged open intent. No broader administrative authority is needed.

## Executed evidence and limits

The first independent script ran nine test methods in0.398seconds; two methods exercised bars and actions separately. A second script ran five additional methods in0.190seconds. All assertions passed without a failed or corrected harness run. Some assertions deliberately reproduce the defects above; these passes are evidence of findings, not product acceptance. The original probe files and outputs were not overwritten.

| Evidence | SHA-256 |
| --- | --- |
| First probe script | `f6c8399beed7112d43bc3fd2faa8414221d1bb2931ffb385b7329467da42c4a0` |
| First output | `0795ede6809b7d5725278167239c03cdc4ffdb941d3d3a4db0775bdaeb469dc4` |
| First bounded observations | `683dc96207b305f4d964cb06e570ec9b4067c41df9f86c08916c6fb8fe4bebb3` |
| Additional probe script | `a3ef5558eaa80e34608caf7211884af14ad1154104d810490a016c25bef32290` |
| Additional output | `59ee2f565c88e4b3708e4d36416236ca44b8fb213366f44f702107c25ff9f714` |
| Additional bounded observations | `36ef3a77f441bfab983c56cbbab76ae97736eeb82f8feaaf1c467f797df45f43` |

This review used direct dispatch and public acquisition/content routes. The raw HTTP response path was inspected in source, not separately executed here; its coverage observer shares the missing token check. No clean-install or full integration suite is claimed. Actual protected eligibility, legacy reconciliation, process isolation/rollout, multi-store recovery and persistent research operation remain incomplete regardless of these fixes. A corrected frozen revision requires fresh independent retesting before criticism can clear the increment.

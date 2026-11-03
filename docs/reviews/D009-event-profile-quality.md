# D009 event-profile compatibility: independent quality record

Initial candidate acceptance is withheld. The packet-origin selector passes the independent cases below, but the separate failure-basis event bypasses that selector and does not distinguish an impossible known legacy producer/event pair. This contradicts the compatibility scope's explicit requirement for that event family. No actual candidate or closure result is accepted by this review.

Reviewer: `/root/recovery_actual_quality`, distinct from the producer and implementation critic. Tests use invented local event/object stores only. I read the public compatibility plan/scope and frozen source, not an actual recovery candidate, private receipt, market payload, key or account. No provider/model/network call or financial replay occurred. Product/context/Git files were not changed.

## Initial frozen candidate

The source is `1c9dcdec2a8f03fee27fd16d19eff0149197c71192e369875b8d163f9d4a2e06`; producer tests are `8bc3a84ebebbcd8f6ed5986ff4f4efadc418b3b8e184191fb721f0b352616af7`. I verified the supplied isolated export and created a separate public Git export of baseline `1fe9ffa2cdffb5a33aa3e9b165e09c5997232b18`, overlaying only those two files. Changing D008 work is excluded. Python 3.13.12 exercises that source; fresh Python 3.11.9 uses a noneditable offline installation of the same export. Socket guards block external network in the fixtures.

Both runtimes executed 21 independently authored cases: **20 passed and one failed**, in 0.51 seconds on source and 0.49 seconds in the clean installation. The passing cases cover both exact legacy broker identities and the current broker/workflow pair, pending-event roots, current-key downgrade attempts, nullable/mandatory fields, metadata types, configuration-row/code-hash contradictions, unknown or missing origin, missing required bytes, configuration/packet tombstones, JSON bounds, inert constructor behavior, unchanged snapshot bytes, recorded source/loaded identities and safe-projection omission of private synthetic values and references.

The failing case binds a synthetic failure-basis event to a configuration and broker-run row recording the exact older `038714` producer, which did not emit that event family. `roots()` sends this event through generic `EVENT_REFS`, never calls producer selection, and returns only generic deferred-semantic/unsupported-role gaps. It emits neither a refusal nor an explicit unresolved/impossible producer-profile gap. The report retains false full flags, so this is not a false full-recovery claim; it is a missing structural distinction required by the accepted finite correction.

Required correction: apply an origin-aware contract to the separate failure-basis event. A known legacy origin must not silently borrow the newer writer's profile. Known current events must retain the documented required references and metadata; unknown/unavailable origin must remain explicitly unresolved. Preserve the existing reference, tombstone, bounds and inertness safeguards. A revised exact freeze needs independent positive/current, incompatible/legacy and unknown-origin checks before acceptance.

The broader producer suite has not been independently rerun for this rejected initial candidate. No broad pass or actual graph is implied by its producer-reported 131 tests. Setup command path/PATH mistakes occurred before clean package installation; they were corrected locally, with no network fallback or product change, before the recorded clean test execution.

## Retained initial evidence

Synthetic exports and outputs are retained in the quality-owned temporary directory ending `quanto-d009-event-quality-gzgnr___`. Earlier failure output is preserved for comparison with any later correction.

| Artifact | SHA-256 |
| --- | --- |
| Initial independent probe source | `4679448638036e8df60490630f0ff662008036e9024d4c54284c94e0ff799639` |
| Source initial output | `906d08fda5ad9c2f11b9068fcc81f0e6ce644d8d0ed454483413928ccd89d679` |
| Clean initial output | `53b935026020a9161512da82d5a83939fc6ac72980387a9047b8b3335979a458` |
| Frozen baseline receipt | `dbd54d66571d070b0e740e841c5bb51b6fb3f6a982b26c15080ad8d1d3ed4bc4` |

Complete typed closure, historical replay, full/off-Mac recovery, offline availability and execution remain unaccepted. This earlier research-only generation also excludes the future D008 control store; event-format compatibility cannot restore that absent authority history.

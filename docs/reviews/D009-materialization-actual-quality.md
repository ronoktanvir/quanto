# D009 actual materialization: independent safe-metadata audit

The permitted projection is internally coherent and supports the lead's limited acceptance of a local materialized candidate. It reports successful strict byte/database verification of the original pinned generation, while preserving incomplete recovery and execution flags. This review independently audits projected metadata, not the candidate's private content or underlying receipts. The original closure refusal and its unknown cause remain preserved.

## Evidence boundary and identities

Reviewer: `/root/d009_v2_quality_finish`, independent of the lead's execution and receipt checks. The only actual runtime file read was the explicitly authorized `runtime/recovery-materialize-actual/safe-evidence.json`, verified as SHA-256 `3ebaba09dd12442d6c0aff6197e68a66a20dae5dd8a31de3855b4da68a595305`. No private destination, original candidate, receipt payload, account, key or credential was opened. No helper/controller invocation, copy, capture, replay or external call occurred during this audit.

Public identities rechecked:

| Artifact | SHA-256 |
| --- | --- |
| Materialization source | `118783f4790aff9c4bb1f1827d4ed573834afea6acb8f48ffdc0d96ef79f7c01` |
| Materialization tests | `9cc4be2f0baf04644d9857edae79baf6623cb37af64109619cae1999ca30c8d8` |
| Unchanged recovery source | `5f7f2526da8d82d5f648c42a3135af3f44dadbafe0be2f40e8888b923d856883` |
| Clarified contract | `414f9012bbec32bb1f2e723c2343dce9497aae477d0b4843e67a89e38731dcba` |
| Prior independent synthetic quality | `fcce76994458ce37b00e00bc52cbd4cc5f87d96414f5f3ccdd2035e95963a298` |
| Lead controller-review report | `e64a2251922fc9bf82f7a7b17eb9feb74039b356e6be10b69ffe90ef884337b4` |

Controller `e5c0a9d671f69bf461bc83f28d12c5996c621181ad0e93b4f9cd6c57da11f802` appears consistently in the projection's outer, process and result records. This reviewer read the public lead controller-review report; direct controller-source review and one-time execution are attributed to the lead, not performed again here. Prior synthetic test results remain separate software evidence and were not rerun.

## Independently observed projection coherence

The projected process starts at `2026-11-03T02:07:28.270503+00:00` and finishes at `02:10:11.172100+00:00`. Its timestamps span 162.901597 seconds, consistent within about 0.0013 seconds with the recorded monotonic duration of 162.900357 seconds. The inner result records 162.856553 seconds and precedes process completion; the safe projection's observation follows both. Return code is zero, stderr is zero bytes, and no timeout or automatic retry is recorded. The 330-second outer limit, isolated-Python flag and environment-key list of only PATH/LANG/LC_ALL are present in the projection; the launcher itself was not independently observed here.

The configured copy allowance is 300 seconds and verification allowance is 15 seconds. The frozen helper calls the original strict destination inspector with that limit. The total process duration includes copying and cannot measure the verifier's individual elapsed time. The evidence supports a reported verification success under the configured allowance, not a separate reviewer measurement of its duration.

The result reports 40 tables, 229 objects, zero unknown schemas and zero tombstoned dependencies. Its 231 final files equal the 229 objects plus manifest and database. Native destination flags are reported observed on the final files, with zero dataless files. The 226 counted source mtime changes are within the 231 copied source files; this count does not identify an actor, a cloud service or the cause of an earlier failure.

The manifest digest is `d4f6f88495f2337f6edc5f7764b4ddab465e64136b5798f6c98a3a72ccdcd87e` and event head is `f5d63033df2295da89984e76420c92e83b5ee54383214f96fbcf2c0ef440bbc2`, matching the original generation identified in the public capture/closure history. The result's intent digest equals the projection's `attempt.json` digest, and its destination-receipt digest equals the projection's `destination.json` digest. All five projected receipt hashes have the expected digest form. These are internal reference matches, not independent hashes of unopened receipts.

All six projected acceptance checks are true: clean launcher outcome, current source pins, exact intent/destination/result bindings, new private Application Support destination, no failure/pending receipt and stdout/result agreement. The lead reports separately verifying their underlying artifacts. This audit confirms that the projection says so and contains no contradictory count, timing or reference; it does not independently reproduce those private checks. In particular, destination placement, modes/ancestry, durable publication and stdout equality remain lead-attributed.

## Accepted claim and remaining limits

The projected success flags are snapshot bytes, database integrity, event chain and known database references. Six omissions remain. Unknown-schema count zero does not imply complete nested evidence coverage, historical replay or restored authority. Closure inspection was not invoked; this staging result supplies no dependency graph or coverage result.

Full recovery, typed closure, off-Mac recovery, historical replay, financial/model replay, execution, production recapture, upload, automatic retry, source-path stability, offline availability and original-failure-cause establishment all remain false. `filesystem_retrieval_possible` remains true. Zero observed destination dataless flags is a bounded observation at that time, not a promise of future residency or proof that OS-mediated retrieval/synchronization never occurred.

The projection reports the outer acceptance checks required because a hard kill or failed marker/result write can leave a byte-valid layout without a successful operation receipt. The local acceptance follows the lead's retained intent/result/process checks; it does not follow merely from directory presence or absence of a failure marker. This audit found no metadata contradiction requiring reversal of that limited acceptance, while leaving those private checks explicitly attributed.

The earlier actual closure attempt remains failed with no dependency report; `original_failed_attempts_superseded=False` and `original_failure_cause_established=False` preserve that history. A successful separate copy and destination verification do not retroactively explain or erase its refusal. Required source/audit evidence, selected-use rights, permanent key/account recovery, encrypted off-Mac transfer/restore, future D008 control-store consistency, freshness/effect barriers and complete Stage B/C acceptance remain open.

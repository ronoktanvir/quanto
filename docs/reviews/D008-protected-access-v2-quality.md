# D008 protected access v2: independent quality record

The frozen v2 candidate passes the bounded source and clean-install checks below, but **quality acceptance is withheld**. Separate criticism reports remaining exposure and authority defects: malformed pagination tokens in provider responses, oversized inputs rejected before import accounting, and a prepared-request publication permit that remains usable after its intent is rejected before access. Passing the durability and publication tests here does not close those routes. Full compatibility and protected operation are not established.

Reviewer: `/root/access_v2_quality`, separate from the producer, active implementation critic and scope reviewer. All executions used invented stores, fake responses and credentials, and isolated public-code exports. No project store, private market artifact, actual account credential, provider/model request, protected acquisition or trade was accessed. Only this report and ignored synthetic quality artifacts were written; product, D009, context and Git files were not modified.

## Exact subject and isolation

I directly verified all 24 files in producer manifest `db655d591229db3bb0f75ef9e90018fd967e09ea50b09069b856fdfc6c65f1a6`, then exported committed baseline `45053742d0f7cca1a68a237781cd81c347648246` and overlaid only those frozen bytes. The contract is `2a308335e4385741ee45b330630013f04d9c2cd431718ea48f3386fda376c525`. Key source identities are registry `c75c224f60d5b922592ffd4367bff90f97b8a50ae4dfa16fd08cf204da2ade11`, data adapter `4cc3f6d40b2d050483c5be898b606f8373792484be4cbb0a12b8eb80fb14da16`, actions adapter `7383bd169d55d4500f8a7ee756b7d80057e6842a7c6f8a18d136155f673d0453` and provenance `e4dd618f573e27cf3a1f9dbd9ee422f5f21b13f514e73218059210f85187c55b`.

Source execution used Python 3.13.12. A fresh Python 3.11.9 environment received an offline, noneditable installation of the exact export. Committed public documentation, including D007_POLICY, was included before tests. The runner explicitly selected source versus installed module locations, used a minimal environment without project keys, and rejected non-loopback DNS/socket access. These selected tests use fake transport; the process-crash probe performs only synthetic control operations. All 24 exported paths and six installed source modules still matched the frozen manifest after execution.

The previous quality temporary directory was absent at this resumed check. Its historical report remains evidence of that prior review; I did not claim to rerun or reuse its 12 probes. This review created 16 new independent cases and retained their source under the current ignored quality directory.

## Executed checks

The new cases exercise externally observable persistence and authority boundaries:

- A separate read-only SQLite connection sees committed effect-start before the physical object open. Same-instance verified-byte reuse causes no second open.
- A failed start-audit write prevents fake transport while the issued intent still blocks an overlapping reservation.
- A real child process exits immediately after committed effect-start. Reopening preserves the unterminated effect and conflicting exposure; this is process-crash evidence, not power-loss or external freshness evidence.
- Principal revocation prevents cached bytes from being returned. Generic input supplied after revocation still leaves a consumed import observation even when publication refuses.
- A refused unknown import invalidates an existing reservation and remains recorded after rollback of the separate research transaction. No object is published.
- Replaying a consumed publication permit refuses and records the newly supplied input. Substituted bytes cannot acquire the permit's classification. A permit issued before response coverage widens cannot later publish under its former narrow coverage.
- Direct dispatch of an HTTP error, an invalid transport object or unreadable JSON preserves unknown coverage and blocks a disjoint-security reservation. These cases do not cover every malformed field inside otherwise parseable JSON.
- A used access intent cannot be rejected as unseen. Two threads attempting the same exact effect reach only one fake transport. A prepared permit from a closed session cannot dispatch.
- A denied valid query publishes no requested symbol, date or principal into ordinary research SQLite/object output. This is one disclosure route, not certification of all invalid-input or future evaluator-release routes.

| Execution | Observed result |
| --- | --- |
| Initial independent source probes | 16 passed in 0.46 seconds |
| Source producer selection plus independent probes | 277 passed in 32.32 seconds |
| Clean Python 3.11, identical selection | 277 passed in 33.16 seconds |
| Ruff on the 24 frozen producer paths | Passed |
| Post-run exported and installed identity checks | Exact matches |

Each 277-case run includes the producer's 261-case selection plus the 16 quality-owned cases. The source and clean runs used separate invented temporary stores. No failed or corrected quality test/setup run occurred in this review. These checks establish software behavior on synthetic fixtures, not financial performance, unseen evaluation or successful production operation.

## Unresolved criticism and integration

The active critic separately reported that an object-valued `next_page_token` can carry foreign-security content without widening a bars/actions intent, and that oversized `put_bytes` input can be rejected before durable exposure accounting, permitting a later overlapping reservation. A later supplemental critic probe also reports that a prepared-request publication permit can still be consumed after `reject_before_access` closes its intent. These are critic-attributed findings on the same frozen source, communicated during this review; they were not executions performed by this quality reviewer. They require corrected exact identities and independent rechecks. The producer's passing selection and the 16 cases above do not override the findings.

The lead subsequently prepared explicit synthetic-session adaptations for the two D009 test helpers. I retained their exact supplied bytes separately: `test_recovery.py` hash `c8ad8db88dbd89531572c03180132e2065d348ae5eb346ea503d67a0cecdaf3b`, and `test_recovery_closure.py` hash `7fcbdd4f07a6d72ff76808840755c2f95700a47c4b1f42cc2249d4734e727359`. They were not overlaid into this frozen-v2 check. The lead's 136-case fixture result is not counted as my execution. A full compatibility run is deferred until the product blockers are corrected and the combined candidate is frozen; no full-suite or CI pass is claimed here.

Legacy reconciliation, global deployment binding, old loaded processes, administrative readers, evaluator isolation/release, multi-store recovery and external freshness remain incomplete. The separate control database's persistence against ordinary research rollback does not prove externally anchored newest state. This increment grants no actual protected eligibility and closes neither R13 nor R14.

## Retained evidence

The ignored directory `runtime/protected-access-v2-quality/` retains the exact export, clean installation, independent fixtures, runner and outputs. Its `quality-evidence.json` has SHA-256 `0ddaa2eb3d3abd0b9ae18da36852ea40a321601f95589c47a4c954ec48502851`.

| Artifact | SHA-256 |
| --- | --- |
| Independent probe source | `2b2880f1077218bd6eb2b26ff8890af8912a857b2e5250b71238860a66559f10` |
| Isolated runner | `addc86adb252b00c65f48fd000b63d75a826e8dc5e7ebca0d509a2786f0ff503` |
| Source selected output | `de6edf5fb07397d87c71e8710de0ed3c34227238b0398ce774e1b1e41110dde7` |
| Clean selected output | `cc16549b395f93c8c847a9f32d9f573a0b96ef4d06a677536a76f35c018d7763` |
| Ruff output | `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` |

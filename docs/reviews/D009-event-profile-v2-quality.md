# D009 event-profile compatibility v2: independent quality acceptance

The corrected finite event-profile increment passes the required quality checks. Its shared producer selector now rejects a failure-basis event bound to either documented legacy writer, preserves the current writer's exact reference/metadata requirements and reports unknown or unavailable origin explicitly. This closes the independently reproduced v1 defect without weakening current packet validation. Acceptance is limited to this software increment; no actual recovery candidate was inspected and no complete closure or recovery is certified.

Reviewer: `/root/recovery_actual_quality`, distinct from the producer and implementation critic. All tests used invented stores/events/object bytes in separate exports. No production data, actual private receipt, credential, account, provider/model call, financial replay or network access was used. Product/context/Git files were not edited. The separate [v1 quality record](D009-event-profile-quality.md), SHA `464783b0c17163b5e1461d3842ef8f021b14bd3ee494fbbecf8c9a9458d09cb2`, remains unchanged with its failing evidence.

## Exact subject and execution

The corrected closure source is `a20c21dbbc72f5931622f54218c1400e837f7eaa76344ed843f76db1706df677`; producer tests are `155d57d7dad60b12d28f5152f621c8f84c1ba7f978c8aca75055f14ad6e851f2`. I verified the supplied v2 snapshot, then exported public baseline `1fe9ffa2cdffb5a33aa3e9b165e09c5997232b18` and overlaid only those two files. Concurrent D008 changes are excluded. Source Python 3.13.12 and a fresh noneditable offline installation on Python 3.11.9 each executed the same test selection under socket-network guards and a minimal environment without project keys.

| Execution | Result |
| --- | --- |
| Source: recovery closure, capture, materialization and independent probes | 166 passed in 9.77 seconds |
| Clean Python 3.11 installation: identical selection | 166 passed in 10.30 seconds |
| Ruff on the two frozen producer files | Passed |
| Post-run source/test and installed-module identity checks | Exact frozen hashes match |

Each runtime ran 136 producer regression cases plus 30 quality-owned cases. The unchanged original 21 independent cases now all pass, including the failure that v1 reproduced in both runtimes. Nine new cases test current failure-basis success, both exact legacy writer refusals, unknown broker/workflow identity, absent broker binding, tombstoned origin and malformed current metadata. No failed v2 test or setup run is omitted from these results.

## What the checks establish

I independently retrieved the three public broker revisions `038714`, `eb47a7` and `9edfa8` from local Git, checked their exact source digests and common workflow digest, and inspected their event-emission dictionary keys through AST parsing. Both legacy writers emit the same three packet references and no failure-basis event; the current writer adds the failure-context/basis packet pair and the separate two-reference basis event. This verifies the finite allowlist's documented field contracts, without executing old broker code or asserting historical producer truth for any actual row.

Synthetic cases distinguish recorded origin from field resemblance. Both exact legacy packet profiles retain their required base references and explicit missing-modern-evidence gap. Known current packets cannot downgrade by dropping failure fields; required digests, nullable basis conditions, fence types and metadata remain strict. Contradictory event/configuration/run/code identities refuse. Unknown or absent producer binding remains unresolved, and no legacy origin is inferred from missing keys alone.

For the corrected separate failure-basis path, known current origin preserves configuration/basis edges and strict metadata. Known legacy origin refuses `event_producer_binding_mismatch`. Unknown or unavailable origin records `failure_basis_profile_origin_unresolved`. Tombstones remain explicit unavailable dependencies; missing required bytes refuse rather than becoming legacy omissions. These outcomes support a finite structural inventory, not full broker-role or workflow semantics.

Further independent cases verify pending-event inclusion, JSON-item bounds, no application/domain constructor invocation during inspection, unchanged snapshot bytes, current source/loaded identity reporting and safe projection exclusion of synthetic private values, paths, IDs and object references. The retained producer suite supplies the surrounding capture, materialization, traversal, refusal and identity regressions. No actual candidate, full inspector controller or consumed diagnostic was rerun.

## Acceptance boundary and retained evidence

A distinct reviewed actual inspection may now use this exact software revision within the existing D009 limits. Actual producer bindings or other unsupported profiles may still refuse. Such an attempt needs its own durable intent/outcome and receipt checks; these synthetic passes do not predict an actual successful graph or supersede earlier failures.

Full typed closure, historical replay, full/off-Mac recovery, offline availability and execution remain false. Required external/source/audit material, rights, key/account recovery, downloaded restore and freshness barriers remain separate. This older research-only generation does not include the proposed D008 control database or restore its authority history.

The quality-owned directory ending `quanto-d009-event-v2-quality-7tl8a_s3` retains both exports, installed environment, synthetic fixtures and outputs. Its `quality-evidence-v2.json` has SHA-256 `171ce8167d1316387f6cf4849e622447afa75a0a434525a91eb2aee42ae05bc2`.

| Artifact | SHA-256 |
| --- | --- |
| Unchanged original independent probes | `4679448638036e8df60490630f0ff662008036e9024d4c54284c94e0ff799639` |
| Added failure-basis probes | `e7f4cf87f5ffa40c67258769b8d4460ecaf867db949531fe5796875cfd14fcc1` |
| Source output | `457a7e2a3d0cbdfd64c9c8eac077a8960a824374e34c34801cf8fa93e125eded` |
| Clean Python 3.11 output | `150fb1c192a84312b7615233f58d05579299e15e3570f412dc38815ca7687675` |
| Independent public writer/AST check | `3f85af626cea1d0c924dc23b1571eb0f324e9e5690c143416d3c71091b672606` |
| Export baseline receipt | `cc2facae5f298bb5a1db8a56b6f9b53c0c82c123ee1190e5cc925b32f05f4062` |

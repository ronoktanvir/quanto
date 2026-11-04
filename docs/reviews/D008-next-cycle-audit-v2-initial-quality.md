# D008 next-cycle auditor v2 quality

**Quality withholds actual-use clearance.** Two independent fresh, complete invented traces received `verified_fixture` and exit 0 despite contradictory records. One had a launch budget from the wrong day. The other omitted 20 of 21 worker modules and supplied an arbitrary loaded-code digest. Both still passed all 282 accounting comparisons. The numerical comparisons are useful evidence about the calculation, but they cannot detect either contradiction in the operational history.

## Required corrections

| Fresh end-to-end witness | What the frozen auditor accepted | Required check |
| --- | --- | --- |
| Planning date disagrees with every dispatch date | I changed the invented budget observation to November 2 and bound its new hash in the call-entry receipt. All seven original dispatches, their reservations and their journal events remained on November 3. The auditor returned `verified_fixture` with 282 fields. | Compare each authorization and dispatch day with the worker’s pinned Los Angeles planning day. A run that crosses its authorized day must withhold the full verdict. A later settlement can occur on a different day. |
| Worker identity is internally consistent but wrong | In a different full trace, both before/after receipts named just the `quanto` package out of 21 compiled modules and supplied an all-zero loaded digest. The broker source identity and financial inputs remained unchanged. The auditor returned the same full-fixture verdict. | Require the exact worker module roster and a worker-specific loaded-code identity, derived from the reviewed interpreter, source, imports and guards. Reject missing, extra or changed entries. |

The worker-identity failure has two separable causes. The receipt checker independently accepted the one-module roster while the original loaded digest remained present, and accepted the all-zero digest while the full roster remained present. The end-to-end witness then exercised both together. I also inspected a prior **invented** real-worker receipt from the corrected supervisor quality integration. Its 21 compiled identities exactly matched this manifest, but its loaded SHA was `ca5081546178b9a74661f323f09fb9a29d9e513b32078fd7bd1fb9778cf63da9`. The auditor fixture’s loaded-manifest digest was `f0d8ec754d24063b848d606a950634ceb3e0b8588a72086e4a3c00521b47db0b`. A direct comparison with the latter would reject the real worker tested in that integration. The correction needs to reproduce the worker’s own loading sequence and then exercise one real-worker fixture receipt as a positive control.

These were mutations of invented evidence before each distinct audit. The original receipt bytes, modified bytes, process results and accepted terminal hashes are retained. The cases demonstrate missing checks in the shared audit path. No actual project state was altered or inspected, and no historical operation was rerun. The separate critic has also identified a purpose-allocation prefix issue. That witness is critic-attributed and requires its own disposition.

## Normal and adverse controls

| Fresh prospective trace | Recorded auditor result |
| --- | --- |
| Complete, seven publications | Exit 0 in 13.21 s. Seven settled requests, four reviews, one block and one inconclusive judgment. Three distinct oracle submissions compared 94 fields each. I reconstructed nine derivative operands from the retained child reports. |
| Hypothesis voluntarily stopped, two publications | Exit 2 in 3.86 s. Two settled requests, no review reached and zero oracle cases. |
| Scope response malformed, six publications | Exit 2 in 12.37 s. Six settled requests and one uncertain hold. The retained financial work received no numerical pass. |

All three clean paths joined 54 receipt/source identities, retained false operational and investment acceptance, and reported zero actual model observations. Each used a fresh marked synthetic store, an inventoried source predecessor, real fixture processes, injected transport and the producer’s fixture supervisor/worker interface. The fixture registration child called the ordinary product registration functions and emitted the interface receipts. The actual supervisor, paid worker entrypoint and actual registration controller were outside these runs. The separate corrected supervisor quality review covers their real predispatch integration. The original early-stop generator exited 1 at invented admission before producing an audit packet. Its stderr and terminal observation are preserved. A distinct fresh early-stop fixture succeeded. The exact cause of the first generator refusal was not isolated.

Nine independent semantic checks covered successful exact-outcome and accounting controls, refusal of stripped and extra-field outcomes, missing call-entry and lead observations, a later unbound checkpoint, mutable accounting rows moved to 1999 without their authorization events, and a changed synthetic response fingerprint. All produced their expected classifications. A real initial manifest stall was interrupted at 0.1244 seconds under a 0.12-second work allowance. A simulated cleanup wait got only the remaining 0.125 seconds, returned its exit after the deadline, and stayed `cleanup_unobserved`; an already-expired second probe issued no poll, kill or wait. These checks close the earlier timing findings within the ordinary-process boundary. They do not promise prompt termination during blocked kernel I/O.

## Exact scope and retained evidence

Reviewer `/root/access_v2_quality` observed checkout `a64791404adf427fd7e6343805d2fe3f25f13fe7`. All 3,604 v2 freeze entries, all 744 original v1 entries, the six auditor tools, both supervisor sources and 33 public product/dependency files matched their hashes. The manifest records 21 compiled module identities. Actual auditor invocations used the pinned Python 3.11.9 interpreter and empty requested environments. No credentials, paid calls, actual market data or real financial replay were used.

| Artifact | SHA-256 |
| --- | --- |
| V2 freeze / producer report | `0d29713b6e010f98f492fc5f1ca67c026300e84eaadb31385278d0f3162efd98` / `c6c1ab96c48230a8d104a2144b22e16af0bfea77576a852b17f3eded8bc3f2b4` |
| Source manifest / auditor | `6ca9e2cd82e7eb91bbccffc85f6c78c06d7fb20b8e4f488d943a19b6396e201c` / `ba9bd68bdfe5ae266d765b7f58e0d14c9b74149b3dbe22b7b888f5e1528bacd1` |
| Prospective evidence checker | `da4c1fe308f6f8c35eb20840c8fc438b562179411f972bb6c5af36a68ddc0d5c` |
| Supervisor / worker source pins | `43f992b081fe7bd5f23d6163dafd5827d265630a6b3049ecf58857eaa802d830` / `9a59cb3eb37f8b6f06d17abde2a474da13fba07264bd37c634ee12a07f0cd01c` |
| Previous v1 freeze, reverified | `3eb2ec572c1ccdc500e017d8442a1be7c5802e5f37e7b8f0eca721e9847699a4` |
| Day mismatch / worker identity false-full records | `00b09775bf7570bef293ebfecf451b6810779249b5d2bfff00e5a4a7006d59cf` / `84d69a95a1f8f116538298263e77bb377ff4e13b0bcac079137fc1bb6935a901` |
| Isolated worker identity checks | `23c96d2d5dfea54674c58c8d228f727f630e4c1b3ff83399322f195e62647e74` |
| Semantic and timing checks | `9e441336847be1f591ae4955618de2cd569199979fd26971b10f6346282f225b` |
| Aggregate quality evidence | `91114c667682b3b408c4aae59d7ef09bd919f42146bff4451f0415c53e554c52` |

All quality execution handles are terminal. Artifacts and commands are retained under ignored `runtime/development-cycle-audit-v2-quality/`. Actual launch remains gated on a corrected, independently reviewed auditor and the lead’s authorized, prospective private preflight.

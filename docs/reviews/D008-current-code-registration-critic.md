# D008 current-code registration criticism

The frozen controller preserves the intended old-to-new registration mapping and existing authority, but **its stated 600-second work plus five-second cleanup bound is not yet enforced throughout the parent invocation**. Correct the initial alarm gap and renewed cleanup allowance before an actual registration attempt. These are local controller corrections within the accepted policy; they do not require a new financial or architectural council.

Reviewer: `/root/rollout_controller_critic`, November 3, 2026, separate from the producer and quality reviewer. This review inspected public source/preparation artifacts and executed invented fixtures only. It did not open the actual request copies, private packet, research/control databases, receipts, credentials, budgets or historical payloads; invoke an actual controller; call a provider/model; or edit product source or Git state.

## Exact inspected artifacts

| Artifact | SHA-256 |
| --- | --- |
| Controller `prepare_current_code.py` | `1d0cd609d6e3185df00c54040b990f7b756d40e689ccd00a876ae12a9515bd84` |
| Producer report | `c13368f105c819dbeac52c708a5a6acc66f35c66b4e759e417e61f97b126dbed` |
| Frozen packet manifest | `34d30516aea6ae2777fee4def8265e9e99553d6ce075b4277e08fac3487b8a84` |
| Producer tests | `d3b0684d6495f677ae4f6a0334c9c0713291f64283df51c1b88ecc669e55194b` |
| Source/runtime/loaded-code manifest | `aa65675f3c7886a2d950b75928811d4f7189adbc2342a383b983f0ea20ea70c4` |
| Independent final probe source | `3f945582ed8db079b791b4e8ddccb63fb63e2b9f00898b80b03f2b03d3950762` |
| Independent final test log | `d723c952551c7459d9ecff35f3f2049875e5c2f65cd3ea4e5b8826e381bf0cbc` |

Exact copies and evidence are retained under ignored `runtime/development-cycle-registration-critic/`. All 33 public source/dependency files in the manifest matched current bytes at the final check. No private target referenced by a manifest or packet was opened. The producer's reported 17 passing cases remain producer evidence; I did not rerun that suite or count it as independent validation.

## Required deadline correction

**The initial preflight runs without an installed alarm.** `run()` starts its monotonic clock at lines 738–740, but the handlers and timer are installed only after environment, packet, manifest and source checks and durable consumed/intent publication at lines 768–771. The later deadline check can reject completed late work, but it cannot interrupt preflight while it is still running. Install the ordinary-process deadline mechanism before the first timed preflight operation and restore handlers on every exit, including failures before an attempt directory exists. No guarantee about interrupting blocked operating-system I/O is required or claimed.

**Failure renews the allowance instead of consuming the remaining allowance.** The initial timer permits work through `started + work_seconds + 5`. The exception path at line 830 then unconditionally starts another five seconds, while `reap()` always allows two seconds and can be called again in `finally`. An exception first delivered at the advertised outer boundary therefore receives additional time. A focused clock witness observed the initial alarm ending at simulated time 705 and the failure path scheduling a new end at 710, from a simulated start of 100. That is a scheduling witness, not an actual ten-minute wall-clock run.

Use one absolute work deadline and one absolute cleanup deadline derived from the original start. Every parent wait, kill/reap wait and final cleanup path must use the remaining allowance; a second cleanup call must not create a new budget. Preserve uncertain child/effect state if cleanup cannot be established within that allowance. The later 7,200-second combined research controller must subtract actual elapsed preparation time from its common start; a separate successful registration timer does not reserve or renew that shared allowance.

## Input preservation and authority

The mapping implements the approved economic scope. Revision registration receives the exact retained request bytes. Admission changes only `policy_revision_sha256`; suite registration changes only each member's admission reference while retaining member order. Original success submissions, start/finish event positions, artifact references, request metadata and retained bytes are checked before mapping. Admission's explicitly declared `embedded_semantics` mode compares the embedded request without claiming to reconstruct unretained original bytes. The complete three-cost roster and shared dataset/admission references remain required, and the normal product validators recheck the new registrations.

The current controller does not infer approval from a digest-shaped field. Its critic and preflight references are durable lead-supplied references; determining their accepted contents and applicability remains the lead's responsibility. The reported three private request copies and existing authority were not independently observed here. Their exact equality and current-state binding remain actual preflight requirements.

Existing-file guards prevent research/control constructors from creating missing databases. Before and after each phase, the controller checks database identity/mode/link count, directory identity, absent SQLite sidecars, complete control schema and all table states. Previous control rows must remain a matching prefix; only normal audit/intent/effect tables may append. Administrative rows cannot change. `legacy_unknown=True` remains explicit. These checks support a cooperating-worker boundary, not global inactivity or hostile-owner isolation; the lead must bind the packet to the reviewed actual authority and worker cut.

The directory-wide exclusive consumed marker prevents switching to a fresh attempt name. Each phase publishes its operation intent before its single registration call, then retains outcome, result and parent launch/exit bindings. A refusal, partial effect or incomplete phase stops later phases without deleting evidence. A successful result is only three current-code registrations; all protected, replay, unattended and investment claims remain false.

## Source and effect boundaries

Source checks compile the pinned product bytes rather than importing an installed alternate package or stale bytecode. The manifest compares compiled module identities, loaded methods/functions/defaults/policy bindings, critical standard-library identities and the richer financial code identity. Children require the pinned Python 3.11.9 runtime and isolated, no-site, no-bytecode startup with the constrained environment. These are explicit current-code checks, not a hardened interpreter-installation claim.

The child audit and profile controls deny network/subprocess, credential and portfolio/evaluator/provider entrypoints while allowing the reviewed local content-publication sequence. Existing registrations still perform local historical evidence and economic-consistency validation. The accurate boundary is local preparation without a portfolio backtest or paid request. The controller contains no paid-launch path and does not grant one through a completed mapping.

## Independent evidence and retained harness failures

The corrected independent run completed **seven tests in 15.99 seconds**. Four exercised actual product registration behavior on invented evidence; three documented the scheduling defects with isolated parent-control stubs. Passing defect witnesses mean the defect was reproduced, not that the timing contract passed.

The product cases verified exact retained revision text, preservation of every preexisting research-table row, three fresh submissions and directory-wide consumption across a changed attempt name. They refused an altered admission dataset and reordered suite even after updating the copied-file digest. They also stopped before admission when an invented extra principal appeared after a completed revision. No registration validator was replaced. The producer fixture helper supplied only invented fixture construction; assertions and scheduling witnesses were independently written. Fixture children retained the reviewed interpreter/environment contract.

The first independent run is preserved: two fixture construction errors reported `artifact_or_storage_unavailable`, two later assertions failed after the controller correctly refused fixture roots inside the actual checkout, and three timing witnesses passed. The revised harness placed product fixtures outside that checkout, as `fixture=True` requires; all seven then passed. The specific cause of the first two construction errors was not isolated, so they are not attributed to a product defect. An unused initial authority-mutation hook also had an incorrect column name and would have hit an append-only trigger; the corrected probe inserts a new invented principal and verifies the subsequent state refusal. Both harness versions, original logs, invented roots and terminal records remain retained.

The timing correction and exact revised-source validation are the remaining blocker identified by this criticism. Separate quality/scope review and the lead's private packet/current-state verification remain necessary before the one actual attempt.

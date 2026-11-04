# D008 next-cycle auditor quality

**Quality withholds clearance for actual use of this freeze.** Fresh invented traces reproduced the full and incomplete classifications, independent accounting comparisons and derivative checks. Two launcher timing witnesses show that the post-run auditor does not yet enforce one finite lifetime through preflight and uncertain cleanup. The [next-cycle plan](D008-next-development-cycle-plan.md) requires a separately bounded post-run inspection.

## Launcher findings

1. The parent starts its 600-second clock after loading the manifest, checking the interpreter and packet, validating paths and creating the attempt directory. With a 0.05-second fixture limit, I delayed the initial manifest read for 0.25 seconds. It had no active work alarm, returned normally from the delay and rejected the deliberately incorrect packet digest after 0.273 seconds. No attempt directory or child was created. This demonstrates an uncovered preflight interval under ordinary signal delivery.
2. A timeout can grant a second cleanup wait. An invented process handle timed out during the work wait and again during its three-second cleanup wait. The exception handler polled it, issued a second kill and granted another three seconds. The second timeout escaped before publication of a process or launcher-failure receipt. The intent and job were preserved. This was a scheduling witness with a stand-in handle. No system PID was signalled, and it does not establish a live orphan.

Start the parent deadline at invocation, derive a single absolute cleanup deadline, and have one cleanup path consume the remaining allowance. Retain uncertainty if the owned process cannot be observed terminal. Rehearse both witnesses against the corrected freeze. A separately reviewed outer supervisor could also enforce the entire lifetime, provided its ownership and uncertainty behavior are demonstrated. Ordinary process timers cannot guarantee timely termination during uninterruptible operating-system I/O.

## Independent fixture results

Reviewer `/root/access_v2_quality` generated two new isolated synthetic stores using the producer's public fixture builders, injected transport and invented clock. An independent hook observed the checkpoint file and verified the journal head before the first broker submission. In both stores, event 46 completed suite registration, event 46 was the pinned checkpoint, and event 47 started the broker. Both generator processes exited zero. The separate auditor ran the exact frozen source under pinned Python 3.11.9 with an empty environment and isolated, no-site, no-bytecode flags.

| Fresh trial | Auditor result | Separately checked outcome |
| --- | --- | --- |
| Complete invented broker trace | Exit 0, `verified_fixture`, 13.73 s | Seven publications, four reviews, one blocking and one inconclusive judgment. Three fresh children, three oracle passes, 282 fields and nine derivative operands. |
| Voluntary stop at hypothesis | Exit 2, `incomplete`, 3.91 s | Two published stages. The auditor published an inspected partial report with zero financial checks. |
| Changed engineer-stage alias in the supplied outcome | Exit 2, `refused`, 16.58 s | The altered outcome file and its new digest agreed with each other. Its contents disagreed with the original trace. The auditor retained the failure with zero oracle passes. |

All three trials had empty stderr, terminal process and output bindings, zero actual model observations and false investment, protected, live, unattended and operational-acceptance flags. The five budget/dispatch/observation table hashes matched before and after each trial. The auditor is effectful. In the full fixture, control storage gained 159 intents, 159 effects, 159 effect completions and 439 audit rows. Separate generator processes used the product workflow and financial engine only on invented data. The auditor performed the comparator calculation separately. No actual database, credentials, model call, acquisition or historical financial replay was used.

The complete fixture had three distinct financial child submissions, three attempt identifiers and three distinct successful oracle submissions for 0, 10 and 25 basis points. For each slot I matched the hashed input and retained child result, comparator stdout/stderr and exit, and registered verdict. Each comparator checked eight evaluation sessions across strategy and benchmark, 94 fields per slot at tolerance `1e-28`. I separately rebuilt the nine operands from the retained child reports and checked the selected fee-order predicate against the decoded derivative. As a sensitivity control, changing the final strategy receivable in the 10-basis-point comparator input by 0.125 caused the standalone pinned oracle to exit 1 on that field. This was an expected refusal and its output is preserved.

The producer's full and three partial confirmations used reconstructed historical event positions. Its voluntary-stop fixture captured its position prospectively. Both fresh traces above captured their checkpoints before broker invocation. An event hash at the expected position establishes consistency with the retained journal. Evidence that the checkpoint was actually saved beforehand comes from the observing supervisor. Inspection-time revalidation likewise cannot independently establish send-time availability. The alias-mutation case establishes refusal of that particular changed field. It does not establish complete outcome-shape binding or resolve the separate critic's adverse findings.

## Exact evidence

The observed repository revision was `b46f44f876d39f1afa154881816609ea95f7fd40`. I verified all 744 entries in the producer freeze, all 33 public product/dependency files, the 21 compiled identities recorded by the manifest, and the five copied tool identities. The successful auditor invocation performs the loaded/compiled identity comparisons. The exact pins are below.

| Artifact | SHA-256 |
| --- | --- |
| Public producer report | `272f248325343736c3acef4dedbb492cf17d23c4ff9643bc736fa3a7dd83c495` |
| Producer freeze | `3eb2ec572c1ccdc500e017d8442a1be7c5802e5f37e7b8f0eca721e9847699a4` |
| Source/loaded manifest | `f3bf3146a00c92e72c7ef3c86e74ec162cbc2b1b8aa45acf77e6f733887fe51c` |
| Auditor | `13a5f72e74c9d779173bebbccffd7571cf527d41b705940a1614b30341bc4351` |
| Boundary | `96a3f8632666fb5229eea0c891dbdb72367fb601f45aae4c60aed34b9419418c` |
| Trace and derivative checks | `ffee43cf42db0883bb2ac2f1171bd5975c03c25c86608999b19a7bf2c4acf508` |
| Context checks | `bb12da1169debcfdec40593bb6510f62e6d61a61d54434b6abb2ef1f46668a17` |
| Oracle | `54887dfae2f12430b5cdd9901c0c3ba367541f6eb4714b987ad68e08f0433ca1` |
| Python 3.11.9 executable | `4e28e811a89aeac6eed668ae641c7f85f5831e42e8dc6cd9a85a3bcc032ec46a` |
| Independent timing witness | `2d8068fc26de803bae442eb42d24292e293e4f19d69186623f8052b6d7b5ed4f` |
| Independent numerical evidence | `60cefbc8fc61ddad3c49aee88351fb68f8ad601ae397e80c7a2693d0a588bfc6` |
| Aggregate quality evidence | `764679bedae12a936fed046448185d9de33e66287f274e5c92067795320ad26a` |

Commands, generated fixtures, terminal receipts and adverse outcomes are retained under ignored `runtime/development-cycle-audit-quality/`. The producer's earlier failures remain distinct from these trials. Actual use requires correction and independent recheck of the launcher and outstanding criticism, a lead-owned prospective checkpoint and writer cut, and a distinct bound post-run audit attempt. This preparation grants no research retry or trading authority.

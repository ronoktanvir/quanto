# D008 manual-cycle launch criticism

**Hold actual use of the combined v1 launcher.** The parent binds the reviewed inputs, preserves prior research requests, consumes the cycle once and tracks the child it acquires. The paid worker can nevertheless reach the broker before the parent establishes ownership, after the common wall deadline, or on a different budget day from the prospective observation. Independent witnesses reproduced each case with an invented broker function.

## Require positive ownership before paid work

The parent publishes `paid-launch.json`, calls `Popen`, and publishes `owned.json` after receiving its handle. The worker checks matching parent IDs and launch/consumption digests. Neither bootstrap nor paid entry checks `owned.json`. The parent can be interrupted between starting the child and acquiring its handle. Its honest `launch_ownership_unknown` record then does not prevent the child from proceeding.

Three witnesses reached the broker stub with the ownership receipt absent, with a wrong PID and digest, and with an already published parent failure. A fourth changed the observed parent PID after prelaunch and still reached the stub. These exercised the frozen worker after its bootstrap seam. Source inspection confirmed the real bootstrap adds no ownership grant.

Require a dedicated parent-to-child grant. The parent should send it only after acquiring its actual process handle, durably publishing the owned PID/launch/consumption binding and reading the receipt back. Interrupted or failed spawn/publication must close the grant path. The child should require the grant, its own PID and current parent PID, the exact owned receipt, and the matching live plan before opening paid access. Recheck parent identity and deadline at authorization and immediately before send. Preserve uncertainty for a request already in flight.

One-use consumption also needs write ownership. A worker that lost creation of `paid-consumed.json` left that file intact but wrote an uncertain `outcome.json` and `terminal.json` into the other invocation's attempt. Only the invocation that successfully acquired and durably bound the paid marker should publish terminal evidence there. A losing or partial creator should exit and preserve the conflicting evidence.

## Apply the common cutoff during work

The parent computes the shorter remaining interval from its original monotonic and wall starts. The worker converts that interval to one monotonic deadline at bootstrap. It can then keep using that deadline after the wall clock has crossed the common cutoff. In a controlled clock witness, the wall had advanced 7,300 seconds while the monotonic clock still had time. The worker entered the broker stub and returned success.

Keep both original clock bounds live through paid entry and each authorization/send boundary. Limit a new transport timeout to the remaining common allowance as well as its existing bounds. The parent should observe both clocks while waiting so a large wall-clock change does not go unnoticed until the child returns. After poll, kill, wait or receipt publication, distinguish an observation inside the allowance from one made later. One fake cleanup handle returned at elapsed wall time 7,201 seconds. The parent reported `owned_child_reaped` without recording that it observed termination late.

The nested registration helper has its own reviewed 600-second monotonic work budget and five-second cleanup allowance. The parent checks its common window before and after calling that helper directly. An invented helper completed its simulated local work at elapsed wall time 7,300 seconds. The parent correctly prevented paid launch on return. Enforce the common wall cutoff during the registration interval as well, or accurately narrow the claim about when that cutoff is enforced. The witness used a simulated nested helper and made no actual registration.

## Keep the prospective budget day valid at entry

The worker reads global and purpose headroom, the allocation prefix and event head in one SQLite snapshot. It requires at least USD2.625 under both the USD20 global and USD4 research-purpose daily limits. Its later check verifies that the budget event head belongs to the prelaunch journal prefix. This is appropriate planning evidence, with per-call atomic authorization still required by the broker.

A ninth witness advanced the LA day just after `prelaunch.json` publication. The November 3 observation had sufficient headroom. On November 4 the invented research-purpose ledger had zero remaining, yet the worker entered the broker stub. Recheck the planning day at the final entry gate and stop the consumed cycle on rollover. Preserve the broker's own per-dispatch day and atomic spending checks. This witness establishes a stale whole-run planning condition. It incurred no charge and does not show that the broker's daily spending cap is bypassed.

## Source, receipt and review disposition

The parent verifies the plan, nine review identities, registration inputs and checker manifest. It preserves original failure roster/model ordering and changes only run key and suite reference. The worker verifies current source/runtime identities and existing authority, links budget/prelaunch/entry to the accepted registration result and preserves the exact normal broker outcome. A normal return can still represent an invalid or pending workflow. Separate audit acceptance remains necessary, including the corrected auditor and its reviews. Reviewing a digest establishes the identity of the selected file. The lead still owns the decision that the review accepted the applicable version.

| Artifact | SHA-256 |
| --- | --- |
| Joint freeze | `bd3f8ca4801c980c1fde88b385649bdf49291cea3af86e0db1a69eb3978c4804` |
| Producer report | `1c3e80c9445be3f9740be1015239a78d251083cbd2d8751da174d3598dcb8b2a` |
| Parent | `1fb79f5735ce6ecbb5d7d026e11ee33c59773d13af7c72e3584547ff03404bcd` |
| Paid worker | `7aa4e43c5a4453fad118d29f379fd5b1ba08d2b0cd5af0a955e2baa2c106c883` |
| Registration helper | `3f52a95452d9a20c6c456624f33a70c717d9f1fc28d83ae65f178e67e9d7047d` |
| Parent tests | `385dbc0f42c873c914698c8be542e2cc03cffbae2d3c67a8ae6212d2e3a5cf36` |
| Worker tests | `27c62e3b323c2d2dd585033eea0263c6098793ff92006174383eed9309619247` |

Nine independent probes reproduced the described behavior. The eight ownership/deadline witnesses and one budget-day witness are retained under ignored `runtime/development-cycle-launch-critic/`. Their logs hash to `e8826ddf071536d75e282d791d15a7e1d8c8d6b92c8b22ddeaf8b6d4ea1e8182` and `3605abb09038ce24e90d81df8f7c0d87bb6f647a5e016bf461d8a8fcb408f6e9`. I reused the producer's invented worker context and wrote independent faults and assertions. The parent probes used controlled handles, an invented state directory and a simulated nested helper. The producer's 59 cases remain producer evidence. This criticism used no actual private inputs, credential, market data, model dispatch or financial execution.

# D008 auditor v2r1 criticism

**Withhold actual use of this freeze.** The three defects recorded against v2 are corrected. A further budget witness shows that a malformed, noncanonical or impossible future day on an ordinary purpose allocation can still hide USD1.50 and change the launch decision. A plausible earlier day needs a separate treatment when its timing cannot be independently established.

## Remaining headroom defect

I tested a purpose-allocation row of USD1.50 with its matching reserve and ordinary provider-request event on November 3. The row was demonstrably inside the captured prefix. With canonical day `2026-11-03`, the checker correctly refused because USD2.50 remained under the USD4 research-purpose ceiling. The threshold is USD2.625.

Changing only the row's day to `not-a-day`, `20261103` or `2026-11-04` made the checker accept USD4.00 of purpose headroom. The SQL sum compares date strings, so every one of those values omitted the row from November 3. The first is malformed, the second is a noncanonical spelling of November 3, and the third is later than the reservation that followed the allocation. Quality first reported this ordinary-row weakness. I reproduced all three cases independently with an in-memory database and no real requests.

Require canonical `YYYY-MM-DD` for the relevant rows. Check the reserve event's day against its LA timestamp and refuse an allocation day later than its proven reserve. A valid November 2 allocation followed by a November 3 reserve across midnight remains possible under the split transaction used for ordinary provider requests. I verified that case separately. If an ordinary row's earlier date lacks independent corroboration and assigning it to the planning day would reverse the decision, use a conservative bound or return incomplete. A later reserve alone cannot establish on which earlier day the allocation occurred. This distinction preserves legitimate overnight calls while preventing a questionable date from establishing sufficient headroom.

## Three previous findings closed

- **Planning day.** The original seven-dispatch invented trace passed unchanged. A planning observation from the preceding LA day now refused against the same run-specific journal and authorizations. This constraint applies to authorization. Settlement may occur later.
- **Purpose prefix.** The original witness with a pre-cut USD1.50 journaled research allocation at row 1 now refused a claimed zero prefix. The correct prefix with USD2.50 remaining also refused. A USD1.00 allocation leaving USD3.00 passed. Known later atomic allocations were excluded, and either choice for an undated row between known sides returned incomplete. The separate ordinary-date counterexample concerns a row already inside the prefix.
- **Worker identity.** The checker accepted the exact positive pre-session receipt recorded by quality when the real paid worker ran on an invented store. It refused a one-module subset/zero digest, a complete roster/zero digest, a missing module with the correct loaded digest, an extra module and a different broker identity. I separately ran the guarded code-only derivation on the pinned Python 3.11.9 interpreter. Its complete 21-module reference matched the manifest, including loaded digest `ca5081546178b9a74661f323f09fb9a29d9e513b32078fd7bd1fb9778cf63da9`. The underlying positive worker execution remains attributed to quality.

## Scope, verification and disposition

Fifteen primary independent cases matched their expected outcomes. Supplemental checks distinguished a valid across-midnight allocation from an unprovable cutoff and refused a replacement audit ID before reading further receipts. Five additional ordinary-day cases reproduced the remaining defect and its controls. The evidence is retained under ignored `runtime/development-cycle-audit-v2r1-critic/`. The primary, supplemental and normalization logs hash to `1731e2020b16805e5a5d9f97eb901aae2229d8974dc19d2a96b6844c88ec6b92`, `ebd4866a17cee8bad2aac2a414c0faa9a65c3c5663491da5ceec6ed99cf3c1f9`, and `0be59021e3e6d6178bb56b07fe9badc0399793b211d232b7ef9f9e55b1d90d0a`.

| Final inspected artifact | SHA-256 |
| --- | --- |
| 2,217-entry preparation freeze | `ec2ebb519a384333ab5d39e84b31077dc17590984b73492624ec114244937891` |
| Producer report | `a7a9ae75585a4c7312552a1b31ca7e4224c64aa2f5448b2f32dd63a852151072` |
| Source and worker-reference manifest | `8f3168799658e6b37179328be2c2cea8739ff6b7ff18bd09c1c763465ce95bde` |
| Corrected evidence/accounting module | `c4ac1a5a44e21f0ee83279a18d303048bef9191145ccb1f507f23f59c85a61f8` |
| Code-only derivation source | `ecb929c0a71bd5b452003d85fd8ef2a5b71c5646e3e77d6582cc11f353e042c1` |
| Known positive worker receipt | `9385d856df0ab7dd39d56f5c638fd7bb10d85339b0faf9c1d0086a77a7238098` |

All six runtime module digests and 33 public source/dependency digests matched the final freeze and tested manifest. Only `cycle_evidence.py` changed among the six runtime modules relative to v2. The prior deadline, prospective chain, full-outcome, projection and numerical-verification evidence therefore keeps its existing applicability. The producer's 80 expected checks, numerical comparisons and retained failures remain separately attributed. This review used code, invented evidence and an already captured synthetic-store worker receipt. It performed no actual audit, paid dispatch, historical financial replay or real credential access.

A corrected successor needs affirmative criticism, quality and scope review before the lead stages its exact six modules, manifest and positive reviews at the fixed canonical paths. Preserve the original sources and adverse reports, verify the staged bytes, use the normal plan loader and perform fresh private preflight before consuming either actual attempt. This r1 freeze is evidence of the remaining defect.

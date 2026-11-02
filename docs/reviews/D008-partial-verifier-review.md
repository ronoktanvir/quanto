# D008 partial-workflow numerical verifier: preparation review

**The new v4 verifier passes invented-fixture preparation checks and is ready for lead review before actual execution.** It can verify retained financial work while preserving an invalid workflow, an incomplete review roster and a fully uncertain failed-review reservation. This report establishes no actual numerical result: no actual database, receipt or artifact was accessed.

Reviewer/producer of this separate verification harness: `/root/d008_broker_quality`, independent of the research implementation and model workers. The lead's actual-trace inspector is separate evidence. The only runtime inputs read for preparation were the permitted v2/v3 harness source and pinned oracle source; other source reads were public project code/tests. Product source, old scripts, actual traces and old outputs remain unchanged.

## Exact prepared artifacts

| Artifact | SHA-256 |
| --- | --- |
| New `runtime/d008/verify-partial-workflow-v4.py` | `c0a26e7f205a413e241daee110910fecc49d4924cc24e60b6b156ddbb43a2429` |
| Reviewer fixture probe | `b055691f8e839a19ff9673ff183537ee89e2dc9938313546613028fa83a89337` |
| Preserved v3 | `05550ba9cc1d39c1e7584bd87d47f242a2ccb0fc9b7156b05d4015028512e571` |
| Preserved v2 | `d7cf5022ffd67168095f4720421c7ca30cd5ade6c8ae799bcfc69e0445444f6f` |
| Unchanged independent oracle | `54887dfae2f12430b5cdd9901c0c3ba367541f6eb4714b987ad68e08f0433ca1` |

V4 compiles and passes Ruff 0.17.3 under Python 3.13.12. Final hashes were rechecked. AST comparison confirms that `number`, `independent_predicate` and `oracle_case` are unchanged from v3. No producer calculation or `research_comparison.evaluate` is imported into the independent arithmetic. Source inspection and an AST check find no budget reservation, settlement, release, uncertainty-update or dispatch-authorization call in the verifier.

Preparation history, source snapshots, deterministic fixture generator and bounded result metadata are retained separately under `runtime/d008/preparation-v4`. No actual database was opened to record preparation evidence. Temporary test databases were disposed by normal test cleanup; the preparation archive does not claim to preserve their exact original UUID-bearing database bytes.

## What v4 verifies and preserves

**Exception records use authoritative configuration.** A caught broker exception may omit the successful-run record's configuration and code fields. V4 resolves the exact parent artifact and terminal outcome, then obtains configuration, code identity and specification binding from the registered broker run and workflow manifest. It compares the saved lifecycle receipt with the retained record instead of manufacturing a successful parent record.

**Publication and observation are separate rosters.** V4 checks published stage records, assignments, contracts, handoffs and safe projections separately from all issued dispatches and bounded response observations. Each request joins its predispatch packet/proof/failure-basis binding, consumed intent, exact rendered body digest, reservation, research-purpose allocation and observed model. Only published projections contribute to review coverage. An unpublished response is never parsed or promoted into a reviewer decision; its private response artifact is hash/availability checked without decoding its reply or rationale.

**A failed scope response remains uncertain.** The unpublished review must have an uncertain effect with no successful output, no handoff/stage record, a full uncertain reservation and no settled amount. Run-specific accounting partitions settled and uncertain requests by their exact assignment/request identities. The verifier snapshots the entire uncertain reservation row and compares it again after all oracle checks. It neither settles nor releases that hold. An incomplete published review set remains `incomplete`; a failure before any review publishes remains `not_reached`. Missing reviews and published inconclusive/block counts remain explicit.

**Financial work is bound to this parent.** The verifier traces the engineer's consumed effect and exact precommitted request to its unique successful comparison, original request bytes, registered derivative, newly registered suite and all three successful cost-slot children. It checks event order, unique attempts, child request identities, retained admission and source/code identities, complete roster/report agreement and the derivative operands. Another invocation or cost-slot child cannot substitute for the retained work.

The selected predicate is recomputed with the existing independent exact Decimal comparisons. Each child then goes through the unchanged pinned rational oracle using its retained selected warmup/evaluation rows and admitted event inputs. Neither predicate truth nor numerical values enter stdout. Only integrity status, lifecycle/coverage counts and code digests are emitted. The command emits `numerical_verification=passed` only after all three oracle cases pass; `workflow_status=invalid`, `all_stages_completed=False` and `operational_acceptance=False` remain separate.

## Inherited harness issues corrected in v4 only

Source review found two unexecuted v3 financial-branch event selectors lacking the `workflow_` prefix. The public emitter records `workflow_broker_tool_child_bound` and `workflow_effect_started`; v4 uses those exact names. Temporary full lineage checks now exercise these selectors. This was a verifier selector issue, not an observed product or actual numerical defect.

The first valid temporary partial-workflow fixture then refused at `frozen_financial_request_mismatch`. Its registered request legitimately omitted documented `StrategySpec` defaults, whereas the frozen engine artifact contains the full specification. V4 now expands only the documented defaults for comparison with that declared engine specification. It validates exact permitted fields, numeric types, finite values and supported ranges; unknown fields refuse. Explicit submitted values preserve their JSON types.

Raw request identities remain separate: original request hashes and byte lengths are checked before this expansion, and the original dictionaries/bytes are never replaced by normalized ones. The three omitted defaults are an engine-protocol identity issue, not missing market observations or permission to alter a study. Mutated default values and inconsistent report specifications are independently refused. The initial refusal, deterministic reproducer and subsequent passes are retained in the preparation archive; no old harness or actual outcome was rewritten.

## Executed invented-fixture evidence

The final probe uses the real admission, policy, suite, financial, broker and journal code with invented D007 source records and injected envelopes using the default five-Haiku/two-Opus roster. These are software fixtures, not actual model responses or historical evidence. The test producer creates the fixture runs; the verifier never launches or repeats a registered financial calculation.

A post-finance scope parser failure yields six published stages, seven synthetic observations and three published reviews. V4 correctly retains `workflow_status=invalid` and `review_outcome=incomplete`, verifies one exact fresh suite/three children and nine derivative operands, and runs three independent oracle cases comparing **282 fixture fields**. The full uncertain scope row remains unchanged.

A separate fixture fails at the first reviewer after three published research stages. It reports four synthetic observations, zero published reviews and `not_reached`, while verifying a different fresh suite with three distinct children. The earlier and later uncertain holds both remain unchanged. This also tests attribution when other cooperating fixture requests share the same temporary journal.

Adversarial checks pass:

- Corrupt comparison bytes, foreign parent-child binding, wrong cost-slot child and an improperly settled failed-review reservation each refuse.
- Two mutated default/report specifications and four invalid field/type/value cases refuse; the raw registered request remains unchanged.
- The strict actual entrypoint rejects the expressly synthetic fixture. Internal fixture testing requires an explicit direct-call-only mode that accepts synthetic evidence/transport, reports zero actual observations and labels its result synthetic; no fixture option exists in the CLI.

The probe's successful checks do not constitute an actual run or independent review of actual private numerical results. No actual model, network, credential or environment file was accessed, and no actual financial or council runner was invoked.

## Limits and next gate

The new partial path deliberately supports a post-finance exception with a published research/engineer prefix and one observed, unpublished failed reviewer whose effect/hold is uncertain. A missing response observation, ambiguous accounting, multiple unfinished reviewers, unbound financial work or unsuccessful comparison/suite refuses; it is not silently reconciled or rerun. Full packet/failure-basis scientific interpretation remains separate from numerical integrity and the lead's independent trace criticism.

The actual third workflow remains invalid on the information supplied by the lead, with scope unpublished and earlier review qualifications unresolved. This preparation report does not certify its numerical work. The lead should review the exact v4 code and these limits before authorizing execution on the saved actual receipt. Any later numerical pass must remain separate from actual-cycle acceptance, R14 and the remaining evaluator, scheduling, paper and live gates.

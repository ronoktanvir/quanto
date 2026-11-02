# D008 context-aware verifier: independent code and probe review

**The revised v3 verifier passes the bounded code/probe review after correcting one review-summary mismatch.** Its new failure-context joins and private-proof exclusions pass invented-record checks, numerical functions remain unchanged from v2, and the pinned oracle invocation passes an invented engine fixture. No actual receipt or operational cycle was inspected or executed by this review.

Reviewer: `/root/d008_broker_quality`, independent of the v3 producer and separate actual-trace criticism. This report is distinct from implementation quality in `D008-applicability-quality.md`. Allowed private-path reads were limited to the v2/v3 harness source and pinned oracle source; other inspected material was public project code. No actual runtime data, receipt, environment file, credential, network or paid model was accessed. Existing v2 source/output and earlier reports remain unchanged.

## Finding: unsupported review decision defaulted to clearance

The initially supplied v3 source, SHA-256 `67ff9f1a1807b285e0ceb8580447d3c3bfd4300ecfbd93d32cde0e11f45eba5f`, checked complete published review sets for `block` and `inconclusive`, then defaulted to `method_no_blockers`. An independent probe executing that exact source block supplied three clear decisions and one unsupported decision. The verifier accepted `method_no_blockers`, while the broker's current reporting helper returned `inconclusive`.

This did not establish a defect in any actual trace: the producer's typed role parser should reject unsupported decisions. However, the independent verifier should preserve the explicit-all-clear contract rather than infer clearance from an unknown value. The producer changed v3 to require every published review decision exactly `no_blocking_method_issue` for clearance, retaining block priority and an inconclusive fallback. Independent rechecks now reject clearance at each of the four possible unsupported-decision positions. **Closed at the final v3 identity below.**

## Executed checks

Final v3 passes in-memory syntax compilation and Ruff 0.17.3. The reviewer-authored temporary probe, `/tmp/d008_context_verifier_review_probe.py`, SHA-256 `290dc1780154f5c92e85f6bc7f7e1ccdd5abbad67eb26e0fe3ca5464f7c02678`, ran under Python 3.13.12 and passed:

- **1296 supported review-summary combinations:** all 81 decision combinations across all 16 published-role subsets, covering not reached, incomplete, blocked, inconclusive and explicit complete clearance.
- **Four unsupported-decision clearance refusals**, independently closing the initial mismatch.
- **Two valid failure-join cases and 13 mutation refusals**, including a director with no basis, mismatched proof/basis/configuration/role/facts, private observation or basis references in aliases/content, disclosed-data flags, predicate truth and rationale fields.
- **All three independent Decimal predicates**, tie and false-result cases, with five invalid operand encodings refused.
- **One pinned-oracle subprocess on invented engine inputs**, comparing 44 fields across two portfolios.
- **One missing invented receipt**, which exits 1, prints only a bounded failure summary and retains a failed verification attempt in disposable storage.

The review-summary and new failure-join/exclusion probes compile and execute the exact AST blocks from v3 with invented dictionaries. They are isolated code-block tests, not a claim that a fabricated complete actual trace was accepted. The negative main-path test runs only in a temporary tree containing copied public source and the permitted oracle code. No actual receipt path is supplied.

One reviewer-probe setup run initially raised `NameError` because the isolated block's test namespace omitted the harness's `same` helper. Adding that test namespace binding corrected the probe; no harness change was required for this setup error. The complete corrected probe then passed. The deliberately missing receipt is an expected negative test, not an actual operational failure.

## Source comparison and numerical independence

AST comparison confirms that `number`, `independent_predicate` and `oracle_case` are unchanged from v2. The verifier imports neither `research_comparison` nor its `evaluate` function. Its exact Decimal comparisons therefore remain separate from the producer's derivative evaluation. The oracle test feeds the wrapper a report produced by the public deterministic event engine on explicitly invented bars, then invokes the unchanged independent rational comparator with captured output and a bounded timeout. It checks the returned count and tolerance metadata without exposing numerical results.

The v3 source identity now includes `research_failure_context.py`. Its private joins connect the predispatch binding, method observation, failure observation, configuration, role, basis and exact nine-field packet facts. The new exclusions keep direct failure-observation and basis references out of aliases and encoded packet content. The main path uses schema version 3 and a distinct `quality-v3` output directory; its existing exclusive file creation and unique verification identities preserve earlier output.

| Reviewed code | SHA-256 |
| --- | --- |
| Final v3 verifier | `05550ba9cc1d39c1e7584bd87d47f242a2ccb0fc9b7156b05d4015028512e571` |
| Preserved v2 verifier | `d7cf5022ffd67168095f4720421c7ca30cd5ade6c8ae799bcfc69e0445444f6f` |
| Pinned independent oracle | `54887dfae2f12430b5cdd9901c0c3ba367541f6eb4714b987ad68e08f0433ca1` |

Final identities were rechecked after execution. No production source or repository test was changed by this review, and no whole-project suite rerun is claimed for this private verifier-only correction.

## Acceptance limits

This accepts the inspected verifier code and the stated invented-fixture paths. It does not accept a future actual run, attest a provider process or independently establish the truth of failure evidence merely because retained artifacts agree. Current dependency/lineage validation belongs to the qualified-context implementation; the separate actual-trace inspector must assess the relevant retained basis when a real trace exists. A complete actual seven-stage numerical path was not read or executed here.

The reason for the two earlier model stops remains unproven. No third paid attempt occurred as part of this review, and actual-workflow acceptance, R14 and later evaluator/scheduling/paper/live gates remain open.

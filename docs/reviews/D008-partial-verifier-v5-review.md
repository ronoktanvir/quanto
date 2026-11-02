# D008 partial-workflow verifier v5: correction and preparation review

**V5 refuses the unpublished-reviewer contract mismatch reproduced against v4 and passes the existing invented-fixture preparation. Actual execution remains on hold for independent critic recheck and lead authorization.** No actual database, receipt, private artifact, response, credential or environment file was accessed. This is verifier preparation, not actual numerical acceptance.

Producer/reviewer of this separate harness: `/root/d008_broker_quality`, independent of the research implementation and model workers. The independent criticism is preserved in [D008-partial-verifier-critic.md](D008-partial-verifier-critic.md). This report does not replace that role or certify its own independent criticism. Product source/tests, v2/v3/v4, prior reports and actual outcomes remain unchanged.

## Exact revision and retained preparation

| Artifact | SHA-256 |
| --- | --- |
| New `runtime/d008/verify-partial-workflow-v5.py` | `9baac52f086a363e9161796807b2c9d64e0c75df409cb0d82905195d4f5f9018` |
| Preserved v4 | `c0a26e7f205a413e241daee110910fecc49d4924cc24e60b6b156ddbb43a2429` |
| Preserved v3 | `05550ba9cc1d39c1e7584bd87d47f242a2ccb0fc9b7156b05d4015028512e571` |
| Preserved v2 | `d7cf5022ffd67168095f4720421c7ca30cd5ade6c8ae799bcfc69e0445444f6f` |
| Unchanged independent oracle | `54887dfae2f12430b5cdd9901c0c3ba367541f6eb4714b987ad68e08f0433ca1` |
| Adapted existing preparation probe | `887ea5d883ecbbc1636177ac579903c48fdf2469ed655cfffe8bbd403e14ba78` |
| Seven-assignment mismatch regression | `0219755d0fed1b4977e159579310f948a9c9b12ad74eacb716aedc6e3fc26063` |

New ignored evidence is under `runtime/d008/preparation-v5`. The unchanged critic reproducer was rerun solely on a disposable invented fixture; its new bounded baseline output preserves `failed_role_contract_mismatch_accepted=true` for v4. That baseline output has SHA-256 `bac814a6b8a56d6cc014beb56364b069f6172ae42688a4c330f4fa77a968f9e2`. The regression result is `dc496314dfa3f29b0ce2a08511611e0848c8f240cec49617fe6b529d06425e7a`; the existing preparation result is `53cffda9a659d12848f3a7ca31e04a5ca369e6818c0fa5e6cbaacfff6edd02c9`. No original result was overwritten. Temporary UUID-bearing fixture databases were disposed by ordinary cleanup; these bounded outputs and deterministic probe sources do not claim to preserve the original database bytes.

## Required correction

V4 checked published assignments against the frozen manifest but omitted the unpublished failed reviewer's complete contract. The critic changed only scope's `max_spend_micro_usd` by one in a rolled-back temporary transaction; v4 accepted that altered contract because it did not change the rendered request. I reproduced this defect using the unchanged critic probe. It is an audit-coverage defect under the tested row-tampering threat model, not an observation about the actual trace.

V5 adds one roster-wide check immediately after establishing the exact assigned-role roster. Every assignment contract must equal its role's complete frozen manifest contract before any `_audit_partial_dispatch` call. A mismatch raises the fixed `partial_assignment_contract_mismatch` refusal. The existing published-assignment checks remain. The only other differences from preserved v4 are the v5 description, separate `quality-v5` output directory and output schema version 5. There is no policy relaxation or financial calculation change.

The new regression applies the critic's single-field change separately to all seven assigned roles, including unpublished scope, inside rollback transactions. All seven refuse with the exact expected code. An instrumentation guard confirms that no dispatch auditor is reached before the mismatch is refused. Each rollback preserves the entire uncertain reservation row, and the restored valid partial trace passes again with invalid workflow status, incomplete review and operational acceptance false.

## Executed preparation and unchanged boundaries

The existing preparation probe, adapted only to load v5, passes using real local admission, broker, suite and financial code over invented D007 records and injected synthetic envelopes. The scope parser-failure fixture has six published stages, seven synthetic observations, three published reviews and one complete fresh three-child suite. Independent predicate checking covers nine derivative operands; three unchanged oracle invocations compare 282 fixture fields. The full uncertain hold remains unchanged, workflow status remains invalid and operational acceptance remains false.

A separate first-review parser-failure fixture has three publications, four synthetic observations, no published reviews and `not_reached`, with a distinct fresh three-child invocation. Both uncertain holds remain intact. Corrupt comparison bytes, foreign parent binding, wrong cost slot and improperly settled failed hold each refuse. Two mutated-default/report mismatches, four invalid specification field/type/value cases and the strict actual-entrypoint rejection of synthetic evidence also pass. Submitted request bytes remain separate from normalized declared defaults and unchanged.

Python 3.13.12 compilation and Ruff 0.17.3 pass for v5. AST comparison confirms `number`, `independent_predicate` and `oracle_case` are identical to v4. No producer comparison calculation is imported, and no reserve, settle, release, uncertainty-update or dispatch-authorization call was added. The CLI still accepts only `outcome` and `--root`; direct-call fixture mode is not a CLI bypass. Outputs remain bounded integrity/count/code identities without predicate truth, numerical operands, prices, private identifiers or rationale.

## Limits and next gate

V5 retains v4's narrow post-finance exception support: an exact published research prefix, one observed unpublished failed reviewer with an uncertain effect/hold, and one parent-bound successful comparison/new complete three-child suite. Missing observations, ambiguous accounting, multiple unfinished reviewers, changed dependencies or unsuccessful financial lineage refuse. Preparation uses synthetic data and cannot establish actual numerical agreement or actual contract integrity.

The lead-reported third actual attempt remains invalid, scope remains unpublished and the published data critic remains inconclusive. No actual audit or model/financial rerun occurred here. Independent critic recheck of these exact v5 bytes and explicit lead authorization are required before reading the actual saved receipt. Any later numerical pass must remain separate from workflow completion, operational acceptance, R14 and the remaining evaluation, scheduling, paper and live gates.

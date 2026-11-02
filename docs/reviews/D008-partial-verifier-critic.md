# D008 partial-workflow verifier: independent criticism

**Disposition: one P2 correction is required before the actual numerical audit.** V4 preserves the distinction between numerical agreement and workflow acceptance, but it fails to compare the unpublished reviewer's assignment contract with the frozen workflow manifest. The lead should retain v4 and prepare a separately identified revision containing that equality check for every assignment.

Reviewer: `/root/d008_v4_lead_audit`, independent of the verifier producer and research implementation. Reviewed harness SHA-256: `c0a26e7f205a413e241daee110910fecc49d4924cc24e60b6b156ddbb43a2429`. The review inspected public source, the permitted verifier/oracle source and invented fixture preparation. No actual receipt, financial values, private response or credential was accessed. No old audit or actual study was rerun. Product source and v4 remain unchanged.

## Required correction: bind the unpublished assignment contract

In `inspect_partial_workflow`, published assignments must have a contract equal to `manifest["roles"][role]`. The failed reviewer is selected immediately afterward, but that path checks only the review role and distinct actor before calling `_audit_partial_dispatch`. The latter reads its contract and reconstructs the outbound body, but does not compare the full contract with the manifest. Fields that do not change the outbound body can therefore differ from the frozen role contract without refusal.

An independent disposable-fixture probe reproduces the gap. It creates seven invented responses with six publications, an inconclusive data critic and a scope parser failure. The unmodified fixture passes partial lineage checking and remains invalid with operational acceptance false. In a temporary transaction, the probe then drops the fixture assignment-update guard and increments only scope's `max_spend_micro_usd` by one. The frozen manifest, issuance event, body, reservation and all financial results remain unchanged. V4 still accepts the partial trace. The transaction is rolled back and the complete uncertain reservation remains unchanged.

This demonstrates a verifier coverage defect under the row-tampering threat model already exercised by its preparation probes. It does not establish tampering or a changed contract in the actual trace. It also does not show an arithmetic defect. However, an audit claiming to bind all seven observed dispatches to their issued contracts needs the missing equality.

Required fix: validate each assigned role's complete contract against the corresponding frozen manifest role, including the unpublished failed reviewer, before auditing that assignment. Add a regression that refuses the reproduced mismatch while preserving the unchanged valid partial fixture, complete uncertain hold, invalid workflow status and incomplete review. Do not settle a reservation, relaunch research or rewrite an earlier outcome to apply this correction.

## Checks supporting the remaining design

- The partial path uses authoritative registered configuration and requires matching current source identities; it keeps observed responses separate from published reviews.
- Financial lineage binds the selected predicate, engineer request, comparison, fresh three-cost suite, child requests, source identities, admission evidence, result metadata and derivative operands. The independent predicate function does not import producer comparison math.
- Strategy normalization expands the documented `StrategySpec` defaults only. Submitted request bytes retain their separate hashes, explicit values keep their types, and unsupported fields/types/ranges refuse.
- AST comparison confirms `number`, `independent_predicate` and `oracle_case` are unchanged from v3. The pinned oracle SHA remains `54887dfae2f12430b5cdd9901c0c3ba367541f6eb4714b987ad68e08f0433ca1`. This review inspected its source but did not independently execute oracle cases.
- The failed reviewer must remain unpublished with an uncertain effect, no settled amount and the full reservation. The verifier checks that full reservation row again after oracle work. No budget mutation or model dispatch is introduced by this harness.
- The command-line arguments are only `outcome` and `--root`; fixture mode is not exposed as a CLI bypass. A preliminary broad substring check returned false because `fixture_only` also names a public result field; the subsequent AST argument inspection confirms the actual CLI boundary.

## Reproduction identity and limits

New ignored probe: `runtime/d008/v4-critic-probe.py`, SHA-256 `e87d8534fd5544bebb43636e2e6596e6ae76a40a19e97572501acb49fc4079e6`. Its safe output is retained in `runtime/d008/v4-critic-probe-result.json`. It reports `valid_synthetic_partial_trace=true`, `failed_role_contract_mismatch_accepted=true`, `uncertain_hold_unchanged=true` and CLI arguments `["outcome", "--root"]`. Execution completed successfully in a disposable invented-data directory; the temporary original UUID-bearing database was not retained.

These are software-audit observations, not actual numerical validation or model evidence. The supplied actual third workflow remains invalid, scope remains unpublished, the data critic remains inconclusive and operational acceptance remains false. A corrected verifier still needs exact-source independent regression review before the lead's one-time retained-result audit.

## V5 independent recheck and final disposition

**The P2 is closed in v5; the exact revised harness is accepted for the lead's one-time retained-result audit.** Reviewed v5 SHA-256 is `9baac52f086a363e9161796807b2c9d64e0c75df409cb0d82905195d4f5f9018`. Preserved v4 still has the original defect and unchanged SHA above. This acceptance concerns the verifier, not the actual workflow or its uninspected numerical result.

The source diff adds complete manifest-contract equality for every assignment immediately after exact roster validation and before any dispatch audit. The only other changes are the v5 description, separate output directory and output schema version. Independent AST comparison confirms `number`, `independent_predicate` and `oracle_case` remain unchanged from v4.

I adapted my own disposable-fixture reproducer to load these exact v5 bytes, require the expected refusal, then verify the restored original trace. The unchanged partial fixture passes; incrementing scope's contract allowance by one now refuses with `partial_assignment_contract_mismatch`. After rollback, the valid partial trace passes again with `workflow_status=invalid`, `review_outcome=incomplete` and `operational_acceptance=false`. The complete uncertain reservation remains unchanged. No actual receipt, financial value, private response, credential or environment file was accessed, and no actual or prior financial workflow was rerun.

New ignored independent probe: `runtime/d008/v5-critic-probe.py`, SHA-256 `49611d1375ab0b3739a44e2cca479d31d79be774d6fa3743f61682c504a80065`. Its retained safe output, `runtime/d008/v5-critic-probe-result.json`, has SHA-256 `8640e79f25e5ca1bedaa2e00648ac8a31334887b8bf0d9284575e1ef40b23424`. The broader seven-role mutation and oracle preparation results in the producer's v5 report remain separately attributed; this critic reran the original unpublished-scope reproducer and valid-restored fixture, not those broader probes.

# D008 broker integration contract review

The frozen D007 suite can support D008's first bounded operational demonstration without changing financial policy, but replay alone cannot satisfy the model-authored-work requirement. A researcher-selected falsification condition must determine an additional, separately registered calculation. This is a conditional implementation interpretation of accepted D008, not acceptance of an implementation or completion of R14.

Reviewer: `/root/d008_broker_contract`. Inspected repository HEAD `fc1c8c4e3c5f8dd37c77617f6a121d2ed42f57af`, including the policy and source sections identified below. This review read repository material only: no private runtime, environment, provider data, network, paid calls, tests or historical execution. It does not inspect the concurrently developed broker/transport.

## Existing constraints

`policy_revision.validate_study` requires the original dataset, evaluation dates, lookback, thresholds and starting cash, with only the frozen costs accepted. `study_suite._members` requires exactly 0/10/25 bps, identical remaining fields and the same admission. `explorer.run_submission` requires that membership plus a registered invocation and unique child binding. Changing a study name cannot create material scientific work; changing a strategy parameter would correctly refuse.

Admission also remains source-bound. `admission._verify` requires local private use and `external_model_transmission=False`; D008 permits expressly approved method, lineage and integrity summaries, not market records or private results. Models can criticize a method without seeing prices, but cannot certify those hidden prices or numerical outcomes.

One integration hazard is exact code identity. `validate_admission` regenerates the admission and compares it with retained bytes; `_code_identity` includes explorer, admission, policy revision and suite modules. Editing those modules can invalidate the saved admission even when economics appear unchanged. Prefer separate broker/comparison modules; necessary identity changes require explicit new admission lineage, never suppression of identity checks.

## Viable bounded experiment

The supervisor can expose a small supported vocabulary of generic falsification predicates, with no instrument, dates, private rule or result values. The director proposes a question within that envelope. After authorized failure retrieval, the researcher selects and explains a substantive predicate; the engineer translates that actual output into a strict local specification. A generic example is testing whether the strategy fails to exceed its matched benchmark across the complete cost roster. This is a descriptive development calculation, not a significance test or investment acceptance threshold.

The specification must freeze predicate semantics, tie handling, required operands, complete-roster aggregation and missing-result behavior before launch. It must bind exact role output, approved packet, code, suite and admission identities. Register a comparison attempt before executing a new complete suite invocation, then compute only from that invocation's successful children. Preserve all failed, incomplete and uncertain outcomes. Do not substitute previously completed children or select favorable costs.

Materiality is a dependency test: replacing the researcher output with another supported choice must change the registered computation, not merely its label. Synthetic counterexamples can establish that two predicates compute different answers for some valid inputs; the actual historical answers need not differ. The supervisor must not preselect the only possible predicate and solicit assent. Engineer refusal of an unsupported proposal is honest failure evidence, not successful workflow acceptance.

This path can satisfy D008's material-choice limb because the accepted contract explicitly permits a falsification condition to determine a new registered calculation. It can support the first demonstration only after the whole trace exists: five actual model roles, new historical execution, distinct criticisms, independently executed quality and separate scope findings. It does not by itself establish persistent operation, broad research competence or close R14. Current code supplies no such demonstrated trace.

## Prioritized integration gates

1. **Preserve admission and calculation authority.** Route suite execution through existing registered entrypoints; bind the derivative to its exact new invocation and all three children. Reject mismatched code/data, absent children, stale admission and alternative result substitution. Comparison code needs its own identity and independent arithmetic checks; the historical engine's identity does not cover a new module.
2. **Separate local evidence from outbound evidence.** Keep raw suite outputs, comparison values and predicate outcomes local. Even a one-bit predicate outcome reveals a result; it is not automatically an integrity fact. Allow only predetermined, explicitly approved lifecycle/integrity fields into later packets. Validate every generated tool projection and exact reference against the supervisor's grant; a hash is not transmission permission. Record what each critic actually received and the limitation of method-only criticism.
3. **Bind role effects and publication.** Use issued actors, live fences, one-use effect starts and exact upstream handoffs. Register every actual effect before dispatch. A long suite that outlives its lease must retain its calculation records but cannot publish an authorized role handoff. Cancellation and crash reconciliation must not silently rerun either models or studies.
4. **Complete real evidence and budget gates.** Verify observed models and responses, research/global reservations, bounded output and uncertainty handling. The reported remaining USD0.020721 cannot fund the actual cycle; it is a checkpoint supplied to this review, not a freshly audited ledger. Continue local implementation. Do not release uncertain holds or replace unavailable roles. Later criticism, quality and scope must inspect exact integrated artifacts and actual trace before acceptance.

If the derivative path produces only ceremonial choices, retain it as limited workflow evidence. A genuinely new event-simple historical acquisition admitted under existing D006 semantics could permit model-authored supported strategy parameters without loosening D007. That alternative needs retained source/use/identity evidence, provider access, bounded acquisition and later model budget; absence of returned events alone does not establish no actions. It is unnecessary merely to demonstrate the valid falsification-condition path.

## Inspected identities

SHA-256 values at inspection; these identify the reviewed inputs, not later concurrent changes.

| Artifact | SHA-256 |
| --- | --- |
| `docs/D008_POLICY.md` | `91bd473d6972355c8cba447fff7b1e66e9b77bddf9712097ebd0f95bafc07aa7` |
| `docs/D008_PROPOSAL.md` | `4dffac76cf1cf87123772f92db85c58fe8d02ccb782074989f717aaa3ed8c97e` |
| `docs/D007_POLICY.md` | `bf8c254645c33550fceb19b794a3aeae933c54d635df149fccda8310f5e987ce` |
| `docs/RESEARCH_WORKFLOW.md` | `530ee70b2321a61664e8915a93d08e3c270d20b343c6ca60a5133cb39c51740f` |
| `docs/REQUIREMENTS.md` | `51ddac9cc894708ecd7f7502be24a9b0c016556a64a60fc6f3ca72475780dd38` |
| `src/quanto/policy_revision.py` | `eb7ac89bbf1c85cf276f614bd296ad82f2d22f94d723788a3718c42ff5b12625` |
| `src/quanto/study_suite.py` | `c3e552ef9998e72ae6f69b55bf43750d51f94522faf98a26ecbb624042f46360` |
| `src/quanto/explorer.py` | `6a3f02d27f0c062d993ee3d112f0e76b88221fc8653305b84be62b822bcb9745` |
| `src/quanto/admission.py` | `5b1d5aa7d9aea6488ba96ac8a89a597d37e78ad28be0175699f6032abb8787c1` |
| `src/quanto/research_workflow.py` | `0228249ce64d433886bd85c4dd4b8da161656eb78f40e1ffec419eec5c913b47` |

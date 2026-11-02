# D008 qualified failure context: independent execution quality

**The qualified failure-context increment passes independent execution quality at the exact identities below.** Final source and clean noneditable suites both pass **1256 tests plus 12 subtests**. Lint and independent invented-fixture checks pass for exact lineage membership, provisional/evidence qualifications, current-state freshness, one-use proof and retrieval binding, atomic rollback, bounded egress and continued refusal freedom. No execution-quality blocker remains within this increment.

This is `synthetic_fixture` software evidence. It does not establish why either actual model stopped, demonstrate a completed actual cycle or authorize a third paid attempt. The historical refusals and two actual stopped attempts retain their original outcomes. Actual-workflow acceptance and R14 remain incomplete.

## Independence and exact reviewed inputs

Reviewer: `/root/d008_broker_quality`, separately assigned from producers and criticism. Base checkout: `92ec9bad31d1a240bb220211cd29cabd2e49294d`; exact hashes identify the uncommitted increment. The reviewer read the failure-context contract, revised actual-trace criticism, helper/broker/packet implementation and tests, then began final execution only after the lead's explicit source freeze.

This review changed no implementation or repository test. Its only repository output is this report. All executions used temporary invented fixtures. No actual project runtime, private market data, environment file, credential, external network or paid model was accessed. Earlier reports, private harnesses and actual receipts were not reopened for execution or altered.

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/research_broker.py` | `aa4f9e93f9fc471273bf2e6c1a0d67acb74583228618cecd17aa9ec513419e34` |
| `src/quanto/research_packets.py` | `ead052fb0fe53576eff02a5f7138af16a58b70c0c5fbd164eb196f4af92e0a93` |
| `src/quanto/research_failure_context.py` | `b99af35355b14d638770c069791124a8d72774346e5a9677ac74d607bc777208` |
| `tests/test_research_broker.py` | `3e641933b374dfed7007cb0e1a4fd5fe121dc7aed38b18f84ef7c0b6e79ae061` |
| `tests/test_research_packets.py` | `b156abdedbc5df734856dcabcb02ff4a17d3e0925c09de3ba6d2ffd06767430a` |
| `tests/test_research_failure_context.py` | `1c8c47c7430a447fc3e5b6c4698c45eb34fe1e5a193e9aa06dfb1739634765ff` |
| `src/quanto/failure_memory.py` | `ee8200079cc0e091b06d60be6fe4ccb3d4886eb1ea986ee626db65ae7f9f7ee7` |
| `src/quanto/research_workflow.py` | `64ca63f155a2417021bb8632673f14ec12ff7d497881aa13a95d7330911ab02b` |
| `src/quanto/research_dispatch.py` | `120834deb63abebeeb54a14f8cf470ad43fd9ac1f44979ee96fe9c88ba20c1f1` |
| `src/quanto/research_comparison.py` | `c2e933841f1664b62528b4342b37a34e7b3452e7783d91f495f78a6b05d65446` |
| `src/quanto/policy_revision.py` | `eb7ac89bbf1c85cf276f614bd296ad82f2d22f94d723788a3718c42ff5b12625` |
| `src/quanto/study_suite.py` | `c3e552ef9998e72ae6f69b55bf43750d51f94522faf98a26ecbb624042f46360` |
| `src/quanto/admission.py` | `5b1d5aa7d9aea6488ba96ac8a89a597d37e78ad28be0175699f6032abb8787c1` |
| `src/quanto/explorer.py` | `6a3f02d27f0c062d993ee3d112f0e76b88221fc8653305b84be62b822bcb9745` |
| `src/quanto/ledger.py` | `29c3f14bdae924b4d369b49b59c3ec7e5079810d76e55992fa1800d49a3da6cf` |
| `src/quanto/provenance.py` | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |
| `tests/test_admission.py` | `fd8c3c2c4faeea6c1923b82bf3223bca5d2532e45238792849e616d6005bf9f3` |
| `tests/test_policy_revision.py` | `52962b9953bd1c11aa5add4b23f5f513c9f9d9f2ccbead3e7a8286ab54584765` |
| `docs/D008_POLICY.md` | `91bd473d6972355c8cba447fff7b1e66e9b77bddf9712097ebd0f95bafc07aa7` |
| `docs/reviews/D008-applicability-contract.md` | `5184df4d0bece7b76a9ef7c2ef883cf17e5aff20210a84e98852f20228fa2950` |

Ten supporting implementation modules, including memory, workflow, dispatch, comparison, policy revision, suite, admission, explorer, journal and provenance, were independently compared with HEAD and remain byte-identical. The financial policy and its pinned admission/calculation identities were not relaxed.

## Executed suites and installation

Source Python **3.13.12**, pytest **9.2.0** and Ruff **0.17.3**: **1256 passed, 12 subtests passed in 185.87 seconds**, with repository lint passing. A new offline-built wheel installed noneditably under Python **3.11.9** passed the same **1256 tests plus 12 subtests in 185.10 seconds**, with clean-tree lint and independent probes also passing. The helper, packet and broker test modules contain **288 collected cases**.

The clean tree copied only public source, tests, docs, scripts and packaging files, excluding runtime, data and environment files. Cached tooling built a wheel offline, created a new Python 3.11 environment and installed the wheel plus cached pytest. No dependency download or network fallback occurred. Tests used `-o pythonpath=` to disable repository source-path injection. Actual `quanto.__file__` resolved beneath the temporary environment's `lib/python3.11/site-packages/quanto`, outside the repository. The existing Ruff checked its `src tests`.

Commands included:

```text
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
PYTHONPATH=src .venv/bin/python /tmp/d008_applicability_quality_probe.py
uv build --offline --wheel --out-dir wheels
uv venv --offline --python python3.11 .venv
uv pip install --offline --python .venv/bin/python 'pytest==9.2.0' wheels/quanto_research-0.1.0-py3-none-any.whl
.venv/bin/python -m pytest -q -o pythonpath=
.venv/bin/python /tmp/d008_applicability_quality_probe.py
```

The build/install, installed suite and final probe commands ran in the disposable clean tree, with `uv` addressed by its existing absolute executable path.

The observed wheel has **181317 bytes**, **34 entries** and SHA-256 `23a07c61d16418542c565b90bacfb89e79cb6d9c831709f5627df2879f1c6f2c`. Every packaged Python module equals the frozen source; all three web assets are present, with no runtime, database or environment entries. These are observed archive bytes, not a reproducible-ZIP claim. Final source, clean-tree and package identities agree.

## Independent semantic and freshness probes

The new reviewer-authored `/tmp/d008_applicability_quality_probe.py`, SHA-256 `91d5a22f0ea862c33be18a539aa31ab0584018eb4ecf0acd13ad3c3bdbdf3fa6`, passes against source and the installed wheel. It uses the existing invented-source `regular_way_fixture` constructor and actual unmodified admission, suite, revision, memory, workflow and financial entrypoints. The reviewer wrote its own actor, evidence checks and adversarial substitutions; model transports remain synthetic regardless of the model names in their envelopes.

**Exact historical membership is distinguished from resemblance.** The fixture's two source-bound original refusals receive `prior_refusal_in_bound_revision` after real current D007 validation. A generic submission with the same refusal code remains `no_relation_established`. A deliberately created experiment attempt shares an identifier with one prior submission but still receives no relation because its source namespace is `attempt`. All original outcomes remain unchanged. Matching a code or identifier string is therefore insufficient; the exact source, original request/outcome and validated revision chain govern the positive relation.

**The nine fields preserve uncertainty and evidence scope.** A seven-record scenario includes both lineage members, a generic nonmember, the coincident-ID attempt, an explicitly unresolved claim, a corrected claim and a pending original. The default unresolved value remains distinguishable from an actually recorded unresolved disposition. Claims remain provisional; the corrected claim does not rewrite the original invalid outcome or certify a repair. Its original and fix evidence remain `not_allowed` under the context helper's empty artifact grant, even though the writer had earlier verified the fix. Private proof records separately retain that the original bytes remain available and the fix has subsequently become unavailable. Lineage validation never upgrades the memory service's approved-subset evidence label.

**Identical outward facts do not make an old basis fresh.** Appending a second unresolved claim with identical visible fields changes its latest disposition identity and causes old-observation revalidation to refuse. An explicitly new test retrieval can produce the same visible nine-field facts, demonstrating that identity, not merely the outward text, triggered refusal. Tombstoning a currently required suite-registration dependency also refuses preparation/revalidation rather than converting a positive relation into `no_relation_established`. Later valid role observations reuse the exact authorized basis without another memory query. The full test suite additionally covers changed original pending outcomes, changed evidence availability, forged lineage and observations, incomplete/duplicate/wrong-source query receipts and missing or corrupted revision/admission/source dependencies.

## Independent binding, transaction and privacy probes

A trusted manual test supervisor exercises live assignments, claims and intents without calling models. Observations prepared before assignment issuance refuse; the same observation cannot bind another request; a proof for a different configuration refuses. These tests preserve the normal broker's validator and journal paths rather than replacing them with approval Booleans.

A basis already bound to an earlier synthetic run cannot stand in for the newly started query effect of another run. A separate adversarial case creates a fresh registered wrapper around an older exact query receipt. That wrapper also refuses: the query did not start and finish within the new basis's preparation interval. Both probes issue zero new memory queries and zero paid dispatches. These checks independently exercise the two retrieval-lineage bypasses identified in the separate criticism; a fresh wrapper does not manufacture fresh worker activity.

The rollback probe enters the actual hypothesis packet binder, inserts a marker inside its existing journal transaction, runs real failure-context revalidation and then deliberately raises a fixed refusal. Revalidation remains in that same transaction, the marker rolls back and the original memory-query count does not increase. Thus neither implicit schema commits nor a hidden retrieval refresh convert failed binding into a published effect. Normal unrelated journal events may advance the head; the specific evidence basis is what must remain valid.

A complete seven-stage synthetic run captures every rendered request body, including its fixed system prompt and context. All private configuration/suite/revision/basis/proof/dependency identities, observation identities, original failure IDs, invented dates/instrument strings, raw rationale and predicate truth remain absent. Every stage's aliases are checked against the complete accumulated private proof-reference set, including references discovered later. Private observations remain retained without becoming model input aliases. Only the authorized nine-field facts cross the failure-context boundary; the director still receives an empty failure list.

That complete invented-data run uses exactly one original memory query, executes one fresh suite and three children, preserves the original failure records and retains a statistical-critic block with `operational_acceptance=False`. A separate hypothesis-stop run ends invalid after two synthetic stages and launches no financial suite. Qualified context does not compel a favorable review or a decision to proceed.

## Review history and acceptance limits

The first reviewer-authored probe passed its semantic, relation and freshness assertions but then failed an arbitrary assertion that the temporary journal must contain more than 100 events. Intermediate probe SHA-256: `5df58bdeee5b063b9021b449381d1f3b1b3e1473f35e8d0158dc7e3dda95e5e0`. This was a reviewer-harness size assumption, not a product failure. The assertion was replaced with successful event-chain verification; no implementation or repository test changed, and the complete corrected probe then passed in both environments. Both final full suites passed without a product-test failure.

The [separate critic](D008-applicability-critic.md) preserves its original cross-run basis finding and the fresh-wrapper variant, plus their producer fixes and independent rechecks. The final reviewed code requires the basis to follow the exact current effect, rejects prior basis binding and verifies each query's start/finish within the basis interval. This quality review independently exercised both repaired cases rather than treating the critic's pass as its own execution.

The result accepts qualified historical context and its bounded application proof. It does not certify evidence truth, repair efficacy, current refusal applicability, investment performance, data-use rights or protection against a privileged owner. The added relationship must not be described as clearing either historical refusal. The reason for the two earlier actual stops remains unproven; no third actual attempt or completed operational cycle is demonstrated. Separate scope acceptance, actual-role/historical acceptance, protected evaluation, persistent scheduling/restore and later paper/live gates remain required.

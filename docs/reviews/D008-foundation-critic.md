# D008 foundation: independent adversarial implementation criticism

Review outcome: both confirmed P2 workflow defects were corrected and independently re-probed successfully. No unresolved blocker was found for integrating this bounded foundation at the final identities below. This is criticism of the reversible local workflow-state and metadata-retrieval foundation only; it does not certify real research roles or close the operational requirements. D008 policy acceptance and implementation acceptance remain separate.

## Scope and evidence

The critic read AGENTS, project context/status/roadmap/decisions/handoff, D008_PROPOSAL, and the D008 roles, operations, and data-boundary briefs, then the accepted D008_POLICY; inspected the two new modules and their tests, with relevant ledger/provenance transaction and object-reading behavior. The initial inspected Git HEAD was `2f59f105e0e34339958a8354afd4246a11123ff7`; uncommitted artifacts are identified separately below.

| Initial artifact | SHA-256 |
| --- | --- |
| `src/quanto/failure_memory.py` | `ee8200079cc0e091b06d60be6fe4ccb3d4886eb1ea986ee626db65ae7f9f7ee7` |
| `src/quanto/research_workflow.py` | `6bdf0d303de8b398736818a37e8a7d2745e2152ff138af917c57d7484bde069d` |
| `tests/test_failure_memory.py` | `68180c3f94209a79d54187aa55dec33aa6322bdbac76990c761a0b77f3dd4057` |
| `tests/test_research_workflow.py` | `cd8598bf87cf87eda5f0fe30db568f1614d6e5702c82924723b8788a9e37768b` |

All executed probes used synthetic temporary directories. No project runtime, private data, environment/credential files, network, provider, or model was accessed. No implementation file was edited. The critic's sole owned repository artifact is this report.

## Confirmed findings

**P2 — an issued capability could be retained as ordinary metadata.** `claim_stage(token, 'worker-' + token)` accepted a valid capability echoed into the worker identifier. Independent execution found the exact raw token in both `workflow_claims.worker_id` and the `workflow_stage_claimed` event payload. The fixed credential-pattern expression recognizes common API credentials but not the randomly issued workflow capability. This breaks the claimed digest-only persistence boundary and permits a later event reader to obtain a still-live capability. It is a disclosure through accepted fields, without direct database tampering. Correction must exclude issued capabilities from every persisted caller field, including embedded occurrences, and keep denials free of raw token bytes.

**P2 — rejected worker transitions disappeared from the attempt history.** Independent execution of `start_intent(token, worker, 1, 'never-authorized')` and `finish_handoff(token, worker, 1, {'bad': 'schema'})` raised `WorkflowError` but added zero events. Only `authorize_intent` durably recorded its denials. Thus invalid starts and rejected publications were absent from retained chronology. Correction must record sanitized operation-level refusals around every worker-facing transition, after transaction rollback, while excluding token/request content.

Both findings were sent immediately to the lead and producer. **Both are corrected at the final checkpoint.** Bounded screening hashes token-shaped substrings and checks indexed issued-token digests before caller metadata or admitted artifact references are retained. The original worker-ID echo and an embedded cross-run request-ID echo now refuse without writing raw tokens. A denial wrapper now covers authenticated worker transitions and privileged mutation APIs; the original invalid start and malformed handoff each append one sanitized operation-level denial after rollback. These are caller-contract denials, not a claim that storage failure can always be durably logged.

The producer additionally rechecks live lease state after artifact verification/publication, refuses zero-allowance model intents, reports failed/blocked and uncertain runs distinctly, and recognizes credential keys in strict JSON. The critic inspected these changes and re-ran the targeted suite. An independent expiry probe confirmed that an already-started effect cannot publish after expiry and recovery reports an uncertain run with no effect outcome written.

## Final reviewed checkpoint

| Final artifact | SHA-256 |
| --- | --- |
| `src/quanto/failure_memory.py` | `ee8200079cc0e091b06d60be6fe4ccb3d4886eb1ea986ee626db65ae7f9f7ee7` |
| `src/quanto/research_workflow.py` | `0228249ce64d433886bd85c4dd4b8da161656eb78f40e1ffec419eec5c913b47` |
| `tests/test_failure_memory.py` | `68180c3f94209a79d54187aa55dec33aa6322bdbac76990c761a0b77f3dd4057` |
| `tests/test_research_workflow.py` | `6f8bd6c0ccb1526ca1a3eef35b5d503d81985e00c2dfc75c0032838bc6d416d8` |

An intermediate fix checkpoint (`8bf2bea8…`, workflow tests `e6ffb302…`) also passed independent re-probes. The final checkpoint adds JSON credential-key screening; the critic repeated token, denial and expiry probes and the complete targeted tests after that change. Acceptance in this report applies only to the full final hashes above.

## Executed checks

`uv run pytest -q tests/test_failure_memory.py tests/test_research_workflow.py` initially passed **58 tests**. These include producer-written concurrent claim, stale fence, cancelled stage, crash/reopen, wrong-model outcome, exact review-set, bounded query, redaction, damaged object, and transactional publication checks. Passing those tests did not cover the two adversarial cases above. At the final checkpoint, the same command passed **62 tests**. `uv run ruff check src/quanto/failure_memory.py src/quanto/research_workflow.py tests/test_failure_memory.py tests/test_research_workflow.py` passed. These executions supplement criticism; they do not replace the separately assigned quality role or a clean-install validation.

Additional independently authored inline probes demonstrated:

- The capability echo and two missing-denial cases exactly as described above.
- Failure retrieval with an unapproved code, private synthetic detail and unapproved artifact returns `undisclosed` and no artifact reference, without projecting the private fixture content.
- An injected `RuntimeError` during correction publication rolls back the correction row, preserves the original invalid failure, retains the correction attempt as pending, and leaves the event chain verifiable.
- Both a blocked handoff and a failed effect reported a blocked run; downstream stage issue was refused. The final source retains that state aggregation.
- At the final checkpoint, the original token-echo and missing-denial reproductions refuse with durable sanitized evidence; a cross-run embedded token also refuses, event payloads and public status contain no token, and an expired started effect cannot publish or acquire a fresh automatic attempt.

A first attempt to hash files using the host's Perl-based `shasum` failed because of its locale configuration. Python SHA-256 subsequently produced the identities above. That tool failure did not execute or modify product behavior.

## Limits and remaining gates

Tokens and fixed role labels enforce only cooperating-client authority. They do not prove that seven distinct humans/models/contexts performed independent work, and same-user filesystem/database access remains privileged. The trusted broker must admit sanitized artifacts, constrain the visible failure IDs, and keep provider credentials/dispatch accounting separate. Failure-memory formatting alone is not authorization or a source-rights decision.

These tests and probes establish software behavior on `synthetic_fixture` inputs only. No real five-role workflow, model transport, historical experiment stage, protected evaluator, statistical inference, prospective paper operation, live execution, unattended scheduling, backup restore, or hostile-owner isolation was exercised. The separate Fable/Opus council responses concern policy criticism; they are not implementation acceptance. Independent quality validation and no-drift review remain separate from this criticism.

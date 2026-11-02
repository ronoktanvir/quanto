# D008 qualified failure context: independent implementation criticism

Status: the P2 retrieval-lineage finding is closed after independent rechecks of both bypasses; no blocking implementation finding remains within the qualified failure-context contract. The narrow historical-membership meaning is supported by the implementation design; it does not classify a refusal as corrected or currently inapplicable and does not authorize another paid attempt. The original two stopped traces and R14 remain incomplete.

Reviewer: `/root/d008_broker_critic`, independent of implementation producers and the quality/scope reviewers. Base revision `92ec9bad31d1a240bb220211cd29cabd2e49294d`, with changed artifacts identified below. I inspected the separate applicability contract, helper, broker, packet validator and tests. Executed probes used temporary invented data and injected model responses only. No project runtime, environment file, credential, actual provider data, network, paid dispatch or historical runner was accessed. I changed only this report.

## P2: an earlier run's retrieval basis can be rebound as the current query effect

The initial `_bind_failure_basis` checked the current parent, hypothesis assignment, live fence and started `query_failures` intent, but only read the supplied basis bytes before recording its binding. It did not establish that the registered basis and its memory queries were created within this specific effect or prevent the same basis being bound to another parent.

Independent reproduction ran two synthetic workflows with the same authorized failure scope, each stopping at hypothesis. After the first workflow, I replaced the retrieval return value with the first workflow's valid basis for the second workflow. The second workflow still dispatched and published both director and hypothesis. Both parent binding events referenced the same basis, while the total `failure_memory_query` count remained one. Thus an earlier retrieval could be represented as the newly consumed query effect even though its outward facts still happened to match current evidence.

Required repair: verify the registered basis and exact grant, require its start after this exact effect's start, require every retained query's start/finish inside that basis's preparation interval, and reject prior binding of that basis to any parent. A fresh wrapper around old query receipts must not bypass the interval check. Empty authorized scope still needs a fresh registered basis but no memory query. Revalidate these facts before publishing successful current-query evidence. This adds no model egress and changes no historical outcome.

The broker portion was subsequently repaired to require basis registration after the exact effect start and reject any prior binding of the basis. I independently reran the original cross-run reproduction: the second workflow now sent only its director, refused at basis binding, retained only the original basis binding/query, and performed no financial work.

A second independent reproduction confirms why receipt chronology must also be checked: I registered a fresh copy of the valid basis with a new submission identity while retaining the old memory-query receipts. Before the helper repair, `verify_failure_context` accepted that new basis and emitted a valid hypothesis observation; the memory-query count remained one. A newly registered wrapper cannot establish that its underlying retrieval occurred in the current effect.

The helper now derives the exact event positions of the basis and every retained query and requires `basis_started < query_started < query_finished < basis_finished`. I independently reran the fresh-wrapper reproduction: the wrapper was refused, the genuine original observation/basis remained valid, and the query count remained one. **P2 closed for both bypasses.** No original retrieval, failure or disposition was rewritten.

## Supported semantics and controls

The nine-field packet distinguishes unchanged status, default versus recorded disposition, provisional claim semantics, the memory service's approved-subset artifact checks and a narrow revision-lineage relation. The prompt explicitly says that neither available bytes nor historical membership establishes repair, current applicability, safety, review certification or permission to execute. Model stop/block decisions remain available; no default predicate or instruction to discount a refusal was introduced.

The helper obtains relations through full current suite/admission/revision validation. A positive relation requires an exact authorized submission identity, original request digest/bytes, original invalid outcome/code and matching event positions in the validated revision's `prior_refusals`. Matching a code or a same-looking experiment attempt cannot establish membership. Unrelated records get the negative relation only after the current basis verifies; missing dependencies cause refusal rather than a negative assertion.

Current failure and disposition snapshots are compared with the originally retained retrieval basis at every dependent packet. This comparison includes latest disposition identity, even if its visible state is unchanged, original outcome evidence and private reference availability. The memory service still receives no artifact-reference transmission grant. Separate lineage validation therefore does not upgrade `not_allowed` to `verified`. Generic requests whose bytes were not retained are explicitly distinguished from the source-bound refused requests used for positive lineage.

The broker's final packet binder revalidates within the live-lease transaction, compares exact packet facts and method/configuration/suite/revision identities, requires the current run's successful basis binding, and prevents observation reuse or a preparation predating assignment issuance. Private basis, source, disposition and observation identities remain outside aliases and model packets. The helper avoids invoking schema initialization during this transaction, which would otherwise risk an implicit SQLite commit.

## Independent executed evidence

The first independent focused run reported **284 passed, one failed in 71.62 seconds** across helper, packet and broker modules. The failure exposed a test setup error: the stale-disposition integration test constructed `FailureMemory` with an empty code allowlist, so `append_disposition` refused before changing any claim. The expected `broker_failure_context_refused` was consequently not reached. This is retained as a failed verification attempt; it is not counted as a passing stale-state test.

My separate probe explicitly allowed `other_refusal`, created an unresolved disposition, and appended another identical-visible unresolved disposition between hypothesis preparation and binding. The changed identity correctly refused the second send with `broker_failure_context_refused`; only the director response existed and no financial launch occurred. This tests actual stale-state detection rather than a refusal to create the test condition.

A second independent probe placed a write marker inside an outer journal transaction, revalidated the exact failure context, then deliberately raised an error. The marker rolled back and no additional memory query appeared. This confirms that revalidation does not commit its caller's transaction or silently refresh its retrieval.

The producer's tests inspected cover positive/negative lineage, wrong-source records, corrected versus unresolved claims, absent claims, exact receipt sets, truncated/duplicate or forged receipts, stale latest dispositions, unavailable/corrupt dependencies, observation/configuration/role mismatch and unchanged original outcomes. The corrected stale-disposition fixture now grants its explicit code before appending the claim; final execution results are recorded below.

After both P2 repairs and the fixture correction, I independently reran the complete helper, packet and broker modules: **288 passed in 100.86 seconds**. Targeted Ruff passed. The existing ledger, provenance, research/event engine, admission, explorer, policy revision, suite and FailureMemory source files remain byte-identical to the base revision. The new helper, broker and packet source carry the correction; historical financial/source identities were not relaxed.

## Boundaries

This implementation can establish only the qualified relation stated in the packet. It does not establish why either earlier actual model stopped or whether the revised context will lead to a meaningful hypothesis. No historical failure was relabeled corrected, no financial policy or admission condition was relaxed, and no protected/evaluator/scheduler/paper/live capability is accepted here. Independent quality and scope remain separate gates.

## Final inspected identities

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/research_failure_context.py` | `b99af35355b14d638770c069791124a8d72774346e5a9677ac74d607bc777208` |
| `src/quanto/research_broker.py` | `aa4f9e93f9fc471273bf2e6c1a0d67acb74583228618cecd17aa9ec513419e34` |
| `src/quanto/research_packets.py` | `ead052fb0fe53576eff02a5f7138af16a58b70c0c5fbd164eb196f4af92e0a93` |
| `tests/test_research_failure_context.py` | `1c8c47c7430a447fc3e5b6c4698c45eb34fe1e5a193e9aa06dfb1739634765ff` |
| `tests/test_research_broker.py` | `3e641933b374dfed7007cb0e1a4fd5fe121dc7aed38b18f84ef7c0b6e79ae061` |
| `tests/test_research_packets.py` | `b156abdedbc5df734856dcabcb02ff4a17d3e0925c09de3ba6d2ffd06767430a` |
| `docs/reviews/D008-applicability-contract.md` | `5184df4d0bece7b76a9ef7c2ef883cf17e5aff20210a84e98852f20228fa2950` |

# D008 role-output clarification: independent implementation criticism

**Disposition: accepted within the narrow role-output clarification contract; no required implementation finding remains.** The change explicitly communicates existing decision and predicate rules while preserving every decision, the strict parser and conservative failure history. This is implementation evidence from invented fixtures, not evidence that the new prompt will change actual model behavior or authorization for another paid attempt.

Reviewer: `/root/d008_broker_critic`. Inspected detached worktree `/Users/ronoktanvir/.codex/worktrees/role-output-clarification/quanto` at `75910f399333eb98f09b23f07715bec19c980cfc`, based on `37721ee`. Only `src/quanto/research_packets.py` and its test file differ from that base. The reviewer owns only this new report in the primary checkout. Product source in the primary checkout, previous reports and runtime were untouched; no merge, cherry-pick, push, actual model/network call, private runtime/data read or credential/environment-file access occurred.

## Contract fidelity

`ROLE_DECISION_BLOCK` deterministically renders the existing `_DECISIONS` mapping in `ROLES` order, with sorted enum values. It contains fixed program constants only. `SYSTEM_PROMPT` includes that block once and remains identical across all seven roles; it introduces neither a context field nor a per-assignment system-prompt interface.

The new text requires output role equality and explicitly names `engineer`, `data_critic`, `statistical_critic`, `quality` and `scope` as preserving the exact hypothesis-proposed predicate. It applies that requirement to engineer `stop` and reviewer `block`/`inconclusive`, explains that predicate retention is not a truth assertion or endorsement, and forbids replacing the test identifier with a conclusion. Director-null and both existing hypothesis-stop forms are stated accurately. The generic stop/block sentences now defer to the role's permitted enum, while all four review roles are explicitly allowed `inconclusive`.

The text directs no preferred decision, default predicate or favorable review. It explicitly warns against preferring agreement merely because earlier stages completed, integrity checks passed or a failure has reviewed lineage. A model can still propose or stop, execute or stop, block, remain inconclusive or report no blocking method issue as permitted by its role. No response example supplies a favored answer.

An independent AST comparison against the base removed only `SYSTEM_PROMPT` and the newly added `ROLE_DECISION_BLOCK` assignments; all remaining module syntax matched. Thus parser functions, packet/projection schemas, accepted codes, bounds and data-access behavior did not change. The changed-file inventory confirms no broker, transport, financial, budget, failure-memory or source-admission implementation change.

## Executed independent checks

The primary virtual environment's executables ran with the isolated worktree as working directory and explicit `PYTHONPATH=src:tests`. The imported `quanto.research_packets` path was checked against the worktree before testing. This prevents an editable installation of the primary package from accidentally satisfying the review.

- **Targeted existing/new suite:** `tests/test_research_packets.py`, `tests/test_research_broker.py` and `tests/test_research_dispatch.py`: **393 passed in 57.02 seconds**. Targeted Ruff passed.
- **Independent decision/predicate matrix:** 490 cases used a separately stated expected role map, the complete existing decision vocabulary plus invented invalid labels, all supported predicates, null, booleans and an unsupported predicate. Acceptance/refusal matched the expected contract. This independently checks both negative decisions and exact predicate retention rather than merely comparing the new block with the same source constant.
- **Determinism and identity:** all seven rendered packets used the same fixed system prompt; separate processes with hash seeds 1 and 83 produced the same prompt hash. The prompt is 5,942 UTF-8 bytes. Retained synthetic failure-context observations contained that exact new prompt identity.
- **Independent partial-history probe:** a synthetic data critic returned `inconclusive`; synthetic scope returned an invented invalid decision and invalid predicate. The run retained seven observations and six published stages, with `review_outcome=incomplete`. Scope's exact rejected response remained private, its effect and reservation remained uncertain, its full reservation was retained without a settled amount, and its job was failed. The earlier inconclusive projection stayed inconclusive. A same-run repeat was refused before any extra transport call; all seven reservation records remained unchanged.
- **Egress and call boundaries:** the independent probe blocked credential lookup and actual network-send functions. Only the injected synthetic transport ran. The rejected response reference was absent from model aliases and effect output references. Complete outbound contexts omitted private rationale/detail sentinels, source/failure identities, rejected tokens and predicate truth. No actual response was copied into the fixtures.

All independent probes passed on the final inspected bytes. No product test failed during this review. One final artifact-hash command used an unavailable unqualified `python` executable in the worktree shell; it was rerun successfully with the explicit primary virtual-environment interpreter. That shell-tooling issue did not execute or invalidate a test.

## Request and spending bounds

The producer's maximum-structure envelope test passed, and the critic separately derived a conservative JSON-escaping bound from the unchanged schema: at most 32 aliases, 16 nine-field failures, six prior outputs and eight findings per prior output. Counting every possible string/key gives at most 4,488 additional quotation escapes. Adding that bound and the unchanged 24,000-byte context ceiling to each model's prepared empty-content request gives:

| Model | Conservative request bytes | Conservative reservation, microUSD | Existing per-stage limit, microUSD |
| --- | ---: | ---: | ---: |
| `claude-haiku-5-5` | 34,580 | 105,236 | 125,000 |
| `claude-opus-5-5` | 34,579 | 882,840 | 1,000,000 |

Both fit the unchanged 40,000-byte request limit. These are software bounds computed from current local wrapper rates and token ceilings, not paid calls, invoices or guarantees about unrelated account usage. The correction requires no increase in per-call, purpose or shared daily spending authority.

## Disposition and remaining gates

The implementation matches the recommendation in `D008-role-output-contract.md`: a fixed deterministic all-role block, explicit predicate rules and preserved decision freedom, with no parser repair, permissive fallback, automatic correction or retry. It remains routine implementation within accepted D008. Separate quality and scope review, ordinary integration checks and completion of the frozen actual audit remain the lead's gates; this critic report does not replace them.

The third actual attempt and all earlier invalid outcomes remain unchanged. Nothing in these tests establishes that omitted role names caused the observed scope error or that the clarification would have prevented it. A successful synthetic complete run is not a completed actual role operation, numerical validation, R14 acceptance or live readiness.

## Exact artifact identities

| Artifact | SHA-256 |
| --- | --- |
| Worktree `src/quanto/research_packets.py` | `dbfa9010a52581c78179f2e9b2451ebfc1143cbb915437104d7efeaaf58e97eb` |
| Worktree `tests/test_research_packets.py` | `06c20179370ce6233bd5cf3cd2f096852c603f1cb77413b07bf94038c8d2e428` |
| Rendered `SYSTEM_PROMPT` | `a1b540249cffad25f8bac66f28dd91b6f7a65041a3d22efd16d9401aa47f6d80` |
| Temporary independent critic probe | `ed9d2b1a13265b70fdbcea0366c6f04ada7ada94091bf939a87a76b7c5d44935` |

The isolated worktree remained clean after inspection. No implementation fix was requested or applied by this reviewer.

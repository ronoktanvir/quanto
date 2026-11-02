# D008 operational research roles perspective

Recommendation: build a durable role supervisor with a deterministic capability broker, initially using bounded text API workers for the five research roles. Keep Fable/Opus council on the owner's signed-in Claude Code route. Persistent identity, work and memory should live in Quanto's journal and artifacts; an indefinitely running model conversation is neither necessary nor sufficient. Protected final evaluation must be a separate service capability, unavailable to all five ideation roles.

This is independently briefed design advice, not implementation certification. I inspected AGENTS, CONTEXT, STATUS, REQUIREMENTS, ROADMAP, DECISIONS, HANDOFF, D007 council records, and the five modules below at Git HEAD `4cf7c3f7628475f99a493ae28203728e96a1b5ab`. I did not inspect runtime, data, credentials or private values, invoke a paid model, run a financial experiment, or review other D008 advisers. No external SDK features are assumed. The adviser is another native Codex process, not an independent human or a persistent service worker.

## What exists and what it does not establish

`ledger.py` already supplies append-only application events, attempts, budget reservations and fenced job completion. `provenance.py` binds bounded submissions and exact artifacts. `explorer.py` records development exposure and registered computation. These are useful foundations. They do not yet supply authenticated role assignments, complete handoffs, role-specific tool authorization or final-evaluation isolation.

`conversations.py` explicitly creates new contextual assistants with no action authority. `provider.py` returns bounded text and supports only conversation/operations purposes. Operational workers need a separate caller contract and research allowance; reusing a chat identity or pretending its response executes work would misstate R14. `Journal.record_review` checks supplied producer/reviewer strings, so it cannot establish independent authorship. The new supervisor must derive actors from issued assignments rather than trust model-supplied identity fields.

Inspected file SHA256 identities:

| File | SHA256 |
| --- | --- |
| ledger.py | `29c3f14bdae924b4d369b49b59c3ec7e5079810d76e55992fa1800d49a3da6cf` |
| conversations.py | `a704d127f14df9dc6d6757f6182c899e875d58ea46292666b53efeb2ec46a8a3` |
| provider.py | `78b4de24c1d29c4303c6b8ed499fe6d206fbc64b14800c7132217646b1d6f94d` |
| explorer.py | `6a3f02d27f0c062d993ee3d112f0e76b88221fc8653305b84be62b822bcb9745` |
| provenance.py | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |

## Role capability boundary

The director proposes bounded assignments, resolves documented objections and requests gates; it cannot edit another role's output or authorize final access. The hypothesis researcher retrieves development evidence and prior failures, then proposes a falsifiable hypothesis with assumptions and stopping criteria. The experiment engineer translates an accepted hypothesis into a strict supported specification and requests deterministic development runs. It has no arbitrary shell, acquisition credentials or financial-policy override.

The data/implementation critic receives pinned source manifests, admission decisions, implementation identity and relevant deterministic probes. It can request bounded diagnostic calculations and return artifact-linked objections, but cannot rewrite the producer's specification. The statistical/portfolio critic receives the complete candidate/trial lineage, common-window results, costs, exposure and selection history. It evaluates multiplicity, comparison design and portfolio assumptions without calling development evidence a holdout. Neither critic certifies its own artifacts. Separate quality and no-drift review remain additional oversight assignments; five research roles do not replace those requirements.

A broker interprets only bounded strict JSON proposals from role outputs: retrieve an authorized development artifact, query failures, validate a specification, launch a registered supported study, inspect status, or submit an exact review. Each request must bind assignment, actor, lease/fence, request ID and allowed input references. Reject unknown fields and unauthorized references before returning data or performing effects. Prompt instructions support this boundary; the broker enforces it. The model never receives a database handle, arbitrary path reader, API key or broker order tool.

## Durable work, memory and review

Persist assignment ID, role-policy version, actual model/backend, worker incarnation, prompt/context hashes, permitted capabilities, byte/token/time/cost/step limits, upstream artifact hashes and dependencies before dispatch. Record all dispatches and outcomes, including invalid output, truncation, timeout, unavailable model and abandoned leases. A handoff is a validated artifact with deliverable hashes, unresolved objections, assumptions, requested next action and explicit terminal or pending state. Free-form summaries cannot silently become approval.

Use bounded stateless turns with reconstructed, cited context; retain earlier messages as evidence rather than unquestioned instructions. Journal the tool intent before execution, then bind its registered submission and outcome. Stale workers must be fenced at each effect and publication boundary, not merely final job completion. If a process dies after dispatch, mark the call uncertain and reconcile its artifacts; do not automatically redispatch a possibly billed call. Lease expiry alone does not authorize a new financial experiment or model retry.

Failure retrieval should begin with indexed structured fields plus bounded keyword search, not a new embedding dependency. Index failure code, affected market/source/specification/engine identity, exposure, root-cause disposition and superseding fix. Return original evidence links and distinguish unresolved failures from corrected defects. Record the retrieval query and returned IDs in each hypothesis packet. Require the director to explain a repeated attempt after a matching failure; this preserves memory without treating every old failure as a permanent veto.

Reviews must bind exact producer run and complete artifact set, actual responding model, reviewer assignment and separate session context. Require machine-checkable findings/dispositions and superseding-review links after changes. Separate contexts reduce conversational contamination; a common provider, briefing, training distribution and lead still create correlated errors. Record those limits and preserve dissent.

## Backend choice and final-access separation

Text API workers fit the existing bounded transport and atomic accounting. A validated JSON action loop can be built without native function-calling support. It adds recurring charges and requires an explicit research-purpose allowance under the shared USD20 daily cap; raw vendor data must remain local unless source rights explicitly permit transmission. Start with private deterministic tools and allowlisted evidence summaries; record what a model actually inspected and what it could not independently check.

Sanitized one-shot Claude Code processes are a viable alternate text backend, evidenced by completed D007 council turns. They require a tested adapter for model identity, terminal outcomes, deadlines, environment exclusion and cost uncertainty. They must not inherit project credentials or gain project filesystem tools. Root separately verified installed help and the official [headless](https://code.claude.com/docs/en/headless) and [CLI reference](https://code.claude.com/docs/en/cli-reference): JSON/schema support does not guarantee a populated structured result; validate all terminal fields. Do not use `--bare` for this OAuth route: it ignores that login and requires an API key. A CLI budget estimate may overshoot within a generation; reserve conservatively for bounded input/output rather than trust that cap. Retain uncertain holds and stop without headroom; never silently purchase capacity or switch models. API operational roles would not change the separate CLI council preference.

Native Codex handoffs remain useful for building and reviewing Quanto during an active chat. They are not the installed unattended operation. All backends must satisfy the same journal/capability contract, so unavailable native sessions cannot strand the research state.

Final data and result artifacts belong behind a distinct evaluator authority and storage boundary. No ideation worker or dashboard context builder may retrieve them. Freeze specification, candidate selection and release policy before the evaluator opens final data; atomically record exposure before returning any permitted result. Failures consume exposure when access occurred. Repeated requests must not create a score oracle; further access needs an explicit reviewed policy and exposure record. All current historical data remains development-exposed.

## Staged acceptance

First prove actor/capability enforcement, strict schemas, replayable handoffs and failure retrieval on synthetic fixtures, including deliberately defective input. Then demonstrate all five actual model roles completing one bounded workflow over admitted historical evidence, preserving genuine objections, corrections, exact separate review and complete attempt history. Report model limitations without requiring a fabricated finding.

Next exercise restart, stale-worker publication, dispatch uncertainty, budget exhaustion, damaged artifacts and backup restore while work is in flight. Finally verify protected-evaluator refusal paths, durable exposure and dashboard exclusion before any final access. Dashboard cards should derive active assignment, last heartbeat, latest handoff, objections and freshness from these records; contextual chat stays separately labeled.

This protects cooperating processes from accidental capability misuse. A filesystem owner or privileged process can copy final data, forge actor records or rewrite the ledger; trusted external checkpoints and backups improve detection, not immunity. Stronger hostile-owner isolation would require a separately controlled OS account or host. R14 closes only after the observed five-role workflow; scheduling, protected evaluation, paper operation and live readiness retain their own acceptance gates.

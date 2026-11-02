# Development workflow foundation

D008 introduces local state and retrieval libraries. They do not yet run models, enforce protected-data storage, broker research tools, schedule work or certify historical research. [The accepted staged contract](D008_POLICY.md) defines those remaining integration gates.

## Role state

`quanto.research_workflow.ResearchWorkflow` uses one existing `Provenance` connection per worker. A trusted supervisor calls `create_run(manifest)` with exact code/specification digests, explicitly admitted sanitized development inputs, and frozen per-role contracts. The seven ordered roles are director, hypothesis, engineer, data critic, statistical critic, quality and scope. The last two are separate oversight stages, not replacements for the research critics.

`issue_stage(run_id, role)` returns a random private capability once. Store it in the supervisor's private memory, never in a prompt, status card, worker name, artifact or log. Only its digest is persisted by this library. Losing a token requires explicit cancellation and a new run lineage; token recovery is not implemented.

`claim_stage` returns the issued identity and current fence. `authorize_intent` registers one allowed action and its exact input references. `start_intent` consumes the effect entitlement immediately before a trusted broker performs the action. `finish_intent` records verified result references; `finish_handoff` publishes the complete result set and exact reviewed inputs atomically with its terminal state. These APIs do not perform the effect themselves. A caller cannot turn a state receipt into evidence that a model or calculation ran.

Every effect entitlement and publication checks actor, lease, fence, cancellation and deadline in its transaction. A crash after an effect starts remains uncertain; there is no automatic retry or built-in reconciliation. `recover_expired` handles state, and `cancel_run` stops subsequent effects. The supervisor must distinguish state recovery from recovery of an external provider call. Role/model spend bounds in the manifest are declarations awaiting enforcement by the future broker and provider integration; they do not reserve money today.

The supervisor is the trust boundary for admission and output sanitization. JSON validity, exact hashes, fixed actions and credential screening do not establish data rights or detect every private value. The same filesystem owner can bypass these cooperative controls. `complete` from `read_status` means every local stage published a complete handoff; it does not mean the full private operation or investment validation is complete.

## Failure memory

`quanto.failure_memory.FailureMemory` reads existing provenance submissions and experiment attempts. A strict query can filter source, status, kind/code, exact IDs/request hashes, bounded metadata keywords, latest disposition and result limit. It returns fixed metadata and a durable receipt containing the query and returned IDs. It does not read or index free-form diagnostic text as searchable content.

Kind, code and artifact-reference allowlists govern projection. An integrating broker must separately authorize which failure IDs a role can see; hashes and identifiers may reveal private relationships. This is a private local retrieval service, not a transmission approval or authentication service. All retrieval/repair attempts that fit the bounded request envelope are retained, including semantic refusals. Memory's own submissions are excluded from subsequent searches.

Search is deliberately bounded: at most500 candidate rows per source,50 results,8 artifact references per result and32 total artifact verifications per query. `truncated` discloses scan/result limits; `artifact_state` separately discloses unavailable or unverified references. A no-match response is not proof that no older failure exists. Query an exact known ID to retrieve a record outside the recent candidate scan.

`append_disposition` records an append-only correction or reopening claim linked to the original failure. A correction requires a retained, allowlisted fix artifact; it does not prove the fix works. Original outcomes remain unchanged, and later artifact loss stays visible. Independent review must assess the correction's substance.

## Acceptance boundary

Synthetic tests exercise the actual SQLite/artifact libraries, seven-stage handoffs, failure retrieval, concurrency and recovery. The real five-model historical workflow still requires a provider adapter, deterministic typed tool broker, egress checks, current source admission, model-authored specification, actual registered study and separate criticism/quality/scope evidence. It must not be simulated by relabeling these fixtures. Protected evaluation, research scheduling and restore remain separate unfinished stages.

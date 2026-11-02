# D004 adviser archive recovered from the original task

## Recovery and verification

The archival worker located the five original D004 child conversations. The lead independently retrieved all five through `read_thread` on 2026-11-02 UTC, selected their actual assistant messages, and compared the quoted text. An initial recovery draft cited the earlier D001 adversarial message and omitted Markdown emphasis from the D004 quotation; both were corrected from the original message. An unrelated preliminary scope-note identifier was removed. Every quotation below now preserves the exact original D004 message text, with Markdown blockquote markers added only for display.

Original parent task: `01a199e8-3c66-79d0-9895-506448044c83`. Source child and message identifiers appear below. The history tool did not expose reliable model identifiers; none is inferred here. These are original design perspectives, not new adviser votes or implementation certification. Statements about pending reviews describe the time of those original messages. The separate actual Opus evidence and later implementation checks are preserved in DECISIONS and VERIFICATION.

## Original perspectives

### Research integrity — `/root/panel_integrity`

Source child thread: `01a199f1-1c31-7583-9efc-19bf8c94112d`  
Original assistant message: `msg_0af7608999ae2c0b016ae7f07893708198821e67fde4208fc5`

> D004 is acceptable if the dashboard clearly separates **recorded work, conversational assistance, and operational health**. An assistant’s explanation must never become evidence that an experiment passed or a worker completed its task.
>
> - **Identify assistants accurately.** Label each Q&A endpoint as a separate assistant using its configured model. Do not imply it is the original Codex worker or retains that worker’s hidden context. Distinguish recorded worker statements from the assistant’s interpretation.
> - **Attach answers to evidence.** Supply an allowlisted context bundle with artifact identities, observation timestamps, and source references. Display when that bundle was assembled and when its underlying records were observed; refreshing the page does not refresh the evidence. Require “unknown” when the records do not support an answer.
> - **Preserve review boundaries.** Conversations may explain findings or propose changes. They cannot approve research, clear objections, promote strategies, or certify independent review. Actual reviews require the existing attributed, artifact-specific workflow.
> - **Keep context bounded and private.** Exclude credentials, execution access, and unrestricted filesystem content. Treat retrieved documents and prior conversations as untrusted evidence, never as authority to expand access or bypass controls. Preserve the supplied context identity and model identity with each response.
> - **Make health deterministic.** Use process checks, heartbeat age, queue state, database accessibility, and failed-job counts to establish health. Haiku may summarize a detected fault; its response must not turn a failing check green. Deduplicate faults and bound model calls so repeated failures cannot consume the daily allowance.
> - **State availability precisely.** `launchd` restart supervision supports unattended operation while the Mac is awake and available. It does not establish continuous 24/7 availability through sleep, shutdown, network loss, or budget exhaustion. Show the last successful check and stale status.
> - **Enforce spending before calls.** Reserve conservative upper bounds through the shared ledger, cap responses, and require a new reservation for every retry. Budget exhaustion should disable model assistance while deterministic monitoring continues.
> - **Retain the proposed request protections.** Keep loopback binding, same-origin/CSRF checks, and a server-side role allowlist; client labels must not select arbitrary models or context.
>
> The outside Opus review remains pending until an actual response is received and recorded against the precise D001/D004 proposal. This perspective is a design assessment, not evidence that the dashboard or monitoring system has been implemented or validated.

### Systems reliability — `/root/panel_systems`

Source child thread: `01a199f1-3ee2-7aa3-96e4-a5a57a677e0d`  
Original assistant message: `msg_0d54ff2abf1b12e2016ae7f0614ff0819abcba0150b4cb33fe`

> D004 is sound if the dashboard separates three systems: observed builder work, conversational assistants, and deterministic service supervision. Approve the design with the following conditions.
>
> **Assistant identity and context.** Each smaller assistant should display “assistant for [role]” and identify the saved context it can inspect. It cannot truthfully claim to be the original Codex worker, observe that worker continuously, or send it instructions. Persist each conversation’s role, model, context revision/hash, source timestamps, request identifiers and usage. The larger desk assistant should use the same bounded context mechanism, with an explicit cross-project view.
>
> **HTTP and resource controls.** The current dashboard already binds to `127.0.0.1`, validates Host, checks supplied Origin, restricts assets and applies CSP. Preserve those controls. Paid POST requests should require an exact same-origin Origin and a random CSRF token, reject duplicate security headers, enforce JSON/body/history limits, and pass through bounded concurrency and rate limits. Render model output as text or sanitized Markdown; never as executable HTML.
>
> **Shared spending.** Route chat, outside criticism and health diagnosis through one provider gateway and reservation ledger. Reserve the complete bounded request before dispatch using America/Los_Angeles calendar days. A double click, browser retry or reconnect must not issue another paid request under the same request identity. Timeouts remain uncertain reservations; no automatic paid retries. A missing key, exhausted budget or unknown model pricing should leave the website usable with an explicit disabled-chat state.
>
> **Persistence and supervision.** Store conversations locally outside Git, with restrictive permissions and bounded context retention. Restarting the website must preserve completed messages and label interrupted requests accurately. A user LaunchAgent can restart a crashed server; a separate deterministic watchdog can detect an unresponsive server. Restart only the identified Quanto process after repeated bounded failures, with backoff and a restart ceiling.
>
> The “24/7” claim needs a concrete boundary: this local service operates while the Mac is awake and the relevant user session is available. Sleep, shutdown and logout interrupt availability. Record the last successful check and show stale observations after a gap.
>
> **Health diagnosis.** Keep routine checks deterministic and free: HTTP responsiveness, snapshot freshness, queue age, journal accessibility, disk conditions and recent failures. Trigger Haiku diagnosis only on a newly meaningful fault after deduplication, cooldown and budget authorization. Its response is advice. It must not execute commands, change files, restart processes or certify recovery. Service health and research freshness should have separate statuses; a responsive web server does not establish an active research operation.
>
> Essential acceptance checks:
>
> 1. Foreign Host/Origin, missing or wrong CSRF, oversized bodies and hostile model markup cannot trigger paid calls or script execution.
> 2. Concurrent chat, criticism and diagnosis requests cannot exceed the shared reservation allowance.
> 3. Repeating one client request identifier dispatches at most once; disconnects and provider timeouts preserve uncertainty.
> 4. Restart preserves transcripts, marks interrupted turns, and does not replay paid calls.
> 5. Assistant context excludes credentials, arbitrary paths and other roles’ unintended transcripts; replies identify stale evidence.
> 6. Missing credentials, exhausted allowance and provider failure degrade chat without breaking the board.
> 7. Server crash and simulated hang recover within declared bounds; repeated failure backs off instead of looping indefinitely.
> 8. Sleep/wake or stale snapshots produce truthful unavailable/stale labels rather than continuous-health claims.
>
> This was a read-only design assessment; no tests or paid calls were executed. Inspected working-tree artifacts above bootstrap revision `396b7db1a9a2e0418cd6b95b2b759e5abb8691c2`:
>
> - `dashboard.py`: SHA-256 `2b70920de0ec3fe13381b169cfcd89a4c431251a0956b090c34ab9cbd7d7fd82`
> - `critic.py`: SHA-256 `ff50f8f22d5968e61d5372fdb180cdd2f6203a09c21bf2b72737f1c83472b6c3`
>
> The decisive tradeoff is availability versus local-only operation: the proposed design provides supervised local service with honest interruption reporting. True availability during Mac sleep requires another always-on environment and a separate decision.

### Adversarial review — `/root/panel_adversarial`

Source child thread: `01a199f1-5a57-7461-aec3-67052209194c`  
Original assistant message: `msg_05abfc2e24cd6f05016ae7f04cd838819a9e333e0059d801b5`

> **Approve D004 conditionally: build the dashboard chats and supervised local service, but treat them as separate capabilities with separate evidence.** A responsive chat does not establish that operations are healthy, and a running background process does not establish continuous market coverage.
>
> The proposed separation is sound: role assistants identify themselves as new assistants, the desk helper receives bounded project context, and chat responses cannot execute tools or place orders. The principal remaining threats are these:
>
> - **Local chat endpoints become a paid-request proxy.** Loopback binding alone is insufficient. Require exact Host and Origin validation, a session-bound CSRF token, JSON-only requests, bounded body sizes, rate limits, and a concurrency limit. Validate these before reserving budget or calling a model. Avoid permissive CORS and query-string authentication.
> - **Retrieved project text changes the assistant’s authority.** Treat documents and conversation history as untrusted content. Context selection must use fixed allowlisted paths, resolve and reject symlink escapes, impose byte limits, and exclude credentials and runtime logs. Instructions inside retrieved files must not expand access or override the no-tools boundary.
> - **Conversation identifiers permit cross-session disclosure.** A durable conversation ID should identify a record, not authorize access. Associate records with the local authenticated session, validate ownership on reads and writes, and never let a client-provided role name select arbitrary context or provider configuration.
> - **Watchdog recovery creates a spending loop.** Automatic restarts and paid diagnosis need different controls. Restart recovery should be bounded and persistent across process restarts; diagnosis should require a new, meaningful failure signature, cooldown, attempt ceiling, and a dedicated sublimit within the shared $20 ceiling. Healthy checks should make no model calls. Repeated unchanged failures should remain visible without buying repeated explanations.
> - **Chat traffic consumes the operational budget.** Give chat and fault diagnosis explicit allocations or priorities beneath the shared cap. Otherwise an extended conversation can prevent an authorized external review. Show reserved, settled, and uncertain amounts separately; do not represent unused local allowance as verified account-wide allowance.
> - **Role labels overstate knowledge or independence.** Display the actual model, role instructions, context snapshot identity, and last observation time. A role assistant should not claim to be the original Codex worker or to remember work absent from its supplied context. An assistant’s conversational approval must not count as independent quality certification.
> - **“24/7” conceals host limitations.** Describe the service as supervised while the Mac is awake and available. Persist heartbeats and missed intervals so sleep, reboot, network loss, and process failure create visible gaps. A health report should distinguish process availability, fresh data, runnable jobs, and successful job completion.
>
> Before activation, require adversarial checks showing that:
>
> 1. Cross-origin and invalid-session requests cannot trigger paid calls.
> 2. Concurrent chat requests respect shared reservations and bounded concurrency.
> 3. Prompt injection in project text cannot expand context access or invoke actions.
> 4. Duplicate submission or restart cannot repeat an already authorized provider call.
> 5. Repeated identical failures trigger bounded diagnosis, then stop spending.
> 6. Sleep or process termination produces a visible stale interval after recovery.
> 7. Provider timeout preserves the reservation and does not produce an invented assistant reply.
> 8. A chat statement such as “approved for live trading” cannot change any operational authorization.
>
> LaunchAgent supervision is a reasonable local deployment mechanism if its configuration uses fixed paths and the owner’s ordinary account. Keep credentials out of command arguments, service definitions, and diagnostic output. The watchdog should detect defined failure conditions; it should not become an autonomous code-repair or shell-execution agent through this decision.
>
> The corrected critic findings and reported 115 passing tests are acknowledged, but I have not independently revalidated that revision. D004 also needs its own actual outside-model review when access is available; a review of the earlier foundation does not satisfy review of these new chat and supervision capabilities.

### Cost and operations — `/root/panel_costs`

Source child thread: `01a199f1-d992-71d3-aeb9-071b6e9652a6`  
Original assistant message: `msg_0b3961fda9f9b1ce016ae7f0582944819ba3ae15adbfd894a5`

> Keep the always-on service local and deterministic. Run routine health checks without model calls; use Haiku only for deduplicated, meaningful incidents, with a cooldown and strict call limit. Make Opus helper calls explicit, with bounded context and output plus a visible cost estimate.
>
> Before every call, reserve its worst-case cost against a local per-day allowance. Include Haiku’s higher long-context rate, disable automatic retries, and stop calls if pricing or usage accounting is unavailable. Show spend, remaining budget, per-role usage, and a pause switch. The local ledger controls only this app’s calls; account-level limits or billing alerts are needed if other clients share the API account. Preserve headroom under the $20 cap for estimation error and other account use.

### Scope fidelity — `/root/panel_fidelity`

Source child thread: `01a199f2-2ec7-7ff2-b951-507cdad570f1`  
Original assistant message: `msg_084e093d0db0cfcc016ae7f093002c819b89b8ee9420620683`

> D004 aligns with the user’s request as a staged implementation, provided the new assistants do not replace the requested worker interaction by implication.
>
> - **R20: distinguish contextual conversation from worker communication.** Each Haiku chat should identify itself as a new assistant for a named role, use that role’s saved tasks/results, and cite the source and observation time. Direct routing to a running worker remains a separate, incomplete capability unless implemented. Preserve it explicitly in the roadmap rather than treating honest labeling as equivalent functionality.
> - **R20: bound the larger helper’s claims.** The Opus helper can explain the allowlisted context it receives. It should disclose omitted or stale evidence and distinguish saved facts from its interpretation. A desk-helper conversation does not itself satisfy independent adversarial review.
> - **R21: define continuous operation operationally.** Supervision, health checks, restart history, and incident records can establish persistent local service. Model diagnosis can run on meaningful incidents. Describe availability as dependent on an awake Mac and the required login session; do not claim guaranteed 24/7 availability or continuous model reasoning.
> - **R08: preserve one spending boundary.** Role chats, the larger helper, incident diagnosis, and outside criticism must use the same reservation/dispatch controls. Set bounded incident frequency and response sizes. Budget exhaustion should stop paid calls while deterministic health checks continue.
> - **R16: preserve the creative interface requirement.** Record agent icons, a distinct research-lab visual direction, and planned/active/completed work as acceptance criteria. Those states must come from actual assignments and evidence; visual activity must not imply running workers or completed tasks.
> - **Authority remains separate.** Conversational advice cannot become a tool action, order, strategy promotion, approval, or independent certification merely because the assistant emits that text.
>
> The decisive boundary is whether each interface accurately exposes a real capability. Saved-context chats and supervised health are useful deliverables, but full worker interaction, autonomous research, and execution readiness remain separately traceable requirements.
>
> One documentation correction remains: D001 still says outside review is pending credentials, while STATUS/HANDOFF say credentials are configured. It should say the actual review and dispositions are pending.

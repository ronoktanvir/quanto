# D011 one-step supervisor criticism

Reviewed 2026-11-04 by the independent native implementation critic. **No blocking objection remains for the reviewed one-step supervisor under the cooperating-process threat model.** This acceptance concerns launch containment and evidence recording. It does not approve a particular private request, market-data admission, financial result, unattended service or order.

Final source: `operations/strategy_campaign/supervise_step.py`, SHA-256 `7cd80f7775f6667fa0f56307cbb720070eee772951a3aed232c9c5f58779e06d`.

Executable verification was performed at `41e5b643890bbf2a8d5f1bd837e05001fc722aaef0ebaa94b1af27f3063a9bc1`. The final revision changes only the module docstring to state the actual cleanup and I/O limits. The critic independently reconstructed the prior bytes by replacing that docstring and recovered the exact tested hash (terminal `5b2de3`); the executable checks therefore still apply without a broad rerun.

Final producer tests: `tests/test_strategy_campaign_supervisor.py`, SHA-256 `c04949a960d850f5f6640709849a8fece6b5bed9f72912c9e99f138a3fc7e52a`.

The critic inspected public source, existing authority behavior, producer tests and the quality agent's explicitly invented scratch fixtures. All executed probes used newly created temporary source trees and invented authority files. No actual project store, credentials, provider, model, request or operation was used.

## Required corrections, preserved

**Reviewed Python source could differ from executed cached bytecode.** On source `3c4006e11208259543bdd991a8331fd7fc09146b8e3367457a7c9764cc4a9cd7`, the critic compiled an invented CLI returning 41, replaced its source with a same-size CLI returning 42, restored the timestamp and froze the new source identity. The supervisor executed 41 while reporting unchanged identities. Python's `-B` disables cache writes, not cache reads. This was a concrete mismatch between the reviewed bytes and the launched behavior, without any concurrent owner mutation during the run.

The producer added an exclusively created, empty private cache prefix for each attempt and retained `-B`. Repeating the original probe on final source executed 42 and retained unchanged identities. This correction applies to product modules imported by the isolated child; the supervisor itself runs as the explicit script.

**An interrupted spawn could dispatch without a retained process handle.** The critic injected a `Popen` wrapper that started the real isolated child and then raised `InterruptedError`, representing interruption after OS creation but before the caller receives the handle. At the same `3c4006e...` revision, the receipt honestly reported uncertainty and unconfirmed cleanup, but the child still reached the invented CLI and remained running outside the supervisor's control. The probe used its separately retained handle to kill and reap that invented child.

The producer added an inherited pipe that grants one byte only after the parent receives the process handle and checks the deadline. The child waits for this grant before importing product code or acquiring authority. Spawn exceptions close the parent's writer; EOF or a five-second gate timeout refuses dispatch. Repeating the original probe on final source produced no CLI marker and the child exited. The supervisor still reports uncertainty and unconfirmed cleanup when it never obtained the handle; it does not infer an observed reap from the gate design.

Both original failures were reproduced with stable before/after source hashes in terminal `f5d565`. An initial probe harness omitted the newly imported `AccessError` type and stopped before the intended behavior; that harness result was not treated as evidence of either defect. Intermediate closure used `aa61292734cd9e9da89b91885c8d04ea73484eb4582df1cdb8258691f5b8653a`; final executable closure used `41e5b643890bbf2a8d5f1bd837e05001fc722aaef0ebaa94b1af27f3063a9bc1`.

## Final verification and accepted boundaries

- The critic independently executed all **16 producer tests**, passing in 2.37 seconds, terminal `ad782a`. They include the actual CLI's malformed-request recording in a newly created store, missing/mismatched authority, fixed command and identity refusals, output limits, deadlines, replay refusal, environment isolation and uncertain cleanup.
- The critic repeated its stale-cache and interrupted-spawn probes on the final executable revision, then independently advanced the wall clock after a real child was created but before its start grant. The expired launch received no grant, did not execute the invented CLI, returned an uncertain deadline receipt and reaped the owned child. All three probes passed with identical before/after tested source hashes, terminal `efc0c9`.
- Source review confirms an explicit eight-command research/acquisition allowlist, exact request/Python/public-source identities, an exclusive attempt directory, a private copied request, and a separate exclusive child-start record. Existing control and research files must exist; the ordinary `Supervisor` verifies the stored root identity and configuration before CLI dispatch. Missing authority is not silently bootstrapped by this path.
- The child receives an explicit environment with no inherited credentials, isolated Python options and fixed CLI arguments. The parent does not read `.env`. Source/request/authority identities are checked again after execution; changed identities withhold acceptance. The inspected commands do not add an order route.
- Output pipes are drained with independent 256-KiB stdout and 64-KiB stderr caps into private files. Process-group termination and child reap are attempted on timeout, output excess and interruption. The deadline uses the earlier wall and monotonic bounds, with checks at most 0.25 seconds apart while polling. Each reap wait is bounded at five seconds; exceptional cleanup can make two such waits. Local preflight and persistence I/O are not preempted by the execution timer. A nonzero child exit remains visible; `completed` describes observed process completion, not success of the requested research operation.
- The quality agent separately discovered intermittent process-group `EPERM` escaping cleanup and being mislabeled as preflight refusal. The critic inspected its correction and reran the producer regression: group-observation/kill failures retain post-launch uncertainty and do not claim confirmed cleanup. The independent quality report owns the original repeated-process evidence.

## Remaining limitations

The wrapper does not defeat a privileged owner, concurrent hostile path replacement, escaped hostile descendants, kernel failures or an uncatchable kill of the supervising parent. Such cases are outside this cooperating-code acceptance; an interrupted attempt stays consumed and must be inspected rather than replayed. A failed group observation, unknown spawn handle or failed private-output persistence remains uncertain. A content hash is not a backup, and this wrapper does not create or reset authority.

Local preflight precedes the execution deadline; the deadline starts immediately before spawning. The process cannot run while the host is suspended, and the wall bound prevents treating suspended time as extra work allowance on resume. These are bounded supervision checks, not hard real-time operating-system guarantees.

The ordinary launch must still use the independently reviewed exact build and a concrete frozen request. Receipt and private output inspection must distinguish a process exit from acquisition, admission or campaign success. This report introduces no retries, wider commands, model budget changes, data uploads or trading authority.

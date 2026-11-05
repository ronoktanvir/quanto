# D012 council runner preparation

The D012 signed-in Claude council runner is prepared and has not been invoked. Its producer checks passed on invented child programs, packets, terminal records and scratch journals. Independent invocation preflight remains a separate acceptance step. No model/auth command, production journal inspection, budget write or credential-file read occurred during this preparation.

Producer: `/root/reattach_council_prepare`, November 4, 2026. The private runner and tests remain under the original root's ignored `runtime/council-cli/d012` directory. The consumed D011 runner was read as source only and remains byte-identical; it must never be rerun.

| Artifact | SHA-256 |
| --- | --- |
| Unchanged D011 source | `37930bf516fb01a5730e50618d4828348e6f13c4739b4bf5e16ef40ea4135c6a` |
| Prepared D012 `runner.py`, 24,928 bytes | `cca8f2ac37cd1c11cfb5261d1b6ed6955999df38cf4ce81e9580ce562b96d9f3` |
| Private `test_runner_invented.py` | `9253c4bf670d102b0c1a577120d20f1256c45cef7d57d1f6912bce05cfe464a4` |
| Private `runner-adaptation.diff` | `d7dc6e2a7d4be42ba9c85e600205f40928b3c8f7a3a18d913f27a21b1dfd9f10` |
| Selected D012 packet, 11,506 bytes | `b9d2ba4ef62b2b4c6e07ed497f261b2c4d1405bbe7e9393c02a3a43d829d9570` |

The lead selected the complete proposed [D012 design](../D012_DESIGN.md), SHA-256 `1f5254505b6bc8a8c84d3a2e492e61b87e9d96ce76eda3b3e2365b58b7d96933`, plus explicitly attributed summaries of five independently briefed perspectives. The runner pins the packet's exact path and digest. This producer verified the supplied packet's byte count/digest and private file mode, not the factual accuracy of every summary. The models will receive proposed policy, not a claim that reattachment has occurred or that private continuity evidence was independently established.

## Exact changes and retained controls

The adaptation changes the D011 campaign names, packet pin and system-purpose phrase to D012. It adds `sys`, replaces the process transport, rechecks eligibility immediately before the start grant, and requires confirmed cleanup for terminal acceptance. Reversing exactly those changes reconstructs the entire original D011 file at the digest above. Ledger construction, atomic pair reservation, one-use dispatch, model commands, usage reconciliation, receipt persistence and uncertain-hold logic are otherwise unchanged.

The existing budget journal is separate from the blocked research-access authority. `ExistingJournal` opens an existing journal with SQLite `mode=rw`, checks its existing records and guards, and never calls a bootstrap constructor. The future council reserves USD 1.40 for `claude-fable-5-1` and USD 0.60 for `claude-opus-5-5` atomically before OAuth verification. Every dispatched, ambiguous or unsent reservation remains held. An unavailable model, auth refusal, lost terminal or partially completed pair cannot trigger a retry, fallback, release or new account purchase.

The CLI receives a constructed environment, including the operating-system account's HOME for its existing sign-in, fixed PATH and bounded settings; it inherits no project API key or arbitrary environment. Commands retain first-party OAuth verification, exact permitted models, one turn, zero retries, disabled tools/MCP/browser integration/customization/session persistence, and the existing time and output limits. The managed-policy/trusted-CLI assumptions from the [D011 preflight](D011-council-preflight.md) remain qualifications, not newly inspected facts.

The 443-byte system prompt, selected packet and unchanged 10,000-token framing allowance yield a 21,949-input-token estimate, with at most 8,192 output tokens. At the previously reviewed worst input/cache-write and output rates, the envelopes are USD 0.848580 for Fable and USD 0.339432 for Opus. Both fit their full holds. These are conservative local estimates, not provider invoices; CLI thresholds may overshoot, framing remains an assumption, and this ledger cannot control unrelated account clients. The existing price-review expiry remains active.

## Interrupted-launch containment

Each auth/model subprocess first runs an isolated inline Python gate through the resolved current interpreter. Only the read end of a new pipe is inherited. The gate executes no project imports or CLI command until it receives one byte; EOF or a five-second wait expiry exits without CLI execution. It closes the inherited descriptor before executing the requested command.

The parent writes that byte only after `Popen` returns a retained process handle, eligibility is rechecked, and both wall and monotonic deadlines remain valid. A generic interruption after OS process creation but before handle assignment closes the parent's writer without a grant. The receipt nevertheless reports an attempted launch with unknown cleanup because the parent did not observe a reap. The gate prevents dispatch under that failure; it does not fabricate process-observation evidence.

Wall and monotonic bounds prevent backward clock changes from extending the allowance and catch forward jumps or host suspension on resumption. Pipe and exit polling rechecks the bounds at intervals of at most 0.25 seconds. Stdout remains capped at 512 KiB and stderr at 64 KiB. Timeouts, output excess and terminal interruptions attempt process-group termination and an observed reap; the one reap wait is bounded at five seconds. Group-observation or cleanup errors withhold acceptance. Terminal signals are ignored only during cleanup and then restored.

The lead must launch the outer runner with the selected source and an exclusively created empty cache prefix; `-B` alone does not prevent reading old Python bytecode. The inline gate imports no product modules. This preparation does not certify that a future outer launch used the reviewed imports or effective CLI configuration.

## Executed producer evidence and limits

The final run passed **27 tests**, including six negative terminal subcases, in 5.930 seconds. Tests ran with an isolated Python environment, `-B` and an exclusively created temporary cache prefix, which remained free of generated bytecode. These are `synthetic_fixture` software checks, not real provider or authority observations.

The executed cases cover successful bounded I/O, nonzero/missing-command outcomes, both output caps, silent and closed-pipe timeouts, refusal before spawn and before grant, interrupted spawn without a retained handle, gate expiry while the writer remains open, a forward wall-clock jump, SIGTERM cleanup/restoration, uncertain group observation, environment isolation, exact model/command limits, packet digest/mode/symlink refusal, missing/unguarded scratch-journal refusal, atomic pair rollback, repeat-pair refusal, retained unsent holds, consumed failed dispatch, exact terminal acceptance and contradictory model/turn/tool/fallback/subagent/token metadata. An invented auth-status result verified that raw identity fields are not persisted. No test launched the real CLI.

The first producer run exposed a transport correction: raising `InterruptedError` from the signal handler let the selector treat the signal as ordinary interrupted I/O and continue until timeout. A distinct internal exception now reaches cleanup immediately; the SIGTERM regression passed. Two initial journal tests also used macOS's aliased temporary path and correctly encountered path refusal. Resolving the invented scratch root repaired those fixtures without weakening the production path check. The initial failures are preserved here rather than represented as passing evidence.

This wrapper supervises cooperating reviewed processes. Local file/journal/persistence I/O is not preempted by its execution timer. Host scheduling, uncatchable parent termination after a grant, hostile escaped descendants, privileged path replacement and kernel failures remain outside this bounded acceptance. Unknown cleanup or missing persistence stays uncertain and consumed. Preparation does not establish current budget headroom, actual OAuth availability, a real model response, accepted D012 policy, restored research access or a strategy result.

# D008 paid worker v2 preparation

The new worker requires a positive parent grant and continuously rechecks ownership, the original two-clock cutoff and the prospective planning day at paid boundaries. Its consumption marker now determines which invocation may publish outcomes. This corrects the worker findings in the [joint criticism](D008-manual-cycle-launch-critic.md); actual use remains withheld pending separate combined review.

Producer `/root/paid_worker` changed only the two new worker files under ignored `runtime/development-cycle-launch-v2-preparation/` and this report. The original worker, tests, frozen copies and prior reports remain unchanged. The [independent quality report](D008-manual-cycle-launch-quality.md) was read: its real-validator refusal probes establish narrower software behavior and do not resolve the ownership, cutoff or competing-marker findings. No actual state, private input, credential, market data, provider request, registration or financial replay was used in this increment.

## Positive ownership and publication

The only supported command line is `--gate-fd FD`. Bootstrap verifies the adjacent supervisor source against the consumed supervisor hash, compiles those bytes and calls its `await_grant('paid', fd)` before obtaining `worker_context()`. The separately owned supervisor closes the descriptor and validates the pipe grant and durable ownership chain. EOF, expired grant or wrong ownership returns through an unset publication destination: no outcome or terminal is written.

Before consumption, the worker independently captures and validates `consumed.json`, `paid-launch.json`, `owned.json` and `start.json`. The current PID and live expected PPID must match the ownership/start/launch/consumption records, phase must be paid, plan and digest joins must agree, the original window must remain open and no parent failure may exist. These exact bytes stay pinned through the paid boundaries. The call-entry receipt adds `owned_sha256` and `start_sha256` to the existing consumed, launch, request, registration-result, prelaunch and budget digest bindings.

Only a successfully returned, durable exclusive `paid-consumed.json` publication installs the worker's publication authority. A duplicate loser or interrupted/partial publisher cannot create an outcome or terminal for another invocation. A winning worker checks its marker digest before normal outcome publication, final terminal publication and uncertain failure publication. Pending, invalid and malformed normal broker returns remain preserved exactly; neither successful return nor uncertain failure grants investment or operational acceptance.

## Live cutoff and prospective day

A worker-owned profile checks the unchanged `ResearchDispatcher._authorize`, `provider._send_research` and credential lookup entry boundaries before their function bodies. The worker also checks immediately before its initial credential lookup and before the single ordinary broker invocation. Every check requires the pinned receipt chain, unchanged live PID/PPID and absence of parent failure.

The remaining allowance is the shortest of the original monotonic window, original wall window and already clipped context deadline. The first two retain the parent's five-second reserve. The child alarm is shortened to that remaining allowance at these boundaries; it cannot renew the original interval or extend the clipped context deadline after a backward wall adjustment. It remains active during provider work, including when the parent disappears. An already in-flight request can still leave uncertain paid effects. The unchanged provider lease and HTTP limits remain additional controls.

Once the transaction-bound budget observation exists, its Los Angeles day becomes fixed. Every subsequent sensitive boundary checks that same day and refuses rollover; it does not acquire a fresh planning observation to continue the consumed cycle. Existing atomic per-dispatch authorization and reservation code is unchanged. The budget/event/allocation checkpoint, exact six-field prelaunch record, real existing access session, complete source/loaded identities and normal broker call without injected transport are retained.

## Producer verification

All **83 invented cases passed in 0.55 seconds**, and Ruff passed both new worker files. The existing reviewed-interpreter minimal-environment and hermetic public-source probes remain included. New cases reproduce the critic's missing/wrong ownership, parent failure, stale parent, wall cutoff, prospective-day change, competing consumption and partial marker publication conditions.

Four faults applied immediately after the call-entry receipt each prevent broker entry. Twelve additional probes apply changed parent, wall, day or failure state after entry but before function bodies bearing the actual authorization, send and credential-lookup names; each body remains unexecuted. Actual anonymous-pipe probes exercise the real adjacent supervisor's grant success, EOF, wrong ownership and expired-wall paths. An invented-root bootstrap probe verifies the adjacent source before actual pipe EOF and confirms no new worker receipt. This test disables only its in-process environment preflight because the independent Python 3.11 environment subprocess already exercises that preflight; there is no corresponding CLI switch.

The test suite still runs on the existing Python 3.13 development environment. Its public hermetic import and minimal-environment subprocesses use the reviewed Python 3.11 interpreter with isolated flags and empty supplied environment. No new producer regression failed during this v2 increment. Earlier failures and independent v1 witnesses remain preserved. Function-name probes test guard placement with invented bodies, not actual network sends or provider responses; the separate real-validator quality probes and renewed combined independent reviews remain distinct evidence.

| Artifact | SHA-256 |
| --- | --- |
| New `paid_worker.py` | `9a59cb3eb37f8b6f06d17abde2a474da13fba07264bd37c634ee12a07f0cd01c` |
| New `test_paid_worker.py` | `7694ff9ada310d5c27c84cca5907464099475c5cbbc1c09b4b6180a723669c1a` |
| Adjacent supervisor inspected for real-pipe/context probes | `7869c3c8df3c2e8bbcf3127cb8ef021173605d98c56fde4adf7b951f82fe1040` |
| Preserved original worker | `7aa4e43c5a4453fad118d29f379fd5b1ba08d2b0cd5af0a955e2baa2c106c883` |
| Preserved original worker tests | `27c62e3b323c2d2dd585033eea0263c6098793ff92006174383eed9309619247` |

These are cooperating-process controls on the trusted owner's host, not isolation from hostile same-user modification. Root owns the grant implementation, registration guardian, process cleanup, staged private inputs and final combined review. No actual-use clearance follows from producer tests alone.

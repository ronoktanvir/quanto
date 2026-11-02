# Local website operations

Quanto can supervise its private loopback website while the owner's Mac is awake and signed in. The supervisor runs deterministic health checks and restarts only a child process it actually created. It does not run research, place orders, change research observations, or establish continuous native Codex agent telemetry.

Sleep, logout, shutdown, and supervisor outages interrupt observations. A gap longer than 30 seconds, or a backwards clock change, is recorded in `runtime/operations.json`. A later successful check does not erase that gap. This is an awake-host service, not a claim of uninterrupted 24/7 hosting.

## Commands and ownership

From the project directory, inspect the proposed user LaunchAgent without changing the system:

```sh
.venv/bin/python scripts/install_local_service.py
```

Install and start the explicitly owned service:

```sh
.venv/bin/python scripts/install_local_service.py --install
```

The script writes `~/Library/LaunchAgents/com.ronoktanvir.quanto.plist`, with absolute Python and project paths. It uses the user's `gui/<uid>` launchd domain, requires no administrator access, and configures a 30-second launchd throttle. It preserves the virtual-environment Python path rather than resolving its interpreter symlink. The plist contains no credentials; the only configured environment variable is the source `PYTHONPATH`. Runtime output files are private local files and must stay untracked.

Remove this project's user service and stop its owned process group:

```sh
.venv/bin/python scripts/install_local_service.py --uninstall
```

The installer verifies the exact label, project root, and supervisor module before replacing or removing an existing plist. An existing service attached to another project root is refused. It does not use process-name matching or terminate arbitrary port owners. To use a different interpreter or port, inspect a plan with `--python /absolute/path/to/python --port 8766`, then repeat those arguments with `--install`.

A manual supervisor runs the same fixed dashboard command:

```sh
PYTHONPATH=src .venv/bin/python -m quanto.operations --root "$PWD" --port 8766
```

The dashboard remains at `http://127.0.0.1:8766`. `--once` performs one observation, persists it, and exits without launching a server or calling a model. Concurrent supervisors for the same runtime are refused by an advisory file lock.

## Deterministic health and restart circuit

The supervisor requests the loopback `/health` endpoint with a two-second timeout, a bounded 4096-byte body, and redirects/proxies disabled. A healthy response must identify both `service: quanto` and `status: ok`. Check cycles are approximately ten seconds apart; slow network checks add their bounded duration.

A separate `/ready` probe checks that the recorded work snapshot and required website assets are available. Failed readiness is displayed as degraded and can receive bounded incident diagnosis, but it never causes a healthy process to restart: a restart cannot repair missing evidence. An old research observation remains visibly stale, not a failed process.

A new child gets a ten-second startup grace period. Three consecutive unsuccessful checks trigger replacement of that owned child. Every launch, including the initial launch, consumes a persisted launch slot. At most five launches may occur in a rolling hour, with backoff starting at 30 seconds and doubling up to 300 seconds. The slot is written atomically before spawning. Restarting the supervisor or launchd job therefore does not reset the circuit. The supervisor remains alive and continues checking while its circuit is open.

If the port already serves healthy Quanto, the supervisor records `healthy_external` and observes it without assuming process ownership. An unknown occupied port is recorded as `blocked_unknown_port_owner`; no process is killed. Persisted PIDs never authorize termination. Shutdown sends SIGTERM only through an actual child handle, waits five seconds, and uses SIGKILL on that same child only if necessary. Child output is discarded rather than copied into diagnostics; broker and API credential environment variables are excluded from the child environment. The server's explicitly configured local credential file remains its provider gateway's responsibility.

The atomic operations snapshot contains the last check, last success, health state, reason, recent checks, restart history, observation gaps, diagnosis status, and the awake-host limitation. These fields describe website observations. They never refresh `runtime/status.json` or any research/worker `observed_at` field. Corrupt or unsupported persisted state is an operator-repair condition, not permission to reset limits.

## Five-minute website snapshots

The running supervisor captures the current validated work record and a small allowlist of service observations every 300 seconds. The first attempt starts immediately when no capture schedule exists. A browser does not need to be open. The one-shot `--once` check does not start this schedule, and no capture calls a model, broker, or network service. These snapshots are saved status records, not screenshots or new observations of native workers.

`runtime/website-snapshots.json` atomically stores the most recent successful capture, the last attempt and result, the next scheduled attempt, and at most 60 attempt summaries. Its maximum size is 2 MiB plus 128 KiB; the source work record remains limited to 2 MiB. Source `observed_at` and individual agent timestamps remain exactly as recorded. Taking a new snapshot of unchanged work does not make that work fresh.

Every attempt reserves its next deadline before reading the source. A failure keeps the previous successful capture and waits until the next five-minute deadline. An interrupted claim becomes a failed `capture_interrupted` attempt when the recorder resumes; it is not replayed, and the next new attempt keeps the reserved deadline. After sleep or a long outage, the recorder makes one attempt and sets the following deadline 300 seconds later, without a catch-up burst. A process lock prevents competing recorders from duplicating an attempt. Corrupt metadata, unsafe paths, or inconsistent history fail visibly instead of resetting the schedule. Snapshot failures do not trigger website restarts.

The read-only `/api/snapshot-status` endpoint reports last attempt, last success, next attempt, source observation time, result, safe failure category, and the server's current time. It creates neither captures nor sessions. The website displays these fields separately from work freshness. A stopped, missing, or stale supervisor clears the active next-attempt deadline; the previously scheduled deadline remains available as `scheduled_attempt_at`. A failed capture with a healthy supervisor retains its real retry deadline. If the machine sleeps, the displayed countdown cannot establish that an attempt happened; a subsequent server response is required.

Only the latest successful capture is retained, not a complete archive. The bounded history describes capture attempts, not research results. The capture file and its lock remain ignored local runtime outputs. `tests/test_snapshots.py` covers synthetic timing, restart, interruption, retention, malformed input, unsafe paths, and competing processes; it does not establish uninterrupted hosting.

## Bounded advisory model diagnosis

Healthy routine checks make zero model calls. After three failed checks, a new deterministic fault signature may request a small Haiku diagnosis through the server-side provider gateway. The signature combines the fixed fault category, dashboard component, and normalized message hash. Repeated signatures are not dispatched again; model downtime is reported as unavailable or failed, never as successful diagnosis.

The supervisor permits at most one attempt per hour and four attempts per America/Los_Angeles calendar day. It conservatively reserves USD 0.125 per attempt, retaining that local reservation even if the request is unavailable or uncertain, so its dedicated daily allowance cannot exceed USD 0.50. Each call also uses the project's shared atomic USD 20 daily provider ledger and a persisted unique request ID. This ledger governs this project's calls, not unrelated clients using the same provider account.

Only fixed health categories, failure/restart counts, and the awake-host limitation enter the incident packet. Credentials, server logs, conversations, and arbitrary local files do not. Calls run in a daemon background thread so model latency does not suspend health checks. A pending call interrupted by shutdown remains conservatively reserved and is not automatically replayed.

The model's bounded response is advisory text. It cannot run commands, modify files, change health, reset circuits, place orders, or certify uptime. If the gateway is absent or its pause/budget controls reject dispatch, deterministic website supervision continues. External model review of the implementation and an actual model diagnosis are distinct evidence from the synthetic tests.

## Verification and remaining limits

`tests/test_operations.py` uses synthetic clocks, processes, HTTP responses, and provider callbacks. It covers restart persistence/backoff, missing-observation gaps, unknown process ownership, one-shot behavior, diagnosis deduplication/caps, fixed child arguments, credential exclusion, and LaunchAgent identity. These tests validate software behavior; they do not establish observed unattended uptime or investment performance.

After installation, the integrator should verify the actual website, terminate the known owned dashboard child once, observe recovery and its persisted launch count, and inspect a fresh operations snapshot. Sleep/wake, logout/login, machine reboot, backup recovery, and sustained unattended operation still require their own observed evidence. This supervisor covers website health only; durable research scheduling and separately approved trading execution remain future work.

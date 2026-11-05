# D011 external supervisor: independent executed quality

**Result: passed for the exact supervisor revision below, after the cleanup, cache-isolation, and launch-gate defects were corrected.** The final independent run passed 35 checks. This review covers only the one-step external supervisor, not a production invocation or an actual research result. The reviewer is `/root/queue_quality`, separate from the implementation author, and owns only this report and ignored scratch probes.

Review completed at 2026-11-05 06:04 UTC (November 4, America/Los_Angeles), in `/Users/ronoktanvir/.codex/worktrees/strategy-research/quanto`. The initial checkout base was `8a4e0a2`; the final observed Git head was `f18a036f55a5f5ff41fa4ed4db35453bb3c40802`, with the supervisor increment still uncommitted. Exact hashes were checked before and after the final test run:

| Artifact | SHA-256 |
| --- | --- |
| `operations/strategy_campaign/supervise_step.py` | `41e5b643890bbf2a8d5f1bd837e05001fc722aaef0ebaa94b1af27f3063a9bc1` |
| `tests/test_strategy_campaign_supervisor.py` | `c04949a960d850f5f6640709849a8fece6b5bed9f72912c9e99f138a3fc7e52a` |
| Reviewer scratch `runtime/d011-supervisor-quality/test_supervisor_quality.py` | `237a795ad71b31f9088f54829668b155195caa834ad2aa2d745600aca43d6a54` |

The independent scratch probes remain ignored local evidence, not part of a fresh checkout. Producer tests are retained in Git. The reviewed campaign implementation itself was not changed by this task.

## Evidence and defect

The reviewer created an invented source package, a fake CLI and authority class, and empty private-mode physical-identity files under ignored `runtime/d011-supervisor-quality/`. The files named `control.sqlite` and `research.sqlite` deliberately contain invented text, not a functioning control database. They test the wrapper's existence/identity preflight; they do not test the real authority's database semantics. No production runtime, credential, real provider, model, or actual campaign was invoked.

The provisional supervisor source had SHA-256 `a9aa05c787af20dd9d67b653a9e65e81d69ccf73c8cb46d22ec488a995d23f13`. Its initial 15-case independent run produced 13 passes and two failures. One failure was an overstrict test expectation: macOS adds `__CF_USER_TEXT_ENCODING` metadata after subprocess creation. The invented secret environment variable was absent, and the test was corrected to permit operating-system locale metadata. The other failure was a real implementation defect.

An invented CLI spawned a sleeping descendant in its own process group with redirected output, printed that descendant's PID, and exited normally. In four of twelve isolated repetitions, a process-group probe or kill raised `PermissionError(EPERM)`. That exception escaped `_capture` cleanup. The outer supervisor then wrote `status=refused`, `reason=preflight_unavailable`, and `exit_code=null` despite having launched a child and captured its output. The result lost the observed post-launch state and cleanup uncertainty. A deterministic probe that forces group operations to raise `PermissionError` reproduced the same misclassification. All introduced descendant PIDs were subsequently checked absent.

The producer corrected cleanup error handling and retained launched-process metadata and uncertainty. All 17 independent probes then passed in 0.87 seconds, exit 0, with source observed at SHA-256 `3c4006e11208259543bdd991a8331fd7fc09146b8e3367457a7c9764cc4a9cd7`. In particular, the deterministic permission failure returned uncertain status, observed exit code zero, and `cleanup_confirmed=false` instead of a preflight refusal.

The separate critic subsequently reproduced two other defects on that source: an old valid timestamp/size Python cache could execute instead of the newly frozen source, and a subprocess creation that succeeded before raising could leave a child able to dispatch without its parent's ownership. The producer added an empty private cache prefix and a parent-granted pipe gate. Independent regression probes passed for both cases on the final revision. A cache containing `OLD` no longer replaced frozen source printing `NEW`. When the reviewer's spawn wrapper created a real child and then raised, that child exited without running the invented CLI; the supervisor retained uncertainty rather than claiming cleanup. The reviewer retained the deliberately hidden test handle solely to observe its exit.

## Final execution and scope

The final independent scratch suite contains 19 checks. It exercises a real wall-clock timeout of a TERM-ignoring child, exact and one-byte-excess stdout/stderr bounds, direct-child reap observation, nonzero exit retention, sequential parent/child replay refusal, competing parent claims, source/request changes before and during execution, missing existing authority files without creation, environment isolation, descendants, cleanup permission failures, stale caches, and ambiguous spawn ownership.

Commands run from the resident checkout use the existing local Python environment:

```sh
/Users/ronoktanvir/Documents/ChatGPT/quanto/.venv/bin/python -m pytest -q tests/test_strategy_campaign_supervisor.py runtime/d011-supervisor-quality/test_supervisor_quality.py --basetemp=runtime/d011-supervisor-quality/final-scratch
```

**Observed terminal result: 35 passed in 4.19 seconds, exit 0.** This combines 16 producer checks independently executed by this reviewer with the 19 independent checks. The producer coverage also exercises the real control registry and real CLI on synthetic authority, invalid request retention, existing configuration mismatch, and forward wall-clock expiry before gate release. The independent fake-authority tests deliberately do not duplicate those database semantics.

The observed process bounds were concrete: a 0.3-second limit killed and reaped a TERM-ignoring invented worker; stdout retained exactly 256 KiB and stderr exactly 64 KiB, while one extra byte forced an uncertain output-limit outcome without exceeding either stored cap. Two real supervisor parents targeted one attempt directory and only one completed a child launch. Existing parent and child attempts could not replay. Changed source/request bytes withheld acceptance, and missing existing authority files were not created. Normal nonzero exit 23 remained visible. The deterministic process-group permission failure retained uncertainty and observed exit zero with `cleanup_confirmed=false`.

The review uses the normal cooperating-process threat model. It does not certify protection against a privileged owner, durability after storage loss, readiness of the production control store, or safety of arbitrary unreviewed commands. Preflight source checks occur before the child execution deadline; this is not a claim that every filesystem operation has a hard whole-command timeout. A receipt stating that a process completed must still be interpreted with its exit code; process terminality is not an accepted financial result. The actual supervised step and its source/request/authority freeze remain lead work, subject to separate source criticism and scope review.

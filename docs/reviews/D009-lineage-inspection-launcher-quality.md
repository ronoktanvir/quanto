# D009 inspection launcher: independent quality

**Decision: conditionally accept the final launcher preparation, SHA-256 `d8940d31d587a94d599cb7ed733d7a90efdc503ae84a932b454ad7908d01d5bb`.** Its synthetic rehearsals support terminal-outcome recording, attempt consumption, bounded normal timeout cleanup, and refusal without result adoption. No actual launcher, controller instance, candidate, or private receipt was executed or accessed. Actual inspection acceptance remains a separate lead-owned decision requiring the controller's complete receipt and terminal checks.

Reviewer: `/root/lineage_v2_quality`, 2026-11-03. This reviewer did not author the launcher. Work used Python **3.11.9**, invented roots, generic invented children, and copies of the prepared source. There were no network, provider, model, financial, capture, materialization, or credential operations.

## Preserved defect and correction

The first launcher, `77f8c293b654ad4cb3403391c523ea669215924bbc9c65f0afd468cd951b82e5`, would consume its attempt and refuse the pinned installed interpreter. Read-only metadata showed that executable had mode **0775**, one link, and the expected SHA-256 `4e28e811a89aeac6eed668ae641c7f85f5831e42e8dc6cd9a85a3bcc032ec46a`; its generic digest check prohibited group write. A byte-identical invented interpreter copy at 0775 reproduced refusal before child dispatch. Actual use of that revision was withheld. The shared interpreter was not modified.

The lead's intermediate correction, `505e46793723f83aaca3f3adc5f894d451091d14e5addecb61b72b9f87321aab`, passed **13/13** scenarios. The final revision replaces its four-field identity lambda with an equivalent local function and was separately rehearsed. It permits group write only through the explicit runtime-executable path for the exact configured interpreter; world write, foreign ownership, non-private controller/receipt files, and wrong hashes still refuse. This exception relies on the stated trusted cooperating-host model. It is not protection against privileged or authorized group members changing runtime files between observations.

## Final executed evidence

The final source passed **13/13 terminal scenarios**, comprising **14 launcher invocations** because the consumed-attempt scenario deliberately invokes the same fixture twice. All launcher processes reached terminal outcomes and were reaped; none exceeded the rehearsal wrapper timeout or emitted stderr. All **9** started generic children were recorded as reaped and independently absent afterward. Expected nonzero and killed-child outcomes remain distinguishable from clean success.

- Clean exit records exact stdout, stderr, and intent digests; nonzero child exit records code 7 and refuses success.
- The hanging child is killed in its owned session and reaped with code -9; the launcher records timeout and refuses success. That fixture completed in **1.897584 seconds**.
- A second invocation preserves the consumed state byte-for-byte and dispatches no second child.
- Wrong controller hash, wrong interpreter hash at mode 0775, world-writable interpreter, and non-private controller each consume an intent, retain failure evidence, and dispatch no child.
- Matching interpreter bytes at mode 0775 succeed. Oversized stdout or stderr, controller mutation after dispatch, and a competing process receipt each prevent successful evidence publication or adoption; the competing receipt remains unchanged.

A separate terminal process passed **7/7 digest-boundary checks**: acceptance of the exact 0775 runtime; refusal without that explicit exception; refusal of private use or another path with the exception; refusal of world write; refusal of foreign-owner descriptor metadata; and continued refusal of group-writable project data. Foreign ownership was tested by mocking descriptor metadata, not by changing an actual owner. This process exited 0 without stderr or timeout.

The final scenario runner exited 0 in **4.015821 seconds**; the digest runner exited 0 in **0.129355 seconds**. The earlier 12-case first-revision run and 13-case intermediate run remain retained and attributed to their respective source hashes. No failing quality assertions were discarded.

## Fixture substitutions and limits

Rehearsal copies replace only the frozen root/interpreter paths, interpreter/controller hashes, and timeout constants. Every substitution is recorded. The original launcher retains **70 seconds** total and a **5-second** cleanup reserve; scenarios use **2.5 seconds** and **0.75 seconds**. The real inspection controller is replaced by an invented child that does no private work. Thus these tests exercise launcher mechanics, not the combined actual inspection.

Timeout tests establish observed cleanup for the tested Python callbacks and local filesystem. A delayed signal handler, blocked system call, or operating-system failure can prevent a bounded reap; neither the timer nor these tests supplies an OS-level termination guarantee. Such uncertainty must remain non-adoptable and consume the attempt. Every launcher success receipt still explicitly denies inspection-result and full-recovery acceptance.

## Exact evidence

Ignored `runtime/recovery-lineage-inspection-quality/launcher-quality-evidence.json` indexes source copies, per-case substitutions, terminal records, receipts, logs, and predecessor evidence. Its SHA-256 is `302822369526f64af243edfda1d3fd0df146b679b4b72b1c1ba030b2135742de`.

| Artifact | SHA-256 |
| --- | --- |
| Final scenario harness | `1173369661c3cd8033e9306dbc27f7eef54b51b95c3faa10568896b097191a89` |
| Final scenario summary | `025b34757d5417de6c5c729cde327bc05acb982c09983c1a0035bc082c6a4482` |
| Digest harness | `90dfbf7d2972987c2cd739b23d66828d3f852a69fd525263379c60c7d19cd386` |
| Digest evidence | `3892171d43c376e07ce366389f8dfb83492647b2718a7bf2a95a95592549eed4` |
| First-revision evidence | `ef34f47b3540e8ece442b7ef6f3ce3acaf28fcbd12d6dd6df7bbc10a0483fe06` |

This is synthetic software evidence. It establishes no actual recovery, backup sufficiency, historical or evaluator replay, economic validity, execution readiness, or investment performance.

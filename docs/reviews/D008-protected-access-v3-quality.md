# D008 protected access v3: independent quality disposition

The exact v3 correction passes the independent boundary and clean-install checks below. No remaining product defect was found in this review; the earlier malformed-response, unrecorded-import and terminal-publication findings are closed by the corrected behavior and separate criticism. Quality supports the bounded preparation-boundary increment, with **normal full GitHub CI still required for integration**. The local full-suite attempt was not a green run: a quality-runner multiprocessing defect caused one failure, which passed after correcting only the runner. That history remains explicit.

Reviewer: `/root/access_v2_quality`, separate from the producer, implementation critic and scope reviewer. All execution used invented temporary stores, fake credentials/responses and isolated public-code exports. No actual project data/store, credential, provider/model request, protected acquisition, financial replay or trade was accessed. Only this report and ignored quality artifacts were written. The prior [v2 quality record](D008-protected-access-v2-quality.md) remains unchanged with its withheld acceptance.

## Exact combined candidate

I verified all 24 files in producer manifest `0a4cb102500e9a94b7e38f37de18386ef72174241af7a12c218678a35c68d462` and contract `6ed97a87afaad2cc2646c4c02208cb60927c0d183754b64522f16f9ac9fa2ad6`. I exported committed baseline `ef41ee80d739d9aea19f7dfc7a16d0915c583cf6`, overlaid those exact frozen files and added the lead's two explicit D009 fixture adaptations:

| Additional fixture | SHA-256 |
| --- | --- |
| `tests/test_recovery.py` | `c8ad8db88dbd89531572c03180132e2065d348ae5eb346ea503d67a0cecdaf3b` |
| `tests/test_recovery_closure.py` | `7fcbdd4f07a6d72ff76808840755c2f95700a47c4b1f42cc2249d4734e727359` |

These helpers explicitly bind authority to their named invented source roots. They do not add ambient production authority or modify the recovery algorithms. The combined 26-file manifest is `edc7592687f9256694f40fd5c015eec02778a87aab108b7da1b6e3bcf11a4d69`. I subsequently compared every path against PR16 head `6f844e40761ff1b75d4a83251b4a15b9c0575761`: all match, and that head has no additional source/test changes outside the combined manifest relative to the exported baseline.

Source execution used Python 3.13.12. A fresh Python 3.11.9 environment received an offline, noneditable installation of the exact export. Public test documentation was included from the start. The runner asserted whether imports came from the source export or installed site-packages, rejected non-loopback DNS/socket calls and received a minimal environment without project keys. All 26 exported paths and six installed source modules still matched after execution.

## Independent behavioral evidence

The unchanged 16 v2 quality cases pass again. They cover separately visible pre-I/O commits, refusal when effect-start audit fails, real child-process crash persistence, revoked cache access, import exposure surviving research rollback/revocation, exact and one-use publication, stale publication after response widening, unknown transport outcomes, consumed-intent history, concurrent effect consumption, closed-session dispatch and ordinary-output privacy. These are synthetic software checks, not protected-market observations.

Eight new cases cover the corrected boundaries:

- An object, list or boolean pagination token cannot leave foreign content published under requested-security coverage. Each case invalidates the conflicting invented reservation and leaves no narrowly classified or published raw page.
- Oversized supplied bytes leave a bounded unknown observation before a later reservation can succeed. The private record identifies an attempt, not a fabricated digest of the unretained payload.
- Invalid JSON and an interrupted serializer leave committed unknown exposure even though no object is published. The interruption probe independently observes the control record before serialization stops.
- Supplied bytes remain accounted for when the research storage handle is already closed but its supervisor session is valid.
- A publication permit issued before its intent's no-access rejection cannot later be consumed. Supplied bytes fall back to conservative import accounting; no classification or publication is created.

Separate criticism, [report](D008-protected-access-v3-critic.md) SHA `9f375d5791b5412c2759c0b814f24c47e5bebddc90f930d37f3f34c44334f94e`, independently closes C5–C7 while preserving the earlier C1–C4 corrections. Its raw-HTTP, action and valid-token controls are critic-owned evidence, not executions attributed to this reviewer.

## Executed results and the preserved harness failure

| Execution | Observed result |
| --- | --- |
| Independent source probes | 24 passed in 0.70 seconds |
| Identical independent clean Python 3.11 probes | 24 passed in 1.13 seconds |
| Clean installed producer selection plus independent probes | 324 passed in 36.24 seconds |
| Initial full source selection, including 24 independent cases | 1 failed, 1,642 passed and 37 subtests passed in 449.57 seconds |
| Failed multiprocessing node after runner correction, source | 1 passed in 3.70 seconds |
| Same corrected node, clean installation | 1 passed in 0.27 seconds |
| Ruff on the full exported source/test trees | Passed |
| Installed `quanto --help` | Passed |

The 324-case installed run contains the producer's 300-case selection plus 24 quality-owned cases. The full source selection includes the repository tests, both explicit D009 fixture adaptations and the same 24 independent cases. Its 1,642 passing parent cases are not 1,642 separate new quality-owned tests.

The full run's only reported failure was `test_process_lock_prevents_duplicate_attempts`. My runner invoked `pytest.main` at module top level without the standard `__main__` guard. Python's multiprocessing spawn re-executed that runner in the children, starting nested test runs instead of the intended capture workers. The parent's queue wait expired. The trace, unexpected child test output and runner source establish a harness defect; they do not establish a snapshot-lock product defect.

After the parent pytest summary, its process remained alive waiting for the unintended children. I enumerated and terminated only the confirmed quality parent and its three descendants, then confirmed those processes were absent. The outer recorded outcome is therefore signal termination (`-15`) at559.49seconds, not a clean test exit. The reason was the demonstrated recursive harness behavior, not elapsed CI time or an observation timeout. All original output and the unguarded runner remain retained.

The sole correction added the runner's `if __name__ == "__main__"` guard. No exported product or test bytes changed. The exact failed node then passed in both source and installed environments and exited cleanly. The source evidence is consequently split across an initial failed run and a corrected one-node run; it is not rewritten as a single green full-suite pass. With the lead's agreement, no redundant full local replay was performed. Normal GitHub pytest on the exact integrated head remains the separate full clean-checkout corroboration gate.

The CI workflow installs the package but its pytest configuration adds `src` to the import path. A successful normal CI run therefore supplies full clean-checkout source evidence, not proof that every test imports the installed wheel. Only the explicitly asserted site-packages runs above are called installed evidence here. Their scope is 324 selected cases plus the separate corrected multiprocessing node. The lead will record actual final-head CI results separately; none is invented or anticipated by this report.

## Acceptance limits and retained evidence

The bounded software correction has no remaining quality blocker identified here, subject to final full CI. It does not deploy the control boundary, reconcile legacy exposure, fence old processes, isolate or release protected evaluation, establish external freshness, restore the separate control store consistently, or complete R13/R14. Synthetic passes create no protected eligibility, financial validation or execution authority. No durability or CI-timeout requirement was relaxed.

Ignored evidence is retained under `runtime/protected-access-v3-quality/`; `quality-evidence.json` has SHA-256 `b39653b3fb72c4b7f054e47146c05f4a8db823d5bc15435db57fbe358b1d2a29`.

| Artifact | SHA-256 |
| --- | --- |
| Unchanged 16-case independent source | `2b2880f1077218bd6eb2b26ff8890af8912a857b2e5250b71238860a66559f10` |
| Added eight boundary cases | `44ef04b9640520bd9637b8f2a938595c21c6a1abf1ece6aa52bb9ae030c2a001` |
| Original unguarded runner | `addc86adb252b00c65f48fd000b63d75a826e8dc5e7ebca0d509a2786f0ff503` |
| Corrected guarded runner | `049f6896801a8a468d2141d6a02fb491dc3fafd9da99bf12828812950dd91034` |
| Initial full source output | `63015ea1a20af8dc85dd1a367dc223909161c06c7414dbf7ac4eaa896a091677` |
| Initial full run process outcome | `3b860e5a5d4a8cc34e04e39cbb00f5e74b2b4a941567140ea6a8d896aa745731` |
| Clean selected output | `eea8ccc11af70c36eca46c99a63c07374fae94eb035d3364ec306be49341c0d5` |
| Corrected source multiprocessing output | `1b0a6e83dbd3855e492cbe1c6dcb640f53cbc1f640a701d8a46adedd4f31d9ca` |
| Corrected installed multiprocessing output | `3b4ad3097d7020cd8b172384869bd1db1102ffc4c9316bde31fef1b3bcacf9c6` |

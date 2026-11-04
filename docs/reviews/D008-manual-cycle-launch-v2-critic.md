# D008 manual-cycle supervisor v2 criticism

**The corrected supervisor resolves the nine v1 objections within its stated process boundary.** I accept this parent and paid worker for the proposed single manual attempt, subject to separate quality and scope review, acceptance of the corrected auditor and the lead's actual private preflight. Sixteen independent invented cases passed.

## Ownership and one-use publication

Both registration and paid execution now wait for a one-byte grant on a dedicated pipe. The parent obtains the child handle, publishes its actual PID and launch binding, publishes the start receipt, verifies time remaining, then writes the grant. `publish()` uses exclusive creation, synchronizes the file and directory, and reads back the exact bytes. The child verifies the grant, the actual PID/PPID and the hashes joining consumption, launch, ownership and start.

I tested interrupted spawn independently for both phases. An invented child had inherited the read descriptor when the simulated spawn raised before returning a handle. Each inherited descriptor received EOF. In two positive cases with real pipes and invented handles, receipt hashes and the selected PID matched when the child read the grant and each phase produced its bound exit record.

The corrected worker refused missing ownership, a mismatched PID and a preexisting parent failure before creating paid receipts. A worker that lost the exclusive paid marker preserved the earlier attempt byte-for-byte. A valid invented worker entered its broker stub once and bound ownership, start, budget, prelaunch, launch and paid consumption to the entry record. Repeating that invocation preserved the first result and produced no second stub call.

## Clock, budget day and interruption

The paid worker keeps both original clock limits live. I reproduced the v1 changes after prelaunch publication. A wall-clock advance of 7,300 seconds, a changed parent PID and rollover into a day with zero research-purpose headroom each stopped before broker entry. A separate simulated broker reached its entry point while authority was valid, then lost ownership or crossed midnight. The installed profile stopped the body of the named authorization/send boundary before either simulated effect executed. The frozen product functions use those exact module and function names. An already started network request can still leave a charge uncertain.

Registration now runs in a granted child. The parent waits in intervals of at most 0.25 seconds and checks both clocks around a terminal observation. A simulated wall advance during the first poll prevented another poll and further paid launch. Cleanup distinguished a terminal callback returning at elapsed wall time 7,201 seconds as `terminal_observed_late`. Failure evidence explicitly leaves descendant quiescence unverified. The guardian establishes when it observed its own handle and whether the cycle may advance. Interrupted nested registration effects can require separate inspection.

The existing SQLite planning snapshot continues to bind LA day, global and research-purpose headroom, allocation prefix and journal head. Actual per-call authorization remains the broker's responsibility. The plan must select the auditor manifest for these exact launch sources. A broker return still requires the separate trace and numerical audit.

## Exact evidence

| Artifact | SHA-256 |
| --- | --- |
| Joint freeze | `a57edc801c50e1657536d76d15a41075faefe914ce9539ae64d76a1a3c2fb5c9` |
| Parent | `43f992b081fe7bd5f23d6163dafd5827d265630a6b3049ecf58857eaa802d830` |
| Paid worker | `9a59cb3eb37f8b6f06d17abde2a474da13fba07264bd37c634ee12a07f0cd01c` |
| Producer report | `482eadba1c217a159374818ef7a08857fe2d2929c885c6c61d56c2b7d594ed29` |
| Parent tests | `af7f64b4e2ea6461f93fc3b9cadcf8c88523276b663fce50c58450430f4baa48` |
| Worker tests | `7694ff9ada310d5c27c84cca5907464099475c5cbbc1c09b4b6180a723669c1a` |
| Preserved v1 criticism | `7784593fd5502026c73b94c54c3857c11e8ed5881e07837cb73d762d25e6fd38` |

The 13 independent regression cases passed in 0.10 seconds and the three positive cases in 0.15 seconds. Their logs are retained under ignored `runtime/development-cycle-launch-v2-critic/`, with hashes `2a478b5123741bc2c16cf9b2a2fa445a4dda94d1f2b3d1bf6b499bf6d6478b01` and `1d3314562a9345a9f75b1adf32d61168822c00d316f7db85833230bba023e448`. I reused the invented worker fixture and supplied the faults, assertions, simulated handles and pipe checks independently. All four frozen source/test hashes and the producer report matched. The producer's separate 91 cases and retained earlier failures keep their original attribution. Actual private inputs, registrations, credentials, model calls and finance were outside this review.

# D008 registration preparation v2

Version 2 corrects both timing defects identified in the first controller. The 600-second work clock now covers initial preflight. Cleanup has a single deadline five seconds after the original work deadline. The independent critic accepted the original request mapping and authority checks within the reviewed scope. [First controller criticism](D008-current-code-registration-critic.md)

The parent arms its work alarm before it checks the environment, packet, source or databases. It derives both deadlines from entry into `run()`. If work fails, it transfers the owned child handle to one cleanup path. Poll, kill and wait each consume the time still available. The outer `finally` restores signal state without attempting another reap.

When time has already expired, cleanup performs no further poll or wait. If the child cannot be observed to have terminated by the cleanup deadline, the controller reports `cleanup_unobserved`. If there is insufficient time to publish a terminal receipt, existing consumed, launch and ownership records document the partial attempt. Delayed signal delivery or blocked operating-system I/O can prevent prompt process termination. The time bound describes the controller's scheduling and waits under ordinary process operation.

## Producer evidence

All 17 existing invented-root cases passed in the initial v2 run. Nine new regression cases also passed separately. Three use real alarms to interrupt deliberately stalled environment, packet or source preflight. The simulated-clock cases exercise the parent's exception path with an invented process handle. With only one second left, the controller arms a one-second alarm. After the simulated kill consumes a quarter second, the wait receives the remaining 0.75 seconds. When the alarm arrives after cleanup expiry, the controller records uncertainty and skips the second wait. The tests also exercise a failed kill, an expired wait and the refusal to grant extra time after a deadline.

The combined run passed all 26 cases in 45.40 seconds. Lint passed. The positive fixture invokes the same revision, admission and suite registration functions that the real operation would use. All inputs for these rehearsals were invented. No actual input, registration, model request or portfolio calculation was used.

## Files for independent review

The working copies are in `runtime/development-cycle-registration-v2-preparation/`. The corresponding `frozen/manifest.json` binds the copies of the controller, tests, source manifest, report and producer checks. Version 2 retains the same product source manifest as version 1. All 33 listed repository files matched at freeze. The version 1 controller, tests, manifest and report also matched their previously recorded hashes.

| Artifact | SHA-256 |
| --- | --- |
| V2 controller | `3f52a95452d9a20c6c456624f33a70c717d9f1fc28d83ae65f178e67e9d7047d` |
| V2 tests | `b717f8603b65570feb4b84c23e4301a1f26f54784a11ebd8ad4bac19423d1d79` |
| Source, interpreter and loaded-code manifest | `aa65675f3c7886a2d950b75928811d4f7189adbc2342a383b983f0ea20ea70c4` |
| Version 1 criticism | `9a32ac023947ccd55a49bed8cf8950e40c5f7f5dfb34da2443abb9558b269ba6` |

The next gate is independent review of these v2 files, followed by the lead's verification of the actual private packet and current authority. This preparation covers the three local registrations only. A later research controller must account for elapsed preparation time against the same 7,200-second cycle start.

# D008 current-code registration v2 criticism

Version 2 resolves both timing findings in the original criticism. The parent covers initial preflight with the work alarm and derives the end of cleanup from the same start time. I accept the corrected helper for the three proposed local registrations, subject to separate quality/scope review and the lead's current private-packet verification.

## Exact review target

| Artifact | SHA-256 |
| --- | --- |
| Frozen packet manifest | `da2db83c28e465345bb74c59e479fcf4fef233d6af8ef2d7406c26c59144fe38` |
| V2 controller | `3f52a95452d9a20c6c456624f33a70c717d9f1fc28d83ae65f178e67e9d7047d` |
| V2 producer report | `9d27b3b07a006d2051b6b8d73cbfe3e06a72c9a3aedddffa565f47180e895628` |
| V2 producer tests | `b717f8603b65570feb4b84c23e4301a1f26f54784a11ebd8ad4bac19423d1d79` |
| Product source/runtime/loaded-code manifest | `aa65675f3c7886a2d950b75928811d4f7189adbc2342a383b983f0ea20ea70c4` |
| Preserved v1 criticism | `9a32ac023947ccd55a49bed8cf8950e40c5f7f5dfb34da2443abb9558b269ba6` |

The nine frozen components matched their working copies and manifest digests. All 33 product source/dependency files matched the source manifest at final verification. The comparison against v1 controller `1d0cd609d6e3185df00c54040b990f7b756d40e689ccd00a876ae12a9515bd84` localized the changes to timing, ownership during launch, cleanup state and its refusal reason. The original criticism and witnesses retain their separate disposition.

## Findings and evidence

`run()` computes both absolute deadlines on entry and arms the work alarm before environment, packet, source and store checks. A separate child first bounds its preflight, then reads and adopts the parent's shared deadline. The parent's exception path transfers its owned handle once and arms only the remaining cleanup time. Each poll, kill and wait checks that same deadline. A late terminal observation or interruption before acquiring a child handle remains explicitly uncertain. The final signal cleanup cannot start another reap.

Six independent scheduling probes passed in 1.145 seconds. Two used real alarms. A stall at the first environment check was interrupted and the prior signal handler restored. A stall immediately after durable marker publication left that marker intact and a subsequent invented attempt refused reuse. The remaining four used a simulated clock and an invented child handle. With one second left, poll and kill consumed 0.375 seconds and the wait received exactly 0.625 seconds. Expired cleanup initiated no new operation. A poll that returned after expiry could not establish timely termination. An interruption inside launch preserved an unknown launch outcome.

One additional invented registration test passed in 8.71 seconds. It used the producer's fixture builder and normal product registration functions. The three phase children shared the parent's deadline, exited successfully and returned fresh submission identities. The revision used its exact retained request and the result kept paid-launch authorization false. This covers the ordinary path alongside the focused failure probes. The producer's separate 26 passing cases remain attributed to the producer.

The independent evidence is retained under ignored `runtime/development-cycle-registration-v2-critic/`. The scheduling source and log hashes are `cae568f874a5265082cff66acd09c8082680a2dcf1ff2baac3a28be4b9d5f392` and `f83db5815e3134addaa5878549d8c648f5333af2b473d7cdb92084c72aee2335`. The ordinary-path source and log hashes are `d1e5ccb4cb73db9c430399837633b54722eb2afe438ba07d244a175ff97c9790` and `8a0b34157d395d4ebcae3339e44c62125965aa75ec18fba0e949ed13ddd55aec`.

These bounds govern ordinary process scheduling and observation. Delayed signals, blocked kernel I/O or loss of a launch handle can leave cleanup uncertain. The actual private requests, authority and databases were outside this criticism, and every executed registration used invented evidence. The proposed paid controller still needs to deduct actual preparation time from the common 7,200-second start.

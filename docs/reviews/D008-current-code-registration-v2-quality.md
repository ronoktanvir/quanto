# D008 current-code registration v2 quality

I accept the frozen v2 controller for registration preparation. All 26 supplied cases passed in 27.09 seconds. Separate paired checks against the frozen v1 controller reproduced the two timing defects and demonstrated the corrected v2 outcomes. Both commands exited zero. This is `synthetic_fixture` evidence from invented projects outside the workspace.

| Inspected item | SHA-256 |
| --- | --- |
| V2 freeze manifest | `da2db83c28e465345bb74c59e479fcf4fef233d6af8ef2d7406c26c59144fe38` |
| V2 controller | `3f52a95452d9a20c6c456624f33a70c717d9f1fc28d83ae65f178e67e9d7047d` |
| V2 tests | `b717f8603b65570feb4b84c23e4301a1f26f54784a11ebd8ad4bac19423d1d79` |
| V2 public preparation report | `9d27b3b07a006d2051b6b8d73cbfe3e06a72c9a3aedddffa565f47180e895628` |
| Product, interpreter and loaded-code manifest | `aa65675f3c7886a2d950b75928811d4f7189adbc2342a383b983f0ea20ea70c4` |
| V1 controller used for comparison | `1d0cd609d6e3185df00c54040b990f7b756d40e689ccd00a876ae12a9515bd84` |

Reviewer `/root/access_v2_quality` verified all nine frozen files and all 33 public source/dependency hashes before and after the runs. The observed repository HEAD was `d8e6f24a136bcc086ccf82692deb1e9f6404bb3a`. Pytest 9.2.0 ran the exact frozen tests under Python 3.13.12. The registration controller's fixture subprocesses and the independent paired checks used pinned Python 3.11.9 (`4e28e811a89aeac6eed668ae641c7f85f5831e42e8dc6cd9a85a3bcc032ec46a`) with `-I -S -B` and an empty requested environment.

The positive fixture performed all three local registrations. It checked the revision request, admission's updated policy-revision reference, and the ordered suite members' updated admission references. A repeated invocation refused as consumed. The combined run also exercised missing or replaced databases, changed source/request/authority pins, incomplete phase histories, forbidden calls and nine timing cases. These are independently reproduced producer tests.

The separate quality probes applied identical stimuli to both controller versions. The preflight probe delayed the first descriptor check during the read of an intentionally incomplete invented packet. Both versions passed their ordinary interpreter checks and began reading the packet. The cleanup probes used an invented handle and a controlled clock, including a wait that **returned normally with a terminal exit code after its observation deadline**. No system PID was signalled by those probes.

| Paired case | V1 observation | V2 observation |
| --- | --- | --- |
| A 0.50-second packet-read stall with a 0.12-second work allowance | No alarm was armed during the descriptor check. Returned `invalid_packet` after 0.503 seconds. | The alarm was armed before the descriptor check. Returned `deadline` after 0.122 seconds, interrupting the stall before it returned. |
| A poll returned exit code zero 0.01 seconds beyond the absolute cleanup deadline | Waited again with a fresh two-second allowance and reported `reaped=true`. | Reported `cleanup_unobserved` after the late poll and stopped. |
| A wait returned an exit code 0.01 seconds beyond the deadline | Granted two seconds and reported `reaped=true`. | Granted the remaining 0.125 seconds, checked the clock again after the wait, and reported `cleanup_unobserved`. |
| The same wait completed before the deadline | Reported `reaped=true`. | Reported `terminal_observed` with `reaped=true`. |

The four paired scenarios passed under both versions in one terminal run. The real alarm witness created no registration history and observed the original signal handler restored. The simulated cleanup witnesses establish the controller's treatment of a late observation. They do not measure OS scheduling latency or guarantee termination when a system call blocks.

Exact commands, tool outcomes and probe sources are retained in ignored `runtime/development-cycle-registration-v2-quality/`. The combined log is `8914706adef9da00a8378416ab2c580eb6a012b9ff926c82c30f645dc30f692b`. The paired probe source is `eecd8b137df61e577d0d66d3fee751fc26a30ed527dcb646c9735edd839d26fc`, its output is `154ee7748b9b1b9e0a58f8e62d3161ab69fd2650ff8c41355ab275f8359a844b`, and the aggregate evidence is `29d965bc3cf3fd410a3ba40c144fb126628a82a38525ada5c3edced7001ba92b`.

The lead must still verify the private packet, current authority and applicable reviews before actual registration. This review used no actual inputs, databases or registrations and made no network or paid calls. A later research operation must charge elapsed preparation against the common 7,200-second cycle budget. Research launch, portfolio replay, protected eligibility, unattended scheduling and live execution remain outside this acceptance.

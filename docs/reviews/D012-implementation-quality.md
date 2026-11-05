# D012 independent executed quality review

The inspected prototype passes this bounded quality review: **199 distinct test cases passed**, including 28 independently authored failure probes. No defect was reproduced within the tested scope. This accepts invented-data software behavior only. Actual outside-model review, a reviewed one-shot administrator controller, production evidence inspection and production activation remain outstanding. The D011 explicit-pin transport is now implemented and tested; it has not been used for an actual campaign.

## Exact inspected artifacts

Checkout HEAD was `8e40eff6a86bb27b0ba95dbd2ce449e19d8a4f80`, with the following uncommitted implementation bytes. Authority and registry hashes matched the producer's declared freeze before the independent probes and after the final run. The table records all inspected artifact hashes at the final check.

| Artifact | SHA-256 |
| --- | --- |
| `docs/D012_DESIGN.md` | `1f5254505b6bc8a8c84d3a2e492e61b87e9d96ce76eda3b3e2365b58b7d96933` |
| `src/quanto/authority_reattachment.py` | `25c77d865427483b3fb705532c97a53d17a14d0edfee8c98f95e89ed7808dd46` |
| `src/quanto/evaluation_registry.py` | `3ca6d69da364c37a2e53973dd70a867532d2174e9e78310b78d2c57b9b52cb34` |
| `tests/test_authority_reattachment.py` | `fbec5fed88f40c1c6b6692acfd5cb54c9e102024660fb6067b0bc245b2d09ed0` |
| `tests/test_evaluation_registry.py` | `cba80802c40a98c0217ec54b89ebdcae5f05d0142759a7307175330037a2b3c4` |
| `operations/strategy_campaign/supervise_step.py` | `8eba085aae7f8f4a54a41972e4cd4a1ac43f990aaefe8676d8b53aabf42b3a8c` |
| `tests/test_strategy_campaign_supervisor.py` | `7f09efc3f97eac82ac4ab002eae3e34d7f8544d76464ed5fe0feb847fe485435` |
| Independent scratch `runtime/d012-quality/test_independent.py` | `c3f1b9ef809f153d76b2dd973497cb09416bb1425c8c8e745e686b8db8c938f3` |

The independent scratch belongs to the resident worktree and is ignored. It never accesses the original production runtime. I changed only this report and that scratch; I did not change producer source or tests.

## Executed evidence

All cases are `synthetic_fixture`. Runs used the existing `/Users/ronoktanvir/Documents/ChatGPT/quanto/.venv/bin/python`, with `PYTHONPATH=src:tests`, on the Mac. Invented stores used actual filesystem identities; only their invented persisted historical device differed. No filesystem-identity monkeypatch, real reboot, provider, credential, market data, outside-model call or production operation was involved.

| Executed set | Observed result | Terminal chunk |
| --- | --- | --- |
| Producer reattachment plus existing evaluation-registry tests | 151 passed, 12.80 seconds | `66c38e` |
| D011 process-supervisor tests, including explicit attachment pin | 20 passed, 4.95 seconds | `d07e4a` |
| Independent failure probes | 28 passed, 4.62 seconds | `8c71f9` |

The initial 19-case independent set also passed in 4.07 seconds (`32abba`). Nine noncanonical-pin cases were then added; the final 28-case result supersedes that count rather than adding the repeated cases twice. No attempted independent test run failed.

## What the independent probes establish

**Exclusion works across actual processes.** A paused administrator held its real control and research `BEGIN IMMEDIATE` transactions. Separate raw SQLite writers failed on both stores, and a fresh supervisor failed with `maintenance_busy`. After release, acceptance committed and a new session opened. A separately running accepted session blocked exclusive maintenance even while idle; killing that process released its gate. Two simultaneously released administrators with distinct attempt identities produced exactly one acceptance event.

**Interrupted writes do not silently authorize.** Separate children were killed with SIGKILL immediately after inserting the acceptance event and immediately before commit, using execution-boundary hooks rather than changed filesystem results. Read-only inspection found no accepted event; complete logical row/schema comparisons matched the preattempt states. A child that exited without output after commit left exactly one event. Inspection recovered its exact plan binding without rerunning the administrator. These are observed process-crash boundaries, not simulated power-loss or disk-controller durability tests.

**Preservation is checked by content and behavior.** Independently constructed stores contained uncertain and reserved budget holds, a consumed dispatch, a consumed access effect, widened exposure, a reservation/invalidation and a revoked principal. Acceptance changed only the appended control event. All other row values and schemas, including all research rows, matched. A fresh interpreter retained the full 1,000-microUSD committed fixture budget, refused another unit of reservation, rejected the consumed dispatch/effect and revoked principal, and refused protected acquisition.

**Pins and history are not replaced by matching counts.** Independent mutations changed a retained control row, replaced TEXT with equal-looking BLOB, changed a research hold, or appended valid later control/research events after freezing. Every stale plan refused without an acceptance append. Hardlinks, symlinks, changed directory permissions, relocation, altered principal configuration and wrong source identity also refused. Restoring valid preacceptance database bytes into the same inode could not satisfy the missing event pin. An already-open accepted supervisor detected a changed retained row on its next database operation.

The D011 tests exercised real child entry with missing, wrong and correct pins. Only the correct pin reached the real CLI's intentionally invalid request; none calculated a strategy. Nine additional independent checks rejected Boolean, numeric, collection, empty, wrong-length, uppercase and newline-suffixed pins before subsequent preflight. Existing registry/reattachment cases separately cover malformed event payloads, duplicate events, chain corruption, bounded scans, stale witnesses, original-device fallback and unchanged legacy/protected restrictions.

## Preserved objections and limits

The earlier SQLite-file `flock` conflict is a producer/critic-attributed finding, not an independently reproduced predecessor failure here. This review tested the corrected existing-directory gate and directly verified coexistence with both SQLite write locks. The gate covers cooperating upgraded paths; old callers and privileged filesystem replacement still require the declared operational exclusion.

The library does not durably consume an administrator attempt before invocation. Its successful-event uniqueness does not prevent retry after a precommit crash; the still-missing outer controller must supply that separate rule. Read-only reconciliation does not itself authorize retry. Full local-row agreement also cannot detect coordinated rollback of all local witnesses or establish external freshness. The fixtures are small, and these results do not certify production-volume timing, a clean Linux installation, full campaign behavior or all storage-failure modes.

The tested change therefore supports continued prototype integration while production remains closed. It does not complete the owner's cost screen, genuinely unseen evaluation, recovery assurance, unattended operation or trading authorization.

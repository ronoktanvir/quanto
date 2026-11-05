# D012 implementation preparation: synthetic fixtures only

The proposed attachment implementation preserves existing authority records and requires the exact committed event hash on each newly constructed attached supervisor. Producer checks passed on invented stores. **This is not D012 policy acceptance or permission to operate on production.** The actual Fable and Opus reviews were not dispatched because the council preflight stopped at OAuth-status timeout; both uncertain holds remain. Independent implementation criticism, executed quality, scope review and the concrete administrative operation have separate acceptance gates.

## Exact source inspected and executed

Prepared in the resident checkout on `codex/authority-reattachment`, based on HEAD `8e40eff6a86bb27b0ba95dbd2ce449e19d8a4f80`. These uncommitted artifact identities identify this producer result more precisely than HEAD:

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/authority_reattachment.py` | `25c77d865427483b3fb705532c97a53d17a14d0edfee8c98f95e89ed7808dd46` |
| `src/quanto/evaluation_registry.py` | `3ca6d69da364c37a2e53973dd70a867532d2174e9e78310b78d2c57b9b52cb34` |
| `tests/test_authority_reattachment.py` | `fbec5fed88f40c1c6b6692acfd5cb54c9e102024660fb6067b0bc245b2d09ed0` |

`inspect_authority` reads existing stores with bounded table, row, byte and SQLite progress checks. `ReattachmentRequest` owns immutable canonical JSON binding the complete inspected state, old/current physical identities, retained-prefix witnesses, consumed-attempt identity, implementation/interpreter, attributed policy/review pins and prepared campaign hash. The hashes identify supplied evidence; they do not establish that a review passed or that the outer attempt was consumed.

`apply_reattachment` takes an exclusive advisory lock on the existing access-control directory, then `BEGIN IMMEDIATE` on control and research in that order. It rechecks the frozen state and appends exactly one versioned event to the existing control audit table. Research is a locked witness and is rolled back without business writes. Postconditions require exact old control prefixes, no additional non-audit control rows, exactly one new audit row and exact research state. Configuration, schema and principal identities are unchanged. This is one-database atomicity with two-store exclusion.

`Supervisor(..., attachment_event_sha256=...)` validates the exact event and complete local chains, original configuration, exact current physical identities and retained control prefixes. After acceptance, absent/wrong pins refuse even when the persisted original device is changed to equal the current device. Normal later control growth and research hold settlement can proceed while preserving the accepted anchor. No-event stores retain strict original binding. Sessions retain a shared maintenance lock through context exit; standalone supervisor database operations retain it through connection use. A PID check rejects inherited supervisor/session authority after `fork`.

## Executed software evidence and preserved failures

All inputs were `synthetic_fixture`: invented temporary files, nonsynthetic legacy configurations, principals, exposure records, invalidations, unfinished/uncertain effects, spending holds and consumed-operation markers. Fixture construction wrote an invented old device into a disposable database. Accepted reopening used actual filesystem calls in fresh interpreters, without metadata monkeypatches. No original production runtime, credentials, private request, provider or outside model was opened or invoked.

- The focused file contains **44 passing tests**. Combined with existing evaluation-registry and provenance coverage, **200 tests passed in 11.44 seconds** using the existing CPython 3.13 environment. Ruff passed on the three implementation/test files. This producer did not execute Linux or the clean-checkout CI matrix.
- Actual competing processes committed exactly one attachment. Actual live sessions excluded administrators; exclusive administration excluded fresh supervisors. Nested shared session/database gates worked with SQLite writes. Separate SQLite transactions excluded non-upgraded SQL writers on both databases.
- Checks covered complete old-row preservation, stale/divergent plans, missing/replaced stores, malformed but correctly chained events, duplicate/repeated acceptance, chain corruption, absent/wrong pins, current research-file replacement, protected/legacy/revocation refusal and normal subsequent growth. Injected failures after append and immediately before commit rolled back; lost postcommit process output was reconciled read-only without retrying the consumed attempt.
- **The initial SQLite-file gate was defective on macOS.** The independent critic reproduced that `flock` on the database inode conflicts with SQLite's own locking. The producer then executed a disposable-directory probe showing that locking the existing parent directory permits SQLite `BEGIN IMMEDIATE`, insert and commit. The final process tests exercise the corrected directory gate. This failure is retained, not counted as a passing design.
- **The initial supervisor allowed fork inheritance.** The critic observed a child process use the parent's active session and issue a principal without constructing its own pinned supervisor. The final PID check and actual subprocess/fork regression refuse inherited session, principal-issuance and overview calls while permitting the parent to continue.
- An initial lint run found one unused test import; it was removed before the passing run. A hash-report command failed because the host Perl locale was unavailable; Python hashing supplied the exact identities above. Neither failure affected authority state.

## Bounded performance observation

A separate actual-Mac probe created **4,568 control events and 686 research events**, all with small invented payloads, then used the frozen implementation above. Preparing the request took **0.129 seconds**, applying it **0.173 seconds**, and constructing the attached supervisor **0.111 seconds**. Ten `overview` calls inside a live session took **0.105 seconds median**, with a **0.102–0.119 second** range.

Attached database calls rescan complete states/chains and retained control prefixes. This observation characterizes the invented workload only; it does not establish production throughput or that a D011 campaign fits its 300-second limit. The concrete campaign preflight must account for repeated validation. No check was weakened or replaced with a performance cache.

## Remaining operational boundaries

The administrative controller is not implemented here. It must durably consume the attempt before dispatch, enforce the selected interpreter/source and fresh bytecode path, supply an external deadline, bound private output and establish owned-process cleanup. A failed or missing event never grants a retry. Scan and lock limits do not hard-preempt filesystem I/O or all allocation; the outer deadline remains necessary.

Directory locking excludes cooperating upgraded paths; already running old callers require the separately attributed inventory/drain. Owner-controlled path replacement, coordinated rollback of every local witness, external freshness and all-object current contents remain outside this assurance. The request's historical witness digests must come from the retained concrete evidence. `legacy_unknown=True`, protected refusal, uncertain spending and consumed operations remain preserved. No acquisition, strategy result, unattended recovery or live-execution milestone follows from these software checks.

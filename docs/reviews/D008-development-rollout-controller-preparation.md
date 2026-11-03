# D008 development bootstrap controller: preparation evidence

The prepared controller passes its producer rehearsal on invented temporary roots. **It is not cleared for actual execution.** Independent criticism and quality must inspect the frozen controller and tests; the lead must later establish and retain the private process cut and preflight evidence. No actual control store, process inventory, research-data read, service change, provider/model request, paid diagnosis or reservation was performed during this task.

Producer: `/root/prepare_access_rollout`. This is implementation and producer evidence, not independent certification. The frozen product module was read without modification. No product source, repository tests, Git state, context files or isolated recovery-lineage worktree were edited. Authored code, tests and logs are confined to ignored `runtime/access-rollout-preparation/`; this report is the only authored public document. No entrypoint or control store was created under `runtime/access-rollout-actual/`.

## Frozen basis and artifacts

| Artifact | SHA-256 |
| --- | --- |
| Accepted rollout plan | `a109a5effa8c5cd5916443cfce30a8ab9c25a509b2f5b35359f2358c9ea5389a` |
| R1–R3 critic addendum | `f4493dce54c27b51f2521ce38aa39931a63fefc7be5da569eb1b2559e7e80380` |
| Frozen `src/quanto/evaluation_registry.py` | `c69c7de7e66c0d6f8b372304db482bf6d83ad0fe35960e55fc8fa00ac4a4b113` |
| Prepared `bootstrap-development-registry.py` | `bddf2c8cee3dd1636ab274bdf0ac56b7ffb055920447f28d3dab35d1d9cce94a` |
| Producer `test_bootstrap_controller.py` | `6f06617be295d01b988da1fb017e36e43ce9b1e5aa6672b9001fe4567ec523bd` |
| `freeze-v1.json` | `03094129100baa800c3095e82cdffb46275f5c18bbf378ba636dfbaae636495c` |

The product source basis is PR16 head `6f844e40761ff1b75d4a83251b4a15b9c0575761`. The manifest also freezes every retained producer test log and the lint log. A source or controller change requires another exact freeze and review; this report does not establish subsequent GitHub CI or merge state.

## Creation ownership and guarded reopen

The bootstrap child compiles the exact hash-checked registry bytes directly, without importing the project package or loading a cached bytecode file. Its module-local `OSObservation` forwards the original exclusive-create flags, path and mode unchanged. Only a successful return from that actual `os.open` supplies creation evidence. The returned file descriptor's device/inode, ownership, mode and link count are bound to the private intent and immediately retained in an exclusive create-witness receipt. A `FileExistsError` becomes `concurrent_create`, so the child cannot adopt a concurrent winner through the constructor's normal existing-file branch.

Reopen is deliberately **active guarded behavior**, not passive observation. The module-local guard checks the first child's exact existing file identity, refuses the constructor's create syscall with `FileExistsError`, and lets the original constructor execute its existing-store validation branch. It never performs a create syscall during reopen. The module-local `SQLiteExistingOnly` guard preserves existing read-only URI connections and changes each ordinary file connection to SQLite `mode=rw`, which permits reads/writes only to an existing file. It checks physical identity before and after connection. This also covers session validation and overview connections after constructor validation; disappearance between the path check and the SQLite call cannot create a replacement.

These guards leave the product file, schema and public API semantics unchanged while imposing stronger controller preconditions. Their exact mechanics require independent review. They establish no isolation from a hostile filesystem owner. A simultaneous owner replacement can still cause refusal or uncertain evidence; local identities and hashes do not establish external freshness or prevent rollback.

## Complete bootstrap witness

Both fresh children run `Supervisor(root, synthetic=False)`, open and close one session, verify exact root/principal binding, and confirm that the closed session cannot be reopened. They do not construct provenance, journal, conversation, acquisition or financial-worker objects. A read-only overview confirms the two source-defined protected flags remain false; a complete state check before and after that overview ensures it did not change the bootstrap state.

The verifier builds the expected schema in an in-memory SQLite database using the pinned module's exact schema and append-only trigger statements. It compares every `sqlite_master` table/index/trigger record, checks database integrity, verifies all eight configuration values including root device/inode, schema, synthetic state and `legacy_unknown=True`, and requires one default principal and exactly one valid bootstrap audit record. The audit's predecessor, canonical payload and event hash are checked. No extra application row is allowed.

| Expected table group | Required count |
| --- | --- |
| `configuration` | 8 |
| `principals` | 1 |
| `audit` | 1 |
| `principal_revocations`, `relations`, `intents`, `intent_ends`, `permitted_pages`, `effects`, `effect_ends`, `reservations`, `invalidations`, `classifications`, `widenings`, `producers`, `producer_responses`, `publications`, `publication_ends` | 0 each |

There are 18 application tables in total: three nonempty bootstrap tables and 15 required-empty tables. The private witness includes canonical schema/state hashes, configuration and bootstrap audit identity, all table counts, file byte hash/size and physical identity. Bootstrap and reopen must agree on this entire witness and the loaded-code identities. The parent also rechecks the final file identity and byte hash before publishing its result. Root paths and principal/store identifiers remain in private receipts; public output contains fixed lifecycle/limitation fields and counts.

## Bounded execution and retained failures

The parent supplies the exact pinned interpreter invocation `-I -S -B`, an empty requested environment, a fixed working directory and no input stream. macOS/CPython may synthesize only the explicitly checked locale metadata keys `LC_CTYPE` and `__CF_USER_TEXT_ENCODING`; no credential or Python startup-path variable is allowed. The registry source bytes, compiled code, loaded callable/constant identities, imported standard-library origins and file hashes, interpreter binary/version, controller and test identities are bound privately. Changes to loaded functions or the schema constant refuse before creation.

One monotonic 30-second work deadline spans both children and terminal publication; it does not restart for reopen. The parent has a 40-second alarm and records the actual `Popen` handles it owns. Every failure/interrupt/timeout path kills and reaps an outstanding owned child and closes its pipes. Each child also receives the same remaining work deadline. No unrelated process is signalled, and no global process inventory is inferred from these handles. These are local cooperating-process bounds, not a guarantee against an uninterruptible kernel or a hostile owner.

All intent, request, launch, owned-child, exit, create-witness, result and failure files use exclusive creation, private permissions and file/directory `fsync`. A consumed marker and existing attempt directory prevent a second name from becoming an automatic first-create retry. The controller has no delete, repair, reconciliation, resume or retry command. A failed attempt leaves partial or committed control evidence in place. Even a published success-shaped result followed by an interrupted/lost outer completion remains unaccepted; adoption requires the lead's clean outer exit observation and the bound terminal receipts together.

The child audit monitor denies network/process creation, project imports, research-file reads and unrelated writes. Python file accesses are constrained to reviewed source/standard library, private receipts and the control store; SQLite connection targets are constrained to the control file or the in-memory schema oracle. SQLite's internal control-file sidecars and the new control directory belong to the allowed store footprint. This is a reviewed application boundary with source and fixture evidence, not an operating-system sandbox or a comprehensive observer of arbitrary native code.

## Producer execution evidence

Final command: isolated Python3.11.9 runs `runtime/access-rollout-preparation/test_bootstrap_controller.py`. Final log `producer-run-07.log` reports **44 test methods passed in 6.599 seconds**, with 20 explicit subcases (15 non-bootstrap tables and five configuration/audit mutations). `lint-run-01.log` reports all selected Ruff checks passed. These are synthetic-fixture software checks; they establish no market or investment result. No unrelated product suite was repeated.

Rehearsals cover a successful bootstrap/fresh reopen; all bootstrap configuration/schema/principal/audit and table-state checks; missing authority, wrong root and permanently closed sessions; legacy refusal of a synthetic follow-on preparation reservation; preexisting valid and empty stores; a concurrent creator after preflight; disappearance before reopen and immediately inside an existing-only SQLite connection; source and loaded-code changes; unsafe permissions and symlink paths; exclusive receipt collision handling; failure before create, after exclusive create, during schema, after commit, during child/outer publication and after result publication; parent interruption with a live owned child; bootstrap/reopen/shared-work/outer timeouts; no reuse of consumed attempt identities; fixed safe output; and unchanged invented research/artifact/credential sentinels. The legacy-reservation probe occurs only as a separate synthetic follow-on after the controller's zero-effect fixture completes.

Preserved failures and corrections:

1. An initial public-file hash command failed because Perl `shasum` rejected the inherited locale. It never reached the intended source read. Isolated Python hashing then confirmed the required pins. No private material was accessed.
2. `producer-run-01.log`: 35 methods, nine failures and 15 errors. The child incorrectly rejected macOS-generated locale metadata; the static import check also treated lazy, unused project imports as startup imports. The producer restricted the locale exception to the exact noncredential keys and checked only executed top-level imports, while the child audit monitor still denies a project import at runtime.
3. `producer-run-02.log`: 35 methods, eight failures and 15 errors. Default marshal reference encoding made a loaded-code digest depend on object-reference lifetime. Identity serialization now uses marshal version2, includes wrapped callable code and critical registry constants, and retains interpreter identity.
4. `producer-run-03.log`: 34 passed and one error, plus pipe `ResourceWarning`s. The missing-file session test expected the wrapper's exception, while the original registry path check correctly raised its own `control_unavailable` first. The test now checks that original refusal and separately tests disappearance at the connection boundary. Owned-child cleanup now closes its pipe descriptors.
5. `producer-run-04.log`: 35 methods passed in5.184s. `producer-run-05.log`: 40 passed in5.930s. `producer-run-06.log`: 43 passed in6.444s. Those intermediate passes are retained separately from the final44-method freeze; their sources were not represented as the final reviewed artifact.

Temporary fixture databases and sentinels were cleaned up by the tests. Their test logs and frozen code/identity manifest remain. No actual control history was deleted or reconciled.

## Later lead dependency and acceptance limits

No private preflight receipt was produced. The actual entry requires a later lead-owned, hash-pinned `runtime/access-rollout-actual/lead-preflight.json` binding the root identity, frozen controller/tests/registry/interpreter, accepted independent reviews and final CI, paused research admission, authoritative evidence that old workers are terminal or quiescent, a lead-owned unexpired process cut, and the acknowledged website boundary. The receipt must remain valid for the bounded operation. The producer has inspected none of that actual state. A Boolean in a fabricated receipt would not establish a real process cut; the lead must inspect and retain its concrete ownership/liveness evidence.

The website may remain active within its separately documented boundary. The controller certifies only its own bounded access footprint and bootstrap state if a later actual operation passes. It does not certify global inactivity, loaded website code, existing direct-journal routes, model-pause state, service freshness or full access rollout.

`legacy_reconciled`, `protected_eligible`, `protected_acquisition_enabled`, `research_replayed`, `market_data_read`, `service_rollout_verified`, `full_recovery_verified` and `global_inactivity_verified` remain false. The older D009 generation excludes this control authority. Multi-store recovery, external freshness, protected evaluator isolation/release, complete route/process rollout, sustained research, prospective paper operation and separately authorized live execution remain incomplete. No new policy, council, purchase or paid retry is implied by this preparation.

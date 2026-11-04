# D008 current-code registration: concrete preparation controller

The concrete controller is prepared for independent review. It performs at most one current-code policy-revision registration, one admission and one suite registration, in that order, using the existing product functions and ordinary development access. Seventeen targeted invented-root tests pass. No actual preparation has run, and no private account, control store, request, receipt, budget or historical payload was inspected during this work.

Producer: `/root/development_cycle_readiness`, November 3, 2026. This implements the accepted source-only [next-cycle plan](D008-next-development-cycle-plan.md) and its [independent criticism](D008-next-development-cycle-critic.md), without changing product source, financial policy, model allocation, spending limits, execution permissions or repository state. Concrete criticism, independent quality and a lead-bound actual packet remain pending.

## Concrete scope and evidence

The artifact is `runtime/development-cycle-registration-preparation/prepare_current_code.py`; its adjacent test file and source manifest are part of the review packet. The final copies, report and digest manifest are retained in that directory's `frozen/` subdirectory. None is a consumed actual controller: all execution in this increment used marked invented roots outside the actual workspace, or public-source identity inspection.

| Artifact | SHA-256 |
| --- | --- |
| Controller | `1d0cd609d6e3185df00c54040b990f7b756d40e689ccd00a876ae12a9515bd84` |
| Producer tests | `d3b0684d6495f677ae4f6a0334c9c0713291f64283df51c1b88ecc669e55194b` |
| Source/runtime/loaded-code manifest | `aa65675f3c7886a2d950b75928811d4f7189adbc2342a383b983f0ea20ea70c4` |
| Final test log | `7400dab536f8c95c235d1e14af3856cfd210d5c1a61ba634d768a489d7bfa9b6` |
| Accepted plan criticism | `55b3723549124e629d11cf39d334042ae1f79cb8ef36f4c853aff69ec74f0d3b` |

The final producer run passed 17 cases in 25.61 seconds; lint passed. Two preceding complete rehearsals passed the same count before additional source-default and child-launch bindings were frozen. Producer debugging first found an OS-proxy attribute collision, overly restrictive handling of normal content publication, and an inappropriate directory link-count invariant. Those were controller defects, corrected before the passing runs; they were not actual application failures. One initial producer tool observation was lost, so it supplies no claimed test result. Earlier passing logs and earlier source manifests remain retained.

The positive fixture uses the existing public synthetic historical-evidence builder and actual registration validators. Fixture preparation runs under the project's Python; the controller's children run under the pinned Python 3.11.9, exercising a genuinely different stored code/runtime identity. No validator is replaced to make registration succeed. The tests verify exact preserved economic requests, fresh submission identities, access-audit growth, retained previous records, refusal of a second attempt, missing/replaced databases, sidecars, unsafe permissions, altered request/source/authority pins, changed inputs between phases and an outer timeout with no surviving owned child. Separate probes reject network/process/credential and portfolio entrypoints, and detect a changed registry policy constant and ledger constructor default.

## Fixed execution boundary

The interpreter is `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11`, version 3.11.9, executable SHA-256 `4e28e811a89aeac6eed668ae641c7f85f5831e42e8dc6cd9a85a3bcc032ec46a`. Parent and children require `-I -S -B` and an empty requested environment; only the documented macOS-generated locale metadata is tolerated. The interpreter is root-owned with the existing group-writable installation mode; the controller verifies its exact binary hash. It does not claim a hardened interpreter installation or hostile-owner isolation.

The manifest pins 33 source/dependency files, critical standard-library origins/hashes, compiled product modules, loaded function/method bytecode and defaults, loaded policy globals and the product's richer financial identity. Product imports compile the checked source bytes through a dedicated importer; an installed alternate package or stale bytecode cache is not used. Source and runtime roots are explicit and separately bound. The current concrete actual target is this repository/workspace; fixture runtime roots are separate. Source changes require renewed applicability review and new pins, not an automatic manifest refresh during execution.

Database creation is prohibited. Module-local OS guards intercept the constructors' existing-file creation probes, and SQLite guards force existing-only connections. Before and after each child, the controller requires the exact owned, single-link `0600` research/control files, original directory identities and absent SQLite sidecars. It pins the complete control schema and every table's initial content digest/count. Existing rows must remain a matching prefix; only the normal audit/intents/effects tables may gain rows. Authority configuration, principals, relations, reservations and other administrative tables must remain unchanged. Missing, replaced or conflicting authority stops preparation; it is never bootstrapped, reconciled or promoted.

The lead reports the research database now has mode `0600`. The original permission-helper terminal observation was lost; that limitation remains. This controller neither repeats that helper nor changes file permissions. Its actual preflight will have to observe the current metadata independently.

Each child has a Python audit boundary denying network, subprocess creation and unrelated file reads, including credentials. A profile guard refuses portfolio backtest, suite execution, broker, paid-model and acquisition entrypoints. Normal content-addressed publication is allowed only through the reviewed local path, including its temporary file/link/unlink sequence. These are cooperating Python-process restrictions, not OS confinement or protection against an owner modifying the environment.

## Private packet the lead must supply

The top-level packet has exactly these keys:

```json
{
  "version": 1,
  "root": "ABSOLUTE_ACTUAL_RUNTIME_ROOT",
  "source_root": "ABSOLUTE_REVIEWED_SOURCE_ROOT",
  "attempt_id": "ONE_NEW_BOUNDED_ID",
  "manifest_sha256": "FROZEN_MANIFEST_DIGEST",
  "controller_sha256": "FROZEN_CONTROLLER_DIGEST",
  "tests_sha256": "FROZEN_TEST_DIGEST",
  "preparation_critic_sha256": "CONCRETE_ACCEPTED_CRITIC_DIGEST",
  "preflight_evidence_sha256": "LEAD_VERIFIED_PRIVATE_PREFLIGHT_DIGEST",
  "expected_state": {},
  "originals": {"revision": {}, "admission": {}, "suite": {}}
}
```

These placeholders describe the schema and are not an executable actual packet. `expected_state` uses the controller's read-only `project_state` shape: root/object-directory device, inode, owner and mode; control-file identity, schema digest and every table's count/content digest; research-file identity and byte digest. The lead must bind this observation to the existing accepted bootstrap authority and the actual cooperating-worker cut. The controller's expected-state equality does not independently establish that administrative review or global inactivity.

Each `originals` entry has exactly:

```json
{
  "submission_id": "ORIGINAL_32_HEX_SUBMISSION",
  "artifact_sha256": "ORIGINAL_REGISTERED_ARTIFACT_DIGEST",
  "request_file": {"path": "ABSOLUTE_PRIVATE_JSON_PATH", "sha256": "EXACT_FILE_DIGEST"},
  "request_binding": "retained_bytes",
  "submission_request": {"sha256": "ORIGINAL_RECORDED_REQUEST_DIGEST", "bytes": 123, "encoding": "utf8_text"}
}
```

Request files must be owned, single-link `0600` regular JSON files under the runtime directory, at most 64 KiB. Reviewed private copies of original files are acceptable; their copy/file identity must not be confused with the original registered request bytes. Accepted recorded encodings are `utf8_text` and `canonical_json`. Revision and suite require `retained_bytes`: the controller reads their retained request objects and checks exact digest, size, event/receipt binding and semantic equality with the supplied file. Admission may use `embedded_semantics` where original request bytes were never retained; that preserves the embedded request fields without inventing an exact original-byte reconstruction. All old success receipts are cross-checked against journal start/finish events and direct artifact references.

The new revision receives the original retained request text unchanged. The new admission changes only `policy_revision_sha256`. The new suite changes only the admission reference in each member; original member order, complete three-cost roster, dataset, dates, specification, sources and old failures are preserved. A private mapping records every old/new submission, artifact and new request identity. The normal product validators then recheck the newly registered object, including the complete suite after phase three.

The critic and preflight digests are durable lead-supplied review references. They do not make a pending criticism accepted, establish the preflight's contents, or grant invocation authority by themselves. Concrete review and private packet verification remain lead responsibilities before any actual command.

## One use, bounded failures and subsequent work

The lead must prepare an empty private `runtime/current-code-registration/` directory. The controller exclusively and durably creates a directory-wide consumed marker; changing the attempt name cannot bypass it. It then records the private intent, each request/launch/owned-child/exit record, operation intent and returned outcome, phase result, final mapping or failure. Children bind the consumed marker, parent intent and exact launch record. A partial marker or receipt collision is retained and refused, never deleted or repaired automatically.

The shared local work deadline is 600 seconds, measured from entry into `run`, with at most five additional seconds for owned-child cleanup. Every phase uses the remaining time, not a renewed per-phase allowance. The parent retains and reaps its actual process handle. No child is adopted by an old PID; there is no retry, resume, fallback, financial rerun or paid-launch path. A failed, pending, interrupted or invalid product result stops subsequent phases. Local validators still reconstruct provider evidence and economic relationships; the precise scope is **local preparation without a portfolio backtest or paid request**, not broadly “nonfinancial” work.

A successful result establishes only that the three new registrations passed current validators in the observed local operation. It does not complete a model-role cycle, certify data accuracy, create an untouched holdout or establish investment value. Protected eligibility, legacy reconciliation, external restore, unattended readiness and investment validation remain false.

The later paid controller is unimplemented here. It must enforce the remaining allowance from a common 7,200-second cycle start using actual elapsed preparation time; independent timers do not reserve a shared time budget. Current-day model reservations, method-only reviews, new financial work and independent numerical/trace verification remain separate gates. Existing external backup rights/key/account and restore gates continue to apply to unattended operation.

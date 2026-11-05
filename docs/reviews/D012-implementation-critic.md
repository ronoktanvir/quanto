# D012 prototype implementation criticism

The exact prototype library and explicit-pin D011 handoff receive provisional acceptance for reversible software integration. No unresolved implementation blocker remains in the reviewed boundary. This is not production approval: D012's outside design reviews did not dispatch, and policy adoption remains pending. Neither native software checks nor this report can replace those reviews. [Council attempt](D012-council-attempt-1.md) · [Proposed design](../D012_DESIGN.md).

## Scope and evidence

The critic owns this report and ignored scratch only. The producer owns `src/quanto/authority_reattachment.py`, the registry integration and its tests; the lead owns the reviewed minimal D011 process integration and the still-outstanding administrator/controller. The critic inspected the public source in the resident worktree and constructed separate invented temporary databases. All executed checks are `synthetic_fixture` software evidence. No original runtime, credentials, licensed observations, model requests, broker routes or production reattachment were accessed.

The invented historical device values were written into disposable fixture configuration. Every acceptance and reopen used actual filesystem calls, including fresh interpreters. This tests a deliberate mismatch without inventing an observation about the owner's filesystem or patching `stat`.

## Preserved findings

### C1 — database-file maintenance locks blocked SQLite on the target Mac

The first draft placed the shared/exclusive `flock` on `control.sqlite` itself. An independently constructed fixture failed in `apply_reattachment` at `PRAGMA synchronous=FULL` with `database is locked`. A separate minimal SQLite-only reproduction isolated the mechanism: shared flock allowed the pragma but blocked `BEGIN IMMEDIATE`; exclusive flock blocked both. Thus the gate would prevent the repair and ordinary supervisor writes on this Mac.

The producer moved the gate to the existing private control-directory inode. No lockfile or schema was added. The directory's ownership, mode, symlink status, descriptor identity and current path identity are checked. Independent tests then observed successful SQLite commits, actual competing-process exclusion and release, and nested session/registry use. The directory's advisory lock is cooperation enforcement, not protection against privileged path replacement.

The preserved first-draft source observation has attachment SHA-256 `934a225356337fcf12a446c5ecfd0a02d353779898abf48ec3c558528cfc73b5` and registry SHA-256 `3b41762d0209eb269302c965d1b9bfb4f615333e32f1259e48b0be88e1f0c13a`. The producer was still editing the prototype; these identify the captured draft, not an accepted release.

### C2 — incomplete nested payload validation

Code inspection found that the initial request validator accepted nested witness/table structures without validating their complete shape. Its apply path compared full snapshots, but a manually constructed valid-chain v1 event could reach a less strict reopen path. The producer added recursive witness/fingerprint validation, event-count consistency and equality with actual table sets. Independent post-correction probes rejected a malformed witness/request, an omitted table prefix, unknown version/kind and numeric substitutes for Boolean limit flags. The original concern was a source finding; the critic did not execute the malformed-event probe before its correction.

### C3 — fork inherited authority without a child pin

An actual `os.fork` probe demonstrated that a child inherited the parent's active pinned session and successfully called `current_session(root)` and `issue_principal()` without constructing its own explicitly pinned supervisor. This contradicts the intended per-process attachment boundary unless all fork inheritance is expressly excluded by an outer process contract. The critic requested a narrow process-ownership refusal rather than relying silently on an eventual exec-only controller.

The observed fork-gap revision has attachment SHA-256 `010efedc197db54ca8714a5333dc00ff0e571953d77823a7d0152df834b89c8e`, registry SHA-256 `3b41762d0209eb269302c965d1b9bfb4f615333e32f1259e48b0be88e1f0c13a` and test SHA-256 `b5805e3a68de55d438e27eaa8d9840fa72d12d427253a640731f8f1ebf62e5ae`. The producer added a creator-process ID and checks it before path/session/database use. The critic reran an independent actual fork: inherited session lookup, principal issuance and overview all refused `authority_closed`, while the parent still issued a principal. The final producer regression observes the same boundary. C3 is resolved for these public authority paths; a privileged Python caller remains outside the threat model.

## Final independently executed evidence

The critic's separately written fixture/probe program produced 31 expected outcomes at the final source: append-only acceptance with unchanged configuration/schema/research state; actual fresh-process reopen preserving store/principal; missing/wrong pin refusal; synthetic-mode and protected-access refusal; replay refusal; later control growth; malformed request refusal; no original-device fallback; actual competing-process shared gate and control/research SQL writer exclusion plus release; session-lifetime exclusion; child exit before commit preserving the entire old snapshot; child exit after commit leaving one readable exact event and a successful fresh-process reopen; root/control/object/parent symlink and research hardlink refusals; unknown event version/kind, numeric flags and omitted-prefix refusals; and refusal of inherited fork authority with the parent still usable.

The pre-fix reattachment/registry suite passed 139 tests but did not expose the inherited-process defect. At final source, the critic ran the reattachment, registry and strategy-supervisor suites together: **174 passed in 15.58 seconds**, and lint passed for the five changed implementation/test artifacts. This includes unchanged old-row preservation, stale snapshots and witnesses, actual competing writers, unexpected append-side-effect rollback and protected refusals. Passing counts support the specific observations; they are not policy approval.

## Boundary requirements retained

The library performs one control-database append while holding both SQLite writer exclusions in fixed order. It does not implement a distributed transaction, external freshness witness, durable attempt consumption, dispatch permission, child cleanup, receipt publication or production-policy approval. A missing event after failure does not authorize another dispatch. The separate controller must consume its exact attempt before launch and reconcile uncertainty without automatic retry.

Source/interpreter and policy/review digests in a plan are identity pins, not proof that a review happened or that the currently loaded interpreter code matches those files. The outstanding controller must enforce selected source, fresh bytecode, bounded output, deadline and cleanup behavior. SQLite length caps and scoped progress handlers bound database work, including accepted reopening. Scan row/byte/time budgets and finite lock waits still do not preempt arbitrary filesystem I/O; row encoding happens after fetch. The separate controller needs its hard process deadline.

The acceptance snapshot preserves every preexisting research row at the write. Later ordinary research-state changes, such as settling a hold, are allowed; reopening checks research schema, table set and complete event ancestry rather than pretending every materialized research row stays frozen forever. Historical witness hashes remain attributed pins whose supplied prefixes are recomputed, not external custody/freshness proof. Current object contents remain checked at use. Cooperating workers outside the upgraded paths still require an explicit drain/inventory before any real operation.

The original authority remains legacy-unknown. Protected evaluation, unseen evidence, unattended recovery and live execution remain unavailable. The library cannot satisfy the outstanding one-shot administrator/controller, actual outside design criticism or fresh-process production observation. Those are separate gates, not completed milestones.


## D011 helper addendum

The lead added one optional `attachment_event_sha256` parameter and CLI flag to the existing finite supervisor. It is retained in the consumed private intent, validated as an exact lowercase digest before launch, and explicitly passed by the fresh child to `Supervisor`. The helper does not apply an attachment, select a newer event or recover from a missing pin. Its existing source identity covers the public Python roster, including the research-chain helper, as well as the supervisor source.

The critic inspected this delta and ran its 20 process tests as part of the 174-test final run. An exact accepted event reached the real CLI and produced an intentionally invalid request outcome. Missing/wrong pins stopped before CLI execution; a malformed pin stopped before child launch. These observations establish the prototype pin handoff, not a real campaign result or production call. No new helper blocker was identified.

## Exact final artifacts

Review worktree base: `8e40eff6a86bb27b0ba95dbd2ce449e19d8a4f80`, with the following uncommitted implementation bytes independently hashed after the final executed checks. The review attaches to these bytes, not unspecified later edits.

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/authority_reattachment.py` | `25c77d865427483b3fb705532c97a53d17a14d0edfee8c98f95e89ed7808dd46` |
| `src/quanto/evaluation_registry.py` | `3ca6d69da364c37a2e53973dd70a867532d2174e9e78310b78d2c57b9b52cb34` |
| `tests/test_authority_reattachment.py` | `fbec5fed88f40c1c6b6692acfd5cb54c9e102024660fb6067b0bc245b2d09ed0` |
| `operations/strategy_campaign/supervise_step.py` | `8eba085aae7f8f4a54a41972e4cd4a1ac43f990aaefe8676d8b53aabf42b3a8c` |
| `tests/test_strategy_campaign_supervisor.py` | `7f09efc3f97eac82ac4ab002eae3e34d7f8544d76464ed5fe0feb847fe485435` |
| `tests/test_evaluation_registry.py` | `cba80802c40a98c0217ec54b89ebdcae5f05d0142759a7307175330037a2b3c4` |

The independent ignored probe source has SHA-256 `ff1f4201d6ccd0eaf22002aed9bdb6a6e035648949fb2bc3cc5b2705c65f85cd`; its 31-outcome result has SHA-256 `a7f59bfc612c4efa0e3b2b837369ec996f3eb91ef712153149b4dffb2ef337e6`. They contain invented fixtures only and remain under `runtime/d012-critic/`. The two executed defects and the initial payload-validation concern remain preserved above. Separate quality and scope review, outside design criticism and the administration/controller boundary remain distinct acceptance responsibilities.

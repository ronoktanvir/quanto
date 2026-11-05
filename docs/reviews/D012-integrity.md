# D012 access-integrity perspective

Recommend one explicit, audit-bound administrative mapping in the existing control database. Accept only a single D012 transition, with exact evidence binding and fresh-process verification. This restores cooperating development access without certifying freshness or changing research eligibility. The proposal needs tighter selection and concurrency rules before implementation.

## Evidence inspected

Independent source/document review; no runtime, credentials, market data, other D012 advisers, tests, model calls or operational invocation inspected/performed. Read AGENTS.md, CONTEXT, STATUS, ROADMAP, DECISIONS and HANDOFF. Source checkout HEAD was `f18a036f55a5f5ff41fa4ed4db35453bb3c40802`.

- `docs/D012_PROPOSAL.md` SHA-256: `490e1061d66e52d9c7e904134dd9e7c0e71d50532c16f4875a696138ae361779`.
- `src/quanto/evaluation_registry.py` SHA-256: `c69c7de7e66c0d6f8b372304db482bf6d83ad0fe35960e55fc8fa00ac4a4b113`.

The source compares persisted configuration against the current root device/inode before ordinary writable access. It preserves append-only application records through triggers, uses control-database transactions for events, and checks runtime physical identities. `_ACTIVE` and its lock are process-local. Ordinary opening currently does not independently authenticate the complete audit chain. The reported 4,568 control events, 686 research events, intact table prefixes and preserved non-device metadata are lead-attributed observations, not independently repeated findings here.

## Mechanism and exact authority

A table is preferable because its acceptance row and audit event can commit together. A separately pinned receipt alone creates a second authority whose publication can disagree with the database after interruption; use an external retained receipt as corroboration, not an alternative acceptance path. A session-only override avoids schema extension but makes fresh-process continuation depend on carrying a bypass and repeating continuity judgments. That is less auditable for this finite campaign.

Keep every existing row and configuration value, including schema value and `legacy_unknown=True`. Permit only a separately named extension table and its fixed append-only triggers through the explicit administrative operation; ordinary construction must never create or repair them. Define exact allowed pre/post schema fingerprints so adding the extension cannot mask changes to existing tables or triggers.

The sole mapping must bind: store/principal identity; original configuration digest; pre/post schema identities; exact canonical paths; old/new device values; each retained inode/owner/mode; preflight and reviewed-source digests; complete preflight control/research heads and table-state fingerprints; unique attempt identity; and the acceptance audit sequence/hash. The event must bind the canonical mapping payload, while the row identifies that event, without circular hashing.

On opening, absence of the extension permits only the original strict binding. Presence requires its exact schema, exactly one valid mapping, an exact event/payload match and a valid audit chain containing that event. Then only the mapped current device is accepted. Do **not** use the proposal's literal “original binding or an exact accepted mapping” after reattachment: old device numbers can become stale authority. Reject malformed, duplicate, conflicting or unrecognized mapping state even when the original device matches. No wildcard, transitive mapping, newest-timestamp selection, absent-table exception catch or fallback to bootstrap is acceptable. Further device changes need a separately reviewed administrative transition.

## Staleness, concurrency and interruption

A worker inventory is evidence of a moment, not exclusion of later starts. Establish a bounded cooperating-process maintenance gate, drain existing workers, and make opening paths honor that gate. The current process-local `_ACTIVE` cannot supply this guarantee. Preserve the documented application-isolation limits.

After acquiring the gate and database locks in a fixed order, recheck exact frozen heads, configuration, schemas, table fingerprints and physical identities. A control `BEGIN IMMEDIATE` alone does not freeze research or spending stores. Keep the relevant cooperating stores quiescent through verification and commit; any unexplained advancement requires refusal and a new reviewable preflight. Preserve all uncertain effects and holds, not just terminal records.

Append extension DDL, mapping and audit event in one explicit SQLite transaction; avoid helpers that implicitly commit DDL. An exclusive durable attempt record must be created before mutation and must remain consumed after interruption. Lost output is uncertain completion, resolved by read-only inspection of the exact attempt/event, never blind reinvocation. Reopening must verify all old logical rows, budgets, exposure, reservations and consumed controllers unchanged, with only the specified additive evidence present. Capture actual current device/inode identities for subsequent in-process checks.

## Limits and acceptance conditions

Local hash chains and matching prefixes detect inconsistency against retained witnesses; they cannot detect coordinated rollback of the databases and every local witness. No historical volume UUID exists, and measuring one now cannot establish the missing past value. Neither owner confirmation nor an administrative mapping proves absence of rollback. The threat model remains cooperative processes under an owner who controls files and code.

Required independent negative tests include stale preflight, concurrent append/attachment, original-device fallback after acceptance, foreign-store receipt, changed metadata/configuration/schema, orphan mapping/event, replay, duplicate/conflicting mapping, interrupted transaction and lost terminal output. Verify protected acquisition remains refused and legacy exposure remains unknown. Implementation acceptance and outside-model criticism are still pending. Once the reviewed repair succeeds, resume the unchanged finite D011 request; no strategy outcome follows from this repair.

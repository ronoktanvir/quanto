# Local research snapshots

Quanto can capture and inspect an inert local research-store candidate. This preserves a consistent database and its available canonical objects without resuming jobs, resetting budgets or calling external services. It is one component of the accepted [D009 recovery contract](D009_POLICY.md), not a complete disaster-recovery system.

## Library boundary

`quanto.recovery.capture_research_snapshot(source_root, destination, *, limits=Limits())` creates a new private destination outside the entire source root. It refuses an existing destination, unsafe paths, unsupported journal mode, conflicting writers, missing known live references and exceeded limits. A failed generation is retained for diagnosis; callers must not blindly retry or overwrite it.

The source must contain `runtime/research.sqlite` and `data/objects/`. Capture preserves every table and row through SQLite's online backup API. A read transaction precedes a separate writer barrier so a hot rollback journal is refused without recovery modifying the source. Cooperating database/object publishers are serialized; unrelated filesystem actors are outside this application boundary. Committed tombstones remain unavailable and are not resurrected.

`inspect_research_snapshot(snapshot, *, expected_manifest_sha256=None, expected_event_head=None, limits=Limits())` verifies a closed candidate read-only. Pass separately retained expected identities when checking a known generation. The inspector verifies file inventories and digests, database integrity and table state, the event chain and supported database references. It never initializes application state or grants execution authority.

Default bounds are 64 MiB of database bytes, 16 MiB per object, 256 MiB combined payload, 10,000 object entries, 100,000 rows, 8 MiB of manifest, 2 seconds of lock wait and 15 seconds per capture/inspection operation. Callers may lower these bounds, not raise them. There is intentionally no production restore or scheduler command in this increment.

## Meaning of a successful result

A pass means the declared local inventory is internally consistent. The result always reports incomplete typed closure, no full recovery acceptance, no verified off-Mac recovery and no execution authority. Unknown nested document schemas, external runtime audit evidence, legacy artifacts and historical code/dependencies require further work. Conversations/session continuity are excluded. Keys and credentials must remain separate from backup payloads.

An authentic old manifest is still old; a digest from the same archive cannot prove that no newer generation exists. Full external recovery also requires selected-use data rights, encrypted transfer, a key obtainable without this Mac, recoverable account access and a downloaded isolated restore. Unattended effects need additional fencing and external intent/outcome records. See [actual local evidence](reviews/D009-local-capture-actual.md) and the [data-use review](reviews/D009-backup-data-use.md).

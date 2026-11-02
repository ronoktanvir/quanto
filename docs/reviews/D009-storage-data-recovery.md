# D009 data consistency and recovery perspective

**Use a coordinated, encrypted recovery snapshot first; do not promote an ordinary two-database backup into an unattended-research recovery guarantee.** The research database, conversation database, artifact store and operational files have different publication boundaries. A backup must preserve those distinctions, including failed work, unavailable artifacts and uncertain spending.

Reviewer: `/root/d009_data_recovery`, independently briefed on data consistency. This is source inspection and a small synthetic SQLite probe, not implementation acceptance or an actual restore. No actual database, artifact values, credentials or account resources were accessed. No storage was created or data transferred. The lead's reported approximately 10 MB footprint and credential checks are attributed observations, not independently measured here. The proposed 10 GB standard Runpod volume, approximately USD0.70/month, is reasonable capacity for that reported footprint; the separate cost adviser owns pricing verification. The owner's USD50 cumulative storage/setup ceiling does not alter model allowances.

## What the source establishes

`Journal` uses SQLite rollback journaling and full synchronization. Its event verifier checks event ordering and hashes, optionally against an expected external head, but explicitly does not verify arbitrary materialized tables. A database hash, integrity check and event-chain check therefore answer different questions; none substitutes for checking retained reservation, exposure, assignment and dispatch state.

`Provenance` publishes bounded content-addressed files by writing, syncing and atomically linking a new object. Existing object bytes must match their digest. Tombstoning blocks future retrieval while retaining the identity and reason. `purge` records that tombstone, then unlinks the file outside the tombstone transaction. A backup that snapshots the database and later copies objects can race with a purge even if every copied file has a correct hash.

`Conversations.chat` commits a pending turn in `conversations.sqlite`, calls the provider against `research.sqlite`, and finally commits its response in the conversation database. The two databases do not share a transaction. A completed chat copy paired with an older research copy could lose the corresponding cost record. The existing pause file is checked at provider entry; it does not drain a call already past that check and is not a universal barrier for research or council processes.

The five-minute website snapshot is status evidence. Its atomic JSON publication and capture lock do not snapshot either database or the artifact store. Restoring that file must preserve its original timestamps and label it historical, not imply a fresh health observation.

## First backup boundary

Use a new private staging directory for each generation and a manifest describing the exact capture scope. For the first manual operation, coordinate a bounded no-effect/no-purge window with the lead: prevent new model/research/council dispatches, wait for known active requests and local evidence writers to finish or remain explicitly uncertain, and prevent artifact purges until copying ends. This coordination must be observed, not inferred from the website being ready. It does not require discarding or settling any existing uncertain hold.

Create each database snapshot through SQLite's online backup API, close and sync the destination, then hash that destination. Do not use `cp` on a live database or copy a main file while guessing whether journal sidecars matter. The API creates a database snapshot while accommodating other connections; it does not promise an atomic snapshot of two independent databases or associated files. [SQLite backup documentation](https://www.sqlite.org/backup.html), [Python backup API](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup).

For a certified coordinated generation, the no-effect/no-purge window covers both database captures, object inventory and relevant evidence-file copying. If the implementation cannot establish that window, it may produce individually consistent recovery copies with separate capture times, but must label the pair uncoordinated and refuse automatic operational activation after restore. Mere absence of a newly observed event does not establish quiescence.

For this small initial store, copying all valid, non-tombstoned content-addressed `.bin` objects is simpler than inventing a partial reachability parser. Exclude temporary files and reject symlinks, special files, invalid names and digest mismatches. Record the complete copied inventory privately. Then validate the known typed references from the captured database and nested manifests against that inventory. An arbitrary 64-character hash is not necessarily an object reference: code and original-request hashes also occur in records. Unknown reference-bearing schemas require explicit support or an incomplete-coverage label.

Preserve tombstone rows and their original reasons, but do not copy tombstoned payloads or silently recreate them. A reference legitimately unavailable at capture remains unavailable on restore; an unexpectedly missing live dependency prevents an artifact-complete label. Older remote generations may still contain an artifact later tombstoned locally, so the retention plan must track affected generations and explicit removal requirements. Encryption does not itself implement erasure.

## Explicit payload and secret boundaries

The manifest should allowlist database snapshots, the checked object inventory, exact source revision plus required uncommitted source evidence, and individually selected historical requests, receipts and verification scripts. A Git bundle can preserve committed implementation history without transporting `.git` credentials/configuration. Runtime evidence scripts are data to preserve, never instructions to execute during restore. Capture changing files with stable-file checks or fail that generation.

Do not recursively upload the workspace, home directory or all of `runtime`. Exclude `.env` and its variants, cloud credentials, encryption identities, SSH material, temporary files, process locks and live-service registration. Logs and arbitrary console output need a separate allowlist and secret review. Retain operational restart/diagnosis history as historical evidence; do not reset circuits or execute restored service state.

There is a concrete conversation exception to a claim that backups contain no secrets: `conversations.sqlite.sessions` stores CSRF tokens, and user message text can contain arbitrary pasted content. For a credential-free initial archive, make a separately labeled derivative conversation snapshot that invalidates session/CSRF authentication material while retaining conversation, turn and inbox evidence. Record its transformation and original local snapshot hash; never call it an exact database-byte copy. Do not silently redact the live database. If arbitrary conversation text has not passed a local secret review, omit that optional payload and record the omission rather than promise it is secret-free. The research ledger and paid-request history remain mandatory. Encryption protects all included private content but does not establish absence of credentials.

Keep the manifest containing filenames, identities, journal head and private counts inside encryption. Outside receipts need only a generation identifier, ciphertext size/digest, storage identity, completion state and safe timestamps. Preserve the decryption key separately from the volume and test that the recovery copy of the key works; a key stored only on this Mac leaves total-Mac-loss recovery unproved.

## Restore verification and activation boundary

Upload ciphertext under a unique generation name, retrieve it into a different empty directory, verify the downloaded ciphertext digest, decrypt, and validate every allowed path and manifest digest before extraction/use. Reject absolute paths, traversal, links, unexpected files and resource limits exceeded. A successful `PUT`, matching ETag or listing is not an end-to-end restore test.

Open restored databases read-only for SQLite integrity and foreign-key checks. Verify the event chain and the captured head/count against the manifest, then compare complete sensitive state tables or canonical state digests with the captured snapshot: all reservation days/states/amounts, purpose allocations, dispatch identities, workflow intents/effects/fences, failures, exposure and consumption records. Preserve pending and uncertain states as they were. Do not free prior-day holds, clear leases, recycle allocations or replay requests because the destination is a new directory. Where the event chain and materialized rows disagree, stop for investigation; do not repair from a preferred source automatically.

The first restore test must have no provider/broker credentials, no network-capable worker launch, no dashboard/supervisor launch and no runner execution. Constructors such as `Journal` and `Provenance` create schema/triggers, so direct read-only validation is preferable for the initial byte-preserving audit; any deeper application validation should use a disposable second copy and account for its mutations. Conversation sessions must be newly authenticated before any eventual UI activation.

A restored archive demonstrates recovery only to its captured boundary. Future unattended operation needs externally retained pre-dispatch intent/full reservation and post-effect state, a single-writer/fencing design, and verified freshness before the next irreversible effect. A same-account mutable remote latest pointer cannot establish resistance to a privileged remote writer. That trust-model decision remains separate from this backup increment and from completing D008 scheduling/restore.

## Evidence and next gates

A temporary invented SQLite database was copied using Python `Connection.backup`; integrity passed, an invented uncertain reservation remained unchanged in the copy, and a subsequent source update did not alter that copy. This probes basic snapshot behavior only. It does not test the project's full schema, coordinated two-database capture, object closure, interruption, encryption, upload or actual restore.

Required implementation checks are bounded capture under concurrent writes, deliberate purge/missing-object refusal, retained tombstone semantics, cross-database skew rejection or explicit labeling, secret exclusions, unsafe-archive rejection, corrupt/incomplete upload refusal, and a downloaded isolated restore preserving all uncertain/consumed state. Separate implementation criticism, execution quality and scope acceptance must follow. No workflow acceptance, protected-evaluation readiness, unattended dispatch or live authority follows from this design report.

Inspected source SHA-256 identities:

| Source | SHA-256 |
| --- | --- |
| `ledger.py` | `29c3f14bdae924b4d369b49b59c3ec7e5079810d76e55992fa1800d49a3da6cf` |
| `provenance.py` | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |
| `conversations.py` | `a704d127f14df9dc6d6757f6182c899e875d58ea46292666b53efeb2ec46a8a3` |
| `snapshots.py` | `25fea03c4bcb7b63bd44457936757f9ae966f8b51ed6286f91691c473736eb1b` |
| `provider.py` | `5f4f214d079bd4a17ddc3049163d5a3bfc9acd8ba2508a3dfe2f5ad5c4c0ace0` |
| `operations.py` | `65004d79a24fffb83b6d2485b34bd3b181aa425c41de501760bf0560264c24bc` |

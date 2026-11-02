# Submission and artifact provenance

`quanto.provenance.Provenance` records bounded acquisition and research requests before semantic validation and stores exact artifact bytes by SHA-256 identity. It provides receipts for cooperating local clients. It does not certify provider accuracy, data rights, historical availability, a complete warehouse, an unexposed holdout, or an investment result.

## Request and outcome contract

Use one `Provenance(root)` context manager per worker or thread. The root directory must already exist. The object exposes `journal`, the existing `Journal` on `runtime/research.sqlite`, so callers can coordinate their own append-only metadata without creating a second research ledger.

Call `begin(kind, request)` before parsing or validating the operation, fetching data, or running an experiment. `kind` is a 1–64 character lowercase identifier matching `[a-z][a-z0-9_.:-]{0,63}`; it is not a fixed operation enum. `request` is either a UTF-8 string of at most 64 KiB, hashed exactly as supplied, or a JSON-serializable dictionary whose bounded canonical representation is hashed. A malformed JSON string is still a valid submission envelope. Arbitrary submitted content is never stored: the record contains its digest, byte count, encoding, kind, identity, and start time.

The bounded envelope is a preflight boundary. An unsupported kind, oversized request, invalid Unicode, nonfinite number, or unserializable object is rejected before a submission is written. Callers must not describe such inputs as journaled attempts. A request hash is an identity, not encryption; predictable low-entropy inputs may be guessed from their hashes. Avoid credentials even in requests that are only hashed.

`finish(submission_id, status, details)` accepts exactly one terminal outcome: `success`, `invalid`, `failed`, or `interrupted`. The details are a finite JSON object of at most 64 KiB. Callers must select safe metadata and fixed error codes rather than persisting arbitrary input, credentials, provider error bodies, or exception text. This generic storage layer cannot determine whether arbitrary metadata is a secret.

Success details require a nonempty `artifact_refs` list of at most 128 unique SHA-256 strings. Every direct reference must resolve to an existing, untombstoned, hash-verified artifact before the outcome is committed. Other keys, such as `receipt_sha256` or `manifest_sha256`, are descriptive metadata; they do not independently cause reference validation. References inside an artifact are not traversed automatically. A caller that needs a complete reference graph must validate it and include the necessary direct references itself.

Each submission and terminal outcome is committed with its event in one journal transaction. A failed event write rolls back that record. A terminal receipt establishes what was observed when it was committed; it does not promise that every artifact will remain available forever.

`finish` joins an existing `store.journal._transaction()` through a savepoint when one is active; otherwise it opens its own transaction. A failed finish rolls back its own outcome and event even if the outer caller handles that exception. This also allows an integration to commit a submission outcome and its associated experiment outcome atomically; the integration must roll back its outer transaction when any part of that combined operation fails. `begin` still owns its transaction and must be called before entering a later publication transaction. Files already published to the object store are not removed if a database transaction rolls back; they remain unclaimed artifacts rather than successful receipts.

`get_submission(id)` returns one receipt. `list_submissions(kind=None, limit=100, status=None)` returns newest submissions first, including pending ones. The status filter accepts the four terminal statuses and `pending`; kind and status filters are applied before the 1–1000 row limit. Returned records include `submission_id`, `kind`, `request_sha256`, `request_bytes`, `request_encoding`, `started_at`, `status`, `details`, and `finished_at`. Pending records have no terminal details or finish time.

Acquisition submissions are separate from the journal's experiment fingerprints and experiment attempts. A request to acquire bytes does not itself establish a registered experiment or its specification, data, code, evidence kind, or assumptions. The research layer remains responsible for those identities.

## Artifact storage and manifests

`put_bytes(raw)` accepts bytes up to 16 MiB and returns their lowercase SHA-256 digest. `read_bytes(digest)` verifies the exact bytes against that identity on every read. Files live at `data/objects/<digest>.bin`, outside version control. New directories are private (`0700`), and new objects and the new journal file are private (`0600`). Existing directory permissions are not silently changed.

Writes use a private temporary file, flush and sync its bytes, and publish with an atomic no-replace link in the same directory. An existing digest path must contain valid matching bytes; corrupt files are rejected rather than overwritten. Publication is serialized against tombstones through the shared journal. Object paths use validated digest names and directory descriptors; symlinks, directories, and special files at object paths are refused. The implementation targets the local POSIX filesystem used by Quanto, not an arbitrary remote object store or Windows filesystem.

`put_json(value)` writes finite canonical UTF-8 JSON of at most 1 MiB. `read_json(digest)` first verifies the artifact bytes and then rejects duplicate object keys, malformed UTF-8, trailing content, nonfinite numbers, and oversized JSON. Hash-valid bytes are not necessarily valid JSON.

Manifests are ordinary JSON artifacts, with schemas and validation owned by their consumer. For example, a provider receipt can identify exact response pages, normalized data, source, retrieval time, request assumptions, and evidence kind. This module does not fill in missing provenance or infer that a manifest describes a complete or point-in-time dataset.

An example using a synthetic artifact:

```python
from pathlib import Path
from quanto.provenance import Provenance

with Provenance(Path("/existing/private/project")) as store:
    submission = store.begin("dataset_registration", '{"source":"synthetic_fixture"}')
    manifest = store.put_json({"source": "fixture", "evidence_kind": "synthetic_fixture"})
    store.finish(submission, "success", {
        "manifest_sha256": manifest,
        "artifact_refs": [manifest],
    })
```

## Interrupted work and explicit removal

A process failure can leave a pending submission, an artifact with no completed receipt, or an orphan `.pending-*` file. Pending means the outcome is unknown; reopening the store does not mark it failed, claim recovery, or retry external work. An operator or higher-level reconciler must gather evidence before recording an explicit terminal outcome. There is no automatic orphan cleanup.

`tombstone(digest, reason)` explicitly blocks future reads and reuse through this API while retaining the digest and reason in the journal. Reasons are fixed codes: `accidental_secret`, `rights_request`, `operator_requested`, and `invalid_artifact`. Repeating a tombstone preserves its first recorded reason. An already-running reader or an external copy cannot be recalled.

`purge(digest, reason)` first commits the tombstone, then removes the addressed regular object file and records the observed removal. It refuses unexpected path types. If removal fails or the process exits, the tombstone remains in force; there is no automatic retry or claim that removal completed. Repeating a successful purge records that the addressed file is absent. Historical submission receipts retain their original outcomes and hashes after removal.

These APIs are an explicit, auditable removal path, not secure erasure. They do not remove backups, copies outside the store, provider copies, filesystem snapshots, or orphan temporary files. They do not remove accidental secrets from an already-written outcome or event. Callers must prevent such metadata from entering the journal; any incident affecting journal contents needs a separate reviewed retention and remediation procedure. None of the tests or examples performs deletion in the actual project runtime.

## Trust and verification limits

Ordinary SQL updates and deletes are blocked by triggers on submission, outcome, and tombstone tables. The shared event hash chain supplies tamper evidence for event contents; it is not immutable storage and does not automatically compare every application table to its events. An owner who can rewrite SQLite, drop triggers, alter local files, or replace a complete chain remains outside this protection. Detecting a rewritten chain or truncated suffix needs a trusted external checkpoint and backups.

The supplied root and its ancestors must be trusted. Known SQLite paths are checked for regular files before opening, but SQLite requires a pathname; these checks do not defeat a malicious local owner racing path replacement. Directory descriptors and no-follow object access prevent routine traversal mistakes without turning the store into an authorization boundary.

Tests use temporary synthetic fixtures only. They check request privacy, pending and terminal transitions, transaction rollback, filtering, strict JSON, content verification, concurrent publication, ordinary append-only protections, path rejection, and explicit removal. They validate storage behavior, not historical market quality or strategy performance.

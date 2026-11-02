"""Private content identities and append-only acquisition/submission receipts.

This module records cooperating clients. It does not establish data rights,
provider truth, historical availability, or protection against the local owner.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
from typing import Any
import uuid

from quanto.ledger import Journal, LedgerError, MAX_JSON_BYTES, canonical_json

MAX_REQUEST_BYTES = 64 * 1024
MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
MAX_DETAILS_BYTES = 64 * 1024
MAX_ARTIFACT_REFS = 128
TERMINAL_STATUSES = frozenset({"success", "invalid", "failed", "interrupted"})
TOMBSTONE_REASONS = frozenset(
    {"accidental_secret", "rights_request", "operator_requested", "invalid_artifact"}
)
_IDENTIFIER = re.compile(r"[a-z][a-z0-9_.:-]{0,63}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SUBMISSION = re.compile(r"[0-9a-f]{32}\Z")


class ProvenanceError(LedgerError):
    """A bounded, non-secret provenance or storage failure."""


def _digest(value: object) -> str:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ProvenanceError("Artifact identity must be a lowercase SHA-256 digest")
    return value


def _kind(value: object) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ProvenanceError("Submission kind must be a bounded identifier")
    return value


def _submission(value: object) -> str:
    if not isinstance(value, str) or not _SUBMISSION.fullmatch(value):
        raise ProvenanceError("Invalid submission identity")
    return value


def _strict_json(raw: bytes) -> Any:
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("Non-finite JSON number")

    try:
        if len(raw) > MAX_JSON_BYTES:
            raise ValueError("Oversized JSON")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
        canonical_json(value)  # Also rejects overflow such as 1e999 and excessive nesting.
        return value
    except (ValueError, UnicodeError, RecursionError, OverflowError, TypeError):
        raise ProvenanceError("Artifact is not bounded strict UTF-8 JSON") from None


_SCHEMA = """
CREATE TABLE IF NOT EXISTS provenance_submissions (
 submission_id TEXT PRIMARY KEY, kind TEXT NOT NULL, request_sha256 TEXT NOT NULL,
 request_bytes INTEGER NOT NULL, request_encoding TEXT NOT NULL, started_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS provenance_outcomes (
 submission_id TEXT PRIMARY KEY REFERENCES provenance_submissions(submission_id),
 status TEXT NOT NULL CHECK(status IN ('success','invalid','failed','interrupted')),
 details TEXT NOT NULL, finished_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS artifact_tombstones (
 digest TEXT PRIMARY KEY, reason TEXT NOT NULL, tombstoned_at TEXT NOT NULL
);
"""


class Provenance:
    """One instance per worker/thread; use ``with Provenance(root) as store``.

    ``begin`` stores only a request digest, byte count and encoding. For strings,
    the digest covers exact UTF-8 bytes; dictionaries use canonical JSON. Semantic
    validation and network/engine work belong after ``begin``. Oversized or
    unencodable envelopes are rejected at this bounded API boundary.

    ``finish`` requires success details to include nonempty ``artifact_refs``.
    These are verified direct references, not a recursively validated graph.
    It joins an active journal transaction with a savepoint when present;
    otherwise it owns its short transaction.
    Other details must be caller-allowlisted safe metadata; do not put credentials
    or raw provider errors in them. Interrupted work remains pending until an
    explicit, evidence-based terminal outcome is supplied. No automatic retry.
    """

    def __init__(self, root: Path):
        self.root = Path(root).absolute()
        self._root_fd = self._runtime_fd = self._data_fd = self._objects_fd = None
        self.journal: Journal | None = None
        try:
            self._root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            self._runtime_fd = self._directory(self._root_fd, "runtime")
            self._data_fd = self._directory(self._root_fd, "data")
            self._objects_fd = self._directory(self._data_fd, "objects")
            # SQLite needs a pathname. Check its known files before handing it
            # to Journal; this is not a defense against an owner racing paths.
            for name in (
                "research.sqlite",
                "research.sqlite-journal",
                "research.sqlite-wal",
                "research.sqlite-shm",
            ):
                try:
                    info = os.stat(name, dir_fd=self._runtime_fd, follow_symlinks=False)
                    if not stat.S_ISREG(info.st_mode):
                        raise ProvenanceError("Journal storage must use regular local files")
                except FileNotFoundError:
                    pass
            try:
                fd = os.open(
                    "research.sqlite",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=self._runtime_fd,
                )
                os.close(fd)
            except FileExistsError:
                pass
            self.journal = Journal(self.root / "runtime" / "research.sqlite")
            self.journal.connection.executescript(_SCHEMA)
            for table in ("provenance_submissions", "provenance_outcomes", "artifact_tombstones"):
                for operation in ("UPDATE", "DELETE"):
                    self.journal.connection.execute(
                        f"CREATE TRIGGER IF NOT EXISTS no_{operation.lower()}_{table} "
                        f"BEFORE {operation} ON {table} BEGIN "
                        "SELECT RAISE(ABORT, 'append-only record'); END"
                    )
        except (OSError, sqlite3.Error, ValueError):
            self.close()
            raise ProvenanceError("Provenance storage is unavailable or unsafe") from None

    @staticmethod
    def _directory(parent: int, name: str) -> int:
        try:
            os.mkdir(name, mode=0o700, dir_fd=parent)
        except FileExistsError:
            pass
        return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)

    def __enter__(self) -> Provenance:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        if self.journal is not None:
            self.journal.close()
            self.journal = None
        for name in ("_objects_fd", "_data_fd", "_runtime_fd", "_root_fd"):
            fd = getattr(self, name, None)
            if fd is not None:
                os.close(fd)
                setattr(self, name, None)

    def _open(self) -> Journal:
        if self.journal is None:
            raise ProvenanceError("Provenance storage is closed")
        return self.journal

    def begin(self, kind: str, request: dict | str) -> str:
        journal = self._open()
        kind = _kind(kind)
        try:
            if isinstance(request, str):
                raw, encoding = request.encode("utf-8"), "utf8_text"
            elif isinstance(request, dict):
                raw, encoding = canonical_json(request).encode("utf-8"), "canonical_json"
            else:
                raise ValueError("Unsupported request envelope")
            if len(raw) > MAX_REQUEST_BYTES:
                raise ValueError("Oversized request envelope")
        except (ValueError, UnicodeError, RecursionError, OverflowError, TypeError):
            raise ProvenanceError("Request must be bounded UTF-8 text or a JSON object") from None
        identity = uuid.uuid4().hex
        record = {
            "submission_id": identity,
            "kind": kind,
            "request_sha256": hashlib.sha256(raw).hexdigest(),
            "request_bytes": len(raw),
            "request_encoding": encoding,
        }
        with journal._transaction():
            now = journal._now()
            journal.connection.execute(
                "INSERT INTO provenance_submissions VALUES (?,?,?,?,?,?)",
                (*record.values(), journal._stamp(now)),
            )
            journal._event("submission_started", record, now)
        return identity

    def finish(self, submission_id: str, status: str, details: dict) -> None:
        journal = self._open()
        _submission(submission_id)
        if not isinstance(status, str) or status not in TERMINAL_STATUSES:
            raise ProvenanceError("Unsupported submission outcome")
        if not isinstance(details, dict):
            raise ProvenanceError("Outcome details must be a JSON object")
        try:
            encoded = canonical_json(details)
            if len(encoded.encode("utf-8")) > MAX_DETAILS_BYTES:
                raise ValueError("Oversized outcome")
        except (ValueError, UnicodeError, RecursionError, OverflowError, TypeError):
            raise ProvenanceError("Outcome details must be bounded finite JSON") from None
        refs = details.get("artifact_refs", [])
        if (
            not isinstance(refs, list)
            or len(refs) > MAX_ARTIFACT_REFS
            or (status == "success" and not refs)
        ):
            raise ProvenanceError("Success needs bounded verified artifact_refs")
        for digest in refs:
            _digest(digest)
        if len(set(refs)) != len(refs):
            raise ProvenanceError("Artifact references must be unique")
        with self._finish_transaction(journal):
            if (
                journal.connection.execute(
                    "SELECT 1 FROM provenance_submissions WHERE submission_id=?", (submission_id,)
                ).fetchone()
                is None
            ):
                raise ProvenanceError("Unknown submission")
            if (
                journal.connection.execute(
                    "SELECT 1 FROM provenance_outcomes WHERE submission_id=?", (submission_id,)
                ).fetchone()
                is not None
            ):
                raise ProvenanceError("Submission already has a terminal outcome")
            for digest in refs:
                self.read_bytes(digest)
            now = journal._now()
            journal.connection.execute(
                "INSERT INTO provenance_outcomes VALUES (?,?,?,?)",
                (submission_id, status, encoded, journal._stamp(now)),
            )
            journal._event(
                "submission_finished",
                {"submission_id": submission_id, "status": status, "details": details},
                now,
            )

    @staticmethod
    @contextmanager
    def _finish_transaction(journal):
        if not journal.connection.in_transaction:
            with journal._transaction():
                yield
            return
        savepoint = "provenance_finish_" + uuid.uuid4().hex
        journal.connection.execute(f"SAVEPOINT {savepoint}")
        try:
            yield
        except BaseException:
            journal.connection.execute(f"ROLLBACK TO {savepoint}")
            journal.connection.execute(f"RELEASE {savepoint}")
            raise
        else:
            journal.connection.execute(f"RELEASE {savepoint}")

    def get_submission(self, submission_id: str) -> dict:
        _submission(submission_id)
        rows = (
            self._open()
            .connection.execute(
                "SELECT s.*, o.status, o.details, o.finished_at FROM provenance_submissions s "
                "LEFT JOIN provenance_outcomes o USING (submission_id) WHERE s.submission_id=?",
                (submission_id,),
            )
            .fetchall()
        )
        if not rows:
            raise ProvenanceError("Unknown submission")
        return self._record(rows[0])

    @staticmethod
    def _record(row) -> dict:
        value = dict(row)
        value["status"] = value["status"] or "pending"
        value["details"] = _strict_json(value["details"].encode()) if value["details"] else None
        return value

    def list_submissions(
        self, kind: str | None = None, limit: int = 100, status: str | None = None
    ) -> list[dict]:
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ProvenanceError("Submission limit must be between 1 and 1000")
        clauses, values = [], []
        if kind is not None:
            clauses.append("s.kind=?")
            values.append(_kind(kind))
        if status is not None:
            if not isinstance(status, str) or status not in TERMINAL_STATUSES | {"pending"}:
                raise ProvenanceError("Unsupported submission status filter")
            clauses.append("o.status IS NULL" if status == "pending" else "o.status=?")
            if status != "pending":
                values.append(status)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        rows = (
            self._open()
            .connection.execute(
                "SELECT s.*, o.status, o.details, o.finished_at FROM provenance_submissions s "
                f"LEFT JOIN provenance_outcomes o USING (submission_id) {where} "
                "ORDER BY s.started_at DESC,s.rowid DESC LIMIT ?",
                (*values, limit),
            )
            .fetchall()
        )
        return [self._record(row) for row in rows]

    def _available(self, digest: str) -> None:
        _digest(digest)
        if (
            self._open()
            .connection.execute("SELECT 1 FROM artifact_tombstones WHERE digest=?", (digest,))
            .fetchone()
            is not None
        ):
            raise ProvenanceError("Artifact has been tombstoned")

    @contextmanager
    def _blob(self, digest: str):
        fd = os.open(
            digest + ".bin", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self._objects_fd
        )
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_ARTIFACT_BYTES:
                raise ProvenanceError("Artifact storage is unsafe or exceeds its bound")
            with os.fdopen(fd, "rb", closefd=False) as source:
                yield source
        finally:
            os.close(fd)

    def read_bytes(self, digest: str) -> bytes:
        self._available(digest)
        try:
            with self._blob(digest) as source:
                raw = source.read(MAX_ARTIFACT_BYTES + 1)
            if len(raw) > MAX_ARTIFACT_BYTES or hashlib.sha256(raw).hexdigest() != digest:
                raise ProvenanceError("Artifact bytes do not match their identity")
            return raw
        except OSError:
            raise ProvenanceError("Artifact is missing, unavailable or unsafe") from None

    def put_bytes(self, raw: bytes) -> str:
        if not isinstance(raw, bytes) or len(raw) > MAX_ARTIFACT_BYTES:
            raise ProvenanceError("Artifact must be bounded bytes")
        journal = self._open()
        # Serialize publication against tombstones so a cooperating writer
        # cannot recreate a physically purged object after its tombstone.
        if journal.connection.in_transaction:
            return self._publish(raw)
        with journal._transaction():
            return self._publish(raw)

    def _publish(self, raw: bytes) -> str:
        digest = hashlib.sha256(raw).hexdigest()
        self._available(digest)
        name, temporary = digest + ".bin", ".pending-" + uuid.uuid4().hex
        try:
            try:
                os.stat(name, dir_fd=self._objects_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                self.read_bytes(digest)
                return digest
            fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=self._objects_fd,
            )
            with os.fdopen(fd, "wb") as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            try:
                # link is an atomic no-replace publication within this directory.
                os.link(
                    temporary,
                    name,
                    src_dir_fd=self._objects_fd,
                    dst_dir_fd=self._objects_fd,
                    follow_symlinks=False,
                )
            except FileExistsError:
                self.read_bytes(digest)
            os.fsync(self._objects_fd)
            self._available(digest)
            return digest
        except OSError:
            raise ProvenanceError("Artifact could not be stored safely") from None
        finally:
            try:
                os.unlink(temporary, dir_fd=self._objects_fd)
            except FileNotFoundError:
                pass

    def put_json(self, value: Any) -> str:
        try:
            raw = canonical_json(value).encode("utf-8")
        except (ValueError, UnicodeError, RecursionError, OverflowError, TypeError):
            raise ProvenanceError("Value must be bounded finite JSON") from None
        return self.put_bytes(raw)

    def read_json(self, digest: str) -> Any:
        return _strict_json(self.read_bytes(digest))

    def tombstone(self, digest: str, reason: str) -> None:
        """Explicitly block retrieval/reuse while retaining only identity and reason."""
        _digest(digest)
        if not isinstance(reason, str) or reason not in TOMBSTONE_REASONS:
            raise ProvenanceError("Unsupported tombstone reason")
        journal = self._open()
        with journal._transaction():
            if (
                journal.connection.execute(
                    "SELECT 1 FROM artifact_tombstones WHERE digest=?", (digest,)
                ).fetchone()
                is None
            ):
                now = journal._now()
                journal.connection.execute(
                    "INSERT INTO artifact_tombstones VALUES (?,?,?)",
                    (digest, reason, journal._stamp(now)),
                )
                journal._event("artifact_tombstoned", {"digest": digest, "reason": reason}, now)

    def purge(self, digest: str, reason: str) -> None:
        """Explicit local removal, never automatic; not secure erasure of other copies."""
        self.tombstone(digest, reason)
        removed = False
        try:
            try:
                info = os.stat(digest + ".bin", dir_fd=self._objects_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                if not stat.S_ISREG(info.st_mode):
                    raise ProvenanceError("Refusing to purge an unexpected artifact path")
                os.unlink(digest + ".bin", dir_fd=self._objects_fd)
                os.fsync(self._objects_fd)
                removed = True
        except OSError:
            raise ProvenanceError(
                "Artifact is blocked but local removal did not complete"
            ) from None
        self._open().append_event("artifact_purge_observed", {"digest": digest, "removed": removed})

"""Inert local research-store capture candidates, never execution or full recovery.

Only cooperating SQLite/object writers are serialized. External side effects,
hostile filesystem owners, nested evidence closure and external audit files are
outside this first version. No credentials, application constructors or network.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time
from typing import Any

FORMAT = "research_state_offline_v1"
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,79}\Z")
OBJECT = re.compile(r"([0-9a-f]{64})\.bin\Z")
PENDING = re.compile(r"\.pending-[0-9a-f]{32}\Z")
OMISSIONS = ["conversations_and_sessions", "external_runtime_audits_and_council_receipts",
             "legacy_synthetic_artifacts", "historical_source_and_dependencies",
             "configuration_credentials_and_recovery_keys", "nested_typed_closure"]


class RecoveryError(ValueError):
    """Only fixed reason codes; never private record contents or SQL diagnostics."""


@dataclass(frozen=True)
class Limits:
    database_bytes: int = 64 * 1024 * 1024
    object_bytes: int = 16 * 1024 * 1024
    total_bytes: int = 256 * 1024 * 1024
    objects: int = 10_000
    rows: int = 100_000
    manifest_bytes: int = 8 * 1024 * 1024
    lock_seconds: float = 2.0
    seconds: float = 15.0


def _need(condition, code):
    if not condition:
        raise RecoveryError(code)


def _bounds(limits):
    _need(type(limits) is Limits, "invalid_limits")
    for name in ("database_bytes", "object_bytes", "total_bytes", "objects", "rows", "manifest_bytes"):
        _need(type(getattr(limits, name)) is int and 0 < getattr(limits, name) <= getattr(Limits(), name), "invalid_limits")
    for name in ("lock_seconds", "seconds"):
        value = getattr(limits, name)
        _need(type(value) in (int, float) and 0 < value <= getattr(Limits(), name), "invalid_limits")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _parse(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            _need(key not in result, "duplicate_json_key")
            result[key] = value
        return result
    def invalid(_):
        raise RecoveryError("invalid_json")
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
        _json(value)
        return value
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise RecoveryError("invalid_json") from None


def _tick(deadline):
    _need(time.monotonic() < deadline, "capture_deadline")


def _path(path):
    path = Path(path).absolute()
    _need(not any(part in {".", ".."} for part in path.parts), "unsafe_path")
    _need(not any(part.is_symlink() for part in (path, *path.parents)), "symlink_path")
    return path


def _directory(path, private=False):
    info = path.lstat()
    _need(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid(), "unsafe_directory")
    _need(not info.st_mode & 0o022 and (not private or stat.S_IMODE(info.st_mode) == 0o700), "directory_permissions")


def _file_info(info, maximum, private=False):
    _need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid()
          and 0 <= info.st_size <= maximum and not info.st_mode & 0o022
          and (not private or stat.S_IMODE(info.st_mode) == 0o600), "unsafe_file")


def _read(path, maximum, *, private=False):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as source:
        before = os.fstat(source.fileno())
        _file_info(before, maximum, private)
        raw = source.read(maximum + 1)
        after = os.fstat(source.fileno())
        current = path.lstat()
        _need(len(raw) <= maximum and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
              == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
              == (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns), "file_changed")
        return raw


def _write(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())


def _sync(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _connect(path, mode, deadline, *, timeout=0, immutable=False):
    db = sqlite3.connect(path.as_uri() + "?mode=" + mode + ("&immutable=1" if immutable else ""),
                         uri=True, timeout=timeout, isolation_level=None)
    # Some supported CPython builds omit the extension-loading API entirely.
    # Never enable it; default-disabled builds still get the SQL denial below.
    disable_extensions = getattr(db, "enable_load_extension", None)
    if disable_extensions is not None:
        disable_extensions(False)
    db.execute("PRAGMA trusted_schema=OFF")
    db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
    allowed_pragmas = {"table_info", "integrity_check", "foreign_key_check", "journal_mode"}
    def authorize(action, arg1, arg2, _database, _source):
        if action in {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_TRANSACTION}:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_FUNCTION and arg2 not in {"load_extension"}:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_PRAGMA and arg1 in allowed_pragmas and (arg1 == "table_info" or arg2 is None):
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    db.set_authorizer(authorize)
    return db


def _value(value):
    if value is None:
        return ["null"]
    if isinstance(value, bytes):
        return ["blob", base64.b64encode(value).decode()]
    if isinstance(value, float):
        return ["float", value.hex()]
    return ["integer" if isinstance(value, int) else "text", value]


def _audit(db, limits, deadline):
    _tick(deadline)
    _need(db.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "database_integrity")
    _need(db.execute("PRAGMA foreign_key_check").fetchone() is None, "foreign_key_violation")
    schema = db.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name").fetchall()
    _need(len(schema) <= 1000, "schema_limit")
    _need(not any(kind == "view" or (sql and "VIRTUAL TABLE" in sql.upper()) for kind, _, _, sql in schema), "unsupported_active_schema")
    tables, total, unknown = {}, 0, []
    for kind, name, _, _ in schema:
        if kind != "table":
            continue
        _need(NAME.fullmatch(name) is not None, "unsafe_table_name")
        columns = [row[1] for row in db.execute('PRAGMA table_info("' + name + '")')]
        if tuple(columns) != KNOWN_COLUMNS.get(name):
            unknown.append(name)
        row_hashes = []
        for row in db.execute('SELECT * FROM "' + name + '"'):
            _tick(deadline)
            total += 1
            _need(total <= limits.rows, "row_limit")
            row_hashes.append(_sha(_json([_value(value) for value in row])))
        tables[name] = {"rows": len(row_hashes), "columns": columns,
                        "state_sha256": _sha(_json(sorted(row_hashes)))}
    _need("events" in tables and "events" not in unknown, "journal_schema_required")
    previous, count = "0" * 64, 0
    for row in db.execute("SELECT id,occurred_at,kind,payload,previous_hash,event_hash FROM events ORDER BY id"):
        _tick(deadline)
        count += 1
        event_id, occurred_at, kind, payload, prior, observed = row
        expected = _sha(_json({"id": event_id, "occurred_at": occurred_at, "kind": kind,
                               "payload": _parse(payload), "previous_hash": previous}))
        _need(event_id == count and prior == previous and observed == expected, "event_chain_invalid")
        previous = observed
    return {"schema_sha256": _sha(_json(schema)), "tables": tables, "unknown_schema_tables": unknown,
            "events": {"count": count, "head": previous}}


DIRECT_REFS = {
    "explorer_datasets": ("manifest_sha256",), "explorer_exposures": ("dataset_sha256",),
    # Suite member requests are inline in the roster; their launch hashes do
    # not promise separately stored request objects.
    "study_suite_runs": ("suite_sha256", "roster_sha256"),
    "research_comparisons": ("registration_sha256",), "research_broker_runs": ("configuration_sha256",),
    "research_broker_aliases": ("artifact_sha256",), "research_broker_stages": ("record_sha256",),
    "research_broker_tool_requests": ("request_sha256",), "research_private_responses": ("artifact_sha256",),
    "workflow_handoffs": ("document_sha256",), "failure_memory_dispositions": ("fix_artifact_ref",),
}
ARRAY_REFS = {"workflow_assignments": "input_refs", "workflow_intents": "input_refs",
              "workflow_effect_outcomes": "artifact_refs"}


def _references(db, audit, limits, deadline):
    refs, tombstones = set(), set()
    tables = audit["tables"]
    def add(value):
        _need(type(value) is str and DIGEST.fullmatch(value), "invalid_reference")
        refs.add(value)
        _need(len(refs) <= limits.objects, "reference_limit")
    def many(value):
        _need(type(value) is list and len(value) <= limits.objects, "invalid_reference_list")
        for item in value:
            add(item)
    def rows(table, columns):
        if table not in tables:
            return []
        _need(table not in audit["unknown_schema_tables"], "unsupported_reference_schema")
        return db.execute('SELECT ' + ','.join('"' + col + '"' for col in columns) + ' FROM "' + table + '"')
    for table, columns in DIRECT_REFS.items():
        for row in rows(table, columns):
            _tick(deadline)
            for item in row:
                if item is not None:
                    add(item)
    for table, column in ARRAY_REFS.items():
        for (value,) in rows(table, [column]):
            many(_parse(value))
    for (value,) in rows("provenance_outcomes", ["details"]):
        details = _parse(value)
        _need(type(details) is dict, "invalid_details")
        many(details.get("artifact_refs", []))
    for (value,) in rows("workflow_runs", ["manifest"]):
        manifest = _parse(value)
        _need(type(manifest) is dict, "invalid_workflow_manifest")
        many(manifest.get("input_refs", []))
    for (value,) in rows("workflow_handoffs", ["document"]):
        document = _parse(value)
        _need(type(document) is dict, "invalid_handoff")
        many(document.get("artifact_refs", []))
        many(document.get("reviewed_refs", []))
        _need(type(document.get("objections", [])) is list, "invalid_handoff")
        for objection in document.get("objections", []):
            _need(type(objection) is dict, "invalid_handoff")
            many(objection.get("artifact_refs", []))
    for kind, value in db.execute("SELECT kind,payload FROM events WHERE kind IN ('acquisition_request_prepared','acquisition_page_received')"):
        payload = _parse(value)
        _need(type(payload) is dict, "invalid_event_reference")
        add(payload.get("request_sha256" if kind == "acquisition_request_prepared" else "raw_sha256"))
    for (digest,) in rows("artifact_tombstones", ["digest"]):
        _need(type(digest) is str and DIGEST.fullmatch(digest), "invalid_tombstone")
        tombstones.add(digest)
    return refs, tombstones


def _copy_object(source, destination, digest, limits, deadline):
    _tick(deadline)
    raw = _read(source, limits.object_bytes)
    _need(_sha(raw) == digest, "object_digest_mismatch")
    _write(destination, raw)
    _tick(deadline)
    return len(raw)


def _coverage(refs, tombstones, objects, unknown):
    available = set(objects)
    _need(not refs - available - tombstones, "required_object_missing")
    _need(not available & tombstones, "tombstone_payload_present")
    return {"version": "known_database_refs_v1", "known_required_refs": sorted(refs),
            "tombstones": sorted(tombstones), "unavailable_tombstoned_refs": sorted(refs & tombstones),
            "unknown_schema_tables": unknown, "nested_document_schemas_checked": [],
            "typed_closure_complete": False, "full_recovery_accepted": False,
            "omissions": OMISSIONS}


def _report(manifest, manifest_sha256):
    return {"scope": FORMAT, "manifest_sha256": manifest_sha256, "event_head": manifest["database_state"]["events"]["head"],
            "table_count": len(manifest["database_state"]["tables"]), "object_count": len(manifest["objects"]),
            "snapshot_bytes_verified": True, "database_integrity_verified": True, "event_chain_verified": True,
            "known_database_references_verified": True, "typed_closure_complete": False,
            "full_recovery_accepted": False, "off_mac_recovery_verified": False, "execution_enabled": False,
            "unknown_schema_count": len(manifest["database_state"]["unknown_schema_tables"]),
            "tombstoned_dependency_count": len(manifest["coverage"]["unavailable_tombstoned_refs"]),
            "omissions": OMISSIONS}


def _manifest(value, limits):
    _need(type(value) is dict and set(value) == {"format", "started_at", "finished_at", "producer_sha256", "database", "database_state",
          "objects", "coverage", "unpublished_temporary_files_excluded", "consistency", "full_recovery_accepted"}
          and value["format"] == FORMAT and value["full_recovery_accepted"] is False
          and value["consistency"] == "separate_sqlite_writer_barrier_and_readonly_backup", "manifest_schema")
    _need(type(value["producer_sha256"]) is str and DIGEST.fullmatch(value["producer_sha256"]), "manifest_producer")
    times = []
    for key in ("started_at", "finished_at"):
        _need(type(value[key]) is str and len(value[key]) <= 40, "manifest_time")
        try:
            moment = datetime.fromisoformat(value[key])
        except ValueError:
            raise RecoveryError("manifest_time") from None
        _need(moment.utcoffset() is not None and moment.utcoffset().total_seconds() == 0
              and moment.isoformat() == value[key], "manifest_time")
        times.append(moment)
    _need(times[1] >= times[0], "manifest_time")
    pending = value["unpublished_temporary_files_excluded"]
    _need(type(pending) is int and 0 <= pending <= limits.objects, "manifest_pending_count")
    objects = value["objects"]
    _need(type(objects) is dict and len(objects) <= limits.objects
          and all(type(digest) is str and DIGEST.fullmatch(digest) for digest in objects), "manifest_objects")
    for metadata, maximum in [(value["database"], limits.database_bytes),
                              *((item, limits.object_bytes) for item in objects.values())]:
        _need(type(metadata) is dict and set(metadata) == {"bytes", "sha256"}
              and type(metadata["bytes"]) is int and 0 <= metadata["bytes"] <= maximum
              and type(metadata["sha256"]) is str and DIGEST.fullmatch(metadata["sha256"]), "manifest_file_metadata")


def capture_research_snapshot(source_root: Path, destination: Path, *, limits: Limits = Limits()) -> dict[str, Any]:
    """Make a new local candidate outside the source root; no automatic retries."""
    _bounds(limits)
    barrier = reader = target = None
    created = False
    try:
        source_root, destination = _path(source_root), _path(destination)
        _need(not destination.is_relative_to(source_root) and not source_root.is_relative_to(destination), "source_destination_overlap")
        _directory(source_root)
        _directory(destination.parent)
        for path in (source_root / "runtime", source_root / "data", source_root / "data/objects"):
            _directory(path)
        source_db, object_dir = source_root / "runtime/research.sqlite", source_root / "data/objects"
        source_info = source_db.lstat()
        _file_info(source_info, limits.database_bytes)
        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = source_db.with_name(source_db.name + suffix)
            if os.path.lexists(sidecar):
                _file_info(sidecar.lstat(), limits.database_bytes)
        destination.mkdir(mode=0o700)
        created = True
        _directory(destination, private=True)
        (destination / "objects").mkdir(mode=0o700)
        started = datetime.now(timezone.utc).isoformat()
        deadline = time.monotonic() + limits.seconds
        # Establish a read-only SHARED lock first. A hot rollback journal must
        # refuse here, never be recovered by opening the writer guard first.
        # Retaining this reader closes the writer/crash gap before the guard;
        # an existing writer may require bounded refusal rather than waiting.
        reader = _connect(source_db, "ro", deadline)
        reader.execute("BEGIN")
        reader.execute("SELECT count(*) FROM sqlite_schema").fetchone()
        barrier = _connect(source_db, "rw", deadline, timeout=limits.lock_seconds)
        barrier.execute("BEGIN IMMEDIATE")
        guarded_info = source_db.lstat()
        _file_info(guarded_info, limits.database_bytes)
        _need((guarded_info.st_ino, guarded_info.st_dev) == (source_info.st_ino, source_info.st_dev), "source_database_changed")
        _need(barrier.execute("PRAGMA journal_mode").fetchone() == ("delete",), "unsupported_journal_mode")
        original = _audit(barrier, limits, deadline)
        copied_db = destination / "research.sqlite"
        _write(copied_db, b"")
        target = sqlite3.connect(str(copied_db), isolation_level=None)
        reader.backup(target, pages=128, progress=lambda *_: _tick(deadline), sleep=0.01)
        target.close()
        target = None
        snapshot_db = _connect(copied_db, "ro", deadline, immutable=True)
        try:
            captured = _audit(snapshot_db, limits, deadline)
            _need(captured == original, "database_state_mismatch")
            refs, tombstones = _references(snapshot_db, captured, limits, deadline)
        finally:
            snapshot_db.close()
        raw_db = _read(copied_db, limits.database_bytes, private=True)
        total, objects, pending, entries = len(raw_db), {}, 0, 0
        _need(total <= limits.total_bytes, "total_bytes_limit")
        with os.scandir(object_dir) as scan:
            for entry in scan:
                _tick(deadline)
                entries += 1
                _need(entries <= limits.objects, "object_count_limit")
                match = OBJECT.fullmatch(entry.name)
                try:
                    _file_info(entry.stat(follow_symlinks=False), limits.object_bytes)
                except FileNotFoundError:
                    # A pre-barrier tombstone may already be committed while
                    # purge's later unlink is still running. Only those absent
                    # payloads are expected; a live disappearance still fails.
                    if match is not None and match[1] in tombstones:
                        continue
                    raise
                if PENDING.fullmatch(entry.name):
                    pending += 1
                    continue
                _need(match is not None, "unexpected_object_name")
                digest = match[1]
                if digest in tombstones:
                    continue
                size = _copy_object(Path(entry.path), destination / "objects" / entry.name, digest, limits, deadline)
                total += size
                _need(total <= limits.total_bytes, "total_bytes_limit")
                objects[digest] = {"bytes": size, "sha256": digest}
        coverage = _coverage(refs, tombstones, objects, captured["unknown_schema_tables"])
        current = source_db.lstat()
        _need((current.st_ino, current.st_dev) == (source_info.st_ino, source_info.st_dev), "source_database_changed")
        _need(_audit(barrier, limits, deadline) == original, "source_state_changed")
        reader.execute("ROLLBACK")
        reader.close()
        reader = None
        barrier.execute("ROLLBACK")
        barrier.close()
        barrier = None
        manifest = {"format": FORMAT, "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
                    "producer_sha256": _sha(Path(__file__).read_bytes()),
                    "database": {"bytes": len(raw_db), "sha256": _sha(raw_db)}, "database_state": captured,
                    "objects": objects, "coverage": coverage, "unpublished_temporary_files_excluded": pending,
                    "consistency": "separate_sqlite_writer_barrier_and_readonly_backup", "full_recovery_accepted": False}
        _manifest(manifest, limits)
        encoded = _json(manifest)
        _need(len(encoded) <= limits.manifest_bytes, "manifest_size_limit")
        _sync(destination / "objects")
        _sync(destination)
        _write(destination / "manifest.json", encoded)
        _sync(destination)
        _sync(destination.parent)
        return _report(manifest, _sha(encoded))
    except BaseException as exc:
        if created:
            try:
                _write(destination / "failure.json", _json({"state": "failed", "reason": str(exc) if isinstance(exc, RecoveryError) else "capture_failed",
                                                           "full_recovery_accepted": False, "automatic_retry": False}))
            except OSError:
                pass
        raise RecoveryError(str(exc) if isinstance(exc, RecoveryError) else "capture_failed") from None
    finally:
        for connection in (target, reader, barrier):
            if connection is not None:
                connection.close()


def inspect_research_snapshot(snapshot: Path, *, expected_manifest_sha256: str | None = None,
                              expected_event_head: str | None = None, limits: Limits = Limits()) -> dict[str, Any]:
    """Validate a closed candidate without modifying it or restoring authority."""
    _bounds(limits)
    db = None
    try:
        snapshot = _path(snapshot)
        _directory(snapshot, private=True)
        _need(set(os.listdir(snapshot)) == {"manifest.json", "research.sqlite", "objects"}, "snapshot_inventory_mismatch")
        _directory(snapshot / "objects", private=True)
        raw = _read(snapshot / "manifest.json", limits.manifest_bytes, private=True)
        if expected_manifest_sha256 is not None:
            _need(type(expected_manifest_sha256) is str and DIGEST.fullmatch(expected_manifest_sha256)
                  and _sha(raw) == expected_manifest_sha256, "manifest_checkpoint_mismatch")
        manifest = _parse(raw)
        _manifest(manifest, limits)
        objects = manifest["objects"]
        _need(set(os.listdir(snapshot / "objects")) == {digest + ".bin" for digest in objects}, "object_inventory_mismatch")
        database = _read(snapshot / "research.sqlite", limits.database_bytes, private=True)
        _need(manifest["database"] == {"bytes": len(database), "sha256": _sha(database)}, "database_digest_mismatch")
        total, deadline = len(database), time.monotonic() + limits.seconds
        _need(total <= limits.total_bytes, "total_bytes_limit")
        for digest, metadata in objects.items():
            _tick(deadline)
            value = _read(snapshot / "objects" / (digest + ".bin"), limits.object_bytes, private=True)
            _need(metadata == {"bytes": len(value), "sha256": _sha(value)} and metadata["sha256"] == digest, "object_digest_mismatch")
            total += len(value)
            _need(total <= limits.total_bytes, "total_bytes_limit")
        db = _connect(snapshot / "research.sqlite", "ro", deadline, immutable=True)
        _need(db.execute("PRAGMA journal_mode").fetchone() == ("delete",), "unsupported_journal_mode")
        observed = _audit(db, limits, deadline)
        _need(_json(observed) == _json(manifest["database_state"]), "database_state_mismatch")
        if expected_event_head is not None:
            _need(type(expected_event_head) is str and DIGEST.fullmatch(expected_event_head)
                  and observed["events"]["head"] == expected_event_head, "event_checkpoint_mismatch")
        refs, tombstones = _references(db, observed, limits, deadline)
        _need(_json(_coverage(refs, tombstones, objects, observed["unknown_schema_tables"])) == _json(manifest["coverage"]), "coverage_mismatch")
        _need(_sha(_read(snapshot / "research.sqlite", limits.database_bytes, private=True)) == manifest["database"]["sha256"], "inspection_changed_database")
        return _report(manifest, _sha(raw))
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, RecursionError) as exc:
        raise RecoveryError(str(exc) if isinstance(exc, RecoveryError) else "inspection_failed") from None
    finally:
        if db is not None:
            db.close()
KNOWN_COLUMNS = {'artifact_tombstones': ('digest', 'reason', 'tombstoned_at'),
 'attempts': ('attempt_id', 'fingerprint', 'started_at'),
 'dispatches': ('request_id', 'day', 'authorized_at'),
 'events': ('id', 'occurred_at', 'kind', 'payload', 'previous_hash', 'event_hash'),
 'experiments': ('fingerprint',
                 'specification',
                 'data_identity',
                 'code_identity',
                 'evidence_kind',
                 'assumptions',
                 'created_at'),
 'explorer_datasets': ('manifest_sha256',
                       'market_key',
                       'coverage_start',
                       'coverage_end',
                       'created_at'),
 'explorer_executions': ('submission_id', 'attempt_id', 'fingerprint', 'market_key'),
 'explorer_exposures': ('exposure_id',
                        'submission_id',
                        'dataset_sha256',
                        'market_key',
                        'market_identity',
                        'coverage_start',
                        'coverage_end',
                        'study_name',
                        'purpose',
                        'observed_at'),
 'failure_memory_dispositions': ('disposition_id',
                                 'source',
                                 'failure_id',
                                 'disposition',
                                 'fix_artifact_ref',
                                 'code',
                                 'submission_id',
                                 'created_at'),
 'jobs': ('job_id',
          'payload',
          'max_attempts',
          'state',
          'attempts',
          'fence',
          'worker_id',
          'lease_until',
          'result',
          'created_at'),
 'outcomes': ('attempt_id', 'status', 'result', 'finished_at'),
 'provenance_outcomes': ('submission_id', 'status', 'details', 'finished_at'),
 'provenance_submissions': ('submission_id',
                            'kind',
                            'request_sha256',
                            'request_bytes',
                            'request_encoding',
                            'started_at'),
 'provider_allocations': ('request_id', 'day', 'purpose', 'amount'),
 'research_broker_aliases': ('run_id', 'alias', 'artifact_sha256'),
 'research_broker_runs': ('submission_id',
                          'run_key',
                          'workflow_run_id',
                          'configuration_sha256',
                          'code_sha256'),
 'research_broker_stages': ('submission_id', 'role', 'assignment_id', 'record_sha256'),
 'research_broker_tool_children': ('assignment_id', 'request_id', 'child_submission_id'),
 'research_broker_tool_requests': ('parent_submission_id',
                                   'assignment_id',
                                   'request_id',
                                   'fence',
                                   'request_sha256'),
 'research_comparison_invocations': ('submission_id', 'suite_run_id'),
 'research_comparisons': ('submission_id', 'registration_sha256', 'fingerprint'),
 'research_dispatch_holds': ('request_id',
                             'assignment_id',
                             'amount',
                             'packet_sha256',
                             'body_sha256',
                             'transport_kind',
                             'created_at'),
 'research_model_observations': ('request_id', 'observation', 'created_at'),
 'research_private_responses': ('request_id', 'artifact_sha256', 'created_at'),
 'reservations': ('request_id',
                  'day',
                  'reserved_micro_usd',
                  'actual_micro_usd',
                  'state',
                  'created_at',
                  'updated_at'),
 'reviews': ('review_id',
             'role',
             'reviewer',
             'producer',
             'artifact_hash',
             'verdict',
             'findings',
             'created_at'),
 'study_suite_failures': ('run_id', 'cost_bps', 'error_code'),
 'study_suite_launches': ('run_id', 'cost_bps', 'request_sha256'),
 'study_suite_results': ('run_id', 'cost_bps', 'child_submission_id'),
 'study_suite_runs': ('submission_id', 'suite_sha256', 'roster_sha256'),
 'workflow_assignments': ('assignment_id',
                          'run_id',
                          'role',
                          'actor_id',
                          'token_hash',
                          'contract',
                          'input_refs',
                          'upstream_handoffs',
                          'job_id',
                          'created_at'),
 'workflow_cancellations': ('run_id', 'reason', 'created_at'),
 'workflow_claim_ends': ('assignment_id', 'fence', 'state', 'created_at'),
 'workflow_claims': ('claim_id', 'assignment_id', 'fence', 'worker_id', 'deadline', 'created_at'),
 'workflow_effect_outcomes': ('assignment_id',
                              'request_id',
                              'status',
                              'artifact_refs',
                              'observed_model',
                              'created_at'),
 'workflow_effect_starts': ('assignment_id', 'request_id', 'created_at'),
 'workflow_handoffs': ('assignment_id', 'document_sha256', 'document', 'created_at'),
 'workflow_intents': ('assignment_id', 'request_id', 'fence', 'action', 'input_refs', 'created_at'),
 'workflow_runs': ('run_id', 'run_key', 'manifest', 'created_at'),
 'workflow_terminals': ('assignment_id', 'state', 'reason', 'created_at')}

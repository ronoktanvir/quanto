"""D012 proposed development attachment; production adoption remains gated.

This is cooperating-process exclusion and local tamper evidence, not protection
against the owner, external freshness, or a general recovery mechanism. The
outer one-shot controller must durably consume its attempt BEFORE calling apply;
an absent event never entitles that controller to retry. No controller is here.
"""
from __future__ import annotations

from contextlib import contextmanager, ExitStack
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import time

from .evaluation_registry import AccessError, Supervisor, _digest, _directory, _id, _json, _need, _private_file, _sha
from .ledger import hash_json

EVENT_KIND = "authority_reattachment_v1"
EVENT_PREFIX = "authority_reattachment"
FLAGS = {"legacy_unknown": True, "external_freshness_verified": False,
         "protected_evaluation": False, "unattended_recovery": False}
_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]{0,127}\Z")


@dataclass(frozen=True)
class Limits:
    tables: int = 128
    rows: int = 250_000
    bytes: int = 128 * 1024 * 1024
    seconds: float = 20.0
    lock_seconds: float = 2.0

    def __post_init__(self):
        _need(all(type(v) is int and 0 < v <= cap for v, cap in
                  ((self.tables, 256), (self.rows, 1_000_000), (self.bytes, 512 * 1024 * 1024))))
        _need(all(type(v) in (int, float) and 0 < v <= 60
                  for v in (self.seconds, self.lock_seconds)))


class _Budget:
    """Finite scan/SQLite progress limits, not preemption of filesystem I/O.

    Cells have SQLite length caps; encoding/inspection still occurs after a row
    is fetched. The separate controller must impose the hard process deadline.
    """
    def __init__(self, limits):
        _need(type(limits) is Limits)
        self.limits = limits
        self.deadline = time.monotonic() + limits.seconds
        self.rows = self.bytes = 0

    def check(self, raw=b"", rows=0):
        self.rows += rows
        self.bytes += len(raw)
        _need(time.monotonic() < self.deadline and self.rows <= self.limits.rows
              and self.bytes <= self.limits.bytes, "reattachment_limit")

    def progress(self):
        return int(time.monotonic() >= self.deadline)


@contextmanager
def maintenance_gate(control: Path, *, exclusive=False, timeout=2.0):
    """Bounded flock on the EXISTING control DIRECTORY; no lockfile/bootstrap.

    Sessions retain shared locks for their lifetime. Standalone supervisor
    operations retain them through database use. Separate descriptors may nest
    shared locks; an exclusive administrator conflicts with every such holder.
    SQLite-file flock conflicts with SQLite record locks on macOS. The separate
    directory inode avoids that conflict. Replacement by a privileged owner is
    outside this cooperating threat model; directory paths are checked twice.
    """
    _need(type(timeout) in (int, float) and 0 < timeout <= 60)
    fd = None
    try:
        _private_file(control)
        directory = control.parent
        info = _directory(directory)
        _need(stat.S_IMODE(info.st_mode) == 0o700, "unsafe_control_store")
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        opened = os.fstat(fd)
        _need((opened.st_dev, opened.st_ino) == (info.st_dev, info.st_ino), "wrong_store")
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(fd, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                _need(time.monotonic() < deadline, "maintenance_busy")
                time.sleep(min(0.02, max(0, deadline - time.monotonic())))
        current = _directory(directory)
        _need(stat.S_IMODE(current.st_mode) == 0o700, "unsafe_control_store")
        _private_file(control)
        _need((current.st_dev, current.st_ino) == (opened.st_dev, opened.st_ino), "wrong_store")
        yield
    except (OSError, sqlite3.Error):
        raise AccessError("control_unavailable") from None
    finally:
        if fd is not None:
            os.close(fd)  # Closing the owned descriptor releases its flock.


def _paths(root):
    root = Path(root).absolute()
    return {"root": root, "control": root / "runtime/access-control/control.sqlite",
            "research": root / "runtime/research.sqlite", "objects": root / "data/objects"}


def _physical(root):
    try:
        return _physical_existing(root)
    except OSError:
        raise AccessError("control_unavailable") from None


def _physical_existing(root):
    paths, result = _paths(root), {}
    for directory in (paths["root"], paths["control"].parent.parent,
                      paths["control"].parent, paths["objects"].parent):
        _directory(directory)
    _need(stat.S_IMODE(paths["control"].parent.stat().st_mode) == 0o700, "unsafe_control_store")
    for name, path in paths.items():
        info = _directory(path) if name in {"root", "objects"} else _private_file(path)
        result[name] = {"path": str(path), "device": info.st_dev, "inode": info.st_ino,
                        "uid": info.st_uid, "gid": info.st_gid, "mode": stat.S_IMODE(info.st_mode)}
        if name in {"control", "research"}:
            for suffix in ("-wal", "-shm", "-journal"):
                sidecar = Path(str(path) + suffix)
                if os.path.lexists(sidecar):
                    _private_file(sidecar)
    return result


@contextmanager
def _connection(path, mode, budget):
    db = None
    try:
        db = sqlite3.connect(path.as_uri() + "?mode=" + mode, uri=True,
                             timeout=budget.limits.lock_seconds, isolation_level=None)
        db.execute("PRAGMA trusted_schema=OFF")
        db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, min(budget.limits.bytes, 16 * 1024 * 1024))
        db.set_progress_handler(budget.progress, 1000)
        if mode == "ro":
            db.execute("PRAGMA query_only=ON")
        yield db
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, OverflowError) as exc:
        if isinstance(exc, AccessError):
            raise
        raise AccessError("control_unavailable") from None
    finally:
        if db is not None:
            db.close()


def _encoded(value):
    # Include SQLite storage types; e.g. BLOB b"1" is not TEXT "1".
    def typed(item):
        if isinstance(item, bytes):
            return ["blob", item.hex()]
        return [type(item).__name__, item]
    return json.dumps([typed(v) for v in value], separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode()


def _table(db, name, budget, prefix=None):
    _need(type(name) is str and _NAME.fullmatch(name), "invalid_request")
    bound = None
    if prefix is not None:
        _need(type(prefix) is dict and set(prefix) == {"rows", "last_rowid", "sha256"})
        _need(type(prefix["rows"]) is int and 0 <= prefix["rows"] <= budget.limits.rows)
        _need(type(prefix["last_rowid"]) is int and prefix["last_rowid"] >= 0)
        _digest(prefix["sha256"])
        bound = prefix["last_rowid"]
    query = f'SELECT rowid,* FROM "{name}"'
    if bound is not None:
        query += " WHERE rowid <= ?"
    query += " ORDER BY rowid"
    digest, count, last = hashlib.sha256(), 0, 0
    for row in db.execute(query, () if bound is None else (bound,)):
        _need(type(row[0]) is int and row[0] > last, "state_mismatch")
        raw = _encoded(row)
        budget.check(raw, 1)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
        count, last = count + 1, row[0]
    result = {"rows": count, "last_rowid": last, "sha256": digest.hexdigest()}
    _need(prefix is None or result == prefix, "state_mismatch")
    return result


def _chain(db, which, budget, checkpoint=None):
    query = ("SELECT sequence,created_at,kind,payload,previous_hash,event_hash FROM audit ORDER BY sequence"
             if which == "control" else
             "SELECT id,occurred_at,kind,payload,previous_hash,event_hash FROM events ORDER BY id")
    count, previous, attachments = 0, "0" * 64, []
    checkpoint_seen = checkpoint is None or checkpoint == {"count": 0, "head": "0" * 64}
    for sequence, stamp, kind, payload, prior, digest in db.execute(query):
        budget.check(_encoded((sequence, stamp, kind, payload, prior, digest)), 1)
        count += 1
        _need(type(sequence) is int and sequence == count and prior == previous, "chain_mismatch")
        _need(all(type(v) is str for v in (stamp, kind, payload, prior, digest)), "chain_mismatch")
        try:
            decoded = json.loads(payload)
            expected = (_sha(_json([sequence, kind, payload, prior, stamp])) if which == "control"
                        else hash_json({"id": sequence, "occurred_at": stamp, "kind": kind,
                                        "payload": decoded, "previous_hash": prior}))
        except (ValueError, TypeError, RecursionError):
            raise AccessError("chain_mismatch") from None
        _need(digest == expected, "chain_mismatch")
        previous = digest
        if checkpoint == {"count": count, "head": digest}:
            checkpoint_seen = True
        if which == "control" and kind.startswith(EVENT_PREFIX):
            attachments.append({"kind": kind, "payload": decoded, "sequence": sequence,
                                "previous_hash": prior, "event_hash": digest})
            _need(len(attachments) <= 1, "attachment_conflict")
    _need(checkpoint_seen, "chain_mismatch")
    return {"count": count, "head": previous}, attachments


def _state(db, which, budget):
    _need(db.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "state_mismatch")
    schema, names = [], []
    for row in db.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name"):
        raw = _encoded(row)
        budget.check(raw, 1)
        schema.append(list(row))
        _need(len(schema) <= budget.limits.tables * 8, "reattachment_limit")
        if row[0] == "table":
            names.append(row[1])
    _need(0 < len(names) <= budget.limits.tables, "reattachment_limit")
    tables = {name: _table(db, name, budget) for name in names}
    head, attachments = _chain(db, which, budget)
    return {"schema_sha256": _sha(_json(schema)), "tables": tables, "head": head,
            "journal_mode": db.execute("PRAGMA journal_mode").fetchone()[0]}, attachments


def _witnesses(dbs, witnesses, budget):
    _need(type(witnesses) is list and 1 <= len(witnesses) <= 8)
    for witness in witnesses:
        _need(type(witness) is dict and set(witness) == {"sha256", "control", "research"})
        _digest(witness["sha256"])
        for which in ("control", "research"):
            prefixes = witness[which]
            _need(type(prefixes) is dict and len(prefixes) <= budget.limits.tables)
            for name, prefix in prefixes.items():
                _table(dbs[which], name, budget, prefix)
        _need(witness["control"] or witness["research"])


def _snapshot(root, dbs, budget, witnesses):
    identities = _physical(root)
    control, attachments = _state(dbs["control"], "control", budget)
    research, _ = _state(dbs["research"], "research", budget)
    configuration = dict(dbs["control"].execute("SELECT name,value FROM configuration"))
    if witnesses:
        _witnesses(dbs, witnesses, budget)
    _need(_physical(root) == identities, "state_mismatch")
    return {"identities": identities, "configuration": configuration, "control": control,
            "research": research, "witnesses": witnesses}, attachments


def inspect_authority(root, *, witnesses=(), limits=Limits()):
    """Read-only bounded inspection; never creates, repairs, or dispatches.

    Retained witness hashes are attributed pins. Their supplied table prefixes
    are independently recomputed; the caller retains the original witness files.
    """
    paths, budget = _paths(root), _Budget(limits)
    _physical(root)
    with maintenance_gate(paths["control"], timeout=limits.lock_seconds), ExitStack() as stack:
        dbs = {name: stack.enter_context(_connection(paths[name], "ro", budget))
               for name in ("control", "research")}
        for db in dbs.values():
            db.execute("BEGIN")
        snapshot, attachments = _snapshot(root, dbs, budget, list(witnesses))
        return {"snapshot": snapshot, "attachments": attachments}


def implementation_identity():
    """Current exact implementation/interpreter identities, not review approval."""
    from . import evaluation_registry
    paths = {"reattachment": Path(__file__), "registry": Path(evaluation_registry.__file__),
             "interpreter": Path(sys.executable).resolve()}
    result = {}
    for name, path in paths.items():
        _need(path.stat().st_size <= 128 * 1024 * 1024, "reattachment_limit")
        result[name] = {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return result


@dataclass(frozen=True)
class ReattachmentRequest:
    """Canonical immutable request; no nested caller-owned mutable structures."""
    encoded: str

    def __post_init__(self):
        _need(type(self.encoded) is str and len(self.encoded.encode()) <= 56 * 1024)
        try:
            value = json.loads(self.encoded)
        except (ValueError, RecursionError):
            raise AccessError("invalid_request") from None
        _need(_json(value) == self.encoded)
        try:
            _validate_request(value)
        except (TypeError, KeyError, OverflowError, RecursionError):
            raise AccessError("invalid_request") from None

    @classmethod
    def freeze(cls, *, snapshot, old_identities, attempt, bindings):
        return cls(_json({"version": 1, "snapshot": snapshot, "old_identities": old_identities,
                          "attempt": attempt, "bindings": bindings}))

    @property
    def document(self):
        return json.loads(self.encoded)

    @property
    def sha256(self):
        return _sha(self.encoded)


def _validate_request(request):
    _need(type(request) is dict and set(request) == {"version", "snapshot", "old_identities", "attempt", "bindings"})
    _need(type(request["version"]) is int and request["version"] == 1)
    _id(request["attempt"])
    snapshot, bindings = request["snapshot"], request["bindings"]
    _need(type(snapshot) is dict and set(snapshot) == {"identities", "configuration", "control", "research", "witnesses"})
    _need(type(bindings) is dict and set(bindings) == {"implementation", "policy_sha256", "reviews", "campaign_sha256"})
    for name in ("policy_sha256", "campaign_sha256"):
        _digest(bindings[name])
    _need(type(bindings["implementation"]) is dict and set(bindings["implementation"]) == {"reattachment", "registry", "interpreter"})
    for item in bindings["implementation"].values():
        _need(type(item) is dict and set(item) == {"path", "sha256"})
        _need(type(item["path"]) is str and Path(item["path"]).is_absolute())
        _digest(item["sha256"])
    _need(type(bindings["reviews"]) is dict and set(bindings["reviews"]) == {"critic", "quality", "scope", "fable", "opus"})
    for value in bindings["reviews"].values():
        _digest(value)
    current, old = snapshot["identities"], request["old_identities"]
    _need(type(old) is dict and type(current) is dict and set(old) == set(current) == {"root", "control", "research", "objects"})
    for name in current:
        before, after = old[name], current[name]
        fields = {"path", "device", "inode", "uid", "gid", "mode"}
        _need(type(before) is dict and type(after) is dict and set(before) == set(after) == fields)
        _need(type(after["path"]) is str and Path(after["path"]).is_absolute())
        _need(all(type(item[field]) is int and item[field] >= 0
                  for item in (before, after) for field in fields - {"path"}))
        _need(all(before[key] == after[key] for key in fields - {"device"}), "wrong_store")
    config = snapshot["configuration"]
    _need(type(config) is dict and set(config) == {"root", "device", "inode", "synthetic", "schema", "store_id", "principal", "legacy_unknown"})
    _need(config["root"] == current["root"]["path"] and config["device"] == str(old["root"]["device"])
          and config["inode"] == str(old["root"]["inode"]), "wrong_store")
    _need(config["synthetic"] == "False" and config["legacy_unknown"] == "True" and config["schema"] == "2", "wrong_store")
    _need(old["root"]["device"] != current["root"]["device"], "wrong_store")
    _id(config["store_id"])
    _id(config["principal"])
    _need(type(snapshot["witnesses"]) is list and 1 <= len(snapshot["witnesses"]) <= 8)
    for witness in snapshot["witnesses"]:
        _need(type(witness) is dict and set(witness) == {"sha256", "control", "research"})
        _digest(witness["sha256"])
        for which in ("control", "research"):
            _fingerprints(witness[which], allow_empty=True)
        _need(witness["control"] or witness["research"])
    for which in ("control", "research"):
        state = snapshot[which]
        _need(type(state) is dict and set(state) == {"schema_sha256", "tables", "head", "journal_mode"})
        _digest(state["schema_sha256"])
        _fingerprints(state["tables"])
        _need(type(state["head"]) is dict and set(state["head"]) == {"count", "head"})
        _need(type(state["head"]["count"]) is int and state["head"]["count"] >= 0)
        _digest(state["head"]["head"])
        _need(state["journal_mode"] in {"delete", "truncate", "persist", "wal"})
        event_table = "audit" if which == "control" else "events"
        _need(event_table in state["tables"] and state["tables"][event_table]["rows"] == state["head"]["count"]
              and state["tables"][event_table]["last_rowid"] == state["head"]["count"])


def _fingerprints(tables, *, allow_empty=False):
    _need(type(tables) is dict and int(not allow_empty) <= len(tables) <= 128)
    for name, prefix in tables.items():
        _need(type(name) is str and _NAME.fullmatch(name))
        _need(type(prefix) is dict and set(prefix) == {"rows", "last_rowid", "sha256"})
        _need(type(prefix["rows"]) is int and 0 <= prefix["rows"] <= 1_000_000)
        _need(type(prefix["last_rowid"]) is int and prefix["last_rowid"] >= prefix["rows"])
        _need((prefix["last_rowid"] == 0) == (prefix["rows"] == 0))
        _digest(prefix["sha256"])


def apply_reattachment(root, request, *, limits=Limits()):
    """Append once after an OUTER controller has consumed its unique attempt.

    Fixed lock order: maintenance EX, control BEGIN IMMEDIATE, research BEGIN
    IMMEDIATE. Only control commits; research is always rolled back. Exceptions
    after commit leave an uncertain consumed attempt, never permission to retry.
    """
    _need(type(request) is ReattachmentRequest)
    document, paths, budget = request.document, _paths(root), _Budget(limits)
    _need(document["bindings"]["implementation"] == implementation_identity(), "state_mismatch")
    _need(document["snapshot"]["identities"] == _physical(root), "wrong_store")
    with maintenance_gate(paths["control"], exclusive=True, timeout=limits.lock_seconds), ExitStack() as stack:
        dbs = {name: stack.enter_context(_connection(paths[name], "rw", budget))
               for name in ("control", "research")}
        control, research = dbs["control"], dbs["research"]
        control.execute("PRAGMA synchronous=FULL")
        control.execute("BEGIN IMMEDIATE")
        research.execute("BEGIN IMMEDIATE")
        try:
            snapshot, attachments = _snapshot(root, dbs, budget, document["snapshot"]["witnesses"])
            _need(not attachments, "attachment_conflict")
            _need(snapshot == document["snapshot"], "state_mismatch")
            _need(control.execute("SELECT 1 FROM principals WHERE principal=?", (snapshot["configuration"]["principal"],)).fetchone(), "wrong_store")
            payload = {"version": 1, "plan_sha256": request.sha256, "request": document, "limits": FLAGS}
            Supervisor._event(control, EVENT_KIND, payload)
            head, accepted = _chain(control, "control", budget)
            _need(len(accepted) == 1 and accepted[0]["payload"] == payload, "attachment_conflict")
            _need(head == {"count": snapshot["control"]["head"]["count"] + 1,
                           "head": accepted[0]["event_hash"]}, "state_mismatch")
            after, _ = _state(control, "control", budget)
            _need(after["schema_sha256"] == snapshot["control"]["schema_sha256"]
                  and after["journal_mode"] == snapshot["control"]["journal_mode"]
                  and set(after["tables"]) == set(snapshot["control"]["tables"]), "state_mismatch")
            for name, prefix in snapshot["control"]["tables"].items():
                _table(control, name, budget, prefix)
                _need(name == "audit" or after["tables"][name] == prefix, "state_mismatch")
            _need(_state(research, "research", budget)[0] == snapshot["research"], "state_mismatch")
            _need(_physical(root) == snapshot["identities"], "state_mismatch")
            _need(document["bindings"]["implementation"] == implementation_identity(), "state_mismatch")
            control.commit()
            return {"event_sha256": accepted[0]["event_hash"], "plan_sha256": request.sha256,
                    "attempt": document["attempt"], "control_head": head, "limits": dict(FLAGS)}
        finally:
            research.rollback()
            control.rollback()


def validate_attachment(db, root, configuration, pin, *, limits=Limits()):
    """Called under a supervisor shared gate; pin is required after acceptance.

    No-event stores retain original strict behavior. Accepted stores additionally
    verify full chains, the exact request, unchanged control prefixes and current
    physical identity. Ordinary later research state may grow/change; its bound
    historical event checkpoint must remain in its complete chain.
    """
    budget = _Budget(limits)
    old_limit = db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, min(limits.bytes, 16 * 1024 * 1024))
    db.set_progress_handler(budget.progress, 1000)
    try:
        return _validate_attachment(db, root, configuration, pin, budget)
    finally:
        db.set_progress_handler(None, 0)
        db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, old_limit)


def _validate_attachment(db, root, configuration, pin, budget):
    candidates = len(db.execute("SELECT 1 FROM audit WHERE kind LIKE ? LIMIT 2", (EVENT_PREFIX + "%",)).fetchall())
    if not candidates:
        _need(pin is None, "attachment_missing")
        return False
    _need(candidates == 1, "attachment_conflict")
    _need(pin is not None, "attachment_missing")
    _digest(pin)
    _, attachments = _chain(db, "control", budget)
    _need(len(attachments) == 1, "attachment_conflict")
    event = attachments[0]
    _need(event["kind"] == EVENT_KIND and event["event_hash"] == pin, "attachment_mismatch")
    payload = event["payload"]
    _need(type(payload) is dict and set(payload) == {"version", "plan_sha256", "request", "limits"}, "attachment_mismatch")
    _need(type(payload["version"]) is int and payload["version"] == 1
          and _json(payload["limits"]) == _json(FLAGS), "attachment_mismatch")
    request = ReattachmentRequest(_json(payload["request"]))
    snapshot = request.document["snapshot"]
    _need(payload["plan_sha256"] == request.sha256 and snapshot["configuration"] == configuration, "attachment_mismatch")
    _need(snapshot["identities"] == _physical(root), "wrong_store")
    _need(event["sequence"] == snapshot["control"]["head"]["count"] + 1
          and event["previous_hash"] == snapshot["control"]["head"]["head"], "chain_mismatch")
    state, _ = _state(db, "control", budget)
    _need(state["schema_sha256"] == snapshot["control"]["schema_sha256"]
          and state["journal_mode"] == snapshot["control"]["journal_mode"]
          and set(state["tables"]) == set(snapshot["control"]["tables"]), "state_mismatch")
    for name, prefix in snapshot["control"]["tables"].items():
        _table(db, name, budget, prefix)
    with _connection(_paths(root)["research"], "ro", budget) as research:
        research.execute("BEGIN")
        state, _ = _state(research, "research", budget)
        _need(state["schema_sha256"] == snapshot["research"]["schema_sha256"]
              and state["journal_mode"] == snapshot["research"]["journal_mode"]
              and set(state["tables"]) == set(snapshot["research"]["tables"]), "state_mismatch")
        _chain(research, "research", budget, snapshot["research"]["head"])
    _need(snapshot["identities"] == _physical(root), "wrong_store")
    return True

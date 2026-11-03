"""Private access accounting for cooperating supervisor-bound application services.

No protected acquisition, statistical acceptance or hostile-owner isolation. The
supervisor constructors are administrative authority, never model-facing tools.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import threading
import uuid
from urllib.parse import parse_qsl, urlsplit

MAX_RECORD = 64 * 1024
ACCESS_POLICY_VERSION = "development_access_v1"
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
IDENTIFIER = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,159}\Z")
REASONS = frozenset({
    "authority_missing", "authority_closed", "authority_already_active", "wrong_store", "principal_revoked",
    "unsafe_control_store", "control_unavailable", "invalid_request", "unknown_principal",
    "stale_identity_revision", "reservation_conflict", "legacy_unreconciled",
    "unknown_coverage", "already_consumed", "intent_refused", "intent_closed",
    "effect_mismatch", "effect_uncertain", "effect_started", "unknown_intent",
    "selector_reviewer_overlap", "unknown_reservation", "protected_unavailable",
    "network_forbidden", "invalid_transition", "classification_conflict",
})


class AccessError(ValueError):
    def __init__(self, reason):
        self.reason = reason if reason in REASONS else "control_unavailable"
        super().__init__(self.reason)


def _need(value, reason="invalid_request"):
    if not value:
        raise AccessError(reason)


def _json(value):
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        _need(len(raw.encode()) <= MAX_RECORD)
        return raw
    except (TypeError, ValueError, RecursionError, OverflowError):
        raise AccessError("invalid_request") from None


def _sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _id(value):
    _need(type(value) is str and IDENTIFIER.fullmatch(value) is not None)
    return value


def _digest(value):
    _need(type(value) is str and DIGEST.fullmatch(value) is not None)
    return value


def _day(value):
    _need(type(value) is str)
    try:
        _need(date.fromisoformat(value).isoformat() == value)
    except ValueError:
        raise AccessError("invalid_request") from None
    return value


def _now():
    return datetime.now(timezone.utc).isoformat()


def _directory(path):
    _need(path.is_absolute() and ".." not in path.parts
          and not any(p.is_symlink() for p in (path, *path.parents)), "unsafe_control_store")
    info = path.stat()
    _need(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o022,
          "unsafe_control_store")
    return info


def _private_file(path):
    info = path.lstat()
    _need(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1
          and stat.S_IMODE(info.st_mode) == 0o600, "unsafe_control_store")
    return info


@dataclass(frozen=True)
class Coverage:
    """Supervisor-derived scope; unknown dates/security conservatively overlap."""
    profile: str
    securities: tuple[str, ...] = ()
    start: str | None = None
    end: str | None = None

    def document(self):
        _need(self.profile in {"bars", "calendar", "actions", "content", "unknown"})
        _need(type(self.securities) is tuple and len(self.securities) <= 64)
        _need(tuple(sorted(set(self.securities))) == self.securities)
        for value in self.securities:
            _id(value)
        _need((self.start is None) == (self.end is None))
        if self.start is not None:
            _need(_day(self.start) <= _day(self.end))
        if self.profile in {"actions", "unknown"}:
            _need(self.start is None)  # Process dates never become economic dates.
        if self.profile == "calendar":
            _need(not self.securities and self.start is not None)
        return {"profile": self.profile, "securities": list(self.securities),
                "start": self.start, "end": self.end}


_SCHEMA = """
CREATE TABLE IF NOT EXISTS configuration (name TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS principals (principal TEXT PRIMARY KEY,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS principal_revocations (
 principal TEXT PRIMARY KEY REFERENCES principals(principal),evidence_sha256 TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS relations (
 revision INTEGER PRIMARY KEY,kind TEXT NOT NULL,left_id TEXT NOT NULL,right_id TEXT NOT NULL,
 evidence_sha256 TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit (
 sequence INTEGER PRIMARY KEY,kind TEXT NOT NULL,payload TEXT NOT NULL,
 previous_hash TEXT NOT NULL,event_hash TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS intents (
 intent TEXT PRIMARY KEY,principal TEXT NOT NULL,operation TEXT NOT NULL,
 request_sha256 TEXT NOT NULL,request_document TEXT,coverage TEXT NOT NULL,revision INTEGER NOT NULL,
 state TEXT NOT NULL,reason TEXT,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS intent_ends (
 intent TEXT PRIMARY KEY REFERENCES intents(intent),state TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS permitted_pages (
 intent TEXT NOT NULL REFERENCES intents(intent),identity TEXT NOT NULL,
 PRIMARY KEY(intent,identity));
CREATE TABLE IF NOT EXISTS effects (
 effect TEXT PRIMARY KEY,intent TEXT NOT NULL REFERENCES intents(intent),
 identity TEXT NOT NULL,started_at TEXT NOT NULL,UNIQUE(intent,identity));
CREATE TABLE IF NOT EXISTS effect_ends (
 effect TEXT PRIMARY KEY REFERENCES effects(effect),state TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reservations (
 reservation TEXT PRIMARY KEY,manifest TEXT NOT NULL,coverage TEXT NOT NULL,
 selectors TEXT NOT NULL,reviewers TEXT NOT NULL,revision INTEGER NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS invalidations (
 reservation TEXT NOT NULL REFERENCES reservations(reservation),reason TEXT NOT NULL,
 revision INTEGER NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(reservation,reason,revision));
CREATE TABLE IF NOT EXISTS classifications (
 digest TEXT PRIMARY KEY,coverage TEXT NOT NULL,evidence_sha256 TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS widenings (
 intent TEXT PRIMARY KEY REFERENCES intents(intent),coverage TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS producers (
 producer TEXT PRIMARY KEY,intent TEXT NOT NULL REFERENCES intents(intent),principal TEXT NOT NULL,
 adapter TEXT NOT NULL,source_sha256 TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS producer_responses (
 effect TEXT PRIMARY KEY REFERENCES effects(effect),producer TEXT NOT NULL REFERENCES producers(producer),
 digest TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS publications (
 publication TEXT PRIMARY KEY,producer TEXT NOT NULL REFERENCES producers(producer),role TEXT NOT NULL,
 digest TEXT NOT NULL,coverage TEXT NOT NULL,origins TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS publication_ends (
 publication TEXT PRIMARY KEY REFERENCES publications(publication),created_at TEXT NOT NULL);
"""
_TABLES = ("configuration", "principals", "principal_revocations", "relations", "audit", "intents", "intent_ends",
           "permitted_pages", "effects", "effect_ends", "reservations", "invalidations", "classifications", "widenings",
           "producers", "producer_responses", "publications", "publication_ends")
_ACTIVE = None
_ACTIVE_LOCK = threading.RLock()


class Supervisor:
    """Trusted bootstrap/administration, deliberately unavailable to ordinary roles."""
    def __init__(self, root: Path, *, synthetic=False):
        self.root = Path(root).absolute()
        _need(type(synthetic) is bool)
        self.synthetic = synthetic
        self._cache = False
        self._pool, self._pool_lock = {}, threading.RLock()
        info = _directory(self.root)
        with _ACTIVE_LOCK:
            _need(_ACTIVE is None or _ACTIVE.root == self.root, "authority_already_active")
        runtime = self.root / "runtime"
        runtime.mkdir(mode=0o700, exist_ok=True)
        _directory(runtime)
        directory = runtime / "access-control"
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            pass
        _directory(directory)
        _need(stat.S_IMODE(directory.stat().st_mode) == 0o700, "unsafe_control_store")
        self.path = directory / "control.sqlite"
        for suffix in ("", "-journal", "-wal", "-shm"):
            path = Path(str(self.path) + suffix)
            if os.path.lexists(path):
                _private_file(path)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
            os.close(fd)
            created = True
        except FileExistsError:
            created = False
        self._root_identity = (info.st_dev, info.st_ino)
        control_info = _private_file(self.path)
        self._file_identity = (control_info.st_dev, control_info.st_ino)
        expected = {"root": str(self.root), "device": str(info.st_dev), "inode": str(info.st_ino),
                    "synthetic": str(synthetic), "schema": "2"}
        if created:
            with self._db() as db:
                db.executescript(_SCHEMA)
                for table in _TABLES:
                    for operation in ("UPDATE", "DELETE"):
                        db.execute(f"CREATE TRIGGER IF NOT EXISTS no_{operation.lower()}_{table} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT,'append-only control record'); END")
                db.execute("BEGIN IMMEDIATE")
                try:
                    legacy = ((self.root / "runtime/research.sqlite").exists()
                              or (self.root / "data/objects").exists()
                              or (self.root / "artifacts").exists())
                    principal = uuid.uuid4().hex
                    values = {**expected, "store_id": uuid.uuid4().hex, "principal": principal,
                              "legacy_unknown": str(bool(legacy))}
                    db.executemany("INSERT INTO configuration VALUES (?,?)", values.items())
                    db.execute("INSERT INTO principals VALUES (?,?)", (principal, _now()))
                    self._event(db, "bootstrap", {"legacy_unknown": bool(legacy), "synthetic": synthetic})
                    rows = values
                    db.commit()
                except BaseException:
                    db.rollback()
                    raise
        else:
            # An existing file is never silently initialized or migrated. Read
            # its binding before any writable connection/schema operation.
            try:
                with closing(sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True)) as db:
                    db.execute("PRAGMA trusted_schema=OFF")
                    rows = dict(db.execute("SELECT name,value FROM configuration"))
                    _need(set(rows) == set(expected) | {"store_id", "principal", "legacy_unknown"}, "wrong_store")
                    _need(all(rows[key] == value for key, value in expected.items()), "wrong_store")
                    _need(rows["legacy_unknown"] in {"True", "False"}, "wrong_store")
                    _id(rows["store_id"])
                    _id(rows["principal"])
                    _need(db.execute("SELECT 1 FROM principals WHERE principal=?", (rows["principal"],)).fetchone(), "wrong_store")
            except (OSError, sqlite3.Error):
                raise AccessError("control_unavailable") from None
            self._check_paths()
        self.store_id, self.principal = rows["store_id"], rows["principal"]

    def _check_paths(self):
        _need(stat.S_IMODE(_directory(self.path.parent).st_mode) == 0o700, "unsafe_control_store")
        info = _private_file(self.path)
        if hasattr(self, "_file_identity"):
            _need((info.st_dev, info.st_ino) == self._file_identity, "wrong_store")
            root_info = _directory(self.root)
            _need((root_info.st_dev, root_info.st_ino) == self._root_identity, "wrong_store")

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=2, isolation_level=None, check_same_thread=False)
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA trusted_schema=OFF")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def _close_connections(self):
        with self._pool_lock:
            self._cache = False
            connections, self._pool = list(self._pool.values()), {}
        for db, lock in connections:
            with lock:
                db.close()

    @contextmanager
    def _db(self):
        db, lock, borrowed = None, None, False
        try:
            self._check_paths()
            with self._pool_lock:
                if self._cache:
                    key = threading.get_ident()
                    if key not in self._pool:
                        self._pool[key] = (self._connect(), threading.RLock())
                    db, lock = self._pool[key]
                    lock.acquire()
                    borrowed = True
                else:
                    db = self._connect()
            yield db
        except (OSError, sqlite3.Error):
            raise AccessError("control_unavailable") from None
        finally:
            if borrowed:
                lock.release()
            elif db is not None:
                db.close()

    @contextmanager
    def _transaction(self):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    @staticmethod
    def _event(db, kind, payload):
        last = db.execute("SELECT sequence,event_hash FROM audit ORDER BY sequence DESC LIMIT 1").fetchone()
        sequence, prior = (last[0] + 1, last[1]) if last else (1, "0" * 64)
        stamp, encoded = _now(), _json(payload)
        digest = _sha(_json([sequence, kind, encoded, prior, stamp]))
        db.execute("INSERT INTO audit VALUES (?,?,?,?,?,?)", (sequence, kind, encoded, prior, digest, stamp))

    @staticmethod
    def _revision(db):
        return db.execute("SELECT coalesce(max(revision),0) FROM relations").fetchone()[0]

    @staticmethod
    def _equivalence(db, kind, values):
        found = set(values)
        links = db.execute("SELECT left_id,right_id FROM relations WHERE kind=?", (kind,)).fetchall()
        _need(len(links) <= 10000, "control_unavailable")
        changed = True
        while changed:
            changed = False
            for left, right in links:
                if (left in found) != (right in found):
                    found.update((left, right))
                    changed = True
        return found

    @classmethod
    def _overlap(cls, db, left, right):
        if (left["start"] is not None and right["start"] is not None
                and (left["end"] < right["start"] or right["end"] < left["start"])):
            return False
        if not left["securities"] or not right["securities"]:
            return True
        return bool(cls._equivalence(db, "security", left["securities"])
                    & cls._equivalence(db, "security", right["securities"]))

    @classmethod
    def _conflicting_reservation(cls, db, coverage):
        return any(cls._overlap(db, coverage, json.loads(row[0]))
                   for row in db.execute("SELECT coverage FROM reservations"))

    @staticmethod
    def _classification(db, digest):
        row = db.execute("SELECT coverage FROM classifications WHERE digest=?", (digest,)).fetchone()
        widened = db.execute("SELECT 1 FROM publications p JOIN publication_ends e USING(publication) JOIN producers r USING(producer) JOIN widenings w ON w.intent=r.intent WHERE p.digest=? LIMIT 1", (digest,)).fetchone()
        return Coverage("unknown").document() if widened else json.loads(row[0]) if row else None

    def _principal_active(self, db, principal):
        _need(db.execute("SELECT 1 FROM principals WHERE principal=?", (principal,)).fetchone(), "unknown_principal")
        related = self._equivalence(db, "principal", [principal])
        revoked = {row[0] for row in db.execute("SELECT principal FROM principal_revocations")}
        _need(not related & revoked, "principal_revoked")

    def revoke_principal(self, principal, evidence_sha256):
        _id(principal)
        _digest(evidence_sha256)
        with self._transaction() as db:
            self._principal_active(db, principal)
            revision = self._revision(db) + 1
            db.execute("INSERT INTO principal_revocations VALUES (?,?,?)", (principal, evidence_sha256, _now()))
            db.execute("INSERT INTO relations VALUES (?,'revocation',?,?,?,?)",
                       (revision, principal, principal, evidence_sha256, _now()))
            self._event(db, "principal_revoked", {"principal": principal, "revision": revision})
            self._invalidate_conflicts(db, revision)

    def session(self, principal=None):
        principal = self.principal if principal is None else _id(principal)
        return AccessSession(self, principal)

    def _validate_session_principal(self, principal):
        reason = None
        with self._transaction() as db:
            try:
                self._principal_active(db, principal)
            except AccessError as exc:
                reason = exc.reason
                self._event(db, "session_refused", {"principal": principal, "reason": reason})
        if reason:
            raise AccessError(reason)

    def issue_principal(self):
        principal = uuid.uuid4().hex
        with self._transaction() as db:
            db.execute("INSERT INTO principals VALUES (?,?)", (principal, _now()))
            self._event(db, "principal_issued", {"principal": principal})
        return principal

    def relate(self, kind, left, right, evidence_sha256):
        _need(kind in {"security", "principal"})
        _id(left)
        _id(right)
        _digest(evidence_sha256)
        with self._transaction() as db:
            if kind == "principal":
                _need(all(db.execute("SELECT 1 FROM principals WHERE principal=?", (x,)).fetchone()
                          for x in (left, right)), "unknown_principal")
            revision = self._revision(db) + 1
            db.execute("INSERT INTO relations VALUES (?,?,?,?,?,?)", (revision, kind, left, right, evidence_sha256, _now()))
            self._event(db, "identity_relation", {"kind": kind, "revision": revision, "evidence_sha256": evidence_sha256})
            self._invalidate_conflicts(db, revision)
        return revision

    def _invalidate_conflicts(self, db, revision):
        exposures = [json.loads(row[0]) for row in db.execute("SELECT coverage FROM intents WHERE state='issued' AND intent NOT IN (SELECT intent FROM intent_ends WHERE state='rejected_before_access')")]
        exposures += [json.loads(row[0]) for row in db.execute("SELECT coverage FROM widenings")]
        reservations = db.execute("SELECT reservation,coverage,selectors,reviewers FROM reservations").fetchall()
        for identity, raw, selectors, reviewers in reservations:
            overlap = any(self._overlap(db, json.loads(raw), scope) for scope in exposures)
            principals_overlap = bool(self._equivalence(db, "principal", json.loads(selectors))
                                      & self._equivalence(db, "principal", json.loads(reviewers)))
            revoked = {row[0] for row in db.execute("SELECT principal FROM principal_revocations")}
            revoked_role = bool(self._equivalence(db, "principal", json.loads(selectors) + json.loads(reviewers)) & revoked)
            if overlap or principals_overlap or revoked_role:
                reason = "exposure_conflict" if overlap else "principal_conflict" if principals_overlap else "principal_revoked"
                db.execute("INSERT OR IGNORE INTO invalidations VALUES (?,?,?,?)", (identity, reason, revision, _now()))
                self._event(db, "reservation_invalidated", {"reservation": identity, "reason": reason})

    def classify(self, digest, coverage: Coverage, evidence_sha256):
        _digest(digest)
        _digest(evidence_sha256)
        document = coverage.document()
        with self._transaction() as db:
            row = db.execute("SELECT coverage,evidence_sha256 FROM classifications WHERE digest=?", (digest,)).fetchone()
            if row:
                _need(row == (_json(document), evidence_sha256), "classification_conflict")
                return
            db.execute("INSERT INTO classifications VALUES (?,?,?,?)", (digest, _json(document), evidence_sha256, _now()))
            self._event(db, "object_classified", {"digest": digest, "evidence_sha256": evidence_sha256})

    def reserve(self, manifest):
        """Reserve a preparation boundary, never activate protected evaluation."""
        identity = uuid.uuid4().hex
        reason = None
        with self._transaction() as db:
            try:
                fields = {"coverage", "warmup", "final", "candidate_sha256", "code_sha256", "dependencies_sha256",
                          "scenarios_sha256", "rights_sha256", "release_sha256", "selectors", "reviewers"}
                _need(type(manifest) is dict and set(manifest) == fields)
                for key in fields - {"coverage", "warmup", "final", "selectors", "reviewers"}:
                    _digest(manifest[key])
                coverage = Coverage(**{**manifest["coverage"], "securities": tuple(manifest["coverage"]["securities"])}).document()
                _need(coverage["securities"] and coverage["start"] is not None, "unknown_coverage")
                known = {item for row in db.execute("SELECT left_id,right_id FROM relations WHERE kind='security'")
                         for item in row if item.startswith("security:")}
                _need(all(item in known for item in coverage["securities"]), "unknown_coverage")
                for interval in (manifest["warmup"], manifest["final"]):
                    _need(type(interval) is dict and set(interval) == {"start", "end"})
                    _need(coverage["start"] <= _day(interval["start"]) <= _day(interval["end"]) <= coverage["end"])
                _need(manifest["warmup"]["end"] < manifest["final"]["start"])
                selectors, reviewers = manifest["selectors"], manifest["reviewers"]
                _need(all(type(group) is list and 0 < len(group) <= 16 and len(set(group)) == len(group)
                          for group in (selectors, reviewers)))
                for principal in selectors + reviewers:
                    _id(principal)
                    self._principal_active(db, principal)
                _need(not (self._equivalence(db, "principal", selectors) & self._equivalence(db, "principal", reviewers)), "selector_reviewer_overlap")
                _need(db.execute("SELECT value FROM configuration WHERE name='legacy_unknown'").fetchone()[0] == "False", "legacy_unreconciled")
                _need(not self._conflicting_reservation(db, coverage), "reservation_conflict")
                for (raw,) in db.execute("SELECT coverage FROM intents WHERE state='issued' AND intent NOT IN (SELECT intent FROM intent_ends WHERE state='rejected_before_access') UNION ALL SELECT coverage FROM widenings"):
                    _need(not self._overlap(db, coverage, json.loads(raw)), "reservation_conflict")
                db.execute("INSERT INTO reservations VALUES (?,?,?,?,?,?,?)", (identity, _json(manifest), _json(coverage),
                           _json(selectors), _json(reviewers), self._revision(db), _now()))
                self._event(db, "preparation_reserved", {"reservation": identity})
            except (AccessError, TypeError, KeyError, ValueError) as exc:
                reason = "invalid_request"
                if isinstance(exc, AccessError):
                    reason = exc.reason
                self._event(db, "reservation_refused", {"attempt": identity, "reason": reason})
        if reason:
            raise AccessError(reason)
        return {"reservation": identity, "state": "preparation_reserved", "protected_eligible": False,
                "protected_acquisition_enabled": False}

    def protected_acquire(self, *_args, **_kwargs):
        with self._transaction() as db:
            self._event(db, "protected_refused", {"reason": "protected_unavailable"})
        raise AccessError("protected_unavailable")

    def producer(self, intent, adapter):
        """Administrative issuance to a pinned deterministic acquisition adapter.

        This authority is not on the ordinary session/intent API. Like principal
        and alias issuance, it must never be exposed as a worker/model tool.
        """
        _need(type(intent) is AccessIntent and intent.session.supervisor is self, "unknown_intent")
        intent.session.check()
        _need(adapter in {"alpaca_bars", "alpaca_calendar", "alpaca_actions"})
        module = "alpaca_actions.py" if adapter == "alpaca_actions" else "alpaca_data.py"
        source = hashlib.sha256(Path(__file__).with_name(module).read_bytes()).hexdigest()
        identity = uuid.uuid4().hex
        with self._transaction() as db:
            row = db.execute("SELECT principal,state,request_document FROM intents WHERE intent=?", (intent.identity,)).fetchone()
            _need(row and row[:2] == (intent.session.principal, "issued"), "unknown_intent")
            _need(json.loads(row[2])["kind"] == adapter.removeprefix("alpaca_"), "effect_mismatch")
            db.execute("INSERT INTO producers VALUES (?,?,?,?,?,?)",
                       (identity, intent.identity, intent.session.principal, adapter, source, _now()))
            self._event(db, "producer_issued", {"producer": identity, "adapter": adapter, "source_sha256": source})
        producer = ProducerAuthority(intent, identity, adapter, source)
        intent.session._producers[identity] = producer
        return producer

    def overview(self):
        with self._db() as db:
            return {"intents": db.execute("SELECT count(*) FROM intents").fetchone()[0],
                    "effects": db.execute("SELECT count(*) FROM effects").fetchone()[0],
                    "reservations": db.execute("SELECT count(*) FROM reservations").fetchone()[0],
                    "invalidations": db.execute("SELECT count(*) FROM invalidations").fetchone()[0],
                    "protected_eligible": False, "protected_acquisition_enabled": False}


class AccessSession:
    def __init__(self, supervisor, principal):
        self.supervisor, self._principal = supervisor, _id(principal)
        supervisor._validate_session_principal(self._principal)
        self._root, self._synthetic = supervisor.root, supervisor.synthetic
        self._active, self._closed = False, False
        self._grants, self._grant_lock = {}, threading.RLock()
        self._producers, self._publications = {}, {}

    @property
    def principal(self):
        return self._principal

    @property
    def root(self):
        return self._root

    @property
    def synthetic(self):
        return self._synthetic

    def __enter__(self):
        global _ACTIVE
        with _ACTIVE_LOCK:
            _need(not self._closed, "authority_closed")
            _need(_ACTIVE is None, "authority_already_active")
            self.supervisor._validate_session_principal(self.principal)
            self._active = True
            with self.supervisor._pool_lock:
                self.supervisor._cache = True
            _ACTIVE = self
        return self

    def __exit__(self, *_):
        global _ACTIVE
        with _ACTIVE_LOCK:
            if not self._active or _ACTIVE is not self:
                return
            self._active = False
            self._closed = True
            with self._grant_lock:
                self._grants.clear()
                self._producers.clear()
                self._publications.clear()
            self.supervisor._close_connections()
            _ACTIVE = None

    def check(self, root=None):
        _need(self._active and _ACTIVE is self, "authority_closed")
        if root is not None:
            _need(Path(root).absolute() == self.root, "wrong_store")
        try:
            self.supervisor._check_paths()
        except OSError:
            raise AccessError("control_unavailable") from None

    def cache_epoch(self):
        """Cache reuse is limited to the same live authority and identity policy."""
        self.check()
        try:
            with self.supervisor._db() as db:
                self.supervisor._principal_active(db, self.principal)
                revision = self.supervisor._revision(db)
                coverage_revision = db.execute("SELECT count(*) FROM widenings").fetchone()[0]
        except AccessError as exc:
            if exc.reason in {"principal_revoked", "unknown_principal"}:
                with self.supervisor._transaction() as db:
                    self.supervisor._event(db, "reuse_refused", {"principal": self.principal, "reason": exc.reason})
            raise
        return (self.supervisor.store_id, self.principal, revision, ACCESS_POLICY_VERSION, coverage_revision)

    def issue(self, operation, request_sha256, *, request_document=None):
        """Derive scope from frozen input; callers cannot supply a narrower scope."""
        self.check()
        _need(operation in {"provider_page", "content_read"})
        _digest(request_sha256)
        encoded = _json(request_document) if request_document is not None else None
        request_document = json.loads(encoded) if encoded else None
        if operation == "provider_page":
            _need(type(request_document) is dict and set(request_document) == {"kind", "request"})
            _need(request_document["kind"] in {"bars", "calendar", "actions"})
            _need(_sha(_json(request_document["request"])) == request_sha256)
        else:
            _need(request_document is None)
        identity, reason = uuid.uuid4().hex, None
        with self.supervisor._transaction() as db:
            document = Coverage("unknown").document()
            try:
                self.supervisor._principal_active(db, self.principal)
                if operation == "provider_page":
                    document = self._request_coverage(db, request_document["kind"], request_document["request"])
                else:
                    document = self.supervisor._classification(db, request_sha256) or document
                if self.supervisor._conflicting_reservation(db, document):
                    reason = "reservation_conflict"
            except AccessError as exc:
                reason = exc.reason
            except (KeyError, TypeError, ValueError):
                reason = "invalid_request"
            revision = self.supervisor._revision(db)
            db.execute("INSERT INTO intents VALUES (?,?,?,?,?,?,?,?,?,?)", (identity, self.principal, operation,
                       request_sha256, encoded, _json(document), revision, "refused" if reason else "issued", reason, _now()))
            self.supervisor._event(db, "intent_refused" if reason else "intent_issued",
                                   {"intent": identity, "reason": reason})
        if reason:
            raise AccessError(reason)
        return AccessIntent(self, identity, operation)

    def _request_coverage(self, db, kind, request):
        _need(type(request) is dict)
        securities = ()
        if kind != "calendar":
            alias = "alpaca:us_equity:" + _id(request["symbol"])
            related = self.supervisor._equivalence(db, "security", [alias])
            securities = tuple(sorted(value for value in related if value.startswith("security:")))
        scope = Coverage(kind if securities or kind == "calendar" else "unknown", securities,
                         request["start"] if kind != "actions" and (securities or kind == "calendar") else None,
                         request["end"] if kind != "actions" and (securities or kind == "calendar") else None)
        return scope.document()

    def acquisition(self, kind, request):
        return self.issue("provider_page", _sha(_json(request)),
                          request_document={"kind": kind, "request": request})

    def content(self, digest):
        return self.issue("content_read", digest)

    def observe_import(self, digest=None, *, unknown_reason=None):
        """Input bytes are already observed, even if their publication refuses."""
        self.check()
        if digest is None:
            _need(unknown_reason in {"json_input", "unbounded_bytes"})
            # This is an attempt identity, not a fabricated content digest. Do
            # not inspect/hash potentially unbounded or unserializable inputs.
            digest = _sha("unknown_import:" + uuid.uuid4().hex)
            document = _json({"identity_kind": "attempt_only", "reason": unknown_reason})
        else:
            _digest(digest)
            _need(unknown_reason is None)
            document = None
        intent, effect = uuid.uuid4().hex, uuid.uuid4().hex
        reason = None
        with self.supervisor._transaction() as db:
            try:
                self.supervisor._principal_active(db, self.principal)
            except AccessError as exc:
                reason = exc.reason
            coverage = (self.supervisor._classification(db, digest) if document is None else None) or Coverage("unknown").document()
            conflict = self.supervisor._conflicting_reservation(db, coverage)
            revision = self.supervisor._revision(db)
            db.execute("INSERT INTO intents VALUES (?,?,?,?,?,?,?,?,?,?)", (intent, self.principal,
                       "content_import", digest, document, _json(coverage), revision, "issued", None, _now()))
            db.execute("INSERT INTO effects VALUES (?,?,?,?)", (effect, intent, digest, _now()))
            db.execute("INSERT INTO effect_ends VALUES (?,'completed',?)", (effect, _now()))
            self.supervisor._event(db, "import_observed", {"intent": intent, "effect": effect,
                                    "publication_refused": bool(conflict or reason), "reason": reason})
            if conflict:
                self.supervisor._invalidate_conflicts(db, revision)
        if conflict or reason:
            raise AccessError(reason or "reservation_conflict")


class AccessIntent:
    def __init__(self, session, identity, operation):
        self.session, self.identity, self.operation = session, identity, operation

    def effect(self, identity):
        return EffectPermit(self, _digest(identity))

    def observe_response(self, raw):
        """Mandatory transport-side coverage check, independent of publication."""
        self.session.check()
        with self.session.supervisor._db() as db:
            row = db.execute("SELECT request_document FROM intents WHERE intent=? AND principal=? AND operation='provider_page' AND state='issued'",
                             (self.identity, self.session.principal)).fetchone()
            _need(row, "unknown_intent")
            document = json.loads(row[0])
        from quanto import alpaca_data, alpaca_actions
        if document["kind"] == "actions":
            alpaca_actions._observe_coverage(self, raw, document["request"])
        else:
            alpaca_data._observe_coverage(self, raw, document["kind"], document["request"])

    def page(self, method, url):
        """Authorize an exact page derived from the already frozen request."""
        self.session.check()
        from quanto import alpaca_data, alpaca_actions
        try:
            _need(self.operation == "provider_page", "effect_mismatch")
            alpaca_data._route(method, url)
            with self.session.supervisor._transaction() as db:
                row = db.execute("SELECT request_document,principal,state FROM intents WHERE intent=?",
                                 (self.identity,)).fetchone()
                _need(row and row[1:] == (self.session.principal, "issued"), "unknown_intent")
                document = json.loads(row[0])
                pairs = dict(parse_qsl(urlsplit(url).query, keep_blank_values=True))
                token = pairs.get("page_token")
                expected = (alpaca_actions._url(document["request"], token) if document["kind"] == "actions"
                            else alpaca_data._url(document["request"], document["kind"], token))
                _need(method == "GET" and url == expected, "effect_mismatch")
                identity = request_identity(method, url)
                db.execute("INSERT OR IGNORE INTO permitted_pages VALUES (?,?)", (self.identity, identity))
        except (AccessError, alpaca_data.AcquisitionError) as exc:
            reason = exc.reason if isinstance(exc, AccessError) else "effect_mismatch"
            audit_refusal("page", reason)
            raise AccessError(reason) from None
        return EffectPermit(self, identity)

    def reject_before_access(self):
        self.session.check()
        with self.session.supervisor._transaction() as db:
            row = db.execute("SELECT state,principal FROM intents WHERE intent=?", (self.identity,)).fetchone()
            _need(row == ("issued", self.session.principal), "unknown_intent")
            _need(not db.execute("SELECT 1 FROM effects WHERE intent=?", (self.identity,)).fetchone(), "effect_started")
            _need(not db.execute("SELECT 1 FROM intent_ends WHERE intent=?", (self.identity,)).fetchone(), "intent_closed")
            db.execute("INSERT INTO intent_ends VALUES (?,'rejected_before_access',?)", (self.identity, _now()))
            self.session.supervisor._event(db, "intent_rejected_before_access", {"intent": self.identity})

    def widen_unknown(self):
        self.session.check()
        with self.session.supervisor._transaction() as db:
            if not db.execute("SELECT 1 FROM widenings WHERE intent=?", (self.identity,)).fetchone():
                db.execute("INSERT INTO widenings VALUES (?,?,?)", (self.identity, _json(Coverage("unknown").document()), _now()))
                self.session.supervisor._event(db, "coverage_became_unknown", {"intent": self.identity})
                self.session.supervisor._invalidate_conflicts(db, self.session.supervisor._revision(db))

    def bind_object(self, digest):
        """Ordinary intents cannot mint classifications for supplied digests."""
        self.session.check()
        audit_refusal("publication", "authority_missing")
        raise AccessError("authority_missing")


class ProducerAuthority:
    """Supervisor-issued authority held only by a pinned deterministic adapter."""
    def __init__(self, intent, identity, adapter, source):
        self.intent, self.identity, self.adapter, self.source = intent, identity, adapter, source
        self._responses = []

    def _check(self):
        session = self.intent.session
        session.check()
        _need(session._producers.get(self.identity) is self, "authority_missing")
        module = "alpaca_actions.py" if self.adapter == "alpaca_actions" else "alpaca_data.py"
        _need(hashlib.sha256(Path(__file__).with_name(module).read_bytes()).hexdigest() == self.source,
              "stale_identity_revision")
        return session

    def observed_response(self, permit, raw):
        """Called by the dispatch adapter with its exact returned immutable bytes."""
        session = self._check()
        _need(type(permit) is EffectPermit and permit.intent is self.intent, "effect_mismatch")
        _need(type(raw) is bytes and len(raw) <= 2 * 1024 * 1024)
        grant = permit._grant
        _need(grant is not None and grant.used, "effect_uncertain")
        digest = hashlib.sha256(raw).hexdigest()
        with session.supervisor._transaction() as db:
            row = db.execute("SELECT e.intent,e.identity,t.state FROM effects e JOIN effect_ends t USING(effect) WHERE effect=?",
                             (grant.effect,)).fetchone()
            _need(row == (self.intent.identity, permit.identity, "completed"), "effect_uncertain")
            db.execute("INSERT INTO producer_responses VALUES (?,?,?,?)", (grant.effect, self.identity, digest, _now()))
            session.supervisor._event(db, "producer_response_observed", {"producer": self.identity, "effect": grant.effect, "digest": digest})
        self._responses.append((grant.effect, digest, raw))

    def _normalized(self, request):
        from quanto import alpaca_data as data, alpaca_actions as actions
        kind = self.adapter.removeprefix("alpaca_")
        rows, categories = [], set()
        _need(self._responses, "effect_uncertain")
        for ordinal, (_, digest, raw) in enumerate(self._responses, 1):
            if kind == "actions":
                records, present, token = actions._page(actions._json(raw), digest, ordinal)
                rows.extend(records)
                categories.update(present)
            elif kind == "calendar":
                _need(len(self._responses) == 1, "effect_mismatch")
                rows, token = data._calendar(data._json(raw), request), None
            else:
                body = data._json(raw)
                _need(body.get("symbol") == request["symbol"] and isinstance(body.get("bars"), list), "effect_mismatch")
                token = body["next_page_token"]
                for value in body["bars"]:
                    row = data._bar(value, request)
                    _need(not rows or row["timestamp"] > rows[-1]["timestamp"], "effect_mismatch")
                    rows.append(row)
            _need((token is None) == (ordinal == len(self._responses)), "effect_uncertain")
        if kind == "actions":
            return actions._normalized(request, rows, categories)
        _need(rows, "effect_uncertain")
        return data._normalized(request, rows, kind)

    def _validate_publication(self, role, raw, document):
        from quanto import alpaca_data as data, alpaca_actions as actions
        request, kind = document["request"], document["kind"]
        if role == "response":
            return
        value = data._json(raw)
        if role == "submitted_request":
            _need(kind == "actions" and value == {key: request[key] for key in ("symbol", "start", "end")}, "effect_mismatch")
        elif role == "request":
            expected = actions._prepared_request(request) if kind == "actions" else data._prepared_request(request, kind)
            _need(value == expected, "effect_mismatch")
        elif role == "normalized":
            _need(value == self._normalized(request), "effect_mismatch")
        else:
            _need(type(value) is dict, "effect_mismatch")
            _need(re.fullmatch(r"[0-9a-f]{32}", value.get("submission_id", "")) is not None, "effect_mismatch")
            expected = (actions._receipt_base(value["submission_id"]) if kind == "actions"
                        else data._receipt_base(value["submission_id"], kind))
            varying = {"pagination_complete", "normalization_status"} if kind == "actions" else set()
            _need(all(value.get(key) == child for key, child in expected.items() if key not in varying), "effect_mismatch")
            allowed = set(expected) | {"request", "pages", "limitations", "started_at", "finished_at",
                "normalizer_sha256", "transport_sha256", "submitted_request_sha256", "request_sha256",
                "normalized_sha256", "status", "row_count", "error", "http_status", "categories_present", "unknown_categories"}
            _need(set(value) <= allowed and value.get("request") == request, "effect_mismatch")
            _need(value.get("limitations") == (actions._receipt_limitations() if kind == "actions" else data._receipt_limitations()), "effect_mismatch")
            _need(value.get("status") in {"success", "invalid", "failed"}, "effect_mismatch")
            _need(value.get("error") is None or value["error"] in data.ERRORS, "effect_mismatch")
            _need(value.get("http_status") is None or type(value["http_status"]) is int and 100 <= value["http_status"] <= 599, "effect_mismatch")
            for key in ("started_at", "finished_at"):
                if key in value:
                    _need(type(value[key]) is str and len(value[key]) <= 40 and datetime.fromisoformat(value[key]).utcoffset() is not None, "effect_mismatch")
            _need(value.get("normalizer_sha256") == self.source, "effect_mismatch")
            if kind == "actions":
                _need(value.get("transport_sha256") == hashlib.sha256(Path(data.__file__).read_bytes()).hexdigest(), "effect_mismatch")
                _need(type(value.get("pagination_complete")) is bool and value.get("normalization_status") in {"incomplete", "complete"}, "effect_mismatch")
            with self.intent.session.supervisor._db() as db:
                produced = {(role, digest) for role, digest in db.execute("SELECT role,digest FROM publications JOIN publication_ends USING(publication) WHERE producer=?", (self.identity,))}
                for key, role_name in (("submitted_request_sha256", "submitted_request"), ("request_sha256", "request"), ("normalized_sha256", "normalized")):
                    if key in value:
                        _need((role_name, value[key]) in produced, "effect_mismatch")
                pages = value.get("pages")
                _need(type(pages) is list and len(pages) <= len(self._responses), "effect_mismatch")
                for index, page in enumerate(pages):
                    effect, digest, body = self._responses[index]
                    _need(type(page) is dict and set(page) == {"page", "url", "retrieved_at", "http_status", "raw_sha256", "bytes"}, "effect_mismatch")
                    _need(page["page"] == index + 1 and page["http_status"] == 200 and page["bytes"] == len(body)
                          and page["raw_sha256"] == digest and ("response", digest) in produced, "effect_mismatch")
                    _need(request_identity("GET", page["url"]) == db.execute("SELECT identity FROM effects WHERE effect=?", (effect,)).fetchone()[0], "effect_mismatch")
                    _need(page["retrieved_at"] is None or type(page["retrieved_at"]) is str and len(page["retrieved_at"]) <= 40
                          and datetime.fromisoformat(page["retrieved_at"]).utcoffset() is not None, "effect_mismatch")
            if value["status"] == "success":
                normalized = self._normalized(request)
                _need(("normalized", value.get("normalized_sha256")) in produced and value.get("row_count") == len(normalized.get("bars", normalized.get("sessions", normalized.get("records", [])))), "effect_mismatch")
            if kind == "actions":
                present = set()
                for _, _, body in self._responses[:len(pages)]:
                    try:
                        _, categories, _ = actions._page(actions._json(body), "0" * 64, 1)
                        present.update(categories)
                    except data.AcquisitionError:
                        pass
                # Failed normalization may retain only the parsed prefix.
                _need(type(value.get("categories_present")) is list and set(value["categories_present"]) <= present, "effect_mismatch")
                _need(value.get("unknown_categories") == sorted(set(value["categories_present"]) - actions.CATEGORIES), "effect_mismatch")

    def permit(self, role, raw):
        """Freeze exact adapter-produced bytes and all real response origins.

        This capability belongs to the issued producer, never an ordinary intent.
        Response bytes must match a dispatched result. Data-derived publications
        require response origins; request-only failures retain request lineage.
        """
        session = self._check()
        _need(role in {"submitted_request", "request", "response", "normalized", "receipt"})
        _need(type(raw) is bytes and len(raw) <= 16 * 1024 * 1024)
        digest = hashlib.sha256(raw).hexdigest()
        origins = [effect for effect, _, _ in self._responses]
        if role == "response":
            origins = [effect for effect, recorded, body in self._responses if recorded == digest and body == raw]
            _need(origins, "effect_mismatch")
        if role == "normalized":
            _need(origins, "effect_uncertain")
        identity = uuid.uuid4().hex
        with session.supervisor._db() as db:
            document = json.loads(db.execute("SELECT request_document FROM intents WHERE intent=?", (self.intent.identity,)).fetchone()[0])
        try:
            self._validate_publication(role, raw, document)
        except (ValueError, TypeError, KeyError, IndexError):
            audit_refusal("publication", "effect_mismatch")
            raise AccessError("effect_mismatch") from None
        with session.supervisor._transaction() as db:
            session.supervisor._principal_active(db, session.principal)
            row = db.execute("SELECT coverage,revision,request_document FROM intents WHERE intent=? AND principal=? AND state='issued'",
                             (self.intent.identity, session.principal)).fetchone()
            _need(row and row[1] == session.supervisor._revision(db), "stale_identity_revision")
            _need(not db.execute("SELECT 1 FROM intent_ends WHERE intent=?", (self.intent.identity,)).fetchone(), "intent_closed")
            wide = db.execute("SELECT coverage FROM widenings WHERE intent=?", (self.intent.identity,)).fetchone()
            coverage = wide[0] if wide else row[0]
            for effect in origins:
                _need(db.execute("SELECT 1 FROM producer_responses WHERE effect=? AND producer=?", (effect, self.identity)).fetchone(), "effect_uncertain")
            db.execute("INSERT INTO publications VALUES (?,?,?,?,?,?,?)",
                       (identity, self.identity, role, digest, coverage, _json(origins), _now()))
            session.supervisor._event(db, "publication_issued", {"publication": identity, "producer": self.identity, "role": role})
        permit = PublicationPermit(self, identity, digest)
        session._publications[identity] = permit
        return permit


class PublicationPermit:
    def __init__(self, producer, identity, digest):
        self.producer, self.identity, self.digest = producer, identity, digest

    def consume(self, session, digest):
        self.producer._check()
        _need(session is self.producer.intent.session, "wrong_store")
        _need(session._publications.get(self.identity) is self, "authority_missing")
        with session.supervisor._transaction() as db:
            row = db.execute("SELECT p.digest,p.coverage,p.producer,i.coverage,i.revision,i.request_sha256 FROM publications p JOIN producers r ON r.producer=p.producer JOIN intents i ON i.intent=r.intent WHERE p.publication=?",
                             (self.identity,)).fetchone()
            _need(row and row[0] == digest == self.digest and row[2] == self.producer.identity, "effect_mismatch")
            _need(not db.execute("SELECT 1 FROM intent_ends WHERE intent=?", (self.producer.intent.identity,)).fetchone(), "intent_closed")
            _need(row[4] == session.supervisor._revision(db), "stale_identity_revision")
            session.supervisor._principal_active(db, session.principal)
            wide = db.execute("SELECT coverage FROM widenings WHERE intent=?", (self.producer.intent.identity,)).fetchone()
            current = wide[0] if wide else row[3]
            _need(row[1] == current, "stale_identity_revision")
            _need(not session.supervisor._conflicting_reservation(db, json.loads(current)), "reservation_conflict")
            _need(not db.execute("SELECT 1 FROM publication_ends WHERE publication=?", (self.identity,)).fetchone(), "already_consumed")
            previous = db.execute("SELECT coverage FROM classifications WHERE digest=?", (digest,)).fetchone()
            _need(previous is None or previous[0] == current, "classification_conflict")
            if previous is None:
                db.execute("INSERT INTO classifications VALUES (?,?,?,?)", (digest, current, row[5], _now()))
            db.execute("INSERT INTO publication_ends VALUES (?,?)", (self.identity, _now()))
            session.supervisor._event(db, "publication_started", {"publication": self.identity})
        session._publications.pop(self.identity, None)


def authorize_publication(session, raw, publication):
    digest = hashlib.sha256(raw).hexdigest()
    if publication is None:
        session.observe_import(digest)
    else:
        try:
            _need(type(publication) is PublicationPermit, "authority_missing")
            publication.consume(session, digest)
        except AccessError:
            # A bogus/stale producer label does not erase bytes already passed
            # into the ordinary publication API. Retain conservative exposure.
            session.observe_import(digest)
            raise


class EffectPermit:
    def __init__(self, intent, identity):
        self.intent, self.identity = intent, identity
        self._grant = None

    @contextmanager
    def start(self, operation, identity):
        session, supervisor = self.intent.session, self.intent.session.supervisor
        session.check()
        _digest(identity)
        reason, effect = None, uuid.uuid4().hex
        with supervisor._transaction() as db:
            try:
                supervisor._principal_active(db, session.principal)
            except AccessError as exc:
                reason = exc.reason
            row = db.execute("SELECT principal,operation,revision,state,request_sha256,coverage FROM intents WHERE intent=?", (self.intent.identity,)).fetchone()
            if reason:
                pass
            elif not row or row[0] != session.principal or row[3] != "issued":
                reason = "unknown_intent"
            elif operation != self.intent.operation or row[1] != operation or identity != self.identity:
                reason = "effect_mismatch"
            elif operation == "content_read" and row[4] != identity:
                reason = "effect_mismatch"
            elif operation == "provider_page" and not db.execute(
                    "SELECT 1 FROM permitted_pages WHERE intent=? AND identity=?",
                    (self.intent.identity, identity)).fetchone():
                reason = "effect_mismatch"
            elif db.execute("SELECT 1 FROM intent_ends WHERE intent=?", (self.intent.identity,)).fetchone():
                reason = "intent_closed"
            elif row[2] != supervisor._revision(db):
                reason = "stale_identity_revision"
            elif db.execute("SELECT 1 FROM effects WHERE intent=? AND identity=?", (self.intent.identity, identity)).fetchone():
                reason = "already_consumed"
            else:
                widened = db.execute("SELECT coverage FROM widenings WHERE intent=?", (self.intent.identity,)).fetchone()
                current = (supervisor._classification(db, row[4]) if operation == "content_read"
                           else json.loads(widened[0] if widened else row[5]))
                if supervisor._conflicting_reservation(db, current or Coverage("unknown").document()):
                    reason = "reservation_conflict"
            if reason:
                supervisor._event(db, "effect_refused", {"intent": self.intent.identity, "reason": reason})
            else:
                db.execute("INSERT INTO effects VALUES (?,?,?,?)", (effect, self.intent.identity, identity, _now()))
                supervisor._event(db, "effect_started", {"effect": effect, "intent": self.intent.identity})
        if reason:
            raise AccessError(reason)
        grant = _Grant(session, operation, identity, row[2], effect)
        with session._grant_lock:
            session._grants[effect] = (grant, operation, identity, row[2])
        self._grant = grant
        try:
            yield grant
        except BaseException:
            self._finish(effect, "uncertain")
            raise
        else:
            self._finish(effect, "completed")
        finally:
            with session._grant_lock:
                grant.active = False
                session._grants.pop(effect, None)

    def _finish(self, effect, state):
        supervisor = self.intent.session.supervisor
        with supervisor._transaction() as db:
            db.execute("INSERT INTO effect_ends VALUES (?,?,?)", (effect, state, _now()))
            supervisor._event(db, "effect_observed", {"effect": effect, "state": state})


class _Grant:
    def __init__(self, session, operation, identity, revision, effect):
        self.session, self.operation, self.identity = session, operation, identity
        self.revision, self.effect = revision, effect
        self.active, self.used = True, False

    def consume(self, operation, identity, *, network=False):
        with self.session._grant_lock:
            self.session.check()
            issued = self.session._grants.get(self.effect)
            _need(issued is not None and issued[0] is self, "unknown_intent")
            _need(self.session.cache_epoch()[2] == issued[3], "stale_identity_revision")
            _need(self.active and not self.used, "already_consumed")
            _need(issued[1:3] == (operation, identity), "effect_mismatch")
            _need(not network or not self.session.synthetic, "network_forbidden")
            del self.session._grants[self.effect]
            self.used = True

    def response(self, raw=None):
        self.session.check()
        _need(self.used, "effect_uncertain")
        with self.session.supervisor._db() as db:
            row = db.execute("SELECT e.intent FROM effects e JOIN intents i USING(intent) WHERE e.effect=? AND i.operation='provider_page' AND i.principal=?",
                             (self.effect, self.session.principal)).fetchone()
            _need(row, "unknown_intent")
        intent = AccessIntent(self.session, row[0], "provider_page")
        if raw is None:
            intent.widen_unknown()
        else:
            intent.observe_response(raw)


def consume_grant(grant, operation, identity, *, network=False):
    """Lower I/O boundary accepts only the exact live, supervisor-minted grant."""
    try:
        _need(type(grant) is _Grant, "authority_missing")
        grant.consume(operation, identity, network=network)
    except AccessError as exc:
        audit_refusal("grant", exc.reason)
        raise


def audit_refusal(operation, reason):
    """Record bounded route denial when an intact installed journal exists.

    Missing/unsafe authority cannot certify its own durable refusal; I/O still
    refuses and no rejected-without-access state is inferred from this helper.
    """
    _need(operation in {"page", "grant", "dispatch", "root", "publication"})
    _need(reason in REASONS)
    with _ACTIVE_LOCK:
        session = _ACTIVE
    if session is None:
        return
    session.check()
    with session.supervisor._transaction() as db:
        session.supervisor._event(db, "route_refused", {
            "operation": operation, "principal": session.principal, "reason": reason})


def current_session(root=None):
    with _ACTIVE_LOCK:
        session = _ACTIVE
    _need(session is not None, "authority_missing")
    try:
        session.check(root)
    except AccessError as exc:
        if exc.reason == "wrong_store":
            audit_refusal("root", exc.reason)
        raise
    return session


def request_identity(method, url):
    return _sha(_json({"method": method, "url": url}))

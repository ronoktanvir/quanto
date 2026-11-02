"""Durable research records, fenced work, and cooperating-client API spending.

The event chain supplies tamper evidence, not immutability. SQL triggers prevent
ordinary UPDATE/DELETE; a database owner can remove triggers or rewrite the whole
chain. Detecting a rewritten chain or truncated suffix requires a trusted external
checkpoint (the last event hash), backups, and access controls. No local ledger
can control calls made outside cooperating clients. Money is integer microUSD.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Callable, Iterator
import uuid
from zoneinfo import ZoneInfo

MAX_DAILY_MICRO_USD = 20_000_000
MAX_JSON_BYTES = 1_048_576
EVIDENCE_KINDS = frozenset({"synthetic_fixture", "historical_market_data", "prospective_paper", "live_execution"})
ATTEMPT_STATUSES = frozenset({"success", "failed", "invalid", "rejected"})
LA = ZoneInfo("America/Los_Angeles")


class LedgerError(ValueError):
    """A request violates the journal's data or state contract."""


class BudgetExceeded(LedgerError):
    """No budget remains, or a provider charge exceeded its reservation."""


class StaleLease(LedgerError):
    """A worker no longer holds the current, unexpired job lease."""


def canonical_json(value: Any) -> str:
    """Encode bounded, finite JSON deterministically, rejecting ambiguous keys."""
    def check(item: Any) -> None:
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise LedgerError("JSON object keys must be strings")
            for child in item.values():
                check(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                check(child)
        elif item is not None and not isinstance(item, (str, int, float, bool)):
            raise LedgerError("Value is not JSON serializable")
    try:
        check(value)
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        if len(encoded.encode("utf-8")) > MAX_JSON_BYTES:
            raise LedgerError("JSON exceeds maximum encoded size")
        return encoded
    except (ValueError, TypeError, RecursionError) as exc:
        raise LedgerError(str(exc)) from exc


def hash_bytes(value: bytes) -> str:
    """Return the SHA-256 identity of exact artifact bytes."""
    return hashlib.sha256(value).hexdigest()


def hash_json(value: Any) -> str:
    """Return SHA-256 of the canonical JSON representation."""
    return hash_bytes(canonical_json(value).encode("utf-8"))


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 4096:
        raise LedgerError(f"{name} must be a nonempty bounded string")
    return value


def _money(value: int) -> int:
    if type(value) is not int or not 0 <= value <= 9_000_000_000_000_000:
        raise LedgerError("Cost must be a nonnegative integer in microUSD")
    return value


_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY, occurred_at TEXT NOT NULL, kind TEXT NOT NULL,
 payload TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS experiments (
 fingerprint TEXT PRIMARY KEY, specification TEXT NOT NULL, data_identity TEXT NOT NULL,
 code_identity TEXT NOT NULL, evidence_kind TEXT NOT NULL, assumptions TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
 attempt_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL REFERENCES experiments(fingerprint),
 started_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS outcomes (
 attempt_id TEXT PRIMARY KEY REFERENCES attempts(attempt_id), status TEXT NOT NULL,
 result TEXT NOT NULL, finished_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
 review_id TEXT PRIMARY KEY, role TEXT NOT NULL, reviewer TEXT NOT NULL,
 producer TEXT NOT NULL, artifact_hash TEXT NOT NULL, verdict TEXT NOT NULL,
 findings TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reservations (
 request_id TEXT PRIMARY KEY, day TEXT NOT NULL, reserved_micro_usd INTEGER NOT NULL,
 actual_micro_usd INTEGER, state TEXT NOT NULL CHECK(state IN ('reserved','settled','uncertain')),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dispatches (
 request_id TEXT PRIMARY KEY REFERENCES reservations(request_id),
 day TEXT NOT NULL, authorized_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
 job_id TEXT PRIMARY KEY, payload TEXT NOT NULL, max_attempts INTEGER NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('pending','leased','complete','failed')),
 attempts INTEGER NOT NULL DEFAULT 0, fence INTEGER NOT NULL DEFAULT 0,
 worker_id TEXT, lease_until TEXT, result TEXT, created_at TEXT NOT NULL
);
"""


class Journal:
    """SQLite journal; create one instance per worker/thread.

    The injected clock must return timezone-aware datetimes. Dispatch accounting
    uses the Los Angeles day at authorization. A reservation from another day
    cannot authorize dispatch. Authorization cannot atomically guarantee the HTTP
    send instant or the provider's billing day. Timed-out calls retain their
    entire reservation until explicitly reconciled.
    """

    def __init__(self, path: str | Path, *, clock: Callable[[], datetime] | None = None,
                 daily_limit_micro_usd: int = MAX_DAILY_MICRO_USD):
        _money(daily_limit_micro_usd)
        if daily_limit_micro_usd > MAX_DAILY_MICRO_USD:
            raise LedgerError("The owner-authorized daily ceiling is USD 20")
        self.daily_limit_micro_usd = daily_limit_micro_usd
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.connection = sqlite3.connect(str(path), timeout=30, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        # Default rollback journaling: no WAL sidecar with uncheckpointed records.
        self.connection.execute("PRAGMA journal_mode=DELETE")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.executescript(_SCHEMA)
        for table in ("events", "experiments", "attempts", "outcomes", "reviews", "dispatches"):
            for operation in ("UPDATE", "DELETE"):
                self.connection.execute(
                    f"CREATE TRIGGER IF NOT EXISTS no_{operation.lower()}_{table} "
                    f"BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT, 'append-only record'); END"
                )

    def __enter__(self) -> Journal:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def _now(self) -> datetime:
        now = self.clock()
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise LedgerError("Clock must return a timezone-aware datetime")
        return now.astimezone(timezone.utc)

    @staticmethod
    def _stamp(now: datetime) -> str:
        return now.isoformat(timespec="microseconds")

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.connection.execute("COMMIT")
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise

    def _event(self, kind: str, payload: Any, now: datetime) -> str:
        last = self.connection.execute("SELECT id,event_hash FROM events ORDER BY id DESC LIMIT 1").fetchone()
        event_id, previous = (last["id"] + 1, last["event_hash"]) if last else (1, "0" * 64)
        stamp, encoded = self._stamp(now), canonical_json(payload)
        identity = hash_json({"id": event_id, "occurred_at": stamp, "kind": kind,
                              "payload": json.loads(encoded), "previous_hash": previous})
        self.connection.execute("INSERT INTO events VALUES (?,?,?,?,?,?)", (event_id, stamp, kind, encoded, previous, identity))
        return identity

    def append_event(self, kind: str, payload: Any) -> str:
        _text(kind, "kind")
        with self._transaction():
            return self._event(kind, payload, self._now())

    def verify_events(self, expected_head: str | None = None) -> dict[str, Any]:
        """Raise on chain damage or checkpoint mismatch; return count and head.

        Without an external expected_head, suffix deletion or a complete rewrite
        cannot be detected. This verifies events, not arbitrary materialized tables.
        """
        previous, count = "0" * 64, 0
        for row in self.connection.execute("SELECT * FROM events ORDER BY id"):
            count += 1
            try:
                expected = hash_json({"id": row["id"], "occurred_at": row["occurred_at"], "kind": row["kind"],
                                      "payload": json.loads(row["payload"]), "previous_hash": previous})
            except (ValueError, LedgerError) as exc:
                raise LedgerError(f"Invalid event {row['id']}") from exc
            if row["id"] != count or row["previous_hash"] != previous or row["event_hash"] != expected:
                raise LedgerError(f"Event chain damaged at event {row['id']}")
            previous = row["event_hash"]
        if expected_head is not None and previous != expected_head:
            raise LedgerError("Event head does not match external checkpoint")
        return {"count": count, "head": previous}

    def register_experiment(self, specification: Any, data_identity: Any, code_identity: Any,
                            evidence_kind: str, assumptions: Any = None) -> str:
        """Persist exact identities; duplicate registrations return one fingerprint."""
        if evidence_kind not in EVIDENCE_KINDS:
            raise LedgerError("Unsupported evidence kind")
        if data_identity is None or code_identity is None:
            raise LedgerError("Data and code identities are required")
        record = {"specification": specification, "data_identity": data_identity,
                  "code_identity": code_identity, "evidence_kind": evidence_kind,
                  "assumptions": {} if assumptions is None else assumptions}
        fingerprint = hash_json(record)
        with self._transaction():
            if self.connection.execute("SELECT 1 FROM experiments WHERE fingerprint=?", (fingerprint,)).fetchone() is None:
                now = self._now()
                self.connection.execute("INSERT INTO experiments VALUES (?,?,?,?,?,?,?)", (
                    fingerprint, canonical_json(specification), canonical_json(data_identity), canonical_json(code_identity),
                    evidence_kind, canonical_json(record["assumptions"]), self._stamp(now)))
                self._event("experiment_registered", {"fingerprint": fingerprint, **record}, now)
        return fingerprint

    def start_attempt(self, fingerprint: str) -> str:
        attempt_id = uuid.uuid4().hex
        with self._transaction():
            now = self._now()
            self.connection.execute("INSERT INTO attempts VALUES (?,?,?)", (attempt_id, fingerprint, self._stamp(now)))
            self._event("attempt_started", {"attempt_id": attempt_id, "fingerprint": fingerprint}, now)
        return attempt_id

    def finish_attempt(self, attempt_id: str, status: str, result: Any = None) -> None:
        """Append an outcome, retaining failed, invalid and rejected attempts."""
        if status not in ATTEMPT_STATUSES:
            raise LedgerError("Unsupported attempt outcome")
        result = {} if result is None else result
        encoded = canonical_json(result)
        with self._transaction():
            now = self._now()
            self.connection.execute("INSERT INTO outcomes VALUES (?,?,?,?)", (attempt_id, status, encoded, self._stamp(now)))
            self._event("attempt_finished", {"attempt_id": attempt_id, "status": status, "result": result}, now)

    def record_review(self, role: str, reviewer: str, producer: str, artifact_hash: str,
                      verdict: str, findings: Any) -> str:
        """Record an attributed review of exact artifact bytes, separate from production.

        Distinct supplied identities are required; caller authentication and genuine
        independence remain orchestration responsibilities, not established here.
        """
        for name, value in (("role", role), ("reviewer", reviewer), ("producer", producer), ("verdict", verdict)):
            _text(value, name)
        if reviewer.strip().casefold() == producer.strip().casefold():
            raise LedgerError("A producer cannot independently review its own artifact")
        if not isinstance(artifact_hash, str) or len(artifact_hash) != 64 or any(c not in "0123456789abcdef" for c in artifact_hash):
            raise LedgerError("artifact_hash must identify exact artifact bytes with SHA-256")
        encoded, review_id = canonical_json(findings), uuid.uuid4().hex
        with self._transaction():
            now = self._now()
            self.connection.execute("INSERT INTO reviews VALUES (?,?,?,?,?,?,?,?)", (
                review_id, role, reviewer, producer, artifact_hash, verdict, encoded, self._stamp(now)))
            self._event("review_recorded", {"review_id": review_id, "role": role, "reviewer": reviewer,
                        "producer": producer, "artifact_hash": artifact_hash, "verdict": verdict, "findings": findings}, now)
        return review_id

    def _budget(self, day: str) -> dict[str, Any]:
        rows = self.connection.execute("SELECT * FROM reservations WHERE day=?", (day,)).fetchall()
        committed = sum(row["actual_micro_usd"] if row["state"] == "settled" else
                        max(row["reserved_micro_usd"], row["actual_micro_usd"] or 0) for row in rows)
        return {"day": day, "limit_micro_usd": self.daily_limit_micro_usd,
                "committed_micro_usd": committed, "remaining_micro_usd": max(0, self.daily_limit_micro_usd - committed),
                "reserved_count": sum(r["state"] == "reserved" for r in rows),
                "uncertain_count": sum(r["state"] == "uncertain" for r in rows),
                "settled_count": sum(r["state"] == "settled" for r in rows)}

    def budget_snapshot(self, day: str | None = None) -> dict[str, Any]:
        return self._budget(day or self._now().astimezone(LA).date().isoformat())

    def reserve(self, request_id: str, max_micro_usd: int) -> dict[str, Any]:
        """Atomically hold budget; request IDs are globally idempotent.

        A repeated ID returns its existing state. No reservation return value
        authorizes a call. The sender must call authorize_dispatch immediately
        before the network operation, even when created is True.
        """
        _text(request_id, "request_id")
        _money(max_micro_usd)
        if max_micro_usd == 0:
            raise LedgerError("External requests require a positive conservative reservation")
        with self._transaction():
            existing = self.connection.execute("SELECT * FROM reservations WHERE request_id=?", (request_id,)).fetchone()
            if existing:
                if existing["reserved_micro_usd"] != max_micro_usd:
                    raise LedgerError("Idempotent request changed its reservation")
                return {**dict(existing), "created": False}
            now = self._now()
            day = now.astimezone(LA).date().isoformat()
            if self._budget(day)["committed_micro_usd"] + max_micro_usd > self.daily_limit_micro_usd:
                raise BudgetExceeded("Daily API budget would be exceeded")
            stamp = self._stamp(now)
            self.connection.execute("INSERT INTO reservations VALUES (?,?,?,NULL,'reserved',?,?)", (request_id, day, max_micro_usd, stamp, stamp))
            self._event("budget_reserved", {"request_id": request_id, "day": day, "max_micro_usd": max_micro_usd}, now)
            return {**dict(self.connection.execute("SELECT * FROM reservations WHERE request_id=?", (request_id,)).fetchone()), "created": True}

    def authorize_dispatch(self, request_id: str) -> dict[str, str]:
        """Consume one current-day authorization immediately before network send.

        The authorization is durably recorded before return. Repeats fail even
        after a crash, timeout, or unsuccessful send; recovery must reconcile
        the existing hold and reserve a unique ID for any new request. Older-day
        reservations retain their hold but cannot authorize a later-day call.
        Accounting day is this authorization's Los Angeles day, which cannot
        guarantee the actual HTTP-send or provider-billing day.
        """
        _text(request_id, "request_id")
        with self._transaction():
            now = self._now()
            day = now.astimezone(LA).date().isoformat()
            row = self.connection.execute("SELECT * FROM reservations WHERE request_id=?", (request_id,)).fetchone()
            if row is None or row["state"] != "reserved":
                raise LedgerError("Dispatch requires a reserved request")
            if row["day"] != day:
                raise LedgerError("Reservation expired at Los Angeles midnight; use a unique request ID")
            if self.connection.execute("SELECT 1 FROM dispatches WHERE request_id=?", (request_id,)).fetchone():
                raise LedgerError("Dispatch was already authorized; repeating the request is forbidden")
            authorization = {"request_id": request_id, "day": day, "authorized_at": self._stamp(now)}
            self.connection.execute("INSERT INTO dispatches VALUES (?,?,?)", (
                request_id, day, authorization["authorized_at"]))
            self._event("dispatch_authorized", authorization, now)
            return authorization

    def mark_uncertain(self, request_id: str, reason: str) -> None:
        """Preserve the full hold after timeout; never automatically release it."""
        _text(reason, "reason")
        with self._transaction():
            row = self.connection.execute("SELECT * FROM reservations WHERE request_id=?", (request_id,)).fetchone()
            if row is None or row["state"] == "settled":
                raise LedgerError("Only an unsettled reservation can become uncertain")
            now = self._now()
            self.connection.execute("UPDATE reservations SET state='uncertain',updated_at=? WHERE request_id=?", (self._stamp(now), request_id))
            self._event("budget_uncertain", {"request_id": request_id, "reason": reason}, now)

    def settle(self, request_id: str, actual_micro_usd: int) -> None:
        """Reconcile known cost. Overage is durably flagged, retained, then raised."""
        _money(actual_micro_usd)
        overage = False
        with self._transaction():
            row = self.connection.execute("SELECT * FROM reservations WHERE request_id=?", (request_id,)).fetchone()
            if row is None:
                raise LedgerError("A call must have a reservation before settlement")
            if row["state"] == "settled":
                if row["actual_micro_usd"] != actual_micro_usd:
                    raise LedgerError("A settled charge cannot change")
                return
            now = self._now()
            overage = actual_micro_usd > row["reserved_micro_usd"]
            # Never lower a previously observed overage using a later smaller value.
            if row["actual_micro_usd"] is not None and actual_micro_usd < row["actual_micro_usd"]:
                raise LedgerError("A recorded uncertain charge cannot be reduced")
            state = "uncertain" if overage else "settled"
            self.connection.execute("UPDATE reservations SET state=?,actual_micro_usd=?,updated_at=? WHERE request_id=?", (state, actual_micro_usd, self._stamp(now), request_id))
            self._event("budget_overage" if overage else "budget_settled", {"request_id": request_id, "actual_micro_usd": actual_micro_usd}, now)
        if overage:
            raise BudgetExceeded("Provider charge exceeded reservation; charge retained as uncertain")

    def enqueue_job(self, job_id: str, payload: Any, *, max_attempts: int = 3) -> str:
        _text(job_id, "job_id")
        if type(max_attempts) is not int or not 1 <= max_attempts <= 100:
            raise LedgerError("max_attempts must be between 1 and 100")
        encoded = canonical_json(payload)
        with self._transaction():
            existing = self.connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if existing:
                if existing["payload"] != encoded or existing["max_attempts"] != max_attempts:
                    raise LedgerError("Idempotent job ID changed content")
                return job_id
            now = self._now()
            self.connection.execute("INSERT INTO jobs(job_id,payload,max_attempts,state,created_at) VALUES (?,?,?,'pending',?)", (job_id, encoded, max_attempts, self._stamp(now)))
            self._event("job_enqueued", {"job_id": job_id, "payload": payload, "max_attempts": max_attempts}, now)
        return job_id

    def claim_job(self, worker_id: str, *, lease_seconds: int = 60) -> dict[str, Any] | None:
        """Claim one job atomically, reclaiming expired work with a new fence."""
        _text(worker_id, "worker_id")
        if type(lease_seconds) is not int or not 1 <= lease_seconds <= 86_400:
            raise LedgerError("lease_seconds must be between 1 and 86400")
        with self._transaction():
            now = self._now()
            stamp = self._stamp(now)
            candidates = self.connection.execute("SELECT * FROM jobs WHERE state='pending' OR (state='leased' AND lease_until<=?) ORDER BY created_at,job_id", (stamp,)).fetchall()
            for row in candidates:
                if row["attempts"] >= row["max_attempts"]:
                    self.connection.execute("UPDATE jobs SET state='failed',worker_id=NULL,lease_until=NULL WHERE job_id=?", (row["job_id"],))
                    self._event("job_exhausted", {"job_id": row["job_id"], "fence": row["fence"]}, now)
                    continue
                fence, attempt = row["fence"] + 1, row["attempts"] + 1
                until = self._stamp(now + timedelta(seconds=lease_seconds))
                self.connection.execute("UPDATE jobs SET state='leased',worker_id=?,lease_until=?,fence=?,attempts=? WHERE job_id=?", (worker_id, until, fence, attempt, row["job_id"]))
                self._event("job_claimed", {"job_id": row["job_id"], "worker_id": worker_id, "fence": fence, "attempt": attempt, "lease_until": until}, now)
                claimed = dict(self.connection.execute("SELECT * FROM jobs WHERE job_id=?", (row["job_id"],)).fetchone())
                claimed["payload"] = json.loads(claimed["payload"])
                return claimed
        return None

    def _leased(self, job_id: str, worker_id: str, fence: int, now: datetime) -> sqlite3.Row:
        row = self.connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None or row["state"] != "leased" or row["worker_id"] != worker_id or row["fence"] != fence or row["lease_until"] <= self._stamp(now):
            raise StaleLease("Worker lease is expired, replaced, or already complete")
        return row

    def complete_job(self, job_id: str, worker_id: str, fence: int, result: Any = None) -> None:
        result = {} if result is None else result
        encoded = canonical_json(result)
        with self._transaction():
            now = self._now()
            self._leased(job_id, worker_id, fence, now)
            self.connection.execute("UPDATE jobs SET state='complete',result=?,worker_id=NULL,lease_until=NULL WHERE job_id=?", (encoded, job_id))
            self._event("job_completed", {"job_id": job_id, "worker_id": worker_id, "fence": fence, "result": result}, now)

    def fail_job(self, job_id: str, worker_id: str, fence: int, reason: str, *, retryable: bool = False) -> None:
        _text(reason, "reason")
        if type(retryable) is not bool:
            raise LedgerError("retryable must be boolean")
        with self._transaction():
            now = self._now()
            row = self._leased(job_id, worker_id, fence, now)
            state = "pending" if retryable and row["attempts"] < row["max_attempts"] else "failed"
            self.connection.execute("UPDATE jobs SET state=?,result=?,worker_id=NULL,lease_until=NULL WHERE job_id=?", (state, canonical_json({"reason": reason}), job_id))
            self._event("job_failed", {"job_id": job_id, "worker_id": worker_id, "fence": fence, "reason": reason, "state": state}, now)

    def overview(self) -> dict[str, Any]:
        """Read persisted counts without manufacturing research or review evidence."""
        with self._transaction():
            counts = {table: self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                      for table in ("events", "experiments", "attempts", "outcomes", "reviews", "jobs")}
            counts["attempt_statuses"] = {r["status"]: r["n"] for r in self.connection.execute("SELECT status,COUNT(*) n FROM outcomes GROUP BY status")}
            counts["unfinished_attempts"] = counts["attempts"] - counts["outcomes"]
            counts["job_states"] = {r["state"]: r["n"] for r in self.connection.execute("SELECT state,COUNT(*) n FROM jobs GROUP BY state")}
            counts["evidence_kinds"] = {r["evidence_kind"]: r["n"] for r in self.connection.execute("SELECT evidence_kind,COUNT(*) n FROM experiments GROUP BY evidence_kind")}
            counts["budget"] = self.budget_snapshot()
            counts["event_chain"] = self.verify_events()
            return counts

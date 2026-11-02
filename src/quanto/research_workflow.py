"""Proposed D008's first, development-only role-state increment.

This service does not dispatch models, execute studies, authorize spending, or
certify research. The trusted supervisor admits only sanitized development JSON
artifacts in a frozen manifest. Content screening supplements that admission; it
cannot establish data rights or recognize every private value. These are controls
for cooperating same-user callers, not OS isolation or protection from an owner.

API: ``create_run(manifest)``; ``issue_stage(run_id, role)`` (returns a private
token once); ``claim_stage(token, worker_id)``; ``authorize_intent(...)``;
``start_intent(...)`` immediately before the broker's effect;
``finish_intent(...)``; ``finish_handoff(...)``. All worker calls derive actor
identity from the token. Callers cannot supply authors or reviewer identities.
``authenticate_capability`` supplies metadata, not execution authorization.

Intents use exactly request_id/action/input_refs. Authorization is idempotent;
start is one-use. External accounting reservations and dispatch authorization
remain the dispatcher's responsibility, in addition to this workflow fence.
An authorized intent has not crossed its effect boundary; a started intent has,
even if no result was retained. Cancellation or expired leases with started
effects are uncertain and never automatically retried. A live lease may finish
several successful intents but cannot retry a failed/invalid/uncertain effect.

Handoffs use exactly state/artifact_refs/reviewed_refs/assumptions/objections/
next_action. Complete means proceed; blocked means stop. A reviewer's reviewed
references must equal its complete issued input set. Stored handoffs add issued
identity and exact upstream handoff references, and are append-only records.
Verified bytes and handoff/job terminal records share a journal transaction;
content objects orphaned by rollback are not a published handoff. Lost private
tokens cannot be recovered: cancel that run and explicitly create a new lineage.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from functools import wraps
import hashlib
import hmac
import json
import re
import secrets
from typing import Callable
import uuid

from quanto.ledger import LedgerError, StaleLease, canonical_json, hash_json
from quanto.provenance import Provenance, ProvenanceError

ROLES = (
    "director", "hypothesis", "engineer", "data_critic", "statistical_critic", "quality", "scope"
)
REVIEW_ROLES = frozenset(ROLES[3:])
ROLE_ACTIONS = {
    "director": frozenset({"inspect_development", "query_failures", "dispatch_model"}),
    "hypothesis": frozenset({"inspect_development", "query_failures", "dispatch_model"}),
    "engineer": frozenset({"inspect_development", "validate_specification",
                           "launch_development", "dispatch_model"}),
    "data_critic": frozenset({"inspect_development", "validate_specification",
                              "submit_review", "dispatch_model"}),
    "statistical_critic": frozenset({"inspect_development", "query_failures",
                                     "submit_review", "dispatch_model"}),
    "quality": frozenset({"inspect_development", "validate_specification",
                          "submit_review", "dispatch_model"}),
    "scope": frozenset({"inspect_development", "submit_review", "dispatch_model"}),
}
_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,95}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_TOKEN = re.compile(r"[A-Za-z0-9_-]{43}\Z")
_SECRET = re.compile(
    r"sk-(?:ant-)?[A-Za-z0-9_-]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"(?i:authorization\s*:\s*bearer|(?:api[_-]?key|access[_-]?token|password)\s*[\"']?\s*[=:])"
)
_TABLES = (
    "workflow_runs", "workflow_assignments", "workflow_claims", "workflow_claim_ends",
    "workflow_intents", "workflow_effect_starts", "workflow_effect_outcomes",
    "workflow_handoffs", "workflow_terminals", "workflow_cancellations",
)
_SCHEMA = """
CREATE TABLE IF NOT EXISTS workflow_runs (
 run_id TEXT PRIMARY KEY, run_key TEXT NOT NULL UNIQUE, manifest TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workflow_assignments (
 assignment_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES workflow_runs(run_id),
 role TEXT NOT NULL, actor_id TEXT NOT NULL UNIQUE, token_hash TEXT NOT NULL UNIQUE,
 contract TEXT NOT NULL, input_refs TEXT NOT NULL, upstream_handoffs TEXT NOT NULL,
 job_id TEXT NOT NULL UNIQUE REFERENCES jobs(job_id), created_at TEXT NOT NULL,
 UNIQUE(run_id, role)
);
CREATE TABLE IF NOT EXISTS workflow_claims (
 claim_id TEXT PRIMARY KEY, assignment_id TEXT NOT NULL REFERENCES workflow_assignments,
 fence INTEGER NOT NULL, worker_id TEXT NOT NULL, deadline TEXT NOT NULL,
 created_at TEXT NOT NULL, UNIQUE(assignment_id, fence)
);
CREATE TABLE IF NOT EXISTS workflow_claim_ends (
 assignment_id TEXT NOT NULL REFERENCES workflow_assignments, fence INTEGER NOT NULL,
 state TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(assignment_id,fence)
);
CREATE TABLE IF NOT EXISTS workflow_intents (
 assignment_id TEXT NOT NULL REFERENCES workflow_assignments, request_id TEXT NOT NULL,
 fence INTEGER NOT NULL, action TEXT NOT NULL, input_refs TEXT NOT NULL,
 created_at TEXT NOT NULL, PRIMARY KEY(assignment_id,request_id)
);
CREATE TABLE IF NOT EXISTS workflow_effect_starts (
 assignment_id TEXT NOT NULL, request_id TEXT NOT NULL, created_at TEXT NOT NULL,
 PRIMARY KEY(assignment_id,request_id), FOREIGN KEY(assignment_id,request_id)
 REFERENCES workflow_intents(assignment_id,request_id)
);
CREATE TABLE IF NOT EXISTS workflow_effect_outcomes (
 assignment_id TEXT NOT NULL, request_id TEXT NOT NULL, status TEXT NOT NULL,
 artifact_refs TEXT NOT NULL, observed_model TEXT, created_at TEXT NOT NULL,
 PRIMARY KEY(assignment_id,request_id), FOREIGN KEY(assignment_id,request_id)
 REFERENCES workflow_effect_starts(assignment_id,request_id)
);
CREATE TABLE IF NOT EXISTS workflow_handoffs (
 assignment_id TEXT PRIMARY KEY REFERENCES workflow_assignments,
 document_sha256 TEXT NOT NULL, document TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workflow_terminals (
 assignment_id TEXT PRIMARY KEY REFERENCES workflow_assignments,
 state TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workflow_cancellations (
 run_id TEXT PRIMARY KEY REFERENCES workflow_runs, reason TEXT NOT NULL,
 created_at TEXT NOT NULL
);
"""


class WorkflowError(LedgerError):
    """A fixed role contract or durable transition was refused."""


def _object(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise WorkflowError("Object fields do not match the fixed schema")


def _identifier(value):
    if not isinstance(value, str) or not _ID.fullmatch(value) or _SECRET.search(value):
        raise WorkflowError("Expected a bounded non-secret identifier")
    return value


def _sha(value):
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        raise WorkflowError("Expected an exact SHA-256 reference")
    return value


def _refs(value):
    if type(value) is not list or len(value) > 128:
        raise WorkflowError("References must be a bounded list")
    for item in value:
        _sha(item)
    if len(set(value)) != len(value):
        raise WorkflowError("Duplicate artifact reference")
    return sorted(value)


def _texts(value):
    if type(value) is not list or len(value) > 32:
        raise WorkflowError("Expected bounded text list")
    for item in value:
        if (not isinstance(item, str) or not item.strip() or len(item) > 1024
                or _SECRET.search(item)):
            raise WorkflowError("Text is invalid or contains a credential pattern")


def _record_denial(method):
    @wraps(method)
    def checked(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except (LedgerError, TypeError):
            self._deny(method.__name__)
            raise
    return checked


class ResearchWorkflow:
    """One instance/Provenance connection per cooperating worker or thread."""

    def __init__(self, store: Provenance, *, clock: Callable[[], datetime] | None = None):
        self.store = store
        self.journal = store._open()
        if clock is not None:
            self.journal.clock = clock
        self.db = self.journal.connection
        self.db.executescript(_SCHEMA)
        for table in _TABLES:
            for operation in ("UPDATE", "DELETE"):
                self.db.execute(
                    f"CREATE TRIGGER IF NOT EXISTS no_{operation.lower()}_{table} "
                    f"BEFORE {operation} ON {table} BEGIN "
                    "SELECT RAISE(ABORT, 'append-only record'); END"
                )

    def _event(self, kind, payload, now):
        self.journal._event("workflow_" + kind, payload, now)

    def _deny(self, operation):
        # Never persist raw tokens, worker text, malformed requests or exceptions.
        self.journal.append_event("workflow_denied", {"operation": operation})

    def _screen(self, value):
        """Refuse recognizable credentials and exact issued secrets, even embedded.

        Tokens are never recoverable from storage. Hash bounded candidate windows
        instead of keeping raw credentials for redaction. This detects issued
        token disclosure; it is not a general private-data classifier.
        """
        if len(value.encode("utf-8")) > 65_536:
            raise WorkflowError("Screened value exceeds workflow byte bound")
        if _SECRET.search(value):
            raise WorkflowError("Value contains a credential pattern")
        candidates = set()
        for segment in re.findall(r"[A-Za-z0-9_-]{43,}", value):
            for offset in range(len(segment) - 42):
                candidate = segment[offset:offset + 43]
                candidates.add(hashlib.sha256(candidate.encode()).hexdigest())
        # Indexed, bounded batches avoid scanning the full assignment history.
        candidates = list(candidates)
        for offset in range(0, len(candidates), 256):
            batch = candidates[offset:offset + 256]
            found = self.db.execute(
                "SELECT 1 FROM workflow_assignments WHERE token_hash IN ("
                + ",".join("?" for _ in batch) + ") LIMIT 1", batch
            ).fetchone()
            if found:
                raise WorkflowError("Value contains an issued capability secret")

    def _run(self, run_id):
        _sha(run_id)
        row = self.db.execute("SELECT * FROM workflow_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise WorkflowError("Unknown run")
        return row

    def _assignment(self, token):
        if not isinstance(token, str) or not _TOKEN.fullmatch(token):
            raise WorkflowError("Invalid capability")
        digest = hashlib.sha256(token.encode()).hexdigest()
        row = self.db.execute(
            "SELECT * FROM workflow_assignments WHERE token_hash=?", (digest,)
        ).fetchone()
        if row is None or not hmac.compare_digest(row["token_hash"], digest):
            raise WorkflowError("Invalid capability")
        return row

    def _active(self, assignment):
        if self.db.execute("SELECT 1 FROM workflow_cancellations WHERE run_id=?",
                           (assignment["run_id"],)).fetchone():
            raise WorkflowError("Run is cancelled")
        if self.db.execute("SELECT 1 FROM workflow_terminals WHERE assignment_id=?",
                           (assignment["assignment_id"],)).fetchone():
            raise WorkflowError("Stage is terminal")

    def _leased(self, token, worker_id, fence, now):
        _identifier(worker_id)
        if type(fence) is not int or fence < 1:
            raise StaleLease("Invalid fence")
        assignment = self._assignment(token)
        self._active(assignment)
        self.journal._leased(assignment["job_id"], worker_id, fence, now)
        claim = self.db.execute(
            "SELECT deadline FROM workflow_claims WHERE assignment_id=? AND fence=?",
            (assignment["assignment_id"], fence),
        ).fetchone()
        if claim is None or claim["deadline"] <= self.journal._stamp(now):
            raise StaleLease("Stage time bound exhausted")
        return assignment

    def _verify_refs(self, refs, maximum):
        count = 0
        for digest in refs:
            try:
                raw = self.store.read_bytes(digest)
                value = self.store.read_json(digest)
            except ProvenanceError:
                raise WorkflowError("Artifact unavailable or not strict JSON") from None
            count += len(raw)
            if count > maximum:
                raise WorkflowError("Artifacts exceed the frozen byte bound")
            # No path resolution or opaque binary payloads at the worker boundary.
            self._screen(canonical_json(value))

    @staticmethod
    def _contract(contract):
        keys = {"policy_version", "backend", "requested_model", "prompt_sha256",
                "context_schema", "output_schema", "max_steps", "max_seconds",
                "max_input_bytes", "max_output_bytes", "max_spend_micro_usd", "max_claims"}
        _object(contract, keys)
        for key in ("policy_version", "requested_model"):
            _identifier(contract[key])
        if (contract["backend"] not in ("synthetic", "anthropic_text")
                or contract["context_schema"] != "research_context.v1"
                or contract["output_schema"] != "research_handoff.v1"):
            raise WorkflowError("Unsupported role backend or schema")
        _sha(contract["prompt_sha256"])
        bounds = {"max_steps": (1, 32), "max_seconds": (1, 3600),
                  "max_input_bytes": (1, 65_536), "max_output_bytes": (1, 65_536),
                  "max_spend_micro_usd": (0, 4_000_000), "max_claims": (1, 3)}
        for key, (low, high) in bounds.items():
            if type(contract[key]) is not int or not low <= contract[key] <= high:
                raise WorkflowError("Role bound is invalid")
        if contract["backend"] == "synthetic" and contract["max_spend_micro_usd"]:
            raise WorkflowError("Synthetic roles cannot request paid dispatch")

    @_record_denial
    def create_run(self, manifest):
        """Freeze exact supervisor-admitted inputs; repeat run_key/content is idempotent.

        Manifest fields: run_key, access_class='sanitized_development', evidence_kind
        (synthetic_fixture/historical_market_data), code_sha256, specification_sha256,
        input_refs (strict JSON digests), and roles (exact ROLES → frozen contracts).
        This is a privileged supervisor API; role capabilities cannot call it.
        """
        _object(manifest, {"run_key", "access_class", "evidence_kind", "code_sha256",
                           "specification_sha256", "input_refs", "roles"})
        _identifier(manifest["run_key"])
        if (manifest["access_class"] != "sanitized_development"
                or manifest["evidence_kind"] not in ("synthetic_fixture", "historical_market_data")):
            raise WorkflowError("Only admitted sanitized development evidence is supported")
        _sha(manifest["code_sha256"])
        _sha(manifest["specification_sha256"])
        refs = _refs(manifest["input_refs"])
        _object(manifest["roles"], ROLES)
        for contract in manifest["roles"].values():
            self._contract(contract)
        encoded = canonical_json(manifest)
        run_id = hash_json(manifest)
        with self.journal._transaction():
            self._screen(encoded)
            self._verify_refs(refs, min(c["max_input_bytes"] for c in manifest["roles"].values()))
            existing = self.db.execute("SELECT * FROM workflow_runs WHERE run_key=?",
                                       (manifest["run_key"],)).fetchone()
            if existing:
                if existing["manifest"] != encoded:
                    raise WorkflowError("Run idempotency key changed its frozen content")
                return existing["run_id"]
            now = self.journal._now()
            self.db.execute("INSERT INTO workflow_runs VALUES (?,?,?,?)",
                            (run_id, manifest["run_key"], encoded, self.journal._stamp(now)))
            self._event("run_created", {"run_id": run_id, "manifest": manifest}, now)
        return run_id

    @_record_denial
    def issue_stage(self, run_id, role):
        """Privileged supervisor issues one assignment, after all upstream complete."""
        if role not in ROLES:
            raise WorkflowError("Unknown fixed role")
        with self.journal._transaction():
            run = self._run(run_id)
            manifest = json.loads(run["manifest"])
            if self.db.execute("SELECT 1 FROM workflow_cancellations WHERE run_id=?",
                               (run_id,)).fetchone():
                raise WorkflowError("Run is cancelled")
            if self.db.execute("SELECT 1 FROM workflow_assignments WHERE run_id=? AND role=?",
                               (run_id, role)).fetchone():
                raise WorkflowError("Assignment already issued; private tokens are returned once")
            upstream, refs = [], set(manifest["input_refs"])
            for prior in ROLES[:ROLES.index(role)]:
                row = self.db.execute(
                    "SELECT h.* FROM workflow_handoffs h JOIN workflow_assignments a "
                    "USING(assignment_id) WHERE a.run_id=? AND a.role=?", (run_id, prior)
                ).fetchone()
                if row is None or json.loads(row["document"])["state"] != "complete":
                    raise WorkflowError("Upstream complete handoff required")
                upstream.append(row["document_sha256"])
                refs.add(row["document_sha256"])
                refs.update(json.loads(row["document"])["artifact_refs"])
            contract = manifest["roles"][role]
            self._verify_refs(sorted(refs), contract["max_input_bytes"])
            token, assignment_id, actor_id = secrets.token_urlsafe(32), uuid.uuid4().hex, uuid.uuid4().hex
            job_id = "workflow:" + assignment_id
            now = self.journal._now()
            stamp = self.journal._stamp(now)
            self.db.execute(
                "INSERT INTO jobs(job_id,payload,max_attempts,state,created_at) VALUES (?,?,?,'pending',?)",
                (job_id, canonical_json({"assignment_id": assignment_id}), contract["max_claims"], stamp)
            )
            self.db.execute("INSERT INTO workflow_assignments VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (assignment_id, run_id, role, actor_id,
                             hashlib.sha256(token.encode()).hexdigest(), canonical_json(contract),
                             canonical_json(sorted(refs)), canonical_json(upstream), job_id, stamp))
            self._event("assignment_issued", {"assignment_id": assignment_id, "run_id": run_id,
                                              "role": role, "actor_id": actor_id,
                                              "input_refs": sorted(refs), "contract": contract}, now)
            return {**self._metadata(self._assignment(token)), "token": token}

    @staticmethod
    def _metadata(row):
        return {key: json.loads(row[key]) if key in ("contract", "input_refs", "upstream_handoffs")
                else row[key] for key in ("assignment_id", "run_id", "role", "actor_id",
                                         "job_id", "contract", "input_refs", "upstream_handoffs")}

    @_record_denial
    def authenticate_capability(self, token):
        with self.journal._transaction():
            row = self._assignment(token)
            self._active(row)
            return self._metadata(row)

    def _terminal(self, assignment, state, reason, now):
        self.db.execute("INSERT INTO workflow_terminals VALUES (?,?,?,?)",
                        (assignment["assignment_id"], state, reason, self.journal._stamp(now)))
        self.db.execute("UPDATE jobs SET state='failed',worker_id=NULL,lease_until=NULL WHERE job_id=?",
                        (assignment["job_id"],))
        self._event("stage_terminal", {"assignment_id": assignment["assignment_id"],
                                        "state": state, "reason": reason}, now)

    def _expire(self, assignment, job, now):
        started = self.db.execute("SELECT 1 FROM workflow_effect_starts WHERE assignment_id=?",
                                  (assignment["assignment_id"],)).fetchone()
        if started:
            self._terminal(assignment, "uncertain", "expired_after_effect", now)
        elif job["attempts"] >= job["max_attempts"]:
            self._terminal(assignment, "failed", "claims_exhausted", now)
        else:
            self.db.execute("UPDATE jobs SET state='pending',worker_id=NULL,lease_until=NULL WHERE job_id=?",
                            (assignment["job_id"],))
        self.db.execute("INSERT INTO workflow_claim_ends VALUES (?,?,?,?)",
                        (assignment["assignment_id"], job["fence"],
                         "uncertain" if started else "expired_before_effect", self.journal._stamp(now)))
        self._event("lease_expired", {"assignment_id": assignment["assignment_id"],
                                      "fence": job["fence"], "effect_crossed": bool(started)}, now)

    @_record_denial
    def claim_stage(self, token, worker_id, *, lease_seconds=60):
        _identifier(worker_id)
        if type(lease_seconds) is not int or not 1 <= lease_seconds <= 3600:
            raise WorkflowError("Lease must be between 1 and 3600 seconds")
        with self.journal._transaction():
            self._screen(worker_id)
            assignment = self._assignment(token)
            self._active(assignment)
            job = self.db.execute("SELECT * FROM jobs WHERE job_id=?", (assignment["job_id"],)).fetchone()
            now = self.journal._now()
            if job["state"] == "leased":
                if job["lease_until"] > self.journal._stamp(now):
                    return None
                self._expire(assignment, job, now)
                if self.db.execute("SELECT 1 FROM workflow_terminals WHERE assignment_id=?",
                                   (assignment["assignment_id"],)).fetchone():
                    return None
            elif job["state"] != "pending":
                return None
            contract = json.loads(assignment["contract"])
            fence = job["fence"] + 1
            first = self.db.execute("SELECT MIN(created_at) FROM workflow_claims WHERE assignment_id=?",
                                    (assignment["assignment_id"],)).fetchone()[0]
            origin = datetime.fromisoformat(first) if first else now
            deadline = origin + timedelta(seconds=contract["max_seconds"])
            if deadline <= now:
                self._terminal(assignment, "failed", "stage_time_exhausted", now)
                return None
            until = min(now + timedelta(seconds=lease_seconds), deadline)
            self.db.execute("UPDATE jobs SET state='leased',worker_id=?,fence=?,attempts=attempts+1,lease_until=? WHERE job_id=?",
                            (worker_id, fence, self.journal._stamp(until), assignment["job_id"]))
            self.db.execute("INSERT INTO workflow_claims VALUES (?,?,?,?,?,?)",
                            (uuid.uuid4().hex, assignment["assignment_id"], fence, worker_id,
                             self.journal._stamp(deadline), self.journal._stamp(now)))
            self._event("stage_claimed", {"assignment_id": assignment["assignment_id"],
                                          "worker_id": worker_id, "fence": fence,
                                          "lease_until": self.journal._stamp(until)}, now)
            return {**self._metadata(assignment), "worker_id": worker_id, "fence": fence,
                    "lease_until": self.journal._stamp(until)}

    def authorize_intent(self, token, worker_id, fence, intent):
        """Register a strict role-allowed request. No caller-defined body/path/tool."""
        try:
            _object(intent, {"request_id", "action", "input_refs"})
            _identifier(intent["request_id"])
            _identifier(intent["action"])
            refs = _refs(intent["input_refs"])
            with self.journal._transaction():
                now = self.journal._now()
                a = self._leased(token, worker_id, fence, now)
                self._screen(canonical_json(intent))
                contract = json.loads(a["contract"])
                if intent["action"] not in ROLE_ACTIONS[a["role"]]:
                    raise WorkflowError("Role capability does not allow this action")
                if intent["action"] == "dispatch_model" and (
                    contract["backend"] == "synthetic" or not contract["max_spend_micro_usd"]
                ):
                    raise WorkflowError("Assignment has no paid model dispatch allowance")
                if not set(refs) <= set(self._available_refs_locked(a, fence)):
                    raise WorkflowError("Reference was not issued to this assignment")
                self._verify_refs(refs, contract["max_input_bytes"])
                existing = self.db.execute("SELECT * FROM workflow_intents WHERE assignment_id=? AND request_id=?",
                                           (a["assignment_id"], intent["request_id"])).fetchone()
                if existing:
                    if (existing["fence"] != fence or existing["action"] != intent["action"]
                            or json.loads(existing["input_refs"]) != refs):
                        raise WorkflowError("Intent idempotency key changed or belongs to an earlier fence")
                    return {"assignment_id": a["assignment_id"], "request_id": intent["request_id"]}
                used = self.db.execute("SELECT COUNT(*) FROM workflow_intents WHERE assignment_id=?",
                                       (a["assignment_id"],)).fetchone()[0]
                if used >= contract["max_steps"]:
                    raise WorkflowError("Frozen step bound exhausted")
                self.db.execute("INSERT INTO workflow_intents VALUES (?,?,?,?,?,?)",
                                (a["assignment_id"], intent["request_id"], fence, intent["action"],
                                 canonical_json(refs), self.journal._stamp(now)))
                self._event("intent_authorized", {"assignment_id": a["assignment_id"],
                                                  "fence": fence, "intent": intent}, now)
                return {"assignment_id": a["assignment_id"], "request_id": intent["request_id"]}
        except (LedgerError, TypeError):
            self._deny("authorize_intent")
            raise

    def _available_refs_locked(self, assignment, fence):
        """Only issued inputs and this claim's successful broker results."""
        refs = set(json.loads(assignment["input_refs"]))
        for row in self.db.execute(
            "SELECT o.artifact_refs FROM workflow_effect_outcomes o JOIN workflow_intents i "
            "USING(assignment_id,request_id) WHERE o.assignment_id=? AND i.fence=? AND o.status='success'",
            (assignment["assignment_id"], fence),
        ):
            refs.update(json.loads(row["artifact_refs"]))
        refs = _refs(sorted(refs))
        self._verify_refs(refs, json.loads(assignment["contract"])["max_input_bytes"])
        return refs

    @_record_denial
    def available_input_refs(self, token, worker_id, fence):
        """Derive bounded inputs after a successful same-assignment tool step."""
        with self.journal._transaction():
            assignment = self._leased(token, worker_id, fence, self.journal._now())
            refs = self._available_refs_locked(assignment, fence)
            self._leased(token, worker_id, fence, self.journal._now())
            return refs

    def _intent(self, assignment, request_id, fence):
        _identifier(request_id)
        row = self.db.execute("SELECT * FROM workflow_intents WHERE assignment_id=? AND request_id=?",
                              (assignment["assignment_id"], request_id)).fetchone()
        if row is None or row["fence"] != fence:
            raise WorkflowError("Intent not authorized for this fence")
        return row

    @_record_denial
    def start_intent(self, token, worker_id, fence, request_id):
        """Durably consume one effect entitlement; call immediately before effect.

        Cancellation after this boundary cannot undo an external request; the
        stage remains uncertain until explicit operator reconciliation outside
        this first increment. Never retry a start that reports an error.
        """
        with self.journal._transaction():
            return self._start_intent_locked(token, worker_id, fence, request_id)

    def _start_intent_locked(self, token, worker_id, fence, request_id):
        """Broker hook; caller must hold the journal write transaction."""
        if not self.db.in_transaction:
            raise WorkflowError("Effect start requires an atomic transaction")
        now = self.journal._now()
        a = self._leased(token, worker_id, fence, now)
        intent = self._intent(a, request_id, fence)
        self._verify_refs(json.loads(intent["input_refs"]), json.loads(a["contract"])["max_input_bytes"])
        if self.db.execute("SELECT 1 FROM workflow_effect_starts WHERE assignment_id=? AND request_id=?",
                           (a["assignment_id"], request_id)).fetchone():
            raise WorkflowError("Effect entitlement already consumed; do not retry")
        now = self.journal._now()
        self._leased(token, worker_id, fence, now)
        self.db.execute("INSERT INTO workflow_effect_starts VALUES (?,?,?)",
                        (a["assignment_id"], request_id, self.journal._stamp(now)))
        self._event("effect_started", {"assignment_id": a["assignment_id"],
                                       "request_id": request_id, "fence": fence}, now)

    @_record_denial
    def finish_intent(self, token, worker_id, fence, request_id, *, status,
                      artifact_refs, observed_model=None):
        """Trusted broker records verified local results, never role-supplied paths.

        Existing result digests must already be admitted sanitized development
        JSON by the broker. This method verifies bytes, not their data rights.
        A changed/wrong model is an invalid terminal outcome, never a fallback.
        """
        with self.journal._transaction():
            return self._finish_intent_locked(
                token, worker_id, fence, request_id, status=status,
                artifact_refs=artifact_refs, observed_model=observed_model)

    def _finish_intent_locked(self, token, worker_id, fence, request_id, *, status,
                              artifact_refs, observed_model=None):
        """Broker hook; same publication checks inside an existing transaction."""
        if not self.db.in_transaction:
            raise WorkflowError("Effect finish requires an atomic transaction")
        refs = _refs(artifact_refs)
        if status not in ("success", "failed", "invalid", "uncertain"):
            raise WorkflowError("Unsupported effect outcome")
        now = self.journal._now()
        a = self._leased(token, worker_id, fence, now)
        intent = self._intent(a, request_id, fence)
        contract = json.loads(a["contract"])
        if observed_model is not None:
            _identifier(observed_model)
            self._screen(observed_model)
        if intent["action"] == "dispatch_model":
            if ((observed_model is not None or status == "success")
                    and observed_model != contract["requested_model"]):
                status = "invalid"
        elif observed_model is not None:
            raise WorkflowError("Only model dispatch can report a responding model")
        if not self.db.execute("SELECT 1 FROM workflow_effect_starts WHERE assignment_id=? AND request_id=?",
                               (a["assignment_id"], request_id)).fetchone():
            raise WorkflowError("Effect was never started")
        if self.db.execute("SELECT 1 FROM workflow_effect_outcomes WHERE assignment_id=? AND request_id=?",
                           (a["assignment_id"], request_id)).fetchone():
            raise WorkflowError("Effect outcome is already terminal")
        if status == "success" and not refs:
            raise WorkflowError("Successful effect requires exact result artifacts")
        self._verify_refs(refs, contract["max_output_bytes"])
        now = self.journal._now()
        self._leased(token, worker_id, fence, now)
        self.db.execute("INSERT INTO workflow_effect_outcomes VALUES (?,?,?,?,?,?)",
                        (a["assignment_id"], request_id, status, canonical_json(refs),
                         observed_model, self.journal._stamp(now)))
        self._event("effect_finished", {"assignment_id": a["assignment_id"],
                                        "request_id": request_id, "status": status,
                                        "artifact_refs": refs, "observed_model": observed_model}, now)
        if status != "success":
            self._terminal(a, status, "effect_" + status, now)

    @_record_denial
    def finish_handoff(self, token, worker_id, fence, handoff):
        _object(handoff, {"state", "artifact_refs", "reviewed_refs", "assumptions", "objections", "next_action"})
        refs, reviewed = _refs(handoff["artifact_refs"]), _refs(handoff["reviewed_refs"])
        _texts(handoff["assumptions"])
        if type(handoff["objections"]) is not list or len(handoff["objections"]) > 32:
            raise WorkflowError("Invalid objections")
        for objection in handoff["objections"]:
            _object(objection, {"code", "artifact_refs"})
            _identifier(objection["code"])
            _refs(objection["artifact_refs"])
        if ((handoff["state"], handoff["next_action"]) not in
                (("complete", "proceed"), ("blocked", "stop"))):
            raise WorkflowError("Handoff state and next action disagree")
        with self.journal._transaction():
            now = self.journal._now()
            a = self._leased(token, worker_id, fence, now)
            self._screen(canonical_json(handoff))
            contract = json.loads(a["contract"])
            inputs = set(json.loads(a["input_refs"]))
            if not set(reviewed) <= inputs or (a["role"] in REVIEW_ROLES and set(reviewed) != inputs):
                raise WorkflowError("Review does not bind the complete issued artifact set")
            intents = self.db.execute(
                "SELECT i.request_id,o.status,o.artifact_refs FROM workflow_intents i "
                "LEFT JOIN workflow_effect_outcomes o USING(assignment_id,request_id) "
                "WHERE i.assignment_id=? AND i.fence=?", (a["assignment_id"], fence)
            ).fetchall()
            if not intents or any(row["status"] != "success" for row in intents):
                raise WorkflowError("All authorized intents require successful outcomes before publication")
            produced = {ref for row in intents for ref in json.loads(row["artifact_refs"])}
            if not refs or set(refs) != produced:
                raise WorkflowError("Handoff must include the exact complete produced artifact set")
            for objection in handoff["objections"]:
                if not set(objection["artifact_refs"]) <= inputs | produced:
                    raise WorkflowError("Objection references an unauthorized artifact")
            self._verify_refs(sorted(inputs), contract["max_input_bytes"])
            self._verify_refs(refs, contract["max_output_bytes"])
            document = {**handoff, "artifact_refs": refs, "reviewed_refs": reviewed,
                        "assignment_id": a["assignment_id"], "actor_id": a["actor_id"],
                        "role": a["role"], "run_id": a["run_id"], "fence": fence,
                        "upstream_handoffs": json.loads(a["upstream_handoffs"])}
            if len(canonical_json(document).encode()) > contract["max_output_bytes"]:
                raise WorkflowError("Handoff exceeds frozen output byte bound")
            self._leased(token, worker_id, fence, self.journal._now())
            digest = self.store.put_json(document)
            self.store.read_bytes(digest)
            now = self.journal._now()
            self._leased(token, worker_id, fence, now)
            self.db.execute("INSERT INTO workflow_handoffs VALUES (?,?,?,?)",
                            (a["assignment_id"], digest, canonical_json(document), self.journal._stamp(now)))
            self.db.execute("INSERT INTO workflow_terminals VALUES (?,?,?,?)",
                            (a["assignment_id"], handoff["state"], "handoff", self.journal._stamp(now)))
            self.db.execute("UPDATE jobs SET state='complete',result=?,worker_id=NULL,lease_until=NULL WHERE job_id=?",
                            (canonical_json({"handoff_sha256": digest}), a["job_id"]))
            self._event("handoff_committed", {"assignment_id": a["assignment_id"],
                                              "actor_id": a["actor_id"], "handoff_sha256": digest}, now)
            return {"handoff_sha256": digest, "document": document}

    @_record_denial
    def cancel_run(self, run_id, *, reason="operator_cancelled"):
        """Privileged supervisor cancellation; preserve already-published stages."""
        _identifier(reason)
        with self.journal._transaction():
            self._run(run_id)
            self._screen(reason)
            if self.db.execute("SELECT 1 FROM workflow_cancellations WHERE run_id=?", (run_id,)).fetchone():
                return
            now = self.journal._now()
            self.db.execute("INSERT INTO workflow_cancellations VALUES (?,?,?)",
                            (run_id, reason, self.journal._stamp(now)))
            for a in self.db.execute("SELECT * FROM workflow_assignments WHERE run_id=?", (run_id,)).fetchall():
                if self.db.execute("SELECT 1 FROM workflow_terminals WHERE assignment_id=?",
                                   (a["assignment_id"],)).fetchone():
                    continue
                started = self.db.execute("SELECT 1 FROM workflow_effect_starts WHERE assignment_id=?",
                                          (a["assignment_id"],)).fetchone()
                self._terminal(a, "uncertain" if started else "cancelled", reason, now)
            self._event("run_cancelled", {"run_id": run_id, "reason": reason}, now)

    @_record_denial
    def recover_expired(self, run_id):
        """Reconcile only expired leases. Never perform or replay any effect."""
        with self.journal._transaction():
            self._run(run_id)
            now = self.journal._now()
            rows = self.db.execute(
                "SELECT a.* FROM workflow_assignments a JOIN jobs j USING(job_id) "
                "WHERE a.run_id=? AND j.state='leased' AND j.lease_until<=?",
                (run_id, self.journal._stamp(now))
            ).fetchall()
            for a in rows:
                job = self.db.execute("SELECT * FROM jobs WHERE job_id=?", (a["job_id"],)).fetchone()
                self._expire(a, job, now)
            return len(rows)

    def read_status(self, run_id):
        """Supervisor metadata only; no tokens, token hashes, or artifact contents."""
        with self.journal._transaction():
            self._run(run_id)
            stages = []
            for role in ROLES:
                a = self.db.execute("SELECT * FROM workflow_assignments WHERE run_id=? AND role=?",
                                    (run_id, role)).fetchone()
                if a is None:
                    stages.append({"role": role, "state": "pending"})
                    continue
                terminal = self.db.execute("SELECT * FROM workflow_terminals WHERE assignment_id=?",
                                           (a["assignment_id"],)).fetchone()
                job = self.db.execute("SELECT * FROM jobs WHERE job_id=?", (a["job_id"],)).fetchone()
                handoff = self.db.execute("SELECT document_sha256 FROM workflow_handoffs WHERE assignment_id=?",
                                          (a["assignment_id"],)).fetchone()
                effects = [dict(row) for row in self.db.execute(
                    "SELECT i.request_id,i.fence,i.action,s.created_at AS started_at,o.status "
                    "FROM workflow_intents i LEFT JOIN workflow_effect_starts s USING(assignment_id,request_id) "
                    "LEFT JOIN workflow_effect_outcomes o USING(assignment_id,request_id) "
                    "WHERE i.assignment_id=? ORDER BY i.created_at,i.request_id", (a["assignment_id"],)
                )]
                stages.append({"role": role, "assignment_id": a["assignment_id"],
                               "actor_id": a["actor_id"], "state": terminal["state"] if terminal else job["state"],
                               "reason": terminal["reason"] if terminal else None,
                               "fence": job["fence"], "claims": job["attempts"],
                               "lease_until": job["lease_until"], "intents": effects,
                               "handoff_sha256": handoff[0] if handoff else None})
            cancelled = bool(self.db.execute("SELECT 1 FROM workflow_cancellations WHERE run_id=?",
                                             (run_id,)).fetchone())
            if cancelled:
                state = "cancelled"
            elif all(s["state"] == "complete" for s in stages):
                state = "complete"
            elif any(s["state"] == "uncertain" for s in stages):
                state = "uncertain"
            elif any(s["state"] in ("blocked", "failed", "invalid") for s in stages):
                state = "blocked"
            else:
                state = "active"
            return {"run_id": run_id, "state": state, "stages": stages}

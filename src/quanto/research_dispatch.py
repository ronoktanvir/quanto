"""Fenced, one-use D008 research calls with conservative aggregate holds.

Only validated program-owned packets cross this boundary. The same SQLite
transaction consumes the workflow effect, role allowance, USD4 research-purpose
allowance, global USD20 reservation and provider dispatch entitlement. It ends
before the network operation. A crash after it cannot authorize automatic replay.
These are cooperating same-user controls, not account-wide billing or OS isolation.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
import json

from quanto import provider
from quanto.ledger import Journal, LA, LedgerError, canonical_json, hash_bytes
from quanto.research_workflow import ResearchWorkflow, WorkflowError, _identifier


class _BorrowedAtomicJournal(Journal):
    """Run unchanged Journal methods on the workflow's existing transaction.

    A SAVEPOINT preserves the original method's error rollback while only the
    enclosing BEGIN IMMEDIATE can commit. No ledger validation is replaced or
    skipped. This adapter is deliberately unusable outside that transaction.
    """

    def __init__(self, journal):
        self.connection = journal.connection
        self.clock = journal.clock
        self.daily_limit_micro_usd = journal.daily_limit_micro_usd
        self._sequence = 0

    @contextmanager
    def _transaction(self):
        if not self.connection.in_transaction:
            raise WorkflowError("Borrowed journal requires a supervisor transaction")
        self._sequence += 1
        name = "research_atomic_" + str(self._sequence)
        self.connection.execute("SAVEPOINT " + name)
        try:
            yield
            self.connection.execute("RELEASE SAVEPOINT " + name)
        except BaseException:
            self.connection.execute("ROLLBACK TO SAVEPOINT " + name)
            self.connection.execute("RELEASE SAVEPOINT " + name)
            raise


_SCHEMA = """
CREATE TABLE IF NOT EXISTS provider_allocations (
 request_id TEXT PRIMARY KEY, day TEXT, purpose TEXT, amount INTEGER
);
CREATE TABLE IF NOT EXISTS research_dispatch_holds (
 request_id TEXT PRIMARY KEY REFERENCES reservations(request_id),
 assignment_id TEXT NOT NULL REFERENCES workflow_assignments(assignment_id),
 amount INTEGER NOT NULL, packet_sha256 TEXT NOT NULL, body_sha256 TEXT NOT NULL,
 transport_kind TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS research_model_observations (
 request_id TEXT PRIMARY KEY REFERENCES research_dispatch_holds(request_id),
 observation TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS research_private_responses (
 request_id TEXT PRIMARY KEY REFERENCES research_dispatch_holds(request_id),
 artifact_sha256 TEXT NOT NULL, created_at TEXT NOT NULL
);
"""


class ResearchDispatcher:
    """Trusted supervisor broker; one workflow/connection per calling thread."""

    def __init__(self, workflow: ResearchWorkflow):
        self.workflow = workflow
        self.journal, self.db = workflow.journal, workflow.db
        self.db.executescript(_SCHEMA)
        for table in ("research_dispatch_holds", "research_model_observations",
                      "research_private_responses"):
            for operation in ("UPDATE", "DELETE"):
                self.db.execute(
                    f"CREATE TRIGGER IF NOT EXISTS no_{operation.lower()}_{table} "
                    f"BEFORE {operation} ON {table} BEGIN "
                    "SELECT RAISE(ABORT, 'append-only record'); END")

    def _authorize(self, token, worker_id, fence, request_id, prepared, context, synthetic):
        workflow = self.workflow
        with self.journal._transaction():
            now = self.journal._now()
            assignment = workflow._leased(token, worker_id, fence, now)
            contract = json.loads(assignment["contract"])
            if contract["backend"] != "anthropic_text" or not contract["max_spend_micro_usd"]:
                raise WorkflowError("Assignment has no research dispatch allowance")
            if self.db.execute("SELECT 1 FROM reservations WHERE request_id=?",
                               (request_id,)).fetchone():
                raise WorkflowError("Request ID already consumed; automatic replay forbidden")
            used = self.db.execute(
                "SELECT COALESCE(SUM(amount),0) FROM research_dispatch_holds WHERE assignment_id=?",
                (assignment["assignment_id"],)).fetchone()[0]
            if used + prepared.reserved_micro_usd > contract["max_spend_micro_usd"]:
                raise WorkflowError("Aggregate role research allowance would be exceeded")
            day = now.astimezone(LA).date().isoformat()
            workflow._start_intent_locked(token, worker_id, fence, request_id)
            # Starting an effect verifies local artifacts and can cross an
            # accounting boundary. Keep the entire atomic operation on its
            # original day; a crossing rolls the effect entitlement back too.
            now = self.journal._now()
            if now.astimezone(LA).date().isoformat() != day:
                raise WorkflowError("Research authorization crossed Los Angeles midnight")
            workflow._leased(token, worker_id, fence, now)
            purpose_used = self.db.execute(
                "SELECT COALESCE(SUM(amount),0) FROM provider_allocations WHERE day=? AND purpose='research'",
                (day,)).fetchone()[0]
            if purpose_used + prepared.reserved_micro_usd > provider.PURPOSE_LIMITS["research"]:
                raise WorkflowError("Daily research purpose allowance would be exceeded")
            atomic = _BorrowedAtomicJournal(self.journal)
            reservation = atomic.reserve(request_id, prepared.reserved_micro_usd)
            stamp = self.journal._stamp(now)
            self.db.execute("INSERT INTO provider_allocations VALUES (?,?,?,?)",
                            (request_id, day, "research", prepared.reserved_micro_usd))
            self.db.execute("INSERT INTO research_dispatch_holds VALUES (?,?,?,?,?,?,?)", (
                request_id, assignment["assignment_id"], prepared.reserved_micro_usd,
                hash_bytes(canonical_json(context).encode()), hash_bytes(prepared.body),
                "synthetic_fixture" if synthetic else "anthropic_api", stamp))
            # Original Journal method enforces reserved state, current LA day,
            # globally unique dispatch ID and its usual durable event evidence.
            authorization = atomic.authorize_dispatch(request_id)
            workflow._event("research_dispatch_authorized", {
                "assignment_id": assignment["assignment_id"], "request_id": request_id,
                "requested_model": prepared.model, "reserved_micro_usd": prepared.reserved_micro_usd,
                "transport_kind": "synthetic_fixture" if synthetic else "anthropic_api",
                "price_verified_on": provider.PRICE_VERIFIED_ON,
                "price_sources": provider.PRICE_SOURCES}, now)
            now = self.journal._now()
            workflow._leased(token, worker_id, fence, now)
            if (now.astimezone(LA).date().isoformat() != day
                    or reservation["day"] != day or authorization["day"] != day):
                raise WorkflowError("Research authorization crossed Los Angeles midnight")

    def _before_send(self, token, worker_id, fence, request_id):
        with self.journal._transaction():
            now = self.journal._now()
            a = self.workflow._leased(token, worker_id, fence, now)
            intent = self.workflow._intent(a, request_id, fence)
            if intent["action"] != "dispatch_model":
                raise WorkflowError("Effect does not authorize model dispatch")
            self.workflow._verify_refs(json.loads(intent["input_refs"]),
                                       json.loads(a["contract"])["max_input_bytes"])
            row = self.db.execute(
                "SELECT r.state,r.day,d.authorized_at FROM reservations r JOIN dispatches d "
                "USING(request_id) JOIN research_dispatch_holds h USING(request_id) "
                "WHERE request_id=? AND h.assignment_id=?", (request_id, a["assignment_id"])
            ).fetchone()
            if row is None or row["state"] != "reserved":
                raise WorkflowError("Current-day research dispatch authorization required")
            if not self.db.execute(
                "SELECT 1 FROM workflow_effect_starts WHERE assignment_id=? AND request_id=?",
                (a["assignment_id"], request_id)).fetchone():
                raise WorkflowError("Model effect entitlement was not consumed")
            provider._research_ready(self.workflow.store.root)
            job = self.db.execute("SELECT lease_until FROM jobs WHERE job_id=?", (a["job_id"],)).fetchone()
            claim = self.db.execute(
                "SELECT deadline FROM workflow_claims WHERE assignment_id=? AND fence=?",
                (a["assignment_id"], fence)).fetchone()
            until = min(datetime.fromisoformat(job["lease_until"]),
                        datetime.fromisoformat(claim["deadline"]))
            # Artifact verification and readiness checks can consume the lease
            # or cross midnight. Revalidate after those local reads, using a
            # fresh clock for both the authority check and returned timeout.
            now = self.journal._now()
            self.workflow._leased(token, worker_id, fence, now)
            if row["day"] != now.astimezone(LA).date().isoformat():
                raise WorkflowError("Current-day research dispatch authorization required")
            return (until - now).total_seconds()

    def _observe(self, request_id, evidence):
        with self.journal._transaction():
            # Provider evidence contains bounded primitive metadata only. Apply
            # workflow secret screening before even this private audit record.
            self.workflow._screen(canonical_json(evidence))
            self.db.execute("INSERT INTO research_model_observations VALUES (?,?,?)", (
                request_id, canonical_json(evidence), self.journal._stamp(self.journal._now())))

    def _uncertain(self, token, worker_id, fence, request_id):
        # No raw provider exception/packet/token becomes audit text. Inability
        # to publish under a stale lease leaves the started effect inspectable;
        # ordinary workflow recovery then marks the assignment uncertain.
        self.journal.mark_uncertain(request_id, "Research dispatch uncertain; no automatic replay")
        observed_model = None
        row = self.db.execute("SELECT observation FROM research_model_observations WHERE request_id=?",
                              (request_id,)).fetchone()
        if row:
            candidate = json.loads(row[0]).get("model")
            try:
                _identifier(candidate)
                self.workflow._screen(candidate)
                observed_model = candidate
            except LedgerError:
                pass
        try:
            self.workflow.finish_intent(token, worker_id, fence, request_id, status="uncertain",
                                        artifact_refs=[], observed_model=observed_model)
        except LedgerError:
            pass

    def dispatch(self, token, worker_id, fence, request_id, context, *, transport=None):
        """Return a safe projection/receipt plus explicitly private visible text.

        ``artifact_refs`` contains only safe typed output and allowlisted
        transport accounting. ``private_response`` is a supervisor inspection
        value; its raw text/artifact is never added to workflow input references.
        Injected transports are always synthetic evidence even when their fake
        envelopes contain a real provider model name.
        """
        from quanto.research_packets import (
            packet_messages, parse_role_output, project_role_output, validate_packet,
        )

        authorized = False
        acquired = False
        try:
            _identifier(request_id)
            context = validate_packet(context)
            assignment = self.workflow.authenticate_capability(token)
            contract = assignment["contract"]
            if context["role"] != assignment["role"]:
                raise WorkflowError("Research packet role differs from issued assignment")
            packet = packet_messages(context)
            if hash_bytes(packet["system"].encode()) != contract["prompt_sha256"]:
                raise WorkflowError("Research system prompt differs from frozen contract")
            # Token bounds and response byte bounds are both enforced. A model
            # can still exceed the byte ceiling before token truncation; such a
            # response is uncertain and never automatically retried.
            ceiling = 4096 if contract["requested_model"] == provider.OPUS else 2048
            max_tokens = min(ceiling, max(1, contract["max_output_bytes"] // 4))
            prepared = provider.prepare_research_text(
                model=contract["requested_model"], system=packet["system"], messages=packet["messages"],
                max_tokens=max_tokens, max_input_bytes=contract["max_input_bytes"])
            self.workflow._screen(prepared.body.decode())
            provider._research_ready(self.workflow.store.root)
            if not provider.CALL_SLOTS.acquire(blocking=False):
                raise WorkflowError("Two model calls are already in progress")
            acquired = True
            if self.db.execute("SELECT 1 FROM reservations WHERE request_id=?",
                               (request_id,)).fetchone():
                raise WorkflowError("Request ID already consumed; automatic replay forbidden")
            self.workflow.authorize_intent(token, worker_id, fence, {
                "request_id": request_id, "action": "dispatch_model",
                "input_refs": self.workflow.available_input_refs(token, worker_id, fence)})
            self._authorize(token, worker_id, fence, request_id, prepared, context, transport is not None)
            authorized = True
            result = provider.send_research_text(
                self.workflow.store.root, prepared,
                before_send=lambda: self._before_send(token, worker_id, fence, request_id),
                max_output_bytes=contract["max_output_bytes"], transport=transport,
                on_response=lambda evidence: self._observe(request_id, evidence))
            required = next((output["predicate"] for output in context["prior_outputs"]
                             if output["role"] == "hypothesis" and output["decision"] == "propose"), None)
            private = {**result, "request_id": request_id, "requested_model": prepared.model,
                       "body_sha256": hash_bytes(prepared.body)}
            # This is private observation evidence, not a worker result or
            # upstream input. Retain it even if a valid-looking envelope later
            # fails typed output validation or its worker lost its lease.
            with self.journal._transaction():
                self.workflow._screen(canonical_json(private))
                private_ref = self.workflow.store.put_json(private)
                self.db.execute("INSERT INTO research_private_responses VALUES (?,?,?)", (
                    request_id, private_ref, self.journal._stamp(self.journal._now())))
            parsed = parse_role_output(result["reply"], assignment["role"],
                                       context["artifact_aliases"], context["allowed_predicates"],
                                       required_predicate=required)
            projection = project_role_output(parsed)
            receipt = {key: result[key] for key in (
                "observed_model", "usage", "cost_micro_usd", "cost_kind", "elapsed_seconds",
                "transport_kind", "actual_model_evidence", "terminal")}
            receipt.update({"schema": "research_transport_receipt.v1", "request_id": request_id,
                            "requested_model": prepared.model,
                            "reserved_micro_usd": prepared.reserved_micro_usd})
            with self.journal._transaction():
                self.workflow._leased(token, worker_id, fence, self.journal._now())
                refs = [self.workflow.store.put_json(projection), self.workflow.store.put_json(receipt)]
                self.workflow._finish_intent_locked(
                    token, worker_id, fence, request_id, status="success", artifact_refs=refs,
                    observed_model=result["observed_model"])
                _BorrowedAtomicJournal(self.journal).settle(request_id, result["cost_micro_usd"])
                # A slow local object write may itself outlast the lease.
                self.workflow._leased(token, worker_id, fence, self.journal._now())
            return {"artifact_refs": sorted(refs), "projection": projection, "receipt": receipt,
                    "private_response": private}
        except Exception as exc:
            if authorized:
                self._uncertain(token, worker_id, fence, request_id)
                raise WorkflowError("Research call did not complete; full hold retained; no automatic replay") from None
            self.workflow._deny("research_dispatch")
            if isinstance(exc, LedgerError):
                raise
            # Packet parsers intentionally have their own fixed exception
            # vocabulary. Keep the broker's worker-facing contract uniform.
            raise WorkflowError("Research dispatch rejected before send") from None
        finally:
            if acquired:
                provider.CALL_SLOTS.release()

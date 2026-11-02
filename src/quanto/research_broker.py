"""One explicit bounded development workflow, not an unattended scheduler.

The supervisor maps private identifiers to typed method-only context. Model
outputs materially select a registered comparison; prices and predicate results
never enter model packets. A stopped/uncertain invocation is never auto-resumed.
Temporary injected transports are synthetic evidence, even with real model names.
"""
from __future__ import annotations

from pathlib import Path
import platform
import re
import sqlite3
import uuid

from quanto.failure_memory import FailureMemory
from quanto.ledger import LedgerError, canonical_json, hash_bytes, hash_json
from quanto.provenance import Provenance, ProvenanceError, _strict_json
from quanto.provider import HAIKU, OPUS, _research_ready
from quanto.research_comparison import completion_projection, run_comparison
from quanto.research_dispatch import ResearchDispatcher
from quanto.research_packets import FAILURE_CODES, PREDICATES, SYSTEM_PROMPT, validate_packet
from quanto.research_workflow import ROLES, REVIEW_ROLES, ResearchWorkflow

_HEX = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[0-9a-f]{32}\Z")
_KEY = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,63}\Z")
_SCHEMA = """
CREATE TABLE IF NOT EXISTS research_broker_runs (
 submission_id TEXT PRIMARY KEY REFERENCES provenance_submissions,
 run_key TEXT NOT NULL UNIQUE, workflow_run_id TEXT NOT NULL UNIQUE,
 configuration_sha256 TEXT NOT NULL, code_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS research_broker_aliases (
 run_id TEXT NOT NULL, alias TEXT NOT NULL, artifact_sha256 TEXT NOT NULL,
 PRIMARY KEY(run_id,alias), UNIQUE(run_id,artifact_sha256)
);
CREATE TABLE IF NOT EXISTS research_broker_stages (
 submission_id TEXT NOT NULL REFERENCES research_broker_runs,
 role TEXT NOT NULL, assignment_id TEXT NOT NULL, record_sha256 TEXT NOT NULL,
 PRIMARY KEY(submission_id,role)
);
CREATE TABLE IF NOT EXISTS research_broker_tool_requests (
 parent_submission_id TEXT NOT NULL REFERENCES research_broker_runs(submission_id),
 assignment_id TEXT NOT NULL, request_id TEXT NOT NULL, fence INTEGER NOT NULL,
 request_sha256 TEXT NOT NULL, PRIMARY KEY(assignment_id,request_id),
 FOREIGN KEY(assignment_id,request_id) REFERENCES workflow_intents(assignment_id,request_id)
);
CREATE TABLE IF NOT EXISTS research_broker_tool_children (
 assignment_id TEXT NOT NULL, request_id TEXT NOT NULL,
 child_submission_id TEXT NOT NULL UNIQUE REFERENCES provenance_submissions(submission_id),
 PRIMARY KEY(assignment_id,request_id), FOREIGN KEY(assignment_id,request_id)
 REFERENCES research_broker_tool_requests(assignment_id,request_id)
);
"""
DEFAULT_MODELS = {role: OPUS if role in {"data_critic", "statistical_critic"} else HAIKU
                  for role in ROLES}


class BrokerError(LedgerError):
    """Fixed supervisor refusal, without private input or capability text."""


def _schema(store):
    db = store.journal.connection
    db.executescript(_SCHEMA)
    for table in ("research_broker_runs", "research_broker_aliases", "research_broker_stages",
                  "research_broker_tool_requests", "research_broker_tool_children"):
        for operation in ("UPDATE", "DELETE"):
            db.execute(f"CREATE TRIGGER IF NOT EXISTS no_{operation.lower()}_{table} "
                       f"BEFORE {operation} ON {table} BEGIN "
                       "SELECT RAISE(ABORT,'append-only record'); END")


def code_identity():
    """Disk/source identity; cooperating-process control, not owner attestation."""
    names = ("research_broker.py", "research_packets.py", "research_dispatch.py",
             "research_comparison.py", "research_workflow.py", "failure_memory.py", "provider.py")
    directory = Path(__file__).parent
    return {"sources": {name: hash_bytes((directory / name).read_bytes()) for name in names},
            "python": platform.python_version(), "implementation": platform.python_implementation()}


def _configuration(raw, synthetic):
    value = _strict_json(raw.encode())
    if (type(value) is not dict or set(value) != {
        "run_key", "suite_sha256", "failure_ids", "models", "evidence_kind"
    } or type(value["run_key"]) is not str or not _KEY.fullmatch(value["run_key"])
            or type(value["suite_sha256"]) is not str or not _HEX.fullmatch(value["suite_sha256"])):
        raise BrokerError("broker_request_refused")
    expected = "synthetic_fixture" if synthetic else "historical_market_data"
    if value["evidence_kind"] != expected:
        raise BrokerError("broker_transport_evidence_mismatch")
    if type(value["models"]) is not dict or set(value["models"]) != set(ROLES):
        raise BrokerError("broker_model_roster_refused")
    if any(type(model) is not str or model not in {HAIKU, OPUS}
           for model in value["models"].values()):
        raise BrokerError("broker_model_roster_refused")
    failures = value["failure_ids"]
    if type(failures) is not list or len(failures) > 16:
        raise BrokerError("broker_failure_scope_refused")
    seen = set()
    for failure in failures:
        if (type(failure) is not dict or set(failure) != {"source", "id"}
                or type(failure["source"]) is not str
                or failure["source"] not in {"submission", "attempt"}
                or type(failure["id"]) is not str or not _ID.fullmatch(failure["id"])):
            raise BrokerError("broker_failure_scope_refused")
        identity = (failure["source"], failure["id"])
        if identity in seen:
            raise BrokerError("broker_failure_scope_refused")
        seen.add(identity)
    return value


def _contracts(models):
    return {role: {
        "policy_version": "d008.development.v1", "backend": "anthropic_text",
        "requested_model": models[role], "prompt_sha256": hash_bytes(SYSTEM_PROMPT.encode()),
        "context_schema": "research_context.v1", "output_schema": "research_handoff.v1",
        "max_steps": 4, "max_seconds": 900, "max_input_bytes": 40_000,
        "max_output_bytes": 65_536, "max_spend_micro_usd":
            1_000_000 if models[role] == OPUS else 125_000, "max_claims": 1,
    } for role in ROLES}


def _aliases(store, run_id, refs):
    db = store.journal.connection
    with store.journal._transaction():
        known = {row["artifact_sha256"]: row["alias"] for row in db.execute(
            "SELECT * FROM research_broker_aliases WHERE run_id=?", (run_id,))}
        for digest in sorted(set(refs) - known.keys()):
            if len(known) >= 32:
                raise BrokerError("broker_alias_bound")
            alias = "artifact-" + str(len(known) + 1)
            db.execute("INSERT INTO research_broker_aliases VALUES (?,?,?)", (run_id, alias, digest))
            known[digest] = alias
    return {known[digest]: digest for digest in refs}


def _failure_projection(store, allowed):
    """Retrieve only exact supervisor-authorized IDs; never forward raw metadata."""
    memory = FailureMemory(store, allowed_codes=tuple(FAILURE_CODES))
    records, receipts = [], []
    for source in ("submission", "attempt"):
        ids = [item["id"] for item in allowed if item["source"] == source]
        if not ids:
            continue  # Empty IDs would be an unrestricted query.
        result = memory.query({"sources": [source], "ids": ids, "limit": 16})
        receipts.append(result["receipt_sha256"])
        for record in result["failures"]:
            if (record["source"], record["id"]) not in {(item["source"], item["id"]) for item in allowed}:
                raise BrokerError("broker_failure_scope_mismatch")
            records.append(record)
    if len(records) != len(allowed):
        raise BrokerError("broker_failure_missing_or_not_unsuccessful")
    facts = [{"alias": "failure-" + str(i + 1),
              "code": record["code"] if record["code"] in FAILURE_CODES else "other_refusal",
              "status": record["status"], "disposition": record["disposition"]["state"]}
             for i, record in enumerate(sorted(records, key=lambda r: (r["source"], r["id"])))]
    return facts, receipts


def _context(role, evidence, aliases, failures, previous, execution):
    return validate_packet({
        "schema_version": 1, "kind": "research_role_context", "role": role,
        "objective": "frozen_suite_falsification", "evidence_kind": evidence,
        "access_class": "sanitized_development",
        "method": "frozen_trailing_return_next_open_three_costs", "scope": "development_only",
        "data_values_disclosed": False, "allowed_predicates": sorted(PREDICATES),
        "artifact_aliases": sorted(aliases), "failures": failures,
        "prior_outputs": previous, "execution_state": execution,
    })


def _finish(store, submission, status, record):
    artifact = store.put_json(record)
    store.finish(submission, status, {"artifact_refs": [artifact],
                                     "workflow_run_id": record.get("workflow_run_id"),
                                     "scope": "bounded_development_workflow"})
    return {**record, "submission_id": submission, "status": status, "artifact_sha256": artifact}


def _dispatch_counts(store, workflow_id):
    """Authorization/response counts are not a claim of billed network calls."""
    if workflow_id is None or not store.journal.connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_dispatch_holds'"
    ).fetchone():
        return {"authorized": 0, "response_observed": 0}
    row = store.journal.connection.execute(
        "SELECT COUNT(h.request_id),COUNT(o.request_id) FROM research_dispatch_holds h "
        "JOIN workflow_assignments a USING(assignment_id) "
        "LEFT JOIN research_model_observations o USING(request_id) WHERE a.run_id=?",
        (workflow_id,)).fetchone()
    return {"authorized": row[0], "response_observed": row[1]}


def _register_comparison_request(workflow, parent, token, worker, fence, request_id, request):
    """Bind the private exact request before consuming its financial effect."""
    with workflow.journal._transaction():
        a = workflow._leased(token, worker, fence, workflow.journal._now())
        intent = workflow._intent(a, request_id, fence)
        if intent["action"] != "launch_development":
            raise BrokerError("broker_tool_action_mismatch")
        run = workflow.db.execute("SELECT workflow_run_id FROM research_broker_runs WHERE submission_id=?",
                                  (parent,)).fetchone()
        if run is None or run[0] != a["run_id"]:
            raise BrokerError("broker_tool_parent_mismatch")
        digest = workflow.store.put_json(request)
        workflow._leased(token, worker, fence, workflow.journal._now())
        workflow.db.execute("INSERT INTO research_broker_tool_requests VALUES (?,?,?,?,?)",
                            (parent, a["assignment_id"], request_id, fence, digest))
        workflow._event("broker_tool_registered", {"parent_submission_id": parent,
                         "assignment_id": a["assignment_id"], "request_id": request_id,
                         "fence": fence, "request_sha256": digest}, workflow.journal._now())


def _bind_comparison_child(workflow, token, worker, fence, request_id, child_id):
    """Called after child begin, before any suite invocation or calculation."""
    with workflow.journal._transaction():
        a = workflow._leased(token, worker, fence, workflow.journal._now())
        request = workflow.db.execute(
            "SELECT * FROM research_broker_tool_requests WHERE assignment_id=? AND request_id=?",
            (a["assignment_id"], request_id)).fetchone()
        started = workflow.db.execute(
            "SELECT 1 FROM workflow_effect_starts WHERE assignment_id=? AND request_id=?",
            (a["assignment_id"], request_id)).fetchone()
        if request is None or request["fence"] != fence or not started:
            raise BrokerError("broker_tool_not_started")
        child = workflow.store.get_submission(child_id)
        raw = workflow.store.read_bytes(request["request_sha256"])
        if (child["kind"] != "research_comparison" or child["status"] != "pending"
                or child["request_sha256"] != hash_bytes(raw) or child["request_bytes"] != len(raw)):
            raise BrokerError("broker_tool_child_mismatch")
        workflow._leased(token, worker, fence, workflow.journal._now())
        workflow.db.execute("INSERT INTO research_broker_tool_children VALUES (?,?,?)",
                            (a["assignment_id"], request_id, child_id))
        workflow._event("broker_tool_child_bound", {"parent_submission_id": request["parent_submission_id"],
                         "assignment_id": a["assignment_id"], "request_id": request_id,
                         "child_submission_id": child_id}, workflow.journal._now())


def run_workflow(root: Path, request: dict | str, *, transport=None):
    """Explicit one-shot seven-role workflow; never retry a prior run key.

    No imported code or data from an arbitrary path, model-selected tool name,
    endpoint, SQL, shell, order or acquisition is supported. Publication records
    distinguish exact local bindings from the method-only packet models saw.
    """
    root = Path(root)
    with Provenance(root) as store:
        raw = canonical_json(request) if isinstance(request, dict) else request
        submission = store.begin("research_broker_run", raw)
        workflow_id = None
        stages, private_refs = [], []
        try:
            config = _configuration(raw, transport is not None)
            _schema(store)
            if store.journal.connection.execute(
                "SELECT 1 FROM research_broker_runs WHERE run_key=?", (config["run_key"],)
            ).fetchone():
                raise BrokerError("broker_run_key_already_used")
            _research_ready(root)
            contracts = _contracts(config["models"])
            # Whole-run planning headroom, plus per-dispatch atomic enforcement.
            # This is not a reservation and does not exclude other cooperating callers.
            required = sum(c["max_spend_micro_usd"] for c in contracts.values())
            budget = store.journal.budget_snapshot()
            if budget["remaining_micro_usd"] < required:
                return _finish(store, submission, "invalid", {
                    "error_code": "broker_budget_unavailable", "planned_max_micro_usd": required,
                    "evidence_kind": config["evidence_kind"], "dispatch_counts": _dispatch_counts(store, None),
                    "operational_acceptance": False})
            from quanto.study_suite import _verified
            suite = _verified(store, config["suite_sha256"])
            # Full legacy verification stays local; no material from the suite enters a packet.
            private_refs.append(config["suite_sha256"])
            identity = code_identity()
            method = store.put_json({"schema_version": 1, "kind": "research_method_contract",
                                     "objective": "frozen_suite_falsification",
                                     "predicates": sorted(PREDICATES), "development_only": True,
                                     "private_values_disclosed": False})
            workflow = ResearchWorkflow(store)
            manifest = {"run_key": config["run_key"], "access_class": "sanitized_development",
                        "evidence_kind": config["evidence_kind"], "code_sha256": hash_json(identity),
                        "specification_sha256": hash_json(config), "input_refs": [method],
                        "roles": contracts}
            workflow_id = workflow.create_run(manifest)
            config_ref = store.put_json({**config, "code_identity": identity,
                                         "verified_policy_revision_sha256": suite["policy_revision_sha256"]})
            with store.journal._transaction():
                store.journal.connection.execute("INSERT INTO research_broker_runs VALUES (?,?,?,?,?)", (
                    submission, config["run_key"], workflow_id, config_ref, hash_json(identity)))
            dispatcher = ResearchDispatcher(workflow)
            previous, facts, execution = [], [], "not_requested"
            projection_refs = {}
            for role in ROLES:
                if code_identity() != identity:
                    raise BrokerError("broker_code_changed")
                assignment = workflow.issue_stage(workflow_id, role)
                token, worker = assignment["token"], "broker-" + uuid.uuid4().hex
                claim = workflow.claim_stage(token, worker, lease_seconds=900)
                if claim is None:
                    raise BrokerError("broker_stage_claim_refused")
                fence = claim["fence"]
                produced, stage_private = [], []
                if role == "hypothesis":
                    intent_id = "memory-" + uuid.uuid4().hex
                    workflow.authorize_intent(token, worker, fence, {
                        "request_id": intent_id, "action": "query_failures", "input_refs": assignment["input_refs"]})
                    workflow.start_intent(token, worker, fence, intent_id)
                    facts, retrievals = _failure_projection(store, config["failure_ids"])
                    stage_private.extend(retrievals)
                    facts_ref = store.put_json({"schema_version": 1, "kind": "approved_failure_facts",
                                               "failures": facts})
                    workflow.finish_intent(token, worker, fence, intent_id,
                                           status="success", artifact_refs=[facts_ref])
                    produced.append(facts_ref)
                inputs = workflow.available_input_refs(token, worker, fence)
                aliases = _aliases(store, workflow_id, inputs)
                context = _context(role, config["evidence_kind"], aliases, facts, previous, execution)
                context_ref = store.put_json(context)
                call = dispatcher.dispatch(token, worker, fence, "research-" + uuid.uuid4().hex,
                                           context, transport=transport)
                produced.extend(call["artifact_refs"])
                projection = call["projection"]
                projection_ref = store.put_json(projection)
                projection_refs[role] = projection_ref
                previous.append(projection)
                if role == "engineer" and projection["decision"] == "execute":
                    intent_id = "comparison-" + uuid.uuid4().hex
                    comparison_request = {
                        "suite_sha256": config["suite_sha256"], "predicate": projection["predicate"],
                        "hypothesis_sha256": projection_refs["hypothesis"],
                        "engineer_sha256": projection_ref}
                    workflow.authorize_intent(token, worker, fence, {
                        "request_id": intent_id, "action": "launch_development",
                        "input_refs": workflow.available_input_refs(token, worker, fence)})
                    _register_comparison_request(workflow, submission, token, worker, fence,
                                                 intent_id, comparison_request)
                    workflow.start_intent(token, worker, fence, intent_id)
                    comparison = run_comparison(root, comparison_request,
                        on_registered=lambda child: _bind_comparison_child(
                            workflow, token, worker, fence, intent_id, child))
                    # Retain exact private receipt, but never put it in role inputs/packets.
                    stage_private.append(store.put_json(comparison))
                    completion = completion_projection(comparison)
                    completion_ref = store.put_json(completion)
                    execution = completion["execution_state"]
                    if comparison["status"] != "success":
                        workflow.finish_intent(token, worker, fence, intent_id,
                                               status="uncertain" if execution == "uncertain" else "failed",
                                               artifact_refs=[completion_ref])
                        raise BrokerError("broker_registered_comparison_incomplete")
                    workflow.finish_intent(token, worker, fence, intent_id,
                                           status="success", artifact_refs=[completion_ref])
                    produced.append(completion_ref)
                stop = projection["decision"] == "stop"
                handoff = workflow.finish_handoff(token, worker, fence, {
                    "state": "blocked" if stop else "complete", "artifact_refs": sorted(set(produced)),
                    "reviewed_refs": assignment["input_refs"] if role in REVIEW_ROLES else [],
                    "assumptions": ["Method-only model packet; hidden numerical values were not inspected.",
                                    "Local reference binding is not a claim of model access to raw artifacts."],
                    "objections": [{"code": item["code"],
                                    "artifact_refs": [aliases[a] for a in item["artifact_aliases"]]}
                                   for item in projection["findings"]],
                    "next_action": "stop" if stop else "proceed"})
                stage = {"role": role, "assignment_id": assignment["assignment_id"],
                         "model_packet_sha256": context_ref, "alias_bindings": aliases,
                         "projection_sha256": projection_ref, "model_receipt": call["receipt"],
                         "handoff_sha256": handoff["handoff_sha256"],
                         "private_tool_refs": stage_private}
                stage_ref = store.put_json(stage)
                with store.journal._transaction():
                    store.journal.connection.execute("INSERT INTO research_broker_stages VALUES (?,?,?,?)", (
                        submission, role, assignment["assignment_id"], stage_ref))
                stages.append(stage)
                private_refs.extend(stage_private)
                if stop:
                    break
            completed = len(stages) == len(ROLES)
            if code_identity() != identity:
                raise BrokerError("broker_code_changed")
            review_decisions = [p["decision"] for p in previous if p["role"] in REVIEW_ROLES]
            review_outcome = ("blocked" if "block" in review_decisions else "inconclusive"
                              if "inconclusive" in review_decisions else "method_no_blockers")
            record = {"workflow_run_id": workflow_id, "configuration_sha256": config_ref,
                      "code_identity": identity, "evidence_kind": config["evidence_kind"],
                      "stages": stages, "private_tool_refs": private_refs,
                      "dispatch_counts": _dispatch_counts(store, workflow_id), "all_stages_completed": completed,
                      "all_models_actual": completed and all(s["model_receipt"]["actual_model_evidence"] for s in stages),
                      "review_outcome": review_outcome, "execution_state": execution,
                      "operational_acceptance": False, "investment_validation": False,
                      "limitations": ["method_only_model_reviews", "separate_actual_trace_review_required",
                                      "no_unattended_scheduler", "no_protected_evaluator"]}
            return _finish(store, submission, "success" if completed else "invalid", record)
        except (ValueError, OSError, sqlite3.Error, KeyError, TypeError) as exc:
            code = str(exc) if isinstance(exc, BrokerError) else "broker_stage_refused"
            try:
                return _finish(store, submission, "invalid", {
                    "error_code": code, "workflow_run_id": workflow_id, "completed_stages": len(stages),
                    "stages": stages, "dispatch_counts": _dispatch_counts(store, workflow_id),
                    "operational_acceptance": False,
                    "note": "Started effects remain retained; no automatic retry or resume."})
            except (ProvenanceError, LedgerError, OSError, sqlite3.Error):
                return {"submission_id": submission, "status": "pending",
                        "error_code": "broker_publication_interrupted"}

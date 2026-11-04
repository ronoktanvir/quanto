"""New guarded-store adaptation of the prior qualified-context checker.
All artifact reads delegate to current Provenance/AccessSession. No private-path reader.
"""

from pathlib import Path
from datetime import datetime
import hashlib
import json
import re

from quanto.ledger import canonical_json, hash_json
from quanto.provider import HAIKU, OPUS, prepare_research_text
from quanto.research_broker import code_identity
from quanto.research_packets import (
    METHOD,
    SUITE_INTEGRITY,
    PREDICATES,
    packet_messages,
    parse_role_output,
    project_role_output,
    validate_packet,
)
from quanto.research_workflow import ROLES
from quanto.research_failure_context import revalidate_failure_context
from quanto.research_packets import PacketError, FINDING_CODES

HEX = re.compile(r"[0-9a-f]{64}\Z")
STATES = {"success", "invalid", "failed", "interrupted", "pending"}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("constant")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


class Audit:
    def __init__(self, store):
        self.store, self.root = store, store.root
        self.db = store.journal.connection
        self.checks, self.events, self.event_times, self.refs = {}, [], {}, set()

    def check(self, label, condition):
        self.checks[label] = self.checks.get(label, True) and bool(condition)

    def one(self, query, args=()):
        rows = self.db.execute(query, args).fetchall()
        if len(rows) != 1:
            raise ValueError("ambiguous_row")
        return rows[0]

    @property
    def journal(self):
        return self.store.journal

    @property
    def connection(self):
        return self.db

    def _open(self):
        return self.store.journal

    def verify_events(self):
        return self.store.journal.verify_events()

    def read_bytes(self, ref):
        raw = self.store.read_bytes(ref)
        self.refs.add(ref)
        return raw

    def obj(self, ref):
        return strict(self.read_bytes(ref))

    read_json = obj

    def get_submission(self, identity):
        return self.store.get_submission(identity)

    sub = get_submission

    def list_submissions(self, *args, **kwargs):
        return self.store.list_submissions(*args, **kwargs)

    def position(self, kind, **match):
        rows = [
            number
            for number, event_kind, value in self.events
            if event_kind == kind and all(value.get(k) == v for k, v in match.items())
        ]
        if len(rows) != 1:
            raise ValueError("event")
        return rows[0]

    def chain(self):
        self.events, self.event_times = [], {}
        previous, count = "0" * 64, 0
        for row in self.db.execute("SELECT * FROM events ORDER BY id"):
            count += 1
            value = strict(row["payload"])
            expected = hash_json(
                {
                    "id": count,
                    "occurred_at": row["occurred_at"],
                    "kind": row["kind"],
                    "payload": value,
                    "previous_hash": previous,
                }
            )
            if (
                row["id"] != count
                or row["previous_hash"] != previous
                or row["event_hash"] != expected
            ):
                raise ValueError("event_chain")
            self.events.append((count, row["kind"], value))
            self.event_times[count] = datetime.fromisoformat(row["occurred_at"])
            previous = expected
        return {"count": count, "head_sha256": previous}


def failure_bindings(audit, parent, run, config):
    """Independent event joins, plus read-only reuse of the current semantic validator.

    Revalidation is an inspection-time check. It cannot independently reconstruct
    filesystem availability at the earlier send; retained events provide that claim.
    """
    bindings = [
        (n, p)
        for n, kind, p in audit.events
        if kind == "workflow_broker_packet_bound" and p.get("parent_submission_id") == parent
    ]
    basis_events = [
        (n, p)
        for n, kind, p in audit.events
        if kind == "workflow_broker_failure_basis_bound" and p.get("parent_submission_id") == parent
    ]
    audit.check("at_most_one_original_failure_basis", len(basis_events) <= 1)
    basis_ref = None
    query_count = 0
    if basis_events:
        bound, event = basis_events[0]
        basis_ref = event["basis_sha256"]
        basis = audit.obj(basis_ref)
        assignment = audit.one(
            "SELECT * FROM workflow_assignments WHERE assignment_id=?", (event["assignment_id"],)
        )
        intent = audit.one(
            "SELECT * FROM workflow_intents WHERE assignment_id=? AND request_id=?",
            (event["assignment_id"], event["request_id"]),
        )
        start = audit.position("submission_started", submission_id=basis["submission_id"])
        finish = audit.position(
            "submission_finished", submission_id=basis["submission_id"], status="success"
        )
        effect = audit.position(
            "workflow_effect_started",
            assignment_id=event["assignment_id"],
            request_id=event["request_id"],
            fence=event["fence"],
        )
        audit.check(
            "basis_bound_to_original_hypothesis_effect",
            set(event)
            == {
                "parent_submission_id",
                "assignment_id",
                "request_id",
                "fence",
                "configuration_sha256",
                "basis_sha256",
            }
            and event["configuration_sha256"] == run["configuration_sha256"]
            and assignment["run_id"] == run["workflow_run_id"]
            and assignment["role"] == "hypothesis"
            and intent["action"] == "query_failures"
            and intent["fence"] == event["fence"]
            and effect < start < finish < bound,
        )
        audit.check(
            "basis_never_rebound",
            sum(
                kind == "workflow_broker_failure_basis_bound" and p.get("basis_sha256") == basis_ref
                for _, kind, p in audit.events
            )
            == 1,
        )
        audit.check(
            "basis_exact_failure_authorization",
            sorted(basis["authorized_failure_ids"], key=canonical_json)
            == sorted(config["failure_ids"], key=canonical_json),
        )
        for retrieval in basis["retrievals"]:
            query = audit.obj(retrieval["receipt_sha256"])
            query_count += 1
            audit.check(
                "original_query_" + str(query_count) + "_inside_basis",
                start
                < audit.position("submission_started", submission_id=query["query_submission_id"])
                < audit.position(
                    "submission_finished",
                    submission_id=query["query_submission_id"],
                    status="success",
                )
                < finish,
            )
    used_roles, proof_refs, observation_refs = set(), set(), set()
    for bound, event in bindings:
        role = event["role"]
        if role not in ROLES:
            raise ValueError("role")
        prefix = role + ":"
        audit.check(prefix + "one_packet_binding", role not in used_roles)
        used_roles.add(role)
        proof = audit.obj(event["verification_sha256"])
        packet = validate_packet(audit.obj(event["packet_sha256"]))
        observation_ref = event["failure_context_sha256"]
        observation = audit.obj(observation_ref)
        assignment = audit.one(
            "SELECT * FROM workflow_assignments WHERE assignment_id=?", (event["assignment_id"],)
        )
        audit.check(
            prefix + "failure_observation_exact_event_binding",
            set(event)
            == {
                "parent_submission_id",
                "assignment_id",
                "role",
                "fence",
                "request_id",
                "configuration_sha256",
                "packet_sha256",
                "verification_sha256",
                "failure_context_sha256",
                "failure_basis_sha256",
            }
            and assignment["role"] == role
            and assignment["run_id"] == run["workflow_run_id"]
            and event["configuration_sha256"] == run["configuration_sha256"]
            and proof["failure_context_sha256"] == observation_ref
            and proof["failure_basis_sha256"]
            == event["failure_basis_sha256"]
            == (None if role == "director" else basis_ref)
            and proof["role"] == observation["role"] == packet["role"] == role
            and proof["configuration_sha256"]
            == observation["configuration_sha256"]
            == run["configuration_sha256"]
            and proof["suite_sha256"] == observation["suite_sha256"] == config["suite_sha256"]
            and proof["policy_revision_sha256"]
            == observation["policy_revision_sha256"]
            == config["verified_policy_revision_sha256"]
            and proof["method"] == packet["method"] == METHOD
            and proof["suite_integrity"] == packet["suite_integrity"] == SUITE_INTEGRITY
            and proof["failure_facts_sha256"] == hash_json(packet["failures"])
            and packet["failures"] == observation["failures"],
        )
        audit.check(
            prefix + "fresh_one_use_observation",
            event["verification_sha256"] not in proof_refs
            and observation_ref not in observation_refs
            and audit.position("workflow_assignment_issued", assignment_id=event["assignment_id"])
            < audit.position("submission_started", submission_id=observation["submission_id"])
            < audit.position(
                "submission_finished", submission_id=observation["submission_id"], status="success"
            )
            < bound
            and sum(
                kind == "workflow_broker_packet_bound"
                and (
                    p.get("verification_sha256") == event["verification_sha256"]
                    or p.get("failure_context_sha256") == observation_ref
                )
                for _, kind, p in audit.events
            )
            == 1,
        )
        proof_refs.add(event["verification_sha256"])
        observation_refs.add(observation_ref)
        if role != "director":
            audit.check(
                prefix + "completed_original_basis_before_binding",
                len(basis_events) == 1
                and basis_events[0][0]
                < audit.position(
                    "workflow_effect_finished",
                    assignment_id=basis_events[0][1]["assignment_id"],
                    request_id=basis_events[0][1]["request_id"],
                    status="success",
                )
                < bound,
            )
        try:
            revalidated = revalidate_failure_context(
                audit,
                observation_ref,
                run["configuration_sha256"],
                role,
                event["failure_basis_sha256"],
            )
            audit.check(prefix + "current_context_revalidated", revalidated == observation)
        except Exception:
            audit.check(prefix + "current_context_revalidated", False)
        private_refs = {
            event["verification_sha256"],
            observation_ref,
            event["failure_basis_sha256"],
        } - {None}
        alias_refs = {
            r[0]
            for r in audit.db.execute(
                "SELECT artifact_sha256 FROM research_broker_aliases WHERE run_id=?",
                (run["workflow_run_id"],),
            )
        }
        audit.check(
            prefix + "failure_proofs_not_aliases", not private_refs.intersection(alias_refs)
        )
        holds = list(
            audit.db.execute(
                "SELECT * FROM research_dispatch_holds WHERE request_id=?", (event["request_id"],)
            )
        )
        audit.check(prefix + "at_most_one_bound_dispatch", len(holds) <= 1)
        if holds:
            hold = holds[0]
            intent = audit.one(
                "SELECT * FROM workflow_intents WHERE assignment_id=? AND request_id=?",
                (event["assignment_id"], event["request_id"]),
            )
            contract = strict(assignment["contract"])
            messages = packet_messages(packet)
            prepared = prepare_research_text(
                model=contract["requested_model"],
                system=messages["system"],
                messages=messages["messages"],
                max_tokens=min(
                    4096 if contract["requested_model"] == OPUS else 2048,
                    max(1, contract["max_output_bytes"] // 4),
                ),
                max_input_bytes=contract["max_input_bytes"],
            )
            audit.check(
                prefix + "bound_request_body_and_fence",
                hold["body_sha256"] == digest(prepared.body)
                and intent["fence"] == event["fence"]
                and intent["action"] == "dispatch_model",
            )
            audit.check(
                prefix + "failure_binding_before_budget",
                hold["assignment_id"] == event["assignment_id"]
                and hold["packet_sha256"] == event["packet_sha256"]
                and bound < audit.position("budget_reserved", request_id=event["request_id"]),
            )
    authorized = list(
        audit.db.execute(
            "SELECT h.request_id FROM research_dispatch_holds h "
            "JOIN workflow_assignments a USING(assignment_id) WHERE a.run_id=?",
            (run["workflow_run_id"],),
        )
    )
    audit.check(
        "every_authorized_dispatch_has_packet_binding",
        all(sum(p["request_id"] == row[0] for _, p in bindings) == 1 for row in authorized),
    )
    return {
        "bound_packets": len(bindings),
        "original_bases": len(basis_events),
        "original_queries": query_count,
        "authorized_dispatches": len(authorized),
    }


PARSE_CODES = frozenset(
    {
        "packet_object_refused",
        "packet_schema_refused",
        "packet_code_refused",
        "packet_list_refused",
        "packet_duplicate_refused",
        "packet_predicate_refused",
        "packet_findings_refused",
        "packet_rationale_refused",
        "role_output_json_refused",
        "role_output_role_refused",
        "role_output_size_refused",
        "packet_version_refused",
    }
)
DECISIONS = {
    "director": {"proceed", "stop"},
    "hypothesis": {"propose", "stop"},
    "engineer": {"execute", "stop"},
    **{role: {"no_blocking_method_issue", "block", "inconclusive"} for role in ROLES[3:]},
}


def parser_diagnostics(raw, role, packet):
    """Fixed boolean categories only; invalid submitted tokens are never returned."""
    output = {"json_object": False}
    try:
        value = strict(raw)
    except Exception:
        return output
    if type(value) is not dict:
        return output
    output["json_object"] = True
    output["role_matches"] = value.get("role") == role
    decision, predicate = value.get("decision"), value.get("predicate")
    output["decision_allowed"] = type(decision) is str and decision in DECISIONS[role]
    output["predicate_allowed"] = (
        type(predicate) is str
        and predicate in packet["allowed_predicates"]
        or predicate is None
        and role in ROLES[:2]
    )
    aliases = value.get("artifact_aliases")
    aliases_valid = type(aliases) is list and all(
        type(item) is str and item in packet["artifact_aliases"] for item in aliases
    )
    output["aliases_allowed"] = aliases_valid
    findings = value.get("findings")
    output["finding_codes_allowed"] = type(findings) is list and all(
        type(item) is dict and type(item.get("code")) is str and item["code"] in FINDING_CODES
        for item in findings
    )
    output["finding_aliases_allowed"] = (
        aliases_valid
        and type(findings) is list
        and all(
            type(item) is dict
            and type(item.get("artifact_aliases")) is list
            and all(type(alias) is str and alias in aliases for alias in item["artifact_aliases"])
            for item in findings
        )
    )
    return output


def dispatch_observations(audit, run, config):
    """Inspect all actual sends independently of successfully published stage rows."""
    output, response_ids = [], set()
    rows = list(
        audit.db.execute(
            "SELECT h.*,a.role,a.contract,a.job_id FROM research_dispatch_holds h "
            "JOIN workflow_assignments a USING(assignment_id) WHERE a.run_id=?",
            (run["workflow_run_id"],),
        )
    )
    rows.sort(key=lambda row: ROLES.index(row["role"]))
    for hold in rows:
        role, request = hold["role"], hold["request_id"]
        prefix = role + ":"
        item = {
            "role": role,
            "response_observed": False,
            "inspection_state": "unavailable_or_invalid",
        }
        output.append(item)
        try:
            contract = strict(hold["contract"])
            packet = validate_packet(audit.obj(hold["packet_sha256"]))
            observation = audit.db.execute(
                "SELECT observation FROM research_model_observations WHERE request_id=?", (request,)
            ).fetchone()
            item["response_observed"] = observation is not None
            retained = audit.db.execute(
                "SELECT artifact_sha256 FROM research_private_responses WHERE request_id=?",
                (request,),
            ).fetchone()
            item["private_response_retained"] = retained is not None
            job = audit.one("SELECT state FROM jobs WHERE job_id=?", (hold["job_id"],))[0]
            item["job_state"] = (
                job
                if job in {"pending", "leased", "complete", "failed", "cancelled"}
                else "unrecognized"
            )
            effect = audit.db.execute(
                "SELECT * FROM workflow_effect_outcomes WHERE assignment_id=? AND request_id=?",
                (hold["assignment_id"], request),
            ).fetchone()
            effect_state = effect["status"] if effect else "pending"
            item["effect_state"] = (
                effect_state
                if effect_state in {"success", "failed", "uncertain", "pending"}
                else "unrecognized"
            )
            reservation = audit.one("SELECT * FROM reservations WHERE request_id=?", (request,))
            item["reservation_state"] = (
                reservation["state"]
                if reservation["state"] in {"held", "settled", "uncertain", "released"}
                else "unrecognized"
            )
            purpose = audit.one("SELECT * FROM provider_allocations WHERE request_id=?", (request,))
            dispatch = audit.one("SELECT * FROM dispatches WHERE request_id=?", (request,))
            audit.check(
                prefix + "dispatch_day_and_hold_identity",
                reservation["day"] == purpose["day"] == dispatch["day"]
                and purpose["purpose"] == "research"
                and purpose["amount"] == hold["amount"] == reservation["reserved_micro_usd"],
            )
            if retained is None:
                # A dispatched request can lose the response entirely. It has no
                # verified model or charge; the independent budget/event join
                # still requires its exact uncertain hold and consumed dispatch.
                unpublished = (
                    audit.db.execute(
                        "SELECT 1 FROM research_broker_stages WHERE assignment_id=?",
                        (hold["assignment_id"],),
                    ).fetchone()
                    is None
                )
                audit.check(
                    prefix + "uncertain_dispatch_without_private_response",
                    unpublished
                    and reservation["state"] == "uncertain"
                    and reservation["actual_micro_usd"] is None
                    and effect_state in {"uncertain", "pending"},
                )
                item.update(
                    inspection_state="uncertain_without_private_response",
                    actual_model_evidence=False,
                )
                continue
            private = audit.obj(retained[0])
            header = strict(observation[0]) if observation is not None else {}
            audit.check(
                prefix + "observed_envelope_matches_private_response",
                header.get("envelope_type") == "dict"
                and header.get("model") == private["observed_model"]
                and header.get("id") == private["provider_request_id"]
                and header.get("type") == "message"
                and header.get("stop_reason") == "end_turn",
            )
            intent = audit.one(
                "SELECT * FROM workflow_intents WHERE assignment_id=? AND request_id=?",
                (hold["assignment_id"], request),
            )
            claim = audit.one(
                "SELECT * FROM workflow_claims WHERE assignment_id=? AND fence=?",
                (hold["assignment_id"], intent["fence"]),
            )
            bound = audit.position(
                "workflow_broker_packet_bound",
                assignment_id=hold["assignment_id"],
                request_id=request,
                fence=intent["fence"],
            )
            authorized = audit.position("dispatch_authorized", request_id=request)
            audit.check(
                prefix + "all_dispatch_authorization_order",
                bound
                < audit.position("budget_reserved", request_id=request)
                < authorized
                < audit.position("workflow_research_dispatch_authorized", request_id=request)
                and audit.event_times[bound]
                <= audit.event_times[authorized]
                < datetime.fromisoformat(claim["deadline"]),
            )
            if effect is not None:
                finished = audit.position(
                    "workflow_effect_finished",
                    assignment_id=hold["assignment_id"],
                    request_id=request,
                )
                event = next(payload for number, _, payload in audit.events if number == finished)
                audit.check(
                    prefix + "effect_outcome_journal_identity",
                    event
                    == {
                        "assignment_id": hold["assignment_id"],
                        "request_id": request,
                        "status": effect["status"],
                        "artifact_refs": strict(effect["artifact_refs"]),
                        "observed_model": effect["observed_model"],
                    }
                    and authorized < finished,
                )
            if effect_state != "success":
                terminal = audit.db.execute(
                    "SELECT state FROM workflow_terminals WHERE assignment_id=?",
                    (hold["assignment_id"],),
                ).fetchone()
                audit.check(
                    prefix + "failed_effect_terminal_preserved",
                    terminal is not None and terminal[0] == effect_state and job == "failed",
                )
            messages = packet_messages(packet)
            prepared = prepare_research_text(
                model=contract["requested_model"],
                system=messages["system"],
                messages=messages["messages"],
                max_tokens=min(
                    4096 if contract["requested_model"] == OPUS else 2048,
                    max(1, contract["max_output_bytes"] // 4),
                ),
                max_input_bytes=contract["max_input_bytes"],
            )
            audit.check(
                prefix + "all_response_exact_body_binding",
                private["request_id"] == request
                and private["requested_model"]
                == contract["requested_model"]
                == config["models"][role]
                and private["body_sha256"] == hold["body_sha256"] == digest(prepared.body)
                and prepared.reserved_micro_usd == hold["amount"],
            )
            actual = (
                private["actual_model_evidence"] is True
                and private["transport_kind"] == hold["transport_kind"] == "anthropic_api"
                and private["observed_model"] == contract["requested_model"]
                and private["observed_model"] in {HAIKU, OPUS}
                and private["terminal"] == "completed"
            )
            item["actual_model_evidence"] = actual
            item["observed_model"] = (
                private["observed_model"]
                if private["observed_model"] in {HAIKU, OPUS}
                else "unrecognized"
            )
            audit.check(prefix + "dispatch_actual_model_confirmed", actual)
            audit.check(
                prefix + "dispatch_model_classification_truthful",
                actual
                or private["actual_model_evidence"] is False
                and private["transport_kind"] == hold["transport_kind"] == "synthetic_fixture",
            )
            audit.check(
                prefix + "response_identity_distinct",
                private["provider_request_id"] not in response_ids,
            )
            response_ids.add(private["provider_request_id"])
            required = next(
                (
                    p["predicate"]
                    for p in packet["prior_outputs"]
                    if p["role"] == "hypothesis" and p["decision"] == "propose"
                ),
                None,
            )
            try:
                parsed = parse_role_output(
                    private["reply"],
                    role,
                    packet["artifact_aliases"],
                    packet["allowed_predicates"],
                    required_predicate=required,
                )
                item["parser_state"] = "accepted"
                item["decision"] = parsed["decision"]
                item["finding_codes"] = sorted({f["code"] for f in parsed["findings"]})
            except PacketError as error:
                item["parser_state"] = "refused"
                item["parser_code"] = (
                    str(error) if str(error) in PARSE_CODES else "unclassified_refusal"
                )
                item["parser_diagnostics"] = parser_diagnostics(private["reply"], role, packet)
                audit.check(
                    prefix + "refused_output_not_successfully_published",
                    effect_state != "success"
                    and audit.db.execute(
                        "SELECT 1 FROM research_broker_stages WHERE assignment_id=?",
                        (hold["assignment_id"],),
                    ).fetchone()
                    is None,
                )
            audit.check(
                prefix + "accounting_matches_effect_state",
                (
                    effect_state == "success"
                    and reservation["state"] == "settled"
                    and reservation["actual_micro_usd"]
                    == private["cost_micro_usd"]
                    <= hold["amount"]
                )
                or (
                    effect_state != "success"
                    and reservation["state"] == "uncertain"
                    and reservation["actual_micro_usd"] is None
                ),
            )
            private_refs = {
                row[0]
                for row in audit.db.execute(
                    "SELECT artifact_sha256 FROM research_broker_aliases WHERE run_id=?",
                    (run["workflow_run_id"],),
                )
            }
            audit.check(
                prefix + "all_responses_remain_private",
                retained[0] not in private_refs
                and (effect is None or retained[0] not in strict(effect["artifact_refs"])),
            )
            item["inspection_state"] = "inspected"
        except Exception:
            audit.check(prefix + "observed_dispatch_inspected", False)
    return output


def inspect(store, receipt_raw, request_raw):
    audit = Audit(store)
    result = {
        "schema_version": 1,
        "kind": "independent_partial_qualified_context_trace_inspection",
        "inspector_sha256": digest(Path(__file__).read_bytes()),
        "evidence_scope": "lifecycle_and_method_only",
        "operational_acceptance": False,
        "financial_values_inspected_by_model": False,
        "roles": [],
    }
    try:
        receipt = strict(receipt_raw)
        result["receipt_sha256"] = digest(receipt_raw)
        result["journal"] = audit.chain()
        parent = audit.sub(receipt["submission_id"])
        result["observed_status"] = (
            parent["status"] if parent["status"] in STATES else "unrecognized"
        )
        audit.check("receipt_matches_persisted_status", receipt["status"] == parent["status"])
        audit.check("broker_submission_kind", parent["kind"] == "research_broker_run")
        record = audit.obj(receipt["artifact_sha256"])
        audit.check(
            "record_is_parent_outcome_artifact",
            receipt["artifact_sha256"] in parent["details"].get("artifact_refs", []),
        )
        expected_receipt = {
            **record,
            "submission_id": receipt["submission_id"],
            "artifact_sha256": receipt["artifact_sha256"],
            "status": parent["status"],
        }
        audit.check(
            "receipt_fields_match_retained_record",
            hash_json(receipt) == hash_json(expected_receipt),
        )
        audit.check(
            "parent_outcome_journal_matches",
            next(
                value
                for number, kind, value in audit.events
                if number
                == audit.position("submission_finished", submission_id=receipt["submission_id"])
            )
            == {
                "submission_id": receipt["submission_id"],
                "status": parent["status"],
                "details": parent["details"],
            },
        )
        run = audit.one(
            "SELECT * FROM research_broker_runs WHERE submission_id=?", (receipt["submission_id"],)
        )
        config = audit.obj(run["configuration_sha256"])
        audit.check(
            "record_registry_binding",
            record["workflow_run_id"] == run["workflow_run_id"]
            and (
                "configuration_sha256" not in record
                or record["configuration_sha256"] == run["configuration_sha256"]
            )
            and (
                "code_identity" not in record or record["code_identity"] == config["code_identity"]
            ),
        )
        result["parent_record_shape"] = (
            "exception_publication" if "completed_stages" in record else "normal_publication"
        )
        registry_roles = [
            row[0]
            for row in audit.db.execute(
                "SELECT role FROM research_broker_stages WHERE submission_id=?",
                (receipt["submission_id"],),
            )
        ]
        audit.check(
            "published_roster_matches_parent_record",
            len(registry_roles) == len(record["stages"])
            and set(registry_roles) == {stage["role"] for stage in record["stages"]}
            and (
                "completed_stages" not in record
                or record["completed_stages"] == len(registry_roles)
            ),
        )
        manifest = strict(
            audit.one(
                "SELECT manifest FROM workflow_runs WHERE run_id=?", (run["workflow_run_id"],)
            )[0]
        )
        base = {
            key: config[key]
            for key in ("run_key", "suite_sha256", "failure_ids", "models", "evidence_kind")
        }
        audit.check(
            "exact_configuration_binding",
            hash_json(base) == manifest["specification_sha256"]
            and strict(request_raw) == base
            and digest(request_raw) == parent["request_sha256"],
        )
        audit.check(
            "exact_current_code_binding",
            config["code_identity"] == code_identity()
            and hash_json(config["code_identity"]) == run["code_sha256"] == manifest["code_sha256"],
        )
        audit.check(
            "historical_development_classification",
            base["evidence_kind"] == manifest["evidence_kind"] == "historical_market_data",
        )
        audit.check("acceptance_not_self_certified", record.get("operational_acceptance") is False)
        suite_manifest = audit.obj(config["suite_sha256"])
        audit.check(
            "bound_registered_suite_identity",
            suite_manifest["kind"] == "study_suite"
            and suite_manifest["policy_revision_sha256"]
            == config["verified_policy_revision_sha256"],
        )
        result["failure_context_counts"] = failure_bindings(
            audit, receipt["submission_id"], run, config
        )
        result["dispatch_observations"] = dispatch_observations(audit, run, config)
        audit.check(
            "parent_dispatch_counts_match_registry",
            record["dispatch_counts"]
            == {
                "authorized": len(result["dispatch_observations"]),
                "response_observed": sum(
                    item["response_observed"] for item in result["dispatch_observations"]
                ),
            },
        )
        result["observed_actual_response_count"] = sum(
            item.get("actual_model_evidence") is True for item in result["dispatch_observations"]
        )
        prior, selected, stage_refs, actual_ids = [], None, {}, set()
        actual_count = 0
        proof_refs = set()
        for role in ROLES:
            safe = {"role": role, "inspection_state": "unavailable_or_invalid"}
            result["roles"].append(safe)
            prefix = role + ":"
            issued = audit.db.execute(
                "SELECT assignment_id FROM workflow_assignments WHERE run_id=? AND role=?",
                (run["workflow_run_id"], role),
            ).fetchone()
            if issued is None:
                safe["inspection_state"] = "not_issued"
                audit.check(
                    prefix + "absent_after_terminal",
                    parent["status"] == "invalid"
                    and (
                        "completed_stages" in record
                        or bool(prior)
                        and prior[-1]["decision"] == "stop"
                    ),
                )
                continue
            published = audit.db.execute(
                "SELECT 1 FROM research_broker_stages WHERE submission_id=? AND role=?",
                (receipt["submission_id"], role),
            ).fetchone()
            if not published:
                safe["inspection_state"] = "issued_not_published"
                audit.check(
                    prefix + "unpublished_stage_not_claimed",
                    role not in registry_roles
                    and not any(stage["role"] == role for stage in record["stages"]),
                )
                continue
            try:
                row = audit.one(
                    "SELECT * FROM research_broker_stages WHERE submission_id=? AND role=?",
                    (receipt["submission_id"], role),
                )
                stage = audit.obj(row["record_sha256"])
                assignment = audit.one(
                    "SELECT * FROM workflow_assignments WHERE assignment_id=?",
                    (row["assignment_id"],),
                )
                audit.check(
                    prefix + "record_stage_binding",
                    stage in record.get("stages", [])
                    and stage["assignment_id"] == row["assignment_id"],
                )
                audit.check(
                    prefix + "issued_role",
                    assignment["run_id"] == run["workflow_run_id"] and assignment["role"] == role,
                )
                contract = strict(assignment["contract"])
                context = audit.obj(stage["model_packet_sha256"])
                audit.check(
                    prefix + "typed_private_free_packet",
                    validate_packet(context) == context
                    and context["role"] == role
                    and context["access_class"] == "sanitized_development"
                    and context["data_values_disclosed"] is False,
                )
                audit.check(prefix + "exact_prior_projections", context["prior_outputs"] == prior)
                aliases = {
                    r["alias"]: r["artifact_sha256"]
                    for r in audit.db.execute(
                        "SELECT * FROM research_broker_aliases WHERE run_id=?",
                        (run["workflow_run_id"],),
                    )
                }
                audit.check(
                    prefix + "exact_alias_scope",
                    set(context["artifact_aliases"]) == set(stage["alias_bindings"])
                    and all(aliases[k] == v for k, v in stage["alias_bindings"].items()),
                )
                held = list(
                    audit.db.execute(
                        "SELECT * FROM research_dispatch_holds WHERE assignment_id=?",
                        (row["assignment_id"],),
                    )
                )
                audit.check(prefix + "single_dispatch", len(held) == 1)
                hold = held[0]
                req = hold["request_id"]
                proof_ref = stage["method_verification_sha256"]
                proof = audit.obj(proof_ref)
                proof_refs.add(proof_ref)
                audit.check(
                    prefix + "exact_integrity_observation",
                    set(proof)
                    == {
                        "schema_version",
                        "kind",
                        "role",
                        "configuration_sha256",
                        "suite_sha256",
                        "policy_revision_sha256",
                        "verified_at",
                        "method",
                        "suite_integrity",
                        "failure_context_sha256",
                        "failure_basis_sha256",
                        "failure_facts_sha256",
                    }
                    and type(proof["schema_version"]) is int
                    and proof["schema_version"] == 1
                    and proof["kind"] == "research_suite_integrity_observation"
                    and proof["role"] == role
                    and proof["configuration_sha256"] == run["configuration_sha256"]
                    and proof["suite_sha256"] == config["suite_sha256"]
                    and proof["policy_revision_sha256"] == config["verified_policy_revision_sha256"]
                    and proof["method"] == context["method"] == METHOD
                    and proof["suite_integrity"] == context["suite_integrity"] == SUITE_INTEGRITY,
                )
                audit.check(
                    prefix + "proof_remains_private",
                    proof_ref in stage["private_tool_refs"]
                    and proof_ref not in stage["alias_bindings"].values(),
                )
                intent = audit.one(
                    "SELECT * FROM workflow_intents WHERE assignment_id=? AND request_id=?",
                    (row["assignment_id"], req),
                )
                binding = {
                    "parent_submission_id": receipt["submission_id"],
                    "assignment_id": row["assignment_id"],
                    "role": role,
                    "fence": intent["fence"],
                    "request_id": req,
                    "configuration_sha256": run["configuration_sha256"],
                    "packet_sha256": stage["model_packet_sha256"],
                    "verification_sha256": proof_ref,
                    "failure_context_sha256": proof["failure_context_sha256"],
                    "failure_basis_sha256": proof["failure_basis_sha256"],
                }
                bound_at = audit.position("workflow_broker_packet_bound", **binding)
                exact_event = next(value for number, _, value in audit.events if number == bound_at)
                audit.check(
                    prefix + "exact_predispatch_binding",
                    exact_event == binding
                    and stage["model_request_id"] == req
                    and intent["action"] == "dispatch_model"
                    and hold["assignment_id"] == binding["assignment_id"]
                    and hold["packet_sha256"] == binding["packet_sha256"],
                )
                budget_at = audit.position("budget_reserved", request_id=req)
                dispatch_at = audit.position(
                    "workflow_research_dispatch_authorized", request_id=req
                )
                journal_dispatch_at = audit.position("dispatch_authorized", request_id=req)
                verified_time = datetime.fromisoformat(proof["verified_at"])
                audit.check(
                    prefix + "proof_bound_before_spend_and_dispatch",
                    bound_at < budget_at < journal_dispatch_at < dispatch_at
                    and verified_time
                    <= audit.event_times[bound_at]
                    <= audit.event_times[budget_at]
                    <= audit.event_times[journal_dispatch_at],
                )
                claim = audit.one(
                    "SELECT * FROM workflow_claims WHERE assignment_id=? AND fence=?",
                    (row["assignment_id"], intent["fence"]),
                )
                audit.check(
                    prefix + "binding_within_frozen_claim_deadline",
                    audit.event_times[bound_at]
                    <= audit.event_times[journal_dispatch_at]
                    < datetime.fromisoformat(claim["deadline"]),
                )
                reservation = audit.one("SELECT * FROM reservations WHERE request_id=?", (req,))
                dispatch = audit.one("SELECT * FROM dispatches WHERE request_id=?", (req,))
                purpose = audit.one("SELECT * FROM provider_allocations WHERE request_id=?", (req,))
                outcome = audit.one(
                    "SELECT * FROM workflow_effect_outcomes WHERE assignment_id=? AND request_id=?",
                    (row["assignment_id"], req),
                )
                private_ref = audit.one(
                    "SELECT artifact_sha256 FROM research_private_responses WHERE request_id=?",
                    (req,),
                )[0]
                private = audit.obj(private_ref)
                audit.check(
                    prefix + "private_response_excluded",
                    private_ref not in stage["alias_bindings"].values()
                    and private_ref not in strict(outcome["artifact_refs"]),
                )
                packet = packet_messages(context)
                maximum = min(
                    4096 if contract["requested_model"] == OPUS else 2048,
                    max(1, contract["max_output_bytes"] // 4),
                )
                prepared = prepare_research_text(
                    model=contract["requested_model"],
                    system=packet["system"],
                    messages=packet["messages"],
                    max_tokens=maximum,
                    max_input_bytes=contract["max_input_bytes"],
                )
                audit.check(
                    prefix + "exact_dispatched_packet",
                    hold["packet_sha256"] == stage["model_packet_sha256"]
                    and hold["body_sha256"] == digest(prepared.body) == private["body_sha256"],
                )
                parsed = parse_role_output(
                    private["reply"],
                    role,
                    context["artifact_aliases"],
                    context["allowed_predicates"],
                    required_predicate=selected if role in ROLES[2:] else None,
                )
                projection = audit.obj(stage["projection_sha256"])
                audit.check(
                    prefix + "actual_response_authored_projection",
                    project_role_output(parsed) == projection,
                )
                if role == "hypothesis":
                    selected = projection["predicate"]
                if role in ROLES[2:]:
                    audit.check(
                        prefix + "selected_predicate_preserved", projection["predicate"] == selected
                    )
                receipt_local = stage["model_receipt"]
                observed = private["observed_model"]
                actual = (
                    observed == contract["requested_model"] == config["models"][role]
                    and observed in {HAIKU, OPUS}
                    and private["actual_model_evidence"] is True
                    and private["transport_kind"] == hold["transport_kind"] == "anthropic_api"
                    and receipt_local["actual_model_evidence"] is True
                    and private["terminal"] == "completed"
                )
                audit.check(prefix + "actual_model_confirmed", actual)
                audit.check(
                    prefix + "exact_public_receipt",
                    all(
                        receipt_local[key] == private[key]
                        for key in (
                            "observed_model",
                            "usage",
                            "cost_micro_usd",
                            "cost_kind",
                            "elapsed_seconds",
                            "transport_kind",
                            "actual_model_evidence",
                            "terminal",
                        )
                    )
                    and receipt_local["request_id"] == req
                    and private["request_id"] == req,
                )
                actual_ids.add(private["provider_request_id"])
                actual_count += int(actual)
                audit.check(
                    prefix + "model_classification_truthful",
                    actual
                    or (
                        private["actual_model_evidence"] is False
                        and receipt_local["actual_model_evidence"] is False
                        and private["transport_kind"]
                        == hold["transport_kind"]
                        == "synthetic_fixture"
                    ),
                )
                audit.check(
                    prefix + "budget_settled_with_retained_purpose_hold",
                    reservation["state"] == "settled"
                    and reservation["day"] == dispatch["day"] == purpose["day"]
                    and purpose["purpose"] == "research"
                    and purpose["amount"] == hold["amount"] == prepared.reserved_micro_usd
                    and reservation["reserved_micro_usd"] == hold["amount"]
                    and reservation["actual_micro_usd"]
                    == private["cost_micro_usd"]
                    <= hold["amount"],
                )
                audit.check(
                    prefix + "effect_and_handoff_consistent",
                    outcome["status"] == "success"
                    and audit.obj(stage["handoff_sha256"])["state"]
                    == ("blocked" if parsed["decision"] == "stop" else "complete"),
                )
                audit.check(
                    prefix + "authorization_precedes_completion",
                    audit.position("workflow_research_dispatch_authorized", request_id=req)
                    < audit.position(
                        "workflow_effect_finished",
                        request_id=req,
                        assignment_id=row["assignment_id"],
                    ),
                )
                prior.append(projection)
                stage_refs[role] = stage["projection_sha256"]
                safe.update(
                    inspection_state="inspected",
                    actual_model_evidence=actual,
                    observed_model=observed if observed in {HAIKU, OPUS} else "unrecognized",
                    decision=parsed["decision"],
                    finding_codes=sorted({f["code"] for f in parsed["findings"]}),
                    packet_sha256=stage["model_packet_sha256"],
                    projection_sha256=stage["projection_sha256"],
                )
            except Exception:
                audit.check(prefix + "complete_inspection", False)
        audit.check(
            "separate_integrity_observation_per_completed_stage", len(proof_refs) == len(prior)
        )
        audit.check("distinct_actual_response_ids", len(actual_ids) == len(prior))
        audit.check("seven_actual_roles", result["observed_actual_response_count"] == 7)
        result["selected_method_predicate"] = selected if selected in PREDICATES else "unavailable"
        result["published_actual_role_count"] = actual_count
        result["published_stage_count"] = len(prior)
        reviews = [p for p in prior if p["role"] in ROLES[3:]]
        expected_review = (
            "not_reached"
            if not reviews
            else "incomplete"
            if len(reviews) < 4
            else "blocked"
            if any(p["decision"] == "block" for p in reviews)
            else "method_no_blockers"
            if all(p["decision"] == "no_blocking_method_issue" for p in reviews)
            else "inconclusive"
        )
        audit.check(
            "review_summary_matches_published_roster",
            record.get("review_outcome") == expected_review,
        )
        result["review_outcome"] = expected_review
        links = list(
            audit.db.execute(
                "SELECT r.*,c.child_submission_id FROM research_broker_tool_requests r "
                "LEFT JOIN research_broker_tool_children c USING(assignment_id,request_id) WHERE parent_submission_id=?",
                (receipt["submission_id"],),
            )
        )
        executed = next(
            (p["decision"] == "execute" for p in prior if p["role"] == "engineer"), False
        )
        if executed:
            audit.check(
                "one_exact_parent_child_link",
                len(links) == 1 and links[0]["child_submission_id"] is not None,
            )
        else:
            audit.check("no_comparison_link_after_stop", not links)
            count = audit.one(
                "SELECT COUNT(*) FROM workflow_intents i JOIN workflow_assignments a USING(assignment_id) WHERE a.run_id=? AND i.action='launch_development'",
                (run["workflow_run_id"],),
            )[0]
            audit.check("no_financial_launch_after_stop", count == 0)
        if len(links) == 1 and links[0]["child_submission_id"]:
            link = links[0]
            comparison = audit.sub(link["child_submission_id"])
            request = audit.obj(link["request_sha256"])
            registration = audit.obj(comparison["details"]["registration_sha256"])
            audit.check(
                "comparison_registration_exact_method_and_suite",
                registration["request"] == request
                and registration["suite_manifest"] == suite_manifest,
            )
            launch_intent = audit.one(
                "SELECT * FROM workflow_intents WHERE assignment_id=? AND request_id=?",
                (link["assignment_id"], link["request_id"]),
            )
            launch_assignment = audit.one(
                "SELECT * FROM workflow_assignments WHERE assignment_id=?", (link["assignment_id"],)
            )
            audit.check(
                "comparison_parent_is_issued_engineer_effect",
                launch_assignment["role"] == "engineer"
                and launch_assignment["run_id"] == run["workflow_run_id"]
                and launch_intent["action"] == "launch_development"
                and launch_intent["fence"] == link["fence"],
            )
            audit.check(
                "comparison_effect_registered_before_child_binding",
                audit.position(
                    "workflow_broker_tool_registered",
                    assignment_id=link["assignment_id"],
                    request_id=link["request_id"],
                )
                < audit.position(
                    "workflow_effect_started",
                    assignment_id=link["assignment_id"],
                    request_id=link["request_id"],
                )
                < audit.position("submission_started", submission_id=link["child_submission_id"])
                < audit.position(
                    "workflow_broker_tool_child_bound",
                    child_submission_id=link["child_submission_id"],
                ),
            )
            audit.check(
                "model_choice_materially_bound",
                request
                == {
                    "suite_sha256": config["suite_sha256"],
                    "predicate": selected,
                    "hypothesis_sha256": stage_refs.get("hypothesis"),
                    "engineer_sha256": stage_refs.get("engineer"),
                },
            )
            audit.check(
                "comparison_success_and_exact_request",
                comparison["status"] == "success"
                and comparison["request_sha256"] == link["request_sha256"],
            )
            run_id = audit.one(
                "SELECT suite_run_id FROM research_comparison_invocations WHERE submission_id=?",
                (link["child_submission_id"],),
            )[0]
            suite = audit.sub(run_id)
            suite_row = audit.one("SELECT * FROM study_suite_runs WHERE submission_id=?", (run_id,))
            audit.check(
                "fresh_suite_matches_exact_bound_suite",
                suite_row["suite_sha256"] == config["suite_sha256"]
                and suite["details"].get("suite_sha256") == config["suite_sha256"],
            )
            private_derivative = audit.obj(comparison["details"]["comparison_sha256"])
            audit.check(
                "derivative_uses_exact_new_suite",
                private_derivative["suite_run_id"] == run_id
                and private_derivative["submission_id"] == link["child_submission_id"]
                and private_derivative["registration_sha256"]
                == comparison["details"]["registration_sha256"]
                and private_derivative["predicate"] == selected
                and private_derivative["investment_evidence"] is False,
            )
            child_sources = private_derivative["child_sources"]
            children = list(
                audit.db.execute(
                    "SELECT * FROM study_suite_results WHERE run_id=? ORDER BY cost_bps", (run_id,)
                )
            )
            audit.check(
                "new_complete_three_child_suite",
                suite["status"] == "success"
                and [r["cost_bps"] for r in children] == [0, 10, 25]
                and len({r["child_submission_id"] for r in children}) == 3,
            )
            audit.check(
                "binding_precedes_fresh_calculation",
                audit.position(
                    "workflow_broker_tool_child_bound",
                    child_submission_id=link["child_submission_id"],
                )
                < audit.position(
                    "research_comparison_registered", submission_id=link["child_submission_id"]
                )
                < audit.position("submission_started", submission_id=run_id),
            )
            for number, child in enumerate(children):
                saved = audit.sub(child["child_submission_id"])
                audit.check(
                    "suite_child_" + str(number) + "_registered_before_calculation",
                    audit.position("submission_started", submission_id=run_id)
                    < audit.position(
                        "study_suite_member_launched", run_id=run_id, cost_bps=child["cost_bps"]
                    )
                    < audit.position(
                        "submission_started", submission_id=child["child_submission_id"]
                    )
                    < audit.position(
                        "study_suite_member_bound",
                        run_id=run_id,
                        cost_bps=child["cost_bps"],
                        child_submission_id=child["child_submission_id"],
                    ),
                )
                audit.check(
                    "suite_child_" + str(number) + "_derivative_source_bound",
                    child_sources[number]["submission_id"] == child["child_submission_id"]
                    and child_sources[number]["cost_bps"] == child["cost_bps"]
                    and child_sources[number]["request_sha256"] == saved["request_sha256"]
                    and child_sources[number]["details"] == saved["details"],
                )
                audit.check(
                    "suite_child_" + str(number) + "_exact_success",
                    saved["status"] == "success"
                    and saved["kind"] == "exploratory_study"
                    and saved["details"].get("suite_run_id") == run_id
                    and saved["details"].get("suite_sha256") == config["suite_sha256"]
                    and saved["details"].get("evidence_kind") == "historical_market_data",
                )
        audit.check(
            "all_seven_stages_completed",
            len(prior) == 7 and record.get("all_stages_completed") is True,
        )
    except Exception:
        audit.check("trace_inspection_completed", False)
    finally:
        result["checks"] = audit.checks
        result["all_checks_passed"] = bool(audit.checks) and all(audit.checks.values())
        acceptance_checks = {
            "all_seven_stages_completed",
            "seven_actual_roles",
            "historical_development_classification",
        }
        acceptance_checks.update(role + ":actual_model_confirmed" for role in ROLES)
        acceptance_checks.update(role + ":dispatch_actual_model_confirmed" for role in ROLES)
        result["observed_trace_consistent"] = bool(audit.checks) and all(
            value for key, value in audit.checks.items() if key not in acceptance_checks
        )
        current_keys = {key for key in audit.checks if key.endswith(":current_context_revalidated")}
        result["current_context_revalidation_passed"] = bool(current_keys) and all(
            audit.checks[key] for key in current_keys
        )
        result["retained_lifecycle_checks_passed"] = bool(audit.checks) and all(
            value
            for key, value in audit.checks.items()
            if key not in acceptance_checks | current_keys
        )
        result["artifact_count_inspected"] = len(audit.refs)
        result["inspected_artifact_set_sha256"] = hash_json(sorted(audit.refs))
        result["numerical_validation_performed"] = False
        result["current_context_check_scope"] = "inspection_time_shared_production_validator"
        # Borrowed guarded store: caller owns its lifecycle.
    return result

"""Attributed structural/numerical joins adapted from retained v5 source.
This is a new module, never an entrypoint to a consumed actual verifier.
Fixture mode preserves synthetic classification and never counts actual models.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
import re

from quanto.ledger import canonical_json, hash_bytes, hash_json

ORACLE_SHA256 = "54887dfae2f12430b5cdd9901c0c3ba367541f6eb4714b987ad68e08f0433ca1"
ROLES = (
    "director",
    "hypothesis",
    "engineer",
    "data_critic",
    "statistical_critic",
    "quality",
    "scope",
)
COSTS = (0, 10, 25)
PREDICATES = frozenset(
    (
        "cost_ending_equity_nonincreasing",
        "cost_fees_nondecreasing",
        "strategy_equals_benchmark_terminal",
    )
)
SOURCE_NAMES = (
    "research_broker.py",
    "research_packets.py",
    "research_dispatch.py",
    "research_comparison.py",
    "research_workflow.py",
    "failure_memory.py",
    "provider.py",
    "research_failure_context.py",
)
HEX = re.compile(r"[0-9a-f]{64}\Z")
IDENTIFIER = re.compile(r"[0-9a-f]{32}\Z")
DECIMAL_TEXT = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:E[+-][0-9]+)?\Z")


class IntegrityRefusal(Exception):
    """Fixed bounded error code; never include submitted/private values."""


def require(condition, code):
    if not condition:
        raise IntegrityRefusal(code)


def same(left, right):
    return hash_json(left) == hash_json(right)


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "ambiguous_json")
            result[key] = value
        return result

    def constant(_):
        raise IntegrityRefusal("nonfinite_json")

    require(isinstance(raw, bytes) and len(raw) <= 16 * 1024 * 1024, "json_byte_bound")
    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    canonical_json(result)
    return result


def _normalized_specification(value):
    """Expand only the documented StrategySpec defaults for identity comparison.

    This does not alter a study or fill market observations. Explicit submitted
    values retain their JSON types, and unknown fields refuse.
    """
    allowed = {"lookback", "entry_threshold", "exit_threshold", "starting_cash", "cost_bps"}
    require(
        type(value) is dict and set(value) <= allowed and "lookback" in value,
        "financial_specification_fields_refused",
    )
    result = {
        "entry_threshold": 0.0,
        "exit_threshold": 0.0,
        "starting_cash": 10000.0,
        "cost_bps": 0.0,
        **value,
    }
    require(
        type(result["lookback"]) is int and result["lookback"] > 0,
        "financial_specification_lookback_refused",
    )
    require(
        all(type(result[key]) in (int, float) for key in allowed - {"lookback"})
        and all(Decimal(str(result[key])).is_finite() for key in allowed - {"lookback"})
        and result["starting_cash"] > 0
        and 0 <= result["cost_bps"] < 10000
        and 0 <= result["entry_threshold"] < 1
        and 0 <= result["exit_threshold"] < 1,
        "financial_specification_values_refused",
    )
    return result


def _validate_financial_report(request, result, admitted, numerical_policy):
    """Compare full declared engine metadata without changing registered bytes."""
    declared = _normalized_specification(request["specification"])
    frozen = {
        "strategy": declared,
        "evaluation_start": request["evaluation_start"],
        "evaluation_end": request["evaluation_end"],
        "initial_position": "cash",
        "benchmark": "buy_and_hold_same_window_same_costs",
        "purpose": "exploratory",
        "admission_scope": admitted["scope"],
        "numerical_policy": numerical_policy,
    }
    require(same(result["frozen_request"], frozen), "frozen_financial_request_mismatch")
    report = result["engine_report"]
    require(
        report["evaluation_start"] == request["evaluation_start"]
        and report["evaluation_end"] == request["evaluation_end"]
        and report["evidence_kind"] == "historical_market_data",
        "report_window_or_evidence_mismatch",
    )
    require(
        same(
            report["specification"],
            {key: value if key == "lookback" else str(value) for key, value in declared.items()},
        ),
        "report_specification_mismatch",
    )
    return report


def number(value):
    require(
        type(value) is str and len(value) <= 128 and DECIMAL_TEXT.fullmatch(value),
        "operand_encoding_refused",
    )
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        raise IntegrityRefusal("operand_decimal_refused") from None
    require(
        parsed.is_finite()
        and parsed >= 0
        and len(parsed.as_tuple().digits) <= 34
        and abs(parsed.adjusted()) <= 999999
        and str(parsed) == value
        and (bool(parsed) or value == "0"),
        "operand_decimal_refused",
    )
    return parsed


def independent_predicate(predicate, operands):
    """Independent exact comparisons; no research_comparison import/evaluate."""
    require(predicate in PREDICATES and len(operands) == 3, "unsupported_predicate_or_roster")
    require([item["cost_bps"] for item in operands] == list(COSTS), "derivative_cost_order")
    equity = [number(item["strategy_ending_equity"]) for item in operands]
    fees = [number(item["strategy_total_fees"]) for item in operands]
    benchmark = [number(item["benchmark_ending_equity"]) for item in operands]
    if predicate == "cost_ending_equity_nonincreasing":
        return equity[0] >= equity[1] and equity[1] >= equity[2]
    if predicate == "cost_fees_nondecreasing":
        return fees[0] <= fees[1] and fees[1] <= fees[2]
    return all(left == right for left, right in zip(equity, benchmark))


class Trace:
    def __init__(self, store):
        self.store = store
        self.db = store.journal.connection
        self.events = [
            (row["id"], row["kind"], strict_json(row["payload"].encode()))
            for row in self.db.execute("SELECT id,kind,payload FROM events ORDER BY id")
        ]

    def event(self, kind, **match):
        matches = [
            (position, value)
            for position, observed, value in self.events
            if observed == kind and all(value.get(key) == item for key, item in match.items())
        ]
        require(len(matches) == 1, "lineage_event_missing_or_ambiguous")
        return matches[0]

    def start(self, submission):
        return self.event("submission_started", submission_id=submission)[0]

    def finish(self, submission):
        return self.event("submission_finished", submission_id=submission, status="success")[0]

    def one(self, sql, args=()):
        rows = self.db.execute(sql, args).fetchall()
        require(len(rows) == 1, "lineage_row_missing_or_ambiguous")
        return rows[0]

    def submission(self, identity, kind):
        require(
            type(identity) is str and IDENTIFIER.fullmatch(identity), "invalid_submission_identity"
        )
        value = self.store.get_submission(identity)
        require(
            value["kind"] == kind and value["status"] == "success",
            "unsuccessful_or_wrong_submission",
        )
        for digest in value["details"].get("artifact_refs", []):
            self.store.read_bytes(digest)
        finished = self.event("submission_finished", submission_id=identity, status="success")[1]
        require(same(finished["details"], value["details"]), "submission_event_details_mismatch")
        return value


def trace_workflow(store, saved, codes, *, fixture_only=False):
    evidence = "synthetic_fixture" if fixture_only else "historical_market_data"
    transport = "synthetic_fixture" if fixture_only else "anthropic_api"
    """Verify fresh durable lineage independently, without running any study."""
    trace = Trace(store)
    require(
        type(saved) is dict
        and all(key in saved for key in ("submission_id", "artifact_sha256", "status")),
        "lifecycle_receipt_missing",
    )
    require(saved["status"] in {"success", "invalid"}, "broker_not_terminal")
    parent_id, parent_ref = saved["submission_id"], saved["artifact_sha256"]
    require(
        type(parent_id) is str and IDENTIFIER.fullmatch(parent_id),
        "invalid_broker_submission_identity",
    )
    parent = store.get_submission(parent_id)
    require(
        parent["kind"] == "research_broker_run" and parent["status"] in {"success", "invalid"},
        "broker_not_terminal",
    )
    parent_finished = trace.event(
        "submission_finished", submission_id=parent_id, status=parent["status"]
    )[1]
    require(same(parent_finished["details"], parent["details"]), "broker_outcome_event_mismatch")
    require(parent["details"]["artifact_refs"] == [parent_ref], "broker_artifact_binding_mismatch")
    record = store.read_json(parent_ref)
    expected = {
        **record,
        "submission_id": parent_id,
        "artifact_sha256": parent_ref,
        "status": parent["status"],
    }
    require(
        same(saved, expected),
        "saved_broker_receipt_mismatch",
    )
    require(
        record["evidence_kind"] == evidence
        and record["operational_acceptance"] is False
        and record["investment_validation"] is False,
        "actual_workflow_or_scope_mismatch",
    )
    require(
        same(record["code_identity"]["sources"], codes["sources"]), "broker_source_identity_changed"
    )
    run = trace.one("SELECT * FROM research_broker_runs WHERE submission_id=?", (parent_id,))
    require(
        run["workflow_run_id"] == record["workflow_run_id"]
        and run["configuration_sha256"] == record["configuration_sha256"]
        and run["code_sha256"] == hash_json(record["code_identity"]),
        "broker_registry_mismatch",
    )
    config = store.read_json(run["configuration_sha256"])
    require(
        config["evidence_kind"] == evidence
        and same(config["code_identity"], record["code_identity"]),
        "broker_configuration_mismatch",
    )
    stages = record["stages"]
    require(
        type(stages) is list
        and 1 <= len(stages) <= 7
        and [s["role"] for s in stages] == list(ROLES[: len(stages)]),
        "stage_roster_mismatch",
    )
    require(
        record["dispatch_counts"] == {"authorized": len(stages), "response_observed": len(stages)},
        "actual_dispatch_roster_mismatch",
    )
    observed_count = trace.db.execute(
        "SELECT COUNT(*) FROM research_dispatch_holds h JOIN workflow_assignments a USING(assignment_id) WHERE a.run_id=?",
        (run["workflow_run_id"],),
    ).fetchone()[0]
    require(observed_count == len(stages), "extra_unreported_model_dispatch")
    stage_rows = trace.db.execute(
        "SELECT * FROM research_broker_stages WHERE submission_id=?", (parent_id,)
    ).fetchall()
    require(len(stage_rows) == len(stages), "stage_registry_roster_mismatch")
    by_role = {row["role"]: row for row in stage_rows}
    projections, actors, attributed_requests = {}, set(), []
    packet_bindings_checked = 0
    for stage in stages:
        role = stage["role"]
        require(
            by_role[role]["assignment_id"] == stage["assignment_id"]
            and same(store.read_json(by_role[role]["record_sha256"]), stage),
            "stage_record_mismatch",
        )
        assignment = trace.one(
            "SELECT * FROM workflow_assignments WHERE assignment_id=?", (stage["assignment_id"],)
        )
        require(
            assignment["run_id"] == run["workflow_run_id"] and assignment["role"] == role,
            "stage_assignment_mismatch",
        )
        require(assignment["actor_id"] not in actors, "stage_actor_reused")
        actors.add(assignment["actor_id"])
        contract = strict_json(assignment["contract"].encode())
        receipt = stage["model_receipt"]
        require(
            receipt["transport_kind"] == transport
            and receipt["actual_model_evidence"] is (not fixture_only)
            and receipt["terminal"] == "completed"
            and receipt["requested_model"]
            == receipt["observed_model"]
            == contract["requested_model"]
            == config["models"][role],
            "actual_model_receipt_mismatch",
        )
        require(
            stage["model_request_id"] == receipt["request_id"], "planned_model_request_mismatch"
        )
        bound_position, bound = trace.event(
            "workflow_broker_packet_bound",
            parent_submission_id=parent_id,
            assignment_id=assignment["assignment_id"],
            role=role,
            request_id=receipt["request_id"],
        )
        require(
            bound["configuration_sha256"] == run["configuration_sha256"]
            and bound["packet_sha256"] == stage["model_packet_sha256"]
            and bound["verification_sha256"] == stage["method_verification_sha256"],
            "packet_proof_stage_binding_mismatch",
        )
        packet = store.read_json(bound["packet_sha256"])
        proof = store.read_json(bound["verification_sha256"])
        failure = store.read_json(proof["failure_context_sha256"])
        require(
            bound["failure_context_sha256"] == proof["failure_context_sha256"]
            and bound["failure_basis_sha256"] == proof["failure_basis_sha256"]
            and failure["configuration_sha256"] == run["configuration_sha256"]
            and failure["basis_sha256"] == proof["failure_basis_sha256"]
            and failure["role"] == role
            and same(failure["failures"], packet["failures"])
            and proof["failure_facts_sha256"] == hash_json(packet["failures"]),
            "failure_context_join_mismatch",
        )
        require(
            proof["failure_context_sha256"] not in stage["alias_bindings"].values()
            and proof["failure_basis_sha256"] not in stage["alias_bindings"].values(),
            "private_failure_evidence_in_aliases",
        )
        require(
            packet["role"] == proof["role"] == role
            and proof["kind"] == "research_suite_integrity_observation"
            and proof["configuration_sha256"] == run["configuration_sha256"]
            and proof["suite_sha256"] == config["suite_sha256"]
            and proof["policy_revision_sha256"] == config["verified_policy_revision_sha256"]
            and proof["method"]
            == packet["method"]
            == "frozen_next_open_three_cost_development_suite"
            and proof["suite_integrity"]
            == packet["suite_integrity"]
            == "verified_roster_and_current_specification",
            "private_integrity_observation_binding_mismatch",
        )
        claim = trace.one(
            "SELECT * FROM workflow_claims WHERE assignment_id=? AND fence=?",
            (assignment["assignment_id"], bound["fence"]),
        )
        require(
            claim["assignment_id"] == assignment["assignment_id"]
            and stage["method_verification_sha256"] in stage["private_tool_refs"]
            and stage["method_verification_sha256"] not in stage["alias_bindings"].values(),
            "proof_claim_or_exclusion_mismatch",
        )
        encoded_packet = canonical_json(packet)
        for private_ref in (
            bound["verification_sha256"],
            bound["configuration_sha256"],
            proof["suite_sha256"],
            proof["policy_revision_sha256"],
            proof["failure_context_sha256"],
            proof["failure_basis_sha256"],
        ):
            require(
                private_ref is None or private_ref not in encoded_packet,
                "private_proof_identity_in_packet",
            )
        require(
            packet["data_values_disclosed"] is False
            and "predicate_holds" not in packet
            and "rationale" not in packet,
            "private_value_or_rationale_in_packet",
        )
        budget_position, _ = trace.event("budget_reserved", request_id=receipt["request_id"])
        require(bound_position < budget_position, "packet_proof_not_bound_before_reservation")
        packet_bindings_checked += 1
        hold = trace.one(
            "SELECT * FROM research_dispatch_holds WHERE request_id=? AND assignment_id=?",
            (receipt["request_id"], assignment["assignment_id"]),
        )
        require(
            hold["transport_kind"] == transport
            and hold["amount"] == receipt["reserved_micro_usd"]
            and hold["packet_sha256"] == hash_json(packet),
            "synthetic_or_mismatched_dispatch_in_actual_trace",
        )
        reservation = trace.one(
            "SELECT * FROM reservations WHERE request_id=?", (receipt["request_id"],)
        )
        allocation = trace.one(
            "SELECT * FROM provider_allocations WHERE request_id=?", (receipt["request_id"],)
        )
        trace.one("SELECT * FROM dispatches WHERE request_id=?", (receipt["request_id"],))
        observation = strict_json(
            trace.one(
                "SELECT observation FROM research_model_observations WHERE request_id=?",
                (receipt["request_id"],),
            )["observation"].encode()
        )
        require(
            observation.get("model") == receipt["observed_model"]
            and observation.get("type") == "message"
            and observation.get("stop_reason") == "end_turn",
            "actual_model_observation_mismatch",
        )
        require(
            reservation["state"] == "settled"
            and reservation["actual_micro_usd"] == receipt["cost_micro_usd"]
            and 0
            <= reservation["actual_micro_usd"]
            <= reservation["reserved_micro_usd"]
            == receipt["reserved_micro_usd"]
            and allocation["day"] == reservation["day"]
            and allocation["purpose"] == "research"
            and allocation["amount"] == receipt["reserved_micro_usd"],
            "actual_dispatch_settlement_mismatch",
        )
        attributed_requests.append(
            {
                "request_id": receipt["request_id"],
                "reserved_micro_usd": reservation["reserved_micro_usd"],
                "actual_micro_usd": reservation["actual_micro_usd"],
                "observed_model": receipt["observed_model"],
            }
        )
        effect = trace.one(
            "SELECT * FROM workflow_effect_outcomes WHERE assignment_id=? AND request_id=?",
            (assignment["assignment_id"], receipt["request_id"]),
        )
        require(
            effect["status"] == "success"
            and stage["projection_sha256"] in strict_json(effect["artifact_refs"].encode()),
            "model_projection_effect_mismatch",
        )
        require(
            any(
                same(store.read_json(ref), receipt)
                for ref in strict_json(effect["artifact_refs"].encode())
            ),
            "model_receipt_effect_mismatch",
        )
        projection = store.read_json(stage["projection_sha256"])
        require(
            projection["role"] == role and "rationale" not in projection,
            "projection_role_or_schema_mismatch",
        )
        projections[role] = projection
        handoff = trace.one(
            "SELECT * FROM workflow_handoffs WHERE assignment_id=?", (assignment["assignment_id"],)
        )
        require(
            handoff["document_sha256"] == stage["handoff_sha256"]
            and hash_json(strict_json(handoff["document"].encode())) == handoff["document_sha256"],
            "handoff_identity_mismatch",
        )
    indexed_bindings = [
        value
        for _, kind, value in trace.events
        if kind == "workflow_broker_packet_bound" and value.get("parent_submission_id") == parent_id
    ]
    require(
        len(indexed_bindings) == packet_bindings_checked == len(stages),
        "unreported_packet_proof_binding",
    )
    require(
        len({item["request_id"] for item in attributed_requests}) == len(stages),
        "model_request_reused",
    )
    placeholders = ",".join("?" for _ in attributed_requests)
    attributed = trace.one(
        "SELECT COUNT(*) AS requests,SUM(actual_micro_usd) AS actual,SUM(reserved_micro_usd) AS reserved FROM reservations WHERE state='settled' AND request_id IN ("
        + placeholders
        + ")",
        tuple(item["request_id"] for item in attributed_requests),
    )
    require(
        attributed["requests"] == len(stages)
        and attributed["actual"] == sum(item["actual_micro_usd"] for item in attributed_requests)
        and attributed["reserved"]
        == sum(item["reserved_micro_usd"] for item in attributed_requests),
        "run_specific_cost_attribution_mismatch",
    )
    accounting = {
        "request_basis": "exact_current_run_stage_request_ids",
        "settled_request_count": attributed["requests"],
        "actual_micro_usd": attributed["actual"],
        "reserved_micro_usd": attributed["reserved"],
        "requests": attributed_requests,
    }
    review_roles = ROLES[3:]
    review_projections = [projections[role] for role in review_roles if role in projections]
    if not review_projections:
        expected_review = "not_reached"
    elif len(review_projections) < len(review_roles):
        expected_review = "incomplete"
    elif any(item["decision"] == "block" for item in review_projections):
        expected_review = "blocked"
    elif all(item["decision"] == "no_blocking_method_issue" for item in review_projections):
        expected_review = "method_no_blockers"
    else:
        expected_review = "inconclusive"
    require(record["review_outcome"] == expected_review, "review_summary_mismatch")
    if len(stages) < 7:
        last = stages[-1]
        require(
            parent["status"] == "invalid"
            and record["all_stages_completed"] is False
            and record["all_models_actual"] is False
            and record["execution_state"] == "not_requested"
            and last["role"] in ROLES[:3]
            and projections[last["role"]]["decision"] == "stop",
            "incomplete_workflow_not_explicit_precalculation_stop",
        )
        if last["role"] == "hypothesis":
            require(
                projections["hypothesis"]["predicate"] is None,
                "stopped_hypothesis_predicate_not_null",
            )
        handoff = store.read_json(last["handoff_sha256"])
        require(
            handoff["state"] == "blocked" and handoff["next_action"] == "stop",
            "stopping_handoff_mismatch",
        )
        for stage in stages[:-1]:
            prior = store.read_json(stage["handoff_sha256"])
            require(
                prior["state"] == "complete" and prior["next_action"] == "proceed",
                "prior_stage_not_complete",
            )
        launch_intents = trace.db.execute(
            "SELECT COUNT(*) FROM workflow_intents i JOIN workflow_assignments a USING(assignment_id) WHERE a.run_id=? AND i.action='launch_development'",
            (run["workflow_run_id"],),
        ).fetchone()[0]
        tool_requests = trace.db.execute(
            "SELECT COUNT(*) FROM research_broker_tool_requests WHERE parent_submission_id=?",
            (parent_id,),
        ).fetchone()[0]
        tool_children = trace.db.execute(
            "SELECT COUNT(*) FROM research_broker_tool_children c JOIN research_broker_tool_requests r USING(assignment_id,request_id) WHERE r.parent_submission_id=?",
            (parent_id,),
        ).fetchone()[0]
        require(
            launch_intents == tool_requests == tool_children == 0,
            "financial_effect_present_after_precalculation_stop",
        )
        start = trace.start(parent_id)
        finish = trace.event("submission_finished", submission_id=parent_id, status="invalid")[0]
        financial_starts = [
            value
            for position, kind, value in trace.events
            if start < position < finish
            and kind == "submission_started"
            and value.get("kind") in {"research_comparison", "study_suite_run", "exploratory_study"}
        ]
        require(not financial_starts, "unexpected_financial_start_during_stopped_trace")
        return {
            "parent_submission_id": parent_id,
            "workflow_run_id": run["workflow_run_id"],
            "parent_artifact_sha256": parent_ref,
            "verification_scope": "stopped_workflow_integrity",
            "workflow_status": "invalid",
            "stages_checked": len(stages),
            "packet_proof_bindings_checked": packet_bindings_checked,
            "attributed_settled_request_count": accounting["settled_request_count"],
            "actual_haiku_observations_checked": 0
            if fixture_only
            else sum(item["observed_model"] == "claude-haiku-5-5" for item in attributed_requests),
            "private_run_accounting": accounting,
            "actual_model_observations_checked": 0 if fixture_only else len(stages),
            "financial_launch_count": 0,
            "fresh_suites_checked": 0,
            "fresh_children_checked": 0,
            "derivative_operands_checked": 0,
            "independent_predicate_agrees": None,
            "numerical_verification": "not_run_no_financial_launch",
            "evidence_kind": evidence,
            "investment_evidence": False,
        }, []
    require(
        parent["status"] == "success"
        and record["all_stages_completed"] is True
        and record["all_models_actual"] is (not fixture_only)
        and record["execution_state"] == "completed",
        "completed_workflow_state_mismatch",
    )
    require(
        projections["hypothesis"]["decision"] == "propose"
        and projections["engineer"]["decision"] == "execute",
        "model_authored_execution_missing",
    )
    predicate = projections["hypothesis"]["predicate"]
    require(
        predicate in PREDICATES
        and all(projections[role]["predicate"] == predicate for role in ROLES[2:]),
        "selected_predicate_mismatch",
    )
    engineer = by_role["engineer"]["assignment_id"]
    binding = trace.one(
        "SELECT r.*,c.child_submission_id FROM research_broker_tool_requests r JOIN research_broker_tool_children c USING(assignment_id,request_id) WHERE r.parent_submission_id=? AND r.assignment_id=?",
        (parent_id, engineer),
    )
    intent = trace.one(
        "SELECT * FROM workflow_intents WHERE assignment_id=? AND request_id=?",
        (engineer, binding["request_id"]),
    )
    require(
        intent["action"] == "launch_development" and intent["fence"] == binding["fence"],
        "comparison_parent_intent_mismatch",
    )
    launch = trace.one(
        "SELECT * FROM workflow_effect_starts WHERE assignment_id=? AND request_id=?",
        (engineer, binding["request_id"]),
    )
    require(launch is not None, "comparison_effect_not_consumed")
    local_request = {
        "suite_sha256": config["suite_sha256"],
        "predicate": predicate,
        "hypothesis_sha256": next(
            s["projection_sha256"] for s in stages if s["role"] == "hypothesis"
        ),
        "engineer_sha256": next(s["projection_sha256"] for s in stages if s["role"] == "engineer"),
    }
    require(
        same(store.read_json(binding["request_sha256"]), local_request),
        "precommitted_tool_request_mismatch",
    )
    comparison_id = binding["child_submission_id"]
    comparison = trace.submission(comparison_id, "research_comparison")
    raw = store.read_bytes(binding["request_sha256"])
    require(
        comparison["request_sha256"] == hash_bytes(raw) and comparison["request_bytes"] == len(raw),
        "comparison_original_request_mismatch",
    )
    registration = store.read_json(comparison["details"]["registration_sha256"])
    derivative = store.read_json(comparison["details"]["comparison_sha256"])
    require(
        registration["submission_id"] == comparison_id
        and same(registration["request"], local_request)
        and derivative["submission_id"] == comparison_id
        and derivative["registration_sha256"] == comparison["details"]["registration_sha256"]
        and derivative["predicate"] == predicate
        and derivative["investment_evidence"] is False
        and derivative["classification"] == "development_only",
        "comparison_artifact_binding_mismatch",
    )
    require(
        registration["code_identity"]["module_sha256"]
        == codes["sources"]["research_comparison.py"],
        "comparison_source_identity_changed",
    )
    require(
        registration["request_sha256"] == binding["request_sha256"],
        "comparison_registration_request_mismatch",
    )
    computed_fingerprint = hash_json(
        {
            key: registration[key]
            for key in (
                "request",
                "suite_manifest",
                "code_identity",
                "predicate_semantics",
                "numerical_policy",
            )
        }
    )
    require(
        computed_fingerprint == derivative["fingerprint"] == comparison["details"]["fingerprint"],
        "comparison_fingerprint_mismatch",
    )
    bound_position, _ = trace.event(
        "workflow_broker_tool_child_bound",
        parent_submission_id=parent_id,
        assignment_id=engineer,
        request_id=binding["request_id"],
        child_submission_id=comparison_id,
    )
    registered_position, _ = trace.event(
        "research_comparison_registered", submission_id=comparison_id
    )
    effect_position, _ = trace.event(
        "workflow_effect_started",
        assignment_id=engineer,
        request_id=binding["request_id"],
        fence=binding["fence"],
    )
    require(
        trace.start(parent_id)
        < effect_position
        < trace.start(comparison_id)
        < bound_position
        < registered_position,
        "comparison_parent_event_order",
    )
    suite_id = comparison["details"]["suite_run_id"]
    require(suite_id == derivative["suite_run_id"], "derivative_suite_binding_mismatch")
    link = trace.one(
        "SELECT * FROM research_comparison_invocations WHERE submission_id=?", (comparison_id,)
    )
    require(link["suite_run_id"] == suite_id, "comparison_invocation_registry_mismatch")
    suite_run = trace.submission(suite_id, "study_suite_run")
    require(
        suite_run["details"]["suite_sha256"] == config["suite_sha256"]
        and suite_run["details"]["all_success"] is True
        and suite_run["details"]["complete"] is True,
        "fresh_suite_not_complete",
    )
    require(
        registered_position
        < trace.start(suite_id)
        < trace.finish(suite_id)
        < trace.finish(comparison_id)
        < trace.finish(parent_id),
        "fresh_suite_event_order",
    )
    manifest = store.read_json(config["suite_sha256"])
    require(same(manifest, registration["suite_manifest"]), "comparison_suite_manifest_mismatch")
    original_registration = trace.submission(manifest["submission_id"], "study_suite_registration")
    require(
        original_registration["details"]["suite_sha256"] == config["suite_sha256"]
        and trace.finish(manifest["submission_id"]) < trace.start(parent_id),
        "suite_not_prefrozen",
    )
    suite_row = trace.one("SELECT * FROM study_suite_runs WHERE submission_id=?", (suite_id,))
    roster = store.read_json(suite_row["roster_sha256"])
    raw = store.read_bytes(roster["run_request_sha256"])
    require(
        suite_run["request_sha256"] == hash_bytes(raw)
        and suite_run["request_bytes"] == len(raw)
        and strict_json(raw) == {"suite_sha256": config["suite_sha256"]},
        "suite_original_request_mismatch",
    )
    members = [
        {
            **item,
            "request": {**item["request"], "suite_sha256": config["suite_sha256"]},
            "request_sha256": hash_json(
                {**item["request"], "suite_sha256": config["suite_sha256"]}
            ),
        }
        for item in manifest["members"]
    ]
    require(
        same(
            roster,
            {
                "schema_version": 1,
                "kind": "study_suite_run_roster",
                "submission_id": suite_id,
                "suite_sha256": config["suite_sha256"],
                "run_request_sha256": roster["run_request_sha256"],
                "members": members,
            },
        ),
        "fresh_suite_roster_mismatch",
    )
    summary = store.read_json(suite_run["details"]["summary_sha256"])
    require(
        summary["submission_id"] == suite_id
        and summary["suite_sha256"] == config["suite_sha256"]
        and summary["roster_sha256"] == suite_row["roster_sha256"]
        and summary["all_success"] is True
        and summary["complete"] is True
        and [item["cost_bps"] for item in summary["members"]] == list(COSTS),
        "fresh_suite_summary_mismatch",
    )
    children, operands, seen = [], [], set()
    for item, expected_member in zip(summary["members"], members):
        require(
            same({key: item[key] for key in expected_member}, expected_member),
            "summary_member_request_mismatch",
        )
        child_id, request, cost = (
            item["outcome"]["submission_id"],
            item["request"],
            item["cost_bps"],
        )
        require(child_id not in seen, "fresh_child_reused")
        seen.add(child_id)
        child = trace.submission(child_id, "exploratory_study")
        details = child["details"]
        require(
            same(
                item["outcome"],
                {
                    "submission_id": child_id,
                    "status": "success",
                    **{
                        key: details[key]
                        for key in ("error_code", "attempt_id", "fingerprint", "artifact_sha256")
                        if key in details
                    },
                },
            ),
            "summary_child_outcome_mismatch",
        )
        require(
            child["request_sha256"] == item["request_sha256"] == hash_json(request)
            and child["request_bytes"] == len(canonical_json(request).encode())
            and details["suite_run_id"] == suite_id
            and details["suite_sha256"] == config["suite_sha256"]
            and details["admission_sha256"] == request["admission_sha256"]
            and details["dataset_sha256"] == request["dataset_sha256"],
            "fresh_child_receipt_mismatch",
        )
        bound = trace.one(
            "SELECT * FROM study_suite_results WHERE run_id=? AND cost_bps=?", (suite_id, cost)
        )
        require(bound["child_submission_id"] == child_id, "fresh_child_registry_mismatch")
        launch_position, _ = trace.event(
            "study_suite_member_launched",
            run_id=suite_id,
            cost_bps=cost,
            request_sha256=item["request_sha256"],
        )
        child_bound_position, _ = trace.event(
            "study_suite_member_bound", run_id=suite_id, cost_bps=cost, child_submission_id=child_id
        )
        require(
            trace.start(suite_id)
            < launch_position
            < trace.start(child_id)
            < child_bound_position
            < trace.finish(child_id)
            < trace.finish(suite_id),
            "fresh_child_event_order",
        )
        execution = trace.one(
            "SELECT * FROM explorer_executions WHERE submission_id=?", (child_id,)
        )
        require(
            execution["attempt_id"] == details["attempt_id"]
            and execution["fingerprint"] == details["fingerprint"],
            "fresh_attempt_registry_mismatch",
        )
        attempt = trace.one("SELECT * FROM outcomes WHERE attempt_id=?", (details["attempt_id"],))
        require(attempt["status"] == "success", "fresh_attempt_not_successful")
        attempt_position, _ = trace.event(
            "attempt_started", attempt_id=details["attempt_id"], fingerprint=details["fingerprint"]
        )
        require(
            child_bound_position < attempt_position < trace.finish(child_id),
            "fresh_attempt_event_order",
        )
        result = store.read_json(details["artifact_sha256"])
        require(
            result["result_kind"] == "exploratory_result"
            and result["evidence_kind"] == "historical_market_data"
            and result["investment_evidence"] is False
            and result["dataset_sha256"] == request["dataset_sha256"]
            and result["admission_sha256"] == request["admission_sha256"]
            and same(result["code_identity"], registration["code_identity"]["engine_identity"]),
            "fresh_result_identity_mismatch",
        )
        require(
            same(result["code_identity"], codes["financial_identity"]),
            "current_financial_identity_mismatch",
        )
        admitted = store.read_json(request["admission_sha256"])
        require(
            same(result["admission_evidence"], admitted), "retained_admission_evidence_mismatch"
        )
        report = _validate_financial_report(
            request,
            result,
            admitted,
            registration["code_identity"]["engine_identity"]["event_policy"],
        )
        operands.append(
            {
                "cost_bps": cost,
                "strategy_ending_equity": report["strategy"]["ending_equity"],
                "strategy_total_fees": report["strategy"]["total_fees"],
                "benchmark_ending_equity": report["benchmark"]["ending_equity"],
            }
        )
        children.append(
            {"submission_id": child_id, "request": request, "details": details, "result": result}
        )
    require(len({item["details"]["attempt_id"] for item in children}) == 3, "fresh_attempt_reused")
    require(
        same(derivative["operands"], operands), "derivative_operands_disagree_with_fresh_children"
    )
    require(
        same(
            derivative["child_sources"],
            [
                {
                    "cost_bps": item["request"]["specification"]["cost_bps"],
                    "submission_id": item["submission_id"],
                    "request_sha256": hash_json(item["request"]),
                    "details": item["details"],
                }
                for item in children
            ],
        ),
        "derivative_child_sources_mismatch",
    )
    predicate_holds = independent_predicate(predicate, operands)
    require(
        type(derivative["predicate_holds"]) is bool
        and derivative["predicate_holds"] is predicate_holds,
        "independent_predicate_disagrees",
    )
    return {
        "parent_submission_id": parent_id,
        "workflow_run_id": run["workflow_run_id"],
        "comparison_submission_id": comparison_id,
        "suite_submission_id": suite_id,
        "parent_artifact_sha256": parent_ref,
        "comparison_artifact_sha256": comparison["details"]["comparison_sha256"],
        "verification_scope": "independent_numerical_integrity",
        "workflow_status": "success",
        "actual_model_observations_checked": 0 if fixture_only else 7,
        "financial_launch_count": 1,
        "packet_proof_bindings_checked": packet_bindings_checked,
        "attributed_settled_request_count": accounting["settled_request_count"],
        "actual_haiku_observations_checked": 0
        if fixture_only
        else sum(item["observed_model"] == "claude-haiku-5-5" for item in attributed_requests),
        "private_run_accounting": accounting,
        "numerical_verification": "passed",
        "stages_checked": 7,
        "fresh_suites_checked": 1,
        "fresh_children_checked": 3,
        "derivative_operands_checked": 9,
        "independent_predicate_agrees": True,
        "evidence_kind": evidence,
        "investment_evidence": False,
    }, children

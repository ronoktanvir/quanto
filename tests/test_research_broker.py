"""Actual broker composition with invented source and synthetic model transport."""
from copy import deepcopy
import json

import pytest

from quanto import admission, research_broker, study_suite
from quanto.ledger import Journal
from quanto.provenance import Provenance
from quanto.provider import HAIKU
from quanto.research_broker import run_workflow
from quanto.research_workflow import ROLES
from test_admission import regular_way_fixture, study


@pytest.fixture
def configuration(tmp_path):
    request, _ = regular_way_fixture(tmp_path)
    admitted = admission.admit_dataset(tmp_path, request)
    assert admitted["status"] == "success"
    member = study(request, admitted["admission_sha256"])
    suite = study_suite.register_suite(tmp_path, {"members": [
        {**member, "specification": {**member["specification"], "cost_bps": cost}}
        for cost in (0, 10, 25)]})
    assert suite["status"] == "success"
    with Provenance(tmp_path) as store:
        failure = store.begin("synthetic_failed_idea", {"fixture": True})
        store.finish(failure, "invalid", {"error_code": "unsupported_due_bill",
                                          "private": "PRIVATE-MARKET-DETAIL-123.45"})
    return {"run_key": "broker-fixture", "suite_sha256": suite["suite_sha256"],
            "models": {role: HAIKU for role in ROLES}, "evidence_kind": "synthetic_fixture",
            "failure_ids": [{"source": "submission", "id": failure}]}


class ModelFixture:
    def __init__(self, predicate="cost_fees_nondecreasing", stop=None, block=None, malformed=None):
        self.predicate, self.stop, self.block, self.malformed = predicate, stop, block, malformed
        self.contexts = []

    def __call__(self, body, key):
        assert key == "synthetic-fixture-key"
        request = json.loads(body)
        context = json.loads(request["messages"][0]["content"])
        self.contexts.append(context)
        role = context["role"]
        decision = {"director": "proceed", "hypothesis": "propose", "engineer": "execute"}.get(
            role, "no_blocking_method_issue")
        if self.stop == role:
            decision = "stop"
        if self.block == role:
            decision = "block"
        output = {"schema_version": 1, "role": role, "decision": decision,
                  "predicate": None if role == "director" else self.predicate,
                  "artifact_aliases": context["artifact_aliases"],
                  "findings": [{"code": "hidden_values_unreviewed",
                                "artifact_aliases": context["artifact_aliases"]}],
                  "rationale": "PRIVATE-RATIONALE-987.65; synthetic model fixture only."}
        text = json.dumps(output) if self.malformed != role else '{"truncated":'
        return {"type": "message", "model": request["model"], "id": "fixture-response-" + role,
                "stop_reason": "end_turn", "usage": {"input_tokens": 100, "output_tokens": 150},
                "content": [{"type": "text", "text": text}]}


def test_complete_real_composition_fresh_suite_and_no_private_context(tmp_path, configuration):
    model = ModelFixture()
    result = run_workflow(tmp_path, configuration, transport=model)
    assert result["status"] == "success", result
    assert result["all_stages_completed"] and not result["all_models_actual"]
    assert result["review_outcome"] == "method_no_blockers"
    assert result["operational_acceptance"] is result["investment_validation"] is False
    assert result["dispatch_counts"] == {"authorized": 7, "response_observed": 7}
    assert [c["role"] for c in model.contexts] == list(ROLES)
    assert model.contexts[1]["failures"][0]["code"] == "unsupported_due_bill"
    assert all(c["execution_state"] == "completed" for c in model.contexts[3:])
    encoded = json.dumps(model.contexts)
    for forbidden in (configuration["suite_sha256"], configuration["failure_ids"][0]["id"],
                      "PRIVATE-MARKET", "PRIVATE-RATIONALE", "predicate_holds", "ending_equity\":"):
        assert forbidden not in encoded
    with Provenance(tmp_path) as store:
        comparisons = store.list_submissions(kind="research_comparison", status="success")
        assert len(comparisons) == 1
        assert len(store.list_submissions(kind="study_suite_run", status="success")) == 1
        assert len(store.list_submissions(kind="exploratory_study", status="success")) == 3
        binding = store.journal.connection.execute(
            "SELECT r.*,c.child_submission_id FROM research_broker_tool_requests r "
            "JOIN research_broker_tool_children c USING(assignment_id,request_id)").fetchone()
        assert binding["parent_submission_id"] == result["submission_id"]
        assert binding["child_submission_id"] == comparisons[0]["submission_id"]
        source = store.read_json(comparisons[0]["details"]["registration_sha256"])
        assert source["request"]["predicate"] == model.predicate
        assert store.list_submissions(kind="failure_memory_query", status="success")
        assert store.journal.verify_events()["count"] > 100
        # Alias meanings remain stable as later roles receive more artifacts.
        aliases = {}
        for stage in result["stages"]:
            observation = store.read_json(stage["method_verification_sha256"])
            assert observation["suite_sha256"] == configuration["suite_sha256"]
            assert observation["configuration_sha256"] == result["configuration_sha256"]
            assert observation["role"] == stage["role"]
            assert stage["method_verification_sha256"] in stage["private_tool_refs"]
            assert stage["method_verification_sha256"] not in stage["alias_bindings"].values()
            for alias, digest in stage["alias_bindings"].items():
                assert alias not in aliases or aliases[alias] == digest
                aliases[alias] = digest
        private = store.journal.connection.execute("SELECT artifact_sha256 FROM research_private_responses").fetchall()
        assert len(private) == 7
        assert all("PRIVATE-RATIONALE" in store.read_json(row[0])["reply"] for row in private)


def test_suite_lost_after_first_response_refuses_next_integrity_claim(tmp_path, configuration):
    model = ModelFixture()

    def lose_suite(body, key):
        response = model(body, key)
        with Provenance(tmp_path) as store:
            store.tombstone(configuration["suite_sha256"], "operator_requested")
        return response

    result = run_workflow(tmp_path, configuration, transport=lose_suite)
    assert result["status"] == "invalid"
    assert len(model.contexts) == 1
    assert result["dispatch_counts"] == {"authorized": 1, "response_observed": 1}
    with Provenance(tmp_path) as store:
        assert store.list_submissions(kind="research_comparison") == []
        assert store.list_submissions(kind="study_suite_run") == []
        assert len(result["stages"]) == 1


def test_failed_response_keeps_exact_predispatch_integrity_binding(tmp_path, configuration):
    result = run_workflow(tmp_path, configuration,
                          transport=ModelFixture(malformed="director"))
    assert result["status"] == "invalid" and result["stages"] == []
    with Provenance(tmp_path) as store:
        db = store.journal.connection
        row = db.execute("SELECT * FROM events WHERE kind='workflow_broker_packet_bound'").fetchone()
        binding = json.loads(row["payload"])
        assert binding["parent_submission_id"] == result["submission_id"]
        packet = store.read_json(binding["packet_sha256"])
        proof = store.read_json(binding["verification_sha256"])
        assert proof["role"] == packet["role"] == "director"
        assert proof["configuration_sha256"] == binding["configuration_sha256"]
        assert proof["suite_sha256"] == configuration["suite_sha256"]
        receipt = db.execute("SELECT * FROM research_dispatch_holds WHERE request_id=?",
                             (binding["request_id"],)).fetchone()
        assert receipt["assignment_id"] == binding["assignment_id"]
        start = db.execute("SELECT id FROM events WHERE kind='budget_reserved' "
                           "AND json_extract(payload,'$.request_id')=?",
                           (binding["request_id"],)).fetchone()[0]
        assert row["id"] < start
        assert store.journal.verify_events()["count"] > 0


def test_material_model_choice_changes_registered_derivative(tmp_path, configuration):
    first = run_workflow(tmp_path, configuration, transport=ModelFixture("cost_fees_nondecreasing"))
    second = run_workflow(tmp_path, {**configuration, "run_key": "another-choice"},
                          transport=ModelFixture("strategy_equals_benchmark_terminal"))
    assert first["status"] == second["status"] == "success"
    with Provenance(tmp_path) as store:
        records = store.list_submissions(kind="research_comparison", status="success")
        assert len(records) == 2 and len({r["details"]["fingerprint"] for r in records}) == 2
        assert len(store.list_submissions(kind="study_suite_run")) == 2


def test_critic_block_is_retained_without_stopping_remaining_reviews_or_claiming_acceptance(tmp_path, configuration):
    result = run_workflow(tmp_path, configuration, transport=ModelFixture(block="data_critic"))
    assert result["status"] == "success" and result["review_outcome"] == "blocked"
    assert result["all_stages_completed"] and result["operational_acceptance"] is False


@pytest.mark.parametrize("role,count", [("director", 1), ("hypothesis", 2), ("engineer", 3)])
def test_stop_does_not_execute_study_or_claim_reviews(tmp_path, configuration, role, count):
    model = ModelFixture(stop=role)
    result = run_workflow(tmp_path, configuration, transport=model)
    assert result["status"] == "invalid" and len(model.contexts) == count
    assert result["review_outcome"] == "not_reached"
    with Provenance(tmp_path) as store:
        assert not store.list_submissions(kind="study_suite_run")
        assert store.journal.connection.execute(
            "SELECT state FROM workflow_terminals ORDER BY rowid DESC LIMIT 1").fetchone()[0] == "blocked"


def test_partial_review_keeps_objections_without_claiming_complete_review(tmp_path, configuration):
    result = run_workflow(tmp_path, configuration,
                          transport=ModelFixture(block="data_critic", malformed="scope"))
    assert result["status"] == "invalid" and result["review_outcome"] == "incomplete"
    with Provenance(tmp_path) as store:
        stage = next(s for s in result["stages"] if s["role"] == "data_critic")
        assert store.read_json(stage["projection_sha256"])["decision"] == "block"


def test_unpublished_last_review_cannot_report_all_clear(tmp_path, configuration, monkeypatch):
    from quanto.research_workflow import ResearchWorkflow, WorkflowError
    original = ResearchWorkflow.finish_handoff

    def fail_scope(self, token, worker, fence, handoff):
        assignment = self._leased(token, worker, fence, self.journal._now())
        if assignment["role"] == "scope":
            raise WorkflowError("synthetic publication refusal")
        return original(self, token, worker, fence, handoff)

    monkeypatch.setattr(ResearchWorkflow, "finish_handoff", fail_scope)
    result = run_workflow(tmp_path, configuration, transport=ModelFixture())
    assert result["status"] == "invalid" and result["review_outcome"] == "incomplete"
    assert len(result["stages"]) == 6


def test_malformed_model_is_retained_uncertain_without_paid_retry(tmp_path, configuration):
    model = ModelFixture(malformed="hypothesis")
    result = run_workflow(tmp_path, configuration, transport=model)
    assert result["status"] == "invalid" and len(model.contexts) == 2
    assert result["review_outcome"] == "not_reached"
    assert result["dispatch_counts"] == {"authorized": 2, "response_observed": 2}
    with Provenance(tmp_path) as store:
        assert store.journal.budget_snapshot()["uncertain_count"] == 1
        assert not store.list_submissions(kind="study_suite_run")
    repeat = run_workflow(tmp_path, configuration, transport=lambda *_: pytest.fail("No repeat"))
    assert repeat["error_code"] == "broker_run_key_already_used"


def test_budget_refusal_before_role_or_model_effect(tmp_path, configuration):
    with Journal(tmp_path / "runtime/research.sqlite") as journal:
        journal.reserve("existing-uncertain", 19_999_000)
        journal.mark_uncertain("existing-uncertain", "synthetic unrelated call")
    result = run_workflow(tmp_path, configuration, transport=lambda *_: pytest.fail("No model call"))
    assert result["status"] == "invalid" and result["error_code"] == "broker_budget_unavailable"
    with Provenance(tmp_path) as store:
        assert not store.list_submissions(kind="study_suite_run")
        assert store.journal.budget_snapshot()["committed_micro_usd"] == 19_999_000


@pytest.mark.parametrize("change", [{"shell": "not executable"}, {"evidence_kind": "historical_market_data"},
                                  {"models": {}}, {"failure_ids": [{"source": "submission", "id": "bad"}]}])
def test_invalid_request_stays_recorded_without_dispatch(tmp_path, configuration, change):
    result = run_workflow(tmp_path, {**configuration, **change}, transport=lambda *_: pytest.fail("No call"))
    assert result["status"] == "invalid"
    with Provenance(tmp_path) as store:
        assert store.get_submission(result["submission_id"])["status"] == "invalid"


def test_ungranted_failures_and_raw_notes_never_enter_context(tmp_path, configuration):
    with Provenance(tmp_path) as store:
        ungranted = store.begin("ungranted_failure", {"private": True})
        store.finish(ungranted, "invalid", {"error_code": "identity_change_unresolved"})
    model = ModelFixture()
    result = run_workflow(tmp_path, deepcopy(configuration), transport=model)
    assert result["status"] == "success"
    assert "identity_change_unresolved" not in json.dumps(model.contexts)


def test_wrong_failure_id_refuses_before_hypothesis_send(tmp_path, configuration):
    configuration["failure_ids"] = [{"source": "submission", "id": "0" * 32}]
    model = ModelFixture()
    result = run_workflow(tmp_path, configuration, transport=model)
    assert result["status"] == "invalid" and len(model.contexts) == 1
    assert result["error_code"] == "broker_failure_missing_or_not_unsuccessful"


def test_child_is_bound_before_execution_and_binding_survives_interruption(tmp_path, configuration, monkeypatch):
    original = research_broker.run_comparison
    def interrupted(root, request, *, on_registered):
        def register(child):
            on_registered(child)
            with Provenance(root) as store:
                row = store.journal.connection.execute(
                    "SELECT * FROM research_broker_tool_children WHERE child_submission_id=?", (child,)).fetchone()
                assert row is not None
                assert not store.list_submissions(kind="study_suite_run")
            raise KeyboardInterrupt("synthetic stop after durable binding")
        return original(root, request, on_registered=register)
    monkeypatch.setattr(research_broker, "run_comparison", interrupted)
    with pytest.raises(KeyboardInterrupt):
        run_workflow(tmp_path, configuration, transport=ModelFixture())
    with Provenance(tmp_path) as store:
        child = store.journal.connection.execute("SELECT * FROM research_broker_tool_children").fetchone()
        request = store.journal.connection.execute("SELECT * FROM research_broker_tool_requests").fetchone()
        assert store.get_submission(child["child_submission_id"])["status"] == "pending"
        assert store.get_submission(request["parent_submission_id"])["status"] == "pending"
        assert not store.list_submissions(kind="study_suite_run")
        assert store.journal.verify_events()["count"] > 0


def test_child_callback_refusal_aborts_financial_work(tmp_path, configuration, monkeypatch):
    def refuse(*args):
        raise ValueError("synthetic binding refusal")
    monkeypatch.setattr(research_broker, "_bind_comparison_child", refuse)
    result = run_workflow(tmp_path, configuration, transport=ModelFixture())
    assert result["status"] == "invalid"
    with Provenance(tmp_path) as store:
        children = store.list_submissions(kind="research_comparison")
        assert len(children) == 1 and children[0]["status"] == "invalid"
        assert not store.list_submissions(kind="study_suite_run")
        assert store.journal.connection.execute("SELECT COUNT(*) FROM research_broker_tool_requests").fetchone()[0] == 1


def test_child_cannot_be_bound_twice(tmp_path, configuration, monkeypatch):
    original = research_broker._bind_comparison_child
    def twice(*args):
        original(*args)
        original(*args)
    monkeypatch.setattr(research_broker, "_bind_comparison_child", twice)
    result = run_workflow(tmp_path, configuration, transport=ModelFixture())
    assert result["status"] == "invalid"
    with Provenance(tmp_path) as store:
        assert store.journal.connection.execute("SELECT COUNT(*) FROM research_broker_tool_children").fetchone()[0] == 1
        assert not store.list_submissions(kind="study_suite_run")


def test_cli_invalid_envelope_is_retained_without_network_or_private_output(tmp_path, capsys):
    from quanto.cli import main
    path = tmp_path / "request.json"
    path.write_text('{"shell":"PRIVATE-DO-NOT-ECHO"}')
    assert main(["--root", str(tmp_path), "run-research", "--request", str(path)]) == 1
    captured = capsys.readouterr()
    assert "PRIVATE-DO-NOT-ECHO" not in captured.out + captured.err
    assert json.loads(captured.out)["status"] == "invalid"
    with Provenance(tmp_path) as store:
        assert len(store.list_submissions(kind="research_broker_run", status="invalid")) == 1
        assert store.journal.budget_snapshot()["committed_micro_usd"] == 0

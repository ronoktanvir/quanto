"""Synthetic integration-boundary checks with controlled admission/revision stubs.

All prices and source artifacts here are invented fixtures. Historical routing
is exercised only to test explorer gates; these stubs do not validate actual
admission, source semantics, investment performance, or independent review.
"""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from quanto import admission, explorer, policy_revision, study_suite
from quanto.ledger import hash_bytes
from quanto.provenance import Provenance
from quanto.research import StrategySpec


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    days = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08",
            "2024-01-09", "2024-01-10", "2024-01-11", "2024-01-12", "2024-01-16"]
    prices = [10, 12, 14, 9, 11, 15, 16, 13, 12, 17]
    market = {"instrument_id": "fixture:invented-integration-boundary", "venue": "invented-fixture",
              "currency": "USD", "session_timezone": "America/New_York"}
    rows = [{"timestamp": datetime.fromisoformat(day).replace(
        tzinfo=ZoneInfo(market["session_timezone"])).isoformat(), "symbol": "INVENTED",
        "open": value, "high": value + 1, "low": value - 1, "close": value, "volume": 1000}
        for day, value in zip(days, prices)]
    with Provenance(tmp_path) as store:
        source = store.put_json(rows)
    registered = explorer.register_dataset(tmp_path, {
        "data_sha256": source, "evidence_kind": "historical_market_data", "market": market,
        "price_basis": "raw", "expected_sessions": days,
    })
    assert registered["status"] == "success", registered
    dataset = registered["manifest_sha256"]
    spec = asdict(StrategySpec(lookback=2))
    spec.pop("cost_bps")
    with Provenance(tmp_path) as store:
        annotation = store.put_json({"fixture": "invented controlling economic terms"})
        semantic = store.put_json({"fixture": "invented semantic review identity"})
        schedule = store.put_json({"fixture": "invented independent schedule identity"})
        decision = store.put_json({"fixture": "invented accepted policy identity"})
        refusal = store.put_json({"fixture": "invented prior refusal identity"})
        revision = {"kind": "policy_revision", "dataset_sha256": dataset,
                    "frozen_study": {**spec, "evaluation_start": days[3], "evaluation_end": days[-1]},
                    "lineage": {"post_acquisition_change_count": 2,
                                "prior_refusals": [{"request_sha256": refusal}]},
                    "facts_delta": [{"path": "$.events[0].regular_way_split", "operation": "add"}],
                    "artifact_refs": [annotation, semantic, schedule, decision, refusal]}
        revision_digest = store.put_json(revision)
        admitted = {"kind": "historical_admission", "dataset_sha256": dataset,
                    "scope": "controlled_synthetic_integration_stub", "actions": [],
                    "policy_revision_sha256": revision_digest, "policy_revision": revision,
                    "limitations": ["invented_fixture_no_financial_admission_claim"],
                    "accepted_action_treatments": [{"profile": "domestic_integer_forward_split_v1",
                                                   "annotation_sha256": annotation,
                                                   "semantic_review_sha256": semantic}],
                    "excluded_actions": [{"fixture": "original exclusions preserved"}],
                    "independent_schedule_sha256": schedule,
                    "unresolved_discrepancies": [{"classification": "unresolved_ancillary_date_discrepancy"}],
                    "artifact_refs": sorted({source, dataset, revision_digest, annotation, semantic,
                                             schedule, decision, refusal})}
        admission_digest = store.put_json(admitted)
        submission = store.begin("historical_admission", {"fixture": "controlled stub"})
        store.finish(submission, "success", {"admission_sha256": admission_digest,
                                             "artifact_refs": [admission_digest]})

    def validate_admission(store, digest, dataset_digest):
        if digest != admission_digest or dataset_digest != dataset:
            raise admission.AdmissionError("fixture_admission_identity_mismatch")
        for ref in (admission_digest, *admitted["artifact_refs"]):
            store.read_bytes(ref)
        return deepcopy(admitted)

    def validate_revision(store, digest, admission_request=None, *, before_submission_id=None):
        if digest != revision_digest:
            raise policy_revision.PolicyRevisionError("fixture_revision_identity_mismatch")
        for ref in (revision_digest, *revision["artifact_refs"]):
            store.read_bytes(ref)
        return deepcopy(revision)

    monkeypatch.setattr(admission, "validate_admission", validate_admission)
    monkeypatch.setattr(policy_revision, "validate_revision", validate_revision)
    requests = [{"dataset_sha256": dataset, "admission_sha256": admission_digest,
                 "study_name": "invented integration boundary", "evaluation_start": days[3],
                 "evaluation_end": days[-1], "specification": {**spec, "cost_bps": cost}}
                for cost in (0, 10, 25)]
    suite = study_suite.register_suite(tmp_path, {"members": requests})
    assert suite["status"] == "success", suite
    return {"requests": [{**request, "suite_sha256": suite["suite_sha256"]} for request in requests],
            "suite_sha256": suite["suite_sha256"], "admission": admitted,
            "dependency": annotation, "revision": revision_digest}


def artifact(root, digest):
    with Provenance(root) as store:
        return store.read_json(digest)


def run_member(root, boundary, cost=0):
    run = study_suite.run_suite(root, {"suite_sha256": boundary["suite_sha256"]})
    member = next(item for item in run["summary"]["members"] if item["cost_bps"] == cost)
    with Provenance(root) as store:
        child = store.get_submission(member["outcome"]["submission_id"])
    return {"submission_id": child["submission_id"], "status": child["status"], **(child["details"] or {})}


def no_attempts(root):
    with Provenance(root) as store:
        assert store.journal.connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0


def test_missing_suite_refuses_before_calculation(tmp_path, boundary, monkeypatch):
    request = deepcopy(boundary["requests"][0])
    request.pop("suite_sha256")
    monkeypatch.setattr(explorer, "run_event_backtest", lambda *a, **k: pytest.fail("must not calculate"))
    result = explorer.run_submission(tmp_path, request)
    assert result["status"] == "invalid" and result["error_code"] == "registered_study_suite_required"
    no_attempts(tmp_path)


@pytest.mark.parametrize("change", ["unknown_suite", "wrong_member_name", "different_cost_bytes"])
def test_incorrect_exact_membership_refuses_before_calculation(tmp_path, boundary, monkeypatch, change):
    request = deepcopy(boundary["requests"][1])
    if change == "unknown_suite":
        request["suite_sha256"] = "f" * 64
        code = "artifact_or_storage_unavailable"
    elif change == "wrong_member_name":
        request["study_name"] = "unregistered renamed member"
        code = "study_not_in_suite"
    else:
        request["specification"]["cost_bps"] = 10.0
        code = "study_not_in_suite"
    monkeypatch.setattr(explorer, "run_event_backtest", lambda *a, **k: pytest.fail("must not calculate"))
    result = explorer.run_submission(tmp_path, request)
    assert result["status"] == "invalid" and result["error_code"] == code
    no_attempts(tmp_path)


@pytest.mark.parametrize("change", ["lookback", "evaluation_start", "starting_cash"])
def test_frozen_study_is_enforced_before_calculation(tmp_path, boundary, monkeypatch, change):
    request = deepcopy(boundary["requests"][1])
    if change == "evaluation_start":
        request[change] = "2024-01-08"
    else:
        request["specification"][change] += 1
    monkeypatch.setattr(explorer, "run_event_backtest", lambda *a, **k: pytest.fail("must not calculate"))
    result = explorer.run_submission(tmp_path, request)
    assert result["status"] == "invalid" and result["error_code"] == "study_outside_frozen_revision"
    no_attempts(tmp_path)


def test_pre_execution_dependency_change_refuses_without_attempt(tmp_path, boundary, monkeypatch):
    with Provenance(tmp_path) as store:
        store.tombstone(boundary["dependency"], "invalid_artifact")
    monkeypatch.setattr(explorer, "run_event_backtest", lambda *a, **k: pytest.fail("must not calculate"))
    result = explorer.run_submission(tmp_path, boundary["requests"][0])
    assert result["status"] == "invalid" and result["error_code"] == "artifact_or_storage_unavailable"
    no_attempts(tmp_path)


def test_post_execution_dependency_change_refuses_and_retains_attempt(tmp_path, boundary, monkeypatch):
    real_engine = explorer.run_event_backtest
    dependency = boundary["dependency"]
    root_path = str(tmp_path)

    def mutate_after_calculation(*args, **kwargs):
        result = real_engine(*args, **kwargs)
        with Provenance(root_path) as store:
            store.tombstone(dependency, "invalid_artifact")
        return result

    monkeypatch.setattr(explorer, "run_event_backtest", mutate_after_calculation)
    result = run_member(tmp_path, boundary)
    assert result["status"] == "invalid" and result["error_code"] == "artifact_or_storage_unavailable"
    assert "attempt_id" in result and "artifact_sha256" not in result
    with Provenance(tmp_path) as store:
        assert store.journal.connection.execute("SELECT status FROM outcomes").fetchone()[0] == "invalid"


def test_post_execution_suite_membership_is_rechecked(tmp_path, boundary, monkeypatch):
    original = study_suite.validate_membership

    def membership(store, digest, request, *, before_submission_id=None):
        result = original(store, digest, request, before_submission_id=before_submission_id)
        # A real attempt appears between the explorer's pre/post checks. This
        # condition is read from durable state, avoiding mutable stub counters.
        if store.journal.connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]:
            return {**result, "fixture_changed_dependency": True}
        return result

    monkeypatch.setattr(study_suite, "validate_membership", membership)
    result = run_member(tmp_path, boundary)
    assert result["status"] == "invalid" and result["error_code"] == "suite_dependencies_changed"
    assert "attempt_id" in result and "artifact_sha256" not in result


def test_result_embeds_complete_private_evidence_and_three_member_roster(tmp_path, boundary):
    result = run_member(tmp_path, boundary, cost=10)
    assert result["status"] == "success", result
    report = artifact(tmp_path, result["artifact_sha256"])
    assert report["admission_evidence"] == boundary["admission"]
    assert report["admission_evidence"]["excluded_actions"]
    assert report["admission_evidence"]["unresolved_discrepancies"]
    assert report["admission_evidence"]["policy_revision"]["lineage"]["post_acquisition_change_count"] == 2
    assert report["admission_evidence"]["accepted_action_treatments"][0]["semantic_review_sha256"]
    assert report["study_suite"]["suite_sha256"] == boundary["suite_sha256"]
    assert [member["cost_bps"] for member in report["study_suite"]["members"]] == [0, 10, 25]
    assert report["study_suite"]["member"]["cost_bps"] == 10
    assert {boundary["suite_sha256"], boundary["revision"], boundary["dependency"]} <= set(result["artifact_refs"])
    assert report["investment_evidence"] is False


def test_exact_three_scenario_replay_preserves_artifact_bytes_and_distinct_attempts(tmp_path, boundary):
    first = study_suite.run_suite(tmp_path, {"suite_sha256": boundary["suite_sha256"]})
    second = study_suite.run_suite(tmp_path, {"suite_sha256": boundary["suite_sha256"]})
    assert first["status"] == second["status"] == "success", (first, second)
    initial = [member["outcome"] for member in first["summary"]["members"]]
    replay = [member["outcome"] for member in second["summary"]["members"]]
    assert len({row["fingerprint"] for row in initial}) == 3
    for before, after in zip(initial, replay):
        assert before["attempt_id"] != after["attempt_id"]
        assert before["fingerprint"] == after["fingerprint"]
        assert before["artifact_sha256"] == after["artifact_sha256"]
        with Provenance(tmp_path) as store:
            assert store.read_bytes(before["artifact_sha256"]) == store.read_bytes(after["artifact_sha256"])


@pytest.mark.parametrize("module,field", [(policy_revision, "RULES"), (study_suite, "COSTS")])
def test_new_loaded_policy_globals_change_identity(module, field, monkeypatch):
    before = explorer._code_identity()
    value = getattr(module, field)
    monkeypatch.setattr(module, field, {**value, "fixture_change": True} if isinstance(value, dict)
                        else (*value, 100))
    after = explorer._code_identity()
    assert before["sources"] == after["sources"]
    key = "loaded_policy_revision_globals" if module is policy_revision else "loaded_study_suite_globals"
    assert before[key] != after[key]


@pytest.mark.parametrize("module,field", [(policy_revision, "validate_study"),
                                         (study_suite, "validate_membership")])
def test_new_loaded_validator_functions_change_identity(module, field, monkeypatch):
    before = explorer._code_identity()
    monkeypatch.setattr(module, field, lambda *args, **kwargs: {"fixture": "changed validator"})
    after = explorer._code_identity()
    key = "loaded_policy_revision_globals" if module is policy_revision else "loaded_study_suite_globals"
    assert before["sources"] == after["sources"] and before[key] != after[key]


def test_loaded_suite_change_during_execution_invalidates_result(tmp_path, boundary, monkeypatch):
    real_engine = explorer.run_event_backtest

    def change_after_calculation(*args, **kwargs):
        result = real_engine(*args, **kwargs)
        # Semantics and membership remain valid; a newly loaded global alone
        # must prevent publication under the earlier calculation identity.
        study_suite.FIXTURE_IDENTITY_CHANGE = "changed during calculation"
        return result

    monkeypatch.setattr(explorer, "run_event_backtest", change_after_calculation)
    monkeypatch.setattr(study_suite, "FIXTURE_IDENTITY_CHANGE", None, raising=False)
    result = run_member(tmp_path, boundary)
    assert result["status"] == "invalid" and result["error_code"] == "code_changed_during_execution"
    assert "attempt_id" in result and "artifact_sha256" not in result


def test_new_module_disk_identities_are_reported(tmp_path, boundary):
    result = run_member(tmp_path, boundary)
    assert result["status"] == "success", result
    sources = artifact(tmp_path, result["artifact_sha256"])["code_identity"]["sources"]
    for module in (policy_revision, study_suite):
        path = explorer.Path(module.__file__)
        assert sources[path.name] == hash_bytes(path.read_bytes())


def paused_invocation(root, boundary, monkeypatch):
    """Create an actual complete roster and first launch, then stop dispatch."""
    def stop_before_child(*args, **kwargs):
        raise KeyboardInterrupt
    with monkeypatch.context() as patch:
        patch.setattr(explorer, "run_submission", stop_before_child)
        with pytest.raises(KeyboardInterrupt):
            study_suite.run_suite(root, {"suite_sha256": boundary["suite_sha256"]})
    with Provenance(root) as store:
        return store.list_submissions(kind="study_suite_run", status="pending")[0]["submission_id"]


def test_valid_registered_member_cannot_calculate_outside_complete_invocation(tmp_path, boundary, monkeypatch):
    monkeypatch.setattr(explorer, "run_event_backtest", lambda *a, **k: pytest.fail("must not calculate"))
    result = explorer.run_submission(tmp_path, boundary["requests"][0])
    assert result["status"] == "invalid" and result["error_code"] == "suite_invocation_required"
    no_attempts(tmp_path)


@pytest.mark.parametrize("case,code", [
    ("unknown_run", "artifact_or_storage_unavailable"),
    ("unregistered_run", "suite_invocation_mismatch"),
    ("wrong_kind", "suite_invocation_not_pending"),
    ("missing_launch", "suite_launch_request_mismatch"),
])
def test_fake_or_missing_invocation_launch_refuses_before_calculation(tmp_path, boundary, monkeypatch, case, code):
    run_id = paused_invocation(tmp_path, boundary, monkeypatch)
    member = boundary["requests"][0]
    if case == "unknown_run":
        run_id = "f" * 32
    elif case == "unregistered_run":
        with Provenance(tmp_path) as store:
            run_id = store.begin("study_suite_run", {"suite_sha256": boundary["suite_sha256"]})
    elif case == "wrong_kind":
        with Provenance(tmp_path) as store:
            run_id = store.begin("exploratory_study", {"fixture": "wrong kind"})
    else:
        # The genuine complete run has launched only cost 0; cost 10 is present
        # in the roster but has no committed launch authorizing this child.
        member = boundary["requests"][1]
    monkeypatch.setattr(explorer, "run_event_backtest", lambda *a, **k: pytest.fail("must not calculate"))
    result = explorer.run_submission(tmp_path, member, suite_run_id=run_id)
    assert result["status"] == "invalid" and result["error_code"] == code
    no_attempts(tmp_path)


def test_bound_child_crash_remains_inspectable_and_duplicate_launch_is_refused(tmp_path, boundary, monkeypatch):
    def stop_after_child_binding(*args, **kwargs):
        raise KeyboardInterrupt
    with monkeypatch.context() as patch:
        patch.setattr(explorer, "run_event_backtest", stop_after_child_binding)
        with pytest.raises(KeyboardInterrupt):
            study_suite.run_suite(tmp_path, {"suite_sha256": boundary["suite_sha256"]})
    with Provenance(tmp_path) as store:
        run = store.list_submissions(kind="study_suite_run", status="pending")[0]
    summary = study_suite.inspect_run(tmp_path, run["submission_id"])
    assert not summary["complete"] and len(summary["members"]) == 3
    first, second, third = summary["members"]
    assert first["outcome"]["status"] == "pending" and first["outcome"]["submission_id"]
    assert second["outcome"] == third["outcome"] == {"status": "pending", "phase": "not_started"}
    result = explorer.run_submission(tmp_path, boundary["requests"][0], suite_run_id=run["submission_id"])
    assert result["status"] == "invalid" and result["error_code"] == "suite_launch_already_bound"
    after = study_suite.inspect_run(tmp_path, run["submission_id"])
    assert after == summary
    with Provenance(tmp_path) as store:
        assert store.journal.connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 1
        assert store.journal.connection.execute("SELECT COUNT(*) FROM study_suite_results").fetchone()[0] == 1
        events = [(row["id"], row["kind"]) for row in store.journal.connection.execute("SELECT id,kind FROM events")]
        bound = next(i for i, kind in events if kind == "study_suite_member_bound")
        execution = next(i for i, kind in events if kind == "explorer_execution_registered")
        assert bound < execution


def test_invalid_before_launch_binding_is_still_recorded_in_every_slot(tmp_path, boundary, monkeypatch):
    original = admission.validate_admission

    def refuse_after_registration(store, digest, dataset):
        if store.list_submissions(kind="exploratory_study"):
            raise admission.AdmissionError("fixture_refused_before_launch_binding")
        return original(store, digest, dataset)

    monkeypatch.setattr(admission, "validate_admission", refuse_after_registration)
    result = study_suite.run_suite(tmp_path, {"suite_sha256": boundary["suite_sha256"]})
    assert result["status"] == "invalid" and result["complete"]
    assert [row["outcome"]["status"] for row in result["summary"]["members"]] == ["invalid"] * 3
    assert all(row["outcome"]["error_code"] == "fixture_refused_before_launch_binding"
               for row in result["summary"]["members"])
    no_attempts(tmp_path)
    with Provenance(tmp_path) as store:
        assert store.journal.connection.execute("SELECT COUNT(*) FROM study_suite_results").fetchone()[0] == 3
        assert store.journal.connection.execute(
            "SELECT COUNT(*) FROM events WHERE kind='study_suite_member_bound'").fetchone()[0] == 0


def test_full_registered_synthetic_admission_suite_and_exact_replay_without_validator_stubs(tmp_path):
    # Real source/admission/revision validators; every underlying source and
    # claimed review is explicitly invented fixture evidence, not market data.
    from test_admission import regular_way_fixture
    request, revision_request = regular_way_fixture(tmp_path)
    admitted = admission.admit_dataset(tmp_path, request)
    assert admitted["status"] == "success", admitted
    frozen = revision_request["frozen_study"]
    members = [{"dataset_sha256": request["dataset_sha256"],
                "admission_sha256": admitted["admission_sha256"], "study_name": "invented full-suite replay",
                "evaluation_start": frozen["evaluation_start"], "evaluation_end": frozen["evaluation_end"],
                "specification": {**{key: frozen[key] for key in (
                    "lookback", "entry_threshold", "exit_threshold", "starting_cash")}, "cost_bps": cost}}
               for cost in (0, 10, 25)]
    registration = study_suite.register_suite(tmp_path, {"members": members})
    assert registration["status"] == "success", registration
    runs = [study_suite.run_suite(tmp_path, {"suite_sha256": registration["suite_sha256"]}) for _ in range(2)]
    assert all(run["status"] == "success" and run["all_success"] for run in runs), runs
    initial, replay = [[item["outcome"] for item in run["summary"]["members"]] for run in runs]
    assert len({item["fingerprint"] for item in initial}) == 3
    for before, after in zip(initial, replay):
        assert before["attempt_id"] != after["attempt_id"]
        assert before["fingerprint"] == after["fingerprint"]
        assert before["artifact_sha256"] == after["artifact_sha256"]
        report = artifact(tmp_path, before["artifact_sha256"])
        evidence = report["admission_evidence"]
        assert evidence["accepted_action_treatments"][0]["annotation"]["purchaser_entitlement"]["classification"] == "inferred"
        assert evidence["policy_revision"]["lineage"]["post_acquisition_change_count"] == 2
        assert len(report["study_suite"]["members"]) == 3

"""Synthetic roster/storage tests; no market or financial-performance evidence."""
from copy import deepcopy
import json

import pytest
from access_fixtures import synthetic_access as synthetic_access


from quanto import admission, explorer, policy_revision, study_suite
from quanto.ledger import hash_bytes, hash_json
from quanto.provenance import MAX_REQUEST_BYTES, Provenance, ProvenanceError
from quanto.study_suite import inspect_run, register_suite, run_suite, validate_membership

pytestmark = pytest.mark.usefixtures("synthetic_access")


@pytest.fixture
def suite_request(tmp_path, monkeypatch):
    with Provenance(tmp_path) as store:
        dataset = store.put_json({"fixture": "dataset"})
        revision = store.put_json({"fixture": "revision"})
        source = store.put_bytes(b"invented public source fixture")
        admitted = store.put_json({"fixture": "admission"})
        submission = store.begin("historical_admission", {"fixture": "admission"})
        store.finish(submission, "success", {"admission_sha256": admitted,
                                             "artifact_refs": [admitted]})

    def validate_admission(store, digest, dataset_digest):
        assert digest == admitted and dataset_digest == dataset
        for ref in (dataset, revision, source, admitted):
            store.read_bytes(ref)
        return {"policy_revision_sha256": revision, "artifact_refs": [source, revision, dataset]}

    def validate_study(store, digest, request):
        assert digest == revision
        store.read_bytes(revision)
        return {"frozen_study": {"fixture": True}}

    monkeypatch.setattr(admission, "validate_admission", validate_admission)
    monkeypatch.setattr(policy_revision, "validate_study", validate_study)
    return {"members": [{"dataset_sha256": dataset, "admission_sha256": admitted,
                          "study_name": "invented suite", "evaluation_start": "2024-01-02",
                          "evaluation_end": "2024-01-08",
                          "specification": {"lookback": 2, "cost_bps": cost}}
                         for cost in (0, 10, 25)]}


def registered(tmp_path, request):
    result = register_suite(tmp_path, request)
    assert result["status"] == "success", result
    return result["suite_sha256"]


def runner(monkeypatch, statuses=("success", "success", "success")):
    calls = []

    def execute(root, request, *, suite_run_id=None):
        index = len(calls) % 3
        calls.append(deepcopy(request))
        with Provenance(root) as store:
            submission = store.begin("exploratory_study", request)
            validate_membership(store, request["suite_sha256"], request,
                                before_submission_id=submission)
            study_suite.validate_launch(store, suite_run_id, request, submission, bind=True)
            status = statuses[index]
            if status != "pending":
                digest = store.put_json({"fixture_result": request["specification"]["cost_bps"]})
                details = ({"artifact_sha256": digest, "artifact_refs": [digest],
                            "fingerprint": hash_json(request), "attempt_id": "fixture"}
                           if status == "success" else {"error_code": "fixture_refusal"})
                store.finish(submission, status, details)
            return {"submission_id": submission, "status": status}

    monkeypatch.setattr(explorer, "run_submission", execute)
    return calls


@pytest.mark.parametrize("operation", [register_suite, run_suite])
@pytest.mark.parametrize("raw,code", [
    ('{"secret":"unretained-private-value",', "invalid_request_json"),
    ('{"members":[],"members":[]}', "duplicate_request_key"),
    ('[]', "request_must_be_object"),
    ('{"members":NaN}', "nonfinite_request"),
])
def test_begin_before_validation_and_private_invalid_bytes_not_retained(tmp_path, operation, raw, code):
    result = operation(tmp_path, raw)
    assert result["status"] == "invalid" and result["error_code"] == code
    with Provenance(tmp_path) as store:
        receipt = store.get_submission(result["submission_id"])
        assert receipt["request_sha256"] == hash_bytes(raw.encode())
        assert "unretained-private-value" not in json.dumps(receipt)
        assert "unretained-private-value" not in str(store.journal.connection.execute(
            "SELECT payload FROM events").fetchall())
        assert not list((tmp_path / "data" / "objects").iterdir())


@pytest.mark.parametrize("operation", [register_suite, run_suite])
def test_oversize_remains_preflight_boundary(tmp_path, operation):
    with pytest.raises(ProvenanceError):
        operation(tmp_path, "x" * (MAX_REQUEST_BYTES + 1))
    with Provenance(tmp_path) as store:
        assert store.list_submissions() == []


@pytest.mark.parametrize("mutation,code", [
    (lambda r: r["members"].pop(), "three_suite_members_required"),
    (lambda r: r["members"][2]["specification"].update(cost_bps=10), "suite_cost_roster_mismatch"),
    (lambda r: r["members"][0]["specification"].update(cost_bps=False), "suite_cost_roster_mismatch"),
    (lambda r: r["members"][0]["specification"].update(cost_bps=0.0), "suite_cost_roster_mismatch"),
    (lambda r: r["members"][1].update(study_name="changed"), "suite_members_differ_beyond_cost"),
    (lambda r: r["members"][1]["specification"].update(lookback=3), "suite_members_differ_beyond_cost"),
    (lambda r: r["members"][1].update(evaluation_end="2024-01-09"), "suite_members_differ_beyond_cost"),
])
def test_complete_frozen_roster_is_required(tmp_path, suite_request, monkeypatch, mutation, code):
    monkeypatch.setattr(explorer, "run_submission", lambda *a: pytest.fail("no calculation"))
    mutation(suite_request)
    result = register_suite(tmp_path, suite_request)
    assert result["status"] == "invalid" and result["error_code"] == code


def test_validates_all_members_against_revision(tmp_path, suite_request, monkeypatch):
    calls = []
    monkeypatch.setattr(policy_revision, "validate_study", lambda s, r, m: calls.append(m))
    digest = registered(tmp_path, suite_request)
    assert [item["specification"]["cost_bps"] for item in calls] == [0, 10, 25]
    with Provenance(tmp_path) as store:
        manifest = store.read_json(digest)
        assert [m["request_sha256"] for m in manifest["members"]] == [
            hash_json(m) for m in suite_request["members"]]


def test_registration_freezes_dict_before_begin(tmp_path, suite_request, monkeypatch):
    original = Provenance.begin

    def begin(store, kind, request):
        result = original(store, kind, request)
        if kind == "study_suite_registration":
            suite_request["members"][0]["specification"]["lookback"] = 999
        return result

    monkeypatch.setattr(Provenance, "begin", begin)
    digest = registered(tmp_path, suite_request)
    with Provenance(tmp_path) as store:
        assert store.read_json(digest)["members"][0]["request"]["specification"]["lookback"] == 2


def test_membership_and_journal_registration_must_precede_study(tmp_path, suite_request):
    with Provenance(tmp_path) as store:
        early = store.begin("exploratory_study", {"fixture": "too early"})
    digest = registered(tmp_path, suite_request)
    request = {**suite_request["members"][1], "suite_sha256": digest}
    with Provenance(tmp_path) as store:
        with pytest.raises(study_suite.StudySuiteError, match="suite_registered_after_study"):
            validate_membership(store, digest, request, before_submission_id=early)
        current = store.begin("exploratory_study", request)
        verified = validate_membership(store, digest, request, before_submission_id=current)
        assert verified["member"]["cost_bps"] == 10 and len(verified["members"]) == 3
        changed = deepcopy(request)
        changed["specification"]["lookback"] = 3
        with pytest.raises(study_suite.StudySuiteError, match="study_not_in_suite"):
            validate_membership(store, digest, changed)


def test_unregistered_manifest_cannot_prove_membership(tmp_path, suite_request):
    digest = registered(tmp_path, suite_request)
    with Provenance(tmp_path) as store:
        manifest = store.read_json(digest)
        changed = store.put_json({**manifest, "extra": "not registered"})
        with pytest.raises(study_suite.StudySuiteError, match="suite_not_registered"):
            validate_membership(store, changed, {**suite_request["members"][0], "suite_sha256": changed})


def test_tombstoned_dependency_refuses_before_calculation(tmp_path, suite_request, monkeypatch):
    digest = registered(tmp_path, suite_request)
    with Provenance(tmp_path) as store:
        store.tombstone(store.read_json(digest)["policy_revision_sha256"], "invalid_artifact")
    monkeypatch.setattr(explorer, "run_submission", lambda *a: pytest.fail("no calculation"))
    result = run_suite(tmp_path, {"suite_sha256": digest})
    assert result["status"] == "invalid" and result["error_code"] == "artifact_or_storage_unavailable"


@pytest.mark.parametrize("statuses,status,complete", [
    (("success", "success", "success"), "success", True),
    (("success", "invalid", "success"), "invalid", True),
    (("failed", "invalid", "success"), "failed", True),
    (("success", "pending", "invalid"), "interrupted", False),
    (("success", "interrupted", "success"), "interrupted", False),
])
def test_summary_preserves_every_member_outcome(tmp_path, suite_request, monkeypatch, statuses, status, complete):
    digest = registered(tmp_path, suite_request)
    calls = runner(monkeypatch, statuses)
    result = run_suite(tmp_path, {"suite_sha256": digest})
    assert result["status"] == status, result
    assert len(calls) == 3 and result["complete"] is complete
    assert [m["outcome"]["status"] for m in result["summary"]["members"]] == list(statuses)
    with Provenance(tmp_path) as store:
        assert store.read_json(result["summary_sha256"]) == result["summary"]
        assert store.get_submission(result["submission_id"])["status"] == status
        events = [(row["id"], row["kind"]) for row in store.journal.connection.execute(
            "SELECT id,kind FROM events")]
        roster_event = next(i for i, k in events if k == "study_suite_run_registered")
        assert all(i > roster_event for i, k in events if k == "study_suite_member_launched")


def test_deliberate_replay_is_separate_attempt_with_identical_requests(tmp_path, suite_request, monkeypatch):
    digest = registered(tmp_path, suite_request)
    calls = runner(monkeypatch)
    first = run_suite(tmp_path, {"suite_sha256": digest})
    second = run_suite(tmp_path, {"suite_sha256": digest})
    assert first["status"] == second["status"] == "success"
    assert first["submission_id"] != second["submission_id"]
    assert calls[:3] == calls[3:]
    assert [m["outcome"]["artifact_sha256"] for m in first["summary"]["members"]] == [
        m["outcome"]["artifact_sha256"] for m in second["summary"]["members"]]
    assert [m["outcome"]["submission_id"] for m in first["summary"]["members"]] != [
        m["outcome"]["submission_id"] for m in second["summary"]["members"]]


def test_crash_retains_complete_roster_and_pending_slots_without_retry(tmp_path, suite_request, monkeypatch):
    digest = registered(tmp_path, suite_request)
    calls = runner(monkeypatch)
    execute = explorer.run_submission

    def crash(root, request, *, suite_run_id=None):
        if len(calls) == 1:
            raise KeyboardInterrupt
        return execute(root, request, suite_run_id=suite_run_id)

    monkeypatch.setattr(explorer, "run_submission", crash)
    with pytest.raises(KeyboardInterrupt):
        run_suite(tmp_path, {"suite_sha256": digest})
    with Provenance(tmp_path) as store:
        pending = store.list_submissions(kind="study_suite_run", status="pending")
    assert len(pending) == 1
    summary = inspect_run(tmp_path, pending[0]["submission_id"])
    assert len(calls) == 1 and len(summary["members"]) == 3
    assert summary["complete"] is False
    assert [m["outcome"]["status"] for m in summary["members"]] == ["success", "pending", "pending"]
    assert [m["outcome"].get("phase") for m in summary["members"]] == [None, "launched", "not_started"]
    assert inspect_run(tmp_path, pending[0]["submission_id"]) == summary
    assert len(calls) == 1


def test_unexpected_member_exception_is_bounded_and_other_scenarios_are_retained(tmp_path, suite_request, monkeypatch):
    digest = registered(tmp_path, suite_request)
    calls = runner(monkeypatch)
    execute = explorer.run_submission
    entered = []

    def fail(root, request, *, suite_run_id=None):
        entered.append(request["specification"]["cost_bps"])
        if request["specification"]["cost_bps"] == 10:
            raise RuntimeError("private exception must not escape")
        return execute(root, request, suite_run_id=suite_run_id)

    monkeypatch.setattr(explorer, "run_submission", fail)
    result = run_suite(tmp_path, {"suite_sha256": digest})
    assert entered == [0, 10, 25] and len(calls) == 2
    assert result["status"] == "interrupted" and not result["complete"]
    assert [m["outcome"]["status"] for m in result["summary"]["members"]] == ["success", "pending", "success"]
    assert "private exception" not in json.dumps(result)


def test_finish_failure_leaves_inspectable_pending_run(tmp_path, suite_request, monkeypatch):
    digest = registered(tmp_path, suite_request)
    runner(monkeypatch)
    original = Provenance.finish

    def fail(store, submission_id, status, details):
        if store.get_submission(submission_id)["kind"] == "study_suite_run":
            raise ProvenanceError("fixture")
        return original(store, submission_id, status, details)

    monkeypatch.setattr(Provenance, "finish", fail)
    result = run_suite(tmp_path, {"suite_sha256": digest})
    assert result["status"] == "pending"
    summary = inspect_run(tmp_path, result["submission_id"])
    assert len(summary["members"]) == 3 and summary["all_success"] is True


def test_registration_publication_failure_is_retained(tmp_path, suite_request, monkeypatch):
    original = Provenance.put_json

    def fail(store, value):
        if isinstance(value, dict) and value.get("kind") == "study_suite":
            raise ProvenanceError("private publication error")
        return original(store, value)

    monkeypatch.setattr(Provenance, "put_json", fail)
    result = register_suite(tmp_path, suite_request)
    assert result["status"] == "interrupted" and result["error_code"] == "publication_interrupted"
    with Provenance(tmp_path) as store:
        assert store.get_submission(result["submission_id"])["status"] == "interrupted"


def test_exact_membership_rejects_numerically_equal_different_request_bytes(tmp_path, suite_request):
    digest = registered(tmp_path, suite_request)
    request = {**deepcopy(suite_request["members"][1]), "suite_sha256": digest}
    request["specification"]["cost_bps"] = 10.0
    with Provenance(tmp_path) as store:
        with pytest.raises(study_suite.StudySuiteError, match="study_not_in_suite"):
            validate_membership(store, digest, request)


def test_admission_must_already_have_finished_before_registration(tmp_path, suite_request, monkeypatch):
    original = Provenance.begin
    with Provenance(tmp_path) as store:
        # Mock validation will recognize a different receipt registered only
        # after the suite begins; journal ordering must independently refuse it.
        late_digest = store.put_json({"fixture": "late admission"})
    for member in suite_request["members"]:
        member["admission_sha256"] = late_digest
    monkeypatch.setattr(admission, "validate_admission", lambda store, a, d: {
        "policy_revision_sha256": store.put_json({"fixture": "revision"}), "artifact_refs": [d]})

    def begin(store, kind, request):
        result = original(store, kind, request)
        if kind == "study_suite_registration":
            late = original(store, "historical_admission", {"fixture": "late"})
            store.finish(late, "success", {"admission_sha256": late_digest, "artifact_refs": [late_digest]})
        return result

    monkeypatch.setattr(Provenance, "begin", begin)
    result = register_suite(tmp_path, suite_request)
    assert result["status"] == "invalid" and result["error_code"] == "suite_admission_order_mismatch"


def test_dependency_tombstone_does_not_hide_existing_run_slots(tmp_path, suite_request, monkeypatch):
    digest = registered(tmp_path, suite_request)
    runner(monkeypatch)
    result = run_suite(tmp_path, {"suite_sha256": digest})
    with Provenance(tmp_path) as store:
        store.tombstone(store.read_json(digest)["policy_revision_sha256"], "invalid_artifact")
    summary = inspect_run(tmp_path, result["submission_id"])
    assert summary["all_success"] and len(summary["members"]) == 3

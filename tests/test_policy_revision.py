"""Synthetic public evidence tests; these establish no investment performance."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
from access_fixtures import synthetic_access as synthetic_access


from quanto.ledger import canonical_json
from quanto.policy_revision import (APPROVED_REVIEWS, FROZEN_FIELDS, PolicyRevisionError, _facts_delta,
                                    register_revision, validate_revision, validate_study)
from quanto.provenance import Provenance, ProvenanceError
from test_admission import evidence, DATES

pytestmark = pytest.mark.usefixtures("synthetic_access")


def _plan():
    return {"instrument": "FIX", "data_start": DATES[0], "data_end": DATES[-1],
            "evaluation_start": DATES[2], "evaluation_end": DATES[-1], "lookback": 2,
            "starting_cash": 10000, "entry_threshold": 0, "exit_threshold": 0,
            "cost_bps_scenarios": [0, 10, 25], "basis": "raw", "signal_basis": "raw completed close",
            "dividend_reinvestment": "none", "signal_rule": "fixed SMA strict crossings",
            "sma_includes_current_close": True, "warmup_selection": "prior lookback sessions",
            "buy_quantity": "cash inclusive of cost", "sell_proceeds": "net of costs",
            "arithmetic": {"economic_cash": True}, "benchmark": "same window and costs",
            "terminal_policy": "no liquidation", "session_order": ["split", "target", "close"],
            "dividend_rate_basis": "ex_date_shares", "split_effective_date": "first adjusted session",
            "same_session_split_and_dividend": "refuse"}


def _record_plan(store, plan, kind="pilot_plan_registration"):
    digest = store.put_json(plan)
    submission = store.begin(kind, {"plan_sha256": digest})
    store.finish(submission, "success", {"plan_sha256": digest, "artifact_refs": [digest],
                                         "financial_result": False})
    return {"submission_id": submission, "plan_sha256": digest}


def _refusal(store, request, code):
    # Exact text bytes are deliberately noncanonical, as in the legacy path.
    raw = json.dumps(request, indent=2)
    digest = store.put_bytes(raw.encode())
    submission = store.begin("historical_admission", raw)
    store.finish(submission, "invalid", {"error_code": code, "result_kind": "no_admission"})
    return {"submission_id": submission, "request_sha256": digest}


def revision_fixture(root):
    full = _plan()
    with Provenance(root) as store:
        first = {key: value for key, value in full.items() if key in (
            "instrument", "data_start", "data_end", "evaluation_start", "evaluation_end", "lookback",
            "starting_cash", "entry_threshold", "exit_threshold", "cost_bps_scenarios", "basis")}
        plans = [_record_plan(store, first)]
        second = {**first, "signal_rule": full["signal_rule"],
                  "previous_plan_bytes_sha256": plans[-1]["plan_sha256"]}
        plans.append(_record_plan(store, second))
        third = {**full, "previous_plan_bytes_sha256": plans[-1]["plan_sha256"]}
        plans.append(_record_plan(store, third))
    request = evidence(root)
    with Provenance(root) as store:
        initial = _refusal(store, request, "identity_change_unresolved")
        fourth = {**third, "previous_plan_bytes_sha256": plans[-1]["plan_sha256"],
                  "relevance_refinement": {"kind": "implementation_of_preexisting_structured_exclusion",
                      "facts_sha256": request["primary_facts_sha256"],
                      "original_admission_refusal": initial["submission_id"],
                      "portfolio_result_observed_before_refinement": False,
                      "strategy_window_costs_unchanged": True}}
        plans.append(_record_plan(store, fourth, "pilot_plan_refinement"))
        latest = _refusal(store, request, "unsupported_due_bill")
        facts = store.read_json(request["primary_facts_sha256"])
        public = store.put_bytes(b'SYNTHETIC new public rule source')
        facts["sources"].append({"sha256": public, "url": "https://rules.example/fixture",
                                 "title": "Synthetic rule", "locator": "section 1"})
        facts["events"][0]["regular_way_split"] = {"profile": "synthetic placeholder; admission validates semantics"}
        facts["events"][0]["semantic_review_sha256"] = store.put_json({"kind": "synthetic_review"})
        facts["independent_schedule_sha256"] = store.put_json({"kind": "synthetic_schedule"})
        new_facts = store.put_json(facts)
        decision = store.put_bytes((Path(__file__).resolve().parents[1] / "docs" / "D007_POLICY.md").read_bytes())
        review_directory = Path(__file__).resolve().parents[1] / "docs" / "reviews"
        reviews = [store.put_bytes((review_directory / ("D007-" + name + ".md")).read_bytes())
                   for name in APPROVED_REVIEWS]
    return {"schema_version": 1, "kind": "policy_revision_request", "predecessor_plans": plans,
            "refused_admissions": [initial, latest], "accepted_decision_sha256": decision,
            "review_sha256s": reviews, "new_primary_facts_sha256": new_facts,
            "frozen_study": {key: full[key] for key in FROZEN_FIELDS},
            "classification": "post_acquisition_development_only"}, request


def test_registered_revision_binds_full_chain_exact_requests_and_study(tmp_path):
    request, prior = revision_fixture(tmp_path)
    result = register_revision(tmp_path, request)
    assert result["status"] == "success", result
    assert result["post_acquisition_change_count"] == 2
    next_request = {**prior, "primary_facts_sha256": request["new_primary_facts_sha256"],
                    "policy_revision_sha256": result["policy_revision_sha256"]}
    with Provenance(tmp_path) as store:
        admission_id = store.begin("historical_admission", next_request)
        revision = validate_revision(store, result["policy_revision_sha256"], next_request,
                                     before_submission_id=admission_id)
        assert len(revision["lineage"]["plans"]) == 4
        assert [entry["error_code"] for entry in revision["lineage"]["prior_refusals"]] == [
            "identity_change_unresolved", "unsupported_due_bill"]
        assert len(revision["facts_delta"]) == 4
        for cost in [0, 10, 25]:
            study = {"dataset_sha256": prior["dataset_sha256"], "evaluation_start": DATES[2],
                     "evaluation_end": DATES[-1], "specification": {"lookback": 2, "cost_bps": cost}}
            assert validate_study(store, revision, study) == revision
        study["specification"]["lookback"] = 3
        with pytest.raises(PolicyRevisionError, match="study_outside_frozen_revision"):
            validate_study(store, revision, study)


@pytest.mark.parametrize("mutation,code", [
    (lambda r: r["predecessor_plans"].pop(1), "incomplete_predecessor_chain"),
    (lambda r: r["predecessor_plans"].reverse(), "incomplete_predecessor_chain"),
    (lambda r: r["refused_admissions"].reverse(), "prior_refusal_outcome_mismatch"),
    (lambda r: r["frozen_study"].update(lookback=3), "predecessor_frozen_fields_changed"),
    (lambda r: r["frozen_study"].update(cost_bps_scenarios=[0, 10]), "invalid_frozen_study"),
])
def test_false_or_reordered_lineage_refused(tmp_path, mutation, code):
    request, _ = revision_fixture(tmp_path)
    mutation(request)
    result = register_revision(tmp_path, request)
    assert (result["status"], result["error_code"]) == ("invalid", code)
    with Provenance(tmp_path) as store:
        assert store.get_submission(result["submission_id"])["status"] == "invalid"


@pytest.mark.parametrize("mutation", [
    lambda f: f.update(reviewer="replacement author"),
    lambda f: f["sources"][0].update(locator="rewritten"),
    lambda f: f["events"].reverse(),
    lambda f: f["events"][0]["event"].update(new_rate="100"),
    lambda f: f["events"].append(deepcopy(f["events"][1])),
    lambda f: f.update(excluded_actions=[]),
])
def test_nonadditive_facts_refused(tmp_path, mutation):
    request, prior = revision_fixture(tmp_path)
    with Provenance(tmp_path) as store:
        facts = store.read_json(request["new_primary_facts_sha256"])
        mutation(facts)
        changed = store.put_json(facts)
        with pytest.raises(PolicyRevisionError, match="non_additive_primary_facts"):
            _facts_delta(store, prior["primary_facts_sha256"], changed)


def test_exact_prior_request_bytes_required_and_tombstones_rechecked(tmp_path):
    request, prior = revision_fixture(tmp_path)
    with Provenance(tmp_path) as store:
        forged = store.put_bytes(canonical_json(prior).encode())
    changed = deepcopy(request)
    changed["refused_admissions"][-1]["request_sha256"] = forged
    assert register_revision(tmp_path, changed)["error_code"] == "predecessor_request_mismatch"
    result = register_revision(tmp_path, request)
    assert result["status"] == "success"
    with Provenance(tmp_path) as store:
        store.tombstone(request["predecessor_plans"][0]["plan_sha256"], "operator_requested")
        with pytest.raises(ProvenanceError, match="tombstoned"):
            validate_revision(store, result["policy_revision_sha256"])


def test_registration_before_validation_and_pending_publication(tmp_path, monkeypatch):
    result = register_revision(tmp_path, '{"broken":')
    assert result["status"] == "invalid"
    with Provenance(tmp_path) as store:
        assert store.get_submission(result["submission_id"])["status"] == "invalid"
    request, _ = revision_fixture(tmp_path)
    original = Provenance.finish
    def broken_finish(self, submission, status, details):
        if self.get_submission(submission)["kind"] == "policy_revision":
            raise ProvenanceError("test storage interruption")
        return original(self, submission, status, details)
    monkeypatch.setattr(Provenance, "finish", broken_finish)
    result = register_revision(tmp_path, request)
    assert result["status"] == "pending"
    with Provenance(tmp_path) as store:
        assert store.get_submission(result["submission_id"])["status"] == "pending"


def test_revision_must_finish_before_admission_and_changed_policy_refuses(tmp_path, monkeypatch):
    request, prior = revision_fixture(tmp_path)
    with Provenance(tmp_path) as store:
        earlier_admission = store.begin("historical_admission", prior)
    result = register_revision(tmp_path, request)
    assert result["status"] == "success"
    with Provenance(tmp_path) as store:
        with pytest.raises(PolicyRevisionError, match="policy_revision_must_precede_admission"):
            validate_revision(store, result["policy_revision_sha256"], before_submission_id=earlier_admission)
        from quanto import explorer
        original = explorer._code_identity
        monkeypatch.setattr(explorer, "_code_identity", lambda: {**original(), "changed": True})
        with pytest.raises(PolicyRevisionError, match="policy_revision_dependencies_changed"):
            validate_revision(store, result["policy_revision_sha256"])


def test_publication_failure_retains_interrupted_outcome(tmp_path, monkeypatch):
    request, _ = revision_fixture(tmp_path)
    original = Provenance.put_json
    def interrupted_put(self, value):
        if isinstance(value, dict) and value.get("kind") == "policy_revision":
            raise ProvenanceError("synthetic publication failure")
        return original(self, value)
    monkeypatch.setattr(Provenance, "put_json", interrupted_put)
    result = register_revision(tmp_path, request)
    assert (result["status"], result["error_code"]) == ("interrupted", "publication_interrupted")
    with Provenance(tmp_path) as store:
        assert store.get_submission(result["submission_id"])["status"] == "interrupted"


def test_materialized_submission_forgery_detected(tmp_path):
    request, _ = revision_fixture(tmp_path)
    with Provenance(tmp_path) as store:
        # Simulate an owner modifying a table while leaving its genuine journal
        # event unchanged. Ordinary application clients cannot perform this edit.
        store.journal.connection.execute("DROP TRIGGER no_update_provenance_outcomes")
        entry = request["predecessor_plans"][0]
        observed = store.get_submission(entry["submission_id"])
        forged = {**observed["details"], "financial_result": True}
        store.journal.connection.execute("UPDATE provenance_outcomes SET details=? WHERE submission_id=?",
                                         (canonical_json(forged), entry["submission_id"]))
    result = register_revision(tmp_path, request)
    assert result["error_code"] == "submission_journal_mismatch"


def test_changed_source_bytes_and_json_type_change_refused(tmp_path):
    request, prior = revision_fixture(tmp_path)
    with Provenance(tmp_path) as store:
        changed = store.read_json(request["new_primary_facts_sha256"])
        # Python equality equates 1 and True; preservation must compare exact
        # JSON values so that a field cannot silently change its type.
        changed["schema_version"] = True
        altered = store.put_json(changed)
        with pytest.raises(PolicyRevisionError, match="non_additive_primary_facts"):
            _facts_delta(store, prior["primary_facts_sha256"], altered)
    digest = request["predecessor_plans"][0]["plan_sha256"]
    (tmp_path / "data" / "objects" / (digest + ".bin")).write_bytes(b"forged predecessor")
    result = register_revision(tmp_path, request)
    assert result["error_code"] == "artifact_or_storage_unavailable"


def test_accepted_decision_is_pinned(tmp_path):
    request, _ = revision_fixture(tmp_path)
    with Provenance(tmp_path) as store:
        request["accepted_decision_sha256"] = store.put_bytes(b"Arbitrary unapproved decision")
    result = register_revision(tmp_path, request)
    assert result["error_code"] == "accepted_decision_mismatch"


@pytest.mark.parametrize("replace", [False, True])
def test_mandatory_design_review_roster(tmp_path, replace):
    request, _ = revision_fixture(tmp_path)
    request["review_sha256s"].pop()
    if replace:
        with Provenance(tmp_path) as store:
            request["review_sha256s"].append(store.put_bytes(b"Unapproved substitute review"))
    result = register_revision(tmp_path, request)
    assert result["error_code"] == "approved_policy_reviews_required"

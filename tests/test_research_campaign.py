"""Invented source transports exercise real registration/admission/event paths."""
from copy import deepcopy
from decimal import Decimal
import json

import pytest

from access_fixtures import synthetic_access as synthetic_access
from test_admission import DATES, MARKET, evidence
from quanto import explorer, research_campaign as campaign, research_metrics
from quanto.admission import admit_dataset
from quanto.ledger import Journal
from quanto.provenance import Provenance

pytestmark = pytest.mark.usefixtures("synthetic_access")


def manifest(count=3):
    return {
        "design": {"rationale": "Invented slow-trend variants for software checks only.",
                   "instrument_selection_rule": "One fixed invented issuer; no alternative on refusal.",
                   "candidate_sources": ["Synthetic fixture specification; no empirical source claim."]},
        "market": deepcopy(MARKET),
        "acquisition_request": {"symbol": "FIX", "start": DATES[0], "end": DATES[-1],
                                "adjustment": "raw"},
        "candidates": [{"id": "candidate_" + str(n), "specification": {
            "lookback": n, "entry_threshold": 0, "exit_threshold": 0}} for n in range(1, count + 1)],
        "cost_bps": [0, 10, 25], "primary_cost_bps": 10, "starting_cash": 10000,
        "blocks": [{"name": "development", "start": "2024-06-06", "end": "2024-06-07"},
                   {"name": "validation", "start": "2024-06-08", "end": "2024-06-11"},
                   {"name": "assessment", "start": "2024-06-12", "end": "2024-06-14"}],
        "selection_criterion": campaign.CRITERION,
    }


def read(root, digest):
    with Provenance(root) as store:
        return store.read_json(digest)


def prepare(root, count=3):
    registration = campaign.register_campaign(root, manifest(count))
    assert registration["status"] == "success", registration
    source = evidence(root)
    admission = admit_dataset(root, source)
    assert admission["status"] == "success", admission
    binding = campaign.bind_dataset(root, {
        "campaign_sha256": registration["campaign_sha256"],
        "dataset_sha256": source["dataset_sha256"], "admission_sha256": admission["admission_sha256"]})
    assert binding["status"] == "success", binding
    return {"campaign_sha256": registration["campaign_sha256"],
            "binding_sha256": binding["binding_sha256"]}, source, admission


def test_real_event_fixture_full_roster_and_continuous_wealth(tmp_path):
    request, source, _ = prepare(tmp_path)
    outcome = campaign.run_campaign(tmp_path, request)
    assert outcome["status"] == "success", outcome
    summary = read(tmp_path, outcome["summary_sha256"])
    assert summary["evidence_kind"] == "synthetic_fixture"
    assert summary["holdout_status"] == "unprotected_development"
    assert summary["complete"] and summary["all_success"]
    assert not summary["investment_validation"] and not summary["protected_evaluation"]
    assert len(summary["outcomes"]) == 9
    assert len({r["child_submission_id"] for r in summary["outcomes"]}) == 9
    for row in summary["outcomes"]:
        metrics = row["metrics"]
        assert metrics["evidence_kind"] == "synthetic_fixture"
        assert metrics["full"]["observations"] == 7
        development, validation, assessment = metrics["blocks"]
        for side in ("strategy", "benchmark"):
            assert Decimal(validation[side]["boundary_equity"]) == Decimal(development[side]["ending_equity"])
            assert Decimal(assessment[side]["boundary_equity"]) == Decimal(validation[side]["ending_equity"])
        with Provenance(tmp_path) as store:
            child = store.get_submission(row["child_submission_id"])
            assert child["details"]["dataset_sha256"] == source["dataset_sha256"]
            artifact = store.read_large_json(child["details"]["artifact_sha256"])
            assert "accounting_policy" in artifact["engine_report"]
            assert artifact["frozen_request"]["result_storage"] == "bounded_large_json"
    assert summary["selection"]["candidate_id"] is None
    assert not summary["selection"]["assessment_used_for_selection"]
    assert not summary["selection"]["stress_used_for_selection"]
    inspection = campaign.inspect_campaign(tmp_path, request["campaign_sha256"])
    assert inspection["current_evidence_available"]
    assert inspection["outcomes"] == summary["outcomes"]


@pytest.mark.parametrize("bad", [
    {"cost_bps": [0, 10, 10]}, {"cost_bps": [0, 10, 25, 50]}, {"primary_cost_bps": 0},
    {"selection_criterion": "best_assessment"}, {"evidence_kind": "historical_market_data"},
    {"candidates": []}, {"starting_cash": True},
])
def test_invalid_campaigns_are_registered_and_retained(tmp_path, bad):
    result = campaign.register_campaign(tmp_path, {**manifest(), **bad})
    assert result["status"] == "invalid"
    with Provenance(tmp_path) as store:
        record = store.get_submission(result["submission_id"])
        assert record["kind"] == "campaign_registration" and record["status"] == "invalid"
        assert not store.journal.connection.execute("SELECT 1 FROM research_campaigns").fetchone()


def test_duplicate_semantic_spec_and_noncontiguous_blocks(tmp_path):
    request = manifest(2)
    request["candidates"][1]["specification"] = {
        "lookback": 1, "entry_threshold": 0.0, "exit_threshold": 0.0}
    assert campaign.register_campaign(tmp_path, request)["error_code"] == "duplicate_candidate"
    request = manifest()
    request["blocks"][1]["start"] = "2024-06-09"
    assert campaign.register_campaign(tmp_path, request)["error_code"] == "noncontiguous_blocks"


@pytest.mark.parametrize("field,value", [
    ("rationale", ""), ("rationale", "x" * 2001), ("instrument_selection_rule", None),
    ("instrument_selection_rule", "bad\x00text"), ("candidate_sources", []),
    ("candidate_sources", ["x"] * 11), ("candidate_sources", ["x" * 501]),
    ("candidate_sources", ["two\nlines"]),
])
def test_design_is_required_bounded_and_retained_only_in_private_manifest(tmp_path, field, value):
    request = manifest()
    request["design"][field] = value
    receipt = campaign.register_campaign(tmp_path, request)
    assert receipt["status"] == "invalid"
    assert "design" not in receipt
    with Provenance(tmp_path) as store:
        assert store.get_submission(receipt["submission_id"])["status"] == "invalid"


def test_registered_manifest_preserves_preacquisition_design(tmp_path):
    request = manifest()
    receipt = campaign.register_campaign(tmp_path, request)
    assert receipt["status"] == "success", receipt
    stored = read(tmp_path, receipt["campaign_sha256"])
    assert stored["request"]["design"] == request["design"]
    request["design"]["rationale"] = "Changed after registration"
    assert read(tmp_path, receipt["campaign_sha256"])["request"]["design"] != request["design"]


def test_old_acquisition_cannot_be_bound_as_new(tmp_path):
    source = evidence(tmp_path)
    admitted = admit_dataset(tmp_path, source)
    registration = campaign.register_campaign(tmp_path, manifest())
    result = campaign.bind_dataset(tmp_path, {
        "campaign_sha256": registration["campaign_sha256"],
        "dataset_sha256": source["dataset_sha256"], "admission_sha256": admitted["admission_sha256"]})
    assert result["status"] == "invalid"
    assert result["error_code"] == "acquisition_precedes_campaign"


def test_second_campaign_run_never_replays(tmp_path):
    request, _, _ = prepare(tmp_path, 1)
    first = campaign.run_campaign(tmp_path, request)
    assert first["status"] == "success", first
    second = campaign.run_campaign(tmp_path, request)
    assert second["error_code"] == "campaign_already_consumed"
    with Provenance(tmp_path) as store:
        assert store.journal.connection.execute("SELECT count(*) FROM research_campaign_claims").fetchone()[0] == 3
        assert len(store.list_submissions(kind="exploratory_study")) == 3


def test_changed_helper_or_metric_global_refuses_before_dispatch(tmp_path, monkeypatch):
    request, _, _ = prepare(tmp_path, 1)
    monkeypatch.setattr(research_metrics, "_YEAR", Decimal("360"))
    outcome = campaign.run_campaign(tmp_path, request)
    assert outcome["error_code"] == "campaign_code_changed"
    with Provenance(tmp_path) as store:
        assert not store.list_submissions(kind="exploratory_study")


def test_selection_function_change_changes_frozen_identity(monkeypatch):
    original = campaign.code_identity()
    monkeypatch.setattr(campaign, "_selection", lambda *args: {"candidate_id": "fiction"})
    assert campaign.code_identity() != original


def test_source_tombstone_refuses_and_remains_visible(tmp_path):
    request, source, _ = prepare(tmp_path, 1)
    with Provenance(tmp_path) as store:
        store.tombstone(source["bars_receipt_sha256"], "rights_request")
    result = campaign.run_campaign(tmp_path, request)
    assert result["status"] != "success"
    with Provenance(tmp_path) as store:
        assert not store.list_submissions(kind="exploratory_study")


def test_midcampaign_current_evidence_failure_keeps_unattempted_slots(tmp_path, monkeypatch):
    # The dispatcher fault is installed before freeze. It runs exactly one real
    # event calculation, then tombstones its admitted dataset. No fake result.
    monkeypatch.setattr(explorer, "run_submission", _tombstone_after_child)
    request, _, _ = prepare(tmp_path, 2)
    outcome = campaign.run_campaign(tmp_path, request)
    assert outcome["status"] != "success"
    snapshot = campaign.inspect_campaign(tmp_path, request["campaign_sha256"])
    assert not snapshot["current_evidence_available"]
    assert len(snapshot["outcomes"]) == 6
    assert sum(r["status"] == "unattempted" for r in snapshot["outcomes"]) == 5
    assert all("metrics" not in row for row in snapshot["outcomes"])
    again = campaign.run_campaign(tmp_path, request)
    assert again["status"] != "success"
    with Provenance(tmp_path) as store:
        assert len(store.list_submissions(kind="exploratory_study")) == 1


_ORIGINAL_DISPATCH = explorer.run_submission


def _tombstone_after_child(root, request):
    result = _ORIGINAL_DISPATCH(root, request)
    with Provenance(root) as store:
        store.tombstone(request["dataset_sha256"], "rights_request")
    return result


def _cost_failure(root, request):
    if request["specification"]["cost_bps"] == 25:
        raise RuntimeError("INVENTED private failure: must not appear in result")
    return _ORIGINAL_DISPATCH(root, request)


def test_cost_failure_retained_without_retry_or_error_echo(tmp_path, monkeypatch):
    monkeypatch.setattr(explorer, "run_submission", _cost_failure)
    request, _, _ = prepare(tmp_path, 1)
    outcome = campaign.run_campaign(tmp_path, request)
    assert outcome["status"] == "interrupted", outcome
    summary = read(tmp_path, outcome["summary_sha256"])
    assert [r["status"] for r in summary["outcomes"]] == ["success", "success", "interrupted"]
    assert not summary["complete"] and not summary["all_success"]
    assert "INVENTED private failure" not in json.dumps(summary)
    assert campaign.run_campaign(tmp_path, request)["error_code"] == "campaign_already_consumed"


def selection_row(name, growth, benchmark, trades=2, cost=10, drawdown="0.1"):
    block = {"name": "validation", "strategy": {"total_return": growth,
             "max_drawdown": drawdown, "trade_count": trades},
             "benchmark": {"total_return": benchmark, "max_drawdown": "0.2"}}
    return {"candidate_id": name, "cost_bps": cost, "status": "success",
            "metrics": {"blocks": [block, {"name": "assessment", "ignored": "any outcome"}]}}


def test_selection_uses_validation_primary_cost_and_exact_ties_only():
    rows = [selection_row("b", "0.3", "0.1", trades=2),
            selection_row("a", "0.3", "0.1", trades=2),
            selection_row("c", "0.9", "0.1", cost=25)]
    assert campaign._selection(rows, {"primary_cost_bps": 10})["candidate_id"] == "a"
    rows[1]["metrics"]["blocks"][0]["strategy"]["trade_count"] = 3
    assert campaign._selection(rows, {"primary_cost_bps": 10})["candidate_id"] == "b"
    rows[0]["metrics"]["blocks"][0]["strategy"]["max_drawdown"] = "0.21"
    assert campaign._selection(rows, {"primary_cost_bps": 10})["candidate_id"] == "a"


def test_selection_exact_growth_difference_not_decimal_context_rounding():
    rows = [selection_row("a", "0.300000000000000000000000000000000001", "0.1"),
            selection_row("b", "0.300000000000000000000000000000000002", "0.1")]
    assert campaign._selection(rows, {"primary_cost_bps": 10})["candidate_id"] == "b"


def test_selection_permits_no_candidate_and_does_not_hide_primary_failure():
    row = selection_row("a", "0.2", "0.2")
    assert campaign._selection([row], {"primary_cost_bps": 10})["candidate_id"] is None
    row["status"] = "interrupted"
    assert campaign._selection([row], {"primary_cost_bps": 10})["reason"] == "incomplete_primary_comparison"


# Faults are installed before registration so source and imported-helper
# identities stay frozen throughout each invented campaign. Mutable clock
# state is outside the production module, like the critic's independent probe.
_CLOCK_STATE = {}
_ORIGINAL_GUARD = campaign._guard
_ORIGINAL_SELECTION = campaign._selection
_ORIGINAL_METRICS = research_metrics.summarize_trace
_ORIGINAL_PUT = Provenance.put_json
_ORIGINAL_FINISH = Provenance.finish
_ORIGINAL_EVENT = Journal._event


def _fixture_monotonic():
    return _CLOCK_STATE["time"]


def _expire_on(phase):
    if _CLOCK_STATE["armed"] and _CLOCK_STATE["phase"] == phase:
        _CLOCK_STATE["time"] = campaign.MAX_SECONDS + 1


def _slow_guard(*args):
    result = _ORIGINAL_GUARD(*args)
    if _CLOCK_STATE["armed"]:
        _CLOCK_STATE["guards"] += 1
        if _CLOCK_STATE["guards"] == 2:
            _expire_on("first_guard")
        if _CLOCK_STATE["guards"] == 5:
            _expire_on("final_guard")
    return result


def _slow_dispatch(*args):
    result = _ORIGINAL_DISPATCH(*args)
    _expire_on("dispatch")
    return result


def _slow_metrics(*args):
    result = _ORIGINAL_METRICS(*args)
    _expire_on("metrics")
    return result


def _slow_selection(*args):
    result = _ORIGINAL_SELECTION(*args)
    _expire_on("selection")
    return result


def _slow_put(self, value, **kwargs):
    result = _ORIGINAL_PUT(self, value, **kwargs)
    if isinstance(value, dict) and value.get("kind") == "campaign_development_summary":
        _expire_on("summary_write")
    return result


def _slow_finish(self, submission, status, details):
    result = _ORIGINAL_FINISH(self, submission, status, details)
    if status == "success" and self.get_submission(submission)["kind"] == "campaign_run":
        _expire_on("finish")
    return result


def _slow_event(self, kind, payload, now):
    result = _ORIGINAL_EVENT(self, kind, payload, now)
    if kind == "campaign_slot_claimed":
        _expire_on("claim")
    return result


@pytest.mark.parametrize("phase,children", [
    ("first_guard", 0), ("final_guard", 3), ("dispatch", 1), ("metrics", 1),
    ("selection", 3), ("summary_write", 3), ("finish", 3), ("claim", 0),
])
def test_deadline_after_slow_boundaries_never_dispatches_or_publishes_late(
        tmp_path, monkeypatch, phase, children):
    _CLOCK_STATE.clear()
    _CLOCK_STATE.update(armed=False, guards=0, time=0, phase=phase)
    monkeypatch.setattr(campaign.time, "monotonic", _fixture_monotonic)
    monkeypatch.setattr(campaign, "_guard", _slow_guard)
    monkeypatch.setattr(campaign, "_selection", _slow_selection)
    monkeypatch.setattr(explorer, "run_submission", _slow_dispatch)
    monkeypatch.setattr(research_metrics, "summarize_trace", _slow_metrics)
    monkeypatch.setattr(Provenance, "put_json", _slow_put)
    monkeypatch.setattr(Provenance, "finish", _slow_finish)
    monkeypatch.setattr(Journal, "_event", _slow_event)
    request, _, _ = prepare(tmp_path, 1)
    _CLOCK_STATE["armed"] = True
    result = campaign.run_campaign(tmp_path, request)
    assert result["status"] == "interrupted", result
    assert result["error_code"] == "campaign_deadline"
    assert "summary_sha256" not in result
    with Provenance(tmp_path) as store:
        assert len(store.list_submissions(kind="exploratory_study")) == children
        record = store.get_submission(result["submission_id"])
        assert record["status"] == "interrupted" and "summary_sha256" not in record["details"]
        assert store.journal.connection.execute("SELECT count(*) FROM research_campaign_runs").fetchone()[0] == 1
    # A new call gets a fresh clock envelope but cannot consume the same run.
    again = campaign.run_campaign(tmp_path, request)
    assert again["error_code"] == "campaign_already_consumed", again
    snapshot = campaign.inspect_campaign(tmp_path, request["campaign_sha256"])
    assert len(snapshot["outcomes"]) == 3
    if phase == "first_guard":
        assert all(row["status"] == "unattempted" for row in snapshot["outcomes"])
    elif phase in {"dispatch", "metrics", "claim"}:
        assert [row["status"] for row in snapshot["outcomes"]] == ["interrupted", "unattempted", "unattempted"]

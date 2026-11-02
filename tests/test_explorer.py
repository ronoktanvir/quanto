"""Registered synthetic workflow tests; these establish no investment performance."""
from copy import deepcopy
from datetime import datetime, timedelta
import json
import sqlite3
from zoneinfo import ZoneInfo

import pytest

from quanto import explorer
from quanto.explorer import list_exposures, register_dataset, run_submission
from quanto.ledger import hash_bytes
from quanto.provenance import MAX_REQUEST_BYTES, Provenance, ProvenanceError


MARKET = {"instrument_id": "synthetic:trend", "venue": "fixture", "currency": "USD",
          "session_timezone": "America/New_York"}


def rows():
    start = datetime(2024, 3, 6, tzinfo=ZoneInfo("America/New_York"))
    return [{"timestamp": (start + timedelta(days=i)).isoformat(), "symbol": "FIXTURE",
             "open": value, "high": value + 1, "low": value - 1, "close": value,
             "volume": 1000} for i, value in enumerate([10, 12, 14, 9, 11, 15, 16, 13, 12, 17])]


def registration(root, *, supplied=None, **changes):
    supplied = rows() if supplied is None else supplied
    with Provenance(root) as store:
        digest = store.put_json(supplied)
    request = {"data_sha256": digest, "evidence_kind": "synthetic_fixture", "market": MARKET,
               "price_basis": "raw", "expected_sessions": [row["timestamp"][:10] for row in rows()]}
    request.update(changes)
    return request


@pytest.fixture

def dataset(tmp_path):
    result = register_dataset(tmp_path, registration(tmp_path))
    assert result["status"] == "success", result
    return result["manifest_sha256"]


def request(dataset, lookback=2, **changes):
    value = {"dataset_sha256": dataset, "study_name": "trend probe",
             "evaluation_start": "2024-03-11", "evaluation_end": "2024-03-15",
             "specification": {"lookback": lookback, "cost_bps": 10}}
    value.update(changes)
    return value


def read(root, digest):
    with Provenance(root) as store:
        return store.read_json(digest)


@pytest.mark.parametrize("raw,code", [
    ('{"secret":"must-not-be-stored",', "invalid_request_json"),
    ('{"a":1,"a":2}', "duplicate_request_key"),
    ('{"a":NaN}', "nonfinite_request"),
    ('{"a":1e999}', "invalid_request_json"),
    ('[]', "request_must_be_object"),
])
@pytest.mark.parametrize("operation", [register_dataset, run_submission])
def test_invalid_text_is_registered_before_parse_without_retaining_raw_text(tmp_path, raw, code, operation):
    outcome = operation(tmp_path, raw)
    assert outcome["status"] == "invalid"
    assert outcome["error_code"] == code
    with Provenance(tmp_path) as store:
        record = store.get_submission(outcome["submission_id"])
        assert record["request_sha256"] == hash_bytes(raw.encode())
        assert record["status"] == "invalid"
        assert "must-not-be-stored" not in json.dumps(record)
        event_text = str(store.journal.connection.execute("SELECT payload FROM events").fetchall())
        assert "must-not-be-stored" not in event_text


def test_oversized_envelope_is_a_preflight_boundary(tmp_path):
    with pytest.raises(ProvenanceError):
        run_submission(tmp_path, "x" * (MAX_REQUEST_BYTES + 1))
    with Provenance(tmp_path) as store:
        assert store.list_submissions() == []


def test_dict_is_frozen_once_before_begin(tmp_path, dataset, monkeypatch):
    supplied = request(dataset)
    original_begin = Provenance.begin

    def mutate_after_begin(store, kind, frozen):
        result = original_begin(store, kind, frozen)
        supplied["specification"]["lookback"] = 500
        return result

    monkeypatch.setattr(Provenance, "begin", mutate_after_begin)
    outcome = run_submission(tmp_path, supplied)
    assert outcome["status"] == "success"
    artifact = read(tmp_path, outcome["artifact_sha256"])
    assert artifact["frozen_request"]["strategy"]["lookback"] == 2


def test_different_lookbacks_have_identical_requested_evaluation_and_benchmark(tmp_path, dataset):
    results = [run_submission(tmp_path, request(dataset, lookback)) for lookback in (2, 4)]
    assert all(result["status"] == "success" for result in results), results
    reports = [read(tmp_path, item["artifact_sha256"])["engine_report"] for item in results]
    assert [len(report["warmup_sessions"]) for report in reports] == [2, 4]
    for report in reports:
        assert report["evaluation_start"] == "2024-03-11"
        assert report["evaluation_end"] == "2024-03-15"
        assert report["holdout_status"] == "unprotected_not_implemented"
        assert len(report["strategy"]["daily_equity"]) == 5
    assert reports[0]["benchmark"] == reports[1]["benchmark"]
    assert results[1]["recorded_candidate_count"] == results[1]["recorded_execution_count"] == 2


def test_exact_warmup_is_selected_and_dst_is_preserved(tmp_path, dataset):
    outcome = run_submission(tmp_path, request(dataset, 4))
    report = read(tmp_path, outcome["artifact_sha256"])["engine_report"]
    assert report["warmup_sessions"] == ["2024-03-07", "2024-03-08", "2024-03-09", "2024-03-10"]
    assert report["strategy"]["daily_equity"][0]["timestamp"].endswith("-04:00")


@pytest.mark.parametrize("changes,code", [
    ({"specification": {"lookback": 6}}, "insufficient_common_window_warmup"),
    ({"specification": {"lookback": True}}, "invalid_specification"),
    ({"specification": {"lookback": 2, "invented": 1}}, "invalid_specification"),
    ({"evaluation_start": "2024-03-01"}, "evaluation_window_unavailable"),
    ({"evaluation_end": "2024-03-10"}, "evaluation_window_unavailable"),
    ({"admission_status": "approved"}, "invalid_study_fields"),
])
def test_invalid_study_is_retained_without_compute(tmp_path, dataset, monkeypatch, changes, code):
    monkeypatch.setattr(explorer, "run_backtest", lambda *args, **kwargs: pytest.fail("must not run"))
    outcome = run_submission(tmp_path, request(dataset, **changes))
    assert outcome["status"] == "invalid"
    assert outcome["error_code"] == code
    with Provenance(tmp_path) as store:
        assert store.get_submission(outcome["submission_id"])["status"] == "invalid"
        assert store.journal.connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0


def test_missing_session_rejected_at_registration(tmp_path):
    missing = rows()
    del missing[3]
    result = register_dataset(tmp_path, registration(tmp_path, supplied=missing))
    assert result["status"] == "invalid"
    assert result["error_code"] == "session_coverage_mismatch"


@pytest.mark.parametrize("target", ["source_sha256", "bars_sha256", "manifest"])
def test_corrupt_blob_cannot_pass_identity_verification(tmp_path, dataset, target):
    manifest = read(tmp_path, dataset)
    digest = dataset if target == "manifest" else manifest[target]
    (tmp_path / "data" / "objects" / f"{digest}.bin").write_bytes(b'{"changed":true}')
    outcome = run_submission(tmp_path, request(dataset))
    assert outcome["status"] == "invalid"
    assert outcome["error_code"] == "artifact_or_storage_unavailable"


def test_success_refs_and_source_hashes_identify_actual_bytes(tmp_path, dataset):
    result = run_submission(tmp_path, request(dataset))
    artifact = read(tmp_path, result["artifact_sha256"])
    assert artifact["investment_evidence"] is False
    assert artifact["result_kind"] == "exploratory_result"
    assert artifact["code_identity"]["sources"]["research.py"] == hash_bytes(
        (explorer.Path(explorer.__file__).parent / "research.py").read_bytes())
    with Provenance(tmp_path) as store:
        for digest in result["artifact_refs"]:
            assert hash_bytes(store.read_bytes(digest)) == digest
        assert dataset in result["artifact_refs"]
        assert result["artifact_sha256"] in result["artifact_refs"]
        assert store.journal.verify_events()["count"] > 0


def test_renamed_identical_study_is_retry_not_new_candidate(tmp_path, dataset):
    first = run_submission(tmp_path, request(dataset))
    second = run_submission(tmp_path, request(dataset, study_name="renamed probe"))
    assert first["status"] == second["status"] == "success"
    assert first["attempt_id"] != second["attempt_id"]
    assert first["fingerprint"] == second["fingerprint"]
    assert first["artifact_sha256"] == second["artifact_sha256"]
    assert second["recorded_candidate_count"] == 1
    assert second["recorded_execution_count"] == 2
    assert second["prior_recorded_overlap_count"] == 2


def test_revised_bytes_and_venue_do_not_erase_full_range_exposure(tmp_path, dataset):
    first = run_submission(tmp_path, request(dataset))
    revised = rows()
    revised[-1]["close"] = 18
    revised_market = {**MARKET, "venue": "other-venue"}
    registered = register_dataset(tmp_path, registration(
        tmp_path, supplied=revised, market=revised_market, parent_dataset_sha256=dataset))
    assert registered["status"] == "success"
    second = run_submission(tmp_path, request(registered["manifest_sha256"], study_name="new name"))
    assert second["status"] == "success"
    assert first["fingerprint"] != second["fingerprint"]
    assert second["recorded_candidate_count"] == 2
    records = list_exposures(tmp_path, MARKET, "2024-03-06", "2024-03-06")
    assert len(records) == 4
    assert {row["dataset_sha256"] for row in records} == {dataset, registered["manifest_sha256"]}
    assert all(row["coverage_start"] == "2024-03-06" and row["coverage_end"] == "2024-03-15"
               for row in records)
    assert all(row["prior_exposure"] == "unknown_outside_application" for row in records)


def historical_registration(root):
    source = {"evidence_kind": "historical_market_data", "price_basis": "raw", "bars": rows(),
              "identity": {"symbol": "FIXTURE", "currency": "USD", "session_timezone": "America/New_York"},
              "coverage": {"requested_start": "2024-03-01", "requested_end": "2024-03-31"}}
    return registration(root, supplied=source, evidence_kind="historical_market_data",
                        market={**MARKET, "instrument_id": "us:EXAMPLE"})


def test_historical_data_is_explicitly_inspection_only_and_full_request_range_exposed(tmp_path, monkeypatch):
    result = register_dataset(tmp_path, historical_registration(tmp_path))
    assert result["status"] == "success"
    assert result["admission_status"] == "inspection_only"
    monkeypatch.setattr(explorer, "run_backtest", lambda *args, **kwargs: pytest.fail("must not run"))
    denied = run_submission(tmp_path, request(result["manifest_sha256"]))
    assert denied["status"] == "invalid"
    assert denied["error_code"] == "historical_admission_not_implemented"
    assert "corporate_action_accounting" in denied["admission_gaps"]
    market = {**MARKET, "instrument_id": "us:EXAMPLE"}
    records = list_exposures(tmp_path, market, "2024-03-30", "2024-03-31")
    assert len(records) == 2
    assert all(record["coverage_start"] == "2024-03-01" for record in records)
    assert all(record["coverage_end"] == "2024-03-31" for record in records)


def test_historical_envelope_cannot_be_declared_synthetic(tmp_path):
    req = historical_registration(tmp_path)
    req.update(evidence_kind="synthetic_fixture", market=MARKET)
    outcome = register_dataset(tmp_path, req)
    assert outcome["status"] == "invalid"
    assert outcome["error_code"] == "source_metadata_mismatch"


@pytest.mark.parametrize("metadata", [
    {"price_basis": "all"}, {"identity": {"currency": "EUR"}},
    {"identity": {"symbol": "OTHER"}}, {"identity": {"session_timezone": "UTC"}},
])
def test_conflicting_source_metadata_rejected(tmp_path, metadata):
    source = {"bars": rows(), **metadata}
    outcome = register_dataset(tmp_path, registration(tmp_path, supplied=source))
    assert outcome["error_code"] == "source_metadata_mismatch"


def test_unregistered_manifest_and_unknown_admission_cannot_bypass_gate(tmp_path, dataset):
    manifest = read(tmp_path, dataset)
    manifest["admission_status"] = "approved"
    with Provenance(tmp_path) as store:
        digest = store.put_json(manifest)
    result = run_submission(tmp_path, request(digest))
    assert result["error_code"] == "dataset_not_registered"
    req = registration(tmp_path)
    req["admission_status"] = "approved"
    assert register_dataset(tmp_path, req)["error_code"] == "invalid_registration_fields"


def test_compute_failure_has_registered_attempt_and_terminal_failure(tmp_path, dataset, monkeypatch):
    def failure(*args, **kwargs):
        with Provenance(tmp_path) as store:
            assert store.journal.connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 1
            assert store.journal.connection.execute("SELECT COUNT(*) FROM experiments").fetchone()[0] == 1
        raise RuntimeError("secret exception must not be persisted")

    monkeypatch.setattr(explorer, "run_backtest", failure)
    result = run_submission(tmp_path, request(dataset))
    assert result["status"] == "failed"
    with Provenance(tmp_path) as store:
        row = store.journal.connection.execute("SELECT status,result FROM outcomes").fetchone()
        assert row["status"] == "failed"
        assert "secret" not in row["result"]
        assert store.get_submission(result["submission_id"])["status"] == "failed"


def test_interrupt_leaves_pending_attempt_and_consumed_exposure(tmp_path, dataset, monkeypatch):
    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(explorer, "run_backtest", interrupted)
    with pytest.raises(KeyboardInterrupt):
        run_submission(tmp_path, request(dataset))
    with Provenance(tmp_path) as store:
        assert store.list_submissions(kind="exploratory_study")[0]["status"] == "pending"
        assert store.journal.connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 1
        assert store.journal.connection.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0] == 0
    assert len(list_exposures(tmp_path, MARKET, "2024-03-06", "2024-03-06")) == 2


def test_changed_source_identity_during_execution_rejects_result(tmp_path, dataset, monkeypatch):
    original = explorer._code_identity
    calls = 0

    def changing():
        nonlocal calls
        result = deepcopy(original())
        calls += 1
        result["simulated_change"] = calls
        return result

    monkeypatch.setattr(explorer, "_code_identity", changing)
    result = run_submission(tmp_path, request(dataset))
    assert result["status"] == "invalid"
    assert result["error_code"] == "code_changed_during_execution"
    assert "artifact_sha256" not in result


@pytest.mark.parametrize("table", ["explorer_datasets", "explorer_exposures", "explorer_executions"])
def test_exploration_records_reject_application_update_and_delete(tmp_path, dataset, table):
    run_submission(tmp_path, request(dataset))
    with Provenance(tmp_path) as store:
        for statement in (f"DELETE FROM {table}", f"UPDATE {table} SET rowid=rowid"):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                store.journal.connection.execute(statement)


def test_loaded_helper_identity_changes_when_edited_source_is_reloaded(tmp_path):
    import shutil
    import subprocess
    import sys

    copied = tmp_path / "quanto"
    shutil.copytree(explorer.Path(explorer.__file__).parent, copied, ignore=shutil.ignore_patterns("__pycache__"))
    script = '''
import importlib,json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from quanto import explorer,research
source=Path(research.__file__)
source.write_text(source.read_text().replace("if bars[index].close > entry:\\n        return True", "if bars[index].close > entry:\\n        return False"))
old=explorer._code_identity()
rows=[research.Bar(datetime(2024,1,1,tzinfo=timezone.utc)+timedelta(days=i),"FIXTURE",10+i,11+i,9+i,10+i,100) for i in range(8)]
old_equity=research.run_backtest(rows,research.StrategySpec(2)).strategy.ending_equity
importlib.invalidate_caches()
importlib.reload(research)
importlib.reload(explorer)
new=explorer._code_identity()
rows=[research.Bar(row.timestamp,row.symbol,row.open,row.high,row.low,row.close,row.volume) for row in rows]
new_equity=research.run_backtest(rows,research.StrategySpec(2)).strategy.ending_equity
print(json.dumps({"disk_equal":old["sources"]==new["sources"],"entry_equal":old["entrypoint_bytecode_sha256"]==new["entrypoint_bytecode_sha256"],"helper_equal":old["loaded_engine_code"]["_target"]==new["loaded_engine_code"]["_target"],"old":old_equity,"new":new_equity}))
'''
    result = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, check=True,
                            capture_output=True, text=True)
    observed = json.loads(result.stdout)
    assert observed["disk_equal"] and observed["entry_equal"]
    assert not observed["helper_equal"]
    assert observed["old"] != observed["new"]


@pytest.mark.parametrize("failure_point", ["artifact", "submission_event", "attempt_event"])
def test_publication_failure_cannot_leave_successful_attempt(tmp_path, dataset, monkeypatch, failure_point):
    if failure_point == "artifact":
        original = Provenance.put_json

        def fail_artifact(store, value):
            if value.get("result_kind") == "exploratory_result":
                raise ProvenanceError("fixture publication failure")
            return original(store, value)

        monkeypatch.setattr(Provenance, "put_json", fail_artifact)
    else:
        from quanto.ledger import Journal
        original = Journal._event

        def fail_event(journal, kind, payload, now):
            if failure_point == "submission_event" and kind == "submission_finished" and payload["status"] == "success":
                raise sqlite3.OperationalError("fixture publication failure")
            if failure_point == "attempt_event" and kind == "attempt_finished" and payload["status"] == "success":
                raise sqlite3.OperationalError("fixture publication failure")
            return original(journal, kind, payload, now)

        monkeypatch.setattr(Journal, "_event", fail_event)
    outcome = run_submission(tmp_path, request(dataset))
    assert outcome["status"] == "interrupted"
    assert outcome["error_code"] == "publication_interrupted"
    with Provenance(tmp_path) as store:
        assert store.get_submission(outcome["submission_id"])["status"] == "interrupted"
        outcomes = store.journal.connection.execute("SELECT status FROM outcomes").fetchall()
        assert [row[0] for row in outcomes] == ["failed"]
        assert store.journal.connection.execute("SELECT COUNT(*) FROM provenance_outcomes WHERE status='success'").fetchone()[0] == 1
        assert store.journal.verify_events()["count"] > 0


def test_loaded_helper_defaults_are_part_of_execution_identity(monkeypatch):
    before = explorer._code_identity()
    monkeypatch.setattr(explorer.research_engine._number, "__kwdefaults__", {"positive": True})
    after = explorer._code_identity()
    assert before["sources"] == after["sources"]
    assert before["entrypoint_bytecode_sha256"] == after["entrypoint_bytecode_sha256"]
    assert before["loaded_engine_code"]["_number"] != after["loaded_engine_code"]["_number"]


def test_persistent_terminal_storage_failure_propagates_and_leaves_pending(tmp_path, dataset, monkeypatch):
    from quanto.ledger import Journal
    original = Journal._event

    def failed_event(journal, kind, payload, now):
        if kind == "attempt_finished":
            raise OSError("fixture persistent storage failure")
        return original(journal, kind, payload, now)

    monkeypatch.setattr(Journal, "_event", failed_event)
    with pytest.raises(OSError, match="fixture persistent storage failure"):
        run_submission(tmp_path, request(dataset))
    with Provenance(tmp_path) as store:
        assert store.list_submissions(kind="exploratory_study")[0]["status"] == "pending"
        assert store.journal.connection.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0] == 0
        assert store.journal.verify_events()["count"] > 0

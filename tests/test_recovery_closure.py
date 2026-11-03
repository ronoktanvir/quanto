"""Invented temporary SQLite/object graphs; no actual research or external calls."""
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import uuid

import pytest

from quanto import recovery, recovery_closure as closure
from quanto.provenance import Provenance


def encode(value):
    return recovery._json(value)


def sha(value):
    return recovery._sha(encode(value))


def dataset_document(source, bars):
    return {"schema_version": 1, "kind": "explorer_dataset", "evidence_kind": "synthetic_fixture",
            "source_sha256": source, "bars_sha256": bars,
            "market": {"instrument_id": "synthetic:fixture", "venue": "synthetic",
                       "currency": "USD", "session_timezone": "UTC"},
            "symbol": "SYNTHETIC", "price_basis": "raw", "sessions": ["2024-01-02"],
            "coverage_start": "2024-01-02", "coverage_end": "2024-01-02",
            "exposure_start": "2024-01-02", "exposure_end": "2024-01-02", "bar_count": 1,
            "parent_dataset_sha256": None, "admission_status": "synthetic_only",
            "development_policy": "entire_dataset_development_only",
            "prior_exposure": "unknown_outside_application", "calendar_status": "synthetic_defined",
            "corporate_actions": "not_applicable_synthetic", "timing": "session_level_assumption",
            "rights": "caller_classification_unverified"}


def bar_document():
    return {"schema_version": 1, "bars": [{"timestamp": "2024-01-02T16:00:00+00:00",
            "symbol": "SYNTHETIC", "open": 1.0, "high": 1.0, "low": 1.0,
            "close": 1.0, "volume": 0.0}]}


def source_store(tmp_path):
    source = tmp_path / "source"
    source.mkdir(mode=0o700)
    return source


def make_dataset(store, mutate=None):
    source = store.put_json({"bars": [], "kind": "untrusted_source", "reference": "f" * 64})
    bars = store.put_json(bar_document())
    document = dataset_document(source, bars)
    if mutate:
        mutate(document)
    digest = store.put_json(document)
    submission = store.begin("dataset_registration", {"data_sha256": source})
    store.finish(submission, "success", {"manifest_sha256": digest, "artifact_refs": [digest]})
    return {"dataset": digest, "bars": bars, "source": source, "document": document}


def captured(source, tmp_path):
    snapshot = tmp_path / "snapshot"
    receipt = recovery.capture_research_snapshot(source, snapshot)
    return snapshot, receipt


def inspect(snapshot, receipt, **kwargs):
    return closure.inspect_research_closure(snapshot, expected_manifest_sha256=receipt["manifest_sha256"],
                                           expected_event_head=receipt["event_head"], **kwargs)


def reasons(report):
    return {item["reason"] for item in report["unsupported"]}


def nodes(report, role):
    return [node for node in report["nodes"] if node["role"] == role]


def full_graph(store):
    found = make_dataset(store)
    admission = store.put_json({"schema_version": 1, "kind": "historical_admission", "synthetic": True})
    policy = store.put_json({"schema_version": 1, "kind": "policy_revision", "synthetic": True})
    requests = [{"dataset_sha256": found["dataset"], "admission_sha256": admission,
                 "study_name": "fixture", "evaluation_start": "2024-01-02", "evaluation_end": "2024-01-02",
                 "specification": {"lookback": 1, "cost_bps": cost}} for cost in (0, 10, 25)]
    request = {"members": requests}
    suite_id = store.begin("study_suite_registration", request)
    suite = store.put_json({"schema_version": 1, "kind": "study_suite", "submission_id": suite_id,
        "registration_request_sha256": store.put_json(request), "policy_revision_sha256": policy,
        "members": [{"cost_bps": item["specification"]["cost_bps"], "request": item,
                     "request_sha256": sha(item)} for item in requests], "artifact_refs": [admission, policy]})
    store.finish(suite_id, "success", {"suite_sha256": suite, "artifact_refs": [suite]})
    run_request = {"suite_sha256": suite}
    run_id = store.begin("study_suite_run", run_request)
    requests = [{**item, "suite_sha256": suite} for item in requests]
    members = [{"cost_bps": item["specification"]["cost_bps"], "request": item,
                "request_sha256": sha(item)} for item in requests]
    roster = store.put_json({"schema_version": 1, "kind": "study_suite_run_roster", "submission_id": run_id,
                            "suite_sha256": suite, "run_request_sha256": store.put_json(run_request), "members": members})
    result = store.put_json({"schema_version": 1, "result_kind": "exploratory_result",
        "evidence_kind": "synthetic_fixture", "investment_evidence": False, "dataset_sha256": found["dataset"],
        "frozen_request": {"strategy": {"lookback": 1}, "purpose": "exploratory"},
        "code_identity": {"sources": {"invented.py": "a" * 64}, "dependency_lock_sha256": "b" * 64},
        "development_policy": "entire_dataset_development_only", "prior_exposure": "unknown_outside_application",
        "engine_report": {"synthetic": True}, "admission_sha256": admission,
        "admission_limitations": ["synthetic fixture"], "admission_evidence": {"fixture": True}, "study_suite": None})
    child = store.begin("exploratory_study", requests[0])
    store.finish(child, "success", {"artifact_sha256": result, "artifact_refs": [result]})
    summary = store.put_json({"schema_version": 1, "kind": "study_suite_summary", "submission_id": run_id,
        "suite_sha256": suite, "roster_sha256": roster, "complete": False, "all_success": False,
        "members": [{**item, "outcome": {"status": "success", "submission_id": child, "artifact_sha256": result}}
                    if index == 0 else {**item, "outcome": {"status": "pending", "phase": "not_started"}}
                    for index, item in enumerate(members)], "artifact_refs": [suite, roster, result]})
    store.finish(run_id, "interrupted", {"suite_sha256": suite, "summary_sha256": summary, "artifact_refs": [summary]})
    return {**found, "suite": suite, "roster": roster, "summary": summary, "result": result,
            "inline_requests": [sha(item) for item in requests]}


def test_supported_graph_preserves_inline_identities_and_keeps_full_claims_false(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        graph = full_graph(store)
        assert all(not (source / "data/objects" / (digest + ".bin")).exists() for digest in graph["inline_requests"])
    snapshot, receipt = captured(source, tmp_path)
    before = {str(p.relative_to(snapshot)): p.read_bytes() for p in snapshot.rglob("*") if p.is_file()}
    report = inspect(snapshot, receipt)
    for role in ("dataset", "bars", "suite", "roster", "summary", "result"):
        assert nodes(report, role)[0]["status"] == "supported_structure_checked"
    assert {edge["digest"] for edge in report["edges"] if edge["edge_type"] == "inline_identity"} >= set(graph["inline_requests"])
    assert "historical_source_environment_required" in reasons(report)
    assert all(report[field] is False for field in closure.FLAGS)
    assert report["status"] == "incomplete"
    assert report == inspect(snapshot, receipt)
    assert before == {str(p.relative_to(snapshot)): p.read_bytes() for p in snapshot.rglob("*") if p.is_file()}
    public = closure.public_projection(report)
    assert not {"nodes", "edges", "unsupported", "omissions"} & public.keys()
    assert "synthetic" not in json.dumps(public) and "invented.py" not in json.dumps(public)


@pytest.mark.parametrize("mutate,reason", [
    (lambda d: d.update(schema_version=2), "unsupported_schema_version"),
    (lambda d: d.update(kind="future_dataset"), "unsupported_document_kind"),
])
def test_unknown_versions_and_kinds_are_incomplete_not_malformed(tmp_path, mutate, reason):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        make_dataset(store, mutate)
    report = inspect(*captured(source, tmp_path))
    assert reason in reasons(report)
    assert nodes(report, "dataset")[0]["status"] == "unsupported"


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(schema_version=True), lambda d: d.update(sessions="not-a-list"),
    lambda d: d.update(extra="unknown-field"), lambda d: d.pop("rights"),
    lambda d: d.update(bar_count=-1), lambda d: d.update(kind="study_suite"),
    lambda d: d.update(market={"unrecognized": "market"}),
])
def test_malformed_supported_dataset_refuses(tmp_path, mutate):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        make_dataset(store, mutate)
    with pytest.raises(closure.ClosureError):
        inspect(*captured(source, tmp_path))


def test_missing_nested_dependency_is_not_hidden_by_byte_inventory_success(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        make_dataset(store, lambda d: d.update(bars_sha256="f" * 64))
    snapshot, receipt = captured(source, tmp_path)
    with pytest.raises(closure.ClosureError, match="^required_object_missing$"):
        inspect(snapshot, receipt)


@pytest.mark.parametrize("purged", [False, True])
def test_nested_tombstone_retains_unavailability_without_copying_or_resurrecting(tmp_path, purged):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        graph = make_dataset(store)
        store.tombstone(graph["bars"], "operator_requested")
        if purged:
            store.purge(graph["bars"], "operator_requested")
    snapshot, receipt = captured(source, tmp_path)
    assert not (snapshot / "objects" / (graph["bars"] + ".bin")).exists()
    report = inspect(snapshot, receipt)
    assert "required_tombstoned_object" in reasons(report)
    assert report["counts"]["tombstoned_edges"] >= 1


def test_opaque_visit_does_not_suppress_later_dataset_visit(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        raw = store.put_json({"fake_sha256": "e" * 64, "kind": "study_suite", "schema_version": 1})
        bars = store.put_json(bar_document())
        dataset = store.put_json(dataset_document(raw, bars))
        store.journal.append_event("acquisition_page_received", {"raw_sha256": dataset})
        store.journal.append_event("explorer_dataset_registered", {"manifest_sha256": dataset})
        store.journal.append_event("acquisition_page_received", {"raw_sha256": raw})
    report = inspect(*captured(source, tmp_path))
    assert {node["role"] for node in report["nodes"] if node["digest"] == dataset} == {"opaque_provider_page", "dataset"}
    assert nodes(report, "dataset")[0]["status"] == "supported_structure_checked"
    assert not any(edge["digest"] == "e" * 64 for edge in report["edges"])


@pytest.mark.parametrize("event", ["workflow_broker_packet_bound", "workflow_broker_failure_basis_bound"])
def test_pending_broker_binding_roots_require_bytes_even_without_terminal_stage(tmp_path, event):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        value = store.put_json({"synthetic": "bound evidence"})
        payload = {field: value for field in closure.EVENT_REFS[event]}
        if "failure_basis_sha256" in payload:
            payload["failure_basis_sha256"] = None
        payload["configuration_sha256"] = "f" * 64
        store.journal.append_event(event, payload)
    with pytest.raises(closure.ClosureError, match="^required_object_missing$"):
        inspect(*captured(source, tmp_path))


def test_historical_availability_in_unsupported_basis_does_not_invent_current_roots(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        basis = store.put_json({"kind": "research_failure_basis", "schema_version": 1,
            "original": {"request_availability": {"f" * 64: "unavailable"}},
            "reference_availability": {"e" * 64: "unavailable"}})
        config = store.put_json({"kind": "untrusted_configuration"})
        store.journal.append_event("workflow_broker_failure_basis_bound", {"basis_sha256": basis, "configuration_sha256": config})
    report = inspect(*captured(source, tmp_path))
    assert nodes(report, "failure_basis")[0]["status"] == "unsupported"
    assert not {"e" * 64, "f" * 64} & {edge["digest"] for edge in report["edges"]}


def packet_fixture(store, *, producer, role="director", modern=False, row=True,
                   workflow=closure.PACKET_WORKFLOW_SOURCE, mutate=None, wrong_code=False):
    identity = {"sources": {"research_broker.py": producer, "research_workflow.py": workflow},
                "python": "3.11.9", "implementation": "CPython"}
    configuration = store.put_json({"code_identity": identity, "synthetic": True})
    submission = store.begin("research_broker", {"fixture": True})
    if row:
        store.journal.connection.execute("CREATE TABLE research_broker_runs (submission_id TEXT PRIMARY KEY, "
            "run_key TEXT, workflow_run_id TEXT, configuration_sha256 TEXT, code_sha256 TEXT)")
        store.journal.connection.execute("INSERT INTO research_broker_runs VALUES (?,?,?,?,?)",
            (submission, "fixture", "fixture-workflow", configuration, "f" * 64 if wrong_code else sha(identity)))
    value = {"parent_submission_id": submission, "assignment_id": "fixture-assignment", "role": role,
             "fence": 1, "request_id": "fixture-request", "configuration_sha256": configuration,
             "packet_sha256": store.put_json({"fixture": "packet"}),
             "verification_sha256": store.put_json({"fixture": "verification"})}
    if modern:
        value.update(failure_context_sha256=store.put_json({"fixture": "context"}),
                     failure_basis_sha256=None if role == "director" else store.put_json({"fixture": "basis"}))
    if mutate:
        mutate(value)
    store.journal.append_event("workflow_broker_packet_bound", value)
    return value


@pytest.mark.parametrize("producer", [key for key, value in closure.PACKET_PRODUCERS.items() if value == "legacy_038"])
def test_bound_historical_packet_uses_recorded_producer_without_modern_evidence(tmp_path, producer):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        payload = packet_fixture(store, producer=producer)
    report = inspect(*captured(source, tmp_path))
    assert "legacy_packet_missing_modern_failure_evidence" in reasons(report)
    assert "packet_profile_origin_unresolved" not in reasons(report)
    assert {payload[field] for field in closure.PACKET_BASE} <= {edge["digest"] for edge in report["edges"]}
    assert all(report[field] is False for field in closure.FLAGS)


CURRENT_PACKET_PRODUCER = next(key for key, value in closure.PACKET_PRODUCERS.items() if value == "current_9ed")


@pytest.mark.parametrize("role", ["director", "hypothesis", "engineer", "data_critic", "statistical_critic", "quality", "scope"])
def test_bound_current_packet_retains_every_reference_and_narrow_nullable_condition(tmp_path, role):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        payload = packet_fixture(store, producer=CURRENT_PACKET_PRODUCER, modern=True, role=role)
    report = inspect(*captured(source, tmp_path))
    assert "legacy_packet_missing_modern_failure_evidence" not in reasons(report)
    assert "packet_profile_origin_unresolved" not in reasons(report)
    assert "event_binding_semantics_not_checked" in reasons(report)
    expected = {payload[field] for field in closure.PACKET_BASE | closure.PACKET_FAILURE if payload[field] is not None}
    assert expected <= {edge["digest"] for edge in report["edges"]}
    assert report["full_recovery_accepted"] is False


@pytest.mark.parametrize("mutate", [
    lambda d: (d.pop("failure_context_sha256"), d.pop("failure_basis_sha256")),
    lambda d: d.pop("failure_context_sha256"),
    lambda d: d.pop("failure_basis_sha256"),
    lambda d: d.pop("verification_sha256"),
    lambda d: d.update(failure_context_sha256=None),
    lambda d: d.update(failure_basis_sha256=d["verification_sha256"]),
    lambda d: d.update(role="engineer"),
    lambda d: d.update(fence=True),
    lambda d: d.update(extra_sha256="f" * 64),
])
def test_known_current_packet_cannot_downgrade_or_relax_required_shape(tmp_path, mutate):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        packet_fixture(store, producer=CURRENT_PACKET_PRODUCER, modern=True, mutate=mutate)
    with pytest.raises(closure.ClosureError):
        inspect(*captured(source, tmp_path))


@pytest.mark.parametrize("mutate", [lambda d: d.pop("verification_sha256"),
    lambda d: d.update(failure_context_sha256=d["packet_sha256"], failure_basis_sha256=None)])
def test_known_legacy_packet_must_match_its_exact_reference_profile(tmp_path, mutate):
    source = source_store(tmp_path)
    producer = next(key for key, value in closure.PACKET_PRODUCERS.items() if value == "legacy_038")
    with Provenance(source) as store:
        packet_fixture(store, producer=producer, mutate=mutate)
    with pytest.raises(closure.ClosureError):
        inspect(*captured(source, tmp_path))


@pytest.mark.parametrize("options", [{"producer": "e" * 64},
    {"producer": CURRENT_PACKET_PRODUCER, "row": False},
    {"producer": CURRENT_PACKET_PRODUCER, "workflow": "e" * 64}])
def test_unknown_packet_origin_never_becomes_verified_legacy_from_keys(tmp_path, options):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        packet_fixture(store, **options)
    report = inspect(*captured(source, tmp_path))
    assert "packet_profile_origin_unresolved" in reasons(report)
    assert "unbound_packet_missing_modern_failure_evidence" in reasons(report)
    assert "legacy_packet_missing_modern_failure_evidence" not in reasons(report)
    assert report["full_recovery_accepted"] is False


def test_packet_configuration_identity_must_match_registered_code_hash(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        packet_fixture(store, producer=CURRENT_PACKET_PRODUCER, modern=True, wrong_code=True)
    with pytest.raises(closure.ClosureError, match="^event_producer_binding_mismatch$"):
        inspect(*captured(source, tmp_path))


@pytest.mark.parametrize("producer,expected", [
    (key, "refused" if profile == "legacy_038" else "current")
    for key, profile in closure.PACKET_PRODUCERS.items()
] + [("e" * 64, "unresolved")])
def test_failure_basis_event_requires_its_own_compatible_recorded_producer(tmp_path, producer, expected):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        packet = packet_fixture(store, producer=producer, modern=expected == "current")
        event = {field: packet[field] for field in
                 ("parent_submission_id", "assignment_id", "request_id", "fence", "configuration_sha256")}
        event["basis_sha256"] = store.put_json({"synthetic": "basis"})
        store.journal.append_event("workflow_broker_failure_basis_bound", event)
    if expected == "refused":
        with pytest.raises(closure.ClosureError, match="^event_producer_binding_mismatch$"):
            inspect(*captured(source, tmp_path))
    else:
        report = inspect(*captured(source, tmp_path))
        assert ("failure_basis_profile_origin_unresolved" in reasons(report)) == (expected == "unresolved")
        assert event["basis_sha256"] in {edge["digest"] for edge in report["edges"]}
        assert report["full_recovery_accepted"] is False


def test_current_failure_basis_event_requires_complete_writer_shape(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        packet = packet_fixture(store, producer=CURRENT_PACKET_PRODUCER, modern=True)
        event = {field: packet[field] for field in
                 ("parent_submission_id", "assignment_id", "fence", "configuration_sha256")}
        event["basis_sha256"] = store.put_json({"synthetic": "basis"})
        store.journal.append_event("workflow_broker_failure_basis_bound", event)
    with pytest.raises(closure.ClosureError, match="^malformed_supported_profile$"):
        inspect(*captured(source, tmp_path))


def test_unknown_schema_event_submission_and_orphan_are_explicit(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        store.put_json({"kind": "explorer_dataset", "schema_version": 1, "not_really_a_dataset": True})
        store.begin("unknown_submission", {})
        store.journal.append_event("unknown_event", {"must_not_fetch": "f" * 64})
    with sqlite3.connect(source / "runtime/research.sqlite") as db:
        db.execute("CREATE TABLE unknown_table(value TEXT)")
        db.execute("INSERT INTO unknown_table VALUES ('synthetic')")
    report = inspect(*captured(source, tmp_path))
    assert {"unsupported_table_schema", "unsupported_event_profile", "unsupported_submission_kind", "unclassified_orphan_inventory"} <= reasons(report)
    assert not nodes(report, "dataset")


def test_private_reply_is_not_dispatched_from_its_json_like_text(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        raw = store.put_json({"reply": '{"kind":"explorer_dataset","schema_version":1}', "body_sha256": "e" * 64})
        store.journal.connection.execute("CREATE TABLE research_private_responses(request_id TEXT PRIMARY KEY,artifact_sha256 TEXT NOT NULL,created_at TEXT NOT NULL)")
        store.journal.connection.execute("INSERT INTO research_private_responses VALUES (?,?,?)", ("fixture", raw, "2026-01-01"))
    report = inspect(*captured(source, tmp_path))
    assert nodes(report, "private_model_response")[0]["status"] == "unsupported"
    assert not nodes(report, "dataset")


def test_no_constructors_current_validators_or_replay_during_inspection(tmp_path, monkeypatch):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        full_graph(store)
    snapshot, receipt = captured(source, tmp_path)
    from quanto import ledger, explorer, study_suite, admission, research_failure_context, research, event_engine
    def forbidden(*_args, **_kwargs):
        pytest.fail("effectful or current-domain validation called")
    for owner, names in [(Provenance, ["__init__"]), (ledger.Journal, ["__init__"]),
        (explorer, ["_code_identity", "run_submission"]), (study_suite, ["_verified", "run_suite", "inspect_run"]),
        (admission, ["validate_admission"]), (research_failure_context, ["_identities", "revalidate_failure_context"]),
        (research, ["run_backtest"]), (event_engine, ["run_event_backtest"])]:
        for name in names:
            monkeypatch.setattr(owner, name, forbidden)
    inspect(snapshot, receipt)


@pytest.mark.parametrize("field,value", [("edges", 1), ("nodes", 1), ("json_items", 1), ("depth", 1), ("seconds", 0.000001)])
def test_limits_refuse_bounded_work(tmp_path, field, value):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        full_graph(store)
    with pytest.raises(closure.ClosureError):
        inspect(*captured(source, tmp_path), limits=replace(closure.ClosureLimits(), **{field: value}))


@pytest.mark.parametrize("checkpoint", ["manifest", "head"])
def test_expected_checkpoint_required_and_mismatch_refuses(tmp_path, checkpoint):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        make_dataset(store)
    snapshot, receipt = captured(source, tmp_path)
    receipt["manifest_sha256" if checkpoint == "manifest" else "event_head"] = "e" * 64
    with pytest.raises(closure.ClosureError, match="snapshot_verification_failed"):
        inspect(snapshot, receipt)


def test_change_after_first_verification_refuses(tmp_path, monkeypatch):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        graph = make_dataset(store)
    snapshot, receipt = captured(source, tmp_path)
    original = closure._Reader.walk
    def mutate_after_read(reader):
        original(reader)
        (snapshot / "objects" / (graph["source"] + ".bin")).write_bytes(b"changed")
    monkeypatch.setattr(closure._Reader, "walk", mutate_after_read)
    with pytest.raises(closure.ClosureError, match="snapshot_verification_failed"):
        inspect(snapshot, receipt)


def test_public_projection_rejects_claim_promotion(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        make_dataset(store)
    report = inspect(*captured(source, tmp_path))
    report["full_recovery_accepted"] = True
    with pytest.raises(closure.ClosureError, match="invalid_report"):
        closure.public_projection(report)


def test_launch_only_request_digest_never_promises_a_file(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        store.journal.connection.execute("CREATE TABLE study_suite_launches(run_id TEXT,cost_bps INTEGER,request_sha256 TEXT)")
        store.journal.connection.execute("INSERT INTO study_suite_launches VALUES (?,?,?)", ("fixture", 0, "d" * 64))
    report = inspect(*captured(source, tmp_path))
    edge = next(edge for edge in report["edges"] if edge["parent"].startswith("study_suite_launches"))
    assert edge["edge_type"] == "inline_identity" and edge["availability"] == "identity_only"
    assert not report["nodes"]


def test_wrong_inline_member_hash_refuses_without_requiring_hash_object(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        graph = full_graph(store)
        document = store.read_json(graph["suite"])
        document["members"][0]["request_sha256"] = "e" * 64
        malformed = store.put_json(document)
        registration = store.begin("study_suite_registration", {})
        store.finish(registration, "success", {"suite_sha256": malformed, "artifact_refs": [malformed]})
    with pytest.raises(closure.ClosureError, match="^inline_identity_mismatch$"):
        inspect(*captured(source, tmp_path))


def test_duplicate_json_keys_in_supported_object_refuse(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        malformed = store.put_bytes(b'{"schema_version":1,"schema_version":1,"kind":"explorer_dataset"}')
        registration = store.begin("dataset_registration", {})
        store.finish(registration, "success", {"manifest_sha256": malformed, "artifact_refs": [malformed]})
    with pytest.raises(closure.ClosureError):
        inspect(*captured(source, tmp_path))


def test_failed_partial_raw_page_and_unknown_request_are_preserved_as_separate_roles(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        page = store.put_bytes(b'not JSON, synthetic failed provider body')
        request = store.put_json({"url": "https://example.invalid/never-fetch", "source_sha256": "e" * 64})
        store.journal.append_event("acquisition_request_prepared", {"request_sha256": request})
        store.journal.append_event("acquisition_page_received", {"raw_sha256": page})
        store.begin("alpaca_bars", {"fixture": True})
    report = inspect(*captured(source, tmp_path))
    assert nodes(report, "opaque_provider_page")[0]["status"] == "opaque_leaf"
    assert nodes(report, "acquisition_request")[0]["status"] == "unsupported"
    assert not any(edge["digest"] == "e" * 64 for edge in report["edges"])


@pytest.mark.parametrize("value", [["synthetic list"], "synthetic string", 1])
def test_generic_ledger_results_and_findings_can_be_non_objects(tmp_path, value):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        journal = store.journal
        experiment = journal.register_experiment({}, {}, {}, "synthetic_fixture")
        attempt = journal.start_attempt(experiment)
        journal.finish_attempt(attempt, "failed", value)
        journal.record_review("fixture", "reviewer", "producer", "d" * 64, "incomplete", value)
    report = inspect(*captured(source, tmp_path))
    assert "unsupported_outcome_origin" in reasons(report)
    assert report["counts"]["supported_nodes"] == 0
    assert report["supported_profiles_verified"] is False
    assert closure.public_projection(report)["supported_profiles_verified"] is False


def test_report_does_not_depend_on_unspecified_sqlite_scan_order(tmp_path, monkeypatch):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        full_graph(store)
    snapshot, receipt = captured(source, tmp_path)
    expected = inspect(snapshot, receipt)
    original = recovery._connect
    class ReversedScans:
        def __init__(self, connection):
            self.connection = connection
        def __getattr__(self, name):
            return getattr(self.connection, name)
        def execute(self, statement, *args):
            cursor = self.connection.execute(statement, *args)
            if statement.startswith('SELECT * FROM "'):
                return iter(reversed(cursor.fetchall()))
            return cursor
    monkeypatch.setattr(recovery, "_connect", lambda *args, **kwargs: ReversedScans(original(*args, **kwargs)))
    observed = inspect(snapshot, receipt)
    # Changed instrumentation has its own loaded dependency identity; the
    # structural findings and raw-source identities remain scan-independent.
    assert observed.pop("recovery_loaded_sha256") != expected.pop("recovery_loaded_sha256")
    assert observed == expected


@pytest.mark.parametrize("outcome,findings", [
    ({"artifact_sha256": "ordinary note"}, {"report_sha256": 7}),
    ({"artifact_sha256": "e" * 64}, {"report_sha256": "f" * 64}),
])
def test_generic_dictionary_key_spelling_never_selects_file_references(tmp_path, outcome, findings):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        journal = store.journal
        experiment = journal.register_experiment({}, {}, {}, "synthetic_fixture")
        attempt = journal.start_attempt(experiment)
        journal.finish_attempt(attempt, "failed", outcome)
        journal.record_review("generic", "reviewer", "producer", "d" * 64, "incomplete", findings)
    report = inspect(*captured(source, tmp_path))
    assert {"unsupported_outcome_origin", "unsupported_review_record"} <= reasons(report)
    assert len(report["edges"]) == 1
    edge = report["edges"][0]
    assert edge["digest"] == "d" * 64 and edge["edge_type"] == "inline_identity"
    assert edge["role"] == "recorded_review_identity"


def parent_chain(store, count):
    raw, bars = store.put_json({"synthetic": True}), store.put_json(bar_document())
    parent = None
    for _ in range(count):
        document = dataset_document(raw, bars)
        document["parent_dataset_sha256"] = parent
        parent = store.put_json(document)
    submission = store.begin("dataset_registration", {})
    store.finish(submission, "success", {"manifest_sha256": parent, "artifact_refs": [parent]})


def test_graph_hops_bound_is_separate_from_shallow_json_nesting(tmp_path):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        parent_chain(store, 9)
    snapshot, receipt = captured(source, tmp_path)
    with pytest.raises(closure.ClosureError, match="^closure_graph_hops_limit$"):
        inspect(snapshot, receipt, limits=replace(closure.ClosureLimits(), depth=4, graph_hops=4))
    report = inspect(snapshot, receipt, limits=replace(closure.ClosureLimits(), depth=4, graph_hops=8))
    assert max(node["graph_hops"] for node in nodes(report, "dataset")) == 8
    assert len(nodes(report, "bars")) == 1
    assert nodes(report, "bars")[0]["graph_hops"] == 1


def module_copy(tmp_path, monkeypatch, *, dependency=False):
    def load(name, path, raw):
        path.write_bytes(raw)
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
        return module
    suffix = uuid.uuid4().hex
    raw = Path(closure.__file__).read_bytes()
    dependency_path = None
    if dependency:
        name = "synthetic_recovery_" + suffix
        dependency_path = tmp_path / "synthetic_recovery.py"
        load(name, dependency_path, Path(recovery.__file__).read_bytes())
        raw = raw.replace(b"from quanto import recovery", ("import " + name + " as recovery").encode())
    path = tmp_path / "synthetic_closure.py"
    return load("synthetic_closure_" + suffix, path, raw), path, dependency_path


@pytest.mark.parametrize("dependency", [False, True])
def test_disk_source_changed_after_import_cannot_identify_old_loaded_code(tmp_path, monkeypatch, dependency):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        make_dataset(store)
    snapshot, receipt = captured(source, tmp_path)
    module, path, dependency_path = module_copy(tmp_path, monkeypatch, dependency=dependency)
    target = dependency_path if dependency else path
    raw = target.read_bytes()
    target.write_bytes(raw.replace(b'research_state_offline_v1' if dependency else b'research_closure_subset_v1',
                                 b'unloaded_replacement_v99'))
    assert module.PROFILE == "research_closure_subset_v1"
    with pytest.raises(module.ClosureError, match="^implementation_source_changed$"):
        module.inspect_research_closure(snapshot, expected_manifest_sha256=receipt["manifest_sha256"])


def test_loaded_constants_and_frozen_defaults_have_separate_identities(monkeypatch):
    original = closure._implementation_identity()
    with monkeypatch.context() as patch:
        patch.setattr(closure, "PROFILE", "synthetic_changed_constant")
        changed = closure._implementation_identity()
    assert changed["inspector_source_sha256"] == original["inspector_source_sha256"]
    assert changed["inspector_loaded_sha256"] != original["inspector_loaded_sha256"]
    with monkeypatch.context() as patch:
        defaults = {**closure.inspect_research_closure.__kwdefaults__,
                    "limits": replace(closure.ClosureLimits(), graph_hops=4)}
        patch.setattr(closure.inspect_research_closure, "__kwdefaults__", defaults)
        changed = closure._implementation_identity()
    assert changed["inspector_loaded_sha256"] != original["inspector_loaded_sha256"]
    assert changed["recovery_loaded_sha256"] == original["recovery_loaded_sha256"]


def test_loaded_constant_change_during_inspection_refuses(tmp_path, monkeypatch):
    source = source_store(tmp_path)
    with Provenance(source) as store:
        graph = make_dataset(store)
    snapshot, receipt = captured(source, tmp_path)
    import os
    original = os.open
    observed = 0
    def observe(path, *args, **kwargs):
        nonlocal observed
        if Path(path) == snapshot / "objects" / (graph["dataset"] + ".bin"):
            observed += 1
            if observed == 2:
                monkeypatch.setattr(closure, "PROFILE", "synthetic_during_inspection")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(os, "open", observe)
    with pytest.raises(closure.ClosureError, match="^loaded_implementation_changed$"):
        inspect(snapshot, receipt)

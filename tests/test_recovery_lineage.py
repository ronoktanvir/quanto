"""Invented raw SQLite/object fixtures; no domain writers or financial replay."""
from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import pytest

from quanto import recovery, recovery_closure as closure, recovery_lineage as lineage

STAMP = "2024-07-01T12:00:00+00:00"
DAY = "2024-06-10"
HASH = "a" * 64


def encoded(value):
    return recovery._json(value)


def hashed(value):
    return recovery._sha(encoded(value))


class RawStore:
    """Independently serialize the documented three-table registration journal."""
    def __init__(self, tmp_path):
        self.base, self.root = tmp_path, tmp_path / "invented-source"
        for part in (self.root, self.root / "runtime", self.root / "data", self.root / "data/objects"):
            part.mkdir(mode=0o700)
        self.db = sqlite3.connect(self.root / "runtime/research.sqlite")
        self.db.execute("CREATE TABLE events(id INTEGER,occurred_at TEXT,kind TEXT,payload TEXT,previous_hash TEXT,event_hash TEXT)")
        self.db.execute("CREATE TABLE provenance_submissions(submission_id TEXT,kind TEXT,request_sha256 TEXT,request_bytes INTEGER,request_encoding TEXT,started_at TEXT)")
        self.db.execute("CREATE TABLE provenance_outcomes(submission_id TEXT,status TEXT,details TEXT,finished_at TEXT)")
        self.number, self.head = 0, "0" * 64
        self.submissions, self.finished, self.starts, self.finishes = {}, {}, {}, {}

    def put(self, value):
        raw = value if type(value) is bytes else encoded(value)
        ref = recovery._sha(raw)
        path = self.root / "data/objects" / (ref + ".bin")
        path.write_bytes(raw)
        path.chmod(0o600)
        return ref

    def event(self, kind, payload):
        self.number += 1
        digest = hashed({"id": self.number, "occurred_at": STAMP, "kind": kind, "payload": payload, "previous_hash": self.head})
        self.db.execute("INSERT INTO events VALUES(?,?,?,?,?,?)", (self.number, STAMP, kind, encoded(payload).decode(), self.head, digest))
        self.head = digest
        return self.number

    def begin(self, kind, request, *, retain=False):
        raw = request if type(request) is bytes else encoded(request)
        sid = f"{len(self.submissions) + 1:032x}"
        value = {"submission_id": sid, "kind": kind, "request_sha256": recovery._sha(raw), "request_bytes": len(raw), "request_encoding": "utf8_text"}
        self.db.execute("INSERT INTO provenance_submissions VALUES(?,?,?,?,?,?)", (*value.values(), STAMP))
        self.submissions[sid] = value
        self.starts[sid] = self.event("submission_started", value)
        if retain:
            self.put(raw)
        return sid

    def finish(self, sid, status, details):
        self.db.execute("INSERT INTO provenance_outcomes VALUES(?,?,?,?)", (sid, status, encoded(details).decode(), STAMP))
        self.finished[sid] = {"status": status, "details": details}
        self.finishes[sid] = self.event("submission_finished", {"submission_id": sid, "status": status, "details": details})

    def inspect(self, *, limits=closure.ClosureLimits()):
        self.db.commit()
        (self.root / "runtime/research.sqlite").chmod(0o600)
        destination = self.base / f"snapshot-{len(list(self.base.glob('snapshot-*')))}"
        receipt = recovery.capture_research_snapshot(self.root, destination)
        before = {str(p.relative_to(destination)): p.read_bytes() for p in destination.rglob("*") if p.is_file()}
        report = closure.inspect_research_closure(destination, expected_manifest_sha256=receipt["manifest_sha256"], limits=limits)
        assert before == {str(p.relative_to(destination)): p.read_bytes() for p in destination.rglob("*") if p.is_file()}
        assert all(report[key] is False for key in closure.FLAGS)
        assert report["status"] == "incomplete"
        return report


@pytest.fixture
def store(tmp_path):
    value = RawStore(tmp_path)
    yield value
    value.db.close()


def reasons(report):
    return {item["reason"] for item in report["unsupported"]}


def checked(report, ref, role):
    return any(n["digest"] == ref and n["role"] == role and n["status"] == "supported_structure_checked" for n in report["nodes"])


def request_url(kind, request, token=None):
    if kind == "calendar":
        return "https://paper-api.alpaca.markets/v2/calendar?" + urlencode(request)
    if kind == "actions":
        values = {"symbols": request["symbol"], **{k: request[k] for k in ("start", "end", "region", "data_quality", "sort", "limit")}}
        route = "https://data.alpaca.markets/v1/corporate-actions?"
    else:
        zone = ZoneInfo("America/New_York")
        end = datetime.combine(date.fromisoformat(request["end"]) + timedelta(days=1), time(), zone) - timedelta(microseconds=1)
        values = {k: request[k] for k in ("timeframe", "feed", "currency", "asof", "adjustment")}
        values.update(start=datetime.combine(date.fromisoformat(request["start"]), time(), zone).astimezone(timezone.utc).isoformat(),
                      end=end.astimezone(timezone.utc).isoformat(), limit=1000, sort="asc")
        route = "https://data.alpaca.markets/v2/stocks/FAKE/bars?"
    if token:
        values["page_token"] = token
    return route + urlencode(values)


def acquisition(store, kind="bars", *, source=None, failure=None, pending=False, null_page=False,
                missing_event=False, mutate_receipt=None, mutate_prepared=None, mutate_normalized=None,
                original=None, retain_original=True, records=None):
    request = {"start": DAY, "end": DAY}
    if kind == "bars":
        request.update(symbol="FAKE", adjustment="raw", timeframe="1Day", feed="sip", currency="USD", asof="-")
    elif kind == "actions":
        request.update(symbol="FAKE", region="us", data_quality="all", sort="asc", limit=1000)
    input_request = request if kind == "calendar" else {key: request[key] for key in ("symbol", "start", "end")}
    sid = store.begin("alpaca_" + kind, original if original is not None else input_request, retain=retain_original)
    prepared = {"method": "GET", "request": request, "url": request_url(kind, request), "max_pages": 1 if kind == "calendar" else 8,
                "max_total_bytes": 8 * 1024 * 1024, "max_total_seconds": 60}
    if kind == "actions":
        prepared.update(max_page_bytes=2 * 1024 * 1024, min_request_interval=1.0, all_categories=True, date_semantics="process_date_envelope")
    if mutate_prepared:
        mutate_prepared(prepared)
    prepared_ref = store.put(prepared)
    store.event("acquisition_request_prepared", {"submission_id": sid, "request_sha256": prepared_ref})
    page_raw = b"invented opaque provider bytes, intentionally not provider JSON"
    raw_ref = store.put(page_raw)
    page = {"page": 1, "url": request_url(kind, request), "retrieved_at": None if null_page else STAMP,
            "http_status": 200, "raw_sha256": raw_ref, "bytes": len(page_raw)}
    if not missing_event and not null_page:
        store.event("acquisition_page_received", {"submission_id": sid, **page})
    identity = {"provider": "alpaca", "asset_class": "us_equity"}
    coverage = {"requested_start": DAY, "requested_end": DAY, "pagination_complete": True,
                "historical_information": "latest_retrieved_revision_not_point_in_time"}
    normalized = {"schema_version": 1, "kind": {"bars": "daily_bars", "calendar": "exchange_calendar", "actions": "corporate_actions"}[kind],
                  "evidence_kind": "historical_market_data", "research_eligible": False, "admission_status": "inspection_only", "identity": identity, "coverage": coverage}
    if kind == "actions":
        identity["symbol"] = "FAKE"
        wrappers = [{"category": category, "record": record, "occurrences": [{"raw_sha256": raw_ref, "page": 1, "index": index}]}
                    for index, (category, record) in enumerate(records or [])]
        categories = sorted({item["category"] for item in wrappers})
        normalized.update(records=wrappers, categories_present=categories, unknown_categories=sorted(set(categories) - lineage.CATEGORIES))
        coverage.update(date_semantics="process_date_envelope", economic_window_coverage="not_assessed", empty_result=None if wrappers else "no_records_returned_not_absence_proof")
        count = len(wrappers)
    else:
        identity["session_timezone"] = "America/New_York"
        coverage.update(returned_start=DAY, returned_end=DAY, corporate_actions="unknown",
                        calendar_status="unverified" if kind == "bars" else "provider_calendar_received_not_independently_certified")
        count = 1
        if kind == "bars":
            identity.update(symbol="FAKE", feed="sip", currency="USD", symbol_mapping="disabled_asof_dash", stable_entity_id=None)
            normalized.update(price_basis="raw", bars=[{"timestamp": DAY + "T00:00:00-04:00", "source_timestamp": DAY + "T04:00:00+00:00",
                "symbol": "FAKE", "open": 10, "high": 12, "low": 9, "close": 11, "volume": 100}])
        else:
            normalized["sessions"] = [{"date": DAY, "open": DAY + "T09:30:00-04:00", "close": DAY + "T16:00:00-04:00"}]
    if mutate_normalized:
        mutate_normalized(normalized)
    normalized_ref = store.put(normalized)
    receipt = {"schema_version": 1, "provider": "alpaca", "kind": kind, "submission_id": sid,
        "evidence_kind": "historical_market_data", "admission_status": "inspection_only", "research_eligible": False,
        "rights": {"status": "account_and_exchange_terms_not_certified", "use": "owner_authorized_private_inspection",
                   "public_distribution": False, "external_model_transmission": False,
                   "terms_reference": "https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf"},
        "source_documentation": ["https://example.test/documentation"], "status": "success", "request": request,
        "pages": [page], "limitations": ["invented fixture; no market evidence"], "started_at": STAMP,
        "normalizer_sha256": source or (lineage.ACTION_SOURCE if kind == "actions" else sorted(lineage.BAR_SOURCES)[0]),
        "request_sha256": prepared_ref, "normalized_sha256": normalized_ref, "row_count": count, "finished_at": STAMP}
    if kind == "actions":
        receipt.update(transport_sha256=lineage.TRANSPORT_SOURCE, submitted_request_sha256=store.submissions[sid]["request_sha256"],
                       pagination_complete=True, normalization_status="complete", coverage_assessment="not_performed",
                       categories_present=normalized["categories_present"], unknown_categories=normalized["unknown_categories"])
    refs = [prepared_ref, raw_ref, normalized_ref]
    if kind == "actions":
        refs.append(store.submissions[sid]["request_sha256"])
    if failure:
        receipt.update(status=failure, error="invented_failure")
        for key in ("normalized_sha256", "row_count", "finished_at"):
            receipt.pop(key)
        refs.remove(normalized_ref)
        if kind == "actions":
            receipt.update(pagination_complete=False, normalization_status="incomplete")
    if mutate_receipt:
        mutate_receipt(receipt)
    receipt_ref = store.put(receipt)
    if not pending:
        store.finish(sid, receipt["status"], {"receipt_sha256": receipt_ref, "artifact_refs": list(dict.fromkeys([*refs, receipt_ref, *[receipt[key] for key in ("request_sha256", "normalized_sha256", "submitted_request_sha256") if key in receipt]])), "error": receipt.get("error"), "research_eligible": False})
    return {"sid": sid, "receipt": receipt, "receipt_ref": receipt_ref, "prepared": prepared, "prepared_ref": prepared_ref,
            "normalized": normalized, "normalized_ref": normalized_ref, "raw_ref": raw_ref, "original_ref": store.submissions[sid]["request_sha256"]}


def code_identity(profile="d007"):
    sources = {name: HASH for name in ("research.py", "event_engine.py", "explorer.py", "admission.py", "alpaca_data.py", "alpaca_actions.py", "provenance.py", "ledger.py")}
    sources["admission.py"], sources["explorer.py"] = lineage.ADMISSION_SOURCES[profile]
    value = {"sources": sources, "dependency_lock_sha256": HASH, "entrypoint_bytecode_sha256": HASH,
             "event_entrypoint_bytecode_sha256": HASH, "loaded_engine_code": {"f": HASH}, "loaded_event_engine_code": {"f": HASH},
             "research_engine_globals": {"CONST": ["uninterpreted", {"value": HASH}]}, "event_engine_globals": {}, "loaded_admission_globals": {},
             "loaded_bars_provider_globals": {}, "loaded_actions_provider_globals": {}, "event_policy": {}, "python": "3.11", "implementation": "CPython"}
    if profile == "d007":
        sources.update({"policy_revision.py": lineage.POLICY_SOURCE, "study_suite.py": HASH})
        value.update(loaded_policy_revision_globals={}, loaded_study_suite_globals={})
    return value


def source_observation(store, *, extensions=None):
    source = store.put(b"invented attributed source, not issuer facts")
    sid = store.begin("public_source_observation", {"url": "https://example.test/source"})
    receipt = {"kind": "public_source_receipt", "source_sha256": source, "url": "https://example.test/source", "submission_id": sid}
    receipt.update(extensions or {})
    ref = store.put(receipt)
    store.finish(sid, "success", {"receipt_sha256": ref, "artifact_refs": [source, ref]})
    return {"sha256": source, "url": receipt["url"], "title": "Invented source", "locator": "invented paragraph", "receipt_sha256": ref}


def facts_and_usage(store, source, *, events=None, long_text=False):
    judgment = {"source_sha256": source["sha256"], "locator": "invented location", "judgment": "x" * 1025 if long_text else "invented attributed declaration"}
    facts = {"schema_version": 1, "kind": "attributed_primary_facts", "reviewer": "Fixture author", "reviewed_at": STAMP, "sources": [source],
             "identity": {**judgment, "symbol": "FAKE", "instrument_id": "invented:FAKE", "issuer_name": "Invented company", "currency": "USD",
                          "continuity_start": DAY, "continuity_end": DAY},
             "coverage": {**judgment, "start": DAY, "end": DAY, "known_events": [item["event"] for item in events or []]}, "events": events or []}
    usage = {"schema_version": 1, "kind": "source_use_review", "reviewer": "Fixture reviewer", "reviewed_at": STAMP, "sources": [source],
             "purpose": "private_own_account_research", "public_distribution": False, "external_model_transmission": False,
             "interpretation": "invented interpretation", "unresolved": ["account_and_exchange_terms_not_certified"]}
    return facts, usage


def dataset(store, bars):
    common_bars = {"schema_version": 1, "bars": [{k: v for k, v in row.items() if k != "source_timestamp"} for row in bars["normalized"]["bars"]]}
    data = {"schema_version": 1, "kind": "explorer_dataset", "evidence_kind": "historical_market_data", "source_sha256": bars["normalized_ref"],
        "bars_sha256": store.put(common_bars), "market": {"instrument_id": "invented:FAKE", "venue": "invented", "currency": "USD", "session_timezone": "America/New_York"},
        "symbol": "FAKE", "price_basis": "raw", "sessions": [DAY], "coverage_start": DAY, "coverage_end": DAY, "exposure_start": DAY, "exposure_end": DAY,
        "bar_count": 1, "parent_dataset_sha256": None, "admission_status": "inspection_only", "development_policy": "entire_dataset_development_only",
        "prior_exposure": "unknown_outside_application", "calendar_status": "unverified", "corporate_actions": "unknown", "timing": "inspection_only", "rights": "unverified"}
    return data, store.put(data)


def admission_fixture(store, profile="d007", *, retain=False, raw_original=None, mutate=None, long_text=False, action_records=None, exclusions=None, mutate_facts=None):
    acquired = {kind: acquisition(store, kind, records=action_records if kind == "actions" else None) for kind in ("bars", "calendar", "actions")}
    source = source_observation(store)
    facts, usage = facts_and_usage(store, source, long_text=long_text)
    if exclusions:
        facts["excluded_actions"] = exclusions(source)
    if mutate_facts:
        mutate_facts(facts)
    data, data_ref = dataset(store, acquired["bars"])
    request = {"dataset_sha256": data_ref, "primary_facts_sha256": store.put(facts), "usage_review_sha256": store.put(usage),
               "submitted_requests": {kind: value["original_ref"] for kind, value in acquired.items()},
               **{kind + "_receipt_sha256": value["receipt_ref"] for kind, value in acquired.items()}}
    original = raw_original(request) if raw_original else request
    sid = store.begin("historical_admission", original, retain=retain)
    result = {"schema_version": 1, "kind": "historical_admission", "request": request, "dataset_sha256": data_ref, "scope": "conditional_retrospective_development",
              "rules": deepcopy(lineage.ADMISSION_RULES[profile]), "code_identity": code_identity(profile), "actions": [], "excluded_actions": [], "sessions": [DAY],
              "full_acquired_exposure": {"start": DAY, "end": DAY}, "market": data["market"],
              "request_parameters_sha256": hashed({kind: value["receipt"]["request"] for kind, value in acquired.items()}),
              "limitations": list(lineage.ADMISSION_LIMITATIONS), "artifact_refs": [data_ref, request["primary_facts_sha256"], request["usage_review_sha256"]]}
    if exclusions:
        result["excluded_actions"] = [{"reason": "completed_pre_window_acquirer_cash_merger", "annotation": annotation, "record_sha256": annotation["record_sha256"],
            "occurrences": acquired["actions"]["normalized"]["records"][index]["occurrences"]} for index, annotation in enumerate(facts["excluded_actions"])]
    if profile == "d007":
        result["accepted_action_treatments"] = []
    if mutate:
        mutate(result)
    ref = store.put(result)
    store.finish(sid, "success", {"admission_sha256": ref, "dataset_sha256": data_ref, "scope": result["scope"], "artifact_refs": [ref, *result["artifact_refs"]]})
    return {"ref": ref, "result": result, "sid": sid, "acquired": acquired, "facts": facts, "usage": usage, "source": source}


@pytest.mark.parametrize("kind,source", [(kind, source) for kind in ("bars", "calendar") for source in sorted(lineage.BAR_SOURCES)] + [("actions", lineage.ACTION_SOURCE)])
def test_known_acquisition_profiles_are_origin_selected(store, kind, source):
    found = acquisition(store, kind, source=source)
    report = store.inspect()
    for key, role in (("receipt_ref", "acquisition_receipt"), ("prepared_ref", "acquisition_request"), ("normalized_ref", "normalized_observation")):
        assert checked(report, found[key], role)
    assert "provider_normalization_semantics_not_replayed" in reasons(report)
    assert not {"unsupported_submission_kind", "unsupported_event_profile"} & reasons(report)
    assert report["lineage_source_sha256"] == recovery._sha(Path(lineage.__file__).read_bytes())
    assert closure.public_projection(report)["lineage_loaded_sha256"] == report["lineage_loaded_sha256"]


@pytest.mark.parametrize("profile", ["d006", "d007"])
@pytest.mark.parametrize("retain,raw_original", [(False, None), (True, None), (True, lambda value: ("  " + json.dumps(value, indent=2) + "\n").encode())])
def test_admission_original_bytes_are_not_reconstructed(store, profile, retain, raw_original):
    found = admission_fixture(store, profile, retain=retain, raw_original=raw_original, long_text=True)
    report = store.inspect()
    assert checked(report, found["ref"], "admission")
    assert ("original_request_bytes_unavailable" in reasons(report)) is (not retain)
    assert {"admission_economic_semantics_not_revalidated", "attributed_facts_not_economically_revalidated"} <= reasons(report)


def test_retained_contradictory_admission_original_refuses(store):
    admission_fixture(store, retain=True, raw_original=lambda value: encoded({**value, "dataset_sha256": "f" * 64}))
    with pytest.raises(closure.ClosureError, match="original_request_content_mismatch"):
        store.inspect()


@pytest.mark.parametrize("kind", ["bars", "calendar", "actions"])
@pytest.mark.parametrize("status", ["failed", "invalid"])
def test_partial_failure_preserves_receipt_pages_and_orphan_normalization(store, kind, status):
    found = acquisition(store, kind, failure=status)
    report = store.inspect()
    assert checked(report, found["receipt_ref"], "acquisition_receipt")
    assert "unclassified_orphan_inventory" in reasons(report)
    assert not checked(report, found["normalized_ref"], "normalized_observation")


def test_actions_clock_failure_preserves_null_retrieval_and_missing_page_event(store):
    found = acquisition(store, "actions", failure="failed", null_page=True)
    report = store.inspect()
    assert checked(report, found["receipt_ref"], "acquisition_receipt")
    assert "interrupted_page_event_publication" in reasons(report)


def test_pending_events_remain_roots_without_invented_receipt_profile(store):
    found = acquisition(store, pending=True)
    report = store.inspect()
    assert {"pending_registered_work", "prepared_request_origin_unresolved"} <= reasons(report)
    assert not checked(report, found["prepared_ref"], "acquisition_request")
    assert any(n["digest"] == found["raw_ref"] and n["status"] == "opaque_leaf" for n in report["nodes"])


@pytest.mark.parametrize("source", ["f" * 64, None])
def test_unknown_or_early_origin_remains_gap(store, source):
    def change(value):
        if source is None:
            for key in ("normalizer_sha256", "started_at"):
                value.pop(key)
    found = acquisition(store, source=source, failure="failed", mutate_receipt=change)
    report = store.inspect()
    assert "acquisition_producer_origin_unresolved" in reasons(report)
    assert not checked(report, found["receipt_ref"], "acquisition_receipt")


@pytest.mark.parametrize("change", [
    lambda d: d.pop("normalized_sha256"), lambda d: d.pop("row_count"), lambda d: d.pop("request_sha256"),
    lambda d: d.update(row_count=True), lambda d: d.update(research_eligible=True), lambda d: d.update(extra=HASH),
    lambda d: d["pages"][0].update(bytes=1), lambda d: d["pages"][0].update(page=2),
    lambda d: d["pages"][0].update(retrieved_at=None), lambda d: d.update(normalizer_sha256=lineage.ACTION_SOURCE),
])
def test_known_receipt_contradictions_refuse(store, change):
    acquisition(store, mutate_receipt=change)
    with pytest.raises(closure.ClosureError):
        store.inspect()


@pytest.mark.parametrize("change", [
    lambda d: d.update(schema_version=1), lambda d: d.update(max_pages=True), lambda d: d.update(method="POST"),
    lambda d: d.update(url=d["url"] + "&sort=asc"), lambda d: d.update(url=d["url"].replace("https://", "file://")),
    lambda d: d.update(url=d["url"].replace("data.alpaca.markets", "evil.test")),
    lambda d: d.update(url=d["url"].replace("data.alpaca.markets", "user@data.alpaca.markets")),
    lambda d: d.update(url=d["url"] + "#ignored"), lambda d: d.update(url=d["url"] + "&page_token=a"),
])
def test_prepared_profile_refuses_unknown_fields_and_adversarial_urls(store, change):
    acquisition(store, mutate_prepared=change)
    with pytest.raises(closure.ClosureError):
        store.inspect()


@pytest.mark.parametrize("kind", ["bars", "calendar", "actions"])
@pytest.mark.parametrize("change", [
    lambda url: "\x00" + url,
    lambda url: url + "\t",
    lambda url: url.replace("https://", "https:\n//"),
])
def test_prepared_url_controls_are_not_erased_before_verification(store, kind, change):
    acquisition(store, kind, mutate_prepared=lambda value: value.update(url=change(value["url"])))
    with pytest.raises(closure.ClosureError, match="acquisition_url_mismatch"):
        store.inspect()


@pytest.mark.parametrize("change", [
    lambda d: d.pop("price_basis"), lambda d: d.update(schema_version=True), lambda d: d["bars"][0].update(open=True),
    lambda d: d["bars"][0].update(open=100), lambda d: d["bars"][0].update(volume=-1),
    lambda d: d["coverage"].update(pagination_complete=False), lambda d: d["identity"].update(stable_entity_id=HASH),
    lambda d: d["bars"].append(deepcopy(d["bars"][0])),
])
def test_normalized_known_profile_is_strict(store, change):
    acquisition(store, mutate_normalized=change)
    with pytest.raises(closure.ClosureError):
        store.inspect()


def test_digest_looking_provider_fields_are_not_files(store):
    found = acquisition(store, "actions", records=[("forward_splits", {"id": "invented", "sha256": "f" * 64, "amount": "1", "flag": True, "nested": [None, "e" * 64]})])
    report = store.inspect()
    assert checked(report, found["normalized_ref"], "normalized_observation")
    assert not any(edge["digest"] in {"f" * 64, "e" * 64} for edge in report["edges"])


@pytest.mark.parametrize("profile,change", [
    ("d007", lambda d: d.pop("accepted_action_treatments")), ("d006", lambda d: d.update(accepted_action_treatments=[])),
    ("d007", lambda d: d["code_identity"]["sources"].update({"explorer.py": lineage.ADMISSION_SOURCES["d006"][1]})),
    ("d007", lambda d: d.update(rules=lineage.ADMISSION_RULES["d006"])), ("d006", lambda d: d.update(request_parameters_sha256="f" * 64)),
])
def test_known_admission_profile_deletion_downgrade_and_identity_mismatch_refuse(store, profile, change):
    admission_fixture(store, profile, mutate=change)
    with pytest.raises(closure.ClosureError):
        store.inspect()


@pytest.mark.parametrize("profile,value,valid", [("d006", " 1_0 ", True), ("d007", " 1_0 ", False),
    ("d006", "NaN", False), ("d007", "+.1e+2", True), ("d006", "1e101", False), ("d007", "1e-101", False)])
def test_historical_decimal_forms(profile, value, valid):
    if valid:
        lineage.rate(value, profile)
    else:
        with pytest.raises(lineage.LineageError):
            lineage.rate(value, profile)


def test_unbound_provider_or_source_kind_does_not_select_profile(store):
    ref = store.put({"schema_version": 1, "kind": "daily_bars", "forged_reference": "f" * 64})
    sid = store.begin("unknown_manual_writer", {})
    store.finish(sid, "success", {"artifact_refs": [ref]})
    report = store.inspect()
    assert "unclassified_declared_object" in reasons(report)
    assert not any(edge["digest"] == "f" * 64 for edge in report["edges"])


def test_manual_public_receipt_extensions_preserve_gap(store):
    source_observation(store, extensions={"extra_digest": "f" * 64, "retrieved_at": STAMP})
    report = store.inspect()
    assert "unsupported_manual_fields" in reasons(report)
    assert not any(edge["digest"] == "f" * 64 for edge in report["edges"])


def split_family(store, source, record, *, mutate_annotation=None, mutate_review=None):
    ref = source["sha256"]
    attributed = {"source_sha256": ref, "locator": "invented location", "judgment": "invented, no factual certification",
                  "author": "Fixture author", "observed_at": STAMP, "classification": "direct", "supporting_sources": []}
    schedule = {"schema_version": 1, "kind": "independent_exchange_schedule", "exchange": "invented exchange", "timezone": "America/New_York",
                "start": DAY, "end": DAY, "source_sha256": ref, "sessions": [DAY], "early_closes": {DAY: "13:00"}, "extraction": attributed,
                "review": {"reviewer": "Calendar reviewer", "reviewed_at": STAMP, "verdict": "accepted", "report_sha256": store.put(b"invented calendar review")}}
    schedule_ref = store.put(schedule)
    annotation = {"schema_version": 1, "profile": "domestic_integer_forward_split_v1", "author": "Fixture author", "observed_at": STAMP,
        "provider_id": record["id"], "record_sha256": hashed(record),
        "provider_dates": {key: {"present": key in record, "value": record.get(key)} for key in lineage.DATE_FIELDS},
        "source_roles": {key: ref for key in lineage.SOURCE_ROLES},
        "issuer_terms": {**attributed, "symbol": "FAKE", "instrument_id": "invented:FAKE", "security_type": "domestic_common_stock", "new_rate": "2", "old_rate": "1",
                         "record_date": DAY, "distribution_date": DAY, "distribution_timing": "after_close", "first_adjusted_session": DAY, "trading_statement": "expected_or_scheduled"},
        "seller_treatment": {**attributed, "transfers_attached_interest": True}, "purchaser_entitlement": {**attributed, "receives_attached_interest": True},
        "economic_scope": {**attributed, "same_security_and_market": True, "separate_entitlement_market": False, "additional_claims_or_cash": False,
                           "elections": False, "fractional_cash_in_lieu": False},
        "rules_applicability": {**attributed, "regime_start": "2024-05-28"},
        "date_dispositions": {key: {**attributed, "status": "unresolved_ancillary_date_discrepancy", "controlling_terms_established": True, "explanation": "invented discrepancy",
            **({"documented_meaning": "delivery_obligations", "actual_outcome": "unverified", "transformation_trigger": "issuer_first_adjusted_session"} if key == "due_bill_redemption_date" else {})}
            for key in ("record_date", "payable_date", "due_bill_redemption_date")}}
    if mutate_annotation:
        mutate_annotation(annotation)
    annotation_ref = store.put(annotation)
    review = {"schema_version": 1, "kind": "regular_way_split_semantic_review", "annotation_sha256": annotation_ref, "author": "Fixture author",
              "reviewer": "Split reviewer", "reviewer_kind": "native_agent", "reviewed_at": STAMP, "verdict": "accepted_with_qualifications",
              "reviewed_sources": [ref], "reviewed_calendar_sha256": schedule_ref, "report_sha256": store.put(b"invented semantic review")}
    if mutate_review:
        mutate_review(review)
    review_ref = store.put(review)
    sid = store.begin("regular_way_split_semantic_review", {"review_sha256": review_ref}, retain=True)
    request_ref = store.submissions[sid]["request_sha256"]
    store.finish(sid, "success", {"review_sha256": review_ref, "request_sha256": request_ref, "annotation_sha256": annotation_ref,
        "artifact_refs": [review_ref, request_ref, annotation_ref, schedule_ref, review["report_sha256"], ref]})
    return {"annotation": annotation, "annotation_ref": annotation_ref, "review": review, "review_ref": review_ref,
            "schedule": schedule, "schedule_ref": schedule_ref, "review_sid": sid}


def frozen_plan():
    value = {key: "invented declaration" for key in lineage.FROZEN_FIELDS}
    value.update(instrument="FAKE", data_start=DAY, data_end=DAY, evaluation_start=DAY, evaluation_end=DAY, lookback=1,
                 starting_cash=1000, entry_threshold=0, exit_threshold=0, cost_bps_scenarios=[0, 10, 25], basis="raw", sma_includes_current_close=True,
                 arithmetic={"economic_cash": True}, session_order=["split", "target", "close"])
    return value


def plan_registration(store, data, kind="pilot_plan_registration"):
    ref = store.put(data)
    sid = store.begin(kind, {"plan_sha256": ref})
    store.finish(sid, "success", {"plan_sha256": ref, "financial_result": False, "artifact_refs": [ref]})
    return {"plan_sha256": ref, "submission_id": sid}


def refusal(store, request, code):
    raw = json.dumps(request, indent=2).encode()
    sid = store.begin("historical_admission", raw, retain=True)
    store.finish(sid, "invalid", {"error_code": code, "result_kind": "no_admission"})
    return {"submission_id": sid, "request_sha256": recovery._sha(raw)}


def policy_fixture(store, *, root_link="absent", mutate_policy=None, mutate_review=None, mutate_annotation=None, mutate_root=None, mutate_request=None):
    frozen = frozen_plan()
    root_plan = deepcopy(frozen)
    if root_link != "absent":
        root_plan[root_link] = None
    if mutate_root:
        mutate_root(root_plan)
    first_plan = plan_registration(store, root_plan)
    record = {"id": "invented-split", "symbol": "FAKE", "new_rate": "2", "old_rate": "1", "ex_date": DAY, "due_bill_redemption_date": DAY}
    acquired = {kind: acquisition(store, kind, records=[("forward_splits", record)] if kind == "actions" else None) for kind in ("bars", "calendar", "actions")}
    source = source_observation(store)
    event = {"kind": "split", "event_id": record["id"], "effective_date": DAY, "new_rate": "2", "old_rate": "1"}
    basic_annotation = {"provider_id": record["id"], "event": event, "source_sha256": source["sha256"], "locator": "fixture", "judgment": "invented"}
    facts, usage = facts_and_usage(store, source, events=[basic_annotation])
    data, data_ref = dataset(store, acquired["bars"])
    request = {"dataset_sha256": data_ref, "primary_facts_sha256": store.put(facts), "usage_review_sha256": store.put(usage),
               "submitted_requests": {kind: value["original_ref"] for kind, value in acquired.items()},
               **{kind + "_receipt_sha256": value["receipt_ref"] for kind, value in acquired.items()}}
    first_refusal = refusal(store, request, "identity_change_unresolved")
    link = "previous_plan_sha256" if root_link == "absent" else root_link
    refined = {**root_plan, link: first_plan["plan_sha256"], "relevance_refinement": {
        "kind": "implementation_of_preexisting_structured_exclusion", "original_admission_refusal": first_refusal["submission_id"],
        "facts_sha256": request["primary_facts_sha256"], "portfolio_result_observed_before_refinement": False, "strategy_window_costs_unchanged": True}}
    second_plan = plan_registration(store, refined, "pilot_plan_refinement")
    second_refusal = refusal(store, request, "unsupported_due_bill")
    family = split_family(store, source, record, mutate_annotation=mutate_annotation, mutate_review=mutate_review)
    new_facts = deepcopy(facts)
    new_facts["events"][0].update(regular_way_split=family["annotation"], semantic_review_sha256=family["review_ref"])
    new_facts["independent_schedule_sha256"] = family["schedule_ref"]
    new_facts_ref = store.put(new_facts)
    directory = Path(__file__).resolve().parents[1] / "docs"
    decision = store.put((directory / "D007_POLICY.md").read_bytes())
    reviews = [store.put((directory / "reviews" / ("D007-" + key + ".md")).read_bytes()) for key in lineage.POLICY_RULES["approved_review_sha256s"]]
    assert decision == lineage.POLICY_RULES["accepted_decision_sha256"]
    assert set(reviews) == set(lineage.POLICY_RULES["approved_review_sha256s"].values())
    policy_request = {"schema_version": 1, "kind": "policy_revision_request", "predecessor_plans": [first_plan, second_plan],
        "refused_admissions": [first_refusal, second_refusal], "accepted_decision_sha256": decision, "review_sha256s": reviews,
        "new_primary_facts_sha256": new_facts_ref, "frozen_study": frozen, "classification": "post_acquisition_development_only"}
    if mutate_request:
        mutate_request(policy_request)
    sid = store.begin("policy_revision", policy_request, retain=True)
    plans = [{**entry, "registration_kind": kind, "started_event": store.starts[entry["submission_id"]], "finished_event": store.finishes[entry["submission_id"]],
              "classification": classification} for entry, kind, classification in ((first_plan, "pilot_plan_registration", "pre_acquisition_plan"),
                  (second_plan, "pilot_plan_refinement", "post_acquisition_implementation_refinement"))]
    refusals = [{**entry, "error_code": code, "started_event": store.starts[entry["submission_id"]], "finished_event": store.finishes[entry["submission_id"]], "request": request}
                for entry, code in ((first_refusal, "identity_change_unresolved"), (second_refusal, "unsupported_due_bill"))]
    acquisitions = {kind: {"submission_id": v["sid"], "receipt_sha256": v["receipt_ref"], "submitted_request_sha256": v["original_ref"],
                   "normalized_sha256": v["normalized_ref"], "started_event": store.starts[v["sid"]], "finished_event": store.finishes[v["sid"]]} for kind, v in acquired.items()}
    result = {"schema_version": 1, "kind": "policy_revision", "request": policy_request, "rules": deepcopy(lineage.POLICY_RULES), "code_identity": code_identity(),
        "dataset_sha256": data_ref, "frozen_study": frozen,
        "facts_delta": [{"path": "$.events[0].regular_way_split", "operation": "add", "value": family["annotation"]},
                        {"path": "$.events[0].semantic_review_sha256", "operation": "add", "value": family["review_ref"]},
                        {"path": "$.independent_schedule_sha256", "operation": "add", "value": family["schedule_ref"]}],
        "lineage": {"plans": plans, "prior_refusals": refusals, "acquisitions": acquisitions, "post_acquisition_change_count": 2,
                    "current_change": "financial_policy_revision", "classification": "post_acquisition_development_only"},
        "artifact_refs": sorted({data_ref, new_facts_ref, decision, *reviews, *[entry["plan_sha256"] for entry in (first_plan, second_plan)],
                                 *[entry["request_sha256"] for entry in (first_refusal, second_refusal)]})}
    if mutate_policy:
        mutate_policy(result)
    ref = store.put(result)
    original_ref = store.submissions[sid]["request_sha256"]
    store.finish(sid, "success", {"policy_revision_sha256": ref, "request_sha256": original_ref, "dataset_sha256": data_ref,
        "post_acquisition_change_count": result["lineage"]["post_acquisition_change_count"], "artifact_refs": sorted({ref, original_ref, *result["artifact_refs"]})})
    return {"ref": ref, "result": result, "request": request, "family": family, "acquired": acquired, "facts": new_facts, "data": data, "sid": sid}


@pytest.mark.parametrize("root_link", ["absent", "previous_plan_sha256", "previous_plan_bytes_sha256"])
def test_complete_connected_policy_family_and_root_predecessor_forms(store, root_link):
    found = policy_fixture(store, root_link=root_link)
    report = store.inspect()
    assert checked(report, found["ref"], "policy_revision")
    for key, role in (("review_ref", "semantic_review"), ("annotation_ref", "split_annotation"), ("schedule_ref", "independent_schedule")):
        assert checked(report, found["family"][key], role)
    assert {"manual_plan_fields_and_origin_unverified", "policy_economic_semantics_not_revalidated"} <= reasons(report)
    assert not any(edge["digest"] == hashed(found["family"]["annotation"]["provider_dates"]) for edge in report["edges"])


@pytest.mark.parametrize("change", [
    lambda d: d["code_identity"]["sources"].pop("policy_revision.py"),
    lambda d: d["code_identity"]["sources"].update({"policy_revision.py": "f" * 64}),
    lambda d: d["code_identity"]["sources"].update({"policy_revision.py": lineage.ADMISSION_SOURCES["d007"][0]}),
])
def test_policy_requires_own_source_selector(store, change):
    found = policy_fixture(store, mutate_policy=change)
    report = store.inspect()
    assert "policy_producer_origin_unresolved" in reasons(report)
    assert not checked(report, found["ref"], "policy_revision")


@pytest.mark.parametrize("change", [
    lambda d: d["rules"].update(version="D006"), lambda d: d["lineage"].update(post_acquisition_change_count=1),
    lambda d: d["lineage"]["plans"][0].update(started_event=True), lambda d: d["lineage"]["prior_refusals"][0].update(error_code="erased"),
    lambda d: d["facts_delta"][0].update(path="$.anything[99].sha256"), lambda d: d["facts_delta"][0].update(operation="replace"),
    lambda d: d["lineage"]["acquisitions"]["bars"].update(submitted_request_sha256=d["lineage"]["acquisitions"]["bars"]["receipt_sha256"]),
])
def test_policy_known_contradictions_refuse(store, change):
    policy_fixture(store, mutate_policy=change)
    with pytest.raises(closure.ClosureError):
        store.inspect()


@pytest.mark.parametrize("change", [lambda d: d.update(reviewer="Fixture author"), lambda d: d.update(reviewed_sources=[]),
    lambda d: d.update(reviewed_at="2020-01-01T00:00:00+00:00"), lambda d: d.update(reviewer_kind="model_guess"),
    lambda d: d.update(annotation_sha256="f" * 64)])
def test_semantic_review_registration_and_attribution_refuse_contradictions(store, change):
    policy_fixture(store, mutate_review=change)
    with pytest.raises(closure.ClosureError):
        store.inspect()


def test_manual_nested_extensions_preserve_gaps(store):
    found = policy_fixture(store, mutate_annotation=lambda d: d["issuer_terms"].update(unknown_reference="f" * 64))
    report = store.inspect()
    assert checked(report, found["ref"], "policy_revision")
    assert "unsupported_manual_fields" in reasons(report)
    assert not any(edge["digest"] == "f" * 64 for edge in report["edges"])


def policy_admission(store, found, *, mutate=None, started_sid=None):
    request = {**found["request"], "primary_facts_sha256": found["result"]["request"]["new_primary_facts_sha256"], "policy_revision_sha256": found["ref"]}
    sid = started_sid or store.begin("historical_admission", request)
    family = found["family"]
    wrapper = found["acquired"]["actions"]["normalized"]["records"][0]
    treatment = {"profile": family["annotation"]["profile"], "provider_id": wrapper["record"]["id"], "annotation": family["annotation"],
        "annotation_sha256": family["annotation_ref"], "provider_record": wrapper["record"], "record_sha256": hashed(wrapper["record"]),
        "occurrences": wrapper["occurrences"], "ratio": "2", "semantic_review_sha256": family["review_ref"], "independent_schedule_sha256": family["schedule_ref"],
        "date_dispositions": family["annotation"]["date_dispositions"], "additional_event_corroboration_status": "not_supplied", "limitations": lineage.SPLIT_LIMITATIONS}
    result = {"schema_version": 1, "kind": "historical_admission", "request": request, "dataset_sha256": request["dataset_sha256"], "scope": "conditional_retrospective_development",
        "rules": lineage.ADMISSION_RULES["d007"], "code_identity": code_identity(), "actions": found["facts"]["coverage"]["known_events"], "excluded_actions": [], "sessions": [DAY],
        "full_acquired_exposure": {"start": DAY, "end": DAY}, "market": found["data"]["market"], "request_parameters_sha256": hashed({k: v["receipt"]["request"] for k, v in found["acquired"].items()}),
        "limitations": lineage.ADMISSION_LIMITATIONS + lineage.SPLIT_LIMITATIONS, "artifact_refs": [found["ref"]], "accepted_action_treatments": [treatment],
        "policy_revision_sha256": found["ref"], "policy_revision": {**found["result"], "policy_revision_sha256": found["ref"]}}
    if mutate:
        mutate(result)
    ref = store.put(result)
    store.finish(sid, "success", {"admission_sha256": ref, "dataset_sha256": request["dataset_sha256"], "scope": result["scope"], "artifact_refs": [ref, *result["artifact_refs"]]})
    return ref, result


def test_admission_embedded_revision_augmentation_is_not_hashed_as_published_object(store):
    found = policy_fixture(store)
    ref, result = policy_admission(store, found)
    report = store.inspect()
    assert checked(report, ref, "admission")
    assert hashed(result["policy_revision"]) != found["ref"]
    assert not any(edge["digest"] == hashed(result["policy_revision"]) for edge in report["edges"])
    assert checked(report, found["ref"], "policy_revision")


@pytest.mark.parametrize("field,value", [("symbol", "FOREIGN"), ("instrument_id", "invented:FOREIGN")])
@pytest.mark.parametrize("with_admission", [False, True])
def test_coherent_split_lineage_cannot_change_the_studied_instrument(store, field, value, with_admission):
    # All published hashes and copies agree; the contradiction is between the
    # split's issuer terms and the retained study identity, not broken storage.
    found = policy_fixture(store, mutate_annotation=lambda annotation: annotation["issuer_terms"].update({field: value}))
    if with_admission:
        policy_admission(store, found)
    with pytest.raises(closure.ClosureError, match="split_instrument_binding_mismatch"):
        store.inspect()


@pytest.mark.parametrize("change", [lambda d: d["policy_revision"].pop("policy_revision_sha256"),
    lambda d: d["policy_revision"].update(policy_revision_sha256="f" * 64),
    lambda d: d["policy_revision"]["facts_delta"].clear(), lambda d: d["accepted_action_treatments"].clear(),
    lambda d: d["accepted_action_treatments"][0].update(ratio=True),
    lambda d: d["accepted_action_treatments"][0]["occurrences"][0].update(index=99)])
def test_embedded_policy_and_treatment_contradictions_refuse(store, change):
    found = policy_fixture(store)
    # Isolate mutation from retained parent dictionaries used by the harness.
    def independent_change(data):
        copy = deepcopy(data)
        change(copy)
        data.clear()
        data.update(copy)
    policy_admission(store, found, mutate=independent_change)
    with pytest.raises(closure.ClosureError):
        store.inspect()


@pytest.mark.parametrize("field,value", [("edges", 2), ("nodes", 2), ("json_items", 10), ("depth", 2), ("graph_hops", 1)])
def test_shared_aggregate_limits_apply_to_lineage(store, field, value):
    policy_fixture(store)
    with pytest.raises(closure.ClosureError, match="closure_.*_limit"):
        store.inspect(limits=replace(closure.ClosureLimits(), **{field: value}))


def test_missing_required_original_refusal_bytes_refuse(store):
    found = policy_fixture(store)
    ref = found["result"]["request"]["refused_admissions"][0]["request_sha256"]
    (store.root / "data/objects" / (ref + ".bin")).unlink()
    with pytest.raises((closure.ClosureError, recovery.RecoveryError), match="required_object_missing"):
        store.inspect()


def test_tombstoned_required_refusal_bytes_remain_explicit_gap(store):
    found = policy_fixture(store)
    ref = found["result"]["request"]["refused_admissions"][0]["request_sha256"]
    store.db.execute("CREATE TABLE artifact_tombstones(digest TEXT,reason TEXT,tombstoned_at TEXT)")
    store.db.execute("INSERT INTO artifact_tombstones VALUES(?,?,?)", (ref, "operator_requested", STAMP))
    report = store.inspect()
    assert {"required_tombstoned_object", "policy_lineage_binding_unavailable"} <= reasons(report)
    assert not checked(report, found["ref"], "policy_revision")


def test_corrupted_nested_object_refuses_before_parsing(store):
    found = policy_fixture(store)
    path = store.root / "data/objects" / (found["family"]["annotation_ref"] + ".bin")
    path.write_bytes(b"corruption")
    with pytest.raises((closure.ClosureError, recovery.RecoveryError)):
        store.inspect()


def test_duplicate_registered_event_refuses_even_with_valid_hash_chain(store):
    found = acquisition(store)
    store.event("submission_started", store.submissions[found["sid"]])
    with pytest.raises(closure.ClosureError, match="registration_event_mismatch"):
        store.inspect()


def test_prepared_digest_cannot_replace_original_submission_digest(store):
    def change(data):
        data["request"]["submitted_requests"]["bars"] = data["request"]["bars_receipt_sha256"]
    admission_fixture(store, mutate=change)
    with pytest.raises(closure.ClosureError, match="original_request_identity_mismatch"):
        store.inspect()


def test_early_failure_can_retain_unparseable_original_bytes(store):
    raw = b"not JSON, failed before parsing"
    sid = store.begin("alpaca_bars", raw, retain=True)
    receipt = {"schema_version": 1, "provider": "alpaca", "kind": "bars", "submission_id": sid,
        "evidence_kind": "historical_market_data", "admission_status": "inspection_only", "research_eligible": False,
        "rights": {"status": "account_and_exchange_terms_not_certified", "use": "owner_authorized_private_inspection", "public_distribution": False,
                   "external_model_transmission": False, "terms_reference": "https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf"},
        "source_documentation": ["https://example.test"], "limitations": ["invented"], "request": None, "pages": [],
        "started_at": STAMP, "normalizer_sha256": sorted(lineage.BAR_SOURCES)[0], "status": "invalid", "error": "request_invalid", "http_status": None}
    ref = store.put(receipt)
    store.finish(sid, "invalid", {"receipt_sha256": ref, "error": "request_invalid", "research_eligible": False, "artifact_refs": [ref, recovery._sha(raw)]})
    report = store.inspect()
    assert checked(report, ref, "acquisition_receipt")


@pytest.mark.parametrize("change", [lambda d: d.update(previous_plan_sha256=None, previous_plan_bytes_sha256=None),
    lambda d: d.update(previous_plan_sha256="f" * 64)])
def test_two_root_predecessors_or_nonnull_disconnected_root_refuse(store, change):
    policy_fixture(store, mutate_root=change)
    with pytest.raises(closure.ClosureError):
        store.inspect()


def test_repeated_policy_plan_is_refused_as_cyclic_predecessor_chain(store):
    policy_fixture(store, mutate_request=lambda d: d["predecessor_plans"].append(d["predecessor_plans"][0]))
    with pytest.raises(closure.ClosureError):
        store.inspect()


def test_one_normalized_digest_cannot_satisfy_conflicting_known_receipt_roles(store):
    calendar = acquisition(store, "calendar")
    acquisition(store, "bars", mutate_receipt=lambda d: d.update(normalized_sha256=calendar["normalized_ref"]))
    with pytest.raises(closure.ClosureError, match="malformed_lineage_profile|profile_role_mismatch"):
        store.inspect()


def test_successful_receipt_requires_observed_page_event(store):
    acquisition(store, missing_event=True)
    with pytest.raises(closure.ClosureError):
        store.inspect()


def test_failed_receipt_missing_prepared_publication_event_preserves_gap(store):
    sid = store.begin("alpaca_bars", {"symbol": "FAKE", "start": DAY, "end": DAY})
    request = {"symbol": "FAKE", "start": DAY, "end": DAY, "adjustment": "raw", "timeframe": "1Day", "feed": "sip", "currency": "USD", "asof": "-"}
    prepared = {"method": "GET", "request": request, "url": request_url("bars", request), "max_pages": 8, "max_total_bytes": 8 * 1024 * 1024, "max_total_seconds": 60}
    prepared_ref = store.put(prepared)
    receipt = {"schema_version": 1, "provider": "alpaca", "kind": "bars", "submission_id": sid,
        "evidence_kind": "historical_market_data", "admission_status": "inspection_only", "research_eligible": False,
        "rights": {"status": "account_and_exchange_terms_not_certified", "use": "owner_authorized_private_inspection", "public_distribution": False,
                   "external_model_transmission": False, "terms_reference": "https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf"},
        "source_documentation": ["https://example.test"], "limitations": ["invented"], "request": request, "request_sha256": prepared_ref, "pages": [],
        "started_at": STAMP, "normalizer_sha256": sorted(lineage.BAR_SOURCES)[0], "status": "failed", "error": "storage_unavailable"}
    ref = store.put(receipt)
    store.finish(sid, "failed", {"receipt_sha256": ref, "error": "storage_unavailable", "research_eligible": False, "artifact_refs": [ref, prepared_ref]})
    report = store.inspect()
    assert checked(report, prepared_ref, "acquisition_request")
    assert "interrupted_prepared_event_publication" in reasons(report)


def test_duplicate_keys_in_retained_original_are_not_collapsed(store):
    admission_fixture(store, retain=True, raw_original=lambda value: encoded(value)[:-1] + b',"dataset_sha256":"' + value["dataset_sha256"].encode() + b'"}')
    with pytest.raises(closure.ClosureError):
        store.inspect()


def test_helper_loaded_change_during_inspection_is_detected(store, monkeypatch):
    import os
    found = acquisition(store)
    original_open, seen = os.open, 0
    def observe(path, *args, **kwargs):
        nonlocal seen
        if str(path).endswith(found["receipt_ref"] + ".bin") and "snapshot-" in str(path):
            seen += 1
            if seen == 2:
                monkeypatch.setattr(lineage, "BAR_SOURCES", frozenset())
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(os, "open", observe)
    with pytest.raises(closure.ClosureError, match="loaded_implementation_changed"):
        store.inspect()


def test_inspector_does_not_import_domain_or_network_modules(store, monkeypatch):
    import builtins
    found = policy_fixture(store)
    original_import = builtins.__import__
    forbidden = {"quanto.admission", "quanto.alpaca_data", "quanto.alpaca_actions", "quanto.policy_revision", "quanto.provenance",
                 "quanto.ledger", "quanto.explorer", "quanto.research", "quanto.event_engine", "http.client", "socket"}
    def guarded(name, *args, **kwargs):
        assert name not in forbidden
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)
    report = store.inspect()
    assert checked(report, found["ref"], "policy_revision")


@pytest.mark.parametrize("profile", ["d006", "d007"])
def test_excluded_merger_annotation_retains_both_attributed_sources_and_inline_record(store, profile):
    record = {"id": "invented-exclusion", "effective_date": "2020-01-01", "acquirer_symbol": "FAKE", "acquiree_symbol": "OTHER", "rate": "1"}
    def exclusions(source):
        judgment = {"source_sha256": source["sha256"], "locator": "invented", "judgment": "invented attributed exclusion"}
        return [{**judgment, "provider_id": record["id"], "category": "cash_mergers", "record_sha256": hashed(record), "effective_date": "2020-01-01",
            "acquirer": {"symbol": "FAKE", "cusip": "invented-cusip", "isin": None}, "acquiree": {"symbol": "OTHER", "cusip": "other-cusip", "isin": None},
            "completion": {**judgment, "date": "2020-01-02", "no_studied_share_conversion": True, "no_outstanding_studied_entitlement": True}}]
    found = admission_fixture(store, profile, action_records=[("cash_mergers", record)], exclusions=exclusions)
    report = store.inspect()
    assert checked(report, found["ref"], "admission")
    matching = [edge for edge in report["edges"] if edge["digest"] == hashed(record)]
    assert matching and all(edge["edge_type"] == "inline_identity" for edge in matching)
    assert not (store.root / "data/objects" / (hashed(record) + ".bin")).exists()


@pytest.mark.parametrize("change", [lambda d: d["identity"].update(symbol="WRONG"),
    lambda d: d["sources"][0].update(url="https://wrong.test/source"),
    lambda d: d["identity"].update(source_sha256=d["sources"][0]["receipt_sha256"]),
    lambda d: d["coverage"].update(start="2024-06-09"),
    lambda d: d["identity"].update(judgment="x" * 8001)])
def test_attributed_facts_and_source_receipt_binding_contradictions_refuse(store, change):
    admission_fixture(store, mutate_facts=change)
    with pytest.raises(closure.ClosureError):
        store.inspect()


def test_semantic_review_finish_must_precede_admission_start(store):
    early = store.begin("historical_admission", {"unretained": "invented input identity"})
    found = policy_fixture(store)
    policy_admission(store, found, started_sid=early)
    with pytest.raises(closure.ClosureError, match="semantic_review_registration_order"):
        store.inspect()


def test_noncanonical_annotation_bytes_refuse_even_when_registered_hash_matches_bytes(store, monkeypatch):
    original = store.put
    def put(value):
        if type(value) is dict and value.get("profile") == "domestic_integer_forward_split_v1":
            return original(json.dumps(value, indent=2).encode())
        return original(value)
    monkeypatch.setattr(store, "put", put)
    policy_fixture(store)
    with pytest.raises(closure.ClosureError, match="noncanonical_annotation_identity|required_object_missing"):
        store.inspect()

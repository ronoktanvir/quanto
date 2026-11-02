"""Synthetic local memory checks; no runtime, credentials or network access."""
import hashlib
import json
import sqlite3

import pytest

from quanto.failure_memory import FailureMemory, FailureMemoryError, MAX_RESULTS, MAX_SCAN
from quanto.provenance import Provenance


def memory(store, **overrides):
    options = {"allowed_kinds": ["study", "experiment_attempt"],
               "allowed_codes": ["engine_rejected_input", "correction_recorded", "reopened"]}
    options.update(overrides)
    return FailureMemory(store, **options)


def failure(store, status="invalid", **details):
    identity = store.begin("study", {"fixture": True})
    store.finish(identity, status, {"error_code": "engine_rejected_input", **details})
    return identity


def test_failed_attempt_is_retained_after_fix_and_reopen(tmp_path):
    with Provenance(tmp_path) as store:
        fingerprint = store.journal.register_experiment(
            {"rule": "fixture"}, {"fixture": "data"}, {"revision": "fixture"}, "synthetic_fixture")
        attempt = store.journal.start_attempt(fingerprint)
        store.journal.finish_attempt(attempt, "failed", {"error_code": "engine_rejected_input"})
        fix = store.put_json({"kind": "synthetic_fixture", "corrected_code": True})
        service = memory(store, allowed_artifact_refs=[fix])
        correction = service.append_disposition("attempt", attempt, "corrected", fix)
        observed = service.query({"ids": [attempt]})["failures"][0]
        assert observed["status"] == "failed"
        assert observed["disposition"]["state"] == "corrected"
        assert observed["disposition"]["fix_artifact_ref"] == fix
        assert observed["fingerprint"] == fingerprint
        assert observed["evidence_kind"] == "synthetic_fixture"
        assert observed["code_identity_sha256"] == hashlib.sha256(b'{"revision":"fixture"}').hexdigest()
        assert service.query({"disposition": "unresolved"})["failures"] == []
        service.append_disposition("attempt", attempt, "unresolved", code="reopened")
        assert service.query({"ids": [attempt]})["failures"][0]["disposition"]["state"] == "unresolved"
        assert store.read_json(correction["receipt_sha256"])["fix_artifact_ref"] == fix
        assert store.journal.connection.execute("SELECT status FROM outcomes").fetchone()[0] == "failed"
        assert store.journal.connection.execute("SELECT COUNT(*) FROM failure_memory_dispositions").fetchone()[0] == 2
        for sql in ("DELETE FROM failure_memory_dispositions",
                    "UPDATE failure_memory_dispositions SET disposition='corrected'"):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                store.journal.connection.execute(sql)
        store.journal.verify_events()


def test_pending_is_current_and_success_exits_memory(tmp_path):
    with Provenance(tmp_path) as store:
        pending = store.begin("study", {})
        fingerprint = store.journal.register_experiment({}, "fixture-data", "fixture-code", "synthetic_fixture")
        attempt = store.journal.start_attempt(fingerprint)
        service = memory(store)
        initial = service.query({"statuses": ["pending"]})
        assert {row["id"] for row in initial["failures"]} == {pending, attempt}
        with pytest.raises(FailureMemoryError, match="refused"):
            service.append_disposition("submission", pending, "corrected", "a" * 64)
        artifact = store.put_json({"fixture": True})
        store.finish(pending, "success", {"artifact_refs": [artifact]})
        store.journal.finish_attempt(attempt, "invalid", {})
        assert service.query({"statuses": ["pending"]})["failures"] == []
        remaining = service.query({})["failures"]
        assert [row["id"] for row in remaining] == [attempt]
        assert remaining[0]["status"] == "invalid"


def test_query_receipt_records_exact_bounded_request_and_selected_ids(tmp_path):
    with Provenance(tmp_path) as store:
        bad = failure(store)
        service = memory(store)
        result = service.query({"codes": ["engine_rejected_input"], "limit": 1})
        saved = store.read_json(result["receipt_sha256"])
        assert saved["returned_ids"] == [{"source": "submission", "id": bad}]
        assert saved["query"]["limit"] == 1
        assert saved["query"]["codes"] == ["engine_rejected_input"]
        submission = store.get_submission(result["query_submission_id"])
        assert submission["status"] == "success"
        assert submission["details"]["artifact_refs"] == [result["receipt_sha256"]]
        assert submission["request_sha256"] == hashlib.sha256(
            b'{"codes":["engine_rejected_input"],"limit":1}').hexdigest()
        assert saved["provisional"] is True


@pytest.mark.parametrize("damage", ["missing", "corrupt", "tombstone"])
def test_unavailable_artifact_never_returned_as_verified(tmp_path, damage):
    with Provenance(tmp_path) as store:
        ref = store.put_json({"fixture": True})
        bad = failure(store, artifact_refs=[ref])
        service = memory(store, allowed_artifact_refs=[ref])
        assert service.query({"ids": [bad]})["failures"][0]["artifact_refs"] == [ref]
        path = tmp_path / "data/objects" / (ref + ".bin")
        if damage == "missing":
            path.unlink()
        elif damage == "corrupt":
            path.write_bytes(b"damaged synthetic bytes")
        else:
            store.tombstone(ref, "invalid_artifact")
        row = service.query({"ids": [bad]})["failures"][0]
        assert row["artifact_refs"] == []
        assert row["artifact_state"] == "unavailable"


def test_corrected_claim_does_not_hide_later_missing_fix(tmp_path):
    with Provenance(tmp_path) as store:
        bad = failure(store)
        fix = store.put_bytes(b"fixture fix")
        service = memory(store, allowed_artifact_refs=[fix])
        service.append_disposition("submission", bad, "corrected", fix)
        (tmp_path / "data/objects" / (fix + ".bin")).unlink()
        disposition = service.query({"ids": [bad]})["failures"][0]["disposition"]
        assert disposition["state"] == "corrected"  # Retained claim, not certified resolution.
        assert disposition["fix_artifact_ref"] is None
        assert disposition["artifact_state"] == "unavailable"
        assert store.get_submission(bad)["status"] == "invalid"


def test_no_raw_details_paths_values_or_nonallowlisted_metadata(tmp_path):
    with Provenance(tmp_path) as store:
        artifact = store.put_bytes(b"fixture private market values")
        bad = store.begin("private_strategy_name", {})
        store.finish(bad, "failed", {"error_code": "private_secret_name", "price": 123.456,
                                    "path": "/private/fixture", "text": "secret_payload",
                                    "artifact_refs": [artifact]})
        result = FailureMemory(store).query({})
        rendered = json.dumps(result)
        for forbidden in ("private_strategy_name", "private_secret_name", "123.456",
                          "/private/fixture", "secret_payload", artifact):
            assert forbidden not in rendered
        assert result["failures"][0]["kind"] == "undisclosed"
        assert result["failures"][0]["code"] == "undisclosed"
        assert result["failures"][0]["artifact_state"] == "not_allowed"
        assert FailureMemory(store).query({"keyword": "secret_payload"})["failures"] == []


@pytest.mark.parametrize("query_input", [
    {"sql": "DROP TABLE attempts"}, {"path": "/private/fixture"},
    {"limit": True}, {"limit": 0}, {"limit": MAX_RESULTS + 1},
    {"ids": ["' OR 1=1 --"]}, {"ids": ["a" * 32] * 33},
    {"keyword": "' OR 1=1 --"}, {"keyword": "x" * 65},
    {"statuses": ["success"]}, {"sources": []}, {"sources": [None]},
    {"disposition": []}, {"codes": ["unapproved"]}, {"kinds": ["unapproved"]},
    {"request_sha256": ["A" * 64]}, {"statuses": ["failed", "failed"]},
])
def test_invalid_query_refuses_before_creating_recursive_noise(tmp_path, query_input):
    with Provenance(tmp_path) as store:
        service = memory(store)
        with pytest.raises(FailureMemoryError):
            service.query(query_input)
        rows = store.list_submissions()
        assert len(rows) == 1 and rows[0]["status"] == "invalid"
        assert service.query({})["failures"] == []


def test_internal_pending_failed_and_invalid_operations_do_not_pollute_search(tmp_path):
    with Provenance(tmp_path) as store:
        bad = failure(store)
        for status in (None, "invalid", "failed"):
            identity = store.begin("failure_memory_query", {})
            if status:
                store.finish(identity, status, {})
        service = memory(store)
        for _ in range(3):
            assert [row["id"] for row in service.query({})["failures"]] == [bad]


def test_scan_and_result_bounds_are_explicit(tmp_path):
    with Provenance(tmp_path) as store:
        # Pending fixture submissions are enough to exercise bounds without outcomes.
        for _ in range(MAX_SCAN + 2):
            store.begin("study", {})
        result = memory(store).query({"limit": 2, "sources": ["submission"]})
        assert len(result["failures"]) == 2
        assert result["scanned_count"] == MAX_SCAN
        assert result["truncated"] is True


def test_exact_identifier_filters_apply_before_scan_bound(tmp_path):
    with Provenance(tmp_path) as store:
        old = failure(store)
        for _ in range(MAX_SCAN + 1):
            store.begin("study", {})
        result = memory(store).query({"ids": [old], "statuses": ["invalid"]})
        assert [row["id"] for row in result["failures"]] == [old]
        assert result["truncated"] is False


def test_malformed_or_large_stored_safe_fields_fail_closed(tmp_path):
    with Provenance(tmp_path) as store:
        bad = failure(store, error_code={"secret": "fixture"})
        service = memory(store)
        with pytest.raises(FailureMemoryError, match="memory_query_refused"):
            service.query({"ids": [bad]})
        receipt = store.list_submissions("failure_memory_query")[0]
        assert receipt["status"] == "invalid"
        assert receipt["details"] == {"error_code": "memory_query_refused"}
        huge = failure(store, error_code="x" * 257)
        with pytest.raises(FailureMemoryError):
            service.query({"ids": [huge]})
        assert service.query({"statuses": ["interrupted"]})["failures"] == []


def test_correction_refuses_success_unknown_pending_or_disallowed_artifact(tmp_path):
    with Provenance(tmp_path) as store:
        ref = store.put_bytes(b"fixture fix")
        successful = store.begin("study", {})
        store.finish(successful, "success", {"artifact_refs": [ref]})
        pending = store.begin("study", {})
        bad = failure(store)
        service = memory(store, allowed_artifact_refs=[ref])
        for identity in (successful, pending, "a" * 32):
            with pytest.raises(FailureMemoryError):
                service.append_disposition("submission", identity, "corrected", ref)
        for fix in (None, "b" * 64):
            with pytest.raises(FailureMemoryError):
                service.append_disposition("submission", bad, "corrected", fix)
        assert store.journal.connection.execute("SELECT COUNT(*) FROM failure_memory_dispositions").fetchone()[0] == 0
        assert [r["id"] for r in service.query({"statuses": ["invalid"]})["failures"]] == [bad]


def test_disposition_publication_failure_rolls_back_state(tmp_path, monkeypatch):
    with Provenance(tmp_path) as store:
        bad = failure(store)
        ref = store.put_bytes(b"fixture fix")
        service = memory(store, allowed_artifact_refs=[ref])
        real_finish = store.finish
        def broken_finish(identity, status, details):
            if status == "success":
                raise FailureMemoryError("fixture refusal")
            return real_finish(identity, status, details)
        monkeypatch.setattr(store, "finish", broken_finish)
        with pytest.raises(FailureMemoryError):
            service.append_disposition("submission", bad, "corrected", ref)
        assert store.journal.connection.execute("SELECT COUNT(*) FROM failure_memory_dispositions").fetchone()[0] == 0
        monkeypatch.setattr(store, "finish", real_finish)
        assert service.query({"ids": [bad]})["failures"][0]["disposition"]["state"] == "unresolved"


def test_artifact_verification_work_is_bounded_and_disclosed(tmp_path, monkeypatch):
    with Provenance(tmp_path) as store:
        refs = [store.put_bytes(f"fixture {i}".encode()) for i in range(12)]
        for _ in range(6):
            failure(store, artifact_refs=refs)
        service = memory(store, allowed_artifact_refs=refs)
        real_read, reads = store.read_bytes, []
        def counted_read(ref):
            reads.append(ref)
            return real_read(ref)
        monkeypatch.setattr(store, "read_bytes", counted_read)
        result = service.query({})
        # 32 approved object checks plus one Provenance.finish receipt check.
        assert len(reads) == 33
        assert sum(len(row["artifact_refs"]) for row in result["failures"]) == 32
        assert all(row["artifact_state"] == "verification_bound" for row in result["failures"])
        assert len(result["failures"][-1]["artifact_refs"]) == 0


def test_large_experiment_identity_refuses_without_disclosing_content(tmp_path):
    with Provenance(tmp_path) as store:
        fingerprint = store.journal.register_experiment(
            {}, "private-fixture" * 6000, "fixture-code", "synthetic_fixture")
        attempt = store.journal.start_attempt(fingerprint)
        store.journal.finish_attempt(attempt, "failed", {})
        with pytest.raises(FailureMemoryError, match="memory_query_refused"):
            memory(store).query({"ids": [attempt]})
        row = store.list_submissions("failure_memory_query")[0]
        assert row["status"] == "invalid"
        assert "private-fixture" not in json.dumps(row)


def test_oversized_unencodable_preflight_does_not_claim_record(tmp_path):
    with Provenance(tmp_path) as store:
        service = memory(store)
        for request_value in ({"keyword": "x" * 70000}, {"keyword": "\ud800"}):
            with pytest.raises(ValueError):
                service.query(request_value)
        assert store.list_submissions() == []


def test_keyword_matches_only_fixed_projected_identity_fields(tmp_path):
    with Provenance(tmp_path) as store:
        bad = failure(store, text="hiddenword")
        service = memory(store)
        assert service.query({"keyword": "hiddenword"})["failures"] == []
        assert [r["id"] for r in service.query({"keyword": "engine_rejected"})["failures"]] == [bad]
        request_hash = store.get_submission(bad)["request_sha256"]
        assert [r["id"] for r in service.query({"request_sha256": [request_hash]})["failures"]] == [bad]

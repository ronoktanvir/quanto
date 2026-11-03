"""Temporary synthetic SQLite stores only; no production data, keys or network."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import time

import pytest
from access_fixtures import synthetic_access as synthetic_access

from quanto import recovery
from quanto.ledger import Journal
from quanto.provenance import Provenance
from quanto import study_suite


@pytest.fixture
def store_paths(tmp_path, synthetic_access):
    source = tmp_path / "source"
    source.mkdir(mode=0o700)
    synthetic_access.bind(source)
    with Provenance(source) as store:
        live = store.put_json({"evidence_kind": "synthetic_fixture", "value": "invented"})
        submission = store.begin("synthetic_capture", {"not_stored": "request digest only"})
        store.finish(submission, "success", {"artifact_refs": [live]})
        store.begin("synthetic_pending", {})
    return source, tmp_path / "snapshot", live


def database(source):
    return source / "runtime/research.sqlite"


def capture(paths):
    source, snapshot, _ = paths
    result = recovery.capture_research_snapshot(source, snapshot)
    return result, json.loads((snapshot / "manifest.json").read_bytes())


def test_complete_database_preservation_and_inert_inspection(store_paths, monkeypatch):
    source, snapshot, live = store_paths
    now = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
    with Journal(database(source), clock=lambda: now) as journal:
        journal.reserve("old-uncertain", 123456)
        journal.authorize_dispatch("old-uncertain")
        journal.mark_uncertain("old-uncertain", "synthetic unknown")
        now += timedelta(days=1)
        journal.reserve("current-reserved", 777)
        journal.enqueue_job("unfinished", {"fixture": True})
        journal.claim_job("synthetic-worker")
    original = database(source).read_bytes()
    result, manifest = capture(store_paths)
    assert database(source).read_bytes() == original
    assert result["object_count"] == 1
    assert not result["full_recovery_accepted"] and not result["typed_closure_complete"]
    assert not result["execution_enabled"]
    assert manifest["coverage"]["known_required_refs"] == [live]
    with sqlite3.connect(database(source)) as src, sqlite3.connect(snapshot / "research.sqlite") as dst:
        for (table,) in src.execute("SELECT name FROM sqlite_schema WHERE type='table'"):
            assert src.execute('SELECT * FROM "' + table + '"').fetchall() == dst.execute('SELECT * FROM "' + table + '"').fetchall()
    before = {str(p.relative_to(snapshot)): p.read_bytes() for p in snapshot.rglob("*") if p.is_file()}
    monkeypatch.setattr(Journal, "__init__", lambda *_a, **_k: pytest.fail("initializer called"))
    monkeypatch.setattr(Provenance, "__init__", lambda *_a, **_k: pytest.fail("initializer called"))
    inspected = recovery.inspect_research_snapshot(snapshot, expected_manifest_sha256=result["manifest_sha256"], expected_event_head=result["event_head"])
    assert inspected == result
    assert before == {str(p.relative_to(snapshot)): p.read_bytes() for p in snapshot.rglob("*") if p.is_file()}


def test_live_orphan_and_tombstone_semantics(store_paths):
    source, snapshot, live = store_paths
    with Provenance(source) as store:
        orphan = store.put_bytes(b"orphan synthetic publication")
        dead = store.put_bytes(b"tombstoned synthetic evidence")
        submission = store.begin("synthetic_dead", {})
        store.finish(submission, "success", {"artifact_refs": [dead]})
        store.tombstone(dead, "operator_requested")
    result, manifest = capture(store_paths)
    assert set(manifest["objects"]) == {live, orphan}
    assert manifest["coverage"]["unavailable_tombstoned_refs"] == [dead]
    assert (source / "data/objects" / (dead + ".bin")).exists()
    assert not (snapshot / "objects" / (dead + ".bin")).exists()
    assert result["tombstoned_dependency_count"] == 1
    assert recovery.inspect_research_snapshot(snapshot)["full_recovery_accepted"] is False


@pytest.mark.parametrize("kind", ["missing", "corrupt"])
def test_missing_or_corrupt_live_object_preserves_failed_generation(store_paths, kind):
    source, snapshot, live = store_paths
    path = source / "data/objects" / (live + ".bin")
    if kind == "missing":
        path.unlink()
    else:
        path.write_bytes(b"damaged")
    with pytest.raises(recovery.RecoveryError):
        capture(store_paths)
    assert (snapshot / "failure.json").exists()
    assert not (snapshot / "manifest.json").exists()
    with pytest.raises(recovery.RecoveryError):
        recovery.inspect_research_snapshot(snapshot)


def test_unknown_table_rows_are_preserved_but_coverage_is_explicit(store_paths):
    source, snapshot, _ = store_paths
    with sqlite3.connect(database(source)) as db:
        db.execute("CREATE TABLE unknown_evidence (id INTEGER, missing_reference TEXT, raw BLOB)")
        db.execute("INSERT INTO unknown_evidence VALUES (?,?,?)", (1, "f" * 64, b"synthetic"))
    result, manifest = capture(store_paths)
    assert manifest["database_state"]["unknown_schema_tables"] == ["unknown_evidence"]
    assert manifest["database_state"]["tables"]["unknown_evidence"]["rows"] == 1
    assert result["unknown_schema_count"] == 1 and result["typed_closure_complete"] is False
    assert recovery.inspect_research_snapshot(snapshot)["full_recovery_accepted"] is False


def test_unknown_shape_of_known_reference_table_refuses(store_paths):
    source, snapshot, _ = store_paths
    with sqlite3.connect(database(source)) as db:
        db.execute("CREATE TABLE research_private_responses (artifact_sha256 TEXT)")
    with pytest.raises(recovery.RecoveryError, match="unsupported_reference_schema"):
        capture(store_paths)
    assert (snapshot / "failure.json").exists()


def test_acquisition_event_and_private_response_roots_are_checked(store_paths):
    source, _, _ = store_paths
    with Provenance(source) as store:
        orphan = store.put_bytes(b"synthetic page")
        store.journal.append_event("acquisition_page_received", {"raw_sha256": orphan})
    (source / "data/objects" / (orphan + ".bin")).unlink()
    with pytest.raises(recovery.RecoveryError, match="required_object_missing"):
        capture(store_paths)


def test_source_writer_timeout_is_bounded_and_lock_is_released(store_paths):
    source, snapshot, _ = store_paths
    with sqlite3.connect(database(source), isolation_level=None) as writer:
        writer.execute("BEGIN IMMEDIATE")
        started = time.monotonic()
        with pytest.raises(recovery.RecoveryError):
            recovery.capture_research_snapshot(source, snapshot, limits=replace(recovery.Limits(), lock_seconds=0.03))
        assert time.monotonic() - started < 2
        writer.execute("ROLLBACK")
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("ROLLBACK")
    assert (snapshot / "failure.json").exists()


def test_cooperating_writer_cannot_commit_during_object_capture(store_paths, monkeypatch):
    source, snapshot, _ = store_paths
    entered, attempted, complete = threading.Event(), threading.Event(), threading.Event()
    with sqlite3.connect(database(source)) as db:
        db.execute("CREATE TABLE concurrent_fixture (value INTEGER)")
    original = recovery._copy_object
    def paused(*args):
        entered.set()
        assert attempted.wait(2)
        time.sleep(0.05)
        assert not complete.is_set()
        return original(*args)
    def writer():
        assert entered.wait(2)
        with sqlite3.connect(database(source), timeout=3) as db:
            attempted.set()
            db.execute("INSERT INTO concurrent_fixture VALUES (1)")
        complete.set()
    monkeypatch.setattr(recovery, "_copy_object", paused)
    with ThreadPoolExecutor(max_workers=1) as pool:
        task = pool.submit(writer)
        capture(store_paths)
        task.result(timeout=3)
    with sqlite3.connect(snapshot / "research.sqlite") as db:
        assert db.execute("SELECT count(*) FROM concurrent_fixture").fetchone()[0] == 0
    assert complete.is_set()


def test_delayed_purge_can_only_remove_excluded_tombstone(store_paths, monkeypatch):
    source, snapshot, _ = store_paths
    with Provenance(source) as store:
        dead = store.put_bytes(b"synthetic delayed purge")
        store.tombstone(dead, "operator_requested")
    original = recovery._copy_object
    def purge_unlink(*args):
        (source / "data/objects" / (dead + ".bin")).unlink(missing_ok=True)
        return original(*args)
    monkeypatch.setattr(recovery, "_copy_object", purge_unlink)
    _, manifest = capture(store_paths)
    assert dead not in manifest["objects"]
    assert dead in manifest["coverage"]["tombstones"]
    assert recovery.inspect_research_snapshot(snapshot)["snapshot_bytes_verified"]


def test_cancellation_retains_failure_and_releases_source_writer(store_paths, monkeypatch):
    source, snapshot, _ = store_paths
    def interrupt(*_):
        raise KeyboardInterrupt
    monkeypatch.setattr(recovery, "_copy_object", interrupt)
    with pytest.raises(recovery.RecoveryError, match="capture_failed"):
        capture(store_paths)
    with sqlite3.connect(database(source), timeout=0.1, isolation_level=None) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("ROLLBACK")
    assert (snapshot / "failure.json").exists()
    assert not (snapshot / "manifest.json").exists()


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo", "name"])
def test_unsafe_objects_refuse(store_paths, tmp_path, kind):
    source, _, _ = store_paths
    directory = source / "data/objects"
    target = tmp_path / "unrelated"
    target.write_bytes(b"untouched")
    path = directory / ("f" * 64 + ".bin")
    if kind == "symlink":
        path.symlink_to(target)
    elif kind == "hardlink":
        os.link(target, path)
    elif kind == "fifo":
        os.mkfifo(path)
    else:
        path = directory / "unexpected.txt"
        path.write_bytes(b"unexpected")
    with pytest.raises(recovery.RecoveryError):
        capture(store_paths)
    assert target.read_bytes() == b"untouched"


def test_overlap_and_existing_destination_refuse_without_overwrite(store_paths):
    source, snapshot, _ = store_paths
    with pytest.raises(recovery.RecoveryError, match="source_destination_overlap"):
        recovery.capture_research_snapshot(source, source / "runtime/recovery")
    capture(store_paths)
    original = (snapshot / "manifest.json").read_bytes()
    with pytest.raises(recovery.RecoveryError):
        capture(store_paths)
    assert (snapshot / "manifest.json").read_bytes() == original
    assert not (snapshot / "failure.json").exists()


@pytest.mark.parametrize("changed", ["object", "database", "extra", "sidecar", "manifest", "linked_object"])
def test_inspection_refuses_tampering_and_unlisted_files(store_paths, changed):
    _, snapshot, live = store_paths
    capture(store_paths)
    if changed == "object":
        (snapshot / "objects" / (live + ".bin")).write_bytes(b"corrupt")
    elif changed == "database":
        with sqlite3.connect(snapshot / "research.sqlite") as db:
            db.execute("UPDATE reservations SET reserved_micro_usd=1")
            db.execute("CREATE TABLE extra (id INTEGER)")
    elif changed == "extra":
        (snapshot / "objects/extra.bin").write_bytes(b"extra")
    elif changed == "sidecar":
        (snapshot / "research.sqlite-wal").write_bytes(b"unknown")
    elif changed == "linked_object":
        path = snapshot / "objects" / (live + ".bin")
        path.unlink()
        path.symlink_to("/nonexistent")
    else:
        (snapshot / "manifest.json").write_bytes(b'{"format":"first","format":"second"}')
    with pytest.raises(recovery.RecoveryError):
        recovery.inspect_research_snapshot(snapshot)


def test_table_state_detects_materialized_change_even_with_updated_file_hash(store_paths):
    _, snapshot, _ = store_paths
    _, manifest = capture(store_paths)
    with sqlite3.connect(snapshot / "research.sqlite") as db:
        db.execute("INSERT INTO reservations VALUES ('forged','2026-01-01',10,NULL,'reserved','x','x')")
    raw = (snapshot / "research.sqlite").read_bytes()
    manifest["database"] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    (snapshot / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(recovery.RecoveryError, match="database_state_mismatch"):
        recovery.inspect_research_snapshot(snapshot)


def test_old_snapshot_is_valid_but_checkpoint_mismatch_refuses(store_paths):
    source, snapshot, _ = store_paths
    old, _ = capture(store_paths)
    with Journal(database(source)) as journal:
        new_head = journal.append_event("synthetic_later", {})
    assert recovery.inspect_research_snapshot(snapshot)["event_head"] == old["event_head"]
    with pytest.raises(recovery.RecoveryError, match="event_checkpoint_mismatch"):
        recovery.inspect_research_snapshot(snapshot, expected_event_head=new_head)
    with pytest.raises(recovery.RecoveryError, match="manifest_checkpoint_mismatch"):
        recovery.inspect_research_snapshot(snapshot, expected_manifest_sha256="0" * 64)


@pytest.mark.parametrize("limit", ["database_bytes", "object_bytes", "total_bytes", "rows", "manifest_bytes"])
def test_bounds_refuse_without_success(store_paths, limit):
    source, snapshot, _ = store_paths
    with pytest.raises(recovery.RecoveryError):
        recovery.capture_research_snapshot(source, snapshot, limits=replace(recovery.Limits(), **{limit: 1}))
    assert not (snapshot / "manifest.json").exists()


def test_unexpected_wal_mode_refuses_without_changing_source_mode(store_paths):
    source, _, _ = store_paths
    with sqlite3.connect(database(source)) as db:
        assert db.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    with pytest.raises(recovery.RecoveryError, match="unsupported_journal_mode"):
        capture(store_paths)
    with sqlite3.connect(database(source)) as db:
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_suite_launch_request_digest_is_inline_not_a_required_object(store_paths):
    source, snapshot, live = store_paths
    request = {"fixture": "inline member request"}
    request_hash = hashlib.sha256(recovery._json(request)).hexdigest()
    with Provenance(source) as store:
        study_suite._schema(store)
        roster = store.put_json({"members": [{"request": request, "request_sha256": request_hash}]})
        run_id = store.begin("synthetic_suite_run", {})
        with store.journal._transaction():
            store.journal.connection.execute("INSERT INTO study_suite_runs VALUES (?,?,?)", (run_id, live, roster))
            store.journal.connection.execute("INSERT INTO study_suite_launches VALUES (?,?,?)", (run_id, 10, request_hash))
    assert not (source / "data/objects" / (request_hash + ".bin")).exists()
    _, manifest = capture(store_paths)
    assert request_hash not in manifest["coverage"]["known_required_refs"]
    assert recovery.inspect_research_snapshot(snapshot)["typed_closure_complete"] is False


@pytest.mark.parametrize("key,value", [
    ("started_at", 1), ("finished_at", None), ("started_at", "2026-01-01T00:00:00"),
    ("finished_at", "1900-01-01T00:00:00+00:00"), ("producer_sha256", "not-a-digest"),
    ("consistency", "arbitrary"), ("unpublished_temporary_files_excluded", -99),
    ("unpublished_temporary_files_excluded", True), ("unpublished_temporary_files_excluded", 10001),
])
def test_manifest_metadata_is_typed_and_bounded(store_paths, key, value):
    _, snapshot, _ = store_paths
    _, manifest = capture(store_paths)
    manifest[key] = value
    (snapshot / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(recovery.RecoveryError, match="manifest_"):
        recovery.inspect_research_snapshot(snapshot)


def test_source_growth_rechecked_under_guard_before_audit(store_paths, monkeypatch):
    source, snapshot, _ = store_paths
    maximum = database(source).stat().st_size + 4096
    original = recovery._connect
    grew = False
    def grow_before_reader(path, mode, *args, **kwargs):
        nonlocal grew
        if mode == "ro" and not grew:
            grew = True
            with sqlite3.connect(database(source)) as writer:
                writer.execute("CREATE TABLE growth_fixture (raw BLOB)")
                writer.execute("INSERT INTO growth_fixture VALUES (zeroblob(131072))")
        return original(path, mode, *args, **kwargs)
    monkeypatch.setattr(recovery, "_connect", grow_before_reader)
    monkeypatch.setattr(recovery, "_audit", lambda *_: pytest.fail("oversized database reached audit"))
    with pytest.raises(recovery.RecoveryError, match="unsafe_file"):
        recovery.capture_research_snapshot(source, snapshot, limits=replace(recovery.Limits(), database_bytes=maximum))
    assert grew and not (snapshot / "research.sqlite").exists()


def test_hot_journal_refuses_without_recovering_source(store_paths, tmp_path):
    source, snapshot, _ = store_paths
    with sqlite3.connect(database(source)) as db:
        db.execute("CREATE TABLE crash_fixture (id INTEGER PRIMARY KEY, content BLOB)")
        db.executemany("INSERT INTO crash_fixture VALUES (?,zeroblob(4096))", [(i,) for i in range(300)])
    script = """import os,sqlite3,sys
db=sqlite3.connect(sys.argv[1],isolation_level=None)
db.execute('PRAGMA cache_size=5')
db.execute('PRAGMA synchronous=FULL')
db.execute('BEGIN IMMEDIATE')
db.execute('UPDATE crash_fixture SET content=randomblob(4096)')
os._exit(0)
"""
    subprocess.run([sys.executable, "-c", script, str(database(source))], check=True, timeout=10,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   env={"PATH": "/usr/bin:/bin", "LANG": "C"})
    journal = database(source).with_name("research.sqlite-journal")
    before_db, before_journal = database(source).read_bytes(), journal.read_bytes()
    assert before_journal[:8] != bytes(8)
    control = tmp_path / "control.sqlite"
    shutil.copyfile(database(source), control)
    shutil.copyfile(journal, control.with_name("control.sqlite-journal"))
    with sqlite3.connect(control) as db:
        assert db.execute("SELECT count(*) FROM crash_fixture WHERE content=zeroblob(4096)").fetchone()[0] == 300
    assert not control.with_name("control.sqlite-journal").exists()
    with pytest.raises(recovery.RecoveryError, match="capture_failed"):
        capture(store_paths)
    assert database(source).read_bytes() == before_db
    assert journal.read_bytes() == before_journal
    assert (snapshot / "failure.json").exists()
    assert not (snapshot / "manifest.json").exists()


@pytest.mark.parametrize("extension_api_present", [False, True])
def test_optional_extension_api_keeps_sql_authorizer_denial(store_paths, monkeypatch, extension_api_present):
    source, _, _ = store_paths
    connect = sqlite3.connect
    toggles = []
    class ConnectionProxy:
        def __init__(self, connection):
            self.connection = connection
        def __getattr__(self, name):
            if name == "enable_load_extension":
                if not extension_api_present:
                    raise AttributeError(name)
                def toggle(enabled):
                    toggles.append(enabled)
                    native = getattr(self.connection, name, None)
                    if native is not None:
                        native(enabled)
                return toggle
            return getattr(self.connection, name)
    monkeypatch.setattr(recovery.sqlite3, "connect", lambda *args, **kwargs: ConnectionProxy(connect(*args, **kwargs)))
    db = recovery._connect(database(source), "ro", time.monotonic() + 5)
    try:
        assert db.execute("SELECT count(*) FROM events").fetchone()[0] > 0
        with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
            db.execute("SELECT load_extension('/synthetic/never-loaded')")
        with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
            db.execute("DELETE FROM events")
    finally:
        db.close()
    assert toggles == ([False] if extension_api_present else [])

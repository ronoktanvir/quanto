"""Synthetic clocks and local files validate monitoring, never research performance."""

import copy
import json
import multiprocessing
import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from quanto import snapshots as snap


@pytest.fixture
def source():
    return {"schema_version": 1, "observed_at": "2026-10-01T10:00:00+00:00",
            "project": {"name": "Synthetic fixture", "phase": "test", "summary": "Software only",
                        "repository_url": "https://example.com/fixture"},
            "agents": [{"id": "fixture", "name": "Worker", "role": "Test", "model": "fixture",
                        "status": "working", "task": "Test", "detail": "Recorded observation",
                        "observed_at": "2026-10-01T09:00:00+00:00"}],
            "milestones": [], "events": [], "decisions": [], "blockers": [],
            "budget": {"scope": "synthetic_fixture", "timezone": "UTC", "daily_limit_usd": 20,
                       "spent_usd": None, "reserved_usd": None}}


def observation(now):
    return {"schema_version": 1, "service": "quanto", "checked_at": snap.timestamp(now),
            "service_state": "healthy", "reason": "health_ok", "readiness_state": "ready",
            "readiness_reason": "readiness_ok", "private_extra": "must not enter service capture"}


def write_source(root, source):
    runtime = root / "runtime"
    runtime.mkdir(exist_ok=True)
    (runtime / "status.json").write_text(json.dumps(source))


def monitor(root, now, **overrides):
    data = observation(now) | overrides
    (root / "runtime" / "operations.json").write_text(json.dumps(data))
    return data


def stored(root):
    return json.loads((root / "runtime" / snap.STATE_FILE).read_text())


def test_immediate_first_capture_and_exact_persisted_five_minute_schedule(tmp_path, source):
    write_source(tmp_path, source)
    before = (tmp_path / "runtime/status.json").read_bytes()
    service = monitor(tmp_path, 1000)
    assert snap.capture_due(tmp_path, service, now=1000)["status"] == "success"
    first = stored(tmp_path)
    assert first["last_success_at"] == snap.timestamp(1000)
    assert first["next_attempt_at"] == snap.timestamp(1300)
    assert first["latest_capture"]["status"] == source
    assert "private_extra" not in first["latest_capture"]["service"]
    assert snap.capture_due(tmp_path, service, now=1299)["status"] == "waiting"
    assert stored(tmp_path) == first
    # No in-memory scheduler object: this next call is also a process restart model.
    assert snap.capture_due(tmp_path, monitor(tmp_path, 1300), now=1300)["status"] == "success"
    second = stored(tmp_path)
    assert second["next_attempt_at"] == snap.timestamp(1600)
    assert len(second["history"]) == 2
    assert second["latest_capture"]["status"] == source
    assert second["source_observed_at"] == source["observed_at"]
    assert (tmp_path / "runtime/status.json").read_bytes() == before
    report = snap.snapshot_status(tmp_path, now=1301)
    assert report["status"] == "current" and report["interval_seconds"] == 300
    assert report["server_time"] == snap.timestamp(1301)


def test_sleep_gap_gets_one_capture_and_no_catch_up_burst(tmp_path, source):
    write_source(tmp_path, source)
    snap.capture_due(tmp_path, monitor(tmp_path, 1000), now=1000)
    stale = snap.snapshot_status(tmp_path, now=5000)
    assert stale["status"] == "delayed" and stale["reason"] == "monitor_stale"
    assert stale["next_attempt_at"] is None
    assert stale["scheduled_attempt_at"] == snap.timestamp(1300)
    snap.capture_due(tmp_path, monitor(tmp_path, 5000), now=5000)
    assert len(stored(tmp_path)["history"]) == 2
    assert stored(tmp_path)["next_attempt_at"] == snap.timestamp(5300)
    assert snap.capture_due(tmp_path, observation(5001), now=5001)["status"] == "waiting"


def test_failed_capture_preserves_success_and_waits_until_next_interval(tmp_path, source):
    write_source(tmp_path, source)
    snap.capture_due(tmp_path, monitor(tmp_path, 1000), now=1000)
    first = stored(tmp_path)["latest_capture"]
    (tmp_path / "runtime/status.json").write_text('{"private_error": "must not leak"}')
    assert snap.capture_due(tmp_path, monitor(tmp_path, 1300), now=1300) == {
        "status": "failure", "reason": "source_invalid"}
    failed = stored(tmp_path)
    assert failed["latest_capture"] == first
    assert failed["last_success_at"] == snap.timestamp(1000)
    assert failed["last_attempt_at"] == snap.timestamp(1300)
    assert failed["next_attempt_at"] == snap.timestamp(1600)
    report = snap.snapshot_status(tmp_path, now=1301)
    assert report["last_result"] == "failure" and report["status"] == "error"
    assert report["error"] == "source_invalid" and "must not leak" not in json.dumps(report)
    write_source(tmp_path, source)
    assert snap.capture_due(tmp_path, observation(1302), now=1302)["status"] == "waiting"
    assert snap.capture_due(tmp_path, monitor(tmp_path, 1600), now=1600)["status"] == "success"


def test_initial_failure_does_not_claim_a_success(tmp_path):
    assert snap.capture_due(tmp_path, observation(1000), now=1000) == {
        "status": "failure", "reason": "source_missing"}
    monitor(tmp_path, 1000)
    report = snap.snapshot_status(tmp_path, now=1001)
    assert report["last_success_at"] is None and report["source_observed_at"] is None
    assert report["next_attempt_at"] == snap.timestamp(1300)


def test_interrupted_attempt_preserves_success_and_resumes_at_persisted_deadline(
    tmp_path, source, monkeypatch
):
    write_source(tmp_path, source)
    snap.capture_due(tmp_path, monitor(tmp_path, 1000), now=1000)
    first = stored(tmp_path)["latest_capture"]
    with monkeypatch.context() as patch:
        patch.setattr(snap, "_capture", Mock(side_effect=KeyboardInterrupt))
        with pytest.raises(KeyboardInterrupt):
            snap.capture_due(tmp_path, monitor(tmp_path, 1300), now=1300)
    pending = snap.snapshot_status(tmp_path, now=1301)
    assert pending["last_result"] == "pending" and pending["status"] == "capturing"
    assert snap.capture_due(tmp_path, observation(1310), now=1310)["status"] == "waiting"
    interrupted = stored(tmp_path)
    assert interrupted["latest_capture"] == first
    assert interrupted["error"] == "capture_interrupted"
    assert interrupted["next_attempt_at"] == snap.timestamp(1600)
    assert snap.capture_due(tmp_path, monitor(tmp_path, 1600), now=1600)["status"] == "success"
    assert len(stored(tmp_path)["history"]) == 3


@pytest.mark.parametrize("raw", [b"{", b"[]", b"null", b'{"schema_version":1}',
                                  b'x' * (snap.MAX_STATE_BYTES + 1)])
def test_corrupt_metadata_fails_closed_without_inventing_deadlines(tmp_path, raw):
    (tmp_path / "runtime").mkdir()
    path = tmp_path / "runtime" / snap.STATE_FILE
    path.write_bytes(raw)
    assert snap.capture_due(tmp_path, observation(1000), now=1000)["status"] == "error"
    assert path.read_bytes() == raw
    report = snap.snapshot_status(tmp_path, now=1001)
    assert report["status"] == "error" and report["next_attempt_at"] is None
    assert report["last_success_at"] is None


@pytest.mark.parametrize("mutate", [
    lambda state: state.update(next_attempt_at=snap.timestamp(1301)),
    lambda state: state.update(last_success_at=snap.timestamp(999)),
    lambda state: state.pop("source_observed_at"),
    lambda state: state["history"][-1].update(result="failure"),
])
def test_inconsistent_metadata_is_not_repaired_by_resetting_schedule(tmp_path, source, mutate):
    write_source(tmp_path, source)
    snap.capture_due(tmp_path, monitor(tmp_path, 1000), now=1000)
    state = stored(tmp_path)
    mutate(state)
    path = tmp_path / "runtime" / snap.STATE_FILE
    path.write_text(json.dumps(state))
    assert snap.capture_due(tmp_path, observation(1300), now=1300)["status"] == "error"
    assert snap.snapshot_status(tmp_path, now=1301)["next_attempt_at"] is None


@pytest.mark.parametrize("value", [[], None, "secret text", 123, {}, {"checked_at": "naive"}])
def test_malformed_monitor_types_are_safe_and_disable_active_deadline(tmp_path, source, value):
    write_source(tmp_path, source)
    snap.capture_due(tmp_path, observation(1000), now=1000)
    (tmp_path / "runtime/operations.json").write_text(json.dumps(value))
    report = snap.snapshot_status(tmp_path, now=1001)
    assert report["status"] == "stopped" and report["next_attempt_at"] is None
    assert report["last_success_at"] == snap.timestamp(1000)
    assert "secret text" not in json.dumps(report)


def test_missing_stopped_and_backwards_clock_are_not_claimed_current(tmp_path, source):
    write_source(tmp_path, source)
    snap.capture_due(tmp_path, observation(1000), now=1000)
    assert snap.snapshot_status(tmp_path, now=1000)["reason"] == "monitor_missing_or_invalid"
    monitor(tmp_path, 1001, service_state="supervisor_stopped")
    assert snap.snapshot_status(tmp_path, now=1002)["status"] == "stopped"
    monitor(tmp_path, 1000)
    clock = snap.snapshot_status(tmp_path, now=990)
    assert clock["error"] == "clock_invalid" and clock["next_attempt_at"] is None
    assert snap.capture_due(tmp_path, observation(990), now=990)["status"] == "waiting"
    assert len(stored(tmp_path)["history"]) == 1


def test_readonly_missing_status_creates_nothing(tmp_path):
    before = list(tmp_path.iterdir())
    result = snap.snapshot_status(tmp_path, now=1000)
    assert result["status"] == "never_started"
    assert result["last_success_at"] is None and result["next_attempt_at"] is None
    assert list(tmp_path.iterdir()) == before


@pytest.mark.parametrize("kind", ["symlink", "directory", "fifo", "oversized"])
def test_unsafe_sources_fail_without_reading_special_files(tmp_path, source, kind):
    write_source(tmp_path, source)
    path = tmp_path / "runtime/status.json"
    path.unlink()
    if kind == "symlink":
        target = tmp_path / "unrelated.json"
        target.write_text(json.dumps(source))
        path.symlink_to(target)
    elif kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path)
    else:
        path.write_bytes(b"x" * (snap.MAX_SOURCE_BYTES + 1))
    assert snap.capture_due(tmp_path, observation(1000), now=1000)["status"] == "failure"
    state = stored(tmp_path)
    assert state["last_success_at"] is None
    assert state["error"] == ("source_oversized" if kind == "oversized" else "source_unsafe")


@pytest.mark.parametrize("part", ["root", "runtime", "metadata", "lock"])
def test_symlink_storage_is_rejected(tmp_path, source, part):
    root = tmp_path / "project"
    root.mkdir()
    write_source(root, source)
    if part == "root":
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        root = alias
    elif part == "runtime":
        (root / "runtime").rename(tmp_path / "outside")
        (root / "runtime").symlink_to(tmp_path / "outside", target_is_directory=True)
    else:
        target = tmp_path / "outside-file"
        target.write_text("private fixture")
        (root / "runtime" / (snap.STATE_FILE if part == "metadata" else snap.LOCK_FILE)).symlink_to(target)
    assert snap.capture_due(root, observation(1000), now=1000)["status"] == "error"
    if part != "lock":
        assert snap.snapshot_status(root, now=1000)["status"] == "error"
    if part in {"metadata", "lock"}:
        assert target.read_text() == "private fixture"


def _competing_capture(root, event, results):
    event.wait(5)
    results.put(snap.capture_due(Path(root), observation(1000), now=1000)["status"])


def test_process_lock_prevents_duplicate_attempts(tmp_path, source):
    write_source(tmp_path, source)
    context = multiprocessing.get_context("spawn")
    event, results = context.Event(), context.Queue()
    processes = [context.Process(target=_competing_capture, args=(str(tmp_path), event, results))
                 for _ in range(2)]
    for process in processes:
        process.start()
    event.set()
    outcomes = [results.get(timeout=10) for _ in processes]
    for process in processes:
        process.join(timeout=10)
        assert process.exitcode == 0
    assert outcomes.count("success") == 1
    assert set(outcomes) <= {"success", "waiting", "busy"}
    assert len(stored(tmp_path)["history"]) == 1


def test_history_and_capture_retention_are_bounded(tmp_path, source):
    write_source(tmp_path, source)
    original = copy.deepcopy(source)
    for index in range(snap.HISTORY_LIMIT + 3):
        now = 1000 + 300 * index
        assert snap.capture_due(tmp_path, observation(now), now=now)["status"] == "success"
    state = stored(tmp_path)
    assert len(state["history"]) == snap.HISTORY_LIMIT
    assert state["latest_capture"]["status"] == original
    files = {path.name for path in (tmp_path / "runtime").iterdir()}
    assert files == {"status.json", snap.STATE_FILE, snap.LOCK_FILE}
    assert (tmp_path / "runtime" / snap.STATE_FILE).stat().st_size <= snap.MAX_STATE_BYTES

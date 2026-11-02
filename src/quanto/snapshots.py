"""Bounded local website captures; observing work never advances its timestamps."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import math
import os
from pathlib import Path
import stat
import time
import uuid

INTERVAL_SECONDS = 300
MONITOR_STALE_SECONDS = 90
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_STATE_BYTES = MAX_SOURCE_BYTES + 128 * 1024
HISTORY_LIMIT = 60
STATE_FILE = "website-snapshots.json"
LOCK_FILE = "website-snapshots.lock"
ERRORS = {
    "source_missing", "source_invalid", "source_unsafe", "source_oversized",
    "service_observation_invalid", "capture_interrupted", "capture_storage_unavailable",
}


class SnapshotError(ValueError):
    """Only fixed categories cross the public status boundary."""


def timestamp(now: float) -> str:
    return datetime.fromtimestamp(now, timezone.utc).isoformat()


def _epoch(value: object) -> float:
    if not isinstance(value, str):
        raise ValueError("Invalid timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp needs timezone")
    return parsed.timestamp()


def _json(raw: bytes):
    def reject(value):
        raise ValueError("Non-finite JSON")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON field")
            result[key] = value
        return result

    return json.loads(raw, parse_constant=reject, object_pairs_hook=unique)


@contextmanager
def _directory(root: Path, *, create=False):
    """Hold directory descriptors so replacement paths cannot redirect a capture."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    root_fd = os.open(root, flags)
    try:
        if create:
            try:
                os.mkdir("runtime", mode=0o700, dir_fd=root_fd)
            except FileExistsError:
                pass
        runtime_fd = os.open("runtime", flags, dir_fd=root_fd)
        try:
            yield runtime_fd
        finally:
            os.close(runtime_fd)
    finally:
        os.close(root_fd)


def _read(directory: int, name: str, limit: int, category: str) -> bytes:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        descriptor = os.open(name, flags, dir_fd=directory)
    except FileNotFoundError:
        raise
    except OSError:
        raise SnapshotError(category + "_unsafe") from None
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        os.close(descriptor)
        raise SnapshotError(category + ("_unsafe" if not stat.S_ISREG(info.st_mode) else "_oversized"))
    with os.fdopen(descriptor, "rb") as source:
        raw = source.read(limit + 1)
        if len(raw) > limit:
            raise SnapshotError(category + "_oversized")
        return raw


def _write(directory: int, state: dict) -> None:
    raw = json.dumps(state, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
    if len(raw) > MAX_STATE_BYTES:
        raise SnapshotError("capture_storage_unavailable")
    # Never replace an unexpected symlink or special file, even though rename
    # itself would not follow it. Unique temporary files cannot collide.
    try:
        target = os.stat(STATE_FILE, dir_fd=directory, follow_symlinks=False)
        if not stat.S_ISREG(target.st_mode) or target.st_size > MAX_STATE_BYTES:
            raise SnapshotError("metadata_invalid")
    except FileNotFoundError:
        pass
    temporary = ".website-snapshots-" + uuid.uuid4().hex + ".tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, STATE_FILE, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass


def _service(observation: object) -> dict:
    if not isinstance(observation, dict):
        raise SnapshotError("service_observation_invalid")
    try:
        _epoch(observation.get("checked_at"))
    except (ValueError, TypeError, OverflowError):
        raise SnapshotError("service_observation_invalid") from None
    result = {"checked_at": observation["checked_at"]}
    for key in ("service_state", "reason", "readiness_state", "readiness_reason"):
        value = observation.get(key)
        if not isinstance(value, str) or not value or len(value) > 120:
            raise SnapshotError("service_observation_invalid")
        result[key] = value
    return result


def _validate(state: object) -> None:
    # This is a persisted schedule, not a hint: invalid metadata cannot reset it.
    required = {"schema_version", "interval_seconds", "last_attempt_at", "last_success_at",
                "next_attempt_at", "source_observed_at", "last_result", "error",
                "latest_capture", "history"}
    if (not isinstance(state, dict) or not required.issubset(state)
            or state.get("schema_version") != 1
            or state.get("interval_seconds") != INTERVAL_SECONDS
            or state.get("last_result") not in {"pending", "success", "failure"}):
        raise ValueError("Invalid snapshot metadata")
    attempted = _epoch(state.get("last_attempt_at"))
    if _epoch(state.get("next_attempt_at")) != attempted + INTERVAL_SECONDS:
        raise ValueError("Invalid snapshot deadline")
    error = state.get("error")
    if ((state["last_result"] == "failure" and error not in ERRORS)
            or (state["last_result"] != "failure" and error is not None)):
        raise ValueError("Invalid snapshot result")
    latest = state.get("latest_capture")
    if latest is None:
        if state.get("last_success_at") is not None or state.get("source_observed_at") is not None:
            raise ValueError("Missing successful capture")
    else:
        from quanto.dashboard import validate_status
        if not isinstance(latest, dict):
            raise ValueError("Invalid successful capture")
        validate_status(latest.get("status"))
        _service(latest.get("service"))
        if (_epoch(latest.get("captured_at")) > attempted
                or latest["captured_at"] != state.get("last_success_at")
                or latest["status"]["observed_at"] != state.get("source_observed_at")):
            raise ValueError("Capture metadata does not match its evidence")
    if state["last_result"] == "success" and state.get("last_success_at") != state["last_attempt_at"]:
        raise ValueError("Success lacks matching capture")
    history = state.get("history")
    if not isinstance(history, list) or not 1 <= len(history) <= HISTORY_LIMIT:
        raise ValueError("Invalid attempt history")
    prior = None
    for entry in history:
        if not isinstance(entry, dict):
            raise ValueError("Invalid attempt history")
        current = _epoch(entry.get("attempted_at"))
        if (prior is not None and current < prior + INTERVAL_SECONDS
                or entry.get("result") not in {"pending", "success", "failure"}
                or (entry.get("result") == "failure" and entry.get("error") not in ERRORS)
                or (entry.get("result") != "failure" and entry.get("error") is not None)):
            raise ValueError("Invalid attempt history")
        prior = current
    if (history[-1]["attempted_at"] != state["last_attempt_at"]
            or history[-1]["result"] != state["last_result"]
            or history[-1].get("error") != error):
        raise ValueError("Attempt history does not match metadata")


def _load(directory: int) -> dict | None:
    try:
        raw = _read(directory, STATE_FILE, MAX_STATE_BYTES, "metadata")
    except FileNotFoundError:
        return None
    try:
        state = _json(raw)
        _validate(state)
        return state
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError, KeyError):
        raise SnapshotError("metadata_invalid") from None


def _capture(directory: int, observation: dict, now: float) -> dict:
    from quanto.dashboard import validate_status
    try:
        raw = _read(directory, "status.json", MAX_SOURCE_BYTES, "source")
    except FileNotFoundError:
        raise SnapshotError("source_missing") from None
    try:
        data = _json(raw)
        validate_status(data)
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        raise SnapshotError("source_invalid") from None
    return {"captured_at": timestamp(now), "status": data, "service": _service(observation)}


def _open_lock(directory: int) -> int:
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        return os.open(LOCK_FILE, flags | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory)
    except FileExistsError:
        return os.open(LOCK_FILE, flags, dir_fd=directory)


def capture_due(root: Path, observation: dict, *, now: float | None = None) -> dict:
    """Attempt at most once per persisted deadline; no browser, network, or model calls."""
    now = time.time() if now is None else now
    if not math.isfinite(now):
        return {"status": "error", "reason": "clock_invalid"}
    try:
        with _directory(Path(root), create=True) as directory:
            lock = _open_lock(directory)
            try:
                lock_info = os.fstat(lock)
                if not stat.S_ISREG(lock_info.st_mode) or lock_info.st_size > 1024:
                    raise SnapshotError("lock_invalid")
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    return {"status": "busy", "reason": "capture_in_progress"}
                state = _load(directory)
                if state and state["last_result"] == "pending":
                    # A previous process lost its claim. Retain its deadline and
                    # last success; never replay that attempt or rush its retry.
                    state.update(last_result="failure", error="capture_interrupted")
                    state["history"][-1].update(result="failure", error="capture_interrupted")
                    _write(directory, state)
                if state and now < _epoch(state["next_attempt_at"]):
                    return {"status": "waiting", "reason": "scheduled"}
                if state is None:
                    state = {"schema_version": 1, "interval_seconds": INTERVAL_SECONDS,
                             "last_success_at": None, "source_observed_at": None,
                             "latest_capture": None, "history": []}
                state.update(last_attempt_at=timestamp(now),
                             next_attempt_at=timestamp(now + INTERVAL_SECONDS),
                             last_result="pending", error=None)
                state["history"] = (state["history"] + [{
                    "attempted_at": timestamp(now), "result": "pending", "error": None,
                }])[-HISTORY_LIMIT:]
                _write(directory, state)  # Durable claim precedes reading/capturing.
                try:
                    captured = _capture(directory, observation, now)
                    state.update(latest_capture=captured, last_success_at=timestamp(now),
                                 source_observed_at=captured["status"]["observed_at"],
                                 last_result="success")
                except (SnapshotError, OSError) as exc:
                    error = str(exc) if isinstance(exc, SnapshotError) else "source_invalid"
                    state.update(last_result="failure", error=error)
                state["history"][-1].update(result=state["last_result"], error=state["error"])
                _write(directory, state)
                return {"status": state["last_result"], "reason": state["error"]}
            finally:
                os.close(lock)
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        return {"status": "error", "reason": "snapshot_storage_invalid_or_unavailable"}


def snapshot_status(root: Path, *, now: float | None = None) -> dict:
    """Read authoritative capture metadata without creating files or sessions."""
    now = time.time() if now is None else now
    result = {"interval_seconds": INTERVAL_SECONDS, "last_attempt_at": None,
              "last_success_at": None, "next_attempt_at": None, "source_observed_at": None,
              "last_result": None, "status": "never_started", "reason": "monitor_not_started",
              "error": None, "server_time": timestamp(now), "monitor_checked_at": None,
              "scheduled_attempt_at": None}
    try:
        with _directory(Path(root)) as directory:
            state = _load(directory)
            if state is None:
                return result
            for key in ("last_attempt_at", "last_success_at", "next_attempt_at",
                        "source_observed_at", "last_result", "error"):
                result[key] = state[key]
            result["scheduled_attempt_at"] = state["next_attempt_at"]
            try:
                operations = _json(_read(directory, "operations.json", 1_000_000, "monitor"))
                if not isinstance(operations, dict):
                    raise ValueError("Invalid monitor")
                checked = _epoch(operations.get("checked_at"))
                if operations.get("schema_version") != 1 or operations.get("service") != "quanto":
                    raise ValueError("Invalid monitor")
            except (OSError, ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
                result.update(status="stopped", reason="monitor_missing_or_invalid",
                              next_attempt_at=None)
                return result
            result["monitor_checked_at"] = operations["checked_at"]
            if operations.get("service_state") == "supervisor_stopped":
                result.update(status="stopped", reason="monitor_stopped", next_attempt_at=None)
            elif now < checked or now < _epoch(state["last_attempt_at"]):
                result.update(status="error", reason="clock_moved_backwards", error="clock_invalid",
                              next_attempt_at=None)
            elif now - checked > MONITOR_STALE_SECONDS:
                result.update(status="delayed", reason="monitor_stale", next_attempt_at=None)
            elif now >= _epoch(state["next_attempt_at"]):
                result.update(status="delayed", reason="capture_due")
            elif state["last_result"] == "failure":
                result.update(status="error", reason="last_attempt_failed")
            elif state["last_result"] == "pending":
                result.update(status="capturing", reason="attempt_pending_or_interrupted")
            else:
                result.update(status="current", reason="scheduled")
            return result
    except FileNotFoundError:
        return result
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        result.update(status="error", reason="snapshot_metadata_invalid_or_unavailable",
                      error="snapshot_metadata_invalid_or_unavailable")
        return result

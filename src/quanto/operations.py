"""Bounded supervision of the local dashboard; never runs research or model commands."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
import fcntl
import hashlib
import json
import os
from pathlib import Path
from queue import SimpleQueue
import signal
import socket
import subprocess
import sys
import threading
import time
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import uuid
from zoneinfo import ZoneInfo

from quanto.snapshots import capture_due

INTERVAL = 10
TIMEOUT = 2
STARTUP_GRACE = 10
FAILURE_LIMIT = 3
MAX_RESTARTS = 5
DIAGNOSIS_RESERVATION_MICRO_USD = 125_000
AWAKE_LIMITATION = (
    "Local checks run only while this Mac is awake, signed in, and the supervisor runs. "
    "Sleep, shutdown, logout, and missing observations are gaps, not continuous uptime."
)


def timestamp(now: float) -> str:
    return datetime.fromtimestamp(now, timezone.utc).isoformat()


def new_state() -> dict:
    return {
        "schema_version": 1, "service": "quanto", "checked_at": None,
        "last_success": None, "service_state": "unknown", "reason": "not_checked",
        "restart_timestamps": [], "restarts": 0, "consecutive_failures": 0,
        "next_restart_at": 0, "recent_checks": [], "observation_gaps": [],
        "diagnosis_attempts": [], "diagnosis": {"status": "not_requested"},
        "awake_host_limitation": AWAKE_LIMITATION,
    }


def observe(state: dict, healthy: bool, reason: str, now: float, *, owned: bool) -> dict:
    """Record an observation without changing research or agent observation times."""
    previous = state.get("checked_at")
    if previous:
        elapsed = now - datetime.fromisoformat(previous).timestamp()
        if elapsed > INTERVAL * 3 or elapsed < 0:
            state["observation_gaps"] = (state.get("observation_gaps", []) + [{
                "from": previous, "to": timestamp(now),
                "seconds": round(elapsed, 3), "reason": "missing_checks_or_clock_change",
            }])[-50:]
    state["checked_at"] = timestamp(now)
    state["reason"] = reason
    state["ownership"] = "owned_child" if owned else "external_or_unknown"
    state["recent_checks"] = (state.get("recent_checks", []) + [{
        "checked_at": timestamp(now), "healthy": healthy, "reason": reason,
    }])[-60:]
    if healthy:
        state["last_success"] = timestamp(now)
        state["consecutive_failures"] = 0
        state["service_state"] = "healthy" if owned else "healthy_external"
    else:
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        state["service_state"] = "unhealthy" if owned else "unavailable"
    state["restart_timestamps"] = [
        value for value in state.get("restart_timestamps", []) if value > now - 3600
    ]
    state["restarts_last_hour"] = len(state["restart_timestamps"])
    return state


def reserve_restart(state: dict, now: float) -> bool:
    """Reserve before spawning, retaining circuit history across supervisor restarts."""
    state["restart_timestamps"] = [
        value for value in state.get("restart_timestamps", []) if value > now - 3600
    ]
    if len(state["restart_timestamps"]) >= MAX_RESTARTS:
        state["service_state"] = "restart_circuit_open"
        state["reason"] = "five_restarts_in_one_hour"
        return False
    if now < state.get("next_restart_at", 0):
        state["service_state"] = "restart_backoff"
        return False
    state["restart_timestamps"].append(now)
    state["restarts"] = state.get("restarts", 0) + 1
    state["restarts_last_hour"] = len(state["restart_timestamps"])
    state["next_restart_at"] = now + min(300, 30 * 2 ** (len(state["restart_timestamps"]) - 1))
    return True


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check_health(port: int) -> tuple[bool, str]:
    """Require Quanto's exact bounded health envelope; never follow redirects."""
    request = Request(f"http://127.0.0.1:{port}/health")
    try:
        with build_opener(ProxyHandler({}), _NoRedirect()).open(request, timeout=TIMEOUT) as response:
            raw = response.read(4097)
            if response.status != 200 or len(raw) > 4096:
                return False, "invalid_health_response"
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("service") == "quanto" and data.get("status") == "ok":
            return True, "health_ok"
        return False, "unrecognized_health_response"
    except TimeoutError:
        return False, "health_timeout"
    except (OSError, ValueError, UnicodeError):
        return False, "health_unavailable"


def check_readiness(port: int) -> tuple[bool, str]:
    """Check website inputs separately; a bad snapshot is not a restart trigger."""
    request = Request(f"http://127.0.0.1:{port}/ready")
    try:
        with build_opener(ProxyHandler({}), _NoRedirect()).open(request, timeout=TIMEOUT) as response:
            raw = response.read(4097)
            if response.status != 200 or len(raw) > 4096:
                return False, "readiness_invalid"
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("service") == "quanto" and data.get("status") == "ready":
            return True, "readiness_ok"
        return False, "readiness_invalid"
    except (OSError, ValueError, UnicodeError):
        return False, "readiness_unavailable"


def port_occupied(port: int) -> bool:
    with socket.socket() as connection:
        connection.settimeout(TIMEOUT)
        return connection.connect_ex(("127.0.0.1", port)) == 0


def _runtime(root: Path) -> Path:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Project root must be a regular local directory")
    runtime = root / "runtime"
    if runtime.is_symlink():
        raise ValueError("Runtime directory must not be a symlink")
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    return runtime


@contextmanager
def supervisor_lock(runtime: Path):
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(runtime / "operations.lock", flags, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("A Quanto supervisor already owns this runtime") from None
        yield
    finally:
        os.close(descriptor)


def load_state(runtime: Path) -> dict:
    path = runtime / "operations.json"
    if not path.exists():
        return new_state()
    if path.is_symlink() or path.stat().st_size > 1_000_000:
        raise ValueError("Operations state must be a bounded regular file")
    state = json.loads(path.read_text())
    # Corrupt state must not silently reset spending or restart circuits.
    if not isinstance(state, dict) or state.get("schema_version") != 1:
        raise ValueError("Operations state is invalid; operator repair is required")
    for field in ("restart_timestamps", "diagnosis_attempts", "recent_checks", "observation_gaps"):
        if not isinstance(state.get(field), list):
            raise ValueError("Operations history is invalid; operator repair is required")
    return state


def save_state(runtime: Path, state: dict) -> None:
    temporary = runtime / "operations.json.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC |
                         getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "w") as output:
        json.dump(state, output, indent=2, allow_nan=False)
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(runtime / "operations.json")


def diagnosis_eligible(state: dict, fingerprint: str, now: float) -> bool:
    attempts = state.get("diagnosis_attempts", [])
    if any(item["fingerprint"] == fingerprint for item in attempts):
        return False
    if attempts and now - attempts[-1]["timestamp"] < 3600:
        return False
    day = datetime.fromtimestamp(now, ZoneInfo("America/Los_Angeles")).date().isoformat()
    today = [item for item in attempts if item["day"] == day]
    return len(today) < 4 and sum(item["reserved_micro_usd"] for item in today) < 500_000


def fault_signature(reason: str) -> str:
    """Fixed categories, never free-form server logs, form a durable incident identity."""
    normalized_hash = hashlib.sha256(reason.strip().lower().encode()).hexdigest()
    signature = {"category": reason, "component": "dashboard", "message_hash": normalized_hash}
    return hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()


def prepare_diagnosis(runtime: Path, state: dict, now: float, callback=None, *, reason=None):
    """Reserve locally before a background shared-ledger provider dispatch."""
    reason = reason or state["reason"]
    fingerprint = fault_signature(reason)
    if not diagnosis_eligible(state, fingerprint, now):
        return
    if callback is None:
        try:
            from quanto.provider import diagnose_operations
            callback = diagnose_operations
        except ImportError:
            state["diagnosis"] = {"status": "unavailable", "reason": "gateway_unavailable"}
            return
    day = datetime.fromtimestamp(now, ZoneInfo("America/Los_Angeles")).date().isoformat()
    request_id = "operations-" + uuid.uuid4().hex
    attempt = {"timestamp": now, "day": day, "fingerprint": fingerprint,
               "request_id": request_id,
               "reserved_micro_usd": DIAGNOSIS_RESERVATION_MICRO_USD}
    state["diagnosis_attempts"].append(attempt)
    state["diagnosis"] = {"status": "pending", "reason": reason, "advisory_only": True}
    save_state(runtime, state)
    incident = {"request_id": request_id, "reason": reason, "fault_signature": fingerprint,
                "component": "dashboard",
                "consecutive_failures": state["consecutive_failures"],
                "readiness_failures": state.get("readiness_failures", 0),
                "restarts_last_hour": state.get("restarts_last_hour", 0),
                "service_state": state["service_state"], "awake_host_limitation": AWAKE_LIMITATION}
    return callback, incident


def diagnosis_result(root: Path, incident: dict, callback, now: float) -> dict:
    """Model output can only become bounded advisory text, never a health decision."""
    try:
        result = callback(root, incident, max_cost_usd=Decimal("0.125"))
        if not isinstance(result, dict) or result.get("status") not in (
            "completed", "incomplete", "unavailable", "failed"
        ):
            raise ValueError("Invalid diagnosis result")
        report = {"status": result["status"], "advisory_only": True,
                  "observed_at": timestamp(now), "reason": incident["reason"]}
        if result["status"] == "completed":
            text = result.get("text")
            if not isinstance(text, str) or not text.strip() or len(text) > 8000:
                raise ValueError("Invalid diagnosis text")
            report.update(text=text, model=result.get("model"),
                          cost_usd=str(result.get("cost_usd", "unknown")))
        return report
    except Exception:
        return {"status": "failed", "reason": "gateway_failed_or_uncertain",
                "advisory_only": True}


def diagnose(root: Path, runtime: Path, state: dict, now: float, callback=None) -> None:
    """Synchronous helper for explicit tests; the supervisor dispatches in the background."""
    prepared = prepare_diagnosis(runtime, state, now, callback)
    if prepared:
        handler, incident = prepared
        state["diagnosis"] = diagnosis_result(root, incident, handler, now)
    save_state(runtime, state)


def child_command(root: Path, port: int) -> list[str]:
    return [os.path.abspath(sys.executable), "-m", "quanto", "--root", str(root),
            "serve", "--port", str(port)]


def start_child(root: Path, port: int):
    # Do not inherit broker/API credentials from the supervisor environment.
    environment = {key: value for key, value in os.environ.items()
                   if key in {"HOME", "PATH", "TMPDIR", "LANG", "LC_ALL"}}
    environment["PYTHONPATH"] = str(Path(__file__).absolute().parents[1])
    return subprocess.Popen(child_command(root, port), cwd=root, env=environment,
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)


def stop_child(child) -> None:
    """Only an actual child handle conveys ownership; persisted PIDs never do."""
    if child is None or child.poll() is not None:
        return
    child.terminate()
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait(timeout=5)


def supervise(root: Path, port: int, *, once: bool = False) -> dict:
    runtime = _runtime(root)
    stopped = threading.Event()
    child = None
    previous_handlers = {}
    diagnosis_queue = SimpleQueue()
    diagnosis_running = False
    with supervisor_lock(runtime):
        state = load_state(runtime)
        try:
            if not once:
                for sig in (signal.SIGTERM, signal.SIGINT):
                    previous_handlers[sig] = signal.signal(sig, lambda *_: stopped.set())
            started_at = 0.0
            while not stopped.is_set():
                now = time.time()
                healthy, reason = check_health(port)
                exited = child is not None and child.poll() is not None
                if exited:
                    healthy, reason = False, "owned_child_exited"
                observe(state, healthy, reason, now, owned=child is not None)
                ready, readiness_reason = check_readiness(port) if healthy else (False, "not_checked")
                state["readiness_state"] = "ready" if ready else "degraded" if healthy else "unknown"
                state["readiness_reason"] = readiness_reason
                state["readiness_failures"] = (
                    state.get("readiness_failures", 0) + 1 if healthy and not ready else 0
                )
                state["recent_checks"][-1]["ready"] = ready if healthy else None
                if not diagnosis_queue.empty():
                    state["diagnosis"] = diagnosis_queue.get()
                    diagnosis_running = False
                if once:
                    save_state(runtime, state)
                    return state
                if not healthy or not ready:
                    failed_count = (state["consecutive_failures"] if not healthy
                                    else state["readiness_failures"])
                    if failed_count >= FAILURE_LIMIT and not diagnosis_running:
                        prepared = prepare_diagnosis(runtime, state, now,
                                                     reason=reason if not healthy else readiness_reason)
                        if prepared:
                            handler, incident = prepared
                            diagnosis_running = True

                            def run_diagnosis(handler=handler, incident=incident, observed=now):
                                diagnosis_queue.put(diagnosis_result(root, incident, handler, observed))

                            threading.Thread(target=run_diagnosis, daemon=True).start()
                if not healthy:
                    occupied = port_occupied(port)
                    if child is None and occupied:
                        state["service_state"] = "blocked_unknown_port_owner"
                        state["reason"] = "port_occupied_by_unrecognized_service"
                    elif child is None or (
                        now - started_at >= STARTUP_GRACE
                        and state["consecutive_failures"] >= FAILURE_LIMIT
                    ):
                        # Every launch consumes a persisted slot, including across supervisor restarts.
                        if reserve_restart(state, now):
                            save_state(runtime, state)
                            stop_child(child)
                            child = None
                            # Never compete with a newly appeared unknown port owner.
                            if port_occupied(port):
                                state["service_state"] = "blocked_unknown_port_owner"
                                state["reason"] = "port_became_occupied"
                            else:
                                try:
                                    child = start_child(root, port)
                                    started_at = now
                                    state["service_state"] = "starting"
                                    state["consecutive_failures"] = 0
                                    state["reason"] = "owned_child_started"
                                except OSError:
                                    state["service_state"] = "start_failed"
                                    state["reason"] = "owned_child_start_failed"
                    save_state(runtime, state)
                state["snapshot_capture"] = {"checked_at": timestamp(now),
                                             **capture_due(root, state, now=now)}
                save_state(runtime, state)
                stopped.wait(INTERVAL)
        finally:
            stop_child(child)
            if not once:
                state["service_state"] = "supervisor_stopped"
                state["reason"] = "stop_requested_or_supervisor_exit"
                state["stopped_at"] = timestamp(time.time())
                save_state(runtime, state)
            for sig, handler in previous_handlers.items():
                signal.signal(sig, handler)
    return state


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Supervise Quanto on this awake local host")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--once", action="store_true", help="Observe once without starting services or API calls")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    try:
        state = supervise(args.root.absolute(), args.port, once=args.once)
        if args.once:
            print(json.dumps(state, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        print(f"Quanto supervision unavailable: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

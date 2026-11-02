"""Synthetic supervision checks: no launchd installation, external model, or broker calls."""

import importlib.util
import json
from pathlib import Path
import subprocess
from unittest.mock import Mock

import pytest

from quanto import operations as ops


def test_health_requires_quanto_identity_and_refuses_unbounded_response(monkeypatch):
    response = Mock()
    response.status = 200
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    opener = Mock()
    opener.open.return_value = response
    monkeypatch.setattr(ops, "build_opener", Mock(return_value=opener))
    response.read.return_value = b'{"status":"ok"}'
    assert ops.check_health(8766) == (False, "unrecognized_health_response")
    response.read.return_value = b'{"status":"ok","service":"quanto"}'
    assert ops.check_health(8766) == (True, "health_ok")
    assert opener.open.call_args.kwargs["timeout"] == 2
    response.read.return_value = b"a" * 4097
    assert ops.check_health(8766) == (False, "invalid_health_response")


def test_gap_does_not_invent_continuous_uptime_or_research_observation():
    state = ops.new_state()
    state["observed_at"] = "research-time-never-touch"
    ops.observe(state, True, "health_ok", 1000, owned=False)
    ops.observe(state, True, "health_ok", 1040, owned=True)
    assert state["service_state"] == "healthy"
    assert state["observation_gaps"][0]["seconds"] == 40
    assert state["observed_at"] == "research-time-never-touch"
    assert "awake" in state["awake_host_limitation"]
    ops.observe(state, False, "health_timeout", 1050, owned=True)
    assert state["last_success"] == ops.timestamp(1040)


def test_restart_budget_backoff_and_persistent_reload(tmp_path):
    state = ops.new_state()
    assert ops.reserve_restart(state, 1000)
    assert not ops.reserve_restart(state, 1001)
    assert state["service_state"] == "restart_backoff"
    for now in (1030, 1090, 1210, 1450):
        assert ops.reserve_restart(state, now)
    ops.save_state(tmp_path, state)
    restored = ops.load_state(tmp_path)
    assert not ops.reserve_restart(restored, 1750)
    assert restored["service_state"] == "restart_circuit_open"
    assert restored["restarts"] == 5
    assert ops.reserve_restart(restored, 4601)
    assert restored["restarts"] == 6


def test_singleton_lock_and_corrupt_history_fail_closed(tmp_path):
    with ops.supervisor_lock(tmp_path):
        with pytest.raises(ValueError, match="already owns"):
            with ops.supervisor_lock(tmp_path):
                pytest.fail("Second supervisor acquired a live lock")
    (tmp_path / "operations.json").write_text('{"schema_version":1}')
    with pytest.raises(ValueError, match="history is invalid"):
        ops.load_state(tmp_path)


def test_once_does_not_launch_or_diagnose(tmp_path, monkeypatch):
    monkeypatch.setattr(ops, "check_health", Mock(return_value=(True, "health_ok")))
    monkeypatch.setattr(ops, "check_readiness", Mock(return_value=(True, "readiness_ok")))
    start = Mock(side_effect=AssertionError("must not spawn"))
    diagnose = Mock(side_effect=AssertionError("must not invoke a model"))
    monkeypatch.setattr(ops, "start_child", start)
    monkeypatch.setattr(ops, "prepare_diagnosis", diagnose)
    state = ops.supervise(tmp_path, 8766, once=True)
    assert state["service_state"] == "healthy_external"
    assert state["restarts"] == 0
    assert state["diagnosis"]["status"] == "not_requested"


class FakeEvent:
    def __init__(self, clock, checks):
        self.clock = clock
        self.remaining = checks
        self.stopped = False

    def is_set(self):
        return self.stopped

    def set(self):
        self.stopped = True

    def wait(self, seconds):
        self.clock[0] += seconds
        self.remaining -= 1
        self.stopped = self.remaining <= 0


def supervisor_fakes(monkeypatch, checks):
    clock = [1000]
    event = FakeEvent(clock, checks)
    monkeypatch.setattr(ops.time, "time", lambda: clock[0])
    monkeypatch.setattr(ops.threading, "Event", lambda: event)
    monkeypatch.setattr(ops.signal, "signal", Mock())
    monkeypatch.setattr(ops, "prepare_diagnosis", Mock(return_value=None))
    monkeypatch.setattr(ops, "check_readiness", lambda _: (True, "readiness_ok"))
    return event


def test_degraded_readiness_never_restarts_a_healthy_service(tmp_path, monkeypatch):
    supervisor_fakes(monkeypatch, 4)
    monkeypatch.setattr(ops, "check_health", lambda _: (True, "health_ok"))
    monkeypatch.setattr(ops, "check_readiness", lambda _: (False, "readiness_unavailable"))
    start = Mock(side_effect=AssertionError("bad snapshots must not cause restarts"))
    monkeypatch.setattr(ops, "start_child", start)
    ops.supervise(tmp_path, 8766)
    state = ops.load_state(tmp_path / "runtime")
    assert state["readiness_state"] == "degraded"
    assert state["readiness_failures"] == 4
    assert state["restarts"] == 0
    assert all(item["healthy"] and not item["ready"] for item in state["recent_checks"])
    assert ops.prepare_diagnosis.call_args.kwargs["reason"] == "readiness_unavailable"


def test_unknown_port_owner_is_never_killed_or_replaced(tmp_path, monkeypatch):
    supervisor_fakes(monkeypatch, 4)
    monkeypatch.setattr(ops, "check_health", lambda _: (False, "unrecognized_health_response"))
    monkeypatch.setattr(ops, "port_occupied", lambda _: True)
    start = Mock()
    stop = Mock()
    monkeypatch.setattr(ops, "start_child", start)
    monkeypatch.setattr(ops, "stop_child", stop)
    ops.supervise(tmp_path, 8766)
    start.assert_not_called()
    assert all(call.args == (None,) for call in stop.call_args_list)
    state = ops.load_state(tmp_path / "runtime")
    assert state["restarts"] == 0
    assert len(state["recent_checks"]) == 4


def test_owned_child_restarts_after_three_failed_checks(tmp_path, monkeypatch):
    supervisor_fakes(monkeypatch, 5)
    # Initial start, successful grace-period check, then three failures.
    health = Mock(side_effect=[(False, "health_unavailable"), (True, "health_ok"),
                               (False, "health_timeout"), (False, "health_timeout"),
                               (False, "health_timeout")])
    monkeypatch.setattr(ops, "check_health", health)
    monkeypatch.setattr(ops, "port_occupied", lambda _: False)
    first, second = Mock(), Mock()
    first.poll.return_value = None
    second.poll.return_value = None
    start = Mock(side_effect=[first, second])
    monkeypatch.setattr(ops, "start_child", start)
    ops.supervise(tmp_path, 8766)
    assert start.call_count == 2
    first.terminate.assert_called_once()
    second.terminate.assert_called_once()  # The supervisor's own orderly shutdown.
    state = ops.load_state(tmp_path / "runtime")
    assert state["restart_timestamps"] == [1000, 1040]


def test_owned_child_stop_uses_handle_only():
    child = Mock()
    child.poll.return_value = None
    child.wait.side_effect = [subprocess.TimeoutExpired("fixed child", 5), 0]
    ops.stop_child(child)
    child.terminate.assert_called_once()
    child.kill.assert_called_once()
    child.poll.return_value = 0
    child.reset_mock()
    ops.stop_child(child)
    child.terminate.assert_not_called()


def test_child_fixed_command_and_environment_exclude_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-secret")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "synthetic-secret")
    spawn = Mock()
    monkeypatch.setattr(ops.subprocess, "Popen", spawn)
    ops.start_child(tmp_path, 8766)
    command = spawn.call_args.args[0]
    assert command[1:] == ["-m", "quanto", "--root", str(tmp_path), "serve", "--port", "8766"]
    environment = spawn.call_args.kwargs["env"]
    assert "ANTHROPIC_API_KEY" not in environment
    assert "APCA_API_SECRET_KEY" not in environment
    assert Path(environment["PYTHONPATH"]).is_absolute()


def test_diagnosis_dedupe_cooldown_count_and_daily_money_reservation(tmp_path):
    state = ops.new_state()
    state["reason"] = "health_timeout"
    state["consecutive_failures"] = 3
    callback = Mock(return_value={"status": "completed", "text": "Check the local service.",
                                 "model": "synthetic_fixture", "cost_usd": "0.001"})
    now = 1_800_000_000
    ops.diagnose(tmp_path, tmp_path, state, now, callback)
    assert state["diagnosis"]["status"] == "completed"
    assert state["diagnosis"]["advisory_only"] is True
    assert state["service_state"] == "unknown"
    callback.assert_called_once()
    # The exact request ID and conservative sub-budget reservation precede the gateway call.
    assert state["diagnosis_attempts"][0]["request_id"] == callback.call_args.args[1]["request_id"]
    assert state["diagnosis_attempts"][0]["reserved_micro_usd"] == 125_000
    ops.diagnose(tmp_path, tmp_path, state, now + 4000, callback)
    assert callback.call_count == 1
    for index in range(1, 5):
        state["reason"] = f"synthetic_distinct_fault_{index}"
        ops.diagnose(tmp_path, tmp_path, state, now + 3600 * index, callback)
    assert callback.call_count == 4
    assert sum(item["reserved_micro_usd"] for item in state["diagnosis_attempts"]) == 500_000
    assert not ops.diagnosis_eligible(state, "new-fault", now + 3600 * 5)


def test_diagnosis_failed_or_unavailable_never_claims_model_success(tmp_path):
    state = ops.new_state()
    state["reason"] = "health_timeout"
    callback = Mock(side_effect=RuntimeError("synthetic fixture secret must not be logged"))
    ops.diagnose(tmp_path, tmp_path, state, 1_800_000_000, callback)
    assert state["diagnosis"]["status"] == "failed"
    assert "synthetic fixture secret" not in json.dumps(state)
    assert len(state["diagnosis_attempts"]) == 1  # Uncertain calls consume their reservation.
    loaded = ops.load_state(tmp_path)
    assert not ops.diagnosis_eligible(loaded, ops.fault_signature("health_timeout"), 1_800_010_000)


def test_installer_plan_has_no_credentials_and_checks_exact_owned_service(tmp_path):
    source = Path(__file__).parents[1] / "scripts" / "install_local_service.py"
    spec = importlib.util.spec_from_file_location("quanto_install_fixture", source)
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    config = installer.configuration(tmp_path, tmp_path / ".venv/bin/python", 8766)
    assert config["EnvironmentVariables"] == {"PYTHONPATH": str(tmp_path / "src")}
    assert config["ThrottleInterval"] == 30
    assert config["ProgramArguments"][1:3] == ["-m", "quanto.operations"]
    path = tmp_path / "service.plist"
    with path.open("wb") as output:
        installer.plistlib.dump(config, output)
    assert installer.verify_owned(path, tmp_path)
    config["WorkingDirectory"] = str(tmp_path / "different-project")
    with path.open("wb") as output:
        installer.plistlib.dump(config, output)
    with pytest.raises(ValueError, match="not this project's"):
        installer.verify_owned(path, tmp_path)

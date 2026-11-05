"""Real child processes and existing authority over invented local stores only."""
import importlib.util
import json
import os
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys
import time

import pytest

from quanto.evaluation_registry import Supervisor
from quanto.provenance import Provenance

SOURCE = Path(__file__).resolve().parents[1]
SCRIPT = SOURCE / "operations/strategy_campaign/supervise_step.py"
spec = importlib.util.spec_from_file_location("campaign_supervisor", SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

FAKE_CLI = '''
import json, os, signal, sys, time
from pathlib import Path
def main(args):
    mode = json.loads(Path(args[args.index("--request") + 1]).read_text())["mode"]
    if mode == "sleep":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        time.sleep(20)
    elif mode in ("stdout", "stderr"):
        target = sys.stdout.buffer if mode == "stdout" else sys.stderr.buffer
        target.write(b"x" * 300000)
        target.flush()
    elif mode == "environment":
        print(json.dumps(dict(os.environ)))
    else:
        print('{"fixture":"completed"}')
    return 0
'''


def inputs(tmp_path, mode="normal", *, actual_cli=False, synthetic=False):
    root = (tmp_path / "invented-root").resolve()
    root.mkdir()
    authority = Supervisor(root, synthetic=synthetic)
    with authority.session(), Provenance(root):
        pass
    source = SOURCE
    if not actual_cli:
        source = tmp_path / "fixture-source"
        package = source / "src/quanto"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("")
        shutil.copyfile(SOURCE / "src/quanto/evaluation_registry.py",
                        package / "evaluation_registry.py")
        (package / "cli.py").write_text(FAKE_CLI)
    raw = b"{" if actual_cli else json.dumps({"mode": mode}).encode()
    request = tmp_path / "private-request.json"
    request.write_bytes(raw)
    request.chmod(0o600)
    python = Path(sys.executable).resolve()
    return {"command": "register-campaign", "runtime_root": root,
            "source_root": source, "python": python, "request": request,
            "attempt": tmp_path / "attempt", "source_sha256": runner.source_identity(source),
            "python_sha256": runner.sha(python.read_bytes()), "request_sha256": runner.sha(raw),
            "timeout": 2}


def absent(pid):
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_actual_cli_retains_invalid_attempt_and_child_has_no_inherited_keys(tmp_path, monkeypatch):
    request = inputs(tmp_path, actual_cli=True)
    result = runner.supervise_step(**request)
    assert result["status"] == "completed" and result["exit_code"] == 1
    assert result["cleanup_confirmed"] and result["identities_unchanged"]
    assert json.loads((request["attempt"] / "stdout.bin").read_text())["status"] == "invalid"
    absent(result["pid"])
    for path in request["attempt"].iterdir():
        assert path.stat().st_mode & 0o777 == (0o700 if path.is_dir() else 0o600)
    other = tmp_path / "environment"
    other.mkdir()
    environment = inputs(other, "environment")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "invented-not-a-secret")
    monkeypatch.setenv("RUNPOD_API_KEY", "invented-not-a-secret")
    result = runner.supervise_step(**environment)
    assert result["status"] == "completed" and result["exit_code"] == 0
    inherited = json.loads((environment["attempt"] / "stdout.bin").read_text())
    assert "ANTHROPIC_API_KEY" not in inherited and "RUNPOD_API_KEY" not in inherited


def test_deadline_kills_and_reaps_term_ignoring_child_without_replay(tmp_path):
    request = inputs(tmp_path, "sleep")
    request["timeout"] = 0.25
    start = time.monotonic()
    result = runner.supervise_step(**request)
    assert result["status"] == "uncertain" and result["reason"] == "deadline"
    assert result["exit_code"] == -9 and result["cleanup_confirmed"]
    assert time.monotonic() - start < 6
    absent(result["pid"])
    receipt = (request["attempt"] / "receipt.json").read_bytes()
    with pytest.raises(runner.Refused, match="attempt_already_exists"):
        runner.supervise_step(**request)
    child = subprocess.run([str(request["python"]), "-I", "-S", "-B", str(SCRIPT),
                            "--child", str(request["attempt"])],
                           capture_output=True, timeout=5, env={"PATH": "/usr/bin:/bin"})
    assert child.returncode == 70 and child.stdout == b""
    assert (request["attempt"] / "receipt.json").read_bytes() == receipt


@pytest.mark.parametrize("stream,limit", [("stdout", runner.MAX_STDOUT), ("stderr", runner.MAX_STDERR)])
def test_output_is_bounded_and_writer_is_reaped(tmp_path, stream, limit):
    request = inputs(tmp_path, stream)
    result = runner.supervise_step(**request)
    assert result["status"] == "uncertain" and result["reason"] == "output_limit"
    assert result[stream + "_bytes"] == limit
    assert (request["attempt"] / (stream + ".bin")).stat().st_size == limit
    absent(result["pid"])


@pytest.mark.parametrize("which", ["source", "python", "request", "control", "research", "command"])
def test_preflight_refusals_never_launch_or_create_missing_authority(tmp_path, which):
    request = inputs(tmp_path)
    missing = None
    if which in {"source", "python", "request"}:
        request[which + "_sha256"] = "0" * 64
    elif which == "command":
        request["command"] = "paper-order"
    else:
        relative = "runtime/access-control/control.sqlite" if which == "control" else "runtime/research.sqlite"
        missing = request["runtime_root"] / relative
        missing.unlink()
    result = runner.supervise_step(**request)
    assert result["status"] == "refused" and result["exit_code"] is None
    assert not (request["attempt"] / "child-started.json").exists()
    if missing:
        assert not missing.exists()


def test_normal_supervisor_refuses_existing_configuration_mismatch_before_cli(tmp_path):
    request = inputs(tmp_path, synthetic=True)
    control = request["runtime_root"] / "runtime/access-control/control.sqlite"
    before = control.read_bytes()
    result = runner.supervise_step(**request)
    assert result["status"] == "completed" and result["exit_code"] == 70
    assert (request["attempt"] / "stdout.bin").read_bytes() == b""
    assert json.loads((request["attempt"] / "stderr.bin").read_text()) == {"child_refusal": "wrong_store"}
    assert control.read_bytes() == before


def test_group_observation_or_kill_failure_preserves_uncertainty(tmp_path, monkeypatch):
    request = inputs(tmp_path)
    def denied(*args):
        raise PermissionError("invented group observation refusal")
    monkeypatch.setattr(runner.os, "killpg", denied)
    result = runner.supervise_step(**request)
    assert result["status"] == "uncertain" and result["exit_code"] == 0
    assert result["pid"] and not result["cleanup_confirmed"]
    absent(result["pid"])


def test_exception_after_entering_capture_is_not_preflight_refusal(tmp_path, monkeypatch):
    request = inputs(tmp_path)
    def uncertain(*args):
        raise OSError("invented supervision failure")
    monkeypatch.setattr(runner, "_capture", uncertain)
    result = runner.supervise_step(**request)
    assert result["status"] == "uncertain" and not result["cleanup_confirmed"]
    assert result["reason"] == "supervision_unavailable"


def test_existing_stale_bytecode_cannot_replace_pinned_source(tmp_path):
    request = inputs(tmp_path)
    source = request["source_root"] / "src/quanto/cli.py"
    before = source.stat()
    py_compile.compile(str(source), doraise=True)
    source.write_text(source.read_text().replace("return 0", "return 7"))
    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    request["source_sha256"] = runner.source_identity(request["source_root"])
    result = runner.supervise_step(**request)
    assert result["status"] == "completed" and result["exit_code"] == 7
    assert list((request["attempt"] / "pycache").iterdir()) == []


def test_lost_spawn_handle_closes_gate_before_authority_or_cli(tmp_path, monkeypatch):
    request = inputs(tmp_path, "sleep")
    created, original = [], subprocess.Popen
    def lose_handle(*args, **kwargs):
        created.append(original(*args, **kwargs))
        raise InterruptedError("invented interruption after spawn")
    monkeypatch.setattr(runner.subprocess, "Popen", lose_handle)
    result = runner.supervise_step(**request)
    assert result["status"] == "uncertain" and not result["cleanup_confirmed"]
    assert result["launch_attempted"] and result["pid"] is None
    process = created[0]
    try:
        output, _ = process.communicate(timeout=5)
        assert output == b"" and process.returncode == 70
        assert not (request["attempt"] / "child-started.json").exists()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def test_wall_clock_expiry_prevents_gate_release_despite_active_monotonic_clock(tmp_path, monkeypatch):
    request = inputs(tmp_path, "sleep")
    calls, original = [], time.time
    def advanced():
        calls.append(None)
        return original() + (10 if len(calls) >= 3 else 0)
    monkeypatch.setattr(runner.time, "time", advanced)
    result = runner.supervise_step(**request)
    assert result["status"] == "uncertain" and result["reason"] == "deadline"
    assert result["cleanup_confirmed"] and result["wall_elapsed_seconds"] >= 10
    assert not (request["attempt"] / "child-started.json").exists()
    absent(result["pid"])

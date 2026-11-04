"""Process-level supervisor tests. Both stage implementations are invented here."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest


HERE = Path(__file__).absolute().parent
PYTHON = "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pack(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_bytes(data)
    path.chmod(0o600)
    return digest(data)


STUB_REG = r'''
import hashlib, json
from pathlib import Path
WORK_SECONDS, CLEANUP_SECONDS = 0.05, 0.01
def parse(raw): return json.loads(raw)
def environment_check(): pass
def validate_packet(packet, fixture): assert not fixture
def write(path,value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    path.write_bytes(raw);path.chmod(0o600)
    return hashlib.sha256(raw).hexdigest()
def run(path, identity):
    packet=parse(path.read_bytes())
    attempt=path.parents[1]/'current-code-registration'/packet['attempt_id']
    attempt.mkdir(parents=True,mode=0o700)
    mapping, phases={}, []
    for index,name in enumerate(('revision','admission','suite')):
        old=packet['originals'][name]
        mapping[name]={'submission_id':str(index+4)*32,'artifact_sha256':str(index+4)*64,
                       'old_artifact_sha256':old['artifact_sha256'],'old_submission_id':old['submission_id']}
        end=write(attempt/(name+'-exit.json'),{'exitcode':0,'stderr_bytes':0,'intent_sha256':'a'*64})
        phase=write(attempt/(name+'-result.json'),{'phase':name,'status':'success','intent_sha256':'a'*64,
                      'mapping':mapping})
        phases.append({'phase':name,'result_sha256':phase,'exit_sha256':end})
    result={'status':'completed','paid_launch_authorized':False,'automatic_retry':False,'packet_sha256':identity,
            'intent_sha256':'a'*64,'mapping':mapping,'phases':phases,'after':{}}
    write(attempt/'result.json',result)
    return result
'''

STUB_WORKER = r'''
import importlib.util, json, os, sys, time
from pathlib import Path
p=Path(__file__).with_name('supervise.py')
spec=importlib.util.spec_from_file_location('fixture_supervisor',p)
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.await_grant('paid', int(sys.argv[2]))
root, state, plan, reg, packet, result, raw, deadline=s.worker_context()
s.publish(state/'paid-consumed.json',{'fixture':True})
if plan['run_key']=='hang': time.sleep(15)
if plan['run_key']=='missing_result': raise SystemExit(7)
assert json.loads(raw)['suite_sha256']==result['mapping']['suite']['artifact_sha256']
h=s.publish(state/'outcome.json',{'fixture':True,'actual_models':0})
s.publish(state/'terminal.json',{'status':'broker_returned','outcome_sha256':h,'operational_acceptance':False,
                                 'investment_validation':False})
print('{"status":"broker_returned"}',flush=True)
'''


def prepare(tmp, run_key="fresh"):
    root = tmp.resolve() / "project"
    base = root / "runtime/development-cycle-launch-v2-preparation"
    state = root / "runtime/manual-development-cycle"
    inputs = root / "runtime/manual-cycle-inputs"
    reg = root / "runtime/development-cycle-registration-v2-preparation"
    audit = root / "runtime/development-cycle-audit-v2-preparation"
    for directory in (base, state, inputs, reg, audit):
        directory.mkdir(mode=0o700, parents=True)
    source = (HERE / "supervise.py").read_text()
    def substitute(name, value):
        nonlocal source
        import re
        source, count = re.subn(r"^" + name + r" = .*$", name + " = " + repr(value),
                                source, count=1, flags=re.M)
        assert count == 1
    reg_hash = put(reg / "prepare_current_code.py", STUB_REG.encode())
    test_hash = put(reg / "test_registration_preparation.py", b"# invented fixture\n")
    manifest_hash = put(reg / "source-manifest.json", b"{}")
    substitute("REG_SHA", reg_hash)
    substitute("REG_TEST_SHA", test_hash)
    substitute("REG_MANIFEST_SHA", manifest_hash)
    substitute("LIMIT", 3 if run_key == "hang" else 15)
    substitute("CLEANUP", 0.6)
    supervisor_hash = put(base / "supervise.py", source.encode())
    worker_hash = put(base / "paid_worker.py", STUB_WORKER.encode())
    spec = importlib.util.spec_from_file_location("test_supervisor", base / "supervise.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reviews = {key: put(root / "docs/reviews" / filename, ("fixture " + key).encode())
               for key, filename in module.REVIEWS.items()}
    tools = {name: put(audit / name, b"# invented auditor\n") for name in module.AUDIT_TOOLS}
    manifest_name = "source-manifest-" + "d" * 32 + ".json"
    audit_hash = put(audit / manifest_name, pack({"tools": tools,
                 "launch_sources": {"supervise.py": supervisor_hash, "paid_worker.py": worker_hash},
                 "oracle_sha256": tools["independent_oracle.py"]}))
    original = {name: {"submission_id": str(index) * 32, "artifact_sha256": str(index) * 64}
                for index, name in enumerate(("revision", "admission", "suite"), 1)}
    preflight = put(inputs / "preflight.json", b'{"fixture":true}')
    packet_hash = put(inputs / "registration.json", pack({
        "attempt_id": "invented", "controller_sha256": reg_hash, "tests_sha256": test_hash,
        "manifest_sha256": manifest_hash, "preparation_critic_sha256": reviews["registration_critic"],
        "preflight_evidence_sha256": preflight, "originals": original}))
    template = {"run_key": "old", "evidence_kind": "historical_market_data",
                "failure_ids": [{"source": "submission", "id": "1" * 32}],
                "suite_sha256": original["suite"]["artifact_sha256"], "models": module.MODELS}
    plan = dict(schema=1, run_key=run_key, audit_attempt_id="invented-audit", registry_packet_sha256=packet_hash,
                template_sha256=put(inputs / "template.json", pack(template)),
                supervisor_sha256=supervisor_hash, worker_sha256=worker_hash, reviews=reviews,
                audit_manifest={"name": manifest_name, "sha256": audit_hash})
    plan_sha = put(inputs / "plan.json", pack(plan))
    return module, state, base / "supervise.py", plan_sha, template


def launch(path, hash_value):
    return subprocess.run([PYTHON, "-I", "-S", "-B", str(path), "--plan-sha256", hash_value],
                          stdin=subprocess.DEVNULL, capture_output=True, cwd="/", env={},
                          timeout=20, check=False)


def test_one_real_parent_child_sequence_on_invented_stage_implementations(tmp_path):
    _module, state, path, identity, template = prepare(tmp_path)
    first = launch(path, identity)
    assert first.returncode == 0 and not first.stderr
    result = json.loads((state / "result.json").read_bytes())
    assert result["audit_required"] and not result["operational_acceptance"]
    request = json.loads((state / "request.json").read_bytes())
    assert request == {**template, "run_key": "fresh", "suite_sha256": "6" * 64}
    original = {file.name: file.read_bytes() for file in state.iterdir()}
    assert launch(path, identity).returncode != 0
    assert original == {file.name: file.read_bytes() for file in state.iterdir()}


@pytest.mark.parametrize("key", ["hang", "missing_result"])
def test_interruption_consumes_cycle_without_acceptance(tmp_path, key):
    _module, state, path, identity, _template = prepare(tmp_path, key)
    assert launch(path, identity).returncode != 0
    assert (state / "consumed.json").exists() and (state / "paid-consumed.json").exists()
    assert not (state / "result.json").exists()
    if key == "hang":
        assert json.loads((state / "paid-uncertainty.json").read_bytes())["cleanup"] == "owned_child_reaped"
        with pytest.raises(ProcessLookupError):
            os.kill(json.loads((state / "owned.json").read_bytes())["pid"], 0)


def test_review_change_refuses_before_registration(tmp_path):
    module, state, path, identity, _template = prepare(tmp_path)
    (module.ROOT / "docs/reviews" / module.REVIEWS["auditor_scope"]).write_bytes(b"changed")
    assert launch(path, identity).returncode != 0
    assert not list(state.iterdir())
    assert not (module.ROOT / "runtime/current-code-registration").exists()


def test_wall_expiry_and_monotonic_expiry_each_refuse(tmp_path, monkeypatch):
    module, *_ = prepare(tmp_path)
    monkeypatch.setattr(module.time, "monotonic", lambda: 101.)
    monkeypatch.setattr(module.time, "time", lambda: 1001.)
    for window in ({"start_monotonic": 0., "start_wall": 1000.},
                   {"start_monotonic": 100., "start_wall": 0.}):
        with pytest.raises(module.Refused, match="deadline"):
            module.remaining(window)


def test_interrupted_spawn_never_releases_start_grant(tmp_path, monkeypatch):
    module, state, path, plan_sha, _ = prepare(tmp_path)
    window = {"start_monotonic": module.time.monotonic(), "start_wall": module.time.time(),
              "parent_pid": os.getpid(), "plan_sha256": plan_sha}
    consumed_sha = module.publish(state / "consumed.json", window)
    launch_sha = module.publish(state / "paid-launch.json", {"consumed_sha256": consumed_sha,
                                "parent_pid": os.getpid(), "plan_sha256": plan_sha})
    real_spawn, spawned = subprocess.Popen, []
    def interrupted_spawn(*args, **kwargs):
        spawned.append(real_spawn(*args, **kwargs))
        raise OSError("simulated interruption before handle delivery")
    monkeypatch.setattr(module.subprocess, "Popen", interrupted_spawn)
    previous_alarm = module.signal.getitimer(module.signal.ITIMER_REAL)
    began = module.time.monotonic()
    try:
        with pytest.raises(OSError):
            module.launch_phase("paid", [PYTHON, "-I", "-S", "-B", str(path.with_name("paid_worker.py"))],
                                window, consumed_sha, launch_sha)
    finally:
        # Calling just the phase bypasses supervise()'s normal outer teardown.
        initial, interval = previous_alarm
        left = max(0.000001, initial - (module.time.monotonic() - began)) if initial else 0
        module.signal.setitimer(module.signal.ITIMER_REAL, left, interval)
    # The test observer retains its own handle; the supervisor received none.
    assert len(spawned) == 1 and spawned[0].wait(timeout=5) != 0
    assert json.loads((state / "paid-uncertainty.json").read_bytes())["cleanup"] == "launch_ownership_unknown"
    assert not any((state / name).exists() for name in ("start.json", "paid-consumed.json", "outcome.json"))


def test_late_termination_observation_stays_late(tmp_path, monkeypatch):
    module, *_ = prepare(tmp_path)
    now = [0.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(module.time, "time", lambda: now[0])
    class Child:
        returncode = None
        def poll(self):
            return self.returncode
        def terminate(self):
            pass
        def wait(self, *, timeout):
            assert 0 < timeout <= module.CLEANUP
            now[0] += module.CLEANUP + 1
            self.returncode = -15
    assert module.cleanup_child(Child(), {"start_monotonic": 0, "start_wall": 0}) == "terminal_observed_late"


def test_guardian_rechecks_wall_while_registration_is_waiting(tmp_path, monkeypatch):
    module, *_ = prepare(tmp_path)
    wall = [21.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: 5.0)
    monkeypatch.setattr(module.time, "time", lambda: wall[0])
    class SleepingRegistration:
        def wait(self, *, timeout):
            assert 0 < timeout <= 0.25
            wall[0] += module.LIMIT
            raise subprocess.TimeoutExpired("invented registration", timeout)
    with pytest.raises(module.Refused, match="deadline"):
        module.wait_child(SleepingRegistration(), {"start_monotonic": 5.0, "start_wall": 21.0})

"""Supervise one manual registration and research cycle on the owner's Mac."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import stat
import subprocess
import time
import types


HERE = Path(__file__).absolute().parent
ROOT = HERE.parents[1]
STATE = ROOT / "runtime/manual-development-cycle"
INPUTS = ROOT / "runtime/manual-cycle-inputs"
REG = ROOT / "runtime/development-cycle-registration-v2-preparation"
AUDIT = ROOT / "runtime/development-cycle-audit-v2-preparation"
PYTHON = Path("/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11")
REG_SHA = "3f52a95452d9a20c6c456624f33a70c717d9f1fc28d83ae65f178e67e9d7047d"
REG_TEST_SHA = "b717f8603b65570feb4b84c23e4301a1f26f54784a11ebd8ad4bac19423d1d79"
REG_MANIFEST_SHA = "aa65675f3c7886a2d950b75928811d4f7189adbc2342a383b983f0ea20ea70c4"
LIMIT = 7200
CLEANUP = 5
ROLES = ("director", "hypothesis", "engineer", "data_critic", "statistical_critic", "quality", "scope")
MODELS = {role: "claude-opus-5-5" if role in {"data_critic", "statistical_critic"}
          else "claude-haiku-5-5" for role in ROLES}
REVIEWS = {f"{stage}_{role}": f"D008-{prefix}-{role}.md"
           for stage, prefix in (("registration", "current-code-registration-v2"),
                                 ("auditor", "next-cycle-audit-v2"), ("supervisor", "manual-cycle-launch-v2"))
           for role in ("critic", "quality", "scope")}
AUDIT_TOOLS = {"audit_cycle.py", "audit_boundary.py", "trace_checks.py", "context_checks.py",
               "independent_oracle.py", "cycle_evidence.py"}


class Refused(Exception):
    """Only program-owned reason codes may reach the public terminal."""


def require(condition, reason):
    if not condition:
        raise Refused(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode()


def parse(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "ambiguous_json")
            result[key] = value
        return result

    def invalid(_value):
        raise Refused("invalid_json")

    return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)


def digest_text(value):
    require(isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value), "invalid_digest")
    return value


def path_check(path):
    require(path.is_absolute() and ".." not in path.parts
            and all(not item.is_symlink() for item in (path, *path.parents)), "unsafe_path")


def read(path, *, private=False, limit=2_097_152):
    path_check(path)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as source:
        before = os.fstat(source.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
                and before.st_nlink == 1 and not before.st_mode & 0o022 and before.st_size <= limit,
                "unsafe_file")
        require(not private or stat.S_IMODE(before.st_mode) == 0o600, "unsafe_file")
        raw = source.read(limit + 1)
        def identity(info):
            return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        require(len(raw) == before.st_size and identity(before) == identity(os.fstat(source.fileno()))
                == identity(path.lstat()), "changed_file")
        return raw


def pinned(path, expected, *, private=False):
    raw = read(path, private=private)
    require(sha(raw) == digest_text(expected), "changed_pin")
    return raw


def private_directory(path):
    path_check(path)
    metadata = path.lstat()
    require(stat.S_ISDIR(metadata.st_mode) and stat.S_IMODE(metadata.st_mode) == 0o700
            and metadata.st_uid == os.getuid(), "unsafe_directory")


def publish(path, value):
    private_directory(path.parent)
    raw = canonical(value)
    require(len(raw) <= 2_097_152, "receipt_too_large")
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), "wb") as out:
        out.write(raw)
        out.flush()
        os.fsync(out.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    require(read(path, private=True) == raw, "receipt_changed")
    return sha(raw)


def remaining(window, *, cleanup=False):
    reserve = 0 if cleanup else CLEANUP
    seconds = min(window["start_monotonic"] + LIMIT - time.monotonic(),
                  window["start_wall"] + LIMIT - time.time()) - reserve
    require(seconds > 0, "deadline")
    return seconds


def arm(window, *, cleanup=False):
    signal.setitimer(signal.ITIMER_REAL, remaining(window, cleanup=cleanup))


def registration_module():
    path = REG / "prepare_current_code.py"
    module = types.ModuleType("reviewed_registration")
    module.__file__ = str(path)
    exec(compile(pinned(path, REG_SHA), str(path), "exec", dont_inherit=True), module.__dict__)
    module.environment_check()
    return module


def load_plan(plan_sha):
    private_directory(INPUTS)
    raw = pinned(INPUTS / "plan.json", plan_sha, private=True)
    plan = parse(raw)
    require(type(plan) is dict and set(plan) == {"schema", "run_key", "audit_attempt_id", "registry_packet_sha256",
            "template_sha256", "supervisor_sha256", "worker_sha256", "audit_manifest",
            "reviews"} and type(plan["schema"]) is int and plan["schema"] == 1, "invalid_plan")
    require(type(plan["run_key"]) is str and re.fullmatch("[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,63}", plan["run_key"]),
            "invalid_run_key")
    require(type(plan["audit_attempt_id"]) is str and re.fullmatch("[a-z0-9][a-z0-9-]{0,63}", plan["audit_attempt_id"]),
            "invalid_audit_attempt")
    pinned(HERE / "supervise.py", plan["supervisor_sha256"])
    pinned(HERE / "paid_worker.py", plan["worker_sha256"])
    pinned(REG / "test_registration_preparation.py", REG_TEST_SHA)
    pinned(REG / "source-manifest.json", REG_MANIFEST_SHA)
    require(type(plan["reviews"]) is dict and set(plan["reviews"]) == set(REVIEWS), "missing_review")
    for role, filename in REVIEWS.items():
        pinned(ROOT / "docs/reviews" / filename, plan["reviews"][role])
    record = plan["audit_manifest"]
    require(type(record) is dict and set(record) == {"name", "sha256"}
            and isinstance(record["name"], str)
            and re.fullmatch(r"source-manifest-[a-f0-9]{32}\.json", record["name"]), "invalid_audit_pin")
    manifest = parse(pinned(AUDIT / record["name"], record["sha256"]))
    require(manifest["launch_sources"] == {"supervise.py": plan["supervisor_sha256"],
            "paid_worker.py": plan["worker_sha256"]}, "audit_for_different_launcher")
    require(set(manifest["tools"]) == AUDIT_TOOLS and manifest["oracle_sha256"]
            == manifest["tools"]["independent_oracle.py"], "invalid_audit_tools")
    for name, expected in manifest["tools"].items():
        pinned(AUDIT / name, expected)
    registration = registration_module()
    packet = registration.parse(pinned(INPUTS / "registration.json", plan["registry_packet_sha256"], private=True))
    registration.validate_packet(packet, False)
    require(packet["controller_sha256"] == REG_SHA and packet["tests_sha256"] == REG_TEST_SHA
            and packet["manifest_sha256"] == REG_MANIFEST_SHA and packet["preparation_critic_sha256"]
            == plan["reviews"]["registration_critic"], "unbound_registration")
    pinned(INPUTS / "preflight.json", packet["preflight_evidence_sha256"], private=True)
    template = parse(pinned(INPUTS / "template.json", plan["template_sha256"], private=True))
    require(set(template) == {"run_key", "suite_sha256", "evidence_kind", "failure_ids", "models"}
            and template["evidence_kind"] == "historical_market_data" and template["models"] == MODELS
            and template["run_key"] != plan["run_key"]
            and template["suite_sha256"] == packet["originals"]["suite"]["artifact_sha256"], "template_mismatch")
    return {**plan, "source_root": str(ROOT), "request_template": template}, registration, packet


def registration_result(packet, expected_sha):
    attempt = ROOT / "runtime/current-code-registration" / packet["attempt_id"]
    result = parse(pinned(attempt / "result.json", expected_sha, private=True))
    require(result["status"] == "completed" and result["paid_launch_authorized"] is False
            and result["automatic_retry"] is False and result["packet_sha256"] == sha(read(INPUTS / "registration.json", private=True))
            and not (attempt / "failure.json").exists(), "registration_incomplete")
    phases = ("revision", "admission", "suite")
    require([item["phase"] for item in result["phases"]] == list(phases)
            and set(result["mapping"]) == set(phases), "registration_mapping")
    for item in result["phases"]:
        name = item["phase"]
        old = packet["originals"][name]
        mapping = result["mapping"][name]
        phase = parse(pinned(attempt / (name + "-result.json"), item["result_sha256"], private=True))
        end = parse(pinned(attempt / (name + "-exit.json"), item["exit_sha256"], private=True))
        require(end["exitcode"] == 0 and end["stderr_bytes"] == 0 and phase["status"] == "success"
                and phase["intent_sha256"] == end["intent_sha256"] == result["intent_sha256"]
                and phase["mapping"][name] == mapping and mapping["old_submission_id"] == old["submission_id"]
                and mapping["old_artifact_sha256"] == old["artifact_sha256"]
                and mapping["submission_id"] != old["submission_id"], "registration_lineage")
        digest_text(mapping["artifact_sha256"])
    return result


def build_request(plan, result):
    return {**plan["request_template"], "run_key": plan["run_key"],
            "suite_sha256": result["mapping"]["suite"]["artifact_sha256"]}


def worker_context():
    private_directory(STATE)
    consumed_raw = read(STATE / "consumed.json", private=True)
    consumed = parse(consumed_raw)
    check_start("paid", consumed, consumed_raw)
    launch = parse(read(STATE / "paid-launch.json", private=True))
    require(launch["parent_pid"] == os.getppid() == consumed["parent_pid"]
            and launch["consumed_sha256"] == sha(consumed_raw)
            and launch["plan_sha256"] == consumed["plan_sha256"], "unbound_child")
    deadline = time.monotonic() + remaining(consumed)
    plan, registration, packet = load_plan(consumed["plan_sha256"])
    require(plan["supervisor_sha256"] == consumed["supervisor_sha256"], "changed_supervisor")
    result = registration_result(packet, launch["registration_result_sha256"])
    raw = pinned(STATE / "request.json", launch["request_sha256"], private=True)
    require(canonical(build_request(plan, result)) == raw, "request_mismatch")
    return ROOT, STATE, plan, registration, packet, result, raw.decode("utf-8"), deadline


def interrupt(_signum, _frame):
    raise Refused("interrupted_or_expired")


def phase_paths(phase):
    require(phase in {"registration", "paid"}, "invalid_phase")
    if phase == "registration":
        return ("registration-launch.json", "registration-owned.json", "registration-start.json",
                "registration-exit.json", "registration.stdout", "registration.stderr")
    return ("paid-launch.json", "owned.json", "start.json", "exit.json", "worker.stdout", "worker.stderr")


def check_start(phase, window, consumed_raw):
    launch_path, owned_path, start_path, *_ = phase_paths(phase)
    launch_raw = read(STATE / launch_path, private=True)
    launch = parse(launch_raw)
    owned_raw = read(STATE / owned_path, private=True)
    owned = parse(owned_raw)
    start = parse(read(STATE / start_path, private=True))
    require(os.getppid() == window["parent_pid"] == owned["parent_pid"] == start["parent_pid"]
            == launch["parent_pid"] and launch["plan_sha256"] == window["plan_sha256"]
            and launch["consumed_sha256"] == sha(consumed_raw)
            and os.getpid() == owned["pid"] == start["pid"]
            and owned["phase"] == start["phase"] == phase
            and owned["consumed_sha256"] == start["consumed_sha256"] == sha(consumed_raw)
            and start["owned_sha256"] == sha(owned_raw)
            and start["launch_sha256"] == owned[phase + "_launch_sha256"] == sha(launch_raw),
            "unowned_child")
    remaining(window)


def await_grant(phase, fd):
    """The pipe byte can only be released after the parent has a usable Popen handle."""
    require(type(fd) is int and fd > 2 and stat.S_ISFIFO(os.fstat(fd).st_mode)
            and fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE == os.O_RDONLY, "invalid_gate")
    consumed_raw = read(STATE / "consumed.json", private=True)
    window = parse(consumed_raw)
    try:
        while True:
            require(os.getppid() == window["parent_pid"], "lost_parent")
            ready, _, _ = select.select([fd], [], [], min(0.25, remaining(window)))
            if ready:
                require(os.read(fd, 2) == b"G", "start_not_granted")
                break
    finally:
        os.close(fd)
    check_start(phase, window, consumed_raw)


def registration_child(fd):
    await_grant("registration", fd)
    consumed = parse(read(STATE / "consumed.json", private=True))
    plan, registry, packet = load_plan(consumed["plan_sha256"])
    launch = parse(read(STATE / "registration-launch.json", private=True))
    require(launch["plan_sha256"] == consumed["plan_sha256"]
            and launch["packet_sha256"] == plan["registry_packet_sha256"]
            and launch["attempt_id"] == packet["attempt_id"], "unbound_registration")
    require(remaining(consumed) > registry.WORK_SECONDS + registry.CLEANUP_SECONDS, "preparation_time")
    result = registry.run(INPUTS / "registration.json", plan["registry_packet_sha256"])
    arm(consumed)
    result_hash = sha(canonical(result))
    require(registration_result(packet, result_hash) == result, "registration_changed")
    publish(STATE / "registration-returned.json", {"status": "registration_returned",
            "result_sha256": result_hash, "registration_launch_sha256": sha(canonical(launch))})
    check_start("registration", consumed, read(STATE / "consumed.json", private=True))
    print('{"status":"registration_returned"}', flush=True)


def wait_child(child, window):
    # Recheck the wall clock after sleep even on systems where monotonic time
    # excludes some suspended time. A timeout on this poll is not a child exit.
    while True:
        try:
            code = child.wait(timeout=min(0.25, remaining(window)))
        except subprocess.TimeoutExpired:
            continue
        remaining(window)
        return code


def cleanup_child(child, window):
    """Attempt termination once and distinguish late, absent and timely observations."""
    observed = False
    cleanup_end = time.monotonic() + CLEANUP
    def left():
        seconds = min(cleanup_end - time.monotonic(), remaining(window, cleanup=True))
        require(seconds > 0, "deadline")
        return seconds
    try:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=min(0.7, left()))
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=left())
        observed = child.returncode is not None
        left()
        return "owned_child_reaped" if observed else "cleanup_unobserved"
    except BaseException:
        if observed:
            return "terminal_observed_late"
        return "cleanup_unobserved"


def launch_phase(phase, argv, window, consumed_sha, launch_sha):
    _, owned_path, start_path, exit_path, outpath, errpath = phase_paths(phase)
    reader, writer = os.pipe()
    child = None
    spawn_started = False
    terminal_observed = False
    try:
        def log(name):
            return os.fdopen(os.open(STATE / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), "wb")
        with log(outpath) as out, log(errpath) as err:
            spawn_started = True
            child = subprocess.Popen([*argv, "--gate-fd", str(reader)], env={}, cwd="/",
                    stdin=subprocess.DEVNULL, stdout=out, stderr=err, close_fds=True,
                    pass_fds=(reader,), start_new_session=True)
            pid = child.pid
            owned_sha = publish(STATE / owned_path, {"pid": pid, "parent_pid": os.getpid(),
                    "phase": phase, "consumed_sha256": consumed_sha, phase + "_launch_sha256": launch_sha})
            start_sha = publish(STATE / start_path, {"phase": phase, "pid": pid,
                    "parent_pid": os.getpid(), "consumed_sha256": consumed_sha,
                    "launch_sha256": launch_sha, "owned_sha256": owned_sha})
            remaining(window)
            require(os.write(writer, b"G") == 1, "grant_failed")
            os.close(writer)
            writer = None
            code = wait_child(child, window)
            terminal_observed = True
        child = None
        stdout = read(STATE / outpath, private=True, limit=8192)
        stderr = read(STATE / errpath, private=True, limit=8192)
        receipt = {"returncode": code, "pid": pid, "stdout_sha256": sha(stdout),
                   "stderr_sha256": sha(stderr), "owned_child_reaped": True,
                   phase + "_launch_sha256": launch_sha, "owned_sha256": owned_sha,
                   "start_sha256": start_sha}
        exit_sha = publish(STATE / exit_path, receipt)
        expected = b'{"status":"registration_returned"}\n' if phase == "registration" else b'{"status":"broker_returned"}\n'
        require(code == 0 and stdout == expected and not stderr, "phase_refused")
        return exit_sha
    except BaseException:
        # Close the grant first. An interrupted spawn without a returned handle
        # cannot pass the start gate, even if the OS started an unknown child.
        if writer is not None:
            os.close(writer)
            writer = None
        # A poll and the kernel work alarm can expire almost simultaneously.
        # Move the one-shot alarm to the original final cutoff before cleanup
        # writes; otherwise a stale work signal can interrupt their publication.
        try:
            arm(window, cleanup=True)
        except Refused:
            pass
        cleanup = ("owned_child_reaped" if terminal_observed else
                   "launch_ownership_unknown" if spawn_started else "child_not_started")
        if child is not None:
            cleanup = cleanup_child(child, window)
        try:
            remaining(window, cleanup=True)
            publish(STATE / (phase + "-uncertainty.json"), {"cleanup": cleanup, "phase": phase,
                    "phase_descendants_quiet_verified": False, "automatic_retry": False})
        except BaseException:
            pass
        raise
    finally:
        if writer is not None:
            os.close(writer)
        os.close(reader)


def supervise(plan_sha):
    window = {"start_monotonic": time.monotonic(), "start_wall": time.time()}
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM)}
    consumed = False
    for sig in handlers:
        signal.signal(sig, interrupt)
    try:
        arm(window)
        require(HERE == ROOT / "runtime/development-cycle-launch-v2-preparation",
                "unexpected_source_location")
        plan, registry, packet = load_plan(plan_sha)
        private_directory(STATE)
        require(not any(STATE.iterdir()), "cycle_already_consumed")
        consumed_sha = publish(STATE / "consumed.json", {**window, "limit_seconds": LIMIT,
                "plan_sha256": plan_sha, "supervisor_sha256": plan["supervisor_sha256"],
                "automatic_retry": False, "parent_pid": os.getpid()})
        consumed = True
        require(remaining(window) > registry.WORK_SECONDS + registry.CLEANUP_SECONDS, "preparation_time")
        reg_launch = publish(STATE / "registration-launch.json", {"plan_sha256": plan_sha,
                "parent_pid": os.getpid(), "consumed_sha256": consumed_sha,
                "packet_sha256": plan["registry_packet_sha256"], "attempt_id": packet["attempt_id"]})
        reg_exit = launch_phase("registration", [str(PYTHON), "-I", "-S", "-B",
                                str(HERE / "supervise.py"), "--registration-child"],
                                window, consumed_sha, reg_launch)
        reg_return = parse(read(STATE / "registration-returned.json", private=True))
        require(reg_return["registration_launch_sha256"] == reg_launch, "registration_changed")
        result_sha = digest_text(reg_return["result_sha256"])
        result = registration_result(packet, result_sha)
        load_plan(plan_sha)
        remaining(window)
        request_sha = publish(STATE / "request.json", build_request(plan, result))
        launch_sha = publish(STATE / "paid-launch.json", {"plan_sha256": plan_sha, "parent_pid": os.getpid(),
                "consumed_sha256": consumed_sha, "request_sha256": request_sha,
                "registration_result_sha256": result_sha, "registration_exit_sha256": reg_exit})
        exit_sha = launch_phase("paid", [str(PYTHON), "-I", "-S", "-B", str(HERE / "paid_worker.py")],
                                window, consumed_sha, launch_sha)
        terminal_raw = read(STATE / "terminal.json", private=True)
        terminal = parse(terminal_raw)
        require(terminal["status"] == "broker_returned" and terminal["operational_acceptance"] is False
                and terminal["investment_validation"] is False, "invalid_terminal")
        pinned(STATE / "outcome.json", terminal["outcome_sha256"], private=True)
        remaining(window)
        publish(STATE / "result.json", {"status": "broker_returned", "plan_sha256": plan_sha,
                "outcome_sha256": terminal["outcome_sha256"], "audit_required": True,
                "terminal_sha256": sha(terminal_raw), "consumed_sha256": consumed_sha,
                "paid_launch_sha256": launch_sha, "registration_result_sha256": result_sha,
                "request_sha256": request_sha, "exit_sha256": exit_sha,
                "operational_acceptance": False, "investment_validation": False})
        remaining(window)
        return 0
    except BaseException as exc:
        if consumed:
            try:
                arm(window, cleanup=True)
                publish(STATE / "failure.json", {"status": "refused_or_uncertain",
                        "reason": str(exc) if type(exc) is Refused else "cycle_failed",
                        "automatic_retry": False, "investment_validation": False})
            except BaseException:
                pass
        return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        for sig, handler in handlers.items():
            signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-sha256")
    parser.add_argument("--registration-child", action="store_true")
    parser.add_argument("--gate-fd", type=int)
    args = parser.parse_args()
    if args.registration_child:
        if args.plan_sha256 is not None or args.gate_fd is None:
            return 1
        try:
            registration_child(args.gate_fd)
            return 0
        except BaseException:
            return 1
    if args.gate_fd is not None or args.plan_sha256 is None:
        return 1
    code = supervise(digest_text(args.plan_sha256))
    print(json.dumps({"status": "broker_returned" if code == 0 else "refused_or_uncertain",
                      "audit_required": True, "automatic_retry": False}), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

"""One selected CLI step, with private bounded output and an external deadline.

This supervises cooperating reviewed code, not a hostile filesystem owner.
Existing authority must match; no bootstrap, repair, retry or order is intended.
Preflight checks are local. The execution deadline starts immediately before
spawning the child. Each reap wait is bounded at five seconds; exceptional
cleanup can make two such waits. Local preflight and persistence I/O are not
preempted by that execution timer. The parent never reads .env and supplies no
inherited environment to the child.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import select
import selectors
import signal
import stat
import subprocess
import sys
import time

COMMANDS = frozenset({"register-campaign", "acquire-bars", "acquire-calendar", "acquire-actions",
                     "register-dataset", "admit-dataset", "bind-campaign-data", "run-campaign"})
MAX_REQUEST = 64 * 1024
MAX_STDOUT = 256 * 1024
MAX_STDERR = 64 * 1024
CLEANUP_SECONDS = 5


class Refused(ValueError):
    """Program-owned, non-sensitive reason code."""


def need(value, reason):
    if not value:
        raise Refused(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def path_check(path):
    need(path.is_absolute() and ".." not in path.parts
         and all(not p.is_symlink() for p in (path, *path.parents)), "unsafe_path")


def physical(path, *, private=False, directory=False):
    path_check(path)
    info = path.lstat()
    need((stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
         and info.st_uid in ({os.getuid()} if private else {0, os.getuid()})
         and not info.st_mode & 0o022, "unsafe_file")
    if not directory:
        need(info.st_nlink == 1, "unsafe_file")
    if private:
        need(stat.S_IMODE(info.st_mode) == (0o700 if directory else 0o600), "unsafe_private_mode")
    return {"device": info.st_dev, "inode": info.st_ino, "uid": info.st_uid,
            "mode": stat.S_IMODE(info.st_mode)}


def read(path, *, private=False, limit=2 * 1024 * 1024):
    identity = physical(path, private=private)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as source:
        before = os.fstat(source.fileno())
        need(before.st_size <= limit and (before.st_dev, before.st_ino) ==
             (identity["device"], identity["inode"]), "file_changed")
        raw = source.read(limit + 1)
        after = os.fstat(source.fileno())
    need(len(raw) == before.st_size <= limit and before.st_mtime_ns == after.st_mtime_ns
         and before.st_ctime_ns == after.st_ctime_ns and identity == physical(path, private=private),
         "file_changed")
    return raw


def save(path, value):
    raw = value if isinstance(value, bytes) else canonical(value) + b"\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as target:
        target.write(raw)
        target.flush()
        os.fsync(target.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def source_identity(source_root):
    """Only public product Python and this supervisor; never .env or data."""
    source_root = Path(source_root)
    physical(source_root, directory=True)
    directory = source_root / "src" / "quanto"
    physical(directory, directory=True)
    paths = sorted(directory.glob("*.py"))
    need(3 <= len(paths) <= 128 and {"__init__.py", "cli.py", "evaluation_registry.py"}
         <= {p.name for p in paths}, "source_roster_invalid")
    files, total = {}, 0
    for path in paths:
        raw = read(path)
        total += len(raw)
        need(total <= 16 * 1024 * 1024, "source_limit")
        files[path.name] = sha(raw)
    return sha(canonical({"files": files, "supervisor_sha256": sha(read(Path(__file__).absolute()))}))


def authority_identity(root):
    """Existing physical identity; normal child Supervisor verifies configuration."""
    return {"root": physical(root, directory=True),
            "control": physical(root / "runtime/access-control/control.sqlite", private=True),
            "research": physical(root / "runtime/research.sqlite", private=True)}


def verify(plan):
    need(plan["command"] in COMMANDS, "command_forbidden")
    need(type(plan["timeout"]) in (int, float) and math.isfinite(plan["timeout"])
         and 0 < plan["timeout"] <= 360, "timeout_invalid")
    need(source_identity(Path(plan["source_root"])) == plan["source_sha256"], "source_mismatch")
    need(sha(read(Path(plan["python"]), limit=64 * 1024 * 1024)) == plan["python_sha256"],
         "python_mismatch")
    need(authority_identity(Path(plan["runtime_root"])) == plan["authority"], "authority_changed")
    request = read(Path(plan["attempt"]) / "request.json", private=True, limit=MAX_REQUEST)
    need(sha(request) == plan["request_sha256"], "request_mismatch")
    request.decode("utf-8")


def child(attempt, gate_fd=None):
    """Fixed isolated child entrypoint; a second invocation cannot dispatch."""
    try:
        need(type(gate_fd) is int and gate_fd >= 3, "launch_gate_missing")
        with os.fdopen(gate_fd, "rb", buffering=0) as gate:
            need(select.select([gate], [], [], CLEANUP_SECONDS)[0], "launch_gate_expired")
            need(gate.read(1) == b"\x01", "launch_gate_closed")
        physical(attempt, private=True, directory=True)
        plan = json.loads(read(attempt / "intent.json", private=True, limit=MAX_REQUEST))
        need(Path(plan["attempt"]) == attempt, "attempt_mismatch")
        save(attempt / "child-started.json", {"pid": os.getpid(), "started_at": stamp()})
        verify(plan)
        sys.path.insert(0, str(Path(plan["source_root"]) / "src"))
        from quanto.evaluation_registry import AccessError, Supervisor
        from quanto.cli import main as cli_main
        root = Path(plan["runtime_root"])
        # Both files must still exist. The normal constructor checks its stored
        # root/device/inode/schema identity; a mismatch is never repaired.
        need(authority_identity(root) == plan["authority"], "authority_changed")
        try:
            supervisor = Supervisor(root)
        except AccessError as exc:
            print(json.dumps({"child_refusal": exc.reason}), file=sys.stderr)
            return 70
        need(authority_identity(root) == plan["authority"], "authority_changed")
        with supervisor.session():
            code = cli_main(["--root", str(root), plan["command"],
                             "--request", str(attempt / "request.json")])
        verify(plan)
        return code
    except Exception:
        # CLI stderr and all returned content remain private in the supervisor.
        print("supervised_child_refused", file=sys.stderr)
        return 70


def _alive(group):
    try:
        os.killpg(group, 0)
        return True
    except ProcessLookupError:
        return False
    except OSError:
        # Permission/observation failure never establishes that a group is gone.
        return True


def _stop(proc):
    confirmed = True
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        confirmed = False
    try:
        proc.wait(timeout=CLEANUP_SECONDS)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return confirmed and not _alive(proc.pid)


def _capture(plan, attempt):
    proc, reason, cleanup, launched = None, "exited", True, False
    counts = {"stdout": 0, "stderr": 0}
    limits = {"stdout": MAX_STDOUT, "stderr": MAX_STDERR}
    files = {}
    started = time.monotonic()
    wall_started = time.time()
    previous = {}
    gate_read, gate_write = None, None

    def interrupted(_signum, _frame):
        raise InterruptedError

    def remaining():
        return min(deadline - time.monotonic(), wall_deadline - time.time())

    try:
        for name in counts:
            fd = os.open(attempt / (name + ".bin"), os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | os.O_NOFOLLOW, 0o600)
            files[name] = os.fdopen(fd, "wb")
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, interrupted)
        verify(plan)
        # -B alone still reads stale .pyc files; an exclusive empty prefix makes
        # this launch import the pinned source bytes, without creating caches.
        cache = attempt / "pycache"
        cache.mkdir(mode=0o700)
        gate_read, gate_write = os.pipe()
        command = [plan["python"], "-I", "-S", "-B", "-X", "pycache_prefix=" + str(cache),
                   str(Path(__file__).absolute()), "--child", str(attempt), str(gate_read)]
        deadline = time.monotonic() + plan["timeout"]
        wall_deadline = time.time() + plan["timeout"]
        launched = True  # A spawn exception cannot prove that no effect occurred.
        proc = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=attempt, close_fds=True, start_new_session=True,
            pass_fds=(gate_read,),
            env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"})
        need(remaining() > 0, "deadline")
        os.write(gate_write, b"\x01")
        os.close(gate_write)
        gate_write = None
        os.close(gate_read)
        gate_read = None
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
            selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
            while selector.get_map():
                wait = remaining()
                if wait <= 0:
                    raise TimeoutError
                # A wall-clock jump/suspend must be noticed even when no child
                # output arrives. Monotonic time prevents backward jumps extending work.
                for ready, _ in selector.select(min(wait, 0.25)):
                    name = ready.data
                    room = limits[name] - counts[name]
                    chunk = os.read(ready.fd, min(8192, room + 1))
                    if not chunk:
                        selector.unregister(ready.fileobj)
                        continue
                    files[name].write(chunk[:room])
                    counts[name] += min(len(chunk), room)
                    need(len(chunk) <= room, "output_limit")
            while proc.poll() is None:
                need(remaining() > 0, "deadline")
                try:
                    proc.wait(timeout=max(0.001, min(0.25, remaining())))
                except subprocess.TimeoutExpired:
                    pass
        need(remaining() > 0, "deadline")
        if _alive(proc.pid):
            reason = "unexpected_descendants"
            cleanup = _stop(proc)
    except (TimeoutError, subprocess.TimeoutExpired):
        reason = "deadline"
    except InterruptedError:
        reason = "interrupted"
    except Refused as exc:
        reason = str(exc)
    except Exception:
        reason = "process_failure"
    finally:
        # A repeated terminal signal must not interrupt reap/receipt cleanup.
        for signum in previous:
            signal.signal(signum, signal.SIG_IGN)
        for descriptor in (gate_read, gate_write):
            if descriptor is not None:
                os.close(descriptor)
        if proc is not None:
            if proc.poll() is None or _alive(proc.pid):
                cleanup = _stop(proc) and cleanup
            for stream in (proc.stdout, proc.stderr):
                try:
                    stream.close()
                except OSError:
                    cleanup = False
        elif launched:
            cleanup = False
        for stream in files.values():
            try:
                stream.flush()
                os.fsync(stream.fileno())
            except OSError:
                reason = "output_persistence_failed"
            finally:
                try:
                    stream.close()
                except OSError:
                    reason = "output_persistence_failed"
        for signum, handler in previous.items():
            signal.signal(signum, handler)
    return {"reason": reason, "exit_code": proc.returncode if proc else None,
            "launch_attempted": launched, "pid": proc.pid if proc else None,
            "cleanup_confirmed": cleanup, "elapsed_seconds": time.monotonic() - started,
            "wall_elapsed_seconds": max(0, time.time() - wall_started),
            "stdout_bytes": counts["stdout"], "stderr_bytes": counts["stderr"]}


def supervise_step(*, command, runtime_root, source_root, python, request, attempt,
                   source_sha256, python_sha256, request_sha256, timeout=120):
    """An existing attempt directory is always refused, including after a crash."""
    attempt = Path(attempt)
    physical(attempt.parent, directory=True)
    path_check(attempt)
    try:
        attempt.mkdir(mode=0o700)
    except FileExistsError:
        raise Refused("attempt_already_exists") from None
    started, plan, launch_possible = stamp(), None, False
    try:
        need(command in COMMANDS, "command_forbidden")
        need(type(timeout) in (int, float) and math.isfinite(timeout)
             and 0 < timeout <= 360, "timeout_invalid")
        request_bytes = read(Path(request), private=True, limit=MAX_REQUEST)
        need(sha(request_bytes) == request_sha256, "request_mismatch")
        request_bytes.decode("utf-8")
        save(attempt / "request.json", request_bytes)
        plan = {"command": command, "runtime_root": str(runtime_root), "source_root": str(source_root),
                "python": str(python), "attempt": str(attempt), "source_sha256": source_sha256,
                "python_sha256": python_sha256, "request_sha256": request_sha256,
                "timeout": timeout, "authority": authority_identity(Path(runtime_root))}
        verify(plan)
        save(attempt / "intent.json", plan)
        launch_possible = True
        result = _capture(plan, attempt)
        try:
            verify(plan)
            unchanged = True
        except Exception:
            unchanged = False
        result["identities_unchanged"] = unchanged
        result["status"] = ("completed" if result["reason"] == "exited"
                            and result["cleanup_confirmed"] and unchanged else "uncertain")
    except Refused as exc:
        result = {"status": "uncertain" if launch_possible else "refused", "reason": str(exc),
                  "exit_code": None, "cleanup_confirmed": not launch_possible}
    except Exception:
        result = {"status": "uncertain" if launch_possible else "refused",
                  "reason": "supervision_unavailable" if launch_possible else "preflight_unavailable",
                  "exit_code": None, "cleanup_confirmed": not launch_possible}
    receipt = {"schema_version": 1, "command": command if command in COMMANDS else "forbidden",
               "started_at": started, "finished_at": stamp(), **result}
    receipt["intent_sha256"] = sha(canonical(plan) + b"\n") if plan else None
    for name in ("stdout", "stderr"):
        path = attempt / (name + ".bin")
        if path.exists():
            receipt[name + "_sha256"] = sha(read(path, private=True, limit=MAX_STDOUT))
    save(attempt / "receipt.json", receipt)
    return receipt


def main():
    if len(sys.argv) in (3, 4) and sys.argv[1] == "--child":
        gate = int(sys.argv[3]) if len(sys.argv) == 4 else None
        return child(Path(sys.argv[2]), gate)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", choices=sorted(COMMANDS), required=True)
    for name in ("runtime-root", "source-root", "python", "request", "attempt"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("source-sha256", "python-sha256", "request-sha256"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--timeout", type=float, default=120)
    try:
        result = supervise_step(**vars(parser.parse_args()))
    except Refused as exc:
        print(json.dumps({"status": "refused", "reason": str(exc)}))
        return 1
    except Exception:
        print(json.dumps({"status": "uncertain", "reason": "supervisor_unavailable"}))
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "completed" and result["exit_code"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""A new, finite D008 trace/numerical auditor. No broker or engine replay.

Only a future lead-bound packet may select private inputs. The preparation task
runs this on invented fixtures; old consumed verifiers are never loaded/run.
"""

from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sqlite3
import stat
import subprocess
import sys
import time

HERE = Path(__file__).absolute().parent
ACTUAL_ROOT = Path("/Users/ronoktanvir/Documents/ChatGPT/quanto")
PYTHON = Path("/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11")
ORACLE_SHA = "54887dfae2f12430b5cdd9901c0c3ba367541f6eb4714b987ad68e08f0433ca1"
SECONDS = 600
TOOLS = {
    "audit_cycle.py",
    "audit_boundary.py",
    "cycle_evidence.py",
    "trace_checks.py",
    "context_checks.py",
    "independent_oracle.py",
}
FLAGS = dict(
    operational_acceptance=False,
    investment_validation=False,
    investment_evidence=False,
    protected_eligible=False,
    external_restore=False,
    unattended_ready=False,
    live_execution_enabled=False,
    financial_engine_replayed=False,
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate")
            result[key] = value
        return result

    def bad(_):
        raise ValueError("constant")

    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("bound")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def raw_file(path, maximum=1024 * 1024, private=True):
    path = Path(path)
    if (
        not path.is_absolute()
        or ".." in path.parts
        or any(p.is_symlink() for p in (path, *path.parents))
    ):
        raise ValueError("path")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_size > maximum
            or info.st_mode & 0o022
        ):
            raise ValueError("file")
        if private and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600):
            raise ValueError("private")
        raw = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
        current = path.lstat()

        def identity(s):
            return (
                s.st_dev,
                s.st_ino,
                s.st_size,
                s.st_mtime_ns,
                s.st_ctime_ns,
                s.st_mode,
                s.st_uid,
            )

        if (
            len(raw) > maximum
            or identity(info) != identity(after)
            or identity(info) != identity(current)
        ):
            raise ValueError("changed")
    return raw


def import_checked(name, path, digest):
    raw = raw_file(path)
    if sha(raw) != digest:
        raise ValueError("source")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec", dont_inherit=True, optimize=0), module.__dict__)
    return module


def load_boundary(manifest_path, manifest_sha):
    raw = raw_file(manifest_path, 16 * 1024 * 1024)
    if sha(raw) != manifest_sha:
        raise ValueError("manifest")
    manifest = strict(raw)
    if set(manifest["tools"]) != TOOLS or manifest["oracle_sha256"] != ORACLE_SHA:
        raise ValueError("tools")
    for name, digest in manifest["tools"].items():
        if sha(raw_file(HERE / name)) != digest:
            raise ValueError("tool_changed")
    return import_checked(
        "fresh_cycle_boundary", HERE / "audit_boundary.py", manifest["tools"]["audit_boundary.py"]
    ), manifest


def validate_packet(packet, fixture, b):
    b.need(
        type(packet) is dict
        and set(packet)
        == {
            "schema_version",
            "kind",
            "runtime_root",
            "source_root",
            "attempt_id",
            "request_file",
            "outcome_file",
            "expected_state",
            "prelaunch",
            "plan_sha256",
        },
        "invalid_packet",
    )
    b.need(
        packet["schema_version"] == 1 and packet["kind"] == "d008_fresh_cycle_audit",
        "invalid_packet",
    )
    b.digest(packet["plan_sha256"])
    root, source = Path(packet["runtime_root"]), Path(packet["source_root"])
    b.directory(root)
    b.directory(source)
    b.need(type(fixture) is bool, "invalid_packet")
    if fixture:
        b.need(root.is_relative_to(HERE / "rehearsals") and root != ACTUAL_ROOT, "fixture_boundary")
    else:
        b.need(root == ACTUAL_ROOT, "fixture_boundary")
    b.need(
        type(packet["attempt_id"]) is str
        and __import__("re").fullmatch("[a-z0-9][a-z0-9-]{0,63}", packet["attempt_id"]),
        "invalid_packet",
    )
    for key in ("request_file", "outcome_file"):
        record = packet[key]
        b.need(type(record) is dict and set(record) == {"path", "sha256"}, "invalid_packet")
        path = Path(record["path"])
        b.pathcheck(path)
        b.digest(record["sha256"])
        b.need(path.is_relative_to(root / "runtime") and path.suffix == ".json", "invalid_packet")
    b.need(packet["request_file"]["path"] != packet["outcome_file"]["path"], "invalid_packet")
    checkpoint = packet["prelaunch"]
    b.need(
        type(checkpoint) is dict
        and set(checkpoint)
        == {
            "event_count",
            "event_head_sha256",
            "request_sha256",
            "run_key",
            "suite_sha256",
            "failure_roster_sha256",
        },
        "invalid_packet",
    )
    b.need(
        type(checkpoint["event_count"]) is int and 1 <= checkpoint["event_count"] <= 100000,
        "invalid_packet",
    )
    b.need(
        type(checkpoint["run_key"]) is str and 1 <= len(checkpoint["run_key"]) <= 64,
        "invalid_packet",
    )
    for key in ("event_head_sha256", "request_sha256", "suite_sha256", "failure_roster_sha256"):
        b.digest(checkpoint[key])
    b.need(checkpoint["request_sha256"] == packet["request_file"]["sha256"], "request_mismatch")
    return root, source


def no_network_profile(frame, event, arg):
    if event != "call":
        return
    pair = (frame.f_globals.get("__name__", ""), frame.f_code.co_name)
    forbidden = {
        ("quanto.research", "run_backtest"),
        ("quanto.event_engine", "run_event_backtest"),
        ("quanto.explorer", "run_submission"),
        ("quanto.study_suite", "run_suite"),
        ("quanto.research_comparison", "run_comparison"),
        ("quanto.research_broker", "run_workflow"),
        ("quanto.provider", "local_key"),
        ("quanto.provider", "send_research_text"),
        ("quanto.alpaca_data", "acquire_bars"),
        ("quanto.alpaca_data", "acquire_calendar"),
        ("quanto.alpaca_actions", "acquire_actions"),
    }
    if pair in forbidden:
        raise ValueError("forbidden_call")


def budget_snapshot(db, b):
    result = {}
    for name in (
        "reservations",
        "provider_allocations",
        "dispatches",
        "research_dispatch_holds",
        "research_model_observations",
    ):
        rows = [
            dict(row) for row in db.execute("SELECT * FROM " + name + " ORDER BY rowid LIMIT 50001")
        ]
        b.need(len(rows) <= 50000, "invalid_result")
        result[name] = {"count": len(rows), "sha256": b.sha(b.canonical(rows))}
    return result


def extra_trace(store, saved, request_raw, fixture, checkpoint, b):
    from quanto.research_broker import DEFAULT_MODELS, _configuration, _contracts, code_identity
    from quanto.research_workflow import ROLES
    from quanto.explorer import _code_identity

    expected = _configuration(request_raw.decode(), fixture)
    b.need(expected["models"] == DEFAULT_MODELS, "request_mismatch")
    from quanto.ledger import hash_json

    b.need(
        expected["run_key"] == checkpoint["run_key"]
        and expected["suite_sha256"] == checkpoint["suite_sha256"]
        and hash_json(expected["failure_ids"]) == checkpoint["failure_roster_sha256"]
        and sha(request_raw) == checkpoint["request_sha256"],
        "request_mismatch",
    )
    parent = store.get_submission(saved["submission_id"])
    db = store.journal.connection
    cut = db.execute(
        "SELECT event_hash FROM events WHERE id=?", (checkpoint["event_count"],)
    ).fetchone()
    b.need(
        cut is not None and cut["event_hash"] == checkpoint["event_head_sha256"], "lineage_mismatch"
    )
    manifest = store.read_json(expected["suite_sha256"])
    registered = store.get_submission(manifest["submission_id"])
    b.need(
        registered["kind"] == "study_suite_registration"
        and registered["status"] == "success"
        and registered["details"]["suite_sha256"] == expected["suite_sha256"],
        "lineage_mismatch",
    )

    def position(kind, submission_id):
        hits = [
            row["id"]
            for row in db.execute("SELECT id,payload FROM events WHERE kind=? ORDER BY id", (kind,))
            if strict(row["payload"].encode()).get("submission_id") == submission_id
        ]
        b.need(len(hits) == 1, "lineage_mismatch")
        return hits[0]

    b.need(
        position("submission_finished", manifest["submission_id"])
        <= checkpoint["event_count"]
        < position("submission_started", saved["submission_id"]),
        "lineage_mismatch",
    )
    b.need(
        parent["kind"] == "research_broker_run"
        and parent["request_sha256"] == sha(request_raw)
        and parent["request_bytes"] == len(request_raw),
        "request_mismatch",
    )
    rows = db.execute(
        "SELECT * FROM research_broker_runs WHERE submission_id=?", (saved["submission_id"],)
    ).fetchall()
    if (
        not rows
        and saved["status"] == "invalid"
        and saved.get("dispatch_counts") == {"authorized": 0, "response_observed": 0}
        and not saved.get("stages")
    ):
        return {}, None
    b.need(len(rows) == 1, "lineage_mismatch")
    run = rows[0]
    config = store.read_json(run["configuration_sha256"])
    b.need(
        {k: config[k] for k in expected} == expected and config["code_identity"] == code_identity(),
        "request_mismatch",
    )
    contracts = _contracts(DEFAULT_MODELS)
    assignments = db.execute(
        "SELECT * FROM workflow_assignments WHERE run_id=?", (run["workflow_run_id"],)
    ).fetchall()
    b.need(
        len(assignments) <= 7 and len({r["role"] for r in assignments}) == len(assignments),
        "lineage_mismatch",
    )
    b.need(
        all(
            r["role"] in ROLES and strict(r["contract"].encode()) == contracts[r["role"]]
            for r in assignments
        ),
        "lineage_mismatch",
    )
    b.need(len({r["actor_id"] for r in assignments}) == len(assignments), "lineage_mismatch")
    manifest = strict(
        db.execute("SELECT manifest FROM workflow_runs WHERE run_id=?", (run["workflow_run_id"],))
        .fetchone()[0]
        .encode()
    )
    from quanto.ledger import hash_json

    b.need(
        manifest["specification_sha256"] == hash_json(expected)
        and manifest["code_sha256"] == hash_json(code_identity()),
        "lineage_mismatch",
    )
    return {"sources": code_identity()["sources"], "financial_identity": _code_identity()}, run


# One invocation per process. A wall-clock jump or a macOS sleep can shorten the
# monotonic allowance, but can never grant more time to a stalled operation.
_WINDOW = None


def remaining(deadline):
    value = deadline - time.monotonic()
    if _WINDOW is not None:
        start_mono, start_wall = _WINDOW
        value = min(value, start_wall + (deadline - start_mono) - time.time())
    if value <= 0:
        raise TimeoutError("audit_deadline")
    return value


def arm(deadline):
    signal.setitimer(signal.ITIMER_REAL, remaining(deadline))


def wait_terminal(child, deadline):
    while True:
        try:
            code = child.wait(timeout=min(0.25, remaining(deadline)))
        except subprocess.TimeoutExpired:
            continue
        remaining(deadline)
        return code


def reap_once(child, deadline, group=False):
    observation = {
        "pid": child.pid,
        "kill_attempted": False,
        "reaped": False,
        "status": "cleanup_unobserved",
        "cleanup_deadline": deadline,
    }
    try:
        remaining(deadline)
        code = child.poll()
        remaining(deadline)
        if code is None:
            observation["kill_attempted"] = True
            if group:
                if os.getpgid(child.pid) != child.pid:
                    raise ValueError("ownership")
                os.killpg(child.pid, signal.SIGKILL)
            else:
                child.kill()
            child.wait(timeout=remaining(deadline))
            code = child.returncode
        remaining(deadline)
        if code is None:
            raise TimeoutError("cleanup_unobserved")
        observation.update(reaped=True, status="terminal_observed", returncode=code)
    except BaseException:
        pass
    return observation


def evidence_module(manifest):
    return import_checked(
        "fresh_cycle_evidence", HERE / "cycle_evidence.py", manifest["tools"]["cycle_evidence.py"]
    )


def oracle_case(store, child, attempt, verification_id, b, deadline, cleanup_deadline):
    """Fresh rational comparison, with distinct provenance; no financial engine call."""
    from quanto.ledger import canonical_json

    request = child["request"]
    result = child["result"]
    cost = request["specification"]["cost_bps"]
    b.need(type(cost) in (int, float) and cost in (0, 10, 25), "invalid_result")
    sid = store.begin(
        "d008_fresh_independent_oracle",
        {
            "audit_submission_id": verification_id,
            "child_submission_id": child["submission_id"],
            "result_sha256": child["details"]["artifact_sha256"],
            "oracle_sha256": ORACLE_SHA,
        },
    )
    refs = []
    proc = None
    try:
        rows = store.read_json(store.read_json(request["dataset_sha256"])["bars_sha256"])["bars"]
        b.need(type(rows) is list and 0 < len(rows) <= 20000, "invalid_result")
        days = [datetime.fromisoformat(r["timestamp"]).date().isoformat() for r in rows]
        b.need(days == sorted(set(days)), "invalid_result")
        first, last = days.index(request["evaluation_start"]), days.index(request["evaluation_end"])
        lookback = request["specification"]["lookback"]
        b.need(type(lookback) is int and 0 < lookback <= first <= last, "invalid_result")
        selected = rows[first - lookback : last + 1]
        count = last - first + 1
        for name in ("strategy", "benchmark"):
            actual = result["engine_report"][name]["daily_equity"]
            b.need(
                len(actual) == count
                and [r["timestamp"] for r in actual]
                == [r["timestamp"] for r in selected[lookback:]],
                "invalid_result",
            )
        payload = {
            "bars": selected,
            "specification": request["specification"],
            "corporate_action_events": result["admission_evidence"]["actions"],
            "engine_report": result["engine_report"],
        }
        raw = canonical_json(payload).encode()
        b.need(len(raw) <= 16 * 1024 * 1024, "invalid_result")
        payload_ref = store.put_bytes(raw)
        refs.append(payload_ref)
        target = attempt / ("oracle-input-" + str(int(cost)) + ".json")
        b.exclusive(target, payload)
        b.need(sha(raw_file(HERE / "independent_oracle.py")) == ORACLE_SHA, "source_mismatch")
        stdout, stderr = (
            attempt / ("oracle-" + str(int(cost)) + ".stdout"),
            attempt / ("oracle-" + str(int(cost)) + ".stderr"),
        )
        started = time.monotonic()
        oracle_deadline = min(deadline, started + 60)
        oracle_cleanup = min(cleanup_deadline, oracle_deadline + 5)
        remaining(oracle_deadline)
        with stdout.open("xb") as out, stderr.open("xb") as err:
            proc = subprocess.Popen(
                [
                    str(PYTHON),
                    "-I",
                    "-S",
                    "-B",
                    str(HERE / "independent_oracle.py"),
                    "--input",
                    str(target),
                ],
                cwd=str(attempt),
                env={},
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=err,
                close_fds=True,
            )
            code = wait_terminal(proc, oracle_deadline)
            remaining(oracle_deadline)
        stdout_raw = raw_file(stdout, 128 * 1024)
        stderr_raw = raw_file(stderr, 128 * 1024)
        terminal = {
            "returncode": code,
            "reaped": proc.returncode is not None,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "stdout_sha256": sha(stdout_raw),
            "stderr_sha256": sha(stderr_raw),
        }
        b.exclusive(attempt / ("oracle-" + str(int(cost)) + "-terminal.json"), terminal)
        refs.extend([store.put_bytes(stdout_raw), store.put_bytes(stderr_raw)])
        b.need(code == 0 and not stderr_raw, "invalid_result")
        verdict = strict(stdout_raw)
        b.need(
            verdict
            == {
                "status": "passed",
                "portfolios": 2,
                "fields_compared": 10 * count + 14,
                "relative_absolute_tolerance": "1e-28",
                "evidence": "software_accounting_only",
            },
            "invalid_result",
        )
        receipt = {
            **verdict,
            "oracle_submission_id": sid,
            "child_submission_id": child["submission_id"],
            "payload_sha256": payload_ref,
            "result_sha256": child["details"]["artifact_sha256"],
            "oracle_sha256": ORACLE_SHA,
            "terminal": terminal,
            "evaluation_sessions": count,
        }
        ref = store.put_json(receipt)
        refs.append(ref)
        store.finish(
            sid, "success", {"artifact_refs": list(dict.fromkeys(refs)), "verdict_sha256": ref}
        )
        return receipt
    except BaseException:
        owned, proc = proc, None
        if owned is not None:
            arm(oracle_cleanup)
            cleanup = reap_once(owned, oracle_cleanup)
            try:
                remaining(oracle_cleanup)
                b.exclusive(attempt / ("oracle-" + str(int(cost)) + "-cleanup.json"), cleanup)
            except BaseException:
                pass
        try:
            remaining(cleanup_deadline)
            store.finish(
                sid,
                "failed",
                {"error_code": "fresh_oracle_failed", "artifact_refs": list(dict.fromkeys(refs))},
            )
        except Exception:
            pass
        raise


def safe_result(
    status, fixture, context=None, cases=None, trace=None, *, broker_flags_checked=False
):
    context = context or {}
    cases = cases or []
    trace = trace or {}
    roles = context.get("roles", [])
    reviews = [
        r
        for r in roles
        if r.get("role") in {"data_critic", "statistical_critic", "quality", "scope"}
        and r.get("inspection_state") == "inspected"
    ]
    complete = status == "verified_full_trace_and_numerics" and not fixture
    return {
        "schema_version": 1,
        "kind": "d008_fresh_cycle_audit",
        "status": status,
        "evidence_kind": "synthetic_fixture" if fixture else "historical_market_data",
        "published_stages_checked": context.get("published_stage_count", 0),
        "actual_model_observations_checked": 0
        if fixture
        else context.get("observed_actual_response_count", 0),
        "published_reviews_checked": len(reviews),
        "review_outcome": context.get("review_outcome", "not_reached"),
        "published_inconclusive_reviews": sum(r.get("decision") == "inconclusive" for r in reviews),
        "published_blocking_reviews": sum(r.get("decision") == "block" for r in reviews),
        "oracle_cases_passed": len(cases),
        "oracle_fields_compared": sum(c["fields_compared"] for c in cases),
        "fresh_children_checked": trace.get("fresh_children_checked", 0),
        "derivative_operands_checked": trace.get("derivative_operands_checked", 0),
        "bounded_operational_evidence_complete": complete,
        "broker_flags_preserved": broker_flags_checked,
        **FLAGS,
    }


def child(job_path):
    global _WINDOW
    job = strict(raw_file(job_path))
    b, manifest = load_boundary(Path(job["manifest_path"]), job["manifest_sha256"])
    b.environment_check()
    packet = job["packet"]
    fixture = job["fixture"]
    deadline = job["deadline"]
    cleanup_deadline = job["cleanup_deadline"]
    _WINDOW = (job["start_monotonic"], job["start_wall"])
    remaining(deadline)
    root, source = validate_packet(packet, fixture, b)
    attempt = job_path.parent
    b.need(
        attempt == root / "runtime" / ("fresh-cycle-audit-" + packet["attempt_id"]),
        "invalid_packet",
    )
    intent_raw = b.readfile(attempt / "intent.json")
    intent = b.parse(intent_raw)
    b.need(
        sha(intent_raw) == job["intent_sha256"]
        and intent["packet"] == packet
        and intent["deadline"] == deadline
        and intent["fixture"] == fixture
        and (intent["start_monotonic"], intent["start_wall"]) == _WINDOW
        and intent["cleanup_deadline"] == cleanup_deadline
        and 0 < cleanup_deadline - deadline <= 5,
        "invalid_packet",
    )
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("deadline")))
    arm(deadline)
    evidence = evidence_module(manifest)
    chain = evidence.launch_chain(
        root,
        source,
        packet,
        Path(job["manifest_path"]),
        job["manifest_sha256"],
        raw_file,
        strict,
        fixture,
    )
    b.need(b.project_state(root, deadline) == packet["expected_state"], "store_changed")
    loader = b.load_product(source, manifest["files"])
    trace_mod = import_checked(
        "fresh_cycle_trace", HERE / "trace_checks.py", manifest["tools"]["trace_checks.py"]
    )
    context_mod = import_checked(
        "fresh_cycle_context", HERE / "context_checks.py", manifest["tools"]["context_checks.py"]
    )
    b.need(
        b.loaded_identity() == manifest["loaded"]
        and loader.loaded == manifest["compiled"]
        and b.standard_library_identity() == manifest["stdlib"],
        "loaded_mismatch",
    )
    from quanto import evaluation_registry as reg, provenance, ledger

    control, research = (
        root / "runtime/access-control/control.sqlite",
        root / "runtime/research.sqlite",
    )
    before = packet["expected_state"]
    reg.os = b.ExistingOS(os, control, before["control"]["physical"])
    reg.sqlite3 = b.ExistingSQLite(sqlite3, control, before["control"]["physical"])
    provenance.os = b.ExistingOS(os, research, before["research"]["physical"], basename=True)
    ledger.sqlite3 = b.ExistingSQLite(sqlite3, research, before["research"]["physical"])
    monitor = b.Boundary(
        source,
        root,
        attempt,
        [Path(packet[k]["path"]) for k in ("request_file", "outcome_file")]
        + [job_path, Path(job["manifest_path"])]
        + [Path(name) for name in chain["identities"]],
    )
    sys.addaudithook(monitor)
    sys.setprofile(no_network_profile)
    supervisor = reg.Supervisor(root, synthetic=fixture)
    context = local = None
    completed_context = None
    accounting = []
    trusted_partial = False
    broker_flags_checked = False
    cases = []
    verification_id = None
    refs = []
    status = "refused"
    budget_before = None
    with supervisor.session() as session:
        session.check(root)
        b.need(session.synthetic is fixture and session.root == root, "authority_changed")
        with provenance.Provenance(root) as store:
            db = store.journal.connection
            db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
            count, bytes_ = db.execute(
                "SELECT COUNT(*),COALESCE(SUM(length(payload)),0) FROM events"
            ).fetchone()
            b.need(count <= 100000 and bytes_ <= 64 * 1024 * 1024, "invalid_result")
            initial = store.journal.verify_events()
            budget_before = budget_snapshot(db, b)
            verification_id = store.begin(
                "d008_fresh_cycle_audit",
                {
                    "packet_sha256": intent["packet_sha256"],
                    "manifest_sha256": job["manifest_sha256"],
                    "intent_sha256": job["intent_sha256"],
                    "evidence_kind": "synthetic_fixture" if fixture else "historical_market_data",
                },
            )
            try:
                values = {}
                for key in ("request_file", "outcome_file"):
                    raw = b.readfile(Path(packet[key]["path"]))
                    b.need(sha(raw) == packet[key]["sha256"], "request_mismatch")
                    values[key] = raw
                    refs.append(store.put_bytes(raw))
                saved = strict(values["outcome_file"])
                b.need(
                    chain["outcome"] == values["outcome_file"]
                    and chain["request"] == values["request_file"],
                    "request_mismatch",
                )
                outcome_state = evidence.exact_outcome(store, saved)
                broker_flags_checked = outcome_state != "pending"
                if outcome_state == "pending":
                    raise evidence.Incomplete("broker_pending")
                evidence.check_registration(store, chain)
                codes, run = extra_trace(
                    store, saved, values["request_file"], fixture, packet["prelaunch"], b
                )
                b.need(
                    saved["status"] in {"success", "invalid", "pending", "failed", "interrupted"},
                    "invalid_result",
                )
                if run is None:
                    raise evidence.Incomplete("before_workflow_registration")
                from quanto.research_broker import code_identity

                b.need(chain["broker_code"] == code_identity(), "source_mismatch")
                accounting = evidence.accounting(
                    store, chain, run["workflow_run_id"], fixture, strict
                )
                context = context_mod.inspect(store, values["outcome_file"], values["request_file"])
                complete = context.get("published_stage_count") == 7
                # A partial/uncertain trace is retained as incomplete. It cannot acquire a numerical pass here.
                b.need(context.get("observed_trace_consistent") is True, "lineage_mismatch")
                completed_context = context
                trusted_partial = not complete
                if complete:
                    if not fixture:
                        b.need(context["all_checks_passed"] is True, "lineage_mismatch")
                    local, children = trace_mod.trace_workflow(
                        store, saved, codes, fixture_only=fixture
                    )
                    b.need(
                        len(children) == 3 and len({c["submission_id"] for c in children}) == 3,
                        "lineage_mismatch",
                    )
                    for child_record in children:
                        cases.append(
                            oracle_case(
                                store,
                                child_record,
                                attempt,
                                verification_id,
                                b,
                                deadline,
                                cleanup_deadline,
                            )
                        )
                    status = "verified_fixture" if fixture else "verified_full_trace_and_numerics"
                else:
                    status = "incomplete"
                b.need(budget_snapshot(db, b) == budget_before, "store_changed")
                b.need(
                    b.source_files(source) == manifest["files"]
                    and loader.loaded == manifest["compiled"],
                    "source_mismatch",
                )
                from quanto.explorer import _code_identity

                b.need(_code_identity() == codes["financial_identity"], "loaded_mismatch")
                private = {
                    "status": status,
                    "context": context,
                    "trace": local,
                    "oracle_cases": cases,
                    "initial_journal": initial,
                    "budget_state_unchanged": True,
                    "cycle_receipts": chain["identities"],
                    "request_accounting": accounting,
                    "planning_budget_evidence": chain.get("planning_budget_evidence"),
                    "prelaunch": packet["prelaunch"],
                    "request_sha256": packet["request_file"]["sha256"],
                    "outcome_sha256": packet["outcome_file"]["sha256"],
                    "manifest_sha256": job["manifest_sha256"],
                    "verification_submission_id": verification_id,
                    "automatic_retry": False,
                    **FLAGS,
                }
                report_ref = store.put_json(private)
                refs.append(report_ref)
                store.finish(
                    verification_id,
                    "success",
                    {"status": status, "audit_report_sha256": report_ref, "artifact_refs": refs},
                )
                b.exclusive(
                    attempt / "private-audit-report.json", {**private, "report_sha256": report_ref}
                )
            except BaseException as exc:
                status = (
                    "incomplete"
                    if isinstance(exc, evidence.Incomplete) or trusted_partial
                    else "refused"
                )
                if isinstance(exc, (TimeoutError, KeyboardInterrupt)):
                    raise
                if budget_before is not None:
                    b.need(budget_snapshot(db, b) == budget_before, "store_changed")
                try:
                    store.finish(
                        verification_id,
                        "failed",
                        {
                            "error_code": "fresh_cycle_audit_refused_or_incomplete",
                            "artifact_refs": refs,
                        },
                    )
                except Exception:
                    pass
                b.exclusive(
                    attempt / "audit-failure.json",
                    {
                        "status": status,
                        "context": context,
                        "oracle_cases": cases,
                        "verification_submission_id": verification_id,
                        "planning_budget_evidence": chain.get("planning_budget_evidence"),
                        "incomplete_reason": str(exc) if type(exc) is evidence.Incomplete else None,
                        "automatic_retry": False,
                        **FLAGS,
                    },
                )
    after = b.preserve_authority(root, before, deadline)
    b.need(
        b.loaded_identity() == manifest["loaded"] and b.source_files(source) == manifest["files"],
        "loaded_mismatch",
    )
    remaining(deadline)
    result = safe_result(
        status, fixture, completed_context, cases, local, broker_flags_checked=broker_flags_checked
    )
    b.exclusive(attempt / "authority-after.json", after)
    b.exclusive(attempt / "result.json", result)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if status in {"verified_full_trace_and_numerics", "verified_fixture"} else 2


def saved_status(raw):
    try:
        return strict(raw)["status"]
    except Exception:
        return None


def run(packet_path, packet_sha, manifest_path, manifest_sha, fixture=False, seconds=SECONDS):
    global _WINDOW
    started = time.monotonic()
    started_wall = time.time()
    previous_window = _WINDOW
    if type(seconds) not in (int, float) or not 0 < seconds <= SECONDS:
        raise ValueError("deadline")
    cleanup_deadline = started + seconds
    deadline = cleanup_deadline - min(5, seconds / 4)
    _WINDOW = (started, started_wall)
    handlers = {
        sig: signal.getsignal(sig) for sig in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM)
    }

    def interrupted(*args):
        raise TimeoutError("audit_interrupted")

    try:
        for sig in handlers:
            signal.signal(sig, interrupted)
        arm(deadline)
        return _run(
            packet_path,
            packet_sha,
            manifest_path,
            manifest_sha,
            fixture,
            seconds,
            started,
            deadline,
            cleanup_deadline,
        )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        _WINDOW = previous_window
        for sig, handler in handlers.items():
            signal.signal(sig, handler)


def _run(
    packet_path,
    packet_sha,
    manifest_path,
    manifest_sha,
    fixture,
    seconds,
    started,
    deadline,
    cleanup_deadline,
):
    b, manifest = load_boundary(manifest_path, manifest_sha)
    b.environment_check()
    packet_raw = b.readfile(packet_path)
    b.need(sha(packet_raw) == packet_sha, "invalid_packet")
    packet = strict(packet_raw)
    root, source = validate_packet(packet, fixture, b)
    b.need(fixture or seconds == SECONDS, "invalid_packet")
    attempt = root / "runtime" / ("fresh-cycle-audit-" + packet["attempt_id"])
    evidence = evidence_module(manifest)
    evidence.bind_plan(root, source, packet, manifest_path, manifest_sha, raw_file, strict, fixture)
    remaining(deadline)
    attempt.mkdir(mode=0o700)
    childproc = None
    spawning = False
    try:
        intent = {
            "packet": packet,
            "packet_sha256": packet_sha,
            "manifest_sha256": manifest_sha,
            "fixture": fixture,
            "deadline": deadline,
            "seconds": seconds,
            "cleanup_deadline": cleanup_deadline,
            "start_monotonic": _WINDOW[0],
            "start_wall": _WINDOW[1],
            "automatic_retry": False,
            **FLAGS,
        }
        intent_sha = b.exclusive(attempt / "intent.json", intent)
        try:
            chain = evidence.launch_chain(
                root, source, packet, manifest_path, manifest_sha, raw_file, strict, fixture
            )
        except evidence.Incomplete:
            result = safe_result("incomplete", fixture)
            b.exclusive(
                attempt / "incomplete-authority.json",
                {
                    "status": "missing_or_uncertain_cycle_receipt",
                    "intent_sha256": intent_sha,
                    "automatic_retry": False,
                },
            )
            b.exclusive(attempt / "result.json", result)
            remaining(deadline)
            print(json.dumps(result, sort_keys=True), flush=True)
            return 2
        job = {
            "packet": packet,
            "fixture": fixture,
            "manifest_path": str(manifest_path),
            "manifest_sha256": manifest_sha,
            "intent_sha256": intent_sha,
            "deadline": deadline,
            "cleanup_deadline": cleanup_deadline,
            "start_monotonic": _WINDOW[0],
            "start_wall": _WINDOW[1],
        }
        job_path = attempt / "job.json"
        b.exclusive(job_path, job)
        stdout, stderr = attempt / "child.stdout", attempt / "child.stderr"
        with stdout.open("xb") as out, stderr.open("xb") as err:
            remaining(deadline)
            spawning = True
            childproc = subprocess.Popen(
                [
                    str(PYTHON),
                    "-I",
                    "-S",
                    "-B",
                    str(Path(__file__).absolute()),
                    "--child",
                    str(job_path),
                ],
                cwd=str(HERE),
                env={},
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=err,
                close_fds=True,
                start_new_session=True,
            )
            spawning = False
            code = wait_terminal(childproc, deadline)
            remaining(deadline)
            pid = childproc.pid
            reaped = childproc.returncode is not None
            childproc = None
        out_raw = b.readfile(stdout, limit=128 * 1024)
        err_raw = b.readfile(stderr, limit=128 * 1024)
        process = {
            "returncode": code,
            "timed_out": False,
            "pid": pid,
            "owned_child_reaped": reaped,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "stdout_sha256": sha(out_raw),
            "stderr_sha256": sha(err_raw),
            "intent_sha256": intent_sha,
            "automatic_retry": False,
            **FLAGS,
        }
        b.exclusive(attempt / "process.json", process)
        b.need(reaped and not err_raw and code in {0, 2}, "child_failed")
        result = strict(out_raw)
        b.need(result == strict(b.readfile(attempt / "result.json")), "invalid_result")
        b.need(result == safe_result_from_shape(result, fixture), "invalid_result")
        validate_private_terminals(attempt, result, b)
        b.need(all(result[k] is False for k in FLAGS), "invalid_result")
        b.need(
            (code == 0)
            == (result["status"] in {"verified_full_trace_and_numerics", "verified_fixture"}),
            "invalid_result",
        )
        load_boundary(manifest_path, manifest_sha)
        final_chain = evidence.launch_chain(
            root, source, packet, manifest_path, manifest_sha, raw_file, strict, fixture
        )
        b.need(chain["identities"] == final_chain["identities"], "receipt_collision")
        remaining(deadline)
        b.exclusive(
            attempt / "accepted-terminal.json",
            {
                "result_sha256": sha(out_raw),
                "result_file_sha256": sha(b.readfile(attempt / "result.json")),
                "process_sha256": sha(b.readfile(attempt / "process.json")),
                "clean_terminal_observed": True,
                "status": result["status"],
                **FLAGS,
            },
        )
        remaining(deadline)
        print(json.dumps(result, sort_keys=True), flush=True)
        remaining(deadline)
        return code
    except BaseException:
        owned, childproc = childproc, None
        cleanup = {"status": "launch_ownership_unknown" if spawning else "no_outstanding_child"}
        try:
            arm(cleanup_deadline)
            if owned is not None:
                cleanup = reap_once(owned, cleanup_deadline, group=True)
        except BaseException:
            cleanup = {"status": "cleanup_unobserved"}
        try:
            remaining(cleanup_deadline)
            b.exclusive(
                attempt / "launcher-failure.json",
                {
                    "status": "refused_or_uncertain",
                    "cleanup": cleanup,
                    "automatic_retry": False,
                    **FLAGS,
                },
            )
        except Exception:
            pass
        try:
            remaining(cleanup_deadline)
            print(
                json.dumps(
                    {"status": "refused_or_uncertain", "automatic_retry": False, **FLAGS},
                    sort_keys=True,
                ),
                flush=True,
            )
        except TimeoutError:
            pass
        return 1


def validate_private_terminals(attempt, result, b):
    count_expected = result["oracle_cases_passed"]
    if count_expected == 0:
        b.need(result["oracle_fields_compared"] == 0, "invalid_result")
        return
    failed = (attempt / "audit-failure.json").exists()
    if result["status"] in {"verified_fixture", "verified_full_trace_and_numerics"}:
        b.need(not failed, "invalid_result")
    report = strict(
        b.readfile(attempt / ("audit-failure.json" if failed else "private-audit-report.json"))
    )
    b.need(
        report["status"] == result["status"] and len(report["oracle_cases"]) == count_expected,
        "invalid_result",
    )
    if not failed:
        report_sha = report.pop("report_sha256")
        b.need(sha(b.canonical(report)) == report_sha, "invalid_result")
    b.need(
        len({c["child_submission_id"] for c in report["oracle_cases"]}) == count_expected
        and len({c["oracle_submission_id"] for c in report["oracle_cases"]}) == count_expected,
        "invalid_result",
    )
    count = 0
    for cost, case in zip((0, 10, 25), report["oracle_cases"]):
        terminal = strict(b.readfile(attempt / f"oracle-{cost}-terminal.json"))
        out = b.readfile(attempt / f"oracle-{cost}.stdout")
        err = b.readfile(attempt / f"oracle-{cost}.stderr")
        verdict = strict(out)
        payload = b.readfile(attempt / f"oracle-input-{cost}.json", limit=16 * 1024 * 1024)
        b.need(
            terminal == case["terminal"]
            and type(terminal["returncode"]) is int
            and terminal["returncode"] == 0
            and terminal["reaped"] is True
            and terminal["stdout_sha256"] == sha(out)
            and terminal["stderr_sha256"] == sha(err)
            and not err
            and sha(payload) == case["payload_sha256"],
            "invalid_result",
        )
        b.need(
            verdict["status"] == "passed"
            and case["fields_compared"]
            == verdict["fields_compared"]
            == 10 * case["evaluation_sessions"] + 14
            and case["oracle_sha256"] == ORACLE_SHA,
            "invalid_result",
        )
        count += case["fields_compared"]
    b.need(count == result["oracle_fields_compared"], "invalid_result")


def safe_result_from_shape(value, fixture):
    template = safe_result("refused", False)
    if type(value) is not dict or set(value) != set(template):
        raise ValueError("projection")
    if (
        value["schema_version"] != 1
        or value["kind"] != template["kind"]
        or value["status"]
        not in {"refused", "incomplete", "verified_fixture", "verified_full_trace_and_numerics"}
    ):
        raise ValueError("projection")
    if value["evidence_kind"] not in {"synthetic_fixture", "historical_market_data"} or value[
        "review_outcome"
    ] not in {"not_reached", "incomplete", "blocked", "inconclusive", "method_no_blockers"}:
        raise ValueError("projection")
    for key in ("published_stages_checked", "actual_model_observations_checked"):
        if type(value[key]) is not int or not 0 <= value[key] <= 7:
            raise ValueError("projection")
    for key in (
        "published_reviews_checked",
        "published_inconclusive_reviews",
        "published_blocking_reviews",
    ):
        if type(value[key]) is not int or not 0 <= value[key] <= 4:
            raise ValueError("projection")
    for key, limit in (
        ("oracle_cases_passed", 3),
        ("fresh_children_checked", 3),
        ("derivative_operands_checked", 9),
        ("oracle_fields_compared", 600042),
    ):
        if type(value[key]) is not int or not 0 <= value[key] <= limit:
            raise ValueError("projection")
    for key in (*FLAGS, "bounded_operational_evidence_complete", "broker_flags_preserved"):
        if type(value[key]) is not bool:
            raise ValueError("projection")
    if value["evidence_kind"] != ("synthetic_fixture" if fixture else "historical_market_data"):
        raise ValueError("mode")
    reviews = value["published_reviews_checked"]
    blocked = value["published_blocking_reviews"]
    uncertain = value["published_inconclusive_reviews"]
    if (
        blocked + uncertain > reviews
        or reviews > value["published_stages_checked"]
        or value["actual_model_observations_checked"] > 7
    ):
        raise ValueError("review_counts")
    expected = (
        "not_reached"
        if reviews == 0
        else "incomplete"
        if reviews < 4
        else "blocked"
        if blocked
        else "inconclusive"
        if uncertain
        else "method_no_blockers"
    )
    if expected != value["review_outcome"]:
        raise ValueError("review_outcome")
    if value["published_reviews_checked"] != max(0, value["published_stages_checked"] - 3):
        raise ValueError("published_prefix")
    if value["evidence_kind"] == "synthetic_fixture" and (
        value["actual_model_observations_checked"] or value["bounded_operational_evidence_complete"]
    ):
        raise ValueError("synthetic")
    if (
        not value["broker_flags_preserved"]
        and any(
            value[k]
            for k in (
                "published_stages_checked",
                "actual_model_observations_checked",
                "oracle_cases_passed",
                "fresh_children_checked",
                "bounded_operational_evidence_complete",
            )
        )
    ) or any(value[k] is not False for k in FLAGS):
        raise ValueError("flags")
    if value["published_stages_checked"] < 7 and any(
        value[k]
        for k in (
            "oracle_cases_passed",
            "oracle_fields_compared",
            "fresh_children_checked",
            "derivative_operands_checked",
        )
    ):
        raise ValueError("partial_financial_counts")
    if (
        bool(value["oracle_cases_passed"]) != bool(value["oracle_fields_compared"])
        or value["oracle_cases_passed"] > value["fresh_children_checked"]
    ):
        raise ValueError("oracle_counts")
    if (
        value["fresh_children_checked"] not in (0, 3)
        or value["derivative_operands_checked"] != 3 * value["fresh_children_checked"]
    ):
        raise ValueError("financial_counts")
    complete = value["status"] in {"verified_full_trace_and_numerics", "verified_fixture"}
    if complete and (
        value["published_stages_checked"] != 7
        or value["published_reviews_checked"] != 4
        or value["oracle_cases_passed"] != 3
        or value["fresh_children_checked"] != 3
        or value["derivative_operands_checked"] != 9
        or value["oracle_fields_compared"] < 42
        or value["review_outcome"] not in {"blocked", "inconclusive", "method_no_blockers"}
    ):
        raise ValueError("complete_counts")
    actual = value["status"] == "verified_full_trace_and_numerics"
    if value["bounded_operational_evidence_complete"] is not actual:
        raise ValueError("complete_flag")
    if actual and (
        value["evidence_kind"] != "historical_market_data"
        or value["actual_model_observations_checked"] != 7
    ):
        raise ValueError("actual")
    if value["status"] == "verified_fixture" and value["evidence_kind"] != "synthetic_fixture":
        raise ValueError("fixture")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", type=Path)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--packet-sha")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--manifest-sha")
    parser.add_argument("--fixture", action="store_true")
    args = parser.parse_args()
    try:
        os.umask(0o077)
        if args.child:
            return child(args.child)
        if None in (args.packet, args.packet_sha, args.manifest, args.manifest_sha):
            raise ValueError("arguments")
        return run(args.packet, args.packet_sha, args.manifest, args.manifest_sha, args.fixture)
    except BaseException:
        print(
            json.dumps(
                {"status": "refused_or_uncertain", "automatic_retry": False, **FLAGS},
                sort_keys=True,
            ),
            flush=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Join a trusted supervisor's prospective receipts to one journal and one complete broker return."""

from datetime import date, datetime
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from zoneinfo import ZoneInfo

PHASES = ("revision", "admission", "suite")
KINDS = ("policy_revision", "historical_admission", "study_suite_registration")
REFS = ("policy_revision_sha256", "admission_sha256", "suite_sha256")
LA = ZoneInfo("America/Los_Angeles")
SHA = re.compile("[a-f0-9]{64}")
ID = re.compile("[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,63}")


class Invalid(ValueError):
    """Only fixed reasons; never submitted text."""


class Incomplete(Invalid):
    """A required clean terminal observation does not exist."""


def need(condition, reason="receipt_mismatch"):
    if not condition:
        raise Invalid(reason)


def digest(raw):
    return sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()


def same(left, right):
    return canonical(left) == canonical(right)


def is_sha(value):
    return type(value) is str and SHA.fullmatch(value) is not None


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def one(db, sql, params=()):
    rows = db.execute(sql, params).fetchall()
    need(len(rows) == 1, "row_missing_or_ambiguous")
    return rows[0]


def stamp(value):
    parsed = datetime.fromisoformat(value)
    need(parsed.tzinfo is not None, "timestamp_refused")
    return parsed


class Receipts:
    def __init__(self, read, parse):
        self.read, self.parse = read, parse
        self.identities = {}

    def bytes(self, path, expected=None, private=True):
        try:
            raw = self.read(path, 16 * 1024 * 1024, private)
        except FileNotFoundError:
            raise Incomplete("receipt_missing") from None
        sha = digest(raw)
        if expected is not None:
            need(is_sha(expected) and sha == expected, "receipt_digest")
        self.identities[str(path)] = sha
        return raw

    def json(self, path, expected=None, private=True):
        return self.parse(self.bytes(path, expected, private))


def bind_plan(root, source, packet, manifest_path, manifest_sha, read, parse, fixture):
    receipts = Receipts(read, parse)
    inputs = root / "runtime/manual-cycle-inputs"
    state = root / "runtime/manual-development-cycle"
    plan = receipts.json(inputs / "plan.json", packet["plan_sha256"])
    need(
        set(plan)
        == {
            "schema",
            "run_key",
            "registry_packet_sha256",
            "template_sha256",
            "supervisor_sha256",
            "worker_sha256",
            "audit_manifest",
            "reviews",
            "audit_attempt_id",
        }
        and type(plan["schema"]) is int
        and plan["schema"] == 1
    )
    need(
        plan["audit_attempt_id"] == packet["attempt_id"]
        and type(plan["run_key"]) is str
        and ID.fullmatch(plan["run_key"])
    )
    need(
        plan["audit_manifest"] == {"name": manifest_path.name, "sha256": manifest_sha}
        and manifest_path.parent == Path(__file__).parent
    )
    need(
        Path(packet["request_file"]["path"]) == state / "request.json"
        and Path(packet["outcome_file"]["path"]) == state / "outcome.json"
    )
    for name, key in [("supervise.py", "supervisor_sha256"), ("paid_worker.py", "worker_sha256")]:
        receipts.bytes(
            (
                root / "fixture-launch-sources"
                if fixture
                else source / "runtime/development-cycle-launch-v2-preparation"
            )
            / name,
            plan[key],
            False,
        )
    manifest = receipts.json(manifest_path, manifest_sha)
    need(
        manifest["launch_sources"]
        == {
            name: plan[key]
            for name, key in [
                ("supervise.py", "supervisor_sha256"),
                ("paid_worker.py", "worker_sha256"),
            ]
        },
        "launch_source_version",
    )
    reviews = {
        f"{stage}_{role}": f"D008-{prefix}-{role}.md"
        for stage, prefix in (
            ("registration", "current-code-registration-v2"),
            ("auditor", "next-cycle-audit-v2"),
            ("supervisor", "manual-cycle-launch-v2"),
        )
        for role in ("critic", "quality", "scope")
    }
    need(set(plan["reviews"]) == set(reviews), "review_roster")
    for key, name in reviews.items():
        receipts.bytes(root / "docs/reviews" / name, plan["reviews"][key], False)
    return receipts, plan


def phase_terminal(receipts, state, phase, consumed, consumed_sha, launch_sha):
    prefix = "registration-" if phase == "registration" else ""
    log = "registration" if prefix else "worker"
    owned = receipts.json(state / (prefix + "owned.json"))
    owned_sha = receipts.identities[str(state / (prefix + "owned.json"))]
    pid = owned["pid"]
    parent = consumed["parent_pid"]
    need(
        integer(pid, 1)
        and pid != parent
        and same(
            owned,
            {
                "pid": pid,
                "parent_pid": parent,
                "phase": phase,
                "consumed_sha256": consumed_sha,
                phase + "_launch_sha256": launch_sha,
            },
        ),
        "owned_phase",
    )
    start = receipts.json(state / (prefix + "start.json"))
    start_sha = receipts.identities[str(state / (prefix + "start.json"))]
    need(
        same(
            start,
            {
                "phase": phase,
                "parent_pid": parent,
                "pid": pid,
                "consumed_sha256": consumed_sha,
                "launch_sha256": launch_sha,
                "owned_sha256": owned_sha,
            },
        ),
        "start_grant",
    )
    terminal = receipts.json(state / (prefix + "exit.json"))
    exit_sha = receipts.identities[str(state / (prefix + "exit.json"))]
    if (
        type(terminal["returncode"]) is not int
        or terminal["returncode"] != 0
        or terminal["owned_child_reaped"] is not True
    ):
        raise Incomplete("phase_exit_uncertain")
    need(
        terminal["pid"] == pid
        and terminal["owned_sha256"] == owned_sha
        and terminal["start_sha256"] == start_sha
        and terminal[phase + "_launch_sha256"] == launch_sha,
        "exit_ownership",
    )
    stdout = receipts.bytes(state / (log + ".stdout"), terminal["stdout_sha256"])
    stderr = receipts.bytes(state / (log + ".stderr"), terminal["stderr_sha256"])
    need(
        stdout
        == (
            b'{"status":"registration_returned"}\n' if prefix else b'{"status":"broker_returned"}\n'
        )
        and not stderr,
        "phase_terminal_streams",
    )
    return terminal, exit_sha, owned_sha, start_sha


def launch_chain(root, source, packet, manifest_path, manifest_sha, read, parse, fixture):
    receipts, plan = bind_plan(
        root, source, packet, manifest_path, manifest_sha, read, parse, fixture
    )
    state = root / "runtime/manual-development-cycle"
    inputs = root / "runtime/manual-cycle-inputs"
    for name in (
        "failure.json",
        "worker-failure.json",
        "paid-failure.json",
        "paid-uncertainty.json",
        "registration-uncertainty.json",
    ):
        if (state / name).exists() or (state / name).is_symlink():
            raise Incomplete("cycle_failure_receipt")
    registration = receipts.json(inputs / "registration.json", plan["registry_packet_sha256"])
    template = receipts.json(inputs / "template.json", plan["template_sha256"])
    regsrc = source / "runtime/development-cycle-registration-v2-preparation"
    for key, filename, pin in [
        (
            "controller_sha256",
            "prepare_current_code.py",
            "3f52a95452d9a20c6c456624f33a70c717d9f1fc28d83ae65f178e67e9d7047d",
        ),
        (
            "tests_sha256",
            "test_registration_preparation.py",
            "b717f8603b65570feb4b84c23e4301a1f26f54784a11ebd8ad4bac19423d1d79",
        ),
        (
            "manifest_sha256",
            "source-manifest.json",
            "aa65675f3c7886a2d950b75928811d4f7189adbc2342a383b983f0ea20ea70c4",
        ),
    ]:
        need(registration[key] == pin, "registration_source")
        receipts.bytes(regsrc / filename, pin, False)
    need(registration["preparation_critic_sha256"] == plan["reviews"]["registration_critic"])
    receipts.bytes(inputs / "preflight.json", registration["preflight_evidence_sha256"])
    need(type(registration["attempt_id"]) is str and ID.fullmatch(registration["attempt_id"]))
    regdir = root / "runtime/current-code-registration" / registration["attempt_id"]
    need(not (regdir / "failure.json").exists())
    consumed = receipts.json(state / "consumed.json")
    consumed_sha = receipts.identities[str(state / "consumed.json")]
    need(
        consumed["plan_sha256"] == packet["plan_sha256"]
        and consumed["supervisor_sha256"] == plan["supervisor_sha256"]
        and consumed["automatic_retry"] is False
        and integer(consumed["parent_pid"], 1)
        and consumed["limit_seconds"] == 7200
    )
    launch = receipts.json(state / "paid-launch.json")
    launch_sha = receipts.identities[str(state / "paid-launch.json")]
    request = receipts.bytes(state / "request.json", packet["request_file"]["sha256"])
    config = parse(request)
    request_sha = digest(request)
    need(
        launch["consumed_sha256"] == consumed_sha
        and launch["plan_sha256"] == packet["plan_sha256"]
        and launch["parent_pid"] == consumed["parent_pid"]
        and launch["request_sha256"] == request_sha
    )
    reglaunch = receipts.json(state / "registration-launch.json")
    reglaunchsha = receipts.identities[str(state / "registration-launch.json")]
    need(
        reglaunch
        == {
            "plan_sha256": packet["plan_sha256"],
            "parent_pid": consumed["parent_pid"],
            "consumed_sha256": consumed_sha,
            "packet_sha256": plan["registry_packet_sha256"],
            "attempt_id": registration["attempt_id"],
        },
        "registration_launch",
    )
    _, regexp, _, _ = phase_terminal(
        receipts, state, "registration", consumed, consumed_sha, reglaunchsha
    )
    need(launch["registration_exit_sha256"] == regexp, "registration_exit_binding")
    returned = receipts.json(state / "registration-returned.json")
    need(
        returned
        == {
            "status": "registration_returned",
            "result_sha256": launch["registration_result_sha256"],
            "registration_launch_sha256": reglaunchsha,
        },
        "registration_return",
    )
    result = receipts.json(regdir / "result.json", launch["registration_result_sha256"])
    need(
        result["status"] == "completed"
        and result["packet_sha256"] == plan["registry_packet_sha256"]
        and result["automatic_retry"] is False
        and result["paid_launch_authorized"] is False
    )
    regintent = receipts.json(regdir / "intent.json", result["intent_sha256"])
    need(
        regintent["packet_sha256"] == result["packet_sha256"]
        and same(regintent["packet"], registration)
    )
    regconsumed = receipts.json(regdir.parent / "consumed.json")
    need(
        regconsumed["attempt"] == registration["attempt_id"]
        and regconsumed["packet_sha256"] == result["packet_sha256"]
        and regconsumed["automatic_retry"] is False
    )
    need(
        [row["phase"] for row in result["phases"]] == list(PHASES)
        and set(result["mapping"]) == set(PHASES)
    )
    for idx, row in enumerate(result["phases"]):
        phase = PHASES[idx]
        mapping = result["mapping"][phase]
        old = registration["originals"][phase]
        record = receipts.json(regdir / (phase + "-result.json"), row["result_sha256"])
        end = receipts.json(regdir / (phase + "-exit.json"), row["exit_sha256"])
        need(
            record["status"] == "success"
            and record["phase"] == phase
            and record["intent_sha256"] == end["intent_sha256"] == result["intent_sha256"]
            and end["exitcode"] == 0
            and type(end["exitcode"]) is int
            and end["stderr_bytes"] == 0
        )
        need(
            same(record["mapping"], {k: result["mapping"][k] for k in PHASES[: idx + 1]})
            and mapping["old_submission_id"] == old["submission_id"]
            and mapping["old_artifact_sha256"] == old["artifact_sha256"]
            and mapping["submission_id"] != old["submission_id"]
            and is_sha(mapping["artifact_sha256"])
            and is_sha(mapping["request_sha256"])
        )
        if phase == "suite":
            need(same(record["after"], result["after"]))
    suite = result["mapping"]["suite"]["artifact_sha256"]
    need(
        template["run_key"] != plan["run_key"]
        and template["suite_sha256"] == registration["originals"]["suite"]["artifact_sha256"]
    )
    need(
        same(config, {**template, "run_key": plan["run_key"], "suite_sha256": suite})
        and request == canonical(config)
    )
    need(config["evidence_kind"] == ("synthetic_fixture" if fixture else "historical_market_data"))
    paid = receipts.json(state / "paid-consumed.json")
    paid_sha = receipts.identities[str(state / "paid-consumed.json")]
    need(
        paid["automatic_retry"] is False
        and paid["request_sha256"] == request_sha
        and paid["parent_pid"] == consumed["parent_pid"]
        and type(paid["deadline"]) in (int, float)
        and math.isfinite(paid["deadline"])
    )
    checkpoint = receipts.json(state / "prelaunch.json")
    cutsha = receipts.identities[str(state / "prelaunch.json")]
    budget = receipts.json(state / "prelaunch-budget.json")
    budgetsha = receipts.identities[str(state / "prelaunch-budget.json")]
    need(
        same(checkpoint, packet["prelaunch"])
        and checkpoint["request_sha256"] == request_sha
        and checkpoint["run_key"] == plan["run_key"]
        and checkpoint["suite_sha256"] == suite
        and checkpoint["failure_roster_sha256"] == digest(canonical(config["failure_ids"]))
    )
    entered = receipts.json(state / "paid-call-entered.json")
    bindings = {
        "paid_consumed_sha256": paid_sha,
        "consumed_sha256": consumed_sha,
        "paid_launch_sha256": launch_sha,
        "registration_result_sha256": launch["registration_result_sha256"],
        "request_sha256": request_sha,
        "prelaunch_sha256": cutsha,
        "prelaunch_budget_sha256": budgetsha,
    }
    _, _, paid_owned, paid_start = phase_terminal(
        receipts, state, "paid", consumed, consumed_sha, launch_sha
    )
    bindings.update(owned_sha256=paid_owned, start_sha256=paid_start)
    need(same(entered, bindings), "entered_ownership")
    before = receipts.json(state / "paid-before.json")
    after = receipts.json(state / "paid-after.json")
    need(
        same(before["state"], result["after"])
        and after.get("uncertain") is not True
        and same(after["state"], packet["expected_state"])
    )
    for key in ("compiled", "loaded_sha256", "broker_code"):
        need(same(before[key], after[key]))
    exitsha = receipts.identities[str(state / "exit.json")]
    raw = receipts.bytes(state / "outcome.json", packet["outcome_file"]["sha256"])
    terminal = receipts.json(state / "terminal.json")
    termsha = receipts.identities[str(state / "terminal.json")]
    need(
        terminal
        == {
            "status": "broker_returned",
            "outcome_sha256": digest(raw),
            "prelaunch_sha256": cutsha,
            "operational_acceptance": False,
            "investment_validation": False,
        }
    )
    final = receipts.json(state / "result.json")
    need(
        final["status"] == "broker_returned"
        and final["audit_required"] is True
        and final["operational_acceptance"] is False
        and final["investment_validation"] is False
    )
    for key, value in {
        "plan_sha256": packet["plan_sha256"],
        "terminal_sha256": termsha,
        "consumed_sha256": consumed_sha,
        "paid_launch_sha256": launch_sha,
        "registration_result_sha256": launch["registration_result_sha256"],
        "request_sha256": request_sha,
        "exit_sha256": exitsha,
        "outcome_sha256": digest(raw),
    }.items():
        need(final[key] == value)
    outer = receipts.json(state / "lead-outer.json")
    need(
        set(outer)
        == {
            "schema",
            "plan_sha256",
            "supervisor_result_sha256",
            "returncode",
            "stdout_sha256",
            "stdout_text",
            "outer_terminal_observed",
            "observed_at",
            "tool_chunk_id",
        }
        and type(outer["schema"]) is int
        and outer["schema"] == 1
    )
    if (
        outer["outer_terminal_observed"] is not True
        or type(outer["returncode"]) is not int
        or outer["returncode"] != 0
    ):
        raise Incomplete("outer_terminal_uncertain")
    need(
        outer["plan_sha256"] == packet["plan_sha256"]
        and outer["supervisor_result_sha256"] == receipts.identities[str(state / "result.json")]
        and type(outer["stdout_text"]) is str
        and len(outer["stdout_text"].encode()) <= 4096
        and digest(outer["stdout_text"].encode()) == outer["stdout_sha256"]
        and same(
            parse(outer["stdout_text"].encode()),
            {"status": "broker_returned", "audit_required": True, "automatic_retry": False},
        )
        and type(outer["tool_chunk_id"]) is str
        and 0 < len(outer["tool_chunk_id"]) <= 128,
        "outer_terminal_binding",
    )
    stamp(outer["observed_at"])
    synthetic_fingerprints = (
        receipts.json(state / "synthetic-response-digests.json") if fixture else {}
    )
    need(
        type(synthetic_fingerprints) is dict
        and len(synthetic_fingerprints) <= 7
        and all(
            type(k) is str and len(k) <= 200 and is_sha(v)
            for k, v in synthetic_fingerprints.items()
        ),
        "fixture_fingerprint_capture",
    )
    audited = receipts.json(manifest_path, manifest_sha)
    check_worker_reference(before, audited, plan)
    need(
        type(consumed["start_monotonic"]) in (int, float)
        and math.isfinite(consumed["start_monotonic"])
        and type(consumed["start_wall"]) in (int, float)
        and math.isfinite(consumed["start_wall"])
        and consumed["start_monotonic"]
        < paid["deadline"]
        <= consumed["start_monotonic"] + consumed["limit_seconds"],
        "worker_deadline",
    )
    return {
        "synthetic_fingerprints": synthetic_fingerprints,
        "identities": receipts.identities,
        "registration": result["mapping"],
        "budget": budget,
        "prelaunch": checkpoint,
        "configuration": config,
        "broker_code": before["broker_code"],
        "request": request,
        "outcome": raw,
    }


def check_worker_reference(observed, manifest, plan):
    """The worker uses the registration loader's identity function, including defaults."""
    worker = manifest["worker_reference"]
    need(
        set(worker)
        == {
            "schema_version",
            "worker_sha256",
            "registration_sha256",
            "registration_manifest_sha256",
            "compiled",
            "loaded_sha256",
            "broker_code_sha256",
            "worker_source_segment_sha256",
        }
        and type(worker["schema_version"]) is int
        and worker["schema_version"] == 1,
        "worker_reference_schema",
    )
    need(
        worker["worker_sha256"] == plan["worker_sha256"]
        and worker["registration_sha256"]
        == "3f52a95452d9a20c6c456624f33a70c717d9f1fc28d83ae65f178e67e9d7047d"
        and worker["registration_manifest_sha256"]
        == "aa65675f3c7886a2d950b75928811d4f7189adbc2342a383b983f0ea20ea70c4",
        "worker_reference_inputs",
    )
    expected = worker["compiled"]
    need(
        type(expected) is dict
        and len(expected) == 21
        and all(is_sha(value) for value in expected.values())
        and all(
            is_sha(worker[key])
            for key in ("loaded_sha256", "broker_code_sha256", "worker_source_segment_sha256")
        ),
        "worker_reference_identity",
    )
    need(
        same(observed["compiled"], expected)
        and observed["loaded_sha256"] == worker["loaded_sha256"]
        and digest(canonical(observed["broker_code"])) == worker["broker_code_sha256"],
        "worker_runtime_identity",
    )


def exact_outcome(store, saved):
    need(type(saved) is dict and type(saved.get("submission_id")) is str, "outcome_shape")
    parent = store.get_submission(saved["submission_id"])
    need(parent["kind"] == "research_broker_run", "outcome_parent")
    if saved.get("status") == "pending":
        need(
            parent["status"] == "pending"
            and same(
                saved,
                {
                    "submission_id": parent["submission_id"],
                    "status": "pending",
                    "error_code": "broker_publication_interrupted",
                },
            ),
            "pending_shape",
        )
        return "pending"
    need(
        saved.get("status") in {"invalid", "success"}
        and parent["status"] == saved["status"]
        and parent["details"]["artifact_refs"] == [saved.get("artifact_sha256")],
        "outcome_status",
    )
    record = store.read_json(saved["artifact_sha256"])
    need(
        same(
            saved,
            {
                **record,
                "submission_id": parent["submission_id"],
                "status": parent["status"],
                "artifact_sha256": saved["artifact_sha256"],
            },
        ),
        "complete_return_mismatch",
    )
    need(
        record.get("operational_acceptance") is False
        and ("investment_validation" not in record or record["investment_validation"] is False),
        "broker_flags",
    )
    return "completed" if saved["status"] == "success" else "invalid"


def check_registration(store, chain):
    for phase, kind, ref in zip(PHASES, KINDS, REFS):
        m = chain["registration"][phase]
        rec = store.get_submission(m["submission_id"])
        need(
            rec["kind"] == kind
            and rec["status"] == "success"
            and rec["request_sha256"] == m["request_sha256"]
            and rec["details"][ref] == m["artifact_sha256"],
            "registered_mapping",
        )


def calendar_day(value):
    """Require an actual calendar date in the ledger's canonical YYYY-MM-DD spelling."""
    need(type(value) is str, "allocation_calendar_day")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise Invalid("allocation_calendar_day") from None
    need(value == parsed.isoformat(), "allocation_calendar_day")
    return value


def spending_bounds(rows, cutoff, planning_day, exact_days, upper_days, purposes):
    """Bound research spend using row order and independently known event days.

    Ordinary allocations precede their journaled reserves but need not share a
    date. A row's uncorroborated date or purpose never excludes a material risk.
    The bounds refer to recorded local amounts under the cooperating-host model.
    """
    upper = None
    uppers = {}
    for row in reversed(rows):
        rid = row["rowid"]
        req = row["request_id"]
        known_upper = upper_days.get(req)
        if rid <= cutoff:
            known_upper = min(known_upper, planning_day) if known_upper else planning_day
        if known_upper is not None:
            upper = min(upper, known_upper) if upper else known_upper
        uppers[rid] = upper
    lower = None
    minimum = maximum = ambiguous_rows = 0
    for row in rows:
        rid = row["rowid"]
        req = row["request_id"]
        exact = exact_days.get(req)
        known_lower = exact
        if rid > cutoff:
            known_lower = max(known_lower, planning_day) if known_lower else planning_day
        if known_lower is not None:
            lower = max(lower, known_lower) if lower else known_lower
        high = uppers[rid]
        recorded = row["day"]
        need(
            (lower is None or lower <= recorded) and (high is None or recorded <= high),
            "allocation_day_outside_event_bounds",
        )
        if rid > cutoff:
            continue
        purpose = purposes.get(req)
        possible_purpose = purpose is None or purpose == "research"
        possible_day = (lower is None or lower <= planning_day) and (
            high is None or planning_day <= high
        )
        if not possible_purpose or not possible_day:
            continue
        maximum += row["amount"]
        if purpose == "research" and (exact == planning_day or lower == high == planning_day):
            minimum += row["amount"]
        else:
            ambiguous_rows += 1
    return {
        "planning_day": planning_day,
        "allocation_prefix_max_rowid": cutoff,
        "minimum_research_micro_usd": minimum,
        "maximum_research_micro_usd": maximum,
        "ambiguous_relevant_rows": ambiguous_rows,
        "basis": "journal_constraints_append_order_and_recorded_local_amounts",
    }


def verify_allocation_prefix(db, events, cut, maxrow, *, planning_day=None):
    """Establish the maximum committed allocation row at the journal cut.

    Research authorizations insert reserve, dispatch and purpose allocation in
    the same transaction. An ordinary provider allocation precedes its reserve,
    but can be committed separately. Its later event alone cannot date the row
    to the far side of a cut. Append order can bound otherwise undated rows.
    """
    rows = list(
        db.execute(
            "SELECT rowid,request_id,day,purpose,amount FROM provider_allocations ORDER BY rowid LIMIT 50001"
        )
    )
    need(
        len(rows) <= 50000
        and integer(maxrow)
        and all(integer(row["rowid"], 1) and integer(row["amount"], 1) for row in rows),
        "purpose_cut",
    )
    for row in rows:
        calendar_day(row["day"])
    if planning_day is not None:
        calendar_day(planning_day)
    exact_days = {}
    upper_days = {}
    purposes = {}
    by_request = {row["request_id"]: row for row in rows}
    reserves = {}
    dispatches = {}
    research = {}
    ordinary = {}
    categories = {
        "budget_reserved": reserves,
        "dispatch_authorized": dispatches,
        "workflow_research_dispatch_authorized": research,
        "provider_call_requested": ordinary,
    }
    for number, kind, payload, occurred in events:
        if kind in categories:
            req = payload["request_id"]
            need(req not in categories[kind], "allocation_event_ambiguous")
            categories[kind][req] = (number, payload, occurred)
    before = []
    after = []
    for req, (position, record, occurred) in research.items():
        if req not in by_request or req not in reserves or req not in dispatches:
            raise Incomplete("research_allocation_evidence_missing")
        row = by_request[req]
        r, rp, rt = reserves[req]
        d, dp, dt = dispatches[req]
        need(
            req not in ordinary
            and r < d < position
            and same(rp, {"request_id": req, "day": row["day"], "max_micro_usd": row["amount"]})
            and dp["day"] == row["day"]
            and dp["authorized_at"] == dt
            and stamp(rt).astimezone(LA).date().isoformat() == row["day"]
            and stamp(dt).astimezone(LA).date().isoformat() == row["day"]
            and record["reserved_micro_usd"] == row["amount"]
            and row["purpose"] == "research",
            "research_allocation_event_join",
        )
        need(
            (r <= cut) == (d <= cut) == (position <= cut),
            "cut_inside_atomic_research_authorization",
        )
        (before if position <= cut else after).append(row["rowid"])
        exact_days[req] = upper_days[req] = row["day"]
        purposes[req] = "research"
    for req, (position, record, occurred) in ordinary.items():
        if req not in by_request or req not in reserves:
            raise Incomplete("provider_allocation_evidence_missing")
        row = by_request[req]
        r, rp, rt = reserves[req]
        need(
            r < position
            and row["amount"] == rp["max_micro_usd"] == record["reserved_micro_usd"]
            and row["purpose"] == record["purpose"],
            "provider_allocation_event_join",
        )
        reserve_day = stamp(rt).astimezone(LA).date().isoformat()
        need(
            calendar_day(rp["day"]) == reserve_day and row["day"] <= reserve_day,
            "allocation_after_ordinary_reserve",
        )
        upper_days[req] = reserve_day
        purposes[req] = record["purpose"]
        if r <= cut:
            before.append(row["rowid"])
    last_before = max(before, default=0)
    first_after = min(after, default=(rows[-1]["rowid"] + 1 if rows else 1))
    need(
        last_before < first_after
        and last_before <= maxrow < first_after
        and (maxrow == 0 or any(row["rowid"] == maxrow for row in rows)),
        "incorrect_allocation_prefix",
    )
    if any(last_before < row["rowid"] < first_after for row in rows):
        raise Incomplete("allocation_cut_not_provable")
    need(maxrow == last_before, "incorrect_allocation_prefix")
    if planning_day is not None:
        return spending_bounds(rows, maxrow, planning_day, exact_days, upper_days, purposes)


def verify_headroom(db, chain, events):
    snapshot = chain["budget"]
    cut = chain["prelaunch"]
    day = snapshot["day"]
    n = snapshot["event_count"]
    maxrow = snapshot["purpose_allocation_max_rowid"]
    need(
        integer(n, 1)
        and n <= cut["event_count"]
        and one(db, "SELECT event_hash FROM events WHERE id=?", (n,))[0]
        == snapshot["event_head_sha256"],
        "budget_cut",
    )
    need(
        stamp(snapshot["observed_at"]).astimezone(LA).date().isoformat() == day
        and snapshot["required_micro_usd"] == 2625000
        and snapshot["planning_only"] is True,
        "budget_day",
    )
    holds = {}
    for number, kind, payload, occurred in events:
        if number > n:
            break
        if kind == "budget_reserved":
            req = payload["request_id"]
            need(req not in holds and integer(payload["max_micro_usd"], 1), "budget_event")
            reserve_day = calendar_day(payload["day"])
            need(
                reserve_day == stamp(occurred).astimezone(LA).date().isoformat()
                and reserve_day <= day,
                "global_reservation_day_mismatch",
            )
            holds[req] = [reserve_day, payload["max_micro_usd"], None, "reserved"]
        elif kind in {"budget_settled", "budget_uncertain", "budget_overage"}:
            req = payload["request_id"]
            need(req in holds, "budget_event")
            entry = holds[req]
            if kind != "budget_uncertain":
                need(integer(payload["actual_micro_usd"]), "budget_event")
                entry[2] = payload["actual_micro_usd"]
            entry[3] = "settled" if kind == "budget_settled" else "uncertain"
    total = sum(
        a if state == "settled" else max(reserved, a or 0)
        for d, reserved, a, state in holds.values()
        if d == day
    )
    bounds = verify_allocation_prefix(db, events, n, maxrow, planning_day=day)
    purpose = one(
        db,
        "SELECT COALESCE(SUM(amount),0) FROM provider_allocations WHERE rowid<=? AND day=? AND purpose='research'",
        (maxrow, day),
    )[0]
    need(
        snapshot["global_limit_micro_usd"] == 20000000
        and snapshot["purpose_limit_micro_usd"] == 4000000
        and snapshot["global_remaining_micro_usd"] == max(0, 20000000 - total)
        and snapshot["purpose_remaining_micro_usd"] == 4000000 - purpose
        and min(snapshot["global_remaining_micro_usd"], snapshot["purpose_remaining_micro_usd"])
        >= 2625000,
        "launch_headroom",
    )

    bounds["captured_research_micro_usd"] = purpose
    bounds["worst_case_remaining_micro_usd"] = 4000000 - bounds["maximum_research_micro_usd"]
    chain["planning_budget_evidence"] = bounds
    need(
        4000000 - bounds["minimum_research_micro_usd"] >= snapshot["required_micro_usd"],
        "insufficient_proven_purpose_headroom",
    )
    if bounds["worst_case_remaining_micro_usd"] < snapshot["required_micro_usd"]:
        raise Incomplete("purpose_headroom_not_provable")


def accounting(store, chain, run_id, fixture, parse):
    from quanto import provider
    from quanto.research_packets import packet_messages, validate_packet

    db = store.journal.connection
    events = [
        (r["id"], r["kind"], parse(r["payload"].encode()), r["occurred_at"])
        for r in db.execute("SELECT id,kind,payload,occurred_at FROM events ORDER BY id")
    ]
    verify_headroom(db, chain, events)
    rows = db.execute(
        "SELECT h.*,a.role,a.contract FROM research_dispatch_holds h JOIN workflow_assignments a USING(assignment_id) WHERE a.run_id=?",
        (run_id,),
    ).fetchall()
    need(len(rows) <= 7, "too_many_dispatches")
    fingerprint_kind = "canonical_synthetic_envelope" if fixture else "http_body_bytes"
    transport = "synthetic_fixture" if fixture else "anthropic_api"
    checked = []
    ids = set()
    for hold in rows:
        req = hold["request_id"]
        model = chain["configuration"]["models"][hold["role"]]
        indexed = {}
        for n, k, p, t in events:
            if p.get("request_id") == req:
                indexed.setdefault(k, []).append((n, p, t))

        def event(kind):
            vals = indexed.get(kind, [])
            need(len(vals) == 1, "event_cardinality")
            return vals[0]

        res = one(db, "SELECT * FROM reservations WHERE request_id=?", (req,))
        allocation = one(db, "SELECT * FROM provider_allocations WHERE request_id=?", (req,))
        dispatch = one(db, "SELECT * FROM dispatches WHERE request_id=?", (req,))
        stamp0, amount = res["day"], hold["amount"]
        need(stamp0 == chain["budget"]["day"], "authorization_outside_planning_day")
        a, ar, at = event("budget_reserved")
        d, dr, dt = event("dispatch_authorized")
        h, hr, ht = event("workflow_research_dispatch_authorized")
        need(
            chain["prelaunch"]["event_count"] < a < d < h
            and ar == {"request_id": req, "day": stamp0, "max_micro_usd": amount}
            and res["created_at"] == at
            and res["reserved_micro_usd"] == amount,
            "reservation_event",
        )
        need(
            stamp(at).astimezone(LA).date().isoformat() == stamp0
            and stamp(dt).astimezone(LA).date().isoformat() == stamp0
            and dict(dispatch) == dr == {"request_id": req, "day": stamp0, "authorized_at": dt},
            "dispatch_event",
        )
        need(
            dict(allocation)
            == {"request_id": req, "day": stamp0, "purpose": "research", "amount": amount}
            and hold["transport_kind"] == transport
            and hr
            == {
                "request_id": req,
                "assignment_id": hold["assignment_id"],
                "requested_model": model,
                "reserved_micro_usd": amount,
                "transport_kind": transport,
                "price_verified_on": provider.PRICE_VERIFIED_ON,
                "price_sources": provider.PRICE_SOURCES,
            },
            "purpose_event",
        )
        contract = parse(hold["contract"].encode())
        packet = validate_packet(store.read_json(hold["packet_sha256"]))
        message = packet_messages(packet)
        prepared = provider.prepare_research_text(
            model=model,
            system=message["system"],
            messages=message["messages"],
            max_tokens=min(
                4096 if model == provider.OPUS else 2048, max(1, contract["max_output_bytes"] // 4)
            ),
            max_input_bytes=contract["max_input_bytes"],
        )
        need(
            prepared.reserved_micro_usd == amount and digest(prepared.body) == hold["body_sha256"],
            "dispatch_body",
        )
        effect = db.execute(
            "SELECT * FROM workflow_effect_outcomes WHERE assignment_id=? AND request_id=?",
            (hold["assignment_id"], req),
        ).fetchone()
        observed = db.execute(
            "SELECT * FROM research_model_observations WHERE request_id=?", (req,)
        ).fetchone()
        priv = db.execute(
            "SELECT * FROM research_private_responses WHERE request_id=?", (req,)
        ).fetchone()
        charged = None
        if priv is not None:
            need(observed is not None, "response_observation")
            response = store.read_json(priv["artifact_sha256"])
            header = parse(observed["observation"].encode())
            rid = response["provider_request_id"]
            need(
                type(rid) is str
                and 0 < len(rid) <= 200
                and rid not in ids
                and header
                == {
                    "envelope_type": "dict",
                    "id": rid,
                    "model": model,
                    "type": "message",
                    "stop_reason": "end_turn",
                },
                "response_identity",
            )
            ids.add(rid)
            need(
                response["response_hash_kind"] == fingerprint_kind
                and is_sha(response["response_sha256"])
                and response["request_id"] == req
                and response["body_sha256"] == hold["body_sha256"]
                and response["observed_model"] == response["requested_model"] == model
                and response["terminal"] == "completed"
                and response["transport_kind"] == transport
                and response["actual_model_evidence"] is (not fixture),
                "response_digest",
            )
            usage = response["usage"]
            need(
                set(usage)
                == {
                    "input_tokens",
                    "output_tokens",
                    "cache_creation_input_tokens",
                    "cache_read_input_tokens",
                }
                and all(integer(n) for n in usage.values())
                and usage["output_tokens"] <= prepared.max_tokens
                and sum(n for k, n in usage.items() if k != "output_tokens")
                <= len(prepared.body) + 65536,
                "usage_bound",
            )
            charged = provider.usage_cost(model, usage)
            need(
                integer(response["cost_micro_usd"])
                and response["cost_micro_usd"] == charged <= amount
                and response["cost_kind"] == "conservative_upper_bound",
                "response_price",
            )
        need(
            hold["created_at"] == ht
            and stamp(ht).astimezone(LA).date().isoformat() == stamp0
            and one(db, "SELECT rowid FROM provider_allocations WHERE request_id=?", (req,))[0]
            > chain["budget"]["purpose_allocation_max_rowid"],
            "hold_time_or_cut",
        )
        if priv is not None and fixture:
            need(
                chain["synthetic_fingerprints"].get(rid) == response["response_sha256"],
                "fixture_fingerprint_value",
            )
        finish = None
        if effect is not None:
            finish, fp, ft = event("workflow_effect_finished")
            need(
                fp
                == {
                    "assignment_id": hold["assignment_id"],
                    "request_id": req,
                    "status": effect["status"],
                    "artifact_refs": parse(effect["artifact_refs"].encode()),
                    "observed_model": effect["observed_model"],
                }
                and finish > h,
                "effect_finish_event",
            )
        else:
            need(not indexed.get("workflow_effect_finished"), "missing_effect_row")
        if res["state"] == "settled":
            n, p, t = event("budget_settled")
            need(finish is not None and finish < n, "settlement_order")
            need(
                n > h
                and not indexed.get("budget_uncertain")
                and not indexed.get("budget_overage")
                and p == {"request_id": req, "actual_micro_usd": charged}
                and charged is not None
                and res["actual_micro_usd"] == charged
                and res["updated_at"] == t
                and effect is not None
                and effect["status"] == "success",
                "settlement_event",
            )
        elif res["state"] == "uncertain":
            n, p, t = event("budget_uncertain")
            need(finish is None or n < finish, "uncertainty_order")
            need(
                n > h
                and p
                == {"request_id": req, "reason": "Research dispatch uncertain; no automatic replay"}
                and not indexed.get("budget_settled")
                and not indexed.get("budget_overage")
                and res["actual_micro_usd"] is None
                and res["updated_at"] == t
                and (effect is None or effect["status"] == "uncertain"),
                "uncertain_hold_event",
            )
        else:
            raise Incomplete("unterminated_hold")
        checked.append(
            {
                "request_id": req,
                "state": res["state"],
                "response_digest_checked": priv is not None,
                "reserved": amount,
                "charged": charged,
            }
        )
    return checked

"""Complete, registered D007 scenario rosters and explicit bounded invocations.

This is a lead-invoked workflow, not an unattended scheduler. A later invocation
is an explicit replay of all three unchanged requests; interrupted invocations
are inspectable and never resumed automatically. No network or engine is called
here: calculations use the registered explorer boundary.
"""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from quanto.ledger import LedgerError, canonical_json, hash_bytes, hash_json
from quanto.provenance import Provenance, ProvenanceError

COSTS = (0, 10, 25)
_SCHEMA = """
CREATE TABLE IF NOT EXISTS study_suite_runs (
 submission_id TEXT PRIMARY KEY, suite_sha256 TEXT NOT NULL, roster_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS study_suite_launches (
 run_id TEXT NOT NULL, cost_bps INTEGER NOT NULL, request_sha256 TEXT NOT NULL,
 PRIMARY KEY (run_id, cost_bps)
);
CREATE TABLE IF NOT EXISTS study_suite_results (
 run_id TEXT NOT NULL, cost_bps INTEGER NOT NULL, child_submission_id TEXT NOT NULL,
 PRIMARY KEY (run_id, cost_bps)
);
CREATE TABLE IF NOT EXISTS study_suite_failures (
 run_id TEXT NOT NULL, cost_bps INTEGER NOT NULL, error_code TEXT NOT NULL,
 PRIMARY KEY (run_id, cost_bps)
);
"""


class StudySuiteError(ValueError):
    """Fixed, safe scenario-suite refusal."""


def _need(condition, code):
    if not condition:
        raise StudySuiteError(code)


def _schema(store):
    connection = store.journal.connection
    connection.executescript(_SCHEMA)
    for table in ("study_suite_runs", "study_suite_launches", "study_suite_results", "study_suite_failures"):
        for operation in ("UPDATE", "DELETE"):
            connection.execute(
                f"CREATE TRIGGER IF NOT EXISTS no_{operation.lower()}_{table} "
                f"BEFORE {operation} ON {table} BEGIN "
                "SELECT RAISE(ABORT, 'append-only record'); END"
            )


def _position(store, submission_id, phase):
    # The revision validator cross-checks journal events and materialized receipts.
    from quanto.policy_revision import _position as position
    return position(store, submission_id, phase)


def _admission_precedes(store, admission_sha256, submission_id):
    before = _position(store, submission_id, "started")
    rows = store.journal.connection.execute(
        "SELECT submission_id,details FROM provenance_outcomes JOIN provenance_submissions "
        "USING(submission_id) WHERE status='success' AND kind='historical_admission'"
    ).fetchall()
    for row in rows:
        if json.loads(row["details"]).get("admission_sha256") == admission_sha256:
            start = _position(store, row["submission_id"], "started")
            finish = _position(store, row["submission_id"], "finished")
            if start < finish < before:
                return
    raise StudySuiteError("suite_admission_order_mismatch")


def _members(store, request):
    from quanto.admission import validate_admission
    from quanto.explorer import _ref, _text
    from quanto.policy_revision import validate_study

    _need(set(request) == {"members"}, "invalid_suite_fields")
    members = request["members"]
    _need(isinstance(members, list) and len(members) == 3, "three_suite_members_required")
    required = {"dataset_sha256", "study_name", "evaluation_start", "evaluation_end",
                "specification", "admission_sha256"}
    common, by_cost = None, {}
    for member in members:
        _need(isinstance(member, dict) and set(member) == required, "invalid_suite_member_fields")
        _text(member["study_name"])
        _ref(member["dataset_sha256"])
        _ref(member["admission_sha256"])
        spec = member["specification"]
        _need(isinstance(spec, dict), "invalid_suite_specification")
        cost = spec.get("cost_bps")
        _need(type(cost) is int and cost in COSTS and cost not in by_cost,
              "suite_cost_roster_mismatch")
        base = {**member, "specification": {key: value for key, value in spec.items()
                                             if key != "cost_bps"}}
        if common is None:
            common = base
        _need(canonical_json(base) == canonical_json(common), "suite_members_differ_beyond_cost")
        by_cost[cost] = member
    first = by_cost[0]
    admission = validate_admission(store, first["admission_sha256"], first["dataset_sha256"])
    revision_sha256 = _ref(admission.get("policy_revision_sha256"))
    for cost in COSTS:
        validate_study(store, revision_sha256, by_cost[cost])
    refs = {first["admission_sha256"], revision_sha256, first["dataset_sha256"],
            *admission["artifact_refs"]}
    for ref in refs:
        store.read_bytes(_ref(ref))
    return ([{"cost_bps": cost, "request": by_cost[cost],
              "request_sha256": hash_json(by_cost[cost])} for cost in COSTS],
            revision_sha256, sorted(refs))


def _safe_failure(store, submission, status, code, **extra):
    details = {"error_code": code, "result_kind": "no_suite", **extra}
    summary = None
    try:
        if store.journal.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='study_suite_runs'"
        ).fetchone() and store.journal.connection.execute(
            "SELECT 1 FROM study_suite_runs WHERE submission_id=?", (submission,)
        ).fetchone():
            summary = _summary(store, submission)
            summary_sha256 = store.put_json(summary)
            details.update(result_kind="suite_incomplete", summary_sha256=summary_sha256,
                           suite_sha256=summary["suite_sha256"], complete=summary["complete"],
                           all_success=summary["all_success"],
                           artifact_refs=[summary_sha256])
    except (OSError, sqlite3.Error, ProvenanceError, LedgerError):
        pass
    try:
        store.finish(submission, status, details)
    except (OSError, sqlite3.Error, ProvenanceError, LedgerError):
        return {"submission_id": submission, "status": "pending", **details,
                **({"summary": summary} if summary is not None else {}),
                "error_code": "publication_interrupted"}
    return {"submission_id": submission, "status": status, **details,
            **({"summary": summary} if summary is not None else {})}


def register_suite(root: Path, request: dict | str) -> dict:
    """Record before validation, then freeze exactly three complete study requests."""
    from quanto.admission import AdmissionError
    from quanto.explorer import ExplorationError, _envelope, _request
    from quanto.policy_revision import PolicyRevisionError

    with Provenance(root) as store:
        frozen = _envelope(request)
        submission = store.begin("study_suite_registration", frozen)
        publishing = False
        try:
            data = _request(frozen)
            members, revision, refs = _members(store, data)
            _admission_precedes(store, members[0]["request"]["admission_sha256"], submission)
            publishing = True
            # Only semantically accepted requests are retained by bytes. Malformed
            # input remains represented by its bounded submission digest only.
            request_sha256 = store.put_bytes(frozen.encode("utf-8"))
            manifest = {"schema_version": 1, "kind": "study_suite", "submission_id": submission,
                        "registration_request_sha256": request_sha256,
                        "members": members, "policy_revision_sha256": revision,
                        "artifact_refs": sorted({request_sha256, *refs})}
            digest = store.put_json(manifest)
            details = {"suite_sha256": digest, "member_count": 3,
                       "artifact_refs": sorted({digest, *manifest["artifact_refs"]})}
            store.finish(submission, "success", details)
            return {"submission_id": submission, "status": "success", **details}
        except (StudySuiteError, ExplorationError, AdmissionError, PolicyRevisionError) as exc:
            return _safe_failure(store, submission, "invalid", str(exc))
        except (ProvenanceError, LedgerError):
            return _safe_failure(store, submission, "interrupted" if publishing else "invalid",
                                 "publication_interrupted" if publishing else "artifact_or_storage_unavailable")
        except (OSError, sqlite3.Error):
            return _safe_failure(store, submission, "interrupted", "storage_interrupted")
        except Exception:
            return _safe_failure(store, submission, "failed", "suite_registration_failed")


def _verified(store, digest, *, before_submission_id=None):
    from quanto.explorer import _ref, _request

    manifest = store.read_json(_ref(digest))
    _need(isinstance(manifest, dict) and manifest.get("kind") == "study_suite"
          and manifest.get("schema_version") == 1, "invalid_suite_manifest")
    registration = store.get_submission(manifest["submission_id"])
    _need(registration["kind"] == "study_suite_registration" and registration["status"] == "success"
          and registration["details"].get("suite_sha256") == digest
          and digest in registration["details"].get("artifact_refs", []), "suite_not_registered")
    for ref in registration["details"]["artifact_refs"]:
        store.read_bytes(_ref(ref))
    raw = store.read_bytes(_ref(manifest["registration_request_sha256"]))
    _need(hash_bytes(raw) == registration["request_sha256"]
          and len(raw) == registration["request_bytes"], "suite_registration_request_mismatch")
    members, revision, refs = _members(store, _request(raw.decode("utf-8")))
    _admission_precedes(store, members[0]["request"]["admission_sha256"], registration["submission_id"])
    expected = {"schema_version": 1, "kind": "study_suite", "submission_id": registration["submission_id"],
                "registration_request_sha256": hash_bytes(raw), "members": members,
                "policy_revision_sha256": revision,
                "artifact_refs": sorted({hash_bytes(raw), *refs})}
    _need(hash_json(manifest) == hash_json(expected), "suite_dependencies_changed")
    start = _position(store, registration["submission_id"], "started")
    finish = _position(store, registration["submission_id"], "finished")
    _need(start < finish, "suite_registration_order_mismatch")
    if before_submission_id is not None:
        _need(finish < _position(store, before_submission_id, "started"),
              "suite_registered_after_study")
    return manifest


def validate_membership(store: Provenance, suite_sha256: str, study_request: dict,
                        *, before_submission_id=None) -> dict:
    """Verify full roster, current dependencies, exact member and event ordering."""
    manifest = _verified(store, suite_sha256, before_submission_id=before_submission_id)
    _need(isinstance(study_request, dict)
          and study_request.get("suite_sha256") == suite_sha256, "suite_identity_mismatch")
    request = {key: value for key, value in study_request.items() if key != "suite_sha256"}
    matches = [member for member in manifest["members"] if member["request_sha256"] == hash_json(request)]
    _need(len(matches) == 1, "study_not_in_suite")
    return {"suite_sha256": suite_sha256, "member": matches[0], "members": manifest["members"],
            "policy_revision_sha256": manifest["policy_revision_sha256"],
            "artifact_refs": sorted({suite_sha256, *manifest["artifact_refs"]})}


def validate_launch(store: Provenance, run_id: str | None, request: dict,
                    child_id: str, *, bind: bool = False) -> None:
    """Require a precommitted run/launch and bind its child before computation."""
    from quanto.explorer import _request
    _need(isinstance(run_id, str) and bool(run_id), "suite_invocation_required")
    _schema(store)
    run = store.get_submission(run_id)
    _need(run["kind"] == "study_suite_run" and run["status"] == "pending",
          "suite_invocation_not_pending")
    row = store.journal.connection.execute(
        "SELECT * FROM study_suite_runs WHERE submission_id=?", (run_id,)).fetchone()
    _need(row is not None and row["suite_sha256"] == request.get("suite_sha256"),
          "suite_invocation_mismatch")
    roster = store.read_json(row["roster_sha256"])
    raw = store.read_bytes(roster["run_request_sha256"])
    _need(hash_bytes(raw) == run["request_sha256"] and len(raw) == run["request_bytes"]
          and _request(raw.decode("utf-8")) == {"suite_sha256": row["suite_sha256"]},
          "suite_invocation_request_mismatch")
    manifest = store.read_json(row["suite_sha256"])
    expected = {"schema_version": 1, "kind": "study_suite_run_roster", "submission_id": run_id,
                "suite_sha256": row["suite_sha256"], "run_request_sha256": roster["run_request_sha256"],
                "members": [{**item, "request": {**item["request"], "suite_sha256": row["suite_sha256"]},
                             "request_sha256": hash_json({**item["request"], "suite_sha256": row["suite_sha256"]})}
                            for item in manifest["members"]]}
    _need(hash_json(roster) == hash_json(expected), "suite_invocation_roster_mismatch")
    digest, cost = hash_json(request), request["specification"]["cost_bps"]
    _need(roster.get("submission_id") == run_id and roster.get("suite_sha256") == row["suite_sha256"]
          and sum(item["request_sha256"] == digest and hash_json(item["request"]) == digest
                  and item["cost_bps"] == cost for item in roster["members"]) == 1,
          "suite_launch_request_mismatch")
    launch = store.journal.connection.execute(
        "SELECT request_sha256 FROM study_suite_launches WHERE run_id=? AND cost_bps=?",
        (run_id, cost)).fetchone()
    child = store.get_submission(child_id)
    _need(launch is not None and launch["request_sha256"] == digest
          and child["kind"] == "exploratory_study" and child["status"] == "pending"
          and child["request_sha256"] == digest, "suite_launch_request_mismatch")
    events = {}
    for event in store.journal.connection.execute(
            "SELECT id,kind,payload FROM events WHERE kind IN "
            "('study_suite_run_registered','study_suite_member_launched')"):
        payload = json.loads(event["payload"])
        match = (payload.get("submission_id") == run_id if event["kind"] == "study_suite_run_registered"
                 else payload.get("run_id") == run_id and payload.get("cost_bps") == cost)
        if match:
            _need(event["kind"] not in events, "suite_launch_event_mismatch")
            if event["kind"] == "study_suite_run_registered":
                _need(payload.get("roster_sha256") == row["roster_sha256"]
                      and payload.get("suite_sha256") == row["suite_sha256"]
                      and payload.get("member_count") == 3, "suite_launch_event_mismatch")
            else:
                _need(payload.get("request_sha256") == digest, "suite_launch_event_mismatch")
            events[event["kind"]] = event["id"]
    _need(set(events) == {"study_suite_run_registered", "study_suite_member_launched"}
          and _position(store, run_id, "started") < events["study_suite_run_registered"]
          < events["study_suite_member_launched"] < _position(store, child_id, "started"),
          "suite_launch_must_precede_study")
    with store.journal._transaction():
        found = store.journal.connection.execute(
            "SELECT child_submission_id FROM study_suite_results WHERE run_id=? AND cost_bps=?",
            (run_id, cost)).fetchone()
        if bind:
            _need(found is None, "suite_launch_already_bound")
            store.journal.connection.execute("INSERT INTO study_suite_results VALUES (?,?,?)",
                                             (run_id, cost, child_id))
            store.journal._event("study_suite_member_bound", {
                "run_id": run_id, "cost_bps": cost, "child_submission_id": child_id,
            }, store.journal._now())
        else:
            _need(found is not None and found["child_submission_id"] == child_id,
                  "suite_child_binding_mismatch")


def _summary(store, run_id):
    run = store.get_submission(run_id)
    row = store.journal.connection.execute(
        "SELECT * FROM study_suite_runs WHERE submission_id=?", (run_id,)
    ).fetchone()
    _need(row is not None and run["kind"] == "study_suite_run", "unknown_suite_run")
    # Snapshot inspection still works if dependencies were later tombstoned. It
    # uses the exact pre-execution roster, never re-admits or executes a member.
    roster = store.read_json(row["roster_sha256"])
    members, refs = [], {row["suite_sha256"], row["roster_sha256"], roster["run_request_sha256"]}
    for item in roster["members"]:
        cost = item["cost_bps"]
        found = store.journal.connection.execute(
            "SELECT child_submission_id FROM study_suite_results WHERE run_id=? AND cost_bps=?",
            (run_id, cost),
        ).fetchone()
        launched = store.journal.connection.execute(
            "SELECT 1 FROM study_suite_launches WHERE run_id=? AND cost_bps=?", (run_id, cost)
        ).fetchone() is not None
        outcome = {"status": "pending", "phase": "launched" if launched else "not_started"}
        failure = store.journal.connection.execute(
            "SELECT error_code FROM study_suite_failures WHERE run_id=? AND cost_bps=?", (run_id, cost)
        ).fetchone()
        if failure:
            outcome = {"status": "pending", "dispatch_status": "failed", "error_code": failure["error_code"],
                       "phase": "dispatch_exception_child_identity_unconfirmed"}
        if found:
            child = store.get_submission(found["child_submission_id"])
            details = child["details"] or {}
            outcome = {"submission_id": child["submission_id"], "status": child["status"],
                       **{key: details[key] for key in ("error_code", "attempt_id", "fingerprint",
                                                       "artifact_sha256") if key in details}}
            refs.update(details.get("artifact_refs", []))
        members.append({**item, "outcome": outcome})
    statuses = [member["outcome"]["status"] for member in members]
    complete = all(status not in {"pending", "interrupted"} for status in statuses)
    return {"schema_version": 1, "kind": "study_suite_summary", "submission_id": run_id,
            "suite_sha256": row["suite_sha256"], "roster_sha256": row["roster_sha256"],
            "complete": complete, "all_success": statuses == ["success"] * 3,
            "members": members, "artifact_refs": sorted(refs)}


def inspect_run(root: Path, submission_id: str) -> dict:
    """Inspect every slot after completion or a crash; never rerun pending work."""
    with Provenance(root) as store:
        _schema(store)
        return _summary(store, submission_id)


def run_suite(root: Path, request: dict | str) -> dict:
    """Explicitly execute one registered roster once, preserving all three slots.

    Repeating this call creates a separate registered replay invocation. A crash
    leaves its existing run incomplete; this function never resumes an old run.
    """
    from quanto.admission import AdmissionError
    from quanto.explorer import ExplorationError, _envelope, _ref, _request, run_submission
    from quanto.policy_revision import PolicyRevisionError

    with Provenance(root) as store:
        frozen = _envelope(request)
        submission = store.begin("study_suite_run", frozen)
        publishing = False
        try:
            _schema(store)
            data = _request(frozen)
            _need(set(data) == {"suite_sha256"}, "invalid_suite_run_fields")
            digest = _ref(data["suite_sha256"])
            manifest = _verified(store, digest, before_submission_id=submission)
            roster = {"schema_version": 1, "kind": "study_suite_run_roster",
                      "submission_id": submission, "suite_sha256": digest,
                      "run_request_sha256": store.put_bytes(frozen.encode("utf-8")),
                      "members": [{**member, "request": {**member["request"], "suite_sha256": digest},
                                   "request_sha256": hash_json({**member["request"], "suite_sha256": digest})}
                                  for member in manifest["members"]]}
            publishing = True
            roster_sha256 = store.put_json(roster)
            with store.journal._transaction():
                store.journal.connection.execute("INSERT INTO study_suite_runs VALUES (?,?,?)",
                                                 (submission, digest, roster_sha256))
                store.journal._event("study_suite_run_registered", {
                    "submission_id": submission, "suite_sha256": digest,
                    "roster_sha256": roster_sha256, "member_count": 3,
                }, store.journal._now())
            for member in roster["members"]:
                # UNIQUE(run,cost) plus the claim committed before dispatch means
                # this invocation can never silently execute a member twice.
                with store.journal._transaction():
                    store.journal.connection.execute("INSERT INTO study_suite_launches VALUES (?,?,?)",
                                                     (submission, member["cost_bps"], member["request_sha256"]))
                    store.journal._event("study_suite_member_launched", {
                        "run_id": submission, "cost_bps": member["cost_bps"],
                        "request_sha256": member["request_sha256"],
                    }, store.journal._now())
                try:
                    result = run_submission(root, member["request"], suite_run_id=submission)
                except Exception:
                    # An unexpected dispatch exception does not erase the other
                    # scenarios or invent an explorer receipt. Its child state
                    # is unknown; no retry is attempted.
                    with store.journal._transaction():
                        store.journal.connection.execute("INSERT INTO study_suite_failures VALUES (?,?,?)",
                                                         (submission, member["cost_bps"], "member_dispatch_failed"))
                        store.journal._event("study_suite_member_dispatch_failed", {
                            "run_id": submission, "cost_bps": member["cost_bps"],
                            "error_code": "member_dispatch_failed",
                        }, store.journal._now())
                    continue
                child = store.get_submission(result["submission_id"])
                _need(child["kind"] == "exploratory_study"
                      and child["request_sha256"] == member["request_sha256"],
                      "suite_child_request_mismatch")
                with store.journal._transaction():
                    bound = store.journal.connection.execute(
                        "SELECT child_submission_id FROM study_suite_results WHERE run_id=? AND cost_bps=?",
                        (submission, member["cost_bps"])).fetchone()
                    if bound is None:
                        # Invalid requests may fail before reaching the launch gate.
                        store.journal.connection.execute("INSERT INTO study_suite_results VALUES (?,?,?)",
                                                         (submission, member["cost_bps"], child["submission_id"]))
                    else:
                        _need(bound["child_submission_id"] == child["submission_id"],
                              "suite_child_binding_mismatch")
                    store.journal._event("study_suite_member_recorded", {
                        "run_id": submission, "cost_bps": member["cost_bps"],
                        "child_submission_id": child["submission_id"], "status": child["status"],
                    }, store.journal._now())
            summary = _summary(store, submission)
            summary_sha256 = store.put_json(summary)
            statuses = [member["outcome"]["status"] for member in summary["members"]]
            status = ("interrupted" if not summary["complete"] else "success" if summary["all_success"]
                      else "failed" if "failed" in statuses else "invalid")
            details = {"suite_sha256": digest, "summary_sha256": summary_sha256,
                       "complete": summary["complete"], "all_success": summary["all_success"],
                       "artifact_refs": sorted({summary_sha256, *summary["artifact_refs"]})}
            store.finish(submission, status, details)
            return {"submission_id": submission, "status": status, **details, "summary": summary}
        except (StudySuiteError, ExplorationError, AdmissionError, PolicyRevisionError) as exc:
            return _safe_failure(store, submission, "invalid", str(exc))
        except (ProvenanceError, LedgerError):
            return _safe_failure(store, submission, "interrupted" if publishing else "invalid",
                                 "publication_interrupted" if publishing else "artifact_or_storage_unavailable")
        except (OSError, sqlite3.Error):
            return _safe_failure(store, submission, "interrupted", "storage_interrupted")
        except Exception:
            return _safe_failure(store, submission, "failed", "suite_execution_failed")

"""Registered, private D008 derivatives of one fresh complete D007 suite.

This cooperative local boundary trusts the broker to authorize exact role
handoffs and packet references. It grants no workflow capability or publication
authority. Values and even predicate truth stay private; completion_projection
releases only the predetermined lifecycle/integrity category.
"""
from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import sqlite3
import sys
from typing import Callable

from quanto import explorer, study_suite
from quanto.ledger import LedgerError, hash_bytes, hash_json
from quanto.provenance import Provenance, ProvenanceError
from quanto.research import StrategySpec
from quanto.research_packets import PREDICATES, PacketError, validate_projection

SEMANTICS = {
    "cost_ending_equity_nonincreasing": "strategy.ending_equity[0]>=strategy.ending_equity[10]>=strategy.ending_equity[25]",
    "cost_fees_nondecreasing": "strategy.total_fees[0]<=strategy.total_fees[10]<=strategy.total_fees[25]",
    "strategy_equals_benchmark_terminal": "all(strategy.ending_equity[c]==benchmark.ending_equity[c] for c in [0,10,25])",
}
NUMERICAL_POLICY = {
    "arithmetic": "exact Decimal comparisons without rounding or float conversion",
    "ties": "included", "cost_order": [0, 10, 25],
    "missing_or_unsuccessful": "no_result; never substitute another invocation",
    "decimal_encoding": "finite nonnegative str(Decimal(value)); zero is exactly 0",
    "maximum_characters": 128, "maximum_coefficient_digits": 34,
    "maximum_absolute_adjusted_exponent": 999999,
    "meaning": "descriptive development predicate; no universal theorem or investment inference",
}
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:E[+-][0-9]+)?\Z")
_SCHEMA = """
CREATE TABLE IF NOT EXISTS research_comparisons (
 submission_id TEXT PRIMARY KEY, registration_sha256 TEXT NOT NULL, fingerprint TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS research_comparison_invocations (
 submission_id TEXT PRIMARY KEY, suite_run_id TEXT NOT NULL UNIQUE
);
"""


class ComparisonError(ValueError):
    """Fixed local refusal with no submitted data in its text."""


def _need(condition, code):
    if not condition:
        raise ComparisonError(code)


def _same(left, right):
    # JSON identities distinguish booleans, integers and floating-point fields.
    return hash_json(left) == hash_json(right)


def _schema(store):
    store.journal.connection.executescript(_SCHEMA)
    for table in ("research_comparisons", "research_comparison_invocations"):
        for operation in ("UPDATE", "DELETE"):
            store.journal.connection.execute(
                f"CREATE TRIGGER IF NOT EXISTS no_{operation.lower()}_{table} "
                f"BEFORE {operation} ON {table} BEGIN "
                "SELECT RAISE(ABORT, 'append-only record'); END")


def _code_identity():
    module = sys.modules[__name__]
    return {"module_sha256": hash_bytes(Path(__file__).read_bytes()),
            "loaded_functions": explorer._loaded_engine_code(module),
            "semantics_sha256": hash_json(SEMANTICS),
            "numerical_policy_sha256": hash_json(NUMERICAL_POLICY),
            "decimal_pattern": _DECIMAL.pattern, "decimal_pattern_flags": _DECIMAL.flags,
            "supported_predicates": sorted(PREDICATES), "costs": list(study_suite.COSTS),
            "projection_validator": explorer._function_identity(validate_projection),
            "packet_module_sha256": hash_bytes(Path(sys.modules[validate_projection.__module__].__file__).read_bytes()),
            "loaded_packet_functions": explorer._loaded_engine_code(sys.modules[validate_projection.__module__]),
            "engine_identity": explorer._code_identity()}


def _number(value):
    _need(type(value) is str and len(value) <= 128 and _DECIMAL.fullmatch(value),
          "comparison_decimal_refused")
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise ComparisonError("comparison_decimal_refused") from None
    _need(number.is_finite() and number >= 0 and len(number.as_tuple().digits) <= 34
          and abs(number.adjusted()) <= 999999 and str(number) == value
          and (bool(number) or value == "0"), "comparison_decimal_refused")
    return number


def evaluate(predicate, operands):
    """Pure exact comparison; inputs are private and all three costs are required."""
    _need(type(predicate) is str and predicate in PREDICATES, "comparison_predicate_refused")
    _need(type(operands) is list and len(operands) == 3, "comparison_roster_mismatch")
    values = []
    for cost, row in zip(study_suite.COSTS, operands):
        _need(type(row) is dict and set(row) == {
            "cost_bps", "strategy_ending_equity", "strategy_total_fees", "benchmark_ending_equity"
        } and type(row["cost_bps"]) is int and row["cost_bps"] == cost,
              "comparison_roster_mismatch")
        values.append({key: _number(value) for key, value in row.items() if key != "cost_bps"})
    if predicate == "cost_ending_equity_nonincreasing":
        return values[0]["strategy_ending_equity"] >= values[1]["strategy_ending_equity"] >= values[2]["strategy_ending_equity"]
    if predicate == "cost_fees_nondecreasing":
        return values[0]["strategy_total_fees"] <= values[1]["strategy_total_fees"] <= values[2]["strategy_total_fees"]
    return all(row["strategy_ending_equity"] == row["benchmark_ending_equity"] for row in values)


def _inputs(store, data, submission):
    _need(set(data) == {"suite_sha256", "predicate", "hypothesis_sha256", "engineer_sha256"},
          "invalid_comparison_fields")
    predicate = data["predicate"]
    _need(type(predicate) is str and predicate in PREDICATES, "comparison_predicate_refused")
    for role, decision in (("hypothesis", "propose"), ("engineer", "execute")):
        value = store.read_json(explorer._ref(data[role + "_sha256"]))
        checked = validate_projection(value, allowed_aliases=[f"artifact-{i}" for i in range(1, 33)],
                                      allowed_predicates=PREDICATES, required_predicate=predicate)
        _need(checked["role"] == role and checked["decision"] == decision,
              "comparison_role_decision_mismatch")
    return study_suite._verified(store, explorer._ref(data["suite_sha256"]),
                                 before_submission_id=submission)


def _event(store, kind, match):
    import json
    found = []
    for row in store.journal.connection.execute("SELECT id,payload FROM events WHERE kind=?", (kind,)):
        value = json.loads(row["payload"])
        if all(value.get(key) == item for key, item in match.items()):
            found.append((row["id"], value))
    _need(len(found) == 1, "comparison_lineage_event_mismatch")
    return found[0]


def _operands(store, submission, registration, result):
    """Verify retained receipts, original request bytes, bindings and exact reports."""
    from quanto.admission import validate_admission

    store.journal.verify_events()
    data, manifest = registration["request"], registration["suite_manifest"]
    run_id = result["submission_id"]
    run = store.get_submission(run_id)
    _need(run["kind"] == "study_suite_run" and run["status"] == "success"
          and run["details"].get("suite_sha256") == data["suite_sha256"]
          and result["status"] == "success", "comparison_suite_unsuccessful")
    start = study_suite._position(store, run_id, "started")
    registered, _ = _event(store, "research_comparison_registered", {"submission_id": submission})
    _need(registered < start < study_suite._position(store, run_id, "finished"),
          "comparison_requires_fresh_suite")
    row = store.journal.connection.execute(
        "SELECT * FROM study_suite_runs WHERE submission_id=?", (run_id,)).fetchone()
    _need(row is not None and row["suite_sha256"] == data["suite_sha256"],
          "comparison_suite_lineage_mismatch")
    roster = store.read_json(row["roster_sha256"])
    raw = store.read_bytes(roster["run_request_sha256"])
    _need(hash_bytes(raw) == run["request_sha256"] and len(raw) == run["request_bytes"]
          and explorer._request(raw.decode()) == {"suite_sha256": data["suite_sha256"]},
          "comparison_suite_request_mismatch")
    members = [{**item, "request": {**item["request"], "suite_sha256": data["suite_sha256"]},
                "request_sha256": hash_json({**item["request"], "suite_sha256": data["suite_sha256"]})}
               for item in manifest["members"]]
    _need(_same(roster, {"schema_version": 1, "kind": "study_suite_run_roster", "submission_id": run_id,
                     "suite_sha256": data["suite_sha256"], "run_request_sha256": hash_bytes(raw),
                     "members": members}), "comparison_roster_mismatch")
    summary = study_suite._summary(store, run_id)
    _need(_same(summary, store.read_json(run["details"]["summary_sha256"]))
          and _same(result.get("summary"), summary) and result.get("summary_sha256") == run["details"]["summary_sha256"]
          and summary["all_success"] is True and summary["complete"] is True,
          "comparison_summary_mismatch")
    operands, sources, refs = [], [], {row["roster_sha256"], run["details"]["summary_sha256"]}
    for item in summary["members"]:
        child_id = item["outcome"]["submission_id"]
        child = store.get_submission(child_id)
        details, request, cost = child["details"], item["request"], item["cost_bps"]
        _need(child["kind"] == "exploratory_study" and child["status"] == "success"
              and child["request_sha256"] == item["request_sha256"] == hash_json(request)
              and child["request_bytes"] == len(explorer._envelope(request).encode())
              and details.get("suite_run_id") == run_id
              and details.get("suite_sha256") == data["suite_sha256"]
              and details.get("admission_sha256") == request["admission_sha256"]
              and details.get("dataset_sha256") == request["dataset_sha256"],
              "comparison_child_lineage_mismatch")
        launch, _ = _event(store, "study_suite_member_launched", {
            "run_id": run_id, "cost_bps": cost, "request_sha256": item["request_sha256"]})
        bound, _ = _event(store, "study_suite_member_bound", {
            "run_id": run_id, "cost_bps": cost, "child_submission_id": child_id})
        _need(start < launch < study_suite._position(store, child_id, "started") < bound
              < study_suite._position(store, child_id, "finished"), "comparison_child_order_mismatch")
        artifact = store.read_json(details["artifact_sha256"])
        membership = study_suite.validate_membership(store, data["suite_sha256"], request,
                                                    before_submission_id=child_id)
        admitted = validate_admission(store, request["admission_sha256"], request["dataset_sha256"])
        frozen = {"strategy": asdict(StrategySpec(**request["specification"])),
                  "evaluation_start": request["evaluation_start"], "evaluation_end": request["evaluation_end"],
                  "initial_position": "cash", "benchmark": "buy_and_hold_same_window_same_costs",
                  "purpose": "exploratory", "admission_scope": admitted["scope"],
                  "numerical_policy": registration["code_identity"]["engine_identity"]["event_policy"]}
        _need(type(artifact.get("schema_version")) is int and artifact["schema_version"] == 1
              and artifact.get("result_kind") == "exploratory_result"
              and artifact.get("dataset_sha256") == request["dataset_sha256"]
              and artifact.get("admission_sha256") == request["admission_sha256"]
              and _same(artifact.get("admission_evidence"), admitted)
              and artifact.get("evidence_kind") == details.get("evidence_kind") == "historical_market_data"
              and artifact.get("investment_evidence") is False
              and _same(artifact.get("study_suite"), membership) and _same(artifact.get("frozen_request"), frozen)
              and _same(artifact.get("code_identity"), registration["code_identity"]["engine_identity"]),
              "comparison_result_identity_mismatch")
        report = artifact["engine_report"]
        specification = asdict(StrategySpec(**request["specification"]))
        _need(_same(report.get("specification"), {
            key: value if key == "lookback" else str(value) for key, value in specification.items()})
            and report.get("evaluation_start") == request["evaluation_start"]
            and report.get("evaluation_end") == request["evaluation_end"]
            and report.get("evidence_kind") == "historical_market_data",
            "comparison_report_request_mismatch")
        operands.append({"cost_bps": cost,
                         "strategy_ending_equity": report["strategy"]["ending_equity"],
                         "strategy_total_fees": report["strategy"]["total_fees"],
                         "benchmark_ending_equity": report["benchmark"]["ending_equity"]})
        refs.update(details["artifact_refs"])
        sources.append({"cost_bps": cost, "submission_id": child_id,
                        "request_sha256": child["request_sha256"], "details": details})
    return operands, sources, sorted(refs)


def _finish(store, submission, status, details):
    try:
        store.finish(submission, status, details)
    except (OSError, sqlite3.Error, ProvenanceError, LedgerError):
        return {"submission_id": submission, "status": "pending", **details,
                "error_code": "comparison_publication_interrupted"}
    return {"submission_id": submission, "status": status, **details}


def run_comparison(root: Path, request: dict | str, *,
                   on_registered: Callable[[str], None] | None = None) -> dict:
    """Register first, execute one new suite once, then retain a private derivative.

    The exact four request fields are suite_sha256, predicate,
    hypothesis_sha256 and engineer_sha256. References identify validated safe
    projections; the broker binds their actual model/stage provenance separately.
    When supplied, on_registered binds this unique child to its consumed parent
    intent immediately after begin, before validation or financial work. Failure
    aborts without a suite invocation. This callback grants no broker authority;
    standalone trusted local calls may omit it.
    A crash leaves pending records. Calling again is an explicit new attempt.
    """
    with Provenance(root) as store:
        frozen = explorer._envelope(request)
        submission = store.begin("research_comparison", frozen)
        if on_registered is not None:
            try:
                on_registered(submission)
            except Exception:
                return _finish(store, submission, "invalid", {
                    "result_kind": "no_comparison",
                    "error_code": "comparison_registration_callback_failed"})
        details = {"result_kind": "no_comparison"}
        dispatched = False
        try:
            _schema(store)
            data = explorer._request(frozen)
            manifest = _inputs(store, data, submission)
            code = _code_identity()
            registration = {"schema_version": 1, "kind": "research_comparison_registration",
                            "submission_id": submission, "request": data,
                            "request_sha256": store.put_bytes(frozen.encode()),
                            "suite_manifest": manifest, "code_identity": code,
                            "predicate_semantics": SEMANTICS[data["predicate"]],
                            "numerical_policy": NUMERICAL_POLICY}
            fingerprint = hash_json({key: registration[key] for key in (
                "request", "suite_manifest", "code_identity", "predicate_semantics", "numerical_policy")})
            digest = store.put_json(registration)
            details.update(registration_sha256=digest, fingerprint=fingerprint)
            with store.journal._transaction():
                store.journal.connection.execute("INSERT INTO research_comparisons VALUES (?,?,?)",
                                                 (submission, digest, fingerprint))
                store.journal._event("research_comparison_registered", {
                    "submission_id": submission, "registration_sha256": digest, "fingerprint": fingerprint,
                }, store.journal._now())
            dispatched = True
            # Exactly one complete suite entrypoint; no fallback, substitution or retry.
            result = study_suite.run_suite(root, {"suite_sha256": data["suite_sha256"]})
            details["suite_run_id"] = result["submission_id"]
            with store.journal._transaction():
                store.journal.connection.execute("INSERT INTO research_comparison_invocations VALUES (?,?)",
                                                 (submission, result["submission_id"]))
                store.journal._event("research_comparison_suite_returned", {
                    "submission_id": submission, "suite_run_id": result["submission_id"],
                }, store.journal._now())
            _need(result["status"] == "success", "comparison_suite_unsuccessful")
            operands, sources, refs = _operands(store, submission, registration, result)
            outcome = evaluate(data["predicate"], operands)
            _need(_same(_inputs(store, data, submission), manifest) and _same(_code_identity(), code),
                  "comparison_dependencies_changed")
            artifact = store.put_json({"schema_version": 1, "kind": "research_comparison_result",
                "submission_id": submission, "registration_sha256": digest, "fingerprint": fingerprint,
                "suite_run_id": result["submission_id"], "predicate": data["predicate"],
                "operands": operands, "predicate_holds": outcome, "child_sources": sources,
                "investment_evidence": False, "classification": "development_only"})
            counts = store.journal.connection.execute(
                "SELECT COUNT(DISTINCT fingerprint),COUNT(*) FROM research_comparisons").fetchone()
            details.update(result_kind="research_comparison_result", comparison_sha256=artifact,
                derivative_candidate_count=counts[0], derivative_attempt_count=counts[1],
                artifact_refs=sorted({artifact, digest, registration["request_sha256"],
                    data["suite_sha256"], data["hypothesis_sha256"], data["engineer_sha256"], *refs}))
            return _finish(store, submission, "success", details)
        except ComparisonError as exc:
            code = str(exc)
        except (explorer.ExplorationError, PacketError):
            code = "comparison_input_refused"
        except study_suite.StudySuiteError:
            code = "comparison_suite_integrity_refused"
        except (ProvenanceError, LedgerError, OSError, sqlite3.Error):
            code = "comparison_artifact_or_storage_unavailable"
        except Exception:
            code = "comparison_execution_failed"
        status = "interrupted" if dispatched else "invalid"
        details["error_code"] = code
        return _finish(store, submission, status, details)


def completion_projection(receipt: dict) -> dict:
    """Predetermined egress category; never include predicate, values or identities."""
    state = receipt.get("status")
    _need(state in {"success", "invalid", "failed", "interrupted", "pending"},
          "comparison_receipt_refused")
    return {"schema_version": 1, "kind": "research_comparison_completion",
            "execution_state": "completed" if state == "success" else "failed" if state in {"invalid", "failed"} else "uncertain",
            "integrity_state": "verified" if state == "success" else "unverified"}

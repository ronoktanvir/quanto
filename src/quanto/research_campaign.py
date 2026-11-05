"""Finite, supervised development campaigns; no acquisition or order authority.

The active access session determines fixture status. Historical child records
created by fake transports remain fixtures at this campaign boundary. Existing
D007 fixed-study revisions are deliberately unsupported. Process supervision
must provide a hard deadline; the local deadline only fences publication and
entry to the next bounded slot. This is not protection against a hostile owner.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys
import time

from . import alpaca_data, explorer, research_metrics
from .admission import validate_admission
from .ledger import canonical_json, hash_json
from .policy_revision import _position, _registered
from .provenance import Provenance
from .research import StrategySpec

CRITERION = "validation_growth_then_turnover"
BLOCKS = ("development", "validation", "assessment")
MAX_SECONDS = 300
_SCHEMA = """
CREATE TABLE IF NOT EXISTS research_campaigns (
 campaign_sha256 TEXT PRIMARY KEY, submission_id TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS research_campaign_bindings (
 campaign_sha256 TEXT PRIMARY KEY, binding_sha256 TEXT UNIQUE NOT NULL,
 submission_id TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS research_campaign_runs (
 campaign_sha256 TEXT PRIMARY KEY, submission_id TEXT UNIQUE NOT NULL,
 binding_sha256 TEXT NOT NULL, roster_sha256 TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS research_campaign_claims (
 run_id TEXT NOT NULL, slot INTEGER NOT NULL, request_sha256 TEXT NOT NULL,
 event_id INTEGER NOT NULL, PRIMARY KEY(run_id,slot));
CREATE TABLE IF NOT EXISTS research_campaign_results (
 run_id TEXT NOT NULL, slot INTEGER NOT NULL, child_submission_id TEXT UNIQUE,
 outcome TEXT NOT NULL, PRIMARY KEY(run_id,slot));
"""


class CampaignError(ValueError):
    """Fixed campaign refusal category; provider exceptions never escape."""


def _need(condition, reason):
    if not condition:
        raise CampaignError(reason)


def _schema(store):
    db = store.journal.connection
    db.executescript(_SCHEMA)
    for table in ("campaigns", "campaign_bindings", "campaign_runs", "campaign_claims",
                  "campaign_results"):
        for operation in ("UPDATE", "DELETE"):
            db.execute(f"CREATE TRIGGER IF NOT EXISTS no_{operation.lower()}_research_{table} "
                       f"BEFORE {operation} ON research_{table} BEGIN "
                       "SELECT RAISE(ABORT, 'append-only campaign record'); END")


def code_identity():
    """Bind the additional wrapper/reducer as well as existing explorer code."""
    directory = Path(__file__).parent
    module = sys.modules[__name__]
    return {"core": explorer._code_identity(), "sources": {
        name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
        for name in ("research_campaign.py", "research_metrics.py")},
        "loaded_campaign": explorer._loaded_engine_code(module),
        "campaign_globals": explorer._engine_globals(module),
        "loaded_metrics": explorer._loaded_engine_code(research_metrics),
        "metrics_globals": explorer._engine_globals(research_metrics),
        "dispatcher": explorer._function_identity(explorer.run_submission)}


def _parse(value):
    try:
        return explorer._request(value if isinstance(value, str) else canonical_json(value))
    except (TypeError, ValueError, RecursionError, OverflowError):
        raise CampaignError("invalid_request") from None


def _day(value):
    _need(type(value) is str and date.fromisoformat(value).isoformat() == value,
          "invalid_calendar_date")
    return date.fromisoformat(value)


def _design(value):
    _need(type(value) is dict and set(value) == {
        "rationale", "instrument_selection_rule", "candidate_sources"}, "invalid_design_fields")
    for field in ("rationale", "instrument_selection_rule"):
        text = value[field]
        _need(type(text) is str and bool(text.strip()) and len(text) <= 2000
              and all(ord(c) >= 32 or c in "\n\t" for c in text), "invalid_design_text")
    sources = value["candidate_sources"]
    _need(type(sources) is list and 1 <= len(sources) <= 10, "invalid_candidate_sources")
    _need(all(type(text) is str and bool(text.strip()) and len(text) <= 500
              and all(ord(c) >= 32 for c in text) for text in sources),
          "invalid_candidate_sources")
    # These are attributed design inputs, not verified publication contents.
    return value


def _request(value):
    keys = {"market", "acquisition_request", "candidates", "cost_bps", "primary_cost_bps",
            "starting_cash", "blocks", "selection_criterion", "design"}
    _need(type(value) is dict and set(value) == keys, "invalid_campaign_fields")
    _design(value["design"])
    market = explorer._market(value["market"])
    _need(market["currency"] == "USD" and market["session_timezone"] == "America/New_York"
          and market["venue"] == "SIP", "unsupported_market")
    acquisition = alpaca_data._request(value["acquisition_request"], "bars",
                                       datetime.now(timezone.utc))
    _need(acquisition["adjustment"] == "raw", "raw_prices_required")
    costs = value["cost_bps"]
    _need(type(costs) is list and len(costs) == 3
          and all(type(c) is int and 0 <= c < 10000 for c in costs)
          and costs == sorted(set(costs)) and costs[0] == 0, "invalid_cost_roster")
    _need(type(value["primary_cost_bps"]) is int and value["primary_cost_bps"] in costs[1:],
          "invalid_primary_cost")
    _need(value["selection_criterion"] == CRITERION, "unsupported_selection")
    candidates = value["candidates"]
    _need(type(candidates) is list and 1 <= len(candidates) <= 3, "invalid_candidate_count")
    normalized, names, specs = [], set(), set()
    for candidate in candidates:
        _need(type(candidate) is dict and set(candidate) == {"id", "specification"},
              "invalid_candidate")
        name, spec = candidate["id"], candidate["specification"]
        _need(type(name) is str and re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", name)
              and name not in names, "invalid_candidate_id")
        _need(type(spec) is dict and set(spec) == {"lookback", "entry_threshold", "exit_threshold"},
              "invalid_candidate_specification")
        checked = asdict(StrategySpec(**spec, starting_cash=value["starting_cash"], cost_bps=0))
        semantic = (checked["lookback"], Decimal(str(checked["entry_threshold"])),
                    Decimal(str(checked["exit_threshold"])))
        _need(semantic not in specs, "duplicate_candidate")
        names.add(name)
        specs.add(semantic)
        normalized.append({"id": name, "specification": {
            key: checked[key] for key in ("lookback", "entry_threshold", "exit_threshold")}})
    blocks = value["blocks"]
    _need(type(blocks) is list and len(blocks) == 3, "invalid_blocks")
    for index, block in enumerate(blocks):
        _need(type(block) is dict and set(block) == {"name", "start", "end"}
              and block["name"] == BLOCKS[index], "invalid_blocks")
        start, end = _day(block["start"]), _day(block["end"])
        _need(start <= end, "invalid_blocks")
        if index:
            _need(_day(blocks[index - 1]["end"]) + timedelta(days=1) == start,
                  "noncontiguous_blocks")
    _need(acquisition["start"] < blocks[0]["start"]
          and blocks[-1]["end"] <= acquisition["end"], "coverage_outside_acquisition")
    return {**value, "market": market, "acquisition_request": acquisition,
            "candidates": normalized}


def _fail(store, submission, reason, status="invalid"):
    details = {"error_code": reason, "investment_validation": False,
               "protected_evaluation": False}
    try:
        store.finish(submission, status, details)
    except Exception:
        return {"submission_id": submission, "status": "pending",
                "error_code": "publication_unavailable"}
    return {"submission_id": submission, "status": status, **details}


def register_campaign(root: Path, request: dict | str) -> dict:
    """Register bounded intent before semantic validation or any acquisition."""
    with Provenance(root) as store:
        frozen = explorer._envelope(request)
        submission = store.begin("campaign_registration", frozen)
        try:
            _schema(store)
            normalized = _request(_parse(frozen))
            raw_sha = store.put_bytes(frozen.encode())
            manifest = {"schema_version": 1, "kind": "finite_development_campaign",
                        "request_sha256": raw_sha, "request": normalized,
                        "code_identity": code_identity(), "evidence_kind": (
                            "synthetic_fixture" if store.access.synthetic else "historical_market_data"),
                        "holdout_status": "unprotected_development",
                        "investment_validation": False, "protected_evaluation": False,
                        "candidate_count": len(normalized["candidates"]),
                        "slot_count": len(normalized["candidates"]) * 3}
            digest = store.put_json(manifest)
            with store.journal._transaction():
                store.journal.connection.execute("INSERT INTO research_campaigns VALUES (?,?)",
                                                 (digest, submission))
                details = {"campaign_sha256": digest, "artifact_refs": [digest, raw_sha]}
                store.finish(submission, "success", details)
            return {"submission_id": submission, "status": "success", **details}
        except CampaignError as exc:
            return _fail(store, submission, str(exc))
        except Exception:
            return _fail(store, submission, "campaign_registration_refused")


def _campaign(store, digest):
    digest = explorer._ref(digest)
    row = store.journal.connection.execute(
        "SELECT submission_id FROM research_campaigns WHERE campaign_sha256=?", (digest,)).fetchone()
    _need(row is not None, "unknown_campaign")
    registered, _, finished = _registered(store, row[0], digest,
                                         {"campaign_registration"}, {"campaign_sha256"})
    manifest = store.read_json(digest)
    raw = store.read_bytes(manifest["request_sha256"])
    _need(hashlib.sha256(raw).hexdigest() == registered["request_sha256"]
          and len(raw) == registered["request_bytes"]
          and _request(_parse(raw.decode())) == manifest["request"], "campaign_request_changed")
    _need(manifest["code_identity"] == code_identity(), "campaign_code_changed")
    expected = "synthetic_fixture" if store.access.synthetic else "historical_market_data"
    _need(manifest["evidence_kind"] == expected, "fixture_authority_mismatch")
    return manifest, registered, finished


def _dataset_binding(store, campaign, registered, finished, dataset_sha, admission_sha):
    dataset = explorer._dataset(store, explorer._ref(dataset_sha))
    request = campaign["request"]
    _need(dataset["evidence_kind"] == "historical_market_data", "event_admission_required")
    admission = validate_admission(store, explorer._ref(admission_sha), dataset_sha)
    _need(not admission.get("policy_revision_sha256"), "fixed_revision_unsupported")
    _need(dataset["market"] == request["market"], "market_mismatch")
    for kind in ("bars", "calendar", "actions"):
        digest = admission["request"][kind + "_receipt_sha256"]
        receipt = store.read_json(digest)
        _, acquired, _ = _registered(store, receipt["submission_id"], digest,
                                     {"alpaca_" + kind}, {"receipt_sha256"})
        _need(acquired > finished, "acquisition_precedes_campaign")
        if not store.access.synthetic:
            _need(datetime.fromisoformat(receipt["started_at"]) >=
                  datetime.fromisoformat(registered["finished_at"]),
                  "acquisition_clock_precedes_campaign")
        if kind == "bars":
            _need(receipt["request"] == request["acquisition_request"], "acquisition_mismatch")
    sessions = dataset["sessions"]
    blocks = []
    for block in request["blocks"]:
        selected = [day for day in sessions if block["start"] <= day <= block["end"]]
        _need(len(selected) >= 2, "insufficient_block_sessions")
        blocks.append({"name": block["name"], "start": selected[0], "end": selected[-1]})
    first = sessions.index(blocks[0]["start"])
    _need(first >= max(c["specification"]["lookback"] for c in request["candidates"]),
          "insufficient_common_warmup")
    # Admission verifies exact provider-calendar agreement before this mapping;
    # no missing bar can be interpreted here as a holiday.
    return {"dataset_sha256": dataset_sha, "admission_sha256": admission_sha,
            "blocks": blocks, "artifact_refs": sorted({dataset_sha, admission_sha,
                dataset["source_sha256"], dataset["bars_sha256"], *admission["artifact_refs"]})}


def bind_dataset(root: Path, request: dict | str) -> dict:
    """Bind one newly acquired, currently admitted event dataset to the intent."""
    with Provenance(root) as store:
        frozen = explorer._envelope(request)
        submission = store.begin("campaign_binding", frozen)
        try:
            _schema(store)
            value = _parse(frozen)
            _need(set(value) == {"campaign_sha256", "dataset_sha256", "admission_sha256"},
                  "invalid_binding_fields")
            campaign, registered, finished = _campaign(store, value["campaign_sha256"])
            data = _dataset_binding(store, campaign, registered, finished,
                                    value["dataset_sha256"], value["admission_sha256"])
            binding = {"schema_version": 1, "kind": "campaign_dataset_binding", **data,
                       "request_sha256": store.put_bytes(frozen.encode()),
                       "campaign_sha256": value["campaign_sha256"]}
            digest = store.put_json(binding)
            with store.journal._transaction():
                store.journal.connection.execute("INSERT INTO research_campaign_bindings VALUES (?,?,?)",
                                                 (value["campaign_sha256"], digest, submission))
                details = {"binding_sha256": digest,
                           "artifact_refs": sorted({digest, value["campaign_sha256"],
                               binding["request_sha256"], *data["artifact_refs"]})}
                store.finish(submission, "success", details)
            return {"submission_id": submission, "status": "success", **details}
        except CampaignError as exc:
            return _fail(store, submission, str(exc))
        except Exception:
            return _fail(store, submission, "campaign_binding_refused")


def _guard(store, campaign_sha, binding_sha):
    campaign, registered, finished = _campaign(store, campaign_sha)
    row = store.journal.connection.execute(
        "SELECT submission_id,binding_sha256 FROM research_campaign_bindings WHERE campaign_sha256=?",
        (campaign_sha,)).fetchone()
    _need(row is not None and row[1] == binding_sha, "unknown_binding")
    record, bound, _ = _registered(store, row[0], binding_sha, {"campaign_binding"}, {"binding_sha256"})
    _need(bound > finished, "binding_order_mismatch")
    binding = store.read_json(binding_sha)
    _need(binding["campaign_sha256"] == campaign_sha, "binding_campaign_mismatch")
    raw = store.read_bytes(binding["request_sha256"])
    _need(hashlib.sha256(raw).hexdigest() == record["request_sha256"]
          and len(raw) == record["request_bytes"] and _parse(raw.decode()) == {
              "campaign_sha256": campaign_sha, "dataset_sha256": binding["dataset_sha256"],
              "admission_sha256": binding["admission_sha256"]}, "binding_request_mismatch")
    expected = _dataset_binding(store, campaign, registered, finished,
                                binding["dataset_sha256"], binding["admission_sha256"])
    _need(all(binding[key] == expected[key] for key in expected), "binding_changed")
    return campaign, binding


def _roster(campaign, binding):
    request = campaign["request"]
    result = []
    for candidate in request["candidates"]:
        for cost in request["cost_bps"]:
            child = {"dataset_sha256": binding["dataset_sha256"],
                     "admission_sha256": binding["admission_sha256"],
                     "study_name": "campaign:" + hash_json(campaign) + ":" + candidate["id"],
                     "result_storage": "bounded_large_json",
                     "evaluation_start": binding["blocks"][0]["start"],
                     "evaluation_end": binding["blocks"][-1]["end"],
                     "specification": {**candidate["specification"], "cost_bps": cost,
                                       "starting_cash": request["starting_cash"]}}
            result.append({"slot": len(result), "candidate_id": candidate["id"],
                           "cost_bps": cost, "request": child, "request_sha256": hash_json(child)})
    return result


def _child(store, result, slot, claim_event, core_identity):
    _need(type(result) is dict, "invalid_child_receipt")
    child = store.get_submission(result.get("submission_id"))
    _need(child["kind"] == "exploratory_study"
          and child["request_sha256"] == slot["request_sha256"]
          and child["request_bytes"] == len(canonical_json(slot["request"]).encode())
          and _position(store, child["submission_id"], "started") > claim_event,
          "child_identity_mismatch")
    _need(child["status"] == result.get("status"), "child_status_mismatch")
    if child["status"] != "success":
        return {"status": child["status"], "child_submission_id": child["submission_id"],
                "error_code": "child_not_successful"}
    _position(store, child["submission_id"], "finished")
    digest = child["details"]["artifact_sha256"]
    _need(result.get("artifact_sha256") == digest, "child_artifact_mismatch")
    artifact = store.read_large_json(digest)
    expected_spec = asdict(StrategySpec(**slot["request"]["specification"]))
    frozen = artifact["frozen_request"]
    _need(artifact["dataset_sha256"] == slot["request"]["dataset_sha256"]
          and artifact["admission_sha256"] == slot["request"]["admission_sha256"]
          and artifact["result_kind"] == "exploratory_result"
          and artifact["investment_evidence"] is False
          and artifact["code_identity"] == core_identity
          and frozen["result_storage"] == "bounded_large_json"
          and frozen["strategy"] == expected_spec
          and all(frozen[k] == slot["request"][k] for k in ("evaluation_start", "evaluation_end")),
          "child_result_mismatch")
    for ref in child["details"]["artifact_refs"]:
        store.read_bytes(ref)
    _need("accounting_policy" in artifact["engine_report"], "event_report_required")
    return {"status": "success", "child_submission_id": child["submission_id"],
            "artifact_sha256": digest, "engine_report": artifact["engine_report"]}


def _selection(outcomes, request):
    rows = [r for r in outcomes if r["cost_bps"] == request["primary_cost_bps"]]
    if any(row["status"] != "success" for row in rows):
        return {"candidate_id": None, "reason": "incomplete_primary_comparison", "criterion": CRITERION}
    eligible = []
    for row in rows:
        block = next(b for b in row["metrics"]["blocks"] if b["name"] == "validation")
        strategy, benchmark = block["strategy"], block["benchmark"]
        growth = Fraction(Decimal(strategy["total_return"]))
        excess = growth - Fraction(Decimal(benchmark["total_return"]))
        if growth > 0 and excess > 0 and Decimal(strategy["max_drawdown"]) <= Decimal(benchmark["max_drawdown"]):
            eligible.append((-excess, strategy["trade_count"], row["candidate_id"]))
    return {"candidate_id": min(eligible)[2] if eligible else None,
            "reason": "validation_screen_selected" if eligible else "no_candidate_meets_rule",
            "criterion": CRITERION, "primary_cost_bps": request["primary_cost_bps"],
            "assessment_used_for_selection": False, "stress_used_for_selection": False}


def _live(deadline):
    _need(time.monotonic() < deadline, "campaign_deadline")


def run_campaign(root: Path, request: dict | str) -> dict:
    """Consume one whole campaign; duplicate requests never retry its slots."""
    deadline = time.monotonic() + MAX_SECONDS
    with Provenance(root) as store:
        frozen = explorer._envelope(request)
        submission = store.begin("campaign_run", frozen)
        try:
            _schema(store)
            value = _parse(frozen)
            _need(set(value) == {"campaign_sha256", "binding_sha256"}, "invalid_run_fields")
            campaign_sha, binding_sha = value["campaign_sha256"], value["binding_sha256"]
            campaign, binding = _guard(store, campaign_sha, binding_sha)
            _live(deadline)
            roster = _roster(campaign, binding)
            roster_sha = store.put_json({"run_id": submission, "slots": roster})
            with store.journal._transaction():
                _live(deadline)
                _need(not store.journal.connection.execute(
                    "SELECT 1 FROM research_campaign_runs WHERE campaign_sha256=?", (campaign_sha,)).fetchone(),
                    "campaign_already_consumed")
                store.journal.connection.execute("INSERT INTO research_campaign_runs VALUES (?,?,?,?)",
                                                 (campaign_sha, submission, binding_sha, roster_sha))
            for slot in roster:
                _live(deadline)
                _guard(store, campaign_sha, binding_sha)
                _live(deadline)
                with store.journal._transaction():
                    _live(deadline)
                    store.journal._event("campaign_slot_claimed", {
                        "run_id": submission, "slot": slot["slot"],
                        "request_sha256": slot["request_sha256"]}, store.journal._now())
                    event = store.journal.connection.execute("SELECT max(id) FROM events").fetchone()[0]
                    store.journal.connection.execute("INSERT INTO research_campaign_claims VALUES (?,?,?,?)",
                                                     (submission, slot["slot"], slot["request_sha256"], event))
                _live(deadline)
                verified_child = None
                try:
                    _live(deadline)
                    reply = explorer.run_submission(root, slot["request"])
                    _live(deadline)
                    outcome = _child(store, reply, slot, event, campaign["code_identity"]["core"])
                    verified_child = outcome["child_submission_id"]
                    _live(deadline)
                    if outcome["status"] == "success":
                        outcome["metrics"] = research_metrics.summarize_trace(
                            outcome.pop("engine_report"), binding["blocks"])
                        _live(deadline)
                        # Existing fake-transport children label their provider-shaped
                        # fixtures historical. The active synthetic authority governs.
                        outcome["metrics"]["evidence_kind"] = campaign["evidence_kind"]
                except CampaignError as exc:
                    outcome = {"status": "interrupted", "child_submission_id": verified_child,
                               "error_code": "campaign_deadline" if str(exc) == "campaign_deadline"
                               else "child_result_unverified"}
                except Exception:
                    outcome = {"status": "interrupted", "child_submission_id": verified_child,
                               "error_code": "child_result_unverified"}
                with store.journal._transaction():
                    store.journal.connection.execute("INSERT INTO research_campaign_results VALUES (?,?,?,?)",
                        (submission, slot["slot"], outcome["child_submission_id"], canonical_json(outcome)))
                _live(deadline)
            _live(deadline)
            with store.journal._transaction():
                _guard(store, campaign_sha, binding_sha)
                _live(deadline)
                outcomes = _outcomes(store, submission, roster)
                all_success = all(row["status"] == "success" for row in outcomes)
                complete = all(row["status"] not in {"pending", "interrupted", "unattempted"}
                               for row in outcomes)
                _live(deadline)
                selection = _selection(outcomes, campaign["request"])
                _live(deadline)
                summary = {"schema_version": 1, "kind": "campaign_development_summary",
                    "campaign_sha256": campaign_sha, "binding_sha256": binding_sha,
                    "run_id": submission, "evidence_kind": campaign["evidence_kind"],
                    "holdout_status": "unprotected_development", "investment_validation": False,
                    "protected_evaluation": False, "all_success": all_success, "complete": complete,
                    "outcomes": outcomes, "selection": selection}
                _live(deadline)
                summary_sha = store.put_json(summary)
                _live(deadline)
                refs = {summary_sha, campaign_sha, binding_sha, roster_sha,
                        *binding["artifact_refs"], *(r["artifact_sha256"] for r in outcomes if "artifact_sha256" in r)}
                details = {"summary_sha256": summary_sha, "all_success": all_success, "complete": complete,
                           "artifact_refs": sorted(refs), "investment_validation": False,
                           "protected_evaluation": False}
                status = "success" if all_success else "failed" if complete else "interrupted"
                _live(deadline)
                store.finish(submission, status, details)
                # finish joins this writer transaction. Expiry during its
                # dependency reads rolls back its success before commit. A
                # written but unregistered content object is not a result.
                _live(deadline)
            return {"submission_id": submission, "status": status, **details}
        except CampaignError as exc:
            return _fail(store, submission, str(exc),
                         "interrupted" if str(exc) == "campaign_deadline" else "invalid")
        except Exception:
            return _fail(store, submission, "campaign_run_refused", "interrupted")


def _outcomes(store, run_id, roster):
    rows = []
    for slot in roster:
        found = store.journal.connection.execute(
            "SELECT outcome FROM research_campaign_results WHERE run_id=? AND slot=?",
            (run_id, slot["slot"])).fetchone()
        claimed = store.journal.connection.execute(
            "SELECT 1 FROM research_campaign_claims WHERE run_id=? AND slot=?",
            (run_id, slot["slot"])).fetchone()
        outcome = json.loads(found[0]) if found else {"status": "interrupted" if claimed else "unattempted"}
        rows.append({"slot": slot["slot"], "candidate_id": slot["candidate_id"],
                     "cost_bps": slot["cost_bps"], **outcome})
    return rows


def inspect_campaign(root: Path, campaign_sha256: str) -> dict:
    """Inspect existing claims/results without starting or resuming a slot."""
    with Provenance(root) as store:
        row = store.journal.connection.execute(
            "SELECT submission_id,roster_sha256,binding_sha256 FROM research_campaign_runs WHERE campaign_sha256=?",
            (explorer._ref(campaign_sha256),)).fetchone()
        _need(row is not None, "campaign_not_started")
        roster = store.read_json(row[1])
        outcomes = _outcomes(store, row[0], roster["slots"])
        current = True
        try:
            _guard(store, campaign_sha256, row[2])
            for outcome in outcomes:
                if outcome.get("artifact_sha256"):
                    store.read_bytes(outcome["artifact_sha256"])
        except Exception:
            current = False
            outcomes = [{key: value for key, value in outcome.items() if key != "metrics"}
                        for outcome in outcomes]
        return {"submission_id": row[0], "status": store.get_submission(row[0])["status"],
                "outcomes": outcomes, "current_evidence_available": current,
                "investment_validation": False, "protected_evaluation": False}

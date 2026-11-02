"""Registered D007 policy changes, preserving refused evidence and prior plans.

Ordering and authorship are claims within cooperating application controls. The
journal hash chain detects ordinary damage, not an owner rewriting all history.
No network, market calculation, or model call occurs here.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

from quanto.ledger import LedgerError, canonical_json, hash_bytes, hash_json
from quanto.provenance import Provenance, ProvenanceError

ACCEPTED_DECISION_SHA256 = "bf8c254645c33550fceb19b794a3aeae933c54d635df149fccda8310f5e987ce"

APPROVED_REVIEWS = {
    "accounting": "f2e6541fef64fe1c3067e0dd9b7f1350a71319618d4482394b14afd025368664",
    "sources": "9a6a797ffcda1634229dbb1e6019fc0e5ad3f810a259f2ba45155b7c75469869",
    "integrity": "57c67a58e9858d8ae7628aed775d802f1e6ad3488976bdeee43c3e56c9604cdf",
    "operations": "055a3a7cd1e6606797043b6e93506993b7dd4d594b3d579fe5a0f784869edb79",
    "scope": "6bc870d5fb72b11dbd1da373ec9b381c50c63ff4c5683d03ef427e4d3a7eade3",
    "fable-cli": "27b75eb526593a579d3858a674cbaabd36b3c9e47c9bfa546ed0434c9dc05139",
    "opus-cli": "3cecb5c8b581d882da536f24449bec833f68b59bb3ac1bf740c5b399eae4fb72",
}

RULES = {"version": "D007-policy-revision-v1", "accepted_decision_sha256": ACCEPTED_DECISION_SHA256,
         "approved_review_sha256s": APPROVED_REVIEWS, "classification": "post_acquisition_development_only",
         "facts": "additive_sources_single_regular_way_split_and_review_independent_schedule",
         "cost_bps": [0, 10, 25], "authorship": "cooperating_owner_not_authenticated"}


class PolicyRevisionError(ValueError):
    """A fixed, safe policy-revision refusal."""


def _need(condition, code):
    if not condition:
        raise PolicyRevisionError(code)


def _equal(left, right):
    return canonical_json(left) == canonical_json(right)


def _ref(value):
    from quanto.explorer import _ref as validate
    return validate(value)


def _position(store, submission_id, phase):
    """Cross-check materialized submission rows against the actual journal."""
    observed = store.get_submission(submission_id)
    kind = "submission_" + phase
    matches = []
    for row in store.journal.connection.execute("SELECT id,payload FROM events WHERE kind=?", (kind,)):
        payload = json.loads(row["payload"])
        if payload.get("submission_id") == submission_id:
            matches.append((row["id"], payload))
    _need(len(matches) == 1, "submission_journal_mismatch")
    position, payload = matches[0]
    if phase == "started":
        expected = {key: observed[key] for key in ("submission_id", "kind", "request_sha256",
                                                  "request_bytes", "request_encoding")}
    else:
        _need(observed["status"] != "pending", "predecessor_pending")
        expected = {"submission_id": submission_id, "status": observed["status"],
                    "details": observed["details"]}
    _need(_equal(payload, expected), "submission_journal_mismatch")
    return position


def _request_bytes(store, submission, digest):
    raw = store.read_bytes(_ref(digest))
    _need(hash_bytes(raw) == submission["request_sha256"]
          and len(raw) == submission["request_bytes"], "predecessor_request_mismatch")
    from quanto.explorer import _request
    return _request(raw.decode("utf-8"))


def _registered(store, submission_id, digest, kinds, fields):
    observed = store.get_submission(submission_id)
    _need(observed["kind"] in kinds and observed["status"] == "success", "predecessor_not_registered")
    details = observed["details"]
    _need(any(details.get(field) == digest for field in fields)
          and digest in details.get("artifact_refs", []), "predecessor_registration_mismatch")
    for ref in details["artifact_refs"]:
        store.read_bytes(_ref(ref))
    start = _position(store, submission_id, "started")
    finish = _position(store, submission_id, "finished")
    _need(start < finish, "predecessor_order_mismatch")
    return observed, start, finish


def _facts_delta(store, previous_digest, current_digest):
    previous = store.read_json(_ref(previous_digest))
    current = store.read_json(_ref(current_digest))
    _need(isinstance(previous, dict) and isinstance(current, dict), "invalid_primary_facts")
    _need("independent_schedule_sha256" not in previous
          and set(current) == set(previous) | {"independent_schedule_sha256"}, "non_additive_primary_facts")
    changes = []
    for key, value in previous.items():
        if key not in {"sources", "events"}:
            _need(_equal(current[key], value), "non_additive_primary_facts")
    before_sources, after_sources = previous.get("sources"), current.get("sources")
    _need(isinstance(before_sources, list) and isinstance(after_sources, list)
          and len(after_sources) >= len(before_sources)
          and _equal(after_sources[:len(before_sources)], before_sources), "non_additive_primary_facts")
    _need(len({hash_json(source) for source in after_sources}) == len(after_sources), "duplicate_primary_source")
    for index in range(len(before_sources), len(after_sources)):
        changes.append({"path": f"$.sources[{index}]", "operation": "add", "value": after_sources[index]})
    before_events, after_events = previous.get("events"), current.get("events")
    _need(isinstance(before_events, list) and isinstance(after_events, list)
          and len(before_events) == len(after_events), "non_additive_primary_facts")
    changed = 0
    for index, (before, after) in enumerate(zip(before_events, after_events)):
        _need(isinstance(before, dict) and isinstance(after, dict), "invalid_primary_event")
        if _equal(before, after):
            continue
        additions = {"regular_way_split", "semantic_review_sha256"}
        _need(not additions & set(before) and set(after) == set(before) | additions
              and all(_equal(after[key], value) for key, value in before.items())
              and before.get("event", {}).get("kind") == "split", "non_additive_primary_facts")
        for key in sorted(additions):
            changes.append({"path": f"$.events[{index}].{key}", "operation": "add", "value": after[key]})
        store.read_bytes(_ref(after["semantic_review_sha256"]))
        changed += 1
    _need(changed == 1, "single_regular_way_split_addition_required")
    store.read_bytes(_ref(current["independent_schedule_sha256"]))
    changes.append({"path": "$.independent_schedule_sha256", "operation": "add",
                    "value": current["independent_schedule_sha256"]})
    from quanto.admission import _sources
    refs = _sources(store, previous) | _sources(store, current)
    refs.update({previous_digest, current_digest, current["independent_schedule_sha256"]})
    refs.update(event["semantic_review_sha256"] for event in after_events if "semantic_review_sha256" in event)
    return changes, refs


FROZEN_FIELDS = (
    "instrument", "data_start", "data_end", "evaluation_start", "evaluation_end", "lookback",
    "starting_cash", "entry_threshold", "exit_threshold", "cost_bps_scenarios", "basis",
    "signal_basis", "dividend_reinvestment", "signal_rule", "sma_includes_current_close",
    "warmup_selection", "buy_quantity", "sell_proceeds", "arithmetic", "benchmark",
    "terminal_policy", "session_order", "dividend_rate_basis", "split_effective_date",
    "same_session_split_and_dividend",
)


def _frozen_study(value):
    from quanto.research import StrategySpec
    from quanto.explorer import _day
    _need(isinstance(value, dict) and set(value) == set(FROZEN_FIELDS)
          and _equal(value["cost_bps_scenarios"], [0, 10, 25]) and value["basis"] == "raw",
          "invalid_frozen_study")
    StrategySpec(**{key: value[key] for key in ("lookback", "starting_cash", "entry_threshold", "exit_threshold")})
    days = [_day(value[field]) for field in ("data_start", "evaluation_start", "evaluation_end", "data_end")]
    _need(days == sorted(days), "invalid_frozen_windows")
    return value


def _plans(store, entries, frozen, refusals, acquisitions):
    _need(isinstance(entries, list) and 2 <= len(entries) <= 16, "complete_predecessor_chain_required")
    plans, refs, previous, seen = [], set(), None, set()
    acquisition_start = min(item["started_event"] for item in acquisitions.values())
    refinement_count = 0
    for entry in entries:
        _need(isinstance(entry, dict) and set(entry) == {"plan_sha256", "submission_id"}, "invalid_plan_reference")
        digest = _ref(entry["plan_sha256"])
        _need(digest not in seen, "cyclic_predecessor_chain")
        seen.add(digest)
        plan = store.read_json(digest)
        _need(isinstance(plan, dict), "invalid_predecessor_plan")
        links = [plan[key] for key in ("previous_plan_bytes_sha256", "previous_plan_sha256") if key in plan]
        _need((not links and previous is None) or len(links) == 1 and links[0] == previous,
              "incomplete_predecessor_chain")
        observed, start, finish = _registered(store, entry["submission_id"], digest,
            {"pilot_plan_registration", "pilot_plan_refinement"}, {"plan_sha256"})
        _need(observed["details"].get("financial_result") is False, "plan_financial_result_must_be_false")
        _need(not plans or plans[-1]["finished_event"] < start, "plan_registration_order_mismatch")
        # Earlier pre-acquisition plans lack later mechanical/accounting detail;
        # every frozen field they do contain must agree with the latest plan.
        _need(all(_equal(plan[key], frozen[key]) for key in FROZEN_FIELDS if key in plan), "predecessor_frozen_fields_changed")
        if start > acquisition_start:
            prior_plan = store.read_json(previous)
            mutable = {"status", "previous_plan_bytes_sha256", "previous_plan_sha256"}
            additions = {"relevance_refined_at", "relevance_refinement"}
            _need(set(plan) - set(prior_plan) <= additions | mutable
                  and set(prior_plan) <= set(plan)
                  and all(_equal(plan[key], value) for key, value in prior_plan.items() if key not in mutable),
                  "non_additive_predecessor_refinement")
            refinement_count += 1
            refinement = plan.get("relevance_refinement", {})
            _need(observed["kind"] == "pilot_plan_refinement"
                  and refinement.get("kind") == "implementation_of_preexisting_structured_exclusion"
                  and refinement.get("original_admission_refusal") == refusals[0]["submission_id"]
                  and refinement.get("facts_sha256") == refusals[-1]["request"]["primary_facts_sha256"]
                  and refinement.get("portfolio_result_observed_before_refinement") is False
                  and refinement.get("strategy_window_costs_unchanged") is True,
                  "invalid_post_acquisition_refinement")
            _need(refusals[0]["finished_event"] < start < finish < refusals[-1]["started_event"],
                  "refinement_refusal_order_mismatch")
        else:
            _need(observed["kind"] == "pilot_plan_registration" and finish < acquisition_start,
                  "plan_acquisition_order_mismatch")
        refs.add(digest)
        refs.update(observed["details"]["artifact_refs"])
        plans.append({**entry, "registration_kind": observed["kind"], "started_event": start,
                      "finished_event": finish, "classification": "post_acquisition_implementation_refinement"
                      if start > acquisition_start else "pre_acquisition_plan"})
        previous = digest
    _need(refinement_count >= 1, "post_acquisition_refinement_required")
    latest = store.read_json(entries[-1]["plan_sha256"])
    _need(all(key in latest and _equal(latest[key], value) for key, value in frozen.items()), "latest_plan_frozen_fields_mismatch")
    return plans, refs


def _refused(store, entries):
    _need(isinstance(entries, list) and 2 <= len(entries) <= 32, "two_prior_refusals_required")
    result, refs = [], set()
    for index, entry in enumerate(entries):
        code = ("identity_change_unresolved" if index == 0 else
                "unsupported_due_bill" if index == len(entries) - 1 else None)
        _need(isinstance(entry, dict) and set(entry) == {"submission_id", "request_sha256"}, "invalid_refusal_reference")
        observed = store.get_submission(entry["submission_id"])
        _need(observed["kind"] == "historical_admission" and observed["status"] == "invalid"
              and isinstance(observed["details"].get("error_code"), str)
              and (code is None or observed["details"].get("error_code") == code), "prior_refusal_outcome_mismatch")
        request = _request_bytes(store, observed, entry["request_sha256"])
        _need(set(request) == {"dataset_sha256", "bars_receipt_sha256", "calendar_receipt_sha256",
                              "actions_receipt_sha256", "primary_facts_sha256", "usage_review_sha256",
                              "submitted_requests"}, "invalid_prior_admission_fields")
        start = _position(store, entry["submission_id"], "started")
        finish = _position(store, entry["submission_id"], "finished")
        _need(start < finish and (not result or result[-1]["finished_event"] < start), "prior_refusal_order_mismatch")
        result.append({**entry, "error_code": observed["details"]["error_code"], "started_event": start, "finished_event": finish,
                       "request": request})
        refs.add(entry["request_sha256"])
        from quanto.admission import _sources
        for field in ("primary_facts_sha256", "usage_review_sha256"):
            ref = _ref(request[field])
            refs.add(ref)
            refs.update(_sources(store, store.read_json(ref)))
    unchanged = set(result[0]["request"]) - {"primary_facts_sha256"}
    _need(all(set(result[0]["request"]) == set(item["request"])
              and all(_equal(result[0]["request"][key], item["request"][key]) for key in unchanged)
              for item in result[1:]), "prior_request_identity_changed")
    return result, refs


def _acquisitions(store, request):
    from quanto.admission import _receipt
    from quanto.explorer import _dataset
    dataset = _dataset(store, _ref(request["dataset_sha256"]))
    refs = {request["dataset_sha256"], dataset["bars_sha256"], dataset["source_sha256"]}
    found = {}
    for kind in ("bars", "calendar", "actions"):
        receipt, _, acquired_refs = _receipt(store, request[kind + "_receipt_sha256"], kind,
                                            request["submitted_requests"][kind])
        start = _position(store, receipt["submission_id"], "started")
        finish = _position(store, receipt["submission_id"], "finished")
        _need(start < finish, "acquisition_order_mismatch")
        refs.update(acquired_refs)
        found[kind] = {"submission_id": receipt["submission_id"], "receipt_sha256": request[kind + "_receipt_sha256"],
                       "submitted_request_sha256": request["submitted_requests"][kind],
                       "normalized_sha256": receipt["normalized_sha256"],
                       "started_event": start, "finished_event": finish}
    for ref in refs:
        store.read_bytes(_ref(ref))
    return dataset, found, refs


def _verify(store, request, *, revision_submission=None):
    """Derive evidence; caller narratives never supply ordering or change count."""
    from quanto.explorer import _code_identity
    required = {"schema_version", "kind", "predecessor_plans", "refused_admissions",
                "accepted_decision_sha256", "review_sha256s", "new_primary_facts_sha256",
                "frozen_study", "classification"}
    _need(set(request) == required and type(request["schema_version"]) is int and request["schema_version"] == 1
          and request["kind"] == "policy_revision_request"
          and request["classification"] == RULES["classification"], "invalid_policy_revision_fields")
    store.journal.verify_events()
    refusals, refs = _refused(store, request["refused_admissions"])
    prior_request = refusals[-1]["request"]
    dataset, acquisitions, acquired_refs = _acquisitions(store, prior_request)
    refs.update(acquired_refs)
    _need(max(item["finished_event"] for item in acquisitions.values()) < refusals[0]["started_event"],
          "refusal_precedes_acquisition")
    frozen = _frozen_study(request["frozen_study"])
    _need(frozen["instrument"] == dataset["symbol"] and frozen["data_start"] == dataset["exposure_start"]
          and frozen["data_end"] == dataset["exposure_end"] and frozen["basis"] == dataset["price_basis"],
          "frozen_dataset_mismatch")
    plans, plan_refs = _plans(store, request["predecessor_plans"], frozen, refusals, acquisitions)
    refs.update(plan_refs)
    delta, fact_refs = _facts_delta(store, prior_request["primary_facts_sha256"], request["new_primary_facts_sha256"])
    refs.update(fact_refs)
    _need(isinstance(request["review_sha256s"], list) and 1 <= len(request["review_sha256s"]) <= 20,
          "policy_review_references_required")
    review_refs = [_ref(value) for value in request["review_sha256s"]]
    _need(len(set(review_refs)) == len(review_refs), "duplicate_policy_review_reference")
    _need(set(APPROVED_REVIEWS.values()) <= set(review_refs), "approved_policy_reviews_required")
    refs.update(review_refs)
    _need(request["accepted_decision_sha256"] == ACCEPTED_DECISION_SHA256, "accepted_decision_mismatch")
    refs.add(_ref(request["accepted_decision_sha256"]))
    for ref in refs:
        _need(bool(store.read_bytes(ref)), "empty_policy_evidence")
    revision_start = _position(store, revision_submission, "started") if revision_submission else None
    if revision_start is not None:
        _need(refusals[-1]["finished_event"] < revision_start
              and plans[-1]["finished_event"] < revision_start, "policy_revision_order_mismatch")
    acquisition_start = min(item["started_event"] for item in acquisitions.values())
    changes = sum(plan["started_event"] > acquisition_start for plan in plans) + 1
    return {"schema_version": 1, "kind": "policy_revision", "request": request,
            "rules": RULES, "code_identity": _code_identity(), "dataset_sha256": prior_request["dataset_sha256"],
            "frozen_study": frozen, "facts_delta": delta,
            "lineage": {"plans": plans, "prior_refusals": refusals, "acquisitions": acquisitions,
                        "post_acquisition_change_count": changes,
                        "current_change": "financial_policy_revision", "classification": RULES["classification"]},
            "artifact_refs": sorted(refs)}


def register_revision(root: Path, request: dict | str) -> dict:
    """Begin before semantic validation; retain safe invalid/interrupted outcomes."""
    from quanto.explorer import _envelope, _request, ExplorationError
    from quanto.admission import AdmissionError
    with Provenance(root) as store:
        frozen = _envelope(request)
        submission = store.begin("policy_revision", frozen)
        publishing = False
        try:
            parsed = _request(frozen)
            result = _verify(store, parsed, revision_submission=submission)
            publishing = True
            request_digest = store.put_bytes(frozen.encode("utf-8"))
            digest = store.put_json(result)
            details = {"policy_revision_sha256": digest, "request_sha256": request_digest,
                       "dataset_sha256": result["dataset_sha256"],
                       "post_acquisition_change_count": result["lineage"]["post_acquisition_change_count"],
                       "artifact_refs": sorted({digest, request_digest, *result["artifact_refs"]})}
            store.finish(submission, "success", details)
            return {"submission_id": submission, "status": "success", **details}
        except (PolicyRevisionError, ExplorationError, AdmissionError) as exc:
            status, code = "invalid", str(exc)
        except (ProvenanceError, LedgerError):
            status, code = ("interrupted", "publication_interrupted") if publishing else ("invalid", "artifact_or_storage_unavailable")
        except (OSError, sqlite3.Error):
            status, code = "interrupted", "storage_interrupted"
        except (ValueError, TypeError, KeyError, ArithmeticError, AttributeError):
            status, code = "invalid", "invalid_policy_revision_evidence"
        try:
            store.finish(submission, status, {"error_code": code, "result_kind": "no_policy_revision"})
        except (OSError, sqlite3.Error, ProvenanceError, LedgerError):
            return {"submission_id": submission, "status": "pending", "error_code": "publication_interrupted"}
        return {"submission_id": submission, "status": status, "error_code": code}


def validate_revision(store: Provenance, digest: str, admission_request: dict | None = None,
                      *, before_submission_id=None) -> dict:
    """Revalidate registered evidence and current disk/loaded-code binding."""
    from quanto.explorer import _request
    revision = store.read_json(_ref(digest))
    candidates = []
    for observed in store.list_submissions(kind="policy_revision", status="success", limit=1000):
        if observed["details"].get("policy_revision_sha256") == digest:
            candidates.append(observed)
    _need(bool(candidates), "policy_revision_not_registered")
    observed = candidates[-1]
    _, _, finished = _registered(store, observed["submission_id"], digest, {"policy_revision"}, {"policy_revision_sha256"})
    raw = store.read_bytes(observed["details"]["request_sha256"])
    _need(hash_bytes(raw) == observed["request_sha256"] and len(raw) == observed["request_bytes"], "policy_revision_request_changed")
    _need(_equal(_request(raw.decode()), revision["request"]), "policy_revision_request_changed")
    if before_submission_id is not None:
        _need(finished < _position(store, before_submission_id, "started"), "policy_revision_must_precede_admission")
    verified = _verify(store, revision["request"], revision_submission=observed["submission_id"])
    _need(_equal(verified, revision), "policy_revision_dependencies_changed")
    if admission_request is not None:
        previous = revision["lineage"]["prior_refusals"][-1]["request"]
        expected = {**previous, "primary_facts_sha256": revision["request"]["new_primary_facts_sha256"],
                    "policy_revision_sha256": digest}
        _need(_equal(admission_request, expected), "policy_revision_admission_mismatch")
    return {**verified, "policy_revision_sha256": digest}


def validate_study(store: Provenance, revision: dict | str, study_request: dict) -> dict:
    """Require frozen dates/specification and one of the three approved costs."""
    if isinstance(revision, str):
        revision = validate_revision(store, revision)
    _need(isinstance(revision, dict) and revision.get("kind") == "policy_revision", "invalid_policy_revision")
    frozen = revision["frozen_study"]
    _need(study_request.get("dataset_sha256") == revision["dataset_sha256"]
          and all(study_request.get(field) == frozen[field] for field in ("evaluation_start", "evaluation_end")),
          "study_outside_frozen_revision")
    specification = study_request.get("specification")
    _need(isinstance(specification, dict), "study_outside_frozen_revision")
    from quanto.research import StrategySpec
    spec = asdict(StrategySpec(**specification))
    cost = spec.pop("cost_bps")
    _need(type(cost) in (int, float) and cost in RULES["cost_bps"]
          and spec == {key: frozen[key] for key in ("lookback", "entry_threshold", "exit_threshold", "starting_cash")}, "study_outside_frozen_revision")
    return revision

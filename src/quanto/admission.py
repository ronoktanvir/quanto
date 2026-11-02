"""Evidence-bound, conditional retrospective admission; no rights/absence certification.

Issuer fact extraction and source-use interpretation are attributed judgments.
Byte/receipt/calendar replay is mechanical; owners of the storage remain trusted.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit

from quanto import alpaca_data as provider
from quanto import alpaca_actions as actions_provider
from quanto.ledger import LedgerError, hash_bytes, hash_json
from quanto.provenance import Provenance, ProvenanceError

RULES = {"version": "D007-admission-v1", "scope": "conditional_retrospective_development",
         "relevance": "full_acquired_interval_ex_effective_and_associated_future_payables",
         "pre_window_cash_merger": "completed_acquirer_only_source_bound_v1",
         "unknown_relevance": "reject", "duplicates": "identical_same_id_only",
         "price_basis": "raw", "currency": "USD", "all_categories": True,
         "regular_way_split": "domestic_integer_forward_split_v1"}
SPLIT_LIMITATIONS = ["economic_packages_not_settled_inventory_or_broker_availability",
                     "redemption_delivery_outcome_unverified",
                     "published_schedule_not_emergency_closure_or_symbol_halt_certificate",
                     "expected_scheduled_trading_not_observed_execution",
                     "attributed_purchaser_entitlement_not_independent_market_observation"]
DATE_FIELDS = {"process_date", "ex_date", "record_date", "payable_date",
               "due_bill_redemption_date", "effective_date"}
SOURCE_ROLES = {"issuer", "finra_11140", "finra_11630", "finra_notice_24_04", "provider_schema"}
ATTRIBUTION_FIELDS = {"source_sha256", "locator", "judgment", "author", "observed_at",
                      "classification", "supporting_sources"}
LIMITATIONS = ["latest_retrieved_revision_not_point_in_time", "vendor_omissions_not_excluded",
               "process_envelope_not_certified_history_floor_or_lag_bound",
               "attributed_issuer_extraction_not_machine_proven", "account_and_exchange_terms_not_certified",
               "development_only_no_protected_holdout", "daily_open_not_certified_executable_fill",
               "fractional_shares_no_cash_in_lieu_taxes_or_settlement_model"]
CATEGORIES = {"reverse_splits", "forward_splits", "unit_splits", "cash_dividends", "stock_dividends",
              "spin_offs", "cash_mergers", "stock_mergers", "stock_and_cash_mergers", "redemptions",
              "name_changes", "worthless_removals", "rights_distributions", "partial_calls",
              "reorganizations", "capital_gains_distributions"}
IDENTITY_EVENTS = {"name_changes", "reorganizations", "cash_mergers", "stock_mergers",
                   "stock_and_cash_mergers", "worthless_removals"}


class AdmissionError(ValueError):
    """Fixed, safe admission refusal."""


def _need(condition, code):
    if not condition:
        raise AdmissionError(code)


def _text(value):
    _need(isinstance(value, str) and bool(value.strip()) and len(value) <= 8000,
          "missing_attributed_judgment")
    return value


def _day(value):
    from quanto.explorer import _day as day
    return day(value).isoformat()


def _ref(value):
    from quanto.explorer import _ref as ref
    return ref(value)


def _decimal(value):
    _need(isinstance(value, str) and 0 < len(value) <= 100
          and re.fullmatch(r"\+?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", value),
          "invalid_action_rate")
    try:
        result = Decimal(value)
        _need(result.is_finite() and result > 0 and abs(result.adjusted()) <= 100,
              "invalid_action_rate")
    except (ValueError, ArithmeticError):
        raise AdmissionError("invalid_action_rate") from None
    return Fraction(result)


def _sources(store, document):
    _text(document.get("reviewer"))
    stamp = datetime.fromisoformat(_text(document.get("reviewed_at")))
    _need(stamp.utcoffset() is not None, "invalid_review_time")
    sources = document.get("sources")
    _need(isinstance(sources, list) and 1 <= len(sources) <= 30, "primary_sources_required")
    refs = set()
    for source in sources:
        digest = _ref(source["sha256"])
        _need(bool(store.read_bytes(digest)), "empty_primary_source")
        url = urlsplit(_text(source["url"]))
        _need(url.scheme == "https" and bool(url.hostname) and not url.username,
              "invalid_primary_source_url")
        _text(source["title"])
        _text(source["locator"])
        refs.add(digest)
        if "receipt_sha256" in source:
            receipt_ref = _ref(source["receipt_sha256"])
            receipt = store.read_json(receipt_ref)
            _need(receipt.get("kind") == "public_source_receipt"
                  and receipt.get("source_sha256") == digest and receipt.get("url") == source["url"],
                  "public_source_receipt_mismatch")
            observed = store.get_submission(receipt["submission_id"])
            _need(observed["status"] == "success" and observed["kind"] == "public_source_observation"
                  and observed["details"].get("receipt_sha256") == receipt_ref
                  and {digest, receipt_ref} <= set(observed["details"].get("artifact_refs", [])),
                  "public_source_receipt_mismatch")
            for ref in observed["details"]["artifact_refs"]:
                store.read_bytes(_ref(ref))
                refs.add(ref)
    return refs


def _judgment(value, sources):
    _need(isinstance(value, dict) and value.get("source_sha256") in sources,
          "unbound_primary_judgment")
    _text(value.get("locator"))
    _text(value.get("judgment"))


def _aware(value):
    try:
        stamp = datetime.fromisoformat(_text(value))
        _need(stamp.utcoffset() is not None, "invalid_review_time")
        return stamp
    except (ValueError, TypeError):
        raise AdmissionError("invalid_review_time") from None


def _attributed(value, sources, *, fields=(), direct=False):
    _need(isinstance(value, dict) and set(value) == ATTRIBUTION_FIELDS | set(fields),
          "invalid_split_judgment")
    _judgment(value, sources)
    _text(value["author"])
    _aware(value["observed_at"])
    _need(value["classification"] in (("direct",) if direct else ("direct", "inferred")),
          "invalid_judgment_classification")
    support = value["supporting_sources"]
    _need(isinstance(support, list) and len(support) <= 20, "invalid_supporting_sources")
    refs = {value["source_sha256"]}
    for item in support:
        _need(isinstance(item, dict) and set(item) == {"source_sha256", "locator"}
              and item["source_sha256"] in sources, "unbound_primary_judgment")
        _text(item["locator"])
        refs.add(item["source_sha256"])
    return refs


def _provider_dates(record):
    """A present null is different from an absent key; never fill source dates."""
    return {name: {"present": name in record, "value": record.get(name)}
            for name in sorted(DATE_FIELDS | {key for key in record if key.endswith("_date")})}


def _annotation_sources(annotation):
    refs = set()
    def visit(value):
        if isinstance(value, dict):
            if "source_sha256" in value:
                refs.add(_ref(value["source_sha256"]))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(annotation)
    roles = annotation.get("source_roles", {})
    _need(isinstance(roles, dict) and set(roles) == SOURCE_ROLES, "split_source_roles_required")
    refs.update(_ref(value) for value in roles.values())
    return refs


def _annotation_authors(value):
    authors = set()
    if isinstance(value, dict):
        if "author" in value:
            authors.add(_text(value["author"]).strip().casefold())
        for child in value.values():
            authors.update(_annotation_authors(child))
    elif isinstance(value, list):
        for child in value:
            authors.update(_annotation_authors(child))
    return authors


def _review_document(store, digest):
    review = store.read_json(_ref(digest))
    fields = {"schema_version", "kind", "annotation_sha256", "author", "reviewer", "reviewer_kind",
              "reviewed_at", "verdict", "reviewed_sources", "reviewed_calendar_sha256", "report_sha256"}
    _need(isinstance(review, dict) and set(review) == fields and review["schema_version"] == 1
          and review["kind"] == "regular_way_split_semantic_review", "invalid_split_semantic_review")
    annotation = store.read_json(_ref(review["annotation_sha256"]))
    _need(hash_json(annotation) == review["annotation_sha256"], "noncanonical_annotation_identity")
    _need(review["author"] == annotation.get("author")
          and _text(review["reviewer"]).strip().casefold() not in _annotation_authors(annotation)
          and review["reviewer_kind"] == "native_agent", "independent_split_reviewer_required")
    _need(_aware(review["reviewed_at"]) >= _aware(annotation.get("observed_at")),
          "semantic_review_precedes_annotation")
    _need(review["verdict"] in ("accepted", "accepted_with_qualifications"), "split_review_not_accepted")
    schedule = store.read_json(_ref(review["reviewed_calendar_sha256"]))
    _need(_aware(review["reviewed_at"]) >= _aware(schedule["review"]["reviewed_at"]),
          "semantic_review_precedes_calendar_review")
    sources = _annotation_sources(annotation) | {_ref(schedule["source_sha256"])}
    _need(review["reviewed_sources"] == sorted(sources), "semantic_review_sources_mismatch")
    _need(bool(store.read_bytes(_ref(review["report_sha256"]))), "empty_semantic_review_report")
    refs = {digest, review["annotation_sha256"], review["reviewed_calendar_sha256"],
            review["report_sha256"], *sources}
    for ref in refs:
        _need(bool(store.read_bytes(ref)), "empty_primary_source")
    return review, refs


def _submission_event(store, submission, kind):
    matches = []
    for row in store.journal.connection.execute("SELECT id,payload FROM events WHERE kind=?", (kind,)):
        value = json.loads(row["payload"])
        if value.get("submission_id") == submission["submission_id"]:
            if kind == "submission_started":
                _need(all(value.get(key) == submission[key] for key in (
                    "kind", "request_sha256", "request_bytes", "request_encoding")),
                    "registration_event_mismatch")
            else:
                _need(value.get("status") == submission["status"]
                      and value.get("details") == submission["details"], "registration_event_mismatch")
            matches.append(row["id"])
    _need(len(matches) == 1, "registration_event_mismatch")
    return matches[0]


def _registered_review(store, digest, *, before_submission_id=None):
    review, refs = _review_document(store, digest)
    store.journal.verify_events()
    rows = store.journal.connection.execute(
        "SELECT s.submission_id,o.details FROM provenance_submissions s JOIN provenance_outcomes o "
        "USING(submission_id) WHERE s.kind='regular_way_split_semantic_review' AND o.status='success'")
    found = []
    before = (_submission_event(store, store.get_submission(before_submission_id), "submission_started")
              if before_submission_id is not None else None)
    for row in rows:
        details = json.loads(row["details"])
        if details.get("review_sha256") != digest:
            continue
        submission = store.get_submission(row["submission_id"])
        started = _submission_event(store, submission, "submission_started")
        finished = _submission_event(store, submission, "submission_finished")
        _need(started < finished, "semantic_review_registration_order")
        if before is not None and finished >= before:
            continue
        raw_ref = _ref(details.get("request_sha256"))
        raw = store.read_bytes(raw_ref)
        _need(hash_bytes(raw) == submission["request_sha256"] and len(raw) == submission["request_bytes"]
              and store.read_json(raw_ref) == {"review_sha256": digest}, "semantic_review_registration_mismatch")
        _need(refs | {raw_ref} <= set(details.get("artifact_refs", [])), "semantic_review_registration_mismatch")
        for ref in details["artifact_refs"]:
            store.read_bytes(_ref(ref))
        found.append(set(details["artifact_refs"]))
    _need(bool(found), "split_semantic_review_not_registered_before_admission")
    return review, refs | set.union(*found)


def register_split_semantic_review(root: Path, request: dict | str) -> dict:
    """Register attributed independent review; this does not grant admission."""
    from quanto.explorer import _envelope, _request, ExplorationError
    with Provenance(root) as store:
        frozen = _envelope(request)
        submission = store.begin("regular_way_split_semantic_review", frozen)
        publishing = False
        try:
            value = _request(frozen)
            _need(set(value) == {"review_sha256"}, "invalid_semantic_review_registration")
            review, refs = _review_document(store, _ref(value["review_sha256"]))
            publishing = True
            raw_ref = store.put_bytes(frozen.encode("utf-8"))
            details = {"review_sha256": value["review_sha256"], "request_sha256": raw_ref,
                       "annotation_sha256": review["annotation_sha256"],
                       "artifact_refs": sorted(refs | {raw_ref})}
            store.finish(submission, "success", details)
            return {"submission_id": submission, "status": "success", **details}
        except (AdmissionError, ExplorationError) as exc:
            status, code = "invalid", str(exc)
        except (ProvenanceError, LedgerError):
            status, code = (("interrupted", "publication_interrupted") if publishing
                            else ("invalid", "artifact_or_storage_unavailable"))
        except (OSError, sqlite3.Error):
            status, code = "interrupted", "storage_interrupted"
        except (ValueError, TypeError, KeyError, ArithmeticError, AttributeError):
            status, code = "invalid", "invalid_semantic_review_evidence"
        try:
            store.finish(submission, status, {"error_code": code, "result_kind": "no_semantic_review"})
        except (OSError, sqlite3.Error, ProvenanceError, LedgerError):
            return {"submission_id": submission, "status": "pending", "error_code": "publication_interrupted"}
        return {"submission_id": submission, "status": status, "error_code": code}


def _independent_schedule(store, digest, sources, start, end, sessions):
    schedule = store.read_json(_ref(digest))
    _need(isinstance(schedule, dict) and set(schedule) == {
        "schema_version", "kind", "exchange", "timezone", "start", "end", "source_sha256",
        "sessions", "early_closes", "extraction", "review"}, "invalid_independent_schedule")
    _need(schedule["schema_version"] == 1 and schedule["kind"] == "independent_exchange_schedule"
          and schedule["timezone"] == "America/New_York" and schedule["start"] == start
          and schedule["end"] == end and schedule["source_sha256"] in sources,
          "independent_schedule_identity_mismatch")
    _text(schedule["exchange"])
    _need(schedule["sessions"] == sessions, "independent_schedule_session_mismatch")
    extraction = schedule["extraction"]
    refs = _attributed(extraction, sources, direct=True)
    _need(extraction["source_sha256"] == schedule["source_sha256"], "unbound_schedule_extraction")
    early = schedule["early_closes"]
    _need(isinstance(early, dict) and set(early) <= set(sessions), "invalid_early_close_metadata")
    for value in early.values():
        _need(isinstance(value, str) and re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value),
              "invalid_early_close_metadata")
    review = schedule["review"]
    _need(isinstance(review, dict) and set(review) == {
        "reviewer", "reviewed_at", "verdict", "report_sha256"}, "independent_schedule_review_required")
    _need(_text(review["reviewer"]).strip().casefold() != extraction["author"].strip().casefold()
          and review["verdict"] == "accepted"
          and _aware(review["reviewed_at"]) >= _aware(extraction["observed_at"]),
          "independent_schedule_review_required")
    report = _ref(review["report_sha256"])
    _need(bool(store.read_bytes(report)), "empty_schedule_review_report")
    refs.update({digest, report})
    return schedule, refs


def _regular_way_split(store, wrapper, annotation, sources, symbol, instrument_id, schedule,
                       schedule_ref, *, before_submission_id=None):
    value, record = annotation["regular_way_split"], wrapper["record"]
    allowed_record = DATE_FIELDS | {"id", "symbol", "new_symbol", "cusip", "isin", "old_cusip",
                                    "new_cusip", "old_isin", "new_isin", "currency", "new_rate", "old_rate"}
    _need(set(record) <= allowed_record, "unsupported_regular_way_provider_fields")
    fields = {"schema_version", "profile", "author", "observed_at", "provider_id", "record_sha256",
              "provider_dates", "source_roles", "issuer_terms", "seller_treatment", "purchaser_entitlement",
              "economic_scope", "rules_applicability", "date_dispositions"}
    _need(isinstance(value, dict) and fields <= set(value) <= fields | {"additional_event_corroboration"}
          and value["schema_version"] == 1
          and value["profile"] == RULES["regular_way_split"], "unsupported_regular_way_profile")
    _text(value["author"])
    observed = _aware(value["observed_at"])
    _need(value["provider_id"] == record["id"] and value["record_sha256"] == hash_json(record)
          and hash_json(value["provider_dates"]) == hash_json(_provider_dates(record)), "regular_way_record_mismatch")
    refs = _annotation_sources(value)
    _need(refs <= sources, "unbound_primary_judgment")
    roles = value["source_roles"]
    additional = value.get("additional_event_corroboration", [])
    _need(isinstance(additional, list) and len(additional) <= 5, "invalid_additional_event_corroboration")
    for judgment in additional:
        _attributed(judgment, sources, direct=True)
        _need(_aware(judgment["observed_at"]) <= observed, "split_annotation_attribution_mismatch")
    terms = value["issuer_terms"]
    term_fields = {"symbol", "instrument_id", "security_type", "new_rate", "old_rate", "record_date",
                   "distribution_date", "distribution_timing", "first_adjusted_session", "trading_statement"}
    _attributed(terms, sources, fields=term_fields, direct=True)
    _need(terms["source_sha256"] == roles["issuer"] and terms["symbol"] == symbol
          and terms["instrument_id"] == instrument_id and terms["security_type"] == "domestic_common_stock",
          "regular_way_identity_conflict")
    ratio = _decimal(record["new_rate"]) / _decimal(record["old_rate"])
    expected = annotation["event"]
    _need(wrapper["category"] == "forward_splits" and ratio.denominator == 1 and ratio >= 2,
          "unsupported_regular_way_ratio")
    _need(_decimal(terms["new_rate"]) / _decimal(terms["old_rate"]) == ratio
          and expected["new_rate"] == terms["new_rate"] and expected["old_rate"] == terms["old_rate"],
          "issuer_split_conflict")
    record_date, distribution, effective = (_day(terms[name]) for name in (
        "record_date", "distribution_date", "first_adjusted_session"))
    _need(effective == record["ex_date"] == expected["effective_date"]
          and record.get("due_bill_redemption_date") == effective, "regular_way_date_shape_mismatch")
    _need(record_date <= distribution < effective and terms["distribution_timing"] == "after_close"
          and terms["trading_statement"] == "expected_or_scheduled", "unsupported_regular_way_terms")
    sessions = schedule["sessions"]
    _need(distribution in sessions and effective in sessions
          and sessions.index(effective) == sessions.index(distribution) + 1,
          "split_distribution_not_adjacent_session")
    for key, flag in (("seller_treatment", "transfers_attached_interest"),
                      ("purchaser_entitlement", "receives_attached_interest")):
        judgment = value[key]
        support = _attributed(judgment, sources, fields={flag}, direct=key == "seller_treatment")
        _need(judgment[flag] is True and roles["issuer"] in support, "unresolved_split_entitlement")
        if key == "purchaser_entitlement" and judgment["classification"] == "inferred":
            _need({roles["finra_11140"], roles["finra_11630"]} <= support,
                  "unbound_purchaser_inference")
    scope = value["economic_scope"]
    flags = {"same_security_and_market": True, "separate_entitlement_market": False,
             "additional_claims_or_cash": False, "elections": False, "fractional_cash_in_lieu": False}
    scope_refs = _attributed(scope, sources, fields=flags)
    _need(roles["issuer"] in scope_refs and all(scope[key] is flag for key, flag in flags.items()),
          "unsupported_split_economic_terms")
    applicability = value["rules_applicability"]
    rule_refs = _attributed(applicability, sources, fields={"regime_start"})
    _need(applicability["regime_start"] == "2024-05-28" and distribution >= "2024-05-28"
          and {roles["finra_11140"], roles["finra_11630"], roles["finra_notice_24_04"]} <= rule_refs,
          "unsupported_split_rule_regime")
    dispositions = value["date_dispositions"]
    _need(isinstance(dispositions, dict) and set(dispositions) == {
        "record_date", "payable_date", "due_bill_redemption_date"}, "split_date_dispositions_required")
    for field, item in dispositions.items():
        extras = {"status", "controlling_terms_established", "explanation"}
        if field == "due_bill_redemption_date":
            extras |= {"documented_meaning", "actual_outcome", "transformation_trigger"}
        item_refs = _attributed(item, sources, fields=extras)
        _need(item["controlling_terms_established"] is True and roles["issuer"] in item_refs,
              "unresolved_controlling_split_terms")
        _text(item["explanation"])
        if field == "due_bill_redemption_date":
            expected_status = "unresolved_ancillary_date_discrepancy"
            _need(roles["provider_schema"] in item_refs and item["documented_meaning"] == "delivery_obligations"
                  and item["actual_outcome"] == "unverified"
                  and item["transformation_trigger"] == "issuer_first_adjusted_session",
                  "unresolved_redemption_disposition")
        else:
            issuer_date = record_date if field == "record_date" else distribution
            expected_status = ("matches_issuer_date" if record.get(field) == issuer_date
                               else "unresolved_ancillary_date_discrepancy")
        _need(item["status"] == expected_status, "ancillary_discrepancy_hidden")
    for key in ("issuer_terms", "seller_treatment", "purchaser_entitlement", "economic_scope", "rules_applicability"):
        _need(_aware(value[key]["observed_at"]) <= observed,
              "split_annotation_attribution_mismatch")
    for item in dispositions.values():
        _need(_aware(item["observed_at"]) <= observed,
              "split_annotation_attribution_mismatch")
    review_ref = _ref(annotation.get("semantic_review_sha256"))
    review, review_refs = _registered_review(store, review_ref, before_submission_id=before_submission_id)
    _need(review["annotation_sha256"] == hash_json(value)
          and review["reviewed_calendar_sha256"] == schedule_ref, "semantic_review_annotation_mismatch")
    refs.update(review_refs)
    return {"profile": value["profile"], "provider_id": record["id"], "annotation": value,
            "annotation_sha256": hash_json(value), "provider_record": record,
            "record_sha256": hash_json(record), "occurrences": wrapper["occurrences"],
            "ratio": str(ratio.numerator), "semantic_review_sha256": review_ref,
            "independent_schedule_sha256": schedule_ref, "date_dispositions": dispositions,
            "additional_event_corroboration_status": "retained_attributed" if additional else "not_supplied",
            "limitations": SPLIT_LIMITATIONS}, refs


def _receipt(store, digest, kind, submitted):
    receipt = store.read_json(_ref(digest))
    _need(receipt.get("provider") == "alpaca" and receipt.get("kind") == kind
          and receipt.get("status") == "success" and receipt.get("schema_version") == 1
          and receipt.get("evidence_kind") == "historical_market_data", "invalid_acquisition_receipt")
    submission = store.get_submission(receipt["submission_id"])
    _need(submission["status"] == "success" and submission["kind"] == "alpaca_" + kind
          and submission["details"].get("receipt_sha256") == digest,
          "receipt_submission_mismatch")
    raw_request = store.read_bytes(_ref(submitted))
    _need(hash_bytes(raw_request) == submission["request_sha256"]
          and len(raw_request) == submission["request_bytes"], "receipt_submission_mismatch")
    now = datetime.fromisoformat(receipt["started_at"])
    request = (actions_provider._request(raw_request.decode("utf-8"), now) if kind == "actions"
               else provider._request(raw_request.decode("utf-8"), kind, now))
    url = (lambda token=None: actions_provider._url(request, token)) if kind == "actions" else (
        lambda token=None: provider._url(request, kind, token))
    _need(request == receipt["request"], "receipt_request_mismatch")
    prepared = store.read_json(_ref(receipt["request_sha256"]))
    page_cap = 1 if kind == "calendar" else provider.MAX_PAGES
    expected_prepared = {"method": "GET", "request": request, "url": url(),
                         "max_pages": page_cap, "max_total_bytes": provider.MAX_TOTAL_BYTES,
                         "max_total_seconds": provider.MAX_TOTAL_SECONDS}
    if kind == "actions":
        expected_prepared.update(max_page_bytes=provider.MAX_PAGE_BYTES,
                                 min_request_interval=provider.MIN_REQUEST_INTERVAL,
                                 all_categories=True, date_semantics="process_date_envelope")
        _need(receipt.get("pagination_complete") is True
              and receipt.get("normalization_status") == "complete", "acquisition_incomplete")
    _need(prepared == expected_prepared, "request_parameters_mismatch")
    pages = receipt.get("pages")
    _need(isinstance(pages, list) and 1 <= len(pages) <= page_cap, "acquisition_incomplete")
    refs = {digest, submitted, receipt["request_sha256"], receipt["normalized_sha256"]}
    rows, token, total, seen = [], None, 0, set()
    for index, page in enumerate(pages):
        _need(page["page"] == index + 1 and page["http_status"] == 200
              and page["url"] == url(token), "page_request_mismatch")
        raw = store.read_bytes(_ref(page["raw_sha256"]))
        refs.add(page["raw_sha256"])
        total += len(raw)
        _need(page["bytes"] == len(raw) and len(raw) <= provider.MAX_PAGE_BYTES
              and total <= provider.MAX_TOTAL_BYTES, "acquisition_cap_exceeded")
        if kind == "actions":
            body = actions_provider._json(raw)
            page_rows, _, _ = actions_provider._page(body, page["raw_sha256"], index + 1)
            rows.extend(page_rows)
        else:
            body = provider._json(raw)
            if kind == "calendar":
                rows = provider._calendar(body, request)
            else:
                _need(body.get("symbol") == request["symbol"] and isinstance(body.get("bars"), list),
                      "source_replay_mismatch")
                rows.extend(provider._bar(row, request) for row in body["bars"])
        if kind != "calendar":
            _need("next_page_token" in body, "acquisition_incomplete")
            token = body["next_page_token"]
            if token is not None:
                _need(isinstance(token, str) and provider.TOKEN.fullmatch(token)
                      and token not in seen and index < len(pages) - 1, "acquisition_incomplete")
                seen.add(token)
            else:
                _need(index == len(pages) - 1, "pagination_extra_pages")
    _need(token is None and len(rows) <= provider.MAX_BARS, "acquisition_incomplete")
    normalized = store.read_json(_ref(receipt["normalized_sha256"]))
    field = {"bars": "bars", "calendar": "sessions", "actions": "records"}[kind]
    _need(normalized.get(field) == rows and receipt["row_count"] == len(rows), "source_replay_mismatch")
    coverage = normalized.get("coverage", {})
    _need(coverage.get("pagination_complete") is True
          and coverage.get("requested_start") == request["start"]
          and coverage.get("requested_end") == request["end"], "source_coverage_mismatch")
    _need(normalized.get("schema_version") == 1
          and normalized.get("evidence_kind") == "historical_market_data"
          and normalized.get("research_eligible") is False
          and normalized.get("admission_status") == "inspection_only"
          and normalized.get("kind") == {"bars": "daily_bars", "calendar": "exchange_calendar",
                                          "actions": "corporate_actions"}[kind], "source_metadata_mismatch")
    _need(refs - {submitted} <= set(submission["details"]["artifact_refs"]), "receipt_refs_mismatch")
    for ref in submission["details"]["artifact_refs"]:
        store.read_bytes(_ref(ref))
    return receipt, normalized, refs



def _excluded_cash_merger(wrapper, annotation, sources, symbol, start, identifiers):
    """Exclude only source-corroborated, completed historical purchases by issuer.

    This does not grant accounting support for mergers. Completion and absence
    of conversion/entitlement are attributed issuer judgments, never inferred
    from provider process dates or a caller's unbound approval flag.
    """
    record = wrapper["record"]
    fields = {"id", "acquirer_symbol", "acquiree_symbol", "acquirer_cusip", "acquiree_cusip",
              "acquirer_isin", "acquiree_isin", "process_date", "effective_date", "payable_date",
              "rate", "currency"}
    _need(set(record) <= fields, "unsupported_cash_merger_fields")
    _need(wrapper["category"] == "cash_mergers", "unsupported_action_exclusion")
    _need(set(annotation) == {"provider_id", "category", "record_sha256", "effective_date",
                              "acquirer", "acquiree", "source_sha256", "locator", "judgment", "completion"},
          "invalid_action_exclusion")
    _judgment(annotation, sources)
    _need(annotation["provider_id"] == record["id"]
          and annotation["category"] == "cash_mergers"
          and _ref(annotation["record_sha256"]) == hash_json(record), "excluded_record_mismatch")
    effective = _day(record.get("effective_date"))
    _need(effective == annotation["effective_date"] and effective < start,
          "excluded_event_not_before_acquired_interval")
    _day(record.get("process_date"))
    _decimal(record.get("rate"))
    currency = record.get("currency")
    _need(currency in (None, "") or isinstance(currency, str)
          and len(currency) == 3 and currency.isascii() and currency.isupper() and currency.isalpha(),
          "invalid_excluded_merger_currency")
    acquirer, acquiree = {}, {}
    for role, target in (("acquirer", acquirer), ("acquiree", acquiree)):
        role_symbol = record.get(role + "_symbol")
        _need(isinstance(role_symbol, str) and provider.SYMBOL.fullmatch(role_symbol),
              "excluded_merger_identity_unresolved")
        target["symbol"] = role_symbol
        for identifier in ("cusip", "isin"):
            value = record.get(role + "_" + identifier)
            _need(value is None or isinstance(value, str) and bool(value.strip()),
                  "excluded_merger_identity_unresolved")
            target[identifier] = value
        _need(annotation[role] == target, "excluded_merger_role_mismatch")
    _need(acquirer["symbol"] == symbol and acquiree["symbol"] != symbol,
          "excluded_merger_role_mismatch")
    _need(acquiree["cusip"] is not None, "excluded_acquiree_identity_unresolved")
    matched = False
    for identifier, observed in identifiers.items():
        own, other = acquirer[identifier], acquiree[identifier]
        if own is not None:
            _need(observed == {own}, "excluded_acquirer_identifier_unresolved")
            matched = True
        if other is not None:
            _need(other != own and other not in observed, "excluded_acquiree_identifier_conflict")
    _need(matched, "excluded_acquirer_identifier_unresolved")
    completion = annotation["completion"]
    _need(isinstance(completion, dict) and set(completion) == {
        "date", "source_sha256", "locator", "judgment", "no_studied_share_conversion",
        "no_outstanding_studied_entitlement"}, "invalid_merger_completion_judgment")
    _judgment(completion, sources)
    completed = _day(completion["date"])
    _need(effective <= completed < start and completion["no_studied_share_conversion"] is True
          and completion["no_outstanding_studied_entitlement"] is True,
          "unresolved_merger_completion")
    payable = record.get("payable_date")
    if payable not in (None, ""):
        _need(effective <= _day(payable) <= completed and payable < start,
              "unresolved_merger_payment")
    # Unknown payment timing is excluded only under the explicit retained
    # completion/no-outstanding-entitlement judgment above.
    return {"reason": "completed_pre_window_acquirer_cash_merger",
            "annotation": annotation, "record_sha256": hash_json(record),
            "occurrences": wrapper["occurrences"]}

def _actions(records, facts, sources, symbol, start, end, sessions, *, store=None, schedule=None,
             schedule_ref=None, instrument_id=None, before_submission_id=None):
    annotations = facts.get("events")
    _need(isinstance(annotations, list), "primary_event_facts_required")
    by_id = {}
    for annotation in annotations:
        _judgment(annotation, sources)
        identity = _text(annotation.get("provider_id"))
        _need(identity not in by_id, "duplicate_primary_annotation")
        by_id[identity] = annotation
    exclusions = facts.get("excluded_actions", [])
    _need(isinstance(exclusions, list), "invalid_action_exclusions")
    exclusion_by_id = {}
    for annotation in exclusions:
        _judgment(annotation, sources)
        event_id = _text(annotation.get("provider_id"))
        _need(event_id not in exclusion_by_id and event_id not in by_id,
              "duplicate_or_conflicting_action_annotation")
        exclusion_by_id[event_id] = annotation
    # Check the entire source corpus for duplicate conflicts before applying any
    # exclusion; retain every exact duplicate occurrence in the grouped record.
    unique = {}
    for wrapper in records:
        category, record = wrapper["category"], wrapper["record"]
        event_id = _text(record.get("id"))
        key = hash_json({"category": category, "record": record})
        if event_id in unique:
            _need(unique[event_id][0] == key, "conflicting_same_id_actions")
            unique[event_id][1]["occurrences"].extend(wrapper["occurrences"])
        else:
            unique[event_id] = (key, {"category": category, "record": record,
                                     "occurrences": list(wrapper["occurrences"])})
    event_keys, events, used, deferred, excluded = set(), [], set(), [], []
    treatments, treatment_refs = [], set()
    identifiers = {"cusip": set(), "isin": set()}
    for _, wrapper in unique.values():
        category, record = wrapper["category"], wrapper["record"]
        event_id = record["id"]
        _need(category in CATEGORIES, "unknown_action_category")
        if event_id in exclusion_by_id:
            _need(category == "cash_mergers", "unsupported_action_exclusion")
            deferred.append(wrapper)
            continue
        _need(category not in IDENTITY_EVENTS, "identity_change_unresolved")
        ex_date = _day(record.get("ex_date"))
        _need(record.get("symbol") == symbol and record.get("new_symbol") in (None, "", symbol),
              "action_identity_mismatch")
        if not start <= ex_date <= end:
            continue
        _need(ex_date in sessions, "action_date_not_session")
        _need(category in ("forward_splits", "reverse_splits", "cash_dividends"),
              "unsupported_relevant_action")
        _day(record.get("process_date"))
        for name, value in record.items():
            if name.endswith("_date") and value not in (None, ""):
                _day(value)
        _need(category == "cash_dividends" or record.get("currency") in (None, "", "USD"),
              "action_currency_conflict")
        for identifier, observed in identifiers.items():
            for name in (identifier, "old_" + identifier, "new_" + identifier):
                if record.get(name):
                    observed.add(_text(record[name]))
            _need(len(observed) <= 1, "action_security_identifier_conflict")
        _need(category in ("forward_splits", "reverse_splits", "cash_dividends"),
              "unsupported_relevant_action")
        _need(event_id in by_id, "primary_event_corroboration_required")
        annotation = by_id[event_id]
        used.add(event_id)
        expected = annotation["event"]
        if category in ("forward_splits", "reverse_splits"):
            new, old = _decimal(record.get("new_rate")), _decimal(record.get("old_rate"))
            _need(new != old and (new > old if category == "forward_splits" else new < old),
                  "split_direction_mismatch")
            event = {"kind": "split", "event_id": event_id, "effective_date": ex_date,
                     "new_rate": record["new_rate"], "old_rate": record["old_rate"]}
            _need(expected.get("kind") == "split" and expected.get("event_id") == event_id
                  and expected.get("effective_date") == ex_date
                  and set(expected) == set(event), "issuer_split_conflict")
            if "regular_way_split" in annotation:
                _need(store is not None and schedule is not None, "regular_way_evidence_required")
                treatment, found = _regular_way_split(
                    store, wrapper, annotation, sources, symbol, instrument_id, schedule, schedule_ref,
                    before_submission_id=before_submission_id)
                treatments.append(treatment)
                treatment_refs.update(found)
            else:
                _need(not record.get("due_bill_redemption_date"), "unsupported_due_bill")
                _need("semantic_review_sha256" not in annotation, "unmatched_semantic_review")
                _need(_decimal(expected.get("new_rate")) == new
                      and _decimal(expected.get("old_rate")) == old, "issuer_split_conflict")
            event = dict(expected)
        else:
            _need("regular_way_split" not in annotation and "semantic_review_sha256" not in annotation,
                  "unsupported_regular_way_profile")
            _need(record.get("special") is False and record.get("foreign") is False
                  and record.get("sub_type") in (None, "", "ordinary")
                  and not record.get("due_bill_on_date") and not record.get("due_bill_off_date"),
                  "unsupported_dividend_terms")
            payable = _day(record.get("payable_date"))
            _need(payable >= ex_date, "invalid_dividend_dates")
            _need(record.get("currency") in (None, "", "USD") and expected.get("currency") == "USD",
                  "unresolved_dividend_currency")
            rate = _decimal(record.get("rate"))
            issuer_rate = _decimal(expected.get("rate"))
            basis = annotation.get("provider_rate_basis")
            if basis == "pre_split_shares":
                split_id = annotation.get("conversion_split_event_id")
                split = by_id.get(split_id, {}).get("event", {})
                _need(split.get("kind") == "split" and split.get("effective_date", "9999") <= ex_date,
                      "unresolved_dividend_rate_basis")
                rate *= _decimal(split.get("old_rate")) / _decimal(split.get("new_rate"))
            else:
                _need(basis == "ex_date_shares", "unresolved_dividend_rate_basis")
            _need(rate == issuer_rate, "issuer_dividend_rate_conflict")
            event = {"kind": "cash_dividend", "event_id": event_id, "ex_date": ex_date,
                     "payable_date": payable, "rate": expected["rate"], "currency": "USD",
                     "share_basis": "ex_date_shares"}
            _need(expected == event, "issuer_dividend_terms_conflict")
        economic = hash_json({key: value for key, value in event.items() if key != "event_id"})
        _need(economic not in event_keys, "ambiguous_multiple_ids_same_event")
        event_keys.add(economic)
        events.append(event)
    _need({wrapper["record"]["id"] for wrapper in deferred} == set(exclusion_by_id),
          "unmatched_action_exclusions")
    excluded_keys = set()
    for wrapper in deferred:
        record = wrapper["record"]
        result = _excluded_cash_merger(wrapper, exclusion_by_id[record["id"]], sources,
                                       symbol, start, identifiers)
        economic = hash_json({key: record[key] for key in (
            "effective_date", "acquirer_symbol", "acquiree_symbol")})
        _need(economic not in excluded_keys, "ambiguous_multiple_ids_same_event")
        excluded_keys.add(economic)
        excluded.append(result)
    _need(set(by_id) == used, "unmatched_primary_events")
    _need(all(annotation.get("conversion_split_event_id") in used for annotation in annotations
              if annotation.get("provider_rate_basis") == "pre_split_shares"),
          "unmatched_conversion_split")
    dates = {}
    for event in events:
        day = event.get("effective_date", event.get("ex_date"))
        _need(day not in dates, "unsupported_coincident_actions")
        dates[day] = event["kind"]
    return (sorted(events, key=lambda event: (event.get("effective_date", event.get("ex_date")), event["event_id"])),
            sorted(excluded, key=lambda item: item["annotation"]["provider_id"]),
            sorted(treatments, key=lambda item: item["provider_id"]), treatment_refs)


def _verify(store, request, *, before_submission_id=None):
    from quanto.explorer import _dataset, _bars, _bar_json, _code_identity
    required = {"dataset_sha256", "bars_receipt_sha256", "calendar_receipt_sha256",
                "actions_receipt_sha256", "primary_facts_sha256", "usage_review_sha256", "submitted_requests"}
    _need(required <= set(request) <= required | {"policy_revision_sha256"}
          and set(request["submitted_requests"]) == {"bars", "calendar", "actions"},
          "invalid_admission_fields")
    dataset = _dataset(store, _ref(request["dataset_sha256"]))
    _need(dataset["evidence_kind"] == "historical_market_data" and dataset["price_basis"] == "raw"
          and dataset["admission_status"] == "inspection_only", "historical_raw_dataset_required")
    receipts, normalized, refs = {}, {}, {request["dataset_sha256"], dataset["bars_sha256"], dataset["source_sha256"]}
    for kind in ("bars", "calendar", "actions"):
        receipts[kind], normalized[kind], found = _receipt(
            store, request[kind + "_receipt_sha256"], kind, request["submitted_requests"][kind])
        refs.update(found)
    bar_source, calendar, action_source = normalized["bars"], normalized["calendar"], normalized["actions"]
    bar_request = receipts["bars"]["request"]
    start, end, symbol = bar_request["start"], bar_request["end"], bar_request["symbol"]
    _need(bar_request == {"start": start, "end": end, "symbol": symbol, "adjustment": "raw", **provider.BAR_FIXED}
          and bar_source.get("price_basis") == "raw", "raw_request_required")
    _need(dataset["source_sha256"] == receipts["bars"]["normalized_sha256"], "dataset_receipt_mismatch")
    market = dataset["market"]
    _need(market["currency"] == "USD" and market["session_timezone"] == "America/New_York",
          "unsupported_market_identity")
    identity = bar_source.get("identity", {})
    _need(identity == {"provider": "alpaca", "asset_class": "us_equity", "session_timezone": "America/New_York",
                       "symbol": symbol, "feed": "sip", "currency": "USD",
                       "symbol_mapping": "disabled_asof_dash", "stable_entity_id": None}, "source_identity_mismatch")
    _need(action_source.get("identity", {}).get("provider") == "alpaca"
          and action_source["identity"].get("symbol") == symbol
          and action_source["identity"].get("asset_class") == "us_equity", "source_identity_mismatch")
    _need(receipts["calendar"]["request"] == {"start": start, "end": end}, "calendar_interval_mismatch")
    _need(calendar.get("identity") == {"provider": "alpaca", "asset_class": "us_equity",
                                      "session_timezone": "America/New_York"}, "calendar_identity_mismatch")
    bars = _bars(bar_source, market)
    sessions = [bar.timestamp.date().isoformat() for bar in bars]
    _need([row["date"] for row in calendar["sessions"]] == sessions == dataset["sessions"], "calendar_session_mismatch")
    _need(store.read_json(dataset["bars_sha256"]) == _bar_json(bars)
          and dataset["bar_count"] == len(bars) and dataset["symbol"] == symbol
          and dataset["exposure_start"] == start and dataset["exposure_end"] == end
          and dataset["coverage_start"] == sessions[0] and dataset["coverage_end"] == sessions[-1],
          "dataset_coverage_mismatch")
    action_request = receipts["actions"]["request"]
    _need(action_request["symbol"] == symbol and action_request["start"] == "2016-01-01"
          and action_request["end"] == datetime.fromisoformat(receipts["actions"]["started_at"]).date().isoformat()
          and action_request["end"] >= end and action_request.get("region") == "us"
          and action_request.get("data_quality") == "all" and action_request.get("sort") == "asc"
          and action_request.get("limit") == provider.PAGE_LIMIT and "types" not in action_request,
          "action_envelope_mismatch")
    facts = store.read_json(_ref(request["primary_facts_sha256"]))
    usage = store.read_json(_ref(request["usage_review_sha256"]))
    _need(facts.get("schema_version") == 1 and facts.get("kind") == "attributed_primary_facts",
          "invalid_primary_facts")
    primary_sources = _sources(store, facts)
    primary_documents = {source["sha256"] for source in facts["sources"]}
    ident = facts.get("identity", {})
    _judgment(ident, primary_documents)
    _need(ident.get("symbol") == symbol and ident.get("instrument_id") == market["instrument_id"]
          and ident.get("currency") == "USD" and _day(ident.get("continuity_start")) <= start
          and _day(ident.get("continuity_end")) >= end, "issuer_identity_mismatch")
    _text(ident.get("issuer_name"))
    coverage = facts.get("coverage", {})
    _judgment(coverage, primary_documents)
    _need(coverage.get("start") == start and coverage.get("end") == end, "issuer_coverage_mismatch")
    new_profile = any("regular_way_split" in event for event in facts.get("events", []))
    schedule, schedule_ref, revision = None, None, None
    if new_profile:
        _need("policy_revision_sha256" in request, "regular_way_policy_revision_required")
        schedule_ref = _ref(facts.get("independent_schedule_sha256"))
        schedule, schedule_refs = _independent_schedule(
            store, schedule_ref, primary_documents, start, end, sessions)
        refs.update(schedule_refs)
        receipt_sources = {source["sha256"] for source in facts["sources"] if "receipt_sha256" in source}
        required_sources = {schedule["source_sha256"]}
        for event in facts["events"]:
            if "regular_way_split" in event:
                required_sources.update(_annotation_sources(event["regular_way_split"]))
        _need(required_sources <= receipt_sources, "regular_way_source_receipts_required")
    events, exclusions, treatments, treatment_refs = _actions(
        action_source["records"], facts, primary_documents, symbol, start, end, sessions,
        store=store, schedule=schedule, schedule_ref=schedule_ref,
        instrument_id=market["instrument_id"], before_submission_id=before_submission_id)
    refs.update(treatment_refs)
    _need(isinstance(coverage.get("known_events"), list)
          and sorted(coverage["known_events"], key=hash_json) == sorted(events, key=hash_json),
          "known_issuer_events_unmatched")
    _need(usage.get("schema_version") == 1 and usage.get("kind") == "source_use_review"
          and usage.get("purpose") == "private_own_account_research"
          and usage.get("public_distribution") is False and usage.get("external_model_transmission") is False,
          "unsupported_source_use")
    usage_sources = _sources(store, usage)
    _text(usage.get("interpretation"))
    _need(isinstance(usage.get("unresolved"), list)
          and "account_and_exchange_terms_not_certified" in usage["unresolved"], "source_use_limitations_required")
    refs.update(primary_sources | usage_sources | {request["primary_facts_sha256"], request["usage_review_sha256"]})
    if "policy_revision_sha256" in request:
        from quanto.policy_revision import validate_revision, PolicyRevisionError
        try:
            revision = validate_revision(store, _ref(request["policy_revision_sha256"]), request,
                                         before_submission_id=before_submission_id)
        except PolicyRevisionError as exc:
            raise AdmissionError(str(exc)) from None
        refs.update(revision["artifact_refs"])
        refs.add(request["policy_revision_sha256"])
    result = {"schema_version": 1, "kind": "historical_admission", "request": request,
            "dataset_sha256": request["dataset_sha256"], "scope": RULES["scope"], "rules": RULES,
            "code_identity": _code_identity(), "actions": events, "excluded_actions": exclusions, "sessions": sessions,
            "accepted_action_treatments": treatments,
            "full_acquired_exposure": {"start": start, "end": end}, "market": market,
            "request_parameters_sha256": hash_json({kind: receipts[kind]["request"] for kind in receipts}),
            "limitations": LIMITATIONS + (SPLIT_LIMITATIONS if treatments else []), "artifact_refs": sorted(refs)}
    if revision is not None:
        result.update(policy_revision_sha256=request["policy_revision_sha256"], policy_revision=revision)
    return result


def admit_dataset(root: Path, request: dict | str) -> dict:
    from quanto.explorer import _envelope, _request, _schema, ExplorationError
    with Provenance(root) as store:
        _schema(store)
        frozen = _envelope(request)
        submission = store.begin("historical_admission", frozen)
        publishing = False
        try:
            result = _verify(store, _request(frozen), before_submission_id=submission)
            publishing = True
            digest = store.put_json(result)
            details = {"admission_sha256": digest, "dataset_sha256": result["dataset_sha256"],
                       "scope": result["scope"], "artifact_refs": sorted({digest, *result["artifact_refs"]})}
            store.finish(submission, "success", details)
            return {"submission_id": submission, "status": "success", **details}
        except (AdmissionError, ExplorationError) as exc:
            status, code = "invalid", str(exc)
        except (ProvenanceError, LedgerError):
            status, code = ("interrupted", "publication_interrupted") if publishing else ("invalid", "artifact_or_storage_unavailable")
        except (OSError, sqlite3.Error):
            status, code = "interrupted", "storage_interrupted"
        except (ValueError, TypeError, KeyError, ArithmeticError, AttributeError):
            status, code = "invalid", "invalid_admission_evidence"
        try:
            store.finish(submission, status, {"error_code": code, "result_kind": "no_admission"})
        except (OSError, sqlite3.Error, ProvenanceError, LedgerError):
            return {"submission_id": submission, "status": "pending", "error_code": "publication_interrupted"}
        return {"submission_id": submission, "status": status, "error_code": code}


def validate_admission(store: Provenance, admission_sha256: str, dataset_sha256: str) -> dict:
    """Recheck every retained dependency, source replay and current loaded policy."""
    admission = store.read_json(_ref(admission_sha256))
    _need(admission.get("dataset_sha256") == dataset_sha256, "admission_dataset_mismatch")
    rows = store.journal.connection.execute(
        "SELECT submission_id,details FROM provenance_outcomes JOIN provenance_submissions USING(submission_id) "
        "WHERE status='success' AND kind='historical_admission'").fetchall()
    registered = [row["submission_id"] for row in rows
                  if json.loads(row["details"]).get("admission_sha256") == admission_sha256]
    _need(bool(registered), "admission_not_registered")
    verified = _verify(store, admission["request"], before_submission_id=registered[0])
    # This terminal comparison deliberately does not depend on the validation
    # helper whose loaded implementation is itself part of the identity.
    if verified != admission:
        raise AdmissionError("admission_dependencies_changed")
    return verified

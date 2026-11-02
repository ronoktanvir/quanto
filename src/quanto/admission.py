"""Evidence-bound, conditional retrospective admission; no rights/absence certification.

Issuer fact extraction and source-use interpretation are attributed judgments.
Byte/receipt/calendar replay is mechanical; owners of the storage remain trusted.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

from quanto import alpaca_data as provider
from quanto import alpaca_actions as actions_provider
from quanto.ledger import LedgerError, hash_bytes, hash_json
from quanto.provenance import Provenance, ProvenanceError

RULES = {"version": "D006-admission-v1.1", "scope": "conditional_retrospective_development",
         "relevance": "full_acquired_interval_ex_effective_and_associated_future_payables",
         "pre_window_cash_merger": "completed_acquirer_only_source_bound_v1",
         "unknown_relevance": "reject", "duplicates": "identical_same_id_only",
         "price_basis": "raw", "currency": "USD", "all_categories": True}
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
    _need(isinstance(value, str) and 0 < len(value) <= 100, "invalid_action_rate")
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

def _actions(records, facts, sources, symbol, start, end, sessions):
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
            _need(not record.get("due_bill_redemption_date"), "unsupported_due_bill")
            event = {"kind": "split", "event_id": event_id, "effective_date": ex_date,
                     "new_rate": record["new_rate"], "old_rate": record["old_rate"]}
            _need(expected.get("kind") == "split" and expected.get("event_id") == event_id
                  and expected.get("effective_date") == ex_date
                  and _decimal(expected.get("new_rate")) == new
                  and _decimal(expected.get("old_rate")) == old
                  and set(expected) == set(event), "issuer_split_conflict")
            event = dict(expected)
        else:
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
            sorted(excluded, key=lambda item: item["annotation"]["provider_id"]))


def _verify(store, request):
    from quanto.explorer import _dataset, _bars, _bar_json, _code_identity
    required = {"dataset_sha256", "bars_receipt_sha256", "calendar_receipt_sha256",
                "actions_receipt_sha256", "primary_facts_sha256", "usage_review_sha256", "submitted_requests"}
    _need(set(request) == required and set(request["submitted_requests"]) == {"bars", "calendar", "actions"},
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
    events, exclusions = _actions(action_source["records"], facts, primary_documents, symbol, start, end, sessions)
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
    return {"schema_version": 1, "kind": "historical_admission", "request": request,
            "dataset_sha256": request["dataset_sha256"], "scope": RULES["scope"], "rules": RULES,
            "code_identity": _code_identity(), "actions": events, "excluded_actions": exclusions, "sessions": sessions,
            "full_acquired_exposure": {"start": start, "end": end}, "market": market,
            "request_parameters_sha256": hash_json({kind: receipts[kind]["request"] for kind in receipts}),
            "limitations": LIMITATIONS, "artifact_refs": sorted(refs)}


def admit_dataset(root: Path, request: dict | str) -> dict:
    from quanto.explorer import _envelope, _request, _schema, ExplorationError
    with Provenance(root) as store:
        _schema(store)
        frozen = _envelope(request)
        submission = store.begin("historical_admission", frozen)
        publishing = False
        try:
            result = _verify(store, _request(frozen))
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
        "SELECT details FROM provenance_outcomes JOIN provenance_submissions USING(submission_id) "
        "WHERE status='success' AND kind='historical_admission'").fetchall()
    import json
    _need(any(json.loads(row[0]).get("admission_sha256") == admission_sha256 for row in rows),
          "admission_not_registered")
    verified = _verify(store, admission["request"])
    # This terminal comparison deliberately does not depend on the validation
    # helper whose loaded implementation is itself part of the identity.
    if verified != admission:
        raise AdmissionError("admission_dependencies_changed")
    return verified

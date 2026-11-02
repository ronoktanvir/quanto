"""Bounded latest-snapshot corporate actions; acquisition never grants admission."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, DecimalException
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode

from quanto import alpaca_data as data
from quanto.alpaca_data import AcquisitionError, Credentials
from quanto.ledger import canonical_json
from quanto.provenance import Provenance, ProvenanceError

MAX_PAGES = 8
MAX_PAGE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_TOTAL_SECONDS = 60
MIN_REQUEST_INTERVAL = 1.0
PAGE_LIMIT = 1000
MAX_REQUEST_BYTES = data.MAX_REQUEST_BYTES
ENDPOINT = "https://data.alpaca.markets/v1/corporate-actions"
FIXED = {"region": "us", "data_quality": "all", "sort": "asc", "limit": PAGE_LIMIT}
CATEGORIES = frozenset({
    "reverse_splits", "forward_splits", "unit_splits", "cash_dividends",
    "stock_dividends", "spin_offs", "cash_mergers", "stock_mergers",
    "stock_and_cash_mergers", "redemptions", "name_changes", "worthless_removals",
    "rights_distributions", "partial_calls", "reorganizations", "capital_gains_distributions",
})


def _request(raw: str, now: datetime) -> dict:
    try:
        value = data._json(raw)
        if not isinstance(value, dict) or value.keys() != {"symbol", "start", "end"}:
            raise ValueError("shape")
        if not isinstance(value["symbol"], str) or not data.SYMBOL.fullmatch(value["symbol"]):
            raise ValueError("symbol")
        start, end = data._date(value["start"]), data._date(value["end"])
        # This is a process-date retrieval envelope, not completed-bar coverage.
        # No documented action-history floor is inferred from bar availability.
        if end < start or end > now.date():
            raise ValueError("dates")
        return {"symbol": value["symbol"], "start": start.isoformat(),
                "end": end.isoformat(), **FIXED}
    except (AcquisitionError, ValueError, TypeError):
        raise AcquisitionError("request_invalid") from None


def _url(request: dict, token: str | None = None) -> str:
    query = {"symbols": request["symbol"], "start": request["start"], "end": request["end"],
             **FIXED}
    if token is not None:
        query["page_token"] = token
    return ENDPOINT + "?" + urlencode(query)


def _json(raw: bytes):
    """Never pass action JSON numbers through binary floats or collapse keys."""
    def unique(pairs):
        value = {}
        for key, child in pairs:
            if key in value:
                raise ValueError("duplicate")
            value[key] = child
        return value

    def reject(_):
        raise ValueError("nonfinite")

    try:
        return json.loads(raw.decode("utf-8"), parse_int=Decimal, parse_float=Decimal,
                          parse_constant=reject, object_pairs_hook=unique)
    except (ValueError, UnicodeError, RecursionError, OverflowError, DecimalException):
        raise AcquisitionError("response_invalid") from None


def _decimal_strings(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _decimal_strings(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_decimal_strings(child) for child in value]
    return value


def _page(body, digest: str, ordinal: int) -> tuple[list[dict], list[str], str | None]:
    if (not isinstance(body, dict) or not isinstance(body.get("corporate_actions"), dict)
            or "next_page_token" not in body):
        raise AcquisitionError("response_invalid")
    rows = []
    categories = list(body["corporate_actions"])
    for category, records in body["corporate_actions"].items():
        if not isinstance(records, list):
            raise AcquisitionError("response_invalid")
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                raise AcquisitionError("response_invalid")
            rows.append({"category": category, "record": _decimal_strings(record),
                         "occurrences": [{"raw_sha256": digest, "page": ordinal, "index": index}]})
            if len(rows) > PAGE_LIMIT:
                raise AcquisitionError("response_oversized")
    return rows, categories, body["next_page_token"]


def acquire_actions(root: Path, request: dict | str, *, transport=None, clock=None,
                    credentials: Credentials | None = None) -> dict:
    """Record bounded all-category observations, including incomplete/unknown events.

    The semantic input has only symbol/start/end. Dates delimit a chosen process
    envelope through the acquisition UTC date. Fully paginated empty results
    remain inspection-only observations and never establish economic absence.
    """
    try:
        store = Provenance(root)
    except (ProvenanceError, OSError, ValueError):
        return {"submission_id": None, "status": "rejected", "error": "storage_unavailable"}
    with store:
        try:
            if not isinstance(request, (dict, str)):
                raise ValueError("unrecordable")
            frozen = canonical_json(request) if isinstance(request, dict) else request
            submission = store.begin("alpaca_actions", frozen)
        except (ProvenanceError, ValueError, TypeError, RecursionError, OverflowError):
            return {"submission_id": None, "status": "rejected", "error": "request_unrecordable"}
        pages, rows, refs, categories = [], [], [], set()
        normalized_request = None
        manifest = {
            "schema_version": 1, "provider": "alpaca", "kind": "actions",
            "submission_id": submission, "evidence_kind": "historical_market_data",
            "research_eligible": False, "admission_status": "inspection_only",
            "pagination_complete": False, "normalization_status": "incomplete",
            "coverage_assessment": "not_performed",
            "rights": {"status": "account_and_exchange_terms_not_certified",
                       "use": "owner_authorized_private_inspection", "public_distribution": False,
                       "external_model_transmission": False,
                       "terms_reference": "https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf"},
            "source_documentation": ["https://docs.alpaca.markets/us/reference/corporateactions-1",
                                     "https://github.com/alpacahq/cli/blob/709d11400129dc7c09b41dd05263187e15801a71/api/specs/market-data-api.json"],
        }
        started = time.monotonic()
        try:
            now = data._utc(clock)
            manifest["started_at"] = now.isoformat()
            manifest["normalizer_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            manifest["transport_sha256"] = hashlib.sha256(Path(data.__file__).read_bytes()).hexdigest()
            normalized_request = _request(frozen, now)
            keys = (data._checked_credentials(credentials) if credentials is not None
                    else data.local_credentials(root))
            try:
                data._safe_body(canonical_json(normalized_request).encode(), keys)
                data._safe_body(frozen.encode("utf-8"), keys)
            except AcquisitionError:
                normalized_request = None
                raise
            submitted_hash = store.put_bytes(frozen.encode("utf-8"))
            refs.append(submitted_hash)
            manifest["submitted_request_sha256"] = submitted_hash
            prepared = {"method": "GET", "request": normalized_request,
                        "url": _url(normalized_request), "max_pages": MAX_PAGES,
                        "max_page_bytes": MAX_PAGE_BYTES, "max_total_bytes": MAX_TOTAL_BYTES,
                        "max_total_seconds": MAX_TOTAL_SECONDS,
                        "min_request_interval": MIN_REQUEST_INTERVAL,
                        "all_categories": True, "date_semantics": "process_date_envelope"}
            request_hash = store.put_json(prepared)
            refs.append(request_hash)
            manifest["request_sha256"] = request_hash
            store.journal.append_event("acquisition_request_prepared", {
                "submission_id": submission, "request_sha256": request_hash})
            token, seen_tokens, total, last_request_at = None, set(), 0, None
            for page in range(MAX_PAGES):
                if last_request_at is not None:
                    delay = MIN_REQUEST_INTERVAL - (time.monotonic() - last_request_at)
                    if delay > 0:
                        time.sleep(delay)
                remaining = MAX_TOTAL_SECONDS - (time.monotonic() - started)
                if remaining <= 0:
                    raise AcquisitionError("request_timeout", status="failed")
                url = _url(normalized_request, token)
                last_request_at = time.monotonic()
                response = data._dispatch("GET", url, keys, remaining,
                                          min(MAX_PAGE_BYTES, MAX_TOTAL_BYTES - total), transport)
                total += len(response.body)
                digest = store.put_bytes(response.body)
                refs.append(digest)
                observation = {"page": page + 1, "url": url, "retrieved_at": None,
                               "http_status": 200, "raw_sha256": digest, "bytes": len(response.body)}
                pages.append(observation)
                observation["retrieved_at"] = data._utc(clock).isoformat()
                store.journal.append_event("acquisition_page_received", {
                    "submission_id": submission, **observation})
                if time.monotonic() - started > MAX_TOTAL_SECONDS:
                    raise AcquisitionError("request_timeout", status="failed")
                records, present, token = _page(_json(response.body), digest, page + 1)
                rows.extend(records)
                categories.update(present)
                if time.monotonic() - started > MAX_TOTAL_SECONDS:
                    raise AcquisitionError("request_timeout", status="failed")
                if token is None:
                    manifest["pagination_complete"] = True
                    break
                if (not isinstance(token, str) or not data.TOKEN.fullmatch(token)
                        or token in seen_tokens):
                    raise AcquisitionError("pagination_incomplete")
                seen_tokens.add(token)
                if page + 1 == MAX_PAGES or total >= MAX_TOTAL_BYTES:
                    raise AcquisitionError("pagination_incomplete")
            coverage = {"requested_start": normalized_request["start"],
                        "requested_end": normalized_request["end"], "pagination_complete": True,
                        "date_semantics": "process_date_envelope",
                        "historical_information": "latest_retrieved_revision_not_point_in_time",
                        "economic_window_coverage": "not_assessed",
                        "empty_result": "no_records_returned_not_absence_proof" if not rows else None}
            normalized = {"schema_version": 1, "kind": "corporate_actions",
                          "evidence_kind": "historical_market_data", "research_eligible": False,
                          "admission_status": "inspection_only",
                          "identity": {"provider": "alpaca", "symbol": normalized_request["symbol"],
                                       "asset_class": "us_equity"}, "coverage": coverage,
                          "categories_present": sorted(categories),
                          "unknown_categories": sorted(categories - CATEGORIES), "records": rows}
            normalized_hash = store.put_json(normalized)
            refs.append(normalized_hash)
            manifest.update(status="success", normalized_sha256=normalized_hash, row_count=len(rows),
                            normalization_status="complete", finished_at=data._utc(clock).isoformat())
        except AcquisitionError as exc:
            manifest.update(status=exc.status, error=exc.category, http_status=exc.http_status)
        except (ProvenanceError, OSError):
            manifest.update(status="failed", error="storage_unavailable")
        except Exception:
            manifest.update(status="failed", error="acquisition_failed")
        manifest.update(request=normalized_request, pages=pages,
                        categories_present=sorted(categories),
                        unknown_categories=sorted(categories - CATEGORIES),
                        limitations=[
                            "Acquisition is inspection-only, not economic coverage or financial admission.",
                            "Process-date search bounds do not certify ex/effective/pay-date coverage.",
                            "A fully paginated empty response does not prove no relevant actions.",
                            "Latest retrieved revisions do not reconstruct historical information availability.",
                            "Provider delay, incomplete fields and unknown categories require admission review.",
                            "Identity continuity, currency, dividend share basis and source rights remain unverified.",
                        ])
        try:
            receipt_hash = store.put_json(manifest)
            refs.append(receipt_hash)
            store.finish(submission, manifest["status"], {
                "receipt_sha256": receipt_hash, "artifact_refs": list(dict.fromkeys(refs)),
                "error": manifest.get("error"), "research_eligible": False})
        except (ProvenanceError, OSError, ValueError):
            return {"submission_id": submission, "status": "pending", "error": "storage_unavailable"}
        return {"submission_id": submission, "status": manifest["status"],
                "receipt_sha256": receipt_hash, "normalized_sha256": manifest.get("normalized_sha256"),
                "row_count": manifest.get("row_count", 0), "error": manifest.get("error"),
                "research_eligible": False, "admission_status": "inspection_only"}

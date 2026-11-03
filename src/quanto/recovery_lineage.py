"""Inert, source-pinned acquisition/admission lineage for recovery_closure.

Only retained bytes and captured rows are interpreted. No provider, admission,
strategy, provenance constructor or historical module is imported or executed.
All caches, traversal, JSON, SQL and deadlines use the owning bounded reader.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
import math
import re
from urllib.parse import parse_qsl, urlsplit
from zoneinfo import ZoneInfo

from quanto import recovery

BAR_SOURCES = frozenset({
    "8ef36538adcb424928a95116d66835387eedb98cc27b5b67e624825875bc015c",
    "9182307746567e349ed1b936eb35949fac7684430336279968f02d6f35ab0c76"})
TRANSPORT_SOURCE = "9182307746567e349ed1b936eb35949fac7684430336279968f02d6f35ab0c76"
ACTION_SOURCE = "f6804b8717a3dd60ff77fcf934581170b762cf82f77b5dd229c349c127205cc7"
ADMISSION_SOURCES = {
    "d006": ("7cd34c3244b7f87496827f933606e4000d52f4408438304ef14f27d1434cd953",
             "58d3e5508cc967210ebe41fb0b07200d32090652534fb87df5749647c9f81ddd"),
    "d007": ("5b1d5aa7d9aea6488ba96ac8a89a597d37e78ad28be0175699f6032abb8787c1",
             "6a3f02d27f0c062d993ee3d112f0e76b88221fc8653305b84be62b822bcb9745")}
POLICY_SOURCE = "eb7ac89bbf1c85cf276f614bd296ad82f2d22f94d723788a3718c42ff5b12625"
ACQUISITIONS = {"alpaca_bars": "bars", "alpaca_calendar": "calendar", "alpaca_actions": "actions"}
REGISTRATIONS = {*ACQUISITIONS, "historical_admission", "policy_revision",
                 "regular_way_split_semantic_review", "public_source_observation",
                 "pilot_plan_registration", "pilot_plan_refinement"}
REGISTRATION_FIELDS = {"historical_admission": ("admission_sha256", "admission"),
    "policy_revision": ("policy_revision_sha256", "policy_revision"),
    "regular_way_split_semantic_review": ("review_sha256", "semantic_review"),
    "public_source_observation": ("receipt_sha256", "public_source_receipt"),
    "pilot_plan_registration": ("plan_sha256", "predecessor_plan"),
    "pilot_plan_refinement": ("plan_sha256", "predecessor_plan")}
ROLES = {"acquisition_receipt", "acquisition_request", "normalized_observation", "dataset_source",
         "admission", "policy_revision", "public_source_receipt", "semantic_review",
         "primary_facts_d006", "primary_facts_d007", "source_use_review", "independent_schedule",
         "split_annotation", "predecessor_plan", "original_request", "admission_request_d006"}
OPAQUE = {"opaque_provider_page", "opaque_source", "opaque_report", "opaque_policy_evidence"}
PAGE_FIELDS = {"page", "url", "retrieved_at", "http_status", "raw_sha256", "bytes"}
CATEGORIES = frozenset({"reverse_splits", "forward_splits", "unit_splits", "cash_dividends",
    "stock_dividends", "spin_offs", "cash_mergers", "stock_mergers", "stock_and_cash_mergers",
    "redemptions", "name_changes", "worthless_removals", "rights_distributions", "partial_calls",
    "reorganizations", "capital_gains_distributions"})
JUDGMENT = {"source_sha256", "locator", "judgment"}
ATTRIBUTION = JUDGMENT | {"author", "observed_at", "classification", "supporting_sources"}
SOURCE_ROLES = {"issuer", "finra_11140", "finra_11630", "finra_notice_24_04", "provider_schema"}
DATE_FIELDS = {"process_date", "ex_date", "record_date", "payable_date", "due_bill_redemption_date", "effective_date"}
ADMISSION_REQUEST = {"dataset_sha256", "bars_receipt_sha256", "calendar_receipt_sha256",
    "actions_receipt_sha256", "primary_facts_sha256", "usage_review_sha256", "submitted_requests"}
FROZEN_FIELDS = ("instrument", "data_start", "data_end", "evaluation_start", "evaluation_end", "lookback",
    "starting_cash", "entry_threshold", "exit_threshold", "cost_bps_scenarios", "basis", "signal_basis",
    "dividend_reinvestment", "signal_rule", "sma_includes_current_close", "warmup_selection", "buy_quantity",
    "sell_proceeds", "arithmetic", "benchmark", "terminal_policy", "session_order", "dividend_rate_basis",
    "split_effective_date", "same_session_split_and_dividend")
SYMBOL = re.compile(r"[A-Z][A-Z0-9.-]{0,14}")
TOKEN = re.compile(r"[A-Za-z0-9_+/=.-]{1,2048}")
DECIMAL = re.compile(r"\+?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")

ADMISSION_RULES = {'d006': {'version': 'D006-admission-v1.1', 'scope': 'conditional_retrospective_development', 'relevance': 'full_acquired_interval_ex_effective_and_associated_future_payables', 'pre_window_cash_merger': 'completed_acquirer_only_source_bound_v1', 'unknown_relevance': 'reject', 'duplicates': 'identical_same_id_only', 'price_basis': 'raw', 'currency': 'USD', 'all_categories': True}, 'd007': {'version': 'D007-admission-v1', 'scope': 'conditional_retrospective_development', 'relevance': 'full_acquired_interval_ex_effective_and_associated_future_payables', 'pre_window_cash_merger': 'completed_acquirer_only_source_bound_v1', 'unknown_relevance': 'reject', 'duplicates': 'identical_same_id_only', 'price_basis': 'raw', 'currency': 'USD', 'all_categories': True, 'regular_way_split': 'domestic_integer_forward_split_v1'}}
POLICY_RULES = {'version': 'D007-policy-revision-v1', 'accepted_decision_sha256': 'bf8c254645c33550fceb19b794a3aeae933c54d635df149fccda8310f5e987ce', 'approved_review_sha256s': {'accounting': 'f2e6541fef64fe1c3067e0dd9b7f1350a71319618d4482394b14afd025368664', 'sources': '9a6a797ffcda1634229dbb1e6019fc0e5ad3f810a259f2ba45155b7c75469869', 'integrity': '57c67a58e9858d8ae7628aed775d802f1e6ad3488976bdeee43c3e56c9604cdf', 'operations': '055a3a7cd1e6606797043b6e93506993b7dd4d594b3d579fe5a0f784869edb79', 'scope': '6bc870d5fb72b11dbd1da373ec9b381c50c63ff4c5683d03ef427e4d3a7eade3', 'fable-cli': '27b75eb526593a579d3858a674cbaabd36b3c9e47c9bfa546ed0434c9dc05139', 'opus-cli': '3cecb5c8b581d882da536f24449bec833f68b59bb3ac1bf740c5b399eae4fb72'}, 'classification': 'post_acquisition_development_only', 'facts': 'additive_sources_single_regular_way_split_and_review_independent_schedule', 'cost_bps': [0, 10, 25], 'authorship': 'cooperating_owner_not_authenticated'}
SPLIT_LIMITATIONS = ['economic_packages_not_settled_inventory_or_broker_availability', 'redemption_delivery_outcome_unverified', 'published_schedule_not_emergency_closure_or_symbol_halt_certificate', 'expected_scheduled_trading_not_observed_execution', 'attributed_purchaser_entitlement_not_independent_market_observation']
ADMISSION_LIMITATIONS = ['latest_retrieved_revision_not_point_in_time', 'vendor_omissions_not_excluded', 'process_envelope_not_certified_history_floor_or_lag_bound', 'attributed_issuer_extraction_not_machine_proven', 'account_and_exchange_terms_not_certified', 'development_only_no_protected_holdout', 'daily_open_not_certified_executable_fill', 'fractional_shares_no_cash_in_lieu_taxes_or_settlement_model']

class LineageError(ValueError):
    """Fixed refusal code, never private values."""


def need(condition, code="malformed_lineage_profile"):
    if not condition:
        raise LineageError(code)


def obj(value, required, optional=()):
    need(type(value) is dict and set(required) <= set(value) <= set(required) | set(optional))


def text(value, maximum=8000):
    need(type(value) is str and bool(value.strip()) and len(value) <= maximum)
    return value


def digest(value):
    need(type(value) is str and recovery.DIGEST.fullmatch(value), "invalid_reference")
    return value


def integer(value, minimum=0, maximum=200_000):
    need(type(value) is int and minimum <= value <= maximum)
    return value


def day(value):
    text(value, 10)
    result = date.fromisoformat(value)
    need(result.isoformat() == value)
    return value


def aware(value):
    text(value, 80)
    result = datetime.fromisoformat(value)
    need(result.utcoffset() is not None)
    return result


def rate(value, profile):
    text(value, 100)
    if profile == "d007":
        need(DECIMAL.fullmatch(value))
    try:
        number = Decimal(value)
        need(number.is_finite() and number > 0 and abs(number.adjusted()) <= 100)
    except InvalidOperation:
        raise LineageError("invalid_historical_decimal") from None


def equal(left, right):
    return recovery._json(left) == recovery._json(right)


def version(value, kind=None):
    need(type(value.get("schema_version")) is int and value["schema_version"] == 1)
    if kind is not None:
        need(value.get("kind") == kind, "profile_role_mismatch")


def sequence(value, maximum=200_000):
    need(type(value) is list and len(value) <= maximum)
    return value


class Lineage:
    def __init__(self, reader):
        self.r = reader
        self.raw_cache, self.documents = {}, {}
        self.submissions, self.outcomes, self.events = {}, {}, []
        self.starts, self.finishes, self.prepared, self.pages = {}, {}, {}, {}
        self.origins, self.receipts, self.prepared_origins, self.normalized_origins = {}, {}, {}, {}
        self.bound = {}
        self.original_bindings = set()

    def raw(self, ref):
        digest(ref)
        if ref in self.r.tombstones:
            self.r.gap("lineage_dependency_tombstoned", ref)
            return None
        need(ref in self.r.objects, "required_object_missing")
        if ref not in self.raw_cache:
            self.r.tick()
            value = recovery._read(self.r.path / "objects" / (ref + ".bin"), self.r.limits.snapshot.object_bytes, private=True)
            need(recovery._sha(value) == ref, "object_changed")
            self.raw_cache[ref] = value
        self.r.tick()
        return self.raw_cache[ref]

    def document(self, ref):
        raw = self.raw(ref)
        if raw is None:
            return None
        if ref not in self.documents:
            value = self.r.parse(raw)
            need(type(value) is dict)
            self.documents[ref] = value
        return self.documents[ref]

    def at(self, ref, role, function, *arguments):
        # Eager nested checks retain the typed edge's graph distance. They may
        # not flatten a dependency chain to the caller's shallower distance.
        previous = self.r.current_hops
        self.r.current_hops = max(previous, self.r.distances.get((ref, role), previous))
        try:
            return function(ref, *arguments)
        finally:
            self.r.current_hops = previous

    def dep(self, parent, field, ref, role, *, nonempty=False):
        self.r.edge(parent, field, ref, role)
        raw = self.raw(ref)
        if nonempty and raw is not None:
            need(bool(raw), "empty_lineage_evidence")
        return raw

    def manual(self, parent, value, required, optional=()):
        need(type(value) is dict and set(required) <= set(value))
        if set(value) - set(required) - set(optional):
            self.r.gap("unsupported_manual_fields", parent)

    def index(self):
        for row in self.r.rows("provenance_submissions"):
            sid = text(row["submission_id"], 1024)
            need(sid not in self.submissions, "duplicate_registration")
            self.submissions[sid] = row
        for row in self.r.rows("provenance_outcomes"):
            sid = row["submission_id"]
            need(sid in self.submissions and sid not in self.outcomes, "duplicate_or_missing_registration")
            data = self.r.parse(row["details"])
            need(type(data) is dict)
            self.outcomes[sid] = {**row, "details": data}
        for row in self.r.rows("events"):
            value = self.r.parse(row["payload"])
            self.events.append((row, value))
            if row["kind"] in {"submission_started", "submission_finished", "acquisition_request_prepared", "acquisition_page_received"}:
                need(type(value) is dict)
                sid = value.get("submission_id")
                if type(sid) is str:
                    target = {"submission_started": self.starts, "submission_finished": self.finishes,
                              "acquisition_request_prepared": self.prepared, "acquisition_page_received": self.pages}[row["kind"]]
                    target.setdefault(sid, []).append((row["id"], value))
        for sid, source in self.submissions.items():
            if source["kind"] not in REGISTRATIONS:
                continue
            self.registration(sid)
            out = self.outcomes.get(sid)
            if out is None:
                self.r.gap("pending_registered_work", "submission/" + sid)
                continue
            details = out["details"]
            if source["kind"] in ACQUISITIONS:
                obj(details, {"receipt_sha256", "artifact_refs", "error", "research_eligible"})
                need(details["research_eligible"] is False)
                ref = digest(details["receipt_sha256"])
                self.origins.setdefault((ref, "acquisition_receipt"), []).append(sid)
                data = self.document(ref)
                if data is not None:
                    self.receipts[ref] = data
                    for field, target in (("request_sha256", self.prepared_origins), ("normalized_sha256", self.normalized_origins)):
                        if field in data:
                            target.setdefault(digest(data[field]), []).append(ref)
            elif out["status"] == "success":
                field, role = REGISTRATION_FIELDS[source["kind"]]
                ref = digest(details[field])
                self.origins.setdefault((ref, role), []).append(sid)
            else:
                if source["kind"] in {"historical_admission", "policy_revision", "regular_way_split_semantic_review"}:
                    obj(details, {"error_code", "result_kind"})
                    text(details["error_code"])
                    need(out["status"] in {"invalid", "interrupted"})
                    expected = {"historical_admission": "no_admission", "policy_revision": "no_policy_revision",
                                "regular_way_split_semantic_review": "no_semantic_review"}[source["kind"]]
                    need(details["result_kind"] == expected)
                else:
                    self.r.gap("unsupported_registration_failure_details", "submission/" + sid)

    def registration(self, sid, kind=None, status=None):
        need(sid in self.submissions, "missing_database_binding")
        row = self.submissions[sid]
        if kind is not None:
            need(row["kind"] in ({kind} if type(kind) is str else kind), "registration_kind_mismatch")
        if sid not in self.bound:
            starts, finishes = self.starts.get(sid, []), self.finishes.get(sid, [])
            need(len(starts) == 1, "registration_event_mismatch")
            expected = {key: row[key] for key in ("submission_id", "kind", "request_sha256", "request_bytes", "request_encoding")}
            digest(row["request_sha256"])
            integer(row["request_bytes"], maximum=64 * 1024)
            need(re.fullmatch(r"[0-9a-f]{32}", sid))
            need(row["request_encoding"] in {"canonical_json", "utf8_text"})
            need(equal(starts[0][1], expected), "registration_event_mismatch")
            out = self.outcomes.get(sid)
            finish = None
            if out is None:
                need(not finishes, "registration_event_mismatch")
            else:
                need(len(finishes) == 1 and starts[0][0] < finishes[0][0], "registration_event_order")
                need(equal(finishes[0][1], {"submission_id": sid, "status": out["status"], "details": out["details"]}), "registration_event_mismatch")
                finish = finishes[0][0]
                refs = sequence(out["details"].get("artifact_refs", []), 128)
                need(len(set(refs)) == len(refs))
                for ref in refs:
                    digest(ref)
            self.bound[sid] = (starts[0][0], finish)
        if status is not None:
            need(self.outcomes.get(sid, {}).get("status") == status, "registration_status_mismatch")
        return self.bound[sid]

    def registered(self, ref, role, kind):
        found = self.origins.get((ref, role), [])
        if not found:
            self.r.gap("unresolved_registered_origin", ref + ":" + role)
        for sid in found:
            self.registration(sid, kind, "success")
            need(ref in self.outcomes[sid]["details"]["artifact_refs"], "registration_artifact_mismatch")
        return found

    def original(self, parent, ref, sid, expected=None, *, promised=True, parse_document=True):
        row = self.submissions[sid]
        need(ref == row["request_sha256"], "original_request_identity_mismatch")
        if not promised and ref not in self.r.objects and ref not in self.r.tombstones:
            self.r.gap("original_request_bytes_unavailable", parent)
            return None
        raw = self.dep(parent, "original_request", ref, "original_request")
        if raw is None:
            return None
        need(len(raw) == row["request_bytes"], "original_request_identity_mismatch")
        if not parse_document:
            raw.decode("utf-8")
            self.original_bindings.add(ref)
            return None
        value = self.r.parse(raw)
        need(type(value) is dict)
        if row["request_encoding"] == "canonical_json":
            need(recovery._json(value) == raw, "original_request_encoding_mismatch")
        if expected is not None:
            need(equal(value, expected), "original_request_content_mismatch")
        self.original_bindings.add(ref)
        return value

    def outcome_root(self, sid):
        source, out = self.submissions[sid], self.outcomes[sid]
        if source["kind"] not in REGISTRATIONS:
            return False
        if source["kind"] in ACQUISITIONS:
            self.r.edge("submission/" + sid, "receipt_sha256", out["details"]["receipt_sha256"], "acquisition_receipt")
        elif out["status"] == "success":
            field, role = REGISTRATION_FIELDS[source["kind"]]
            self.r.edge("submission/" + sid, field, out["details"][field], role)
        return True

    def event_root(self, row, data):
        kind, parent = row["kind"], "event/" + str(row["id"])
        sid = data.get("submission_id") if type(data) is dict else None
        if kind in {"submission_started", "submission_finished"}:
            return sid in self.submissions and self.submissions[sid]["kind"] in REGISTRATIONS
        if kind not in {"acquisition_request_prepared", "acquisition_page_received"}:
            return False
        if sid not in self.submissions or self.submissions[sid]["kind"] not in ACQUISITIONS:
            field, role = (("request_sha256", "acquisition_request") if kind == "acquisition_request_prepared"
                           else ("raw_sha256", "opaque_provider_page"))
            need(field in data)
            self.r.edge(parent, field, data[field], role)
            self.r.gap("acquisition_event_origin_unresolved", parent)
            return True
        start, finish = self.registration(sid)
        need(start < row["id"] and (finish is None or row["id"] < finish), "acquisition_event_order")
        if kind == "acquisition_request_prepared":
            obj(data, {"submission_id", "request_sha256"})
            need(len(self.prepared[sid]) == 1, "duplicate_prepared_event")
            self.r.edge(parent, "request_sha256", data["request_sha256"], "acquisition_request")
        else:
            obj(data, {"submission_id", *PAGE_FIELDS})
            self.page(parent, {key: data[key] for key in PAGE_FIELDS})
            prepared = self.prepared.get(sid, [])
            need(len(prepared) == 1 and prepared[0][0] < row["id"], "acquisition_event_order")
            pages = sorted(self.pages[sid])
            need([v["page"] for _, v in pages] == list(range(1, len(pages) + 1)), "acquisition_page_order")
        return True

    def profile(self, ref, data):
        normalizer = data.get("normalizer_sha256")
        if normalizer is not None:
            self.r.edge(ref, "normalizer_sha256", normalizer, "historical_source", "external_evidence")
        if "transport_sha256" in data:
            self.r.edge(ref, "transport_sha256", data["transport_sha256"], "historical_source", "external_evidence")
        kind = data.get("kind")
        known = normalizer in BAR_SOURCES or normalizer == ACTION_SOURCE
        if normalizer in BAR_SOURCES:
            need(kind in {"bars", "calendar"}, "producer_profile_conflict")
            return kind
        if normalizer == ACTION_SOURCE:
            need(kind == "actions", "producer_profile_conflict")
            if data.get("transport_sha256") == TRANSPORT_SOURCE:
                return kind
            if data.get("transport_sha256") in BAR_SOURCES:
                need(False, "producer_profile_conflict")
        self.r.gap("acquisition_producer_origin_unresolved", ref)
        if known:
            self.r.gap("acquisition_transport_origin_unresolved", ref)
        return None

    def request_parameters(self, value, kind):
        fixed = {"calendar": {}, "bars": {"timeframe": "1Day", "feed": "sip", "currency": "USD", "asof": "-"},
                 "actions": {"region": "us", "data_quality": "all", "sort": "asc", "limit": 1000}}[kind]
        obj(value, {"start", "end", *fixed, *({"symbol"} if kind != "calendar" else set()), *({"adjustment"} if kind == "bars" else set())})
        need(day(value["start"]) <= day(value["end"]))
        need(all(equal(value[key], item) for key, item in fixed.items()))
        if kind != "calendar":
            need(SYMBOL.fullmatch(text(value["symbol"], 15)))
        if kind == "bars":
            need(value["adjustment"] in {"raw", "all"})

    def url(self, value, request, kind, *, first=False):
        text(value, 8000)
        # urlsplit removes some literal controls; the recorded writer URL must
        # be checked before parsing can erase a contradictory retained byte.
        need(not any(ord(char) <= 0x20 or ord(char) == 0x7f for char in value),
             "acquisition_url_mismatch")
        parsed = urlsplit(value)
        need(parsed.scheme == "https" and not parsed.username and not parsed.password
             and not parsed.fragment and parsed.port is None, "acquisition_url_mismatch")
        pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True, max_num_fields=16)
        need(len({key for key, _ in pairs}) == len(pairs), "duplicate_url_parameter")
        query = dict(pairs)
        if kind == "calendar":
            host, path, expected = "paper-api.alpaca.markets", "/v2/calendar", request
        elif kind == "actions":
            host, path = "data.alpaca.markets", "/v1/corporate-actions"
            expected = {"symbols": request["symbol"], **{key: str(request[key]) for key in ("start", "end", "region", "data_quality", "sort", "limit")}}
        else:
            host, path = "data.alpaca.markets", "/v2/stocks/" + request["symbol"] + "/bars"
            zone = ZoneInfo("America/New_York")
            start = datetime.combine(date.fromisoformat(request["start"]), time(), zone)
            end = datetime.combine(date.fromisoformat(request["end"]) + timedelta(days=1), time(), zone)
            expected = {key: request[key] for key in ("timeframe", "feed", "currency", "asof", "adjustment")}
            expected.update(start=start.astimezone(timezone.utc).isoformat(),
                            end=(end - timedelta(microseconds=1)).astimezone(timezone.utc).isoformat(), limit="1000", sort="asc")
        need(parsed.netloc == host and parsed.path == path, "acquisition_url_mismatch")
        token = query.get("page_token")
        if not first and kind != "calendar":
            need(token is not None, "acquisition_url_mismatch")
        if "page_token" in query:
            need(not first and kind != "calendar" and TOKEN.fullmatch(query.pop("page_token")), "acquisition_url_mismatch")
        need(query == expected, "acquisition_url_mismatch")
        return token

    def page(self, parent, value, *, nullable=False):
        obj(value, PAGE_FIELDS)
        integer(value["page"], 1, 8)
        need(type(value["http_status"]) is int and value["http_status"] == 200)
        integer(value["bytes"], maximum=2 * 1024 * 1024)
        text(value["url"])
        if value["retrieved_at"] is None:
            need(nullable)
        else:
            aware(value["retrieved_at"])
        raw = self.dep(parent, "pages/raw_sha256", value["raw_sha256"], "opaque_provider_page")
        if raw is not None:
            need(len(raw) == value["bytes"], "provider_byte_length_mismatch")

    def receipt(self, ref, data):
        origins = self.origins.get((ref, "acquisition_receipt"), [])
        if not origins:
            self.r.gap("unresolved_registered_origin", ref)
            return False
        for sid in origins:
            kind = ACQUISITIONS[self.submissions[sid]["kind"]]
            need(data.get("submission_id") == sid and data.get("kind") == kind
                 and data.get("status") == self.outcomes[sid]["status"], "receipt_registration_mismatch")
            need(ref in self.outcomes[sid]["details"]["artifact_refs"], "receipt_registration_mismatch")
        kind = self.profile(ref, data)
        for field, role in (("request_sha256", "acquisition_request"), ("submitted_request_sha256", "original_request"),
                            ("normalized_sha256", "normalized_observation")):
            if field in data:
                self.dep(ref, field, data[field], role)
        for item in sequence(data.get("pages", []), 8):
            self.page(ref, item, nullable=data.get("kind") == "actions" and data.get("status") != "success")
        if kind is None:
            return False
        common = {"schema_version", "provider", "kind", "submission_id", "evidence_kind", "admission_status",
                  "research_eligible", "rights", "source_documentation", "status", "request", "pages", "limitations"}
        progress = {"started_at", "normalizer_sha256", "request_sha256", "normalized_sha256", "row_count", "finished_at"}
        optional = progress | {"error", "http_status"}
        if kind == "actions":
            common |= {"pagination_complete", "normalization_status", "coverage_assessment", "categories_present", "unknown_categories"}
            optional |= {"transport_sha256", "submitted_request_sha256"}
        obj(data, common, optional)
        version(data)
        need(data["provider"] == "alpaca" and data["evidence_kind"] == "historical_market_data"
             and data["admission_status"] == "inspection_only" and data["research_eligible"] is False)
        need(data["status"] in {"success", "failed", "invalid"})
        obj(data["rights"], {"status", "use", "public_distribution", "external_model_transmission", "terms_reference"})
        need(data["rights"] == {"status": "account_and_exchange_terms_not_certified", "use": "owner_authorized_private_inspection",
             "public_distribution": False, "external_model_transmission": False,
             "terms_reference": "https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf"})
        for key in ("source_documentation", "limitations"):
            need(sequence(data[key], 30))
            for value in data[key]:
                text(value)
        for key in ("started_at", "finished_at"):
            if key in data:
                aware(data[key])
        # Writer phase order: fields from later successful publication cannot
        # survive an exception before the single manifest.update call.
        order = ["started_at", "normalizer_sha256"]
        if kind == "actions":
            order += ["transport_sha256", "submitted_request_sha256"]
        order += ["request_sha256"]
        for index, key in enumerate(order):
            if key in data:
                need(all(prior in data for prior in order[:index]), "invalid_acquisition_prefix")
        if data["request"] is not None:
            self.request_parameters(data["request"], kind)
            need("normalizer_sha256" in data)
        if "request_sha256" in data or data["pages"]:
            need(data["request"] is not None and "request_sha256" in data)
        if data["status"] == "success":
            need(progress <= data.keys() and data["pages"] and "error" not in data and "http_status" not in data)
            integer(data["row_count"], 0 if kind == "actions" else 1, 10_000)
        else:
            need(not {"normalized_sha256", "row_count", "finished_at"} & data.keys(), "invalid_acquisition_prefix")
            text(data["error"])
            if data.get("http_status") is not None:
                integer(data["http_status"], 100, 599)
        need([item["page"] for item in data["pages"]] == list(range(1, len(data["pages"]) + 1)))
        need(len(data["pages"]) <= (1 if kind == "calendar" else 8)
             and sum(item["bytes"] for item in data["pages"]) <= 8 * 1024 * 1024)
        sid = data["submission_id"]
        details = self.outcomes[sid]["details"]
        need(details["error"] == data.get("error"), "receipt_registration_mismatch")
        required = {ref, *(item["raw_sha256"] for item in data["pages"])}
        required.update(data[key] for key in ("request_sha256", "normalized_sha256", "submitted_request_sha256") if key in data)
        need(required <= set(details["artifact_refs"]), "receipt_registration_mismatch")
        prepared = self.prepared.get(sid, [])
        if "request_sha256" in data:
            need(len(prepared) <= 1)
            if prepared:
                need(prepared[0][1]["request_sha256"] == data["request_sha256"], "prepared_request_binding_mismatch")
            else:
                need(data["status"] != "success")
                self.r.gap("interrupted_prepared_event_publication", ref)
        else:
            need(not prepared and not self.pages.get(sid))
        recorded = {value["page"]: value for _, value in self.pages.get(sid, [])}
        need(len(recorded) == len(self.pages.get(sid, [])) and set(recorded) <= {p["page"] for p in data["pages"]})
        tokens = set()
        for item in data["pages"]:
            token = self.url(item["url"], data["request"], kind, first=item["page"] == 1)
            if token is not None:
                need(token not in tokens, "duplicate_page_token")
                tokens.add(token)
            if item["page"] in recorded:
                need(equal(recorded[item["page"]], {"submission_id": sid, **item}), "page_event_receipt_mismatch")
            else:
                need(data["status"] != "success" and item["page"] == len(data["pages"]))
                self.r.gap("interrupted_page_event_publication", ref)
        if kind == "actions":
            need(type(data["pagination_complete"]) is bool and data["coverage_assessment"] == "not_performed")
            self.categories(data)
            if data["status"] == "success":
                need(data["pagination_complete"] is True and data["normalization_status"] == "complete"
                     and "submitted_request_sha256" in data)
            else:
                need(data["normalization_status"] == "incomplete")
            if "submitted_request_sha256" in data:
                expected = {key: data["request"][key] for key in ("symbol", "start", "end")}
                self.original(ref, data["submitted_request_sha256"], sid, expected)
        else:
            self.original(ref, self.submissions[sid]["request_sha256"], sid, promised=False, parse_document=data["status"] == "success")
        self.r.gap("provider_normalization_semantics_not_replayed", ref)
        return True

    def prepared_request(self, ref, data):
        candidates = self.prepared_origins.get(ref, [])
        profiles = []
        for receipt_ref in candidates:
            receipt = self.receipts[receipt_ref]
            kind = self.profile(receipt_ref, receipt)
            if kind is not None:
                profiles.append((kind, receipt))
        if not profiles:
            self.r.gap("prepared_request_origin_unresolved", ref)
            return False
        for kind, receipt in profiles:
            fields = {"method", "request", "url", "max_pages", "max_total_bytes", "max_total_seconds"}
            if kind == "actions":
                fields |= {"max_page_bytes", "min_request_interval", "all_categories", "date_semantics"}
            obj(data, fields)
            need(data["method"] == "GET" and equal(data["request"], receipt["request"]), "prepared_request_binding_mismatch")
            self.request_parameters(data["request"], kind)
            for key, value in {"max_pages": 1 if kind == "calendar" else 8, "max_total_bytes": 8 * 1024 * 1024, "max_total_seconds": 60}.items():
                need(type(data[key]) is int and data[key] == value)
            if kind == "actions":
                need(type(data["max_page_bytes"]) is int and data["max_page_bytes"] == 2 * 1024 * 1024
                     and type(data["min_request_interval"]) is float and data["min_request_interval"] == 1.0
                     and data["all_categories"] is True and data["date_semantics"] == "process_date_envelope")
            self.url(data["url"], data["request"], kind, first=True)
        return True

    def categories(self, data):
        for key in ("categories_present", "unknown_categories"):
            values = sequence(data[key], 200_000)
            for value in values:
                text(value)
            need(values == sorted(set(values)))
        need(data["unknown_categories"] == sorted(set(data["categories_present"]) - CATEGORIES))

    def provider_record(self, value):
        need(type(value) is dict)
        pending = [value]
        while pending:
            self.r.tick()
            item = pending.pop()
            if type(item) is dict:
                for key, child in item.items():
                    need(type(key) is str and len(key) <= self.r.limits.snapshot.object_bytes)
                    pending.append(child)
            elif type(item) is list:
                pending.extend(item)
            else:
                need(item is None or type(item) in {str, bool}, "provider_record_number_not_string")

    def occurrences(self, parent, values, pages=None, *, single=False):
        sequence(values)
        need(len(values) == 1 if single else len(values) > 0)
        for value in values:
            obj(value, {"raw_sha256", "page", "index"})
            integer(value["page"], 1, 8)
            integer(value["index"], maximum=999)
            self.dep(parent, "occurrences/raw_sha256", value["raw_sha256"], "opaque_provider_page")
            if pages is not None:
                need(pages.get(value["page"]) == value["raw_sha256"], "occurrence_page_mismatch")

    def normalized(self, ref, data):
        candidates = self.normalized_origins.get(ref, [])
        if not candidates:
            self.r.gap("normalized_observation_origin_unresolved", ref)
            return False
        supported = False
        for receipt_ref in candidates:
            receipt = self.receipts[receipt_ref]
            kind = self.profile(receipt_ref, receipt)
            if kind is None:
                continue
            supported = True
            need(receipt.get("status") == "success", "normalized_receipt_status_mismatch")
            request = receipt["request"]
            fields = {"schema_version", "kind", "evidence_kind", "research_eligible", "admission_status", "identity", "coverage"}
            fields |= {"bars", "price_basis"} if kind == "bars" else {"sessions"} if kind == "calendar" else {"records", "categories_present", "unknown_categories"}
            obj(data, fields)
            version(data, {"bars": "daily_bars", "calendar": "exchange_calendar", "actions": "corporate_actions"}[kind])
            need(data["evidence_kind"] == "historical_market_data" and data["research_eligible"] is False and data["admission_status"] == "inspection_only")
            identity = {"provider": "alpaca", "asset_class": "us_equity"}
            if kind == "actions":
                identity["symbol"] = request["symbol"]
            else:
                identity["session_timezone"] = "America/New_York"
                if kind == "bars":
                    identity.update(symbol=request["symbol"], feed="sip", currency="USD", symbol_mapping="disabled_asof_dash", stable_entity_id=None)
            need(equal(data["identity"], identity), "normalized_identity_mismatch")
            coverage = {"requested_start": request["start"], "requested_end": request["end"], "pagination_complete": True,
                        "historical_information": "latest_retrieved_revision_not_point_in_time"}
            rows = data[{"bars": "bars", "calendar": "sessions", "actions": "records"}[kind]]
            sequence(rows, 10_000)
            need(type(receipt["row_count"]) is int and len(rows) == receipt["row_count"], "normalized_count_mismatch")
            if kind == "actions":
                self.categories(data)
                need(data["categories_present"] == receipt["categories_present"] and data["unknown_categories"] == receipt["unknown_categories"])
                coverage.update(date_semantics="process_date_envelope", economic_window_coverage="not_assessed",
                                empty_result=None if rows else "no_records_returned_not_absence_proof")
                pages = {item["page"]: item["raw_sha256"] for item in receipt["pages"]}
                page_counts, occurrence_indices, page_order = {}, {}, []
                for row in rows:
                    obj(row, {"category", "record", "occurrences"})
                    need(row["category"] in data["categories_present"])
                    self.provider_record(row["record"])
                    self.occurrences(ref, row["occurrences"], pages, single=True)
                    occurrence = row["occurrences"][0]
                    ordinal = occurrence["page"]
                    page_counts[ordinal] = page_counts.get(ordinal, 0) + 1
                    occurrence_indices.setdefault((ordinal, row["category"]), []).append(occurrence["index"])
                    page_order.append(ordinal)
                need(page_order == sorted(page_order) and all(count <= 1000 for count in page_counts.values()))
                need(all(indices == list(range(len(indices))) for indices in occurrence_indices.values()), "occurrence_index_sequence_mismatch")
            else:
                need(rows)
                dates, stamps = [], []
                for row in rows:
                    self.r.tick()
                    if kind == "bars":
                        obj(row, {"timestamp", "source_timestamp", "symbol", "open", "high", "low", "close", "volume"})
                        stamp = aware(row["timestamp"])
                        need(aware(row["source_timestamp"]) == stamp)
                        local = stamp.astimezone(ZoneInfo("America/New_York"))
                        need(local.time() == time() and local.isoformat() == row["timestamp"])
                        need(row["symbol"] == request["symbol"])
                        for field in ("open", "high", "low", "close", "volume"):
                            value = row[field]
                            need(type(value) in (int, float) and math.isfinite(value) and (value >= 0 if field == "volume" else value > 0))
                        need(row["low"] <= min(row["open"], row["close"]) <= max(row["open"], row["close"]) <= row["high"])
                        dates.append(day(row["timestamp"][:10]))
                        stamps.append(stamp)
                    else:
                        obj(row, {"date", "open", "close"})
                        date_value = day(row["date"])
                        opening, closing = aware(row["open"]), aware(row["close"])
                        need(opening < closing and opening.date().isoformat() == closing.date().isoformat() == date_value)
                        dates.append(date_value)
                need(dates == sorted(set(dates)) and request["start"] <= dates[0] <= dates[-1] <= request["end"])
                if stamps:
                    need(stamps == sorted(set(stamps)))
                    need(data["price_basis"] == request["adjustment"])
                coverage.update(returned_start=dates[0], returned_end=dates[-1], corporate_actions="unknown",
                    calendar_status="unverified" if kind == "bars" else "provider_calendar_received_not_independently_certified")
            need(equal(data["coverage"], coverage), "normalized_coverage_mismatch")
            self.r.gap("provider_normalization_semantics_not_replayed", ref)
        return supported

    def code_profile(self, ref, code, *, policy=False):
        if type(code) is not dict or type(code.get("sources")) is not dict:
            self.r.gap("policy_producer_origin_unresolved" if policy else "admission_producer_origin_unresolved", ref)
            return None
        sources = code["sources"]
        need(0 < len(sources) <= 32)
        for name, value in sources.items():
            text(name, 1024)
            self.r.edge(ref, "code_identity/sources/" + name, value, "historical_source", "external_evidence")
        if code.get("dependency_lock_sha256") is not None:
            self.r.edge(ref, "code_identity/dependency_lock_sha256", code["dependency_lock_sha256"], "historical_dependency_lock", "external_evidence")
        profile = None
        if policy:
            if sources.get("policy_revision.py") == POLICY_SOURCE:
                need(sources.get("explorer.py") not in {ADMISSION_SOURCES["d006"][1]}, "producer_profile_conflict")
                if sources.get("explorer.py") == ADMISSION_SOURCES["d007"][1]:
                    profile = "d007"
        else:
            for label, (admission, explorer) in ADMISSION_SOURCES.items():
                if sources.get("admission.py") == admission:
                    other = ADMISSION_SOURCES["d007" if label == "d006" else "d006"][1]
                    need(sources.get("explorer.py") != other, "producer_profile_conflict")
                    if sources.get("explorer.py") == explorer:
                        profile = label
        if profile is None:
            self.r.gap("policy_producer_origin_unresolved" if policy else "admission_producer_origin_unresolved", ref)
            return None
        names = {"research.py", "event_engine.py", "explorer.py", "admission.py", "alpaca_data.py", "alpaca_actions.py", "provenance.py", "ledger.py"}
        fields = {"sources", "dependency_lock_sha256", "entrypoint_bytecode_sha256", "loaded_engine_code", "research_engine_globals",
                  "event_entrypoint_bytecode_sha256", "loaded_event_engine_code", "event_engine_globals", "loaded_admission_globals",
                  "loaded_bars_provider_globals", "loaded_actions_provider_globals", "event_policy", "python", "implementation"}
        if profile == "d007":
            names |= {"policy_revision.py", "study_suite.py"}
            fields |= {"loaded_policy_revision_globals", "loaded_study_suite_globals"}
        obj(code, fields)
        need(set(sources) == names, "producer_profile_conflict")
        for field in fields - {"sources", "dependency_lock_sha256", "python", "implementation", "event_policy"}:
            # The historical emitter uses digest maps for loaded functions and
            # digest scalars for entrypoints/globals; none promise content files.
            value = code[field]
            if field in {"entrypoint_bytecode_sha256", "event_entrypoint_bytecode_sha256"}:
                digest(value)
            else:
                need(type(value) is dict)
                if field in {"loaded_engine_code", "loaded_event_engine_code"}:
                    for key, item in value.items():
                        text(key)
                        digest(item)
            self.r.edge(ref, "code_identity/" + field, recovery._sha(recovery._json(value)), "inline_code_identity", "inline_identity")
        need(type(code["event_policy"]) is dict)
        text(code["python"])
        text(code["implementation"])
        self.r.gap("historical_source_environment_required", ref)
        return profile

    def sources(self, ref, data):
        text(data["reviewer"])
        aware(data["reviewed_at"])
        values = sequence(data["sources"], 30)
        need(values)
        found = set()
        for source in values:
            self.manual(ref, source, {"sha256", "url", "title", "locator"}, {"receipt_sha256"})
            source_ref = digest(source["sha256"])
            self.dep(ref, "sources/sha256", source_ref, "opaque_source", nonempty=True)
            url = urlsplit(text(source["url"]))
            need(url.scheme == "https" and url.hostname and not url.username and not url.password)
            text(source["title"])
            text(source["locator"])
            found.add(source_ref)
            if "receipt_sha256" in source:
                receipt_ref = source["receipt_sha256"]
                self.dep(ref, "sources/receipt_sha256", receipt_ref, "public_source_receipt")
                receipt = self.document(receipt_ref)
                if receipt is not None:
                    need(receipt.get("source_sha256") == source_ref and receipt.get("url") == source["url"], "source_receipt_mismatch")
            else:
                self.r.gap("public_source_observation_unverified", ref)
        return found

    def public_source(self, ref, data):
        self.manual(ref, data, {"kind", "source_sha256", "url", "submission_id"}, {"retrieved_at"})
        need(data["kind"] == "public_source_receipt")
        self.dep(ref, "source_sha256", data["source_sha256"], "opaque_source", nonempty=True)
        url = urlsplit(text(data["url"]))
        need(url.scheme == "https" and url.hostname and not url.username and not url.password)
        if "retrieved_at" in data:
            aware(data["retrieved_at"])
        registered = self.registered(ref, "public_source_receipt", "public_source_observation")
        need(not registered or registered == [data["submission_id"]], "source_receipt_mismatch")
        for sid in registered:
            details = self.outcomes[sid]["details"]
            self.manual(ref, details, {"receipt_sha256", "artifact_refs"})
            need({ref, data["source_sha256"]} <= set(details["artifact_refs"]), "source_receipt_mismatch")
        self.r.gap("attributed_source_truth_not_verified", ref)
        return bool(registered) and "schema_version" not in data

    def judgment(self, parent, value, sources, fields=(), *, attributed=False, direct=False):
        required = (ATTRIBUTION if attributed else JUDGMENT) | set(fields)
        self.manual(parent, value, required)
        source = digest(value["source_sha256"])
        need(sources is None or source in sources, "unbound_primary_source")
        self.dep(parent, "judgment/source_sha256", source, "opaque_source", nonempty=True)
        text(value["locator"])
        text(value["judgment"])
        used = {source}
        if attributed:
            text(value["author"])
            aware(value["observed_at"])
            need(value["classification"] in ({"direct"} if direct else {"direct", "inferred"}))
            for support in sequence(value["supporting_sources"], 20):
                self.manual(parent, support, {"source_sha256", "locator"})
                other = digest(support["source_sha256"])
                need(sources is None or other in sources, "unbound_primary_source")
                self.dep(parent, "supporting_sources/source_sha256", other, "opaque_source", nonempty=True)
                text(support["locator"])
                used.add(other)
        return used

    def event(self, value, profile):
        need(type(value) is dict)
        if value.get("kind") == "split":
            obj(value, {"kind", "event_id", "effective_date", "new_rate", "old_rate"})
            day(value["effective_date"])
            rate(value["new_rate"], profile)
            rate(value["old_rate"], profile)
        else:
            obj(value, {"kind", "event_id", "ex_date", "payable_date", "rate", "currency", "share_basis"})
            need(value["kind"] == "cash_dividend" and value["currency"] == "USD" and value["share_basis"] == "ex_date_shares")
            need(day(value["ex_date"]) <= day(value["payable_date"]))
            rate(value["rate"], profile)
        text(value["event_id"])

    def excluded_annotation(self, ref, value, sources):
        fields = {"provider_id", "category", "record_sha256", "effective_date", "acquirer", "acquiree", "completion"}
        self.judgment(ref, value, sources, fields)
        text(value["provider_id"])
        need(value["category"] == "cash_mergers")
        day(value["effective_date"])
        self.r.edge(ref, "excluded_actions/record_sha256", value["record_sha256"], "inline_provider_record", "inline_identity")
        for key in ("acquirer", "acquiree"):
            obj(value[key], {"symbol", "cusip", "isin"})
            need(SYMBOL.fullmatch(text(value[key]["symbol"], 15)))
            for item in ("cusip", "isin"):
                if value[key][item] is not None:
                    text(value[key][item])
        completion = value["completion"]
        self.judgment(ref, completion, sources, {"date", "no_studied_share_conversion", "no_outstanding_studied_entitlement"})
        day(completion["date"])
        need(completion["no_studied_share_conversion"] is True and completion["no_outstanding_studied_entitlement"] is True)

    def facts(self, ref, data, profile):
        self.manual(ref, data, {"schema_version", "kind", "reviewer", "reviewed_at", "sources", "identity", "coverage", "events"},
                    {"excluded_actions", "independent_schedule_sha256"})
        version(data, "attributed_primary_facts")
        sources = self.sources(ref, data)
        identity = data["identity"]
        self.judgment(ref, identity, sources, {"symbol", "instrument_id", "issuer_name", "currency", "continuity_start", "continuity_end"})
        for field in ("symbol", "instrument_id", "issuer_name", "currency"):
            text(identity[field])
        need(day(identity["continuity_start"]) <= day(identity["continuity_end"]))
        coverage = data["coverage"]
        self.judgment(ref, coverage, sources, {"start", "end", "known_events"})
        need(day(coverage["start"]) <= day(coverage["end"]))
        for event in sequence(coverage["known_events"]):
            self.event(event, profile)
        ids, conversions = {}, []
        for annotation in sequence(data["events"]):
            need(type(annotation) is dict and type(annotation.get("event")) is dict)
            self.event(annotation["event"], profile)
            fields = {"provider_id", "event"}
            if annotation["event"]["kind"] == "cash_dividend":
                fields.add("provider_rate_basis")
                need(annotation.get("provider_rate_basis") in {"pre_split_shares", "ex_date_shares"})
                if annotation["provider_rate_basis"] == "pre_split_shares":
                    fields.add("conversion_split_event_id")
                    conversions.append(text(annotation["conversion_split_event_id"]))
                need(not {"regular_way_split", "semantic_review_sha256"} & annotation.keys())
            pair = {"regular_way_split", "semantic_review_sha256"} & annotation.keys()
            if pair:
                need(profile == "d007" and pair == {"regular_way_split", "semantic_review_sha256"}
                     and annotation["event"]["kind"] == "split")
                fields |= pair
                annotation_ref = recovery._sha(recovery._json(annotation["regular_way_split"]))
                self.dep(ref, "events/regular_way_split", annotation_ref, "split_annotation")
                self.dep(ref, "events/semantic_review_sha256", annotation["semantic_review_sha256"], "semantic_review")
                self.at(annotation_ref, "split_annotation", self.annotation, annotation["regular_way_split"], sources)
                terms = annotation["regular_way_split"]["issuer_terms"]
                need(terms["symbol"] == identity["symbol"]
                     and terms["instrument_id"] == identity["instrument_id"],
                     "split_instrument_binding_mismatch")
                review = self.document(annotation["semantic_review_sha256"])
                if review is not None:
                    need(review["annotation_sha256"] == annotation_ref
                         and review["reviewed_calendar_sha256"] == data.get("independent_schedule_sha256"), "semantic_review_binding_mismatch")
            self.judgment(ref, annotation, sources, fields)
            provider_id = text(annotation["provider_id"])
            need(provider_id == annotation["event"]["event_id"] and provider_id not in ids)
            ids[provider_id] = annotation["event"]["kind"]
        need(sorted(coverage["known_events"], key=recovery._json) == sorted([item["event"] for item in data["events"]], key=recovery._json), "primary_event_declaration_mismatch")
        need(all(ids.get(value) == "split" for value in conversions), "conversion_event_binding_mismatch")
        for value in sequence(data.get("excluded_actions", [])):
            self.excluded_annotation(ref, value, sources)
            need(value["provider_id"] not in ids, "duplicate_action_annotation")
            ids[value["provider_id"]] = "excluded"
        if "independent_schedule_sha256" in data:
            self.dep(ref, "independent_schedule_sha256", data["independent_schedule_sha256"], "independent_schedule")
            schedule = self.document(data["independent_schedule_sha256"])
            if schedule is not None:
                self.at(data["independent_schedule_sha256"], "independent_schedule", self.schedule, schedule, sources)
                need(schedule["start"] == coverage["start"] and schedule["end"] == coverage["end"], "schedule_coverage_binding_mismatch")
        self.r.gap("attributed_facts_not_economically_revalidated", ref)
        return True

    def usage(self, ref, data):
        self.manual(ref, data, {"schema_version", "kind", "reviewer", "reviewed_at", "sources", "purpose",
                              "public_distribution", "external_model_transmission", "interpretation", "unresolved"})
        version(data, "source_use_review")
        self.sources(ref, data)
        need(data["purpose"] == "private_own_account_research" and data["public_distribution"] is False and data["external_model_transmission"] is False)
        text(data["interpretation"])
        for item in sequence(data["unresolved"]):
            text(item)
        need("account_and_exchange_terms_not_certified" in data["unresolved"])
        self.r.gap("source_rights_and_external_backup_permission_unverified", ref)
        return True

    def schedule(self, ref, data, sources=None):
        self.manual(ref, data, {"schema_version", "kind", "exchange", "timezone", "start", "end", "source_sha256",
                              "sessions", "early_closes", "extraction", "review"})
        version(data, "independent_exchange_schedule")
        text(data["exchange"])
        need(data["timezone"] == "America/New_York" and day(data["start"]) <= day(data["end"]))
        self.dep(ref, "source_sha256", data["source_sha256"], "opaque_source", nonempty=True)
        need(sources is None or data["source_sha256"] in sources, "unbound_primary_source")
        sessions = sequence(data["sessions"])
        for value in sessions:
            day(value)
        need(sessions and sessions == sorted(set(sessions)) and data["start"] <= sessions[0] <= sessions[-1] <= data["end"])
        extraction = data["extraction"]
        self.judgment(ref, extraction, sources, attributed=True, direct=True)
        need(extraction["source_sha256"] == data["source_sha256"])
        early = data["early_closes"]
        need(type(early) is dict and set(early) <= set(sessions))
        for value in early.values():
            need(type(value) is str and re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value))
        review = data["review"]
        self.manual(ref, review, {"reviewer", "reviewed_at", "verdict", "report_sha256"})
        need(text(review["reviewer"]).strip().casefold() != extraction["author"].strip().casefold()
             and review["verdict"] == "accepted" and aware(review["reviewed_at"]) >= aware(extraction["observed_at"]))
        self.dep(ref, "review/report_sha256", review["report_sha256"], "opaque_report", nonempty=True)
        self.r.gap("attributed_schedule_truth_not_verified", ref)
        return True

    def annotation(self, ref, data, sources=None):
        self.manual(ref, data, {"schema_version", "profile", "author", "observed_at", "provider_id", "record_sha256", "provider_dates",
                              "source_roles", "issuer_terms", "seller_treatment", "purchaser_entitlement", "economic_scope", "rules_applicability", "date_dispositions"},
                    {"additional_event_corroboration"})
        version(data)
        need(data["profile"] == "domestic_integer_forward_split_v1")
        author, observed = text(data["author"]), aware(data["observed_at"])
        text(data["provider_id"])
        self.r.edge(ref, "record_sha256", data["record_sha256"], "inline_provider_record", "inline_identity")
        dates = data["provider_dates"]
        need(type(dates) is dict and DATE_FIELDS <= dates.keys())
        for key, item in dates.items():
            need(key.endswith("_date"))
            obj(item, {"present", "value"})
            need(type(item["present"]) is bool and (item["present"] or item["value"] is None))
            need(item["value"] is None or type(item["value"]) is str)
        roles = data["source_roles"]
        obj(roles, SOURCE_ROLES)
        used, authors = set(), {author.strip().casefold()}
        for key, source in roles.items():
            need(sources is None or source in sources, "unbound_primary_source")
            self.dep(ref, "source_roles/" + key, source, "opaque_source", nonempty=True)
            used.add(source)
        fields = {
            "issuer_terms": {"symbol", "instrument_id", "security_type", "new_rate", "old_rate", "record_date", "distribution_date",
                             "distribution_timing", "first_adjusted_session", "trading_statement"},
            "seller_treatment": {"transfers_attached_interest"}, "purchaser_entitlement": {"receives_attached_interest"},
            "economic_scope": {"same_security_and_market", "separate_entitlement_market", "additional_claims_or_cash", "elections", "fractional_cash_in_lieu"},
            "rules_applicability": {"regime_start"}}
        items = []
        for key, extras in fields.items():
            value = data[key]
            used.update(self.judgment(ref, value, sources, extras, attributed=True, direct=key in {"issuer_terms", "seller_treatment"}))
            items.append(value)
        terms = data["issuer_terms"]
        for key in ("symbol", "instrument_id"):
            text(terms[key])
        need(terms["source_sha256"] == roles["issuer"] and terms["security_type"] == "domestic_common_stock"
             and terms["distribution_timing"] == "after_close" and terms["trading_statement"] == "expected_or_scheduled")
        for key in ("record_date", "distribution_date", "first_adjusted_session"):
            day(terms[key])
        rate(terms["new_rate"], "d007")
        rate(terms["old_rate"], "d007")
        need(data["seller_treatment"]["transfers_attached_interest"] is True and data["purchaser_entitlement"]["receives_attached_interest"] is True)
        for key in fields["economic_scope"]:
            need(data["economic_scope"][key] is (key == "same_security_and_market"))
        need(data["rules_applicability"]["regime_start"] == "2024-05-28")
        dispositions = data["date_dispositions"]
        obj(dispositions, {"record_date", "payable_date", "due_bill_redemption_date"})
        for key, item in dispositions.items():
            extras = {"status", "controlling_terms_established", "explanation"}
            if key == "due_bill_redemption_date":
                extras |= {"documented_meaning", "actual_outcome", "transformation_trigger"}
                need(item.get("documented_meaning") == "delivery_obligations" and item.get("actual_outcome") == "unverified"
                     and item.get("transformation_trigger") == "issuer_first_adjusted_session")
            used.update(self.judgment(ref, item, sources, extras, attributed=True))
            need(item["controlling_terms_established"] is True and item["status"] in {"matches_issuer_date", "unresolved_ancillary_date_discrepancy"})
            text(item["explanation"])
            items.append(item)
        for value in sequence(data.get("additional_event_corroboration", []), 5):
            used.update(self.judgment(ref, value, sources, attributed=True, direct=True))
            items.append(value)
        for value in items:
            need(aware(value["observed_at"]) <= observed)
            authors.add(value["author"].strip().casefold())
        self.r.gap("attributed_split_economics_not_revalidated", ref)
        return used, authors

    def semantic_review(self, ref, data):
        self.manual(ref, data, {"schema_version", "kind", "annotation_sha256", "author", "reviewer", "reviewer_kind", "reviewed_at",
                              "verdict", "reviewed_sources", "reviewed_calendar_sha256", "report_sha256"})
        version(data, "regular_way_split_semantic_review")
        self.dep(ref, "annotation_sha256", data["annotation_sha256"], "split_annotation")
        self.dep(ref, "reviewed_calendar_sha256", data["reviewed_calendar_sha256"], "independent_schedule")
        self.dep(ref, "report_sha256", data["report_sha256"], "opaque_report", nonempty=True)
        for source in sequence(data["reviewed_sources"], 200):
            self.dep(ref, "reviewed_sources", source, "opaque_source", nonempty=True)
        need(data["reviewed_sources"] == sorted(set(data["reviewed_sources"])))
        need(data["reviewer_kind"] == "native_agent" and data["verdict"] in {"accepted", "accepted_with_qualifications"})
        text(data["author"])
        text(data["reviewer"])
        aware(data["reviewed_at"])
        annotation, schedule = self.document(data["annotation_sha256"]), self.document(data["reviewed_calendar_sha256"])
        if annotation is not None:
            need(recovery._sha(recovery._json(annotation)) == data["annotation_sha256"], "noncanonical_annotation_identity")
            used, authors = self.at(data["annotation_sha256"], "split_annotation", self.annotation, annotation)
            need(data["author"] == annotation["author"] and data["reviewer"].strip().casefold() not in authors)
            need(aware(data["reviewed_at"]) >= aware(annotation["observed_at"]))
            if schedule is not None:
                need(data["reviewed_sources"] == sorted(used | {schedule["source_sha256"]}), "semantic_review_sources_mismatch")
        if schedule is not None:
            need(aware(data["reviewed_at"]) >= aware(schedule["review"]["reviewed_at"]))
        registered = self.registered(ref, "semantic_review", "regular_way_split_semantic_review")
        for sid in registered:
            details = self.outcomes[sid]["details"]
            obj(details, {"review_sha256", "request_sha256", "annotation_sha256", "artifact_refs"})
            need(details["annotation_sha256"] == data["annotation_sha256"], "semantic_review_binding_mismatch")
            self.original(ref, details["request_sha256"], sid, {"review_sha256": ref})
            need({ref, data["annotation_sha256"], data["reviewed_calendar_sha256"], data["report_sha256"],
                  details["request_sha256"], *data["reviewed_sources"]} <= set(details["artifact_refs"]), "semantic_review_binding_mismatch")
        self.r.gap("attributed_review_identity_not_authenticated", ref)
        return bool(registered)

    def admission_request(self, ref, request, profile):
        obj(request, ADMISSION_REQUEST, {"policy_revision_sha256"} if profile == "d007" else ())
        obj(request["submitted_requests"], {"bars", "calendar", "actions"})
        self.dep(ref, "dataset_sha256", request["dataset_sha256"], "dataset")
        self.dep(ref, "primary_facts_sha256", request["primary_facts_sha256"], "primary_facts_" + profile)
        self.dep(ref, "usage_review_sha256", request["usage_review_sha256"], "source_use_review")
        if "policy_revision_sha256" in request:
            self.dep(ref, "policy_revision_sha256", request["policy_revision_sha256"], "policy_revision")
        receipts = {}
        for kind in ("bars", "calendar", "actions"):
            receipt_ref = request[kind + "_receipt_sha256"]
            self.dep(ref, kind + "_receipt_sha256", receipt_ref, "acquisition_receipt")
            receipt = self.document(receipt_ref)
            if receipt is not None:
                need(receipt.get("kind") == kind and receipt.get("status") == "success", "admission_receipt_binding_mismatch")
                sid = receipt["submission_id"]
                self.registration(sid, "alpaca_" + kind, "success")
                need(self.outcomes[sid]["details"]["receipt_sha256"] == receipt_ref, "admission_receipt_binding_mismatch")
                original = self.original(ref, request["submitted_requests"][kind], sid)
                if original is not None:
                    expected = {key: receipt["request"][key] for key in ("symbol", "start", "end")} if kind == "actions" else receipt["request"]
                    if kind == "bars":
                        # Historical bars inputs may omit the fixed parameters;
                        # compare only their exact documented input contract.
                        obj(original, {"symbol", "start", "end"}, {"adjustment", "timeframe", "feed", "currency", "asof"})
                        need(original.get("adjustment", "raw") == expected["adjustment"])
                        expected = {key: expected[key] for key in original}
                    need(equal(original, expected), "original_request_content_mismatch")
                receipts[kind] = receipt
            else:
                self.dep(ref, "submitted_requests/" + kind, request["submitted_requests"][kind], "original_request")
        return receipts

    def unresolved_references(self, ref, data, *, policy=False):
        # These are declarations only. Their spelling never selects a verified
        # writer; independently registered child receipts may select themselves.
        if "artifact_refs" in data:
            self.r.refs(ref, "artifact_refs", data["artifact_refs"])
        request = data.get("request")
        if type(request) is not dict:
            return
        if policy:
            for field in ("accepted_decision_sha256", "new_primary_facts_sha256"):
                if field in request:
                    self.dep(ref, "unverified_request/" + field, request[field], "declared")
            if "review_sha256s" in request:
                self.r.refs(ref, "unverified_request/review_sha256s", request["review_sha256s"])
            for key, field, role in (("predecessor_plans", "plan_sha256", "predecessor_plan"),
                                     ("refused_admissions", "request_sha256", "original_request")):
                for value in sequence(request.get(key, []), 32):
                    if type(value) is dict and field in value:
                        self.dep(ref, "unverified_request/" + key, value[field], role)
        else:
            for field in ("dataset_sha256", "primary_facts_sha256", "usage_review_sha256", "policy_revision_sha256"):
                if field in request:
                    self.dep(ref, "unverified_request/" + field, request[field], "declared")
            for kind in ("bars", "calendar", "actions"):
                field = kind + "_receipt_sha256"
                if field in request:
                    self.dep(ref, "unverified_request/" + field, request[field], "acquisition_receipt")
            if type(request.get("submitted_requests")) is dict:
                for key in ("bars", "calendar", "actions"):
                    if key in request["submitted_requests"]:
                        self.dep(ref, "unverified_request/submitted_requests/" + key, request["submitted_requests"][key], "original_request")

    def admission(self, ref, data):
        profile = self.code_profile(ref, data.get("code_identity"))
        if profile is None:
            self.unresolved_references(ref, data)
            self.r.gap("unsupported_admission_profile", ref)
            return False
        fields = {"schema_version", "kind", "request", "dataset_sha256", "scope", "rules", "code_identity", "actions", "excluded_actions", "sessions",
                  "full_acquired_exposure", "market", "request_parameters_sha256", "limitations", "artifact_refs"}
        if profile == "d007":
            fields.add("accepted_action_treatments")
        obj(data, fields, {"policy_revision_sha256", "policy_revision"} if profile == "d007" else ())
        version(data, "historical_admission")
        need(equal(data["rules"], ADMISSION_RULES[profile]) and data["scope"] == ADMISSION_RULES[profile]["scope"], "admission_rule_mismatch")
        need(data["dataset_sha256"] == data["request"]["dataset_sha256"])
        receipts = self.admission_request(ref, data["request"], profile)
        self.r.refs(ref, "artifact_refs", data["artifact_refs"])
        registered = self.registered(ref, "admission", "historical_admission")
        for sid in registered:
            details = self.outcomes[sid]["details"]
            obj(details, {"admission_sha256", "dataset_sha256", "scope", "artifact_refs"})
            need(details["dataset_sha256"] == data["dataset_sha256"] and details["scope"] == data["scope"]
                 and {ref, *data["artifact_refs"]} <= set(details["artifact_refs"]), "admission_registration_mismatch")
            self.original(ref, self.submissions[sid]["request_sha256"], sid, data["request"], promised=False)
        for item in sequence(data["actions"]):
            self.event(item, profile)
        sessions = sequence(data["sessions"])
        for value in sessions:
            day(value)
        need(sessions and sessions == sorted(set(sessions)))
        obj(data["full_acquired_exposure"], {"start", "end"})
        start, end = (day(data["full_acquired_exposure"][key]) for key in ("start", "end"))
        need(start <= sessions[0] <= sessions[-1] <= end)
        obj(data["market"], {"instrument_id", "venue", "currency", "session_timezone"})
        for value in data["market"].values():
            text(value)
        for item in sequence(data["limitations"]):
            text(item)
        dataset = self.document(data["dataset_sha256"])
        if dataset is not None:
            need(data["market"]["currency"] == "USD" and data["market"]["session_timezone"] == "America/New_York")
            need(data["market"] == dataset["market"] and data["sessions"] == dataset["sessions"]
                 and start == dataset["exposure_start"] and end == dataset["exposure_end"], "admission_dataset_binding_mismatch")
        if set(receipts) == {"bars", "calendar", "actions"}:
            self.r.inline(ref, "request_parameters_sha256", data["request_parameters_sha256"], {kind: value["request"] for kind, value in receipts.items()})
            bars = receipts["bars"]
            need(bars["request"]["adjustment"] == data["rules"]["price_basis"]
                 and receipts["actions"]["request"]["symbol"] == bars["request"]["symbol"])
            need(bars["request"]["start"] == start and bars["request"]["end"] == end
                 and receipts["calendar"]["request"] == {"start": start, "end": end})
            if dataset is not None:
                need(dataset["source_sha256"] == bars["normalized_sha256"] and dataset["symbol"] == bars["request"]["symbol"]
                     and dataset["price_basis"] == bars["request"]["adjustment"])
            calendar = self.document(receipts["calendar"]["normalized_sha256"])
            if calendar is not None:
                need(data["sessions"] == [row["date"] for row in calendar["sessions"]])
        else:
            self.r.edge(ref, "request_parameters_sha256", data["request_parameters_sha256"], "inline_request_parameters", "inline_identity")
            self.r.gap("request_parameter_identity_unavailable", ref)
        facts = self.document(data["request"]["primary_facts_sha256"])
        sources = {item["sha256"] for item in facts["sources"]} if facts else None
        if facts is not None:
            need(facts["coverage"]["start"] == start and facts["coverage"]["end"] == end
                 and facts["identity"]["instrument_id"] == data["market"]["instrument_id"])
            need(facts["identity"]["currency"] == data["market"]["currency"]
                 and facts["identity"]["continuity_start"] <= start <= end <= facts["identity"]["continuity_end"])
            if dataset is not None:
                need(facts["identity"]["symbol"] == dataset["symbol"], "facts_symbol_binding_mismatch")
            need(sorted(data["actions"], key=recovery._json) == sorted(facts["coverage"]["known_events"], key=recovery._json))
        action_doc = self.document(receipts["actions"]["normalized_sha256"]) if "actions" in receipts else None
        records = {}
        if action_doc is not None:
            for item in action_doc["records"]:
                record = item["record"]
                identity = record.get("id")
                if identity in records:
                    need(equal(records[identity]["record"], record) and records[identity]["category"] == item["category"], "conflicting_provider_record_identity")
                    records[identity]["occurrences"].extend(item["occurrences"])
                else:
                    records[identity] = {**item, "occurrences": list(item["occurrences"])}
        for item in sequence(data["excluded_actions"]):
            obj(item, {"reason", "annotation", "record_sha256", "occurrences"})
            need(item["reason"] == "completed_pre_window_acquirer_cash_merger")
            self.excluded_annotation(ref, item["annotation"], sources)
            need(item["record_sha256"] == item["annotation"]["record_sha256"], "excluded_record_binding_mismatch")
            if facts is not None:
                need(any(equal(item["annotation"], declared) for declared in facts.get("excluded_actions", [])), "excluded_annotation_binding_mismatch")
            self.record_summary(ref, item, records, item["annotation"]["provider_id"])
        for treatment in sequence(data.get("accepted_action_treatments", [])):
            obj(treatment, {"profile", "provider_id", "annotation", "annotation_sha256", "provider_record", "record_sha256", "occurrences", "ratio",
                            "semantic_review_sha256", "independent_schedule_sha256", "date_dispositions", "additional_event_corroboration_status", "limitations"})
            annotation = treatment["annotation"]
            need(treatment["profile"] == annotation["profile"] and treatment["provider_id"] == annotation["provider_id"])
            self.r.inline(ref, "treatment/annotation_sha256", treatment["annotation_sha256"], annotation)
            self.dep(ref, "treatment/annotation_sha256", treatment["annotation_sha256"], "split_annotation")
            self.at(treatment["annotation_sha256"], "split_annotation", self.annotation, annotation, sources)
            terms = annotation["issuer_terms"]
            need(terms["instrument_id"] == data["market"]["instrument_id"],
                 "split_instrument_binding_mismatch")
            if dataset is not None:
                need(terms["symbol"] == dataset["symbol"], "split_instrument_binding_mismatch")
            if "bars" in receipts:
                need(terms["symbol"] == receipts["bars"]["request"]["symbol"],
                     "split_instrument_binding_mismatch")
            self.r.inline(ref, "treatment/record_sha256", treatment["record_sha256"], treatment["provider_record"])
            need(annotation["record_sha256"] == treatment["record_sha256"])
            record = treatment["provider_record"]
            expected_dates = {key: {"present": key in record, "value": record.get(key)} for key in DATE_FIELDS | {key for key in record if key.endswith("_date")}}
            need(equal(annotation["provider_dates"], expected_dates), "provider_date_binding_mismatch")
            self.record_summary(ref, treatment, records, treatment["provider_id"])
            text(treatment["ratio"], 101)
            need(re.fullmatch(r"[1-9][0-9]*", treatment["ratio"]))
            need(equal(treatment["date_dispositions"], annotation["date_dispositions"]) and treatment["limitations"] == SPLIT_LIMITATIONS)
            need(treatment["additional_event_corroboration_status"] == ("retained_attributed" if annotation.get("additional_event_corroboration") else "not_supplied"))
            for field, role in (("semantic_review_sha256", "semantic_review"), ("independent_schedule_sha256", "independent_schedule")):
                self.dep(ref, "treatment/" + field, treatment[field], role)
            review = self.document(treatment["semantic_review_sha256"])
            if review is not None:
                need(review["annotation_sha256"] == treatment["annotation_sha256"] and review["reviewed_calendar_sha256"] == treatment["independent_schedule_sha256"])
                review_sids = self.registered(treatment["semantic_review_sha256"], "semantic_review", "regular_way_split_semantic_review")
                for sid in registered:
                    need(any(self.registration(other)[1] < self.registration(sid)[0] for other in review_sids), "semantic_review_registration_order")
            schedule = self.document(treatment["independent_schedule_sha256"])
            if schedule is not None:
                need(schedule["sessions"] == data["sessions"] and schedule["start"] == start and schedule["end"] == end, "schedule_admission_binding_mismatch")
            if facts is not None:
                need(facts["independent_schedule_sha256"] == treatment["independent_schedule_sha256"])
                matches = [item for item in facts["events"] if item["provider_id"] == treatment["provider_id"]]
                need(len(matches) == 1 and equal(matches[0]["regular_way_split"], annotation)
                     and matches[0]["semantic_review_sha256"] == treatment["semantic_review_sha256"])
        if facts is not None:
            need(sorted(item["provider_id"] for item in data.get("accepted_action_treatments", []))
                 == sorted(item["provider_id"] for item in facts["events"] if "regular_way_split" in item), "accepted_treatment_binding_mismatch")
        paired = {"policy_revision_sha256", "policy_revision"} & data.keys()
        need(not paired or paired == {"policy_revision_sha256", "policy_revision"})
        need(("policy_revision_sha256" in data["request"]) == bool(paired))
        if paired:
            revision_ref = data["policy_revision_sha256"]
            need(revision_ref == data["request"]["policy_revision_sha256"])
            self.dep(ref, "policy_revision_sha256", revision_ref, "policy_revision")
            embedded = data["policy_revision"]
            need(type(embedded) is dict and embedded.get("policy_revision_sha256") == revision_ref)
            stored = self.document(revision_ref)
            if stored is not None:
                need(equal({key: value for key, value in embedded.items() if key != "policy_revision_sha256"}, stored), "embedded_policy_revision_mismatch")
                expected = {**stored["lineage"]["prior_refusals"][-1]["request"], "primary_facts_sha256": stored["request"]["new_primary_facts_sha256"], "policy_revision_sha256": revision_ref}
                need(equal(data["request"], expected), "policy_admission_request_mismatch")
            for sid in registered:
                policy_sids = self.registered(revision_ref, "policy_revision", "policy_revision")
                need(any(self.registration(other)[1] < self.registration(sid)[0] for other in policy_sids), "policy_revision_registration_order")
        self.r.gap("admission_economic_semantics_not_revalidated", ref)
        return bool(registered)

    def record_summary(self, ref, item, records, provider_id):
        digest(item["record_sha256"])
        self.r.edge(ref, "record_sha256", item["record_sha256"], "inline_provider_record", "inline_identity")
        self.occurrences(ref, item["occurrences"])
        if provider_id in records:
            record = records[provider_id]
            self.r.inline(ref, "record_sha256", item["record_sha256"], record["record"])
            need(equal(item["occurrences"], record["occurrences"]), "record_occurrences_mismatch")
        else:
            self.r.gap("inline_provider_record_binding_unavailable", ref)

    def frozen(self, value):
        obj(value, FROZEN_FIELDS)
        need(equal(value["cost_bps_scenarios"], [0, 10, 25]) and value["basis"] == "raw")
        need(type(value["lookback"]) is int and value["lookback"] > 0)
        for field in ("starting_cash", "entry_threshold", "exit_threshold"):
            need(type(value[field]) in (int, float) and math.isfinite(value[field]))
        need(value["starting_cash"] > 0)
        dates = [day(value[field]) for field in ("data_start", "evaluation_start", "evaluation_end", "data_end")]
        need(dates == sorted(dates))
        need(type(value["sma_includes_current_close"]) is bool)
        text(value["instrument"])
        # Remaining mechanical/accounting declarations are bounded retained JSON;
        # historical consumers do not impose a universal text-only schema.
        # No strategy constructor or arithmetic is used to reinterpret them.

    def plan(self, ref, data):
        # No committed universal manual-plan producer exists. These named
        # consumer paths are inventoried while the remaining origin stays open.
        self.r.gap("manual_plan_fields_and_origin_unverified", ref)
        links = [data[key] for key in ("previous_plan_bytes_sha256", "previous_plan_sha256") if key in data]
        need(len(links) <= 1, "ambiguous_plan_predecessor")
        if links and links[0] is not None:
            self.dep(ref, "previous_plan", links[0], "predecessor_plan")
        if "relevance_refinement" in data:
            value = data["relevance_refinement"]
            self.manual(ref, value, {"kind", "original_admission_refusal", "facts_sha256", "portfolio_result_observed_before_refinement", "strategy_window_costs_unchanged"})
            self.dep(ref, "relevance_refinement/facts_sha256", value["facts_sha256"], "primary_facts_d006")
            self.registration(value["original_admission_refusal"], "historical_admission", "invalid")
        return True

    def facts_delta(self, ref, previous, current):
        need("independent_schedule_sha256" not in previous
             and set(current) == set(previous) | {"independent_schedule_sha256"}, "non_additive_facts_lineage")
        for key, value in previous.items():
            if key not in {"sources", "events"}:
                need(equal(current[key], value), "non_additive_facts_lineage")
        before_sources, after_sources = sequence(previous["sources"], 30), sequence(current["sources"], 30)
        need(len(after_sources) >= len(before_sources) and equal(after_sources[:len(before_sources)], before_sources), "non_additive_facts_lineage")
        need(len({recovery._sha(recovery._json(item)) for item in after_sources}) == len(after_sources))
        result = [{"path": f"$.sources[{index}]", "operation": "add", "value": after_sources[index]}
                  for index in range(len(before_sources), len(after_sources))]
        before_events, after_events = sequence(previous["events"]), sequence(current["events"])
        need(len(before_events) == len(after_events), "non_additive_facts_lineage")
        changed = 0
        for index, (before, after) in enumerate(zip(before_events, after_events, strict=True)):
            self.r.tick()
            if equal(before, after):
                continue
            additions = {"regular_way_split", "semantic_review_sha256"}
            need(not additions & before.keys() and set(after) == set(before) | additions
                 and all(equal(after[key], value) for key, value in before.items())
                 and before.get("event", {}).get("kind") == "split", "non_additive_facts_lineage")
            for key in sorted(additions):
                result.append({"path": f"$.events[{index}].{key}", "operation": "add", "value": after[key]})
            self.dep(ref, "facts_delta/semantic_review_sha256", after["semantic_review_sha256"], "semantic_review")
            self.dep(ref, "facts_delta/regular_way_split", recovery._sha(recovery._json(after["regular_way_split"])), "split_annotation")
            changed += 1
        need(changed == 1, "non_additive_facts_lineage")
        self.dep(ref, "facts_delta/independent_schedule_sha256", current["independent_schedule_sha256"], "independent_schedule")
        result.append({"path": "$.independent_schedule_sha256", "operation": "add", "value": current["independent_schedule_sha256"]})
        return result

    def policy(self, ref, data):
        profile = self.code_profile(ref, data.get("code_identity"), policy=True)
        if profile is None:
            self.unresolved_references(ref, data, policy=True)
            self.r.gap("unsupported_policy_revision_profile", ref)
            return False
        obj(data, {"schema_version", "kind", "request", "rules", "code_identity", "dataset_sha256", "frozen_study", "facts_delta", "lineage", "artifact_refs"})
        version(data, "policy_revision")
        need(equal(data["rules"], POLICY_RULES), "policy_rule_mismatch")
        request = data["request"]
        obj(request, {"schema_version", "kind", "predecessor_plans", "refused_admissions", "accepted_decision_sha256", "review_sha256s",
                      "new_primary_facts_sha256", "frozen_study", "classification"})
        version(request, "policy_revision_request")
        need(request["classification"] == POLICY_RULES["classification"])
        need(request["accepted_decision_sha256"] == POLICY_RULES["accepted_decision_sha256"], "accepted_decision_mismatch")
        review_refs = sequence(request["review_sha256s"], 20)
        need(review_refs and len(set(review_refs)) == len(review_refs)
             and set(POLICY_RULES["approved_review_sha256s"].values()) <= set(review_refs))
        for value in [request["accepted_decision_sha256"], *review_refs]:
            self.dep(ref, "policy_evidence", value, "opaque_policy_evidence", nonempty=True)
        self.dep(ref, "new_primary_facts_sha256", request["new_primary_facts_sha256"], "primary_facts_d007")
        self.dep(ref, "dataset_sha256", data["dataset_sha256"], "dataset")
        self.r.refs(ref, "artifact_refs", data["artifact_refs"])
        self.frozen(data["frozen_study"])
        need(equal(data["frozen_study"], request["frozen_study"]))
        frozen = data["frozen_study"]
        lineage = data["lineage"]
        obj(lineage, {"plans", "prior_refusals", "acquisitions", "post_acquisition_change_count", "current_change", "classification"})
        need(lineage["classification"] == POLICY_RULES["classification"] and lineage["current_change"] == "financial_policy_revision")
        registered = self.registered(ref, "policy_revision", "policy_revision")
        for sid in registered:
            details = self.outcomes[sid]["details"]
            obj(details, {"policy_revision_sha256", "request_sha256", "dataset_sha256", "post_acquisition_change_count", "artifact_refs"})
            need(details["dataset_sha256"] == data["dataset_sha256"]
                 and equal(details["post_acquisition_change_count"], lineage["post_acquisition_change_count"])
                 and {ref, details["request_sha256"], *data["artifact_refs"]} <= set(details["artifact_refs"]), "policy_registration_mismatch")
            self.original(ref, details["request_sha256"], sid, request)
        entries = sequence(request["refused_admissions"], 32)
        need(len(entries) >= 2)
        refusals = []
        incomplete = False
        for index, entry in enumerate(entries):
            obj(entry, {"submission_id", "request_sha256"})
            sid = entry["submission_id"]
            start, finish = self.registration(sid, "historical_admission", "invalid")
            code = self.outcomes[sid]["details"]["error_code"]
            text(code)
            need((index != 0 or code == "identity_change_unresolved")
                 and (index != len(entries) - 1 or code == "unsupported_due_bill"), "refusal_history_mismatch")
            need(not refusals or refusals[-1]["finished_event"] < start, "refusal_event_order")
            prior_request = self.original(ref, entry["request_sha256"], sid)
            self.dep(ref, "prior_refusals/request_sha256", entry["request_sha256"], "admission_request_d006")
            if prior_request is None:
                incomplete = True
            else:
                self.admission_request(ref, prior_request, "d006")
            refusals.append({**entry, "error_code": code, "started_event": start, "finished_event": finish, "request": prior_request})
        observed_refusals = sequence(lineage["prior_refusals"], 32)
        need(len(observed_refusals) == len(refusals))
        for observed, expected in zip(observed_refusals, refusals, strict=True):
            obj(observed, {"submission_id", "request_sha256", "error_code", "started_event", "finished_event", "request"})
            if expected["request"] is None:
                need(equal({k: v for k, v in observed.items() if k != "request"}, {k: v for k, v in expected.items() if k != "request"}), "refusal_lineage_mismatch")
                # This embedded claim does not replace required missing bytes.
                self.admission_request(ref, observed["request"], "d006")
            else:
                need(equal(observed, expected), "refusal_lineage_mismatch")
        prior = observed_refusals[-1]["request"]
        unchanged = ADMISSION_REQUEST - {"primary_facts_sha256"}
        need(all(all(equal(item["request"][key], prior[key]) for key in unchanged) for item in observed_refusals), "refusal_request_changed")
        need(data["dataset_sha256"] == prior["dataset_sha256"])
        obj(lineage["acquisitions"], {"bars", "calendar", "actions"})
        acquisitions = {}
        for kind in ("bars", "calendar", "actions"):
            item = lineage["acquisitions"][kind]
            obj(item, {"submission_id", "receipt_sha256", "submitted_request_sha256", "normalized_sha256", "started_event", "finished_event"})
            start, finish = self.registration(item["submission_id"], "alpaca_" + kind, "success")
            need(type(item["started_event"]) is int and type(item["finished_event"]) is int
                 and item["started_event"] == start and item["finished_event"] == finish)
            need(item["receipt_sha256"] == prior[kind + "_receipt_sha256"]
                 and item["submitted_request_sha256"] == prior["submitted_requests"][kind], "policy_acquisition_binding_mismatch")
            self.dep(ref, "lineage/acquisitions/receipt_sha256", item["receipt_sha256"], "acquisition_receipt")
            self.dep(ref, "lineage/acquisitions/normalized_sha256", item["normalized_sha256"], "normalized_observation")
            self.original(ref, item["submitted_request_sha256"], item["submission_id"])
            receipt = self.document(item["receipt_sha256"])
            if receipt is not None:
                need(receipt["normalized_sha256"] == item["normalized_sha256"] and receipt["submission_id"] == item["submission_id"])
            acquisitions[kind] = item
        need(max(item["finished_event"] for item in acquisitions.values()) < refusals[0]["started_event"], "refusal_precedes_acquisition")
        acquisition_start = min(item["started_event"] for item in acquisitions.values())
        plan_entries = sequence(request["predecessor_plans"], 16)
        need(len(plan_entries) >= 2)
        plans, previous, previous_data, seen, changes = [], None, None, set(), 0
        for entry in plan_entries:
            obj(entry, {"plan_sha256", "submission_id"})
            plan_ref, sid = digest(entry["plan_sha256"]), entry["submission_id"]
            need(plan_ref not in seen, "cyclic_predecessor_chain")
            seen.add(plan_ref)
            self.dep(ref, "predecessor_plans/plan_sha256", plan_ref, "predecessor_plan")
            start, finish = self.registration(sid, {"pilot_plan_registration", "pilot_plan_refinement"}, "success")
            out = self.outcomes[sid]
            details = out["details"]
            need(details.get("plan_sha256") == plan_ref and plan_ref in details["artifact_refs"] and details.get("financial_result") is False, "plan_registration_mismatch")
            self.r.refs(ref, "plan_registration/artifact_refs", details["artifact_refs"])
            need(not plans or plans[-1]["finished_event"] < start, "plan_event_order")
            post = start > acquisition_start
            kind = self.submissions[sid]["kind"]
            if post:
                changes += 1
                need(kind == "pilot_plan_refinement" and refusals[0]["finished_event"] < start < finish < refusals[-1]["started_event"], "plan_refinement_order")
            else:
                need(kind == "pilot_plan_registration" and finish < acquisition_start, "plan_acquisition_order")
            plan = self.document(plan_ref)
            if plan is not None:
                links = [plan[key] for key in ("previous_plan_bytes_sha256", "previous_plan_sha256") if key in plan]
                need((not links and previous is None) or len(links) == 1 and links[0] == previous, "plan_predecessor_mismatch")
                need(all(equal(plan[key], frozen[key]) for key in FROZEN_FIELDS if key in plan), "plan_frozen_fields_mismatch")
                if post:
                    refinement = plan.get("relevance_refinement", {})
                    need(refinement.get("kind") == "implementation_of_preexisting_structured_exclusion"
                         and refinement.get("original_admission_refusal") == refusals[0]["submission_id"]
                         and refinement.get("facts_sha256") == prior["primary_facts_sha256"]
                         and refinement.get("portfolio_result_observed_before_refinement") is False
                         and refinement.get("strategy_window_costs_unchanged") is True, "plan_refinement_mismatch")
                    if previous_data is not None:
                        mutable = {"status", "previous_plan_bytes_sha256", "previous_plan_sha256"}
                        additions = {"relevance_refined_at", "relevance_refinement"}
                        need(set(plan) - set(previous_data) <= additions | mutable and set(previous_data) <= set(plan)
                             and all(equal(plan[key], value) for key, value in previous_data.items() if key not in mutable), "non_additive_plan_refinement")
                if entry == plan_entries[-1]:
                    need(all(key in plan and equal(plan[key], value) for key, value in frozen.items()), "latest_plan_frozen_fields_mismatch")
            else:
                incomplete = True
            plans.append({**entry, "registration_kind": kind, "started_event": start, "finished_event": finish,
                          "classification": "post_acquisition_implementation_refinement" if post else "pre_acquisition_plan"})
            previous, previous_data = plan_ref, plan
        need(changes >= 1 and type(lineage["post_acquisition_change_count"]) is int
             and lineage["post_acquisition_change_count"] == changes + 1, "policy_change_count_mismatch")
        need(equal(lineage["plans"], plans), "plan_lineage_mismatch")
        for sid in registered:
            need(max(refusals[-1]["finished_event"], plans[-1]["finished_event"]) < self.registration(sid)[0], "policy_event_order")
        old_facts = self.document(prior["primary_facts_sha256"])
        new_facts = self.document(request["new_primary_facts_sha256"])
        for value in sequence(data["facts_delta"]):
            obj(value, {"path", "operation", "value"})
            need(value["operation"] == "add" and type(value["path"]) is str
                 and re.fullmatch(r"\$\.(?:sources\[[0-9]+\]|events\[[0-9]+\]\.(?:regular_way_split|semantic_review_sha256)|independent_schedule_sha256)", value["path"]), "unsupported_facts_delta_path")
        if old_facts is not None and new_facts is not None:
            need(equal(data["facts_delta"], self.facts_delta(ref, old_facts, new_facts)), "facts_delta_mismatch")
        else:
            incomplete = True
        dataset = self.document(data["dataset_sha256"])
        if dataset is not None:
            need(frozen["instrument"] == dataset["symbol"] and frozen["data_start"] == dataset["exposure_start"]
                 and frozen["data_end"] == dataset["exposure_end"] and frozen["basis"] == dataset["price_basis"], "policy_dataset_binding_mismatch")
        if incomplete:
            self.r.gap("policy_lineage_binding_unavailable", ref)
        self.r.gap("policy_economic_semantics_not_revalidated", ref)
        return bool(registered) and not incomplete

    def handle(self, ref, role, data):
        if role == "acquisition_receipt":
            return self.receipt(ref, data)
        if role == "acquisition_request":
            return self.prepared_request(ref, data)
        if role in {"normalized_observation", "dataset_source"}:
            return self.normalized(ref, data)
        if role == "admission":
            return self.admission(ref, data)
        if role == "policy_revision":
            return self.policy(ref, data)
        if role == "public_source_receipt":
            return self.public_source(ref, data)
        if role == "semantic_review":
            return self.semantic_review(ref, data)
        if role.startswith("primary_facts_"):
            return self.facts(ref, data, role.removeprefix("primary_facts_"))
        if role == "source_use_review":
            return self.usage(ref, data)
        if role == "independent_schedule":
            return self.schedule(ref, data)
        if role == "split_annotation":
            self.annotation(ref, data)
            return True
        if role == "predecessor_plan":
            return self.plan(ref, data)
        if role == "admission_request_d006":
            self.admission_request(ref, data, "d006")
            return True
        if role == "original_request":
            # Its binding is checked by each explicit consuming registration.
            if ref in self.original_bindings:
                return True
            self.r.gap("original_request_requires_consumer_binding", ref)
            return False
        need(False, "unknown_lineage_role")

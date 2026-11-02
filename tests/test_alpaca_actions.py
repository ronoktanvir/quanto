"""Synthetic action observations test acquisition, never market performance."""
from datetime import datetime, timezone
import hashlib
import json
from urllib.parse import parse_qs, urlsplit

import pytest

from quanto import alpaca_actions as actions
from quanto import alpaca_data as data
from quanto.provenance import Provenance, ProvenanceError

KEYS = data.Credentials("fixture-paper-key-12345", "fixture-secret-key-12345")
NOW = datetime(2025, 1, 20, tzinfo=timezone.utc)
REQUEST = {"symbol": "AAPL", "start": "2016-01-01", "end": "2025-01-20"}


def record(**changes):
    value = {"id": "id-1", "symbol": "AAPL", "process_date": "2024-06-03",
             "ex_date": "2024-06-04", "rate": 0.25, "currency": "USD"}
    value.update(changes)
    return value


def page(categories=None, token=None):
    value = {"corporate_actions": {"cash_dividends": [record()]} if categories is None
             else categories, "next_page_token": token}
    return data.HTTPResult(200, json.dumps(value).encode())


@pytest.fixture(autouse=True)
def no_wait(monkeypatch):
    monkeypatch.setattr(actions, "MIN_REQUEST_INTERVAL", 0)


def acquire(root, responses, request=None, **kwargs):
    calls = []

    def transport(method, url, headers, timeout, max_bytes):
        calls.append((method, url, dict(headers), timeout, max_bytes))
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    result = actions.acquire_actions(root, REQUEST if request is None else request,
                                     transport=transport, credentials=KEYS,
                                     clock=lambda: NOW, **kwargs)
    return result, calls


def load(root, result):
    with Provenance(root) as store:
        receipt = store.read_json(result["receipt_sha256"])
        normalized = (store.read_json(result["normalized_sha256"])
                      if result.get("normalized_sha256") else None)
        submission = store.get_submission(result["submission_id"])
    return receipt, normalized, submission


def stored_bytes(root):
    return b"".join(path.read_bytes() for path in root.rglob("*") if path.is_file())


def test_request_and_complete_all_category_source_identity(tmp_path):
    categories = {category: [record(id=category)] for category in actions.CATEGORIES}
    categories["future_category"] = [record(id="future", unknown=None)]
    first, last = page(categories, "next+=="), page({"cash_dividends": [record()]})
    result, calls = acquire(tmp_path, [first, last])
    receipt, normalized, submission = load(tmp_path, result)
    assert result["status"] == "success" and result["row_count"] == 18
    assert submission["status"] == "success" and receipt["kind"] == "actions"
    assert receipt["request"] == {**REQUEST, **actions.FIXED}
    assert receipt["pagination_complete"] is True
    assert receipt["coverage_assessment"] == "not_performed"
    assert normalized["kind"] == "corporate_actions"
    assert normalized["identity"] == {"provider": "alpaca", "symbol": "AAPL",
                                      "asset_class": "us_equity"}
    assert normalized["unknown_categories"] == ["future_category"]
    assert not normalized["research_eligible"] and not result["research_eligible"]
    assert normalized["admission_status"] == "inspection_only"
    assert normalized["coverage"]["historical_information"] == "latest_retrieved_revision_not_point_in_time"
    assert normalized["coverage"]["requested_end"] == REQUEST["end"]
    assert receipt["normalizer_sha256"] == hashlib.sha256(
        actions.Path(actions.__file__).read_bytes()).hexdigest()
    for index, response in enumerate((first, last)):
        digest = hashlib.sha256(response.body).hexdigest()
        assert receipt["pages"][index]["raw_sha256"] == digest
        with Provenance(tmp_path) as store:
            assert store.read_bytes(digest) == response.body
    for _, url, headers, timeout, max_bytes in calls:
        parsed = urlsplit(url)
        assert parsed.scheme == "https" and parsed.netloc == "data.alpaca.markets"
        assert parsed.path == "/v1/corporate-actions"
        assert "types" not in parse_qs(parsed.query)
        assert KEYS.secret not in url and KEYS.key_id not in url
        assert headers["APCA-API-KEY-ID"] == KEYS.key_id
        assert 0 < timeout <= 60 and 0 < max_bytes <= 2 * 1024 * 1024
    assert parse_qs(urlsplit(calls[0][1]).query) == {
        "symbols": ["AAPL"], "start": [REQUEST["start"]], "end": [REQUEST["end"]],
        "region": ["us"], "data_quality": ["all"], "sort": ["asc"], "limit": ["1000"]}
    assert parse_qs(urlsplit(calls[1][1]).query)["page_token"] == ["next+=="]
    assert KEYS.secret.encode() not in stored_bytes(tmp_path)


def test_decimal_numbers_keep_precision_and_exact_source_bytes(tmp_path):
    raw = (b'{"corporate_actions":{"cash_dividends":[{"rate":0.1000000000000000000001,'
           b'"large":9007199254740993,"scaled":1.2300,"exp":2.50e-3,"negativezero":-0,'
           b'"nested":[{"x":99.00100}],"special":false,"empty":"","missing":null}]},'
           b'"next_page_token":null}')
    result, _ = acquire(tmp_path, [data.HTTPResult(200, raw)])
    receipt, normalized, _ = load(tmp_path, result)
    row = normalized["records"][0]
    assert row["record"] == {
        "rate": "0.1000000000000000000001", "large": "9007199254740993", "scaled": "1.2300",
        "exp": "0.00250", "negativezero": "-0", "nested": [{"x": "99.00100"}],
        "special": False, "empty": "", "missing": None}
    assert row["occurrences"] == [{"raw_sha256": hashlib.sha256(raw).hexdigest(),
                                    "page": 1, "index": 0}]
    with Provenance(tmp_path) as store:
        assert store.read_bytes(receipt["pages"][0]["raw_sha256"]) == raw


def test_duplicate_and_conflicting_ids_are_all_preserved(tmp_path):
    duplicate = record()
    result, _ = acquire(tmp_path, [page({"cash_dividends": [duplicate, duplicate]}, "next"),
                                   page({"cash_dividends": [record(rate=99)]})])
    normalized = load(tmp_path, result)[1]
    rows = normalized["records"]
    assert len(rows) == 3 and [row["record"]["rate"] for row in rows] == ["0.25", "0.25", "99"]
    assert [row["occurrences"][0]["index"] for row in rows] == [0, 1, 0]
    assert [row["occurrences"][0]["page"] for row in rows] == [1, 1, 2]


def test_incomplete_foreign_out_of_envelope_and_unknown_records_are_retained(tmp_path):
    categories = {"cash_dividends": [{"id": None, "symbol": "MSFT", "ex_date": None,
                                      "process_date": "2010-01-01", "rate": -1}],
                  "future_category": [{}], "forward_splits": []}
    result, _ = acquire(tmp_path, [page(categories)])
    receipt, normalized, _ = load(tmp_path, result)
    assert result["status"] == "success"
    assert normalized["records"][0]["record"]["rate"] == "-1"
    assert set(receipt["categories_present"]) == set(categories)
    assert "reverse_splits" not in normalized["categories_present"]


@pytest.mark.parametrize("categories", [{}, {"cash_dividends": []}, {"future_category": []}])
def test_empty_complete_result_does_not_prove_no_actions(tmp_path, categories):
    result, _ = acquire(tmp_path, [page(categories)])
    receipt, normalized, _ = load(tmp_path, result)
    assert result["status"] == "success" and result["row_count"] == 0
    assert normalized["records"] == [] and receipt["pagination_complete"] is True
    assert normalized["coverage"]["empty_result"] == "no_records_returned_not_absence_proof"
    assert normalized["coverage"]["economic_window_coverage"] == "not_assessed"
    assert result["admission_status"] == "inspection_only"


def test_empty_page_with_token_is_not_terminal(tmp_path):
    result, calls = acquire(tmp_path, [page({}, "next"), page()])
    assert result["status"] == "success" and len(calls) == 2


@pytest.mark.parametrize("value", [
    "{", '{"symbol":"AAPL","symbol":"MSFT","start":"2024-01-01","end":"2024-01-02"}',
    '{"symbol":"AAPL","start":"2024-01-01","end":NaN}', [],
    {**REQUEST, "types": "cash_dividend"}, {**REQUEST, "region": "us"},
    {**REQUEST, "data_quality": "complete"}, {**REQUEST, "limit": 1},
    {**REQUEST, "symbol": "AAPL,MSFT"}, {**REQUEST, "symbol": "AAPL/../../orders"},
    {**REQUEST, "start": "2024-6-01"}, {**REQUEST, "end": "2025-01-21"},
    {**REQUEST, "end": "2015-01-01"}, {"symbol": "AAPL", "start": "2024-01-01"},
])
def test_unbounded_or_nonfrozen_requests_do_not_dispatch(tmp_path, value):
    result, calls = acquire(tmp_path, [], value)
    assert not calls
    assert result["status"] in {"invalid", "rejected"}
    if result["status"] == "invalid":
        assert result["error"] == "request_invalid"
        assert load(tmp_path, result)[2]["status"] == "invalid"


def test_no_undocumented_action_history_floor_is_imposed(tmp_path):
    result, _ = acquire(tmp_path, [page({})], {**REQUEST, "start": "2000-01-01"})
    assert result["status"] == "success"


def test_oversized_request_is_unrecordable(tmp_path):
    result, calls = acquire(tmp_path, [], "a" * (actions.MAX_REQUEST_BYTES + 1))
    assert not calls and result == {"submission_id": None, "status": "rejected",
                                   "error": "request_unrecordable"}
    with Provenance(tmp_path) as store:
        assert store.list_submissions() == []


@pytest.mark.parametrize("raw", [
    b"not-json", b'[]', b'{"corporate_actions":{},"next_page_token":NaN}',
    b'{"corporate_actions":{},"corporate_actions":{},"next_page_token":null}',
    b'{"corporate_actions":{"cash_dividends":[{"rate":1,"rate":2}]},"next_page_token":null}',
    b'{"corporate_actions":{"cash_dividends":[{"rate":Infinity}]},"next_page_token":null}',
    b'{"corporate_actions":{}}', b'{"corporate_actions":[],"next_page_token":null}',
    b'{"corporate_actions":{"cash_dividends":null},"next_page_token":null}',
    b'{"corporate_actions":{"future_category":{"foo":"bar"}},"next_page_token":null}',
    b'{"corporate_actions":{"cash_dividends":[null]},"next_page_token":null}',
])
def test_malformed_pages_retain_safe_bytes_before_parsing(tmp_path, raw):
    result, _ = acquire(tmp_path, [data.HTTPResult(200, raw)])
    assert result["status"] == "invalid"
    receipt, normalized, _ = load(tmp_path, result)
    assert normalized is None and len(receipt["pages"]) == 1
    assert receipt["normalization_status"] == "incomplete"
    with Provenance(tmp_path) as store:
        assert store.read_bytes(receipt["pages"][0]["raw_sha256"]) == raw


@pytest.mark.parametrize("token", ["", "https://evil.test/", True, 1, {}, []])
def test_unsafe_or_malformed_tokens_fail_after_raw_storage(tmp_path, token):
    result, calls = acquire(tmp_path, [page(token=token)])
    assert result["error"] == "pagination_incomplete" and len(calls) == 1
    assert load(tmp_path, result)[0]["pages"]


def test_repeated_token_and_page_cap_are_incomplete(tmp_path, monkeypatch):
    result, calls = acquire(tmp_path, [page(token="again"), page(token="again")])
    assert result["error"] == "pagination_incomplete" and len(calls) == 2
    monkeypatch.setattr(actions, "MAX_PAGES", 1)
    root = tmp_path / "capped"
    root.mkdir()
    result, calls = acquire(root, [page(token="more")])
    receipt, normalized, _ = load(root, result)
    assert result["error"] == "pagination_incomplete" and len(calls) == 1
    assert receipt["pagination_complete"] is False and normalized is None


@pytest.mark.parametrize("response,error", [
    (data.HTTPResult(302, b"sensitive"), "redirect_refused"),
    (data.HTTPResult(401, b"sensitive"), "access_denied"),
    (data.HTTPResult(429, b"sensitive"), "rate_limited"),
    (data.HTTPResult(500, b"sensitive"), "provider_http_error"),
    (TimeoutError("private exception"), "request_timeout"),
    (OSError("private exception"), "network_unavailable"),
    ({"body": "wrong type"}, "transport_invalid"),
])
def test_failed_transport_preserves_previous_page_and_never_retries(tmp_path, response, error):
    first = page(token="next")
    result, calls = acquire(tmp_path, [first, response])
    receipt, normalized, _ = load(tmp_path, result)
    assert result["status"] == "failed" and result["error"] == error
    assert len(calls) == 2 and len(receipt["pages"]) == 1 and normalized is None
    assert b"sensitive" not in stored_bytes(tmp_path) and b"private exception" not in stored_bytes(tmp_path)


@pytest.mark.parametrize("payload", [
    KEYS.secret.encode(), json.dumps({"echo": KEYS.key_id}).encode(),
    ('{"echo":"' + ''.join(f"\\u{ord(char):04x}" for char in KEYS.secret) + '"}').encode(),
    b'{"echo":"sk-ant-syntheticcredential123456"}',
])
def test_reflected_credentials_are_withheld(tmp_path, payload):
    result, _ = acquire(tmp_path, [data.HTTPResult(200, payload)])
    assert result["error"] == "credential_reflection"
    assert load(tmp_path, result)[0]["pages"] == []
    assert payload not in stored_bytes(tmp_path) and KEYS.secret.encode() not in stored_bytes(tmp_path)


def test_submission_and_prepared_request_exist_before_dispatch_and_safe_bytes_before_parser(tmp_path, monkeypatch):
    original = actions._json
    raw = page().body

    def parser(body):
        with Provenance(tmp_path) as store:
            assert store.read_bytes(hashlib.sha256(body).hexdigest()) == body
        return original(body)

    def transport(*_):
        with Provenance(tmp_path) as store:
            assert store.list_submissions()[0]["status"] == "pending"
            kinds = [row[0] for row in store.journal.connection.execute("SELECT kind FROM events")]
            assert "acquisition_request_prepared" in kinds
        return data.HTTPResult(200, raw)

    monkeypatch.setattr(actions, "_json", parser)
    result = actions.acquire_actions(tmp_path, REQUEST, transport=transport, credentials=KEYS,
                                     clock=lambda: NOW)
    assert result["status"] == "success"


def test_dict_is_frozen_before_clock_and_submission_hash_binds_exact_input(tmp_path):
    request = dict(REQUEST)
    frozen = actions.canonical_json(request).encode()

    def clock():
        request["symbol"] = "MSFT"
        return NOW

    result = actions.acquire_actions(tmp_path, request, clock=clock, credentials=KEYS,
                                     transport=lambda *_: page())
    receipt, normalized, submission = load(tmp_path, result)
    assert result["status"] == "success" and normalized["identity"]["symbol"] == "AAPL"
    assert submission["request_sha256"] == hashlib.sha256(frozen).hexdigest()
    assert receipt["submitted_request_sha256"] == submission["request_sha256"]
    with Provenance(tmp_path) as store:
        assert store.read_bytes(receipt["submitted_request_sha256"]) == frozen


def test_receipt_publication_failure_remains_pending(tmp_path, monkeypatch):
    original = Provenance.put_json

    def fail_receipt(self, value):
        if value.get("kind") == "actions":
            raise ProvenanceError("synthetic storage fault")
        return original(self, value)

    monkeypatch.setattr(Provenance, "put_json", fail_receipt)
    result, _ = acquire(tmp_path, [page()])
    assert result["status"] == "pending" and result["error"] == "storage_unavailable"
    with Provenance(tmp_path) as store:
        assert store.get_submission(result["submission_id"])["status"] == "pending"
        assert store.read_bytes(hashlib.sha256(page().body).hexdigest()) == page().body


def test_finish_failure_remains_pending_without_false_success(tmp_path, monkeypatch):
    monkeypatch.setattr(Provenance, "finish", lambda *_: (_ for _ in ()).throw(
        ProvenanceError("synthetic finish fault")))
    result, _ = acquire(tmp_path, [page()])
    assert result["status"] == "pending"
    with Provenance(tmp_path) as store:
        assert store.get_submission(result["submission_id"])["status"] == "pending"


def test_interrupted_dispatch_remains_pending(tmp_path):
    def transport(*_):
        raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        actions.acquire_actions(tmp_path, REQUEST, credentials=KEYS, clock=lambda: NOW,
                                transport=transport)
    with Provenance(tmp_path) as store:
        assert store.list_submissions()[0]["status"] == "pending"


def test_missing_credentials_is_recorded_without_dispatch(tmp_path):
    result = actions.acquire_actions(tmp_path, REQUEST, clock=lambda: NOW,
                                     transport=lambda *_: pytest.fail("must not dispatch"))
    assert result["error"] == "credentials_unavailable"
    assert load(tmp_path, result)[2]["status"] == "failed"


def test_byte_cap_limits_transport_and_preserves_prior_page(tmp_path, monkeypatch):
    first = page(token="next")
    monkeypatch.setattr(actions, "MAX_TOTAL_BYTES", len(first.body) + 1)
    result, calls = acquire(tmp_path, [first, page()])
    assert result["error"] == "response_oversized" and calls[1][4] == 1
    assert len(load(tmp_path, result)[0]["pages"]) == 1


def test_page_byte_cap_and_provider_record_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(actions, "MAX_PAGE_BYTES", 10)
    result, _ = acquire(tmp_path, [page()])
    assert result["error"] == "response_oversized" and not load(tmp_path, result)[0]["pages"]
    monkeypatch.setattr(actions, "MAX_PAGE_BYTES", 2 * 1024 * 1024)
    root = tmp_path / "rows"
    root.mkdir()
    result, _ = acquire(root, [page({"cash_dividends": [{}] * 1001})])
    assert result["error"] == "response_oversized" and len(load(root, result)[0]["pages"]) == 1


def test_total_deadline_and_one_second_spacing(tmp_path, monkeypatch):
    ticks, times = [0.0], []
    monkeypatch.setattr(actions, "MIN_REQUEST_INTERVAL", 1.0)
    monkeypatch.setattr(actions.time, "monotonic", lambda: ticks[0])
    monkeypatch.setattr(actions.time, "sleep", lambda delay: ticks.__setitem__(0, ticks[0] + delay))

    def transport(*_):
        times.append(ticks[0])
        return page(token="next") if len(times) == 1 else page()

    result = actions.acquire_actions(tmp_path, REQUEST, transport=transport, credentials=KEYS,
                                     clock=lambda: NOW)
    assert result["status"] == "success" and times == [0, 1]
    root = tmp_path / "slow"
    root.mkdir()

    def slow(*_):
        ticks[0] += actions.MAX_TOTAL_SECONDS + 1
        return page()

    result = actions.acquire_actions(root, REQUEST, transport=slow, credentials=KEYS,
                                     clock=lambda: NOW)
    assert result["error"] == "request_timeout"
    # The injected transport yielded safe, complete bytes, retained before the late-response refusal.
    assert len(load(root, result)[0]["pages"]) == 1


@pytest.mark.parametrize("change", [
    {"types": "cash_dividend"}, {"region": "all"}, {"data_quality": "complete"},
    {"sort": "desc"}, {"limit": "1001"}, {"symbols": "AAPL,MSFT"},
    {"start": "2024-6-01"}, {"end": "1900-01-01"}, {"page_token": "https://evil.test/"},
])
def test_actions_route_rejects_query_drift_before_transport(change):
    from urllib.parse import urlencode
    query = {"symbols": "AAPL", "start": "2024-01-01", "end": "2024-01-02",
             **actions.FIXED, **change}
    calls = []
    with pytest.raises(data.AcquisitionError, match="route_refused"):
        data._dispatch("GET", actions.ENDPOINT + "?" + urlencode(query), KEYS, 1, 100,
                       lambda *args: calls.append(args))
    assert not calls


@pytest.mark.parametrize("method,url", [
    ("POST", actions.ENDPOINT),
    ("GET", "https://data.alpaca.markets/v2/corporate_actions/announcements"),
    ("GET", "https://paper-api.alpaca.markets/v1/corporate-actions"),
    ("GET", "https://data.alpaca.markets/v1/corporate-actions/"),
    ("GET", "https://data.alpaca.markets.evil.test/v1/corporate-actions"),
    ("GET", "https://data.alpaca.markets:443/v1/corporate-actions"),
    ("GET", "http://data.alpaca.markets/v1/corporate-actions"),
])
def test_actions_route_rejects_other_methods_hosts_and_paths(method, url):
    with pytest.raises(data.AcquisitionError, match="route_refused"):
        data._dispatch(method, url, KEYS, 1, 100, lambda *_: pytest.fail("must not dispatch"))


def test_slow_terminal_page_parsing_cannot_publish_success(tmp_path, monkeypatch):
    ticks = [0.0]
    parser = actions._json
    monkeypatch.setattr(actions.time, "monotonic", lambda: ticks[0])

    def slow_parser(raw):
        result = parser(raw)
        ticks[0] += actions.MAX_TOTAL_SECONDS + 1
        return result

    monkeypatch.setattr(actions, "_json", slow_parser)
    result, calls = acquire(tmp_path, [page()])
    receipt, normalized, _ = load(tmp_path, result)
    assert len(calls) == 1 and result["error"] == "request_timeout"
    assert receipt["pagination_complete"] is False and normalized is None
    assert len(receipt["pages"]) == 1


def test_safe_original_string_bytes_are_bound_without_whitespace_rewrite(tmp_path):
    raw = '\n { "end": "2025-01-20", "start": "2016-01-01", "symbol": "AAPL" } \n'
    result, _ = acquire(tmp_path, [page({})], raw)
    receipt, _, submission = load(tmp_path, result)
    with Provenance(tmp_path) as store:
        assert store.read_bytes(receipt["submitted_request_sha256"]) == raw.encode()
    assert submission["request_sha256"] == hashlib.sha256(raw.encode()).hexdigest()


def test_credential_reflection_in_valid_request_is_not_persisted(tmp_path):
    keys = data.Credentials("AAPLTEST", "fixture-secret-key-12345")
    request = {**REQUEST, "symbol": keys.key_id}
    result = actions.acquire_actions(tmp_path, request, credentials=keys, clock=lambda: NOW,
                                     transport=lambda *_: pytest.fail("must not dispatch"))
    assert result["error"] == "credential_reflection"
    receipt, _, _ = load(tmp_path, result)
    assert receipt["request"] is None and "submitted_request_sha256" not in receipt
    assert keys.key_id.encode() not in stored_bytes(tmp_path)


@pytest.mark.parametrize("suffix", ["&symbols=MSFT", "&types=", "#fragment"])
def test_actions_route_refuses_duplicate_or_extra_query_and_fragment(suffix):
    request = actions._request(actions.canonical_json(REQUEST), NOW)
    with pytest.raises(data.AcquisitionError, match="route_refused"):
        data._dispatch("GET", actions._url(request) + suffix, KEYS, 1, 100,
                       lambda *_: pytest.fail("must not dispatch"))

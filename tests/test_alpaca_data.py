"""Synthetic HTTP evidence exercises the adapter; no provider or credentials are used."""
from datetime import datetime, timezone
import hashlib
import json
from urllib.parse import parse_qs, urlsplit

import pytest
from access_fixtures import synthetic_access as synthetic_access


from quanto import alpaca_data as data
from quanto.provenance import Provenance

pytestmark = pytest.mark.usefixtures("synthetic_access")

KEYS = data.Credentials("fixture-paper-key-12345", "fixture-secret-key-12345")
NOW = datetime(2025, 1, 20, tzinfo=timezone.utc)
REQUEST = {"symbol": "AAPL", "start": "2024-06-03", "end": "2024-06-05"}


def row(day=3, **changes):
    value = {"t": f"2024-06-{day:02d}T04:00:00Z", "o": 100, "h": 103,
             "l": 99, "c": 102, "v": 1000}
    value.update(changes)
    return value


def page(rows=None, token=None, **changes):
    value = {"symbol": "AAPL", "bars": [row()] if rows is None else rows,
             "next_page_token": token}
    value.update(changes)
    return data.HTTPResult(200, json.dumps(value).encode())


@pytest.fixture(autouse=True)
def no_wait(monkeypatch):
    monkeypatch.setattr(data, "MIN_REQUEST_INTERVAL", 0)


def acquire(root, responses, request=None, **kwargs):
    calls = []

    def transport(method, url, headers, timeout, max_bytes):
        calls.append((method, url, dict(headers), timeout, max_bytes))
        value = responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    result = data.acquire_bars(root, REQUEST if request is None else request,
                               transport=transport, credentials=KEYS, clock=lambda: NOW, **kwargs)
    return result, calls


def load(root, result):
    with Provenance(root) as store:
        receipt = store.read_json(result["receipt_sha256"])
        normalized = (store.read_json(result["normalized_sha256"])
                      if result.get("normalized_sha256") else None)
        submission = store.get_submission(result["submission_id"])
    return receipt, normalized, submission


def test_complete_pages_preserve_bytes_and_explicit_query(tmp_path):
    first, second = page([row(3)], "next_page"), page([row(4), row(5)])
    result, calls = acquire(tmp_path, [first, second])
    assert result["status"] == "success" and result["row_count"] == 3
    receipt, normalized, submission = load(tmp_path, result)
    assert submission["status"] == "success"
    assert receipt["research_eligible"] is False
    assert normalized["admission_status"] == "inspection_only"
    assert normalized["price_basis"] == "raw"
    assert normalized["identity"]["stable_entity_id"] is None
    assert normalized["bars"][0]["timestamp"] == "2024-06-03T00:00:00-04:00"
    assert normalized["bars"][0]["source_timestamp"] == "2024-06-03T04:00:00Z"
    assert normalized["coverage"]["calendar_status"] == "unverified"
    for index, raw in enumerate((first.body, second.body)):
        assert receipt["pages"][index]["raw_sha256"] == hashlib.sha256(raw).hexdigest()
        with Provenance(tmp_path) as store:
            assert store.read_bytes(receipt["pages"][index]["raw_sha256"]) == raw
    query = parse_qs(urlsplit(calls[0][1]).query)
    assert calls[0][0] == "GET" and urlsplit(calls[0][1]).netloc == "data.alpaca.markets"
    assert query == {"feed": ["sip"], "timeframe": ["1Day"], "adjustment": ["raw"],
                     "currency": ["USD"], "asof": ["-"], "limit": ["1000"], "sort": ["asc"],
                     "start": ["2024-06-03T04:00:00+00:00"],
                     "end": ["2024-06-06T03:59:59.999999+00:00"]}
    assert parse_qs(urlsplit(calls[1][1]).query)["page_token"] == ["next_page"]
    for _, url, headers, _, _ in calls:
        assert KEYS.key_id not in url and KEYS.secret not in url
        assert headers["APCA-API-KEY-ID"] == KEYS.key_id
    stored = b"".join(p.read_bytes() for p in (tmp_path / "data/objects").iterdir())
    assert KEYS.key_id.encode() not in stored and KEYS.secret.encode() not in stored


def test_submission_commits_before_first_transport(tmp_path):
    def transport(*_):
        with Provenance(tmp_path) as store:
            records = store.list_submissions()
            assert len(records) == 1 and records[0]["status"] == "pending"
            events = [r[0] for r in store.journal.connection.execute("SELECT kind FROM events")]
            assert "submission_started" in events and "acquisition_request_prepared" in events
        return page()
    result = data.acquire_bars(tmp_path, REQUEST, transport=transport,
                              credentials=KEYS, clock=lambda: NOW)
    assert result["status"] == "success"


@pytest.mark.parametrize("request_value", [
    "{", '{"symbol":"AAPL","symbol":"MSFT"}', '{"value":NaN}',
    {**REQUEST, "feed": "iex"}, {**REQUEST, "symbol": "AAPL/../../orders"},
    {**REQUEST, "adjustment": "split"}, {**REQUEST, "url": "https://example.com"},
    {**REQUEST, "end": "2025-01-20"}, {**REQUEST, "start": "2015-01-01"},
    {**REQUEST, "end": "2024-6-05"}, {**REQUEST, "start": "2024-06-06"},
])
def test_invalid_requests_remain_recorded_without_dispatch(tmp_path, request_value):
    result, calls = acquire(tmp_path, [], request_value)
    assert result["status"] == "invalid" and result["error"] == "request_invalid"
    assert not calls
    _, _, submission = load(tmp_path, result)
    assert submission["status"] == "invalid"


def test_oversized_input_is_explicit_preflight_rejection(tmp_path):
    result, calls = acquire(tmp_path, [], "x" * (data.MAX_REQUEST_BYTES + 1))
    assert result == {"submission_id": None, "status": "rejected", "error": "request_unrecordable"}
    with Provenance(tmp_path) as store:
        assert store.list_submissions() == []
    assert not calls


@pytest.mark.parametrize("response,category", [
    (data.HTTPResult(302, b"sensitive redirect body"), "redirect_refused"),
    (data.HTTPResult(401, b"sensitive auth body"), "access_denied"),
    (data.HTTPResult(429, b"sensitive rate body"), "rate_limited"),
    (data.HTTPResult(500, b"sensitive error body"), "provider_http_error"),
    (TimeoutError("private error"), "request_timeout"),
    (OSError("private error"), "network_unavailable"),
])
def test_provider_failures_are_sanitized_and_never_retried(tmp_path, response, category):
    result, calls = acquire(tmp_path, [response])
    assert result["status"] == "failed" and result["error"] == category
    assert len(calls) == 1
    receipt, _, submission = load(tmp_path, result)
    assert receipt["pages"] == [] and submission["status"] == "failed"
    all_bytes = b"".join(p.read_bytes() for p in (tmp_path / "data/objects").iterdir())
    assert b"sensitive" not in all_bytes and b"private error" not in all_bytes


@pytest.mark.parametrize("body", [
    b"not json", b'{"symbol":"AAPL","bars":[],"next_page_token":null,"x":1e999}',
    b'{"symbol":"AAPL","symbol":"MSFT","bars":[],"next_page_token":null}',
    page(symbol="MSFT").body, page([row(t="2024-06-03T00:00:00Z")]).body,
    page([row(t="2024-06-03")]).body, page([row(o=True)]).body,
    page([row(l=110)]).body, page([row(v=-1)]).body,
])
def test_invalid_responses_keep_safe_raw_evidence(tmp_path, body):
    result, _ = acquire(tmp_path, [data.HTTPResult(200, body)])
    assert result["status"] == "invalid"
    receipt, normalized, _ = load(tmp_path, result)
    assert normalized is None and len(receipt["pages"]) == 1
    with Provenance(tmp_path) as store:
        assert store.read_bytes(receipt["pages"][0]["raw_sha256"]) == body


@pytest.mark.parametrize("payload", [
    KEYS.secret.encode(),
    b'{"echo":"' + b"".join(f"\\u{ord(c):04x}".encode() for c in KEYS.key_id) + b'"}',
    b'{"echo":"sk-ant-syntheticcredential123456"}',
])
def test_reflected_credentials_are_never_persisted(tmp_path, payload):
    result, _ = acquire(tmp_path, [data.HTTPResult(200, payload)])
    assert result["error"] == "credential_reflection"
    receipt, _, _ = load(tmp_path, result)
    assert receipt["pages"] == []
    all_bytes = b"".join(p.read_bytes() for p in tmp_path.rglob("*") if p.is_file())
    assert payload not in all_bytes and KEYS.secret.encode() not in all_bytes


def test_partial_failure_retains_earlier_page(tmp_path):
    first = page([row(3)], "cursor")
    result, calls = acquire(tmp_path, [first, data.HTTPResult(403, b"denied")])
    assert result["status"] == "failed" and len(calls) == 2
    receipt, normalized, _ = load(tmp_path, result)
    assert normalized is None and receipt["pages"][0]["raw_sha256"] == hashlib.sha256(first.body).hexdigest()


@pytest.mark.parametrize("responses,category", [
    ([page([row(3)], "cursor"), page([row(3)])], "coverage_invalid"),
    ([page([row(3)], "cursor"), page([row(4)], "cursor")], "pagination_incomplete"),
    ([page([row(2)])], "coverage_invalid"),
    ([page([])], "empty_coverage"),
    ([page(token="https://elsewhere")], "pagination_incomplete"),
])
def test_coverage_and_pagination_are_not_silently_repaired(tmp_path, responses, category):
    result, _ = acquire(tmp_path, list(responses))
    assert result["status"] == "invalid" and result["error"] == category


def test_page_and_byte_caps(tmp_path, monkeypatch, synthetic_access):
    monkeypatch.setattr(data, "MAX_PAGES", 1)
    result, calls = acquire(tmp_path, [page(token="more")])
    assert result["error"] == "pagination_incomplete" and len(calls) == 1
    second = tmp_path / "bytes"
    second.mkdir()
    synthetic_access.bind(second)
    monkeypatch.setattr(data, "MAX_PAGE_BYTES", 100)
    result, calls = acquire(second, [page()])
    assert result["error"] == "response_oversized" and len(calls) == 1


def test_all_adjustment_is_retained_as_inspection_only(tmp_path):
    result, calls = acquire(tmp_path, [page()], {**REQUEST, "adjustment": "all"})
    _, normalized, _ = load(tmp_path, result)
    assert normalized["price_basis"] == "all" and not normalized["research_eligible"]
    assert parse_qs(urlsplit(calls[0][1]).query)["adjustment"] == ["all"]


@pytest.mark.parametrize("method,url", [
    ("POST", "https://paper-api.alpaca.markets/v2/orders"),
    ("GET", "https://paper-api.alpaca.markets/v2/orders"),
    ("GET", "https://api.alpaca.markets/v2/calendar?start=2024-01-01&end=2024-01-02"),
    ("GET", "https://data.alpaca.markets.evil.test/v2/stocks/AAPL/bars"),
    ("GET", "http://paper-api.alpaca.markets/v2/calendar?start=2024-01-01&end=2024-01-02"),
])
def test_central_allowlist_rejects_other_methods_hosts_and_paths(method, url):
    calls = []
    with pytest.raises(data.AcquisitionError, match="route_refused"):
        data._dispatch(method, url, KEYS, 1, 100, lambda *args: calls.append(args))
    assert calls == []


def test_calendar_preserves_ny_times_and_source(tmp_path):
    body = json.dumps([{"date": "2024-06-03", "open": "09:30", "close": "16:00"},
                       {"date": "2024-06-04", "open": "09:30", "close": "13:00"}]).encode()
    calls = []
    def transport(*args):
        calls.append(args)
        return data.HTTPResult(200, body)
    result = data.acquire_calendar(tmp_path, {"start": "2024-06-03", "end": "2024-06-05"},
                                   transport=transport, credentials=KEYS, clock=lambda: NOW)
    assert result["status"] == "success" and result["row_count"] == 2
    receipt, normalized, _ = load(tmp_path, result)
    assert normalized["kind"] == "exchange_calendar"
    assert normalized["sessions"][1]["close"] == "2024-06-04T13:00:00-04:00"
    assert not normalized["research_eligible"]
    assert urlsplit(calls[0][1]).netloc == "paper-api.alpaca.markets"
    assert receipt["pages"][0]["raw_sha256"] == hashlib.sha256(body).hexdigest()


def test_missing_local_credentials_is_a_recorded_failure(tmp_path):
    result = data.acquire_bars(tmp_path, REQUEST, clock=lambda: NOW,
                              transport=lambda *_: pytest.fail("must not dispatch"))
    assert result["error"] == "credentials_unavailable"
    assert load(tmp_path, result)[2]["status"] == "failed"


def test_test_configuration_is_private_and_never_exported(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text(f"APCA_API_KEY_ID={KEYS.key_id}\nAPCA_API_SECRET_KEY={KEYS.secret}\n")
    path.chmod(0o600)
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    assert data.local_credentials(tmp_path) == KEYS
    import os
    assert "APCA_API_KEY_ID" not in os.environ
    path.chmod(0o644)
    with pytest.raises(data.AcquisitionError, match="credentials_unavailable"):
        data.local_credentials(tmp_path)


def test_interrupted_transport_leaves_pending_submission(tmp_path):
    def interrupted(*_):
        raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        data.acquire_bars(tmp_path, REQUEST, transport=interrupted, credentials=KEYS, clock=lambda: NOW)
    with Provenance(tmp_path) as store:
        records = store.list_submissions()
        assert len(records) == 1 and records[0]["status"] == "pending"


def test_elapsed_time_bound_rejects_late_response(tmp_path, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(data.time, "monotonic", lambda: clock[0])
    def slow(*_):
        clock[0] = data.MAX_TOTAL_SECONDS + 1
        return page()
    result = data.acquire_bars(tmp_path, REQUEST, transport=slow, credentials=KEYS, clock=lambda: NOW)
    assert result["error"] == "request_timeout" and load(tmp_path, result)[0]["pages"] == []


def test_winter_daily_bucket_uses_new_york_midnight(tmp_path):
    winter = {"symbol": "AAPL", "start": "2024-01-03", "end": "2024-01-03"}
    result, _ = acquire(tmp_path, [page([row(t="2024-01-03T05:00:00Z")])], winter)
    assert load(tmp_path, result)[1]["bars"][0]["timestamp"] == "2024-01-03T00:00:00-05:00"


def test_total_bytes_limit_retains_only_prior_complete_page(tmp_path, monkeypatch):
    first = page(token="next")
    monkeypatch.setattr(data, "MAX_TOTAL_BYTES", len(first.body) + 1)
    result, calls = acquire(tmp_path, [first, page([row(4)])])
    receipt = load(tmp_path, result)[0]
    assert result["error"] == "response_oversized" and len(receipt["pages"]) == 1
    assert calls[1][4] == 1


def test_escaped_punctuation_in_injected_secret_is_rejected(tmp_path):
    keys = data.Credentials("fixture-key-12345", 'fixture-quote"and-backslash\\1234')
    body = json.dumps({"echo": keys.secret}).encode()
    result = data.acquire_bars(tmp_path, REQUEST, credentials=keys, clock=lambda: NOW,
                              transport=lambda *_: data.HTTPResult(200, body))
    assert result["error"] == "credential_reflection"
    assert load(tmp_path, result)[0]["pages"] == []


@pytest.mark.parametrize("status", [200, 302])
def test_production_transport_is_direct_bounded_and_never_follows_redirects(monkeypatch, status, tmp_path, synthetic_access):
    calls = []
    body = bytearray(page().body)

    class Response:
        def read1(self, size):
            assert status == 200, "error bodies must not be read"
            assert size <= 65536
            value = bytes(body[:size])
            del body[:size]
            return value

    response = Response()
    response.status = status

    class Socket:
        def settimeout(self, value):
            assert 0 < value <= 15

    class Connection:
        sock = Socket()

        def __init__(self, hostname, timeout):
            calls.append(("connect_to", hostname, timeout))

        def connect(self):
            calls.append(("connect",))

        def request(self, method, path, headers):
            calls.append(("request", method, path))
            assert headers["APCA-API-KEY-ID"] == KEYS.key_id

        def getresponse(self):
            return response

        def close(self):
            calls.append(("close",))

    monkeypatch.setattr(data.http.client, "HTTPSConnection", Connection)
    http_root = tmp_path / "mocked-http"
    http_root.mkdir()
    session = synthetic_access.bind(http_root, synthetic=False)
    request = data._request(REQUEST, "bars", NOW)
    intent = session.acquisition("bars", request)
    url = data._url(request, "bars")
    permit = intent.page("GET", url)
    if status == 200:
        assert data._dispatch("GET", url, KEYS, 30, 1024, permit=permit).body == page().body
    else:
        with pytest.raises(data.AcquisitionError, match="redirect_refused"):
            data._dispatch("GET", url, KEYS, 30, 1024, permit=permit)
    assert sum(call[0] == "connect_to" for call in calls) == 1
    assert calls[0][1] == "data.alpaca.markets" and calls[-1] == ("close",)


def test_dict_request_is_frozen_before_clock_or_transport(tmp_path):
    request = dict(REQUEST)
    calls = []

    def clock():
        request['symbol'] = 'MSFT'
        return NOW

    def transport(method, url, headers, timeout, max_bytes):
        calls.append(url)
        return page()

    result = data.acquire_bars(tmp_path, request, clock=clock, transport=transport,
                               credentials=KEYS)
    receipt, normalized, submission = load(tmp_path, result)
    assert result['status'] == 'success'
    assert normalized['identity']['symbol'] == 'AAPL'
    assert receipt['request']['symbol'] == 'AAPL'
    assert '/AAPL/bars?' in calls[0]
    assert submission['request_sha256'] == hashlib.sha256(
        data.canonical_json(REQUEST).encode()
    ).hexdigest()

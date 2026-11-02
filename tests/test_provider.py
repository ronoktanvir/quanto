"""Provider contract checks with synthetic responses; never makes a paid call."""
import json
import threading
from datetime import datetime, timezone

import pytest

from quanto import provider
from quanto.ledger import Journal, LedgerError


@pytest.fixture
def fake_key(monkeypatch):
    monkeypatch.setattr(provider, "local_key", lambda _: "synthetic-key")
    monkeypatch.setattr(provider, "PRICE_VERIFIED_ON", datetime.now(timezone.utc).date().isoformat())


def response(model=provider.HAIKU):
    return {"type": "message", "id": "synthetic", "model": model,
            "content": [{"type": "text", "text": "Synthetic reply"}],
            "usage": {"input_tokens": 100, "output_tokens": 20}, "stop_reason": "end_turn"}


def call(root, request_id="provider-test", **kwargs):
    return provider.request_text(root, request_id=request_id, model=provider.HAIKU,
                                 system="Synthetic test", messages=[{"role": "user", "content": "Hi"}],
                                 purpose="conversation", role="qa", **kwargs)


def test_paid_call_reserves_dispatches_and_settles_shared_journal(tmp_path, fake_key):
    sent = []

    def transport(body, key):
        sent.append(json.loads(body))
        with Journal(tmp_path / "runtime/research.sqlite") as journal:
            assert journal.connection.execute("SELECT COUNT(*) FROM dispatches").fetchone()[0] == 1
            assert journal.budget_snapshot()["committed_micro_usd"] > 50_000
        return response()

    result = call(tmp_path, transport=transport)
    assert result["cost_micro_usd"] == 100
    assert result["status"] == "completed"
    assert set(sent[0]) == {"model", "system", "max_tokens", "messages"}
    with Journal(tmp_path / "runtime/research.sqlite") as journal:
        assert journal.budget_snapshot()["committed_micro_usd"] == 100
    with pytest.raises(LedgerError, match="second call"):
        call(tmp_path, transport=transport)
    assert len(sent) == 1


@pytest.mark.parametrize("change", [
    {"model": "different-model"}, {"type": "error"}, {"usage": {}},
    {"content": [{"type": "tool_use", "id": "x"}]},
    {"usage": {"input_tokens": True, "output_tokens": 1}},
])
def test_unverified_response_retains_full_hold_and_observation(tmp_path, fake_key, change):
    result = response()
    result.update(change)
    with pytest.raises(LedgerError, match="no retry"):
        call(tmp_path, transport=lambda *_: result)
    with Journal(tmp_path / "runtime/research.sqlite") as journal:
        row = journal.connection.execute("SELECT * FROM reservations").fetchone()
        assert row["state"] == "uncertain" and row["actual_micro_usd"] is None
        kinds = [r[0] for r in journal.connection.execute("SELECT kind FROM events")]
        assert "provider_response_observed" in kinds
        assert "provider_call_uncertain" in kinds


def test_timeout_retains_hold_and_never_retries(tmp_path, fake_key):
    sent = []

    def timeout(*_):
        sent.append(1)
        raise TimeoutError("Do not log this provider body")

    with pytest.raises(LedgerError):
        call(tmp_path, transport=timeout)
    with pytest.raises(LedgerError):
        call(tmp_path, transport=timeout)
    assert len(sent) == 1
    with Journal(tmp_path / "runtime/research.sqlite") as journal:
        assert journal.connection.execute("SELECT state FROM reservations").fetchone()[0] == "uncertain"


def test_global_budget_blocks_before_network(tmp_path, fake_key):
    (tmp_path / "runtime").mkdir()
    with Journal(tmp_path / "runtime/research.sqlite") as journal:
        journal.reserve("other-client", 19_990_000)
    with pytest.raises(LedgerError, match="budget"):
        call(tmp_path, transport=lambda *_: pytest.fail("must not send"))


def test_pause_and_secret_guard_precede_dispatch(tmp_path, fake_key):
    (tmp_path / "runtime").mkdir()
    marker = tmp_path / "runtime/model_calls_paused"
    marker.touch()
    with pytest.raises(LedgerError, match="paused"):
        call(tmp_path, transport=lambda *_: pytest.fail("must not send"))
    marker.unlink()
    with pytest.raises(LedgerError, match="secret"):
        provider.request_text(tmp_path, request_id="secret", model=provider.HAIKU,
                              system="sk-ant-synthetic0123456789", messages=[{"role": "user", "content": "Hi"}],
                              purpose="conversation", role="qa", transport=lambda *_: pytest.fail("must not send"))


def test_third_concurrent_call_is_rejected(tmp_path, fake_key):
    entered, release = threading.Event(), threading.Event()
    count, lock = [0], threading.Lock()

    def blocked(*_):
        with lock:
            count[0] += 1
            if count[0] == 2:
                entered.set()
        assert release.wait(5)
        return response()

    errors = []

    def run(identity):
        try:
            call(tmp_path, request_id=identity, transport=blocked)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=run, args=(str(i),)) for i in range(2)]
    for thread in threads:
        thread.start()
    try:
        assert entered.wait(5)
        with pytest.raises(LedgerError, match="already in progress"):
            call(tmp_path, request_id="third", transport=lambda *_: pytest.fail("must not send"))
    finally:
        release.set()
        for thread in threads:
            thread.join(5)
    assert not errors


def test_cost_rounding_and_conservative_haiku_rates():
    assert provider.usage_cost(provider.HAIKU, {"input_tokens": 1, "output_tokens": 0}) == 1
    assert provider.usage_cost(provider.OPUS, {"input_tokens": 2, "output_tokens": 1,
                                               "cache_creation_input_tokens": 3}) == 52


def test_expired_prices_fail_closed(tmp_path, fake_key, monkeypatch):
    monkeypatch.setattr(provider, "PRICE_VERIFIED_ON", "2000-01-01")
    with pytest.raises(LedgerError, match="verification"):
        call(tmp_path, transport=lambda *_: pytest.fail("must not send"))


def test_purpose_allowance_counts_outstanding_allocations(tmp_path, fake_key):
    import sqlite3

    (tmp_path / "runtime").mkdir()
    path = tmp_path / "runtime/research.sqlite"
    with Journal(path):
        pass
    provider._purpose_hold(path, "prior", "conversation", 18_000_000)
    with pytest.raises(LedgerError, match="purpose allowance"):
        call(tmp_path, transport=lambda *_: pytest.fail("must not send"))
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM reservations").fetchone()[0] == 0


@pytest.mark.parametrize("hidden", [
    {"type": "thinking", "thinking": "", "signature": "synthetic-signature"},
    {"type": "thinking", "thinking": "Hidden test reasoning", "signature": "synthetic-signature"},
    {"type": "redacted_thinking", "data": "synthetic-redacted-data"},
])
def test_opus_thinking_is_validated_but_never_exposed(tmp_path, fake_key, hidden):
    result = response(provider.OPUS)
    result["content"].insert(0, hidden)
    report = provider.request_text(tmp_path, request_id="opus-thinking", model=provider.OPUS,
                                   system="Synthetic test", messages=[{"role": "user", "content": "Hello"}],
                                   purpose="conversation", role="desk_helper", transport=lambda *_: result)
    assert report["reply"] == "Synthetic reply" and report["status"] == "completed"
    assert "Hidden test reasoning" not in json.dumps(report)
    assert "synthetic-redacted-data" not in json.dumps(report)
    with Journal(tmp_path / "runtime/research.sqlite") as journal:
        assert journal.connection.execute("SELECT state FROM reservations").fetchone()[0] == "settled"
        events = " ".join(row[0] for row in journal.connection.execute("SELECT payload FROM events"))
        assert "Hidden test reasoning" not in events and "synthetic-redacted-data" not in events


@pytest.mark.parametrize("block", [
    {"type": "thinking", "thinking": []},
    {"type": "thinking", "thinking": "", "signature": None},
    {"type": "redacted_thinking", "data": {}},
    {"type": "unknown_future_block", "text": "Do not accept"},
])
def test_malformed_hidden_or_unknown_content_remains_uncertain(tmp_path, fake_key, block):
    result = response()
    result["content"].insert(0, block)
    with pytest.raises(LedgerError, match="no retry"):
        call(tmp_path, transport=lambda *_: result)
    with Journal(tmp_path / "runtime/research.sqlite") as journal:
        assert journal.connection.execute("SELECT state FROM reservations").fetchone()[0] == "uncertain"


def test_research_http_response_hash_binds_exact_bytes_and_shortens_read_deadline(monkeypatch):
    from types import SimpleNamespace
    from quanto.ledger import hash_bytes

    raw = b'{ "type": "message", "model": "synthetic" }\n'
    timeouts, opens = [], []

    class Response:
        def __init__(self):
            self.parts = [raw[:10], raw[10:], b""]
            self.fp = SimpleNamespace(raw=SimpleNamespace(
                _sock=SimpleNamespace(settimeout=timeouts.append)))

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def isclosed(self):
            return False

        def read1(self, maximum):
            part = self.parts.pop(0)
            assert len(part) <= maximum
            return part

    class Opener:
        def open(self, request, *, timeout):
            opens.append((request, timeout))
            return Response()

    monkeypatch.setattr(provider, "build_opener", lambda *_: Opener())
    result, digest = provider._send_research(b"{}", "synthetic", timeout=5, maximum=1000)
    assert result == {"type": "message", "model": "synthetic"}
    assert digest == hash_bytes(raw)
    assert digest != hash_bytes(provider.canonical_json(result).encode())
    assert len(opens) == 1 and opens[0][0].method == "POST"
    assert all(0 < value <= 5 for value in timeouts)
    assert timeouts == sorted(timeouts, reverse=True)


@pytest.mark.parametrize("raw,maximum", [
    (b'{"model":"first","model":"second"}', 1000),
    (b"x" * 101, 100),
])
def test_research_wire_bytes_refuse_duplicate_keys_or_overflow(monkeypatch, raw, maximum):
    from types import SimpleNamespace

    class Response:
        def __init__(self):
            self.parts = [raw, b""]
            self.fp = SimpleNamespace(raw=SimpleNamespace(_sock=SimpleNamespace(settimeout=lambda _: None)))

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def isclosed(self):
            return False

        def read1(self, size):
            return self.parts.pop(0)

    monkeypatch.setattr(provider, "build_opener", lambda *_: SimpleNamespace(
        open=lambda *args, **kwargs: Response()))
    with pytest.raises(LedgerError):
        provider._send_research(b"{}", "synthetic", timeout=5, maximum=maximum)

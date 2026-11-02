"""Local chat/session security checks; all provider results are synthetic fixtures."""
import http.client
import json
import threading
import uuid
from datetime import datetime, timezone

import pytest

from quanto import provider
from quanto.conversations import Conversations, ConversationError
from quanto.dashboard import make_server
from quanto.ledger import Journal


@pytest.fixture
def desk(tmp_path, monkeypatch):
    monkeypatch.setattr(provider, "local_key", lambda _: "synthetic-key")
    monkeypatch.setattr(provider, "PRICE_VERIFIED_ON", datetime.now(timezone.utc).date().isoformat())
    monkeypatch.setattr("quanto.conversations.local_key", lambda _: "synthetic-key")
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "status.json").write_text(json.dumps({"observed_at": "2026-11-01T00:00:00+00:00",
                                                   "agents": [{"id": "qa", "name": "Quality"}]}))
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/STATUS.md").write_text("Synthetic evidence only.")
    sent = []

    def transport(body, _):
        sent.append(json.loads(body))
        return {"type": "message", "model": sent[-1]["model"], "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "<script>hostile text stays text</script>"}],
                "usage": {"input_tokens": 100, "output_tokens": 10}}

    server = make_server(tmp_path, port=0, transport=transport)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01))
    thread.start()
    port = server.server_address[1]

    def request(path, method="GET", data=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        connection.request(method, path, body=json.dumps(data) if data is not None else None,
                           headers=headers or {})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), json.loads(response.read())
        connection.close()
        return result

    def session():
        code, headers, body = request("/api/session")
        assert code == 200
        return {"Cookie": headers["Set-Cookie"].split(";", 1)[0],
                "X-Quanto-CSRF": body["csrf_token"], "Content-Type": "application/json",
                "Origin": f"http://127.0.0.1:{port}"}, body

    yield request, session, sent, tmp_path, port
    server.shutdown()
    server.server_close()
    thread.join(3)


def turn(**changes):
    result = {"agent_id": "qa", "request_id": str(uuid.uuid4()), "message": "What is recorded?",
              "conversation_id": None}
    result.update(changes)
    return result


def test_chat_is_persistent_deduplicated_and_session_owned(desk):
    request, session, sent, root, _ = desk
    headers, info = session()
    assert {r["id"] for r in info["roles"]} == {"qa", "desk_helper"}
    data = turn()
    code, _, result = request("/api/chat", "POST", data, headers)
    assert code == 200 and result["status"] == "completed"
    assert result["model"] == provider.HAIKU
    assert result["context"]["observed_at"] == "2026-11-01T00:00:00+00:00"
    assert request("/api/chat", "POST", data, headers)[2] == result
    store = Conversations(root, transport=lambda *_: pytest.fail("must not resend after restart"))
    session_id, _, _ = store.session(headers["Cookie"].split("=", 1)[1])
    assert store.chat(session_id, data) == result
    assert len(sent) == 1
    history = request("/api/conversations?agent_id=qa", headers=headers)[2]["conversations"]
    assert len(history) == 1
    assert history[0]["messages"][1]["content"] == result["reply"]
    other, _ = session()
    assert request("/api/conversations?agent_id=qa", headers=other)[2] == {"conversations": []}
    assert request("/api/chat", "POST", data, other)[0] == 409
    data = turn(conversation_id=result["conversation_id"])
    assert request("/api/chat", "POST", data, other)[0] == 404
    assert len(sent) == 1


@pytest.mark.parametrize("change", [
    {"Origin": "http://127.0.0.1:1"}, {"Origin": "null"}, {"Origin": "https://evil.example"},
    {"X-Quanto-CSRF": "wrong"}, {"Host": "evil.example"}, {"Origin": None},
])
def test_cross_origin_and_csrf_rejected_before_paid_call(desk, change):
    request, session, sent, _, _ = desk
    headers, _ = session()
    headers.update(change)
    headers = {k: v for k, v in headers.items() if v is not None}
    assert request("/api/chat", "POST", turn(), headers)[0] == 403
    assert not sent


def test_inbox_is_pending_only_and_idempotent(desk):
    request, session, sent, root, _ = desk
    headers, _ = session()
    data = turn()
    code, _, result = request("/api/inbox", "POST", data, headers)
    assert code == 200 and result["status"] == "pending"
    assert request("/api/inbox", "POST", data, headers)[2] == result
    assert not sent
    pending = Conversations(root).pending_inquiries()
    assert len(pending) == 1 and pending[0]["message"] == data["message"]
    Conversations(root).reply_inquiry(data["request_id"], "Actually observed worker reply",
                                     actor="original-qa-worker", source_ref="native-worker-turn:test")
    inquiries = request("/api/inbox?agent_id=qa", headers=headers)[2]["inquiries"]
    assert inquiries[0]["status"] == "answered"
    assert inquiries[0]["reply"]["source_ref"] == "native-worker-turn:test"
    receipt = request("/api/inbox", "POST", data, headers)[2]
    assert receipt["status"] == "answered"
    assert receipt["reply"] == inquiries[0]["reply"]
    assert "no answer" not in receipt["message"]
    with pytest.raises(ConversationError, match="already"):
        Conversations(root).reply_inquiry(data["request_id"], "Replacement", actor="lead", source_ref="test")
    other, _ = session()
    assert request("/api/inbox", "POST", data, other)[0] == 409
    assert request("/api/inbox?agent_id=qa", headers=other)[2] == {"inquiries": []}


def test_restart_never_resends_pending_turn(tmp_path, monkeypatch):
    monkeypatch.setattr(provider, "local_key", lambda _: "synthetic-key")
    store = Conversations(tmp_path)
    session, _, _ = store.session(None, create=True)
    identity = str(uuid.uuid4())
    with store.db() as db:
        db.execute("INSERT INTO turns VALUES (?,?,?,'conversation','Hello','pending',NULL,?)",
                   (identity, session, "desk_helper", "2026-11-01"))
    reopened = Conversations(tmp_path, transport=lambda *_: pytest.fail("must not resend"))
    result = reopened.chat(session, turn(agent_id="desk_helper", request_id=identity, message="Hello"))
    assert result["status"] == "incomplete"


def test_context_excludes_env_other_files_and_rejects_symlink(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / ".env").write_text("DO_NOT_SEND_THIS")
    (tmp_path / "docs/private.txt").write_text("PRIVATE_DATA")
    (tmp_path / "docs/STATUS.md").write_text("Allowed saved observation")
    store = Conversations(tmp_path)
    context, meta = store.context("desk_helper")
    assert "Allowed saved observation" in context
    assert "DO_NOT_SEND_THIS" not in context and "PRIVATE_DATA" not in context
    assert meta["sources"] == ["docs/STATUS.md"]
    (tmp_path / "docs/STATUS.md").unlink()
    (tmp_path / "docs/STATUS.md").symlink_to(tmp_path / ".env")
    with pytest.raises(ConversationError, match="symlink"):
        store.context("desk_helper")


def test_pause_marker_blocks_calls_and_can_be_resumed(desk):
    request, session, sent, _, _ = desk
    headers, _ = session()
    assert request("/api/model-calls/pause", "POST", {}, headers)[2]["model_calls_paused"]
    assert request("/api/chat", "POST", turn(), headers)[2]["status"] == "error"
    assert not sent
    assert not request("/api/model-calls/resume", "POST", {}, headers)[2]["model_calls_paused"]
    assert request("/api/chat", "POST", turn(), headers)[2]["status"] == "completed"


def test_rate_limit_precedes_provider_budget(desk):
    request, session, sent, root, _ = desk
    headers, _ = session()
    for _ in range(10):
        assert request("/api/inbox", "POST", turn(), headers)[0] == 200
    assert request("/api/chat", "POST", turn(), headers)[0] == 429
    assert not sent
    with Journal(root / "runtime/research.sqlite") as journal:
        assert journal.budget_snapshot()["committed_micro_usd"] == 0


def test_duplicate_csrf_and_origin_headers_are_rejected(desk):
    _, session, sent, _, port = desk
    headers, _ = session()
    for field in ("Origin", "X-Quanto-CSRF"):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        raw = json.dumps(turn())
        connection.putrequest("POST", "/api/chat")
        for name, value in headers.items():
            connection.putheader(name, value)
        connection.putheader(field, headers[field])
        connection.putheader("Content-Length", str(len(raw)))
        connection.endheaders(raw.encode())
        response = connection.getresponse()
        assert response.status == 403
        response.read()
        connection.close()
    assert not sent


@pytest.mark.parametrize("changes", [{"agent_id": []}, {"message": []},
                                     {"request_id": "invalid"}, {"message": "x" * 4001}])
def test_malformed_chat_input_is_rejected_without_spend(desk, changes):
    request, session, sent, _, _ = desk
    headers, _ = session()
    assert request("/api/chat", "POST", turn(**changes), headers)[0] == 400
    assert not sent


def test_secret_pattern_in_allowlisted_context_refuses_dispatch(desk):
    request, session, sent, root, _ = desk
    (root / "docs/STATUS.md").write_text("A pasted credential: sk-ant-synthetic1234567890")
    headers, _ = session()
    result = request("/api/chat", "POST", turn(), headers)[2]
    assert result["status"] == "error" and not sent


def test_health_metadata_is_bounded_local_and_has_truthful_freshness(desk):
    request, _, _, root, _ = desk
    assert request("/api/health-details")[0] == 503
    path = root / "runtime/operations.json"
    path.write_text(json.dumps({"schema_version": 1, "service": "quanto", "service_state": "healthy",
                                "checked_at": "2000-01-01T00:00:00+00:00", "observation_gaps": []}))
    assert request("/api/health-details")[2]["status"] == "stale"
    path.unlink()
    path.symlink_to(root / "runtime/status.json")
    assert request("/api/health-details")[0] == 503

"""Local HTTP boundary checks using synthetic status observations."""

import copy
import http.client
import json
import threading
from datetime import datetime, timezone

import pytest

from quanto.dashboard import MAX_STATUS_BYTES, make_server, validate_status


@pytest.fixture
def status():
    return {
        "schema_version": 1,
        "observed_at": "2026-11-01T16:00:00-08:00",
        "project": {
            "name": "Synthetic dashboard fixture",
            "phase": "testing",
            "summary": "A software test, not research evidence.",
            "repository_url": "https://example.com/private",
        },
        "agents": [{
            "id": "qa", "name": "Quality reviewer", "role": "Quality",
            "model": "recorded-model", "status": "running", "task": "Inspect fixture",
            "detail": "Inspect the exact revision.", "observed_at": "2026-11-01T16:00:00-08:00",
        }],
        "milestones": [{
            "id": "m1", "title": "Check snapshot", "status": "pending",
            "evidence": "Not yet verified.",
        }],
        "events": [{
            "id": "e1", "timestamp": "2026-11-01T16:00:00-08:00",
            "kind": "review", "title": "Review requested", "detail": "Synthetic event",
            "agent_id": "qa",
        }],
        "decisions": [{
            "id": "d1", "title": "Loopback", "status": "accepted",
            "decision": "Serve locally.", "reason": "Keep this desk local.",
        }],
        "blockers": [{
            "id": "b1", "title": "Outside review pending", "detail": "No key available.",
            "scope": "Outside-model review",
        }],
        "budget": {
            "daily_limit_usd": 20, "spent_usd": None, "reserved_usd": None,
            "scope": "Unknown account spend", "timezone": "America/Los_Angeles",
        },
    }


@pytest.fixture
def desk(tmp_path):
    server = make_server(tmp_path, port=0)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01))
    thread.start()
    port = server.server_address[1]

    def request(path="/", *, method="GET", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    yield request, tmp_path / "runtime" / "status.json", port
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


def write_status(path, data):
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data))


def test_status_round_trip_preserves_unknown_budget_and_recorded_text(desk, status):
    request, path, _ = desk
    status["agents"][0]["detail"] = '<script>alert("snapshot text")</script>'
    write_status(path, status)
    code, headers, body = request("/api/status")
    assert code == 200
    assert json.loads(body) == status
    assert json.loads(body)["budget"]["spent_usd"] is None
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert "Access-Control-Allow-Origin" not in headers


@pytest.mark.parametrize("route", ["/", "/index.html", "/app.js", "/styles.css", "/health"])
def test_only_fixed_assets_and_health_are_available_without_snapshot(desk, route):
    request, _, _ = desk
    code, headers, body = request(route)
    assert code == 200 and body
    assert "default-src 'none'" in headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "unsafe-inline" not in headers["Content-Security-Policy"]
    assert headers["X-Frame-Options"] == "DENY"


def test_dependency_graph_preserves_edges_when_completion_changes(desk, status):
    request, path, _ = desk
    status["milestones"].append({"id": "m2", "title": "Next step", "status": "pending",
                                 "evidence": "Await earlier check."})
    edge = {"from": "m1", "to": "m2", "reason": "The earlier check supplies evidence."}
    status["dependencies"] = [edge]
    write_status(path, status)
    first = json.loads(request("/api/status")[2])
    assert first["dependencies"] == [edge]
    status["milestones"][0]["status"] = "completed"
    write_status(path, status)
    second = json.loads(request("/api/status")[2])
    assert second["milestones"][0]["status"] == "completed"
    assert second["dependencies"] == first["dependencies"]


@pytest.mark.parametrize("edges", [
    [{"from": "m1", "to": "missing", "reason": "Unknown prerequisite"}],
    [{"from": "m1", "to": "m2", "reason": "First"},
     {"from": "m2", "to": "m1", "reason": "Cycle"}],
    [{"from": "m1", "to": "m2", "reason": "First"},
     {"from": "m1", "to": "m2", "reason": "Duplicate"}],
])
def test_dependency_graph_rejects_unknown_cycles_and_duplicate_edges(status, edges):
    status["milestones"].append({"id": "m2", "title": "Next step", "status": "pending",
                                 "evidence": "Synthetic fixture"})
    status["dependencies"] = edges
    with pytest.raises(ValueError, match="Dependency"):
        validate_status(status)


@pytest.mark.parametrize("route", [
    "/runtime/status.json", "/docs/CONTEXT.md", "/../AGENTS.md", "/%2e%2e/AGENTS.md",
    "/web/../../AGENTS.md", "/assets/", "//example.com/api/status", "/api/anything",
])
def test_arbitrary_files_and_traversal_are_unavailable(desk, route):
    request, _, _ = desk
    assert request(route)[0] == 404


def test_missing_snapshot_reports_unavailable_without_progress(desk):
    request, _, _ = desk
    code, _, body = request("/api/status")
    assert code == 503
    assert json.loads(body)["error"] == "status_missing"
    assert "agents" not in json.loads(body)


@pytest.mark.parametrize("raw", [b"{", b"[]", b"\xff", b'{"schema_version": 2}', b"x" * (MAX_STATUS_BYTES + 1)])
def test_malformed_or_oversize_snapshot_reports_invalid(desk, raw):
    request, path, _ = desk
    path.parent.mkdir()
    path.write_bytes(raw)
    code, _, body = request("/api/status")
    assert code == 503
    assert json.loads(body)["error"] == "status_invalid"


def test_status_symlink_is_not_read(desk, status, tmp_path):
    request, path, _ = desk
    outside = tmp_path / "not-status.json"
    outside.write_text(json.dumps(status))
    path.parent.mkdir()
    path.symlink_to(outside)
    assert request("/api/status")[0] == 503


def test_nonfinite_values_in_extra_fields_do_not_break_response_serialization(desk, status):
    request, path, _ = desk
    status["extra"] = float("nan")
    write_status(path, status)
    code, _, body = request("/api/status")
    assert code == 503
    assert json.loads(body)["error"] == "status_invalid"


@pytest.mark.parametrize("headers", [
    {"Host": "remote.example"}, {"Host": "127.0.0.1.evil.example"},
    {"Host": "localhost:1"}, {"Origin": "https://remote.example"},
    {"Origin": "null"}, {"Origin": "http://localhost:1"},
])
def test_nonlocal_hosts_and_origins_are_rejected(desk, headers):
    request, _, _ = desk
    assert request("/api/status", headers=headers)[0] == 403


def test_matching_loopback_origin_is_allowed(desk):
    request, _, port = desk
    code, _, _ = request("/health", headers={
        "Host": f"localhost:{port}", "Origin": f"http://localhost:{port}",
    })
    assert code == 200


def test_duplicate_host_is_rejected(desk):
    _, _, port = desk
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    connection.putrequest("GET", "/health", skip_host=True)
    connection.putheader("Host", f"127.0.0.1:{port}")
    connection.putheader("Host", "remote.example")
    connection.endheaders()
    response = connection.getresponse()
    assert response.status == 403
    response.read()
    connection.close()


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def test_write_methods_are_unavailable(desk, method):
    request, path, _ = desk
    assert request("/api/status", method=method)[0] == 405
    assert not path.exists()


def test_head_has_headers_without_body(desk):
    request, _, _ = desk
    code, headers, body = request("/", method="HEAD")
    assert code == 200
    assert int(headers["Content-Length"]) > 0
    assert body == b""


def test_external_bind_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="127.0.0.1"):
        make_server(tmp_path, host="0.0.0.0", port=0)


@pytest.mark.parametrize("mutation", [
    lambda data: data.update(schema_version=True),
    lambda data: data.update(observed_at="2026-11-01T12:00:00"),
    lambda data: data.update(agents={}),
    lambda data: data["agents"].append(copy.deepcopy(data["agents"][0])),
    lambda data: data["agents"][0].update(observed_at="yesterday"),
    lambda data: data["milestones"][0].update(evidence=[]),
    lambda data: data["budget"].update(spent_usd=-1),
    lambda data: data["budget"].update(daily_limit_usd=True),
    lambda data: data["budget"].pop("reserved_usd"),
    lambda data: data["budget"].update(reserved_usd=float("inf")),
])
def test_incomplete_and_invalid_schema_is_rejected(status, mutation):
    mutation(status)
    with pytest.raises(ValueError):
        validate_status(status)


def test_readiness_is_distinct_from_liveness_without_status_or_sessions(desk):
    request, path, _ = desk
    code, headers, body = request("/ready")
    assert code == 503
    assert json.loads(body)["status"] == "degraded"
    assert "Set-Cookie" not in headers
    assert request("/health")[0] == 200
    assert not (path.parent / "conversations.sqlite").exists()
    assert not (path.parent / "research.sqlite").exists()


@pytest.mark.parametrize("raw", [b"{", b"[]", b'{"schema_version":1}',
                                  b"x" * (MAX_STATUS_BYTES + 1)])
def test_invalid_or_oversized_status_degrades_readiness(desk, raw):
    request, path, _ = desk
    path.parent.mkdir()
    path.write_bytes(raw)
    code, _, body = request("/ready")
    assert code == 503 and json.loads(body)["checks"]["status_snapshot"] == "unavailable"
    assert request("/health")[0] == 200


def test_valid_old_observation_is_ready_without_claiming_new_research(desk, status):
    request, path, _ = desk
    status["observed_at"] = "2000-01-01T00:00:00+00:00"
    write_status(path, status)
    code, _, body = request("/ready")
    assert code == 200 and json.loads(body) == {"service": "quanto", "status": "ready",
                                               "checks": {"status_snapshot": "ready", "local_assets": "ready"}}
    assert json.loads(request("/api/status")[2])["observed_at"] == status["observed_at"]


def test_missing_packaged_asset_degrades_readiness(desk, status, monkeypatch):
    from quanto import dashboard

    request, path, _ = desk
    write_status(path, status)
    monkeypatch.setitem(dashboard.ASSETS, "/required-test-asset", ("missing-file.js", "text/javascript"))
    code, _, body = request("/ready")
    assert code == 503
    assert json.loads(body)["checks"] == {"status_snapshot": "ready", "local_assets": "unavailable"}


def test_detailed_health_preserves_liveness_when_readiness_degraded(desk):
    request, path, _ = desk
    path.parent.mkdir()
    (path.parent / "operations.json").write_text(json.dumps({
        "schema_version": 1, "service": "quanto", "checked_at": datetime.now(timezone.utc).isoformat(),
        "service_state": "healthy", "readiness_state": "degraded", "readiness_reason": "snapshot_missing",
        "observation_gaps": [],
    }))
    code, _, body = request("/api/health-details")
    data = json.loads(body)
    assert code == 200 and data["status"] == "degraded"
    assert data["liveness_state"] == "healthy"
    assert data["readiness_state"] == "degraded"

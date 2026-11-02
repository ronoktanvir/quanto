"""Read-only, loopback-only operator dashboard over an explicit status snapshot."""

from __future__ import annotations

import json
import math
from http.cookies import SimpleCookie, CookieError
import secrets
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from quanto.conversations import Conversations, ConversationError

MAX_STATUS_BYTES = 2 * 1024 * 1024
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}
CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
    "img-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'; "
    "frame-ancestors 'none'"
)


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"Non-finite JSON number: {value}")


def _timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def validate_status(data: object) -> None:
    """Reject incomplete snapshots instead of displaying invented defaults."""
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int:
        raise ValueError("Status snapshot must declare schema_version 1.")
    if data["schema_version"] != 1 or not _timestamp(data.get("observed_at")):
        raise ValueError("Status snapshot version or observation timestamp is invalid.")

    def strings(record: object, fields: tuple[str, ...]) -> None:
        if not isinstance(record, dict) or any(
            not isinstance(record.get(field), str) for field in fields
        ):
            raise ValueError("Status snapshot contains missing or invalid text fields.")

    strings(data.get("project"), ("name", "phase", "summary", "repository_url"))
    collections = {
        "agents": ("id", "name", "role", "model", "status", "task", "detail", "observed_at"),
        "milestones": ("id", "title", "status", "evidence"),
        "events": ("id", "timestamp", "kind", "title", "detail", "agent_id"),
        "decisions": ("id", "title", "status", "decision", "reason"),
        "blockers": ("id", "title", "detail", "scope"),
    }
    for key, fields in collections.items():
        records = data.get(key)
        if not isinstance(records, list):
            raise ValueError(f"Status snapshot must contain a {key} list.")
        identifiers = set()
        for record in records:
            strings(record, fields)
            if not record["id"] or record["id"] in identifiers:
                raise ValueError(f"Status snapshot contains invalid or duplicate {key} IDs.")
            identifiers.add(record["id"])
            timestamp = "observed_at" if key == "agents" else "timestamp"
            if key in ("agents", "events") and not _timestamp(record[timestamp]):
                raise ValueError(f"Status snapshot contains an invalid {key} timestamp.")
    budget = data.get("budget")
    strings(budget, ("scope", "timezone"))
    for field in ("daily_limit_usd", "spent_usd", "reserved_usd"):
        value = budget.get(field)
        if field != "daily_limit_usd" and field in budget and value is None:
            continue
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError(f"Status snapshot contains an invalid budget {field}.")

    # Optional recorded prerequisite graph. Status changes never create edges.
    dependencies = data.get("dependencies", [])
    if not isinstance(dependencies, list) or len(dependencies) > 256:
        raise ValueError("Dependencies must be a bounded list.")
    identifiers = {item["id"] for item in data["milestones"]}
    outgoing = {identifier: [] for identifier in identifiers}
    incoming = dict.fromkeys(identifiers, 0)
    seen = set()
    for edge in dependencies:
        strings(edge, ("from", "to", "reason"))
        pair = (edge["from"], edge["to"])
        if (pair[0] not in identifiers or pair[1] not in identifiers
                or pair in seen or pair[0] == pair[1] or len(edge["reason"]) > 500):
            raise ValueError("Dependency references must be unique known milestones.")
        seen.add(pair)
        outgoing[pair[0]].append(pair[1])
        incoming[pair[1]] += 1
    ready = [identifier for identifier in identifiers if incoming[identifier] == 0]
    visited = 0
    while ready:
        identifier = ready.pop()
        visited += 1
        for following in outgoing[identifier]:
            incoming[following] -= 1
            if incoming[following] == 0:
                ready.append(following)
    if visited != len(identifiers):
        raise ValueError("Dependency graph must not contain a cycle.")


def make_server(
    root: Path, host: str = "127.0.0.1", port: int = 8765, *, transport=None
) -> ThreadingHTTPServer:
    """Create a local server. Port zero is supported for isolated tests."""
    if host != "127.0.0.1":
        raise ValueError("The dashboard must bind to 127.0.0.1.")
    status_path = Path(root).resolve() / "runtime" / "status.json"
    web_root = Path(__file__).resolve().parent / "web"
    conversations = None
    backend_lock = threading.Lock()

    def backend():
        nonlocal conversations
        with backend_lock:
            if conversations is None:
                conversations = Conversations(Path(root), transport=transport)
        return conversations

    def read_status():
        if status_path.is_symlink() or status_path.parent.is_symlink():
            raise ValueError("Status snapshot must be a regular local file.")
        if status_path.exists() and not status_path.is_file():
            raise ValueError("Status snapshot must be a regular local file.")
        with status_path.open("rb") as snapshot:
            raw = snapshot.read(MAX_STATUS_BYTES + 1)
        if len(raw) > MAX_STATUS_BYTES:
            raise ValueError("Status snapshot exceeds the size limit.")
        data = json.loads(raw, parse_constant=_reject_nonfinite)
        validate_status(data)
        return data

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            # Request paths and snapshot content do not belong in runtime logs.
            pass

        def _reply(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", CSP)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            if getattr(self, "session_cookie", None):
                self.send_header("Set-Cookie", "quanto_session=" + self.session_cookie
                                 + "; Path=/; HttpOnly; SameSite=Strict")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, status: int, data: object) -> None:
            self._reply(status, json.dumps(data, allow_nan=False).encode(), "application/json")

        def _trusted_request(self, *, write=False) -> bool:
            hosts = self.headers.get_all("Host", [])
            origins = self.headers.get_all("Origin", [])
            if len(hosts) != 1 or len(origins) > 1:
                return False
            expected_port = self.server.server_address[1]
            allowed_hosts = {f"127.0.0.1:{expected_port}", f"localhost:{expected_port}"}
            if expected_port == 80:
                allowed_hosts.update(("127.0.0.1", "localhost"))
            if hosts[0].lower() not in allowed_hosts:
                return False
            if write:
                return len(origins) == 1 and origins[0] == f"http://{hosts[0]}"
            return not origins or origins[0].lower() == f"http://{hosts[0].lower()}"

        def _session(self, *, create=False):
            cookies = self.headers.get_all("Cookie", [])
            if len(cookies) > 1 or (cookies and cookies[0].count("quanto_session=") > 1):
                raise ConversationError("Ambiguous session cookie", 403)
            parsed = SimpleCookie()
            try:
                if cookies:
                    parsed.load(cookies[0])
            except CookieError:
                raise ConversationError("Invalid session cookie", 403) from None
            token = parsed.get("quanto_session")
            session, csrf, fresh = backend().session(token.value if token else None, create=create)
            if fresh:
                self.session_cookie = fresh
            return session, csrf

        def do_GET(self) -> None:
            if not self._trusted_request():
                self._json(403, {"error": "forbidden", "message": "Only local requests are allowed."})
                return
            parsed = urlsplit(self.path)
            if parsed.scheme or parsed.netloc or parsed.fragment:
                self._json(404, {"error": "not_found", "message": "Page not found."})
                return
            path = parsed.path
            if path == "/health":
                self._json(200, {"status": "ok", "service": "quanto"})
            elif path == "/ready":
                self._ready()
            elif path == "/api/status":
                self._status()
            elif path == "/api/health-details":
                self._health_details()
            elif path in ("/api/session", "/api/conversations", "/api/inbox"):
                try:
                    session, csrf = self._session(create=path == "/api/session")
                    if path == "/api/session":
                        data = backend().session_info(csrf)
                    else:
                        agent_id = parse_qs(parsed.query).get("agent_id", [""])[0]
                        data = (backend().list_inquiries(session, agent_id) if path == "/api/inbox"
                                else backend().list_conversations(session, agent_id))
                    self._json(200, data)
                except ConversationError as exc:
                    self._json(exc.status, {"error": str(exc)})
                except (ValueError, OSError):
                    self._json(503, {"error": "Local conversation service unavailable"})
            elif path in ASSETS:
                name, content_type = ASSETS[path]
                self._reply(200, (web_root / name).read_bytes(), content_type)
            else:
                self._json(404, {"error": "not_found", "message": "Page not found."})

        def _status(self) -> None:
            try:
                data = read_status()
            except FileNotFoundError:
                self._json(503, {
                    "error": "status_missing",
                    "message": "No status snapshot is available. The operator must write runtime/status.json.",
                })
                return
            except (ValueError, OSError, UnicodeError, RecursionError):
                self._json(503, {
                    "error": "status_invalid",
                    "message": "The status snapshot is unreadable or invalid. No progress can be inferred.",
                })
                return
            self._json(200, data)

        def _ready(self) -> None:
            checks = {"status_snapshot": "unavailable", "local_assets": "unavailable"}
            try:
                # Readability and schema determine website readiness. The
                # observation age remains visible separately in the interface.
                read_status()
                checks["status_snapshot"] = "ready"
            except (ValueError, OSError, UnicodeError, RecursionError):
                pass
            try:
                if web_root.is_symlink():
                    raise ValueError("Local assets must be regular packaged files")
                for name in {asset[0] for asset in ASSETS.values()}:
                    path = web_root / name
                    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_STATUS_BYTES:
                        raise ValueError("Missing or oversized local asset")
                    with path.open("rb") as asset:
                        if not asset.read(1):
                            raise ValueError("Empty local asset")
                checks["local_assets"] = "ready"
            except (ValueError, OSError):
                pass
            ready = all(value == "ready" for value in checks.values())
            self._json(200 if ready else 503, {"service": "quanto",
                                             "status": "ready" if ready else "degraded",
                                             "checks": checks})

        def _health_details(self) -> None:
            path = status_path.parent / "operations.json"
            try:
                if path.is_symlink() or path.parent.is_symlink():
                    raise ValueError("Health metadata must be a regular project file")
                with path.open("rb") as source:
                    raw = source.read(1_000_001)
                if len(raw) > 1_000_000:
                    raise ValueError("Health metadata is too large")
                data = json.loads(raw, parse_constant=_reject_nonfinite)
                if (not isinstance(data, dict) or data.get("schema_version") != 1
                        or data.get("service") != "quanto" or not _timestamp(data.get("checked_at"))):
                    raise ValueError("Invalid health metadata")
                checked = datetime.fromisoformat(data["checked_at"].replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - checked).total_seconds()
                status = data.get("service_state", "unknown") if 0 <= age <= 90 else "stale"
                if 0 <= age <= 90 and data.get("readiness_state") == "degraded":
                    status = "degraded"
                result = {"status": status, "summary": data.get("awake_host_limitation", ""),
                          "liveness_state": data.get("service_state", "unknown"),
                          "model_calls_paused": (path.parent / "model_calls_paused").exists()}
                for key in ("checked_at", "last_success", "reason", "ownership", "restarts",
                            "restarts_last_hour", "consecutive_failures", "readiness_state",
                            "readiness_reason"):
                    value = data.get(key)
                    if type(value) in (str, int, float, bool) or value is None:
                        result[key] = value
                result["observation_gap_count"] = len(data.get("observation_gaps", []))
                self._json(200, result)
            except (ValueError, OSError, TypeError, RecursionError):
                self._json(503, {"error": "health_unavailable",
                                 "message": "No valid supervisor health observation is available."})

        def do_HEAD(self) -> None:
            self.do_GET()

        def do_POST(self) -> None:
            if self.command != "POST" or self.path not in (
                "/api/chat", "/api/inbox", "/api/model-calls/pause", "/api/model-calls/resume"
            ):
                self._json(405, {"error": "method_not_allowed"})
                return
            if not self._trusted_request(write=True):
                self._json(403, {"error": "Exact local origin is required"})
                return
            self.connection.settimeout(10)
            try:
                session, csrf = self._session()
                csrf_headers = self.headers.get_all("X-Quanto-CSRF", [])
                if len(csrf_headers) != 1 or not secrets.compare_digest(csrf_headers[0].encode(), csrf.encode()):
                    raise ConversationError("Invalid CSRF token", 403)
                lengths = self.headers.get_all("Content-Length", [])
                if (len(lengths) != 1 or not lengths[0].isdigit()
                        or int(lengths[0]) > 32_768 or self.headers.get_all("Transfer-Encoding", [])):
                    raise ConversationError("A body up to 32768 bytes is required", 413)
                types = self.headers.get_all("Content-Type", [])
                if len(types) != 1 or types[0].split(";", 1)[0].strip() != "application/json":
                    raise ConversationError("JSON content type required", 415)
                raw = self.rfile.read(int(lengths[0]))
                if len(raw) != int(lengths[0]):
                    raise ConversationError("Incomplete JSON request")

                def unique_pairs(pairs):
                    result = {}
                    for key, value in pairs:
                        if key in result:
                            raise ConversationError("Duplicate JSON fields are invalid")
                        result[key] = value
                    return result

                data = json.loads(raw, parse_constant=_reject_nonfinite, object_pairs_hook=unique_pairs)
                if not isinstance(data, dict):
                    raise ConversationError("A JSON object is required")
                if self.path == "/api/chat":
                    result = backend().chat(session, data)
                elif self.path == "/api/inbox":
                    result = backend().inbox(session, data)
                else:
                    marker = Path(root).resolve() / "runtime" / "model_calls_paused"
                    if self.path.endswith("/pause"):
                        marker.touch(mode=0o600)
                    else:
                        marker.unlink(missing_ok=True)
                    result = {"model_calls_paused": marker.exists()}
                self._json(200, result)
            except ConversationError as exc:
                self.close_connection = True
                self._json(exc.status, {"error": str(exc)})
            except (ValueError, OSError, RecursionError):
                self.close_connection = True
                self._json(400, {"error": "Invalid or unavailable local request"})

        do_PUT = do_POST
        do_PATCH = do_POST
        do_DELETE = do_POST
        do_OPTIONS = do_POST

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server


def serve(root: Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Serve until interrupted; research and execution are never started here."""
    server = make_server(root, host, port)
    print(f"Quanto dashboard: http://127.0.0.1:{server.server_address[1]}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

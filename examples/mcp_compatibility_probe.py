"""Observe the installed Claude Code MCP client using an invented local server."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile


def fixture_server(trace):
    while raw := sys.stdin.buffer.readline(65_537):
        if len(raw) > 65_536:
            return 1
        request = json.loads(raw)
        method = request.get("method")
        version = request.get("params", {}).get("protocolVersion")
        known = {"initialize", "notifications/initialized", "server/discover",
                 "tools/list", "tools/call", "ping"}
        with trace.open("a", encoding="utf-8") as log:
            log.write(json.dumps({"method": method if method in known else "other",
                                  "version": version if isinstance(version, str) else None,
                                  "pid": os.getpid()}) + "\n")
        if "id" not in request:
            continue
        response = {"jsonrpc": "2.0", "id": request["id"]}
        if method == "initialize":
            response["result"] = {"protocolVersion": version, "capabilities": {"tools": {}},
                                  "serverInfo": {"name": "quanto-fixture", "version": "1"}}
        elif method == "tools/list":
            response["result"] = {"tools": [{"name": "fixture_status", "description": "Return a test marker",
                    "inputSchema": {"type": "object", "additionalProperties": False}}]}
        elif method == "tools/call" and request.get("params", {}).get("name") == "fixture_status":
            if request["params"].get("arguments", {}) == {}:
                response["result"] = {"content": [{"type": "text", "text": "invented fixture"}]}
            else:
                response["error"] = {"code": -32602, "message": "The fixture takes no arguments"}
        elif method == "ping":
            response["result"] = {}
        else:
            response["error"] = {"code": -32601, "message": "Unsupported fixture method"}
        print(json.dumps(response, separators=(",", ":")), flush=True)
    return 0


def probe():
    claude = shutil.which("claude")
    if not claude:
        raise RuntimeError("Claude Code is not installed")
    with tempfile.TemporaryDirectory(prefix="quanto-mcp-probe-") as name:
        base = Path(name).resolve()
        config, project = base / "config", base / "project"
        config.mkdir(mode=0o700)
        project.mkdir(mode=0o700)
        trace = base / "events.jsonl"
        server = {"type": "stdio", "command": sys.executable,
                  "args": ["-I", "-S", "-B", str(Path(__file__).resolve()), "--fixture-server", str(trace)]}
        # Supply a user-scope fixture in an isolated Claude configuration directory.
        # The CLI is only asked to list servers. No prompt or model key is supplied.
        (config / ".claude.json").write_text(json.dumps({"mcpServers": {"quanto_fixture": server}}))
        env = {"PATH": os.environ["PATH"], "CLAUDE_CONFIG_DIR": str(config),
               "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "ANTHROPIC_BASE_URL": "http://127.0.0.1:1"}
        version = subprocess.run([claude, "--version"], env=env, cwd=project, stdin=subprocess.DEVNULL,
                                 capture_output=True, text=True, timeout=10, check=True).stdout.strip()
        proc = subprocess.Popen([claude, "mcp", "list"], env=env, cwd=project, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            stdout, stderr = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate(timeout=3)
            raise RuntimeError("The isolated client health check timed out") from None
        events = [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
        absent = []
        for pid in {e["pid"] for e in events}:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                absent.append(True)
            else:
                absent.append(False)
        result = {"client": version, "client_exit": proc.returncode, "fixture_listed": b"quanto_fixture" in stdout,
                  "fixture_connected": any(b"quanto_fixture" in line and b"Connected" in line
                                           for line in stdout.splitlines()),
                  "methods": [e["method"] for e in events],
                  "requested_versions": [e["version"] for e in events if e["version"]],
                  "observed_fixture_processes_absent": bool(absent) and all(absent),
                  "stderr_sha256": hashlib.sha256(stderr).hexdigest(), "evidence_kind": "synthetic_fixture"}
        print(json.dumps(result, sort_keys=True))
        return 0 if proc.returncode == 0 and result["fixture_connected"] and events else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-server", type=Path, metavar="TRACE")
    args = parser.parse_args()
    raise SystemExit(fixture_server(args.fixture_server) if args.fixture_server else probe())

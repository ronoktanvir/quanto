"""Exercise the fixture on its actual standard streams without installing a client."""
import json
from pathlib import Path
import subprocess
import sys


def test_discovery_fallback_and_fixture_call(tmp_path):
    script = Path(__file__).resolve().parents[1] / "examples/mcp_compatibility_probe.py"
    trace = tmp_path / "fixture.jsonl"
    messages = [
        {"id": 1, "method": "server/discover"},
        {"id": 2, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
        {"method": "notifications/initialized"},
        {"id": 3, "method": "tools/list"},
        {"id": 4, "method": "tools/call", "params": {"name": "fixture_status", "arguments": {}}},
        {"id": 5, "method": "tools/call", "params": {"name": "fixture_status", "arguments": {"unexpected": 1}}},
    ]
    raw = "".join(json.dumps({"jsonrpc": "2.0", **msg}) + "\n" for msg in messages)
    reply = subprocess.run([sys.executable, "-I", "-S", "-B", str(script), "--fixture-server", str(trace)],
                           input=raw, capture_output=True, text=True, cwd=tmp_path, timeout=5, check=True)
    assert not reply.stderr
    records = {v["id"]: v for v in map(json.loads, reply.stdout.splitlines())}
    assert records[1]["error"]["code"] == -32601
    assert records[2]["result"]["protocolVersion"] == "2025-11-25"
    assert [t["name"] for t in records[3]["result"]["tools"]] == ["fixture_status"]
    assert records[4]["result"]["content"] == [{"type": "text", "text": "invented fixture"}]
    assert records[5]["error"]["code"] == -32602

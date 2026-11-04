"""Code-only reconstruction of the pinned worker's pre-session module identity."""

import ast
import hashlib
import importlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from types import ModuleType, SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = ROOT / "runtime/development-cycle-registration-v2-preparation/prepare_current_code.py"
REG_MANIFEST = REG.with_name("source-manifest.json")
WORKER = ROOT / "runtime/development-cycle-launch-v2-preparation/paid_worker.py"
REG_SHA = "3f52a95452d9a20c6c456624f33a70c717d9f1fc28d83ae65f178e67e9d7047d"
REG_MANIFEST_SHA = "aa65675f3c7886a2d950b75928811d4f7189adbc2342a383b983f0ea20ea70c4"
WORKER_SHA = "9a59cb3eb37f8b6f06d17abde2a474da13fba07264bd37c634ee12a07f0cd01c"


def checked(path, expected):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    return raw


def generate():
    assert (
        sys.version_info[:3] == (3, 11, 9)
        and sys.flags.isolated
        and sys.flags.no_site
        and sys.dont_write_bytecode
    )
    raw = checked(REG, REG_SHA)
    reg = ModuleType("reviewed_registration")
    reg.__file__ = str(REG)
    exec(compile(raw, str(REG), "exec", dont_inherit=True), reg.__dict__)
    manifest = json.loads(checked(REG_MANIFEST, REG_MANIFEST_SHA))
    worker = checked(WORKER, WORKER_SHA)
    tree = ast.parse(worker)
    proc = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "execute")

    def sets(node, name):
        return isinstance(node, ast.Assign) and any(
            isinstance(x, ast.Name) and x.id == name for x in node.targets
        )

    start = next(i for i, n in enumerate(proc.body) if sets(n, "loader"))
    end = next(i for i, n in enumerate(proc.body) if sets(n, "before_broker"))
    segment = proc.body[start : end + 1]
    definitions = [
        n
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.ClassDef))
        and n.name in {"Refused", "need", "configuration"}
    ]
    dummy = HERE / "never-opened-invented-root"
    suite = "a" * 64
    models = {
        r: "claude-opus-5-5" if r in ("data_critic", "statistical_critic") else "claude-haiku-5-5"
        for r in (
            "director",
            "hypothesis",
            "engineer",
            "data_critic",
            "statistical_critic",
            "quality",
            "scope",
        )
    }
    config = {
        "run_key": "new-invented",
        "suite_sha256": suite,
        "models": models,
        "failure_ids": [],
        "evidence_kind": "historical_market_data",
    }
    context = {
        "reg": reg,
        "source": ROOT,
        "root": dummy,
        "plan": {"request_template": {**config, "run_key": "old-invented"}},
        "manifest": manifest,
        "authority": SimpleNamespace(),
        "request_text": reg.canonical(config).decode(),
        "importlib": importlib,
        "sqlite3": sqlite3,
        "os": os,
        "result": {
            "mapping": {"suite": {"artifact_sha256": suite}},
            "after": {"research": {"physical": {}}, "control": {"physical": {}}},
        },
    }
    stdlib = Path(reg.sysconfig.get_path("stdlib")).resolve()

    def deny(event, args):
        if event == "sqlite3.connect" or event.startswith(
            ("socket.", "subprocess.", "os.exec", "os.spawn", "os.fork")
        ):
            raise RuntimeError("reference_forbidden_effect")
        if event == "open" and not isinstance(args[0], int):
            path = Path(os.fsdecode(args[0]))
            flags = args[2]
            if flags & (os.O_CREAT | os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_TRUNC):
                raise RuntimeError("reference_write")
            if (
                path in (REG, REG_MANIFEST, WORKER, ROOT / "uv.lock", ROOT / "pyproject.toml")
                or ROOT / "src/quanto" in path.parents
                or stdlib in path.resolve().parents
                or str(path).startswith("/usr/share/zoneinfo/")
            ):
                return
            raise RuntimeError("reference_noncode_read")

    sys.addaudithook(deny)
    # This is the exact accepted function body from load_product through
    # before_broker. No registration, session, store, key or provider is opened.
    block = ast.Module(body=definitions + segment, type_ignores=[])
    exec(compile(block, str(WORKER), "exec", dont_inherit=True), context)
    loaded = context["before_loaded"]
    compiled = context["before_compiled"]
    assert len(compiled) == 21 and set(compiled) == set(loaded["modules"])
    return {
        "schema_version": 1,
        "worker_sha256": WORKER_SHA,
        "registration_sha256": REG_SHA,
        "registration_manifest_sha256": REG_MANIFEST_SHA,
        "compiled": compiled,
        "loaded_sha256": reg.sha(reg.canonical(loaded)),
        "broker_code_sha256": reg.sha(reg.canonical(context["before_broker"])),
        "worker_source_segment_sha256": reg.sha(ast.dump(block, include_attributes=False).encode()),
    }


if __name__ == "__main__":
    print(json.dumps(generate(), sort_keys=True))

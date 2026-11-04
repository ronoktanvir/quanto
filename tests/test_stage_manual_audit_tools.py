"""Protect the audit restorer's source identities and default verification boundary."""
import hashlib
from pathlib import Path
import runpy


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/stage_manual_audit_tools.py"


def test_versioned_sources_match_reviewed_pins():
    stager = runpy.run_path(str(SCRIPT))
    pins = {**stager["TOOLS"], "derive_worker_reference.py": stager["REFERENCE_SHA"]}
    for name, expected in pins.items():
        assert hashlib.sha256((stager["SOURCE"] / name).read_bytes()).hexdigest() == expected


def test_verification_skips_installation(monkeypatch):
    stage = runpy.run_path(str(SCRIPT))["stage"]
    calls = []
    monkeypatch.setitem(stage.__globals__, "rebuild", lambda reader: calls.append(reader) or {})
    def no_install(*args):
        raise AssertionError("verification must not publish runtime files")
    monkeypatch.setattr(runpy, "run_path", lambda _: {"checked_read": "reader", "install_reviewed_files": no_install})
    assert stage(verify_only=True) == 0
    assert calls == ["reader"]

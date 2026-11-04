"""Recovery of source tooling must preserve existing operator state."""
import hashlib
import importlib.util
from pathlib import Path

import pytest


def fixture_tools(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/stage_registration_tools.py"
    spec = importlib.util.spec_from_file_location("registration_staging_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "source"
    source.mkdir()
    files = {module.CONTROLLER: b"# fixture controller\n", module.TESTS: b"# fixture checks\n",
             "source-manifest.json": b'{"fixture":true}'}
    for name in (module.CONTROLLER, module.TESTS):
        (source / name).write_bytes(files[name])
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "SOURCE", source)
    monkeypatch.setattr(module, "STAGE", tmp_path / "runtime/stage")
    monkeypatch.setattr(module, "PINS", {k: hashlib.sha256(v).hexdigest() for k, v in files.items()})
    monkeypatch.setattr(module, "manifest_bytes", lambda controller: files["source-manifest.json"])
    return module, files


def test_recovers_missing_files_once_and_preserves_existing_files(tmp_path, monkeypatch):
    module, expected = fixture_tools(tmp_path, monkeypatch)
    assert module.stage() == 3
    before = {p.name: (p.stat().st_ino, p.stat().st_mtime_ns) for p in module.STAGE.iterdir()}
    assert module.stage() == 0
    assert before == {p.name: (p.stat().st_ino, p.stat().st_mtime_ns) for p in module.STAGE.iterdir()}
    assert expected == {p.name: p.read_bytes() for p in module.STAGE.iterdir()}


def test_refuses_a_conflicting_existing_file_before_any_install(tmp_path, monkeypatch):
    module, _ = fixture_tools(tmp_path, monkeypatch)
    module.STAGE.mkdir(mode=0o700, parents=True)
    existing = module.STAGE / module.TESTS
    existing.write_bytes(b"operator's retained file")
    with pytest.raises(ValueError, match="identity mismatch"):
        module.stage()
    assert list(module.STAGE.iterdir()) == [existing]
    assert existing.read_bytes() == b"operator's retained file"

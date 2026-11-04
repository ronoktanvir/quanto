"""Exercise the source restorer in a temporary workspace without any private state."""
import importlib.util
from pathlib import Path
import shutil
import stat

import pytest


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts/stage_manual_cycle_tools.py"
    spec = importlib.util.spec_from_file_location("manual_staging_fixture", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    test_root = tmp_path.resolve()
    source = test_root / "operations/manual_cycle"
    source.mkdir(parents=True)
    for name in module.PINS:
        shutil.copyfile(root / "operations/manual_cycle" / name, source / name)
    monkeypatch.setattr(module, "ROOT", test_root)
    monkeypatch.setattr(module, "REVIEWED_ROOT", test_root)
    return module, source, test_root / "runtime" / module.STAGE_NAME


def test_restores_only_frozen_sources_and_preserves_exact_files(workspace):
    stager, source, destination = workspace
    (source / "unreviewed.py").write_text("raise AssertionError('unexpected source')\n")
    assert stager.stage() == 4
    assert set(stager.PINS) == {entry.name for entry in destination.iterdir()}
    assert stat.S_IMODE(destination.stat().st_mode) == 0o700
    for name in stager.PINS:
        assert (destination / name).read_bytes() == (source / name).read_bytes()
        assert stat.S_IMODE((destination / name).stat().st_mode) == 0o600
    retained = destination / "paid_worker.py"
    identity = retained.stat()
    (destination / "test_supervise.py").unlink()
    unrelated = destination / "operator-note"
    unrelated.write_text("retain")
    assert stager.stage() == 1
    assert stager.stage() == 0
    assert (retained.stat().st_ino, retained.stat().st_mtime_ns) == (
        identity.st_ino, identity.st_mtime_ns)
    assert unrelated.read_text() == "retain"


def test_existing_conflict_refused_before_install(workspace):
    stager, _source, destination = workspace
    destination.mkdir(mode=0o700, parents=True)
    conflict = destination / "test_supervise.py"
    conflict.write_text("retained content")
    with pytest.raises(ValueError, match="identity mismatch"):
        stager.stage()
    assert list(destination.iterdir()) == [conflict]
    assert conflict.read_text() == "retained content"


def test_source_drift_refused_before_creating_runtime(workspace):
    stager, source, destination = workspace
    (source / "supervise.py").write_text("altered source")
    with pytest.raises(ValueError, match="identity mismatch"):
        stager.stage()
    assert not destination.parent.exists()


def test_altered_pin_refused_by_joint_freeze_before_creating_runtime(workspace, monkeypatch):
    stager, _source, destination = workspace
    monkeypatch.setitem(stager.PINS, "supervise.py", "0" * 64)
    with pytest.raises(ValueError, match="joint freeze"):
        stager.stage()
    assert not destination.parent.exists()


def test_existing_target_symlink_cannot_redirect_install(workspace):
    stager, source, destination = workspace
    destination.mkdir(mode=0o700, parents=True)
    link = destination / "test_supervise.py"
    link.symlink_to(source / link.name)
    with pytest.raises(ValueError, match="symlink"):
        stager.stage()
    assert list(destination.iterdir()) == [link]
    assert link.is_symlink()


def test_wrong_workspace_refused_before_creating_runtime(workspace, monkeypatch):
    stager, _source, destination = workspace
    monkeypatch.setattr(stager, "REVIEWED_ROOT", stager.ROOT / "different")
    with pytest.raises(ValueError, match="reviewed workspace"):
        stager.stage()
    assert not destination.parent.exists()

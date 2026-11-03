"""Invented local snapshots; no production records or provider calls."""
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import sqlite3

import pytest

from quanto import recovery, recovery_materialize as materialize
from quanto.ledger import Journal


@pytest.fixture
def candidate(tmp_path):
    root = tmp_path / "source"
    (root / "runtime").mkdir(parents=True, mode=0o700)
    (root / "data/objects").mkdir(parents=True, mode=0o700)
    with Journal(root / "runtime/research.sqlite") as journal:
        journal.append_event("invented_materialization_fixture", {"evidence_kind": "synthetic_fixture"})
    payload = b"synthetic payload only"
    digest = hashlib.sha256(payload).hexdigest()
    obj = root / "data/objects" / (digest + ".bin")
    obj.write_bytes(payload)
    obj.chmod(0o600)
    source = tmp_path / "captured"
    report = recovery.capture_research_snapshot(root, source)
    target_parent = tmp_path / "private"
    target_parent.mkdir(mode=0o700)
    return source, target_parent / "materialized", report, digest


def run(candidate, **kwargs):
    source, destination, report, _ = candidate
    return materialize.materialize_research_snapshot(source, destination,
        expected_manifest_sha256=report["manifest_sha256"], expected_event_head=report["event_head"], **kwargs)


def tree(path):
    return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob("*") if p.is_file()}


def test_exact_copy_preserves_source_and_strictly_verifies(candidate, monkeypatch):
    source, destination, original, _ = candidate
    before = tree(source)
    verify = recovery.inspect_research_snapshot
    calls = []

    def checked(*args, **kwargs):
        calls.append((args[0], kwargs["limits"].seconds))
        return verify(*args, **kwargs)

    monkeypatch.setattr(recovery, "inspect_research_snapshot", checked)
    report = run(candidate)
    assert tree(source) == before == tree(destination)
    assert calls == [(destination, 15.0)]
    assert report["manifest_sha256"] == original["manifest_sha256"]
    assert report["snapshot_bytes_verified"] and report["database_integrity_verified"]
    assert report["source_mtime_change_count"] == 0
    assert not any(report[key] for key in ("source_path_stability_verified", "offline_availability_verified",
        "typed_closure_complete", "full_recovery_accepted", "execution_enabled", "production_recaptured"))
    with sqlite3.connect(destination / "research.sqlite") as db:
        assert db.execute("SELECT count(*) FROM events").fetchone()[0] == 1


def test_source_mtime_change_with_pinned_bytes_is_reported(candidate, monkeypatch):
    source, destination, _, digest = candidate
    obj = source / "objects" / (digest + ".bin")
    inode = obj.stat().st_ino
    real = os.fstat
    seen = 0

    def touch(fd):
        nonlocal seen
        info = real(fd)
        if info.st_ino == inode:
            seen += 1
            if seen == 2:
                os.utime(obj, ns=(info.st_atime_ns, info.st_mtime_ns + 1_000_000))
                info = real(fd)
        return info

    monkeypatch.setattr(os, "fstat", touch)
    report = run(candidate)
    assert report["source_mtime_change_count"] == 1
    assert tree(destination) == tree(source)
    assert not report["source_path_stability_verified"]


@pytest.mark.parametrize("kind", ["wrong_manifest", "wrong_head", "changed_bytes", "missing_object",
                                  "extra_object", "symlink", "hardlink", "existing_destination"])
def test_reject_invalid_candidate_and_preserve_attempt(candidate, kind, tmp_path):
    source, destination, report, digest = candidate
    obj = source / "objects" / (digest + ".bin")
    if kind == "wrong_manifest":
        report["manifest_sha256"] = "f" * 64
    elif kind == "wrong_head":
        report["event_head"] = "f" * 64
    elif kind == "changed_bytes":
        obj.write_bytes(b"X" * obj.stat().st_size)
    elif kind == "missing_object":
        obj.unlink()
    elif kind == "extra_object":
        (source / "objects/extra").write_bytes(b"invented")
    elif kind == "symlink":
        outside = tmp_path / "payload"
        outside.write_bytes(obj.read_bytes())
        obj.unlink()
        obj.symlink_to(outside)
    elif kind == "hardlink":
        os.link(obj, tmp_path / "alias")
    else:
        destination.mkdir(mode=0o700)
    before = tree(source)
    with pytest.raises(materialize.MaterializationError):
        run(candidate)
    assert tree(source) == before
    if (destination / "failure.json").exists():
        with pytest.raises(recovery.RecoveryError):
            recovery.inspect_research_snapshot(destination)
    with pytest.raises(materialize.MaterializationError):
        run(candidate)


def test_new_inode_with_identical_bytes_is_not_treated_as_mtime_only(candidate, monkeypatch):
    source, _, _, digest = candidate
    obj = source / "objects" / (digest + ".bin")
    real = Path.lstat
    changed = False

    def swap(path, *args, **kwargs):
        nonlocal changed
        if path == obj and not changed:
            changed = True
            replacement = obj.with_suffix(".replacement")
            replacement.write_bytes(obj.read_bytes())
            replacement.chmod(0o600)
            replacement.replace(obj)
        return real(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", swap)
    with pytest.raises(materialize.MaterializationError, match="source_identity_changed"):
        run(candidate)


def test_failed_destination_verifier_is_never_promoted(candidate, monkeypatch):
    def refuse(*_, **__):
        raise recovery.RecoveryError("file_changed")
    monkeypatch.setattr(recovery, "inspect_research_snapshot", refuse)
    with pytest.raises(materialize.MaterializationError, match="materialization_failed"):
        run(candidate)
    assert (candidate[1] / "failure.json").exists()


@pytest.mark.parametrize("interruption", [KeyboardInterrupt, SystemExit])
def test_catchable_interruption_preserves_failed_candidate(candidate, monkeypatch, interruption):
    original = materialize._resident

    def interrupt_after_payloads(path):
        if path.name == "manifest.json":
            raise interruption()
        return original(path)

    monkeypatch.setattr(materialize, "_resident", interrupt_after_payloads)
    with pytest.raises(materialize.MaterializationError, match="materialization_failed"):
        run(candidate)
    assert (candidate[1] / "failure.json").exists()
    with pytest.raises(recovery.RecoveryError, match="snapshot_inventory_mismatch"):
        recovery.inspect_research_snapshot(candidate[1])
    with pytest.raises(materialize.MaterializationError, match="destination_exists"):
        run(candidate)


def test_dataless_destination_refuses(candidate, monkeypatch):
    def refuse(_):
        raise materialize.MaterializationError("destination_dataless")
    monkeypatch.setattr(materialize, "_resident", refuse)
    with pytest.raises(materialize.MaterializationError, match="destination_dataless"):
        run(candidate)


@pytest.mark.parametrize("limits", [materialize.MaterializationLimits(copy_seconds=0),
    materialize.MaterializationLimits(copy_seconds=301),
    materialize.MaterializationLimits(snapshot=replace(recovery.Limits(), seconds=16))])
def test_limits_cannot_be_raised(candidate, limits):
    with pytest.raises(materialize.MaterializationError):
        run(candidate, limits=limits)
    assert not candidate[1].exists()


def test_copy_deadline_refuses_without_retry(candidate):
    with pytest.raises(materialize.MaterializationError, match="materialization_deadline"):
        run(candidate, limits=materialize.MaterializationLimits(copy_seconds=0.000000001))

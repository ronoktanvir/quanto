"""Materialize an exact pinned candidate; never recapture live application state.

Source bytes may be fetched by the filesystem on read. Matching a trusted digest
does not attest source-path stability. The new destination must pass the original
strict snapshot inspector unchanged before any candidate-verification claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import time

from quanto import recovery


class MaterializationError(ValueError):
    """Fixed reason codes, with no paths or payloads in displayed exceptions."""


@dataclass(frozen=True)
class MaterializationLimits:
    snapshot: recovery.Limits = recovery.Limits()
    copy_seconds: float = 300.0


def _need(condition, code):
    if not condition:
        raise MaterializationError(code)


def _tick(deadline):
    _need(time.monotonic() < deadline, "materialization_deadline")


def _expected_read(path, maximum, expected, expected_bytes, deadline):
    """Accept only pinned bytes; observe, but do not waive, identity changes."""
    _tick(deadline)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as source:
        before = os.fstat(source.fileno())
        recovery._file_info(before, maximum, private=True)
        raw = source.read(maximum + 1)
        after, current = os.fstat(source.fileno()), path.lstat()
        for info in (after, current):
            recovery._file_info(info, maximum, private=True)
        _need((before.st_dev, before.st_ino, before.st_size)
              == (after.st_dev, after.st_ino, after.st_size)
              == (current.st_dev, current.st_ino, current.st_size), "source_identity_changed")
        _need(len(raw) <= maximum and (expected_bytes is None or len(raw) == expected_bytes)
              and recovery._sha(raw) == expected, "source_bytes_mismatch")
        changed = before.st_mtime_ns != after.st_mtime_ns or after.st_mtime_ns != current.st_mtime_ns
    _tick(deadline)
    return raw, changed


def _resident(path):
    # Darwin's SF_DATALESS is a read-only synthetic flag. On other platforms,
    # absence of st_flags is not a promise that a filesystem is local/offline.
    _need(not getattr(path.lstat(), "st_flags", 0) & 0x40000000, "destination_dataless")


def materialize_research_snapshot(source: Path, destination: Path, *,
                                 expected_manifest_sha256: str,
                                 expected_event_head: str,
                                 limits: MaterializationLimits = MaterializationLimits()) -> dict:
    """Write a new candidate with exact pinned bytes and verify it strictly.

    No source-path stability, offline availability, external recovery, nested
    closure or trusted newest-state claim follows. A failed destination remains
    preserved and cannot be reused automatically. The outer controller must
    retain its intent: a hard process kill cannot guarantee cleanup or a receipt.
    """
    created = False
    try:
        _need(type(limits) is MaterializationLimits, "invalid_limits")
        recovery._bounds(limits.snapshot)
        _need(type(limits.copy_seconds) in (int, float) and 0 < limits.copy_seconds <= 300,
              "invalid_limits")
        _need(type(expected_manifest_sha256) is str
              and recovery.DIGEST.fullmatch(expected_manifest_sha256)
              and type(expected_event_head) is str and recovery.DIGEST.fullmatch(expected_event_head),
              "invalid_checkpoint")
        source, destination = recovery._path(source), recovery._path(destination)
        _need(not source.is_relative_to(destination) and not destination.is_relative_to(source),
              "source_destination_overlap")
        recovery._directory(source, private=True)
        recovery._directory(source / "objects", private=True)
        recovery._directory(destination.parent, private=True)
        _need(not os.path.lexists(destination), "destination_exists")
        _need(set(os.listdir(source)) == {"manifest.json", "research.sqlite", "objects"},
              "source_inventory_mismatch")
        deadline = time.monotonic() + limits.copy_seconds
        raw, changed = _expected_read(source / "manifest.json", limits.snapshot.manifest_bytes,
                                      expected_manifest_sha256, None, deadline)
        manifest = recovery._parse(raw)
        recovery._manifest(manifest, limits.snapshot)
        objects = manifest["objects"]
        _need(all(metadata["sha256"] == digest for digest, metadata in objects.items()),
              "manifest_object_identity")
        _need(manifest["database_state"]["events"]["head"] == expected_event_head,
              "event_checkpoint_mismatch")
        _need(set(os.listdir(source / "objects")) == {digest + ".bin" for digest in objects},
              "source_inventory_mismatch")
        total = manifest["database"]["bytes"] + sum(item["bytes"] for item in objects.values())
        _need(total <= limits.snapshot.total_bytes, "total_bytes_limit")
        destination.mkdir(mode=0o700)
        created = True
        (destination / "objects").mkdir(mode=0o700)
        recovery._write(destination / "manifest.json", raw)
        changes = int(changed)
        entries = [("research.sqlite", manifest["database"], limits.snapshot.database_bytes)]
        entries.extend(("objects/" + digest + ".bin", metadata, limits.snapshot.object_bytes)
                       for digest, metadata in sorted(objects.items()))
        for name, metadata, maximum in entries:
            value, changed = _expected_read(source / name, maximum, metadata["sha256"],
                                           metadata["bytes"], deadline)
            changes += int(changed)
            recovery._write(destination / name, value)
            _resident(destination / name)
            _tick(deadline)
        _resident(destination / "manifest.json")
        recovery._sync(destination / "objects")
        recovery._sync(destination)
        recovery._sync(destination.parent)
        _tick(deadline)
        # The strict verifier and its maximum 15-second budget are unchanged.
        report = recovery.inspect_research_snapshot(destination,
            expected_manifest_sha256=expected_manifest_sha256,
            expected_event_head=expected_event_head, limits=limits.snapshot)
        for name, _, _ in entries:
            _resident(destination / name)
        _resident(destination / "manifest.json")
        return {"format": "research_candidate_materialization_v1", **report,
                "source_mtime_change_count": changes, "source_path_stability_verified": False,
                "filesystem_retrieval_possible": True, "offline_availability_verified": False,
                "production_recaptured": False, "automatic_retry": False}
    except BaseException as exc:
        reason = str(exc) if isinstance(exc, MaterializationError) else "materialization_failed"
        if created:
            try:
                recovery._write(destination / "failure.json", recovery._json({"status": "failed", "reason": reason}))
                recovery._sync(destination)
            except (OSError, ValueError):
                pass
        raise MaterializationError(reason) from None

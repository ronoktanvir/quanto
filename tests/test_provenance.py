"""Synthetic receipt/storage checks; no provider, credential or project runtime access."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import sqlite3
import stat
import threading

import pytest

from quanto.ledger import Journal, canonical_json
from quanto.provenance import MAX_ARTIFACT_BYTES, MAX_REQUEST_BYTES, Provenance, ProvenanceError


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def test_submissions_precede_semantic_validation_and_store_only_identity(tmp_path):
    raw = '{"secret-looking-field":"synthetic-sensitive-value", malformed'
    with Provenance(tmp_path) as store:
        identity = store.begin("alpaca_bars", raw)
        pending = store.get_submission(identity)
        assert pending["status"] == "pending" and pending["details"] is None
        assert pending["request_sha256"] == digest(raw.encode())
        assert pending["request_bytes"] == len(raw.encode())
        assert pending["request_encoding"] == "utf8_text"
        store.finish(identity, "invalid", {"reason": "invalid_json"})
        assert store.get_submission(identity)["status"] == "invalid"
        assert store.journal.verify_events()["count"] == 2
        events = "".join(
            row[0] for row in store.journal.connection.execute("SELECT payload FROM events")
        )
        assert "synthetic-sensitive-value" not in events
    assert b"synthetic-sensitive-value" not in (tmp_path / "runtime/research.sqlite").read_bytes()


def test_dictionary_requests_have_canonical_identity_but_distinct_submissions(tmp_path):
    with Provenance(tmp_path) as store:
        a = store.begin("dataset_registration", {"z": 2, "a": 1})
        b = store.begin("dataset_registration", {"a": 1, "z": 2})
        assert a != b
        assert (
            store.get_submission(a)["request_sha256"] == store.get_submission(b)["request_sha256"]
        )
        assert store.get_submission(a)["request_encoding"] == "canonical_json"
        assert len(store.list_submissions("dataset_registration")) == 2
        assert store.list_submissions("other") == []
        assert len(store.list_submissions(limit=1)) == 1


def test_submission_filters_apply_before_limit_and_include_pending(tmp_path):
    with Provenance(tmp_path) as store:
        failed = store.begin("alpaca_bars", "first")
        store.finish(failed, "failed", {"reason": "synthetic_failure"})
        pending = store.begin("alpaca_bars", "second")
        other = store.begin("exploratory_study", "third")
        store.finish(other, "invalid", {"reason": "synthetic_invalid"})
        assert [row["submission_id"] for row in store.list_submissions(status="pending")] == [
            pending
        ]
        assert [
            row["submission_id"]
            for row in store.list_submissions(kind="alpaca_bars", status="failed", limit=1)
        ] == [failed]
        assert store.list_submissions(kind="alpaca_bars", status="invalid") == []
        assert [row["submission_id"] for row in store.list_submissions(limit=1)] == [other]
        for status in ("rejected", "", [], 1):
            with pytest.raises(ProvenanceError):
                store.list_submissions(status=status)


@pytest.mark.parametrize(
    "envelope",
    [
        "x" * (MAX_REQUEST_BYTES + 1),
        {"n": float("nan")},
        {"x": object()},
        ["not-a-request-object"],
        "\ud800",
    ],
)
def test_envelope_preflight_is_explicit_and_does_not_claim_a_submission(tmp_path, envelope):
    with Provenance(tmp_path) as store:
        with pytest.raises(ProvenanceError):
            store.begin("test", envelope)
        assert store.list_submissions() == []
        assert store.journal.verify_events()["count"] == 0


def test_pending_survives_reopening_and_terminal_outcome_is_single(tmp_path):
    with Provenance(tmp_path) as store:
        identity = store.begin("test", "bounded request")
    with Provenance(tmp_path) as store:
        assert store.get_submission(identity)["status"] == "pending"
        store.finish(identity, "interrupted", {"reason": "explicit_operator_reconciliation"})
        with pytest.raises(ProvenanceError, match="terminal"):
            store.finish(identity, "failed", {})
        assert store.get_submission(identity)["status"] == "interrupted"
        for sql in (
            "UPDATE provenance_submissions SET kind='other'",
            "DELETE FROM provenance_outcomes",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                store.journal.connection.execute(sql)


def test_artifact_refs_must_resolve_before_success_commits(tmp_path):
    with Provenance(tmp_path) as store:
        identity = store.begin("test", {})
        for details in ({}, {"artifact_refs": ["a" * 64]}, {"artifact_refs": "a" * 64}):
            with pytest.raises(ProvenanceError):
                store.finish(identity, "success", details)
            assert store.get_submission(identity)["status"] == "pending"
        receipt = store.put_json({"evidence_kind": "synthetic_fixture", "source": "fixture"})
        store.finish(identity, "success", {"receipt_sha256": receipt, "artifact_refs": [receipt]})
        result = store.get_submission(identity)
        assert result["status"] == "success" and result["details"]["receipt_sha256"] == receipt
        assert store.journal.verify_events()["count"] == 2


def test_event_failure_rolls_back_outcome(tmp_path, monkeypatch):
    with Provenance(tmp_path) as store:
        identity = store.begin("test", {})
        monkeypatch.setattr(
            store.journal, "_event", lambda *args: (_ for _ in ()).throw(RuntimeError("injected"))
        )
        with pytest.raises(RuntimeError):
            store.finish(identity, "failed", {"reason": "synthetic"})
        assert store.get_submission(identity)["status"] == "pending"


def test_artifact_identity_deduplicates_without_replacing_bytes(tmp_path):
    raw = b"synthetic raw response\x00\xff"
    with Provenance(tmp_path) as store:
        identity = store.put_bytes(raw)
        path = tmp_path / "data/objects" / (identity + ".bin")
        info = path.stat()
        assert store.read_bytes(identity) == raw
        assert store.put_bytes(raw) == identity
        assert path.stat().st_ino == info.st_ino
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert stat.S_IMODE((tmp_path / "data").stat().st_mode) == 0o700
        assert stat.S_IMODE((tmp_path / "runtime/research.sqlite").stat().st_mode) == 0o600
        assert list(path.parent.iterdir()) == [path]
        path.write_bytes(b"corrupted")
        with pytest.raises(ProvenanceError, match="identity"):
            store.read_bytes(identity)
        with pytest.raises(ProvenanceError, match="identity"):
            store.put_bytes(raw)
        assert path.read_bytes() == b"corrupted"


def test_write_failure_does_not_publish_or_leave_ordinary_temporary(tmp_path, monkeypatch):
    with Provenance(tmp_path) as store:
        monkeypatch.setattr(os, "link", lambda *a, **k: (_ for _ in ()).throw(OSError("injected")))
        with pytest.raises(ProvenanceError, match="stored safely"):
            store.put_bytes(b"unpublished")
        assert list((tmp_path / "data/objects").iterdir()) == []


def test_atomic_publication_exposes_only_complete_content(tmp_path, monkeypatch):
    started, release = threading.Event(), threading.Event()
    original = os.link
    raw = b"synthetic complete object"

    def delayed_link(*args, **kwargs):
        started.set()
        assert release.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(os, "link", delayed_link)

    def publish():
        with Provenance(tmp_path) as store:
            return store.put_bytes(raw)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(publish)
        assert started.wait(5)
        assert not (tmp_path / "data/objects" / (digest(raw) + ".bin")).exists()
        release.set()
        assert future.result(timeout=5) == digest(raw)
    with Provenance(tmp_path) as store:
        assert store.read_bytes(digest(raw)) == raw


def test_concurrent_publishers_share_one_verified_object(tmp_path):
    # Initialize the schema first so this specifically tests publication races.
    with Provenance(tmp_path):
        pass

    def publish(_):
        with Provenance(tmp_path) as store:
            return store.put_bytes(b"concurrent synthetic object")

    with ThreadPoolExecutor(max_workers=4) as pool:
        identities = list(pool.map(publish, range(8)))
    assert len(set(identities)) == 1
    assert len(list((tmp_path / "data/objects").iterdir())) == 1


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":1e999}',
        b"\xff",
        b"[] trailing",
        b'"' + b"x" * (1024 * 1024) + b'"',
    ],
)
def test_json_read_is_strict_even_for_hash_valid_bytes(tmp_path, raw):
    with Provenance(tmp_path) as store:
        identity = store.put_bytes(raw)
        with pytest.raises(ProvenanceError, match="strict"):
            store.read_json(identity)


def test_json_write_canonical_and_finite(tmp_path):
    with Provenance(tmp_path) as store:
        obj = {"z": "✓", "a": [True, None, 2]}
        identity = store.put_json(obj)
        assert store.read_json(identity) == obj
        assert store.read_bytes(identity) == canonical_json(obj).encode()
        with pytest.raises(ProvenanceError):
            store.put_json({"x": float("inf")})
        with pytest.raises(ProvenanceError):
            store.put_bytes(b"x" * (MAX_ARTIFACT_BYTES + 1))


@pytest.mark.parametrize("part", ["root", "runtime", "data", "objects", "database"])
def test_symlink_storage_is_refused(tmp_path, part):
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    if part == "root":
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        root = alias
    elif part == "database":
        (root / "runtime").mkdir()
        target = outside / "db"
        target.write_text("unrelated")
        (root / "runtime/research.sqlite").symlink_to(target)
    elif part == "objects":
        (root / "data").mkdir()
        (root / "data/objects").symlink_to(outside, target_is_directory=True)
    else:
        (root / part).symlink_to(outside, target_is_directory=True)
    with pytest.raises(ProvenanceError, match="unsafe"):
        Provenance(root)
    if part == "database":
        assert target.read_text() == "unrelated"


@pytest.mark.parametrize("kind", ["symlink", "directory", "fifo"])
def test_nonregular_blob_paths_are_not_followed_or_overwritten(tmp_path, kind):
    with Provenance(tmp_path) as store:
        raw = b"safe synthetic object"
        identity = digest(raw)
        path = tmp_path / "data/objects" / (identity + ".bin")
        if kind == "symlink":
            target = tmp_path / "outside"
            target.write_bytes(raw)
            path.symlink_to(target)
        elif kind == "directory":
            path.mkdir()
        else:
            os.mkfifo(path)
        with pytest.raises(ProvenanceError):
            store.read_bytes(identity)
        with pytest.raises(ProvenanceError):
            store.put_bytes(raw)
        if kind == "symlink":
            assert target.read_bytes() == raw and path.is_symlink()


def test_explicit_tombstone_and_purge_keep_audit_but_block_reuse(tmp_path):
    with Provenance(tmp_path) as store:
        raw = b"synthetic object requiring removal"
        identity = store.put_bytes(raw)
        path = tmp_path / "data/objects" / (identity + ".bin")
        submission = store.begin("test", {})
        store.finish(submission, "success", {"artifact_refs": [identity]})
        store.tombstone(identity, "accidental_secret")
        assert path.exists()  # Tombstone blocks reads before an explicit physical purge.
        with pytest.raises(ProvenanceError, match="tombstoned"):
            store.read_bytes(identity)
        with pytest.raises(ProvenanceError, match="tombstoned"):
            store.put_bytes(raw)
        store.purge(identity, "accidental_secret")
        assert not path.exists()
        store.purge(identity, "accidental_secret")  # Missing object is explicitly observed.
        events = [
            json.loads(row[0])
            for row in store.journal.connection.execute(
                "SELECT payload FROM events WHERE kind='artifact_purge_observed' ORDER BY id"
            )
        ]
        assert events == [
            {"digest": identity, "removed": True},
            {"digest": identity, "removed": False},
        ]
        assert (
            store.get_submission(submission)["status"] == "success"
        )  # Historical outcome survives.
        store.journal.verify_events()
    with Provenance(tmp_path) as reopened:
        with pytest.raises(ProvenanceError, match="tombstoned"):
            reopened.read_bytes(identity)


def test_purge_refuses_unexpected_paths_and_preserves_tombstone(tmp_path):
    with Provenance(tmp_path) as store:
        raw = b"synthetic"
        identity = digest(raw)
        outside = tmp_path / "outside"
        outside.write_bytes(raw)
        path = tmp_path / "data/objects" / (identity + ".bin")
        path.symlink_to(outside)
        with pytest.raises(ProvenanceError, match="unexpected"):
            store.purge(identity, "rights_request")
        assert outside.read_bytes() == raw and path.is_symlink()
        with pytest.raises(ProvenanceError, match="tombstoned"):
            store.read_bytes(identity)


def test_invalid_identifiers_cannot_escape_store(tmp_path):
    with Provenance(tmp_path) as store:
        for value in ("../secret", "A" * 64, "g" * 64, [], None):
            with pytest.raises(ProvenanceError):
                store.read_bytes(value)
        with pytest.raises(ProvenanceError):
            store.begin("../kind", {})
        for limit in (0, True, 1001):
            with pytest.raises(ProvenanceError):
                store.list_submissions(limit=limit)
    with pytest.raises(ProvenanceError, match="closed"):
        store.begin("test", {})


def test_new_tables_share_existing_journal_without_changing_budget_records(tmp_path):
    (tmp_path / "runtime").mkdir()
    with Journal(tmp_path / "runtime/research.sqlite") as journal:
        journal.reserve("synthetic-reservation", 100)
        before = journal.budget_snapshot()
    with Provenance(tmp_path) as store:
        sub = store.begin("test", {})
        store.finish(sub, "failed", {"reason": "fixture"})
        assert store.journal.budget_snapshot() == before
        assert store.journal.verify_events()["count"] == 3


def test_finish_joins_caller_transaction_and_rolls_back_with_it(tmp_path):
    with Provenance(tmp_path) as store:
        submission = store.begin("test", {})
        artifact = store.put_bytes(b"synthetic atomic publication fixture")
        with pytest.raises(RuntimeError, match="fixture rollback"):
            with store.journal._transaction():
                store.finish(submission, "success", {"artifact_refs": [artifact]})
                assert store.get_submission(submission)["status"] == "success"
                raise RuntimeError("fixture rollback")
        assert store.get_submission(submission)["status"] == "pending"
        with store.journal._transaction():
            store.finish(submission, "success", {"artifact_refs": [artifact]})
        assert store.get_submission(submission)["status"] == "success"
        assert store.journal.verify_events()["count"] == 2


def test_joined_finish_rolls_back_locally_when_caller_catches_failure(tmp_path, monkeypatch):
    with Provenance(tmp_path) as store:
        submission = store.begin("test", {})
        original = store.journal._event

        def failed_event(kind, payload, now):
            if kind == "submission_finished":
                raise RuntimeError("fixture event failure")
            return original(kind, payload, now)

        monkeypatch.setattr(store.journal, "_event", failed_event)
        with store.journal._transaction():
            with pytest.raises(RuntimeError, match="fixture event failure"):
                store.finish(submission, "failed", {"reason": "fixture"})
        assert store.get_submission(submission)["status"] == "pending"
        assert store.journal.verify_events()["count"] == 1

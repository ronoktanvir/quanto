"""Invented access scopes and fake I/O; no actual store, credentials or network."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import threading

import pytest

from quanto import alpaca_data as data
from quanto import alpaca_actions as actions
from quanto.evaluation_registry import AccessError, Coverage, Supervisor, current_session, request_identity
from quanto.provenance import Provenance, ProvenanceError

H = "a" * 64
KEYS = data.Credentials("fixture-key-value", "fixture-secret-value")
REQUEST = {"symbol": "AAPL", "start": "2024-06-03", "end": "2024-06-05"}
NOW = datetime(2025, 1, 20, tzinfo=timezone.utc)


def setup(root):
    supervisor = Supervisor(root, synthetic=True)
    supervisor.relate("security", "alpaca:us_equity:AAPL", "security:one", H)
    reviewer = supervisor.issue_principal()
    return supervisor, reviewer


def manifest(supervisor, reviewer, start="2024-06-01", end="2024-06-30", security="security:one"):
    return {"coverage": Coverage("bars", (security,), start, end).document(),
            "warmup": {"start": start, "end": start}, "final": {"start": end, "end": end},
            "candidate_sha256": H, "code_sha256": H, "dependencies_sha256": H,
            "scenarios_sha256": H, "rights_sha256": H, "release_sha256": H,
            "selectors": [supervisor.principal], "reviewers": [reviewer]}


def records(supervisor, table):
    with sqlite3.connect(supervisor.path) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute("SELECT * FROM " + table)]


def content_opens(supervisor):
    """Distinguish physical read effects from newly accounted input imports."""
    intents = {row["intent"] for row in records(supervisor, "intents") if row["operation"] == "content_read"}
    return [row for row in records(supervisor, "effects") if row["intent"] in intents]


def response():
    return data.HTTPResult(200, json.dumps({"symbol": "AAPL", "next_page_token": None,
        "bars": [{"t": "2024-06-03T04:00:00Z", "o": 100, "h": 102, "l": 99, "c": 101, "v": 20}]}).encode())


def test_missing_authority_denies_before_store_or_transport(tmp_path):
    with pytest.raises(ProvenanceError):
        Provenance(tmp_path)
    assert not list(tmp_path.iterdir())
    calls = []
    with pytest.raises(data.AcquisitionError, match="access_refused"):
        data._dispatch("GET", data._url(data._request(REQUEST, "bars", NOW), "bars"),
                       KEYS, 2, 1000, lambda *_: calls.append(True))
    assert calls == []
    with pytest.raises(data.AcquisitionError, match="access_refused"):
        data._http("GET", "https://data.alpaca.markets/", {}, 1, 100)


def test_session_pins_root_and_persistent_principal(tmp_path):
    supervisor, _ = setup(tmp_path)
    principal = supervisor.principal
    with supervisor.session() as session:
        assert current_session(tmp_path) is session
        other = tmp_path / "other"
        other.mkdir()
        with pytest.raises(ProvenanceError):
            Provenance(other)
        with pytest.raises(AccessError, match="authority_already_active"):
            Supervisor(other, synthetic=True)
        with Provenance(tmp_path) as store:
            digest = store.put_bytes(b"invented")
            assert store.read_bytes(digest) == b"invented"
    with pytest.raises(AccessError, match="authority_missing"):
        current_session(tmp_path)
    assert Supervisor(tmp_path, synthetic=True).principal == principal


def test_reservation_blocks_access_before_i_o(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    held = supervisor.reserve(manifest(supervisor, reviewer))
    assert held["protected_eligible"] is False
    calls = []
    with supervisor.session():
        result = data.acquire_bars(tmp_path, REQUEST, transport=lambda *_: calls.append(True),
                                   credentials=KEYS, clock=lambda: NOW)
        assert result["error"] == "access_refused"
    assert calls == [] and not records(supervisor, "effects")
    assert records(supervisor, "intents")[0]["state"] == "refused"


def test_issued_access_blocks_reservation_before_first_effect(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    with supervisor.session() as session:
        session.acquisition("bars", data._request(REQUEST, "bars", NOW))
        with pytest.raises(AccessError, match="reservation_conflict"):
            supervisor.reserve(manifest(supervisor, reviewer))
    assert len(records(supervisor, "effects")) == 0
    assert any(row["kind"] == "reservation_refused" for row in records(supervisor, "audit"))


def test_race_has_only_one_compatible_winner(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    barrier = threading.Barrier(2)
    with supervisor.session() as session:
        def reserve():
            barrier.wait()
            try:
                supervisor.reserve(manifest(supervisor, reviewer))
                return "reserved"
            except AccessError:
                return "refused"
        def acquire():
            barrier.wait()
            try:
                session.acquisition("bars", data._request(REQUEST, "bars", NOW))
                return "issued"
            except AccessError:
                return "refused"
        with ThreadPoolExecutor(2) as pool:
            first, second = pool.submit(reserve), pool.submit(acquire)
            result = [first.result(), second.result()]
    assert result.count("refused") == 1


def test_effect_consumption_precedes_fake_transport_and_reuse_refuses(tmp_path):
    supervisor, _ = setup(tmp_path)
    with supervisor.session() as session:
        request = data._request(REQUEST, "bars", NOW)
        intent = session.acquisition("bars", request)
        url = data._url(request, "bars")
        permit = intent.page("GET", url)
        def transport(*_):
            assert len(records(supervisor, "effects")) == 1
            assert records(supervisor, "effect_ends") == []
            return response()
        assert data._dispatch("GET", url, KEYS, 2, 1000, transport, permit=permit).status == 200
        with pytest.raises(data.AcquisitionError, match="access_refused"):
            data._dispatch("GET", url, KEYS, 2, 1000, lambda *_: pytest.fail("replayed"), permit=permit)
    assert records(supervisor, "effect_ends")[0]["state"] == "completed"


def test_page_request_cannot_change_symbol_dates_or_replay(tmp_path):
    supervisor, _ = setup(tmp_path)
    with supervisor.session() as session:
        request = data._request(REQUEST, "bars", NOW)
        intent = session.acquisition("bars", request)
        for altered in ({**request, "symbol": "MSFT"}, {**request, "end": "2024-07-01"}):
            with pytest.raises(AccessError, match="effect_mismatch"):
                intent.page("GET", data._url(altered, "bars"))
        url = data._url(request, "bars", "page-2")
        # A fabricated effect object has no persisted exact-page permission.
        with pytest.raises(data.AcquisitionError, match="access_refused"):
            data._dispatch("GET", url, KEYS, 1, 1000, lambda *_: pytest.fail("called"),
                           permit=intent.effect(request_identity("GET", url)))
        permit = intent.page("GET", url)
        data._dispatch("GET", url, KEYS, 1, 1000, lambda *_: response(), permit=permit)
    assert len(records(supervisor, "effects")) == 1


def test_synthetic_authority_cannot_enable_real_http(tmp_path, monkeypatch):
    supervisor, _ = setup(tmp_path)
    monkeypatch.setattr(data.http.client, "HTTPSConnection", lambda *_a, **_k: pytest.fail("network"))
    with supervisor.session() as session:
        request = data._request(REQUEST, "bars", NOW)
        intent = session.acquisition("bars", request)
        url = data._url(request, "bars")
        with pytest.raises(data.AcquisitionError, match="access_refused"):
            data._dispatch("GET", url, KEYS, 1, 1000, permit=intent.page("GET", url))
    assert records(supervisor, "effect_ends")[0]["state"] == "uncertain"


def test_uncertain_effect_and_research_rollback_preserve_conflict(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    with supervisor.session() as session:
        with Provenance(tmp_path) as store:
            store.journal.connection.execute("BEGIN IMMEDIATE")
            request = data._request(REQUEST, "bars", NOW)
            intent = session.acquisition("bars", request)
            url = data._url(request, "bars")
            with pytest.raises(data.AcquisitionError, match="request_timeout"):
                data._dispatch("GET", url, KEYS, 1, 1000,
                               lambda *_: (_ for _ in ()).throw(TimeoutError()), permit=intent.page("GET", url))
            store.journal.connection.rollback()
    supervisor = Supervisor(tmp_path, synthetic=True)
    with pytest.raises(AccessError, match="reservation_conflict"):
        supervisor.reserve(manifest(supervisor, reviewer))
    assert records(supervisor, "effect_ends")[0]["state"] == "uncertain"


def test_only_no_start_rejection_removes_conflict(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    with supervisor.session() as session:
        intent = session.acquisition("bars", data._request(REQUEST, "bars", NOW))
        intent.reject_before_access()
        assert supervisor.reserve(manifest(supervisor, reviewer))["state"] == "preparation_reserved"
        with pytest.raises(AccessError, match="intent_closed"):
            intent.reject_before_access()


def test_cached_read_does_not_reopen_or_reconsume(tmp_path):
    supervisor, _ = setup(tmp_path)
    with supervisor.session():
        with Provenance(tmp_path) as store:
            digest = store.put_bytes(b"invented")
            assert store.read_bytes(digest) == store.read_bytes(digest)
    assert len(content_opens(supervisor)) == 1
    assert len(records(supervisor, "effects")) == 2  # One import plus one physical open.


def test_content_identity_and_unknown_scope_cannot_be_substituted(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    first, second = hashlib.sha256(b"a").hexdigest(), hashlib.sha256(b"b").hexdigest()
    supervisor.classify(first, Coverage("content", ("security:one",), "2024-01-01", "2024-01-01"), H)
    supervisor.reserve(manifest(supervisor, reviewer))
    with supervisor.session() as session:
        intent = session.content(first)
        with pytest.raises(AccessError, match="effect_mismatch"):
            with intent.effect(second).start("content_read", second):
                pytest.fail("read")
        with pytest.raises(AccessError, match="reservation_conflict"):
            session.content(second)


def test_known_old_access_allows_known_later_window(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    with supervisor.session() as session:
        session.acquisition("bars", data._request({**REQUEST, "start": "2024-01-02", "end": "2024-01-03"}, "bars", NOW))
        assert supervisor.reserve(manifest(supervisor, reviewer))["state"] == "preparation_reserved"


def test_actions_process_dates_are_not_economic_dates(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    with supervisor.session() as session:
        session.acquisition("actions", actions._request(json.dumps({**REQUEST, "start": "2020-01-01", "end": "2020-01-02"}), NOW))
        with pytest.raises(AccessError, match="reservation_conflict"):
            supervisor.reserve(manifest(supervisor, reviewer))
    scope = json.loads(records(supervisor, "intents")[0]["coverage"])
    assert scope["start"] is None and scope["end"] is None


def test_global_calendar_conflicts_across_security(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    with supervisor.session() as session:
        session.acquisition("calendar", {"start": "2024-06-02", "end": "2024-06-04"})
        with pytest.raises(AccessError, match="reservation_conflict"):
            supervisor.reserve(manifest(supervisor, reviewer))


def test_stale_identity_fences_effects_and_alias_merge_invalidates(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    supervisor.relate("security", "alpaca:us_equity:OTHER", "security:two", H)
    supervisor.reserve(manifest(supervisor, reviewer))
    with supervisor.session() as session:
        request = data._request({**REQUEST, "symbol": "OTHER"}, "bars", NOW)
        intent = session.acquisition("bars", request)
        url = data._url(request, "bars")
        permit = intent.page("GET", url)
        supervisor.relate("security", "security:one", "security:two", H)
        with pytest.raises(data.AcquisitionError, match="access_refused"):
            data._dispatch("GET", url, KEYS, 1, 1000, lambda *_: pytest.fail("called"), permit=permit)
    assert records(supervisor, "invalidations")[0]["reason"] == "exposure_conflict"


def test_principal_link_invalidates_selector_reviewer_separation(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    supervisor.reserve(manifest(supervisor, reviewer))
    supervisor.relate("principal", supervisor.principal, reviewer, H)
    assert records(supervisor, "invalidations")[0]["reason"] == "principal_conflict"
    with pytest.raises(AccessError, match="selector_reviewer_overlap"):
        supervisor.reserve(manifest(supervisor, reviewer, "2025-01-01", "2025-02-01"))


def test_existing_history_never_becomes_clean_by_new_registry(tmp_path):
    (tmp_path / "data/objects").mkdir(parents=True)
    supervisor, reviewer = setup(tmp_path)
    with pytest.raises(AccessError, match="legacy_unreconciled"):
        supervisor.reserve(manifest(supervisor, reviewer))


def test_protected_activation_always_unavailable_and_private_logs_not_shared(tmp_path):
    supervisor, _ = setup(tmp_path)
    with pytest.raises(AccessError, match="protected_unavailable"):
        supervisor.protected_acquire()
    assert not supervisor.overview()["protected_eligible"]
    assert not (tmp_path / "runtime/research.sqlite").exists()
    assert b"protected_refused" in supervisor.path.read_bytes()


def test_controls_are_append_only_and_replaced_control_file_refuses(tmp_path):
    supervisor, _ = setup(tmp_path)
    with sqlite3.connect(supervisor.path) as db:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("DELETE FROM principals")
    raw = supervisor.path.read_bytes()
    moved = supervisor.path.with_name("replacement.sqlite")
    moved.write_bytes(raw)
    moved.chmod(0o600)
    moved.replace(supervisor.path)
    with pytest.raises(AccessError, match="wrong_store"):
        supervisor.overview()


def test_denied_read_never_opens_unclassified_bytes(tmp_path, monkeypatch):
    supervisor, reviewer = setup(tmp_path)
    with supervisor.session():
        with Provenance(tmp_path) as store:
            supervisor.reserve(manifest(supervisor, reviewer))
            # Simulate externally placed, unclassified content. The ordinary
            # put path itself is separately required to account/refuse imports.
            raw = b"unknown-content"
            digest = hashlib.sha256(raw).hexdigest()
            target = tmp_path / "data/objects" / (digest + ".bin")
            target.write_bytes(raw)
            target.chmod(0o600)
            monkeypatch.setattr(store, "_blob", lambda *_a, **_k: pytest.fail("opened"))
            with pytest.raises(ProvenanceError):
                store.read_bytes(digest)


def test_denied_query_does_not_publish_control_details(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    held = supervisor.reserve(manifest(supervisor, reviewer))
    query_digest = hashlib.sha256(json.dumps(data._request(REQUEST, "bars", NOW),
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with supervisor.session():
        result = data.acquire_bars(tmp_path, REQUEST, transport=lambda *_: pytest.fail("called"),
                                   credentials=KEYS, clock=lambda: NOW)
    assert result["status"] == "invalid" and "receipt_sha256" not in result
    ordinary = (tmp_path / "runtime/research.sqlite").read_bytes()
    ordinary += b"".join(p.read_bytes() for p in (tmp_path / "data/objects").iterdir())
    for value in ("AAPL", "2024-06-03", "2024-06-05", query_digest, held["reservation"], supervisor.principal, reviewer):
        assert value.encode() not in ordinary
    assert records(supervisor, "intents")[0]["request_sha256"] == query_digest


@pytest.mark.parametrize("change", ["bytes", "mtime", "mode", "link", "replace"])
def test_cached_bytes_do_not_hide_file_changes(tmp_path, change):
    import os
    supervisor, _ = setup(tmp_path)
    with supervisor.session():
        with Provenance(tmp_path) as store:
            digest = store.put_bytes(b"first")
            assert store.read_bytes(digest) == b"first"
            before = len(records(supervisor, "effects"))
            path = tmp_path / "data/objects" / (digest + ".bin")
            if change == "bytes":
                path.write_bytes(b"other")
            elif change == "mtime":
                info = path.stat()
                os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns + 1000000))
            elif change == "mode":
                path.chmod(0o644)
            elif change == "link":
                os.link(path, path.with_name("extra-link"))
            else:
                replacement = path.with_name("replacement")
                replacement.write_bytes(b"first")
                replacement.chmod(0o600)
                replacement.replace(path)
            if change in {"bytes", "mode", "link"}:
                with pytest.raises(ProvenanceError):
                    store.read_bytes(digest)
            else:
                assert store.read_bytes(digest) == b"first"
                assert len(records(supervisor, "effects")) == before + 1


def test_cache_rechecks_tombstone_and_session(tmp_path):
    supervisor, _ = setup(tmp_path)
    with supervisor.session():
        store = Provenance(tmp_path)
        digest = store.put_bytes(b"first")
        store.read_bytes(digest)
        store.tombstone(digest, "operator_requested")
        with pytest.raises(ProvenanceError):
            store.read_bytes(digest)
        second = store.put_bytes(b"second")
        store.read_bytes(second)
    with supervisor.session():
        with pytest.raises(ProvenanceError):
            store.read_bytes(second)
    store.close()


def test_cache_rechecks_alias_policy_and_canonical_store(tmp_path):
    from quanto import evaluation_registry as registry
    supervisor, _ = setup(tmp_path)
    with supervisor.session():
        with Provenance(tmp_path) as store:
            digest = store.put_bytes(b"first")
            store.read_bytes(digest)
            count = len(records(supervisor, "effects"))
            supervisor.relate("security", "alias:extra", "security:one", H)
            store.read_bytes(digest)
            assert len(records(supervisor, "effects")) == count + 1
            original = registry.ACCESS_POLICY_VERSION
            try:
                registry.ACCESS_POLICY_VERSION = "synthetic-changed-policy"
                store.read_bytes(digest)
                assert len(records(supervisor, "effects")) == count + 2
            finally:
                registry.ACCESS_POLICY_VERSION = original
            directory = tmp_path / "data/objects"
            directory.rename(tmp_path / "data/moved")
            directory.mkdir(mode=0o700)
            with pytest.raises(ProvenanceError):
                store.read_bytes(digest)


def test_cached_json_returns_new_mutable_values_and_instances_do_not_share(tmp_path):
    supervisor, _ = setup(tmp_path)
    with supervisor.session():
        with Provenance(tmp_path) as store:
            digest = store.put_json({"invented": [1]})
            first = store.read_json(digest)
            first["invented"].append(2)
            assert store.read_json(digest) == {"invented": [1]}
            assert len(content_opens(supervisor)) == 1
        with Provenance(tmp_path) as second:
            assert second.read_json(digest) == {"invented": [1]}
            assert len(content_opens(supervisor)) == 2


def test_cache_limits_preserve_new_open_evidence(tmp_path, monkeypatch):
    from quanto import provenance
    supervisor, _ = setup(tmp_path)
    monkeypatch.setattr(provenance, "MAX_READ_CACHE_BYTES", 5)
    with supervisor.session():
        with Provenance(tmp_path) as store:
            a, b = store.put_bytes(b"first"), store.put_bytes(b"other")
            store.read_bytes(a)
            store.read_bytes(b)
            assert store._read_cache_bytes <= 5
            store.read_bytes(a)
            assert len(content_opens(supervisor)) == 3


def test_revoked_principal_cannot_use_cached_bytes_or_new_session(tmp_path):
    supervisor, _ = setup(tmp_path)
    with supervisor.session() as session:
        with pytest.raises(AttributeError):
            session.principal = "a-new-role-label"
        with Provenance(tmp_path) as store:
            digest = store.put_bytes(b"private invented bytes")
            store.read_bytes(digest)
            supervisor.revoke_principal(session.principal, H)
            with pytest.raises(ProvenanceError):
                store.read_bytes(digest)
    with pytest.raises(AccessError, match="principal_revoked"):
        supervisor.session()


@pytest.mark.parametrize("change", ["revision", "tombstone"])
def test_cache_refuses_visibility_change_during_validation(tmp_path, monkeypatch, change):
    supervisor, _ = setup(tmp_path)
    with supervisor.session():
        with Provenance(tmp_path) as store:
            digest = store.put_bytes(b"invented")
            store.read_bytes(digest)
            original = store._read_identity
            changed = False
            def identity(value):
                nonlocal changed
                result = original(value)
                if not changed:
                    changed = True
                    if change == "revision":
                        supervisor.relate("security", "alias:changed", "security:one", H)
                    else:
                        store.tombstone(value, "operator_requested")
                return result
            monkeypatch.setattr(store, "_read_identity", identity)
            with pytest.raises(ProvenanceError):
                store.read_bytes(digest)


def test_unregistered_security_cannot_create_known_reservation(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    with pytest.raises(AccessError, match="unknown_coverage"):
        supervisor.reserve(manifest(supervisor, reviewer, security="security:unresolved"))
    assert not records(supervisor, "reservations")
    assert records(supervisor, "audit")[-1]["kind"] == "reservation_refused"


def test_existing_wrong_root_is_refused_without_schema_repair(tmp_path):
    import shutil
    source, destination = tmp_path / "source", tmp_path / "destination"
    source.mkdir(mode=0o700)
    destination.mkdir(mode=0o700)
    supervisor, _ = setup(source)
    target = destination / "runtime/access-control/control.sqlite"
    target.parent.mkdir(parents=True, mode=0o700)
    shutil.copy2(supervisor.path, target)
    with sqlite3.connect(target) as db:
        db.execute("DROP TRIGGER no_delete_intents")
    before = target.read_bytes()
    with pytest.raises(AccessError, match="wrong_store"):
        Supervisor(destination, synthetic=True)
    assert target.read_bytes() == before
    with sqlite3.connect(target) as db:
        assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='no_delete_intents'").fetchone()


def test_existing_partial_control_file_is_not_new_authority(tmp_path):
    target = tmp_path / "runtime/access-control/control.sqlite"
    target.parent.mkdir(parents=True, mode=0o700)
    target.write_bytes(b"")
    target.chmod(0o600)
    with pytest.raises(AccessError, match="control_unavailable"):
        Supervisor(tmp_path, synthetic=True)
    assert target.read_bytes() == b""


def test_revoked_attempts_keep_fixed_private_refusal_evidence(tmp_path):
    supervisor, _ = setup(tmp_path)
    with supervisor.session() as session:
        request = data._request(REQUEST, "bars", NOW)
        intent = session.acquisition("bars", request)
        url = data._url(request, "bars")
        permit = intent.page("GET", url)
        supervisor.revoke_principal(session.principal, H)
        with pytest.raises(AccessError, match="principal_revoked"):
            session.content(H)
        with pytest.raises(AccessError, match="principal_revoked"):
            session.cache_epoch()
        with pytest.raises(AccessError, match="principal_revoked"):
            with permit.start("provider_page", request_identity("GET", url)):
                pytest.fail("effect started")
    with pytest.raises(AccessError, match="principal_revoked"):
        supervisor.session()
    refused = {row["kind"] for row in records(supervisor, "audit")
               if json.loads(row["payload"]).get("reason") == "principal_revoked"}
    assert {"intent_refused", "reuse_refused", "effect_refused", "session_refused"} <= refused
    assert not records(supervisor, "effects")


def test_direct_session_constructor_does_not_mint_a_principal(tmp_path):
    from quanto.evaluation_registry import AccessSession
    supervisor, _ = setup(tmp_path)
    with pytest.raises(AccessError, match="unknown_principal"):
        AccessSession(supervisor, "new-role-label")
    assert records(supervisor, "audit")[-1]["kind"] == "session_refused"


def test_direct_issue_derives_scope_and_refuses_caller_narrowing(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    supervisor.reserve(manifest(supervisor, reviewer))
    request = data._request(REQUEST, "bars", NOW)
    digest = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with supervisor.session() as session:
        with pytest.raises(TypeError):
            session.issue("provider_page", digest, Coverage("bars", ("security:other",), "2020-01-01", "2020-01-02"),
                          request_document={"kind": "bars", "request": request})
        with pytest.raises(AccessError, match="reservation_conflict"):
            session.issue("provider_page", digest, request_document={"kind": "bars", "request": request})
        with pytest.raises(AccessError, match="reservation_conflict"):
            session.issue("content_read", H)
    assert all(row["state"] == "refused" for row in records(supervisor, "intents"))
    assert not records(supervisor, "effects")


def test_tombstone_during_new_open_refuses_returned_content(tmp_path, monkeypatch):
    from contextlib import contextmanager
    supervisor, _ = setup(tmp_path)
    with supervisor.session():
        with Provenance(tmp_path) as store:
            digest = store.put_bytes(b"invented")
            original = store._blob
            @contextmanager
            def blob(value, **kwargs):
                with original(value, **kwargs) as source:
                    store.tombstone(value, "operator_requested")
                    yield source
            monkeypatch.setattr(store, "_blob", blob)
            with pytest.raises(ProvenanceError, match="tombstoned"):
                store.read_bytes(digest)
            assert digest not in store._read_cache
    assert len(content_opens(supervisor)) == 1


def test_cached_read_refuses_replaced_canonical_root(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir(mode=0o700)
    supervisor, _ = setup(root)
    with supervisor.session():
        with Provenance(root) as store:
            digest = store.put_bytes(b"invented")
            store.read_bytes(digest)
            root.rename(tmp_path / "moved")
            root.mkdir(mode=0o700)
            with pytest.raises(ProvenanceError):
                store.read_bytes(digest)


def test_duck_typed_and_unregistered_grants_cannot_open_content_or_http(tmp_path, monkeypatch):
    from quanto.evaluation_registry import _Grant
    class PretendGrant:
        def consume(self, *_args, **_kwargs):
            return None
    supervisor, _ = setup(tmp_path)
    monkeypatch.setattr(data.http.client, "HTTPSConnection", lambda *_a, **_k: pytest.fail("network"))
    with supervisor.session() as session:
        with Provenance(tmp_path) as store:
            digest = store.put_bytes(b"invented")
            fabricated = _Grant(session, "content_read", digest, session.cache_epoch()[2], "unissued")
            for grant in (PretendGrant(), fabricated):
                with pytest.raises(ProvenanceError):
                    with store._blob(digest, grant=grant):
                        pytest.fail("content opened")
                with pytest.raises(data.AcquisitionError, match="access_refused"):
                    data._http("GET", "https://data.alpaca.markets/", {}, 1, 100, grant=grant)
    assert not content_opens(supervisor)


def test_one_live_grant_cannot_be_consumed_twice_concurrently(tmp_path):
    from quanto.evaluation_registry import consume_grant
    supervisor, _ = setup(tmp_path)
    barrier = threading.Barrier(2)
    with supervisor.session() as session:
        intent = session.content(H)
        with intent.effect(H).start("content_read", H) as grant:
            def consume():
                barrier.wait()
                try:
                    consume_grant(grant, "content_read", H)
                    return "consumed"
                except AccessError:
                    return "refused"
            with ThreadPoolExecutor(2) as pool:
                first, second = pool.submit(consume), pool.submit(consume)
                assert sorted([first.result(), second.result()]) == ["consumed", "refused"]
    assert len(records(supervisor, "effects")) == 1


def test_grant_copy_fields_and_used_flag_cannot_change_issued_effect(tmp_path):
    import copy
    from quanto.evaluation_registry import consume_grant
    supervisor, _ = setup(tmp_path)
    with supervisor.session() as session:
        intent = session.content(H)
        with intent.effect(H).start("content_read", H) as grant:
            with pytest.raises(AccessError):
                consume_grant(copy.copy(grant), "content_read", H)
            grant.identity = "b" * 64
            with pytest.raises(AccessError, match="effect_mismatch"):
                consume_grant(grant, "content_read", "b" * 64)
            consume_grant(grant, "content_read", H)
            grant.used = False
            with pytest.raises(AccessError):
                consume_grant(grant, "content_read", H)
    assert len(records(supervisor, "effects")) == 1


def test_bound_direct_route_denials_have_private_bounded_audit(tmp_path):
    supervisor, _ = setup(tmp_path)
    with supervisor.session() as session:
        request = data._request(REQUEST, "bars", NOW)
        intent = session.acquisition("bars", request)
        url = data._url(request, "bars")
        with pytest.raises(AccessError, match="effect_mismatch"):
            intent.page("POST", url)
        with pytest.raises(data.AcquisitionError, match="access_refused"):
            data._http("GET", url, {}, 1, 100)
        with pytest.raises(data.AcquisitionError, match="access_refused"):
            data._dispatch("GET", url, KEYS, 1, 100, lambda *_: pytest.fail("transport"))
        other = tmp_path / "unissued"
        other.mkdir()
        with pytest.raises(AccessError, match="wrong_store"):
            current_session(other)
    refusals = [json.loads(row["payload"]) for row in records(supervisor, "audit") if row["kind"] == "route_refused"]
    assert {row["operation"] for row in refusals} == {"page", "grant", "dispatch", "root"}
    assert all(set(row) == {"operation", "principal", "reason"} for row in refusals)
    assert not records(supervisor, "effects")


def test_session_is_one_lifetime_and_late_exit_does_not_close_another(tmp_path):
    supervisor, _ = setup(tmp_path)
    first = supervisor.session()
    with first:
        store = Provenance(tmp_path)
        digest = store.put_bytes(b"invented")
        store.read_bytes(digest)
    with pytest.raises(AccessError, match="authority_closed"):
        first.__enter__()
    with supervisor.session() as second:
        first.__exit__(None, None, None)
        assert current_session(tmp_path) is second
        with pytest.raises(ProvenanceError):
            store.read_bytes(digest)
        with Provenance(tmp_path) as fresh:
            assert fresh.read_bytes(digest) == b"invented"
    store.close()
    assert len(content_opens(supervisor)) == 2


def reserve_other(supervisor, reviewer):
    supervisor.relate("security", "alpaca:us_equity:OTHER", "security:two", H)
    return supervisor.reserve(manifest(supervisor, reviewer, security="security:two"))


def test_generic_import_blocks_later_reservation_and_survives_research_rollback(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    with supervisor.session(), Provenance(tmp_path) as store:
        store.journal.connection.execute("BEGIN IMMEDIATE")
        digest = store.put_json({"invented_observation": {"symbol": "OTHER", "value": 17}})
        store.journal.connection.rollback()
        assert store.read_json(digest)["invented_observation"]["value"] == 17
        with pytest.raises(AccessError, match="reservation_conflict"):
            supervisor.reserve(manifest(supervisor, reviewer))
    imported = [row for row in records(supervisor, "intents") if row["operation"] == "content_import"]
    assert len(imported) == 2 and all(row["state"] == "issued" for row in imported)
    assert json.loads(imported[0]["request_document"])["identity_kind"] == "attempt_only"
    assert not records(supervisor, "intent_ends")
    restarted = Supervisor(tmp_path, synthetic=True)
    with pytest.raises(AccessError, match="reservation_conflict"):
        restarted.reserve(manifest(restarted, reviewer))


@pytest.mark.parametrize("label", [None, {}, "pretend-authority"])
def test_unknown_import_after_reservation_is_consumed_and_invalidates_even_if_not_published(tmp_path, label):
    supervisor, reviewer = setup(tmp_path)
    supervisor.reserve(manifest(supervisor, reviewer))
    raw = b"invented already-observed reserved bytes"
    with supervisor.session(), Provenance(tmp_path) as store:
        with pytest.raises(ProvenanceError):
            store.put_bytes(raw, publication=label)
    assert not (tmp_path / "data/objects" / (hashlib.sha256(raw).hexdigest() + ".bin")).exists()
    assert len(records(supervisor, "effects")) == 1
    assert records(supervisor, "effect_ends")[0]["state"] == "completed"
    assert records(supervisor, "invalidations")
    assert not records(supervisor, "intent_ends")


def test_ordinary_intent_cannot_classify_arbitrary_existing_bytes(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    reserve_other(supervisor, reviewer)
    raw = b"invented OTHER reserved observation"
    digest = hashlib.sha256(raw).hexdigest()
    with supervisor.session() as session, Provenance(tmp_path) as store:
        target = tmp_path / "data/objects" / (digest + ".bin")
        target.write_bytes(raw)  # Explicit external-file fixture, outside supported imports.
        target.chmod(0o600)
        with pytest.raises(ProvenanceError):
            store.read_bytes(digest)
        intent = session.acquisition("bars", data._request(REQUEST, "bars", NOW))
        with pytest.raises(AccessError, match="authority_missing"):
            intent.bind_object(digest)
        with pytest.raises(ProvenanceError):
            store.read_bytes(digest)
    assert not records(supervisor, "classifications")
    assert not records(supervisor, "effects")


def test_disjoint_valid_bars_publish_verified_receipt_without_unknown_import(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    reserve_other(supervisor, reviewer)
    with supervisor.session(), Provenance(tmp_path) as store:
        result = data.acquire_bars(tmp_path, REQUEST, transport=lambda *_: response(), credentials=KEYS, clock=lambda: NOW)
        assert result["status"] == "success"
        receipt = store.read_json(result["receipt_sha256"])
        assert receipt["status"] == "success" and receipt["row_count"] == 1
        assert store.read_json(result["normalized_sha256"])["identity"]["symbol"] == "AAPL"
    assert not records(supervisor, "invalidations")
    assert not [row for row in records(supervisor, "intents") if row["operation"] == "content_import"]
    assert any(row["role"] == "receipt" for row in records(supervisor, "publications"))


@pytest.mark.parametrize("record", [
    {"symbol": "OTHER", "ex_date": "2024-06-20", "rate": "17"},
    {"ex_date": "2024-06-20", "rate": "17"},
    {"symbol": "AAPL", "child_symbol": "OTHER", "rate": "17"},
    {"symbol": "AAPL", "party": {"symbol": "OTHER"}, "rate": "17"},
])
def test_action_unresolved_or_multi_party_response_widens_before_publication(tmp_path, record):
    supervisor, reviewer = setup(tmp_path)
    reserve_other(supervisor, reviewer)
    raw = json.dumps({"corporate_actions": {"cash_dividends": [record]}, "next_page_token": None}).encode()
    with supervisor.session(), Provenance(tmp_path) as store:
        result = actions.acquire_actions(tmp_path, REQUEST, transport=lambda *_: data.HTTPResult(200, raw), credentials=KEYS, clock=lambda: NOW)
        assert result["status"] != "success"
        with pytest.raises(ProvenanceError):
            store.read_bytes(hashlib.sha256(raw).hexdigest())
    assert records(supervisor, "invalidations")
    assert records(supervisor, "widenings")
    assert not (tmp_path / "data/objects" / (hashlib.sha256(raw).hexdigest() + ".bin")).exists()


def test_disjoint_single_party_actions_preserve_positive_development_flow(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    reserve_other(supervisor, reviewer)
    raw = json.dumps({"corporate_actions": {"cash_dividends": [{"symbol": "AAPL", "ex_date": "2024-06-03", "rate": "1"}]}, "next_page_token": None}).encode()
    with supervisor.session(), Provenance(tmp_path) as store:
        result = actions.acquire_actions(tmp_path, REQUEST, transport=lambda *_: data.HTTPResult(200, raw), credentials=KEYS, clock=lambda: NOW)
        assert result["status"] == "success"
        assert store.read_json(result["receipt_sha256"])["status"] == "success"
    assert not records(supervisor, "invalidations")


def test_disjoint_calendar_dates_publish_receipt_without_unknown_import(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    supervisor.reserve(manifest(supervisor, reviewer, start="2024-07-01", end="2024-07-31"))
    raw = json.dumps([{"date": "2024-06-03", "open": "09:30", "close": "16:00"}]).encode()
    with supervisor.session(), Provenance(tmp_path) as store:
        result = data.acquire_calendar(tmp_path, {"start": "2024-06-03", "end": "2024-06-05"},
            transport=lambda *_: data.HTTPResult(200, raw), credentials=KEYS, clock=lambda: NOW)
        assert result["status"] == "success"
        assert store.read_json(result["receipt_sha256"])["status"] == "success"
        assert len(store.read_json(result["normalized_sha256"])["sessions"]) == 1
    assert not records(supervisor, "invalidations")
    assert not [row for row in records(supervisor, "intents") if row["operation"] == "content_import"]


def test_producer_permissions_reject_skipped_effect_wrong_response_and_forged_normalization(tmp_path):
    supervisor, _ = setup(tmp_path)
    with supervisor.session() as session:
        request = data._request(REQUEST, "bars", NOW)
        intent = session.acquisition("bars", request)
        producer = supervisor.producer(intent, "alpaca_bars")
        with pytest.raises(AccessError):
            producer.permit("response", response().body)
        with pytest.raises(AccessError):
            producer.permit("normalized", b'{"invented":"OTHER"}')
        with pytest.raises(AccessError):
            producer.permit("request", b'{"invented":"OTHER"}')
        url = data._url(request, "bars")
        data._dispatch("GET", url, KEYS, 1, 10000, lambda *_: response(), permit=intent.page("GET", url), producer=producer)
        with pytest.raises(AccessError):
            producer.permit("response", b"invented OTHER bytes")
        with pytest.raises(AccessError):
            producer.permit("normalized", b'{"identity":{"symbol":"AAPL"},"bars":[17]}')
    assert len(records(supervisor, "producer_responses")) == 1
    assert not records(supervisor, "publications")


def test_exact_publication_is_one_use_and_cannot_survive_widening(tmp_path):
    from quanto.evaluation_registry import PublicationPermit
    supervisor, _ = setup(tmp_path)
    with supervisor.session() as session, Provenance(tmp_path) as store:
        request = data._request(REQUEST, "bars", NOW)
        intent = session.acquisition("bars", request)
        producer = supervisor.producer(intent, "alpaca_bars")
        raw = json.dumps(data._prepared_request(request, "bars"), sort_keys=True, separators=(",", ":")).encode()
        permit = producer.permit("request", raw)
        fake = PublicationPermit(producer, permit.identity, permit.digest)
        with pytest.raises(ProvenanceError):
            store.put_bytes(raw, publication=fake)
        digest = store.put_bytes(raw, publication=permit)
        with pytest.raises(ProvenanceError):
            store.put_bytes(raw, publication=permit)
        stale = producer.permit("request", raw)
        intent.widen_unknown()
        with pytest.raises(ProvenanceError):
            store.put_bytes(raw, publication=stale)
        assert store.read_bytes(digest) == raw
    assert len(records(supervisor, "publication_ends")) == 1


def test_direct_dispatch_cannot_skip_response_widening_without_a_publisher(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    reserve_other(supervisor, reviewer)
    raw = json.dumps({"symbol": "OTHER", "bars": [], "next_page_token": None}).encode()
    with supervisor.session() as session:
        request = data._request(REQUEST, "bars", NOW)
        intent = session.acquisition("bars", request)
        url = data._url(request, "bars")
        assert data._dispatch("GET", url, KEYS, 1, 10000, lambda *_: data.HTTPResult(200, raw), permit=intent.page("GET", url)).body == raw
    assert records(supervisor, "widenings") and records(supervisor, "invalidations")


@pytest.mark.parametrize("kind", ["bars", "actions", "calendar"])
def test_unclassified_extra_provider_fields_cannot_inherit_request_coverage(tmp_path, kind):
    supervisor, reviewer = setup(tmp_path)
    supervisor.relate("security", "alpaca:us_equity:OTHER", "security:two", H)
    supervisor.reserve(manifest(supervisor, reviewer, start="2024-07-01", end="2024-07-31", security="security:two"))
    if kind == "bars":
        body = json.loads(response().body)
        body["bars"][0]["other_observation"] = {"symbol": "OTHER", "value": 17}
        request, acquire = REQUEST, data.acquire_bars
    elif kind == "actions":
        body = {"corporate_actions": {"cash_dividends": [{"symbol": "AAPL", "rate": "1", "foreign_price": 17}]}, "next_page_token": None}
        request, acquire = REQUEST, actions.acquire_actions
    else:
        body = [{"date": "2024-06-03", "open": "09:30", "close": "16:00", "other_observation": "OTHER July"}]
        request, acquire = {"start": "2024-06-03", "end": "2024-06-05"}, data.acquire_calendar
    raw = json.dumps(body).encode()
    with supervisor.session(), Provenance(tmp_path) as store:
        result = acquire(tmp_path, request, transport=lambda *_: data.HTTPResult(200, raw), credentials=KEYS, clock=lambda: NOW)
        assert result["status"] != "success"
        with pytest.raises(ProvenanceError):
            store.read_bytes(hashlib.sha256(raw).hexdigest())
    assert records(supervisor, "widenings") and records(supervisor, "invalidations")


def test_invalid_provider_response_keeps_unknown_exposure_and_refuses_publication(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    reserve_other(supervisor, reviewer)
    with supervisor.session():
        result = data.acquire_bars(tmp_path, REQUEST, transport=lambda *_: data.HTTPResult(403, b"invented unclassified response"), credentials=KEYS, clock=lambda: NOW)
    assert result["status"] != "success"
    assert records(supervisor, "widenings") and records(supervisor, "invalidations")


@pytest.mark.parametrize("kind", ["bars", "actions"])
@pytest.mark.parametrize("outcome", ["foreign_response", "http_error", "partial_failure", "malformed_token", "valid_null", "valid_string"])
def test_direct_raw_http_accounts_response_scope_without_dispatch_or_publisher(tmp_path, monkeypatch, kind, outcome):
    # Non-synthetic authority exercises the raw boundary, but the TLS constructor
    # is replaced before authority exists. No network or real credentials enter.
    calls = []
    symbol = "OTHER" if outcome == "foreign_response" else "AAPL"
    token = {"symbol": "OTHER", "price": 17} if outcome == "malformed_token" else "page_2" if outcome == "valid_string" else None
    body = ({"symbol": symbol, "bars": [], "next_page_token": token} if kind == "bars" else
            {"corporate_actions": {"cash_dividends": [{"symbol": symbol, "rate": "1"}]}, "next_page_token": token})
    raw = json.dumps(body).encode()

    class FakeConnection:
        def __init__(self, *_args, **_kwargs):
            self.sock, self.chunks = self, iter([raw, b""])
            calls.append("constructed")
        def connect(self):
            pass
        def settimeout(self, _timeout):
            pass
        def request(self, *_args, **_kwargs):
            calls.append("request")
        def getresponse(self):
            return self
        @property
        def status(self):
            return 403 if outcome == "http_error" else 200
        def read1(self, _limit):
            if outcome == "partial_failure" and "read" in calls:
                raise TimeoutError("synthetic interrupted response")
            calls.append("read")
            return next(self.chunks)
        def close(self):
            calls.append("closed")

    monkeypatch.setattr(data.http.client, "HTTPSConnection", FakeConnection)
    supervisor = Supervisor(tmp_path, synthetic=False)
    supervisor.relate("security", "alpaca:us_equity:AAPL", "security:one", H)
    reviewer = supervisor.issue_principal()
    reserve_other(supervisor, reviewer)
    with supervisor.session() as session:
        request = (data._request(REQUEST, "bars", NOW) if kind == "bars"
                   else actions._request(json.dumps(REQUEST), NOW))
        intent = session.acquisition(kind, request)
        url = data._url(request, "bars") if kind == "bars" else actions._url(request)
        if outcome == "partial_failure":
            with pytest.raises(TimeoutError):
                with intent.page("GET", url).start("provider_page", request_identity("GET", url)) as grant:
                    data._http("GET", url, {}, 1, 10000, grant=grant)
        else:
            with intent.page("GET", url).start("provider_page", request_identity("GET", url)) as grant:
                result = data._http("GET", url, {}, 1, 10000, grant=grant)
                assert result.status == (403 if outcome == "http_error" else 200)
    assert calls.count("request") == 1 and calls[-1] == "closed"
    if outcome.startswith("valid_"):
        assert not records(supervisor, "widenings") and not records(supervisor, "invalidations")
    else:
        assert records(supervisor, "widenings") and records(supervisor, "invalidations")
    assert not records(supervisor, "publications")


def test_injected_transport_failure_retains_unknown_scope_and_blocks_next_page(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    reserve_other(supervisor, reviewer)
    calls = []
    def broken(*_args):
        calls.append("partial response")
        raise TimeoutError("invented incomplete response")
    with supervisor.session() as session:
        request = data._request(REQUEST, "bars", NOW)
        intent = session.acquisition("bars", request)
        url = data._url(request, "bars")
        with pytest.raises(data.AcquisitionError, match="request_timeout"):
            data._dispatch("GET", url, KEYS, 1, 10000, broken, permit=intent.page("GET", url))
        next_url = data._url(request, "bars", "next")
        with pytest.raises(data.AcquisitionError, match="access_refused"):
            data._dispatch("GET", next_url, KEYS, 1, 10000, lambda *_: pytest.fail("second transport"), permit=intent.page("GET", next_url))
    assert calls == ["partial response"]
    assert records(supervisor, "effect_ends")[0]["state"] == "uncertain"
    assert len(records(supervisor, "effects")) == 1
    assert records(supervisor, "widenings") and records(supervisor, "invalidations")


def test_revoked_principal_import_is_still_an_observation(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    supervisor.reserve(manifest(supervisor, reviewer))
    with supervisor.session() as session, Provenance(tmp_path) as store:
        supervisor.revoke_principal(session.principal, H)
        with pytest.raises(ProvenanceError):
            store.put_bytes(b"invented already received observation")
    assert any(row["operation"] == "content_import" for row in records(supervisor, "intents"))
    assert len(records(supervisor, "effects")) == 1
    assert any(row["reason"] == "exposure_conflict" for row in records(supervisor, "invalidations"))


@pytest.mark.parametrize("kind", ["bars", "actions"])
@pytest.mark.parametrize("token", [{"symbol": "OTHER", "price": 17}, ["OTHER"], 17, True, "", "invalid token", "x" * 2049])
def test_malformed_pagination_metadata_is_unknown_before_raw_publication(tmp_path, kind, token):
    supervisor, reviewer = setup(tmp_path)
    reserve_other(supervisor, reviewer)
    body = (json.loads(response().body) if kind == "bars" else
            {"corporate_actions": {"cash_dividends": [{"symbol": "AAPL", "rate": "1"}]}})
    body["next_page_token"] = token
    raw = json.dumps(body).encode()
    with supervisor.session(), Provenance(tmp_path) as store:
        acquire = data.acquire_bars if kind == "bars" else actions.acquire_actions
        result = acquire(tmp_path, REQUEST, transport=lambda *_: data.HTTPResult(200, raw), credentials=KEYS, clock=lambda: NOW)
        assert result["status"] != "success"
        with pytest.raises(ProvenanceError):
            store.read_bytes(hashlib.sha256(raw).hexdigest())
    assert records(supervisor, "widenings") and records(supervisor, "invalidations")
    assert not (tmp_path / "data/objects" / (hashlib.sha256(raw).hexdigest() + ".bin")).exists()


@pytest.mark.parametrize("kind", ["bars", "actions"])
def test_direct_dispatch_malformed_token_widens_without_publisher(tmp_path, kind):
    supervisor, reviewer = setup(tmp_path)
    reserve_other(supervisor, reviewer)
    body = (json.loads(response().body) if kind == "bars" else {"corporate_actions": {"cash_dividends": []}})
    body["next_page_token"] = {"symbol": "OTHER", "price": 17}
    raw = json.dumps(body).encode()
    with supervisor.session() as session:
        request = (data._request(REQUEST, kind, NOW) if kind == "bars"
                   else actions._request(json.dumps(REQUEST), NOW))
        intent = session.acquisition(kind, request)
        url = data._url(request, kind) if kind == "bars" else actions._url(request)
        data._dispatch("GET", url, KEYS, 1, 10000, lambda *_: data.HTTPResult(200, raw), permit=intent.page("GET", url))
    assert records(supervisor, "widenings") and records(supervisor, "invalidations")
    assert not records(supervisor, "publications")


@pytest.mark.parametrize("before", [True, False])
@pytest.mark.parametrize("input_kind", ["oversized_bytes", "invalid_json", "oversized_json", "non_bytes", "cyclic_json"])
def test_rejected_supplied_inputs_are_unknown_observations_without_hashing_content(tmp_path, monkeypatch, before, input_kind):
    from quanto.provenance import MAX_ARTIFACT_BYTES
    supervisor, reviewer = setup(tmp_path)
    if before:
        supervisor.reserve(manifest(supervisor, reviewer))
    original = hashlib.sha256
    def bounded_hash(raw=b"", *args, **kwargs):
        assert len(raw) <= MAX_ARTIFACT_BYTES, "Oversized supplied content was hashed"
        return original(raw, *args, **kwargs)
    monkeypatch.setattr(hashlib, "sha256", bounded_hash)
    with supervisor.session(), Provenance(tmp_path) as store:
        with pytest.raises(ProvenanceError):
            if input_kind == "oversized_bytes":
                store.put_bytes(b"x" * (MAX_ARTIFACT_BYTES + 1))
            elif input_kind == "invalid_json":
                store.put_json({"other_observation": 17, "bad": float("nan")})
            elif input_kind == "oversized_json":
                store.put_json({"other_observation": "x" * (1024 * 1024 + 1)})
            elif input_kind == "non_bytes":
                store.put_bytes({"other_observation": 17})
            else:
                value = {"other_observation": 17}
                value["cycle"] = value
                store.put_json(value)
        if not before:
            with pytest.raises(AccessError, match="reservation_conflict"):
                supervisor.reserve(manifest(supervisor, reviewer))
    imported = [row for row in records(supervisor, "intents") if row["operation"] == "content_import"]
    assert len(imported) == 1
    assert json.loads(imported[0]["request_document"])["identity_kind"] == "attempt_only"
    assert json.loads(imported[0]["coverage"])["profile"] == "unknown"
    assert records(supervisor, "effect_ends")[0]["state"] == "completed"
    assert not records(supervisor, "intent_ends")
    if before:
        assert records(supervisor, "invalidations")
    assert not list((tmp_path / "data/objects").iterdir())


def test_json_input_is_recorded_before_serialization_is_attempted(tmp_path, monkeypatch):
    import quanto.provenance as provenance
    supervisor, reviewer = setup(tmp_path)
    called = []
    def interrupted(_value):
        assert len(records(supervisor, "effects")) == 1
        called.append(True)
        raise KeyboardInterrupt("synthetic serializer interruption")
    with supervisor.session(), Provenance(tmp_path) as store:
        monkeypatch.setattr(provenance, "canonical_json", interrupted)
        with pytest.raises(KeyboardInterrupt):
            store.put_json({"invented_other_observation": 17})
        with pytest.raises(AccessError, match="reservation_conflict"):
            supervisor.reserve(manifest(supervisor, reviewer))
    assert called == [True]


@pytest.mark.parametrize("failure", ["closed_store", "transaction"])
def test_bytes_are_recorded_before_research_storage_failure(tmp_path, monkeypatch, failure):
    supervisor, reviewer = setup(tmp_path)
    with supervisor.session(), Provenance(tmp_path) as store:
        if failure == "closed_store":
            store.close()
        else:
            def broken():
                raise ProvenanceError("synthetic transaction refusal")
            monkeypatch.setattr(store.journal, "_transaction", broken)
        with pytest.raises(ProvenanceError):
            store.put_bytes(b"invented OTHER observed content")
        with pytest.raises(AccessError, match="reservation_conflict"):
            supervisor.reserve(manifest(supervisor, reviewer))
    assert len(records(supervisor, "effects")) == 1
    assert records(supervisor, "effect_ends")[0]["state"] == "completed"


def test_preissued_publication_permit_is_fenced_after_intent_rejection(tmp_path):
    supervisor, reviewer = setup(tmp_path)
    reserve_other(supervisor, reviewer)
    with supervisor.session() as session, Provenance(tmp_path) as store:
        request = data._request(REQUEST, "bars", NOW)
        intent = session.acquisition("bars", request)
        producer = supervisor.producer(intent, "alpaca_bars")
        raw = data.canonical_json(data._prepared_request(request, "bars")).encode()
        permit = producer.permit("request", raw)
        intent.reject_before_access()
        with pytest.raises(ProvenanceError):
            store.put_bytes(raw, publication=permit)
    assert not records(supervisor, "publication_ends")
    assert records(supervisor, "invalidations")
    assert any(row["operation"] == "content_import" for row in records(supervisor, "intents"))

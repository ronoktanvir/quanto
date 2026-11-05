"""D012 synthetic_fixture software checks; every authority and value is invented.

Fixture construction writes an invented historical device in a disposable DB.
Accepted reopening always uses actual stat calls, including fresh interpreters.
No production runtime, provider, credential, market data or controller is used.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from quanto import authority_reattachment as attachment
from quanto.evaluation_registry import AccessError, Coverage, Supervisor, _json
from quanto.ledger import Journal

H = "a" * 64
PYTHON = sys.executable
ENV = {"PATH": os.defpath, "PYTHONPATH": str(Path(attachment.__file__).parent.parent),
       "PYTHONDONTWRITEBYTECODE": "1"}


def _change_configuration(path, key, value):
    """Craft invented fixture history, never alter real metadata or patch stat."""
    with sqlite3.connect(path) as db:
        sql = db.execute("SELECT sql FROM sqlite_schema WHERE name='no_update_configuration'").fetchone()[0]
        db.execute("DROP TRIGGER no_update_configuration")
        db.execute("UPDATE configuration SET value=? WHERE name=?", (value, key))
        db.execute(sql)


def fixture_store(root, *, mismatch=True):
    (root / "runtime").mkdir(mode=0o700)
    (root / "data/objects").mkdir(mode=0o700, parents=True)
    research = root / "runtime/research.sqlite"
    with Journal(research) as journal:
        journal.append_event("invented_consumed_controller", {"consumed": True})
        journal.reserve("invented_uncertain_hold", 123_000)
        journal.mark_uncertain("invented_uncertain_hold", "invented timeout")
    research.chmod(0o600)
    supervisor = Supervisor(root)
    with supervisor._transaction() as db:
        principal = supervisor.principal
        db.execute("INSERT INTO principals VALUES ('invented-revoked','fixture')")
        db.execute("INSERT INTO principal_revocations VALUES ('invented-revoked',?,'fixture')", (H,))
        unknown = _json({"profile": "unknown", "securities": [], "start": None, "end": None})
        db.execute("INSERT INTO intents VALUES ('invented-intent',?,'content_read',?,'{}',?,0,'issued',NULL,'fixture')", (principal, H, unknown))
        db.execute("INSERT INTO intent_ends VALUES ('invented-intent','consumed','fixture')")
        db.execute("INSERT INTO effects VALUES ('invented-effect','invented-intent',?,'fixture')", (H,))
        db.execute("INSERT INTO effect_ends VALUES ('invented-effect','uncertain','fixture')")
        db.execute("INSERT INTO effects VALUES ('invented-pending','invented-intent',?,'fixture')", ("b" * 64,))
        db.execute("INSERT INTO reservations VALUES ('invented-reservation','{}',?,'[]','[]',0,'fixture')", (unknown,))
        db.execute("INSERT INTO invalidations VALUES ('invented-reservation','invented',0,'fixture')")
        Supervisor._event(db, "invented_preserved_state", {"evidence_kind": "synthetic_fixture"})
    if mismatch:
        _change_configuration(supervisor.path, "device", str(root.stat().st_dev + 91))
    return supervisor.path, research


def frozen_request(root):
    first = attachment.inspect_authority(root)["snapshot"]
    witness = {"sha256": hashlib.sha256(b"invented retained local witness").hexdigest(),
               "control": first["control"]["tables"], "research": first["research"]["tables"]}
    snapshot = attachment.inspect_authority(root, witnesses=[witness])["snapshot"]
    old = deepcopy(snapshot["identities"])
    for value in old.values():
        value["device"] += 91
    return attachment.ReattachmentRequest.freeze(
        snapshot=snapshot, old_identities=old, attempt="invented-consumed-attempt",
        bindings={"implementation": attachment.implementation_identity(), "policy_sha256": H,
                  "reviews": {name: H for name in ("critic", "quality", "scope", "fable", "opus")},
                  "campaign_sha256": H})


def run_python(code, *args, timeout=10):
    return subprocess.run([PYTHON, "-c", code, *map(str, args)], env=ENV, text=True,
                          capture_output=True, timeout=timeout, check=False)


def rows(path):
    with sqlite3.connect(path) as db:
        names = [row[0] for row in db.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name")]
        return {name: db.execute(f'SELECT rowid,* FROM "{name}" ORDER BY rowid').fetchall() for name in names}


def test_apply_preserves_every_prior_row_and_reopens_fresh_process(tmp_path):
    control, research = fixture_store(tmp_path)
    request = frozen_request(tmp_path)
    before_control, before_research = rows(control), rows(research)
    with pytest.raises(AccessError, match="wrong_store"):
        Supervisor(tmp_path)
    result = attachment.apply_reattachment(tmp_path, request)
    after = rows(control)
    for name in before_control:
        assert (after[name][:-1] if name == "audit" else after[name]) == before_control[name]
    assert rows(research) == before_research
    assert result["limits"] == attachment.FLAGS
    code = '''
import json,sys
from pathlib import Path
from quanto.evaluation_registry import Supervisor,AccessError
s=Supervisor(Path(sys.argv[1]),attachment_event_sha256=sys.argv[2])
with s.session():
    assert s.overview()["protected_eligible"] is False
    try: s.session("invented-revoked")
    except AccessError as exc: assert exc.reason=="principal_revoked"
    else: raise AssertionError("revocation lost")
with s._db() as db:
    assert dict(db.execute("SELECT name,value FROM configuration"))["legacy_unknown"]=="True"
print(json.dumps({"principal":s.principal,"store_id":s.store_id}))
'''
    completed = run_python(code, tmp_path, result["event_sha256"])
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["store_id"] == request.document["snapshot"]["configuration"]["store_id"]


def test_explicit_pin_required_even_when_original_device_reappears(tmp_path):
    control, _ = fixture_store(tmp_path)
    result = attachment.apply_reattachment(tmp_path, frozen_request(tmp_path))
    for pin in (None, "f" * 64):
        with pytest.raises(AccessError):
            Supervisor(tmp_path, attachment_event_sha256=pin)
    # Craft an adversarial original-device fallback; no actual stat is patched.
    _change_configuration(control, "device", str(tmp_path.stat().st_dev))
    for pin in (None, result["event_sha256"]):
        with pytest.raises(AccessError):
            Supervisor(tmp_path, attachment_event_sha256=pin)


def test_no_event_keeps_strict_normal_open_and_supplied_pin_refuses(tmp_path):
    fixture_store(tmp_path, mismatch=False)
    supervisor = Supervisor(tmp_path)
    with supervisor.session():
        assert supervisor.overview()["protected_acquisition_enabled"] is False
    with pytest.raises(AccessError, match="attachment_missing"):
        Supervisor(tmp_path, attachment_event_sha256=H)


def test_normal_control_and_research_growth_extends_accepted_anchor(tmp_path):
    control, research = fixture_store(tmp_path)
    result = attachment.apply_reattachment(tmp_path, frozen_request(tmp_path))
    supervisor = Supervisor(tmp_path, attachment_event_sha256=result["event_sha256"])
    supervisor.issue_principal()
    with Journal(research) as journal:
        journal.append_event("invented_later_growth", {"fixture": True})
        journal.settle("invented_uncertain_hold", 5)
    with Supervisor(tmp_path, attachment_event_sha256=result["event_sha256"]).session():
        assert rows(control)["audit"][-1][2] != attachment.EVENT_KIND


@pytest.mark.parametrize("change", ["control_append", "research_append", "old_row", "schema", "configuration", "witness"])
def test_stale_or_divergent_frozen_state_refuses_without_append(tmp_path, change):
    control, research = fixture_store(tmp_path)
    request = frozen_request(tmp_path)
    if change == "control_append":
        with sqlite3.connect(control) as db:
            Supervisor._event(db, "invented_racer", {})
    elif change == "research_append":
        with Journal(research) as journal:
            journal.append_event("invented_racer", {})
    elif change == "old_row":
        with sqlite3.connect(research) as db:
            db.execute("UPDATE reservations SET reserved_micro_usd=123001")
    elif change == "schema":
        with sqlite3.connect(control) as db:
            db.execute("DROP TRIGGER no_delete_principals")
    elif change == "configuration":
        _change_configuration(control, "store_id", "another-invented-store")
    else:
        value = request.document
        value["snapshot"]["witnesses"][0]["control"]["principals"]["sha256"] = "e" * 64
        request = attachment.ReattachmentRequest(_json(value))
    before = rows(control)
    with pytest.raises(AccessError):
        attachment.apply_reattachment(tmp_path, request)
    assert rows(control) == before


@pytest.mark.parametrize("kind", ["root_mode", "control_inode", "research_inode", "objects_inode", "research_missing", "control_missing"])
def test_physical_or_missing_store_refuses_without_recreation(tmp_path, kind):
    control, research = fixture_store(tmp_path)
    request = frozen_request(tmp_path)
    if kind == "root_mode":
        tmp_path.chmod(0o750)
    elif kind.endswith("_missing"):
        (control if kind == "control_missing" else research).unlink()
    elif kind == "objects_inode":
        directory = tmp_path / "data/objects"
        directory.rename(directory.with_name("old_objects"))
        directory.mkdir(mode=0o700)
    else:
        path = control if kind == "control_inode" else research
        content = path.read_bytes()
        path.rename(path.with_suffix(".old"))
        path.write_bytes(content)
        path.chmod(0o600)
    with pytest.raises(AccessError):
        attachment.apply_reattachment(tmp_path, request)
    if kind.endswith("_missing"):
        assert not (control if kind == "control_missing" else research).exists()


def test_missing_pinned_supervisor_does_not_bootstrap(tmp_path):
    with pytest.raises(AccessError):
        Supervisor(tmp_path, attachment_event_sha256=H)
    assert list(tmp_path.iterdir()) == []


def test_replay_duplicate_event_and_corrupt_chain_refuse(tmp_path):
    control, _ = fixture_store(tmp_path)
    request = frozen_request(tmp_path)
    result = attachment.apply_reattachment(tmp_path, request)
    with pytest.raises(AccessError):
        attachment.apply_reattachment(tmp_path, request)
    with sqlite3.connect(control) as db:
        payload = json.loads(db.execute("SELECT payload FROM audit WHERE kind=?", (attachment.EVENT_KIND,)).fetchone()[0])
        Supervisor._event(db, attachment.EVENT_KIND, payload)
    with pytest.raises(AccessError, match="attachment_conflict"):
        Supervisor(tmp_path, attachment_event_sha256=result["event_sha256"])


def test_chain_corruption_before_or_after_event_refuses(tmp_path):
    control, _ = fixture_store(tmp_path)
    result = attachment.apply_reattachment(tmp_path, frozen_request(tmp_path))
    with sqlite3.connect(control) as db:
        db.execute("DROP TRIGGER no_update_audit")
        db.execute("UPDATE audit SET payload='{}' WHERE sequence=1")
    with pytest.raises(AccessError, match="chain_mismatch"):
        Supervisor(tmp_path, attachment_event_sha256=result["event_sha256"])


@pytest.mark.parametrize("boundary", ["after_append", "before_commit"])
def test_injected_precommit_failure_leaves_no_event_or_other_change(tmp_path, monkeypatch, boundary):
    control, research = fixture_store(tmp_path)
    request = frozen_request(tmp_path)
    before = rows(control), rows(research)
    if boundary == "after_append":
        original = Supervisor._event
        def fail(db, kind, payload):
            original(db, kind, payload)
            raise RuntimeError("invented interruption after append")
        monkeypatch.setattr(Supervisor, "_event", staticmethod(fail))
    else:
        original = attachment.implementation_identity
        calls = []
        def fail():
            calls.append(True)
            if len(calls) == 2:
                raise RuntimeError("invented interruption before commit")
            return original()
        monkeypatch.setattr(attachment, "implementation_identity", fail)
    with pytest.raises(RuntimeError):
        attachment.apply_reattachment(tmp_path, request)
    assert (rows(control), rows(research)) == before


def test_lost_postcommit_output_reconciles_read_only_without_retry(tmp_path):
    fixture_store(tmp_path)
    request = frozen_request(tmp_path)
    frozen = tmp_path / "invented-request.json"
    frozen.write_text(request.encoded)
    code = '''
import os,sys
from pathlib import Path
from quanto.authority_reattachment import ReattachmentRequest,apply_reattachment
apply_reattachment(Path(sys.argv[1]),ReattachmentRequest(Path(sys.argv[2]).read_text()))
os._exit(9)
'''
    child = run_python(code, tmp_path, frozen)
    assert child.returncode == 9, child.stderr
    observed = attachment.inspect_authority(tmp_path)
    assert len(observed["attachments"]) == 1
    assert observed["attachments"][0]["payload"]["plan_sha256"] == request.sha256
    with Supervisor(tmp_path, attachment_event_sha256=observed["attachments"][0]["event_hash"]).session():
        pass


def test_live_session_excludes_admin_in_another_process_and_releases_on_exit(tmp_path):
    control, _ = fixture_store(tmp_path, mismatch=False)
    supervisor = Supervisor(tmp_path)
    code = '''
import sys
from pathlib import Path
from quanto.authority_reattachment import maintenance_gate
from quanto.evaluation_registry import AccessError
try:
    with maintenance_gate(Path(sys.argv[1]),exclusive=True,timeout=.15): pass
except AccessError as exc:
    print(exc.reason); sys.exit(3)
'''
    with supervisor.session():
        # A nested registry transaction succeeds while the session holds SH.
        supervisor.issue_principal()
        child = run_python(code, control)
        assert child.returncode == 3 and child.stdout.strip() == "maintenance_busy", child.stderr
    child = run_python(code, control)
    assert child.returncode == 0, child.stderr


def test_exclusive_admin_gate_excludes_fresh_supervisor_and_sqlite_writer(tmp_path):
    control, research = fixture_store(tmp_path, mismatch=False)
    with attachment.maintenance_gate(control, exclusive=True, timeout=.2):
        child = run_python('from pathlib import Path; from quanto.evaluation_registry import Supervisor; import sys; Supervisor(Path(sys.argv[1]))', tmp_path)
        assert child.returncode != 0 and "maintenance_busy" in child.stderr
    # The advisory gate and SQLite locks coexist. BEGIN IMMEDIATE fences a
    # non-upgraded cooperating SQL writer even though it does not use flock.
    with sqlite3.connect(control, isolation_level=None) as db, sqlite3.connect(research, isolation_level=None) as research_db:
        db.execute("BEGIN IMMEDIATE")
        research_db.execute("BEGIN IMMEDIATE")
        for path in (control, research):
            child = run_python('import sqlite3,sys; db=sqlite3.connect(sys.argv[1],timeout=.1); db.execute("BEGIN IMMEDIATE")', path)
            assert child.returncode != 0 and "locked" in child.stderr
        db.rollback()
        research_db.rollback()


def test_real_competing_processes_commit_exactly_one_event(tmp_path):
    control, _ = fixture_store(tmp_path)
    request = frozen_request(tmp_path)
    frozen = tmp_path / "invented-request.json"
    frozen.write_text(request.encoded)
    code = '''
import sys
from pathlib import Path
from quanto.authority_reattachment import ReattachmentRequest,apply_reattachment
try: print(apply_reattachment(Path(sys.argv[1]),ReattachmentRequest(Path(sys.argv[2]).read_text()))["event_sha256"])
except Exception as exc: print(type(exc).__name__); sys.exit(3)
'''
    children = [subprocess.Popen([PYTHON, "-c", code, str(tmp_path), str(frozen)], env=ENV,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    try:
        outputs = [child.communicate(timeout=15) for child in children]
        assert sorted(child.returncode for child in children) == [0, 3], outputs
        assert sum(row[2] == attachment.EVENT_KIND for row in rows(control)["audit"]) == 1
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=3)


@pytest.mark.parametrize("limits", [attachment.Limits(rows=1), attachment.Limits(bytes=50), attachment.Limits(tables=1)])
def test_bounded_inspection_refuses_before_acceptance(tmp_path, limits):
    control, _ = fixture_store(tmp_path)
    before = rows(control)
    with pytest.raises(AccessError):
        attachment.inspect_authority(tmp_path, limits=limits)
    assert rows(control) == before


def test_frozen_request_owns_canonical_values_and_rejects_malformed_fields(tmp_path):
    fixture_store(tmp_path)
    request = frozen_request(tmp_path)
    document = request.document
    document["attempt"] = "mutated"
    assert request.document["attempt"] == "invented-consumed-attempt"
    for mutate in (
        lambda d: d["snapshot"]["witnesses"][0].update({"unexpected": True}),
        lambda d: d["snapshot"]["control"]["tables"].update({"bad;SQL": {}}),
        lambda d: d["snapshot"]["research"]["tables"]["events"].update({"rows": True}),
        lambda d: d.update({"version": True}),
        lambda d: d["old_identities"]["root"].update({"inode": 1}),
    ):
        value = request.document
        mutate(value)
        with pytest.raises(AccessError):
            attachment.ReattachmentRequest(_json(value))


@pytest.mark.parametrize("mutation", ["omit_table", "witness", "limits", "plan", "head", "version", "event_kind"])
def test_valid_hash_chain_does_not_authorize_malformed_acceptance(tmp_path, mutation):
    control, _ = fixture_store(tmp_path)
    request = frozen_request(tmp_path)
    document = request.document
    payload = {"version": 1, "plan_sha256": request.sha256, "request": document,
               "limits": dict(attachment.FLAGS)}
    kind = attachment.EVENT_KIND
    if mutation == "omit_table":
        del document["snapshot"]["control"]["tables"]["principals"]
    elif mutation == "witness":
        document["snapshot"]["witnesses"][0]["research"] = {"bad;SQL": {}}
    elif mutation == "limits":
        payload["limits"]["legacy_unknown"] = 1
    elif mutation == "plan":
        payload["plan_sha256"] = "f" * 64
    elif mutation == "head":
        document["snapshot"]["control"]["head"]["head"] = "f" * 64
    elif mutation == "version":
        payload["version"] = 2
    else:
        kind = "authority_reattachment_v99"
    if mutation in {"omit_table", "witness", "head"}:
        payload["plan_sha256"] = hashlib.sha256(_json(document).encode()).hexdigest()
    with sqlite3.connect(control) as db:
        Supervisor._event(db, kind, payload)
        pin = db.execute("SELECT event_hash FROM audit ORDER BY sequence DESC LIMIT 1").fetchone()[0]
    with pytest.raises(AccessError):
        Supervisor(tmp_path, attachment_event_sha256=pin)


def test_protected_and_legacy_refusals_remain_behaviorally_enforced(tmp_path):
    fixture_store(tmp_path)
    result = attachment.apply_reattachment(tmp_path, frozen_request(tmp_path))
    supervisor = Supervisor(tmp_path, attachment_event_sha256=result["event_sha256"])
    reviewer = supervisor.issue_principal()
    supervisor.relate("security", "invented:TICKER", "security:invented", H)
    manifest = {"coverage": Coverage("bars", ("security:invented",), "2020-01-01", "2020-12-31").document(),
                "warmup": {"start": "2020-01-01", "end": "2020-06-30"},
                "final": {"start": "2020-07-01", "end": "2020-12-31"},
                **{name: H for name in ("candidate_sha256", "code_sha256", "dependencies_sha256", "scenarios_sha256", "rights_sha256", "release_sha256")},
                "selectors": [supervisor.principal], "reviewers": [reviewer]}
    with pytest.raises(AccessError, match="legacy_unreconciled"):
        supervisor.reserve(manifest)
    with pytest.raises(AccessError, match="protected_unavailable"):
        supervisor.protected_acquire()
    with supervisor.session():
        assert supervisor.overview()["protected_eligible"] is False


def test_stale_supervisor_cannot_adopt_event_after_construction(tmp_path):
    control, _ = fixture_store(tmp_path, mismatch=False)
    stale = Supervisor(tmp_path)
    _change_configuration(control, "device", str(tmp_path.stat().st_dev + 91))
    attachment.apply_reattachment(tmp_path, frozen_request(tmp_path))
    with pytest.raises(AccessError, match="attachment_missing"):
        stale.issue_principal()
    with pytest.raises(AccessError, match="attachment_missing"):
        stale.session()


def test_physical_boundaries_after_acceptance_are_not_only_root_control(tmp_path):
    _, research = fixture_store(tmp_path)
    result = attachment.apply_reattachment(tmp_path, frozen_request(tmp_path))
    supervisor = Supervisor(tmp_path, attachment_event_sha256=result["event_sha256"])
    with supervisor.session() as session:
        original = research.with_suffix(".old")
        research.rename(original)
        research.write_bytes(original.read_bytes())
        research.chmod(0o600)
        with pytest.raises(AccessError, match="wrong_store"):
            session.check()


@pytest.mark.parametrize("attribute", ["synthetic", "legacy_unknown"])
def test_attachment_never_admits_synthetic_or_reconciled_authority(tmp_path, attribute):
    control, _ = fixture_store(tmp_path)
    _change_configuration(control, attribute, "True" if attribute == "synthetic" else "False")
    with pytest.raises(AccessError, match="wrong_store"):
        frozen_request(tmp_path)


def test_forked_process_cannot_inherit_pinned_supervisor_or_active_session(tmp_path):
    fixture_store(tmp_path)
    result = attachment.apply_reattachment(tmp_path, frozen_request(tmp_path))
    code = '''
import os,sys
from pathlib import Path
from quanto.evaluation_registry import Supervisor,AccessError,current_session
root=Path(sys.argv[1])
s=Supervisor(root,attachment_event_sha256=sys.argv[2])
with s.session():
    pid=os.fork()
    if pid==0:
        for action in (lambda:current_session(root),s.issue_principal,s.overview):
            try: action()
            except AccessError as exc:
                if exc.reason!="authority_closed": os._exit(8)
            else: os._exit(9)
        os._exit(0)
    _,status=os.waitpid(pid,0)
    assert os.waitstatus_to_exitcode(status)==0
    s.issue_principal()
'''
    completed = run_python(code, tmp_path, result["event_sha256"])
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize("extra", ["audit", "principal"])
def test_unexpected_append_side_effect_rolls_back_whole_operation(tmp_path, monkeypatch, extra):
    control, research = fixture_store(tmp_path)
    request = frozen_request(tmp_path)
    before = rows(control), rows(research)
    original = Supervisor._event
    def side_effect(db, kind, payload):
        original(db, kind, payload)
        if extra == "audit":
            original(db, "invented_extra_event", {})
        else:
            db.execute("INSERT INTO principals VALUES ('invented_extra_principal','fixture')")
    monkeypatch.setattr(Supervisor, "_event", staticmethod(side_effect))
    with pytest.raises(AccessError, match="state_mismatch"):
        attachment.apply_reattachment(tmp_path, request)
    assert (rows(control), rows(research)) == before

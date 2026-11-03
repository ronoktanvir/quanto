"""Synthetic D008 cooperative boundary tests; no market/model/network access."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import sqlite3
import threading

import pytest
from access_fixtures import synthetic_access as synthetic_access


from quanto.ledger import StaleLease
from quanto.provenance import Provenance
from quanto.research_workflow import ResearchWorkflow, ROLES, WorkflowError

pytestmark = pytest.mark.usefixtures("synthetic_access")


class Clock:
    def __init__(self):
        self.now = datetime(2026, 11, 2, tzinfo=timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


def manifest(store, **changes):
    value = {
        "run_key": "synthetic-workflow-1", "access_class": "sanitized_development",
        "evidence_kind": "synthetic_fixture", "code_sha256": "a" * 64,
        "specification_sha256": "b" * 64,
        "input_refs": [store.put_json({"fixture": "development methods only"})],
        "roles": {role: {
            "policy_version": "development.v1", "backend": "synthetic",
            "requested_model": "synthetic-test", "prompt_sha256": "c" * 64,
            "context_schema": "research_context.v1", "output_schema": "research_handoff.v1",
            "max_steps": 8, "max_seconds": 600, "max_input_bytes": 65_536,
            "max_output_bytes": 65_536, "max_spend_micro_usd": 0, "max_claims": 3,
        } for role in ROLES},
    }
    value.update(changes)
    return value


def intent(request="request-1", action="inspect_development", refs=None):
    return {"request_id": request, "action": action, "input_refs": refs or []}


def handoff(refs, *, reviewed=None, blocked=False, objections=None):
    return {"state": "blocked" if blocked else "complete", "artifact_refs": refs,
            "reviewed_refs": reviewed or [], "assumptions": ["synthetic software check"],
            "objections": objections or [], "next_action": "stop" if blocked else "proceed"}


def setup(store, clock=None, **manifest_changes):
    workflow = ResearchWorkflow(store, clock=clock)
    frozen = manifest(store, **manifest_changes)
    run_id = workflow.create_run(frozen)
    assignment = workflow.issue_stage(run_id, "director")
    return workflow, frozen, run_id, assignment


def complete_effect(workflow, store, assignment, fence=1, *, request="request-1", action="inspect_development"):
    token = assignment["token"]
    output = store.put_json({"result": "synthetic", "role": assignment["role"]})
    workflow.authorize_intent(token, "worker-1", fence, intent(request, action, assignment["input_refs"]))
    workflow.start_intent(token, "worker-1", fence, request)
    workflow.finish_intent(token, "worker-1", fence, request, status="success", artifact_refs=[output])
    return output


def test_seven_roles_are_distinct_exact_and_handoffs_are_bound(tmp_path):
    with Provenance(tmp_path) as store:
        workflow = ResearchWorkflow(store)
        frozen = manifest(store)
        run_id = workflow.create_run(frozen)
        assert workflow.create_run(deepcopy(frozen)) == run_id
        with pytest.raises(WorkflowError, match="Upstream"):
            workflow.issue_stage(run_id, "quality")
        actors, handoffs = set(), []
        for role in ROLES:
            assignment = workflow.issue_stage(run_id, role)
            assert assignment["role"] == role
            assert assignment["upstream_handoffs"] == handoffs
            assert not actors.intersection({assignment["actor_id"]})
            actors.add(assignment["actor_id"])
            assert workflow.authenticate_capability(assignment["token"])["actor_id"] == assignment["actor_id"]
            assert workflow.claim_stage(assignment["token"], "worker-1")["fence"] == 1
            output = complete_effect(workflow, store, assignment)
            review_refs = assignment["input_refs"] if role in ROLES[3:] else []
            result = workflow.finish_handoff(assignment["token"], "worker-1", 1,
                                              handoff([output], reviewed=review_refs))
            assert store.read_json(result["handoff_sha256"]) == result["document"]
            assert result["document"]["actor_id"] == assignment["actor_id"]
            handoffs.append(result["handoff_sha256"])
        status = workflow.read_status(run_id)
        assert status["state"] == "complete"
        assert len(actors) == 7
        assert [s["role"] for s in status["stages"]] == list(ROLES)
        assert store.journal.verify_events()["count"] >= 43


def test_tokens_are_one_use_issued_hashed_and_not_in_status_or_events(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, _, run_id, a = setup(store)
        digest = hashlib.sha256(a["token"].encode()).hexdigest()
        assert store.journal.connection.execute("SELECT token_hash FROM workflow_assignments").fetchone()[0] == digest
        with pytest.raises(WorkflowError, match="once"):
            workflow.issue_stage(run_id, "director")
        for bad in (None, "", "sk-ant-synthetic-sensitive-value", "z" * 43):
            with pytest.raises(WorkflowError):
                workflow.authenticate_capability(bad)
        assert a["token"] not in json.dumps(workflow.read_status(run_id))
        assert digest not in json.dumps(workflow.read_status(run_id))
        events = "".join(r[0] for r in store.journal.connection.execute("SELECT payload FROM events"))
        assert a["token"] not in events and digest not in events
    assert a["token"].encode() not in (tmp_path / "runtime/research.sqlite").read_bytes()


@pytest.mark.parametrize("change", [
    {"access_class": "protected"}, {"evidence_kind": "live_execution"},
    {"path": "/private/data"}, {"roles": {}}, {"input_refs": ["../../private"]},
    {"input_refs": ["a" * 64]}, {"run_key": "api_key=secret"},
])
def test_manifest_rejects_unknown_fields_protected_data_and_missing_refs(tmp_path, change):
    with Provenance(tmp_path) as store:
        workflow = ResearchWorkflow(store)
        with pytest.raises(WorkflowError):
            workflow.create_run(manifest(store, **change))
        assert store.journal.connection.execute("SELECT COUNT(*) FROM workflow_runs").fetchone()[0] == 0


def test_changed_manifest_same_key_refuses_and_bad_contracts_fail_closed(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, frozen, _, _ = setup(store)
        changed = deepcopy(frozen)
        changed["specification_sha256"] = "d" * 64
        with pytest.raises(WorkflowError, match="idempotency"):
            workflow.create_run(changed)
        for field, bad in (("max_steps", True), ("max_claims", 4), ("backend", "shell"),
                           ("output_schema", "arbitrary"), ("max_spend_micro_usd", 1)):
            changed = deepcopy(frozen)
            changed["roles"]["engineer"][field] = bad
            with pytest.raises(WorkflowError):
                workflow.create_run(changed)


def test_concurrent_claim_is_single_and_expired_claim_fences_every_boundary(tmp_path):
    clock = Clock()
    with Provenance(tmp_path) as store:
        workflow, _, run_id, a = setup(store, clock)
    barrier = threading.Barrier(2)

    def claim(worker):
        with Provenance(tmp_path) as store:
            workflow = ResearchWorkflow(store, clock=clock)
            barrier.wait()
            return workflow.claim_stage(a["token"], worker, lease_seconds=10)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(claim, worker) for worker in ("worker-a", "worker-b")]
        claims = [future.result() for future in futures]
    winner = next(c for c in claims if c)
    assert sum(c is not None for c in claims) == 1
    with Provenance(tmp_path) as store:
        workflow = ResearchWorkflow(store, clock=clock)
        workflow.authorize_intent(a["token"], winner["worker_id"], 1, intent())
        clock.advance(11)
        assert workflow.recover_expired(run_id) == 1
        new = workflow.claim_stage(a["token"], "worker-1")
        assert new["fence"] == 2
        checks = [
            lambda: workflow.authorize_intent(a["token"], winner["worker_id"], 1, intent("other")),
            lambda: workflow.start_intent(a["token"], winner["worker_id"], 1, "request-1"),
            lambda: workflow.finish_intent(a["token"], winner["worker_id"], 1, "request-1", status="success", artifact_refs=[]),
            lambda: workflow.finish_handoff(a["token"], winner["worker_id"], 1, handoff([])),
        ]
        for check in checks:
            with pytest.raises(StaleLease):
                check()
        with pytest.raises(WorkflowError, match="earlier fence"):
            workflow.authorize_intent(a["token"], "worker-1", 2, intent())
        result = complete_effect(workflow, store, a, 2, request="new-incarnation")
        workflow.finish_handoff(a["token"], "worker-1", 2, handoff([result]))
        assert len(workflow.read_status(run_id)["stages"][0]["intents"]) == 2


def test_intent_schema_role_input_bounds_and_durable_secret_free_denials(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, _, _, a = setup(store)
        workflow.claim_stage(a["token"], "worker-1")
        other = store.put_json({"unissued": "safe"})
        proposals = [
            {**intent(), "actor_id": a["actor_id"]}, {**intent(), "path": "/etc/passwd"},
            intent(action="protected_evaluate"), intent(action="broker_order"),
            intent(action="launch_development"), intent(refs=[other]),
            intent(refs=["/etc/passwd"]), intent(request="sk-ant-synthetic-secret-value"),
        ]
        for proposal in proposals:
            with pytest.raises(WorkflowError):
                workflow.authorize_intent(a["token"], "worker-1", 1, proposal)
        count = store.journal.connection.execute("SELECT COUNT(*) FROM events WHERE kind='workflow_denied'").fetchone()[0]
        assert count == len(proposals)
        raw = "".join(r[0] for r in store.journal.connection.execute("SELECT payload FROM events"))
        assert "/etc/passwd" not in raw and "sk-ant-synthetic-secret-value" not in raw


def test_intent_idempotency_and_effect_start_cannot_repeat(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, _, _, a = setup(store)
        workflow.claim_stage(a["token"], "worker-1")
        first = workflow.authorize_intent(a["token"], "worker-1", 1, intent())
        assert workflow.authorize_intent(a["token"], "worker-1", 1, intent()) == first
        with pytest.raises(WorkflowError, match="changed"):
            workflow.authorize_intent(a["token"], "worker-1", 1, intent(action="query_failures"))
        workflow.start_intent(a["token"], "worker-1", 1, "request-1")
        with pytest.raises(WorkflowError, match="consumed"):
            workflow.start_intent(a["token"], "worker-1", 1, "request-1")
        output = store.put_json({"result": "fixture"})
        workflow.finish_intent(a["token"], "worker-1", 1, "request-1", status="success", artifact_refs=[output])
        with pytest.raises(WorkflowError, match="terminal"):
            workflow.finish_intent(a["token"], "worker-1", 1, "request-1", status="success", artifact_refs=[output])


@pytest.mark.parametrize("start", [False, True])
def test_crash_reopen_before_or_after_effect_preserves_uncertainty(tmp_path, start):
    clock = Clock()
    with Provenance(tmp_path) as store:
        workflow, _, run_id, a = setup(store, clock)
        workflow.claim_stage(a["token"], "worker-1", lease_seconds=5)
        workflow.authorize_intent(a["token"], "worker-1", 1, intent())
        if start:
            workflow.start_intent(a["token"], "worker-1", 1, "request-1")
    clock.advance(6)
    with Provenance(tmp_path) as store:
        workflow = ResearchWorkflow(store, clock=clock)
        assert workflow.recover_expired(run_id) == 1
        assert workflow.recover_expired(run_id) == 0
        stage = workflow.read_status(run_id)["stages"][0]
        assert stage["state"] == ("uncertain" if start else "pending")
        if start:
            with pytest.raises(WorkflowError, match="terminal"):
                workflow.claim_stage(a["token"], "worker-1")
            assert stage["claims"] == 1
        else:
            assert workflow.claim_stage(a["token"], "worker-1")["fence"] == 2


@pytest.mark.parametrize("start", [False, True])
def test_cancellation_revokes_all_future_effects_and_publication(tmp_path, start):
    with Provenance(tmp_path) as store:
        workflow, _, run_id, a = setup(store)
        workflow.claim_stage(a["token"], "worker-1")
        workflow.authorize_intent(a["token"], "worker-1", 1, intent())
        if start:
            workflow.start_intent(a["token"], "worker-1", 1, "request-1")
        workflow.cancel_run(run_id)
        workflow.cancel_run(run_id)
        assert workflow.read_status(run_id)["stages"][0]["state"] == ("uncertain" if start else "cancelled")
        operations = [lambda: workflow.claim_stage(a["token"], "worker-1"),
                      lambda: workflow.authorize_intent(a["token"], "worker-1", 1, intent("new")),
                      lambda: workflow.start_intent(a["token"], "worker-1", 1, "request-1"),
                      lambda: workflow.finish_intent(a["token"], "worker-1", 1, "request-1", status="success", artifact_refs=[]),
                      lambda: workflow.finish_handoff(a["token"], "worker-1", 1, handoff([]))]
        for operation in operations:
            with pytest.raises(WorkflowError, match="cancelled"):
                operation()


def test_handoff_requires_exact_complete_verified_results_and_issued_authorship(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, _, _, a = setup(store)
        workflow.claim_stage(a["token"], "worker-1")
        output = complete_effect(workflow, store, a)
        extra = store.put_json({"unbound": "artifact"})
        for bad in (handoff([extra]), handoff([output, extra]),
                    {**handoff([output]), "actor_id": "forged"},
                    handoff([output], objections=[{"code": "issue", "artifact_refs": [extra]}])):
            with pytest.raises(WorkflowError):
                workflow.finish_handoff(a["token"], "worker-1", 1, bad)
        (tmp_path / "data/objects" / (output + ".bin")).write_bytes(b'{"altered":true}')
        with pytest.raises(WorkflowError, match="unavailable"):
            workflow.finish_handoff(a["token"], "worker-1", 1, handoff([output]))
        assert store.journal.connection.execute("SELECT COUNT(*) FROM workflow_handoffs").fetchone()[0] == 0


def test_handoff_publication_and_terminal_job_event_are_atomic_on_failure(tmp_path, monkeypatch):
    with Provenance(tmp_path) as store:
        workflow, _, run_id, a = setup(store)
        workflow.claim_stage(a["token"], "worker-1")
        output = complete_effect(workflow, store, a)
        original = workflow._event

        def fail(kind, payload, now):
            if kind == "handoff_committed":
                raise RuntimeError("synthetic crash before transaction commit")
            return original(kind, payload, now)

        monkeypatch.setattr(workflow, "_event", fail)
        with pytest.raises(RuntimeError):
            workflow.finish_handoff(a["token"], "worker-1", 1, handoff([output]))
        assert workflow.read_status(run_id)["stages"][0]["state"] == "leased"
        assert store.journal.connection.execute("SELECT COUNT(*) FROM workflow_handoffs").fetchone()[0] == 0
        assert store.journal.connection.execute("SELECT COUNT(*) FROM workflow_terminals").fetchone()[0] == 0
        monkeypatch.setattr(workflow, "_event", original)
        workflow.finish_handoff(a["token"], "worker-1", 1, handoff([output]))
        with pytest.raises(WorkflowError, match="terminal"):
            workflow.finish_handoff(a["token"], "worker-1", 1, handoff([output]))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            store.journal.connection.execute("UPDATE workflow_handoffs SET document='{}'")


def test_secret_pattern_artifacts_are_not_admitted_or_published(tmp_path):
    with Provenance(tmp_path) as store:
        workflow = ResearchWorkflow(store)
        secret = store.put_json({"unsafe": "sk-ant-synthetic-sensitive-value"})
        with pytest.raises(WorkflowError, match="credential"):
            workflow.create_run(manifest(store, input_refs=[secret]))
        json_credential = store.put_json({"api_key": "synthetic-unrecognized-value"})
        with pytest.raises(WorkflowError, match="credential"):
            workflow.create_run(manifest(store, input_refs=[json_credential]))
        workflow, _, _, a = setup(store)
        workflow.claim_stage(a["token"], "worker-1")
        workflow.authorize_intent(a["token"], "worker-1", 1, intent())
        workflow.start_intent(a["token"], "worker-1", 1, "request-1")
        with pytest.raises(WorkflowError, match="credential"):
            workflow.finish_intent(a["token"], "worker-1", 1, "request-1", status="success", artifact_refs=[secret])


def test_wrong_responding_model_is_retained_as_invalid_no_retry(tmp_path):
    with Provenance(tmp_path) as store:
        frozen = manifest(store)
        frozen["roles"]["director"].update(backend="anthropic_text", requested_model="claude-haiku-5-5", max_spend_micro_usd=1000)
        workflow = ResearchWorkflow(store)
        run_id = workflow.create_run(frozen)
        a = workflow.issue_stage(run_id, "director")
        workflow.claim_stage(a["token"], "worker-1")
        workflow.authorize_intent(a["token"], "worker-1", 1, intent(action="dispatch_model"))
        workflow.start_intent(a["token"], "worker-1", 1, "request-1")
        workflow.finish_intent(a["token"], "worker-1", 1, "request-1", status="success",
                               artifact_refs=[store.put_json({"response": "wrong model"})], observed_model="unexpected-model")
        assert workflow.read_status(run_id)["stages"][0]["state"] == "invalid"
        with pytest.raises(WorkflowError, match="terminal"):
            workflow.authorize_intent(a["token"], "worker-1", 1, intent("retry", "dispatch_model"))


def test_claim_step_and_time_bounds_are_durable(tmp_path):
    clock = Clock()
    with Provenance(tmp_path) as store:
        frozen = manifest(store)
        frozen["roles"]["director"].update(max_steps=1, max_seconds=20, max_claims=2)
        workflow = ResearchWorkflow(store, clock=clock)
        run_id = workflow.create_run(frozen)
        a = workflow.issue_stage(run_id, "director")
        workflow.claim_stage(a["token"], "worker-1", lease_seconds=5)
        workflow.authorize_intent(a["token"], "worker-1", 1, intent())
        with pytest.raises(WorkflowError, match="step"):
            workflow.authorize_intent(a["token"], "worker-1", 1, intent("second"))
        clock.advance(6)
        assert workflow.claim_stage(a["token"], "worker-1", lease_seconds=5)["fence"] == 2
        clock.advance(6)
        assert workflow.claim_stage(a["token"], "worker-1") is None
        assert workflow.read_status(run_id)["stages"][0]["state"] == "failed"


def test_direct_reclaim_after_dispatch_does_not_roll_back_uncertain_marker(tmp_path):
    clock = Clock()
    with Provenance(tmp_path) as store:
        workflow, _, run_id, a = setup(store, clock)
        workflow.claim_stage(a["token"], "worker-1", lease_seconds=1)
        workflow.authorize_intent(a["token"], "worker-1", 1, intent())
        workflow.start_intent(a["token"], "worker-1", 1, "request-1")
        clock.advance(2)
        assert workflow.claim_stage(a["token"], "worker-2") is None
        assert workflow.read_status(run_id)["stages"][0]["state"] == "uncertain"


def test_raw_issued_token_embedded_in_worker_request_or_artifact_is_never_persisted(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, _, _, a = setup(store)
        token = a["token"]
        with pytest.raises(WorkflowError, match="capability secret"):
            workflow.claim_stage(token, "worker-" + token)
        workflow.claim_stage(token, "worker-1")
        with pytest.raises(WorkflowError, match="capability secret"):
            workflow.authorize_intent(token, "worker-1", 1, intent("request-" + token))
        output = complete_effect(workflow, store, a)
        leaked = handoff([output])
        leaked["assumptions"] = ["embedded:" + token + ":suffix"]
        with pytest.raises(WorkflowError, match="capability secret"):
            workflow.finish_handoff(token, "worker-1", 1, leaked)
        workflow.authorize_intent(token, "worker-1", 1, intent("artifact-probe"))
        workflow.start_intent(token, "worker-1", 1, "artifact-probe")
        secret_ref = store.put_json({"summary": "prefix-" + token + "-suffix"})
        with pytest.raises(WorkflowError, match="capability secret"):
            workflow.finish_intent(token, "worker-1", 1, "artifact-probe",
                                   status="success", artifact_refs=[secret_ref])
        # A second run also cannot write the first run's capability into its manifest.
        second = manifest(store, run_key="run-" + token)
        with pytest.raises(WorkflowError, match="capability secret"):
            workflow.create_run(second)
        rows = store.journal.connection.execute("SELECT payload FROM events").fetchall()
        assert all(token not in row[0] for row in rows)
    assert token.encode() not in (tmp_path / "runtime/research.sqlite").read_bytes()


def test_all_rejected_worker_transitions_record_only_sanitized_operation(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, _, _, a = setup(store)
        workflow.claim_stage(a["token"], "worker-1")
        before = store.journal.connection.execute("SELECT COUNT(*) FROM events WHERE kind='workflow_denied'").fetchone()[0]
        for operation in (
            lambda: workflow.start_intent(a["token"], "worker-1", 1, "never-authorized"),
            lambda: workflow.finish_handoff(a["token"], "worker-1", 1, {"bad": "schema"}),
            lambda: workflow.finish_intent(a["token"], "worker-1", 1, "never-authorized", status="invalid", artifact_refs=[]),
            lambda: workflow.authenticate_capability("not-an-issued-token"),
        ):
            with pytest.raises(WorkflowError):
                operation()
        denials = [json.loads(row[0]) for row in store.journal.connection.execute(
            "SELECT payload FROM events WHERE kind='workflow_denied' ORDER BY id")][before:]
        assert denials == [{"operation": op} for op in (
            "start_intent", "finish_handoff", "finish_intent", "authenticate_capability")]


def test_long_handoff_cannot_commit_after_lease_expires_during_artifact_publication(tmp_path, monkeypatch):
    clock = Clock()
    with Provenance(tmp_path) as store:
        workflow, _, run_id, a = setup(store, clock)
        workflow.claim_stage(a["token"], "worker-1", lease_seconds=10)
        output = complete_effect(workflow, store, a)
        original = store.put_json

        def delayed(value):
            digest = original(value)
            clock.advance(11)
            return digest

        monkeypatch.setattr(store, "put_json", delayed)
        with pytest.raises(StaleLease):
            workflow.finish_handoff(a["token"], "worker-1", 1, handoff([output]))
        assert workflow.read_status(run_id)["stages"][0]["handoff_sha256"] is None
        workflow.recover_expired(run_id)
        assert workflow.read_status(run_id)["state"] == "uncertain"


def test_cancellation_racing_effect_start_has_one_serialized_outcome(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, _, run_id, a = setup(store)
        workflow.claim_stage(a["token"], "worker-1")
        workflow.authorize_intent(a["token"], "worker-1", 1, intent())
    barrier = threading.Barrier(2)

    def operation(cancel):
        with Provenance(tmp_path) as store:
            workflow = ResearchWorkflow(store)
            barrier.wait()
            if cancel:
                workflow.cancel_run(run_id)
                return "cancelled"
            try:
                workflow.start_intent(a["token"], "worker-1", 1, "request-1")
                return "started"
            except WorkflowError:
                return "refused"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(operation, cancel) for cancel in (True, False)]
        results = [f.result() for f in futures]
    with Provenance(tmp_path) as store:
        workflow = ResearchWorkflow(store)
        state = workflow.read_status(run_id)["stages"][0]["state"]
        assert state == ("uncertain" if "started" in results else "cancelled")
        kinds = [row[0] for row in store.journal.connection.execute("SELECT kind FROM events ORDER BY id")]
        if "workflow_effect_started" in kinds:
            assert kinds.index("workflow_effect_started") < kinds.index("workflow_run_cancelled")

"""D008 research transport uses synthetic envelopes only; no paid calls or keys."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import threading

import pytest
from access_fixtures import synthetic_access as synthetic_access


from quanto import provider
from quanto.ledger import Journal, LedgerError, hash_bytes
from quanto.provenance import Provenance
from quanto.research_dispatch import ResearchDispatcher, _BorrowedAtomicJournal
from quanto.research_packets import PREDICATES, SYSTEM_PROMPT
from quanto.research_workflow import ResearchWorkflow, ROLES, WorkflowError

pytestmark = pytest.mark.usefixtures("synthetic_access")


class Clock:
    def __init__(self):
        self.now = datetime(2026, 11, 2, tzinfo=timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


def context():
    return {"schema_version": 1, "kind": "research_role_context", "role": "director",
            "objective": "frozen_suite_falsification", "evidence_kind": "synthetic_fixture",
            "access_class": "sanitized_development", "data_values_disclosed": False,
            "method": "frozen_next_open_three_cost_development_suite",
            "suite_integrity": "verified_roster_and_current_specification",
            "scope": "development_only",
            "allowed_predicates": sorted(PREDICATES), "artifact_aliases": ["artifact-1"],
            "failures": [], "prior_outputs": [], "execution_state": "not_requested"}


def response(**changes):
    output = {"schema_version": 1, "role": "director", "decision": "proceed", "predicate": None,
              "artifact_aliases": ["artifact-1"],
              "findings": [{"code": "hidden_values_unreviewed", "artifact_aliases": ["artifact-1"]}],
              "rationale": "Synthetic private reasoning; not inspected historical values."}
    value = {"type": "message", "id": "synthetic-provider-request", "model": provider.HAIKU,
             "content": [{"type": "text", "text": json.dumps(output)}],
             "usage": {"input_tokens": 100, "output_tokens": 100}, "stop_reason": "end_turn"}
    value.update(changes)
    return value


@pytest.fixture(autouse=True)
def no_credentials(monkeypatch):
    monkeypatch.setattr(provider, "local_key", lambda _: pytest.fail("Synthetic transport read a key"))
    monkeypatch.setattr(provider, "PRICE_VERIFIED_ON", datetime.now(timezone.utc).date().isoformat())


def setup(store, *, clock=None, run_key="synthetic-dispatch", allowance=4_000_000,
          model=provider.HAIKU, **bounds):
    workflow = ResearchWorkflow(store, clock=clock or Clock())
    contract = {"policy_version": "development.v1", "backend": "anthropic_text",
                "requested_model": model, "prompt_sha256": hash_bytes(SYSTEM_PROMPT.encode()),
                "context_schema": "research_context.v1", "output_schema": "research_handoff.v1",
                "max_steps": 8, "max_seconds": 600, "max_input_bytes": 65_536,
                "max_output_bytes": 16_384, "max_spend_micro_usd": allowance, "max_claims": 3}
    contract.update(bounds)
    manifest = {"run_key": run_key, "access_class": "sanitized_development",
                "evidence_kind": "synthetic_fixture", "code_sha256": "a" * 64,
                "specification_sha256": "b" * 64,
                "input_refs": [store.put_json({"fixture": "method-only"})],
                "roles": {role: dict(contract) for role in ROLES}}
    run_id = workflow.create_run(manifest)
    assignment = workflow.issue_stage(run_id, "director")
    claim = workflow.claim_stage(assignment["token"], "worker", lease_seconds=60)
    return workflow, ResearchDispatcher(workflow), run_id, assignment, claim["fence"]


def dispatch(dispatcher, assignment, fence=1, request="request-1", transport=None, packet=None):
    return dispatcher.dispatch(assignment["token"], "worker", fence, request,
                               context() if packet is None else packet,
                               transport=transport or (lambda *_: response()))


def reservation(workflow):
    return workflow.db.execute("SELECT * FROM reservations WHERE request_id='request-1'").fetchone()


def test_atomic_authorization_and_safe_projection_private_response_separation(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, assignment, fence = setup(store)

        def transport(body, key):
            assert key == "synthetic-fixture-key"
            assert not workflow.db.in_transaction
            with Journal(tmp_path / "runtime/research.sqlite", clock=workflow.journal.clock) as journal:
                assert journal.connection.execute("SELECT COUNT(*) FROM dispatches").fetchone()[0] == 1
                assert journal.connection.execute("SELECT COUNT(*) FROM workflow_effect_starts").fetchone()[0] == 1
                assert journal.connection.execute("SELECT COUNT(*) FROM research_dispatch_holds").fetchone()[0] == 1
                assert journal.budget_snapshot()["committed_micro_usd"] > 60_000
            assert json.loads(body)["system"] == SYSTEM_PROMPT
            return response()

        result = dispatch(dispatcher, assignment, fence, transport=transport)
        assert result["receipt"]["transport_kind"] == "synthetic_fixture"
        assert result["receipt"]["actual_model_evidence"] is False
        assert "rationale" not in result["projection"]
        assert result["private_response"]["reply"] == response()["content"][0]["text"]
        assert "response_sha256" not in result["receipt"]
        assert "body_sha256" not in result["receipt"]
        raw = store.read_json(workflow.db.execute("SELECT artifact_sha256 FROM research_private_responses").fetchone()[0])
        assert raw == result["private_response"]
        assert reservation(workflow)["state"] == "settled"
        assert reservation(workflow)["actual_micro_usd"] == 300
        refs = json.loads(workflow.db.execute("SELECT artifact_refs FROM workflow_effect_outcomes").fetchone()[0])
        assert sorted(refs) == result["artifact_refs"]
        for ref in refs:
            artifact = store.read_json(ref)
            assert "rationale" not in artifact and "reply" not in artifact
        assert workflow.journal.verify_events()["count"] > 5


def test_duplicate_id_never_sends_twice_even_after_success(tmp_path):
    with Provenance(tmp_path) as store:
        _, dispatcher, _, a, _ = setup(store)
        dispatch(dispatcher, a)
        with pytest.raises(WorkflowError, match="replay"):
            dispatch(dispatcher, a, transport=lambda *_: pytest.fail("Duplicate network send"))


def test_role_allowance_is_aggregate_full_holds_even_after_cheaper_settlement(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store, allowance=100_000)
        first = dispatch(dispatcher, a)
        assert first["receipt"]["reserved_micro_usd"] < 100_000
        with pytest.raises(WorkflowError, match="Aggregate role"):
            dispatch(dispatcher, a, request="request-2", transport=lambda *_: pytest.fail("Must not send"))
        assert workflow.db.execute("SELECT COUNT(*) FROM research_dispatch_holds").fetchone()[0] == 1


def test_zero_role_allowance_rejects_before_reservation(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store, allowance=0)
        with pytest.raises(WorkflowError, match="allowance"):
            dispatch(dispatcher, a)
        assert workflow.db.execute("SELECT COUNT(*) FROM reservations").fetchone()[0] == 0


def test_research_purpose_hold_never_recycles_actual_cost(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store)
        workflow.db.execute("INSERT INTO provider_allocations VALUES (?,?,?,?)",
                            ("prior", "2026-11-01", "research", 3_900_000))
        dispatch(dispatcher, a)
        with pytest.raises(WorkflowError, match="research purpose"):
            dispatch(dispatcher, a, request="request-2")
        assert workflow.db.execute("SELECT COUNT(*) FROM reservations").fetchone()[0] == 1


def test_global_budget_failure_rolls_back_role_and_purpose_and_effect_start(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store)
        workflow.journal.reserve("other-client", 19_990_000)
        with pytest.raises(LedgerError, match="budget"):
            dispatch(dispatcher, a)
        for table in ("research_dispatch_holds", "provider_allocations", "workflow_effect_starts", "dispatches"):
            assert workflow.db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] == 0


def test_concurrent_reservations_cannot_overspend_shared_global_budget(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, _, _, a, _ = setup(store, run_key="first")
        _, _, _, b, _ = setup(store, run_key="second")
        workflow.journal.reserve("other-client", 19_900_000)
    entered, release = threading.Event(), threading.Event()

    def run(assignment, request, blocked=False):
        with Provenance(tmp_path) as store:
            workflow = ResearchWorkflow(store, clock=Clock())
            dispatcher = ResearchDispatcher(workflow)

            def transport(*_):
                entered.set()
                if blocked:
                    assert release.wait(5)
                return response()

            return dispatch(dispatcher, assignment, request=request, transport=transport)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(run, a, "first", True)
        try:
            assert entered.wait(5)
            second = pool.submit(run, b, "second")
            with pytest.raises(LedgerError, match="budget"):
                second.result(5)
        finally:
            release.set()
        assert first.result(5)["receipt"]["terminal"] == "completed"


def test_crash_after_atomic_authorization_keeps_all_entitlements_consumed(tmp_path, monkeypatch):
    with Provenance(tmp_path) as store:
        workflow, dispatcher, run_id, a, _ = setup(store)

        def crash(*args, **kwargs):
            raise KeyboardInterrupt("Synthetic process death")

        monkeypatch.setattr(provider, "send_research_text", crash)
        with pytest.raises(KeyboardInterrupt):
            dispatch(dispatcher, a)
        assert reservation(workflow)["state"] == "reserved"
        assert workflow.db.execute("SELECT COUNT(*) FROM dispatches").fetchone()[0] == 1
        assert workflow.db.execute("SELECT COUNT(*) FROM workflow_effect_starts").fetchone()[0] == 1
        with pytest.raises(WorkflowError, match="replay"):
            dispatch(dispatcher, a)
        workflow.journal.clock.advance(61)
        workflow.recover_expired(run_id)
        assert workflow.read_status(run_id)["stages"][0]["state"] == "uncertain"


@pytest.mark.parametrize("interruption", ["cancel", "expire", "pause", "midnight"])
def test_fence_is_rechecked_immediately_before_actual_send(tmp_path, monkeypatch, interruption):
    clock = Clock()
    with Provenance(tmp_path) as store:
        workflow, dispatcher, run_id, a, _ = setup(store, clock=clock)
        original = provider.send_research_text

        def interrupt(*args, **kwargs):
            if interruption == "cancel":
                workflow.cancel_run(run_id)
            elif interruption == "expire":
                clock.advance(61)
            elif interruption == "pause":
                (tmp_path / "runtime/model_calls_paused").touch()
            else:
                clock.advance(24 * 3600)
            return original(*args, **kwargs)

        monkeypatch.setattr(provider, "send_research_text", interrupt)
        with pytest.raises(WorkflowError, match="full hold"):
            dispatch(dispatcher, a, transport=lambda *_: pytest.fail("Stale or cancelled send"))
        assert reservation(workflow)["state"] == "uncertain"
        assert not workflow.db.execute("SELECT 1 FROM workflow_effect_outcomes WHERE status='success'").fetchone()


@pytest.mark.parametrize("interruption", ["cancel", "expire"])
def test_lost_lease_during_network_cannot_publish_or_settle(tmp_path, interruption):
    clock = Clock()
    with Provenance(tmp_path) as store:
        workflow, dispatcher, run_id, a, _ = setup(store, clock=clock)

        def transport(*_):
            if interruption == "cancel":
                workflow.cancel_run(run_id)
            else:
                clock.advance(61)
            return response()

        with pytest.raises(WorkflowError, match="full hold"):
            dispatch(dispatcher, a, transport=transport)
        assert reservation(workflow)["state"] == "uncertain"
        assert reservation(workflow)["actual_micro_usd"] is None
        assert workflow.db.execute("SELECT COUNT(*) FROM research_private_responses").fetchone()[0] == 1
        assert not workflow.db.execute("SELECT 1 FROM workflow_effect_outcomes WHERE status='success'").fetchone()


@pytest.mark.parametrize("change", [
    {"model": provider.OPUS}, {"stop_reason": "max_tokens"}, {"usage": {}},
    {"usage": {"input_tokens": 100, "output_tokens": 2049}},
    {"usage": {"input_tokens": 100_000, "output_tokens": 1}},
    {"content": [{"type": "tool_use", "name": "forbidden"}]},
    {"content": [{"type": "text", "text": "not a typed role output"}]},
    {"content": [{"type": "text", "text": "x" * 20_000}]},
])
def test_invalid_provider_envelopes_keep_full_hold_and_exact_model_observation(tmp_path, change):
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store)
        with pytest.raises(WorkflowError, match="full hold"):
            dispatch(dispatcher, a, transport=lambda *_: response(**change))
        assert reservation(workflow)["state"] == "uncertain"
        assert reservation(workflow)["actual_micro_usd"] is None
        observed = json.loads(workflow.db.execute("SELECT observation FROM research_model_observations").fetchone()[0])
        assert observed["model"] == change.get("model", provider.HAIKU)
        with pytest.raises(WorkflowError):
            dispatch(dispatcher, a, transport=lambda *_: pytest.fail("No retry"))


def test_provider_failure_and_no_automatic_retry(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store)
        sends = []

        def fail(*_):
            sends.append(1)
            raise RuntimeError("Private provider error must not appear in journal")

        with pytest.raises(WorkflowError, match="no automatic replay"):
            dispatch(dispatcher, a, transport=fail)
        with pytest.raises(WorkflowError):
            dispatch(dispatcher, a, transport=fail)
        assert len(sends) == 1 and reservation(workflow)["state"] == "uncertain"
        assert workflow.read_status(a["run_id"])["stages"][0]["state"] == "uncertain"
        events = " ".join(row[0] for row in workflow.db.execute("SELECT payload FROM events"))
        assert "Private provider error" not in events


@pytest.mark.parametrize("bounds", [
    {"max_input_bytes": 100}, {"prompt_sha256": "a" * 64}, {"requested_model": "unknown"},
])
def test_actual_input_and_prompt_model_bounds_precede_holds(tmp_path, bounds):
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store, **bounds)
        with pytest.raises(LedgerError):
            dispatch(dispatcher, a)
        assert workflow.db.execute("SELECT COUNT(*) FROM reservations").fetchone()[0] == 0


def test_arbitrary_messages_or_data_bearing_context_refuses_before_holds(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store)
        packet = context()
        packet["prices"] = [1, 2, 3]
        with pytest.raises(LedgerError):
            dispatch(dispatcher, a, packet=packet)
        assert workflow.db.execute("SELECT COUNT(*) FROM reservations").fetchone()[0] == 0


def test_borrowed_journal_runs_original_validation_and_cannot_commit_outer_transaction(tmp_path):
    with Journal(tmp_path / "journal.sqlite", clock=Clock()) as journal:
        atomic = _BorrowedAtomicJournal(journal)
        with pytest.raises(LedgerError, match="supervisor transaction"):
            atomic.reserve("outside", 1)
        with pytest.raises(RuntimeError):
            with journal._transaction():
                assert atomic.reserve("inside", 123)["created"]
                assert not atomic.reserve("inside", 123)["created"]
                atomic.authorize_dispatch("inside")
                with pytest.raises(LedgerError, match="already authorized"):
                    atomic.authorize_dispatch("inside")
                raise RuntimeError("rollback outer transaction")
        assert journal.connection.execute("SELECT COUNT(*) FROM reservations").fetchone()[0] == 0
        assert journal.connection.execute("SELECT COUNT(*) FROM dispatches").fetchone()[0] == 0
        assert journal.verify_events()["count"] == 0


def test_research_cannot_bypass_workflow_using_conversation_api(tmp_path):
    with pytest.raises(LedgerError, match="ResearchDispatcher"):
        provider.request_text(tmp_path, request_id="bypass", model=provider.HAIKU,
                              system="test", messages=[{"role": "user", "content": "test"}],
                              purpose="research", role="director", transport=lambda *_: response())


def test_successful_tool_projection_is_bound_to_following_model_intent(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store)
        safe_tool_output = store.put_json({"schema": "safe_tool_projection.v1", "code": "fixture_only"})
        workflow.authorize_intent(a["token"], "worker", 1, {
            "request_id": "inspect", "action": "inspect_development", "input_refs": a["input_refs"]})
        workflow.start_intent(a["token"], "worker", 1, "inspect")
        workflow.finish_intent(a["token"], "worker", 1, "inspect", status="success",
                               artifact_refs=[safe_tool_output])
        assert workflow.available_input_refs(a["token"], "worker", 1) == sorted(
            a["input_refs"] + [safe_tool_output])
        dispatch(dispatcher, a)
        refs = json.loads(workflow.db.execute(
            "SELECT input_refs FROM workflow_intents WHERE request_id='request-1'").fetchone()[0])
        assert safe_tool_output in refs


def test_foreign_and_unadmitted_tool_results_are_not_capabilities(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, _, _, a, _ = setup(store)
        unrelated = store.put_json({"foreign": "not issued and never produced"})
        with pytest.raises(WorkflowError, match="not issued"):
            workflow.authorize_intent(a["token"], "worker", 1, {
                "request_id": "unissued", "action": "inspect_development", "input_refs": [unrelated]})
        workflow.authorize_intent(a["token"], "worker", 1, {
            "request_id": "failed", "action": "inspect_development", "input_refs": []})
        workflow.start_intent(a["token"], "worker", 1, "failed")
        workflow.finish_intent(a["token"], "worker", 1, "failed", status="failed",
                               artifact_refs=[unrelated])
        assert unrelated not in workflow._available_refs_locked(workflow._assignment(a["token"]), 1)
        with pytest.raises(WorkflowError, match="terminal"):
            workflow.available_input_refs(a["token"], "worker", 1)


def test_derived_tool_inputs_remain_bounded_in_aggregate(tmp_path):
    with Provenance(tmp_path) as store:
        workflow, _, _, a, _ = setup(store, max_input_bytes=40)
        value = store.put_json({"method": "x" * 35})
        workflow.authorize_intent(a["token"], "worker", 1, {
            "request_id": "inspect", "action": "inspect_development", "input_refs": []})
        workflow.start_intent(a["token"], "worker", 1, "inspect")
        workflow.finish_intent(a["token"], "worker", 1, "inspect", status="success", artifact_refs=[value])
        with pytest.raises(WorkflowError, match="byte bound"):
            workflow.available_input_refs(a["token"], "worker", 1)


@pytest.mark.parametrize("interruption", ["stale", "cancelled", "wrong_worker", "wrong_fence"])
def test_inactive_claim_rejects_before_spend_or_effect(tmp_path, interruption):
    clock = Clock()
    with Provenance(tmp_path) as store:
        workflow, dispatcher, run_id, a, _ = setup(store, clock=clock)
        if interruption == "stale":
            clock.advance(61)
        elif interruption == "cancelled":
            workflow.cancel_run(run_id)
        with pytest.raises(LedgerError):
            dispatcher.dispatch(a["token"], "intruder" if interruption == "wrong_worker" else "worker",
                                2 if interruption == "wrong_fence" else 1, "request-1", context(),
                                transport=lambda *_: pytest.fail("Inactive worker sent a request"))
        assert not workflow.db.execute("SELECT 1 FROM reservations").fetchone()
        assert not workflow.db.execute("SELECT 1 FROM workflow_effect_starts").fetchone()


def test_midnight_refuses_current_lease_authorized_under_previous_day(tmp_path, monkeypatch):
    clock = Clock()
    clock.now = datetime(2026, 11, 2, 7, 59, 50, tzinfo=timezone.utc)
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store, clock=clock)
        original = provider.send_research_text

        def cross_midnight(*args, **kwargs):
            clock.advance(11)
            return original(*args, **kwargs)

        monkeypatch.setattr(provider, "send_research_text", cross_midnight)
        with pytest.raises(WorkflowError, match="full hold"):
            dispatch(dispatcher, a, transport=lambda *_: pytest.fail("Reservation crossed midnight"))
        assert reservation(workflow)["day"] == "2026-11-01"
        assert reservation(workflow)["state"] == "uncertain"


def test_lease_expiration_during_local_publication_rolls_back_results_and_settlement(tmp_path, monkeypatch):
    clock = Clock()
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store, clock=clock)
        original = store.put_json

        def slow_write(value):
            digest = original(value)
            if type(value) is dict and value.get("schema") == "research_transport_receipt.v1":
                clock.advance(61)
            return digest

        monkeypatch.setattr(store, "put_json", slow_write)
        with pytest.raises(WorkflowError, match="full hold"):
            dispatch(dispatcher, a)
        assert reservation(workflow)["state"] == "uncertain"
        assert reservation(workflow)["actual_micro_usd"] is None
        assert not workflow.db.execute("SELECT 1 FROM workflow_effect_outcomes WHERE status='success'").fetchone()


@pytest.mark.parametrize("local_step", ["verify_refs", "research_ready"])
@pytest.mark.parametrize("interruption", ["lease_expiry", "midnight"])
def test_slow_final_guard_cannot_send_using_cached_time(tmp_path, monkeypatch, local_step, interruption):
    clock = Clock()
    if interruption == "midnight":
        clock.now = datetime(2026, 11, 2, 7, 59, 50, tzinfo=timezone.utc)
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store, clock=clock)
        original_guard = dispatcher._before_send
        owner, attribute = ((workflow, "_verify_refs") if local_step == "verify_refs"
                            else (provider, "_research_ready"))
        original_step = getattr(owner, attribute)
        sends = []

        def slow_step(*args, **kwargs):
            value = original_step(*args, **kwargs)
            clock.advance(61 if interruption == "lease_expiry" else 11)
            return value

        def delayed_guard(*args, **kwargs):
            # Delay only the final send guard, after atomic authorization.
            with monkeypatch.context() as guarded:
                guarded.setattr(owner, attribute, slow_step)
                return original_guard(*args, **kwargs)

        def transport(*_):
            sends.append(1)
            return response()

        monkeypatch.setattr(dispatcher, "_before_send", delayed_guard)
        with pytest.raises(WorkflowError, match="full hold"):
            dispatch(dispatcher, a, transport=transport)
        assert sends == []
        assert reservation(workflow)["state"] == "uncertain"
        assert reservation(workflow)["actual_micro_usd"] is None


@pytest.mark.parametrize("crossing_step", ["effect_start", "dispatch_authorization"])
def test_atomic_authorization_cannot_charge_research_allowance_to_previous_day(
    tmp_path, monkeypatch, crossing_step,
):
    clock = Clock()
    clock.now = datetime(2026, 11, 2, 7, 59, 50, tzinfo=timezone.utc)
    with Provenance(tmp_path) as store:
        workflow, dispatcher, _, a, _ = setup(store, clock=clock)
        workflow.db.execute("INSERT INTO provider_allocations VALUES (?,?,?,?)",
                            ("next-day-exhausted", "2026-11-02", "research", 4_000_000))
        if crossing_step == "effect_start":
            original = workflow._start_intent_locked

            def slow_start(*args, **kwargs):
                result = original(*args, **kwargs)
                clock.advance(11)
                return result

            monkeypatch.setattr(workflow, "_start_intent_locked", slow_start)
        else:
            original = _BorrowedAtomicJournal.authorize_dispatch

            def slow_dispatch(self, *args, **kwargs):
                result = original(self, *args, **kwargs)
                clock.advance(11)
                return result

            monkeypatch.setattr(_BorrowedAtomicJournal, "authorize_dispatch", slow_dispatch)
        sends = []

        def transport(*_):
            sends.append(1)
            return response()

        with pytest.raises(LedgerError):
            dispatch(dispatcher, a, transport=transport)
        assert sends == []
        assert reservation(workflow) is None
        assert workflow.db.execute("SELECT COUNT(*) FROM provider_allocations").fetchone()[0] == 1
        for table in ("research_dispatch_holds", "workflow_effect_starts", "dispatches"):
            assert workflow.db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] == 0

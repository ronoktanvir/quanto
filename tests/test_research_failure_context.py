"""Invented fixtures validate evidence binding, not investment performance."""
from copy import deepcopy
import json

import pytest

from quanto import admission, study_suite
from quanto.failure_memory import FailureMemory
from quanto.ledger import canonical_json
from quanto.provenance import Provenance
from quanto.research_failure_context import (
    FailureContextError, retrieve_failure_basis, revalidate_failure_context, verify_failure_context,
)
from test_admission import regular_way_fixture, study


@pytest.fixture
def bound(tmp_path):
    request, _ = regular_way_fixture(tmp_path)
    admitted = admission.admit_dataset(tmp_path, request)
    assert admitted["status"] == "success"
    member = study(request, admitted["admission_sha256"])
    suite = study_suite.register_suite(tmp_path, {"members": [
        {**member, "specification": {**member["specification"], "cost_bps": cost}}
        for cost in (0, 10, 25)]})
    assert suite["status"] == "success"
    with Provenance(tmp_path) as store:
        manifest = store.read_json(suite["suite_sha256"])
        revision_ref = manifest["policy_revision_sha256"]
        revision = store.read_json(revision_ref)
        scope = [{"source": "submission", "id": entry["submission_id"]}
                 for entry in revision["lineage"]["prior_refusals"]]
    return {"suite_sha256": suite["suite_sha256"], "failure_ids": scope,
            "verified_policy_revision_sha256": revision_ref}


def prepare(store, configuration, role="hypothesis"):
    config_ref = store.put_json(configuration)
    basis_ref = retrieve_failure_basis(store, configuration["failure_ids"])
    observation_ref = verify_failure_context(store, config_ref, role, basis_ref)
    return config_ref, basis_ref, observation_ref


def test_exact_lineage_relation_and_full_revalidation_remain_qualified(tmp_path, bound):
    with Provenance(tmp_path) as store:
        config, basis, observation = prepare(store, bound)
        result = revalidate_failure_context(store, observation, config, "hypothesis", basis)
        assert len(result["failures"]) == 2
        assert all(failure == {
            "alias": f"failure-{index + 1}", "code": failure["code"], "status": "invalid",
            "disposition": "unresolved", "disposition_recorded": False, "provisional": True,
            "artifact_state": "none", "disposition_artifact_state": "none",
            "relation": "prior_refusal_in_bound_revision",
        } for index, failure in enumerate(result["failures"]))
        assert {f["code"] for f in result["failures"]} == {
            "identity_change_unresolved", "unsupported_due_bill"}
        assert {config, basis, observation}.isdisjoint(result["dependency_refs"])
        for ref in (bound["suite_sha256"], bound["verified_policy_revision_sha256"]):
            assert ref in result["dependency_refs"]
        revision = result["current_evidence"]["revision"]
        assert set(revision["artifact_refs"]) <= set(result["dependency_refs"])
        assert all(item["prior_refusal"] is not None
                   for item in result["current_evidence"]["relations"])
        assert len(store.list_submissions(kind="failure_memory_query")) == 1
        for item in bound["failure_ids"]:
            assert store.get_submission(item["id"])["status"] == "invalid"
        assert not store.journal.connection.execute(
            "SELECT * FROM failure_memory_dispositions").fetchall()


def test_later_roles_reuse_exact_basis_without_new_queries_or_transaction_commit(tmp_path, bound):
    with Provenance(tmp_path) as store:
        config, basis, observation = prepare(store, bound)
        original_queries = len(store.list_submissions(kind="failure_memory_query"))
        with store.journal._transaction():
            revalidate_failure_context(store, observation, config, "hypothesis", basis)
            assert store.journal.connection.in_transaction
        later = verify_failure_context(store, config, "engineer", basis)
        assert later != observation
        assert store.read_json(later)["observation_id"] != store.read_json(observation)["observation_id"]
        assert store.read_json(later)["failures"] == store.read_json(observation)["failures"]
        assert len(store.list_submissions(kind="failure_memory_query")) == original_queries


def test_director_has_no_basis_and_empty_scope_never_queries_unrestricted(tmp_path, bound):
    with Provenance(tmp_path) as store:
        config = store.put_json(bound)
        director = verify_failure_context(store, config, "director", None)
        assert store.read_json(director)["failures"] == []
        assert not store.list_submissions(kind="failure_memory_query")
        with pytest.raises(FailureContextError):
            verify_failure_context(store, config, "hypothesis", None)
        empty = {**bound, "failure_ids": []}
        empty_config, basis, observation = prepare(store, empty)
        assert revalidate_failure_context(store, observation, empty_config, "hypothesis", basis)["failures"] == []
        assert not store.list_submissions(kind="failure_memory_query")
        with pytest.raises(FailureContextError):
            verify_failure_context(store, empty_config, "director", basis)


def test_same_code_generic_submission_and_attempt_are_nonmembers(tmp_path, bound):
    with Provenance(tmp_path) as store:
        submission = store.begin("invented_failure", {"private": "PRIVATE-REQUEST-831"})
        store.finish(submission, "invalid", {"error_code": "unsupported_due_bill"})
        fingerprint = store.journal.register_experiment(
            {"fixture": True}, {"fixture": True}, {"fixture": True}, "synthetic_fixture")
        attempt = store.journal.start_attempt(fingerprint)
        store.journal.finish_attempt(attempt, "invalid", {"error_code": "unsupported_due_bill"})
        configuration = {**bound, "failure_ids": [
            {"source": "submission", "id": submission}, {"source": "attempt", "id": attempt}]}
        config, basis, observation = prepare(store, configuration)
        result = revalidate_failure_context(store, observation, config, "hypothesis", basis)
        assert [item["relation"] for item in result["failures"]] == ["no_relation_established"] * 2
        assert all(item["code"] == "unsupported_due_bill" for item in result["failures"])
        snapshot = store.read_json(basis)["records"][1]
        assert snapshot["original"]["request_availability"] == {
            store.get_submission(submission)["request_sha256"]: "unavailable"}
        rendered = json.dumps(result["failures"])
        assert submission not in rendered and attempt not in rendered
        assert "PRIVATE-REQUEST" not in rendered


@pytest.mark.parametrize("state", ["unresolved", "corrected"])
@pytest.mark.parametrize("unavailable", [False, True])
def test_recorded_claim_preserves_approved_subset_without_lineage_upgrade(tmp_path, bound, state, unavailable):
    with Provenance(tmp_path) as store:
        failure = bound["failure_ids"][0]
        fix = store.put_bytes(b"INVENTED attributed fix; no independent certification")
        memory = FailureMemory(store, allowed_codes=("other_refusal",), allowed_artifact_refs=(fix,))
        claim = memory.append_disposition(failure["source"], failure["id"], state, fix, "other_refusal")
        if unavailable:
            store.tombstone(fix, "operator_requested")
        config, basis, observation = prepare(store, bound)
        result = revalidate_failure_context(store, observation, config, "hypothesis", basis)
        alias = next(item["alias"] for item in store.read_json(basis)["aliases"]
                     if item["id"] == failure["id"])
        fact = next(item for item in result["failures"] if item["alias"] == alias)
        assert fact["disposition"] == state and fact["disposition_recorded"] is True
        assert fact["provisional"] is True
        assert fact["disposition_artifact_state"] == "not_allowed"
        assert fact["relation"] == "prior_refusal_in_bound_revision"
        snapshot = next(item for item in store.read_json(basis)["records"] if item["id"] == failure["id"])
        assert snapshot["disposition"]["row"]["disposition_id"] == claim["disposition_id"]
        assert snapshot["reference_availability"][fix] == ("unavailable" if unavailable else "available")


def test_explicit_unresolved_without_fix_distinguishes_absent_claim(tmp_path, bound):
    with Provenance(tmp_path) as store:
        failure = bound["failure_ids"][0]
        FailureMemory(store, allowed_codes=("other_refusal",)).append_disposition(
            failure["source"], failure["id"], "unresolved", code="other_refusal")
        _, _, observation = prepare(store, bound)
        facts = store.read_json(observation)["failures"]
        assert sorted(item["disposition_recorded"] for item in facts) == [False, True]
        assert all(item["disposition"] == "unresolved" and item["disposition_artifact_state"] == "none"
                   for item in facts)


def test_latest_identical_visible_claim_refuses_stale_basis(tmp_path, bound):
    with Provenance(tmp_path) as store:
        failure = bound["failure_ids"][0]
        memory = FailureMemory(store, allowed_codes=("other_refusal",))
        memory.append_disposition(failure["source"], failure["id"], "unresolved", code="other_refusal")
        config, basis, observation = prepare(store, bound)
        memory.append_disposition(failure["source"], failure["id"], "unresolved", code="other_refusal")
        with pytest.raises(FailureContextError):
            verify_failure_context(store, config, "engineer", basis)
        with pytest.raises(FailureContextError):
            revalidate_failure_context(store, observation, config, "hypothesis", basis)


@pytest.mark.parametrize("when", ["preparation", "binding"])
def test_changed_fix_availability_refuses_even_when_outward_state_unchanged(tmp_path, bound, when):
    with Provenance(tmp_path) as store:
        failure = bound["failure_ids"][0]
        fix = store.put_bytes(b"invented fix evidence")
        FailureMemory(store, allowed_codes=("other_refusal",), allowed_artifact_refs=(fix,)).append_disposition(
            failure["source"], failure["id"], "corrected", fix, "other_refusal")
        config = store.put_json(bound)
        basis = retrieve_failure_basis(store, bound["failure_ids"])
        observation = verify_failure_context(store, config, "hypothesis", basis) if when == "binding" else None
        store.tombstone(fix, "operator_requested")
        with pytest.raises(FailureContextError):
            if observation:
                revalidate_failure_context(store, observation, config, "hypothesis", basis)
            else:
                verify_failure_context(store, config, "hypothesis", basis)


@pytest.mark.parametrize("mutation", [
    lambda value: value.update(truncated=True),
    lambda value: value.update(provisional=False),
    lambda value: value["failures"].pop(),
    lambda value: value["failures"].append(deepcopy(value["failures"][0])),
    lambda value: value["returned_ids"].reverse(),
    lambda value: value["returned_ids"][0].update(source="attempt"),
    lambda value: value.update(scanned_count=0),
    lambda value: value.update(unapproved_private_field="PRIVATE-UNAPPROVED"),
])
def test_incomplete_duplicate_or_wrong_source_receipts_refuse(tmp_path, bound, monkeypatch, mutation):
    original = FailureMemory.query

    def altered(memory, request):
        result = original(memory, request)
        receipt = memory.store.read_json(result["receipt_sha256"])
        mutation(receipt)
        submission = memory.store.begin("failure_memory_query", request)
        receipt["query_submission_id"] = submission
        ref = memory.store.put_json(receipt)
        memory.store.finish(submission, "success", {"artifact_refs": [ref], "returned_ids": receipt["returned_ids"]})
        return {**receipt, "receipt_sha256": ref}

    monkeypatch.setattr(FailureMemory, "query", altered)
    with Provenance(tmp_path) as store:
        with pytest.raises(FailureContextError):
            retrieve_failure_basis(store, bound["failure_ids"])
        assert store.list_submissions(kind="research_failure_basis")[0]["status"] == "invalid"


@pytest.mark.parametrize("mutation", [
    lambda config: config.update(failure_ids=[]),
    lambda config: config["failure_ids"][0].update(source="attempt"),
    lambda config: config.update(verified_policy_revision_sha256="0" * 64),
    lambda config: config.update(suite_sha256="0" * 64),
])
def test_wrong_configuration_authorization_suite_or_revision_refuses(tmp_path, bound, mutation):
    with Provenance(tmp_path) as store:
        _, basis, _ = prepare(store, bound)
        configuration = deepcopy(bound)
        mutation(configuration)
        config = store.put_json(configuration)
        with pytest.raises(FailureContextError):
            verify_failure_context(store, config, "engineer", basis)


@pytest.mark.parametrize("target", ["source", "registration_request", "revision", "admission"])
def test_missing_current_dependencies_refuse_instead_of_negative_relation(tmp_path, bound, target):
    with Provenance(tmp_path) as store:
        config, basis, observation = prepare(store, bound)
        observed = store.read_json(observation)
        refs = {
            "source": observed["current_evidence"]["revision"]["request"]["accepted_decision_sha256"],
            "registration_request": observed["current_evidence"]["suite"]["registration_request_sha256"],
            "revision": observed["policy_revision_sha256"], "admission": observed["admission_sha256"],
        }
        store.tombstone(refs[target], "operator_requested")
        with pytest.raises(FailureContextError):
            revalidate_failure_context(store, observation, config, "hypothesis", basis)


def test_forged_lineage_json_and_unregistered_observation_cannot_certify_context(tmp_path, bound):
    with Provenance(tmp_path) as store:
        config, basis, observation = prepare(store, bound)
        observed = store.read_json(observation)
        observed["failures"][0]["disposition"] = "corrected"
        forged = store.put_json(observed)
        with pytest.raises(FailureContextError):
            revalidate_failure_context(store, forged, config, "hypothesis", basis)
        revision = store.read_json(bound["verified_policy_revision_sha256"])
        revision["lineage"]["prior_refusals"][0]["error_code"] = "other_refusal"
        fake_revision = store.put_json(revision)
        config = store.put_json({**bound, "verified_policy_revision_sha256": fake_revision})
        with pytest.raises(FailureContextError):
            verify_failure_context(store, config, "engineer", basis)


def test_changed_original_outcome_and_aliases_are_refused_without_private_errors(tmp_path, bound):
    with Provenance(tmp_path) as store:
        config, basis, observation = prepare(store, bound)
        failure = bound["failure_ids"][0]
        store.journal.connection.execute("DROP TRIGGER no_update_provenance_outcomes")
        original = store.get_submission(failure["id"])["details"]
        store.journal.connection.execute("UPDATE provenance_outcomes SET details=? WHERE submission_id=?",
                                         (canonical_json({**original, "private": "PRIVATE-SECRET-998"}), failure["id"]))
        with pytest.raises(FailureContextError) as error:
            revalidate_failure_context(store, observation, config, "hypothesis", basis)
        assert str(error.value) == "failure_context_refused"
        assert "PRIVATE" not in str(error.value)


def test_observation_role_configuration_and_basis_are_exact(tmp_path, bound):
    with Provenance(tmp_path) as store:
        config, basis, observation = prepare(store, bound)
        other_config = store.put_json({**bound, "private_run_key": "different"})
        other_basis = retrieve_failure_basis(store, bound["failure_ids"])
        for args in ((other_config, "hypothesis", basis), (config, "engineer", basis),
                     (config, "hypothesis", other_basis)):
            with pytest.raises(FailureContextError):
                revalidate_failure_context(store, observation, *args)


def test_changed_failure_evidence_and_original_pending_outcome_refuse(tmp_path, bound):
    with Provenance(tmp_path) as store:
        evidence = store.put_bytes(b"invented original evidence")
        failure = store.begin("invented_failure", {"invented": True})
        store.finish(failure, "invalid", {"error_code": "unsupported_due_bill", "artifact_refs": [evidence]})
        config, basis, observation = prepare(store, {**bound, "failure_ids": [
            {"source": "submission", "id": failure}]})
        assert store.read_json(observation)["failures"][0]["artifact_state"] == "not_allowed"
        store.tombstone(evidence, "operator_requested")
        with pytest.raises(FailureContextError):
            revalidate_failure_context(store, observation, config, "hypothesis", basis)
        pending = store.begin("invented_pending", {"invented": "pending"})
        config, basis, observation = prepare(store, {**bound, "failure_ids": [
            {"source": "submission", "id": pending}]})
        assert store.read_json(observation)["failures"][0]["status"] == "pending"
        store.finish(pending, "invalid", {"error_code": "unsupported_due_bill"})
        with pytest.raises(FailureContextError):
            revalidate_failure_context(store, observation, config, "hypothesis", basis)


def test_missing_wrong_source_and_duplicate_authorization_do_not_expand_retrieval(tmp_path, bound):
    with Provenance(tmp_path) as store:
        bad_scopes = [[{"source": "attempt", "id": bound["failure_ids"][0]["id"]}],
                      [bound["failure_ids"][0], bound["failure_ids"][0]],
                      [{"source": "submission", "id": "0" * 32}]]
        for scope in bad_scopes:
            with pytest.raises(FailureContextError):
                retrieve_failure_basis(store, scope)
        for query in store.list_submissions(kind="failure_memory_query"):
            assert query["status"] == "success"  # Empty exact result, not an unrestricted search.


def test_forged_registered_observation_is_recomputed_and_originals_are_untouched(tmp_path, bound):
    with Provenance(tmp_path) as store:
        config, basis, observation = prepare(store, bound)
        original_outcomes = [store.get_submission(item["id"]) for item in bound["failure_ids"]]
        document = store.read_json(observation)
        document["submission_id"] = store.begin(document["kind"], document["request"])
        document["failures"][0]["relation"] = "no_relation_established"
        forged = store.put_json(document)
        store.finish(document["submission_id"], "success", {
            "context_sha256": forged, "artifact_refs": [forged]})
        with pytest.raises(FailureContextError):
            revalidate_failure_context(store, forged, config, "hypothesis", basis)
        assert original_outcomes == [store.get_submission(item["id"]) for item in bound["failure_ids"]]


def test_corrupt_dependency_refuses_without_echoing_bytes(tmp_path, bound):
    with Provenance(tmp_path) as store:
        config, basis, observation = prepare(store, bound)
        doc = store.read_json(observation)
        dependency = doc["current_evidence"]["suite"]["registration_request_sha256"]
        (tmp_path / "data" / "objects" / (dependency + ".bin")).write_bytes(b"PRIVATE-CORRUPT-DATA")
        with pytest.raises(FailureContextError) as error:
            revalidate_failure_context(store, observation, config, "hypothesis", basis)
        assert str(error.value) == "failure_context_refused"


def test_fresh_basis_cannot_rewrap_an_older_registered_query_receipt(tmp_path, bound):
    with Provenance(tmp_path) as store:
        config, basis, original_observation = prepare(store, bound)
        original = store.read_json(basis)
        histories = [store.get_submission(item["id"]) for item in bound["failure_ids"]]
        replacement = deepcopy(original)
        replacement["submission_id"] = store.begin(original["kind"], original["request"])
        forged_basis = store.put_json(replacement)
        store.finish(replacement["submission_id"], "success", {
            "context_sha256": forged_basis, "artifact_refs": [forged_basis]})
        with pytest.raises(FailureContextError):
            verify_failure_context(store, config, "engineer", forged_basis)
        # The genuine basis remains usable; rejecting the wrapper neither
        # refreshes its receipt nor changes any original failure or claim.
        assert revalidate_failure_context(
            store, original_observation, config, "hypothesis", basis)["basis_sha256"] == basis
        assert histories == [store.get_submission(item["id"]) for item in bound["failure_ids"]]
        assert len(store.list_submissions(kind="failure_memory_query")) == 1

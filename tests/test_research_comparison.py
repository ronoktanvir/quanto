"""Invented fixtures check deterministic controls, never investment merit.

The real_d007 helper uses the existing invented provider transport and source
factory. Admission, revision, suite, explorer and financial calculation run
unstubbed; separate arithmetic tests supply independently chosen counterexamples.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
import json

import pytest

from quanto import admission, research_comparison as comparison, study_suite
from quanto.ledger import hash_bytes
from quanto.provenance import Provenance, ProvenanceError
from test_admission import regular_way_fixture, study


def rows(equity=("100", "90", "80"), fees=("0", "1", "2"), benchmark=None):
    benchmark = benchmark or equity
    return [{"cost_bps": cost, "strategy_ending_equity": equity[i],
             "strategy_total_fees": fees[i], "benchmark_ending_equity": benchmark[i]}
            for i, cost in enumerate((0, 10, 25))]


def role_refs(root, predicate):
    with Provenance(root) as store:
        return {role + "_sha256": store.put_json({
            "schema_version": 1, "role": role, "decision": decision, "predicate": predicate,
            "artifact_aliases": ["artifact-1"], "findings": []})
            for role, decision in (("hypothesis", "propose"), ("engineer", "execute"))}


@pytest.fixture
def real_d007(tmp_path):
    source_request, _ = regular_way_fixture(tmp_path)
    admitted = admission.admit_dataset(tmp_path, source_request)
    assert admitted["status"] == "success", admitted
    member = study(source_request, admitted["admission_sha256"])
    suite = study_suite.register_suite(tmp_path, {"members": [
        {**member, "specification": {**member["specification"], "cost_bps": cost}}
        for cost in (0, 10, 25)]})
    assert suite["status"] == "success", suite
    predicate = "cost_ending_equity_nonincreasing"
    return {"suite_sha256": suite["suite_sha256"], "predicate": predicate,
            **role_refs(tmp_path, predicate)}


def test_material_choices_compute_different_answers_and_ties():
    # Equity rises with costs while fees rise: the first predicate is false,
    # the second true, and equality false because only the middle cost differs.
    operands = rows(("80", "90", "100"), benchmark=("80", "91", "100"))
    assert comparison.evaluate("cost_ending_equity_nonincreasing", operands) is False
    assert comparison.evaluate("cost_fees_nondecreasing", operands) is True
    assert comparison.evaluate("strategy_equals_benchmark_terminal", operands) is False
    # A second counterexample separates fees from both other computations.
    operands = rows(fees=("2", "1", "0"))
    assert comparison.evaluate("cost_ending_equity_nonincreasing", operands) is True
    assert comparison.evaluate("cost_fees_nondecreasing", operands) is False
    assert comparison.evaluate("strategy_equals_benchmark_terminal", operands) is True
    for predicate in comparison.PREDICATES:
        assert comparison.evaluate(predicate, rows(("1", "1", "1"), ("0", "0", "0"))) is True


def test_exact_decimal_is_not_float_or_context_rounded():
    operands = rows(("1.000000000000000000000000000000002",
                     "1.000000000000000000000000000000001", "1"))
    with localcontext() as context:
        context.prec = 2
        assert comparison.evaluate("cost_ending_equity_nonincreasing", operands) is True
        operands[1]["strategy_ending_equity"] = "1.000000000000000000000000000000003"
        assert comparison.evaluate("cost_ending_equity_nonincreasing", operands) is False


@pytest.mark.parametrize("value", [1, 1.0, True, None, "NaN", "Infinity", "-1", "-0", "0.0",
    "+1", "01", "1e2", "1E2", "1" * 35, "1E+1000000", "1E-1000000", " " * 129])
def test_noncanonical_nonfinite_or_unbounded_operands_refuse(value):
    operands = rows()
    operands[0]["strategy_total_fees"] = value
    with pytest.raises(comparison.ComparisonError, match="comparison_decimal_refused"):
        comparison.evaluate("cost_ending_equity_nonincreasing", operands)


@pytest.mark.parametrize("mutate", [lambda x: x.pop(), lambda x: x.reverse(),
    lambda x: x[1].update(cost_bps=25), lambda x: x[0].pop("benchmark_ending_equity"),
    lambda x: x[0].update(cost_bps=False)])
def test_missing_reordered_or_wrong_roster_refuses(mutate):
    operands = rows()
    mutate(operands)
    with pytest.raises(comparison.ComparisonError, match="comparison_roster_mismatch"):
        comparison.evaluate("cost_fees_nondecreasing", operands)


@pytest.mark.parametrize("predicate", sorted(comparison.PREDICATES))
def test_real_complete_d007_suite_fresh_registration_and_private_exact_result(tmp_path, real_d007, predicate):
    real_d007.update(predicate=predicate, **role_refs(tmp_path, predicate))
    result = comparison.run_comparison(tmp_path, real_d007)
    assert result["status"] == "success", result
    with Provenance(tmp_path) as store:
        artifact = store.read_json(result["comparison_sha256"])
        registration = store.read_json(result["registration_sha256"])
        assert registration["request"] == real_d007
        assert registration["predicate_semantics"] == comparison.SEMANTICS[real_d007["predicate"]]
        assert registration["code_identity"]["module_sha256"] == hash_bytes(
            comparison.Path(comparison.__file__).read_bytes())
        values = artifact["operands"]
        equities = [Decimal(row["strategy_ending_equity"]) for row in values]
        fees = [Decimal(row["strategy_total_fees"]) for row in values]
        expected = {
            "cost_ending_equity_nonincreasing": all(a >= b for a, b in zip(equities, equities[1:])),
            "cost_fees_nondecreasing": all(a <= b for a, b in zip(fees, fees[1:])),
            "strategy_equals_benchmark_terminal": all(
                Decimal(row["strategy_ending_equity"]) == Decimal(row["benchmark_ending_equity"])
                for row in values),
        }[predicate]
        assert artifact["predicate_holds"] is expected
        assert [x["cost_bps"] for x in artifact["child_sources"]] == [0, 10, 25]
        assert len({x["submission_id"] for x in artifact["child_sources"]}) == 3
        assert result["derivative_candidate_count"] == result["derivative_attempt_count"] == 1
        assert len(store.list_submissions(kind="study_suite_run")) == 1
        assert store.journal.verify_events()["count"] > 0
    safe = comparison.completion_projection(result)
    assert safe == {"schema_version": 1, "kind": "research_comparison_completion",
                    "execution_state": "completed", "integrity_state": "verified"}
    assert "predicate" not in json.dumps(safe) and "sha256" not in json.dumps(safe)


@pytest.mark.parametrize("raw_request", ['{"private":"not retained",', '{"predicate":null,"predicate":null}',
    [], {"suite_sha256": "0" * 64, "predicate": "unsupported"}])
def test_invalid_registration_retained_without_execution(tmp_path, monkeypatch, raw_request):
    monkeypatch.setattr(study_suite, "run_suite", lambda *args: pytest.fail("no dispatch"))
    if isinstance(raw_request, list):
        raw_request = json.dumps(raw_request)
    result = comparison.run_comparison(tmp_path, raw_request)
    assert result["status"] == "invalid"
    with Provenance(tmp_path) as store:
        receipt = store.get_submission(result["submission_id"])
        assert receipt["kind"] == "research_comparison" and receipt["status"] == "invalid"
        assert "not retained" not in json.dumps(receipt)
        assert not store.list_submissions(kind="study_suite_run")


@pytest.mark.parametrize("mutate", [lambda r: r.update(suite_run_id="0" * 32),
    lambda r: r.update(predicate="cost_fees_nondecreasing"),
    lambda r: r.update(hypothesis_sha256=r["engineer_sha256"])])
def test_unsupported_fields_or_incorrect_role_projection_refuses_before_suite(tmp_path, real_d007, monkeypatch, mutate):
    mutate(real_d007)
    monkeypatch.setattr(study_suite, "run_suite", lambda *args: pytest.fail("no dispatch"))
    result = comparison.run_comparison(tmp_path, real_d007)
    assert result["status"] == "invalid"


def test_corrupt_input_source_refuses_before_dispatch(tmp_path, real_d007, monkeypatch):
    digest = real_d007["hypothesis_sha256"]
    (tmp_path / "data" / "objects" / (digest + ".bin")).write_bytes(b"corrupt source")
    monkeypatch.setattr(study_suite, "run_suite", lambda *args: pytest.fail("no dispatch"))
    result = comparison.run_comparison(tmp_path, real_d007)
    assert result["status"] == "invalid"
    assert result["error_code"] == "comparison_artifact_or_storage_unavailable"


@pytest.mark.parametrize("change", ["reorder", "missing", "foreign_child", "numeric_type", "corrupt_result", "corrupt_source"])
def test_fresh_result_corruption_or_substitution_never_computes(tmp_path, real_d007, monkeypatch, change):
    original = comparison._operands
    calls = []
    def altered(store, submission, registration, result):
        calls.append(result["submission_id"])
        assert result["status"] == "success", result
        if change == "reorder":
            result["summary"]["members"].reverse()
        elif change == "missing":
            result["summary"]["members"].pop()
        elif change == "foreign_child":
            result["summary"]["members"][0]["outcome"]["submission_id"] = "0" * 32
        elif change == "numeric_type":
            result["summary"]["members"][1]["cost_bps"] = 10.0
        else:
            if change == "corrupt_result":
                digest = result["summary"]["members"][0]["outcome"]["artifact_sha256"]
            else:
                manifest = store.read_json(real_d007["suite_sha256"])
                digest = store.read_json(manifest["members"][0]["request"]["dataset_sha256"])["source_sha256"]
            (tmp_path / "data" / "objects" / (digest + ".bin")).write_bytes(b"private corrupted bytes")
        return original(store, submission, registration, result)
    monkeypatch.setattr(comparison, "_operands", altered)
    result = comparison.run_comparison(tmp_path, real_d007)
    assert result["status"] == "interrupted" and len(calls) == 1
    assert "comparison_sha256" not in result
    assert "private corrupted bytes" not in json.dumps(result)


def test_old_successful_invocation_cannot_be_substituted(tmp_path, real_d007, monkeypatch):
    old = study_suite.run_suite(tmp_path, {"suite_sha256": real_d007["suite_sha256"]})
    assert old["status"] == "success", old
    original = comparison._operands
    monkeypatch.setattr(comparison, "_operands", lambda store, sub, reg, result:
                        original(store, sub, reg, deepcopy(old)))
    result = comparison.run_comparison(tmp_path, real_d007)
    assert result["status"] == "interrupted"
    assert result["error_code"] == "comparison_requires_fresh_suite"


def test_interruption_retains_pending_derivative_and_suite_without_retry(tmp_path, real_d007, monkeypatch):
    from quanto import explorer
    original = explorer.run_submission
    calls = []
    def interrupted(root, request, *, suite_run_id):
        calls.append(request)
        if len(calls) == 2:
            raise KeyboardInterrupt
        return original(root, request, suite_run_id=suite_run_id)
    monkeypatch.setattr(explorer, "run_submission", interrupted)
    with pytest.raises(KeyboardInterrupt):
        comparison.run_comparison(tmp_path, real_d007)
    with Provenance(tmp_path) as store:
        attempts = store.list_submissions(kind="research_comparison")
        suites = store.list_submissions(kind="study_suite_run")
        assert len(attempts) == len(suites) == 1
        assert attempts[0]["status"] == suites[0]["status"] == "pending"
        assert store.journal.connection.execute("SELECT COUNT(*) FROM research_comparisons").fetchone()[0] == 1
    summary = study_suite.inspect_run(tmp_path, suites[0]["submission_id"])
    assert [x["outcome"]["status"] for x in summary["members"]] == ["success", "pending", "pending"]
    assert len(calls) == 2


def test_partial_child_failure_retains_original_suite_and_no_comparison(tmp_path, real_d007, monkeypatch):
    from quanto import explorer
    original = explorer.run_submission
    calls = []
    def fail(root, request, *, suite_run_id):
        calls.append(request["specification"]["cost_bps"])
        if calls[-1] == 10:
            raise RuntimeError("raw private provider exception")
        return original(root, request, suite_run_id=suite_run_id)
    monkeypatch.setattr(explorer, "run_submission", fail)
    result = comparison.run_comparison(tmp_path, real_d007)
    assert result["status"] == "interrupted" and calls == [0, 10, 25]
    summary = study_suite.inspect_run(tmp_path, result["suite_run_id"])
    assert [x["outcome"]["status"] for x in summary["members"]] == ["success", "pending", "success"]
    assert "comparison_sha256" not in result and "raw private" not in json.dumps(result)


def test_deliberate_new_attempts_and_material_choice_have_separate_counts(tmp_path, real_d007):
    first = comparison.run_comparison(tmp_path, real_d007)
    replay = comparison.run_comparison(tmp_path, real_d007)
    assert first["status"] == replay["status"] == "success", (first, replay)
    assert first["fingerprint"] == replay["fingerprint"]
    assert first["suite_run_id"] != replay["suite_run_id"]
    assert replay["derivative_candidate_count"] == 1 and replay["derivative_attempt_count"] == 2
    predicate = "strategy_equals_benchmark_terminal"
    changed = {**real_d007, "predicate": predicate, **role_refs(tmp_path, predicate)}
    result = comparison.run_comparison(tmp_path, changed)
    assert result["status"] == "success", result
    assert result["fingerprint"] != first["fingerprint"]
    assert result["derivative_candidate_count"] == 2 and result["derivative_attempt_count"] == 3
    with Provenance(tmp_path) as store:
        assert len(store.list_submissions(kind="exploratory_study")) == 9


def test_changed_derivative_code_identity_before_publication_refuses(tmp_path, real_d007, monkeypatch):
    original = comparison._code_identity
    calls = []
    def identity():
        calls.append(True)
        return {**original(), "injected_revision": len(calls)}
    monkeypatch.setattr(comparison, "_code_identity", identity)
    result = comparison.run_comparison(tmp_path, real_d007)
    assert result["status"] == "interrupted" and len(calls) == 2
    assert result["error_code"] == "comparison_dependencies_changed"
    assert "comparison_sha256" not in result


def test_comparison_publication_failure_stays_pending_without_rerun(tmp_path, real_d007, monkeypatch):
    original = Provenance.finish
    def unavailable(store, submission, status, details):
        if store.get_submission(submission)["kind"] == "research_comparison":
            raise ProvenanceError("private storage error")
        return original(store, submission, status, details)
    monkeypatch.setattr(Provenance, "finish", unavailable)
    result = comparison.run_comparison(tmp_path, real_d007)
    assert result["status"] == "pending" and "comparison_sha256" in result
    assert result["error_code"] == "comparison_publication_interrupted"
    with Provenance(tmp_path) as store:
        assert store.get_submission(result["submission_id"])["status"] == "pending"
        assert len(store.list_submissions(kind="study_suite_run")) == 1
    assert comparison.completion_projection(result)["execution_state"] == "uncertain"


def test_parent_binding_callback_precedes_validation_and_complete_suite(tmp_path, real_d007):
    bound = []
    def bind(submission):
        bound.append(submission)
        with Provenance(tmp_path) as store:
            child = store.get_submission(submission)
            assert child["kind"] == "research_comparison" and child["status"] == "pending"
            assert store.list_submissions(kind="study_suite_run") == []
            assert store.journal.connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_comparisons'"
            ).fetchone() is None
            store.journal.append_event("synthetic_parent_bound", {"submission_id": submission})
    result = comparison.run_comparison(tmp_path, real_d007, on_registered=bind)
    assert result["status"] == "success" and bound == [result["submission_id"]], result
    with Provenance(tmp_path) as store:
        events = [(row["id"], row["kind"]) for row in store.journal.connection.execute(
            "SELECT id,kind FROM events WHERE kind IN "
            "('synthetic_parent_bound','research_comparison_registered','study_suite_run_registered')")]
        assert [kind for _, kind in events] == ["synthetic_parent_bound",
            "research_comparison_registered", "study_suite_run_registered"]
        assert len(store.list_submissions(kind="study_suite_run")) == 1


def test_parent_binding_runs_even_before_invalid_request_validation(tmp_path):
    bound = []
    result = comparison.run_comparison(tmp_path, '{"invalid":', on_registered=bound.append)
    assert result["status"] == "invalid" and bound == [result["submission_id"]]
    assert result["error_code"] == "comparison_input_refused"


def test_failed_parent_binding_retains_child_and_aborts_before_validation(tmp_path, real_d007, monkeypatch):
    bound = []
    def bind(submission):
        bound.append(submission)
        raise RuntimeError("private parent identity and fence must not escape")
    monkeypatch.setattr(comparison, "_inputs", lambda *args: pytest.fail("no validation"))
    monkeypatch.setattr(study_suite, "run_suite", lambda *args: pytest.fail("no financial work"))
    result = comparison.run_comparison(tmp_path, real_d007, on_registered=bind)
    assert result["status"] == "invalid" and bound == [result["submission_id"]]
    assert result["error_code"] == "comparison_registration_callback_failed"
    assert "private parent" not in json.dumps(result)
    with Provenance(tmp_path) as store:
        receipt = store.get_submission(bound[0])
        assert receipt["status"] == "invalid"
        assert receipt["details"] == {"result_kind": "no_comparison",
            "error_code": "comparison_registration_callback_failed"}
        assert store.list_submissions(kind="study_suite_run") == []
        assert store.journal.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_comparisons'"
        ).fetchone() is None


def test_interrupted_parent_binding_retains_pending_child_without_suite(tmp_path, real_d007, monkeypatch):
    bound = []
    def interrupted(submission):
        bound.append(submission)
        raise KeyboardInterrupt
    monkeypatch.setattr(study_suite, "run_suite", lambda *args: pytest.fail("no financial work"))
    with pytest.raises(KeyboardInterrupt):
        comparison.run_comparison(tmp_path, real_d007, on_registered=interrupted)
    with Provenance(tmp_path) as store:
        children = store.list_submissions(kind="research_comparison")
        assert len(children) == 1 and children[0]["submission_id"] == bound[0]
        assert children[0]["status"] == "pending"
        assert store.list_submissions(kind="study_suite_run") == []

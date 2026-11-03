"""Synthetic adversarial tests of the fixed D008 method-only packet vocabulary."""

from copy import deepcopy
from hashlib import sha256
import json

import pytest
from access_fixtures import synthetic_access as synthetic_access


from quanto.research_packets import (
    FAILURE_ARTIFACT_STATES, FAILURE_CODES, FAILURE_FIELDS, FAILURE_RELATIONS,
    FINDING_CODES, MAX_OUTPUT_BYTES, MAX_PACKET_BYTES, METHOD, PREDICATES,
    ROLE_DECISION_BLOCK, SUITE_INTEGRITY, SYSTEM_PROMPT, PacketError, _DECISIONS,
    packet_messages, parse_role_output, project_role_output, validate_packet, validate_projection,
)
from quanto.research_workflow import ROLES

pytestmark = pytest.mark.usefixtures("synthetic_access")


PREDICATE = "cost_ending_equity_nonincreasing"


def output(role="hypothesis", **changes):
    value = {
        "schema_version": 1, "role": role,
        "decision": {"director": "proceed", "hypothesis": "propose", "engineer": "execute"}.get(
            role, "no_blocking_method_issue"),
        "predicate": None if role == "director" else PREDICATE,
        "artifact_aliases": ["artifact-1"],
        "findings": [{"code": "hidden_values_unreviewed", "artifact_aliases": ["artifact-1"]}],
        "rationale": "Synthetic method reasoning only.",
    }
    value.update(changes)
    return value


def packet(role="hypothesis", **changes):
    value = {
        "schema_version": 1, "kind": "research_role_context", "role": role,
        "objective": "frozen_suite_falsification", "evidence_kind": "synthetic_fixture",
        "access_class": "sanitized_development",
        "method": METHOD, "suite_integrity": SUITE_INTEGRITY, "scope": "development_only",
        "data_values_disclosed": False, "allowed_predicates": sorted(PREDICATES),
        "artifact_aliases": ["artifact-1", "artifact-2"],
        "failures": [{"alias": "failure-1", "code": "unsupported_due_bill",
                      "status": "invalid", "disposition": "unresolved",
                      "disposition_recorded": False, "provisional": True,
                      "artifact_state": "not_allowed", "disposition_artifact_state": "none",
                      "relation": "no_relation_established"}],
        "prior_outputs": [project_role_output(output("director"))],
        "execution_state": "not_requested",
    }
    if role == "director":
        value["prior_outputs"] = []
    elif role in ROLES[2:]:
        value["prior_outputs"].append(project_role_output(output()))
    value.update(changes)
    return value


def parse(value=None, *, role="hypothesis", aliases=None, predicates=None, required=None):
    return parse_role_output(
        json.dumps(output(role) if value is None else value), role,
        ["artifact-1", "artifact-2"] if aliases is None else aliases,
        sorted(PREDICATES) if predicates is None else predicates, required,
    )


@pytest.mark.parametrize("role", ROLES)
def test_all_roles_have_fixed_bounded_packets_and_outputs(role):
    source = packet(role)
    checked = validate_packet(source)
    assert checked == source
    assert checked is not source
    checked["artifact_aliases"].append("artifact-3")
    assert source["artifact_aliases"] == ["artifact-1", "artifact-2"]
    messages = packet_messages(source)
    assert messages["system"] == SYSTEM_PROMPT
    assert messages["messages"] == [{"role": "user", "content": json.dumps(
        source, sort_keys=True, separators=(",", ":"), ensure_ascii=True)}]
    assert len(messages["messages"][0]["content"].encode()) <= MAX_PACKET_BYTES
    parsed = parse(role=role, required=PREDICATE if role in ROLES[2:] else None)
    assert parsed == output(role)
    assert project_role_output(parsed) == {k: v for k, v in parsed.items() if k != "rationale"}


def test_fixed_prompt_decision_block_exactly_matches_parser_in_role_order():
    decisions = json.loads(ROLE_DECISION_BLOCK)
    assert list(decisions) == list(ROLES)
    assert decisions == {role: sorted(_DECISIONS[role]) for role in ROLES}
    assert ROLE_DECISION_BLOCK == json.dumps(decisions, separators=(",", ":"))
    assert SYSTEM_PROMPT.count(ROLE_DECISION_BLOCK) == 1
    prompts = [packet_messages(packet(role))["system"] for role in ROLES]
    assert len({sha256(prompt.encode()).hexdigest() for prompt in prompts}) == 1
    assert "role must equal the input context's role" in SYSTEM_PROMPT
    assert "engineer, data_critic, statistical_critic, quality and scope" in SYSTEM_PROMPT
    assert "including engineer stop and reviewer block or inconclusive" in SYSTEM_PROMPT


@pytest.mark.parametrize("role,decision", [
    (role, decision) for role in ROLES for decision in sorted(_DECISIONS[role])
])
@pytest.mark.parametrize("predicate", sorted(PREDICATES))
def test_every_permitted_decision_preserves_supported_predicate_and_decision_freedom(
        role, decision, predicate):
    selected = None if role == "director" else predicate
    candidate = output(role, decision=decision, predicate=selected)
    checked = parse(candidate, role=role, required=predicate if role in ROLES[2:] else None)
    assert checked["decision"] == decision
    assert checked["predicate"] == selected
    if role in ROLES[3:] and decision == "inconclusive":
        assert project_role_output(checked)["decision"] == "inconclusive"


@pytest.mark.parametrize("predicate", [None, *sorted(PREDICATES)])
def test_hypothesis_stop_keeps_both_null_and_supported_predicate_forms(predicate):
    assert parse(output(decision="stop", predicate=predicate))["predicate"] == predicate


@pytest.mark.parametrize("role,decision", [
    (role, decision) for role in ROLES[2:] for decision in sorted(_DECISIONS[role])
])
@pytest.mark.parametrize("predicate", [None, "cost_fees_nondecreasing"])
def test_dependent_roles_cannot_change_predicate_even_when_stopping_blocking_or_inconclusive(
        role, decision, predicate):
    with pytest.raises(PacketError):
        parse(output(role, decision=decision, predicate=predicate), role=role, required=PREDICATE)


@pytest.mark.parametrize("role", ROLES)
def test_output_role_must_match_exact_context_role(role):
    other = ROLES[(ROLES.index(role) + 1) % len(ROLES)]
    with pytest.raises(PacketError):
        parse(output(other), role=role, required=PREDICATE if role in ROLES[2:] else None)


def test_invented_last_role_contract_violation_is_rejected_without_repair():
    candidate = output("scope", decision="unlisted_scope_decision", predicate=None)
    original = deepcopy(candidate)
    with pytest.raises(PacketError):
        parse(candidate, role="scope", required=PREDICATE)
    assert candidate == original


def test_last_role_schema_refusal_retains_private_partial_history_and_full_hold(tmp_path, monkeypatch):
    from quanto import provider
    from quanto.provenance import Provenance
    from quanto.research_broker import run_workflow
    from test_research_broker import ModelFixture, configuration

    monkeypatch.setattr(provider, "local_key", lambda _: pytest.fail("No credential access"))
    # Reuse the existing invented-data factory; no retained runtime/data is read.
    config = configuration.__wrapped__(tmp_path)

    class ClarificationFixture(ModelFixture):
        def __call__(self, body, key):
            response = super().__call__(body, key)
            candidate = json.loads(response["content"][0]["text"])
            if candidate["role"] == "data_critic":
                candidate["decision"] = "inconclusive"
            if candidate["role"] == "scope":
                candidate.update(decision="unlisted_scope_decision", predicate=None)
            response["content"][0]["text"] = json.dumps(candidate)
            return response

    fixture = ClarificationFixture()
    result = run_workflow(tmp_path, config, transport=fixture)
    assert result["status"] == "invalid" and result["review_outcome"] == "incomplete"
    assert len(result["stages"]) == 6 and len(fixture.contexts) == 7
    assert result["dispatch_counts"] == {"authorized": 7, "response_observed": 7}
    with Provenance(tmp_path) as store:
        critic = next(stage for stage in result["stages"] if stage["role"] == "data_critic")
        assert store.read_json(critic["projection_sha256"])["decision"] == "inconclusive"
        row = store.journal.connection.execute(
            "SELECT h.request_id,h.assignment_id,p.artifact_sha256 FROM research_dispatch_holds h "
            "JOIN workflow_assignments a USING(assignment_id) "
            "JOIN research_private_responses p USING(request_id) WHERE a.role='scope'").fetchone()
        private = store.read_json(row["artifact_sha256"])
        rejected = json.loads(private["reply"])
        assert rejected["decision"] == "unlisted_scope_decision" and rejected["predicate"] is None
        hold = store.journal.connection.execute(
            "SELECT state,actual_micro_usd FROM reservations WHERE request_id=?",
            (row["request_id"],)).fetchone()
        assert hold["state"] == "uncertain" and hold["actual_micro_usd"] is None
        effect = store.journal.connection.execute(
            "SELECT status FROM workflow_effect_outcomes WHERE assignment_id=? AND request_id=?",
            (row["assignment_id"], row["request_id"])).fetchone()
        assert effect["status"] == "uncertain"
        assert store.journal.connection.execute(
            "SELECT COUNT(*) FROM research_dispatch_holds").fetchone()[0] == 7
    repeated = run_workflow(tmp_path, config, transport=lambda *_: pytest.fail("No retry"))
    assert repeated["error_code"] == "broker_run_key_already_used"


def test_maximum_typed_request_envelope_fits_unchanged_bounds_for_both_models():
    from quanto import provider
    from quanto.research_broker import _contracts

    aliases = [f"artifact-{i}" for i in range(1, 33)]
    prior = [project_role_output(output(
        role, artifact_aliases=aliases,
        findings=[{"code": code, "artifact_aliases": aliases}
                  for code in sorted(FINDING_CODES)[:8]])) for role in ROLES[:-1]]
    failures = [{**packet()["failures"][0], "alias": f"failure-{i}"} for i in range(1, 17)]
    largest_structure = packet("scope", artifact_aliases=aliases, prior_outputs=prior,
                               failures=failures)
    encoded = json.dumps(largest_structure, sort_keys=True, separators=(",", ":"))
    # Every permitted packet string is an ASCII code/alias. Only JSON quotation
    # marks need additional escaping when it becomes the request's content string.
    maximum_content_escaping = encoded.count('"')
    candidate = deepcopy(largest_structure)
    while True:
        try:
            rendered = packet_messages(candidate)
            break
        except PacketError as exc:
            assert str(exc) == "packet_size_refused"
            next(item for item in candidate["prior_outputs"] if item["findings"])["findings"].pop()
    for model in (provider.HAIKU, provider.OPUS):
        contract = _contracts({role: model for role in ROLES})["scope"]
        assert contract["prompt_sha256"] == sha256(SYSTEM_PROMPT.encode()).hexdigest()
        ceiling = 4096 if model == provider.OPUS else 2048
        empty = provider.prepare_research_text(
            model=model, system=SYSTEM_PROMPT, messages=[{"role": "user", "content": ""}],
            max_tokens=ceiling, max_input_bytes=contract["max_input_bytes"])
        conservative_body_bound = len(empty.body) + MAX_PACKET_BYTES + maximum_content_escaping
        assert conservative_body_bound <= contract["max_input_bytes"] == 40_000
        conservative_hold_bound = ((conservative_body_bound + 65_536) *
                                   (8 if model == provider.OPUS else 1) +
                                   (ceiling * 20 if model == provider.OPUS else ceiling * 5 // 2))
        assert conservative_hold_bound <= contract["max_spend_micro_usd"]
        prepared = provider.prepare_research_text(
            model=model, **rendered, max_tokens=ceiling,
            max_input_bytes=contract["max_input_bytes"])
        assert len(prepared.body) <= conservative_body_bound
        assert prepared.reserved_micro_usd <= contract["max_spend_micro_usd"]


def test_packet_requires_exact_neutral_method_and_supervisor_integrity_fact():
    assert METHOD == "frozen_next_open_three_cost_development_suite"
    assert SUITE_INTEGRITY == "verified_roster_and_current_specification"
    source = packet()
    checked = validate_packet(source)
    assert checked["method"] == METHOD
    assert checked["suite_integrity"] == SUITE_INTEGRITY
    rendered = json.loads(packet_messages(source)["messages"][0]["content"])
    assert rendered == checked
    del source["suite_integrity"]
    with pytest.raises(PacketError, match="packet_fields_refused"):
        validate_packet(source)


@pytest.mark.parametrize("value", [
    None, True, False, 1, 1.0, [], {}, [SUITE_INTEGRITY],
    {"roster": "verified", "specification": "current"},
    "", "unverified", "verified_data_accuracy", "verified_predicate_true",
    "verified_roster", SUITE_INTEGRITY + " ", SUITE_INTEGRITY.upper(),
    "2026-11-02", "provider-AAPL", "/private/suite.json", "sk-ant-private",
    {"prices": [100, 101], "dates": ["2026-11-02"]},
])
def test_integrity_fact_rejects_wrong_types_unapproved_claims_and_private_payloads(value):
    source = packet(suite_integrity=value)
    for action in (validate_packet, packet_messages):
        with pytest.raises(PacketError):
            action(source)


@pytest.mark.parametrize("value", [
    "frozen_trailing_return_next_open_three_costs", METHOD + " ", METHOD.upper(),
    "frozen_sma_three_costs", "private_strategy_parameters", None, True, [],
    {"method": METHOD},
])
def test_method_rejects_old_inaccurate_label_and_nonexact_replacements(value):
    with pytest.raises(PacketError):
        validate_packet(packet(method=value))


@pytest.mark.parametrize("extra", [
    {"integrity_details": {"suite_sha256": "a" * 64}},
    {"verified_predicate": True}, {"roster_verified": True},
    {"artifact_purposes": {"artifact-1": "method_contract"}},
    {"suite_integrity_source": "/private/suite.json"},
])
def test_integrity_fact_does_not_expand_packet_to_extra_claims_or_alias_purposes(extra):
    with pytest.raises(PacketError):
        validate_packet(packet(**extra))


def test_integrity_fact_cannot_be_asserted_in_model_output_or_forwarded_projection():
    with pytest.raises(PacketError):
        parse(output(suite_integrity=SUITE_INTEGRITY))
    source = packet()
    source["prior_outputs"][0]["suite_integrity"] = SUITE_INTEGRITY
    with pytest.raises(PacketError):
        validate_packet(source)


@pytest.mark.parametrize("role", ROLES)
def test_verified_integrity_preserves_free_stop_block_or_inconclusive_decisions(role):
    decisions = ["stop"] if role in ROLES[:3] else ["block", "inconclusive"]
    for decision in decisions:
        source = packet(role)
        assert validate_packet(source)["suite_integrity"] == SUITE_INTEGRITY
        stopped = output(role, decision=decision, findings=[{
            "code": "specification_mismatch", "artifact_aliases": ["artifact-1"]}],
            rationale="A synthetic justified method objection remains permitted.")
        checked = parse(stopped, role=role, required=PREDICATE if role in ROLES[2:] else None)
        assert checked["decision"] == decision
        assert checked["findings"][0]["code"] == "specification_mismatch"


@pytest.mark.parametrize("payload", [
    {"prices": [100.5, 101.5]}, {"dates": ["2026-11-01"]},
    {"provider_id": "alpaca-AAPL"}, {"credential": "sk-ant-private"},
    {"path": "/Users/private/data.json"}, {"result": True},
    {"metadata": {"hidden": {"prices": [1, 2, 3]}}},
])
def test_unknown_data_bearing_fields_refuse_at_each_schema_boundary(payload):
    cases = []
    p = packet()
    p.update(payload)
    cases.append(p)
    p = packet()
    p["failures"][0].update(payload)
    cases.append(p)
    p = packet()
    p["prior_outputs"][0].update(payload)
    cases.append(p)
    p = packet()
    p["prior_outputs"][0]["findings"][0].update(payload)
    cases.append(p)
    for candidate in cases:
        with pytest.raises(PacketError) as exc:
            validate_packet(candidate)
        assert not any(str(item) in str(exc.value) for item in payload.values())


@pytest.mark.parametrize("field,value", [
    ("schema_version", True), ("schema_version", 1.0), ("schema_version", "1"),
    ("kind", "private_data"), ("role", "execution"),
    ("objective", "Choose AAPL on 2026-11-01"),
    ("evidence_kind", "live_execution"), ("access_class", "protected"),
    ("method", "[100, 101]"), ("scope", "holdout"),
    ("data_values_disclosed", 0), ("data_values_disclosed", True),
    ("allowed_predicates", []), ("allowed_predicates", ["price_rise"]),
    ("allowed_predicates", [PREDICATE, PREDICATE]),
    ("allowed_predicates", [PREDICATE, {"prices": [1]}]),
    ("artifact_aliases", ["a" * 64]), ("artifact_aliases", ["artifact-0"]),
    ("artifact_aliases", ["artifact-01"]), ("artifact_aliases", ["artifact-33"]),
    ("artifact_aliases", ["artifact-1", "artifact-1"]),
    ("artifact_aliases", ["2026-11-01"]), ("artifact_aliases", ["/private/data"]),
    ("artifact_aliases", ["sk-ant-secret"]), ("artifact_aliases", [[100, 101]]),
    ("failures", "private raw error"), ("prior_outputs", ["raw model narrative"]),
    ("execution_state", "predicate_true"), ("execution_state", {"equity": 100}),
])
def test_packet_rejects_wrong_types_and_values(field, value):
    with pytest.raises(PacketError):
        validate_packet(packet(**{field: value}))


@pytest.mark.parametrize("field,value", [
    ("alias", "failure-17"), ("alias", "provider-record-id"),
    ("code", "raw_error:/private/data"), ("status", "success"),
    ("disposition", "proven_fixed"),
])
def test_failure_projection_is_finite(field, value):
    source = packet()
    source["failures"][0][field] = value
    with pytest.raises(PacketError):
        validate_packet(source)


@pytest.mark.parametrize("field", sorted(FAILURE_FIELDS))
def test_failure_context_requires_every_exact_qualification(field):
    source = packet()
    del source["failures"][0][field]
    with pytest.raises(PacketError, match="packet_fields_refused"):
        validate_packet(source)


@pytest.mark.parametrize("field,value", [
    ("disposition_recorded", 0), ("disposition_recorded", 1),
    ("disposition_recorded", None), ("disposition_recorded", "false"),
    ("disposition_recorded", []), ("disposition_recorded", {}),
    ("provisional", False), ("provisional", 1), ("provisional", 0),
    ("provisional", None), ("provisional", "true"), ("provisional", []),
    ("artifact_state", "repair_verified"), ("artifact_state", True),
    ("artifact_state", {"sha256": "a" * 64}),
    ("disposition_artifact_state", "reviewed"), ("disposition_artifact_state", None),
    ("disposition_artifact_state", ["verified"]),
    ("relation", "resolved_under_reviewed_revision"), ("relation", "current_safe"),
    ("relation", True), ("relation", []), ("relation", {"outcome": True}),
])
def test_failure_qualifications_reject_wrong_types_and_stronger_claims(field, value):
    source = packet()
    source["failures"][0][field] = value
    with pytest.raises(PacketError):
        validate_packet(source)


def test_absent_disposition_cannot_be_projected_as_a_corrected_claim():
    source = packet()
    source["failures"][0].update(disposition="corrected", disposition_recorded=False,
                                  disposition_artifact_state="verified")
    with pytest.raises(PacketError, match="packet_failure_state_refused"):
        validate_packet(source)


@pytest.mark.parametrize("state", ["not_allowed", "verified", "unavailable", "verification_bound"])
def test_absent_disposition_cannot_claim_linked_disposition_evidence(state):
    source = packet()
    source["failures"][0]["disposition_artifact_state"] = state
    with pytest.raises(PacketError, match="packet_failure_state_refused"):
        validate_packet(source)


@pytest.mark.parametrize("changes", [
    {"disposition_artifact_state": "none"}, {"status": "pending"},
])
def test_corrected_claim_requires_fix_evidence_state_and_a_historical_outcome(changes):
    source = packet()
    source["failures"][0].update(disposition="corrected", disposition_recorded=True,
                                  disposition_artifact_state="verified")
    source["failures"][0].update(changes)
    with pytest.raises(PacketError, match="packet_failure_state_refused"):
        validate_packet(source)


@pytest.mark.parametrize("status", ["failed", "interrupted", "rejected", "pending", "uncertain"])
def test_positive_revision_relation_requires_original_invalid_status(status):
    source = packet()
    source["failures"][0].update(status=status, relation="prior_refusal_in_bound_revision")
    with pytest.raises(PacketError, match="packet_failure_state_refused"):
        validate_packet(source)


@pytest.mark.parametrize("state", sorted(FAILURE_ARTIFACT_STATES))
def test_failure_and_recorded_disposition_evidence_states_are_preserved_without_upgrade(state):
    source = packet()
    source["failures"][0].update(disposition_recorded=True, artifact_state=state,
                                  disposition_artifact_state=state)
    checked = validate_packet(source)["failures"][0]
    assert checked["artifact_state"] == state
    assert checked["disposition_artifact_state"] == state
    assert checked["provisional"] is True
    assert checked["status"] == "invalid"
    assert checked["disposition"] == "unresolved"


@pytest.mark.parametrize("relation", sorted(FAILURE_RELATIONS))
def test_relation_does_not_rewrite_historical_status_or_default_disposition(relation):
    source = packet()
    source["failures"][0]["relation"] = relation
    checked = validate_packet(source)["failures"][0]
    assert checked["status"] == "invalid"
    assert checked["disposition"] == "unresolved"
    assert checked["disposition_recorded"] is False
    assert checked["relation"] == relation


@pytest.mark.parametrize("state", ["verified", "unavailable", "not_allowed", "verification_bound"])
def test_recorded_corrected_claim_keeps_provisional_and_evidence_availability(state):
    source = packet()
    source["failures"][0].update(disposition="corrected", disposition_recorded=True,
                                  disposition_artifact_state=state)
    checked = validate_packet(source)["failures"][0]
    assert checked["status"] == "invalid"
    assert checked["disposition"] == "corrected"
    assert checked["provisional"] is True
    assert checked["disposition_artifact_state"] == state


@pytest.mark.parametrize("private", [
    "/private/failure.json", "2026-11-02", "provider-record-AAPL", "sk-ant-private",
    "a" * 64, [100.5, 101.5], {"prices": [100, 101], "dates": ["2026-11-02"]},
])
def test_new_failure_fields_have_no_private_data_or_free_prose_channel(private):
    for field in ("artifact_state", "disposition_artifact_state", "relation",
                  "disposition_recorded", "provisional"):
        source = packet()
        source["failures"][0][field] = private
        with pytest.raises(PacketError) as exc:
            packet_messages(source)
        assert str(private) not in str(exc.value)


@pytest.mark.parametrize("extra", [
    {"fix_artifact_ref": "a" * 64}, {"request_sha256": "b" * 64},
    {"failure_id": "private-provider-id"}, {"rationale": "private failure prose"},
    {"date": "2026-11-02"}, {"prices": [100, 101]}, {"predicate_holds": True},
    {"reviewed_repair": True},
])
def test_failure_context_refuses_extra_reference_outcome_and_review_claim_fields(extra):
    source = packet()
    source["failures"][0].update(extra)
    with pytest.raises(PacketError, match="packet_fields_refused"):
        validate_packet(source)


@pytest.mark.parametrize("role", ROLES)
def test_failure_relation_and_verified_bytes_do_not_preclude_stop_or_block(role):
    source = packet(role)
    source["failures"][0].update(relation="prior_refusal_in_bound_revision",
                                  disposition="corrected", disposition_recorded=True,
                                  artifact_state="verified", disposition_artifact_state="verified")
    validate_packet(source)
    decision = "stop" if role in ROLES[:3] else "block"
    checked = parse(output(role, decision=decision), role=role,
                    required=PREDICATE if role in ROLES[2:] else None)
    assert checked["decision"] == decision


def test_finite_vocabularies_and_duplicate_failure_aliases():
    assert "unsupported_due_bill" in FAILURE_CODES
    assert "hidden_values_unreviewed" in FINDING_CODES
    p = packet()
    p["failures"] *= 2
    with pytest.raises(PacketError):
        validate_packet(p)


def test_raw_model_rationale_is_retained_privately_and_never_forwarded():
    private = "Prices [100,101]; 2026-11-01; provider-AAPL; /private/data; sk-ant-private"
    parsed = parse(output(rationale=private))
    assert parsed["rationale"] == private
    projected = project_role_output(parsed)
    p = packet("engineer", prior_outputs=[projected])
    serialized = json.dumps(packet_messages(p))
    assert private not in serialized
    assert "rationale" not in json.dumps(projected)
    assert "2026-11-01" not in serialized
    assert "provider-AAPL" not in serialized
    assert "/private/data" not in serialized
    p["prior_outputs"] = [parsed]
    with pytest.raises(PacketError):
        validate_packet(p)


@pytest.mark.parametrize("prior", [
    [project_role_output(output("hypothesis"))],
    [project_role_output(output("director")), project_role_output(output("director"))],
    [project_role_output(output("engineer")), project_role_output(output("director"))],
])
def test_prior_roles_cannot_impersonate_current_future_duplicate_or_reordered_roles(prior):
    with pytest.raises(PacketError):
        validate_packet(packet("hypothesis", prior_outputs=prior))


def test_later_packets_require_actual_hypothesis_selection_and_consistent_prior_predicates():
    with pytest.raises(PacketError):
        validate_packet(packet("engineer", prior_outputs=[]))
    with pytest.raises(PacketError):
        validate_packet(packet("engineer", prior_outputs=[
            project_role_output(output(decision="stop", predicate=None))]))
    p = packet("quality")
    p["prior_outputs"].append(project_role_output(output(
        "data_critic", predicate="cost_fees_nondecreasing")))
    with pytest.raises(PacketError):
        validate_packet(p)


def test_prior_aliases_are_checked_against_this_packets_issued_scope():
    p = packet("engineer")
    p["prior_outputs"][-1]["artifact_aliases"] = ["artifact-3"]
    with pytest.raises(PacketError):
        validate_packet(p)


@pytest.mark.parametrize("role", ROLES[2:])
def test_engineer_and_critics_require_exact_selected_predicate(role):
    with pytest.raises(PacketError):
        parse(role=role)
    with pytest.raises(PacketError):
        parse(role=role, required="cost_fees_nondecreasing")
    with pytest.raises(PacketError):
        parse(output(role, predicate=None), role=role, required=PREDICATE)


@pytest.mark.parametrize("changes", [
    {"schema_version": True}, {"role": "director"}, {"decision": "execute"},
    {"predicate": None}, {"predicate": "price_rise"}, {"predicate": [100, 101]},
    {"artifact_aliases": ["artifact-3"]}, {"artifact_aliases": ["artifact-1", "artifact-1"]},
    {"findings": [{"code": "provider-data-valid", "artifact_aliases": []}]},
    {"findings": [{"code": "method_consistent", "artifact_aliases": ["artifact-2"]}]},
    {"findings": [{"code": "method_consistent", "artifact_aliases": [], "date": "2026-11-01"}]},
    {"findings": ["free prose"]}, {"rationale": ""}, {"rationale": " "},
    {"rationale": ["prose"]}, {"rationale": "x" * 2001},
    {"rationale": "\ud800"}, {"extra": {"prices": [1, 2]}},
])
def test_role_output_rejects_unknown_fields_types_codes_aliases_and_long_rationale(changes):
    with pytest.raises(PacketError):
        parse(output(**changes))


def test_findings_and_collection_bounds():
    finding = {"code": "method_consistent", "artifact_aliases": []}
    for changes in ({"findings": [deepcopy(finding), deepcopy(finding)]},
                    {"findings": [finding] * 9}):
        with pytest.raises(PacketError):
            parse(output(**changes))
    with pytest.raises(PacketError):
        parse(aliases=["artifact-1", "artifact-1"])
    with pytest.raises(PacketError):
        parse(predicates=[])
    with pytest.raises(PacketError):
        parse(predicates=[PREDICATE, "unregistered"])
    with pytest.raises(PacketError):
        parse(aliases="artifact-1")


@pytest.mark.parametrize("raw", [
    "{}", "[]", "null", "true", "1", "", "{", "{\"schema_version\":1,",
    "```json\n{}\n```", "{} trailing prose", "{} {}",
    '{"schema_version":1,"schema_version":1}',
    '{"schema_version":NaN}', '{"schema_version":Infinity}',
    '{"schema_version":-Infinity}', '{"schema_version":1e999}',
    "[" * 1500 + "]" * 1500, " " * (MAX_OUTPUT_BYTES + 1),
])
def test_json_parser_rejects_nonobjects_duplicate_keys_nonfinite_truncated_and_oversize(raw):
    with pytest.raises(PacketError):
        parse_role_output(raw, "hypothesis", ["artifact-1"], [PREDICATE])


def test_nested_duplicate_keys_cannot_be_last_value_wins():
    raw = json.dumps(output()).replace(
        '"code": "hidden_values_unreviewed"',
        '"code": "private_provider_id", "code": "hidden_values_unreviewed"')
    with pytest.raises(PacketError):
        parse_role_output(raw, "hypothesis", ["artifact-1"], [PREDICATE])


def test_bounded_prior_output_envelope_refuses_even_individually_valid_large_projections():
    aliases = [f"artifact-{i}" for i in range(1, 33)]
    prior = []
    for role in ROLES[:-1]:
        prior.append(project_role_output(output(
            role, artifact_aliases=aliases,
            findings=[{"code": code, "artifact_aliases": aliases}
                      for code in sorted(FINDING_CODES)[:8]])))
    with pytest.raises(PacketError, match="packet_size_refused"):
        validate_packet(packet("scope", artifact_aliases=aliases, prior_outputs=prior))


def test_fixed_error_text_does_not_echo_submitted_private_value():
    private = "/private/secret-provider-prices-2026-11-01.json"
    for action in (
        lambda: validate_packet(packet(method=private)),
        lambda: parse(output(predicate=private)),
        lambda: parse_role_output(private, "hypothesis", ["artifact-1"], [PREDICATE]),
    ):
        with pytest.raises(PacketError) as exc:
            action()
        assert private not in str(exc.value)


def test_director_cannot_preselect_and_hypothesis_must_select_when_proposing():
    with pytest.raises(PacketError):
        parse(output("director", predicate=PREDICATE), role="director")
    assert parse(output(decision="stop", predicate=None))["decision"] == "stop"
    with pytest.raises(PacketError):
        parse(required=PREDICATE)


def test_parser_refuses_nonstring_and_projection_never_trusts_arbitrary_output():
    with pytest.raises(PacketError):
        parse_role_output(output(), "hypothesis", ["artifact-1"], [PREDICATE])
    with pytest.raises(PacketError):
        project_role_output(output(artifact_aliases=["private-provider-id"]))
    with pytest.raises(PacketError):
        project_role_output({"rationale": "raw prose"})


def test_already_projected_outputs_can_be_bound_without_inventing_rationale():
    scope = {"allowed_aliases": ["artifact-1"], "allowed_predicates": [PREDICATE]}
    projected = project_role_output(output())
    assert validate_projection(projected, **scope) == projected
    assert validate_projection(projected, required_predicate=PREDICATE, **scope) == projected
    engineer = project_role_output(output("engineer"))
    assert validate_projection(engineer, required_predicate=PREDICATE, **scope) == engineer
    with pytest.raises(PacketError):
        validate_projection(engineer, **scope)
    with pytest.raises(PacketError):
        validate_projection(output(), **scope)
    with pytest.raises(PacketError):
        validate_projection(projected, allowed_aliases=[], allowed_predicates=PREDICATES)
    with pytest.raises(PacketError):
        validate_projection(projected, required_predicate="cost_fees_nondecreasing",
                            allowed_aliases=["artifact-1"], allowed_predicates=PREDICATES)

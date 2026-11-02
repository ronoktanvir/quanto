"""Synthetic adversarial tests of the fixed D008 method-only packet vocabulary."""

from copy import deepcopy
import json

import pytest

from quanto.research_packets import (
    FAILURE_CODES, FINDING_CODES, MAX_OUTPUT_BYTES, MAX_PACKET_BYTES, PREDICATES,
    SYSTEM_PROMPT, PacketError, packet_messages, parse_role_output,
    project_role_output, validate_packet, validate_projection,
)
from quanto.research_workflow import ROLES


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
        "method": "frozen_trailing_return_next_open_three_costs", "scope": "development_only",
        "data_values_disclosed": False, "allowed_predicates": sorted(PREDICATES),
        "artifact_aliases": ["artifact-1", "artifact-2"],
        "failures": [{"alias": "failure-1", "code": "unsupported_due_bill",
                      "status": "invalid", "disposition": "unresolved"}],
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

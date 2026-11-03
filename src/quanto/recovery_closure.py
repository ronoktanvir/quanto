"""Bounded structural evidence inventory; no domain replay or recovery approval.

The returned graph is private. Use public_projection for display. Origin selects
the profile: untrusted document tags never authorize new interpretation or I/O.
"""
from __future__ import annotations

from collections import deque
from dataclasses import MISSING, dataclass, fields as dataclass_fields, is_dataclass, replace
from pathlib import Path
import marshal
import platform
import re
import sqlite3
import sys
import time
from types import CodeType, FunctionType, ModuleType

from quanto import recovery

PROFILE = "research_closure_subset_v1"
FLAGS = {"typed_closure_complete": False, "full_recovery_accepted": False,
         "historical_replay_verified": False, "execution_enabled": False}


class ClosureError(ValueError):
    """Fixed reason codes only; never record values, paths or SQL diagnostics."""


@dataclass(frozen=True)
class ClosureLimits:
    snapshot: recovery.Limits = recovery.Limits()
    edges: int = 20_000
    nodes: int = 20_000
    json_items: int = 200_000
    depth: int = 64
    graph_hops: int = 64
    seconds: float = 45.0


def _need(condition, code="malformed_supported_profile"):
    if not condition:
        raise ClosureError(code)


def _digest(value):
    _need(type(value) is str and recovery.DIGEST.fullmatch(value), "invalid_reference")
    return value


def _object(value, required, optional=()):
    _need(type(value) is dict and set(required) <= set(value) <= set(required) | set(optional))


def _text(value):
    _need(type(value) is str and 0 < len(value) <= 1024)


def _loaded_value(value, stack=()):
    """Portable loaded-code identity, not hostile same-process attestation."""
    _need(len(stack) < 64, "implementation_identity_limit")
    if value is MISSING:
        return ["dataclass_missing"]
    if value is None or type(value) in (str, bool, int):
        return [type(value).__name__, value]
    if type(value) is float:
        return ["float", value.hex()]
    if type(value) is bytes:
        return ["bytes", value.hex()]
    if id(value) in stack:
        return ["cycle", type(value).__module__, type(value).__qualname__]
    stack = (*stack, id(value))
    if type(value) in (tuple, list, set, frozenset):
        result = [_loaded_value(item, stack) for item in value]
        return [type(value).__name__, sorted(result, key=recovery._json)
                if type(value) in (set, frozenset) else result]
    if type(value) is dict:
        return ["dict", sorted([[_loaded_value(key, stack), _loaded_value(item, stack)]
                                for key, item in value.items()], key=recovery._json)]
    if isinstance(value, re.Pattern):
        return ["pattern", value.pattern, value.flags]
    if isinstance(value, Path):
        return ["path_value", str(value)]  # No read or following a saved path.
    if isinstance(value, ModuleType):
        return ["module_dependency", value.__name__]
    if isinstance(value, FunctionType):
        def portable(code):
            return code.replace(co_filename="<module>", co_consts=tuple(
                portable(item) if isinstance(item, CodeType) else item for item in code.co_consts))
        closure = []
        for cell in value.__closure__ or ():
            try:
                content = cell.cell_contents
            except ValueError:
                closure.append(["empty_cell"])
            else:
                closure.append(_loaded_value(content, stack))
        return ["function", recovery._sha(marshal.dumps(portable(value.__code__), 2)),
                _loaded_value(value.__defaults__, stack), _loaded_value(value.__kwdefaults__, stack), closure]
    if isinstance(value, type):
        if value.__module__ == "builtins":
            return ["builtin_type", value.__qualname__]
        methods = {name: _loaded_value(item.__func__ if isinstance(item, (staticmethod, classmethod)) else item, stack)
                   for name, item in vars(value).items()
                   if isinstance(item, (FunctionType, staticmethod, classmethod))}
        defaults = []
        if is_dataclass(value):
            for field in dataclass_fields(value):
                defaults.append([field.name, _loaded_value(field.default, stack) if field.default is not MISSING else ["missing"],
                                 _loaded_value(field.default_factory, stack) if field.default_factory is not MISSING else ["missing"]])
        return ["class", value.__module__, value.__qualname__,
                [[base.__module__, base.__qualname__] for base in value.__bases__], methods, defaults]
    if is_dataclass(value):
        return ["dataclass_value", type(value).__module__, type(value).__qualname__,
                [[field.name, _loaded_value(getattr(value, field.name), stack)] for field in dataclass_fields(value)]]
    raise ClosureError("unsupported_implementation_identity")


def _implementation_identity():
    result = {}
    for role, module in (("inspector", sys.modules[__name__]), ("recovery", recovery)):
        raw = recovery._read(Path(module.__file__).absolute(), 2 * 1024 * 1024)
        source = recovery._sha(raw)
        _need(source == _SOURCE_AT_IMPORT[role], "implementation_source_changed")
        names = _OWN_NAMES[role] | {name for name, value in vars(module).items()
                 if (isinstance(value, (FunctionType, type)) and value.__module__ == module.__name__)
                 or (name.isupper() and name not in {"_SOURCE_AT_IMPORT", "_OWN_NAMES"})}
        loaded = {name: _loaded_value(getattr(module, name)) if hasattr(module, name) else ["missing"]
                  for name in sorted(names)}
        result[role + "_source_sha256"] = source
        result[role + "_loaded_sha256"] = recovery._sha(recovery._json(loaded))
    result["runtime"] = {"python_version": platform.python_version(),
                         "python_implementation": sys.implementation.name,
                         "sqlite_version": sqlite3.sqlite_version, "fingerprint_marshal_version": 2}
    return result


KINDS = {"dataset": "explorer_dataset", "suite": "study_suite",
         "roster": "study_suite_run_roster", "summary": "study_suite_summary",
         "result": "exploratory_result"}
SUPPORTED = {*KINDS, "bars"}
DIRECT = {
    "explorer_datasets": {"manifest_sha256": "dataset"},
    "explorer_exposures": {"dataset_sha256": "dataset"},
    "study_suite_runs": {"suite_sha256": "suite", "roster_sha256": "roster"},
    "research_comparisons": {"registration_sha256": "comparison_registration"},
    "research_broker_runs": {"configuration_sha256": "broker_configuration"},
    "research_broker_aliases": {"artifact_sha256": "declared"},
    "research_broker_stages": {"record_sha256": "broker_stage"},
    "research_broker_tool_requests": {"request_sha256": "broker_tool_request"},
    "research_private_responses": {"artifact_sha256": "private_model_response"},
    "workflow_handoffs": {"document_sha256": "workflow_handoff"},
    "failure_memory_dispositions": {"fix_artifact_ref": "declared"},
}
DETAILS = {
    "dataset_registration": {"manifest_sha256": "dataset"},
    "study_suite_registration": {"suite_sha256": "suite"},
    "study_suite_run": {"suite_sha256": "suite", "summary_sha256": "summary"},
    "exploratory_study": {"artifact_sha256": "result", "dataset_sha256": "dataset",
                          "admission_sha256": "admission", "suite_sha256": "suite",
                          "policy_revision_sha256": "policy_revision"},
}
REQUIRED_SUCCESS = {"dataset_registration": "manifest_sha256",
                    "study_suite_registration": "suite_sha256",
                    "study_suite_run": "summary_sha256", "exploratory_study": "artifact_sha256"}
EVENT_REFS = {
    "acquisition_request_prepared": {"request_sha256": "acquisition_request"},
    "acquisition_page_received": {"raw_sha256": "opaque_provider_page"},
    "workflow_broker_packet_bound": {
        "configuration_sha256": "broker_configuration", "packet_sha256": "model_context",
        "verification_sha256": "broker_verification", "failure_context_sha256": "failure_context",
        "failure_basis_sha256": "failure_basis"},
    "workflow_broker_failure_basis_bound": {
        "configuration_sha256": "broker_configuration", "basis_sha256": "failure_basis"},
    "explorer_dataset_registered": {"manifest_sha256": "dataset"},
    "study_suite_run_registered": {"suite_sha256": "suite", "roster_sha256": "roster"},
}
# Versionless event names require recorded producer identity, not key-shape
# inference. Exact public writer revisions are retained in the review plan.
PACKET_PRODUCERS = {
    "c59a3801d41a68811231d640bc9dbd69e8a7ce933ab855e8f011f969d4654af7": "legacy_038",
    "d26ca8496ab50cb7536b28e2623fd4d8902d67ba3a3c7a93da9be01349924630": "legacy_038",
    "aa4f9e93f9fc471273bf2e6c1a0d67acb74583228618cecd17aa9ec513419e34": "current_9ed",
}
PACKET_WORKFLOW_SOURCE = "64ca63f155a2417021bb8632673f14ec12ff7d497881aa13a95d7330911ab02b"
PACKET_BASE = {"configuration_sha256", "packet_sha256", "verification_sha256"}
PACKET_FAILURE = {"failure_context_sha256", "failure_basis_sha256"}
PACKET_METADATA = {"parent_submission_id", "assignment_id", "role", "fence", "request_id"}
DATASET_FIELDS = {
    "schema_version", "kind", "evidence_kind", "source_sha256", "bars_sha256", "market", "symbol",
    "price_basis", "sessions", "coverage_start", "coverage_end", "exposure_start", "exposure_end",
    "bar_count", "parent_dataset_sha256", "admission_status", "development_policy", "prior_exposure",
    "calendar_status", "corporate_actions", "timing", "rights"}
RESULT_FIELDS = {
    "schema_version", "result_kind", "evidence_kind", "investment_evidence", "dataset_sha256",
    "frozen_request", "code_identity", "development_policy", "prior_exposure", "engine_report",
    "admission_sha256", "admission_limitations", "admission_evidence", "study_suite"}


class _Reader:
    def __init__(self, snapshot, manifest, db, limits, deadline):
        self.path, self.manifest, self.db = snapshot, manifest, db
        self.limits, self.deadline = limits, deadline
        self.objects = manifest["objects"]
        self.tombstones = set(manifest["coverage"]["tombstones"])
        self.tables = manifest["database_state"]["tables"]
        self.queue, self.visited, self.edges, self.unsupported = deque(), set(), [], set()
        self.distances, self.current_hops = {}, -1
        self.nodes, self.rows_read, self.json_items = [], 0, 0
        self.broker_runs = None

    def tick(self):
        _need(time.monotonic() < self.deadline, "closure_deadline")

    def gap(self, reason, origin):
        self.unsupported.add((reason, origin))
        _need(len(self.unsupported) <= self.limits.nodes, "closure_node_limit")

    def parse(self, raw):
        self.tick()
        value = recovery._parse(raw)
        pending = [(value, 0)]
        while pending:
            item, depth = pending.pop()
            self.json_items += 1
            _need(depth <= self.limits.depth, "closure_depth_limit")
            _need(self.json_items <= self.limits.json_items, "closure_json_limit")
            self.tick()
            if type(item) is dict:
                pending.extend((child, depth + 1) for child in item.values())
            elif type(item) is list:
                pending.extend((child, depth + 1) for child in item)
        return value

    def rows(self, table):
        if table not in self.tables:
            return
        if table in self.manifest["database_state"]["unknown_schema_tables"]:
            self.gap("unsupported_table_schema", table)
            return
        columns = self.tables[table]["columns"]
        ordered = []
        for row in self.db.execute('SELECT * FROM "' + table + '"'):
            self.rows_read += 1
            _need(self.rows_read <= self.limits.snapshot.rows * 4, "closure_row_limit")
            self.tick()
            ordered.append((recovery._json([recovery._value(value) for value in row]), row))
        # SQLite does not promise scan order. Type-tagged canonical row order
        # also distinguishes values that SQL comparison might consider equal.
        ordered.sort(key=lambda item: item[0])
        for _, row in ordered:
            self.tick()
            yield dict(zip(columns, row, strict=True))

    def edge(self, parent, field, digest, role="declared", kind="required_object"):
        self.tick()
        _digest(digest)
        _need(len(self.edges) < self.limits.edges, "closure_edge_limit")
        availability = "identity_only"
        if kind == "required_object":
            availability = "tombstoned" if digest in self.tombstones else "available"
            _need(digest in self.objects or digest in self.tombstones, "required_object_missing")
            if availability == "tombstoned":
                self.gap("required_tombstoned_object", digest)
            elif (digest, role) not in self.distances:
                # All roots are enqueued before BFS. Repeated origin-role nodes
                # retain their shortest root distance, without cyclic growth.
                hops = self.current_hops + 1
                _need(hops <= self.limits.graph_hops, "closure_graph_hops_limit")
                self.distances[digest, role] = hops
                self.queue.append((digest, role))
                _need(len(self.queue) <= self.limits.edges, "closure_edge_limit")
        elif kind == "external_evidence":
            self.gap("external_evidence_required", parent + ":" + field)
        self.edges.append({"parent": parent, "field": field, "digest": digest,
                           "role": role, "edge_type": kind, "availability": availability})

    def refs(self, parent, field, values):
        _need(type(values) is list)
        for index, value in enumerate(values):
            self.edge(parent, f"{field}/{index}", value)

    def inline(self, parent, field, digest, value):
        _need(recovery._sha(recovery._json(value)) == _digest(digest), "inline_identity_mismatch")
        self.edge(parent, field, digest, "inline", "inline_identity")

    def roots(self):
        for table in self.manifest["database_state"]["unknown_schema_tables"]:
            self.gap("unsupported_table_schema", table)
        for table, fields in DIRECT.items():
            for index, row in enumerate(self.rows(table)):
                for field, role in fields.items():
                    if row[field] is not None:
                        self.edge(f"{table}/{index}", field, row[field], role)
        for table, field in recovery.ARRAY_REFS.items():
            for index, row in enumerate(self.rows(table)):
                self.refs(f"{table}/{index}", field, self.parse(row[field]))
        for index, row in enumerate(self.rows("study_suite_launches")):
            self.edge(f"study_suite_launches/{index}", "request_sha256", row["request_sha256"],
                      "recorded_request_identity", "inline_identity")
            self.gap("launch_roster_binding_not_checked", "study_suite_launches")
        for index, row in enumerate(self.rows("research_dispatch_holds")):
            for field in ("packet_sha256", "body_sha256"):
                self.edge(f"research_dispatch_holds/{index}", field, row[field],
                          "dispatch_identity", "inline_identity")
            self.gap("dispatch_binding_not_checked", "research_dispatch_holds")
        submissions = {row["submission_id"]: row for row in self.rows("provenance_submissions")}
        for identity, row in submissions.items():
            self.edge("submission/" + identity, "request_sha256", row["request_sha256"],
                      "recorded_request_identity", "inline_identity")
            if row["kind"] not in DETAILS:
                self.gap("unsupported_submission_kind", row["kind"])
        for row in self.rows("provenance_outcomes"):
            parent = "submission/" + row["submission_id"]
            data = self.parse(row["details"])
            _need(type(data) is dict)
            self.refs(parent, "artifact_refs", data.get("artifact_refs", []))
            source = submissions.get(row["submission_id"])
            _need(source is not None, "missing_database_binding")
            kind = source["kind"]
            if row["status"] == "success" and kind in REQUIRED_SUCCESS:
                _need(REQUIRED_SUCCESS[kind] in data)
            for field, role in DETAILS.get(kind, {}).items():
                if data.get(field) is not None:
                    self.edge(parent, field, data[field], role)
            # Details carry producer-specific metadata beyond this finite root subset.
            self.gap("submission_details_semantics_not_checked", kind)
        for index, row in enumerate(self.rows("workflow_runs")):
            data = self.parse(row["manifest"])
            _need(type(data) is dict)
            self.refs(f"workflow_runs/{index}", "input_refs", data.get("input_refs", []))
            self.gap("unsupported_inline_workflow_manifest", "workflow_runs")
        for index, row in enumerate(self.rows("workflow_handoffs")):
            data = self.parse(row["document"])
            _need(type(data) is dict)
            for field in ("artifact_refs", "reviewed_refs"):
                self.refs(f"workflow_handoffs/{index}", field, data.get(field, []))
            _need(type(data.get("objections", [])) is list)
            for item in data.get("objections", []):
                _need(type(item) is dict)
                self.refs(f"workflow_handoffs/{index}", "objections/artifact_refs", item.get("artifact_refs", []))
        explorer_attempts = {row["attempt_id"] for row in self.rows("explorer_executions")}
        for index, row in enumerate(self.rows("outcomes")):
            if row["attempt_id"] not in explorer_attempts:
                self.gap("unsupported_outcome_origin", "outcomes")
                continue
            data = self.parse(row["result"])
            _need(type(data) is dict)
            if "artifact_sha256" in data:
                _need("artifact_path" not in data)
                self.edge(f"outcomes/{index}", "artifact_sha256", data["artifact_sha256"],
                          "result")
            self.gap("outcome_origin_semantics_not_checked", "outcomes")
        for index, row in enumerate(self.rows("reviews")):
            self.edge(f"reviews/{index}", "artifact_hash", row["artifact_hash"],
                      "recorded_review_identity", "inline_identity")
            # findings is arbitrary canonical JSON. Its key spelling does not
            # identify critic.py or any other producer or external file schema.
            self.gap("unsupported_review_record", "reviews")
        for row in self.rows("events"):
            kind, parent = row["kind"], "event/" + str(row["id"])
            if kind not in EVENT_REFS:
                self.gap("unsupported_event_profile", kind)
                continue
            data = self.parse(row["payload"])
            _need(type(data) is dict)
            if kind == "workflow_broker_packet_bound":
                self.packet_references(parent, data)
            elif kind == "workflow_broker_failure_basis_bound":
                self.failure_basis_references(parent, data)
            else:
                for field, role in EVENT_REFS[kind].items():
                    _need(field in data)
                    self.edge(parent, field, data[field], role)
            self.gap("event_binding_semantics_not_checked", kind)

    def packet_producer(self, parent, data):
        """Select the shared broker-event writer pair, never infer it from keys."""
        identity = data.get("parent_submission_id")
        if type(identity) is not str or not identity:
            self.gap("unresolved_packet_producer_binding", parent)
            return None
        if self.broker_runs is None:
            self.broker_runs = {}
            for row in self.rows("research_broker_runs"):
                key = row["submission_id"]
                _need(key not in self.broker_runs, "event_producer_binding_mismatch")
                self.broker_runs[key] = row
        row = self.broker_runs.get(identity)
        if row is None:
            self.gap("unresolved_packet_producer_binding", parent)
            return None
        digest = data["configuration_sha256"]
        _need(row["configuration_sha256"] == digest, "event_producer_binding_mismatch")
        if digest in self.tombstones:
            self.gap("unavailable_packet_producer_configuration", parent)
            return None
        raw = recovery._read(self.path / "objects" / (digest + ".bin"),
                             self.limits.snapshot.object_bytes, private=True)
        _need(recovery._sha(raw) == digest, "object_changed")
        configuration = self.parse(raw)
        _need(type(configuration) is dict)
        code = configuration.get("code_identity")
        if code is None:
            self.gap("unsupported_packet_configuration_profile", parent)
            return None
        _object(code, {"sources", "python", "implementation"})
        _need(recovery._sha(recovery._json(code)) == _digest(row["code_sha256"]),
              "event_producer_binding_mismatch")
        _text(code["python"])
        _text(code["implementation"])
        sources = code["sources"]
        _need(type(sources) is dict and 0 < len(sources) <= 32)
        for name, source in sources.items():
            _text(name)
            self.edge(digest, "code_identity/sources/" + name, source,
                      "historical_source", "external_evidence")
        profile = PACKET_PRODUCERS.get(sources.get("research_broker.py"))
        if profile is None or sources.get("research_workflow.py") != PACKET_WORKFLOW_SOURCE:
            self.gap("unsupported_packet_producer_identity", parent)
            return None
        return profile

    def failure_basis_references(self, parent, data):
        fields = EVENT_REFS["workflow_broker_failure_basis_bound"]
        for field, role in fields.items():
            _need(field in data)
            self.edge(parent, field, data[field], role)
        profile = self.packet_producer(parent, data)
        _need(profile != "legacy_038", "event_producer_binding_mismatch")
        if profile is None:
            self.gap("failure_basis_profile_origin_unresolved", parent)
            return
        _object(data, {"parent_submission_id", "assignment_id", "request_id", "fence", *fields})
        for field in ("parent_submission_id", "assignment_id", "request_id"):
            _text(data[field])
        _need(type(data["fence"]) is int and data["fence"] > 0)

    def packet_references(self, parent, data):
        fields = EVENT_REFS["workflow_broker_packet_bound"]
        # These references occur in every documented generation. Even an
        # unbound event cannot erase them or invent a missing object.
        for field in sorted(PACKET_BASE):
            _need(field in data)
            self.edge(parent, field, data[field], fields[field])
        present = PACKET_FAILURE & data.keys()
        _need(not present or present == PACKET_FAILURE)
        profile = self.packet_producer(parent, data)
        if profile is not None:
            expected = PACKET_METADATA | PACKET_BASE
            if profile == "current_9ed":
                expected |= PACKET_FAILURE
            _object(data, expected)
            for field in PACKET_METADATA - {"fence"}:
                _text(data[field])
            _need(type(data["fence"]) is int and data["fence"] > 0)
            _need(data["role"] in {"director", "hypothesis", "engineer", "data_critic", "statistical_critic", "quality", "scope"})
            if profile == "legacy_038":
                self.gap("legacy_packet_missing_modern_failure_evidence", parent)
            else:
                _need((data["failure_basis_sha256"] is None) == (data["role"] == "director"))
        else:
            # This inventories unambiguous present references, without calling
            # an unknown/missing producer a verified historical profile.
            self.gap("packet_profile_origin_unresolved", parent)
            if not present:
                self.gap("unbound_packet_missing_modern_failure_evidence", parent)
        for field in sorted(present):
            if field == "failure_basis_sha256" and data[field] is None:
                continue
            self.edge(parent, field, data[field], fields[field])

    def members(self, parent, values, role):
        _need(type(values) is list and len(values) == 3)
        costs = []
        for index, member in enumerate(values):
            path = f"members/{index}"
            _object(member, {"cost_bps", "request", "request_sha256"}, {"outcome"} if role == "summary" else ())
            cost = member["cost_bps"]
            _need(type(cost) is int and cost in (0, 10, 25))
            costs.append(cost)
            request = member["request"]
            fields = {"dataset_sha256", "study_name", "evaluation_start", "evaluation_end", "specification", "admission_sha256"}
            _object(request, fields | ({"suite_sha256"} if role != "suite" else set()))
            _need(type(request["specification"]) is dict and request["specification"].get("cost_bps") == cost)
            for field in ("study_name", "evaluation_start", "evaluation_end"):
                _text(request[field])
            self.inline(parent, path + "/request_sha256", member["request_sha256"], request)
            for field, child in (("dataset_sha256", "dataset"), ("admission_sha256", "admission"), ("suite_sha256", "suite")):
                if field in request:
                    self.edge(parent, path + "/request/" + field, request[field], child)
            if role == "summary":
                _need("outcome" in member and type(member["outcome"]) is dict)
                outcome = member["outcome"]
                _object(outcome, {"status"}, {"phase", "dispatch_status", "error_code", "submission_id", "attempt_id", "fingerprint", "artifact_sha256"})
                _text(outcome["status"])
                if "artifact_sha256" in outcome:
                    self.edge(parent, path + "/outcome/artifact_sha256", outcome["artifact_sha256"], "result")
        _need(costs == [0, 10, 25])

    def dataset(self, digest, data):
        _object(data, DATASET_FIELDS)
        _need(type(data["market"]) is dict and type(data["sessions"]) is list
              and type(data["bar_count"]) is int and data["bar_count"] == len(data["sessions"]) > 0)
        _object(data["market"], {"instrument_id", "venue", "currency", "session_timezone"})
        for value in data["market"].values():
            _text(value)
        for field in DATASET_FIELDS - {"schema_version", "market", "sessions", "bar_count", "parent_dataset_sha256"}:
            _text(data[field])
        for session in data["sessions"]:
            _text(session)
        self.edge(digest, "source_sha256", data["source_sha256"], "dataset_source")
        self.edge(digest, "bars_sha256", data["bars_sha256"], "bars")
        if data["parent_dataset_sha256"] is not None:
            self.edge(digest, "parent_dataset_sha256", data["parent_dataset_sha256"], "dataset")
        self.gap("dataset_market_semantics_not_checked", digest)

    def bars(self, _digest_value, data):
        _object(data, {"schema_version", "bars"})
        _need(type(data["bars"]) is list)
        for bar in data["bars"]:
            _object(bar, {"timestamp", "symbol", "open", "high", "low", "close", "volume"})
            _text(bar["timestamp"])
            _text(bar["symbol"])
            for field in ("open", "high", "low", "close", "volume"):
                _need(type(bar[field]) in (int, float))

    def suite_family(self, digest, data, role):
        common = {"schema_version", "kind", "submission_id", "members"}
        if role == "suite":
            _object(data, common | {"registration_request_sha256", "policy_revision_sha256", "artifact_refs"})
            self.edge(digest, "registration_request_sha256", data["registration_request_sha256"], "suite_request")
            self.edge(digest, "policy_revision_sha256", data["policy_revision_sha256"], "policy_revision")
        elif role == "roster":
            _object(data, common | {"suite_sha256", "run_request_sha256"})
            self.edge(digest, "run_request_sha256", data["run_request_sha256"], "suite_run_request")
        else:
            _object(data, common | {"suite_sha256", "roster_sha256", "complete", "all_success", "artifact_refs"})
            _need(type(data["complete"]) is bool and type(data["all_success"]) is bool)
            self.edge(digest, "roster_sha256", data["roster_sha256"], "roster")
        if role != "suite":
            self.edge(digest, "suite_sha256", data["suite_sha256"], "suite")
        _text(data["submission_id"])
        self.members(digest, data["members"], role)
        if "artifact_refs" in data:
            self.refs(digest, "artifact_refs", data["artifact_refs"])
        self.gap("suite_database_bindings_not_checked", digest)

    def result(self, digest, data):
        _object(data, RESULT_FIELDS)
        _need(data["investment_evidence"] is False)
        for field in ("evidence_kind", "development_policy", "prior_exposure"):
            _text(data[field])
        for field in ("frozen_request", "code_identity", "engine_report"):
            _need(type(data[field]) is dict)
        _need(type(data["admission_limitations"]) is list)
        for value in data["admission_limitations"]:
            _text(value)
        self.edge(digest, "dataset_sha256", data["dataset_sha256"], "dataset")
        if data["admission_sha256"] is not None:
            self.edge(digest, "admission_sha256", data["admission_sha256"], "admission")
        for field in ("admission_evidence", "study_suite"):
            _need(data[field] is None or type(data[field]) is dict)
            if data[field] is not None:
                self.gap("unsupported_embedded_" + field, digest)
        # This derived specification is not the original submission request.
        for field in ("frozen_request", "engine_report"):
            self.edge(digest, field, recovery._sha(recovery._json(data[field])), "inline", "inline_identity")
        self.gap("historical_source_environment_required", digest)
        identity = data["code_identity"]
        if "sources" in identity:
            _need(type(identity["sources"]) is dict)
            for name, source_digest in identity["sources"].items():
                _text(name)
                self.edge(digest, "code_identity/sources/" + name, source_digest,
                          "historical_source", "external_evidence")
        if identity.get("dependency_lock_sha256") is not None:
            self.edge(digest, "code_identity/dependency_lock_sha256", identity["dependency_lock_sha256"],
                      "historical_dependency_lock", "external_evidence")
        self.gap("embedded_result_semantics_not_checked", digest)

    def walk(self):
        while self.queue:
            self.tick()
            digest, role = self.queue.popleft()
            if (digest, role) in self.visited:
                continue
            self.visited.add((digest, role))
            self.current_hops = self.distances[digest, role]
            _need(len(self.visited) <= self.limits.nodes, "closure_node_limit")
            node = {"digest": digest, "role": role, "graph_hops": self.current_hops, "status": "unsupported"}
            self.nodes.append(node)
            if role == "declared":
                node["status"] = "declared_bytes_only"
                continue
            raw = recovery._read(self.path / "objects" / (digest + ".bin"), self.limits.snapshot.object_bytes, private=True)
            _need(recovery._sha(raw) == digest, "object_changed")
            if role == "opaque_provider_page":
                node["status"] = "opaque_leaf"
                continue
            if role not in SUPPORTED:
                self.gap("unsupported_object_role", digest + ":" + role)
                continue
            data = self.parse(raw)
            _need(type(data) is dict)
            version = data.get("schema_version")
            _need(type(version) is int and version > 0)
            if version != 1:
                self.gap("unsupported_schema_version", digest + ":" + role)
                continue
            if role in KINDS:
                kind = data.get("result_kind" if role == "result" else "kind")
                _text(kind)
                if kind != KINDS[role]:
                    _need(kind not in KINDS.values(), "profile_role_mismatch")
                    self.gap("unsupported_document_kind", digest + ":" + role)
                    continue
            if role in {"suite", "roster", "summary"}:
                self.suite_family(digest, data, role)
            else:
                getattr(self, role)(digest, data)
            node["status"] = "supported_structure_checked"
        typed = {digest for digest, role in self.visited if role != "declared"}
        for digest, role in self.visited:
            if role == "declared" and digest not in typed:
                self.gap("unclassified_declared_object", digest)
        for digest in set(self.objects) - {digest for digest, _ in self.visited}:
            self.gap("unclassified_orphan_inventory", digest)


def inspect_research_closure(snapshot: Path, *, expected_manifest_sha256: str,
                             expected_event_head: str | None = None,
                             limits: ClosureLimits = ClosureLimits()) -> dict:
    """Return private structural findings without writing or certifying recovery."""
    db = None
    try:
        _need(type(limits) is ClosureLimits, "invalid_limits")
        recovery._bounds(limits.snapshot)
        for field in ("edges", "nodes", "json_items", "depth", "graph_hops"):
            _need(type(getattr(limits, field)) is int and 0 < getattr(limits, field) <= getattr(ClosureLimits(), field), "invalid_limits")
        _need(type(limits.seconds) in (int, float) and 0 < limits.seconds <= 45, "invalid_limits")
        _digest(expected_manifest_sha256)
        if expected_event_head is not None:
            _digest(expected_event_head)
        deadline = time.monotonic() + limits.seconds
        implementation = _implementation_identity()
        snapshot = recovery._path(snapshot)
        def inspect():
            remaining = deadline - time.monotonic()
            _need(remaining > 0, "closure_deadline")
            return recovery.inspect_research_snapshot(snapshot, expected_manifest_sha256=expected_manifest_sha256,
                expected_event_head=expected_event_head,
                limits=replace(limits.snapshot, seconds=min(limits.snapshot.seconds, remaining)))
        original = inspect()
        raw = recovery._read(snapshot / "manifest.json", limits.snapshot.manifest_bytes, private=True)
        _need(recovery._sha(raw) == expected_manifest_sha256, "snapshot_changed")
        manifest = recovery._parse(raw)
        db = recovery._connect(snapshot / "research.sqlite", "ro", deadline, immutable=True)
        reader = _Reader(snapshot, manifest, db, limits, deadline)
        reader.roots()
        reader.walk()
        db.close()
        db = None
        _need(inspect() == original, "snapshot_changed")
        _need(_implementation_identity() == implementation, "loaded_implementation_changed")
        reader.tick()
        state = manifest["database_state"]
        report = {"format": PROFILE, "manifest_sha256": expected_manifest_sha256,
                  "event_head": state["events"]["head"], "schema_sha256": state["schema_sha256"],
                  "table_state_sha256": recovery._sha(recovery._json(state["tables"])),
                  **implementation,
                  "status": "incomplete",
                  "nodes": sorted(reader.nodes, key=lambda n: (n["digest"], n["role"])),
                  "edges": sorted(reader.edges, key=lambda e: recovery._json(e)),
                  "unsupported": [{"reason": reason, "origin": origin} for reason, origin in sorted(reader.unsupported)],
                  "omissions": list(recovery.OMISSIONS), **FLAGS}
        report["counts"] = {"nodes": len(report["nodes"]), "edges": len(report["edges"]),
                            "unsupported": len(report["unsupported"]),
                            "supported_nodes": sum(n["status"] == "supported_structure_checked" for n in reader.nodes),
                            "tombstoned_edges": sum(e["availability"] == "tombstoned" for e in reader.edges)}
        report["supported_profiles_verified"] = report["counts"]["supported_nodes"] > 0
        return report
    except ClosureError:
        raise
    except recovery.RecoveryError:
        raise ClosureError("snapshot_verification_failed") from None
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, RecursionError, OverflowError):
        raise ClosureError("closure_inspection_failed") from None
    finally:
        if db is not None:
            db.close()


def public_projection(report: dict) -> dict:
    """Fixed display fields: no private graph, record values, paths or origins."""
    try:
        _need(report["format"] == PROFILE and report["status"] == "incomplete"
              and type(report["supported_profiles_verified"]) is bool
              and all(report[key] is False for key in FLAGS), "invalid_report")
        identities = {key: _digest(report[key]) for key in ("manifest_sha256", "event_head", "schema_sha256", "table_state_sha256",
                     "inspector_source_sha256", "inspector_loaded_sha256", "recovery_source_sha256", "recovery_loaded_sha256")}
        counts = {key: report["counts"][key] for key in ("nodes", "edges", "unsupported", "supported_nodes", "tombstoned_edges")}
        _need(all(type(value) is int and value >= 0 for value in counts.values()), "invalid_report")
        _need(report["supported_profiles_verified"] == (counts["supported_nodes"] > 0), "invalid_report")
        runtime = report["runtime"]
        _object(runtime, {"python_version", "python_implementation", "sqlite_version", "fingerprint_marshal_version"})
        _need(runtime["fingerprint_marshal_version"] == 2 and all(
            type(runtime[key]) is str and re.fullmatch(r"[a-zA-Z0-9_.+-]{1,40}", runtime[key])
            for key in ("python_version", "python_implementation", "sqlite_version")), "invalid_report")
        return {"format": PROFILE, "status": "incomplete", **identities, "counts": counts,
                "runtime": dict(runtime), "supported_profiles_verified": report["supported_profiles_verified"], **FLAGS}
    except (KeyError, TypeError):
        raise ClosureError("invalid_report") from None


# Raw source at import and loaded code are separate identities. A later on-disk
# edit cannot be reported as the source of an already loaded algorithm. This is
# a cooperating-process stability boundary, not a claim against hostile patches.
_OWN_NAMES = {role: {name for name, value in vars(module).items()
              if isinstance(value, (FunctionType, type)) and value.__module__ == module.__name__}
              for role, module in (("inspector", sys.modules[__name__]), ("recovery", recovery))}
_SOURCE_AT_IMPORT = {role: recovery._sha(recovery._read(Path(module.__file__).absolute(), 2 * 1024 * 1024))
                     for role, module in (("inspector", sys.modules[__name__]), ("recovery", recovery))}

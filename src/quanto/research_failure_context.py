"""Private, current evidence for D008's narrowly qualified failure context.

Only ``retrieve_failure_basis`` performs a memory query. The broker calls it in
the issued hypothesis query effect; all later checks revisit exact retained
records and receipts. Nothing here clears a historical refusal or changes it.
Proofs are cooperating-application records, not protection from the local owner.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sqlite3
import uuid

from quanto.failure_memory import FailureMemory, _STATUSES
from quanto.ledger import LedgerError, canonical_json, hash_bytes, hash_json
from quanto.policy_revision import _position, validate_revision
from quanto.provenance import ProvenanceError, _strict_json
from quanto.research_packets import FAILURE_CODES, SYSTEM_PROMPT
from quanto.research_workflow import ROLES
from quanto.study_suite import _verified

_ID = re.compile(r"[0-9a-f]{32}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_BASIS = "research_failure_basis"
_OBSERVATION = "research_failure_context_observation"


class FailureContextError(LedgerError):
    """Fixed refusal without private records or validation diagnostics."""


def _need(condition):
    if not condition:
        raise FailureContextError("failure_context_refused")


def _scope(values):
    _need(type(values) is list and len(values) <= 16)
    result = []
    for item in values:
        _need(type(item) is dict and set(item) == {"source", "id"}
              and type(item["source"]) is str and item["source"] in {"submission", "attempt"}
              and type(item["id"]) is str and _ID.fullmatch(item["id"]))
        result.append({"source": item["source"], "id": item["id"]})
    _need(len({(item["source"], item["id"]) for item in result}) == len(result))
    return sorted(result, key=lambda item: (item["source"], item["id"]))


def _memory(store):
    # Revalidation runs inside the broker transaction. FailureMemory.__init__
    # executes schema DDL, whose executescript would commit that transaction.
    # The schema was created at the one original retrieval; no DDL belongs here.
    memory = object.__new__(FailureMemory)
    memory.store = store
    memory.allowed_artifact_refs = frozenset()
    memory.allowed_kinds = frozenset()
    memory.allowed_codes = frozenset(FAILURE_CODES)
    return memory


def _identities():
    directory = Path(__file__).parent
    names = ("research_failure_context.py", "research_packets.py", "failure_memory.py",
             "study_suite.py", "policy_revision.py")
    return {"sources": {name: hash_bytes((directory / name).read_bytes()) for name in names},
            "prompt_sha256": hash_bytes(SYSTEM_PROMPT.encode()),
            "failure_schema": "research_failure_context.nine_fields.v1"}


def _event(store, kind, identity_key, identity, expected):
    matches = []
    for row in store.journal.connection.execute(
            "SELECT id,payload FROM events WHERE kind=?", (kind,)):
        payload = json.loads(row["payload"])
        if payload.get(identity_key) == identity:
            matches.append((row["id"], payload))
    _need(len(matches) == 1 and canonical_json(matches[0][1]) == canonical_json(expected))
    return matches[0][0]


def _availability(store, refs):
    states = {}
    for ref in sorted(set(refs)):
        _need(type(ref) is str and _HASH.fullmatch(ref))
        try:
            store.read_bytes(ref)
            states[ref] = "available"
        except ProvenanceError:
            states[ref] = "unavailable"
    return states


def _record_matches_request(record, request):
    raw = canonical_json(request).encode()
    _need(record["request_sha256"] == hash_bytes(raw)
          and record["request_bytes"] == len(raw)
          and record["request_encoding"] == "canonical_json")


def _publish(store, kind, request, derive):
    """Retain attempted preparation, including deterministic refusals."""
    submission = store.begin(kind, request)
    try:
        payload = derive()
        document = {"schema_version": 1, "kind": kind, "submission_id": submission,
                    "request": request, **payload}
        digest = store.put_json(document)
        store.finish(submission, "success", {"context_sha256": digest, "artifact_refs": [digest]})
        return digest
    except (ValueError, TypeError, KeyError, AttributeError, OSError, sqlite3.Error,
            LedgerError, ProvenanceError):
        store.finish(submission, "invalid", {"error_code": "failure_context_refused"})
        raise FailureContextError("failure_context_refused") from None


def _registered(store, digest, kind):
    _need(type(digest) is str and _HASH.fullmatch(digest))
    document = store.read_json(digest)
    _need(type(document) is dict and document.get("kind") == kind
          and type(document.get("schema_version")) is int and document["schema_version"] == 1)
    record = store.get_submission(document["submission_id"])
    _need(record["kind"] == kind and record["status"] == "success"
          and record["details"] == {"context_sha256": digest, "artifact_refs": [digest]})
    _record_matches_request(record, document["request"])
    _need(_position(store, record["submission_id"], "started")
          < _position(store, record["submission_id"], "finished"))
    return document


def _disposition_anchor(store, source, identity):
    row = store.journal.connection.execute(
        "SELECT * FROM failure_memory_dispositions WHERE source=? AND failure_id=? "
        "ORDER BY rowid DESC LIMIT 1", (source, identity)).fetchone()
    if row is None:
        return None
    row = dict(row)
    request = {"source": source, "failure_id": identity, "disposition": row["disposition"],
               "fix_artifact_ref": row["fix_artifact_ref"], "code": row["code"]}
    record = store.get_submission(row["submission_id"])
    _need(record["kind"] == "failure_memory_disposition" and record["status"] == "success"
          and row["disposition"] in {"unresolved", "corrected"})
    _record_matches_request(record, request)
    expected = {"schema_version": 1, "provisional": True,
                "disposition_id": row["disposition_id"], "submission_id": row["submission_id"],
                **request}
    receipt_refs = []
    for ref in record["details"]["artifact_refs"]:
        if ref == row["fix_artifact_ref"]:
            continue  # An unavailable fix is qualified, not a missing disposition receipt.
        if store.read_json(ref) == expected:
            receipt_refs.append(ref)
    _need(len(receipt_refs) == 1)
    start = _position(store, row["submission_id"], "started")
    event = _event(store, "failure_memory_disposition", "disposition_id",
                   row["disposition_id"], expected)
    finish = _position(store, row["submission_id"], "finished")
    _need(start < event < finish)
    _need(row["disposition"] != "corrected" or row["fix_artifact_ref"] is not None)
    return {"row": row, "receipt_sha256": receipt_refs[0], "started_event": start,
            "disposition_event": event, "finished_event": finish}


def _snapshot(store, memory, source, identity):
    """Revisit one authorized identity, never search for replacement failures."""
    db = store.journal.connection
    if source == "submission":
        row = db.execute(
            "SELECT s.submission_id AS id,s.kind,s.request_sha256,o.status,o.details AS metadata,"
            "NULL AS fingerprint,NULL AS evidence_kind,NULL AS specification,NULL AS data_identity,"
            "NULL AS code_identity FROM provenance_submissions s LEFT JOIN provenance_outcomes o "
            "USING(submission_id) WHERE s.submission_id=?", (identity,)).fetchone()
        _need(row is not None and not row["kind"].startswith("failure_memory_"))
        original = store.get_submission(identity)
        start = _position(store, identity, "started")
        finish = (_position(store, identity, "finished") if original["status"] != "pending" else None)
        request_availability = _availability(store, [original["request_sha256"]])
        original = {"record": original, "started_event": start, "finished_event": finish,
                    "request_availability": request_availability}
    else:
        row = db.execute(
            "SELECT a.attempt_id AS id,'experiment_attempt' AS kind,NULL AS request_sha256,"
            "o.status,o.result AS metadata,a.fingerprint,e.evidence_kind,e.specification,"
            "e.data_identity,e.code_identity FROM attempts a JOIN experiments e USING(fingerprint) "
            "LEFT JOIN outcomes o USING(attempt_id) WHERE a.attempt_id=?", (identity,)).fetchone()
        _need(row is not None)
        attempt = dict(db.execute("SELECT * FROM attempts WHERE attempt_id=?", (identity,)).fetchone())
        experiment = dict(db.execute("SELECT * FROM experiments WHERE fingerprint=?",
                                     (row["fingerprint"],)).fetchone())
        registration = {key: json.loads(experiment[key]) for key in (
            "specification", "data_identity", "code_identity", "assumptions")}
        registration["evidence_kind"] = experiment["evidence_kind"]
        _need(hash_json(registration) == row["fingerprint"])
        registered = _event(store, "experiment_registered", "fingerprint", row["fingerprint"],
                            {"fingerprint": row["fingerprint"], **registration})
        start = _event(store, "attempt_started", "attempt_id", identity,
                       {"attempt_id": identity, "fingerprint": row["fingerprint"]})
        outcome = db.execute("SELECT * FROM outcomes WHERE attempt_id=?", (identity,)).fetchone()
        outcome = dict(outcome) if outcome else None
        finish = (_event(store, "attempt_finished", "attempt_id", identity,
                         {"attempt_id": identity, "status": row["status"],
                          "result": json.loads(row["metadata"])}) if outcome else None)
        _need(registered < start and (finish is None or start < finish))
        original = {"attempt": attempt, "experiment": experiment, "outcome": outcome,
                    "registered_event": registered, "started_event": start, "finished_event": finish}
    _need((row["status"] or "pending") in _STATUSES)
    record, refs = memory._project(source, row)
    record["artifact_refs"], record["artifact_state"] = memory._verify(refs, [32])
    disposition = _disposition_anchor(store, source, identity)
    fix = disposition["row"]["fix_artifact_ref"] if disposition else None
    verified, state = memory._verify([fix] if fix else [], [32])
    record["disposition"]["fix_artifact_ref"] = verified[0] if verified else None
    record["disposition"]["artifact_state"] = state
    _need(record["disposition"]["state"] != "corrected"
          or record["status"] != "pending")
    return {"source": source, "id": identity, "memory_record": record, "original": original,
            "disposition": disposition,
            "reference_availability": _availability(store, [*refs, *([fix] if fix else [])])}


def _receipt(store, ref, source, ids):
    receipt = store.read_json(ref)
    memory = _memory(store)
    request = {"sources": [source], "ids": ids, "limit": 16}
    _need(type(receipt) is dict and set(receipt) == {
        "schema_version", "status", "provisional", "query_submission_id", "query", "failures",
        "scanned_count", "truncated", "returned_ids"})
    _need(receipt.get("schema_version") == 1 and type(receipt["schema_version"]) is int
          and receipt.get("status") == "success" and receipt.get("provisional") is True
          and receipt.get("truncated") is False and receipt.get("query") == memory._query(request)
          and type(receipt["scanned_count"]) is int and receipt["scanned_count"] == len(ids))
    observed = store.get_submission(receipt["query_submission_id"])
    _need(observed["kind"] == "failure_memory_query" and observed["status"] == "success"
          and observed["details"] == {"artifact_refs": [ref], "returned_ids": receipt["returned_ids"]})
    _record_matches_request(observed, request)
    _need(_position(store, observed["submission_id"], "started")
          < _position(store, observed["submission_id"], "finished"))
    expected = [{"source": source, "id": identity} for identity in ids]
    returned = [{"source": item["source"], "id": item["id"]} for item in receipt["failures"]]
    _need(_scope(receipt["returned_ids"]) == expected and _scope(returned) == expected
          and receipt["returned_ids"] == returned)
    return receipt


def retrieve_failure_basis(store, authorized_failure_ids):
    """Query the exact grant inside the broker's issued hypothesis effect only."""
    request = {"authorized_failure_ids": authorized_failure_ids}

    def derive():
        store.journal.verify_events()
        scope = _scope(authorized_failure_ids)
        memory = FailureMemory(store, allowed_codes=tuple(FAILURE_CODES))
        receipts, records = [], {}
        for source in ("submission", "attempt"):
            ids = [item["id"] for item in scope if item["source"] == source]
            if not ids:
                continue  # An empty memory ID filter is unrestricted.
            result = memory.query({"sources": [source], "ids": ids, "limit": 16})
            receipt = _receipt(store, result["receipt_sha256"], source, ids)
            receipts.append({"source": source, "receipt_sha256": result["receipt_sha256"]})
            for record in receipt["failures"]:
                records[(source, record["id"])] = record
        snapshots = [_snapshot(store, memory, item["source"], item["id"]) for item in scope]
        for snapshot in snapshots:
            _need(snapshot["memory_record"] == records[(snapshot["source"], snapshot["id"])])
        return {"authorized_failure_ids": scope, "retrievals": receipts,
                "aliases": [{"alias": f"failure-{index + 1}", **item}
                            for index, item in enumerate(scope)],
                "records": snapshots, "implementation": _identities()}

    return _publish(store, _BASIS, request, derive)


def _current_basis(store, basis_sha256, authorized):
    basis = _registered(store, basis_sha256, _BASIS)
    basis_started = _position(store, basis["submission_id"], "started")
    basis_finished = _position(store, basis["submission_id"], "finished")
    scope = _scope(authorized)
    _need(basis["authorized_failure_ids"] == scope
          and _scope(basis["request"]["authorized_failure_ids"]) == scope
          and basis["implementation"] == _identities())
    expected_aliases = [{"alias": f"failure-{index + 1}", **item}
                        for index, item in enumerate(scope)]
    _need(basis["aliases"] == expected_aliases)
    memory = _memory(store)
    expected_sources = [source for source in ("submission", "attempt")
                        if any(item["source"] == source for item in scope)]
    _need([item["source"] for item in basis["retrievals"]] == expected_sources)
    records = {}
    for retrieval in basis["retrievals"]:
        source = retrieval["source"]
        ids = [item["id"] for item in scope if item["source"] == source]
        receipt = _receipt(store, retrieval["receipt_sha256"], source, ids)
        query_started = _position(store, receipt["query_submission_id"], "started")
        query_finished = _position(store, receipt["query_submission_id"], "finished")
        _need(basis_started < query_started < query_finished < basis_finished)
        for record in receipt["failures"]:
            records[(source, record["id"])] = record
    current = [_snapshot(store, memory, item["source"], item["id"]) for item in scope]
    _need(canonical_json(current) == canonical_json(basis["records"]))
    for snapshot in current:
        _need(snapshot["memory_record"] == records[(snapshot["source"], snapshot["id"])])
    return basis


class _Reads:
    """Observe actual validator reads, including transitive request/source bytes."""

    def __init__(self, store):
        self.store, self.refs = store, set()

    def __getattr__(self, name):
        return getattr(self.store, name)

    def read_bytes(self, digest):
        raw = self.store.read_bytes(digest)
        self.refs.add(digest)
        return raw

    def read_json(self, digest):
        return _strict_json(self.read_bytes(digest))


def _evidence(store, configuration_sha256, role, basis_sha256):
    _need(type(role) is str and role in ROLES)
    configuration = store.read_json(configuration_sha256)
    authorized = _scope(configuration["failure_ids"])
    _need((role == "director" and basis_sha256 is None)
          or (role != "director" and basis_sha256 is not None))
    basis = (_current_basis(store, basis_sha256, authorized) if basis_sha256 is not None else None)
    tracked = _Reads(store)
    suite = _verified(tracked, configuration["suite_sha256"])
    revision_ref = suite["policy_revision_sha256"]
    _need(revision_ref == configuration["verified_policy_revision_sha256"])
    admission_ref = suite["members"][0]["request"]["admission_sha256"]
    admission = tracked.read_json(admission_ref)
    revision = validate_revision(tracked, revision_ref, admission["request"])
    refusals = revision["lineage"]["prior_refusals"]
    failures, relations = [], []
    for alias, snapshot in zip(basis["aliases"] if basis else [], basis["records"] if basis else []):
        record, original = snapshot["memory_record"], snapshot["original"]
        matches = []
        if snapshot["source"] == "submission":
            for refusal in refusals:
                if refusal["submission_id"] == snapshot["id"]:
                    _need(record["status"] == "invalid"
                          and refusal["request_sha256"] == record["request_sha256"]
                          and refusal["error_code"] == original["record"]["details"]["error_code"]
                          and refusal["started_event"] == original["started_event"]
                          and refusal["finished_event"] == original["finished_event"])
                    raw = tracked.read_bytes(refusal["request_sha256"])
                    _need(hash_bytes(raw) == original["record"]["request_sha256"]
                          and len(raw) == original["record"]["request_bytes"])
                    matches.append(refusal)
        _need(len(matches) <= 1)
        disposition = record["disposition"]
        failures.append({"alias": alias["alias"],
                         "code": record["code"] if record["code"] in FAILURE_CODES else "other_refusal",
                         "status": record["status"], "disposition": disposition["state"],
                         "disposition_recorded": disposition["id"] is not None,
                         "provisional": True, "artifact_state": record["artifact_state"],
                         "disposition_artifact_state": disposition["artifact_state"],
                         "relation": "prior_refusal_in_bound_revision" if matches
                         else "no_relation_established"})
        relations.append({"alias": alias["alias"], "source": snapshot["source"],
                          "id": snapshot["id"], "prior_refusal": matches[0] if matches else None})
    return {"configuration_sha256": configuration_sha256, "role": role,
            "basis_sha256": basis_sha256, "suite_sha256": configuration["suite_sha256"],
            "policy_revision_sha256": revision_ref, "admission_sha256": admission_ref,
            "authorized_failure_ids": authorized, "failures": failures,
            "current_evidence": {"suite": suite, "revision": revision, "admission": admission,
                                 "relations": relations},
            "dependency_refs": sorted(tracked.refs), "implementation": _identities()}


def verify_failure_context(store, configuration_sha256, role, basis_sha256):
    """Create one private observation after checking the original grant and current validators."""
    request = {"configuration_sha256": configuration_sha256, "role": role,
               "basis_sha256": basis_sha256}

    def derive():
        evidence = _evidence(store, configuration_sha256, role, basis_sha256)
        return {**evidence, "observation_id": uuid.uuid4().hex,
                "verified_at": store.journal._stamp(store.journal._now())}

    return _publish(store, _OBSERVATION, request, derive)


def revalidate_failure_context(store, observation_sha256, configuration_sha256, role, basis_sha256):
    """Recompute inside the broker's live-lease transaction before exact one-use binding.

    This does not issue another observation or worker query. The binder owns
    assignment/fence/request/packet binding and rejects observation reuse.
    """
    try:
        store.journal.verify_events()
        observed = _registered(store, observation_sha256, _OBSERVATION)
        expected_request = {"configuration_sha256": configuration_sha256, "role": role,
                            "basis_sha256": basis_sha256}
        _need(observed["request"] == expected_request)
        current = _evidence(store, configuration_sha256, role, basis_sha256)
        expected_keys = {"schema_version", "kind", "submission_id", "request", "observation_id",
                         "verified_at", *current}
        _need(set(observed) == expected_keys and type(observed["observation_id"]) is str
              and _ID.fullmatch(observed["observation_id"]))
        _need(canonical_json({key: observed[key] for key in current}) == canonical_json(current))
        return observed
    except (ValueError, TypeError, KeyError, AttributeError, OSError, sqlite3.Error,
            LedgerError, ProvenanceError):
        raise FailureContextError("failure_context_refused") from None

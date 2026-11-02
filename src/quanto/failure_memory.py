"""Provisional D008 local failure retrieval; capability checks belong to its broker.

Only fixed metadata and explicitly allowlisted kinds/codes/references leave this service.
Opaque IDs and hashes can still disclose private relationships. The broker must
authorize which failure IDs the caller may retrieve; formatting is not authority.
No stored free text, artifact contents, paths, market values or identity documents
are returned. Bounded scans are disclosed; a result is not a full-corpus search.
Application append-only controls do not protect against the database owner.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid

from quanto.ledger import EVIDENCE_KINDS, canonical_json
from quanto.provenance import Provenance, ProvenanceError

MAX_RESULTS = 50
MAX_SCAN = 500  # Per source, before post-filtering on safe projected metadata.
MAX_FILTER_VALUES = 32
MAX_REFS = 8
MAX_VERIFICATIONS = 32
MAX_METADATA_BYTES = 64 * 1024
_SOURCES = frozenset({"submission", "attempt"})
_STATUSES = frozenset({"failed", "invalid", "interrupted", "rejected", "pending"})
_DISPOSITIONS = frozenset({"unresolved", "corrected"})
_IDENTIFIER = re.compile(r"[a-z][a-z0-9_.:-]{0,63}\Z")
_ID = re.compile(r"[0-9a-f]{32}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_KEYWORD = re.compile(r"[a-z0-9_.:-]{1,64}\Z")
_INTERNAL_PREFIX = "failure_memory_"
_SCHEMA = """
CREATE TABLE IF NOT EXISTS failure_memory_dispositions (
 disposition_id TEXT PRIMARY KEY, source TEXT NOT NULL, failure_id TEXT NOT NULL,
 disposition TEXT NOT NULL CHECK(disposition IN ('unresolved','corrected')),
 fix_artifact_ref TEXT, code TEXT NOT NULL, submission_id TEXT NOT NULL UNIQUE
 REFERENCES provenance_submissions(submission_id), created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS no_update_failure_memory_dispositions
 BEFORE UPDATE ON failure_memory_dispositions BEGIN
 SELECT RAISE(ABORT, 'append-only record'); END;
CREATE TRIGGER IF NOT EXISTS no_delete_failure_memory_dispositions
 BEFORE DELETE ON failure_memory_dispositions BEGIN
 SELECT RAISE(ABORT, 'append-only record'); END;
"""


class FailureMemoryError(ProvenanceError):
    """A fixed-message refusal, safe to expose without underlying record text."""


def _check(value, pattern):
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise FailureMemoryError("invalid_memory_identifier")
    return value


def _allowlist(values, pattern, maximum=128):
    if not isinstance(values, (tuple, list, set, frozenset)) or len(values) > maximum:
        raise FailureMemoryError("invalid_memory_allowlist")
    return frozenset(_check(value, pattern) for value in values)


def _metadata(raw):
    """Read only bounded JSON; unknown fields are never projected or searched."""
    if raw is None:
        return {}
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_METADATA_BYTES:
        raise FailureMemoryError("invalid_memory_metadata")
    try:
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise ValueError
                result[key] = value
            return result
        result = json.loads(raw, object_pairs_hook=pairs)
        if not isinstance(result, dict):
            raise ValueError
        canonical_json(result)
        return result
    except (ValueError, TypeError, RecursionError, UnicodeError):
        raise FailureMemoryError("invalid_memory_metadata") from None


class FailureMemory:
    """Private local service, with no caller-authentication claim.

    The integrating capability broker supplies transmission-approved kinds,
    codes and artifact references. Unapproved kinds/codes become fixed values.
    Artifact references are checked against retained bytes on every retrieval.
    A correction records a claim linked to actual bytes, not independent proof
    that the fix resolves the failure. Its original outcome is never changed.
    """

    def __init__(self, store: Provenance, *, allowed_artifact_refs=(),
                 allowed_kinds=(), allowed_codes=()):
        self.store = store
        self.allowed_artifact_refs = _allowlist(allowed_artifact_refs, _HASH)
        self.allowed_kinds = _allowlist(allowed_kinds, _IDENTIFIER)
        self.allowed_codes = _allowlist(allowed_codes, _IDENTIFIER)
        store._open().connection.executescript(_SCHEMA)

    def _query(self, request):
        keys = {"sources", "statuses", "kinds", "codes", "ids", "request_sha256",
                "keyword", "disposition", "limit"}
        if not isinstance(request, dict) or set(request) - keys:
            raise FailureMemoryError("invalid_memory_query")
        query = {"sources": ["submission", "attempt"], "statuses": sorted(_STATUSES),
                 "kinds": [], "codes": [], "ids": [], "request_sha256": [],
                 "keyword": None, "disposition": None, "limit": 20}
        query.update(request)
        if type(query["limit"]) is not int or not 1 <= query["limit"] <= MAX_RESULTS:
            raise FailureMemoryError("invalid_memory_limit")
        for key, allowed, pattern in (
            ("sources", _SOURCES, None), ("statuses", _STATUSES, None),
            ("kinds", self.allowed_kinds, _IDENTIFIER),
            ("codes", self.allowed_codes, _IDENTIFIER), ("ids", None, _ID),
            ("request_sha256", None, _HASH),
        ):
            values = query[key]
            if (not isinstance(values, list) or len(values) > MAX_FILTER_VALUES
                    or (key in {"sources", "statuses"} and not values)):
                raise FailureMemoryError("invalid_memory_filter")
            for value in values:
                if pattern:
                    _check(value, pattern)
                if allowed is not None and (not isinstance(value, str) or value not in allowed):
                    raise FailureMemoryError("invalid_memory_filter")
            if len(set(values)) != len(values):
                raise FailureMemoryError("invalid_memory_filter")
            query[key] = sorted(values)
        if query["keyword"] is not None:
            _check(query["keyword"], _KEYWORD)
        if (query["disposition"] is not None
                and (not isinstance(query["disposition"], str)
                     or query["disposition"] not in _DISPOSITIONS)):
            raise FailureMemoryError("invalid_memory_disposition")
        return query

    def _rows(self, source, query):
        if source == "submission":
            sql = ("SELECT s.submission_id AS id,substr(s.kind,1,65) AS kind,s.request_sha256,o.status,"
                   "substr(o.details,1,65537) "
                   "AS metadata,NULL AS fingerprint,NULL AS evidence_kind,NULL AS specification,"
                   "NULL AS data_identity,NULL AS code_identity "
                   "FROM provenance_submissions s LEFT JOIN provenance_outcomes o "
                   "USING(submission_id) WHERE substr(s.kind,1,15) != 'failure_memory_'")
            id_column, order = "s.submission_id", "s.started_at DESC,s.rowid DESC"
        else:
            sql = ("SELECT a.attempt_id AS id,'experiment_attempt' AS kind,NULL AS request_sha256,"
                   "o.status,substr(o.result,1,65537) AS metadata,a.fingerprint,e.evidence_kind,"
                   "substr(e.specification,1,65537) AS specification,"
                   "substr(e.data_identity,1,65537) AS data_identity,"
                   "substr(e.code_identity,1,65537) AS code_identity "
                   "FROM attempts a JOIN experiments e USING(fingerprint) "
                   "LEFT JOIN outcomes o USING(attempt_id) WHERE 1=1")
            id_column, order = "a.attempt_id", "a.started_at DESC,a.rowid DESC"
        values = []
        states = [s for s in query["statuses"] if s != "pending"]
        conditions = []
        if states:
            conditions.append("o.status IN (" + ",".join("?" for _ in states) + ")")
            values.extend(states)
        if "pending" in query["statuses"]:
            conditions.append("o.status IS NULL")
        sql += " AND (" + " OR ".join(conditions) + ")"
        if query["ids"]:
            sql += " AND " + id_column + " IN (" + ",".join("?" for _ in query["ids"]) + ")"
            values.extend(query["ids"])
        if query["request_sha256"]:
            if source == "attempt":
                return []
            sql += " AND s.request_sha256 IN (" + ",".join(
                "?" for _ in query["request_sha256"]) + ")"
            values.extend(query["request_sha256"])
        return self.store._open().connection.execute(
            sql + " ORDER BY " + order + " LIMIT ?", (*values, MAX_SCAN + 1)).fetchall()

    def _disposition(self, source, identity):
        row = self.store._open().connection.execute(
            "SELECT disposition_id,disposition,fix_artifact_ref,code FROM "
            "failure_memory_dispositions WHERE source=? AND failure_id=? ORDER BY rowid DESC LIMIT 1",
            (source, identity)).fetchone()
        if row is None:
            return {"state": "unresolved", "id": None, "code": None,
                    "fix_artifact_ref": None}
        return {"state": row["disposition"], "id": _check(row["disposition_id"], _ID),
                "code": row["code"] if row["code"] in self.allowed_codes else "undisclosed",
                "fix_artifact_ref": row["fix_artifact_ref"]}

    def _project(self, source, row):
        metadata = _metadata(row["metadata"])
        kind = _check(row["kind"], _IDENTIFIER)
        code = metadata.get("error_code", metadata.get("reason", metadata.get("error_type")))
        if code is not None and (not isinstance(code, str) or len(code) > 256):
            raise FailureMemoryError("invalid_memory_metadata")
        code = code if code in self.allowed_codes else ("undisclosed" if code else None)
        refs = metadata.get("artifact_refs", [])
        if (not isinstance(refs, list) or len(refs) > 128
                or any(not isinstance(ref, str) or not _HASH.fullmatch(ref) for ref in refs)
                or len(set(refs)) != len(refs)):
            raise FailureMemoryError("invalid_memory_metadata")
        identity = _check(row["id"], _ID)
        record = {"source": source, "id": identity,
                  "kind": kind if kind in self.allowed_kinds or source == "attempt" else "undisclosed",
                  "status": row["status"] or "pending", "code": code,
                  "request_sha256": _check(row["request_sha256"], _HASH)
                  if row["request_sha256"] else None,
                  "fingerprint": _check(row["fingerprint"], _HASH) if row["fingerprint"] else None,
                  "evidence_kind": row["evidence_kind"] if row["evidence_kind"] in EVIDENCE_KINDS else None,
                  "disposition": self._disposition(source, identity)}
        for field in ("specification", "data_identity", "code_identity"):
            raw = row[field]
            if raw is not None:
                if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_METADATA_BYTES:
                    raise FailureMemoryError("invalid_memory_metadata")
                record[field + "_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            else:
                record[field + "_sha256"] = None
        return record, refs

    def _verify(self, refs, budget):
        verified, unavailable, bounded = [], False, False
        approved = sorted(set(refs) & self.allowed_artifact_refs)
        for ref in approved[:MAX_REFS]:
            if budget[0] == 0:
                bounded = True
                break
            budget[0] -= 1
            try:
                self.store.read_bytes(ref)
                verified.append(ref)
            except ProvenanceError:
                unavailable = True
        state = ("unavailable" if unavailable else "verification_bound" if bounded
                 or len(approved) > MAX_REFS else "verified" if verified
                 else "not_allowed" if refs else "none")
        return verified, state

    def query(self, request: dict) -> dict:
        """Return and durably receipt a bounded metadata-only current-state query."""
        submission = self.store.begin(_INTERNAL_PREFIX + "query", request)
        journal = self.store._open()
        try:
            query = self._query(request)
            with journal._transaction():
                matches, scanned, truncated = [], 0, False
                for source in query["sources"]:
                    rows = self._rows(source, query)
                    truncated |= len(rows) > MAX_SCAN
                    for row in rows[:MAX_SCAN]:
                        scanned += 1
                        record, refs = self._project(source, row)
                        if query["kinds"] and record["kind"] not in query["kinds"]:
                            continue
                        if query["codes"] and record["code"] not in query["codes"]:
                            continue
                        if query["disposition"] and record["disposition"]["state"] != query["disposition"]:
                            continue
                        # No details, raw JSON, timestamps, paths or artifact text enter this index.
                        searchable = [record[k] for k in ("source", "id", "kind", "status", "code",
                                                         "request_sha256", "fingerprint", "evidence_kind",
                                                         "specification_sha256", "data_identity_sha256",
                                                         "code_identity_sha256")]
                        if query["keyword"] and not any(
                            query["keyword"] in value for value in searchable if isinstance(value, str)
                        ):
                            continue
                        matches.append((record, refs))
                truncated |= len(matches) > query["limit"]
                results, budget = [], [MAX_VERIFICATIONS]
                for record, refs in matches[:query["limit"]]:
                    record["artifact_refs"], record["artifact_state"] = self._verify(refs, budget)
                    disposition = record["disposition"]
                    fix = disposition["fix_artifact_ref"]
                    verified, state = self._verify([_check(fix, _HASH)] if fix else [], budget)
                    disposition["fix_artifact_ref"] = verified[0] if verified else None
                    disposition["artifact_state"] = state
                    results.append(record)
                receipt = {"schema_version": 1, "status": "success", "provisional": True,
                           "query_submission_id": submission, "query": query, "failures": results,
                           "scanned_count": scanned, "truncated": truncated,
                           "returned_ids": [{"source": r["source"], "id": r["id"]} for r in results]}
                ref = self.store.put_json(receipt)
                self.store.finish(submission, "success", {"artifact_refs": [ref],
                                  "returned_ids": receipt["returned_ids"]})
            return {**receipt, "receipt_sha256": ref}
        except (FailureMemoryError, ProvenanceError, sqlite3.Error, ValueError, TypeError):
            self.store.finish(submission, "invalid", {"error_code": "memory_query_refused"})
            raise FailureMemoryError("memory_query_refused") from None

    def append_disposition(self, source: str, failure_id: str, disposition: str,
                           fix_artifact_ref: str | None = None, code: str = "correction_recorded") -> dict:
        """Append an attributed repair claim; never rewrite the failed attempt."""
        request = {"source": source, "failure_id": failure_id, "disposition": disposition,
                   "fix_artifact_ref": fix_artifact_ref, "code": code}
        submission = self.store.begin(_INTERNAL_PREFIX + "disposition", request)
        journal = self.store._open()
        try:
            if (not isinstance(source, str) or source not in _SOURCES
                    or not isinstance(disposition, str) or disposition not in _DISPOSITIONS):
                raise FailureMemoryError("invalid_memory_disposition")
            _check(failure_id, _ID)
            if not isinstance(code, str) or code not in self.allowed_codes:
                raise FailureMemoryError("invalid_memory_disposition_code")
            if fix_artifact_ref is not None:
                _check(fix_artifact_ref, _HASH)
                if fix_artifact_ref not in self.allowed_artifact_refs:
                    raise FailureMemoryError("disallowed_fix_artifact")
            if disposition == "corrected" and fix_artifact_ref is None:
                raise FailureMemoryError("correction_requires_fix_artifact")
            with journal._transaction():
                rows = self._rows(source, self._query({"sources": [source], "ids": [failure_id]}))
                if len(rows) != 1 or (disposition == "corrected" and rows[0]["status"] is None):
                    raise FailureMemoryError("original_failure_required")
                if fix_artifact_ref:
                    self.store.read_bytes(fix_artifact_ref)
                identity, now = uuid.uuid4().hex, journal._now()
                receipt = {"schema_version": 1, "provisional": True,
                           "disposition_id": identity, "submission_id": submission, **request}
                ref = self.store.put_json(receipt)
                journal.connection.execute(
                    "INSERT INTO failure_memory_dispositions VALUES (?,?,?,?,?,?,?,?)",
                    (identity, source, failure_id, disposition, fix_artifact_ref, code,
                     submission, journal._stamp(now)))
                journal._event("failure_memory_disposition", receipt, now)
                self.store.finish(submission, "success", {"artifact_refs": sorted(
                    {ref} | ({fix_artifact_ref} if fix_artifact_ref else set()))})
            return {**receipt, "receipt_sha256": ref}
        except (FailureMemoryError, ProvenanceError, sqlite3.Error, ValueError, TypeError):
            self.store.finish(submission, "invalid", {"error_code": "memory_disposition_refused"})
            raise FailureMemoryError("memory_disposition_refused") from None

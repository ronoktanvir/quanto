"""Registered development-only exploration over verified private artifacts.

These controls apply to cooperating callers, not a database or filesystem owner.
Historical calculation requires separately verified conditional admission; the
original dataset registration remains inspection-only. No result is a protected holdout or edge claim.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
import json
import marshal
from pathlib import Path
import platform
import re
import sqlite3
from types import CodeType, FunctionType
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from quanto.ledger import LedgerError, canonical_json, hash_bytes, hash_json
from quanto import research as research_engine
from quanto import event_engine
from quanto.event_engine import run_event_backtest
from quanto.provenance import Provenance, ProvenanceError
from quanto.research import Bar, ResearchValidationError, StrategySpec, run_backtest

MAX_BARS = 20_000
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_MARKET_FIELDS = {"instrument_id", "venue", "currency", "session_timezone"}
_BAR_FIELDS = {"timestamp", "symbol", "open", "high", "low", "close", "volume"}
_SCHEMA = """
CREATE TABLE IF NOT EXISTS explorer_datasets (
 manifest_sha256 TEXT PRIMARY KEY, market_key TEXT NOT NULL,
 coverage_start TEXT NOT NULL, coverage_end TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS explorer_exposures (
 exposure_id TEXT PRIMARY KEY, submission_id TEXT NOT NULL,
 dataset_sha256 TEXT NOT NULL, market_key TEXT NOT NULL, market_identity TEXT NOT NULL,
 coverage_start TEXT NOT NULL, coverage_end TEXT NOT NULL,
 study_name TEXT NOT NULL, purpose TEXT NOT NULL, observed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS explorer_executions (
 submission_id TEXT PRIMARY KEY, attempt_id TEXT NOT NULL UNIQUE,
 fingerprint TEXT NOT NULL, market_key TEXT NOT NULL
);
"""

HISTORICAL_ADMISSION_GAPS = [
    "verified_exchange_session_coverage", "corporate_action_accounting",
    "historical_information_timing", "permitted_data_use",
]


class ExplorationError(ValueError):
    """A fixed safe reason for refusing an exploratory request."""


def _ref(value: object) -> str:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ExplorationError("invalid_artifact_identity")
    return value


def _text(value: object, *, limit=160) -> str:
    if (not isinstance(value, str) or not value.strip() or len(value) > limit
            or any(ord(char) < 32 for char in value)):
        raise ExplorationError("invalid_text_field")
    return value.strip()


def _day(value: object) -> date:
    if not isinstance(value, str):
        raise ExplorationError("invalid_date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ExplorationError("invalid_date") from None
    if parsed.isoformat() != value:
        raise ExplorationError("invalid_date")
    return parsed


def _envelope(value: dict | str) -> str:
    # Freeze a dict once. Validation uses these same bytes after begin records
    # their identity, even if the caller subsequently mutates the original dict.
    try:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return canonical_json(value)
    except (ValueError, TypeError, RecursionError, OverflowError, UnicodeError):
        pass
    raise ProvenanceError("Request must be bounded UTF-8 text or a JSON object")


def _request(raw: str) -> dict:
    def unique(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ExplorationError("duplicate_request_key")
            result[key] = item
        return result

    def nonfinite(_):
        raise ExplorationError("nonfinite_request")

    try:
        parsed = json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
        canonical_json(parsed)
    except ExplorationError:
        raise
    except (ValueError, TypeError, RecursionError, OverflowError, UnicodeError):
        raise ExplorationError("invalid_request_json") from None
    if not isinstance(parsed, dict):
        raise ExplorationError("request_must_be_object")
    return parsed


def _market(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != _MARKET_FIELDS:
        raise ExplorationError("invalid_market_identity")
    result = {key: _text(value[key]) for key in sorted(_MARKET_FIELDS)}
    if not re.fullmatch(r"[A-Z]{3}", result["currency"]):
        raise ExplorationError("invalid_currency")
    try:
        ZoneInfo(result["session_timezone"])
    except (ValueError, ZoneInfoNotFoundError):
        raise ExplorationError("unknown_session_timezone") from None
    return result


def _market_key(market: dict) -> str:
    # Venue/feed/currency changes cannot clear exposure for the same declared
    # instrument. Resolving different identifiers to one issuer is still pending.
    return hash_json({"instrument_id": market["instrument_id"].casefold()})


def _schema(store: Provenance) -> None:
    journal = store.journal
    journal.connection.executescript(_SCHEMA)
    for table in ("explorer_datasets", "explorer_exposures", "explorer_executions"):
        for operation in ("UPDATE", "DELETE"):
            journal.connection.execute(
                f"CREATE TRIGGER IF NOT EXISTS no_{operation.lower()}_{table} "
                f"BEFORE {operation} ON {table} BEGIN "
                "SELECT RAISE(ABORT, 'append-only record'); END"
            )


def _bars(value: object, market: dict) -> tuple[Bar, ...]:
    if isinstance(value, dict):
        value = value.get("bars")
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_BARS:
        raise ExplorationError("invalid_bars_shape")
    zone = ZoneInfo(market["session_timezone"])
    result = []
    for row in value:
        if (not isinstance(row, dict) or not _BAR_FIELDS.issubset(row)
                or set(row) - (_BAR_FIELDS | {"source_timestamp"})):
            raise ExplorationError("invalid_bar_fields")
        try:
            timestamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            if timestamp.utcoffset() is None:
                raise ValueError("naive timestamp")
            timestamp = timestamp.astimezone(zone)
            item = Bar(timestamp, _text(row["symbol"], limit=64),
                       *(row[key] for key in ("open", "high", "low", "close", "volume")))
        except (ValueError, TypeError, AttributeError, OverflowError):
            raise ExplorationError("invalid_bar") from None
        if result and (item.symbol != result[0].symbol
                       or item.timestamp.date() <= result[-1].timestamp.date()):
            raise ExplorationError("mixed_or_nonmonotonic_bars")
        result.append(item)
    return tuple(result)


def _bar_json(bars: tuple[Bar, ...]) -> dict:
    return {"schema_version": 1, "bars": [
        {**asdict(bar), "timestamp": bar.timestamp.isoformat()} for bar in bars
    ]}


def _source_metadata(source: object, evidence: str, basis: str, market: dict, bars) -> None:
    if not isinstance(source, dict):
        return
    for key, expected in (("evidence_kind", evidence), ("price_basis", basis)):
        if key in source and source[key] != expected:
            raise ExplorationError("source_metadata_mismatch")
    identity = source.get("identity", {})
    if not isinstance(identity, dict):
        raise ExplorationError("source_metadata_mismatch")
    for key, expected in (("currency", market["currency"]),
                          ("session_timezone", market["session_timezone"]),
                          ("symbol", bars[0].symbol)):
        if key in identity and identity[key] != expected:
            raise ExplorationError("source_metadata_mismatch")


def _exposure_in_transaction(store, submission_id, dataset, market, start, end, study, purpose):
    journal = store.journal
    key = _market_key(market)
    prior = journal.connection.execute(
        "SELECT COUNT(*) FROM explorer_exposures WHERE market_key=? "
        "AND coverage_start<=? AND coverage_end>=?",
        (key, end, start),
    ).fetchone()[0]
    now = journal._now()
    record = {"exposure_id": uuid.uuid4().hex, "submission_id": submission_id,
              "dataset_sha256": dataset, "market_key": key, "market": market,
              "coverage_start": start, "coverage_end": end, "study_name": study,
              "purpose": purpose, "observed_at": journal._stamp(now)}
    journal.connection.execute("INSERT INTO explorer_exposures VALUES (?,?,?,?,?,?,?,?,?,?)", (
        record["exposure_id"], submission_id, dataset, key, canonical_json(market),
        start, end, study, purpose, record["observed_at"],
    ))
    journal._event("exploratory_exposure_recorded", {
        **record, "policy": "development_only", "prior_exposure": "unknown_outside_application",
    }, now)
    return prior


def _finish(store, submission_id, status, details, *, attempt=None, attempt_result=None):
    """Commit submission/attempt terminals together after reference verification.

    Journal.finish_attempt owns a transaction, so this adapter appends the same
    outcome/event schema inside the shared transaction instead of nesting it.
    """
    journal = store.journal
    with journal._transaction():
        store.finish(submission_id, status, details)
        if attempt is not None:
            attempt_status = status if status in ("success", "invalid") else "failed"
            now = journal._now()
            journal.connection.execute("INSERT INTO outcomes VALUES (?,?,?,?)", (
                attempt, attempt_status, canonical_json(attempt_result), journal._stamp(now),
            ))
            journal._event("attempt_finished", {
                "attempt_id": attempt, "status": attempt_status, "result": attempt_result,
            }, now)


def _error(store, submission_id, status, code, *, attempt=None, evidence=None):
    details = {"error_code": code, "result_kind": "no_result"}
    if evidence is not None:
        details["evidence_kind"] = evidence
    if code == "historical_admission_required":
        details["admission_status"] = "inspection_only"
        details["admission_gaps"] = HISTORICAL_ADMISSION_GAPS
    if attempt:
        details["attempt_id"] = attempt
    try:
        _finish(store, submission_id, status, details, attempt=attempt,
                attempt_result={"error_code": code, **({"evidence_kind": evidence} if evidence else {})})
    except (OSError, sqlite3.Error, ProvenanceError, LedgerError):
        return {"submission_id": submission_id, "status": "pending", **details,
                "error_code": "publication_interrupted"}
    return {"submission_id": submission_id, "status": status, **details}


def register_dataset(root: Path, request: dict | str) -> dict:
    """Register an existing exact-byte artifact; historical records are inspection-only.

    Request fields: data_sha256, evidence_kind, market, price_basis,
    expected_sessions (mandatory for synthetic fixtures), optional parent_dataset_sha256.
    Artifact may be a bar list or an object with a bars list. This records data
    classification supplied by the caller, not provider authenticity or rights.
    """
    with Provenance(root) as store:
        _schema(store)
        frozen_request = _envelope(request)
        submission = store.begin("dataset_registration", frozen_request)
        publishing = False
        try:
            data = _request(frozen_request)
            required = {"data_sha256", "evidence_kind", "market", "price_basis"}
            if not required.issubset(data) or set(data) - (required | {
                "expected_sessions", "parent_dataset_sha256"
            }):
                raise ExplorationError("invalid_registration_fields")
            evidence = data["evidence_kind"]
            if evidence not in ("synthetic_fixture", "historical_market_data"):
                raise ExplorationError("unsupported_evidence_kind")
            market = _market(data["market"])
            basis = data["price_basis"]
            if basis not in ("raw", "all"):
                raise ExplorationError("unsupported_price_basis")
            if evidence == "synthetic_fixture" and (
                not market["instrument_id"].startswith("synthetic:") or basis != "raw"
            ):
                raise ExplorationError("synthetic_identity_required")
            if evidence == "historical_market_data" and market["instrument_id"].startswith("synthetic:"):
                raise ExplorationError("historical_identity_required")
            source = _ref(data["data_sha256"])
            source_data = store.read_json(source)
            bars = _bars(source_data, market)
            _source_metadata(source_data, evidence, basis, market, bars)
            sessions = [bar.timestamp.date().isoformat() for bar in bars]
            exposure_start, exposure_end = sessions[0], sessions[-1]
            if evidence == "historical_market_data" and isinstance(source_data, dict):
                coverage = source_data.get("coverage", {})
                if not isinstance(coverage, dict):
                    raise ExplorationError("invalid_source_coverage")
                if "requested_start" in coverage or "requested_end" in coverage:
                    exposure_start = _day(coverage.get("requested_start")).isoformat()
                    exposure_end = _day(coverage.get("requested_end")).isoformat()
                    if exposure_start > sessions[0] or exposure_end < sessions[-1]:
                        raise ExplorationError("invalid_source_coverage")
            expected = data.get("expected_sessions")
            if evidence == "synthetic_fixture" and expected is None:
                raise ExplorationError("synthetic_schedule_required")
            if expected is not None:
                if not isinstance(expected, list) or [_day(day).isoformat() for day in expected] != sessions:
                    raise ExplorationError("session_coverage_mismatch")
            parent = data.get("parent_dataset_sha256")
            if parent is not None:
                parent_manifest = _dataset(store, _ref(parent))
                if _market_key(parent_manifest["market"]) != _market_key(market):
                    raise ExplorationError("parent_instrument_mismatch")
            publishing = True
            normalized = store.put_json(_bar_json(bars))
            manifest = {
                "schema_version": 1, "kind": "explorer_dataset", "evidence_kind": evidence,
                "source_sha256": source, "bars_sha256": normalized, "market": market,
                "symbol": bars[0].symbol, "price_basis": basis, "sessions": sessions,
                "coverage_start": sessions[0], "coverage_end": sessions[-1],
                "exposure_start": exposure_start, "exposure_end": exposure_end,
                "bar_count": len(bars), "parent_dataset_sha256": parent,
                "admission_status": "synthetic_only" if evidence == "synthetic_fixture" else "inspection_only",
                "development_policy": "entire_dataset_development_only",
                "prior_exposure": "unknown_outside_application",
                "calendar_status": "synthetic_defined" if evidence == "synthetic_fixture" else "unverified",
                "corporate_actions": "not_applicable_synthetic" if evidence == "synthetic_fixture" else "unknown",
                "timing": "session_level_assumption", "rights": "caller_classification_unverified",
            }
            digest = store.put_json(manifest)
            with store.journal._transaction():
                now = store.journal._now()
                store.journal.connection.execute(
                    "INSERT OR IGNORE INTO explorer_datasets VALUES (?,?,?,?,?)",
                    (digest, _market_key(market), sessions[0], sessions[-1], store.journal._stamp(now)),
                )
                _exposure_in_transaction(store, submission, digest, market, exposure_start, exposure_end,
                                         "dataset_registration", "development_registration")
                store.journal._event("explorer_dataset_registered", {
                    "submission_id": submission, "manifest_sha256": digest,
                    "evidence_kind": evidence, "admission_status": manifest["admission_status"],
                }, now)
            details = {"manifest_sha256": digest, "evidence_kind": evidence,
                       "admission_status": manifest["admission_status"],
                       "development_policy": manifest["development_policy"],
                       "artifact_refs": sorted({digest, normalized, source})}
            store.finish(submission, "success", details)
            return {"submission_id": submission, "status": "success", **details}
        except ExplorationError as exc:
            return _error(store, submission, "invalid", str(exc))
        except (OSError, sqlite3.Error):
            return _error(store, submission, "interrupted", "storage_interrupted")
        except (ProvenanceError, LedgerError):
            return _error(store, submission, "interrupted" if publishing else "invalid",
                          "publication_interrupted" if publishing else "artifact_or_storage_unavailable")
        except (TypeError, ValueError, KeyError, OverflowError, RecursionError):
            return _error(store, submission, "invalid", "invalid_dataset")
        except Exception:
            return _error(store, submission, "failed", "registration_failed")


def _dataset(store: Provenance, digest: str) -> dict:
    row = store.journal.connection.execute(
        "SELECT * FROM explorer_datasets WHERE manifest_sha256=?", (digest,)
    ).fetchone()
    if row is None:
        raise ExplorationError("dataset_not_registered")
    data = store.read_json(digest)
    if (not isinstance(data, dict) or data.get("schema_version") != 1
            or data.get("kind") != "explorer_dataset"):
        raise ExplorationError("invalid_dataset_manifest")
    market = _market(data.get("market"))
    if (row["market_key"] != _market_key(market)
            or row["coverage_start"] != data.get("coverage_start")
            or row["coverage_end"] != data.get("coverage_end")
            or data.get("development_policy") != "entire_dataset_development_only"):
        raise ExplorationError("dataset_registry_mismatch")
    return data


def _code_identity() -> dict:
    from quanto import admission, alpaca_data, alpaca_actions, policy_revision, study_suite
    directory = Path(__file__).resolve().parent
    lock = directory.parents[1] / "uv.lock"
    return {"sources": {name: hash_bytes((directory / name).read_bytes())
                         for name in ("research.py", "event_engine.py", "explorer.py", "admission.py",
                                      "alpaca_data.py", "alpaca_actions.py", "provenance.py", "ledger.py", "evaluation_registry.py",
                                      "policy_revision.py", "study_suite.py")},
            "dependency_lock_sha256": hash_bytes(lock.read_bytes()) if lock.is_file() else None,
            "entrypoint_bytecode_sha256": _function_identity(run_backtest),
            "loaded_engine_code": _loaded_engine_code(),
            "research_engine_globals": _engine_globals(research_engine),
            "event_entrypoint_bytecode_sha256": _function_identity(run_event_backtest),
            "loaded_event_engine_code": _loaded_engine_code(event_engine),
            "event_engine_globals": _engine_globals(event_engine),
            "loaded_admission_globals": _engine_globals(admission),
            "loaded_bars_provider_globals": _engine_globals(alpaca_data),
            "loaded_actions_provider_globals": _engine_globals(alpaca_actions),
            "loaded_policy_revision_globals": _engine_globals(policy_revision),
            "loaded_study_suite_globals": _engine_globals(study_suite),
            "event_policy": event_engine.policy_identity(),
            "python": platform.python_version(), "implementation": platform.python_implementation()}


def _function_identity(function: FunctionType, _stack=()) -> str:
    if id(function) in _stack:
        raise ExplorationError("cyclic_loaded_function_default")
    def portable(code):
        return code.replace(co_filename="<module>", co_consts=tuple(
            portable(value) if isinstance(value, CodeType) else value for value in code.co_consts
        ))
    # Marshal v2 avoids reference-tracking flags varying with transient reference
    # counts. Normalize filenames so moving a checkout does not change behavior identity.
    def default(value):
        if value is None or type(value) in (str, int, float, bool):
            return value
        if isinstance(value, type):
            return {"class": value.__module__ + "." + value.__qualname__}
        if isinstance(value, FunctionType):
            return {"function": _function_identity(value, (*_stack, id(function)))}
        if isinstance(value, (tuple, list)):
            return {"type": type(value).__name__, "items": [default(item) for item in value]}
        if isinstance(value, (set, frozenset)):
            return {"type": type(value).__name__,
                    "items": sorted((default(item) for item in value), key=canonical_json)}
        if isinstance(value, dict) and all(isinstance(key, str) for key in value):
            return {"type": "dict", "items": {key: default(item) for key, item in value.items()}}
        raise ExplorationError("unsupported_loaded_function_default")

    closure = {}
    for name, cell in zip(function.__code__.co_freevars, function.__closure__ or ()):
        try:
            contents = cell.cell_contents
        except ValueError:
            raise ExplorationError("empty_loaded_function_closure") from None
        closure[name] = default(contents)
    return hash_json({
        "code_sha256": hash_bytes(marshal.dumps(portable(function.__code__), 2)),
        "defaults": default(function.__defaults__),
        "keyword_defaults": default(function.__kwdefaults__),
        "closure": closure,
    })


def _loaded_engine_code(module=research_engine) -> dict:
    """Fingerprint loaded helpers too: disk files may change after module import."""
    result = {}
    for name, value in sorted(vars(module).items()):
        if getattr(value, "__module__", None) != module.__name__:
            continue
        if isinstance(value, FunctionType):
            result[name] = _function_identity(value)
        elif isinstance(value, type):
            for attribute, method in sorted(vars(value).items()):
                if isinstance(method, (staticmethod, classmethod)):
                    method = method.__func__
                if isinstance(method, FunctionType):
                    result[f"{name}.{attribute}"] = _function_identity(method)
                elif isinstance(method, property):
                    for accessor in ("fget", "fset", "fdel"):
                        function = getattr(method, accessor)
                        if function is not None:
                            result[f"{name}.{attribute}.{accessor}"] = _function_identity(function)
    return result



def _engine_globals(module) -> dict:
    """Bind mutable policy globals and imported Quanto helpers used by the engine."""
    from decimal import Decimal, Context
    from fractions import Fraction

    def encode(value):
        if value is None or type(value) in (str, int, float, bool):
            return value
        if isinstance(value, bytes):
            return {"bytes_sha256": hash_bytes(value)}
        if isinstance(value, (Decimal, Fraction)):
            return {"type": type(value).__name__, "value": str(value)}
        if isinstance(value, re.Pattern):
            return {"pattern": encode(value.pattern), "flags": value.flags}
        if isinstance(value, Context):
            return {"context": str(value)}
        if isinstance(value, (list, tuple, set, frozenset)):
            items = [encode(item) for item in value]
            if isinstance(value, (set, frozenset)):
                items.sort(key=canonical_json)
            return {"type": type(value).__name__, "items": items}
        if isinstance(value, dict) and all(isinstance(key, str) for key in value):
            return {key: encode(item) for key, item in value.items()}
        if isinstance(value, FunctionType):
            return {"function": _function_identity(value)}
        if isinstance(value, type):
            return {"class": value.__module__ + "." + value.__qualname__}
        return {"binding_type": type(value).__module__ + "." + type(value).__qualname__}

    return {name: encode(value) for name, value in sorted(vars(module).items())
            if not name.startswith("__")}

def _counts(store: Provenance, market: dict) -> dict:
    row = store.journal.connection.execute(
        "SELECT COUNT(DISTINCT fingerprint), COUNT(*) FROM explorer_executions WHERE market_key=?",
        (_market_key(market),),
    ).fetchone()
    return {"recorded_candidate_count": row[0], "recorded_execution_count": row[1]}


def run_submission(root: Path, request: dict | str, *, suite_run_id: str | None = None) -> dict:
    """Record an exploratory request before parsing/specification construction.

    Fields are dataset_sha256, study_name, evaluation_start, evaluation_end,
    specification, with admission_sha256 required for historical data and a
    registered suite_sha256 for D007 policy revisions. All loaded coverage is development-only.
    Malformed bounded JSON is retained by hash. Unbounded/unencodable API envelopes
    fail the provenance preflight boundary before a submission can be recorded.
    """
    from quanto.admission import AdmissionError
    from quanto.policy_revision import PolicyRevisionError, validate_study
    from quanto.study_suite import StudySuiteError, validate_membership, validate_launch
    with Provenance(root) as store:
        _schema(store)
        frozen_request = _envelope(request)
        submission = store.begin("exploratory_study", frozen_request)
        attempt, publishing, evidence = None, False, None
        try:
            data = _request(frozen_request)
            required = {"dataset_sha256", "study_name", "evaluation_start",
                        "evaluation_end", "specification"}
            if not required <= set(data) or set(data) - (required | {
                "admission_sha256", "suite_sha256", "result_storage"
            }):
                raise ExplorationError("invalid_study_fields")
            large_result = "result_storage" in data
            if large_result and data["result_storage"] != "bounded_large_json":
                raise ExplorationError("unsupported_result_storage")
            study = _text(data["study_name"])
            digest = _ref(data["dataset_sha256"])
            manifest = _dataset(store, digest)
            market = manifest["market"]
            with store.journal._transaction():
                prior = _exposure_in_transaction(
                    store, submission, digest, market, manifest["exposure_start"],
                    manifest["exposure_end"], study, "exploratory_access",
                )
            evidence = manifest["evidence_kind"]
            admission = None
            suite = None
            if evidence == "historical_market_data":
                if "admission_sha256" not in data:
                    raise ExplorationError("historical_admission_required")
                from quanto.admission import validate_admission
                admission = validate_admission(store, _ref(data["admission_sha256"]), digest)
                if admission.get("policy_revision_sha256"):
                    if large_result:
                        raise ExplorationError("revised_policy_large_result_not_supported")
                    validate_study(store, admission["policy_revision"], data)
                    if "suite_sha256" not in data:
                        raise ExplorationError("registered_study_suite_required")
                    suite = validate_membership(store, _ref(data["suite_sha256"]), data,
                                                before_submission_id=submission)
                    validate_launch(store, suite_run_id, data, submission, bind=True)
                elif "suite_sha256" in data:
                    raise ExplorationError("suite_policy_revision_required")
            elif evidence != "synthetic_fixture" or manifest["admission_status"] != "synthetic_only":
                raise ExplorationError("unsupported_evidence_kind")
            elif "admission_sha256" in data:
                raise ExplorationError("synthetic_admission_not_applicable")
            elif "suite_sha256" in data:
                raise ExplorationError("synthetic_suite_not_applicable")
            # Re-read both source and normalized objects: identity strings alone
            # cannot certify that the exact bytes still exist or are unchanged.
            store.read_bytes(_ref(manifest["source_sha256"]))
            bars = _bars(store.read_json(_ref(manifest["bars_sha256"])), market)
            sessions = [bar.timestamp.date().isoformat() for bar in bars]
            if (sessions != manifest["sessions"] or len(bars) != manifest["bar_count"]
                    or sessions[0] != manifest["coverage_start"]
                    or sessions[-1] != manifest["coverage_end"]):
                raise ExplorationError("dataset_coverage_changed")
            start, end = _day(data["evaluation_start"]), _day(data["evaluation_end"])
            if start > end or start.isoformat() not in sessions or end.isoformat() not in sessions:
                raise ExplorationError("evaluation_window_unavailable")
            if not isinstance(data["specification"], dict):
                raise ExplorationError("invalid_specification")
            try:
                specification = StrategySpec(**data["specification"])
            except (TypeError, ValueError, OverflowError):
                raise ExplorationError("invalid_specification") from None
            first, last = sessions.index(start.isoformat()), sessions.index(end.isoformat())
            if first < specification.lookback:
                raise ExplorationError("insufficient_common_window_warmup")
            selected = bars[first - specification.lookback:last + 1]
            expected = [bar.timestamp.date() for bar in selected]
            code = _code_identity()
            frozen = {"strategy": asdict(specification), "evaluation_start": start.isoformat(),
                      "evaluation_end": end.isoformat(), "initial_position": "cash",
                      "benchmark": "buy_and_hold_same_window_same_costs", "purpose": "exploratory"}
            if large_result:
                frozen["result_storage"] = "bounded_large_json"
            identities = {"dataset_sha256": digest, "bars_sha256": manifest["bars_sha256"],
                          "source_sha256": manifest["source_sha256"], "market": market}
            if admission is not None:
                identities.update(admission_sha256=data["admission_sha256"],
                                  actions_sha256=hash_json(admission["actions"]),
                                  admission_dependencies=admission["artifact_refs"])
                frozen.update(admission_scope=admission["scope"], numerical_policy=event_engine.policy_identity())
            if suite is not None:
                identities.update(suite_sha256=data["suite_sha256"],
                                  suite_dependencies=suite["artifact_refs"],
                                  policy_revision_sha256=suite["policy_revision_sha256"])
            fingerprint = store.journal.register_experiment(
                frozen, identities, code, evidence,
                assumptions={"development_policy": "entire_dataset_development_only"},
            )
            attempt = store.journal.start_attempt(fingerprint)
            with store.journal._transaction():
                store.journal.connection.execute("INSERT INTO explorer_executions VALUES (?,?,?,?)",
                                                 (submission, attempt, fingerprint, _market_key(market)))
                store.journal._event("explorer_execution_registered", {
                    "submission_id": submission, "attempt_id": attempt, "fingerprint": fingerprint,
                }, store.journal._now())
            if admission is not None:
                report = run_event_backtest(selected, specification, corporate_action_events=admission["actions"],
                                           expected_session_dates=expected, evidence_kind=evidence,
                                           price_basis=manifest["price_basis"])
                rechecked = validate_admission(store, data["admission_sha256"], digest)
                if suite is not None:
                    validate_study(store, rechecked["policy_revision"], data)
                    if validate_membership(store, data["suite_sha256"], data,
                                           before_submission_id=submission) != suite:
                        raise ExplorationError("suite_dependencies_changed")
                    validate_launch(store, suite_run_id, data, submission)
            else:
                report = run_backtest(selected, specification, expected_session_dates=expected,
                                      evidence_kind=evidence, price_basis=manifest["price_basis"]).to_dict()
            if _code_identity() != code:
                raise ExplorationError("code_changed_during_execution")
            publishing = True
            publish_result = store.put_large_json if large_result else store.put_json
            artifact = publish_result({
                "schema_version": 1, "result_kind": "exploratory_result", "evidence_kind": evidence,
                "investment_evidence": False, "dataset_sha256": digest, "frozen_request": frozen,
                "code_identity": code, "development_policy": "entire_dataset_development_only",
                "prior_exposure": "unknown_outside_application", "engine_report": report,
                "admission_sha256": data.get("admission_sha256"),
                "admission_limitations": admission["limitations"] if admission else [],
                "admission_evidence": admission,
                "study_suite": suite,
            })
            counts = _counts(store, market)
            details = {"result_kind": "exploratory_result", "artifact_sha256": artifact,
                       "dataset_sha256": digest, "fingerprint": fingerprint, "attempt_id": attempt,
                       "evidence_kind": evidence, "investment_evidence": False,
                       "prior_recorded_overlap_count": prior, **counts,
                       "artifact_refs": sorted({artifact, digest, manifest["bars_sha256"], manifest["source_sha256"]}
                                               | ({data["admission_sha256"], *admission["artifact_refs"]} if admission else set())
                                               | ({data["suite_sha256"], *suite["artifact_refs"]} if suite else set()))}
            if large_result:
                details["result_storage"] = "bounded_large_json"
            if admission is not None:
                details["admission_sha256"] = data["admission_sha256"]
            if suite is not None:
                details.update(suite_sha256=data["suite_sha256"],
                               suite_run_id=suite_run_id,
                               policy_revision_sha256=suite["policy_revision_sha256"])
            _finish(store, submission, "success", details, attempt=attempt,
                    attempt_result={"artifact_sha256": artifact, "evidence_kind": evidence,
                                    "admission_sha256": data.get("admission_sha256")})
            return {"submission_id": submission, "status": "success", **details}
        except (ExplorationError, AdmissionError, PolicyRevisionError, StudySuiteError) as exc:
            return _error(store, submission, "invalid", str(exc), attempt=attempt, evidence=evidence)
        except (OSError, sqlite3.Error):
            return _error(store, submission, "interrupted",
                          "publication_interrupted" if publishing else "storage_interrupted", attempt=attempt, evidence=evidence)
        except (ProvenanceError, LedgerError):
            return _error(store, submission, "interrupted" if publishing else "invalid",
                          "publication_interrupted" if publishing else "artifact_or_storage_unavailable",
                          attempt=attempt, evidence=evidence)
        except ResearchValidationError:
            return _error(store, submission, "invalid", "engine_rejected_input", attempt=attempt, evidence=evidence)
        except Exception:
            return _error(store, submission, "failed", "execution_failed", attempt=attempt, evidence=evidence)


def list_exposures(root: Path, market: dict, start: str, end: str, *, limit: int = 100) -> list[dict]:
    """Inspect overlapping development records regardless of study name or byte revision."""
    market = _market(market)
    start, end = _day(start).isoformat(), _day(end).isoformat()
    if start > end or type(limit) is not int or not 1 <= limit <= 1000:
        raise ExplorationError("invalid_exposure_query")
    with Provenance(root) as store:
        _schema(store)
        rows = store.journal.connection.execute(
            "SELECT * FROM explorer_exposures WHERE market_key=? AND coverage_start<=? "
            "AND coverage_end>=? ORDER BY observed_at, rowid LIMIT ?",
            (_market_key(market), end, start, limit),
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["market"] = json.loads(item.pop("market_identity"))
            item["development_policy"] = "entire_dataset_development_only"
            item["prior_exposure"] = "unknown_outside_application"
            result.append(item)
        return result

"""Bounded, read-only Alpaca observations; acquisition is not research admission."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time as day_time, timedelta, timezone
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import re
import stat
import time
from typing import Callable
from urllib.parse import parse_qsl, urlencode, urlsplit
from zoneinfo import ZoneInfo

from quanto.ledger import canonical_json
from quanto.provenance import Provenance, ProvenanceError

NY = ZoneInfo("America/New_York")
UTC = timezone.utc
MAX_PAGES = 8
MAX_PAGE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_TOTAL_SECONDS = 60
MAX_BARS = 10_000
MIN_REQUEST_INTERVAL = 1.0
PAGE_LIMIT = 1000
MAX_REQUEST_BYTES = 64 * 1024
SYMBOL = re.compile(r"[A-Z][A-Z0-9.-]{0,14}\Z")
TOKEN = re.compile(r"[A-Za-z0-9_+/=.-]{1,2048}\Z")
SECRET = re.compile(rb"sk-ant-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|"
                    rb"(?:APCA_API_SECRET_KEY|APCA-API-SECRET-KEY|ANTHROPIC_API_KEY)\s*[=:]")
BAR_FIXED = {"timeframe": "1Day", "feed": "sip", "currency": "USD", "asof": "-"}
ERRORS = {
    "request_invalid", "request_unrecordable", "clock_invalid", "credentials_unavailable",
    "request_timeout", "network_unavailable", "transport_invalid", "route_refused",
    "redirect_refused", "access_denied", "rate_limited", "provider_http_error",
    "response_oversized", "credential_reflection", "response_invalid", "coverage_invalid",
    "pagination_incomplete", "empty_coverage", "storage_unavailable", "acquisition_failed",
}


class AcquisitionError(ValueError):
    """Fixed categories only: no provider body, credential, or arbitrary error text."""

    def __init__(self, category: str, *, status: str = "invalid", http_status: int | None = None):
        self.category = category if category in ERRORS else "acquisition_failed"
        self.status = status
        self.http_status = http_status
        super().__init__(self.category)


@dataclass(frozen=True, repr=False)
class Credentials:
    key_id: str
    secret: str


@dataclass(frozen=True)
class HTTPResult:
    status: int
    body: bytes


def _utc(clock: Callable | None) -> datetime:
    value = clock() if clock else datetime.now(UTC)
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise AcquisitionError("clock_invalid")
    return value.astimezone(UTC)


def _json(raw: bytes | str):
    def reject(_):
        raise ValueError("nonfinite")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate")
            result[key] = value
        return result

    def finite(value):
        if isinstance(value, dict):
            for child in value.values():
                finite(child)
        elif isinstance(value, list):
            for child in value:
                finite(child)
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError("nonfinite")

    try:
        value = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw,
                           parse_constant=reject, object_pairs_hook=unique)
        finite(value)
        return value
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise AcquisitionError("response_invalid") from None


def _date(value) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise AcquisitionError("request_invalid")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise AcquisitionError("request_invalid") from None


def _request(value: dict | str, kind: str, now: datetime) -> dict:
    if isinstance(value, str):
        try:
            value = _json(value)
        except AcquisitionError:
            raise AcquisitionError("request_invalid") from None
    allowed = ({"symbol", "start", "end", "adjustment", *BAR_FIXED}
               if kind == "bars" else {"start", "end"})
    required = {"symbol", "start", "end"} if kind == "bars" else {"start", "end"}
    if not isinstance(value, dict) or not required <= value.keys() or not value.keys() <= allowed:
        raise AcquisitionError("request_invalid")
    start, end = _date(value["start"]), _date(value["end"])
    if start < date(2016, 1, 1) or end < start or (end - start).days > 20 * 366:
        raise AcquisitionError("request_invalid")
    try:
        completed = datetime.combine(end + timedelta(days=1), day_time(), NY)
    except (ValueError, OverflowError):
        raise AcquisitionError("request_invalid") from None
    if completed.astimezone(UTC) > now - timedelta(minutes=15):
        raise AcquisitionError("request_invalid")
    result = {"start": start.isoformat(), "end": end.isoformat()}
    if kind == "bars":
        if not isinstance(value["symbol"], str) or not SYMBOL.fullmatch(value["symbol"]):
            raise AcquisitionError("request_invalid")
        if any(value.get(key, default) != default for key, default in BAR_FIXED.items()):
            raise AcquisitionError("request_invalid")
        adjustment = value.get("adjustment", "raw")
        if adjustment not in ("raw", "all"):
            raise AcquisitionError("request_invalid")
        result.update(symbol=value["symbol"], adjustment=adjustment, **BAR_FIXED)
    return result


def _checked_credentials(value: Credentials) -> Credentials:
    if not isinstance(value, Credentials) or any(
        not isinstance(item, str) or not 8 <= len(item) <= 512
        or any(ord(char) < 33 or ord(char) > 126 for char in item)
        for item in (value.key_id, value.secret)
    ):
        raise AcquisitionError("credentials_unavailable", status="failed")
    return value


def local_credentials(root: Path) -> Credentials:
    """Read only this task's private .env, without executing or exporting it."""
    descriptor = None
    try:
        descriptor = os.open(Path(root) / ".env", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077
                or info.st_uid != os.getuid() or info.st_size > MAX_REQUEST_BYTES):
            raise AcquisitionError("credentials_unavailable", status="failed")
        raw = os.read(descriptor, MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES:
            raise AcquisitionError("credentials_unavailable", status="failed")
        values = {}
        for line in raw.decode().splitlines():
            if line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if key in ("APCA_API_KEY_ID", "APCA_API_SECRET_KEY"):
                if key in values:
                    raise AcquisitionError("credentials_unavailable", status="failed")
                if value.startswith(("'", '"')):
                    if len(value) < 2 or value[-1] != value[0]:
                        raise AcquisitionError("credentials_unavailable", status="failed")
                    value = value[1:-1]
                values[key] = value
        return _checked_credentials(Credentials(values.get("APCA_API_KEY_ID", ""),
                                                values.get("APCA_API_SECRET_KEY", "")))
    except (OSError, UnicodeError):
        raise AcquisitionError("credentials_unavailable", status="failed") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _route(method: str, url: str) -> None:
    """Central allowlist applies before production and injected transports alike."""
    if not isinstance(url, str) or any(char.isspace() for char in url):
        raise AcquisitionError("route_refused")
    try:
        parsed = urlsplit(url)
    except ValueError:
        raise AcquisitionError("route_refused") from None
    if method != "GET" or parsed.scheme != "https" or parsed.fragment or parsed.username:
        raise AcquisitionError("route_refused")
    try:
        pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        raise AcquisitionError("route_refused") from None
    query = dict(pairs)
    if len(query) != len(pairs):
        raise AcquisitionError("route_refused")
    if parsed.netloc == "data.alpaca.markets":
        if parsed.path == "/v1/corporate-actions":
            fixed = {"region": "us", "data_quality": "all", "sort": "asc",
                     "limit": str(PAGE_LIMIT)}
            required = {*fixed, "symbols", "start", "end"}
            if (not required <= query.keys() or not query.keys() <= required | {"page_token"}
                    or any(query.get(key) != value for key, value in fixed.items())
                    or not SYMBOL.fullmatch(query.get("symbols", ""))
                    or "page_token" in query and not TOKEN.fullmatch(query["page_token"])):
                raise AcquisitionError("route_refused")
            try:
                if _date(query["end"]) < _date(query["start"]):
                    raise AcquisitionError("route_refused")
            except AcquisitionError:
                raise AcquisitionError("route_refused") from None
            return
        match = re.fullmatch(r"/v2/stocks/([A-Z][A-Z0-9.-]{0,14})/bars", parsed.path)
        fixed = {**BAR_FIXED, "limit": str(PAGE_LIMIT), "sort": "asc"}
        required = {*fixed, "adjustment", "start", "end"}
        if (not match or not required <= query.keys()
                or not query.keys() <= required | {"page_token"}
                or any(query.get(key) != value for key, value in fixed.items())
                or query.get("adjustment") not in ("raw", "all")
                or "page_token" in query and not TOKEN.fullmatch(query["page_token"])):
            raise AcquisitionError("route_refused")
    elif parsed.netloc == "paper-api.alpaca.markets":
        if parsed.path != "/v2/calendar" or query.keys() != {"start", "end"}:
            raise AcquisitionError("route_refused")
    else:
        raise AcquisitionError("route_refused")


def _http(method: str, url: str, headers: dict, timeout: float, max_bytes: int) -> HTTPResult:
    """Direct TLS connection: no proxy, redirect handling, retry, or order route."""
    _route(method, url)
    parsed = urlsplit(url)
    deadline = time.monotonic() + timeout
    connection = http.client.HTTPSConnection(parsed.hostname, timeout=min(15, timeout))
    try:
        connection.connect()
        sock = connection.sock
        if sock is None:
            raise AcquisitionError("network_unavailable", status="failed")

        def remaining():
            value = deadline - time.monotonic()
            if value <= 0:
                raise AcquisitionError("request_timeout", status="failed")
            sock.settimeout(min(15, value))

        remaining()
        connection.request(method, parsed.path + "?" + parsed.query, headers=headers)
        remaining()
        response = connection.getresponse()
        if response.status != 200:
            return HTTPResult(response.status, b"")
        chunks, count = [], 0
        while True:
            remaining()
            chunk = response.read1(min(65536, max_bytes + 1 - count))
            if not chunk:
                break
            chunks.append(chunk)
            count += len(chunk)
            if count > max_bytes:
                raise AcquisitionError("response_oversized", status="failed")
        if time.monotonic() > deadline:
            raise AcquisitionError("request_timeout", status="failed")
        return HTTPResult(response.status, b"".join(chunks))
    finally:
        connection.close()


def _dispatch(method: str, url: str, keys: Credentials, timeout: float,
              max_bytes: int, transport: Callable | None = None) -> HTTPResult:
    _route(method, url)
    _checked_credentials(keys)
    headers = {"APCA-API-KEY-ID": keys.key_id, "APCA-API-SECRET-KEY": keys.secret,
               "Accept": "application/json", "User-Agent": "Quanto/0.1 personal-research"}
    try:
        result = (transport or _http)(method, url, headers, timeout, max_bytes)
    except AcquisitionError:
        raise
    except (TimeoutError,):
        raise AcquisitionError("request_timeout", status="failed") from None
    except Exception:
        raise AcquisitionError("network_unavailable", status="failed") from None
    if (not isinstance(result, HTTPResult) or type(result.status) is not int
            or not 100 <= result.status <= 599 or not isinstance(result.body, bytes)):
        raise AcquisitionError("transport_invalid", status="failed")
    if result.status != 200:
        category = ("redirect_refused" if 300 <= result.status < 400 else
                    "access_denied" if result.status in (401, 403) else
                    "rate_limited" if result.status == 429 else "provider_http_error")
        raise AcquisitionError(category, status="failed", http_status=result.status)
    if len(result.body) > max_bytes:
        raise AcquisitionError("response_oversized", status="failed")
    _safe_body(result.body, keys)
    return result


def _safe_body(raw: bytes, keys: Credentials) -> None:
    try:
        text = raw.decode("utf-8")
    except UnicodeError:
        raise AcquisitionError("response_invalid") from None
    # Also refuse ASCII credentials encoded with JSON unicode escapes. This
    # intentionally errs toward withholding suspicious bytes from storage.
    candidates = [text]
    # Decode each string literal independently, including when the complete JSON
    # is malformed or has duplicate keys. Quoted/backslash-containing secrets
    # must not escape the check merely because JSON has escaped them.
    for match in re.finditer(r'"(?:[^"\\]|\\.)*"', text):
        try:
            candidates.append(json.loads(match[0]))
        except ValueError:
            pass
    candidates.append(re.sub(r"\\u00([0-9a-fA-F]{2})",
                             lambda match: chr(int(match[1], 16)), text).replace("\\/", "/"))
    if any(SECRET.search(value.encode("utf-8", errors="replace"))
           or keys.key_id in value or keys.secret in value for value in candidates):
        raise AcquisitionError("credential_reflection", status="failed")


def _number(value, *, positive: bool) -> float | int:
    if type(value) not in (int, float):
        raise AcquisitionError("response_invalid")
    try:
        valid = math.isfinite(value) and (value > 0 if positive else value >= 0)
    except OverflowError:
        valid = False
    if not valid:
        raise AcquisitionError("response_invalid")
    return value


def _bar(row, request: dict) -> dict:
    if not isinstance(row, dict) or not {"t", "o", "h", "l", "c", "v"} <= row.keys():
        raise AcquisitionError("response_invalid")
    raw_timestamp = row["t"]
    if not isinstance(raw_timestamp, str) or len(raw_timestamp) > 80:
        raise AcquisitionError("response_invalid")
    try:
        timestamp = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
        if timestamp.utcoffset() is None:
            raise ValueError("naive")
        local = timestamp.astimezone(NY)
        if local.time() != day_time():
            raise ValueError("not a NY daily bucket")
    except (ValueError, OverflowError):
        raise AcquisitionError("response_invalid") from None
    if not request["start"] <= local.date().isoformat() <= request["end"]:
        raise AcquisitionError("coverage_invalid")
    prices = {name: _number(row[field], positive=True)
              for name, field in (("open", "o"), ("high", "h"), ("low", "l"), ("close", "c"))}
    if prices["low"] > min(prices["open"], prices["close"]) or prices["high"] < max(prices["open"], prices["close"]):
        raise AcquisitionError("response_invalid")
    return {"timestamp": local.isoformat(), "source_timestamp": raw_timestamp,
            "symbol": request["symbol"], **prices, "volume": _number(row["v"], positive=False)}


def _calendar(rows, request: dict) -> list[dict]:
    if not isinstance(rows, list) or len(rows) > MAX_BARS:
        raise AcquisitionError("response_invalid")
    result = []
    for row in rows:
        if not isinstance(row, dict) or not {"date", "open", "close"} <= row.keys():
            raise AcquisitionError("response_invalid")
        try:
            session = _date(row["date"])
            if not request["start"] <= session.isoformat() <= request["end"]:
                raise ValueError("range")
            times = {}
            for key in ("open", "close"):
                if not isinstance(row[key], str) or not re.fullmatch(r"\d{2}:\d{2}(?::\d{2})?", row[key]):
                    raise ValueError("time")
                times[key] = datetime.combine(session, day_time.fromisoformat(row[key]), NY)
            if times["open"] >= times["close"] or result and result[-1]["date"] >= row["date"]:
                raise ValueError("order")
        except (ValueError, TypeError):
            raise AcquisitionError("response_invalid") from None
        result.append({"date": session.isoformat(), "open": times["open"].isoformat(),
                       "close": times["close"].isoformat()})
    return result


def _url(request: dict, kind: str, token: str | None = None) -> str:
    if kind == "calendar":
        return "https://paper-api.alpaca.markets/v2/calendar?" + urlencode(request)
    start = datetime.combine(date.fromisoformat(request["start"]), day_time(), NY)
    end = datetime.combine(date.fromisoformat(request["end"]) + timedelta(days=1), day_time(), NY)
    query = {**BAR_FIXED, "adjustment": request["adjustment"], "start": start.astimezone(UTC).isoformat(),
             "end": (end - timedelta(microseconds=1)).astimezone(UTC).isoformat(),
             "limit": PAGE_LIMIT, "sort": "asc"}
    if token is not None:
        query["page_token"] = token
    return "https://data.alpaca.markets/v2/stocks/" + request["symbol"] + "/bars?" + urlencode(query)


def _acquire(root: Path, request: dict | str, kind: str, *, transport=None,
             clock=None, credentials: Credentials | None = None) -> dict:
    try:
        store = Provenance(root)
    except (ProvenanceError, OSError, ValueError):
        return {"submission_id": None, "status": "rejected", "error": "storage_unavailable"}
    with store:
        try:
            if not isinstance(request, (dict, str)):
                raise ValueError("unrecordable")
            frozen_request = canonical_json(request) if isinstance(request, dict) else request
            submission = store.begin("alpaca_" + kind, frozen_request)
        except (ProvenanceError, ValueError, TypeError, RecursionError, OverflowError):
            return {"submission_id": None, "status": "rejected", "error": "request_unrecordable"}
        pages, rows, refs = [], [], []
        normalized_request = None
        manifest = {"schema_version": 1, "provider": "alpaca", "kind": kind,
                    "submission_id": submission, "evidence_kind": "historical_market_data",
                    "admission_status": "inspection_only", "research_eligible": False,
                    "rights": {"status": "account_and_exchange_terms_not_certified",
                               "use": "owner_authorized_private_inspection",
                               "public_distribution": False, "external_model_transmission": False,
                               "terms_reference": "https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf"},
                    "source_documentation": ["https://docs.alpaca.markets/us/docs/market-data-faq",
                                             "https://docs.alpaca.markets/us/reference/stockbars",
                                             "https://docs.alpaca.markets/us/v1.4.2/reference/getcalendar-1"]}
        started = time.monotonic()
        try:
            now = _utc(clock)
            manifest["started_at"] = now.isoformat()
            manifest["normalizer_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            normalized_request = _request(frozen_request, kind, now)
            keys = _checked_credentials(credentials) if credentials is not None else local_credentials(root)
            try:
                _safe_body(json.dumps(normalized_request).encode(), keys)
            except AcquisitionError:
                normalized_request = None
                raise
            request_manifest = {"method": "GET", "request": normalized_request,
                                "url": _url(normalized_request, kind),
                                "max_pages": MAX_PAGES if kind == "bars" else 1,
                                "max_total_bytes": MAX_TOTAL_BYTES,
                                "max_total_seconds": MAX_TOTAL_SECONDS}
            request_hash = store.put_json(request_manifest)
            refs.append(request_hash)
            manifest["request_sha256"] = request_hash
            store.journal.append_event("acquisition_request_prepared", {
                "submission_id": submission, "request_sha256": request_hash})
            token, seen_tokens, total, last_request_at = None, set(), 0, None
            for page in range(MAX_PAGES if kind == "bars" else 1):
                if last_request_at is not None:
                    delay = MIN_REQUEST_INTERVAL - (time.monotonic() - last_request_at)
                    if delay > 0:
                        time.sleep(delay)
                remaining = MAX_TOTAL_SECONDS - (time.monotonic() - started)
                if remaining <= 0:
                    raise AcquisitionError("request_timeout", status="failed")
                url = _url(normalized_request, kind, token)
                last_request_at = time.monotonic()
                response = _dispatch("GET", url, keys, remaining,
                                     min(MAX_PAGE_BYTES, MAX_TOTAL_BYTES - total), transport)
                if time.monotonic() - started > MAX_TOTAL_SECONDS:
                    raise AcquisitionError("request_timeout", status="failed")
                total += len(response.body)
                digest = store.put_bytes(response.body)
                refs.append(digest)
                observation = {"page": page + 1, "url": url, "retrieved_at": _utc(clock).isoformat(),
                               "http_status": 200, "raw_sha256": digest, "bytes": len(response.body)}
                pages.append(observation)
                store.journal.append_event("acquisition_page_received", {
                    "submission_id": submission, **observation})
                body = _json(response.body)
                if kind == "calendar":
                    rows = _calendar(body, normalized_request)
                    break
                if (not isinstance(body, dict) or body.get("symbol") != normalized_request["symbol"]
                        or not isinstance(body.get("bars"), list) or "next_page_token" not in body):
                    raise AcquisitionError("response_invalid")
                for raw_bar in body["bars"]:
                    row = _bar(raw_bar, normalized_request)
                    if rows and row["timestamp"] <= rows[-1]["timestamp"]:
                        raise AcquisitionError("coverage_invalid")
                    rows.append(row)
                    if len(rows) > MAX_BARS:
                        raise AcquisitionError("response_oversized")
                token = body["next_page_token"]
                if token is None:
                    break
                if not isinstance(token, str) or not TOKEN.fullmatch(token) or token in seen_tokens:
                    raise AcquisitionError("pagination_incomplete")
                seen_tokens.add(token)
                if page + 1 == MAX_PAGES or total >= MAX_TOTAL_BYTES:
                    raise AcquisitionError("pagination_incomplete")
            if not rows:
                raise AcquisitionError("empty_coverage")
            coverage = {"requested_start": normalized_request["start"],
                        "requested_end": normalized_request["end"], "pagination_complete": True,
                        "calendar_status": "unverified", "corporate_actions": "unknown",
                        "historical_information": "latest_retrieved_revision_not_point_in_time"}
            normalized = {"schema_version": 1, "evidence_kind": "historical_market_data",
                          "kind": "daily_bars" if kind == "bars" else "exchange_calendar",
                          "research_eligible": False, "admission_status": "inspection_only",
                          "identity": {"provider": "alpaca", "asset_class": "us_equity",
                                       "session_timezone": "America/New_York"}, "coverage": coverage}
            if kind == "bars":
                coverage.update(returned_start=rows[0]["timestamp"][:10], returned_end=rows[-1]["timestamp"][:10])
                normalized.update(price_basis=normalized_request["adjustment"], bars=rows)
                normalized["identity"].update(symbol=normalized_request["symbol"], feed="sip", currency="USD",
                                               symbol_mapping="disabled_asof_dash", stable_entity_id=None)
            else:
                coverage.update(returned_start=rows[0]["date"], returned_end=rows[-1]["date"],
                                calendar_status="provider_calendar_received_not_independently_certified")
                normalized["sessions"] = rows
            normalized_hash = store.put_json(normalized)
            refs.append(normalized_hash)
            manifest.update(status="success", normalized_sha256=normalized_hash,
                            row_count=len(rows), finished_at=_utc(clock).isoformat())
        except AcquisitionError as exc:
            manifest.update(status=exc.status, error=exc.category, http_status=exc.http_status)
        except (ProvenanceError, OSError):
            manifest.update(status="failed", error="storage_unavailable")
        except Exception:
            manifest.update(status="failed", error="acquisition_failed")
        manifest.update(request=normalized_request, pages=pages,
                        limitations=["Acquisition is not a research-admission or investment-performance result.",
                                     "Current downloaded revisions do not establish historical information availability.",
                                     "Calendar, corporate-action treatment, data-use rights and execution timing need admission evidence.",
                                     "Daily OHLC uses eligible trades; the open is not certified as an executable primary auction fill.",
                                     "Daily stock volume can include extended-hours trades excluded from daily OHLC.",
                                     "No point-in-time universe, stable issuer mapping, or survivorship-free coverage is established."])
        try:
            receipt_hash = store.put_json(manifest)
            refs.append(receipt_hash)
            details = {"receipt_sha256": receipt_hash, "artifact_refs": list(dict.fromkeys(refs)),
                       "error": manifest.get("error"), "research_eligible": False}
            store.finish(submission, manifest["status"], details)
        except (ProvenanceError, OSError, ValueError):
            # The initial submission stays pending if evidence publication cannot be completed.
            return {"submission_id": submission, "status": "pending", "error": "storage_unavailable"}
        return {"submission_id": submission, "status": manifest["status"],
                "receipt_sha256": receipt_hash, "normalized_sha256": manifest.get("normalized_sha256"),
                "row_count": manifest.get("row_count", 0), "error": manifest.get("error"),
                "research_eligible": False, "admission_status": "inspection_only"}


def acquire_bars(root: Path, request: dict | str, *, transport=None, clock=None,
                 credentials: Credentials | None = None) -> dict:
    return _acquire(root, request, "bars", transport=transport, clock=clock, credentials=credentials)


def acquire_calendar(root: Path, request: dict | str, *, transport=None, clock=None,
                     credentials: Credentials | None = None) -> dict:
    return _acquire(root, request, "calendar", transport=transport, clock=clock, credentials=credentials)

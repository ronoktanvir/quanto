# Data-source acquisition boundary

The D005 Alpaca adapter acquires a bounded, private US-equity observation with durable provenance. It does not admit that observation to the research engine. Every resulting dataset and receipt carries `evidence_kind: historical_market_data`, `admission_status: inspection_only`, and `research_eligible: false`. A successful HTTP request is evidence of that request's access and returned bytes; it does not certify investment performance, complete market coverage, or data-use rights.

## Documented availability and private use

Alpaca documents free historical SIP access when the requested end is at least 15 minutes old, while free real-time equity coverage uses IEX. The documented Basic historical coverage begins in 2016. This adapter explicitly requests SIP, never substitutes another feed, and requires the complete requested New York end date to be at least 15 minutes old. Account entitlement remains unverified until an actual owner-authorized request succeeds. No subscription purchase is needed or attempted. Sources: [market-data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq), [plans and coverage](https://docs.alpaca.markets/us/docs/about-market-data-api), [historical bars](https://docs.alpaca.markets/us/reference/stockbars).

The owner has authorized a private acquisition pilot. The general [Alpaca Terms and Conditions](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf), reviewed by the lead on 2026-11-02 UTC, describe personal/noncommercial use on page 1 and redistribution, publication, and commercial-copying restrictions on page 2. The separate NASDAQ and NYSE subscriber PDFs could not be inspected through the research browser, and the owner's accepted account/exchange agreements have not been audited. The receipt therefore records `account_and_exchange_terms_not_certified`; it does not claim rights approval. The [official disclosures index](https://alpaca.markets/disclosures) identifies the additional agreements.

Keep raw data, normalized market values, and data-bearing reports local and outside Git and external-model packets. Public repository examples use synthetic fixtures. No corporate-action, SEC, crypto, or macro acquisition is implemented in this module; the D005 source review records those sources' separate access and rights questions.

## Request and result contract

```python
from pathlib import Path
from quanto.alpaca_data import acquire_bars, acquire_calendar

root = Path("/path/to/private/quanto")
receipt = acquire_bars(root, {
    "symbol": "AAPL", "start": "2024-06-03", "end": "2024-06-05",
    "feed": "sip", "timeframe": "1Day", "currency": "USD",
    "asof": "-", "adjustment": "raw",
})
calendar = acquire_calendar(root, {"start": "2024-06-03", "end": "2024-06-05"})
```

These are example calls, not evidence that either request has executed. Both functions also accept raw JSON text. Passing file text directly preserves a bounded malformed JSON submission before parsing. Duplicate JSON keys and non-finite numbers are rejected. Bar requests require one uppercase US symbol, explicit inclusive ISO calendar dates, a start no earlier than 2016-01-01, and a span of at most 7,320 days. Optional fields have the fixed values shown above, except `adjustment` may be `raw` or `all`; the default is `raw`. Unknown fields are rejected. Calendar requests permit only `start` and `end`, with the same historical-date bounds.

The standard result contains `submission_id`, `status`, `receipt_sha256`, `normalized_sha256` or null, `row_count`, `error` or null, and the inspection-only labels. Status is `success`, `invalid`, or `failed`. A storage failure after submission can return `pending`; process interruption also leaves a pending submission for later reconciliation. A bounded malformed request is recorded by its hash before request or credential validation. Unserializable, unencodable, or greater-than-64-KiB inputs return `rejected/request_unrecordable` without a submission; unavailable storage can likewise prevent recording. These boundaries do not claim to capture arbitrary unbounded input.

Credentials are read only from the owner's local `.env`: `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY`. The file must be a regular file owned by the current user, have no group/other permissions, and not be a symlink. The reader does not execute the file, export values, or fall back to process environment variables. Synthetic tests inject a `Credentials` object; production callers should use the private local file. No credential or credential-bearing header is recorded in request manifests, receipts, URLs, or errors.

## Network and failure bounds

The central allowlist permits only the following routes, and validates it before invoking even a test transport. The corporate-action extension belongs to D006 and is documented separately:

- `GET https://data.alpaca.markets/v2/stocks/{symbol}/bars`, with fixed daily SIP/USD parameters, explicit raw/all adjustment, and `asof=-` disabling automatic historical symbol mapping.
- `GET https://paper-api.alpaca.markets/v2/calendar`, with explicit start/end parameters. This is a calendar read, not an order operation. The [calendar reference](https://docs.alpaca.markets/us/v1.4.2/reference/getcalendar-1) describes market dates, opening/closing times, and early closures.
- `GET https://data.alpaca.markets/v1/corporate-actions`, with explicit symbol/process dates and fixed all-category US parameters. [Action sources](ACTION_SOURCES.md) describes this extension's preservation, normalization and limits.

The direct TLS client has no proxy, redirect, retry, or trading route. Limits are eight bar pages, 1,000 requested rows per page, 10,000 normalized rows, 2 MiB per response, 8 MiB per acquisition, and a 60-second elapsed deadline. Sequential requests within an acquisition are separated by at least one second; this is not an account-wide concurrent-client rate limiter. Socket operations use timeouts of at most 15 seconds and the remaining acquisition deadline. An over-deadline response is rejected. OS DNS resolution is not strictly cancellable by the socket timeout, so this is not yet a hard process-level wall-clock guarantee during a resolver stall.

Every bounded request is first represented by a provenance submission. Before network access, the adapter stores a safe request manifest and an `acquisition_request_prepared` event. Each safe successful response is stored verbatim by SHA-256 before semantic parsing, with its page ordinal, safe URL/query, retrieval time in UTC, status, byte count, and `acquisition_page_received` event. The receipt records the normalizer source-file hash and links the canonical request, raw pages, and normalized data. Terminal outcome publication verifies all referenced artifacts through `Provenance`.

Safe malformed response bytes remain available for inspection. Non-200 response bodies and responses that reflect configured credentials or recognized credential patterns are withheld from storage; only fixed error categories and safe HTTP status values remain. Raw pages already acquired before a later failure remain linked to the failure receipt. No automatic retry follows a partial acquisition. Process interruption leaves the committed submission and any completed page events visible; recovery and deliberate retry must preserve that ambiguity and create a new request identity.

## Normalization and unresolved admission evidence

The daily dataset uses `kind: daily_bars`. Its identity records Alpaca, US equities, the requested ticker, SIP, USD, `America/New_York`, `symbol_mapping: disabled_asof_dash`, and `stable_entity_id: null`. A raw ticker is not a permanent issuer identity. Each row contains the original provider `source_timestamp`, an aware New York-midnight `timestamp`, symbol, OHLC, and volume. The parser verifies that the provider timestamp converts exactly to New York midnight, including daylight-saving offsets. The midnight label identifies a daily bucket; it is not historical signal availability or an execution instant.

All OHLC values must be finite and positive, volume finite and nonnegative, and high/low consistent with open/close. Bars must be strictly increasing, unique, in the requested date window, and for the requested symbol. Pagination must terminate explicitly. Duplicate or overlapping bars, unsafe/repeated page tokens, missing fields, empty total coverage, out-of-range bars, and exhausted bounds are rejected; data is never filled, deduplicated silently, or spliced across feeds. Exhausted pagination does not prove session completeness. Requested/returned dates and the unknown calendar/action states remain explicit in `coverage`.

Alpaca's [aggregation rules](https://docs.alpaca.markets/us/docs/market-data-faq) distinguish price-eligible trades from volume: extended-hours trades can contribute daily volume without updating daily OHLC. A bar's open is not certified as a fill at the primary exchange's opening auction. A newly downloaded historical bar is the provider's current revision, not proof of the value available to a strategy at the historical decision time. Raw prices omit action/dividend accounting; `all` adjusted prices are a separate inspection artifact, never mixed with raw prices or sent to the engine by this adapter.

Calendar datasets use `kind: exchange_calendar`, with ordered date/open/close sessions and aware New York timestamps. They preserve early closing times and raw source bytes, but use `calendar_status: provider_calendar_received_not_independently_certified`. Empty calendar responses, including a weekend-only window, currently produce `empty_coverage`; they do not establish a complete empty schedule. Calendar receipts do not automatically certify associated price coverage.

Acquisition alone never grants research admission. The separate D006 boundary checks source receipts, calendar comparisons, supported corporate actions, attributed issuer facts and a source-use review for conditional retrospective development research. The software passed independent verification. Two actual admission refusals are preserved; the pilot currently requires a separately reviewed split-entitlement policy before calculation. Multi-decade delisted history, point-in-time universes and fundamentals, empirical execution costs, and prospective paper trading remain future work. The adapter never invokes the backtest engine or a broker order API.

## Verification scope

The lead executed three owner-authorized private requests on 2026-11-02 UTC for the 2024-01-02 through 2024-01-31 pilot: raw daily SIP bars, the paper-account calendar, and separately adjusted daily bars. All succeeded with 21 rows each; the three session-date lists matched. Raw and adjusted price fields differed on all 21 rows, which demonstrates why price-basis handling cannot be ignored. This comparison does not identify the complete action history or certify execution assumptions. The exact receipts and check report remain in ignored local storage; market values are not published here. The run used immutable JSON CLI requests and the adapter revision `88c60d80be6295767c8cc9de65c239a5d528135c0bb89de98b7574cad52bb2eb`. Later dict-request freezing was verified separately with synthetic regression tests.

`tests/test_alpaca_data.py` uses synthetic responses and temporary stores only. It covers pagination, request-before-network recording, malformed requests and responses, source preservation, credentials and redirect refusal, escaped credential reflection, partial failure, byte/page/time bounds, New York summer/winter buckets, calendar early closes, and interruption. These tests establish software behavior; they do not establish provider entitlement, source accuracy, legal permission, or investment performance. Any actual acquisition must be reported separately with its own receipt.

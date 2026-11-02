# Corporate-action acquisition

`quanto.alpaca_actions.acquire_actions(root, request, *, transport=None, clock=None, credentials=None)` records bounded corporate-action observations from the owner's existing Alpaca account. Acquisition remains inspection-only. It does not establish economic coverage, data rights, historical knowledge, or permission to calculate a strategy.

## Frozen request and transport

The input is an object or strict JSON string containing exactly `symbol`, `start` and `end`. The dates are explicit inclusive ISO dates defining a chosen **process-date search envelope**; the end cannot exceed the acquisition UTC date. There is no inferred 2016 corporate-action history floor. The dates are not an ex-date interval, a guaranteed economic coverage interval, or completed-bar boundaries.

The sole route is `GET https://data.alpaca.markets/v1/corporate-actions`. The receipt's semantic request uses singular `symbol`, consistent with the bar adapter; the exact prepared URL and each page URL use the provider's plural `symbols` query parameter. Every request fixes `region=us`, `data_quality=all`, `sort=asc` and `limit=1000`. It omits `types`, because a split/dividend-only query would conceal unsupported events. No alternate announcement endpoint, source substitution, redirects, retries, or trading routes are available.

The adapter reuses the existing protected credential reader, central route allowlist, credential-reflection checks and direct bounded HTTPS transport. It permits at most eight pages, 2 MiB per page, 8 MiB total, 60 seconds, and a one-second minimum interval between request starts. Each request receives the remaining deadline and byte allowance. Parsing that exceeds the observed deadline fails after retaining the safe page. Complete bytes returned late by an injected transport are likewise retained and refused; the production transport can instead raise its deadline error before returning bytes. A cap hit remains an incomplete failed/invalid acquisition. It never becomes a narrower successful query.

The initial submission freezes the input before reading the clock or dispatching. The prepared request artifact records the exact first URL, semantic parameters, bounds and all-category policy. Safe original request bytes are also stored as `submitted_request_sha256`, matching the submission's request digest. Request text is checked for credential reflection before it is stored; invalid original inputs are represented by the submission digest rather than unconditionally persisted.

## Source retention and normalized contract

Every successfully returned safe, bounded page is content-addressed before action parsing. Page observations retain its ordinal, exact URL including pagination token, retrieval timestamp, byte count and SHA-256 identity. Provider error/redirect bodies and credential-reflecting content are withheld. Earlier pages survive later parse, pagination, transport or storage failures. Receipt publication or terminal-submission publication failure returns `pending`; it never reports success without a committed outcome. Interruption also leaves the submission pending and does not authorize a retry.

The current official schema has sixteen category arrays:

- `reverse_splits`, `forward_splits`, `unit_splits`
- `cash_dividends`, `stock_dividends`, `capital_gains_distributions`
- `spin_offs`, `cash_mergers`, `stock_mergers`, `stock_and_cash_mergers`
- `redemptions`, `name_changes`, `worthless_removals`
- `rights_distributions`, `partial_calls`, `reorganizations`

All returned categories are retained. New category arrays are preserved and listed in `unknown_categories`; acquisition does not certify their accounting support. Null category values, non-array categories and non-object records cannot satisfy the normalized record contract, so they cause an invalid outcome while their safe source bytes remain available. Missing optional categories and explicitly empty arrays stay distinguishable in the exact source and `categories_present` metadata.

The normalized artifact contains:

```text
schema_version: 1
kind: corporate_actions
evidence_kind: historical_market_data
identity: {provider: alpaca, symbol, asset_class: us_equity}
coverage: {requested_start, requested_end, pagination_complete: true,
           historical_information: latest_retrieved_revision_not_point_in_time,
           date_semantics: process_date_envelope,
           economic_window_coverage: not_assessed, ...}
records: [{category, record, occurrences: [{raw_sha256, page, index}]}]
```

`page` is one-based; `index` is zero-based within the source category array. Each source record occurrence remains a separate normalized entry. Identical records, repeated IDs and conflicting terms are not collapsed. Admission must decide whether economic terms are duplicates or conflicts. Incomplete fields, unexpected identities, negative amounts and dates outside the request envelope also remain available for admission rather than disappearing through acquisition filtering.

Action numbers are parsed directly to `Decimal`, then represented as decimal strings within each normalized record, including nested numeric values. Booleans, nulls, empty strings and missing fields retain their distinctions. For example, `0.1000000000000000000001` remains that exact decimal value, `1.2300` retains its scale, and `2.50e-3` becomes `"0.00250"`. Exact original lexemes always remain in the raw page. Duplicate JSON keys and non-finite constants reject. Numeric page tokens retain their numeric type until validation and cannot silently become accepted string tokens.

`next_page_token` must be explicitly present. Only null establishes terminal pagination; short or empty pages with tokens continue. Unsafe or repeated tokens reject. A fully paginated empty response is a successful observation with `no_records_returned_not_absence_proof`, zero rows and `inspection_only` status. It does not establish that no economically relevant action occurred.

## Receipt and limits of inference

Receipts use `provider=alpaca`, `kind=actions`, schema version 1, the frozen normalized request, prepared request hash, original submitted request hash, normalizer and shared transport source hashes, raw page references, normalized artifact hash when successful, submission ID and terminal status. Pagination completion, normalization status and the unperformed coverage assessment are separate fields. Source bytes and data-bearing receipts remain private local artifacts outside Git and external-model packets.

`data_quality=all` includes early incomplete records. It does not promise exhaustive action creation, processing timeliness, fields, correction history, delisted coverage or stable issuer identity. Process-date coverage is distinct from ex/effective-date coverage and a payment tail. All snapshots are latest retrieved revisions, not point-in-time information history. Ordinary dividend currency and share basis, split terms, unsupported categories, identity continuity, issuer corroboration and scoped economic relevance require a separate admission decision. Rights remain `account_and_exchange_terms_not_certified`; acquisition does not widen the already-authorized private inspection scope.

The frozen public-source evidence is recorded in [D006 source advice](reviews/D006-action-sources.md). The contract follows the [Alpaca corporate-actions reference](https://docs.alpaca.markets/us/reference/corporateactions-1) and the [official pinned OpenAPI specification](https://github.com/alpacahq/cli/blob/709d11400129dc7c09b41dd05263187e15801a71/api/specs/market-data-api.json). Synthetic tests establish adapter behavior only; they do not demonstrate account entitlement or investment performance.

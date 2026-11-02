# D006 corporate-action sources and access advice

Attribution: independently briefed source/access adviser `/root/d006_actions_source_adviser`. Research performed 2026-11-02 UTC (clock observation 03:52:39 UTC). This is source and acquisition-contract advice, not independent implementation certification, legal certification, or an investment result.

## Recommendation and evidence boundary

Use Alpaca's current market-data corporate-actions REST endpoint for a bounded private acquisition, preserve every returned category, and normalize supported ordinary USD cash dividends and simple forward/reverse splits separately from unsupported events. A successful empty response establishes only that the particular request returned no records. It cannot establish that a price window contains no corporate actions. The financial admission decision needs an explicit assessment of identity, event-date coverage, unsupported events and accounting assumptions.

D005's three successful owner-authorized raw SIP, adjusted SIP and calendar requests (21 rows each) are reported by the inspected project documents. I did not inspect their private receipts, source values or credentials. Those requests establish neither corporate-action endpoint entitlement nor complete action history. I made no authenticated/provider-data request, accessed no `.env`, runtime file or raw market-data object, and called no paid model. All network research here used public official documentation, official issuer/fund pages and Alpaca's public source repository.

## Inspected revision and sources

Local HEAD was `fffc374ba14e74d6cf801f409efb8cb5d4b44990`; working tree was clean before this report. Exact inspected local SHA256 values:

| Artifact | SHA256 |
| --- | --- |
| `AGENTS.md` | `0f3a1577fb417c2434383f426895aad1fcd540feed7e81aa4a2362a4d9fefc86` |
| `docs/CONTEXT.md` | `9a6ea5a4ea276f38073c56533013feac8cbe369d7ab1167e3a181b799236698e` |
| `docs/STATUS.md` | `d7bef4193172a604ffb7895e74b5cb8e090f8f978c58233233ee4731e956cac1` |
| `docs/ROADMAP.md` | `471c604e8b5a89b952b86751f67d87618f86d78b75989c3af07ddbb81e1b17bf` |
| `docs/HANDOFF.md` | `5c912a96d58d8e8e825007a5b0a74758537863f7e53d8352d81cd67ed8435617` |
| `docs/DECISIONS.md` (including D005) | `0ad2cf27c048a21e3db048b01f3ee423a5b9353d2939f0d5fc25474577107b7b` |
| `docs/DATA_SOURCES.md` | `a44a4db6b8f964afaadd867fc83691014039bf5dcef4c36e97d9ed3c63d20adc` |
| `src/quanto/alpaca_data.py` | `8ef36538adcb424928a95116d66835387eedb98cc27b5b67e624825875bc015c` |

All external sources below were retrieved or checked on 2026-11-02 UTC. The schema source is the [official Alpaca CLI market-data OpenAPI specification at commit `709d11400129dc7c09b41dd05263187e15801a71`](https://github.com/alpacahq/cli/blob/709d11400129dc7c09b41dd05263187e15801a71/api/specs/market-data-api.json), fetched publicly without credentials. Its exact bytes have SHA256 `2856fc7ed4dc6aa55a7b5db453a3cb8c5e9270b56e0679ded695bd926ec4e7dc`; the pinned and then-current main versions matched. OpenAPI is a documented contract, not an observed account response.

## Current REST acquisition contract

The production read endpoint is `GET https://data.alpaca.markets/v1/corporate-actions`, authenticated with the existing Alpaca API-key pair. It is distinct from the older trading endpoint `/v2/corporate_actions/announcements`. The [official SDK documentation](https://alpaca.markets/sdks/python/api_reference/trading/corporate-actions.html) marks the trading announcements call deprecated in favor of the market-data call; no legacy route should be silently substituted.

The [current reference](https://docs.alpaca.markets/us/reference/corporateactions-1) documents inclusive ISO-date `start`/`end`, sorting by `process_date`, `sort=asc|desc`, `symbols`, `cusips`, and optional `types`. `region=us|non_us|all` defaults to US. `ids` is mutually exclusive with the other filters. `limit` is 1–1,000, default 100, across all data points rather than per symbol. Follow `next_page_token` using `page_token`; short or empty pages alone do not terminate pagination.

There is no `date_type=ex_date` parameter on this endpoint. The start/end descriptions explicitly identify process-date ordering but do not separately spell out a filtering expression. Treat the interval operationally as a process-date interval, never an ex-date guarantee; preserve that documentation wording and validate actual returned boundaries during acquisition. Query defaults are the current day, so production requests must always send explicit dates.

The pinned OpenAPI requires a response object containing `corporate_actions` and `next_page_token`. The inner object has optional arrays, whose keys and request type names differ:

| Request type | Response array |
| --- | --- |
| `reverse_split` | `reverse_splits` |
| `forward_split` | `forward_splits` |
| `unit_split` | `unit_splits` |
| `cash_dividend` | `cash_dividends` |
| `stock_dividend` | `stock_dividends` |
| `spin_off` | `spin_offs` |
| `cash_merger` | `cash_mergers` |
| `stock_merger` | `stock_mergers` |
| `stock_and_cash_merger` | `stock_and_cash_mergers` |
| `redemption` | `redemptions` |
| `name_change` | `name_changes` |
| `worthless_removal` | `worthless_removals` |
| `rights_distribution` | `rights_distributions` |
| `partial_call` | `partial_calls` |
| `reorganization` | `reorganizations` |
| `capital_gains_distribution` | `capital_gains_distributions` |

This complete category list comes from the pinned official specification's `cas_types` and `corporate_actions` schemas. Older documentation/SDKs expose fewer categories and are insufficient as an exhaustive allowlist. Omit the `types` filter during the admission acquisition: requesting only splits/dividends would conceal unsupported events. Missing optional arrays may be represented internally as empty *returned* categories while preserving their absence in the source; this does not assert true-world absence. Unknown nonempty categories must be preserved and block unsupported accounting rather than be dropped.

## Fields and semantics that matter to accounting

The following schema facts come from the pinned official OpenAPI's `cash_dividend`, `forward_split`, `reverse_split` and shared date schemas. Required is a schema label; it does not override the documented possibility of incomplete real records.

| Event | Schema-required fields | Additional documented fields |
| --- | --- | --- |
| Cash dividend | `id`, `symbol`, `cusip`, `rate`, `special`, `foreign`, `process_date`, `ex_date` | `currency`, `isin`, `record_date`, `payable_date`, `due_bill_on_date`, `due_bill_off_date`, `sub_type` |
| Forward split | `id`, `symbol`, `cusip`, `new_rate`, `old_rate`, `process_date`, `ex_date` | `currency`, `isin`, `record_date`, `payable_date`, `due_bill_redemption_date` |
| Reverse split | `id`, `symbol`, `old_cusip`, `new_cusip`, `new_rate`, `old_rate`, `process_date`, `ex_date` | `currency`, old/new ISIN, `new_symbol`, `record_date`, `payable_date` |

Dates are date strings, not timestamped publication observations. The shared definitions distinguish the shareholder cutoff (`ex_date`), ownership record (`record_date`), payment/distribution (`payable_date`) and Alpaca processing (`process_date`). None identifies when the strategy could historically have known the event. Cash dividends and simple splits have **no `declaration_date` field** in this current REST schema. Normalize it as unknown/null, never manufacture it from another date or retrieval time.

The REST numeric fields are JSON numbers described as doubles. Preserve raw numeric lexemes or parse with decimal arithmetic before deriving ratios or money amounts; do not introduce binary-float rounding into the canonical event ledger. Split `old_rate` and `new_rate` fields have no further descriptions in this current schema. The older [official announcements reference](https://docs.alpaca.markets/us/reference/getcorporateannouncements) explicitly calls `new_rate` the numerator and `old_rate` the denominator of a position quantity-change ratio. Accordingly `new_rate / old_rate` is the proposed share multiplier, subject to a known issuer split reconciliation before financial admission; its reciprocal applies to earlier per-share price basis. Zero, negative or non-finite rates cannot support this calculation.

Cash `rate` has no per-share description in the current schema; the older announcements reference describes its `cash` amount per share, and issuer distributions can corroborate the convention. Do not infer gross/net tax treatment, ADR fees, withholding, fraction rounding or cash-in-lieu rules from the REST number. `foreign` and `special` are booleans without richer semantics here. `sub_type` can identify `interest` or `return_of_capital`; those should not silently become ordinary dividends. Due-bill fields require dedicated handling; `due_bill_on_date`/`off_date` have no explanatory descriptions in this schema.

The currency definition explicitly permits an empty value to mean USD, inapplicable, **or unknown**, with later changes possible. Thus missing/empty currency must remain unresolved unless separate source evidence establishes the payout currency. A US ticker or USD bar request does not establish dividend currency. Missing ISIN may be legitimate; a changing CUSIP or ticker prevents treating either as a permanent issuer identifier.

Fund distributions require special attention: the separate `capital_gains_distributions` schema contains long-term and/or short-term per-share rates. At least one leg is expected. This is not a `cash_dividends` alias, and handling only that array can omit ETF/fund cash flows. Unit splits can create an alternate security, stock dividends have their own `rate`, and reorganizations may have multiple stock legs. Preserve them as unsupported until their distinct accounting is implemented and reviewed.

## Coverage, timing and the empty-response problem

`data_quality=complete` is the default. It excludes early incomplete, unprocessed actions, but already-processed actions can still be returned despite incomplete fields. `data_quality=all` includes the early incomplete records. Alpaca explicitly disclaims guaranteed creation time; upstream delivery and internal processing may delay availability after announcement. Consequently neither option means that all real actions or necessary fields are present. These are documented provider limitations, not observed omissions in the owner's data. [Current reference](https://docs.alpaca.markets/us/reference/corporateactions-1).

The reviewed official material does not establish a corporate-action historical inception date, guaranteed delisted-security coverage, correction/deletion history for REST snapshots, maximum announcement delay, maximum difference between process and ex/pay dates, or exhaustive historical category coverage. The bar plan's historical availability since 2016 is not a corporate-action coverage promise. No specific provider event omission was reproduced in this assignment.

For a price window `[S,E]`, fetching action `start=S,end=E` can miss a cash entitlement whose ex-date is inside the window and process/pay date is after E. An earlier process date could likewise precede S. No documented finite padding (30, 90, 365 days, or otherwise) guarantees coverage. A concrete bounded first pilot can request all categories with `region=us,data_quality=all,sort=asc,limit=1000` over a declared wider process span, for example 2016-01-01 through the acquisition date for the historical January 2024 pilot. That is a **chosen search envelope**, not a provider-certified historical floor, maximum lag or absence proof. Events processed outside that envelope, future processes and later additions remain limitations.

Normalize the whole retrieved envelope first, then select economic relevance using ex/effective dates and position entitlements, with pending payables allowed to extend beyond E. Preserve records with unknown event dates for review; excluding them because they cannot be dated would conceal the precise uncertainty. Record the complete process envelope, requested identity set, returned process/ex/pay ranges, all category counts, and pagination status separately from `economic_window_coverage`.

A useful admission standard is scoped, corroborated support rather than an impossible claim of universal vendor certainty: establish the instrument identity; compare known issuer/fund action histories across and around `[S,E]`; reconcile returned supported actions and dated unsupported actions; explicitly enumerate residual coverage limitations. A source disagreement, unresolved currency/date/identity, or relevant unsupported action blocks that financial calculation. A fully paginated empty response can be recorded as successful acquisition with `no_records_returned`; it cannot itself satisfy this admission standard. This avoids both fabricated completeness and a permanent synthetic-only definition of the project.

## Adjusted prices and ticker history are supporting evidence

Alpaca's [historical-bar reference](https://docs.alpaca.markets/us/reference/stockbars) offers raw, split, dividend, spin-off and combined adjustments. Split adjustment affects price and volume; dividend/spin-off adjustment affects price. `all` combines the documented adjustments. The same reference explains that `asof` enables historical name mapping and `asof=-` disables it. D005 deliberately disables mapping.

The price ratio `adjusted / raw` is a provider-derived adjustment diagnostic, not an event ledger. Constant ratios can reflect actions after the sampled price window; a ratio change does not uniquely identify cash, split, spin-off, entitlement or settlement. Equality does not prove no actions. Ratios can support reconciliation against known actions or a separately declared adjusted-return study, but cannot establish raw-share/cash accounting or executable prices. The inspected official OpenAPI has no separate adjustment-factor route among its 44 paths; that observation does not prove no such Alpaca product exists. Do not invent an endpoint.

Current `name_changes` contain old/new symbols and CUSIPs, optional ISINs and process date, with no separate effective/publication date. Reverse splits may carry a changed symbol. Neither those records nor automatic bar mapping establishes a complete point-in-time security master or historical universe. If a requested ticker's historical continuity cannot be supported, restrict the admitted instrument/window or refuse the calculation; never silently splice successor/predecessor bars or claim survivorship-free research.

## Entitlement and private-use restrictions

The [official pricing page](https://alpaca.markets/data) marks corporate actions included in both Free and paid plans. The [plan documentation](https://docs.alpaca.markets/us/docs/about-market-data-api) identifies Basic as the default free option for paper/live accounts and gives Basic historical API limits. This supports trying the existing account without buying anything. It does not establish this account's corporate-action access, date retention or field completeness. Only a bounded actual response can establish that request's access; preserve 401/403/429 outcomes and do not purchase, upgrade or silently switch source.

The [general terms](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf), pages 1–2, limit usage to personal/noncommercial purposes, restrict publication/redistribution and commercial copying without consent, disclaim completeness, and incorporate additional agreements. Private local own-account API analysis is consistent with the stated personal-use purpose; this is an interpretation, not certification of every accepted agreement. No special blanket prohibition on local automation was identified in those terms. Keep values and data-bearing reports local, outside Git and external-model packets.

The [disclosures index](https://alpaca.markets/disclosures) links NASDAQ and NYSE subscriber agreements. Both linked PDFs returned 403 to the research browser, and the owner's accepted versions and classifications remain uninspected. Retain `account_and_exchange_terms_not_certified`; do not turn a failed public-document fetch into an invented requirement that the owner reapprove the already-authorized private pilot. Redistribution, commercial expansion and new subscriptions remain outside scope. These unresolved agreements require further factual review before claiming broader rights.

## Official-source fallback and operational normalization proposal

Issuer/fund pages are documented corroboration or fallback sources, with their own terms and provenance, not automatic replacements. [Apple's dividend history](https://investor.apple.com/dividend-history/default.aspx) supplies declared/record/payable dates, amounts and split entries and expressly says amounts are not split-adjusted; it does not provide an ex-date column. [Apple's FAQ](https://investor.apple.com/investor-relations/faq/default.aspx) supplies split history. Those different date labels must not be merged by guesswork. [State Street's US distribution history](https://www.ssga.com/us/en/institutional/resources/documents/etf-dividend-distributions) supplies ex/record/payable dates, amounts and separate capital-gain columns plus an official historical download link. A scheduled future distribution list is not proof that every historical event occurred, and a CDI/UCITS page is not interchangeable with the US-listed fund. This adviser has not approved their terms for bulk automated extraction; use documented official downloads/manual evidence with recorded source-use review, no third-party scraping or access-control bypass.

The proposed implementation contract is:

1. Add only the exact market-data corporate-actions GET path to the central allowlist; freeze explicit symbol/identity, process envelope, `region=us`, `data_quality=all`, all-category policy and page limits in a submission before dispatch. Keep market values private. Production credentials remain in the existing protected reader; reviewers/model assistants receive none.
2. Retain D005 transport bounds initially: at most eight pages, 1,000 requested records per page, 2 MiB/page, 8 MiB total and 60 seconds, with one-second inter-request spacing, no redirects, implicit retries or trade routes. A bound hit is incomplete acquisition, never complete empty coverage. Deliberate larger/chunked acquisitions need explicit new recorded requests and aggregate bounds; there is no claim of account-wide throttling.
3. Store safe successful raw page bytes and exact URL/query, source/retrieval times, page ordinal, body hash, schema/source identities and normalizer hash before parsing. Preserve partial pages and invalid/incomplete records; withhold credential echoes/non-200 unsafe bodies under the existing policy. An interrupted attempt remains pending.
4. Reject malformed envelopes, duplicate JSON keys, non-finite numbers, unsafe/repeated tokens and missing explicit terminal pagination. Do not require distinct events to have distinct process dates. Preserve exact duplicates with their page references as a coverage anomaly; conflicting rows for one provider ID require reconciliation, never last-row-wins. Preserve all returned known/unknown categories even if unsupported.
5. Canonical normalized rows should contain provider ID, category, raw-record hash and page reference, symbol(s)/CUSIP(s)/ISIN(s), all source date labels, decimal rate fields, currency and flags, `retrieved_at`, `known_at_status=latest_snapshot_not_point_in_time`, parsing completeness and unsupported reasons. Keep absent, null and empty source values distinguishable in raw provenance. Do not coerce incomplete data into fully specified events.
6. Derive only validated simple split ratios and ordinary USD cash dividends after rate/currency/date/identity reconciliation. Cash should accrue as a receivable at the supported entitlement boundary and become spendable only under the explicit payment policy; process date is never an automatic payout date. Carry terminal unpaid receivables explicitly. Taxes, DRIP, short dividends, due bills, special dividends, foreign payouts, return of capital and fractional cash-in-lieu remain unsupported unless reviewed separately.
7. Publish separate states for acquisition success, pagination completion, normalized-record completeness, scoped economic coverage assessment and financial admission. All action downloads initially remain `historical_market_data`, `inspection_only`, `research_eligible=false`. Link the eventual admission decision to exact bars/calendar/actions/issuer evidence, code identity and limitations; do not let a caller-authored `complete=true` substitute for those references.

Required next evidence is an actual bounded existing-account corporate-actions response, known issuer split/dividend normalization reconciliation, a scoped pilot coverage assessment, and independent implementation criticism/quality/scope review of the eventual exact artifacts. A useful proposed pilot is AAPL January–June 2024 for ordinary cash distributions, plus a separate 2020 split window for quantity accounting. This is advice only: the lead will select the exact windows after the panel and outside critique, and I made no provider call. Price-window dates must remain distinct from the expanded process-date acquisition envelope. Synthetic fixtures can validate software behavior while that evidence is acquired, but cannot satisfy the financial evidence requirement.

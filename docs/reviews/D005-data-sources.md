# D005 adviser — data-source access, rights and coverage

Date: 2026-11-02 UTC. Role: independent data-source adviser. This report records documentation research, not a live-data acquisition or legal opinion. No market prices, credentials, paid providers or trading endpoints were accessed. The owner selected both asset classes with US markets first.

## Recommendation

Prioritize an explicit Alpaca historical SIP adapter for US stocks and ETFs, paired with direct SEC filing data. Begin the credential-free acquisition/provenance path with a small SEC company-concept/submissions sample while the owner supplies Alpaca credentials and applicable data-use permissions are recorded. Do not substitute crypto for the requested US-market work merely because a public endpoint is easier to call.

Alpaca's current documentation makes a decisive distinction: free real-time equities coverage is IEX, but historical SIP queries do not require a paid subscription when `end` is at least 15 minutes old. Specify `feed=sip` explicitly rather than relying on the account-dependent default. Historical requests still require the owner's API key and secret. The documented Basic plan covers US stocks/ETFs from 2016 and allows 200 historical calls per minute. [Historical-feed FAQ](https://docs.alpaca.markets/us/docs/market-data-faq), [plan and coverage documentation](https://docs.alpaca.markets/us/docs/about-market-data-api).

Concrete first price request shape, after access/rights checks:

```text
GET https://data.alpaca.markets/v2/stocks/{symbol}/bars
    ?feed=sip&timeframe=1Day&adjustment=raw&start={fixed_start}&end={fixed_end}
```

Choose a fixed historical end well outside the recent-data restriction and record the requested feed, returned coverage, adjustment policy and every pagination token. A successful response must not silently authorize a switch to IEX or prove that delisted coverage, corporate actions, or complete exchange-calendar coverage exist.

## Session meaning and supporting endpoints remain separate checks

Alpaca daily bars use a New York day bucket and trade-condition rules. Extended-hours conditions `T` and `U` contribute daily volume but do not update daily OHLC. Thus the answer is field-specific: extended-hours volume is included; treating daily OHLC as an unrestricted extended-hours aggregate is incorrect. The documented open is the first price eligible under those rules, not a guarantee of a primary-exchange opening-auction fill. Quarantine the initial daily bars until the research execution contract is verified. [Bar aggregation rules](https://docs.alpaca.markets/us/docs/market-data-faq).

The documented paper-account calendar endpoint is `GET https://paper-api.alpaca.markets/v2/calendar`. It returns market dates and session opening/closing times, including early closures; the versioned documentation describes 1970–2029 coverage. It requires account credentials and documents no separate paid market-data prerequisite. Free paper-account availability is therefore a reasonable implementation expectation, not a verified entitlement for this owner; test one bounded read after credentials exist. [Calendar reference](https://docs.alpaca.markets/us/v1.4.2/reference/getcalendar-1).

Use the current corporate-action endpoint, `GET https://data.alpaca.markets/v1/corporate-actions`. Its reference requires authentication but does not establish free-account entitlement. It documents possible publication/processing delays, interval selection by `process_date`, and a default `data_quality=complete` policy that excludes some incomplete unprocessed records. A bounded account probe and coverage audit remain necessary. An empty response does not establish that no split or dividend occurred; keep its date semantics and completeness policy separate from the bar adapter. [Corporate-action reference](https://docs.alpaca.markets/us/reference/corporateactions-1).

## Public SEC data can establish the acquisition record now

The SEC explicitly provides unauthenticated JSON APIs for company submissions and XBRL facts. A narrow first sample can pair `https://data.sec.gov/submissions/CIK0000320193.json` with `https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/Assets.json`. This tests actual provenance and filing linkage without pretending that fundamentals are executable OHLC prices. The standard XBRL APIs cover non-custom, entity-wide facts; they are not a complete normalized fundamentals warehouse. [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

Use declared, truthful application/contact identification and a conservative request rate below the SEC's aggregate ten-requests-per-second ceiling. Do not invent a contact address, evade a denial, or distribute requests across machines to bypass the limit. Larger acquisition should use the documented bulk archives rather than repeated company-by-company polling. [SEC developer resources](https://www.sec.gov/about/developer-resources).

For research availability, retain each accession, fact period, form, filing date and corresponding submission acceptance metadata. Do not map quarter-end directly to the date the strategy knew the fact. A current company-facts response can contain later amendments; reconstructing the as-known value requires filing-level selection and an explicit information-time rule. A successful fetch would not by itself establish point-in-time correctness.

## Access documentation is not a data-license review

The Alpaca findings above establish documented API availability and pricing, not the owner's account entitlement or unrestricted rights. The official disclosures library identifies Alpaca Terms & Conditions plus NASDAQ and NYSE subscriber agreements. This adviser inspected that index, but did not inspect the owner's accepted agreements or complete those agreements' clauses. Record those as pending before claiming storage, redistribution, external-model transmission or public derived-result rights are approved. Keep downloaded data private and outside Git; publish reproducible code and synthetic fixtures only until the release audit establishes otherwise. [Alpaca disclosures and agreements](https://alpaca.markets/disclosures).

The SEC access documentation was reviewed; it supports the proposed bounded acquisition mechanism. It should not be interpreted as a blanket copyright license over every issuer-authored filing attachment. Retain source citations and avoid committing source filings or raw datasets in this increment.

## Alternatives that should not become silent defaults

Coinbase's Market Data Terms, updated August 7, 2026, grant limited personal/research use but also restrict outside redistribution of data and derived work. Section 3.5 expressly restricts uses involving development, validation, benchmarking or operation of AI models, agents and automated systems. That wording is material to this project; do not select Coinbase candles for the agent desk without resolving permission for the intended use. This is a source-selection objection, not a claim that every ordinary personal chart violates the terms. [Coinbase Market Data Terms](https://www.coinbase.com/legal/market_data).

FRED's current terms also restrict uses connected with AI/software development or training, and its API terms restrict caching/archiving. A no-subscription warehouse should not assume that FRED access implies permission for this intended storage and agent workflow. Underlying government-origin sources can be assessed separately; they do not inherit FRED's API access grant merely because the numeric series is the same. [FRED legal notices and terms](https://fred.stlouisfed.org/legal/terms/).

## Required acceptance boundary

Every acquisition should retain its provider, exact safe URL/query, request/retrieval UTC times, requested and returned coverage, raw-content hash, parser/version hash, feed and adjustment identifiers, units/time zone, pagination/completeness result, source-document links and rights-review state. Preserve original bytes privately before normalization, identify revisions rather than overwriting them, and record failures as attempts. Credentials must never enter URLs, manifests, logs or source control.

The next price study remains blocked on more than a price download: the existing engine lacks corporate-action accounting and verified session calendars. A single-symbol raw-price demonstration is not a survivorship-free US equity warehouse, a dividend-aware total-return result, or a tradable strategy. The recommended source path advances the real objective while keeping those gaps explicit.

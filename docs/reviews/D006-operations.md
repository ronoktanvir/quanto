# D006 independent design advice — operations and reproducibility

Author: Codex operations adviser, independently briefed by the lead. Prepared 2026-11-02 UTC. This is one bounded operations perspective, not an implementation review, financial-accounting certification, outside-model review, or five-perspective consensus. I made no implementation edits and ran no tests. I did not read `.env`, runtime state, private data, or call provider/model endpoints.

## Recommendation

Proceed with a manual, bounded corporate-actions pilot after the D006 decision and external-model review gates. Reuse the D005 acquisition boundary: record a submission before semantic validation and network dispatch; allow only the exact HTTPS GET route; bound time, bytes, page count and inter-request spacing; reject redirects; do not retry implicitly; store each safe response page by content hash before parsing; and finish with fixed error categories. Keep this action acquisition and any resulting registration labeled `historical_market_data`, with `research_eligible=false`, until a separate evidence-backed admission step succeeds.

The attainable increment is a latest-snapshot, scoped retrospective research admission for a specifically identified security/window, with simple split and ordinary cash-dividend accounting. It is not point-in-time data, a universal completeness certificate, a historical-universe study, an execution-price certification, or profitability evidence. This boundary serves the full own-account research objective while preventing operations labels from implying financial validation.

## Exact revision and inspected artifacts

The checked-out commit is `fffc374ba14e74d6cf801f409efb8cb5d4b44990`. Existing review reports below are untracked working-tree artifacts in the inspected state. Hashes identify what I read; a later implementation or changed artifact needs its own review hashes.

| Artifact | SHA-256 |
| --- | --- |
| `AGENTS.md` | `0f3a1577fb417c2434383f426895aad1fcd540feed7e81aa4a2362a4d9fefc86` |
| `docs/CONTEXT.md` | `9a6ea5a4ea276f38073c56533013feac8cbe369d7ab1167e3a181b799236698e` |
| `docs/STATUS.md` | `d7bef4193172a604ffb7895e74b5cb8e090f8f978c58233233ee4731e956cac1` |
| `docs/ROADMAP.md` | `471c604e8b5a89b952b86751f67d87618f86d78b75989c3af07ddbb81e1b17bf` |
| `docs/DECISIONS.md` | `0ad2cf27c048a21e3db048b01f3ee423a5b9353d2939f0d5fc25474577107b7b` |
| `docs/HANDOFF.md` | `5c912a96d58d8e8e825007a5b0a74758537863f7e53d8352d81cd67ed8435617` |
| `docs/PROVENANCE.md` | `e2d055172d93f8e65d0825d9622f726f854c9cb28ba8ffa5203feba89f346260` |
| `docs/RESEARCH_PROTOCOL.md` | `7a4cce12ebc9d454b9ddd8697fb8a9c43908357f3daf7338a818eaddbbe9928d` |
| `src/quanto/alpaca_data.py` | `8ef36538adcb424928a95116d66835387eedb98cc27b5b67e624825875bc015c` |
| `src/quanto/provenance.py` | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |
| `src/quanto/explorer.py` | `47a9d6b6921418f997e8cdbc1f52f820a4e991dda52b7bc58704c2065c0e0808` |
| `docs/reviews/D006-accounting.md` | `c470a0f5d65a6c619573edb44a1111af81797faf4e32d3dc6cf9c6da009eaf74` |
| `docs/reviews/D006-admission.md` | `96621ea3ed789b4123ce54fe916ab2a2f9a4f533e6968cee4512843daff1ff77` |
| `docs/reviews/D006-action-sources.md` | `b0d04108020afc2a6adc902e53ccacc28d3ae5f65b802ab2d7a47e4d51772c05` |

## Operational controls that matter

**Treat the process-date query as a bounded retrieval envelope, not the research interval.** The current proposal filters by process date and requests `data_quality=all`, which is a useful way to include early incomplete/unprocessed records. However, the requested bar/economic window, action-source process envelope, returned process dates, event-effective dates, and payment tail are separate intervals. Keep all of them in the manifest. A chosen wider envelope such as 2016 through acquisition date is an explicit search policy, not a documented provider history floor or a proof that events outside it do not exist.

**Make partial acquisition an inspectable outcome.** Preserve the prepared request manifest and every successfully received safe page even when a later page, parser, total-time cap, or storage operation fails. Record a fixed terminal failure when the evidence can be committed; leave the submission pending if receipt publication fails. Do not normalize a page-cap or byte-cap hit into an empty result or complete search. Keep page ordinal, exact query including token identity without leaking credentials, retrieval time, raw-byte digest, byte count, and terminal pagination evidence. Duplicate provider IDs, repeated records, unknown categories, absent/null/empty fields, and unknown dates belong in the retained evidence and anomaly summary rather than being dropped by last-row-wins normalization.

**Report several completion dimensions independently.** A transport success, terminal page token, parseable response, complete fields for each returned record, scoped economic coverage assessment, and financial admission are different claims. Expose separate fields for acquisition status, pagination status, normalization status, coverage assessment, and admission status. `data_quality=all` expands what Alpaca returns; it does not mean the service returns all actions or complete fields. The provider's current snapshot and delayed processing also mean an action record's latest retrieval time cannot establish what was knowable at an earlier decision time.

**Bound broad history operationally.** Preserve conservative D005 limits initially, for example eight pages, 1,000 requested rows per page, 2 MiB per page, 8 MiB total, 60 seconds, and at least one second between requests. If an explicitly chosen process envelope cannot fit, split it into separately frozen, clearly adjacent date chunks under a documented aggregate cap. Retain every chunk's request and receipt and link them from a parent acquisition record. A bound hit is incomplete, not a reason for unbounded retries or silent narrowing. The existing shared USD 20/day limit governs outside-model use; it is not a local mechanism to claim control over unrelated clients of that account, and no paid model call is needed for this acquisition pilot.

**Bind admission to actual receipts and software identity.** Admission must reference the exact bar, calendar, all-category action, and any issuer/fund corroboration artifacts by content hash, as well as their request/receipt hashes, retrieval timestamps, declared coverage, parser/schema version, and code identity. Keep the normalization and accounting version in every result. Re-run against exact stored bytes, not a later live response. A request hash alone is not enough to replay a request, while market payloads and private financial artifacts should stay out of Git and external-model packets. Capture code/specification/data identities and assumptions in the result, including the available lock/interpreter details; do not imply these attest the entire machine or malicious-local-owner resistance.

**Keep the pilot manual until durable scheduling is independently specified.** The existing local supervisor and dashboard are not evidence of a reliable research job scheduler. A future scheduler needs bounded jobs, persisted attempts, idempotent artifact publication, stale-worker fencing, explicit pending reconciliation, bounded retry policy, and observability for start/heartbeat/deadline/last-success. It should never interpret a pending acquisition as permission to rerun automatically, nor convert an old source snapshot into current coverage. Those controls can be added later; they are not prerequisites for one manually invoked pilot and no action here demonstrates unattended reliability.

## Objections and required wording

1. **Do not call this “complete historical actions” or “complete data.”** The provider reference does not certify exhaustive event creation, coverage inception, delisted issuer history, or correction history. An empty, fully paginated response only establishes that the bounded query returned no rows at retrieval time. It does not establish no economically relevant actions.
2. **Do not infer that action processing-date coverage equals economic-date coverage.** Preserve events whose relevant dates fall outside the bar window, and request a payment tail for earned entitlements. Unknown dates and incomplete records require adjudication or refusal, not omission.
3. **Do not call the historical admission point-in-time or execution-valid.** The returned dataset is a latest retrieved revision; price/action known-at time is not reconstructed. Raw daily open remains an assumed simulated fill. The strategy can support conditional descriptive research on that selected asset/window only.
4. **Do not claim schedule/cost/external review completion from this advice.** This report is one of five requested perspectives; the independent accounting, admission, and source reviewers have separate reports. Parent must complete the remaining perspectives and actual requested Opus critique before approving a significant data/accounting decision. No provider request or paid review was made by me.

The operational tradeoff is clear: conservative caps and explicit partial outcomes make the first pilot auditable but may require several manually bounded date chunks. That inconvenience is preferable to a silent incomplete fetch being treated as economic absence; unattended scheduling can follow once its retry, fencing, and reconciliation rules have their own decision and review.

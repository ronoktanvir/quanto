# D005 actual outside-model critique

Requested and reported model: `claude-opus-5-5`. Status: completed. Received: 2026-11-02T03:16:46.232719+00:00. Packet SHA-256: `766d85a50c9e5083a31a01aeb2687faea349357685d33d3bd5718fbcc2bbb382`. Usage: 17780 input tokens and 6325 output tokens. Calculated cost: USD 0.197620.

The model reviewed the proposal and five adviser reports. It did not inspect or execute the implementation. Its report is preserved below; the lead's dispositions are recorded separately in DECISIONS. Runtime retains the original response and provider request identity.

---

# D005 Adversarial Review: Acquisition, Provenance, and Exploratory Runner

**Basis and limits.** I reviewed the proposal text and the five adviser reports only. I executed no code, made no provider calls, and did not inspect source files. Code-level claims, such as `start_attempt` requiring a fingerprint or warmup shifting evaluation dates, are **reported by advisers, not independently verified**. Agreement among the advisers does not make those claims true.

## Blocking findings

**B1. The session-coverage gate cannot be met by the proposed fixed host (confirmed internal contradiction).**
- **Evidence:** The proposal fixes acquisition to one host, `data.alpaca.markets`, and requires runs to fail admission when session coverage is unresolved. The only calendar source cited (the sources report) is `paper-api.alpaca.markets/v2/calendar`, a different host that serves the trading API.
- **Check:** Find a calendar source in the proposed allowlist. There is none.
- **Correction:** Choose one calendar source explicitly.
  - Option A: a pinned, offline exchange-calendar dataset or library, recorded by version and hash.
  - Option B: a second allowlisted GET path limited to `/v2/calendar`, with no other paper-api path permitted.
- Without one of these, every real-price run is blocked by construction.

**B2. An append-only store with no deletion path conflicts with security and rights obligations (confirmed design gap).**
- **Evidence:** The proposal requires "no overwrites" and stores bounded raw submissions before validation. A pasted secret, a key echoed in an error response, or data the terms require deleting at termination would become permanently stored.
- **Check:** Submit a request containing a string shaped like an Alpaca key (paper keys begin `PK`). Confirm whether it is stored and whether any tool can remove it.
- **Correction:**
  - Scan submissions for secrets and redact them before persisting.
  - Keep raw provider bytes in a separate private store that supports an audited tombstone or purge, with the purge itself journaled.
  - Treat "no overwrite" as "no silent mutation," not "no deletion ever."

**B3. A credential cannot enforce "GET-only, no trading endpoints" (confirmed limitation).**
- **Evidence:** Alpaca paper keys are not read-only scoped. They authorize paper order placement. GET-only is self-restraint in the client. The hidden-prompt helper prevents the secret from being displayed, but not from being used by an agent with tool access, and not from leaking through the process environment, child processes, or exception traces.
- **Check:**
  - Look for any code path besides the adapter that can read the credential variable.
  - Search the journal, manifests, logs, and dashboard output for `PK` or `APCA-` prefixes.
  - Confirm that the HTTP layer rejects any method other than GET and any host or path outside the allowlist before sending.
- **Correction:**
  - Run acquisition only as an owner-invoked command.
  - Do not export the credential to agent shells.
  - Never pass it in argv or URLs.
  - Enforce the method/host/path allowlist in a single transport function, with a test asserting that `POST /v2/orders` is refused locally.

**B4. The corporate-action gate has no satisfiable evidence standard (confirmed from cited documentation).**
- **Evidence:** Both the data-integrity and sources reports state that Alpaca's corporate-actions endpoint omits incomplete records by default and filters by `process_date`. An empty response therefore cannot certify absence. The proposal says unresolved absence fails admission but defines no evidence that would resolve it. That means a permanent block or, later, an ad hoc weakening of the gate.
- **Correction:** Define the admissible evidence now. A practical minimum:
  - Acquire the same window with `adjustment=raw` and with `adjustment=all`, both recorded as artifacts.
  - If every bar is identical and the action query, run with `data_quality` explicitly set and an ex-date-padded window, is empty, record the state as `no_provider_adjustment_observed`.
  - That state is provider-dependent evidence, not proof. It admits exploratory runs only.
  - Any difference between the two series rejects the run until split/dividend accounting exists.

**B5. Content-addressed writes need crash and corruption semantics (confirmed gap in spec).**
- **Evidence:** The `interrupted` state is named but the write protocol is not. If a file already exists at a hash path, a naive "exists, so skip" accepts a truncated earlier write.
- **Correction:**
  - Write to a temporary file, fsync, verify the hash, then rename atomically.
  - On a hash-path collision, re-hash the existing bytes. Never trust the existing file.
  - On recovery, record the attempt as `interrupted/unknown`. Do not assume failure, because a crash can follow a successful response.
  - Any re-fetch is a new attempt ID.
- **Test:** Kill the process between the rename and the manifest commit, then check that recovery links the orphaned blob without inventing success.

## Non-blocking but consequential

**N1. Daily-bar date mapping (hypothesis; verify on first real response).** Alpaca daily-bar timestamps are reportedly midnight New York time expressed in UTC, so the UTC offset differs across daylight-saving changes.
- **Check:** Assert that every timestamp converts to 00:00 America/New_York.
- **Correction:** Derive the session date in New York time, never from the UTC date. Reject the response if the assertion fails.

**N2. Common evaluation dates need an engine change (reported).** The evaluation report states that evaluation begins `lookback` bars after the first supplied bar.
- **Correction:** Pass an explicit `eval_start`/`eval_end` and give each lookback exactly its required preceding warmup slice.
- **Test:** Run lookbacks 20 and 50. Assert identical strategy and benchmark scored dates, and identical benchmark entry.

**N3. Submission-first conflicts with the existing journal schema (reported).** `start_attempt` reportedly requires a registered experiment.
- **Correction:** Add a submission/acquisition record type that can later link to an experiment. Do not use placeholder data hashes.

**N4. Cost control covers cooperating clients only (confirmed from description).** The USD 20/day ledger does not cap spend by non-cooperating clients or direct API use.
- **Correction:**
  - Confirm whether a provider-side organization spend limit exists, and state "not enforced" if it does not.
  - Keep Alpaca and SEC request counters separate from model spend, but bounded.
  - Never automatically retry model calls during recovery.

**N5. Rights state needs an attainable form (confirmed gap).** "Rights resolved" cannot mean legal certification.
- **Correction:** Record an owner attestation in this form: "terms X dated Y reviewed; permitted use: private, non-redistributed, local research; external-model transmission: raw prohibited, derived metrics only."
- **Open item (hypothesis, needs evidence):** Automated SIP consumption may be classed as exchange "non-display use" under the NYSE/Nasdaq subscriber agreements. Check this before any "rights: approved" label. It does not block private local storage of a pilot.

**N6. Exposure records must cover the choice itself.** Choosing the pilot symbol and window is already an exposure.
- **Correction:**
  - Designate the whole acquired pilot range as `development_only` with `prior_exposure_unknown`.
  - Forbid later carving a final interval from it.
  - Key exposure to instrument, venue, and time, not to hashes. The proposal's "stable market/range identity" is consistent with this.

## Unnecessary gates and scope drift

- **SEC acquisition.**
  - **Acceptable:** one or two requests as a smoke test of the acquisition store, using a truthful user-agent the owner actually provides.
  - **Drift:** reporting it as warehouse (R10) progress, or building fundamentals point-in-time logic now.
  - If no truthful contact is available, skip it. Do not invent one.
- **Scope report items 5–6** (five-role workers, paper-forward trading, execution isolation). These are legitimate roadmap work but are not this increment. Bundling them delays the first verified acquisition. I disagree with including them in D005.
- **Feed fallback and retries.** Prohibiting them is correct. Deliberate manual re-attempts, linked to the prior attempt, should remain allowed so the gate does not become a dead end.
- **Crypto.** Deferring it is correct. Note that the Coinbase and FRED terms objections are **reported, not verified by me**. Alpaca crypto would need its own terms review. US-first does not settle crypto source selection.

## May proceed now

1. Content-addressed store with atomic writes, secret redaction, and a purge path (B2, B5).
2. Submission/acquisition record type with explicit states: success, invalid, failed, interrupted/unknown.
3. Transport function with method/host/path allowlist, byte, page, and time bounds, and no retries (B3), tested against fixtures and a local mock server.
4. Common-window engine change and the regression tests in N2.
5. Exploratory exposure registry.
6. Synthetic fixtures labeled `synthetic_not_market_evidence`, with that label carried through every derived output.
7. Calendar source decision (B1) and corporate-action evidence standard (B4) written down before any real-price run.

## Requires additional evidence before claims

- That the owner's account can actually retrieve historical SIP data: one bounded real request, receipt retained. Documentation alone is not entitlement.
- Exchange and Alpaca agreement terms on storage, non-display use, and derived-result transmission to external models.
- That corporate-action and calendar evidence meet the B4 and B1 standards for the specific pilot window.
- That the next-open fill assumption matches Alpaca's documented daily-open definition (first eligible trade, not the auction).
- Any "protected," "validated," or performance claim. None is supportable from this increment.

## Verdict

**Accept as an increment, conditional on corrections B1–B5.** Without them, the design either blocks every real-price run (B1, B4) or permanently retains secrets and licensed data with weak enforcement (B2, B3, B5). Nothing here supports a profitability or protected-evaluation claim.

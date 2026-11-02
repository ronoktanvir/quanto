# D006 independent quality validation

Reviewer: `/root/d006_quality`, separate from the producers, implementation critic and scope reviewer. Review completed 2026-11-02 UTC against the working tree on `feat/historical-admission`, with HEAD `c4ff21882dab1885e9707ab5a60b42dc436bb5a7`. File identities below, rather than HEAD alone, identify this uncommitted implementation. The reviewer owns only this report and edited no implementation, test or operational files.

**Result: no remaining software-quality blocker was found at these identities.** The complete suite passes 661 tests and 12 subtests both from source and from an offline-built wheel installed outside the checkout under Python 3.11. Independent rational accounting, source/failure/publication and CLI probes also pass. This clears the reviewed software increment for the next private evidence step. It does not certify a completed D006 historical pilot or the complete operation: this reviewer did not inspect actual market artifacts or run a real-data experiment.

## Inspected identities

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/event_engine.py` | `cb1a61985ebb08089eab50d00d1e78f09a83fdea6754587af7e871e177175ffc` |
| `src/quanto/alpaca_actions.py` | `f6804b8717a3dd60ff77fcf934581170b762cf82f77b5dd229c349c127205cc7` |
| `src/quanto/admission.py` | `7cd34c3244b7f87496827f933606e4000d52f4408438304ef14f27d1434cd953` |
| `src/quanto/explorer.py` | `58d3e5508cc967210ebe41fb0b07200d32090652534fb87df5749647c9f81ddd` |
| `src/quanto/alpaca_data.py` | `9182307746567e349ed1b936eb35949fac7684430336279968f02d6f35ab0c76` |
| `src/quanto/cli.py` | `b19c8927d5152a308540a3d9e3ce5e8ac70516bd91ba41d3cba776b49b1830e1` |
| `tests/test_event_engine.py` | `e096e4e919b63476fd90fa0d2433d4d739a9bfc671517547fce3077f69dd1a53` |
| `tests/test_alpaca_actions.py` | `054e7bbe2f8a8502446636b46eb629908927e3f5079cb231d3a3c0bcf4341906` |
| `tests/test_admission.py` | `e2111f2d8e84adc088e44666a7cc512e04cd12c0bf2fabba7b518b5dcf1312fb` |
| `tests/test_explorer.py` | `f2355a8629303fcd43bf1cc3ae24edc9db82b49990eefb8775eff8b0324cdc15` |
| `tests/test_cli_requests.py` | `4ff710514aed1bd4e50286521a90b21cfb1a29f152b56e8a9e480b749b9d6f30` |
| `examples/synthetic_actions.py` | `01c5b72e5be6284c36547aee9b65313ff5547499908f7b675ca70b329c6e764b` |
| `examples/synthetic_exploration.py` | `4b07deb2063bea54da092bde51866073e435223159480978b6c61a9758fd7af6` |
| `docs/ACCOUNTING.md` | `3a45f81bbf05af25f207431a67bff890a9f6bbb96998ae034dae00e0097777cc` |
| `docs/ACTION_SOURCES.md` | `6b3d81ede600e53c66d7032aa4e1b2747980496c7ec63d18793abe56e233667e` |
| `docs/RESEARCH_PROTOCOL.md` | `a0ab1a620f92fe08da39004b78bf85d2a5b1bf8327117a08990a9c47ec6a924c` |
| `pyproject.toml` | `4f37dc1155abde9f5cc2c1b3a5b02b18ca8212ea67005b8b71ee21418c4f6997` |

## Executed accounting checks

An independent reference uses `Fraction` for the whole portfolio, including quantities, cash, claims and costs. It reconstructs each signal afresh from the original historical closes, applying only splits between each observation and its signal date. It does not reuse the engine's mutable rolling-price implementation, Decimal operations, helpers or target function. Its exact results are compared with the specified precision-34 Decimal results using `max(1, absolute expected value) * 1e-28` tolerance; the tolerance acknowledges declared Decimal rounding rather than treating it as exact rational portfolio accounting.

Across 180 deterministic scenarios (seed 6006), with lookbacks 2–5, fees 0/10/25 bps, 10:1, 3:2 and 1:4 splits, several dividends and payment delays, all 20,880 daily quantity/cash/receivable/equity comparisons pass. The reusable oracle additionally checks daily returns and final equity, cash, quantity, claims, total return, fees and drawdown, giving 28,620 field comparisons over the same scenarios. The invented dates and prices are synthetic fixtures, not market performance evidence.

Separate hand-derived assertions passed:

- A 3:2 split produces an exact rational SMA tie and preserves either the prior cash state or prior long state; it creates no false split signal. An initial completed warmup signal may buy at the first scored open, with the previous session retained as its signal date.
- Starting cash 1,010 buys 10 shares at 100 with a 10 entry fee. A 100 dividend stays as cash. A later sale at 80 credits 792 after its 8 fee, yielding 892 cash and 18 total fees. The benchmark ends at 900 with its dividend and first entry fee, without a forced terminal sale.
- In a gapped-session fixture, a Saturday payable is available for Monday's open and funds 11.25 shares. A Monday payable cannot fund Monday's open: the strategy ends with 10 shares and 100 cash after modeled end-of-session release. The benchmark retains 100 cash without reinvestment in both cases.
- The installed split/dividend example buys 10 at 100, splits to 20 shares, accrues 10 and pays it into cash. Both final portfolios equal 20 shares at 50 plus 10 cash, or 1,010 equity. This also checks importability of the example outside the repository.

Producer tests, independently executed as part of the complete suite, additionally cover ex-date seller/buyer entitlement, warmup non-entitlement, nominal claims unaffected by a later split, the post-split penny-dividend basis, unpaid terminal claims, split/payment/pending-entry ordering, future-input prefix invariance, local Decimal context, calendar gaps, unsupported events and ambiguous simultaneous actions. Their synthetic status limits the conclusions to software behavior.

## Independent source, admission and failure checks

Temporary stores used only invented transport responses, fake credentials and explicitly synthetic issuer/use documents. The synthetic fixture generator supplied input data for the admission checks; the assertions below were separately selected and executed by this reviewer.

- A two-page corporate-action request observes its durable pending submission before transport. A second-page HTTP 403 produces failure after exactly two calls, preserves the first safe page byte-for-byte and by its correct hash, and never retries. All requests retain `data_quality=all` without a category filter. Fake secrets and the withheld error-body marker are absent from saved temporary-store bytes.
- Full synthetic transport acquisition, registration, admission and two registered calculations succeed. Replays have identical fingerprints/result artifacts, preserve the historical routing label and `investment_evidence: false`, and disclose unpaid dividend claims. Tombstoning the referenced primary source then refuses the same study with `artifact_or_storage_unavailable`.
- Replacing the loaded admission validation helper or action source replay helper forces readmission. A separate probe first admits with a replay helper capturing a mutable primitive dictionary, then changes only that dictionary; the prior admission refuses with `admission_dependencies_changed`. This specifically rechecks the critic's captured-closure objection.
- Conflicting returned ISINs refuse with `action_security_identifier_conflict`; the observed implementation also validates nonempty CUSIP and old/new identifier variants conservatively.
- Persistent failure of `submission_finished` during admission returns safe `pending`, with no successful admission outcome. The same injection during a registered historical calculation returns `pending`, leaves the durable submission pending and commits zero attempt outcomes. Event-chain verification passes after reopening. Unclaimed content-addressed artifacts can remain; pending is not permission to retry automatically.
- The actual CLI admission route succeeds on the synthetic evidence packet. Malformed `acquire-actions` JSON returns a nonzero exit, retains its invalid submission and does not echo the sensitive marker. The complete CLI suite also exercises bounded regular-file reads, symlink/pipe refusal and pending non-success exits.

The reviewed suite checks source-page replay against normalized bytes, actual successful receipt/submission binding, original request bytes and parameters, byte/page/pagination bounds, primary observation receipts, calendar equality, duplicates/conflicts, currency/rate basis, corruption, tombstones and changed policy. These controls establish mechanical consistency and refusal behavior. Attributed issuer extraction and source-use interpretation remain human/agent judgments tied to retained sources, not mechanically authenticated truths.

## Complete suite and clean installation

- Source run: `PYTHONPATH=src .venv/bin/python -m pytest -q` — **661 passed, 12 subtests passed**, 13.78 seconds on the final freeze.
- `.venv/bin/ruff check .` and `git diff --check` — passed.
- A temporary source tree containing only `src`, packaging metadata, README and lockfile built with `uv build --offline --wheel`. Python 3.11.9 installed with `pip install --no-index --no-deps --target ...`; the resolved imported package path was verified outside the repository.
- The wheel contains all three D006 modules and the HTML/CSS/JavaScript website assets, without data, runtime, private or `.env` entries. Its SHA-256 is `265e7df38257aa6dc159a31e46ef404798107fb7e3e265bb25975fa4d0edabc2`. This identifies the observed build, not byte-reproducible wheel timestamps.
- Installed CLI help includes `acquire-actions` and `admit-dataset`; the synthetic demo, fresh-directory registered-exploration example and split/dividend example pass. Copied tests and scripts then ran against the installed package under Python 3.11 using cached offline test dependencies: **661 passed, 12 subtests passed**, 13.45 seconds. There was no repository `src` on that run's import path.

During the changing implementation, an intermediate full run exposed the known failure-injection fixture capturing an unsupported `Path` in its closure: it was refused before computation rather than exercising the intended failure. The lead changed only that fixture capture to a string while preserving its assertions that an experiment and attempt exist before the injected computation failure. Both final complete-suite runs above pass. Earlier passing counts are superseded by this final freeze.

The critic's loaded-helper/closure identity, ISIN-conflict and persistent-publication findings are preserved in the separate criticism record. Their corrected behaviors were independently rechecked here; the quality reviewer did not implement the fixes.

## Post-acquisition relevance correction

The lead reported that actual acquisition exposed an overbroad blanket refusal of identity-category records. This reviewer independently reproduced the old `identity_change_unresolved` refusal using an invented cash-merger record describing the studied issuer as an acquirer years before the full acquired window. The correction admits only a retained, source-bound exclusion for that narrowly specified case. It adds no merger portfolio treatment, changes no strategy or evaluation window, and does not turn the acquisition's process-date envelope into an economic date.

The final admission rule requires exact normalized-record hash and category binding, exact acquirer/acquiree participants, a valid provider effective date strictly before the **full acquired start**, an attributed completion date between effectiveness and that boundary, and explicit source-bound judgments of no studied-share conversion or outstanding studied entitlement. At least one acquirer identifier must match the relevant studied corpus; all supplied acquirer identifiers must agree, and acquiree identifiers must differ. Unknown fields, mixed-stock terms, other merger categories and unresolved roles remain refused. A supplied payable must fall between effective date and completion, before the acquired start. Missing payment timing is covered only by the separately retained completion/no-entitlement judgment; it is not silently inferred from process date.

An independently written temporary matrix passes **41 scenarios** on the final correction. It checks a positive exclusion while retaining the preceding invalid submission, exact record binding, incorrect participant roles and identifiers, missing/equal-boundary/future dates, invalid or missing completion/source judgments, conversion and entitlement flags (including integer `1` versus Boolean true), unsupported categories and stock fields, duplicate annotations, unmatched exclusions and insufficient issuer continuity. Exact duplicate source records yield one exclusion with both occurrences retained; conflicting same-ID records and ambiguous multiple IDs reject before exclusion. Raw/normalized/facts corruption refuses subsequent calculation, and removing the old merger only from normalized data is caught by source replay. A **42nd independent scenario** uses a distinct completion document: admission retains its artifact reference, then tombstoning that document refuses a registered calculation.

The complete source and installed suites, original independent source/admission/publication/CLI probes, loaded-helper regressions and 180-case rational oracle were rerun after this correction. Their final results are the 661-test counts and identities recorded above. Source extraction and completion remain attributed judgments; neither a successful exclusion nor this software review certifies the private historical pilot or the legal/economic truth of the source assertions.

## Reusable independent oracle and remaining limits

The reviewer preserved `/tmp/d006_reference_oracle.py`, SHA-256 `54887dfae2f12430b5cdd9901c0c3ba367541f6eb4714b987ad68e08f0433ca1`, for the lead's later private local numerical comparison. It imports no Quanto code and performs no network calls. Invoke `python3.11 /tmp/d006_reference_oracle.py --input /absolute/local/payload.json`. The input object contains the exact selected normalized warmup/evaluation `bars` with timestamps/open/close, `specification`, canonical `corporate_action_events`, and `engine_report`. Success output contains only status/count/tolerance metadata; mismatch errors identify a portfolio, row and field without printing market values. The file is temporary and should be preserved by the lead if needed beyond this session. Its availability is not evidence that the private historical pilot has run.

No actual credentials, real project runtime/database, private data objects, provider service, paid model or broker endpoint was accessed by this reviewer. Real provider access, retained issuer facts, permitted source use and the actual split/dividend historical calculation require separate observed evidence. No actual-market numerical, investment-performance, profitability or strategy-readiness claim follows from this report.

Current-revision history, residual vendor omissions, price-normalization precision, theoretical open fills, fractional shares and nominal receivables remain disclosed modeling limits. Protected evaluation, five operational research roles, searchable failure retrieval, durable research scheduling/restore, prospective paper operation, separately credentialed execution and explicit owner live activation remain required. Event-chain checks provide consistency/tamper evidence under the documented local-owner threat model; they do not make SQLite or filesystem storage immutable.

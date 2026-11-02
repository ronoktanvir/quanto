# Registered exploratory research

`quanto.explorer` connects private artifacts to the deterministic research engine with recorded submissions, explicit dataset registration, common evaluation windows, and development exposure history. This increment can execute **synthetic fixtures only**. It validates research software and recordkeeping; it does not establish an investment result, a protected holdout, or a complete research operation.

Historical acquisitions can be registered and inspected. They remain `inspection_only`: calendar evidence, corporate action accounting, historical information timing, and permitted use have not been admitted by an implemented verification process. A supplied approval flag cannot override this gate. The next real-data increment must implement attainable evidence checks and the required accounting, rather than treating a caller declaration as proof.

## Submission and dataset contract

Both `register_dataset(root, request)` and `run_submission(root, request)` accept a dictionary or bounded raw JSON text and return a receipt dictionary. Dictionary requests are serialized once; the resulting bytes are the same bytes hashed and parsed. Raw JSON is hashed exactly as received. The submission is committed before JSON parsing, semantic validation, Bar construction, or StrategySpec construction. Malformed JSON, duplicate keys, nonfinite values supplied as text, invalid fields, missing data, and unsupported assumptions produce retained outcomes with fixed reason codes. Raw submitted content and arbitrary exception messages are not retained.

The provenance boundary accepts at most 64 KiB of UTF-8 request text. Oversized text, unsupported Python objects, unserializable dictionaries, or invalid Unicode cannot cross that boundary and do not have a submission receipt. A hash-only submission identifies the request without providing its contents for replay; preserve an approved request separately when replay is required. See [PROVENANCE.md](PROVENANCE.md) for the storage and privacy threat model.

Dataset registration accepts exactly:

| Field | Meaning |
| --- | --- |
| `data_sha256` | Existing JSON artifact identity; its actual bytes are read and verified. |
| `evidence_kind` | `synthetic_fixture` or `historical_market_data`. |
| `market` | Exactly `instrument_id`, `venue`, three-letter `currency`, and IANA `session_timezone`. |
| `price_basis` | Explicitly `raw` or `all`; only raw synthetic fixtures can compute. |
| `expected_sessions` | Ordered ISO date list, mandatory for synthetic fixtures; if supplied it must exactly match all source bar dates. |
| `parent_dataset_sha256` | Optional registered parent for the same declared instrument. |

The source may be a bar list or a JSON object containing `bars`. Every bar requires timestamp, symbol, open, high, low, close, and volume; an optional source timestamp is retained in the source artifact. Normalization constructs typed `Bar` values, rejects nonfinite/inconsistent prices and duplicate or unordered dates, and converts aware timestamps into the declared session timezone. Explicit source-envelope evidence, price basis, symbol, currency, and timezone must agree with registration metadata. No missing bar is filled or substituted.

A successful registration writes a normalized artifact and a manifest with their actual hashes, the source hash, exact dates, coverage, evidence classification, financial limitations, and admission state. Its receipt includes verified direct references to all three artifacts. Synthetic instruments require a `synthetic:` identifier. Historical instruments cannot use that prefix. Classification of a bare caller-supplied list still relies on the caller; these controls do not authenticate a provider or prove that synthetic data are synthetic.

The registration manifest's `coverage_start` and `coverage_end` describe returned bars. Its `exposure_start` and `exposure_end` cover the full provider-requested interval when supplied, including dates for which no bars were returned. Otherwise the complete returned range is used. An exact synthetic schedule tests fixture coverage; it does not verify an exchange calendar. Merely providing an expected date list cannot admit historical data.

## Fixed windows and execution identities

A study request contains exactly `dataset_sha256`, `study_name`, `evaluation_start`, `evaluation_end`, and `specification`. The specification is the existing `StrategySpec` object: lookback, entry and exit thresholds, starting cash, and per-fill cost in basis points. Defaults are frozen into the recorded specification.

Every candidate evaluates exactly the requested inclusive dates. For a lookback of `L`, the runner selects exactly the `L` registered sessions immediately preceding the evaluation start, followed by the common evaluation window. It rejects missing boundaries or insufficient preceding sessions. Two lookbacks therefore share benchmark dates and benchmark accounting while using their own required warmup. A longer lookback cannot silently shorten the tested period. The strategy starts in cash, and the last warmup close can first affect an order at the evaluation window's first open. Warmup does not simulate an inherited portfolio.

Before computation, the runner registers a fingerprint of the normalized specification, verified dataset identities, assumptions, and code identity, then registers an attempt linked to its submission. The code identity includes current source-file hashes, including uncommitted contents, the available dependency lock hash, interpreter version, the actual engine entrypoint's bytecode, and loaded research helper functions and class methods, including normalized positional and keyword defaults. Unsupported function-default objects are refused. This distinguishes an old imported helper from a changed source file that has not been reloaded. Source and loaded-code identities are checked again after execution. These identities aid reproduction; they do not attest the complete machine, imported native libraries, mutable arbitrary process state, or a malicious owner.

A successful result is a content-addressed artifact containing the complete engine report and frozen specification/data/code identities. The artifact and its referenced dataset objects must be published and verified before success. The attempt and submission outcomes commit in one journal transaction. A publication error cannot leave a successful attempt paired with a failed submission. If an observed publication interruption can be recorded, the submission is `interrupted` and its attempt is failed with a fixed reason; if storage itself cannot accept an outcome, the call raises an error and work remains pending. Published but unclaimed artifacts may remain after a rollback.

Results say `exploratory_result`, preserve the engine's `unprotected_not_implemented` holdout status, and mark `investment_evidence: false`. There is no `DATA VALIDATED`, `NO EDGE`, profitability, or protected-final verdict. The existing engine's timing and accounting limitations remain attached to its report.

## Candidate counts, retries, and exposure

Study names are labels rather than candidate identities. Repeating the same normalized rules, dates, data, and code under a new name creates another execution of the same fingerprint. `recorded_candidate_count` counts distinct executed fingerprints for the declared instrument; `recorded_execution_count` counts registered executions, including unfinished or failed ones. Requests rejected before an execution is registered remain submissions rather than being falsely counted as executed candidates. Changed data or code create a distinct fingerprint. These are application counts, not estimates of every idea the owner has considered.

Registration and exploratory access append development exposure records. The entire registered/acquired range is `development_only`, with prior exposure `unknown_outside_application`. This includes warmup and any additional loaded or selected dates, not just the displayed evaluation interval. Exposure survives a failed run, a renamed study, a changed parameter, and revised data bytes. An optional parent manifest records a known revision relationship; overlap is still found without a supplied parent.

`list_exposures(root, market, start, end, limit=100)` returns inclusive date overlaps. Matching conservatively uses the case-insensitive declared instrument identity; changing venue, feed-related naming outside that identity, currency, or study name does not clear existing overlap. Original market metadata and dataset identities remain in each record. Alias resolution and stable issuer identity are not implemented, so changing the instrument identifier can obscure a relationship. No identifier or empty query establishes that an interval was unseen.

Exposure records are append-only application tables with events in the journal's hash chain. They are not OS isolation, access authorization, or immutable storage. Direct file reads outside this API, previous charts and model training, provider revisions, omitted acquisitions, and a database owner can escape these controls. The complete acquisition request is separately retained by the acquisition receipt; an interrupted registration before it can identify a valid dataset may have no explorer exposure row. That absence cannot be used to certify a final interval.

## Remaining admission and operation work

The first historical calculation requires explicit exchange-session coverage, applicable action accounting or supportable action-free eligibility, the relevant information-time assumptions, and permitted use. Calendar acquisition alone does not supply those controls. Comparing raw and adjusted prices can establish that no provider adjustment was observed in that comparison; it does not prove an absence of splits, dividends, revisions, or other corporate actions. Current data revisions and ticker identity cannot establish point-in-time or survivorship-free research.

Protected final evaluation needs a separate access boundary and independently reviewed exposure policy. This module does not implement either. Scheduled research, full research-role orchestration, independent reviews of actual strategy artifacts, performance statistics beyond the engine's current measures, and paper/live promotion are also separate unfinished requirements. This runner contains no network, scheduler, model call, credentials, or order placement.

Tests use temporary synthetic artifacts. They cover malformed-input retention, exact-byte corruption, common windows and warmup, daylight-saving normalization, changed/reloaded helper identity, source metadata conflict, historical refusal, retry versus candidate counts, full-range revision overlap, interruption, atomic publication failure, and ordinary append-only protections. Passing those tests supports software behavior only.

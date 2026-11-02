# D006 independent adversarial implementation review

Reviewer: `/root/d006_implementation_critic`. This review is separate from the producers, quality validation and scope review. Only this report was written by the reviewer. No credentials, existing runtime records, private source data, provider account, broker or paid-model endpoint was accessed. All executed fixtures used temporary directories and invented data.

Status: the reproduced implementation blockers and subsequent bounded cash-merger relevance refinement are independently checked at the hashes below. The follow-up section records the latest admission revision and supersedes that file's initial hash. No unresolved blocking implementation finding remains within this review's inspected scope. The code is suitable to proceed to the separately checked, already-authorized historical pilot; this report does not certify that pilot, the source judgments or the full operation.

## Reproduced findings

### C1 — Loaded admission/replay validation was absent from code identity

At admission source hash `f019c1168328ca2111ca20064987903dab57c9754528c64cd05f11567050ab78` and explorer hash `94988defafa780fb6ec9b8cac03d1701c9efcaef4bc00b4e1cd20e545c11165a`, `_code_identity()` included disk source hashes and loaded research/event-engine functions but omitted loaded admission and provider replay functions. A temporary fixture successfully admitted through the real synthetic transports. Replacing `admission._need` with a no-op left `_code_identity()` unchanged and the existing admission still validated. The numerical artifact can therefore identify current disk files while an older or replaced validation implementation remains loaded.

A related reproduction replaced `event_engine._target` first with an always-long lambda and then an always-cash lambda. The two behaviorally different loaded helpers produced equal code identities: `_loaded_engine_code` skipped functions attributed to another module and `_engine_globals` reduced non-Quanto functions to their binding type. This is a replay/provenance defect, not a claim that hashes isolate code from a privileged owner. Required correction: bind the actual loaded validation/replay helpers and policy globals, and fingerprint or reject imported/replaced function bindings rather than silently recording only their type.

The first correction exposed one further variant: `def target(flag): return lambda prices, spec, holding: flag` has the same bytecode for captured `True` and `False`. The final correction binds closure cell names/values, defaults, imported function bindings, loaded admission/provider helpers and policy globals; unsupported, empty and cyclic function closure state refuses identity. The reviewer reran the original `_need` replacement and confirmed `admission_dependencies_changed`; reran the two captured target values at the final explorer hash and confirmed different identities. This closes the reproduced identity defects. It does not attest every external library, arbitrary mutable interpreter state or a malicious filesystem/database owner.

### C2 — Relevant ISIN contradictions were silently accepted

At the same admission hash, `_actions` checked `cusip`, `old_cusip` and `new_cusip`, but ignored the documented `isin`, `old_isin` and `new_isin` fields. Starting from the explicit synthetic acquisition fixture, assigning `US0000000001` to the relevant split's `isin` and `US0000000002` to the relevant cash dividend's `isin` still returned `status=success`. Neither primary identity judgment reconciled that conflict.

The defect matters because known contradictory security identifiers cannot be treated as residual vendor omissions. Required correction: check ISIN continuity separately from CUSIP continuity, including old/new ISIN changes on a relevant reverse split, and refuse unresolved contradictions. No assertion was made that an arbitrary ISIN/CUSIP must be present in every supported provider record.

Correction verified: separate ISIN and CUSIP collections now inspect ordinary, old and new identifier fields. The original different-ISIN fixture returns `action_security_identifier_conflict`; the targeted suite also covers reverse-split old/new ISIN contradictions.

### C3 — Persistent publication failure lost the structured pending response

With valid temporary evidence, replacing `Provenance.finish` with an operation that consistently raises `ProvenanceError` made `admit_dataset` raise on its second terminal-publication attempt. The stored admission submission correctly remained pending. No false success or contradictory terminal record was observed.

The operational defect is narrower: the API did not return its submission ID and pending status, and the CLI could display a raw exception instead of its fixed safe result. SQLite errors could escape the CLI handler. The same error-publication pattern exists in the explorer path. Required correction: guard failure-outcome publication and return a fixed pending result when publication remains unavailable. An interrupted submission is not permission to retry acquisition automatically.

Correction verified: admission and explorer guard error-outcome publication. The independent persistent-`ProvenanceError` fixture now returns the same submission ID, `status=pending` and `error_code=publication_interrupted`, without the injected private exception text; the stored submission remains pending. The targeted suite covers persistent SQLite/OSError failures and verifies that explorer cannot leave a successful attempt behind after terminal-event failure.

## Independent checks executed

An independent exact-`Fraction` reference accountant generated 100 deterministic random price paths. Each path used a 3-session SMA, 10,000 initial cash, a 3:2 split, an ordinary USD dividend, and a later payable session. Both strategy and benchmark marks were checked against the event engine: 1,800 equity comparisons passed within an absolute `1e-24` tolerance for the specified Decimal arithmetic. The reference independently modeled entitlement before trading, fixed nominal claims, split-adjusted shares/history, cash-retaining benchmark, and end-of-pay-date release. This check used zero fees; fee and boundary cases require the broader targeted tests and quality review.

A separate prefix-invariance check used 25 deterministic random paths under each 0/10/25 bps scenario. Appending future bars and a future split preserved every earlier daily mark, signal and trade for both portfolios: 150 portfolio-path comparisons passed. These checks were independently constructed in temporary Python invocations, not assertions copied from the producer tests.

The integrated targeted command `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_alpaca_actions.py tests/test_alpaca_data.py tests/test_event_engine.py tests/test_admission.py tests/test_explorer.py tests/test_cli_requests.py` passed 338 tests after the initial corrections. After the final closure-identity edit, the reviewer re-read the changed code and tests, reran the independent closure counterexample, and ran `tests/test_admission.py tests/test_explorer.py`: all 118 tests passed. The final identity change did not modify acquisition or accounting. Separate full-suite, lint and clean-install conclusions belong to quality validation, not this report.

The reviewer also inspected the exact route allowlist, bounded all-category acquisition, Decimal action normalization, occurrence retention, explicit terminal pagination, safe response retention, receipt publication, source replay, event conflict handling, full-acquired-interval exposure, next-open execution, warmup isolation, terminal marks, loaded numerical context and CLI routing. These observations establish implementation properties under the stated threat model, not issuer-source truth, account entitlement, exhaustive vendor coverage, point-in-time history or investment performance.

## Initial inspected identities and correction checks

Final review used branch `feat/historical-admission`, base HEAD `c4ff21882dab1885e9707ab5a60b42dc436bb5a7`, plus the uncommitted implementation identified below. Producer freeze was confirmed before the final reinspection. SHA-256 identifies the exact working-tree bytes; the base commit alone does not contain this implementation.

| Artifact | Final inspected SHA-256 |
| --- | --- |
| `src/quanto/alpaca_actions.py` | `f6804b8717a3dd60ff77fcf934581170b762cf82f77b5dd229c349c127205cc7` |
| `src/quanto/alpaca_data.py` | `9182307746567e349ed1b936eb35949fac7684430336279968f02d6f35ab0c76` |
| `src/quanto/event_engine.py` | `cb1a61985ebb08089eab50d00d1e78f09a83fdea6754587af7e871e177175ffc` |
| `src/quanto/admission.py` | `7adda60cfc5b47a7b66f473fc661afd5dc9f3a8ff5723d8f6ce1ad2e5392d42c` |
| `src/quanto/explorer.py` | `58d3e5508cc967210ebe41fb0b07200d32090652534fb87df5749647c9f81ddd` |
| `src/quanto/cli.py` | `b19c8927d5152a308540a3d9e3ce5e8ac70516bd91ba41d3cba776b49b1830e1` |
| `src/quanto/research.py` | `186e6a9aa95a484e94d71cbd71f276c053b923e96e030fa6eea0adcfc53223ca` |
| `src/quanto/provenance.py` | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |
| `src/quanto/ledger.py` | `29c3f14bdae924b4d369b49b59c3ec7e5079810d76e55992fa1800d49a3da6cf` |
| `tests/test_alpaca_actions.py` | `054e7bbe2f8a8502446636b46eb629908927e3f5079cb231d3a3c0bcf4341906` |
| `tests/test_alpaca_data.py` | `909a7655cab13b05f88fddcb581d93ee012b7ca5765429c9c2d2f8b002bdb6f0` |
| `tests/test_event_engine.py` | `e096e4e919b63476fd90fa0d2433d4d739a9bfc671517547fce3077f69dd1a53` |
| `tests/test_admission.py` | `9a814d4727aa29e883fac263eaaf8218c8e4486fa0418b1a7234390db2eea8bf` |
| `tests/test_explorer.py` | `f2355a8629303fcd43bf1cc3ae24edc9db82b49990eefb8775eff8b0324cdc15` |
| `tests/test_cli_requests.py` | `4ff710514aed1bd4e50286521a90b21cfb1a29f152b56e8a9e480b749b9d6f30` |
| `docs/ACCOUNTING.md` | `3a45f81bbf05af25f207431a67bff890a9f6bbb96998ae034dae00e0097777cc` |
| `docs/ACTION_SOURCES.md` | `6b3d81ede600e53c66d7032aa4e1b2747980496c7ec63d18793abe56e233667e` |

No conclusion here closes the protected-evaluation, operational five-role research, searchable failure memory, durable scheduling/restore, prospective paper or separately approved execution requirements.

## Follow-up: bounded acquirer-only historical cash-merger exclusion

The lead subsequently reported that a complete action acquisition contains old cash-merger records in which the queried issuer is the acquirer, while the acquiree is another security. This observation is lead-reported; the reviewer has not inspected the private records or runtime. The lead reports preserving the initial refused admission and performing no historical calculation before resolving the issue.

The blanket rejection of every `IDENTITY_EVENTS` record precedes structured relevance in the inspected implementation. That is more restrictive than D006's accepted rule to refuse when structured evidence cannot exclude relevance. A narrowly documented exclusion for a completed cash acquisition before the full acquired interval is consistent with that rule; it does not add merger accounting. The [pinned official REST schema](https://raw.githubusercontent.com/alpacahq/cli/709d11400129dc7c09b41dd05263187e15801a71/api/specs/market-data-api.json), `cash_merger` at lines 1783–1843, supplies an `effective_date` and distinct acquiree/acquirer identity fields rather than an `ex_date`.

Required adversarial boundaries communicated before implementation:

- Restrict the exception to `cash_mergers` whose effective date is strictly before the full acquired interval. Do not use the narrower evaluation start or substitute process/payable dates for effectiveness.
- Require an explicit queried-acquirer role, a different identified acquiree, and an attributed source judgment supporting issuer continuity and no conversion of the studied shares. Reconcile available acquirer CUSIP/ISIN fields with the studied issuer; do not compare the acquiree's identifiers as if they represented the issuer.
- Bind each exclusion judgment to the exact provider ID, category, normalized record hash, date and roles. Retain the excluded record and source occurrences, reviewer attribution, source bytes and reason in admission. A Boolean approval is insufficient.
- Detect same-ID conflicts before exclusion. Reject ambiguous roles, crossed or identical security identities, missing/invalid dates, on-start/in-window/future events, queried-acquiree cases, stock/mixed mergers and other unsupported identity events.
- For the narrow completed-before-window case, any recorded payable date must be valid and earlier than the full acquired start. Missing payment information requires explicit source-supported completion, not an assumed payment.
- Preserve the failed admission, version the refinement and require fresh admission. Source corruption/tombstones, changed excluded records, altered judgments and loaded-policy drift must invalidate reuse.

Follow-up implementation reinspection is complete. The refinement implements `D006-admission-v1.1` and `completed_acquirer_only_source_bound_v1`. It performs corpus-wide same-ID conflict detection before exclusion, retains every exact-duplicate source occurrence, rejects multiple provider IDs for the same acquisition participants/effective date, and binds attributed judgments to source-document hashes rather than arbitrary receipt references. Acquiree CUSIP is required; optional ISIN is not fabricated. An acquirer identifier must reconcile with the relevant studied-event corpus, every supplied acquirer identifier must agree, and an acquiree identifier cannot collide with that corpus. The conservative limitation is explicit: a pre-window merger cannot be excluded through this path when the studied-event corpus lacks the required identity comparison.

The reviewer constructed a new cash-merger fixture on the synthetic acquisition pipeline and independently changed fourteen conditions: effective date on acquired start; effective date within acquired warmup but before evaluation; queried-acquiree role; acquiree identifier collision; missing acquiree identity; unmatched acquirer ISIN; in-window payable date; an unsupported share leg; malformed currency; changed record hash; unbound completion source; in-window completion; duplicate judgments; and a stock-merger category. All fourteen attempts returned invalid. These mutations were constructed independently rather than invoking the producer's merger test cases.

A positive case with two exact source occurrences admitted one retained exclusion while preserving both occurrence references and the two original split/dividend accounting events. Tombstoning the completion source then refused the historical study before calculation. In another check, replacing the loaded `_excluded_cash_merger` helper with a wrapper left the disk unchanged but changed code identity; reuse of the prior admission refused with `admission_dependencies_changed`. The final `tests/test_admission.py tests/test_explorer.py` run passed all 182 tests.

No unresolved blocking implementation finding remains for this bounded refinement. This conclusion does not authenticate the lead's actual exclusion judgments, establish exhaustive event coverage, or certify the historical calculation. Actual artifacts and the preserved first refusal require their separate local evidence review.

| Follow-up artifact | Final inspected SHA-256 |
| --- | --- |
| `src/quanto/admission.py` | `7cd34c3244b7f87496827f933606e4000d52f4408438304ef14f27d1434cd953` |
| `src/quanto/explorer.py` (unchanged) | `58d3e5508cc967210ebe41fb0b07200d32090652534fb87df5749647c9f81ddd` |
| `tests/test_admission.py` | `e2111f2d8e84adc088e44666a7cc512e04cd12c0bf2fabba7b518b5dcf1312fb` |
| `tests/test_explorer.py` (unchanged) | `f2355a8629303fcd43bf1cc3ae24edc9db82b49990eefb8775eff8b0324cdc15` |
| `docs/RESEARCH_PROTOCOL.md` | `a0ab1a620f92fe08da39004b78bf85d2a5b1bf8327117a08990a9c47ec6a924c` |

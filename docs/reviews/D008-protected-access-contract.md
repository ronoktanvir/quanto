# D008: reservation and access authority implementation contract

**All ordinary content reads and provider dispatches require an explicitly installed supervisor session.** The session binds one canonical development root, one private control database and one persistent principal. Calling an ordinary API with a different root does not issue new authority. The trusted CLI establishes the session for its selected workspace; fixtures establish explicit synthetic sessions. No evaluator acquisition or final protected eligibility is provided by this increment.

This contract implements the accepted D008 policy and the seven clarifications in the separate protected-evaluation contract scope review. Producer: `/root/protected_access_builder`. This is an implementation specification, not independent review or actual protected operation. No actual project store, provider, model, credential or protected observation is used during development.

## Authority and persistence

The trusted supervisor opens the control database before handing an `AccessSession` to ordinary services. Control records live separately from `research.sqlite`, so a later research transaction rollback cannot erase access authorization or consumption. Each control operation owns a short SQLite transaction; none remains open across a provider request or file read. File ownership, private modes, symlinks, regular-file properties, pinned root inode/device and control-store identity are checked. An already active process cannot silently switch workspace or principal.

Principal identities persist in the control store and survive session restarts. A supervisor-issued principal relation and security-alias relation are append-only revisions. Intents bind the revision under which they were issued; effect authorization checks the current revision atomically. Changed relations fence stale intents and invalidate conflicting provisional reservations rather than resetting their histories. Models and ordinary callers do not issue principals, aliases or sessions.

The supervisor API is a trusted application boundary, not protection from code that can invoke administrative constructors, replace Python objects or edit files as the owner. A CLI invocation deliberately selecting another independently controlled workspace does not prove absence of exposure there. Global deployment binding and outside-process observation remain requirements before real protected eligibility; this increment never grants that eligibility.

## State and effects

An access attempt records `issued` or a bounded refusal. An issued intent pins principal, coverage, operation, request identity and identity revision. It blocks overlapping reservation creation immediately, before any page or file opens. Each exact effect is consumed once in a committed `started` record before I/O. The effect identifies the full page request or content digest; replaying its entitlement refuses. A terminal observation records `completed` or `uncertain`; absent terminal evidence also means uncertain access.

An intent may be rejected without consumption only through a local transition that verifies no effect-start exists. A generic failure/cancellation never erases its conflict. Once an effect starts, a crash, timeout, malformed response or failed publication preserves exposure; no empty response or missing object restores an untouched interval. Audit-storage failure denies I/O. Repeated actual content opens create distinct access attempts, while repeated use of one issued effect is refused.

Provisional reservations freeze acquisition/warmup/final coverage, candidate/code/dependency/scenario identities, rights and disclosure-contract identities, and persistent selector/reviewer principals. Reservation creation and access intent issue use the same control-store transaction boundary, so only the compatible side of an overlap race can proceed. Reservation records remain preparation-only; there is no protected execution or activation method.

## Coverage and legacy state

Coverage profiles distinguish daily bars, global calendar observations, action process-date queries and unknown content. Bars resolve through supervisor-issued economic-security aliases and use the whole requested date envelope. Calendar coverage is global for its dates. Action process dates never substitute for economic dates: their coverage remains unknown over time for the resolved security, or global when security identity is unresolved. Feed, adjustment, byte revision or renamed ticker does not reset an economic-security interval.

Object reads use a prior supervisor-owned classification by exact digest. Unclassified bytes receive unknown coverage before opening them; the reader cannot inspect bytes to decide whether that same read was permitted. A caller's dataset metadata, `access_class`, root argument or self-declared synthetic tag cannot narrow that coverage. Unknown coverage conflicts conservatively with reservations. Known older observations do not conflict with a genuinely later known interval.

Existing workspace history is not silently reconciled. Bootstrap records whether the controlled research/object stores were absent at the boundary; any existing store leaves a legacy-unknown marker that prevents reservation eligibility. This version has no operator boolean that clears that marker. A later reviewed reconciliation tool must cover prior requests, pages, imports, outcomes, pending effects and alias history with bound evidence. Generic writes and new unknown reads remain conservative observations, never evidence that an interval is clean.

## Mandatory routes and disclosure

`Provenance` content-open paths require the bound session and commit a content effect before opening bytes, including direct reads and deduplication reads. The bounded cache below can reuse already verified bytes without another content open. Dataset registration inherits this mandatory lower-level guard; metadata parsing happens only afterward. Bars/calendar/actions register normalized acquisition intents before dispatch. The lower dispatch layer requires an issued effect; both injected and real transport paths consume it before I/O, and pagination uses a distinct exact URL/page effect. The raw transport entrypoint also requires consumed supervisor authority; an unguarded direct call refuses.

Private control rows and manifests do not enter ordinary research events, model packets, dashboard state, conversations or failure-memory messages. Ordinary failures use fixed public categories; details and protected identities remain control-private. This is not the future evaluator's release service: protected bytes and data-dependent evaluation results are unavailable, so no release timing or numerical acceptance is claimed.

Administrative capture/restore readers, direct SQLite/file access, future evaluator roots and all cross-process control entrypoints still need their separate evaluated route inventory before protected activation. Existing D009 tests remain frozen during its diagnostic and will require explicit fixture-session adaptation later. Their historical passes are not reinterpreted as passes against this new access boundary.

## Verification and remaining work

Producer checks will cover reservation/access races in both orders, stale relation revisions, one-use page/file effects, conservative uncertainty, no-start rejection, crash/restart retention, stable principals, alias merges, unknown legacy/coverage, wrong roots and refused I/O. Fake transports and invented temporary content supply test evidence. Separate criticism, quality and scope must inspect exact final source/tests before integration.

Required later work remains real legacy reconciliation, complete evaluator storage/service isolation, controlled protected acquisition and private source review, fixed outcome-independent release, independently reviewed statistical planning, protected pilot evidence, external checkpoint/effect/freshness barriers, sustained operation and prospective paper execution. This increment completes neither R13 nor R14 and changes no financial model or trading authority.

## Producer implementation observations (not independent acceptance)

The first 21-test registry run passed 20 cases and failed one reporting assertion: an acquisition correctly refused before transport, but its ordinary failure-receipt publication also refused an unclassified content read and masked the access reason as storage failure. The first correction preserved the original access-refused category with pending publication. The later, retained implementation moved the control decision before ordinary query registration: a denied query now publishes only a constant marker and fixed refusal, with no request or receipt artifact. No request was emitted in the failed test. This failure is preserved rather than relabeled as an initial pass.

Repeated content opens require distinct intents and effects; a completed effect can be queried but cannot reopen bytes. Provider permits bind exact GET method and URL, including pagination token, to a retained normalized request. GET has no body. Both injected dispatch and the raw HTTP helper enforce the consumed permit; synthetic sessions refuse raw network. Separate control commits survive research SQL rollback, but copied or overwritten authentic control history is not externally anchored freshness. These controls do not establish malicious-owner antirollback protection.

The first existing-route integration run passed 257 tests and failed two checks. One fixture assumed no runtime directory existed before the supervisor bootstrap; it now tolerates the explicitly created control directory. The calendar page permit exposed a real canonicalization defect: reloading its sorted private request changed query-key order, so the exact URL check rejected an otherwise valid request. Calendar URL construction now fixes start/end order explicitly. A separate exploratory diagnostic initially rejected a temporary path containing a macOS symlink ancestor; the diagnostic used its resolved temporary path on the next distinct run, without weakening product path checks.

The first high-level compatibility run was deliberately interrupted after 755.93 seconds: 285 tests had passed, with no observed failed test, but this subset alone exceeded the repository's 10-minute CI bound. It is an interrupted partial run, not a complete pass. Its owned process remained live and CPU-active; the stop was not caused by a branch change or observation timeout. One active fixture had 7,792 content intents/effects and 23,387 audit events. A one-second native sample showed repeated SQLite setup and file metadata work alongside durable commits. A tiny 100-read comparison found WAL slower than unchanged DELETE mode (0.427 versus 0.284 seconds), so journal mode and durability were not reduced. A separate reused-connection prototype measured 0.140 versus 0.271 seconds; that probe alone was not treated as production throughput evidence.

The implementation now reuses a distinct connection per active supervisor-session thread, with short transaction scopes, per-connection synchronization, explicit FULL synchronous mode and closure when the session ends. Every effect start and outcome still commits before advancing; no transaction spans I/O and no entitlement checks or audit records were dropped. Targeted race, restart, failure and representative high-level checks must validate this optimization before a new full compatibility claim. The initial fixture-import insertion also produced Ruff E402 errors; its marker was moved after imports without widening fixture authority.

The control database is `runtime/access-control/control.sqlite`. The existing D009 research-only candidate predates and excludes it. A future recovery must restore its principals, relations, reservations, access intents and uncertain effects consistently, or refuse protected eligibility through conservative reconciliation. Restoring research.sqlite alone cannot establish a clean authority history. No actual production bootstrap or migration has occurred in this task.

## Approved same-session byte reuse

Connection reuse alone did not resolve high-level cost: two representative broker cases passed in 123.35 seconds (80.63 and 27.97 seconds for their calls). The lead approved a narrower per-Provenance-instance byte cache, subject to independent review. Cache entries hold only immutable bytes already opened and hash-verified under the same live session/principal, with a 32 MiB / 256-object bound. Parsed JSON is rebuilt on each call and cannot mutate cached bytes.

Each hit checks live installed authority, the current principal/alias/policy revision, root/control-store identity, current tombstone state, research-journal identity, object-directory identity and file type/link count/ownership/mode/device/inode/size/mtime/ctime. Changed or uncertain evidence invalidates/refuses before reuse; an actual new open requires a fresh durable effect. No cache crosses instances or sessions, and old exposure/uncertainty history remains. This is reuse of previously verified bytes under cooperating-writer metadata assumptions, not fresh hostile-owner integrity verification or recycled access authority. Source identities now include the access-registry module. No broad preauthorization or reduced persistence was adopted.

The final cache contract also includes persistent principal revocation and read-only session identity properties. Revocation fences new effects and cached reuse; alias/principal revisions invalidate conflicting preparation reservations. Producer tests specifically inject revision and tombstone changes during cache validation, inspect actual content-open/effect counts, and verify that parsed JSON mutation cannot alter cached bytes. These are cooperating-application tests, not a claim of hostile Python-process or filesystem isolation.

## Frozen producer candidate and self-review corrections

Coverage is derived inside the intent transaction from its frozen normalized provider request or the prior trusted classification of its exact content digest. Ordinary `issue` callers cannot supply coverage. Self-review found and removed that draft parameter because it could otherwise narrow the direct-helper route. A reservation also refuses a security identifier without a trusted relation. A late relation change cannot relabel the frozen intent as current.

The lower content and HTTP helpers require the exact live grant registered by the session after durable effect-start. Self-review found that the draft raw helpers accepted a duck-typed object with a `consume` method. The retained implementation rejects fabricated and copied grants, binds operation/identity/revision in the supervisor's registered tuple, and atomically removes the one-use grant on consumption. Resetting a local used flag or changing a grant's displayed identity cannot restore its authority. Exact-page rejection, raw-grant rejection, wrong-root rejection and revoked-principal attempts leave bounded private refusal events when a valid installed control journal is available. Missing or unsafe authority still refuses I/O, but cannot certify a durable rejected-without-access outcome through a nonexistent or untrusted journal.

Existing control files are opened read-only to validate their store/root binding before any writable connection or schema operation. An empty or partial existing file is not initialized as a new authority, and a copied wrong-root file is not repaired while refusing it. Sessions have one lifetime; a closed session cannot be reentered, and a repeated exit cannot close another session's connection pool. A fresh content read rechecks tombstones before returning bytes, including a tombstone introduced during the read. These corrections received direct regression coverage before the source freeze.

The following outcomes are producer evidence only. Terminal handles identify the retained tool transcript; they are not live processes or independent acceptance. No full-suite pass is claimed after this hardening.

| Attempt | Terminal result | Evidence handle |
| --- | --- | --- |
| Initial high-level compatibility, before connection/byte reuse | Deliberately interrupted; 285 passed in 755.93 seconds; exit 2 | `68413` |
| Two representative cases after connection reuse only | 2 passed in 123.35 seconds | `62917` |
| Same pair after byte reuse | 2 passed in 24.85 seconds | `58122` |
| Seventeen relevant modules before final hardening | 1,089 passed in 509.08 seconds; exit 0 | `59917` |
| Bootstrap, identity and revocation hardening | 230 passed in 7.85 seconds | `35345` |
| Exact registered-grant and concurrency regressions | 232 passed in 7.77 seconds | `67939` |
| Grant-copy/field checks plus representative pair | 235 passed in 35.85 seconds | `94452` |
| Private route-refusal audit plus representative pair | 236 passed in 31.04 seconds | `87643` |
| Final one-lifetime session candidate | 237 passed in 31.29 seconds; exit 0 | `17091` |

The final command selected `test_evaluation_registry`, `test_provenance`, `test_alpaca_data`, `test_alpaca_actions`, `test_cli_requests`, and two broker nodes: `test_historical_relations_are_qualified_without_changing_refusals` and `test_unused_proof_prepared_before_assignment_is_refused`. Their calls took 15.70 and 4.64 seconds respectively. Ruff passed across all 24 owned source/test paths at this freeze. Earlier fixture/lint failures, the misdirected test selection that ran no tests, and the slower/interrupted attempts remain historical observations; their results are not attributed to this final source.

Independent criticism, quality execution and scope acceptance remain pending. Recovery/closure source/tests remain unchanged and pinned for D009 work; their explicit session-fixture adaptation is still required before the full compatibility suite. Other direct/runtime administrative routes, global deployment identity, old processes, legacy reconciliation and the actual evaluator/release boundary remain incomplete. Quality must measure the full required suite before any CI-timeout decision; no route or durable commit may be omitted to fit the earlier ten-minute setting. There was no production bootstrap, actual market/model call, financial replay, provider request, credential access, upload, Git staging or commit by this producer.

The new `runtime/access-control/control.sqlite` is a separate recovery dependency. The current D009 materialized research candidate does not contain it. Future operational recovery must preserve its identities, reservations, intents and uncertain effects with research state, or conservatively refuse protected eligibility; a restored research database alone cannot authorize a clean access history.

## Frozen changed source and fixture identities

The following manifest covers this producer's 24 source/test files only. The contract's own digest is supplied separately to the lead after this table is written. Other unstaged D009/context/reviewer files are not part of this candidate.

| Path | SHA-256 |
| --- | --- |
| `src/quanto/alpaca_actions.py` | `bb3106dc40da289566df55200fd870248fc70c2f71417db6a9aa4563a95c58a4` |
| `src/quanto/alpaca_data.py` | `b115e822677761b7ae4177ca4135a5c28c359b48ce42d5aa0f11841dd6ecb9ff` |
| `src/quanto/cli.py` | `69b4301ab74530659d5433967512bbf3cbaf423f9c96d8f6e1fd2c91a4c6f02d` |
| `src/quanto/evaluation_registry.py` | `4815144aecac18b18dbd69c858046b4d700debf1abf6138cf417c7bd24789cee` |
| `src/quanto/explorer.py` | `5bf8768505b02691aba5c321d70c8f62dddac3e4bbd5be31c983f2f43a23832a` |
| `src/quanto/provenance.py` | `ceba0b408788d099e7bcac53037ada81c4be93305249488e8357590e2319e2f7` |
| `tests/access_fixtures.py` | `72410d741a0676a079306532e93668545b6a284a52b75de6060b8e9c1d99be92` |
| `tests/test_admission.py` | `5268c7debe91494126606937a6f477f0f2f9e4674a8c2360c7a3c31d5b3e2995` |
| `tests/test_alpaca_actions.py` | `21b39a8008c0a6b71df64ff679d5baa3015abdc5631846bf32b0562702f9edbe` |
| `tests/test_alpaca_data.py` | `c91d22c6333f57bb79883c4c82b403c1d926830ab492f346bae9a66e12ff486f` |
| `tests/test_cli_requests.py` | `ac5ac928ff7a3c8f500646ea54209f21289650fa5c09e09ea060b7584ec18ab1` |
| `tests/test_evaluation_registry.py` | `ee77c35b6ed4cd3916e688086135d2be99367c901b6674e2c475f726a4c9e19b` |
| `tests/test_explorer.py` | `a0b50c807aa224e4d64e50f831b44ab4f13031179a7a3a3d64e2a409d3a79c98` |
| `tests/test_explorer_suite.py` | `81fa78f8dddcc05ba4b0b77a3b6e8f89723e3e0a46dfba3df56745407284e97a` |
| `tests/test_failure_memory.py` | `1281725db3853e26aa9a26476da9727613000691941d6a565e91bb7b95f50437` |
| `tests/test_policy_revision.py` | `cd9a303628c1b0ce02d34c2c32cf31015ea68a57cf79c0a8bd616643eb5f66b2` |
| `tests/test_provenance.py` | `4e5866c4c5bb491a992939f9bdc4e6c5c65b314e435fdeefe1c33c2ab5324ee0` |
| `tests/test_research_broker.py` | `6c4e6c2c7e8f9b5c95f6b6baef4e1ac17e09848dfd10501c39a7a575f756006f` |
| `tests/test_research_comparison.py` | `8fa13d6b41dd37993331a0e18a1fcd01eeb4fe00077f80df7c3710f177a979a3` |
| `tests/test_research_dispatch.py` | `5834db43c5ecf56c6baacf4d5c7c950839f150881215e04ebc6145fbdebfd52e` |
| `tests/test_research_failure_context.py` | `37c767f52aeb04f46ed3d506266632a035ef08bae4e41e994d9d7f489d8ae41d` |
| `tests/test_research_packets.py` | `f11eca0d6cb1e748a80320aff5ab190319fa48c4bccb7b1541dfd9a451ee943a` |
| `tests/test_research_workflow.py` | `34dbea72f7a3512cefe9ef2b95eaa474f07c1476cee953b08f13655b3432f1c9` |
| `tests/test_study_suite.py` | `f6a51f377b4c31a61d8a663bbfe516ceeefd4a949d6557a0f25cb48c51d16ce6` |


## Corrected producer candidate v2

The earlier 24-file table is the rejected v1 candidate. Independent criticism reproduced C1 arbitrary intent classification, C2 action coverage mismatch, C3 unrecorded generic imports and C4 disjoint acquisition receipt refusal. Its report and original frozen source remain preserved. The original temporary producer directory is no longer present at this resumed inspection; all 24 original identities were instead reverified against the retained `runtime/protected-access-critic/frozen-v1/` export and manifest `3b9fbb9c95c5718727fe8928f5e84f9ad5b56f6c0abc1d3848f0786507baf22a`. Do not describe the absent temporary directory as currently retained.

The corrected producer is `/root/access_v2_finish`, continuing the prior builder's implementation. Ordinary intent `bind_object` now refuses. A separate administrative supervisor method issues an adapter-bound producer capability; it is part of the explicitly trusted supervisor boundary, never a worker/model capability. Exact one-use publication permits bind the active session/principal, current identity revision, adapter source, artifact role, bytes and consumed origin effects. Prepared request bytes are reconstructed; response bytes must match actual dispatched results; normalized content is recomputed from those responses; final receipts require typed metadata and completed publication/effect lineage. No arbitrary intent or caller-supplied coverage can certify content origin.

Generic bytes passed to ordinary publication are already observations. They create a durable `content_import` intent plus completed effect, conservatively invalidate conflicting reservations and remain consumed even if publication refuses, the research transaction rolls back or the principal was revoked. A bogus/stale producer permit cannot erase those supplied bytes. A correctly bound producer receipt instead carries its actual lineage, so valid disjoint bars, actions and calendar acquisitions can complete and retain their verification reads.

Response coverage is checked beneath both dispatch and the raw HTTP helper, independently of whether a publisher exists. Foreign-symbol, malformed, unresolved, multi-party or unsupported extra-field responses widen the intent to unknown before publication. Action process dates never become economic dates. Only a finite simple action profile can retain the requested security scope; other action forms remain inspectable in ordinary development without reservations but cannot receive narrowly classified authority. This is conservative access accounting, not new action admission or financial semantics. Transport error, partial response and exception preserve unknown coverage; subsequent effects recheck current widened coverage before further I/O. The raw-helper test replaces the TLS constructor before creating its temporary non-synthetic authority; it performs no network request.

The prior v2 development run reported 214 passes and nine failures: seven old import-count/fixture assumptions plus two parser/instrumentation assumptions. Its subsequent 236-pass result remains historical. During resumption, an incorrectly class-qualified broker-node command ran zero tests and exited 4. After correcting selection, 253 tests passed in 33.52 seconds. Transport failure/current-coverage corrections then passed 257 tests in 32.71 seconds; a new disjoint-calendar positive case separately passed in 0.13 seconds. A final source change conservatively widens unsupported provider extra fields. The final exact candidate below passed **261 tests in 32.45 seconds** (terminal handle `33854`) across registry, provenance, bars, actions, CLI and two representative broker nodes. Ruff passed across all 24 owned paths. These are producer checks, not independent criticism, clean-install execution or full-suite acceptance.

The final producer test command selected `tests/test_evaluation_registry.py tests/test_provenance.py tests/test_alpaca_data.py tests/test_alpaca_actions.py tests/test_cli_requests.py tests/test_research_broker.py::test_historical_relations_are_qualified_without_changing_refusals tests/test_research_broker.py::test_unused_proof_prepared_before_assignment_is_refused`. Earlier terminal evidence remains distinct: 82506 (253), 81996 (257), and 770396 (single calendar test plus Ruff). No D009 source/test, Git, context file, actual store, credential, provider/model call, bootstrap, protected campaign, financial replay or external transfer was changed or executed by this resumed producer.

Independent criticism must retest the four original findings and the administrative publication boundary on these exact bytes. Independent quality and scope remain required. D009 fixture sessions, full-suite/runtime rollout, legacy reconciliation, evaluator isolation/release and consistent multi-store recovery remain incomplete; this candidate grants no actual protected eligibility and completes neither R13 nor R14.

| Corrected path | SHA-256 |
| --- | --- |
| `src/quanto/alpaca_actions.py` | `7383bd169d55d4500f8a7ee756b7d80057e6842a7c6f8a18d136155f673d0453` |
| `src/quanto/alpaca_data.py` | `4cc3f6d40b2d050483c5be898b606f8373792484be4cbb0a12b8eb80fb14da16` |
| `src/quanto/cli.py` | `69b4301ab74530659d5433967512bbf3cbaf423f9c96d8f6e1fd2c91a4c6f02d` |
| `src/quanto/evaluation_registry.py` | `c75c224f60d5b922592ffd4367bff90f97b8a50ae4dfa16fd08cf204da2ade11` |
| `src/quanto/explorer.py` | `5bf8768505b02691aba5c321d70c8f62dddac3e4bbd5be31c983f2f43a23832a` |
| `src/quanto/provenance.py` | `e4dd618f573e27cf3a1f9dbd9ee422f5f21b13f514e73218059210f85187c55b` |
| `tests/access_fixtures.py` | `72410d741a0676a079306532e93668545b6a284a52b75de6060b8e9c1d99be92` |
| `tests/test_admission.py` | `5268c7debe91494126606937a6f477f0f2f9e4674a8c2360c7a3c31d5b3e2995` |
| `tests/test_alpaca_actions.py` | `8cb19323fab03697050aac50d9b1d0a066a76bdefd1f26866715f7b84423fc2c` |
| `tests/test_alpaca_data.py` | `c91d22c6333f57bb79883c4c82b403c1d926830ab492f346bae9a66e12ff486f` |
| `tests/test_cli_requests.py` | `ac5ac928ff7a3c8f500646ea54209f21289650fa5c09e09ea060b7584ec18ab1` |
| `tests/test_evaluation_registry.py` | `04659ea87204b07e324f3366b989ecf6231ea32d67b9be641a1d198c0b4b9e00` |
| `tests/test_explorer.py` | `a0b50c807aa224e4d64e50f831b44ab4f13031179a7a3a3d64e2a409d3a79c98` |
| `tests/test_explorer_suite.py` | `81fa78f8dddcc05ba4b0b77a3b6e8f89723e3e0a46dfba3df56745407284e97a` |
| `tests/test_failure_memory.py` | `1281725db3853e26aa9a26476da9727613000691941d6a565e91bb7b95f50437` |
| `tests/test_policy_revision.py` | `cd9a303628c1b0ce02d34c2c32cf31015ea68a57cf79c0a8bd616643eb5f66b2` |
| `tests/test_provenance.py` | `4e5866c4c5bb491a992939f9bdc4e6c5c65b314e435fdeefe1c33c2ab5324ee0` |
| `tests/test_research_broker.py` | `6c4e6c2c7e8f9b5c95f6b6baef4e1ac17e09848dfd10501c39a7a575f756006f` |
| `tests/test_research_comparison.py` | `8fa13d6b41dd37993331a0e18a1fcd01eeb4fe00077f80df7c3710f177a979a3` |
| `tests/test_research_dispatch.py` | `5834db43c5ecf56c6baacf4d5c7c950839f150881215e04ebc6145fbdebfd52e` |
| `tests/test_research_failure_context.py` | `37c767f52aeb04f46ed3d506266632a035ef08bae4e41e994d9d7f489d8ae41d` |
| `tests/test_research_packets.py` | `f11eca0d6cb1e748a80320aff5ab190319fa48c4bccb7b1541dfd9a451ee943a` |
| `tests/test_research_workflow.py` | `34dbea72f7a3512cefe9ef2b95eaa474f07c1476cee953b08f13655b3432f1c9` |
| `tests/test_study_suite.py` | `f6a51f377b4c31a61d8a663bbfe516ceeefd4a949d6557a0f25cb48c51d16ce6` |


## Corrected producer candidate v3

Independent v2 criticism verified corrections to C1–C4, then reproduced C5 malformed pagination metadata retaining narrow coverage, C6 oversized/invalid generic inputs escaping import accounting, and C7 a publication permit surviving its intent's terminal rejection. The exact independent report is `D008-protected-access-v2-critic.md`, SHA `52027446f37716317114a245f128ff92f21c180c7b4a4ac9681358e777aff092`. Both its original and supplemental probe scripts/outputs remain unchanged. All 24 frozen v2 source/test bytes were reverified under `runtime/protected-access-producer-v2/`; that candidate is preserved and not accepted.

V3 validates nullable pagination-token type and the existing bounded token grammar inside mandatory response coverage checks, before raw response publication. Bars/actions malformed object, list, boolean, numeric, empty, invalid-character and oversized token values widen to unknown. Direct dispatch and raw HTTP use this same check even without a publisher. Later repetition and pagination completeness checks remain. Synthetic raw-HTTP cases replace the TLS constructor before creating temporary authority and exercise both bars/actions, valid null/string tokens, malformed tokens, foreign records, HTTP failure and partial response interruption; they make no network connection.

Ordinary import validity no longer determines whether supplied content counts as an observation. Unbounded/non-byte inputs create a constant-sized unknown import record without hashing or retaining their payload. The private record explicitly marks its identity as `attempt_only`, not a content digest. Ordinary `put_json` records an unknown observation before serialization, including NaN, oversized and cyclic input or serializer interruption. A successful ordinary JSON import consequently records both that supplied-object observation and the later exact serialized-byte import; neither history is erased. Trusted deterministic adapter JSON publications use their already constructed exact bytes and existing one-use publication permit. This keeps their verified narrow lineage distinct from an ordinary caller's unclassified object without granting a new trust exception.

Exact-byte import or permit consumption now commits before opening the research transaction or checking whether that storage handle is closed. Storage refusal therefore preserves already supplied observations. The lower `_publish` boundary retains the same bounded input and authority checks; there is no unguarded publication helper. Research-transaction rollback cannot remove control evidence. Missing or unsafe installed control authority still refuses and cannot invent a durable record. This is conservative accounting for supported import APIs, not observation of arbitrary Python objects outside those APIs or malicious-owner isolation.

Publication consumption now checks the originating intent's terminal state within its existing control transaction. A valid permit issued before `reject_before_access()` is refused afterward, and the already supplied bytes fall back to conservative import accounting. The check does not grant evaluator access, release authority or statistical eligibility.

The first v3 bounded run passed290 tests and failed one existing fault-injection fixture in30.63seconds (terminal62975). That fixture patched `put_json`, but the trusted adapter now publishes already constructed bytes; its intended receipt-storage fault did not occur. After moving the injection to the actual `put_bytes` boundary,291tests passed in31.73seconds (terminal8395). The final expanded raw-HTTP controls then passed **300 tests in32.35seconds** (terminal26081, exit0). Final Ruff and tracked whitespace checks pass across all24owned paths. These results are producer evidence; independent criticism, clean-install quality, full-suite compatibility and scope acceptance remain pending.

V3 retains the same final bounded command selection as v2: registry, provenance, bars, actions, CLI and the two named broker nodes. The separately owned D009 fixture adaptations are excluded from this producer's24-file manifest and must be accounted for by the integrator/quality reviewer. No D009 file, Git/context state, actual project store, credential, provider/model call, financial replay, protected operation or external transfer was changed or executed by this producer. Full legacy reconciliation, rollout/old-process fencing, evaluator isolation/release, consistent multi-store recovery and R13/R14 completion remain open.

| V3 corrected path | SHA-256 |
| --- | --- |
| `src/quanto/alpaca_actions.py` | `63219d3c9b2ff03855821a794341c03b95ab74af1cad2b5959f01326dc8b4715` |
| `src/quanto/alpaca_data.py` | `752dad50e4aceeda0e367dfc449715663fd5c8967980d787065411f69004a8fb` |
| `src/quanto/cli.py` | `69b4301ab74530659d5433967512bbf3cbaf423f9c96d8f6e1fd2c91a4c6f02d` |
| `src/quanto/evaluation_registry.py` | `c69c7de7e66c0d6f8b372304db482bf6d83ad0fe35960e55fc8fa00ac4a4b113` |
| `src/quanto/explorer.py` | `5bf8768505b02691aba5c321d70c8f62dddac3e4bbd5be31c983f2f43a23832a` |
| `src/quanto/provenance.py` | `c765ffdfbbaeed019b82552a2ad97b1ebf14699960582600ca372996e661f5f9` |
| `tests/access_fixtures.py` | `72410d741a0676a079306532e93668545b6a284a52b75de6060b8e9c1d99be92` |
| `tests/test_admission.py` | `5268c7debe91494126606937a6f477f0f2f9e4674a8c2360c7a3c31d5b3e2995` |
| `tests/test_alpaca_actions.py` | `bf08320f3c15d46ec527750277f2fd7136f563a468fce7a272a883e78fb2573e` |
| `tests/test_alpaca_data.py` | `c91d22c6333f57bb79883c4c82b403c1d926830ab492f346bae9a66e12ff486f` |
| `tests/test_cli_requests.py` | `ac5ac928ff7a3c8f500646ea54209f21289650fa5c09e09ea060b7584ec18ab1` |
| `tests/test_evaluation_registry.py` | `cba80802c40a98c0217ec54b89ebdcae5f05d0142759a7307175330037a2b3c4` |
| `tests/test_explorer.py` | `a0b50c807aa224e4d64e50f831b44ab4f13031179a7a3a3d64e2a409d3a79c98` |
| `tests/test_explorer_suite.py` | `81fa78f8dddcc05ba4b0b77a3b6e8f89723e3e0a46dfba3df56745407284e97a` |
| `tests/test_failure_memory.py` | `1281725db3853e26aa9a26476da9727613000691941d6a565e91bb7b95f50437` |
| `tests/test_policy_revision.py` | `cd9a303628c1b0ce02d34c2c32cf31015ea68a57cf79c0a8bd616643eb5f66b2` |
| `tests/test_provenance.py` | `4e5866c4c5bb491a992939f9bdc4e6c5c65b314e435fdeefe1c33c2ab5324ee0` |
| `tests/test_research_broker.py` | `6c4e6c2c7e8f9b5c95f6b6baef4e1ac17e09848dfd10501c39a7a575f756006f` |
| `tests/test_research_comparison.py` | `8fa13d6b41dd37993331a0e18a1fcd01eeb4fe00077f80df7c3710f177a979a3` |
| `tests/test_research_dispatch.py` | `5834db43c5ecf56c6baacf4d5c7c950839f150881215e04ebc6145fbdebfd52e` |
| `tests/test_research_failure_context.py` | `37c767f52aeb04f46ed3d506266632a035ef08bae4e41e994d9d7f489d8ae41d` |
| `tests/test_research_packets.py` | `f11eca0d6cb1e748a80320aff5ab190319fa48c4bccb7b1541dfd9a451ee943a` |
| `tests/test_research_workflow.py` | `34dbea72f7a3512cefe9ef2b95eaa474f07c1476cee953b08f13655b3432f1c9` |
| `tests/test_study_suite.py` | `f6a51f377b4c31a61d8a663bbfe516ceeefd4a949d6557a0f25cb48c51d16ce6` |

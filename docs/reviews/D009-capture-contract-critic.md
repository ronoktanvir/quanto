# D009 research capture contract: independent source criticism

**Recommendation: implement an offline, manifest-bound research capture and inert local verifier first; do not label that increment a complete Stage B backup or resumable operation.** The difficult boundary is the relationship between a consistent SQLite image, independently stored objects, and audit evidence outside both. A valid database copy alone does not establish complete research recovery.

**Latest bounded source disposition: the four original defects and the later quality-discovered compatibility blocker are closed at product SHA-256 `5f7f2526da8d82d5f648c42a3135af3f44dadbafe0be2f40e8888b923d856883`; no remaining code blocker was found within this candidate scope.** Independent quality and scope acceptance remain separate. Earlier dispositions below identify their historical revisions. This does not authorize actual capture or upload, certify complete evidence closure, or accept Stage B recovery.

Reviewer: `/root/d009_v2_critic_finish`, separate from the producer. Baseline inspected: `955710036e41270b05bdf56964ae65a530869e98` on `feat/recovery-snapshots`, after PR11 merged. The initial contract inspection was source-only; the later product findings/rechecks below used synthetic temporary databases. No production state, actual runtime receipt/database, key, credentials, account or financial result was opened. No external call, model council, research replay or financial test occurred. Contract verification scenarios are requirements; only the later explicitly described defect probes were executed by this critic.

## Consistency must cover the database/object boundary

`Provenance.put_bytes` publishes and fsyncs the content object while holding a journal write transaction; its later consumers publish database references after the bytes exist. This ordering supports a snapshot containing a committed reference and its earlier object. It also permits orphan objects after a rollback, so a directory listing is not equivalent to a database-reference closure. `finish` verifies direct `artifact_refs`, but does not recursively validate an arbitrary artifact graph.

Use a short, bounded database writer barrier spanning the selected database image and object/evidence capture. In the existing rollback-journal design, a dedicated connection can hold `BEGIN IMMEDIATE` to exclude cooperating new database writers, while an independent read-only connection performs the online backup. **Do not call Python SQLite backup on the same source connection while that connection owns the write transaction.** That arrangement can repeatedly encounter its own busy/locked state rather than produce the copy. A connection timeout alone is not a demonstrated bound on the backup loop: implement an overall deadline/progress abort and release every transaction/connection on all failure paths. Avoid SQLite schema initialization or a journal-mode change while acquiring the barrier. Check the actual supported mode; do not add an assumed WAL-checkpoint step.

This barrier pauses database transitions; it does not cancel remote work already authorized before it was acquired. Capture every table, including full reservations, uncertain amounts, consumed dispatch records, purpose allocations, exposure and lease/effect records, without pruning older days or normalizing unfinished states. A result that arrives after the boundary belongs to later source history. Restoration of the captured earlier state must remain inert and cannot justify retransmission, claim reclamation or budget release.

### Tombstones and deletion need an explicit rule

`purge` first commits `tombstone`, then unlinks the object outside that transaction, and finally appends the purge observation. A purge begun before the capture barrier can therefore continue deleting while the barrier is held. The barrier must not be described as universal filesystem quiescence.

The minimal compatible rule is to read the snapshot's tombstone set, exclude those bytes even if still physically present, and hold the database barrier while copying the selected nontombstoned objects. An already-started cooperative purge then affects an excluded object; a new tombstone cannot commit during capture. If a required dependency is tombstoned, record its identity/reason as an explicit unavailable dependency and refuse any claim requiring those bytes. Do not resurrect a tombstoned accidental secret or rights-restricted object by bypassing `read_bytes` and walking the physical directory. A stronger shared filesystem lock is another option, but would require every publication/deletion path to cooperate and a documented lock order; an advisory lock used only by the capturer is insufficient.

The copied objects need bounded regular-file reads, exact size and SHA-256 checks, and race detection against the opened files/directory identities. Missing, changed, unsafe or unsupported required evidence refuses finalization. No silent re-fetch, replacement, price filling or research rerun repairs a capture.

## Closure and sidecar coverage are distinct

The closure cannot be defined as only `provenance_outcomes.details.artifact_refs`. The existing schema also stores object identities in workflow manifests/assignments/effect outcomes/handoffs, broker configuration/alias/stage/tool-request rows, dispatch packet/private-response rows, suite rosters and nested content documents. Conversely, many SHA-256 fields identify source code, a request or a semantic projection rather than a stored object. Treating every hash-looking string as a mandatory object would confuse those roles; intersecting every hash with the current directory would silently hide a missing required object.

Require a versioned reference inventory for the supported schema and artifact kinds. Distinguish stored-object references, retained-byte identities, source-code identities and plain comparison hashes. Complete typed closure would require traversing declared object references to a bounded fixed point and refusing unsupported reference-bearing kinds. The narrowed first increment may instead report unknown nested kinds and unknown ordinary tables as explicit incomplete coverage, while still refusing altered known reference-table shapes, active schema such as views/virtual tables, and missing mandatory live dependencies in the known inventory. Bound object count, individual size, total bytes and traversal work. A conservative superset must be explicitly identified: copying all valid canonical nontombstoned objects can be an offline inspection candidate, but is not permission to upload unpublished/orphan contents. The full SQLite image preserves unrelated rows, but that fact does not validate their external dependencies.

The source also contains a legacy out-of-store artifact path: `cli.run_demo` writes `artifacts/synthetic/<digest>.json` and records its relative path in the outcome. Public D007/D008 reports identify retained oracle/verifier sources, execution receipts and failed harness evidence. Some such evidence is in the content store and some is a runtime sidecar; a source-only review cannot establish the actual inventory. Therefore require a reviewed, explicit required-source/audit selection manifest before a real capture can claim that coverage. Each selected file needs a safe logical path, byte bound, digest and required/optional status. Missing required files fail; declared omissions remain visible and prevent stronger recovery claims. Do not infer that a Git commit contains ignored runtime verifiers, or that a stored receipt digest reconstructs the missing receipt bytes.

The first implementation can exercise this selection contract on synthetic fixtures while the real inventory remains pending. It must not quietly label database-plus-objects as complete research evidence. The selected scope is research-only: exclude `conversations.sqlite`, session/CSRF continuity, credentials, `.env`, OAuth/browser state, private decryption identities and unrelated runtime files. Research accounting still includes reservations used by the chat clients; exclusion of chat history does not permit deletion of those research-database financial records. Live cross-database transitions are outside this initial consistency claim.

## Verification must not initialize or revive anything

`Journal.__init__` changes journal/synchronous settings and installs schema/triggers; `Provenance.__init__` creates directories/files, invokes that initializer and installs more schema. Workflow, dispatch and broker constructors also install schema. None is an acceptable way to open the captured database for read-only verification.

Open the already-existing captured database explicitly read-only, disable mutation, extensions and trusted schema where supported, and use fixed bounded queries over verified table shapes. Verify SQLite integrity/foreign keys, the existing event-chain algorithm and the manifest's recorded count/head without an initializing constructor. Reusing a pure event verifier or a reader-only adapter is preferable to duplicating its hash semantics. Event-chain integrity is not an independent audit of arbitrary materialized tables; the database byte digest binds those captured tables. Comparing a head with the manifest checks internal identity, not independently trusted freshness or detection of a fully rewritten/truncated source before capture.

The verifier must not expire leases, recover jobs, cancel workflows, settle/release holds, create sessions or dispatch anything. It should require no key, environment credential or network. Check that input bytes/identities remain unchanged and emit bounded verification metadata separately. Tests must show that a valid input produces no schema, journal, lock, sidecar, object or row mutation and no constructor/network/research-runner call. Wrong-key checks and downloaded restore belong to a later encrypted transfer increment, not a claim made by this plaintext verifier.

## Safe output and acceptance boundary

Use a new private destination disjoint from the source database, object tree and selected evidence paths in both directions. Reject source/destination aliasing, symlink components, existing output, hardlink surprises, special files and paths that escape an explicit allowlist. Hold directory descriptors for file copies, use no-follow opens and compare descriptor/path identities where SQLite's pathname API requires a residual local-path assumption. A privileged filesystem owner remains outside application isolation; do not claim path-string validation prevents that owner from replacing the tree.

The minimal first format can be a plain private directory with fixed manifest paths and no archive extraction. Write exclusive files, fsync them and directories, validate the complete manifest, and publish completion last. An interrupted or raced capture remains an explicitly incomplete candidate, never a selectable latest recovery copy. If archive packaging is added, reject absolute/traversal/duplicate member names, symlinks, hardlinks and special files; enforce bounds before extraction and do not use blind `extractall`.

Before implementation acceptance, independent synthetic checks should cover a writer at every relevant boundary, an orphan object, publication before a reference commit, a pre-barrier purge paused after tombstoning, required missing/corrupt/tombstoned dependencies, unsupported references, missing required sidecars, same-connection backup refusal/bounded cancellation, output/source overlap and path substitution, interrupted finalization, corrupt/truncated chains and a verifier that attempts any write or external effect. These checks establish software behavior only. Actual-data capture, rights/privacy review of the exact selection, encryption and upload, off-Mac key/account recovery, externally retrieved-key challenge and isolated downloaded restore remain Stage B evidence; trusted freshness and unattended effects remain Stage C.

## Inspected source identities

| Artifact at baseline | SHA-256 |
| --- | --- |
| `docs/D009_POLICY.md` | `68eea41a20a171681e53368b98954fefa8e65e7513ec21b6dc482dfc25851c61` |
| `src/quanto/ledger.py` | `29c3f14bdae924b4d369b49b59c3ec7e5079810d76e55992fa1800d49a3da6cf` |
| `src/quanto/provenance.py` | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |
| `src/quanto/research_workflow.py` | `64ca63f155a2417021bb8632673f14ec12ff7d497881aa13a95d7330911ab02b` |
| `src/quanto/research_dispatch.py` | `120834deb63abebeeb54a14f8cf470ad43fd9ac1f44979ee96fe9c88ba20c1f1` |
| `src/quanto/research_broker.py` | `aa4f9e93f9fc471273bf2e6c1a0d67acb74583228618cecd17aa9ec513419e34` |
| `src/quanto/study_suite.py` | `c3e552ef9998e72ae6f69b55bf43750d51f94522faf98a26ecbb624042f46360` |
| `src/quanto/cli.py` | `7201b943efea1777c70e0fff7ce3d2e953089ba58648e360e53b5f6a22dabbd7` |
| `src/quanto/conversations.py` | `a704d127f14df9dc6d6757f6182c899e875d58ea46292666b53efeb2ec46a8a3` |
| `src/quanto/provider.py` | `5f4f214d079bd4a17ddc3049163d5a3bfc9acd8ba2508a3dfe2f5ad5c4c0ace0` |

## Producer proposal and accepted narrowing

I inspected the builder's source-only proposal `docs/reviews/D009-capture-implementation-plan.md` at SHA-256 `223efcb4de68cfea634c7b784041648647c60cb2828b002bce8c818a2207bd91` and sent the source hazards and corrections directly. The producer adopted separate barrier/backup connections, snapshot-tombstone exclusion, raw inert verification and explicit evidence-coverage limits. The lead authorized implementation of `src/quanto/recovery.py` and `tests/test_recovery.py` only, without a CLI, actual project-data access, key use, network or archive extraction.

**No contract blocker remains for that narrowed candidate, subject to the lead's destination correction.** The proposal's initial `runtime/recovery/snapshots` destination is superseded: output must be an explicit new destination outside the entire source project root, with overlap/alias checks in both directions. I requested that the producer update the written plan accordingly. A distinct subtree of runtime is not the selected first-increment destination.

The candidate preserves the whole research database and every available valid canonical content object except snapshot-tombstoned digests. It must distinguish opaque/orphan/pending bytes from published evidence, check known typed roots, refuse missing/corrupt required live objects, and retain unavailable tombstoned dependencies and unknown nested coverage as limitations. `.pending-*` leftovers are counted but not promoted. The conservative object superset is accepted only for private offline candidate capture. Its future transfer still needs exact selection, rights and privacy review; copying a file locally does not grant those approvals.

For this first product revision, `full_recovery_accepted=False` and `typed_closure_complete=False` remain unconditional. Explicitly omitted runtime audit sidecars, legacy artifacts, source/dependency copies and chat state must be named in the manifest/report rather than inferred absent from an empty current reference set. Verifying known declared references is a bounded property and must not be presented as complete nested coverage. An internally verified candidate can therefore be useful without satisfying complete research evidence or Stage B.

This narrowing is routine implementation inside accepted D009 and retains its threat model. It does not substitute a weaker trusted-freshness guarantee, revive scheduling, grant uploads or certify externally held key/account recovery. At this contract stage, no implementation had been inspected; the subsequent bounded product inspection and corrected-source disposition follow.

## First frozen-product findings

The initial product was independently inspected at `src/quanto/recovery.py` SHA-256 `0688bd81cdcc903df31629bd1d2d1cb9a862b0a6f7e88751955cdd3d146955a4`, with producer tests SHA-256 `4db722632e271465ec9c9d0a7b5ff7b5a6ddb163e2fd2f826af8e26ed7913cc6`. The lead supplied the metadata, pre-lock growth and hot-journal concerns as hypotheses; I independently reproduced them. The suite-request classification finding arose from this critic's source comparison and was also reproduced. These are `synthetic_fixture` results against temporary stores, not observations of production. The source remained frozen during those reproductions.

**P1, closed by corrected recheck: opening a writable source can perform hot-journal recovery.** A synthetic subprocess changed many pages inside an uncommitted rollback transaction and exited without cleanup. The frozen capture accepted that source, rolled its main database back to committed bytes and removed the hot journal. This was ordinary SQLite crash recovery, not invented application rows, but it contradicts the unconditional claim that this capture changes no source state. The read-only verifier's authorizer cannot prevent recovery already performed by opening/reading the separate writable capture connection. A corrected design must demonstrate hot-journal refusal without source-byte/sidecar changes; opening and establishing a read-only source snapshot before any writable barrier is one viable direction, subject to bounded lock-order tests under a preexisting writer. A stale pre-open sidecar check alone does not close the race.

**P2, closed by corrected recheck: a suite launch request identity is mistaken for a mandatory object.** `study_suite.run_suite` constructs a member's `request_sha256` from the inline roster request and inserts the launch before invoking the child. It stores the run-level request and roster, but does not require a standalone object at every member-request digest. The frozen `DIRECT_REFS` nevertheless requires such an object. A valid-shape synthetic launch with its digest-only request identity refused with `required_object_missing`. Remove that unconditional object-root mapping and preserve the identity in the copied database/roster; absence of byte storage must not be repaired by a financial replay.

**P2, closed by corrected recheck: unsupported manifest metadata passes inspection.** Five separate self-consistent manifest mutations were accepted: numeric `started_at`, null `finished_at`, a malformed producer digest, an arbitrary consistency claim and negative unpublished-temporary count. Check the recognized consistency value, bounded nonnegative integer count, well-formed producer digest and timezone-aware ordered timestamps. A syntactically valid producer digest still is not independent producer attestation; that stronger property requires an externally trusted expected identity.

**P2, closed by corrected recheck: pre-lock growth bypasses the database bound during expensive work.** A cooperating synthetic writer grew the database after initial path validation but before barrier acquisition. The frozen capture audited and copied the over-bound database before finally refusing at the destination byte check. The result was not falsely accepted, but the source-size bound failed to constrain the audit/backup it was intended to bound. Recheck the source's opened/path identity and size after the barrier and before audit or backup; retain the later destination checks as well.

The producer received all four reproductions and corrected the product. No remaining-code-blocker disposition is granted to the initial product. Separate quality owns broad real-SQLite concurrency, full-table preservation and inert-byte verification; my probes are defect-focused and do not replace that evidence.

| Independent initial-product evidence | SHA-256 |
| --- | --- |
| `/tmp/quanto-capture-critic-probe.py` | `7ec92f4cb58b57061b694d7cdd79ec083f324c1fc8a60a3080df0b20997d18ae` |
| `/tmp/quanto-capture-critic-output.txt` | `596920a5a3379b2c5240ecdf300ae825f7c306874ec186cbbd99526c9d86ee35` |
| `/tmp/quanto-capture-hot-journal-probe.py` | `48ce012cc4599421464dd0f9e07ed475332c66615111c82334f1a3646621682c` |
| `/tmp/quanto-capture-hot-journal-output.txt` | `bacf8a4d9af234225d17b3ac5c2e00400bba26aafdbb98d67980f34c4124f10c` |

The exact initial probe/output bytes have now also been retained under the ignored `runtime/d009-capture-critic/` directory as `initial-probe.py`, `initial-output.txt`, `hot-journal-probe.py` and `hot-journal-initial-output.txt`, with the same hashes. No real runtime, key, account or financial state was accessed to reproduce the findings.

## Corrected product recheck and evidence limits

The corrected product establishes and retains the read-only source transaction/schema read before opening the separate writable barrier. My same genuine-hot-journal scenario now refuses with the source database unchanged, not rolled back, and the journal retained. This closes the source-mutation finding for that demonstrated path. The order may refuse under a preexisting writer rather than waiting for it indefinitely; separate quality owns the real concurrency/deadline integration checks. Source identity and size are rechecked immediately after the barrier and before `_audit`/backup.

The corrected request classification accepts the valid-shape digest-only suite launch. All five malformed metadata mutations now refuse with fixed manifest reason codes. The inspector also compares canonical JSON state/coverage rather than relying on Python's equality between booleans and integers. My original pre-barrier growth injection attempted its writer after the newly retained read-only lock and was itself blocked; that intermediate run is retained and is not counted as proof of the new size check. Moving the same synthetic committed growth to just before the initial read-only connection produces `unsafe_file` before any audit or copied database pages, which independently confirms the post-lock bound.

I also compared every remaining scalar root family against its actual publication path: explorer manifest/dataset identities, suite manifest/roster, comparison registration, broker configuration/alias/stage/tool request, private model response, workflow handoff and optional failure fix bytes are stored or verified as content references before the corresponding publication. No second digest-only scalar mapping was found. The workflow manifest actually uses `input_refs` as required by `create_run`; assignment inputs additionally include stored upstream handoffs, and effect/handoff reference lists are verified by the producer services before publication.

`known_database_references_verified` is limited to the manifest's `known_database_refs_v1` extractor: those scalar roots, assignment/intent/effect arrays, the selected inline provenance/workflow/handoff reference fields and the two acquisition-event reference kinds. It is not universal semantic validation of all rows, all hashes or nested object schemas. Generic request/body/code hashes remain identities, while unknown ordinary tables and unchecked nested documents retain incomplete coverage. The unconditional false full-recovery/typed-closure/off-Mac/execution flags and explicit sidecar/legacy/chat omissions remain necessary.

The verifier checks SQLite integrity/foreign keys before rejecting active view/virtual schema, with extensions disabled and bounded execution. Quality raised that ordering as a source question; neither reviewer established a resulting mutation or external effect. I found no additional actionable blocker under the stated local-owner threat boundary, and no broader adversarial-SQLite isolation claim is made.

**Evidence-retention limitation:** neither the producer nor this critic saved a separate contemporaneous copy of the initial untracked `0688bd...` product or `4db722...` producer tests before correction. Their SHA-256 identities, tool reads/corrective patch history, initial probes and observed outputs are retained, but the original source/test byte files must not be described as preserved. No reconstructed file is claimed as an original. This limits later reproduction of the exact pre-fix implementation from retained files; it does not turn the observed independent reproductions into tests of the corrected source. The corrected source/test bytes are separately retained now, before further changes.

| Corrected inspected/executed artifact | SHA-256 |
| --- | --- |
| `src/quanto/recovery.py` | `07665bb3a7c030017aa3876f602ab89e0a05ec9a950f2b640fe4abcfe87fa5c0` |
| `tests/test_recovery.py` (inspected, not counted as this critic's tests) | `9fdad9ca69f483b2ba1152f7fcce97642477eaac0bbd38e2035397e15524e540` |
| Retained `runtime/d009-capture-critic/corrected-probe.py` | `a2c97cea420c6a75922441136868d537bf3d3295125ef6b0b41450f9a4a56458` |
| Retained `runtime/d009-capture-critic/corrected-output.txt` | `6dae55217ae7fb157839b87df104b6afc1f27722b82bd29dab1fa39e609215db` |
| Retained `runtime/d009-capture-critic/intermediate-recheck-output.txt` | `a7c879dbb29ff7c091ea1a79f934647eb77bf357056d55ad99ee4959fa3049d8` |
| Retained `runtime/d009-capture-critic/hot-journal-corrected-output.txt` | `9236288f1aeb7dd7a5fa2283b72a309301961ac04374d6f045640552ccac15f6` |

The retained `corrected-recovery.py` and `corrected-test-recovery.py` copies have the same respective product hashes. Source hashes were checked again after my rechecks. The final disposition is limited to this offline candidate: no actual project capture, upload, key/custody operation, financial replay, scheduler activation or Stage B recovery was performed or accepted by this critic.

## One-shot local controller: source-only disposition

**No controller-source blocker was found at `runtime/d009-capture-actual/run-local-candidate.py` SHA-256 `1dbb71f3642797592defbe5201f2d65c314b71f47c4754d7a23a0cb482f5a592`.** I read and hashed only that explicitly permitted operational source file; I did not execute it or read any actual attempt, result, destination, key, environment, database or object.

Its resolved file location selects the primary project root. It checks the exact corrected product/test hashes before dispatch, exclusively writes and fsyncs a consumed attempt before import/capture, and refuses an existing attempt/result/failure. Even two cooperating controllers passing the preliminary existence check cannot both create the exclusive attempt. It creates a unique mode0700 sibling parent and invokes the fixed root's capture exactly once, followed by inspection bound to the returned manifest digest and event head. Source/test hashes are rechecked afterward. The capture/inspection reports must agree and full-recovery, complete-closure, off-Mac and execution flags must each remain false.

The private result contains the bounded inspection report and identifiers; displayed success contains lifecycle/count/flag metadata, and failure displays only fixed recovery categories. No row, object payload, private key or credential is printed. The reviewed product has no provider/financial/resumption call, and the controller additionally blocks the ordinary socket connection/name-resolution methods it uses as a defensive guard. That monkeypatch is not an operating-system network boundary against arbitrary replacement code. Local candidate paths are retained privately for reconciliation, with no cleanup, overwrite or automatic retry.

The lead specifies an isolated Python launcher with a minimal environment, private captured stdout/stderr and a120-second process deadline. That launcher was not part of this one-file inspection; this report does not claim to have verified its execution. This disposition permits the bounded controller source to proceed to the separately gated actual local candidate after final quality/scope acceptance, and supplies no upload, complete-recovery or worker-revival authority.

## Supported-Python compatibility correction

**P1 compatibility blocker, closed by focused source/regression recheck:** separate full clean-install quality discovered that its supported CPython3.11.9/SQLite3.45.1 build omits `Connection.enable_load_extension`. The previous unconditional call therefore refused28 recovery cases; quality reported1,387 other tests plus37 subtests passing in that clean run. Quality separately reported1,415 tests plus37 subtests passing on the prior source Python3.13 environment. Those are attributed quality results, not this critic's executions, and the earlier `07665...` disposition did not establish compatibility with that clean build.

The corrected product differs from the retained `07665...` bytes only by obtaining the optional method with `getattr(..., None)` and calling it with `False` when present. It never requests enablement. The unchanged SQLite authorizer still denies SQL `load_extension`, mutations and unsupported actions. No fallback swallows a failure from a present extension-control method, and no environment/key/network access or execution path is added.

I executed an independent two-case capability regression using real SQLite connections subclassed to expose or hide only that optional API. Each case captured and inspected a temporary invented research store with equal reports; ordinary reads succeeded, while SQL extension loading and DELETE both refused. The absent case made zero extension-control calls; the present case made five, all with `False`. No extension was enabled or loaded. This is a controlled capability simulation on this critic's interpreter; separate quality owns native clean Python3.11 validation. No broader suite rerun or actual project-state capture was performed by this critic.

| Compatibility-corrected artifact | SHA-256 |
| --- | --- |
| `src/quanto/recovery.py` | `5f7f2526da8d82d5f648c42a3135af3f44dadbafe0be2f40e8888b923d856883` |
| `tests/test_recovery.py` (inspected) | `6edb1e99f37f28eda64fcbe233c12693ae4fd5917130edda63663cff081a0e8a` |
| Independent `runtime/d009-capture-critic/optional-extension-probe.py` | `04eff7a934c2b279f538e1e2b511948bbe066b87bc0e079472213f7926ee630c` |
| Retained `runtime/d009-capture-critic/optional-extension-output.txt` | `0c3cdb64819907a08cc7bd2f99eb816b7cddb31a7f678e000df1731652aec9c3` |

Exact corrected source/test copies are retained as `compatibility-recovery.py` and `compatibility-test-recovery.py` in the same ignored review directory. The prior `07665...`/`9fdad...` copies remain unchanged. Hashes were checked after the independent regression.

The reviewed controller at `1dbb71...` pins the prior source/test hashes and will refuse the compatibility-corrected product. It was not executed. Its pins must be updated and reviewed before any actual local candidate, with final native quality and scope dispositions still required. No upload or stronger recovery claim follows from this compatibility fix.

## Final controller pin update

**No blocker was found in the final static controller revision at SHA-256 `817699781b5bcd8b770314d95ed75cc17b6070098facbafb36f894040714b6ff`.** I reread only the explicitly permitted `runtime/d009-capture-actual/run-local-candidate.py` operational source and verified its hash; I did not execute it or inspect any actual receipt, source database/object, credential, key or account.

The controller now pins the accepted compatibility-corrected product `5f7f2526da8d82d5f648c42a3135af3f44dadbafe0be2f40e8888b923d856883` and tests `6edb1e99f37f28eda64fcbe233c12693ae4fd5917130edda63663cff081a0e8a`. Its failure metadata reports a preserved candidate only when the destination was assigned and actually exists. Exclusive consumed intent, unique private sibling destination, exactly one capture and bound inspection, source rechecks, false acceptance/execution flags and bounded metadata output remain within the previously inspected scope.

The lead reports that no attempt/result/failure exists; that is attributed preflight evidence and was not checked by this critic. The planned absolute isolated-Python launch uses PATH `/usr/bin:/bin`, LANG/LC_ALL `C`, disabled stdin, exclusive private stdout/stderr and a120-second timeout. This static disposition does not claim that launch has occurred or attest its runtime outcome. It introduces no upload, paid work, key use, restart or automatic retry authority.

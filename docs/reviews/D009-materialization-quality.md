# D009 materialization: independent execution quality

The frozen helper passes the bounded synthetic quality checks in source and a clean native Python 3.11 installation. This accepts an exact pinned-byte copy followed by the unchanged strict destination inspector. It does not accept an actual materialization, offline availability, typed closure, complete recovery or execution readiness. No actual candidate or private record was accessed by this reviewer.

## Revision and isolation

Reviewer: `/root/d009_v2_quality_finish`, separate from lead producer `/root` and critic `/root/d009_v2_critic_finish`. Evidence kind: `synthetic_fixture` throughout.

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/recovery_materialize.py` | `118783f4790aff9c4bb1f1827d4ed573834afea6acb8f48ffdc0d96ef79f7c01` |
| `tests/test_recovery_materialize.py` | `9cc4be2f0baf04644d9857edae79baf6623cb37af64109619cae1999ca30c8d8` |
| Unchanged `src/quanto/recovery.py` dependency | `5f7f2526da8d82d5f648c42a3135af3f44dadbafe0be2f40e8888b923d856883` |
| Independent harness | `2af8e11d88f59597bb11f52ebc4cd5bd9a2090d27c13f0bbf524d5051ac6d41e` |
| Final clarified contract read for this review | `414f9012bbec32bb1f2e723c2343dce9497aae477d0b4843e67a89e38731dcba` |

The test source tree was exported from committed public revision `6454c07461eb70dde20d29ad3e94ccde436039d2`, with only the two frozen materialization files added as product/test code. Hashes were checked before execution. Changing D008 registry/integration files from the shared working tree were excluded; the exported package has no evaluation-registry module. The independent harness stayed outside that tree. Fixtures create an invented raw Journal/SQLite database and one invented object, then use the frozen capture library; they do not invoke a guarded production Provenance constructor.

A fresh target installation was built offline, without dependencies or build isolation, from this exported source using the existing native Python 3.11 environment. Its actual imported materialization path and SHA were printed before tests. Test support packages came from existing local installation paths, with automatic third-party pytest plugins disabled and pytest source-path injection disabled. Socket connection methods were denied in the clean runner and independent fixtures. These guards constrain application calls; they do not attest that filesystem services cannot retrieve or synchronize bytes.

## Executed results

| Environment/check | Observed result |
| --- | --- |
| Exported source, producer tests | 19 passed, 0.33 seconds |
| Exported source, independent probes | 21 passed, 0.30 seconds |
| Clean installed Python 3.11.9, producer plus independent | 40 passed, 1.02 seconds |
| Focused Ruff, new source/test plus independent harness | Passed |
| Syntax parse, same three files | Passed |

The source independent run used Python 3.13.12 / SQLite 3.50.4. Clean Python 3.11.9 used SQLite 3.45.1, where `Connection.enable_load_extension` is genuinely absent; all 40 targeted tests passed without a compatibility proxy for that API. No broad suite was run for this bounded increment; final integration CI remains separate.

One initial independent-harness launch selected an unrelated `python3` without pytest and stopped with `No module named pytest`, before importing product code. Its stdout/stderr are retained separately. The corrected launch used the intended project interpreter and passed all 21 cases. This preparation failure is not a product failure. The lead/critic's initial `07b210…` interruption defect and subsequent correction are historical evidence in their reports, not executions claimed by this reviewer.

## What the independent probes establish

The normal copy preserves source file bytes and modes, writes equal destination bytes with private file/directory modes, and invokes the original strict inspector exactly once with the pinned manifest/head and a 15-second verification limit. A separate probe confirms a tighter two-second verification limit is passed through unchanged. Patching the Journal constructor to refuse after fixture preparation does not affect copying or inspection.

Real descriptor/path observations with injected timing changes cover manifest, database and object mtime variation independently. Each copy succeeds with exact bytes and a change count of one. Another probe changes the source object's contents to different bytes of equal length after its buffer has been read. The destination retains the original pinned buffer and verifies, while the source path now differs. The returned `source_path_stability_verified=False` is therefore a necessary qualification, not merely a reserved future flag.

Seven source refusal cases cover wrong byte length, wrong digest, nonprivate object mode, nonprivate source directory, hardlink, symlink and extra top-level inventory. All refuse before calling the destination verifier. An equal-byte inode replacement is separately refused as `source_identity_changed`. A destination inside the source refuses without changing source bytes. Producer cases additionally cover wrong manifest/head, missing/extra objects, existing destinations and repeated-attempt refusal.

The actual `_resident` bit test is exercised using an invented destination stat projection containing Darwin's `SF_DATALESS` bit, producing refusal and a failure marker. A separate projection removes `st_flags`; the copy can verify but retains `offline_availability_verified=False` and `filesystem_retrieval_possible=True`. Neither case measures actual filesystem residency or certifies an Application Support parent.

Independent interruption cases raise KeyboardInterrupt and SystemExit after strict verification, during the final residency checks. Both become fixed `MaterializationError`, leave a failure marker, make the ordinary strict inventory inspector refuse, and prevent automatic reuse. A controlled clock expires during database copying after destination creation; it likewise refuses and preserves the marker. Producer checks also exercise pre-verification interruption and invalid/excessive limits.

## Failure boundary and disposition

Failure marking is best-effort. An independent probe injects a strict-verifier failure followed by an OSError while writing `failure.json`. The original call correctly refuses, but the fully copied destination has no marker and later passes a distinct strict byte inspection. A repeated materializer call still refuses `destination_exists`. This is not an original success receipt, and later inspection cannot create one retroactively. Hard kills can also prevent terminal recording. The outer controller must durably record its exclusive intent before work and require its own verified terminal success before adoption; directory existence or a later valid layout is insufficient. The lead corrected the contract's formerly unconditional marker wording; this reviewer read and hashed that clarification after the tests, without changing or rerunning the frozen product.

No remaining bounded helper blocker was found under that outer acceptance requirement. Cooperative copy checks do not bound every blocking filesystem operation; the controller supplies its own process timeout. Safe ancestry, Application Support placement, actual destination flag observations, no-overwrite/exclusive outer files and receipt acceptance remain controller responsibilities requiring their own review. No controller or actual materialization was executed here.

Required nested evidence, source/audit coverage, legacy reconciliation, off-Mac key/account recovery, selected-use rights, encrypted transfer/restore, trusted freshness and the future D008 control-store recovery contract remain incomplete. The returned false full-recovery, typed-closure, execution, production-recapture, automatic-retry and offline flags remain part of this limited acceptance.

## Retained evidence

Ignored synthetic harness and outputs: `runtime/recovery-materialization-quality/`. The environment record retains the temporary exported source and fresh installation paths; both frozen source files remain there. `evidence-manifest.json` records all output and artifact hashes, including the failed harness launch and the earlier contract identity `d85ff13d65021b3323a5737cd9a12bd8c8865b9cacf38849dc350699684e274a`. The final clarified contract identity is pinned above. No passed test was rerun during final report completion after the reported model-capacity interruption; retained output supplies these observations, and that interruption is not a product failure.

Key stdout identities: source producer `401d86b3082351244547e1eda53b8f14860eeb0498986b120f46f47121d2527b`; source independent `b0c9a4a2df507052d22f8d23cbdfc680ad0fe7c1b48c2992c06f0e4abb82e30a`; clean combined `6bc4a8a10d84e430a42fcf3b77f8c8387c80a92290e3b7c7c90885698615291e`. Their stderr files are empty. Separate criticism is recorded in `D009-materialization-critic.md`; its seven probe results are attributed to that reviewer and are not added to this reviewer's counts.

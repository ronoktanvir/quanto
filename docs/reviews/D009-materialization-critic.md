# D009 pinned local materialization: independent criticism

**No remaining code blocker was found at corrected source SHA-256 `118783f4790aff9c4bb1f1827d4ed573834afea6acb8f48ffdc0d96ef79f7c01`.** Independent criticism reproduced a catchable-interruption evidence gap in the initial prototype, then verified its correction and the remaining focused behaviors. This accepts the bounded content-staging module, not an actual materialization, new research capture, complete closure or recovery.

Reviewer: `/root/d009_v2_critic_finish`, separate from the lead who produced this module. Accepted background: D009 policy and the safe actual-refusal audit at `D009-closure-actual-refusal-critic.md`, frozen SHA-256 `46ce518f1c87d42c05dbf6600f773f613369fbd88ff45ff03352d9010674be46`. This review inspected public source/tests and executed owned temporary synthetic fixtures only. No actual candidate, production database/object, account, key, credential, model/provider call, financial replay or project-data copy was accessed or executed by this critic.

## Governing contract: content identity, then strict destination verification

Materialization is a copy of the exact earlier generation, not another capture of current application state. The trusted manifest digest and event-head checkpoint identify that generation. Each selected manifest/database/object buffer must match its pinned digest and applicable byte length. This preserves the recorded database bytes, including budgets, uncertain effects, exposure and unfinished work, without reinitializing or normalizing them.

The source read may observe an mtime transition while the filesystem supplies bytes. That cannot pass the original stable-read predicate, and the materializer does not change that predicate. Instead, it accepts only the exact expected buffer while retaining regular-file/private ownership/link checks and equal device/inode/size across before-fstat, after-fstat and path-lstat. It reports source mtime transitions and explicitly refuses to attest source-path stability. A matching buffer is not a proof of what currently occupies the path.

The new destination uses exclusive mode0700 directories and mode0600 byte writes, with file/directory fsync. Only the pinned fixed inventory is copied; filenames derive from fixed layout/canonical digests. Source xattrs, flags, mtimes, links and arbitrary runtime files are not cloned. After copying, the ORIGINAL unchanged snapshot inspector must pass with the same expected manifest/head and a limit at or below15seconds. The300-second copy budget is a distinct bounded staging budget, not an increase to the verifier's bound. A source read blocked in the filesystem also requires the outer controller's process deadline; cooperative checks alone are not a hard interruption of kernel I/O.

The returned flags correctly preserve `source_path_stability_verified=False`, `filesystem_retrieval_possible=True`, `offline_availability_verified=False`, `production_recaptured=False` and the inherited incomplete-recovery/execution limits. The old snapshot format identifier does not establish globally offline operation. Operating-system filesystem retrieval can use network outside an application socket guard, and this review attributes neither a particular cloud/provider nor the original closure cause.

## P2, closed: catchable interruption omitted the failure marker

Initial source `07b210710f6a5c0ffdeabc48773cb4f853b3e35156131960f9accbe64d9296de`, with tests `f843cbc2c2666d3a85209d2123497c9c462102b9edea9032b231eb60acadcdfb`, caught ordinary errors but excluded `KeyboardInterrupt` and `SystemExit`. My synthetic interruption just after all payloads were copied escaped without a failure marker. A later separate strict byte inspection accepted the completed byte layout, while repeated materialization correctly refused `destination_exists`. The latter two observations are distinct: later byte validity did not supply the missing earlier operation outcome.

The corrected source catches `BaseException`, attempts a fixed failure marker, and maps the interruption to `MaterializationError` without private exception text. My fresh `KeyboardInterrupt` and `SystemExit` cases now retain the marker, refuse strict inspection because of the failed layout, and reject destination reuse. The original source/test copies and reproduction remain preserved.

Failure markers are best-effort, including when storage refuses the marker write; a hard kill cannot run cleanup. Therefore the actual one-shot controller must durably consume its intent and require an explicit successfully retained materialization result before adoption. Directory presence, lack of a failure marker or a later independent byte-valid inspection cannot reconstruct a missing prior success. This is an operational acceptance gate, not a guarantee the module can enforce after process/storage failure.

## Independent executed evidence

The first attempted reproducer stopped during `Provenance` fixture construction before calling materialization. Its original script/output are retained and are not counted as a product failure or pass. A minimal raw-SQLite synthetic fixture then isolated the materializer and reproduced the interruption defect on the exact initial source. No financial calculation was used to construct or verify the fixture.

On the corrected source, seven focused cases completed with all assertions passing:

- Catchable `KeyboardInterrupt` and `SystemExit` each produce fixed refusal, a failure marker, strict rejection and no automatic reuse.
- An induced source mtime transition still makes the original verifier refuse the source; the materializer accepts the exact pinned buffer and its new destination passes the unchanged verifier.
- A same-size source-content change after the read leaves the retained buffer valid. The destination contains the expected bytes and verifies, while the source-path claim remains false. This directly tests the buffer/path distinction rather than silently assuming they coincide.
- A wrong source digest refuses before destination verification and retains a failed copy.
- An injected destination-verifier refusal is invoked exactly once at15seconds and cannot be promoted; its failed directory remains uninspectable.
- A synthetic native `SF_DATALESS` bit at the destination is refused, with a failure marker.

The interruption item contains two separately executed cases; the list summarizes seven total. The prototype's producer-suite counts are not counted as this critic's execution. Separate quality owns the broader source/native-Python qualification.

## Gates for the actual staging controller

The reusable module accepts a private destination supplied by its caller; it does not choose Application Support. The actual controller must pin the old capture/attempt identities, consume a distinct one-shot intent, and choose a fresh exclusive candidate under `~/Library/Application Support/Quanto/recovery-candidates`, outside Documents, the primary project and the old candidate. It must retain the old candidate's names/content rather than intentionally modify, delete or relabel it. Reads may themselves cause OS-controlled metadata/flag transitions, so no stronger physical-unchanged-source claim is available.

The module rejects the Darwin dataless flag when exposed by `st_flags`; missing flag support is not a residency or offline attestation. The Mac controller should require native flag observability and report its bounded checks truthfully, without making this location a permanent-residency guarantee. Final destination verification and flag checks remain required even after exact buffer writes. No source guard may be waived on that destination.

Success/failure receipts belong outside the fixed-layout snapshot. A new materialized copy must retain the exact original manifest bytes/digest and event head; it is not a newly trusted latest checkpoint. Do not call capture, source-data admission, constructors, model/broker functions or worker revival to fill gaps. Historical source/audit omissions, unknown nested profiles, use-specific transfer rights, off-Mac key/account recovery, encrypted transfer and isolated restore remain open. Actual copying awaits a separately reviewed controller and explicit lead execution; none occurred in this review.

## Exact identities and retained evidence

All private review artifacts below are under ignored `runtime/recovery-materialization-critic/`. Initial and corrected product/test byte copies were saved before further changes.

| Artifact | SHA-256 |
| --- | --- |
| Initial product / `initial-materialize.py` | `07b210710f6a5c0ffdeabc48773cb4f853b3e35156131960f9accbe64d9296de` |
| Initial producer tests / `initial-test-materialize.py` | `f843cbc2c2666d3a85209d2123497c9c462102b9edea9032b231eb60acadcdfb` |
| Fixture-setup failure script | `3a9e25431070f66d7a8594a2e37b5b7bf830a4f059a237b255614a406f868bb5` |
| Fixture-setup failure output | `5d7a59e8bcddb9cbf4df0f76b375161aa5d8a50ebe52e9827cfb1059f286914b` |
| Initial successful reproducer `probe-interruption.py` | `f5163ae486407f1876ad526e6ab21decde608cb1882317fc63f7f23d58ebcf53` |
| Initial defect output | `55e5a88bcfe28ea6030985b696b75842f4f00e1c9cbe72b60170bdb94c8f1cff` |
| Corrected `src/quanto/recovery_materialize.py` / `corrected-materialize.py` | `118783f4790aff9c4bb1f1827d4ed573834afea6acb8f48ffdc0d96ef79f7c01` |
| Corrected producer tests / `corrected-test-materialize.py` | `9cc4be2f0baf04644d9857edae79baf6623cb37af64109619cae1999ca30c8d8` |
| Independent `probe-corrected.py` | `055b2d0fd49e68b203fcec7588ac14929396dee20259f7e53d889a72a7d8d6f7` |
| Corrected independent output | `5ac2b0bbab678a0a64a8c5d5369989c4c056802296dbd0869eab251a6b665172` |

Final source/test hashes were checked after the rechecks. Existing recovery source remains `5f7f2526da8d82d5f648c42a3135af3f44dadbafe0be2f40e8888b923d856883` and closure source remains `3618457a9170f0533efe0b4081478a3662dfd7f6031525dce24f488a28cd8981`; this work did not change or re-certify them.

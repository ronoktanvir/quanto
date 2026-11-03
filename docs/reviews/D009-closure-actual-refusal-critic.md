# D009 actual closure refusal: safe-evidence audit and diagnostic proposal

**The closure attempt refused without a report; a later direct base-verifier diagnostic refused specifically with `file_changed`.** That identifies the guard reached by the later call, but neither the affected file/tuple field nor the original closure cause. The next distinct diagnostic should observe only the failed read's already-retained metadata and buffer-digest comparison, without reopening candidate files or relaxing the guard.

Reviewer: `/root/d009_v2_critic_finish`. I read only the explicitly permitted safe projection and metadata diagnostic listed below, the previously permitted controller source and public product source/reports. I did not read original private receipts, the destination, candidate files, database rows, object payloads, keys or accounts. I did not rerun the actual controller, closure inspection, capture or any financial/model work.

## Observed failure and evidence limits

The safe projection reports a lead-executed one-shot attempt using controller `6857ce823c4028eb7ec215768901b33715d6c0fdf2334a16fa16ed4505cd1bc6`, frozen closure source `3618457a9170f0533efe0b4081478a3662dfd7f6031525dce24f488a28cd8981` and unchanged recovery source `5f7f2526da8d82d5f648c42a3135af3f44dadbafe0be2f40e8888b923d856883`. Inspection was invoked, the child returned1 with zero stderr bytes, no outer timeout occurred, and no private report or safe result file was produced. It records `snapshot_verification_failed`, no new snapshot/upload/replay and no accepted recovery.

The recorded process interval is2026-11-03T01:09:49.984983Z to01:10:05.097545Z:15.112562seconds. These fields are consistent with a caught refusal from the reviewed controller; they are not a second execution or an independent audit of the underlying private receipts. The consumed attempt and its failure remain the authoritative original outcome.

The additional lead-authored metadata-only projection reports a matching manifest/inventory,40 tables,229 objects, matching declared database size, zero file type/permission or object-size mismatches, and1.115267seconds elapsed. It explicitly says that object payloads and database rows were not read and that the prior cause is unestablished. Those observations narrow obvious metadata/inventory explanations; they do not verify object content hashes, database integrity, event semantics or nested JSON/profile compatibility.

## What the source can and cannot establish

The closure API performs an initial and final `inspect_research_snapshot` call, each capped at the lesser of its remaining total budget and the base default15seconds. The total closure budget is45seconds; the reported outer process was not killed by its120-second launcher deadline. Thus the elapsed time makes the15-second base-verifier boundary a useful first diagnostic target, but does not prove which phase ran or that its deadline fired.

The same outer `snapshot_verification_failed` catch also wraps `RecoveryError` from other helpers: raw source/manifest/object reads, strict JSON parsing and related recovery checks. It is not exclusively an initial/final base-verification label. In particular, byte-valid nested content can fail strict JSON parsing during graph traversal and receive the same outer category. Separate quality reproduced that distinction with invented data; no actual payload was inspected to assign it here.

Within the base verifier, an explicit deadline check can raise `capture_deadline`; a SQLite progress-handler interruption can instead become generic `inspection_failed`. Explicit digest, database-integrity, event-chain, reference or coverage predicates also have fixed refusal codes. The closure wrapper currently discards these distinctions from persisted output. None should be inferred retrospectively from timing alone.

Python's `raise ... from None` suppresses displayed context, but the exception object's `__context__` chain remains available to the catching diagnostic. A new direct base-verifier call can therefore record an allowed fixed `RecoveryError` category and bounded native SQLite error numbers/OS errno without serializing raw error text, SQL, paths, arguments, traceback frames or payloads. SQLite interruption is evidence of interruption; it must not be automatically relabeled corruption or proof of the original attempt's phase.

## First distinct one-shot diagnostic: preparation

At the lead's explicit request I authored `runtime/recovery-closure-actual/diagnose-snapshot.py`, SHA-256 `b6be552bdae552d5326c4cb89456220869df12da0becc91da52b3088ca3b0bac`. At preparation time it awaited the lead's independent inspection and explicit execution. I am its author and do not certify it as an independently reviewed controller. I performed only a static AST syntax parse and never imported or executed it. The lead's subsequent execution is recorded separately below.

The source pins all four frozen product/test files, the original capture result/destination, the failed closure controller/attempt/failure and both permitted safe projections. It checks the fixed expected manifest/head and sibling destination shape, preserves the absence of an original report/result, then exclusively consumes new `diagnostic-attempt.json`. Its result/failure names are separate from the consumed closure attempt. Existing diagnostic files refuse; no overwrite, automatic retry or deletion is provided.

It invokes `recovery.inspect_research_snapshot` exactly once with `Limits(seconds=15.0)`, retaining every other existing bound and the exact manifest/head. It does not invoke the closure walker, capture a replacement, patch helpers, extend deadlines, load credentials, enable network, resume workers, release holds or perform model/financial work. Bytecode writing is disabled before project imports. Output is limited to fixed status/flag/digest metadata, monotonic elapsed time and at most eight links of allowlisted recovery codes/native numeric SQLite codes and errno.

On a base refusal, the diagnostic records the observed refusal in `diagnostic-result.json` and returns1; an unexpected controller failure uses separate `diagnostic-failure.json`. A base pass returns0 but still reports `original_failure_cause_established=False`, no closure inspection and all stronger acceptance flags false. A pass would show only that this later direct base check completed; it would not identify the original phase or rule out a graph-helper failure. A refusal would identify this diagnostic's current predicate/interruption, not authorize repair or prove causation of the earlier attempt.

The preparation contract required the lead to inspect this exact source before a distinct launch under the specified isolated Python/minimal environment, disabled stdin, exclusive private stdout/stderr and120-second outer timeout. No actual diagnostic has been run by this critic. The original attempt remains failed, the product remains frozen, and any later change to limits, profiles or recovery scope needs its own concrete review rather than a silent retry.

## Exact permitted evidence

| Artifact | SHA-256 |
| --- | --- |
| Safe original-failure projection | `ae2cf7f698d0d553d95ebcbe6acc835405efb4cb2ec3452c57f5c612e2c80aa3` |
| Metadata-only diagnostic projection | `f72318aaddb0c5af8e45600e28e91ee8ddb7c35ab78b212bd51cf13b79d58bf4` |
| Previously reviewed actual controller source | `6857ce823c4028eb7ec215768901b33715d6c0fdf2334a16fa16ed4505cd1bc6` |
| First diagnostic source, subsequently lead-executed | `b6be552bdae552d5326c4cb89456220869df12da0becc91da52b3088ca3b0bac` |

The projection reports original attempt/failure/process receipt hashes, but this critic did not open those underlying receipts. This review preserves the actual refusal and proposes a bounded observation; it does not close actual closure acceptance, complete evidence recovery, Stage B or unattended operation.

## Lead-executed direct diagnostic: observed guard refusal

The lead states that it independently reviewed and executed the first diagnostic once. I read only the newly permitted safe result at SHA-256 `51e968b211f0e4970d53439b5a63c412c959722e54d84fc8e5dc7e3778e121bc` and process projection at `8592bab1374ed0f909e3413bcb075b1d8312dbdaf76ca7a8ee8d6a559538dfc9`. They report `base_verification_refused`, `recovery_codes=["file_changed"]`, no SQLite/OS error codes,2.929007seconds inside the call, child exit1, zero stderr and no outer timeout. Process elapsed time is3.036114seconds.

At frozen recovery source5f7f2526..., `file_changed` is raised by `_read` when its bounded-read condition or before-fstat/after-fstat/current-path tuple equality fails. The compared tuple contains device, inode, size and nanosecond mtime. That later refusal is a read-stability guard result, rather than a demonstrated deadline for this call. The safe result does not identify which file or tuple component was involved. It also cannot establish the original closure phase or exclude a separate graph-helper cause; `original_failure_cause_established` correctly remains false.

A metadata-only change can trigger this guard while read bytes still match. Conversely, a matching already-read buffer does not prove that the bytes currently at its pathname still match. The diagnostic must preserve both distinctions and must not turn a buffer match into `current_file_verified` or bypass the refusal.

## Prepared narrower read-guard diagnostic, not executed

At the lead's next explicit request I authored a new distinct controller, `runtime/recovery-closure-actual/diagnose-file-change.py`, SHA-256 `fcf68a9083ac6bc5680cad7642653c225b8abf75a6290fc224d19e21eeef901e`. It leaves the executed source and every prior attempt/result unchanged, pins the first diagnostic source and newly permitted result/process identities, and uses separate exclusive `filechange-*` files. It again invokes only the direct base verifier once with the unchanged15-second limit. I performed a static AST syntax parse only; this controller was not imported or executed by me and awaits the lead's independent review.

If that new invocation independently raises `file_changed`, the source walks at most eight exception contexts and16 traceback frames per context. It selects only frames whose code objects are the exact frozen `recovery._read` or base-inspector functions. It does not dump frames or arbitrary locals. From the existing read frame it emits only:

- A fixed file class: manifest, database, object or unclassified.
- Separate before/after fstat and after-fstat/path-lstat inequality booleans for device, inode, size and nanosecond mtime; no actual stat values.
- Whether the already-produced bytes are within the original read bound.
- Whether an expected digest is available and `bytes_read_match_expected`, using only that retained immutable buffer. Manifest expectation comes from the fixed pin, database expectation from the already-parsed manifest in the known inspector frame, and object expectation from the canonical filename already used by the read.

There is no diagnostic reopen, extra lstat, file repair or second verification call. The existing frozen verifier performs its usual reads; the observer only interprets the resulting exception's selected retained values. No path, digest value from the private graph, raw bytes, arbitrary error text, SQL, argument or traceback-local dump is emitted. A buffer digest match says nothing about current pathname stability. A pass, different refusal or missing eligible frame remains an explicitly limited observation, with the original cause and all stronger acceptance flags false.

As author, I left independent controller-source review and explicit execution to the lead. Product source/tests and the candidate were unchanged by this preparation. A source copy is retained in the ignored critic evidence directory before any later change. All original failed attempts remain preserved. The lead's later execution and permitted safe observations follow.

## Read-guard diagnostic and filesystem metadata: bounded audit

The lead reports that it independently reviewed the exact delta from the first diagnostic to source `fcf68a9083ac6bc5680cad7642653c225b8abf75a6290fc224d19e21eeef901e`, then executed the new controller once. I read only its explicitly permitted safe result/process projections and filesystem metadata summary, identified below. I did not inspect the actual candidate, file paths/stat values, payloads, attribute values or private underlying receipts.

The new result reports another `file_changed` refusal in4.073923seconds. The child returned1 with zero stderr and no outer timeout. Its eligible read frame is classed as an object. Only the before/after fstat nanosecond-mtime comparison changed; device, inode and size did not. The after-fstat and path-lstat observations agree on all four compared fields. The already-read buffer was within its read limit and matched the expected object digest.

These facts identify the failed comparison for this new invocation. They establish neither the current pathname's content after that observation nor why its metadata changed. The matching buffer cannot bypass the original guard, and the original closure attempt's phase/cause remains unknown. The controller correctly records no stronger acceptance, upload, replay or new research capture.

The later metadata-only summary reports229 objects:227 with flags `0x40008060` and2 with `0x8040`. Twelve bounded attribute-name samples report only `com.apple.provenance`, with no query errors or attribute-value reads. The summary itself records `filesystem_cause_established=False`, no payload reads and no snapshot mutation by that survey. The lead separately checked local Apple SDK `sys/stat.h` and the official Apple xnu header for `SF_DATALESS=0x40000000`; this definition is lead-attributed primary-source evidence, not an additional source fetched by this critic. Under that definition, the flag is present on227 of the229 surveyed objects.

The dataless flags and observed mtime transition support an on-demand materialization hypothesis. They do not identify a specific cloud/provider, prove that hydration caused this particular transition, or explain the original closure failure. Reads can induce operating-system filesystem work outside an application's socket guard, so a later staging operation must not be described as globally offline or guaranteed network-free.

A routine D009 implementation may stage the exact pinned manifest/database/object buffers into a new private Application Support candidate, retain the old candidate, and then require the unchanged strict verifier at the same15-second limit. That separates content identity from the original source's physical stability; it must not weaken `_read`, recapture production state or promote incomplete evidence into recovery acceptance. The root-produced materialization prototype will receive a separate independent source/fixture review; this safe-evidence audit does not certify it or authorize an actual copy.

| Newly permitted safe artifact | SHA-256 |
| --- | --- |
| `filechange-result.json` | `2da5f07821848634fece73de2aafb380c5ad3da804ab97ed97a16dc4e7561660` |
| `filechange-process.json` | `e08fc5a46a5b86a3f2732b93fda09e996e33d471309a528da2be544ff294d823` |
| `filesystem-metadata.json` | `e7455f3b16c5bf5261ad7be068dbf6fdd12c9e8bf5e5e818e85a437122c73928` |

No further validator run, guard relaxation, actual-data copy, financial/model operation or private candidate read was performed by this critic. The finite inspector's synthetic acceptance and these unsuccessful actual attempts remain distinct evidence.

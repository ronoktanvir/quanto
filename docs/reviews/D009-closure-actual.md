# D009: first actual dependency inspection and diagnosis

**The first actual dependency inspection refused and returned no dependency report.** This does not reverse the earlier successful capture, but it does leave the candidate's current content verification and structural dependency coverage unresolved. All attempts and the original candidate remain preserved. No complete backup or operational recovery is accepted.

## Execution and evidence boundary

After the corrected product received separate criticism, quality and scope acceptance, the lead executed the statically reviewed controller once. It consumed its own new intent and invoked only the read-only closure API against the existing candidate. It did not recapture production, replay research, call a provider/model, upload data, read credentials or restart workers.

The isolated child started at `2026-11-03T01:09:49.984983Z` and finished at `2026-11-03T01:10:05.097545Z`, exiting 1 with zero stderr bytes and no outer timeout. Its failure receipt records `snapshot_verification_failed` at `01:10:05.065582Z`, with `inspection_invoked=true`. Neither a private graph nor a safe result exists. No graph node or coverage count can be inferred from this failed attempt.

| Retained artifact | SHA-256 |
| --- | --- |
| Controller source | `6857ce823c4028eb7ec215768901b33715d6c0fdf2334a16fa16ed4505cd1bc6` |
| Consumed attempt receipt | `aef1b259f3f3f14f0548e4bce1ca955a4de5abc686dd432711f183bfc55d67b5` |
| Failure receipt | `cb4d0ad9162f2c6f84fd835d2e5a67f0bc6dd75ac7dde94aa85479f76232b729` |
| Process receipt | `5273f06af1d9f26821f83616e4d81a308a4c6b1873f1f55e666abc30056752aa` |
| Safe metadata projection | `ae2cf7f698d0d553d95ebcbe6acc835405efb4cb2ec3452c57f5c612e2c80aa3` |

The source pins are closure module `3618457a9170f0533efe0b4081478a3662dfd7f6031525dce24f488a28cd8981`, closure tests `2ba696117cd60c503f642fbb739ec28386688c223b04a3503952e07db6c20e57`, capture module `5f7f2526da8d82d5f648c42a3135af3f44dadbafe0be2f40e8888b923d856883` and capture tests `6edb1e99f37f28eda64fcbe233c12693ae4fd5917130edda63663cff081a0e8a`. The original manifest and event head remain those in [the successful capture report](D009-local-capture-actual.md).

Reviewers receive only the explicitly permitted safe projection, metadata diagnostic and operational source. The actual candidate's private content remains lead-inspected; independent fixture execution must not be described as independent inspection of that content.

## Bounded metadata observation

At `2026-11-03T01:13:49.834397Z`, the lead performed one separate read-only manifest, inventory and file-metadata observation. The manifest digest, top-level inventory and 229-object inventory matched. Database size was 1,376,256 bytes; the total object size was 6,788,622 bytes. No file type/ownership/permission/link or object-size mismatch was observed. The manifest records 40 tables. This observation took approximately 1.115 seconds, read no database rows or object payloads, and changed no candidate files.

The safe diagnostic receipt is `f72318aaddb0c5af8e45600e28e91ee8ddb7c35ab78b212bd51cf13b79d58bf4`. Matching metadata excludes several simple inventory defects; it does not re-establish content digests, journal integrity or the cause of the prior refusal.

## Unresolved cause and next diagnostic

The closure API maps recovery errors to one fixed code. Its initial and final snapshot inspections each have a maximum 15-second budget within the 45-second closure bound; other recovery helpers can also raise the mapped exception. The approximately 15.11-second process duration is consistent with a deadline hypothesis, but does not identify a phase or establish that hypothesis. Corruption is likewise not established.

The next proposed diagnostic is a distinct reviewed direct snapshot-inspector invocation at unchanged bounds, recording only allowlisted reason codes and native numeric SQLite/OS error codes. It must retain a new exclusive intent and all outcomes, never reuse the consumed closure controller, and never print exception text, tracebacks, private paths or payloads. This proposal is not evidence that the diagnostic has run or that the original failure is resolved.

## Subsequent direct-verifier diagnostic

The lead inspected the distinct diagnostic controller `b6be552bdae552d5326c4cb89456220869df12da0becc91da52b3088ca3b0bac` and executed it once at `2026-11-03T01:24:11.282508Z`. The child finished at `01:24:14.318601Z`, exit 1, zero stderr, no outer timeout. The base verifier refused after 2.929007 seconds with the fixed reason `file_changed`, without a native SQLite or OS error code. Its 15-second budget was unchanged. No closure traversal, snapshot creation, mutation, upload or research/model replay was invoked.

The consumed diagnostic intent is `2edf0f1253d7221e06fd37afb5dcb12e5ba31d15b1d9a92746711c7d96c5cd40`; safe result is `51e968b211f0e4970d53439b5a63c412c959722e54d84fc8e5dc7e3778e121bc`; process receipt is `8592bab1374ed0f909e3413bcb075b1d8312dbdaf76ca7a8ee8d6a559538dfc9`. Original failure evidence remains unchanged.

This observation identifies the current refusal as a file-read stability check, not a deadline refusal. It does not identify which file property changed, establish content corruption, or retroactively determine the original closure failure's phase or cause. Separate synthetic quality probes also demonstrate that the closure wrapper maps graph-parse errors to the same generic snapshot error. A new bounded diagnostic is being prepared to report only the file category, changed metadata fields and digest-match booleans from a known recovery read frame, without revealing private paths or content or relaxing the stability check.

## Read-frame observation and filesystem flags

The lead independently reviewed the next diagnostic source `fcf68a9083ac6bc5680cad7642653c225b8abf75a6290fc224d19e21eeef901e` and executed it once at `2026-11-03T01:31:25.569993Z`. It used the same direct verifier and limits, observing only existing locals in exact known exception frames. The child ended at `01:31:29.714826Z`, exit 1, zero stderr and no outer timeout. The verifier again refused `file_changed`, after 4.073923 seconds.

This invocation's failed read was an object file. Only modification time changed between the initial and final file-descriptor metadata checks; device, inode and size were unchanged. The subsequent pathname metadata matched the final descriptor metadata on all four fields. The already-read buffer was within its bound and matched the expected digest. These are observations about that read and its captured metadata; they do not verify later pathname contents or establish the original closure failure's cause. Safe result SHA: `2da5f07821848634fece73de2aafb380c5ad3da804ab97ed97a16dc4e7561660`; process SHA: `e08fc5a46a5b86a3f2732b93fda09e996e33d471309a528da2be544ff294d823`.

A separate metadata-only survey at `01:33:21.343287Z` found 227 objects with flags `0x40008060` and two with `0x8040`. The local Apple SDK header and [Apple's XNU header](https://github.com/apple/darwin-xnu/blob/main/bsd/sys/stat.h) define `SF_DATALESS` as `0x40000000`: 227 of the 229 objects therefore had that flag at the observation. A bounded sample of 12 files exposed only the attribute name `com.apple.provenance`; no attribute values or object payloads were read. Safe survey SHA: `e7455f3b16c5bf5261ad7be068dbf6fdd12c9e8bf5e5e818e85a437122c73928`. The initial survey preparation failed because this Python has no `os.listxattr`; that failure is retained as `3f0526c1f2a4f38caac729c40ab39ff0aaec2c7a32bf65c971fd973f803300d2`. The corrected observation used the native tool's documented name-only mode.

Together, dataless flags and a modification-time transition during a read support filesystem materialization as an explanation. They do not identify a specific cloud service, demonstrate who changed the metadata, or prove the original error's cause. An application socket guard does not prevent OS-mediated retrieval of file bytes. Earlier statements that these controllers made no network/provider/upload calls describe their own operations; they do not attest the absence of filesystem synchronization or retrieval outside those processes. The original successful capture was not an offline-availability test.

The next local increment prepares a new private candidate outside Documents, accepting source buffers only against the pinned original manifest and exact lengths/digests, then requiring the unchanged strict verifier to pass on the destination. Source timestamp variation is recorded separately from source stability; destination dataless flags refuse. The prototype has 17 producer fixture tests passing, but separate reviews and an explicitly reviewed controller are still required before any actual materialization. No actual copy has occurred, no original file is replaced, and all broader recovery gates remain incomplete.

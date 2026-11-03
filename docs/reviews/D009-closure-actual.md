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

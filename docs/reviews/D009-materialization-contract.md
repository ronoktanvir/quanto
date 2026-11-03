# D009: materialize the pinned local candidate

**Create a separate copy of the exact retained snapshot, then require the unchanged strict verifier to accept that destination.** The original candidate remains preserved. This is routine local staging under accepted D009, not another production capture, a relaxed integrity check, an external backup or a fresh research attempt. No actual materialization has run.

The [actual diagnosis](D009-closure-actual.md) records a source object's modification time changing during a read whose buffer matched the expected digest. A metadata survey found 227 of 229 objects marked dataless. These observations support filesystem materialization as an explanation, without identifying a specific service or establishing the original closure failure's cause. A socket guard cannot prevent OS-mediated retrieval; neither the source nor destination is promised to remain available offline.

## Content identity and physical stability

The trusted input is the original capture's pinned manifest digest and event head. Copy only its exact manifest, database and canonical object inventory. Every source buffer must match its declared byte length and SHA-256, under the original size/count limits. Require owned private regular files, no links, and unchanged device/inode/size across descriptor and pathname observations. Source modification-time variation is counted rather than represented as source stability. A matching captured buffer does not certify subsequent source-path contents.

The destination is new and exclusive, with 0700 directories and 0600 files. Write ordinary bytes without cloning links or extended attributes. Refuse an observed Darwin dataless flag. The generic helper cannot determine whether a folder is managed by a cloud service; the reviewed actual controller must pin a private staging parent under Application Support, outside Documents, verify its safe ancestry and current metadata, and disclose the limits of that placement. On platforms without `st_flags`, absence of the flag API is not proof of local residency.

After copy and directory synchronization, run the original `recovery.inspect_research_snapshot` unchanged with the same expected manifest/head and a maximum 15-second verification budget. Copy work has a separate maximum 300-second cooperative budget; a controller timeout supplies the process boundary. These bounds do not prevent all blocking filesystem calls by themselves. The result retains every original omission and false recovery/execution flag, adds observed source timestamp-change count, and explicitly denies source stability and offline-availability claims.

## Failure and authority

Existing destinations refuse. Catchable failures and interruptions attempt to retain a fixed failure marker; when written, the ordinary strict inventory check rejects that failed layout. Marker writes are best-effort: a storage error can leave a byte-valid layout even though the operation refused. Never clean up, overwrite or reuse a failed directory automatically. A hard process kill may prevent cleanup and can leave a byte-valid layout without a terminal receipt. The outer controller must durably record an exclusive intent before copying and require its own verified terminal result for acceptance; directory presence is insufficient. Later read-only reconciliation is a distinct observation and cannot fabricate the missing original result.

No application constructor, live research database, provider/model call, key, financial replay, entitlement reset, worker revival or upload belongs in this helper. Source rights and external key/account recovery remain separate gates. The captured state predates the proposed D008 access-control database; materializing it cannot restore future identities/reservations or supply a multi-store recovery contract.

## Implementation and independent review

Producer: lead `/root`. Initial source `07b210710f6a5c0ffdeabc48773cb4f853b3e35156131960f9accbe64d9296de`, tests `f843cbc2c2666d3a85209d2123497c9c462102b9edea9032b231eb60acadcdfb`: 17 synthetic tests passed in 0.31 seconds. Exact initial bytes and output remain in the ignored producer review directory.

The separate critic reproduced a catchable-interruption gap after all payloads were copied: `KeyboardInterrupt` escaped without a failure marker, and a later strict byte inspection accepted that layout. Reinvoking materialization still correctly refused the existing destination. The critic's initial fixture preparation stopped before any materializer call because an unrelated changing access guard rejected its constructor; that preparation failure is separate from the successful minimal-SQLite reproduction.

Corrected source: `118783f4790aff9c4bb1f1827d4ed573834afea6acb8f48ffdc0d96ef79f7c01`; tests: `9cc4be2f0baf04644d9857edae79baf6623cb37af64109619cae1999ca30c8d8`. Catchable `BaseException` failures now retain the marker and a fixed `MaterializationError`. Explicit KeyboardInterrupt/SystemExit regressions verify the marker, strict-inspector refusal and reuse refusal. Nineteen producer tests pass in 0.99 seconds; focused lint passes. Corrected output SHA: `05b413cdb3bb528f1d1589733e8a5f26f08e4ede5eb856957ba72ae1aefd34ca`. Source and corrected bytes are retained separately.

Criticism of this correction, separate execution quality, scope review and the actual one-shot controller remain pending. No test here uses actual project data. Passing this finite helper will still leave typed dependency closure, required source/audit evidence, off-Mac key/account recovery, selected-use rights, encrypted transfer, downloaded restore and trusted scheduling freshness incomplete.

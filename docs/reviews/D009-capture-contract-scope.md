# D009 offline research capture: contract and scope review

**Implementing an offline research-state snapshot and isolated inspection is a routine subset of accepted D009, not a new architecture decision.** The policy explicitly permits research-only capture with conversations excluded. No new five-perspective council or repeat owner spending approval is required. Separate implementation criticism, quality validation and scope review remain necessary before accepting the code. This report accepts the bounded contract below; it does not accept an implementation, actual capture, Stage B recovery or R14 completion.

Reviewer: `/root/d009_scope`, independently assigned scope and acceptance. Source-only inspection on `feat/recovery-snapshots`, base commit `955710036e41270b05bdf56964ae65a530869e98` (merged PR11). I read the public context and D009 policy, the earlier data-recovery perspective, and relevant schema, object lifecycle and verification source. I did not inspect production databases, artifacts, keys, account data or private runtime records, execute tests, make network calls, or modify anything except this report.

## What this increment can establish

The immediate deliverable is local capture and inspection software, exercised against synthetic temporary stores. A successful local check may establish that an explicitly bounded research snapshot preserves its captured database, selected object inventory and declared references. It cannot establish recovery of the whole operation. `conversations.sqlite` and its chat history, pending turns, inbox, session/CSRF state and rate records are excluded. Source/audit evidence outside the content store also remains excluded unless individually selected and verified under a documented allowlist.

Research-only does not mean deleting chat-related spending from the research database. The shared research ledger can contain reservations, dispatches and purpose allocations for several callers. Preserve all of them. Chat content cannot be reconstructed from those cost records, and omission of chat must not justify freeing a hold or replaying a request.

The manifest and result should identify the scope explicitly, for example `research_state_offline_v1`, with separate fields for complete database preservation, object/reference coverage, omissions and inspection outcome. Keep project-backup acceptance, whole-operation recovery and effect resumption false. This is a proposed interface contract, not a claim that these fields already exist.

## Minimum capture contract

1. **Capture the entire database through SQLite's online backup API.** Do not rebuild selected tables, filter by purpose/date/status, copy a live main file with `cp`, or initialize a fresh application schema and import a convenient subset. Preserve schema objects and all rows, including tables the inspector does not yet understand. Inventory the captured schema so unsupported reference-bearing structures produce an incomplete/refused coverage result rather than silent omission. The source uses rollback journaling; do not impose a WAL checkpoint or change production journaling mode.

2. **Retain state that constrains future actions.** This includes the core journal, experiments, all attempts/outcomes/reviews, reservations in every state and day, consumed dispatches, jobs/fences/leases, provider allocations, research dispatch holds and observations, private-response references, workflow assignments/claims/intents/effect starts/outcomes/handoffs/terminals/cancellations, broker records, study suites/comparisons, exposure history, failure dispositions, provenance and tombstones. Preserve pending and uncertain records without normalization, expiry, refund, settlement, reset or inferred completion. SQLite integrity and a valid event chain alone do not establish preservation of these materialized rows.

3. **Establish a bounded consistency window for database and files.** SQLite's backup API provides a consistent database copy, not an atomic database-plus-directory copy. Existing `Provenance.purge` commits a tombstone before unlinking its object; `put_bytes` publishes objects inside a cooperating database transaction. Coordinate publication, tombstones/purges and selected evidence writers through a tested capture protocol, or reject a raced capture. A new advisory lock is insufficient unless relevant writers honor it. Do not infer quiescence from the website being ready, an unchanged event head, or a pause flag checked only before new provider calls. Tests can establish the protocol on fixtures while actual capture remains unexecuted.

4. **Copy bounded safe objects and verify typed closure.** For this small store, the earlier D009 data perspective permits copying all valid non-tombstoned content-addressed objects as a local inventory, then checking known typed references against it. That is an implementable first approach; it is not permission to upload unrelated objects without privacy/rights review. Reject invalid names, links, special files, oversized objects, digest mismatches, partial publications and unexpected dependencies. Enumerate typed reference sources and supported nested manifest schemas. Do not treat every 64-character hash as an artifact: request/code hashes and inline document identities can be non-object identities. Direct `provenance_outcomes.details.artifact_refs` alone is insufficient; workflow inputs/effect outputs, private responses, broker aliases/stages, registered datasets, suite rosters and comparison/failure references also matter. Unknown reference-bearing schemas must be supported or explicitly prevent an artifact-complete result.

5. **Preserve deletion semantics and omissions.** Retain original tombstone identities, reasons and times while excluding tombstoned payloads, including files still physically present. A legitimate tombstoned dependency remains unavailable on inspection; never recreate it. Distinguish that recorded omission from an unexpectedly missing live object, which fails closure. A snapshot may faithfully preserve history containing tombstones without establishing that every historical study is reproducible. Later remote-generation retention must account for artifacts tombstoned after earlier backups; local omission does not erase older copies.

6. **Publish a bounded private generation only after validation.** Use a new destination, no overwrite, private permissions, explicit file paths/sizes/digests, schema identity, captured event count/head, table-state identities, capture times and consistency/coverage/omission declarations. Keep incomplete attempts distinguishable from accepted generations. Validate every included path and the entire manifest. Exclude credentials, permanent/canary identities, environment/OAuth/browser files, service registrations, locks and unrelated runtime content. Preserve exact source and audit evidence only through explicit safe selections; a source hash alone cannot recover absent source bytes.

## Isolated inspection contract

Inspect a separate destination with direct read-only SQLite connections. **Do not construct `Journal`, `Provenance`, `ResearchWorkflow`, a dispatcher or another schema-initializing application object on the restored database.** `Journal.__init__` changes pragmas and executes table/trigger creation; `Provenance` and workflow components add further schema. This would alter the evidence being inspected. Reuse pure verification logic or a deliberately read-only adapter without invoking constructors. Any later mutating application compatibility check belongs on a second disposable copy and must disclose its changes.

Validate SQLite integrity, foreign keys where declared, complete schema/table preservation, event chain and manifest-bound head/count, exact file hashes and typed closure. Preserve source and restored database hashes across inspection to demonstrate that the audit did not mutate the copy. An event-chain check verifies events, not arbitrary table consistency, and a manifest from the same archive is not an independent freshness witness.

No inspection path may load credentials, send requests, initialize a broker/model client, start a dashboard/supervisor/worker, renew a lease, retry an uncertain effect or replace production. Restored jobs and authorizations are historical state to inspect, not permission to execute. An authentic older snapshot can pass internal checks; this increment must not describe it as the newest trustworthy generation.

Relevant independent quality cases include retained cross-day uncertain holds and consumed dispatches; every present table/schema object; unknown schema coverage; missing/corrupt objects; nested references and non-object hashes; tombstones with present and absent payloads; raced publication/purge; unsafe paths and resource bounds; interrupted capture; unchanged inspected database; and no network or application initialization. These are acceptance recommendations, not tests performed by this reviewer.

## Remaining gates and decision boundary

Off-Mac key custody is not a dependency for writing and testing this offline module. It remains a dependency for accepting real external recovery, alongside a retrieved-key challenge, recoverable Runpod/email/2FA access, selected-use data rights, allowlisted encryption/upload, an independently checked real snapshot and isolated downloaded restore. No project-data transfer or permanent-key access is authorized by this source review. Existing owner authority remains unchanged; user participation is needed only for evidence that agents cannot provide, not another spending permission.

Stage C's external pre/post-effect records, single-writer fencing, stale/divergent-history refusal and trusted freshness remain separate. Automatic operational revival, dropping accounting/exposure state, silent chat inclusion or a weaker recovery threat model would exceed this subset and require a new substantive decision review. Implementing the stated research-only contract does not.

## Exact source identities

These hashes identify the contract and inspected source excerpts, not acceptance of future capture code.

| Artifact | SHA-256 |
| --- | --- |
| `docs/D009_POLICY.md` | `68eea41a20a171681e53368b98954fefa8e65e7513ec21b6dc482dfc25851c61` |
| `src/quanto/ledger.py` | `29c3f14bdae924b4d369b49b59c3ec7e5079810d76e55992fa1800d49a3da6cf` |
| `src/quanto/provenance.py` | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |
| `src/quanto/research_workflow.py` | `64ca63f155a2417021bb8632673f14ec12ff7d497881aa13a95d7330911ab02b` |
| `src/quanto/research_dispatch.py` | `120834deb63abebeeb54a14f8cf470ad43fd9ac1f44979ee96fe9c88ba20c1f1` |
| `src/quanto/research_broker.py` | `aa4f9e93f9fc471273bf2e6c1a0d67acb74583228618cecd17aa9ec513419e34` |
| `src/quanto/explorer.py` | `6a3f02d27f0c062d993ee3d112f0e76b88221fc8653305b84be62b822bcb9745` |
| `src/quanto/study_suite.py` | `c3e552ef9998e72ae6f69b55bf43750d51f94522faf98a26ecbb624042f46360` |
| `src/quanto/research_comparison.py` | `c2e933841f1664b62528b4342b37a34e7b3452e7783d91f495f78a6b05d65446` |
| `src/quanto/failure_memory.py` | `ee8200079cc0e091b06d60be6fe4ccb3d4886eb1ea986ee626db65ae7f9f7ee7` |
| `src/quanto/conversations.py` | `a704d127f14df9dc6d6757f6182c899e875d58ea46292666b53efeb2ec46a8a3` |

No scope blocker prevents implementation of this contract while owner key custody is pending. Acceptance must remain proportionate to the later observed evidence: synthetic software checks first, local research-state inspection next, and external recovery only after its distinct gates.

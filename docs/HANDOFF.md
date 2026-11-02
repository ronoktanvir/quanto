# Resume here

Read AGENTS.md and CONTEXT, STATUS, REQUIREMENTS, ROADMAP, DECISIONS. Inspect current Git/processes/provider ledger before trusting historical checkpoints.

## Current checkpoint — 2026-11-02 UTC

Repository remains private at https://github.com/ronoktanvir/quanto. PR #1 merged as `56964a78d7db003ac3515eb1beba255ff90db256`; PR #2 passed final CI and merged as `8aea7652750c5cf191e2b44a9089e9e88a2522c1`. D005 was developed on `feat/research-provenance` through [PR #3](https://github.com/ronoktanvir/quanto/pull/3); inspect its current remote checks and merge state. No public release or license is authorized.

The D005 integrated suite passed 364 tests plus 12 subtests and full lint. It adds the private artifact/submission store, bounded Alpaca bars/calendar acquisition, registered synthetic exploration, CLI commands and private credential setup. Separate criticism, quality and scope reports under `docs/reviews/D005-*` identify final inspected hashes. Independent quality validation also passed an offline wheel installation outside the checkout. These tests and local reviews do not imply remote CI success; check PR #3's final head.

## Actual private data evidence

The owner chose US markets first and crypto later, approved Alpaca, and saved paper-account keys through `scripts/configure_alpaca.py`. Both provider credentials stay in `.env`, mode 0600. Never print or send values. Alpaca credentials are not intrinsically read-only; the adapter enforces specific GET routes and assistants receive no tools.

Three immutable-JSON CLI acquisitions succeeded at adapter SHA256 `88c60d80be6295767c8cc9de65c239a5d528135c0bb89de98b7574cad52bb2eb`: raw bars, calendar, and adjusted bars for the January 2024 example range. All returned 21 records with matching dates. Every raw/adjusted OHLC row differed. Ignored `runtime/alpaca-pilot-check.json` records the check and submission IDs. Exact raw/normalized objects and receipts are private under `data/objects`; do not expose values to external models or Git.

These acquisitions remain inspection-only. Calendar matching is one observation; complete action handling, information timing, executable-price assumptions, stable issuer history and account/exchange terms are not certified. A dict-request mutation defect found after the pilot was fixed separately; the pilot used immutable text and was unaffected. Both datasets were subsequently registered, with adjusted data linked to the raw parent. The explicit identity remains an unresolved provider ticker. An admission-boundary check returned `historical_admission_not_implemented` without calculation. Three exposure records cover the entire requested pilot range; event-chain verification passed. The private check record is `runtime/alpaca-registration-check.json`.

## D005 decision and review

D005 has five complete independently attributed adviser reports and an actual completed `claude-opus-5-5` critique, archived in `docs/reviews`. The Opus call cost $0.197620; total cooperating-project accounting was $0.562722 afterward. Runtime ledger is authoritative for new usage. Existing allowance remains USD 20 per America/Los_Angeles calendar day. No subscription purchases and no automatic paid retries.

Accepted constraints: submission hash before validation; verify actual bytes; preserve pending work; bounded explicit historical SIP and separate paper calendar routes; never turn raw/adjusted equality into proof of no actions. The whole pilot is development-only with unknown prior exposure. Protected final access, authentic worker separation, genuine five-role research and prospective paper evidence remain required.

Independent review identified loaded-code/default identity, mutable acquisition requests, pending CLI exit status, nested-transaction rollback, fresh example directories and bounded configuration-read defects. Corrections and exact inspected hashes are preserved in the final reports. Explorer/provenance outcomes now commit atomically, and persistent publication failures leave pending records without false success. The increment passed local review; the full operation remains incomplete.

## Website operation

LaunchAgent `com.ronoktanvir.quanto` runs at http://127.0.0.1:8766/. Controlled failure recovery and actual readiness were verified. Before a reload, inspect persisted restart history and the rolling-hour launch limit; never reset safety records. D005 does not change the serving code, so no reload is required.

The dashboard is a personal management workspace, not a landing page. It includes work, blockers, evidence, costs, conversations and a progress-linked DAG. Actual role/helper responses and an original-worker inquiry/answer were verified. Role chats are new contextual assistants, not the original workers. Original replies require actual native collaboration and recorded source attribution.

Background captures run every 300 seconds with last-attempt/last-success/next-attempt metadata. Two live captures were verified 303 seconds apart; subsequent captures continue. Capture/health timers never update research observation timestamps. Local sleep/logout/shutdown interrupt observation. Project files were marked Keep Downloaded after iCloud offloading stalled reads.

## Continuation

Check PR #3's final CI and merge state, completing that step if still pending. Refresh main before the next feature branch. Then implement supported historical-data admission and corporate-action accounting; protected evaluation/exposure access; searchable failure memory; actual five-role research and scheduling; paper operation and separately approved live readiness. Do not redefine these into a permanently synthetic system.

D004's detailed per-adviser archive remains incomplete. The original working conversation is evidence; never invent votes or quotations to fill the gap. Use `PYTHONPATH=src .venv/bin/python` for source commands if the editable install does not apply its .pth. Root-owned runtime observations should change only when actual work evidence changes.

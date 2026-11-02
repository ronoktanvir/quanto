# D008 qualified-context trace inspector preparation

**Disposition: prepared and fixture-verified for a separately authorized future inspection. No actual third workflow was run or inspected.** The new private inspector checks lifecycle, exact method/context lineage and current evidence availability. It cannot validate numerical results, certify a strategy or complete D008/R14.

Reviewer/preparer: `/root/d008_broker_critic`. Product checkpoint: `9edfa86ea37ec89616ee0218cb31ac187a78665c`. Owned outputs are only this report and the new ignored `runtime/d008/inspect-context-trace.py`. The existing inspectors and prior actual reports/traces remain unchanged. Preparation read product/test/governing source and only the two explicitly permitted runtime harness files: `inspect-revised-trace.py` and `verify-actual-workflow-v2.py`. No actual receipt, database, data artifact, environment file, credential, network service or paid workflow was accessed. Temporary invented fixtures were executed with an injected synthetic model transport.

## What the inspector checks

The inspector opens the supplied database with SQLite `mode=ro`, sets `query_only`, and holds a read snapshot. Its adapter exposes reads only; it never constructs a writable `Provenance` or `FailureMemory` service. Artifact reads reject tombstones, symlinks, nonregular/oversized files and hash mismatch. JSON rejects duplicate keys and nonfinite constants. Journal hashes and event ordering are recomputed. Receipt fields are compared with the retained parent artifact, whose parent outcome and registry/configuration/code identities are checked.

The qualified-context audit independently joins the original hypothesis assignment, query intent, fence and effect-start event to the registered basis. It checks that the basis begins after that exact effect, finishes before its binding event, and is never rebound. Each retained query must begin and finish strictly inside that basis interval. The exact authorized failure set remains private. Every packet binding checks assignment/role/configuration, suite/revision, packet, method proof, failure observation, original basis and exact nine-field facts. Observations must be prepared after assignment issuance and registered before binding; both proof and observation are one-use across the journal. Later packets require the same run's completed original query effect. The audit checks every binding event, including a binding without a published model stage.

The planned request ID joins the private binding to its actual hold, prepared request-body hash, intent and fence. Binding must precede budget authorization. Completed stages additionally check the reservation/purpose accounting relationship, bounded request, exact configured/observed model, actual-versus-synthetic transport evidence, private-response-derived projection, predicate continuity, handoff and publication. Costs are checked locally by exact request IDs; no global budget delta is attributed to this run and no amounts are printed.

The inspector retains the earlier exact comparison-parent-child, registration-before-computation, fresh suite and three unique successful child checks. It checks the selected allowed method predicate and exact derivative/source ancestry without emitting predicate truth, operands, numerical results or rationale. A stop must have no comparison link or financial-launch intent for that run. Unrelated concurrent calculations are not attributed through a global timestamp count.

Review summaries are independently derived from successfully published stages: no review roles means `not_reached`, an incomplete roster means `incomplete`, and all four roles are needed for `blocked`, `inconclusive` or `method_no_blockers`. A supplied receipt that disagrees with its retained artifact fails inspection. Historical receipts are not rewritten or reclassified.

## Current revalidation and its limit

A read-only adapter invokes the frozen production `revalidate_failure_context` for each bound observation. That rederives the exact basis snapshots, latest disposition identity, availability states and currently validated suite/admission/revision dependencies without a new query or write. Reusing this semantic validator is explicit shared logic, not an independent implementation of financial validation. Independent event joins and fixture attacks test its composition with the inspector.

Current revalidation describes inspection-time state. It cannot independently reconstruct all filesystem states at the earlier network send. A later disposition or availability change can make current revalidation fail while the retained lifecycle bindings still pass. The output separates `current_context_revalidation_passed` from `retained_lifecycle_checks_passed`; neither converts a historical refusal into correction, supersession or clearance. Content hashes and journal checks cover the cooperating application model, not a privileged owner capable of rewriting all artifacts and history.

## Output and execution boundary

Stdout and the new exclusive-create output contain only fixed check names/verdicts, counts, code/artifact digests, allowed role/model/decision/finding categories and lifecycle classifications. Private source IDs, failure IDs, response IDs, timestamps, financial values, raw rationale, evidence contents and predicate truth are not emitted. The inspected artifact set is represented by a count and aggregate digest rather than a list of source references. Exceptions produce fixed failure output, without traceback or private diagnostics. An existing output is never overwritten.

A stopped trace may have `observed_trace_consistent=true` while `all_checks_passed=false`: the seven actual-role/completion prerequisites are still unmet. A complete synthetic fixture also fails actual-model prerequisites. `operational_acceptance` and `numerical_validation_performed` remain false in every inspector output. A malformed, incomplete or unavailable trace remains failed/incomplete; the inspector does not retry or invent completion. Inspection requires explicit `--root`, `--receipt`, `--request` and a new `--output` path. No actual invocation is authorized by this preparation report.

## Executed fixture evidence

Final checks used newly created temporary roots and invented source/model fixtures; none used retained actual datasets. Before/after content hashes of every temporary fixture file matched around each inspection.

- Director stop, hypothesis stop, engineer stop and complete seven-stage synthetic workflow: all expected lifecycle/current-context checks passed. Synthetic model classification remained false for actual evidence; incomplete stops remained incomplete. Output omitted the private fixture rationale/detail sentinels and private submission/failure identities.
- Query-before-basis attack: swapped registration events in a copied temporary journal, then recomputed its hash chain. The inspector rejected the query interval despite valid chain hashes.
- Substituted failure-observation event: a rehashed binding pointing to another role's observation failed the exact binding check.
- Newly appended unresolved disposition with the same visible disposition string: the changed identity caused current-context revalidation refusal; no refreshed query was issued.
- Tombstoned original basis: inspection refused unavailable evidence.
- Receipt review label changed to `method_no_blockers` after a hypothesis stop: receipt-versus-record comparison failed.
- Malformed CLI input and a preexisting output path: both returned fixed failure results, printed no sentinel or traceback, and preserved the existing output bytes.

The final four lifecycle cases and six adverse/output probes passed on the pinned inspector bytes. Targeted Ruff passed. Product source/tests were not modified.

Preparation failures are preserved here rather than presented as successful first attempts. The first lifecycle pass found a missing `list_submissions` method in the read-only adapter and a fixture-classification assertion that incorrectly equated the synthetic model run with the child calculation's retained evidence label. Both inspector defects were corrected and all four cases rerun. The first adversarial harness mutation was blocked by the temporary journal's append-only trigger; only the copied invented database's trigger was removed to construct the attack. A later harness call used the wrong `append_disposition` signature and was corrected before that probe ran. The final six-probe execution passed. A system hash-command locale failure was replaced by Python SHA-256 computation. These were local preparation/harness failures, not actual workflow attempts.

## Exact inspected and delivered identities

| Artifact | SHA-256 |
| --- | --- |
| New `runtime/d008/inspect-context-trace.py` | `496e78b6b29d4bcb2867753af4fd99d589ecb2dffe88cf57d468f2000c3ffe2b` |
| Preserved `runtime/d008/inspect-revised-trace.py` | `5daddec045931a4d764acbe167b480fa31571fd45cee2710dea33c395d2d06af` |
| Preserved `runtime/d008/verify-actual-workflow-v2.py` | `d7cf5022ffd67168095f4720421c7ca30cd5ade6c8ae799bcfc69e0445444f6f` |
| `src/quanto/research_failure_context.py` | `b99af35355b14d638770c069791124a8d72774346e5a9677ac74d607bc777208` |
| `src/quanto/research_broker.py` | `aa4f9e93f9fc471273bf2e6c1a0d67acb74583228618cecd17aa9ec513419e34` |
| `src/quanto/research_packets.py` | `ead052fb0fe53576eff02a5f7138af16a58b70c0c5fbd164eb196f4af92e0a93` |
| Temporary lifecycle probe script | `d0c7f28326e9c3fb7568763577c6e400c2ff9e6d4d6ba6b87e20397a4a2a3c65` |
| Temporary adverse/output probe script | `ed53a96007f9a3a5af726435d975b1de8c162c92cefb1b824cb6815ff0dd5545` |

Actual use remains pending separate root authorization after integration. A completed future trace would still need the separate numerical/oracle verifier and independent quality/scope dispositions; no favorable model decision or inspector verdict closes the broader operation.

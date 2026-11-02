# D007 historical pilot: bounded independent quality check

Reviewer: independent native agent `/root/d007_quality`, 2026-11-02 UTC. This is a new metadata and harness review; it does not modify or replace the earlier independently executed software-quality report retained in the actual policy revision.

The sanitized pilot record and inspected harness control flow support the lead's claim that the bounded D006/D007 calculation, deliberate replay and independent numerical-comparison work completed. No blocking inconsistency was found. This reviewer did not inspect private market inputs or result values and did not independently rerun the actual comparisons; the reported actual outcomes remain lead-executed evidence, supported by the separately verified software boundaries.

## Exact review material

| Material | SHA-256 |
| --- | --- |
| `docs/reviews/D007-historical-pilot.md` | `de9cacf6caf47b4e3f7a7a4552d117319108a4af0968246fa04513e7df6e2fed` |
| `runtime/d007/verify-historical-pilot.py` (source only) | `68c08345ab6f5868a87960237fc76d2935e2dd59539815dc84930de6ec662d34` |
| `runtime/d007/run-reviewed-suite.py` (source only) | `b17cb4f7520fa7a5fa2d1fb34fcfcb9861f3d8ce3d78709f68c01bd3f9831cf1` |

The prior `docs/reviews/D007-quality.md` remains byte-identical at `f49673eb01b9add5bd079ca94c3a9296dd4614164928a39fa713a4518fe33646`. Its 808 tests plus 12 subtests in source and clean installed environments, lint results and independently written synthetic probes are separate earlier evidence. This check did not rerun those checks or expand their claims to investment performance.

## What the reported outcomes establish

The sanitized record reports successful registered admission and a complete suite containing the three predeclared costs, followed by a separate deliberate invocation. Each cost has distinct initial/replay attempt identities, while each pair has the same exact result artifact. The recorded initial/replay suite submissions are `bb8f173707db4438a389e37c7bab2cb0` and `53e0580818d24bc2a8780f342995e220`; the registered suite is `051c2c263e4d29b29243b4ee041c3aa0421451a344ba218363770a4aa4d73f96`.

The record reports 20 warmup sessions and 28 evaluation sessions for every scenario. The lead reports 294 oracle field comparisons per scenario, 882 overall, at relative/absolute tolerance 1e-28, all passing. Strategy and benchmark each report one split, one dividend accrual and one dividend payment. These figures are observations attributed to the lead's sanitized record, not values independently recomputed by this reviewer.

The record also identifies preserved earlier refusals, four predecessor plans, the additive policy change and derived change count of two. Those disclosures preserve the distinction between changing policy after seeing source metadata and discovering an error in the earlier refusals. Successful calculation does not retroactively invalidate either refusal.

## Harness inspection

The suite runner builds exactly the 0, 10 and 25 basis-point requests from the registered revision's frozen evaluation dates, lookback, thresholds and starting cash. It uses the successful admission's dataset/admission identities, registers the entire roster once and deliberately calls `run_suite` twice with that same registered identity. It stops if registration or either full invocation is unsuccessful. There is no parameter search, result-dependent cost selection or automatic retry loop in the inspected script.

The comparison harness requires both recorded invocations to be complete and successful. For each paired member it checks equal costs, successful outcomes, equal fingerprints and artifact identities, distinct submission/attempt IDs, and equality of retained result bytes. It obtains the selected input from that member's registered dataset's normalized-bars wrapper, includes the prior `lookback` sessions through the inclusive evaluation end, then checks the 48-session selection and exact timestamp alignment of its 28 evaluation rows with the strategy report. This matches the software's warmup/evaluation selection mechanism; it avoids accidentally comparing an oracle run over a different interval.

The oracle input combines that selected normalized input, the member specification, canonical actions embedded in the admitted result and the engine report being checked. The harness pins the oracle bytes to `54887dfae2f12430b5cdd9901c0c3ba367541f6eb4714b987ad68e08f0433ca1`, then invokes the local program with a 30-second limit. A comparison submission is begun before invocation. A nonzero exit receives a retained failed outcome and stops the harness; there is no unbudgeted model call or numerical retry. A successful returned verdict is retained, and the summary records all case identities and three distinct fingerprints. These are appropriate mechanics for comparing an unchanged independent numerical implementation against each retained result.

The inspected harness is a bounded local verification aid rather than an independently hardened receipt verifier. It pairs member lists with `zip` and relies on successful production suite construction for equal three-member rosters and common suite identity; the final three-distinct-fingerprint assertion alone does not independently prove those upstream invariants. It also trusts the pinned oracle's successful verdict to carry its comparison count and tolerance. The runner constructs the exact common roster and the previously validated production APIs enforce those invariants, so no observed outcome is contradicted. These reliance points limit what this code inspection alone certifies; they do not establish a missing actual scenario.

## Preserved failure and limits

The sanitized report preserves the initial payload-preparation failure as `2b89cc1a70ec4f7dadd8c46e48b4d7d6`: the harness expected a list instead of the normalized-bars wrapper and stopped before oracle invocation or another financial calculation. The final inspected code correctly reads `['bars']`. This reviewer verified the corrected access in code, but did not inspect the private failure receipt or journal. The claim that the failed preparation was retained and required no financial rerun is therefore attributed to the lead's record.

No permitted harness was executed during this review. No payload file, private source record, normalized market object, result table, runtime database, credential or `.env` was read. No new calculation, outside-model request, broker request or order occurred. Only this new review file was written; no production source was changed and no commit was made.

The actual numerical agreement supports accounting consistency under the accepted economic-share abstraction. It does not certify issuer/source truth, licensed use, emergency calendar completeness, point-in-time availability, settlement delivery, executable fills, protected holdout performance or strategy profitability. All acquired history remains development-exposed; the profile's origin in observed metadata and unresolved ancillary dates remain disclosed qualifications.

This bounded quality check supports closing the specified actual historical calculation/replay/oracle increment when the lead integrates the separate criticism and scope dispositions. It does not close protected evaluation, persistent research roles, failure retrieval, unattended research scheduling/restore, prospective paper operation, crypto support or separately gated execution.

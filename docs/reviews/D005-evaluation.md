# D005 independent evaluation adviser

Author: native adviser `/root/evaluation_adviser`. Recorded 2026-11-02 UTC. Perspective: research evaluation and adversarial statistical integrity. This is a design recommendation, not implementation certification or investment evidence.

## Recommendation

Build an auditable real-data explorer next, with common comparison windows, registration before computation, and explicit exposure records. Keep its results exploratory. Add a separate final-evaluation access gate before claiming protected evaluation. The owner's selected scope is both US markets and crypto, with US markets first; a convenient crypto test must not replace the US-data and corporate-action work.

The decisive distinction is between reproducibility and an uncontaminated test. Hashes can establish which inputs produced a result. They cannot establish that the researcher had never seen the period, that every prior trial was recorded, or that repeated selection on that period was statistically harmless. More trials can produce impressive selected results without improving the underlying rule; the relevant research literature explicitly examines this selection problem. [Bailey et al., The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)

## Observations from the current implementation

- `Journal.register_experiment` fingerprints supplied specification, data identity, code identity, evidence kind and assumptions. It does not verify that those identity claims match actual bytes. Attempts and one terminal outcome per attempt are append-only through the application.
- `run_demo` records an attempt before invoking the engine, but its `StrategySpec` and bars are constructed before that record. This demonstrates valid synthetic execution; it does not establish that invalid user submissions or every alternative trial enter the journal.
- `run_backtest` reports `unprotected_not_implemented`. It has no split, study-family, final-evaluation release or exposure registry. It also leaves source rights, corporate-action absence and actual availability times to its caller.
- Evaluation starts after `spec.lookback` supplied bars. Running different lookbacks over the same full series therefore changes the evaluated dates and the benchmark's entry date. A parameter search must first fix common evaluation dates and give each candidate exactly its required preceding warmup slice.
- `record_review` rejects identical supplied producer/reviewer names, but names are caller assertions, not authenticated independent identities. The ledger's documentation accurately limits its tamper claims.

Inspected SHA-256 identities:

| Source | SHA-256 |
| --- | --- |
| `src/quanto/research.py` | `186e6a9aa95a484e94d71cbd71f276c053b923e96e030fa6eea0adcfc53223ca` |
| `src/quanto/ledger.py` | `29c3f14bdae924b4d369b49b59c3ec7e5079810d76e55992fa1800d49a3da6cf` |
| `src/quanto/cli.py` | `fc31330987d030faab498baad506dc88ff00d97e0f6b195de65caca2bf4d441e` |

## Gates for the next increment

1. **Record a submission before semantic validation or computation.** Persist a bounded raw-request hash, request ID, actor, requested evidence kind, and submission time. Then record parsing/validation rejection, data-acquisition failure, accepted candidate, execution failure or completed result. A rejected malformed specification cannot require an already valid experiment fingerprint; use a submission record that can later link to an experiment. Do not record credentials or unbounded raw requests.
2. **Freeze verified inputs.** Bind the accepted candidate to canonical specification bytes, source and normalized-data hashes, acquisition manifest, parser version, expected calendar, price basis, corporate-action treatment, code-content hash, dependency lock/runtime identity, costs and benchmark rules. Read the actual content and verify its hashes before computing. A Git commit alone is insufficient when local code is dirty. New data revisions or repairs receive new identities and explicit parent links.
3. **Freeze a common comparison interval.** Store inclusive evaluation dates separately from warmup dates. A longer lookback gets more earlier data, not a later benchmark start. Reject insufficient warmup and unexplained missing sessions. Use only information available before each decision; do not fit preprocessing on the final interval. Record any position carry/reset rule at window boundaries because it changes the experiment. The current engine starts each run in cash, so that behavior must remain explicit.
4. **Register each candidate and execution attempt.** A parameter variant, changed rule, changed cost assumption or other choice informed by results is a new candidate with ancestry and a reason. A retry of identical frozen bytes is another execution attempt, not automatically an independent statistical trial. Preserve failed, invalid and rejected outcomes and distinguish candidate count, execution count and selection events. Expose these counts beside the selected result.
5. **Publish only reconciled results.** Save content-addressed output, verify its bytes, and bind the terminal journal outcome to that artifact. If jobs use leases, publication must validate the current fence in the same transaction as accepting the outcome. A stale worker cannot publish success. Recovery must reconcile incomplete attempts and orphaned artifacts, not silently overwrite them or invent success.

For US markets, an empty corporate-action list is not evidence that no event occurred. The acquisition acceptance record needs supported treatment or affirmative evidence covering the requested period; otherwise reject the financial calculation or explicitly restrict it to a data-inspection artifact. The current engine's exact execution availability, liquidity and slippage limits also prevent an execution-readiness claim.

## Protected evaluation requires an additional boundary

Create a stable research-campaign/study lineage distinct from an experiment fingerprint. Changing a parameter, dataset revision, filename, code hash or study label must not manufacture an unseen period. Record exposure against underlying instrument/venue/time coverage, dataset ancestry, campaign and related studies, with exact-byte hashes as supplementary identities. Overlap matters even when the downloaded bytes change.

Use a development region for repeated exploration, predeclared chronological validation windows for selection, and a separately declared final interval. Freeze the candidate set, selection rule, metrics, benchmark, costs and acceptance criteria before final access. Learning new choices from the final result makes subsequent evaluations on that information exploratory, even if the developer calls them a new study. Do not choose a universal split year or an arbitrary minimum sample that is then presented as statistical adequacy.

The evaluator should durably record `final_access_authorized` before releasing final bars or computing any final-derived output. An interrupted or uncertain access stays consumed; failure does not reset the holdout. Recovery may reproduce the same frozen computation under linked attempts, but must not grant a new claim of unseen evaluation. Raw bars, summary metrics, charts, logs, chat context and quality summaries all need consideration as exposure channels. Deterministic validation may read final data without showing it to a strategy-producing agent, but that separation must be real and documented.

Initially describe this as **application-tracked exposure**, with `prior_exposure_unknown` where appropriate. Historical market periods may already be familiar to the owner or represented in model training. Prospective paper observations after an actual freeze can strengthen the evidence later; they do not repair undocumented historical exposure.

## Verdicts and statistical claims

Keep software completion separate from research validity. Appropriate immediate labels are `invalid`, `failed`, `exploratory_result`, and `insufficient_evidence`, with explicit evidence kind and limitations. Later, `final_evaluation_completed` and `predeclared_criteria_met/not_met` can describe the protocol outcome. Do not equate beating a benchmark on growth and Sharpe with a demonstrated investment edge; likewise, failure to detect an edge does not establish that no edge exists.

Do not bolt an automated Deflated Sharpe Ratio onto an incomplete search history. That method addresses selection bias and non-normal returns, but its interpretation depends on the relevant trial and return assumptions. Preserve the candidate return matrix and selection history first; add an independently checked statistical implementation later. [Bailey and López de Prado, The Deflated Sharpe Ratio](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)

Required regression cases include invalid submission retention; changed bytes under the same claimed identity; common strategy/benchmark dates across lookbacks; future-bar perturbations leaving earlier signals unchanged; related-study and revised-data exposure inheritance; crash after final-access authorization; stale-worker publication rejection; and recovery that preserves failed attempts and prior exposure.

## Tradeoff and objection

This design adds bookkeeping before it adds impressive performance metrics. That is the appropriate tradeoff: otherwise the first real-data explorer can create undocumented selection history that a later holdout feature cannot undo. I support implementing acquisition/provenance and the auditable explorer now; I object to calling it a protected research system until the additional access boundary and exposure tests exist.

With one administrator and agents sharing files, the system cannot prevent direct data reads, altered code, deleted/rebuilt databases, fabricated reviewer names, unrecorded external studies, or use of prior knowledge. Local hash chains do not defeat an administrator rewriting the whole chain without an external checkpoint. The enforceable claim is cooperation with the recorded workflow. Stronger claims require actual worker/access separation, trusted checkpoints and explicit threat-model evidence, not additional prompt wording.

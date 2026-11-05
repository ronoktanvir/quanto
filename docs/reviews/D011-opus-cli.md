# D011 Opus CLI critique

Actual responding model: `claude-opus-5-5`. One signed-in local Claude Code turn completed on November 4, 2026 (Los Angeles), with exit 0 and an accepted terminal. The reviewer received the complete proposal and attributed lead summaries of five independent perspectives, not full reports, implementation or private observations. Packet SHA-256 `29c52dc46c15b8a04757be40142a0dcdb1a84cb73529cff11f1e3ecc9e42bac7`; visible response SHA-256 `a574d722baa70ebeb4cd5a21c6bead6cf4cd69e7180433a34b3b76e24afe1b35`. Tools, MCP, fallback and retries were disabled; available terminal counters reported no tools/subagents. This is observed terminal evidence, not privileged process attestation.

The CLI estimated USD 0.118872; the full USD 0.60 reservation remains uncertain because provider billing is unreconciled. Outer process handle 90287 completed in terminal chunk `c9ede7`, exit 0. The invocation is consumed and cannot be retried.

## Full visible response

# Independent critique: D011 finite strategy research campaign

**Basis:** This review covers only the proposal text and the lead-written adviser summaries. I have not inspected code, full reports, private data or results. Nothing here certifies performance or authorizes execution, disclosure or a broader scope.

## Overall judgement

The staging is sound. It separates a descriptive development screen from any later protected or future evaluation, it refuses to "reset" exposure, and it allows a no-candidate result. That preserves the owner's demand for after-cost and unseen evaluation without pretending this session can meet it. Several remaining degrees of freedom could still quietly turn the screen into a search. These are listed below.

## Consequential objections and smallest fixes

1. **The cost case is an unbound selection axis.** The proposal has three candidates and three cost cases, and the selection rule picks one candidate. It does not say which cost case governs selection.
   - **Fix:** In the manifest, name one governing cost case, ideally the middle or a stressed one. Treat the other two as sensitivity reporting only.
   - Selection must not depend on a candidate "winning" under any one case.

2. **Instruments silently multiply trials.** The trial cap counts candidates × costs, but "mechanical instrument choice" could cover several ETFs.
   - **Fix:** State the instrument count explicitly. Make the trial maximum equal candidates × costs × instruments.
   - If the screen uses more than one instrument, the selection criterion must say how it aggregates across them.

3. **ETF capital-gains distributions may cause outcome-dependent substitution.** The data adviser notes these distributions are retained but not admissible. Failing closed is correct. Choosing a different instrument after a refusal would be selection on admission outcome.
   - **Fix:** Freeze the instrument rule before acquisition. Record a refusal as the campaign's empirical result, with no fallback instrument in this campaign.

4. **Warmup and identical scoring sessions.** "Identical scored sessions" only holds if every variant's first scored session follows the warmup of the slowest lookback.
   - **Fix:** Derive the common scoring start from the maximum lookback in the manifest.
   - Score the benchmark over the same sessions, as a continuous trace, with the same entry-fill cost.

5. **Zero-interest cash biases the two sides differently.** A long/cash rule sits in cash often, so a zero cash rate penalizes the strategy. Meanwhile, holding benchmark dividends as idle cash penalizes buy-and-hold.
   - **Fix:** Report both biases next to the results and state their direction.
   - Forbid describing the comparison as "conservative" without that qualification.

6. **"Indistinguishable" is undefined in a descriptive-only stage.** With no inference allowed, "favor simpler when indistinguishable" becomes a judgement call made after seeing the results.
   - **Fix:** Predeclare a numeric tolerance and the simplicity ordering, for example a fixed lookback ordering.
   - Predeclare the no-candidate condition, such as failing to beat the matched benchmark under the governing cost case on the stated measure and a drawdown bound.

7. **Block naming invites later misuse.** "Later historical-assessment block" will be read as a holdout. Each lookback is also plausibly anchored on published in-sample work (for example Faber) over overlapping history.
   - **Fix:** Label all three blocks "development A/B/C" in schema and UI. Record each lookback's provenance in the manifest.

8. **Summaries can leak private parameters and spread exposure.** Turnover, trade counts and exposure fractions can reveal lookbacks. Showing results to agents or the council that later propose new families makes that knowledge development exposure.
   - **Fix:** Define the "approved summary" fields in advance and run a leakage review against the private parameters.
   - Log every context into which results were injected as an exposure event, carried forward to D008 scope reconciliation.

9. **Crash recovery and verification could become replays.** Refusing duplicate invocation is right. Independent reconciliation must not mean re-executing the run.
   - **Fix:** Verify by recomputing arithmetic from stored fills, cash and claims records only.
   - Give uncertain slots a terminal "uncertain/consumed" state with no rerun path in this campaign.

10. **Fill realism.** Daily bars do not show executable opens, and gap days concentrate cost.
    - **Fix:** In the cost-stress output, report the per-fill cost needed to erase any advantage over the benchmark (breakeven cost). This is more informative than three fixed points.

11. **Future-interval power.** A slow trend rule may trade a few times a year, so a short frozen future window will likely be inconclusive.
    - **Fix:** Before freeze, the future plan must show a calculated sample and duration at an effect above the worthwhile threshold, plus fixed release dates. "Inconclusive" must be declared a legitimate pre-registered outcome.

## Acceptance conditions

**Development screen, achievable now:**
- The manifest is frozen before acquisition and includes the governing cost case, instrument count, trial cap, tolerance, selection and no-candidate rule, block labels, and lookback provenance.
- The output is one of two things:
  - a complete table of all candidate/cost/instrument traces plus matched benchmarks, with every failed or unattempted slot shown; or
  - an observed admission or data refusal, recorded without substitution.
- Independent reconciliation is performed from stored records.
- The schema enforces `investment_validation=false` and `protected_evaluation=false`.
- The direction of the cash and dividend biases is disclosed, along with breakeven cost.
- The approved-summary leakage review is complete and the exposure log is updated.

**Later protected or statistical acceptance, not achievable in this session:** Either D008 scope reconciliation has passed with an isolated evaluator, or a precommitted future interval has been fixed. In both routes the following must be fixed before observations exist:
- the estimand, using paired net strategy-minus-benchmark returns;
- the worthwhile-effect threshold;
- the dependence model;
- calibrated uncertainty;
- power at an alternative above the threshold;
- multiplicity, counting all logged trials;
- the stopping and release rule.

Any ambiguous access consumes the evaluation. Model prior knowledge remains a stated limitation in either route.

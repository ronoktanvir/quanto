# D011 data and exposure feasibility

**Start a small, preregistered historical development screen while completing the separate evaluator boundary.** The current software can acquire and admit new historical inputs and compare supported rules under fixed cost scenarios. It cannot truthfully certify an untouched holdout: `Supervisor.reserve` is preparation-only, `protected_acquire` always refuses, and the existing production history remains `legacy_unknown`. A fresh download, renamed ticker, revised dataset, or new workspace does not remove previous exposure.

Reviewer: `/root/queue_data`, independent data perspective, 2026-11-04. Inspected public source and records at root revision `60fe9299ab44cbd34962944fcc8039f1376435da`. The nine source files identified below are byte-identical in the research worktree at `94e0df5a79234f3423cabe137377efb796fe9cd0`. No private runtime, raw historical data, credentials, control database, actual strategy results, model dispatch, acquisition, or experiment was accessed or executed. No tests were run. This is a design recommendation, not operational acceptance. The unfinished D010 work is outside this report.

## What “unseen” can mean

| Claim | Evidence needed | Current applicability |
| --- | --- | --- |
| Newly downloaded | A new retrieval receipt and exact returned bytes | Establishes retrieval time only; may contain familiar/revised history. |
| Chronologically withheld from fitting | Rules, parameters, universe, costs and selection process frozen before evaluating later dates | Useful historical screening if faithfully recorded; does not establish that researchers or model training never encountered the history. |
| Protected from this research process | Reconciled exposure inventory, reserved scope, enforced access separation and controlled release | Not implemented end to end. Unknown prior exposure prevents certification. |
| Future prospective evidence | A timestamped freeze before the observations occur, then time-ordered collection and evaluation | The strongest available fallback against historical prior knowledge, but requires elapsed market time. Visible paper observations count as development exposure under D008. |

An unseen historical interval is a claim about a particular research process, not about the public world or a language model's training corpus. Even an enforced local holdout cannot establish that a model has never encountered public market history. A prospective frozen test reduces that uncertainty; it cannot produce months or years of evidence immediately.

## Existing route and its limits

1. `cli.main` installs the existing trusted workspace session, then routes `acquire-bars`, `acquire-calendar`, and `acquire-actions` to the guarded adapters. Direct calls still require `current_session`; no new blank control store should be created to bypass the established history.
2. `alpaca_data.acquire_bars` fixes daily SIP, USD, and `asof=-`; the normalizer allows raw or fully adjusted observations. Completed-day requests, pagination, bytes and runtime are bounded. `acquire_calendar` retrieves the matching session calendar. Actual entitlement must be observed; documentation alone is not account permission, and failure must not trigger a silent feed substitution or subscription purchase.
3. `alpaca_actions.acquire_actions` retains all action categories and incomplete records over an explicit process-date envelope. Acquisition alone is inspection-only. The current admission profile requires raw bars, matching calendar coverage, source identity/continuity judgments, corroborated action economics, and a source-use review. Its action request spans the existing profile's full process envelope through acquisition time; that is not proof of complete economic history.
4. `explorer.register_dataset` records the **full acquired envelope** as development exposure, including bars outside the scored slice. `admission.admit_dataset` then decides whether this specific raw-event dataset is usable. `study_suite.register_suite` and `run_suite` register and execute the complete cost roster. Every failed, refused, uncertain and completed attempt must remain in the journal.
5. The current event engine supports a single-security, long/cash SMA-level rule with completed-close signals and next-open modeled execution. It reports `unprotected_development`. Volatility targeting, multi-asset rotation, mean-reversion rules and richer execution are additional implementations, not existing capabilities implied by the formula sheet.

The Alpaca [bars reference](https://docs.alpaca.markets/us/reference/stockbarsingle-1) confirms that `asof=-` disables historical symbol mapping and that `all` applies multiple corporate-action adjustments. The [corporate-actions reference](https://docs.alpaca.markets/us/reference/corporateactions-1) describes process-date bounds and warns that records may arrive late. These semantics support preserving the current explicit identity and action qualifications. They do not establish point-in-time availability or complete delisting coverage.

## Two data issues that would otherwise invalidate the queue

**ETF distributions need explicit support.** The action adapter retains capital-gains distributions, but `admission._actions` accepts only the currently supported splits and cash-dividend semantics when relevant. Do not discard an ETF's unsupported distribution to make admission pass, count every distribution as an ordinary dividend without evidence, or replace raw bars with fully adjusted bars inside the raw-event engine. Freeze a mechanical universe and eligibility policy before looking at performance, retain each excluded instrument and reason, and qualify any results as conditional on that universe. Selecting currently surviving ETFs does not establish a survivorship-free stock-market study.

**A daily bar open is not a proven achievable opening fill.** The provider describes bars as trade aggregates governed by trade-condition rules in its [market-data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq). The current engine itself discloses unverified exact availability and no spread, impact, liquidity, tax or interest model. Fixed fees are useful stress scenarios, but do not independently calibrate implementation costs. A strategy passing the existing three scenarios should be described as passing those modeled costs, not all real trading costs. The evaluation/cost reviewers should specify additional spread/slippage and timing stress before a stronger claim.

## Minimum route to an honest reserved evaluator

**Reconcile scopes, not a global “clean” boolean.** Add an independently reviewed, append-only reconciliation product that binds the existing store identity and journal boundary to prior normalized acquisition requests, emitted/started/uncertain pages, imports, publication lineage, aliases, classifications and explorer exposure. Use metadata where it is sufficient; an authorized reviewer must handle ambiguous content without exposing candidate-final observations to selectors. Record known intervals and unresolved scopes separately. Unknown history remains conflicting, and new activity after the inventory boundary must be included or fence the inventory. Original records and the historical legacy marker remain intact.

A particularly concrete obstacle is `Coverage('actions')`: its dates must be unknown, so a completed action query conservatively overlaps every date for the resolved security. Unknown imports can be global. Merely choosing later bar dates therefore does not establish non-overlap. A narrower reconciliation requires evidence for the actual information envelope of each retained observation and uncertainty, not treating process dates as economic dates. If that evidence cannot bound an old scope, use a declared future campaign boundary and a separately reviewed rule for genuinely future, not-yet-existing observations; do not silently clear the conflicting record.

**Keep the evaluator physically separate and deployment-bound.** Its private store and acquisition process own protected raw/partial responses, admission, diagnostics and detailed results. Candidate selectors, ordinary `Provenance`, the dashboard, model packets and development artifacts must have no supported access. The trusted deployment inventory must include ordinary CLI/import/refresh routes, administrative capture/restore, direct database readers and other workspaces. A new directory alone is not proof of isolation or absence of earlier exposure. Shared-owner filesystem access remains a disclosed threat-model limit.

**Freeze before the first protected effect.** Bind candidate/code/dependencies, mechanical universe/window selection, warmup, final dates, benchmark, costs, rights, selector/reviewer principals, statistical plan and release policy. Commit a one-use consumption record before acquisition or protected reads. Failures and unknown outcomes consume the opportunity; retuning or changing the dataset does not restore it. Protected data reviewers cannot later select candidates for that reservation. Retain the D008 outcome-independent integrity receipt for an access-control pilot; releasing final numerical performance requires its own approved campaign disclosure contract.

These are accepted D008 requirements being completed, not reasons to delay ordinary supervised development tests. D010 client retrieval and completed external backup are not prerequisites for a manually supervised, development-only screen. External checkpoint/restore remains a requirement before unattended research; no real project upload is proposed here.

## Recommended immediate sequence

1. Freeze a finite development candidate roster, universe-selection rule, chronological slices, common scored dates, benchmarks, costs, rejection rules and trial accounting before retrieving broader inputs. Keep final candidate parameters private.
2. Acquire only the declared development envelope through the existing authorized route. Admit each dataset, retain every failure, calculate the complete cost roster, and independently recompute results. Report later-period screening as unprotected historical development unless stronger exposure evidence exists.
3. Implement and test scoped reconciliation plus the separate evaluator on invented inputs. Test overlap races, aliases/revisions, action-date ambiguity, global unknown imports, partial-page crashes, accidental dashboard/model disclosure and failure consumption.
4. After exact-build independent acceptance, freeze a single protected campaign. If existing historical non-exposure cannot be established, preregister future observations and wait for sufficient evidence. A short future run is operational evidence, not a substitute for a statistically adequate horizon.

The immediate useful answer is which candidates fail data admission, accounting checks, modeled costs or the declared chronological screen. The stronger answer—what holds up on protected or prospective observations—must remain pending until those observations and controls exist.

## Inspected source identities

| Source | SHA-256 |
| --- | --- |
| `src/quanto/evaluation_registry.py` | `c69c7de7e66c0d6f8b372304db482bf6d83ad0fe35960e55fc8fa00ac4a4b113` |
| `src/quanto/alpaca_data.py` | `752dad50e4aceeda0e367dfc449715663fd5c8967980d787065411f69004a8fb` |
| `src/quanto/alpaca_actions.py` | `63219d3c9b2ff03855821a794341c03b95ab74af1cad2b5959f01326dc8b4715` |
| `src/quanto/admission.py` | `5b1d5aa7d9aea6488ba96ac8a89a597d37e78ad28be0175699f6032abb8787c1` |
| `src/quanto/explorer.py` | `5bf8768505b02691aba5c321d70c8f62dddac3e4bbd5be31c983f2f43a23832a` |
| `src/quanto/event_engine.py` | `cb1a61985ebb08089eab50d00d1e78f09a83fdea6754587af7e871e177175ffc` |
| `src/quanto/cli.py` | `69b4301ab74530659d5433967512bbf3cbaf423f9c96d8f6e1fd2c91a4c6f02d` |
| `src/quanto/provenance.py` | `c765ffdfbbaeed019b82552a2ad97b1ebf14699960582600ca372996e661f5f9` |
| `src/quanto/study_suite.py` | `c3e552ef9998e72ae6f69b55bf43750d51f94522faf98a26ecbb624042f46360` |

Entry points inspected: `evaluation_registry.py:224,443,487`; `alpaca_data.py:37,555,677,682`; `alpaca_actions.py:200`; `admission.py:600,748`; `explorer.py:201,262,515`; `study_suite.py:147,352`; `provenance.py:359,411`; `event_engine.py:156,305`; `cli.py:81`. Source inspection establishes these implementation observations, not successful runtime behavior of a new campaign.

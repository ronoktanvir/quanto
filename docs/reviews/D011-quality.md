# D011 independent executed-quality review

**Result: passed for the bounded, supervised development-screen implementation identified below, after the critic's deadline defect was fixed and independently rechecked.** This review's initial checks did not exercise the slow-guard defect; the final checks cover it and additional expiry boundaries. This is software evidence from invented inputs, not an executed historical screen, a protected evaluation, or evidence of investment performance. Source criticism, scope acceptance, concrete campaign freeze, and actual acquisition/admission remain separate gates.

Reviewer: native agent `/root/queue_quality`, independently assigned the executed-quality role. The reviewer did not author or change producer source or producer tests. Review completed at 2026-11-05 04:47 UTC (November 4, America/Los_Angeles). The resident checkout was `/Users/ronoktanvir/.codex/worktrees/strategy-research/quanto`; final observed Git base was `433021d781a824d4e58bdf81725dab790dcd2add`, with the implementation below still uncommitted. The earlier cloud-stalled checkout and production runtime were not opened.

## Exact artifacts

The following source hashes were checked before the final run and confirmed afterward. These hashes, rather than an anticipated integration commit, define the reviewed implementation.

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/research_campaign.py` | `b0475711c2215e561e29e77f831b63205897779b07c35bad4362ad1d383bd8fa` |
| `src/quanto/research_metrics.py` | `58f9300bc7c3d18d8bd82bc5467fdc1f1d7f557aa29e7f8d4a009e64ce7e11d5` |
| `src/quanto/provenance.py` | `37f8e2130effcaf81e74bd1e4c762120a71a029b2be9b8b6736746614590f565` |
| `src/quanto/explorer.py` | `d63098279cc2487efbcc73dd2c09292ff92485e33215757307fa79dc552ceb2b` |
| `src/quanto/cli.py` | `354babf8b51b5027819c9487e82bca51ba7150848a881786cd788140d0f5264e` |
| `tests/test_research_campaign.py` | `3eef645844a3dbff9e8f8f715dacdbdd9ca80cd410eec7c186c24f73bf443ade` |
| `tests/test_research_metrics.py` | `7d9f2726606958c342816c83037e10d6e0c8eab3bfcc246fd43806e7aaa14cbf` |
| `tests/test_cli_requests.py` | `db6d03fb59039ede81147d067f5c7e22e31632a2bbeeb3ec50ae987e626d744d` |
| `tests/test_explorer.py` | `19bc5ec0d0a34d8cda3b4ef3c167de95c43fb4a7b08dcd5bfe96ee19f459fda5` |
| `tests/test_provenance.py` | `0c80bd13a63aeeb1d22e5e9dd77be528004f684b3ee53cbb0dad5614b040f88d` |
| Reviewer scratch `runtime/d011-quality/test_independent_quality.py` | `24f8ece1c62066dcb72ae1fc849d315543e155ff2354537ac83d919bd55093eb` |

The scratch probes and invented stores remain ignored local artifacts. Their digest identifies the executed reviewer checks; it does not imply that a fresh checkout contains them. Producer tests are retained in Git. The reviewer changed only this report and the ignored scratch directory.

## Executed checks

All commands ran from the resident checkout using the existing Python environment. No provider or model call was made, no credential was read, and no actual market observation was opened. Campaign fixtures used the explicitly synthetic supervisor and existing fake-transport input factory; these fixtures exercise acquisition-shaped records without acquiring anything.

The broad focused command was:

```sh
PYTHONPATH=src:tests /Users/ronoktanvir/Documents/ChatGPT/quanto/.venv/bin/python -m pytest -q tests/test_research_metrics.py tests/test_research_campaign.py tests/test_cli_requests.py tests/test_explorer.py tests/test_provenance.py runtime/d011-quality/test_independent_quality.py --basetemp=runtime/d011-quality/final-scratch
```

**Observed terminal result: 188 passed in 15.43 seconds, exit 0.** This included 180 producer checks independently executed by this reviewer and eight independently written scratch probes. It ran against campaign SHA-256 `1a6a7f9c4cca40fb9c7f64b3828f2d6958b55c17c39f490a4b86002d22e9e1fc`, before the deadline correction. An earlier 171-test focused run and an earlier eight-probe run also passed. A source-hashing attempt using `shasum` failed because of the terminal locale; Python `hashlib` was then used successfully. No hash is inferred from the failed command.

The critic then reproduced two failures not covered by that suite: a slow per-slot guard could let a dispatch start after expiry, and a slow final guard could allow a success result after expiry. After the producer added deadline checks around guarded and publication boundaries, this reviewer reran the affected campaign suite and all independent probes, including three new exact-boundary expiry cases:

```sh
PYTHONPATH=src:tests /Users/ronoktanvir/Documents/ChatGPT/quanto/.venv/bin/python -m pytest -q tests/test_research_campaign.py runtime/d011-quality/test_independent_quality.py --basetemp=runtime/d011-quality/deadline-scratch
```

**Final observed terminal result: 47 passed in 21.95 seconds, exit 0**, against the final hashes in the table. This includes eight producer expiry cases and three independent time-boundary cases. Afterward, all source/test hashes were compared with the earlier run: only the campaign module, its test file, and the independent scratch probes had changed. The unchanged metrics, explorer, provenance, and CLI results remain applicable; they were not redundantly rerun.

The independent probes establish the following limited claims:

- **Known wealth and costs:** a hand-derived buy at 120, sale at 105, and reentry at 115 reconciles ending value at 125, all three per-fill fees, and traded notional against exact `Fraction` calculations. The open terminal position receives no invented liquidation or exit charge. Recorded fills occur one session after their signals; the matched benchmark buys only once.
- **Long continuous trace:** 900 scored invented sessions, with separate open/close prices and three 300-session blocks, reconcile mean return, sample standard deviation, unannualized daily Sharpe, maximum drawdown, and the declared calendar-label CAGR proxy against independent standard-library arithmetic. Block boundaries use preceding portfolio value; block trade counts and fees sum to the full trace.
- **Future invariance:** appending 150 extreme future prices leaves all 438 previously scored rows, prior trades, and a fixed earlier block unchanged. This tests the covered engine/reducer path; it does not establish point-in-time cleanliness of a future real dataset.
- **Claims across blocks:** an invented dividend claim survives a sale, remains in wealth, becomes cash on its payment date, and supports subsequent reentry without resetting the portfolio at a block boundary. The checked block endings are 1000, 910, and 910 from starting cash 1000.
- **Refusals:** inconsistent returns, mismatched timestamp alignment, same-close fill labeling, nonfinite quantities, and a trace exceeding 10,000 rows refuse. Bounded malformed, duplicate-key, and nonfinite request text is retained as invalid for all three campaign lifecycle operations. Oversized request text refuses before dispatch; this is not claimed to create a retained experiment record.
- **Finite consumption and receipts:** a complete three-candidate/three-cost fixture yields nine children and nine claims. Two repeat run requests produce `campaign_already_consumed` without adding children or changing inspection. A retained successful child cannot satisfy a later claim for the same slot or a different cost slot.
- **Selection:** an exact return advantage of `0.00000000000000000000000000000001` outranks lower turnover; exact growth ties use fewer trades and then candidate identifier. Favorable assessment and nonprimary-cost figures do not change selection. An interrupted primary comparison produces no selected candidate.
- **Deadline boundary:** using a controlled clock and real invented-data children, completion at 299.999 seconds can proceed, while completion at exactly 300 or 301 seconds produces an interrupted campaign. The completed child remains recorded; later slots stay unattempted, no campaign summary is returned, and the consumed campaign cannot rerun. The producer cases separately cover expiry during per-slot/final guards, claim commit, dispatch, metrics, selection, summary writing, and final ledger publication.

The independently rerun producer coverage additionally exercises raw-price/action admission, source invalidation before and during the campaign, pending/unattempted slots, fixed error messages without private exception echo, loaded code/global changes, required bounded design metadata, malformed CLI recording, finite large JSON, ordinary one-MiB JSON refusal, access/tombstone enforcement, and a 4,000-bar invented explorer result exceeding the ordinary JSON limit.

## Qualifications and remaining evidence

These checks support proceeding to a supervised development screen after the other independent roles accept the same build. They do not complete that screen. Acquisition may still refuse; a refusal must remain the outcome rather than trigger an unregistered replacement instrument, period, feed, or rule.

The reducer validates the scalar fields it consumes. It is not an independent replay of every corporate action or a proof of source rights, provider completeness, calendar correctness, or exact execution availability. The campaign relies on the existing admission and authority controls for those boundaries. Authorization and loaded source identity are the critic's separate review remit.

The statistics remain descriptive. CAGR uses the documented inclusive calendar-label duration proxy, not exact execution instants. Daily Sharpe uses a zero reference rate and a sample standard deviation; it is not annualized and has no confidence interval. `traded_notional` and trade counts measure activity here; no standardized annual portfolio-turnover rate has been established. Fixed fees are assumed scenarios, not calibrated opening execution costs. The tests therefore cannot support an edge verdict, a profitability claim, or a claim that the assessment block was unseen.

The local deadline prevents new dispatch and accepted campaign publication after the checked boundaries. It does not preempt an in-flight calculation or a blocked dependency call; the supervising process still needs the separate hard deadline specified by D011. The controlled-clock tests exercise decisions without waiting 300 wall-clock seconds.

Actual historical values require independent arithmetic reconciliation after the frozen campaign runs. Protected or prospective evaluation, statistical uncertainty, final release, unattended operation, and live trading remain incomplete and outside this quality acceptance.

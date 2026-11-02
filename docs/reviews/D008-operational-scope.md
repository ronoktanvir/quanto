# D008 first operational attempt: no-drift review

**Disposition: retain and classify this as an actual stopped-workflow attempt, not an accepted five-role historical workflow.** The separate quality and criticism reports describe three actual `claude-haiku-5-5` responses: director `proceed`, hypothesis `propose` with `cost_ending_equity_nonincreasing`, and engineer `stop`. The stop prevented all financial work. The reports record $0.009116 settled, zero financial launch intents, zero new suite/child attempts, zero numerical or oracle checks, and no critic, operational-quality, or operational-scope stages. R14 and the bounded successful-cycle requirement remain incomplete.

Reviewer: `/root/d008_scope`. Repository revision inspected: `2dd9ab00fc7c9b6354ca409bba4bd51d7a890d0f`. Scope review is limited to public source and documents. I read the operational quality and critic reports, current public workflow/status/requirements/handoff/context/decision/roadmap documentation, and the source files listed below. I did not access runtime records, environment files, raw data, credentials, external services, or tests; I ran no checks, paid calls, or research attempts. The actual outcome is attributed to the separate reviewers' retained evidence, not independently verified by me. This disposition applies to the observed, pre-correction source and stopped trace; any later prompt/schema/code correction cannot retroactively change what the three models received.

| Artifact | SHA-256 |
| --- | --- |
| `docs/reviews/D008-operational-quality.md` | `7b2a13e5c8a96b3544408eb0dfd485720f0525d8f2414ae4e6e61ff007d5a838` |
| `docs/reviews/D008-operational-critic.md` | `9dd3d69a8f5d31935a3be8a5c100437d88c4283d3851c147e39e827f2f9c8728` |
| `docs/RESEARCH_WORKFLOW.md` | `4efc2d9445e9a73f922ae94bc528cc2e161b90cdf8ffc28ddb27fd8f4688071c` |
| `docs/STATUS.md` | `fd9c0f72eff37956bf0da1fe1b277744797828785ab339de90e6391d544f6f8a` |
| `docs/HANDOFF.md` | `3865019abb9771be6079f638a970016376d377e30e0534aa3ffe0fcd2bfc9a7d` |
| `docs/REQUIREMENTS.md` | `07f2fb62d996a888bcfe4243bed3693bfc34106ac985e2b79f04967ef82257f2` |
| `docs/CONTEXT.md` | `f6aec6ea03a0afb77b2879409a18a31c96c16d02d68bb55105dd4f501b631fb8` |
| `docs/DECISIONS.md` | `d7b512d98a96d449becf99bbec4518058cbfaf425ab406b6f9ecb2171a1964d4` |
| `docs/ROADMAP.md` | `1f5be9fac5216ac7c3418d08fc469ca67939b197afcd9746a75af0332e15e4a0` |
| `src/quanto/research_broker.py` | `ad8fe8f46103c85fdf77dd4ade94449f504d449ed5e01d580934312d6b8bd6b4` |
| `src/quanto/research_packets.py` | `81232c126b7a50b54dad92f7339ce41de80899d709358c9a4ae8a6efe23dcdeb` |
| `src/quanto/research_comparison.py` | `c2e933841f1664b62528b4342b37a34e7b3452e7783d91f495f78a6b05d65446` |
| `src/quanto/event_engine.py` | `cb1a61985ebb08089eab50d00d1e78f09a83fdea6754587af7e871e177175ffc` |
| `src/quanto/research.py` | `186e6a9aa95a484e94d71cbd71f276c053b923e96e030fa6eea0adcfc53223ca` |

## What this attempt establishes

The reports support a narrow operational observation: the broker dispatched and retained three actual Haiku model responses, bound them to distinct issued stages, settled their provider usage, and honored the engineer's explicit stop. The engineer did not authorize `launch_development`; independent quality reports no financial intent, comparison child, suite run, exploratory study, predicate result, or oracle check. The model's finding codes describe its expressed concerns. They do not show that the private roster was incomplete or the frozen specification mismatched.

The $0.009116 is settled usage for these three calls. The critic reports $0.221817 in retained research-purpose holds, which is reservation accounting and must not be presented as an invoice. The latest public project-wide budget statements still refer to an earlier November 1 Los Angeles checkpoint; I did not inspect the runtime journal and cannot state current global headroom. Contextualization should record this actual usage and explicitly label the older budget figure as historical until the lead checks the current ledger.

The pre-entrypoint `python -m quanto.cli` launch error is reported by the lead as producing no submission, reservation, or dispatch; the supported CLI entrypoint then produced the three-response attempt. The critic did not independently observe the initial empty invocation. Preserve it as an attributed local harness failure, not as a paid retry or completed workflow. The critic's own inspector also had two retained corrections before its final consistent-but-incomplete inspection. These inspection corrections do not erase the original attempt or convert `all_checks_passed=false` into full-cycle acceptance.

## Required correction before another paid attempt

The critic identifies a factual packet defect that is visible in public source: `research_packets.py` permits the method label `frozen_trailing_return_next_open_three_costs`, and `research_broker.py` sends it. But `research.py` defines a simple moving average (SMA) level rule; `event_engine._target` compares a completed close with its lookback SMA, and execution uses the next supplied session's open. “Trailing return” misdescribes the computation. This is a required correction, not a stylistic preference: the three models received inaccurate method framing. It does not establish that this label caused the engineer to stop, and the stop remains valid.

Before any later paid dispatch, correct the method label and give models only verified, nonnumerical method-integrity facts sufficient to distinguish authorizing a deterministic test from certifying its result. Such facts must be derived from the exact locally verified suite/configuration, and may state only what those validators actually checked (for example, a complete frozen three-cost roster and one common specification except cost). Keep predicate truth, numerical operands, prices, dates, instrument identifiers, raw rationale and result values private. Add focused consistency/egress checks and obtain fresh independent review of the changed prompt/schema/code. Do not rerun or rewrite this stopped attempt; any later attempt needs a new run identity and fresh budget authorization.

## Contextualization corrections and next gate

As inspected, `STATUS.md` and `HANDOFF.md` say no actual D008 model workflow has run, which is now false. `ROADMAP.md` says the next step is to observe the first real workflow; instead, it should record that the first actual attempt stopped at the engineer and that the next paid attempt is gated on the packet correction and fresh review. `REQUIREMENTS.md` correctly keeps R14 pending and should continue to do so. `CONTEXT.md` and `DECISIONS.md` should record this attempt as a real, incomplete workflow event and distinguish its $0.009116 settlement from the older global-budget checkpoint; no current remaining-cap figure can be asserted from this review.

The next operational acceptance is a distinct, corrected, complete seven-stage run in which an actual model-authored supported choice drives a newly registered calculation over a fresh frozen D007 suite. It then requires separate trace review of actual assignments, model identities, choices, handoffs and child lineage, plus an independent local numerical review of the new private derivative and its accounting inputs. Any numerical reviewer must use an independently derived calculation path and must not transmit values to role models. Quality and scope remain distinct. Until that succeeds, this attempt demonstrates truthful stopping and partial actual dispatch only; it does not close R14, establish investment performance, or imply persistent operation.

# D007 independent quality validation

Reviewer: independent native agent `/root/d007_quality`, 2026-11-02 UTC. This reviewer did not produce the implementation, act as implementation critic, inspect the actual annotation, or perform the scope review. The only repository file owned by this review is this report.

The frozen implementation passes independent software-quality validation: **808 tests plus 12 subtests** pass in both the source workspace and a clean, noneditable installed environment; lint passes in both. Additional independently written probes confirm the complete unstubbed synthetic D007 path, exact three-cost replay, pre-computation child binding, durable interrupted-suite inspection, privacy, timing and preservation of prior nominal cash claims. No unresolved quality blocker was found. This is software evidence from invented fixtures, not actual source-semantic approval, market performance or a completed historical pilot.

## Exact inspected revision

Review started on base commit `23c99219c608be6430f357f75f10fed373dd0af0` with uncommitted implementation changes. During review the lead committed the same inspected implementation as `76f46cd9b54b0635404b9ba7d64fb41017344197`. All identities below were checked again after both full-suite runs and the installed probes and remained unchanged. Commit identity alone does not replace these artifact identities.

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/admission.py` | `5b1d5aa7d9aea6488ba96ac8a89a597d37e78ad28be0175699f6032abb8787c1` |
| `src/quanto/policy_revision.py` | `eb7ac89bbf1c85cf276f614bd296ad82f2d22f94d723788a3718c42ff5b12625` |
| `src/quanto/study_suite.py` | `c3e552ef9998e72ae6f69b55bf43750d51f94522faf98a26ecbb624042f46360` |
| `src/quanto/explorer.py` | `6a3f02d27f0c062d993ee3d112f0e76b88221fc8653305b84be62b822bcb9745` |
| `src/quanto/cli.py` | `44d5ecb2876e320c3b71f5bf00c7cac9caa50bf36c666956e64817a27e0ca471` |
| `src/quanto/event_engine.py` | `cb1a61985ebb08089eab50d00d1e78f09a83fdea6754587af7e871e177175ffc` |
| `tests/test_admission.py` | `fd8c3c2c4faeea6c1923b82bf3223bca5d2532e45238792849e616d6005bf9f3` |
| `tests/test_policy_revision.py` | `52962b9953bd1c11aa5add4b23f5f513c9f9d9f2ccbead3e7a8286ab54584765` |
| `tests/test_study_suite.py` | `ed184008dc6a2596143c8d4666a3c2baf730fe731ecbe79450197a30cf62f7d2` |
| `tests/test_explorer_suite.py` | `c753bad81a017f586a6563796713b84183d1467076795f96398a6f7fca4fcb59` |
| `tests/test_cli_requests.py` | `c54429143072ffb2539b4259f5f1892a002cd7d3fdc209932f2a2fc9deb5babf` |
| `docs/D007_POLICY.md` | `bf8c254645c33550fceb19b794a3aeae933c54d635df149fccda8310f5e987ce` |
| `docs/POLICY_REVISIONS.md` | `58b1595513581ca4c94bf90cf21696c11d5bba8831f3be42393f0ce1d7ca7cb5` |
| `docs/STUDY_SUITES.md` | `37207a318c08e962c461a743ca145db5ce8552c8815f072c83c8ef5648954a7f` |
| `docs/RESEARCH_PROTOCOL.md` | `9bd2ffa6e6ef49c1787da33324beba12e6c898ff5dc4200343c7ee1bbdbc7a21` |
| `pyproject.toml` | `4f37dc1155abde9f5cc2c1b3a5b02b18ca8212ea67005b8b71ee21418c4f6997` |

The numerical event engine matches the supplied original hash exactly; D007 changes admission, lineage and workflow controls rather than its arithmetic.

## Reproduction and executed checks

Source verification used `PYTHONPATH=src .venv/bin/pytest -q`: **808 passed, 12 subtests passed in 23.38 seconds**. `.venv/bin/ruff check .` returned `All checks passed!`. Source Python was **3.13.12**, pytest **9.2.0**, ruff **0.17.3**.

A fresh bounded temporary tree copied only `src`, `tests`, `docs`, `scripts`, `pyproject.toml`, `README.md` and the lock file when present. It copied no project runtime, data, environment file or private source. These commands built and installed a wheel into a new environment, rather than installing editable source:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[dev]'
env -u PYTHONPATH .venv/bin/python -m pytest -q -o pythonpath=
.venv/bin/ruff check src tests
```

The installed run returned **808 passed, 12 subtests passed in 25.43 seconds**, and lint returned `All checks passed!`. Import inspection confirmed `quanto.__file__` under `.venv/lib/python3.11/site-packages/quanto/__init__.py`; the pytest `pythonpath` override prevented the copied `src` tree from supplying the implementation. Installed Python was **3.11.9**, pytest **9.2.0**, ruff **0.17.3**. The built wheel was `quanto_research-0.1.0-py3-none-any.whl`, 133246 bytes, SHA-256 `3ecbbbcf13ea16fe9b6cdc5cad1423bb76ce0fc68e8de10c231f930a083a4a1b`. Build/development dependencies were downloaded without a paid service or model call. This also exercises two supported Python versions; it does not certify every permitted future dependency version.

Three additional temporary probe programs were independently authored, executed against source, then rerun against the installed package. Their final hashes were `55c9cef3a15f7556050e02e4ed56a4df172a9f054a20f4be3c66b5cf6d2eca18` (integration/privacy), `c8033f9dd3cec7ad9e51ac303ab35328b13dcc3ca09ac09874e332b1d10ad6a5` (abrupt interruption), and `86160267c8cdc88ac67251fabe5bc24dfcd0b1a5e84c6bd1c6f5113e7439983d` (timing/accounting). They remain temporary review aids, not new production tests. Their substantive assertions and outcomes follow.

## Independent probes and implications

**Actual synthetic admission through complete replay.** The integration probe reused the producer's invented fixture constructor, `regular_way_fixture`, solely to build retained synthetic source artifacts and invoke the real adapters through synthetic transports. It did not replace admission, revision, membership, launch or numerical validators. It preserved the real API's two refusal outcomes, registered the semantic review and additive revision, then called actual admission. It supplied the suite members in order 25, 0, 10; the successful registered/run roster was canonical 0, 10, 25. Two intentional complete invocations succeeded, yielding three distinct fingerprints and six distinct attempt IDs. Each scenario retained identical result-artifact bytes and the same fingerprint across replay. Source and installed probe journals each verified **112 events**; variable journal heads reflect separate fresh executions rather than a promised identical timestamped journal.

Each resulting report contained the complete three-member roster, full admission evidence, original action exclusion, policy lineage with post-acquisition-change count 2, explicitly unresolved redemption disposition and attributed inferred purchaser entitlement. `investment_evidence` remained false. This establishes that the newly connected boundaries work together without admission/revision stubs, beyond the narrower mocked integration tests. All market-like values were invented; their use of the historical routing label tests that route and does not turn them into historical market evidence.

**Launch gate and critic correction.** Calling the individual public explorer route with a valid registered D007 member but without a suite invocation returned `invalid/suite_invocation_required`; no attempt existed afterward. For all six successful children, the independently read journal showed suite registration before binding and binding before `explorer_execution_registered`. The full roster and original run-request bytes are retained and checked; launch payload and event order, pending child request identity and unique binding are verified before calculation. The post-computation check repeats validation. Per-invocation IDs stay in receipts, preserving identical result bytes across deliberate replay. These observations support closure of the critic's earlier direct-member completeness objection for these inspected bytes.

**Abrupt interruption and no silent recovery.** A separate probe replaced only the engine entrypoint with a deterministic `KeyboardInterrupt` before building the fixture, so the recorded code identity consistently described that fault-injection environment. This probe tests interruption behavior rather than numerical correctness. An interruption at the first calculation left one discoverable pending suite run, a bound pending child and exactly one registered attempt. Inspection retained all three slots: first pending with its child identity, two explicitly `not_started`. No automatic retry occurred. This directly checks the binding-before-computation fix under interruption instead of assuming that a successful path alone establishes crash visibility.

**Unavailable dependencies and privacy.** Tombstoning the retained facts after successful runs blocked a new run as `invalid/artifact_or_storage_unavailable`; an old run remained inspectable with all three successful outcomes. Separate malformed requests containing a private sentinel produced retained invalid submissions, no artifact objects and no sentinel in event payloads. Existing suite/revision tests independently executed in both full runs additionally exercise malformed and duplicate JSON, publication interruption/pending status, dispatch failures, roster completeness, non-additive facts, false lineage, journal/materialized-record mismatch and stale loaded validators. Passing those producer-authored tests is separate evidence from the new probes, not independently authored coverage.

**Hand-derived timing and cash-claim check.** A separately constructed six-session numerical path began with cash 120, bought 10 shares at an evaluation-session open of 12, accrued a nominal dividend claim of 10, converted holdings once from 10 to 20 at a 2-for-1 split, then sold those 20 shares at the split-session open of 6 using the previous completed-close target. Ending cash was 120, quantity zero and the earlier nominal receivable remained 10. Altering only the split-session close from 5 to 999 did not change any executed trade. Truncating the path before the split gave identical strategy and benchmark portfolios whether the future split was supplied or omitted. This independently checks prior-close timing, one transformation and preservation of an earlier cash claim. The full suite separately covers E-open entry, pre/post-record trades, warmup and additional negative profile cases.

## Attempt history and qualifications

No failed review attempt is hidden. The first integration-probe draft asserted a nonexistent top-level `unresolved_discrepancies` field; actual evidence correctly stores these dispositions within `accepted_action_treatments`. The probe was corrected to inspect that actual schema and passed. The first future-prefix comparison compared entire reports, including differing declared action metadata; it was corrected to compare the strategy and benchmark portfolios that the invariance claim concerns. The first clean-copy collection omitted `scripts/configure_alpaca.py` and failed collection; copying the omitted public script directory resolved the harness error. An initial attempt to use `uv` found no executable on this shell's path, so reproduction used the standard-library environment and pip commands recorded above. None of these corrections changed production code or tests.

The reviewer read no `.env`, runtime database, project data directory, private provider records or actual annotation candidates. Synthetic databases lived only under fresh temporary directories. No external-model, broker, order or market-data request occurred. No production edits or commits were made by this reviewer.

The accepted policy's economic-share model, expected/scheduled trading language, unresolved ancillary details and economic-only limitations remain qualifications, not defects erased by passing tests. Hashes and append-only application records constrain cooperating processes; they do not authenticate authors or make SQLite immutable against its owner. This review does not independently establish issuer facts, rule interpretation, calendar completeness, licensed-source rights, protected evaluation or investment performance.

Quality validation clears these exact software bytes for the next separately gated work. Actual annotation semantic approval, independent criticism and scope disposition, admitted actual three-scenario calculation, unchanged-oracle comparison and exact historical replay remain distinct requirements. D006 and the complete private operation are not closed by this report.

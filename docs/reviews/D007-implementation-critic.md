# D007 implementation criticism

Reviewer: independent native agent `/root/d007_implementation_critic`. Review date: 2026-11-02 UTC. This reviewer did not produce the implementation and did not act as its quality validator or actual-event semantic reviewer.

The reviewed implementation enforces the main D007 financial-admission and lineage boundaries. The public-route reporting objection below was reproduced, corrected by the lead, and independently rechecked. Every D007 calculation now needs a durable suite invocation and unique child binding. The corrected path passed an independent, unstubbed synthetic exercise, including all three costs and deliberate exact replay. This report approves neither actual source facts nor actual-market calculation.

## Exact inspected artifacts

The worktree was based on `23c99219c608be6430f357f75f10fed373dd0af0` with uncommitted implementation changes. These SHA-256 identities identify the reviewed bytes; the base commit alone does not identify the implementation.

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/admission.py` | `5b1d5aa7d9aea6488ba96ac8a89a597d37e78ad28be0175699f6032abb8787c1` |
| `src/quanto/policy_revision.py` | `eb7ac89bbf1c85cf276f614bd296ad82f2d22f94d723788a3718c42ff5b12625` |
| `src/quanto/study_suite.py` | `c3e552ef9998e72ae6f69b55bf43750d51f94522faf98a26ecbb624042f46360` |
| `src/quanto/explorer.py` | `6a3f02d27f0c062d993ee3d112f0e76b88221fc8653305b84be62b822bcb9745` |
| `src/quanto/cli.py` | `44d5ecb2876e320c3b71f5bf00c7cac9caa50bf36c666956e64817a27e0ca471` |
| `src/quanto/event_engine.py` (unchanged supporting code) | `cb1a61985ebb08089eab50d00d1e78f09a83fdea6754587af7e871e177175ffc` |
| `tests/test_admission.py` | `fd8c3c2c4faeea6c1923b82bf3223bca5d2532e45238792849e616d6005bf9f3` |
| `tests/test_policy_revision.py` | `52962b9953bd1c11aa5add4b23f5f513c9f9d9f2ccbead3e7a8286ab54584765` |
| `tests/test_study_suite.py` | `ed184008dc6a2596143c8d4666a3c2baf730fe731ecbe79450197a30cf62f7d2` |
| `tests/test_explorer_suite.py` | `c753bad81a017f586a6563796713b84183d1467076795f96398a6f7fca4fcb59` |
| `tests/test_cli_requests.py` | `c54429143072ffb2539b4259f5f1892a002cd7d3fdc209932f2a2fc9deb5babf` |
| `docs/D007_POLICY.md` | `bf8c254645c33550fceb19b794a3aeae933c54d635df149fccda8310f5e987ce` |
| `docs/POLICY_REVISIONS.md` | `58b1595513581ca4c94bf90cf21696c11d5bba8831f3be42393f0ce1d7ca7cb5` |
| `docs/STUDY_SUITES.md` | `37207a318c08e962c461a743ca145db5ce8552c8815f072c83c8ef5648954a7f` |
| `docs/RESEARCH_PROTOCOL.md` | `9bd2ffa6e6ef49c1787da33324beba12e6c898ff5dc4200343c7ee1bbdbc7a21` |

The final admission inspection includes the producer's checks that semantic review cannot predate calendar review or name any annotation judgment producer as reviewer, and filtering later duplicate semantic-review registrations out of an earlier admission's dependency set. The final corrected-path exercises used the admission, suite and explorer identities in the table.

## Corrected objection: individual execution omitted incomplete-suite reporting

**P2, public workflow completeness; corrected and reverified.** The original inspected suite/explorer identities were respectively `cacb15435e3e109f02737a340884efb5a4e91042776f4de14b7041d10fd68422` and `17e5b9ba69caddf70559cd613f3a12f9cb5dfdcec81568cb12aff3bfc8a667a6`. In those versions, `explorer.run_submission` checked registered roster membership at `src/quanto/explorer.py:555`, but did not require or create a suite invocation. `study_suite._summary` and `inspect_run`, starting at `src/quanto/study_suite.py:230`, inspected only members linked to an existing `study_suite_runs` row. The CLI exposes `explore` separately from `run-suite`.

Reproduction used only temporary invented artifacts and the production APIs, without replacing validators or the calculation engine:

1. Create `regular_way_fixture` from `tests/test_admission.py` in a fresh temporary directory. This invokes the actual refusal, review and policy-registration APIs.
2. Admit its dataset and register a three-member suite for 0, 10 and 25 basis points, using `DATES[2]` through `DATES[-1]`, lookback 2 and otherwise identical requests.
3. Call `explorer.run_submission(root, {**members[0], "suite_sha256": registered_digest})` directly.
4. Count `Provenance.list_submissions(kind="study_suite_run")`, then call `inspect_run(root, child_submission_id)`.

Observed output was `direct_member_status success`, `suite_run_submissions 0`, and `StudySuiteError unknown_suite_run`. The successful private result retained the complete registered roster and did not assert suite completion. Nevertheless, there was no discoverable suite invocation reporting the two missing member outcomes, although the accepted D007 contract requires every member's result/failure/pending state and an incomplete suite when a member is absent.

The lead corrected this by adding `validate_launch`: before computation it verifies the retained run request, canonical full roster, precommitted launch, request identity and journal ordering, then transactionally binds the exact child into the unique run/cost slot. Explorer rechecks the binding after calculation. Run identities remain in receipts and the journal, outside deterministic result bytes. The runner accepts an already-bound matching child and still records early validation failures.

Independent correction checks used the production APIs and invented source artifacts. A direct member now refuses `invalid/suite_invocation_required` with zero attempts. Two full suite runs succeed, preserve three distinct cost fingerprints, produce identical result artifacts for each replay and retain different attempt IDs. Reusing a completed invocation refuses `suite_invocation_not_pending`. In a separate fault-injection process, an engine-boundary `SystemExit` left the invocation pending, its first child already bound, the other two slots `not_started`, and `complete: false`. Reusing that pending slot refused `suite_launch_already_bound`; the attempt count remained one. This closes the reported omission and makes an interrupted computed child discoverable.

## Checks and supporting evidence

The reviewer executed `PYTHONPATH=src .venv/bin/pytest -q tests/test_admission.py tests/test_policy_revision.py tests/test_study_suite.py tests/test_explorer_suite.py tests/test_cli_requests.py`: **273 passed in 17.85 seconds** on the initial reviewed implementation. After the correction, the same selected files passed **288 tests in 18.38 seconds**. These are existing implementation tests independently executed by the critic, not a claim of independently authored coverage. Quality validation remains a separate role.

An additional temporary end-to-end exercise used the actual `regular_way_fixture`, `admit_dataset`, `register_suite` and `run_suite` APIs, with no validator or engine stubs. Both three-member invocations succeeded. The first invocation produced three different fingerprints. Each deliberate replay had an identical result-artifact identity and a different attempt ID. All invented fixtures, journal records and calculated values stayed in a temporary directory and were deleted when that exercise ended.

The source inspection supports the following bounded conclusions:

- Plan registration and refusal events are checked against the journal; predecessor links are ordered and complete relative to the declared chain. Actual refusal status/codes and exact request byte identities are retained. The decision and seven design reviews are pinned. The post-acquisition change count is derived from registration order rather than narrative timestamps.
- The latest refused facts are compared as canonical JSON values. Existing events, exclusions and source entries cannot be changed or reordered. Only appended sources, one split annotation/review pair and the independent schedule reference are added, with a retained path delta.
- The regular-way profile requires exact positive decimal/rational rates, integer forward ratio, identity agreement, issuer E matching provider ex-date and redemption guard, represented adjacent P/E sessions, source-bound entitlement judgments, explicit unresolved ancillary dispositions, distinct semantic reviewer and registered review precedence. Provider records and raw occurrence references remain embedded.
- Receipt sources, full acquired schedule dates, reviewed source identities and exact calendar/annotation identities are checked. Expected trading and unverified delivery remain explicit limitations; the software does not establish the truth of source interpretation or authenticate reviewer identity.
- Explorer enforces the frozen dataset, evaluation dates and strategy parameters. All three suite requests must differ only in their exact integer cost. Admission/revision/suite dependencies are revalidated before and after calculation, with disk and loaded identities for both new modules. Results carry the full admission evidence and scenario roster.
- Suite-run launch claims precede dispatch, retain all three slots, and do not automatically retry an uncertain child. Existing tests exercise pending/interrupted publication, crash discovery, dispatch errors and tombstones. Exact known failures count as complete but unsuccessful, while interrupted or pending outcomes remain incomplete; these meanings are documented separately.

The frozen mechanical descriptions are preserved from the registered predecessor plans rather than parsed as an independent strategy language. The actual numerical policy and engine identity are bound separately. This review found no demonstrated change in the fixed calculation semantics; it does not endorse arbitrary new plan descriptions as executable financial specifications.

## Limits and disposition

No credentials, runtime databases, real private market records or actual annotation candidates were inspected. No external request, model call, broker call or order occurred. All calculations used invented fixtures. The reviewer did not edit production code or existing tests and made no commit.

Actual event semantic approval, independent quality validation, no-drift review, actual three-scenario historical calculation, unchanged-oracle agreement and exact registered historical replays remain separate gates. The reported P2 is closed on the final identities recorded here; no unresolved consequential implementation objection was established in this inspection. This bounded software review cannot establish investment performance, protected holdout status or completion of the private operation.

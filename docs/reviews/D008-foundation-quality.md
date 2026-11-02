# D008 foundation independent quality validation

**Result: the bounded workflow-state and failure-memory foundation passes independent execution quality checks at the identities below.** The final complete suite passes **870 tests plus 12 subtests** from source and from an offline-built, noneditable clean installation. Lint and independently authored synthetic integration/recovery probes pass. No unresolved software-quality blocker was found within this foundation scope.

This validates software using `synthetic_fixture` evidence. It does not establish five actual model workers, an operational historical experiment, a capability broker or model dispatcher, protected evaluator isolation, a research scheduler, external-checkpoint restore, statistical acceptance, paper operation or trading readiness. Those remain separate requirements under D008_POLICY. A successful synthetic handoff cannot close R14.

## Independence and inspected identities

Reviewer: native agent `/root/d008_foundation_quality`, separately assigned by the lead. This reviewer wrote no implementation or production tests; its only repository-owned output is this report. Criticism and scope review belong to different agents. Required context, the preserved proposal and the accepted staged policy were read. No project runtime, actual market data, environment file, credentials, network service or model API was accessed by this review.

Review began at proposal commit `2f59f105e0e34339958a8354afd4246a11123ff7`, with the four implementation/test files uncommitted. The final source was subsequently committed as `fed57cfdcee1436de5b9f22dc51722aa5d463425`; final hash reinspection agrees with that implementation. Commit identity is supplemented by exact byte identities:

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/failure_memory.py` | `ee8200079cc0e091b06d60be6fe4ccb3d4886eb1ea986ee626db65ae7f9f7ee7` |
| `tests/test_failure_memory.py` | `68180c3f94209a79d54187aa55dec33aa6322bdbac76990c761a0b77f3dd4057` |
| `src/quanto/research_workflow.py` | `0228249ce64d433886bd85c4dd4b8da161656eb78f40e1ffec419eec5c913b47` |
| `tests/test_research_workflow.py` | `6f8bd6c0ccb1526ca1a3eef35b5d503d81985e00c2dfc75c0032838bc6d416d8` |
| `src/quanto/provenance.py` | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |
| `src/quanto/ledger.py` | `29c3f14bdae924b4d369b49b59c3ec7e5079810d76e55992fa1800d49a3da6cf` |
| `docs/D008_POLICY.md` | `91bd473d6972355c8cba447fff7b1e66e9b77bddf9712097ebd0f95bafc07aa7` |

## Executed suites and installation

From the source workspace:

```text
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
PYTHONPATH=src .venv/bin/python /tmp/d008_quality_probe.py
```

Final result: **870 passed, 12 subtests passed in 30.92 seconds**; `All checks passed!`; all independent probes passed. Source Python was **3.13.12**. The D008 modules contribute **62 collected test cases**: 35 memory and 27 workflow cases. These include parametrized cases rather than 62 distinct functions.

A fresh temporary tree copied only public `src`, `tests`, `docs`, `scripts`, packaging metadata, README and the lockfile if present. It copied no runtime, data or environment file. Cached tooling built a wheel offline, created a new Python **3.11.9** environment, and installed the wheel noneditably with no application dependencies. The final workflow/test bytes replaced the earlier reviewed copy before rebuilding and reinstalling. Commands from that tree were:

```text
uv build --offline --wheel --out-dir wheels
uv venv --offline --python python3.11 .venv
uv pip install --offline --python .venv/bin/python 'pytest==9.2.0'
uv pip install --offline --python .venv/bin/python --reinstall --no-deps wheels/quanto_research-0.1.0-py3-none-any.whl
.venv/bin/python -m pytest -q -o pythonpath=
/Users/ronoktanvir/Documents/ChatGPT/quanto/.venv/bin/ruff check src tests
.venv/bin/python /tmp/d008_quality_probe.py
```

The actual `uv` executable was addressed by its absolute installed path when the temporary directory's shell did not resolve it. Imported `quanto.__file__` resolved under the new environment's `lib/python3.11/site-packages/quanto`, outside the repository. The pytest override removes the project's normal `src` path injection. Final installed result: **870 passed, 12 subtests passed in 28.85 seconds**; lint and all independent probes passed. Ruff **0.17.3** was reused as an existing standalone executable after its offline installation was unavailable from cache; no network fallback occurred.

The final wheel was **147760 bytes**, SHA-256 `f19db29c93b98a7064987a751f0b49e36be5df9fb37983021d6f90dde13749e4`, with 29 entries. Both reviewed modules equal the source bytes in the archive. All three web assets are present; no runtime, data, private or environment entries occur. This identifies the observed wheel, without claiming reproducible ZIP timestamps.

## Independent synthetic probes

The temporary reviewer-authored probe program has SHA-256 `d5d37bc71485598a87141b33935894be0b3ffbaf1d32e80418a0cbe9c1061336`. It ran against final source and the final installed package. It calls actual Provenance, Ledger, ResearchWorkflow and FailureMemory APIs, retains real SQLite/artifact bytes in disposable temporary directories, and does not stub storage, issue network requests or load project runtime. Clock injection supplies synthetic time.

**Seven-stage persistence and exact handoffs.** The probe creates a frozen sanitized development manifest, then runs director, hypothesis, engineer, data critic, statistical critic, quality and scope in the fixed order. Each stage closes and reopens its Provenance connection, claims its issued token, registers and starts an allowed intent, retains a real JSON result, finishes that intent and publishes its exact handoff. All seven actor identities are distinct. Upstream handoff lists equal the preceding published identities; each critic/oversight handoff binds its entire issued reference set, with an intentionally incomplete review refused. Issued authorship and a synthetic-only objection survive publication. Forbidden order actions and caller-supplied author fields are refused. The final run is complete and its event chain verifies **75 events** in both executions.

The hypothesis stage actually calls FailureMemory and uses that query's retained receipt as its intent result. The source failure remains `invalid` while its correction disposition is returned with the verified fix reference. Later stages inspect actual upstream JSON references. The other role outputs are explicitly invented software-check summaries; the engineer performs no financial calculation and no stage calls a model. This distinction prevents the state exercise from being misreported as the operational-role acceptance cycle.

**Recovery and cancellation.** Closing and reopening after authorization but before an effect allows an expired assignment to return to pending and acquire fence 2. Calls at the old fence cannot authorize, start, finish or publish. Closing after effect start produces durable `uncertain` state, no automatic reclaim and no duplicate effect. Recovery is idempotent. Cancellation before start yields `cancelled`; cancellation after start yields `uncertain`. Reopening preserves both outcomes and all five worker transition APIs reject later effects/publication.

**Artifact integrity and atomic publication.** The probe alters retained result bytes after successful effect recording. Handoff refuses and leaves neither a handoff nor a terminal stage record. Restoring the exact original bytes permits publication. Application triggers refuse deletion of run, assignment, intent, outcome and handoff rows. These are application append-only controls over SQLite, not owner-proof immutability. The production suite separately exercises rollback on a deliberately raised publication exception and concurrent claim/cancellation races.

**Live time checks and secret/audit corrections.** An independently controlled clock advances past the lease between initial validation and the final authorization check at effect start, effect completion and handoff publication. Every operation refuses and its corresponding start/outcome/handoff row remains absent. No storage method is replaced. Issued-token text embedded in worker/request identity refuses, and the raw token remains absent from journal payloads and SQLite bytes. JSON fields `api_key`, `access_token` and `password` refuse even with an otherwise unrecognized synthetic value. Four rejected authenticate/start/finish/handoff calls each create a sanitized audit event. The suite additionally exercises token text in an artifact and handoff, and lease expiry during the actual publication helper.

**Bounded searchable corrections.** After a failed original submission and 501 newer pending submissions, a two-result query scans exactly **500** submission rows and reports truncation. An exact old-ID query finds the older failure before the scan cutoff. An append-only correction links verified bytes without changing original failed status. Removing those bytes retains the correction claim but returns no fix reference and explicitly reports `unavailable`. A later reopening disposition yields unresolved state while both dispositions and the original failure remain retained. Event verification succeeds. Suite checks additionally cover the 50-result cap, bounded filter sizes, maximum eight references per result and 32 approved artifact verification operations per query, with explicit verification-bound disclosure.

## Review history, limits and disposition

Earlier source and installed runs passed **866 tests plus 12 subtests** at the initial workflow hash `6bdf0d303de8b398736818a37e8a7d2745e2152ff138af917c57d7484bde069d` and test hash `cd8598bf87cf87eda5f0fe30db568f1614d6e5702c82924723b8788a9e37768b`. The separate critic then reported embedded-token persistence and missing rejection-audit findings. The producer corrected those, added lease rechecks and four tests; intermediate source/installed runs passed 870 plus 12. The final JSON credential-key correction was inspected and both complete suites and expanded probes were rerun at the exact final identities above. Earlier results are not substituted for final verification.

Review-tool corrections were limited to tooling: the shell's `shasum` failed because of an unsupported locale, so hashes were computed with Python; the temporary shell needed absolute `uv`; offline Ruff dependency resolution refused, so the existing executable was used. An initial successful wheel build ran in the checkout before the separate clean-tree build; the reported wheel and installed tests come from the clean tree. No production implementation was edited to make a probe pass.

The foundation is suitable for integration at these bytes. Its security claim is limited to cooperating same-user callers and trusted supervisor admission. Fixed metadata projection and credential screening do not establish data-use rights, detect every private value or authorize external transmission. FailureMemory itself authenticates no caller; a future broker must restrict retrievable failure IDs and generated outputs. Contract spend fields do not reserve money or enforce the daily cap without the future dispatcher. Actual paid workers, registered historical execution, egress controls, evaluator gates, scheduler/restore and later paper/live acceptance remain incomplete.

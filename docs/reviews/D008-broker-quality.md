# D008 broker independent execution quality

**Result: the bounded D008 broker increment passes independent execution-quality checks at the exact identities below.** Final complete suites pass **1087 tests plus 12 subtests** from source and from a clean noneditable installation. Lint and independently authored composition, privacy, arithmetic, cost, fencing, interruption and CLI probes pass. No unresolved execution-quality blocker remains within this bounded increment.

This is `synthetic_fixture` software evidence. The model envelopes and all source records are invented. No actual model, historical research run, account charge, unseen holdout, protected evaluator, scheduler, paper operation or trading readiness is certified. R14 and the full private operation remain incomplete.

## Independence and exact inputs

Reviewer: native agent `/root/d008_broker_quality`, independently assigned for execution quality. This reviewer changed no production module or repository test. Its sole owned repository output is this report. Separate criticism and scope reviewers are not counted as this reviewer. The review read AGENTS, CONTEXT, STATUS, ROADMAP, DECISIONS, HANDOFF, D008_POLICY and D008-broker-contract, then inspected the new broker/dispatcher/packet/comparison code and the provider, workflow and CLI changes.

Repository HEAD at review was `fc1c8c4e3c5f8dd37c77617f6a121d2ed42f57af`; the increment was uncommitted, so the byte hashes below identify the accepted checkpoint. No project runtime, private market records, `.env`, credentials, live service, network or paid call was accessed. Disposable temporary trees contain only public repository files and invented fixtures. The native HTTP probe replaces the opener with an in-memory response; it is not an actual provider response.

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/research_broker.py` | `ad8fe8f46103c85fdf77dd4ade94449f504d449ed5e01d580934312d6b8bd6b4` |
| `src/quanto/research_dispatch.py` | `120834deb63abebeeb54a14f8cf470ad43fd9ac1f44979ee96fe9c88ba20c1f1` |
| `src/quanto/research_packets.py` | `81232c126b7a50b54dad92f7339ce41de80899d709358c9a4ae8a6efe23dcdeb` |
| `src/quanto/research_comparison.py` | `c2e933841f1664b62528b4342b37a34e7b3452e7783d91f495f78a6b05d65446` |
| `src/quanto/research_workflow.py` | `64ca63f155a2417021bb8632673f14ec12ff7d497881aa13a95d7330911ab02b` |
| `src/quanto/provider.py` | `5f4f214d079bd4a17ddc3049163d5a3bfc9acd8ba2508a3dfe2f5ad5c4c0ace0` |
| `src/quanto/cli.py` | `7201b943efea1777c70e0fff7ce3d2e953089ba58648e360e53b5f6a22dabbd7` |
| `src/quanto/failure_memory.py` | `ee8200079cc0e091b06d60be6fe4ccb3d4886eb1ea986ee626db65ae7f9f7ee7` |
| `src/quanto/ledger.py` | `29c3f14bdae924b4d369b49b59c3ec7e5079810d76e55992fa1800d49a3da6cf` |
| `src/quanto/provenance.py` | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |
| `src/quanto/explorer.py` | `6a3f02d27f0c062d993ee3d112f0e76b88221fc8653305b84be62b822bcb9745` |
| `src/quanto/admission.py` | `5b1d5aa7d9aea6488ba96ac8a89a597d37e78ad28be0175699f6032abb8787c1` |
| `src/quanto/study_suite.py` | `c3e552ef9998e72ae6f69b55bf43750d51f94522faf98a26ecbb624042f46360` |
| `tests/test_research_broker.py` | `25c6b971df6ca9286ef196a1d76a30cca2a4f056a8e246c2e767c12882c07129` |
| `tests/test_research_dispatch.py` | `fac65cd292e8c7a13c0c62f514a17a17963787bb26838eab348f6e6d7e9eb616` |
| `tests/test_research_packets.py` | `dd35ec89718b3b0b5678443eba58ca9a25f9d5153c1c6171f6de34ac0a307897` |
| `tests/test_research_comparison.py` | `95e920e547e9a56daf9adab032eba0d5d1b0b946d182364f78d9546636ede88a` |
| `tests/test_provider.py` | `87083d561434fdb7eae9c100bc027400397cfe3cbd000b3336d7c2fac347fe59` |
| `docs/D008_POLICY.md` | `91bd473d6972355c8cba447fff7b1e66e9b77bddf9712097ebd0f95bafc07aa7` |
| `docs/reviews/D008-broker-contract.md` | `8be2607b843b14f840bd6c55de90296124eb15a8ca76bc57a8cbb175ed33f86d` |
| `pyproject.toml` | `4f37dc1155abde9f5cc2c1b3a5b02b18ca8212ea67005b8b71ee21418c4f6997` |
| `src/quanto/research.py` | `186e6a9aa95a484e94d71cbd71f276c053b923e96e030fa6eea0adcfc53223ca` |
| `src/quanto/event_engine.py` | `cb1a61985ebb08089eab50d00d1e78f09a83fdea6754587af7e871e177175ffc` |
| `src/quanto/policy_revision.py` | `eb7ac89bbf1c85cf276f614bd296ad82f2d22f94d723788a3718c42ff5b12625` |
| `tests/test_admission.py` | `fd8c3c2c4faeea6c1923b82bf3223bca5d2532e45238792849e616d6005bf9f3` |
| `tests/test_policy_revision.py` | `52962b9953bd1c11aa5add4b23f5f513c9f9d9f2ccbead3e7a8286ab54584765` |

The eight unchanged storage/financial modules `ledger`, `provenance`, `research`, `event_engine`, `admission`, `explorer`, `policy_revision` and `study_suite` were independently compared with HEAD and remain byte-identical. No financial-policy or historical-admission identity was relaxed.

## Executed suite and installation

Final source execution used Python **3.13.12**, pytest **9.2.0** and Ruff **0.17.3**. `pytest -q` passed **1087 tests plus 12 subtests in 70.22 seconds**; `ruff check .` passed. The final clean installed suite passed the same **1087 tests plus 12 subtests in 72.01 seconds**, with lint also passing. The five directly relevant test files contain **237 collected cases**, including preexisting provider coverage.

Commands executed for the final checkpoint include:

```text
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
PYTHONPATH=src .venv/bin/python /tmp/d008_broker_quality_probe.py
uv build --offline --wheel --out-dir final-wheels
uv pip install --offline --python .venv/bin/python --reinstall --no-deps final-wheels/quanto_research-0.1.0-py3-none-any.whl
.venv/bin/python -m pytest -q -o pythonpath=
.venv/bin/python /tmp/d008_broker_quality_probe.py
```

The last four commands ran in the disposable clean tree. Before final reinstall, it was initialized with `uv venv --offline --python python3.11 .venv` and cached `pytest==9.2.0`; `uv` was addressed by its existing absolute local path. Ruff from the existing source environment checked the clean tree's `src tests`.

The clean build copied only `src`, `tests`, `docs`, `scripts`, packaging metadata and README, excluding runtime, data and environment files. A fresh offline-built wheel was installed noneditably into a new Python 3.11.9 environment using cached pytest 9.2.0. Tests ran with `-o pythonpath=` to disable the repository's `src` injection. Actual `quanto.__file__` resolved under that environment's `lib/python3.11/site-packages/quanto`, outside the source checkout. Existing Ruff 0.17.3 checked both trees. No dependency download or network fallback occurred.

The final wheel has **172902 bytes**, **33 entries** and SHA-256 `7cf421e648a6fd64367db5a2b5923b6be12c0db127db7d2bb79ce68ee4a5084e`.

The final wheel's Python module bytes equal the reviewed source. Its archive includes all three web assets and no environment, runtime, database or private data entries. The reported wheel hash identifies this observed build, without claiming stable ZIP timestamps.

## Independently authored probes

The temporary reviewer-authored program, `/tmp/d008_broker_quality_probe.py`, SHA-256 `b07a0a4edab5df1fac23b4c696daa69d77201e0015e8c635b4e8a70e8ac049a8`, passed against both final source and the final installed wheel. It uses real Provenance, SQLite, admission, suite, explorer, financial engine and derivative code. Only model transport, synthetic clocks and explicitly described interruption points are injected. The fixture constructor is `tests/test_admission.py::regular_way_fixture`; the reviewer wrote its own model actor, checks and arithmetic rather than using the producer's broker fixture actor.

**Actual seven-stage composition over invented evidence.** Two complete runs execute director, hypothesis, engineer, data critic, statistical critic, quality and scope through separate issued assignments. Each has seven synthetic dispatch authorizations and observed envelopes, while `all_models_actual`, `operational_acceptance` and `investment_validation` remain false. The first run's journal verifies 170 events. Researcher output selects two different supported predicates; the engineer follows each selection, and registration fingerprints differ. Each run executes one fresh full suite and three actual engine children, with no substitution of older attempts.

The reviewer independently reads the six fresh children's reports, converts their nine operands per run directly to Decimal and compares all 18 derivative operands. It independently computes the nonincreasing-cost-equity predicate and the all-cost strategy/benchmark equality predicate without calling the derivative's `evaluate`. Both retained Boolean results agree. This independently checks the derivative arithmetic and child selection; it does not reimplement the financial engine or establish investment performance. The invented D007 helper uses the historical admission interfaces for software coverage; its classification fields do not turn invented records into observed market evidence.

**Bounded egress and stable meanings.** Every outbound packet is inspected. Suite hashes, failure submission IDs, invented instrument/date strings, raw private failure notes, model rationale, numerical result keys and predicate truth remain absent. Only the expressly granted unsuccessful failure ID appears, as fixed code `unsupported_due_bill`; an ungranted `identity_change_unresolved` failure remains excluded. All artifact aliases preserve their exact local meanings as later stages receive more references. Private response objects never become alias inputs. Additional prices, dates, provider ID, raw error and protected-reference fields each refuse under the exact schema. These checks establish this broker's explicit typed projection, not a universal privacy detector or transmission-rights judgment.

**Uncertainty, spend and fencing.** A mismatched hypothesis model stops after two fixture sends, leaves its full reservation uncertain with no actual amount, launches no suite and cannot replay the same run key. A separately recorded uncertain hold of USD19.999999 leaves no sufficient headroom; the workflow refuses before a dispatch. Independent cancellation and expiry inserted immediately after atomic authorization produce no transport call, retain the started entitlement and full uncertain hold, and publish no successful model effect. A near-exhausted global budget rolls back effect start, provider allocation, role hold and dispatch together. Separate independent local-delay probes advance the clock during effect-start verification across Los Angeles midnight, rolling back reservation, purpose allocation, dispatch and start together, and during the final send guard past lease expiry, retaining a full uncertain hold with zero sends. The complete producer suite additionally exercises concurrent shared reservations, wrong fences/workers, malformed/truncated responses, pause and midnight, lost lease during response/publication, and nonrecycled research-purpose holds.

**Financial completion and child recovery.** The reviewer lets an unstubbed comparison and all three children finish, then cancels the workflow before the engineer publishes. The successful comparison, suite and three children remain retained, but the broker returns invalid and no engineer handoff exists. A different probe interrupts immediately after the registration callback's child binding, before any suite launch. Reopening shows the exact pending parent and child, matching original request hash/size, assignment/fence and consumed intent, with no successful outcome and no financial suite. That journal verifies 91 events. This validates the final repair's durable parent-to-effect-to-child chain under interrupted handoff publication.

**Native request path and operator boundary.** An in-memory urllib response exercises `_send_research`'s native path: one POST to the fixed endpoint, the required API-version/header values, exact response-byte hashing and decreasing read deadlines. The HTTP body is never sent over a network. Separately, an actual CLI process receives a request containing arbitrary shell, endpoint and tool fields. It exits 1, retains one invalid submission, displays only the bounded lifecycle refusal, creates no reservation or dispatch, and never creates the proposed marker file. This establishes local refusal and request construction; actual provider access, returned models, billing and end-to-end live transport remain untested by this review.

## History, limitations and disposition

Before the final recovery correction, independent source execution passed 1073 tests plus 12 subtests in 80.23 seconds. A later clean snapshot, including dispatch guard corrections and six subsequently added cases, passed 1079 plus 12 in 77.24 seconds. Those intermediate runs do not certify the final source. The [separate critic](D008-broker-critic.md) closed two P1 timing/accounting findings and a P2 parent-linkage finding. The P2 identified ambiguous parent/tool/child linkage if a comparison crashed before stage handoff. The producer also corrected final lease/day rechecks after potentially slow reads and kept atomic authorization on one original accounting day. For parent linkage, the producer added precommitted exact request records and a unique child-binding callback; this reviewer inspected the fix and executed the independent recovery/cancellation probes above before repeating final verification.

Reviewer-harness corrections were limited to an assumption about newest-first submission ordering, an incorrect reservation column name and an overlarge expected event-count floor for a pre-financial interruption. No production implementation changed to make those probes pass. Final claims use successful reruns after those corrections.

Broker revision checks bind disk source bytes and Python identity; the derivative additionally binds loaded-function identities. This acceptance covers the explicit one-shot workflow, not revision coherence for an already loaded or hot-reloaded persistent process.

The acceptance boundary is a cooperating same-user supervisor and application journal, not operating-system isolation or account-wide billing enforcement. Fixed method-only packets deliberately prevent later critics from inspecting private numerical outcomes; those models cannot certify hidden values. The separate actual-model historical workflow, exact observed models and charges, independent trace acceptance, protected evaluation, unattended research/restore and paper/live gates remain required. No unresolved execution-quality blocker remains within this reviewed bounded increment at the recorded bytes.

# D008 method-packet correction: independent quality

**The narrow method-packet correction passes independent execution quality at the recorded bytes.** Both complete suites pass **1133 tests plus 12 subtests**, source and clean installed lint pass, and independent invented-fixture probes confirm the integrity fact, bounded egress, conservative refusals, continued stop/block freedom and proof recovery after unsuccessful dispatch. No execution-quality blocker remains within this correction.

This is `synthetic_fixture` evidence. It neither demonstrates a new actual model cycle nor changes the original real engineer stop. The original stopped attempt remains historical; actual-workflow acceptance and R14 remain incomplete. This report does not authorize a paid retry or certify investment merit.

## Independence and inspected artifacts

Reviewer: `/root/d008_broker_quality`, separate from the producer and implementation critic. Base checkout: `72ac6b2b704dc2ad77d2284589a5aea573cd8871`; the correction was uncommitted, so the exact byte identities below govern. The reviewer inspected source, tests, accepted D008 policy and the separate correction critique. Its only repository output is this report. No actual project runtime, market data, environment file, credential, external service or model was accessed. Previous reports and private harnesses were not modified.

The correction changes only the broker and packet implementation plus three test files. Twelve supporting modules, including comparison, dispatch, provider, workflow, admission, suite, financial engines and storage, were independently compared with HEAD and remain byte-identical. No financial policy or admission identity was relaxed.

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/research_broker.py` | `c59a3801d41a68811231d640bc9dbd69e8a7ce933ab855e8f011f969d4654af7` |
| `src/quanto/research_packets.py` | `acdab795bbb47c2002d50cf4872bd9c58775bafd832ace5f0903ed2649d92dde` |
| `src/quanto/research_dispatch.py` | `120834deb63abebeeb54a14f8cf470ad43fd9ac1f44979ee96fe9c88ba20c1f1` |
| `src/quanto/research_comparison.py` | `c2e933841f1664b62528b4342b37a34e7b3452e7783d91f495f78a6b05d65446` |
| `src/quanto/research_workflow.py` | `64ca63f155a2417021bb8632673f14ec12ff7d497881aa13a95d7330911ab02b` |
| `src/quanto/provider.py` | `5f4f214d079bd4a17ddc3049163d5a3bfc9acd8ba2508a3dfe2f5ad5c4c0ace0` |
| `src/quanto/study_suite.py` | `c3e552ef9998e72ae6f69b55bf43750d51f94522faf98a26ecbb624042f46360` |
| `src/quanto/admission.py` | `5b1d5aa7d9aea6488ba96ac8a89a597d37e78ad28be0175699f6032abb8787c1` |
| `src/quanto/explorer.py` | `6a3f02d27f0c062d993ee3d112f0e76b88221fc8653305b84be62b822bcb9745` |
| `src/quanto/policy_revision.py` | `eb7ac89bbf1c85cf276f614bd296ad82f2d22f94d723788a3718c42ff5b12625` |
| `src/quanto/ledger.py` | `29c3f14bdae924b4d369b49b59c3ec7e5079810d76e55992fa1800d49a3da6cf` |
| `src/quanto/provenance.py` | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |
| `src/quanto/event_engine.py` | `cb1a61985ebb08089eab50d00d1e78f09a83fdea6754587af7e871e177175ffc` |
| `src/quanto/research.py` | `186e6a9aa95a484e94d71cbd71f276c053b923e96e030fa6eea0adcfc53223ca` |
| `tests/test_research_broker.py` | `9869296ba174939b8112da1cfdc7bcb96c1c77155c3717c54f7f3dfaa0710fc7` |
| `tests/test_research_packets.py` | `0d6726bf830465857ba1d305d498e9521def07d5ee2c9f580df03380b0760f61` |
| `tests/test_research_dispatch.py` | `68cdc6d9599d0059e5d46443b6fe0cd24656fa8b1c3d5ec3d7f561c4a435a838` |
| `tests/test_admission.py` | `fd8c3c2c4faeea6c1923b82bf3223bca5d2532e45238792849e616d6005bf9f3` |
| `tests/test_policy_revision.py` | `52962b9953bd1c11aa5add4b23f5f513c9f9d9f2ccbead3e7a8286ab54584765` |
| `docs/D008_POLICY.md` | `91bd473d6972355c8cba447fff7b1e66e9b77bddf9712097ebd0f95bafc07aa7` |

## Executed verification

Source Python **3.13.12**, pytest **9.2.0** and Ruff **0.17.3**: **1133 passed, 12 subtests passed in 93.27 seconds**; repository lint passed. A new offline-built noneditable installation under Python **3.11.9** passed the identical **1133 tests plus 12 subtests in 94.01 seconds**, with clean-tree lint passing. The packet, broker and dispatch modules contain **209 collected cases**.

The clean tree copied only public source, tests, docs, scripts and packaging metadata. It contained no runtime, data or environment file. Cached tooling created a new environment and installed the wheel plus cached pytest; no dependency download or network fallback occurred. `pytest -q -o pythonpath=` disabled source-path injection. Actual `quanto.__file__` resolved beneath the temporary environment's `lib/python3.11/site-packages/quanto`, outside the repository. The existing standalone Ruff checked its `src tests`.

Commands included:

```text
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
PYTHONPATH=src .venv/bin/python /tmp/d008_method_packet_quality_probe.py
uv build --offline --wheel --out-dir wheels
uv venv --offline --python python3.11 .venv
uv pip install --offline --python .venv/bin/python 'pytest==9.2.0' wheels/quanto_research-0.1.0-py3-none-any.whl
.venv/bin/python -m pytest -q -o pythonpath=
.venv/bin/python /tmp/d008_method_packet_quality_probe.py
```

The build, environment, installation, installed suite and final probe commands ran in the disposable clean tree. The actual local `uv` executable was addressed by its existing absolute path.

The observed wheel has **174077 bytes**, **33 entries** and SHA-256 `567a03b871f3f020fca86164114fac9f8f84ffd6dc32094d3c9150550d3273be`. Every packaged Python module equals the frozen source bytes. All three web assets are present, with no runtime, database, environment or private-data entries. This identifies the observed archive rather than promising reproducible ZIP timestamps. Source, clean-tree and wheel identities were rechecked after the successful suites.

## Independent probes and interpretation

The new reviewer-authored temporary probe `/tmp/d008_method_packet_quality_probe.py`, SHA-256 `35371ae6236e529b8a923387d07f455f37cd34e167ffa81d5e0a42e9187b9a03`, passes against both source and the installed wheel. It uses invented D007 sources from `regular_way_fixture`, its own synthetic model actor and real unmodified admission, suite, financial and journal entrypoints. It does not use the producer's broker actor or substitute a fake validator. Synthetic provider envelopes containing real model names remain synthetic evidence.

**The integrity fact follows from the actual validator.** One complete seven-stage run produces seven distinct private observations. At each injected transport call, the reviewer opens the temporary store, resolves that exact packet/proof/request binding, invokes the real `study_suite._verified` independently and compares its policy revision with the proof. It also independently checks costs 0/10/25 and equal frozen member specifications apart from costs. The observation's configuration and role match the issued binding. The full run executes one fresh registered comparison, one complete suite and three financial children over invented inputs; its event chain verifies 171 events. No investment result follows.

The outbound method is exactly `frozen_next_open_three_cost_development_suite`; the integrity category is exactly `verified_roster_and_current_specification`. The fixed prompt's exact operands, ordered comparisons, tie handling, fresh complete-roster requirement and missing-input refusal agree with the unchanged comparison implementation. This category concerns local roster/specification validation at packet preparation. It does not establish data accuracy, financial correctness, predicate truth or uninterrupted validity after preparation.

**Invalid evidence prevents another assertion.** An absent suite refuses before any model send. In separate runs, tombstoning the suite or corrupting normalized input bytes after the first response prevents the second packet: each retains exactly one dispatch and one proof binding, with no comparison or suite launch. A direct call using a configuration with the wrong bound policy revision also refuses after the actual suite validation. Thus an earlier valid observation is not reused to certify later stale evidence.

**Proof identity stays private and decisions remain free.** The reviewer inspects every captured outbound context. Suite and proof hashes, configuration/policy references, observation time, raw rationale, invented instrument/date strings, numerical result keys and predicate truth remain absent. Private verification observations never enter alias bindings. Seven nonexact category variants and four extra data/proof/outcome fields refuse; model output cannot author its own integrity field. A director stop and an engineer stop still produce invalid workflows with respectively one and three fixture sends and no financial suite. A data-critic block remains recorded while the complete seven-stage run finishes with `review_outcome=blocked` and `operational_acceptance=False`. The new fact does not compel execution or favorable review.

**Failure paths retain their exact proof basis.** Independent malformed-director and process-death probes each leave zero completed stage records but one durable packet/proof/configuration/request/assignment binding. At the injected transport boundary, the bound packet digest equals the dispatch hold's packet digest; the proof revalidates, and the binding event precedes budget reservation. Malformed output leaves the full hold uncertain; interruption leaves it reserved with no actual amount. Both retain verifiable journal chains, and same-key repeats refuse before transport. Successful stage records bind the same planned model request and proof. This independently checks the repair for the separate critic's P2 concerning proof lineage when response validation or handoff publication never completes.

## Acceptance boundary

This correction supports the truthful method description and the narrowly stated supervisor fact. Typed egress and exact private bindings are application controls for a trusted cooperating supervisor; they are not operating-system isolation, universal privacy detection, transmission-rights certification or account-wide billing control.

The original actual stopped attempt was not rerun or reclassified. This review establishes no claim that a real model will proceed under the new wording. A later actual cycle must preserve genuine refusal freedom and obtain its own observed trace, fresh calculation, numerical checks, distinct criticism and scope acceptance. Persistent research scheduling, protected evaluation and paper/live readiness remain separate work.

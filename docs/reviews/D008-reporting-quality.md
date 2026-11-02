# D008 review-summary reporting: independent quality

**The reporting-only correction passes independent targeted quality checks.** A workflow with no published review stage reports `not_reached`; a partial published review set reports `incomplete`; only four explicit published review decisions can produce a complete review label. A received final response without its published review cannot clear the workflow. No execution-quality blocker was found in this bounded change.

Reviewer: `/root/d008_broker_quality`, independent of the producer. Base checkout: `bc44fa9f8d7eada9f00077cb5793c7e031e885ff`, with the uncommitted byte identities below. This review changed no source or repository test and accessed no actual project runtime, private market data, environment file, credential, network or paid model. It used disposable invented fixtures. Earlier source-quality reports, actual traces and private verification harnesses remain unchanged; no third actual attempt occurred.

## Executed targeted evidence

Source Python **3.13.12**, pytest **9.2.0** and Ruff **0.17.3** passed:

- **22 broker tests in 25.03 seconds**.
- **22 CLI/integration tests in 3.06 seconds**.
- Repository lint and the reviewer-authored independent probes below.

A fresh noneditable wheel installation under Python **3.11.9** passed the identical **44 targeted tests in 27.41 seconds**, clean-tree lint and the same independent probes. The clean tree copied only public source, tests, docs, scripts and packaging files. Cached `uv` built and installed offline with cached pytest; no dependency download or network fallback occurred. `pytest -q -o pythonpath=` disabled source-path injection, and the imported package resolved under the new environment's `lib/python3.11/site-packages/quanto`, outside the repository.

The source commands were `pytest -q tests/test_research_broker.py`, `pytest -q tests/test_cli_requests.py tests/test_integration.py` and `ruff check .`. Installed checks combined those three test modules with `-o pythonpath=`. The existing Ruff checked the clean tree's `src tests`. No complete-suite rerun is claimed: the change is limited to summary derivation and its broker tests, and these targeted checks directly exercise the affected paths.

The observed wheel has **174194 bytes**, **33 entries** and SHA-256 `83617f5bbba72c853772aad1a829f955807e66e29a2899c975badcd79db58c29`. Its Python modules equal the tested source; it contains no runtime, database or environment entries. Final recorded source/clean-tree identities remained unchanged.

## Independent probes

The reviewer-authored `/tmp/d008_reporting_quality_probe.py`, SHA-256 `e0a87d21936a535f23719fcc77c32f2ddb86cf59b459f9bc8089de85b622ea97`, passes in both source and installed environments. It checks the complete 81 combinations of four supported review decisions against all 16 published-stage subsets: **1296 cases**. Empty published sets remain `not_reached`, partial sets remain `incomplete`, and complete sets preserve block priority, inconclusive findings and explicit all-clear decisions. Duplicate-role and unknown-decision inputs do not yield clearance.

An independent integration probe runs the real admission, suite, engine and broker on invented D007 source records with synthetic model transport. At the final scope response, it cancels the workflow before publication authority can be exercised. All seven response objects remain privately retained, but only three review stages publish and no scope handoff exists. The workflow reports invalid with `review_outcome=incomplete`; its already completed invented-data suite and three children remain retained. This validates the distinction between observing an answer and publishing an authorized review. It is software evidence, not an actual operational research cycle.

A separate engineer-stop probe reports `not_reached`, retaining the stop and launching no financial suite. An actual CLI process receiving an invalid request exits 1 and displays `review_outcome=not_reached` without echoing private request text. These checks exercise both ordinary early stopping and the exception path, where no reviewer decision should be inferred. The targeted producer suite additionally checks a parsed final scope response whose handoff publication explicitly refuses, and a partial review retaining a data-critic block while scope output is malformed.

## Exact reviewed identities

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/research_broker.py` | `d26ca8496ab50cb7536b28e2623fd4d8902d67ba3a3c7a93da9be01349924630` |
| `tests/test_research_broker.py` | `56953cbb463068678013ddb002375222dbf009e183e9da405b1fa67ced38583c` |
| `src/quanto/cli.py` | `7201b943efea1777c70e0fff7ce3d2e953089ba58648e360e53b5f6a22dabbd7` |
| `src/quanto/research_workflow.py` | `64ca63f155a2417021bb8632673f14ec12ff7d497881aa13a95d7330911ab02b` |
| `src/quanto/research_packets.py` | `acdab795bbb47c2002d50cf4872bd9c58775bafd832ace5f0903ed2649d92dde` |
| `tests/test_cli_requests.py` | `c54429143072ffb2539b4259f5f1892a002cd7d3fdc209932f2a2fc9deb5babf` |
| `tests/test_integration.py` | `4fd60a7d0364de028b6ac150717667f01583672def3d241d6b850062d7cd2840` |

Only `research_broker.py` and its broker test file change in this increment. CLI, workflow and packet implementation bytes were independently compared with HEAD and remain unchanged. The helper derives its summary from projections whose corresponding stage records have been published; it does not infer clearance from an empty decision collection or a raw response. Partial completion does not erase retained objections, and a complete blocked or inconclusive review does not become a favorable result.

The earlier actual attempts remain unsuccessful, with their original bytes preserved. This correction changes newly generated summary labels; it neither creates the missing reviews nor resolves the open memory/context gap. Actual-workflow acceptance, the fresh historical calculation and independent numerical checks, and R14 remain incomplete. No paid retry is implied by this quality result.

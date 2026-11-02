# D008 role-output clarification: independent execution quality

**Disposition: accepted for this bounded implementation.** Independently executed targeted checks passed in the isolated source and a clean noneditable wheel installation. The clarified prompt preserves the existing role decisions, exact selected-predicate rules, strict refusal behavior, private-response retention, frozen identities, egress boundary and spending limits. These checks use invented fixtures; they do not establish why an actual model violated the previous contract or authorize another paid run.

Reviewer: `/root/d008_prompt_quality`. Reviewed detached commit `75910f399333eb98f09b23f07715bec19c980cfc`, based on `37721ee286b95ecd8a1ea9a2f5ed0067fbe52ddf`, in `/Users/ronoktanvir/.codex/worktrees/role-output-clarification/quanto`. This reviewer owns only this new report in the primary checkout. Primary production source remained frozen for the separate actual numerical audit. No primary runtime/database, actual receipt or provider response, private data, environment file, credential or previous private harness was read. No provider/network call, dependency download, merge, cherry-pick, push or production/test edit occurred.

## Inspected change and contract

The complete isolated diff changes only `src/quanto/research_packets.py` and `tests/test_research_packets.py`. The source adds `ROLE_DECISION_BLOCK`, generated deterministically from unchanged `_DECISIONS` in `ROLES` order, and expands fixed `SYSTEM_PROMPT` instructions. An independent AST comparison against the base, excluding only those two assignments, matched the remainder of the packet module exactly. The parser, schemas, finite vocabularies, predicate set and size limits are unchanged. The broker, dispatch, failure-context, provider and financial modules are byte-identical to the base.

The new prompt explicitly states role equality, each role's existing decision codes, director-null behavior and both permitted hypothesis-stop forms. It names engineer and all four review roles as retaining the exact selected hypothesis predicate for every decision, including stop, block and inconclusive. Predicate retention is expressly separated from predicate truth or favorable review. The prompt preserves decision freedom and discourages agreement merely because preceding stages or integrity checks completed. It adds no populated example, default decision, fallback, output repair, extra egress field or retry.

Read governing `AGENTS.md`, CONTEXT, STATUS, ROADMAP, DECISIONS, HANDOFF and REQUIREMENTS, the role-output contract assessment, and the new separate critic/scope reports. Those reports informed scope and constraints; their executions were not substituted for this review's checks.

## Executed checks and installation isolation

Both environments used CPython 3.13.12 and pytest 9.2.0. The four-module targeted command covers packets, broker composition, dispatch and failure context:

```sh
PYTHONPATH=src:tests /Users/ronoktanvir/Documents/ChatGPT/quanto/.venv/bin/python -m pytest -q tests/test_research_packets.py tests/test_research_broker.py tests/test_research_dispatch.py tests/test_research_failure_context.py
```

Run from the isolated worktree, it passed **429 tests in 69.39 seconds**. Before execution, the packet import resolved to that worktree's `src/quanto/research_packets.py`, rather than the primary editable package. Full-worktree `/Users/ronoktanvir/Documents/ChatGPT/quanto/.venv/bin/ruff check .` passed.

A clean `git archive` of the exact detached commit was extracted into `/tmp/quanto-prompt-quality.xzzqz2`. `uv build --offline --wheel` built a wheel there, `uv venv --offline` created a fresh environment, and `uv pip install --offline` installed that wheel and cached pytest dependencies. No editable installation was used. The installed command was:

```sh
PYTHONPATH=tests /tmp/quanto-prompt-quality.xzzqz2/installed-env/bin/python -m pytest -q -o pythonpath= tests/test_research_packets.py tests/test_research_broker.py tests/test_research_dispatch.py tests/test_research_failure_context.py
```

Run from the exported directory, it passed **429 tests in 66.88 seconds**. The explicit `pythonpath` override prevents the project's pytest configuration from injecting `src`. The packet import resolved to `/tmp/quanto-prompt-quality.xzzqz2/installed-env/lib/python3.13/site-packages/quanto/research_packets.py`; distribution metadata identifies the local wheel URL without editable metadata. Every installed Python module was compared byte-for-byte with both the wheel and exported commit and matched.

The historical **1256 tests plus 12 subtests were not rerun**. The scope of this independent execution is the 429 targeted tests, lint, source comparison and additional probes described here.

## Independent temporary probes

The separate temporary harness `/tmp/quanto-prompt-quality.xzzqz2/independent_prompt_quality.py` imports only the existing invented-data fixture builders. It blocks credential lookup and the actual provider-send function; its only model transport is injected synthetic text. Its final five tests passed in both source (**5.46 seconds**) and clean installation (**5.01 seconds**), using the same source/installed path isolation as above.

**Decision and predicate matrix:** a separately stated seven-role decision map, the seven existing decision labels plus invented/invalid labels and types, all three supported predicates, null, a boolean and an invented predicate produced 1,260 acceptance/refusal checks. Another 42 checks attempted every unequal claimed/context role pairing. All **1,302 checks** matched the independent expected contract; 69 matrix cases were accepted. This covers all allowed decisions, every selected predicate, engineer stop and all reviewer block/inconclusive paths, different supported predicates, null refusal for dependent roles, director-null and both hypothesis-stop forms. The accepted role map also matched the rendered fixed prompt block.

**Strict final-stage refusal and retained history:** an invented transport returned an inconclusive data critic and a final scope response containing an invented decision and invented predicate. The workflow remained invalid with incomplete review, seven observed responses and six published stages. Its exact rejected scope reply remained in a private response artifact. Scope's effect and reservation remained uncertain, the reservation retained its complete **81,079 microUSD** bound with no settled amount, and the effect published no artifact references. The earlier data-critic projection remained inconclusive. A same-run repeat refused before any extra transport call; all reservation rows remained identical.

**Identity propagation and refusal:** all seven assignment contracts used the new prompt hash, all seven prepared outbound bodies contained the exact new prompt, and all seven predispatch failure-context observations retained the new prompt/source implementation identity. Body hashes matched the actual captured synthetic request bytes. The durable private broker configuration retained the current code identity. A contract bearing the exact old prompt hash refused before any reservation or send. Separately registered synthetic basis/context records were created under the old prompt and packet-source identity, verified under that identity, then rejected under the new one: both a hypothesis context with its old basis and a director context without a basis refused, and preparing an engineer context from the old basis also refused. Old records remained unchanged.

**Complete outbound-body privacy:** every complete captured request body, including system text and serialized context, was checked against 99 exclusions covering private fixture rationale/market-detail sentinels, suite/failure identities, local fixture path, alias target digests, private proof/context/basis references, rejected reply identity/tokens and predicate-outcome field names. None appeared. The private scope response was absent from effect outputs. These are synthetic egress assertions, not a claim of OS isolation or inspection of actual private requests.

## Request and reservation bounds

The independent bound starts with the unchanged maximum schema structure: 32 aliases, 16 nine-field failures, six prior outputs and eight findings per output, each with up to 32 aliases. Legal value strings are fixed ASCII codes without escape characters; JSON quotation marks are the only additional content escaping. The fully populated structure contained 4,480 quotes. An independently derived overcount of **4,558** covers every top-level scalar and every failure value as if it were a string, including booleans, plus the complete collection expansions. Adding that expansion bound to the unchanged 24,000-byte packet ceiling and each prepared empty-content wrapper gives:

| Model | Conservative complete request bytes | Conservative reservation, microUSD | Existing request limit | Existing role limit, microUSD |
| --- | ---: | ---: | ---: | ---: |
| `claude-haiku-5-5` | 34,650 | 105,306 | 40,000 | 125,000 |
| `claude-opus-5-5` | 34,649 | 883,400 | 40,000 | 1,000,000 |

These reservations apply the unchanged conservative local formula, its 65,536-byte allowance and output-token ceilings of 2,048/4,096. No limit or rate was increased. A valid dense 23,786-byte context also exercised actual preparation: Haiku produced a 33,168-byte request with a 103,824-microUSD reservation; Opus produced a 33,167-byte request with an 871,544-microUSD reservation. Each stayed below the independently computed conservative bound. These are software reservations for cooperating project callers, not invoices or controls over unrelated account use.

## Failed attempts and limitations

Early executions of the temporary harness encountered two reviewer assumptions: the invalid broker summary intentionally omits `code_identity`, which instead resides in its durable configuration; and the populated structure had 4,480 quotes rather than the initially asserted exact 4,488. The retained logged early run reports **2 failed, 3 passed**. The harness was corrected to inspect the durable configuration and derive an explicit conservative structural overcount. Only temporary probe code changed. The final probe version then passed in both environments. No product test failed and no implementation correction was needed.

One artifact-hash shell command encountered the host's unsupported `C.UTF-8` Perl locale; Python hashing replaced it. An initial archive/build command found `uv` absent from that worktree shell's path; the absolute installed `uv` path succeeded offline. An attempted poll used a nonexistent session identifier and returned no test evidence. Initial live-output runs were repeated with retained log capture; only the completed recorded executions above support the reported results. These tooling failures are not concealed as product passes.

This review accepts a routine D008 clarification. Separate criticism, quality and scope remain distinct roles. The frozen actual numerical audit and ordinary integration checks remain lead gates; this report neither performs that audit nor certifies the actual model's quality stage. No finding here establishes that prompt ambiguity caused the actual scope refusal or predicts that another response will comply. All actual attempts remain invalid/incomplete; R14, protected evaluation, persistent scheduling/restore, paper/live readiness and the full operation remain unfinished. No new paid attempt is authorized.

## Exact identities

| Artifact | SHA-256 |
| --- | --- |
| New `src/quanto/research_packets.py` | `dbfa9010a52581c78179f2e9b2451ebfc1143cbb915437104d7efeaaf58e97eb` |
| New `tests/test_research_packets.py` | `06c20179370ce6233bd5cf3cd2f096852c603f1cb77413b07bf94038c8d2e428` |
| New fixed `SYSTEM_PROMPT` (5,942 UTF-8 bytes) | `a1b540249cffad25f8bac66f28dd91b6f7a65041a3d22efd16d9401aa47f6d80` |
| Old fixed `SYSTEM_PROMPT` (4,700 UTF-8 bytes) | `3f0c056e00b1a8565871e811d481b5988122298d335ad74b47e4e34d3089b057` |
| Unchanged `src/quanto/research_broker.py` | `aa4f9e93f9fc471273bf2e6c1a0d67acb74583228618cecd17aa9ec513419e34` |
| Unchanged `src/quanto/research_dispatch.py` | `120834deb63abebeeb54a14f8cf470ad43fd9ac1f44979ee96fe9c88ba20c1f1` |
| Unchanged `src/quanto/research_failure_context.py` | `b99af35355b14d638770c069791124a8d72774346e5a9677ac74d607bc777208` |
| Unchanged `src/quanto/provider.py` | `5f4f214d079bd4a17ddc3049163d5a3bfc9acd8ba2508a3dfe2f5ad5c4c0ace0` |
| Unchanged `src/quanto/research_comparison.py` | `c2e933841f1664b62528b4342b37a34e7b3452e7783d91f495f78a6b05d65446` |
| Unchanged `src/quanto/event_engine.py` | `cb1a61985ebb08089eab50d00d1e78f09a83fdea6754587af7e871e177175ffc` |
| Final temporary independent quality probe | `2bc241b53da88ff87d85c015dd76039d754d3745550381165523642691e4f394` |
| Clean built wheel | `343bc6d05a9b6748ed4fd9bdbb5f0b2ba4ed94178fefa9925304fb5f22c90bd8` |

The isolated worktree remained clean. Only this new review report was written in the primary checkout; the primary packet module retains its prior operational-source identity.

# D005 independent quality validation

Reviewer: `/root/d005_quality`, separate from the producers and implementation critic. Review date: 2026-11-02 UTC. Scope: the D005 acquisition, provenance and registered-exploration increment. No implementation files were edited by this reviewer.

**Result:** no remaining quality blocker was found at the identities below. The complete suite passes 364 tests and 12 subtests, lint passes, and a wheel built offline runs the synthetic workflow outside the checkout. This is software validation; it does not establish historical-data admission, provider entitlement, rights, strategy performance, or completion of the private operation.

## Inspected identities

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/provenance.py` | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |
| `src/quanto/alpaca_data.py` | `8ef36538adcb424928a95116d66835387eedb98cc27b5b67e624825875bc015c` |
| `src/quanto/explorer.py` | `47a9d6b6921418f997e8cdbc1f52f820a4e991dda52b7bc58704c2065c0e0808` |
| `src/quanto/cli.py` | `bb083af70627d21f70d37e55ee38490a0183d33150e1a0eb50255f27664dbaa6` |
| `scripts/configure_alpaca.py` | `fc2482e2356bcc66f6576d2b0f66b8958b21425b672cf68e9718251734626fb2` |
| `examples/synthetic_exploration.py` | `4b07deb2063bea54da092bde51866073e435223159480978b6c61a9758fd7af6` |
| `tests/test_provenance.py` | `fb40af9a10e7d31129a8fa4f284a8994226d9fdd0c2f1f88dafc8c87316d18f0` |
| `tests/test_alpaca_data.py` | `909a7655cab13b05f88fddcb581d93ee012b7ca5765429c9c2d2f8b002bdb6f0` |
| `tests/test_explorer.py` | `8132664b573d004d44ace43d3c1fad774c647e35d7069bddd8d748a3a19abd05` |
| `tests/test_cli_requests.py` | `34b3be6be7503335ece34dd9f1c130a95a578d61e4c7b82a1d16834939e224be` |
| `tests/test_configure_alpaca.py` | `4457c58e35d51dcc1d3b6113b0af1c88220dcced67f9499898ce08420ef75fe3` |

## Executed checks

- `PYTHONPATH=src .venv/bin/python -m pytest -q`: **364 passed, 12 subtests passed**, 4.41 seconds, on the frozen implementation.
- `.venv/bin/ruff check .`: all checks passed.
- `git diff --check`: passed.
- Focused acquisition, request-file and credential-helper suites: 67 passed after the final acquisition/CLI/helper changes. Focused explorer/provenance suites: 82 passed after their freeze. These are subsets of the complete count, not additional tests.
- A read-only scan of 66 then-visible tracked and nonignored untracked files found no private-runtime paths or obvious credential-pattern matches. It deliberately excluded ignored files and did not inspect the real `.env`, runtime database, or market artifacts. This limited pattern check is not a complete secret or publication audit.

The reviewer also ran independent temporary fixtures, rather than relying solely on producer tests:

- An injected two-page acquisition saw a committed pending submission before transport. A second-page HTTP 429 produced a failed receipt after exactly two calls, retained the exact first-page bytes and their hash, and did not retry. Fake credentials and the private error-body marker were absent from all saved temporary-store bytes.
- Five disallowed routes were rejected before the injected transport: POST orders, GET orders, a lookalike data host, a user-info URL, and plain HTTP. A malformed JSON request containing a fake secret produced a retained invalid submission without retaining its raw secret-bearing text.
- Persistent failure of the `attempt_finished` event rolled back terminal publication. Reopening the store showed a pending submission and no attempt outcome. The error propagated rather than claiming success. A deliberate subsequent run used a new attempt for the same candidate; the candidate/execution counts were one and two. A query over a warmup-only date returned all three full-range registration/access records. This probe was rerun on the frozen revision.
- The event chain verified after the temporary acquisition and exploration scenarios. This checks event consistency, not immutable storage or independent authentication.

## Defects found and rechecked

**Loaded defaults were missing from code identity.** In a temporary copied package, the reviewer imported the engine, changed only `_number`'s keyword default `positive=False` to `True` on disk, captured the identity, reloaded the modules, and captured it again. Before correction, the identity stayed equal although a zero-volume bar changed from accepted to rejected. The producer added default and keyword-default identities. The same independent reproduction now reports different identities and the expected changed behavior. Unsupported loaded defaults fail explicitly.

**The synthetic example failed on a new directory.** Calling the example with a nonexistent output root initially raised a provenance storage error. The lead added directory creation. The installed-wheel check below executes the example on a fresh directory and passes.

The reviewer confirmed the intended persistent-storage-error contract with the producer: an error that prevents even an interrupted outcome propagates, while durable submissions remain pending. It is not reported as a completed failure or silently retried.

## Clean package verification

Only `src`, packaging metadata, README and the dependency lock were copied into a temporary source tree. `uv build --offline --wheel --out-dir ...` built the wheel with cached build dependencies. Python 3.11.9 installed it with `pip install --no-index --no-deps --target ...`. Execution then used a separate working directory and only the installed package on `PYTHONPATH`; the imported package's resolved path was verified outside the checkout.

The resulting wheel was `quanto_research-0.1.0-py3-none-any.whl`, SHA-256 `5194c024f998b02976b2ccd2fda7ed0e1397646d36501000fc165e1fc8b0ae32`. It contained the new modules and website assets, with no data, runtime, private, or `.env` paths. This hash identifies this particular build, not a claim that wheel timestamps are reproducible.

The copied synthetic example completed on a fresh root. Two lookbacks had warmups of two and four sessions but identical evaluation dates, 2024-01-05 through 2024-01-12, and identical benchmark reports. Its renamed retry reused the first candidate fingerprint; final counts were two candidates and three executions. The malformed submission remained invalid. Installed CLI help included acquisition and exploration commands. All result artifacts remained labeled `synthetic_fixture` with `investment_evidence: false`.

An initial QA path assertion compared `/var` with macOS's resolved `/private/var` spelling. Canonicalizing both paths repaired that assertion; it was a validation-script issue, not a package failure. The final installed-wheel run passed.

## Limits that remain

No real credentials, actual project runtime, provider service, paid model, or broker order endpoint was accessed by this reviewer. Any real acquisition receipt is separate evidence owned by the lead. The socket/deadline controls do not impose a hard process-level DNS timeout. Data rights, corporate actions, historical information availability, certified exchange coverage, stable issuer mapping, protected final evaluation, persistent research roles, and prospective paper operation remain outside this increment's completed claims. Local-owner filesystem/database authority is outside the application controls' threat model.

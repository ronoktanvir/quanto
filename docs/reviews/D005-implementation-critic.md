# D005 implementation criticism

Reviewer: `/root/d005_critic`, a separate native agent from the implementation producers. Scope: provenance storage, Alpaca acquisition, registered exploration, CLI integration and local credential setup. Review began on 2026-11-02 UTC. This review used source inspection and synthetic temporary-directory tests; it did not read actual credentials or market values, contact a provider, place orders, or change the live service.

## Final conclusion

No remaining implementation blocker was found for the D005 bounded acquisition and synthetic exploratory increment on the final artifacts listed below. The independently reproduced code-identity, nested-transaction, mutable-request, pending-exit and setup-read defects were corrected and rechecked. This is approval of the implemented scope, not certification of historical research admission, investment performance or a complete operation.

## Findings and corrections

### Loaded code can differ while the recorded identity stays equal

On `explorer.py` SHA-256 `e515d24801578ea37d8d172f9940d2650eb074474683c5d532d210a1cec929eb`, the identity hashed current source files and only the `run_backtest` entry point's bytecode. Source files can change after a module has been imported, while Python continues using previously loaded helper functions.

An independent reproduction copied the package into a temporary directory, imported it, changed only `_target` on disk, then compared execution before and after reloading. The reported code identities were identical, while the same explicitly synthetic fixture produced ending equity of 10588.235294117649 before reload and 10000.0 afterward. This demonstrates an identity mismatch, not a market result. The correction must identify loaded helpers and class methods as well as source files. The separate quality reviewer also identified keyword-default identity as a required part of that correction. The final implementation fingerprints loaded helpers and class methods, positional defaults and keyword defaults. The independent copied-package reproduction now reports distinct code identities for the distinct executed helpers while disk identities remain equal. The keyword-default regression also passes.

### Joined transactions must preserve outcome/event atomicity

The first transaction-aware `Provenance.finish` revision joined an existing transaction through `nullcontext`. An independent synthetic check forced its event write to fail and caught that exception within the caller's outer transaction. The outer commit preserved a terminal failed outcome with zero corresponding completion events. This contradicts the storage contract that a failed event write rolls back the record. A nested savepoint can preserve that local guarantee while retaining atomic completion across explorer records. Explorer's own completion wrapper propagated the error; the defect concerned the generic storage API when an outer caller handled it. The final implementation uses a unique nested savepoint. Repeating the independent reproduction now leaves the submission pending with its event chain intact. The combined submission/attempt publication regressions also pass.

### Mutable acquisition requests can diverge from their submission identity

On Alpaca SHA-256 `88c60d80be6295767c8cc9de65c239a5d528135c0bb89de98b7574cad52bb2eb`, a caller-supplied dictionary was hashed at submission and read again later. A synthetic clock callback changed `symbol` after recording; the submission identified AAPL while the successful acquisition requested MSFT. The later request manifest accurately identified MSFT, but the initial intent was not frozen. The lead corrected this by freezing dictionary input once to canonical text and using those same bytes for recording and parsing. The CLI pilot used immutable file text and was not exposed to this dictionary mutation.

### Pending publication returned a successful process exit

The initial CLI returned exit code 0 when an acquisition returned `status: pending` and `error: storage_unavailable`. A synthetic mocked adapter reproduced this. The lead added pending to nonzero outcomes and a regression test, so shell callers cannot treat an unresolved receipt as completed acquisition.

### Credential setup read an unbounded or special file before checking it

The initial helper used `Path.read_text()` before its size check and rejected only symlinks. A FIFO could block, and an oversized regular file was fully read first. The lead replaced this with no-follow, nonblocking file-descriptor access, regular-file and size checks, and a bounded read. Synthetic tests cover these cases and preservation of existing settings. No actual credential file was read during this review.

## Confirmed boundaries

- Acquisition enforces exact GET methods, hosts and paths before either production or injected transports. The paper-host exception is the calendar path only.
- Credentials come from a private regular local configuration file, without environment fallback or export. Non-200 bodies and detected credential reflections are withheld from artifacts.
- Safe raw pages precede semantic parsing and remain linked on later failure. Redirects, automatic retries and feed substitution are absent.
- Acquired history remains inspection-only. Registration checks explicit source-envelope classifications, and historical execution is rejected with the outstanding admission requirements.
- Exploratory fixtures share requested evaluation dates and benchmark windows across lookbacks. The whole declared dataset range is recorded as development exposure; renamed studies and revised bytes do not clear that exposure for the same declared instrument.
- These controls apply to cooperating local callers. They do not prove provider accuracy, data rights, permanent issuer identity, protected holdouts, investment performance or isolation from the filesystem owner.

The adapter documents that socket timeouts do not provide a hard process deadline for an OS DNS stall. That limitation is accepted for the bounded manually initiated pilot and must remain visible before unattended acquisition scheduling.

## Verification record

After the final producer freeze, the independent targeted command passed **149 tests** across `test_explorer.py`, `test_provenance.py`, `test_alpaca_data.py`, `test_cli_requests.py` and `test_configure_alpaca.py`. Ruff passed for those tests and the five reviewed implementation files. Independent copied-package and caught-nested-event reproductions confirmed both principal fixes. Earlier 100- and 102-test checkpoints preceded the final explorer/savepoint changes and are superseded by this result. These counts describe synthetic software checks only; actual provider receipts are separate lead evidence. No whole-repository or remote CI claim is made by this review.

## Final inspected artifact identities

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/provenance.py` | `488d1fe28fb19a7c308dcdb9233ca6db4096ef0ecb157379bfa4001467d74dcb` |
| `src/quanto/alpaca_data.py` | `8ef36538adcb424928a95116d66835387eedb98cc27b5b67e624825875bc015c` |
| `src/quanto/explorer.py` | `47a9d6b6921418f997e8cdbc1f52f820a4e991dda52b7bc58704c2065c0e0808` |
| `src/quanto/cli.py` | `bb083af70627d21f70d37e55ee38490a0183d33150e1a0eb50255f27664dbaa6` |
| `scripts/configure_alpaca.py` | `fc2482e2356bcc66f6576d2b0f66b8958b21425b672cf68e9718251734626fb2` |
| `tests/test_explorer.py` | `8132664b573d004d44ace43d3c1fad774c647e35d7069bddd8d748a3a19abd05` |
| `tests/test_provenance.py` | `fb40af9a10e7d31129a8fa4f284a8994226d9fdd0c2f1f88dafc8c87316d18f0` |
| `tests/test_alpaca_data.py` | `909a7655cab13b05f88fddcb581d93ee012b7ca5765429c9c2d2f8b002bdb6f0` |
| `tests/test_cli_requests.py` | `34b3be6be7503335ece34dd9f1c130a95a578d61e4c7b82a1d16834939e224be` |
| `tests/test_configure_alpaca.py` | `4457c58e35d51dcc1d3b6113b0af1c88220dcced67f9499898ce08420ef75fe3` |
| `docs/RESEARCH_PROTOCOL.md` | `7a4cce12ebc9d454b9ddd8697fb8a9c43908357f3daf7338a818eaddbbe9928d` |
| `docs/PROVENANCE.md` | `e2d055172d93f8e65d0825d9622f726f854c9cb28ba8ffa5203feba89f346260` |
| `docs/DATA_SOURCES.md` | `a44a4db6b8f964afaadd867fc83691014039bf5dcef4c36e97d9ed3c63d20adc` |

The review preserves objections and their corrections rather than replacing the initial findings with a claim that the first revision was already sound. Later changes to these files require an appropriately scoped recheck.

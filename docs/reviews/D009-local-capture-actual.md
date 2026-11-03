# D009: first actual local research snapshot

The lead executed one local capture and read-only inspection successfully at **2026-11-03T00:25:33.892493Z**. The snapshot contains all **40 research-database tables and 229 canonical objects**. Captured and independently reopened inventories agree; database integrity, event-chain integrity, file digests and the supported database-reference checks pass. No model call, financial replay, upload or worker restart occurred.

This is operational preservation evidence from the existing research store, not a new financial experiment. It does not change the evidence kinds or outcomes of the captured experiments. The source and tests had already passed separate criticism, quality and scope review. The lead executed the actual command; independent post-execution reviewers receive only a fixed safe metadata projection, not the private database or object payloads.

## Exact identities

| Artifact | SHA-256 |
| --- | --- |
| Capture module | `5f7f2526da8d82d5f648c42a3135af3f44dadbafe0be2f40e8888b923d856883` |
| Product tests | `6edb1e99f37f28eda64fcbe233c12693ae4fd5917130edda63663cff081a0e8a` |
| One-time controller | `817699781b5bcd8b770314d95ed75cc17b6070098facbafb36f894040714b6ff` |
| Private attempt receipt | `ccd21590fdd92590cc21cd4e19bc8b98148fed4568f01273d8b4efd4e6c3d334` |
| Private result receipt | `81c7740ba22d83e4d7874e618c0a51ab0051b6ef1f08a5297fdc8befdd018d54` |
| Private process receipt | `23aaa0264237d9e9b2052cac2e0fc7cd8494892aa8849a435b879bd0d43df7d7` |
| Safe review projection | `d762aef9ba80b01dd5779c9c802ff2d6e92d3e8c7e4f9ec1ee870a37361a3c51` |
| Snapshot manifest | `d4f6f88495f2337f6edc5f7764b4ddab465e64136b5798f6c98a3a72ccdcd87e` |

The captured event head is `f5d63033df2295da89984e76420c92e83b5ee54383214f96fbcf2c0ef440bbc2`. It identifies this captured state; it is not an externally trusted newest-state witness. Private receipts remain under ignored `runtime/d009-capture-actual/`. The snapshot itself is in a new private sibling directory outside the repository, whose location is recorded privately. The consumed controller must not be rerun.

## Execution and interpretation

The process started at 00:25:33.668421Z and ended at 00:25:33.909716Z with exit 0, no timeout and zero stderr bytes. It ran Python in isolated mode with only PATH, LANG and LC_ALL in its environment, no stdin, and exclusive private output files. Socket and DNS calls were denied by an application guard; this is not an operating-system network sandbox. The capture used SQLite's online backup API under the reviewed read-before-write lock ordering, then reopened the copy read-only without application constructors or effect resumption.

Zero unknown table schemas and zero tombstoned dependencies were observed in this generation. These counts do not establish complete nested document coverage: the inspector checks a declared database-reference subset, and every available canonical nontombstoned object is copied conservatively. All captured table state, including prior-day uncertain holds, consumed dispatches and failed work, is preserved rather than reset.

The final product passed 44 focused tests and 16 independent probes on source Python 3.13 and clean installed Python 3.11. Earlier full-suite results and the discovered Python 3.11 compatibility failure remain separately recorded in the [quality report](D009-capture-quality.md); they must not be presented as a final-revision full-suite pass. Final GitHub CI will supply its own exact-revision evidence.

## Remaining recovery boundary

`typed_closure_complete`, `full_recovery_accepted`, `off_mac_recovery_verified` and `execution_enabled` are all false. No project bytes have been uploaded. Nested document validation, required external runtime audits and council receipts, legacy evidence, historical source/dependencies and selected-use rights remain unresolved. Conversations and session continuity are explicitly excluded from this research-store candidate. Configuration credentials and recovery keys are excluded deliberately.

The owner has the existing key open locally and will handle its storage; an off-Mac retrieved-copy check and account recovery are unconfirmed. Encrypted packaging, exact-ciphertext transfer and a downloaded isolated restore remain future work. Stage C additionally requires external effect records, fencing and a separately reviewed freshness boundary. This successful local copy closes none of those gates and does not complete R14 or authorize trading.

Post-execution independent projection audits are recorded in the separate [quality](D009-capture-quality.md) and [scope](D009-capture-scope.md) reports. Their review of lead-executed metadata is distinct from their synthetic execution checks and from direct inspection of private actual payloads.

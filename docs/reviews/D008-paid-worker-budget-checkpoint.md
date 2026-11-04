# D008 paid worker budget checkpoint

The worker now binds launch planning to one SQLite read snapshot. The budget receipt adds `event_count`, `event_head_sha256` and `purpose_allocation_max_rowid`; the six-field prelaunch receipt and existing call-entry digest bindings remain unchanged. No actual entrypoint, private state, credential or provider call was used.

`headroom()` refuses an already active transaction, then explicitly begins a short read transaction on the existing journal connection. The Los Angeles day, global ledger snapshot, maximum allocation rowid across the complete purpose table, research-purpose sum and verified journal head are observed together. A missing purpose table binds rowid zero and zero usage. The observation timestamp must remain within the selected day. Success commits before receipt publication; exceptions roll back the worker-owned transaction. An existing caller-owned transaction is refused without rollback.

The later prelaunch verifies the event chain again. Its count cannot precede the budget checkpoint; an equal count requires the same head, and a larger count requires the checkpoint's head at the corresponding historical event row. The empty prefix requires the canonical zero head. Current Los Angeles day is checked before and after this verification. Later competing calls may add legitimate ledger events and purpose allocations; the fixed checkpoint rowid and event head let the auditor reconstruct the earlier observation without treating those later calls as part of its planning state. Neither receipt reserves funds or measures unrelated account spending.

The final producer run passed **54 invented cases in 0.42 seconds**; Ruff passed. A targeted concurrency case uses the real public `Journal` implementation on temporary invented SQLite stores. The test deliberately enables WAL to permit another connection to commit a reservation, journal event and purpose allocation between the observer's SELECTs. The receipt retains the old coherent global/purpose/head snapshot, while later prelaunch verification accepts the legitimate extension. WAL is confined to this concurrency fixture and changes no actual project setting. Other new cases cover event/head replacement or reversal, missing purpose table, midnight rollover, exception rollback and refusal to disturb an existing transaction. All prior worker tests remain included.

The immediately preceding source, tests and correction report were preserved byte-for-byte under ignored `runtime/development-cycle-launch-preparation/paid-worker-pre-budget-frozen/`; the original first-version freeze also remains. The earlier [integration-correction report](D008-paid-worker-correction.md) is unchanged. No new producer test failure occurred during this increment. These are producer software checks; they do not establish independent acceptance, actual private readiness, numerical economics or an operational cycle.

| Artifact | SHA-256 |
| --- | --- |
| Final `paid_worker.py` | `7aa4e43c5a4453fad118d29f379fd5b1ba08d2b0cd5af0a955e2baa2c106c883` |
| Final `test_paid_worker.py` | `27c62e3b323c2d2dd585033eea0263c6098793ff92006174383eed9309619247` |
| Preserved preceding worker | `09afd6f6e2da6e293b912798a22c9611c12fd6d7bfc74d60b9948dc9e0cbb21f` |
| Preserved preceding tests | `99d61c6d42dbf2a96c5c0743136914ee37473dd0a4801b80adf022e35a5de4d5` |
| Preserved preceding correction report | `3a89856e26672cfb72ae7fae4efeb01183915dad97df23c45538d3766923657c` |

Separate combined launch/auditor review remains required. The checkpoint authenticates a cooperating-process observation; it does not protect against hostile owner-level rewriting or replace atomic per-dispatch budget checks.

# Research database permission correction

The existing research database is now owner-readable and owner-writable only (`0600`). The lead invoked the separately inspected metadata helper once at 2026-11-03T10:27:43Z. Its retained intent and result bind the same regular, single-link, owner-held file and report a change from `0644` to `0600`. A subsequent metadata-only check independently observed `0600`; no failure receipt exists.

The helper SHA-256 is `23a9b375cb12de8fc4398ea85a456d2c8bec18f907cbccd7bfc62cb3519305ea`. [Independent source criticism](D008-next-development-cycle-critic.md) found no necessary correction. The helper opens the file through a no-follow descriptor, changes only that descriptor's mode, verifies its identity and publishes exclusive receipts. It contains no database-content read, SQL operation, model request or financial calculation.

The original outer terminal response was truncated during context transfer. Its exit status is therefore **unverified**, even though the saved result and current mode agree. This is not recorded as a clean, fully observed controller completion. The helper is consumed and was not repeated to manufacture that missing observation. The later metadata observation establishes the present permission prerequisite; future preparation must independently check its existing database, sidecars and authority.

Neither the helper nor the subsequent check establishes concurrent content stability, complete access isolation, reconciliation of old exposure or protected eligibility. The private receipts remain under ignored `runtime/development-cycle-preparation/`. Original intent, result and any uncertainty remain retained.

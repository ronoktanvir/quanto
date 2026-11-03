# Root-shape diagnostic: independent quality audit

The safe projection consistently records a completed diagnostic that observed a refused root predicate. It does not record successful root collection or closure. The observed site, frozen `_Reader.roots` line 356, requires each recognized event to contain its registered reference field. This identifies the predicate class, not the particular event kind, field, row or correction.

Reviewer: `/root/recovery_actual_quality`, separate from the diagnostic author and actual executor. I read only the specifically permitted projection and diagnostic/frozen public source. I independently checked hashes, strict JSON parsing, internal receipt references, chronology, reported limits/flags and AST call sites. No product code or tests were rerun; no actual candidate, underlying private receipt, market payload, account or key was accessed. Actual execution and private binding checks remain lead-attributed.

The projected controller identity matches source `5baa8758…`. Result/attempt, process/launcher-intent and stdout/stderr references agree internally. The process records exit 0, no timeout, zero stderr and 0.076342 seconds, from `2026-11-03T02:30:40.072202Z` to `02:30:40.148874Z`. The result observation falls between those timestamps; the projection follows them. Diagnostic completion is true, but root completion, closure acceptance and full recovery are false. The recorded code is `malformed_supported_profile`, with exact frozen locations `need:43` and `roots:356`; trace truncation is false.

Source inspection confirms one direct `reader.roots()` call and no call to the full inspector, base snapshot inspector or graph walker. The diagnostic checks exact manifest/database bytes and schema before root collection, then rechecks identity and source after the observed refusal. It retains the 45-second overall and 15-second identity-check allowances, plus the existing row/graph/JSON bounds. These are cooperative software checks, not proof that every blocking filesystem operation is interruptible. The traceback observation compares known code objects and publishes fixed location/predicate labels without frame locals. No object graph is published.

Reported aggregates—864 row observations, 3,007 JSON-item observations, 2,029 registered edges and 93 gaps before stopping—describe this interrupted root scan. They are not complete coverage, unique-row counts or a verified graph. The result preserves false capture/copy/upload/replay/execution/offline/full-closure flags, possible operating-system retrieval and the original failure's unresolved cause. The earlier consumed inspection is not superseded.

Accept the bounded diagnostic report. Determining whether the inspector or a producer representation is wrong still requires public writer/schema evidence and a synthetic reproducer. This audit does not authorize an inferred compatibility relaxation or certify a future correction.

| Inspected artifact | SHA-256 |
| --- | --- |
| Authorized root-shape projection | `2385159aedbff76df90e4a67b1f4a47812933b48c656f65355b1fd6d8f96611b` |
| Consumed diagnostic source | `5baa87582ce6f2f73489f4082121819eb09c965f6053d3a8c9e11bacac8cfb6a` |
| Frozen closure source | `3618457a9170f0533efe0b4081478a3662dfd7f6031525dce24f488a28cd8981` |
| Frozen recovery source | `5f7f2526da8d82d5f648c42a3135af3f44dadbafe0be2f40e8888b923d856883` |

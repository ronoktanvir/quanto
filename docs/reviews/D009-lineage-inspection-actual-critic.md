# D009 actual lineage inspection: independent metadata criticism

The permitted safe projection and public report consistently describe one completed, **incomplete structural inspection**. No required correction was found within this metadata-only scope. The private verification remains attributed to the lead; this review does not independently certify the graph, receipts, process state or actual data.

Reviewed by `/root/rollout_controller_critic`, separate from execution, preparation and quality. Exact inspected artifacts:

| Artifact | SHA-256 |
| --- | --- |
| `docs/reviews/D009-lineage-inspection-actual.md` | `5b211e7638ea5a942865d2c49b259a824c22e9b19c3ab1b74e773367e8f67cc0` |
| Permitted `runtime/recovery-closure-lineage-actual/safe-evidence.json` | `e91255c29c80aafc6b70e56447a65bf321e715d05027a927a421619f72cca6d2` |

Both artifacts report 347 nodes, 3,281 edges, 61 supported structures, 370 reason/origin gaps and zero tombstoned edges. Their earlier counts also agree. Multiple gaps can concern one node, so the gap count exceeding the node count is not an inconsistency. Neither the added supported structures nor the smaller gap count measures a percentage of recovery completion.

The reported child `9e0b4ceb88cebd785f6da14e442f6c86fdc4ea2f0d37b5db4c41ef0e828c87d6` and launcher `d8940d31d587a94d599cb7ed733d7a90efdc503ae84a932b454ad7908d01d5bb` match the exact preparation versions previously inspected by this critic. The projection's three source hashes, original manifest and event head also match that prepared contract. Loaded hashes and Python/SQLite metadata are present, but their agreement with the actual process was checked by the lead, not reproduced here.

The projection reports outer and child exit zero, no timeout, a reaped child and a later absence check. Its roughly 0.197-second child receipt interval is consistent with the separately recorded inspection and longer launcher elapsed values; none is presented as the outer tool's wait duration. All nine aggregate checks explicitly retain lead attribution. I did not observe original tool chunk `4e0438` in this audit or follow any receipt hash to its target.

The report preserves the erroneous serialization copy of the outer observation and distinguishes its corrected transcription from original actual receipts. The projection records that correction as retained. This supports honest failure reporting; it does not independently verify either private copy. No rerun or supersession of earlier failures is claimed.

Status remains incomplete, and the exposed typed/full/off-Mac/offline recovery, control-store, evaluator/historical replay, execution and upload flags remain false. The older research generation does not restore newer D008 authority or external freshness evidence. Rights, external key/account recovery, complete dependency coverage and downloaded restore remain unresolved.

Only the two identified artifacts were opened for this audit. No private graph, original receipt, database or process was inspected; no controller, test or replay was executed. All actual controllers remain consumed. Acceptance here is limited to consistent reporting and appropriately qualified attribution.

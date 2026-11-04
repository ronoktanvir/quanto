# Manual research cycle supervisor correction

The second supervisor requires positive proof of child ownership before either registration or paid work can start. The first version could enter the broker before the parent had recorded a process handle. Its worker could also use a stale wall-clock or spending-day check. The original source, findings and rehearsals are retained. [First criticism](D008-manual-cycle-launch-critic.md) · [First quality review](D008-manual-cycle-launch-quality.md).

The parent creates a private pipe for each child. After starting the child, it durably records the actual PID, parent PID, launch identity and start receipt. It then sends one byte through the pipe. An interrupted spawn closes the write end and gives the child no grant. A child also checks the current process relationship and the receipt identities. The registration helper now runs in a separate child. The parent can observe wall and monotonic expiry while that helper is busy.

The paid worker rechecks ownership, its original deadline and the prospective Los Angeles spending day at broker entry, authorization and send boundaries. Only the worker that successfully creates the durable consumption record may publish an outcome. The budget observation includes a verified journal prefix and the last purpose-allocation row visible in the same read transaction. A request already in flight can leave uncertain charges.

The plan selects one audit attempt and pins the corrected six-module auditor. The auditor manifest must also match the parent and paid-worker source identities. The real auditor will need the externally observed parent exit and the prospective receipt chain. [Worker preparation](D008-paid-worker-v2-preparation.md).

## Exact producer evidence

| File | SHA-256 |
| --- | --- |
| `supervise.py` | `43f992b081fe7bd5f23d6163dafd5827d265630a6b3049ecf58857eaa802d830` |
| `paid_worker.py` | `9a59cb3eb37f8b6f06d17abde2a474da13fba07264bd37c634ee12a07f0cd01c` |
| `test_supervise.py` | `af7f64b4e2ea6461f93fc3b9cadcf8c88523276b663fce50c58450430f4baa48` |
| `test_paid_worker.py` | `7694ff9ada310d5c27c84cca5907464099475c5cbbc1c09b4b6180a723669c1a` |

The final combined run passed **91 invented-data cases in 3.45 seconds**. Ruff passed. The parent cases used real process and pipe interfaces with invented stage implementations. They cover a spawn interrupted before handle delivery, a child observed late during cleanup, a hanging child, wall expiry while registration is waiting, refusal after a review changes, retention of the authorized request and one-use behavior. The worker cases separately cover day rollover, ownership loss, a competing marker, the journal checkpoint, planning headroom and refusal before a send.

One earlier hang rehearsal retained an empty uncertainty file. Expiry during a normal poll and the pending work alarm could overlap as cleanup began. The parent now moves the alarm to its original final cutoff before publishing cleanup evidence. Three fresh repetitions of the failing case passed. A later combined run found a test-harness defect. A direct test call bypassed the normal supervisor teardown and left its timer active for a worker test. The test now restores the original timer. Both failed rehearsals and source versions are retained under the ignored preparation directory.

The corrected source lives under `runtime/development-cycle-launch-v2-preparation/`. These tests used invented inputs. Actual registration, model dispatch and combined operational acceptance await separate review and the lead's final private preflight.

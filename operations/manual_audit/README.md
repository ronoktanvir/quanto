# Restore the manual research auditor

The six programs in this directory check the records of one supervised research cycle. They join the worker and spending records to the registered result and run an independently prepared arithmetic comparator against the reported financial fields. The reference builder reproduces the model worker’s program identity in a separate Python process from the reviewed program source.

This source represents the second correction to auditor v2. It checks reservation dates against their own journal timestamps and computes a range for spending that earlier split-transaction records cannot date precisely. It withholds a full verdict if that uncertainty could change the spending decision. The previous revision and its adverse reviews are retained at commit `763ef90`. Criticism, quality and scope accepted this revision for one supervised development cycle following fresh private preflight. [Scope and evidence](../../docs/reviews/D008-next-cycle-audit-v2r2-scope.md).

On the reviewed Mac, after restoring the registration and supervisor files, rebuild the host-specific manifest in memory from the project root.

```sh
/usr/bin/env -i /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 -I -S -B scripts/stage_manual_audit_tools.py --verify-only
```

Verification compares the reconstructed file with the exact selected manifest. The builder reads code and runtime identities. The numerical comparator retains its original, independently checked bytes, including the statement layout that gives it its reviewed digest. The local lint configuration preserves that file’s two historical layout conventions.

The optional installation mode restores missing program files in an existing reviewed setup and refuses conflicting files. Research verification still requires the separately accepted revision, its positive reviews, a fresh private plan and an observed actual cycle. [Registration restoration](../registration/README.md) · [Supervisor restoration](../manual_cycle/README.md).

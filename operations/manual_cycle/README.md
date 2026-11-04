# Restore the reviewed manual-cycle source

These four Python files reproduce the supervisor, paid worker and two synthetic fixture suites accepted for a manually supervised D008 development cycle. The accepted joint freeze is `a57edc801c50e1657536d76d15a41075faefe914ce9539ae64d76a1a3c2fb5c9`. [Independent scope review](../../docs/reviews/D008-manual-cycle-launch-v2-scope.md).

From the reviewed workspace at `/Users/ronoktanvir/Documents/ChatGPT/quanto` on the owner's Mac, run the code-only restorer.

```sh
/usr/bin/env -i /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 -I -S -B scripts/stage_manual_cycle_tools.py
```

The restorer reconstructs the accepted freeze and verifies each source digest before writing. It places only the four named files in `runtime/development-cycle-launch-v2-preparation/`. Existing matching files keep their inode and modification time. An existing conflict or unsafe target stops the initial check before any installation. Each new file is published without overwriting an existing name. A second invocation can finish a partial restore when the retained files pass the same checks. The command reads source bytes without importing or starting the supervisor or worker.

For the **91 synthetic cases**, first restore the reviewed registration source using its own instructions. One fixture imports public product code with that exact helper. The suite also needs the macOS Python executable named above. [Registration source restoration](../registration/README.md).

```sh
/usr/bin/env -i .venv/bin/python -B -m pytest -q operations/manual_cycle/test_supervise.py operations/manual_cycle/test_paid_worker.py
```

The process fixtures use invented inputs and temporary state. Actual registration, role dispatch and audit each require their reviewed operational inputs and gates. The controller and worker here are retained as source for restoration. [Manual-cycle plan](../../docs/reviews/D008-next-development-cycle-plan.md).

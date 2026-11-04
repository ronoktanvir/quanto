# Rebuild the reviewed registration tools

These two Python files are the exact sources used to prepare and test the current-code registration helper. The helper registers a revised policy, an admission and a three-cost study suite using the original approved inputs. Its tests use invented evidence. The source review records the intended deadline, request mapping and authority checks. [Producer report](../../docs/reviews/D008-current-code-registration-v2-preparation.md).

On the owner's Mac, run this from the project root to verify the source files, rebuild the source manifest in memory and stage any missing tool files under the ignored runtime directory.

```sh
/usr/bin/env -i /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 -I -S -B scripts/stage_registration_tools.py
```

The stager compares the computed digest with the manifest accepted for this workspace and interpreter. An exact existing file keeps its inode and modification time. A different file causes the command to stop before installing anything. The stage contains the controller, its tests and a generated source manifest. The command reads program source and runtime identities and performs no registration.

To run the invented registration cases on this setup, use the project's development environment.

```sh
.venv/bin/python -m pytest -q runtime/development-cycle-registration-v2-preparation/test_registration_preparation.py
```

The accepted manifest is specific to Python 3.11.9 and the reviewed workspace path. Moving the workspace or changing a product source file requires another identity review. A real cycle also requires the existing development authority, its private input packet and a reviewed supervisor. [Research cycle plan](../../docs/reviews/D008-next-development-cycle-plan.md).

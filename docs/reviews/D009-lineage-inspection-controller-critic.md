# D009 lineage inspection controller criticism

The frozen controller and corrected final launcher are suitable for the proposed **one incomplete structural inspection**, subject to separate quality/scope review and the lead's current-input and post-launch acceptance checks. No required source correction remains in the versions identified below. Quality found an interpreter-permission mismatch in the first launcher; that finding and its narrow correction are preserved below. This is preparation acceptance, not acceptance of an actual inspection, backup, recovery or control authority.

## Exact evidence and review boundary

This independent critic reviewed source in the `codex/recovery-lineage-inspection` worktree. The producer's actual-input pin literals were inspected as code; their private targets were not opened. The root-supplied outer launcher was read only from its preparation location. No actual controller, launcher, candidate, receipt, research database, provider, model, evaluator, capture or materialization operation was invoked.

| Artifact | Inspected SHA-256 |
| --- | --- |
| Prepared `inspect-lineage-materialized-candidate.py` | `9e0b4ceb88cebd785f6da14e442f6c86fdc4ea2f0d37b5db4c41ef0e828c87d6` |
| Preparation report | `13ebb34ff6dc2f8620b25fe34a3eba3be95c83ce5af3f4dc09cd34c84ffe66eb` |
| `preparation-freeze.json` | `73ff642176854a1218b825285e487a37d0059141f062751abc03c9d781f05500` |
| Producer fixture helper, `rehearse_controller.py` | `b6742df6c3a1133dbf53cf6313f0b45940f81180b7be7502d2b2d3b6d0f363fc` |
| Lead's final separately prepared `launch-lineage-inspection.py` | `d8940d31d587a94d599cb7ed733d7a90efdc503ae84a932b454ad7908d01d5bb` |
| Rejected first launcher, retained | `77f8c293b654ad4cb3403391c523ea669215924bbc9c65f0afd468cd951b82e5` |
| Corrected launcher before the final lint-only edit, retained | `505e46793723f83aaca3f3adc5f894d451091d14e5addecb61b72b9f87321aab` |
| Independent `probe_controller.py` | `9c2ce06b2154d72b1549e0a2eaca11ac040935561ae6fcb7eadf44cb986f4d3e` |
| Independent seven-case summary | `953077d69851cde89c78720d02edfb419ece91d296bc132613c0c5297b3fc73b` |

The eight public source/test pins were verified against current worktree bytes and rechecked at the end. In particular, closure is `e096331e6bf0e9aaa8cd8714416387e20b401bacd3943a5287ed5878bde7b196`, lineage is `20176d08eab4000666e3fddcd191e420ab5f68deb87fe55143427ba0671950ff`, and recovery is `5f7f2526da8d82d5f648c42a3135af3f44dadbafe0be2f40e8888b923d856883`. All eight identities, exact prepared copies and the final source check are retained under ignored `runtime/recovery-lineage-inspection-critic/`. These checks do not establish the state of the different main checkout at a future launch.

## Attribution, integrity and safe output

The controller compiles the verified bytes of only the inert initializer, recovery, lineage and closure modules. It binds the earlier accepted materialization result and destination, then compares source identities, loaded implementation fingerprints and runtime identities during the inspection and before publication. The launcher separately pins the Python executable bytes and requires Python 3.11.9, an empty child environment, isolated mode, no site initialization, no bytecode writes and disabled stdin. This is a cooperating-process identity boundary. It is not a cryptographic measurement of every standard-library or native dependency, or isolation from a hostile same-user process.

Quality found that the original launcher refused the already selected Python executable because its mode is 0775. The lead independently confirmed the reported root ownership, single link, mode and pinned digest through metadata/executable checks. Those actual observations are attributed to quality and the lead, not to this critic. The inspected correction permits group-write only for the exact `PYTHON` path when `runtime_executable=True` and `private=False`; it requires root/current ownership, rejects world-write, and retains exact before/after byte hashes. All project/private files retain stricter mode checks. This avoids changing a shared executable's permissions and does not claim isolation from an actor allowed to modify that executable. The final lint-only edit replaces a lambda with a local function returning the identical four stat fields. I inspected both deltas; the original source remains preserved rather than silently superseded.

The fixed projection reconstructs five count fields and four runtime fields, carries bounded hashes and false completion flags, and excludes the private graph. The controller validates its exact top-level field set and current implementation identity. The error path emits only fixed refusal codes, bounded exception context, native integer error codes and source-bound phase names; arbitrary messages and paths do not cross that boundary. Application socket refusal does not establish that filesystem reads cannot hydrate files over a network. The source correctly keeps offline availability unverified.

Exclusive receipt publication preserves partial evidence. A late pin, controller or intent change refuses final acceptance; an interrupted hardlink publication can leave a private report and pending link, which must remain a failed/uncertain attempt. A terminal result alone does not establish success: the lead must also establish clean launcher completion, exact receipt and stdout bindings, and absence of conflicting or pending evidence.

## Bounds and one-shot behavior

The closure's 45-second deadline starts before its initial implementation check and covers both base snapshot verifications. Each base verification receives the lesser of 15 seconds and the remaining closure time. The traversal, final verification and final identity check share that deadline; the final tick refuses overrun. Node, edge, JSON, depth, hop and report-byte limits remain finite. These application checks do not interrupt arbitrary blocking kernel I/O.

The child itself does not enforce the outer 70-second limit. The separately inspected launcher establishes a 70-second alarm and deadline, reserves five seconds from the normal child wait for cleanup, starts exactly one child in a new session and sends a kill only after checking the still-owned child's process-group identity. It then waits within the remaining deadline. It neither retries nor adopts the inspection result. A receipt written before a later failure cannot override a nonclean terminal outcome; unknown cleanup remains unknown. The alarm is an ordinary-process deadline mechanism, not proof that a stalled operating system or blocked filesystem will finish cleanup within 70 seconds.

The outer intent is necessary because child pin/binding preflight occurs before the child's own attempt receipt. The launcher publishes an exclusive intent before interpreter/controller preflight or starting the child, and requires a distinct state containing only the two staged sources on entry. Missing child intent after timeout or preflight refusal therefore cannot justify another launch. The lead must preserve and treat the outer attempt as consumed even when its final receipt is absent or incomplete.

## Independent invented evidence

Seven independent cases passed under Python 3.11.9 with `-I -S -B`, an empty environment and disabled stdin. The run is retained at `runtime/recovery-lineage-inspection-critic/rehearsals/independent-b77f80ca84f04fc8bccaf73c562aa121/`. I reused the producer helper solely to build fresh invented roots, raw SQLite fixtures and inert module inputs, retaining its audit restrictions. The independent faults and assertions were written separately; this is not an independent implementation of the fixture builder.

- A real inert traversal returned the expected incomplete result, exact 45/15/70 metadata and false recovery/control/evaluator flags.
- Late changes to the intent, prior receipt and controller were each refused before graph/result publication.
- An injected failure immediately after the report hardlink preserved the report and pending link, recorded failure and published no result.
- A second call after success refused the consumed attempt before rereading any pins and preserved existing receipt bytes.
- A deliberately hanging invented inspector was killed and reaped by its owning test parent after a two-second test timeout; its attempt remained and no result existed.

All six normally finishing cases compared the invented candidate bytes before and after and found them unchanged. No post-run byte-stability claim is made for the killed case. The timeout case tests the independent harness's ownership and refusal expectations, not the newly supplied launcher or a real 70-second execution. Launcher execution validation remains the separate quality role's work. There were no failed independent cases in this run. The producer's reported 36-case suite and its retained earlier corrections remain producer evidence, not additional independent passes.

## Acceptance limits

The remaining required action is the existing lead/quality acceptance sequence: validate the exact staged launcher and child, current main-checkout pins and original private materialization bindings, perform the separately reviewed single launch only when those checks pass, and evaluate its clean terminal outcome and receipts. None of those actual-state claims is certified here.

A supported lineage count means that specified structures were checked. It does not cover every semantic dependency, replay historical evaluators, restore the newer D008 control store, recover execution authority, establish off-Mac recovery or close the full recovery requirement. The prepared code preserves those distinctions and keeps the corresponding claims false.

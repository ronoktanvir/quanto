# D012 independent quality and failure-test plan

Recommendation: prefer one bounded administrative event in the existing audit table, explicitly pinned by the reviewed supervisor invocation. Accept only an exact old-device-to-current-device exception. This is a design recommendation, not implementation acceptance or permission to perform reattachment.

## Reviewed identity and evidence

Reviewed checkout HEAD: `19c3054298cc7b9f4bdf997951356adddb0f3785`.

- `docs/D012_PROPOSAL.md` SHA-256: `490e1061d66e52d9c7e904134dd9e7c0e71d50532c16f4875a696138ae361779`.
- `src/quanto/evaluation_registry.py` SHA-256: `c69c7de7e66c0d6f8b372304db482bf6d83ad0fe35960e55fc8fa00ac4a4b113`.

Read required project context and selected existing registry tests. No other D012 advisers were consulted. The current constructor checks original configuration before opening writable connections; `_check_paths` pins current root/control identities per process; transactions use `BEGIN IMMEDIATE`; audit events chain hashes. `_ACTIVE_LOCK` is process-local and does not establish cross-process exclusion. Budgets and consumed operation records require separate preservation evidence beyond this module.

The owner-reported reboot and lead-reported matching metadata/prefixes, two integrity checks and 4,568/686-event chains are attributed observations; I did not inspect production evidence. No prior volume UUID or external freshness witness exists. Tests cannot supply either retrospectively.

## Mechanism comparison

An existing-table event avoids a schema migration and makes acceptance plus its audit evidence one database append. Its payload must bind the exact transition, store/principal, original configuration/schema, non-device identities, preflight and source identities, prior audit head, research checkpoint and finite attempt identity. Opening must require the supplied event hash, validate its chain and exact payload, and reject duplicate/conflicting authorizations. Merely finding an event with a familiar kind is insufficient.

A mapping table can enforce uniqueness directly but adds schema, triggers and two representations whose agreement must be tested. A separately stored receipt creates a filesystem/database commit gap; its presence alone must never authorize access. A session-only exception limits reach but still needs durable evidence and fresh-process consumption semantics. Prefer the event unless implementation shows a concrete missing invariant. All options retain current-device checks throughout the process and forbid wildcard or transitive device exceptions.

## Discriminating fixture tests

All following tests are proposed `synthetic_fixture` work, not executed results. An independent checker should compare canonical, ordered row values and schema objects, not counts alone. Seed invented exposure, reservations, revocations, uncertain effects, budget holds and consumed controllers; retain exact before-state digests.

1. **Positive exception and unchanged defaults.** Build an invented old-device binding against the actual current filesystem; only the device differs. Apply one exact accepted event, then open in a fresh interpreter with the pin and perform a permitted local operation. Without the pin, with a wrong pin, or under ordinary unchanged code, mismatch refuses. Normal original-device attachment still works. The fresh process uses actual filesystem calls, without monkeypatches or inherited authority objects.
2. **Wrong physical/configuration identity.** Independently change path, root/control/research/object inode, owner, mode, symlink/hardlink status, store/principal, synthetic flag, configuration key/value, schema or trigger. Also swap a file between validation and use. Each case refuses before authorization; unsafe inputs cause no store initialization or migration.
3. **Stale evidence and state changes.** After freezing, append legitimate control/research state, alter an old row without changing counts, remove/reorder a retained prefix, corrupt a chain link, or change a terminal checkpoint. Recheck under the cooperating-writer exclusion boundary. Every divergence refuses; successful SQLite integrity checks alone cannot override it. Test a writer attempting entry during the cut, not merely an empty process inventory.
4. **Rollback and partial commit.** Inject failure after each validation/write boundary, immediately before commit, and after commit before receipt publication. Observe either no accepted event or exactly one complete accepted event; never permit half-state. Restore an older valid database lacking the pinned event and require refusal. A consistent rollback retaining all local witnesses may remain undetectable: document this boundary rather than claiming universal antirollback.
5. **Replay and concurrency.** Launch two real processes against the same frozen attempt, then competing mappings from the same prior head. Exactly one commit can authorize; losers cannot refresh their preflight automatically. Reusing the attempt, changing its payload, removing its terminal receipt, or invoking a consumed controller never grants another execution.
6. **Uncertain crashes and preservation.** Kill the child at controlled commit boundaries and lose its terminal output. Retain uncertainty; perform read-only reconciliation without rerunning the administrator. Compare every old row and consumed marker, including uncertain budget holds. Verify unchanged spending eligibility, exposure conflicts, revocations, reservation invalidations and one-use denials through behavioral checks; legacy-unknown remains true and protected acquisition remains unavailable.

Acceptance requires exact-source independent execution records, fault-injection outcomes and fresh-process verification. This review executes none of those tests. It supports only a possible supervised development reattachment; the prepared D011 request remains unregistered, and no acquisition, strategy result, unattended assurance or trading authority follows.

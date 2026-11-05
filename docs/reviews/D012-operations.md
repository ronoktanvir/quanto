# D012 independent operational recovery perspective

Recommend one durable administrative acceptance in the existing control store, explicitly selected by receipt identity when each supervised D011 process attaches. Preserve ordinary fail-closed opening without that explicit selection. This gives a fresh process inspectable evidence of the exception without making every later caller silently accept a replacement device. It is a bounded development-access repair, not recovery certification.

## Evidence and design choice

I inspected the source and documents below, independently of other D012 perspectives. I did not inspect production stores, credentials or market data, execute tests or operations, or call another model. Matching configuration, non-device identities, retained prefixes, passing chains and the restart are lead/owner-attributed observations. They support considering this repair; they do not establish external freshness. `legacy_unknown=True` must remain unchanged.

`Supervisor.__init__` compares the persisted root/device/inode/schema before opening existing authority for normal use. `_check_paths` subsequently binds the actual process-local root and control-file identities. `EffectPermit.start` refuses existing effect identities. Recovery should change only the first comparison's explicitly reviewed exception; retaining those later checks and consumed rows is essential.

A permanent mapping automatically consulted on every open is operationally simple but makes the exception broader than this supervised unblock. A standalone session receipt avoids a schema migration, but file publication is not atomic with database acceptance and an old receipt can be reused. Prefer an acceptance event in the existing audit chain plus an explicitly pinned receipt referring to that event. A new mapping table is optional, not a prerequisite: if adopted, its schema/triggers and audit insertion must be one transaction, with the exact additive schema delta reviewed. Neither variant may rewrite original configuration or create authority when a file is missing. An audit event alone needs transaction-protected uniqueness/conflict checks; its existence is not permission to issue new principals or effects.

## Required operational sequence

1. **Freeze the concrete operation.** Pin administrator, supervisor, interpreter and relevant source bytes; original configuration/schema; original and observed physical identities; complete retained-prefix fingerprints; control/research heads; relevant unfinished effects, spending holds and consumed operations; and the prepared D011 request hash. Record limits and exact acceptance payload. A newly measured volume identifier can supplement observation but cannot replace missing historical evidence.
2. **Establish a bounded process cut.** Inventory and exclude cooperating mutators of the stores being frozen, including any scheduled writer that actually touches them. A process listing is a point-in-time observation, not a lock. Keep the cut through acceptance and fresh-process verification; refuse unexplained activity. Do not restart unrelated services or claim protection from privileged filesystem changes.
3. **Consume one attempt before launch.** Exclusively create and durably persist the private attempt/intent before dispatch. A second invocation of that attempt always refuses. Use a reviewed parent with an external deadline, gated child launch, bounded output and confirmed owned-process cleanup. The inspected D011 parent supplies useful patterns, but its timer does not preempt local preflight/persistence I/O and it does not authorize an administrator command. A bounded administrative wrapper still needs exact-source review.
4. **Recheck under database locks.** Acquire bounded write-exclusion locks on control and research in a fixed order compatible with existing callers. Verify actual journal modes and frozen state while both locks are held; do not change journal modes. Reject stale heads, changed identities, non-device differences, replay or conflicting acceptance. Append acceptance and its audit binding atomically in control. Research is a locked witness, with no business-row write; do not claim a multistore atomic commit. Recheck paths before releasing locks. Any required schema delta belongs in that same control transaction.
5. **Reconcile uncertainty without dispatch.** Timeout, lost terminal output, failed receipt persistence, or unconfirmed cleanup means uncertain, even if acceptance may have committed. Retain the attempt and every reservation. A separate read-only inspector checks exact acceptance/payload, audit extension and unchanged historical records. Presence establishes only the committed database outcome; absence does not authorize rerunning the consumed attempt. Conflicts or unresolved workers block continuation.
6. **Verify in a fresh process.** Select the exact accepted receipt, validate its committed chain anchor and current physical identities, and reopen the original store under the reviewed exception. Verify configuration, store/principal identity, exposure, budgets, reservations, legacy flag and consumed records remain intact. Normal subsequent audit growth must extend the acceptance anchor, not require the old head to stay current. Only then freeze/register the unchanged D011 request under final code and resume its existing gates.

Implementation acceptance needs independent interruption/concurrency tests around lock acquisition, commit, receipt persistence and fresh reopen. Preserving history must include unfinished effects, not merely totals. No repair outcome is a strategy result, protected eligibility, spending reconciliation or permission to repeat consumed work.

## Inspected identities

Checkout HEAD: `f18a036f55a5f5ff41fa4ed4db35453bb3c40802`. Exact SHA-256:

| Artifact | SHA-256 |
| --- | --- |
| `AGENTS.md` | `93f6a6092942c1464bcd157212d300b1dfaa9f18242d8ced62c28ba49ba11e91` |
| `docs/CONTEXT.md` | `16912d8191a11f0182fa6bb0a1e09beeaaa63eb294c5654e0e29f743ff3ba853` |
| `docs/STATUS.md` | `b4e86e6bd8514db4aca098ba3042a1cc2be41aa3e04da4a31f312cbc492d69dd` |
| `docs/ROADMAP.md` | `f6b6838215889a3fc845386e414b78543e4b244536bbe274a12720c864948ad4` |
| `docs/DECISIONS.md` | `438e692408678d6cc70f8fceaf97abaf7cfd367c45d064cfe0029111184c663a` |
| `docs/HANDOFF.md` | `986cdb524cbf23e12413de9653325cdb8527dae65f644c930cecf6aa6b041288` |
| `docs/D012_PROPOSAL.md` | `490e1061d66e52d9c7e904134dd9e7c0e71d50532c16f4875a696138ae361779` |
| `src/quanto/evaluation_registry.py` | `c69c7de7e66c0d6f8b372304db482bf6d83ad0fe35960e55fc8fa00ac4a4b113` |
| `operations/strategy_campaign/supervise_step.py` | `7cd80f7775f6667fa0f56307cbb720070eee772951a3aed232c9c5f58779e06d` |

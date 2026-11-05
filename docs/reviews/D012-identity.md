# D012 identity and continuity perspective

**Recommendation: conditionally accept an explicit administrative attachment for the fixed D011 screen, preserving the original authority and its uncertainty.** Prefer one append-only event in the existing audit table, with the D011 supervisor explicitly pinning that event's receipt digest. This is a design recommendation, not accepted policy or permission to execute.

## Inspected evidence and its limits

Inspected checkout HEAD `f18a036f55a5f5ff41fa4ed4db35453bb3c40802`, contributor instructions, CONTEXT, STATUS, ROADMAP, DECISIONS and HANDOFF. Exact inspected SHA-256:

- `docs/D012_PROPOSAL.md`: `490e1061d66e52d9c7e904134dd9e7c0e71d50532c16f4875a696138ae361779`.
- `src/quanto/evaluation_registry.py`: `c69c7de7e66c0d6f8b372304db482bf6d83ad0fe35960e55fc8fa00ac4a4b113`.

The source directly shows that existing-store construction compares configuration against the current root path, device, inode, synthetic flag and schema; `_check_paths` separately pins root/control device-inode pairs within the process. Existing configuration and other control records have UPDATE/DELETE refusal triggers. The module explicitly limits itself to cooperating supervisor-bound services and disclaims hostile-owner isolation.

Production facts are **lead-attributed**, not independently verified here: unchanged configuration/schema and retained table prefixes; matching root/object/control/research inode, ownership and mode; changed device numbers; successful integrity checks and control/research chains of 4,568/686 events. I did not open production runtime, credentials, market data or the private continuity receipt. No tests or model calls were run.

Apple documents that device IDs can change across reboot and recommends UUID comparison for persistent per-device identification. Its guide also distinguishes UUID agreement from valid event history after restoration. Thus restart-related renumbering is consistent with the evidence; it is not established as the exclusive cause. [Apple File System Events guide](https://developer.apple.com/library/archive/documentation/Darwin/Conceptual/FSEvents_ProgGuide/UsingtheFSEventsFramework/UsingtheFSEventsFramework.html).

The stat interface reports the containing device separately from the inode number; neither inode agreement nor private permissions asserts unchanged file contents. [Apple stat manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/stat.2.html). A UUID first observed now is a prospective baseline, not a comparison with a missing historical observation. Valid local chains and matching prefixes establish internal consistency with retained local witnesses; a mutually consistent rollback can preserve them all.

## Preferred attachment and alternatives

Record one bounded, versioned administrative audit payload binding the original configuration/schema digests, store/principal identities, old and current physical identities, pre-attachment control/research heads and retained-checkpoint digests, evidence/preflight/source/policy digests, and the explicit statement `legacy_unknown=True`, freshness unverified. Preserve the old configuration exactly. Validate the frozen pre-state under exclusive cooperating-worker control and append the attachment in one transaction. Require a fresh process to verify the exact receipt and full audit chain before exercising the exception; retain ordinary live physical checks thereafter.

This uses an existing append-only structure without introducing a table migration merely to resume D011. A dedicated mapping table is also defensible if the mapping and its audit evidence commit together, but its schema extension and triggers need separate exact validation. A standalone external receipt alone introduces two-state publication/reconciliation problems. A session-only override without durable evidence fails the history requirement; a session explicitly bound to the durable event meets it.

Pinning the receipt in the D011 supervisor makes the changed assumption reviewable. It should grant only the device comparison exception, not bypass any other check. Record any UUID measured now with its exact API/meaning; do not conflate an FSEvents history identifier with proof of physical-volume continuity. Future identity hardening can remain separate from this finite campaign.

## Required objections and failure boundaries

1. **Reject a timeless device allowlist.** “Original or any accepted mapping” could accept a retired numeric identity when device numbers recur. For this operation, require the explicitly selected attachment, exact current identities and its bound history. Future mappings need explicit lineage and must not resurrect earlier alternatives implicitly.
2. **Freeze a coherent state.** A valid chain observed before another writer runs is insufficient. Refuse changed heads/prefixes, unexpected schema/configuration, changed path/inode/owner/mode, symlinks, active workers, conflicting mappings or replay. Recheck research state as well as control state; one SQLite transaction cannot by itself freeze both databases and the object directory.
3. **Preserve uncertainty.** Lost completion requires read-only reconciliation, not retry. Unfinished effects, consumed runs, reservations, holds, revocations and exposure remain unchanged. Matching metadata does not validate every object's bytes; existing content verification must continue at use.

The stated observations can support accepting a documented continuity assumption for supervised development on the cooperating owner's Mac. They cannot certify external freshness, recovery completeness, historical non-exposure or hostile-writer resistance. Keep protected/unattended/live gates closed. After exact implementation reviews and accepted policy, return to the unchanged D011 request; this administrative result is neither a strategy failure nor the empirical screen deliverable.

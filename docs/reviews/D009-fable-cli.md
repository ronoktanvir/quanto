# D009 Fable terminal council review

Observed requested and responding model: `claude-fable-5-1`. Route: existing local Claude Code OAuth, one completed turn, no tools/MCP, no fallback or automatic retries. Request `cli-300d49b1a9864a70ac5ca3f69c14a76c` completed `2026-11-02T10:39:51.929782+00:00`. Packet SHA-256 `40c34299f3b686a2b8134bf7d08f5f52518eeecbf2fc040737ade3982c917b2c`, 11730 bytes: complete proposal plus explicitly attributed lead summaries of five independent perspectives. The reviewer did not inspect full reports, code, account, credentials or private data. Its recommendation is advisory, not execution authorization or implementation verification.

The conservative project hold remains uncertain because CLI list-price estimates are not subscription invoices. Exact raw CLI output remains private. The following is the full visible final response, with objections preserved. Lead dispositions are in D009_POLICY.md.

# Stage A review: external recovery storage (D009)

## Consequential blockers before creating the volume

**1. S3 reachability of US-WA-1 is asserted, not shown.** Runpod's S3 compatibility applies only to data centers listed as S3-enabled; catalog support for STANDARD and a successful empty S3 list do not prove US-WA-1 is on that list. If it is not, the volume is only reachable from a Pod, which the authorization forbids, and the USD0.70/month becomes dead spend. Condition: record the S3-enabled datacenter list entry for US-WA-1 (public doc plus the exact endpoint hostname) in the create record before the create call.

**2. Credit depletion is a data-loss path, not just a cost path.** Runpod states that network volumes are at risk of deletion when account balance is exhausted. The proposal watches cumulative spend toward USD45/50 but never names remaining credit as a hard monitored floor. Condition: the recurring cost check must report remaining credit and the projected months of runway, with a stop/escalate threshold above the deletion point, implemented before Stage A is declared complete. "No top-up needed" is a snapshot, not a control.

**3. Name-based reconciliation is weaker than stated.** Runpod does not guarantee volume-name uniqueness. A lost create response reconciled by "unique name" alone can match a stranger's later resource or miss a partially-created one. Correction: reconcile on name plus exact size, tier, datacenter and a creation timestamp inside the attempt window; if ambiguous, stop and report rather than proceed.

**4. Credential scoping is account-wide.** Runpod S3 access keys are not bucket- or volume-scoped; the uploader child can read and delete any volume in the account. For Stage A this is tolerable because nothing else exists, but the proposal should say so explicitly instead of implying least-privilege. Stage B must treat the S3 key as a full-account write capability and never leave it in a long-lived unattended process.

## Corrections to the canary procedure

- Disable HTTP redirect following and path/virtual-host auto-switching in the S3 client; "exact endpoint" is only enforced if the client cannot follow a 3xx. Record the resolved endpoint used.
- Compare `Content-Length` and SHA-256 of ciphertext, and verify the decrypted plaintext equals the pre-encryption bytes, not merely that `age` decryption "succeeds". Record a negative test: decryption with a wrong key must fail.
- State canary cleanup policy. The canary is not a recovery copy, so deletion is permitted, but the proposal's "never delete automatically" wording should be scoped to recovery generations only. Decide: retain the canary as a continuing read-probe, or delete and verify a 404 by exact key. Either is acceptable; silence is not.
- The management API key and the S3 key must never be present in the same process; create with the management key in one short-lived invocation, canary with S3 only.
- Hourly billing starts at creation; expect the first observed charge to lag. Record stated rate, first visible line item, and any tax separately so the 30-day review compares like with like.

## Later-gate requirements (not Stage A blockers)

**Stage B.** Two SQLite databases backed up independently are not one consistent snapshot. Require either a documented quiescence point (all writers paused, WAL checkpointed, both online backups taken, writers resumed) or an explicit written acceptance that conversation state may be one transaction ahead or behind research state, with the boundary recorded in the manifest. Off-Mac key custody must be demonstrated by performing the isolated restore from the off-Mac identity, not by attestation. Confirm Runpod's S3 maximum object and multipart part limits against the expected archive size; a 10GB volume with a growing content-object closure can hit size before cost.

**Stage C.** The freshness gap is correctly diagnosed but still has no decision owner. Acceptable closures are a second independently controlled store holding only a signed generation counter, or an explicit owner acceptance of the narrower "Mac loss under trusted account" model for D008. Leaving this open blocks nothing in Stage A but must not be allowed to drift into implicit acceptance.

## Residual risks that survive acceptance

Account compromise or provider action can still erase every generation; `age` protects confidentiality, not availability. Hourly charges continue if the operator forgets the resource. The USD45 alert depends on a process that has not yet been built. Growth without shrinkage means a mistaken resize is permanent cost.

## Acceptance conditions for Stage A

1. Recorded S3-enabled confirmation and exact endpoint for US-WA-1 before create.
2. Single create, reconciliation rule as corrected above, fresh GET verified.
3. Canary round trip with length, hash and plaintext equality checks, plus wrong-key negative test, redirect following disabled.
4. Remaining-credit floor and USD45 threshold implemented as a scheduled check with a named reviewer and a concrete 30-day date.
5. Explicit canary cleanup decision recorded.
6. Cost report separating cash deposited, credit consumed and projected runway.

With these conditions, the Stage A spend is proportionate and the staging boundaries are honest. I do not authorize execution; Stage A proceeds only after independent implementation checks against the above.

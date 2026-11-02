# D009 Opus terminal council review

Observed requested and responding model: `claude-opus-5-5`. Route: existing local Claude Code OAuth, one completed turn, no tools/MCP, no fallback or automatic retries. Request `cli-1f02f16af8cf4f87a0b3594aeb9b44f6` completed `2026-11-02T10:40:40.098826+00:00`. Packet SHA-256 `40c34299f3b686a2b8134bf7d08f5f52518eeecbf2fc040737ade3982c917b2c`, 11730 bytes: complete proposal plus explicitly attributed lead summaries of five independent perspectives. The reviewer did not inspect full reports, code, account, credentials or private data. Its recommendation is advisory, not execution authorization or implementation verification.

The conservative project hold remains uncertain because CLI list-price estimates are not subscription invoices. Exact raw CLI output remains private. The following is the full visible final response, with objections preserved. Lead dispositions are in D009_POLICY.md.

# D009 Stage A Review: Runpod Recovery Storage

The staged structure is sound, and the scope boundaries are honest. The trusted-provider caveat, the refusal to claim a provider-enforced cap, and the rejection of the adviser's autopay suggestion are all correct. Below are the remaining blockers, corrections, risks and acceptance conditions.

## Stage A blockers

1. **S3 endpoint support for US-WA-1 is not established.** The catalog showing STANDARD availability is not the same as the S3 API being served for that datacenter. Runpod's S3 support has been limited to specific datacenters. The passed "S3 list" check does not say which regional endpoint it hit. Before creating anything, confirm from the docs or a read-only call against the exact US-WA-1 endpoint that S3 access exists there. If it does not, stop and re-decide the region. Do not fall back silently to US-CA-2 premium or another region.

2. **Credential blast radius is unexamined.** The management key can likely create Pods and delete volumes. S3 keys may be account-wide rather than per-volume.
   - Use the narrowest key scope Runpod offers.
   - Use a separate read-only key for reconciliation and monitoring if one is available.
   - Document whatever scope remains, so the "trusted remote account" assumption names what a leaked key can do.

3. **Concurrent invocation is not excluded.** "List, then create once" is not safe if two runs overlap. Require a local exclusive lock around the list-create-reconcile sequence. Also state what happens if reconciliation finds more than one match or a near-match: stop and escalate, with no deletion.

4. **Canary failure semantics are incomplete.** With retries disabled, a timed-out PUT is ambiguous. Specify that:
   - a retry always uses a new unique key, never an overwrite;
   - an ambiguous upload is reported as uncertain;
   - the uploader issues no DELETE in Stage A, or, if canary cleanup is wanted, deletion is an explicit, logged, exact-key action.

   Also require TLS certificate validation against the pinned host. "No arbitrary endpoints" is not sufficient on its own.

## Precise corrections

- **Cap accounting.** State that the USD50 ceiling counts tax-inclusive resource consumption from the existing credit, attributed to this project. Without that, "existing credit is not a new deposit" can be read as "consuming credit doesn't count."
- **Observed billing.** Charges may lag. Stage A should record the first observed charge within a stated window, for example 72 hours. If none appears, treat the rate as unverified rather than block indefinitely. The 30-day review must be a dated, owned action with a recorded outcome.
- **Request retention.** "Retain the exact create request and result" must exclude credentials and headers, and stay in the same private, ignored store.
- **Status wording.** Reword "Immediate decision" to "Proposed immediate action," consistent with "proposed, not accepted."

## Later-gate requirements (not Stage A blockers)

- **Account access is a recovery dependency.** Off-Mac custody of the age identity is necessary but not sufficient. Today the S3 and management credentials exist only on the Mac. Stage B must document and test an off-Mac path to regain Runpod account access: login, 2FA recovery and key regeneration. Otherwise Mac loss also means loss of access to the ciphertext.
- **Provider-side deletion is not covered by "never delete automatically."** Runpod may terminate network volumes when the balance is exhausted or the account is suspended. Stage B needs:
  - credit-runway monitoring with a lead time well beyond the termination risk;
  - an explicit statement that provider or billing continuity is part of the trusted assumption.
- **No versioning means the uploader is the retention mechanism.** Stage B must enforce:
  - write-once generation keys;
  - no DELETE or overwrite in the routine uploader;
  - a separately reviewed retention and garbage-collection policy, so an uploader bug cannot destroy history.
- **Restore test realism.** Run the isolated restore from a clean environment that uses only off-Mac custody materials: the identity and the recovered account access. A restore that reuses the Mac's config does not demonstrate disaster recovery.
- **Two-database boundary.** Stage B acceptance must name its consistency boundary explicitly as one of:
  - research-only, with chat excluded and stated;
  - a coordinated quiescent capture of both databases.

  An implicit choice is not acceptable.
- **Stage C fail-closed dependency.** Externally committing intent before dispatch makes remote availability a precondition for effects. State that an outage blocks effects rather than degrading to local-only commits.

## Residual risks to retain in the record

- Single-provider, single-account concentration. Account compromise, suspension or billing failure is correlated with loss of the only off-Mac copy.
- An authorized writer can still roll back or remove generations until an independent freshness anchor exists. This is correctly acknowledged; keep it visible.
- Runpod S3 behavioral quirks remain possible, such as consistency, listing or metadata differences. The canary covers one small object and does not cover multipart or larger transfers.
- Documentation drift. Region and S3 support observations are dated and should be rechecked before Stage B.

## Stage A acceptance conditions

1. US-WA-1 S3 endpoint support is confirmed against the exact endpoint, before creation.
2. Key scopes are minimized and documented. A lock and an ambiguous-result policy are implemented.
3. Exactly one volume exists. Its returned ID, name, size, tier and region match a fresh GET. No other account resources have changed.
4. The age canary round trip passes: exact-key GET, SHA-256 match, authenticated decrypt and byte equality. The temporary identity is destroyed or isolated afterwards.
5. The cost record covers creation time, stated rate, tax treatment, the first observed charge or an "unverified" flag, and a dated 30-day review.
6. Independent implementation review is complete, and objections are retained.

Stage A passing establishes only a verified destination and transfer path. It does not establish backup, recovery, freshness or any trading readiness.

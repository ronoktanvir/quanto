# D009 storage security and recovery perspective

**Disposition: support the proposed first stage as a manually triggered encrypted recovery copy, not a trusted antirollback checkpoint or authorization for automated effects.** The root proposes 10 GB Standard storage in US-WA-1, approximately USD0.70/month before taxes, within the owner's USD50 total setup allowance and USD5/month target. Capacity adequacy still requires an authorized inventory. No rented compute is needed.

Reviewer: `/root/d008_broker_critic`, independently briefed for D009 security/recovery. Inspected public-source checkpoint `37721ee286b95ecd8a1ea9a2f5ed0067fbe52ddf`; official documentation checked November 2, 2026. No account, environment, credential, private financial/runtime record, purchase or transfer was accessed or performed. The root reports that S3 keys are now configured and a read-only authentication check is running; that is attributed status, not this reviewer's verification. This is one design perspective for the lead's five-perspective/council review.

## Provider facts and the security boundary

Runpod explicitly documents **versioning and Object Lock as unsupported**. Bucket policies, ACLs and bucket-encryption configuration APIs are also unsupported. GET/HEAD/PUT/DELETE and multipart operations are supported; single PUT is below 500 MB. US-WA-1 appears among supported S3 datacenters. S3 uses a separate access-key/secret pair, and direct uploads require no Pod. Do not infer conditional writes, delete-denying keys, per-prefix permissions or other AWS guarantees from protocol compatibility. Unsupported encryption configuration does not establish whether provider disks are encrypted. [Official S3 capabilities](https://docs.runpod.io/storage/s3-api)

Standard storage costs USD0.07/GB/month for the first terabyte. Allocated capacity can grow but cannot shrink. Storage can eventually be terminated if its charges remain unpaid; the documentation supplies no guaranteed grace period. Distinct volumes do not automatically replicate. [Official network-volume documentation](https://docs.runpod.io/storage/network-volumes)

The S3-key instructions do not establish per-volume or delete-denying permissions. Keep the management key out of the routine uploader and treat the S3 key's narrow scope as unverified until demonstrated. A key named “backup writer” is not an enforced append-only identity. [Official credential documentation](https://docs.runpod.io/get-started/credentials)

An encrypted off-Mac copy can protect recovery from loss of this Mac. It does not prove that a selected restore is latest. A signed old manifest remains authentic but old; a hash chain can lose its newest suffix; a mutable `latest` file can be replaced. Trusted recovery additionally needs an independent monotonic latest-sequence/digest anchor and a defined single-writer/fencing model. Those capabilities remain gated for this first stage.

## Minimal first-stage plan

1. **Pin the destination.** Privately record expected account/tenant, immutable volume ID, datacenter, exact HTTPS endpoint, namespace and key identities. Cross-check management metadata with the S3 target and perform a synthetic random-canary round trip. A display name or bucket listing alone is insufficient identity evidence. Keep TLS verification enabled; never accept arbitrary redirected endpoints. Do not attach backup storage to compute for transfer.

2. **Freeze a complete recovery boundary.** Pause new cooperating effect authorizations, artifact publication and purge; drain or conservatively classify in-flight effects. Use SQLite's Online Backup API into a new staging file, then stage the exact referenced artifact closure under the same application barrier. A database snapshot does not make separate files consistent automatically. [SQLite backup API](https://sqlite.org/backup.html)

   The inspected ledger uses `journal_mode=DELETE` and `synchronous=FULL`, not WAL. Avoid raw copying of an open database regardless. If WAL is introduced later, its sidecar can contain committed state; separating it from the database can lose transactions. Keep the live database off network/S3 mounts. [SQLite WAL requirements](https://sqlite.org/wal.html)

3. **Verify the staged state.** Check database integrity, foreign keys, event chain and materialized-state consistency; hash every required regular artifact and reject symlinks/path escape. Preserve tombstones and recorded unavailability rather than resurrecting purged bytes. Include all approved authoritative journals, reservations, uncertain outcomes, request IDs, exposure records and failure history. Exclude credentials, `.env`, tokens and encryption private keys. `integrity_check` alone does not detect foreign-key violations. [SQLite checks](https://sqlite.org/pragma.html#pragma_integrity_check)

4. **Encrypt locally with independently recoverable keys.** Use a maintained, pinned implementation such as age with an explicit public recipient. The uploader needs that public recipient, not the recovery identity. Keep two owner-controlled recovery copies outside the Mac and Runpod writer's custody, for example a protected independent vault and an encrypted offline copy. Test the secondary recovery path with synthetic data before relying on actual backups. Multiple recipients provide alternative decryption paths, not two-person approval. [Official age documentation](https://github.com/FiloSottile/age)

   Keep manifests/inventories encrypted and bind code/schema/tool identities, database/artifact digests, sequence/parent receipt and chunk lengths. Authenticated encryption protects content integrity; it is not a latest-state proof or, by itself, sender authentication when anyone can encrypt to the public recipient. Bind the ciphertext digest to an independently authenticated receipt. Do not hand-roll cryptography. [age format](https://age-encryption.org/v1)

5. **Upload unique objects and verify their bytes.** Use one bounded uploader, nonoverwriting names and a small number of encrypted archive chunks, initially at most 256 MiB each. Upload payload before its commit manifest. Read back complete ciphertext and verify SHA-256/length; HEAD, listing or ETag alone is insufficient. Treat upload timeouts as ambiguous and inspect the exact planned key. Never use destructive mirroring, automatic resize or automatic pruning initially. Retain an earlier verified generation and reserve capacity headroom.

6. **Restore before declaring success.** Restore into a clean directory with model/network/execution paths disabled. Recover the key independently, verify receipt and bytes, decrypt, and rerun database/reference checks. Do not import execution credentials or silently restart work. Record measured recovery time and the precise captured effect boundary. A successful upload is not a restore test. Encryption does not grant licensed-data transfer rights; the explicit export allowlist and retention policy must precede project-data transfer.

Store a latest accepted receipt outside both this Mac and the uploader's authority. For this manual first stage, it is an owner-confirmed recovery floor, not continuous automated witnessing. Do not claim malicious-account deletion resistance or unattended freshness from it. Securely retaining the recovery identity is essential: losing it makes the ciphertext unusable; replacing the public recipient cannot unlock old backups.

## Later trusted-checkpoint requirement

Post-effect backup alone leaves a dangerous gap: the Mac can die after a paid send or protected-data access but before its new state reaches the remote copy. An older restore could then present unused budget or entitlement.

Before automated irreversible work is accepted, require: **local unique intent plus full conservative reservation/consumption record → externally acknowledged prepared checkpoint → one effect → retained outcome/uncertainty → externally acknowledged terminal checkpoint before the next effect**. Restoring a prepared intent without an acknowledged outcome must preserve it as consumed and uncertain, never retry it or reset its reservation/exposure. This protocol is a future design obligation, not an existing D008 capability or a relaxation of the USD20 Los Angeles-day model limit.

A separate witness must enforce sequence/parent continuity and prevent stale or concurrent writers from replacing acknowledged state. Do not assume Runpod conditional-write or distributed-fencing support. Without such a mechanism, prohibit concurrent restored supervisors and retain manual recovery authorization. If the remote anchor is missing, stale, contradictory or unavailable, permit read-only inspection only. Additional infrastructure or providers require their own scoped decision; current storage approval does not imply them.

## Required verification and limits

Use invented fixtures first: database/artifact races; missing/corrupt objects; preserved tombstones; wrong volume/account/endpoint; lost primary recovery key; interrupted uploads; full capacity; and a clean-machine restore. For later checkpoint acceptance, add validly signed older manifests, deleted remote suffixes, local counter/database rollback, conflicting writers and crashes on both sides of every irreversible-effect boundary. Each must refuse unsafe resumption while retaining spend/exposure obligations.

The first-stage recommendation is useful and bounded: a recoverable encrypted copy on the specifically identified external volume. Its availability depends on provider/account continuity, retention and tested key custody. Trusted antirollback, automated scheduling and full operation acceptance remain explicitly incomplete. No account capability or restore test is represented as executed by this review.

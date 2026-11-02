# D009: external recovery storage, staged proposal

Status: proposed, not accepted. The owner authorized Runpod storage around USD5/month and subsequently up to USD50 total setup spending. This is a cumulative Runpod ceiling, separate from the unchanged USD20/day model ceiling and USD4/day research-purpose allowance. No compute rental or live orders are authorized.

## Immediate decision

Provision one 10GB STANDARD network volume in US-WA-1, estimated USD0.70/month before applicable tax, using the owner's existing credit. Use direct S3; rent no Pod, CPU, GPU or serverless worker. The lead's authenticated read-only checks found no existing volumes, STANDARD availability in US-WA-1, and working management and S3 credentials. Current local runtime/data files total approximately10MB. US-CA-2 currently offers only the premium tier. The API allows growth but not shrinkage, so unused capacity has no immediate benefit.

The first increment is a verified destination and encrypted synthetic canary. It does not upload research data, establish a usable project backup, enable unattended research or close R14. Significant decision review requires five independent perspectives and actual Fable/Opus CLI criticism before acceptance; implementation then needs separate criticism, quality and scope review.

## Resource and spending controls

Pin the account identity privately and retain the exact create request and result. Use an opaque unique name and exact size, tier and region; list before creation. Create once, with no automatic mutation retry. A lost response requires read-only reconciliation by unique name and exact resource properties, not another blind create. Verify the returned ID and a fresh GET before use. No unrelated account resources may be changed.

Record creation time, stated rate, hourly estimate, observed billing and all Quanto-attributable deposits/charges. Existing credit is not a new deposit and does not expand authorization. Avoid double-counting a deposit and its later consumption when reporting total paid cash versus resource usage; show both separately. No top-up is needed on the observed account. Do not change account-wide auto-pay or unrelated spending settings. A local process stopping does not stop provider charges.

The USD50 cap is not enforced by Runpod's account hourly limit. Warn early and stop new capacity, transfers and other spending commitments at USD45, leaving room for ongoing storage while obtaining a lifecycle decision before USD50. Never delete the only recovery copy automatically. Before any later decommissioning, make and verify a replacement copy and obtain the owner's explicit deletion decision. Initial cost review is due within30days; recurring operation and its reporting must be implemented before calling the storage managed. No claim of a provider-enforced USD50 lifetime cap is made.

## Encrypted canary and credential separation

Management and S3 credentials remain in ignored mode0600 local configuration and never enter Git, prompts, logs or backup archives. Uploader children receive only the required S3 credentials through their environment, with external AWS profiles disabled, bounded timeouts and automatic retries disabled. Use the exact HTTPS endpoint for the pinned region; no arbitrary redirects/endpoints.

Use an established portable authenticated encryption format, proposed age, rather than custom cryptography. The initial canary contains only a fixed synthetic marker and random nonce, with a temporary canary identity. Encrypt locally, PUT a uniquely named opaque ciphertext object, download it by exact key, compare its SHA-256, decrypt locally and compare the original bytes. Do not rely on ETag as a content hash. Retain bounded metadata and report every failure. A canary pass validates this transfer path only. Temporary canary secrets never become the production backup key.

## Later project-backup contract

Before project-data transfer, independently review and implement a consistent manifest-driven capture, encryption, restore and key-recovery procedure. The operator must retain the permanent decryption identity outside this Mac; possession of the S3 key alone cannot recover encrypted data. A key only on this Mac is not disaster recovery.

Capture research.sqlite using SQLite's online backup API, preserving budgets, full uncertain reservations, consumed dispatch identities, exposure history and pending outcomes. Capture its referenced content-object closure and required source/audit evidence without copying .env, OAuth/browser files, credentials, live session tokens or unrelated paths. Conversations use another database with cross-database paid-call transitions and CSRF sessions; treat them under a separately specified quiescence/sanitization contract. A backup of research state alone must explicitly say that chat history/session continuity is excluded.

All files need bounded safe paths, regular-file checks, byte sizes and digests. Coordinate writers and tombstone/purge behavior or reject a raced capture. Verify database integrity, the event chain and the entire manifest after capture. Source rights must be reviewed for the selected private encrypted backup use; do not treat encryption as an exemption from applicable agreements. Upload only ciphertext after allowlist and privacy review. The exact snapshot, omissions and consistency boundary must be recorded.

Restore into an isolated directory with no credentials, model/network dispatch, broker calls, worker revival or budget/exposure resets. Download exact ciphertext, verify its digest, authenticate decryption, validate the manifest, object closure, database state and journal head. Test wrong keys, corrupted/missing objects, interrupted uploads, stale generations and uncertain effects. Never replace production automatically.

## Recovery versus trusted freshness

Runpod's S3 documentation explicitly lists versioning, Object Lock and bucket policies/ACLs as unsupported. Unique keys, hashes, encryption and a signed manifest cannot prevent an account-authorized writer from removing the newest generation or presenting an authentic older one. A mutable latest pointer is a convenience, not a freshness proof.

The initial backup therefore addresses Mac loss under a trusted remote-account/provider assumption. It is not an independently retained antirollback witness. An independently controlled latest-generation trust anchor or an explicitly accepted narrower recovery threat model remains necessary for the stronger scheduler gate. No weaker threat model is silently substituted for D008.

Before future unattended effects, externally preserve a unique intent and its full conservative reservation/consumption entitlement before dispatch. Preserve the subsequent outcome or uncertainty before allowing another irreversible effect. A crash in between retains uncertainty and cannot justify replay. Implement single-writer/fencing, stale-generation and divergent-history refusal, including recovery across calendar days. These mechanisms and sustained operational evidence remain future work; five-minute website captures are unrelated operational observations.

## Review and acceptance boundaries

Five perspectives cover architecture, security, costs/operations, data consistency/recovery and scope. Their observations, objections and source limits remain in individual reports. Outside reviewers receive this complete proposal plus explicitly attributed lead summaries, not credentials, private data or an invented claim that they tested implementation.

Stage A acceptance requires reviewed resource code/configuration, actual exact resource identity, an observed encrypted-canary round trip and truthful cost/limit reporting. Stage B requires the independently checked real snapshot, off-Mac key custody and successful isolated restore. Stage C requires the separately implemented external effect barriers, trusted freshness boundary and observed unattended operation. No stage validates a strategy, completes protected evaluation or authorizes trading.

Sources: [network volumes](https://docs.runpod.io/storage/network-volumes), [S3 compatibility](https://docs.runpod.io/storage/s3-api), [API v2 create](https://docs.runpod.io/api-reference-v2/network-volumes/create-a-network-volume), [catalog](https://docs.runpod.io/api-reference-v2/catalog/list-data-centers), [SQLite backup](https://sqlite.org/backup.html), [age](https://github.com/FiloSottile/age). Account observations are lead-executed and retained privately, distinct from public documentation.

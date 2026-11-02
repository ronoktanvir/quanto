# D009 Stage A: independent implementation criticism

**No remaining code blocker was found in the corrected one-shot harness at the identity below.** Independent criticism reproduced one evidence-retention defect, then verified its repair. This disposition covers source inspection and invented failure-path probes; it is not an observed purchase, S3 transfer, project backup, spending monitor or recovery acceptance.

Reviewer: `/root/d009_stage_a_critic`, separate from the producer and execution-quality reviewer. I read the accepted D009 contract, both actual council reports, project context and the frozen harness. I did not read the real environment file, credentials, account responses, databases, financial artifacts or raw model results. No account API, paid model, financial runner, provisioning command or actual upload was invoked. The only network reads were public primary documentation.

## Reproduced finding and correction

**P2, closed: the exact create response was discarded.** The initial harness reduced the provider result to ID, name, size, region and tier before writing `create-response.json`. It retained a hash and length of the original response but not those original bytes. An invented response with distinct whitespace and an optional `createdAt` field reproduced the loss. A hash without its original bytes cannot independently establish the complete observed result or preserve optional reconciliation evidence required by D009.

The producer corrected this before any actual execution. The bounded HTTP reader first checks for reflected configured credentials. The create API call then writes the exact checked body privately, plus a separate HTTP-status/hash/length receipt, before interpreting the status or reducing the schema. No request headers are persisted. The normalized projection remains a separate convenience. My corrected probe verifies byte-exact preservation of whitespace and the optional timestamp, preserves an observed503 body before a fixed refusal, and confirms that a reflected credential prevents both body and metadata persistence. A timeout with no observed response still leaves uncertainty rather than an invented result.

The original harness and original reproducer are retained under the private critic directory. The finding is not erased by the corrected test result.

## Independently checked boundaries

Nine invented tests pass against the corrected harness:

- Durable intent and dispatch-marker files exist before the single create call; repeating the command performs no further transport call.
- A lost create response remains potentially created, with automatic retry false and the attempt permanently consumed.
- A fresh GET with mismatched resource properties cannot produce a verified result.
- The common nonblocking file lock excludes a second cooperating actor.
- Non-HTTPS hosts, lookalike hosts, explicit alternate ports and user-info URLs refuse before transport; S3 signing refuses unsupported mutation methods.
- Redirect construction returns no follow-up request. Reflected credentials produce a fixed refusal, including before response persistence.
- The exact successful response and observed error-body retention cases above pass.

Ruff passes for the harness and credential helper. These tests mock the HTTP boundary with invented values; they do not establish provider behavior or live TLS/S3 compatibility.

Source inspection confirms a fixed account-identity digest, exact10GB STANDARD US-WA-1 properties, an empty/unpaginated inventory prerequisite, a fresh resource GET, fixed non-secret error codes, bounded response sizes and a180-second command deadline. HTTPS uses the system certificate verifier, disabled proxies and a no-redirect handler. The SigV4 signer permits only the fixed region host and restricted opaque object paths; there is no DELETE, compute creation, resize or top-up path. A direct helper call is not a security boundary against the filesystem owner, and the source does not claim that protection.

The canary generates synthetic plaintext and temporary age identities locally. It checks wrong-key refusal, an absent random object key, exactly one PUT, remote length, downloaded SHA-256 and authenticated plaintext equality. PUT uncertainty remains recorded with the exact key and no automatic replay. The temporary identities and local canary files are scoped to a private temporary directory; the remote synthetic ciphertext is retained. My review inspected this path but did not execute its encryption or transfer steps. The separate quality review owns independent canary/SigV4 execution evidence; producer test counts are not counted as my tests.

The credential helper uses hidden prompts, refuses terminal-echo fallback, preserves other settings, checks the ignored destination and writes mode0600 atomically. My review found no consequential source defect there; separate quality owns its synthetic filesystem tests.

## Limits that remain operational gates

This harness intentionally has no automatic reconciliation or resource adoption. An uncertain create, an existing/ambiguous inventory or a failed canary requires lead inspection of retained evidence and read-only provider state. Nothing in this review permits another blind POST or PUT.

Account and S3 credentials retain broad authority; method allowlists reduce accidental application actions but do not restrict what a stolen key can do. Runpod lacks versioning/Object Lock, and the HEAD-before-random-PUT sequence is not a provider-enforced write-once guarantee against an independent remote writer. The first canary is deliberately below the multipart boundary and does not test large transfers.

The recorded estimated rate, credit floor, projected runway and review deadlines do not stop recurring provider billing or enforce a lifetimeUSD50 cap. The lead still needs the actual recurring cost/credit observation and dated review required by D009 before calling this storage managed. No project data moves in Stage A. Consistent project snapshots, off-Mac key/account recovery, isolated project restore, trusted freshness and unattended-effect barriers remain separate stages.

## Exact inspected identities

| Artifact | SHA-256 |
| --- | --- |
| Corrected `runtime/runpod/stage_a.py` | `d5371dd9e4b3618229c3c1e2bcf48944bf2f2464175e2130b4e68f67bc847156` |
| Preserved initial harness | `813fd89b003247a6620481ec218c53cdb5ae25f8cf254a49c72b17820cc8f08e` |
| Initial independent reproducer | `def8c43d3a4242b442bb5272f9f67cbed07d2256cc8a797f4ebcdd6b682eeadb` |
| Corrected independent probe | `7bb62d5bd743138dacfc7b342c49dbb2292650ea1e7db59cba01a7bf402a07f8` |
| Corrected probe output | `aaf04ea80b5d03a5d24e12b3b49ac78fb3b95b2ce7d6c3f8c3fd670505aa23f7` |
| `scripts/configure_runpod_s3.py` | `f2ca9b81d32a49e78bf5c847b992ac57e4b1cbecffab6d50a159622506bfcb5f` |
| Accepted D009 contract | `68eea41a20a171681e53368b98954fefa8e65e7513ec21b6dc482dfc25851c61` |

Public references checked: [Runpod S3 support and capabilities](https://docs.runpod.io/storage/s3-api), [AWS SigV4 single-payload signing](https://docs.aws.amazon.com/AmazonS3/latest/developerguide/sig-v4-header-based-auth.html). Actual account observations remain lead evidence, distinct from this review.

## V2 correction: identifier reflection and preserved pre-create failure

**No remaining blocker was found in the narrow v2 correction at SHA-256 `37ccc56c1b2f4b0949a21bce0137fdf9015d36a1d1387616458ad9cd23c09b05`.** This supplements the preceding review; it does not erase its missed case or accept an actual resource, transfer or managed-storage operation.

**P2, closed in v2: v1 treated the S3 access-key identifier as an authentication secret.** The lead reports that Runpod's legitimate `myself.id` matched that identifier, so v1 refused with `credential_reflected` during the account preflight, before the create request. The original review did not exercise that equality and therefore missed this false positive. The lead reports no create mutation and preserved the consumed v1 attempt. This continuation did not inspect private account evidence and does not independently certify that actual-account history; the retained invented reproducer demonstrates the corresponding code path and absence of a dispatch marker.

The inspected diff adds `secret_values`, which screens the management API key and S3 secret access key in both management and S3 responses. It excludes only the S3 access-key identifier. The account response must still match the pinned identity digest, and retained preflight metadata contains that digest rather than the identifier. If the identifier also equals either authentication secret, the response still refuses. The correction therefore addresses the false positive without removing either secret from reflection screening. This is a source-level credential taxonomy distinction, not a claim that account identifiers should be published.

V2 uses the separate `runtime/runpod/stage-a-v2` state directory, leaving the consumed v1 files unchanged. Its lock excludes other cooperating v2 actors; it is not a shared lock across the two version directories. The separate directory does not itself establish that another create is safe: the lead's determination that v1 stopped before dispatch remains the operational prerequisite. V2 still refuses an existing or ambiguous inventory and consumes its own attempt before transport, with no automatic create or PUT retry. It must not be used to bypass an uncertain earlier create.

### Retained synthetic evidence and review attribution

The predecessor independent critic completed seven new transport-level probes and nine earlier boundary probes adapted to v2, then stopped with a capacity error before writing this final record. I inspected those probe sources, retained passing outputs, the exact v2 source and its diff from preserved v1. I did not rerun the probes or count producer checks as independent tests. Evidence kind throughout these probes is `synthetic_fixture`; the transport returns invented account and resource values and the tests use temporary directories.

The seven new probes cover the original pre-create false positive and consumed attempt; acceptance of the matching public identifier followed by exactly one invented create while preserving v1 files; refusal of a wrong account; continued refusal of each authentication secret in management and S3 bodies before persistence; acceptance of the identifier in an invented S3 error body; identifier/secret equality remaining blocked; and v2 lock exclusion. The nine retained boundary probes cover durable intent and one-shot dispatch, exact response-byte retention, consumed ambiguous create, fresh-resource mismatch, lock exclusion, endpoint/method/redirect refusal, reflected-secret refusal, refusal before response persistence, and observed HTTP-error retention without retry. Their retained outputs report seven and nine tests passed respectively. These observations establish behavior under the specified mocks, not real Runpod behavior.

This continuation read no `.env`, real account response, private database, financial result or raw model output. It made no account call, provisioning request, canary transfer, paid model call or financial run. The earlier review's operational limits remain in force. Separate quality and scope dispositions, actual exact-resource verification, actual encrypted-canary evidence and required cost observations remain distinct acceptance evidence.

| V2 artifact inspected | SHA-256 |
| --- | --- |
| `runtime/runpod/stage_a_v2.py` | `37ccc56c1b2f4b0949a21bce0137fdf9015d36a1d1387616458ad9cd23c09b05` |
| Independent `critic/probe_v2.py` | `3506536d9c74d5217cecf3dbf47f44339b78a14de3fef915320c7a4650d3efda` |
| Retained `critic/v2-probe-output.txt` | `154e6734b5a7911274a5d8ab06e6f087e7144f20240e5c411d5b42701036a1fc` |
| Independent `critic/probe_v2_boundaries.py` | `0e25602623f769b7d2db693ae9a1b7f3af351d327887c77a62dc04b47d35cd73` |
| Retained `critic/v2-boundaries-output.txt` | `088bbcfd5db89d0c99f6861aeda9e6df91e6b191bcfa0d589af9f14ee6e45643` |
| Accepted D009 contract, unchanged | `68eea41a20a171681e53368b98954fefa8e65e7513ec21b6dc482dfc25851c61` |

Continuation reviewer: `/root/d009_v2_critic_finish`, separate from the producer, execution-quality reviewer and scope reviewer. The retained independent probes are predecessor critic evidence; this disposition adds independent source/evidence inspection with the limits stated above.

## V3 canary-only handoff

**No remaining code blocker was found for the bounded first v3 synthetic PUT at source SHA-256 `38880a7e8b97a1ebaccaf5c9012b4b879f3d0bf81098f2c2a82cbbdf1e2230df`.** This disposition covers the canary-only handoff, destination identity, restricted transport and preserved uncertainty rules. It does not accept an actual canary result or any project backup.

The lead reports that v2 provisioned exactly one volume and retained a verified provision receipt with SHA-256 `ed87c3480170b09b67f72e8a4f5b66a7c7c6e7f77199502a90e9794d445e5fff`. The lead also reports that v2's canary stopped at the absence check before any PUT or dispatch marker: the custom request returned403, AWS CLI returned404, and a custom GET reported Cloudflare1010. Its read-only request with the descriptive application user-agent `quanto-recovery/0.1` then returned404. These are lead-attributed actual observations; I did not read the private receipt/account responses or repeat those requests. The observations support trying the application user-agent in the separately reviewed controller, but do not establish that a PUT or readback will succeed. All earlier attempts and the original missed identifier-equality case above remain part of the history.

Source inspection confirms that v3 has no `provision` function or provisioning CLI choice. Both the management helper and raw transport admit only the exact read-only account GraphQL query and a GET of one volume; volume POST, arbitrary GraphQL payloads, list/create routes, compute, resize and deletion are absent or refused before transport. The S3 boundary admits HEAD, PUT and GET for the exact regional HTTPS host and restricted opaque object path. Query strings, redirects, alternate authorities and unsupported methods refuse. Every outgoing request adds the truthful application user-agent. This is an application guard, not a restriction on the broad authority of stolen credentials or a filesystem owner's ability to replace code.

The handoff requires the exact pinned v2 provision-receipt bytes, pinned account/source/endpoint metadata and the expected10GB STANDARD US-WA-1 volume. It additionally requires a matching prior synthetic attempt/failure pair with the fixed absence-check error, explicit `put_may_have_occurred: false`, automatic retry false, matching object key and volume, and absence of both the prior PUT marker and success result. It records hashes of those prior files in its own attempt and result. These local checks bind the supplied history; they do not independently prove the provider had no effect if local evidence were maliciously replaced. The ordinary local-owner threat boundary remains unchanged.

Unlike v2's separate version directories, v3 takes both the existing v2 lock and its own v3 lock, retaining v2 files without rewriting them. It chooses a new random opaque key and records a one-shot v3 intent before account/volume checks. A fresh volume GET must reproduce the chosen volume. The absent-key HEAD must return404 before the durable PUT marker and single PUT; timeout or later failure retains possible mutation and refuses automatic replay. A second invocation cannot replace the consumed attempt. The unchanged canary path compares remote length and ciphertext SHA-256, authenticates decryption, compares plaintext bytes, and checks a wrong key locally. A successful canary would establish only this synthetic transfer path.

### Independent v3 probes

I executed eight focused tests in `critic/probe_v3.py`, all passing, with evidence kind `synthetic_fixture`. They use invented receipts and temporary directories, substitute only the provision digest for the invented fixture, and mock transport responses/account preflight where needed. They verify exact receipt-byte tamper refusal and provenance, ambiguous/mismatched prior history refusal, prior marker refusal including dangling symlinks, v2/v3 lock exclusion in both directions, refusal of raw creation/authority-expansion routes before transport, the forced application user-agent and continued reflection refusal for both authentication secrets, consumed v3 attempts with unchanged v2 bytes, and a fresh destination change stopping before encryption or S3. No actual environment file, provider response, account, private database or financial artifact was read, and no network or provider call occurred.

These tests do not execute the full encryption/S3 round trip or establish provider compatibility. Separate quality reports its own real local age exercise, mocked full transfer and failure paths, and reference SigV4 comparisons; those are not included in my eight-test count. No producer tests are represented as independent critic tests. No new defect was reproduced in this bounded revision, so no source modification was requested.

The frozen source hash was checked before and after the probes. Prior-report gates remain: actual result verification, recurring billing observation and operational cost review are distinct; project-data capture, off-Mac production key custody, restore, trusted freshness and unattended effects remain future work. A v3 uncertainty must receive read-only reconciliation before any later distinct mutation.

V3 reviewer: `/root/d009_v2_critic_finish`, separate from the producer and execution-quality reviewer. Probe and output identities below identify this review's own executed evidence.

| V3 artifact inspected or executed | SHA-256 |
| --- | --- |
| `runtime/runpod/stage_a_v3_canary.py` | `38880a7e8b97a1ebaccaf5c9012b4b879f3d0bf81098f2c2a82cbbdf1e2230df` |
| Independent `critic/probe_v3.py` | `67f5de25b0dbded43bfd5b0558e17a27414fd4048e7aa248097e683b405085e8` |
| Retained `critic/v3-probe-output.txt` | `914ec05ed7b7012f25a38c214610f77aaacf6510b113eb846689561190e4412e` |

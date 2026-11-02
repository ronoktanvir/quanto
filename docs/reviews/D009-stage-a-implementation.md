# D009 Stage A implementation preparation

**The bounded provisioning and encrypted-canary harness is prepared; actual execution has not occurred.** It implements only the accepted destination and synthetic transfer stage. It cannot upload project files, create compute, top up credit, resize or delete a resource, restore a project, launch a worker or retry a remote mutation automatically.

Producer: `/root/d009_stage_a_builder`. Read the governing context, D009 proposal, all five perspectives and the accepted policy. No actual credential file, account resource, private database, financial result or stored model response was accessed. All executed HTTP/S3 tests use injected invented responses. The only executed encryption uses generated temporary identities and synthetic bytes.

## Prepared identities and invocation boundary

| Artifact | SHA-256 |
| --- | --- |
| Ignored `runtime/runpod/stage_a.py` | `d5371dd9e4b3618229c3c1e2bcf48944bf2f2464175e2130b4e68f67bc847156` |
| Ignored `runtime/runpod/stage_a_builder_probe.py` | `dd29042ce8578bca5917cb4627ae5f90b23e317bb9f9ed3fea71d5032f07d1e8` |
| Accepted D009 policy inspected | `68eea41a20a171681e53368b98954fefa8e65e7513ec21b6dc482dfc25851c61` |

The lead may invoke `provision --execute-reviewed-stage-a`, followed only after a verified provision outcome by `canary --execute-reviewed-stage-a`. This report is not independent acceptance or an instruction to run those commands before criticism and quality finish. There is no CLI resume, retry, arbitrary endpoint, arbitrary payload or deletion option. Importing the module performs no account or credential read.

## Resource and mutation controls

Both operations acquire the same nonblocking local `flock`. An exclusive, fsynced intent file is created before preflight. Another invocation refuses even if the earlier process died; it never implicitly resumes. A separate dispatched marker precedes each POST or PUT. Failure after that boundary records the outcome as potentially applied and directs the lead to read-only reconciliation. No automatic adoption of a name match is implemented; ambiguous creation must be investigated externally before any new decision.

Provisioning binds the privately pinned account hash, checks at least USD5 credit and90days projected account runway including the proposed volume, verifies STANDARD availability in US-WA-1, and requires an unpaginated empty volume inventory. It sends exactly one fixed10GB STANDARD create request with a random retained name. The exact returned properties and ID must agree with a fresh GET. No region or premium-tier substitution occurs. An unrelated existing volume causes conservative refusal, not modification.

The initial receipt records the estimated USD0.70/month before tax, the USD50 total authorization, zero new deposit, tax-inclusive consumption scope, a72hour first billing-observation deadline and a30day review deadline. These are persistent deadlines, not a scheduled monitor or provider lifetime cap. The lead owns registering the recurring read-only check. Account-wide billing settings remain unchanged.

## Transport and credential boundaries

The controller reads only the three named Runpod credentials from a bounded regular mode0600 file and rejects duplicate, malformed or missing values. It does not retain credential values, HTTP Authorization headers or remote error text. Known credential reflection in a response causes a fixed refusal. JSON receipts contain selected identities, exact body hashes, bounded counts and fixed outcomes.

Management uses the fixed API host and narrowly allowed paths. S3 uses only the exact regional HTTPS host, an allowlisted volume/object path and HEAD, PUT or GET. Python's default verified TLS context remains enabled; environment proxies are disabled; the redirect handler never follows a redirect. Responses have explicit byte limits, socket timeouts and a180second CLI deadline. No HTTP retry loop exists.

S3 uses standard AWS SigV4 HMAC header signing with SHA-256 payload binding. This avoids relying on AWS CLI transport redirect behavior. It is not custom encryption: age provides authenticated encryption. The three synthetic HEAD/GET/PUT signatures were compared against the official signer bundled with the installed AWS CLI. The protocol reference is [AWS signing documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_sigv-create-signed-request.html).

Only age and age-keygen execute as children. Their environment contains PATH, a temporary HOME and locale settings, with no management, S3, broker or model credential. The trusted controller necessarily handles both credential types; the accepted policy explicitly distinguishes that fact from granting credentials to an external worker.

## Canary evidence boundary

The canary consists only of a fixed synthetic marker and32 random bytes. Temporary private age identities are generated locally, an incorrect identity must fail decryption, and the ciphertext must have the expected format. HEAD must return404 for the exact random object key before the one PUT; a403 does not count as absence. After upload, HEAD and GET lengths must match, the downloaded ciphertext SHA-256 must agree, and authenticated decryption must reproduce the original bytes.

The remote ciphertext remains retained. The temporary canary identities and local payloads are removed by normal temporary-directory cleanup; they are not the future project recovery key. A failed/uncertain PUT remains identified by exact key and ciphertext digest. Reconciliation can inspect that identity without retrying the PUT, but a failed canary is never promoted into a successful decrypt/restore claim. ETag is not used as a digest.

## Durable receipt paths

All actual receipts would be under ignored `runtime/runpod/stage-a/`, with private file permissions:

- `provision-attempt.json`: fixed resource request, source identity, cost limits and review deadlines.
- `preflight.json`: account hash, credit/runway threshold checks, catalog region and empty inventory.
- `create-dispatched.json`: pre-send marker and exact create-request digest.
- `create-response.body.json` and its `.metadata.json` sidecar: exact bounded credential-checked response bytes plus HTTP status/hash/length, including an observed error response. No headers are retained.
- `create-response.json`: selected returned volume properties and response hash/length.
- `provision-result.json` or `provision-failure.json`: verified destination, or preserved uncertainty/refusal.
- `canary-attempt.json`: exact volume and new object key before canary preparation.
- `put-dispatched.json`: pre-send object key, ciphertext digest and length.
- `canary-result.json` or `canary-failure.json`: observed round-trip conditions, or preserved uncertainty/refusal.

The readonly monitor must inspect these and fresh authorized account metadata. It must never rerun either mutation command as a health check. Stage A success fields explicitly set project-data upload and project-backup acceptance false.

## Executed preparation evidence and limitations

Thirteen producer fixture tests pass, with four account-boundary subcases and three independent synthetic signature comparisons. They cover successful one-shot provision, refusal of repeat invocation, lost creation response, existing inventory, wrong tier/account, credit/runway/nonfinite values, fresh GET disagreement, concurrent lock refusal, real age round trip/wrong-key refusal on synthetic bytes, corrupted readback, uncertain PUT,403 absence refusal and endpoint/method/redirect restrictions. No fixture contacts Runpod. Compilation and Ruff pass.

Independent criticism found that the first prepared candidate (`813fd89b003247a6620481ec218c53cdb5ae25f8cf254a49c72b17820cc8f08e`) retained only a projected create result and the original body hash. Optional provider fields and exact bytes were lost. The revised candidate preserves the full checked body before status/schema reduction, with HTTP metadata separately. A new fixture verifies exact whitespace, optional timestamp/extra-field retention and error-body preservation before refusal. This was a preparation defect corrected before any actual call; the independent critic is rechecking it.

Two preliminary attempts to import the installed AWS signer used the wrong bundled package path and produced import errors; no network or account operation occurred. The corrected comparison locates AWS CLI's bundled botocore through its own package path and passes for all three supported S3 methods. Those preparation errors do not represent failed provider calls.

This is producer evidence. Independent criticism and quality must inspect the exact prepared hash before actual use. The harness does not test provider price, billing settlement, actual S3 compatibility, resource creation or a real project restore. A successful future canary closes only the transfer-path evidence; Stage B snapshot/key custody/restore, Stage C trusted freshness/effect barriers, R14 and the full operation remain incomplete.

## V2 correction after the first actual preflight refusal

**The new v2 candidate corrects credential taxonomy without changing resource or transfer authority.** The lead reports that the first actual provision preflight stopped at `credential_reflected`, with `creation_may_have_occurred=False` and no create-dispatched marker. Its safe comparison found that Runpod's S3 access-key identifier equals the account's `myself.id`; the management API key and S3 secret do not. Those actual observations are attributed to the lead. This producer did not inspect the credential file, account response, actual failure receipt or account resource.

The original guard checked every credential value, including the access-key identifier. That identifier legitimately appears in the account response, so the guard refused before any resource POST. V2 explicitly distinguishes the public identifier from the two authentication secrets. Both management and S3 responses still refuse reflection of the management API key or S3 secret. Account metadata continues to expose only the pinned account hash; no access identifier is printed or logged. Private exact create-response preservation remains unchanged.

The original source at `d5371dd9e4b3618229c3c1e2bcf48944bf2f2464175e2130b4e68f67bc847156` remains byte-identical. V2 is a new file and uses the separate `runtime/runpod/stage-a-v2/` state directory with the same receipt filenames described above. Original attempt files remain untouched. Source differences are limited to version description, state directory, the `secret_values` helper and its use in the two transport wrappers. There is no automatic retry or adoption. The lead must make a separate decision to execute a new first-create attempt after independent criticism, quality and scope checks.

| V2 prepared artifact | SHA-256 |
| --- | --- |
| `runtime/runpod/stage_a_v2.py` | `37ccc56c1b2f4b0949a21bce0137fdf9015d36a1d1387616458ad9cd23c09b05` |
| `runtime/runpod/stage_a_v2_builder_probe.py` | `2d4adc7d8a8edd6c0e07ca58407731cdbe08d238156e83e2628903c87efa2059` |

Fifteen producer tests and the three official AWS signer comparisons pass for v2. The new fixture passes an invented GraphQL account response through the actual bounded HTTP/parser path with `account.id` equal to the synthetic S3 access identifier; the account check succeeds and its returned metadata contains only the hash. Four separate reflection subcases confirm that each actual secret still refuses on each transport. All prior one-shot, ambiguity, mutex, destination, credit/runway, age wrong-key, ciphertext-readback and no-retry fixtures continue to pass. Compilation and Ruff pass. No actual network, credential, database or project-data access occurred in these tests.

This is a preflight usability correction, not a storage purchase or successful canary. Independent v2 criticism and quality are in progress at this producer checkpoint. No additional actual execution was performed by this producer.

## V3 canary-only correction after the actual transport refusal

**The new v3 candidate tests only the already-created volume; it has no resource-creation capability.** The lead reports that v2 provision completed once at 2026-11-02T11:06:25.659093Z, then the actual canary refused at `canary_key_not_proven_absent`, with `put_may_have_occurred=False` and no PUT marker. Those actual outcomes are lead-attributed. This producer has not read actual receipts, credentials or account state and has made no authenticated provider call.

The lead's controlled read-only comparison isolated the request user-agent: the custom client received Cloudflare's `error code: 1010`, while the same signed HEAD with only `User-Agent: quanto-recovery/0.1` returned404, matching the official AWS client. [Cloudflare's Error1010 documentation](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/) identifies default urllib user-agent filtering and recommends an application-specific identifier. V3 sends that honest identifier; it does not impersonate a browser or alter the existing SigV4 algorithm.

V3 pins the root-supplied SHA-256 of the verified v2 provision receipt and requires its v2 source identity, account hash, exact10GB STANDARD US-WA-1 properties and endpoint. It also checks the old canary attempt/failure: same volume and object identity, the exact absence-check refusal, Boolean false for possible PUT, no dispatched marker and no successful result. A fresh account check and GET must confirm the destination before any canary upload. The old receipt's source and the current canary source are recorded separately; the new code does not pretend to be the provisioning revision.

The new controller acquires both the old v2 operation lock and its separate v3 lock. It leaves the old source, attempt and receipt bytes unchanged. The provision function and CLI choice are removed. Both the management wrapper and its underlying transport reject volume POST, DELETE and arbitrary GraphQL operations; only the exact account-read query and an individual-volume GET remain. Encryption, wrong-key testing, pre-PUT absence, one-shot dispatch, ciphertext length/hash and authenticated plaintext verification retain their earlier boundaries.

| V3 prepared artifact | SHA-256 |
| --- | --- |
| `runtime/runpod/stage_a_v3_canary.py` | `38880a7e8b97a1ebaccaf5c9012b4b879f3d0bf81098f2c2a82cbbdf1e2230df` |
| `runtime/runpod/stage_a_v3_builder_probe.py` | `7b2ed8d3d9e40706fa1b4ea5ee9d957dfbcd3a8acd11d5948e74f9f3b21d0bca` |
| Pinned actual v2 provision receipt; digest supplied by lead | `ed87c3480170b09b67f72e8a4f5b66a7c7c6e7f77199502a90e9794d445e5fff` |

Thirteen producer fixture tests and three official AWS signer comparisons pass. The fixtures cover exact receipt/source binding, old uncertainty/marker/result/mismatched-volume refusal, destination drift, overlapping controllers, honest user-agent propagation on five request forms, absent creation/GraphQL-mutation routes, real age encryption and wrong-key failure on synthetic bytes, corrupted readback, lost PUT with no retry,403 refusal, secret reflection and endpoint/redirect limits. A complete synthetic round trip verifies old receipt bytes remain unchanged and current/prior source identities remain distinct. Compilation and Ruff pass. All network operations are injected; default real-network construction is forbidden in the fixture suite.

The lead may separately approve `runtime/runpod/stage_a_v3_canary.py canary --execute-reviewed-stage-a` after independent criticism, quality and scope. This producer has not run it against the account. New receipts use `runtime/runpod/stage-a-v3/canary-attempt.json`, `put-dispatched.json`, and `canary-result.json` or `canary-failure.json`; prior provision and failed-canary evidence remains in `stage-a-v2/`. This is a reviewed correction after a proven pre-PUT refusal, not an automatic mutation retry. No project data transfer, usable backup, managed cost monitoring, Stage B or Stage C completion follows from these fixture results.

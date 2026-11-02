# D009 actual storage and encrypted transfer

One 10 GB STANDARD Runpod network volume in US-WA-1 was created and verified. A 267-byte encrypted synthetic canary was subsequently uploaded once, downloaded, checked by length and SHA-256, and decrypted to the original test bytes. No project data has been uploaded and no project backup or restore is accepted.

The lead executed the resource and transfer operations. Separate implementation, criticism, quality and scope reports identify the exact code reviewed. The post-execution quality reviewer inspected an explicitly sanitized result projection and the frozen source; that is independent consistency inspection, not a second provider execution or inspection of private account receipts.

## Observed outcomes and preserved failures

The original provisioning preflight refused before creation because its reflection guard treated a legitimate public account/access-key identifier as an authentication secret. V2 preserved the management-key and S3-secret guards while correcting that classification. Its one actual creation succeeded at 2026-11-02T11:06:25.659093Z, with a fresh GET confirming the exact resource. No further resource was created.

V2's canary then stopped before PUT: the absence check returned 403 and no PUT marker existed. Read-only reconciliation found the key absent through the AWS client. The custom client received Cloudflare error 1010; using the descriptive `quanto-recovery/0.1` application identifier returned the expected 404. Cloudflare documents default Python client identification as a possible cause and recommends an appropriate User-Agent. [Cloudflare error 1010](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)

V3 permits only a synthetic canary on the pinned existing destination. It has no provisioning command or volume-creation route, requires the preserved pre-PUT refusal, obtains both version locks and uses a new opaque object key. After separate criticism, quality and scope acceptance, the lead executed it once. It returned verified at 2026-11-02T11:26:12.447810Z, exit 0 with empty stderr. The single PUT was followed by matching HEAD/GET length, ciphertext digest and authenticated plaintext comparison. A wrong decryption key failed. Temporary canary identities were removed; the remote synthetic ciphertext remains for read checks. Prior refusals remain unchanged.

| Retained evidence | SHA-256 |
| --- | --- |
| V2 provisioning source | `37ccc56c1b2f4b0949a21bce0137fdf9015d36a1d1387616458ad9cd23c09b05` |
| Private verified provisioning receipt | `ed87c3480170b09b67f72e8a4f5b66a7c7c6e7f77199502a90e9794d445e5fff` |
| V3 canary-only source | `38880a7e8b97a1ebaccaf5c9012b4b879f3d0bf81098f2c2a82cbbdf1e2230df` |
| Private verified canary receipt | `fedb7b568d2ea28e22bcfc5004e3cced01d444d56ec096a8a3b02db58b6e5b3d` |
| 267-byte ciphertext | `140f6dc4332389d99c219ef995762b013025c20e4154fc6e20a9e7ca34b8cebc` |
| Sanitized execution projection | `477bfb9779fbeebcdace1b671c7e83895640d468c1dcab4dbfef6802f624ab2c` |
| Safe execution stdout | `24a39475a96d6e1733be4cd171138463882737f05d044f36b28970b872a357ae` |

## Costs and operation

The stated STANDARD rate gives an estimate of USD 0.70/month before applicable tax for 10 GB. Existing account credit funded creation; no deposit, compute rental, resize or account-wide payment-setting change occurred. The owner-authorized USD 50 cumulative ceiling and USD 45 early-action threshold remain separate from model budgets. This is locally monitored authorization, not a provider-enforced lifetime spending cap. [Runpod network-volume pricing](https://docs.runpod.io/storage/network-volumes)

The initial billing request omitted an end time and returned 400. A corrected bounded request with both timestamps returned 200 and zero records at 11:15:11Z. No posted charge or tax treatment was observed at that checkpoint; an empty billing response does not establish zero accrued cost. The first-charge review is due by November 5 at 11:06:23Z, and the initial 30-day cost review by December 2 at 11:06:23Z.

The daily 09:00 local `quanto-storage-health-and-budget` heartbeat is registered ACTIVE. Its private configuration pins the resource, provisioning receipt and now the accepted canary receipt. It checks storage, credit/billing and website health without creating resources, uploading projects, deleting copies or replaying research. No future scheduled execution has yet been observed. It needs the Mac and app available; stopping local work does not stop provider storage charges.

At 11:26:41Z the website returned ready. Its five-minute capture metadata reported success at 11:25:24Z and the next attempt at 11:30:24Z. Website captures remain distinct from external research recovery checkpoints.

## Remaining acceptance gates

Stage A now has actual destination and encrypted-transfer evidence. Stage B still requires a reviewed consistent real-data capture, explicit source-use rights and omissions, a permanent decryption identity retained outside this Mac, account recovery and an isolated downloaded restore. Stage C still requires external pre/post-effect records, single-writer fencing and a separately accepted freshness boundary. None of these observations completes R14, validates a strategy or authorizes live trading.

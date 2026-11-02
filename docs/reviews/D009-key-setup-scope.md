# D009 permanent-key setup: independent scope review

**The frozen helper and runbook are ready for the owner's local setup step within the accepted Stage B preparation scope.** Criticism and execution-quality reviews identify no remaining blocker at the exact source below. No new purchase, council decision or owner spending approval is needed. Running the helper creates and verifies a local key; it does not establish off-Mac custody, account recovery, project backup or Stage B acceptance.

Reviewer: `/root/d009_scope`, separate from the producer, critic and quality reviewer. I read the complete helper, runbook, accepted D009 contract and final independent reports. I executed no test, key-generation command or network call and read no actual key, environment file, account response, private runtime record or financial data. The existing Stage A scope report remains unchanged by this review.

## Implementation and claim boundary

The helper creates one age identity at the fixed ignored `runtime/recovery/identity.txt` path, refusing an existing file or unsafe path rather than silently rotating a key. It uses owner-only creation permissions and a private recovery directory, checks ownership/inode/link conditions and syncs accepted output. Key-generation stdout goes directly to the private file descriptor; the key is not returned, logged or put in command-line arguments. Children receive a small explicit environment without inherited cloud/model credentials.

Only a fixed synthetic plaintext is encrypted and decrypted locally. Successful output contains the public recipient and its public-byte fingerprint. The result explicitly leaves off-Mac custody and account recovery false, and the terminal text preserves those pending gates. There is no cloud upload, account mutation, project-payload selection, spending or research/trading path. Failure preserves a potentially generated identity for review, because deleting it or recreating it could invalidate an external copy that already exists.

These controls are appropriate to local preparation. They do not isolate the key from another process with the owner's privileges, a compromised Mac or replaced installed binaries. The guide states that limitation and does not promise that a private local file alone survives loss of this Mac.

## Owner command and off-Mac next step

The runbook's one-time command matches the helper location and current workspace:

```sh
cd /Users/ronoktanvir/Documents/ChatGPT/quanto && .venv/bin/python scripts/configure_backup_key.py
```

On success the owner should save the entire identity file in an existing independently accessible password manager or secure external storage, along with the public recipient and fingerprint. The guide correctly says not to paste private contents into chat, a shell command, an issue or Git. Opening the file in the owner's trusted local editor or importing it directly into the vault is an owner action, not permission for an agent to display it in tool output. An optional convenience command may reveal the file in Finder without printing its contents:

```sh
open -R /Users/ronoktanvir/Documents/ChatGPT/quanto/runtime/recovery/identity.txt
```

No runbook change is required for that optional convenience. The owner must preserve any failed/interrupted identity and report only the failure, rather than delete it to force another generation.

The requested custody statement is correctly limited to an owner report. It is not automated evidence that a vault entry exists or that disaster recovery works. A subsequent check must use material retrieved from the external location, derive the same recipient and decrypt a synthetic challenge. Runpod login/email/2FA recovery is a distinct dependency. Both must be demonstrated under the accepted procedure before an isolated downloaded project restore can establish recovery. User participation here supplies missing custody/recovery evidence; it is not a repeat request for spending permission.

## Independent evidence and exact identities

The critic reports six independent mocked-child tests, including concurrent creation, timeout/interruption retention, nonignored/unsafe target refusal and invalid output without success reporting. Quality reports 14 tests plus 9 subtests in both the source layout and a separate clean three-file layout, lint in both, and two additional independent tests covering five refusal cases. All use invented values and mocked children. Neither review claims actual permanent-key generation or proves that the current installed programs and checkout will pass; those results will come from the owner-run helper.

After both reviews completed, the lead separately reported checking that the actual target path is ignored and that no permanent identity exists yet, without reading a secret. That limited checkout observation is lead-attributed; I did not repeat it. It does not establish successful age interoperability, external custody or recovery.

| Inspected artifact | SHA-256 |
| --- | --- |
| `scripts/configure_backup_key.py` | `04507378fc1aeb0240b49b61843eede40eb0a2f5d691ca1b5a60e43fe44f4cbe` |
| `docs/BACKUP_KEY_SETUP.md` | `e54b61d4d4197b2edeb34ed2c591e24ec8b4ffc5197768b3c4d39380f417d73b` |
| Accepted D009 policy | `68eea41a20a171681e53368b98954fefa8e65e7513ec21b6dc482dfc25851c61` |
| Independent key-setup critic report | `5d9bcefabf795f90d49ea5de1908a75cfa3043fb4a218c6bb43fb2dd2bdfc855` |
| Independent key-setup quality report | `c40a219d737a53b77e838ec7ec2272edef7196966d0beef55c94c72f993c455e` |

No scope objection remains to presenting the command and runbook to the owner. No permanent identity was generated or custody result established by this scope review. Consistent capture, data-use rights, typed object closure/tombstones, isolated project restore, cost observations, trusted freshness, unattended operation and R14 remain separate incomplete gates. Permanent key creation must not change `project_backup_accepted` to true or expose the private identity to a future uploader/archive.

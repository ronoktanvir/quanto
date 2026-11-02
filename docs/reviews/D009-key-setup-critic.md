# D009 permanent-key preparation: independent criticism

**No remaining code blocker was found in the frozen local key-setup helper identified below.** This accepts preparation for an owner-run local setup, not off-Mac custody, account recovery, a project backup or Stage B completion. No permanent identity was generated during this review.

Reviewer: `/root/d009_v2_critic_finish`, separate from the producer. I inspected the helper, its producer tests, runbook, accepted D009 contract and public Stage A outcome report. I read no `.env`, existing key, actual runtime receipt, account response, private database or financial result. I made no network, provider or paid-model call. All executed probes used invented bytes and mocked subprocesses in temporary directories; their evidence kind is `synthetic_fixture`.

## Key handling and refusal boundaries

The helper fixes the destination to the ignored `runtime/recovery/identity.txt`. It checks that the project path is absolute and has no symlink components, that the project and runtime directory are owned by the current user and not group/world writable, and that the recovery directory is owned by that user with mode0700. Git's `check-ignore` must succeed before key creation. An exclusive no-follow open creates the identity at mode0600, followed by regular-file, ownership and single-link checks. Existing files, hardlinks, symlinks and directories cannot be replaced through this creation path. A second cooperating invocation loses at the exclusive open, including while the first key-generation child is running.

The generation child is the exact `/opt/homebrew/bin/age-keygen` path. Its stdout goes directly to the already-opened private identity descriptor; private bytes are not captured for display or placed in arguments or the child environment. Public derivation uses the identity's path, and the public recipient must pass a bounded format check. Encryption/decryption use the exact `/opt/homebrew/bin/age` path with synthetic input only. All child environments contain only PATH, LANG and LC_ALL; stderr is discarded, stdin is disabled unless supplied with the explicit synthetic challenge/ciphertext, and timeout/errors become fixed reason codes. Source inspection found no network, Git write, upload or private-key logging path.

The successful path fsyncs the identity, verifies the generated file's size/mode/inode relationship, checks synthetic encryption and authenticated plaintext equality, and fsyncs the containing directory. Failure or interruption retains any newly created file and prevents an automatic replacement on rerun. The runbook correctly requires review of an interrupted identity before reuse or deletion. These controls do not isolate the key from a compromised Mac, a hostile filesystem owner or replaced installed binaries; the source and runbook explicitly retain that local trust boundary. A retained partial file is not accepted as a usable recovery identity.

## Verification and custody claims

The helper returns only the public recipient, its SHA-256 fingerprint, local-roundtrip success and two explicit false fields: `off_mac_custody_confirmed` and `account_recovery_confirmed`. Its terminal success text preserves those limits. Local decryption demonstrates that the local identity can decrypt the local synthetic challenge; it cannot establish that an external copy exists or that the owner can recover their account.

The runbook therefore requires the owner to save the full identity outside this Mac, retrieve it without this Mac, and separately confirm Runpod/email/2FA recovery. It asks for a public custody statement rather than private contents. A later challenge must use the externally retrieved copy and match its public recipient before recovery acceptance; consistent backup capture and isolated restore remain separate gates. This distinction matches D009's requirement that a key available only on this Mac is insufficient for disaster recovery.

## Independently executed evidence

Six independent tests passed, with two subcases in the invalid-output test. They exercise actual temporary-file creation and mocked child processes rather than a real key generator:

- An interleaved second invocation cannot generate another identity or replace the first; later rerun preserves its inode and bytes.
- A nonignored target refuses before creation of the private runtime directory.
- A timeout after a partial write retains mode0600 bytes, exposes only the fixed error and prevents another generation.
- An interruption through the CLI wrapper retains the invented identity and emits no private contents or success text.
- Existing hardlinks and a symlink recovery directory refuse without key generation or modification of the unrelated target.
- Invalid public derivation and incorrect decrypted bytes cannot produce success text; the candidate identity remains retained.

The child mock also asserts the exact commands, minimal environment, disabled stderr, bounded timeout and direct private descriptor, including under injected parent-environment sentinels. The independent tests are not a real age integration test, installation attestation or proof of filesystem behavior under power loss. I inspected the producer tests but did not count their reported results as my execution. No source change was requested because these probes did not reproduce a consequential defect.

The public Stage A outcome report contains no obvious claim mismatch with the reviewed canary source and stated history. It separates one created destination and a synthetic transfer from project recovery, preserves prior refusals, does not equate an empty billing response with zero accrued cost, and says the active heartbeat has no observed future scheduled execution. This is a consistency read of public claims, not verification of private receipts or linked external documentation. No financial test was repeated.

## Exact inspected identities

| Artifact | SHA-256 |
| --- | --- |
| `scripts/configure_backup_key.py` | `04507378fc1aeb0240b49b61843eede40eb0a2f5d691ca1b5a60e43fe44f4cbe` |
| `tests/test_configure_backup_key.py` | `4dd592fa85c9ebe80f811991b83bf6e803c228c6c99ede1a7c3646ad2a656736` |
| `docs/BACKUP_KEY_SETUP.md` | `e54b61d4d4197b2edeb34ed2c591e24ec8b4ffc5197768b3c4d39380f417d73b` |
| Accepted `docs/D009_POLICY.md` | `68eea41a20a171681e53368b98954fefa8e65e7513ec21b6dc482dfc25851c61` |
| Public `docs/reviews/D009-stage-a-actual.md` | `ce5bf57d2f2e25ea84b18570edc984dd21b17f728b37d755d989556f9c1f59c8` |
| Independent `/tmp/quanto-d009-key-critic-probe.py` | `e29a2b1ff8dd29e98e13215ae7f1463ffb69ed5a2c6f2f823f5930fb6114e593` |
| Retained `/tmp/quanto-d009-key-critic-output.txt` | `c602542163b1b74e5bb3e7bbddb8f71657ff2a9296604d3573b887eda01e50ae` |

The three frozen implementation/runbook hashes were unchanged after the probes. The independent synthetic harness/output remain temporary review artifacts at the stated paths and should be preserved by the lead if retained across system cleanup. Actual setup, external custody, account recovery, retrieved-copy verification and project restore remain unperformed or unverified by this critic.

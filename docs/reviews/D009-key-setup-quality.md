# D009 recovery-key setup: independent bounded quality review

**The frozen public setup helper passes the focused quality checks and is ready for local operator use, subject to the separate critic and scope dispositions.** This review validates safe local preparation and truthful pending-custody reporting. It does not establish that a permanent identity has been generated, saved outside this Mac, retrieved or used in a successful project restore.

Reviewer: `/root/d009_v2_quality_finish`, separate from the producer and critic. Evidence kind: `synthetic_fixture`. All identity/recipient/ciphertext values were invented and every encryption/key-generation/Git child in the tests was mocked. No real key generation, network, credential file, private runtime/account record, financial data or database access occurred. No helper execution against the actual project destination occurred.

## Frozen artifacts

| Artifact | SHA-256 |
| --- | --- |
| `scripts/configure_backup_key.py` | `04507378fc1aeb0240b49b61843eede40eb0a2f5d691ca1b5a60e43fe44f4cbe` |
| `tests/test_configure_backup_key.py` | `4dd592fa85c9ebe80f811991b83bf6e803c228c6c99ede1a7c3646ad2a656736` |
| `docs/BACKUP_KEY_SETUP.md` | `e54b61d4d4197b2edeb34ed2c591e24ec8b4ffc5197768b3c4d39380f417d73b` |

The hashes were independently calculated before verification and remain identical afterward. Only this review report was added; the three reviewed files were unchanged.

## Executed verification

The working-tree focused test file passed **14 tests and 9 subtests in 0.06 seconds**. Ruff passed for the helper and its tests using the repository's configured rules. A separate temporary clean directory then received only the exact helper, test file and setup guide, preserving their relative paths. The same test file passed **14 tests and 9 subtests in 0.06 seconds** there; isolated Ruff with the repository's E4/E7/E9/F selection also passed. Each command exited 0. The copy reused the existing test/lint executables; this is an independent clean-file-layout check, not a newly installed dependency environment or a full-repository test claim.

The tests exercise owner-only directory/file permissions, fixed child allowlists and a minimal child environment, secret-free output and public fingerprint derivation, preservation of an existing identity, unsafe paths/owners/permissions, nonignored-target refusal before creation, timeouts and interruptions, nonzero exits, recipient/output limits, generated-file permissions and decryption mismatch. Git's ignore result and the encryption programs are mocked, so these cases establish the helper's response to those outcomes without independently checking the actual checkout's ignore configuration or the installed programs' behavior.

Two additional independent tests covered five refusal cases beyond the supplied suite. After mocked key generation, an empty file, a file exceeding 4096 bytes and a new hard link each refuse before recipient derivation. A mocked ciphertext containing the synthetic plaintext marker, or lacking the age-format prefix, refuses before decryption. Every failed identity remains in place; a second invocation refuses rather than replacing it. No secret or success output appears. These probes used temporary invented files, a forbidden-actual-child guard and a Python socket guard, and passed in 0.006 seconds. They add evidence for the no-silent-rotation contract and the distinction between having a file and accepting a verified key.

## Source and guide consistency

The helper creates the identity exclusively with mode 0600 under a mode-0700 recovery directory, refuses symlink components and unsafe ownership/permissions, checks the generated inode and link count, and synchronizes the file and directory. Child diagnostics are suppressed and child environments exclude inherited credentials. The success output contains only the public recipient and its public-byte fingerprint. Failure paths keep the identity for review, which avoids silently rotating a key that may already have been copied or used. An owner actively replacing filesystem paths is explicitly outside the isolation boundary; permissions do not isolate secrets from a compromised same-account process.

The guide matches those behaviors and makes the recovery boundary explicit: the owner must save the complete identity outside the Mac, confirm independent retrieval and Runpod account/2FA recovery, and later demonstrate a retrieved-copy challenge and isolated restore. The helper always leaves `off_mac_custody_confirmed=False` and `account_recovery_confirmed=False`; local synthetic round-trip success cannot substitute for those later observations. No project-data transfer or recovery acceptance follows from running this helper.

No quality blocker was found within this public-helper scope. Actual local key generation and installed age interoperability remain unexecuted in this review. Off-Mac key custody, retrieved-copy verification, account recovery, independently reviewed capture/encryption, isolated restore, managed costs and the broader D009/D008 operational gates remain incomplete unless established by separate evidence. No financial validation, R14 completion or trading authority is implied.

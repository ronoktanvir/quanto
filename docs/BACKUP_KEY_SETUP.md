# Keep the recovery key outside this Mac

This setup creates a permanent age decryption identity and checks it locally. It does not upload files, create a backup, or confirm that you can recover after losing this Mac. Keep the identity for as long as any backup encrypted to its public recipient must remain recoverable.

The installed `/opt/homebrew/bin/age` and `/opt/homebrew/bin/age-keygen` are required. The helper refuses an existing identity, an unsafe path, or a destination that Git does not ignore. It writes `runtime/recovery/identity.txt` with owner-only permissions inside an owner-only directory. It does not print the secret or send it anywhere.

1. Run this once in Terminal:

   ```sh
   cd /Users/ronoktanvir/Documents/ChatGPT/quanto && .venv/bin/python scripts/configure_backup_key.py
   ```

   Success reports a public recipient, its SHA-256 fingerprint, and a passed local synthetic encryption/decryption check. The fingerprint hashes the public recipient's ASCII bytes, without a trailing newline; it is not a hash of the secret. Save these public values with your recovery instructions.

2. Open `runtime/recovery/identity.txt` yourself in a trusted local editor. Do not paste its contents into chat, a terminal command, an issue, or Git. Save the entire file as a secure note or attachment in your existing password manager, or on secure external storage. The saved copy must be accessible if this Mac is lost; a file or password-manager installation available only on this Mac does not satisfy that requirement. Close the editor afterward.

3. Check that you can retrieve the saved copy without relying on this Mac. Keep the original file unchanged. Separately confirm that you can recover access to the Runpod account and its email/2FA credentials from another device, including any recovery codes. Do not share those credentials or codes here.

4. Tell the operator only: “The recovery identity is saved outside this Mac, I can retrieve it without this Mac, and I can recover my Runpod account and 2FA.” Include the public recipient fingerprint if needed to identify the key. This is your custody confirmation, not a claim made by the helper. A later check must use a copy retrieved from that external location, derive the same public recipient, and decrypt a synthetic challenge. That retrieved-copy check, the separately reviewed backup, and an isolated restore must still succeed before recovery is accepted.

If setup stops, preserve any identity file it left and report the failure without its contents. The helper deliberately refuses to overwrite or automatically remove a key after an interrupted or failed check. Do not delete the file merely to make a second run succeed; the operator must first determine whether that identity has already been retained or used. Filesystem owners with the same account privileges can still read or replace local files; the permissions and path checks do not isolate the key from a compromised Mac.

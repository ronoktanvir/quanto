#!/usr/bin/env python3
"""Create one local age identity without displaying it or claiming off-Mac custody."""
import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile


AGE = "/opt/homebrew/bin/age"
KEYGEN = "/opt/homebrew/bin/age-keygen"
GIT = "/usr/bin/git"
RECIPIENT = re.compile(rb"age1[0-9a-z]{58}\n?\Z")
SYNTHETIC = b"quanto-recovery-key-setup: synthetic local verification only\n"


class SetupRefused(Exception):
    """Contains only a fixed, public reason code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise SetupRefused(code)


def directory_check(path: Path, *, private: bool = False) -> None:
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid(), "unsafe_directory")
    require(stat.S_IMODE(info.st_mode) == 0o700 if private else not info.st_mode & 0o022,
            "unsafe_directory_permissions")


def command(argv: list[str], directory: Path, *, input_bytes: bytes | None = None,
            destination=None, limit: int = 4096) -> bytes:
    require(argv[0] in {AGE, KEYGEN, GIT}, "program_refused")
    environment = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}
    with tempfile.TemporaryFile() as captured:
        kwargs = {"stdin": subprocess.DEVNULL} if input_bytes is None else {"input": input_bytes}
        try:
            completed = subprocess.run(
                argv, cwd=directory, env=environment, stdout=captured if destination is None else destination,
                stderr=subprocess.DEVNULL, timeout=20, check=False, **kwargs,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise SetupRefused("local_program_failed") from None
        require(completed.returncode == 0, "local_program_refused")
        if destination is not None:
            return b""
        captured.seek(0)
        output = captured.read(limit + 1)
        require(len(output) <= limit, "local_output_too_large")
        return output


def configure(root: Path) -> dict[str, str | bool]:
    require(root.is_absolute(), "absolute_project_path_required")
    # The CLI supplies its canonical source root. Reject symlink components in
    # direct callers too; a filesystem owner actively replacing paths is outside
    # this local setup helper's isolation boundary.
    for component in (root, *root.parents):
        require(not component.is_symlink(), "symlink_path_refused")
    directory_check(root)
    directory = root / "runtime/recovery"
    identity = directory / "identity.txt"
    command([GIT, "check-ignore", "--quiet", "--", str(identity)], root)
    for parent in (root / "runtime", directory):
        try:
            parent.mkdir(mode=0o700)
        except FileExistsError:
            pass
        directory_check(parent, private=parent == directory)
    descriptor = os.open(identity, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    # Keep any partial file after failure or interruption: never silently rotate
    # an identity that an operator might already have saved elsewhere.
    try:
        initial = os.fstat(descriptor)
        require(stat.S_ISREG(initial.st_mode) and stat.S_IMODE(initial.st_mode) == 0o600
                and initial.st_uid == os.getuid() and initial.st_nlink == 1, "unsafe_identity_file")
        command([KEYGEN], directory, destination=descriptor)
        os.fsync(descriptor)
        generated = os.fstat(descriptor)
        observed = identity.lstat()
        require(0 < generated.st_size <= 4096 and stat.S_ISREG(observed.st_mode)
                and observed.st_ino == generated.st_ino and observed.st_dev == generated.st_dev
                and observed.st_nlink == 1 and stat.S_IMODE(observed.st_mode) == 0o600,
                "generated_identity_refused")
        public = command([KEYGEN, "-y", str(identity)], directory, limit=128)
        require(RECIPIENT.fullmatch(public) is not None, "public_recipient_refused")
        recipient = public.decode("ascii").strip()
        encrypted = command([AGE, "-r", recipient], directory, input_bytes=SYNTHETIC)
        require(encrypted.startswith(b"age-encryption.org/v1\n") and SYNTHETIC not in encrypted,
                "synthetic_encryption_refused")
        restored = command([AGE, "-d", "-i", str(identity)], directory, input_bytes=encrypted)
        require(restored == SYNTHETIC, "synthetic_roundtrip_failed")
        parent_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
        return {"recipient": recipient, "recipient_sha256": hashlib.sha256(recipient.encode()).hexdigest(),
                "local_roundtrip_verified": True, "off_mac_custody_confirmed": False,
                "account_recovery_confirmed": False}
    finally:
        os.close(descriptor)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    try:
        result = configure(root)
    except (SetupRefused, OSError, KeyboardInterrupt, EOFError):
        raise SystemExit(
            "Key setup stopped. Existing files were not replaced. Any new identity file was kept; "
            "do not use or overwrite it until reviewed."
        ) from None
    print("Recovery identity created privately; the local synthetic encryption/decryption check passed.")
    print("Public recipient: " + str(result["recipient"]))
    print("Public recipient SHA-256: " + str(result["recipient_sha256"]))
    print("Next: follow docs/BACKUP_KEY_SETUP.md to save the identity outside this Mac.")
    print("Off-Mac custody and Runpod account recovery are not confirmed; project backup remains gated.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Save owner-supplied Runpod S3 keys locally using hidden terminal prompts."""
from getpass import GetPassWarning, getpass
import os
from pathlib import Path
import stat
import tempfile
import subprocess
import warnings


def save_keys(path: Path, key_id: str, secret: str) -> None:
    values = {"RUNPOD_S3_ACCESS_KEY_ID": key_id, "RUNPOD_S3_SECRET_ACCESS_KEY": secret}
    if any(not v or len(v) > 512 or any(c.isspace() or c in "\"'\x00" for c in v)
           for v in values.values()):
        raise ValueError("Both keys must be nonempty single-line values without quotes or spaces")
    descriptor = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > 64_000:
            raise ValueError("Configuration must be a regular file within the size limit")
        with os.fdopen(descriptor, "rb") as source:
            descriptor = None
            raw = source.read(64_001)
        if len(raw) > 64_000:
            raise ValueError("Configuration file exceeds the size limit")
        existing = raw.decode("utf-8")
    except FileNotFoundError:
        existing = ""
    finally:
        if descriptor is not None:
            os.close(descriptor)
    kept = [line for line in existing.splitlines()
            if line.partition("=")[0].strip() not in values]
    content = "\n".join(kept + [f"{k}={v}" for k, v in values.items()]) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=".env.config-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main() -> None:
    path = Path(__file__).resolve().parents[1] / ".env"
    try:
        subprocess.run(["git", "check-ignore", "--quiet", "--", str(path)],
                       cwd=path.parent, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        warnings.simplefilter("error", GetPassWarning)
        key_id = getpass("Runpod S3 access key ID (hidden): ").strip()
        secret = getpass("Runpod S3 secret access key (hidden): ").strip()
        save_keys(path, key_id, secret)
        print("Runpod S3 keys saved in the private local .env file. Existing settings preserved.")
    except (ValueError, OSError, subprocess.CalledProcessError, GetPassWarning):
        raise SystemExit("Could not save keys; check the values and local file permissions.") from None
    except (KeyboardInterrupt, EOFError):
        raise SystemExit("Cancelled; credentials were not saved.") from None


if __name__ == "__main__":
    main()

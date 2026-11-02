"""Small publication boundary check. Reports paths, never suspected secret values."""

from pathlib import Path
import re
import subprocess


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    paths = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=root
    ).decode().split("\0")
    problems = []
    secret = re.compile(rb"(?:sk-ant-[A-Za-z0-9_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,})")
    for value in filter(None, paths):
        path = Path(value)
        if (
            path.parts[0] in {"runtime", "artifacts", "data", "private", ".venv"}
            or (path.name.startswith(".env") and path.name != ".env.example")
            or path.suffix in {".sqlite", ".db"}
        ):
            problems.append(f"Private/runtime path tracked: {value}")
        target = root / path
        if target.is_file() and secret.search(target.read_bytes()):
            problems.append(f"Potential credential in tracked file: {value}")
    if problems:
        print("\n".join(problems))
        return 1
    print("Tracked files pass the private-data and obvious-credential boundary check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

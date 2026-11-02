#!/usr/bin/env python3
"""Inspect/install/remove only this project's user LaunchAgent, without sudo."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys

LABEL = "com.ronoktanvir.quanto"


def configuration(root: Path, python: Path, port: int) -> dict:
    return {
        "Label": LABEL,
        "ProgramArguments": [str(python), "-m", "quanto.operations", "--root", str(root),
                             "--port", str(port)],
        "WorkingDirectory": str(root),
        "EnvironmentVariables": {"PYTHONPATH": str(root / "src")},
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 30,
        "Umask": 0o077,
        "StandardOutPath": str(root / "runtime" / "service.stdout.log"),
        "StandardErrorPath": str(root / "runtime" / "service.stderr.log"),
    }


def verify_owned(path: Path, root: Path) -> bool:
    if not path.exists():
        return False
    if path.is_symlink():
        raise ValueError("Refusing a symlink LaunchAgent")
    with path.open("rb") as source:
        current = plistlib.load(source)
    args = current.get("ProgramArguments", [])
    if (current.get("Label") != LABEL or current.get("WorkingDirectory") != str(root)
            or not isinstance(args, list) or len(args) != 7
            or args[1:6] != ["-m", "quanto.operations", "--root", str(root), "--port"]):
        raise ValueError("Existing LaunchAgent is not this project's owned service")
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parents[1])
    parser.add_argument("--python", type=Path, help="Absolute Python interpreter; defaults to .venv/bin/python")
    parser.add_argument("--port", type=int, default=8766)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--install", action="store_true", help="Install and bootstrap the owned user service")
    actions.add_argument("--uninstall", action="store_true", help="Remove only this project's owned service")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    # Preserve the venv executable path: resolving its symlink would discard the venv.
    python = Path(os.path.abspath(args.python or root / ".venv" / "bin" / "python"))
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    directory = Path.home() / "Library" / "LaunchAgents"
    path = directory / f"{LABEL}.plist"
    domain = f"gui/{os.getuid()}"
    config = configuration(root, python, args.port)
    action = "uninstall" if args.uninstall else "install" if args.install else "dry_run"
    try:
        owned = verify_owned(path, root)
        if not args.install and not args.uninstall:
            print(json.dumps({"action": action, "plist": str(path), "already_owned": owned,
                              "configuration": config}, indent=2))
            return 0
        if sys.platform != "darwin":
            raise ValueError("LaunchAgent installation requires macOS")
        if args.uninstall:
            if owned:
                subprocess.run(["launchctl", "bootout", domain, str(path)], check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                path.unlink()
            print(json.dumps({"action": "uninstalled" if owned else "already_absent",
                              "label": LABEL}))
            return 0
        if not python.is_file() or not os.access(python, os.X_OK):
            raise ValueError("Configured Python interpreter is not executable")
        if not (root / "src" / "quanto" / "operations.py").is_file():
            raise ValueError("Project supervisor source is missing")
        runtime = root / "runtime"
        if runtime.is_symlink() or directory.is_symlink():
            raise ValueError("Service directories must not be symlinks")
        runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if owned:
            subprocess.run(["launchctl", "bootout", domain, str(path)], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        temporary = path.with_suffix(".plist.tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC |
                             getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(descriptor, "wb") as output:
            plistlib.dump(config, output)
        temporary.replace(path)
        subprocess.run(["launchctl", "bootstrap", domain, str(path)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(json.dumps({"action": "installed", "label": LABEL, "plist": str(path)}))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError, plistlib.InvalidFileException) as exc:
        print(f"Quanto local service unavailable: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

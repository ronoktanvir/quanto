"""Restore only the four reviewed manual-cycle source files on the owner's Mac."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[1]
REVIEWED_ROOT = Path("/Users/ronoktanvir/Documents/ChatGPT/quanto")
STAGE_NAME = "development-cycle-launch-v2-preparation"
PINS = {
    "paid_worker.py": "9a59cb3eb37f8b6f06d17abde2a474da13fba07264bd37c634ee12a07f0cd01c",
    "supervise.py": "43f992b081fe7bd5f23d6163dafd5827d265630a6b3049ecf58857eaa802d830",
    "test_paid_worker.py": "7694ff9ada310d5c27c84cca5907464099475c5cbbc1c09b4b6180a723669c1a",
    "test_supervise.py": "af7f64b4e2ea6461f93fc3b9cadcf8c88523276b663fce50c58450430f4baa48",
}
JOINT_FREEZE_SHA256 = "a57edc801c50e1657536d76d15a41075faefe914ce9539ae64d76a1a3c2fb5c9"


def stage():
    if ROOT != REVIEWED_ROOT:
        raise ValueError("This freeze is specific to the reviewed workspace path")
    # Reconstruct the approved source declaration without relying on a private run or its logs.
    freeze = {
        "actual_invoked": False,
        "fixture_log_sha256": "2518e023df64af2096b51f2e02eb3a4a072f2efc9756b6b6ae314d12637cf6f2",
        "fixture_tests": 91,
        "report_sha256": "482eadba1c217a159374818ef7a08857fe2d2929c885c6c61d56c2b7d594ed29",
        "sources": PINS,
    }
    encoded = (json.dumps(freeze, indent=2, sort_keys=True) + "\n").encode()
    if hashlib.sha256(encoded).hexdigest() != JOINT_FREEZE_SHA256:
        raise ValueError("Manual-cycle source declaration disagrees with the accepted joint freeze")
    # Isolated Python omits the script directory from its import path.
    staging = runpy.run_path(str(Path(__file__).with_name("stage_registration_tools.py")))
    source = ROOT / "operations/manual_cycle"
    files = {name: staging["checked_read"](source / name, pin) for name, pin in PINS.items()}
    runtime = ROOT / "runtime"
    return staging["install_reviewed_files"](runtime, runtime / STAGE_NAME, files, PINS)


if __name__ == "__main__":
    installed = stage()
    print(f"Verified four reviewed manual-cycle source files. Installed {installed} missing files.")

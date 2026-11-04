"""Rebuild and stage the code-only research audit manifest on its reviewed host."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import types


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "operations/manual_audit"
STAGE = ROOT / "runtime/development-cycle-audit-v2-preparation"
MANIFEST_NAME = "source-manifest-110a44f9139a41ba8510cd5f0defe18b.json"
MANIFEST_SHA = "e78ae5ee34746c7a572171006e5aaa012ba905e4b1fca44bf16ae7be3550616d"
REFERENCE_SHA = "ecb929c0a71bd5b452003d85fd8ef2a5b71c5646e3e77d6582cc11f353e042c1"
TOOLS = {
    "audit_boundary.py": "96a3f8632666fb5229eea0c891dbdb72367fb601f45aae4c60aed34b9419418c",
    "audit_cycle.py": "95f3c8aa9adf51ce04854eaa3f77472a9c400ba73fed3267c159e63e5467550f",
    "context_checks.py": "e05dfa963cd5f880f3dea80f5a241c22aee43e1859afc8ed6bf407e446d497b4",
    "cycle_evidence.py": "0fbb3d4e76d50b59fdf0b4f7240d77feb978a086bcdc4b35dff9c4c8eef287e6",
    "independent_oracle.py": "54887dfae2f12430b5cdd9901c0c3ba367541f6eb4714b987ad68e08f0433ca1",
    "trace_checks.py": "42adf830b9bdd4974d60c4486e85ec0100d6421be0f306498acb1b5e6e004423",
}
LAUNCH = {
    "supervise.py": "43f992b081fe7bd5f23d6163dafd5827d265630a6b3049ecf58857eaa802d830",
    "paid_worker.py": "9a59cb3eb37f8b6f06d17abde2a474da13fba07264bd37c634ee12a07f0cd01c",
}


def rebuild(checked_read):
    files = {name: checked_read(SOURCE / name, pin) for name, pin in TOOLS.items()}
    def load_source(name, filename):
        path = SOURCE / filename
        module = types.ModuleType(name)
        module.__file__ = str(path)
        sys.modules[name] = module
        exec(compile(files[filename], str(path), "exec", dont_inherit=True), module.__dict__)
        return module

    boundary = load_source("fresh_cycle_boundary", "audit_boundary.py")
    boundary.environment_check()
    if ROOT != boundary.ACTUAL_ROOT:
        raise ValueError("The accepted manifest requires the reviewed workspace")
    source_files = boundary.source_files(ROOT)
    product = boundary.load_product(ROOT, source_files)
    for name in ("trace_checks", "context_checks"):
        load_source("fresh_cycle_" + name, name + ".py")
    for name, pin in LAUNCH.items():
        checked_read(ROOT / "runtime/development-cycle-launch-v2-preparation" / name, pin)
    reference = SOURCE / "derive_worker_reference.py"
    checked_read(reference, REFERENCE_SHA)
    process = subprocess.run([sys.executable, "-I", "-S", "-B", str(reference)], env={},
                             stdin=subprocess.DEVNULL, capture_output=True, timeout=20, check=True)
    if process.stderr:
        raise ValueError("The worker identity reconstruction reported an unexpected diagnostic")
    manifest = boundary.canonical({
        "schema_version": 1, "kind": "d008_fresh_audit_source_freeze", "files": source_files,
        "compiled": product.loaded, "loaded": boundary.loaded_identity(),
        "stdlib": boundary.standard_library_identity(), "oracle_sha256": TOOLS["independent_oracle.py"],
        "launch_sources": LAUNCH, "tools": TOOLS, "worker_reference": json.loads(process.stdout),
    })
    if hashlib.sha256(manifest).hexdigest() != MANIFEST_SHA:
        raise ValueError("Current product, runtime or worker identity differs from the reviewed manifest")
    return {**files, MANIFEST_NAME: manifest}


def stage(*, verify_only):
    shared = runpy.run_path(str(Path(__file__).with_name("stage_registration_tools.py")))
    files = rebuild(shared["checked_read"])
    if verify_only:
        return 0
    return shared["install_reviewed_files"](ROOT / "runtime", STAGE, files, {**TOOLS, MANIFEST_NAME: MANIFEST_SHA})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify-only", action="store_true", help="rebuild in memory (the default)")
    mode.add_argument("--install", action="store_true", help="also restore missing files to the reviewed runtime")
    installed = stage(verify_only=not parser.parse_args().install)
    print(f"Verified six audit programs and their manifest. Installed {installed} missing files.")

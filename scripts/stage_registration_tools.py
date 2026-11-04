"""Rebuild the reviewed registration tools from versioned source on the pinned host."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import types
import uuid


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "operations/registration"
STAGE = ROOT / "runtime/development-cycle-registration-v2-preparation"
CONTROLLER = "prepare_current_code.py"
TESTS = "test_registration_preparation.py"
PINS = {CONTROLLER: "3f52a95452d9a20c6c456624f33a70c717d9f1fc28d83ae65f178e67e9d7047d",
        TESTS: "b717f8603b65570feb4b84c23e4301a1f26f54784a11ebd8ad4bac19423d1d79",
        "source-manifest.json": "aa65675f3c7886a2d950b75928811d4f7189adbc2342a383b983f0ea20ea70c4"}


def checked_read(path, digest):
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("The reviewed path must have no symlink components")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_nlink != 1 or info.st_mode & 0o022 or info.st_size > 2 * 1024 * 1024):
            raise ValueError("Unsafe source or staging file")
        data = stream.read(info.st_size + 1)
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"Reviewed identity mismatch for {path.name}")
    return data


def manifest_bytes(controller):
    module = types.ModuleType("accepted_registration_source")
    module.__file__ = str(SOURCE / CONTROLLER)
    exec(compile(controller, module.__file__, "exec", dont_inherit=True), module.__dict__)
    module.environment_check()
    if module.ACTUAL_ROOT != ROOT:
        raise ValueError("This historical manifest is specific to the reviewed workspace path")
    files = module.source_files(ROOT)
    loader = module.load_product(ROOT, files)
    manifest = {"version": 1, "files": files, "interpreter": module.runtime_identity(),
                "compiled": loader.loaded, "loaded": module.loaded_identity(),
                "stdlib": module.standard_library_identity()}
    data = module.canonical(manifest)
    if hashlib.sha256(data).hexdigest() != PINS["source-manifest.json"]:
        raise ValueError("The current code or Python runtime does not reproduce the reviewed manifest")
    return data


def stage():
    files = {name: checked_read(SOURCE / name, PINS[name]) for name in (CONTROLLER, TESTS)}
    files["source-manifest.json"] = manifest_bytes(files[CONTROLLER])
    runtime = ROOT / "runtime"
    if any(p.is_symlink() for p in (runtime, *runtime.parents)):
        raise ValueError("Unsafe runtime directory path")
    runtime.mkdir(mode=0o700, exist_ok=True)
    info = runtime.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
        raise ValueError("The runtime directory must belong to the operator and disallow shared writes")
    STAGE.mkdir(mode=0o700, exist_ok=True)
    info = STAGE.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError("The staging directory must belong to the operator and have mode 0700")
    # Check all existing targets before installing any missing one.
    for name in files:
        if os.path.lexists(STAGE / name):
            checked_read(STAGE / name, PINS[name])
    directory_fd = os.open(STAGE, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    installed = 0
    try:
        for name, data in files.items():
            if os.path.lexists(STAGE / name):
                checked_read(STAGE / name, PINS[name])
                continue
            temporary = ".stage-" + uuid.uuid4().hex
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory_fd)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.link(temporary, name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd,
                        follow_symlinks=False)
                installed += 1
            finally:
                os.unlink(temporary, dir_fd=directory_fd)
            os.fsync(directory_fd)
            checked_read(STAGE / name, PINS[name])
    finally:
        os.close(directory_fd)
    return installed


if __name__ == "__main__":
    installed = stage()
    print(f"Verified three reviewed files. Installed {installed} previously missing files.")

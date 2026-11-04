#!/usr/bin/env python3
"""One consumed, local registration preparation; never a paid research launcher.

Reviewed cooperating-process controls, not protection against a hostile owner.
The private packet and source manifest require a later independent review.
"""

from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.abc
import importlib.util
import json
import marshal
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import sysconfig
import time
import types

ACTUAL_ROOT = Path("/Users/ronoktanvir/Documents/ChatGPT/quanto")
PYTHON = Path("/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11")
PYTHON_SHA = "4e28e811a89aeac6eed668ae641c7f85f5831e42e8dc6cd9a85a3bcc032ec46a"
WORK_SECONDS = 600.0
CLEANUP_SECONDS = 5.0
MAX_FILE = 1024 * 1024
MAX_DB = 128 * 1024 * 1024
MODULES = (
    "ledger",
    "evaluation_registry",
    "provenance",
    "research",
    "event_engine",
    "alpaca_data",
    "alpaca_actions",
    "admission",
    "policy_revision",
    "study_suite",
    "explorer",
    "research_broker",
    "research_failure_context",
    "research_dispatch",
    "research_packets",
    "research_workflow",
    "provider",
)
DYNAMIC = {"audit", "intents", "intent_ends", "effects", "effect_ends"}
REASONS = frozenset(
    {
        "unsafe_path",
        "unsafe_file",
        "unsafe_environment",
        "invalid_packet",
        "source_mismatch",
        "loaded_mismatch",
        "authority_missing",
        "authority_changed",
        "sidecar_present",
        "store_changed",
        "request_mismatch",
        "lineage_mismatch",
        "already_consumed",
        "receipt_collision",
        "unexpected_io",
        "forbidden_call",
        "deadline",
        "interrupted",
        "child_failed",
        "invalid_result",
        "registration_refused",
        "publication_failed",
        "internal_failure",
        "fixture_boundary",
    }
)


class Refusal(Exception):
    def __init__(self, reason):
        self.reason = reason if reason in REASONS else "internal_failure"
        super().__init__(self.reason)


def need(value, reason):
    if not value:
        raise Refusal(reason)


def canonical(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def parse(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "invalid_packet")
            result[key] = value
        return result

    value = json.loads(
        raw,
        object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(Refusal("invalid_packet")),
    )
    canonical(value)
    return value


def digest(value):
    need(type(value) is str and re.fullmatch("[a-f0-9]{64}", value), "invalid_packet")
    return value


def pathcheck(path):
    need(path.is_absolute() and ".." not in path.parts, "unsafe_path")
    for part in (path, *path.parents):
        need(not part.is_symlink(), "unsafe_path")


def directory(path, *, private=False):
    pathcheck(path)
    info = path.lstat()
    need(
        stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o022,
        "unsafe_path",
    )
    need(not private or stat.S_IMODE(info.st_mode) == 0o700, "unsafe_path")
    return info


def physical(info):
    return dict(
        device=info.st_dev,
        inode=info.st_ino,
        uid=info.st_uid,
        mode=stat.S_IMODE(info.st_mode),
        nlink=info.st_nlink,
    )


def fileinfo(path, *, private=True):
    pathcheck(path)
    info = path.lstat()
    need(
        stat.S_ISREG(info.st_mode)
        and info.st_uid == os.getuid()
        and info.st_nlink == 1
        and not info.st_mode & 0o022,
        "unsafe_file",
    )
    need(not private or stat.S_IMODE(info.st_mode) == 0o600, "unsafe_file")
    return info


def readfile(path, *, private=True, limit=MAX_FILE):
    before = fileinfo(path, private=private)
    need(before.st_size <= limit, "unsafe_file")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        need(physical(os.fstat(fd)) == physical(before), "store_changed")
        raw = b""
        while len(raw) <= limit:
            part = os.read(fd, min(65536, limit + 1 - len(raw)))
            if not part:
                break
            raw += part
        after = os.fstat(fd)
        need(
            len(raw) == before.st_size == after.st_size
            and len(raw) <= limit
            and before.st_mtime_ns == after.st_mtime_ns
            and before.st_ctime_ns == after.st_ctime_ns
            and physical(after) == physical(fileinfo(path, private=private)),
            "store_changed",
        )
        return raw
    finally:
        os.close(fd)


def syncdir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def exclusive(path, value):
    directory(path.parent, private=True)
    raw = canonical(value)
    need(len(raw) <= MAX_FILE, "invalid_result")
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        raise Refusal("receipt_collision") from None
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)
    syncdir(path.parent)
    need(readfile(path) == raw, "publication_failed")
    return sha(raw)


def deadline_check(deadline):
    need(time.monotonic() < deadline, "deadline")


def runtime_identity():
    path = Path(sys.executable).resolve()
    pathcheck(path)
    info = path.lstat()
    need(
        stat.S_ISREG(info.st_mode)
        and info.st_uid in {0, os.getuid()}
        and not info.st_mode & 0o002
        and info.st_size <= 32 * MAX_FILE,
        "unsafe_environment",
    )
    return dict(
        executable=str(path),
        sha256=sha(path.read_bytes()),
        version=sys.version,
        implementation=sys.implementation.name,
        cache_tag=sys.implementation.cache_tag,
    )


def environment_check():
    need(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, "unsafe_environment")
    need(set(os.environ) <= {"LC_CTYPE", "__CF_USER_TEXT_ENCODING"}, "unsafe_environment")
    need(os.environ.get("LC_CTYPE", "C.UTF-8") in {"C.UTF-8", "UTF-8"}, "unsafe_environment")
    need(
        re.fullmatch(
            r"0x[0-9A-Fa-f]+:0x[0-9A-Fa-f]+:0x[0-9A-Fa-f]+",
            os.environ.get("__CF_USER_TEXT_ENCODING", "0x0:0x0:0x0"),
        ),
        "unsafe_environment",
    )
    need(
        Path(sys.executable).resolve() == PYTHON
        and sys.version_info[:3] == (3, 11, 9)
        and runtime_identity()["sha256"] == PYTHON_SHA,
        "unsafe_environment",
    )


def standard_library_identity():
    names = (
        "sqlite3",
        "_sqlite3",
        "json",
        "hashlib",
        "decimal",
        "_decimal",
        "fractions",
        "urllib.request",
        "urllib.parse",
        "zoneinfo",
        "_zoneinfo",
        "pathlib",
        "os",
        "stat",
        "datetime",
        "_datetime",
        "threading",
        "uuid",
        "types",
        "marshal",
        "contextlib",
        "importlib.util",
        "importlib.abc",
        "dataclasses",
    )
    base, found = Path(sysconfig.get_path("stdlib")).resolve(), {}
    for name in names:
        module = importlib.import_module(name)
        origin = module.__spec__.origin
        if origin in {"built-in", "frozen"}:
            found[name] = {"origin": origin}
        else:
            path = Path(origin).resolve()
            need(base in path.parents and path.stat().st_size <= 32 * MAX_FILE, "loaded_mismatch")
            found[name] = {"origin": str(path), "sha256": sha(path.read_bytes())}
    return found


def source_files(source):
    directory(source)
    files = {
        str(p.relative_to(source)): sha(readfile(p, private=False))
        for p in sorted((source / "src/quanto").glob("*.py"))
    }
    for name in ("uv.lock", "pyproject.toml"):
        files[name] = sha(readfile(source / name, private=False))
    return files


class FrozenImports(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Compile checked source bytes, never a pyc or an installed alternate copy."""

    def __init__(self, source, files):
        self.source, self.files = source, files
        self.loaded = {}

    def find_spec(self, fullname, path=None, target=None):
        if fullname == "quanto" or fullname.startswith("quanto."):
            relative = (
                "src/quanto/__init__.py"
                if fullname == "quanto"
                else "src/" + fullname.replace(".", "/") + ".py"
            )
            need(relative in self.files, "source_mismatch")
            return importlib.util.spec_from_file_location(
                fullname,
                self.source / relative,
                loader=self,
                submodule_search_locations=[] if fullname == "quanto" else None,
            )

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        path = Path(module.__spec__.origin)
        raw = readfile(path, private=False)
        need(sha(raw) == self.files[str(path.relative_to(self.source))], "source_mismatch")
        code = compile(raw, str(path), "exec", dont_inherit=True, optimize=0)
        self.loaded[module.__name__] = sha(marshal.dumps(code, 2))
        exec(code, module.__dict__)


def loaded_identity():
    result = {}

    def function(fn):
        def normalize(code):
            return code.replace(
                co_filename="<reviewed>",
                co_consts=tuple(
                    normalize(x) if isinstance(x, types.CodeType) else x for x in code.co_consts
                ),
            )

        record = {"code": sha(marshal.dumps(normalize(fn.__code__), 2))}
        if isinstance(getattr(fn, "__wrapped__", None), types.FunctionType):
            record["wrapped"] = function(fn.__wrapped__)
        return record

    def value_identity(value):
        if value is None or type(value) in (str, bool, int, float):
            return value
        if isinstance(value, bytes):
            return {"bytes_sha256": sha(value)}
        if isinstance(value, re.Pattern):
            return {"pattern": value_identity(value.pattern), "flags": value.flags}
        if isinstance(value, (list, tuple, set, frozenset)):
            items = [value_identity(x) for x in value]
            if isinstance(value, (set, frozenset)):
                items.sort(key=canonical)
            return {"type": type(value).__name__, "items": items}
        if isinstance(value, dict) and all(type(x) is str for x in value):
            return {k: value_identity(v) for k, v in value.items()}
        if isinstance(value, types.ModuleType):
            return {"module": value.__name__}
        if isinstance(value, (ExistingOS, ExistingSQLite)):
            return {"module": value.original.__name__}
        if isinstance(value, types.FunctionType):
            return {"function": function(value)}
        if isinstance(value, type):
            return {"class": value.__module__ + "." + value.__qualname__}
        return {"binding_type": type(value).__module__ + "." + type(value).__qualname__}

    for name, module in sorted(sys.modules.items()):
        if name == "quanto" or name.startswith("quanto."):
            members = {}
            for key, value in vars(module).items():
                if isinstance(value, types.FunctionType) and value.__module__ == name:
                    members[key] = function(value)
                elif isinstance(value, type) and value.__module__ == name:
                    for label, method in vars(value).items():
                        if isinstance(method, (staticmethod, classmethod)):
                            method = method.__func__
                        if isinstance(method, property):
                            method = method.fget
                        if isinstance(method, types.FunctionType):
                            members[key + "." + label] = function(method)
            result[name] = {
                "file": str(Path(module.__file__).absolute()),
                "functions": members,
                "globals": {
                    key: value_identity(value)
                    for key, value in vars(module).items()
                    if not key.startswith("__")
                },
            }
    explorer = sys.modules["quanto.explorer"]
    return {"modules": result, "financial_identity": explorer._code_identity()}


def load_product(source, files):
    need(not any(x == "quanto" or x.startswith("quanto.") for x in sys.modules), "loaded_mismatch")
    need(source_files(source) == files, "source_mismatch")
    loader = FrozenImports(source, files)
    sys.meta_path.insert(0, loader)
    for name in MODULES:
        importlib.import_module("quanto." + name)
    return loader


def no_sidecars(path):
    need(
        all(not os.path.lexists(str(path) + suffix) for suffix in ("-journal", "-wal", "-shm")),
        "sidecar_present",
    )


def db_state(path, deadline):
    no_sidecars(path)
    before = physical(fileinfo(path))
    need(fileinfo(path).st_size <= MAX_DB, "unsafe_file")
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=1)) as db:
        db.execute("PRAGMA query_only=ON")
        db.execute("PRAGMA trusted_schema=OFF")
        db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
        schema = db.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
        ).fetchall()
        tables = {}
        for (name,) in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ):
            need(re.fullmatch("[a-z_]+", name), "authority_changed")
            rows = db.execute('SELECT * FROM "' + name + '" ORDER BY rowid LIMIT 50001').fetchall()
            need(len(rows) <= 50000 and len(canonical(rows)) <= 32 * MAX_FILE, "authority_changed")
            tables[name] = rows
    need(physical(fileinfo(path)) == before, "authority_changed")
    no_sidecars(path)
    deadline_check(deadline)
    return {"physical": before, "schema_sha256": sha(canonical(schema)), "tables": tables}


def project_state(root, deadline):
    directory(root)
    directory(root / "runtime")
    directory(root / "runtime/access-control", private=True)
    directory(root / "data")
    directory(root / "data/objects", private=True)
    control = root / "runtime/access-control/control.sqlite"
    research = root / "runtime/research.sqlite"
    need(control.exists() and research.exists(), "authority_missing")
    no_sidecars(control)
    no_sidecars(research)
    state = db_state(control, deadline)
    tables = state.pop("tables")
    state["tables"] = {
        name: {"count": len(rows), "sha256": sha(canonical(rows))} for name, rows in tables.items()
    }
    config = dict(tables["configuration"])
    info = root.lstat()
    need(
        config["root"] == str(root)
        and config["device"] == str(info.st_dev)
        and config["inode"] == str(info.st_ino)
        and config["synthetic"] in {"False", "True"}
        and config["schema"] == "2"
        and config["legacy_unknown"] in {"True", "False"},
        "authority_changed",
    )
    need(
        tables["reservations"] == [] and tables["principal_revocations"] == [], "authority_changed"
    )
    # Directory link counts can change when content-addressed files are added.
    # Pin ownership/mode/device/inode; regular database links remain pinned above.
    root_identity = {k: v for k, v in physical(info).items() if k != "nlink"}
    object_identity = {
        k: v for k, v in physical((root / "data/objects").lstat()).items() if k != "nlink"
    }
    return {
        "root": root_identity,
        "objects": object_identity,
        "control": state,
        "research": {
            "physical": physical(fileinfo(research)),
            "sha256": sha(readfile(research, limit=MAX_DB)),
        },
    }


def preserve_authority(root, before, deadline):
    current = project_state(root, deadline)
    need(
        current["root"] == before["root"]
        and current["objects"] == before["objects"]
        and current["research"]["physical"] == before["research"]["physical"],
        "store_changed",
    )
    old, new = before["control"], current["control"]
    need(
        new["physical"] == old["physical"]
        and new["schema_sha256"] == old["schema_sha256"]
        and set(new["tables"]) == set(old["tables"]),
        "authority_changed",
    )
    full = db_state(root / "runtime/access-control/control.sqlite", deadline)["tables"]
    for name, previous in old["tables"].items():
        rows = full[name]
        need(
            len(rows) >= previous["count"]
            and sha(canonical(rows[: previous["count"]])) == previous["sha256"],
            "authority_changed",
        )
        if name not in DYNAMIC:
            need(new["tables"][name] == previous, "authority_changed")
    return current


class ExistingOS:
    def __init__(self, original, path, expected, basename=False):
        self.original, self.target, self.expected, self.basename = (
            original,
            path,
            expected,
            basename,
        )

    def __getattr__(self, name):
        return getattr(self.original, name)

    def open(self, path, flags, mode=0o777, *, dir_fd=None):
        target = Path(path)
        applies = target == self.target or (self.basename and target == Path(self.target.name))
        if applies and flags & os.O_CREAT:
            need(
                flags == os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW and mode == 0o600,
                "unexpected_io",
            )
            if dir_fd is not None:
                need(
                    physical(os.fstat(dir_fd)) == physical(self.target.parent.lstat()),
                    "store_changed",
                )
            need(physical(fileinfo(self.target)) == self.expected, "authority_changed")
            raise FileExistsError()  # No creation syscall, even if subsequently deleted.
        return self.original.open(path, flags, mode, dir_fd=dir_fd)


class ExistingSQLite:
    def __init__(self, original, path, expected):
        self.original, self.path, self.expected = original, path, expected

    def __getattr__(self, name):
        return getattr(self.original, name)

    def connect(self, database, *args, **kwargs):
        target = str(database)
        need(target in {str(self.path), self.path.as_uri() + "?mode=ro"}, "unexpected_io")
        need(physical(fileinfo(self.path)) == self.expected, "authority_changed")
        if target == str(self.path):
            database, kwargs = self.path.as_uri() + "?mode=rw", {**kwargs, "uri": True}
        db = self.original.connect(database, *args, **kwargs)
        try:
            need(physical(fileinfo(self.path)) == self.expected, "authority_changed")
        except BaseException:
            db.close()
            raise
        return db


class Boundary:
    """Block network, child processes, credentials and portfolio entrypoints."""

    def __init__(self, source, root, attempt, request_files):
        self.source, self.root, self.attempt = source, root, attempt
        self.stdlib = Path(sysconfig.get_path("stdlib")).resolve()
        self.allowed = (
            set(request_files)
            | set(Path(__file__).parent.glob("*.py"))
            | {Path(__file__).with_name("source-manifest.json"), PYTHON}
        )
        self.oracle = Path(__file__).with_name("independent_oracle.py")
        self.db = {root / "runtime/research.sqlite", root / "runtime/access-control/control.sqlite"}
        self.denied = []

    def __call__(self, event, args):
        if event == "subprocess.Popen":
            executable, argv, cwd, env = args
            need(
                executable == str(PYTHON)
                and len(argv) == 7
                and argv[:5] == [str(PYTHON), "-I", "-S", "-B", str(self.oracle)]
                and argv[5] == "--input"
                and Path(argv[6]).parent == self.attempt
                and Path(argv[6]).name
                in {"oracle-input-0.json", "oracle-input-10.json", "oracle-input-25.json"}
                and cwd == str(self.attempt)
                and env == {},
                "unexpected_io",
            )
            return
        if event.startswith(("socket.", "subprocess.", "os.exec", "os.spawn", "os.fork")):
            self.denied.append("network_or_process")
            raise Refusal("unexpected_io")
        if event == "sqlite3.connect":
            need(
                str(args[0])
                in {p.as_uri() + mode for p in self.db for mode in ("?mode=ro", "?mode=rw")},
                "unexpected_io",
            )
        if event == "open":
            name, mode, flags = args
            if isinstance(name, int):
                return
            path = Path(os.fsdecode(name))
            if path == Path("/dev/null"):
                need(flags & ~os.O_CLOEXEC == os.O_RDWR, "unexpected_io")
                return
            if not path.is_absolute():
                if re.fullmatch(r"\.pending-[a-f0-9]{32}", str(path)):
                    need(
                        flags & ~os.O_CLOEXEC
                        == os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        "unexpected_io",
                    )
                    return
                if flags & os.O_DIRECTORY and str(path) in {"runtime", "data", "objects"}:
                    return
                # Provenance's descriptor-relative operations are independently
                # guarded by the exact loaded source and directory descriptor.
                need(
                    str(path) == "research.sqlite" or re.fullmatch(r"[a-f0-9]{64}\.bin", str(path)),
                    "unexpected_io",
                )
                return
            writable = bool(
                flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            )
            dbfile = any(
                str(path) in {str(p) + s for s in ("", "-journal", "-wal", "-shm")} for p in self.db
            )
            local = path == self.attempt or path.parent == self.attempt or path in self.db or dbfile
            objects = (
                path == self.root / "data/objects" or path.parent == self.root / "data/objects"
            )
            directories = path in {
                self.root,
                self.root / "runtime",
                self.root / "data",
                self.root / "runtime/access-control",
            }
            code = self.source / "src/quanto" in path.parents or path in {
                self.source / "uv.lock",
                self.source / "pyproject.toml",
            }
            system = (
                self.stdlib == path
                or self.stdlib in path.parents
                or str(path).startswith("/usr/share/zoneinfo/")
            )
            need(
                local
                or objects
                or (not writable and (directories or code or system or path in self.allowed)),
                "unexpected_io",
            )
        if event == "os.remove":
            name, fd = args
            need(
                re.fullmatch(r"\.pending-[a-f0-9]{32}", os.fsdecode(name))
                and fd is not None
                and fd >= 0
                and physical(os.fstat(fd)) == physical((self.root / "data/objects").lstat()),
                "unexpected_io",
            )
        if event == "os.link":
            source, target, source_fd, target_fd = args
            need(
                re.fullmatch(r"\.pending-[a-f0-9]{32}", os.fsdecode(source))
                and re.fullmatch(r"[a-f0-9]{64}\.bin", os.fsdecode(target))
                and source_fd >= 0
                and target_fd >= 0
                and physical(os.fstat(source_fd))
                == physical(os.fstat(target_fd))
                == physical((self.root / "data/objects").lstat()),
                "unexpected_io",
            )
        if event in {"os.rename", "os.symlink", "os.rmdir"}:
            raise Refusal("unexpected_io")
        if event == "os.mkdir":
            path = Path(os.fsdecode(args[0]))
            need(
                path
                in {
                    self.root / "runtime",
                    self.root / "runtime/access-control",
                    self.root / "data",
                    self.root / "data/objects",
                }
                or str(path) in {"runtime", "data", "objects"},
                "unexpected_io",
            )

#!/usr/bin/env python3
"""One consumed, local registration preparation; never a paid research launcher.

Reviewed cooperating-process controls, not protection against a hostile owner.
The private packet and source manifest require a later independent review.
"""
from __future__ import annotations

import argparse
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
import signal
import sqlite3
import stat
import subprocess
import sys
import sysconfig
import time
import types

ACTUAL_ROOT = Path('/Users/ronoktanvir/Documents/ChatGPT/quanto')
PYTHON = Path('/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11')
PYTHON_SHA = '4e28e811a89aeac6eed668ae641c7f85f5831e42e8dc6cd9a85a3bcc032ec46a'
WORK_SECONDS = 600.0
CLEANUP_SECONDS = 5.0
MAX_FILE = 1024 * 1024
MAX_DB = 128 * 1024 * 1024
PHASES = ('revision', 'admission', 'suite')
KINDS = dict(revision='policy_revision', admission='historical_admission',
             suite='study_suite_registration')
REFS = dict(revision='policy_revision_sha256', admission='admission_sha256', suite='suite_sha256')
MODULES = ('ledger', 'evaluation_registry', 'provenance', 'research', 'event_engine',
           'alpaca_data', 'alpaca_actions', 'admission', 'policy_revision', 'study_suite', 'explorer')
DYNAMIC = {'audit', 'intents', 'intent_ends', 'effects', 'effect_ends'}
REASONS = frozenset({'unsafe_path', 'unsafe_file', 'unsafe_environment', 'invalid_packet',
    'source_mismatch', 'loaded_mismatch', 'authority_missing', 'authority_changed',
    'sidecar_present', 'store_changed', 'request_mismatch', 'lineage_mismatch',
    'already_consumed', 'receipt_collision', 'unexpected_io', 'forbidden_call',
    'deadline', 'interrupted', 'child_failed', 'invalid_result', 'registration_refused',
    'publication_failed', 'internal_failure', 'fixture_boundary', 'cleanup_unobserved'})
LIMITS = dict(protected_eligible=False, protected_acquisition_enabled=False,
              legacy_reconciled=False, portfolio_backtest=False, paid_request=False,
              external_restore=False, unattended_ready=False, investment_validation=False)


class Refusal(Exception):
    def __init__(self, reason):
        self.reason = reason if reason in REASONS else 'internal_failure'
        super().__init__(self.reason)


def need(value, reason):
    if not value:
        raise Refusal(reason)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def parse(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'invalid_packet')
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(Refusal('invalid_packet')))
    canonical(value)
    return value


def digest(value):
    need(type(value) is str and re.fullmatch('[a-f0-9]{64}', value), 'invalid_packet')
    return value


def pathcheck(path):
    need(path.is_absolute() and '..' not in path.parts, 'unsafe_path')
    for part in (path, *path.parents):
        need(not part.is_symlink(), 'unsafe_path')


def directory(path, *, private=False):
    pathcheck(path)
    info = path.lstat()
    need(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
         and not info.st_mode & 0o022, 'unsafe_path')
    need(not private or stat.S_IMODE(info.st_mode) == 0o700, 'unsafe_path')
    return info


def physical(info):
    return dict(device=info.st_dev, inode=info.st_ino, uid=info.st_uid,
                mode=stat.S_IMODE(info.st_mode), nlink=info.st_nlink)


def fileinfo(path, *, private=True):
    pathcheck(path)
    info = path.lstat()
    need(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1
         and not info.st_mode & 0o022, 'unsafe_file')
    need(not private or stat.S_IMODE(info.st_mode) == 0o600, 'unsafe_file')
    return info


def readfile(path, *, private=True, limit=MAX_FILE):
    before = fileinfo(path, private=private)
    need(before.st_size <= limit, 'unsafe_file')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        need(physical(os.fstat(fd)) == physical(before), 'store_changed')
        raw = b''
        while len(raw) <= limit:
            part = os.read(fd, min(65536, limit + 1 - len(raw)))
            if not part:
                break
            raw += part
        after = os.fstat(fd)
        need(len(raw) == before.st_size == after.st_size and len(raw) <= limit
             and before.st_mtime_ns == after.st_mtime_ns
             and before.st_ctime_ns == after.st_ctime_ns
             and physical(after) == physical(fileinfo(path, private=private)), 'store_changed')
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
    need(len(raw) <= MAX_FILE, 'invalid_result')
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        raise Refusal('receipt_collision') from None
    try:
        with os.fdopen(fd, 'wb', closefd=False) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)
    syncdir(path.parent)
    need(readfile(path) == raw, 'publication_failed')
    return sha(raw)


def deadline_check(deadline):
    need(time.monotonic() < deadline, 'deadline')


def runtime_identity():
    path = Path(sys.executable).resolve()
    pathcheck(path)
    info = path.lstat()
    need(stat.S_ISREG(info.st_mode) and info.st_uid in {0, os.getuid()}
         and not info.st_mode & 0o002 and info.st_size <= 32 * MAX_FILE, 'unsafe_environment')
    return dict(executable=str(path), sha256=sha(path.read_bytes()),
                version=sys.version, implementation=sys.implementation.name,
                cache_tag=sys.implementation.cache_tag)


def environment_check():
    need(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, 'unsafe_environment')
    need(set(os.environ) <= {'LC_CTYPE', '__CF_USER_TEXT_ENCODING'}, 'unsafe_environment')
    need(os.environ.get('LC_CTYPE', 'C.UTF-8') in {'C.UTF-8', 'UTF-8'}, 'unsafe_environment')
    need(re.fullmatch(r'0x[0-9A-Fa-f]+:0x[0-9A-Fa-f]+:0x[0-9A-Fa-f]+',
                     os.environ.get('__CF_USER_TEXT_ENCODING', '0x0:0x0:0x0')),
         'unsafe_environment')
    need(Path(sys.executable).resolve() == PYTHON and sys.version_info[:3] == (3, 11, 9)
         and runtime_identity()['sha256'] == PYTHON_SHA, 'unsafe_environment')


def standard_library_identity():
    names = ('sqlite3', '_sqlite3', 'json', 'hashlib', 'decimal', '_decimal', 'fractions',
             'urllib.request', 'urllib.parse', 'zoneinfo', '_zoneinfo', 'pathlib', 'os',
             'stat', 'datetime', '_datetime', 'threading', 'uuid', 'types', 'marshal',
             'contextlib', 'importlib.util', 'importlib.abc', 'dataclasses')
    base, found = Path(sysconfig.get_path('stdlib')).resolve(), {}
    for name in names:
        module = importlib.import_module(name)
        origin = module.__spec__.origin
        if origin in {'built-in', 'frozen'}:
            found[name] = {'origin': origin}
        else:
            path = Path(origin).resolve()
            need(base in path.parents and path.stat().st_size <= 32 * MAX_FILE, 'loaded_mismatch')
            found[name] = {'origin': str(path), 'sha256': sha(path.read_bytes())}
    return found


def source_files(source):
    directory(source)
    files = {str(p.relative_to(source)): sha(readfile(p, private=False))
             for p in sorted((source / 'src/quanto').glob('*.py'))}
    for name in ('uv.lock', 'pyproject.toml'):
        files[name] = sha(readfile(source / name, private=False))
    return files


class FrozenImports(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Compile checked source bytes, never a pyc or an installed alternate copy."""
    def __init__(self, source, files):
        self.source, self.files = source, files
        self.loaded = {}

    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'quanto' or fullname.startswith('quanto.'):
            relative = ('src/quanto/__init__.py' if fullname == 'quanto'
                        else 'src/' + fullname.replace('.', '/') + '.py')
            need(relative in self.files, 'source_mismatch')
            return importlib.util.spec_from_file_location(fullname, self.source / relative,
                    loader=self, submodule_search_locations=[] if fullname == 'quanto' else None)

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        path = Path(module.__spec__.origin)
        raw = readfile(path, private=False)
        need(sha(raw) == self.files[str(path.relative_to(self.source))], 'source_mismatch')
        code = compile(raw, str(path), 'exec', dont_inherit=True, optimize=0)
        self.loaded[module.__name__] = sha(marshal.dumps(code, 2))
        exec(code, module.__dict__)


def loaded_identity():
    result = {}
    def function(fn):
        def normalize(code):
            return code.replace(co_filename='<reviewed>', co_consts=tuple(
                normalize(x) if isinstance(x, types.CodeType) else x for x in code.co_consts))
        record = {'code': sha(marshal.dumps(normalize(fn.__code__), 2)),
                  'defaults': value_identity(fn.__defaults__),
                  'keyword_defaults': value_identity(fn.__kwdefaults__)}
        if isinstance(getattr(fn, '__wrapped__', None), types.FunctionType):
            record['wrapped'] = function(fn.__wrapped__)
        return record
    def value_identity(value):
        if value is None or type(value) in (str, bool, int, float):
            return value
        if isinstance(value, bytes):
            return {'bytes_sha256': sha(value)}
        if isinstance(value, re.Pattern):
            return {'pattern': value_identity(value.pattern), 'flags': value.flags}
        if isinstance(value, (list, tuple, set, frozenset)):
            items = [value_identity(x) for x in value]
            if isinstance(value, (set, frozenset)):
                items.sort(key=canonical)
            return {'type': type(value).__name__, 'items': items}
        if isinstance(value, dict) and all(type(x) is str for x in value):
            return {k: value_identity(v) for k, v in value.items()}
        if isinstance(value, types.ModuleType):
            return {'module': value.__name__}
        if isinstance(value, (ExistingOS, ExistingSQLite)):
            return {'module': value.original.__name__}
        if isinstance(value, types.FunctionType):
            return {'function': function(value)}
        if isinstance(value, type):
            return {'class': value.__module__ + '.' + value.__qualname__}
        return {'binding_type': type(value).__module__ + '.' + type(value).__qualname__}
    for name, module in sorted(sys.modules.items()):
        if name == 'quanto' or name.startswith('quanto.'):
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
                            members[key + '.' + label] = function(method)
            result[name] = {'file': str(Path(module.__file__).absolute()), 'functions': members,
                            'globals': {key: value_identity(value) for key, value in vars(module).items()
                                        if not key.startswith('__')}}
    explorer = sys.modules['quanto.explorer']
    return {'modules': result, 'financial_identity': explorer._code_identity()}


def load_product(source, files):
    need(not any(x == 'quanto' or x.startswith('quanto.') for x in sys.modules), 'loaded_mismatch')
    need(source_files(source) == files, 'source_mismatch')
    loader = FrozenImports(source, files)
    sys.meta_path.insert(0, loader)
    for name in MODULES:
        importlib.import_module('quanto.' + name)
    return loader


def no_sidecars(path):
    need(all(not os.path.lexists(str(path) + suffix) for suffix in ('-journal', '-wal', '-shm')),
         'sidecar_present')


def db_state(path, deadline):
    no_sidecars(path)
    before = physical(fileinfo(path))
    need(fileinfo(path).st_size <= MAX_DB, 'unsafe_file')
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=1)) as db:
        db.execute('PRAGMA query_only=ON')
        db.execute('PRAGMA trusted_schema=OFF')
        db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
        schema = db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall()
        tables = {}
        for name, in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            need(re.fullmatch('[a-z_]+', name), 'authority_changed')
            rows = db.execute('SELECT * FROM "' + name + '" ORDER BY rowid LIMIT 50001').fetchall()
            need(len(rows) <= 50000 and len(canonical(rows)) <= 32 * MAX_FILE, 'authority_changed')
            tables[name] = rows
    need(physical(fileinfo(path)) == before, 'authority_changed')
    no_sidecars(path)
    deadline_check(deadline)
    return {'physical': before, 'schema_sha256': sha(canonical(schema)), 'tables': tables}


def project_state(root, deadline):
    directory(root)
    directory(root / 'runtime')
    directory(root / 'runtime/access-control', private=True)
    directory(root / 'data')
    directory(root / 'data/objects', private=True)
    control = root / 'runtime/access-control/control.sqlite'
    research = root / 'runtime/research.sqlite'
    need(control.exists() and research.exists(), 'authority_missing')
    no_sidecars(control)
    no_sidecars(research)
    state = db_state(control, deadline)
    tables = state.pop('tables')
    state['tables'] = {name: {'count': len(rows), 'sha256': sha(canonical(rows))}
                       for name, rows in tables.items()}
    config = dict(tables['configuration'])
    info = root.lstat()
    need(config['root'] == str(root) and config['device'] == str(info.st_dev)
         and config['inode'] == str(info.st_ino) and config['synthetic'] == 'False'
         and config['schema'] == '2' and config['legacy_unknown'] == 'True', 'authority_changed')
    need(tables['reservations'] == [] and tables['principal_revocations'] == [], 'authority_changed')
    # Directory link counts can change when content-addressed files are added.
    # Pin ownership/mode/device/inode; regular database links remain pinned above.
    root_identity = {k: v for k, v in physical(info).items() if k != 'nlink'}
    object_identity = {k: v for k, v in physical((root / 'data/objects').lstat()).items() if k != 'nlink'}
    return {'root': root_identity, 'objects': object_identity,
            'control': state, 'research': {'physical': physical(fileinfo(research)),
            'sha256': sha(readfile(research, limit=MAX_DB))}}


def preserve_authority(root, before, deadline):
    current = project_state(root, deadline)
    need(current['root'] == before['root'] and current['objects'] == before['objects']
         and current['research']['physical'] == before['research']['physical'], 'store_changed')
    old, new = before['control'], current['control']
    need(new['physical'] == old['physical'] and new['schema_sha256'] == old['schema_sha256']
         and set(new['tables']) == set(old['tables']), 'authority_changed')
    full = db_state(root / 'runtime/access-control/control.sqlite', deadline)['tables']
    for name, previous in old['tables'].items():
        rows = full[name]
        need(len(rows) >= previous['count'] and sha(canonical(rows[:previous['count']])) == previous['sha256'],
             'authority_changed')
        if name not in DYNAMIC:
            need(new['tables'][name] == previous, 'authority_changed')
    return current


class ExistingOS:
    def __init__(self, original, path, expected, basename=False):
        self.original, self.target, self.expected, self.basename = original, path, expected, basename

    def __getattr__(self, name):
        return getattr(self.original, name)

    def open(self, path, flags, mode=0o777, *, dir_fd=None):
        target = Path(path)
        applies = target == self.target or (self.basename and target == Path(self.target.name))
        if applies and flags & os.O_CREAT:
            need(flags == os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
                 and mode == 0o600, 'unexpected_io')
            if dir_fd is not None:
                need(physical(os.fstat(dir_fd)) == physical(self.target.parent.lstat()), 'store_changed')
            need(physical(fileinfo(self.target)) == self.expected, 'authority_changed')
            raise FileExistsError()  # No creation syscall, even if subsequently deleted.
        return self.original.open(path, flags, mode, dir_fd=dir_fd)


class ExistingSQLite:
    def __init__(self, original, path, expected):
        self.original, self.path, self.expected = original, path, expected

    def __getattr__(self, name):
        return getattr(self.original, name)

    def connect(self, database, *args, **kwargs):
        target = str(database)
        need(target in {str(self.path), self.path.as_uri() + '?mode=ro'}, 'unexpected_io')
        need(physical(fileinfo(self.path)) == self.expected, 'authority_changed')
        if target == str(self.path):
            database, kwargs = self.path.as_uri() + '?mode=rw', {**kwargs, 'uri': True}
        db = self.original.connect(database, *args, **kwargs)
        try:
            need(physical(fileinfo(self.path)) == self.expected, 'authority_changed')
        except BaseException:
            db.close()
            raise
        return db


class Boundary:
    """Block network, child processes, credentials and portfolio entrypoints."""
    def __init__(self, source, root, attempt, request_files):
        self.source, self.root, self.attempt = source, root, attempt
        self.stdlib = Path(sysconfig.get_path('stdlib')).resolve()
        self.allowed = set(request_files) | {Path(__file__).absolute(), Path(__file__).with_name('source-manifest.json')}
        self.db = {root / 'runtime/research.sqlite', root / 'runtime/access-control/control.sqlite'}
        self.denied = []

    def __call__(self, event, args):
        if event.startswith(('socket.', 'subprocess.', 'os.exec', 'os.spawn', 'os.fork')):
            self.denied.append('network_or_process')
            raise Refusal('unexpected_io')
        if event == 'sqlite3.connect':
            need(str(args[0]) in {p.as_uri() + mode for p in self.db for mode in ('?mode=ro', '?mode=rw')},
                 'unexpected_io')
        if event == 'open':
            name, mode, flags = args
            if isinstance(name, int):
                return
            path = Path(os.fsdecode(name))
            if not path.is_absolute():
                if re.fullmatch(r'\.pending-[a-f0-9]{32}', str(path)):
                    need(flags & ~os.O_CLOEXEC == os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         'unexpected_io')
                    return
                if flags & os.O_DIRECTORY and str(path) in {'runtime', 'data', 'objects'}:
                    return
                # Provenance's descriptor-relative operations are independently
                # guarded by the exact loaded source and directory descriptor.
                need(str(path) == 'research.sqlite' or re.fullmatch(r'[a-f0-9]{64}\.bin', str(path)),
                     'unexpected_io')
                return
            writable = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            dbfile = any(str(path) in {str(p) + s for s in ('', '-journal', '-wal', '-shm')} for p in self.db)
            local = path == self.attempt or path.parent == self.attempt or path in self.db or dbfile
            objects = path == self.root / 'data/objects' or path.parent == self.root / 'data/objects'
            directories = path in {self.root, self.root / 'runtime', self.root / 'data',
                                   self.root / 'runtime/access-control'}
            code = (self.source / 'src/quanto' in path.parents or path in
                    {self.source / 'uv.lock', self.source / 'pyproject.toml'})
            system = self.stdlib == path or self.stdlib in path.parents or str(path).startswith('/usr/share/zoneinfo/')
            need(local or objects or (not writable and (directories or code or system or path in self.allowed)),
                 'unexpected_io')
        if event == 'os.remove':
            name, fd = args
            need(re.fullmatch(r'\.pending-[a-f0-9]{32}', os.fsdecode(name))
                 and fd is not None and fd >= 0
                 and physical(os.fstat(fd)) == physical((self.root / 'data/objects').lstat()),
                 'unexpected_io')
        if event == 'os.link':
            source, target, source_fd, target_fd = args
            need(re.fullmatch(r'\.pending-[a-f0-9]{32}', os.fsdecode(source))
                 and re.fullmatch(r'[a-f0-9]{64}\.bin', os.fsdecode(target))
                 and source_fd >= 0 and target_fd >= 0
                 and physical(os.fstat(source_fd)) == physical(os.fstat(target_fd))
                 == physical((self.root / 'data/objects').lstat()), 'unexpected_io')
        if event in {'os.rename', 'os.symlink', 'os.rmdir'}:
            raise Refusal('unexpected_io')
        if event == 'os.mkdir':
            path = Path(os.fsdecode(args[0]))
            need(path in {self.root / 'runtime', self.root / 'runtime/access-control',
                          self.root / 'data', self.root / 'data/objects'}
                 or str(path) in {'runtime', 'data', 'objects'}, 'unexpected_io')


def forbid_calls(frame, event, arg):
    if event != 'call':
        return
    module, name = frame.f_globals.get('__name__', ''), frame.f_code.co_name
    denied = {('quanto.research', 'run_backtest'), ('quanto.event_engine', 'run_event_backtest'),
              ('quanto.study_suite', 'run_suite'), ('quanto.explorer', 'run_submission'),
              ('quanto.research_broker', 'run_workflow'), ('quanto.provider', 'send_research_text'),
              ('quanto.alpaca_data', 'acquire_bars'), ('quanto.alpaca_data', 'acquire_calendar'),
              ('quanto.alpaca_actions', 'acquire_actions')}
    need((module, name) not in denied, 'forbidden_call')


def validate_packet(packet, fixture):
    need(type(packet) is dict and set(packet) == {'version', 'root', 'source_root', 'attempt_id',
        'manifest_sha256', 'controller_sha256', 'tests_sha256', 'preparation_critic_sha256',
        'preflight_evidence_sha256', 'expected_state', 'originals'}, 'invalid_packet')
    need(packet['version'] == 1 and type(packet['version']) is int, 'invalid_packet')
    root, source = Path(packet['root']), Path(packet['source_root'])
    pathcheck(root)
    pathcheck(source)
    need(source == ACTUAL_ROOT, 'invalid_packet')
    if fixture:
        need(root.name == 'invented-project' and root.parent.name.startswith('d008-registration-')
             and root != ACTUAL_ROOT and ACTUAL_ROOT not in root.parents and root not in ACTUAL_ROOT.parents,
             'fixture_boundary')
        need(readfile(root.parent / 'fixture-marker') == b'invented registration fixture\n', 'fixture_boundary')
    else:
        need(root == ACTUAL_ROOT, 'invalid_packet')
    need(type(packet['attempt_id']) is str and re.fullmatch('[a-z0-9][a-z0-9-]{0,79}', packet['attempt_id']),
         'invalid_packet')
    for name in ('manifest_sha256', 'controller_sha256', 'tests_sha256', 'preparation_critic_sha256',
                 'preflight_evidence_sha256'):
        digest(packet[name])
    need(set(packet['originals']) == set(PHASES), 'invalid_packet')
    for phase, old in packet['originals'].items():
        need(set(old) == {'submission_id', 'artifact_sha256', 'request_file', 'request_binding',
                         'submission_request'}, 'invalid_packet')
        need(re.fullmatch('[a-f0-9]{32}', old['submission_id']), 'invalid_packet')
        digest(old['artifact_sha256'])
        need(set(old['request_file']) == {'path', 'sha256'}, 'invalid_packet')
        digest(old['request_file']['sha256'])
        path = Path(old['request_file']['path'])
        pathcheck(path)
        need(root / 'runtime' in path.parents and path.suffix == '.json', 'invalid_packet')
        need(old['request_binding'] in ({'retained_bytes', 'embedded_semantics'} if phase == 'admission'
                                       else {'retained_bytes'}), 'invalid_packet')
        need(set(old['submission_request']) == {'sha256', 'bytes', 'encoding'}, 'invalid_packet')
        digest(old['submission_request']['sha256'])
        need(type(old['submission_request']['bytes']) is int and 0 < old['submission_request']['bytes'] <= 65536
             and old['submission_request']['encoding'] in {'utf8_text', 'canonical_json'}, 'invalid_packet')
    return root, source


def original_requests(store, packet):
    records, documents = {}, {}
    store.journal.verify_events()
    for phase in PHASES:
        old = packet['originals'][phase]
        raw_file = readfile(Path(old['request_file']['path']), limit=65536)
        need(sha(raw_file) == old['request_file']['sha256'], 'request_mismatch')
        document = parse(raw_file)
        need(type(document) is dict, 'request_mismatch')
        submission, old_start, old_finish = sys.modules['quanto.policy_revision']._registered(
            store, old['submission_id'], old['artifact_sha256'], {KINDS[phase]}, {REFS[phase]})
        need(old_start < old_finish, 'lineage_mismatch')
        req = old['submission_request']
        need(submission['kind'] == KINDS[phase] and submission['status'] == 'success'
             and submission['request_sha256'] == req['sha256']
             and submission['request_bytes'] == req['bytes']
             and submission['request_encoding'] == req['encoding']
             and submission['details'][REFS[phase]] == old['artifact_sha256']
             and old['artifact_sha256'] in submission['details']['artifact_refs'], 'lineage_mismatch')
        artifact = store.read_json(old['artifact_sha256'])
        if phase in {'revision', 'admission'}:
            need(canonical(artifact['request']) == canonical(document), 'request_mismatch')
        if phase == 'suite':
            need(artifact['submission_id'] == old['submission_id']
                 and canonical([m['request'] for m in artifact['members']])
                 == canonical(sorted(document['members'], key=lambda m: m['specification']['cost_bps'])),
                 'request_mismatch')
        retained = None
        if phase == 'revision':
            retained = store.read_bytes(submission['details']['request_sha256'])
        elif phase == 'suite':
            retained = store.read_bytes(artifact['registration_request_sha256'])
        elif old['request_binding'] == 'retained_bytes':
            retained = store.read_bytes(req['sha256'])
        if retained is not None:
            need(sha(retained) == req['sha256'] and len(retained) == req['bytes']
                 and canonical(parse(retained)) == canonical(document), 'request_mismatch')
        records[phase] = {'artifact': artifact, 'retained': retained, 'submission': submission}
        documents[phase] = document
    need(documents['admission']['policy_revision_sha256'] == packet['originals']['revision']['artifact_sha256'],
         'lineage_mismatch')
    need(type(documents['suite'].get('members')) is list and len(documents['suite']['members']) == 3,
         'lineage_mismatch')
    need(sorted(m['specification']['cost_bps'] for m in documents['suite']['members']) == [0, 10, 25]
         and all(type(m['specification']['cost_bps']) is int and
                 m['admission_sha256'] == packet['originals']['admission']['artifact_sha256']
                 and m['dataset_sha256'] == documents['admission']['dataset_sha256']
                 for m in documents['suite']['members']), 'lineage_mismatch')
    return records, documents


def new_request(phase, records, documents, mapping):
    if phase == 'revision':
        return records[phase]['retained'].decode('utf-8')
    if phase == 'admission':
        value = {**documents[phase], 'policy_revision_sha256': mapping['revision']['artifact_sha256']}
    else:
        value = {**documents[phase], 'members': [{**member,
            'admission_sha256': mapping['admission']['artifact_sha256']}
            for member in documents[phase]['members']]}
    return canonical(value).decode('utf-8')


def read_manifest(packet):
    path = Path(__file__).with_name('source-manifest.json')
    raw = readfile(path, private=False)
    need(sha(raw) == packet['manifest_sha256'], 'source_mismatch')
    manifest = parse(raw)
    need(manifest['interpreter'] == runtime_identity(), 'source_mismatch')
    need(sha(readfile(Path(__file__), private=False)) == packet['controller_sha256']
         and sha(readfile(Path(__file__).with_name('test_registration_preparation.py'), private=False))
         == packet['tests_sha256'], 'source_mismatch')
    return manifest


def child_main(request_path):
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(Refusal('deadline')))
    arm_deadline(time.monotonic() + WORK_SECONDS)
    environment_check()
    request_raw = readfile(request_path)
    request = parse(request_raw)
    packet = request['packet']
    root, source = validate_packet(packet, request['fixture'])
    attempt, phase, deadline = request_path.parent, request['phase'], request['deadline']
    need(phase in PHASES, 'invalid_packet')
    need(attempt == root / 'runtime/current-code-registration' / packet['attempt_id']
         and request_path.name == phase + '-request.json', 'invalid_packet')
    deadline_check(deadline)
    arm_deadline(deadline)
    intent_raw = readfile(attempt / 'intent.json')
    intent = parse(intent_raw)
    need(sha(intent_raw) == request['intent_sha256'] and intent['packet'] == packet
         and intent['deadline'] == deadline and intent['fixture'] == request['fixture'], 'invalid_packet')
    consumed = parse(readfile(attempt.parent / 'consumed.json'))
    launch = parse(readfile(attempt / (phase + '-launch.json')))
    need(consumed['attempt'] == packet['attempt_id'] and consumed['packet_sha256'] == intent['packet_sha256']
         and consumed['automatic_retry'] is False
         and launch['intent_sha256'] == request['intent_sha256']
         and launch['request_sha256'] == sha(request_raw) and launch['environment'] == {}
         and launch['argv'] == [str(PYTHON), '-I', '-S', '-B', str(Path(__file__).absolute()),
                               '--child', str(request_path)], 'invalid_packet')
    manifest = read_manifest(packet)
    need(project_state(root, deadline) == request['before'], 'store_changed')
    if phase == 'revision':
        need(request['before'] == packet['expected_state'] and request['mapping'] == {}, 'invalid_packet')
    else:
        prior = PHASES[PHASES.index(phase) - 1]
        previous = parse(readfile(attempt / (prior + '-result.json')))
        need(previous['after'] == request['before'] and previous['mapping'] == request['mapping']
             and previous['status'] == 'success' and previous['intent_sha256'] == request['intent_sha256'],
             'invalid_packet')
    loader = load_product(source, manifest['files'])
    need(loaded_identity() == manifest['loaded'] and loader.loaded == manifest['compiled']
         and standard_library_identity() == manifest['stdlib'], 'loaded_mismatch')
    modules = {name: sys.modules['quanto.' + name] for name in MODULES}
    control, research = root / 'runtime/access-control/control.sqlite', root / 'runtime/research.sqlite'
    modules['evaluation_registry'].os = ExistingOS(os, control, request['before']['control']['physical'])
    modules['evaluation_registry'].sqlite3 = ExistingSQLite(sqlite3, control, request['before']['control']['physical'])
    modules['provenance'].os = ExistingOS(os, research, request['before']['research']['physical'], basename=True)
    modules['ledger'].sqlite3 = ExistingSQLite(sqlite3, research, request['before']['research']['physical'])
    monitor = Boundary(source, root, attempt,
                       [Path(item['request_file']['path']) for item in packet['originals'].values()])
    sys.addaudithook(monitor)
    sys.setprofile(forbid_calls)
    supervisor = modules['evaluation_registry'].Supervisor(root, synthetic=False)
    mapping = dict(request['mapping'])
    with supervisor.session() as session:
        session.check(root)
        with modules['provenance'].Provenance(root) as store:
            records, documents = original_requests(store, packet)
            raw = new_request(phase, records, documents, mapping)
        exclusive(attempt / (phase + '-operation-intent.json'), {
            'phase': phase, 'request_utf8': raw, 'request_sha256': sha(raw.encode()),
            'intent_sha256': request['intent_sha256'], 'recorded_at': stamp(),
            'old_submission_id': packet['originals'][phase]['submission_id'],
            'old_artifact_sha256': packet['originals'][phase]['artifact_sha256']})
        deadline_check(deadline)
        functions = {'revision': modules['policy_revision'].register_revision,
                     'admission': modules['admission'].admit_dataset,
                     'suite': modules['study_suite'].register_suite}
        outcome = functions[phase](root, raw)
        exclusive(attempt / (phase + '-operation-outcome.json'), outcome)
        need(outcome.get('status') == 'success', 'registration_refused')
        new_ref = digest(outcome[REFS[phase]])
        need(outcome['submission_id'] != packet['originals'][phase]['submission_id'], 'invalid_result')
        with modules['provenance'].Provenance(root) as store:
            observed = store.get_submission(outcome['submission_id'])
            need(observed['status'] == 'success' and observed['kind'] == KINDS[phase]
                 and observed['request_sha256'] == sha(raw.encode())
                 and observed['details'][REFS[phase]] == new_ref, 'invalid_result')
            if phase == 'revision':
                verified = modules['policy_revision'].validate_revision(store, new_ref)
            elif phase == 'admission':
                verified = modules['admission'].validate_admission(store, new_ref, documents['admission']['dataset_sha256'])
            else:
                verified = modules['study_suite']._verified(store, new_ref)
            need(type(verified) is dict, 'invalid_result')
            original_requests(store, packet)
            store.journal.verify_events()
        mapping[phase] = {'submission_id': outcome['submission_id'], 'artifact_sha256': new_ref,
                         'request_sha256': sha(raw.encode()), 'old_submission_id': packet['originals'][phase]['submission_id'],
                         'old_artifact_sha256': packet['originals'][phase]['artifact_sha256']}
    need(session._closed and modules['evaluation_registry']._ACTIVE is None, 'invalid_result')
    after = preserve_authority(root, request['before'], deadline)
    need(source_files(source) == manifest['files'] and loaded_identity() == manifest['loaded']
         and loader.loaded == manifest['compiled'] and standard_library_identity() == manifest['stdlib'],
         'source_mismatch')
    deadline_check(deadline)
    result = {'status': 'success', 'phase': phase, 'intent_sha256': request['intent_sha256'],
              'request_sha256': sha(request_raw), 'mapping': mapping, 'after': after,
              'loaded_sha256': sha(canonical(manifest['loaded'])), 'compiled': loader.loaded,
              'ended_at': stamp(), 'limitations': LIMITS, 'network_or_process_denials': monitor.denied}
    exclusive(attempt / (phase + '-result.json'), result)
    print('{"status":"phase_complete"}', flush=True)
    return 0


def remaining_time(deadline):
    remaining = deadline - time.monotonic()
    need(remaining > 0, 'deadline')
    return remaining


def arm_deadline(deadline):
    # Never clamp an expired deadline to a new positive grace period.
    remaining = remaining_time(deadline)
    signal.setitimer(signal.ITIMER_REAL, remaining)


def reap(child, cleanup_deadline):
    """One cleanup observation, bounded by the original absolute deadline.

    A late alarm or exhausted allowance does not establish process termination.
    This function never retries an expired wait or hands out a fresh allowance.
    """
    result = {'pid': child.pid, 'reaped': False, 'kill_attempted': False,
              'status': 'unobserved', 'cleanup_deadline': cleanup_deadline}
    try:
        remaining_time(cleanup_deadline)
        returncode = child.poll()
        remaining_time(cleanup_deadline)
        if returncode is None:
            result['kill_attempted'] = True
            child.kill()
            child.wait(timeout=remaining_time(cleanup_deadline))
            returncode = child.returncode
        remaining_time(cleanup_deadline)
        need(returncode is not None, 'cleanup_unobserved')
        result.update(reaped=True, returncode=returncode, status='terminal_observed')
    except BaseException:
        # Includes a delayed signal, TimeoutExpired, wait/kill error or expired
        # initial allowance. No second poll can convert uncertainty to success.
        result['status'] = 'cleanup_unobserved'
    return result


def run(packet_path, packet_sha, *, fixture=False, work_seconds=WORK_SECONDS, hook=None):
    started = time.monotonic()
    need(type(work_seconds) in (int, float) and 0 < work_seconds <= WORK_SECONDS, 'invalid_packet')
    deadline = started + work_seconds
    cleanup_deadline = deadline + CLEANUP_SECONDS
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGALRM)}
    try:
        signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(Refusal('deadline')))
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda *_: (_ for _ in ()).throw(Refusal('interrupted')))
        # The ordinary-process work timer precedes environment, source, packet,
        # database and directory preflight. Both deadlines originate above.
        arm_deadline(deadline)
        return _run(packet_path, packet_sha, fixture=fixture, work_seconds=work_seconds,
                    hook=hook, started=started, deadline=deadline, cleanup_deadline=cleanup_deadline)
    finally:
        # Cleanup belongs solely to _run's single ownership transfer. Resetting
        # our signal state never adopts or reaps an unobserved process.
        signal.setitimer(signal.ITIMER_REAL, 0)
        for sig, handler in handlers.items():
            signal.signal(sig, handler)


def _run(packet_path, packet_sha, *, fixture, work_seconds, hook, started, deadline, cleanup_deadline):
    environment_check()
    raw = readfile(packet_path)
    need(sha(raw) == digest(packet_sha), 'invalid_packet')
    packet = parse(raw)
    root, source = validate_packet(packet, fixture)
    need(fixture or (work_seconds == WORK_SECONDS and hook is None), 'invalid_packet')
    manifest = read_manifest(packet)
    need(source_files(source) == manifest['files'], 'source_mismatch')
    parent = root / 'runtime/current-code-registration'
    directory(parent, private=True)
    need(not os.path.lexists(parent / 'consumed.json') and not any(parent.iterdir()), 'already_consumed')
    deadline_check(deadline)
    attempt = parent / packet['attempt_id']
    exclusive(parent / 'consumed.json', {'attempt': packet['attempt_id'], 'packet_sha256': packet_sha,
              'started_at': stamp(), 'automatic_retry': False})
    attempt.mkdir(mode=0o700)
    syncdir(parent)
    intent = {'packet': packet, 'packet_sha256': packet_sha, 'deadline': deadline,
              'work_seconds': work_seconds, 'cleanup_deadline': cleanup_deadline,
              'fixture': fixture, 'started_at': stamp(),
              'limitations': LIMITS, 'automatic_retry': False}
    intent_sha = exclusive(attempt / 'intent.json', intent)
    child, phase = None, 'preflight'
    launch_in_progress = False
    outputs = []
    mapping = {}
    try:
        before = project_state(root, deadline)
        need(before == packet['expected_state'], 'store_changed')
        for phase in PHASES:
            deadline_check(deadline)
            need(source_files(source) == manifest['files'], 'source_mismatch')
            if hook:
                hook('before_' + phase, attempt)
            need(project_state(root, deadline) == before, 'store_changed')
            request = {'packet': packet, 'before': before, 'mapping': mapping, 'phase': phase,
                       'deadline': deadline, 'intent_sha256': intent_sha, 'fixture': fixture}
            request_path = attempt / (phase + '-request.json')
            request_sha = exclusive(request_path, request)
            argv = [str(PYTHON), '-I', '-S', '-B', str(Path(__file__).absolute()), '--child', str(request_path)]
            exclusive(attempt / (phase + '-launch.json'), {'argv': argv, 'environment': {},
                       'request_sha256': request_sha, 'intent_sha256': intent_sha, 'at': stamp()})
            # On-disk bounded-at-read outputs avoid unbounded communicate buffers.
            outpath, errpath = attempt / (phase + '-stdout.bin'), attempt / (phase + '-stderr.bin')
            outfd = os.open(outpath, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            errfd = os.open(errpath, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try:
                launch_in_progress = True
                child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=outfd, stderr=errfd,
                                         env={}, cwd='/', start_new_session=True)
                launch_in_progress = False
            finally:
                os.close(outfd)
                os.close(errfd)
            exclusive(attempt / (phase + '-owned.json'), {'pid': child.pid, 'intent_sha256': intent_sha})
            try:
                child.wait(timeout=remaining_time(deadline))
            except subprocess.TimeoutExpired:
                raise Refusal('deadline') from None
            exitcode = child.returncode
            child = None
            stdout, stderr = readfile(outpath, limit=4096), readfile(errpath, limit=4096)
            exit_sha = exclusive(attempt / (phase + '-exit.json'), {'exitcode': exitcode,
                'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr), 'stdout_bytes': len(stdout),
                'stderr_bytes': len(stderr), 'intent_sha256': intent_sha, 'at': stamp()})
            need(exitcode == 0 and stdout == b'{"status":"phase_complete"}\n' and not stderr, 'child_failed')
            result_raw = readfile(attempt / (phase + '-result.json'))
            result = parse(result_raw)
            need(result['status'] == 'success' and result['phase'] == phase
                 and result['intent_sha256'] == intent_sha and result['request_sha256'] == request_sha
                 and result['limitations'] == LIMITS and result['network_or_process_denials'] == []
                 and set(result['mapping']) == set(PHASES[:PHASES.index(phase) + 1]), 'invalid_result')
            need(project_state(root, deadline) == result['after'], 'store_changed')
            before, mapping = result['after'], result['mapping']
            outputs.append({'phase': phase, 'result_sha256': sha(result_raw), 'exit_sha256': exit_sha})
            if hook:
                hook('after_' + phase, attempt)
        need(source_files(source) == manifest['files'], 'source_mismatch')
        deadline_check(deadline)
        result = {'status': 'completed', 'packet_sha256': packet_sha, 'intent_sha256': intent_sha,
                  'mapping': mapping, 'phases': outputs, 'after': before, 'completed_at': stamp(),
                  'elapsed_seconds': time.monotonic() - started, 'limits': LIMITS,
                  'automatic_retry': False, 'paid_launch_authorized': False}
        exclusive(attempt / 'result.json', result)
        deadline_check(deadline)
        return result
    except BaseException as exc:
        reason = exc.reason if isinstance(exc, Refusal) else 'internal_failure'
        # Transfer ownership once. Neither the outer finally nor an exception
        # while observing cleanup may repeat a kill/poll/wait on this handle.
        owned, child = child, None
        cleanup = ({'no_live_owned_child': True} if not launch_in_progress else {
            'reaped': False, 'status': 'launch_outcome_unobserved', 'kill_attempted': False}
            ) if owned is None else {
                'pid': owned.pid, 'reaped': False, 'status': 'unobserved', 'kill_attempted': False}
        try:
            arm_deadline(cleanup_deadline)
            if owned is not None:
                cleanup = reap(owned, cleanup_deadline)
            # Persistence shares the same absolute allowance. If it cannot be
            # completed, the consumed/owned records remain explicitly partial.
            deadline_check(cleanup_deadline)
            exclusive(attempt / 'failure.json', {'status': 'unaccepted', 'phase': phase,
                'reason': reason, 'intent_sha256': intent_sha, 'finished_phases': outputs,
                'cleanup': cleanup, 'cleanup_deadline': cleanup_deadline,
                'ended_at': stamp(), 'limits': LIMITS, 'automatic_retry': False})
            deadline_check(cleanup_deadline)
        except BaseException:
            # No late timer renewal, wait, second reap or false clean-exit claim.
            if launch_in_progress or (owned is not None and not cleanup.get('reaped', False)):
                raise Refusal('cleanup_unobserved') from None
        if launch_in_progress or (owned is not None and not cleanup.get('reaped', False)):
            raise Refusal('cleanup_unobserved') from None
        raise Refusal(reason) from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--child', type=Path)
    parser.add_argument('--packet', type=Path)
    parser.add_argument('--packet-sha256')
    args = parser.parse_args()
    try:
        if args.child is not None:
            need(args.packet is None and args.packet_sha256 is None, 'invalid_packet')
            return child_main(args.child)
        need(args.packet is not None and args.packet_sha256 is not None, 'invalid_packet')
        result = run(args.packet, args.packet_sha256)
        print(json.dumps({'status': result['status'], 'completed_registrations': len(result['phases']),
                          'paid_launch_authorized': False}, separators=(',', ':')))
        return 0
    except BaseException as exc:
        reason = exc.reason if isinstance(exc, Refusal) else 'internal_failure'
        if args.child is not None:
            sites, tb = [], exc.__traceback__
            while tb is not None and len(sites) < 30:
                sites.append({'function': tb.tb_frame.f_code.co_name, 'line': tb.tb_lineno})
                tb = tb.tb_next
            try:
                exclusive(args.child.parent / (args.child.name.split('-request.json')[0] + '-failure.json'),
                          {'status': 'unaccepted', 'reason': reason, 'sites': sites,
                           'exception_class': type(exc).__name__, 'at': stamp()})
            except BaseException:
                pass
        print(json.dumps({'status': 'unaccepted', 'reason': reason}, separators=(',', ':')))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

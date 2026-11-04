#!/usr/bin/env python3
"""One supervised paid child. No arguments, fixture mode, retry or resume."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
import re
import signal
from pathlib import Path
import sqlite3
import stat
import sys
import time
import types

ROOT = Path('/Users/ronoktanvir/Documents/ChatGPT/quanto')
STATE = ROOT / 'runtime/manual-development-cycle'
REG_SHA = '3f52a95452d9a20c6c456624f33a70c717d9f1fc28d83ae65f178e67e9d7047d'
REQUIRED = 2_625_000


class Refused(Exception):
    """Deliberately fixed, nonprivate failure text."""


def need(value):
    if not value:
        raise Refused('paid_worker_stopped')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@contextmanager
def descriptor(fd):
    try:
        yield fd
    finally:
        os.close(fd)


def read(path, *, private=True):
    path = Path(path)
    for parent in [path.parent, *path.parents]:
        need(not parent.is_symlink())
    with descriptor(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)) as fd:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
             and before.st_nlink == 1 and before.st_size <= 1024 * 1024
             and not before.st_mode & (0o077 if private else 0o022))
        raw = os.read(fd, before.st_size + 1)
        def identity(info):
            return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns,
                    info.st_uid, info.st_mode, info.st_nlink)
        need(len(raw) == before.st_size and identity(os.fstat(fd)) == identity(before)
             and identity(path.lstat()) == identity(before))
        return raw


def exclusive(path, value):
    raw = canonical(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        with descriptor(os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)) as directory:
            os.fsync(directory)
    except BaseException:
        # A partial exclusive receipt consumes its filename; never replace it.
        raise
    return sha(raw)


def environment_check():
    need(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode)
    need(set(os.environ) <= {'LC_CTYPE', '__CF_USER_TEXT_ENCODING'})
    need(os.environ.get('LC_CTYPE', 'C.UTF-8') in {'C.UTF-8', 'UTF-8'})
    need(re.fullmatch(r'0x[0-9A-Fa-f]+:0x[0-9A-Fa-f]+:0x[0-9A-Fa-f]+',
                     os.environ.get('__CF_USER_TEXT_ENCODING', '0x0:0x0:0x0')))


def bootstrap():
    need(len(sys.argv) == 3 and sys.argv[1] == '--gate-fd'
         and re.fullmatch('[0-9]+', sys.argv[2]) and int(sys.argv[2]) >= 3)
    environment_check()
    need(Path(__file__).absolute() == ROOT / 'runtime/development-cycle-launch-v2-preparation/paid_worker.py')
    consumed = json.loads(read(STATE / 'consumed.json'))
    source = Path(__file__).with_name('supervise.py')
    raw = read(source, private=False)
    need(sha(raw) == consumed['supervisor_sha256'])
    module = types.ModuleType('reviewed_cycle_supervisor')
    module.__file__ = str(source)
    exec(compile(raw, str(source), 'exec', dont_inherit=True), module.__dict__)
    module.await_grant('paid', int(sys.argv[2]))
    return module.worker_context()


def configuration(broker, raw, template, suite):
    config = broker._configuration(raw, False)
    need(config['models'] == broker.DEFAULT_MODELS and template['models'] == broker.DEFAULT_MODELS
         and config['failure_ids'] == template['failure_ids']
         and config['suite_sha256'] == suite
         and config['evidence_kind'] == 'historical_market_data'
         and config['run_key'] != template['run_key'])
    return config


def headroom(journal, provider, ledger):
    # One SQLite snapshot binds budget, purpose-allocation prefix and event head.
    db = journal.connection
    need(not db.in_transaction)
    db.execute('BEGIN')
    try:
        day = datetime.now(timezone.utc).astimezone(ledger.LA).date().isoformat()
        budget = journal.budget_snapshot(day)
        need(budget['day'] == day and budget['limit_micro_usd'] == 20_000_000
             and type(budget['remaining_micro_usd']) is int
             and budget['remaining_micro_usd'] >= REQUIRED)
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='provider_allocations'").fetchone()
        maximum, used = (db.execute(
            "SELECT COALESCE(MAX(rowid),0),COALESCE(SUM(CASE WHEN day=? AND purpose='research' "
            "THEN amount ELSE 0 END),0) FROM provider_allocations", (day,)).fetchone()
            if exists else (0, 0))
        need(type(used) is int and used >= 0 and type(maximum) is int and maximum >= 0
             and provider.PURPOSE_LIMITS['research'] == 4_000_000
             and provider.PURPOSE_LIMITS['research'] - used >= REQUIRED)
        events = journal.verify_events()
        observed = datetime.now(timezone.utc)
        need(observed.astimezone(ledger.LA).date().isoformat() == day)
        observation = {
            'day': day, 'observed_at': observed.isoformat(),
            'event_count': events['count'], 'event_head_sha256': events['head'],
            'purpose_allocation_max_rowid': maximum,
            'global_limit_micro_usd': budget['limit_micro_usd'],
            'global_remaining_micro_usd': budget['remaining_micro_usd'],
            'purpose_limit_micro_usd': provider.PURPOSE_LIMITS['research'],
            'purpose_remaining_micro_usd': provider.PURPOSE_LIMITS['research'] - used,
            'required_micro_usd': REQUIRED, 'planning_only': True}
        db.commit()
        return observation
    except BaseException:
        if db.in_transaction:
            db.rollback()
        raise


def verify_budget_order(journal, observation, ledger):
    need(datetime.now(timezone.utc).astimezone(ledger.LA).date().isoformat() == observation['day'])
    events = journal.verify_events()
    count = observation['event_count']
    need(type(count) is int and 0 <= count <= events['count'])
    if count == events['count']:
        need(events['head'] == observation['event_head_sha256'])
    elif count == 0:
        need(observation['event_head_sha256'] == '0' * 64)
    else:
        row = journal.connection.execute('SELECT event_hash FROM events WHERE id=?', (count,)).fetchone()
        need(row is not None and row[0] == observation['event_head_sha256'])
    need(datetime.now(timezone.utc).astimezone(ledger.LA).date().isoformat() == observation['day'])
    return events


def forbid_calls(frame, event, arg):
    if event != 'call':
        return
    module, name = frame.f_globals.get('__name__', ''), frame.f_code.co_name
    need(not (module.startswith(('quanto.execution', 'quanto.runpod'))
              or (module in {'quanto.alpaca_data', 'quanto.alpaca_actions'}
                  and name in {'_acquire', 'acquire_bars', 'acquire_calendar', 'acquire_actions'})
              or (module == 'quanto.provider' and name in {'request_text', 'diagnose_operations'})
              or (module == 'quanto.critic' and name in {'request_review'})))


class Authority:
    """Durable positive parent grant and original two-clock window."""

    def __init__(self, state, deadline):
        self.state, self.deadline = state, deadline
        self.raw = {name: read(state / name) for name in
                    ('consumed.json', 'paid-launch.json', 'owned.json', 'start.json')}
        self.consumed, self.launch, self.owned, self.start = (
            json.loads(self.raw[name]) for name in self.raw)
        self.pid, self.parent = os.getpid(), os.getppid()
        self.paid_sha, self.day, self.ledger = None, None, None
        self.check()

    def owns_consumption(self):
        need(self.paid_sha is not None
             and sha(read(self.state / 'paid-consumed.json')) == self.paid_sha)

    def check(self):
        need(not os.path.lexists(self.state / 'failure.json')
             and self.parent > 1 and os.getpid() == self.pid and os.getppid() == self.parent)
        need(all(read(self.state / name) == raw for name, raw in self.raw.items()))
        consumed_sha, launch_sha, owned_sha = (sha(self.raw[name]) for name in
                                              ('consumed.json', 'paid-launch.json', 'owned.json'))
        need(self.consumed['parent_pid'] == self.launch['parent_pid']
             == self.owned['parent_pid'] == self.start['parent_pid'] == self.parent
             and self.owned['pid'] == self.start['pid'] == self.pid
             and self.owned['phase'] == self.start['phase'] == 'paid'
             and self.consumed['automatic_retry'] is False
             and self.consumed['limit_seconds'] == 7200
             and self.launch['plan_sha256'] == self.consumed['plan_sha256']
             and self.launch['consumed_sha256'] == self.owned['consumed_sha256']
             == self.start['consumed_sha256'] == consumed_sha
             and self.owned['paid_launch_sha256'] == self.start['launch_sha256'] == launch_sha
             and self.start['owned_sha256'] == owned_sha)
        remaining = min(self.deadline - time.monotonic(),
                        self.consumed['start_monotonic'] + 7195 - time.monotonic(),
                        self.consumed['start_wall'] + 7195 - time.time())
        need(0 < remaining <= 7195)
        if self.day is not None:
            need(datetime.now(timezone.utc).astimezone(self.ledger.LA).date().isoformat() == self.day)
        if self.paid_sha is not None:
            self.owns_consumption()
        # Refresh only to the original shorter bound; never grant another interval.
        if signal.getsignal(signal.SIGALRM) == interrupt:
            signal.setitimer(signal.ITIMER_REAL, remaining)
        return remaining

    def profile(self, frame, event, arg):
        forbid_calls(frame, event, arg)
        if event == 'call' and (frame.f_globals.get('__name__'), frame.f_code.co_name) in {
            ('quanto.research_broker', 'run_workflow'),
            ('quanto.research_dispatch', '_authorize'),
            ('quanto.provider', '_send_research'), ('quanto.critic', 'local_key')
        }:
            self.check()


def execute(context, consumption=None):
    """Internal seam for invented unit contexts; never selected by CLI or packet."""
    root, state, plan, reg, packet, result, request_text, deadline = context
    reg.deadline_check(deadline)
    authority = Authority(state, deadline)
    if consumption is None:
        consumption = {}
    # Consumes the paid attempt before loading product, inspecting a key or opening stores.
    paid_consumed_sha = exclusive(state / 'paid-consumed.json', {
        'automatic_retry': False, 'request_sha256': sha(request_text.encode()),
        'deadline': deadline, 'parent_pid': os.getppid()})
    consumption['authority'] = authority
    authority.paid_sha = paid_consumed_sha
    consumed_raw, launch_raw = authority.raw['consumed.json'], authority.raw['paid-launch.json']
    consumed, launch = json.loads(consumed_raw), json.loads(launch_raw)
    need(launch['consumed_sha256'] == sha(consumed_raw)
         and launch['parent_pid'] == consumed['parent_pid'] == os.getppid()
         and launch['request_sha256'] == sha(request_text.encode())
         and launch['registration_result_sha256'] == sha(canonical(result)))
    bindings = {'paid_consumed_sha256': paid_consumed_sha,
                'consumed_sha256': sha(consumed_raw), 'paid_launch_sha256': sha(launch_raw),
                'request_sha256': sha(request_text.encode()),
                'registration_result_sha256': launch['registration_result_sha256'],
                'owned_sha256': sha(authority.raw['owned.json']),
                'start_sha256': sha(authority.raw['start.json'])}
    need(sha(reg.readfile(Path(reg.__file__), private=False)) == REG_SHA)
    manifest = reg.read_manifest(packet)
    source = Path(plan['source_root'])
    need(reg.project_state(root, deadline) == result['after'])
    loader = reg.load_product(source, manifest['files'])
    need(reg.loaded_identity() == manifest['loaded'] and loader.loaded == manifest['compiled']
         and reg.standard_library_identity() == manifest['stdlib'])
    broker = importlib.import_module('quanto.research_broker')
    provider = importlib.import_module('quanto.provider')
    ledger = importlib.import_module('quanto.ledger')
    authority.ledger = ledger
    registry = importlib.import_module('quanto.evaluation_registry')
    provenance = importlib.import_module('quanto.provenance')
    suite = result['mapping']['suite']['artifact_sha256']
    config = configuration(broker, request_text, plan['request_template'], suite)
    control, research = root / 'runtime/access-control/control.sqlite', root / 'runtime/research.sqlite'
    registry.os = reg.ExistingOS(os, control, result['after']['control']['physical'])
    registry.sqlite3 = reg.ExistingSQLite(sqlite3, control, result['after']['control']['physical'])
    provenance.os = reg.ExistingOS(os, research, result['after']['research']['physical'], basename=True)
    ledger.sqlite3 = reg.ExistingSQLite(sqlite3, research, result['after']['research']['physical'])
    before_loaded, before_compiled = reg.loaded_identity(), dict(loader.loaded)
    before_broker = broker.code_identity()
    exclusive(state / 'paid-before.json', {
        'state': result['after'], 'loaded_sha256': sha(reg.canonical(before_loaded)),
        'compiled': before_compiled, 'broker_code': before_broker})
    previous_profile = sys.getprofile()
    sys.setprofile(authority.profile)
    try:
        supervisor = registry.Supervisor(root, synthetic=False)
        with supervisor.session() as session:
            session.check(root)
            with provenance.Provenance(root) as store:
                verified = importlib.import_module('quanto.study_suite')._verified(store, suite)
                need(type(verified) is dict)
                provider._research_ready(root)
                # Only this consumed request process checks the credential; never retain it.
                authority.check()
                need(bool(provider.local_key(root)))
                budget_observation = headroom(store.journal, provider, ledger)
                authority.day = budget_observation['day']
                authority.check()
                budget_sha = exclusive(state / 'prelaunch-budget.json', budget_observation)
                reg.deadline_check(deadline)
                need(reg.source_files(source) == manifest['files']
                     and broker.code_identity() == before_broker)
                events = verify_budget_order(store.journal, budget_observation, ledger)
                prelaunch_sha = exclusive(state / 'prelaunch.json', {
                    'event_count': events['count'], 'event_head_sha256': events['head'],
                    'request_sha256': sha(request_text.encode()), 'run_key': config['run_key'],
                    'suite_sha256': suite,
                    'failure_roster_sha256': sha(reg.canonical(config['failure_ids']))})
                reg.deadline_check(deadline)
                need(sha(read(state / 'prelaunch.json')) == prelaunch_sha
                     and sha(read(state / 'paid-consumed.json')) == paid_consumed_sha
                     and read(state / 'consumed.json') == consumed_raw
                     and read(state / 'paid-launch.json') == launch_raw
                     and sha(read(state / 'prelaunch-budget.json')) == budget_sha)
                authority.check()
                exclusive(state / 'paid-call-entered.json', {
                    **bindings, 'prelaunch_sha256': prelaunch_sha,
                    'prelaunch_budget_sha256': budget_sha})
                # Real existing session; exactly one normal broker call, no injected transport.
                authority.check()
                outcome = broker.run_workflow(root, request_text)
                authority.owns_consumption()
                outcome_sha = exclusive(state / 'outcome.json', outcome)
            need(session is not None)
        need(session._closed and registry._ACTIVE is None)
        authority.owns_consumption()
        after = reg.preserve_authority(root, result['after'], deadline)
        need(reg.source_files(source) == manifest['files']
             and reg.loaded_identity() == before_loaded and loader.loaded == before_compiled
             and reg.standard_library_identity() == manifest['stdlib']
             and broker.code_identity() == before_broker)
        exclusive(state / 'paid-after.json', {
            'state': after, 'loaded_sha256': sha(reg.canonical(reg.loaded_identity())),
            'compiled': dict(loader.loaded), 'broker_code': broker.code_identity()})
        # Pending/invalid/malformed normal returns remain exact audit inputs; no acceptance.
        need(type(outcome) is dict and outcome.get('status') in {'success', 'invalid', 'pending'})
        reg.deadline_check(deadline)
        authority.check()
        return outcome_sha, prelaunch_sha
    finally:
        sys.setprofile(previous_profile)
        if not os.path.lexists(state / 'paid-after.json'):
            try:
                reg.deadline_check(deadline)
                authority.owns_consumption()
                after = reg.preserve_authority(root, result['after'], deadline)
                exclusive(state / 'paid-after.json', {
                    'state': after, 'loaded_sha256': sha(reg.canonical(reg.loaded_identity())),
                    'compiled': dict(loader.loaded), 'broker_code': broker.code_identity(),
                    'uncertain': True, 'source_matches': reg.source_files(source) == manifest['files'],
                    'loaded_matches': reg.loaded_identity() == before_loaded})
            except BaseException:
                pass  # Finite parent/auditor retain unobserved post-state uncertainty.


def run(context_factory=bootstrap):
    state, outcome_sha, previous_alarm = None, None, None
    consumption = {}
    try:
        context = context_factory()
        state = context[1]  # Publish failures only after authenticated bootstrap succeeds.
        remaining = context[7] - time.monotonic()
        need(remaining > 0)
        previous_alarm = (signal.getsignal(signal.SIGALRM),
                          signal.getitimer(signal.ITIMER_REAL), time.monotonic())
        signal.signal(signal.SIGALRM, interrupt)
        signal.setitimer(signal.ITIMER_REAL, remaining)
        outcome_sha, prelaunch_sha = execute(context, consumption)
        consumption['authority'].owns_consumption()
        exclusive(state / 'terminal.json', {
            'status': 'broker_returned', 'outcome_sha256': outcome_sha,
            'prelaunch_sha256': prelaunch_sha,
            'operational_acceptance': False, 'investment_validation': False})
        print('{"status":"broker_returned"}', flush=True)
        return 0
    except BaseException:
        # Never serialize exception text: it may contain private/provider material.
        try:
            if state is None or 'authority' not in consumption:
                return 1
            consumption['authority'].owns_consumption()
            path = state / 'outcome.json'
            if not os.path.lexists(path):
                exclusive(path, {
                    'status': 'uncertain', 'error_code': 'paid_worker_stopped',
                    'operational_acceptance': False, 'investment_validation': False,
                    'automatic_retry': False, 'effects_or_charges_possible': True})
            outcome_sha = sha(read(path))
            exclusive(state / 'terminal.json', {
                'status': 'refused_or_uncertain', 'outcome_sha256': outcome_sha,
                'operational_acceptance': False, 'investment_validation': False})
        except BaseException:
            pass  # Parent owns finite cleanup and retains missing-publication uncertainty.
        return 1
    finally:
        if previous_alarm is not None:
            signal.setitimer(signal.ITIMER_REAL, 0)
            handler, timer, started = previous_alarm
            signal.signal(signal.SIGALRM, handler)
            if timer[0] > 0:
                signal.setitimer(signal.ITIMER_REAL,
                                 max(0.000001, timer[0] - (time.monotonic() - started)), timer[1])


def interrupt(_signum, _frame):
    raise Refused('paid_worker_stopped')


if __name__ == '__main__':
    raise SystemExit(run())

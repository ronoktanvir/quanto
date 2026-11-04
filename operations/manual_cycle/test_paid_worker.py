"""Invented isolated roots and fake modules only. No real controller entrypoint."""
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

SPEC = importlib.util.spec_from_file_location('paid_worker_fixture', Path(__file__).with_name('paid_worker.py'))
w = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(w)


def document(path):
    return json.loads(path.read_bytes())


@pytest.fixture
def invented(tmp_path, monkeypatch):
    root = tmp_path / 'invented-project'
    state = root / 'runtime/manual-development-cycle'
    state.mkdir(parents=True, mode=0o700)
    db = sqlite3.connect(':memory:', isolation_level=None)
    db.execute('CREATE TABLE provider_allocations(day TEXT,purpose TEXT,amount INTEGER)')
    calls = []
    manifest = {'files': {'fake': 'digest'}, 'loaded': {'baseline': True},
                'compiled': {'fake': 'compiled'}, 'stdlib': {'stdlib': 'pinned'}}
    baseline = {'control': {'physical': {}}, 'research': {'physical': {}}}
    result = {'after': baseline, 'mapping': {'suite': {'artifact_sha256': 'a' * 64}}}
    models = {'hypothesis': 'haiku', 'critic': 'opus'}
    template = {'run_key': 'prior', 'failure_ids': [{'source': 'attempt', 'id': 'b' * 32}],
                'models': models, 'suite_sha256': 'c' * 64, 'evidence_kind': 'historical_market_data'}
    request = {**template, 'run_key': 'new', 'suite_sha256': 'a' * 64}
    loader = SimpleNamespace(loaded=dict(manifest['compiled']))
    reg = SimpleNamespace(__file__='/invented/controller.py', canonical=w.canonical,
        readfile=lambda *a, **kw: b'invented controller',
        read_manifest=lambda packet: manifest, deadline_check=lambda d: None,
        project_state=lambda *a: baseline, load_product=lambda *a: loader,
        loaded_identity=lambda: manifest['loaded'], standard_library_identity=lambda: manifest['stdlib'],
        source_files=lambda source: manifest['files'],
        ExistingOS=lambda original, *a, **kw: original,
        ExistingSQLite=lambda original, *a: original)
    def preserve(*args):
        calls.append('preserve_after')
        return {**baseline, 'legitimate_new_effects': True}
    reg.preserve_authority = preserve
    monkeypatch.setattr(w, 'REG_SHA', w.sha(b'invented controller'))
    journal = SimpleNamespace(connection=db, budget_snapshot=lambda day: {'remaining_micro_usd': 20_000_000, 'day': day, 'limit_micro_usd': 20_000_000},
                              verify_events=lambda: {'count': 42, 'head': 'd' * 64})
    @contextmanager
    def provenance(root):
        assert registry._ACTIVE is not None
        yield SimpleNamespace(journal=journal)
    class Supervisor:
        def __init__(self, root, synthetic):
            assert not synthetic
        @contextmanager
        def session(self):
            session = SimpleNamespace(_closed=False, check=lambda root: calls.append('session_check'))
            registry._ACTIVE = session
            try:
                yield session
            finally:
                session._closed = True
                registry._ACTIVE = None
    registry = SimpleNamespace(Supervisor=Supervisor, _ACTIVE=None)
    def key(root):
        assert (state / 'paid-consumed.json').exists()
        calls.append('credential_checked')
        return 'invented-noncredential'
    def workflow(root, raw):
        assert registry._ACTIVE is not None
        assert document(state / 'prelaunch.json')['event_count'] == 42
        assert (state / 'paid-call-entered.json').exists()
        calls.append('workflow')
        return {'status': 'success', 'operational_acceptance': False, 'investment_validation': False}
    broker = SimpleNamespace(_configuration=lambda raw, synthetic: json.loads(raw),
                             DEFAULT_MODELS=models, code_identity=lambda: {'code': 'pinned'},
                             run_workflow=workflow)
    provider = SimpleNamespace(PURPOSE_LIMITS={'research': 4_000_000},
                               _research_ready=lambda root: None, local_key=key)
    ledger = SimpleNamespace(LA=ZoneInfo('America/Los_Angeles'))
    modules = {'research_broker': broker, 'provider': provider, 'ledger': ledger,
               'evaluation_registry': registry, 'provenance': SimpleNamespace(Provenance=provenance),
               'study_suite': SimpleNamespace(_verified=lambda *a: {'suite': 'invented'})}
    monkeypatch.setattr(w.importlib, 'import_module', lambda name: modules[name.removeprefix('quanto.')])
    context = (root, state, {'source_root': str(root), 'request_template': template}, reg,
               {}, result, json.dumps(request), w.time.monotonic() + 3600)
    consumed = {'parent_pid': w.os.getppid(), 'start_monotonic': w.time.monotonic(),
                'start_wall': w.time.time(), 'limit_seconds': 7200, 'automatic_retry': False,
                'plan_sha256': '9' * 64}
    w.exclusive(state / 'consumed.json', consumed)
    w.exclusive(state / 'paid-launch.json', {
        'parent_pid': w.os.getppid(), 'consumed_sha256': w.sha(w.canonical(consumed)),
        'plan_sha256': consumed['plan_sha256'],
        'request_sha256': w.sha(context[6].encode()),
        'registration_result_sha256': w.sha(w.canonical(result))})
    owned_sha = w.exclusive(state / 'owned.json', {
        'pid': w.os.getpid(), 'parent_pid': w.os.getppid(), 'phase': 'paid',
        'consumed_sha256': w.sha((state / 'consumed.json').read_bytes()),
        'paid_launch_sha256': w.sha((state / 'paid-launch.json').read_bytes())})
    w.exclusive(state / 'start.json', {
        'pid': w.os.getpid(), 'parent_pid': w.os.getppid(), 'phase': 'paid',
        'consumed_sha256': w.sha((state / 'consumed.json').read_bytes()),
        'launch_sha256': w.sha((state / 'paid-launch.json').read_bytes()), 'owned_sha256': owned_sha})
    yield SimpleNamespace(context=context, state=state, reg=reg, calls=calls, request=request,
                          broker=broker, provider=provider, ledger=ledger, journal=journal,
                          manifest=manifest, db=db, registry=registry)
    db.close()


def test_exact_single_call_and_prelaunch_and_append_state(invented):
    f = invented
    assert w.run(lambda: f.context) == 0
    assert f.calls.count('workflow') == 1
    pre = document(f.state / 'prelaunch.json')
    assert set(pre) == {'event_count', 'event_head_sha256', 'request_sha256', 'run_key',
                        'suite_sha256', 'failure_roster_sha256'}
    assert pre['failure_roster_sha256'] == w.sha(w.canonical(f.request['failure_ids']))
    assert document(f.state / 'paid-after.json')['state']['legitimate_new_effects']
    terminal = document(f.state / 'terminal.json')
    assert terminal == {'status': 'broker_returned',
                        'outcome_sha256': w.sha((f.state / 'outcome.json').read_bytes()),
                        'prelaunch_sha256': w.sha((f.state / 'prelaunch.json').read_bytes()),
                        'operational_acceptance': False, 'investment_validation': False}


@pytest.mark.parametrize('status', ['invalid', 'pending', 'malformed', None])
def test_exact_normal_outcome_is_preserved(invented, status):
    f = invented
    outcome = {'status': status, 'private_invented': 'preserve-verbatim'}
    f.broker.run_workflow = lambda *a: outcome
    assert w.run(lambda: f.context) == (0 if status in {'invalid', 'pending'} else 1)
    assert document(f.state / 'outcome.json') == outcome
    assert document(f.state / 'terminal.json')['operational_acceptance'] is False


def test_provider_exception_is_uncertain_and_never_leaks(invented, capsys):
    f = invented
    def crash(*args):
        f.calls.append('workflow')
        raise RuntimeError('invented-sensitive-provider-text')
    f.broker.run_workflow = crash
    assert w.run(lambda: f.context) == 1
    assert f.calls.count('workflow') == 1
    assert document(f.state / 'outcome.json')['effects_or_charges_possible'] is True
    assert 'invented-sensitive' not in ''.join(p.read_text() for p in f.state.glob('*.json'))
    assert not capsys.readouterr().out


@pytest.mark.parametrize('field,value', [
    ('models', {'hypothesis': 'opus', 'critic': 'opus'}),
    ('failure_ids', []), ('failure_ids', [{'source': 'attempt', 'id': 'f' * 32}]),
    ('suite_sha256', 'f' * 64), ('evidence_kind', 'synthetic_fixture'), ('run_key', 'prior')])
def test_changed_request_refused_before_key_or_dispatch(invented, field, value):
    f = invented
    req = {**f.request, field: value}
    context = (*f.context[:6], json.dumps(req), f.context[7])
    assert w.run(lambda: context) == 1
    assert 'credential_checked' not in f.calls and 'workflow' not in f.calls


@pytest.mark.parametrize('global_remaining,purpose_used,okay', [
    (2_625_000, 1_375_000, True), (2_624_999, 0, False),
    (20_000_000, 1_375_001, False), (20_000_000, -1, False)])
def test_both_headroom_boundaries(invented, global_remaining, purpose_used, okay):
    f = invented
    day = w.datetime.now(w.timezone.utc).astimezone(f.ledger.LA).date().isoformat()
    f.journal.budget_snapshot = lambda d: {'remaining_micro_usd': global_remaining, 'day': d, 'limit_micro_usd': 20_000_000}
    f.db.execute('INSERT INTO provider_allocations VALUES (?,?,?)', (day, 'research', purpose_used))
    assert w.run(lambda: f.context) == (0 if okay else 1)
    assert ('workflow' in f.calls) is okay


def test_stale_state_refused_before_product_load(invented):
    f = invented
    f.reg.project_state = lambda *a: {'changed': True}
    f.reg.load_product = lambda *a: pytest.fail('must not load')
    assert w.run(lambda: f.context) == 1


def test_exact_helper_pin_required(invented):
    f = invented
    f.reg.readfile = lambda *a, **kw: b'changed'
    assert w.run(lambda: f.context) == 1
    assert not f.calls


def test_consumed_attempt_cannot_repeat(invented):
    f = invented
    assert w.run(lambda: f.context) == 0
    original = (f.state / 'outcome.json').read_bytes()
    assert w.run(lambda: f.context) == 1
    assert f.calls.count('workflow') == 1
    assert (f.state / 'outcome.json').read_bytes() == original


def test_after_source_change_preserves_outcome_but_denies_completion(invented):
    f = invented
    def changed(*args):
        f.reg.source_files = lambda source: {'changed': True}
        return {'status': 'success'}
    f.broker.run_workflow = changed
    assert w.run(lambda: f.context) == 1
    assert document(f.state / 'outcome.json') == {'status': 'success'}
    assert document(f.state / 'terminal.json')['status'] == 'refused_or_uncertain'


def test_event_chain_failure_never_enters_broker(invented):
    f = invented
    def fail():
        raise ValueError('chain damaged')
    f.journal.verify_events = fail
    assert w.run(lambda: f.context) == 1
    assert 'workflow' not in f.calls
    assert not (f.state / 'prelaunch.json').exists()


@pytest.mark.parametrize('module,name', [('quanto.execution', 'place_order'),
    ('quanto.runpod', 'upload'), ('quanto.alpaca_data', '_acquire'),
    ('quanto.alpaca_actions', 'acquire_actions'), ('quanto.provider', 'request_text')])
def test_denied_calls(module, name):
    frame = SimpleNamespace(f_globals={'__name__': module}, f_code=SimpleNamespace(co_name=name))
    with pytest.raises(w.Refused):
        w.forbid_calls(frame, 'call', None)


def test_no_args_or_fixture_switch(monkeypatch):
    monkeypatch.setattr(w.sys, 'argv', ['paid_worker.py', '--fixture'])
    with pytest.raises(w.Refused):
        w.bootstrap()


def test_safe_reader_rejects_symlink_and_receipt_collision(tmp_path):
    original = tmp_path / 'original'
    original.write_bytes(b'invented')
    original.chmod(0o600)
    link = tmp_path / 'link'
    link.symlink_to(original)
    with pytest.raises(OSError):
        w.read(link)
    receipt = tmp_path / 'receipt'
    w.exclusive(receipt, {'invented': True})
    with pytest.raises(FileExistsError):
        w.exclusive(receipt, {'changed': True})
    assert document(receipt) == {'invented': True}


def test_real_adjacent_context_contract_uses_invented_receipts(invented, monkeypatch):
    f = invented
    source = Path(__file__).with_name('supervise.py')
    spec = importlib.util.spec_from_file_location('invented_supervisor_contract', source)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    monkeypatch.setattr(supervisor, 'ROOT', f.context[0])
    monkeypatch.setattr(supervisor, 'STATE', f.state)
    plan = {**f.context[2], 'supervisor_sha256': 'e' * 64, 'run_key': 'new'}
    consumed = {'parent_pid': supervisor.os.getppid(), 'plan_sha256': 'f' * 64,
                'supervisor_sha256': 'e' * 64,
                'start_monotonic': supervisor.time.monotonic(), 'start_wall': supervisor.time.time(),
                'limit_seconds': 7200, 'automatic_retry': False}
    (f.state / 'consumed.json').unlink()
    (f.state / 'paid-launch.json').unlink()
    supervisor.publish(f.state / 'consumed.json', consumed)
    raw = supervisor.canonical(f.request)
    (f.state / 'request.json').write_bytes(raw)
    (f.state / 'request.json').chmod(0o600)
    launch = {'parent_pid': supervisor.os.getppid(),
              'consumed_sha256': supervisor.sha((f.state / 'consumed.json').read_bytes()),
              'plan_sha256': 'f' * 64, 'registration_result_sha256': w.sha(w.canonical(f.context[5])),
              'request_sha256': supervisor.sha(raw)}
    supervisor.publish(f.state / 'paid-launch.json', launch)
    (f.state / 'owned.json').unlink()
    (f.state / 'start.json').unlink()
    owned_sha = supervisor.publish(f.state / 'owned.json', {
        'pid': w.os.getpid(), 'parent_pid': w.os.getppid(), 'phase': 'paid',
        'consumed_sha256': launch['consumed_sha256'],
        'paid_launch_sha256': w.sha((f.state / 'paid-launch.json').read_bytes())})
    supervisor.publish(f.state / 'start.json', {
        'pid': w.os.getpid(), 'parent_pid': w.os.getppid(), 'phase': 'paid',
        'consumed_sha256': launch['consumed_sha256'],
        'launch_sha256': w.sha((f.state / 'paid-launch.json').read_bytes()), 'owned_sha256': owned_sha})
    monkeypatch.setattr(supervisor, 'load_plan', lambda pin: (plan, f.reg, {}))
    monkeypatch.setattr(supervisor, 'registration_result', lambda *args: f.context[5])
    reader, writer = w.os.pipe()
    w.os.write(writer, b'G')
    w.os.close(writer)
    supervisor.await_grant('paid', reader)
    context = supervisor.worker_context()
    assert len(context) == 8 and context[6] == raw.decode()
    assert context[7] > supervisor.time.monotonic()
    assert w.run(lambda: context) == 0


def test_exception_path_observes_new_effects_without_old_equality(invented):
    f = invented
    def crash(*args):
        raise RuntimeError('invented-interruption')
    f.broker.run_workflow = crash
    assert w.run(lambda: f.context) == 1
    after = document(f.state / 'paid-after.json')
    assert after['uncertain'] is True and after['state']['legitimate_new_effects'] is True


def test_reviewed_interpreter_hermetic_broker_imports_and_loaded_mutation():
    """Public source only; no constructors, project content or provider access."""
    import subprocess
    root = Path(__file__).resolve().parents[2]
    helper = root / 'runtime/development-cycle-registration-v2-preparation/prepare_current_code.py'
    script = '''import hashlib, importlib, pathlib, sys, types
root = pathlib.Path(sys.argv[1])
helper = pathlib.Path(sys.argv[2])
raw = helper.read_bytes()
assert hashlib.sha256(raw).hexdigest() == sys.argv[3]
reg = types.ModuleType('invented_import_probe')
reg.__file__ = str(helper)
exec(compile(raw, str(helper), 'exec'), reg.__dict__)
loader = reg.load_product(root, reg.source_files(root))
broker = importlib.import_module('quanto.research_broker')
identity = reg.loaded_identity()
assert 'quanto.research_broker' in identity['modules']
assert set(loader.loaded) == set(identity['modules'])
assert all(str(root / 'src/quanto') in v['file'] for v in identity['modules'].values())
broker.DEFAULT_MODELS = dict(broker.DEFAULT_MODELS, director='invented-model-change')
assert reg.loaded_identity() != identity
print('public hermetic import/mutation probe passed')
'''
    checked = subprocess.run([
        '/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11', '-I', '-S', '-B',
        '-c', script, str(root), str(helper),
        '3f52a95452d9a20c6c456624f33a70c717d9f1fc28d83ae65f178e67e9d7047d'],
        env={}, stdin=subprocess.DEVNULL, capture_output=True, timeout=20)
    assert checked.returncode == 0, checked.stderr.decode()
    assert checked.stdout == b'public hermetic import/mutation probe passed\n'


def test_direct_exact_call_bindings(invented):
    f = invented
    _, prelaunch_sha = w.execute(f.context)
    entered = document(f.state / 'paid-call-entered.json')
    for field, filename in [('prelaunch_sha256', 'prelaunch.json'),
                            ('paid_consumed_sha256', 'paid-consumed.json'),
                            ('consumed_sha256', 'consumed.json'),
                            ('paid_launch_sha256', 'paid-launch.json'),
                            ('prelaunch_budget_sha256', 'prelaunch-budget.json'),
                            ('owned_sha256', 'owned.json'), ('start_sha256', 'start.json')]:
        assert entered[field] == w.sha((f.state / filename).read_bytes())
    assert entered['prelaunch_sha256'] == prelaunch_sha
    assert entered['request_sha256'] == w.sha(f.context[6].encode())
    assert entered['registration_result_sha256'] == w.sha(w.canonical(f.context[5]))



def test_failed_bootstrap_cannot_publish_into_default_state(invented, monkeypatch):
    f = invented
    monkeypatch.setattr(w, 'STATE', f.state)
    def refused():
        raise w.Refused('paid_worker_stopped')
    before = set(f.state.iterdir())
    assert w.run(refused) == 1
    assert set(f.state.iterdir()) == before


def test_real_child_alarm_interrupts_without_extending_deadline(invented, monkeypatch):
    f = invented
    context = (*f.context[:7], w.time.monotonic() + 0.03)
    previous_handler = w.signal.getsignal(w.signal.SIGALRM)
    def stalled(context, consumption):
        w.time.sleep(0.3)
        pytest.fail('deadline failed to interrupt')
    monkeypatch.setattr(w, 'execute', stalled)
    started = w.time.monotonic()
    assert w.run(lambda: context) == 1
    assert w.time.monotonic() - started < 0.2
    assert w.signal.getsignal(w.signal.SIGALRM) == previous_handler
    assert w.signal.getitimer(w.signal.ITIMER_REAL)[0] == 0


@pytest.mark.parametrize('changed', ['consumed.json', 'paid-launch.json'])
def test_durable_binding_changes_refuse_before_model_access(invented, changed):
    f = invented
    path = f.state / changed
    value = document(path)
    value['parent_pid'] = -1
    path.write_bytes(w.canonical(value))
    assert w.run(lambda: f.context) == 1
    assert 'credential_checked' not in f.calls and 'workflow' not in f.calls


def test_reviewed_minimal_environment_preflight_only():
    import subprocess
    source = Path(__file__).with_name('paid_worker.py').resolve()
    script = """import pathlib,sys,types
p=pathlib.Path(sys.argv[1])
m=types.ModuleType('environment_only_probe')
m.__file__=str(p)
exec(compile(p.read_bytes(), str(p), 'exec'), m.__dict__)
m.environment_check()
print('minimal environment passed')
"""
    checked = subprocess.run([
        '/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11', '-I', '-S', '-B',
        '-c', script, str(source)], env={}, stdin=subprocess.DEVNULL,
        capture_output=True, timeout=10)
    assert checked.returncode == 0, checked.stderr.decode()
    assert checked.stdout == b'minimal environment passed\n'


@pytest.mark.parametrize('environment', [
    {'ANTHROPIC_API_KEY': 'invented'}, {'UNREVIEWED': 'x'}, {'LC_CTYPE': 'bad'},
    {'__CF_USER_TEXT_ENCODING': 'bad'}])
def test_extra_or_malformed_environment_rejected(monkeypatch, environment):
    monkeypatch.setattr(w.sys, 'flags', SimpleNamespace(isolated=1, no_site=1))
    monkeypatch.setattr(w.sys, 'dont_write_bytecode', True)
    monkeypatch.setattr(w.os, 'environ', environment)
    with pytest.raises(w.Refused):
        w.environment_check()


@pytest.mark.parametrize('module,name', [('quanto.critic', 'request_review'),
                                        ('quanto.provider', 'diagnose_operations'),
                                        ('quanto.alpaca_data', 'acquire_calendar')])
def test_actual_unrelated_entry_names_denied(module, name):
    frame = SimpleNamespace(f_globals={'__name__': module}, f_code=SimpleNamespace(co_name=name))
    with pytest.raises(w.Refused):
        w.forbid_calls(frame, 'call', None)


def test_planning_budget_observation_is_separate_and_bound(invented):
    f = invented
    assert w.run(lambda: f.context) == 0
    observed = document(f.state / 'prelaunch-budget.json')
    assert observed['planning_only'] is True
    assert observed['required_micro_usd'] == 2_625_000
    assert observed['global_remaining_micro_usd'] == 20_000_000
    assert observed['purpose_remaining_micro_usd'] == 4_000_000
    assert observed['global_limit_micro_usd'] == 20_000_000
    assert observed['purpose_limit_micro_usd'] == 4_000_000
    entered = document(f.state / 'paid-call-entered.json')
    assert entered['prelaunch_budget_sha256'] == w.sha((f.state / 'prelaunch-budget.json').read_bytes())


def test_registration_result_digest_change_refuses_before_product(invented):
    f = invented
    f.context[5]['after'] = {'unexpected_generation': True}
    f.reg.load_product = lambda *a: pytest.fail('must refuse before product')
    assert w.run(lambda: f.context) == 1
    assert 'credential_checked' not in f.calls and 'workflow' not in f.calls


def test_atomic_read_snapshot_excludes_interleaved_committed_writer(tmp_path):
    """WAL deliberately permits a second connection to commit mid-observation."""
    from quanto import ledger
    path = tmp_path / 'invented-budget.sqlite'
    provider = SimpleNamespace(PURPOSE_LIMITS={'research': 4_000_000})
    with ledger.Journal(path) as observer, ledger.Journal(path) as writer:
        observer.connection.execute(
            'CREATE TABLE provider_allocations(day TEXT,purpose TEXT,amount INTEGER)')
        observer.append_event('invented_checkpoint', {'synthetic_fixture': True})
        assert observer.connection.execute('PRAGMA journal_mode=WAL').fetchone()[0] == 'wal'
        original = observer.budget_snapshot
        def interleaved(day):
            snapshot = original(day)  # Establishes the observer transaction's read snapshot.
            assert observer.connection.in_transaction
            writer.reserve('invented-competing-client', 1_000_000)
            writer.connection.execute('INSERT INTO provider_allocations VALUES (?,?,?)',
                                      (day, 'research', 1_000_000))
            assert not writer.connection.in_transaction
            return snapshot
        observer.budget_snapshot = interleaved
        observation = w.headroom(observer, provider, ledger)
        assert not observer.connection.in_transaction
        assert observation['global_remaining_micro_usd'] == 20_000_000
        assert observation['purpose_remaining_micro_usd'] == 4_000_000
        assert observation['purpose_allocation_max_rowid'] == 0
        assert observation['event_count'] == 1
        later = w.verify_budget_order(observer, observation, ledger)
        assert later['count'] == 2
        assert original(observation['day'])['remaining_micro_usd'] == 19_000_000
        assert observer.connection.execute('SELECT MAX(rowid) FROM provider_allocations').fetchone()[0] == 1


def test_headroom_rolls_back_before_failure_publication(invented):
    f = invented
    def refused_events():
        assert f.db.in_transaction
        raise ValueError('invented-corrupt-chain')
    f.journal.verify_events = refused_events
    assert w.run(lambda: f.context) == 1
    assert not f.db.in_transaction
    assert not (f.state / 'prelaunch-budget.json').exists()
    assert 'workflow' not in f.calls
    f.db.execute('BEGIN IMMEDIATE')
    f.db.rollback()


def test_headroom_refuses_caller_owned_transaction_without_rollback(invented):
    f = invented
    f.db.execute('BEGIN')
    with pytest.raises(w.Refused):
        w.headroom(f.journal, f.provider, f.ledger)
    assert f.db.in_transaction
    f.db.rollback()


def test_observation_refuses_midnight_rollover_and_rolls_back(invented, monkeypatch):
    from datetime import datetime, timedelta, timezone
    f = invented
    now = datetime.now(timezone.utc)
    moments = iter((now, now + timedelta(days=1)))
    monkeypatch.setattr(w, 'datetime', SimpleNamespace(now=lambda zone: next(moments)))
    with pytest.raises(w.Refused):
        w.headroom(f.journal, f.provider, f.ledger)
    assert not f.db.in_transaction


@pytest.mark.parametrize('count,head', [(41, 'd' * 64), (42, 'e' * 64), (43, 'e' * 64)])
def test_checkpoint_cannot_follow_or_replace_prelaunch(invented, count, head):
    f = invented
    observation = w.headroom(f.journal, f.provider, f.ledger)
    f.journal.verify_events = lambda: {'count': count, 'head': head}
    if count == 43:
        f.db.execute('CREATE TABLE events(id INTEGER,event_hash TEXT)')
        f.db.execute('INSERT INTO events VALUES (?,?)', (42, 'f' * 64))
    with pytest.raises(w.Refused):
        w.verify_budget_order(f.journal, observation, f.ledger)


def test_missing_purpose_table_binds_zero_prefix(invented):
    f = invented
    f.db.execute('DROP TABLE provider_allocations')
    observation = w.headroom(f.journal, f.provider, f.ledger)
    assert observation['purpose_allocation_max_rowid'] == 0
    assert observation['purpose_remaining_micro_usd'] == 4_000_000
    assert observation['event_count'] == 42
    assert observation['event_head_sha256'] == 'd' * 64


@pytest.mark.parametrize('name', ['owned.json', 'start.json'])
def test_missing_positive_ownership_cannot_consume_or_publish(invented, name):
    f = invented
    (f.state / name).unlink()
    before = {p.name: p.read_bytes() for p in f.state.iterdir()}
    assert w.run(lambda: f.context) == 1
    assert {p.name: p.read_bytes() for p in f.state.iterdir()} == before
    assert not f.calls


@pytest.mark.parametrize('name,field,value', [
    ('owned.json', 'pid', -1), ('owned.json', 'paid_launch_sha256', 'f' * 64),
    ('start.json', 'owned_sha256', 'f' * 64), ('start.json', 'parent_pid', -1)])
def test_wrong_positive_ownership_cannot_publish(invented, name, field, value):
    f = invented
    path = f.state / name
    record = document(path)
    record[field] = value
    path.write_bytes(w.canonical(record))
    assert w.run(lambda: f.context) == 1
    assert not (f.state / 'paid-consumed.json').exists()
    assert not (f.state / 'outcome.json').exists()
    assert not (f.state / 'terminal.json').exists()


def test_preexisting_parent_failure_prevents_consumption(invented):
    f = invented
    w.exclusive(f.state / 'failure.json', {'status': 'refused_or_uncertain'})
    assert w.run(lambda: f.context) == 1
    assert not (f.state / 'paid-consumed.json').exists()
    assert not (f.state / 'outcome.json').exists()
    assert not (f.state / 'terminal.json').exists()


def test_competing_consumption_loser_cannot_publish_for_winner(invented):
    f = invented
    winning = b'{"invented_winning_invocation":true}'
    (f.state / 'paid-consumed.json').write_bytes(winning)
    (f.state / 'paid-consumed.json').chmod(0o600)
    assert w.run(lambda: f.context) == 1
    assert (f.state / 'paid-consumed.json').read_bytes() == winning
    assert not (f.state / 'outcome.json').exists()
    assert not (f.state / 'terminal.json').exists()
    assert not (f.state / 'paid-before.json').exists()


def test_partial_marker_publisher_does_not_own_outcome(invented, monkeypatch):
    f = invented
    original = w.exclusive
    def interrupted(path, value):
        digest = original(path, value)
        if path.name == 'paid-consumed.json':
            raise OSError('invented-fsync-publication-failure')
        return digest
    monkeypatch.setattr(w, 'exclusive', interrupted)
    assert w.run(lambda: f.context) == 1
    assert (f.state / 'paid-consumed.json').exists()
    assert not (f.state / 'outcome.json').exists()
    assert not (f.state / 'terminal.json').exists()


def change_authority(kind, f, monkeypatch):
    if kind == 'parent':
        monkeypatch.setattr(w.os, 'getppid', lambda: 1)
    elif kind == 'wall':
        real_now = w.time.time()
        monkeypatch.setattr(w.time, 'time', lambda: real_now + 7300)
    elif kind == 'day':
        from datetime import datetime, timedelta, timezone
        next_day = datetime.now(timezone.utc) + timedelta(days=1)
        monkeypatch.setattr(w, 'datetime', SimpleNamespace(now=lambda zone: next_day))
    elif kind == 'failure':
        w.exclusive(f.state / 'failure.json', {'status': 'refused_or_uncertain'})
    else:
        raise AssertionError('unknown invented fault')


@pytest.mark.parametrize('fault', ['parent', 'wall', 'day', 'failure'])
def test_loss_after_entry_receipt_never_reaches_broker(invented, monkeypatch, fault):
    f = invented
    original = w.exclusive
    def changed_after_entry(path, value):
        digest = original(path, value)
        if path.name == 'paid-call-entered.json':
            change_authority(fault, f, monkeypatch)
        return digest
    monkeypatch.setattr(w, 'exclusive', changed_after_entry)
    assert w.run(lambda: f.context) == 1
    assert 'workflow' not in f.calls
    assert document(f.state / 'terminal.json')['status'] == 'refused_or_uncertain'


@pytest.mark.parametrize('module,name', [
    ('quanto.research_dispatch', '_authorize'), ('quanto.provider', '_send_research'),
    ('quanto.critic', 'local_key')])
@pytest.mark.parametrize('fault', ['parent', 'wall', 'day', 'failure'])
def test_live_guards_fire_before_each_sensitive_function_body(
        invented, monkeypatch, module, name, fault):
    f = invented
    reached = []
    namespace = {'__name__': module, 'reached': reached}
    exec(compile(f'def {name}():\n    reached.append(True)\n', '<invented-sensitive-boundary>', 'exec'),
         namespace)
    def workflow(*args):
        f.calls.append('broker_stub_entered')
        change_authority(fault, f, monkeypatch)
        namespace[name]()
        pytest.fail('invalid authority crossed sensitive boundary')
    f.broker.run_workflow = workflow
    assert w.run(lambda: f.context) == 1
    assert 'broker_stub_entered' in f.calls
    assert not reached
    assert document(f.state / 'outcome.json')['status'] == 'uncertain'


@pytest.mark.parametrize('fault', ['eof', 'wrong_owned_pid', 'expired_wall'])
def test_real_pipe_grant_failure_publishes_no_worker_evidence(invented, monkeypatch, fault):
    f = invented
    source = Path(__file__).with_name('supervise.py')
    spec = importlib.util.spec_from_file_location('invented_gate_supervisor', source)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    monkeypatch.setattr(supervisor, 'ROOT', f.context[0])
    monkeypatch.setattr(supervisor, 'STATE', f.state)
    if fault == 'wrong_owned_pid':
        path = f.state / 'owned.json'
        value = document(path)
        value['pid'] = -1
        path.write_bytes(w.canonical(value))
    elif fault == 'expired_wall':
        path = f.state / 'consumed.json'
        value = document(path)
        value['start_wall'] -= 7300
        path.write_bytes(w.canonical(value))
    reader, writer = w.os.pipe()
    if fault != 'eof':
        w.os.write(writer, b'G')
    w.os.close(writer)
    before = {p.name: p.read_bytes() for p in f.state.iterdir()}
    def granted_context():
        supervisor.await_grant('paid', reader)
        pytest.fail('bad grant unexpectedly accepted')
    assert w.run(granted_context) == 1
    assert {p.name: p.read_bytes() for p in f.state.iterdir()} == before
    with pytest.raises(OSError):
        w.os.fstat(reader)


def test_bootstrap_verifies_adjacent_supervisor_then_refuses_pipe_eof(invented, monkeypatch):
    f = invented
    source = Path(__file__).with_name('supervise.py').read_bytes()
    directory = f.context[0] / 'runtime/development-cycle-launch-v2-preparation'
    directory.mkdir()
    copied = directory / 'paid_worker.py'
    copied.write_bytes(Path(__file__).with_name('paid_worker.py').read_bytes())
    (directory / 'supervise.py').write_bytes(source)
    record = document(f.state / 'consumed.json')
    record['supervisor_sha256'] = w.sha(source)
    (f.state / 'consumed.json').write_bytes(w.canonical(record))
    reader, writer = w.os.pipe()
    w.os.close(writer)
    monkeypatch.setattr(w, 'ROOT', f.context[0])
    monkeypatch.setattr(w, 'STATE', f.state)
    monkeypatch.setattr(w, '__file__', str(copied))
    monkeypatch.setattr(w, 'environment_check', lambda: None)  # Independently exercised in 3.11.
    monkeypatch.setattr(w.sys, 'argv', [str(copied), '--gate-fd', str(reader)])
    before = {p.name: p.read_bytes() for p in f.state.iterdir()}
    assert w.run(w.bootstrap) == 1
    assert {p.name: p.read_bytes() for p in f.state.iterdir()} == before
    with pytest.raises(OSError):
        w.os.fstat(reader)

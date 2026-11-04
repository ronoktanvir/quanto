"""Invented-root rehearsals only; no actual account, data, controller or model calls."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRIPT = HERE / 'prepare_current_code.py'
spec = importlib.util.spec_from_file_location('registration_preparation', SCRIPT)
prep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'src'))


def private(path, raw):
    path.write_bytes(raw)
    path.chmod(0o600)


@pytest.fixture
def project():
    # Tests import existing PUBLIC invented-evidence builders. No actual runtime
    # artifact is read. All operations below use this fresh marked temporary root.
    from quanto.evaluation_registry import Supervisor
    from quanto.provenance import Provenance
    from quanto.admission import admit_dataset
    from quanto.study_suite import register_suite
    from test_admission import regular_way_fixture
    with tempfile.TemporaryDirectory(prefix='d008-registration-') as temp:
        base = Path(temp).resolve()
        base.chmod(0o700)
        private(base / 'fixture-marker', b'invented registration fixture\n')
        root = base / 'invented-project'
        root.mkdir(mode=0o700)
        (root / 'runtime').mkdir(mode=0o700)
        (root / 'data').mkdir(mode=0o700)
        (root / 'data/objects').mkdir(mode=0o700)
        (root / 'runtime/input').mkdir(mode=0o700)
        (root / 'runtime/current-code-registration').mkdir(mode=0o700)
        with Supervisor(root, synthetic=False).session():
            admission_request, revision_request = regular_way_fixture(root)
            admitted = admit_dataset(root, admission_request)
            assert admitted['status'] == 'success', admitted
            with Provenance(root) as store:
                revision_row = store.list_submissions(kind='policy_revision', status='success')[-1]
                revised = {'submission_id': revision_row['submission_id'],
                           'policy_revision_sha256': revision_row['details']['policy_revision_sha256']}
                frozen = revision_request['frozen_study']
            suite_request = {'members': [{
                'dataset_sha256': admission_request['dataset_sha256'],
                'admission_sha256': admitted['admission_sha256'], 'study_name': 'invented registration',
                'evaluation_start': frozen['evaluation_start'], 'evaluation_end': frozen['evaluation_end'],
                'specification': {key: frozen[key] for key in ('lookback', 'starting_cash',
                                  'entry_threshold', 'exit_threshold')} | {'cost_bps': cost}}
                for cost in (0, 10, 25)]}
            suited = register_suite(root, suite_request)
            assert suited['status'] == 'success', suited
            originals = {}
            with Provenance(root) as store:
                for phase, request, outcome in zip(prep.PHASES,
                        (revision_request, admission_request, suite_request), (revised, admitted, suited)):
                    path = root / 'runtime/input' / (phase + '.json')
                    raw = json.dumps(request, indent=2).encode()
                    private(path, raw)
                    row = store.get_submission(outcome['submission_id'])
                    originals[phase] = {'submission_id': row['submission_id'],
                        'artifact_sha256': outcome[prep.REFS[phase]],
                        'request_file': {'path': str(path), 'sha256': prep.sha(raw)},
                        'request_binding': 'embedded_semantics' if phase == 'admission' else 'retained_bytes',
                        'submission_request': {'sha256': row['request_sha256'], 'bytes': row['request_bytes'],
                                               'encoding': row['request_encoding']}}
        packet = {'version': 1, 'root': str(root), 'source_root': str(ROOT), 'attempt_id': 'invented-01',
                  'manifest_sha256': prep.sha((HERE / 'source-manifest.json').read_bytes()),
                  'controller_sha256': prep.sha(SCRIPT.read_bytes()),
                  'tests_sha256': prep.sha(Path(__file__).read_bytes()),
                  'preparation_critic_sha256': 'a' * 64, 'preflight_evidence_sha256': 'b' * 64,
                  'expected_state': prep.project_state(root, time.monotonic() + 30), 'originals': originals}
        path = base / 'packet.json'
        private(path, prep.canonical(packet))
        yield root, path, packet


def launch(path, *, seconds=120, hook=''):
    raw = path.read_bytes()
    # Literal source code is passed as an argument, never interpolated in shell.
    code = '''import importlib.util, json, sys
from pathlib import Path
p=Path(sys.argv[1]); s=importlib.util.spec_from_file_location('prep',p)
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
hook_text=sys.argv[5]
hook=None
if hook_text:
 namespace={"m":m,"Path":Path}; exec(hook_text,namespace); hook=namespace['hook']
try:
 result=m.run(Path(sys.argv[2]),sys.argv[3],fixture=True,work_seconds=float(sys.argv[4]),hook=hook)
 print(json.dumps({"status":result['status']}))
except BaseException as exc:
 print(json.dumps({"status":"unaccepted","reason":getattr(exc,'reason','unexpected_test_error')}))
 sys.exit(1)
'''
    return subprocess.run([str(prep.PYTHON), '-I', '-S', '-B', '-c', code, str(SCRIPT),
                           str(path), prep.sha(raw), str(seconds), hook], env={}, cwd='/',
                          capture_output=True, timeout=seconds + 15)


def attempt(root):
    return root / 'runtime/current-code-registration/invented-01'


def test_full_unchanged_registrations_and_fresh_identity(project):
    root, path, packet = project
    result = launch(path)
    if result.returncode:
        for failure in attempt(root).glob('*failure.json'):
            print(failure.name, failure.read_text())
    assert result.returncode == 0, (result.stdout, result.stderr,
        [(p.name, p.read_text()) for p in attempt(root).glob('*outcome.json')],
        [(p.name, p.read_text()) for p in attempt(root).glob('*failure.json')],
        [(p.name, p.read_text()) for p in attempt(root).glob('*stdout.bin')])
    final = json.loads((attempt(root) / 'result.json').read_text())
    assert len(final['phases']) == 3 and final['paid_launch_authorized'] is False
    assert all(value is False for value in final['limits'].values())
    requests = [json.loads((attempt(root) / (p + '-operation-intent.json')).read_text())
                for p in prep.PHASES]
    old = {p: json.loads(Path(packet['originals'][p]['request_file']['path']).read_text()) for p in prep.PHASES}
    assert json.loads(requests[0]['request_utf8']) == old['revision']
    assert json.loads(requests[1]['request_utf8']) == {**old['admission'],
        'policy_revision_sha256': final['mapping']['revision']['artifact_sha256']}
    assert json.loads(requests[2]['request_utf8']) == {'members': [{**m,
        'admission_sha256': final['mapping']['admission']['artifact_sha256']} for m in old['suite']['members']]}
    assert final['mapping']['revision']['artifact_sha256'] != packet['originals']['revision']['artifact_sha256']
    assert final['after']['control']['tables']['audit']['count'] > packet['expected_state']['control']['tables']['audit']['count']
    second = launch(path)
    assert second.returncode == 1 and b'already_consumed' in second.stdout
    assert json.loads((attempt(root) / 'result.json').read_text()) == final


@pytest.mark.parametrize('change', ['control_missing', 'research_missing', 'sidecar', 'mode', 'request',
                                  'source_pin', 'authority_pin', 'extra_field'])
def test_preflight_refusals_never_register(project, change):
    root, path, packet = project
    if change == 'control_missing':
        (root / 'runtime/access-control/control.sqlite').unlink()
    elif change == 'research_missing':
        (root / 'runtime/research.sqlite').unlink()
    elif change == 'sidecar':
        private(root / 'runtime/research.sqlite-wal', b'invented')
    elif change == 'mode':
        (root / 'runtime/research.sqlite').chmod(0o644)
    elif change == 'request':
        packet['originals']['revision']['request_file']['sha256'] = '0' * 64
    elif change == 'source_pin':
        packet['manifest_sha256'] = '0' * 64
    elif change == 'authority_pin':
        packet['expected_state']['control']['physical']['inode'] += 1
    else:
        packet['model'] = 'forbidden'
    private(path, prep.canonical(packet))
    result = launch(path)
    assert result.returncode == 1, result.stdout
    assert not list(attempt(root).glob('*operation-outcome.json'))
    if change == 'control_missing':
        assert not (root / 'runtime/access-control/control.sqlite').exists()


def test_same_byte_control_replacement_between_phases_stops(project):
    root, path, packet = project
    hook = '''def hook(phase,attempt):
 if phase == 'after_revision':
  control=attempt.parents[1]/'access-control/control.sqlite'
  raw=control.read_bytes(); alternate=control.with_suffix('.replacement')
  alternate.write_bytes(raw); alternate.chmod(0o600); alternate.replace(control)
'''
    result = launch(path, hook=hook)
    assert result.returncode == 1
    assert (attempt(root) / 'revision-result.json').exists()
    assert not (attempt(root) / 'admission-launch.json').exists()


def test_deadline_consumes_attempt(project):
    root, path, packet = project
    result = launch(path, seconds=.15, hook='''import time
def hook(phase,attempt):
 time.sleep(.25)
''')
    assert result.returncode == 1
    assert (root / 'runtime/current-code-registration/consumed.json').exists()
    assert not (attempt(root) / 'result.json').exists()
    assert launch(path).returncode == 1


def test_changed_original_after_revision_stops_before_admission(project):
    root, path, packet = project
    hook = '''def hook(phase,attempt):
 if phase == 'after_revision':
  target=attempt.parents[1]/'input/admission.json'
  target.write_bytes(target.read_bytes()+b' ')
'''
    result = launch(path, hook=hook)
    assert result.returncode == 1
    assert (attempt(root) / 'revision-result.json').exists()
    assert not (attempt(root) / 'admission-operation-intent.json').exists()
    assert not (attempt(root) / 'suite-launch.json').exists()


def test_outer_timeout_reaps_owned_child(project):
    root, path, packet = project
    # Start normal work with a deadline short enough to expire during the first
    # child. No deliberately slow provider, network or product override exists.
    result = launch(path, seconds=.35)
    assert result.returncode == 1
    failure = json.loads((attempt(root) / 'failure.json').read_text())
    assert failure['cleanup'].get('reaped') or failure['cleanup'].get('no_live_owned_child')
    owned = list(attempt(root).glob('*-owned.json'))
    assert owned
    for receipt in owned:
        with pytest.raises(ProcessLookupError):
            os.kill(json.loads(receipt.read_text())['pid'], 0)
    assert not (attempt(root) / 'suite-launch.json').exists()


def test_boundary_denies_network_credentials_and_execution(tmp_path):
    source, root, attempt_path = ROOT, tmp_path, tmp_path / 'attempt'
    monitor = prep.Boundary(source, root, attempt_path, [])
    with pytest.raises(prep.Refusal):
        monitor('socket.connect', ())
    with pytest.raises(prep.Refusal):
        monitor('subprocess.Popen', ())
    with pytest.raises(prep.Refusal):
        monitor('open', (str(ROOT / '.env'), 'r', os.O_RDONLY))
    with pytest.raises(prep.Refusal):
        monitor('sqlite3.connect', (str(root / 'runtime/research.sqlite'),))
    frame = type('Frame', (), {'f_globals': {'__name__': 'quanto.event_engine'},
                              'f_code': type('Code', (), {'co_name': 'run_event_backtest'})()})()
    with pytest.raises(prep.Refusal):
        prep.forbid_calls(frame, 'call', None)


def test_existing_only_guards_refuse_deleted_files(tmp_path):
    path = tmp_path / 'control.sqlite'
    private(path, b'invented')
    old = prep.physical(prep.fileinfo(path))
    guard = prep.ExistingOS(os, path, old)
    with pytest.raises(FileExistsError):
        guard.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    path.unlink()
    with pytest.raises(FileNotFoundError):
        guard.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with pytest.raises(FileNotFoundError):
        prep.ExistingSQLite(prep.sqlite3, path, old).connect(path)
    assert not path.exists()


def test_strict_json_and_fixture_boundary():
    with pytest.raises(prep.Refusal):
        prep.parse(b'{"x":1,"x":2}')
    with pytest.raises(prep.Refusal):
        prep.parse(b'{"x":NaN}')


def test_loaded_policy_and_helper_defaults_changes_are_detected():
    code = '''import importlib.util,json,sys
from pathlib import Path
p=Path(sys.argv[1]);s=importlib.util.spec_from_file_location('prep',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
manifest=json.loads(p.with_name('source-manifest.json').read_text())
m.load_product(m.ACTUAL_ROOT,manifest['files'])
assert m.loaded_identity()==manifest['loaded']
registry=sys.modules['quanto.evaluation_registry']
before=registry.ACCESS_POLICY_VERSION;registry.ACCESS_POLICY_VERSION='invented-altered-version'
assert m.loaded_identity()!=manifest['loaded'];registry.ACCESS_POLICY_VERSION=before
function=sys.modules['quanto.ledger'].Journal.__init__
old=function.__kwdefaults__;function.__kwdefaults__={**old,'daily_limit_micro_usd':1}
assert m.loaded_identity()!=manifest['loaded'];function.__kwdefaults__=old
assert m.loaded_identity()==manifest['loaded']
print('loaded mutation probes passed')
'''
    result = subprocess.run([str(prep.PYTHON), '-I', '-S', '-B', '-c', code, str(SCRIPT)],
                            env={}, cwd='/', capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('slow_stage', ['environment', 'packet', 'source'])
def test_initial_preflight_is_covered_by_real_alarm(monkeypatch, tmp_path, slow_stage):
    """Real SIGALRM interrupts the formerly unbounded initial preflight."""
    packet = b'{}'
    monkeypatch.setattr(prep, 'environment_check', lambda: None)
    monkeypatch.setattr(prep, 'readfile', lambda *a, **kw: packet)
    monkeypatch.setattr(prep, 'validate_packet', lambda *a: (tmp_path, tmp_path))
    monkeypatch.setattr(prep, 'read_manifest', lambda *a: {'files': {}})
    monkeypatch.setattr(prep, 'source_files', lambda *a: {})
    def stall(*args, **kwargs):
        time.sleep(.5)
        pytest.fail('preflight outlived its work alarm')
    target = {'environment': 'environment_check', 'packet': 'readfile', 'source': 'source_files'}[slow_stage]
    monkeypatch.setattr(prep, target, stall)
    started = time.monotonic()
    with pytest.raises(prep.Refusal, match='deadline'):
        prep.run(tmp_path / 'not-opened.json', prep.sha(packet), fixture=True, work_seconds=.05)
    assert time.monotonic() - started < .4
    assert not list(tmp_path.iterdir())


class Clock:
    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now


class Signals:
    SIGALRM, SIGINT, SIGTERM, ITIMER_REAL = 14, 2, 15, 0

    def __init__(self, clock):
        self.clock, self.arms = clock, []

    def getsignal(self, _):
        return None

    def signal(self, *args):
        pass

    def setitimer(self, _, seconds):
        self.arms.append((self.clock.now, seconds))


class OwnedChild:
    """Invented handle; never an OS PID that the tests signal or adopt."""
    pid = 123456789

    def __init__(self, clock, mode):
        self.clock, self.mode, self.calls, self.returncode = clock, mode, [], None

    def poll(self):
        self.calls.append(('poll', self.clock.now))
        return self.returncode

    def kill(self):
        self.calls.append(('kill', self.clock.now))
        if self.mode == 'kill_error':
            raise OSError('invented cleanup failure')
        self.clock.now += .25

    def wait(self, timeout):
        self.calls.append(('wait', timeout))
        if sum(call[0] == 'wait' for call in self.calls) == 1:
            self.clock.now = 1106.0 if self.mode == 'after_cleanup_deadline' else 1104.0
            raise prep.Refusal('deadline')  # Simulated late delivery of work alarm.
        if self.mode == 'wait_exhausted':
            self.clock.now = 1105.1
            raise subprocess.TimeoutExpired('invented-owned-child', timeout)
        self.clock.now += .25
        self.returncode = -9
        return self.returncode


@pytest.mark.parametrize('mode', ['late_but_observed', 'after_cleanup_deadline', 'wait_exhausted', 'kill_error'])
def test_late_alarm_cleanup_uses_absolute_remaining_time_once(project, monkeypatch, mode):
    """Exercise the real _run exception path with an invented Popen handle."""
    root, path, packet = project
    clock, child = Clock(), None
    signals = Signals(clock)
    child = OwnedChild(clock, mode)
    monkeypatch.setattr(prep, 'time', clock)
    monkeypatch.setattr(prep, 'signal', signals)
    monkeypatch.setattr(prep, 'environment_check', lambda: None)
    manifest = {'files': prep.source_files(ROOT)}
    monkeypatch.setattr(prep, 'read_manifest', lambda _: manifest)
    monkeypatch.setattr(prep.subprocess, 'Popen', lambda *a, **kw: child)
    real_reap, reap_calls = prep.reap, []
    def observed_reap(handle, deadline):
        reap_calls.append((handle, deadline))
        return real_reap(handle, deadline)
    monkeypatch.setattr(prep, 'reap', observed_reap)
    with pytest.raises(prep.Refusal) as caught:
        prep.run(path, prep.sha(path.read_bytes()), fixture=True, work_seconds=100)
    positive = [(at, seconds) for at, seconds in signals.arms if seconds > 0]
    assert positive[0] == (1000.0, 100.0)
    assert all(at + seconds <= 1105.0 for at, seconds in positive)
    waits = [value for call, value in child.calls if call == 'wait']
    assert waits[0] == 100.0
    if mode == 'after_cleanup_deadline':
        assert reap_calls == [] and len(waits) == 1
        assert caught.value.reason == 'cleanup_unobserved'
        assert not (attempt(root) / 'failure.json').exists()
    else:
        assert len(reap_calls) == 1 and reap_calls[0][1] == 1105.0
        assert positive[1] == (1104.0, 1.0)
        assert sum(call[0] == 'poll' for call in child.calls) == 1
        assert sum(call[0] == 'kill' for call in child.calls) == 1
        if mode == 'kill_error':
            assert len(waits) == 1
        else:
            assert len(waits) == 2 and waits[1] == .75
        if mode == 'late_but_observed':
            assert caught.value.reason == 'deadline'
            failure = json.loads((attempt(root) / 'failure.json').read_text())
            assert failure['cleanup']['reaped'] is True
        else:
            assert caught.value.reason == 'cleanup_unobserved'
    assert (attempt(root) / 'revision-owned.json').exists()
    assert not (attempt(root) / 'admission-launch.json').exists()


def test_cleanup_already_exhausted_never_polls_kills_or_waits(monkeypatch):
    clock = Clock()
    child = OwnedChild(clock, 'unused')
    monkeypatch.setattr(prep, 'time', clock)
    observed = prep.reap(child, clock.now)
    assert child.calls == []
    assert observed['reaped'] is False and observed['status'] == 'cleanup_unobserved'


def test_expired_alarm_is_not_clamped_to_new_grace(monkeypatch):
    clock = Clock()
    signals = Signals(clock)
    monkeypatch.setattr(prep, 'time', clock)
    monkeypatch.setattr(prep, 'signal', signals)
    with pytest.raises(prep.Refusal, match='deadline'):
        prep.arm_deadline(clock.now)
    assert signals.arms == []

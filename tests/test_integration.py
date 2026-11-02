import json
from pathlib import Path

import pytest

from quanto.cli import main, run_demo
from quanto.critic import MODEL, local_key, request_review
from quanto.ledger import Journal, LedgerError


def test_reproducible_demo_preserves_distinct_attempts(tmp_path):
    first, second = run_demo(tmp_path), run_demo(tmp_path)
    assert first['experiment'] == second['experiment']
    assert first['artifact_sha256'] == second['artifact_sha256']
    assert first['attempt_id'] != second['attempt_id']
    assert first['investment_evidence'] is False
    saved = json.loads(Path(first['artifact_path']).read_text())
    assert saved['evidence_kind'] == 'synthetic_fixture'
    assert saved['holdout_status'] == 'unprotected_not_implemented'
    with Journal(tmp_path/'runtime/research.sqlite') as ledger:
        assert ledger.overview()['attempts'] == 2
        assert ledger.verify_events()['count'] >= 5


def test_status_does_not_initialize_empty_journal(tmp_path, capsys):
    assert main(['--root', str(tmp_path), 'status']) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'not_initialized'
    assert not (tmp_path/'runtime/research.sqlite').exists()


def test_missing_key_does_not_call_provider_or_create_journal(tmp_path, monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    def forbidden(*args):
        pytest.fail('No provider call is permitted without credentials')
    with pytest.raises(LedgerError, match='not configured'):
        request_review(tmp_path, 'review', transport=forbidden)
    assert not (tmp_path/'runtime').exists()


def test_mocked_provider_cost_is_settled_and_metadata_saved(tmp_path, monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'unit-test-placeholder')
    def fake_transport(body, key):
        request = json.loads(body)
        assert key == 'unit-test-placeholder'
        assert request['model'] == MODEL
        assert 'tools' not in request
        return {'id':'unit-test-response', 'type':'message', 'model':MODEL, 'stop_reason':'end_turn',
                'usage':{'input_tokens':100, 'output_tokens':20},
                'content':[{'type':'text', 'text':'Synthetic mocked review; not an actual model response.'}]}
    report = request_review(tmp_path, 'Synthetic unit test packet', transport=fake_transport)
    assert report['cost_micro_usd'] == 800
    assert report['status'] == 'completed'
    assert Path(report['artifact_path']).exists()
    assert 'unit-test-placeholder' not in Path(report['artifact_path']).read_text()
    with Journal(tmp_path/'runtime/research.sqlite') as ledger:
        assert ledger.budget_snapshot()['committed_micro_usd'] == 800


def test_uncertain_provider_call_keeps_reservation_and_does_not_retry(tmp_path, monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'unit-test-placeholder')
    calls=[]
    def timeout(*args):
        calls.append(1)
        raise TimeoutError('Do not expose provider bodies or credentials')
    with pytest.raises(LedgerError, match='no automatic retry'):
        request_review(tmp_path, 'test', transport=timeout)
    assert len(calls) == 1
    with Journal(tmp_path/'runtime/research.sqlite') as ledger:
        budget=ledger.budget_snapshot()
        assert budget['uncertain_count'] == 1
        assert budget['committed_micro_usd'] > 0


def test_local_key_rejects_shared_permissions(tmp_path, monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    path=tmp_path/'.env'
    path.write_text('ANTHROPIC_API_KEY=unit-test-placeholder\n')
    path.chmod(0o644)
    with pytest.raises(LedgerError, match='private'):
        local_key(tmp_path)
    path.chmod(0o600)
    assert local_key(tmp_path) == 'unit-test-placeholder'


def test_authenticated_transport_never_follows_redirect(monkeypatch):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread
    from urllib.error import HTTPError
    import quanto.critic as critic

    received=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            self.send_response(302)
            self.send_header('Location', f'http://127.0.0.1:{self.server.server_port}/target')
            self.send_header('Content-Length', '0')
            self.end_headers()
        def do_GET(self):
            received.append(self.headers.get('x-api-key'))
            self.send_response(200)
            self.end_headers()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        monkeypatch.setattr(critic,'ENDPOINT',f'http://127.0.0.1:{server.server_port}/start')
        with pytest.raises(HTTPError):
            critic._send(b'{}','synthetic-placeholder')
        assert received == []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize('override', [{'model':'unapproved-model'}, {'content':None}, {'type':'error'}])
def test_unverified_provider_response_retains_full_hold(tmp_path, monkeypatch, override):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'unit-test-placeholder')
    def unexpected(*args):
        return {'type':'message','model':MODEL,'stop_reason':'end_turn',
                'usage':{'input_tokens':10,'output_tokens':1},
                'content':[{'type':'text','text':'Mocked content'}],**override}
    with pytest.raises(LedgerError, match='no automatic retry'):
        request_review(tmp_path,'test',transport=unexpected)
    with Journal(tmp_path/'runtime/research.sqlite') as ledger:
        budget=ledger.budget_snapshot()
        assert budget['uncertain_count'] == 1
        assert budget['settled_count'] == 0
        assert budget['committed_micro_usd'] > 100_000

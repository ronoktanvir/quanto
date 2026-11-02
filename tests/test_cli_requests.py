"""Operator boundary checks: invalid requests remain visible without leaking bodies."""
import json
import os
from pathlib import Path

import pytest

from quanto.cli import _request_text, main
from quanto.provenance import Provenance


def test_submission_query_does_not_initialize_empty_workspace(tmp_path, capsys):
    assert main(['--root', str(tmp_path), 'submissions', '--status', 'failed']) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'not_initialized'
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('command', ['acquire-bars', 'acquire-calendar', 'acquire-actions',
                                     'admit-dataset'])
def test_malformed_json_is_recorded_before_credentials_or_network(tmp_path, capsys, command):
    path = tmp_path / 'invalid.json'
    marker = 'synthetic-sensitive-request-content'
    path.write_text('{"unexpected":"' + marker + '",broken')
    assert main(['--root', str(tmp_path), command, '--request', str(path)]) == 1
    output = capsys.readouterr()
    assert marker not in output.out + output.err
    with Provenance(tmp_path) as store:
        rows = store.list_submissions(status='invalid')
        assert len(rows) == 1
        assert rows[0]['request_sha256']
        assert marker not in json.dumps(rows)
    assert marker.encode() not in (tmp_path / 'runtime/research.sqlite').read_bytes()


def test_request_reader_refuses_symlink_and_pipe_without_blocking(tmp_path):
    target = tmp_path / 'source.json'
    target.write_text('{}')
    link = tmp_path / 'linked.json'
    link.symlink_to(target)
    with pytest.raises(OSError):
        _request_text(link)
    fifo = tmp_path / 'pipe'
    os.mkfifo(fifo)
    with pytest.raises(ValueError):
        _request_text(fifo)


def test_request_reader_bounds_file_size_before_decoding(tmp_path):
    path = Path(tmp_path) / 'oversized.json'
    path.write_bytes(b'x' * (64 * 1024 + 1))
    with pytest.raises(ValueError):
        _request_text(path)


def test_unresolved_publication_is_not_a_success_exit(tmp_path, monkeypatch, capsys):
    path = tmp_path / 'request.json'
    path.write_text('{}')
    monkeypatch.setattr('quanto.alpaca_data.acquire_bars', lambda *args: {
        'status': 'pending', 'error': 'storage_unavailable',
    })
    assert main(['--root', str(tmp_path), 'acquire-bars', '--request', str(path)]) == 1
    assert json.loads(capsys.readouterr().out)['status'] == 'pending'

"""Synthetic source/issuer fixtures test controls; no real investment evidence."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from quanto.admission import admit_dataset, validate_admission, AdmissionError
from quanto.alpaca_data import acquire_bars, acquire_calendar, Credentials, HTTPResult
from quanto.alpaca_actions import acquire_actions
from quanto.explorer import register_dataset, run_submission, list_exposures
from quanto.ledger import canonical_json
from quanto.provenance import Provenance

CLOCK = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
DATES = ['2024-06-03', '2024-06-04', '2024-06-05', '2024-06-06', '2024-06-07',
         '2024-06-10', '2024-06-11', '2024-06-12', '2024-06-13', '2024-06-14']
MARKET = {"instrument_id": "us:fixture-issuer", "venue": "SIP", "currency": "USD",
          "session_timezone": "America/New_York"}
SPLIT = {"kind": "split", "event_id": "split1", "effective_date": "2024-06-10",
         "new_rate": "10", "old_rate": "1"}
DIVIDEND = {"kind": "cash_dividend", "event_id": "div1", "ex_date": "2024-06-11",
            "payable_date": "2024-06-28", "rate": "0.01", "currency": "USD",
            "share_basis": "ex_date_shares"}
ACTIONS = {"forward_splits": [{"id": "split1", "symbol": "FIX", "cusip": "fixture-cusip",
                                "process_date": "2024-06-10", "ex_date": "2024-06-10",
                                "new_rate": 10, "old_rate": 1}],
           "cash_dividends": [{"id": "div1", "symbol": "FIX", "cusip": "fixture-cusip",
                               "process_date": "2024-06-28", "ex_date": "2024-06-11",
                               "payable_date": "2024-06-28", "rate": 0.01,
                               "special": False, "foreign": False, "currency": "USD"}]}


def put(root, value):
    with Provenance(root) as store:
        return store.put_json(value)


def get(root, digest):
    with Provenance(root) as store:
        return store.read_json(digest)


def evidence(root, *, actions=None, dates=None, basis='raw', facts_mutate=None):
    """Run actual adapter code against explicit synthetic transports."""
    bar_rows = []
    for i, day in enumerate(DATES):
        close = 100 + i if i < 5 else 10 + i / 10
        bar_rows.append({"t": day + 'T04:00:00Z', "o": close, "c": close,
                         "l": close - 0.1, "h": close + 0.1, "v": 100})
    bodies = {"bars": {"symbol": "FIX", "bars": bar_rows, "next_page_token": None},
              "calendar": [{"date": day, "open": "09:30", "close": "16:00"} for day in (dates or DATES)],
              "actions": {"corporate_actions": deepcopy(ACTIONS if actions is None else actions),
                          "next_page_token": None}}
    requests = {"bars": {"symbol": "FIX", "start": DATES[0], "end": DATES[-1], "adjustment": basis},
                "calendar": {"start": DATES[0], "end": DATES[-1]},
                "actions": {"symbol": "FIX", "start": "2016-01-01", "end": CLOCK.date().isoformat()}}
    receipts, originals = {}, {}
    for kind, operation in (("bars", acquire_bars), ("calendar", acquire_calendar), ("actions", acquire_actions)):
        raw_request = canonical_json(requests[kind])
        with Provenance(root) as store:
            originals[kind] = store.put_bytes(raw_request.encode())
        raw = json.dumps(bodies[kind]).encode()
        outcome = operation(root, raw_request, transport=lambda *args, raw=raw: HTTPResult(200, raw),
                            clock=lambda: CLOCK, credentials=Credentials('fixture-key-123', 'fixture-secret-456'))
        assert outcome['status'] == 'success', outcome
        receipts[kind] = outcome
    registered = register_dataset(root, {"data_sha256": receipts['bars']['normalized_sha256'],
                                         "evidence_kind": "historical_market_data", "market": MARKET,
                                         "price_basis": basis})
    assert registered['status'] == 'success', registered
    with Provenance(root) as store:
        primary = store.put_bytes(b'SYNTHETIC issuer evidence fixture. Not an actual issuer publication.')
        terms = store.put_bytes(b'SYNTHETIC source-use text fixture. Not actual licensing evidence.')
    source = {"sha256": primary, "url": "https://issuer.example/fixture.pdf",
              "title": "Synthetic issuer fixture", "locator": "page 1"}
    judgment = {"source_sha256": primary, "locator": "page 1", "judgment": "Synthetic attributed test extraction."}
    facts = {"schema_version": 1, "kind": "attributed_primary_facts", "reviewer": "fixture reviewer",
             "reviewed_at": CLOCK.isoformat(), "sources": [source],
             "identity": {**judgment, "symbol": "FIX", "instrument_id": MARKET['instrument_id'],
                          "currency": "USD", "issuer_name": "Synthetic fixture issuer",
                          "continuity_start": DATES[0], "continuity_end": DATES[-1]},
             "coverage": {**judgment, "start": DATES[0], "end": DATES[-1],
                          "known_events": [SPLIT, DIVIDEND]},
             "events": [{**judgment, "provider_id": "split1", "event": SPLIT},
                        {**judgment, "provider_id": "div1", "event": DIVIDEND,
                         "provider_rate_basis": "ex_date_shares"}]}
    if facts_mutate:
        facts_mutate(facts)
    usage = {"schema_version": 1, "kind": "source_use_review", "reviewer": "fixture reviewer",
             "reviewed_at": CLOCK.isoformat(), "purpose": "private_own_account_research",
             "public_distribution": False, "external_model_transmission": False,
             "sources": [{**source, "sha256": terms, "title": "Synthetic use fixture"}],
             "interpretation": "Synthetic judgment for software testing only.",
             "unresolved": ["account_and_exchange_terms_not_certified"]}
    return {"dataset_sha256": registered['manifest_sha256'],
            **{kind + '_receipt_sha256': outcome['receipt_sha256'] for kind, outcome in receipts.items()},
            "submitted_requests": originals, "primary_facts_sha256": put(root, facts),
            "usage_review_sha256": put(root, usage)}


def study(request, admission):
    return {"dataset_sha256": request['dataset_sha256'], "admission_sha256": admission,
            "study_name": "Synthetic transport admission software fixture", "evaluation_start": DATES[2],
            "evaluation_end": DATES[-1], "specification": {"lookback": 2, "cost_bps": 10}}


def test_historical_success_replay_and_original_inspection_only(tmp_path):
    request = evidence(tmp_path)
    admitted = admit_dataset(tmp_path, request)
    assert admitted['status'] == 'success', admitted
    assert get(tmp_path, request['dataset_sha256'])['admission_status'] == 'inspection_only'
    with Provenance(tmp_path) as store:
        verified = validate_admission(store, admitted['admission_sha256'], request['dataset_sha256'])
    assert verified['actions'] == [SPLIT, DIVIDEND]
    result = run_submission(tmp_path, study(request, admitted['admission_sha256']))
    assert result['status'] == 'success', result
    second = run_submission(tmp_path, study(request, admitted['admission_sha256']))
    assert result['artifact_sha256'] == second['artifact_sha256']
    assert result['fingerprint'] == second['fingerprint']
    assert result['evidence_kind'] == 'historical_market_data'
    artifact = get(tmp_path, result['artifact_sha256'])
    assert artifact['engine_report']['evidence_kind'] == 'historical_market_data'
    assert artifact['engine_report']['strategy']['ending_receivables'] != '0'
    assert all(x['coverage_start'] == DATES[0] and x['coverage_end'] == DATES[-1]
               for x in list_exposures(tmp_path, MARKET, DATES[0], DATES[-1]))
    with Provenance(tmp_path) as store:
        assert store.journal.verify_events()['count'] > 0
        attempt = store.journal.connection.execute('SELECT result FROM outcomes LIMIT 1').fetchone()
        assert json.loads(attempt[0])['evidence_kind'] == 'historical_market_data'


def test_malformed_request_recorded_before_validation(tmp_path):
    result = admit_dataset(tmp_path, '{"a":')
    assert result['status'] == 'invalid'
    with Provenance(tmp_path) as store:
        assert store.get_submission(result['submission_id'])['status'] == 'invalid'


@pytest.mark.parametrize('change,code', [
    ({'new_rate': 0}, 'invalid_action_rate'),
    ({'ex_date': None}, 'invalid_date'),
    ({'symbol': 'OTHER'}, 'action_identity_mismatch'),
    ({'new_symbol': 'OTHER'}, 'action_identity_mismatch'),
    ({'ex_date': '2024-06-09'}, 'action_date_not_session'),
])
def test_invalid_split_evidence_refused(tmp_path, change, code):
    actions = deepcopy(ACTIONS)
    actions['forward_splits'][0].update(change)
    outcome = admit_dataset(tmp_path, evidence(tmp_path, actions=actions))
    assert outcome['status'] == 'invalid'
    assert outcome['error_code'] == code


@pytest.mark.parametrize('change,code', [
    ({'currency': 'EUR'}, 'unresolved_dividend_currency'),
    ({'rate': 0.1}, 'issuer_dividend_rate_conflict'),
    ({'payable_date': None}, 'invalid_date'),
    ({'payable_date': '2024-06-10'}, 'invalid_dividend_dates'),
    ({'special': True}, 'unsupported_dividend_terms'),
    ({'special': None}, 'unsupported_dividend_terms'),
    ({'foreign': True}, 'unsupported_dividend_terms'),
    ({'sub_type': 'return_of_capital'}, 'unsupported_dividend_terms'),
    ({'due_bill_on_date': '2024-06-11'}, 'unsupported_dividend_terms'),
])
def test_invalid_dividend_terms_refused(tmp_path, change, code):
    actions = deepcopy(ACTIONS)
    actions['cash_dividends'][0].update(change)
    outcome = admit_dataset(tmp_path, evidence(tmp_path, actions=actions))
    assert outcome['error_code'] == code


def test_primary_bound_rate_conversion_supported(tmp_path):
    actions = deepcopy(ACTIONS)
    actions['cash_dividends'][0]['rate'] = 0.1
    def annotate(facts):
        facts['events'][1].update(provider_rate_basis='pre_split_shares', conversion_split_event_id='split1')
    request = evidence(tmp_path, actions=actions, facts_mutate=annotate)
    assert admit_dataset(tmp_path, request)['status'] == 'success'


def test_unknown_currency_needs_primary_usd_judgment(tmp_path):
    actions = deepcopy(ACTIONS)
    actions['cash_dividends'][0]['currency'] = ''
    request = evidence(tmp_path, actions=actions)
    assert admit_dataset(tmp_path, request)['status'] == 'success'
    facts = get(tmp_path, request['primary_facts_sha256'])
    facts['events'][1]['event']['currency'] = ''
    request['primary_facts_sha256'] = put(tmp_path, facts)
    assert admit_dataset(tmp_path, request)['error_code'] == 'unresolved_dividend_currency'


def test_exact_duplicate_preserves_occurrences_but_counts_once(tmp_path):
    actions = deepcopy(ACTIONS)
    actions['forward_splits'].append(deepcopy(actions['forward_splits'][0]))
    request = evidence(tmp_path, actions=actions)
    outcome = admit_dataset(tmp_path, request)
    assert outcome['status'] == 'success', outcome
    receipt = get(tmp_path, request['actions_receipt_sha256'])
    assert len(get(tmp_path, receipt['normalized_sha256'])['records']) == 3
    assert len(get(tmp_path, outcome['admission_sha256'])['actions']) == 2


def test_conflicting_duplicate_is_never_selected(tmp_path):
    actions = deepcopy(ACTIONS)
    duplicate = deepcopy(actions['forward_splits'][0])
    duplicate['new_rate'] = 2
    actions['forward_splits'].append(duplicate)
    assert admit_dataset(tmp_path, evidence(tmp_path, actions=actions))['error_code'] == 'conflicting_same_id_actions'


def test_multiple_provider_ids_same_economic_event_reject(tmp_path):
    actions = deepcopy(ACTIONS)
    duplicate = deepcopy(actions['forward_splits'][0])
    duplicate['id'] = 'split2'
    actions['forward_splits'].append(duplicate)
    def annotate(facts):
        copy = deepcopy(facts['events'][0])
        copy['provider_id'] = copy['event']['event_id'] = 'split2'
        facts['events'].append(copy)
    assert admit_dataset(tmp_path, evidence(tmp_path, actions=actions, facts_mutate=annotate))['error_code'] == 'ambiguous_multiple_ids_same_event'


@pytest.mark.parametrize('category,record,code', [
    ('unknown_kind', {'id': 'u', 'ex_date': '2020-01-01'}, 'unknown_action_category'),
    ('name_changes', {'id': 'u', 'ex_date': '2020-01-01'}, 'identity_change_unresolved'),
    ('stock_dividends', {'id': 'u', 'symbol': 'FIX', 'ex_date': None}, 'invalid_date'),
    ('stock_dividends', {'id': 'u', 'symbol': 'FIX', 'ex_date': DATES[1]}, 'unsupported_relevant_action'),
])
def test_uncertain_or_unsupported_events_reject(tmp_path, category, record, code):
    actions = deepcopy(ACTIONS)
    actions[category] = [record]
    assert admit_dataset(tmp_path, evidence(tmp_path, actions=actions))['error_code'] == code


def test_known_outside_interval_unsupported_ex_event_can_be_excluded(tmp_path):
    actions = deepcopy(ACTIONS)
    actions['stock_dividends'] = [{'id': 'old', 'symbol': 'FIX', 'ex_date': '2020-01-01'}]
    assert admit_dataset(tmp_path, evidence(tmp_path, actions=actions))['status'] == 'success'


def test_empty_action_response_does_not_replace_known_issuer_events(tmp_path):
    assert admit_dataset(tmp_path, evidence(tmp_path, actions={}))['error_code'] == 'unmatched_primary_events'


def test_calendar_must_match_full_acquired_dataset(tmp_path):
    request = evidence(tmp_path, dates=DATES[1:])
    assert admit_dataset(tmp_path, request)['error_code'] == 'calendar_session_mismatch'


def test_adjusted_dataset_is_not_admissible(tmp_path):
    request = evidence(tmp_path, basis='all')
    assert admit_dataset(tmp_path, request)['error_code'] == 'historical_raw_dataset_required'


@pytest.mark.parametrize('field', ['bars_receipt_sha256', 'calendar_receipt_sha256', 'actions_receipt_sha256'])
def test_receipt_needs_matching_successful_submission(tmp_path, field):
    request = evidence(tmp_path)
    receipt = get(tmp_path, request[field])
    receipt['submission_id'] = get(tmp_path, request['actions_receipt_sha256'])['submission_id']
    receipt['extra'] = 'replaced bytes'
    request[field] = put(tmp_path, receipt)
    assert admit_dataset(tmp_path, request)['error_code'] == 'receipt_submission_mismatch'


def test_original_submission_request_bytes_must_match(tmp_path):
    request = evidence(tmp_path)
    with Provenance(tmp_path) as store:
        request['submitted_requests']['bars'] = store.put_bytes(b'{}')
    assert admit_dataset(tmp_path, request)['error_code'] == 'receipt_submission_mismatch'


@pytest.mark.parametrize('mode', ['corrupt', 'tombstone'])
def test_every_admission_dependency_rechecked_on_run(tmp_path, mode):
    request = evidence(tmp_path)
    admission = admit_dataset(tmp_path, request)
    artifact = get(tmp_path, admission['admission_sha256'])
    primary = get(tmp_path, request['primary_facts_sha256'])['sources'][0]['sha256']
    assert primary in artifact['artifact_refs']
    if mode == 'corrupt':
        (tmp_path / 'data' / 'objects' / f'{primary}.bin').write_bytes(b'corrupt')
    else:
        with Provenance(tmp_path) as store:
            store.tombstone(primary, 'invalid_artifact')
    denied = run_submission(tmp_path, study(request, admission['admission_sha256']))
    assert denied['status'] == 'invalid'
    assert denied['error_code'] == 'artifact_or_storage_unavailable'


def test_policy_change_requires_readmission(tmp_path, monkeypatch):
    from quanto import event_engine
    request = evidence(tmp_path)
    admitted = admit_dataset(tmp_path, request)
    original = event_engine.policy_identity
    monkeypatch.setattr(event_engine, 'policy_identity', lambda: {**original(), 'changed': True})
    with Provenance(tmp_path) as store:
        with pytest.raises(AdmissionError, match='admission_dependencies_changed'):
            validate_admission(store, admitted['admission_sha256'], request['dataset_sha256'])


def test_unregistered_admission_cannot_be_fabricated(tmp_path):
    from quanto.admission import _verify
    request = evidence(tmp_path)
    with Provenance(tmp_path) as store:
        artifact = store.put_json(_verify(store, request))
        with pytest.raises(AdmissionError, match='admission_not_registered'):
            validate_admission(store, artifact, request['dataset_sha256'])


def replace_receipt(root, request, kind, change):
    """Construct an intentionally inconsistent receipt through public provenance APIs."""
    with Provenance(root) as store:
        old = store.read_json(request[kind + '_receipt_sha256'])
        raw = store.read_bytes(request['submitted_requests'][kind]).decode()
        submission = store.begin('alpaca_' + kind, raw)
        old['submission_id'] = submission
        change(store, old)
        digest = store.put_json(old)
        refs = {digest, old['normalized_sha256'], old['request_sha256']}
        refs.update(page['raw_sha256'] for page in old['pages'])
        store.finish(submission, 'success', {'receipt_sha256': digest, 'artifact_refs': sorted(refs)})
        request[kind + '_receipt_sha256'] = digest


def test_normalized_action_omission_detected_by_source_replay(tmp_path):
    request = evidence(tmp_path)
    def omit(store, receipt):
        normalized = store.read_json(receipt['normalized_sha256'])
        normalized['records'] = normalized['records'][:1]
        receipt['normalized_sha256'] = store.put_json(normalized)
        receipt['row_count'] = 1
    replace_receipt(tmp_path, request, 'actions', omit)
    assert admit_dataset(tmp_path, request)['error_code'] == 'source_replay_mismatch'


@pytest.mark.parametrize('change,code', [
    ('page_cap', 'request_parameters_mismatch'),
    ('incomplete', 'acquisition_incomplete'),
    ('http_status', 'page_request_mismatch'),
    ('page_bytes', 'acquisition_cap_exceeded'),
    ('normalized_complete', 'source_coverage_mismatch'),
    ('query_types', 'page_request_mismatch'),
    ('next_token', 'acquisition_incomplete'),
])
def test_claimed_success_cannot_bypass_acquisition_contract(tmp_path, change, code):
    request = evidence(tmp_path)
    def mutate(store, receipt):
        if change == 'page_cap':
            prepared = store.read_json(receipt['request_sha256'])
            prepared['max_pages'] = 100
            receipt['request_sha256'] = store.put_json(prepared)
        elif change == 'incomplete':
            receipt['pagination_complete'] = False
        elif change == 'http_status':
            receipt['pages'][0]['http_status'] = 403
        elif change == 'page_bytes':
            receipt['pages'][0]['bytes'] += 1
        elif change == 'normalized_complete':
            normalized = store.read_json(receipt['normalized_sha256'])
            normalized['coverage']['pagination_complete'] = False
            receipt['normalized_sha256'] = store.put_json(normalized)
        elif change == 'query_types':
            receipt['pages'][0]['url'] += '&types=cash_dividend'
        else:
            raw = store.read_json(receipt['pages'][0]['raw_sha256'])
            raw['next_page_token'] = 'more'
            digest = store.put_json(raw)
            receipt['pages'][0]['raw_sha256'] = digest
            receipt['pages'][0]['bytes'] = len(store.read_bytes(digest))
    replace_receipt(tmp_path, request, 'actions', mutate)
    assert admit_dataset(tmp_path, request)['error_code'] == code


@pytest.mark.parametrize('target', ['raw', 'normalized', 'prepared', 'submitted', 'facts', 'usage', 'dataset', 'bars'])
def test_admission_rejects_corrupt_dependency_bytes(tmp_path, target):
    request = evidence(tmp_path)
    receipt = get(tmp_path, request['actions_receipt_sha256'])
    dataset = get(tmp_path, request['dataset_sha256'])
    digest = {'raw': receipt['pages'][0]['raw_sha256'], 'normalized': receipt['normalized_sha256'],
              'prepared': receipt['request_sha256'], 'submitted': request['submitted_requests']['actions'],
              'facts': request['primary_facts_sha256'], 'usage': request['usage_review_sha256'],
              'dataset': request['dataset_sha256'], 'bars': dataset['bars_sha256']}[target]
    (tmp_path / 'data' / 'objects' / f'{digest}.bin').write_bytes(b'changed')
    assert admit_dataset(tmp_path, request)['error_code'] == 'artifact_or_storage_unavailable'


def test_public_source_receipt_is_bound_and_rechecked(tmp_path):
    request = evidence(tmp_path)
    facts = get(tmp_path, request['primary_facts_sha256'])
    source = facts['sources'][0]
    with Provenance(tmp_path) as store:
        submission = store.begin('public_source_observation', {'url': source['url']})
        receipt = store.put_json({'kind': 'public_source_receipt', 'source_sha256': source['sha256'],
                                  'url': source['url'], 'submission_id': submission})
        store.finish(submission, 'success', {'receipt_sha256': receipt,
                                             'artifact_refs': [source['sha256'], receipt]})
    source['receipt_sha256'] = receipt
    request['primary_facts_sha256'] = put(tmp_path, facts)
    result = admit_dataset(tmp_path, request)
    assert result['status'] == 'success', result
    assert receipt in get(tmp_path, result['admission_sha256'])['artifact_refs']
    with Provenance(tmp_path) as store:
        store.tombstone(receipt, 'invalid_artifact')
    assert run_submission(tmp_path, study(request, result['admission_sha256']))['error_code'] == 'artifact_or_storage_unavailable'


def test_wrong_public_source_url_rejects(tmp_path):
    request = evidence(tmp_path)
    facts = get(tmp_path, request['primary_facts_sha256'])
    source = facts['sources'][0]
    source['receipt_sha256'] = put(tmp_path, {'kind': 'public_source_receipt',
                                            'source_sha256': source['sha256'], 'url': 'https://other.example/'})
    request['primary_facts_sha256'] = put(tmp_path, facts)
    assert admit_dataset(tmp_path, request)['error_code'] == 'public_source_receipt_mismatch'


def test_conflicting_security_identifier_rejects(tmp_path):
    actions = deepcopy(ACTIONS)
    actions['cash_dividends'][0]['cusip'] = 'different-security'
    assert admit_dataset(tmp_path, evidence(tmp_path, actions=actions))['error_code'] == 'action_security_identifier_conflict'


def test_historical_failed_attempt_keeps_evidence_kind(tmp_path, monkeypatch):
    from quanto import explorer
    def crash(*args, **kwargs):
        raise RuntimeError('fixture')
    monkeypatch.setattr(explorer, 'run_event_backtest', crash)
    request = evidence(tmp_path)
    admitted = admit_dataset(tmp_path, request)
    result = run_submission(tmp_path, study(request, admitted['admission_sha256']))
    assert result['status'] == 'failed'
    assert result['evidence_kind'] == 'historical_market_data'
    with Provenance(tmp_path) as store:
        row = store.journal.connection.execute('SELECT result FROM outcomes').fetchone()
        assert json.loads(row[0])['evidence_kind'] == 'historical_market_data'


@pytest.mark.parametrize('identifier', ['isin', 'cusip'])
def test_conflicting_provider_identifiers_reject(tmp_path, identifier):
    actions = deepcopy(ACTIONS)
    actions['forward_splits'][0][identifier] = 'first-security'
    actions['cash_dividends'][0][identifier] = 'second-security'
    assert admit_dataset(tmp_path, evidence(tmp_path, actions=actions))['error_code'] == 'action_security_identifier_conflict'


def test_reverse_split_old_new_isin_conflict_rejects(tmp_path):
    actions = deepcopy(ACTIONS)
    split = actions.pop('forward_splits')[0]
    split.update(new_rate=1, old_rate=2, old_isin='first-security', new_isin='second-security')
    actions['reverse_splits'] = [split]
    assert admit_dataset(tmp_path, evidence(tmp_path, actions=actions))['error_code'] == 'action_security_identifier_conflict'


@pytest.mark.parametrize('target', ['admission_helper', 'admission_rules', 'bars_helper', 'actions_helper', 'provider_constant'])
def test_admission_identity_binds_loaded_validation_and_replay(tmp_path, monkeypatch, target):
    from quanto import admission, alpaca_data, alpaca_actions, explorer
    request = evidence(tmp_path)
    admitted = admit_dataset(tmp_path, request)
    before = explorer._code_identity()
    if target == 'admission_helper':
        monkeypatch.setattr(admission, '_need', lambda *args: None)
    elif target == 'admission_rules':
        monkeypatch.setattr(admission, 'RULES', {**admission.RULES, 'version': 'changed'})
    elif target == 'bars_helper':
        original = alpaca_data._bar
        monkeypatch.setattr(alpaca_data, '_bar', lambda *args: original(*args))
    elif target == 'actions_helper':
        original = alpaca_actions._page
        monkeypatch.setattr(alpaca_actions, '_page', lambda *args: original(*args))
    else:
        monkeypatch.setattr(alpaca_data, 'ERRORS', {*alpaca_data.ERRORS, 'changed'})
    assert explorer._code_identity() != before
    with Provenance(tmp_path) as store:
        with pytest.raises(AdmissionError, match='admission_dependencies_changed'):
            validate_admission(store, admitted['admission_sha256'], request['dataset_sha256'])


def test_nonquanto_lambdas_and_imported_helper_aliases_are_bound(monkeypatch):
    from quanto import explorer, event_engine
    monkeypatch.setattr(event_engine, '_target', lambda *args: True)
    before = explorer._code_identity()
    monkeypatch.setattr(event_engine, '_target', lambda *args: False)
    assert explorer._code_identity() != before
    before = explorer._code_identity()
    monkeypatch.setattr(event_engine, '_identity', lambda *args: 'replaced-imported-alias')
    assert explorer._code_identity() != before


@pytest.mark.parametrize('exception', ['provenance', 'sqlite', 'os'])
def test_admission_persistent_finish_failure_returns_safe_pending(tmp_path, monkeypatch, exception):
    import sqlite3
    from quanto.provenance import ProvenanceError
    request = evidence(tmp_path)
    failure = {'provenance': ProvenanceError, 'sqlite': sqlite3.OperationalError, 'os': OSError}[exception]
    def cannot_finish(*args, **kwargs):
        raise failure('private details must not escape')
    monkeypatch.setattr(Provenance, 'finish', cannot_finish)
    outcome = admit_dataset(tmp_path, request)
    assert outcome['status'] == 'pending'
    assert outcome['error_code'] == 'publication_interrupted'
    assert 'private details' not in str(outcome)
    with Provenance(tmp_path) as store:
        assert store.get_submission(outcome['submission_id'])['status'] == 'pending'


MERGER = {"id": "old-merger", "acquirer_symbol": "FIX", "acquirer_cusip": "fixture-cusip",
          "acquiree_symbol": "OLD", "acquiree_cusip": "other-cusip", "rate": 1.25,
          "effective_date": "2020-02-03", "process_date": "2020-02-04"}


def merger_evidence(root, *, record=None, category='cash_mergers', duplicates=(), annotate=None,
                    actions_mutate=None):
    actions = deepcopy(ACTIONS)
    actions[category] = [deepcopy(MERGER if record is None else record), *deepcopy(duplicates)]
    if actions_mutate:
        actions_mutate(actions)
    request = evidence(root, actions=actions)
    receipt = get(root, request['actions_receipt_sha256'])
    normalized = get(root, receipt['normalized_sha256'])
    record = next(row['record'] for row in normalized['records'] if row['category'] == category)
    from quanto.ledger import hash_json
    facts = get(root, request['primary_facts_sha256'])
    with Provenance(root) as store:
        completed = store.put_bytes(b'SYNTHETIC separate issuer completion publication fixture.')
    facts['sources'].append({'sha256': completed, 'url': 'https://issuer.example/completion',
                             'title': 'Synthetic acquisition completion', 'locator': 'paragraph 1'})
    source = facts['sources'][0]['sha256']
    facts['excluded_actions'] = [{
        'provider_id': record['id'], 'category': category, 'record_sha256': hash_json(record),
        'effective_date': record.get('effective_date'),
        'acquirer': {key: record.get('acquirer_' + key) for key in ('symbol', 'cusip', 'isin')},
        'acquiree': {key: record.get('acquiree_' + key) for key in ('symbol', 'cusip', 'isin')},
        'source_sha256': source, 'locator': 'page 1',
        'judgment': 'Synthetic exact participant and historical acquisition role extraction.',
        'completion': {'date': '2020-02-03', 'source_sha256': completed, 'locator': 'paragraph 1',
                       'judgment': 'Synthetic completion and no studied share conversion or claim judgment.',
                       'no_studied_share_conversion': True, 'no_outstanding_studied_entitlement': True}}]
    if annotate:
        annotate(facts)
    request['primary_facts_sha256'] = put(root, facts)
    return request


def test_completed_pre_window_cash_merger_exclusion_keeps_exact_evidence(tmp_path):
    request = merger_evidence(tmp_path, duplicates=[MERGER])
    outcome = admit_dataset(tmp_path, request)
    assert outcome['status'] == 'success', outcome
    admission = get(tmp_path, outcome['admission_sha256'])
    assert admission['rules']['version'] == 'D006-admission-v1.1'
    assert admission['actions'] == [SPLIT, DIVIDEND]
    assert len(admission['excluded_actions']) == 1
    exclusion = admission['excluded_actions'][0]
    assert exclusion['reason'] == 'completed_pre_window_acquirer_cash_merger'
    assert len(exclusion['occurrences']) == 2
    assert [x['index'] for x in exclusion['occurrences']] == [0, 1]
    assert all(x['raw_sha256'] in admission['artifact_refs'] for x in exclusion['occurrences'])
    assert exclusion['record_sha256'] == exclusion['annotation']['record_sha256']
    assert exclusion['annotation']['completion']['source_sha256'] in admission['artifact_refs']
    assert run_submission(tmp_path, study(request, outcome['admission_sha256']))['status'] == 'success'
    with Provenance(tmp_path) as store:
        assert validate_admission(store, outcome['admission_sha256'], request['dataset_sha256']) == admission


@pytest.mark.parametrize('changes,code', [
    ({'effective_date': None}, 'invalid_date'),
    ({'effective_date': ''}, 'invalid_date'),
    ({'effective_date': 'not-a-date'}, 'invalid_date'),
    ({'effective_date': DATES[0]}, 'excluded_event_not_before_acquired_interval'),
    ({'effective_date': DATES[1]}, 'excluded_event_not_before_acquired_interval'),
    ({'effective_date': '2030-01-01'}, 'excluded_event_not_before_acquired_interval'),
    ({'process_date': None}, 'invalid_date'),
    ({'acquirer_symbol': 'OTHER', 'acquiree_symbol': 'FIX'}, 'excluded_merger_role_mismatch'),
    ({'acquirer_symbol': 'FIX', 'acquiree_symbol': 'FIX'}, 'excluded_merger_role_mismatch'),
    ({'acquirer_symbol': None}, 'excluded_merger_identity_unresolved'),
    ({'acquiree_symbol': ''}, 'excluded_merger_identity_unresolved'),
    ({'acquiree_cusip': 'fixture-cusip'}, 'excluded_acquiree_identifier_conflict'),
    ({'acquiree_cusip': None}, 'excluded_acquiree_identity_unresolved'),
    ({'acquiree_cusip': ''}, 'excluded_merger_identity_unresolved'),
    ({'acquirer_cusip': 'different'}, 'excluded_acquirer_identifier_unresolved'),
    ({'acquirer_cusip': None}, 'excluded_acquirer_identifier_unresolved'),
    ({'acquirer_isin': 'UNRECONCILED'}, 'excluded_acquirer_identifier_unresolved'),
    ({'payable_date': DATES[0]}, 'unresolved_merger_payment'),
    ({'payable_date': DATES[1]}, 'unresolved_merger_payment'),
    ({'payable_date': '2019-01-01'}, 'unresolved_merger_payment'),
    ({'payable_date': '2020-02-04'}, 'unresolved_merger_payment'),
    ({'payable_date': 'unknown'}, 'invalid_date'),
    ({'new_rate': 1}, 'unsupported_cash_merger_fields'),
    ({'stock_rate': 1}, 'unsupported_cash_merger_fields'),
    ({'new_symbol': 'OTHER'}, 'unsupported_cash_merger_fields'),
    ({'rate': 0}, 'invalid_action_rate'),
    ({'rate': None}, 'invalid_action_rate'),
    ({'currency': 123}, 'invalid_excluded_merger_currency'),
    ({'currency': {}}, 'invalid_excluded_merger_currency'),
])
def test_cash_merger_exclusion_refuses_ambiguous_or_relevant_record(tmp_path, changes, code):
    request = merger_evidence(tmp_path, record={**MERGER, **changes})
    result = admit_dataset(tmp_path, request)
    assert result['status'] == 'invalid', result
    assert result['error_code'] == code


@pytest.mark.parametrize('category', ['stock_mergers', 'stock_and_cash_mergers', 'name_changes', 'reorganizations'])
def test_merger_exclusion_does_not_expand_supported_categories(tmp_path, category):
    request = merger_evidence(tmp_path, category=category)
    assert admit_dataset(tmp_path, request)['error_code'] == 'unsupported_action_exclusion'


@pytest.mark.parametrize('changes,code', [
    ({'record_sha256': '0' * 64}, 'excluded_record_mismatch'),
    ({'source_sha256': '0' * 64}, 'unbound_primary_judgment'),
    ({'category': 'stock_mergers'}, 'excluded_record_mismatch'),
    ({'provider_id': 'unmatched'}, 'identity_change_unresolved'),
    ({'effective_date': '2020-02-02'}, 'excluded_event_not_before_acquired_interval'),
    ({'acquirer': {'symbol': 'FIX', 'cusip': 'other-cusip', 'isin': None}}, 'excluded_merger_role_mismatch'),
    ({'acquiree': {'symbol': 'WRONG', 'cusip': 'other-cusip', 'isin': None}}, 'excluded_merger_role_mismatch'),
])
def test_excluded_annotation_is_bound_to_exact_record_and_roles(tmp_path, changes, code):
    def modify(facts):
        facts['excluded_actions'][0].update(changes)
    assert admit_dataset(tmp_path, merger_evidence(tmp_path, annotate=modify))['error_code'] == code


@pytest.mark.parametrize('changes,code', [
    ({'date': '2019-01-01'}, 'unresolved_merger_completion'),
    ({'date': DATES[0]}, 'unresolved_merger_completion'),
    ({'date': None}, 'invalid_date'),
    ({'source_sha256': '0' * 64}, 'unbound_primary_judgment'),
    ({'judgment': ''}, 'missing_attributed_judgment'),
    ({'no_studied_share_conversion': False}, 'unresolved_merger_completion'),
    ({'no_studied_share_conversion': 1}, 'unresolved_merger_completion'),
    ({'no_outstanding_studied_entitlement': False}, 'unresolved_merger_completion'),
])
def test_unknown_payment_requires_bound_explicit_completion(tmp_path, changes, code):
    def modify(facts):
        facts['excluded_actions'][0]['completion'].update(changes)
    request = merger_evidence(tmp_path, annotate=modify)
    assert admit_dataset(tmp_path, request)['error_code'] == code


def test_completion_judgment_cannot_be_replaced_with_approval_boolean(tmp_path):
    def modify(facts):
        facts['excluded_actions'][0]['completion'] = True
    assert admit_dataset(tmp_path, merger_evidence(tmp_path, annotate=modify))['error_code'] == 'invalid_merger_completion_judgment'


@pytest.mark.parametrize('case', ['duplicate', 'accepted_and_excluded', 'extra_unknown'])
def test_duplicate_and_unmatched_exclusion_annotations_reject(tmp_path, case):
    def modify(facts):
        extra = deepcopy(facts['excluded_actions'][0])
        if case == 'accepted_and_excluded':
            facts['events'].append({key: extra[key] for key in ('provider_id', 'source_sha256', 'locator', 'judgment')})
        else:
            if case == 'extra_unknown':
                extra['provider_id'] = 'unknown'
            facts['excluded_actions'].append(extra)
    expected = 'unmatched_action_exclusions' if case == 'extra_unknown' else 'duplicate_or_conflicting_action_annotation'
    assert admit_dataset(tmp_path, merger_evidence(tmp_path, annotate=modify))['error_code'] == expected


def test_excluded_record_conflicts_are_checked_before_exclusion(tmp_path):
    conflicting = {**MERGER, 'acquirer_symbol': 'OTHER'}
    request = merger_evidence(tmp_path, duplicates=[conflicting])
    assert admit_dataset(tmp_path, request)['error_code'] == 'conflicting_same_id_actions'


def test_cross_category_same_id_conflict_precedes_exclusion(tmp_path):
    def mutate(actions):
        actions['stock_mergers'] = [deepcopy(MERGER)]
    request = merger_evidence(tmp_path, actions_mutate=mutate)
    assert admit_dataset(tmp_path, request)['error_code'] == 'conflicting_same_id_actions'


def test_excluded_multiple_ids_same_event_reject_despite_process_difference(tmp_path):
    other = {**MERGER, 'id': 'new-id', 'process_date': '2020-02-10'}
    request = merger_evidence(tmp_path, duplicates=[other])
    facts = get(tmp_path, request['primary_facts_sha256'])
    receipt = get(tmp_path, request['actions_receipt_sha256'])
    normalized = get(tmp_path, receipt['normalized_sha256'])
    record = next(x['record'] for x in normalized['records'] if x['record']['id'] == 'new-id')
    from quanto.ledger import hash_json
    extra = deepcopy(facts['excluded_actions'][0])
    extra.update(provider_id='new-id', record_sha256=hash_json(record))
    facts['excluded_actions'].append(extra)
    request['primary_facts_sha256'] = put(tmp_path, facts)
    assert admit_dataset(tmp_path, request)['error_code'] == 'ambiguous_multiple_ids_same_event'


def test_acquiree_isin_cannot_match_studied_security_even_if_acquirer_isin_absent(tmp_path):
    def mutate(actions):
        actions['forward_splits'][0]['isin'] = 'STUDIEDISIN'
        actions['cash_dividends'][0]['isin'] = 'STUDIEDISIN'
    request = merger_evidence(tmp_path, record={**MERGER, 'acquiree_isin': 'STUDIEDISIN'}, actions_mutate=mutate)
    assert admit_dataset(tmp_path, request)['error_code'] == 'excluded_acquiree_identifier_conflict'


def test_acquirer_cusip_cannot_mask_isin_conflict(tmp_path):
    def mutate(actions):
        actions['forward_splits'][0]['isin'] = 'STUDIEDISIN'
    request = merger_evidence(tmp_path, record={**MERGER, 'acquirer_isin': 'OTHERISIN'}, actions_mutate=mutate)
    assert admit_dataset(tmp_path, request)['error_code'] == 'excluded_acquirer_identifier_unresolved'


@pytest.mark.parametrize('payable', [None, '', '2020-02-03'])
def test_explicit_completion_supports_unknown_or_completed_payment(tmp_path, payable):
    request = merger_evidence(tmp_path, record={**MERGER, 'payable_date': payable})
    assert admit_dataset(tmp_path, request)['status'] == 'success'


@pytest.mark.parametrize('mode', ['corrupt', 'tombstone'])
def test_excluded_primary_completion_source_rechecked_before_calculation(tmp_path, mode):
    request = merger_evidence(tmp_path)
    result = admit_dataset(tmp_path, request)
    assert result['status'] == 'success', result
    facts = get(tmp_path, request['primary_facts_sha256'])
    digest = facts['excluded_actions'][0]['completion']['source_sha256']
    if mode == 'corrupt':
        (tmp_path / 'data' / 'objects' / f'{digest}.bin').write_bytes(b'changed')
    else:
        with Provenance(tmp_path) as store:
            store.tombstone(digest, 'invalid_artifact')
    denied = run_submission(tmp_path, study(request, result['admission_sha256']))
    assert denied['error_code'] == 'artifact_or_storage_unavailable'


def test_new_exclusion_never_overwrites_original_refusal(tmp_path):
    request = merger_evidence(tmp_path)
    facts = get(tmp_path, request['primary_facts_sha256'])
    initial = deepcopy(facts)
    del initial['excluded_actions']
    first = admit_dataset(tmp_path, {**request, 'primary_facts_sha256': put(tmp_path, initial)})
    assert first['error_code'] == 'identity_change_unresolved'
    second = admit_dataset(tmp_path, request)
    assert second['status'] == 'success'
    with Provenance(tmp_path) as store:
        assert store.get_submission(first['submission_id'])['status'] == 'invalid'
        assert store.get_submission(second['submission_id'])['status'] == 'success'

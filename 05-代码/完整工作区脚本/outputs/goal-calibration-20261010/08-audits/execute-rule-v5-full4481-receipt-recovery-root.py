"""Derive a receipt-recovered v5 full-rule output without rerunning semantic coding.

This consumes the sealed failed first run.  Only the three independently verified
legacy status-alias failures can receive their already-validated diagnostic
decisions.  Original first-run files are never modified.
"""
import copy
import datetime
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
FIRST = R / '06-coding/rule-full4481-final-v5-sol/run4481-first'
PLAN = R / '06-coding/rule-full4481-final-v5-receipt-recovery-plan-sol'
INTEGRATION = R / '08-audits/source-request-status-bridge-S3-integration-sol'
INTERFACE = R / '08-audits/v5-historical-S3-ledger-interface-sol'
BRIDGE = R / '08-audits/source-request-status-bridge-sol'
OUT = R / '06-coding/rule-full4481-final-v5-receipt-recovery-root'
TARGETS = ('RECODE25-00036', 'RECODE25-00038', 'RECODE25-00045')
DIMS = ('S', 'E', 'Ec', 'I', 'F')

assert not OUT.exists()

def load(path):
    return json.loads(Path(path).read_bytes())

def bind(path):
    p = Path(path).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def exact(item):
    current = bind(item['path'])
    assert current == {key: item[key] for key in ('path', 'bytes', 'sha256')}, item['path']

def receive_seal(path, sha, member_key, member_n, input_n=None):
    item = bind(path)
    assert item['sha256'] == sha
    payload = load(path)
    members = payload[member_key]
    assert len(members) == member_n
    if input_n is not None:
        assert len(payload['inputs']) == input_n
    for member in members + payload.get('inputs', []):
        if 'path' in member:
            exact(member)
        else:
            # This older audit uses a self-contained relative manifest.
            candidate = Path(path).parent / member['relative_path']
            raw = candidate.read_bytes()
            assert len(raw) == member['bytes']
            assert hashlib.sha256(raw).hexdigest() == member['sha256']
    return item, payload

def jsonl(path):
    rows = []
    raw_lines = Path(path).read_bytes().splitlines(keepends=True)
    for index, raw in enumerate(raw_lines, 1):
        value = json.loads(raw.rstrip(b'\r\n'))
        rows.append((index, raw, value))
    return rows

def write_json(path, value):
    with Path(path).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def write_jsonl(path, values):
    with Path(path).open('x', encoding='utf8') as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False))
            stream.write('\n')

# First run is terminal and complete; bind every existing recorded artifact before
# deriving anything.  The failure remains evidence, not an overwrite target.
first_execution = load(FIRST / 'execution.json')
assert first_execution['status'] == 'failed_execution_attempt'
assert (first_execution['expected_record_N'], first_execution['actual_record_N']) == (4481, 4481)
assert first_execution['technical_failure_dimension_N'] == 15
first_seal = load(FIRST / 'seal.json')
assert first_seal['status'] == 'sealed_failed_execution_attempt'
assert first_seal['technical_failure_dimension_N'] == 15
first_pre = bind(R / '06-coding/rule-full4481-final-v5-sol/pre-execution-run-seal.json')
assert first_pre['sha256'] == '2bf1a02ec6a92fc96bdf698b3d80ff8e28a6a7c980c924d76a53008b291a3dfc'
for item in first_seal['output_files']:
    exact(item)

integration_seal, integration = receive_seal(
    INTEGRATION / 'output-seal.json',
    'a8fa784bf60226613e3939a57d3d0935f014aa14b300c8c7e7e021f690ce9e9f',
    'members', 32, 49)
assert integration['records'] == list(TARGETS)
assert integration['check_calls_N'] == integration['matching_checks_N'] == 6
assert integration['semantic_unit_RelationView_judge_actual_reading_log_calls_N'] == 0
assert integration['recovery_N'] == integration['retained_labels_N'] == integration['metrics_N'] == 0
interface_seal, interface = receive_seal(
    INTERFACE / 'output-seal.json',
    '8311a4f6876e1d8ce700551dc9d209d79b18f6201fca0fe18f4bb59561d8d6ee',
    'members', 17)
assert interface['original_first_failures_preserved']
assert interface['classifier_calls'] == interface['protocol_check_calls'] == interface['recovery_calls'] == 0
bridge_seal, bridge = receive_seal(
    BRIDGE / 'output-seal.json',
    'df32a5eefebff587eaf0a3b1606146db85022c017e4574e466b17c8d92d3c5a5',
    'members', 12, 10)
assert bridge['synthetic_controls_N'] == bridge['synthetic_matches_N'] == 18
assert bridge['actual_full_domain_processed_N'] == bridge['classifier_calls_N'] == 0
assert not bridge['recovery_executed']
plan = load(PLAN / 'execution-plan.json')
assert not plan['GO']
for item in (plan['first_run_pre_execution_binding'], plan['final_candidate_algorithm']):
    exact(item)
evidence = load(PLAN / 'evidence-path-and-pointer-freeze.json')
assert not evidence['GO']
assert evidence['semantic_unit_RelationView_judge_calls_allowed'] == 0
assert evidence['candidate_diagnostics_not_first_run_retained_labels']
assert len(evidence['receiver_source_requests_pointer_whitelist']) == 6

pred_rows = jsonl(FIRST / 'predictions.jsonl')
consume_rows = jsonl(FIRST / 'actual-source-consumption.jsonl')
ledger_rows = jsonl(FIRST / 'execution-ledger.jsonl')
assert len(pred_rows) == len(consume_rows) == len(ledger_rows) == 4481
assert [row[2]['id'] for row in pred_rows] == [row[2]['id'] for row in consume_rows]
assert [row[2]['id'] for row in pred_rows] == [row[2]['id'] for row in ledger_rows]
for index, (_, _, ledger) in enumerate(ledger_rows, 1):
    assert ledger['index_1based'] == index

target_source = {}
for index, raw, value in pred_rows:
    if value['id'] in TARGETS:
        target_source[value['id']] = {'prediction_line_1based': index,
            'prediction_line_sha256': hashlib.sha256(raw).hexdigest(), 'prediction': value}
for index, raw, value in consume_rows:
    if value['id'] in TARGETS:
        target_source[value['id']].update({'consumption_line_1based': index,
            'consumption_line_sha256': hashlib.sha256(raw).hexdigest(), 'consumption': value})
assert set(target_source) == set(TARGETS)

# The integration audit saved the only permitted derived checks.  Its preservation
# receipts bind source/log/closure evidence to each first-run target.
for record_id in TARGETS:
    prediction = target_source[record_id]['prediction']
    consumption = target_source[record_id]['consumption']
    errors = prediction['implementation_errors']
    assert len(errors) == 1
    assert errors[0]['type'] == 'ValueError'
    assert errors[0]['message'] == 'source dependency stop has no concrete stopped rule dependency'
    diagnostics = prediction['candidate_decisions_diagnostic_only']
    assert set(diagnostics) == set(DIMS)
    assert all(diagnostics[dimension]['value'] in (0, 1, None) for dimension in DIMS)
    assert not prediction.get('labels') and not prediction.get('decisions')
    for role in ('source_requests', 'uniform_source_reading_log', 'live_view_source_audit'):
        if role == 'source_requests':
            direct = prediction[role]
        else:
            direct = prediction[role]['source_requests']
        assert direct == prediction['source_requests']
    assert consumption['source_requests'] == prediction['source_requests']
    preserved = load(INTEGRATION / 'execution/preservation' / f'{record_id}.json')
    assert preserved['record_id'] == record_id
    assert preserved['exact_only_status_alias_added']
    assert preserved['complete_original_wrapper_except_target_request_array_equal']
    assert preserved['mapping_receipt']['original_document_sha256'] == target_source[record_id]['consumption_line_sha256']
    checks = load(INTEGRATION / 'execution/checks' / f'{record_id}-alias.json')
    original_checks = load(INTEGRATION / 'execution/checks' / f'{record_id}-original.json')
    assert checks['actual_output']['errors'] == []
    assert checks['actual_output']['dependency_stop_reasons'] == []
    assert checks['driver_equivalent_required_stops_N'] == 0
    assert original_checks['actual_output']['errors'] == []
    assert original_checks['actual_output']['dependency_stop_reasons'] == ['missing_required_source']
    assert original_checks['driver_equivalent_required_stops_N'] == 1

OUT.mkdir()
recovered_predictions = []
recovery_ledger = []
for index, raw, prediction in pred_rows:
    updated = copy.deepcopy(prediction)
    record_id = updated['id']
    if record_id in TARGETS:
        diagnostics = updated.pop('candidate_decisions_diagnostic_only')
        first_errors = copy.deepcopy(updated['implementation_errors'])
        updated['implementation_errors'] = []
        updated['labels'] = {dimension: diagnostics[dimension]['value'] for dimension in DIMS}
        updated['decisions'] = diagnostics
        updated['receipt_recovery'] = {
            'kind': 'mechanical_status_alias_receipt_recovery',
            'first_prediction_line_sha256': hashlib.sha256(raw).hexdigest(),
            'first_implementation_errors': first_errors,
            'independent_integration_seal': integration_seal,
            'semantic_reexecution_N': 0,
            'semantic_result_changed': False,
            'original_first_run_remains_failed_and_preserved': True}
        recovery_ledger.append({'id': record_id, 'first_prediction_line_1based': index,
            'first_prediction_line_sha256': hashlib.sha256(raw).hexdigest(),
            'first_failure_type': first_errors[0]['type'],
            'first_failure_message': first_errors[0]['message'],
            'recovered_values': updated['labels'],
            'recovery_kind': 'receipt_only_status_alias',
            'semantic_adapter_RelationView_judge_calls': 0})
    else:
        assert isinstance(updated.get('labels'), dict) and isinstance(updated.get('decisions'), dict)
        assert not updated['implementation_errors']
    recovered_predictions.append(updated)
assert len(recovery_ledger) == 3
assert sum(bool(p.get('implementation_errors')) for p in recovered_predictions) == 0
assert sum(isinstance(p.get('labels'), dict) for p in recovered_predictions) == 4481

slots = []
for prediction in recovered_predictions:
    for dimension in DIMS:
        decision = prediction['decisions'][dimension]
        value = decision['value']
        slots.append({'id': prediction['id'], 'dimension': dimension,
            'status': 'source_dependency_unresolved' if value is None else 'retained_rule_decision',
            'technical_failure': False, 'rules_null': value is None, 'rule_value': value,
            'retained_rule_decision': decision,
            'receipt_recovered_from_first_failure': prediction['id'] in TARGETS,
            'no_semantic_reexecution': prediction['id'] in TARGETS})
assert len(slots) == 22405
assert sum(item['technical_failure'] for item in slots) == 0
assert sum(item['rules_null'] for item in slots) == first_execution['lawful_null_N']

write_jsonl(OUT / 'recovered-predictions.jsonl', recovered_predictions)
write_jsonl(OUT / 'all-dimension-slots.jsonl', slots)
write_json(OUT / 'receipt-recovery-ledger.json', recovery_ledger)
execution = {'status': 'completed_receipt_only_recovery',
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'expected_record_N': 4481, 'retained_decision_N': 22405,
    'technical_failure_dimension_N': 0, 'lawful_null_N': sum(item['rules_null'] for item in slots),
    'first_run_technical_failure_dimension_N': 15,
    'recovered_record_N': 3, 'recovered_dimension_N': 15,
    'unrecovered_first_failure_record_N': 0,
    'semantic_adapter_RelationView_judge_calls_N': 0,
    'first_run_preserved_not_overwritten': True,
    'formal_validation_complete': False,
    'human_validation_complete': False,
    'metric_claims_N': 0,
    'source_bindings': {'first_execution': bind(FIRST / 'execution.json'),
        'first_seal': bind(FIRST / 'seal.json'), 'first_pre_execution': first_pre,
        'integration_seal': integration_seal, 'interface_seal': interface_seal,
        'bridge_seal': bridge_seal, 'recovery_plan': bind(PLAN / 'execution-plan.json'),
        'evidence_pointer_freeze': bind(PLAN / 'evidence-path-and-pointer-freeze.json')}}
write_json(OUT / 'execution.json', execution)
outputs = [bind(path) for path in sorted(OUT.iterdir()) if path.is_file()]
write_json(OUT / 'seal.json', {'status': 'sealed_completed_receipt_only_recovery',
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'output_files': outputs, 'first_run_preserved_not_overwritten': True,
    'recovered_record_N': 3, 'recovered_dimension_N': 15,
    'semantic_adapter_RelationView_judge_calls_N': 0,
    'formal_metric_or_accuracy_claims_N': 0})
print(json.dumps({'status': execution['status'], 'records': execution['retained_decision_N'] // 5,
    'recovered_records': execution['recovered_record_N'], 'technical_failure_dimensions': 0,
    'lawful_null': execution['lawful_null_N']}, ensure_ascii=False))

"""Explicit ROOT version-level authorization: historical S3, v5, once each."""
from pathlib import Path
import copy
import datetime
import hashlib
import importlib
import json
import shutil
import sys
import traceback

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
CODE = ROOT / '06-coding/rule-five-dimension-joint-root/versions/joint-v5-primary-standard-bridge-sol'
PLAN = ROOT / '08-audits/common-candidate-actual-interface-sol/historical-human-S3-development-plan'
BASELINE = ROOT / '08-audits/common-candidate-actual-interface-v4-execution-sol'
OUT = Path(__file__).resolve().parent
IDS = ['RECODE25-00036', 'RECODE25-00038', 'RECODE25-00045']
DIMS = ['S', 'E', 'Ec', 'I', 'F']
PRE_SHA = '4f8ae9d0a3eb116dd3cd6b44bd8355683b08a54921ee1a6739aff0b609dc3cae'
ALG_SHA = '5f9d780b4a72779f69e91082881109f65aa8adc6395ebf94b061bd207e0d14bf'
PLAN_SHA = 'e791c3183117c5d2c427788b818febf6df0faa2c6c99d3d2f73206690f4b185b'
BASELINE_SHA = '3440b911dd4eb92773a2edda27ea33e87b71e90da40165203a6af2300c4af8ca'


def load(p):
    return json.loads(Path(p).read_bytes())


def cj(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def bind(p):
    p = Path(p).resolve(); raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def verified(m):
    assert bind(m['path']) == m
    return m


def write(name, v):
    p = OUT / name; p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f:
        json.dump(v, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n'); f.flush()


assert not (OUT / 'execution-started.json').exists(), 'No technical or semantic retry allowed'
assert bind(CODE / 'pre-execution-seal.json')['sha256'] == PRE_SHA
assert bind(CODE / 'algorithm-bindings.json')['sha256'] == ALG_SHA
assert bind(PLAN / 'output-seal.json')['sha256'] == PLAN_SHA
assert bind(BASELINE / 'output-seal.json')['sha256'] == BASELINE_SHA
pre, alg, planseal = load(CODE / 'pre-execution-seal.json'), load(CODE / 'algorithm-bindings.json'), load(PLAN / 'output-seal.json')
assert pre['five_modules'] == alg['five_modules']
assert pre['post_independent_result_mutation_allowed'] is False
active = [verified(m) for m in pre['five_modules'] + [pre['manual']] + pre['common_frozen_input_bindings']]
for m in planseal['members'] + planseal['inputs']:
    verified(m)
fixed = load(PLAN / 'fixed-S3-before-execution.json')
assert [(c['record_id'], c['dimension'], c['expected_value']) for c in fixed] == [(rid, 'S', 1) for rid in IDS]
assert all(c['other_dimension_expectations'] is None for c in fixed)
snapshot = OUT / 'code-snapshot'; snapshot.mkdir(exist_ok=False)
source_snapshot = OUT / 'source-only-packets'; source_snapshot.mkdir(exist_ok=False)
for m in pre['five_modules']:
    p = Path(m['path']); shutil.copyfile(p, snapshot / p.name)
    assert bind(snapshot / p.name)['sha256'] == m['sha256']
for c in fixed:
    p = Path(c['frozen_source_packet_copy']['path']); verified(c['frozen_source_packet_copy'])
    shutil.copyfile(p, source_snapshot / p.name)
shutil.copyfile(PLAN / 'fixed-S3-before-execution.json', OUT / 'historical-S3-fixed-expectations-original-copy.json')
write('execution-started.json', {
    'authority': 'ROOT explicitly authorizes final sealed v5 to run the same historical S3 once each as a new version-level development regression; v4 limit and files remain unchanged',
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'candidate_preseal': bind(CODE / 'pre-execution-seal.json'), 'algorithm_bindings': bind(CODE / 'algorithm-bindings.json'),
    'plan_seal': bind(PLAN / 'output-seal.json'), 'original_v4_execution_seal': bind(BASELINE / 'output-seal.json'),
    'source_bindings': [c['frozen_source_packet_copy'] for c in fixed],
    'active_5modules_manual_common_bindings': active,
    'per_case_limits': {'semantic_unit': 1, 'RelationView': 1, 'judge': 1},
    'retry_allowed': False, 'source_only_interface': True, 'expected_values_passed_to_candidate': False,
    'injected_proof_relation_unit_label_or_resolved_receipt': False,
    'historical_expectation_dimensions_only': ['S'], 'new_human_or_formal_reference_results': 0,
})
sys.dont_write_bytecode = True
sys.path.insert(0, str(snapshot))
source_packet = importlib.import_module('source_packet')
relations = importlib.import_module('relations')
dimensions = importlib.import_module('dimensions')
evidence = importlib.import_module('evidence')
for name in ('source_packet', 'relations', 'dimensions', 'evidence'):
    assert Path(sys.modules[name].__file__).resolve() == snapshot / (name + '.py')

observed_units = []; positive_events = []
original_units = dimensions._units; original_add = dimensions.Accumulator.add


def allowed(details):
    permitted = set(details.get('affected_dimensions', DIMS))
    if details.get('only_IF_consumers'):
        permitted &= {'I', 'F'}
    return [d for d in DIMS if d in permitted]


def observe_units(view):
    units = original_units(view)
    for u in units:
        observed_units.append({'text': u.text, 'start': u.a, 'end': u.b,
                               'kind': u.kind, 'inherited': u.inherited,
                               'contexts': copy.deepcopy(u.contexts), 'details': copy.deepcopy(u.details),
                               'allowed_consumers': allowed(u.details)})
    return units


def observe_add(acc, dim, u, path, reason, obj, details=None):
    before = len(acc.positive[dim]); value = original_add(acc, dim, u, path, reason, obj, details)
    if len(acc.positive[dim]) > before:
        positive_events.append({'dimension': dim, 'basis_path': path, 'unit_kind': u.kind, 'unit_text': u.text,
                                'unit_details': copy.deepcopy(u.details), 'unit_contexts': copy.deepcopy(u.contexts),
                                'accepted_positive': copy.deepcopy(acc.positive[dim][-1]),
                                'allowed_consumers': allowed(u.details), 'consumer_contract_matched': dim in allowed(u.details)})
    return value


dimensions._units = observe_units; dimensions.Accumulator.add = observe_add
events = (OUT / 'immediate-events.jsonl').open('x', encoding='utf-8')
stream = (OUT / 'immediate-case-results.jsonl').open('x', encoding='utf-8')


def emit(event, rid, **values):
    events.write(cj({'event': event, 'record_id': rid, 'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), **values}) + '\n')
    events.flush()


results = []
for c in fixed:
    rid = c['record_id']; unit = view = decisions = None
    counts = {'semantic_unit': 0, 'RelationView': 0, 'judge': 0}
    observed_units.clear(); positive_events.clear()
    raw = load(source_snapshot / (rid + '.json')); bundle = raw['source_bundle']
    assert hashlib.sha256(cj(bundle).encode()).hexdigest() == c['source_bundle_sha256']
    assert bundle['source_record']['id'] == rid
    emit('case_start', rid, source_packet_binding=c['frozen_source_packet_copy'])
    error = validator_error = None; validator_pass = False; stage = 'source_packet'
    try:
        counts['semantic_unit'] += 1; emit('source_packet_enter', rid)
        unit = source_packet.semantic_unit(copy.deepcopy(bundle))
        assert 'id' not in unit and 'expected_value' not in unit
        write('semantic-units/' + rid + '.json', unit)
        stage = 'RelationView'; counts['RelationView'] += 1; emit('RelationView_enter', rid)
        view = relations.RelationView(unit); emit('RelationView_return', rid)
        stage = 'judge'; counts['judge'] += 1; emit('judge_enter', rid)
        decisions = dimensions.judge(view); emit('judge_return', rid, full_five_decisions=decisions)
    except Exception as exc:
        error = {'stage': stage, 'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
        emit(stage + '_exception', rid, error=error)
    if decisions is not None:
        try:
            evidence.validate_decisions(unit, decisions); validator_pass = True
            emit('evidence_validator_pass', rid)
        except Exception as exc:
            validator_error = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
            emit('evidence_validator_exception', rid, error=validator_error)
    inspection_error = None; trace = None
    try:
        if view is not None:
            trace = {'relations': view.traces(), 'material_requests': view.material_requests,
                     'source_requests': view.source_requests, 'source_view_events': view.source_view_events,
                     'source_relation_traces': view.source_relation_traces,
                     'structural_address_issues': view.structural_address_issues, 'source_scope_review': view.source_scope_review}
    except Exception as exc:
        inspection_error = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
        emit('trace_inspection_exception', rid, error=inspection_error)
    row = {'record_id': rid, 'source_packet': c['frozen_source_packet_copy'],
           'source_bundle_sha256': c['source_bundle_sha256'], 'calls': counts,
           'expected_S': c['expected_value'], 'other_dimension_expectations': None,
           'decisions_first_v5_execution': decisions,
           'observed_values_only': {d: decisions[d]['value'] for d in DIMS} if decisions is not None else None,
           'S_output_present': decisions is not None,
           'actual_S': decisions['S']['value'] if decisions is not None else None,
           'matches_historical_S': decisions is not None and decisions['S']['value'] == c['expected_value'],
           'execution_error': error, 'validator_pass': validator_pass, 'validator_error': validator_error,
           'trace': trace, 'trace_inspection_error': inspection_error,
           'natural_units': copy.deepcopy(observed_units), 'accepted_positive_consumers': copy.deepcopy(positive_events),
           'candidate_version_level_attempt': 1, 'technical_or_semantic_retry': False,
           'not_new_human_result_or_formal_validation': True}
    stream.write(cj(row) + '\n'); stream.flush(); results.append(row)
    emit('case_result_saved', rid, actual_S=row['actual_S'], semantic_output_present=decisions is not None,
         error=error, trace=trace)
emit('execution_complete', 'all3', calls={k: sum(r['calls'][k] for r in results) for k in counts}, saved_results_N=len(results))
events.close(); stream.close()
write('execution-results.json', results)
summary = {'status': 'first_v5_historical_S3_development_execution_saved', 'record_ids': IDS,
           'actual_S': [r['actual_S'] for r in results], 'S_outputs_present_N': sum(r['S_output_present'] for r in results),
           'historical_S_matches_N': sum(r['matches_historical_S'] for r in results),
           'calls': {k: sum(r['calls'][k] for r in results) for k in counts},
           'execution_errors_N': sum(r['execution_error'] is not None for r in results),
           'validator_pass_N': sum(r['validator_pass'] for r in results),
           'validator_errors_N': sum(r['validator_error'] is not None for r in results),
           'trace_inspection_errors_N': sum(r['trace_inspection_error'] is not None for r in results),
           'retry_N': 0, 'new_human_results_N': 0, 'new_policy_record_ids_N': 0, 'formal_metrics_N': 0,
           'expectation_dimensions': ['S'], 'other_dimensions_observation_only': True}
write('execution-summary.json', summary)
print(json.dumps(summary, ensure_ascii=False))

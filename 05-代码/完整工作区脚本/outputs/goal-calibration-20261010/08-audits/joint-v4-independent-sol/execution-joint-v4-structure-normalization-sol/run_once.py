"""One source-only execution of the previously sealed hidden six.

Observation wrappers call original functions once and return their unchanged
values. No relation, unit, receipt, source material or expected answer is added
to the candidate input. Every case and every judge return is flushed immediately.
"""
from pathlib import Path
import copy
import datetime
import hashlib
import importlib
import json
import shutil
import sys
import traceback

ROOT = Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
PREP = ROOT / '08-audits/joint-v4-independent-sol'
CANDIDATE = ROOT / '06-coding/rule-five-dimension-joint-root/versions/joint-v4-structure-normalization-sol'
OUT = Path(__file__).resolve().parent
DIMS = ['S', 'E', 'Ec', 'I', 'F']
EXPECTED_PREP = 'f0a5d3d68161f1856723c2d5ff1f107272a6a06f414fe23fb5d12bb92893f06b'
EXPECTED_CANDIDATE_PRESEAL = 'd3eb4a895f1154173488eac32366f86a47687c9935716eb50876f3ba9a5670e0'
EXPECTED_ALGORITHM = '45c33b4eb89e3a263a36560515617f1884f91c13e988777881675b7119e8a54b'


def cj(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def bind(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def check_binding(binding):
    actual = bind(Path(binding['path']))
    assert actual == binding, {'expected': binding, 'actual': actual}
    return actual


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()


assert bind(PREP / 'preparation-seal.json')['sha256'] == EXPECTED_PREP
assert bind(CANDIDATE / 'pre-execution-seal.json')['sha256'] == EXPECTED_CANDIDATE_PRESEAL
assert bind(CANDIDATE / 'algorithm-bindings.json')['sha256'] == EXPECTED_ALGORITHM
preseal = load(PREP / 'preparation-seal.json')
candidate_preseal = load(CANDIDATE / 'pre-execution-seal.json')
algorithm = load(CANDIDATE / 'algorithm-bindings.json')
assert preseal['case_N'] == 6 and preseal['candidate_judge_attempts_N'] == 0
assert len(preseal['output_members']) == 10
assert all(Path(m['path']).resolve() != (PREP / 'preparation-seal.json').resolve() for m in preseal['output_members'])
checked_preparation = [check_binding(m) for m in preseal['output_members']]
checked_active = [check_binding(m) for m in candidate_preseal['five_modules']]
assert checked_active == algorithm['five_modules']
assert preseal['manual_binding'] == candidate_preseal['manual'] == algorithm['manual']
checked_manual = check_binding(candidate_preseal['manual'])
checked_common = [check_binding(m) for m in candidate_preseal['common_frozen_input_bindings']]
assert checked_common == algorithm['common_frozen_input_bindings']
assert not candidate_preseal['post_independent_result_mutation_allowed']
assert not candidate_preseal['new_v4_hidden_controls_read']
plan = load(PREP / 'controls6-fixed-before-execution.json')
assert plan['case_N'] == len(plan['cases']) == 6
assert len({c['name'] for c in plan['cases']}) == 6
assert not plan['expected_changes_after_candidate_execution_allowed']
snapshot = OUT / 'code-snapshot'
snapshot.mkdir(exist_ok=False)
for m in checked_active:
    src = Path(m['path'])
    shutil.copyfile(src, snapshot / src.name)
    assert bind(snapshot / src.name)['sha256'] == m['sha256']
input_snapshot = OUT / 'input-snapshot'
input_snapshot.mkdir(exist_ok=False)
for name in ('controls6-fixed-before-execution.json', 'preparation-seal.json', 'manual-basis-quotes.json'):
    shutil.copyfile(PREP / name, input_snapshot / name)
docs_snapshot = input_snapshot / 'synthetic-source-documents'
docs_snapshot.mkdir(exist_ok=False)
for member in checked_preparation:
    path = Path(member['path'])
    if path.parent.name == 'synthetic-source-documents':
        shutil.copyfile(path, docs_snapshot / path.name)
write('execution-input-and-code-seal.json', {
    'status': 'original_hidden6_and_final_v4_bound_before_first_candidate_execution',
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'original_preparation_seal': bind(PREP / 'preparation-seal.json'),
    'original_controls': bind(PREP / 'controls6-fixed-before-execution.json'),
    'preparation_members': checked_preparation,
    'candidate_pre_execution_seal': bind(CANDIDATE / 'pre-execution-seal.json'),
    'algorithm_bindings': bind(CANDIDATE / 'algorithm-bindings.json'),
    'active_modules': checked_active,
    'snapshot_modules': [bind(snapshot / Path(m['path']).name) for m in checked_active],
    'manual': checked_manual, 'common_frozen_bindings': checked_common,
    'owner_development_control_or_result_contents_read': False,
    'parent75_or235_answer_tables_read': False,
    'candidate_judge_attempts_before_this_execution_N': 0,
    'source_only_interface': 'deepcopy(synthetic_bundle) -> semantic_unit -> RelationView -> judge -> validate_decisions',
    'expected_answer_or_case_name_passed_to_candidate': False,
    'relation_or_unit_or_receipt_or_material_injected': False,
})
with (OUT / 'executed-source-only-inputs.jsonl').open('x', encoding='utf-8') as stream:
    for case in plan['cases']:
        stream.write(cj({'name': case['name'], 'source_only_bundle': case['synthetic_bundle']}) + '\n')
    stream.flush()

sys.dont_write_bytecode = True
sys.path.insert(0, str(snapshot))
source_packet = importlib.import_module('source_packet')
evidence = importlib.import_module('evidence')
relations = importlib.import_module('relations')
dimensions = importlib.import_module('dimensions')
for module_name in ('source_packet', 'source_receipts', 'evidence', 'relations', 'dimensions'):
    if module_name in sys.modules:
        assert Path(sys.modules[module_name].__file__).resolve() == snapshot / (module_name + '.py')

units_observed = []
positive_events = []
original_units = dimensions._units
original_add = dimensions.Accumulator.add


def allowed_consumers(details):
    allowed = set(details.get('affected_dimensions', DIMS))
    if details.get('only_IF_consumers'):
        allowed &= {'I', 'F'}
    return [d for d in DIMS if d in allowed]


def observe_units(view):
    actual = original_units(view)
    for unit in actual:
        units_observed.append({
            'text': unit.text, 'start': unit.a, 'end': unit.b,
            'kind': unit.kind, 'inherited': unit.inherited,
            'contexts': copy.deepcopy(unit.contexts), 'details': copy.deepcopy(unit.details),
            'allowed_consumers_from_contract': allowed_consumers(unit.details),
        })
    return actual


def observe_add(acc, dim, unit, path, reason, obj, details=None):
    before = len(acc.positive[dim])
    result = original_add(acc, dim, unit, path, reason, obj, details)
    if len(acc.positive[dim]) > before:
        allowed = allowed_consumers(unit.details)
        positive_events.append({
            'dimension': dim, 'basis_path': path,
            'unit_kind': unit.kind, 'unit_text': unit.text,
            'unit_inherited': unit.inherited, 'unit_details': copy.deepcopy(unit.details),
            'unit_contexts': copy.deepcopy(unit.contexts),
            'accepted_positive': copy.deepcopy(acc.positive[dim][-1]),
            'allowed_consumers_from_contract': allowed,
            'consumer_route_matched': dim in allowed,
        })
    return result


dimensions._units = observe_units
dimensions.Accumulator.add = observe_add


def recursively_citations(value):
    if isinstance(value, dict):
        if {'context_id', 'start', 'end', 'text', 'source_ref', 'usage'} <= set(value):
            yield value
        for child in value.values():
            yield from recursively_citations(child)
    elif isinstance(value, list):
        for child in value:
            yield from recursively_citations(child)


def literal_checks(case, packet, unit, decision, traces, requests, material, positives):
    documents = {d['binding']['sha256']: d for d in case['synthetic_documents']}
    contexts = {c['context_id']: c for c in unit['contexts']}
    assert len(contexts) == len(unit['contexts'])
    rows = []
    current = packet['source_record']
    for role, context in [('current', current)] + [('available_context', c) for c in unit['contexts'] if c['text']]:
        ref = context['source_ref']
        doc = documents[ref['sha256']]
        assert bind(Path(doc['binding']['path'])) == doc['binding']
        assert hashlib.sha256(doc['text'].encode('utf-8')).hexdigest() == ref['sha256']
        loc = ref['locator']; a, b = loc['unicode_code_point_interval_half_open']
        ba, bb = loc['utf8_byte_interval_half_open']
        assert doc['text'][a:b] == context['text']
        assert doc['text'].encode('utf-8')[ba:bb].decode('utf-8') == context['text']
        expected_lines = [doc['text'][:a].count('\n') + 1, doc['text'][:max(a, b - 1)].count('\n') + 1]
        assert loc['physical_line_interval_inclusive'] == expected_lines
        rows.append({'role': role, 'context_id': context.get('context_id'), 'text': context['text'],
                     'source_ref': ref, 'literal_binding_valid': True})
    quotes = []
    seen = set()
    for q in recursively_citations([decision, traces, requests, material, positives]):
        identity = cj(q)
        if identity in seen:
            continue
        seen.add(identity)
        ctx = contexts[q['context_id']]
        assert ctx['text'][q['start']:q['end']] == q['text']
        assert ctx['source_ref'] == q['source_ref']
        doc = documents[q['source_ref']['sha256']]
        loc = ctx['source_ref']['locator']; ca, cb = loc['unicode_code_point_interval_half_open']
        ba, bb = loc['utf8_byte_interval_half_open']
        a, b = ca + q['start'], ca + q['end']
        qa = ba + len(ctx['text'][:q['start']].encode('utf-8'))
        qb = ba + len(ctx['text'][:q['end']].encode('utf-8'))
        assert doc['text'][a:b] == q['text']
        assert doc['text'].encode('utf-8')[qa:qb].decode('utf-8') == q['text']
        quotes.append({'context_id': q['context_id'], 'context_kind': ctx['kind'],
                       'context_structure': ctx['structure'], 'usage': q['usage'], 'quote': q['text'],
                       'context_relative_unicode_span': [q['start'], q['end']],
                       'synthetic_document_unicode_span': [a, b],
                       'synthetic_document_utf8_byte_span': [qa, qb],
                       'source_ref': q['source_ref'], 'literal_binding_valid': True})
    anchors = []
    if decision is not None:
        for dim in DIMS:
            for field in ('current_anchor', 'current_proposition'):
                q = decision[dim].get(field)
                if q is None:
                    assert decision[dim]['value'] != 1, (dim, field, 'positive requires actual anchor')
                    continue
                assert current['text'][q['start']:q['end']] == q['text']
                anchors.append({'dimension': dim, 'field': field, 'quote': q,
                                'literal_binding_valid': True})
    return {'case': case['name'], 'source_geometry_rows': rows,
            'context_quotes': quotes, 'current_anchor_checks': anchors,
            'available_literal_text_does_not_prove_applicability': True,
            'undelivered_saved_original_not_added_to_candidate': True}


events = (OUT / 'immediate-events.jsonl').open('x', encoding='utf-8')
case_stream = (OUT / 'immediate-case-results.jsonl').open('x', encoding='utf-8')


def emit(event, name, **details):
    events.write(cj({'event': event, 'name': name,
                    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), **details}) + '\n')
    events.flush()


results = []
geometry_results = []
adapter_attempts = view_attempts = view_success = judge_attempts = judge_returns = 0
emit('execution_begin', 'all6', candidate_first_execution=True, case_N=6)
for case in plan['cases']:
    packet = copy.deepcopy(case['synthetic_bundle'])
    unit = view = decision = None
    error = quote_error = None
    evidence_valid = False
    units_observed.clear(); positive_events.clear()
    emit('case_start', case['name'], source_only_bundle_sha256=hashlib.sha256(cj(packet).encode()).hexdigest())
    stage = 'source_packet'
    try:
        adapter_attempts += 1
        emit('source_packet_enter', case['name'])
        unit = source_packet.semantic_unit(packet)
        assert 'id' not in unit and 'expected_values_fixed_before_execution' not in unit
        stage = 'RelationView'; view_attempts += 1
        emit('RelationView_enter', case['name'])
        view = relations.RelationView(unit); view_success += 1
        emit('RelationView_return', case['name'])
        stage = 'judge'; judge_attempts += 1
        emit('judge_enter', case['name'], judge_attempt_index=judge_attempts)
        decision = dimensions.judge(view); judge_returns += 1
        emit('judge_return', case['name'], full_five_decisions=decision)
        stage = 'evidence_validator'
        evidence.validate_decisions(unit, decision); evidence_valid = True
        emit('evidence_validator_pass', case['name'])
    except Exception as exc:
        error = {'stage': stage, 'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
        emit(stage + '_exception', case['name'], error=error)
    traces = []
    requests = []
    material = []
    inspection_error = None
    try:
        if view is not None:
            traces = view.traces()
            requests = copy.deepcopy(view.source_requests)
            material = copy.deepcopy(view.material_requests)
    except Exception as exc:
        inspection_error = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
        emit('source_inspection_exception', case['name'], error=inspection_error)
    local_geometry = None
    try:
        if unit is not None:
            local_geometry = literal_checks(case, packet, unit, decision, traces, requests, material, positive_events)
            geometry_results.append(local_geometry)
    except Exception as exc:
        quote_error = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
        emit('literal_quote_check_exception', case['name'], error=quote_error)
    actual = {d: decision[d]['value'] for d in DIMS} if decision is not None else None
    # An absent technical output has no semantic value and contributes no
    # numeric mismatch dimension count. It remains a separate failed case.
    numeric_mismatches = [d for d in DIMS if actual[d] != case['expected_values_fixed_before_execution'][d]] if actual is not None else []
    row = {
        'name': case['name'], 'pair_group': case['pair_group'],
        'expected_values_fixed_before_execution': case['expected_values_fixed_before_execution'],
        'actual_values': actual, 'numeric_mismatched_dimensions': numeric_mismatches,
        'semantic_output_present': decision is not None,
        'values_matched': actual is not None and not numeric_mismatches and error is None,
        'full_five_decisions_first_execution': decision, 'execution_error': error,
        'evidence_validator_passed': evidence_valid,
        'source_inspection_error': inspection_error, 'literal_quote_error': quote_error,
        'source_relation_traces': traces, 'source_requests': requests, 'material_requests': material,
        'resolved_receipts': [r for r in requests if r.get('dependency_status') == 'resolved'],
        'stopped_requests': [r for r in requests if r.get('dependency_status', 'stopped') == 'stopped'],
        'source_view_events': copy.deepcopy(getattr(view, 'source_view_events', [])) if view is not None else [],
        'source_scope_review': copy.deepcopy(getattr(view, 'source_scope_review', None)) if view is not None else None,
        'observed_natural_units': copy.deepcopy(units_observed),
        'accepted_positive_events': copy.deepcopy(positive_events),
        'consumer_route_violations': [p for p in positive_events if not p['consumer_route_matched']],
        'original_input_or_expectations_changed': False,
        'candidate_code_changed': False, 'candidate_execution_ordinal': 1,
        'synthetic_control_not_formal_human_validation': True,
    }
    results.append(row)
    case_stream.write(cj(row) + '\n'); case_stream.flush()
    emit('case_result_saved', case['name'], actual_values=actual,
         numeric_mismatched_dimensions=numeric_mismatches, execution_error=error)
emit('execution_complete', 'all6', adapter_attempts_N=adapter_attempts,
     source_view_attempts_N=view_attempts, judge_attempts_N=judge_attempts,
     judge_returns_N=judge_returns, saved_case_results_N=len(results))
case_stream.close(); events.close()
write('execution-results.json', {'status': 'first_execution_all_case_outputs_saved', 'cases': results})
write('literal-source-and-quote-validation.json', {
    'cases': geometry_results,
    'case_quote_errors': [{'case': r['name'], 'error': r['literal_quote_error']} for r in results if r['literal_quote_error']],
    'literal_alignment_is_separate_from_semantic_applicability': True,
})
summary = {
    'case_N': 6, 'source_adapter_attempts_N': adapter_attempts,
    'source_view_attempts_N': view_attempts, 'source_view_success_N': view_success,
    'candidate_judge_attempts_N': judge_attempts, 'judge_returns_N': judge_returns,
    'saved_case_results_N': len(results), 'technical_execution_attempt': 1,
    'matched_N': sum(r['values_matched'] for r in results),
    'numeric_unmatched_cases_N': sum(bool(r['numeric_mismatched_dimensions']) for r in results),
    'numeric_mismatched_dimensions_N': sum(len(r['numeric_mismatched_dimensions']) for r in results),
    'execution_exceptions_N': sum(r['execution_error'] is not None for r in results),
    'source_inspection_exceptions_N': sum(r['source_inspection_error'] is not None for r in results),
    'evidence_validator_passed_N': sum(r['evidence_validator_passed'] for r in results),
    'literal_quote_errors_N': sum(r['literal_quote_error'] is not None for r in results),
    'source_geometry_rows_N': sum(len(r['source_geometry_rows']) for r in geometry_results),
    'context_quotes_N': sum(len(r['context_quotes']) for r in geometry_results),
    'current_anchor_checks_N': sum(len(r['current_anchor_checks']) for r in geometry_results),
    'only_IF_natural_observed_units_N': sum(bool(u['details'].get('only_IF_consumers')) for r in results for u in r['observed_natural_units']),
    'typed_subset_natural_observed_units_N': sum('affected_dimensions' in u['details'] and set(u['details']['affected_dimensions']) != set(DIMS) for r in results for u in r['observed_natural_units']),
    'only_IF_accepted_positive_events_N': sum(bool(e['unit_details'].get('only_IF_consumers')) for r in results for e in r['accepted_positive_events']),
    'typed_subset_accepted_positive_events_N': sum('affected_dimensions' in e['unit_details'] and set(e['unit_details']['affected_dimensions']) != set(DIMS) for r in results for e in r['accepted_positive_events']),
    'accepted_positive_consumer_route_violations_N': sum(len(r['consumer_route_violations']) for r in results),
    'failed_case_names': [r['name'] for r in results if not r['values_matched']],
    'original_preparation_seal_unchanged': bind(PREP / 'preparation-seal.json')['sha256'] == EXPECTED_PREP,
    'original_controls_unchanged': bind(PREP / 'controls6-fixed-before-execution.json')['sha256'] == 'd8031632e7e5205f7cb1e15faa51fd0c435f06d147db4ce1ff926675cc5c6078',
    'parent_or_owner_answer_tables_read': False,
    'full77_800_4481_execution_N': 0, 'actual_human_validation_N': 0,
}
write('execution-summary.json', summary)
print(json.dumps(summary, ensure_ascii=False, allow_nan=False))

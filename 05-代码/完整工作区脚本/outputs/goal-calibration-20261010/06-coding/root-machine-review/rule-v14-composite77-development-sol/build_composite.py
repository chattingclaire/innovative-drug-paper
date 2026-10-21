#!/usr/bin/env python3
"""Copy exact sealed first-output lines into an explicitly mixed development result."""
import datetime
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
OUT = Path(__file__).resolve().parent
NEW = ROOT / '06-coding/development-rule-sol/coverage36/implementation09-source-v14-binding'
DIMS = ['S', 'E', 'Ec', 'I', 'F']


def bind(p):
    b = Path(p).read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


def verify(e):
    a = bind(e['path'])
    assert a['bytes'] == e['bytes'] and a['sha256'] == e['sha256'], e['path']
    return a


def load(p):
    return json.loads(Path(p).read_bytes())


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def lined(p, id_getter):
    result = []
    for ordinal, raw in enumerate(Path(p).read_bytes().splitlines(keepends=True), 1):
        item = json.loads(raw)
        result.append({'id': id_getter(item), 'item': item, 'raw': raw, 'line': ordinal, 'line_sha256': hashlib.sha256(raw).hexdigest()})
    assert len({x['id'] for x in result}) == len(result)
    return result


def save(name, value, jsonl=False):
    raw = ''.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) + '\n' for x in value) if jsonl else json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    with (OUT / name).open('xb') as f:
        f.write(raw.encode())


def ratio(a, b):
    if not b:
        return {'value': None, 'exact_fraction': None, 'undefined_reason': 'zero denominator'}
    x = Fraction(a, b)
    return {'value': float(x), 'exact_fraction': f'{x.numerator}/{x.denominator}', 'undefined_reason': None}


def calc(rows, references):
    results = {}
    for dim in DIMS:
        counts = {'TP': 0, 'FP': 0, 'FN': 0, 'TN': 0}
        binary = []
        for row in rows:
            p, t = row['item']['labels'][dim], references[row['id']]['item']['labels'][dim]
            if p is None or t is None:
                continue
            binary.append((p, t, row['id']))
            counts['TP' if p == 1 and t == 1 else 'FP' if p == 1 else 'FN' if t == 1 else 'TN'] += 1
        tp, fp, fn, tn = [counts[k] for k in ['TP', 'FP', 'FN', 'TN']]
        n = len(binary)
        chance = (tp + fn) * (tp + fp) + (tn + fp) * (tn + fn)
        results[dim] = {
            'assigned': len(rows), 'candidate_binary_decidable': sum(x['item']['labels'][dim] is not None for x in rows),
            'candidate_null': sum(x['item']['labels'][dim] is None for x in rows),
            'reference_null': sum(references[x['id']]['item']['labels'][dim] is None for x in rows),
            'paired_binary_n': n, 'technical_failed': sum(bool(x['item'].get('implementation_errors')) for x in rows),
            **counts, 'kappa': ratio(n * (tp + tn) - chance, n * n - chance),
            'P': ratio(tp, tp + fp), 'R': ratio(tp, tp + fn), 'F1': ratio(2 * tp, 2 * tp + fp + fn),
            'Po': ratio(tp + tn, n), 'Pe': ratio(chance, n * n),
            'Ppos': ratio(2 * tp, 2 * tp + fp + fn), 'Pneg': ratio(2 * tn, 2 * tn + fp + fn),
            'disagreement_ids': [sid for p, t, sid in binary if p != t],
        }
    return results


new_master_path = NEW / 'v14-final-delivery-bindings.json'
new_master_binding = bind(new_master_path)
assert new_master_binding['sha256'] == '217c78caab42917f50af79a53049220e997ae90cfa76022dad88c5dbeb4865ff'
master = load(new_master_path)
post_path = ROOT / 'logs/root-rule10-v14-postseal-reception-and-development-comparison-20261010.json'
post = load(post_path)
assert post['actual_rule10_final_master'] == new_master_binding
assert post['root_member_checks_N'] == 38 and post['all_match'] is True
old_master_binding = verify(master['previous_v09_master'])
old = load(old_master_binding['path'])
required_bindings = []


def checked(e):
    a = verify(e)
    if a not in required_bindings:
        required_bindings.append(a)
    return a


old_predictions = []
old_origin = {}
run_info = []
for scope in ['run-old41-01', 'run-old36-01']:
    entry = next(x for x in old['files'] if x['path'].endswith('/' + scope + '/predictions.jsonl'))
    pb = checked(entry)
    seal_entry = next(x for x in old['actual_run_seals'] if '/' + scope + '/' in x['path'])
    sb = checked(seal_entry)
    seal = load(sb['path'])
    assert seal['prediction_sha256'] == pb['sha256'] and seal['prediction_path'] == pb['path'] and seal['complete']
    rows = lined(pb['path'], lambda x: x['id'])
    assert [x['id'] for x in rows] == seal['record_ids'] and len(rows) == seal['prediction_n']
    for x in rows:
        old_origin[x['id']] = {'prediction_file': pb, 'run_seal': sb, 'runtime_version': seal['runtime_version'], 'scope_name': seal['scope_name']}
    old_predictions.extend(rows)
    run_info.append({'seal': sb, 'runtime_version': seal['runtime_version'], 'scope': seal['scope_name'], 'n': seal['prediction_n'], 'slots': seal['decision_n'], 'implementation_error_n': seal['implementation_error_n'], 'rules_null_n': seal['rules_null_n'], 'technical_failure_dimension_n': seal['technical_failure_dimension_n'], 'sealed_at_utc': seal['sealed_at_utc']})
assert len(old_predictions) == 77 and len(old_origin) == 77
new_pred_binding = checked(post['prediction'])
new_seal_binding = checked(master['actual_first_run_seal'])
new_seal = load(new_seal_binding['path'])
assert new_seal['prediction_sha256'] == new_pred_binding['sha256'] and new_seal['complete']
new_predictions = lined(new_pred_binding['path'], lambda x: x['id'])
changed_ids = master['approved_record_ids']
assert len(new_predictions) == 10 and [x['id'] for x in new_predictions] == changed_ids == new_seal['record_ids']
new_map = {x['id']: x for x in new_predictions}
old_map = {x['id']: x for x in old_predictions}

old_bundle_binding = checked(old['complete77_snapshot'])
new_bundle_entry = next(x for x in master['source_material_bindings'] if '/development77-common-v14/common-source-bundles.jsonl' in x['path'])
new_bundle_binding = checked(new_bundle_entry)
old_bundles = lined(old_bundle_binding['path'], lambda x: x['source_record']['id'])
new_bundles = lined(new_bundle_binding['path'], lambda x: x['source_record']['id'])
old_bmap = {x['id']: x for x in old_bundles}
new_bmap = {x['id']: x for x in new_bundles}
expected_order = [x['id'] for x in old_predictions]
assert expected_order == [x['id'] for x in old_bundles] == [x['id'] for x in new_bundles]
assert {x for x in expected_order if old_bmap[x]['item'] != new_bmap[x]['item']} == set(changed_ids)
finite_binding = checked(master['complete10_snapshot'])
finite = lined(finite_binding['path'], lambda x: x['source_record']['id'])
assert [x['id'] for x in finite] == changed_ids and all(x['item'] == new_bmap[x['id']]['item'] for x in finite)
delivered_entry = next(x for x in master['files'] if x['path'].endswith('/delivered-complete-source-bundles.jsonl'))
delivered_binding = checked(delivered_entry)
delivered = lined(delivered_binding['path'], lambda x: x['source_record']['id'])
assert [x['id'] for x in delivered] == changed_ids and all(x['item'] == new_bmap[x['id']]['item'] for x in delivered)
checked(master['manual_v1_3'])
assert old['manual_v1_3'] == master['manual_v1_3']
schema_bindings = [checked(x) for x in old['source_material_bindings'] if 'schema' in Path(x['path']).name]
checked(next(x for x in master['implementation_files'] if x['path'].endswith('/source_packet.py')))
checked(master['source_scope'])
checked(next(x for x in master['files'] if x['path'].endswith('/run-changed10-01/freeze.json')))
checked(next(x for x in master['files'] if x['path'].endswith('/run-changed10-01/execution.json')))
summary_entry = next(x for x in master['files'] if x['path'].endswith('/v14-actual-source-use-summary.json'))
summary_binding = checked(summary_entry)
summary = load(summary_binding['path'])
consumption_entry = next(x for x in master['files'] if x['path'].endswith('/actual-source-consumption.jsonl'))
consumption_binding = checked(consumption_entry)
consumption = lined(consumption_binding['path'], lambda x: x['id'])
leaf_ids = {x['resource_id'] for x in summary['unique_literal_resources']}
assert len(leaf_ids) == 5
leaf_audit, reads_total, selected_total = [], 0, 0
for x in consumption:
    log = x['item']['uniform_source_reading_log']
    source_sha = canonical_sha(new_bmap[x['id']]['item'])
    assert log['actual_full_source_bundle_sha256'] == source_sha
    reads = [v for v in log['read_receipts'] if v['resource_id'] in leaf_ids]
    uses = [v for v in log['use_receipts'] if v['resource_id'] in leaf_ids]
    reads_total += len(reads)
    selected_total += len(uses)
    assert len(reads) == 5 and len(uses) == 0
    leaf_audit.append({'id': x['id'], 'consumption_line': x['line'], 'consumption_line_sha256': x['line_sha256'], 'actual_full_source_bundle_sha256': source_sha, 'newleaf_program_text_read_n': len(reads), 'newleaf_selected_use_n': len(uses), 'newleaf_resource_ids_read': [v['resource_id'] for v in reads]})
assert reads_total == 50 and selected_total == 0
raw_leaf_headers = []
for resource in finite[0]['item']['source_full_text_resources']:
    if resource['source_resource_id'] in leaf_ids:
        assert resource['kind'] == 'verbatim_UTF8_snapshot_text'
        assert 'text_sha256' not in resource and 'source_locator' not in resource
        assert hashlib.sha256(resource['text'].encode()).hexdigest() == resource['text_utf8_sha256']
        raw_leaf_headers.append({k: v for k, v in resource.items() if k != 'text'})
assert len(raw_leaf_headers) == 5

reference_binding = checked(post['reference'])
references = {x['id']: x for x in lined(reference_binding['path'], lambda x: x['id'])}
assert set(references) == set(expected_order)
chosen, provenance, comparisons = [], [], []
for ordinal, original in enumerate(old_predictions, 1):
    sid = original['id']
    changed = sid in new_map
    row = new_map[sid] if changed else original
    origin = {'prediction_file': new_pred_binding, 'run_seal': new_seal_binding, 'runtime_version': new_seal['runtime_version'], 'scope_name': new_seal['scope_name']} if changed else old_origin[sid]
    assert row['raw'].endswith(b'\n')
    for value in row['item']['labels'].values():
        assert value is None or (type(value) is int and value in [0, 1])
    assert set(row['item']['labels']) == set(DIMS)
    chosen.append(row)
    old_sha = canonical_sha(old_bmap[sid]['item'])
    new_sha = canonical_sha(new_bmap[sid]['item'])
    assert changed or old_sha == new_sha
    actual_sha = new_sha if changed else old_sha
    provenance.append({
        'composite_ordinal_one_based': ordinal, 'id': sid,
        'component': 'new_v14_changed10_first' if changed else 'retained_v09_unchanged67_first',
        **origin, 'original_prediction_line_one_based': row['line'], 'original_prediction_line_sha256_including_newline': row['line_sha256'],
        'composite_line_identical_to_original_bytes': True,
        'actual_execution_source_bundle_sha256': actual_sha,
        'old_v09_source_bundle_sha256': old_sha, 'new_common_v14_source_bundle_sha256': new_sha,
        'bundle_same_between_v13_and_v14': old_sha == new_sha,
        'old_source_bundle_file': old_bundle_binding, 'old_bundle_line_one_based': old_bmap[sid]['line'],
        'new_common_v14_bundle_file': new_bundle_binding, 'new_bundle_line_one_based': new_bmap[sid]['line'],
        'old_original_source_ref': old_bmap[sid]['item']['source_record']['source_ref'],
        'new_common_original_source_ref': new_bmap[sid]['item']['source_record']['source_ref'],
        'original_source_ref_same': old_bmap[sid]['item']['source_record']['source_ref'] == new_bmap[sid]['item']['source_record']['source_ref'],
        'old67_rerun_by_v14_loader': False if not changed else None,
        'historical_reference_line_one_based': references[sid]['line'],
        'historical_reference_line_sha256_including_newline': references[sid]['line_sha256'],
    })
    if changed:
        comparisons.append({'id': sid, 'old_first_file': old_origin[sid]['prediction_file'], 'old_first_line': original['line'], 'old_first_line_sha256': original['line_sha256'], 'old_labels': original['item']['labels'], 'new_first_file': new_pred_binding, 'new_first_line': row['line'], 'new_first_line_sha256': row['line_sha256'], 'new_labels': row['item']['labels'], 'five_labels_equal': original['item']['labels'] == row['item']['labels'], 'full_line_bytes_equal': original['raw'] == row['raw']})
assert len(chosen) == 77 and len(provenance) == 77 and sum(x['component'].startswith('retained') for x in provenance) == 67
with (OUT / 'composite-predictions77.jsonl').open('xb') as f:
    f.write(b''.join(x['raw'] for x in chosen))
copied = (OUT / 'composite-predictions77.jsonl').read_bytes().splitlines(keepends=True)
assert copied == [x['raw'] for x in chosen]
save('provenance-rows77.jsonl', provenance, jsonl=True)
save('changed10-label-comparison.json', comparisons)
save('input-bindings.json', {
    'new_master': new_master_binding, 'ROOT_postseal_report': bind(post_path), 'old_v09_master': old_master_binding,
    'required_inputs_actually_SHA_bytes_checked': required_bindings,
    'new38_member_check_reused_from_ROOT': {'source': bind(post_path), 'N': 38, 'all_match': True, 'not_repeated_here': True},
    'old101_member_full_recheck_performed': False,
    'old_run_first_metadata': run_info,
    'new_run_first_metadata': {k: new_seal[k] for k in ['runtime_version', 'scope_name', 'sealed_at_utc', 'prediction_n', 'decision_n', 'implementation_error_n', 'rules_null_n', 'technical_failure_dimension_n', 'complete']},
    'same_manual_binding_old_and_new': master['manual_v1_3'], 'original_source_schema_bindings': schema_bindings,
    'ID_order': expected_order, 'ID_N': 77, 'duplicates': [], 'missing': [],
    'order_rule': 'Original v09 old41 first lines then old36 first lines; replace changed10 in the same positions with exact new first lines. Also equals common77 v13/v14 order.',
    'source_packet_raw_vs_alias': {
        'source_packet_binding': next(x for x in required_bindings if x['path'].endswith('/source_packet.py')),
        'raw_original_leaf_headers': raw_leaf_headers,
        'raw_preserved_fields': ['kind=verbatim_UTF8_snapshot_text', 'text_utf8_sha256', 'locator', 'text; unchanged Unicode/UTF8 source'],
        'semantic_copy_aliases': {'text_sha256': 'exact raw text_utf8_sha256', 'source_locator': 'deepcopy(raw locator)'},
        'static_code_location_one_based': [617, 626],
        'raw_alias_fields_absent': True, 'raw_finite_and_delivered_equal_common_v14': True,
        'program_newleaf_read_receipts': reads_total, 'newleaf_selected_use_receipts': selected_total,
        'newleaf_availability_instances': 50, 'newleaf_unique_resources': 5,
        'per_record': leaf_audit, 'read_use_are_not_human_or_semantic_gold': True,
        'source_producer_status_not_recorded_not_overwritten': True,
    },
    'preserved_auditor_failure_metadata': master['first_mechanical_review_assertion_failure_preserved'],
    'new_master_unchanged67_not_rerun_declaration': master['unchanged67_old_v09_first_judgments_retained_without_rerun'],
    'new_master_not_new77_first_run': master['not_new77_first_run'],
    'new_loader_executed_67_claim': False,
})
save('metrics-exact.json', {
    'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'result_kind': 'Explicitly mixed development execution: retained old v09/v13 first67 + new source-v14 changed10 first; not one new77 first execution.',
    'historically_exposed_nonprobability_AI_nonblind_ROOT_adjudicated_development_reference': True,
    'records': 77, 'slots': 385, 'components': {'old_v09_v13_retained_firsts': 67, 'new_v14_changed_firsts': 10},
    'new10_five_labels_same_as_old10': all(x['five_labels_equal'] for x in comparisons),
    'technical_failure_n': 0, 'candidate_null_n': sum(x['item']['labels'][d] is None for x in chosen for d in DIMS),
    'full77_per_dimension': calc(chosen, references),
    'new10_component_per_dimension': calc(new_predictions, references),
    'new10_component_is_separate_denominator': True,
    'confusion_orientation': 'reference target; TP candidate1/reference1; FP1/0; FN0/1; TN0/0',
    'formulas': {'kappa': '(Po-Pe)/(1-Pe)', 'Pe': '[(TP+FN)(TP+FP)+(TN+FP)(TN+FN)]/n^2', 'P': 'TP/(TP+FP)', 'R': 'TP/(TP+FN)', 'F1': '2TP/(2TP+FP+FN)', 'Po': '(TP+TN)/n', 'Ppos': '2TP/(2TP+FP+FN)', 'Pneg': '2TN/(2TN+FP+FN)'},
    'null_policy': 'Preserve null; either-side null excluded from binary denominator, no failure filled0.',
    'undefined_policy': 'Zero denominator => null/NA, not imputed as1. New10 S/Ec all0 have NA kappa/P/R/F1/Ppos, Po/Pneg=1.',
    'reference_file': reference_binding,
    'candidate_manual_sha256': master['manual_v1_3']['sha256'],
    'historical_reference_manual_sha256': sorted({x['item']['manual_sha256'] for x in references.values()}),
    'formal_acceptance': False, 'human_validation_or_semantic_gold': False, 'random_holdout': False, 'population_CI': None,
    'new77_same_execution_first': False, 'new_loader_ran_old67': False,
    'new_inference_or_native_model_calls_by_this_task': 0, 'old_large_tests_or_fullframe_QA_repeated': False,
    'analyst': 'AI /root/pilot01_a_sol, GPT-6.1 Sol ultra; prior A/source/technical and metric exposure; nonblind development reproduction only.',
})
print(json.dumps({'records': 77, 'slots': 385, 'old67_retained_exact_lines': 67, 'new10_first_exact_lines': 10, 'all_new10_labels_same_as_old': all(x['five_labels_equal'] for x in comparisons), 'newleaf_program_reads': reads_total, 'newleaf_selected': selected_total}))

"""Combine complete v7 results with the single sealed v8 affected-set execution.

Preserves actual prediction and slot bytes and explicit execution origins.
Does not claim a complete v8 inference pass or formal accuracy validation.
"""
from pathlib import Path
import collections, datetime, hashlib, json

R = Path(__file__).resolve().parents[1]
PARENT = R / '06-coding/rule-full4481-final-v7-root/run4481-first'
PREP = R / '06-coding/rule-v8-bounded-delta-root'
DELTA = PREP / 'run-affected-first'
OUT = R / '06-coding/rule-full4481-v8-delta-merged-root'
DIMS = ('S', 'E', 'Ec', 'I', 'F')


def bind(p):
    p = Path(p).resolve(); raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def exact(b):
    a = bind(b['path'])
    assert all(a[k] == b[k] for k in ('path', 'bytes', 'sha256')), b['path']


def load(p):
    return json.loads(Path(p).read_bytes())


def save(p, x):
    with Path(p).open('x', encoding='utf8') as f:
        json.dump(x, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')


def lines(p, slot=False):
    result = {}
    for raw in Path(p).read_bytes().splitlines(keepends=True):
        x = json.loads(raw); key = (x['id'], x['dimension']) if slot else x['id']
        assert key not in result
        result[key] = (x, raw)
    return result


def check_run(directory, status, N):
    seal = load(directory / 'seal.json')
    assert seal['status'] == status
    for k in ('output_files', 'implementation_files', 'material_bindings', 'control_inputs'):
        for b in seal[k]: exact(b)
    e = load(directory / 'execution.json')
    assert e['status'] == 'completed' and e['actual_record_N'] == N
    assert e['actual_dimension_N'] == N * 5 and e['technical_failure_dimension_N'] == 0
    assert seal['source_packet_unchanged'] and e['no_reference_read']
    return e


def main():
    assert not OUT.exists(), 'Never overwrite old actual or composite outputs'
    plan = load(PREP / 'impact-closure-plan.json')
    adoption = load(PREP / 'ROOT-pre-inference-adoption-sidecar.json')
    for k in ('candidate_total_seal', 'selection', 'impact_plan', 'frozen_scope', 'pre_execution_seal', 'original_input_lineage'):
        exact(adoption[k])
    for b in adoption['required_candidate_members_verified']: exact(b)
    assert adoption['provisional_delta_adoption_by_ROOT'] and adoption['same_independent_selector_set']
    parent_execution = check_run(PARENT, 'sealed_complete_production_provisional_rule_run', 4481)
    delta_N = plan['affected_record_N']
    delta_execution = check_run(DELTA, 'sealed_complete_production_provisional_rule_delta_run', delta_N)
    old = lines(PARENT / 'predictions.jsonl'); new = lines(DELTA / 'predictions.jsonl')
    old_slots = lines(PARENT / 'all-dimension-slots.jsonl', True)
    new_slots = lines(DELTA / 'all-dimension-slots.jsonl', True)
    assert len(old) == 4481 and len(old_slots) == 22405
    assert list(new) == plan['affected_record_ids'] and len(new) == delta_N
    assert len(new_slots) == delta_N * 5 and set(new) <= set(old)
    scope = load(PREP / 'frozen-scope.json')
    parent_scope = load(Path(load(PARENT / 'freeze.json')['control_inputs'][0]['path']))
    assert list(old) == parent_scope['approved_record_ids']
    assert scope['approved_record_ids'] == list(new)
    assert scope['manual'] == parent_scope['manual'] and scope['protocol'] == parent_scope['protocol']
    assert scope['prompt'] == parent_scope['prompt']
    before_after = []; decision_changed = []; request_changed = []
    for rid, (x, _) in new.items():
        y = old[rid][0]
        assert not x['implementation_errors'] and not y['implementation_errors']
        assert set(x['labels']) == set(y['labels']) == set(DIMS)
        for d in DIMS:
            assert x['labels'][d] == x['decisions'][d]['value']
            if d != 'F': assert x['decisions'][d] == y['decisions'][d], (rid, d)
            if x['labels'][d] != y['labels'][d]:
                before_after.append({'id': rid, 'dimension': d, 'parent_value': y['labels'][d], 'delta_value': x['labels'][d], 'parent_decision': y['decisions'][d], 'delta_decision': x['decisions'][d]})
            if x['decisions'][d] != y['decisions'][d]:
                decision_changed.append({'id': rid, 'dimension': d, 'value_changed': x['labels'][d] != y['labels'][d]})
        for k in ('source_requests', 'source_relation_traces', 'relation_traces'):
            if x.get(k) != y.get(k): request_changed.append({'id': rid, 'field': k})
    OUT.mkdir()
    lineage = []; counts = {d: collections.Counter() for d in DIMS}
    with (OUT / 'predictions.jsonl').open('xb') as p, (OUT / 'all-dimension-slots.jsonl').open('xb') as s:
        for i, rid in enumerate(old, 1):
            actual = DELTA if rid in new else PARENT
            x, raw = (new if rid in new else old)[rid]
            p.write(raw)
            slot_dict = new_slots if rid in new else old_slots
            for d in DIMS:
                slot, slot_raw = slot_dict[(rid, d)]
                assert slot['rule_value'] == x['labels'][d] and not slot['technical_failure']
                s.write(slot_raw)
                counts[d]['positive_N' if x['labels'][d] == 1 else 'negative_N' if x['labels'][d] == 0 else 'lawful_null_N'] += 1
            lineage.append({'corpus_ordinal_1based': i, 'id': rid, 'actual_inference_algorithm': 'joint-v8-target-product-gap-sol' if rid in new else 'joint-v7-relation-content-sol', 'actual_run_directory': str(actual), 'actual_prediction_line_sha256': hashlib.sha256(raw).hexdigest(), 'prediction_line_bytes': len(raw), 'unchanged_actual_record_bytes_retained': True, 'v8_compatibility_basis': 'actual_v8_delta_inference' if rid in new else 'unchanged_input_and_proved_changed_branch_not_reached', 'source_consumption_log': str(actual / 'actual-source-consumption.jsonl'), 'source_consumption_record_key': rid})
    with (OUT / 'execution-origin-lineage.jsonl').open('x', encoding='utf8') as f:
        for x in lineage: f.write(json.dumps(x, ensure_ascii=False, allow_nan=False) + '\n')
    save(OUT / 'v7-to-v8-actual-changes.json', {'label_changes': before_after, 'complete_decision_changes': decision_changed, 'source_or_relation_log_changes': request_changed, 'other_four_dimensions_all_identical': True})
    status = {'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'complete_v8_compatible_composite_with_explicit_execution_origins', 'actual_record_N': 4481, 'actual_dimension_N': 22405, 'technical_failure_dimension_N': 0, 'lawful_null_N': sum(c['lawful_null_N'] for c in counts.values()), 'counts': {d: {k: c[k] for k in ('positive_N', 'negative_N', 'lawful_null_N')} for d, c in counts.items()}, 'actual_v7_full_inference_record_N': parent_execution['actual_record_N'], 'actual_v8_delta_inference_record_N': delta_execution['actual_record_N'], 'inherited_v7_record_N': len(old)-len(new), 'all4481_actually_inferred_under_v8': False, 'label_change_N_v7_to_v8': len(before_after), 'decision_change_N_v7_to_v8': len(decision_changed), 'no_reference_read_by_classifier': True, 'reference_comparison_NOT_executed_by_merge': True, 'formal_validation_complete': False, 'human_validation_complete': False, 'paper_writing_gate_open': False, 'parent_seal': bind(PARENT / 'seal.json'), 'delta_seal': bind(DELTA / 'seal.json'), 'impact_closure_plan': bind(PREP / 'impact-closure-plan.json'), 'adoption': bind(PREP / 'ROOT-pre-inference-adoption-sidecar.json'), 'original_input_lineage': bind(PREP / 'original-input-lineage-sidecar.json'), 'merger': bind(__file__)}
    save(OUT / 'composite-status.json', status)
    save(OUT / 'seal.json', {'status': status['status'], 'files': [bind(p) for p in sorted(OUT.iterdir()) if p.is_file()], 'self_excluded': True, 'ancestor_seals': [status['parent_seal'], status['delta_seal']], 'no_new_inference_executed_by_merge': True, 'all4481_actually_inferred_under_v8': False, 'formal_validation_complete': False})
    print(json.dumps({k: status[k] for k in ('actual_record_N', 'actual_dimension_N', 'actual_v8_delta_inference_record_N', 'inherited_v7_record_N', 'lawful_null_N', 'label_change_N_v7_to_v8', 'decision_change_N_v7_to_v8')}, ensure_ascii=False))


if __name__ == '__main__':
    main()

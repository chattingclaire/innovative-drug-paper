"""Post-seal comparison of old/new machine results only. No reference scores."""
import collections, datetime, hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / '06-coding/rule-v18-overall-health-boundary-development-root/run77-first'
NEW = HERE / 'run77-once'
def binding(p):
    p = Path(p).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
def read(p):
    return json.loads(Path(p).read_bytes())
def rows(p):
    return [json.loads(line) for line in Path(p).read_bytes().splitlines()]
def verify(b):
    actual = binding(b['path'])
    if any(actual[k] != b[k] for k in ('path', 'sha256', 'bytes')):
        raise ValueError('sealed result changed: ' + b['path'])
    return actual
oldseal, newseal = read(OLD / 'seal.json'), read(NEW / 'seal.json')
old_files = oldseal.get('output_files', oldseal.get('files', []))
new_files = newseal.get('output_files', newseal.get('files', []))
oldverified, newverified = [verify(b) for b in old_files], [verify(b) for b in new_files]
op, np = rows(OLD / 'predictions.jsonl'), rows(NEW / 'predictions.jsonl')
oslots, nslots = rows(OLD / 'all-dimension-slots.jsonl'), rows(NEW / 'all-dimension-slots.jsonl')
oc, nc = rows(OLD / 'actual-source-consumption.jsonl'), rows(NEW / 'actual-source-consumption.jsonl')
if [p['id'] for p in op] != [p['id'] for p in np]:
    raise ValueError('old/new machine record order differs')
if [(s['id'], s['dimension']) for s in oslots] != [(s['id'], s['dimension']) for s in nslots]:
    raise ValueError('old/new machine dimension slot order differs')
DIMS = ('S', 'E', 'Ec', 'I', 'F')
label_changes, mask_changes, positive_changes, decision_audit_changes = [], [], [], []
for a, b in zip(op, np):
    if a['labels'] != b['labels']:
        label_changes.append({'id': a['id'], 'old': a['labels'], 'candidate': b['labels']})
    for d in DIMS:
        ad, bd = (a.get('decisions') or {}).get(d), (b.get('decisions') or {}).get(d)
        if ad is None or bd is None:
            continue
        if ad.get('value') == 1 and any(ad.get(k) != bd.get(k) for k in ('value', 'basis_path', 'current_anchor', 'current_proposition', 'context_evidence', 'reason')):
            positive_changes.append({'id': a['id'], 'dimension': d})
        if ad.get('details') != bd.get('details'):
            olddetails, newdetails = ad.get('details', {}), bd.get('details', {})
            decision_audit_changes.append({'id': a['id'], 'dimension': d, 'changed_detail_keys': sorted(k for k in set(olddetails) | set(newdetails) if olddetails.get(k) != newdetails.get(k)), 'candidate_route_N': len(newdetails.get('material_request_routes', [])), 'needed_material_equal': ad.get('needed_material') == bd.get('needed_material')})
for a, b in zip(oslots, nslots):
    fields = ('status', 'technical_failure', 'rules_null', 'rule_value', 'comparison_eligible')
    if any(a[k] != b[k] for k in fields):
        mask_changes.append({'id': a['id'], 'dimension': a['dimension'], 'old': {k: a[k] for k in fields}, 'candidate': {k: b[k] for k in fields}})
consumption_changes = []
counts = {'old': collections.Counter(), 'candidate': collections.Counter()}
for a, b in zip(oc, nc):
    if a['id'] != b['id']:
        raise ValueError('consumption record order differs')
    fields = ('actual_text_geometry_events', 'source_relation_traces', 'source_requests', 'material_requests')
    changed = [k for k in fields if a.get(k) != b.get(k)]
    if changed:
        consumption_changes.append({'id': a['id'], 'changed_fields': changed})
    for tag, row in (('old', a), ('candidate', b)):
        log = row.get('uniform_source_reading_log') or {}
        counts[tag]['actual_text_geometry_events'] += len(row.get('actual_text_geometry_events', []))
        counts[tag]['source_relation_traces'] += len(row.get('source_relation_traces', []))
        counts[tag]['material_requests'] += len(row.get('material_requests', []))
        counts[tag]['source_requests'] += len(row.get('source_requests', []))
        counts[tag]['read_receipts'] += len(log.get('read_receipts', []))
        counts[tag]['use_receipts'] += len(log.get('use_receipts', []))
        counts[tag]['available_returned_source_logs'] += bool(row.get('uniform_source_reading_log'))
        counts[tag]['available_returned_source_checks'] += bool(row.get('uniform_source_protocol_check'))
        counts[tag]['image_read_N'] += row.get('image_read_N', 0)
oe, ne = read(OLD / 'execution.json'), read(NEW / 'execution.json')
value_counts = {d: {'old': dict(collections.Counter(str((p.get('labels') or {}).get(d)) for p in op)), 'candidate': dict(collections.Counter(str((p.get('labels') or {}).get(d)) for p in np))} for d in DIMS}
old_code_reads = set(oe['read_paths'])
new_code_reads = set(ne['read_paths'])
materials = read(HERE / 'development77-source-scope.json')['material_bindings']
material_paths = {b['path'] for b in materials}
runtime_material_reads_equal = old_code_reads & material_paths == new_code_reads & material_paths
summary = {'status': 'post_seal_machine_only_comparison', 'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'comparison_authorized_after_candidate_execution_seal': True, 'old_run_seal_binding': binding(OLD / 'seal.json'), 'new_run_seal_binding': binding(NEW / 'seal.json'), 'old_outputs_seal_actual_bindings_verified': oldverified, 'new_outputs_seal_actual_bindings_verified': newverified, 'old_outputs_modified': False, 'old800_source_or_results_read': False, 'reference_Gold_A_B_or_new_calibration_read': False, 'human_independent_label_N': 0, 'actual_candidate_driver_process_launch_N': 1, 'actual_record_N': len(np), 'actual_dimension_N': len(nslots), 'old_execution_summary': {k: oe.get(k) for k in ('status', 'actual_record_N', 'actual_dimension_N', 'technical_failure_dimension_N', 'lawful_null_N', 'retained_decision_N', 'actual_cohort_inference_runs', 'no_reference_read')}, 'candidate_execution_summary': {k: ne.get(k) for k in ('status', 'actual_record_N', 'actual_dimension_N', 'technical_failure_dimension_N', 'lawful_null_N', 'retained_decision_N', 'actual_cohort_inference_runs', 'no_reference_read', 'execution_purpose')}, 'value_counts_by_dimension': value_counts, 'record_label_change_N': len(label_changes), 'record_label_changes': label_changes, 'dimension_value_failure_mask_change_N': len(mask_changes), 'dimension_value_failure_mask_changes': mask_changes, 'original_positive_evidence_or_reason_change_N': len(positive_changes), 'original_positive_evidence_or_reason_changes': positive_changes, 'decision_audit_detail_change_N': len(decision_audit_changes), 'decision_audit_detail_changes': decision_audit_changes, 'consumption_relation_request_change_record_N': len(consumption_changes), 'consumption_relation_request_changes': consumption_changes, 'source_consumption_counts': {k: dict(v) for k, v in counts.items()}, 'actual_runtime_material_read_paths_equal': runtime_material_reads_equal, 'runtime_read_path_difference': {'old_only': sorted(old_code_reads-new_code_reads), 'candidate_only': sorted(new_code_reads-old_code_reads)}, 'available_source_materials_not_claimed_read': True, 'semantic_validity_or_human_reliability_inferred': False, 'formal_validation_complete': False, 'human_validation_complete': False, 'no_final_freeze_claimed': True}
with (HERE / 'machine-comparison.json').open('x', encoding='utf8') as f:
    f.write(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: summary[k] for k in ('actual_record_N', 'actual_dimension_N', 'record_label_change_N', 'dimension_value_failure_mask_change_N', 'original_positive_evidence_or_reason_change_N', 'decision_audit_detail_change_N', 'consumption_relation_request_change_record_N', 'actual_runtime_material_read_paths_equal')}, ensure_ascii=False))
print(json.dumps({'old_execution': summary['old_execution_summary'], 'candidate_execution': summary['candidate_execution_summary'], 'source_consumption_counts': summary['source_consumption_counts']}, ensure_ascii=False))

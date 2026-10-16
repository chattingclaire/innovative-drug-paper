"""Read-only, result-blind comparison of declared old/new source inputs."""
from pathlib import Path
import collections
import hashlib
import json

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
OLD = ROOT / '06-coding/native-full4481-v1-sol'
NEW = ROOT / '06-coding/common-material-new-batch-plan-sol'
MATERIAL = ROOT / '03-manual/common-material-projection-candidate-root'
OUT = Path(__file__).resolve().parent


def canonical(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def h(raw):
    return hashlib.sha256(raw).hexdigest()


def load(p):
    return json.loads(Path(p).read_bytes())


def bind(p):
    p = Path(p).resolve(); raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': h(raw)}


def verify(b):
    assert bind(b['path']) == b, b


def write(name, v):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(v, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


manifest = load(OLD / 'run-manifest.json')
plan = load(NEW / 'batch-plan.json')
inventory = load(MATERIAL / 'packet-inventory.json')
candidate_seal = load(NEW / 'output-seal.json')
assert len(inventory) == manifest['record_N'] == plan['record_N'] == 4481
assert manifest['context_unit'] == 'batch'
assert manifest['batch_N'] == 504 and plan['batch_N'] == 659
assert candidate_seal['member_N'] == len(candidate_seal['output_members']) == 1329
for m in candidate_seal['output_members']:
    verify(m)
old_assignments = []
old_records = {}
old_context = {}
old_batches = {}
for b in manifest['batches']:
    verify(b['assignment'])
    a = load(b['assignment']['path'])
    assert a['context_unit'] == 'batch'
    assert a['requested_model'] == manifest['requested_model'] and a['requested_reasoning_effort'] == manifest['requested_reasoning_effort']
    for k in ('manual', 'execution_prompt', 'run_scope_binding', 'actor_instructions'):
        verify(a[k])
    assert a['manual'] == manifest['manual'] and a['execution_prompt'] == manifest['execution_prompt'] and a['run_scope_binding'] == manifest['protocol']
    ids = tuple(b['source_ids'])
    assert ids == tuple(x['source_id'] for x in a['packets'])
    old_batches[ids] = b['batch_id']
    for rec in a['packets']:
        assert rec['source_id'] not in old_records
        raw = Path(rec['path']).read_bytes()
        assert len(raw) == rec['bytes'] and h(raw) == rec['sha256']
        packet = json.loads(raw)
        assert h(canonical(packet['source_bundle'])) == packet['source_bundle_sha256'] == rec['source_bundle_sha256']
        assert len(canonical(packet['source_bundle'])) == rec['source_bundle_utf8_bytes']
        old_records[rec['source_id']] = {'binding': {k: rec[k] for k in ('path', 'bytes', 'sha256')}, 'raw': raw, 'packet': packet}
        old_context[rec['source_id']] = ids
    old_assignments.append(b['assignment'])
assert len(old_records) == 4481

new_records = {}
new_context = {}
new_batches = {}
for b in plan['batches']:
    verify(b['source_only_complete_inputs'])
    raw = Path(b['source_only_complete_inputs']['path']).read_bytes()
    lines = raw.splitlines(keepends=True)
    assert len(lines) == b['record_N']
    ids = tuple(b['source_ids']); new_batches[ids] = b['batch_id']
    for line, rec in zip(lines, b['records']):
        packet = json.loads(line)
        verify(rec['candidate_packet_binding'])
        packet_raw = Path(rec['candidate_packet_binding']['path']).read_bytes()
        assert packet == json.loads(packet_raw)
        assert line == canonical(packet) + b'\n'
        assert h(line) == rec['compact_whole_packet_line_sha256']
        assert len(line) == rec['compact_whole_packet_line_bytes']
        assert packet['source_id'] == rec['source_id']
        assert rec['source_id'] not in new_records
        new_records[rec['source_id']] = {'binding': rec['candidate_packet_binding'], 'raw': packet_raw, 'line': line, 'packet': packet}
        new_context[rec['source_id']] = ids
assert list(old_records) == list(new_records) == [x['source_id'] for x in inventory]

rows = []
outer_fields = collections.Counter()
bundle_fields = collections.Counter()
classifications = collections.Counter()
old_bytes = compact_old_bytes = new_raw_bytes = compact_new_bytes = 0
for item in inventory:
    sid = item['source_id']; old = old_records[sid]; new = new_records[sid]
    assert old['binding'] == item['parent_packet'] and new['binding'] == item['packet_binding']
    a, b = old['packet'], new['packet']
    ab, bb = a['source_bundle'], b['source_bundle']
    inner_same = canonical(ab) == canonical(bb)
    assert inner_same == (not item['material_interface_changed'])
    assert h(canonical(bb)) == b['source_bundle_sha256'] == item['source_bundle_sha256']
    changed_outer = sorted(k for k in set(a) | set(b) if k != 'source_bundle' and (k not in a or k not in b or a[k] != b[k]))
    changed_inner = sorted(k for k in set(ab) | set(bb) if k not in ab or k not in bb or ab[k] != bb[k])
    outer_fields.update(changed_outer); bundle_fields.update(changed_inner)
    assert ab['source_record'] == bb['source_record']
    same_context_members = old_context[sid] == new_context[sid]
    all_context_material_same = same_context_members and all(canonical(old_records[x]['packet']['source_bundle']) == canonical(new_records[x]['packet']['source_bundle']) for x in old_context[sid])
    category = 'material_changed' if not inner_same else ('inner_unchanged_same_ordered_batch_all_inner_material_same' if all_context_material_same else 'inner_unchanged_same_ordered_batch_with_changed_neighbor' if same_context_members else 'inner_unchanged_different_batch_members')
    classifications[category] += 1
    rows.append({'source_id': sid, 'output_id': a['output_id'],
                 'old_packet': old['binding'], 'candidate_packet': new['binding'],
                 'old_compact_packet_sha256': h(canonical(a)), 'candidate_compact_packet_sha256': h(canonical(b)),
                 'old_compact_line_sha256': h(canonical(a) + b'\n'), 'candidate_actual_line_sha256': h(new['line']),
                 'old_source_bundle_sha256': h(canonical(ab)), 'new_source_bundle_sha256': h(canonical(bb)),
                 'whole_file_bytes_equal': old['raw'] == new['raw'],
                 'whole_compact_packet_bytes_equal': canonical(a) == canonical(b),
                 'inner_source_bundle_bytes_equal': inner_same, 'source_record_exact_equal': True,
                 'outer_changed_fields': changed_outer, 'inner_changed_fields': changed_inner,
                 'old_batch_id': old_batches[old_context[sid]], 'new_batch_id': new_batches[new_context[sid]],
                 'ordered_batch_members_equal': same_context_members,
                 'all_inner_material_in_same_batch_equal': all_context_material_same,
                 'material_and_context_category': category,
                 'reuse_authorized_by_this_audit': False})
    old_bytes += len(old['raw']); compact_old_bytes += len(canonical(a)) + 1
    new_raw_bytes += len(new['raw']); compact_new_bytes += len(new['line'])
same_groups = set(old_batches) & set(new_batches)
same_groups_material = [ids for ids in same_groups if all(canonical(old_records[sid]['packet']['source_bundle']) == canonical(new_records[sid]['packet']['source_bundle']) for sid in ids)]
core_diffs = []
for name, key in [('manual.txt', 'manual'), ('execution-prompt.txt', 'execution_prompt'), ('common-execution-protocol.txt', 'protocol')]:
    old_b = manifest[key]; new_b = bind(MATERIAL / name)
    verify(old_b)
    assert Path(old_b['path']).read_bytes() == Path(new_b['path']).read_bytes()
    core_diffs.append({'field': key, 'old': old_b, 'candidate_copy': new_b, 'exact_bytes_equal': True, 'path_differs': old_b['path'] != new_b['path']})
summary = {
    'status': 'read_only_execution_planning_no_reuse_authorization',
    'record_N': 4481, 'native_assignment_N_verified': 504,
    'candidate_seal_members_N_verified': 1329, 'candidate_input_batch_N_verified': 659,
    'old_and_new_packet_N_each_verified': 4481,
    'source_record_exact_equal_N': 4481,
    'inner_source_bundle_unchanged_N': sum(r['inner_source_bundle_bytes_equal'] for r in rows),
    'inner_source_bundle_changed_N': sum(not r['inner_source_bundle_bytes_equal'] for r in rows),
    'whole_packet_file_byte_equal_N': sum(r['whole_file_bytes_equal'] for r in rows),
    'whole_compact_packet_byte_equal_N': sum(r['whole_compact_packet_bytes_equal'] for r in rows),
    'outer_changed_field_counts': dict(outer_fields),
    'inner_changed_field_counts': dict(bundle_fields),
    'record_categories': dict(classifications),
    'same_ordered_batch_group_N': len(same_groups),
    'same_ordered_batch_all_inner_material_equal_group_N': len(same_groups_material),
    'same_ordered_batch_all_inner_material_equal_record_N': sum(map(len, same_groups_material)),
    'old_actual_packet_file_bytes_sum': old_bytes,
    'old_compact_packet_plus_LF_sum': compact_old_bytes,
    'candidate_actual_packet_file_bytes_sum': new_raw_bytes,
    'candidate_actual_compact_packet_plus_LF_sum': compact_new_bytes,
    'core_differences': core_diffs,
    'old_requested_model': manifest['requested_model'], 'old_requested_reasoning_effort': manifest['requested_reasoning_effort'],
    'old_context_unit': manifest['context_unit'], 'candidate_batch_N': 659,
    'candidate_final_runtime_model_settings_or_actor_assignment_available': False,
    'candidate_core_is_copied_preparation_not_new_release': True,
    'provider_wire_body_or_full_tool_context_compared': False,
    'actual_model_outputs_or_partial_labels_read_N': 0,
    'model_execution_or_retry_or_selection_performed_N': 0,
    'protocol_modified_or_scope_registered': False,
    'reuse_or_GO_authorized': False,
}
write('record-byte-and-context-comparison.json', {'records': rows})
write('summary.json', summary)
write('input-bindings.json', {'native_manifest': bind(OLD / 'run-manifest.json'),
                             'candidate_plan': bind(NEW / 'batch-plan.json'),
                             'candidate_inventory': bind(MATERIAL / 'packet-inventory.json'),
                             'candidate_output_seal': bind(NEW / 'output-seal.json'),
                             'native_assignment_bindings': old_assignments,
                             'candidate_builder': bind(NEW / 'build_candidate_batch_plan.py'),
                             'native_actor_instructions': manifest['actor_instructions'],
                             'core_comparisons': core_diffs,
                             'source_only_inputs_not_labels': True})
print(json.dumps({k: v for k, v in summary.items() if k != 'core_differences'}, ensure_ascii=False))

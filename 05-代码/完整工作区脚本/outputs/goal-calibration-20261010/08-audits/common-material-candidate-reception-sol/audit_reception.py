#!/usr/bin/env python3
"""Read-only source candidate reception and compact-byte budget analysis.

No producer, classification function, model runner, or dispatch is called.
Outputs are exclusive creations under this independent audit directory.
"""
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
CAND = ROOT / '03-manual/common-material-projection-candidate-root'
OWNER = ROOT / '06-coding/rule-v20-semantic-audit-repair-sol'
CAT = OWNER / 'neutral-material-projection-candidate'
PRIOR = ROOT / '08-audits/neutral-common-projection-independent-sol'
PREP = ROOT / '06-coding/full4481-common-v15-production-preparation-sol'
OLD = ROOT / '03-manual/full4481-common-release-20261010-root'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':')).encode('utf8')


def load(path):
    return json.loads(Path(path).read_bytes())


def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


inputs = {}


def checked(bound):
    actual = bind(bound['path'])
    assert actual == {k: bound[k] for k in ('path', 'bytes', 'sha256')}, bound['path']
    inputs[actual['path']] = actual
    return actual


def own_input(path):
    actual = bind(path)
    inputs[actual['path']] = actual
    return actual


def write(name, value):
    with (OUT / name).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


seal = load(CAND / 'output-seal.json')
own_input(CAND / 'output-seal.json')
assert seal['status'] == 'candidate_preparation_sealed_not_released'
assert seal['self_excluded'] is True
assert len(seal['output_members']) == 9
for member in seal['output_members']:
    checked(member)
checked(seal['parent_manifest'])
checked(seal['independent_projection_audit'])
manifest = load(CAT / 'release-candidate-manifest.json')
checked(manifest['builder_binding'])
for item in manifest['inventory_bindings']:
    checked(item)
for item in load(PRIOR / 'output-seal.json')['output_members']:
    checked(item)
provenance = load(CAND / 'preparation-provenance.json')
for key in ('projection', 'catalog', 'catalog_independent_audit',
            'old_common_freeze', 'builder'):
    checked(provenance[key])
assert provenance['projection'] == manifest['builder_binding']
assert provenance['status'] == 'preparation_only_not_common_release_or_execution'
assert provenance['label_or_prediction_files_read'] is False
assert provenance['new_model_dispatch_N'] == 0
freeze = load(OLD / 'common-input-freeze.json')
common = []
for field, name in (('manual', 'manual.txt'), ('prompt', 'execution-prompt.txt'),
                    ('protocol', 'common-execution-protocol.txt')):
    old_binding = checked(freeze[field])
    new_binding = own_input(CAND / name)
    assert Path(old_binding['path']).read_bytes() == Path(new_binding['path']).read_bytes()
    common.append({'role': field, 'old': old_binding, 'candidate': new_binding,
                   'exact_original_bytes': True})

roles = load(CAND / 'equal-visibility-role-bindings.json')
inventory_binding = own_input(CAND / 'packet-inventory.json')
assert roles['shared_packet_inventory'] == inventory_binding
assert set(roles['role_inventory_bindings']) == {
    'human_A', 'human_B', 'rule', 'LLM', 'adjudication_reference'}
assert all(bound == inventory_binding for bound in roles['role_inventory_bindings'].values())
assert roles['status'] == 'prepared_only_no_actual_role_delivery'
assert roles['human_independence_or_model_execution_claimed'] is False
summary_declared = load(CAND / 'summary.json')
assert summary_declared['actual_release_or_coder_delivery'] is False
assert summary_declared['actual_new_human_results'] == 0
assert summary_declared['actual_new_rule_or_LLM_coding_runs'] == 0

catalog = {}
for line in (CAT / 'bound-original-resources.jsonl').read_text().splitlines():
    row = json.loads(line)
    checked(row['original_binding'])
    raw = Path(row['original_binding']['path']).read_bytes()
    text = raw.decode('utf8', errors='strict')
    assert raw == text.encode() == row['text'].encode()
    assert sha(raw) == row['source_sha256']
    catalog[row['source_sha256']] = {'row': row, 'raw': raw, 'text': text}
delivery = load(CAND / 'original-delivery-map.json')
assert len(catalog) == len(delivery) == 17
portable = {}
copy_checks = []
for row in delivery:
    original = checked(row['original_provenance_binding'])
    copied = checked(row['candidate_copy'])
    expected_path = (CAND / row['relative_copy']).resolve()
    assert expected_path == Path(copied['path'])
    assert expected_path.is_relative_to(CAND.resolve())
    assert original['bytes'] == copied['bytes'] and original['sha256'] == copied['sha256']
    assert Path(original['path']).read_bytes() == Path(copied['path']).read_bytes()
    assert row['locator_rewritten'] is False
    key = original['sha256']
    assert key not in portable and catalog[key]['row']['original_binding'] == original
    portable[key] = row
    copy_checks.append({**row, 'actual_bytes_equal': True, 'strict_UTF8_roundtrip': True,
                        'original_locator_preserved': True,
                        'relative_copy_resolves_within_candidate': True})
assert set(portable) == set(catalog)
assert {Path(x['candidate_copy']['path']).resolve() for x in delivery} == {
    p.resolve() for p in (CAND / 'bound-UTF8-originals').glob('*.txt')}

code = Path(manifest['builder_binding']['path'])
ns = {'__name__': 'independent_read_only_neutral_projection', '__file__': str(code)}
exec(compile(code.read_bytes(), str(code), 'exec'), ns)
parent_inventory = load(CAT / 'packet-input-bindings.json')
route_by_id = {row['source_id']: row for row in load(CAT / 'record-material-routes.json')}
inventory = load(CAND / 'packet-inventory.json')
old_prepared = load(PREP / 'packet-bindings.json')
old_plan = load(PREP / 'batch-plan.json')
frame = load(PREP / 'frame-order.json')
for name in ('prepare-full4481.py', 'packet-bindings.json', 'batch-plan.json',
             'frame-order.json', 'candidate-core-bindings.json'):
    own_input(PREP / name)
assert old_plan['packet_byte_limit'] == 260000 and old_plan['max_records'] == 12
assert len(parent_inventory) == len(route_by_id) == len(inventory) == len(old_prepared) == 4481
assert [row['source_id'] for row in inventory] == frame['source_ids']
assert [row['source_id'] for row in old_prepared] == frame['source_ids']
assert len(set(frame['source_ids'])) == 4481
assert {Path(x['packet_binding']['path']).resolve() for x in inventory} == {
    p.resolve() for p in (CAND / 'packets').glob('*.json')}
assert all(item['parent_packet'] == parent for item, parent in zip(inventory, parent_inventory))

checks, measures = [], []
counts = Counter()
for item, old_metric in zip(inventory, old_prepared):
    new_binding = checked(item['packet_binding'])
    parent_binding = checked(item['parent_packet'])
    checked(old_metric)
    assert new_binding['path'] == str((CAND / item['relative_packet']).resolve())
    assert Path(new_binding['path']).is_relative_to((CAND / 'packets').resolve())
    old_raw = Path(parent_binding['path']).read_bytes()
    old = json.loads(old_raw)
    assert Path(old_metric['path']).read_bytes() == old_raw
    # This equality establishes the original preparation's actual metering,
    # not a text-body approximation or pretty-JSON file-size inference.
    assert old_raw == canon(old) + b'\n'
    new_raw = Path(new_binding['path']).read_bytes()
    new = json.loads(new_raw)
    bundle, projected = old['source_bundle'], new['source_bundle']
    sid = item['source_id']
    assert sid == old['source_id'] == new['source_id'] == bundle['source_record']['id']
    assert sid == projected['source_record']['id'] == Path(new_binding['path']).stem
    assert item['output_id'] == old['output_id'] == new['output_id']
    assert sha(canon(bundle)) == old['source_bundle_sha256']
    assert sha(canon(projected)) == new['source_bundle_sha256'] == item['source_bundle_sha256']
    expected, receipt = ns['project'](bundle)
    assert receipt == {k: v for k, v in route_by_id[sid].items() if k != 'source_id'}
    assert projected == expected
    assert projected['source_record'] == bundle['source_record']
    old_n = len(bundle['source_full_text_resources'])
    assert projected['source_full_text_resources'][:old_n] == bundle['source_full_text_resources']
    unchanged = set(bundle) - {'source_full_text_resources', 'common_source_bundle_version',
                              'source_bundle_extension'}
    assert all(projected[k] == bundle[k] for k in unchanged)
    expected_envelope = copy.deepcopy(old)
    expected_envelope.update({
        'packet_version': 'common-neutral-UTF8-projection-preparation-1',
        'source_bundle': expected, 'source_bundle_sha256': sha(canon(expected)),
        'common_material_candidate_provenance': {
            'status': 'candidate_not_released', 'parent_packet': item['parent_packet'],
            'projection_version': ns['VERSION'],
            'material_interface_changed': receipt['material_interface_changed'],
            'actual_consumer_read_or_execution_recorded': False, 'source_only': True}})
    assert new == expected_envelope
    additions = projected['source_full_text_resources'][old_n:]
    assert len(additions) == item['added_literal_resource_N'] == len(receipt['added_resources'])
    assert item['material_interface_changed'] is receipt['material_interface_changed']
    range_checks = []
    expected_ranges = []
    for doc in bundle['source_documents']:
        snapshot = Path(doc['snapshot'])
        if snapshot.suffix.lower() != '.txt':
            continue
        key = doc['source_sha256']
        original = catalog[key]
        raw, text = original['raw'], original['text']
        assert str(snapshot.resolve()) == original['row']['original_binding']['path']
        assert snapshot.resolve().is_relative_to((ROOT / '00-baseline/source-files').resolve())
        assert doc['bytes'] == len(raw) and doc['source_resource_id'] == 'SOURCE-' + key
        existing = []
        for leaf in bundle['source_full_text_resources']:
            if leaf.get('kind') == 'verbatim_UTF8_snapshot_text' and leaf['source_sha256'] == key:
                a, b = leaf['locator']['unicode_code_point_interval_half_open']
                assert type(a) is type(b) is int and 0 <= a < b <= len(text)
                assert leaf['text'] == text[a:b]
                assert sha(leaf['text'].encode()) == leaf['text_utf8_sha256']
                existing.append((a, b))
        existing.sort()
        assert all(a[1] <= b[0] for a, b in zip(existing, existing[1:]))
        gaps, cursor = [], 0
        for a, b in existing:
            if cursor < a:
                gaps.append((cursor, a))
            cursor = b
        if cursor < len(text):
            gaps.append((cursor, len(text)))
        new_leaves = [z for z in additions if z['source_sha256'] == key]
        assert len(new_leaves) == len(gaps)
        for leaf, (a, b) in zip(new_leaves, gaps):
            loc = leaf['locator']
            byte_a, byte_b = len(text[:a].encode()), len(text[:b].encode())
            first, last = text.count('\n', 0, a) + 1, text.count('\n', 0, b - 1) + 1
            assert leaf['text'] == text[a:b] and raw[byte_a:byte_b] == leaf['text'].encode()
            assert leaf['text_utf8_sha256'] == sha(raw[byte_a:byte_b])
            assert loc['unicode_code_point_interval_half_open'] == [a, b]
            assert loc['utf8_byte_interval_half_open'] == [byte_a, byte_b]
            assert loc['physical_line_range_1based_inclusive'] == [first, last]
            assert loc['snapshot_absolute_path'] == portable[key]['original_provenance_binding']['path']
            assert loc['snapshot_sha256'] == key and loc['original_archive_absolute_path'] == doc.get('original_path')
            assert loc['physical_pages'] is None and loc['PDF_page_or_pixel_locator_available'] is False
            assert leaf['text_unicode_code_points'] == b - a and leaf['text_utf8_bytes'] == byte_b - byte_a
            assert leaf['source_resource_id'] == f'SOURCE-TEXT-GAP-{key}-C{a}-C{b}'
            expected_ranges.append((key, a, b))
            range_checks.append({'source_sha256': key, 'unicode_range': [a, b],
                                 'byte_range': [byte_a, byte_b], 'lines': [first, last],
                                 'snapshot_locator_preserved': True,
                                 'portable_same_SHA_copy': portable[key]['relative_copy'],
                                 'exact_raw_quote_and_range': True})
        complete = sorted(existing + gaps)
        assert complete and complete[0][0] == 0 and complete[-1][1] == len(text)
        assert all(a[1] == b[0] for a, b in zip(complete, complete[1:]))
    assert expected_ranges == [
        (z['source_sha256'], *z['locator']['unicode_code_point_interval_half_open'])
        for z in receipt['added_resources']]
    if not additions:
        assert projected == bundle
    # Secondary counterfactual changes only the old envelope's bundle/hash.
    # It is a size decomposition, not an adopted future runtime contract.
    source_change_only = copy.deepcopy(old)
    source_change_only['source_bundle'] = projected
    source_change_only['source_bundle_sha256'] = new['source_bundle_sha256']
    metric = {'source_id': sid, 'old_actual_compact_packet_bytes': len(old_raw),
              'candidate_actual_pretty_file_bytes': len(new_raw),
              'candidate_compact_same_serializer_bytes': len(canon(new)) + 1,
              'projected_bundle_in_original_envelope_bytes': len(canon(source_change_only)) + 1,
              'old_bundle_compact_bytes': len(canon(bundle)),
              'new_bundle_compact_bytes': len(canon(projected)),
              'source_material_compact_delta': len(canon(projected)) - len(canon(bundle)),
              'candidate_preparation_envelope_extra_bytes': len(canon(new)) - len(canon(source_change_only))}
    measures.append(metric)
    counts['records'] += 1
    counts['changed'] += bool(additions)
    counts['added_ranges'] += len(additions)
    checks.append({'source_id': sid, 'candidate_packet': new_binding, 'parent_packet': parent_binding,
                   'source_record_exact': True, 'old_resource_prefix_exact': True,
                   'unchanged_keys_exact': True, 'neutral_projection_exact': True,
                   'candidate_envelope_exact': True, 'material_changed': bool(additions),
                   'source_permissions_inherited_unchanged': True,
                   'new_range_checks': range_checks})
assert counts['records'] == 4481 and counts['changed'] == 1227


def distribution(values):
    return {'min': min(values), 'max': max(values), 'sum': sum(values)}


def greedy_metrics(rows, key):
    groups, current, byte_n = [], [], 0
    for row in rows:
        size = row[key]
        if current and (len(current) == 12 or byte_n + size > 260000):
            groups.append((len(current), byte_n))
            current, byte_n = [], 0
        current.append(row['source_id'])
        byte_n += size
    if current:
        groups.append((len(current), byte_n))
    return {'group_N_simulated': len(groups),
            'group_record_N_distribution': dict(sorted(Counter(n for n, b in groups).items())),
            'group_packet_bytes_distribution': distribution([b for n, b in groups]),
            'oversize_single_packet_source_ids': [r['source_id'] for r in rows if r[key] > 260000]}


assert [sid for group in old_plan['batches'] for sid in group['source_ids']] == frame['source_ids']
by_id = {row['source_id']: row for row in measures}
old_assignment = []
for group in old_plan['batches']:
    ids = group['source_ids']
    old_byte_n = sum(by_id[sid]['old_actual_compact_packet_bytes'] for sid in ids)
    assert old_byte_n == group['packet_bytes'] == group['input_bytes']
    new_byte_n = sum(by_id[sid]['candidate_compact_same_serializer_bytes'] for sid in ids)
    source_only_byte_n = sum(by_id[sid]['projected_bundle_in_original_envelope_bytes'] for sid in ids)
    old_assignment.append({'old_batch_id': group['batch_id'], 'source_ids': ids,
                           'old_packet_bytes': old_byte_n,
                           'candidate_compact_packet_bytes': new_byte_n,
                           'original_envelope_projected_bundle_bytes': source_only_byte_n,
                           'candidate_exceeds260000': new_byte_n > 260000,
                           'source_only_exceeds260000': source_only_byte_n > 260000})
old_greedy = greedy_metrics(measures, 'old_actual_compact_packet_bytes')
assert old_greedy['group_N_simulated'] == old_plan['batch_N'] == 504
budget = {
    'status': 'read_only_budget_analysis_no_batch_files_or_dispatch',
    'meter': 'json.dumps(ensure_ascii=False,sort_keys=True,separators=(comma,colon)).encode(UTF8) + one LF; whole packet envelope',
    'original_serializer_binding': inputs[str((PREP / 'prepare-full4481.py').resolve())],
    'original_4481_actual_files_equal_that_serializer': True,
    'inherited_packet_byte_limit': 260000, 'inherited_max_records': 12,
    'order': 'unchanged frozen FRAME4481 order',
    'original': {'packet_bytes': distribution([r['old_actual_compact_packet_bytes'] for r in measures]), **old_greedy},
    'current_candidate_compact_full_preparation_envelope': {
        'packet_bytes': distribution([r['candidate_compact_same_serializer_bytes'] for r in measures]),
        **greedy_metrics(measures, 'candidate_compact_same_serializer_bytes')},
    'material_delta_only_original_envelope_counterfactual': {
        'not_adopted_runtime_contract': True,
        'packet_bytes': distribution([r['projected_bundle_in_original_envelope_bytes'] for r in measures]),
        **greedy_metrics(measures, 'projected_bundle_in_original_envelope_bytes')},
    'candidate_pretty_artifact_bytes_not_the_budget_meter': distribution([r['candidate_actual_pretty_file_bytes'] for r in measures]),
    'source_material_compact_delta_sum': sum(r['source_material_compact_delta'] for r in measures),
    'candidate_preparation_envelope_extra_bytes_sum': sum(r['candidate_preparation_envelope_extra_bytes'] for r in measures),
    'unchanged_old504_assignments_candidate_over_budget_N': sum(r['candidate_exceeds260000'] for r in old_assignment),
    'unchanged_old504_assignments_source_delta_only_over_budget_N': sum(r['source_only_exceeds260000'] for r in old_assignment),
    'candidate_copied_manual_prompt_protocol_bytes_separate_from_packet_meter': sum(r['candidate']['bytes'] for r in common),
    'original_preparer_provisional_core_bytes_separate_from_packet_meter': sum(x['bytes'] for x in load(PREP / 'candidate-core-bindings.json')['bindings'].values()),
    'limits': ['260000 is the inherited packet byte heuristic, not a model token/context guarantee.',
               'Core instructions and externally available assets are recorded separately by the original preparer.',
               'No new batch-plan, assigned input files, inference, dispatch, or candidate adoption was created.',
               'The current compact-candidate scenario includes its actual preparation provenance; source-only scenario is a counterfactual decomposition.']}

write('all4481-reception-checks.json', checks)
write('all4481-compact-byte-measures.json', measures)
write('old504-assignment-budget-impact.json', old_assignment)
write('compact-budget-summary.json', budget)
write('17-original-copy-map-checks.json', copy_checks)
write('common-and-role-bindings-checks.json', {
    'manual_prompt_protocol': common, 'five_roles': roles,
    'same_actual_inventory_binding': True, 'role_delivery_or_human_independence_certified': False,
    'future_portability': 'Resolve unchanged original snapshot bindings via the verified separate relative-copy map; no locator rewriting or external-machine execution was tested.'})
mechanical = {'status': 'all4481_mechanical_reception_passed_preparation_only',
              'counts': dict(counts), 'unchanged_material_records': 4481 - counts['changed'],
              'candidate_seal_9_members_exact': True, 'candidate_inventory_exact4481': True,
              'parent_source_record_old_resource_prefix_equality_N': 4481,
              'actual_neutral_projection_and_envelope_equality_N': 4481,
              'all_added_ranges_original_byte_char_line_SHA_exact': True,
              'actual_bound_original_and_copy_SHA_checks_N': 17,
              'unchanged_snapshot_locators_and_relative_map_checked': True,
              'five_roles_one_inventory_preparation_only': True,
              'classification_or_model_runner_called': False,
              'actual_new_delivery_or_results_created': False,
              'semantically_read_all4481_or17_originals': False}
write('mechanical-summary.json', mechanical)
write('audited-input-bindings.json', {
    'files': [inputs[k] for k in sorted(inputs)],
    'coverage': 'All candidate/parent packet bindings, originals/copies, source catalogs, original preparation meter/plan and declared common files; source/result separation preserved.',
    'no_labels_prediction_or_800_replay_files_read': True})
print(json.dumps({'mechanical': mechanical, 'budget': budget}, ensure_ascii=False, indent=2))

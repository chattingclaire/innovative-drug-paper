"""Prepare two neutral same-version source additions; never classify or adopt."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / '01-review/source-interface-v16-article6-addendum-sol'
PRE = ROOT / '06-coding/full4481-common-v15-production-preparation-sol'
LEAVES = ROOT / '10-closure-20261012/rule-repair-v14/source-material-preparation/materials-candidate.json'
TARGETS = {'RECODE25-02588', 'RECODE25-04598'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def checked(spec):
    raw = Path(spec['path']).read_bytes()
    assert len(raw) == spec['bytes'] and sha(raw) == spec['sha256'], spec['path']
    return raw


def save(path, raw):
    assert path.resolve().is_relative_to(HERE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(raw)


def save_json(path, value):
    save(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode() + b'\n')


def main():
    assert bind(LEAVES)['sha256'] == 'e6e4a61996da231ba27af7c05eb67a39edade520512ae666b76dadbca548d4b1'
    material = json.loads(LEAVES.read_bytes())
    assert material['candidate_packet_written_or_adopted'] is False
    assert material['source_READ_or_USE_events_created'] is False
    additions = {row['source_id']: row for row in material['records']}
    assert set(additions) == TARGETS
    old_seal = json.loads((BASE / 'output-seal.json').read_bytes())
    sealed = {row['path']: row for row in old_seal['files']}
    old_common = BASE / 'common-frame-bundles-v16.jsonl'
    old_frames = BASE / 'frame-bundle-bindings-v16.jsonl'
    old_specs = BASE / 'packet-bindings-v16.json'
    lines = checked(sealed[str(old_common)]).splitlines(keepends=True)
    frames = checked(sealed[str(old_frames)]).splitlines(keepends=True)
    specs = json.loads(checked(sealed[str(old_specs)]))
    assert sealed[str(old_common)]['sha256'] == '5df3be1d9e5b84a2e280566621d86c6ec9012cac1cdf2b1716d279c19a6e575e'
    assert sealed[str(old_specs)]['sha256'] == 'cd790b5845252cb0385d7f5502e056c71bdbef5665b75ffec9d642d90f0427b9'
    order = [row['source_id'] for row in specs]
    assert len(lines) == len(frames) == len(specs) == len(set(order)) == 4481
    new_lines, new_frames, new_specs = list(lines), list(frames), copy.deepcopy(specs)
    changes = []
    for source_id in sorted(TARGETS, key=order.index):
        index = order.index(source_id)
        addition = additions[source_id]
        assert addition['current_v16_packet_binding'] == specs[index]
        packet = json.loads(checked(specs[index]))
        bundle = packet['source_bundle']
        assert set(packet) == {'output_id', 'packet_version', 'source_bundle', 'source_bundle_sha256', 'source_id', 'verified_asset_files'}
        assert packet['packet_version'] == 'native-full-source-3'
        assert packet['source_id'] == source_id and packet['output_id'] == specs[index]['output_id']
        assert packet['source_bundle_sha256'] == sha(canonical(bundle)) == specs[index]['source_bundle_sha256']
        assert json.loads(lines[index]) == bundle
        assert bundle['source_record']['id'] == source_id
        resources = addition['candidate_resources']
        original = checked(addition['source_snapshot'])
        original_text = original.decode('utf-8')
        for leaf in resources:
            assert leaf['kind'] == 'verbatim_UTF8_snapshot_text'
            assert leaf['source_sha256'] == bundle['source_record']['source_ref']['sha256'] == sha(original)
            loc = leaf['locator']
            a, b = loc['unicode_code_point_interval_half_open']
            ba, bb = loc['utf8_byte_interval_half_open']
            first, last = loc['physical_line_interval_inclusive_1based']
            assert original_text[a:b] == leaf['text']
            assert original[ba:bb] == leaf['text'].encode('utf-8')
            assert ''.join(original_text.splitlines(keepends=True)[first-1:last]) == leaf['text']
            assert sha(original[ba:bb]) == leaf['text_utf8_sha256']
        new_bundle = copy.deepcopy(bundle)
        old_resource_N = len(bundle['source_full_text_resources'])
        new_bundle['source_full_text_resources'].extend(copy.deepcopy(resources))
        assert len({x['source_resource_id'] for x in new_bundle['source_full_text_resources']}) == len(new_bundle['source_full_text_resources'])
        for key in bundle:
            if key != 'source_full_text_resources':
                assert new_bundle[key] == bundle[key]
        assert new_bundle['source_full_text_resources'][:old_resource_N] == bundle['source_full_text_resources']
        new_raw = canonical(new_bundle)
        new_packet = copy.deepcopy(packet)
        new_packet['source_bundle'] = new_bundle
        new_packet['source_bundle_sha256'] = sha(new_raw)
        packet_path = HERE / 'packets' / f'{source_id}.json'
        save(packet_path, canonical(new_packet))
        new_specs[index].update(bind(packet_path))
        new_specs[index]['source_bundle_sha256'] = sha(new_raw)
        new_specs[index]['source_bundle_utf8_bytes'] = len(new_raw)
        new_lines[index] = new_raw + b'\n'
        new_frame = {'id': source_id, 'frame_ordinal_1based': index + 1,
                     'old_v16_bundle_sha256': packet['source_bundle_sha256'],
                     'new_v17_bundle_sha256': sha(new_raw), 'new_v17_bundle_utf8_bytes': len(new_raw),
                     'source_record_object_sha256': sha(canonical(bundle['source_record'])),
                     'primary_source_sha256': bundle['source_record']['source_ref']['sha256'],
                     'old_current_source_record_and_contexts_exact': True,
                     'all_fields_except_appended_source_full_text_resources_exact': True,
                     'added_literal_resource_N': len(resources), 'original_source_version_unchanged': True,
                     'actual_coding_or_consumer_read_run': False}
        new_frames[index] = canonical(new_frame) + b'\n'
        changes.append({'source_id': source_id, 'frame_ordinal_1based': index + 1,
                        'old_packet': specs[index], 'new_packet': new_specs[index],
                        'appended_resource_pointers': [f'/source_full_text_resources/{n}' for n in range(old_resource_N, old_resource_N + len(resources))],
                        'appended_resource_ids': [x['source_resource_id'] for x in resources]})
    changed_ordinals = [i + 1 for i, (old, new) in enumerate(zip(lines, new_lines)) if old != new]
    assert changed_ordinals == [order.index(x) + 1 for x in sorted(TARGETS, key=order.index)]
    assert [i + 1 for i, (old, new) in enumerate(zip(frames, new_frames)) if old != new] == changed_ordinals
    assert all(old == new for sid, old, new in zip(order, specs, new_specs) if sid not in TARGETS)
    save(HERE / 'common-frame-bundles-v17.jsonl', b''.join(new_lines))
    save(HERE / 'frame-bundle-bindings-v17.jsonl', b''.join(new_frames))
    save_json(HERE / 'packet-bindings-v17.json', new_specs)
    correspondence = [{'source_id': sid, 'frame_ordinal_1based': i + 1,
                       'old_common_line_sha256': sha(old), 'new_common_line_sha256': sha(new),
                       'common_line_byte_same': old == new}
                      for i, (sid, old, new) in enumerate(zip(order, lines, new_lines))]
    save_json(HERE / 'full4481-material-correspondence.json', correspondence)
    human_manifest_path = ROOT / '09-delivery/human200-independent-preparation-root/workbook-manifest.json'
    human_draw_binding = json.loads(human_manifest_path.read_bytes())['draw']
    human_ids = json.loads(checked(human_draw_binding))['source_ids_sorted']
    stability_manifest_path = ROOT / '06-coding/current-freeze-stability800-v1-root/run-manifest.json'
    stability_ids_binding = json.loads(stability_manifest_path.read_bytes())['ordered_source_ids']
    stability_ids = json.loads(checked(stability_ids_binding))
    assert len(human_ids) == len(set(human_ids)) == 200
    assert len(stability_ids) == len(set(stability_ids)) == 800
    batch_plan_path = PRE / 'batch-plan.json'
    plan = json.loads(batch_plan_path.read_bytes())
    closures = []
    for batch in plan['batches']:
        if not TARGETS.intersection(batch['source_ids']):
            continue
        new_packets = [new_specs[order.index(sid)] for sid in batch['source_ids']]
        closures.append({'batch_id': batch['batch_id'], 'source_ids': batch['source_ids'],
                         'expected_N': batch['expected_N'], 'new_packets': new_packets,
                         'actual_current_v16_packets': [specs[order.index(sid)] for sid in batch['source_ids']],
                         'new_packet_sum_bytes': sum(x['bytes'] for x in new_packets),
                         'original_packet_byte_limit': plan['packet_byte_limit'],
                         'within_original_byte_limit': sum(x['bytes'] for x in new_packets) <= plan['packet_byte_limit'],
                         'new_execution_authorized_or_started': False})
    assert set(sid for b in closures for sid in b['source_ids']) >= TARGETS
    assert all(b['within_original_byte_limit'] for b in closures)
    proof = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
             'status': 'shared_material_candidate_only_not_adopted_not_delivered_to_consumers',
             'version': 'source-interface/v17-finite-same-version-source-addenda',
             'base_v16_seal': bind(BASE / 'output-seal.json'),
             'base_common': sealed[str(old_common)], 'base_frame_bindings': sealed[str(old_frames)],
             'base_packet_bindings': sealed[str(old_specs)], 'neutral_material_preparation': bind(LEAVES),
             'new_common': bind(HERE / 'common-frame-bundles-v17.jsonl'),
             'new_frame_bindings': bind(HERE / 'frame-bundle-bindings-v17.jsonl'),
             'new_packet_bindings': bind(HERE / 'packet-bindings-v17.json'),
             'complete_line_correspondence': bind(HERE / 'full4481-material-correspondence.json'),
             'changes': changes, 'changed_ordinals_1based': changed_ordinals,
             'record_N': 4481, 'unchanged_common_and_frame_line_N': 4479,
             'reused_packet_binding_N': 4479, 'physically_new_packet_N': 2,
             'all_old_fields_and_existing_resource_prefixes_exact': True,
             'changed_pointers_only': '/source_full_text_resources appended entries; packet bundle hash updated',
             'canonical_contract': 'ensure_ascii=False sort_keys=True compact separators allow_nan=False UTF8; bundle hash excludes newline',
             'historical_internal_version_metadata_preserved': True,
             'human200': {'draw': human_draw_binding, 'changed_material_ids': sorted(TARGETS.intersection(human_ids))},
             'stability800': {'ordered_source_ids': stability_ids_binding, 'changed_material_ids': sorted(TARGETS.intersection(stability_ids)),
                              'existing_v16_campaign_unchanged': True, 'future_report_must_identify_v16_material': True},
             'native_original_batch_plan': bind(batch_plan_path), 'native_whole_batch_closures': closures,
             'sampling_ids_or_weights_changed': False, 'human_answers_or_machine_labels_accessed': False,
             'classifier_or_model_calls': 0, 'READ_or_USE_events_created': False,
             'source_semantic_applicability_preassigned': False,
             'preparation_preflight_history': 'First preflight stopped before creating any material output: an incorrect three-key packet assertion. It was corrected to the observed six-key native-full-source-3 schema; existing packet fields remain exact. No classifier/model calls or partial material outputs occurred.',
             'production_adopted': False, 'manual_or_algorithm_or_existing_outputs_modified': False,
             'requires_before_execution': ['Independent material review', 'Actual same-version finite source consumers and their bounded controls',
                                           'Both machine execution inputs must bind the same new materials', 'Separate truthful actual execution and result receipt']}
    save_json(HERE / 'source-extension-manifest-v17.json', proof)
    outputs = [bind(p) for p in sorted(HERE.rglob('*')) if p.is_file()]
    save_json(HERE / 'output-seal.json', {'status': proof['status'], 'files': outputs, 'self_excluded': True,
                                         'classifier_or_model_calls': 0, 'production_adopted': False})
    print(json.dumps({'new_common': proof['new_common'], 'changed_ids': sorted(TARGETS),
                      'unchanged_record_N': 4479, 'native_batches': [{'batch_id': b['batch_id'], 'source_ids': b['source_ids']} for b in closures],
                      'human200_changed_ids': proof['human200']['changed_material_ids'],
                      'stability800_changed_ids': proof['stability800']['changed_material_ids'],
                      'seal': bind(HERE / 'output-seal.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()

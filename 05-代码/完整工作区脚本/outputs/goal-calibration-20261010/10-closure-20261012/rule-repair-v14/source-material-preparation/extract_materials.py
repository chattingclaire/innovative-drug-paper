"""Prepare exact, unadopted UTF-8 leaves; never classify or record consumer READ."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import unicodedata

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MANIFEST = ROOT / '01-review/source-interface-v16-article6-addendum-sol/packet-bindings-v16.json'
SOURCE = ROOT / '06-coding/rule-five-dimension-joint-root/versions/joint-v13b-clinical-safety-role-root/source_packet.py'
DRIVER = ROOT / '10-closure-20261012/rule-repair-v13/execution-preparation/rule_driver.py'
SPECS = [
    ('RECODE25-04598', 'd959108cdaaa3b46c8334c217619a42f14c4d83f17af0934502a08c5d62864be',
     [(208, 217)], [211, 212]),
    ('RECODE25-02588', 'e3806c85b274ffd86c41b9780a316babd2f8a51f40c25b099a22132fa8cbcef9',
     [(45, 45), (85, 93)], [91]),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': sha(raw), 'bytes': len(raw)}


def normalized(text):
    return ''.join(unicodedata.normalize('NFKC', text).split())


def build():
    assert binding(MANIFEST)['sha256'] == 'cd790b5845252cb0385d7f5502e056c71bdbef5665b75ffec9d642d90f0427b9'
    assert binding(SOURCE)['sha256'] == '637332307d059e7f03af94441aaf4a012843c0541b549a2820b386b370c80611'
    assert binding(DRIVER)['sha256'] == '979363460d383412a060e4032a3aa010660f12a0aa316fbd6c492713a54085a3'
    entries = {r['source_id']: r for r in json.loads(MANIFEST.read_text())}
    # Load only the unchanged source-inventory adapter, no relation or classifier.
    source = {'__name__': 'candidate_source_inventory', '__file__': str(SOURCE)}
    exec(compile(SOURCE.read_bytes(), str(SOURCE), 'exec'), source)
    # Execute the exact existing integrity function, excluding driver runtime/imports.
    tree = ast.parse(DRIVER.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'literal_leaf_integrity')
    integrity = {'Path': Path, 'hashlib': hashlib}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(DRIVER), 'exec'), integrity)
    records, proposed_bundles, materials = [], [], []
    for rid, expected_sha, spans in [(x[0], x[1], x[2]) for x in SPECS]:
        entry = entries[rid]
        packet_path = Path(entry['path'])
        assert binding(packet_path) == {k: entry[k] for k in ('path', 'sha256', 'bytes')}
        packet = json.loads(packet_path.read_text())
        original = packet['source_bundle']
        canonical = json.dumps(original, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        assert sha(canonical) == packet['source_bundle_sha256'] == entry['source_bundle_sha256']
        assert len(canonical) == entry['source_bundle_utf8_bytes']
        assert not original['source_full_text_resources']
        assert original['source_record']['source_ref']['sha256'] == expected_sha
        doc = next(d for d in original['source_documents'] if d['source_sha256'] == expected_sha)
        snapshot = Path(doc['snapshot'])
        raw = snapshot.read_bytes()
        assert sha(raw) == expected_sha and len(raw) == doc['bytes']
        full = raw.decode('utf-8')
        lines = full.splitlines(keepends=True)
        leaves = []
        for first, last in spans:
            start = len(''.join(lines[:first - 1]))
            end = len(''.join(lines[:last]))
            text = full[start:end]
            a, b = len(full[:start].encode('utf-8')), len(full[:end].encode('utf-8'))
            assert raw[a:b] == text.encode('utf-8')
            leaves.append({
                'kind': 'verbatim_UTF8_snapshot_text',
                'source_resource_id': f'TEXTLEAF-{expected_sha[:16]}-L{first:04d}-L{last:04d}',
                'source_version_id': doc['source_version_id'],
                'source_sha256': expected_sha,
                'text': text,
                'text_utf8_sha256': sha(text.encode('utf-8')),
                'locator': {
                    'snapshot_absolute_path': str(snapshot.resolve()),
                    'physical_line_interval_inclusive_1based': [first, last],
                    'unicode_code_point_interval_half_open': [start, end],
                    'utf8_byte_interval_half_open': [a, b],
                },
            })
        proposed = copy.deepcopy(original)
        proposed['source_full_text_resources'].extend(leaves)
        old_inventory = source['source_inventory'](original)
        new_inventory = source['source_inventory'](proposed)
        assert new_inventory[:len(old_inventory)] == old_inventory
        added_inventory = new_inventory[len(old_inventory):]
        assert [z['resource_id'] for z in added_inventory] == [z['source_resource_id'] for z in leaves]
        assert all(z['consumer_read_status'] == z['consumer_use_status'] == 'not_recorded' for z in added_inventory)
        missing_lines = next(x[3] for x in SPECS if x[0] == rid)
        supplied = [original['source_record']['text']] + [c.get('text', '') for c in original['source_record']['contexts']]
        missing = [{'physical_line_1based': n,
                    'absent_from_current_body_and_context_texts': all(normalized(lines[n - 1]) not in normalized(t) for t in supplied)}
                   for n in missing_lines]
        assert all(x['absent_from_current_body_and_context_texts'] for x in missing)
        records.append({
            'source_id': rid,
            'current_v16_packet_binding': copy.deepcopy(entry),
            'current_packet_internal_version_preserved': packet['packet_version'],
            'current_bundle_internal_version_preserved': original['common_source_bundle_version'],
            'source_snapshot': binding(snapshot),
            'same_snapshot_as_current_source_ref': True,
            'current_body_source_ref': original['source_record']['source_ref'],
            'current_source_full_text_resource_N': 0,
            'current_context_ids': [c['context_id'] for c in original['source_record']['contexts']],
            'missing_literal_definition_checks': missing,
            'candidate_append_pointer': '/source_bundle/source_full_text_resources',
            'candidate_resources': leaves,
            'candidate_inventory_append': added_inventory,
            'classifier_delivery_status': 'not_delivered',
            'consumer_read_status': 'not_recorded',
            'consumer_use_status': 'not_recorded',
        })
        proposed_bundles.append(proposed)
        materials.append(binding(snapshot))
    checks = integrity['literal_leaf_integrity'](proposed_bundles, materials)
    assert len(checks) == 3
    return {
        'artifact_type': 'unadopted_exact_source_leaf_preparation',
        'status': 'candidate_material_only_not_delivered_not_classified',
        'current_v16_manifest': binding(MANIFEST),
        'source_inventory_implementation': binding(SOURCE),
        'literal_integrity_implementation': binding(DRIVER),
        'literal_integrity_function_ast_sha256': sha(ast.dump(node, include_attributes=False).encode()),
        'extractor': binding(__file__),
        'records': records,
        'literal_leaf_integrity_checks': checks,
        'same_version_means_exact_current_source_sha_not_filename_year': True,
        'existing_source_metadata_and_title_candidates_do_not_prove_definition_READ': True,
        'original_packets_or_sources_modified': False,
        'candidate_packet_written_or_adopted': False,
        'semantic_unit_RelationView_judge_or_protocol_prepare_called': False,
        'source_READ_or_USE_events_created': False,
        'classifier_io_required': False,
        'pending': [
            'A future common-source release must append these leaves to both consumers and bind the resulting material identity.',
            'The future exact finite relation must verify current operation, same-source scope, complete definition and boundaries; no sibling label inheritance.',
            'Actual consumer execution and source READ/USE events must be produced by that future run, not this preparation.',
        ],
    }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True, help='New JSON path; never overwrite existing artifacts.')
    args = parser.parse_args()
    data = build()
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'path': str(args.output.resolve()), 'records': 2, 'literal_leaves': 3,
                      'sha256': sha(args.output.read_bytes()), 'classified': False}, ensure_ascii=False))

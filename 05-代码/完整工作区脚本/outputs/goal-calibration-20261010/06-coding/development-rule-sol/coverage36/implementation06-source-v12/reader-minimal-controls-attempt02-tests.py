"""Eight necessary source-only integrity/boundary controls; no classifier imports."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock
import source_packet as reader

WORK = Path(__file__).resolve().parent
BASE = Path(json.loads((WORK / 'source-scope-v12.json').read_text())['v12_source_base'])


def synthetic_bundle():
    sha = 'a' * 64
    ref = {'sha256': sha, 'source_resource_id': 'SOURCE-' + sha, 'locator': {'physical_pages': [1]}}
    row = {'id': 'RECODE25-00001', 'text': '当前原文。', 'pages': [1], 'source_ref': copy.deepcopy(ref),
           'contexts': [{'context_id': 'CTX-RAW', 'kind': 'paragraph', 'text': '原始上下文。',
                         'source_ref': copy.deepcopy(ref), 'structure': {'position': '原位置'}}],
           'source_attachments': [{'sha256': 'b' * 64, 'source_pdf_sha256': sha,
                                   'relative_path': 'original.jpg', 'mime_type': 'image/jpeg'}]}
    doc = {'source_resource_id': 'SOURCE-LITERAL', 'snapshot_sha256': sha,
           'source_texts': [{'source_resource_id': 'SOURCEPARAGRAPH-literal', 'text': '独立原文候选。',
                             'source_ref': copy.deepcopy(ref), 'role': 'right_side_example',
                             'representation': 'literal_source_text'}]}
    return {'common_source_bundle_version': {'version': 'v12', 'actual_consumer_read_and_use_status': 'not_recorded'},
            'source_record': row, 'source_documents': [], 'explicit_or_primary_source_resources': [doc],
            'preserved_historical_neutral_source_supplements': [{'record_id': row['id'], 'supplement_id': 'SUPP-neutral',
                'source_sha256': 'c' * 64, 'text': '历史共同原文。', 'locator': {'physical_pages': [2]}}],
            'source_full_text_resources': [], 'source_asset_locations': [], 'source_locator_bases': {},
            'source_reference_index': [{'record_id': row['id'], 'source_resource_id': doc['source_resource_id']}],
            'source_provenance_addenda': []}


class FiniteSourceControls(unittest.TestCase):
    def test_canonical_unapproved_rows_never_json_decoded(self):
        data = b'{"id":"RECODE25-00001","text":"selected"}\n{"id":"RECODE25-99999",THIS IS NOT JSON}\n'
        real = reader._json
        calls = []
        def checked(raw, path):
            self.assertNotIn(b'99999', raw)
            calls.append(raw)
            return real(raw, path)
        with mock.patch.object(reader, '_json', checked):
            rows = reader._select_records(data, ['RECODE25-00001'])
        self.assertEqual(rows[0]['text'], 'selected')
        self.assertEqual(len(calls), 1)

    def test_selected_missing_or_duplicate_id_fails(self):
        line = b'{"id":"RECODE25-00001"}\n'
        for data, ids in ((line, ['RECODE25-00002']), (line + line, ['RECODE25-00001']),
                          (line, ['RECODE25-00001', 'RECODE25-00001'])):
            with self.subTest(ids=ids), self.assertRaises(reader.PacketInterfaceError):
                reader._select_records(data, ids)
        scope = json.loads((WORK / 'source-scope-v12.json').read_text())
        scope['scopes']['renewal2'] = ['RECODE25-99999']
        with tempfile.TemporaryDirectory(prefix='reader-boundary-', dir=WORK) as temp:
            manifest = Path(temp) / 'tampered-source-scope.json'
            manifest.write_text(json.dumps(scope))
            with mock.patch.object(reader, '_select_records', side_effect=AssertionError('record decode before scope check')):
                with self.assertRaises(reader.PacketInterfaceError): reader.load_scope(manifest)

    def test_sealed_hash_or_unlisted_dependency_fails(self):
        with tempfile.TemporaryDirectory(prefix='reader-control-', dir=WORK) as temp:
            path = Path(temp) / 'source.bin'
            path.write_bytes(b'original source bytes')
            with self.assertRaises(reader.PacketInterfaceError): reader._checked(path, 'a' * 64, {})
            with self.assertRaises(reader.PacketInterfaceError): reader._assemble(Path(temp), [], {}, {}, {})

    def test_raw_current_contexts_roles_refs_images_preserved_and_semantic_ids_excluded(self):
        bundle = synthetic_bundle()
        original = copy.deepcopy(bundle)
        unit = reader.semantic_unit(bundle)
        raw = bundle['source_record']
        self.assertEqual(unit['contexts'][:len(raw['contexts'])], raw['contexts'])
        self.assertEqual(unit['source_ref'], raw['source_ref'])
        self.assertEqual(unit['source_attachments'], raw['source_attachments'])
        self.assertNotEqual(unit['source_attachments'][0]['sha256'], unit['source_attachments'][0]['source_pdf_sha256'])
        self.assertNotIn('id', unit)
        self.assertNotIn('id', unit['source_bundle']['source_record'])
        self.assertNotIn('record_id', unit['source_bundle']['source_reference_index'][0])
        self.assertNotIn('record_id', unit['source_bundle']['preserved_historical_neutral_source_supplements'][0])
        self.assertEqual(bundle, original)

    def test_exact_resource_context_origin_and_historical_supplement_retention(self):
        bundle = synthetic_bundle()
        unit = reader.semantic_unit(bundle)
        extra = unit['contexts'][1:]
        self.assertEqual({c['text'] for c in extra}, {'独立原文候选。', '历史共同原文。'})
        literal = next(c for c in extra if c['kind'] == 'source_resource_text')
        self.assertEqual(literal['structure']['source_role'], 'right_side_example')
        origin = unit['derived_context_origins'][literal['context_id']]
        self.assertEqual(origin['role'], 'right_side_example')
        self.assertEqual(origin['source_bundle_pointer'], '/explicit_or_primary_source_resources/0/source_texts/0')
        self.assertEqual(origin['origin_inventory_view'], 'document_bundle')
        self.assertEqual(origin['origin_inventory_consumption_scope'], 'partial_exact_text_field_of_document_bundle')
        self.assertEqual(origin['origin_inventory_view_sha256'], reader.h(reader.cj(bundle['explicit_or_primary_source_resources'][0])))
        self.assertEqual(unit['source_bundle']['preserved_historical_neutral_source_supplements'][0]['supplement_id'], 'SUPP-neutral')
        self.assertFalse(any('applicable' in c['structure'] or 'dimension' in c['structure'] for c in extra))
        unit['source_bundle']['explicit_or_primary_source_resources'][0]['source_texts'][0]['text'] = 'mutated'
        self.assertEqual(bundle['explicit_or_primary_source_resources'][0]['source_texts'][0]['text'], '独立原文候选。')

    def test_approved_schema_unknown_or_result_field_fails(self):
        schema = json.loads((BASE / 'current-source-schema-v12.json').read_text())
        row = synthetic_bundle()['source_record']
        reader._validate_schema(row, schema, schema)
        row['unknown_projection'] = 'unreviewed'
        with self.assertRaises(reader.PacketInterfaceError): reader._validate_schema(row, schema, schema)
        with self.assertRaises(reader.PacketInterfaceError):
            reader._guard({'raw_source': {'labels': [1]}}, set(schema['x-source-protocol']['recursive_forbidden_exact_keys']))
        with self.assertRaises(reader.PacketInterfaceError): reader._json('{"x":1,"x":2}', 'synthetic')

    def test_complete_scoped_bundles_equal_sealed_common4_and36_source_only(self):
        bundles = reader.load_scope(WORK / 'source-scope-v12.json')
        self.assertEqual(len(bundles), 77)
        by_id = {b['source_record']['id']: b for b in bundles}
        for package in ('4-record-common-v12', 'coverage36-common-v12'):
            seal = json.loads((BASE / package / 'delivery-seal.json').read_text())
            entry = next(x for x in seal['files'] if Path(x['path']).name == 'common-source-bundles.jsonl')
            data = Path(entry['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'])
            for line in data.splitlines():
                original = json.loads(line)
                self.assertEqual(reader.cj(by_id[original['source_record']['id']]), reader.cj(original))

    def test_pure_inventory_equal_upstream_function_without_lookup(self):
        source = (BASE / 'source_only_interface_v12.py').read_text()
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'source_inventory')
        function = ''.join(source.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
        namespace = {'cj': reader.cj, 'h': reader.h}
        exec(compile(function, 'pure-source-inventory-only', 'exec'), namespace)
        bundle = synthetic_bundle()
        actual = reader.source_inventory(bundle)
        self.assertEqual(actual, namespace['source_inventory'](bundle))
        self.assertTrue(all(x['consumer_read_status'] == 'not_recorded' for x in actual))


if __name__ == '__main__': unittest.main(verbosity=2)

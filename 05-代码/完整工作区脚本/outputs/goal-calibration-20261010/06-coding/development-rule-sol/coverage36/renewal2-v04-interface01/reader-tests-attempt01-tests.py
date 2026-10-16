"""Predeclared synthetic source-interface controls; no classifier is imported."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import source_packet as reader

WORK = Path(__file__).resolve().parent
PDF_SHA = 'a' * 64
RESOURCE_ID = 'SOURCE-' + PDF_SHA
PARAGRAPH_ID = 'SOURCEPARAGRAPH-synthetic'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def geometry(paragraph_id):
    group = {'parent_resource_id': paragraph_id, 'operator_printed': '原文操作词',
             'operator': 'any', 'shared_scope': '原文共同范围', 'numbered_members': [paragraph_id]}
    return {'layout_type': 'single_column_prose_and_numbered_lists',
            'actual_viewed_physical_pages': [1], 'table_cells_or_merges': [], 'diagram_arrows': [],
            'rule1_condition_group': copy.deepcopy(group),
            'rule2_due_condition_group': {**copy.deepcopy(group), 'renewal_period_text': '原文期限',
                                          'member3_submembers': [paragraph_id], 'geometry_note': '原文位置'},
            'rule2_not_due_adjustment_group': {**copy.deepcopy(group), 'geometry_note': '原文位置'},
            'cross_page_joins': [{'resource_id': paragraph_id, 'pages': [1]},
                                 {'rule3_heading_page': 1, 'rule3_common_predicate_page': 1, 'note': '原文跨页位置'}],
            'rule2_other_shared_definitions': [paragraph_id], 'global_scope_resources': [paragraph_id]}


class ReaderInterfaceControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-reader-', dir=WORK)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.materials = self.root / 'materials'
        self.materials.mkdir()
        (self.root / 'assets').mkdir()
        (self.root / 'admin').mkdir()
        self.asset = self.root / 'assets' / 'page.png'
        self.asset.write_bytes(b'\x89PNG\r\n\x1a\nsynthetic exact-byte binding')
        self.source = self.materials / 'canonical.jsonl'
        self.manual = self.materials / 'manual.md'
        self.manual.write_text('Synthetic common manual source.\n', encoding='utf-8')
        self.resource_path = self.materials / 'source-resource.json'
        self.design_path = self.root / 'admin' / 'design.json'
        asset_sha = digest(self.asset.read_bytes())
        self.attachment = {'attachment_id': 'ASSET-synthetic', 'relative_path': '../assets/page.png',
                           'sha256': asset_sha, 'physical_page': 1, 'source_pdf_sha256': PDF_SHA,
                           'render_dpi': 220, 'kind': 'original_binary_rendered_source_page'}
        locator = {'physical_pages': [1], 'printed_pages': [1], 'heading_path': ['原始标题'],
                   'regions': [{'physical_page': 1, 'printed_page': 1,
                                'bbox_pdf_points_xyxy': [1.0, 2.0, 3.0, 4.0],
                                'bbox_220dpi_px_xyxy': [3.0, 6.0, 9.0, 12.0],
                                'page_asset': 'pages/page.png'}]}
        source_ref = {'sha256': PDF_SHA, 'source_resource_id': RESOURCE_ID, 'locator': locator}
        paragraph = {'source_resource_id': PARAGRAPH_ID, 'source_sha256': PDF_SHA,
                     'source_path': str(self.root / 'unread-snapshot.pdf'), 'kind': 'source_paragraph',
                     'text': '原始来源全文片段。', 'text_sha256': digest('原始来源全文片段。'.encode()),
                     'heading_path': ['原始标题'], 'source_char_interval_footerless_whitespace_normalized': [0, 11],
                     'source_ref': copy.deepcopy(source_ref)}
        self.resource = {'source_resource_id': RESOURCE_ID, 'source_sha256': PDF_SHA,
                         'snapshot': str(self.root / 'unread-snapshot.pdf'), 'snapshot_sha256': PDF_SHA,
                         'document_title': '合成来源', 'document_year': 2025,
                         'official_url': None, 'official_publication_date': None, 'metadata_status': '原始元数据',
                         'source_texts': [paragraph], 'source_geometry': geometry(PARAGRAPH_ID),
                         'source_page_assets': [{k: v for k, v in self.attachment.items() if k not in {'attachment_id', 'kind'}}],
                         'scope': '原始材料范围'}
        ctx_ref = copy.deepcopy(source_ref)
        ctx_ref['locator']['source_paragraph_id'] = PARAGRAPH_ID
        contexts = [
            {'context_id': 'CTX-CURRENT', 'kind': 'paragraph', 'source_document': 'D-synthetic',
             'text': '当前原文。', 'structure': {'pages': [1]},
             'source_ref': {'sha256': PDF_SHA, 'source_resource_id': RESOURCE_ID, 'locator': {'physical_pages': [1]}}},
            {'context_id': 'CTX-PARAGRAPH', 'kind': 'same_snapshot_referenced_source_paragraph',
             'source_document': 'D-synthetic', 'text': paragraph['text'],
             'structure': {'heading_path': ['原始标题'], 'source_paragraph_id': PARAGRAPH_ID,
                           'related_context_ids': ['CTX-CURRENT']}, 'source_ref': ctx_ref},
            {'context_id': 'CTX-GEOMETRY', 'kind': 'same_snapshot_source_numbered_group_geometry',
             'source_document': 'D-synthetic', 'structure': {**geometry('CTX-PARAGRAPH'),
                                                          'related_context_ids': ['CTX-PARAGRAPH']},
             'source_ref': {'sha256': PDF_SHA, 'source_resource_id': RESOURCE_ID, 'locator': {'physical_pages': [1]}}},
        ]
        self.row = {'id': 'synthetic-record', 'text': '当前原文。', 'pages': [1], 'contexts': contexts,
                    'source_ref': {'sha256': PDF_SHA, 'source_resource_id': RESOURCE_ID, 'locator': {'physical_pages': [1]}},
                    'source_attachments': [copy.deepcopy(self.attachment)],
                    'source_references': [{'source_resource_id': RESOURCE_ID, 'context_id': None,
                                           'source_field': 'source_context', 'literal_reference': '原始确指援引',
                                           'literal_relation_type': 'same_primary_SHA_named_rule_reference_restoration'}]}
        self.design = {'n': 1, 'source': {'path': str(self.source), 'sha256': ''},
                       'manual': {'path': str(self.manual), 'sha256': digest(self.manual.read_bytes())},
                       'resource': {'path': str(self.resource_path), 'sha256': ''},
                       'asset_path_base': str(self.materials),
                       'source_page_assets': [{'path': str(self.asset), 'sha256': asset_sha,
                                              'physical_page': 1, 'source_pdf_sha256': PDF_SHA}],
                       'unused_private_output': str(self.root / 'never-open-reference.jsonl')}
        self.sync()

    def sync(self, rows=None):
        self.source.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in (rows or [self.row])), encoding='utf-8')
        self.resource_path.write_text(json.dumps(self.resource, ensure_ascii=False), encoding='utf-8')
        self.design['source']['sha256'] = digest(self.source.read_bytes())
        self.design['resource']['sha256'] = digest(self.resource_path.read_bytes())
        self.write_design()

    def write_design(self):
        self.design_path.write_text(json.dumps(self.design, ensure_ascii=False), encoding='utf-8')

    def load(self):
        return reader.load_fixture(self.source, self.design_path)

    def rejected(self, edit, *, target='row', sync=True):
        edit(self.row if target == 'row' else self.resource if target == 'resource' else self.design)
        if sync:
            self.sync()
        with self.assertRaises(reader.PacketInterfaceError):
            self.load()

    def supported_row(self):
        row = copy.deepcopy(self.row)
        row['contexts'] = [row['contexts'][0]]
        row['source_references'] = []
        return row

    def test_bound_absolute_design_preserves_source_rows_and_raw_semantic_fields(self):
        rows = self.load()
        self.assertEqual(rows, [self.row])
        self.assertEqual(json.dumps(rows, ensure_ascii=False, sort_keys=True),
                         json.dumps([self.row], ensure_ascii=False, sort_keys=True))
        unit = reader.semantic_unit(self.supported_row())
        for key in ('text', 'pages', 'contexts', 'source_ref', 'source_attachments', 'source_references'):
            self.assertEqual(unit[key], self.supported_row()[key])
        self.assertNotIn('id', unit)
        self.assertFalse(Path(self.resource['snapshot']).exists())

    def test_context_kinds_and_geometry_are_not_reclassified_or_reconstructed(self):
        rows = self.load()
        self.assertEqual([c['kind'] for c in rows[0]['contexts']], [c['kind'] for c in self.row['contexts']])
        self.assertEqual(rows[0]['contexts'][2], self.row['contexts'][2])
        self.assertEqual(rows[0]['source_references'][0]['source_field'], 'source_context')

    def test_resource_text_is_not_appended_to_semantic_unit(self):
        self.row = self.supported_row()
        self.sync()
        rows = self.load()
        unit = reader.semantic_unit(rows[0])
        self.assertEqual(len(unit['contexts']), 1)
        self.assertNotIn('source_texts', unit)
        self.assertNotIn('source_geometry', unit)
        self.assertEqual(unit['contexts'], self.row['contexts'])

    def test_semantic_unit_deepcopies_neutral_raw_fields(self):
        row = self.supported_row()
        original = copy.deepcopy(row)
        unit = reader.semantic_unit(row)
        unit['source_attachments'][0]['kind'] = 'mutated'
        unit['source_ref']['locator']['physical_pages'].append(2)
        unit['contexts'][0]['text'] = 'mutated'
        self.assertEqual(row, original)

    def test_legacy_manifest_and_existing_semantic_unit_shape_remain_compatible(self):
        root = self.root / 'legacy'
        root.mkdir()
        row = {'id': 'old', 'text': '原文', 'pages': [1], 'contexts': [
            {'context_id': 'CTX-OLD', 'kind': 'paragraph', 'text': '原文', 'structure': {},
             'source_ref': {'sha256': PDF_SHA, 'locator': {}}}]}
        source = root / 'source.jsonl'
        source.write_text(json.dumps(row) + '\n')
        manual = root / 'manual.md'
        manual.write_text('old manual')
        manifest = root / 'manifest.json'
        manifest.write_text(json.dumps({'status': 'sealed_development_fixture_not_formal_test_or_human_reference',
            'n': 1, 'source_pages': [], 'outputs': [{'path': str(p), 'sha256': digest(p.read_bytes())}
                                                  for p in (source, manual)]}))
        self.assertEqual(reader.load_fixture(source, manifest), [row])
        self.assertEqual(set(reader.semantic_unit(row)), {'text', 'pages', 'contexts', 'attachments', 'source_image_attachments'})

    def test_unknown_source_field_rejected(self):
        self.rejected(lambda r: r.update(unreviewed_source_field='value'))

    def test_unknown_context_field_rejected(self):
        self.rejected(lambda r: r['contexts'][0].update(unreviewed_context_field='value'))

    def test_unknown_structure_field_rejected(self):
        self.rejected(lambda r: r['contexts'][0]['structure'].update(unreviewed_edge='value'))

    def test_unknown_geometry_field_rejected(self):
        self.rejected(lambda r: r['contexts'][2]['structure'].update(unreviewed_geometry='value'))

    def test_unknown_region_field_rejected(self):
        self.rejected(lambda r: r['contexts'][1]['source_ref']['locator']['regions'][0].update(unreviewed_region='value'))

    def test_unknown_attachment_field_rejected(self):
        self.rejected(lambda r: r['source_attachments'][0].update(unreviewed_asset='value'))

    def test_unknown_reference_field_rejected(self):
        self.rejected(lambda r: r['source_references'][0].update(unreviewed_reference='value'))

    def test_unknown_resource_field_rejected(self):
        self.rejected(lambda r: r.update(unreviewed_resource='value'), target='resource')

    def test_unknown_resource_text_field_rejected(self):
        self.rejected(lambda r: r['source_texts'][0].update(unreviewed_text='value'), target='resource')

    def test_nested_result_key_injection_rejected(self):
        self.rejected(lambda r: r['contexts'][2]['structure']['rule1_condition_group'].update(expected=1))

    def test_invalid_source_ref_resource_type_rejected(self):
        self.rejected(lambda r: r['source_ref'].update(source_resource_id=['not a string']))

    def test_boolean_page_and_dpi_rejected(self):
        for field in ('physical_page', 'render_dpi'):
            row = copy.deepcopy(self.row)
            row['source_attachments'][0][field] = True
            with self.subTest(field=field), self.assertRaises(reader.PacketInterfaceError):
                reader._row(row, 'synthetic')

    def test_invalid_bbox_type_order_or_nonfinite_rejected(self):
        for bbox in ([False, 1, 2, 3], [1, 2, 0, 3], [1, 2, float('inf'), 4], [1, 2, 3]):
            row = copy.deepcopy(self.row)
            row['contexts'][1]['source_ref']['locator']['regions'][0]['bbox_pdf_points_xyxy'] = bbox
            with self.subTest(bbox=bbox), self.assertRaises(reader.PacketInterfaceError):
                reader._row(row, 'synthetic')

    def test_dangling_context_reference_rejected(self):
        self.rejected(lambda r: r['contexts'][2]['structure']['rule1_condition_group'].update(parent_resource_id='CTX-MISSING'))

    def test_duplicate_context_and_attachment_identity_rejected(self):
        for field, value in (('contexts', self.row['contexts'][0]), ('source_attachments', self.row['source_attachments'][0])):
            row = copy.deepcopy(self.row)
            row[field].append(copy.deepcopy(value))
            with self.subTest(field=field), self.assertRaises(reader.PacketInterfaceError):
                reader._row(row, 'synthetic')

    def test_source_sha_mismatch_rejected(self):
        self.source.write_text(self.source.read_text() + ' ')
        with self.assertRaises(reader.PacketInterfaceError): self.load()

    def test_manual_sha_mismatch_rejected(self):
        self.manual.write_text('changed manual')
        with self.assertRaises(reader.PacketInterfaceError): self.load()

    def test_resource_sha_mismatch_rejected(self):
        self.resource_path.write_text(self.resource_path.read_text() + ' ')
        with self.assertRaises(reader.PacketInterfaceError): self.load()

    def test_asset_sha_mismatch_rejected(self):
        self.asset.write_bytes(b'changed asset')
        with self.assertRaises(reader.PacketInterfaceError): self.load()

    def test_unlisted_attachment_path_rejected_before_open(self):
        unlisted = self.root / 'unlisted.png'
        unlisted.write_bytes(b'not authorized')
        self.row['source_attachments'][0]['relative_path'] = '../unlisted.png'
        self.sync()
        original = Path.open
        def restricted_open(path, *args, **kwargs):
            self.assertNotEqual(path.resolve(), unlisted.resolve(), 'unlisted file was opened')
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, 'open', restricted_open), self.assertRaises(reader.PacketInterfaceError):
            self.load()

    def test_wrong_source_path_rejected_before_open(self):
        unlisted = self.root / 'wrong-source.jsonl'
        unlisted.write_text('private source')
        original = Path.open
        def restricted_open(path, *args, **kwargs):
            self.assertNotEqual(path.resolve(), unlisted.resolve(), 'unlisted source was opened')
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, 'open', restricted_open), self.assertRaises(reader.PacketInterfaceError):
            reader.load_fixture(unlisted, self.design_path)

    def test_relative_design_material_path_rejected(self):
        self.design['manual']['path'] = '../materials/manual.md'
        self.write_design()
        with self.assertRaises(reader.PacketInterfaceError): self.load()

    def test_asset_page_or_pdf_binding_mismatch_rejected(self):
        for field, value in (('physical_page', 2), ('source_pdf_sha256', 'b' * 64)):
            row = copy.deepcopy(self.row)
            row['source_attachments'][0][field] = value
            self.sync([row])
            with self.subTest(field=field), self.assertRaises(reader.PacketInterfaceError): self.load()

    def test_unknown_source_resource_id_rejected(self):
        self.rejected(lambda r: r['contexts'][0]['source_ref'].update(source_resource_id='SOURCE-unknown'))

    def test_unknown_source_paragraph_id_rejected(self):
        self.rejected(lambda r: r['contexts'][1]['structure'].update(source_paragraph_id='SOURCEPARAGRAPH-missing'))

    def test_resource_paragraph_text_mismatch_rejected(self):
        self.rejected(lambda r: r['contexts'][1].update(text='不同于原始绑定正文'))

    def test_resource_paragraph_locator_mismatch_rejected(self):
        self.rejected(lambda r: r['contexts'][1]['source_ref']['locator']['regions'][0].update(bbox_pdf_points_xyxy=[1, 2, 4, 5]))

    def test_geometry_binding_mismatch_rejected(self):
        self.rejected(lambda r: r['contexts'][2]['structure']['rule1_condition_group'].update(operator='all'))

    def test_resource_text_sha_mismatch_rejected(self):
        self.rejected(lambda r: r['source_texts'][0].update(text_sha256='b' * 64), target='resource')

    def test_resource_duplicate_paragraph_id_rejected(self):
        self.rejected(lambda r: r['source_texts'].append(copy.deepcopy(r['source_texts'][0])), target='resource')

    def test_region_asset_mismatch_rejected(self):
        self.rejected(lambda r: r['source_texts'][0]['source_ref']['locator']['regions'][0].update(page_asset='pages/foreign.png'), target='resource')

    def test_reference_resource_or_context_mismatch_rejected(self):
        for field, value in (('source_resource_id', 'SOURCE-foreign'), ('context_id', 'CTX-MISSING')):
            row = copy.deepcopy(self.row)
            row['source_references'][0][field] = value
            self.sync([row])
            with self.subTest(field=field), self.assertRaises(reader.PacketInterfaceError): self.load()

    def test_duplicate_json_keys_and_nonfinite_constants_rejected(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(reader.PacketInterfaceError):
                reader._json_loads(raw, 'synthetic')

    def test_count_or_duplicate_record_id_rejected(self):
        self.design['n'] = 2
        self.write_design()
        with self.assertRaises(reader.PacketInterfaceError): self.load()
        self.sync([self.row, copy.deepcopy(self.row)])
        with self.assertRaises(reader.PacketInterfaceError): self.load()

    def test_nonempty_undeclared_table_or_arrow_geometry_rejected(self):
        for field in ('table_cells_or_merges', 'diagram_arrows'):
            row = copy.deepcopy(self.row)
            row['contexts'][2]['structure'][field] = [{'unknown': 'shape'}]
            with self.subTest(field=field), self.assertRaises(reader.PacketInterfaceError):
                reader._row(row, 'synthetic')

    def test_original_frozen_context_contract_produces_unit(self):
        row = self.supported_row()
        unit = reader.semantic_unit(row)
        self.assertEqual(unit['contexts'], row['contexts'])
        self.assertEqual(reader.FROZEN_CONTEXT_KINDS, reader.CONTEXT_KINDS - {
            'same_snapshot_referenced_source_paragraph', 'same_snapshot_source_numbered_group_geometry'})

    def test_new_same_snapshot_paragraph_kind_rejected_at_semantic_boundary(self):
        row = copy.deepcopy(self.row)
        row['contexts'] = row['contexts'][:2]
        row['source_references'] = []
        with self.assertRaises(reader.UnsupportedSourceGraph): reader.semantic_unit(row)

    def test_new_same_snapshot_geometry_kind_rejected_at_semantic_boundary(self):
        row = copy.deepcopy(self.row)
        row['contexts'][1]['kind'] = 'source_paragraph'
        row['source_references'] = []
        with self.assertRaises(reader.UnsupportedSourceGraph): reader.semantic_unit(row)

    def test_required_source_reference_graph_rejected_without_role_conversion(self):
        row = self.supported_row()
        row['source_references'] = copy.deepcopy(self.row['source_references'])
        with self.assertRaises(reader.UnsupportedSourceGraph): reader.semantic_unit(row)
        self.assertEqual(row['contexts'][0]['kind'], 'paragraph')

    def test_strict_semantic_rejection_leaves_raw_row_unchanged(self):
        rows = self.load()
        original = copy.deepcopy(rows)
        with self.assertRaises(reader.UnsupportedSourceGraph): reader.semantic_unit(rows[0])
        self.assertEqual(rows, original)


if __name__ == '__main__':
    unittest.main(verbosity=2)

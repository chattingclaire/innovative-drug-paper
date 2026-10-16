"""Source/material integrity regressions; not held-out accuracy tests."""
import copy
import json
from pathlib import Path
import unittest
import policy_coding_v27 as coder
from table_material_adapter_v321 import verified_rows, describes_exclusive_data_right

INPUT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/agent-validation-20261007-r2/rule_inputs_shared_v6.jsonl')


class TableMaterialAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [r['input'] for r in map(json.loads, INPUT.read_text().splitlines())
                    if r['input'].get('verified_table_context_v4')]
        assert len(cls.rows) == 18

    def mutated(self, field, value):
        record = copy.deepcopy(self.rows[0])
        record['verified_table_context_v4'][0][field] = value
        record['llm_v29_shared_context']['verified_table_context_v4'] = copy.deepcopy(record['verified_table_context_v4'])
        return record

    def test_all_eighteen_source_rows_bound_and_literal(self):
        for record in self.rows:
            self.assertEqual(len(verified_rows(record)), 1)
            result = coder.code_unit(record)
            self.assertEqual(result['labels']['I'], 1)
            evidence = [e for e in result['evidence'] if e['rule'].startswith('V321_')]
            self.assertEqual(len(evidence), 1)
            self.assertEqual(record['unit_text'][evidence[0]['start']:evidence[0]['end']], evidence[0]['text'])

    def test_negative_right_eligibility_is_still_right_content(self):
        records = [r for r in self.rows if '不给予数据保护' in r['unit_text']]
        self.assertEqual(len(records), 4)
        for record in records:
            self.assertEqual(coder.code_unit(record)['labels']['I'], 1)
            self.assertEqual(record['verified_table_context_v4'][0]['raw_row_cells'][2], '—')

    def test_hash_paths_urls_and_source_identity_tampering_rejected(self):
        for key, value in [('source_image_sha256', '0' * 64), ('source_image', '/nonexistent.jpg'),
                           ('source_structured_sha256', '1' * 64), ('source_url', 'https://invalid.test/image.jpg'),
                           ('source_document_url', 'https://invalid.test/document')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                coder.code_unit(self.mutated(key, value))
        for key in ['source', 'source_sha256', 'unit_source', 'unit_source_sha256', 'candidate_file', 'candidate_sha256', 'unit_id']:
            record = copy.deepcopy(self.rows[0]); record[key] += '-altered'
            with self.subTest(key=key), self.assertRaises(ValueError):
                coder.code_unit(record)

    def test_row_index_cells_title_and_columns_tampering_rejected(self):
        changes = [('row_index_zero_based', 1), ('row_index_zero_based', True),
                   ('raw_row_cells', ['1类', '境内外均未上市的创新药', '4年', '']),
                   ('table_title', '普通记录保存期限'),
                   ('column_names', ['分类', '内容', '备注', '数据保护期']),
                   ('kind', 'unverified_table_title'), ('text', '伪造表列')]
        for key, value in changes:
            with self.subTest(key=key), self.assertRaises(ValueError):
                coder.code_unit(self.mutated(key, value))
        record = copy.deepcopy(self.rows[0]); record['unit_text'] += '改变'
        with self.assertRaises(ValueError): coder.code_unit(record)

    def test_shared_context_mismatch_missing_or_duplicate_certificate_rejected(self):
        record = copy.deepcopy(self.rows[0]); record['llm_v29_shared_context']['verified_table_context_v4'] = []
        with self.assertRaises(ValueError): coder.code_unit(record)
        record = copy.deepcopy(self.rows[0]); del record['verified_table_context_v4']
        with self.assertRaises(ValueError): coder.code_unit(record)
        record = copy.deepcopy(self.rows[0]); record['verified_table_context_v4'] *= 2
        record['llm_v29_shared_context']['verified_table_context_v4'] = copy.deepcopy(record['verified_table_context_v4'])
        with self.assertRaises(ValueError): coder.code_unit(record)

    def test_missing_both_certificates_never_infers_from_document_title(self):
        record = copy.deepcopy(self.rows[0])
        del record['verified_table_context_v4']; del record['llm_v29_shared_context']['verified_table_context_v4']
        self.assertEqual(verified_rows(record), [])
        result = coder.code_unit(record)
        self.assertFalse(any(e['rule'].startswith('V321_') for e in result['evidence']))
        self.assertEqual(result['labels']['I'], 0)

    def test_numeric_duration_requires_substantive_protection_column(self):
        cert = copy.deepcopy(self.rows[0]['verified_table_context_v4'][0])
        self.assertTrue(describes_exclusive_data_right(cert))
        cert['column_names'][2] = '文件保存期'
        self.assertFalse(describes_exclusive_data_right(cert))
        cert = copy.deepcopy(self.rows[0]['verified_table_context_v4'][0]); cert['table_title'] = '普通商业信息保存期限'
        self.assertFalse(describes_exclusive_data_right(cert))
        cert = copy.deepcopy(self.rows[0]['verified_table_context_v4'][0]); cert['raw_row_cells'][2] = '—'
        self.assertFalse(describes_exclusive_data_right(cert))
        cert['raw_row_cells'][3] = '不给予数据保护。'
        self.assertTrue(describes_exclusive_data_right(cert))

    def test_other_dimensions_are_never_added_by_material_adapter(self):
        for record in self.rows:
            result = coder.code_unit(record)
            self.assertEqual({d: result['labels'][d] for d in ['S', 'E', 'Ec', 'F']},
                             {'S': 0, 'E': 0, 'Ec': 0, 'F': 0})


if __name__ == '__main__': unittest.main()

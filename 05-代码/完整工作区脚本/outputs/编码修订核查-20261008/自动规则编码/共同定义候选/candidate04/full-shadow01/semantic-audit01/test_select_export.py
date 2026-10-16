"""Constructed records only; this suite never opens the real source pool."""
import copy
import unittest
import select_export as s


class ConstructedControls(unittest.TestCase):
    def test_frozen_draw_deduplicates_and_is_reproducible(self):
        rows = [{'id': f'x{i:03d}', 'department': s.DEPTS[i % 3],
                 'old': {'I': i % 2, 'F': (i // 2) % 2},
                 'new': {'I': (i + 1) % 2 if i < 20 else 0,
                         'F': (i // 2 + 1) % 2 if i < 30 else 0}}
                for i in range(60)]
        a, log = s.select(rows)
        self.assertEqual((a, log), s.select(list(reversed(rows))))
        self.assertEqual(len(a), len({r['id'] for r in a}))
        self.assertLessEqual(len(a), 22)
        self.assertEqual([r['quota'] for r in log], [6, 6, 3, 3, 4])

    def test_negative_frames_are_independent_and_pending_not_zero(self):
        row = {'old': {'I': 0, 'F': 1}, 'new': {'I': 0, 'F': 1}}
        self.assertTrue(s.in_bucket(row, 'I_unchanged_zero'))
        self.assertFalse(s.in_bucket(row, 'F_unchanged_zero'))
        row['old']['I'] = None
        self.assertFalse(s.in_bucket(row, 'I_unchanged_zero'))
        row['old']['I'] = False
        self.assertFalse(s.in_bucket(row, 'I_unchanged_zero'))

    def test_no_fill_from_other_departments_or_other_buckets(self):
        rows = [{'id': 'g', 'department': 'GOV', 'old': {'I': 1}, 'new': {'I': 0}},
                {'id': 'n', 'department': 'NHC', 'old': {'I': 1}, 'new': {'I': 0}}]
        result, log = s.select(rows)
        self.assertEqual([r['id'] for r in result], ['n'])
        self.assertEqual(log[0]['shortfall'], 5)

    def fixture(self):
        candidate = '/synthetic/source.json'
        text, context = '构造完整单元。', '构造前置原段。'
        record = {'input': {'unit_text': text, 'unit_id': 'p1-u1', 'pages': [1],
                            'candidate_file': candidate, 'candidate_sha256': 'a',
                            'llm_v29_shared_context': {
                                'paragraph_context': [{'text': context, 'pages': [1],
                                                       'old_label': 1, 'model_reason': 'do not export'}],
                                'model_suggestion': 'do not export'}}}
        dep = {'field_path': 'input.llm_v29_shared_context.paragraph_context[0].text',
               'field_text_sha256': s.text_digest(context), 'mapped': True,
               'protected_full_normalized_match_ids': [], 'bindings': [{
                   'candidate_path': candidate, 'candidate_sha256': 'a',
                   'method': 'EXACT_NORMALIZED_EXISTING_UNIT_OR_PARAGRAPH'}]}
        bound = {'current_unit_text_sha256': s.text_digest(text), 'candidate_unit_id': 'p1-u1',
                 'candidate_sha256': 'a', 'source_sha256': 's', 'dependencies': [dep]}
        return record, bound, {candidate: 'a'}

    def test_allowlist_exports_source_text_without_annotations(self):
        record, bound, hashes = self.fixture()
        out, consumed = s.export_record(record, bound, 'SA01-001', hashes)
        self.assertEqual(out['contexts'][0]['text'], '构造前置原段。')
        self.assertNotIn('do not export', str(out))
        self.assertNotIn('old_label', str(out))
        self.assertNotIn('verified_innovation_scope', s.neutral_role('verified_innovation_scope.text'))
        self.assertEqual(len(consumed), 1)

    def test_missing_or_protected_context_blocks_whole_unit(self):
        record, bound, hashes = self.fixture()
        bound['dependencies'][0]['protected_full_normalized_match_ids'] = ['protected']
        with self.assertRaises(ValueError):
            s.export_record(record, bound, 'SA01-001', hashes)
        bound['dependencies'][0]['protected_full_normalized_match_ids'] = []
        record['input']['llm_v29_shared_context'] = {}
        with self.assertRaises(KeyError):
            s.export_record(record, bound, 'SA01-001', hashes)

    def test_context_hash_and_nontext_field_fail_closed(self):
        record, bound, hashes = self.fixture()
        bound['dependencies'][0]['field_text_sha256'] = 'wrong'
        with self.assertRaises(ValueError):
            s.export_record(record, bound, 'SA01-001', hashes)
        record, bound, hashes = self.fixture()
        bound['dependencies'][0]['field_path'] = 'input.llm_v29_shared_context.model_suggestion'
        with self.assertRaises(ValueError):
            s.export_record(record, bound, 'SA01-001', hashes)

    def test_canonical_alias_requires_registered_direct_family_member(self):
        bound = {'id': 'alias', 'canonical_family_id': 'family',
                 'review_status': 'AVAILABLE_IN_BOUNDED_DEVELOPMENT_POOL',
                 'current_candidate_binding_verified': True, 'original_protected267_current_member': False,
                 'unmapped_dependency_field_paths': [], 'protected_dependency_family_ids': [],
                 'protected_embedded_or_context_unit_ids': [], 'isolation_reasons': [],
                 'confirmed_development_exposure': False,
                 'canonical_family_registered_development_members': ['direct'],
                 'development_exposure_basis': 'CANONICAL_EXACT_NORMALIZED_FAMILY_ALIAS'}
        direct = {'confirmed_development_exposure': True, 'canonical_family_id': 'family'}
        self.assertEqual(s.safety(bound, bound, {'direct': direct}), 'CANONICAL_EXACT_NORMALIZED_FAMILY_ALIAS')
        direct['canonical_family_id'] = 'other'
        with self.assertRaises(ValueError):
            s.safety(bound, bound, {'direct': direct})


if __name__ == '__main__':
    unittest.main()

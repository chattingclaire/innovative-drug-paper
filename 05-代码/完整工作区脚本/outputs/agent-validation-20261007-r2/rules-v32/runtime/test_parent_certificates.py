import copy
import unittest
from context_validation import digest, validate_added_parents


class ParentCertificateTests(unittest.TestCase):
    def setUp(self):
        self.record = {'unit_text': '不能有效保证受试者安全的', 'unit_id': 'u1',
                       'source_sha256': 'source-version', 'candidate_sha256': 'candidate-version'}
        parent = '有下列情形之一的，可以暂停药物临床试验：'
        self.record['verified_parent_context'] = [{
            'repair_version': 'v28', 'text': parent, 'text_sha256': digest(parent),
            'original_unit_sha256': digest(self.record['unit_text']),
            'source_sha256': 'source-version', 'candidate_sha256': 'candidate-version',
            'unit_id': 'u1', 'paragraph_id': 'p1', 'pages': [2],
            'verification': {'verified': True}}]

    def test_valid_binding(self):
        validate_added_parents(self.record)

    def test_altered_parent_rejected(self):
        self.record['verified_parent_context'][0]['text'] += '添加内容'
        with self.assertRaises(ValueError): validate_added_parents(self.record)

    def test_wrong_unit_or_source_rejected(self):
        for key in ('unit_text', 'unit_id', 'source_sha256', 'candidate_sha256'):
            with self.subTest(key=key):
                record = copy.deepcopy(self.record); record[key] += 'changed'
                with self.assertRaises(ValueError): validate_added_parents(record)

    def test_no_locator_or_verification_rejected(self):
        for key in ('pages', 'verification'):
            with self.subTest(key=key):
                record = copy.deepcopy(self.record)
                del record['verified_parent_context'][0][key]
                with self.assertRaises(ValueError): validate_added_parents(record)


if __name__ == '__main__': unittest.main()

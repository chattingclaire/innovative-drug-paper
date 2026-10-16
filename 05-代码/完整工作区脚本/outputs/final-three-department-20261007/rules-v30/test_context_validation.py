import copy
import json
import unittest
from pathlib import Path
from context_validation import verified_following_list, payload_digest


class ContextValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = [json.loads(s) for s in (Path(__file__).parent/'rule_inputs_v27.jsonl').read_text().splitlines()]
        cls.records = [r['input'] for r in rows if r['input'].get('verified_following_list_v27')]

    def test_all_eight_source_bound_certificates(self):
        self.assertEqual(len(self.records),8)
        for rec in self.records:
            self.assertTrue(verified_following_list(rec))

    def test_no_certificate_is_not_certified(self):
        self.assertFalse(verified_following_list({'unit_text':'应当符合以下条件:'}))

    def test_stale_text_wrong_source_and_missing_proof(self):
        for rec in self.records:
            altered = copy.deepcopy(rec)
            altered['unit_text'] += '不同原文'
            self.assertFalse(verified_following_list(altered))
            altered = copy.deepcopy(rec)
            altered['verified_following_list_v27']['source_sha256'] = 'wrong'
            self.assertFalse(verified_following_list(altered))
            altered = copy.deepcopy(rec)
            altered['verified_following_list_v27']['source_files_hash_verified'] = False
            self.assertFalse(verified_following_list(altered))

    def test_corrupted_context_and_uncertified_item(self):
        altered = copy.deepcopy(self.records[0])
        cert = altered['verified_following_list_v27']
        cert['contexts'][-1]['text'] += 'changed'
        self.assertFalse(verified_following_list(altered))
        cert['contexts_sha256'] = payload_digest(cert['contexts'])
        cert['contexts'][-1]['verification']['verified'] = False
        cert['contexts_sha256'] = payload_digest(cert['contexts'])
        self.assertFalse(verified_following_list(altered))


if __name__ == '__main__':
    unittest.main()

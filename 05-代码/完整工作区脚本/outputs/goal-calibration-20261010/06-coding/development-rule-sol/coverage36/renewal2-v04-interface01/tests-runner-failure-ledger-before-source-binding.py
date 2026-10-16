import unittest
import json
from pathlib import Path
import tempfile
import runner

class RawFailureLedgerTests(unittest.TestCase):
    def setUp(self):
        self.old=runner.EXPECTED_N
        runner.EXPECTED_N=2
        self.tmp=tempfile.TemporaryDirectory(prefix='failure-ledger-control-',dir=Path(__file__).parent)
        self.p=Path(self.tmp.name)/'synthetic.jsonl'
    def tearDown(self):
        runner.EXPECTED_N=self.old
        self.tmp.cleanup()
    def test_complete_raw_failure_keeps_all10(self):
        raw=[{'id':'synthetic-a','text':'甲','contexts':[],'unknown_original_field':{'kept':[1,2]}},{'id':'synthetic-b','text':'乙','contexts':[],'another_original_field':'all retained'}]
        self.p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in raw))
        result=runner.raw_failure_diagnostics(self.p,[{'type':'SourceSchemaError','message':'unsupported structure'}])
        self.assertEqual(len(result),10)
        self.assertTrue(all(s['technical_failure'] and s['rule_not_executed'] and not s['rules_null'] for s in result))
        self.assertTrue(all(s['rule_value'] is None and s['retained_rule_decision'] is None and not s['comparison_eligible'] for s in result))
        self.assertEqual(result[0]['source_record'],raw[0])
        self.assertEqual(result[-1]['source_record'],raw[1])
    def test_failed_raw_parse_never_becomes_rule_values(self):
        self.p.write_text('{invalid source')
        with self.assertRaises(json.JSONDecodeError):runner.raw_failure_diagnostics(self.p,[{'type':'SourceSchemaError'}])
    def test_duplicate_raw_ids_refuse_false_alignment(self):
        self.p.write_text('{"id":"synthetic-a"}\n{"id":"synthetic-a"}\n')
        with self.assertRaisesRegex(ValueError,'not unique'):runner.raw_failure_diagnostics(self.p,[{'type':'SourceSchemaError'}])

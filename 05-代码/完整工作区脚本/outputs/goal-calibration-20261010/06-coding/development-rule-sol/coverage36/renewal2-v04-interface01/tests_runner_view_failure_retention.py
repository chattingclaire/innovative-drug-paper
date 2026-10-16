import unittest
import runner

class ViewFailureRawRetentionTests(unittest.TestCase):
    def test_unsupported_view_retains_all_raw_fields_and_no_values(self):
        old=runner.EXPECTED_N
        runner.EXPECTED_N=2
        try:
            raw=[{'id':'synthetic-a','text':'甲','contexts':[],'source_references':{'raw':['kept']},'source_attachments':[{'original':True}]},{'id':'synthetic-b','text':'乙','contexts':[],'source_ref':{'all_original':'kept'}}]
            predictions=[{'id':row['id'],'decisions':None,'implementation_errors':[{'id':row['id'],'type':'UnsupportedSourceGraph'}]} for row in raw]
            result=runner.technical_diagnostics(raw,predictions,[predictions[0]['implementation_errors'][0],predictions[1]['implementation_errors'][0]])
            self.assertEqual(len(result),10)
            self.assertTrue(all(s['technical_failure'] and s['rule_not_executed'] and not s['rules_null'] for s in result))
            self.assertTrue(all(s['rule_value'] is None and s['retained_rule_decision'] is None for s in result))
            self.assertEqual(result[0]['source_record'],raw[0]);self.assertEqual(result[9]['source_record'],raw[1])
        finally:runner.EXPECTED_N=old

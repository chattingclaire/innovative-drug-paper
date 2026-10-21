import unittest
import sys
from unittest import mock
from pathlib import Path
import runner

class RunnerInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.expected_old = runner.EXPECTED_N
        runner.EXPECTED_N = 2
        self.rows = [dict(id='synthetic-a', text='原文甲', contexts=[]), dict(id='synthetic-b', text='原文乙', contexts=[])]
        self.dec = {d:{'value':0, 'kept':'original'} for d in runner.DIMENSIONS}
        self.pred = [dict(id=r['id'], decisions=dict(self.dec), implementation_errors=[]) for r in self.rows]
    def tearDown(self):
        runner.EXPECTED_N = self.expected_old
    def test_global_failure_keeps_ten_slots(self):
        result=runner.technical_diagnostics(self.rows,self.pred,[{'type':'SourceSchemaError'}])
        self.assertEqual(len(result),10)
        self.assertTrue(all(s['technical_failure'] for s in result))
        self.assertTrue(all(not s['comparison_eligible'] for s in result))
        self.assertTrue(all(s['retained_rule_decision']==self.dec[s['dimension']] for s in result))
    def test_per_record_failure_does_not_overwrite_other_rule_null(self):
        self.pred[0]['implementation_errors']=[{'type':'SourceSchemaError','id':'synthetic-a'}]
        self.pred[0]['decisions']=None
        self.pred[1]['decisions']['S']={'value':None,'kept':'null'}
        result=runner.technical_diagnostics(self.rows,self.pred,[])
        self.assertEqual(len(result),10)
        self.assertEqual(sum(s['technical_failure'] for s in result),5)
        self.assertTrue(result[5]['rules_null'])
        self.assertIsNone(result[5]['retained_rule_decision']['value'])
        self.assertTrue(all(s['retained_rule_decision']['value']==0 for s in result[6:]))
    def test_incomplete_source_no_fabricated_ids_or_slots(self):
        self.assertIsNone(runner.technical_diagnostics(self.rows[:1],self.pred,[]))
    def test_mismatched_ids_no_alignment_imputation(self):
        self.pred[1]['id']='another-id'
        self.assertIsNone(runner.technical_diagnostics(self.rows,self.pred,[]))
    def test_duplicate_ids_no_label_merge(self):
        self.rows[1]['id']='synthetic-a'
        self.pred[1]['id']='synthetic-a'
        self.assertIsNone(runner.technical_diagnostics(self.rows,self.pred,[]))
    def test_coder_import_before_freeze_refused(self):
        with mock.patch.dict(sys.modules,{'evidence':object()}):
            with self.assertRaisesRegex(ValueError,'before the inference freeze'):
                runner.load_frozen_coders(Path(__file__).parent,[])
    def test_wrong_source_scope_refused_before_coder_import(self):
        b=Path(__file__).parent
        design=Path('/PROJECT_ROOT/outputs/goal-calibration-20261010/04-calibration/renewal-rejudge-v11/admin/design.json')
        import json
        config=json.loads(design.read_text())
        argv=['runner.py','--source',config['source']['path'],'--manual',config['manual']['path'],'--manifest',str(design),'--source-sha256',config['source']['sha256'],'--expected-n','3','--approved-output-root',str(b),'--out',str(b/'not-created-wrong-count-test')]
        with mock.patch.object(sys,'argv',argv),mock.patch.object(runner,'load_frozen_coders',side_effect=AssertionError('coder import should not happen')) as gate:
            with self.assertRaisesRegex(ValueError,'source design scope'):
                runner.main()
            gate.assert_not_called()
        self.assertFalse((b/'not-created-wrong-count-test').exists())

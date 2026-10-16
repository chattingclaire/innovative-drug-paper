"""Development controls for coverage-object grammar, never reference labels."""
import copy,json,unittest
from pathlib import Path
import policy_coding_v27 as coder
from rules_recall_v31 import _covered_negotiated_object

HERE=Path(__file__).resolve().parents[2]
def record(text,parent=''):
 r={'unit_text':text,'source_sha256':'constructed-coverage-boundary','paragraph_context':[]}
 if parent:r['verified_parent_context']=[{'text':parent,'paragraph_id':'constructed-object-scope','pages':[1]}]
 return r

class CoverageObjectBoundaries(unittest.TestCase):
 def check(self,text,wanted,parent=''):
  p=coder.code_unit(record(text,parent));self.assertEqual(p['labels']['F'],wanted,(text,parent,p))
  for e in p['evidence']:self.assertEqual(text[e['start']:e['end']],e['text'])
  return p
 def test_literal_synonymous_object_anchors(self):
  for t in ['协议期内谈判药品','谈判药品(含续约药品)协议到期后的处理规则',
            '谈判药品的协议期满','谈判药品协议届满','协议到期后的谈判药品',
            '协议期满的谈判药品','协议届满后的谈判药品']:
   self.assertTrue(_covered_negotiated_object(t),t)
  for t in ['药物研究协议到期','谈判药品申报文件','目录外药品拟参加谈判',
            '谈判药品协议尚未签订','新药纳入医保目录']:
   self.assertFalse(_covered_negotiated_object(t),t)
 def test_current_object_and_management_class(self):
  for t in ['谈判药品(含续约药品)协议到期后原则上列入目录乙类。',
            '谈判药品的协议期满后纳入常规目录管理。',
            '协议届满后的谈判药品纳入“乙类药品”管理。']:
   self.check(t,0)
 def test_parent_object_and_current_management_class(self):
  for t in ['现分类制定谈判药品(含续约药品)协议到期后的处理规则如下。',
            '谈判药品的协议期满，适用以下规则。',
            '协议届满后的谈判药品适用以下规则。']:
   self.check('1.原则上列入目录乙类。',0,t)
 def test_actual_new_coverage_remains_positive(self):
  self.check('该新药纳入医保乙类目录。',1)
  self.check('该药品纳入医保支付范围。',1)
  self.check('1.原则上列入目录乙类。',1,'满足条件的药品可以纳入常规目录管理。')
 def test_independent_coverage_or_burden_survives(self):
  parent='谈判药品(含续约药品)协议到期后的处理规则如下。'
  self.check('原则上列入目录乙类，同时新药品纳入医保目录。',1,parent)
  self.check('原则上列入目录乙类；患者自付一定比例药品费用。',1,parent)
 def test_title_or_answer_metadata_cannot_supply_scope(self):
  a=record('1.原则上列入目录乙类。','满足条件的药品可以纳入常规目录管理。')
  b=copy.deepcopy(a);b.update(file_title='谈判药品协议到期续约规则',source='谈判药品协议到期.pdf',
    review_id='02077',group='NHSA',labels_A={'F':0},labels_C={'F':0})
  self.assertEqual(coder.code_unit(a)['labels'],coder.code_unit(b)['labels'])
  self.assertEqual(coder.code_unit(a)['labels']['F'],1)
 def test_bound_real_2022_object_scope(self):
  rows={r['id']:r['input'] for r in map(json.loads,(HERE/'rule_inputs_v31_shared_v2.jsonl').read_text().splitlines())}
  r=rows['RECODE25-02077'];p=coder.code_unit(r)
  self.assertEqual(p['labels']['F'],0)
  parents=[c for c in r['verified_parent_context'] if c.get('repair_version')=='v31-source-object-scope']
  self.assertEqual(len(parents),1);self.assertEqual(parents[0]['paragraph_id'],'renew22_p001')
  self.assertTrue(any(s['rule']=='V31_F_existing_coverage_management_category' for s in p['suppressions']))

if __name__=='__main__':unittest.main()

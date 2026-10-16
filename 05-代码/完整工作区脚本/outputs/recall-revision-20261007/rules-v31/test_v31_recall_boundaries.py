"""Development controls for traceable relation repairs; not validation data."""
import copy,json,unittest
from pathlib import Path
import policy_coding_v27 as coder

BASE=Path(__file__).resolve().parents[2]/'final-three-department-20261007'/'rules-v30'

def rec(text, prefix=''):
 return {'unit_text':text,'source_sha256':'constructed-v31-control','paragraph_context':[{'paragraph_id':'p','text':prefix+text,'pages':[]}]}

class V31RecallBoundaries(unittest.TestCase):
 def check(self,text,dim,wanted,prefix=''):
  p=coder.code_unit(rec(text,prefix));self.assertEqual(p['labels'][dim],wanted,(text,prefix,p))
  for e in p['evidence']:self.assertEqual(text[e['start']:e['end']],e['text'])
  return p
 def test_real_changed_rows_keep_exact_evidence(self):
  rows={r['id']:r['input'] for r in map(json.loads,(BASE/'rule_inputs_v30_shared.jsonl').read_text().splitlines())}
  expected={'RECODE25-00178':('I',1),'RECODE25-00203':('F',1),'RECODE25-00676':('F',0),
   'RECODE25-00843':('F',0),'RECODE25-02625':('F',0),'RECODE25-02224':('I',1),
   'RECODE25-02226':('I',1),'RECODE25-03734':('F',0),'RECODE25-04442':('I',1),'RECODE25-00028':('I',1),'RECODE25-00837':('F',0),'RECODE25-03282':('F',0)}
  for rid,(d,label) in expected.items():
   with self.subTest(id=rid):
    p=coder.code_unit(rows[rid]);self.assertEqual(p['labels'][d],label)
    for e in p['evidence']:self.assertEqual(rows[rid]['unit_text'][e['start']:e['end']],e['text'])
 def test_concrete_instrument_target_and_generic_purpose(self):
  self.check('建立药物研发资助制度，促进药品创新。','I',1)
  self.check('第一条为鼓励药品创新，满足公众用药需求，制定本办法。','I',0)
  self.check('现发布《建立药品加快上市注册制度支持药物创新办法》。','I',0)
  self.check('建立办公资助制度，促进管理创新。','I',0)
 def test_specific_new_generation_change_not_new_name(self):
  self.check('开发新一代克服肿瘤耐药的药物。','I',1)
  self.check('该抗肿瘤新药已完成申请。','I',0)
  self.check('开发新一代克服设备故障的系统。','I',0)
 def test_fast_track_requires_current_instrument_and_context_object(self):
  text='支持符合条件的全球同步研发品种和国际多中心临床试验纳入40日通道。'
  self.check(text,'I',1,'支持药物临床试验机构参与创新药物早期临床研发。')
  self.check(text,'I',0,'支持药物临床试验机构开展国际多中心临床试验。')
  self.check('已纳入40日通道的品种应上传材料。','I',0,'支持药物临床试验机构参与创新药物早期临床研发。')
 def test_participation_condition_not_generic_research_description(self):
  text='III期临床试验应当为主要研究者牵头开展的试验，主要研究者早期参与临床研发，有助于创新药全球同步研发。'
  prefix='支持药物临床试验机构参与创新药物早期临床研发。支持全球同步研发品种纳入40日通道。'
  self.check(text,'I',1,prefix)
  self.check(text,'I',0)
 def test_trial_gateway_requires_missing_standard_therapy_and_arrangement(self):
  text='对于肿瘤患者，临床试验即是重要的治疗手段，为了使患者在临床试验中更有可能获得潜在治疗，推荐FIH试验在具有治疗应答的瘤种中进行。'
  self.check(text,'F',1,'抗肿瘤药物试验选择已经没有标准治疗可供选择的末线患者。')
  self.check(text,'F',0,'抗肿瘤药物试验选择有标准治疗可供选择的患者。')
  self.check('为了使更多患者接受潜在更优治疗，可以使用2:1的试验分配比例。','F',0,'抗肿瘤药物试验选择已经没有标准治疗可供选择的末线患者。')
 def test_management_transfer_not_actual_coverage_or_patient_share(self):
  self.check('该药品确定支付标准后，统一转入常规目录乙类管理。','F',0)
  self.check('协议期内谈判药品纳入“乙类药品”管理。','F',0)
  self.check('各省按国家规定纳入《药品目录》的民族药纳入“乙类药品”管理。','F',0)
  self.check('该药品纳入医保乙类目录。','F',1)
  self.check('协议期内谈判药品纳入“乙类药品”管理，同时新药品纳入医保目录。','F',1)
  self.check('协议期内谈判药品纳入“乙类药品”管理；患者自付一定比例药品费用。','F',1)
  self.check('该药品可申请转入常规目录乙类管理。','F',0)
  self.check('说明该药品转入常规目录的支付标准确定方式。','F',0)
 def test_future_organising_procedure_not_current_membership(self):
  self.check('组织专家论证是否将药品纳入常规目录管理。','F',0)
  self.check('组织专家论证是否将药品纳入常规目录管理；保障药品持续供应。','F',1)
  self.check('该药品纳入医保支付范围。','F',1)
 def test_prior_membership_is_price_scope_not_current_coverage(self):
  self.check('药品通过竞价纳入医保目录的，企业需承诺供应该药品的价格不高于竞价报价。','F',0)
  self.check('药品通过竞价纳入医保目录的，企业需承诺供应该药品的价格不高于竞价报价；降低患者药费负担。','F',1)
 def test_claims_general_cost_not_drug_cost(self):
  self.check('医保数据指取得治疗赔付的医疗费用及相关医疗信息汇编。','Ec',0)
  self.check('医保数据包括药品费用和药费报销记录。','Ec',1)
 def test_metadata_cannot_determine_any_label(self):
  a=rec('建立药物研发资助制度，促进药品创新。');b=copy.deepcopy(a)
  b.update(review_id='all-labels-one',group='NHSA',file_title='创新性公平性答案',labels_A={d:1 for d in ['S','E','Ec','I','F']})
  self.assertEqual(coder.code_unit(a)['labels'],coder.code_unit(b)['labels'])
if __name__=='__main__':unittest.main()

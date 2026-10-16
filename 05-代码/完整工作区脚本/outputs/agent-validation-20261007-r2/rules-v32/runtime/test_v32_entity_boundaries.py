"""Development regressions, not a held-out or human validation sample."""
import copy
import json
import unittest
from pathlib import Path
import policy_coding_v27 as coder

OLD = Path(__file__).resolve().parents[3]/'recall-revision-20261007'
INPUT = OLD/'rule_inputs_v31_shared_v3.jsonl'

def rec(text,prefix='',parent=''):
    r={'unit_text':text,'source_sha256':'constructed-regression-source',
       'paragraph_context':[{'paragraph_id':'constructed-paragraph','text':prefix+text,'pages':[]}]}
    if parent:r['verified_parent_context']=[{'paragraph_id':'constructed-parent','text':parent,'pages':[]}]
    return r

class EntityBoundaries(unittest.TestCase):
    def check(self,text,dim,wanted,prefix='',parent=''):
        record=rec(text,prefix,parent);result=coder.code_unit(record)
        self.assertEqual(result['labels'][dim],wanted,(text,parent,result))
        for e in result['evidence']:
            self.assertEqual(text[e['start']:e['end']],e['text'])
        for e in result['suppressions']:
            if all(k in e for k in ['start','end','text']):
                self.assertEqual(text[e['start']:e['end']],e['text'])
        return result

    def test_plain_comparison_vs_explicit_product_change(self):
        for text in ['应说明和已上市中药处方对比情况。','评价与现有制剂结构比较情况。']:
            self.check(text,'I',0)
        for text in ['非处方药的改变剂型。','应说明和已上市中药处方对比情况；该药品改良制剂特征。','评价药品的作用机制新颖性。']:
            self.check(text,'I',1)

    def test_purpose_vs_actual_support_and_mixed_unit(self):
        for text in ['为支持创新药研发，制定本工作方案。','为鼓励研究和创制具有明显临床优势的药物，根据有关法律制定本工作程序。','为支持创新药研发，国家药监局制定了《工作方案》，现印发给你们。']:
            self.check(text,'I',0)
        self.check('为创新药研发提供资金支持。','I',1)
        self.check('建立药物研发资助制度，促进药品创新。','I',1)
        self.check('为支持创新药研发，制定本工作方案；为创新药研发优先配置资源。','I',1)

    def test_expert_preference_vs_actual_coverage(self):
        prefix='确定调入和调出的备选药品名单。'
        self.check('对于医保目录外药品，提请咨询专家予以重点考虑。','F',0,prefix)
        self.check('对于医保目录外药品，提请咨询专家予以重点考虑；该药品纳入医保支付范围。','F',1,prefix)
        self.check('该药品不纳入基本医疗保险支付范围。','F',1)
        self.check('该药品确认医保支付标准后纳入目录。','F',1)

    def test_commercial_recommendation_does_not_erase_basic_coverage(self):
        self.check('商保创新药目录共纳入19种药品。','F',0)
        self.check('商保创新药目录共纳入19种药品；该药品纳入基本医疗保险支付范围。','F',1)
        self.check('医保目录共纳入19种药品。','F',1)

    def test_verified_exit_predicate_vs_application_eligibility(self):
        item='(1)被撤销药品批准证明文件的药品。'
        self.check(item,'F',1,parent='1.调出目录药品的范围。')
        self.check(item,'F',1,parent='具有以下情况之一的药品将重点考虑调出基本目录:')
        self.check(item,'F',0,parent='具备以下情形之一的目录外药品，可以提出申报。')
        self.check(item,'F',0,parent='以下情形的药品可纳入评审范围。')
        self.check('被撤销药品批准证明文件的药品应提交报告。','F',0,parent='调出目录药品的范围。')

    def test_fund_condition_vs_management_class(self):
        parent='参保人使用目录内药品发生的费用，符合以下条件的，可由基本医疗保险基金支付:'
        self.check('(一)以疾病诊断或治疗为目的;','F',1,parent=parent)
        self.check('(一)以疾病诊断或治疗为目的;','F',0,parent='药品申报材料符合以下条件的，可以提出申请:')
        self.check('1.原则上列入目录乙类。','F',0,parent='谈判药品协议到期后的处理规则如下。')

    def test_new_scope_condition_vs_renegotiation_path(self):
        item='(1)独家药品。'
        self.check(item,'F',1,parent='协议期内谈判药品，同时符合以下条件的，以补充协议确定新的支付标准和支付范围。')
        self.check(item,'F',0,parent='药品同时符合以下条件的，可以按原支付范围重新谈判。')
        self.check('如谈判失败，则以原支付范围重新谈判或简易续约。','F',0)

    def test_substantive_protection_right_vs_confidentiality_or_filing_date(self):
        term='数据保护期自该药品注册申请在境内获得批准之日起计算。'
        prefix='符合条件的化学药品获批上市时，给予最长不超过6年的数据保护期。'
        self.check(term,'I',1,prefix=prefix)
        self.check(term,'I',0)
        self.check('该药品申请材料自批准之日起十日内提交。','I',0,prefix=prefix)
        self.check('药品的数据保护范围包括支持批准的临床试验数据，但不包括生物等效性数据。','I',1)
        self.check('药品的数据保护范围不包括已经公开的临床试验数据。','I',1)
        self.check('申请人提交的药品商业秘密不得公开。','I',0)
        self.check('药品上市申请的未披露申报数据应保存。','I',0)

    def test_wide_unmet_need_preserved_without_payer_obstacle(self):
        for text in ['该药物用于尚无有效治疗手段的患者。','仍有部分患者未能得到有效治疗，该药物应开展进一步研究。']:
            self.check(text,'F',1)
        self.check('该药物能够提高疗效。','F',0)
        self.check('该药物临床价值较高。','F',0)

    def test_clinical_management_vs_general_convenience_and_trial_supply(self):
        self.check('老年患者在准确量取及使用药物时遇到困难。','F',1)
        self.check('患者难以记住何时服药。','F',1)
        self.check('在药物设计时，应适配老年患者的认知水平。','F',0)
        self.check('申办者负责向研究者提供临床试验用药品。','F',0)
        self.check('为了使更多患者接受更优治疗，试验采用2:1分配比例。','F',0)

    def test_metadata_does_not_supply_dimensions(self):
        a=rec('应说明和已上市中药处方对比情况。')
        b=copy.deepcopy(a);b.update(review_id='anything',group='NMPA',file_title='创新性公平性',labels_A={'I':1,'F':1})
        self.assertEqual(coder.code_unit(a)['labels'],coder.code_unit(b)['labels'])

    def test_previously_exposed_real_units_only(self):
        records={r['id']:r['input'] for r in map(json.loads,INPUT.read_text().splitlines())}
        expected={'00004':('I',0),'01728':('I',0),'03894':('I',0),'02598':('F',0),'03803':('F',0),
                  '01009':('F',1),'01242':('F',1),'02290':('F',1),'03274':('F',1),'03361':('F',1),
                  '01389':('I',1),'01406':('I',1),'00009':('I',1),'00028':('I',1),'03430':('F',1),
                  '03425':('F',1),'03489':('I',1),'04737':('I',0),'04094':('F',0),'04099':('F',0),
                  '01723':('F',0),'02563':('F',0),'02570':('F',0)}
        for short,(dim,wanted) in expected.items():
            with self.subTest(id=short):
                record=records['RECODE25-'+short];result=coder.code_unit(record)
                self.assertEqual(result['labels'][dim],wanted)
                for e in result['evidence']:
                    self.assertEqual(record['unit_text'][e['start']:e['end']],e['text'])

if __name__=='__main__':unittest.main()

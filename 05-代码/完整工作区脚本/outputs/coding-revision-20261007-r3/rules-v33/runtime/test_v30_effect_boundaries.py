"""Constructed development controls for the confirmed CAL-v1.3 E boundaries."""
import unittest
import policy_coding_v27 as coder

def rec(text):
    return {'unit_text':text,'source_sha256':'constructed-control',
            'paragraph_context':[{'paragraph_id':'p','text':text,'pages':[]}]}

class V30EffectBoundaries(unittest.TestCase):
    def check(self,text,expected):
        result=coder.code_unit(rec(text))
        self.assertEqual(result['labels']['E'],expected,(text,result))
        for e in result['evidence']:
            self.assertEqual(text[e['start']:e['end']],e['text'])
        return result

    def test_inclusion_identity_alone_is_not_a_recommendation(self):
        for text in ['申报对象为纳入《甲病诊疗方案》的药品。',
                     '纳入最新版《乙病用药指南》的药品可以申报。',
                     '目录外药品申报条件：纳入《丙病药物治疗指南》的药品。',
                     '归档《某病诊疗方案》。',
                     '符合《基本医疗保险用药管理暂行办法》的药品。']:
            with self.subTest(text=text):self.check(text,0)

    def test_real_recommendations_and_independent_effects_survive(self):
        for text in ['药物治疗指南推荐该药物用于一线治疗。',
                     '纳入《甲病诊疗方案》的药品，应提供延长总生存期的研究证据。',
                     '该药物临床价值高，随机试验表明其疗效仍不确定。']:
            with self.subTest(text=text):self.check(text,1)

    def test_bare_clinical_value_is_not_an_effect(self):
        for text in ['参照药品用于证明药品价值、体现药品临床价值和明确市场定位。',
                     '药品评价应当体现临床价值。',
                     '评估该药物的临床价值。']:
            with self.subTest(text=text):self.check(text,0)

    def test_value_exclusion_is_local(self):
        for text in ['证明该药物临床价值，并提交临床获益证据。',
                     '药品临床价值体现为总生存期提高。',
                     '该药品临床价值待评估；应补充疗效数据。']:
            with self.subTest(text=text):self.check(text,1)

    def test_explicit_patient_benefit_retained(self):
        for text in ['创新程度高、临床价值大、患者获益显著的创新药。',
                     '创新程度高、临床价值大、患者受益显著的创新药。',
                     '综合考虑临床需求、患者获益等因素，确定该药品支付标准。',
                     '综合考虑药品临床价值、不良反应等因素，经评估认为风险大于收益。']:
            with self.subTest(text=text):self.check(text,1)

    def test_financial_patient_benefit_is_not_therapeutic(self):
        for text in ['该药物价格降低，药费报销使患者获益显著。',
                     '药品基金投资的风险大于收益。']:
            with self.subTest(text=text):self.check(text,0)

    def test_value_drop_retains_other_dimensions(self):
        result=self.check('该药品创新程度高、临床价值大，并有明显不良反应。',0)
        self.assertEqual(result['labels']['I'],1)
        self.assertEqual(result['labels']['S'],1)

    def test_id_and_source_metadata_permutation(self):
        text='该药品临床价值需评估，并提交疗效数据。'
        a=rec(text);b=rec(text)
        b.update(review_id='unrelated',original_file_stem='arbitrary-name',source='/unrelated')
        self.assertEqual(coder.code_unit(a)['labels'],coder.code_unit(b)['labels'])

    def test_general_claims_definition_remains_ec_zero(self):
        result=coder.code_unit(rec('医保数据：医疗保健提供者向保险公司提交的用以获得治疗和其它干预措施赔付的医疗费用及相关医疗信息汇编。'))
        self.assertEqual(result['labels']['Ec'],0)

if __name__=='__main__':unittest.main()

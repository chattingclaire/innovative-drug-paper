"""Synthetic semantic boundary checks; examples are not policy observations."""
import copy
import hashlib
import unittest
import policy_coding_v25 as coder


def record(text, paragraph=None):
    return {'unit_text': text, 'source_sha256': 'synthetic-source',
            'paragraph_context': [{'paragraph_id':'synthetic-p','text':paragraph or text,'pages':[1]}]}


class SemanticBoundaryTests(unittest.TestCase):
    def assert_dim(self, text, dim, value, paragraph=None):
        out=coder.code_unit(record(text,paragraph))
        self.assertEqual(out['labels'][dim],value,(text,out))
        for e in out['evidence']:
            self.assertEqual(text[e['start']:e['end']],e['text'])
        return out

    def test_innovation_degree_and_institutional_control(self):
        self.assert_dim('根据药品的创新程度制定分类要求。','I',1)
        self.assert_dim('药品监管机构的创新程度纳入机关考核。','I',0)
        self.assert_dim('开展创新药目录调整工作。','I',0)

    def test_conditional_data_protection_not_distance_cutoff(self):
        self.assert_dim('原研药品在满足试验数据提交及注册条件并完成相关申请程序之后，对全部试验数据给予六年数据保护期。','I',1)
        self.assert_dim('医院数据库在满足数据报送要求之后，对数据库给予六年数据保护期。','I',0)

    def test_innovation_support_and_concrete_modification(self):
        self.assert_dim('鼓励新药和创新医疗器械研发。','I',1)
        self.assert_dim('加快药品医疗器械原创性成果专利布局。','I',1)
        self.assert_dim('药品专利诉讼会议于明日举行。','I',0)
        self.assert_dim('根据用药数据改善片剂易碎性。','I',1)
        self.assert_dim('开发供老年患者用药的不同规格片剂。','I',0)

    def test_unmet_treatment_and_population_only(self):
        self.assert_dim('该药品用于缺乏有效治疗措施的疾病。','F',1)
        self.assert_dim('该药品上市后仍有部分患者未能得到有效治疗。','F',1)
        self.assert_dim('该药品的缓解率为30%。','F',0)
        self.assert_dim('该药品用于罕见病患者。','F',0)

    def test_clinical_management_obstacle_and_convenience(self):
        out=self.assert_dim('患者在打开药品包装及使用药物时遇到困难。','F',1)
        self.assertEqual(out['fairness_subtypes'],['clinical_management'])
        self.assert_dim('为老年患者设计便利的药品包装。','F',0)

    def test_current_qualification_vs_borrowed_program(self):
        text='用于尚无有效防治手段的疾病且具有明显临床优势的创新药或者改良型新药，可以申请适用突破性治疗药物程序。'
        out=self.assert_dim(text,'I',1)
        self.assertIn('qualification_advantage',out['innovation_subtypes'])
        out=coder.code_unit(record('一般优先审评参照突破性治疗的明显临床优势要求，药品申请人提交材料。'))
        self.assertNotIn('qualification_advantage',out['innovation_subtypes'])

    def test_supply_state_and_non_treatment_boundary(self):
        self.assert_dim('三年未向定点医疗机构供应的药品应予核查。','F',1)
        self.assert_dim('三年未向定点医疗机构供应的办公用品应予核查。','F',0)
        self.assert_dim('研究用药未向试验患者供应，应完成研究物流记录。','F',0)

    def test_stocking_information_and_archive(self):
        self.assert_dim('企业应及时更新药品配备情况。','F',1)
        self.assert_dim('企业仅按日期归档药品配备情况表。','F',0)
        self.assert_dim('企业仅更新药品配备情况表的文件名。','F',0)

    def test_explicit_access_reference(self):
        text='相应要求在协议中一并明确。'
        p='药品生产企业需要保障市场药品供应。包括推进配备并上报配备情况。'+text
        out=self.assert_dim(text,'F',1,p)
        self.assertTrue(any(e.get('context_dependency') for e in out['evidence']))
        self.assert_dim(text,'F',0,'企业需要完成财务审计。'+text)
        self.assert_dim(text,'F',0,'药品生产企业需要保障市场药品供应。'+text+text)

    def test_access_evaluation_information(self):
        text='根据评价需要可获得相关支持信息，如药品生产、供应相关信息。'
        self.assert_dim(text,'F',1,'可获得性可由药品配备情况反映。'+text)
        self.assert_dim(text,'F',0,'检查材料的归档格式。'+text)

    def test_ae_adr_with_object(self):
        self.assert_dim('报告药品ADR发生率及严重程度。','S',1)
        self.assert_dim('报告数据库AE发生率。','S',0)

    def test_scope_must_be_bound(self):
        r=record('呈现AE和ADR的总体发生率。')
        quote='针对首次递交上市申请的抗肿瘤创新药产品，提供安全性资料建议。'
        r['verified_object_scope']=[{'kind':'anticancer_drug_safety_dossier',
            'source_sha256':r['source_sha256'],'source_hash_field':'source_sha256',
            'unit_text_sha256':hashlib.sha256(r['unit_text'].encode()).hexdigest(),
            'text':quote,'text_sha256':hashlib.sha256(quote.encode()).hexdigest(),
            'locator':{'physical_pages':[1]},'verification':'synthetic fixture'}]
        out=coder.code_unit(r)
        self.assertEqual(out['labels']['S'],1)
        self.assertTrue(out['evidence'][-1].get('context_dependency'))
        bad=copy.deepcopy(r);bad['verified_object_scope'][0]['source_sha256']='different-source'
        with self.assertRaises(AssertionError):coder.code_unit(bad)

    def test_effect_endpoint_and_non_drug_activity(self):
        self.assert_dim('药品应达到最小有效剂量和最短有效疗程。','E',1)
        self.assert_dim('药品试验质量管理活动的有效性需要审查。','E',0)
        self.assert_dim('审查药品试验质量管理活动的有效性；同时提交药物疗效数据。','E',1)

    def test_quality_process_risk_vs_patient_risk(self):
        self.assert_dim('药品试验中审查风险控制措施，以确保质量管理活动的有效性。','S',0)
        self.assert_dim('药品试验中审查患者安全风险控制措施，以确保质量管理活动。','S',1)

    def test_registration_fee_and_drug_cost_mixed(self):
        self.assert_dim('药品注册申请受理后，申请人应当缴纳费用。','Ec',0)
        self.assert_dim('申请人未按期缴纳费用的，终止药品注册审评审批。','Ec',0)
        self.assert_dim('药品注册申请受理后，申请人缴纳费用；同时评价药物成本效果。','Ec',1)

    def test_document_title_is_not_a_dimension(self):
        self.assert_dim('根据《药品价格形成机制意见》组织工作。','Ec',0)
        self.assert_dim('根据《药品价格形成机制意见》，测算该药物治疗费用。','Ec',1)

    def test_incomplete_condition_vs_organizational_colon(self):
        out=self.assert_dim('一类创新药申请应满足以下条件之一：','I',None)
        self.assertEqual(set(out['labels'].values()),{None})
        self.assert_dim('药品监督管理部门承担以下职责：','I',0)
        text='一类创新药申请应满足以下条件之一：'
        r=record(text);r['verified_list_context']=[{'text':'具有明确临床优势。'}]
        self.assertIsNotNone(coder.code_unit(r)['labels']['I'])

    def test_normalization_preserves_exact_original_spans(self):
        self.assert_dim('根据药品的创 新 程 度制定要求。','I',1)
        self.assert_dim('报告药品ＡＤＲ发生率。','S',1)

    def test_metadata_does_not_determine_labels(self):
        r=record('提供药品安全性和疗效数据。')
        before=coder.code_unit(r)['labels']
        r.update(id='KNOWN_POSITIVE',source_title='医保创新公平目录',department='NMPA',filename='all_zero',review_id='test')
        self.assertEqual(coder.code_unit(r)['labels'],before)

    def test_do_not_blanket_abstain_nonmatch(self):
        out=self.assert_dim('药品申报会议将于下周召开。','I',0)
        self.assertEqual(set(out['labels'].values()),{0})


if __name__=='__main__':
    unittest.main()

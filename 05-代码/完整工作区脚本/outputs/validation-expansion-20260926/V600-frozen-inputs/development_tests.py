"""Development regressions, never an independent accuracy evaluation."""
import json
import hashlib
from pathlib import Path
import unittest
from policy_coding_v4_development import code_unit


def code(text, context=None):
    return code_unit(dict(unit_text=text, paragraph_context=[{'text': context}] if context else []))


class CodingDevelopmentTests(unittest.TestCase):
    def test_unmet_treatment_need_is_access_not_population_name(self):
        self.assertEqual(code('药品资料应说明未满足的治疗需求。')['labels']['F'],1)
        self.assertEqual(code('药品资料应说明儿童患者人数。')['labels']['F'],0)
        self.assertEqual(code('药品资料中列明未满足的研发需求。')['labels']['F'],0)

    def test_ratio_definition_resolves_reference_without_copying_other_dimensions(self):
        text='比值A超过规定值。'
        entry={'kind':'same_source_ratio_definition','original_unit_sha256':hashlib.sha256(text.encode()).hexdigest(),
               'contexts':[{'paragraph_id':'definition','text':'比值A为药品费用与预算之比。另须报告安全性。','source_sha256':'fixture','pages':[1],'verification':'constructed fixture'}]}
        r=code_unit({'unit_text':text,'verified_supplemental_context':[entry]})
        self.assertEqual(r['labels'],dict(S=0,E=0,Ec=1,I=0,F=0))
        self.assertEqual(r['evidence'][0]['text'],'比值A')
        self.assertEqual(r['evidence'][0]['context_dependency']['paragraph_id'],'definition')
        entry['kind']='same_article_following_list'
        self.assertEqual(code_unit({'unit_text':text,'verified_supplemental_context':[entry]})['labels']['Ec'],0)
        entry['original_unit_sha256']='stale'
        with self.assertRaises(AssertionError):code_unit({'unit_text':text,'verified_supplemental_context':[entry]})

    def test_explicit_fairness_content_and_publication_boundary(self):
        for t in ['申报药品资料包括公平性信息。','比较药品公平性方面的优势。','从公平性等方面综合研判药品价值。','药品应说明公平性方面的比较优势。']:
            self.assertEqual(code(t)['labels']['F'],1,t)
        for t in ['公示药品公平性信息。','药品企业应公平竞争。','公平性、系统性工作需逐步推进。']:
            self.assertEqual(code(t)['labels']['F'],0,t)

    def test_drug_access_channels_and_information(self):
        for t in ['建立单独的药品保障机制。','收集并报告药品配备品种、供应配送等信息。','鼓励定点医药机构开展预约就诊、送药上门等服务。','将符合条件的药品纳入医保支付范围。']:
            self.assertEqual(code(t)['labels']['F'],1,t)
        for t in ['医药机构开展预约就诊服务。','药品研究项目由医药机构提供送药上门服务。','报告药品研究材料配送信息。']:
            self.assertEqual(code(t)['labels']['F'],0,t)
        self.assertEqual(code('药品研究项目由医药机构提供送药上门服务；同时建立药品保障机制。')['labels']['F'],1)

    def test_insurance_and_charity_drug_costs(self):
        for t in ['鼓励商业健康保险将创新药纳入保障范围。','推动企业通过慈善捐赠，支持困难群众使用创新药。']:
            self.assertEqual(code(t)['labels']['Ec'],1,t)
        for t in ['鼓励药品企业参与慈善捐赠。','支持药物研发项目接受企业捐赠。','商业健康保险分享药物研究信息。']:
            self.assertEqual(code(t)['labels']['Ec'],0,t)

    def test_rd_background_is_not_an_innovation_criterion(self):
        for text in ['新药研发的失败率较高。','创新药研发早期需持续更新安全性风险。','印发《创新药研发期间风险管理计划》。','在创新药研发中考虑老年人特点。']:
            self.assertEqual(code(text)['labels']['I'],0)
        r=code('创新药研发早期需持续更新安全性风险。')
        self.assertEqual(r['labels']['S'],1)
        r=code('开发适配创新药研发需求的数据产品，支持企业合理确定研发方向。')
        self.assertEqual(r['labels']['I'],1)
        self.assertEqual(r['innovation_subtypes'],['research_support'])
        r=code('药品申报资料说明是否为国家“重大新药创制”科技重大专项支持上市药品。')
        self.assertEqual(r['innovation_subtypes'],['attribute'])
        self.assertEqual(code('组织重大新药创制专项专家会议。')['labels']['I'],0)

    def test_innovation_subtypes_follow_separate_evidence(self):
        r=code('提交药品创新性信息。')
        self.assertEqual(r['innovation_subtypes'],['attribute'])
        self.assertEqual(r['innovation_subtype_status'],'complete')
        r=code('支持创新药研发，说明药品自主知识产权。')
        self.assertEqual(r['innovation_subtypes'],['attribute','research_support'])
        self.assertEqual(r['innovation_subtype_status'],'complete')
        r=code_unit(dict(unit_text='具有明显临床优势。',verified_parent_context=[{'paragraph_id':'p1','text':'突破性治疗药物程序应满足以下条件。'}]))
        self.assertEqual(r['innovation_subtypes'],['qualification_advantage'])
        self.assertEqual(next(e for e in r['evidence'] if e['rule']=='I04')['governing_paragraph_ids'],['p1'])

    def test_bare_rd_token_does_not_invent_support_subtype(self):
        r=code('登记新药研发项目。')
        self.assertEqual(r['innovation_subtype_status'],'not_applicable')
        self.assertEqual(r['innovation_subtypes'],[])
        self.assertEqual(r['labels']['I'],0)
        self.assertEqual(code('创新药上市后支付范围。')['innovation_subtype_status'],'not_applicable')
        r=code_unit(dict(unit_text=None))
        self.assertEqual(r['innovation_subtype_status'],'undetermined')

    def test_drug_coverage_and_specific_access_restrictions(self):
        for text in ['推动商业健康保险产品扩大创新药支付范围。','扩展药品的保障范围。','高血压、糖尿病用药不受“一品两规”限定。']:
            r=code(text);self.assertEqual(r['labels']['F'],1)
            self.assertIn('access',r['fairness_subtypes'])
        for text in ['讨论创新药支付范围名称。','扩大科研项目经费支付范围。','用药管理不受机构编制限定。','医疗设备使用不受“一品两规”限定。']:
            self.assertEqual(code(text)['labels']['F'],0)

    def test_normalized_matching_preserves_original_evidence(self):
        text='推动商业健康保险产品扩⼤创新药⽀付范 围'
        r=code(text);self.assertEqual(r['labels']['F'],1)
        for e in r['evidence']+r['suppressions']:
            self.assertEqual(text[e['start']:e['end']],e['text'])
        self.assertEqual(r['evidence'][0]['text'],'扩⼤创新药⽀付范 围')
        import hashlib
        self.assertEqual(r['unit_text_sha256'],hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(code('药品信息不含经济 性信息予以公示。')['labels']['Ec'],0)
        self.assertEqual(code('药品  创新性信息予以公示。')['labels']['I'],0)
        self.assertEqual(code('药品临床疗 效。')['labels']['E'],1)
        self.assertEqual(code('药品临床疗。')['labels']['E'],0)

    def test_defective_input_is_undetermined_not_negative(self):
        for status in ['text_problem', 'context_insufficient']:
            result=code_unit(dict(unit_text='药品安全性和疗效', input_assessment={'status':status,'reason':'缺少关键限定条件'}))
            self.assertEqual(result['labels'],dict.fromkeys(['S','E','Ec','I','F'],None))
            self.assertEqual(result['judgement_status'],'undetermined')
            self.assertEqual(result['evidence'],[])
        for text in [None, '', '   ']:
            result=code_unit(dict(unit_text=text))
            self.assertTrue(all(v is None for v in result['labels'].values()))
            self.assertEqual(result['issue_reason'],'missing_unit_text')

    def test_no_match_is_not_missing_context(self):
        result=code_unit(dict(unit_text='完善办事流程。',input_assessment={'status':'sufficient','basis':'完整自足句，已逐字核对'}))
        self.assertTrue(all(v==0 for v in result['labels'].values()))
        self.assertEqual(result['judgement_status'],'rule_prediction')
        self.assertEqual(result['input_assessment_status'],'sufficient')
        result=code('完善办事流程。')
        self.assertEqual(result['input_assessment_status'],'not_assessed')

    def test_precheck_requires_reason_and_does_not_imply_accuracy(self):
        for assessment in [{'status':'context_insufficient'},{'status':'sufficient'},{'status':'bogus'}]:
            with self.assertRaises(AssertionError):code_unit(dict(unit_text='药品疗效',input_assessment=assessment))
        result=code_unit(dict(unit_text='药品疗效',input_assessment={'status':'sufficient','basis':'完整文本'}))
        self.assertEqual(result['labels']['E'],1)
        self.assertEqual(result['status'],'development_output_not_validated')

    def test_disclosure_names_follow_same_rule_across_dimensions(self):
        r=code('药品申报信息包括有效性、安全性、创新性、公平性方面的信息，进行公示。')
        self.assertFalse(any(r['labels'].values()))
        r=code('药品安全性、有效性信息进行公示，并补充长期疗效和不良反应数据。')
        self.assertEqual(r['labels']['S'],1)
        self.assertEqual(r['labels']['E'],1)
        self.assertTrue(any(e['text']=='疗效' for e in r['evidence']))
        self.assertEqual(code('药品申报材料应提交创新性信息。')['labels']['I'],1)
        self.assertEqual(code('对药品创新性进行评价并公开评价依据。')['labels']['I'],1)


    def test_cost_does_not_cross_word_boundary(self):
        self.assertEqual(code('形成本机构重点监控合理用药药品目录。')['labels']['Ec'],0)
        self.assertEqual(code('形成本地区药品管理制度。')['labels']['Ec'],0)
        self.assertEqual(code('形成药品成本效果分析报告。')['labels']['Ec'],1)
        self.assertEqual(code('形成本机构药品目录，并比较治疗成本。')['labels']['Ec'],1)

    def test_fairness_information_requirements(self):
        r=code('药品申报材料应提供公平性信息。')
        self.assertEqual(r['labels']['F'],1)
        self.assertEqual(r['fairness_subtypes'],['dimension_information'])
        self.assertEqual(code('药品评审过程应维护公平性。')['labels']['F'],0)
        r=code('提交药品公平性资料，说明患者药费负担及可及性。')
        self.assertIn('dimension_information',r['fairness_subtypes'])
        self.assertIn('access',r['fairness_subtypes'])

    def test_economic_disclosure_exclusion_is_local(self):
        for t in ['药品申报资料（不含经济性信息）进行公示。','企业填报药品信息（除经济性以外）将在官网公示。']:
            self.assertEqual(code(t)['labels']['Ec'],0)
        r=code('药品申报资料（不含经济性信息）进行公示，并提交成本效果分析。')
        self.assertEqual(r['labels']['Ec'],1)
        self.assertTrue(any(e['text']=='成本' for e in r['evidence']))
        self.assertEqual(code('药品申报材料不含经济性信息，应补充。')['labels']['Ec'],1)
        self.assertEqual(code('提交药品经济性评价资料。')['labels']['Ec'],1)


    def test_drug_transaction_volume(self):
        r=code('近3年未向医保定点医药机构供应或国家医保信息平台上无交易量的常规目录药品。')
        self.assertEqual(r['labels']['Ec'],1)
        self.assertTrue(any(e['rule']=='Ec03' for e in r['evidence']))
        self.assertEqual(code('核查药品交易量。')['labels']['Ec'],1)
        self.assertEqual(code('核查设备交易量。')['labels']['Ec'],0)
        self.assertEqual(code('评审专家提出药品支付范围调整建议。')['labels']['Ec'],0)


    def test_quality_safety_subtypes(self):
        self.assertEqual(code('控制药品质量风险。')['safety_subtypes'],['quality_safety'])
        self.assertEqual(code('分析药物不良反应。')['safety_subtypes'],['other_safety'])
        self.assertEqual(code('控制药品质量风险并监测不良反应。')['safety_subtypes'],['other_safety','quality_safety'])
        self.assertEqual(code('完善药品质量标准。')['safety_subtypes'],[])


    def test_verified_table_object_and_no_header_label_leakage(self):
        def row(cells, caption='示例表：药物X的临床研发计划表', headers=None):
            return dict(unit_text=' | '.join(cells), unit_type='example_table_row',
                verified_table_context=[dict(caption=caption, headers=headers or ['分期','研究内容'],row_cells=cells)])
        r=code_unit(row(['II期','有效性、安全性']))
        self.assertEqual((r['labels']['S'],r['labels']['E']),(1,1))
        self.assertEqual(code_unit(row(['I期','PK']))['labels'],dict(S=0,E=0,Ec=0,I=0,F=0))
        self.assertEqual(code_unit(row(['I期','PK'],headers=['药物安全性','有效性']))['labels'],dict(S=0,E=0,Ec=0,I=0,F=0))
        self.assertEqual(code_unit(row(['II期','有效性、安全性'],caption='设备性能试验表'))['labels'],dict(S=0,E=0,Ec=0,I=0,F=0))
        bad=row(['II期','安全性']);bad['unit_text']='另一行'
        with self.assertRaises(AssertionError):code_unit(bad)


    def test_explicit_drug_quality_safety_and_risk(self):
        cases=json.loads((Path(__file__).parent/'药品质量安全-开发例句.json').read_text())['examples']
        for case in cases:
            result=code_unit(case)
            self.assertEqual(result['labels']['S'],1)
            for e in result['evidence']:
                self.assertEqual(case['unit_text'][e['start']:e['end']],e['text'])

    def test_quality_alone_is_not_safety(self):
        for text in ['完善药品质量标准。','开展药品质量检测。','确保药品研究数据质量。']:
            self.assertEqual(code(text)['labels']['S'],0)
        self.assertEqual(code('明确设备质量安全要求。')['labels']['S'],0)
        self.assertEqual(code('药品质量安全风险尚未排除。')['labels']['S'],1)

    def test_drug_use_amount_source_examples(self):
        cases=json.loads((Path(__file__).parent/'药品使用金额-开发例句.json').read_text())['examples']
        for case in cases:
            with self.subTest(unit=case['review_id']):
                result=code_unit(case)
                self.assertEqual(result['labels']['Ec'],1)
                for e in result['evidence']:
                    self.assertEqual(case['unit_text'][e['start']:e['end']],e['text'])

    def test_non_drug_use_amount_mask_is_local(self):
        self.assertEqual(code('汇总设备使用金额。')['labels']['Ec'],0)
        self.assertEqual(code('药品管理科负责填报设备使用金额。')['labels']['Ec'],0)
        self.assertEqual(code('药品管理科负责填报设备使用金额，并核对药品价格。')['labels']['Ec'],1)
        self.assertEqual(code('掌握其使用金额。','对药品开展监测，掌握其使用金额。')['labels']['Ec'],1)
        self.assertEqual(code('加强药品使用管理。')['labels']['Ec'],0)

    def test_basic_insurance_regulation_development_boundaries(self):
        cases=json.loads((Path(__file__).parent/'医保用药办法-边界开发例句.json').read_text())['examples']
        for case in cases:
            with self.subTest(unit=case['review_id']):
                result=code_unit(case)
                for dim,value in case['expected_dimensions'].items():self.assertEqual(result['labels'][dim],value)
                for e in result['evidence']:self.assertEqual(case['unit_text'][e['start']:e['end']],e['text'])

    def test_expert_specialty_mask_is_local_and_safety_efficacy_is_substantive(self):
        self.assertEqual(code('组织药物经济学、医保管理等方面专家评审药品。')['labels']['Ec'],0)
        self.assertEqual(code('组织药物经济学、医保管理等方面专家评审药品，同时核对药品价格。')['labels']['Ec'],1)
        self.assertEqual(code('提交药品的药物经济学评价资料。')['labels']['Ec'],1)
        self.assertEqual(code('确保药品安全有效。')['labels']['S'],1)
        self.assertEqual(code('确保药品安全有效。')['labels']['E'],1)
        self.assertEqual(code('药品申报数据的安全有效管理。')['labels']['E'],0)

    def test_complete_qualification_list_and_boundary(self):
        cases = json.loads((Path(__file__).parent / '连续资格条款开发例句.json').read_text())['examples']
        for case in cases:
            with self.subTest(unit=case['review_id']):
                actual = code_unit(case)
                correction = json.loads((Path(__file__).parent / 'v21历史开发预期纠错.json').read_text()).get(case['review_id'], {})
                self.assertEqual(actual['labels'], correction.get('labels', case['development_labels']))
                self.assertEqual(actual['fairness_subtypes'], case['fairness_subtypes'])

    def test_five_verified_context_development_cases(self):
        cases = json.loads((Path(__file__).parent / '编码语境开发结论.json').read_text())['examples']
        for case in cases:
            with self.subTest(unit=case['review_id']):
                actual = code_unit(case)
                correction = json.loads((Path(__file__).parent / 'v21历史开发预期纠错.json').read_text()).get(case['review_id'], {})
                self.assertEqual(actual['labels'], correction.get('labels', case['development_labels']))
                for e in actual['evidence']:
                    self.assertEqual(case['unit_text'][e['start']:e['end']], e['text'])

    def test_20_third_batch_development_cases(self):
        cases = json.loads((Path(__file__).parent / '跨部门编码边界开发-第三批.json').read_text())['examples']
        for case in cases:
            with self.subTest(unit=case['review_id']):
                actual = code_unit(case)
                correction = json.loads((Path(__file__).parent / 'v21历史开发预期纠错.json').read_text()).get(case['review_id'], {})
                self.assertEqual(actual['labels'], correction.get('labels', case['development_labels']))
                self.assertEqual(set(actual['fairness_subtypes']), set(correction.get('fairness_subtypes', case['fairness_subtypes'])))
                for e in actual['evidence']:
                    self.assertEqual(case['unit_text'][e['start']:e['end']], e['text'])

    def test_30_reviewed_development_cases(self):
        cases = json.loads((Path(__file__).parent / '跨部门编码边界开发-第二批.json').read_text())['examples']
        for case in cases:
            with self.subTest(unit=case['review_id']):
                actual = code_unit(case)
                correction = json.loads((Path(__file__).parent / 'v21历史开发预期纠错.json').read_text()).get(case['review_id'], {})
                self.assertEqual(actual['labels'], correction.get('labels', case['development_labels']))
                self.assertEqual(set(actual['fairness_subtypes']), set(correction.get('fairness_subtypes', case['fairness_subtypes'])))
                for e in actual['evidence']:
                    self.assertEqual(case['unit_text'][e['start']:e['end']], e['text'])

    def test_data_access_mask_is_local(self):
        self.assertEqual(code('药品评价模型选择可获得的数据。')['labels']['F'], 0)
        r = code('药品评价模型选择可获得的数据，同时改善药品可获得性。')
        self.assertEqual(r['labels']['F'], 1)
        self.assertTrue(r['suppressions'])

    def test_obtaining_response_is_not_drug_access(self):
        self.assertEqual(code('该药物治疗可获得完全应答。')['labels']['F'], 0)
        self.assertEqual(code('改善患者可获得的药品种类。')['labels']['F'], 1)

    def test_non_drug_risk_and_genuine_adverse_effect_same_unit(self):
        r = code('保障药品研究数据安全，同时监测药物不良反应。')
        self.assertEqual(r['labels']['S'], 1)
        self.assertEqual([e['text'] for e in r['evidence'] if e['dimension'] == 'S'], ['不良反应'])

    def test_validity_does_not_erase_effect(self):
        r = code('药品资料应在有效期内提交，并提供比较疗效证据。')
        self.assertEqual(r['labels']['E'], 1)
        self.assertEqual(code('药品资料应在有效期内提交。')['labels']['E'], 0)

    def test_negation_still_addresses_effect(self):
        self.assertEqual(code('目前没有证据证明该药品疗效优于对照。')['labels']['E'], 1)

    def test_trial_evidence_is_not_automatically_effectiveness(self):
        r = code('药物临床试验须提供不良反应的因果证据。')
        self.assertEqual(r['labels']['S'], 1)
        self.assertEqual(r['labels']['E'], 0)

    def test_innovation_object_and_admin_timing_not_substantive_innovation(self):
        r = code('创新药申请人应于5日内提交优先审评申请。')
        self.assertEqual(r['labels']['I'], 0)
        self.assertEqual(code('鼓励新药研发。')['labels']['I'], 1)

    def test_paragraph_can_resolve_object_but_not_supply_labels(self):
        p = '药品评价涉及安全性、有效性和经济性。另须提供临床管理难度资料。'
        r = code('另须提供临床管理难度资料。', p)
        self.assertEqual(r['labels'], dict(S=0, E=0, Ec=0, I=0, F=1))

    def test_slide_mask_does_not_erase_actual_price_requirement(self):
        r = code('药品摘要幻灯片另有不含经济性/价格费用信息的版本；同时应提供药品价格比较资料。')
        self.assertEqual(r['labels']['Ec'], 1)

    def test_generic_medical_event_has_no_drug_scope(self):
        self.assertEqual(code('每百出院人次主动报告不良事件例次。')['labels']['S'], 0)

    def test_drug_object_does_not_turn_team_interaction_into_safety(self):
        self.assertEqual(code('关注药物研发团队相互作用。')['labels']['S'], 0)
        self.assertEqual(code('评估药物与合并用药之间的相互作用。')['labels']['S'], 1)

    def test_research_investment_not_automatically_treatment_economics(self):
        r = code('为创新药研发提供长期投资支持。')
        self.assertEqual(r['labels']['I'], 1)
        self.assertEqual(r['labels']['Ec'], 0)

    def test_misattributed_adverse_effect_mask_preserves_separate_efficacy_claim(self):
        r = code('患者把服药后的不适感看作是疗效的一部分；仍应评价该药物的比较疗效。')
        self.assertEqual(r['labels']['E'], 1)
        self.assertEqual(len([e for e in r['evidence'] if e['dimension'] == 'E']), 1)

    def test_unverified_heading_does_not_trigger_innovation_qualification(self):
        r = code_unit(dict(unit_text='该药物具有明显临床优势。', paragraph_context=[],
                           nearest_preceding_heading={'text': '突破性治疗药物程序适用条件'}))
        self.assertEqual(r['labels']['E'], 1)
        self.assertEqual(r['labels']['I'], 0)

    def test_institution_name_does_not_supply_safety_claim(self):
        self.assertEqual(code('组织对药物非临床安全性评价研究机构的日常监督检查。')['labels']['S'], 0)
        r = code('药物非临床安全性评价研究机构应报告药物不良反应。')
        self.assertEqual(r['labels']['S'], 1)
        self.assertEqual([e['text'] for e in r['evidence'] if e['dimension'] == 'S'], ['不良反应'])
        self.assertEqual(code('药物非临床安全性评价研究应在认证机构开展。')['labels']['S'], 1)
        self.assertEqual(code('建立药物非临床安全性评价研究机构药品安全信用档案。')['labels']['S'], 1)

    def test_coordinated_drug_quality_safety(self):
        self.assertEqual(code('强化基层药品支付保障和质量安全。')['labels']['S'], 1)
        self.assertEqual(code('强化基层药品支付保障和数据质量。')['labels']['S'], 0)
        self.assertEqual(code('完善药品支付保障和机构网络安全。')['labels']['S'], 0)

    def test_innovative_work_is_not_drug_innovation(self):
        r = code('开展药品使用监测和临床综合评价是一项创新性、系统性工作。')
        self.assertEqual(r['labels']['I'], 0)
        r = code('药品监测是一项创新性、系统性工作，同时须评价药品创新性。')
        self.assertEqual(r['labels']['I'], 1)
        self.assertEqual(len([e for e in r['evidence'] if e['dimension']=='I']), 1)


if __name__ == '__main__':
    unittest.main()

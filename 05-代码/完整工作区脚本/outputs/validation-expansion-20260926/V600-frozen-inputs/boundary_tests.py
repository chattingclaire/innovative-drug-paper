"""Constructed boundary checks: development regressions, not validation data."""
import unittest
import hashlib
import copy
from policy_coding_v4_development import code_unit

def code(text, context=None):
    return code_unit({'unit_text':text,'paragraph_context':[{'text':context}] if context else []})

class CandidateBoundaries(unittest.TestCase):
    def test_medication_error_vs_design(self):
        self.assertEqual(code('药品包装应便于区分，减少用药错误。')['labels']['S'],1)
        self.assertEqual(code('药品包装应使用不同颜色。')['labels']['S'],0)
    def test_object_vs_dimension(self):
        self.assertEqual(code('仿制药应与参比制剂疗效一致。')['labels']['E'],1)
        self.assertEqual(code('申请人选择参比制剂。')['labels']['E'],0)
        self.assertEqual(code('仿制药应与参比制剂质量一致。')['labels']['S'],0)
    def test_quote_condition_vs_administration(self):
        self.assertEqual(code('药品报价均高于100元。')['labels']['Ec'],1)
        self.assertEqual(code('若AB报价均高于100元，该药品不入围。')['labels']['Ec'],1)
        self.assertEqual(code('企业于明日提交报价材料。','本段涉及药品申报。')['labels']['Ec'],0)
        self.assertEqual(code('办公设备报价高于100元。')['labels']['Ec'],0)
    def test_procedure_and_independent_substance(self):
        self.assertEqual(code('五是组织谈判/竞价/价格协商。','本段为药品申报工作安排。')['labels']['Ec'],0)
        self.assertEqual(code('开展价格协商。','药品谈判流程。')['labels']['Ec'],0)
        self.assertEqual(code('组织价格协商；药品支付标准为100元。')['labels']['Ec'],1)
        self.assertEqual(code('药品价格协商不得超过100元。')['labels']['Ec'],1)
    def test_drug_coverage_vs_catalogue_administration(self):
        for text in ['将符合条件的创新药纳入医保目录。','该药品不被纳入《药品目录》。','《药品目录》不再新增OTC药品。','将药品调出基本目录。']:
            self.assertEqual(code(text)['labels']['F'],1,text)
        for text in ['印发药品目录并编号。','药品申报材料纳入电子文件目录。','药品研究机构将设备纳入采购目录。']:
            self.assertEqual(code(text)['labels']['F'],0,text)
    def test_patient_payment_vs_unrelated_payment(self):
        for text in ['药品价格高于支付标准的部分由患者自付。','支付标准以上部分需由患者自付。','药品支付标准包括基金和参保人员共同支付的全部费用。']:
            self.assertEqual(code(text,'本段讨论药品支付标准与费用责任。')['labels']['F'],1,text)
        self.assertEqual(code('药品研究中患者自付交通费用。')['labels']['F'],0)
        self.assertEqual(code('药品企业承担材料印刷费用。')['labels']['F'],0)
    def test_title_mask_keeps_actual_innovation_content(self):
        self.assertEqual(code('按照《中药注册分类及申报资料要求》格式编号整理药物申报资料。')['labels']['I'],0)
        self.assertEqual(code('按照《中药注册分类及申报资料要求》格式编号整理药物申报资料；另需说明创新点。')['labels']['I'],1)
        self.assertEqual(code('申请人应说明药品注册分类。')['labels']['I'],1)
    def test_specific_product_change_vs_dosage_name(self):
        for text in ['严格控制肌肉注射制剂改静脉注射制剂。','大容量注射剂、小容量注射剂之间互改剂型需说明依据。']:
            result=code(text)
            self.assertEqual(result['labels']['I'],1)
            self.assertIn('attribute',result['innovation_subtypes'])
        for text in ['药品采用肌肉注射制剂。','列明药品剂型和规格。']:
            self.assertEqual(code(text)['labels']['I'],0)
    def test_explicit_research_incentive_vs_background(self):
        for text in ['为鼓励研究和创制新药，制定工作程序。','将审评审批资源向符合条件的创新药临床试验申请倾斜。']:
            result=code(text)
            self.assertEqual(result['labels']['I'],1)
            self.assertIn('research_support',result['innovation_subtypes'])
        for text in ['企业提交创新药临床试验申请。','新药研发的失败率较高。','药物试验数据需保密。']:
            self.assertEqual(code(text)['labels']['I'],0)
    def test_supply_monitoring_vs_general_inspection(self):
        for text in ['促进基本药物优先配备使用。','不断提升医疗机构创新药配备使用能力。','定期分析医疗机构药品配备使用情况。','建立药品配备情况监测机制。','进一步提高参保人员用药保障水平。']:
            self.assertEqual(code(text)['labels']['F'],1,text)
        for text in ['加强药品管理工作的监督检查。','药品申报工作提高行政保障水平。','药品监管机构监测办公设备配备情况。']:
            self.assertEqual(code(text)['labels']['F'],0,text)
    def test_unmet_therapy_vs_generic_technology(self):
        self.assertEqual(code('对尚无有效治疗手段疾病的药品，规定拓展使用条件。')['labels']['F'],1)
        self.assertEqual(code('药品研究暂无有效数据处理手段。')['labels']['F'],0)
    def test_product_data_exclusivity_vs_confidentiality(self):
        result=code('原研药品自首次境内上市许可之日起，给予6年数据保护期。')
        self.assertEqual(result['labels']['I'],1)
        self.assertIn('research_support',result['innovation_subtypes'])
        for text in ['药品研究需保护患者个人数据。','药品临床试验数据暂不公开。','机构给予研究数据六年保管期。']:
            self.assertEqual(code(text)['labels']['I'],0,text)
    def test_coverage_ellipsis_with_drug_context(self):
        self.assertEqual(code('原则上列入目录乙类。','谈判药品按本规则纳入常规目录管理。')['labels']['F'],1)
        self.assertEqual(code('确定是否可以纳入医保目录。','讨论同通用名药品的报价。')['labels']['F'],1)
        self.assertEqual(code('协议期内谈判药品纳入“乙类药品”管理。')['labels']['F'],1)
        self.assertEqual(code('查阅药品目录乙类文件。')['labels']['F'],0)
    def test_unmet_need_and_directory_gap(self):
        self.assertEqual(code('该药品可填补目录空白。')['labels']['F'],1)
        self.assertEqual(code('患者治疗需求迫切，因此鼓励研发相关药物。')['labels']['F'],1)
        self.assertEqual(code('儿童患者参加药物研究。')['labels']['F'],0)
    def test_drug_exclusivity_vs_market_status(self):
        self.assertEqual(code('对符合条件的药品给予一定的市场独占期。')['innovation_subtypes'],['research_support'])
        self.assertEqual(code('企业的药品目前市场份额最高。')['labels']['I'],0)
        self.assertEqual(code('药品采用独家生产模式。')['labels']['I'],0)
    def test_direct_drug_names_without_dimension_inheritance(self):
        self.assertEqual(code('中药应提供疗效证据。')['labels']['E'],1)
        self.assertEqual(code('中药研发会议明日召开。')['labels']['E'],0)
        self.assertEqual(code('评价医院软件的有效性，并介绍仿制药政策。')['labels']['E'],0)
    def test_non_drug_cost_scope_not_authorized_by_paragraph(self):
        context='本院讨论药品采购。另行编制门诊大楼建设预算。'
        self.assertEqual(code('门诊大楼建设费用增加。',context)['labels']['Ec'],0)
        self.assertEqual(code('完善医保基金总额预算，与医疗机构绩效考核相挂钩。','另行研究药品支付。')['labels']['Ec'],0)
        self.assertEqual(code('确保患者不因费用问题影响就医。','另外减免用药量限制。')['labels']['Ec'],0)
        self.assertEqual(code('办公设备采购费用减少；同时评价药品成本。')['labels']['Ec'],1)
    def test_actual_drug_cost_kept(self):
        self.assertEqual(code('医疗机构应分析药品费用。')['labels']['Ec'],1)
        self.assertEqual(code('分析药品对医保基金的影响。')['labels']['Ec'],1)
    def test_verified_scope_binding_and_no_label_copy(self):
        text='申办者设计临床试验应当基于安全性和有效性数据。'
        quote='本规范适用于为研制药品而进行的药物临床试验。'
        scope={'kind':'drug_clinical_trial','source_sha256':'fixture-source','unit_text_sha256':hashlib.sha256(text.encode()).hexdigest(),'text':quote,'text_sha256':hashlib.sha256(quote.encode()).hexdigest(),'locator':{'article':2},'verification':'constructed fixture'}
        record={'unit_text':text,'source_sha256':'fixture-source','verified_object_scope':[scope]}
        result=code_unit(record)
        self.assertEqual(result['labels'],dict(S=1,E=1,Ec=0,I=0,F=0))
        self.assertTrue(result['evidence'][0]['object_scope_dependency'])
        for changed in ['source_sha256','unit_text_sha256','text_sha256']:
            bad=copy.deepcopy(record);bad['verified_object_scope'][0][changed]='wrong'
            with self.assertRaises(AssertionError):code_unit(bad)
        for target in ['临床试验文件应按顺序编号。','伦理审查会议的办公设备采购费用增加。']:
            z=copy.deepcopy(record);z['unit_text']=target;z['verified_object_scope'][0]['unit_text_sha256']=hashlib.sha256(target.encode()).hexdigest()
            self.assertEqual(code_unit(z)['labels'],dict(S=0,E=0,Ec=0,I=0,F=0))
    def test_trial_safety_content_requires_drug_object(self):
        self.assertEqual(code('药物试验不能保障受试者安全时应当暂停。')['labels']['S'],1)
        self.assertEqual(code('药物临床试验参与者出现非预期严重损害。')['labels']['S'],1)
        self.assertEqual(code('器械临床试验不能保障受试者安全。')['labels']['S'],0)
    def test_regulatory_scope_not_dimension_copy(self):
        quote='本指南主要用于支持药物监管决策的研究。'
        def scoped(text):
            z={'unit_text':text,'source_sha256':'fixture-source','verified_object_scope':[{'kind':'drug_regulatory_research','source_sha256':'fixture-source','unit_text_sha256':hashlib.sha256(text.encode()).hexdigest(),'text':quote,'text_sha256':hashlib.sha256(quote.encode()).hexdigest(),'locator':{'page':1},'verification':'constructed fixture'}]}
            return code_unit(z)
        self.assertEqual(scoped('敏感性分析用于检查疗效估计偏倚。')['labels']['E'],1)
        self.assertEqual(scoped('患者研究资料应按年份归档。')['labels'],dict(S=0,E=0,Ec=0,I=0,F=0))
        self.assertEqual(scoped('评价患者登记软件的有效性。')['labels']['E'],0)
    def test_substantive_economic_content(self):
        for text in ['药品报价不得高于医保支付意愿。','根据药品测算意见形成医保底价。','完善短缺药品保供稳价机制。','医务人员薪酬不得与药品业务收入挂钩。']:
            self.assertEqual(code(text)['labels']['Ec'],1,text)
        self.assertEqual(code('医院薪酬不得与停车场收入挂钩。')['labels']['Ec'],0)
    def test_exclusion_is_local_not_whole_unit(self):
        self.assertEqual(code('审核医疗用毒性药品处方权限。')['labels']['S'],0)
        self.assertEqual(code('审核医疗用毒性药品处方权限，并评价药物毒性。')['labels']['S'],1)
        self.assertEqual(code('以药品临床价值为导向开展工作。')['labels']['E'],0)
        self.assertEqual(code('以药品临床价值为导向，同时补充疗效数据。')['labels']['E'],1)
        self.assertEqual(code('评价药品研究科学方面的有效性。')['labels']['E'],0)
    def test_procedure_does_not_erase_payment_rule(self):
        self.assertEqual(code('企业确认是否参与药品谈判或价格协商。')['labels']['Ec'],0)
        self.assertEqual(code('竞价药品支付标准有效期到期后纳入常规目录。')['labels']['Ec'],0)
        self.assertEqual(code('药品支付标准有效期到期后仍按原标准支付药品费用。')['labels']['Ec'],1)
        self.assertEqual(code('研发期间安全性更新报告应当每年提交一次。','药物临床试验工作。')['labels']['S'],0)
        self.assertEqual(code('研发期间安全性更新报告应当每年提交一次，并新增药物不良事件收集要求。')['labels']['S'],1)
    def test_explicit_definition_relation_not_whole_paragraph(self):
        text='抗肿瘤药物关键试验应进行期中分析。'
        definition='期中分析定义为正式完成临床试验前对临床数据的有效性和安全性进行分析。'
        result=code(text,definition+text)
        self.assertEqual(result['labels']['S'],1)
        self.assertEqual(result['labels']['E'],1)
        self.assertTrue(any(e.get('context_dependency') for e in result['evidence']))
        self.assertEqual(code('抗肿瘤药物期中分析文件按日期归档。',definition)['labels']['S'],0)
        self.assertEqual(code('抗肿瘤药物进行期中分析，仅核查入组人数。',definition)['labels']['E'],0)
        self.assertEqual(code('抗肿瘤药物关键试验应进行期中分析。','期中分析定义为核查药物试验入组人数。')['labels']['E'],0)
    def test_specific_analysis_relation_not_general_study(self):
        current='合并分组的方法应在统计分析报告中具体说明。'
        context='药物不良事件分析应规范AE报告的原则。临床意义相同的医学概念可以适当合并分组。'+current
        self.assertEqual(code(current,context)['labels']['S'],1)
        self.assertEqual(code(current,'药物试验按年龄合并分组。'+current)['labels']['S'],0)
        text='因此，应该尽可能减少受试者的无效暴露。'
        self.assertEqual(code(text,'药物剂量研究中患者往往无法接受到充分、有效的治疗。'+text)['labels']['E'],1)
        self.assertEqual(code('药物研究文件按日期归档。','本研究评价药物疗效和安全性。')['labels']['E'],0)
    def test_combination_purpose_dimension_specific(self):
        text='例如药物联合治疗出现多种组合。'
        result=code(text,'为了提高疗效，积极探索联合用药方案。'+text+'后续另行评估安全性风险。')
        self.assertEqual(result['labels']['E'],1)
        self.assertEqual(result['labels']['S'],0)
        self.assertEqual(code(text,'为便于药品包装运输，探索多种组合。'+text)['labels']['E'],0)
    def test_stop_condition_preserves_quality_and_other_bases(self):
        text='药品监督管理部门依职责可以责令暂停或者终止药物临床试验。'
        both='药物临床试验中出现严重不良反应，或者临床试验用药品存在严重质量问题时，应当立即停止药物临床试验。'+text
        result=code(text,both)
        self.assertEqual(result['labels']['S'],1)
        self.assertEqual(result['safety_subtypes'],['other_safety','quality_safety'])
        quality='临床试验用药品存在严重质量问题时，应当立即停止药物临床试验。'+text
        self.assertEqual(code(text,quality)['safety_subtypes'],['quality_safety'])
        self.assertEqual(code(text,'药物临床试验因行政材料不完整暂停。'+text)['labels']['S'],0)
        self.assertEqual(code('另因财务审计暂停另一项药物临床试验。',both)['labels']['S'],0)
    def test_renewal_component_scope_and_content(self):
        quote='同时满足以下条件的药品，可以简易续约，续约有效期2年。'
        def record(text):
            return {'unit_text':text,'source_sha256':'main','unit_source_sha256':'component',
                'verified_rule_branch_context':{'text':'规则二 简易续约'},
                'verified_object_scope':[{'kind':'negotiated_drug_renewal','source_sha256':'component',
                    'source_hash_field':'unit_source_sha256','required_branch_text':'规则二简易续约',
                    'unit_text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                    'text':quote,'text_sha256':hashlib.sha256(quote.encode()).hexdigest(),
                    'locator':{'physical_pages':[2]},'verification':'constructed fixture'}]}
        self.assertEqual(code_unit(record('基金实际支出由医保部门统计。'))['labels']['Ec'],1)
        self.assertEqual(code_unit(record('基金年均实际支出=(去年基金实际支出+当年上半年基金实际支出×2)/2。'))['labels']['Ec'],1)
        for text in ['资料须按时间顺序归档。','汇总医疗机构门诊大楼建设费用。']:
            self.assertEqual(code_unit(record(text))['labels'],dict(S=0,E=0,Ec=0,I=0,F=0))
        self.assertEqual(code('基金实际支出由医保部门统计。')['labels']['Ec'],0)
        z=record('基金实际支出由医保部门统计。')
        for field,value in [('unit_source_sha256','other-component'),('verified_rule_branch_context',{'text':'规则三重新谈判'})]:
            bad=copy.deepcopy(z);bad[field]=value
            with self.assertRaises(AssertionError):code_unit(bad)
        bad=copy.deepcopy(z);bad['verified_object_scope'][0]['source_hash_field']='source_sha256';bad['verified_object_scope'][0]['source_sha256']='main'
        with self.assertRaises(AssertionError):code_unit(bad)
        market=record('市场环境未发生重大变化。')
        market['paragraph_context']=[{'text':'市场环境未发生重大变化。“重大变化”主要是指同治疗领域中价格明显偏高或者低于现行支付标准。'}]
        self.assertEqual(code_unit(market)['labels']['Ec'],1)
        market['paragraph_context']=[]
        self.assertEqual(code_unit(market)['labels']['Ec'],0)

    def test_drug_access_arrangements_not_general_administration(self):
        for text in ['企业故意不供货时将药品调出目录。','基层医疗卫生机构应开展用药需求评估。','给药装置应尽可能附在药品包装中，以避免难以获得装置。']:
            z=code(text)
            self.assertEqual(z['labels']['F'],1,text)
            self.assertEqual(z['fairness_subtypes'],['access'])
        for text in ['将药品目录文件调出归档目录。','医院开展会议服务需求评估。','给药装置应附在药品包装中，附清晰的使用说明。']:
            self.assertEqual(code(text)['labels']['F'],0,text)
        self.assertEqual(code('给药装置应尽可能附在药品包装中，以避免难以获得装置。')['labels']['S'],0)

    def test_clinical_evidence_and_payment_expressions(self):
        self.assertEqual(code('获得药物在儿童人群中的安全有效性证据。')['labels']['S'],1)
        self.assertEqual(code('为了确保临床试验安全，应评价试验药物风险。')['labels']['S'],1)
        self.assertEqual(code('评价药物在老年人群中的获益风险情况。')['labels']['E'],1)
        self.assertEqual(code('研究药物不良反应对患者生活质量的影响。')['labels']['E'],1)
        self.assertEqual(code('研究创新药在DRG/DIP付费中的除外支付政策。')['labels']['Ec'],1)
        for text,dim in [('维护器械临床试验安全。','S'),('评价办公环境干预效果。','E'),('医院员工生活质量调查。','E'),('研究先进医疗技术在DRG付费中的除外支付政策。','Ec')]:
            self.assertEqual(code(text)['labels'][dim],0)

    def test_quality_risk_overlap_is_not_independent_other_basis(self):
        self.assertEqual(code('加强药品质量风险管理。')['safety_subtypes'],['quality_safety'])
        self.assertEqual(code('评价药品质量安全性。')['safety_subtypes'],['quality_safety'])
        self.assertEqual(code('评价药品质量安全性；同时评价患者用药安全性。')['safety_subtypes'],['other_safety','quality_safety'])
        self.assertEqual(code('评价药品质量安全性，并监测药物不良反应。')['safety_subtypes'],['other_safety','quality_safety'])
        self.assertEqual(code('加强药品质量风险管理，同时监测药物不良反应。')['safety_subtypes'],['other_safety','quality_safety'])
        self.assertEqual(code('加强药品质量风险控制；另行开展患者用药风险管理。')['safety_subtypes'],['other_safety','quality_safety'])
    def test_priority_review_does_not_inherit_breakthrough_status(self):
        text='与现有治疗手段相比具有明显临床优势。'
        parents=[{'paragraph_id':'priority','text':'申请优先审评应满足以下条件，临床优势参照突破性治疗药物程序标准。'}]
        self.assertEqual(code_unit({'unit_text':text,'verified_parent_context':parents})['labels']['I'],0)
        split=[{'paragraph_id':'p1','text':'介绍突破性治疗药物程序。'},{'paragraph_id':'p2','text':'医院信息化项目需满足以下条件。'}]
        self.assertEqual(code_unit({'unit_text':text,'verified_parent_context':split})['labels']['I'],0)
        genuine=[{'paragraph_id':'p1','text':'申请突破性治疗药物程序应满足以下条件。'}]
        self.assertEqual(code_unit({'unit_text':text,'verified_parent_context':genuine})['innovation_subtypes'],['qualification_advantage'])
    def test_clinical_scope_does_not_convert_office_objects(self):
        quote='本规范适用于为研制药品而进行的药物临床试验。'
        def scoped(text):
            return code_unit({'unit_text':text,'source_sha256':'fixture-source','verified_object_scope':[{'kind':'drug_clinical_trial','source_sha256':'fixture-source','unit_text_sha256':hashlib.sha256(text.encode()).hexdigest(),'text':quote,'text_sha256':hashlib.sha256(quote.encode()).hexdigest(),'locator':{'article':2},'verification':'constructed fixture'}]})
        for text in ['研究者应解决归档打印纸供应短缺。','研究者会议交通费用增加。','临床试验服务器风险管理。','评价临床试验管理制度有效性。']:
            self.assertEqual(scoped(text)['labels'],dict(S=0,E=0,Ec=0,I=0,F=0),text)
        mixed=scoped('研究者会议交通费用增加；同时比较药品费用。')
        self.assertEqual(mixed['labels']['Ec'],1)
        self.assertEqual(scoped('临床试验服务器风险管理，同时监测药物不良反应。')['labels']['S'],1)
    def test_registration_archive_preserves_separate_attribute(self):
        self.assertEqual(code('药品注册分类资料按编号归档。')['labels']['I'],0)
        self.assertEqual(code('药品注册分类资料按编号归档，同时评价药品的新作用机制。')['labels']['I'],1)
        self.assertEqual(code('提交药品注册分类信息供评价。')['labels']['I'],1)

    def test_uncertain_phrases_not_silently_expanded(self):
        self.assertEqual(code('收集药物反应数据。')['labels']['E'],0)
        self.assertEqual(code('药品能够满足临床需求。')['labels']['E'],0)

if __name__=='__main__':unittest.main()

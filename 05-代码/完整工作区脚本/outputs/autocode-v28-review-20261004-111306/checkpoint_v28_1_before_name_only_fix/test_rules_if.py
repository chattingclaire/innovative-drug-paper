import copy
import hashlib
import unittest
from rule_support import rebuild
import policy_coding_v26_2 as old
from rules_if import revise


def record(text, **kwargs):
    return dict(unit_text=text,input_assessment={'status':'sufficient','basis':'constructed complete regression example'},**kwargs)


def run(text, **kwargs):
    r=record(text,**kwargs)
    result=old.code_unit(r)
    revise(r,result)
    return rebuild(result)


def bound_scope(text):
    quote='用于尚无有效防治手段的疾病且具有明显临床优势的创新药或者改良型新药，可以申请适用突破性治疗药物程序。'
    digest=lambda value:hashlib.sha256(value.encode()).hexdigest()
    return dict(source_sha256=digest('synthetic source'),unit_id='synthetic-unit',candidate_sha256=digest('synthetic candidate'),
                verified_innovation_scope_v27=dict(text=quote,text_sha256=digest(quote),source_sha256=digest('synthetic source'),
                  original_unit_sha256=digest(text),component='突破性治疗程序',verified=True,
                  locator={'paragraph_id':'synthetic-scope','source_lines':[1]},
                  component_binding={'unit_id':'synthetic-unit','candidate_sha256':digest('synthetic candidate')}))


class IFReviewTest(unittest.TestCase):
    def assert_case(self,text,i,f,subtype=None,**kwargs):
        r=run(text,**kwargs)
        self.assertEqual((r['labels']['I'],r['labels']['F']),(i,f),text)
        if subtype:
            self.assertIn(subtype,r['innovation_subtypes']+r['fairness_subtypes'],text)
        for e in r['evidence']:
            self.assertEqual(text[e['start']:e['end']],e['text'])
        return r

    def test_attribute_and_content(self):
        for t in ['评价药品创新性。','该药缺乏创新性。','提交药品创新性信息。','药物的作用机制新颖性尚不能确定。','该药物采用新靶点。','该药品原创性不足。','该药创新程度较低。']:
            with self.subTest(t=t): self.assert_case(t,1,0,'attribute')

    def test_v28_amount_definition_and_membership_subject(self):
        self.assert_case('纳入支付范围的药品费用是指属于医保支付范围内的药品费用。',0,0)
        self.assert_case('药品的支付范围调整属于医保药品目录调整工作的一部分。',0,0)
        self.assert_case('连续纳入目录的药品达到五年，之前纳入基本目录，支付标准降幅减半。',0,0)
        self.assert_case('该药品不属于医保支付范围。',0,1)
        self.assert_case('药品费用是指属于医保支付范围内的药品费用；患者仍无法承担药费。',0,1)

    def test_v28_research_instruments_and_non_innovation_controls(self):
        for t in ['鼓励医生参与药品技术创新活动。','支持药物临床试验机构参与创新药物早期临床研发。','组织实施创新药物研发国家科技重大专项。','促进医疗机构中药制剂向新药转化。','药品医疗器械科技创新支撑不够。','围绕创新药等重点领域建设成果转化服务平台。']:
            with self.subTest(t=t):self.assert_case(t,1,0,'research_support')
        for t in ['缩短创新药临床试验沟通时限。','支持开展国际多中心临床试验。','鼓励医生参与医院管理创新活动。','该创新药申请应在七日内上传。','为支持创新药发展，现发布工作通知。']:
            with self.subTest(t=t):self.assert_case(t,0,0)

    def test_v28_data_right_scope_lifecycle_and_nondrug_control(self):
        for t in ['药品获批上市后，对未披露试验数据给予数据保护。','该药品数据保护期届满后方可批准其他申请人的上市申请。','药品持有人主动放弃数据保护的，数据保护终止。','该药品增加适应症，对相应保护数据给予4年数据保护期。']:
            with self.subTest(t=t):self.assert_case(t,1,0,'research_support')
        for t in ['软件数据保护期届满。','药品材料已经提交，办公日志数据保护终止。','药品数据保护期报告按编号归档。']:
            with self.subTest(t=t):self.assert_case(t,0,0)

    def test_v28_product_comparison_and_explicit_innovation_class(self):
        for t in ['说明和已上市中药处方对比情况。','非处方药改变剂型，但不改变适应症。','试点范围为1类创新药临床试验申请。','要求创新程度高、临床价值大的创新药。']:
            with self.subTest(t=t):self.assert_case(t,1,0,'attribute')
        for t in ['药品新品种、剂型、规格分别填报。','药械组合产品应当按照药品申报。','该创新药已上市。']:
            with self.subTest(t=t):self.assert_case(t,0,0)

    def test_v28_parent_criterion_and_supply_anaphor(self):
        parent=[{'paragraph_id':'scope','text':'以下药品不纳入《药品目录》：'}]
        self.assert_case('（三）保健药品。',0,1,verified_parent_context=parent)
        self.assert_case('（三）保健药品。',0,0)
        self.assert_case('药品申请应在十日内提交。',0,0,verified_parent_context=parent)
        t='企业供应情况发生重大变化，必须在一个月内报国家医保局。'
        self.assert_case(t,0,1,paragraph_context=[{'paragraph_id':'p','text':'企业须保证市场供应，无合理理由不得断供。'+t}])
        self.assert_case(t,0,0,paragraph_context=[{'paragraph_id':'p','text':'企业须完成办公软件采购。'+t}])
        t='如谈判失败，调出目录。'
        self.assert_case(t,0,1,paragraph_context=[{'paragraph_id':'p','text':'该药品可申请重新谈判。'+t}])
        self.assert_case(t,0,0,paragraph_context=[{'paragraph_id':'p','text':'办公设备可申请重新谈判。'+t}])
        t='原则上列入目录乙类。'
        self.assert_case(t,0,1,paragraph_context=[{'paragraph_id':'p','text':'该药品通过准入评价。'+t}])
        self.assert_case(t,0,0)
        self.assert_case('办公设备原则上列入目录乙类。',0,0)

    def test_v28_coverage_payment_and_procedure_only(self):
        for t in ['药品确认医保支付标准后纳入目录。','该药品纳入医保乙类目录。','对药品给予DRG/DIP付费中除外支付。','该药物不适合按病种标准支付的，可申报特例单议。','及时将新药纳入公立医院药品集中采购范围。','临时调整医保药品支付范围。','免除医保目录、支付限额、用药量等限制性条款。']:
            with self.subTest(t=t):self.assert_case(t,0,1)
        for t in ['药品按照竞价规则产生医保支付标准。','药品应通过医保目录申报模块提交申请。','药品仅具有已经纳入目录的申报身份。']:
            with self.subTest(t=t):self.assert_case(t,0,0)

    def test_v28_access_supply_and_patient_burden(self):
        for t in ['加大罕见病用药品医疗器械配备和使用力度。','保障临床基本用药的供应。','保障抢救设备和药品可用。','扩大基层用药种类。','中药饮片可按规定跨省销售。','特定医疗机构先行进口临床急需用药品。','了解该药品报销情况以判断患者实际支付水平。','要求提交国内外慈善赠药等资料。']:
            with self.subTest(t=t):self.assert_case(t,0,1)
        for t in ['保障办公设备可用。','药品临床试验中负责向研究者提供试验用药品。','新增医院随访服务。','软件可按规定跨省销售。','该药品价格较低。']:
            with self.subTest(t=t):self.assert_case(t,0,0)

    def test_v28_management_and_explicit_unmet_needs(self):
        for t in ['该药物设计应减少治疗方案的复杂性。','评估药物使用环节中遇到的突出问题。','患者难以记住是否服药。','患者混淆不同药品。','该药物的研究不足可能无法满足老年患者的治疗需求。']:
            with self.subTest(t=t):self.assert_case(t,0,1)
        for t in ['临床试验提高患者接受潜在更优治疗的概率。','药物临床试验应扩大研究代表性。','医疗机构提供一般药物管理服务。','患者需要按时服药。']:
            with self.subTest(t=t):self.assert_case(t,0,0)

    def test_registration(self):
        self.assert_case('该药品注册分类为改良型新药。',1,0,'attribute')
        self.assert_case('说明药品的注册分类。',1,0,'attribute')
        for t in ['该创新药已纳入申报范围。','改良型新药的申请应在十日内提交。','药品注册分类资料按编号归档。','药品属于新上市产品。','药品新品种、剂型、规格分别填报。']:
            with self.subTest(t=t): self.assert_case(t,0,0)

    def test_modification(self):
        for t in ['改良药物结构。','药物结构得到改良。','优化给药途径。','片剂的易碎性得到改善。','口服制剂改为静脉注射制剂。','与原有制剂相比改变释放特征。']:
            with self.subTest(t=t): self.assert_case(t,1,0,'attribute')
        self.assert_case('该药为儿童提供便利的给药方式。',0,0)

    def test_patent_and_support(self):
        self.assert_case('申报药品的专利情况。',1,0,'attribute')
        self.assert_case('该药品没有自主知识产权。',1,0,'attribute')
        for t in ['支持创新药研发。','不再支持创新药研发。','取消对新药研发的支持。','创新药研发得到资金支持。','为新药研发提供资金。','鼓励研究和创制新药。','支持医药企业、科研院所、医疗机构等开展以创新药研发为导向的科研攻关。','审评审批资源向创新药临床试验申请倾斜。','对原研药品给予六年数据保护期。','对符合条件的儿童用药品、首个化学仿制药及独家中药品种给予一定的市场独占期。']:
            with self.subTest(t=t): self.assert_case(t,1,0,'research_support')

    def test_history_support(self):
        t='说明申报药品是否为重大新药创制专项支持的药品。'
        r=self.assert_case(t,1,0,'attribute')
        self.assertNotIn('research_support',r['innovation_subtypes'])

    def test_data_protection_purpose(self):
        self.assert_case('为促进药品创新发展，按照《药品试验数据保护办法》完善药品试验数据保护制度。',1,0,'research_support')
        self.assert_case('药品试验数据保护制度文件按编号归档。',0,0)
        self.assert_case('创新药研发文件已上传，支持医院软件数据保护。',0,0)

    def test_titles_and_wrong_innovation_objects(self):
        for t in ['现发布《支持创新药研发办法》。','现发布《改良给药途径指导原则》。','药品材料已提交，创新性管理系统上线。','药品已批准，软件具有自主知识产权。','药品申请已提交，管理系统的创新性需要评价。']:
            with self.subTest(t=t): self.assert_case(t,0,0)
        self.assert_case('现发布《支持创新药研发办法》，同时不再支持创新药研发。',1,0)

    def test_supply(self):
        for t in ['未按协议约定保障市场供应的谈判药品。','药品供应中断。','药物持续供应应得到保障。','保障药品持续供应。','须优先配备和使用《药品目录》内药品。','提高基本药物优先配备使用水平。','收集药品配备使用情况。','未向医保定点医疗机构供应的药品。']:
            with self.subTest(t=t): self.assert_case(t,0,1,'access')

    def test_coverage(self):
        for t in ['药品自动属于基本医疗保险基金支付范围。','所有符合条件的药品均纳入医保支付范围。','该药品不纳入医保目录。','扩大药品报销范围。','医保基金不予支付药品费用。','符合目录的药品费用按照国家规定由基本医疗保险基金支付。','医保支付条件仅限于重症患者用药。']:
            with self.subTest(t=t): self.assert_case(t,0,1,'access')
        for t in ['药品支付范围填写在表格第二列。','请上传医保药品支付范围表。','药品谈判程序按期举行。']:
            with self.subTest(t=t): self.assert_case(t,0,0)

    def test_coverage_membership_requires_drug_predicate(self):
        for t in [
            '常规目录药品如需新增适应症均申报目录内条件3。',
            '常规目录药品的支付范围调整（说明书没有新增适应症）属于目录调整工作。',
            '纳入支付范围的药品费用是指参保人员发生的医保范围内费用。',
            '企业预测纳入医保支付范围的药品销售金额。',
            '不符合纳入常规目录管理条件的药品。',
            '如成功纳入药品目录，则按规则确定支付标准。',
            '如果连续纳入目录达到四年，则支付标准降幅减半。',
            '建议新增纳入《药品目录》的药品。',
        ]:
            with self.subTest(t=t): self.assert_case(t,0,0)
        self.assert_case('该药品纳入医保支付范围。',0,1,'access')
        self.assert_case('该药品调出医保目录。',0,1,'access')
        self.assert_case('保障药品持续供应。',0,1,'access')
        self.assert_case('近三年未向医保定点医药机构供应或平台上无交易量的常规目录药品。',0,1,'access')

    def test_access_channels(self):
        for t in ['医疗机构为患者送药上门。','患者可以在指定零售药店购药。','扩大药品的双通道供药。','药品配备使用不再受一品两规限制。','不得以药占比影响患者用药。','药物的可获得性不足。']:
            with self.subTest(t=t): self.assert_case(t,0,1,'access')
        for t in ['药品货运公司负责一般配送。','药品研究安排受试者送药上门。','医疗机构在临床试验中为受试者送药上门。']:
            with self.subTest(t=t): self.assert_case(t,0,0)

    def test_access_wrong_objects_and_mixed(self):
        for t in ['药品研究需要数据可及性。','药品研究改善证据的可获得性。','药品材料已收到，办公用品供应短缺。','药品报告已交，信息系统可及性需要改善。','药品临床试验提高代表性并减少访视频次。','儿童、老年和罕见病患者用药。','该药的给药便利性较好。']:
            with self.subTest(t=t): self.assert_case(t,0,0)
        self.assert_case('数据可及性仍不足，药物的可获得性得到改善。',0,1,'access')

    def test_treatment_gaps(self):
        for t in ['该药用于尚无有效治疗手段的患者。','该药用于缺乏有效标准治疗手段的患者。','药品研发应满足未被满足的治疗需求。','该药用于用药需求尚未满足的患者。','该药品用于无药可治的患者。']:
            with self.subTest(t=t): self.assert_case(t,0,1,'access')
        self.assert_case('患者入组后接受试验药物治疗。',0,0)
        self.assert_case('患者无法得到有效治疗，该药提供治疗机会。',0,1,'access')

    def test_affordability(self):
        for t in ['该药品减轻患者的药费负担。','药品价格较低，但患者仍无法承担药费。','该药品患者自付比例增加药费负担。','药品费用由基金和患者共同支付全部费用。','药物的可负担性需要评价。']:
            with self.subTest(t=t): self.assert_case(t,0,1,'affordability')
        for t in ['该药品价格为五十元。','药品研究减轻受试者访视负担。','该药物治疗负担较重。','药品生产企业负担较重。']:
            with self.subTest(t=t): self.assert_case(t,0,0)

    def test_clinical_management(self):
        for t in ['患者打开药品包装存在困难。','患者难以准确量取药物。','服用药物时面临困难。','给药方式较为复杂。','评价该药的临床管理难度。','评价该药监测频率及基层能否完成必要监测。']:
            with self.subTest(t=t): self.assert_case(t,0,1,'clinical_management')
        for t in ['患者服用药物，医院审批面临困难。','患者服用药物而医院审批面临困难。','患者服用药物并说明申报工作遇到困难。','药品需要专科给药和特殊储存。','医疗机构应规范开具处方。','老年患者按时服用药物。']:
            with self.subTest(t=t): self.assert_case(t,0,0)

    def test_information_and_carriers(self):
        self.assert_case('提交药品公平性信息。',0,1,'dimension_information')
        self.assert_case('内容包括药品基本信息、创新性信息、公平性信息。',1,1)
        for t in ['药品创新性信息予以公示。','药品公平性资料按编号归档。','药品申报专家身份包括公平性专家。','药品生产企业公平竞争。']:
            with self.subTest(t=t): self.assert_case(t,0,0)
        self.assert_case('药品公平性资料予以公示，同时提交药品公平性评价证据。',0,1)

    def test_dont_copy_context(self):
        self.assert_case('应在十日内提交。',0,0,paragraph_context=[{'paragraph_id':'p','text':'该药物具有创新性和可及性。应在十日内提交。'}])
        self.assert_case('说明其创新性。',1,0,'attribute',paragraph_context=[{'paragraph_id':'p','text':'现评价该药品。说明其创新性。'}])

    def test_explicit_supply_anaphor(self):
        t='上述义务应在协议中明确。'
        self.assert_case(t,0,1,'access',paragraph_context=[{'paragraph_id':'p','text':'生产企业应保障药品供应。'+t}])
        self.assert_case(t,0,0,paragraph_context=[{'paragraph_id':'p','text':'生产企业应保障药品供应。另行规定财务审计。'+t}])

    def test_qualification_anchors(self):
        good=[{'paragraph_id':'p','text':'创新药或改良型新药申请适用突破性治疗药物程序，应满足以下条件：'}]
        only_program=[{'paragraph_id':'p','text':'申请适用突破性治疗药物程序，应满足以下条件：'}]
        self.assert_case('该药物具有明显临床优势。',1,0,'qualification_advantage',verified_parent_context=good)
        self.assert_case('该药物具有明显临床优势。',0,0,verified_parent_context=only_program)
        self.assert_case('该药物已纳入突破性治疗药物程序，应在十日内提交材料。',0,0,verified_parent_context=good)
        self.assert_case('一般优先审评参照突破性治疗药物的明显临床优势标准。',0,0,verified_parent_context=good)
        self.assert_case('创新药或改良型新药申请适用突破性治疗药物程序须具有明显临床优势。',1,0,'qualification_advantage')

    def test_repaired_object_relations(self):
        for t in ['取消对创新药研发的资金支持。','支持新药和创新器械联合研发。','设立创新药研发资助专项。','根据药物产品特性，创新程度制定要求。','原研药品在满足注册要求之后，对其试验数据给予六年数据保护期。']:
            with self.subTest(t=t):self.assert_case(t,1,0)
        for t in ['患者难以获得所需药物。','药品资料库可及性提高，同时应保障患者获得药物。','三年未向定点医疗机构供应的药品应予核查。']:
            with self.subTest(t=t):self.assert_case(t,0,1,'access')
        for t in ['药品企业应评价信息平台建设工作的创新程度。','药品配备情况表的文件格式应更新为PDF。','药品资料库可及性提高。','软件在满足注册要求之后，对其试验数据给予六年数据保护期。','药品企业的产品特性、创新程度应进行评价。']:
            with self.subTest(t=t):self.assert_case(t,0,0)

    def test_legacy_semantic_group_continuity(self):
        for t in ['药品调出目录。','该药纳入目录乙类。','开展用药需求评估。','该药品填补目录空白。','收集药品配备及供应信息。','药品挂网价格超出支付标准部分由患者自付。','通过慈善捐赠帮助困难群众承担药费。','装置附在药品包装中以避免难以获得装置。']:
            with self.subTest(t=t):self.assert_case(t,0,1)
        for t in ['开展软件需求评估。','该药品的目录文件已上传。','药品研发办公室开展机关用药需求评估报告归档。']:
            with self.subTest(t=t):self.assert_case(t,0,0)

    def test_verified_scope_requires_current_and_parent_anchors(self):
        parent=[{'paragraph_id':'eligibility','text':'药物临床试验期间，申请适用突破性治疗药物程序的，应当同时满足以下条件：'}]
        t='与现有治疗手段相比，该药物具有显著的安全性优势。'
        kwargs=bound_scope(t)
        r=self.assert_case(t,1,0,'qualification_advantage',verified_parent_context=parent,**kwargs)
        deps=[e['context_dependency'] for e in r['evidence'] if e.get('subtype')=='qualification_advantage']
        self.assertTrue(all(d['innovation_object_scope']==kwargs['verified_innovation_scope_v27'] for d in deps))
        self.assert_case(t,0,0,**kwargs)
        self.assert_case(t,0,0,verified_parent_context=parent)
        ordinary=[{'paragraph_id':'ordinary','text':'创新药已纳入突破性治疗药物程序，企业可以终止材料上传。'}]
        self.assert_case(t,0,0,verified_parent_context=ordinary,**kwargs)
        for t in ['该药物已经纳入突破性治疗药物程序。','该药物应在十日内提交材料。','该药物用于严重危及生命的疾病。','该药物临床获益尚不能证实。','其他应当终止程序的情形。']:
            with self.subTest(t=t):self.assert_case(t,0,0,verified_parent_context=parent,**bound_scope(t))
        t='一般优先审评参照突破性治疗的明显临床优势要求。'
        self.assert_case(t,0,0,verified_parent_context=parent,**bound_scope(t))

    def test_verified_scope_rejects_unbound_or_invalid_metadata(self):
        t='该药物具有明显临床优势。'
        changes=[('text','changed'),('text_sha256','wrong'),('source_sha256','wrong'),('original_unit_sha256','wrong'),('component','优先审评程序'),('verified',False),('verified',1),('locator',{}),('locator',{'paragraph_id':'p','source_lines':[0]}),('locator',{'paragraph_id':'p','source_lines':[True]}),('component_binding',{'unit_id':'other','candidate_sha256':hashlib.sha256(b'synthetic candidate').hexdigest()}),('component_binding',{'unit_id':'synthetic-unit','candidate_sha256':'wrong'})]
        for field,value in changes:
            with self.subTest(field=field,value=value):
                kwargs=bound_scope(t);kwargs['verified_innovation_scope_v27'][field]=value
                with self.assertRaises(AssertionError):run(t,**kwargs)
        for field in ('text','text_sha256','source_sha256','original_unit_sha256','component','verified','locator','component_binding'):
            with self.subTest(missing=field):
                kwargs=bound_scope(t);del kwargs['verified_innovation_scope_v27'][field]
                with self.assertRaises(AssertionError):run(t,**kwargs)

    def test_pending_identity(self):
        r=record('支持创新药研发。');r['input_assessment'].update(status='context_insufficient',reason='constructed missing context')
        o=old.code_unit(r);expected=copy.deepcopy(o)
        self.assertIs(revise(r,o),o)
        self.assertEqual(o,expected)

    def test_only_permitted_fields_mutated(self):
        r=record('评价药品安全性及创新性，并保障药品供应。')
        o=old.code_unit(r);before=copy.deepcopy(o)
        revise(r,o)
        for k in set(o)|set(before):
            if k not in {'evidence','suppressions','review_flags'}:self.assertEqual(o.get(k),before.get(k),k)
        self.assertEqual([e for e in o['evidence'] if e['dimension'] not in {'I','F'}], [e for e in before['evidence'] if e['dimension'] not in {'I','F'}])

    def test_ids_and_filenames_do_not_decide(self):
        text='药品价格为五十元。'
        a=run(text,review_id='fictional',original_file_stem='创新药-公平性')
        b=run(text,review_id='another',original_file_stem='other')
        self.assertEqual(a['labels'],b['labels'])

    def test_unicode_offsets(self):
        self.assert_case('评 价 药 品 创 新 性；改 善 药 物 的 可 获 得 性。',1,1)

    def test_document_action_not_report_name(self):
        for t in ['将药品创新性评价报告按编号归档。','将药品公平性评价报告按编号归档。','药品创新性评价报告仅予公示。','药品公平性评价报告仅上传。','申报内容包括药品基本信息、创新性、公平性方面的信息，以及摘要幻灯片进行公示。']:
            with self.subTest(t=t):self.assert_case(t,0,0)
        self.assert_case('提交药品创新性评价报告。',1,0)
        self.assert_case('提交药品公平性评价报告。',0,1)
        self.assert_case('将药品创新性评价报告按编号归档并提交药品公平性评价资料。',0,1)
        self.assert_case('将药品公平性评价报告按编号归档并评价该药创新性。',1,0)

    def test_qualification_document_operations_not_comparative_content(self):
        parent=[{'paragraph_id':'p','text':'创新药或改良型新药申请适用突破性治疗药物程序，应满足以下条件：'}]
        for t in ['将明显临床优势评价报告按编号归档。','药品企业仅上传明显临床优势资料。']:
            with self.subTest(t=t):self.assert_case(t,0,0,verified_parent_context=parent)
        self.assert_case('提交该药物明显临床优势的评价报告。',1,0,verified_parent_context=parent)
        t='将明显临床优势评价报告按编号归档，同时该药物仍具有明显临床优势。'
        r=self.assert_case(t,1,0,verified_parent_context=parent)
        self.assertTrue(all(e['start']>=t.index('该药物') for e in r['evidence'] if e['dimension']=='I'))

    def test_innovation_possessor_not_institutional_actor(self):
        for t in ['药品企业应评价医院管理机制的创新性。','开展药品使用监测和临床综合评价是一项创新性、系统性工作。']:
            with self.subTest(t=t):self.assert_case(t,0,0)
        self.assert_case('药品企业应评价医院管理机制的创新性并评价该药物的创新性。',1,0)

    def test_list_and_condition_relations_survive_punctuation(self):
        for t in ['从有效性、安全性、创新性、公平性等方面，综合研判药品价值。','申报材料应突出申报药品在创新性、公平性方面的比较优势。']:
            with self.subTest(t=t):self.assert_case(t,1,1)
        for t in ['鼓励抗肿瘤新药研发。','支持以临床价值为导向的创新药研发。','开发适配创新药研发需求的数据产品，支持科研机构研发。','自创新药首次上市许可之日起，给予6年数据保护期。','申请应当为中药、化学药品、生物制品1类创新药临床试验。']:
            with self.subTest(t=t):self.assert_case(t,1,0)
        for t in ['包括但不限于：药品通用名称；未满足的治疗需求。','该药品费用的支付标准包括了医保基金和患者共同支付的全部费用。','若药品挂网价格高于支付标准，则超出部分需由患者自付。','可负担性可由人均年用药治疗费用占家庭年收入比重体现。','开发老年患者口服药物时，将吞咽困难作为评估内容。','使用该药物时，降低给药时点的复杂性。']:
            with self.subTest(t=t):self.assert_case(t,0,1)

    def test_directory_and_channel_identity_not_arrangement(self):
        for t in ['该药品通用名不被纳入《药品目录》。','药品经专家评审后，可以调出《药品目录》。','《药品目录》不再新增 OTC 药品。','对纳入“双通道”管理的药品，在定点医疗机构和药店施行统一的支付政策。','纳入“双通道”管理和施行单独支付的药品范围，由省级部门确定。']:
            with self.subTest(t=t):self.assert_case(t,0,1)
        for t in ['纳入基本目录后，通过续约控制药品降价幅度。','确保“双通道”谈判药品质量安全。','加强“双通道”用药费用和基金支出分析，确保基金安全。','谈判药品如需新增适应症，应申报目录内条件3。','根据《药品目录》安排会议。','申办者负责向研究者提供临床试验用药品；临床试验用药品的制备、供应和管理应符合要求。']:
            with self.subTest(t=t):self.assert_case(t,0,0)

    def test_registration_and_drug_value_information_boundaries(self):
        for t in ['按照药品注册分类标准批准的1类化学药品可以申请。',
                  '1类治疗用生物制品、1类中药（按照现行药品注册分类标准）可以申请。',
                  '化学药注册按照化学药创新药、改良型新药和仿制药进行分类。',
                  '上市药品目录集注明创新药、改良型新药等属性。',
                  '评价聚焦药品临床使用问题，围绕技术评价，从安全性、创新性等维度开展分析。']:
            with self.subTest(t=t): self.assert_case(t,1,0,'attribute')
        # v1.3 explicitly includes registration innovation classification;
        # the class-number requirement cannot be excluded as a bare name.
        self.assert_case('试点范围为1类创新药临床试验申请。',1,0,'attribute')
        for t in ['试点范围为创新药临床试验申请。',
                  '1类化学药品的项目文件按编号归档。',
                  '公布《化学药创新药注册分类说明》。',
                  '药品材料归档，软件从创新性维度开展分析。']:
            with self.subTest(t=t): self.assert_case(t,0,0)

    def test_data_protection_and_development_support_relations(self):
        for t in ['自改良型药品首次境内上市许可之日起，给予4年数据保护期。',
                  '原研药品提交新适应症试验数据，对全部试验数据给予6年数据保护期。',
                  '对创新药申请人提交的试验数据，给予一定的数据保护期。',
                  '在数据保护期内，其他申请人依赖持有人受保护的数据提交改良型新药上市申请，国家药监局不予许可。',
                  '药品的数据保护范围包括证明临床优势的新的临床试验数据。',
                  '申请人提交药品上市申请，若依赖其他申请人受保护数据则不予许可。',
                  '要求全链条强化政策保障，合力助推创新药突破发展。',
                  '重点创新药品种将依申请纳入30日通道。',
                  '支持中药传承和创新，建立评价体系，鼓励运用现代技术研制中药。',
                  '使用已知非处方药的活性成份组成的新的复方制剂。']:
            with self.subTest(t=t): self.assert_case(t,1,0)
        for t in ['缩短临床急需创新药临床试验沟通交流等待时限。',
                  '软件的数据保护范围包括新的日志数据。',
                  '药品试验数据保护制度文件按编号归档。',
                  '药品新品种和新剂型可申请。']:
            with self.subTest(t=t): self.assert_case(t,0,0)

    def test_access_and_management_relation_boundaries(self):
        for t in ['支持商保创新药患者可及。',
                  '竞价药品支付标准到期后，经评审同意，纳入常规目录乙类。',
                  '该药品通用名不被纳入《药品目录》。',
                  '药品医疗器械质量安全、有效、可及得到保障。',
                  '医保药品保障水平提升，有效缓解用药难。',
                  '药品费用，按照规定由基本医疗保险基金支付。',
                  '定点医疗机构根据《药品目录》调整结果及时对本医疗机构用药目录进行调整。',
                  '商保创新药目录内药品享受政策，不计入基本医保自费率指标。',
                  '装置应附在药品包装中，以避免难以获得装置。']:
            with self.subTest(t=t): self.assert_case(t,0,1,'access')
        for t in ['复杂给药方式通常需要培训以指导患者用药。',
                  '培训教育不能完全满足合理用药及正确操作的要求。',
                  '复杂给药方式下将照护者辅助方式作为患者自我给药的补充。']:
            with self.subTest(t=t): self.assert_case(t,0,1,'clinical_management')
        for t in ['药品目录文件按编号归档。',
                  '创新药审批速度得到提升。',
                  '软件可及性得到保障，药品文件已归档。',
                  '药品货运装置应附在包装中，避免难以获得发票。']:
            with self.subTest(t=t): self.assert_case(t,0,0)

    def test_supply_information_requires_bound_access_evaluation(self):
        t='根据评价需要可获得相关支持信息，如药品生产、供应相关信息。'
        self.assert_case(t,0,0)
        paragraph='可获得性可由医疗卫生机构药品配备使用情况或有无短缺反映。'+t
        r=self.assert_case(t,0,1,'access',paragraph_context=[{'paragraph_id':'access-p','text':paragraph}])
        ev=[e for e in r['evidence'] if e['rule']=='V27_F_drug_supply_evaluation_information']
        self.assertEqual(ev[0]['context_dependency']['kind'],'same_paragraph_access_evaluation')
        self.assert_case(t,0,0,paragraph_context=[{'paragraph_id':'other-p','text':'药品数据归档。'+t}])

if __name__=='__main__':unittest.main()

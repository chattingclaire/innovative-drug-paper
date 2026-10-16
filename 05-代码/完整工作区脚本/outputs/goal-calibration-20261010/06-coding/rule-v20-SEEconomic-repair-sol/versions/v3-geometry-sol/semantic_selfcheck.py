"""Fixed semantic counterexamples; synthetic source, never a human reference."""
import hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions

HERE=Path(__file__).resolve().parent


def context(text, kind='paragraph', cid='CTX-SYN', structure=None):
    return {'context_id':cid,'kind':kind,'text':text,'source_ref':{'sha256':'a'*64,'source_resource_id':'SOURCE-SYN','locator':{}},'structure':structure or {}}


def unit(text, contexts=None, documents=None):
    return {'text':text,'source_ref':{'sha256':'a'*64,'source_resource_id':'SOURCE-SYN','locator':{}},
        'contexts': contexts or [context(text)], 'source_bundle':{'source_record':{'text':text,'contexts':contexts or [context(text)]},
            'source_documents':documents or [],'explicit_or_primary_source_resources':[],'source_full_text_resources':[],
            'preserved_historical_neutral_source_supplements':[],'source_reference_index':[]},'derived_context_origins':{}}


CASES=[
 ('risk_comparison_negative','药品的上市后研究不能证明其获益大于风险，应不予批准。',{'S':1,'E':1,'Ec':0}),
 ('risk_information','应审阅并评估该药物已有的安全性信息。',{'S':1,'E':0,'Ec':0}),
 ('report_submission','申办者应当定期在药审网站提交药物研发期间安全性更新报告。',{'S':0,'E':0,'Ec':0}),
 ('report_authority','药物研发期间安全性更新报告的具体要求由主管机构制定公布。',{'S':0,'E':0,'Ec':0}),
 ('report_actual_content','建议基于上述数据撰写该药物申报资料的安全性内容。',{'S':1,'E':0,'Ec':0}),
 ('discipline_status','申请人应完成药理毒理学等研究并提交药物临床试验申请资料。',{'S':0,'E':0,'Ec':0}),
 ('general_quality','应评价该药物的稳定性及批次质量。',{'S':0,'E':0,'Ec':0}),
 ('quality_risk_link','应评价该药物杂质导致肝毒性的不良反应风险。',{'S':1,'E':0,'Ec':0}),
 ('administrative_safety','药品申报数据必须符合网络安全和信息安全要求。',{'S':0,'E':0,'Ec':0}),
 ('risk_control_exception','除非经评估不存在药物相互作用风险，否则应暂停用药。',{'S':1,'E':0,'Ec':0}),
 ('prescription_error','药品处方剂量、用法是否正确，单次处方总量是否符合规定，应当核对。',{'S':1,'E':0,'Ec':0}),
 ('pkpd_isolated','综合评估药物的药代动力学、药效学、剂型和给药途径等基本特征。',{'S':0,'E':0,'Ec':0}),
 ('no_standard_care','该药物首次人体研究选择已没有标准治疗可供选择的患者。',{'S':0,'E':0,'Ec':0}),
 ('no_effective_care','该药物适用于尚无有效治疗手段的患者，应提交疗效证据。',{'S':0,'E':1,'Ec':0}),
 ('uncertain_effect','应了解患者是否能从该药物治疗中获益及其对治疗不确定性的接受程度。',{'S':0,'E':1,'Ec':0}),
 ('effect_condition','如该药物尚未显示患者明显获益，不得以该观察研究直接推定治疗效果。',{'S':0,'E':1,'Ec':0}),
 ('effect_shortfall','申报资料显示申请药品有效性存在较大缺陷。',{'S':0,'E':1,'Ec':0}),
 ('trial_response','应分析药物临床研究中不同阶段患者对于治疗的反应。',{'S':0,'E':1,'Ec':0}),
 ('certificate_validity','应确认药品注册证书的有效性。',{'S':0,'E':0,'Ec':0}),
 ('enactment_purpose','为了提高药物有效性和用药安全，制定本指导原则。',{'S':0,'E':0,'Ec':0}),
 ('quotation','参加竞价的药品企业按要求报价并提交承诺书。',{'S':0,'E':0,'Ec':1}),
 ('price_threshold','经测算提出医保支付意愿，作为药品的准入门槛。',{'S':0,'E':0,'Ec':1}),
 ('negative_price_consequence','若药品企业报价高于支付意愿，该药不纳入目录。',{'S':0,'E':0,'Ec':1}),
 ('budget_qualitative','未来两年该药品的基金支出预算增幅应当合理。',{'S':0,'E':0,'Ec':1}),
 ('pay_content_check','申报时应核对该药品支付范围及医保费用信息。',{'S':0,'E':0,'Ec':1}),
 ('pay_field_only','药品支付范围字段不能为空。',{'S':0,'E':0,'Ec':0}),
 ('price_field_only','药品报价字段不能为空。',{'S':0,'E':0,'Ec':0}),
 ('mixed_form_content','药品价格字段不能为空，并应核验药品实际费用。',{'S':0,'E':0,'Ec':1}),
 ('application_identity','适应症变化且企业主动申报调整医保支付范围的常规目录药品。',{'S':0,'E':0,'Ec':0}),
 ('payment_authorization','经申请并审核同意后，药品方可调整支付范围。',{'S':0,'E':0,'Ec':1}),
 ('category_only','药品按甲类和乙类进行归类。',{'S':0,'E':0,'Ec':0}),
 ('existing_status','竞价药品支付标准有效期到期后，经评审同意纳入常规目录乙类。',{'S':0,'E':0,'Ec':0}),
 ('payment_title','（二）调整支付范围的药品。',{'S':0,'E':0,'Ec':0}),
 ('negotiation_stage','独家药品进入谈判环节。',{'S':0,'E':0,'Ec':0}),
 ('price_job','专家负责与药品企业进行现场价格协商。',{'S':0,'E':0,'Ec':1}),
 ('cost_responsibility','申办者应承担药物临床试验参与者损害的诊疗费用及赔偿。',{'S':0,'E':0,'Ec':1}),
]


def run():
    result=[]
    def check(name, u, expected):
        v=RelationView(u);d=judge(v);validate_decisions(u,d)
        actual={key:d[key]['value'] for key in expected}
        result.append({'name':name,'synthetic_input':u,'expected_fixed_before_execution':expected,'actual':actual,
                       'passed':actual==expected,'decisions':d,'relation_trace':v.traces()})
    for name,text,expected in CASES: check(name,unit(text),expected)
    check('same_cost_data_reference',unit('如协商不能达成一致，以医保方数据为准。',[
        context('企业和医保方对该药品基金实际支出存在分歧，允许补充数据并协商。如协商不能达成一致，以医保方数据为准。')]),{'Ec':1})
    check('unrelated_sibling_cost_not_inherited',unit('如协商不能达成一致，以医保方数据为准。',[
        context('如协商不能达成一致，以医保方数据为准。'),context('其他药品的基金支出应单独测算。','preceding_paragraph','CTX-OTHER')]),{'Ec':0})
    check('quality_ADR_response_same_paragraph',unit('药学部门立即进行药品追溯和质量评估，评估后确定是否继续使用或更换药品。',[
        context('发现该药品严重不良反应后，应立即暂停使用并救治。药学部门立即进行药品追溯和质量评估，评估后确定是否继续使用或更换药品。')]),{'S':1})
    # Complete finite article and deliberately missing member/terminator controls.
    current='符合《药物准入测试规定》第五条规定的药品可以申请。'
    ref=lambda t,cid,i:dict(context(t,'cited_article',cid,{'article':'第五条','sequence_index':i}),
        source_ref={'sha256':'b'*64,'source_resource_id':'SOURCE-REF','locator':{'article':'第五条'}})
    docs=[{'source_sha256':'b'*64,'byte_SHA_verified':True,
           'source_title_lines_verbatim_extraction_candidates':['药物准入测试规定','2024年3月1日']}]
    contexts=[context(current),ref('第五条 药品应当符合以下条件：','CTX-H',0),
        ref('（一）核验药品不良反应风险；','CTX-R',1),ref('（二）药品价格合理。','CTX-P',2)]
    check('complete_explicit_article_condition',unit(current,contexts,docs),{'S':1,'E':0,'Ec':1})
    check('missing_article_last_member',unit(current,contexts[:-1],docs),{'S':None,'E':None,'Ec':None})
    # Reference identity is an integrity constraint, not a topic-label feature.
    renamed=current.replace('药物准入测试规定','另一份准入规定')
    renamed_docs=[dict(docs[0],source_title_lines_verbatim_extraction_candidates=['另一份准入规定','2024年3月1日'])]
    check('different_title_same_substance',unit(renamed,[context(renamed)]+contexts[1:],renamed_docs),{'S':1,'E':0,'Ec':1})
    path=HERE/(sys.argv[1] if len(sys.argv)>1 else 'semantic-selfcheck.json')
    with path.open('x') as stream: json.dump({'status':'synthetic_development_only','is_human_reference':False,
        'test_N':len(result),'failed_N':sum(not x['passed'] for x in result),'tests':result},stream,ensure_ascii=False,indent=2)
    print(json.dumps({'test_N':len(result),'failed':[x['name'] for x in result if not x['passed']]},ensure_ascii=False))


if __name__=='__main__':run()

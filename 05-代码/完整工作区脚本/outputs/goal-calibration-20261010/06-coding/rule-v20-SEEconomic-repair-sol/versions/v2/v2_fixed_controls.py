"""Pre-fixed real examples and adjacent synthetic controls; non-human regression."""
import json,hashlib,sys
from pathlib import Path
sys.dont_write_bytecode=True
from source_packet import semantic_unit
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
from semantic_selfcheck import unit,context,CASES
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
ACTUAL=[
 ('risk_benefit_complete','A-000007',{'S':1,'E':1},'获益风险比较本身是内容，不要求另有评价动词'),
 ('latin_events_adjacent','A-000061',{'S':1},'AE/ADR发生率内容，中文邻接不消除缩写'),
 ('risk_control_actual','A-000060',{'S':1},'药物风险控制预防监测和治疗措施'),
 ('used_qualitative_standard','A-000307',{'S':1,'E':1,'Ec':1},'操作性第七八条完整已交付标准含安全有效价格合理及排除例外'),
 ('pay_parent_member','A-000138',{'Ec':1},'直接支付父谓词与成员条件组合，不借兄弟内容'),
 ('prescription_check_member','A-000352',{'S':1},'直接处方审核内容中检查剂量用法正确性'),
 ('safety_population_member','A-000170',{'S':1},'直接安全性数据整理内容的人群界定'),
 ('complete_removal_total','A-000280',{'S':1,'E':1,'Ec':1},'当前实质调出条件总领消费完整有界五项'),
 ('content_intro_only','A-000293',{'Ec':0},'当前仅引导协议内容，不借兄弟新支付后果'),
 ('complete_renewal_total','A-000450',{'Ec':1},'完整已交付续约条件组实际限定预算和费用'),
 ('actual_price_information','A-000207',{'Ec':1},'市场价格和销售金额实际信息范围'),
 ('actual_economic_data_anaphor','A-000016',{'Ec':1},'相关数据确指同段药品费用和基金支出核验'),
 ('actual_payment_mechanism_definition','A-000638',{'Ec':1},'当前双通道定义直接同步纳入医保支付'),
 ('settlement_price','A-000557',{'Ec':1},'当前协商合理确定药品结算价'),
 ('narrow_therapeutic_window','A-000690',{'S':1},'治疗窗窄与混合服用限制直接连接用药风险'),
 ('vaccine_harm','A-000373',{'S':1},'接种异常反应严重危害人体健康'),
 ('tolerability_enrolment','A-000314',{'S':1},'当前耐受性较差导致关键药物研究人群排除'),
 ('actual_fund_payment_monitor','A-000184',{'Ec':1},'实质监测医保基金支付情况'),
 ('fund_payment_condition','A-000213',{'Ec':1},'药品配备使用指标与基金支付挂钩'),
 ('efficacy_indicator_anaphor','A-000236',{'E':1},'当前相同指标差异是确指同段疗效观察指标'),
 ('enrichment_benefit','A-000372',{'E':1},'当前最可能获益的试验人群与同段药物对象相连'),
 ('PRO_health_content','A-000020',{'E':1},'当前PRO定义含症状和健康相关生活质量内容'),
 ('burden_defined_in_same_paragraph','A-000481',{'Ec':1},'当前负担由同段误工收入损失有限说明'),
]
SYNTHETIC=[
 ('disease_risk_only','药物研究应记录患者基础疾病的进展风险。',{'S':0},'疾病风险不等同药物损害风险'),
 ('production_risk_only','评价药品生产车间的消防安全风险。',{'S':0},'生产消防安全不等同药物患者风险'),
 ('data_risk_only','评价药品申报数据丢失的风险。',{'S':0},'数据风险不等同药物损害风险'),
 ('latin_uncertain_negative','应核验该药物的AE/ADR，即使未发现ADR也应记录发生率。',{'S':1},'不良事件/反应否定仍在场'),
 ('latin_admin_near_miss','药品申报系统的AE字段不能为空，ADR文件须按格式上传。',{'S':0},'缩写字段手续不形成实质内容'),
 ('drug_safe_effective_condition','符合安全有效且价格合理条件的药品方可纳入。',{'S':1,'E':1,'Ec':1},'明确实质药物条件'),
 ('safe_effective_identity','已被登记为安全有效产品的药品应按编号填写申报表。',{'S':0,'E':0,'Ec':0},'既有身份与填写手续不核验内容'),
 ('general_object_identity','药品申报时应选择支付范围调整类别。',{'Ec':0},'只申报归类，不授予支付变更'),
 ('research_cost_near_miss','应测算药品研发项目的研究经费和设备采购成本。',{'Ec':0},'一般研究资源不是药品治疗支付费用'),
 ('conditional_cost_content','如该药品价格未定，应说明预期结算价及预算，不能只留空字段。',{'Ec':1},'实质费用内容与字段形式并存'),
 ('wrong_sibling_only','当前药品应补交盖章材料；另一药品的支付标准另行调整。',{'Ec':1},'完整当前中另一药品自身确有经济内容，但不用于前项授权'),
 ('isolated_pkpd_near_miss','综合评估药物的PK-PD参数、剂型与给药途径。',{'E':0},'孤立PKPD不补效果内容'),
 ('standard_care_near_miss','该药物研究纳入没有标准治疗可供选择的末线患者。',{'E':0},'无标准治疗不能补无有效治疗'),
 ('pure_total_structure','药品经济性材料内容如下：',{'Ec':0},'纯组织性引导没有内容谓词'),
]


def run():
    results=[];bindings=[]
    for name,blind,expected,basis in ACTUAL:
        path=ROOT/'outputs/ai-audit800-20261010/source-A/coder-A/materials'/f'{blind}.json';raw=path.read_bytes()
        bundle=json.loads(raw);u=semantic_unit(bundle);v=RelationView(u);d=judge(v);validate_decisions(u,d)
        results.append({'name':name,'input_kind':'actual_frozen_material','input_binding':{'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()},
            'expected_fixed_before_v2_edit':expected,'manual_rationale':basis,'actual':{dim:d[dim]['value'] for dim in expected},
            'passed':all(d[dim]['value']==val for dim,val in expected.items()),'decisions':d,'relations':v.traces(),
            'source_current':bundle['source_record']['text'],'not_human_or_formal_gold':True})
    for name,text,expected,basis in SYNTHETIC:
        u=unit(text);v=RelationView(u);d=judge(v);validate_decisions(u,d)
        results.append({'name':name,'input_kind':'synthetic_near_miss_or_scope_control','source_current':text,
            'expected_fixed_before_v2_edit':expected,'manual_rationale':basis,'actual':{dim:d[dim]['value'] for dim in expected},
            'passed':all(d[dim]['value']==val for dim,val in expected.items()),'decisions':d,'relations':v.traces(),'not_human_or_formal_gold':True})
    # A sibling can never supply the price/risks of the tested current record.
    for name,text,other,expected in [
      ('pay_sibling_not_borrowed','该药品申报时应补交签章材料。','另一药品价格合理且可扩大支付范围。',{'Ec':0}),
      ('risk_sibling_not_borrowed','该药物应补交试验计划。','另一药物发生严重不良反应。',{'S':0}),
      ('effect_sibling_not_borrowed','该药物应报告研究进度。','另一药物已显示患者明显临床获益。',{'E':0}),
    ]:
        u=unit(text,[context(text),context(other,'preceding_paragraph','CTX-OTHER')]);v=RelationView(u);d=judge(v);validate_decisions(u,d)
        results.append({'name':name,'input_kind':'synthetic_sibling_boundary','source_current':text,'unrelated_context':other,
            'expected_fixed_before_v2_edit':expected,'actual':{dim:d[dim]['value'] for dim in expected},
            'passed':all(d[dim]['value']==val for dim,val in expected.items()),'decisions':d,'not_human_or_formal_gold':True})
    result={'status':'disclosed_non_human_fixed_controls','test_N':len(results),'failed_N':sum(not x['passed'] for x in results),'tests':results,
        'no_800_or_77_full_replay':True,'formal_acceptance_score':False}
    with (HERE/sys.argv[1]).open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'test_N':len(results),'failed':[x['name'] for x in results if not x['passed']]},ensure_ascii=False))


if __name__=='__main__':run()

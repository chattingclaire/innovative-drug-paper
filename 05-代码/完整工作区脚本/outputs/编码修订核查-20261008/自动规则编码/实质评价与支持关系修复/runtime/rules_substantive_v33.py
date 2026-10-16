"""Exposed-development repairs under unchanged CAL-5D v1.3 / operation v1.4.

Patterns express a current object–predicate relation. Neither reference rows,
IDs, source filename meaning, departments nor target metrics enter inference.
"""
import re
from rule_support import RuleView
from rules_if import BASIS_I, BASIS_F, _norm
from rules_se import S_BASIS, E_BASIS, _non_drug_proposition, _verified_scope
from rules_ec import EC_BASIS

VERSION = 'v33-substantive-relations-20261007-candidate01'
BASES = {'I': BASIS_I, 'F': BASIS_F, 'S': S_BASIS, 'E': E_BASIS, 'Ec': EC_BASIS}
DRUG = r'(?:药品|药物|用药|新药|制剂|给药|药费|该药|本药)'


def add(v, rule, dimension, match, subtype=None, dependency=None):
    return v.add(rule, dimension, *match.span(), subtype, BASES[dimension],
                 dependency=dependency, safety_basis='other_safety' if dimension == 'S' else None)


def scan(v, rule, dimension, pattern, subtype=None, drug=True, dependency=None):
    for m in re.finditer(pattern, v.text):
        local_drug = re.search(DRUG + r'|定点零售药店|(?:抗肿瘤|抗癌|抗感染|抗病毒|降压|降糖|抗菌|镇痛|麻醉)药', v.text)
        if drug and not (v.drug_scope or local_drug):
            continue
        if dimension in {'S', 'E'} and _non_drug_proposition(m.group()):
            continue
        dep = dependency
        if drug and not local_drug and dep is None:
            parent = next((p for p in v.record.get('verified_parent_context', [])
                           if re.search(DRUG,p.get('text',''))), None)
            if parent:
                dep = v.dependency(parent,'verified_parent_drug_object_only',parent['text'])
                if parent.get('source_context_certificate_field'):
                    dep['source_context_certificate_field'] = parent['source_context_certificate_field']
                    dep['candidate_sha256'] = parent.get('candidate_sha256')
                    dep['original_unit_sha256'] = parent.get('original_unit_sha256')
            else:
                p = next((p for p in v.record.get('paragraph_context', [])
                          if re.search(DRUG,p.get('text','')) and _norm(p['text']).count(v.normalized)==1),None)
                if p:
                    dep = v.dependency(p,'same_paragraph_drug_object_only',p['text'])
        add(v, rule, dimension, m, subtype, dep)


def same_paragraph(v):
    """The exact source-supplied paragraph, not an arbitrary neighbouring row."""
    for p in v.record.get('paragraph_context', []):
        full = _norm(p['text'])
        if full.count(v.normalized) == 1:
            yield p, full


def fairness(v):
    # Treatment need is broader than insurance affordability, but general
    # better efficacy or a wish to meet needs does not establish a gap.
    scan(v, 'V33_F_explicit_unmet_treatment', 'F',
         r'(?:填补|弥补|解决)[^。；;，,]{0,10}临床治疗空白|'
         r'(?:解决|存在|针对|填补)[^。；;，,]{0,12}(?:临床|治疗|用药)[^。；;，,]{0,6}未满足(?:的)?需求|'
         r'(?:患者|人群)[^。；;，,]{0,12}(?:无法|不能|未能)接受(?:到)?(?:充分[、，,及和]*)?(?:有效)?的?治疗|'
         r'(?:境内|国内|当地)[^。；;，,]{0,4}尚无药物获批[^。；;，,]{0,20}(?:疾病|适应症)', 'access')
    scan(v, 'V33_F_unavailable_form_for_population', 'F',
         r'现有上市规格均不适用于[^。；;，,]{1,15}(?:人群|患者)[,，]新规格适于[^。；;，,]{1,15}(?:人群|患者)使用', 'access')
    scan(v, 'V33_F_actual_patient_treatment_access', 'F',
         r'(?:患者|人群)[^。；;，,]{0,12}(?:更快|及时|尽早|及早|持续)(?:地)?(?:获得|获取|接受)(?:治疗)?(?:药品|药物)|'
         r'(?:无效|低效)[^。；;]{0,80}(?:从而|因此)[^。；;]{0,8}(?:有机会|能够|可)接受[^。；;]{0,25}治疗', 'access')
    scan(v, 'V33_F_supply_continuity', 'F',
         r'(?:须|应当|应|必须)(?:保障|保证|确保)(?:药品|药物)?市场供应[^。；;]{0,25}(?:不得|不能)断供|'
         r'(?:保障|保证|确保)(?:药品|药物|用药)(?:的)?(?:持续|连续|稳定)供应|'
         r'(?:药品|药物)[^。；;]{0,25}(?:不得|不能)(?:无故)?断供', 'access')
    scan(v, 'V33_F_supply_information_requirement', 'F',
         r'(?:跟踪|监测|评价|评估|报告|收集|分析)[^。；;]{0,30}药品[^。；;]{0,10}(?:实际供应|配备(?:与|和|及)?使用|供应与使用)(?:情况)?|'
         r'(?:报告|报送)[^。；;]{0,30}基层用药品种(?:优化)?调整情况|'
         r'基层用药品种(?:优化)?调整情况[^。；;]{0,25}报告', 'access')
    scan(v, 'V33_F_actual_formulary_configuration', 'F',
         r'(?:药品采购目录|(?:本机构|医疗机构|医联体)?用药目录|国家基本药物目录)[^。；;]{0,45}(?:制定|实行动态调整|动态调整)|'
         r'(?:制定|动态调整|优化|统筹确定)[^。；;]{0,20}(?:药品采购目录|用药目录|国家基本药物目录)|'
         r'履行药品配备[、和及与][^。；;]{0,25}职责(?:的)?监督检查', 'access')
    scan(v, 'V33_F_complementary_drug_coverage', 'F',
         r'(?:制定|增设|建立)(?:商业健康保险|商保)创新药(?:品)?目录[^。；;]{0,60}(?:满足[^。；;]{0,15}用药需求|超出基本医保保障范围)|'
         r'(?:增设|建立)[^。；;]{0,30}(?:商保|商业健康保险)[^。；;]{0,90}超出基本医保保障范围', 'access')
    scan(v, 'V33_F_actual_patient_cost_responsibility', 'F',
         r'(?:高出|超出)(?:的)?部分由(?:患者|参保人|参保人员)(?:自行)?(?:承担|自付)|'
         r'(?:患者|参保人|参保人员)(?:自行)?承担[^。；;，,]{0,15}(?:药费|药品费用|超额部分)', 'affordability')
    scan(v, 'V33_F_current_drug_payment_condition', 'F',
         r'(?:药品|药物)(?:发生的)?费用[^。；;]{0,20}符合(?:以下|下列)条件[^。；;]{0,20}(?:可|可以|应)由(?:基本医疗保险|医保)基金支付|'
         r'(?:根据|依据)[^。；;，,]{0,15}(?:谈判|评审)结果确定(?:是否)?调整(?:医保)?支付范围|'
         r'(?:同意|决定|批准|予以)(?:扩大|缩小|调整)(?:新的)?(?:医保)?支付范围|'
         r'以补充协议[^。；;]{0,30}确定新的[^。；;]{0,15}支付范围', 'access')
    parents = v.record.get('verified_parent_context', [])
    renewal = next((p for p in parents if re.search(r'谈判药品[^。]*续约规则|谈判药品[^。]*协议到期', _norm(p['text']))), None)
    if renewal or re.search(r'(?:目录内|谈判|医保)药品', v.text):
        scan(v, 'V33_F_current_coverage_renewal_term', 'F',
             r'(?:满足|符合)[^。；;]{0,30}条件的药品[^。；;]{0,15}(?:可|可以)(?:简易)?续约[,，]续约有效期[^。；;，,]{1,8}',
             'access', dependency=v.dependency(renewal, 'verified_current_coverage_renewal_object', renewal['text']) if renewal else None)
    scan(v, 'V33_F_actual_drug_use_scope_restriction', 'F',
         r'(?:对|对于)[^。；;]{0,20}药品[^。；;]{0,45}限定其在[^。；;]{0,20}(?:期限|范围)[^。；;]{0,12}使用', 'access')
    scan(v, 'V33_F_routine_drug_channel', 'F',
         r'定点零售药店(?:纳入|退出)[“”"\s]*双通道[“”"\s]*管理|'
         r'(?:纳入|退出)[“”"\s]*双通道[“”"\s]*(?:管理|药店配备范围)|'
         r'(?:医疗机构制剂|药品)[^。；;]{0,30}(?:促进|实现)[^。；;]{0,20}(?:医联体|医疗联合体)[^。；;]{0,12}共享使用|'
         r'药品向基层下沉[^。；;]{0,20}满足转诊用药需求|'
         r'(?:提供|开展)[^。；;]{0,20}(?:延伸处方|长期处方)[^。；;]{0,30}上下用药联动|'
         r'(?:药品供货周期|用药需求)[^。；;]{0,60}基层用药需求计划[^。；;]{0,8}(?:汇总审核|调整)|'
         r'药品配送问题[^。；;]{0,65}(?:集中|定期)?配送所需药品|'
         r'(?:强化|加强|完善|保障)(?:基层)?药品支付保障|'
         r'缺药登记[^。；;]{0,70}(?:配送至|用药衔接范围)', 'access')
    scan(v, 'V33_F_specific_drug_monitoring_obstacle', 'F',
         r'对药物反应的理解[^。；;]{0,45}(?:偏差|不主动报告)[^。；;]{0,60}(?:难以|遗漏|无法)[^。；;]{0,12}(?:信息|检查)|'
         r'(?:无法|难以)准确[^。；;]{0,20}描述[^。；;]{0,40}药物反应[^。；;]{0,30}偏差', 'clinical_management')

    # A listing used as a price premise or reported expenditure object does
    # not itself enact coverage; suppress only the inherited membership span.
    if re.search(r'药品通过竞价纳入[^。；;，,]{0,15}目录(?:的)?[,，](?:取|以|按照)', v.text) and re.search(r'支付标准', v.text):
        v.drop(lambda e: e['dimension']=='F' and 'membership' in e['rule'],
               'V33_F_existing_listing_price_premise', '既有竞价纳入是当前定价命题的前提，不另视为实际保障变化。')
    if re.search(r'(?:反馈|统计|报送)[^。；;]{0,40}药品纳入医保支付范围的药品费用', v.text):
        v.drop(lambda e: e['dimension']=='F' and 'membership' in e['rule'],
               'V33_F_covered_expenditure_reporting', '当前报告既有范围内药费/基金支出，不是重新确定保障范围。')
    if re.search(r'支付标准是[^。；;]{0,100}药品费用的基准', v.text):
        v.drop(lambda e:e['dimension']=='F' and e['rule']=='V27_F_coverage_condition',
               'V33_F_payment_benchmark_definition', '支付基准定义未独立规定保障范围、支付条件或患者承担。')
    assessment = any(re.search(r'纳入[^。；;]{0,15}(?:药品)?目录评审范围', _norm(p['text'])) for p in parents)
    if assessment and not re.search(r'(?:应当|应|将|予以)(?:调出|移出)[^。；;]{0,10}目录', v.text):
        v.drop(lambda e:e['dimension']=='F' and e['rule']=='V32_F_bound_actual_directory_exit_condition',
               'V33_F_assessment_scope_not_actual_exit', '上层明确仅纳入目录评审范围，子标题调出分类不等于已确定实际退出。')


def innovation(v):
    # An unexpanded registration number is not evidence of innovation identity.
    v.drop(lambda e:e['dimension']=='I' and e['rule']=='V27_I_standard_based_class_one',
           'V33_I_registration_number_needs_definition', '仅有注册序号及引用分类标准，没有当前材料中实际创新含义，不凭序号外推。')
    for m in re.finditer(r'(?:鼓励|支持)(?:新药|创新药|药物)(?:的)?研发(?:人员|研究人员|者)', v.text):
        a,b=v.raw_span(*m.span())
        v.drop(lambda e:e['dimension']=='I' and 'research_support' in e['rule'] and e['start']<b and a<e['end'],
               'V33_I_research_personnel_not_support_instrument', '当前鼓励的是研发人员沟通行为，不能截断人员名词当作创新研发支持措施。')
    if re.search(r'(?:计划开展|拟开展|启动|开展)[^。；;]{0,35}(?:研发鼓励试点|试点计划)', v.text) and not re.search(r'(?:给予|配置|提供|投入|资助|优先安排)[^。；;]{0,35}(?:资源|经费|资金|技术指导|研发便利|保护期)', v.text):
        v.drop(lambda e:e['dimension']=='I' and e['rule']=='V27_I_research_program',
               'V33_I_announced_program_without_instrument', '仅宣布研发鼓励试点名称与目的，不推定未陈述的资源、资格或实质支持内容。')
    scan(v, 'V33_I_explicit_mechanism_innovation', 'I', r'药物作用机制创新|(?:药品|药物)(?:的)?(?:原创|创新|改良)(?:属性|特点|机制)', 'attribute')
    scan(v, 'V33_I_concrete_product_modification', 'I',
         r'(?:改进|改良|改善)(?:药品|药物|制剂)(?:的)?(?:剂型|规格|包装|特征)|'
         r'(?:优化|改良|改进)装置结构设计|开发不同推注速度[、和及与]剂量规格的产品', 'attribute')
    scan(v, 'V33_I_explicit_innovation_registration_identity', 'I',
         r'(?:[1一]\s*类创新药|(?:注册分类|注册类别)[^。；;，,]{0,8}(?:创新药|改良型新药))', 'attribute')
    # An explicit innovation/modified object plus a real governing predicate
    # granting dedicated review support establishes support eligibility. It
    # does not evaluate an attribute or establish comparative qualification.
    eligibility = next((p for p in v.record.get('verified_parent_context', [])
                        if re.search(r'(?:以下|下列)[^。]*药品[^。]*(?:申请适用|可申请)[^。]*优先审评', _norm(p['text']))), None)
    if (eligibility and re.match(r'\s*[（(][一二三四五六七八九十0-9]+[）)]', v.text)
            and not re.search(r'申请人|提交|填报|报送|上传|系统|材料|文件|工作流程|办理', v.text)):
        scan(v, 'V33_I_current_innovation_support_eligibility', 'I',
             r'创新药(?:物)?|改良型新药', 'research_support',
             dependency=v.dependency(eligibility,'verified_current_innovation_object_and_review_support_eligibility',eligibility['text']))
    scan(v, 'V33_I_current_targeted_acceleration_instrument', 'I',
         r'创新药[^。；;]{0,25}(?:\d+|[一二三四五六七八九十]+)日通道支持[^。；;]{0,15}研发品种[,，]鼓励[^。；;]{0,20}同步研发', 'research_support')
    scope = v.record.get('verified_adapted_source_scope_v33')
    if scope:
        contexts = scope['contexts']
        text = '。'.join(_norm(p['text']) for p in contexts)
        # The object AND an actual dedicated support instrument are required.
        if (re.search(r'适用范围[:：][^。]*创新药',text)
                and re.search(r'沟通交流时限为[^。]*审评时限[^。]*单独序列管理',text)):
            anchor = next(p for p in contexts if re.search(r'适用范围[:：]',p['text']))
            dep = v.dependency(anchor,'verified_innovation_support_scope_and_current_eligibility',anchor['text'])
            dep['authenticated_scope_certificate'] = scope['certificate']
            # Only a current actual access qualification is restored. Routine
            # submissions, channels, and isolated handling dates stay outside.
            scan(v,'V33_I_current_substantive_support_eligibility','I',
                 r'适用条件及研发阶段[^。；;]{0,110}按照本工作规范开展[^。；;]{0,20}(?:沟通交流|审评审批)|'
                 r'对于拟申请附条件批准的创新药[^。；;]{0,35}(?:适用|不适用)本工作规范|'
                 r'本工作规范中的[^。；;]{0,30}创新药是指[^。；;]{0,50}[1一]\s*类创新药',
                 'research_support',dependency=dep)


def safety_effectiveness(v):
    scan(v,'V33_S_dose_safety_condition','S',r'在安全可控的前提下[^。；;]{0,35}(?:剂量|滴定)|药理毒理(?:及|和|与)[^。；;，,]{0,12}研发情况')
    scan(v,'V33_S_medication_error_accuracy','S',r'三查七对[^。；;]{0,40}给药[^。；;]{0,35}准确无误')
    scan(v,'V33_E_inadequate_effective_treatment','E',r'(?:患者|人群)[^。；;，,]{0,12}(?:无法|不能|未能)接受(?:到)?充分[、，,及和]*有效的?治疗')
    if _verified_scope(v) and not _non_drug_proposition(v.text):
        scan(v,'V33_E_effect_evaluation_content','E',r'(?:更全面的|全面的|药物|药品)(?:治疗)?效果评价',drug=False)
    for p, full in same_paragraph(v):
        if (re.search(r'药品临床使用监测和超常预警制度',v.text)
                and re.search(r'(?:无指征|超剂量)使用',full)):
            scan(v,'V33_S_bound_abnormal_drug_use_monitoring','S',r'药品临床使用监测和超常预警制度',
                 dependency=v.dependency(p,'same_paragraph_explicit_dosing_risk_monitoring',full))
        if (re.match(r'因此[,，]以上(?:两|几|多)种情况',v.text)
                and re.search(r'研究药物有效性和安全性',full)
                and re.search(r'外部对照',v.text)):
            dep=v.dependency(p,'same_paragraph_explicit_drug_SE_validation_external_control',full)
            scan(v,'V33_S_bound_drug_validation_external_control','S',r'以[^。；;]{0,35}数据作为外部对照的基础',dependency=dep)
            scan(v,'V33_E_bound_drug_validation_external_control','E',r'以[^。；;]{0,35}数据作为外部对照的基础',dependency=dep)
    if re.search(r'临床试验项目风险管理计划',v.text) and not re.search(r'不良反应|毒性|毒理|用药风险|药物风险|风险获益|获益风险|用药错误',v.text):
        v.drop(lambda e:e['dimension']=='S' and e['rule'] in {'S02','V27_S_harm_control_relation','V27_S_harm_control_context'}
               and re.fullmatch(r'风险管理(?:计划)?',e['text']),
               'V33_S_generic_project_risk_not_drug_harm','临床试验项目风险管理未明确药物损害或风险内容，不凭项目风险一词推安全性。')
    if re.search(r'药品安全信用档案|药品安全信用管理',v.text) and not re.search(r'不良反应|毒性|毒理|用药风险|质量风险',v.text):
        v.drop(lambda e:e['dimension']=='S' and e['rule'] in {'S01','S02'},
               'V33_S_institution_credit_not_drug_harm','机构信用档案和名称中的安全性评价不等于当前实质讨论药物损害。')


def economics(v):
    scan(v,'V33_Ec_drug_fund_constraint','Ec',r'以医保基金安全为底线[^。；;]{0,35}(?:进入目录的药品|药品准入)')
    scan(v,'V33_Ec_drug_pricing_regime_scope','Ec',r'药品通用名[^。；;]{0,25}(?:国家集中带量采购|政府定价)范围')
    scan(v,'V33_Ec_actual_drug_payment_regulation','Ec',r'(?:创新药|药品|药物)支付[^。；;]{0,15}基金监管|'
         r'履行药品配备[、和及与][^。；;]{0,10}支付[、和及与][^。；;]{0,20}职责|'
         r'(?:强化|加强|完善)(?:基层)?药品支付保障')
    if re.search(r'(?:通过|在)目录调整模块确认协议信息',v.text) and not re.search(r'(?:调整|确定|下调|提高)(?:新的)?(?:医保)?支付标准',v.text):
        v.drop(lambda e:e['dimension']=='Ec' and e['rule']=='V27_Ec_payment_standard',
               'V33_Ec_agreement_information_confirmation_only','当前仅通过模块确认既有协议信息/签订手续，列举支付标准不构成新的经济评价内容。')


def revise(record, result):
    if result.get('judgement_status') == 'undetermined':
        return result
    v=RuleView(record,result)
    fairness(v)
    innovation(v)
    safety_effectiveness(v)
    economics(v)
    return result

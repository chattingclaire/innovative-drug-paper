"""Exposed-development object/predicate repairs under the frozen manuals.

Only literal current propositions and validated contextual relations are read.
No case identifiers, departments, filenames, reference vectors or metrics are
classifier features. Context never donates a dimension vector.
"""
import re
from rule_support import RuleView, baseline
from rules_se import S_BASIS, E_BASIS
from rules_ec import EC_BASIS
from rules_if import BASIS_I, BASIS_F, _carrier_only, _disclosure_only

RELEASE = 'v36.1-bounded-semantic-relations-development'
BASES = {'S': S_BASIS, 'E': E_BASIS, 'Ec': EC_BASIS, 'I': BASIS_I, 'F': BASIS_F}
DRUG = r'(?:药品|药物|新药|用药|给药|制剂|该药|本药|某药|对照药|阳性药)'


def emit(v, dim, name, pattern, subtype=None, dependency=None):
    for m in re.finditer(pattern, v.text):
        clause = next((x.group() for x in v.clauses() if x.start() <= m.start() < x.end()), m.group())
        if _carrier_only(clause) or _disclosure_only(clause):
            continue
        e = v.add('V36_' + dim + '_' + name, dim, *m.span(), subtype,
                  BASES[dim], dependency=dependency,
                  safety_basis='other_safety' if dim == 'S' else None)
        e['rule_release'] = RELEASE


def _boundaries(v):
    # Urgency alone establishes neither unavailable therapy nor supply failure.
    # Drop only that legacy evidence; independent shortage/need evidence survives.
    v.drop(lambda e: e['dimension'] == 'F' and e['rule'] == 'V27_F_unmet_treatment'
           and re.fullmatch(r'(?:治疗|用药)需求(?:迫切|急迫)|满足[^。；;，,]*(?:急迫|迫切)[^。；;，,]*(?:用药|治疗)需求', e.get('matching_text', e['text'])),
           'V36_F_urgency_without_gap', '需求急迫本身不证明未获满足、无可用治疗或药物供应缺口。')
    for s in v.sentences():
        x = s.group()
        if (re.search(r'(?:危及生命|影响生存质量|严重疾病|病情严重)[^。；;]{0,25}是指', x)
                and re.search(r'(?:如果|若)得不到有效治疗', x)
                and not re.search(DRUG, x)):
            v.drop_within('E', *s.span(), 'V36_E_disease_definition_counterfactual',
                          '疾病严重程度定义中的不治疗反事实并未判断药物治疗效果。')
        # Rights classify protected data; a separate content demand is retained.
        for m in re.finditer(r'药品(?:的)?数据保护范围(?:包括|限于|不包括)[^。；;]{0,160}(?:全部)?试验数据', x):
            if not re.search(r'(?:应当|应|须|需|要求)(?:提交|补充|评价|收集)|另行|同时(?:提交|评价|补充)', m.group()):
                for d in ('S', 'E'):
                    v.drop_within(d, s.start()+m.start(), s.start()+m.end(),
                                  'V36_SE_rights_object_not_evaluation',
                                  '当前为数据专有权范围，安全/有效仅标识被保护数据；独立评价或资料要求另保留。')
        # Existing/newly included medicine is the subject of a pricing rule.
        # Work on unmasked text only to identify the actual directory name.
        raw = v.normalized[s.start():s.end()]
        for m in re.finditer(r'(?:新|已)?纳入《(?:国家)?药品目录》的药品(?:应|需|须|应当|同步|同时|原则上)*确定(?:医保)?支付标准', raw):
            v.drop_within('F', s.start()+m.start(), s.start()+m.end(),
                          'V36_F_pricing_subject_not_admission',
                          '纳入身份作支付定价主语，当前谓词只确定支付标准，未决定实际纳入。')
        for m in re.finditer(r'无论是否申请调整(?:医保)?支付标准(?:和|及|、)支付范围', x):
            v.drop_within('Ec', s.start()+m.start(), s.start()+m.end(),
                          'V36_Ec_filing_premise_not_payment_rule',
                          '无论是否申请调整仅列申报前提，不规定价格水平、费用责任或经济评价。')


def _direct(v):
    emit(v, 'E', 'patient_benefit_from_drug',
         r'(?:患者|受试者|人群)[^。；;，,]{0,25}从(?:该|本|研究|试验)?药物中(?:获得|取得)?获益')
    emit(v, 'E', 'effective_treatment_for_drug_recipients',
         r'药物上市后[,，]?[^。；;]{0,50}(?:患者|人群)[^。；;]{0,25}接受[^。；;]{0,15}(?:合理)?有效的?治疗')
    emit(v, 'E', 'active_comparator_therapeutic_choice',
         r'(?:阳性对照药|对照药品|对照药物)[^。；;，,]{0,45}(?:代表|反映)[^。；;，,]{0,25}(?:最佳|最优)治疗选择')

    emit(v, 'I', 'specific_dosing_frequency_modification',
         r'给药频次(?:进行|予以|实施|作出|的)?(?:改良|改进)|(?:改良|改进)(?:了)?(?:药物的?)?给药频次', 'attribute')
    emit(v, 'I', 'postposed_drug_innovation_degree',
         r'创新程度(?:较高|较低|高|低)(?:(?!企业|系统|平台|机制|生产方法|管理)[^。；;]){0,75}的(?:药品|药物)', 'attribute')
    emit(v, 'I', 'resources_for_innovative_development',
         r'(?:优化|增加|加强|优先配置|配置)[^。；;，,]{0,20}(?:审评审批|研发|研究|沟通)(?:资源配置|资源)[,，]'
         r'[^。；;，,]{0,18}(?:提升|支持|促进|推动|保障)创新药(?:物)?(?:临床)?研发[^。；;，,]{0,15}', 'research_support')

    emit(v, 'F', 'current_drug_market_shortage',
         r'(?:市场|临床)?短缺[^。；;，,]{0,25}(?:儿童|罕见病)?用药品|'
         r'临床急需[^。；;，,]{0,15}境外已上市(?:、|而)?境内未上市[^。；;，,]{0,15}药品', 'access')
    if re.search(DRUG, v.text):
        emit(v, 'F', 'no_standard_treatment',
             r'适应症[^。；;，,]{0,15}(?:确无|尚无|没有)标准治疗', 'access')
        emit(v, 'F', 'loss_of_treatment_opportunity',
             r'(?:药物|该药|本药)(?:的)?不良反应[^。；;]{0,80}(?:使|导致)患者(?:失去|丧失)治疗机会', 'access')
    emit(v, 'F', 'actual_commercial_formulary_membership',
         r'(?:协商|谈判|竞价)成功的药品(?:应|可)?纳入商保创新药目录|'
         r'(?:药品|品种)[,，]?(?:不会|不得|不予|不被)[^。；;]{0,45}纳入商保创新药目录', 'access')
    emit(v, 'F', 'drug_renewal_necessary_condition',
         r'(?:不申报|未申报|未提出申请)的?(?:谈判)?药品(?:无法|不能|不得|不予)续约', 'access')
    emit(v, 'F', 'negotiated_drug_agreement_duration',
         r'谈判药品协议有效期(?:原则上)?为[一二两三四五六七八九十0-9]+年', 'access')
    emit(v, 'Ec', 'explicit_drug_insurance_payment',
         r'(?:谈判)?药品[^。；;]{0,55}(?:同步|一并)纳入医保支付(?:的)?机制|'
         r'(?:谈判)?药品纳入异地就医直接结算范围')


def _contexts(v):
    # Only a current list criterion completes an explicit actual exit predicate.
    if re.match(r'^\s*(?:[（(][一二三四五六七八九十0-9]+[）)]|[一二三四五六七八九十0-9]+[、.．])', v.text):
        for p in v.record.get('verified_parent_context', []):
            pt = baseline.matching_view(p['text'])[0]
            if (re.search(r'药品[^。；;]{0,25}有(?:以下|下列)(?:情况|情形|条件)之一', pt)
                    and re.search(r'(?:直接|可以|应当|予以)调出《?(?:医保|药品|基本)目录》?[:：]?$', pt)
                    and re.search(r'的药品[;；。]?$', v.text)):
                emit(v, 'F', 'current_exit_criterion', r'[^。；;]+的药品', 'access',
                     v.dependency(p, 'verified_parent_actual_drug_exit_predicate', p['text']))
                break
    # A source-verified target-indication dossier plus its real content request.
    parents = v.record.get('verified_parent_context', [])
    indication = next((p for p in parents if re.search(r'目标适应症.*诊疗', p['text'])), None)
    request = next((p for p in parents if re.search(r'(?:请|应|需).*(?:总结|说明|提供)(?:以下|下列)内容', p['text'])), None)
    if indication and request:
        dep = v.dependency(request, 'verified_target_indication_content_request', request['text'])
        dep['object_context'] = v.dependency(indication, 'target_indication', indication['text'])
        emit(v, 'F', 'target_indication_unmet_need_information',
             r'未(?:被)?满足的临床需求', 'access', dep)
    for p, prefix in v.paragraph_prefixes():
        predecessors = [x.group().strip() for x in re.finditer(r'[^。]+', prefix) if x.group().strip()]
        if not predecessors:
            continue
        last = predecessors[-1]
        if re.search(r'(?:建立|实施|实行)[^。；;]{0,15}药品保障机制', last):
            emit(v, 'F', 'same_paragraph_drug_guarantee_level',
                 r'确定(?:适宜|合理|相应)的保障水平', 'access',
                 v.dependency(p, 'nearest_predecessor_drug_guarantee_mechanism', last))
        # One intervening procedural sentence about the SAME study may occur.
        # A generic research theme or mere quality/representativeness is not enough.
        candidates = [last]
        if (len(predecessors) > 1 and re.match(r'该研究', last)
                and re.search(r'研究方案|研究的良好实践', last)):
            candidates.append(predecessors[-2])
        for ante in candidates:
            if (re.search(DRUG + r'[^。]{0,70}评价[^。]{0,65}(?:减少[^。]{0,20}(?:骨折|复发|死亡)|治疗效果|疗效|临床获益|有效性)', ante)
                    and not re.search(r'另(?:一|项)研究|另一药|其他药', ante)):
                emit(v, 'E', 'same_study_endpoint_validation',
                     r'该研究的主要终点[^。；;，,]{0,35}(?:验证|核实|确认)', dependency=
                     v.dependency(p, 'explicit_drug_effect_study_endpoint_anaphor', ante))
                break


def _innovation_support_content(v):
    # A project may DISCUSS a defined support function before producing results.
    # Require its current innovation objective AND a specified scientific task;
    # a project name, general slogan, or application form alone is insufficient.
    emit(v, 'I', 'innovation_project_scientific_support_function',
         r'(?:(?:本|该)(?:试点工作|项目|计划)|(?:试点工作|项目|计划)的(?:核心)?目的)[^。；;]{0,20}'
         r'(?:鼓励|支持|促进)创新药[^。；;]{0,65}'
         r'(?:聚焦并解决|关注并探讨解决|帮助解决|协助解决)'
         r'[^。；;，,]{0,20}创新[^。；;，,]{0,25}药物研发'
         r'(?:中|过程中的|中的)科学问题', 'research_support')
    # Here a title resolves WHICH R&D receives the explicitly stated technical
    # resource. The two-anchor rule never assigns I from the title by itself.
    pattern = (r'(?:专门)?(?:起草|制定|编制)(?:了)?'
               r'《(?P<title>创新药(?:物)?[^》]{0,65}(?:技术指导原则|技术指南)[^》]{0,15})》'
               r'[,，](?P<function>为[^。；;]{0,120}提供(?:技术)?指导)')
    for m in re.finditer(pattern, v.normalized):
        function = m.group('function')
        sentence = next((s.group() for s in re.finditer(r'[^。；;]+', v.normalized)
                         if s.start() <= m.start() < s.end()), m.group())
        if (_carrier_only(sentence) or _disclosure_only(sentence)
                or not re.search(r'药物研发|药品研发|新药研发|临床试验', function)
                or not re.search(r'风险管理|试验设计|方案设计|剂量选择|药物设计|研究方法', function)
                or re.search(r'文件格式|申报时点|填表|上传|报送|资料递交', function)):
            continue
        dependency = {'kind':'current_named_technical_resource_and_explicit_support_function',
                      'innovation_target_title':m.group('title'),
                      'current_support_function':function,
                      'usage':'Title resolves resource target only; independent technical guidance predicate supplies I.'}
        e = v.add('V36_I_technical_guidance_resource_with_innovation_target', 'I',
                  *m.span(), 'research_support', BASIS_I, dependency=dependency)
        e['rule_release'] = RELEASE


def revise(record, result):
    if result.get('judgement_status') == 'undetermined':
        return result
    v = RuleView(record, result)
    _boundaries(v)
    _direct(v)
    _contexts(v)
    _innovation_support_content(v)
    return result

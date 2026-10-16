"""Execute the frozen five constructs with operation note v1.4.

Repairs are derived exclusively from previously exposed development text.
No ID, department, source title, reference label, or evaluation metric selects
a rule. Validated parents complete a current list proposition; they do not
propagate all dimensions. Earlier runtime files remain auditable dependencies.
"""
import re
from rule_support import RuleView
from rules_if import _norm, _carrier_only, _has_drug_object, WRONG

RELEASE = 'v32-entity-context-boundaries-20261007-candidate01'
BASIS_I = 'CAL-5D-v1.3 I; 共用操作说明v1.4 创新性1–3、5'
BASIS_F = 'CAL-5D-v1.3 F; 共用操作说明v1.4 公平性1–4及共同判断步骤'
ITEM = re.compile(r'^\s*(?:[（(][0-9一二三四五六七八九十]+[）)]|[0-9一二三四五六七八九十]+[、.．]?)[\s\S]+')


def _add(v, rule, dimension, start, end, subtype, dependency=None):
    item = v.add(rule, dimension, start, end, subtype,
                 BASIS_I if dimension == 'I' else BASIS_F,
                 dependency=dependency)
    item['rule_release'] = RELEASE


def _document_purpose_span(sentence):
    """An introductory purpose followed by promulgation is not a resource.

    Match the purpose only, so an independent substantive clause survives.
    The support object may be innovative, but that does not change the action
    from formulating/publishing a document to allocating R&D resources.
    """
    purpose = re.search(r'(?:^|[,，])\s*(?:第[一二三四五六七八九十]+条\s*)?(?:为|为了)(?:落实[^。；;]{0,140}?)?[^。；;]{0,180}?(?:鼓励|支持|促进|推动)[^。；;]{0,120}?(?:药品|药物|创新药|新药)', sentence)
    if not purpose:
        return None
    promulgation = re.search(r'(?:制定(?:了)?(?:本|该)?(?:工作程序|办法|规定|通知|指导原则|工作方案)|(?:现)?(?:印发|发布|转发)(?:给你们|如下|本|该)|制定了\s*[,，])', sentence[purpose.start():])
    if not promulgation:
        return None
    end = purpose.start()+promulgation.start()
    # A concrete instrument in the purported purpose chain is substantive.
    # A later independent support clause is untouched by span-local removal.
    prefix = sentence[purpose.start():end]
    if re.search(r'(?:建立|设立|配置|给予|提供|投入|资助|拨付|延长)(?:[^。；;，,]{0,35})(?:资源|经费|资金|基金|资助制度|保护期|独占期|平台|技术指导)', prefix):
        return None
    return purpose.start(), end


def _restore_current_list_predicate(v):
    """Interpret only explicitly bound coverage predicates on current items."""
    if not ITEM.match(v.normalized) or _carrier_only(v.text):
        return
    for parent in v.record.get('verified_parent_context', []):
        raw = parent.get('text', '')
        text = _norm(raw)
        rule = kind = None
        # Actual exit criteria, unlike application/assessment eligibility.
        if (re.search(r'调出(?:基本|医保|药品)?目录(?:的)?药品(?:的)?范围', text)
                or re.search(r'(?:以下|下列)(?:情况|情形|条件)[^。；;]{0,30}(?:药品|药物)[^。；;]{0,20}调出(?:基本|医保|药品)?目录', text)):
            rule='V32_F_bound_actual_directory_exit_condition'
            kind='verified_parent_actual_drug_coverage_exit_predicate'
        # Fund payment conditions remain coverage content even when the child
        # names only a purpose, an appropriate prescriber, or another condition.
        elif (re.search(r'(?:药品|药物)[^。；;]{0,30}费用', text)
                and re.search(r'符合(?:以下|下列)条件', text)
                and re.search(r'(?:可|可以|应)?由(?:基本医疗保险|医保)(?:基金)?支付', text)):
            rule='V32_F_bound_actual_fund_payment_condition'
            kind='verified_parent_actual_drug_fund_payment_predicate'
        # Supplementary agreements explicitly determine a new payment scope.
        # A quoted existing scope used only to choose a procedure is different.
        elif (re.search(r'(?:药品|药物)', text)
                and re.search(r'(?:同时)?符合(?:以下|下列)条件', text)
                and re.search(r'补充协议', text)
                and re.search(r'确定新的[^。；;]{0,35}支付范围', text)):
            rule='V32_F_bound_new_payment_scope_condition'
            kind='verified_parent_substantive_new_drug_payment_scope'
        if rule:
            dep = v.dependency(parent, kind, raw)
            dep['scope_usage'] = 'Complete only this current list condition; no other parent dimension is inherited.'
            _add(v,rule,'F',0,len(v.text),'access',dep)
            break


def revise(record, result):
    if result.get('judgement_status') == 'undetermined':
        return result
    v=RuleView(record,result)

    # Plain comparison is not an assertion/request about innovation attributes.
    # The second legacy branch explicitly changing a dosage form still counts;
    # any independent specific-change evidence also remains untouched.
    v.drop(lambda e: e['dimension']=='I'
           and e['rule']=='V28_I_existing_product_comparison'
           and re.search(r'对比|比较',e['text'])
           and not re.search(r'原创|新颖|创新|改良|改变|改进|优化|改善',e['text']),
           'V32_I_plain_product_comparison_not_modification',
           '普通处方/组成/结构对比要求未指明原创、改良或具体变化，不由比较动作推定创新属性。')

    for sentence in v.sentences():
        x=sentence.group()
        span=_document_purpose_span(x)
        if span:
            a,b=v.raw_span(sentence.start()+span[0],sentence.start()+span[1])
            v.drop(lambda e:e['dimension']=='I' and e.get('subtype')=='research_support'
                   and a<=e['start'] and e['end']<=b,
                   'V32_I_promulgation_purpose_not_substantive_support',
                   '制定或印发文件的创新研发宗旨不是当前实体支持；只删除宗旨范围内的支持推断，独立资源/属性内容保留。')

        # An adverb such as 优先 modifies resource allocation, not the object.
        # Generic support remains concrete even without a named procedure.
        for m in re.finditer(r'为(?:创新药(?:物)?|药品创新|药物创新)(?:的)?(?:研发|研究|开发)(?:优先|重点|及时)?(?:配置|提供|投入|拨付)[^。；;，,]{0,25}(?:资源|经费|资金|技术指导)',x):
            if not _carrier_only(m.group()) and not re.search(WRONG,m.group()):
                _add(v,'V32_I_direct_innovative_rnd_resource_allocation','I',sentence.start()+m.start(),sentence.start()+m.end(),'research_support')

        # The manual permits actual unmet treatment need without a payer or
        # supply barrier. Resolve its drug object across explanatory commas,
        # while rejecting explicitly different (software/admin/data) objects.
        drug_clauses=[c for c in re.split('[，,]',x) if _has_drug_object(c) and not re.search(WRONG,c)]
        if any(re.search(r'治疗|防治|研发|研究|用药',c) for c in drug_clauses):
            for m in re.finditer(r'(?:患者|人群)(?:仍|尚)?(?:未能|无法|不能)(?:得到|获得)(?:充分[、,，]?)?有效治疗',x):
                local=next((c for c in re.finditer(r'[^，,]+',x) if c.start()<=m.start()<c.end()),None)
                if local and not re.search(r'研究需求|数据需求|入组需求|'+WRONG,local.group()):
                    _add(v,'V32_F_current_sentence_explicit_unmet_treatment','F',sentence.start()+m.start(),sentence.start()+m.end(),'access',
                         {'kind':'current_sentence_explicit_drug_treatment_need_object','antecedent_text':x})

        # A commercial recommended list is not an insurance contract. Suppress
        # only the legacy list-count proposition, not a real basic-insurance
        # inclusion branch, actual underwriting, or an independent exception.
        a,b=v.raw_span(sentence.start(),sentence.end())
        v.drop(lambda e:e['dimension']=='F' and e['rule']=='V28_F_substantive_coverage_decision'
               and a<=e['start'] and e['end']<=b
               and re.search(r'(?:商保创新药|商业健康保险[^。；;]{0,10})目录共纳入',e['matching_text']),
               'V32_F_recommended_commercial_list_not_underwriting',
               '商保推荐目录收载数量或既有身份不等于具体保险计划实际承保；不删除同单元独立的基本医保纳排内容。')

        # The current drug-data protection scope is a substantive right,
        # including a restriction/exception. General secrecy is not this right.
        for m in re.finditer(r'药品(?:的)?数据保护范围(?:包括|限于|不包括)[^。；;]{0,180}(?:临床试验数据|试验数据)',x):
            if not _carrier_only(m.group()):
                _add(v,'V32_I_substantive_drug_data_right_scope','I',sentence.start()+m.start(),sentence.start()+m.end(),'research_support')

    # An expert consideration preference does not decide insurance membership.
    # Remove that inference only; explicit independent coverage survives.
    v.drop(lambda e:e['dimension']=='F' and e['rule']=='V28_F_coverage_priority_reference',
           'V32_F_expert_consideration_not_actual_coverage',
           '提请专家重点考虑仅是评议路径/偏好，不推定最终纳入或实际给付覆盖。')

    # The start of a specifically granted exclusive drug-data protection term
    # describes that substantive right, unlike a stand-alone filing deadline.
    for parent,prefix in v.paragraph_prefixes():
        antecedent=_norm(prefix)
        if not (re.search(r'化学药品|生物制品|药品|药物',antecedent)
                and re.search(r'给予[^。；;]{0,35}(?:[0-9一二三四五六七八九十]+年)[^。；;]{0,10}数据保护期',antecedent)):
            continue
        for sentence in v.sentences():
            for m in re.finditer(r'数据保护期自(?:该|本)?药品注册申请[^。；;]{0,30}获得批准之日起计算',sentence.group()):
                _add(v,'V32_I_substantive_exclusive_right_term_start','I',sentence.start()+m.start(),sentence.start()+m.end(),'research_support',
                     v.dependency(parent,'same_paragraph_explicit_drug_exclusive_data_right_duration',antecedent))
    _restore_current_list_predicate(v)
    return result

"""Final evidence migration to the common conceptual definitions.

This is a development candidate. Earlier rule traces remain available. I/F
are rejudged; S quality and Ec procedural/payment-name paths are gated. Other
S/Ec and E first retain their existing implementation, with E supplemented here for
an exact current requirement for drug-effectiveness evidence. Unsupported grammar is an implementation limitation, not a
proof that a human judgement is false. Candidate06 then applies its finalized
E/I boundary stage in common_definition_delta06. No reference labels are read here.
"""
import copy
import hashlib
import re

from common_if_relations import inspect_innovation, inspect_fairness
from common_se_ec_relations import inspect_safety, inspect_economics
from common_if_extensions03 import inspect_extensions
from common_if_current_relations05 import inspect_current_relations
from common_reference_resolution03 import select_direct_contexts, inspect_required_effectiveness
from common_s_design_example import inspect_safety_design_example
from rule_support import rebuild

PROTOCOL = 'UNIFIED-5D-OPERATIONAL-20261009'
RULES_SHA256 = 'fb78f1922e2e5ade34dbe076890c61c6e04e2e3ec605f9d9b3e938dfaf49437f'
DETECTORS = {'S': inspect_safety, 'Ec': inspect_economics,
             'I': inspect_innovation, 'F': inspect_fairness}
REQUIRED_CONTENT = {
    'S': r'药物安全性|用药安全性|药品安全性|不良反应|毒性|用药风险',
    'Ec': r'药费|药品费用|治疗成本|药品价格|药价|患者自付(?:费用|比例)|医保支付(?:标准|范围)|基金预算影响',
    'I': r'原创属性|原创性|技术新颖性|创新属性|实质(?:性)?改良',
    'F': r'患者可负担性|用药保障公平性|药品获取机会差异|用药保障缺口',
}


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _evidence(text, dim, relation, dependency=None):
    a, b = relation['start'], relation['end']
    assert 0 <= a < b <= len(text) and text[a:b] == relation['quote']
    e = {'rule': 'COMMON_' + dim + '_' + relation['kind'], 'dimension': dim,
         'start': a, 'end': b, 'text': text[a:b],
         'subtype': relation.get('subtype'), 'protocol_basis': PROTOCOL,
         'common_definition_basis': relation['basis']}
    if dim == 'S':
        e['safety_basis'] = 'quality_safety' if re.search(r'质量|杂质|污染', text[a:b]) else 'other_safety'
    if dependency:
        e['context_dependency'] = dependency
    return e


def _actual_bridge(text):
    """A current content obligation, not programme status or navigation."""
    masked = re.sub(r'《[^》]*》|〈[^〉]*〉', lambda m: ' ' * len(m.group()), text)
    # General navigation cannot license a substantive reference, but it also
    # cannot cancel a separate current requirement elsewhere in this unit.
    # Mask only its own comma/sentence-delimited clause, preserving offsets.
    masked = re.sub(r'(?:详见|参见)[^，,。；;\n]*', lambda m: ' ' * len(m.group()), masked)
    masked = re.sub(r'不符合纳入常规目录管理的条件', lambda m: ' ' * len(m.group()), masked)
    patterns = (
        r'(?:应当|应|须|需)(?:当)?包括(?:下列|以下)(?:药物)?(?:内容|要求|条件)?',
        r'(?:同时)?(?:满足|符合)(?:下列|以下)(?:条件|要求)',
        r'(?:评价|评估|比较|验证|证明|提供|提交|补充)[^。；;]{0,24}(?:上述|前述)(?:安全|疗效|费用|创新|公平)?(?:要求|内容|证据)',
        r'符合\s*(?:本办法|本规定|本规范)?\s*第[零一二三四五六七八九十百0-9]+条(?:规定的?|所列的?)?(?:实质)?(?:条件|要求)',
        r'符合\s*(?:本办法|本规定|本规范)?\s*第[零一二三四五六七八九十百0-9]+条第[零一二三四五六七八九十百0-9]+款(?:的|规定|情形|条件|要求)?',
    )
    for p in patterns:
        m = re.search(p, masked)
        if m:
            return m
    return None


def _authenticated_contexts(record, bridge):
    """Use certified exact references/lists; previews never certify a list."""
    groups = list(record.get('typed_contexts_v34', []))
    # Older source-verified complete-list certificates carry the same literal
    # material under a different field. Reauthenticate the interval with the
    # current adapter rather than silently dropping that necessary content.
    if not any(g.get('field') == 'complete_following_list_v11' for g in groups):
        from context_validation import verified_following_list
        from source_context_adapter_v34 import authenticate_target, following_list
        if verified_following_list(record):
            authenticate_target(record)
            cert = record['verified_following_list_v27']
            temp = copy.deepcopy(record)
            temp['complete_following_list_v11'] = cert
            shared = copy.deepcopy(record.get('llm_v29_shared_context', {}))
            shared['complete_following_list_v11'] = cert
            added, log = [], []
            following_list(temp, shared, added, log)
            groups.extend(added)
    for group in groups:
        field, role = group.get('field', ''), group.get('role', '')
        if field == 'complete_following_list_v11':
            if role not in {'current_following_conditions_only', 'current_following_list'}:
                continue
        elif field in {'explicitly_cited_articles_v10', 'explicitly_cited_qualifications_v12'}:
            if role == 'navigation_preview_only':
                continue
            for c in select_direct_contexts(group, bridge.group()):
                yield field, c
            continue
        else:
            continue
        for c in group.get('contexts', []):
            if c.get('authentication_v34'):
                yield field, c


def _context_evidence(record, text, scoped):
    bridge = _actual_bridge(text)
    if not bridge:
        return []
    found = []
    for field, c in _authenticated_contexts(record, bridge):
        content = c['text']
        for dim, detector in {**DETECTORS, 'E': inspect_required_effectiveness}.items():
            relations = detector(content, drug_scope=scoped)
            # An exact list explicitly required by the current sentence can
            # consist of noun phrases; the obligation is in the bridge itself.
            for m in re.finditer(REQUIRED_CONTENT.get(dim, r'(?!)'), content):
                relations.append({'start': m.start(), 'end': m.end(), 'quote': m.group(),
                    'kind': 'explicitly_required_content',
                    'subtype': 'attribute' if dim == 'I' else
                               'patient_affordability' if dim == 'F' and '可负担' in m.group() else
                               'guarantee_equity' if dim == 'F' else None,
                    'basis': '当前明确要求的内容，经确指且来源认证的语境补全；不复制邻段标签。'})
            for r in relations:
                if dim == 'Ec' and _payment_context_premise_only(content, r):
                    continue
                if dim == 'S' and _disease_severity_not_drug_harm(r['quote']):
                    continue
                anchor = {'text': r['quote'], 'start': r['start'], 'end': r['end'],
                    'paragraph_id': c.get('paragraph_id'),
                    'source_path': c.get('source_path'), 'source_sha256': c.get('source_sha256'),
                    'candidate_sha256': c.get('candidate_sha256'),
                    'paragraph_sha256': _sha(content), 'pages': c.get('pages', []),
                    'source_authentication': c['authentication_v34']}
                if c.get('common_exact_clause_selection03'):
                    anchor['exact_clause_selection'] = c['common_exact_clause_selection03']
                current = {'start': bridge.start(), 'end': bridge.end(), 'quote': text[bridge.start():bridge.end()],
                           'kind': 'authenticated_current_requirement',
                           'subtype': r.get('subtype'), 'basis': r['basis']}
                e = _evidence(text, dim, current, {'kind': 'common_explicit_requirement_two_anchors',
                    'source_context_field': field, 'current_unit_sha256': _sha(text),
                    'cited_content': anchor})
                e['cited_substantive_anchors'] = [anchor]
                found.append(e)
    return found


def _disease_severity_not_drug_harm(quote):
    """Current disease/condition consequences are not medicine-caused harm.

    Drug scope resolves a medicine programme, not the cause of every harm.
    This predicate acts only on the current evidence proposition, so an
    independent adjacent drug-risk proposition is retained.
    """
    disease_object=re.search(r'疾病|病情|病症|病种|所患疾病',quote)
    disease_consequence=re.search(r'严重|不可治愈|发展不可逆|危及生命|影响生存质量|缩短生命|导致患者死亡|致残|残疾|(?:生理|社会)功能缺失',quote)
    medicine_harm=re.search(r'不良反应|毒性|药物警戒|用药(?:风险|安全)|药品损害|'
        r'(?:药物|药品|该药|本药|本品|用药|给药|服药|试验治疗)[^，,。；;]{0,24}(?:诱发|导致|引起|造成|损害|危及|风险|损伤)',quote)
    return bool(disease_object and disease_consequence and not medicine_harm)

def _payment_name_or_premise_only(quote):
    value = re.split(r'[:：]', quote)[-1]
    return bool(re.search(r'原(?:医保)?支付(?:范围|标准)', value)
                and re.search(r'满足条件|符合条件|的情况下|作为前提', value)
                and not re.search(r'预算|支出|费用|金额|承担|自付|降幅|不超过|不高于|不低于', value))


def _payment_context_premise_only(text, relation):
    # A required-content noun span can omit its preceding "原" and following
    # eligibility premise. Inspect its actual enclosing clause, not that noun
    # in isolation, so the noun fallback cannot bypass the procedural filter.
    start, end = relation['start'], relation['end']
    left = max((text.rfind(c, 0, start) for c in '，,。；;'), default=-1) + 1
    right = min((i for c in '，,。；;' if (i := text.find(c, end)) >= 0), default=len(text))
    return _payment_name_or_premise_only(text[left:right])


def _supplemental_current_relations(text, scoped):
    """Explicit relationships omitted by short-distance first-pass grammar."""
    out = []
    if not scoped and not re.search(r'药品|药物|用药', text):
        return out
    masked = re.sub(r'《[^》]*》|〈[^〉]*〉', lambda m: ' ' * len(m.group()), text)
    for s in re.finditer(r'[^。；;]+', masked):
        value = s.group()
        original = text[s.start():s.end()]
        if (re.search(r'创新药(?:物)?|改良型新药', value)
                and re.search(r'申请(?:适用|纳入)突破性治疗药物程序', value)
                and re.search(r'(?:与现有治疗手段相比[^。；;]*明显临床优势|尚无有效防治手段)', value)):
            out.append(('I', {'start': s.start(), 'end': s.end(), 'quote': original,
                'kind': 'actual_innovative_qualification_comparison', 'subtype': 'qualification_advantage',
                'basis': '创新／改良对象、当前突破性治疗资格及实质比较条件共同出现；不把疾病严重程度当药物损害。'}))
        if (re.search(r'药品目录|药品保障|用药保障', value)
                and re.search(r'保障(?:更加|应当|应|要|实现)?公平可及', value)
                and not re.search(r'公平竞争|公平招标|公平交易', value)):
            out.append(('F', {'start': s.start(), 'end': s.end(), 'quote': original,
                'kind': 'explicit_drug_guarantee_equity_goal', 'subtype': 'guarantee_equity',
                'basis': '当前药品保障安排明确提出公平可及目标；表示政策关注，不宣称目标已经实现。'}))
        if (re.search(r'适应[证症]|治疗需要|用药需求|用药需要', value)
                and re.search(r'(?:可不受|不受|取消|解除)[^。；;]{0,35}(?:一品两规|药品总品种数|机构品种数)[^。；;]{0,15}限制', value)):
            out.append(('F', {'start': s.start(), 'end': s.end(), 'quote': original,
                'kind': 'needs_linked_nonclinical_quantity_restriction', 'subtype': 'opportunity_barrier',
                'basis': '明确适应人群／用药需要与解除机构品种数量限制相连；不是仅凭人群名称赋F。'}))
        m = re.search(r'(?:开展|组织)[^。；;]{0,25}用药需求评估[，,]\s*指导[^。；;]{0,120}(?:组织)?制定[^。；;]{0,25}用药遴选(?:和调整)?规则', value)
        if m:
            out.append(('F', {'start': s.start()+m.start(), 'end': s.start()+m.end(), 'quote': text[s.start()+m.start():s.start()+m.end()],
                'kind': 'needs_assessment_explicitly_guides_drug_selection', 'subtype': 'needs_based_guarantee',
                'basis': '用药需求评估经当前明确指导关系作用于用药遴选规则；中间行政主体不切断这一关系。'}))
    return out


def _retained_guidance(e):
    """Scientific-guidance family is rejudged by the local I3 owner.

    Preserve earlier evidence in the migration trace, never retain its title
    object as an independent positive beside the replacement role resolver.
    """
    return False

def _evidence_has_drug_quality_relation(e, text):
    """Migrate a quality relation attached to this evidence, not a sentence word.

    Health-related quality of life and study/data quality are different objects.
    An independent drug-harm or PV proposition beside product quality survives.
    """
    if e.get('safety_basis') == 'quality_safety' or re.search(r'quality', e.get('rule', ''), re.I):
        return True
    start, end = e['start'], e['end']
    left = max((text.rfind(c, 0, start) for c in '，,。；;'), default=-1) + 1
    right = min((i for c in '，,。；;' if (i := text.find(c, end)) >= 0), default=len(text))
    clause = text[left:right]
    masked = re.sub(r'(?:生活|生存)质量|(?:研究|试验)?数据(?:的)?质量|(?:试验|研究|评价)质量',
                    lambda m: ' ' * len(m.group()), clause)
    quality = re.compile(r'(?:药品|药物|制剂|产品)(?:的)?质量(?:安全|风险|可控|控制|标准|检验|问题|评价)?'
                         r'|杂质|纯度|(?:药品|药物|制剂)(?:的)?稳定性|生产工艺|制剂工艺')
    local_start, local_end = start-left, end-left
    for match in quality.finditer(masked):
        if match.start() < local_end and local_start < match.end():
            return True
        # A quality-caused harm relation is implicated, while a coordinate
        # "quality and independent safety" list is not automatically migrated.
        if match.end() <= local_start and re.search(r'导致|造成|引起|诱发|带来|危及|损害',
                                                   masked[match.end():local_start]):
            return True
    return False


def _unchanged_relation(e, text):
    """Retain unaffected safety/cost evidence; migrate implicated paths only."""
    dim = e['dimension']
    start, end = e['start'], e['end']
    left = max((text.rfind(c, 0, start) for c in '。；;'), default=-1) + 1
    stops = [text.find(c, end) for c in '。；;']
    right = min((i for i in stops if i >= 0), default=len(text))
    proposition = text[left:right]
    if dim == 'S':
        return not _evidence_has_drug_quality_relation(e, text)
    if dim == 'Ec':
        # The changed boundary concerns prices/payment objects and procedure,
        # not unchanged explicit treatment costs, sales, or budget estimates.
        return not bool(re.search(r'价格|药价|支付标准|支付范围|谈判|协商|协议', e['text']))
    return False


def revise(record, result):
    result['semantic_protocol'] = PROTOCOL
    result['common_rules_sha256'] = RULES_SHA256
    result['status'] = 'common_definition_development_candidate_not_adopted'
    if result.get('judgement_status') == 'undetermined':
        return result
    text = record['unit_text']
    prior = copy.deepcopy(result.get('evidence', []))
    scoped = bool(result.get('drug_object_evidence') or result.get('drug_object_in_unit'))
    if not scoped:
        from common_parent_object03 import resolve_enumerated_drug_object
        object_evidence = resolve_enumerated_drug_object(record)
        if object_evidence:
            result['common_definition_resolved_drug_object03'] = object_evidence
            result['drug_object_evidence'] = object_evidence
            scoped = True
    new = [e for e in result.get('evidence', []) if e['dimension'] == 'E']
    for dim, detector in DETECTORS.items():
        for relation in detector(text, drug_scope=scoped):
            if dim == 'S' and _disease_severity_not_drug_harm(relation['quote']):
                continue
            if dim == 'Ec' and _payment_name_or_premise_only(relation['quote']):
                continue
            new.append(_evidence(text, dim, relation))
    for dim, relation in _supplemental_current_relations(text, scoped):
        new.append(_evidence(text, dim, relation))
    for relation in inspect_safety_design_example(record):
        new.append(_evidence(text, 'S', relation, relation['context_dependency']))
    for e in prior:
        if _unchanged_relation(e, text):
            kept = copy.deepcopy(e)
            kept['common_definition_basis'] = '该实质关系未受本轮质量／流程名称边界变更影响，保留既有来源及对象约束。'
            new.append(kept)
        elif e['dimension'] == 'I' and _retained_guidance(e):
            kept = copy.deepcopy(e)
            kept['prior_rule'] = kept['rule']
            kept['rule'] = 'COMMON_I_authenticated_targeted_scientific_guidance'
            kept['protocol_basis'] = PROTOCOL
            kept['common_definition_basis'] = '特定创新研发对象与当前实际技术指导供给同时成立。'
            new.append(kept)
    new.extend(_context_evidence(record, text, scoped))
    for e in inspect_extensions(record, result) + inspect_current_relations(record, result):
        e['protocol_basis'] = PROTOCOL
        e['common_definition_basis'] = e['basis']
        new.append(e)
    unique = {}
    for e in new:
        key = (e['dimension'], e['start'], e['end'], e.get('subtype'),
               (e.get('context_dependency') or {}).get('kind'),
               str(e.get('cited_substantive_anchors', [])))
        unique.setdefault(key, e)
    result['evidence'] = list(unique.values())
    result['common_definition_prior_evidence'] = prior
    result['common_definition_migration_trace'] = []
    for e in prior:
        if e['dimension'] not in DETECTORS:
            continue
        supported = any(n['dimension'] == e['dimension'] and n['start'] < e['end']
                        and e['start'] < n['end'] for n in result['evidence'])
        result['common_definition_migration_trace'].append({
            'dimension': e['dimension'], 'prior_rule': e['rule'],
            'start': e['start'], 'end': e['end'], 'text': e['text'],
            'action': 'common_relation_available' if supported else 'old_evidence_not_sufficient_under_common_implementation',
            'interpretation': '概念变化或规则语法未覆盖须结合原文复核，不能据此宣称原人工标签错误。'})
    result = rebuild(result)
    masked = re.sub(r'《[^》]*》', lambda m: ' ' * len(m.group()), text)
    result['quality_content_without_safety'] = bool(not result['labels']['S'] and re.search(
        r'药品质量|药物质量|药品注册标准|药典|质量标准|质量风险|质量安全|纯度|杂质|稳定性|质量可控|生产工艺', masked))
    result['clinical_management_content'] = bool(re.search(
        r'临床管理难度|监测频率|高频监测|吞咽困难|开启包装|给药便利|储存条件', masked))
    result['implementation_scope_note'] = 'I/F依据共同关系语法重判，S质量与Ec流程／支付名称路径迁移；其他S/Ec及E保留既有实现，E仅补确指款次实际要求的有效性试验数据；有界开发检查不等于独立效度检验。'
    return result

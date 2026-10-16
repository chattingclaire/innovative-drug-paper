"""Final evidence migration to the common conceptual definitions.

This is a development candidate. Earlier rule traces remain available. I/F
are rejudged; S quality and Ec procedural/payment-name paths are gated. Other
S/Ec and E retain their unchanged implementation. Unsupported grammar is an implementation limitation, not a
proof that a human judgement is false. No reference labels are read here.
"""
import copy
import hashlib
import re

from common_if_relations import inspect_innovation, inspect_fairness
from common_se_ec_relations import inspect_safety, inspect_economics
from rule_support import rebuild

PROTOCOL = 'COMMON-5D-20261009'
RULES_SHA256 = '6b902fd7518379d5edc8e100c1192b627202a0069e69d6e40fea72cad7880a28'
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
    if re.search(r'不符合纳入常规目录管理的条件|详见|参见[^。]*工作方案', text):
        return None
    patterns = (
        r'(?:应当|应|须|需)(?:当)?包括(?:下列|以下)(?:药物)?(?:内容|要求|条件)?',
        r'(?:同时)?(?:满足|符合)(?:下列|以下)(?:条件|要求)',
        r'(?:评价|评估|比较|验证|证明|提供|提交|补充)[^。；;]{0,24}(?:上述|前述)(?:安全|疗效|费用|创新|公平)?(?:要求|内容|证据)',
        r'符合(?:本办法|本规定|本规范)?第[零一二三四五六七八九十百0-9]+条(?:规定的?|所列的?)?(?:实质)?(?:条件|要求)',
    )
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m
    return None


def _authenticated_contexts(record, bridge):
    """Use certified exact references/lists; previews never certify a list."""
    for group in record.get('typed_contexts_v34', []):
        field, role = group.get('field', ''), group.get('role', '')
        if field == 'complete_following_list_v11':
            if role not in {'current_following_conditions_only', 'current_following_list'}:
                continue
        elif field in {'explicitly_cited_articles_v10', 'explicitly_cited_qualifications_v12'}:
            address = group.get('reference_address', '') or ''
            articles = re.findall(r'第[零一二三四五六七八九十百0-9]+条', address)
            if articles and not any(a in bridge.group() for a in articles):
                continue
            if role == 'navigation_preview_only':
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
        for dim, detector in DETECTORS.items():
            relations = detector(content, drug_scope=scoped)
            # An exact list explicitly required by the current sentence can
            # consist of noun phrases; the obligation is in the bridge itself.
            for m in re.finditer(REQUIRED_CONTENT[dim], content):
                relations.append({'start': m.start(), 'end': m.end(), 'quote': m.group(),
                    'kind': 'explicitly_required_content',
                    'subtype': 'attribute' if dim == 'I' else
                               'patient_affordability' if dim == 'F' and '可负担' in m.group() else
                               'guarantee_equity' if dim == 'F' else None,
                    'basis': '当前明确要求的内容，经确指且来源认证的语境补全；不复制邻段标签。'})
            for r in relations:
                anchor = {'text': r['quote'], 'start': r['start'], 'end': r['end'],
                    'paragraph_id': c.get('paragraph_id'),
                    'source_path': c.get('source_path'), 'source_sha256': c.get('source_sha256'),
                    'candidate_sha256': c.get('candidate_sha256'),
                    'paragraph_sha256': _sha(content), 'pages': c.get('pages', []),
                    'source_authentication': c['authentication_v34']}
                current = {'start': bridge.start(), 'end': bridge.end(), 'quote': bridge.group(),
                           'kind': 'authenticated_current_requirement',
                           'subtype': r.get('subtype'), 'basis': r['basis']}
                e = _evidence(text, dim, current, {'kind': 'common_explicit_requirement_two_anchors',
                    'source_context_field': field, 'current_unit_sha256': _sha(text),
                    'cited_content': anchor})
                e['cited_substantive_anchors'] = [anchor]
                found.append(e)
    return found


def _retained_guidance(e):
    """Audited two-anchor guidance implementations unchanged in meaning."""
    dep = e.get('context_dependency') or {}
    if e.get('rule') == 'V36_I_technical_guidance_resource_with_innovation_target':
        return (dep.get('kind') == 'current_named_technical_resource_and_explicit_support_function'
                and bool(dep.get('innovation_target_title')) and bool(dep.get('current_support_function')))
    if e.get('rule') == 'V37_I_actual_professional_scientific_guidance':
        return (dep.get('kind') == 'authenticated_innovation_object_and_current_scientific_guidance'
                and bool(dep.get('innovation_object_scope')) and bool(dep.get('source_authentication')))
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
        quality_path = (e.get('safety_basis') == 'quality_safety' or
                        bool(re.search(r'质量|杂质|纯度|稳定性|生产工艺', proposition)) or
                        bool(re.search(r'quality', e.get('rule', ''), re.I)))
        return not quality_path
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
    new = [e for e in result.get('evidence', []) if e['dimension'] == 'E']
    for dim, detector in DETECTORS.items():
        for relation in detector(text, drug_scope=scoped):
            new.append(_evidence(text, dim, relation))
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
        r'药品质量|药物质量|药典|质量标准|质量风险|质量安全|纯度|杂质|稳定性|质量可控|生产工艺', masked))
    result['clinical_management_content'] = bool(re.search(
        r'临床管理难度|监测频率|高频监测|吞咽困难|开启包装|给药便利|储存条件', masked))
    result['implementation_scope_note'] = 'I/F依据共同关系语法重判，S质量与Ec流程／支付名称路径迁移，其他S/Ec及E保留既有实现；有界开发检查不等于独立效度检验。'
    return result

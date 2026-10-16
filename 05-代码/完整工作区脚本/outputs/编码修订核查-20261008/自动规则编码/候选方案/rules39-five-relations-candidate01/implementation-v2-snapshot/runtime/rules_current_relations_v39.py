"""Five exposed-development relation repairs under unchanged CAL-5D.

Only current linguistic relations and authenticated supplied context are used.
No reference labels, real IDs, department names, filenames or target scores.
Unrecognized grammar remains a coverage limitation, never a new definition.
"""
import hashlib
import copy
import re
from baseline_candidate17 import matching_view
from rule_support import RuleView
from inherited_rules_v25 import _without_titles
from rules_se import S_BASIS, E_BASIS
from rules_ec import EC_BASIS
from rules_if import BASIS_I, BASIS_F
from referenced_relations_v34 import content_matches
from source_context_adapter_v34 import authenticate_target, authenticate_context

RELEASE = 'v39-five-current-relations-development'
ARTICLE = r'第[零一二三四五六七八九十百0-9]+条'
BASIS = {'S': S_BASIS, 'E': E_BASIS, 'Ec': EC_BASIS}
STAT_KEYS = ('协变量', '敏感性分析', '倾向评分', '接受治疗的概率', '接受治疗概率')


def emit(v, dim, start, end, suffix, dependency=None, subtype=None, quality=False):
    basis = BASIS.get(dim, BASIS_I if dim == 'I' else BASIS_F)
    e = v.add('V39_' + dim + '_' + suffix, dim, start, end, subtype, basis,
              dependency=dependency, safety_basis=('quality_safety' if quality else 'other_safety') if dim == 'S' else None)
    e['rule_release'] = RELEASE
    return e


def prepare(record):
    """Missing current substantive article content is material insufficiency.

    Navigation/title references do not trigger this guard. Fine addresses remain
    conservatively unsupported by the addition, rather than reading siblings.
    """
    normalized = matching_view(record['unit_text'])[0]
    text = _without_titles(normalized)
    missing = set()
    for sentence in re.finditer(r'[^。；;]+', text):
        current = sentence.group()
        if not re.search(r'药品|药物|该药|本药', current):
            continue
        relation = re.search(r'(?:符合|满足)[^。；;]{0,90}?' + ARTICLE + r'(?:[、和及与,，]*(?:' + ARTICLE + r'))*[^。；;]{0,12}(?:规定|条件|要求)', current)
        if not relation or re.search(r'文件名|命名|归档|标注|格式|标题|填写说明|参见|详见', current[:relation.start()]):
            continue
        cited = set(re.findall(ARTICLE, relation.group()))
        available = set()
        for group in record.get('typed_contexts_v34', []):
            if group.get('field') != 'explicitly_cited_articles_v10':
                continue
            for c in group.get('contexts', []):
                if c.get('authentication_v34'):
                    available.update(re.findall(ARTICLE, c.get('article') or group.get('reference_address') or ''))
        missing.update(cited - available)
    if not missing:
        return record
    out = copy.deepcopy(record)
    out['input_assessment'] = {'status': 'context_insufficient', 'reason': 'current_substantive_cited_article_content_missing'}
    out['current_reference_gate_v39'] = {'missing_current_cited_articles': sorted(missing), 'publishable': False, 'rule_release': RELEASE}
    return out


def article_condition(v):
    # A reference can be an eligibility condition without being actual coverage.
    # Only S/E/Ec content is read: the cited disposal consequence never supplies F.
    for s in re.finditer(r'[^。；;]+', v.text):
        text = s.group()
        if not re.search(r'药品|药物|该药|本药', text):
            continue
        relation = re.search(r'(?:符合|满足)[^。；;]{0,90}?' + ARTICLE + r'(?:[、和及与,，]*(?:' + ARTICLE + r'))*[^。；;]{0,12}(?:规定|条件|要求)', text)
        if not relation:
            continue
        if re.search(r'文件名|命名|归档|标注|格式|标题|填写说明|参见|详见', text[:relation.start()]):
            continue
        if re.search(ARTICLE + r'(?:第[零一二三四五六七八九十百0-9]+[款项]|[（(][零一二三四五六七八九十0-9]+[）)])', relation.group()):
            # Exact sub-article resolution is not implemented; never read siblings.
            continue
        cited = set(re.findall(ARTICLE, relation.group()))
        for group in v.record.get('typed_contexts_v34', []):
            if group.get('field') != 'explicitly_cited_articles_v10':
                continue
            for c in group.get('contexts', []):
                auth = c.get('authentication_v34')
                # No absent address is treated as a licence to read all context.
                address = c.get('article') or group.get('reference_address') or ''
                addresses = set(re.findall(ARTICLE, address))
                if not auth or not addresses or not addresses.issubset(cited):
                    continue
                for dim in ('S', 'E', 'Ec'):
                    anchors = list(content_matches(c['text'], dim))
                    if dim == 'Ec':
                        for m in re.finditer(r'药物经济性|经济性|价格或费用[^。；;，,]{0,12}(?:偏高|合理)', c['text']):
                            a = max(c['text'].rfind(k, 0, m.start()) for k in '。；;') + 1
                            stops = [c['text'].find(k, m.end()) for k in '。；;']
                            b = min((x for x in stops if x >= 0), default=len(c['text']))
                            quote = c['text'][a:b]
                            if re.search(r'公开|公示|保密|归档|文件名|格式', quote) and not re.search(r'评价|评估|考虑|符合|条件|分析', quote):
                                continue
                            anchors.append((a, b, quote))
                    for a, b, quote in anchors:
                        dep = {'kind': 'current_explicit_compliance_with_authenticated_cited_article_content',
                               'current_cited_articles': sorted(cited), 'cited_article': address,
                               'cited_paragraph_id': c.get('paragraph_id'), 'cited_source_path': c.get('source_path'),
                               'cited_source_sha256': c.get('source_sha256'), 'cited_candidate_sha256': c.get('candidate_sha256'),
                               'cited_start': a, 'cited_end': b, 'cited_text': quote, 'source_authentication': auth,
                               'dimension_permission': 'S/E/Ec content only; no uncited article, title, disposal consequence, I/F propagation'}
                        quality = (dim == 'S' and bool(re.search(r'药品质量(?:安全|风险)', quote)) and not re.search(r'安全有效|不良反应|不良事件|毒性|毒理|用药风险|药物风险', quote))
                        e = emit(v, dim, s.start() + relation.start(), s.start() + relation.end(), 'explicit_article_content_condition' + ('_quality' if quality else ''), dep, quality=quality)
                        existing = next(x for x in v.result['evidence'] if x['rule'] == e['rule'] and x['dimension'] == dim and x['start'] == e['start'] and x['end'] == e['end'])
                        anchor = {'article': address, 'start': a, 'end': b, 'text': quote,
                                  'paragraph_id': c.get('paragraph_id'), 'source_path': c.get('source_path'),
                                  'source_sha256': c.get('source_sha256'), 'candidate_sha256': c.get('candidate_sha256'),
                                  'paragraph_sha256': hashlib.sha256(c['text'].encode()).hexdigest(), 'source_authentication': auth}
                        if anchor not in existing.setdefault('cited_substantive_anchors', []):
                            existing['cited_substantive_anchors'].append(anchor)
                        existing['current_relation_anchor'] = {k: existing[k] for k in ('start', 'end', 'text')}


def statistical_effect_purpose(v):
    current_keys = [k for k in STAT_KEYS if k in v.text]
    if not current_keys or not v.drug_scope:
        return
    # Authenticate the exact supplied same paragraph; no document-wide search.
    for p in v.record.get('paragraph_context', []):
        full, offsets = matching_view(p.get('text', ''))
        if full.count(v.normalized) != 1:
            continue
        for m in re.finditer(r'[^。；;]+', full):
            clause = m.group()
            shared = [k for k in current_keys if k in clause]
            if not shared or not re.search(r'疗效估计|药物疗效(?:的)?(?:估计|上下限)|估计(?:的)?疗效', clause):
                continue
            if re.search(r'另一项|另一种|另一个|独立研究|其他研究|文件名|归档|上传格式|公开|保密', clause):
                continue
            if not re.search(r'检测|分析|估计|确定|评价|影响|协助|用于', clause):
                continue
            authenticate_target(v.record)
            c = authenticate_context({**p, 'source_path': v.record.get('unit_source') or v.record.get('source'),
                                      'source_sha256': v.record.get('unit_source_sha256') or v.record.get('source_sha256'),
                                      'candidate_path': v.record['candidate_file'], 'candidate_sha256': v.record['candidate_sha256'],
                                      'source_lines': p.get('source_lines') or p.get('line_ids')})
            a, b = offsets[m.start()][0], offsets[m.end()-1][1]
            emit(v, 'E', 0, len(v.text), 'same_paragraph_statistical_effect_estimation',
                 {'kind': 'authenticated_same_paragraph_same_statistical_object_explicit_effect_estimation_purpose',
                  'shared_statistical_object': shared, 'paragraph_id': p.get('paragraph_id'),
                  'context_start': a, 'context_end': b, 'context_text': p['text'][a:b],
                  'source_sha256': c['source_sha256'], 'source_authentication': c['authentication_v34']})
            return


def current_risk_history(v):
    for s in re.finditer(r'[^。；;]+', v.text):
        text = s.group()
        if not re.search(r'处方(?:审核|审查)|审方', text):
            continue
        if not re.search(r'提供|收集|获取|查阅|索取|核查', text):
            continue
        m = re.search(r'(?:药物|药品|用药)?过敏史', text)
        if not m:
            continue
        emit(v, 'S', s.start(), s.end(), 'prescription_review_concrete_allergy_history',
             {'kind': 'current_prescription_review_requires_specific_patient_drug_risk_history',
              'concrete_risk_information': m.group(), 'usage': 'Risk-history content supplies S, general information-system or prescription-review identity does not; no F inference.'})


def current_product_attribute_change(v):
    for s in re.finditer(r'[^。；;]+', v.text):
        text = s.group()
        if not re.search(r'药品|药物|该药|本药', text):
            continue
        approved = re.search(r'(?:经|获得|已经|已获)[^。；;]{0,20}(?:药监|药品监督管理|国家药品监管)[^。；;]{0,15}批准', text)
        change = re.search(r'(?:适应症|功能主治)(?:或(?:适应症|功能主治))?[^。；;，,]{0,8}(?:发生|有)[^。；;，,]{0,4}重大(?:变化|改变)', text)
        if not approved or not change:
            continue
        if re.search(r'未发生|没有发生|未有', text[max(0, change.start()-6):change.end()]):
            continue
        emit(v, 'I', s.start(), s.end(), 'approved_major_product_attribute_change',
             {'kind': 'current_approved_concrete_product_attribute_change_relative_to_existing_product',
              'approval_anchor': approved.group(), 'attribute_change_anchor': change.group(),
              'usage': 'Operation v1.4 I2: concrete changed indication/function; no novelty keyword or demonstrated superiority required.'}, 'attribute')


def current_routine_prescription_channel(v):
    for s in re.finditer(r'[^。；;]+', v.text):
        text = s.group()
        if not re.search(r'医疗机构|医院', text) or not re.search(r'定点(?:零售)?药店', text):
            continue
        if not re.search(r'连通|互通|连接|衔接|建立[^。；;]{0,15}(?:渠道|通道)', text):
            continue
        if not re.search(r'(?:保证|保障|确保|实现)[^。；;]{0,10}电子处方流转|电子处方流转(?:渠道|通道)|凭处方(?:取药|购药)', text):
            continue
        if re.search(r'仅归档|仅记录|仅储存|只归档|仅统计', text):
            continue
        emit(v, 'F', s.start(), s.end(), 'routine_institution_pharmacy_prescription_acquisition_channel',
             {'kind': 'current_routine_treatment_prescription_access_channel_between_institution_and_designated_pharmacy',
              'usage': 'Concrete routine treatment acquisition channel; no affordability, cost, or general platform inference.'}, 'access')


def revise(record, result):
    if result.get('judgement_status') == 'undetermined':
        return result
    v = RuleView(record, result)
    article_condition(v)
    statistical_effect_purpose(v)
    current_risk_history(v)
    current_product_attribute_change(v)
    current_routine_prescription_channel(v)
    return result

"""Two bounded development repairs; preimplementation controls are frozen.

Source identifiers/hashes authenticate a supplied parent only. No identifier,
department, filename meaning, reference label or score is a coding feature.
"""
import re
from rule_support import RuleView, baseline
from rules_if import BASIS_F, _carrier_only, _disclosure_only
from rules_se import S_BASIS
from context_validation import validate_added_parents, digest

RELEASE = 'v36.2-two-bounded-omissions-development'
ITEM = re.compile(r'^\s*(?:[（(][一二三四五六七八九十0-9]+[）)]|[一二三四五六七八九十0-9]+[、.．:：]|[•●])')


def renewal_predicate(parent_text):
    """Return the literal actual-renewal/result-period proposition, not filing."""
    text = re.sub(r'\s+', '', baseline.matching_view(parent_text)[0])
    return re.search(
        r'(?:同时)?(?:满足|符合)(?:以下|下列)条件的药品[,，]'
        r'(?:可以|可|应当|应|予以)(?:简易)?续约[,，]'
        r'续约有效期(?:为)?[0-9一二两三四五六七八九十]+(?:年|个月|月)', text)


def current_renewal_condition(text):
    """A substantive list condition, not an isolated heading or upload duty."""
    if not ITEM.match(text) or _carrier_only(text) or _disclosure_only(text):
        return False
    if (re.search(r'填写|填报|上传|递交|截止时间|提交申请表|提交申报材料', text)
            and not re.search(r'药品费用|基金支出|预算增幅|支付范围|临床价值', text)):
        return False
    return bool(re.search(r'不超过|超过|不低于|达到|未发生|不调整|调整支付范围|'
                          r'连续纳入|到期|独家|非独家|变化|满足', text))


def _authenticated_parent(record, p):
    # The caller's standard gate validates actual source and candidate bytes.
    # Recheck here so this module cannot be invoked with a bare asserted parent.
    return (p.get('verification', {}).get('verified') is True
            and bool(p.get('repair_version'))
            and p.get('source_path') == (record.get('unit_source') or record.get('source'))
            and p.get('source_sha256') == (record.get('unit_source_sha256') or record.get('source_sha256'))
            and p.get('candidate_path') == record.get('candidate_file')
            and p.get('candidate_sha256') == record.get('candidate_sha256')
            and bool(p.get('source_sha256') and p.get('candidate_sha256'))
            and p.get('unit_id') == record.get('unit_id')
            and p.get('original_unit_sha256') == digest(record['unit_text'])
            and p.get('text_sha256') == digest(p.get('text', ''))
            and bool(p.get('paragraph_id')))


def _renewal(v):
    if not current_renewal_condition(v.text):
        return
    for p in v.record.get('verified_parent_context', []):
        predicate = renewal_predicate(p.get('text', ''))
        if predicate and _authenticated_parent(v.record, p):
            validate_added_parents(v.record)
            from source_context_adapter_v34 import authenticate_target, authenticate_context
            authenticate_target(v.record)
            authenticate_context(p)
            dep = v.dependency(p, 'source_bound_actual_drug_renewal_with_duration', p['text'])
            dep['matched_parent_predicate'] = predicate.group()
            dep['usage'] = 'Compose current substantive list condition with actual renewal and duration; no other dimension inherited.'
            e = v.add('V362_F_verified_actual_renewal_condition', 'F', 0, len(v.text),
                      'access', BASIS_F, dependency=dep)
            e['rule_release'] = RELEASE
            break


def drug_treatment_safety_matches(text):
    """Bind a safety-control predicate to an explicitly named drug treatment.

    Chemotherapy is a drug-treatment object; a mixed enumeration can contain
    surgery without cancelling its chemotherapy member. General medical
    quality or infusion alone is not enough. Facility/data safety is excluded.
    """
    pattern = (r'(?:加强|强化|做好|实施|开展)'
               r'(?P<objects>[^。；;，,]{0,45}(?:化疗|药物输注|静脉给药)[^。；;，,]{0,45})'
               r'(?:的)?(?:质量)?安全(?:管理|风险控制|控制|风险管理)')
    for m in re.finditer(pattern, text):
        sentence = next((s.group() for s in re.finditer(r'[^。；;]+',text)
                         if s.start() <= m.start() < s.end()),m.group())
        if (_carrier_only(sentence) or _disclosure_only(sentence)
                or re.search(r'科室|诊室|设备|信息|数据|网络|消防|排班|收费|培训',m.group('objects'))):
            continue
        yield m


def revise(record, result):
    if result.get('judgement_status') == 'undetermined':
        return result
    v = RuleView(record, result)
    _renewal(v)
    for m in drug_treatment_safety_matches(v.text):
        anchor = re.search(r'化疗|药物输注|静脉给药',m.group('objects')).group()
        e = v.add('V362_S_explicit_drug_treatment_safety_control', 'S', *m.span(),
                  basis=S_BASIS, safety_basis='other_safety',
                  dependency={'kind':'current_explicit_drug_treatment_safety_object',
                              'drug_treatment_anchor':anchor,
                              'usage':'Safety control of the named drug treatment; no inference from general medical-service quality.'})
        e['rule_release'] = RELEASE
    return result

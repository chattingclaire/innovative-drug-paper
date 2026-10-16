"""Bounded relations for exposed real-material coverage, under the fixed manual.

No record identity, filename meaning, department, reference labels, or scores
are coding features. Current relationships are required; a certified guideline
scope supplies only its R&D object, never its other attention dimensions.
"""
from __future__ import annotations

import re

from rule_support import rebuild

MANUAL_SHA256 = '24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9'
VERSION = 'measurement-semantic-coverage-01'
C = r'[^，,。！？!?；;\n]'
J = r'[^。！？!?；;\n]'
DRUG = r'(?:药品|药物|用药|该药|本药|制剂)'
INNOVATIVE = r'(?:创新药(?:物)?|改良型新药|改良型药品)'
_TITLE = re.compile(r'《[^》\n]*》|〈[^〉\n]*〉')
_CARRIER = re.compile(r'文件名|栏目名称|上传格式|填写格式|排版|字体|字符串|字样')
_OTHER = re.compile(r'非药物治疗|设备自身|软件自身|数据安全|基金安全|网络风险')


def _mask(text):
    return _TITLE.sub(lambda m: ' ' * len(m.group()), text)


def _segments(text):
    """Top-level comma clauses; punctuation in administrative brackets is local."""
    stack, start = [], 0
    pairs = {'(': ')', '（': '）', '[': ']', '【': '】'}
    for index, char in enumerate(text):
        if char in pairs:
            stack.append(pairs[char])
        elif stack and char == stack[-1]:
            stack.pop()
        if not stack and char in '，,。！？!?；;\n':
            if index > start:
                yield start, index, text[start:index], char
            start = index + 1
    if start < len(text):
        yield start, len(text), text[start:], ''


def _anchor(text, start, end, role):
    return {'role': role, 'start': start, 'end': end, 'text': text[start:end]}


def _emit(out, text, dimension, kind, start, end, anchors, subtype=None,
          dependency=None, basis=''):
    quote = text[start:end]
    if not quote or _CARRIER.search(quote) or _OTHER.search(quote):
        return
    for anchor in anchors:
        assert text[anchor['start']:anchor['end']] == anchor['text']
    evidence = {'dimension': dimension, 'rule': 'COMMON11_' + dimension + '_' + kind,
                'start': start, 'end': end, 'text': quote, 'subtype': subtype,
                'current_relation_anchors': anchors,
                'target_common_rules_sha256': MANUAL_SHA256,
                'common_definition_basis': basis, 'rule_release': VERSION}
    if dimension == 'S':
        evidence['safety_basis'] = 'other_safety'
    if dependency is not None:
        evidence['context_dependency'] = dependency
    out.append(evidence)


def _matched(out, text, dimension, kind, pattern, roles, subtype=None, basis=''):
    for match in re.finditer(pattern, _mask(text)):
        anchors = [_anchor(text, match.start(name), match.end(name), role)
                   for name, role in roles.items() if match.group(name)]
        _emit(out, text, dimension, kind, *match.span(), anchors, subtype, basis=basis)


def _safety(text, out):
    _matched(out, text, 'S', 'treatment_adverse_effect_causal_harm',
        rf'(?P<treatment>治疗|药物治疗|用药)(?:相关|所致)(?:的)?'
        rf'(?P<risk>不良反应)(?:而)?(?:存在|发生|出现|造成|导致|引起)'
        rf'{C}{{0,60}}(?P<harm>(?:疾病|症状|健康)(?:负担|损害)|(?:患者|人体)损害)',
        {'treatment': 'drug_treatment', 'risk': 'adverse_effect', 'harm': 'harm_outcome'},
        'adverse_effects', 'S：当前治疗相关不良反应与患者损害/症状负担明确相连，非疾病严重程度推定。')
    _matched(out, text, 'S', 'drug_population_risk_consideration',
        rf'(?P<object>药物|药品|该药|本药)(?:用于|应用于|使用于)'
        rf'(?P<population>{C}{{1,20}}?人群)(?:时)?(?:在)?'
        rf'(?P<risk>风险(?:控制|管理|识别|评价|评估))(?:方面)?(?:的)?'
        rf'(?P<action>考虑|评价|评估|判断|研究)',
        {'object': 'drug_object', 'population': 'use_population',
         'risk': 'drug_use_risk', 'action': 'risk_consideration'},
        'pharmacovigilance_risk', 'S：当前明确讨论药物用于特定人群时的风险控制考虑；不要求已有安全结论。')


def _capacity_constraints(text, out):
    # Shared heads in a coordinated fund/patient phrase are retained as two
    # distinct anchors, rather than equating fund affordability with F.
    base = (rf'(?P<guarantee>(?:用药|药品)保障(?:水平)?)'
            rf'(?:应当|应|须|需)?与(?P<capacity>{C}{{0,45}}'
            r'(?:承受能力|支付能力))(?P<relation>相适应|相匹配|匹配)')
    for match in re.finditer(base, _mask(text)):
        value = match.group('capacity')
        common = [_anchor(text, *match.span(name), role) for name, role in
                  [('guarantee', 'medicine_guarantee_level'), ('relation', 'capacity_constraint')]]
        fund = re.search(r'(?:基本医疗保险|医疗保险|医保)?基金', value)
        patient = re.search(r'(?:参保人(?:员)?|患者|病人)', value)
        ability = re.search(r'承受能力|支付能力', value)
        for dim, target, kind, subtype, basis in [
            ('Ec', fund, 'fund_capacity_constraint', 'budget_resource',
             'Ec：药品保障支付水平实质受到基金承受能力约束；并列患者能力另行留痕。'),
            ('F', patient, 'patient_capacity_linked_guarantee', 'patient_affordability',
             'F：用药保障水平明确联系参保人/患者承受或支付能力，非只有普通费用责任。')]:
            if target is None:
                continue
            offset = match.start('capacity')
            anchors = common + [_anchor(text, offset+target.start(), offset+target.end(),
                                       'fund_object' if dim == 'Ec' else 'patient_object'),
                                _anchor(text, offset+ability.start(), offset+ability.end(), 'capacity')]
            _emit(out, text, dim, kind, *match.span(), anchors, subtype, basis=basis)


def _innovation_attributes(text, out):
    _matched(out, text, 'I', 'comparative_novel_technology_definition',
        rf'(?P<target>首创新药(?:[（(][^）)]{{0,60}}[）)])?|药物|药品)'
        rf'(?:[，,]?\s*(?:即|是指|定义为))?(?P<relation>具有不同于)'
        rf'(?P<baseline>{C}{{1,60}}已上市(?:药品|药物))'
        r'的(?P<novel>新(?:作用)?机制(?:[/／、及和]新靶点)?|新靶点)(?:药物|药品)?',
        {'target': 'drug_definition_target', 'relation': 'novelty_comparison',
         'baseline': 'existing_drug_baseline', 'novel': 'novel_technology'},
        'attribute', 'I路径1：当前自足定义相对已上市药物的不同机制/靶点技术；不从普通机制名称推定。')
    _matched(out, text, 'I', 'actual_drug_innovation_comparison_requirement',
        rf'(?P<obligation>(?:申报|申请|评价)?材料(?:应当|应|须|需)(?:重点)?(?:突出|说明|展示|提供))'
        rf'{C}{{0,12}}(?P<target>药品|药物)与(?P<baseline>{C}{{1,35}}(?:药品|药物))'
        rf'在{C}{{0,55}}(?P<attribute>创新性){C}{{0,55}}方面的'
        r'(?P<comparison>比较优势|比较结果|评价结果)',
        {'obligation': 'current_content_requirement', 'target': 'current_drug',
         'baseline': 'comparison_drug', 'attribute': 'innovation_attribute',
         'comparison': 'substantive_comparison'},
        'attribute', 'I路径1：当前要求药品与参照/同类药品的创新属性比较内容；混合公平栏目另按F判据。')


def _review_time_support(text, out):
    _matched(out, text, 'I', 'innovative_rnd_review_time_arrangement',
        rf'(?P<target>{INNOVATIVE}(?:的)?临床试验申请)[，,]\s*'
        r'(?P<clock>在(?:受理|接受申请)后)'
        r'(?P<duration>[0-9一二两三四五六七八九十百]+(?:个)?(?:工作日|日|天))内'
        r'(?P<action>完成(?:技术)?(?:审评审批|审评|审批))',
        {'target': 'innovative_rnd_application', 'clock': 'review_start',
         'duration': 'actual_review_time', 'action': 'review_completion_arrangement'},
        'research_support', 'I路径3：明确创新研发申请实际获得审评完成时限安排；不以某时间阈值推定，不将行政效率赋E。')


def _direct_needs(text, out):
    _matched(out, text, 'F', 'reasonable_patient_drug_need_guarantee',
        rf'(?P<action>保障|确保|保证|满足)(?P<patient>参保人(?:员)?|患者|病人)'
        rf'(?:的)?(?P<need>(?:合理|必要|基本)(?:的)?(?:临床)?用药(?:需求|需要))',
        {'action': 'guarantee_action', 'patient': 'treatment_recipient', 'need': 'specified_drug_need'},
        'needs_based_guarantee', 'F：当前保障具体参保人/患者合理、必要或基本用药需要；不是普通需求口号。')
    _matched(out, text, 'F', 'basic_clinical_drug_supply_guarantee',
        r'(?P<action>保障|确保|保证)(?P<need>临床(?:基本|必需|急需)(?:的)?(?:用药|药品|药物))'
        r'(?:的)?(?P<supply>供应|配备|获取)',
        {'action': 'guarantee_action', 'need': 'specified_clinical_drug_need', 'supply': 'medicine_supply'},
        'needs_based_guarantee', 'F：具体临床基本/必需用药与当前供应保障相连；不从一般供药自动推定治疗需要。')


def _linked_needs(text, out):
    clauses = list(_segments(_mask(text)))
    # A directory guarantee gap is the condition of a remedy, rather than
    # an effect/innovation gap or an ordinary directory identity.
    gap = re.compile(r'(?:对于|针对|对)(?P<gap>(?:基本|医保|药品|用药)?目录保障(?:还|仍|尚)?(?:不充分|不足|有缺口|有空白))')
    remedy = re.compile(r'(?:着力)?(?P<action>弥补|填补|消除|解决)(?P<need>(?:临床)?用药(?:需求)?(?:短板|缺口|不足))')
    continuation = re.compile(r'(?:或者|或)有保障空白的领域|(?:如|例如).*用药.*(?:不限制|放宽|取消).*上市时间|(?:关注|考虑)(?:患者|病人|人群)(?:用药)?需求')
    for index, (start, end, value, stop) in enumerate(clauses):
        match = gap.search(value)
        if not match or stop not in ('，', ','):
            continue
        anchors = [_anchor(text, start+match.start('gap'), start+match.end('gap'), 'directory_guarantee_gap')]
        for a, b, following, following_stop in clauses[index+1:index+6]:
            target = remedy.fullmatch(following.strip())
            if target:
                shift = a + len(following)-len(following.lstrip())
                final = anchors + [_anchor(text, shift+target.start(name), shift+target.end(name), role)
                                   for name, role in [('action', 'gap_remedy'), ('need', 'specified_drug_need')]]
                _emit(out, text, 'F', 'directory_gap_linked_drug_need_remedy', start+match.start(), b,
                      final, 'needs_based_guarantee', basis='F：明确目录保障不足/空白条件与弥补临床用药需求短板的同一安排相连；非仅目录身份。')
                break
            if not continuation.fullmatch(following.strip()) or following_stop not in ('，', ','):
                break

    # Same-action continuations are bounded by top-level commas. Parenthetic
    # administrative names neither break a clause nor license another topic.
    need = re.compile(r'(?:注重|根据|依据|满足|保障)(?P<need>(?:上下)?转诊用药(?:需求|需要))')
    linkage = re.compile(r'(?:做好|保障|加强|完善)(?P<levels>.*(?:县|乡镇|村|社区|街道).*)用药(?:种类|品种)?(?P<action>衔接|连续供应|连续保障)')
    priority = re.compile(r'(?:注重|优先考虑|重点关注|优先保障)(?P<region>.*(?:医药资源|药品供应|医疗资源)(?:相对)?(?:薄弱|不足).*?(?:偏远|边远)地区)(?:和|及|与)(?P<need>.*用药(?:需求|需要).*)')
    down = re.compile(r'(?:推进|推动|加强)(?P<drug>药品(?:供应|配备))(?:和|及)?(?:服务)?(?P<action>下沉|覆盖|保障)')
    for index, (a, b, value, stop) in enumerate(clauses[:-1]):
        if stop not in ('，', ','):
            continue
        c, d, following, following_stop = clauses[index+1]
        left, right = need.fullmatch(value.strip()), linkage.fullmatch(following.strip())
        if left and right:
            aa = a+len(value)-len(value.lstrip()); cc = c+len(following)-len(following.lstrip())
            anchors = [_anchor(text, aa+left.start('need'), aa+left.end('need'), 'referral_drug_need'),
                       _anchor(text, cc+right.start('levels'), cc+right.end('levels'), 'care_levels'),
                       _anchor(text, cc+right.start('action'), cc+right.end('action'), 'medicine_continuity_action')]
            _emit(out, text, 'F', 'referral_need_linked_medicine_continuity', aa, d, anchors,
                  'needs_based_guarantee', basis='F：上下转诊用药需要明确支配不同基层层级的药品衔接安排；可及性或人群名称单独不够。')
        left, right = priority.fullmatch(value.strip()), down.fullmatch(following.strip())
        if left and right:
            aa = a+len(value)-len(value.lstrip()); cc = c+len(following)-len(following.lstrip())
            anchors = [_anchor(text, aa+left.start(name), aa+left.end(name), role) for name, role in
                       [('region', 'underserved_region'), ('need', 'specified_drug_need')]]
            anchors += [_anchor(text, cc+right.start(name), cc+right.end(name), role) for name, role in
                        [('drug', 'medicine_supply'), ('action', 'targeted_supply_action')]]
            _emit(out, text, 'F', 'underserved_region_need_linked_medicine_supply', aa, d, anchors,
                  'opportunity_barrier', basis='F：资源薄弱偏远地区/基层用药需要与药品供应下沉同一优先安排相连；一般服务或地区推广不足。')


def _guidance(record, text, out, result):
    # Current publication is itself the supply of a specific technical
    # resource. The named R&D object is not a safety evidence source.
    title_pattern = (r'(?P<actor>药审中心|药品审评中心|药品监管部门)(?:组织)?'
                     r'(?P<supply>起草|制定|编制)(?:了)?《(?P<title>[^》\n]{1,110})》')
    for match in re.finditer(title_pattern, text):
        title = match.group('title')
        if not (re.search(INNOVATIVE, title) and re.search(r'研发|临床试验|开发', title)
                and re.search(r'技术指导原则|技术指南|指导原则|试验设计要点|一般原则及考虑要点', title)):
            continue
        tail = text[match.end():]
        release = re.search(r'现(?:予|予以|正式)?(?:发布|印发)', tail)
        if not release or release.start() > 180 or re.search(r'[。；;]|另行|其他指南|另一本', tail[:release.start()]):
            continue
        from common_guideline_scope11 import authenticate_current_guideline_paragraph, GuidelineScopeUnavailable
        try:
            current = authenticate_current_guideline_paragraph(record)
        except GuidelineScopeUnavailable as error:
            _pending(result, error)
            continue
        start, end = match.start(), match.end()+release.end()
        anchors = [_anchor(text, *match.span(name), role) for name, role in
                   [('actor', 'actual_guideline_provider'), ('supply', 'actual_resource_creation'), ('title', 'innovative_rnd_guideline')]]
        anchors.append(_anchor(text, match.end()+release.start(), end, 'actual_resource_release'))
        _emit(out, text, 'I', 'actual_innovative_rnd_guideline_supply', start, end, anchors,
              'research_support', {'kind': 'COMMON11_actual_current_guideline_supply',
              'current_source_authentication': current, 'usage': 'Title identifies the resource supplied by the current creation/release predicates only.'},
              'I路径3：当前监管者实际起草并发布面向明确创新研发的技术指南；标题仅识别供给对象。')

    # Internal advice is not a supplied support opportunity. Authenticate
    # scope only after an independent resource/feedback/convenience predicate.
    from current_innovation_support import current_support_relations
    matches = current_support_relations(text)
    if not matches:
        return
    from common_guideline_scope11 import resolve_guideline_scope, GuidelineScopeUnavailable
    try:
        scope = resolve_guideline_scope(record)
    except GuidelineScopeUnavailable as error:
        _pending(result, error)
        return
    if scope is None:
        return
    for anchors in matches:
        start=min(x['start'] for x in anchors);end=max(x['end'] for x in anchors)
        _emit(out, text, 'I', 'authenticated_innovative_rnd_current_support_arrangement',
              start,end,anchors, 'research_support', scope,
              'I路径3：当前具体资源、方案反馈或研发便利安排与来源认证的创新研发对象相连；一般科学技术要求不构成支持。')


def _pending(result, error):
    issue = {'reason':str(error), 'details':getattr(error, 'details', {})}
    result.setdefault('common11_pending_dimensions', {}).setdefault('I', []).append(issue)
    result.setdefault('review_flags', []).append({'rule':'COMMON11_guideline_scope_unavailable',
        'dimensions':['I'], 'action':'unresolved_not_default_zero', **issue})


def revise(record, result):
    if result.get('judgement_status') == 'undetermined':
        return result
    owned={'COMMON11_I_authenticated_innovative_rnd_current_technical_guidance','COMMON11_I_authenticated_innovative_rnd_current_support_arrangement'}
    removed=[e for e in result.get('evidence',[]) if e.get('rule') in owned]
    result['evidence']=[e for e in result.get('evidence',[]) if e.get('rule') not in owned]
    result.setdefault('family_migration_trace',[]).append(dict(owner=VERSION,dimension='I',removed_rules=[e['rule'] for e in removed],retired_families=['ordinary_technical_advice_plus_innovation_guideline_scope']))
    text, out = record['unit_text'], []
    scoped = bool(result.get('drug_object_evidence') or result.get('drug_object_in_unit'))
    if scoped or re.search(DRUG, _mask(text)):
        _safety(text, out)
        _capacity_constraints(text, out)
        _innovation_attributes(text, out)
        _review_time_support(text, out)
        _direct_needs(text, out)
        _linked_needs(text, out)
        _guidance(record, text, out, result)
    seen = {(e['dimension'],e['start'],e['end'],e['rule']) for e in result.get('evidence', [])}
    for evidence in out:
        key = (evidence['dimension'],evidence['start'],evidence['end'],evidence['rule'])
        if key not in seen:
            result['evidence'].append(evidence)
            seen.add(key)
    result['common11_coverage_scope'] = 'bounded_current_relations_with_authenticated_guideline_object_not_exhaustive_semantics'
    return rebuild(result)

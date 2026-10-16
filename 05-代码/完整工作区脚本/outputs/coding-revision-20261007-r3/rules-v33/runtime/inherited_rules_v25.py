"""Post-validation rule development under unchanged CAL-5D v1.3.

This module is not validated by its development examples. It preserves the
candidate17 implementation as an auditable baseline and adds bounded semantic
relations. No rule may inspect an ID, department, filename or reference label.
"""
import copy
import hashlib
import re
import baseline_candidate17 as baseline
from context_validation import verified_following_list

VERSION = 'v25-development-3-bounded-review-fix'
DIMENSIONS = baseline.DIMENSIONS
DRUG = baseline.DRUG_OBJECT


def _texts(value):
    """Only text-bearing fields; never metadata, titles or filenames."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {'text', 'headers', 'row_cells'}:
                if isinstance(child, str):
                    yield child
                elif isinstance(child, list):
                    yield from (s for s in child if isinstance(s, str))
            elif isinstance(child, (dict, list)):
                yield from _texts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _texts(child)


def _without_titles(text):
    """Retain offsets while denying bare document titles as rule anchors."""
    return re.sub(r'《[^》]+》', lambda m: ' ' * len(m.group()), text)


def _part_at(text, start, end):
    """The immediate proposition, not every object anywhere in the unit."""
    left = max((text.rfind(c, 0, start) for c in '。；;，,'), default=-1) + 1
    stops = [text.find(c, end) for c in '。；;，,']
    right = min((p for p in stops if p >= 0), default=len(text))
    return _without_titles(text[left:right])


def _file_operation(part):
    """The current proposition acts on a carrier, not its evaluation content."""
    return bool(re.search(r'文件|文档|表格|情况表|报告表|文件格式', part)
                and re.search(r'归档|命名|改名|文件名|文件格式|格式[^。；;]*PDF|按编号', part))


def _attribute_relation(text, match):
    part = _part_at(text, match.start(), match.end())
    if _file_operation(part):
        return False
    # Only an explicit drug attribute relation is licensed here. A company,
    # platform or another sentence's drug noun is not a drug attribute.
    if match.group() == '创新程度':
        # A comma may enumerate two attributes of the very same drug noun.
        # Bind that exact noun/attribute phrase ending at this occurrence;
        # never recover an unrelated drug word from elsewhere in the unit.
        anchored = _without_titles(text[:match.end()])
        return bool(re.search(r'(?:药品|药物|新药)(?:的)?(?:产品特性[、,，]\s*)?创新程度$', anchored))
    return bool(re.search(r'(?:药品|药物|新药)(?:的)?(?:靶点|作用机制|化合物|分子实体)(?:的)?新颖性', part))


def _incentive_relation(value):
    value = _without_titles(value)
    obj = re.search(r'原研药|改良型(?:新药|药品)|创新药', value)
    if not obj or _file_operation(value):
        return False
    action = re.search(r'给予|享有|保护期(?:为|延长)|延长[^，,]*保护', value[obj.end():])
    if not action or not re.search(r'数据保护期|市场独占期', value[obj.end():]):
        return False
    # An explicitly different beneficiary/data object breaks the relation.
    if re.search(r'软件|数据库|信息平台|文件副本', value[obj.end():]):
        return False
    # Bare trading/administrative mention is not the protected object.
    if re.search(r'(?:经营|登记|会议介绍)[^，,]*$', value[:obj.start()]):
        return False
    return True


def _condition_text(text):
    """A bounded condition-item grammar; unknown following prose stays unresolved."""
    text = baseline.matching_view(text)[0].strip()
    marker = r'(?:[（(][一二三四五六七八九十0-9]+[）)]|[一二三四五六七八九十0-9]+[、.．])?'
    return bool(re.match(marker + r'\s*(?:具有|填补|用于|属于|能够|已证明|已经证明|符合|满足)', text))


def _missing_required_list(record, text):
    """Require linked condition content, never an arbitrary nonempty parent."""
    if not re.search(r'(?:满足|符合)(?:以下|下列)(?:条件|要求)(?:之一)?\s*[:：]$', text):
        return False
    target_hash = hashlib.sha256(record['unit_text'].encode()).hexdigest()
    sources = {record.get('unit_source_sha256') or record.get('source_sha256')} - {None}
    for item in record.get('verified_supplemental_context', []):
        if item.get('kind') != 'same_article_following_list' or item.get('original_unit_sha256') != target_hash:
            continue
        contexts = item.get('contexts', [])
        if (contexts and all(c.get('source_sha256') in sources and c.get('pages')
                             and c.get('verification') for c in contexts)
                and any(_condition_text(t) for t in _texts(contexts))):
            return False
    # Explicit list fields must bind the target and source too. A field name
    # alone is not proof that this is the missing list for this unit.
    for context in record.get('verified_list_context', []):
        if (context.get('original_unit_sha256') == target_hash
                and context.get('source_sha256') in sources
                and context.get('verification')
                and any(_condition_text(t) for t in _texts(context))):
            return False
    for context in record.get('paragraph_context', []):
        whole = baseline.matching_view(context['text'])[0]
        if whole.count(text) == 1 and _condition_text(whole.split(text, 1)[1]):
            return False
    return True


def code_unit(record):
    original = record.get('unit_text')
    # Baseline performs frozen input, scope-hash and source-binding checks.
    result = copy.deepcopy(baseline.code_unit(record))
    result['version'] = VERSION
    result['baseline_version'] = baseline.VERSION
    result['status'] = 'post_validation_development_not_independently_validated'
    result['semantic_protocol'] = 'CAL-5D-20260926-v1.3'
    result['review_flags'] = []
    if result['judgement_status'] == 'undetermined':
        return result
    text, offsets = baseline.matching_view(original)
    if _missing_required_list(record, text) and not verified_following_list(record):
        # The unchanged manual requires whole-unit pending for this real gap.
        result.update(labels={d: None for d in DIMENSIONS}, judgement_status='undetermined',
                      input_assessment_status='context_insufficient',
                      issue_reason='explicit_required_eligibility_list_not_verified_as_complete',
                      evidence=[], fairness_subtypes=[], safety_subtypes=[],
                      innovation_subtypes=[], innovation_subtype_status='undetermined',
                      innovation_unclassified_evidence=[])
        return result

    def raw_span(start, end):
        return offsets[start][0], offsets[end-1][1]

    def add(rule, dim, match, subtype=None, dependency=None):
        start, end = raw_span(match.start(), match.end())
        evidence = {'rule': rule, 'dimension': dim, 'start': start, 'end': end,
                    'text': original[start:end], 'matching_text': match.group(),
                    'subtype': subtype, 'protocol_basis': 'CAL-5D-20260926-v1.3'}
        if dependency:
            evidence['context_dependency'] = dependency
        result['evidence'].append(evidence)

    def unresolved(rule, reason):
        # This is a skipped new-rule inference, not a fabricated positive or
        # whole-unit abstention. Downstream users must retain this limitation.
        result['review_flags'].append({'rule': rule, 'reason': reason,
            'action': 'new_positive_not_added_without_bound_relation'})

    def suppress(rule, dim, start, end):
        a, b = raw_span(start, end)
        dropped = [e for e in result['evidence']
                   if e['dimension'] == dim and a <= e['start'] and e['end'] <= b]
        result['evidence'] = [e for e in result['evidence'] if e not in dropped]
        for entry in dropped:
            result['suppressions'].append({'rule': rule, 'dimensions': [dim],
                'start': entry['start'], 'end': entry['end'], 'text': entry['text'],
                'suppressed_rule': entry['rule']})

    def paragraphs_containing_current():
        for p in record.get('paragraph_context', []):
            whole = baseline.matching_view(p['text'])[0]
            # Ambiguous repeated occurrences cannot license a coreference link.
            if whole.count(text) == 1:
                yield p, whole, whole.index(text)

    def dependency(p, kind, antecedent):
        return {'kind': kind, 'paragraph_id': p.get('paragraph_id'),
                'source_sha256': record.get('unit_source_sha256') or record.get('source_sha256'),
                'paragraph_sha256': hashlib.sha256(p['text'].encode()).hexdigest(),
                'antecedent_text': antecedent, 'pages': p.get('pages', [])}

    drug_in_unit = bool(DRUG.search(text))
    scoped_drug = bool(result.get('drug_object_evidence'))

    # Attribute wording is a substantive classification criterion, unlike a
    # bare innovation-drug name or an agency's institutional innovation.
    if drug_in_unit:
        for m in re.finditer(r'创新程度|(?:靶点|作用机制|化合物|分子实体)(?:的)?新颖性', text):
            if not _attribute_relation(text, m):
                unresolved('V25_I_attribute_criterion', 'drug_attribute_relation_not_established_or_file_operation')
                continue
            add('V25_I_attribute_criterion', 'I', m, 'attribute')

    if drug_in_unit or scoped_drug:
        for m in re.finditer(r'(?:改良|改善|优化)(?:药物|药品|制剂|片剂|胶囊)(?:的)?(?:结构|特征|易碎性|释放特征|释放行为)', text):
            add('V25_I_specific_product_modification', 'I', m, 'attribute')
        for m in re.finditer(r'(?:支持|鼓励|促进|推动)(?:新药|创新药)(?:和|与|及|、)(?:创新)?医疗器械(?:的)?(?:研发|研制)', text):
            add('V25_I_coordinated_drug_device_research', 'I', m, 'research_support')
        for clause in re.finditer(r'[^。；;]+', text):
            value = _without_titles(clause.group())
            if (DRUG.search(value) and '原创性成果' in value
                    and re.search(r'(?:加快|支持|鼓励|促进)[^。；;]*专利(?:布局|保护|转化)', value)):
                if re.search(r'(?:药品|药物|新药)(?:(?:[、和与及]|以及)*(?:创新)?医疗器械)?(?:的)?原创性成果', value):
                    add('V25_I_original_drug_patent_support', 'I', clause, 'research_support')
                else:
                    unresolved('V25_I_original_drug_patent_support', 'patent_support_object_not_bound_to_drug_result')

        # Explicitly absent effective treatment is a named access gap; disease
        # names, low response alone and research participation remain excluded.
        for m in re.finditer(r'(?:缺乏|缺少|没有|尚无)有效(?:的)?(?:治疗|防治)(?:措施|手段|药物)', text):
            add('V25_F_explicit_unmet_treatment', 'F', m, 'access')
        for m in re.finditer(r'(?:部分|有些|一些)?患者(?:仍)?未能(?:得到|获得)有效治疗', text):
            add('V25_F_explicit_patient_treatment_gap', 'F', m, 'access')
        for m in re.finditer(r'(?:打开药品包装|量取(?:及使用)?药物|使用药物)[^。；;]*?(?:遇到困难|存在困难|难以完成)', text):
            add('V25_F_explicit_drug_use_management_obstacle', 'F', m, 'clinical_management')

    # Qualification can be established in the current unit itself. Both the
    # innovation population and its comparative eligibility requirement are
    # necessary; cross-program borrowing does not transfer this subtype.
    if (re.search(r'创新药或者改良型新药|创新药或改良型新药|创新药和改良型新药', text)
            and re.search(r'申请(?:适用|纳入)突破性治疗药物程序', text)
            and not re.search(r'优先审评|参照[^。]*突破性治疗', text)):
        for m in re.finditer(r'(?:与现有治疗手段相比[^。；;]*?)?明显临床优势|尚无有效(?:防治|治疗)手段', text):
            add('V25_I_current_unit_qualification_anchors', 'I', m, 'qualification_advantage')

    # Join object, policy action and incentive within one sentence; do not use
    # an arbitrary 35-character window that drops intervening conditions.
    for clause in re.finditer(r'[^。；;]+', text):
        value = _without_titles(clause.group())
        if (re.search(r'原研药|改良型(?:新药|药品)|创新药', value)
                and re.search(r'给予|享有|保护期(?:为|延长)|延长[^，,]*保护', value)
                and re.search(r'数据保护期|市场独占期', value)
                and not re.search(r'会议|归档|文件编号', value)):
            if _incentive_relation(value):
                add('V25_I_innovation_incentive_relation', 'I', clause, 'research_support')
            else:
                unresolved('V25_I_innovation_incentive_relation', 'protection_beneficiary_not_bound_to_innovation_drug')

    if drug_in_unit:
        # Reporting actual stocking/supply status is substantive access
        # information; mere archive/search instructions do not qualify.
        for clause in re.finditer(r'[^。；;，,]+', text):
            value = _without_titles(clause.group())
            if (re.search(r'药品配备(?:使用)?(?:情况|状况|信息|数据)', value)
                    and re.search(r'维护|更新|报送|报备|采集|收集|报告|监测|分析|评估|掌握|了解', value)
                    and not re.search(r'仅(?:归档|查询)|按(?:编号|日期)归档|仅更新[^，,]*文件名', value)):
                if not _file_operation(value):
                    add('V25_F_stocking_information_requirement', 'F', clause, 'access')
                else:
                    unresolved('V25_F_stocking_information_requirement', 'stocking_document_carrier_operation_only')
            if (re.search(r'(?:未|没有|停止|中断)[^，,]*供应', value)
                    and re.search(r'医保定点|医疗机构|医药机构|零售药店|患者', value)
                    and DRUG.search(value)
                    and not re.search(r'办公|试验用药|研究用药', value)):
                add('V25_F_treatment_supply_status', 'F', clause, 'access')

    # A current anaphoric obligation can inherit only the referenced access
    # obligation, with an exact same-paragraph antecedent recorded.
    for m in re.finditer(r'(?:相应|上述)(?:要求|义务)[^。；;]*(?:协议|约定)[^。；;]*(?:明确|落实|约定)', text):
        for p, whole, pos in paragraphs_containing_current():
            prefix = whole[:pos]
            preceding = [s.strip() for s in re.findall(r'[^。]+', prefix) if s.strip()][-2:]
            if not preceding:
                continue
            antecedent = preceding[-1]
            # One explicit elaboration may continue the preceding obligation;
            # a new subject or financial-audit topic is not such a bridge.
            if (len(preceding) == 2 and re.match(r'包括|其中|具体包括|并', antecedent)
                    and not re.search(r'财务审计|仅规定|另行|其他事项', antecedent)):
                antecedent = '。'.join(preceding)
            if (re.search(r'保障[^。]*药品供应|药品[^。]*保障供应', antecedent)
                    and not re.search(r'另行|其他事项|财务审计', text)):
                add('V25_F_explicit_obligation_reference', 'F', m, 'access',
                    dependency(p, 'same_paragraph_explicit_obligation', antecedent))
                break

    for m in re.finditer(r'(?:根据|为满足)评价需要[^。；;]*药品生产[、,，]?供应(?:相关)?信息', text):
        for p, whole, pos in paragraphs_containing_current():
            antecedent = whole[:pos]
            if re.search(r'可获得性[^。]*药品配备|药物可及性[^。]*可获得性', antecedent):
                add('V25_F_access_evaluation_information', 'F', m, 'access',
                    dependency(p, 'same_paragraph_access_evaluation', antecedent))
                break

    # Standard adverse-event abbreviations require a drug object or a supplied,
    # baseline-validated safety-dossier scope. A filename is never sufficient.
    safety_scopes = [s for s in record.get('verified_object_scope', [])
                     if s['kind'] == 'anticancer_drug_safety_dossier']
    if drug_in_unit or safety_scopes or scoped_drug:
        for m in re.finditer(r'(?<![A-Za-z])(?:SAE|SUSAR|ADR|AE)(?![A-Za-z])', text):
            if not re.search(r'发生率|发生情况|分级|严重|致死|停药|减量|不良|安全|报告', text):
                continue
            part = _part_at(text, m.start(), m.end())
            if (_file_operation(part) or re.search(r'数据库|软件|信息平台', part)
                    or not (DRUG.search(part) or safety_scopes)):
                unresolved('V25_S_adverse_event_abbreviation', 'local_drug_event_relation_not_established_or_file_operation')
                continue
            dep = None
            if not drug_in_unit and not scoped_drug and safety_scopes:
                s = safety_scopes[0]
                dep = {'kind': 'verified_drug_safety_scope', 'source_sha256': s['source_sha256'],
                       'scope_text_sha256': s['text_sha256'], 'scope_text': s['text'],
                       'locator': s['locator']}
            add('V25_S_adverse_event_abbreviation', 'S', m, dependency=dep)

    if drug_in_unit:
        for m in re.finditer(r'(?:最小|最低)?有效(?:剂量|疗程)|药效学', text):
            add('V25_E_drug_effect_endpoint', 'E', m)
        for m in re.finditer(r'安全[、,，]有效[、,，]经济(?:[、,，]适宜)?用药', text):
            for dim in ['S', 'E', 'Ec']:
                add('V25_multidimension_use_requirement', dim, m)

    # Exclusions operate on evidence spans, never on the entire mixed unit.
    # Independent genuine evidence in another clause remains intact.
    for m in re.finditer(r'《[^》]+》', text):
        for dim in DIMENSIONS:
            suppress('V25_document_title_not_dimension_evidence', dim, m.start(), m.end())
    for m in re.finditer(r'(?:质量管理|管理体系|工作流程|信息系统)(?:活动|工作|措施|体系)?(?:的)?有效性', text):
        suppress('V25_E_non_drug_effect_object', 'E', m.start(), m.end())
    for clause in re.finditer(r'[^。；;]+', text):
        value = clause.group()
        if (re.search(r'质量管理活动|数据质量|质量体系', value)
                and not re.search(r'不良反应|药物损害|毒性|用药错误|受试者安全|患者安全|药品质量风险', value)):
            for m in re.finditer(r'风险控制|风险管理', value):
                suppress('V25_S_quality_process_not_drug_harm', 'S',
                         clause.start()+m.start(), clause.start()+m.end())
        if re.search(r'药品注册|注册申请|注册审评审批', value):
            for m in re.finditer(r'申请人[^，,。；;]*?(?:缴纳|缴付|交纳)[^，,。；;]*?费用', value):
                suppress('V25_Ec_registration_administrative_fee', 'Ec',
                         clause.start()+m.start(), clause.start()+m.end())
        if (re.search(r'协同衔接|制度衔接', value)
                and not re.search(r'评价[^，,。；;]*(?:疗效是否|临床获益)|提交[^，,。；;]*疗效数据', value)):
            for m in re.finditer(r'仿制药质量(?:与|和)疗效一致性评价', value):
                suppress('V25_E_named_system_coordination', 'E',
                         clause.start()+m.start(), clause.start()+m.end())

    result['labels'] = {d: int(any(e['dimension'] == d for e in result['evidence'])) for d in DIMENSIONS}
    result['innovation_subtypes'] = sorted({e['subtype'] for e in result['evidence'] if e['dimension']=='I' and e.get('subtype')})
    result['innovation_unclassified_evidence'] = [e for e in result['evidence'] if e['dimension']=='I' and not e.get('subtype')]
    result['innovation_subtype_status'] = ('needs_review' if result['innovation_unclassified_evidence']
                                         else 'complete' if result['labels']['I'] else 'not_applicable')
    result['fairness_subtypes'] = sorted({e['subtype'] for e in result['evidence'] if e['dimension']=='F' and e.get('subtype')})
    result['safety_subtypes'] = sorted({e.get('safety_basis', 'quality_safety' if e['rule']=='S07' else 'other_safety')
                                      for e in result['evidence'] if e['dimension']=='S'})
    # An explicit unresolved object is flagged for source review without
    # manufacturing a positive label or declaring all nonmatches pending.
    if not scoped_drug and not drug_in_unit and re.search(r'获益[-—－]?风险评估|安全性风险', text):
        result['review_flags'].append({'reason': 'substantive_dimension_signal_without_resolved_drug_object',
                                       'action': 'verify_source_scope_before_releasing_as_negative'})
    return result

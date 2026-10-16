"""Traceable rule-based prototype, NOT a frozen or validated coding method.

Runs on complete, previously reconstructed units. Does not clean/split text,
alter source records, infer labels from filenames, or aggregate departments.
Rule spans refer to original unit offsets; surrounding text only establishes
the drug-related object, never supplies a missing dimension trigger.
"""
import hashlib
import re
import unicodedata

VERSION = 'v4-development-23'
DIMENSIONS = ('S', 'E', 'Ec', 'I', 'F')
DRUG_OBJECT = re.compile(r'药品|药物|用药|药学|药效|药剂|新药|处方|药代')

# Generic clinical/cost words require a drug-related unit or paragraph.
# These are research operational rules, not verbatim official definitions.
RULES = [
    ('S01', 'S', r'安全性|药品安全|用药安全|药物警戒|药物相互作用|不良反应|不良事件|毒性|禁忌|副作用|安全信号', True, None),
    ('S02', 'S', r'获益.{0,4}风险|风险.{0,4}获益|风险控制|风险管理|风险最小化|安全监测|潜在治疗风险|药物已识别风险', True, None),
    ('S03', 'S', r'药物相关.{0,35}风险|风险.{0,15}用药.{0,20}因果关系', False, None),
    ('S04', 'S', r'安全、有效、经济(?:、适宜)?的合理用药原则', False, None),
    ('S05', 'S', r'药物(?:与|和)[^。;；]{1,30}相互作用|(?:药物之间|药物间)[^。;；]{0,20}相互作用', True, None),
    ('S07', 'S', r'(?:药品|药物)(?:(?:支付|供应|使用)保障(?:和|与|及))?质量(?:安全|风险)', False, None),
    ('S06', 'S', r'临床必需[、,，]安全有效|(?:药品|药物|用药)(?:的)?安全有效(?!期)', True, None),
    ('E05', 'E', r'临床必需[、,，]安全有效|(?:药品|药物|用药)(?:的)?安全有效(?!期)', True, None),
    ('E01', 'E', r'有效性|疗效|临床价值|临床获益|治疗效果|临床效果|临床优势|治疗价值|无进展生存|客观缓解|疾病控制率|生存率|生存期|生命质量|健康效用|QALY', True, None),
    ('E02', 'E', r'安全、有效、经济(?:、适宜)?的合理用药原则', False, None),
    ('E03', 'E', r'(?:药品|药物|用药).{0,18}(?:指南推荐|诊疗规范推荐)', False, None),
    ('E04', 'E', r'有效(?:治疗|防治)(?:药物|手段)', True, None),
    ('Ec01', 'Ec', r'价格|费用|成本|支付标准|报销|医保基金|基金支出|基金承受|基金可持续|预算影响|基金支付能力|销售金额|使用金额|销量|药物经济|经济性|定价|降价|降幅', True, None),
    ('Ec02', 'Ec', r'安全、有效、经济(?:、适宜)?的合理用药原则', False, None),
    ('Ec03', 'Ec', r'(?:药品|药物)(?:的)?交易量|(?:医保信息平台|药品交易平台)[^。;；]{0,8}交易量', True, None),
    ('I01', 'I', r'创新性|创新点|自主知识产权|原始创新|新靶点|新作用机制|新化合物|新分子实体|注册分类|改良型新药|中成药.{0,8}传承性', True, None),
    ('I05', 'I', r'是否为[^。;；]{0,12}重大新药创制[^。;；]{0,20}(?:专项|支持)', True, 'attribute'),
    ('I06', 'I', r'(?:开发|提供|建设)[^。;；]{0,12}创新药研发[^。;；]{0,12}数据(?:产品|服务)[^。;；]{0,30}支持', True, 'research_support'),
    ('I02', 'I', r'(?:支持|鼓励|促进|激励|推动|加快).{0,10}(?:创新药研发|创新药物研发|新药研发)', False, None),
    ('I03', 'I', r'为创新药(?:物)?研发提供[^。;；]{0,20}(?:数据服务|投资|资金|支持)|创新药(?:物)?研发[^。;；]{0,10}科研攻关|创新药(?:物)?研发(?:鼓励|支持|专项)', False, None),
    ('Ec04', 'Ec', r'(?:商业健康保险|医疗互助)[^。;；]{0,35}(?:药品|创新药|药物)[^。;；]{0,8}纳入保障范围|慈善捐赠[^。;；]{0,25}支持困难群众[^。;；]{0,12}(?:用药|使用[^。;；]{0,6}药)', True, None),
    ('F10', 'F', r'公平性(?:信息|资料|证据)|公平性[^。;；]{0,25}(?:比较优势|综合研判|评价|评估)|(?:评价|评估|比较)[^。;；]{0,25}公平性', True, 'dimension_information'),
    ('F11', 'F', r'(?:收集|报告|监测)[^。;；]{0,35}药品配备[^。;；]{0,45}(?:供应|配送)[^。;；]{0,12}信息', True, 'access'),
    ('F12', 'F', r'(?:医药机构|医疗机构|药店)[^。;；]{0,35}送药上门', False, 'access'),
    ('F13', 'F', r'(?:将|把)[^。;；]{0,40}药品[^。;；]{0,25}纳入医保支付范围', True, 'access'),
    ('F08', 'F', r'(?:扩大|扩展|拓展|拓宽)[^。;；]{0,15}(?:药品|药物|创新药|用药)(?:的)?(?:支付|保障|报销)范围', True, 'access'),
    ('F09', 'F', r'(?:用药|药品(?:配备|使用)?)[^。;；]{0,12}(?:不受|不再受)[^。;；]{0,12}(?:一品两规|药占比)[^。;；]{0,6}(?:限定|限制|约束)', True, 'access'),
    ('F07', 'F', r'(?:提交|提供|补充|报送|申报材料|申报内容)[^。；;]{0,100}公平性(?:信息|资料|证据)', True, 'dimension_information'),
    ('F01', 'F', r'药品目录短板|保障空白|保障尚不充分|用药需求短板|用药保障需求|用药保障机制|药品保障机制|短缺|供应保障|断供|可及性|可及', True, 'access'),
    ('F02', 'F', r'可负担|患者.{0,8}(?:经济负担|费用负担|支付负担)|减轻.{0,8}(?:用药负担|药费负担)', True, 'affordability'),
    ('F03', 'F', r'临床管理难度', True, 'clinical_management'),
    ('F04', 'F', r'未(?:被)?满足的?(?:用药|治疗)需求|尚无有效(?:治疗|防治)药物|满足[^。;；]{0,18}(?:急迫|迫切)[^。;；]{0,8}(?:用药|治疗)需求|不得以[^。;；]{0,30}(?:影响|限制)[^。;；]{0,12}(?:配备|用药)|(?:将|把)[^。;；]{0,16}药[^。;；]{0,8}纳入保障范围', True, 'access'),
    ('F05', 'F', r'慈善捐赠[^。;；]{0,25}困难群众[^。;；]{0,12}(?:用药|药)', True, 'affordability'),
    ('F06', 'F', r'(?:药品|药物|用药)(?:的)?可获得性?|可获得(?:的)?(?:药品|药物|治疗药物)', True, 'access'),
]

# Mask only the mismatched phrase. A genuine second claim in the same unit
# must survive (e.g. data accessibility AND patient drug accessibility).
MASKS = [
    ('cross_word_cost', ('Ec',), r'形成本(?:机构|单位|部门|地区|年度)'),
    ('economic_disclosure_only', ('Ec',), r'除经济性以外|不含经济性信息'),
    ('work_character_innovation', ('I',), r'创新性[、,，]系统性工作'),
    ('safety_institution_name_only', ('S',), r'药物非临床安全性评价研究机构'),
    ('non_drug_use_amount', ('Ec',), r'(?:设备|耗材|器械|办公用品|科研经费|项目经费|资金)(?:的)?使用金额'),
    ('expert_specialty_only', ('Ec',), r'药物经济学(?=[、,，](?:[^。;；、,，]{1,10}[、,，])*[^。;；、,，]{0,15}专家)'),
    ('non_drug_safety', ('S',), r'数据安全|生产安全|安全生产|网络安全|信息安全|食品安全|安全感'),
    ('non_efficacy_validity', ('E',), r'有效期|有效账号|有效身份'),
    ('administrative_fee', ('Ec',), r'不收取任何费用|行政申报收费'),
    ('institutional_innovation', ('I',), r'创新型国家|创新驱动发展|产业创新发展|新质生产力|制度创新|管理创新'),
    ('research_delivery', ('F',), r'(?:临床试验|研究项目)[^。;；]{0,40}送药上门'),
    ('competition', ('F',), r'公平竞争'),
    ('data_accessibility', ('F',), r'(?:可获得|可及)(?:的)?(?:数据|证据|文献|模型参数)'),
    ('slide_format_only', ('Ec',), r'不含经济性/价格费用信息'),
    ('adverse_effect_misattributed_as_efficacy', ('E',), r'(?:把|将)[^。;；()（）]{0,20}(?:不适|不良反应)[^。;；()（）]{0,12}(?:看作|误认为|当作)(?:是)?疗效(?:的一部分)?'),
]



def matching_view(raw):
    """Compatibility glyphs and spaces between CJK characters only.

    Keep offsets into the exact supplied original, including whitespace inside
    a matched phrase. Do not reconstruct missing characters or missing context.
    """
    chars=[]; offsets=[]
    for index,char in enumerate(raw):
        for normalized in unicodedata.normalize('NFKC',char):
            chars.append(normalized);offsets.append((index,index+1))
    joined=''.join(chars)
    remove=set()
    for match in re.finditer(r'(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])',joined):
        remove.update(range(match.start(),match.end()))
    return ''.join(c for i,c in enumerate(chars) if i not in remove), [v for i,v in enumerate(offsets) if i not in remove]


def code_unit(record):
    text = record.get('unit_text')
    # A source reviewer supplies this assessment; regex non-matches cannot
    # establish completeness. Missing assessments remain explicitly uncertified.
    assessment = record.get('input_assessment', {'status': 'not_assessed'})
    assert isinstance(assessment, dict), 'Invalid input assessment'
    assessment_status = assessment.get('status')
    assert assessment_status in {'sufficient', 'not_assessed', 'text_problem', 'context_insufficient'}, 'Unknown input assessment'
    if text is not None:
        assert isinstance(text, str), 'Invalid unit text type'
    missing_text = text is None or not text.strip()
    unresolved = missing_text or assessment_status in {'text_problem', 'context_insufficient'}
    if unresolved:
        reason = 'missing_unit_text' if missing_text else assessment.get('reason')
        assert isinstance(reason, str) and reason.strip(), 'Unresolved input requires a reason'
        return dict(version=VERSION, status='development_output_not_validated',
                    judgement_status='undetermined', input_assessment_status=assessment_status,
                    issue_reason=reason, labels={dim: None for dim in DIMENSIONS},
                    unit_text_sha256=hashlib.sha256(text.encode()).hexdigest() if text is not None else None,
                    fairness_subtypes=[], safety_subtypes=[], innovation_subtypes=[],
                    innovation_subtype_status='undetermined', innovation_unclassified_evidence=[], evidence=[], suppressions=[],
                    drug_object_evidence=None, drug_object_in_unit=None)
    if assessment_status == 'sufficient':
        assert isinstance(assessment.get('basis'), str) and assessment['basis'].strip(), 'Sufficient input requires review basis'
    contexts = record.get('paragraph_context', [])
    # The caller supplies source-verified paragraph membership. No arbitrary
    # neighbouring heading or previous paragraph is used for semantic scope.
    parents = record.get('verified_parent_context', [])
    # Source-verified table captions/columns establish the drug object only.
    # Dimension triggers still have to occur in the row, never in a header.
    tables = record.get('verified_table_context', [])
    table_object_context = []
    if tables:
        assert record.get('unit_type') == 'example_table_row', 'Unsupported table context'
        for table in tables:
            assert len(table['headers']) == len(table['row_cells']), 'Table column mismatch'
            assert text == ' | '.join(table['row_cells']), 'Table context/row mismatch'
            table_object_context.extend([table.get('caption') or '', *table['headers']])
    supplements = record.get('verified_supplemental_context', [])
    for item in supplements:
        assert item['kind'] in {'same_source_ratio_definition','official_figure_prompt','same_article_following_list'}, 'Unknown supplemental context'
        assert item['original_unit_sha256'] == hashlib.sha256(text.encode()).hexdigest(), 'Stale supplemental context'
        assert item['contexts'] and all(c.get('source_sha256') and c.get('pages') and c.get('verification') for c in item['contexts']), 'Unverified supplemental context'
    # Figure headings and following-list text are visible source structure, not
    # automatic dimension evidence. Ratio definitions resolve only an explicit
    # ratio reference in the current unit; other parent content is never copied.
    original_text = text
    text, original_offsets = matching_view(original_text)
    object_text = matching_view('\n'.join([original_text] + [p['text'] for p in contexts + parents] + table_object_context))[0]
    object_match = DRUG_OBJECT.search(object_text)
    masked = {d: text for d in DIMENSIONS}
    suppressions = []
    for name, dims, pattern in MASKS:
        if name == 'economic_disclosure_only' and not re.search(r'公示|公开', text):
            continue
        if name == 'slide_format_only' and not re.search(r'幻灯片|PPT|命名为', text):
            continue
        for match in re.finditer(pattern, text):
            for dim in dims:
                value = masked[dim]
                masked[dim] = value[:match.start()] + ' ' * (match.end() - match.start()) + value[match.end():]
            suppressions.append(dict(rule=name, dimensions=list(dims), start=match.start(), end=match.end(), text=match.group()))
    # Dimension names in a purely administrative publication clause are not
    # substantive evaluation requirements. Split coordinated clauses so an
    # additional assessment requirement keeps its original evidence spans.
    names = {'安全性':'S', '有效性':'E', '经济性':'Ec', '创新性':'I', '公平性':'F'}
    for clause in re.finditer(r'[^。；;]+', text):
        for part in re.finditer(r'(?:(?!并|同时|且).)+', clause.group()):
            phrase = part.group()
            if not re.search(r'进行公示|予以公示|公示(?:药品|药物|申报资料|申报内容)|公示的申报内容|将在[^。；;]{0,15}公示', phrase):
                continue
            if re.search(r'评价|评估|比较|补充|测算|分析|判断|应提交|须提交|需提交', phrase):
                continue
            for m in re.finditer('|'.join(names), phrase):
                dim=names[m.group()]
                start=clause.start()+part.start()+m.start();end=start+len(m.group())
                masked[dim]=masked[dim][:start]+' '*(end-start)+masked[dim][end:]
                suppressions.append(dict(rule='dimension_disclosure_only', dimensions=[dim], start=start,end=end,text=text[start:end]))
    evidence = []
    for rule, dim, pattern, needs_drug, subtype in RULES:
        if needs_drug and not object_match:
            continue
        for match in re.finditer(pattern, masked[dim]):
                evidence.append(dict(rule=rule, dimension=dim, start=match.start(), end=match.end(),
                                 text=text[match.start():match.end()], subtype=subtype))
    for item in supplements:
        if item['kind'] != 'same_source_ratio_definition':
            continue
        for ctx in item['contexts']:
            definition = matching_view(ctx['text'])[0]
            for match in re.finditer(r'比值\s*([AB])', text):
                if re.search(r'比值\s*'+match.group(1), definition) and re.search(r'药品费用|基金(?:实际)?支出', definition) and '预算' in definition:
                    evidence.append(dict(rule='Ec05', dimension='Ec', start=match.start(), end=match.end(), text=match.group(), subtype=None,
                                         context_dependency=dict(kind=item['kind'],paragraph_id=ctx['paragraph_id'],source_sha256=ctx['source_sha256'],pages=ctx['pages'])))
    # A verified governing clause is necessary: a nearby title alone is not
    # evidence that a comparative claim defines innovation qualification.
    parent_text = matching_view('\n'.join(p['text'] for p in parents))[0]
    if re.search(r'突破性治疗药物程序', parent_text) and re.search(r'满足.{0,8}条件|终止', parent_text):
        qualification_pattern = r'明显临床优势'
        if '明显临床优势' in parent_text and '具体包括以下任一情形' in parent_text:
            qualification_pattern += r'|疗效|治疗效果|临床获益|安全性优势|显著改善|临床结局'
        for match in re.finditer(qualification_pattern, text):
            evidence.append(dict(rule='I04', dimension='I', start=match.start(), end=match.end(),
                                 text=match.group(), subtype=None,
                                 governing_paragraph_ids=[p['paragraph_id'] for p in parents]))
    # Innovation subtypes are traceability fields, not extra dimensions.
    # A bare R&D token does not by itself establish an incentive/support clause.
    support_spans=[e for e in evidence if e['rule'] in {'I02','I03','I06'}]
    for e in evidence:
        if e['dimension'] != 'I':
            continue
        if e['rule'] in {'I02','I03','I06'}:
            e['subtype']='research_support'
        elif e['rule']=='I05':
            e['subtype']='attribute'
        elif e['rule']=='I04':
            e['subtype']='qualification_advantage'
        elif e['rule']=='I01':
            if e['text'] not in {'新药研发','重大新药创制','自主研发'}:
                e['subtype']='attribute'
            elif any(x['start']<=e['start'] and e['end']<=x['end'] for x in support_spans):
                e['subtype']='research_support'
            else:
                e['subtype']=None
                e['subtype_review_reason']='研发词命中，尚无已识别的属性判定或明确研发支持依据；需回查，不能猜测子类型。'
    # Restore all evidence/suppression spans before exposing the result.
    for entry in evidence + suppressions:
        start,end=entry['start'],entry['end']
        entry['matching_text']=entry['text']
        entry['start']=original_offsets[start][0]
        entry['end']=original_offsets[end-1][1]
        entry['text']=original_text[entry['start']:entry['end']]
    labels = {dim: int(any(e['dimension'] == dim for e in evidence)) for dim in DIMENSIONS}
    return dict(version=VERSION, status='development_output_not_validated',
                judgement_status='rule_prediction', input_assessment_status=assessment_status,
                available_supplemental_context_kinds=sorted({x['kind'] for x in supplements}),
                unit_text_sha256=hashlib.sha256(original_text.encode()).hexdigest(), labels=labels,
                matching_normalization='NFKC_per_character_and_CJK_internal_whitespace',
                innovation_subtypes=sorted({e['subtype'] for e in evidence if e['dimension']=='I' and e['subtype']}),
                innovation_subtype_status=('needs_review' if any(e['dimension']=='I' and e['subtype'] is None for e in evidence) else 'complete' if labels['I'] else 'not_applicable'),
                innovation_unclassified_evidence=[e for e in evidence if e['dimension']=='I' and e['subtype'] is None],
                fairness_subtypes=sorted({e['subtype'] for e in evidence if e['dimension'] == 'F'}),
                safety_subtypes=sorted({'quality_safety' if e['rule']=='S07' else 'other_safety' for e in evidence if e['dimension']=='S'}),
                evidence=evidence, suppressions=suppressions,
                drug_object_evidence=object_match.group() if object_match else None,
                drug_object_in_unit=bool(DRUG_OBJECT.search(text)))

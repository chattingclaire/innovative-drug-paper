"""Read-only independent semantic preflight of frozen synthetic controls.

No classifier, model, raw180 text, reference labels, or performance metrics run/read.
Writes only this independent directory. Protected originals stay in the redactor.
"""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
BASE = OUT.parent
DESIGN = BASE / 'design-v2'
ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
DIMS = ['S', 'E', 'Ec', 'I', 'F']

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def dump_new(path, obj):
    assert not path.exists(), 'Do not overwrite independent reviews.'
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def main():
    declared = {'controls_FULL5_FROZEN.json': 'a0ce7a0a06a35e74148a9db476ce909f8b679d01e7b659940f33960ebda7140a',
                'design_FROZEN.json': '1bfd1a3caa311874bbe68f59e562b7417a2dbe84d3746a32c3e02b0d98ad74e8',
                'freeze_manifest.json': 'a211cbb5f97a6db332637d71015f4f53f57db808b750cb612e921d95e3a6f390'}
    assert all(sha(DESIGN / name) == value for name, value in declared.items())
    frozen = read(DESIGN / 'freeze_manifest.json')
    source_bindings = [{'path': str(DESIGN / name), 'sha256': value} for name, value in declared.items()]
    for relative, value in frozen['files'].items():
        path = BASE / relative
        assert sha(path) == value
        source_bindings.append({'path': str(path), 'sha256': value})
    assert len(frozen['files']) == 64 and frozen['before_any_candidate_output'] is True
    design = read(DESIGN / 'design_FROZEN.json')
    assert design['revision'] == 'v2'
    for path, value in design['manual_hashes'].items():
        assert sha(ROOT / path) == value
        source_bindings.append({'path': str(ROOT / path), 'sha256': value})
    controls = read(DESIGN / 'controls_FULL5_FROZEN.json')['controls']
    assert len(controls) == len({c['id'] for c in controls}) == 31
    expected_independently = {
        'REF-P01': '11100', 'REF-P02': '10000', 'REF-P03': '01100',
        'REF-N01': '00000', 'REF-N02': '00000', 'REF-N03': '00000', 'REF-N04': '00000',
        'STAT-P01': '01000', 'STAT-P02': '01000', 'STAT-N01': '00000', 'STAT-N02': '00000', 'STAT-N03': '00000',
        'RISK-P01': '10000', 'RISK-P02': '10000', 'RISK-N01': '00000', 'RISK-N02': '00000', 'RISK-N03': '00000',
        'ATTR-P01': '00010', 'ATTR-P02': '00010', 'ATTR-N01': '00000', 'ATTR-N02': '00000', 'ATTR-N03': '00000',
        'CHAN-P01': '00001', 'CHAN-P02': '00001', 'CHAN-N01': '00000', 'CHAN-N02': '00000', 'CHAN-N03': '00000',
        'REF-N05': '00000', 'REF-N06': '00000', 'REF-P04-QUALITY': '10000', 'REF-TECH-MISSING01': None}
    explanations = {
        'REF-P01': '当前要求符合第七条，真实七条含安全、有效及价格合理；当前仅可申请，无具体保障结果，临床必需本身不等于未满足治疗缺口。其他未被引用条号不参与。',
        'REF-P02': '当前须满足第八条，其实际内容为不良反应审查，仅安全；不能借未引用七/九/十条补E/Ec。',
        'REF-P03': '当前同时要求符合九和十条，真实九条明确疗效、十条药物经济性；未引用七/八条风险内容不传播。',
        'REF-N01': '当前为申请表填写说明导航，未以第七条实质条件约束药物评价；不将参见当成全部评价内容要求。',
        'REF-N02': '真正被援引的十一条仅申请人名称和联系方式，材料完整但全五维无实质依据；未引用七至十条仍不可借。',
        'REF-N03': '当前仅归档时标注条号这一元数据动作，不以七条条件要求评价药物。',
        'REF-N04': '真正被援引的十二条已经完整给出，仅申报材料顺序编号；因此是完整全0，而非以缺料伪装0。',
        'STAT-P01': '当前未观测协变量造成治疗选择概率差异；同一研究、同一变量的敏感性分析明确服务疗效估计偏倚。E源于该实际研究用途，非临床研究身份；治疗选择概率不是政策保障获取。',
        'STAT-P02': '“该敏感性分析”明确回指当前分析并用于药物疗效估计上下限，E有直接用途依据；不要求肯定疗效。',
        'STAT-N01': '当前敏感性分析只有模型假设和计算稳定性用途，没有药物效果用途。',
        'STAT-N02': '效果评价明确属于另一独立药物研究，不是当前敏感性分析的对象或用途。',
        'STAT-N03': '当前只要求统一格式归档；邻句疗效估计分析不将一般归档动作变成效果证据要求。',
        'RISK-P01': '为处方审核提供过敏史是具体患者药物风险资料要求，信息系统载体不排除S；未陈述风险已经发生。',
        'RISK-P02': '处方审核收集药物过敏史直接涉及用药损害识别，S有独立风险内容。',
        'RISK-N01': '一般审方信息化，没有当前具体药物风险内容、获取渠道或管理难度。',
        'RISK-N02': '审方系统提供就诊编号和挂号记录，只是行政信息；不能由处方审核名称补药物风险。',
        'RISK-N03': '药品申报系统提供申请人联系方式，仅一般事务，不涉及药物价值。',
        'ATTR-P01': '明确已批准药品适应症发生重大变化，属于相对既有产品的具体属性变化；不要求创新字样、优效、新靶点，记录attribute。适应症变化本身并非疗效评价或保障变动。',
        'ATTR-P02': '明确该药功能主治发生重大改变，具体产品属性变化支持I/attribute；审批身份不是理由本身，不推E/F。',
        'ATTR-N01': '第一次目录申报只是申请新旧，没有产品创新或明确具体保障纳入内容。',
        'ATTR-N02': '申请调整支付范围是申请动作，不陈述具体纳入/退出结果或药费责任，不能补I/Ec/F。',
        'ATTR-N03': '补交注册材料是一般事务，无创新分类实际含义或产品属性变化。',
        'CHAN-P01': '医疗机构与定点药店连通并保证电子处方流转，明确形成常规处方取药渠道，F/access成立；不要求平台已经产生效果。',
        'CHAN-P02': '明确医疗机构—零售药店处方流转并患者凭处方取药，直接为常规药物获取渠道，F/access成立。',
        'CHAN-N01': '一般信息平台和数据归档，没有患者取药或药品供应渠道关系。',
        'CHAN-N02': '虽有医疗机构和药店对象，但当前只流转档案数据，不是处方送达/患者取药的实际渠道内容。',
        'CHAN-N03': '电子处方记录归档本身不是处方送达/取药；不按处方词赋F。',
        'REF-N05': '符合七条的表达只在书名号内文件名称中；当前仅名称填写格式，标题内容不是当前实质条件。',
        'REF-N06': '当前明确援引第七条第二款，其实际内容仅材料编号；第一款安全有效/价格条件不适用。第二款已给全，语义可全0；算法细地址未支持只是不能新增，不能借整条替代。',
        'REF-P04-QUALITY': '当前符合十三条，其独立要求明确为药品质量安全评价资料，按披露的扩展S口径纳入；没有其他药物损害依据，必须quality_only/quality_safety。',
        'REF-TECH-MISSING01': '当前第十二条是实质条件援引，但材料只给七至十一条，认证十二条缺失，影响整条可判；应material_issue、undetermined、不可发布，不能用全0替代。'}
    positive_rationale = {
        ('REF-P01', 'S'): '被当前实质引用的七条明确安全。', ('REF-P01', 'E'): '同一七条明确有效。', ('REF-P01', 'Ec'): '同一七条明确药品价格合理。',
        ('REF-P02', 'S'): '当前引用八条不良反应内容。', ('REF-P03', 'E'): '当前引用九条明确疗效。', ('REF-P03', 'Ec'): '当前引用十条药物经济性条件。',
        ('STAT-P01', 'E'): '给定同一研究语境明确当前协变量/选择概率机制的疗效估计偏倚用途。',
        ('STAT-P02', 'E'): '该分析明确用于疗效估计上下限，属效果判断证据用途。',
        ('RISK-P01', 'S'): '处方审核要求具体患者过敏史风险资料。', ('RISK-P02', 'S'): '处方审核收集药物过敏史。',
        ('ATTR-P01', 'I'): '明确相对既有药品适应症发生重大变化。', ('ATTR-P02', 'I'): '明确该药功能主治发生重大改变。',
        ('CHAN-P01', 'F'): '医疗机构与药店的电子处方流转形成实际常规获取渠道。', ('CHAN-P02', 'F'): '处方流转并患者凭处方取药直接体现获取渠道。',
        ('REF-P04-QUALITY', 'S'): '明确药品质量安全评价资料要求，且仅此质量安全依据。'}
    absence = {'S': '当前有效作用域没有药物损害/风险或质量安全依据，不从主题/未适用条文补入。',
               'E': '当前没有防治效果/临床获益、治疗推荐或明确服务效果判断的证据要求。',
               'Ec': '当前没有药价、药费、支付标准/责任或药物治疗支付资源内容；申请/身份/渠道本身不足。',
               'I': '当前没有创新/改良/相对既有产品属性改变、知识产权、明确创新研发支持或创新资格比较。',
               'F': '当前没有实质药物给付/供应/获取渠道、未满足治疗缺口、患者药费负担或管理难度；程序/研究选择概率不等于获取。'}
    rows, fixture_checks = [], []
    for c in controls:
        ident = c['id']
        value = expected_independently[ident]
        labels = dict(zip(DIMS, [int(x) for x in value])) if value is not None else None
        assert labels == c['expected_labels']
        f_types = ['access'] if ident in {'CHAN-P01', 'CHAN-P02'} else []
        i_types = ['attribute'] if ident in {'ATTR-P01', 'ATTR-P02'} else []
        assert c['expected_subtype_requirements'] == {'F': f_types, 'I': i_types}
        quality = 'undetermined' if labels is None else ('quality_only' if ident == 'REF-P04-QUALITY' else 'no_quality_basis')
        safety_sources = ['quality_safety'] if ident == 'REF-P04-QUALITY' else (['other_safety'] if labels is not None and labels['S'] else [])
        if 'expected_safety_quality_basis' in c:
            assert c['expected_safety_quality_basis'] == quality
            assert c['expected_safety_subtypes'] == safety_sources
        if labels is None:
            assert c['expected_material_issue'] is True and c['expected_judgement_status'] == 'undetermined' and c['expected_publishable'] is False
        inp = c['input']
        assert inp['unit_id'] == ident and inp['unit_text'] == c['input_text']
        assert inp['unit_source'] == inp['source'] and sha(inp['unit_source']) == inp['unit_source_sha256'] == inp['source_sha256']
        assert sha(inp['candidate_file']) == inp['candidate_sha256']
        source_lines = Path(inp['unit_source']).read_text().splitlines()
        candidate = read(inp['candidate_file'])
        assert candidate['unit_candidates'] == [{'id': ident, 'text': c['input_text'], 'paragraph_id': 'p0', 'pages': [1]}]
        assert candidate['paragraphs'][0]['text'] == c['paragraph']
        assert c['input_text'] in c['paragraph']
        assert inp['paragraph_context'][0]['text'] == c['paragraph']
        for paragraph in candidate['paragraphs']:
            assert paragraph['text'] == '\n'.join(source_lines[i - 1] for i in paragraph['source_lines'])
        refs = inp.get('explicitly_cited_articles_v10', [])
        assert [(x['article'], x['text']) for x in refs] == [tuple(a) for a in c['articles']]
        assert inp.get('llm_v29_shared_context', {}).get('explicitly_cited_articles_v10', []) == refs
        for ref in refs:
            assert ref['source_path'] == inp['unit_source'] and ref['source_sha256'] == sha(ref['source_path'])
            assert ref['candidate_path'] == inp['candidate_file'] and ref['candidate_sha256'] == sha(ref['candidate_path'])
            assert ref['text'] == '\n'.join(source_lines[i - 1] for i in ref['source_lines'])
        fixture_checks.append({'id': ident, 'source_sha256': sha(inp['unit_source']), 'candidate_sha256': sha(inp['candidate_file']),
            'current_text_context_and_actual_articles_bound': True, 'source_lines_exact': True, 'unit_source_priority_verified': True})
        current_ref = {'REF-P01': ['第七条'], 'REF-P02': ['第八条'], 'REF-P03': ['第九条', '第十条'],
                       'REF-N02': ['第十一条'], 'REF-N04': ['第十二条'], 'REF-N06': ['第七条第二款'],
                       'REF-P04-QUALITY': ['第十三条'], 'REF-TECH-MISSING01': ['第十二条-缺失']} .get(ident, [])
        rows.append({'id': ident, 'input_text_read': c['input_text'], 'full_paragraph_read': c['paragraph'], 'all_given_articles_read': c['articles'],
            'independent_full5_judgment': labels, 'author_expected_full5': c['expected_labels'],
            'independent_per_dimension_reason': ({d: positive_rationale.get((ident, d), absence[d]) for d in DIMS} if labels is not None else {d: '整条缺少实际援引十二条，五维均待定，不猜0。' for d in DIMS}),
            'case_specific_scope_reason': explanations[ident], 'F_subtypes': f_types, 'I_subtypes': i_types,
            'S_quality_basis': quality, 'rule_S_source_flags_required': safety_sources, 'current_substantive_reference_addresses': current_ref,
            'evidence_expectation': {'current_unit_continuous_span': labels is not None and any(labels.values()),
                'actual_context_or_article_needed': ident in {'REF-P01', 'REF-P02', 'REF-P03', 'REF-P04-QUALITY', 'STAT-P01', 'STAT-P02'},
                'no_evidence_from_uncited_articles_or_other_study': True, 'title_only_no_current_reference_evidence': ident == 'REF-N05',
                'no_first_clause_evidence_for_second_clause': ident == 'REF-N06', 'missing_source_not_fabricated': ident == 'REF-TECH-MISSING01'},
            'material_issue': labels is None, 'judgement_status_expected': 'undetermined' if labels is None else 'determined',
            'publishable_expected': labels is not None, 'status': 'SUPPORTED_TECHNICAL_MATERIAL_GUARD' if labels is None else 'SUPPORTED_SEMANTIC_CONTROL',
            'model_or_classifier_output_seen': False})
    spec = importlib.util.spec_from_file_location('read_only_rules39_reserved_redactor', ROOT / 'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py')
    redactor_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(redactor_module)
    redactor = redactor_module.ReservedContextRedactor()
    assert redactor.audit_object_no_full_match(read(DESIGN / 'controls_FULL5_FROZEN.json'))['no_remaining_full_normalized_reserved_unit_match']
    assert all(sha(b['path']) == b['sha256'] for b in source_bindings), 'Frozen source changed while reviewing.'
    report = {'status': 'PASS_INDEPENDENT_DESIGN_V2_SEMANTIC_PREFLIGHT_NOT_IMPLEMENTATION_CERTIFICATION',
        'reviewed_at_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'reviewer': 'validation_state_oct8 AI subagent, independent of39 design/implementation author; not a blind human coder',
        'source_bindings': source_bindings, 'frozen_at': frozen['frozen_at'], 'frozen_manifest_file_count_verified': 64,
        'scope': {'controls': 31, 'semantic_controls': 30, 'semantic_dimension_cells': 150, 'missing_material_technical_controls': 1,
                  'original27_semantic_plus_title_fine_address_quality': True},
        'blocking_findings': [], 'controls_full_review': rows, 'fixture_source_audit': fixture_checks,
        'important_guard_review': {'REF_N02': 'Complete general applicant-name/contact condition supports all0; no I/F or unused S/E/Ec propagation.',
            'REF_N04': 'Complete administrative numbering clause supports all0.',
            'REF_TECH_MISSING01': 'Different control with missing required clause must be undetermined/nonpublishable; excluded from binary semantic accuracy.',
            'REF_N05': 'A reference-looking phrase inside the book title is not an operative current condition; title-masked working view must preserve original source for audit.',
            'REF_N06': 'Current second clause is administrative; do not borrow first-clause risks/effect/price. Lack of implemented fine-address parsing cannot be claimed as complete fine-address coverage.',
            'REF_P04_QUALITY': 'Only explicit drug-quality-safety evidence supports S; quality_only and quality_safety required, other_safety alone would be wrong.',
            'statistics_scope': 'Same-study explicit effect-estimation use supportsE; another independent study or neighboring archive action does not.',
            'risk_scope': 'Concrete prescription-review allergy history supportsS; general information systems and registration metadata do not.',
            'attribute_scope': 'Concrete relative product changes supportI/attribute without superiority; new applications/coverage applications do not.',
            'access_scope': 'Medical/pharmacy prescription flow and getting medicines supportsF/access, not affordability; archive flow is not that channel.'},
        'implementation_checks_still_required': ['Run frozen controls with candidate, compare all5/subtypes/quality/status and exact literal evidence/offsets; this review did not run code.',
            'Verify current matched relation is taken from title-masked v.text, not an unmasked book title.',
            'Verify reference evidence points only to actually cited authenticated address/source, not all supplied articles or wrong subclause.',
            'Verify missing-source diagnostics prevent publication of an all0 row.',
            'Any old180 bounded output/projection must retain raw input byte binding, source priority and all-field differences; manual review uses reserved-context redaction.',
            'No full4924, production or manuscript adoption is authorized by this report.'],
        'read_boundaries': {'real180_raw_text_or_predictions': 'Not read', 'A_B_T_labels_and_scores': 'Not read',
            'reserved267': 'Only in-memory full-normalized mechanical matching; zero matches in synthetic controls, index not emitted',
            'synthetic_text': 'All31 current control units, paragraphs, given articles and expected metadata actually read; repeated input/candidate forms mechanically checked for exact equality'},
        'source_files_modified': False, 'classifier_runs': 0, 'model_calls': 0,
        'limits': ['Constructed development controls do not establish new human reliability or independent machine validity.',
            'Guard negatives do not prove recall for unsupported fine reference addresses.',
            'Unresolved old boundaries remain listed in frozen design, not forced to a target score.',
            'Prior context exposure registrations remain in force; redaction cannot detect every partial quote or paraphrase.',
            'No metric-target or journal-acceptance guarantee.']}
    dump_new(OUT / 'rules39_design_v2_independent_semantic_preflight.json', report)
    text = '# 规则39 v2独立设计预检\n\n结论：当前冻结设计语义预检通过，无未闭合阻断；尚不是实现或正式效度通过。全部31条已实际读完整单元、段落、给定条文、五维预期及子类/状态元数据。\n\n'
    text += '30条语义控制共150维与固定v1.3/v1.4相符；另1条缺失援引技术控制必须待定、不可发布，不计作五维全0。REF-N02和N04完整一般行政条件与该缺料控制已分开。标题内符合条文不传播；当前第二款不能借第一款；质量单独来源必须quality_only/quality_safety。\n\n'
    text += '64个冻结文件及所有synthetic source/candidate SHA、来源行号、当前单元和实际条文绑定核对通过。新控制完整归一预留文本命中0。未运行规则/模型，未读真实180未遮蔽正文、A/B/T或分数，未改候选文件。\n\n'
    text += '首次有界运行后仍须核完整五维、子类、质量依据、状态和逐字证据/偏移；标题屏蔽、精细条款地址及缺料发布门禁不能仅由本设计报告替代。未实现细地址解析不得声称已覆盖相应正类。旧180原始输入保持绑定，任何审读投影先遮蔽预留语境。此报告不授权全量4924或改正文，也不代表新真人盲评、独立机器效度或录用保证。\n'
    (OUT / '规则39-v2独立设计预检.md').write_text(text)
    dump_new(OUT / 'review_seal.json', {'files': [{'path': str(p), 'sha256': sha(p)} for p in [OUT / 'rules39_design_v2_independent_semantic_preflight.json', OUT / '规则39-v2独立设计预检.md', Path(__file__).resolve()]], 'model_calls': 0, 'classifier_runs': 0})
    print(json.dumps({'status': report['status'], 'report': str(OUT / 'rules39_design_v2_independent_semantic_preflight.json'),
                      'sha256': sha(OUT / 'rules39_design_v2_independent_semantic_preflight.json'), 'controls': 31, 'semantic_cells': 150,
                      'model_calls': 0, 'classifier_runs': 0}, ensure_ascii=False))

if __name__ == '__main__':
    main()

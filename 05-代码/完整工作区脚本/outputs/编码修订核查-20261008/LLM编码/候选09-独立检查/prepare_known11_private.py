"""Freeze a known development probe, preserving original input rows; zero model/CLI."""
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/PROJECT_ROOT')
HERE = Path(__file__).resolve().parent
OLD = HERE.parent / '候选08-命题与证据判定'
R4 = ROOT / 'outputs/coding-revision-20261008-r4/validation-state-audit'
REAL_IDS = {'RECODE25-' + value for value in ['01955', '02764', '03876', '02830', '02845', '01562', '02220', '04894', '02086']}
SYNTHETIC_IDS = {'C05-NEW-015', 'C05-NEW-016'}
DIMENSIONS = ['S', 'E', 'Ec', 'I', 'F']
UTC = datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(path):
    path = Path(path)
    return {'path': str(path.resolve()), 'sha256': sha(path), 'bytes': path.stat().st_size}


def write(path, obj):
    with Path(path).open('x') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


source_real = OLD / 'exposed240_inputs_UNCHANGED.jsonl'
source_synthetic = OLD / 'synthetic62_inputs_UNCHANGED.jsonl'
source_expected = OLD / 'synthetic106_expected_INHERITED_PRIVATE.json'
protection = R4 / 'future_human_v5_development_exclusion_metadata.json'
redactor_path = R4 / 'reserved_context_redactor.py'
prior_exposure = HERE.parent / '候选方案/human-review-projections-REDACTED/redaction_metadata.json'
inventory = ROOT / 'outputs/编码修订核查-20261008/统计复算/同样本注意力解释/当前Rule39与完整LLM03_已修待修与边界清单.json'
manual13 = ROOT / 'outputs/coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md'
manual14 = ROOT / 'outputs/coding-revision-20261007-r3/protocol/共用操作说明-v1.4.md'
assert sha(source_real) == '4fb4dbaf39e47de5b6ff6773ace5e9e6cec98356c6538401c076845d22c31960'
assert sha(source_synthetic) == '2b70296448ddb3c1b2028eb4f85e313b59ef66c6e66842ef2c3d03153f39138b'
assert sha(source_expected) == '6507fa5c0524729ece3af87ae0661bfa733c2c134196e3c1ce56102868622f35'
assert sha(protection) == 'a3ea2e0aaabbf9d00fafb4f3511b3a8910b182111d1cff803c0bb5f03040d135'
reserved = set(json.loads(protection.read_text())['all_registered_members_of_reserved_families_unit_ids'])
assert len(reserved) == 267 and not REAL_IDS & reserved
sources = [source_real, source_synthetic, source_expected, protection, redactor_path, prior_exposure, inventory, manual13, manual14]
source_before = {str(path): sha(path) for path in sources}
selected = {}
extraction = []
for path, wanted in [(source_real, REAL_IDS), (source_synthetic, SYNTHETIC_IDS)]:
    for line_number, raw_line in enumerate(path.read_bytes().splitlines(keepends=True), 1):
        if not raw_line.strip():
            continue
        row = json.loads(raw_line)
        if row['id'] not in wanted:
            continue
        assert raw_line.endswith(b'\n'), 'Preserve complete original JSONL lines, including original newline.'
        assert row['id'] not in selected
        selected[row['id']] = (row, raw_line)
        extraction.append({'id': row['id'], 'source': bind(path), 'source_line_number': line_number,
                           'original_line_SHA': hashlib.sha256(raw_line).hexdigest(),
                           'original_row_field_order': list(row), 'original_text_SHA': hashlib.sha256(row['text'].encode()).hexdigest(),
                           'original_context_canonical_SHA': hashlib.sha256(json.dumps(row.get('contexts'), ensure_ascii=False, sort_keys=True).encode()).hexdigest()})
assert set(selected) == REAL_IDS | SYNTHETIC_IDS and len(selected) == 11
order = sorted(selected, key=lambda unit_id: hashlib.sha256(unit_id.encode()).hexdigest())
rows = [selected[unit_id][0] for unit_id in order]
input_path = HERE / 'known11_inputs_ORIGINAL_FIELDS_PRIVATE_FROZEN.jsonl'
with input_path.open('xb') as stream:
    for unit_id in order:
        stream.write(selected[unit_id][1])
assert [json.loads(line) for line in input_path.read_bytes().splitlines()] == rows
for unit_id, raw_line in zip(order, input_path.read_bytes().splitlines(keepends=True)):
    assert raw_line == selected[unit_id][1]

spec = importlib.util.spec_from_file_location('known11_protection_redactor', redactor_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
redactor = module.ReservedContextRedactor()
safe_rows, hits = redactor.redact_object(rows)
assert redactor.audit_object_no_full_match(safe_rows)['no_remaining_full_normalized_reserved_unit_match']
safe_by_id = {row['id']: row for row in safe_rows}
for hit in hits:
    row_index = int(hit['locator'].split('[')[1].split(']')[0])
    hit['current_development_unit_id'] = order[row_index]
prior = json.loads(prior_exposure.read_text())
prior_hit_records = []
for record_index, record in enumerate(prior['records']):
    matching = [hit for hit in record.get('hits_ID_and_field_path_only', []) if hit.get('reserved_unit_id') == 'RECODE25-02822']
    if matching:
        prior_hit_records.append({'prior_record_index': record_index, 'source_path': record['source'], 'source_SHA': record['source_sha256'],
                                  'unique_reserved_member_count_in_record': len({hit['reserved_unit_id'] for hit in record['hits_ID_and_field_path_only']}),
                                  'matching_ID_and_field_metadata_only': matching})
projection_path = HERE / 'known11_semantic_review_projection_REDACTED_PRIVATE.json'
write(projection_path, {'status': 'REVIEW_PROJECTION_ONLY_MODEL_INPUT_UNCHANGED', 'rows': safe_rows,
                        'new_protected_original_text_read': False,
                        'limitation': 'Full normalized protected matches are masked; arbitrary partial/paraphrase matching is not guaranteed. Do not claim full protected-context semantics were read.'})

relations = {
    'RECODE25-01955': {
        'must_recognize': [
            '当前对象的适应症或功能主治发生重大变化，是独立实体属性变化命题，不能被主动申请这一事务成分覆盖。',
            '经批准、时间范围和主动申请调整医保支付范围共同限定当前药品；给定父条款是须申报后方可调整。'],
        'must_not_infer': ['重大变化已被证明优效或具有新靶点。', '主动申请调整已经获得实际给付范围变更。']},
    'RECODE25-02764': {
        'must_recognize': [
            '当前单元同时陈述适应症或功能主治重大变化及针对此次变更取得批准证明，须保留实际改变内容。',
            '目录外可以按程序申报是父级申请资格谓词，不是已经纳入保障。'],
        'must_not_infer': ['一般新申报身份是唯一当前内容。', '获得变更批准等于获得医保纳入或证明临床优效。']},
    'RECODE25-03876': {
        'must_recognize': [
            '完整图示同时包含申报、两类专家评审、形成建议名单、价格谈判或协商、公布结果；不能只取标题或第一句。',
            '目录外申报资格有新通用名及排除单纯更名条件、罕见病适应症条件，与后续实际纳入结果分开。',
            '仅商保分支在协商成功时纳入、失败时不纳入；双目录分支先基本目录谈判，失败后才商保协商；保留条件和先后关系。',
            '目录内药品分支明确讨论适应症或功能主治重大变化及主动申请调整；这是当前图示中的实体变化，不能因图示为申报流程而删除。',
            '建议新增适应症后，协商成功新增，失败保持原表述；须保留分支结果，不把所有分支改写为已获新增保障。'],
        'must_not_infer': ['标题商保创新药目录使所有条目自动具有原创属性。', '未发生变化的全部药品也属于重大变化条件。', '申报或建议本身已确定实际纳入。']},
    'RECODE25-02830': {
        'must_recognize': [
            '施事为申请人；根据试验期间新知识经验及时更新DRMP，并在DSUR执行概要简述更新情况。',
            '申请人持续实施药物警戒及风险最小化，目的包括受试者权益、安全、福祉及试验结果可靠性，必要时与监管部门沟通。',
            '文件指导背景与当前申请人安全操作义务分开，保留全部当前动作。'],
        'must_not_infer': ['当前条款的施事是监管机构向申请人提供创新研发资源或便利。', '所有数据可靠性内容等同药物损害风险。'],
        'protected_context_limit': '部分父背景含02822，当前未读该保护句；期待仅依据完整当前句及未遮蔽必要关系，若StageA援引该保护句为关键实质依据，报告审查缺口而非冒称完整关系通过。'},
    'RECODE25-02845': {
        'must_recognize': [
            '施事为申请人，根据药物安全性风险特征实施药物警戒，识别管理风险，确保受试者安全。',
            '机构撰写指南的背景不改变当前申请人履行安全义务这一关系。'],
        'must_not_infer': ['当前条款给申请人新增创新研发资源、指导服务或优先资格。'],
        'protected_context_limit': '部分父背景含02822，未读该保护句；如实际输出依其语义，先报告缺口，不据遮蔽投影宣称全上下文实读。'},
    'RECODE25-01562': {
        'must_recognize': [
            '当前是调整支付范围药品的预算增幅子条件，包含原范围满足条件(1)以及因调整范围引起未来两年预算增幅不超过100%。',
            '给定真实父谓词明确为符合条件的协议到期药品可以简易续约，续约有效期两年；子条件必须连接这个保障延续关系。',
            '预算条件与续约资格的实质关系并存；保留条件性，不宣称当前所有药品已无条件续约。'],
        'must_not_infer': ['只有预算/价格内容而没有父续约谓词。', '只有重新谈判申请机会，或所有药品无条件永久持续给付。']},
    'RECODE25-02220': {
        'must_recognize': [
            '当前施事为药审中心，专门起草具体创新药研发风险管理技术指导原则。',
            '当前明确向临床试验各方提供将全生命周期风险管理贯穿药物研发全过程的指导；不能压缩成仅发布文件名。'],
        'must_not_infer': ['当前施事是申请人且只承担一般资料递交义务。', '凭标题推断没有明示的专有权利、产品改良或临床优势。']},
    'RECODE25-04894': {
        'must_recognize': [
            '部署处方流转中心，连通经办机构、定点医疗机构、定点零售药店，保证电子处方顺畅流转。',
            '保留机构与药店间实际处方获取渠道的联系，不能降为任意一般信息系统或纯后台文件上传。'],
        'must_not_infer': ['已经保证全部药品持续供应、降低患者药费或新增报销比例。', '段落中其他基金监管/费用分析命题自动成为当前句的动作。']},
    'RECODE25-02086': {
        'must_recognize': [
            '当前明确为协议到期并同时满足列举条件的药品提供可以简易续约、有效期两年的实质安排。',
            '给定完整后项用于明确当前续约条件；当前父谓词不能因为另有条件而被删除，也不把续约写成重新谈判机会。'],
        'must_not_infer': ['无条件所有药品均续约两年。', '续约仅为一般申报路线而没有保障连续性命题。']},
    'C05-NEW-015': {
        'must_recognize': ['当前是自足的一般综合评价方法定义；相邻句另列评价项目，但当前句没有下列/包括等实质援引。'],
        'must_not_infer': ['仅因字段名structured_following_units、相邻位置或主题接近就建立当前句对全部后项的控制关系。']},
    'C05-NEW-016': {
        'must_recognize': ['当前本次评价应包括下列药物内容明确控制给定后项清单；后项是当前对象内容的必要补足，不能被一律排除。'],
        'must_not_infer': ['凡后项都只是背景而一律不使用。', '实际药品已经满足安全、有效或原创等正面结果。']}
}

stage_a_cases = []
for unit_id in order:
    row = safe_by_id[unit_id]
    stage_a_cases.append({'id': unit_id, 'current_text_for_review': row['text'], **relations[unit_id],
                          'correct_relation_evidence_source': 'Original frozen current text and provided true parent/list context; protected02822 not used.',
                          'review_projection_row': row,
                          'semantic_judgment_not_token_string_match': True})
stage_a_path = HERE / 'stageA_semantic_expectations_PRIVATE_PREOUTPUT.json'
write(stage_a_path, {'status': 'PRIVATE_STAGE_A_RELATION_CRITERIA_FROZEN_BEFORE_CANDIDATE09_OUTPUT', 'created_at_UTC': UTC,
                     'n': 11, 'stageA_has_no_five_dimension_answers': True, 'cases': stage_a_cases,
                     'manual_bindings': [bind(manual13), bind(manual14)], 'model_input': bind(input_path),
                     'full_current_actions_and_scope_review_required': True,
                     'protected_semantics_not_reviewed': ['RECODE25-02822'],
                     'if_protected_context_needed_for_actual_A_review': 'Report the exact ID/field/SHA and semantic-review gap; do not use redacted text to claim full relation reading.',
                     'not_independent_external_validation': True, 'not_new_human_labels': True,
                     'A_B_original_reference_labels_used': False, 'new_model_calls': 0, 'new_CLI_invocations': 0})

targets = {
    'RECODE25-01955': ('I', 1, ['attribute'], 'v1.4 I2；明确适应症/功能主治重大变化。', 'confirmed_error_repair'),
    'RECODE25-02764': ('I', 1, ['attribute'], 'v1.4 I2；明确重大变化及此次变更获批。', 'confirmed_error_repair'),
    'RECODE25-03876': ('I', 1, ['attribute'], 'v1.4 I2；完整图示目录内分支的明确重大变化。', 'confirmed_error_repair'),
    'RECODE25-02830': ('I', 0, [], 'v1.4 I1/I5；当前是申请人安全操作义务，没有机构给予创新研发支持。', 'confirmed_error_repair'),
    'RECODE25-02845': ('I', 0, [], 'v1.4 I1/I5；当前药物警戒义务不是研发支持资源。', 'confirmed_error_repair'),
    'RECODE25-01562': ('F', 1, ['access'], 'v1.4 F1/F2；真父谓词为符合条件的两年简易续约。', 'confirmed_error_repair'),
    'RECODE25-02220': ('I', 1, ['research_support'], 'v1.4 I1；药审中心当前明确提供创新研发技术指导。', 'currently_correct_protection'),
    'RECODE25-04894': ('F', 1, ['access'], 'v1.4 F1/F4；机构与药店电子处方流转构成实际用药获取渠道。', 'currently_correct_protection'),
    'RECODE25-02086': ('F', 1, ['access'], 'v1.4 F1/F2；当前明确两年简易续约实质连续性。', 'currently_correct_protection')
}
old_tests = json.loads(source_expected.read_text())['tests']
old_synthetic = {test['input']['id']: test for test in old_tests if test['input']['id'] in SYNTHETIC_IDS}
assert set(old_synthetic) == SYNTHETIC_IDS
stage_b_cases = []
for unit_id in order:
    if unit_id in targets:
        dim, value, subtypes, rationale, role = targets[unit_id]
        labels = {dim: value}
        case = {'id': unit_id, 'role': role, 'frozen_partial_labels': labels,
                'frozen_subtypes': {('innovation_subtypes' if dim == 'I' else 'fairness_subtypes'): subtypes},
                'basis': rationale, 'unfrozen_dimensions': [dim for dim in DIMENSIONS if dim not in labels],
                'unfrozen_dimensions_policy': 'No default0 or copied old prediction/human vector; all still require actual full semantic review.',
                'source': 'Actual current text plus given context and unchanged manual; prior confirmed diagnosis is a locator, not a human reference vector.'}
    else:
        test = old_synthetic[unit_id]
        assert test['input'] == selected[unit_id][0]
        value = 0 if unit_id == 'C05-NEW-015' else 1
        assert test['labels'] == {dim: value for dim in DIMENSIONS}
        case = {'id': unit_id, 'role': 'known_synthetic_definition_vs_explicit_list_regression',
                'frozen_partial_labels': test['labels'],
                'frozen_subtypes': {'innovation_subtypes': [] if value == 0 else ['attribute'],
                                    'fairness_subtypes': [] if value == 0 else ['affordability']},
                'subtype_expectation_provenance': 'New09 manual-based auxiliary predeclaration; original inherited labels file did not include auxiliary expectations. Do not call these old frozen subtype expectations.',
                'basis': test['rationale'], 'unfrozen_dimensions': [], 'original_label_expectation_source': bind(source_expected)}
    stage_b_cases.append(case)
assert sum(len(case['frozen_partial_labels']) for case in stage_b_cases) == 19
stage_b_path = HERE / 'stageB_partial_expectations_PRIVATE_PREOUTPUT.json'
write(stage_b_path, {'status': 'PRIVATE_PARTIAL_LABELS_AND_KNOWN_SUBTYPES_FROZEN_BEFORE_CANDIDATE09_OUTPUT', 'created_at_UTC': UTC,
                     'cases': stage_b_cases, 'n': 11, 'total_possible_dimension_cells': 55, 'explicit_frozen_dimension_cells': 19,
                     'not_prefilled_dimension_cells': 36, 'model_input': bind(input_path), 'manual_bindings': [bind(manual13), bind(manual14)],
                     'minimum_known_correction_requirement': 'All six confirmed wrong target dimensions corrected; all three correct protection targets preserved; original015 five zeros and016 five ones preserved.',
                     'additional_requirement': 'Review all55 actual dimension decisions, reasons, evidence, subtypes, quality and issues semantically; passing19 fixed cells alone is insufficient. Do not change frozen expectations after output.',
                     'human_AB_labels_or_old_machine_full_vectors_copied_as_gold': False,
                     'not_new_independent_human_validation': True, 'known_development_material': True,
                     'no_kappa_target': True, 'no_model_execution_or_adoption_authorization': True,
                     'new_model_calls': 0, 'new_CLI_invocations': 0})

metadata_path = HERE / 'known11_source_extraction_and_protection_metadata.json'
write(metadata_path, {'status': 'MECHANICAL_SOURCE_EXTRACTION_AND_PRIVACY_REGISTER_ONLY', 'created_at_UTC': UTC,
                      'model_input': bind(input_path), 'n': 11, 'real_n': 9, 'known_synthetic_n': 2,
                      'fixed_order': order, 'order_rule': 'ascending SHA256(UTF-8 original id); fixed before candidate09 output',
                      'all11_rows_byte_identical_to_original_JSONL_source_lines': True,
                      'source_rows_and_fields_not_reencoded_or_renamed': True,
                      'source_rows': extraction, 'source_bindings': [bind(path) for path in sources],
                      'nine_current_unit_IDs_reserved267_intersection': [],
                      'whole_package_contains_reserved_context_material': bool(hits),
                      'reserved_context_member_ids': sorted({hit['reserved_unit_id'] for hit in hits}),
                      'reserved_context_occurrences': hits, 'prior_registered_metadata_02822': prior_hit_records,
                      'current_reviewer_new_protected_original_text_semantically_read': False,
                      'current_manual_review_projection': bind(projection_path),
                      'current_model_visible_09': 'NOT_RUN; input prepared only, not sent to a model',
                      'required_after_actual_StageA_if_authorized': 'Append separate metadata record for actual09 request includes02822: input/source/request/attempt path+SHA, distinguish model visibility from human/agent semantic reading. Do not modify originalv5.',
                      'cannot_claim': 'Nine current IDs outside267 does not make all input context unreserved or establish independent external validity.',
                      'real_model_calls': 0, 'real_CLI_invocations': 0, 'execution_authorized': False})
assert all(sha(path) == value for path, value in source_before.items())
manifest_path = HERE / 'known11_independent_preparation_manifest.json'
write(manifest_path, {'status': 'FROZEN_KNOWN_DEVELOPMENT_PROBE_ROOT_REVIEW_REQUIRED_NO_EXECUTION_AUTHORIZATION', 'created_at_UTC': UTC,
                      'model_input': bind(input_path), 'n': 11, 'private_stageA_expectations': bind(stage_a_path),
                      'private_stageB_partial_expectations': bind(stage_b_path), 'metadata': bind(metadata_path),
                      'redacted_semantic_projection': bind(projection_path), 'builder': bind(Path(__file__)),
                      'source_bindings': [bind(path) for path in sources],
                      'A_B_reference_status': 'User-confirmed human adjudication accepted; original references unchanged. This preparation is an agent-defined known development probe, not new human coding.',
                      'author_access': 'Root reviews first; only then author may receive model-input path/SHA/n for mechanical configuration. Do not send author privateA/B criteria, answers or the earlier private four-arm examples.',
                      'source_files_modified': False, 'new_model_calls': 0, 'new_CLI_invocations': 0,
                      'candidate09_prompt_or_runtime_modified_by_reviewer': False, 'execution_authorized': False})
print(json.dumps({'status': 'FROZEN_ZERO_MODEL_ZERO_CLI', 'n': 11, 'input': bind(input_path),
                  'stageA': bind(stage_a_path), 'stageB': bind(stage_b_path), 'manifest': bind(manifest_path),
                  'frozen_B_cells': 19, 'unfrozen_B_cells': 36, 'reserved_context_members': sorted({hit['reserved_unit_id'] for hit in hits}),
                  'reserved_context_occurrences': len(hits), 'source_files_modified': False}, ensure_ascii=False))

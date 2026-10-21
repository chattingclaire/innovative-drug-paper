"""Build a proposed fixed prompt and synthetic controls; never invoke a model.

No gold/reference table, statistic, future-human text or future-human label is read.
Existing exposed240 inputs are checked by IDs and copied byte for byte.
"""
from pathlib import Path
from datetime import datetime, timezone
import difflib
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate05-preparation'
REVIEW = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate05-independent-semantic-review/candidate05_semantic_review_PRIVATE.json'
EXCLUSION = ROOT / 'outputs/coding-revision-20261008-r4/validation-state-audit/future_human_v5_development_exclusion_metadata.json'
DIMS = ['S', 'E', 'Ec', 'I', 'F']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def labels(*ones):
    return {d: int(d in ones) for d in DIMS}


def main():
    assert sha(EXCLUSION) == 'a3ea2e0aaabbf9d00fafb4f3511b3a8910b182111d1cff803c0bb5f03040d135'
    reserved = set(json.loads(EXCLUSION.read_text())['all_registered_members_of_reserved_families_unit_ids'])
    source = OLD / 'candidate05_prompt_frozen.txt'
    assert sha(source) == 'e609d2564c8471f5376057948089a6d9ae03dff3a6811d7ee5965711efb43a0e'
    old_prompt = source.read_text()
    marker = '--- 冻结的完整手册（原样） ---'
    prefix, suffix = old_prompt.split(marker, 1)
    modifications = []

    def replace(rule, old, new, manuals):
        nonlocal prefix
        assert prefix.count(old) == 1, (rule, prefix.count(old))
        prefix = prefix.replace(old, new)
        modifications.append({'rule': rule, 'old': old, 'new': new, 'manual_locations': manuals})

    replace('version_title', '候选05-development', '候选06-design-v2-only', [])
    replace('R1_current_context_role',
            '引导句可结合明确属于它的后项理解。上下文只消解对象、指代、比较、条件、缩写、列义或明确承接的证据用途，不传播相邻句或父段全部标签。',
            '引导句只在后项是理解其关键对象、条件、列义或实质评价内容所必需时，结合真实所属后项；判断当前命题是否自足，须包括原句明示的适用条件；不能仅因主体、主要结果或期限已经出现、后项另列单元，就认定后项不必要。对当前明确设置的实质条件，应依据其真实适用关系使用；没有该关系的相邻后项不回传标签。现有手册对某一引导句需展开到何种内容存在解释边界时，保留个人二元判断并记录boundary_note，不一律复制或一律排除后项。当前明确援引某项必须满足的实质条件时，使用给定的该项条件内容，不把它降为背景；仅借用既有身份、对象范围或办理结果时，不传递该身份背后的全部评价内容。上下文只消解对象、指代、比较、条件、缩写、列义或明确承接的证据用途，不传播相邻句或父段全部标签。',
            ['v1.3:17,65,146,148', 'v1.4:7'])
    replace('R2_F_current_relation',
            '明确规定适用条件、退出或续期时可以讨论F；仅组织决定步骤、研究可行路径或确认既有协议信息，不自行补成实际给付条件。',
            '当前实质陈述或规定药物保障覆盖、排除、适用条件及持续期限时，按F原边界判断，不额外要求新增保障、另一个给付承诺或已经产生患者获益。保障协议的适用期限可由给定语境补足其药物保障对象；仅核对编号、存档、报送或办理日期等事务信息不自动计F。一般遴选或申报范围不自动等于实际保障，但同句明确陈述某项现有药物保障覆盖或排除状态时，该内容不能因兼作分类条件而删除。仅组织决定步骤或研究可行路径，不自行补成实际给付条件。',
            ['v1.3:11,53,152', 'v1.4:7,21,22'])
    replace('R4_E_identity_not_content',
            '一般制定或遵守用药指南、处方权限和给药规范的制度职责，不自行补成已经陈述的药物治疗推荐。',
            '一般制定或遵守用药指南、处方权限和给药规范的制度职责，不自行补成已经陈述的药物治疗推荐。药品已经列入某诊疗方案等身份若仅界定其他规定的适用对象，不把既有方案的治疗推荐内容带入当前单元；当前实质提出药物治疗推荐，或明确要求相应效果内容或证据时，仍据该内容判断E。',
            ['v1.3:17,29,31,65', 'v1.4:7,9'])
    replace('R5_I_no_extra_novelty_threshold',
            '按v1.4判断当前规定本身是否新增或改变创新研发支持的实际内容、资源或资格。',
            '按v1.3/v1.4判断当前是否实质规定、提供、扩大或讨论创新研发支持的内容、资源或资格；“新增或改变”不是所有研发支持命题的额外必要条件。',
            ['v1.3:166', 'v1.4:13'])
    replace('R2_F_internal_administration',
            '一般机构准入、公平竞争或公示程序而没有该药物渠道关系时仍排除。',
            '一般机构准入、公平竞争或公示程序而没有该药物渠道关系时仍排除。仅分派机构内部采购、验收或经办职责，不因其通常有助于供药就推定为常规治疗获取渠道；当前另有实际药物配备、供应范围或获取安排时，仍保留F。',
            ['v1.3:53,123,152', 'v1.4:21,25'])
    replace('R3_Ec_and_R4_SE_content',
            '价格协商的会务流程、协议数据确认与价格/费用实质内容分别判断；经济性不要求必须出现金额。知识产权范围内用安全/疗效名称分类资料，不因此自动成为新增安全/疗效评价要求；若同句独立要求评价或提交相应证据仍纳入。',
            '只组织价格协商、签约、会务或办理步骤而未实质讨论药价取值或调整、费用、支付、经济评价或费用责任时，不因程序名称赋Ec；明确讨论这些经济内容时，不要求出现具体金额、新价格或已发生支付结果。仅用安全/疗效名称标识受保护、公开或保存的资料类别，不自动计S/E；当前明确要求评价、收集、提交该内容，或明确援引必须满足的相应证据要求时，按当前与所援引内容组成的实质命题判断，不额外要求本句重复原词、提出新的评价或给出结果。沟通、申报或指南的主题可以消解对象，但主题本身不能把一般沟通方式变成S/E内容要求。',
            ['v1.3:21,29,31,35,37,65,67', 'v1.4:7'])
    replace('R5_I_classification_meaning',
            '创新对象可由真实适用范围补足，但范围只补对象，不替代当前支持措施。',
            '以研发支持为依据时，创新对象可由真实适用范围补足，但范围只补对象，不替代当前支持措施。以注册创新分类为依据时，说清给定材料中实际适用于当前对象的分类含义及引文；只有分类序号、一般支持创新宗旨或机制背景时，不补出其创新含义。已给定并实际适用的创新分类定义可支持属性依据，不另要求实体研发支持或优效结果。',
            ['v1.3:43,136,142', 'v1.4:7,16,17'])
    replace('R2_F_no_new_coverage_requirement',
            '就不能把既有给付范围/保障期限变成本句的新保障内容。',
            '就不能把作为对象前提的既有给付范围/保障期限当作当前实质规定的保障内容；这不排除当前本身实质陈述或规定保障持续期限。',
            ['v1.4:21,22'])
    prompt = prefix + marker + suffix
    assert prompt.split(marker, 1)[1] == old_prompt.split(marker, 1)[1]
    assert all(x not in prompt for x in ['RECODE25-', 'RECALL-BLIND-', 'C06-PAIR-', '0.80'])
    (HERE / 'candidate06_prompt_PROPOSED.txt').write_text(prompt)
    (HERE / 'candidate05_to_06_prompt.diff').write_text(''.join(difflib.unified_diff(old_prompt.splitlines(True), prompt.splitlines(True), fromfile='candidate05_prompt_frozen.txt', tofile='candidate06_prompt_PROPOSED.txt')))
    write(HERE / 'prompt_change_map.json', {'status': 'PROPOSED_NOT_MODEL_TESTED', 'five_semantic_clarifications': True, 'constructs_schema_manuals_changed': False, 'changes': modifications})
    manual_basis = []
    for file, line_numbers in [('完整五维手册-v1.3.md', [11,17,21,29,31,35,37,43,53,65,67,121,123,136,142,146,148,152,166]),
                               ('共用操作说明-v1.4.md', [7,9,13,16,17,21,22,24,25])]:
        path = ROOT / 'outputs/coding-revision-20261007-r3/protocol' / file
        lines = path.read_text().splitlines()
        manual_basis.append({'path': str(path), 'sha256': sha(path), 'quotes': [{'line': i, 'quote': lines[i-1]} for i in line_numbers]})
    write(HERE / 'manual_rule_basis.json', {'definitions_not_changed': True, 'sources': manual_basis})

    pairs = []

    def pair(number, target, negative, positive, negative_labels, positive_labels, rationale, negative_context=None, positive_context=None):
        ident = f'C06-PAIR-{number:02d}'
        n = {'id': ident + '-A', 'text': negative, 'contexts': negative_context or {}}
        p = {'id': ident + '-B', 'text': positive, 'contexts': positive_context or {}}
        pairs.append({'pair_id': ident, 'target': target, 'rationale': rationale,
                      'members': [{'input': n, 'labels': negative_labels}, {'input': p, 'labels': positive_labels}],
                      'synthetic_not_policy_quote': True})

    pair(1, 'R2 coverage exclusion vs work grouping',
         '本轮材料按慢性病用药和急救用药分组送交评议。',
         '本保障计划明确不覆盖供美容用途使用的药物。',
         labels(), labels('F'), '工作分组不决定保障；当前负向覆盖范围属于保障内容。')
    pair(2, 'R2 operative coverage duration vs administrative record',
         '经办人员应核对药物保障协议的编号和到期日期，并登记归档。',
         '本类药物的保障协议有效期为十八个月。',
         labels(), labels('F'), '仅核对既有信息与当前直接规定保障期限相区分。')
    shared_scope = {'verified_parent_context': [{'text': '本节针对已经纳入本保障计划的药品。'}]}
    pair(3, 'R2 budget child controlled by continuity vs application',
         '本期药费预算增幅不高于百分之十二。',
         '本期药费预算增幅不高于百分之十二。',
         labels('Ec'), labels('Ec', 'F'), '同一预算子项的F取决于真正控制它的父谓词，不由预算词决定。',
         {'verified_parent_context': [{'text': '本节针对已经纳入本保障计划的药品；符合以下条件者可以提出再次谈判申请。'}]},
         {'verified_parent_context': [{'text': '本节针对已经纳入本保障计划的药品；符合以下条件者原有药物保障延续十八个月。'}]})
    pair(4, 'R1/R4 explicit operative reference vs record checking',
         '工作人员核对依第九款完成资料存档的记录编号。',
         '获得本项资格必须满足第九款规定的证据条件。',
         labels(), labels('S', 'E'), '明确援引必须满足的内容要求与仅核对存档编号不同。',
         {'explicitly_cited_conditions': [{'text': '第九款：申请人须提交该药毒性风险和降低死亡率的研究证据。'}]},
         {'explicitly_cited_conditions': [{'text': '第九款：申请人须提交该药毒性风险和降低死亡率的研究证据。'}]})
    pair(5, 'R3 economic content vs negotiation organization',
         '秘书处安排药价协商会的地点并组织签约手续。',
         '该药的协商价格以对照治疗费用为基准下调一成。',
         labels(), labels('Ec'), '经济性不由协商程序名自动成立，也不要求必须给出金额。')
    pair(6, 'R4 existing treatment-plan identity vs actual recommendation',
         '对已经列入某治疗方案的药物，资料提交日期延后一周。',
         '本治疗方案推荐使用该药，以提高患者的无进展生存率。',
         labels(), labels('E'), '已有身份只是事务规定的对象，当前推荐及效果内容独立成立。')
    shared_safety = {'paragraph_context': [{'text': '本节主题为药物肝毒性证据材料。'}]}
    pair(7, 'R4 safety topic vs safety-content requirement',
         '有疑问的申请人可预约电话沟通。',
         '申请人须补充该药肝毒性发生率和监测结果。',
         labels(), labels('S'), '同一安全主题不会把一般沟通方式变成安全内容要求。', shared_safety, shared_safety)
    following = {'structured_following_units': [{'text': '一、计算每名患者的药物疗程成本。'}, {'text': '二、比较不同支付方案下的药费分担。'}]}
    pair(8, 'R1 self-contained head vs content-requiring head',
         '本类药物保障协议延续十八个月。',
         '申报材料应当评价以下内容：',
         labels('F'), labels('Ec'), '前者保障命题完整自足，另一独立任务的经济内容不传递；后者须借列表补足评价内容。此对不裁断明确条件引导句。',
         {'immediately_following_paragraph': {'text': '另一项独立任务要求计算药物疗程成本，并比较不同方案的药费分担。'}}, following)
    pair(9, 'R2 internal procurement duty vs treatment access channel',
         '药学办公室承担购药单据核对和入库验收职责。',
         '患者可在指定基层药房领取本计划覆盖的治疗药物。',
         labels(), labels('F'), '内部经办职责不自行补成患者用药渠道；实际领取渠道属于获取安排。')
    pair(10, 'R5 unsupported serial vs supplied classification meaning',
         'R7类药品可适用本项规定。',
         'R7类药品可适用本项规定。',
         labels(), labels('I'), '相同编号只有在给定实际定义后才能支持创新属性，不依常识补义。',
         {}, {'verified_definition': {'definition': '本文件的R7类指含有首次开发活性成分的原创药物。'}})
    pair(11, 'R5 broad innovation purpose does not define serial',
         'R7类药品的价格下调比例可取原定比例的七成。',
         'R7类药品的价格下调比例可取原定比例的七成。',
         labels('Ec'), labels('Ec', 'I'), '价格安排与一般创新宗旨不能自行证明编号含义；实际适用的分类定义可以提供属性依据。',
         {'paragraph_context': [{'text': '本文件总体旨在鼓励药物创新。'}]},
         {'paragraph_context': [{'text': '本文件总体旨在鼓励药物创新。'}], 'verified_definition': {'definition': '本文件的R7类指含有首次开发活性成分的原创药物。'}})
    innovation_scope = {'verified_parent_context': [{'text': '本节适用于开展原创药物研发的团队。'}]}
    pair(12, 'R5 substantive ongoing support vs routine report',
         '研发团队按季度报送联系人信息。',
         '本中心持续向上述研发团队提供免费的药学技术咨询。',
         labels(), labels('I'), '实质支持不额外要求本次新增；同一创新对象范围不把通用报告变为支持措施。', innovation_scope, innovation_scope)

    new_tests = []
    new_inputs = []
    for p in pairs:
        for m in p['members']:
            new_inputs.append(m['input'])
            new_tests.append({'input': m['input'], 'labels': m['labels'], 'rationale': p['rationale'], 'pair_id': p['pair_id'], 'control_origin': 'candidate06_new_synthetic_pair'})
    write(HERE / 'synthetic24_pairs_PRIVATE_PROPOSED.json', {'status': 'PREEXECUTION_SYNTHETIC_EXPECTATIONS_REQUIRE_INDEPENDENT_REVIEW', 'pairs': pairs})
    (HERE / 'synthetic24_inputs_PROPOSED.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in new_inputs))
    old_inputs = (OLD / 'synthetic62_inputs_frozen.jsonl').read_bytes()
    (HERE / 'synthetic62_inputs_UNCHANGED.jsonl').write_bytes(old_inputs)
    inherited = [json.loads(line) for line in old_inputs.decode().splitlines() if line.strip()]
    expected = json.loads((OLD / 'synthetic62_expected_PRIVATE_frozen.json').read_text())
    assert len(inherited) == len(expected['tests']) == 62
    assert {r['id'] for r in inherited} == {r['input']['id'] for r in expected['tests']}
    assert len({x['id'] for x in inherited + new_inputs}) == 86
    assert not {r['id'] for r in inherited + new_inputs} & reserved
    (HERE / 'synthetic86_inputs_PROPOSED.jsonl').write_bytes(old_inputs + (b'' if old_inputs.endswith(b'\n') else b'\n') + (HERE / 'synthetic24_inputs_PROPOSED.jsonl').read_bytes())
    write(HERE / 'synthetic86_expected_PRIVATE_PROPOSED.json', {'status': 'PREEXECUTION_PROPOSED_NOT_MODEL_TESTED', 'inherited62_unchanged': True,
          'preexisting_disputed_control': 'C05-NEW-019', 'disputed_expectation_preserved_not_silently_scored_as_pass_or_error': True,
          'new_pair_count': 12, 'new_unit_count': 24, 'tests': expected['tests'] + new_tests})
    shutil.copyfile(OLD / 'exposed240_inputs_frozen.jsonl', HERE / 'exposed240_inputs_UNCHANGED.jsonl')
    exposed = [json.loads(line) for line in (HERE / 'exposed240_inputs_UNCHANGED.jsonl').read_text().splitlines() if line.strip()]
    assert len(exposed) == 240 and len({x['id'] for x in exposed}) == 240
    assert not {x['id'] for x in exposed} & reserved
    assert sha(HERE / 'exposed240_inputs_UNCHANGED.jsonl') == '4fb4dbaf39e47de5b6ff6773ace5e9e6cec98356c6538401c076845d22c31960'

    runtime = HERE / 'runtime-unchanged-v2'
    runtime.mkdir(exist_ok=True)
    for name in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']:
        shutil.copyfile(OLD / 'runtime-v2' / name, runtime / name)
        assert sha(runtime / name) == sha(OLD / 'runtime-v2' / name)
    # Only invoke the input-field checker as a pure function, never runner.main().
    import importlib.util
    spec = importlib.util.spec_from_file_location('candidate06_no_execution_runtime', runtime / 'run_production_v32.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.no_reference_fields(exposed)
    module.no_reference_fields(inherited + new_inputs)

    semantic = json.loads(REVIEW.read_text())
    error_items = [x for x in semantic['confirmed_current_errors_in_changed_review']['items'] if not (x['id'] == 'RECODE25-02086' and x['dimension'] == 'Ec')]
    assert not {x['id'] for x in semantic['changed_unit_reviews']} & reserved
    current_changed_errors = {(x['id'], x['dimension']) for x in semantic['comparison_change_counts_and_manual_review']['current_full_candidate03_exposed240_rows']['cells'] if x['review_status'] == 'confirmed_error'}
    mechanics = {
        'RECODE25-00663': ('R2', 'current_negative_coverage_misread_as_only_work_classification'),
        'RECODE25-00964': ('R3', 'negotiation_action_misread_as_substantive_price_content'),
        'RECODE25-01432': ('R1/R4', 'operative_explicit_evidence_condition_misread_as_only_rights_background'),
        'RECODE25-01562': ('R2', 'verified_parent_continuity_result_misread_as_only_procedure'),
        'RECODE25-01616': ('R4', 'existing_treatment_plan_identity_misread_as_current_treatment_recommendation'),
        'RECODE25-01768': ('R4', 'safety_topic_misread_as_current_safety_evidence_requirement'),
        'RECODE25-02086': ('R2', 'operative_coverage_continuity_omission_Ec_reconsidered_boundary'),
        'RECODE25-02364': ('R2', 'internal_procurement_duty_misread_as_treatment_access_channel'),
        'RECODE25-03261': ('R2', 'operative_coverage_agreement_duration_misread_as_no_patient_result'),
        'RECODE25-03712': ('R5', 'broad_innovation_purpose_misread_as_actual_innovation_class_scope')
    }
    private_ledger = []
    actual_by_id = {}
    actual_output = OLD / 'runtime-v2/exposed240-candidate05-first-run/all_predictions.jsonl'
    for line in actual_output.read_text().splitlines():
        row = json.loads(line)
        if row['id'] in mechanics:
            actual_by_id[row['id']] = row
    input_by_id = {row['id']: row for row in exposed if row['id'] in mechanics}
    for x in error_items:
        is_regression = (x['id'], x['dimension']) in current_changed_errors
        private_ledger.append({'id': x['id'], 'dimension': x['dimension'], 'status_vs_current_full03': 'regression' if is_regression else 'persistent_error',
                               'actual05': x['actual'], 'prior_semantic_reviewer_judgment_not_gold': x['reviewer_judgment_not_gold'],
                               'actual05_dimension_reason': actual_by_id[x['id']]['dimension_reasons'][x['dimension']],
                               'actual05_dimension_evidence': [e for e in actual_by_id[x['id']]['evidence'] if e['dimension'] == x['dimension']],
                               'complete_input_object_canonical_sha256': hashlib.sha256(json.dumps(input_by_id[x['id']], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                               'prior_review_reason': x['reason'], 'candidate06_rule': mechanics[x['id']][0], 'mechanism': mechanics[x['id']][1],
                               'classification': 'explicit_manual_execution_plus_unavailable_class_definition' if x['id'] == 'RECODE25-03712' else 'explicit_manual_execution',
                               'context_state': 'classification_meaning_not_supplied_no_external_fill' if x['id'] == 'RECODE25-03712' else 'necessary_context_present_in_frozen05_input',
                               'correction_not_yet_demonstrated': True})
    assert sum(x['status_vs_current_full03'] == 'regression' for x in private_ledger) == 8
    assert sum(x['status_vs_current_full03'] == 'persistent_error' for x in private_ledger) == 3
    write(HERE / 'candidate05_regression_mechanism_review_PRIVATE.json', {'status': 'MECHANISM_HYPOTHESES_NOT_GOLD_OR_NEW_RESULTS', 'regression_cells': 8, 'persistent_cells': 3, 'withdrawn_from_confirmed_error': {'id': 'RECODE25-02086', 'dimension': 'Ec', 'new_status': 'boundary_with_direct_support_for_Ec1', 'historical_review_not_modified': True},
          'items': private_ledger, 'definition_boundary_cases_not_forced': semantic['manual_boundary_cells_in_changed_review'] + [{'id': 'RECODE25-02086', 'dimension': 'Ec', 'actual': 1, 'reason': '原句明示同时满足以下条件，给定完整经济后项构成当前适用条件；不能仅因结果和期限出现认定其不必要。Ec1有直接支持，撤回此前确定错误判断，保留边界并倾向Ec1。'}],
          'preexisting_control_boundary_not_forced': 'C05-NEW-019', 'no_A_C_scores_or_reference_labels_used': True})
    write(HERE / 'predeclared_acceptance_PROPOSED.json', {
        'status': 'PROPOSED_BEFORE_ANY_CANDIDATE06_MODEL_OUTPUT',
        'pre_execution': ['Root or a separately assigned reviewer checks prompt diff and all24 new synthetic full-five-dimensional expectations against unchanged manuals.',
                          'Bind all input/prompt/manual/schema/validator/runner hashes and actual CLI version before root separately authorizes calls.',
                          'Do not inspect reserved267 original texts/labels for development; current design ID intersection is zero.'],
        'technical': ['One unique item.completed agent_message; parsed JSON equals raw_output with type-preserving canonical comparison.',
                      'Exact complete input ID order, schema, integer binary types, literal quotes, subtype contracts and zero tool/unknown events.',
                      'Accept first chronological technically valid attempt only; identical-request technical retries maximum3. No semantic retries.'],
        'synthetic': ['All24 new controls must satisfy independently accepted full-five-dimensional expectations and both sides of all12 pairs; review reasons/evidence/subtypes, not labels alone.',
                      'Review all62 inherited controls. Do not lose any of the61 previously non-disputed control decisions.',
                      'Preserve the original C05-NEW-019 expectation and explicit boundary status; do not silently call it a pass, proven error or reason to change the manual.'],
        'complete_exposed240_development': ['Run all240 once with the same prompt and original input/order/batch membership. Never rerun only error IDs and splice production labels.',
                                         'Review all five dimensions of every change versus candidate05 and all three intact histories. Review all11 remaining preidentified error cells and all prior confirmed improvements; do not use A/C scores for tuning or selecting.',
                                         'Before considering a full shadow run, require no confirmed new regression in the complete change review and resolution of all11 remaining preidentified error cells under unchanged materials/manuals. If a cell remains definition-boundary or material-limited, report that explicitly and do not declare safe improvement.',
                                         'Keep the9 real-material boundary cells (including reconsidered Ec02086) separate; their agreement with any historical output is not an acceptance metric.'],
        'release_limits': ['Development remeasurement is not independent validation. No production labels or manuscript may be updated from this design/run alone.',
                          'Do not compare candidate kappa/F1 to select a winner. Do not average, vote, cherry-pick attempts or splice different candidates.',
                          'This fixed run cannot establish repeat stability, provider-version stability or causal attribution to the prompt. Any separate repetition/order study requires a separately bounded decision and cannot replace true labels.']})

    python = '/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
    plans = []
    for n, inp, name, workers in [(240, HERE / 'exposed240_inputs_UNCHANGED.jsonl', 'exposed240-candidate06-first-run', 3), (62, HERE / 'synthetic62_inputs_UNCHANGED.jsonl', 'synthetic62-candidate06-first-run', 1), (24, HERE / 'synthetic24_inputs_PROPOSED.jsonl', 'synthetic24-candidate06-first-run', 1)]:
        command = [python, str(runtime / 'run_production_v32.py'), '--input', str(inp), '--expected-input-sha256', sha(inp), '--prompt', str(HERE / 'candidate06_prompt_PROPOSED.txt'), '--expected-n', str(n), '--run-name', name, '--batch-size', '25', '--workers', str(workers), '--max-attempts', '3', '--purpose', 'Single proposed candidate06 complete development run; no semantic retries, independent-validation claim, production-label update or manuscript update.']
        plans.append({'n': n, 'batch_size': 25, 'logical_requests': (n + 24) // 25, 'workers': workers, 'plan_only_command': command + ['--plan-only'], 'future_execution_command_after_separate_root_authorization_only': command})
    write(HERE / 'candidate06_execution_plan_PROPOSED.json', {'status': 'DESIGN_ONLY_NOT_AUTHORIZED_NOT_EXECUTED', 'model': 'gpt-5.6-sol', 'reasoning_effort': 'medium',
          'runs': plans, 'nominal_logical_requests': 14, 'maximum_identical_technical_attempts': 42, 'model_calls_by_this_design': 0,
          'synthetic86_combined_inventory_not_an_additional_execution_input': True,
          'old240_and_inherited62_batch_membership_and_order_preserved_vs_candidate05': True,
          'manuals_schema_validator_and_v2_technical_gate_unchanged': True,
          'selection': 'first chronologically technically valid attempt only; no labels/metrics/semantic selection',
          'retry': 'identical complete request after technical failure only; never retry semantic disagreement or favorable score',
          'full_corpus': False, 'requires_independent_prompt_controls_preflight_and_separate_root_authorization': True})
    write(HERE / 'design_QA.json', {'status': 'PASS_NO_MODEL_CALLS', 'manual_schema_footer_exactly_unchanged': True, 'runtime_three_files_exactly_unchanged': True,
          'exposed240_input_exactly_unchanged': True, 'inherited62_input_bytes_prefix_exactly_preserved': (HERE / 'synthetic86_inputs_PROPOSED.jsonl').read_bytes().startswith(old_inputs),
          'inherited62_expected_records_exactly_preserved': expected['tests'] == json.loads((HERE / 'synthetic86_expected_PRIVATE_PROPOSED.json').read_text())['tests'][:62],
          'new_pairs': 12, 'new_controls': 24, 'total_controls': 86, 'new_controls_full_five_dimension_expectations': True,
          'unique_ids': True, 'exposed240_reserved267_intersection': 0, 'reviewed38_reserved267_intersection': 0,
          'prompt_has_no_real_unit_ids_or_new_control_ids_or_target_kappa': True, 'inputs_have_no_reference_or_prediction_fields': True,
          'CLI_subprocess_calls': 0, 'model_calls': 0, 'future_reserved_source_text_or_labels_read': False,
          'prior_candidate05_prompt_preserved': sha(source) == 'e609d2564c8471f5376057948089a6d9ae03dff3a6811d7ee5965711efb43a0e',
          'semantic_success_not_proven': True, 'Ec02086_not_forced_to_zero': True, 'v1_design_files_preserved': True})
    print('Design artifacts prepared; 0 CLI subprocess/model calls; independent review and root decision pending.')


if __name__ == '__main__':
    main()

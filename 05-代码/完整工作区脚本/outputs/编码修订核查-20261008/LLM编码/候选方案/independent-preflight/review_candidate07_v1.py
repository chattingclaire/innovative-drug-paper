"""Independent read-only review of candidate07 proposal v1. No CLI/model calls.

Only metadata/IDs/hashes are inspected for old real materials. The protected
normalization index remains in memory inside the redactor and is never emitted.
All writes are confined to this independent review directory.
"""
from pathlib import Path
import ast
import contextlib
import datetime
import difflib
import hashlib
import importlib.util
import io
import json
import math
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
BASE = OUT.parent
ROOT = BASE.parents[3]
OLD = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate06-design/revision-v2'
OLD05 = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate05-preparation'
V13 = ROOT / 'outputs/coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md'
V14 = ROOT / 'outputs/coding-revision-20261007-r3/protocol/共用操作说明-v1.4.md'
DIMS = ['S', 'E', 'Ec', 'I', 'F']

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def dump_new(path, value):
    assert not path.exists(), 'Independent review must not overwrite an earlier report.'
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def bindings(paths):
    return [{'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in paths]

def mechanics():
    old_prompt = (OLD / 'candidate06_prompt_PROPOSED.txt').read_text()
    prompt = (BASE / 'candidate07_prompt_PROPOSED.txt').read_text()
    layer = (BASE / 'execution_layer_PROPOSED.txt').read_text()
    marker = '--- 冻结的完整手册（原样） ---'
    marker14 = '--- v1.4共用实质操作说明 ---'
    marker_schema = '--- 最终二元输出结构 ---'
    assert prompt.count(marker) == old_prompt.count(marker) == 1
    suffix_same = prompt.split(marker, 1)[1] == old_prompt.split(marker, 1)[1]
    assert suffix_same
    expected_diff = ''.join(difflib.unified_diff(old_prompt.splitlines(keepends=True), prompt.splitlines(keepends=True), fromfile='candidate06_frozen_prompt', tofile='candidate07_proposed_prompt'))
    assert expected_diff == (BASE / 'candidate06_to_07_prompt.diff').read_text()
    assert prompt.split(marker, 1)[0] == layer.rstrip() + '\n\n'
    v13_embedded = prompt.split(marker, 1)[1].split(marker14, 1)[0].strip()
    v14_embedded = prompt.split(marker14, 1)[1].split(marker_schema, 1)[0].strip()
    assert v13_embedded == V13.read_text().strip()
    assert v14_embedded == V14.read_text().split('## 版本与验证纪律', 1)[0].strip()
    assert 'RECODE25-' not in prompt and '0.80' not in prompt
    unchanged = []
    for older, newer in [
        ('exposed240_inputs_UNCHANGED.jsonl', 'exposed240_inputs_UNCHANGED.jsonl'),
        ('synthetic62_inputs_UNCHANGED.jsonl', 'synthetic62_inputs_UNCHANGED.jsonl'),
        ('synthetic24_inputs_PROPOSED.jsonl', 'synthetic24_inputs_UNCHANGED.jsonl'),
        ('synthetic86_expected_PRIVATE_PROPOSED.json', 'synthetic86_expected_INHERITED_PRIVATE.json'),
        ('manual_rule_basis.json', 'manual_rule_basis_UNCHANGED.json')]:
        assert (OLD / older).read_bytes() == (BASE / newer).read_bytes()
        unchanged.append({'candidate07': str(BASE / newer), 'candidate06': str(OLD / older), 'sha256': sha(BASE / newer), 'byte_identical': True})
    runtime = []
    for name in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']:
        new = BASE / 'runtime-unchanged-v2' / name
        old = OLD / 'runtime-unchanged-v2' / name
        old05 = OLD05 / 'runtime-v2' / name
        assert new.read_bytes() == old.read_bytes() == old05.read_bytes()
        runtime.append({'name': name, 'candidate07': str(new), 'sha256': sha(new), 'byte_identical_to_06_and_05v2': True})
    pairs = read(BASE / 'synthetic20_pairs_PRIVATE_PROPOSED.json')['pairs']
    members = [member for pair in pairs for member in pair['members']]
    assert len(pairs) == 10 and len(members) == 20 and len({m['input']['id'] for m in members}) == 20
    inputs = [json.loads(line) for line in (BASE / 'synthetic20_inputs_PROPOSED.jsonl').read_text().splitlines() if line.strip()]
    assert inputs == [m['input'] for m in members]
    inherited = read(BASE / 'synthetic86_expected_INHERITED_PRIVATE.json')['tests']
    combined = read(BASE / 'synthetic106_expected_PRIVATE_PROPOSED.json')['tests']
    assert len(inherited) == 86 and combined == inherited + members
    redactor_mod = module('independent07_reserved_redactor', ROOT / 'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py')
    redactor = redactor_mod.ReservedContextRedactor()
    scan = redactor.audit_object_no_full_match(read(BASE / 'synthetic20_pairs_PRIVATE_PROPOSED.json'))
    assert scan['no_remaining_full_normalized_reserved_unit_match']
    # Only the ID column is retained or examined here for real development units.
    ids240 = [json.loads(line)['id'] for line in (BASE / 'exposed240_inputs_UNCHANGED.jsonl').read_text().splitlines() if line.strip()]
    assert len(ids240) == len(set(ids240)) == 240
    assert not any(redactor.is_reserved(ident) for ident in ids240)
    plan = read(BASE / 'candidate07_execution_plan_PROPOSED.json')
    assert [run['n'] for run in plan['runs']] == [240, 62, 24, 20]
    assert sum(math.ceil(run['n'] / 25) for run in plan['runs']) == 15
    for run in plan['runs']:
        command = run['future_execution_command_after_separate_root_authorization_only']
        assert command[command.index('--max-attempts') + 1] == '3'
        assert command[command.index('--batch-size') + 1] == '25'
        assert '--start' not in command and '--limit-batches' not in command
        assert sha(command[command.index('--input') + 1]) == command[command.index('--expected-input-sha256') + 1]
    for p in [BASE / 'run_bounded_candidate07.py', BASE / 'audit_candidate07.py', BASE / 'build_candidate07_design.py']:
        ast.parse(p.read_text(), filename=str(p))
    return {'status': 'PASS_MECHANICAL_CHECKS_ONLY', 'complete_v13_embedded': True,
            'v14_substantive_part_embedded': True, 'v14_validation_discipline_not_embedded': True,
            'v14_omission_inherited_from06_not_new07': True, 'complete_suffix_after_manual_marker_byte_identical_to06': suffix_same,
            'exact_diff_reproduced': True, 'prompt_exactly_execution_layer_plus_frozen_suffix': True,
            'no_real_unit_ID_or_numeric_target_in_prompt': True, 'unchanged_sources': unchanged,
            'runtime_dependencies': runtime, 'new20_all_fields_scanned_no_full_normalized_reserved_match': True,
            'reserved_current_unit_ID_intersection_240': 0, 'inherited86_and_all106_expected_composition_exact': True,
            'logical_requests': 15, 'max_pure_technical_attempts': 45, 'scope': [240, 62, 24, 20],
            'source_and_candidate_files_modified_by_review': False, 'model_calls': 0,
            'redaction_limit': 'Only full normalized retained-unit strings; partial quotations and paraphrases are not ruled out.'}

def no_model_technical_tests():
    runner = module('independent07_runner_static_import_only', BASE / 'runtime-unchanged-v2/run_production_v32.py')
    def events(messages):
        return '\n'.join(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': s}}) for s in messages)
    tests = []
    for name, messages, raw, valid in [
        ('single_same_object', ['{"a":1,"b":0}'], {'a': 1, 'b': 0}, True),
        ('key_order_irrelevant', ['{"b":0,"a":1}'], {'a': 1, 'b': 0}, True),
        ('missing_completed_message', [], {'a': 1}, False),
        ('two_completed_messages', ['{"a":1}', '{"a":1}'], {'a': 1}, False),
        ('non_json_message', ['not-json'], {'a': 1}, False),
        ('raw_differs', ['{"a":0}'], {'a': 1}, False),
        ('boolean_is_not_integer', ['{"a":true}'], {'a': 1}, False),
        ('float_is_not_integer', ['{"a":1.0}'], {'a': 1}, False)]:
        result = runner.event_output_binding_audit(events(messages), raw)
        assert (not result['errors']) == valid
        tests.append({'test': name, 'expected_technical_acceptance': valid, 'actual_errors': result['errors'], 'PASS': True})
    wrapper = module('independent07_wrapper_mock_only', BASE / 'run_bounded_candidate07.py')
    mock = OUT / 'mock-wrapper-v1-NO_MODEL'
    mock.mkdir(exist_ok=False)
    fakefreeze = {'nominal_logical_requests': 15, 'max_identical_technical_attempts': 45,
                  'model': 'gpt-5.6-sol', 'reasoning_effort': 'medium', 'files': [], 'source_bindings': [],
                  'independent_preflight_no_blocking_findings': True,
                  'MOCK_ONLY_NOT_AUTHORIZATION_OR_CANDIDATE_FREEZE': True}
    (mock / 'design_freeze.json').write_text(json.dumps(fakefreeze))
    # The test uses fake commands; subprocess.run is intercepted before main.
    fakeplan = {'runs': [{'n': n, 'logical_requests': count,
        'future_execution_command_after_separate_root_authorization_only': ['MOCK_DO_NOT_EXECUTE', '--run-name', 'mock-' + str(n)]}
        for n, count in [(240, 10), (62, 3), (24, 1), (20, 1)]]}
    (mock / 'candidate07_execution_plan_PROPOSED.json').write_text(json.dumps(fakeplan))
    authorization = {'authorized': True, 'design_freeze_sha256': sha(mock / 'design_freeze.json'), 'scope': [240, 62, 24, 20],
                     'model': 'gpt-5.6-sol', 'reasoning_effort': 'medium', 'max_logical_requests': 15,
                     'max_technical_attempts': 45, 'first_technically_valid_only': True,
                     'MOCK_ONLY_NOT_REAL_ROOT_AUTHORIZATION': True}
    auth_path = mock / 'mock_authorization.json'
    auth_path.write_text(json.dumps(authorization))
    original_argv, original_run = sys.argv, wrapper.subprocess.run
    calls = []
    def intercept(command, **kwargs):
        calls.append(command)
        return None
    wrapper.HERE = mock
    wrapper.PYTHON = Path(sys.executable)
    wrapper.subprocess.run = intercept
    outcomes = []
    def exercise(name, args, should_fail, expected_calls):
        calls.clear()
        sys.argv = ['MOCK_WRAPPER'] + args
        failure = None
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                wrapper.main()
        except AssertionError as exc:
            failure = str(exc)
        assert (failure is not None) == should_fail and len(calls) == expected_calls
        outcomes.append({'test': name, 'assertion_rejected': failure is not None, 'mock_subprocess_count': len(calls), 'PASS': True})
    try:
        exercise('default_has_no_subprocess_or_CLI', [], False, 0)
        exercise('execute_without_authorization_rejected', ['--execute'], True, 0)
        authorization['design_freeze_sha256'] = '0' * 64
        auth_path.write_text(json.dumps(authorization))
        exercise('wrong_freeze_hash_rejected', ['--execute', '--authorization-file', str(auth_path)], True, 0)
        authorization['design_freeze_sha256'] = sha(mock / 'design_freeze.json')
        auth_path.write_text(json.dumps(authorization))
        exercise('matching_synthetic_authorization_only_four_scope_commands', ['--execute', '--authorization-file', str(auth_path)], False, 4)
        (mock / 'runtime-unchanged-v2' / 'mock-240').mkdir(parents=True)
        exercise('existing_scope_rejected_before_any_subprocess', ['--execute', '--authorization-file', str(auth_path)], True, 0)
    finally:
        wrapper.subprocess.run = original_run
        sys.argv = original_argv
    return {'status': 'PASS_NO_MODEL_SYNTHETIC_TECHNICAL_TESTS', 'event_binding': tests, 'wrapper_mock_tests': outcomes,
            'real_CLI_invocations': 0, 'real_model_calls': 0,
            'limits': ['No real root authorization or package freeze generated.', 'Real first-valid attempt selection inherited unchanged and statically inspected; not a new real execution.']}

def semantic_review():
    pairs = read(BASE / 'synthetic20_pairs_PRIVATE_PROPOSED.json')['pairs']
    # Independent per-dimension rationales; values are not inferred from a target score.
    reasons = {
        '01-A': ['无药物损害/风险内容。', '资料排版不提出效果证据要求。', '无药费/支付资源。', '原创研发团队是对象；当前只发布递交文件的排版说明，未提供实体研发支持。', '文件递交便利无治疗获取/患者负担/管理难度。'],
        '01-B': ['无风险内容。', '科学设计建议没有给定效果判断用途。', '专家配置不是药物治疗/支付费用。', '明确原创研发对象、药学专家资源与研发方案技术指导，支持research_support；对象身份不另计attribute。', '无治疗获取或管理难度。'],
        '02-A': ['无风险内容。', '无治疗效果内容。', '当前药物治疗支出与预算阈值直接支持Ec，不把它写成已发生支付。', '无创新依据。', '核验父句只准提交续约申请，是否续签另定；不补保障继续。'],
        '02-B': ['无风险内容。', '无治疗效果内容。', '相同药物治疗支出预算阈值支持Ec。', '无创新依据。', '父句使当前预算条件决定既有医保药品协议续签并有效十八个月，明确保障连续，access成立。'],
        '03-A': ['毒性主题仅能消解问题背景；当前仅规定沟通形式和将来修订指引，没有安全评价/证据要求。', '无效果内容。', '无药费内容。', '无创新研发支持对象/内容。', '无保障获取、负担或管理难度。'],
        '03-B': ['逐项分析毒性发生原因并确定风险控制，是安全评价和控制；不要求既有肯定风险结果。', '无效果内容。', '无药费内容。', '未涉及创新。', '风险控制不是当然的管理难度；没有负担/障碍依据。'],
        '04-A': ['未讨论成人患者的风险。', '确诊成人只是保障适用条件，并非疗效。', '保障适用人群限制本身未陈述价格/支付标准/费用责任。', '无产品改变/创新支持。', '拟定具体药物保障人群限制实质讨论覆盖范围，access成立；无需已经实施。'],
        '04-B': ['无风险内容。', '无效果内容。', '基金承担药费70%是独立费用责任。', '无创新内容。', '具体保障人群限制支持access；未直接讨论患者支付能力/药费负担，不能自动添加affordability。'],
        '05-A': ['单位储备资金安全不属药物风险。', '无效果内容。', '档案室运行和单位储备资金未联系药物治疗/支付资源。', '无创新内容。', '无药物获取/负担/管理难度。'],
        '05-B': ['基金可持续不是药物安全。', '无效果内容。', '药品支付预算受到医保基金可持续使用约束，直接有药物支付资源含义，无需具体金额。', '无创新内容。', '未确定药品保障范围/患者负担或获取缺口，仅基金资源约束不自动计F。'],
        '06-A': ['无风险内容。', '无效果内容。', '申请扩围手续没有药费责任/支付标准。', '无创新内容。', '愿望/申请者预约受理时段只是办理动作，未提出具体覆盖人群、药品范围或结果。'],
        '06-B': ['无风险内容。', '新增适应症名称不等于效果评价或推荐。', '保障范围纳入未附经济责任。', '“新增适应症”可指产品适应症相对既有状态发生具体变化，也可能仅指新增保障对象；未说明产品属性是否变化。I0不宜作为无争议必过期望。', '当前明确拟把具体适应症纳入保障，access成立；计划性不排除F。'],
        '07-A': ['归档处方扫描件没有药物风险内容。', '无效果内容。', '无药费内容。', '信息系统/归档不属药物创新。', '档案室—统计室归档链条不是患者获取药物渠道。'],
        '07-B': ['无风险内容。', '无效果内容。', '协议药房身份未另给费用责任。', '平台形式不属药物创新。', '开方机构—药房处方传送—患者领药形成实际常规获取渠道，access成立。'],
        '08-A': ['年龄和减量本身不陈述药物损害。', '剂量调整无给定效果依据。', '无药费内容。', '剂量减半不陈述产品创新/改良。', '一般给药量调整未讨论管理复杂性或监测负担，不计clinical_management。'],
        '08-B': ['每日监测未明确针对药物损害，不能据监测词推S。', '无效果判断用途。', '管理负担不是当然经济负担。', '无创新内容。', '明确评价每日监测管理负担及社区药房完成难度，clinical_management成立。'],
        '09-A': ['无风险内容。', '无效果内容。', '保险机构承担相关药费直接支持Ec。', '无创新内容。', '该药被保障覆盖支持access；句中未独立讨论患者支付能力或药费负担，不由Ec/覆盖自动推出affordability。'],
        '09-B': ['无风险内容。', '无效果内容。', '减免个人药费直接涉及费用责任。', '无创新内容。', '覆盖支持access；患者难以负担自付药费及相应减免独立支持affordability，不要求补充真实贫困证明。'],
        '10-A': ['无风险内容。', '比较临床终点反映治疗获益的能力，明确效果判断用途，E成立，不要求已经有效。', '专家资源不是药物治疗/支付费用。', '原创研发团队获得专家与设计建议支持research_support；未评价产品创新属性，不另加attribute。', '终点比较不等于治疗获取或管理难度。'],
        '10-B': ['针对药物毒性风险提出监测方案，S成立。', '监测目的为毒性风险，未另给效果内容。', '无药费内容。', '原创研发团队获得专家和研发监测方案建议，支持research_support，不另加attribute。', '监测方案本身不评价复杂性/负担，不自动计clinical_management。'],
    }
    rows = []
    for pair in pairs:
        for member in pair['members']:
            ident = member['input']['id']
            key = ident.removeprefix('C07-PAIR-')
            independently_supported = dict(member['labels'])
            if key == '06-B':
                independently_supported['I'] = None
            row = {'id': ident, 'constructed_input': member['input'], 'author_expected_labels': member['labels'],
                   'independent_labels': independently_supported,
                   'independent_per_dimension_reason': dict(zip(DIMS, reasons[key])),
                   'F_subtypes_supported': member['fairness_subtypes'],
                   'I_subtypes_supported': member['innovation_subtypes'],
                   'S_quality_basis_supported': 'no_quality_basis',
                   'manual_basis': pair['manual_basis'],
                   'status': 'BLOCKING_AMBIGUOUS_I0_EXPECTATION' if key == '06-B' else 'SUPPORTED_UNDER_FIXED_MANUAL',
                   'actual_model_output_read': False}
            if key == '06-B':
                row.update({'I_acceptable_interpretations_without_rewording': [0, 1],
                            'if_I1_supported_subtype': 'attribute',
                            'additional_manual_basis': ['v1.3:142', 'v1.4:14'],
                            'remedy': 'Use clearly existing unchanged product/indication coverage as the F-only control, or isolate the present sentence as an I boundary; do not change gold after seeing model output.'})
            rows.append(row)
    return rows

def main():
    paths = [BASE / name for name in ['execution_layer_PROPOSED.txt', 'candidate07_prompt_PROPOSED.txt',
        'candidate06_to_07_prompt.diff', 'synthetic20_pairs_PRIVATE_PROPOSED.json', 'synthetic20_inputs_PROPOSED.jsonl',
        'synthetic106_expected_PRIVATE_PROPOSED.json', 'predeclared_acceptance_PROPOSED.json',
        'candidate07_execution_plan_PROPOSED.json', 'run_bounded_candidate07.py', 'audit_candidate07.py',
        'prompt_conflict_and_mechanism_audit_PRIVATE.json']] + [V13, V14]
    start_bindings = bindings(paths)
    mechanical = mechanics()
    technical = no_model_technical_tests()
    controls = semantic_review()
    assert bindings(paths) == start_bindings, 'Proposal changed during independent review; do not seal a mixed snapshot.'
    result = {'status': 'PREEXECUTION_REVIEW_V1_BLOCKING_FINDINGS_NOT_AUTHORIZATION',
        'reviewed_at_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'reviewer': 'independent AI subagent validation_state_oct8; not a new blind human coder',
        'source_bindings': start_bindings, 'scope': 'Complete new execution layer and its exact diff; 20 constructed controls all five dimensions/subtypes; predeclared gates and static technical boundary.',
        'mechanical': mechanical, 'no_model_technical_tests': technical, 'controls': controls,
        'prompt_review': [
            {'item': 'current_proposition_and_scope', 'status': 'SUPPORTED', 'reason': 'Explicitly retains plans, negatives, conditions, direct parent predicates and required substantive references while preventing theme/identity inheritance.'},
            {'item': 'five_dimension_boundaries', 'status': 'SUPPORTED', 'reason': 'S/E/Ec/I/F exclusions are paired with positive content; no requirement for realized positive effects, numeric fees, new drug targets or wider coverage.'},
            {'item': 'I_research_support_actor_explanation', 'status': 'INTERPRETATION_NOTE', 'reason': 'Who gives what support is a reason-writing aid, not an added condition that a named actor must appear verbatim. Given context may resolve an implicit actor. Do not mark missing names as automatic I0.'},
            {'item': 'F_access_affordability_management_subtypes', 'status': 'SUPPORTED', 'reason': 'Independent evidence is required for each subtype; coverage/insurance responsibility alone does not automatically express patient payability; monitoring alone does not express management difficulty.'},
            {'item': 'manual_completeness_wording', 'status': 'PRECISION_NOTE', 'reason': 'The full v1.3 and v1.4 substantive part are embedded. The v1.4 validation-discipline appendix is absent as in06; suffix is unchanged. Do not claim two complete files are byte-embedded.'},
            {'item': 'conflict_causality', 'status': 'SUPPORTED_LIMIT', 'reason': 'One earlier run cannot identify a causal prompt mechanism. Proposal keeps the mechanism as a hypothesis and forbids metric selection.'}],
        'blocking_findings': [
            {'id': 'SEM-01', 'file': str(BASE / 'synthetic20_pairs_PRIVATE_PROPOSED.json'), 'unit': 'C07-PAIR-06-B',
             'finding': 'Expected I0 is ambiguous because the constructed sentence says new indication. All other dimensions are supportable; F1 is explicit.',
             'required_before_freeze': 'Make the constructed F-positive control unambiguous without product-attribute change, or isolate its I interpretation as a boundary before any07 output; synchronize input, expectations and plan hashes.'},
            {'id': 'AUDIT-01', 'file': str(BASE / 'audit_candidate07.py'),
             'finding': 'Current all_changes selection compares labels only. A subtype, safety-quality marker, rationale or evidence change with identical labels is not selected. all240 retains full rows but the change-review manifest alone is incomplete.',
             'required_before_freeze': 'Define and implement the full output change scope consistent with the predeclared review, at minimum separately tracking all F/I subtype and S-quality changes. Do not call label-identical rows wholly unchanged. State whether explanation-only changes receive all240 review or a separate complete diagnostic.'}],
        'predeclared_gates_review': {'status': 'SEMANTIC_GATES_SUPPORTED_SUBJECT_TO_FINDINGS',
            'eight_errors_and_nine_fixed_cells': 'Working reviewer judgments preserved as development hypotheses, not gold; their old real text was not reopened in this preflight.',
            'boundaries': '11 real boundaries and C05-NEW-019 remain unforced; previous008 affordability and034 reason-precision objections retained.',
            'synthetic_scope': 'All106 must receive full five-dimension/reason/evidence/subtype review after the single run; matching expected labels alone is insufficient.',
            'release': 'Any confirmed new error or unresolved gate fails safe-improvement; no automatic full corpus or manuscript adoption.'},
        'read_boundaries': {'old240': 'IDs/hash only, no manual semantic reading in this preflight',
            'reserved267': 'Mechanical in-memory normalization matching only; no protected text/prediction/labels displayed',
            'A_B_first_labels_or_scores': 'Not read', 'old_86_expected': 'Exact-byte/composition checks only, not newly semantically certified'},
        'candidate_freeze_exists_at_review': (BASE / 'design_freeze.json').exists(),
        'real_CLI_invocations': 0, 'real_model_calls': 0, 'source_files_modified': False,
        'limits': ['This is a development design review, not new human reliability or independent machine validity.',
                   'No claim that any model result will be correct or that this improves a metric.',
                   'No journal-acceptance guarantee.', 'Final authorization and a final dependency-closed freeze remain the root reviewer\'s separate steps.']}
    dump_new(OUT / 'candidate07_independent_preflight_v1.json', result)
    text = '# 候选07独立执行前审查 v1\n\n结论：当前快照有两项阻断，尚不能将其记作无阻断冻结或执行授权。独立审查未调用 CLI/模型，未改准备文件。\n\n'
    text += '1. C07-PAIR-06-B 的“新增适应症”使 I0 预期不够单一。F1 明确；v1.3:142/v1.4:14也允许明确产品属性改变支持I，不能把这条当成无争议I0必过控制。须在任何07输出前改成产品属性保持不变的具体保障范围构造，或独立登记I边界。\n'
    text += '2. 当前 audit 的 all_changes 只筛五标签差异；五标签相同而子类、质量标记或解释变化会漏出变化投影。须与“任一变化”预声明统一，至少完整跟踪子类及质量标记变化，并明示解释变化的完整复审范围。all240保留全输出不等于all_changes已穷尽。\n\n'
    text += '其余19条控制和该条另外四维均有手册依据；逐维理由与子类详见JSON。未用目标分数、A/B标签或机器一致度判断。\n\n'
    text += '机械检查确认完整v1.3、v1.4实质操作部分、schema及引文footer相对06未变；v1.4末尾验证纪律从06起未入prompt，不能表述成两份全文均完整嵌入。旧240/62/24、继承86预期、runner/schema/validator字节一致。新20未匹配267完整归一原文，当前240 ID与267交集0；这不撤销既往上下文暴露登记。\n\n'
    text += '15逻辑请求、每请求最多3次纯技术尝试、合计最多45次；真实模型参数gpt-5.6-sol/medium在不变runner中。8个event/raw绑定合成测试及5个wrapper拦截测试通过，实际CLI/模型0次。默认wrapper仅打印；执行需独立root授权绑定最终freeze SHA。静态检查未见参考标签/期望进入请求、按语义分数重试或拼接结果。最终freeze尚未产生；此报告不授权执行。\n\n'
    text += '本审查是AI开发复核，不是真人新盲评、独立机器效度或录用保证。原首次标签、用户事后真人复核与本轮agent意见须继续分开保存。\n'
    (OUT / '候选07独立执行前审查-v1.md').write_text(text)
    dump_new(OUT / 'preflight_v1_seal.json', {'report_files': bindings([OUT / 'candidate07_independent_preflight_v1.json', OUT / '候选07独立执行前审查-v1.md', Path(__file__).resolve()]), 'model_calls': 0})
    print(json.dumps({'status': result['status'], 'controls': len(controls), 'blocking_findings': len(result['blocking_findings']),
                      'report': str(OUT / 'candidate07_independent_preflight_v1.json'), 'report_sha256': sha(OUT / 'candidate07_independent_preflight_v1.json'), 'model_calls': 0}, ensure_ascii=False))

if __name__ == '__main__':
    main()

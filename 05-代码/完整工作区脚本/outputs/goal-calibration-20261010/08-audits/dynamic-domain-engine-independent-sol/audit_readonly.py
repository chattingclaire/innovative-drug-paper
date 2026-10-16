#!/usr/bin/env python3
"""Independent byte/AST/contract reception; no engine or control execution."""
from pathlib import Path
import ast
import datetime
import difflib
import hashlib
import json

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
CANDIDATE = ROOT / '07-statistics/prospective-dynamic-domain-engine-sol'
EXPECTED_SEAL = '612e3948e0c48c551a4feb7479e2fc813540124bbbbca70933813c0f52642e7b'


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def verify(member):
    actual = binding(member['path'])
    assert actual == member, member['path']
    return actual


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(name, data):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def code_quote(path, marker, after=0):
    lines = Path(path).read_text(encoding='utf-8').splitlines(keepends=True)
    at = [i for i, line in enumerate(lines) if marker in line]
    assert len(at) == 1, marker
    i = at[0]
    return {'binding': binding(path), 'line_1based': i+1,
            'quote': ''.join(lines[i:i+1+after])}


assert not (OUT / 'output-seal.json').exists()
owner_seal = binding(CANDIDATE / 'output-seal.json')
assert owner_seal['sha256'] == EXPECTED_SEAL and owner_seal['bytes'] == 48509
sealed = load(owner_seal['path'])
members = [verify(m) for m in sealed['output_members']]
assert len(members) == 140
inputs = load(CANDIDATE / 'input-bindings.json')['frozen_inputs']
input_readback = {key: verify(value) for key, value in inputs.items()}
assert len(input_readback) == 23
old_handoff_seal = load(inputs['old200_adapter_seal']['path'])
old_handoff_members = [verify(m) for m in old_handoff_seal['output_members']]
assert len(old_handoff_members) == 40
registry = load(CANDIDATE / 'ROOT-scope-registry.UNADOPTED.json')
assert registry['registrations'] == {}
wrapper = load(inputs['LLM_frame_ids']['path'])
source_ids = wrapper['approved_record_ids']
assert len(source_ids) == len(set(source_ids)) == 4481
order_sha = hashlib.sha256(('\n'.join(source_ids)+'\n').encode('utf-8')).hexdigest()
assert order_sha == wrapper['frame_order_UTF8_LF_sha256']
assert wrapper['preserves_original_FRAME4481_order'] is True
write('sealed-input-reception.json', {'owner_seal': owner_seal, 'candidate140_members': members,
      'upstream23_bindings_readback': input_readback, 'old_handoff40_members_unchanged': old_handoff_members,
      'approved_original_wrapper_metadata': {'binding': inputs['LLM_frame_ids'], 'unique_N': 4481,
                                           'UTF8_LF_order_sha256': order_sha},
      'actual_registry': registry, 'actual_approved_scope_N': 0,
      'input_files_raw_SHA_read_not_label_content_read': True})

snapshot = OUT / 'code-snapshot'
snapshot.mkdir(exist_ok=False)
for name in ('metrics_engine.py', 'scope_admission.py', 'frozen_year_core.py'):
    with (snapshot / name).open('xb') as stream:
        stream.write((CANDIDATE / name).read_bytes())
    assert binding(snapshot / name)['sha256'] == binding(CANDIDATE / name)['sha256']

engine_path = CANDIDATE / 'metrics_engine.py'
core_path = CANDIDATE / 'frozen_year_core.py'
admission_path = CANDIDATE / 'scope_admission.py'
old_path = Path(inputs['engine']['path'])
assert binding(core_path)['sha256'] == inputs['year_engine']['sha256']
engine_source = engine_path.read_text(encoding='utf-8')
core_source = core_path.read_text(encoding='utf-8')
admission_source = admission_path.read_text(encoding='utf-8')
engine_tree = ast.parse(engine_source)
core_tree = ast.parse(core_source)


def functions(tree):
    return {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}


def dump(node):
    return ast.dump(node, include_attributes=False)


ef, cf = functions(engine_tree), functions(core_tree)
unchanged = [name for name in cf if name in ef and dump(ef[name]) == dump(cf[name])]
changed = [name for name in cf if name not in ef or dump(ef[name]) != dump(cf[name])]
assert len(unchanged) == 27 and changed == ['prepare', 'review_eligibility', 'analyze']


def constants(tree):
    return {n.targets[0].id: n.value for n in tree.body
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}


ec, cc = constants(engine_tree), constants(core_tree)
constant_checks = {name: dump(ec[name]) == dump(value) for name, value in cc.items()}
assert all(constant_checks.values())
guards = [line for line in core_source.splitlines()
          if ('full_4481_audit' in line and 'domain_N' in line)
          or ('remaining_1444' in line and 'domain_N' in line)]
assert len(guards) == 2 and all(line in engine_source for line in guards)
with (OUT / 'independent-core-diff.patch').open('x', encoding='utf-8') as stream:
    stream.writelines(difflib.unified_diff(core_source.splitlines(keepends=True),
                                         engine_source.splitlines(keepends=True),
                                         fromfile='frozen_year_core.py', tofile='metrics_engine.py'))
write('independent-AST-preservation.json', {'candidate_engine': binding(engine_path),
      'year_core': binding(core_path), 'original_core': binding(old_path),
      'unchanged27_original_functions': unchanged, 'changed_admission_only_functions': changed,
      'original_constants_AST_equal': constant_checks, 'legacy1444_3037_guard_lines_identical': guards,
      'original_math_and_annual_functions_executed_by_this_audit_N': 0,
      'candidate_diff_reviewed': binding(OUT / 'independent-core-diff.patch'),
      'registered_execution_5000_seed20261010_single_category_preserved': True,
      'new_CI_gate_or_estimator_N': 0})

plan = load(CANDIDATE / 'controls-fixed-before-execution.json')
first = load(CANDIDATE / 'control-results-first.json')
final = load(CANDIDATE / 'control-results-final.json')
assert len(plan['cases']) == len(first['cases']) == len(final['cases']) == 29
case_reception = []
for fixed, early, last in zip(plan['cases'], first['cases'], final['cases']):
    assert fixed['case_id'] == early['case_id'] == last['case_id']
    assert fixed['expected'] == early['expected'] == last['expected']
    verify(fixed['input_binding'])
    case_reception.append({'fixed_case': fixed, 'first_result': early, 'final_result': last,
                           'fixed_expected_preserved': True})
wrapper_plan = load(CANDIDATE / 'wrapper-control-fixed-before-execution.json')
wrapper_result = load(CANDIDATE / 'wrapper-control-result.json')
assert wrapper_result['passed'] and wrapper_plan['expected'] == wrapper_result['expected']
stage_plan = load(CANDIDATE / 'stage-helper-controls-fixed-before-execution.json')
stage_results = load(CANDIDATE / 'stage-helper-control-results.json')
assert len(stage_plan['cases']) == len(stage_results['cases']) == 2
for fixed, observed in zip(stage_plan['cases'], stage_results['cases']):
    assert fixed['case_id'] == observed['case_id'] and fixed['expected'] == observed['expected']
    assert observed['passed']
cli_results = load(CANDIDATE / 'cli-negative-results.json')
assert cli_results['both_rejected_before_output'] and len(cli_results['results']) == 2
for result in cli_results['results']:
    assert result['returncode'] != 0
    output_path = Path(result['command'][result['command'].index('--output')+1])
    assert not output_path.exists()
history = load(CANDIDATE / 'execution-history-and-archives.json')
for epoch in history['executions']:
    verify(epoch['execution_report_binding'])
    for item in epoch['archived_code_bindings'].values():
        verify(item)
assert first['passed_N'] == 28 and first['failed_N'] == 1 and final['passed_N'] == 29
failure = [x for x in first['cases'] if not x['passed']]
assert failure[0]['error'] == {'type': 'KeyError', 'message': "'Precision'"}
write('owner-control-reception.json', {'status': 'existing_sealed_controls_received_not_rerun',
      '29_fixed_cases': case_reception, 'additional_wrapper_plan': wrapper_plan,
      'additional_wrapper_result': wrapper_result, 'additional_two_stage_helper_plan': stage_plan,
      'additional_two_stage_helper_results': stage_results, 'two_CLI_refusal_results': cli_results,
      'first28_of29_failure_preserved': failure,
      'first_failure_is_reader_A_vs_B_has_no_classification_Precision_not_estimator_defect': True,
      'original_four_execution_rounds_archived_code_and_reports_SHA_equal': True,
      'all_existing_controls_are_synthetic_or_blank_not_actual_project_validation': True,
      'controls_rerun_by_this_audit_N': 0})

chain = {
    'admit_receipt_to_metadata_binding': code_quote(admission_path, "seal.get('joined_projection_sha256')==r.get('joined_projection_sha256')"),
    'current_records_canonical_projection_definition': code_quote(engine_path, 'def projection_hash(records,method):', 1),
    'core_prepare_recalculates_current_active_records': code_quote(engine_path, "meta['input_seals'][method].get('joined_projection_sha256')!=projection_hash(records,method)", 1),
    'prepare_admits_then_checks_current_rows_before_return': code_quote(engine_path, 'registered_scope=_admit_registered_scope(payload)'),
    'canonical_projection_functions_unchanged_AST': all(name in unchanged for name in ('canonical_hash', 'projection_hash', '_validate_metadata')),
    'old_handoff_initial_A_B_projection_construction': code_quote(inputs['old200_adapter']['path'], "for side in ('A','B'):meta['input_seals'][side]="),
    'old_handoff_active_method_projection_construction': code_quote(inputs['old200_adapter']['path'], "if method in rawbindings:meta['input_seals'][method]="),
    'assessment': 'ROOT-received projection string -> metadata input_seal -> unchanged prepare recomputation on current assigned records; changed current labels/status do not retain equality.',
    'admit_alone_is_not_a_complete_ledger_statistics_verifier': True,
    'only_full_engine_prepare_analyze_chain_supports_current_ledger_binding': True,
    'new_projection_control_N': 0,
    'ROOT_instruction_no_new_control_after_full_chain_confirmed': True,
}
write('projection-binding-full-chain.json', chain)

stage_review = {
    'scope_pre_freeze': 'Complete formal-test scope must freeze both machine algorithm/prompt/settings before new A/B test feedback. This is shared registration identity, not proof of machine output or adjudication.',
    'ROOT_clarification_received': '无条件两机器version/协议artifact_seals是完整正式检验scope登记前置，只要求版本/协议事先固定，不要求human_first已产生机器全量输出或裁定参照。',
    'scope_version_validation': code_quote(admission_path, "versions={k:load(descriptor[k])", 8),
    'scope_common_artifact_seals': code_quote(admission_path, "for key,dkey in (('common_manual','common_manual')", 2),
    'stage_actual_receipts_selection': code_quote(admission_path, "stage=meta.get('analysis_stage','combined');active=", 1),
    'active_only_original_reception_loop': code_quote(admission_path, 'for method in active:', 5),
    'freeze_helper_source': code_quote(admission_path, 'def validate_stage_attestations(metadata):', 12),
    'human_first_active_methods': ['A','B'],
    'human_first_does_not_require_reference_rule_LLM_actual_result_receipts': True,
    'machine_reference_active_methods': ['reference','rule','LLM'],
    'machine_reference_does_not_require_A_B_actual_first_submission_receipts': True,
    'old_core_project_review_remains_whole_project_and_can_list_inactive_missing_prerequisites': True,
    'core_review_eligibility_preservation_is_not_stage_execution_refusal': True,
    'two_stage_helpers_are_not_full_actual_positive_path_proof': True,
    'actual_ROOT_registered_stage_positive_execution_N': 0,
}
write('stage-dependency-review.json', stage_review)

scope_review = {
    'conclusion': 'No self-consistent unapproved-input bypass found in the sealed full admission chain; real new-scope registry is empty and code-SHA pinned. Future approved positive path not exercised.',
    'registry_SHA_anchor': code_quote(admission_path, "REGISTRY_SHA256='"),
    'actual_registry_before_descriptor_and_records': code_quote(admission_path, "require(binding(REGISTRY_PATH)['sha256']==REGISTRY_SHA256", 10),
    'approved4481_external_wrapper_anchor': code_quote(admission_path, 'require(approved_binding==ORIGINAL_FRAME_IDS_BINDING', 8),
    'checked_contracts': [
        'exact4481 unique approved original order and per-record source-bundle identity',
        'common-material identity manifest same frame order/SHA; actual source truth remains ROOT review',
        'both domains nonempty and exact partition; one family cannot span domains; freeze binding matches',
        'exact estimand membership with no zero-pi omissions; all positive N counted from members',
        'pure department/domain stratum, integer positive n, noncensus n>=2',
        'original assigned draw n/order/IDs and exact rational pi=n/N,weight=N/n',
        'ROOT registry authority and reviewed scope/design receipts; caller booleans cannot create registry entry',
        'scope/material/machine versions pre-fixed; actual active original bytes/identity/blinding/independence receipts separate',
        'complete first4481 machine terminal reception, failure/null retained, only when machines active',
        'optional exact4481 registered year metadata; current per-row year equality and unchanged core projection',
    ],
    'temporal_randomization_and_identity_truth_boundary': 'Statuses/SHA bind ROOT-reviewed records; engine does not independently certify historical dates, random draw provenance, human identity, material truth or text-family truth. Actual immutable ROOT adoption is required; none exists here.',
    'legacy_scope_boundary': 'Old1444/3037 math/guards are preserved; old direct-engine behavior does not replace historical handoff/version admission and cannot qualify later rule versions using old200.',
    'additional_independent_negative_controls_N': 0,
    'reason_no_expansion': 'Existing29+wrapper+2helper+2CLI cover concrete rejection gates; alleged projection risk is rejected by unchanged downstream core, and shared machine protocol freeze is ROOT-confirmed scope prerequisite.',
}
write('scope-admission-review.json', scope_review)

report = {'status': 'independent_readonly_candidate_reception_complete_unadopted',
          'owner_output_seal': owner_seal, 'sealed_candidate_members_N': 140,
          'sealed_upstream_bindings_N': 23, 'unchanged_old_handoff_members_N': 40,
          'unchanged_math_year_functions_N': 27, 'all_original_constants_AST_identical': True,
          'legacy1444_3037_guards_preserved': True,
          'received_owner_controls': {'original29_final_passed': 29, 'first_original29_passed': 28,
                                      'first_original29_failed_preserved': 1, 'wrapper_passed': 1,
                                      'stage_helpers_passed': 2, 'CLI_refusals_before_metric_files': 2},
          'independent_new_tests_or_analysis_N': 0,
          'new_actual_scope_or_draw_or_human_reference_statistics_N': 0,
          'actual_registered_positive_path_checked': False,
          'whole4481_source_order_metadata_only_N': 4481,
          'read_scope': ['140 member bytes and 23 frozen upstream bytes for SHA verification',
                         'candidate admission full source; candidate/year engine AST and additive diff',
                         'original approved4481 wrapper IDs/order only',
                         'fixed owner control plan and first/final records, wrapper/helpers/CLI/error archives',
                         'owner test driver source to distinguish tested assertions and helper-only bounds',
                         'old handoff projection-construction lines and sealed-member byte preservation',
                         'contracts/README; statistical contract metric definitions and fixed constants'],
          'not_read_or_executed': ['main fullLLM partial labels', 'owner actual77/800 prediction values',
                                  'policy body reclassification', 'real human submissions/adjudication',
                                  'real year metrics', 'new draws or rule judges',
                                  'hidden12 candidate execution or disclosure'],
          'mathematical_reception_not_formal_validation': True,
          'owner_files_modified': False}
write('report.json', report)
with (OUT / 'README.txt').open('x', encoding='utf-8') as stream:
    stream.write('动态域候选只读独审已完成。140成员、23既有上游字节绑定和旧handoff40成员一致；27原数学/年度函数及6组统计常量AST相同，只有prepare/review_eligibility/analyze接入附加，旧1444/3037守卫保留。\\n'
                 '已接收原29控制及另1wrapper、2stage helper、2CLI负例，无复跑。原首轮28/29的Precision读取KeyError及代码归档保留。两个CLI在指标文件创建前拒绝；helper通过不是实际scope或真人正路径。\\n'
                 '当前空ROOT registry由代码SHA锚定，实际新域均不能靠自洽输入批准。原4481 wrapper同时由固定路径/字节/SHA锚定；注册框、层成员、原draw、精确概率与源年度映射受同一登记绑定。身份、时间、抽样来源和原件真值须ROOT凭实际材料审定，SHA不自行认证。\\n'
                 'projection字符串由admit绑定ROOT receipt，再由未改prepare按当前active records重算。只改ledger不能保留封存投影等式；没有因此新增控制。admit单独不是完整指标接收入口。\\n'
                 '阶段实际原提交分别为human_first的A/B与machine_reference的reference/rule/LLM。两机器算法/prompt/设置的预冻结是ROOT确认的共同scope前置，避免使用新A/B反馈调参；human_first不要求实际机器输出或裁定receipt。旧整体project_review继续列全项目缺口，不表示stage运行被门槛分数阻断。\\n'
                 '本审计无新增测试、draw、真实真人/参照/统计或年度指标，不读主LLM部分标签，不改owner。隐藏12预期不改、未执行、未公开，等最终joint-v3 seal。\\n')
write('final-readback.json', {'candidate140_unchanged': [verify(m) for m in members],
                            'own_outputs_before_seal': [binding(p) for p in sorted(OUT.rglob('*')) if p.is_file()],
                            'additional_execution_N': 0, 'status': 'pass'})
own_members = [binding(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
write('output-seal.json', {'status': 'sealed_independent_readonly_dynamic_candidate_reception',
                          'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          'bound_owner_output_seal': owner_seal, 'output_members': own_members,
                          'seal_self_excluded': True, 'actual_results_or_formal_validation': False})
for member in own_members:
    verify(member)
print(json.dumps({'output_seal': binding(OUT / 'output-seal.json'), 'own_members_N': len(own_members),
                  'candidate140_readback': True, 'unchanged_functions_N': 27,
                  'additional_controls_or_actual_statistics_N': 0}, ensure_ascii=False))

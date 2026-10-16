#!/usr/bin/env python3
"""Seal finite independent audit, without rerunning any control or statistic."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
OWNER=ROOT/'07-statistics/human200-machine-reference-handoff-sol'


def bind(path):
    p=Path(path).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def load(path):return json.loads(Path(path).read_bytes())


def write(name,value):
    with (OUT/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


src=(OWNER/'handoff.py').read_text();tree=ast.parse(src)
locations={node.name:{'start_line':node.lineno,'end_line':node.end_lineno}
           for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
inputs=load(OUT/'sealed-input-verification.json')
plan=load(OUT/'controls12-fixed-before-execution.json')
execution=load(OUT/'execution-results.json')
summary=load(OUT/'execution-summary.json')
io=load(OUT/'execution-scope-and-IO-receipt.json')
assert summary['case_N']==12 and summary['matched_N']==11 and summary['mismatched_N']==1
failed=[r for r in execution['cases'] if not r['matched']]
assert len(failed)==1 and failed[0]['name']=='self_consistent_foreign_wrapper_not_approved'
assert failed[0]['actual']['outcome']=='accept'
assert failed[0]['actual']['record_N']==4481
assert failed[0]['actual']['unapproved_ID_N']==1
assert io['guards_not_called'] is True
for b in inputs['all_verified_bindings']:assert bind(b['path'])==b
assert bind(OWNER/'output-seal.json')==plan['owner_seal_binding']
assert bind(OWNER/'handoff.py')==plan['code_binding']
for b in load(OUT/'pre-execution-seal.json')['output_members']:assert bind(b['path'])==b

static={
    'status':'read_only_call_graph_and_contract_review_no_further_execution',
    'code_binding':plan['code_binding'],'function_locations':locations,
    'runtime_frozen_frame_calls':[
        {'caller':'initial_projection','manifest_origin':'load(verify(c.frozen_inputs.LLM_manifest))'},
        {'caller':'rule_projection','manifest_origin':'load(verify(c.frozen_inputs.LLM_manifest))'},
        {'caller':'llm_projection','manifest_origin':'terminal_inventory_gate returns load(verify(c.frozen_inputs.LLM_manifest))'},
    ],
    'sealed_manifest_to_approved_wrapper':{
        'manifest_binding_equals_review_and_contract_fixed_binding':True,
        'manifest_ordered_source_ids_equals_frozen_LLM_frame_ids_binding':True,
        'verified_original_wrapper_binding':load(OWNER/'bindings.json')['frozen_inputs']['LLM_frame_ids'],
        'unique4481_and_exact504_batch_flattened_original_order':True,
        'UTF8_LF_order_digest':inputs['approved_UTF8_LF_order_sha256'],
        'canonical_JSON_coverage_digest':inputs['campaign_JSON_canonical_coverage_order_sha256'],
        'two_digest_formats_are_not_a_contradiction':True,
    },
    'observed_helper_limit':{
        'function':'frozen_frame','scope':'standalone callable supplied-manifest helper',
        'actual_failure_case':failed[0]['name'],
        'actual_acceptance':'4481 unique IDs including one unapproved synthetic ID; file binding, LF digest and batch order self-consistent',
        'missing_internal_anchor':'helper does not compare supplied manifest/file binding with the independently fixed approved file or fixed manifest binding',
        'real_sealed_entrypoint_bypass_demonstrated':False,
        'reason_not_CLI_bypass':'all existing runtime callers load the exact sealed manifest through fixed c.frozen_inputs.LLM_manifest; current original manifest is bound to exact approved file',
        'bounded_candidate_if_helper_becomes_public':'a future separate candidate can require a trusted manifest/approved file binding; do not edit the sealed original',
    },
    'unexecuted_configuration_anchor_risk':{
        'function':'contract',
        'observation':'contract loads local HERE/bindings.json and verifies files described by it; it does not itself compare local bindings.json SHA with this output-seal.json binding',
        'scope':'external sealed release/caller must keep the reviewed bindings.json and output seal fixed, as this audit did',
        'replacement_configuration_test_executed':False,
        'claimed_human_or_CLI_bypass':False,
        'not_new_source_authentication_framework':True,
    },
    'historical_snapshot_and_annual_gate':{
        'snapshot_gate_before_label_projections':True,
        'fixed_original_rule_prediction_freeze_manifest_manual_material_source_draw_checks':True,
        'immutable_historical_domain_population':{'remaining':1444,'exposed':3037},
        'new1261_3220_domain_refusal_observed':True,
        'annual_flag_does_not_replace_snapshot_gate':'build calls actual_gate then original full-terminal gate; year_join only after genuine A/B/reference/rule/LLM projections',
        'original_engines_kept':'nonannual05f5999084...; annualf6b33491bb...; fixed5000/seed20261010/single_category',
        'year_mapping_or_metrics_executed_in_this_audit':False,
    },
    'actual_identity_and_independence_boundary':{
        'inherits_human_first_reviewed_receive':True,
        'actual_review_required':'ROOT-reviewed actual execution, direct user confirmation, distinct A/B codes, exact original byte bindings, receive mode, complete1000 slots and canonical re-read',
        'reference_not_A_B_consensus_or_AI':'actual_gate requires AI_substitution_used and A_B_agreement_used_as_reference False',
        'reference_blind_and_time_order':'requires reference_machine_blinded and reference_before_machine_comparison True plus exact reference original binding',
        'booleans_and_SHA_authenticate_real_person':False,
        'trusted_actual_human_attestation_is_external':'ROOT/user must establish actual execution and independence; this audit has no such attestation and creates none',
        'only_static_for_identity_facts':'no real human or blind execution was inspected or established',
    },
    'complete_LLM_before_any_valid_batch_labels':{
        'all504_terminal_inventory_first':True,
        'all504_original_terminal_attempt_and_selection_receipts_before_first_json_semantic_reads':True,
        'earliest_whole_technical_valid_no_cross_attempt_merge_no_reference_selection':True,
        'actor_first_report_seal_mirror_assignment_validator_bindings':'checked before final validator/label projection in llm_projection',
        'actual_machine_campaign_reception_tested':False,
        'partial503_and_one_running_batch_refusals_observed':True,
    },
    'null_failure_and_partial_dimension_boundary':{
        'actual_blank_reference_unfilled_not_NULL_refusal_observed':True,
        'partial_returned_reference_dimension_nonreturn_refusal_observed':True,
        'integer0_1_only_bool_string_NaN_rejection':'static code value/load/load_line',
        'lawful_NULL_requires_human_reason_and_identity':'static reference_output; not an actual adjudication',
        'whole_not_returned_and_execution_failure_distinct':'static reference_output/llm_projection; no whole results fabricated',
    },
    'numeric_gate_is_not_accuracy_threshold':True,
    'formal_acceptance_granted_by_interface':False,
}
write('static-safety-boundary-review.json',static)
write('failure-full-input-and-scope.json',{
    'status':'observed_first_execution_failure_retained_not_CLI_bypass',
    'case':next(c for c in plan['cases'] if c['name']==failed[0]['name']),
    'full_synthetic_input':load(failed[0]['input_binding']['path']),
    'first_execution_output':failed[0],
    'scope_interpretation':static['observed_helper_limit'],
    'expectation_not_rewritten':True,
})
write('report.json',{
    'status':'independent_finite_historical200_handoff_audit_complete_no_formal_validation',
    'owner_seal':plan['owner_seal_binding'],'owner_code':plan['code_binding'],
    'pre_execution_seal':bind(OUT/'pre-execution-seal.json'),
    'case_N':12,'each_case_once':True,'matched_N':11,'failed_N':1,
    'one_administrative_positive_and_ten_expected_refusals_observed':True,
    'observed_failure':static['observed_helper_limit'],
    'unexecuted_risk':static['unexecuted_configuration_anchor_risk'],
    'sealed_original_approved_frame_runtime_binding_verified':True,
    'current_historical_gate_and_blank_partial_refusals_observed':True,
    'actual_human_N':0,'actual_reference_N':0,'actual_machine_label_reception_N':0,
    'actual_statistics_N':0,'actual_annual_metrics_N':0,
    'main_LLM_partial_labels_read_N':0,'rule_prediction_semantic_labels_read_N':0,
    'owner_files_modified_N':0,'expected_values_changed_after_execution':False,
    'machine_actor_terminal_or_actual_human_identity_authentication_performed':False,
    'no_new_admission_rule_or_source_authentication_framework':True,
    'findings_are_code_interface_controls_not_formal_human_accuracy_or_reliability':True,
})
with (OUT/'README.txt').open('x',encoding='utf-8') as stream:
    stream.write(
        '旧冻结human200机器/真人参照交接独立有限审查\n\n'
        '绑定owner output-seal SHA d83514d4001afc0ace717c025659458f02f2ed966343b6f564ccf1f0ebe01be6；'
        'handoff.py SHA65ec6edce057d8504846f9a368027e81e2f246292399e1fdbc3457d8767cfa30。'
        '原40封存成员和直接冻结输入及共同材料回执成员均做字节/SHA核验，未解析主LLM部分标签、规则预测标签或owner统计结果。\n\n'
        '12项输入与预期先封存（f78ca1aa4855c496d7294dc3edc297829fd9b21f53744a4148675bc1fd9f3e50），'
        '再各调用一次原函数。11项符合预期：一个真实管理名单正例和10个空白/合成拒绝；保留1项真实控制不符。'
        '未重新执行或修改任何预期。\n\n'
        '真正冻结manifest的ordered_source_ids三键绑定精确等于原approved_record_ids.json绑定；'
        'wrapper的4481唯一ID、UTF8/LF顺序SHA和504批展开一致。wrapper原序LF SHA c4ec6247…；'
        '机器终止库存coverage用JSON规范序列SHA87b1ea27…；编码形式不同，各自正确，不把二者不相等报告为缺陷。\n\n'
        '观察到的有限失败：单独调用frozen_frame并传入自洽的替换manifest/wrapper，'
        '一个未批准合成ID仍被接收。helper核其参数自身的SHA、唯一性和顺序，没有在函数内部钉住外部批准名单。'
        '现真实封存入口的三个调用点都先load(verify(c.frozen_inputs.LLM_manifest))，'
        '该原manifest精确绑定原批准文件，因此此失败不等于已演示真实CLI绕过。'
        '若以后把helper对外开放，可另建有限修正候选绑定可信manifest/批准文件；本审查不修改旧文件。\n\n'
        '另有只读未执行风险：contract本身未用外部output-seal的SHA核本地bindings.json；'
        '其逐项核验基于本地配置声明。真实执行须延续外部ROOT已封存文件绑定，不把换配置后自洽的SHA当同一历史release。'
        '本轮没有更换原配置执行，不能称已验证配置绕过。\n\n'
        '历史版本/域闸门先于标签读取；改规则预测SHA和以annual开关放入1261/3220域均实际拒绝。'
        '未填真人review、未填机器库存、503终止行、504中一批运行、未填裁定null、已返行某维未返均实际拒绝。'
        '身份、独立性、遮盲、时间先后由实际用户与ROOT可信执行复核建立，JSON/SHA不认证真人。'
        'A/B不能自动成为裁定参照，机器全批原终止/选择/失败证据须在有效批标签前核完。\n\n'
        'run_once的标签读取/投影/模块引擎/年度入口守卫未触发。实际A/B、真人参照、机器标签接收、'
        '引擎导入、指标及年度指标全部为0。仅私有函数拒绝控制造一个明确synthetic的整数0作为前置槽，'
        '没有200参照、假release或假用户执行声明。所有控制输入、首次输出、错误与范围解释在本目录封存。'
        '这不是正式真人验证或验收，也未改旧版本准入、公式或源文件。\n'
    )
write('final-readback.json',{
    'status':'owner_sealed_and_all_presealed_control_inputs_unchanged',
    'owner_output_members_N':inputs['owner_output_members_N'],
    'all_owner_and_direct_frozen_bindings_unchanged':True,
    'all_pre_execution_members_unchanged':True,
    'all12_inputs_and_first_outputs_retained':True,
    'classification_or_statistics_reruns_N':0,
})
members=[bind(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
for b in members:assert bind(b['path'])==b
write('output-seal.json',{
    'status':'sealed_independent_human200_handoff_finite_audit_with_one_bounded_helper_failure',
    'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'owner_seal_binding':plan['owner_seal_binding'],'case_N':12,
    'matched_N':11,'failed_N':1,'actual_human_reference_or_metrics_N':0,
    'output_members':members,'seal_self_excluded':True,
})
print(json.dumps({'case_N':12,'matched_N':11,'failed_N':1,'sealed_members_N':len(members),
                  'seal':bind(OUT/'output-seal.json')},ensure_ascii=False))

"""Independent final read-only binding check; does not run any prepared entrypoint."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import ast
import hashlib
import json

ROOT=Path('/PROJECT_ROOT')
PREP=ROOT/'outputs/coding-revision-20261008-r4/llm-candidate05-preparation'
OUT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def bind(p):return {'path':str(Path(p).resolve()),'sha256':sha(p)}


def main():
    exact={
      'candidate05_development_freeze_v2.json':'f7a4e14f30818ba388e1cb5dbce894471cfa0a887dfee6c29481f0d96ec70abd',
      'runtime-v2/run_production_v32.py':'90695fff92a8db1717ac126d423e071a7ffe1af674a22e449cc5f9d8c655b0fa',
      'run_bounded_candidate05_v2.py':'b49a793722c7345008ec78d43ecd0d347647352c17742831172a23b365897659',
      'audit_candidate05_v2.py':'f4bf1a3a6fe9399460c8df58cc4d9ec5b3f2a44e9f829e7144f502f2ee456293',
      'candidate05_package_manifest_v2.json':'9e3ccb9613185b482013c30f9f1bfc1445a6f1d745cf310d2292968afb35c6f8'}
    assert all(sha(PREP/p)==v for p,v in exact.items())
    package=read(PREP/'candidate05_package_manifest_v2.json')
    hashes=[]
    for b in package['files']:
        hashes.append({**b,'matches':sha(b['path'])==b['sha256']})
    assert all(x['matches'] for x in hashes)
    v1=read(OUT/'independent_preflight.json')
    tests=read(OUT/'runtime_v2_gate_recheck.json')
    assert tests['status']=='V2_TECHNICAL_GATE_RECHECK_PASS_NO_ACTUAL_MODEL_CALLS'
    f1=read(PREP/'candidate05_development_freeze.json')
    f2=read(PREP/'candidate05_development_freeze_v2.json')
    semantic_keys=['base','candidate05_prompt','exposed240_input','synthetic62_input',
                   'synthetic_expected_private','human_reserved_exclusion_metadata','planned_runs',
                   'model','reasoning_effort','nominal_model_calls','technical_maximum_calls',
                   'max_identical_technical_attempts_per_batch','prior_artifacts_preserved']
    assert all(f1[k]==f2[k] for k in semantic_keys)
    for key in ['candidate05_prompt','exposed240_input','synthetic62_input','synthetic_expected_private','human_reserved_exclusion_metadata']:
        b=f2[key];assert sha(b['path'])==b['sha256']
        prior=next(x for x in v1['binding_checks'] if x['name']==key)
        assert prior['matches'] and prior['path']==b['path']
    for name in ['output_schema_codex_compatible.json','validate_binary_output.py']:
        assert sha(PREP/'runtime-v2'/name)==sha(PREP/'runtime'/name)
    for b in tests['input_bindings']:assert sha(b['path'])==b['sha256']
    runtime=(PREP/'runtime-v2/run_production_v32.py').read_text()
    wrapper=(PREP/'run_bounded_candidate05_v2.py').read_text()
    auditor=(PREP/'audit_candidate05_v2.py').read_text()
    for s in [runtime,wrapper,auditor]:ast.parse(s)
    assert "binding=event_output_binding_audit" in runtime and "errors.extend(binding['errors'])" in runtime
    assert "not binding_audit['errors']" in auditor and "event_output_binding_audit_sha256" in auditor
    assert 'candidate05_package_manifest_v2.json' in wrapper and 'runtime-v2/run_production_v32.py' in wrapper
    assert "command.append('--plan-only')" in wrapper and "'--max-attempts', '3'" in wrapper
    assert 'candidate05_development_freeze_v2.json' in auditor
    plans=[]
    for run in f2['planned_runs']:
        home=PREP/'runtime-v2'/run['name'];p=read(home/'run_plan.json')
        assert p['n']==run['n'] and p['batch_count']==run['logical_batches']
        assert p['batch_size']==25 and p['max_attempts']==3
        assert p['model']=='gpt-5.6-sol' and p['reasoning_effort']=='medium'
        assert p['runner_sha256']==sha(PREP/'runtime-v2/run_production_v32.py')==sha(home/'frozen_runner.py')
        assert p['prompt_sha256']==f2['candidate05_prompt']['sha256']==sha(home/'frozen_prompt.txt')
        assert p['input_sha256']==sha(run['input'])==sha(home/'frozen_input.jsonl')
        assert p['schema_sha256']==sha(home/'frozen_schema.json')
        assert p['validator_sha256']==sha(home/'frozen_validator.py')
        assert sha(p['cli_path'])==p['cli_binary_sha256']
        assert not list((home/'batches').glob('batch-*/attempts/attempt-*'))
        plans.append({'name':run['name'],'n':run['n'],'batch_count':p['batch_count'],
                      'binding':bind(home/'run_plan.json'),'frozen_runner':bind(home/'frozen_runner.py'),
                      'CLI_binary_sha256_matches_recorded_plan':True,'actual_attempt_count':0})
    assert sum(x['batch_count'] for x in plans)==13
    controls=[dict(x) for x in v1['controls']['control_review']]
    next(x for x in controls if x['id']=='C05-NEW-017')['independent_semantic_reason']='最终冻结文本只陈述常规剂量调整需求，未规定治疗推荐、损害、效果或临床管理复杂性；全0与冻结手册相符。初版更具体的减量安排已另存draft-initial-no-calls，未发生模型调用。'
    report={
      'status':'INDEPENDENT_PREFLIGHT_V2_PASS_BOUNDED_EXECUTION_AWAITING_ROOT_AUTHORIZATION',
      'created_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),
      'scope':'Independent read-only preflight of candidate05 semantic preparation plus final v2 technical execution closure.',
      'real_model_calls_by_reviewer':0,'real_CLI_invocations_by_reviewer':0,'network_calls_by_reviewer':0,
      'preparation_files_edited_by_reviewer':False,'protected_unit_text_prediction_or_human_label_opened':False,
      'unresolved_preflight_blockers':[],
      'v1_blocker_resolved':{'problem':'Acceptance lacked unique completed-agent-message/raw-output binding, despite later audit requiring it.',
                             'resolution':'v2 requires type-preserving canonical JSON equality and one completed message before first-valid selection; post-audit recomputes the same binding gate and verifies audit SHA.',
                             'recheck':bind(OUT/'runtime_v2_gate_recheck.json')},
      'semantic_review':{'complete_candidate03_retained_except_title':True,
                         'added_only_plain_language_I_F_actor_action_recipient_and_parent_result_request':True,
                         'constructs_manual_v13_v14_schema_unchanged':True,
                         'independent_S_E_Ec_and_full_five_dimension_reading_required':True,
                         'controls_total':62,'inherited_controls_unchanged':38,'new_symmetric_controls':24,
                         'new_pairs':12,'final_control017_refinement_before_calls':True,
                         'all_expected_positive_negative_semantics_reviewed':controls,
                         'no_target_score_or_expected_department_distribution_used':True,
                         'no_empirical_semantic_improvement_claim':True},
      'exclusion_review':v1['exclusions'],
      'runner_review':{'only_input_prompt_schema_validator_are_semantic_execution_inputs':True,
                       'private_expected_file_hashed_only_in_wrapper_not_parsed_or_sent_to_model':True,
                       'no_human_A_B_C_reference_read_or_label_based_selection':True,
                       'all_selected_raw_rows_aggregated_without_dimension_splicing_or_label_repair':True,
                       'first_valid_requires_execution_schema_literal_ID_order_zero_tools_one_final_equal_raw':True,
                       'retries_identical_request_technical_failure_only':True,
                       'provider_internal_model_revision_not_exposed':True,
                       'requested_model':'gpt-5.6-sol','reasoning_effort':'medium'},
      'bounded_execution':{'rows':[240,62],'batch_size':25,'logical_calls':13,
                           'maximum_technical_attempts_per_batch':3,'maximum_actual_model_calls':39,
                           'workers':[3,1],'entrypoint':str(PREP/'run_bounded_candidate05_v2.py'),
                           'requires_root_actual_execution_authorization':True,
                           'wrapper_defaults_plan_only':True,'no_full_corpus_run_or_manuscript_adoption_in_scope':True},
      'mock_recheck_counts':{'pure_cases':tests['all_pure_gate_cases_passed'],
                             'run_attempt_cases':tests['all_run_attempt_cases_passed'],
                             'actual_retry_driver_with_mock_provider_cases':tests['all_retry_driver_cases_passed'],
                             'all_pass':True,'actual_model_calls':0},
      'final_frozen_package':bind(PREP/'candidate05_package_manifest_v2.json'),
      'exact_top_level_bindings':[{'path':str(PREP/p),'sha256':v} for p,v in exact.items()],
      'package_binding_checks':hashes,'package_files_verified':len(hashes),
      'actual_plan_checks':plans,
      'preserved_v1_independent_report':bind(OUT/'independent_preflight.json'),
      'audit_code':bind(Path(__file__)),
      'post_execution_required':'Audit every real source/request/raw/final-event binding, all retained failures and first-valid selections, then review all five-dimension changes in exposed240 and both sides of all62 controls. Passing preflight is no evidence of improved semantic accuracy or independent human validity.'}
    target=OUT/'independent_preflight_v2.json';target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (OUT/'independent_preflight_v2.txt').write_text('\n'.join([
      'LLM候选05独立执行前审查v2：通过准备审查，待root有界执行授权',
      '',
      '已核最终v2闭包'+str(len(hashes))+'个文件SHA和两份10/3逻辑批计划；真实执行尝试仍为0。候选05保留完整03、冻结v1.3/v1.4及schema，仅增加普通语言的I/F当前行为与父条件结果说明。62合成控制逐项按手册审读，38继承不变、24新增为12对，期望不依赖目标分数。旧240及其历史比较与267保留成员的ID/规范化正文家族交集均为0。',
      '',
      'v1唯一阻断已修复：接受前必须唯一完成agent_message且其JSON与raw_output按保留类型的canonical JSON相同；运行选择和后审采用同一门禁。12纯函数例、11无模型run_attempt例、3组真实重试驱动的模拟均通过，覆盖缺/多message、非JSON、raw不等、bool/int、float/int及键序/空白/Unicode；验证首个有效即停、相同请求最多3次、失败原件保留。',
      '',
      '允许root审后授权的范围为旧240和62控制，共13逻辑调用、最多39真实技术尝试，gpt-5.6-sol/medium；不含全量重跑、生产采用或稿件更新。执行前通过不代表语义准确率提高或真人独立验证完成。',
      '',
      '审查者实际模型/CLI/网络调用均0；未修改准备闭包，未读取保留原句、机器逐条预测或真人具体标签。',
      '',
      '报告：'+str(target),
    ])+'\n')
    print(json.dumps({'status':report['status'],'report':str(target),'sha256':sha(target),
                      'verified_package_files':len(hashes),'blockers':0,'real_model_calls':0},ensure_ascii=False))


if __name__=='__main__':main()

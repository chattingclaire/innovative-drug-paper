"""Read-only preparation review; subprocess model calls are never invoked."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone, timedelta
import ast
import hashlib
import importlib.util
import json
import math
import re
import sys
import tempfile
import types
import unicodedata

sys.dont_write_bytecode = True
ROOT = Path('/PROJECT_ROOT')
PREP = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate05-preparation'
OUT = Path(__file__).resolve().parent
DIMS = ['S', 'E', 'Ec', 'I', 'F']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def binding(p):
    return {'path': str(Path(p).resolve()), 'sha256': sha(p)}


def norm_sha(s):
    s = unicodedata.normalize('NFKC', s)
    s = ''.join(c for c in s if not c.isspace() and not unicodedata.category(c).startswith('P'))
    return hashlib.sha256(s.encode()).hexdigest()


def load_code(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Independent semantic review, recorded before any actual candidate05 call.
# These notes express the reviewer's reading of the constructs, not measured truth.
OLD_NOTES = {
  1: ('F缺口', '疾病严重和临床迫切未陈述无治疗或获取障碍，全0符合F边界。', 'v1.4 F6'),
  2: ('F缺口', '尚无可获得药物并提出常规获取渠道，F有直接依据；没有独立疗效或费用内容。', 'v1.4 F4/F6'),
  3: ('F部署', '审批提速与满足更多一般需求未具体讨论药物保障关系，不以可能有助于可及赋F。', 'v1.4 F1/F6'),
  4: ('F部署', '短缺储备与持续供药直接构成药物供应保障，F成立。', 'v1.4 F4'),
  5: ('试验获取', '入组后随机转组仅是研究安排，无明确治疗获取缺口。', 'v1.4 F3'),
  6: ('试验获取', '无其他可获得治疗选择及提供研究药物共同满足试验获取例外。', 'v1.4 F3/F6'),
  7: ('公布与实质保障', '发布结果及组织落实未给出当前药物给付/获取内容。', 'v1.4 F1'),
  8: ('公布与实质保障', '扩展药物保险范围和保险承担药费分别支持F及Ec，不自动赋E。', 'v1.4 F1; v1.3 Ec'),
  9: ('经济会务', '价格协商会议的安排和通知只是会务，未规定价格/经济评价内容。', 'v1.3 Ec及评价内容/事务性提及'),
 10: ('经济会务', '明确每盒支付标准是Ec；没有患者可负担或新增保障命题，不自动赋F。', 'v1.3 Ec/F'),
 11: ('临床管理', '明确评价药物频繁监测所致管理难度，F临床管理成立；未明示毒性不补S。', 'v1.4 F5'),
 12: ('临床管理', '医院处方管理的一般规范不构成特定药物管理难度或损害锚点。', 'v1.4 F5; v1.3 S'),
 13: ('创新程序与资源', '创新药对象加沟通提交形式，不等于当前实体研发支持。', 'v1.4 I1'),
 14: ('创新程序与资源', '针对创新研发配置专职顾问和持续技术辅导，I实体支持成立。', 'v1.4 I1'),
 15: ('注册分类', '注册序号未提供创新含义，不借常识填I。', 'v1.4 I4'),
 16: ('注册分类', '给定原创化合物定义及属性资料要求有I直接依据。', 'v1.4 I4'),
 17: ('产品改变', '普通适老包装文字要求未表明创新或实际获取障碍。', 'v1.4 I2; v1.3 F'),
 18: ('产品改变', '相对原制剂的释药改良有I依据；给药频次降低未单独证明疗效、风险或管理难度。', 'v1.4 I2/F5'),
 19: ('机制属性', '普通机制描述未表示新颖性，不能将机制自动编码I。', 'v1.4 I4'),
 20: ('机制属性', '首次采用的新颖机制及原创信息要求，I属性成立。', 'v1.3 I及评价内容要求'),
 21: ('专有权利', '一般商业秘密保密未给出专有试验数据保护权利。', 'v1.4 I3'),
 22: ('专有权利', '专有试验数据的期限及他人不得依赖申报，明确创新权利范围。', 'v1.4 I3'),
 23: ('条件传播', '当前仅公示及办理纳入手续；不把前段创新/临床优势条件全部传播。', 'v1.3上下文边界; v1.4共同步骤'),
 24: ('创新资格', '当前创新资格需证明相对标准治疗生存获益，I及E双锚点成立。', 'v1.3当前创新资格与跨程序引用'),
 25: ('安全正反', '药物不良反应监测和风险控制是S直接内容。', 'v1.3 S'),
 26: ('安全正反', '平台数据安全和账户权限不属于药物损害安全。', 'v1.3 S排除'),
 27: ('有效性正反', '降低复发的临床证据要求明确用于效果判断，E成立。', 'v1.3 E'),
 28: ('有效性正反', '数据字段有效性不等于药物效果，E不成立。', 'v1.3 E排除'),
 29: ('支付与负担', '患者药费过高及降低自付同时涉及费用责任Ec和患者可负担F。', 'v1.3 Ec/F'),
 30: ('支付与负担', '一般实验室设备资金未限定创新药物研发，也不属于药物治疗支付；全0合理。', 'v1.3 Ec/I'),
 31: ('保障续期', '仅允许再次递交续约材料，未规定当前保障延续。', 'v1.4 F2'),
 32: ('保障续期', '对符合条件者持续供药和三年期限，明确F保障持续。', 'v1.4 F1/F2'),
 33: ('保障父谓词', '年度费用条件由保险承担治疗费用三年的父谓词直接控制，Ec及F成立。', 'v1.3上下文; v1.4 F1/F2'),
 34: ('保障父谓词', '相同费用阈值仅用于办理顺序，Ec保留、F不从邻近保障背景补入。', 'v1.3 Ec; v1.4 F1'),
 35: ('创新办理形式', '创新对象下的沟通形式/议题，未陈述机构实际给予研发资源或指导。', 'v1.4 I1'),
 36: ('创新办理形式', '配置专家并持续提供方案技术辅导，实体支持I成立；无具体效果用途不补E。', 'v1.4 I1; v1.3 E'),
 37: ('创新资格与义务', '已入项目的报告事务并不增加/改变支持内容，I不成立。', 'v1.4 I1'),
 38: ('创新资格与义务', '原创属性确认和获取专门研发资源资格均为I实质内容。', 'v1.4 I1/I2'),
}
NEW_NOTES = {
  1: ('agency_safety', '创新研发范围不能把申请人安全监测/风险义务变成机构支持；S保留、I0。', 'v1.3 S; v1.4 I1'),
  2: ('agency_safety', '机构给创新研发配置专家、提供风险技术辅导，S和I分别有锚点。', 'v1.3 S; v1.4 I1'),
  3: ('support_entitlement', '创新项目报告节奏属于事务义务，未增加资源或资格。', 'v1.4 I1'),
  4: ('support_entitlement', '当前规定取得专门研发设备优先使用权的实质资格，I成立。', 'v1.4 I1'),
  5: ('publication_vs_guidance', '发布提交指南及支持宗旨不能替代实际创新支持措施。', 'v1.4 I5'),
  6: ('publication_vs_guidance', '创新研发期间安排人员提出方案技术建议，I支持成立；研究设计未明确用于效果判断不补E。', 'v1.4 I1; v1.3 E'),
  7: ('object_scope', '真实本节范围补足原创新药对象，当前专门方案咨询是支持行为。', 'v1.4 I1及共同步骤'),
  8: ('object_scope', '当前普通药物范围不能被下一节原创项目覆盖；一般咨询不能猜成创新支持。', 'v1.3上下文边界; v1.4 I1'),
  9: ('parent_result', '真实父谓词让费用条件决定保障继续生效；Ec和F均成立。', 'v1.4 F1/F2; v1.3 Ec'),
 10: ('parent_result', '同一费用条件只决定办理排序，Ec成立但没有F给付/供应结果。', 'v1.4 F1; v1.3 Ec'),
 11: ('prior_vs_current_duration', '已履约年数仅是管理转类前提，不是本条新增保障持续。', 'v1.4 F1'),
 12: ('prior_vs_current_duration', '本条直接规定现有保障继续生效和给付条件适用，F成立。', 'v1.4 F2'),
 13: ('application_vs_scope', '当前为支付范围增加申请手续，未确定实际新给付范围或费用责任。', 'v1.4 F1; v1.3 Ec排除'),
 14: ('application_vs_scope', '新增适应证入保障范围与基金承担药费，F及Ec成立；非疗效判断。', 'v1.4 F1; v1.3 Ec/E'),
 15: ('definition_vs_list', '抽象过程定义未控制后句另列项目，不能传播五维。', 'v1.3上下文边界'),
 16: ('definition_vs_list', '当前引导句实质要求下列五维评价内容，随后直接后项补足内容；五维均1合理。', 'v1.3评价内容要求及上下文边界'),
 17: ('management_difficulty', '普通减量安排未给损害、效果或实际管理复杂性，不补S/E/F。', 'v1.3 S/E; v1.4 F5'),
 18: ('management_difficulty', '明确评价每周监测的管理负担和基层可行性，F成立；不补未述毒性S。', 'v1.4 F5'),
 19: ('specific_product_change', '只换申报编号且产品未变，不能视为I创新属性。', 'v1.4 I4'),
 20: ('specific_product_change', '从既有注射液改变为无菌粉末，明确相对既有剂型变化，符合I而无需创新词/优效。', 'v1.4 I2'),
 21: ('exclusive_data_right', '格式存档和未经许可不公开是一般保密义务，不等于专有数据保护。', 'v1.4 I3'),
 22: ('exclusive_data_right', '专有期限及禁止他人依赖数据申请明确权利范围，I成立。', 'v1.4 I3'),
 23: ('unmet_access', '严重、急需、希望早用未证明实际治疗获取缺口或药物效果。', 'v1.4 F6; v1.3 E'),
 24: ('unmet_access', '尚无可获得治疗及机构持续供药，明确F缺口/保障安排。', 'v1.4 F4/F6'),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    initial = {str(p.relative_to(PREP)): sha(p) for p in PREP.rglob('*') if p.is_file()}
    freeze_path = PREP / 'candidate05_development_freeze.json'
    freeze = read(freeze_path)
    history = read(PREP / 'historical_comparison_freeze.json')
    exclusion = read(freeze['human_reserved_exclusion_metadata']['path'])
    reserved = set(exclusion['all_registered_members_of_reserved_families_unit_ids'])
    reserved_hashes = {r['normalized_text_sha256'] for r in exclusion['reserved_family_metadata']}
    input240 = [json.loads(s) for s in Path(freeze['exposed240_input']['path']).read_text().splitlines() if s]
    controls = [json.loads(s) for s in Path(freeze['synthetic62_input']['path']).read_text().splitlines() if s]
    tests = read(freeze['synthetic_expected_private']['path'])['tests']
    expected = {t['input']['id']: t for t in tests}
    ids240 = [r['id'] for r in input240]
    prompt = Path(freeze['candidate05_prompt']['path']).read_text()
    base = Path(freeze['base']['path']).read_text()
    marker = '--- 冻结的完整手册（原样） ---'
    base_prefix, base_tail = base.split(marker, 1)
    candidate_prefix, candidate_tail = prompt.split(marker, 1)
    renamed_prefix = base_prefix.replace('候选03-development', '候选05-development', 1)
    assert candidate_prefix.startswith(renamed_prefix)
    addition = candidate_prefix[len(renamed_prefix):]
    assert candidate_tail == base_tail
    assert '候选05：把当前行为与语境作用写清楚' in addition
    assert 'RECODE25-' not in prompt and 'C05-NEW-' not in prompt and '0.80' not in prompt
    protocol_paths = [ROOT/'outputs/coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md',
                      ROOT/'outputs/coding-revision-20261007-r3/llm-v32/共用实质操作说明-v1.4-运行摘录.txt']
    assert all(p.read_text().strip() in prompt for p in protocol_paths)
    runtime = PREP/'runtime/run_production_v32.py'
    runner_source = runtime.read_text()
    wrapper_source = (PREP/'run_bounded_candidate05.py').read_text()
    ast.parse(runner_source)
    ast.parse(wrapper_source)
    runner = load_code('independent_candidate05_runtime', runtime)
    runner.no_reference_fields(input240)
    runner.no_reference_fields(controls)
    binding_checks = []
    for name in ['base','candidate05_prompt','exposed240_input','synthetic62_input','synthetic_expected_private','human_reserved_exclusion_metadata']:
        b = freeze[name]
        binding_checks.append({'name':name,'path':b['path'],'matches':sha(b['path'])==b['sha256']})
    for name,b in freeze['runtime'].items():
        prior = Path(freeze['base']['path']).parent/name
        binding_checks.append({'name':'runtime:'+name,'path':b['path'],'matches':sha(b['path'])==b['sha256']==sha(prior)})
    for name,b in freeze['prior_artifacts_preserved'].items():
        binding_checks.append({'name':'prior:'+name,'path':b['path'],'matches':sha(b['path'])==b['sha256']})
    for name,b in history['frozen_files'].items():
        binding_checks.append({'name':'history:'+name,'path':b['path'],'matches':sha(b['path'])==b['sha256']})
        if name.endswith('_rows') or name.endswith('_provenance'):
            ids=[json.loads(s)['id'] for s in Path(b['path']).read_text().splitlines() if s]
            assert ids==ids240 and not reserved.intersection(ids)
    assert all(x['matches'] for x in binding_checks)
    assert len(ids240)==len(set(ids240))==240 and not reserved.intersection(ids240)
    assert len(controls)==len(expected)==len(tests)==62
    assert len({r['id'] for r in controls})==62
    assert all(r==expected[r['id']]['input'] for r in controls)
    text_family_intersections = {
        'exposed240': sorted(r['id'] for r in input240 if norm_sha(r['text']) in reserved_hashes),
        'synthetic62': sorted(r['id'] for r in controls if norm_sha(r['text']) in reserved_hashes)}
    assert not any(text_family_intersections.values())
    inherited30 = read(Path(freeze['base']['path']).parent/'synthetic30_expected_PRIVATE.json')['tests']
    inherited38 = read(Path(freeze['base']['path']).parent/'synthetic38_candidate04_expected_PRIVATE.json')['tests']
    stripped = [{k:v for k,v in t.items() if k!='control_origin'} for t in tests[:38]]
    assert inherited30==inherited38[:30] and stripped==inherited38
    control_review=[]
    for t in tests:
        rid=t['input']['id']; n=int(rid.rsplit('-',1)[1])
        category,note,manual=(NEW_NOTES if rid.startswith('C05-NEW-') else OLD_NOTES)[n]
        assert set(t['labels'])==set(DIMS) and all(type(v)is int and v in (0,1) for v in t['labels'].values())
        control_review.append({'id':rid,'construct_group':category,'expected_labels':t['labels'],
                               'review_status':'REASONABLE_PREDECLARED_EXPECTATION_UNDER_FROZEN_MANUAL',
                               'independent_semantic_reason':note,'manual_locator':manual,
                               'not_an_empirical_truth_or_validation_score':True})

    # Reproduce the acceptance discrepancy with a replaced subprocess.run that
    # never invokes CLI, network or a real model. Output lives outside PREP.
    fake_packet={'rows':[{'id':'INDEPENDENT-MOCK-ONLY','text':'一般申请流程。','contexts':{}}]}
    raw={'protocol_version':'CAL-5D-20260926-v1.3','execution_version':'LLM-binary-v32',
         'release_stage':'final_binary_labels','rows':[{'id':'INDEPENDENT-MOCK-ONLY',
         'labels':{d:0 for d in DIMS},'dimension_reasons':{d:'未讨论本维。' for d in DIMS},
         'evidence':[],'fairness_subtypes':[],'innovation_subtypes':[],
         'safety_quality_basis':'no_quality_basis'}],'issue_records':[]}
    assert not runner.v.validate(fake_packet,raw)
    mocked=[]
    actual_subprocess=runner.subprocess.run
    for name,count,mismatch in [('honest_single_final',1,False),('raw_final_mismatch',1,True),('two_final_messages',2,False)]:
        event_value=json.loads(json.dumps(raw))
        if mismatch:
            event_value['rows'][0]['dimension_reasons']['I']='另一份理由。'
        event_text='\n'.join([json.dumps({'type':'item.completed','item':{'type':'agent_message','text':json.dumps(event_value,ensure_ascii=False)}}) for _ in range(count)]+[json.dumps({'type':'turn.completed'})])+'\n'
        fake_calls=[]
        def fake_run(command,**kwargs):
            fake_calls.append(command)
            Path(command[command.index('--output-last-message')+1]).write_text(json.dumps(raw,ensure_ascii=False))
            return types.SimpleNamespace(returncode=0,stdout=event_text,stderr='')
        runner.subprocess.run=fake_run
        dest=OUT/'mock-technical-acceptance'/name
        if dest.exists():
            raise RuntimeError('Mock audit outputs already exist; use immutable new preflight version.')
        meta=runner.run_attempt(dest,fake_packet,'MOCK ONLY; never sent to any model','MOCK-PROMPT-SHA','MOCK-CLI-VERSION','MOCK-CLI-SHA',1)
        post_audit_requires = count==1 and event_value==raw
        mocked.append({'case':name,'real_model_calls':0,'mocked_subprocess_calls':len(fake_calls),
                       'runner_accepts':meta['status']=='accepted_structural_literal_zero_tools',
                       'post_audit_final_message_requirement_passes':post_audit_requires,
                       'output_path':str(dest),'metadata':binding(dest/'run_metadata.json')})
    runner.subprocess.run=actual_subprocess
    assert mocked[0]['runner_accepts'] and mocked[0]['post_audit_final_message_requirement_passes']
    assert all(x['runner_accepts'] and not x['post_audit_final_message_requirement_passes'] for x in mocked[1:])

    final_hashes={str(p.relative_to(PREP)):sha(p) for p in PREP.rglob('*') if p.is_file()}
    assert initial==final_hashes,'Preparation file changed during independent review.'
    run_batches=[math.ceil(x['n']/x['batch_size']) for x in freeze['planned_runs']]
    assert run_batches==[10,3] and sum(run_batches)==13
    assert freeze['nominal_model_calls']==13 and freeze['technical_maximum_calls']==39
    assert all(x['logical_batches']==n for x,n in zip(freeze['planned_runs'],run_batches))
    existing_attempts=list((PREP/'runtime').glob('*/batches/batch-*/attempts/attempt-*'))
    assert not existing_attempts
    report={
      'status':'PREFLIGHT_BLOCKED_ONE_TECHNICAL_FIRST_VALID_GATE_MISMATCH',
      'created_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),
      'reviewer':'validation_state_oct8 independent review; no candidate preparation files edited',
      'actual_model_calls':0,'CLI_invocations':0,'network_calls':0,
      'protected_material_boundary':'Reserved sample texts, machine row predictions and human answers were not opened. Only exclusion IDs/family hashes used; synthetic controls and already-exposed240 were permitted review scope.',
      'prompt_checks':{'only_title_rename_and_candidate05_addition':True,
                       'full_candidate03_prefix_retained':True,'manual_schema_and_citation_tail_byte_identical':True,
                       'manual_v13_v14_verbatim_present':True,'ordinary_language_I_F_relation_request':True,
                       'new_construct_or_schema_field':False,'candidate04_appendix_added':False,
                       'semantic_scope':'Actor/action/recipient and parent-condition-controlled outcome; preserve product-attribute, qualification and exclusive-right I routes, F burden/management/information routes, conditional/negative cases and independent S/E/Ec.',
                       'semantic_improvement_established':False},
      'controls':{'count':62,'inherited_unchanged':38,'new':24,'new_symmetric_pairs':12,
                  'input_contains_only_input_objects_no_expectations':True,'all_expectations_independently_reviewed':True,
                  'control_review':control_review,'no_score_or_department_distribution_selection':True,
                  'ordering':'Fixed SHA over control IDs; expected labels do not determine batching.',
                  'meaning':'Construct execution probes, not independent empirical accuracy.'},
      'exclusions':{'old240_reserved_ID_intersection':[],'old240_reserved_text_family_intersection':text_family_intersections['exposed240'],
                    'synthetic_reserved_text_family_intersection':text_family_intersections['synthetic62'],
                    'reserved_member_n':267,'reserved_hash_n':len(reserved_hashes),
                    'three_historical240_snapshots_ID_only_check_passed':True},
      'runner_checks':{'requested_model':'gpt-5.6-sol','reasoning_effort':'medium',
                       'empty_temporary_cwd_read_only_ignore_user_config_rules_web_disabled':True,
                       'input_forbidden_reference_field_recursive_check_passed':True,
                       'runner_does_not_parse_expected_or_human_reference_files':True,
                       'wrapper_only_hashes_private_expectation_file':True,
                       'aggregation_preserves_entire_selected_raw_rows':True,
                       'retry_only_same_request_after_technical_failure':True,
                       'all_attempts_immutable_retained':True,
                       'selected_first_passing_current_runner_checks':True,
                       'current_acceptance_matches_post_audit_technical_validity':False,
                       'real_provider_internal_revision_not_verified_before_execution':True},
      'bounded_scope':{'planned_rows':[240,62],'batch_size':25,'logical_batches':run_batches,
                       'logical_calls':13,'maximum_identical_technical_attempts_per_batch':3,
                       'maximum_actual_calls':39,'workers':[3,1],
                       'default_wrapper_plan_only':True,'no_full_corpus_or_manuscript_adoption':True,
                       'existing_actual_attempt_directories':len(existing_attempts)},
      'blocking_findings':[{
          'priority':'P1_before_authorized_model_execution',
          'file':str(runtime),'start':61,'end':71,
          'problem':'run_attempt marks accepted after schema/literal/event-count checks without checking exactly one completed agent_message and equality of its parsed JSON to raw_output.json; audit_candidate05.py requires both conditions later.',
          'demonstrated_effect':'Two no-model synthetic cases are accepted by the runtime but fail the planned final-message authenticity condition. Such an attempt would stop retries and be selected as first-valid before post-audit rejects it.',
          'required_resolution':'Use the same final-event/agent-message/raw-output equality gate before selecting a technical attempt and in the post-audit; preserve mismatch attempts as technical failures and retry only identical requests within the existing3-attempt limit. Freeze the changed runner and audit bindings before execution.'}],
      'mocked_reproduction':mocked,
      'binding_checks':binding_checks,
      'input_bindings':[binding(p) for p in [freeze_path,PREP/'historical_comparison_freeze.json',PREP/'run_bounded_candidate05.py',PREP/'audit_candidate05.py',PREP/'prepare_candidate05.py',*protocol_paths]],
      'preparation_before_after_hashes_identical':True,
      'preparation_snapshot':initial,
      'audit_code':binding(Path(__file__)),
      'next_step':'Root resolves/reseals this technical gate, then obtains a fresh independent binding recheck and may authorize the stated bounded actual run. No semantic control result or accuracy gain is claimed in preflight.'
    }
    target=OUT/'independent_preflight.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (OUT/'independent_preflight.txt').write_text('\n'.join([
      'LLM候选05独立执行前审查：暂不通过（1项技术门禁不一致）',
      '',
      '提示、构念、手册、schema、62合成控制、旧240/267排除和13逻辑/39技术调用边界均按准备包核查通过。完整03保留，05只新增普通语言的I/F关系说明及标题版本号；38旧控制未改、24新控制构成12组对称边界。全部62的期望五维已按冻结手册逐条独立审读；未使用目标分数或预期部门分布作判断。',
      '',
      '阻断点：runtime/run_production_v32.py第61—71行接受技术尝试时，未核对唯一最终agent_message及其JSON与raw_output.json一致；audit_candidate05.py事后要求这两项。无模型模拟显示：raw/final不一致和两个最终消息均会被运行器接受，随后被既定后审拒绝，因此当前“首个有效”前后口径不一致。',
      '',
      '应在选择尝试前补齐同一最终事件—原始输出门禁，失败原件保留，仅在原3次技术尝试界限内重试相同请求；修改后重新封存runner/审计绑定再复核。不需要改合成期望、提示或原生产输出。',
      '',
      '真实模型/CLI/网络调用均为0；3次为被替换subprocess的合成模拟，不是实际技术调用。没有运行准备包的plan-only入口，因此没有向准备目录写计划；准备文件审查前后哈希完全一致。真人保留原句、机器预测、具体人工标签均未打开。',
      '',
      '完整检查和62逐项语义记录：'+str(target),
    ])+'\n')
    print(json.dumps({'status':report['status'],'report':str(target),'sha256':sha(target),
                      'model_calls':0,'preparation_unchanged':True,'blockers':1,'control_semantics_reviewed':62},ensure_ascii=False))


if __name__=='__main__':
    main()

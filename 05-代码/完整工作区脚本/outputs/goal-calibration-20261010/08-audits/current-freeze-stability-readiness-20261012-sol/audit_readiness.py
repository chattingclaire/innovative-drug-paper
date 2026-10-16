#!/usr/bin/env python3
"""Metadata-only stability readiness. No packet body read, model or classifier."""
import collections, datetime, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1]
STABLE=BASE/'06-coding/current-freeze-stability800-v1-root'
FULL=BASE/'06-coding/native-full4481-v1-sol'
RECOVERY=BASE/'06-coding/native-full4481-transport-recovery-v2-sol'
EXECUTOR=BASE/'06-coding/current-freeze-stability-execution-root'
INPUTS={};DECLARED_PACKETS={}
def bind(p):
    p=Path(p).resolve();r=p.read_bytes();return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
def reg(p):
    x=bind(p);INPUTS.setdefault(x['path'],x);return x
def load(p):reg(p);return json.loads(Path(p).read_bytes())
def text(p):reg(p);return Path(p).read_text()
def exact(x):
    y=reg(x['path']);assert y=={k:x[k] for k in ('path','bytes','sha256')};return y
def save(n,x):
    with (HERE/n).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def no_const(x):
    if isinstance(x,dict):return {k:no_const(v) for k,v in x.items() if k!='const'}
    if isinstance(x,list):return [no_const(v) for v in x]
    return x
manifest=load(STABLE/'run-manifest.json');scope=load(STABLE/'run-scope.json');ids=load(STABLE/'ordered-source-ids.json')
original=load(FULL/'run-manifest.json');recovery=load(RECOVERY/'manifest.json')
assert len(ids)==len(set(ids))==manifest['record_N']==scope['record_N']==800
assert manifest['batch_N']==scope['batch_N']==87
assert manifest['conditions']==['R1','R2','R3','W','H'] and len(manifest['routes'])==1305
assert manifest['actual_model_calls_at_freeze']==0 and manifest['actual_GO_or_execution_claimed'] is False
assert scope['primary_P_is_R1'] is False and scope['actual_inference_N_at_freeze']==0
for k in ('manual','execution_prompt','protocol'):
    exact(manifest[k]);assert manifest[k]==scope[k]==original[k]
for k in ('plan','common_freeze','ordered_source_ids','W_preset_addendum','validator','statistics_bridge','statistics_engine'):
    exact(manifest[k])
for x in manifest['implementation_bindings']+manifest['cli_executable_bindings']:exact(x)
plan=load(manifest['plan']['path']);assert plan['primary_P']['may_be_R1'] is False
assert plan['batching']['different_from_P_batch_partition_declared'] is True
metadata=load(exact(manifest['sample_metadata_coordinator_only'])['path'])
assert {r['source_id'] for r in metadata}==set(ids)
assert dict(collections.Counter(r['domain'] for r in metadata))=={'exposed':200,'remaining':600}
assert dict(collections.Counter(r['department'] for r in metadata))=={'NMPA':384,'NHSA':340,'NHC':76}
assert hashlib.sha256(('\n'.join(ids)+'\n').encode()).hexdigest()==plan['sample']['selected_ID_UTF8_LF_sha256']
preset=text(BASE/'06-coding/llm-protocol-sol/稳定性与运行封存预设.md')
engine_readme=text(BASE/'07-statistics/prospective-stability-engine-sol/README.md')
engine_audit=text(BASE/'07-statistics/stability-engine-independent-audit-sol/audit-report.md')
audit_boundaries=load(BASE/'07-statistics/stability-engine-independent-audit-sol/acceptance-boundaries.json')
assert audit_boundaries['true_model_dispatches']==0 and audit_boundaries['formal_stability_or_production_eligibility_proven'] is False
for p in [BASE/'07-statistics/prospective-stability-engine-sol/preparation-seal.json',BASE/'07-statistics/stability-engine-independent-audit-sol/audit-seal.json']:
    reg(p) # Seal identity only: constructed fixture trees are not production results.
for p in [BASE/'logs/root-current-freeze-stability-minimal-plan-reception-20261010.json',BASE/'logs/root-stability800-execution-interface-preparation-reception-20261010.json']:
    receipt=load(p)
    assert receipt.get('actual_model_calls',receipt.get('actual_rule_or_model_runs'))==0
run_source=text(EXECUTOR/'run_one.py');receive_source=text(EXECUTOR/'receive_one.py')
for name in ('README.md','common.py','statistics_after_terminal.py','terminal_projection.py'):text(EXECUTOR/name)
recovery_controller=text(BASE/'08-audits/recover-native-whole-batches-v4-root.py')
capacity_sidecar=load(BASE/'08-audits/native-recovery-v2-preflight-sol/ROOT-transport-capacity3-sidecar.json')
recovery_profile=load(RECOVERY/'ROOT-controller-v4-binding.json')
for k in ('controller','guard','capacity_sidecar','prepared_manifest'):exact(recovery_profile[k])
assert manifest['max_concurrent_CLI']==3 and recovery_profile['actual_concurrency_cap']==3
assert '--ephemeral' in run_source and '--ignore-user-config' in run_source and 'features.multi_agent=false' in run_source
assert 'flock' in run_source and 'flock' not in recovery_controller and 'scheduler.lock' not in recovery_controller

# Only assignments, schemas, requests and source identities. Never load or hash packet bodies.
sample=set(ids);original_batches=original['batches'];touched=[b for b in original_batches if sample&set(b['source_ids'])]
full_packet_metadata={};old_assignment_metadata={}
for b in touched:
    a=load(exact(b['assignment'])['path']);old_assignment_metadata[b['batch_id']]=a
    for p in a['packets']:full_packet_metadata[p['source_id']]=p
recovery_packet_metadata={}
for b in recovery['batches']:
    if sample&set(b['source_ids']):
        a=load(exact(b['assignment'])['path'])
        for k in ('manual','execution_prompt','packets','source_ids','source_asset_bindings'):
            old=old_assignment_metadata.get(b['batch_id'])
            if old is not None:assert a[k]==old[k]
        for p in a['packets']:recovery_packet_metadata[p['source_id']]=p
packet_comparisons=[];condition_bindings=[];diagnostic_members=[];matched_full_batches=[]
schema_shapes=[]
for b in manifest['batches']:
    raw=load(exact(b['assignments']['raw'])['path']);w=load(exact(b['assignments']['W'])['path'])
    assert b['members']==raw['source_ids']==w['source_ids'] and b['expected_N']==len(b['members'])
    diagnostic_members.extend(b['members'])
    for k in ('manual','execution_prompt'):assert raw[k]==w[k]==manifest[k]
    assert raw['context_unit']==w['context_unit']=='batch'
    rawschema=load(exact(raw['output_schema'])['path'])
    original_for_member=next(o for o in touched if b['members'][0] in o['source_ids'])
    original_schema=load(exact(old_assignment_metadata[original_for_member['batch_id']]['output_schema'])['path'])
    assert rawschema['required']==original_schema['required']
    assert set(rawschema['properties'])==set(original_schema['properties'])
    assert rawschema['properties']['read_manifest']==original_schema['properties']['read_manifest']
    assert no_const(rawschema['properties']['records']['prefixItems'][0])==no_const(original_schema['properties']['records']['prefixItems'][0])
    schema_shapes.append({'diagnostic_batch_id':b['batch_id'],'fields_required_and_per_record_nonidentity_schema_match_original':True})
    for a in (raw,w):
        assert a['strict_technical_validator']==manifest['validator']
    routes=[r for r in manifest['routes'] if r['batch_id']==b['batch_id']]
    assert len(routes)==15
    for r in routes:
        assert r['reservation_only_not_actual_attempt'] is True
        if r['condition'] in ('R1','R2','R3','H'):assert r['assignment']==b['assignments']['raw']
        else:assert r['assignment']==b['assignments']['W']
        if r['condition']=='H':assert r['fixed_request']==b['requests']['H']
        else:assert r['fixed_request']==b['requests']['base']
    core=exact(b['fixed_core']);base=exact(b['requests']['base']);h=exact(b['requests']['H'])
    basebytes=Path(base['path']).read_bytes();hbytes=Path(h['path']).read_bytes()
    assert basebytes.split(b'\n',1)[0]=='判读要求'.encode() and hbytes.split(b'\n',1)[0]=='判读说明'.encode()
    assert basebytes.split(b'\n',1)[1]==hbytes.split(b'\n',1)[1]
    condition_bindings.append({'batch_id':b['batch_id'],'R1_R2_R3_W_fixed_request':base,'H_fixed_request':h,'H_only_first_line_in_fixed_request':True,'full_actual_dispatch_prompt_not_same_due_to_route_envelope':True})
    for p,wp in zip(raw['packets'],w['packets']):
        sid=p['source_id'];assert sid==wp['source_id'] and p==full_packet_metadata[sid]
        recovery_match=None
        if sid in recovery_packet_metadata:assert p==recovery_packet_metadata[sid];recovery_match=True
        for k in ('source_id','output_id','source_bundle_sha256','source_bundle_utf8_bytes','frame_ordinal_1based'):assert p[k]==wp[k]
        DECLARED_PACKETS[sid]={'original':p,'W_display':wp}
        packet_comparisons.append({'source_id':sid,'declared_original_binding':p,'exact_original_full_assignment_binding_match':True,
            'recovery_declared_binding_match_when_in_recovery_scope':recovery_match,'W_declared_source_bundle_identity_unchanged':True,
            'W_decoded_text_not_rechecked_in_this_metadata_only_audit':True,'packet_body_opened_by_auditor':False})
    matches=[o['batch_id'] for o in original_batches if o['source_ids']==b['members']]
    if matches:matched_full_batches.append({'diagnostic':b['batch_id'],'original':matches[0]})
assert diagnostic_members==ids and len(packet_comparisons)==800
empty=0;actual_files=[];selections=[]
for r in manifest['routes']:
    directory=Path(r['output_directory']);assert directory.is_dir()
    files=[str(p) for p in directory.iterdir()]
    if not files:empty+=1
    else:actual_files.extend(files)
    selection=Path(r['selection_directory'])/'root-selection.json'
    if selection.exists():selections.append(str(selection))
assert empty==1305 and not actual_files and not selections
top_actual=[p.name for p in STABLE.iterdir() if p.is_file() and any(k in p.name.lower() for k in ('go','execution','terminal','result'))]
assert not top_actual
inventory={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'route_N':1305,'empty_reserved_attempt_directory_N':empty,
    'nonempty_attempt_paths':actual_files,'root_selection_files':selections,'top_level_GO_or_terminal_result_files':top_actual,
    'genuine_diagnostic_conditions_executed_N':0,'complete_R1_R2_R3_N':0,'independent_R2_R3_repeats_completed_N':0,'W_H_completed_N':0,
    'technical_retry_or_primary_not_counted_as_repeat':True,'prepared_or_constructed_fixture_files_not_counted_as_real_attempts':True}

progress_path=BASE/'progress.json';progress=load(progress_path)
selected_progress={k:v for k,v in progress.items() if k in ('stability_independent_audit_reception_actual','native_batch_stability_adapter_independent_reception_actual','native_v17_prospective_stability_interface_candidate','current_freeze_stability_execution_interface_preparation_actual')}
save('observed-progress-metadata.json',{'source_binding_at_read':INPUTS[str(progress_path.resolve())],'fields':selected_progress,'not_execution_evidence_without_real_artifacts':True})

closure_ids=[s for b in touched for s in b['source_ids']]
assert len(touched)==351 and len(closure_ids)==len(set(closure_ids))==3759 and sample<=set(closure_ids)
assert len(matched_full_batches)==13
closure={'status':'unexecuted_metadata_only_scope_proposal_not_adopted_contract','target_sample_binding':manifest['ordered_source_ids'],
    'target_N':800,'original_whole_batch_N':351,'actual_carried_record_N':3759,'companion_not_scored_record_N':2959,
    'selection_rule':'All and only original frozen whole batches intersecting the unchanged800 prelabel sample; preserve every original member and order. No machine/human labels inspected.',
    'target_source_ids':ids,'all_carried_source_ids':closure_ids,'batches':[{'original_batch_id':b['batch_id'],'assignment':b['assignment'],'all_members':b['source_ids'],'target_members':[s for s in b['source_ids'] if s in sample]} for b in touched],
    'minimum_fresh_first_attempt_batch_dispatches_if_all_five_conditions_adopted':1755,
    'M12_R1_R2_R3_minimum':1053,'M13_W_H_minimum':702,
    'strictly_new_freeze_required_before_GO':True,'old87_directory_members_must_not_change':True,
    'cannot_retroactively_call_current_primary_R1':True,'not_full4481_repeat':True,'classification_or_model_calls':0}
save('proposed-original-whole-batch-scope.json',closure)
save('800-packet-binding-metadata-comparison.json',{'rows':packet_comparisons,'body_opened_N':0})
save('condition-request-binding-comparison.json',condition_bindings)
save('schema-shape-comparison.json',schema_shapes)
save('observed-real-attempt-inventory.json',inventory)
transport_findings=[
    {'finding':'Existing runner appends condition/attempt/logical-label/unique-slot metadata inside the actual model prompt.',
     'evidence':"prompt = fixed_request.read_bytes() + 请求外操作元数据 + json.dumps(metadata)",
     'implication':'Same fixed core is proved; full sent prompt bytes differ. Old plan expressly discloses this method variant. Do not claim exact whole-request identity under original preset. For literal identity, prepare new common visible prompt using relative own-slot outputs and external-only routing; freeze any method variant before dispatch.'},
    {'finding':'Receiver already checks seal identities, template/completion and first/report hashes, but empty actual_input_bindings pass and arbitrary existing bindings are not restricted to assignment.',
     'evidence':"for bound in seal.get('actual_input_bindings', []): validator.check_binding(bound)",
     'implication':'Before new GO, copy receiver/guard into a new frozen transport layer, enforce nonempty real allowed bindings plus v4 explicit flags and actual closed events. Adapt metadata shapes/names; current recovery guard is not plug-compatible with diagnostic manifest.'},
    {'finding':'Existing shared lock addresses original primary scheduler; current recoveryv4 does not acquire that lock.',
     'evidence':'stability run_one acquires shared_primary_scheduler_lock; recoveryv4 has no flock/scheduler.lock.',
     'implication':'A released old lock does not prove recovery terminal. Require real recovery controller/result and child-process terminal receipts before stability GO; enforce global cap3 in fresh controller. Do not edit or interrupt running recovery.'},
    {'finding':'Old stability entrypoints may use unspecified Python; frozen production validator imports jsonschema.',
     'evidence':'validator SHA34a7...; current recovery receiver dependency incident is preserved.',
     'implication':'Use already verified /opt/homebrew/opt/python@3.14/bin/python3.14 and frozen CLI0.162.1; preflight read-only dependencies before dispatch. Null or optional first.attempt_number absence must not trigger retry.'}
]
proposal={'status':'readiness_recommendation_not_execution_authorization','no_actual_model_or_classifier_calls':True,
    'minimum_existing_registered_scope':{'conditions':['R1','R2','R3','W','H'],'target_record_N':800,'fixed_diagnostic_batch_N':87,
        'minimum_first_batch_dispatches':435,'M12_minimum':261,'M13_minimum':174,'maximum_technical_attempt_slots':1305,
        'use':'Declared fixed800 diagnostic partition stability, remaining600/exposed200 disclosed; not exact originalP batch-context reproduction.',
        'original_prepared_run':str(STABLE),'existing_executor':str(EXECUTOR),
        'necessary_before_GO':'Freeze separate transport/receiver/capacity/actual terminal sidecar with old byte bindings preserved. Keep all five conditions and same800/87 plan; no output-based shrinking.'},
    'if_original_batch_context_is_required':{'scope_proposal_path':str(HERE/'proposed-original-whole-batch-scope.json'),
        'actual_record_N':3759,'whole_batch_N':351,'minimum_five_condition_batch_dispatches':1755,
        'necessary_new_preparation':'New campaign namespace for351 original intact batches, unchanged800 analysis targets/weights, full original schemas/packets/context. R1/R2/R3 common core and fresh isolated contexts; W same semantics/array/order; H only header. Keep all companion rows as retained whole-batch outputs but exclude from800 statistical estimand.',
        'current_step':'propose and freeze metadata only; do not prepare production assignments or execute now'},
    'transport_findings':transport_findings,
    'rule_reproduction_legacy_plan_note':'Old plan recommends two unchangedv2 full4481 rule runs. It is not evidence of completed current-version repeats and cannot be reused across later algorithm changes/composites. No rule rerun is needed to establish this LLM stability readiness; any current rule reproducibility question needs its own actual implementation/origin freeze.'}
save('minimal-next-scope-and-transport-proposal.json',proposal)
report={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'no_real_independent_stability_runs; reusable_preparation_with_declared_scope_and_transport_limits',
    'completed_real_independent_diagnostic_runs':0,'completed_extra_main_repeats_R2_R3':0,'completed_W_H_runs':0,
    'old800_preparation_is_not_development_label_based_truth':'Same prelabel formal800 selection reused; remaining600 and exposed200 retained. Machine stability diagnostic, not human assignment or accuracy validation.',
    'same_current_manual_prompt_protocol_bytes':True,'all800_raw_packet_bindings_match_original_metadata':True,
    'recovery_packet_bindings_match_when_in_recovery_scope':True,'original_packet_body_read_N':0,'W_body_read_N':0,
    'W_semantic_equivalence_evidence':'Same source_bundle metadata and previously sealed ROOT preparation800 decoded equality reception; this audit did not reopen W content.',
    'same_required_schema_and_per_record_nonidentity_structure':True,'different_diagnostic_partition':True,'diagnostic_batch_N':87,
    'diagnostic_batches_coincidentally_equal_original':13,'old_primary_or_recovery_not_R1':True,
    'minimum_registered_diagnostic_scope_first_calls':435,'original_batch_embedded_target_scope_first_calls':1755,
    'original_batch_embedded_N':351,'original_batch_embedded_carried_N':3759,'full4481_rerun_recommended':False,
    'actual_serving_model_independently_verified':False,'formal_stability_complete':False,'classification_or_model_calls_by_auditor':0,
    'old_frozen_inputs_or_progress_modified':False,'transport_findings':transport_findings}
save('report.json',report)
notes={'exploratory_metadata_display_recovery':'Initial file-depth inventory was too broad and truncated; recovered with top-level nonrecursive inventory. One inspection wrongly treated ordered-source-ids list as dict; another assumed JSON schema items was an object although prefixItems is used and items=false. All occurred before audit outputs or any execution, recovered without changing frozen files.',
    'scope':'Top-level reports plus referenced assignments/schemas/requests/implementation metadata only. No policy packet body, source JSONL body, human200 workbook/answers, native first labels or model outputs opened for this task.',
    'binding_limit':'800 packet file bytes were not rehashed here to avoid reopening source material; comparisons use exact declared source bindings and existing reception chain. Metadata bindings were rehashed.'}
save('audit-scope-and-preparation-observations.json',notes)
changed=[{'before':x,'after':bind(x['path'])} for x in INPUTS.values() if bind(x['path'])!=x]
stable_changed=[x for x in changed if x['before']['path']!=str(progress_path.resolve())];assert not stable_changed
save('input-bindings.json',{'files':list(INPUTS.values()),'file_N':len(INPUTS),'mutable_progress_changes_during_audit':changed,'declared_packet_comparison_only':True})
md=f'''真实独立稳定性执行完成 **0**：R1/R2/R3均未执行，额外重复R2/R3为0，W/H为0。1305个预留attempt目录全空，无GO、dispatch、first、selection或terminal统计。构造控制和统计引擎审查均不是真实重复；原生产P、恢复和技术失败重试也不能追认R1。\n\n可复用现有固定800选择、共同manual/prompt/protocol、原packet绑定、五条件及统计数学。逐项metadata比对800原packet与当前full/recovery绑定一致，schema必需字段/read_manifest及非身份逐记录结构一致。本次没有重开原文、W正文或真人200答案，W等义仅复核已封印准备接收与source_bundle元数据，不新宣称独立全文等义验证。该800包含remaining600/exposed200；它不是新增真人任务或正确性检验。\n\n旧方案将800重新分87批，明确不同于主运行P，仅13个诊断批恰好与原批全成员/顺序相同。因此可用于已登记87批上下文的机器诊断，不能称原P完整批上下文复现。保留旧范围时，最少仍需R1/R2/R3/W/H各87批，合计435个fresh首次批执行（M12为261，M13为174）；最多1305个技术槽不是重复次数。准备路径为06-coding/current-freeze-stability800-v1-root；执行接口为06-coding/current-freeze-stability-execution-root。未建议另起全4481重复。\n\n原样启动前需另封运输补充：旧接收器已有seal身份/标志及first/report字节检查，但应补强实际输入非空且限制于assignment；绑定已验证Python3.14/jsonschema、CLI0.162.1、至多3实际进程及完整真实终态。旧锁只覆盖旧主调度器，不覆盖正在继续的recoveryv4；主恢复真正全末态前不能用锁释放冒称可开始。旧runner把路由/条件/attempt/slot追加到真实prompt，原plan已披露固定core与全请求字节的区别；如要求原preset的R全请求相同，需新冻结相同模型可见prompt及相对自身slot输出，把路由留在ROOT外部台账，否则只能称已披露方法变体。不能偷偷改旧准备字节或删条件。\n\n若ROOT需要的是**原整批嵌入**稳定性，元数据最小闭包为351原批、3759条实际输入（800统计目标+2959同批伴随）。只能另立新scope/namespace，保留原全成员/顺序/packet/schema，五条件最少1755首次批执行；800分析目标和权重不变，伴随结果仅作整批保留。闭包清单见proposed-original-whole-batch-scope.json，当前只是未采纳、未执行的准备建议，不能把87目录改为351或从现有P挑结果充R1。两种范围都应保留合法null、失败和未调用，不设新稳定阈值。\n\n旧方案的两个v2全4481规则复现建议未执行，也不能跨之后算法修改当作当前规则稳定性证据；本任务不启动规则重算。后续真正五条件都末态后才沿用已封印修复数学及whole-batch projection，报告固定五对/三方、共同二元分母、null/失败/覆盖。服务模型身份与独立完整上下文仍不能由文件SHA或工具准备认证。\n'''
with (HERE/'report.md').open('x',encoding='utf8') as f:f.write(md)
save('seal.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[bind(p) for p in sorted(HERE.iterdir()) if p.is_file()],'self_excluded':True,'actual_models_called':0})
print(json.dumps({'audit':str(HERE),'seal':bind(HERE/'seal.json'),'real_repeats':0,'registered87_scope_minimum':435,'original351_scope_minimum':1755,'inputs_N':len(INPUTS)},ensure_ascii=False))

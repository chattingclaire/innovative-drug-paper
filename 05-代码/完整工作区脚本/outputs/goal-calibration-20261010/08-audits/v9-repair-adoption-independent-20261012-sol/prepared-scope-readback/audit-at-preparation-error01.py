"""Actual prepared scope byte/metadata audit; never imports a coder or selector."""
from pathlib import Path
import ast,datetime,hashlib,json,collections
G=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent
P=G/'06-coding/rule-full4481-final-v7-root';Q=G/'06-coding/rule-v9-affected-original-common-root';A=G/'08-audits/v9-final-adoption-and-selection-root';F=O.parent/'final-static-adoption';inputs={}
def bind(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def read(p):
 s=bind(p);inputs[s['path']]=s;return Path(p).read_bytes()
def load(p):return json.loads(read(p))
def verify(s):
 a=bind(s['path']);assert all(a[k]==s[k] for k in ('path','bytes','sha256')),s['path'];inputs[a['path']]=a
 return a
def save(n,v):
 with (O/n).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
selection=load(A/'static-selection.json');adopt=load(A/'ROOT-static-candidate-adoption.json');sel_seal=load(A/'selection-seal.json')
for s in sel_seal['files']+sel_seal['ancestor_seals']:verify(s)
assert selection['status']=='static_selection_only_no_classifier_execution' and selection['full_fallback_reasons']==[] and selection['record_N']==4481 and selection['selected_N']==3904 and selection['reusable_N']==577
for k in ('contract_binding','manifest_binding','baseline_prediction_binding','selector_binding'):verify(selection[k])
assert selection['contract_binding']==bind(F/'approved-static-selector-contract.json')
contract=load(selection['contract_binding']['path']);required=load(F/'ROOT-ready-required-candidate-members.json');candidate_seal=load(required['candidate_delivery']['path'])
assert required['independent_readback_complete'] and len(required['required_candidate_members'])==117
for s in required['required_candidate_members']:verify(s);assert s in candidate_seal['files']
assert required['candidate_delivery']==adopt['candidate_delivery']
for k in ('candidate_delivery','candidate_freeze','independent_audit_seal','approved_contract','required_candidate_members','static_selection'):verify(adopt[k])
scope=load(Q/'frozen-scope.json');old_scope=load(P/'frozen-scope.json');plan=load(Q/'impact-closure-plan.json');pre=load(Q/'pre-execution-run-seal.json');alg=load(Q/'algorithm-bindings.json');lineage=load(Q/'original-input-lineage-sidecar.json');packets=load(Q/'packet-bindings.json');old_packets=load(P/'packet-bindings.json')
for k in ('scope','impact_plan','lineage'):verify(pre[k])
for s in pre['implementation_files']:verify(s)
assert pre['scope']==bind(Q/'frozen-scope.json') and pre['impact_plan']==bind(Q/'impact-closure-plan.json') and pre['lineage']==bind(Q/'original-input-lineage-sidecar.json')
assert pre['actual_inference_runs']==0 and pre['max_actual_cohort_passes']==1 and pre['formal_validation_complete'] is False
assert not (Q/'run-affected-first').exists(),'Inference must not precede this scope audit'
assert scope['expected_record_N']==3904 and scope['expected_dimension_N']==19520 and scope['parent_complete_record_N']==4481 and scope['bounded_delta_only'] is True
ids=old_scope['approved_record_ids'];chosen=[r['id'] for r in selection['affected_records']];selected=set(chosen)
assert len(ids)==len(set(ids))==4481 and len(chosen)==len(selected)==3904 and chosen==[i for i in ids if i in selected]
assert scope['approved_record_ids']==plan['affected_record_ids']==packets['ordered_source_ids']==chosen
assert plan['affected_record_N']==3904 and plan['unaffected_inherited_record_N']==577
assert plan['selection']==bind(A/'static-selection.json') and plan['contract']==selection['contract_binding'] and plan['independent_required_candidate_members']==bind(F/'ROOT-ready-required-candidate-members.json')
assert plan['candidate_delivery']==scope['final_candidate_delivery_seal']==alg['final_candidate_delivery_seal']==adopt['candidate_delivery']
assert plan['candidate_freeze']==scope['final_candidate_pre_execution_seal']==alg['final_candidate_pre_execution_seal']==adopt['candidate_freeze']
assert scope['final_candidate_algorithm']==scope['algorithm_bindings']==bind(Q/'algorithm-bindings.json') and alg['impact_closure_plan']==scope['impact_closure_plan']==bind(Q/'impact-closure-plan.json')
assert alg['algorithm_version']=='joint-v9-generic-relationship-sol'
assert [{k:v for k,v in x.items() if k!='module'}for x in alg['modules']]==[next(y for y in contract['candidate_modules']if Path(y['path']).stem==x['module'])for x in alg['modules']]
for s in alg['modules']:verify(s)
allowed_changes={'authorization_id','source_packet','release','algorithm_bindings','driver_version','output_directory','approved_record_ids','expected_record_N','expected_dimension_N','material_bindings','ordered_record_ids_binding','algorithm_origin','packet_bindings','final_candidate_algorithm','final_candidate_pre_execution_seal','final_candidate_delivery_seal'}
assert {k for k in old_scope if scope.get(k)!=old_scope[k]}==allowed_changes
assert set(scope)-set(old_scope)=={'parent_complete_seal','original_ordered_record_ids_binding','bounded_delta_only','impact_closure_plan','parent_complete_record_N'}
for k in ('manual','prompt','protocol','source_reading_protocol_code','source_package_seal','source_manifest','source_material_inventory_binding'):assert scope[k]==old_scope[k];verify(scope[k])
assert scope['formal_validation_complete'] is scope['human_validation_complete'] is scope['blind_validation'] is False
assert scope['max_actual_cohort_inference_runs']==1 and scope['execution_purpose']=='production_provisional'
assert packets['packet_N']==3904 and packets['packets']==[p for p in old_packets['packets']if p['source_id']in selected]
assert packets['parent_complete_packet_manifest']==bind(P/'packet-bindings.json')
assert lineage['original_source']==old_scope['source_packet'] and lineage['subset_source']==scope['source_packet']
verify(old_scope['source_packet']);verify(scope['source_packet'])
raw=read(old_scope['source_packet']['path']);lines=raw.splitlines(keepends=True);assert len(lines)==4481
subset=read(scope['source_packet']['path']);derived=[];rows=[];start=0;newstart=0
for ordinal,(rid,line) in enumerate(zip(ids,lines),1):
 # Identity only is interpreted; no current/context prose is adjudicated.
 assert json.loads(line)['source_record']['id']==rid
 if rid in selected:
  derived.append(line);rows.append({'id':rid,'parent_ordinal_1based':ordinal,'parent_utf8_start':start,'parent_utf8_end':start+len(line),'subset_ordinal_1based':len(derived),'subset_utf8_start':newstart,'subset_utf8_end':newstart+len(line),'line_sha256':hashlib.sha256(line).hexdigest()});newstart+=len(line)
 start+=len(line)
assert subset==b''.join(derived) and lineage['rows']==rows and lineage['source_lines_byte_identical']
for n in ('interface_common.py','status_bridge.py'):assert read(Q/n)==read(P/n)
driver=read(P/'rule_driver.py').decode();actual=read(Q/'rule_driver.py').decode()
transforms=[("VERSION='v7-full4481-original-common-driver-1'","VERSION='v9-original-common-affected-driver-1'"),("    if scope.get('expected_record_N') != 4481 or scope.get('expected_dimension_N') != 22405:\n        raise ValueError('adapter requires the complete 4481-record, 22405-dimension scope')","    if not scope.get('bounded_delta_only') or scope.get('parent_complete_record_N') != 4481:\n        raise ValueError('complete compatible parent and explicit affected scope required')\n    delta_N=scope.get('expected_record_N')\n    if type(delta_N) is not int or not (0 < delta_N <= 4481) or scope.get('expected_dimension_N') != delta_N*5:\n        raise ValueError('exact affected scope or explicit full fallback required')"),("packet_plan['packet_N']!=4481","packet_plan['packet_N']!=scope['expected_record_N']"),('joint-v7 generic direct-content and bounded-relation repair; original common packets/manual/prompt/protocol unchanged','joint-v9 relation repair on all statically selected original records; inherited records retain actual prior origins'),("'fixed_algorithm_version':'joint-v7-relation-content-sol'","'fixed_algorithm_version':'joint-v9-generic-relationship-sol'"),("'sealed_complete_production_provisional_rule_run'","'sealed_complete_production_provisional_rule_delta_run'"),('Final sealed v5 full4481 original common source-only execution; one first domain pass; persistent per-record outputs.','v9 original-common affected execution; persistent first results; full fallback allowed only as explicit complete scope.')]
for old,new in transforms:assert driver.count(old)==1;driver=driver.replace(old,new)
assert driver==actual;ast.parse(actual)
manifest=load(selection['manifest_binding']['path']);assert [x['id'] for x in manifest['records']]==manifest['approved_record_ids']==ids
assert [r['packet_binding']for r in manifest['records']]==[p['packet_binding']for p in old_packets['packets']]
counts={'selected':{d:collections.Counter()for d in ('S','E','Ec','I','F')},'inherited':{d:collections.Counter()for d in ('S','E','Ec','I','F')}}
baseline_ids=[]
for line in read(selection['baseline_prediction_binding']['path']).splitlines():
 r=json.loads(line);baseline_ids.append(r['id']);which='selected'if r['id']in selected else'inherited'
 for d in counts[which]:
  v=r['labels'][d];assert v is None or type(v)is int and v in (0,1);counts[which][d]['null'if v is None else str(v)]+=1
assert baseline_ids==ids
report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'actual_prepared_scope_mechanical_readback_passed_before_inference','selected_N':3904,'inherited_N':577,'expected_dimension_N':19520,'actual_inference_directory_absent_at_audit':True,'selection_contract_required117_algorithm_bound_exact':True,'actual_selection_complete_original_order':True,'original_input_line_N':4481,'byte_identical_selected_line_N':3904,'original_and_subset_ordinal_UTF8_spans_exact_N':3904,'source_subset_binding':scope['source_packet'],'selected_packet_manifests_literal_equal_parent_subset':True,'source_manual_prompt_protocol_unchanged':True,'unchanged_interface_status_bridge_bytes':True,'driver_exact_allowed_text_replacements_N':len(transforms),'driver_semantic_pipeline_elsewhere_unchanged':True,'scope_only_allowed_metadata_changes':sorted(allowed_changes),'all_old_1_0_null_selected_states_retained_in_original_input_and_whole_record_recompute':True,'baseline_label_state_counts':{w:{d:dict(c)for d,c in dims.items()}for w,dims in counts.items()},'full_fallback_reasons':[],'classification_or_selector_executed_by_this_audit':False,'new_or_human200_body_semantic_review':False,'body_interpretation_only_source_id_metadata_not_semantics':True,'actual_source_input_byte_check_is_not_prediction_or_semantic_confirmation':True,'ROOT_still_must_seal_pre_inference_adoption_sidecar_before_start':True,'no_reference_gold_values_read_or_modified':True,'formal_validation_complete':False,'prepared_scope_binding':bind(Q/'frozen-scope.json'),'prepared_pre_execution_seal_binding':bind(Q/'pre-execution-run-seal.json'),'prepared_lineage_binding':bind(Q/'original-input-lineage-sidecar.json'),'actual_driver_binding':bind(Q/'rule_driver.py')}
save('report.json',report)
with (O/'report.md').open('x',encoding='utf8')as f:f.write('实际准备范围通过机械读回：3904条、19520维槽位，577条可继承，fallback为空。3904个选中原行与原完整common输入逐字节相同，原序号、子集序号和UTF8跨度全部相同；packet元数据是原完整清单的精确有序子集。五模块、候选总seal、freeze、批准契约、117成员与选择结果绑定一致。\n\n适配器和status bridge字节不变；driver只有7处已授权版本、计数约束与记录说明替换，其余字节相同。原手册、prompt、protocol、来源包和库存绑定保持。选中整条重算包含既有1、0和null，并未按旧值削减证据链。此检查没有解读新正文、人审200或remaining语义，也没有运行selector或分类器。\n\n审计时实际推理目录尚不存在。ROOT仍须在启动前记录实际pre-inference采用sidecar，之后核真实一次运行、零技术失败、来源消费和合并字节。formal gate保持false。\n')
for s in inputs.values():assert bind(s['path'])==s
save('input-bindings.json',{'inputs':list(inputs.values()),'exact_before_after':True})
files=[bind(p)for p in sorted(O.iterdir())if p.is_file()and p.name!='output-seal.json'];save('output-seal.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,'input_bindings':list(inputs.values()),'actual_scope_readback_passed':True,'classification_runs':0,'self_excluded':True})
print(json.dumps({'report':bind(O/'report.json'),'seal':bind(O/'output-seal.json'),'inputs_N':len(inputs),'counts':report['baseline_label_state_counts']},ensure_ascii=False,indent=2))

"""Seal an independent readback; no selector/classifier execution."""
from pathlib import Path
import ast,datetime,hashlib,json,copy,re,unicodedata
G=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent
C=G/'06-coding/rule-five-dimension-joint-root/versions/joint-v9-generic-relationship-sol'
D=G/'08-audits/v9-generic-relationship-repair-design-sol/final-candidate-delivery-20261012-sol'
B=O.parent/'baseline-compatibility-phase02';M=['evidence','source_packet','source_receipts','relations','dimensions'];inputs={}
def bind(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def load(p):
 s=bind(p);inputs[s['path']]=s;return json.loads(Path(p).read_bytes())
def verify(s):
 a=bind(s['path']);assert all(a[k]==s[k] for k in ['path','bytes','sha256']),s['path'];inputs[a['path']]=a;return a
def save(n,v):
 with (O/n).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
s=load(D/'output-seal.json');assert bind(D/'output-seal.json')['sha256']=='a930c16126099b1a2640d25c3903879c7b2375c526f4f565b5237b10ee3da5ec'
assert len(s['files'])==117 and len(s['required_member_bindings'])==46
members={x['path']:x for x in s['files']};assert len(members)==117
for x in s['files']+s['input_bindings']:verify(x)
assert set(s['required_members'])=={x['path'] for x in s['required_member_bindings']}
for x in s['required_member_bindings']:assert members[x['path']]==verify(x)
f=load(D/'candidate-freeze.json');contract=load(D/'selector-contract.json')
for key in ['selector_binding','final_control_summary_binding','final_control_results_binding','manual_binding','fixed_preimplementation_seal_binding','baseline_compatibility_report_binding']:verify(f[key])
for x in f['candidate_modules']+f['all_attempt_seal_bindings']:verify(x)
assert f['candidate_modules']==contract['candidate_modules']
last=Path(f['final_finite_control_directory']);lastpre=load(last/'pre-execution-seal.json')
for x in lastpre['code']:
 a=verify(x);assert Path(a['path']).read_bytes()==(C/Path(a['path']).name).read_bytes()
assert str(last)==str(C/'attempt08-final-governance-controls')
all_attempts=[];expected_history={};control_input_members=set();snapshot_members=set()
for spec in f['all_attempt_seal_bindings']:
 seal=load(spec['path']);root=Path(spec['path']).parent;pre=load(root/'pre-execution-seal.json');results=load(root/'results.json');summary=load(root/'summary.json')
 for x in pre['controls']+pre['code']+pre['old_code']:verify(x)
 for x in pre['controls']:assert members[x['path']]==x;control_input_members.add(x['path'])
 for x in pre['code']:assert members[x['path']]==x;snapshot_members.add(x['path'])
 for key in ['files','members','output_files']:
  for x in seal.get(key,[]):verify(x)
 cases={}
 for x in pre['controls']:
  for case in load(x['path'])['cases']:
   assert case['name'] not in cases;cases[case['name']]=case
 assert len(results)==len(cases)==summary['case_N']
 failures=[]
 for row in results:
  c=cases[row['name']];assert row['expected']==c['expected'] and row['hard_assertion']==c['hard_assertion']
  exp=(row['expected'],row['hard_assertion']);assert row['name'] not in expected_history or expected_history[row['name']]==exp,row['name'];expected_history[row['name']]=exp
  if not row['hard_assertion']:assert row['expected']=={}
  if not row['passed']:failures.append(row['name'])
 assert failures==[x['name'] for x in summary['all_failures']]
 all_attempts.append({'directory':str(root),'case_N':len(results),'hard_N':sum(r['hard_assertion'] for r in results),'hard_passed_N':sum(r['hard_assertion'] and r['passed'] for r in results),'hard_failed_N':sum(r['hard_assertion'] and not r['passed'] for r in results),'pending_N':sum(not r['hard_assertion'] for r in results),'failure_names':failures,'expectations_unchanged_across_all_attempts':True})
assert len(all_attempts)==8
last_results=load(last/'results.json');last_summary=load(last/'summary.json');quotes=load(O/'finite-control-exact-quotes-readback.json')
assert (quotes['case_N'],quotes['hard_passed_N'],quotes['hard_failed_N'],quotes['pending_N'])==(189,165,9,15)
pop=load(G/'08-audits/current-machine-rare-disagreement-semantic-20261011-sol/population-membership-metadata.json');opened=load(O/'actual-opened-exposed-packets-and-used-quote-resources.json')
ids={x['source_id'] for x in opened['packet_bindings']};assert len(ids)==98 and ids<=set(pop['exposed_ids_in_frame_order']) and not ids.intersection(pop['remaining_ids_in_frame_order']) and not ids.intersection(pop['human200_source_ids_excluded'])
gate=load(O/'independent-AST-and-new-body-inventory.json')['frozen_gate']
synthetics={}
for x in lastpre['controls']:
 for c in load(x['path'])['cases']:
  if 'semantic_input' in c:synthetics[c['name']]=c
outside=[]
for row in last_results:
 if row['name'] in synthetics:
  text=synthetics[row['name']]['semantic_input']['text'];norm=re.sub(r'(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])','', ''.join(unicodedata.normalize('NFKC',ch) for ch in text))
  if not re.search(gate,norm):
   assert row['candidate']['decisions']==row['baseline']['decisions'];outside.append(row['name'])
assert not any(last_summary[k] for k in ['SEEc_complete_decision_mismatch','outside_gate_complete_decision_mismatch','restricted_mother_unproved_positive','filesystem_access_attempts'])
for key in ['manifest_binding','baseline_prediction_binding','selector_binding']:verify(contract[key])
for x in contract['old_modules']+contract['candidate_modules']+contract['manual_static_audit']['proof_artifact_bindings']:verify(x)
base=load(B/'report.json');assert base['inherited_v7_record_N']==4474 and base['actual_v8_delta_record_N']==7 and base['exact_ordered_ids_and_packet_bindings_equal_v7_and_previous_independent_readback']
root_interfaces=[bind(G/'08-audits'/n) for n in ['prepare-rule-v9-affected-execution-root.py','merge-rule-v9-affected-composite-root.py']]
for x in root_interfaces:inputs[x['path']]=x;ast.parse(Path(x['path']).read_text())
for n in ['input-bindings-initial.json','finite-quote-input-bindings.json']:
 for x in load(O/n)['inputs']:verify(x)
helper_names={'relations':['norm','same_component','ordinal_number','sentence_spans','_closed_primary_programme','_primary_role_quotes','_se_current_geometry_contexts','_se_geometry_value','_se_same_geometry','_se_parent_binding','_se_parent_span_geometry','_se_next_geometry','_quote','context_anchor','proposition','current_anchor','linked','traces','_used_views','_add','object_evidence'], 'dimensions':['_norm','_object','_context_text','_form_only','_document_name_only','_publication_purpose','_publication_content_spans','_administrative_innovation_owner','_unique_contexts','add','boundary','finish','_units'], 'evidence':['matching_view','raw_span','anchor','context_anchor','_context','make_decision']}
helpers=[]
for module,names in helper_names.items():
 tree=ast.parse((C/(module+'.py')).read_text())
 for node in ast.walk(tree):
  if isinstance(node,ast.FunctionDef) and node.name in names:
   targets=[]
   for n in ast.walk(node):
    if isinstance(n,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
     for t in n.targets if isinstance(n,ast.Assign) else [n.target]:
      if isinstance(t,(ast.Attribute,ast.Subscript)):targets.append(ast.unparse(t))
   helpers.append({'module':module,'name':node.name,'line':node.lineno,'AST_sha256':hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest(),'assignment_targets':targets,'calls':sorted({ast.unparse(q.func) for q in ast.walk(node) if isinstance(q,ast.Call)})})
save('transitive-helper-and-all-attempt-readback.json',{'all_attempts':all_attempts,'final_modules_byte_same_final_control_snapshot':True,'every_control_source_and_code_snapshot_exact':True,'expectations_and_empty_pending_preserved':True,'outside_gate_synthetic_cases':outside,'transitive_helpers':helpers,'classifier_executed':False})
# Explicitly require every delivered actual member; this includes the essential46,
# all control input sets/snapshots/runners and all prior true failures.
required={'candidate_delivery':bind(D/'output-seal.json'),'independent_readback_complete':True,'required_candidate_members':s['files'],'includes_static_proofs_and_all_finite_controls_and_readback':True,'explicit_minimal_essential_member_N':46,'explicit_delivered_member_N':117,'control_input_member_N':len(control_input_members),'snapshot_member_N':len(snapshot_members),'independent_readback_artifacts':[bind(O/'independent-AST-and-new-body-inventory.json'),bind(O/'finite-control-exact-quotes-readback.json'),bind(O/'transitive-helper-and-all-attempt-readback.json')],'classification_executed':False}
save('ROOT-ready-required-candidate-members.json',required)
report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'approved_static_scope_contract_for_provisional_delta_only','candidate_delivery':bind(D/'output-seal.json'),'candidate_freeze':bind(D/'candidate-freeze.json'),'candidate_modules':f['candidate_modules'],'selector_binding':f['selector_binding'],'sealed_members_verified_N':117,'explicit_required_verified_N':46,'final_code_snapshot_identical':True,'complete_old_AST_restored_after_removing_new_definitions_constant_and_one_guard_per_module':True,'unchanged_source_evidence_receipt_module_N':3,'record_local_only':True,'new_kind':'v9_IF_relationship','builder_shared_mutations':['self.relations append via unchanged _add','self.source_relation_traces rebuilt via unchanged _add'],'builder_cannot_mutate_contexts_unit_original_bundle_requests_caches':True,'old_unit_kind_filter_excludes_new_kind':True,'old_object_evidence_only_current_parent_heading_parent_predicate_anaphor':True,'consumer_mutations':['acc.positive I/F entries','acc.excluded I/F entries','acc.boundaries I/F entries'],'affected_dimensions_validated_nonempty_unique_IF_subset':True,'helper_purity_reason':'geometry, source quote, programme closure and object/form helpers read existing record only; _add writes relation/traces only, Unit/add/boundary produce per-record IF decisions; no imports, IO, global/nonlocal or cross-record cache in new route','ordered_parent_proof':'same source/component, complete member original paragraph equality, current fragment unique, both source_lines if present agree, contiguous sequence/monotonic source lines/parent ids/first-last/next-top-number closure; conflicts stop','static_selector_review':'same exact gate and per-character NFKC/CJK whitespace view as old evidence; both new effects dominated by gate; includes every reachable old1/0/null whole record regardless labels/IDs/department; failed binding or incomplete decision forbids reuse; missing static proof forces all4481','full_population_selector_executed':False,'actual_selected_record_N':None,'classifier_runs_by_this_audit':0,'baseline_mixed_origin':{'v7_actual':4474,'v8_actual':7,'all4481_actually_v8':False,'compatible_exact_frozen_v8_proof':bind(B/'report.json')},'final_controls':{'cases':189,'real_pairs':130,'real_unique_packet_ids':98,'synthetics':59,'hard':174,'hard_passed':165,'hard_failed':9,'pending':15,'failure_names':[x['name'] for x in last_summary['all_failures']],'S_E_Ec_complete_decisions_equal_N':189,'exact_quote_checks':2326,'unique_quote_resources':353,'all_expected_preserved':True,'expected_failure_is_not_adjudicated_true_error':True},'boundary_qualification':'00093/F catch-all expected1 may not inherit shortage sibling; 01382/01402 distinguish original asset binding from actually supplied packet projection; eight real failed expectations are not eight independently adjudicated false negatives; one unchanged old E synthetic failure remains outside IF repair scope','focused_semantic_findings':{'01391':'same self-data applicant cannot borrow original innovator protection; preserve valid current innovator rights','01430_01435_01436':'exact ordinary three-class table row cannot borrow innovative sibling row','02235_02229':'explicit innovative RND beneficiary and actual service/allocation support self-contained I3','01482':'same-stage closed qualification/admission/service chain can carry the specific domestic target treatment gap branch; rarity or advantage alone cannot','00068_00071':'restricted mother intersection unproved; keep declared IF/I boundary, no whole programme donation'},'opened_packet_bodies_this_final_phase_N':98,'opened_packet_scope':'frozen130 selected exposed98 only; technical range checking, no repeated all130 semantic adjudication; no human200/remaining or external originals opened','ROOT_interfaces_static_only':root_interfaces,'ROOT_preparation_constraints':'explicit actual candidate-delivery/freeze path and exact candidate directory; all required bindings in total seal; same frozen common line subset/ordered ids/UTF8 spans; unchanged adapter/status bridge; driver only bounded count/version/source binding adaptation; no actual classifier during preparation','ROOT_merger_constraints':'actual adoption prep/selection/delivery equals plan, bound delta scope/freeze/algorithm/preseal; adoption strictly before execution; completed single cohort and zero technical failures; full Cartesian slot keys before output; all S/E/Ec complete decision unchanged; unselected literal parent and selected literal delta bytes plus true origins','post_selection_execution_obligations':['ROOT must execute exact static selector on all4481 and bind actual scope/contract/member list before run; selected count is not claimed here','ROOT must seal actual source-identical subset and original ordinal/UTF8 byte lineage; preserve whole original packet chain and old positives/null/negatives','ROOT adoption sidecar must precede actual delta and bind actual independent static contract, candidate total seal/freeze/algorithm/selection/preparation/source lineage','After single zero-technical-failure delta, verify actual receipts, each selected IF decision/source traces, S/E/Ec complete equality, literal merged bytes, all22405slots and true v7/v8/v9 origins','Recalculate actual diagnostics using proper NA/coverage; development finite expectations do not become gold/accuracy; formal and paper gate remain false'],'fallback_obligation':'If an exact binding, record-local proof, unchanged wrapper/adapter/source or mixed-parent equivalence is absent, do not reuse outside selected gate: full4481 fallback (no classifier run performed here).','semantic_acceptance_complete':False,'formal_validation_complete':False,'paper_final_results_ready':False,'preparation_failure_preserved':'preparation-error01.json: independent allowlist omitted pure returned dict.get; before any audit output; audit predicate corrected, candidate untouched; not a machine runtime failure','changes_to_machine_manual_reference_source_progress':False}
save('readiness-report.json',report)
md='''最终封印候选通过独立静态采用审计，可由 ROOT 作为下一轮暂定修复执行。此结论只批准完整影响范围与记录隔离，不代表全部新语义已验收，也不代表正式验证或论文结果完成。\n\n实际总封印117成员、明示必需46成员全部按绝对路径/字节/SHA读回。最终五模块与 attempt08 快照逐字相同；三个来源/证据/receipt模块不变，删除新增定义、常量和各唯一入口后恢复完整v8 AST。新增builder只追加独有关系及trace；旧六类unit和object读取不能消费新kind。新consumer只改I/F，本次未运行分类器或全4481 selector。\n\n最后189控制包含冻结130维项的98个已暴露包和59合成控制；174硬期待中165通过、9失败，另15待定空期待保持。全部189项S/E/Ec完整decision相同；2326精确引文检查、353唯一资源检查通过。八轮原期待、控制、代码快照和真实失败完整保留。原期待失败不等于已裁定真错误：00093/F开放兜底不自动继承短缺兄弟；01382/01402应区分原资产绑定与包内有限投影供应。另一个旧E反例失败仍属本次I/F范围之外。\n\n旧底稿实际来自4474条v7与7条v8，已有封印证明其与冻结v8语义兼容。候选两个入口均受同一当前正文gate控制；selector覆盖所有可达整条记录和全部原有依据，包含旧1、旧0与null，不以130、真人值、机器值、ID或部门缩小范围。任何源绑定、完整decision或隔离证明缺失均禁止复用；全4481 fallback仍是未执行的退路。\n\n01391自身数据、01430/35/36普通表行的错对象撤销可支持有限通用修正；02235/02229须由明文创新研发受益对象与服务成立；01482须以同阶段完整资格—纳入—服务链承接具体缺口。00068/71受限母对象的交集仍未证明，不能复制整程序或兄弟支。父治理要求完整原段相等、fragment唯一、source_lines不冲突及封闭ordered边界，不以相同component单独作继承。\n\nROOT准备与合并接口仅静态检查并按实际hash绑定。ROOT接下来必须先执行静态selector、封实际scope与原字节lineage、在实际推理前记录采用，再核实际零技术失败delta与合并原/新逐行字节、完整22405槽位和真实执行来源。此处没有提前给出实际选中数或运行结论。参考、手册、原包、机器输出和progress均未修改。\n\n预备审计一次失败已保留：纯helper返回dict.get漏入审计白名单，发生于产出之前；修正审计检查器后复核成功，候选源码未改。这不是机器运行失败。\n'''
with (O/'readiness-report.md').open('x',encoding='utf8') as out:out.write(md)
approved=copy.deepcopy(contract);approved['schema_version']='v9_static_impact_contract_independent_A_1';approved['candidate_delivery_binding']=bind(D/'output-seal.json');approved['candidate_freeze_binding']=bind(D/'candidate-freeze.json');approved['manual_static_audit'].update(approved=True,identity='independent A exact final-source static scope/IF isolation audit; provisional delta only, semantic/formal validation remains false')
approved['manual_static_audit']['proof_artifact_bindings'] += [bind(O/n) for n in ['readiness-report.json','independent-AST-and-new-body-inventory.json','transitive-helper-and-all-attempt-readback.json','finite-control-exact-quotes-readback.json','ROOT-ready-required-candidate-members.json']]
approved['semantic_acceptance_complete']=False;approved['formal_validation_complete']=False;approved['actual_selector_or_classifier_executed_by_independent_audit']=False
save('approved-static-selector-contract.json',approved)
for x in inputs.values():assert bind(x['path'])==x,x['path']
save('input-bindings-final.json',{'inputs':list(inputs.values()),'all_exact_before_after':True,'candidate_frozen_unchanged':True,'old_artifacts_unchanged':True})
files=[bind(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='output-seal.json']
save('output-seal.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'independent_static_readiness_and_binding_readback_sealed','files':files,'input_bindings':list(inputs.values()),'classifier_or_selector_runs':0,'approval_is_static_scope_only':True,'semantic_acceptance_complete':False,'formal_validation_complete':False,'self_excluded':True})
print(json.dumps({'output':str(O),'seal':bind(O/'output-seal.json'),'approved_contract':bind(O/'approved-static-selector-contract.json'),'required_members':bind(O/'ROOT-ready-required-candidate-members.json'),'report':bind(O/'readiness-report.json'),'files_N':len(files),'all_inputs_N':len(inputs),'root_interfaces':root_interfaces},ensure_ascii=False,indent=2))

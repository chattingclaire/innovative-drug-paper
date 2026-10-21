from pathlib import Path
import ast,difflib,json,hashlib,datetime,re
ROOT=Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
P=ROOT/'06-coding/rule-five-dimension-joint-root/versions/joint-v4-structure-normalization-sol'
B=P.parent/'joint-v3-interface-sol'
AUDIT=ROOT/'08-audits/five-dimension-joint-v3-independent-sol'
EX=AUDIT/'execution-joint-v3-interface-sol'
NAMES=['source_packet','source_receipts','evidence','relations','dimensions']
AT=datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):return json.loads(Path(p).read_text())
def bind(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p.resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def verify(b):assert bind(b['path'])==b,b['path']
def dump(name,value):
 f=P/name;assert not f.exists(),str(f);f.parent.mkdir(exist_ok=True,parents=True);f.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');return bind(f)
def write(name,s):
 f=P/name;assert not f.exists(),str(f);f.write_text(s);return bind(f)
def functions(path):
 tree=ast.parse(path.read_text());out={}
 def walk(nodes,prefix=''):
  for n in nodes:
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    source='\n'.join(path.read_text().splitlines()[n.lineno-1:n.end_lineno])
    out[prefix+n.name]=dict(line=n.lineno,end_line=n.end_lineno,ast=ast.dump(n,include_attributes=False),source=source,source_sha256=hashlib.sha256(source.encode()).hexdigest())
   elif isinstance(n,ast.ClassDef):walk(n.body,prefix+n.name+'.')
 walk(tree.body);return out,tree
pre=load(P/'pre-execution-seal.json')
for b in pre['five_modules']+[pre['algorithm_bindings'],pre['manual']]+pre['common_frozen_input_bindings']:verify(b)
changes=[];counts={};constchanges=[];maps={}
for name in NAMES:
 before,tb=functions(B/f'{name}.py');after,ta=functions(P/f'{name}.py');maps[name]=(before,after)
 rows=[]
 for fn in sorted(before.keys()|after.keys()):
  old,new=before.get(fn),after.get(fn)
  if (old or {}).get('ast')==(new or {}).get('ast'):continue
  rows.append(dict(module=name+'.py',function=fn,status='new' if old is None else 'removed' if new is None else 'modified',before={k:v for k,v in old.items() if k!='ast'} if old else None,after={k:v for k,v in new.items() if k!='ast'} if new else None))
 changes+=rows;counts[name+'.py']=len(rows)
 def constants(tree):return {ast.dump(n.targets if isinstance(n,ast.Assign) else n.target,include_attributes=False) if isinstance(n,ast.AnnAssign) else str([ast.dump(t,include_attributes=False) for t in n.targets]):ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.Assign,ast.AnnAssign))}
 c1,c2=constants(tb),constants(ta)
 for key in sorted(c1.keys()|c2.keys()):
  if c1.get(key)!=c2.get(key):constchanges.append(dict(module=name+'.py',target=key,before=c1.get(key),after=c2.get(key)))
 if rows:
  write(f'{name}-v3-to-v4.patch',''.join(difflib.unified_diff((B/f'{name}.py').read_text().splitlines(keepends=True),(P/f'{name}.py').read_text().splitlines(keepends=True),fromfile=str(B/f'{name}.py'),tofile=str(P/f'{name}.py'))))
assert counts=={'source_packet.py':0,'source_receipts.py':0,'evidence.py':0,'relations.py':16,'dimensions.py':3}
assert not constchanges
shared=[('relations','RelationView._add'),('dimensions','_units'),('dimensions','_generic'),('dimensions','judge')]
for module,fn in shared:
 before,after=maps[module];assert before[fn]['ast']==after[fn]['ast'],fn
fd=dump('function-diff.json',dict(identity='nonhuman AST and source-level candidate comparison',baseline_algorithm=bind(B/'algorithm-bindings.json'),final_algorithm=bind(P/'algorithm-bindings.json'),effective_function_changes_N=len(changes),changed_count_by_module=counts,constant_changes=constchanges,functions=changes,shared_unchanged=[dict(module=m,function=f,before=maps[m][0][f]['source_sha256'],after=maps[m][1][f]['source_sha256']) for m,f in shared],note='__init__ only additionally initializes structural_address_issues; consumer identity, deduplication, request resolution, geometry proof, and boundaries remain as v3 unless listed here.'))
md='v4 相对已封存 v3 有效函数差异：19项（relations 16，dimensions 3），顶层常量改动0。source_packet、source_receipts、evidence原字节不变。\n\n|模块|函数|变化|v3行|v4行|\n|---|---|---|---|---|\n'
for r in changes:md+=f"|{r['module']}|{r['function']}|{r['status']}|{r['before']['line'] if r['before'] else '—'}|{r['after']['line'] if r['after'] else '—'}|\n"
md+='\n详细有效源码、SHA及统一补丁见 function-diff.json、relations-v3-to-v4.patch、dimensions-v3-to-v4.patch。共享 _add/_units/_generic/judge 有效AST未改。\n'
write('function-diff.md',md)
# Exact manual quotes bound before semantic changes; no changed definition.
additional=load(P/'additional-control-pre-edit-seal.json');manual=Path(pre['manual']['path']).read_text();manualbytes=Path(pre['manual']['path']).read_bytes()
for q in additional['manual_quotes']:
 a,b=q['unicode_code_point_interval_half_open'];u,v=q['utf8_byte_interval_half_open'];assert manual[a:b]==q['text'];assert manualbytes[u:v].decode()==q['text']
# Use the already exposed audit's saved source-only case text and supplied contexts.
# Do not open a source_ref absolute path, especially not missing original sections.
fail=load(EX/'failure-full-inputs-and-paths.json');final12=load(P/'exposed12-attempt01/results.json');by12={r['name']:r for r in final12}
basis_cases=[];quote_N=0
for index,c in enumerate(fail['cases']):
 fixed=c['unchanged_presealed_full_case'];bundle=fixed['synthetic_bundle'];current=bundle['source_record'];supplied=current.get('contexts',[])
 docs={d['binding']['sha256']:d for d in fixed['synthetic_documents']}
 quotes=[]
 for item in [current]+[x for x in supplied if x.get('text')]:
  ref=item.get('source_ref',{});loc=ref.get('locator',{});sha=ref.get('sha256');text=item.get('text','');a=loc.get('unicode_code_point_interval_half_open');u=loc.get('utf8_byte_interval_half_open')
  if sha in docs and a is not None:
   literal=docs[sha]['text'];assert literal[a[0]:a[1]]==text,(c['name'],item.get('context_id'))
   assert hashlib.sha256(literal.encode()).hexdigest()==sha
   if u is not None:assert literal.encode()[u[0]:u[1]].decode()==text
   quote_N+=1
  quotes.append(dict(context_id=item.get('context_id'),role='current' if item is current else item.get('kind'),text=text,source_ref=ref,structure=item.get('structure',{}),locator_validated_against_saved_audit_literal=True if sha in docs and a is not None else False))
 basis_cases.append(dict(name=c['name'],audit_failure_case_index=index,origin=bind(EX/'failure-full-inputs-and-paths.json'),expected_original=fixed['expected_values_fixed_before_execution'],v4_actual=by12[c['name']]['observed'],original_failure=c['review'],current_and_supplied_context_quotes=quotes,current_source_only_bundle_sha256=hashlib.sha256(json.dumps(bundle,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),unprovided_original_sections_are_not_consumed=True))
semantic_notes=[dict(type='I3 actual admitted-project service',functions=['RelationView._IF_named_feedback_access'],manual_lines=[9,52,124,127,135,137,139],relation='Current actual access/appointment + only one fully bounded same-version/component programme + one direct beneficiary/service definition + same research stage. 本/该 is resolved locally; a title or parallel substantive eligibility is insufficient.',positive_control=0,negative_control=1),dict(type='I3 same-current comparative convenience',functions=['_same_current_RND_comparative_support','_innovation'],manual_lines=[9,124,127],relation='One immediate antecedent in the same current semicolon proposition explicitly makes an innovation RND special channel available; explicit anaphor, shortened review time and ordinary-procedure comparison connect the current convenience. Numeric time alone, other drug and ordinary common time are insufficient.',positive_control=2,negative_control=3),dict(type='F current substantive continuous-treatment obstacle',functions=['_fairness'],manual_lines=[9,11,15,147,151,158],relation='Target patient + inability to continue obtain/receive needed medicine treatment is substantive F evidence. Added 得到/接受 as the same relation already recognized for 获得/取得/获取. A compensation arrangement is unnecessary for substantive information verification; general logistics, bare accessibility fields and signatures are insufficient.',positive_control=4,negative_control=5)]
dump('semantic-change-basis.json',dict(identity='nonhuman development semantic repair basis, not a human gold standard',manual=pre['manual'],exact_pre_bound_manual_quotes=additional['manual_quotes'],definition_changes=False,source_of_exposed_development_feedback=bind(EX/'output-seal.json'),already_exposed_failure_cases=basis_cases,saved_literal_quote_location_checks_N=quote_N,repair_types=semantic_notes,actual_source_ids_newly_read=[],source_ref_absolute_paths_opened_by_classifier=0,absolute_unprovided_source_sections_not_used=True))
# Callsites and type constraints are matching gates, never a text/cohort whitelist.
callsite=[dict(function=r['function'],before_line=r['before']['line'] if r['before'] else None,after_line=r['after']['line'] if r['after'] else None) for r in changes if r['module']=='relations.py' and r['function']!='RelationView._IF_named_feedback_access']
dump('structure-address-callsite-review.json',dict(identity='nonhuman neutral metadata interface repair',source_packet_interface=bind(P/'structure-interface-observation.json'),raw_metadata_unchanged=True,accepted_scalars='positive exact int (bool excluded); positive decimal digit or Chinese ordinal string; existing full article/clause literal address string',rejected_types='bool, float, list, dict, explicit null, negative/zero or malformed number',original_heading_conflict='A supplied article/clause/index must not contradict any actual original heading. Invalid or conflicting metadata blocks that address binding and keeps the appropriate unresolved dependency.',no_number_used_as_original_quote=True,no_metadata_number_proves_closure=True,closure='Original text head, actual same-source/component ordered members and existing genuine next boundary/group proof are still required. An explicit clause consumes only that clause; siblings prove bounds without donating substance.',affected_callsites=callsite,matching_view_original_text_calls_after_repair=[dict(line=i+1,text=s) for i,s in enumerate((P/'relations.py').read_text().splitlines()) if re.search(r"norm\(st\['article'\]\)",s)],unsafe_direct_norm_structure_article_or_clause_remaining=0,opaque_article_id_identity_unchanged=True,request_scope='Each stopped cited standard keeps typed dimensions; judge uses affected_dimensions intersect only_IF. Known independently positive dimensions stay1. No all-request clearing or numeric zero fallback introduced.',retained_diagnostic_scope_risk='A structural issue whose original_article_number is None may be attached to another unresolved article request. This is a diagnostic-range limitation; it is not counted as an executed classification bypass or changed consumer scope.'))
# All executions and all failures remain separate, including baseline/intermediates.
runnames=['baseline-v3-controls6','attempt01-controls6','attempt02-controls6','numbering-positive2-baseline','semantic6-before-edit','semantic6-attempt01','exposed12-attempt01','final-parent235','final-exposed20','final-original75','final-numbering2','final-original6']
runs=[];seal_checked_N=0
for name in runnames:
 folder=P/name;summary=load(folder/'summary.json');results=load(folder/'results.json')
 if name=='final-original75':
  # Collect first, then write the receipt, so a partially-written receipt is never self-bound.
  members=[bind(f) for f in sorted(folder.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f.name!='output-seal.json']
  dump(name+'/output-seal.json',dict(identity='nonhuman post-execution receipt for unchanged original75 runner',at_utc=AT,execution_already_finished=True,not_a_pre_execution_seal=True,output_members=members,self_in_output_members=False))
 seal=load(folder/'output-seal.json');members=seal.get('members',seal.get('output_members',[]))
 assert members,name
 for b in members:verify(b);seal_checked_N+=1
 failing=[dict(row_index=i,full_record=r) for i,r in enumerate(results) if not r.get('passed',False)]
 runs.append(dict(name=name,summary=summary,summary_binding=bind(folder/'summary.json'),results_binding=bind(folder/'results.json'),output_seal=bind(folder/'output-seal.json'),verified_member_N=len(members),failed_original_records=failing))
final235=load(P/'final-parent235/results.json');base235=load(B/'final-parent235/results.json')
assert len(final235)==len(base235)==235
assert all(x['observed']==y['observed'] and x['expected']==y['expected'] for x,y in zip(final235,base235))
fixtures=load(P/'controls6-fixed-before-edit.json')['cases'];final6=load(P/'final-original6/results.json')
assert len(fixtures)==len(final6)==6
assert all(x['expected']==y['expected'] and x['synthetic_input']==y['semantic_input'] for x,y in zip(fixtures,final6))
for file,key,run in [('controls2-numbering-positive-fixed.json','expected','final-numbering2'),('controls6-semantic-fixed-before-edit.json','expected','semantic6-attempt01')]:
 fx=load(P/file)['cases'];rr=load(P/run/'results.json');assert all(x[key]==y['expected'] and x['synthetic_input']==y['semantic_input'] for x,y in zip(fx,rr))
for plan,run in [(AUDIT/'controls12-fixed-before-execution.json','exposed12-attempt01'),(ROOT/'08-audits/five-dimension-joint-independent-controls-sol/controls20-fixed-before-execution.json','final-exposed20')]:
 fx=load(plan)['cases'];rr=load(P/run/'results.json');assert len(fx)==len(rr)
 assert all(x['expected_values_fixed_before_execution']==y['expected'] for x,y in zip(fx,rr))
for b in pre['fixed_development_controls']:verify(b)
retained=[]
for name in ['final-parent235','final-exposed20','final-original6']:
 rr=load(P/name/'results.json')
 for i,r in enumerate(rr):
  if not r['passed']:
   if name=='final-original6':why='原fixture将实际下一条第十一条的metadata也设为10/字符串10，已有原文头与编号冲突；原预期1未改，输出NULL保留。另行固定两条编号/原文真正一致的正向对应例，不能据其通过覆盖本差异。'
   elif name=='final-exposed20':why='确指第10条已给独立过敏风险实质证据，S=1有据；第12条仍缺关键标准且stopped，I/F及合理未知维保留NULL。原S=NULL预期保留，不为匹配抹去S阳性。'
   elif r['name']=='foreign_single_unlisted_not_no_options':why='单品种境内未上市不等于目标治疗无获批选项；原F0/实际NULL的冻结手册边界保留。'
   elif r['name']=='direct_payment_child_condition':why='原夹具实际字符顺序current→parent，paragraph/sequence却parent→current；已提供同源跨度冲突，拒绝承接。原Ec1/实际0保留。'
   elif r['name']=='protection_base_and_exception_separate':why='创新资格主权利实质分支仍I1；显式例外款缺闭合，F未知依赖未清空或硬赋0。'
   else:why='原控制缺实际父/清单闭合或完整源末界，原预期及实际NULL均保留；不以题名、句号或boundary字段声明代替闭合。'
   retained.append(dict(run=name,row_index=i,reason=why,record=r))
dump('retained-failures.json',dict(identity='nonhuman original fixed expectations and actual discrepancies retained',remaining_final_discrepancy_rows_N=len(retained),developer_references_are_not_gold=True,records=retained,baseline_and_intermediate_errors_preserved=True,construction_exception_is_not_semantic_NULL=True))
reception=dump('finite-runs-reception.json',dict(identity='nonhuman finite development regressions only',at_utc=AT,run_N=len(runs),case_execution_N=sum(r['summary'].get('case_N',r['summary'].get('test_N',0)) for r in runs),runs=runs,run_seal_member_readback_N=seal_checked_N,v3_parent235_all_five_outputs_identical=True,v3_parent235_all_expectations_identical=True,original6_inputs_and_expectations_identical=True,new_numbering2_and_semantic6_fixed_before_edit=True,exposed12_and20_expectations_unchanged=True,expectations_not_passed_to_classifiers=True,post_view_operations_of_parent235_preserved=True,all_final_finite_constructions_succeeded=True,known_positive_and_separate_stopped_reference_both_retained=True,no_new_cohort_runs=True,not_formal_accuracy_or_independent_acceptance=True))
source_log=load(B/'source-reading-log.json')
for b in source_log['75_packet_byte_bindings']:verify(b)
dump('source-reading-log.json',dict(identity='非真人有限开发来源读取日志',new_actual_source_ids=[],new_policy_semantic_reads_outside_prior_exposed_fixtures=[],original75_existing_packet_source_ids=source_log['75_existing_packet_fixture_source_ids'],original75_packet_byte_bindings=source_log['75_packet_byte_bindings'],original75_previous_source_reading_log=bind(B/'source-reading-log.json'),prior_parent235_full_inputs_replayed=True,exposed_old12_source_only_bundles_replayed=True,new_numbering6_then2_and_semantic6_are_synthetic=True,absolute_source_ref_paths_not_resolved_during_classification=True,synthetic_source_quote_checks_use_already_exposed_audit_literal_not_absolute_source_files=True,new_hidden_v4_controls_read=False,new_actual_S3_plan_read=False,main_full_LLM_partial_labels_read=False,cohort77_800_4481_run=False,new_neutral_projection_used=False,manual_material_formal_prediction_modified=False))
dump('peer-static-observation.json',dict(identity='nonhuman peer static-only observation, not an independent classification audit',peer='/root/audit800_innovation_first22',classification_executions=0,hidden_controls_or_actual3_plan_read=False,observed_module_bindings=pre['five_modules'],confirmed_shared_unchanged=['_add','_units','_generic','judge'],typed_consumers_intersection_confirmed=True,source_packet_receipts_evidence_bytes_unchanged=True,structure_scalar_rejection_and_heading_conflict_confirmed=True,structure_validity_is_not_closure=True,semantic_increments_must_be_explicitly_declared=['same-plan current appointment feedback','same-current innovation RND comparative time','continuous treatment 得到/接受 barrier'],unexecuted_diagnostic_scope_risk='original_article_number=None 的无关结构issue可附某次未决请求，仅记录诊断范围，未宣称已执行标签绕过。'))
summary=dict(identity='非真人 GPT-6.1 Sol ultra 开发候选，非真人编码、非正式准确率',status='sealed_algorithm_development_candidate_not_deployed',algorithm_bindings=bind(P/'algorithm-bindings.json'),pre_execution_seal=bind(P/'pre-execution-seal.json'),effective_function_changes_N=19,constants_changed_N=0,only_changed_modules=['relations.py','dimensions.py'],unchanged_modules=['source_packet.py','source_receipts.py','evidence.py'],final_runs=[dict(run=r['name'],case_N=r['summary'].get('case_N',r['summary'].get('test_N')),matched=r['summary'].get('matched',r['summary'].get('pass_N')),exceptions=r['summary'].get('exceptions',0),evidence_validated=r['summary'].get('evidence_validated'),failed_N=len(r['failed_original_records'])) for r in runs if r['name'] in ['final-original75','final-parent235','final-exposed20','exposed12-attempt01','final-numbering2','semantic6-attempt01','final-original6']],all_runs_N=12,all_case_executions_N=382,remaining_final_fixed_discrepancy_rows_N=11,new_actual_source_ids=[],no_formal_acceptance_or_cohort_run=True,definitions_materials_predictions_unchanged=True,original_expectations_and_failures_preserved=True,hidden_new6_and_actual3_not_read_or_executed_by_owner=True)
dump('summary.json',summary)
write('README.md','''v4 为非真人开发候选，最终算法在新的隐藏6项及历史实际3条执行前封存，不是正式发布或部署。\n\n修复条/款编号的中性接口类型：合法整数、数字字符串和中文序数只用于匹配。元数据与实际条款头矛盾、非法类型或未核明边界会保留相应未决依赖，不产生引文、闭合证明或0兜底。原文、同源/组件及下一边界要求继续适用。\n\n另按冻结手册修复三类已暴露的语义缺口：纳入后当前可用的同计划上市前研发反馈；同一当前命题分号后明确承接创新研发对象的相对普通程序缩时；实质核验患者无法持续得到/接受所需治疗的具体障碍。均保留对象—当前行动—直接联系，未借并行资格或兄弟内容赋值。\n\n实际有限回归：原75为75/75；原235为227/235；暴露20为19/20；已暴露12为12/12；新增正确编号2为2/2；新增语义6为6/6；原编号6为4/6。原6两个下一条编号矛盾夹具仍保留原预期1/实际NULL。235的8处原差异与20的已知S1/原预期NULL差异均保留；完整记录在 retained-failures.json。所有最终有限构造成功，350项含标准证据验证的最终结构/语义回放均完成原引文验证；75为原开发脚本断言验证，不能合并为独立准确率。\n\n保留12次382项有限执行及全部代码快照、首次失败和固定预期。原12审计首次存储失败与授权runner attempt02分开记录，不冒充首次结果。v4相对v3为19项有效函数变化，常量0；共享_add/_units/_generic/judge不变，typed消费者与only_IF仍取交集。\n\n新实际source_id读取0。未运行77/800/4481，未读取主LLM标签、未来隐藏6或历史实际3计划，未接新neutral投影。有限开发复审不作为真人金标准或正式验收。新独立结果若提出问题，另版本处理，不覆盖v4。\n''')
# Correct count: final evidence validation excludes75; 235+20+12+2+6+6=281.
# README uses explicit 281 finite structural/semantic validations.
readme=(P/'README.md').read_text().replace('350项含标准证据验证的最终结构/语义回放','281项含标准证据验证的最终结构/语义回放')
(P/'README.md').write_text(readme)
validation=dict(identity='mechanical binding/integrity checks without classification execution',at_utc=AT,final_five_modules_match_preseal_and_final_run_snapshots=True,manual_quotes_unicode_and_utf8_verified_N=len(additional['manual_quotes']),supplied_exposed_failure_quote_locations_verified_N=quote_N,exposed12_original_output_seal_members_verified=load(P/'exposed12-reception-bindings.json')['verified_output_member_N'],v3_parent235_all5_outputs_and_expected_unchanged=True,original6_inputs_expected_unchanged=True,new_control_input_expected_fixed_integrity=True,original75_packet_bindings_verified_N=len(source_log['75_packet_byte_bindings']),effective_function_diffs_verified_N=19,constant_diffs_N=0,shared_effective_ast_unchanged=True,all_run_seal_members_verified_N=seal_checked_N,new_classifications_during_finalization=0,new_actual_source_ids=[])
dump('validation.json',validation)
# Specific candidate seal first; full delivery manifest next. Never self-bind.
dump('candidate-seal.json',dict(identity='nonhuman sealed developer candidate',at_utc=AT,algorithm=bind(P/'algorithm-bindings.json'),preseal=bind(P/'pre-execution-seal.json'),five_modules=pre['five_modules'],manual=pre['manual'],function_diff=fd,finite_runs=reception,summary=bind(P/'summary.json'),validation=bind(P/'validation.json'),module_edits_after_preseal=False,formal_release_or_deployment=False))
for b in pre['five_modules']+[pre['algorithm_bindings']]:verify(b)
members=[bind(f) for f in sorted(P.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f.name!='delivery-seal.json']
seal=dump('delivery-seal.json',dict(identity='nonhuman full v4 candidate delivery seal',at_utc=AT,status='sealed_development_candidate_not_formal_release',output_members=members,self_in_output_members=False,cache_files_excluded=True,algorithm_seal=bind(P/'pre-execution-seal.json'),new_actual_source_ids=[],independent_postseal_results_will_not_change_this_version=True))
for b in members:verify(b)
verify(seal)
print(json.dumps({'delivery_seal':seal,'candidate_seal':bind(P/'candidate-seal.json'),'output_member_N':len(members),'all_members_readback_valid':True,'algorithm':bind(P/'algorithm-bindings.json'),'preseal':bind(P/'pre-execution-seal.json'),'summary':summary},ensure_ascii=False,indent=2))

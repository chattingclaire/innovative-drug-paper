from pathlib import Path
import json,hashlib,ast,difflib,datetime,re
P=Path(__file__).resolve().parent;B=P.parent/'joint-v4-structure-normalization-sol';ROOT=P.parents[3]
AT=datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):return json.loads(Path(p).read_text())
def bind(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p.resolve()),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def verify(b):assert bind(b['path'])==b,b['path']
def dump(name,x):
 p=P/name;assert not p.exists(),str(p);p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');return bind(p)
def write(name,x):
 p=P/name;assert not p.exists(),str(p);p.write_text(x);return bind(p)
pre=load(P/'pre-execution-seal.json');initial=load(P/'input-bindings.json');fixed=load(P/'control-pre-edit-seal.json')
for b in pre['five_modules']+[pre['algorithm_bindings'],pre['manual']]+pre['common_frozen_input_bindings']:verify(b)
manual=Path(pre['manual']['path']).read_text();mb=manual.encode()
for q in fixed['manual_quotes']:
 a,b=q['unicode_code_point_interval_half_open'];u,v=q['utf8_byte_interval_half_open'];assert manual[a:b]==q['text'] and mb[u:v].decode()==q['text']
changes=[];maps={};constant_changes=[]
def fmap(path):
 text=path.read_text();tree=ast.parse(text);m={}
 def walk(nodes,prefix=''):
  for n in nodes:
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    s='\n'.join(text.splitlines()[n.lineno-1:n.end_lineno]);m[prefix+n.name]=dict(line=n.lineno,end_line=n.end_lineno,source=s,source_sha256=hashlib.sha256(s.encode()).hexdigest(),ast=ast.dump(n,include_attributes=False))
   if isinstance(n,ast.ClassDef):walk(n.body,prefix+n.name+'.')
 walk(tree.body);return m,tree
for module in ['source_packet','source_receipts','evidence','relations','dimensions']:
 a,ta=fmap(B/(module+'.py'));b,tb=fmap(P/(module+'.py'));maps[module]=(a,b)
 for name in sorted(a.keys()|b.keys()):
  if (a.get(name) or {}).get('ast')!=(b.get(name) or {}).get('ast'):
   changes.append(dict(module=module+'.py',function=name,type='added' if name not in a else 'modified',before={k:v for k,v in a[name].items() if k!='ast'} if name in a else None,after={k:v for k,v in b[name].items() if k!='ast'} if name in b else None))
 ca=[ast.dump(n,include_attributes=False) for n in ta.body if isinstance(n,(ast.Assign,ast.AnnAssign))];cb=[ast.dump(n,include_attributes=False) for n in tb.body if isinstance(n,(ast.Assign,ast.AnnAssign))]
 if ca!=cb:constant_changes.append(module)
 if (P/(module+'.py')).read_bytes()!=(B/(module+'.py')).read_bytes():
  write(module+'-v4-to-v5.patch',''.join(difflib.unified_diff((B/(module+'.py')).read_text().splitlines(keepends=True),(P/(module+'.py')).read_text().splitlines(keepends=True),fromfile=str(B/(module+'.py')),tofile=str(P/(module+'.py')))))
assert len(changes)==5 and not constant_changes
unchanged=[('relations','RelationView._add'),('dimensions','_generic'),('dimensions','judge'),('dimensions','_se_allowed'),('dimensions','_safety_effect'),('dimensions','_economics'),('dimensions','_innovation'),('dimensions','_fairness')]
for module,fn in unchanged:assert maps[module][0][fn]['ast']==maps[module][1][fn]['ast'],fn
fd=dump('function-diff.json',dict(identity='nonhuman effective function/static source comparison',baseline_algorithm=initial['baseline_algorithm'],final_algorithm=bind(P/'algorithm-bindings.json'),effective_function_changes_N=5,constant_changes_N=0,changes=changes,unchanged_functions=[dict(module=m+'.py',function=f,source_sha256=maps[m][0][f]['source_sha256']) for m,f in unchanged],unchanged_modules=['source_packet.py','source_receipts.py','evidence.py']))
md='v5相对已封存v4：5项有效函数变化，常量0。\n\n|模块|函数|变化|旧行|新行|\n|---|---|---|---|---|\n'
for c in changes:md+=f"|{c['module']}|{c['function']}|{c['type']}|{c['before']['line'] if c['before'] else '—'}|{c['after']['line'] if c['after'] else '—'}|\n"
md+='\n_add/_generic/judge、_se_allowed及五维实质判据不变。_units仅按精确原文区间身份过滤非内容引文，不扩大typed消费者。详见JSON及两份统一补丁。\n'
write('function-diff.md',md)
# Receive original actual S3 outputs only; do not call SourcePacket/RelationView/judge.
A=ROOT/'08-audits/common-candidate-actual-interface-v4-execution-sol';sa=load(A/'output-seal.json')
for b in sa['members']+sa['inputs']:verify(b)
records=load(A/'execution-results.json');quote_checks=[];source_readings=[]
for i,row in enumerate(records):
 unit=load(A/'semantic-units'/(row['record_id']+'.json'))
 byid={c['context_id']:c for c in unit['contexts']}
 for rel in row['trace']['relations']:
  for q in rel['context_evidence']:
   c=byid[q['context_id']];assert c['text'][q['start']:q['end']]==q['text'] and c['source_ref']==q['source_ref']
   quote_checks.append(dict(source_id=row['record_id'],relation_kind=rel['kind'],context_id=q['context_id'],start=q['start'],end=q['end'],text=q['text'],source_ref=q['source_ref']))
 leaves=[]
 for c in unit['contexts']:
  if c['kind']=='source_textleaf':
   a,b=c['source_ref']['locator']['unicode_code_point_interval_half_open'];leaves.append((a,b,c))
 leaves.sort(key=lambda t:t[0]);assert leaves[0][0]==0 and all(a[1]==b[0] for a,b in zip(leaves,leaves[1:]));raw=''.join(c['text'] for _,_,c in leaves);sha=unit['source_ref']['sha256'];assert hashlib.sha256(raw.encode()).hexdigest()==sha
 span=[132,1181] if i<2 else [2349,2718];next_end=raw.find('\n',span[1]);next_end=len(raw) if next_end<0 else next_end
 source_readings.append(dict(source_id=row['record_id'],source_packet=row['source_packet'],baseline_trace_row_index=i,current_text=unit['text'],current_ref=unit['source_ref'],same_primary_literal_source_sha256=sha,baseline_selected_standard_group_snapshot_span=span,standard_group_text=raw[span[0]:span[1]],actual_next_normative_boundary_text=raw[span[1]:next_end],actual_next_normative_boundary_unicode_interval=[span[1],next_end],actual_next_normative_boundary_utf8_interval=[len(raw[:span[1]].encode()),len(raw[:next_end].encode())],necessary_semantic_read_scope='current full proposition; same primary first programme relevant standard and source lines1–37; no later programme or unprovided source needed',historical_S_expected=row['expected_S'],original_v4_actual_S=row['actual_S'],other_dimensions_observation_only=row['observed_values_only']))
s3=dump('actual-S3-baseline-reception.json',dict(identity='nonhuman read-only reception of already executed historical development S3',origin_seal=initial['actual_S3_baseline_seal'],all_original_member_bindings_verified_N=len(sa['members']),all_original_input_bindings_verified_N=len(sa['inputs']),already_executed_v4_calls=sa['calls'],new_owner_v5_S3_classification_calls=0,fixed_historical_S_only=True,no_other_dimension_expectations_defined=True,source_readings=source_readings,quote_readback_checks=quote_checks,original_three_S0_kept=True,current_S3_not_a_formal_accuracy_observation=True,material_candidate_packets_are_bound_development_inputs_not_new_formal_release=True))
notes=dump('interface-change-basis.json',dict(identity='nonhuman source-only finite interface repair',manual=pre['manual'],exact_manual_quotes=fixed['manual_quotes'],definition_changes=False,repair_basis='Old source relation already resolved and quoted full finite standard, but restricted S/E/Ec consumer required verified source geometry; add neutral receipt before crossing that gate.',current_binding='Unique full current occurrence within the same snapshot programme, exact source and component consistency; supplied current/seed Unicode ranges cannot conflict. Without supplied current range, report unique raw occurrence grade rather than invented coordinates.',closure='Only actual next normative heading or actual next programme heading; EOF/finite leaf end is not a boundary. Explicit numbered members are continuous. Title and current-source proof, next heading and independent tail do not donate content.',content_unit_projection='Continuous exact original quote ranges use explicit members/headings or completed original clauses; visual continuations and qualification links remain in one quote. No dimension terms filter or skip members.',same_leaf_boundary='Exact original identity context_id+start/end+text+unchanged source_ref. A valid different non-overlapping bounded quote survives in the same leaf. Missing/contradictory quote identity or overlap stops typed consumption; different text alone is insufficient.',typed_bridge='New cited_standard relation affected_dimensions=[S,E,Ec], with actual neutral closure proof and exact current operative anchor; existing source predicate APIs remain. Old cited_standard has no unconditional allowance, only_IF consumer intersection remains unchanged.',missing_scope='Scoped provided_source_scope_unverified requests preserve stopped dependencies rather than formal0. Known independent positives remain1 through unchanged finish. No resolved request clears unrelated stopped references.',termination_tail='Only explicit numbered termination-condition members and their necessary contiguous continuation enter content. Subsequent independent source paragraph to the next actual section is retained as proof-only; original status-list paragraph is not a condition donor.',actual_S3_reception=s3,root_feedback_visual_line_scope_adjustment_preserved=True,new_actual_source_ids_outside_authorized_S3=[],new_external_hidden_controls_read=False))
run_names=['baseline-v4-controls6','attempt01-controls6','attempt02-controls6','attempt03-controls6','attempt04-controls6','final-original75','final-parent235','final02-original75','final02-parent235'];runs=[];seal_member_N=0
for name in run_names:
 f=P/name;summary=load(f/'summary.json');rows=load(f/'results.json')
 if 'original75' in name:
  members=[bind(x) for x in sorted(f.rglob('*')) if x.is_file() and '__pycache__' not in x.parts and x.name!='output-seal.json']
  dump(name+'/output-seal.json',dict(identity='post-execution exact receipt for original75',at_utc=AT,execution_already_finished=True,not_pre_execution=True,output_members=members,self_excluded=True))
 seal=load(f/'output-seal.json');members=seal.get('output_members',[])
 for b in members:verify(b);seal_member_N+=1
 failures=[dict(row_index=i,record=r) for i,r in enumerate(rows) if not r['passed']]
 runs.append(dict(name=name,summary=summary,summary_binding=bind(f/'summary.json'),results_binding=bind(f/'results.json'),output_seal=bind(f/'output-seal.json'),verified_member_N=len(members),failure_records=failures))
final235=load(P/'final02-parent235/results.json');base235=load(B/'final-parent235/results.json');assert len(final235)==len(base235)==235
assert all(x['expected']==y['expected'] and all(x['decisions'][d]['value']==y['decisions'][d]['value'] for d in ['S','E','Ec','I','F']) for x,y in zip(final235,base235))
final6=load(P/'attempt04-controls6/results.json');fx=load(P/'controls6-fixed-before-edit.json')['cases'];assert all(x['expected']==y['expected'] and x['semantic_input']==y['synthetic_input'] for x,y in zip(final6,fx))
assert (P/'regression_tests.py').read_bytes()==(B/'regression_tests.py').read_bytes()
for b in pre['five_modules']:verify(b)
failures=dump('retained-failures.json',dict(identity='original expectations/failures kept, no expectation repair',final235_remaining_original_differences_N=8,final235_failure_rows=[dict(index=i,original_record=r) for i,r in enumerate(final235) if not r['passed']],original_v4_actual_S3=[dict(source_id=r['record_id'],expected_S=r['expected_S'],actual_v4_S=r['actual_S']) for r in records],all_control_baseline_and_intermediate_failure_paths=[bind(P/n/'results.json') for n in ['baseline-v4-controls6','attempt01-controls6','attempt02-controls6']],editor_failure=bind(P/'editor-attempt01-failure.json'),unintended_unchanged_baseline_repeat_preserved=True,formal_acceptance_or_machine_gold_claim=False))
fr=dump('finite-runs-reception.json',dict(identity='nonhuman limited development execution reception',runs_N=9,case_execution_N=650,runs=runs,execution_attempt_history='baseline6; editor syntax failure then unintended same-baseline repeat6; first effective bridge6; source-member quote adjustment6; ROOT visual/qualifier source-scope adjustment6; 75/235 once each after first bridge then once each after the new scope adjustment',all_failed_versions_and_fixed_expectations_preserved=True,editor_failure_before_any_module_mutation=True,final6_matches=6,final75_matches=75,final235_matches=227,final235_all_five_outputs_identical_to_v4=True,actual_S3_not_executed_by_owner=True,hidden4_not_read=True,all_run_seal_members_readback_N=seal_member_N,new_cohort_runs=0))
previous=load(B/'source-reading-log.json');bindings=previous['original75_packet_byte_bindings']
for b in bindings:verify(b)
dump('source-reading-log.json',dict(identity='非真人有限来源读取日志',authorized_actual_source_ids=['RECODE25-00036','RECODE25-00038','RECODE25-00045'],new_actual_source_ids_outside_authorized_S3=[],source_reading_scope_and_current_quotes=s3,prior_exposed_original75_packet_ids=previous['original75_existing_packet_source_ids'],prior_original75_packet_bindings=bindings,prior_source_reading_log=bind(B/'source-reading-log.json'),source_only_synthetic_controls6=True,actual_S3_no_owner_classification=True,hidden4_not_read=True,new_v4_hidden6_not_read=True,no_main_LLM_labels_or_cohort=True,no_new_reader_or_material_release=True))
summary=dict(identity='非真人 GPT-6.1 Sol ultra 候选；非正式发布或准确率',status='sealed_developer_candidate',effective_function_changes=5,constant_changes=0,final_algorithm=bind(P/'algorithm-bindings.json'),final_preseal=bind(P/'pre-execution-seal.json'),final_development_runs=[dict(name=n,summary=load(P/n/'summary.json')) for n in ['attempt04-controls6','final02-original75','final02-parent235']],all_preserved_runs=9,case_execution_count=650,original_v4_actual_S3_remain_S0=True,owner_actual_v5_S3_runs=0,independent_hidden4_read=False,actual_source_ids_outside_authorized_S3=[],shared_consumer_permissions_unchanged=True,old_standard_not_unconditionally_allowed=True,all_original_expectations_unchanged=True,no_deployment_or_definition_material_changes=True)
dump('summary.json',summary)
validation=dump('validation.json',dict(identity='mechanical integrity/source quotation checks without classification',at_utc=AT,final_module_bindings_match_preseal_and_final6_75_235_snapshots=True,manual_exact_quotes_unicode_and_utf8_verified_N=len(fixed['manual_quotes']),actual_S3_baseline_quote_readbacks_N=len(quote_checks),actual_S3_original_seal_member_and_inputs_readback_N=len(sa['members'])+len(sa['inputs']),same_primary_full_literal_bytes_sha_for_authorized_S3_verified=True,all_run_seal_member_readback_N=seal_member_N,original6_inputs_and_expected_unchanged=True,original75_script_unchanged=True,final235_five_values_and_expected_unchanged_vs_v4=True,effective_functions_changed_N=5,constant_changes_N=0,shared_add_generic_judge_se_allowed_and_five_predicates_AST_unchanged=True,original75_packet_bindings_N=len(bindings),new_classification_during_finalization=0))
write('README.md','''v5为非真人开发候选，最终算法在独立4控制及历史实际S3重放前封存，不是正式发布或部署。\n\n现有原件有限标准关系已解析，但S/E/Ec消费门槛未收到闭合证明。候选补中性receipt：同一原件唯一当前操作命题、同源/组件及已供区间一致、连续编号成员与实际下一规范边界。EOF或有限叶截止不作闭合；无法核明保留S/E/Ec的明确依赖，不记形式0。新bridge只授权S/E/Ec；旧cited_standard不无条件放行，only_IF与typed集合交集未改。\n\n同leaf标准与边界仅按context_id不能区别。本候选按精确原文区间、text及完整source_ref区分引文；缺失/冲突区间或与边界重叠不会仅靠不同文字放行。标准完整scope保留，标题、当前来源证明、实际下一边界与独立尾段仅作证明，不捐实质内容。内容quote按明确成员或已终结原文句段组织；视觉续行及限定承接保留连续原文，不按维度词筛选成员。\n\n最终有限回归：6项预固定控制6/6，原75为75/75，原235为227/235且五维实际值与v4完全一致。8处原差异及既有三条S0全部保留。9次650项实际执行均保存：包含编辑脚本SyntaxError未写入代码后误续跑的一次原基线6项，以及必要源码变化后的有限复跑；不把重复基线称修复结果。\n\n相对v4改5个有效函数，常量0；source_packet、source_receipts、evidence原字节未动，五维判据与共享consumer权限保持。读取实际记录限ROOT已授权00036/00038/00045的当前与必要同版原文，范围在source-reading-log.json；实际S3候选分类交由ROOT封存后各一次，所有者未执行。独立4内容未读、主LLM标签未读、77/800/4481未运行，不采用新材料release。\n\n新独立结果若要求修订，另版本处理，不覆盖本候选。函数级源码、两份补丁、引用、依赖和全部实际失败见function-diff、interface-change-basis、finite-runs-reception及retained-failures。\n''')
dump('candidate-seal.json',dict(identity='nonhuman frozen developer delivery',at_utc=AT,algorithm=bind(P/'algorithm-bindings.json'),preseal=bind(P/'pre-execution-seal.json'),function_diff=fd,interface_basis=notes,finite_reception=fr,retained_failures=failures,validation=validation,module_mutation_after_preseal=False,formal_release=False))
for b in pre['five_modules']+[pre['algorithm_bindings']]:verify(b)
members=[bind(x) for x in sorted(P.rglob('*')) if x.is_file() and '__pycache__' not in x.parts and x.name!='delivery-seal.json']
seal=dump('delivery-seal.json',dict(identity='nonhuman v5 developer candidate full delivery seal',at_utc=AT,output_members=members,self_in_output_members=False,cache_files_excluded=True,final_algorithm=bind(P/'algorithm-bindings.json'),final_preseal=bind(P/'pre-execution-seal.json'),independent_results_will_not_mutate_this_version=True))
for b in members:verify(b)
verify(seal)
print(json.dumps(dict(delivery_seal=seal,output_member_N=len(members),readback_valid=True,algorithm=bind(P/'algorithm-bindings.json'),preseal=bind(P/'pre-execution-seal.json'),source_ids_outside_authorized_S3=[],actual_S3_classification_by_owner=0),ensure_ascii=False,indent=2))

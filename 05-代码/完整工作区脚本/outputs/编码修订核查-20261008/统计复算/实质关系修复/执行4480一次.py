from pathlib import Path
import argparse,ast,collections,copy,datetime,hashlib,json,sys,time,traceback
B=Path(__file__).resolve().parent;W=B.parents[1]
RT=W/'自动规则编码/实质评价与支持关系修复/runtime03'
FIXED=W/'自动规则编码/实质评价与支持关系修复/运行前固定记录03.json'
INPUT=W/'统计复算/来源读取与图示校正/规则输入4480.jsonl'
BASE=W/'统计复算/来源读取与图示校正/当前同材料结果/规则全量输出4480.jsonl'
MANUAL=W/'定义溯源核查/测量与计数统一/共用编码手册.md'
DIMENSIONS=('S','E','Ec','I','F')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def manifest(root):return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
def treehash(m):return hashlib.sha256(json.dumps(m,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def writejson(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def existing_input_paths(obj,found,absent):
 if isinstance(obj,dict):
  for value in obj.values():existing_input_paths(value,found,absent)
 elif isinstance(obj,list):
  for value in obj:existing_input_paths(value,found,absent)
 elif isinstance(obj,str) and obj.startswith('/') and '\n' not in obj and len(obj)<2000:
  p=Path(obj)
  if p.is_file():found.add(str(p))
  elif p.suffix in ('.pdf','.txt','.json','.doc','.docx'):absent.add(obj)
def literal_errors(row,out):
 text=row['input']['unit_text'];result=out.get('result',{});errors=[];checked=0;anchor_n=0
 if out['status']!='completed':return [{'kind':'execution_failed','error':out.get('error')}],0,0
 if result.get('unit_text_sha256')!=hashlib.sha256(text.encode()).hexdigest():errors.append({'kind':'current_unit_sha_mismatch'})
 labels=result.get('labels',{})
 if set(labels)!=set(DIMENSIONS):errors.append({'kind':'label_keys'})
 if any(not ((type(v) is int and v in (0,1)) or (v is None and result.get('judgement_status')=='undetermined')) for v in labels.values()):errors.append({'kind':'invalid_label_value'})
 for i,e in enumerate(result.get('evidence',[])):
  checked+=1
  start,end=e.get('start'),e.get('end')
  if not (type(start) is int and type(end) is int and 0<=start<=end<=len(text) and text[start:end]==e.get('text')):errors.append({'kind':'evidence_locator_mismatch','evidence_index':i,'rule':e.get('rule')})
  for field in ('current_statement','evidence_expression'):
   q=e.get(field)
   if q is not None and not (q.get('start')==0 and q.get('end')==len(text) and q.get('text')==text):errors.append({'kind':'full_current_quote_mismatch','field':field,'evidence_index':i})
  if 'display_quote' in e and e['display_quote']!=text:errors.append({'kind':'display_quote_mismatch','evidence_index':i})
  for anchor in e.get('current_relation_anchors',[]):
   anchor_n+=1;s,t=anchor.get('start'),anchor.get('end')
   if not (type(s) is int and type(t) is int and 0<=s<=t<=len(text) and text[s:t]==anchor.get('text')):errors.append({'kind':'current_anchor_mismatch','evidence_index':i,'anchor_role':anchor.get('role')})
 return errors,checked,anchor_n
parser=argparse.ArgumentParser();parser.add_argument('--authorization',required=True);args=parser.parse_args()
assert args.authorization.strip(),'root independent review authorization required'
paths=[B/name for name in ('规则全量输出4480.jsonl','规则全量输出4480.execution.json','运行前冻结.json','全量前后标签差异.jsonl','全量前后标签差异.md','执行与字面核查.json')]
assert not any(p.exists() for p in paths),'one actual full run only; preserve existing artifacts'
assert sha(INPUT)=='16b65b1ea5ed895173efb7b6c4bc91e74ddddbfa39d4b4c1b4018a2fe4df033c'
assert sha(BASE)=='9728ed804f4178d953072dbe24ea5f1517971dd1f3dd7440f458d7d52f2a4ac2'
assert sha(MANUAL)=='24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9'
fixed=json.loads(FIXED.read_text());before=manifest(RT)
assert before==fixed['runtime_all_files_sha256'] and treehash(before)=='d7d8b8fe77a5a420ec089d52ae28974d50963a0ef2acd47dc009f25591f1bb1d'
for p in RT.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
rows=[json.loads(l) for l in INPUT.open()];base_rows=[json.loads(l) for l in BASE.open()]
assert len(rows)==4480 and len({r['id'] for r in rows})==4480
assert [r['id'] for r in rows]==[r['id'] for r in base_rows]
pre=json.loads((B/'真实5入口预检02报告.json').read_text());assert pre['all_target_relations_and_other_dimensions_pass'] and pre['runtime_unchanged']
found={str(p) for p in (INPUT,BASE,MANUAL,FIXED,Path(__file__),B/'真实5入口预检02报告.json')};absent=set()
for row in rows:existing_input_paths(row['input'],found,absent)
protected={p:sha(p) for p in sorted(found)}
base_rt=Path(fixed['runtime02_all_files_sha256'] and W/'自动规则编码/实质评价与支持关系修复/runtime02');base_before=manifest(base_rt)
freeze={'kind':'one_actual_deterministic4480_run_no_model_no_validity_claim','authorization_from_root':args.authorization,'fixed_runtime_record_sha256':sha(FIXED),'entry_VERSION':fixed['entry_VERSION'],'n':4480,'input_path':str(INPUT),'input_sha256':sha(INPUT),'base_output_path':str(BASE),'base_output_sha256':sha(BASE),'manual_sha256':sha(MANUAL),'runtime_before':before,'runtime_before_tree_sha256':treehash(before),'runtime02_protected_before':base_before,'protected_input_source_files_before':protected,'metadata_local_file_paths_absent':sorted(absent),'runner_sha256':sha(Path(__file__)),'prepared_utc':utc()}
writejson(B/'运行前冻结.json',freeze)
sys.path.insert(0,str(RT));import pypdf;import policy_coding_v27
assert policy_coding_v27.VERSION==fixed['entry_VERSION']
start=time.monotonic();started=utc();results=[]
with (B/'规则全量输出4480.jsonl').open('w') as h:
 for n,row in enumerate(rows,1):
  try:out={'id':row['id'],'status':'completed','result':policy_coding_v27.code_unit(copy.deepcopy(row['input']))}
  except Exception as e:out={'id':row['id'],'status':'failed','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()}
  h.write(json.dumps(out,ensure_ascii=False)+'\n');h.flush();results.append(out)
  if n%250==0 or n==len(rows) or out['status']=='failed':print(json.dumps({'processed':n,'total':4480,'elapsed_seconds':round(time.monotonic()-start,1),'last_id':row['id'],'status':out['status']},ensure_ascii=False),flush=True)
finished=utc();elapsed=round(time.monotonic()-start,3);after=manifest(RT);protected_after={p:sha(p) for p in protected};base_after=manifest(base_rt)
execution={'kind':'one_actual_deterministic4480_execution_not_validity','started_utc':started,'finished_utc':finished,'elapsed_seconds':elapsed,'n':4480,'status_counts':dict(collections.Counter(x['status'] for x in results)),'n_undetermined':sum(x.get('result',{}).get('judgement_status')=='undetermined' for x in results),'output_path':str(B/'规则全量输出4480.jsonl'),'output_sha256':sha(B/'规则全量输出4480.jsonl'),'input_sha256':sha(INPUT),'manual_sha256':sha(MANUAL),'entry_VERSION':policy_coding_v27.VERSION,'runtime_before':before,'runtime_after':after,'runtime_before_tree_sha256':treehash(before),'runtime_after_tree_sha256':treehash(after),'runtime_unchanged':after==before,'runtime02_unchanged':base_after==base_before,'protected_sources_input_base_manual_runner_unchanged':protected_after==protected,'protected_files_after':protected_after,'pypdf_version':pypdf.__version__,'python_executable':sys.executable,'full_input_n':4480,'no_model_run':True,'no_human_labels_or_metrics_used':True}
writejson(B/'规则全量输出4480.execution.json',execution)
changes=[];qa_errors=[];evidence_n=anchor_n=0;pending=[]
for row,old,out in zip(rows,base_rows,results):
 errors,ne,na=literal_errors(row,out);evidence_n+=ne;anchor_n+=na
 if errors:qa_errors.append({'id':row['id'],'errors':errors})
 cur=out.get('result',{});prior=old.get('result',{});changed=[d for d in DIMENSIONS if prior.get('labels',{}).get(d)!=cur.get('labels',{}).get(d)]
 if cur.get('judgement_status')=='undetermined':pending.append({'id':row['id'],'labels':cur.get('labels'),'common11_pending_dimensions':cur.get('common11_pending_dimensions'),'common14_pending_dimensions':cur.get('common14_pending_dimensions'),'assessment':cur.get('input_assessment_status'),'completeness_gate_v34':cur.get('completeness_gate_v34')})
 if changed or out['status']!=old['status'] or cur.get('judgement_status')!=prior.get('judgement_status'):
  changes.append({'id':row['id'],'original_id':row.get('original_id'),'unit_source':row['input'].get('unit_source'),'candidate_file':row['input'].get('candidate_file'),'unit_text':row['input']['unit_text'],'before_labels':prior.get('labels'),'after_labels':cur.get('labels'),'changed_dimensions':changed,'before_status':old['status'],'after_status':out['status'],'before_judgement_status':prior.get('judgement_status'),'after_judgement_status':cur.get('judgement_status'),'before_changed_dimension_evidence':[e for e in prior.get('evidence',[]) if e.get('dimension') in changed],'after_changed_dimension_evidence':[e for e in cur.get('evidence',[]) if e.get('dimension') in changed],'error':out.get('error')})
with (B/'全量前后标签差异.jsonl').open('w') as h:
 for change in changes:h.write(json.dumps(change,ensure_ascii=False)+'\n')
qa={'kind':'structural_literal_source_binding_and_before_after_description_not_semantic_validity','n':4480,'output_sha256':execution['output_sha256'],'input_sha256':sha(INPUT),'manual_sha256':sha(MANUAL),'baseline_output_sha256':sha(BASE),'runtime_before_tree_sha256':treehash(before),'runtime_after_tree_sha256':treehash(after),'ids_unique_and_order_match':len({r['id'] for r in results})==4480 and [r['id'] for r in results]==[r['id'] for r in rows],'status_counts':execution['status_counts'],'n_undetermined':len(pending),'undetermined_rows':pending,'literal_error_rows':qa_errors,'n_literal_error_rows':len(qa_errors),'n_current_evidence_locators_checked':evidence_n,'n_current_relation_anchors_checked':anchor_n,'changed_row_n':len(changes),'changed_dimension_counts':dict(collections.Counter(d for c in changes for d in c['changed_dimensions'])),'changed_ids':[c['id'] for c in changes],'unchanged_five_label_rows':4480-sum(bool(c['changed_dimensions']) for c in changes),'unexpected_SE_Ec_change_ids':[c['id'] for c in changes if set(c['changed_dimensions']) & {'S','E','Ec'}],'runtime_unchanged':execution['runtime_unchanged'],'runtime02_unchanged':execution['runtime02_unchanged'],'protected_sources_input_base_manual_runner_unchanged':execution['protected_sources_input_base_manual_runner_unchanged'],'coverage_limitation':'evidence substrings and full current quotes checked against actual fixed input; not a fresh independent semantic coding/construct validation or new government source review','independent_control10_first_failure_preserved':True,'full_run_count_this_patch':1,'no_LLM_run':True,'no_ground_truth_comparison':True}
writejson(B/'执行与字面核查.json',qa)
md=['一次实际确定性规则执行 4480 条；不使用模型、旧人工参照或一致性指标。固定手册与输入未改。本轮结构与证据字面核查不属于语义效度验证。','',f"完成状态：{execution['status_counts']}；待核 {len(pending)}；字面核查异常行 {len(qa_errors)}。实际耗时 {elapsed} 秒。",f"前后标签变化 {len(changes)} 行；维度计数 {qa['changed_dimension_counts']}；S/E/Ec 意外变化行 {qa['unexpected_SE_Ec_change_ids']}。",f"runtime 前后字节一致：{after==before}；固定源、输入、基线、手册与执行脚本一致：{protected_after==protected}。",'', '| ID | 原标签 S/E/Ec/I/F | 新标签 S/E/Ec/I/F | 变化维度 |','|---|---|---|---|']
for c in changes:
 a='/'.join(str((c['before_labels'] or {}).get(d)) for d in DIMENSIONS);b='/'.join(str((c['after_labels'] or {}).get(d)) for d in DIMENSIONS)
 md.append(f"| {c['id']} | {a} | {b} | {','.join(c['changed_dimensions'])} |")
md+=['','全部实际输出、失败、待核和原始首次独立控制失败均保留。每条变化的真实原句、来源、前后依据见同目录全量前后标签差异.jsonl。未解决的语义边界和独立控制08/09未在本轮扩展处理。']
(B/'全量前后标签差异.md').write_text('\n'.join(md)+'\n')
print(json.dumps({k:qa[k] for k in ('n','status_counts','n_undetermined','n_literal_error_rows','changed_row_n','changed_dimension_counts','changed_ids','unexpected_SE_Ec_change_ids','runtime_unchanged','protected_sources_input_base_manual_runner_unchanged','output_sha256')},ensure_ascii=False),flush=True)

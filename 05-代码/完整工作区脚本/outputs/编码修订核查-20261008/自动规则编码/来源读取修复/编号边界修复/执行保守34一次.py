from pathlib import Path
import ast,collections,hashlib,json,sys,time,traceback
B=Path(__file__).resolve().parent;W=B.parents[2];RT=B/'runtime'
DATA=W/'统计复算/来源读取与图示校正'
INPUT=DATA/'规则输入4480.jsonl';BASE_OUTPUT=DATA/'规则全量输出4480.jsonl'
BASE_RT=W/'自动规则编码/来源读取修复/图示校正运行目录'
MANUAL=W/'定义溯源核查/测量与计数统一/共用编码手册.md'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def manifest(root):return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
def treehash(m):return hashlib.sha256(json.dumps(m,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
scope=json.loads((B/'静态影响范围.json').read_text());ids=scope['conservative_current_paragraph_ids']
assert len(ids)==34 and len(set(ids))==34
assert all(x['not_in_inline_branch'] and not x['direct_marker_syntax_differs'] for x in scope['structured_mapping_exceptions_reviewed'])
assert sha(INPUT)==scope['input_sha256']
input_lines=INPUT.read_text().splitlines(keepends=True);rowsall=[json.loads(l) for l in input_lines];idset=set(ids)
selected_lines=[l for l,r in zip(input_lines,rowsall) if r['id'] in idset];rows=[json.loads(l) for l in selected_lines]
assert [r['id'] for r in rows]==ids and len(rows)==34
subset=B/'保守34输入.jsonl';outpath=B/'保守34实际输出.jsonl'
assert not subset.exists() and not outpath.exists(),'one actual subset run only; do not overwrite'
subset.write_text(''.join(selected_lines))
allbase_lines=BASE_OUTPUT.read_text().splitlines(keepends=True);base_rows=[json.loads(l) for l in allbase_lines];base={r['id']:r for r in base_rows}
(B/'保守34原全量输出留存.jsonl').write_text(''.join(l for l,r in zip(allbase_lines,base_rows) if r['id'] in idset))
before=manifest(RT);base_manifest=manifest(BASE_RT)
assert set(before)==set(base_manifest)
assert [k for k in before if before[k]!=base_manifest[k]]==['common_innovation_relations14.py']
for p in RT.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
protected={str(p):sha(p) for p in (INPUT,BASE_OUTPUT,MANUAL)}
for row in rows:
 for key in ('unit_source','candidate_file'):
  path=Path(row['input'][key]);protected[str(path)]=sha(path)
assert sha(MANUAL)=='24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9'
freeze={'kind':'bounded_numbered_boundary_repair_not_validity','subset_n':34,'input_path':str(subset),'input_sha256':sha(subset),'full_input_path':str(INPUT),'full_input_sha256':sha(INPUT),'base_full_output_path':str(BASE_OUTPUT),'base_full_output_sha256':sha(BASE_OUTPUT),'manual_sha256':sha(MANUAL),'scope_sha256':sha(B/'静态影响范围.json'),'runtime_manifest':before,'runtime_tree_sha256':treehash(before),'baseline_runtime_manifest':base_manifest,'baseline_runtime_tree_sha256':treehash(base_manifest),'protected_files_before':protected,'ids':ids,'expected_labels_not_used':True}
(B/'实际34执行冻结.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
sys.path.insert(0,str(RT))
from pypdf import PdfReader
import policy_coding_v27
start=time.monotonic();results=[]
with outpath.open('w') as h:
 for row in rows:
  try:out={'id':row['id'],'status':'completed','result':policy_coding_v27.code_unit(row['input'])}
  except Exception as e:out={'id':row['id'],'status':'failed','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()}
  h.write(json.dumps(out,ensure_ascii=False)+'\n');h.flush();results.append(out)
  print(row['id'],out['status'],flush=True)
changes=[]
for out in results:
 prior=base[out['id']].get('result',{});cur=out.get('result',{})
 changed=[d for d in ('S','E','Ec','I','F') if prior.get('labels',{}).get(d)!=cur.get('labels',{}).get(d)]
 changes.append({'id':out['id'],'before_labels':prior.get('labels'),'after_labels':cur.get('labels'),'changed_dimensions':changed,'before_judgement_status':prior.get('judgement_status'),'after_judgement_status':cur.get('judgement_status'),'pending':cur.get('common14_pending_dimensions',{}),'status':out['status'],'failure':out.get('error')})
report={'kind':'one_actual_full_entry_subset_run_not_independent_validation','n':34,'status_counts':dict(collections.Counter(x['status'] for x in results)),'n_undetermined':sum(x.get('result',{}).get('judgement_status')=='undetermined' for x in results),'elapsed_seconds':round(time.monotonic()-start,3),'input_sha256':sha(subset),'full_input_sha256':sha(INPUT),'base_full_output_sha256':sha(BASE_OUTPUT),'output_sha256':sha(outpath),'manual_sha256':sha(MANUAL),'runtime_tree_sha256':treehash(before),'runtime_manifest':before,'runtime_unchanged_during_run':manifest(RT)==before,'baseline_runtime_unchanged':manifest(BASE_RT)==base_manifest,'protected_source_input_output_manual_unchanged':all(sha(p)==s for p,s in protected.items()),'changes':changes,'changed_rows':[x for x in changes if x['changed_dimensions'] or x['before_judgement_status']!=x['after_judgement_status']],'rows_with_identical_five_labels':sum(not x['changed_dimensions'] for x in changes),'no_human_or_model_labels_used':True,'no_performance_or_validity_claim':True}
(B/'实际34执行报告.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('n','status_counts','n_undetermined','elapsed_seconds','output_sha256','runtime_tree_sha256','runtime_unchanged_during_run','baseline_runtime_unchanged','protected_source_input_output_manual_unchanged','changed_rows','rows_with_identical_five_labels')},ensure_ascii=False,indent=2))

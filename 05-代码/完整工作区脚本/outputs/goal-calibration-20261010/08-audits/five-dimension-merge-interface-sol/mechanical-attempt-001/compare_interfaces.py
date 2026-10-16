"""Read-only AST merge preflight. Never imports or runs candidate predicates."""
import ast,json,hashlib,datetime,difflib,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1];CODING=BASE/'06-coding';NAMES=('relations','dimensions','evidence','source_packet','source_receipts')
ROOTS={'baseline':CODING/'full4481-rule-production-adapter-sol','IF_v2':CODING/'rule-v20-semantic-audit-repair-sol/versions/v2','SE_v1':CODING/'rule-v20-SEEconomic-repair-sol','SE_v2_observed':CODING/'rule-v20-SEEconomic-repair-sol/versions/v2'}
def h(raw):return hashlib.sha256(raw).hexdigest()
def bind(p):
 raw=p.read_bytes();return{'path':str(p.resolve()),'bytes':len(raw),'sha256':h(raw)}
def save(p,v):
 with p.open('x',encoding='utf8')as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def calls(node):
 out=set()
 for n in ast.walk(node):
  if isinstance(n,ast.Call):
   if isinstance(n.func,ast.Name):out.add(n.func.id)
   elif isinstance(n.func,ast.Attribute):
    try:out.add(ast.unparse(n.func))
    except Exception:pass
 return sorted(out)
def inventory(raw):
 text=raw.decode('utf8');tree=ast.parse(text);functions={};constants={};definitions=[]
 def walk(nodes,prefix=''):
  counts=collections.Counter(n.name for n in nodes if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)))
  seen=collections.Counter()
  for n in nodes:
   if isinstance(n,ast.ClassDef):walk(n.body,prefix+n.name+'.')
   elif isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    key=prefix+n.name;seen[n.name]+=1
    rec={'name':key,'definition_index':seen[n.name],'definitions_in_owner':counts[n.name],
         'effective_last_definition':seen[n.name]==counts[n.name],'first_line':n.lineno,'last_line':n.end_lineno,
         'signature':ast.unparse(n.args),'source':ast.get_source_segment(text,n),
         'ast_sha256':h(ast.dump(n,include_attributes=False).encode()),'direct_and_nested_calls':calls(n),
         'constants_read':sorted({a.id for a in ast.walk(n)if isinstance(a,ast.Name)and a.id.isupper()})}
    definitions.append(rec);functions[key]=rec
    # Nested helper identities remain distinguishable from module/class defs.
    nested=[c for c in n.body if isinstance(c,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
    walk(nested,key+'.<locals>.')
   elif not prefix and isinstance(n,(ast.Assign,ast.AnnAssign)):
    targets=n.targets if isinstance(n,ast.Assign)else[n.target]
    value=n.value
    for target in targets:
     if isinstance(target,ast.Name)and target.id.isupper():
      constants[target.id]={'name':target.id,'first_line':n.lineno,'last_line':n.end_lineno,'source':ast.get_source_segment(text,n),'ast_sha256':h(ast.dump(value,include_attributes=False).encode())}
 return {'effective_functions':functions,'all_function_definitions':definitions,'constants':constants}
started=datetime.datetime.now(datetime.timezone.utc).isoformat();manifest={'status':'read-only merge preflight; no merged release or semantic execution','started_at_utc':started,'SE_v2_owner_status':'unsealed static observation only','manual_binding':bind(BASE/'03-manual/full4481-common-release-20261010-root/manual.txt'),'branches':{}}
inv={};(HERE/'source-code-observation-snapshots').mkdir()
for branch,root in ROOTS.items():
 sub=HERE/'source-code-observation-snapshots'/branch;sub.mkdir();inv[branch]={};entries=[]
 for name in NAMES:
  p=root/(name+'.py');before=bind(p);raw=p.read_bytes();(sub/p.name).write_bytes(raw);after=bind(p)
  entries.append({'input_binding_at_read':before,'snapshot_binding':bind(sub/p.name),'owner_file_same_before_and_after_read':before==after,'published_release_binding':branch!='SE_v2_observed'})
  inv[branch][name]=inventory(raw)
 manifest['branches'][branch]={'module_read_bindings':entries,'code_not_executed':True}
# Seal verification reads metadata/code only, never prediction/expected-label files.
IFseal=CODING/'rule-v20-semantic-audit-repair-sol/delivery/delivery-seal.json';SEseal=CODING/'rule-v20-SEEconomic-repair-sol/candidate-seal.json'
manifest['existing_owner_seals']=[bind(IFseal),bind(SEseal)]
manifest['not_read_as_task_inputs']=['formal full LLM outputs','candidate800/77 prediction files','expected label files after accidental metadata preview']
manifest['access_exception_disclosure']={'file':str((ROOTS['SE_v2_observed']/'before-v2-repair.json').resolve()),'what_happened':'mistaken version-metadata preview exposed fixed-control expected fields, including source800 fixtures','used_in_AST_comparison_or_merge_recommendations':False,'no_additional_test_or_label_file_read':True,'ROOT_notified':True}
save(HERE/'input-code-observation-bindings.json',manifest)
rows=[]
for module in NAMES:
 funcs=set().union(*(set(inv[b][module]['effective_functions'])for b in ROOTS))
 for name in sorted(funcs):
  records={b:inv[b][module]['effective_functions'].get(name)for b in ROOTS};base=records['baseline'];base_sha=base['ast_sha256']if base else None
  statuses={b:'absent'if not rec else 'new'if not base else 'same_as_baseline'if rec['ast_sha256']==base_sha else 'modified'for b,rec in records.items()if b!='baseline'}
  IF=records['IF_v2'];SE1=records['SE_v1'];SE2=records['SE_v2_observed']
  overlap={b:statuses['IF_v2'] in ('modified','new')and statuses[b] in ('modified','new')for b in ('SE_v1','SE_v2_observed')}
  row={'module':module,'function':name,'statuses':statuses,'both_branches_changed':overlap,
       'same_IF_and_SE_v2_AST':bool(IF and SE2 and IF['ast_sha256']==SE2['ast_sha256']),
       'records':{b:{k:v for k,v in rec.items()if k!='source'}if rec else None for b,rec in records.items()}}
  rows.append(row)
  if any(s in ('modified','new')for s in statuses.values()):
   diffs={}
   for b,rec in records.items():
    if b=='baseline' or rec is None:continue
    old=base['source']if base else '';delta=''.join(difflib.unified_diff(old.splitlines(True),rec['source'].splitlines(True),fromfile='baseline/'+name,tofile=b+'/'+name))
    if delta:diffs[b]=delta
   row['exact_function_diffs_vs_baseline']=diffs
save(HERE/'function-level-differences.json',rows)
constant_rows=[]
for module in NAMES:
 for name in sorted(set().union(*(set(inv[b][module]['constants'])for b in ROOTS))):
  records={b:inv[b][module]['constants'].get(name)for b in ROOTS};baseline=records['baseline'];base_sha=baseline['ast_sha256']if baseline else None
  statuses={b:'absent'if not rec else 'new'if not baseline else 'same_as_baseline'if rec['ast_sha256']==base_sha else 'modified'for b,rec in records.items()if b!='baseline'}
  constant_rows.append({'module':module,'constant':name,'statuses':statuses,'records':records})
save(HERE/'constant-level-differences.json',constant_rows)
save(HERE/'all-definition-and-call-inventory.json',inv)
summary={'function_total_N':len(rows),'constants_N':len(constant_rows),'function_rows_changed_either_branch_N':sum(any(s in('modified','new')for s in r['statuses'].values())for r in rows),'overlapping_IF_SEv1_functions':[r['module']+'.'+r['function']for r in rows if r['both_branches_changed']['SE_v1']],'overlapping_IF_SEv2_observed_functions':[r['module']+'.'+r['function']for r in rows if r['both_branches_changed']['SE_v2_observed']], 'module_byte_identity':{m:{b:manifest['branches'][b]['module_read_bindings'][NAMES.index(m)]['snapshot_binding']['sha256']==manifest['branches']['baseline']['module_read_bindings'][NAMES.index(m)]['snapshot_binding']['sha256']for b in ROOTS if b!='baseline'}for m in NAMES},'no_semantic_execution':True,'SE_v2_static_only':True}
save(HERE/'mechanical-summary.json',summary)
# Plain table is part of technical report, not an edited spreadsheet workbook.
lines=['函数级差异表（AST有效定义；SE v2未封存，读取时静态观察）','模块 | 函数 | I/F v2 vs基线 | SE v1 vs基线 | SE v2静态 vs基线 | 双方重叠','']
for r in rows:
 if any(s in('modified','new')for s in r['statuses'].values()):
  st=r['statuses'];lines.append(f"{r['module']} | {r['function']} | {st['IF_v2']} | {st['SE_v1']} | {st['SE_v2_observed']} | {r['both_branches_changed']['SE_v2_observed']}")
(HERE/'函数级差异表.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))

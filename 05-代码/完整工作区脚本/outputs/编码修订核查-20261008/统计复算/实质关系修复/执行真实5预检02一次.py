from pathlib import Path
import ast,collections,copy,datetime,hashlib,json,sys,time,traceback
B=Path(__file__).resolve().parent;W=B.parents[1]
RT=W/'自动规则编码/实质评价与支持关系修复/runtime02'
INPUT=W/'统计复算/来源读取与图示校正/规则输入4480.jsonl'
BASE=W/'统计复算/来源读取与图示校正/当前同材料结果/规则全量输出4480.jsonl'
MANUAL=W/'定义溯源核查/测量与计数统一/共用编码手册.md'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def manifest(root):return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
def treehash(m):return hashlib.sha256(json.dumps(m,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
ids={'RECODE25-'+x for x in ('03710','02206','01090','02556','03206')}
lines=INPUT.read_text().splitlines(keepends=True);selected=[l for l in lines if json.loads(l)['id'] in ids];rows=[json.loads(l) for l in selected]
assert len(rows)==5 and len({r['id'] for r in rows})==5
assert sha(INPUT)=='16b65b1ea5ed895173efb7b6c4bc91e74ddddbfa39d4b4c1b4018a2fe4df033c'
assert sha(BASE)=='9728ed804f4178d953072dbe24ea5f1517971dd1f3dd7440f458d7d52f2a4ac2'
assert sha(MANUAL)=='24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9'
before=manifest(RT);assert treehash(before)=='71caac7c5fec02ee2c92bb00182593567ecd7a95a307faec698d9e85274c8a21'
for p in RT.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
output=B/'真实5入口预检02输出.jsonl';subset=B/'真实5入口预检02输入.jsonl';freeze=B/'真实5入口预检02冻结.json';reportp=B/'真实5入口预检02报告.json'
assert not any(p.exists() for p in (output,subset,freeze,reportp)), 'one actual precheck only'
subset.write_text(''.join(selected))
base={r['id']:r for r in map(json.loads,BASE.open()) if r['id'] in ids}
protected={str(p):sha(p) for p in (INPUT,BASE,MANUAL,Path(__file__))}
for r in rows:
 for key in ('unit_source','candidate_file'):
  p=Path(r['input'][key]);protected[str(p)]=sha(p)
freeze.write_text(json.dumps({'kind':'purpose_selected_5_development_entry_precheck_not_validation','authorized_by_parent':True,'runtime_before':before,'runtime_tree_sha256':treehash(before),'protected_before':protected,'full_input_sha256':sha(INPUT),'subset_sha256':sha(subset),'manual_sha256':sha(MANUAL),'base_sha256':sha(BASE)},ensure_ascii=False,indent=2)+'\n')
sys.path.insert(0,str(RT));import pypdf;import policy_coding_v27
started=datetime.datetime.now(datetime.timezone.utc).isoformat();start=time.monotonic();results=[]
with output.open('w') as h:
 for r in rows:
  try:o={'id':r['id'],'status':'completed','result':policy_coding_v27.code_unit(copy.deepcopy(r['input']))}
  except Exception as e:o={'id':r['id'],'status':'failed','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()}
  h.write(json.dumps(o,ensure_ascii=False)+'\n');h.flush();results.append(o)
expected_targets={'RECODE25-03710':{'I':1},'RECODE25-02206':{'I':1},'RECODE25-01090':{'F':0},'RECODE25-02556':{'F':1},'RECODE25-03206':{'F':1}}
checks=[]
for o,r in zip(results,rows):
 old=base[o['id']]['result'];new=o.get('result',{});target=expected_targets[o['id']]
 changes=[d for d in ('S','E','Ec','I','F') if old['labels'].get(d)!=new.get('labels',{}).get(d)]
 checks.append({'id':o['id'],'unit_text':r['input']['unit_text'],'unit_source':r['input']['unit_source'],'before_labels':old['labels'],'after_labels':new.get('labels'),'changed_dimensions':changes,'target_relation_check':all(new.get('labels',{}).get(d)==v for d,v in target.items()),'other_dimensions_unchanged':all(old['labels'][d]==new.get('labels',{}).get(d) for d in old['labels'] if d not in target),'judgement_status':new.get('judgement_status'),'evidence':new.get('evidence',[]),'error':o.get('error')})
after=manifest(RT);rep={'kind':'purpose_selected_5_development_precheck_not_independent_validity','n':5,'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':round(time.monotonic()-start,3),'status_counts':dict(collections.Counter(o['status'] for o in results)),'runtime_before':before,'runtime_after':after,'runtime_before_tree_sha256':treehash(before),'runtime_after_tree_sha256':treehash(after),'runtime_unchanged':before==after,'protected_unchanged':all(sha(p)==v for p,v in protected.items()),'output_sha256':sha(output),'full_input_sha256':sha(INPUT),'subset_sha256':sha(subset),'manual_sha256':sha(MANUAL),'checks':checks,'all_target_relations_and_other_dimensions_pass':all(c['target_relation_check'] and c['other_dimensions_unchanged'] and c['judgement_status']!='undetermined' for c in checks),'independent_control10_not_rerun_or_changed':True,'full4480_not_run':True}
reportp.write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:rep[k] for k in ('n','elapsed_seconds','status_counts','all_target_relations_and_other_dimensions_pass','runtime_unchanged','protected_unchanged','output_sha256')},ensure_ascii=False))
for c in checks:print(c['id'],c['before_labels'],c['after_labels'],c['changed_dimensions'])

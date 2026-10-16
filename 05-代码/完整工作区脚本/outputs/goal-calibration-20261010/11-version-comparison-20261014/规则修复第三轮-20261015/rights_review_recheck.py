"""Recheck only previously reported rights-boundary findings. Never edits inputs."""
import json,copy,sys,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path.insert(0,str(P/'code'))
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
sha=lambda:{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (P/'code').glob('*.py')}
before=sha();units={}
for line in (R/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl').open():
 x=json.loads(line)
 if x['id'] in ['RECODE25-01408','RECODE25-01412','RECODE25-01416']:units[x['id']]=x['semantic_unit']
def renamed(base,text):
 u=copy.deepcopy(base);old=u['text'];u['text']=text
 for c in u['contexts']:
  if c.get('kind')=='paragraph' and old in c.get('text',''):c['text']=c['text'].replace(old,text)
 u['source_bundle']['source_record']['text']=text
 for c in u['source_bundle']['source_record'].get('contexts',[]):
  if c.get('kind')=='paragraph' and old in c.get('text',''):c['text']=c['text'].replace(old,text)
 return u
cases=[(k,copy.deepcopy(v),[1]) for k,v in units.items()]
u=copy.deepcopy(units['RECODE25-01408']);u.setdefault('structure',{})['component_id']='A'
for c in u['contexts']:c.setdefault('structure',{})['component_id']='B' if c['kind']=='source_resource_text' else 'A'
for doc in u['source_bundle']['explicit_or_primary_source_resources']:
 doc.setdefault('structure',{})['component_id']='B'
 for t in doc['source_texts']:t.setdefault('structure',{})['component_id']='B'
cases.append(('cross_component_B_definitions',u,[0,None]))
for name,text in [
('application_form_quote','第九条 申报系统新增“申请人拟申请数据保护的，应当在提交药品上市许可申请时同时提出数据保护申请”栏目。'),
('application_timing_consultation','第九条 对“申请人拟申请数据保护的，应当在提交药品上市许可申请时同时提出数据保护申请”这一表述，企业可以咨询其标点格式。'),
('list_only','第九条 公布获得药品试验数据保护的品种名单，更新数据保护期届满日期。'),
('ordinary_consultation','第九条 对药品试验数据保护名单存在疑问的，可以申请沟通交流。'),
('application_material','第九条 申请人拟申请数据保护的，应当在提交药品上市许可申请时同时提出数据保护申请材料。'),
]:cases.append((name,renamed(units['RECODE25-01408'],text),[0]))
u=copy.deepcopy(units['RECODE25-01408'])
def edit_text(o):
 if isinstance(o,dict):
  if isinstance(o.get('text'),str):
   o['text']=o['text'].replace('创新药','非创新药')
   if 'text_sha256' in o:o['text_sha256']=hashlib.sha256(o['text'].encode()).hexdigest()
  for k,v in o.items():
   if k!='text':edit_text(v)
 elif isinstance(o,list):
  for x in o:edit_text(x)
edit_text(u);cases.append(('non_innovation_entitlement',u,[0]))
results=[]
for n,u,exp in cases:
 try:
  v=RelationView(u);d=judge(v);validate_decisions(v.unit,d)
  rel=[r for r in v.relations if r['details'].get('relation_subtype')=='bounded_data_protection_rights_consequence']
  out={'name':n,'allowed_I':exp,'actual_I':d['I']['value'],'rights_relation_N':len(rel),'basis':d['I']['basis_path'],'passed':d['I']['value'] in exp and (exp==[1] or len(rel)==0),'text':u['text']}
 except Exception as e:out={'name':n,'error':repr(e),'passed':False}
 results.append(out)
assert before==sha(),'source changed during check; run again after freeze'
report={'scope':'Existing review findings only; original rights positives plus reported source/semantic counterexamples. Not independent validation.','code_sha':before,'total':len(results),'passed':sum(x['passed'] for x in results),'cases':results}
(P/'round3-rights-review-recheck.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'total':report['total'],'failed':[x for x in results if not x['passed']]},ensure_ascii=False))

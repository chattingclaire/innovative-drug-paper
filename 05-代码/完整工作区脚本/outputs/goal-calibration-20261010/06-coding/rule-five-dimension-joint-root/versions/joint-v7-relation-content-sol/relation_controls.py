"""Fixed, disclosed relation development controls. Expected values stay outside the coder."""
from pathlib import Path
from datetime import datetime, timezone
import copy, json, hashlib, sys, importlib.util, traceback
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
G=P.parents[3]
NAMES=('evidence','source_packet','source_receipts','relations','dimensions')
def bind(p):
 p=Path(p).resolve();raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(p,x):
 with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def modules(code):
 out={}
 for n in NAMES:
  s=importlib.util.spec_from_file_location(n,code/(n+'.py'));m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);out[n]=m
 return out
def prepare():
 m=modules(P/'before-code-snapshot');cases=[];packets=G/'06-coding/full4481-common-v15-production-preparation-sol/packets'
 sources={}
 for sid,expected in [('00005',{'S':1}),('00099',{'I':0,'F':1}),('00900',{'Ec':1}),('01459',{'E':1}),('01955',{'Ec':1}),('01423',{'S':1,'E':1,'Ec':0,'I':1,'F':0}),('00110',{'F':None}),('00118',{'F':None})]:
  path=packets/('RECODE25-'+sid+'.json');raw=json.loads(path.read_bytes());u=m['source_packet'].semantic_unit(raw['source_bundle']);sources[sid]=u
  cases.append({'name':'original source relation '+sid,'semantic_input':u,'expected':expected,'packet_binding':bind(path),'synthetic':False})
 def literal(name,text,d,expected,contexts=None):
  u={'text':text,'contexts':contexts or [],'source_ref':{'sha256':'a'*64,'source_resource_id':'SOURCE-'+'a'*64,'locator':{}}}
  cases.append({'name':name,'semantic_input':u,'expected':{d:expected},'synthetic':True})
 literal('explicit innovation service restriction remains I','对创新药研发，药审中心不再提供研究方案反馈。','I',1)
 literal('generic drug service not innovation','对仿制药申请，药审中心不再接受新的申报。','I',0)
 literal('bare route identity remains excluded','药品企业主动申请调整医保支付范围。','Ec',0)
 ref={'sha256':'a'*64,'source_resource_id':'SOURCE-'+'a'*64,'locator':{'paragraph_id':'p0012'}}
 def payment_unit(parent,sha='a'*64):
  text='(3)适应症发生重大变化，主动申请调整医保支付范围的药品。'
  contexts=[{'context_id':'current','kind':'paragraph','text':text,'source_ref':ref,'structure':{'paragraph_id':'p0012','unit_id':'unit'}},
   {'context_id':'parent','kind':'parent_paragraph','text':parent,'source_ref':{'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{'paragraph_id':'p0008'}},'structure':{'paragraph_id':'p0008','unit_id':'unit'}}]
  return {'text':text,'contexts':contexts,'source_ref':ref}
 for name,parent,sha,expected in [('elliptical payment consequence','以下情况须申报后方可调整:','a'*64,1),('ordinary administrative list','以下为申报药品名称:','a'*64,0),('foreign payment parent','以下情况须申报后方可调整:','b'*64,0)]:
  cases.append({'name':name,'semantic_input':payment_unit(parent,sha),'expected':{'Ec':expected},'synthetic':True})
 for sid,dim in [('00005','S'),('00900','Ec'),('01459','E')]:
  u=copy.deepcopy(sources[sid]);primary=u['source_ref']['sha256']
  # Deliberately remove all donor material, retaining only exact current text.
  u['contexts']=[c for c in u['contexts'] if c['kind']=='paragraph' and m['relations'].norm(c.get('text',''))==m['relations'].norm(u['text'])]
  u['source_bundle']={};u['derived_context_origins']={}
  cases.append({'name':'missing source prevents inheritance '+sid,'semantic_input':u,'expected':{dim:None},'synthetic':True})
 # Cited-reference container controls. Remove whole selected donor groups from
 # the synthetic semantic input, with no original packet mutation or external IO.
 original=sources['01423'];contexts=original['contexts']
 cited=[c for c in contexts if c['kind']=='cited_reference']
 def addressed(c):
  text=str(c.get('structure',{}).get('reference_address',''))
  return 7 if '七' in text else 6 if '六' in text else None
 for variation in ('missing sixth article','missing seventh boundary','missing sixth boundary','foreign sixth article','reordered seventh clauses'):
  u=copy.deepcopy(original);drop=set()
  for container in u['contexts']:
   number=addressed(container)
   if number is None:continue
   child_ids=[cid for g in container.get('structure',{}).get('child_groups',[]) if g.get('position')=='contexts' for cid in g.get('ordered_context_ids',[])]
   boundary_ids=[cid for g in container.get('structure',{}).get('child_groups',[]) if g.get('position')=='structure_boundary' for cid in g.get('ordered_context_ids',[])]
   if variation=='missing sixth article' and number==6:drop.update([container['context_id']]+child_ids+boundary_ids)
   if variation=='missing seventh boundary' and number==7:drop.update(boundary_ids)
   if variation=='missing sixth boundary' and number==6:drop.update(boundary_ids)
   if variation=='foreign sixth article' and number==6:
    for c in u['contexts']:
     if c['context_id'] in [container['context_id']]+child_ids+boundary_ids:c['source_ref']['sha256']='b'*64
   if variation=='reordered seventh clauses' and number==7:
    for g in container['structure']['child_groups']:
     if g.get('position')=='contexts':g['ordered_context_ids']=list(reversed(g['ordered_context_ids']))
  u['contexts']=[c for c in u['contexts'] if c['context_id'] not in drop]
  # The independent base branch retains S/E; an unclosed whole exception
  # keeps its otherwise unknown economic and fairness consumers unresolved.
  cases.append({'name':'table exception guard '+variation,'semantic_input':u,'expected':{'S':1,'E':1,'Ec':None,'F':None},'synthetic':True})
 save(P/'relation-controls-fixed-before-edit.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'identity':'fixed exposed development relation controls, not independent validation','expected_not_classifier_input':True,'cases':cases})
 print('fixed_cases',len(cases))
def run(name):
 O=P/name;O.mkdir(exist_ok=False);snap=O/'code-snapshot';snap.mkdir();m={}
 for n in NAMES:(snap/(n+'.py')).write_bytes((P/(n+'.py')).read_bytes())
 m=modules(snap);fixed=P/(sys.argv[2] if len(sys.argv)>2 else 'relation-controls-fixed-before-edit.json');x=json.loads(fixed.read_bytes())
 save(O/'pre-execution-seal.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'fixed_controls':bind(fixed),'code':[bind(snap/(n+'.py')) for n in NAMES],'expected_not_classifier_input':True})
 results=[];active=[False];denied=[]
 def audit(event,args):
  if active[0] and event=='open':denied.append(str(args[0]));raise RuntimeError('Classifier filesystem IO denied')
 sys.addaudithook(audit)
 for c in x['cases']:
  u=copy.deepcopy(c['semantic_input']);before=copy.deepcopy(u);r={k:v for k,v in c.items() if k!='semantic_input'}
  try:
   active[0]=True;v=m['relations'].RelationView(u);ds=m['dimensions'].judge(v);m['evidence'].validate_decisions(u,ds);active[0]=False
   assert u==before
   values={d:ds[d]['value'] for d in c['expected']};r.update(actual=values,passed=values==c['expected'],decisions=ds,relations=v.traces(),material_requests=v.material_requests,structural_address_issues=v.structural_address_issues)
  except Exception as e:
   active[0]=False;r.update(passed=False,error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
  results.append(r)
 summary={'case_N':len(results),'pass_N':sum(r['passed'] for r in results),'failure_N':sum(not r['passed'] for r in results),'failed':[{'name':r['name'],'expected':r['expected'],'actual':r.get('actual'),'error':r.get('error')} for r in results if not r['passed']],'filesystem_access_attempts_during_classification':denied,'identity':'disclosed relation development controls','formal_validation_complete':False}
 save(O/'results.json',results);save(O/'summary.json',summary);save(O/'seal.json',{'files':[bind(p) for p in sorted(O.rglob('*')) if p.is_file()],'self_excluded':True})
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 else:run(sys.argv[1])

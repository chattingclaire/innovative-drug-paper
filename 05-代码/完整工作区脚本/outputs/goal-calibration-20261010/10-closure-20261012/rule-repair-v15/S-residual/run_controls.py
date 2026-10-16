"""Only the six pre-fixed S residual controls, no old suites or population."""
from pathlib import Path
import copy,datetime,hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
NAMES=('evidence','source_packet','source_receipts','relations','dimensions')
def read(p):return json.loads(p.read_text())
def binding(p):
 b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,j):
 with p.open('x') as f:json.dump(j,f,ensure_ascii=False,indent=2);f.write('\n')
def load(p):
 out={}
 for n in NAMES:
  spec=importlib.util.spec_from_file_location(n,p/(n+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);out[n]=m
 return out
p=read(HERE/'preparation.json');B=Path(p['base']);C=Path(p['candidate']);O=HERE/'attempt01';O.mkdir(exist_ok=False);snap=O/'code-snapshot';snap.mkdir()
for b in p['base_code']+[p['index'],p['controls'],p['diagnosis'],p['composition']]:assert binding(Path(b['path']))==b
for n in NAMES:(snap/(n+'.py')).write_bytes((C/(n+'.py')).read_bytes())
for n in NAMES[:-1]:assert (B/(n+'.py')).read_bytes()==(C/(n+'.py')).read_bytes()
cs=read(HERE/'controls-index.json')['cases'];assert len(cs)==6 and len({c['name'] for c in cs})==6
prepared=[]
for c in cs:
 bundle=None
 if 'packet_binding' in c:
  b=c['packet_binding'];assert binding(Path(b['path']))==b;bundle=read(Path(b['path']))['source_bundle']
 prepared.append((c,bundle))
save(O/'pre-execution-seal.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base':p['base_code'],'candidate':[binding(C/(n+'.py')) for n in NAMES],'driver':binding(Path(__file__)),'controls':p['controls'],'index':p['index'],'case_N':6,'old_suites_executed':False})
bm=load(B);cm=load(snap);active=[False];denied=[]
def audit(event,args):
 if active[0] and event=='open':denied.append(str(args[0]));raise RuntimeError('classifier filesystem access denied')
sys.addaudithook(audit)
def run(m,u):
 original=copy.deepcopy(u);active[0]=True
 try:
  view=m['relations'].RelationView(copy.deepcopy(u));ds=m['dimensions'].judge(view);m['evidence'].validate_decisions(u,ds);assert view.unit==original
  return {'decisions':ds,'values':{d:x['value'] for d,x in ds.items()},'relations':view.traces(),'source_events':view.source_view_events,'source_requests':view.source_requests,'material_requests':view.material_requests,'private_I_requests':getattr(view,'v11_protected_data_requests',[])}
 finally:active[0]=False
rows=[]
for c,bundle in prepared:
 row={k:v for k,v in c.items() if k!='semantic_input'}
 try:
  u=cm['source_packet'].semantic_unit(bundle) if bundle else c['semantic_input'];a=run(bm,u);b=run(cm,u)
  row.update(baseline=a,candidate=b,expected_match=all(b['values'][d]==v for d,v in c['expected'].items()),baseline_expected_match=all(a['values'][d]==v for d,v in c['expected'].items()),protected_equal=all(a['decisions'][d]==b['decisions'][d] for d in ['E','Ec','I','F']),source_equal=all(a[k]==b[k] for k in ['relations','source_events','source_requests','material_requests','private_I_requests']),changed_dimensions=[d for d in a['decisions'] if a['decisions'][d]!=b['decisions'][d]])
  row['pass']=all(row[k] for k in ['expected_match','protected_equal','source_equal'])
 except Exception as e:row.update({'pass':False,'error':{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}})
 rows.append(row)
summary={'case_N':len(rows),'pass_N':sum(x['pass'] for x in rows),'failed':[{'name':x['name'],'expected':x['expected'],'error':x.get('error'),'actual':x.get('candidate',{}).get('values')} for x in rows if not x['pass']],'protected_changes':[x['name'] for x in rows if x.get('protected_equal') is False],'source_changes':[x['name'] for x in rows if x.get('source_equal') is False],'changed_cases':[{'name':x['name'],'dimensions':x['changed_dimensions'],'baseline':x['baseline']['values'],'candidate':x['candidate']['values']} for x in rows if x.get('changed_dimensions')],'classifier_filesystem_access_attempts':denied,'model_calls':0,'population_calls':0,'old_suites_executed':False,'production_modified':False}
save(O/'results.json',rows);save(O/'summary.json',summary);save(O/'output-seal.json',{'files':[binding(f) for f in sorted(O.rglob('*')) if f.is_file()]});print(json.dumps(summary,ensure_ascii=False,indent=2))

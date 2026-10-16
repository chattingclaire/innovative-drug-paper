from pathlib import Path
import sys,json,hashlib,copy,importlib.util,datetime,traceback
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];D=R/'08-audits/v9-generic-relationship-repair-design-sol/revision02-bidirectional-before-implementation';V=O.parent/'joint-v8-target-product-gap-sol'
NAMES=['evidence','source_packet','source_receipts','relations','dimensions']
def bind(p):
 p=p.resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,x):
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def mods(p):
 result={}
 for n in NAMES:
  spec=importlib.util.spec_from_file_location(n,p/(n+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);result[n]=m
 return result
out=O/sys.argv[1];out.mkdir(exist_ok=False);snap=out/'code-snapshot';snap.mkdir()
for n in NAMES:(snap/(n+'.py')).write_bytes((O/(n+'.py')).read_bytes())
fixed=D/'real-controls-fixed-before-edit.json';syn=D/'synthetic-controls-fixed-before-edit.json'
raw=json.loads(fixed.read_bytes());synthetics=json.loads(syn.read_bytes())
extra=[O/'supplemental-controls-before-attempt02.json',O/'supplemental-controls-b-before-attempt02.json',O/'supplemental-controls-before-attempt04.json',O/'supplemental-controls-before-attempt06.json']
for path in extra:synthetics['cases'].extend(json.loads(path.read_bytes())['cases'])
# Entire authorized selection is fixed; failures and pending examples retained.
inputs=[]
for c in raw['cases']:
 spec=c['packet_binding'];assert bind(Path(spec['path']))==spec
 packet=json.loads(Path(spec['path']).read_bytes());inputs.append((c,packet['source_bundle']))
save(out/'pre-execution-seal.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'controls':[bind(fixed),bind(syn)]+[bind(p) for p in extra],'code':[bind(snap/(n+'.py')) for n in NAMES],'old_code':[bind(V/(n+'.py')) for n in NAMES],'classifier_input_omits_expected_and_record_identity':True,'whole4481_classification':False})
old=mods(V);new=mods(snap);active=[False];denied=[]
def audit(event,args):
 if active[0] and event=='open':denied.append(str(args[0]));raise RuntimeError('Classifier filesystem I/O denied')
sys.addaudithook(audit)
def run(m,u):
 before=copy.deepcopy(u);active[0]=True
 try:
  v=m['relations'].RelationView(copy.deepcopy(u));ds=m['dimensions'].judge(v);m['evidence'].validate_decisions(u,ds);assert v.unit==before
  return {'decisions':ds,'values':{d:ds[d]['value'] for d in ds},'relations':v.traces(),'material_requests':v.material_requests,'source_requests':v.source_requests,'source_events':v.source_view_events}
 finally:active[0]=False
results=[];cache={}
for c,b in inputs:
 row={k:v for k,v in c.items()};key=c['packet_binding']['sha256']
 try:
  if key not in cache:
   u=new['source_packet'].semantic_unit(b);cache[key]=(run(old,u),run(new,u))
  a,z=cache[key];row.update(actual={d:z['values'][d] for d in c['expected']},old_values=a['values'],new_values=z['values'],passed=all(z['values'][d]==v for d,v in c['expected'].items()),SEEc_complete_decisions_equal=all(a['decisions'][d]==z['decisions'][d] for d in ['S','E','Ec']),gate_outside_complete_decisions_equal=(None if new['dimensions']._v9_repair_gate(new['relations'].norm(b['source_record']['text'])) else a['decisions']==z['decisions']),candidate=z,baseline=a)
  if c.get('must_not_add_unproved_whole_programme_positive'):
   d=c['pending_dimensions'][0];path=z['decisions'][d]['basis_path'];row['restricted_mother_no_new_positive']=not (z['values'][d]==1 and path.startswith('v9_'))
 except Exception as exc:row.update(passed=False,error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()})
 results.append(row)
for c in synthetics['cases']:
 row={k:v for k,v in c.items() if k!='semantic_input'}
 try:
  a=run(old,c['semantic_input']);z=run(new,c['semantic_input']);row.update(actual={d:z['values'][d] for d in c['expected']},old_values=a['values'],new_values=z['values'],passed=all(z['values'][d]==v for d,v in c['expected'].items()),SEEc_complete_decisions_equal=all(a['decisions'][d]==z['decisions'][d] for d in ['S','E','Ec']),gate_outside_complete_decisions_equal=(None if new['dimensions']._v9_repair_gate(new['relations'].norm(c['semantic_input']['text'])) else a['decisions']==z['decisions']),candidate=z,baseline=a)
 except Exception as exc:row.update(passed=False,error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()})
 results.append(row)
summary={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'case_N':len(results),'hard_assertion_case_N':sum(c['hard_assertion'] for c in results),'passed_N':sum(c['passed'] for c in results),'failed_N':sum(not c['passed'] for c in results),'hard_passed_N':sum(c['hard_assertion'] and c['passed'] for c in results),'hard_failed_N':sum(c['hard_assertion'] and not c['passed'] for c in results),'pending_N':sum(not c['hard_assertion'] for c in results),'all_failures':[{'name':c['name'],'expected':c['expected'],'actual':c.get('actual'),'error':c.get('error')} for c in results if not c['passed']],'SEEc_complete_decision_mismatch':[c['name'] for c in results if c.get('SEEc_complete_decisions_equal') is False],'outside_gate_complete_decision_mismatch':[c['name'] for c in results if c.get('gate_outside_complete_decisions_equal') is False],'restricted_mother_unproved_positive':[c['name'] for c in results if c.get('restricted_mother_no_new_positive') is False],'filesystem_access_attempts':denied,'selected_packet_N':len(cache),'identity':'fixed exposed development controls, never independent accuracy or gold','all_cases_retained':True}
save(out/'results.json',results);save(out/'summary.json',summary);save(out/'output-seal.json',{'files':[bind(p) for p in sorted(out.rglob('*')) if p.is_file()],'self_excluded':True});print(json.dumps(summary,ensure_ascii=False,indent=2))

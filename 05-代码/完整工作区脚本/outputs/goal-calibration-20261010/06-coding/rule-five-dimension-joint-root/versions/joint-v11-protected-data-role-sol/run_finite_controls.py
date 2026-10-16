from pathlib import Path
import sys,json,hashlib,copy,importlib.util,datetime,traceback
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];D=R/'08-audits/v9-generic-relationship-repair-design-sol/revision02-bidirectional-before-implementation';OLDV9=O.parent/'joint-v9-generic-relationship-sol';V=O.parent/'joint-v10-if-e-combined-v2-root';IF_AUD=R/'08-audits/v10-generic-relationship-repair-sol';AUD=R/'08-audits/v11-protected-data-role-repair-sol'
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
out=AUD/sys.argv[1];out.mkdir(exist_ok=False);snap=out/'code-snapshot';snap.mkdir()
for n in NAMES:(snap/(n+'.py')).write_bytes((O/(n+'.py')).read_bytes())
fixed=D/'real-controls-fixed-before-edit.json';syn=D/'synthetic-controls-fixed-before-edit.json'
raw=json.loads(fixed.read_bytes());synthetics=json.loads(syn.read_bytes())
extra=[OLDV9/'supplemental-controls-before-attempt02.json',OLDV9/'supplemental-controls-b-before-attempt02.json',OLDV9/'supplemental-controls-before-attempt04.json',OLDV9/'supplemental-controls-before-attempt06.json']
for path in extra:synthetics['cases'].extend(json.loads(path.read_bytes())['cases'])
extra.append(IF_AUD/'new-controls-fixed-before-edit.json');synthetics['cases'].extend(json.loads(extra[-1].read_bytes())['cases'])
extra.append(IF_AUD/'additional-counter-controls-fixed-before-attempt02.json');synthetics['cases'].extend(json.loads(extra[-1].read_bytes())['cases'])
extra.append(R/'08-audits/e-complete-response-coverage-repair-sol/targeted24-fixed-before-second-edit.json');synthetics['cases'].extend(json.loads(extra[-1].read_bytes())['cases'])
extra.append(AUD/'new-role-controls-fixed-before-edit.json');roles=json.loads(extra[-1].read_bytes());raw['cases'].extend(roles['real_cases']);synthetics['cases'].extend(roles['cases'])
# Entire authorized selection is fixed; failures and pending examples retained.
inputs=[]
for c in raw['cases']:
 spec=c['packet_binding'];assert bind(Path(spec['path']))==spec
 packet=json.loads(Path(spec['path']).read_bytes());inputs.append((c,packet['source_bundle']))
save(out/'pre-execution-seal.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'gate':bind(O/'static_gate.py'),'driver':bind(Path(__file__)),'controls':[bind(fixed),bind(syn)]+[bind(p) for p in extra],'code':[bind(snap/(n+'.py')) for n in NAMES],'old_code':[bind(V/(n+'.py')) for n in NAMES],'classifier_input_omits_expected_and_record_identity':True,'whole4481_classification':False})
old=mods(V);new=mods(snap)
spec=importlib.util.spec_from_file_location('pure_gate',O/'static_gate.py');pure=importlib.util.module_from_spec(spec);spec.loader.exec_module(pure)
active=[False];denied=[]
def audit(event,args):
 if active[0] and event=='open':denied.append(str(args[0]));raise RuntimeError('Classifier filesystem I/O denied')
sys.addaudithook(audit)
def run(m,u):
 before=copy.deepcopy(u);active[0]=True
 try:
  v=m['relations'].RelationView(copy.deepcopy(u));ds=m['dimensions'].judge(v);m['evidence'].validate_decisions(u,ds);assert v.unit==before
  return {'decisions':ds,'values':{d:ds[d]['value'] for d in ds},'relations':v.traces(),'material_requests':v.material_requests,'source_requests':v.source_requests,'source_events':v.source_view_events,'input_unchanged':v.unit==before,'private_v11_I_requests':copy.deepcopy(getattr(v,'v11_protected_data_requests',[]))}
 finally:active[0]=False
results=[];cache={}
for c,b in inputs:
 row={k:v for k,v in c.items()};key=c['packet_binding']['sha256']
 try:
  if key not in cache:
   u=new['source_packet'].semantic_unit(b);cache[key]=(run(old,u),run(new,u))
  a,z=cache[key];row.update(actual={d:z['values'][d] for d in c['expected']},old_values=a['values'],new_values=z['values'],passed=all(z['values'][d]==v for d,v in c['expected'].items()),SEEcF_complete_decisions_equal=all(a['decisions'][d]==z['decisions'][d] for d in ['S','E','Ec','F']),gate_outside_complete_decisions_equal=(None if pure.gate(b['source_record']['text']) else a['decisions']==z['decisions']),candidate=z,baseline=a)
  if c.get('must_not_add_unproved_whole_programme_positive'):
   d=c['pending_dimensions'][0];path=z['decisions'][d]['basis_path'];row['restricted_mother_no_new_positive']=not (z['values'][d]==1 and path.startswith(('v9_','v10_','v11_')))
 except Exception as exc:row.update(passed=False,error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()})
 row['old_relations_preserved']=('baseline' in row and row['baseline']['relations']==[r for r in row['candidate']['relations'] if r['kind']!='v11_protected_data_I_relationship'])
 row['source_state_equal']=('baseline' in row and all(row['baseline'][k]==row['candidate'][k] for k in ['material_requests','source_requests','source_events']))
 if c.get('must_not_add_v10_positive') and 'candidate' in row:row['no_unproved_v10_positive']=not any(r['kind']=='v10_IF_relationship' for r in row['candidate']['relations'])
 if c.get('must_not_add_v11_positive') and 'candidate' in row:
  row['no_unproved_v11_positive']=not any(r['kind']=='v11_protected_data_I_relationship' for r in row['candidate']['relations'])
  row['passed']=row['passed'] and row['no_unproved_v11_positive']
 if 'candidate' in row:
  row['private_v11_request_I_only']=all(d['kind']=='v11_protected_data_I_dependency' and d['affected_dimensions']==['I'] and d['request']['dimensions']==['I'] and d['request']['affected_dimensions']==['I'] for d in row['candidate']['private_v11_I_requests'])
  row['gate_outside_private_request_empty']=None if pure.gate(b['source_record']['text']) else not row['candidate']['private_v11_I_requests']
 results.append(row)
for c in synthetics['cases']:
 row={k:v for k,v in c.items() if k!='semantic_input'}
 try:
  a=run(old,c['semantic_input']);z=run(new,c['semantic_input']);row.update(actual={d:z['values'][d] for d in c['expected']},old_values=a['values'],new_values=z['values'],passed=all(z['values'][d]==v for d,v in c['expected'].items()),SEEcF_complete_decisions_equal=all(a['decisions'][d]==z['decisions'][d] for d in ['S','E','Ec','F']),gate_outside_complete_decisions_equal=(None if pure.gate(c['semantic_input']['text']) else a['decisions']==z['decisions']),candidate=z,baseline=a)
 except Exception as exc:row.update(passed=False,error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()})
 row['old_relations_preserved']=('baseline' in row and row['baseline']['relations']==[r for r in row['candidate']['relations'] if r['kind']!='v11_protected_data_I_relationship'])
 row['source_state_equal']=('baseline' in row and all(row['baseline'][k]==row['candidate'][k] for k in ['material_requests','source_requests','source_events']))
 if c.get('must_not_add_v10_positive') and 'candidate' in row:row['no_unproved_v10_positive']=not any(r['kind']=='v10_IF_relationship' for r in row['candidate']['relations'])
 if c.get('must_not_add_v11_positive') and 'candidate' in row:
  row['no_unproved_v11_positive']=not any(r['kind']=='v11_protected_data_I_relationship' for r in row['candidate']['relations'])
  row['passed']=row['passed'] and row['no_unproved_v11_positive']
 if 'candidate' in row:
  row['private_v11_request_I_only']=all(d['kind']=='v11_protected_data_I_dependency' and d['affected_dimensions']==['I'] and d['request']['dimensions']==['I'] and d['request']['affected_dimensions']==['I'] for d in row['candidate']['private_v11_I_requests'])
  row['gate_outside_private_request_empty']=None if pure.gate(c['semantic_input']['text']) else not row['candidate']['private_v11_I_requests']
 results.append(row)
summary={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'case_N':len(results),'hard_assertion_case_N':sum(c['hard_assertion'] for c in results),'passed_N':sum(c['passed'] for c in results),'failed_N':sum(not c['passed'] for c in results),'hard_passed_N':sum(c['hard_assertion'] and c['passed'] for c in results),'hard_failed_N':sum(c['hard_assertion'] and not c['passed'] for c in results),'pending_N':sum(not c['hard_assertion'] for c in results),'all_failures':[{'name':c['name'],'expected':c['expected'],'actual':c.get('actual'),'error':c.get('error')} for c in results if not c['passed']],'SEEcF_complete_decision_mismatch':[c['name'] for c in results if c.get('SEEcF_complete_decisions_equal') is False],'outside_gate_complete_decision_mismatch':[c['name'] for c in results if c.get('gate_outside_complete_decisions_equal') is False],'restricted_mother_unproved_positive':[c['name'] for c in results if c.get('restricted_mother_no_new_positive') is False],'filesystem_access_attempts':denied,'selected_packet_N':len(cache),'identity':'fixed exposed development controls, never independent accuracy or gold','all_cases_retained':True,'original_control_N':189,'new_IF_counter_control_N':12,'new_E_counter_control_N':24,'new_v11_role_control_N':16,'local_execution_limit':2,'production_classifier_calls':0,'model_calls':0,'private_v11_request_non_I':[c['name'] for c in results if c.get('private_v11_request_I_only') is False],'unproved_v11_positive':[c['name'] for c in results if c.get('no_unproved_v11_positive') is False],'old_relation_mismatch':[c['name'] for c in results if not c['old_relations_preserved']],'source_state_mismatch':[c['name'] for c in results if not c['source_state_equal']],'unproved_v10_positive':[c['name'] for c in results if c.get('no_unproved_v10_positive') is False]}
save(out/'results.json',results);save(out/'summary.json',summary);save(out/'output-seal.json',{'files':[bind(p) for p in sorted(out.rglob('*')) if p.is_file()],'self_excluded':True});print(json.dumps(summary,ensure_ascii=False,indent=2))

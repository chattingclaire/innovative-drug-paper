"""Execute only fixed F-domain controls; no shared353 or population run."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];VERS=ROOT/'06-coding/rule-five-dimension-joint-root/versions'
BASE=VERS/'joint-v14f-form-gap-root';CANDIDATE=VERS/'joint-v14fb-form-gap-scope-root'
NAMES=('evidence','source_packet','source_receipts','relations','dimensions')
def read(p):return json.loads(p.read_text())
def binding(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,x):
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def modules(folder):
 d={}
 for n in NAMES:
  spec=importlib.util.spec_from_file_location(n,folder/(n+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);d[n]=m
 return d

def main():
 name=sys.argv[1];assert Path(name).name==name and name not in ('.','..');out=HERE/name;out.mkdir(exist_ok=False);snap=out/'code-snapshot';snap.mkdir()
 prep=read(HERE/'preparation.json')
 for b in prep['base_files']:assert binding(Path(b['path']))==b
 for n in NAMES:(snap/(n+'.py')).write_bytes((CANDIDATE/(n+'.py')).read_bytes())
 for n in NAMES:
  if n!='relations':assert (BASE/(n+'.py')).read_bytes()==(snap/(n+'.py')).read_bytes()
 ix=read(HERE/'controls-index.json')
 for b in ix['input_bindings']:assert binding(Path(b['path']))==b
 cases=ix['cases'];assert len(cases)==31 and len({(c['control_file'],c['name']) for c in cases})==31
 prepared=[]
 for c in cases:
  if 'packet_binding' in c:
   b=c['packet_binding'];assert binding(Path(b['path']))==b;u=read(Path(b['path']))['source_bundle'];kind='bundle'
  elif 'synthetic_bundle' in c:u=c['synthetic_bundle'];kind='bundle'
  else:u=c['semantic_input'];kind='semantic'
  prepared.append((c,u,kind))
 save(out/'pre-execution-seal.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'baseline':[binding(BASE/(n+'.py')) for n in NAMES],'candidate':[binding(snap/(n+'.py')) for n in NAMES],'driver':binding(Path(__file__)),'index':binding(HERE/'controls-index.json'),'input_files':ix['input_bindings'],'preparation':binding(HERE/'preparation.json'),'previous_proposal_preserved':binding(HERE/'additional-scope-controls-fixed-before-edit.json'),'case_N':31,'shared353_rerun':False,'overall_execution':False})
 old=modules(BASE);new=modules(snap);active=[False];denied=[]
 def audit(event,args):
  if active[0] and event=='open':denied.append(str(args[0]));raise RuntimeError('Classifier filesystem I/O denied')
 sys.addaudithook(audit)
 def run(mod,unit):
  original=copy.deepcopy(unit);active[0]=True
  try:
   view=mod['relations'].RelationView(copy.deepcopy(unit));dec=mod['dimensions'].judge(view);mod['evidence'].validate_decisions(unit,dec);assert view.unit==original
   return {'decisions':dec,'values':{d:x['value'] for d,x in dec.items()},'relations':view.traces(),'material_requests':view.material_requests,'source_requests':view.source_requests,'source_events':view.source_view_events,'private_I_requests':copy.deepcopy(getattr(view,'v11_protected_data_requests',[]))}
  finally:active[0]=False
 rows=[]
 for c,u,kind in prepared:
  row={k:v for k,v in c.items() if k not in ('semantic_input','synthetic_bundle')}
  try:
   unit=new['source_packet'].semantic_unit(u) if kind=='bundle' else u;a,b=run(old,unit),run(new,unit)
   row.update(baseline=a,candidate=b,baseline_expected_match=all(a['values'][d]==v for d,v in c['expected'].items()),expected_match=all(b['values'][d]==v for d,v in c['expected'].items()),unchanged_S_E_Ec_I=all(a['decisions'][d]==b['decisions'][d] for d in ('S','E','Ec','I')),source_state_equal=all(a[k]==b[k] for k in ('material_requests','source_requests','source_events','private_I_requests')),changed_dimensions=[d for d in a['decisions'] if a['decisions'][d]!=b['decisions'][d]])
   checks={}
   if Path(c['control_file']).name=='form-gap-controls-fixed-before-edit.json':checks['original24_five_complete_decisions_equal']=a['decisions']==b['decisions']
   newrels=[x for x in b['relations'] if x.get('details',{}).get('v9_semantic_path')=='current_form_suitability_gap_qualification']
   if newrels:
    used={q['context_id'] for x in newrels for q in x.get('context_evidence',[])};readids={x.get('resource_id') for x in b['source_events'] if x.get('view')=='text' and x.get('event_kind')=='actual_structured_json_scan'}
    checks['F_relation_evidence_actually_read']=bool(used) and used<=readids
   row['extra_checks']=checks;row['pass']=row['expected_match'] and row['unchanged_S_E_Ec_I'] and row['source_state_equal'] and all(checks.values())
  except Exception as e:row.update({'pass':False,'error':{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}})
  rows.append(row)
 hard=[x for x in rows if x.get('hard_assertion',True)];pending=[x for x in rows if not x.get('hard_assertion',True)]
 summary={'at_utc':datetime.now(timezone.utc).isoformat(),'N':len(rows),'hard_N':len(hard),'hard_pass_N':sum(x['pass'] for x in hard),'hard_failed':[{'name':x['name'],'expected':x['expected'],'baseline':x.get('baseline',{}).get('values'),'candidate':x.get('candidate',{}).get('values'),'error':x.get('error'),'extra_checks':x.get('extra_checks')} for x in hard if not x['pass']],'pending_N':len(pending),'pending':[{'name':x['name'],'candidate_values':x.get('candidate',{}).get('values'),'semantic_reason':x['semantic_reason']} for x in pending],'nonF_changes':[x['name'] for x in rows if x.get('unchanged_S_E_Ec_I') is False],'source_state_changes':[x['name'] for x in rows if x.get('source_state_equal') is False],'original24_full_decision_changes':[x['name'] for x in rows if x.get('extra_checks',{}).get('original24_five_complete_decisions_equal') is False],'changed_cases':[{'name':x['name'],'dimensions':x.get('changed_dimensions'),'before':x.get('baseline',{}).get('values'),'after':x.get('candidate',{}).get('values')} for x in rows if x.get('changed_dimensions')],'filesystem_access_attempts':denied,'shared353_rerun':False,'all_failed_results_preserved':True,'classifier_only_NONHUMAN_or_exposed_development_material':True,'formal_validation':False,'production_execution':False,'adoption':False}
 save(out/'results.json',rows);save(out/'summary.json',summary);save(out/'output-seal.json',{'files':[binding(p) for p in sorted(out.rglob('*')) if p.is_file()],'self_excluded':True});print(json.dumps({k:v for k,v in summary.items() if k!='changed_cases'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()

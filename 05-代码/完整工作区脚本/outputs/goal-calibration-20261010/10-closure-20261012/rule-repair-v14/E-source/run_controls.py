"""Bounded E45+finite-standard controls only; never population execution."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,importlib.util,json,sys,traceback
from routing_checks import check_actual_route
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
VERS=ROOT/'06-coding/rule-five-dimension-joint-root/versions'
BASE=VERS/'joint-v14e2-mixed-action-root'
CANDIDATE=VERS/'joint-v14e3-finite-standard-root'
NAMES=('evidence','source_packet','source_receipts','relations','dimensions')
def read(p):return json.loads(p.read_text())
def binding(p):
 raw=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(p,d):
 with p.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def modules(p):
 result={}
 for n in NAMES:
  spec=importlib.util.spec_from_file_location(n,p/(n+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);result[n]=m
 return result

def main():
 out=HERE/sys.argv[1];assert out.parent==HERE and sys.argv[1] not in ('.','..');out.mkdir(exist_ok=False);snapshot=out/'code-snapshot';snapshot.mkdir()
 for item in read(HERE/'preparation.json')['base_files']:assert binding(Path(item['path']))==item
 for n in NAMES:(snapshot/(n+'.py')).write_bytes((CANDIDATE/(n+'.py')).read_bytes())
 cases=read(HERE/'controls-index.json')['cases'];assert len(cases)==62
 prepared=[]
 for c in cases:
  if 'packet_binding' in c:
   pb=c['packet_binding'];assert binding(Path(pb['path']))==pb;bundle=read(Path(pb['path']))['source_bundle']
  else:bundle=c.get('synthetic_bundle')
  prepared.append((c,bundle))
 save(out/'pre-execution-seal.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'controls_index':binding(HERE/'controls-index.json'),'baseline':[binding(BASE/(n+'.py')) for n in NAMES],'candidate':[binding(snapshot/(n+'.py')) for n in NAMES],'runner':binding(Path(__file__)),'routing':binding(HERE/'routing_checks.py'),'shared353_executed':False,'case_N':62})
 old,new=modules(BASE),modules(snapshot);active=[False];denied=[]
 def audit(event,args):
  if active[0] and event=='open':denied.append(str(args[0]));raise RuntimeError('Classifier filesystem I/O denied')
 sys.addaudithook(audit)
 def run(loaded,unit,bundle,route):
  original=copy.deepcopy(unit);active[0]=True
  try:
   view=loaded['relations'].RelationView(copy.deepcopy(unit));decisions=loaded['dimensions'].judge(view);loaded['evidence'].validate_decisions(unit,decisions);assert view.unit==original
  finally:active[0]=False
  proof=check_actual_route(loaded,view,decisions,bundle) if route and bundle else None
  return {'decisions':decisions,'values':{d:x['value'] for d,x in decisions.items()},'relations':view.traces(),'material_requests':view.material_requests,'source_requests':view.source_requests,'source_events':view.source_view_events,'private_I_requests':getattr(view,'v11_protected_data_requests',[]),'routing_proof':proof}
 results=[]
 for case,bundle in prepared:
  row={k:v for k,v in case.items() if k not in ('semantic_input','synthetic_bundle')}
  try:
   unit=new['source_packet'].semantic_unit(bundle) if bundle else case['semantic_input'];b=run(old,unit,bundle,False);c=run(new,unit,bundle,case.get('source_revision_case',False) or case['name'] in ('current_material_RECODE25-04598','requested_list_missing_member','independent_E_positive_with_unclosed_requested_scope'))
   mutable=case.get('mutable_dimensions',['E']);protected=all(b['decisions'][d]==c['decisions'][d] for d in ('S','E','Ec','I','F') if d not in mutable)
   source_equal=all(b[k]==c[k] for k in ('source_events','private_I_requests'))
   prefix=all(c[k][:len(b[k])]==b[k] for k in ('material_requests','source_requests','relations'))
   new_requests=[x for k in ('material_requests','source_requests') for x in c[k][len(b[k]):]]
   typed=all((q.get('path'),q.get('dimensions'),q.get('affected_dimensions'),q.get('producer')) in [('E_explicit_content_scope',['E'],['E'],'E_closed_content_dependency'),('F_finite_standard_scope',['F'],['F'],'F_finite_standard_dependency'),('S_finite_standard_scope',['S'],['S'],'S_finite_standard_dependency')] and q.get('dependency_status')=='stopped' for q in new_requests)
   expected=all(c['values'][d]==x for d,x in case['expected'].items());old_preservation=b['decisions']['E']==c['decisions']['E'] if case.get('require_E_unchanged') else None
   revision=case.get('preservation_contract_revision');superseded=bool(revision and 'require_E_unchanged' in revision['superseded_flags'])
   new_contract=(all(c['values'][d] is None for d in ('S','E','F'))) if superseded else True
   preservation=old_preservation is not False or superseded
   new_relations=c['relations'][len(b['relations']):];relation_scope=all(x['kind']=='finite_standard_scope' and x['details']['affected_dimensions']==['S','E','F'] for x in new_relations)
   readids={e['resource_id'] for e in c['source_events'] if e['view']=='text'};origins=unit.get('derived_context_origins',{})
   quotes=[]
   def collect(x):
    if isinstance(x,dict):
     if 'context_id' in x and 'source_ref' in x and 'text' in x and 'start' in x:quotes.append(x)
     for y in x.values():collect(y)
    elif isinstance(x,list):
     for y in x:collect(y)
   collect(c['decisions']);actual_read=all(q['context_id'] in readids or origins.get(q['context_id'],{}).get('origin_inventory_resource_id') in readids for q in quotes)
   row.update(baseline=b,candidate=c,expected_match=expected,protected_decisions_equal=protected,old_source_prefixes_equal=prefix,old_READ_and_private_I_equal=source_equal,new_requests_typed_only=typed,new_relation_scope_only=relation_scope,exact_evidence_actually_read=actual_read,old_preservation_check=old_preservation,preservation_contract_superseded=superseded,new_contract_pass=new_contract,changed_dimensions=[d for d in b['decisions'] if b['decisions'][d]!=c['decisions'][d]])
   row['pass']=all([expected,protected,prefix,source_equal,typed,relation_scope,actual_read,preservation,new_contract])
  except Exception as exc:row.update({'pass':False,'error':{'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}})
  results.append(row)
 save(out/'results.json',results)
 summary={'at_utc':datetime.now(timezone.utc).isoformat(),'case_N':len(results),'pass_N':sum(x['pass'] for x in results),'failed':[{'name':x['name'],'error':x.get('error'),'values':x.get('candidate',{}).get('values'),'expected':x['expected'],'checks':{k:v for k,v in x.items() if type(v) is bool}} for x in results if not x['pass']],'changed':[{'name':x['name'],'dimensions':x.get('changed_dimensions'),'before':x.get('baseline',{}).get('values'),'after':x.get('candidate',{}).get('values')} for x in results if x.get('changed_dimensions')],'superseded_preservation':[{'name':x['name'],'old_preservation_check':x.get('old_preservation_check'),'new_contract_pass':x.get('new_contract_pass')} for x in results if x.get('preservation_contract_superseded')],'classifier_filesystem_attempts':denied,'shared353_executed':False,'population_calls':0,'model_calls':0}
 save(out/'summary.json',summary);save(out/'output-seal.json',{'files':[binding(f) for f in sorted(out.rglob('*')) if f.is_file()],'self_excluded':True});print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

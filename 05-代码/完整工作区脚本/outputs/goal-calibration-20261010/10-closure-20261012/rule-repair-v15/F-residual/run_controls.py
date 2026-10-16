"""Six fixed local controls only; not the shared353 or prior31F."""
from pathlib import Path
import copy, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
VERS=ROOT/'06-coding/rule-five-dimension-joint-root/versions'
BASE=VERS/'joint-v15-E-Ec-F-integrated-root'
CANDIDATE=VERS/'joint-v15f-requested-qualification-root'
NAMES=('evidence','source_packet','source_receipts','relations','dimensions')
ROUTING=ROOT/'10-closure-20261012/rule-repair-v14/E-source/routing_checks.py'
def read(p):return json.loads(p.read_text())
def binding(p):
 z=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(z),'sha256':hashlib.sha256(z).hexdigest()}
def save(p,d):
 with p.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def modules(p):
 result={}
 for n in NAMES:
  spec=importlib.util.spec_from_file_location(n,p/(n+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);result[n]=m
 return result

def main():
 out=HERE/'attempt01';out.mkdir(exist_ok=False);snapshot=out/'code-snapshot';snapshot.mkdir()
 prep=read(HERE/'preparation.json')
 for q in prep['parent_modules']:assert binding(Path(q['path']))==q
 for key in ('fixed_controls','controls_index'):assert binding(Path(prep[key]['path']))==prep[key]
 for n in NAMES:(snapshot/(n+'.py')).write_bytes((CANDIDATE/(n+'.py')).read_bytes())
 cases=read(HERE/'controls-index.json')['cases'];assert len(cases)==6
 prepared=[]
 for case in cases:
  if 'packet_binding' in case:
   q=case['packet_binding'];assert binding(Path(q['path']))==q;bundle=read(Path(q['path']))['source_bundle']
  else:bundle=case['synthetic_bundle']
  prepared.append((case,bundle))
 assert binding(ROUTING)['sha256']=='c673a06b41b13a43ef107d459783f49565231c38cd252b0d0bcae8483d353129'
 spec=importlib.util.spec_from_file_location('existing_routing_helper',ROUTING);routing=importlib.util.module_from_spec(spec);spec.loader.exec_module(routing)
 save(out/'pre-execution-seal.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'input':binding(HERE/'controls-index.json'),'base':[binding(BASE/(n+'.py')) for n in NAMES],'code':[binding(snapshot/(n+'.py')) for n in NAMES],'runner':binding(Path(__file__)),'routing':binding(ROUTING),'case_N':6,'shared353_executed':False,'previous31F_executed':False})
 old,new=modules(BASE),modules(snapshot);active=[False];denied=[]
 def audit(event,args):
  if active[0] and event=='open':denied.append(str(args[0]));raise RuntimeError('Classifier filesystem I/O denied')
 sys.addaudithook(audit)
 def run(loaded,bundle):
  unit=loaded['source_packet'].semantic_unit(bundle);before=copy.deepcopy(unit);active[0]=True
  try:
   view=loaded['relations'].RelationView(copy.deepcopy(unit));decisions=loaded['dimensions'].judge(view);loaded['evidence'].validate_decisions(unit,decisions);assert view.unit==before
  finally:active[0]=False
  proof=routing.check_actual_route(loaded,view,decisions,bundle)
  for q in view.material_requests:
   if q.get('producer')=='F_requested_qualification_dependency':
    assert q['path']=='F_requested_qualification_scope' and q['dimensions']==q['affected_dimensions']==['F'] and q['necessary_dependency'] is True
    assert q['stop_reason']=='F_requested_qualification_scope_unresolved' and q['stop_reason'] in proof['dependency_stop_reasons']
  return {'values':{d:x['value'] for d,x in decisions.items()},'decisions':decisions,'relations':view.traces(),'source_events':view.source_view_events,'material_requests':view.material_requests,'source_requests':view.source_requests,'private_I_requests':getattr(view,'v11_protected_data_requests',[]),'routing_proof':proof}
 results=[]
 for case,bundle in prepared:
  row={k:v for k,v in case.items() if k!='synthetic_bundle'}
  try:
   a,b=run(old,bundle),run(new,bundle)
   protected=all(a['decisions'][d]==b['decisions'][d] for d in ('S','E','Ec','I'))
   prefix=all(b[k][:len(a[k])]==a[k] for k in ('relations','source_requests','material_requests'))
   sources=all(a[k]==b[k] for k in ('source_events','private_I_requests'))
   additions=b['source_requests'][len(a['source_requests']):]
   typed=all(q.get('path')=='F_requested_qualification_scope' and q.get('producer')=='F_requested_qualification_dependency' and q.get('dimensions')==q.get('affected_dimensions')==['F'] for q in additions)
   relation_scope=all(q['kind']=='F_requested_qualification' and q['details']['affected_dimensions']==['F'] for q in b['relations'][len(a['relations']):])
   expected=all(b['values'][d]==v for d,v in case['expected'].items())
   row.update(baseline=a,candidate=b,expected_match=expected,protected_S_E_Ec_I_complete=protected,old_source_and_private_I_equal=sources,old_request_and_relation_prefix=prefix,new_F_request_only=typed,new_F_relation_only=relation_scope,changed_dimensions=[d for d in a['decisions'] if a['decisions'][d]!=b['decisions'][d]])
   row['pass']=all([expected,protected,sources,prefix,typed,relation_scope])
  except Exception as exc:row.update({'pass':False,'error':{'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}})
  results.append(row)
 save(out/'results.json',results)
 summary={'at_utc':datetime.now(timezone.utc).isoformat(),'case_N':6,'passed_N':sum(x['pass'] for x in results),'failed':[{'name':x['name'],'expected':x['expected'],'error':x.get('error'),'values':x.get('candidate',{}).get('values'),'checks':{k:v for k,v in x.items() if type(v)is bool}} for x in results if not x['pass']],'changes':[{'name':x['name'],'before':x.get('baseline',{}).get('values'),'after':x.get('candidate',{}).get('values'),'dimensions':x.get('changed_dimensions')} for x in results],'classifier_filesystem_attempts':denied,'shared353_executed':False,'previous31F_executed':False,'population_calls':0,'model_calls':0}
 save(out/'summary.json',summary);save(out/'output-seal.json',{'files':[binding(p) for p in sorted(out.rglob('*')) if p.is_file()],'self_excluded':True});print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

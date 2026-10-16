"""One bounded actual E-control round; reuse sealedv9 original189 baseline, retain all expectations."""
from pathlib import Path
import sys,json,hashlib,copy,importlib.util,datetime,traceback
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parents[2]
A=Path(__file__).resolve().parent
V=B/'06-coding/rule-five-dimension-joint-root/versions/joint-v9-e-outcome-candidate-sol'
O=V.parent/'joint-v9-generic-relationship-sol'
F=B/'08-audits/v9-generic-relationship-repair-design-sol/revision02-bidirectional-before-implementation'
NAMES=['evidence','source_packet','source_receipts','relations','dimensions']
def bind(p):
 p=p.resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,x):
 with p.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def mods(p):
 result={}
 for n in NAMES:
  spec=importlib.util.spec_from_file_location(n,p/(n+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);result[n]=m
 return result
out=A/'execution02';out.mkdir(exist_ok=False);snap=out/'code-snapshot';snap.mkdir()
for n in NAMES:(snap/(n+'.py')).write_bytes((V/(n+'.py')).read_bytes())
fixed=F/'real-controls-fixed-before-edit.json';syn=F/'synthetic-controls-fixed-before-edit.json'
real=json.loads(fixed.read_bytes())['cases'];synthetics=json.loads(syn.read_bytes())['cases']
extras=[O/x for x in ['supplemental-controls-before-attempt02.json','supplemental-controls-b-before-attempt02.json','supplemental-controls-before-attempt04.json','supplemental-controls-before-attempt06.json']]
for p in extras:synthetics+=json.loads(p.read_bytes())['cases']
original=real+synthetics;assert len(original)==189
basefile=O/'attempt08-final-governance-controls/results.json';base=json.loads(basefile.read_bytes())
assert len(base)==189 and [x['name'] for x in base]==[x['name'] for x in original]
for old,c in zip(base,original):assert old['expected']==c['expected'] and old['hard_assertion']==c['hard_assertion']
expectedbase=hashlib.sha256(basefile.read_bytes()).hexdigest();assert expectedbase=='2bd35483dc29fb09588cef2629256ccbd550c2afba7c3c93a0fa8d754f5c231a'
targetpath=A/'targeted24-fixed-before-second-edit.json';targeted=json.loads(targetpath.read_bytes())['cases'];assert len(targeted)==24
inputs=[];packet_bindings={}
for c in real:
 spec=c['packet_binding'];assert bind(Path(spec['path']))==spec
 packet=json.loads(Path(spec['path']).read_bytes());inputs.append(packet['source_bundle']);packet_bindings[spec['path']]=spec
save(out/'pre-execution-seal.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'controls':[bind(fixed),bind(syn)]+[bind(p) for p in extras]+[bind(targetpath)],'sealed_original189_v9_actual_baseline':bind(basefile),'code':[bind(snap/(n+'.py')) for n in NAMES],'base_code':[bind(O/(n+'.py')) for n in NAMES],'selected_original98_packet_bindings':list(packet_bindings.values()),'classifier_inputs_omit_expected_and_record_identity':True,'new_real_error_scan':False,'whole_or_partial_production_classifier':False,'classifier_control_round':2})
old=mods(O);new=mods(snap);active=[False];denied=[]
def audit(event,args):
 if active[0] and event=='open':denied.append(str(args[0]));raise RuntimeError('Classifier filesystem I/O denied')
sys.addaudithook(audit)
def run(m,u):
 before=copy.deepcopy(u);active[0]=True
 try:
  v=m['relations'].RelationView(copy.deepcopy(u));ds=m['dimensions'].judge(v);m['evidence'].validate_decisions(u,ds);assert v.unit==before
  return {'decisions':ds,'values':{d:ds[d]['value'] for d in ds},'relations':v.traces(),'material_requests':v.material_requests,'source_requests':v.source_requests,'source_events':v.source_view_events,'isolated_E_relations':getattr(v,'e_current_outcome_relations',[])}
 finally:active[0]=False
rows=[];cache={};candidate_evaluations=0;baseline_new_target_evaluations=0
for index,c in enumerate(original+targeted):
 row={k:v for k,v in c.items() if k!='semantic_input'};row['original189']=index<189
 try:
  if index<len(real):
   key=c['packet_binding']['sha256'];u=new['source_packet'].semantic_unit(inputs[index])
   if key not in cache:cache[key]=run(new,u);candidate_evaluations+=1
   z=cache[key]
  else:
   u=c['semantic_input'];z=run(new,u);candidate_evaluations+=1
  if index<189:a=base[index]['candidate'];baseline_origin='sealed_actual_v9_attempt08_candidate'
  else:a=run(old,u);baseline_new_target_evaluations+=1;baseline_origin='fresh_v9_targeted_controls_in_same_bounded_round'
  gate=new['dimensions']._e_outcome_gate(u['text'])
  equal=all(a['decisions'][d]==z['decisions'][d] for d in ('S','Ec','I','F'))
  row.update(actual={d:z['values'][d] for d in c['expected']},old_values=a['values'],new_values=z['values'],passed=all(z['values'][d]==v for d,v in c['expected'].items()),other_four_complete_decisions_equal=equal,raw_text_gate=gate,outside_gate_all_complete_decisions_equal=None if gate else a['decisions']==z['decisions'],legacy_relations_and_source_logs_equal=all(a[k]==z[k] for k in ('relations','material_requests','source_requests','source_events')),E_complete_decision_changed=a['decisions']['E']!=z['decisions']['E'],baseline_origin=baseline_origin,baseline=a,candidate=z)
 except Exception as e:row.update(passed=False,error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
 rows.append(row)
legacy=rows[:189];targeted_rows=rows[189:]
summary={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classifier_control_round_N':2,'original189_baseline_reused_without_reexecution':True,'candidate_semantic_evaluations_N':candidate_evaluations,'fresh_targeted_baseline_semantic_evaluations_N':baseline_new_target_evaluations,'control_row_N':len(rows),'original189':{'case_N':189,'hard_passed_N':sum(x['hard_assertion'] and x['passed'] for x in legacy),'hard_failed_N':sum(x['hard_assertion'] and not x['passed'] for x in legacy),'pending_N':sum(not x['hard_assertion'] for x in legacy),'passed_N':sum(x['passed'] for x in legacy)},'targeted24':{'case_N':22,'passed_N':sum(x['passed'] for x in targeted_rows),'failed_N':sum(not x['passed'] for x in targeted_rows),'negative_case_N':sum(x['expected']['E']==0 for x in targeted_rows),'negative_candidate_one_N':sum(x['expected']['E']==0 and x.get('new_values',{}).get('E')==1 for x in targeted_rows)},'all_failures':[{'name':x['name'],'expected':x['expected'],'actual':x.get('actual'),'error':x.get('error')} for x in rows if not x['passed']],'technical_error_N':sum('error' in x for x in rows),'other_four_complete_decision_mismatch':[x['name'] for x in rows if x.get('other_four_complete_decisions_equal') is False],'outside_gate_complete_decision_mismatch':[x['name'] for x in rows if x.get('outside_gate_all_complete_decisions_equal') is False],'legacy_relations_and_source_logs_mismatch':[x['name'] for x in rows if x.get('legacy_relations_and_source_logs_equal') is False],'original189_E_changes':[{'name':x['name'],'old_E':x['old_values']['E'],'new_E':x['new_values']['E']} for x in legacy if x.get('E_complete_decision_changed')],'filesystem_access_attempts':denied,'selected_unique_packet_N':len(cache),'all_expectations_preserved':True,'all_rows_and_failures_retained':True,'independent_accuracy_or_human_gold':False,'model_calls':0,'production_classifier_runs':0}
save(out/'results.json',rows);save(out/'summary.json',summary);save(out/'output-seal.json',{'files':[bind(p) for p in sorted(out.rglob('*')) if p.is_file()],'self_excluded':True})
print(json.dumps(summary,ensure_ascii=False,indent=2))

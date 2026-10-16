"""Post-run mechanical strict-receipt diagnostics; never reconstruct or retry classification."""
from pathlib import Path
import json,hashlib,collections,datetime
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'run4481-first'
def b(p):
 r=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
def rows(p):
 with p.open() as f:
  for line in f:yield json.loads(line)
def lines(p,a,z):
 t=p.read_text().splitlines();return {'binding':b(p),'line_range_1based':[a,z],'text':'\n'.join(t[a-1:z])}
scope=json.loads((ROOT/'frozen-scope.json').read_text());alg=json.loads(Path(scope['final_candidate_algorithm']['path']).read_text());relation=next(Path(x['path']) for x in alg['five_modules'] if Path(x['path']).name=='relations.py')
protocol=Path(scope['source_reading_protocol_code']['path']);driver=ROOT/'rule_driver.py'
term=next(i for i,l in enumerate(driver.read_text().splitlines(),1) if "source dependency stop has no concrete stopped rule dependency" in l)
source_append=next(i for i,l in enumerate(relation.read_text().splitlines(),1) if "self.source_requests.append" in l and "primary_literal_complete_operative_standard" in l)
items=[];types=collections.Counter();stops=collections.Counter()
for p in rows(OUT/'predictions.jsonl'):
 if not p.get('implementation_errors'):continue
 reqs=p.get('source_requests',[]);material=p.get('material_requests',[]);check=p.get('uniform_source_protocol_check') or {}
 diag=p.get('candidate_decisions_diagnostic_only')
 for e in p['implementation_errors']:types[e['type']+': '+e['message']]+=1
 for s in check.get('dependency_stop_reasons',[]):stops[s]+=1
 evaluated=[{'request_index_0based':i,'path':r.get('path'),'declared_dependency_status':r.get('dependency_status'),'declared_status':r.get('status'),'strict_legacy_status_default':r.get('status','unresolved'),'legacy_necessary_dependency_default':r.get('necessary_dependency',True),'legacy_rule_counts_it_unresolved':r.get('status','unresolved')!='resolved' and r.get('necessary_dependency',True),'stop_reason_default':r.get('stop_reason','missing_required_source'),'resolution_path':r.get('resolution_path'),'evidence':r.get('evidence',[]),'source_request_full':r} for i,r in enumerate(reqs)]
 items.append({'id':p['id'],'retained_labels':p.get('labels'),'retained_decisions':p.get('decisions'),'implementation_errors':p['implementation_errors'],'candidate_diagnostic_values_not_retained':{d:v['value'] for d,v in diag.items()} if isinstance(diag,dict) else None,'candidate_diagnostic_decisions_full_not_retained':diag,'strict_source_protocol_check':check,'source_requests_full':reqs,'material_requests_full':material,'legacy_request_field_evaluation':evaluated,'source_audit_primary_origin':p.get('primary_source_audit_origin'),'exception_audit':p.get('exception_source_audit'),'live_view_audit':p.get('live_view_source_audit'),'classification_retry_count':0,'labels_not_backfilled_from_diagnostic':True})
with (ROOT/'strict-ledger-failure-details.json').open('x') as f:json.dump({'identity':'first-v5-original-common4481-strict-ledger-failures','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'failure_record_N':len(items),'error_distribution':dict(types),'protocol_stop_reason_distribution':dict(stops),'code_paths':{'original_protocol_status_default':lines(protocol,55,62),'runner_strict_concrete_dependency_guard':lines(driver,term-7,term+7),'candidate_resolved_request_schema':lines(relation,source_append-2,source_append+2)},'interpretation':'The frozen candidate uses dependency_status; the unchanged legacy protocol checks status with unresolved default. Any diagnostic decision remains non-retained in this first strict-ledger run. Failures may include other types and are listed without relabeling.','candidate_modules_and_first_run_unchanged':True,'strict_failure_records':items},f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
print(json.dumps({'failure_record_N':len(items),'error_distribution':dict(types),'stop_distribution':dict(stops)},ensure_ascii=False))

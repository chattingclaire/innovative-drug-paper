"""Mechanical source identity, coverage, and version-difference summary. No classification."""
from pathlib import Path
import json, hashlib, datetime, collections, itertools, csv,sys
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'run4481-first'
BASE=ROOT.parent/'rule-full4481-v2-root/run4481-first'
DIMS=('S','E','Ec','I','F')
def read(p):return json.loads(p.read_text())
def rows(p):
 with p.open(encoding='utf8') as f:
  for line in f:
   if not line.strip():raise ValueError('blank persisted row: '+str(p))
   yield json.loads(line)
def b(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for part in iter(lambda:f.read(1048576),b''):h.update(part)
 return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def verify(x):
 got=b(Path(x['path']));assert all(got[k]==x[k] for k in ('path','bytes','sha256')),x['path']
def write(n,x):
 with (ROOT/n).open('x',encoding='utf8') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
execution=read(OUT/'execution.json');seal=read(OUT/'seal.json')
for x in seal['output_files']:verify(x)
for x in seal['implementation_files']+seal['control_inputs']:verify(x)
oldseal=read(BASE/'seal.json');verify(oldseal['prediction_binding'])
scope=read(ROOT/'frozen-scope.json');order=scope['approved_record_ids']
oldorder=[];neworder=[];same=[]
for old,new in itertools.zip_longest(rows(BASE/'input-deliveries.jsonl'),rows(OUT/'input-deliveries.jsonl')):
 assert old is not None and new is not None
 assert old['source_id']==new['source_id'] and old['source_bundle_sha256']==new['source_bundle_sha256'] and old['source_bundle_utf8_bytes']==new['source_bundle_utf8_bytes']
 assert new['same_common_JSONL_identity_verified'] is True and new['actual_input_kind']=='original_frozen_native_packet'
 oldorder.append(old['source_id']);neworder.append(new['source_id']);same.append({'source_id':new['source_id'],'source_bundle_sha256':new['source_bundle_sha256'],'original_packet_binding':new['actual_packet_binding']})
assert oldorder==neworder==order and len(order)==4481==len(set(order))
counts={d:dict(expected=4481,covered=0,zero=0,one=0,NULL=0,technical_failure=0) for d in DIMS}
oldcounts={d:dict(zero=0,one=0,NULL=0,technical_failure=0) for d in DIMS}
transitions={d:collections.Counter() for d in DIMS};changes=[];pending=[];fails=[];ids=[];changed_ids=set();null_ids=set();positive_known_with_unresolved=collections.Counter()
def state(p,d):
 if p.get('implementation_errors') or not isinstance(p.get('labels'),dict) or d not in p['labels']:return 'technical_failure'
 v=p['labels'][d];assert v is None or type(v) is int and v in (0,1)
 return 'NULL' if v is None else 'one' if v==1 else 'zero'
for old,new in itertools.zip_longest(rows(BASE/'predictions.jsonl'),rows(OUT/'predictions.jsonl')):
 assert old is not None and new is not None and old['id']==new['id']
 rid=new['id'];ids.append(rid)
 if new.get('implementation_errors'):fails.append({'id':rid,'errors':new['implementation_errors'],'candidate_decisions_diagnostic_only_retained':bool(new.get('candidate_decisions_diagnostic_only'))})
 for d in DIMS:
  pre,post=state(old,d),state(new,d);counts[d]['covered']+=1;counts[d][post]+=1;oldcounts[d][pre]+=1;transitions[d][pre+'->'+post]+=1
  if pre!=post:
   changes.append({'id':rid,'dimension':d,'baseline_state':pre,'final_v5_state':post,'baseline_value':old.get('labels',{}).get(d) if isinstance(old.get('labels'),dict) else None,'final_v5_value':new.get('labels',{}).get(d) if isinstance(new.get('labels'),dict) else None,'same_frozen_source_identity':True});changed_ids.add(rid)
  if post=='NULL':
   dec=new['decisions'][d];pending.append({'id':rid,'dimension':d,'value':None,'needed_material':dec.get('needed_material',[]),'decision_details':dec.get('details',{}),'source_requests':new.get('source_requests',[]),'source_dependency_stop_reasons':new.get('source_dependency_stop_reasons',[])});null_ids.add(rid)
  if post=='one' and new.get('material_requests'):positive_known_with_unresolved[d]+=1
assert ids==order
ledger=list(rows(OUT/'execution-ledger.jsonl'));assert [r['id'] for r in ledger]==order and [r['index_1based'] for r in ledger]==list(range(1,4482))
slots_count=0;slot_order=[]
for slot in rows(OUT/'all-dimension-slots.jsonl'):
 slots_count+=1;slot_order.append((slot['id'],slot['dimension']))
assert slot_order==[(rid,d) for rid in order for d in DIMS]
assert execution['actual_cohort_inference_runs']==1 and execution['actual_record_N']==4481 and execution['actual_dimension_N']==slots_count==22405
assert sum(c['technical_failure'] for c in counts.values())==execution['technical_failure_dimension_N']
assert sum(c['NULL'] for c in counts.values())==execution['lawful_null_N']
for name,data in [('changed-dimension-items.jsonl',changes),('pending-dimension-items.jsonl',pending),('technical-failure-records.jsonl',fails),('same-input-identity-comparison.jsonl',same)]:
 with (ROOT/name).open('x',encoding='utf8') as f:
  for row in data:f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
with (ROOT/'version-differences.csv').open('x',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['id','dimension','baseline_state','final_v5_state','baseline_value','final_v5_value','same_frozen_source_identity']);w.writeheader();w.writerows(changes)
summary={'identity':'final_sealed_v5_first_full_domain_execution_original_common_materials','status':execution['status'],'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_record_N':4481,'dimension_item_N':22405,'source_input_order_exactly_once':True,'same_baseline_original_source_bundle_identity_N':4481,'original_packets_actual_input':True,'new_neutral_material_adopted':False,'neutral_projection_GO':False,'actual_full_domain_inference_runs':1,'dimensions':counts,'baseline_dimensions':oldcounts,'version_transition_matrix':{d:dict(transitions[d]) for d in DIMS},'changed_dimension_item_N':len(changes),'changed_unique_record_N':len(changed_ids),'pending_dimension_item_N':len(pending),'pending_unique_record_N':len(null_ids),'technical_failure_record_N':len(fails),'known_positive_with_independent_unresolved_dependency_count_by_dimension':dict(positive_known_with_unresolved),'no_NULL_filled_zero':True,'version_difference_is_not_repeat_stability_or_formal_validity':True,'formal_validation_complete':False,'human_validation_complete':False,'main_LLM_labels_or_human_reference_read':False,'runtime_execution_binding':b(OUT/'execution.json'),'runtime_seal_binding':b(OUT/'seal.json'),'original_baseline_prediction_binding':b(BASE/'predictions.jsonl'),'original_baseline_seal_binding':b(BASE/'seal.json'),'final_v5_algorithm_binding':scope['final_candidate_algorithm'],'final_v5_pre_execution_seal':scope['final_candidate_pre_execution_seal'],'final_v5_delivery_seal':scope['final_candidate_delivery_seal']}
write('summary.json',summary)
write('mechanical-validation.json',{'all_source_order_unique_and_complete':True,'all_dimension_slots_order_unique_and_complete':True,'all4481_packet_common_JSONL_baseline_identities_match':True,'ledger_all4481_once':True,'runtime_outputs_and_code_and_scope_bindings_verified':True,'baseline_prediction_SHA_verified':True,'dimension_count_totals_match_runtime':True,'semantic_inference_by_summary_script':False,'main_LLM_label_read':False,'technical_failure_not_counted_as_NULL_or_zero':True})
print(json.dumps({'status':summary['status'],'dimensions':counts,'changed_dimension_N':len(changes),'changed_record_N':len(changed_ids),'NULL_N':len(pending),'technical_failure_record_N':len(fails)},ensure_ascii=False))

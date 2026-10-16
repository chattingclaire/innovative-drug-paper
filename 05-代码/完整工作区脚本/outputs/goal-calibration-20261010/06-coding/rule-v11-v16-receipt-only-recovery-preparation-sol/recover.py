"""Future receipt-only recovery. Original first decisions/events are immutable.

No semantic_unit, RelationView, judge, validate_decisions or model calls.
Only the original frozen receipt protocol executes after explicit ROOT adoption.
"""
import argparse,ast,copy,json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
from common import *
H=Path(__file__).resolve().parent;B=H.parents[1];TARGET='RECODE25-01402'
FIRST=B/'06-coding/rule-v11-I-v16-affected-v2-root/run-affected-first'
PREP=FIRST.parent
C=B/'08-audits/v11-v16-01402-consumption-binding-diagnostic-sol'

def preflight():
 contract=load(H/'recovery-contract.json');seal(H/'preparation-seal.json')
 for b in contract['frozen_input_bindings']:exact(b)
 s=seal(FIRST/'seal.json');e=load(FIRST/'execution.json')
 assert s['status']=='sealed_failed_execution_attempt' and e['actual_record_N']==44 and e['technical_failure_dimension_N']==5 and e['actual_cohort_inference_runs']==1
 preds=rows(FIRST/'predictions.jsonl');cons=rows(FIRST/'actual-source-consumption.jsonl');deliver=rows(FIRST/'input-deliveries.jsonl','source_id');ledger=rows(FIRST/'execution-ledger.jsonl');slots=rows(FIRST/'all-dimension-slots.jsonl',('id','dimension'));units=rows(FIRST/'effective-semantic-units.jsonl')
 ids=load(PREP/'frozen-scope.json')['approved_record_ids'];assert list(preds)==list(cons)==list(deliver)==list(ledger)==ids and len(slots)==220 and len(units)==43 and TARGET not in units
 for rid in ids:
  p=preds[rid][2]
  for d in DIMS:
   slot=slots[rid,d][2];dec=(p['candidate_decisions_diagnostic_only'] if rid==TARGET else p['decisions'])[d]
   assert slot['retained_rule_decision']==dec
   assert slot['technical_failure']==(rid==TARGET) and slot['rule_executed'] is True
  if rid!=TARGET:assert p['implementation_errors']==[] and p['labels']=={d:p['decisions'][d]['value'] for d in DIMS}
 p=preds[TARGET][2];c=cons[TARGET][2]
 assert p['labels'] is None and p['decisions'] is None and len(p['implementation_errors'])==1
 assert p['implementation_errors'][0]['message']=='actual consumption event source/view binding does not match inventory'
 for k in ('source_view_events','source_relation_traces','source_requests','material_requests'):
  assert p[k]==p['live_view_source_audit'][k]==c[k]==c['live_view_source_audit'][k] and p['primary_source_audit_origin'][k]=='live_view'
 assert len(p['source_view_events'])==29 and len(p['source_relation_traces'])==1 and p['uniform_source_reading_log'] is None and p['uniform_source_protocol_check'] is None
 assert not any(x['resource_id']=='BODY-'+TARGET for x in p['source_view_events'])
 assert p['source_requests']==p['material_requests']==[]
 bundles=[json.loads(raw) for raw in (FIRST/'delivered-complete-source-bundles.jsonl').read_bytes().splitlines()]
 assert [b['source_record']['id'] for b in bundles]==ids
 input_lines=Path(load(PREP/'frozen-scope.json')['source_packet']['path']).read_bytes().splitlines(keepends=True);assert len(input_lines)==44
 offset=0
 for ordinal,b in enumerate(bundles,1):
  rid=b['source_record']['id'];de=deliver[rid][2];raw=input_lines[ordinal-1]
  assert de['input_line_1based']==ordinal and de['input_line_sha256']==sha(raw) and de['input_start_utf8_byte']==offset and de['input_end_utf8_byte_exclusive']==offset+len(raw)
  assert de['source_bundle_sha256']==sha(cj(b).encode()) and de['source_bundle_utf8_bytes']==len(cj(b).encode())
  packet_binding=de['actual_packet_binding'];exact(packet_binding);packet=load(packet_binding['path'])
  assert packet['source_id']==rid and packet['source_bundle']==b
  offset+=len(raw)
 return contract,preds,cons,deliver,ledger,slots,units

def adopted_go(path,contract):
 go=load(path);assert bind(path)==contract['ROOT_causal_adoption'] and go['approval_actor']=='ROOT'
 for field,key in [('adopted_diagnostic_seal','C_diagnostic_seal'),('adopted_receipt_recovery_supplement','C_receipt_supplement'),('adopted_proposal','C_proposal')]:
  exact(go[field]);assert go[field]==contract[key]
 assert go['actual_first_run_seal']==bind(FIRST/'seal.json') and go['original_driver']==bind(PREP/'rule_driver.py')
 assert go['stored_view_events_N']==29 and go['BODY_stored'] is False and go['scope_review_stored'] is False and go['effective_unit14_stored'] is False and go['new_semantic_inference_authorized'] is False
 assert go['permitted_actions']==contract['ROOT_permitted_actions'] and go['forbidden_actions']==contract['ROOT_forbidden_actions']
 return dict(go,allow_exact_frozen_constructor_scope_review_causal_recovery_not_stored=True,allow_exact_historical_local_BODY_receipt_causal_recovery_not_stored=True)

def independent_inventory(bundle,evidence):
 # Original14 independently frozen projection from unchanged producer; no event-derived expected identity.
 old=copy.deepcopy(evidence['static_expected_inventory_projection']);assert old==evidence['static_resolved_inventory_projection'] and len(old)==14
 registry={x['resource_id']:x for x in old};added=[];proof=load(C/'necessary-five-literal-inventory-provenance.json')
 for frozen in proof['resources']:
  t=pointer(bundle,frozen['source_bundle_pointer']);assert t['source_resource_id']==frozen['source_resource_id'] and t['text']==frozen['text'] and t['text_sha256']==sha(t['text'].encode())==frozen['text_sha256']
  assert t['source_sha256']==frozen['source_sha256'] and t['source_version_id']==frozen['source_version_id'] and t['source_locator']==frozen['source_locator']
  loc=t['source_locator'];ss=loc['structured_snapshot'];html=loc['raw_html'];raw=Path(ss['absolute_path']).read_bytes();text=raw.decode('utf8');assert sha(raw)==ss['sha256']==t['source_sha256']
  if 'raw_JSON_string_literal_unicode_interval_half_open' in ss:
   a,b=ss['raw_JSON_string_literal_unicode_interval_half_open'];x,y=ss['raw_JSON_string_literal_utf8_byte_interval_half_open'];assert text[a:b].encode()==raw[x:y] and json.loads(text[a:b])==t['text']
  else:
   a,b=ss['raw_JSON_string_literal_header_unicode_interval_half_open'];x,y=ss['raw_JSON_string_literal_header_utf8_byte_interval_half_open'];assert text[a:b]==t['text'] and raw[x:y]==t['text'].encode()
  hr=Path(html['absolute_path']).read_bytes();assert sha(hr)==html['sha256'];ht=hr.decode('utf8');a,b=html['raw_unicode_interval_half_open'];x,y=html['raw_utf8_byte_interval_half_open'];assert ht[a:b].encode()==hr[x:y]
  if 'outer_html_sha256_utf8' in html:assert sha(hr[x:y])==html['outer_html_sha256_utf8']
  else:assert ht[a:b]==t['text']
  item={'resource_id':t['source_resource_id'],'source_sha256':t['source_sha256'],'available_views':{'text':t['text_sha256']},'locator':copy.deepcopy(loc),'projection_pointer':frozen['source_bundle_pointer']}
  if item['resource_id'] in registry:assert registry[item['resource_id']]==item,'Conflicting resource ID'
  else:registry[item['resource_id']]=item;added.append(item)
 assert len(added)==5 and list(registry.values())[:14]==old
 return old,list(registry.values()),added

def receipt_metadata(bundle,pred,scope,go):
 evidence=load(C/'exact01402-first-failure-evidence.json');assert evidence['actual_original_source_view_events']==pred['source_view_events'] and evidence['actual_source_relation_traces']==pred['source_relation_traces']
 old,inventory,added=independent_inventory(bundle,evidence);by_id={x['resource_id']:x for x in inventory}
 # Pure finite facade, unchanged original v12 prepare/check code. No coder import.
 facade=types.ModuleType('source_only_interface_v12')
 def lookup(rid,reader='rule',bundle=True):
  assert rid==TARGET and reader=='rule' and bundle;return copy.deepcopy(delivered)
 delivered=bundle;facade.lookup=lookup;facade.source_inventory=lambda b:copy.deepcopy(inventory);facade.cj=cj;facade.CANON_SHA=scope['complete_bundles_canonical_sha256'];facade.MANIFEST_SHA=scope['source_manifest_sha256'];sys.modules['source_only_interface_v12']=facade
 protocol_binding=scope['source_reading_protocol_code'];exact(protocol_binding);protocol=types.ModuleType('frozen_receipt_protocol');protocol.__file__=protocol_binding['path'];exec(compile(Path(protocol.__file__).read_bytes(),protocol.__file__,'exec'),protocol.__dict__)
 log=protocol.prepare(TARGET,FIRST.name,'rule')
 log['actual_full_source_bundle_sha256']=sha(cj(bundle).encode())
 log['receipt_recovery_material_identity']={'original_scope':bind(PREP/'frozen-scope.json'),'actual_packet_binding':load(C/'necessary-five-literal-inventory-provenance.json')['packet_binding'],'original_finite_v15_CANON_manifest_fields_preserved':True,'v16_target_bundle_explicitly_bound':True,'original_inventory':old,'added_inventory_entries':added,'inventory_repair_not_source_content_change':True}
 # Exact frozen constructor literal only, not a saved original review field or new judgment.
 alg=load(PREP/'algorithm-bindings.json');rel=next(x for x in alg['modules'] if Path(x['path']).name=='relations.py');exact(rel)
 tree=ast.parse(Path(rel['path']).read_text());assignments=[n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id=='self' and t.attr=='source_scope_review' for t in n.targets)]
 assert len(assignments)==1;review=ast.literal_eval(assignments[0].value)
 assert go['allow_exact_frozen_constructor_scope_review_causal_recovery_not_stored'] is True
 log['necessary_source_scope_review_status']=review['status'];log['necessary_source_scope_review_note']=review['source_evidence_note']
 body=by_id['BODY-'+TARGET]
 assert go['allow_exact_historical_local_BODY_receipt_causal_recovery_not_stored'] is True
 body_event={'resource_id':body['resource_id'],'view':'text','source_sha256':body['source_sha256'],'view_sha256':body['available_views']['text'],'locator_read':body['locator'],'event_kind':'current_text_matching_view','consumption_scope':'complete fixed current proposition, normalized matching and original offsets'}
 assert sha(bundle['source_record']['text'].encode())==body_event['view_sha256']
 # Retain stored group exactly. BODY is separately disclosed code-derived historical local action.
 events=[body_event]+copy.deepcopy(pred['source_view_events']);reads=[];seen=set()
 for i,event in enumerate(events):
  key=event['resource_id'],event['view']
  if key in seen:continue
  seen.add(key);resource=by_id.get(event['resource_id']);assert resource and event['source_sha256']==resource['source_sha256'] and event['view_sha256']==resource['available_views'].get(event['view'])
  assert event['view'] in ('text','geometry','document_bundle'),'Original pixel-read rejection preserved'
  reads.append(dict(receipt_id='READ-'+str(i),run_id=FIRST.name,record_id=TARGET,resource_id=event['resource_id'],source_sha256=event['source_sha256'],view=event['view'],view_sha256=event['view_sha256'],locator_read=event['locator_read'],delivery_status=event.get('delivery_status','complete'),read_attestation='recorded',reader='AI_rule_runtime',event_id=FIRST.name+':source-event:'+str(i),event_kind=event['event_kind'],consumption_scope=event['consumption_scope'],content_modalities=['text','structure','source_identity'] if event['view']=='document_bundle' else [event['view']],pixel_interpretation=False,recovery_origin='code_derived_historical_local_event_not_stored' if i==0 else 'receipt_derived_from_exact_stored_source_view_event',original_stored_view_event_index=None if i==0 else i-1,no_new_read_or_timestamp=True))
 log['read_receipts']=reads;by_key={(r['resource_id'],r['view']):r for r in reads};uses=[]
 for trace in pred['source_relation_traces']:
  for use in trace.get('used_source_views',[]):
   key=use['resource_id'],use['view'];assert key in by_key
   uses.append(dict(resource_id=key[0],view=key[1],use_status='used',read_receipt_id=by_key[key]['receipt_id'],use_scope=use['use_scope'],source_relation_kind=trace.get('relation_kind')))
 log['use_receipts']=uses;log['source_requests']=copy.deepcopy(pred['source_requests']);assert log['source_requests']==[] and log['reference_resolution']==[]
 log['receipt_recovery_provenance']={'stored_source_view_events':copy.deepcopy(pred['source_view_events']),'stored_event_N':29,'stored_events_unchanged':True,'code_derived_historical_BODY_event':body_event,'BODY_origin':'code_derived_historical_local_event_not_stored','scope_review_literal':review,'scope_review_origin':'frozen_literal_constructor_causal_recovery_not_stored','original_effective_unit_missing':True,'original_uniform_log_never_returned':True,'no_new_semantic_calls':True}
 check=protocol.check(log);assert check['errors']==[] and check['dependency_stop_reasons']==[] and check['source_read_requirements_recorded'] is True
 return log,check,old,inventory,added

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['preflight','recover'],required=True);parser.add_argument('--go');parser.add_argument('--output');args=parser.parse_args()
 contract,preds,cons,deliver,ledger,slots,units=preflight()
 if args.mode=='preflight':print(json.dumps({'status':'prepared_not_recovered','records':44,'actual_effective_units':43,'stored_target_events':29,'first_technical_failure_N':5,'judge_or_classifier_calls':0}));return
 assert args.go and args.output,'Actual recovery requires ROOT review/adoption and separate exclusive output'
 go=adopted_go(args.go,contract)
 out=Path(args.output).resolve();assert not out.exists() and out.parent==B/'06-coding'
 bundles=[json.loads(x) for x in (FIRST/'delivered-complete-source-bundles.jsonl').read_bytes().splitlines()];bundle=next(x for x in bundles if x['source_record']['id']==TARGET);p=preds[TARGET][2]
 log,check,old,extended,added=receipt_metadata(bundle,p,load(PREP/'frozen-scope.json'),go)
 # No files are created before all protocol/source proofs have passed.
 out.mkdir();recovery={'origin':'receipt_only_recovered_original_v11_v16_diagnostic','original_prediction_line_sha256':sha(preds[TARGET][1]),'original_failure':p['implementation_errors'],'original_first_execution_still_failed':True,'original_decisions_preserved_from_diagnostic':True,'semantic_adapter_RelationView_judge_calls_N':0,'new_read_events_N':0,'stored_source_view_events_N':29,'code_derived_unstored_historical_BODY_N':1,'scope_review_origin':'frozen_literal_constructor_causal_recovery_not_stored','effective_unit_missing_preserved':True,'ROOT_adoption':bind(args.go)}
 raw=preds[TARGET][1];fs=spans(raw);diagnostic=raw[slice(*fs['candidate_decisions_diagnostic_only'])];labels={d:p['candidate_decisions_diagnostic_only'][d]['value'] for d in DIMS}
 recovered=replace(raw,{'labels':cj(labels).encode(),'decisions':diagnostic,'implementation_errors':b'[]'}, {'receipt_recovery':recovery,'source_protocol_requirements_recorded':True,'source_dependency_stop_reasons':[]})
 assert json.loads(recovered)['decisions']==p['candidate_decisions_diagnostic_only'] and recovered[slice(*spans(recovered)['decisions'])]==diagnostic
 with (out/'predictions.jsonl').open('xb') as f:
  for rid,(_,raw,x) in preds.items():f.write(recovered if rid==TARGET else raw)
 with (out/'all-dimension-slots.jsonl').open('xb') as f:
  for (rid,d),(_,raw,x) in slots.items():
   if rid==TARGET:
    value=labels[d];updates={'status':cj('source_dependency_unresolved' if value is None else 'retained_rule_decision').encode(),'technical_failure':b'false','rules_null':b'true' if value is None else b'false','rule_value':cj(value).encode(),'record_implementation_errors':b'[]','comparison_eligible':b'true'};original_raw=raw;raw=replace(raw,updates,{'receipt_recovery':recovery});assert raw[slice(*spans(raw)['retained_rule_decision'])]==original_raw[slice(*spans(original_raw)['retained_rule_decision'])]
   f.write(raw)
 with (out/'actual-source-consumption.jsonl').open('xb') as f:
  for rid,(_,raw,x) in cons.items():f.write(replace(raw,{}, {'receipt_only_recovered_uniform_log':log,'receipt_only_recovered_protocol_check':check,'receipt_recovery':recovery}) if rid==TARGET else raw)
 for name in ('effective-semantic-units.jsonl','input-deliveries.jsonl','delivered-complete-source-bundles.jsonl','execution-ledger.jsonl'):
  with (out/name).open('xb') as f:f.write((FIRST/name).read_bytes())
 save(out/'receipt-recovery-ledger.json',{'record_id':TARGET,'original_inventory':old,'extended_inventory':extended,'added_inventory_entries':added,'log':log,'check':check,'provenance':recovery,'43_prediction_and215_slot_rawbytes_preserved':True,'44_delivery_and_source_bundle_rawbytes_preserved':True,'43_effective_units_preserved_no14_added':True,'original_candidate_decisions_raw_token_bytes_preserved':True})
 origin=[]
 for rid,(_,raw,x) in preds.items():origin.append({'id':rid,'actual_inference_algorithm':'joint-v11-protected-data-role-sol','actual_run_directory':str(FIRST),'actual_original_first_prediction_line_sha256':sha(raw),'actual_output_origin':'receipt_only_recovered_original_diagnostic' if rid==TARGET else 'original_first_valid_prediction','derived_prediction_line_sha256':sha(recovered if rid==TARGET else raw),'source_consumption_log':str(out/'actual-source-consumption.jsonl'),'source_consumption_record_key':rid,'new_semantic_execution':False,'original_first_failure_preserved':rid==TARGET,'missing_effective_unit':rid==TARGET})
 with (out/'execution-origin-lineage.jsonl').open('x') as f:
  for x in origin:f.write(json.dumps(x,ensure_ascii=False)+'\n')
 status={'status':'completed_receipt_only_recovered_original_v11_v16_delta_composite','at_utc':now(),'actual_record_N':44,'actual_dimension_N':220,'retained_decision_N':220,'technical_failure_dimension_N':0,'lawful_null_N':load(FIRST/'execution.json')['lawful_null_N']+sum(v is None for v in labels.values()),'original_first_technical_failure_dimension_N':5,'original_first_status':'failed_execution_attempt','original_actual_inference_runs':1,'new_actual_inference_runs':0,'semantic_adapter_RelationView_judge_calls_N':0,'original_effective_unit_N':43,'missing_effective_unit_ids':[TARGET],'receipt_recovered_record_N':1,'receipt_recovered_dimension_N':5,'original_valid_record_N':43,'first_run_preserved_not_overwritten':True,'no_reference_read':True,'formal_validation_complete':False,'human_validation_complete':False,'preparation':bind(H/'preparation-seal.json'),'ROOT_adoption':bind(args.go),'original_first_seal':bind(FIRST/'seal.json')}
 save(out/'execution.json',status);save(out/'seal.json',{'status':'sealed_completed_receipt_only_recovered_original_v11_v16_delta_composite','output_files':[bind(p) for p in sorted(out.iterdir()) if p.is_file()],'ancestor_seals':[bind(FIRST/'seal.json'),bind(H/'preparation-seal.json'),contract['C_diagnostic_seal'],contract['C_receipt_supplement_seal']],'semantic_adapter_RelationView_judge_calls_N':0,'first_run_preserved_not_overwritten':True,'formal_validation_complete':False})
 print(json.dumps(status,ensure_ascii=False))
if __name__=='__main__':main()

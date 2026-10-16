"""Future explicit v11/v16 receipt-recovered44 + parent4437 mechanical merge."""
import argparse,collections,json
from pathlib import Path
from common import *
H=Path(__file__).resolve().parent;B=H.parents[1]
P=B/'06-coding/rule-full4481-v10-if-e-delta-merged-root'
ORIGINAL=B/'06-coding/rule-v11-I-v16-affected-v2-root';TARGET='RECODE25-01402'
def main():
 p=argparse.ArgumentParser();p.add_argument('--delta',required=True);p.add_argument('--output',required=True);x=p.parse_args();delta=Path(x.delta).resolve();out=Path(x.output).resolve();assert not out.exists() and out.parent==B/'06-coding'
 seal(H/'preparation-seal.json');contract=load(H/'recovery-contract.json')
 for b in contract['frozen_input_bindings']:exact(b)
 seal(P/'seal.json');ds=seal(delta/'seal.json');e=load(delta/'execution.json');scope=load(ORIGINAL/'frozen-scope.json');original=load(ORIGINAL/'run-affected-first/execution.json')
 assert ds['status']=='sealed_completed_receipt_only_recovered_original_v11_v16_delta_composite' and e['status']=='completed_receipt_only_recovered_original_v11_v16_delta_composite'
 assert e['actual_record_N']==44 and e['actual_dimension_N']==e['retained_decision_N']==220 and e['technical_failure_dimension_N']==0
 assert e['original_first_technical_failure_dimension_N']==5 and e['original_first_status']=='failed_execution_attempt' and e['new_actual_inference_runs']==e['semantic_adapter_RelationView_judge_calls_N']==0 and e['original_actual_inference_runs']==1
 assert e['missing_effective_unit_ids']==[TARGET] and e['original_effective_unit_N']==43
 assert e['original_first_seal']==bind(ORIGINAL/'run-affected-first/seal.json') and e['preparation']==bind(H/'preparation-seal.json')
 assert e['ROOT_adoption']==contract['ROOT_causal_adoption'];exact(e['ROOT_adoption'])
 recovered_ledger=load(delta/'receipt-recovery-ledger.json')
 assert recovered_ledger['check']['errors']==[] and recovered_ledger['check']['dependency_stop_reasons']==[] and recovered_ledger['check']['source_read_requirements_recorded'] is True
 assert recovered_ledger['log']['receipt_recovery_provenance']['stored_event_N']==29 and recovered_ledger['log']['receipt_recovery_provenance']['original_effective_unit_missing'] is True
 for name in ('effective-semantic-units.jsonl','input-deliveries.jsonl','delivered-complete-source-bundles.jsonl','execution-ledger.jsonl'):
  assert (delta/name).read_bytes()==(ORIGINAL/'run-affected-first'/name).read_bytes(),name
 adoption=load(ORIGINAL/'ROOT-pre-inference-adoption-sidecar.json');assert adoption['at_utc']<original['started_at_utc']
 material_lineage=load(ORIGINAL/'original-input-lineage-sidecar.json');algorithm=load(ORIGINAL/'algorithm-bindings.json');material_delta=algorithm['material_delta_bindings']
 assert set(material_delta)=={'seal','correspondence','packet_bindings','byteproof'}
 for b in material_delta.values():exact(b)
 material_proof=load(material_delta['byteproof']['path'])
 assert material_lineage['source_common_v15']==material_proof['old_common'] and material_lineage['source_common_v16']==material_proof['new_common']
 for key in ('source_common_v15','source_common_v16'):exact(material_lineage[key])
 old=rows(P/'predictions.jsonl');new=rows(delta/'predictions.jsonl');oldslots=rows(P/'all-dimension-slots.jsonl',('id','dimension'));newslots=rows(delta/'all-dimension-slots.jsonl',('id','dimension'));origins=rows(P/'execution-origin-lineage.jsonl');neworigins=rows(delta/'execution-origin-lineage.jsonl');first=rows(ORIGINAL/'run-affected-first/predictions.jsonl');firstslots=rows(ORIGINAL/'run-affected-first/all-dimension-slots.jsonl',('id','dimension'))
 assert len(old)==len(origins)==4481 and len(oldslots)==22405 and list(new)==scope['approved_record_ids'] and len(new)==44 and len(newslots)==220
 assert set(new)<=set(old) and list(neworigins)==list(new)
 for rid,(_,raw,row) in new.items():
  assert row['implementation_errors']==[] and set(row['labels'])==set(row['decisions'])==set(DIMS)
  if rid!=TARGET:
   assert raw==first[rid][1]
   for d in DIMS:assert newslots[rid,d][1]==firstslots[rid,d][1]
  else:
   assert row['decisions']==first[rid][2]['candidate_decisions_diagnostic_only']
   sf=spans(raw);ff=spans(first[rid][1]);assert raw[slice(*sf['decisions'])]==first[rid][1][slice(*ff['candidate_decisions_diagnostic_only'])]
  for d in DIMS:
   assert row['labels'][d]==row['decisions'][d]['value'] and (row['labels'][d] is None or type(row['labels'][d]) is int and row['labels'][d] in (0,1))
   assert newslots[rid,d][2]['rule_value']==row['labels'][d] and newslots[rid,d][2]['technical_failure'] is False and newslots[rid,d][2]['retained_rule_decision']==row['decisions'][d]
   if d in scope['immutable_dimensions']:
    assert row['decisions'][d]==old[rid][2]['decisions'][d],(rid,d)
    a,b=spans(raw)['decisions'];new_dec=raw[a:b];a,b=spans(old[rid][1])['decisions'];old_dec=old[rid][1][a:b]
    assert new_dec[slice(*spans(new_dec)[d])]==old_dec[slice(*spans(old_dec)[d])],('immutable decision bytes',rid,d)
 out.mkdir();lineage=[];counts={d:collections.Counter() for d in DIMS};algorithms=collections.Counter();changes=[]
 with (out/'predictions.jsonl').open('xb') as pf,(out/'all-dimension-slots.jsonl').open('xb') as sf:
  for ordinal,(rid,(_,parentraw,parentrow)) in enumerate(old.items(),1):
   selected=rid in new;_,raw,row=(new if selected else old)[rid];pf.write(raw)
   prior=origins[rid][2];assert prior['corpus_ordinal_1based']==ordinal and prior['actual_prediction_line_sha256']==sha(parentraw) and prior['prediction_line_bytes']==len(parentraw)
   origin=dict(prior)
   if selected:
    origin.update(neworigins[rid][2]);origin['source_consumption_log']=str(delta/'actual-source-consumption.jsonl');origin['source_consumption_record_key']=rid
    origin['original_first_prediction_file']=str(ORIGINAL/'run-affected-first/predictions.jsonl')
    origin['material_lineage']='same-version v16 article6 addendum' if rid==TARGET else 'unchanged original v15 packet, actual v11 inference'
   origin.update(corpus_ordinal_1based=ordinal,id=rid,actual_prediction_line_sha256=sha(raw),prediction_line_bytes=len(raw),unchanged_actual_record_bytes_retained=(rid!=TARGET),candidate_compatibility_basis='receipt_only_recovered_original_v11_v16_diagnostic' if rid==TARGET else 'actual_original_v11_first_valid' if selected else 'unaffected_inherited_v10_compatible_parent',inherited_parent_origin_binding=None if selected else {'path':str(P/'execution-origin-lineage.jsonl'),'record_key':rid,'line_sha256':sha(origins[rid][1])})
   lineage.append(origin);algorithms[origin['actual_inference_algorithm']]+=1
   for d in DIMS:
    _,sraw,slot=(newslots if selected else oldslots)[rid,d];assert slot['retained_rule_decision']==row['decisions'][d] and slot['rule_value']==row['labels'][d] and not slot['technical_failure'];sf.write(sraw)
    counts[d]['positive_N' if row['labels'][d]==1 else 'negative_N' if row['labels'][d]==0 else 'lawful_null_N']+=1
    if selected and row['labels'][d]!=parentrow['labels'][d]:changes.append({'id':rid,'dimension':d,'parent_value':parentrow['labels'][d],'actual_delta_value':row['labels'][d],'origin':origin['actual_output_origin']})
 with (out/'execution-origin-lineage.jsonl').open('x') as f:
  for row in lineage:f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
 save(out/'material-receipt-compatible-changes.json',{'label_changes':changes,'immutable_dimensions':scope['immutable_dimensions'],'immutable_complete_decisions_unchanged':True,'material_changed_record_ids':[TARGET],'new_actual_semantic_runs':0,'14_decisions_from_original_validated_diagnostic_not_new_judge':True})
 status={'at_utc':now(),'status':'complete_v11_v16_receipt_compatible_composite_with_explicit_execution_origins','actual_record_N':4481,'actual_dimension_N':22405,'technical_failure_dimension_N':0,'lawful_null_N':sum(c['lawful_null_N'] for c in counts.values()),'counts':{d:{k:c[k] for k in ('positive_N','negative_N','lawful_null_N')} for d,c in counts.items()},'actual_execution_algorithm_record_N':dict(algorithms),'original_v11_actual_cohort_record_N':44,'original_v11_first_valid_record_N':43,'receipt_recovered_original_v11_diagnostic_record_N':1,'inherited_compatible_parent_record_N':4437,'original_v11_first_status':'failed_execution_attempt','original_v11_first_technical_failure_dimension_N':5,'original_v11_effective_unit_N':43,'missing_auxiliary_effective_unit_ids':[TARGET],'all4481_actually_inferred_under_v11':False,'new_inference_executed_by_merge':False,'label_change_N':len(changes),'new_semantic_execution_N':0,'material_changed_record_ids':[TARGET],'parent_seal':bind(P/'seal.json'),'delta_seal':bind(delta/'seal.json'),'ROOT_receipt_recovery_adoption':e['ROOT_adoption'],'original_material_input_lineage':bind(ORIGINAL/'original-input-lineage-sidecar.json'),'merger':bind(__file__),'formal_validation_complete':False,'human_validation_complete':False}
 status.update(source_common_v15=material_lineage['source_common_v15'],source_common_v16=material_lineage['source_common_v16'],material_delta_bindings=material_delta,impact_closure_plan=bind(ORIGINAL/'impact-closure-plan.json'),adoption=bind(ORIGINAL/'ROOT-pre-inference-adoption-sidecar.json'),original_input_lineage=bind(ORIGINAL/'original-input-lineage-sidecar.json'),candidate_algorithm_version=algorithm['algorithm_version'],allowed_mutable_dimensions=scope['allowed_mutable_dimensions'],immutable_dimensions=scope['immutable_dimensions'],immutable_complete_decision_bytes_all_identical=True,prediction_binding=bind(out/'predictions.jsonl'),label_slots_binding=bind(out/'all-dimension-slots.jsonl'),predictions_path=str(out/'predictions.jsonl'),label_slots_path=str(out/'all-dimension-slots.jsonl'),unresolved_technical_dimension_N=0,paper_writing_gate_open=False)
 save(out/'composite-status.json',status);save(out/'seal.json',{'status':status['status'],'files':[bind(p) for p in sorted(out.iterdir()) if p.is_file()],'ancestor_seals':[bind(P/'seal.json'),bind(delta/'seal.json'),bind(H/'preparation-seal.json')],'self_excluded':True,'new_semantic_execution_N':0,'formal_validation_complete':False});print(json.dumps(status,ensure_ascii=False))
if __name__=='__main__':main()

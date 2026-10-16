"""Static current-text nomination only; no classifier imports or output labels."""
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode=True

def bind(p):
 p=Path(p).resolve();raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def exact(b):
 assert bind(b['path'])=={k:b[k] for k in ('path','bytes','sha256')};return Path(b['path'])
def load(p):return json.loads(Path(p).read_bytes())

def main():
 p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 out=Path(a.output);assert not out.exists()
 c=load(a.contract);approved=c['manual_static_audit']
 assert approved['approved'] is True and approved['approval_actor']=='ROOT'
 assert c['allowed_mutable_dimensions']==['E','I','F']
 for k in ('record_local_only','new_relation_not_consumed_by_old_units','only_allowed_dimension_decision_or_explicit_request_mutations','same_packets_adapter_evidence_wrapper','mixed_baseline_equivalence_verified'):assert approved[k] is True
 for b in approved['proof_artifact_bindings']:exact(b)
 assert c['selector_binding']==bind(__file__)
 for b in c['candidate_modules']:exact(b)
 manifest=load(exact(c['manifest_binding']))
 assert manifest['record_N']==4481 and manifest['approved_record_ids']==[q['id'] for q in manifest['records']]
 assert manifest['classifier_executed'] is False
 for key in ('parent_frozen_scope','parent_packet_bindings','source_input'):exact(manifest[key])
 scope=load(manifest['parent_frozen_scope']['path']);plan=load(manifest['parent_packet_bindings']['path'])
 assert scope['approved_record_ids']==plan['ordered_source_ids']==manifest['approved_record_ids']
 assert plan['packet_N']==4481 and scope['expected_dimension_N']==22405
 assert [q['packet_binding'] for q in manifest['records']]==[{k:b[k] for k in ('path','bytes','sha256')} for b in plan['packets']]
 # Baseline parsing establishes completeness only. No label is used to nominate.
 parent=[json.loads(q) for q in exact(c['baseline_prediction_binding']).read_bytes().splitlines()]
 assert [q['id'] for q in parent]==manifest['approved_record_ids']
 assert all(not q['implementation_errors'] and set(q['decisions'])=={'S','E','Ec','I','F'} for q in parent)
 exact(c['baseline_seal_binding']);gatepath=exact(c['static_gate_binding'])
 spec=importlib.util.spec_from_file_location('pure_combined_gate',gatepath);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 selected=[];excluded=[]
 for row in manifest['records']:
  packet=load(exact(row['packet_binding']));assert packet['source_id']==row['id'] and packet['output_id']==row['output_id']
  source=packet['source_bundle']['source_record'];assert source['id']==row['id']
  matched=m.gate(source['text'])
  result={'id':row['id'],'packet_binding':row['packet_binding'],'gate_matched':bool(matched),
          'reasons':['pure_current_IF_or_E_entry'] if matched else [],
          'recompute_scope':'whole record, every existing/new unit and complete evidence chain'}
  (selected if matched else excluded).append(result)
 result={'status':'static_selection_only_no_classifier_execution','record_N':4481,'selected_N':len(selected),'reusable_N':len(excluded),
         'affected_records':selected,'excluded_records':excluded,'selected_record_ids':[q['id'] for q in selected],
         'reusable_record_ids':[q['id'] for q in excluded],'full_fallback_reasons':[],
         'contract_binding':bind(a.contract),'manifest_binding':c['manifest_binding'],
         'baseline_prediction_binding':c['baseline_prediction_binding'],'selector_binding':bind(__file__),
         'gate_source_binding':c['static_gate_binding'],'approved_record_ids':manifest['approved_record_ids'],
         'selection_never_filters_old_zero_one_or_null':True,'classifier_executions':0}
 with out.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({k:result[k] for k in ('record_N','selected_N','reusable_N','classifier_executions')}))
if __name__=='__main__':main()

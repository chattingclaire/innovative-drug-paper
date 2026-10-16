"""Independent mechanical audit of the completed v38 run against v37.2 only.

Never runs a classifier/model. Reserved predictions are aggregated only;
the sole per-unit exception is already-exposed RECODE25-01361.  No human
references, agreement scores or source documents are opened for semantics.
"""
from pathlib import Path
from datetime import datetime,timezone
import collections,hashlib,json,re,unicodedata

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/coding-revision-20261008-r4'
OUT=BASE/'rules-v38-shadow-independent-comparison'
OLD=BASE/'rules-v37.2-shadow-full-v14/all_predictions_material_v14_shadow.jsonl'
NEW=BASE/'rules-v38-shadow-full-v14/all_predictions_material_v14_shadow.jsonl'
INPUT=ROOT/'outputs/coding-revision-20261007-r3/rule_inputs_shared_v14.jsonl'
EXCLUSION=BASE/'rules-v37.2-development/future_human_development_exclusion_metadata_frozen.json'
FREEZE=BASE/'rules-v38-development/candidate_freeze.json'
DIMS=('S','E','Ec','I','F')
EXCEPTION='RECODE25-01361'
MARK='[保留家族文本已机械遮蔽]'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(t):return hashlib.sha256(t.encode()).hexdigest()
def write(n,x):
 p=OUT/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');return p
def jl(p):
 rows=[json.loads(s) for s in p.read_text().splitlines() if s.strip()]
 data={r['id']:r for r in rows}
 assert len(data)==len(rows)==4924
 return data
def norm_with_offsets(t):
 chars=[];offsets=[]
 for i,c in enumerate(t):
  for n in unicodedata.normalize('NFKC',c):
   if n.isalnum():chars.append(n);offsets.append(i)
 return ''.join(chars),offsets
def norm(t):return norm_with_offsets(t)[0]
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def main():
 assert NEW.exists() and NEW.with_suffix('.run.json').exists(),'Wait for complete root-owned run; do not rerun here.'
 assert not OUT.exists(),'Never overwrite this independent audit.'
 oldrun=json.loads(OLD.with_suffix('.run.json').read_text());newrun=json.loads(NEW.with_suffix('.run.json').read_text())
 assert oldrun['version']=='v37.2-complete-scientific-and-price-objects-development'
 assert newrun['version']=='v38-institution-routine-drug-supply-membership-development'
 assert oldrun['n']==newrun['n']==4924 and oldrun['pending_n']==newrun['pending_n']==0
 assert oldrun['input_sha256']==newrun['input_sha256']==sha(INPUT)
 assert oldrun['prediction_sha256']==sha(OLD) and newrun['prediction_sha256']==sha(NEW)
 assert newrun['candidate_freeze_sha256']==sha(FREEZE)
 assert not oldrun['reference_labels_loaded'] and not newrun['reference_labels_loaded']
 assert oldrun['component_settings']==newrun['component_settings']=={'legacy_model':False,'source_adapter':True,'substantive_rules':True}
 freeze=json.loads(FREEZE.read_text())
 assert all(sha(p)==h for p,h in freeze['production_code_sha256'].items())
 assert all(sha(p)==h for p,h in newrun['runtime_code_sha256'].items())
 assert all(freeze['production_code_sha256'].get(p)==h for p,h in newrun['runtime_code_sha256'].items())
 assert oldrun['actual_source_and_candidate_sha256']==newrun['actual_source_and_candidate_sha256']
 assert all(sha(p)==h for p,h in newrun['actual_source_and_candidate_sha256'].items())
 old,new,inputs=jl(OLD),jl(NEW),jl(INPUT)
 assert old.keys()==new.keys()==inputs.keys()
 reserved=set(json.loads(EXCLUSION.read_text())['all_registered_members_of_reserved_families_unit_ids'])
 assert len(reserved)==267 and reserved<=inputs.keys() and EXCEPTION in reserved
 # The texts below are machine filter material only, never printed or
 # individually copied into the audit (except the disclosed exception).
 reserved_texts=sorted({inputs[k]['input']['unit_text'] for k in reserved},key=len,reverse=True)
 reserved_norms=sorted({norm(t) for t in reserved_texts if norm(t)},key=len,reverse=True)
 context24={n[i:i+24] for n in reserved_norms for i in range(max(0,len(n)-23))}
 redactions=collections.Counter()
 def context_path(path):return any(s in path for s in ('context','heading','dependency','dependencies','adaptation','review_flags'))
 def redact(value,path=''):
  if isinstance(value,dict):return {k:redact(v,path+'.'+k) for k,v in value.items()}
  if isinstance(value,list):return [redact(v,path+'[]') for v in value]
  if not isinstance(value,str):return value
  for t in reserved_texts:
   if t and t in value:
    redactions['exact_reserved_unit_occurrences']+=value.count(t);value=value.replace(t,MARK)
  n,offsets=norm_with_offsets(value);spans=[]
  for t in reserved_norms:
   start=n.find(t)
   while start>=0:
    spans.append((offsets[start],offsets[start+len(t)-1]+1));start=n.find(t,start+len(t))
  if spans:
   merged=[]
   for a,b in sorted(spans):
    if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
    else:merged.append((a,b))
   for a,b in reversed(merged):value=value[:a]+MARK+value[b:]
   redactions['normalized_reserved_unit_spans']+=len(merged)
  if context_path(path):
   n=norm(value)
   if any(n[i:i+24] in context24 for i in range(max(0,len(n)-23))):
    redactions['context_strings_conservatively_omitted_for_24_character_overlap']+=1
    value=MARK
  return value
 def strings(value,path=''):
  if isinstance(value,str):yield path,value
  elif isinstance(value,dict):
   for k,v in value.items():yield from strings(v,path+'.'+k)
  elif isinstance(value,list):
   for v in value:yield from strings(v,path+'[]')
 checks=collections.Counter();per_group=collections.defaultdict(collections.Counter)
 changed_nonreserved=[];projection=[];all_field_changes=collections.Counter();subtype_changes=collections.Counter()
 direction=collections.defaultdict(collections.Counter);evidence_only=collections.Counter();nonversion_changed=collections.Counter()
 subtype_fields=('fairness_subtypes','innovation_subtypes','safety_subtypes','safety_quality_basis','innovation_subtype_status','innovation_unclassified_evidence')
 for key in sorted(inputs):
  unit=inputs[key]['input'];text=unit['unit_text'];before=old[key]['prediction'];after=new[key]['prediction']
  group='reserved267_aggregate_only' if key in reserved else 'nonreserved'
  assert old[key]['original_id']==new[key]['original_id']==inputs[key]['original_id']
  for stage,pred in [('v37.2',before),('v38',after)]:
   assert pred['unit_text_sha256']==digest(text)
   assert pred['judgement_status']=='rule_prediction'
   assert set(pred['labels'])==set(DIMS)
   assert all(type(pred['labels'][d]) is int and pred['labels'][d] in (0,1) for d in DIMS)
   assert pred['labels']=={d:int(any(e['dimension']==d for e in pred['evidence'])) for d in DIMS}
   for e in pred['evidence']:
    assert e['dimension'] in DIMS and type(e['start']) is int and type(e['end']) is int
    assert 0<=e['start']<e['end']<=len(text) and text[e['start']:e['end']]==e['text']
    checks[stage+'_literal_evidence_spans']+=1
   for s in pred.get('suppressions',[]):
    if all(k in s for k in ('start','end','text')):
     assert type(s['start']) is int and type(s['end']) is int
     assert 0<=s['start']<s['end']<=len(text) and text[s['start']:s['end']]==s['text']
     checks[stage+'_literal_suppression_spans']+=1
   for dim,field in [('F','fairness_subtypes'),('I','innovation_subtypes')]:
    assert pred[field]==sorted({e['subtype'] for e in pred['evidence'] if e['dimension']==dim and e.get('subtype')})
   ss=sorted({e.get('safety_basis','quality_safety' if e['rule']=='S07' else 'other_safety') for e in pred['evidence'] if e['dimension']=='S'})
   assert pred['safety_subtypes']==ss
   assert pred['safety_quality_basis']==('quality_only' if ss==['quality_safety'] else 'quality_and_other' if 'quality_safety' in ss else 'no_quality_basis')
   unclassified=[e for e in pred['evidence'] if e['dimension']=='I' and not e.get('subtype')]
   assert pred['innovation_unclassified_evidence']==unclassified
   assert pred['innovation_subtype_status']==('needs_review' if unclassified else 'complete' if pred['labels']['I'] else 'not_applicable')
   checks[stage+'_five_labels_input_hash_and_subtypes_validated']+=1
  labeldims=[d for d in DIMS if before['labels'][d]!=after['labels'][d]]
  subfields=[f for f in subtype_fields if before.get(f)!=after.get(f)]
  changedfields=[f for f in sorted(before.keys()|after.keys()) if f!='version' and before.get(f)!=after.get(f)]
  if not changedfields:continue
  nonversion_changed[group]+=1
  per_group[group]['any_nonversion_changed_units']+=1
  per_group[group]['label_changed_units']+=bool(labeldims)
  per_group[group]['label_changed_cells']+=len(labeldims)
  per_group[group]['subtype_changed_units']+=bool(subfields)
  per_group[group]['evidence_changed_units']+=before['evidence']!=after['evidence']
  evidence_only[group]+=bool(not labeldims and before['evidence']!=after['evidence'])
  for field in changedfields:all_field_changes[(group,field)]+=1
  for field in subfields:subtype_changes[(group,field)]+=1
  for d in labeldims:direction[group][f"{d}:{before['labels'][d]}->{after['labels'][d]}"]+=1
  if key in reserved:continue
  public_meta={'id':key,'changed_label_dimensions':labeldims,'changed_subtype_fields':subfields,'changed_nonversion_fields':changedfields,'labels_before':before['labels'],'labels_after':after['labels']}
  changed_nonreserved.append(public_meta)
  primary=unit.get('unit_source') or unit.get('source')
  primary_sha=unit.get('unit_source_sha256') if unit.get('unit_source') else unit.get('source_sha256')
  assert primary and primary_sha==sha(primary)
  assert newrun['actual_source_and_candidate_sha256'][str(Path(primary).resolve())]==primary_sha
  row={**public_meta,'unit_text':text,'unit_text_sha256':digest(text),'source_display':primary,'source_display_sha256':primary_sha,'source_display_field':'unit_source' if unit.get('unit_source') else 'source','legacy_source':unit.get('source'),'legacy_source_differs':unit.get('source')!=primary,'pages':unit.get('pages'),
       'subtypes_before':{f:before.get(f) for f in subtype_fields},'subtypes_after':{f:after.get(f) for f in subtype_fields},
       'evidence_before':before['evidence'],'evidence_after':after['evidence'],'suppressions_before':before.get('suppressions'),'suppressions_after':after.get('suppressions'),
       'paragraph_context':unit.get('paragraph_context'),'nearest_preceding_heading':unit.get('nearest_preceding_heading'),'immediately_preceding_paragraph':unit.get('immediately_preceding_paragraph'),'llm_v29_shared_context':unit.get('llm_v29_shared_context'),
       'object_scope_dependencies':after.get('object_scope_dependencies'),'typed_contexts_v34':after.get('typed_contexts_v34'),'source_context_adaptation_log_v33':after.get('source_context_adaptation_log_v33'),'review_flags':after.get('review_flags')}
  projection.append(redact(row))
 # Final mechanical projection gate: protected full units cannot survive
 # normalization; context strings cannot retain the conservative overlap.
 for row in projection:
  for path,value in strings(row):
   n=norm(value)
   assert not any(t in n for t in reserved_norms)
   if context_path(path):assert not any(n[i:i+24] in context24 for i in range(max(0,len(n)-23)))
 exunit=inputs[EXCEPTION]['input'];a=old[EXCEPTION]['prediction'];b=new[EXCEPTION]['prediction']
 exception={'id':EXCEPTION,'already_exposed_development':True,'retain_original_reserved_membership_and_exposure_flag':True,'not_independent_validation':True,'unit_text_sha256':digest(exunit['unit_text']),'labels_before_v37_2':a['labels'],'labels_after_v38':b['labels'],'fairness_subtypes_before':a['fairness_subtypes'],'fairness_subtypes_after':b['fairness_subtypes'],'new_evidence':[e for e in b['evidence'] if e not in a['evidence']],'source_display':exunit.get('unit_source') or exunit.get('source'),'source_display_sha256':exunit.get('unit_source_sha256') or exunit.get('source_sha256'),'policy':'This is the only individually disclosed reserved member in this comparison, by explicit root authorization.'}
 summary={'status':'independent_mechanical_comparison_complete_pending_nonreserved_semantic_review','audited_utc':datetime.now(timezone.utc).isoformat(),'n':4924,'baseline_version':'v37.2 shadow; not v36.2','new_version':newrun['version'],'all_4924_ids_original_ids_and_input_unit_hashes_match':True,'strict_five_binary_labels_and_evidence_rebuild_match':True,'all_subtypes_and_safety_quality_markers_match_evidence':True,'literal_span_checks':dict(checks),'same_input_sha256':sha(INPUT),'baseline_predictions_sha256':sha(OLD),'shadow_predictions_sha256':sha(NEW),'baseline_run_manifest_sha256':sha(OLD.with_suffix('.run.json')),'new_run_manifest_sha256':sha(NEW.with_suffix('.run.json')),'candidate_freeze_sha256':sha(FREEZE),'exclusion_metadata_sha256':sha(EXCLUSION),'reserved_family_members_n':len(reserved),'counts_by_group':{g:dict(per_group[g]) for g in ('nonreserved','reserved267_aggregate_only')},'changes_by_dimension_direction':{g:dict(direction[g]) for g in ('nonreserved','reserved267_aggregate_only')},'subtype_field_change_counts':{g:{f:n for (gg,f),n in subtype_changes.items() if gg==g} for g in ('nonreserved','reserved267_aggregate_only')},'nonversion_field_change_counts':{g:{f:n for (gg,f),n in all_field_changes.items() if gg==g} for g in ('nonreserved','reserved267_aggregate_only')},'evidence_changed_without_label_change_counts':dict(evidence_only),'nonreserved_projection_n':len(projection),'context_redaction_counts':dict(redactions),'protected_projection_postcheck_pass':True,'source_display_uses_unit_source_first':True,'actual_source_and_candidate_bindings_same_as_v37_2':True,'actual_bound_sources_and_code_current_hashes_match':True,'new_frozen_production_file_n':len(freeze['production_code_sha256']),'actual_run_declared_runtime_file_n':len(newrun['runtime_code_sha256']),'frozen_files_not_in_preloop_runtime_module_map':[p for p in freeze['production_code_sha256'] if p not in newrun['runtime_code_sha256']],'known_exposed_exception_id':EXCEPTION,'individual_other_reserved_changes_or_predictions_disclosed':False,'human_labels_or_reference_loaded':False,'kappa_or_machine_validity_computed':False,'classifier_or_model_executed_by_auditor':False,'script_sha256':sha(__file__)}
 OUT.mkdir()
 write('mechanical_comparison_summary.json',summary)
 write('nonreserved_change_ids_labels_subtypes.json',changed_nonreserved)
 write('nonreserved_changes_manual_review_projection.json',projection)
 write('previously_exposed_01361_flagged_check.json',exception)
 seal=write('mechanical_audit_artifact_seal.json',{'sealed_utc':datetime.now(timezone.utc).isoformat(),'files':{str(p.resolve()):sha(p) for p in sorted(OUT.glob('*.json'))},'script':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)}})
 print(json.dumps({'n':4924,'counts_by_group':summary['counts_by_group'],'dimension_directions':summary['changes_by_dimension_direction'],'nonreserved_projection_n':len(projection),'projection_path':str(OUT/'nonreserved_changes_manual_review_projection.json'),'summary_sha256':sha(OUT/'mechanical_comparison_summary.json'),'seal_sha256':sha(seal)},ensure_ascii=False))

if __name__=='__main__':main()

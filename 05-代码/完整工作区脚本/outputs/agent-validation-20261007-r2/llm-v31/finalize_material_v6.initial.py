"""Seal actual I/F calls and dimension-explicit S/E/Ec provenance; no score selection."""
from pathlib import Path
import json,hashlib,copy,importlib.util
HERE=Path(__file__).resolve().parent;ROUND=HERE.parent;OLD=ROUND.parent/'recall-revision-20261007/llm-v30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def load_selected(run,index):
 b=run/'batches'/f'batch-{index:04d}';selection=json.loads((b/'selection.json').read_text());assert selection['status']=='accepted_first_valid_actual_attempt'
 accepted=[a for a in selection['attempts'] if a['status']=='accepted_structural_literal_zero_tools'];assert accepted and accepted[0]['relative_path']==selection['selected_relative_path']
 selected=run/selection['selected_relative_path'];raw=selected/'raw_output.json';meta=json.loads((selected/'run_metadata.json').read_text())
 assert meta['raw_output_sha256']==sha(raw)==selection['selected_output_sha256']
 assert meta['requested_model']=='gpt-5.6-sol' and meta['tool_event_count']==0 and meta['label_or_metric_selection'] is False
 event=json.loads((selected/'tool_event_audit.json').read_text());assert event['tool_or_unknown_item_event_count']==0 and event['completed_turns']==1
 assert sha(selected/'events.jsonl')==meta['events_sha256']
 inp=json.loads((selected/'input.json').read_text())['rows'];out=json.loads(raw.read_text())
 assert [r['id'] for r in inp]==[r['id'] for r in out['rows']]
 return inp,out,{'run':str(run.resolve()),'batch_index':index,'selected_relative_path':selection['selected_relative_path'],'selection_sha256':sha(b/'selection.json'),'input_sha256':sha(selected/'input.json'),'raw_output_sha256':sha(raw),'metadata_sha256':sha(selected/'run_metadata.json'),'events_sha256':sha(selected/'events.jsonl'),'raw_path':str(raw.resolve()),'all_attempts':selection['attempts']}
def main():
 final_input=jl(ROUND/'effective_blind_inputs_v6.jsonl');assert len(final_input)==4924
 base=HERE/'production-25';plan=json.loads((base/'run_plan.json').read_text());assert plan['n']==4924 and plan['batch_size']==25
 # Do not finalize a partially completed production, even if selected patches exist.
 selections=list((base/'batches').glob('batch-*/selection.json'));assert len(selections)==197,'full production still running'
 replacements={57:(HERE/'material-v4-affected',1),58:(HERE/'material-v4-affected',2),68:(HERE/'material-v5-affected',1),133:(HERE/'material-v6-affected',1)}
 spec=importlib.util.spec_from_file_location('if_validator',HERE/'validate_binary_output.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 if_rows=[];lineage=[]
 for index in range(1,198):
  run,bi=replacements.get(index,(base,index));inp,out,record=load_selected(run,bi)
  assert inp==final_input[(index-1)*25:index*25],f'Final material mismatch in I/F batch {index}'
  assert not v.validate({'rows':inp},out)
  assert json.loads((run/'run_plan.json').read_text())['prompt_sha256']==plan['prompt_sha256']
  record['original_batch_index']=index;record['reason']='changed_input_complete_batch_unconditional' if index in replacements else 'exact_final_input_equality'
  if_rows.extend(out['rows']);lineage.append(record)
 assert [r['id'] for r in if_rows]==[r['id'] for r in final_input]
 old_rows=jl(OLD/'sealed-final-material-v3/all_predictions.jsonl');original={r['id']:r for r in old_rows}
 source_input={r['id']:r for r in jl(ROUND.parent/'recall-revision-20261007/effective_blind_inputs_v30_v3.jsonl')}
 seec_patch_runs=[(OLD/'material-v4-se-ec-r2',[1,2]),(ROUND/'llm-v30-seec/material-v5-v6',[1,2])]
 seec_rows=copy.deepcopy(original);seec_sources={rid:'original_v30_actual_prediction' for rid in original};seec_lineage=[];patched=set()
 for run,indices in seec_patch_runs:
  assert json.loads((run/'run_plan.json').read_text())['prompt_sha256']==sha(OLD/'完整系统提示词-v30-候选03.txt')
  for index in indices:
   inp,out,record=load_selected(run,index)
   for s,r in zip(inp,out['rows']):
    assert s==next(x for x in final_input if x['id']==s['id'])
    assert r['id'] not in patched;patched.add(r['id']);seec_rows[r['id']]=r;seec_sources[r['id']]=record['raw_path']
   seec_lineage.append(record)
 assert len(patched)==100
 for r in final_input:
  if r['id'] not in patched:assert r==source_input[r['id']],f'Unreexecuted S/E/Ec changed input: {r["id"]}'
 combined=[];changes=[]
 for updated in if_rows:
  rid=updated['id'];r=copy.deepcopy(seec_rows[rid]);r['id']=rid
  r['labels']={**{d:r['labels'][d] for d in ['S','E','Ec']},**updated['labels']}
  r['dimension_reasons']={**{d:r['dimension_reasons'][d] for d in ['S','E','Ec']},**updated['dimension_reasons']}
  r['evidence']=[e for e in r['evidence'] if e['dimension'] in ['S','E','Ec']]+updated['evidence']
  r['innovation_subtypes']=updated['innovation_subtypes'];r['fairness_subtypes']=updated['fairness_subtypes']
  r['dimension_execution_versions']={'S':'LLM-binary-v30','E':'LLM-binary-v30','Ec':'LLM-binary-v30','I':'LLM-IF-v31-candidate02','F':'LLM-IF-v31-candidate02'}
  r['se_ec_actual_source']=seec_sources[rid];r['material_version']='v6';combined.append(r)
  for d in ['S','E','Ec','I','F']:
   if r['labels'][d]!=original[rid]['labels'][d]:changes.append({'id':rid,'dimension':d,'old':original[rid]['labels'][d],'new':r['labels'][d],'cause_scope':'S/E/Ec same-prompt actual full-batch material refresh' if d in ['S','E','Ec'] else 'I/F fixed new execution plus material changes; not pure prompt-only effect'})
 dest=HERE/'sealed-final-material-v6';dest.mkdir(exist_ok=True)
 for name,rows in [('all_predictions_if_actual.jsonl',if_rows),('all_predictions_composite.jsonl',combined)]:
  p=dest/name;data=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)
  if p.exists():assert p.read_text()==data
  else:p.write_text(data)
 dump(dest/'selected_actual_execution_lineage.json',{'if':lineage,'se_ec_material_refresh':seec_lineage})
 dump(dest/'changes_vs_actual_v30.json',changes)
 sources=[ROUND/'effective_blind_inputs_v6.jsonl',ROUND/'rule_inputs_shared_v6.jsonl',HERE/'I-F复核提示词-v31-候选02.txt',HERE/'validate_binary_output.py',HERE/'run_production_v31.py',Path(__file__),OLD/'完整系统提示词-v30-候选03.txt',OLD/'sealed-final-material-v3/all_predictions.jsonl']
 dump(dest/'final_manifest.json',{'status':'complete_actual_execution_dimension_explicit','n':4924,'material_version':'v6','requested_model':'gpt-5.6-sol','provider_internal_revision':'not_exposed','I_F_actual_reread_n':4924,'S_E_Ec_original_actual_retained_n':4824,'S_E_Ec_same_prompt_material_batch_rerun_n':100,'all_methods_final_material_same':True,'all_I_F_selected_batches_input_exactly_final':True,'changed_batches_unconditional':sorted(replacements),'selected_I_F_batch_n':197,'selected_S_E_Ec_refresh_batch_n':4,'references_or_metrics_used_to_select_outputs':False,'human_validation_completed':False,'source_sha256':{str(p.resolve()):sha(p) for p in sources},'outputs_sha256':{str(p.resolve()):sha(p) for p in dest.iterdir() if p.is_file() and p.name!='final_manifest.json'}})
 print(json.dumps({'complete':True,'n':4924,'composite_sha256':sha(dest/'all_predictions_composite.jsonl'),'if_sha256':sha(dest/'all_predictions_if_actual.jsonl'),'changed_labels_vs_old':len(changes)},ensure_ascii=False))
if __name__=='__main__':main()

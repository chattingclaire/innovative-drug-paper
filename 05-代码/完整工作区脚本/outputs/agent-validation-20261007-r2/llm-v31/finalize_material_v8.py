"""Seal actual I/F calls and dimension-explicit S/E/Ec provenance; no score selection."""
from pathlib import Path
import json,hashlib,copy,importlib.util
from execution_integrity_v6 import audit_run
HERE=Path(__file__).resolve().parent;ROUND=HERE.parent;OLD=ROUND.parent/'recall-revision-20261007/llm-v30'
CACHE={}
def audited(run):
 run=Path(run).resolve()
 if str(run) not in CACHE:CACHE[str(run)]=audit_run(run)
 return CACHE[str(run)]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def dump(p,d):
 data=json.dumps(d,ensure_ascii=False,indent=2)+'\n'
 if p.exists():assert p.read_text()==data,('refusing to overwrite sealed output',str(p))
 else:p.write_text(data)
def load_selected(run,index):
 checked=audited(run);actual=checked['selected'][index]
 b=run/'batches'/f'batch-{index:04d}';selection=json.loads((b/'selection.json').read_text());assert selection['status']=='accepted_first_valid_actual_attempt'
 accepted=[a for a in selection['attempts'] if a['status']=='accepted_structural_literal_zero_tools'];assert accepted and accepted[0]['relative_path']==selection['selected_relative_path']
 selected=run/selection['selected_relative_path'];raw=selected/'raw_output.json';meta=json.loads((selected/'run_metadata.json').read_text())
 assert meta['raw_output_sha256']==sha(raw)==selection['selected_output_sha256']
 assert meta['requested_model']=='gpt-5.6-sol' and meta['tool_event_count']==0 and meta['label_or_metric_selection'] is False
 event=json.loads((selected/'tool_event_audit.json').read_text());assert event['tool_or_unknown_item_event_count']==0 and event['completed_turns']==1
 assert sha(selected/'events.jsonl')==meta['events_sha256']
 inp=json.loads((selected/'input.json').read_text())['rows'];out=json.loads(raw.read_text())
 assert [r['id'] for r in inp]==[r['id'] for r in out['rows']]
 assert inp==actual['input'] and out==actual['output'] and str(raw.resolve())==actual['raw_path']
 return inp,out,{'run':str(run.resolve()),'batch_index':index,'selected_relative_path':selection['selected_relative_path'],'selection_sha256':sha(b/'selection.json'),'input_sha256':sha(selected/'input.json'),'raw_output_sha256':sha(raw),'metadata_sha256':sha(selected/'run_metadata.json'),'events_sha256':sha(selected/'events.jsonl'),'raw_path':str(raw.resolve()),'all_attempts':selection['attempts']}
def main():
 final_input=jl(ROUND/'effective_blind_inputs_v8.jsonl');assert len(final_input)==4924
 rule_inputs=jl(ROUND/'rule_inputs_shared_v8.jsonl');assert len(rule_inputs)==4924
 assert all(a['id']==b['id'] and a['text']==b['input']['unit_text'] and a['contexts']==b['input']['llm_v29_shared_context'] for a,b in zip(final_input,rule_inputs))
 base=HERE/'production-25';plan=json.loads((base/'run_plan.json').read_text());assert plan['n']==4924 and plan['batch_size']==25
 # Do not finalize a partially completed production, even if selected patches exist.
 selections=list((base/'batches').glob('batch-*/selection.json'));assert len(selections)==197,'full production still running'
 original_execution=audited(base)
 assert original_execution['completed_batch_count']==197
 assert not original_execution['all_material_issue_records'],'unresolved actual material_issue requires source review'
 replacements={57:(HERE/'material-v4-affected',1),58:(HERE/'material-v4-affected',2),68:(HERE/'material-v5-affected',1),133:(HERE/'material-v6-affected',1),90:(HERE/'material-v7-affected',1),166:(HERE/'material-v8-affected',1),167:(HERE/'material-v8-affected',2),168:(HERE/'material-v8-affected',3),185:(HERE/'material-v8-affected',4)}
 assert sorted(replacements)==json.loads((ROUND/'material_v8_manifest.json').read_text())['final_changed_original_batches']
 repairs={};repair_lineage=[]
 for repair_plan_path in sorted(HERE.glob('technical-repair-original-*/technical_repair_plan.json')):
  rp=json.loads(repair_plan_path.read_text());bi=rp['original_batch'];assert bi not in repairs
  failure=next(x for x in original_execution['failed_batches'] if x['batch']==bi)
  assert rp['original_selection_sha256']==failure['selection_sha256'] and rp['blind_reference_or_metric_access'] is False
  assert all(a['errors'] and not any('unresolved_material_issue' in e for e in a['errors']) for a in failure['attempts'])
  rr=repair_plan_path.parent/'actual-five-row-retry';checked=audited(rr)
  if bi in replacements:
   repair_lineage.append({'original_batch_index':bi,'technical_repair_plan_path':str(repair_plan_path),'technical_repair_plan_sha256':sha(repair_plan_path),'original_failure':failure,'actual_split_run':str(rr),'selected_for_final':False,'reason':'Subsequent independently source-verified material gap; complete original batch unconditionally reexecuted, no partial split stitching.','split_failures_preserved':checked['failed_batches']})
   continue
  assert not checked['failed_batches'] and not checked['all_material_issue_records']
  assert checked['plan']['prompt_sha256']==rp['prompt_sha256']==plan['prompt_sha256']
  assert checked['plan']['batch_size']==5 and checked['plan']['n']==rp['original_n']==25
  repairs[bi]=[(rr,j) for j in range(1,6)]
  repair_lineage.append({'original_batch_index':bi,'technical_repair_plan_path':str(repair_plan_path),'technical_repair_plan_sha256':sha(repair_plan_path),'original_failure':failure})
 assert {x['batch'] for x in original_execution['failed_batches']}<=set(replacements)|set(repairs),'unrepaired original production technical failure'
 spec=importlib.util.spec_from_file_location('if_validator',HERE/'validate_binary_output.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 if_rows=[];lineage=[]
 for index in range(1,198):
  chosen=repairs.get(index,[replacements.get(index,(base,index))]);material=[]
  for run,bi in chosen:
   inp,out,record=load_selected(run,bi);material.extend(inp)
   assert not v.validate({'rows':inp},out)
   assert not audited(run)['all_material_issue_records']
   assert json.loads((run/'run_plan.json').read_text())['prompt_sha256']==plan['prompt_sha256']
   record['original_batch_index']=index;record['reason']='changed_input_complete_batch_unconditional' if index in replacements else 'entire_three_failure_original_batch_five_row_technical_retry' if index in repairs else 'exact_final_input_equality'
   if_rows.extend(out['rows']);lineage.append(record)
  assert material==final_input[(index-1)*25:index*25],f'Final material mismatch in I/F batch {index}'
 assert [r['id'] for r in if_rows]==[r['id'] for r in final_input]
 old_rows=jl(OLD/'sealed-final-material-v3/all_predictions.jsonl');original={r['id']:r for r in old_rows}
 source_input={r['id']:r for r in jl(ROUND.parent/'recall-revision-20261007/effective_blind_inputs_v30_v3.jsonl')}
 old_lineage=json.loads((OLD/'sealed-final-material-v3/selected_execution_lineage.json').read_text())
 old_raw_rows={}
 seec_patch_runs=[(OLD/'material-v4-se-ec-r2',[1,2]),(ROUND/'llm-v30-seec/material-v5-v6',[1,2]),(ROUND/'llm-v30-seec/material-v7',[1]),(ROUND/'llm-v30-seec/material-v8',[1,2,3,4])]
 seec_rows=copy.deepcopy(original);seec_sources={rid:'original_v30_actual_prediction' for rid in original};seec_lineage=[];patched=set()
 for run,indices in seec_patch_runs:
  assert json.loads((run/'run_plan.json').read_text())['prompt_sha256']==sha(OLD/'完整系统提示词-v30-候选03.txt')
  for index in indices:
   inp,out,record=load_selected(run,index)
   for s,r in zip(inp,out['rows']):
    assert s==next(x for x in final_input if x['id']==s['id'])
    assert r['id'] not in patched;patched.add(r['id']);seec_rows[r['id']]=r;seec_sources[r['id']]=record['raw_path']
   seec_lineage.append(record)
 assert len(patched)==225
 retained_sources={}
 for r in final_input:
  if r['id'] not in patched:
   rid=r['id'];assert r==source_input[rid],f'Unreexecuted S/E/Ec changed input: {rid}'
   binding=old_lineage['rows'][rid];actual=audited(binding['actual_run_path'])['selected'][binding['actual_batch_index']]
   assert actual['raw_path']==binding['selected_raw_output_path'] and sha(actual['raw_path'])==binding['selected_raw_output_sha256']
   if actual['raw_path'] not in old_raw_rows:old_raw_rows[actual['raw_path']]={row['id']:(inp,row) for inp,row in zip(actual['input'],actual['output']['rows'])}
   inp,row=old_raw_rows[actual['raw_path']][rid];assert inp==r and row==original[rid]
   seec_sources[rid]=actual['raw_path'];retained_sources[rid]={'raw_path':actual['raw_path'],'raw_sha256':sha(actual['raw_path']),'actual_input_path':str(Path(actual['selected_attempt'])/'input.json')}
 combined=[];changes=[]
 for updated in if_rows:
  rid=updated['id'];r=copy.deepcopy(seec_rows[rid]);r['id']=rid
  r['labels']={**{d:r['labels'][d] for d in ['S','E','Ec']},**updated['labels']}
  r['dimension_reasons']={**{d:r['dimension_reasons'][d] for d in ['S','E','Ec']},**updated['dimension_reasons']}
  r['evidence']=[e for e in r['evidence'] if e['dimension'] in ['S','E','Ec']]+updated['evidence']
  r['innovation_subtypes']=updated['innovation_subtypes'];r['fairness_subtypes']=updated['fairness_subtypes']
  r['dimension_execution_versions']={'S':'LLM-binary-v30','E':'LLM-binary-v30','Ec':'LLM-binary-v30','I':'LLM-IF-v31-candidate02','F':'LLM-IF-v31-candidate02'}
  r['se_ec_actual_source']=seec_sources[rid];r['material_version']='v8';combined.append(r)
  for d in ['S','E','Ec','I','F']:
   if r['labels'][d]!=original[rid]['labels'][d]:changes.append({'id':rid,'dimension':d,'old':original[rid]['labels'][d],'new':r['labels'][d],'cause_scope':'S/E/Ec same-prompt actual full-batch material refresh' if d in ['S','E','Ec'] else 'I/F fixed new execution plus material changes; not pure prompt-only effect'})
 dest=HERE/'sealed-final-material-v8';dest.mkdir(exist_ok=True)
 for name,rows in [('all_predictions_if_actual.jsonl',if_rows),('all_predictions_composite.jsonl',combined)]:
  p=dest/name;data=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)
  if p.exists():assert p.read_text()==data
  else:p.write_text(data)
 dump(dest/'selected_actual_execution_lineage.json',{'if':lineage,'se_ec_material_refresh':seec_lineage,'se_ec_retained_4699_row_sources':retained_sources,'technical_repair':repair_lineage})
 dump(dest/'changes_vs_actual_v30.json',changes)
 dump(dest/'actual_execution_reconstruction_QA.json',{'status':'all_original_and_selected_actual_attempts_reconstructed','original_production_batch_count':197,'original_production_accepted_batch_count':len(original_execution['selected']),'original_production_failed_batches':original_execution['failed_batches'],'selected_I_F_original_batch_groups':197,'selected_I_F_actual_calls':len(lineage),'technical_repair_original_batches':sorted(repairs),'all_actual_audited_runs':[{k:z for k,z in a.items() if k not in ['selected','plan']} for a in CACHE.values()],'all_selected_request_material_exact_final_v8':True,'all_selected_first_valid_attempt':True,'all_selected_tool_events':0,'counts_scope':'Current production, selected material and technical reruns, and old actual v30 source runs; not all project probes.','semantic_validity_not_proven_by_structure':True})
 sources=[ROUND/'effective_blind_inputs_v8.jsonl',ROUND/'rule_inputs_shared_v8.jsonl',HERE/'I-F复核提示词-v31-候选02.txt',HERE/'validate_binary_output.py',HERE/'run_production_v31.py',HERE/'execution_integrity_v6.py',HERE/'final_material_v8_seal_plan.json',HERE/'final_material_v8_seal_plan_amendment_01.json',Path(__file__),OLD/'完整系统提示词-v30-候选03.txt',OLD/'sealed-final-material-v3/all_predictions.jsonl',OLD/'sealed-final-material-v3/selected_execution_lineage.json']
 dump(dest/'final_manifest.json',{'status':'complete_actual_execution_dimension_explicit','n':4924,'material_version':'v8','requested_model':'gpt-5.6-sol','reasoning_effort':'medium','provider_internal_revision':'not_exposed','I_F_actual_reread_n':4924,'S_E_Ec_original_actual_retained_n':4699,'S_E_Ec_same_prompt_material_batch_rerun_n':225,'all_methods_final_material_same':True,'all_I_F_selected_batches_input_exactly_final':True,'changed_batches_unconditional':sorted(replacements),'selected_I_F_batch_n':197,'selected_I_F_actual_call_n':len(lineage),'selected_S_E_Ec_refresh_batch_n':9,'technical_repair_original_batches':sorted(repairs),'all_original_197_batches_attempt_audited':True,'references_or_metrics_used_to_select_outputs':False,'human_validation_completed':False,'source_sha256':{str(p.resolve()):sha(p) for p in sources},'material_manifests_sha256':{str(ROUND/f'material_v{i}_manifest.json'):sha(ROUND/f'material_v{i}_manifest.json') for i in [4,5,6,7,8]},'outputs_sha256':{str(p.resolve()):sha(p) for p in dest.iterdir() if p.is_file() and p.name!='final_manifest.json'}})
 print(json.dumps({'complete':True,'n':4924,'composite_sha256':sha(dest/'all_predictions_composite.jsonl'),'if_sha256':sha(dest/'all_predictions_if_actual.jsonl'),'changed_labels_vs_old':len(changes)},ensure_ascii=False))
if __name__=='__main__':main()

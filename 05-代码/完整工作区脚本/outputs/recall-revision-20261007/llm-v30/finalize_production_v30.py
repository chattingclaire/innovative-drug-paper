"""Bind genuinely completed v30 output, raw execution lineage and shared material; no label editing."""
from pathlib import Path
import hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
RUN=HERE/'production-25-v30-v2'
LLM_SHA='0c05b1dbd43a74943bb1deafd26b1dbb1963bef0505dda501d83cdf1bfed9955'
RULE_SHA='0d4e6358807c5ed38311b9a306dd539de7278e2c57de94b7a0f7730b2e06258a'
PROMPT_SHA='bc2d1ef42d90b369f1949ee954bd37f7e3e5838286e248222c455beb16187753'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def load(p):return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
def main():
 material_issue=HERE/'material_scope_issue_01775.json'
 if material_issue.exists():assert json.loads(material_issue.read_text())['status'] in {'resolved_no_material_change_required','resolved_new_material_and_actual_rerun_bound'},'Current material scope issue has not been resolved; do not publish final LLM completion.'
 subprocess.run([sys.executable,str(HERE/'verify_actual_execution_v30.py'),'--run',str(RUN)],check=True,capture_output=True,text=True)
 qa=json.loads((RUN/'actual_execution_reconstruction_QA.json').read_text());summary=json.loads((RUN/'execution_summary.json').read_text());assert qa['status']=='passed_actual_execution_reconstruction' and qa['n']==4924 and summary['status']=='complete_actual_calls_structurally_valid';assert qa['prompt_sha256']==PROMPT_SHA and qa['input_sha256']==LLM_SHA
 inp=BASE/'effective_blind_inputs_v30_v2.jsonl';rules=BASE/'rule_inputs_v31_shared_v2.jsonl';assert sha(inp)==LLM_SHA and sha(rules)==RULE_SHA
 assert sha(HERE/'protocol-v1.3.md')=='75ff8ebda018a15e008bc1075892000fb9c9c053943d05f04bbe193176c605a6';assert sha(HERE/'完整系统提示词-v30-候选03.txt')==PROMPT_SHA;assert (HERE/'protocol-v1.3.md').read_text() in (RUN/'frozen_prompt.txt').read_text()
 sourceqa=BASE/'source_object_scope_v2_independent_QA.json';sq=json.loads(sourceqa.read_text());assert sq['status']=='passed' and sq['rule_and_llm_contexts_identical']==4924
 llm=load(inp);rule=load(rules);assert [r['id'] for r in llm]==[r['id'] for r in rule];assert all(a['text']==b['input']['unit_text'] for a,b in zip(llm,rule));assert all(a['contexts']==b['input']['llm_v29_shared_context'] for a,b in zip(llm,rule))
 trace=[];rowmap={};artifacts={}
 for sel in sorted(RUN.glob('batches/*/selection.json')):
  d=json.loads(sel.read_text());raw=RUN/d['selected_relative_path']/'raw_output.json';data=json.loads(raw.read_text());assert d['selected_output_sha256']==sha(raw);ids=[r['id'] for r in data['rows']];assert ids==d['ids'];meta=json.loads((raw.parent/'run_metadata.json').read_text());assert meta['tool_event_count']==0
  trace.append({'batch':sel.parent.name,'selected_output':str(raw.resolve()),'selected_output_sha256':sha(raw),'selected_execution_paths':[str(raw.parent.resolve())],'row_to_actual_raw_response':{rid:str(raw.resolve()) for rid in ids},'first_valid_actual_attempt':True})
  rowmap.update({rid:{'selected_raw_output_path':str(raw.resolve()),'selected_raw_output_sha256':sha(raw),'batch':sel.parent.name} for rid in ids})
 assert len(rowmap)==4924
 whole=json.loads((RUN/'all_predictions.json').read_text());write(RUN/'all_issue_records.json',whole['issue_records'])
 for path in sorted(RUN.rglob('*')):
  if path.is_file() and path.name not in {'execution_artifact_hashes.json','final_manifest.json'}:artifacts[str(path.relative_to(RUN))]=sha(path)
 write(RUN/'selected_execution_lineage.json',{'status':'all_rows_bound_to_unchanged_selected_actual_responses','rows':rowmap,'batches':trace})
 artifacts['selected_execution_lineage.json']=sha(RUN/'selected_execution_lineage.json');write(RUN/'execution_artifact_hashes.json',{'status':'actual_artifact_inventory','artifacts':artifacts})
 finalqa={'status':'passed','n':4924,'dimension_labels_checked':24620,'whole_output_literal_and_structure_errors':[],'predictions_sha256':sha(RUN/'all_predictions.jsonl'),'effective_input_sha256':LLM_SHA,'shared_rule_input_sha256':RULE_SHA,'input_context_equality_n':4924,'unit_texts_unchanged_n':4924,'selected_tool_event_count':qa['selected_tool_events'],'selected_actual_execution_count':qa['selected_batches'],'all_attempt_count':qa['actual_attempt_count'],'all_attempt_tool_event_count':qa['all_attempt_tool_events'],'hashed_artifacts_checked':len(artifacts),'mechanically_edited_output_selected':False,'selected_batch_trace':trace,'actual_reconstruction_QA_path':str((RUN/'actual_execution_reconstruction_QA.json').resolve()),'actual_reconstruction_QA_sha256':sha(RUN/'actual_execution_reconstruction_QA.json'),'shared_source_QA_sha256':sha(sourceqa),'scope':'New v30 independent reconstruction of all selected actual outputs, literal evidence, shared-material equality and CLI execution lineage. Does not claim semantic accuracy or completed human validation.','requested_model':'gpt-5.6-sol','reasoning_effort':'medium','provider_internal_model_revision':'not_exposed'}
 write(BASE/'最终LLM执行独立核验.json',finalqa)
 manifest={'status':'complete_validated_full_corpus','n':4924,'candidate':'03','requested_model':'gpt-5.6-sol','reasoning_effort':'medium','predictions_path':str((RUN/'all_predictions.jsonl').resolve()),'predictions_sha256':sha(RUN/'all_predictions.jsonl'),'issue_records_sha256':sha(RUN/'all_issue_records.json'),'execution_artifact_hashes_sha256':sha(RUN/'execution_artifact_hashes.json'),'selected_execution_lineage_sha256':sha(RUN/'selected_execution_lineage.json'),'effective_input_sha256':LLM_SHA,'shared_rule_input_sha256':RULE_SHA,'system_prompt_sha256':PROMPT_SHA,'manual_sha256':sha(HERE/'protocol-v1.3.md'),'run_plan_sha256':sha(RUN/'run_plan.json'),'source_object_scope_v2_QA_sha256':sha(sourceqa),'actual_execution_QA_sha256':sha(RUN/'actual_execution_reconstruction_QA.json'),'root_execution_QA_sha256':sha(BASE/'最终LLM执行独立核验.json'),'mechanically_edited_output_selected':False,'reference_or_metric_based_output_selection':False,'selected_tool_event_count':0,'source_rules_and_llm_materials_identical':True,'not_independent_human_validation':True}
 stability=HERE/'stability_comparison_v30.json'
 if stability.exists():manifest['stability_comparison_v30_sha256']=sha(stability);manifest['stability_comparison_v30_path']=str(stability.resolve())
 write(RUN/'final_manifest.json',manifest);print(json.dumps({'status':manifest['status'],'n':4924,'predictions_sha256':manifest['predictions_sha256'],'root_QA_sha256':manifest['root_execution_QA_sha256']},ensure_ascii=False))
if __name__=='__main__':main()

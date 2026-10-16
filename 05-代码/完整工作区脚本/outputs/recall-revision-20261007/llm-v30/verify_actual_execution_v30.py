"""Reconstruct selected rows from immutable actual CLI attempts, without assigning labels."""
import argparse,hashlib,json,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();run=Path(a.run).resolve();plan=json.loads((run/'run_plan.json').read_text());inp=run/plan['frozen_input_relative_path'];source_input=Path(plan['source_input_path']);prompt=run/'frozen_prompt.txt';rows=[json.loads(l) for l in inp.read_text().splitlines() if l.strip()] if inp.suffix=='.jsonl' else json.loads(inp.read_text())['rows']
 assert sha(inp)==plan['input_sha256'] and len(rows)==plan['n'];assert sha(prompt)==plan['prompt_sha256'];assert sha(run/'frozen_schema.json')==plan['schema_sha256'];assert sha(run/'frozen_validator.py')==plan['validator_sha256'];assert sha(run/'frozen_runner.py')==plan['runner_sha256'];assert plan['model']=='gpt-5.6-sol' and plan['reasoning_effort']=='medium'
 spec=importlib.util.spec_from_file_location('frozen_validator',run/'frozen_validator.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 output=[];issues=[];attempt_n=0;all_tool_n=0;selected_tool_n=0;selected_paths=[];unknown_provider_revision=False
 for bi,start in enumerate(range(0,len(rows),plan['batch_size']),1):
  b=run/'batches'/f'batch-{bi:04d}';packet=json.loads((b/'input.json').read_text());assert packet=={'rows':rows[start:start+plan['batch_size']]};selection=json.loads((b/'selection.json').read_text());assert selection['status']=='accepted_first_valid_actual_attempt';assert selection['selection_uses_metric_or_label_values'] is False
  expected_request=prompt.read_text()+'\n\n--- 本批冻结盲法输入 ---\n'+json.dumps(packet,ensure_ascii=False)+'\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。';assert (b/'request.txt').read_text()==expected_request
  accepted=[]
  for record in selection['attempts']:
   attempt_n+=1;ad=run/record['relative_path'];meta=json.loads((ad/'run_metadata.json').read_text());assert sha(ad/'run_metadata.json')==record['metadata_sha256'];assert json.loads((ad/'input.json').read_text())==packet;assert sha(ad/'input.json')==meta['input_sha256'];assert (ad/'request.txt').read_text()==expected_request and sha(ad/'request.txt')==meta['request_sha256'];assert sha(ad/'events.jsonl')==meta['events_sha256'];assert sha(ad/'raw_stderr.txt')==meta['stderr_sha256'];assert sha(ad/'validation.json')==meta['validation_sha256'];assert sha(ad/'tool_event_audit.json')==meta['tool_event_audit_sha256']
   if (ad/'raw_output.json').exists():assert sha(ad/'raw_output.json')==meta['raw_output_sha256']==record['raw_output_sha256']
   assert meta['requested_model']=='gpt-5.6-sol' and meta['reasoning_effort']=='medium' and meta['label_or_metric_selection'] is False
   cmd=meta['command'];assert cmd[cmd.index('--model')+1]=='gpt-5.6-sol';assert cmd[cmd.index('--sandbox')+1]=='read-only';assert all(x in cmd for x in ['--ignore-user-config','--ignore-rules','--ephemeral','--skip-git-repo-check','--json']);assert 'model_reasoning_effort="medium"' in cmd and 'web_search="disabled"' in cmd
   assert meta['cli_binary_sha256']==plan['cli_binary_sha256'] and meta['cli_version']==plan['cli_version'];unknown_provider_revision |= meta['provider_internal_model_revision']=='not_exposed'
   tool_events=[];complete_n=0;turn_errors=[]
   for line in (ad/'events.jsonl').read_text().splitlines():
    if not line.strip():continue
    try:event=json.loads(line)
    except ValueError:tool_events.append(line);continue
    et=event.get('type');it=event.get('item',{}).get('type') if isinstance(event.get('item',{}),dict) else None
    if it is not None and it not in {'agent_message','reasoning'}:tool_events.append(event)
    if isinstance(et,str) and any(t in et.lower() for t in ['tool_call','function_call','web_search','web_fetch','command_execution']):tool_events.append(event)
    complete_n+=int(et=='turn.completed')
    if et in ['turn.failed','error']:turn_errors.append(event)
   assert len(tool_events)==meta['tool_event_count'];all_tool_n+=len(tool_events)
   if meta['status']=='accepted_structural_literal_zero_tools':
    assert not tool_events and complete_n==1 and not turn_errors and meta['exit_code']==0 and not meta['errors'];d=json.loads((ad/'raw_output.json').read_text());assert not v.validate(packet,d);accepted.append(ad)
  assert len(accepted)==1,'runner should stop immediately after first valid attempt'
  selected=run/selection['selected_relative_path'];assert selected==accepted[0];assert sha(selected/'raw_output.json')==selection['selected_output_sha256'];d=json.loads((selected/'raw_output.json').read_text());output.extend(d['rows']);issues.extend(d['issue_records']);selected_paths.append(str(selected.relative_to(run)))
 expected={'protocol_version':'CAL-5D-20260926-v1.3','execution_version':'LLM-binary-v30','release_stage':'final_binary_labels','rows':output,'issue_records':issues};assert json.loads((run/'all_predictions.json').read_text())==expected;actual=[json.loads(l) for l in (run/'all_predictions.jsonl').read_text().splitlines() if l.strip()];assert actual==output;assert [r['id'] for r in output]==[r['id'] for r in rows];assert not v.validate({'rows':rows},expected)
 result={'status':'passed_actual_execution_reconstruction','n':len(rows),'binary_label_count':5*len(rows),'actual_attempt_count':attempt_n,'selected_batches':len(selected_paths),'all_attempt_tool_events':all_tool_n,'selected_tool_events':selected_tool_n,'input_sha256':sha(inp),'current_source_input_sha256':sha(source_input),'source_still_equals_frozen_snapshot':sha(source_input)==sha(inp),'prompt_sha256':sha(prompt),'output_sha256':sha(run/'all_predictions.jsonl'),'all_selected_rows_equal_unchanged_actual_raw_outputs':True,'all_attempts_preserved_and_metadata_hashes_match':True,'all_actual_commands_bound_to_gpt_56_sol_medium':True,'provider_model_revision_not_exposed':unknown_provider_revision,'material_semantics_and_label_correctness_not_proven':True,'not_independent_human_validation':True,'selected_attempt_paths':selected_paths};write(run/'actual_execution_reconstruction_QA.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()

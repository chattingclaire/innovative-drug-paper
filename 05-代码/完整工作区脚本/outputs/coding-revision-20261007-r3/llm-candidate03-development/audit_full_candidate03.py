"""Read-only audit of the fixed candidate03 full run; outputs audit sidecars only.

No reference labels, statistical scores, alternate candidate labels, or semantic
retries are used. Raw outputs and their five-dimensional vectors remain intact.
"""
import json,pathlib,hashlib,importlib.util,collections,datetime
H=pathlib.Path(__file__).resolve().parent;R=H.parent
RUN=H/'full-corpus-candidate03-material-v14-development'
PROMPT_SHA='8576d9a1be10b0dd7b69b4c12367f4c357f55abf4ca30d979d5b333493089ba4'
INPUT_SHA='6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763'
BASELINE_SHA='c6a5672053aacc3e9839e0d04d8e457d1207a500682460bdacbbc4abee10c5aa'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def lines(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def canonical_sha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def events_check(p):
 result={'completed':0,'violations':[],'turn_errors':[],'observed_models':[]}
 for i,line in enumerate(p.read_text().splitlines(),1):
  if not line.strip():continue
  try:e=json.loads(line)
  except ValueError:result['violations'].append({'line':i,'kind':'not_json'});continue
  typ=e.get('type');item=e.get('item');it=item.get('type') if isinstance(item,dict) else None
  if it is not None and it not in {'agent_message','reasoning'}:result['violations'].append({'line':i,'kind':it})
  if isinstance(typ,str) and any(t in typ.lower() for t in ['tool_call','function_call','web_search','web_fetch','command_execution']):result['violations'].append({'line':i,'kind':typ})
  if typ=='turn.completed':result['completed']+=1
  if typ in {'turn.failed','error'}:result['turn_errors'].append(e)
  for field in ['model','model_name']:
   if isinstance(e.get(field),str) and e[field] not in result['observed_models']:result['observed_models'].append(e[field])
 return result

plan=read(RUN/'run_plan.json');summary=read(RUN/'execution_summary.json')
assert summary['status']=='complete_actual_calls_structurally_valid',summary
assert plan['n']==4924 and plan['batch_size']==25 and plan['batch_count']==197 and plan['max_attempts']==3
assert plan['model']=='gpt-5.6-sol' and plan['reasoning_effort']=='medium'
assert plan['prompt_sha256']==PROMPT_SHA==sha(RUN/'frozen_prompt.txt')==sha(H/'candidate03_prompt.txt')
assert plan['input_sha256']==INPUT_SHA==sha(RUN/'frozen_input.jsonl')==sha(R/'effective_blind_inputs_v14.jsonl')
assert plan['schema_sha256']==sha(RUN/'frozen_schema.json')
assert plan['validator_sha256']==sha(RUN/'frozen_validator.py')
assert plan['runner_sha256']==sha(RUN/'frozen_runner.py')
assert plan['cli_binary_sha256']==sha(pathlib.Path(plan['cli_path']))
spec=importlib.util.spec_from_file_location('frozen_candidate03_validator',RUN/'frozen_validator.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
inputs=lines(RUN/'frozen_input.jsonl');assert len(inputs)==4924 and len({x['id'] for x in inputs})==4924
prompt=(RUN/'frozen_prompt.txt').read_text()
reconstructed=[];issues=[];provenance=[];batch_audits=[];attempt_audits=[]
for bi in range(1,198):
 b=RUN/'batches'/f'batch-{bi:04d}';selection=read(b/'selection.json');packet=read(b/'input.json')
 assert packet=={'rows':inputs[(bi-1)*25:bi*25]}
 assert selection['batch']==bi and selection['ids']==[r['id'] for r in packet['rows']]
 assert selection['status']=='accepted_first_valid_actual_attempt'
 request=prompt+'\n\n--- 本批冻结盲法输入 ---\n'+json.dumps(packet,ensure_ascii=False)+'\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
 assert (b/'request.txt').read_text()==request
 attempts=sorted((b/'attempts').glob('attempt-*'));assert 1<=len(attempts)<=3
 assert [a.name for a in attempts]==[f'attempt-{i:02d}' for i in range(1,len(attempts)+1)]
 accepted=[]
 for ai,a in enumerate(attempts,1):
  m=read(a/'run_metadata.json');saved_validation=read(a/'validation.json');saved_audit=read(a/'tool_event_audit.json')
  assert read(a/'input.json')==packet and (a/'request.txt').read_text()==request
  assert m['input_sha256']==sha(a/'input.json') and m['request_sha256']==sha(a/'request.txt') and m['prompt_sha256']==PROMPT_SHA
  assert m['events_sha256']==sha(a/'events.jsonl') and m['stderr_sha256']==sha(a/'raw_stderr.txt')
  assert m['tool_event_audit_sha256']==sha(a/'tool_event_audit.json') and m['validation_sha256']==sha(a/'validation.json')
  assert m['requested_model']=='gpt-5.6-sol' and m['reasoning_effort']=='medium'
  assert m['cli_binary_sha256']==plan['cli_binary_sha256'] and m['cli_version']==plan['cli_version']
  c=m['command'];assert c[0]==plan['cli_path'] and c[c.index('--model')+1]=='gpt-5.6-sol'
  assert 'model_reasoning_effort="medium"' in c and 'web_search="disabled"' in c
  assert '--ignore-user-config' in c and '--ignore-rules' in c and '--ephemeral' in c and c[c.index('--sandbox')+1]=='read-only'
  ev=events_check(a/'events.jsonl');raw=a/'raw_output.json';validation_errors=[]
  if raw.exists():
   assert sha(raw)==m['raw_output_sha256']
   try:validation_errors=v.validate(packet,read(raw))
   except Exception as e:validation_errors=[f'{type(e).__name__}:{e}']
  else:validation_errors=['missing_raw_output']
  valid=m['exit_code']==0 and not validation_errors and ev['completed']==1 and not ev['violations'] and not ev['turn_errors'] and all(z=='gpt-5.6-sol' for z in ev['observed_models'])
  assert valid==saved_validation['valid']==(m['status']=='accepted_structural_literal_zero_tools')
  assert len(ev['violations'])==m['tool_event_count']==saved_audit['tool_or_unknown_item_event_count']
  item=selection['attempts'][ai-1];assert item['metadata_sha256']==sha(a/'run_metadata.json')
  assert item['relative_path']==str(a.relative_to(RUN)) and item['raw_output_sha256']==m['raw_output_sha256'] and item['events_sha256']==m['events_sha256']
  attempt_audits.append({'batch':bi,'attempt':ai,'path':str(a),'valid':valid,'metadata_sha256':sha(a/'run_metadata.json'),'request_sha256':m['request_sha256'],'raw_output_sha256':m['raw_output_sha256'],'events_sha256':m['events_sha256'],'validation_errors':validation_errors,'event_check':ev,'original_execution_errors':m['errors']})
  if valid:accepted.append(a)
 assert accepted and selection['selected_relative_path']==str(accepted[0].relative_to(RUN))
 assert accepted[0]==attempts[-1],'No attempts permitted after first valid result'
 selected=accepted[0];m=read(selected/'run_metadata.json');data=read(selected/'raw_output.json')
 assert selection['selected_output_sha256']==sha(selected/'raw_output.json')
 reconstructed.extend(data['rows']);issues.extend(data['issue_records'])
 for src,row in zip(packet['rows'],data['rows']):
  assert src['id']==row['id']
  provenance.append({'id':row['id'],'method_id':'LLM-v32-candidate03-full-corpus-development','all_five_labels_from_one_intact_actual_row':True,'source_row_canonical_sha256':canonical_sha(src),'output_row_canonical_sha256':canonical_sha(row),'batch':bi,'actual_attempt_path':str(selected),'actual_prompt_sha256':PROMPT_SHA,'actual_request_sha256':m['request_sha256'],'raw_output_sha256':m['raw_output_sha256'],'events_sha256':m['events_sha256'],'metadata_sha256':sha(selected/'run_metadata.json'),'requested_model':m['requested_model'],'reasoning_effort':m['reasoning_effort'],'provider_internal_revision':m['provider_internal_model_revision'],'actual_model_identity_beyond_cli_parameter':m['actual_model_identity_beyond_cli_parameter'],'selection':'first valid actual attempt; no reference or metric selection','release_scope':'development comparison, not independent validation or formal adoption'})
 batch_audits.append({'batch':bi,'n':len(packet['rows']),'actual_attempts':len(attempts),'selected_actual_attempt':str(selected),'status':'PASS'})

aggregate=read(RUN/'all_predictions.json');flat=lines(RUN/'all_predictions.jsonl')
assert aggregate['rows']==flat==reconstructed and aggregate['issue_records']==issues
assert not v.validate({'rows':inputs},aggregate)
assert len(reconstructed)==4924 and [r['id'] for r in reconstructed]==[r['id'] for r in inputs]
assert summary['actual_attempt_count']==len(attempt_audits)<=591
assert summary['accepted_batch_count']==197 and summary['source_unchanged_during_run']
assert summary['output_sha256']==sha(RUN/'all_predictions.jsonl') and summary['plan_sha256']==sha(RUN/'run_plan.json')
baseline=R/'llm-v32/full-production-candidate02-material-v14-source-citation-reconciled/all_predictions.jsonl'
assert sha(baseline)==BASELINE_SHA
assert all(sha(H/p)==expected for p,expected in read(H/'candidate03_preservation_hashes.json')['files'].items())
(RUN/'row_provenance.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in provenance))
byid={r['id']:r for r in reconstructed}
known=[{'id':rid,'frozen_input':next(r for r in inputs if r['id']==rid),'new_full_run_original_row':byid[rid],'note':'Known development semantic issue; whole-row output retained exactly without label repair, substitution, or attempt selection.'} for rid in ['RECODE25-01562','RECODE25-02086']]
dump(RUN/'known_continuity_cases_preserved.json',{'status':'descriptive_original_full_run_rows','known_development_errors_not_assumed_to_repeat_deterministically':True,'cases':known})
qa={'status':'PASS','scope':'execution identity, exact requests, first valid attempts, literal evidence, full five-dimensional row reconstruction; not semantic accuracy','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method_id':'LLM-v32-candidate03-full-corpus-development','n':4924,'batches':197,'actual_attempts':len(attempt_audits),'failed_attempts_preserved':sum(not a['valid'] for a in attempt_audits),'selected_tool_event_count':0,'all_attempt_tool_event_count':sum(len(a['event_check']['violations']) for a in attempt_audits),'full_v14_source_sha256':INPUT_SHA,'actual_prompt_sha256':PROMPT_SHA,'output_sha256':sha(RUN/'all_predictions.jsonl'),'plan_sha256':sha(RUN/'run_plan.json'),'summary_sha256':sha(RUN/'execution_summary.json'),'row_provenance_sha256':sha(RUN/'row_provenance.jsonl'),'known_continuity_cases_sha256':sha(RUN/'known_continuity_cases_preserved.json'),'formal_candidate02_baseline_unchanged':True,'candidate03_previous_artifacts_unchanged':True,'all_240_exposed_development':True,'independent_validation':False,'formal_adoption':False,'labels_spliced_or_quotes_repaired':False,'reference_or_metric_based_selection':False,'provider_model_revision':'not exposed; requested CLI model and event model fields audited without inventing provider identity','batch_audits':batch_audits,'attempt_audits':attempt_audits}
dump(RUN/'full_execution_and_row_binding_QA.json',qa)
bindings={'status':'complete_actual_full_corpus_development_comparison_QA_PASS','run':str(RUN),'method_id':qa['method_id'],'source_input':{'path':str(R/'effective_blind_inputs_v14.jsonl'),'sha256':INPUT_SHA},'prompt':{'path':str(RUN/'frozen_prompt.txt'),'sha256':PROMPT_SHA},'requested_model':'gpt-5.6-sol','reasoning_effort':'medium','n':4924,'batches':197,'actual_attempts':len(attempt_audits),'failed_attempts_preserved':qa['failed_attempts_preserved'],'formal_adoption':False,'independent_validation':False,'all_240_exposed_development':True,'baseline_v14_preserved':True,'known_semantic_errors_and_analogous_effects_not_posthoc_repaired':True}
for key,file in [('output','all_predictions.jsonl'),('execution_summary','execution_summary.json'),('run_plan','run_plan.json'),('row_provenance','row_provenance.jsonl'),('technical_QA','full_execution_and_row_binding_QA.json'),('known_continuity_cases','known_continuity_cases_preserved.json')]:bindings[key]={'path':str(RUN/file),'sha256':sha(RUN/file)}
dump(RUN/'full_development_binding.json',bindings)
print(json.dumps({k:qa[k] for k in ['status','n','batches','actual_attempts','failed_attempts_preserved','output_sha256','row_provenance_sha256']},ensure_ascii=False));print('binding_sha256',sha(RUN/'full_development_binding.json'))

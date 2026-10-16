"""Build traceable three-version comparison and actual-row bindings; no relabeling."""
import pathlib,json,hashlib,collections
H=pathlib.Path(__file__).resolve().parent;R=H.parent;D=['S','E','Ec','I','F']
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def idx(p):return {x['id']:x for x in lines(p)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def canonical_sha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

out={
 'v14':idx(R/'llm-v32/full-production-candidate02-material-v14-source-citation-reconciled/all_predictions.jsonl'),
 'candidate03':idx(H/'exposed240-first-run/all_predictions.jsonl'),
 'candidate04':idx(H/'exposed240-candidate04-first-run/all_predictions.jsonl')}
ref={'A':idx(R/'reference/agent_A_final_v14.jsonl'),'C':idx(R/'reference/agent_C_final_v14.jsonl'),'candidate':idx(R/'statistics/final-v14/candidate_reference.jsonl')}
inp=idx(H/'exposed240_inputs.jsonl');sample={s['original_id']:s for s in read(R/'admin/confirmation_sampling_PRIVATE.json')['sample']}
assert set(inp)==set(out['candidate03'])==set(out['candidate04'])
changes=[];remaining=[]
for rid,x in inp.items():
 for d in D:
  labels={name:rows[rid]['labels'][d] for name,rows in out.items()};refs={name:rows[rid]['labels'][d] for name,rows in ref.items()}
  row={'id':rid,'dimension':d,'component':sample[rid]['component'],'versions':labels,'references':refs,'text':x['text'],'contexts':x['contexts'],'reasons':{name:rows[rid]['dimension_reasons'][d] for name,rows in out.items()},'evidence':{name:[e for e in rows[rid]['evidence'] if e['dimension']==d] for name,rows in out.items()}}
  if len(set(labels.values()))>1:
   row['reference_direction_only']={}
   for a,b in [('v14','candidate03'),('candidate03','candidate04'),('v14','candidate04')]:
    av,bv=labels[a],labels[b]; y=refs['candidate']
    row['reference_direction_only'][f'{a}_to_{b}']='unchanged' if av==bv else 'toward_candidate_reference' if bv==y else 'away_from_candidate_reference'
   changes.append(row)
  if any(labels['candidate04']!=v for v in refs.values()):remaining.append(row)

bind=[]
for runname in ['exposed240-first-run','synthetic30-first-run','exposed240-candidate04-first-run','synthetic38-candidate04-first-run']:
 run=H/runname;plan=read(run/'run_plan.json');summary=read(run/'execution_summary.json');prov=[]
 assert summary['status']=='complete_actual_calls_structurally_valid'
 for bp in sorted((run/'batches').glob('batch-*')):
  selection=read(bp/'selection.json');at=run/selection['selected_relative_path'];m=read(at/'run_metadata.json');packet=read(at/'input.json')
  for source,row in zip(packet['rows'],read(at/'raw_output.json')['rows']):
   assert source['id']==row['id']
   prov.append({'id':row['id'],'method_id':'LLM-v32-candidate04-development' if 'candidate04' in runname else 'LLM-v32-candidate03-development','all_five_labels_from_one_intact_actual_row':True,'source_row_canonical_sha256':canonical_sha(source),'output_row_canonical_sha256':canonical_sha(row),'batch':selection['batch'],'actual_attempt_path':str(at),'actual_prompt_sha256':m['prompt_sha256'],'actual_request_sha256':m['request_sha256'],'raw_output_sha256':m['raw_output_sha256'],'events_sha256':m['events_sha256'],'metadata_sha256':sha(at/'run_metadata.json'),'requested_model':m['requested_model'],'reasoning_effort':m['reasoning_effort'],'provider_internal_revision':m['provider_internal_model_revision'],'actual_model_identity_beyond_cli_parameter':m['actual_model_identity_beyond_cli_parameter'],'selection_rule':'first actual technically valid attempt; no metric or reference selection','reference_exposure':'development'} )
 (run/'row_provenance.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in prov))
 bind.append({'run':str(run),'n':summary['n'],'attempt_n':summary['actual_attempt_count'],'output':{'path':str(run/'all_predictions.jsonl'),'sha256':sha(run/'all_predictions.jsonl')},'plan':{'path':str(run/'run_plan.json'),'sha256':sha(run/'run_plan.json')},'summary':{'path':str(run/'execution_summary.json'),'sha256':sha(run/'execution_summary.json')},'row_provenance':{'path':str(run/'row_provenance.jsonl'),'sha256':sha(run/'row_provenance.jsonl')}})

# Keep all originally preserved c03 bytes unchanged; row_provenance is an added sidecar.
assert all(sha(H/p)==v for p,v in read(H/'candidate03_preservation_hashes.json')['files'].items())
directions={transition:dict(collections.Counter(r['reference_direction_only'][transition] for r in changes)) for transition in ['v14_to_candidate03','candidate03_to_candidate04','v14_to_candidate04']}
continuity=[]
for rid in ['RECODE25-01562','RECODE25-02086']:
 continuity.append({'id':rid,'unchanged_v14_input':inp[rid],'all_five_dimensional_original_rows':{k:v[rid] for k,v in out.items()},'do_not_splice_dimensions':True})
controls=read(H/'synthetic38_candidate04_expected_PRIVATE.json')['tests']
controloutputs=idx(H/'synthetic38-candidate04-first-run/all_predictions.jsonl')
dump(H/'continuity_parent_predicate_contrasts_PRIVATE.json',{'policy_cases':continuity,'predeclared_control_contrasts':[{'predeclared':t,'actual_output':controloutputs[t['input']['id']]} for t in controls if t['input']['id'] in {'C04-CONTROL-031','C04-CONTROL-032','C04-CONTROL-033','C04-CONTROL-034'}]})
original=read(R/'statistics/final_bindings_v14_CONFIRMED_r3.json');original_checks=[]
def check_bindings(x):
 if isinstance(x,dict):
  if 'path' in x and 'sha256' in x and isinstance(x['path'],str):
   p=pathlib.Path(x['path']);actual=sha(p);assert actual==x['sha256'],f'original binding changed: {p}'
   original_checks.append({'path':str(p),'sha256':actual})
  else:
   for y in x.values():check_bindings(y)
 elif isinstance(x,list):
  for y in x:check_bindings(y)
check_bindings(original['references']);check_bindings(original['third']);check_bindings(original['material']['llm_inputs']);check_bindings(original['methods']['LLM']['output'])
dump(H/'original_reference_source_baseline_preservation_QA.json',{'status':'PASS','checks':original_checks,'all_240_development_disclosed':True})
dump(H/'candidate03_candidate04_complete_changes_PRIVATE.json',{'status':'descriptive_complete_comparison_not_gold_relabeling','all_240_exposed_development':True,'all_changes':changes,'remaining_candidate04_disagreements_with_any_AI_reference':remaining,'reference_direction_counts_not_semantic_truth':directions,'note':'Every changed dimension across all three versions retained, including adverse movements. Semantic verdict is separate. No kappa threshold or output cherry-picking.'})
dump(H/'development_handoff_bindings.json',{'candidate03_preserved':True,'candidate04_requires_root_confirm_before_full_corpus':True,'all_240_exposed_development':True,'synthetic_controls_not_independent_validation':True,'all_runs':bind,'change_ledger':{'path':str(H/'candidate03_candidate04_complete_changes_PRIVATE.json'),'sha256':sha(H/'candidate03_candidate04_complete_changes_PRIVATE.json')},'candidate03_QA_sha256':sha(H/'development_actual_QA_and_changes_PRIVATE.json'),'candidate04_QA_sha256':sha(H/'candidate04_actual_QA_and_changes_PRIVATE.json'),'candidate03_prompt_sha256':sha(H/'candidate03_prompt.txt'),'candidate04_prompt_sha256':sha(H/'candidate04_prompt.txt'),'full_corpus_actual_calls_started':0,'original_reference_and_source_files_changed':False})
print(json.dumps({'changed_case_dimensions':len(changes),'directions':directions,'candidate04_remaining_disagreement_case_dimensions':len(remaining),'actual_calls_total':sum(x['attempt_n'] for x in bind)},ensure_ascii=False))

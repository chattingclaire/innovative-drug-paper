"""Audit real requests and first-valid outputs; compare without changing outputs."""
import json, pathlib, hashlib, collections, importlib.util
HERE=pathlib.Path(__file__).resolve().parent; R3=HERE.parent
DIMS=['S','E','Ec','I','F']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def lines(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def idx(p): return {r['id']:r for r in lines(p)}
spec=importlib.util.spec_from_file_location('c03_runner',HERE/'run_production_v32.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
freeze=read(HERE/'candidate04_development_freeze.json')
assert sha(HERE/'candidate04_prompt.txt')==freeze['prompt_sha256']
assert sha(HERE/'synthetic38_candidate04_expected_PRIVATE.json')==freeze['synthetic_control_expected_sha256']
execution=[]
for name,n in [('exposed240-candidate04-first-run',240),('synthetic38-candidate04-first-run',38)]:
    run=HERE/name;plan=read(run/'run_plan.json');summary=read(run/'execution_summary.json')
    assert summary['status']=='complete_actual_calls_structurally_valid'
    assert plan['model']=='gpt-5.6-sol' and plan['reasoning_effort']=='medium'
    assert plan['prompt_sha256']==freeze['prompt_sha256']==sha(run/'frozen_prompt.txt')
    assert plan['n']==n
    source=lines(run/plan['frozen_input_relative_path']);output=read(run/'all_predictions.json')
    assert not runner.v.validate({'rows':source},output)
    reconstructed=[];attempt_count=0;attempts=[]
    for batch in sorted((run/'batches').glob('batch-*')):
        selection=read(batch/'selection.json');packet=read(batch/'input.json')
        request=plan and (run/'frozen_prompt.txt').read_text()+'\n\n--- 本批冻结盲法输入 ---\n'+json.dumps(packet,ensure_ascii=False)+'\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
        assert (batch/'request.txt').read_text()==request
        valid=[]
        for at in sorted((batch/'attempts').glob('attempt-*')):
            attempt_count+=1;m=read(at/'run_metadata.json');raw=at/'raw_output.json'
            assert m['requested_model']=='gpt-5.6-sol' and m['reasoning_effort']=='medium'
            command=m['command'];assert command[command.index('--model')+1]=='gpt-5.6-sol'
            assert 'model_reasoning_effort="medium"' in command
            assert read(at/'input.json')==packet and (at/'request.txt').read_text()==request
            assert sha(at/'request.txt')==m['request_sha256'] and m['prompt_sha256']==freeze['prompt_sha256']
            assert sha(at/'events.jsonl')==m['events_sha256']
            if raw.exists(): assert sha(raw)==m['raw_output_sha256']
            ea=runner.event_audit((at/'events.jsonl').read_text())
            ok=m['exit_code']==0 and ea['completed_turns']==1 and not ea['turn_errors'] and not ea['tool_or_unknown_item_event_count'] and raw.exists() and not runner.v.validate(packet,read(raw))
            if ok:valid.append(at)
            assert ok==(m['status']=='accepted_structural_literal_zero_tools')
            attempts.append({'path':str(at),'metadata_sha256':sha(at/'run_metadata.json'),'valid':ok,'errors':m['errors']})
        assert valid and str(valid[0].relative_to(run))==selection['selected_relative_path']
        assert sha(valid[0]/'raw_output.json')==selection['selected_output_sha256']
        reconstructed.extend(read(valid[0]/'raw_output.json')['rows'])
    assert reconstructed==output['rows']
    assert reconstructed==lines(run/'all_predictions.jsonl')
    execution.append({'run':str(run),'n':n,'actual_attempts':attempt_count,'first_valid_and_hash_checks':'PASS','output_sha256':sha(run/'all_predictions.jsonl'),'summary_sha256':sha(run/'execution_summary.json'),'attempts':attempts})

new=idx(HERE/'exposed240-candidate04-first-run/all_predictions.jsonl')
old=idx(R3/'llm-v32/full-production-candidate02-material-v14-source-citation-reconciled/all_predictions.jsonl')
refs={'A':idx(R3/'reference/agent_A_final_v14.jsonl'),'C':idx(R3/'reference/agent_C_final_v14.jsonl'),'candidate':idx(R3/'statistics/final-v14/candidate_reference.jsonl')}
inputs=idx(HERE/'exposed240_inputs.jsonl')
sample={r['original_id']:r for r in read(R3/'admin/confirmation_sampling_PRIVATE.json')['sample']}
tests=read(HERE/'synthetic38_candidate04_expected_PRIVATE.json')['tests'];control=idx(HERE/'synthetic38-candidate04-first-run/all_predictions.jsonl')
control_errors=[]
for t in tests:
    p=control[t['input']['id']]
    for d in DIMS:
        if p['labels'][d]!=t['labels'][d]:control_errors.append({'id':p['id'],'dimension':d,'expected':t['labels'][d],'actual':p['labels'][d],'text':t['input']['text'],'rationale':t['rationale'],'actual_reason':p['dimension_reasons'][d]})

changes=[]
for rid in new:
    for d in DIMS:
        if new[rid]['labels'][d]!=old[rid]['labels'][d]:
            changes.append({'id':rid,'dimension':d,'component':sample[rid]['component'],'baseline':old[rid]['labels'][d],'candidate04':new[rid]['labels'][d],'references':{name:rows[rid]['labels'][d] for name,rows in refs.items()},'text':inputs[rid]['text'],'contexts':inputs[rid]['contexts'],'baseline_reason':old[rid]['dimension_reasons'][d],'new_reason':new[rid]['dimension_reasons'][d],'new_evidence':[e for e in new[rid]['evidence'] if e['dimension']==d]})
confirmed=[];boundary=[]
for r in read(HERE/'IF_semantic_diagnosis_PRIVATE.json')['records']:
    rid,d=r['id'],r['dimension'];v=new[rid]['labels'][d]
    item={'id':rid,'dimension':d,'category':r['category'],'diagnosis':r['semantic_diagnosis'],'baseline':r['baseline_prediction'],'candidate04':v,'new_reason':new[rid]['dimension_reasons'][d],'references':r['references_preserved']}
    if r['category']=='repairable_execution_misuse':item['corrected_on_predeclared_semantic_basis']=v!=r['baseline_prediction'];confirmed.append(item)
    else:boundary.append(item)

# Diagnostic counts only. Probability and challenge components stay separate.
comparisons=[]
for component in sorted({s['component'] for s in sample.values()}):
  selected=[rid for rid in new if sample[rid]['component']==component]
  for ref,rr in refs.items():
    for d in DIMS:
      entry={'component':component,'reference':ref,'dimension':d,'n':len(selected),'development_only':True,'kappa_is_not_a_gate':True}
      for method,preds in [('baseline',old),('candidate04',new)]:
        cells=collections.Counter();na=0
        for rid in selected:
          y,p=rr[rid]['labels'][d],preds[rid]['labels'][d]
          if type(y)!=int or y not in (0,1):na+=1;continue
          cells['TP' if p==y==1 else 'TN' if p==y==0 else 'FP' if p==1 else 'FN']+=1
        entry[method]={**{k:cells[k] for k in ['TP','FP','FN','TN']},'NA':na}
      comparisons.append(entry)

report={'status':'technical_audit_complete_semantic_review_required','method_id':'LLM-v32-candidate04-development','strict_independent_validation':False,'all_240_development_exposed':True,'baseline_preserved':True,'prompt_sha256':freeze['prompt_sha256'],'execution':execution,'synthetic_control_case_n':len(tests),'synthetic_control_dimension_n':len(tests)*5,'synthetic_control_errors':control_errors,'confirmed_misuse_corrected_n':sum(x['corrected_on_predeclared_semantic_basis'] for x in confirmed),'confirmed_misuse_n':len(confirmed),'confirmed_misuse_review':confirmed,'reference_boundary_review':boundary,'changes_n':len(changes),'changes':changes,'diagnostic_confusions_separate_components':comparisons,'automatic_semantic_freeze':False,'no_raw_output_or_reference_edits':True}
dump(HERE/'candidate04_actual_QA_and_changes_PRIVATE.json',report)
preserved=read(HERE/'candidate03_preservation_hashes.json')['files']
assert all(sha(HERE/p)==h for p,h in preserved.items()),'candidate03 artifact changed'
print(json.dumps({k:report[k] for k in ['status','synthetic_control_errors','confirmed_misuse_corrected_n','confirmed_misuse_n','changes_n']},ensure_ascii=False))

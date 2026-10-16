"""Single finite coding execution; no adaptive editing, no models or gold."""
import copy,hashlib,json,sys,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'runtime'))
import policy_coding_v27 as coding
import source_context_adapter_v34 as adapter
import common_innovation_relations14 as I
import common_medicine_access14 as F
from content_only_impact_scope import scope
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    marker=H/'finite_execution_started.json'
    if marker.exists():raise RuntimeError('Finite execution already started; no rerun permitted in this attempt.')
    plan=json.loads((H/'finite_check_plan_before_execution.json').read_text())
    assert sha(H/'source04_selected32_inputs.jsonl')==plan['actual_input_sha256']
    assert sha(H/'synthetic24_inputs.jsonl')==plan['synthetic_input_sha256']
    marker.write_text(json.dumps(dict(start_time=time.time(),runtime_sha256={p.name:sha(p) for p in sorted((H/'runtime').glob('*.py'))},plan_sha256=sha(H/'finite_check_plan_before_execution.json')),indent=2))
    actual=[json.loads(x) for x in (H/'source04_selected32_inputs.jsonl').open()]
    synthetics=[json.loads(x) for x in (H/'synthetic24_inputs.jsonl').open()]
    target={r['id']:r for r in plan['actual_checks']};results=[];start=time.time()
    out=H/'finite_actual32_outputs.jsonl'
    with out.open('x') as handle:
        for n,row in enumerate(actual+synthetics,1):
            k=row['id'];record=row['input'];isreal=n<=len(actual)
            goal=target[k] if isreal else row
            expected=goal.get('expected_development_mechanism',goal.get('expected_mechanism',{}))
            observation=goal.get('role')=='unresolved_boundary_observation'
            try:
                r=coding.code_unit(copy.deepcopy(record));error=None
            except Exception as e:
                r=None;error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
            labels=r.get('labels') if r else None
            passed=all(labels is not None and labels.get(d)==value for d,value in expected.items()) if expected else None
            item=dict(id=k,kind='actual_source_development' if isreal else row['kind'],input_sha256=hashlib.sha256(json.dumps(record,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),unit_text=record['unit_text'],source_path=record.get('unit_source') or record.get('source'),source_sha256=record.get('unit_source_sha256') or record.get('source_sha256'),scope=scope(record),expected_development_mechanism=expected,boundary_observation=observation,check_pass=passed,error=error,result=r)
            results.append(item)
            if isreal:handle.write(json.dumps(item,ensure_ascii=False)+'\n');handle.flush()
            print(json.dumps(dict(n=n,id=k,labels=labels,check_pass=passed,error=error and error['message']),ensure_ascii=False),flush=True)
    # Invalid binding controls are independent mutations of the exact actual
    # source input; direct module checks preserve unknown as pending, not zero.
    rows={r['id']:r['input'] for r in actual}
    mutations=[('I_actual_source_hash_invalid','RECODE25-03476','I'),('F_actual_source_hash_invalid','RECODE25-04615','F'),('complete_list_content_hash_invalid','RECODE25-00290','F'),('decimal_wrong_actual_chapter','RECODE25-03894','I')]
    controls=[]
    for name,key,dim in mutations:
        try:
            record=adapter.prepare(copy.deepcopy(rows[key]))
            if name.endswith('source_hash_invalid'):record['unit_source_sha256']='0'*64
            elif name=='complete_list_content_hash_invalid':record['complete_following_list_v11']['contexts_sha256']='0'*64
            else:
                for group in record['typed_contexts_v34']:
                    if 'reference_address' in group:group['reference_address']=group['reference_address'].replace('化学药品与生物制品','另一个章节')
            r=(I if dim=='I' else F).revise(record,dict(evidence=[],judgement_status='determined'))
            pending=bool((r.get('common14_pending_dimensions') or {}).get(dim));positive=any(e['dimension']==dim for e in r['evidence'])
            item=dict(id=name,kind='actual_source_binding_mutation',source_record_locator=key,pending_dimension=dim,observed_pending=pending,positive_evidence_emitted=positive,check_pass=pending and not positive,result=r)
        except Exception as error:item=dict(id=name,kind='actual_source_binding_mutation',check_pass=False,error=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
        controls.append(item);print(json.dumps({k:v for k,v in item.items() if k!='result'},ensure_ascii=False),flush=True)
    report=dict(manual_sha256=I.MANUAL_SHA256,plan_sha256=sha(H/'finite_check_plan_before_execution.json'),source04_input_sha256=plan['source_input_sha256'],selected_actual_input_sha256=plan['actual_input_sha256'],actual_output_sha256=sha(out),actual_count=len(actual),synthetic_count=len(synthetics),binding_mutation_count=len(controls),coding_pass_count=1,full_corpus_coding_performed=False,model_calls=0,elapsed_seconds=time.time()-start,independent_validity_claimed=False,formal_adoption=False,actual_and_synthetic_results=results,binding_mutation_results=controls,all_failures_retained=True,failed_checks=[r['id'] for r in results+controls if r.get('check_pass') is False],actual_pending_or_errors=[r['id'] for r in results[:len(actual)] if r.get('error') or (r.get('result') or {}).get('judgement_status')=='undetermined'])
    (H/'finite_execution14_actual01.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(dict(actual_count=len(actual),synthetic_count=len(synthetics),binding_mutations=len(controls),failed=report['failed_checks'],pending_or_errors=report['actual_pending_or_errors'],report_sha256=sha(H/'finite_execution14_actual01.json')),ensure_ascii=False),flush=True)
if __name__=='__main__':main()

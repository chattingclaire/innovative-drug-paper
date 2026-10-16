"""Independently reconstruct selected model calls; never assign or repair labels."""
from pathlib import Path
from collections import Counter
import hashlib, importlib.util, json

OUT=Path(__file__).resolve().parent
HERE=OUT/'llm-v29'; RUN=HERE/'production-25-v29'
ROOT=OUT.parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def lines(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
spec=importlib.util.spec_from_file_location('literal_validator',ROOT/'outputs/llm-v29-method-audit-20261005/validate_binary_output.py')
validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)

def main():
    final=read(RUN/'final_manifest.json')
    effective=lines(HERE/'effective_blind_inputs_v29.jsonl')
    base=lines(HERE/'frozen_blind_inputs_v29.jsonl')
    predictions=lines(RUN/'all_predictions.jsonl')
    shared=lines(HERE/'rule_inputs_v29_shared.jsonl')
    assert len(effective)==len(base)==len(predictions)==len(shared)==4924
    assert [r['id'] for r in effective]==[r['id'] for r in predictions]==[r['id'] for r in shared]
    assert len({r['id'] for r in effective})==4924
    assert final['status']=='complete_validated_full_corpus'
    assert final['predictions_sha256']==sha(RUN/'all_predictions.jsonl')
    assert final['effective_input_sha256']==sha(HERE/'effective_blind_inputs_v29.jsonl')
    assert final['base_input_sha256']==sha(HERE/'frozen_blind_inputs_v29.jsonl')
    assert final['requested_model']=='gpt-5.6-sol' and final['reasoning_effort']=='medium'
    assert all(x['text']==b['text'] for x,b in zip(effective,base))
    for x,r in zip(effective,shared):
        assert x['text']==r['input']['unit_text'],x['id']
        assert x['contexts']==r['input']['llm_v29_shared_context'],x['id']
    issues=read(RUN/'all_issue_records.json')
    output={'protocol_version':'CAL-5D-20260926-v1.3','execution_version':'LLM-binary-v29','release_stage':'final_binary_labels','rows':predictions,'issue_records':issues}
    errors=validator.validate({'rows':effective},output)
    assert not errors,errors
    actual_by_id={r['id']:r for r in effective}
    trace=[]; reconstructed=[]; call_paths=set(); selected_tools=[]
    for number in range(1,198):
        batch=RUN/'batches'/f'batch-{number:04d}'
        selected=next((batch/n for n in ['no_retrieval_output.json','repaired_output.json','raw_output.json'] if (batch/n).exists()))
        answer=read(selected); packet=effective[(number-1)*25:number*25]
        assert [r['id'] for r in answer['rows']]==[r['id'] for r in packet],batch.name
        assert not validator.validate({'rows':packet},answer),batch.name
        # Full-batch reruns must trace exactly to an actual raw response with the
        # effective input. Historical calls are preserved but cannot supply labels.
        full_calls=[]
        for raw in batch.rglob('raw_output.json'):
            if 'history-' in str(raw.relative_to(batch)): continue
            inp=raw.parent/'input.json'
            if not inp.exists(): continue
            try: raw_obj=read(raw); call_rows=read(inp)['rows']
            except (ValueError,KeyError): continue
            if raw_obj==answer and call_rows==packet: full_calls.append(raw.parent)
        if full_calls:
            chosen=sorted(full_calls,key=lambda p: (p==batch,str(p)))[0]
            sources=[chosen]
            row_trace={r['id']:str(chosen/'raw_output.json') for r in answer['rows']}
        else:
            repair=read(batch/'repair_manifest.json')
            assert repair['status']=='accepted_after_isolated_model_rerun',repair
            assert read(batch/'input.json')['rows']==packet
            original=read(batch/'raw_output.json')
            originals={r['id']:r for r in original['rows']}
            sources=[batch];row_trace={}
            repair_id=repair['repaired_id']
            for row in answer['rows']:
                if row['id']!=repair_id:
                    assert row==originals[row['id']],row['id']
                    row_trace[row['id']]=str(batch/'raw_output.json')
                else:
                    candidates=[]
                    for raw in (batch/'repairs').rglob('raw_output.json'):
                        inp=raw.parent/'input.json'
                        if inp.exists() and read(inp)['rows']==[actual_by_id[row['id']]] and read(raw)['rows']==[row]: candidates.append(raw.parent)
                    assert candidates,row['id']
                    chosen=sorted(candidates)[0];sources.append(chosen)
                    row_trace[row['id']]=str(chosen/'raw_output.json')
        for source in sources:
            events=source/'events.jsonl';assert events.exists(),source
            call_paths.add(str(source))
            for event in lines(events):
                item=event.get('item',{})
                if item and item.get('type') not in {'agent_message','reasoning'}:
                    selected_tools.append({'path':str(events),'event_type':event.get('type'),'item_type':item.get('type')})
        reconstructed.extend(answer['rows'])
        trace.append({'batch':batch.name,'selected_output':str(selected),'selected_output_sha256':sha(selected),'selected_execution_paths':[str(s) for s in sources],'row_to_actual_raw_response':row_trace})
    assert reconstructed==predictions,'Global predictions must equal actual selected calls'
    assert not selected_tools,selected_tools
    hashes=read(RUN/'execution_artifact_hashes.json');checked=0
    for record in hashes['records']:
        for relative,digest in record['files'].items():
            assert sha(RUN/relative)==digest,relative;checked+=1
    assert final['execution_artifact_hashes_sha256']==sha(RUN/'execution_artifact_hashes.json')
    assert final['stability_comparison_v2_sha256']==sha(HERE/'stability_comparison_v2.json')
    report={'status':'passed','n':4924,'dimension_labels_checked':24620,'whole_output_literal_and_structure_errors':errors,'predictions_sha256':sha(RUN/'all_predictions.jsonl'),'effective_input_sha256':sha(HERE/'effective_blind_inputs_v29.jsonl'),'shared_rule_input_sha256':sha(HERE/'rule_inputs_v29_shared.jsonl'),'input_context_equality_n':4924,'unit_texts_unchanged_n':4924,'selected_tool_event_count':len(selected_tools),'selected_actual_execution_count':len(call_paths),'hashed_artifacts_checked':checked,'mechanically_edited_output_selected':False,'selected_batch_trace':trace,'scope':'Structure, literal evidence and execution provenance only. Semantic correctness and human validation require separate evidence.'}
    target=OUT/'最终LLM执行独立核验.json';target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='selected_batch_trace'},ensure_ascii=False))

if __name__=='__main__':main()

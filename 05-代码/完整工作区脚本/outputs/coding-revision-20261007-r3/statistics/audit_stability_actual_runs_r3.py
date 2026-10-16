"""Technical provenance QA of nine frozen repeat/order-sensitivity actual runs.

No reference labels read, no best-run selection and no agreement table produced.
This checks the saved original requests/responses, not semantic correctness.
"""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import jsonschema
import statistical_core_r3 as c

RUN=Path(__file__).resolve().parents[1]
LLM=RUN/'llm-v32'
OUT=Path(__file__).resolve().parent


def read(path):return json.loads(path.read_text())
def binding(path):return {'path':str(path),'sha256':c.sha(path)}
def frozen_validator(path):
    spec=importlib.util.spec_from_file_location('saved_validation',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def audit_run(directory,expected_ids,expected_prompt_sha,expected_input_sha):
    summary=read(directory/'execution_summary.json');plan=read(directory/'run_plan.json')
    assert summary['status']=='complete_actual_calls_structurally_valid'
    assert summary['accepted_batch_count']==summary['expected_batch_count']==summary['recorded_batch_count']==1
    assert summary['n']==plan['n']==len(expected_ids)==25
    assert summary['plan_sha256']==c.sha(directory/'run_plan.json')
    assert summary['prompt_sha256']==plan['prompt_sha256']==expected_prompt_sha==c.sha(directory/'frozen_prompt.txt')
    assert summary['input_sha256']==plan['input_sha256']==expected_input_sha==c.sha(directory/'frozen_input.jsonl')
    assert summary['output_sha256']==c.sha(directory/'all_predictions.jsonl')
    for name,key in [('frozen_schema.json','schema_sha256'),('frozen_validator.py','validator_sha256'),('frozen_runner.py','runner_sha256')]:
        assert c.sha(directory/name)==plan[key]
    inputs=[json.loads(line) for line in (directory/'frozen_input.jsonl').read_text().splitlines() if line]
    assert [r['id'] for r in inputs]==expected_ids
    packet=read(directory/'batches/batch-0001/input.json')
    assert packet['rows']==inputs
    prompt=(directory/'frozen_prompt.txt').read_text()
    expected_request=prompt+'\n\n--- 本批冻结盲法输入 ---\n'+json.dumps(packet,ensure_ascii=False)+'\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
    assert (directory/'batches/batch-0001/request.txt').read_text()==expected_request
    selection=read(directory/'batches/batch-0001/selection.json')
    assert selection['status']=='accepted_first_valid_actual_attempt'
    assert selection['ids']==expected_ids and selection['selection_uses_metric_or_label_values'] is False
    validator=frozen_validator(directory/'frozen_validator.py')
    schema=read(directory/'frozen_schema.json')
    first_valid=None;attempts=[]
    for entry in selection['attempts']:
        attempt=directory/entry['relative_path'];meta=read(attempt/'run_metadata.json')
        assert c.sha(attempt/'run_metadata.json')==entry['metadata_sha256']
        assert (attempt/'request.txt').read_text()==expected_request
        assert read(attempt/'input.json')==packet
        assert meta['request_sha256']==hashlib.sha256(expected_request.encode()).hexdigest()
        assert meta['input_sha256']==c.sha(attempt/'input.json')
        assert meta['prompt_sha256']==expected_prompt_sha and meta['label_or_metric_selection'] is False
        for name,key in [('raw_output.json','raw_output_sha256'),('events.jsonl','events_sha256'),
                         ('raw_stderr.txt','stderr_sha256'),('tool_event_audit.json','tool_event_audit_sha256'),
                         ('validation.json','validation_sha256')]:
            if meta[key] is not None:assert c.sha(attempt/name)==meta[key]
        events=[json.loads(line) for line in (attempt/'events.jsonl').read_text().splitlines() if line.strip()]
        bad_items=[event for event in events if event['type'].startswith('item.')
                   and event.get('item',{}).get('type')!='agent_message']
        assert not bad_items and meta['tool_event_count']==0
        if meta['status']=='accepted_structural_literal_zero_tools':
            assert meta['exit_code']==0 and not meta['errors']
            raw=read(attempt/'raw_output.json')
            jsonschema.Draft202012Validator(schema).validate(raw)
            assert not validator.validate(packet,raw)
            if first_valid is None:first_valid=entry['relative_path']
        attempts.append({'attempt':entry['attempt'],'status':meta['status'],
                         'request_sha256':meta['request_sha256'],'tool_event_count':meta['tool_event_count'],
                         'raw_output_sha256':meta['raw_output_sha256'],'elapsed_seconds':meta['elapsed_seconds']})
    assert selection['selected_relative_path']==first_valid
    selected=directory/first_valid;raw=read(selected/'raw_output.json')
    assert c.sha(selected/'raw_output.json')==selection['selected_output_sha256']
    aggregate=read(directory/'all_predictions.json')
    lines=[json.loads(line) for line in (directory/'all_predictions.jsonl').read_text().splitlines() if line]
    assert aggregate['rows']==raw['rows']==lines
    assert aggregate['issue_records']==raw['issue_records']
    assert summary['actual_attempt_count']==len(attempts)
    assert summary['metric_or_reference_label_based_selection'] is False
    return {'directory':str(directory),'n':25,'status':'pass_technical_provenance_and_literal_evidence',
            'summary':binding(directory/'execution_summary.json'),'plan':binding(directory/'run_plan.json'),
            'output':binding(directory/'all_predictions.jsonl'),'selected_raw':binding(selected/'raw_output.json'),
            'input':binding(directory/'frozen_input.jsonl'),'packet':binding(directory/'batches/batch-0001/input.json'),
            'request':binding(selected/'request.txt'),'prompt':binding(directory/'frozen_prompt.txt'),
            'attempts':attempts,'first_structurally_valid_actual_output_retained':True}


def main():
    pre=read(LLM/'stability_preselection_freeze.json')
    material=read(LLM/'stability_material_v11_binding.json')
    perturb=read(LLM/'prompt_order_perturbation_freeze.json')
    assert c.sha(LLM/'stability_preselection_freeze.json')==material['selection_freeze_sha256']
    original=c.jsonl(RUN/'effective_blind_inputs_v11.jsonl')
    assert c.sha(RUN/'effective_blind_inputs_v11.jsonl')==material['input_sha256']
    audits=[];requests={};packets={}
    for group in material['bindings']:
        batch=group['production_batch'];ids=group['all_ids'];ip=Path(group['input_path'])
        assert c.sha(ip)==group['input_sha256']
        assert [json.loads(line) for line in ip.read_text().splitlines() if line]==[original[rid] for rid in ids]
        for purpose in ('stability-base-repeat-2','stability-base-repeat-3','stability-order-perturbation'):
            directory=LLM/f'{purpose}-batch-{batch:04d}'
            psha=perturb['perturbed_prompt_sha256'] if purpose.endswith('perturbation') else pre['prompt_sha256']
            audit=audit_run(directory,ids,psha,group['input_sha256'])
            audit.update({'production_batch':batch,'purpose':purpose});audits.append(audit)
            requests[purpose,batch]=audit['request']['sha256']
            packets[purpose,batch]=read(Path(audit['packet']['path']))
        assert requests['stability-base-repeat-2',batch]==requests['stability-base-repeat-3',batch]
        assert packets['stability-base-repeat-2',batch]==packets['stability-base-repeat-3',batch]==packets['stability-order-perturbation',batch]
        base=(LLM/f'stability-base-repeat-2-batch-{batch:04d}/frozen_prompt.txt').read_text()
        altered=(LLM/f'stability-order-perturbation-batch-{batch:04d}/frozen_prompt.txt').read_text()
        assert altered.endswith(base) and len(altered)>len(base)
    result={'status':'pass_nine_actual_runs_technical_QA','created_at':datetime.datetime.now().astimezone().isoformat(),
        'material_version':'v11','actual_completed_run_n':9,'actual_selected_output_rows':225,
        'actual_attempt_n':sum(len(a['attempts']) for a in audits),
        'all_selected_and_recorded_attempt_tool_event_count':sum(x['tool_event_count'] for a in audits for x in a['attempts']),
        'base_repeats_identical_full_request_bytes':True,'order_perturbation_same_packet_base_prompt_preserved':True,
        'original_production_reference_pending':True,'final_material_equivalence_pending':True,
        'reference_labels_read':False,'semantic_correctness_claimed':False,
        'bindings':{'preselection':binding(LLM/'stability_preselection_freeze.json'),
            'material':binding(LLM/'stability_material_v11_binding.json'),
            'perturbation':binding(LLM/'prompt_order_perturbation_freeze.json')},
        'runs':audits,'script_sha256':c.sha(Path(__file__)),
        'limits':['No agreement or accuracy table produced before root final binding.',
                  'Technical validation establishes traceable actual requests, coverage and literal evidence, not semantic truth.',
                  'Production first output and final v12 material compatibility remain to be bound; v11 repeats cannot silently substitute changed v12 requests.']}
    target=OUT/'LLM九组实际重复与顺序微扰技术QA-v11.json'
    assert not target.exists();c.write_json(target,result)
    print(json.dumps({'status':result['status'],'runs':9,'attempts':result['actual_attempt_n'],
                      'tool_events':result['all_selected_and_recorded_attempt_tool_event_count'],'path':str(target)},ensure_ascii=False))


if __name__=='__main__':main()

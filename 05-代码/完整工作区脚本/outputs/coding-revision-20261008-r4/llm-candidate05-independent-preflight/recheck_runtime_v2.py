"""No-provider tests of v2 event/output binding and first-valid retry driver."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import sys
import types

sys.dont_write_bytecode=True
ROOT=Path('/PROJECT_ROOT')
PREP=ROOT/'outputs/coding-revision-20261008-r4/llm-candidate05-preparation'
OUT=Path(__file__).resolve().parent
RUNTIME=PREP/'runtime-v2/run_production_v32.py'
DIMS=['S','E','Ec','I','F']


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(Path(p).resolve()),'sha256':sha(p)}
def clone(x):return copy.deepcopy(x)


def main():
    before={str(p.relative_to(PREP)):sha(p) for p in PREP.rglob('*') if p.is_file()}
    spec=importlib.util.spec_from_file_location('independent_runtime_v2_tests',RUNTIME)
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    packet={'rows':[{'id':'INDEPENDENT-V2-MOCK-ONLY','text':'一般申请流程。','contexts':{}}]}
    raw={'protocol_version':'CAL-5D-20260926-v1.3','execution_version':'LLM-binary-v32',
         'release_stage':'final_binary_labels','rows':[{'id':'INDEPENDENT-V2-MOCK-ONLY',
         'labels':{d:0 for d in DIMS},'dimension_reasons':{d:'未讨论本维。' for d in DIMS},
         'evidence':[],'fairness_subtypes':[],'innovation_subtypes':[],
         'safety_quality_basis':'no_quality_basis'}],'issue_records':[]}
    assert not runner.v.validate(packet,raw)
    def event_stream(texts,turn=True,prefix=None):
        es=list(prefix or [])+[{'type':'item.completed','item':{'type':'agent_message','text':t}} for t in texts]
        if turn:es.append({'type':'turn.completed'})
        return '\n'.join(json.dumps(x,ensure_ascii=False) for x in es)+'\n'
    normal=json.dumps(raw,ensure_ascii=False)
    unequal=clone(raw);unequal['rows'][0]['dimension_reasons']['I']='另一份理由。'
    boolean=clone(raw);boolean['rows'][0]['labels']['I']=False
    floating=clone(raw);floating['rows'][0]['labels']['I']=0.0
    reordered={k:raw[k] for k in reversed(list(raw))}
    cases=[
      ('exact_good',event_stream([normal]),raw,True,True),
      ('JSON_key_order_good',event_stream([json.dumps(reordered,ensure_ascii=False)]),raw,True,True),
      ('JSON_whitespace_unicode_good',event_stream([json.dumps(raw,ensure_ascii=True,indent=3)]),raw,True,True),
      ('missing_message',event_stream([]),raw,True,False),
      ('two_messages',event_stream([normal,normal]),raw,True,False),
      ('final_not_JSON',event_stream(['not JSON']),raw,True,False),
      ('final_text_not_string',event_stream([None]),raw,True,False),
      ('raw_final_mismatch',event_stream([json.dumps(unequal,ensure_ascii=False)]),raw,True,False),
      ('bool_vs_int_mismatch',event_stream([json.dumps(boolean,ensure_ascii=False)]),raw,True,False),
      ('float_vs_int_mismatch',event_stream([json.dumps(floating,ensure_ascii=False)]),raw,True,False),
      ('raw_unavailable',event_stream([normal]),None,False,False),
      ('JSON_array_order_mismatch',event_stream([json.dumps({'rows':[2,1]})]),{'rows':[1,2]},True,False),
    ]
    pure=[]
    for name,events,raw_obj,available,expected_pass in cases:
        result=runner.event_output_binding_audit(events,raw_obj,available)
        actual=not result['errors']
        assert actual==expected_pass,(name,result)
        pure.append({'case':name,'expected_pass':expected_pass,'observed_pass':actual,'audit':result})

    original_run=runner.subprocess.run
    attempts=[]
    for name,events,raw_obj,available,expected_pass in cases[:11]:
        call_list=[]
        def fake_run(command,**kwargs):
            call_list.append(command)
            if available:Path(command[command.index('--output-last-message')+1]).write_text(json.dumps(raw_obj,ensure_ascii=False))
            return types.SimpleNamespace(returncode=0,stdout=events,stderr='')
        runner.subprocess.run=fake_run
        dest=OUT/'mock-v2-attempts'/name
        m=runner.run_attempt(dest,packet,'MOCK NEVER SENT','MOCK-PROMPT-SHA','MOCK-VERSION','MOCK-CLI-SHA',1)
        accepted=m['status']=='accepted_structural_literal_zero_tools'
        assert accepted==expected_pass,(name,m)
        audit=json.loads((dest/'event_output_binding_audit.json').read_text())
        assert m['event_output_binding_audit_sha256']==sha(dest/'event_output_binding_audit.json')
        assert m['completed_agent_message_count']==audit['completed_agent_message_count']
        assert m['raw_output_matches_unique_completed_agent_message']==audit['event_raw_full_object_equal']
        attempts.append({'case':name,'expected_accepted':expected_pass,'observed_accepted':accepted,
                         'errors':m['errors'],'binding':bind(dest/'event_output_binding_audit.json'),
                         'metadata':bind(dest/'run_metadata.json'),'mock_subprocess_calls':len(call_list)})

    # Exercise the actual bounded retry/selection main with all provider calls
    # replaced, storing runs under OUT rather than the prepared runtime directory.
    driver_home=OUT/'mock-v2-main-driver'
    driver_home.mkdir(exist_ok=True)
    mock_input=driver_home/'input.jsonl'
    mock_input.write_text(json.dumps(packet['rows'][0],ensure_ascii=False)+'\n')
    original_here=runner.HERE;original_argv=sys.argv[:];original_sleep=runner.time.sleep
    runner.HERE=driver_home;runner.time.sleep=lambda seconds:None
    driver_results=[]
    for name,sequence,expected_exit,selected in [
      ('two_fail_then_first_valid',[event_stream([json.dumps(unequal,ensure_ascii=False)]),event_stream([]),event_stream([normal])],0,'attempt-03'),
      ('stop_at_first_valid',[event_stream([normal])],0,'attempt-01'),
      ('three_fail_stop',[event_stream([json.dumps(unequal,ensure_ascii=False)])]*3,2,None),
    ]:
        exec_calls=[];version_calls=[]
        def driver_fake_run(command,**kwargs):
            if command[1:]==['--version']:
                version_calls.append(command)
                return types.SimpleNamespace(returncode=0,stdout='MOCK-VERSION\n',stderr='')
            assert command[1]=='exec'
            idx=len(exec_calls);assert idx<len(sequence),'Exceeded declared mock attempt sequence'
            exec_calls.append({'command':command,'request':kwargs.get('input')})
            Path(command[command.index('--output-last-message')+1]).write_text(normal)
            return types.SimpleNamespace(returncode=0,stdout=sequence[idx],stderr='')
        runner.subprocess.run=driver_fake_run
        sys.argv=[str(RUNTIME),'--input',str(mock_input),'--expected-input-sha256',sha(mock_input),
                  '--prompt',str(PREP/'candidate05_prompt_frozen.txt'),'--expected-n','1',
                  '--run-name',name,'--batch-size','25','--workers','1','--max-attempts','3']
        exit_code=0
        with contextlib.redirect_stdout(io.StringIO()):
            try:runner.main()
            except SystemExit as e:exit_code=e.code
        assert exit_code==expected_exit
        run=driver_home/name;selection=json.loads((run/'batches/batch-0001/selection.json').read_text())
        assert len(exec_calls)==len(sequence)<=3
        assert len({x['request'] for x in exec_calls})==1,'Technical retries changed request'
        selected_actual=Path(selection['selected_relative_path']).name if selection['selected_relative_path'] else None
        assert selected_actual==selected,(selected_actual,selected)
        assert len(list((run/'batches/batch-0001/attempts').glob('attempt-*')))==len(sequence)
        driver_results.append({'case':name,'exit_code':exit_code,'mock_exec_calls':len(exec_calls),
                               'mock_version_calls':len(version_calls),'identical_request_for_retries':True,
                               'selected_attempt':selected_actual,'expected_selection':selected,
                               'all_attempts_preserved':True,'selection':bind(run/'batches/batch-0001/selection.json'),
                               'summary':bind(run/'execution_summary.json')})
    runner.subprocess.run=original_run;runner.HERE=original_here;runner.time.sleep=original_sleep;sys.argv=original_argv
    after={str(p.relative_to(PREP)):sha(p) for p in PREP.rglob('*') if p.is_file()}
    modified_existing=[p for p,v in before.items() if after.get(p)!=v]
    assert not modified_existing,'Existing preparation files changed during test'
    report={'status':'V2_TECHNICAL_GATE_RECHECK_PASS_NO_ACTUAL_MODEL_CALLS',
      'created_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),
      'real_model_calls':0,'real_CLI_invocations':0,'network_calls':0,
      'pure_gate_cases':pure,'mock_run_attempt_cases':attempts,'mock_actual_retry_driver_cases':driver_results,
      'all_pure_gate_cases_passed':len(pure),'all_run_attempt_cases_passed':len(attempts),
      'all_retry_driver_cases_passed':len(driver_results),
      'resolved_v1_blocker':'Unique completed agent_message JSON equality to raw output is required before technical acceptance; failed mismatches are preserved and identical requests retry at most3, stopping at the first valid attempt.',
      'schema_validator_unchanged':sha(PREP/'runtime-v2/output_schema_codex_compatible.json')==sha(PREP/'runtime/output_schema_codex_compatible.json') and sha(PREP/'runtime-v2/validate_binary_output.py')==sha(PREP/'runtime/validate_binary_output.py'),
      'existing_preparation_files_modified':modified_existing,
      'concurrently_added_files_not_modified_by_this_review':sorted(set(after)-set(before)),
      'input_bindings':[bind(RUNTIME),bind(PREP/'runtime-v2/output_schema_codex_compatible.json'),bind(PREP/'runtime-v2/validate_binary_output.py'),bind(PREP/'candidate05_prompt_frozen.txt')],
      'review_code':bind(Path(__file__)),
      'scope_boundary':'Technical v2 function and actual retry driver tested with mocked subprocess only. Final v2 wrapper/freeze/post-audit dependency binding review remains separate before any root-authorized actual run.'}
    target=OUT/'runtime_v2_gate_recheck.json';target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'report':str(target),'sha256':sha(target),
                      'pure_cases':len(pure),'mock_attempts':len(attempts),'mock_retry_drivers':len(driver_results),
                      'real_model_calls':0},ensure_ascii=False))


if __name__=='__main__':main()

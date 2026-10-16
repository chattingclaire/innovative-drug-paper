"""Synthetic local contract tests only; never launch CLI or read independent16."""
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode=True
import candidate08_support as s


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def main():
    results=[]
    def passed(name):results.append({'test':name,'status':'PASS'})
    def reject(name,fn):
        try:fn()
        except (AssertionError,KeyError,ValueError,FileNotFoundError):passed(name)
        else:raise AssertionError('Expected rejection: '+name)
    plan=s.read(s.PLAN);s.check_plan(plan);passed('17 logical / 51 attempts ordered phase plan and all input hashes')
    auth={'authorized':True,'design_freeze_sha256':'mock','scope_run_keys':plan['scope_run_keys'],'scope_sizes':plan['scope_sizes'],
        'model':'gpt-5.6-sol','reasoning_effort':'medium','max_logical_requests':17,'max_technical_attempts':51,
        'first_technically_valid_only':True,'semantic_retry_allowed':False,'full_corpus_or_adoption_allowed':False,'phase_semantic_gate_required':True}
    s.check_authorization(auth,'mock',plan);passed('bounded authorization accepted')
    for key,value in [('authorized',False),('design_freeze_sha256','wrong'),('scope_run_keys',[]),('scope_sizes',[24,16,62,24,20,4924]),
        ('model','other'),('max_logical_requests',18),('max_technical_attempts',52),('first_technically_valid_only',False),
        ('semantic_retry_allowed',True),('full_corpus_or_adoption_allowed',True),('phase_semantic_gate_required',False)]:
        bad=copy.deepcopy(auth);bad[key]=value
        reject('authorization rejects '+key,lambda bad=bad:s.check_authorization(bad,'mock',plan))
    old_here,old_runtime=s.HERE,s.RUNTIME
    with tempfile.TemporaryDirectory(prefix='candidate08-no-model-selftest-') as tmp:
        s.HERE=Path(tmp);s.RUNTIME=Path(tmp)/'runtime'
        phase=plan['phases'][0]
        runs=[r for r in plan['runs'] if r['run_key'] in phase['run_keys']]
        for r in runs:
            p=s.RUNTIME/r['run_name']/'all_predictions.json';p.parent.mkdir(parents=True);p.write_text('{}')
        qa=s.HERE/'execution-audit/new-controls/candidate08_technical_QA.json';qa.parent.mkdir(parents=True)
        qa.write_text(json.dumps({'status':'PASS_TECHNICAL_ONLY_SEMANTIC_REVIEW_PENDING','completed_run_keys':phase['run_keys']}))
        report=s.HERE/'mock-semantic-report.json';report.write_text('{}')
        gate={'status':'PASS_NO_CONFIRMED_SEMANTIC_ERROR','phase':'new-controls','design_freeze_sha256':'mock',
            'root_reviewed_and_approved_to_continue':True,'confirmed_semantic_error_count':0,
            'all_rows_all_five_dimensions_and_fields_reviewed':True,'boundary_disputes_separately_retained_not_forced':True,
            'run_keys':phase['run_keys'],'reviewed_rows':40,'reviewed_dimension_cells':200,
            'actual_output_bindings':[s.binding(s.RUNTIME/r['run_name']/'all_predictions.json') for r in runs],
            'semantic_review_report_bindings':[s.binding(report)],'technical_QA_binding':s.binding(qa)}
        s.check_phase_gate(gate,'new-controls','mock',plan);passed('complete phase gate accepted with output hashes')
        for key,value in [('status','FAIL'),('root_reviewed_and_approved_to_continue',False),('confirmed_semantic_error_count',1),
            ('all_rows_all_five_dimensions_and_fields_reviewed',False),('reviewed_rows',24),('reviewed_dimension_cells',199),
            ('run_keys',['new24']),('actual_output_bindings',[]),('semantic_review_report_bindings',[])]:
            bad=copy.deepcopy(gate);bad[key]=value
            reject('phase gate rejects '+key,lambda bad=bad:s.check_phase_gate(bad,'new-controls','mock',plan))
    s.HERE,s.RUNTIME=old_here,old_runtime
    runner=load('candidate08_runner_test',s.RUNTIME/'run_production_v32.py')
    raw={'x':1,'y':[0,True]}
    def events(messages):return '\n'.join(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':json.dumps(m)}}) for m in messages)
    assert not runner.event_output_binding_audit(events([raw]),raw,True)['errors'];passed('unique completed agent message equals raw')
    for name,messages,out,available in [('no message',[],raw,True),('two messages',[raw,raw],raw,True),('raw mismatch',[raw],{'x':2},True),
        ('bool/int',[{'x':True}],{'x':1},True),('float/int',[{'x':1.0}],{'x':1},True),('missing raw',[raw],None,False)]:
        assert runner.event_output_binding_audit(events(messages),out,available)['errors'];passed('event binding rejects '+name)
    assert not runner.event_output_binding_audit(events([{'b':2,'a':1}]),{'a':1,'b':2},True)['errors'];passed('key order ignored, JSON number/bool types retained')
    audit=load('candidate08_fields_test',s.HERE/'audit_candidate08.py')
    old={'id':'SYN','labels':{d:0 for d in s.DIMS},'reasons':{'S':'old'},'evidence':[],
        'innovation_subtypes':[],'fairness_subtypes':[],'safety_quality_basis':'no_quality_basis'}
    for field,value in [('reasons',{'S':'new'}),('evidence',[{'quote':'x'}]),('innovation_subtypes',['attribute']),
        ('fairness_subtypes',['access']),('safety_quality_basis','quality_stated')]:
        new=copy.deepcopy(old);new[field]=value
        assert audit.changed_fields(old,new)==[field];passed('equal labels still detect '+field)
    new=copy.deepcopy(old);del new['reasons']
    assert audit.changed_fields(old,new)==['reasons'];passed('missing field detected')
    obj={'status':'PASS_NO_MODEL_CONTRACT_TESTS','tests':results,'test_count':len(results),
        'real_model_calls':0,'real_CLI_invocations':0,'independent16_content_read':False,
        'not_end_to_end_model_or_semantic_validation':True}
    s.dump_new(s.HERE/'selftest_no_model_results.json',obj)
    print(json.dumps({'status':obj['status'],'test_count':len(results),'model_calls':0,'CLI_invocations':0},ensure_ascii=False))


if __name__=='__main__':main()

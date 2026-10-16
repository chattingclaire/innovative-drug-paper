"""Explicit 196 original + 25 single-unit candidate03 profile. Read-only.
The first gate reads only binding/summary/QA/plan/authorization JSON, never labels.
Actual audit helpers are invoked only after all complete-run header gates pass.
"""
from pathlib import Path
import hashlib, importlib.util, json, sys

R = Path(__file__).resolve().parent.parent
H = R/'llm-candidate03-development'
PROFILE = 'LLM03_single_unit_reconciled_execution_v2'
METHOD = 'LLM-v32-candidate03-single-unit-reconciled-development'
STAT_KEY = 'LLM-candidate03-single-unit-reconciled'
STATUS = 'complete_actual_full_corpus_development_reconciled_QA_PASS'
ADAPTER_STATUS = 'passed_candidate03_reconciled_actual_execution_and_binding_QA_v2'
PLAN_SHA = 'd0cf693884e16e86c317c523e20a63263407d8758e32f069a23d9ca6ee7d4188'
PROMPT_SHA = '8576d9a1be10b0dd7b69b4c12367f4c357f55abf4ca30d979d5b333493089ba4'
INPUT_SHA = '6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763'
HELPER_SHA = '0f49b3e640c94777f05527770b2f9c1d7b2379bfa830a8af826d3faa2e5aae64'
DRIVER_SHA = '374df5924bdc509fb4c7a3a55c2b948b6f60f6fdbad3e4da5bb09aee61cd3d8a'
FINAL_DIR = H/'full-corpus-candidate03-material-v14-single-unit-reconciled-development'

class ProfileGateError(ValueError): pass

def require(ok, message):
    if not ok: raise ProfileGateError(message)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def bound_json(b):
    require(isinstance(b,dict) and isinstance(b.get('path'),str) and isinstance(b.get('sha256'),str),'Pending path/SHA binding')
    p=Path(b['path']);require(p.is_absolute() and p.is_file(),'Pending bound file: '+str(p))
    require(sha(p)==b['sha256'],'SHA mismatch: '+str(p))
    return json.loads(p.read_text())
def same(a,b): return a['path']==b['path'] and a['sha256']==b['sha256']

def closed_header(binding):
    """No recursion into prediction, lineage, raw output, or reference documents."""
    require(sys.flags.optimize==0,'Python optimization must be disabled')
    entry=bound_json(binding)
    require(entry.get('status')==STATUS,'Reconciled full execution is not complete; labels must remain unread')
    require(entry.get('method_id')==METHOD and entry.get('n')==4924 and entry.get('batches')==221,'Wrong reconciled method/scope')
    require(entry.get('source_production_batches')==197 and entry.get('original_terminal_failed_batches')==[115],'Original protocol failure scope differs')
    require(entry.get('original_execution_status')=='partial_or_failed_preserved','Original197 must remain explicitly incomplete')
    require(entry.get('formal_adoption') is False and entry.get('independent_validation') is False and entry.get('all_240_exposed_development') is True,'Development exposure/adoption scope differs')
    require(entry.get('requested_model')=='gpt-5.6-sol' and entry.get('reasoning_effort')=='medium','Actual model parameters differ')
    require(Path(entry['run']).resolve()==FINAL_DIR.resolve() and Path(entry['output']['path']).resolve()==FINAL_DIR/'all_predictions.jsonl','Unplanned reconciled output path')
    require(entry['source_input']['sha256']==INPUT_SHA and entry['prompt']['sha256']==PROMPT_SHA,'Source or semantic prompt changed')
    require(entry['protocol_supplement']['sha256']==PLAN_SHA and same(entry['protocol_supplement'],entry['run_plan']),'Not the reviewed v2 protocol supplement')
    qa=bound_json(entry['technical_QA']);summary=bound_json(entry['execution_summary'])
    oq=bound_json(entry['original_run_QA']);rq=bound_json(entry['recovery_QA'])
    plan=bound_json(entry['protocol_supplement']);auth=bound_json(entry['root_authorization'])
    require(qa.get('status')=='PASS','Reconciled execution QA is not PASS; labels must remain unread')
    require(summary.get('status')=='complete_reconciled_actual_development_with_disclosed_protocol_supplement','Reconciled summary incomplete')
    expected={'method_id':METHOD,'n':4924,'source_production_batches':197,'original_accepted_batches':196,'original_terminal_failed_batches':[115],'original_execution_status':'partial_or_failed_preserved','recovery_logical_single_unit_calls':25,'accepted_model_request_batches':221,'same_frozen_prompt_sha256':PROMPT_SHA,'same_v14_input_sha256':INPUT_SHA,'batch_partition_changed_only_for_original_batch115':True,'original_max3_protocol_not_claimed_successful':True,'new_requests_semantically_five_dimensional':True,'references_or_metrics_used_to_select':False,'rows_or_quotes_manually_changed':False,'dimension_splicing':False,'formal_adoption':False,'independent_validation':False,'all_240_exposed_development':True}
    for k,v in expected.items(): require(summary.get(k)==v and qa.get(k)==v,'QA/summary header mismatch: '+k)
    for k in ('original_run_unchanged','formal_candidate02_unchanged','candidate03_previous_artifacts_unchanged'): require(qa.get(k) is True,'Preservation QA failed: '+k)
    for q,k in [('output','output'),('row_provenance','row_provenance'),('original_incomplete_run_QA','original_run_QA'),('recovery_QA','recovery_QA'),('protocol_supplement','protocol_supplement'),('authorization','root_authorization')]:require(same(qa[q],entry[k]),'QA binding mismatch: '+k)
    require(oq.get('status')=='PASS_AUDIT_OF_TECHNICALLY_INCOMPLETE_RUN' and oq.get('original_execution_status')=='partial_or_failed_preserved','Original incomplete audit missing')
    require((oq.get('n_input_rows'),oq.get('logical_batches'),oq.get('accepted_batches'),oq.get('accepted_rows'),oq.get('terminal_failed_batches'))==(4924,197,196,4899,[115]),'Original196/4899 scope differs')
    require(rq.get('status')=='PASS' and rq.get('original_execution_status')=='complete_actual_calls_structurally_valid','Single-unit recovery incomplete')
    require((rq.get('n_input_rows'),rq.get('logical_batches'),rq.get('accepted_batches'),rq.get('accepted_rows'),rq.get('terminal_failed_batches'))==(25,25,25,25,[]),'Recovery25 scope differs')
    for name,q in [('original',oq),('recovery',rq)]:
        require(q.get('first_valid_selected_without_post_valid_calls') is True and q.get('all_selected_raw_objects_equal_actual_final_event_JSON') is True,'First-valid/event-object QA missing')
        require(len(q['batch_audits'])==q['logical_batches'] and len(q['attempt_audits'])==q['actual_attempts'],'Actual attempt audit coverage differs')
        require(summary[name+'_actual_attempts']==q['actual_attempts'] and summary[name+'_failed_attempts_preserved']==q['failed_attempts_preserved'],'Summary attempt counts differ')
        require(all(not x['event_check']['violations'] for x in q['attempt_audits']),'Tool or unknown execution events present')
    require(auth.get('status')=='passed_root_independent_recovery_review' and auth.get('plan_sha256')==PLAN_SHA and auth.get('new_calls_authorized')==25 and auth.get('technical_max_attempts')==75,'Recovery authorization missing')
    require(plan['permitted_original_terminal_failed_batches']==[115] and plan['recovery_n']==25 and plan['batch_size']==1 and plan['max_attempts_per_single_unit']==3,'Recovery partition differs')
    require(plan['reconciled_method_id']==METHOD and plan['source']['sha256']==INPUT_SHA and plan['prompt']['sha256']==PROMPT_SHA,'Recovery plan identity differs')
    require(Path(entry['original_run']).resolve()==Path(plan['original_run']).resolve()==Path(oq['run']).resolve(),'Original run lineage differs')
    require(Path(entry['recovery_run']).resolve()==Path(plan['recovery_run']).resolve()==Path(rq['run']).resolve(),'Recovery lineage differs')
    require(plan['code_bindings']['candidate03_execution_audit_utils_v2.py']['sha256']==HELPER_SHA and plan['code_bindings']['run_candidate03_unit_recovery_and_reconcile_v2.py']['sha256']==DRIVER_SHA,'Wrong execution audit code')
    return entry,qa,summary,oq,rq,plan,auth

def verify_complete(binding,io,rows=None):
    """Actual complete execution audit; caller must not use on partial runs."""
    entry,qa,summary,oq,rq,plan,auth=closed_header(binding)
    io.verify(binding);io.tree(entry)
    helper=H/'candidate03_execution_audit_utils_v2.py'
    require(sha(helper)==HELPER_SHA,'Execution audit helper changed')
    sys.path.insert(0,str(H))
    try:
        spec=importlib.util.spec_from_file_location('reconciled_v2_actual_execution_audit',helper)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        original,original_qa,validator=module.audit(entry['original_run'],4924,25,INPUT_SHA,PROMPT_SHA,[115])
        recovery,recovery_qa,_=module.audit(entry['recovery_run'],25,1,plan['recovery_input']['sha256'],PROMPT_SHA,[])
    finally: sys.path.pop(0)
    require(original_qa==oq and recovery_qa==rq,'Actual execution audit differs from bound QA')
    for q in (oq,rq):
        for attempt in q['attempt_audits']:
            for key,file in (('metadata_sha256','run_metadata.json'),('request_sha256','request.txt'),('events_sha256','events.jsonl'),('raw_output_sha256','raw_output.json')):
                if attempt.get(key) is not None:io.verify({'path':str(Path(attempt['path'])/file),'sha256':attempt[key]})
    source=io.rows(entry['source_input']);actual=io.rows(entry['output']);lineage=io.rows(entry['row_provenance'])
    require(len(source)==len(actual)==len(lineage)==4924 and list(source)==list(actual)==list(lineage),'Incomplete/reordered actual rows')
    if rows is not None:require(actual==rows,'Caller rows differ from bound full output')
    source_rows=list(source.values());recovery_input=io.rows(plan['recovery_input'])
    require(list(recovery_input.values())==source_rows[2850:2875] and list(recovery_input)==plan['recovery_ids'],'Recovery input must exactly equal all25 original records')
    reconstructed=[];issues=[];expected_lineage={}
    for batch in range(1,198):
        components=[recovery[i] for i in range(1,26)] if batch==115 else [original[batch]]
        for component in components:
            raw=component['raw'];meta=component['metadata'];attempt=component['attempt_path']
            reconstructed.extend(raw['rows']);issues.extend(raw['issue_records'])
            for src,row in zip(component['packet']['rows'],raw['rows']):
                expected_lineage[row['id']]={'method_id':METHOD,'original_production_batch':batch,'source_kind':'single_unit_protocol_supplement' if batch==115 else 'original_full_run_first_valid_batch','actual_request_batch_size':len(component['packet']['rows']),'actual_attempt_path':str(attempt),'actual_prompt_sha256':meta['prompt_sha256'],'actual_request_sha256':meta['request_sha256'],'raw_output_sha256':meta['raw_output_sha256'],'events_sha256':meta['events_sha256'],'metadata_sha256':sha(attempt/'run_metadata.json'),'requested_model':meta['requested_model'],'reasoning_effort':meta['reasoning_effort'],'provider_internal_revision':meta['provider_internal_model_revision'],'source_row_canonical_sha256':canonical(src),'output_row_canonical_sha256':canonical(row),'all_five_labels_from_one_intact_actual_row':True,'actual_final_event_full_object_checked':True}
    require(list(actual.values())==reconstructed,'Output is not actual first-valid complete row reconstruction')
    aggregate_path=FINAL_DIR/'all_predictions.json'
    io.verify({'path':str(aggregate_path),'sha256':sha(aggregate_path)})
    aggregate=json.loads(aggregate_path.read_text())
    require(aggregate['rows']==reconstructed and aggregate['issue_records']==issues,'Aggregate full object differs')
    require(not validator.validate({'rows':source_rows},aggregate),'Reconciled aggregate fails literal/schema validation')
    for rid,expected in expected_lineage.items():require(all(lineage[rid].get(k)==v for k,v in expected.items()),'Actual row provenance differs: '+rid)
    require(sum(x['source_kind']=='single_unit_protocol_supplement' for x in lineage.values())==25,'Recovery row count differs')
    return {'status':'PASS_ACTUAL_RECONCILED_EXECUTION_PROFILE_V2','method_id':METHOD,'n':4924,'accepted_requests':221,'original_accepted_requests':196,'original_failed_batches':[115],'recovery_single_unit_requests':25,'actual_attempts':oq['actual_attempts']+rq['actual_attempts'],'failed_attempts_preserved':oq['failed_attempts_preserved']+rq['failed_attempts_preserved'],'partial_original_not_called_complete':True,'all_rows_reconstructed_exactly':True,'stability_not_evaluated':True,'formal_adoption':False,'independent_validation':False}

def development_header(dev):
    require(sys.flags.optimize==0,'Python optimization must be disabled')
    require(dev.get('stage')=='development_only_all240_exposed' and dev.get('root_development_bindings_confirmed') is True,'Pending root development binding')
    require(dev.get('independent_validation') is False and dev.get('human_validation_completed') is False,'Development scope changed')
    require(set(dev.get('methods',{}))=={'rules-v36.2',STAT_KEY},'Explicit rules36.2/reconciled03 methods required')
    m=dev['methods'][STAT_KEY]
    require(m.get('frozen_method_id')==METHOD and m.get('execution_profile')==PROFILE,'Wrong explicit reconciled profile')
    adapter=bound_json(m['execution_adapter'])
    require(adapter.get('status')==ADAPTER_STATUS and adapter.get('root_confirmed') is True and adapter.get('n')==4924 and adapter.get('accepted_request_n')==221,'Pending reconciled execution adapter')
    require(same(adapter['output'],m['output']) and adapter.get('original_failed_batches')==[115],'Execution adapter scope mismatch')
    full=closed_header(adapter['source_full_binding'])[0]
    require(same(full['output'],m['output']),'Execution/full output differs')
    return adapter

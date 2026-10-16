"""Fix synthetic contract inputs/expectations before executing the bridge."""
from pathlib import Path
import hashlib
import json

D=Path(__file__).resolve().parent;R=D.parents[1]
def bind(p):
    p=Path(p).resolve();b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def write(name,v):
    with (D/name).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
base={'path':'synthetic_reference','reference':'合成条款内容','necessary_dependency':True,'evidence':[{'text':'合成连续原文','locator':{'synthetic':True,'start':0,'end':6}}],'closure_proof':{'synthetic':True,'unchanged_test_payload':'not a real closure certification'},'affected_dimensions':['S','E'],'only_IF_consumers':False}
cases=[]
def add(name,reqs,expected=None,error=None,raw=None,pointer='/log/source_requests',wrong_sha=False):
    doc={'identity':'synthetic_contract_control_not_policy_record','log':{'source_requests':reqs,'read_receipts':[{'synthetic':'unchanged raw receipt'}],'use_receipts':[]},'unrelated_material_requests':[{'synthetic':'retained stopped material'}]}
    raw=raw or json.dumps(doc,ensure_ascii=False,indent=1)+'\n'
    cases.append({'control_id':name,'synthetic':True,'raw_utf8_json':raw,'input_sha256':hashlib.sha256(raw.encode()).hexdigest(),'supplied_sha256':'0'*64 if wrong_sha else hashlib.sha256(raw.encode()).hexdigest(),'request_pointer':pointer,'expected_statuses':expected,'expected_error':error,'basis':'Exact enum alias only; evidence, source reads, consumer scope and unresolved requests remain subject to original validators.'})
def q(**fields):return dict(base,**fields)
add('dependency_resolved_alias',[q(dependency_status='resolved')],['resolved'])
add('legacy_status_resolved',[q(status='resolved')],['resolved'])
add('both_resolved_match',[q(status='resolved',dependency_status='resolved')],['resolved'])
add('dependency_stopped',[q(dependency_status='stopped',stop_reason='synthetic_missing_source')],['stopped'])
add('dependency_unresolved',[q(dependency_status='unresolved')],['unresolved'])
add('legacy_unresolved',[q(status='unresolved')],['unresolved'])
add('resolved_vs_stopped_conflict',[q(status='resolved',dependency_status='stopped')],error='status_fields_conflict')
add('stopped_vs_resolved_conflict',[q(status='stopped',dependency_status='resolved')],error='status_fields_conflict')
add('negative_fields_conflict',[q(status='stopped',dependency_status='unresolved')],error='status_fields_conflict')
add('both_fields_missing',[q()],error='status_fields_missing')
add('present_null_is_not_missing_alias',[q(status='resolved',dependency_status=None)],error='status_field_unknown_or_invalid')
add('unknown_case_not_normalized',[q(status='RESOLVED',dependency_status='resolved')],error='status_field_unknown_or_invalid')
add('boolean_not_status',[q(status='resolved',dependency_status=True)],error='status_field_unknown_or_invalid')
add('resolved_does_not_remove_other_stop',[q(dependency_status='resolved'),q(dependency_status='stopped',stop_reason='separate_unknown_standard')],['resolved','stopped'])
add('empty_list_stays_empty',[],[])
add('duplicate_key_cannot_select_last_resolved',[],error='duplicate_json_key',raw='{"log":{"source_requests":[{"status":"stopped","status":"resolved"}]}}\n')
add('wrong_raw_byte_sha',[],error='original_bytes_sha_mismatch',wrong_sha=True)
add('missing_request_pointer_not_empty',[],error='request_pointer_missing',pointer='/missing/source_requests')
assert len(cases)==18
write('fixed-synthetic-controls.json',cases)
driver=R/'06-coding/rule-full4481-final-v5-sol/rule_driver.py'
protocol=R/'01-review/context-projection-sol/full-frame-preflight/source_reading_protocol_v12.py'
scope=R/'06-coding/rule-full4481-final-v5-sol/frozen-scope.json'
candidate=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v5-primary-standard-bridge-sol'
scope_doc=json.loads(scope.read_bytes());assert scope_doc['source_reading_protocol_code']==bind(protocol)
pre=json.loads((candidate/'pre-execution-seal.json').read_bytes())
assert bind(candidate/'pre-execution-seal.json')['sha256']=='4f8ae9d0a3eb116dd3cd6b44bd8355683b08a54921ee1a6739aff0b609dc3cae'
assert bind(candidate/'algorithm-bindings.json')['sha256']=='5f9d780b4a72779f69e91082881109f65aa8adc6395ebf94b061bd207e0d14bf'
for m in pre['five_modules']:assert bind(m['path'])==m
assert bind(protocol)['sha256']=='edec7a03cb29b835f106acb55f306ad8fe4767d3964fdf130e2f3f91754ff076'
assert bind(driver)['sha256']=='0cbb28c7fcb1176212c41e2bf7cd428c0df6bb18f4958d1f258ad8f56a089267'
write('frozen-interface-bindings.json',{'inputs':[bind(p) for p in [protocol,driver,scope,candidate/'pre-execution-seal.json',candidate/'algorithm-bindings.json']]+pre['five_modules'],'read_code_sections':{'protocol_source_requests_status':'58–59','driver_raw_log_source_requests':'228','driver_protocol_check':'362','driver_stop_consumer':'370–373','v5_dependency_status_producer':'764/773'},'actual_run_outputs_or_labels_read':False})
write('preparation-seal.json',{'status':'candidate_code_and_18_synthetic_inputs_fixed_before_execution','members':[bind(D/name) for name in ['status_bridge.py','prepare_controls.py','fixed-synthetic-controls.json','frozen-interface-bindings.json','run_controls.py']],'self_excluded':True,'classifier_calls':0,'actual_full_domain_records_processed':0})
print(json.dumps({'controls_N':18,'preparation_seal':bind(D/'preparation-seal.json')},ensure_ascii=False))

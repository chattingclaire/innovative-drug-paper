"""Finite synthetic exception-audit controls; never imports/runs frozen coders."""
import ast, copy, hashlib, json, types
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'formal-freeze-interface-v1-sol/rule_driver.py'
NEW=HERE/'rule_driver.py'
old_text=OLD.read_text();new_text=NEW.read_text()
old_tree=ast.parse(old_text);new_tree=ast.parse(new_text)
old_funcs={n.name:n for n in old_tree.body if isinstance(n,ast.FunctionDef)}
new_funcs={n.name:n for n in new_tree.body if isinstance(n,ast.FunctionDef)}
results=[]
def record(name,ok,scope):
 if not ok:raise AssertionError(name)
 results.append({'name':name,'passed':True,'evidence_kind':scope})
for name in old_funcs:
 if name!='main':assert ast.dump(old_funcs[name],include_attributes=False)==ast.dump(new_funcs[name],include_attributes=False),name
record('all_existing_functions_except_main_exact_AST_unchanged',True,'static function equality')
def guard_text(t):
 a=t.index('            if stops:\n');b=t.index('            prediction.update(labels=',a);return t[a:b]
old_guard=guard_text(old_text);new_guard=guard_text(new_text)
record('dependency_request_guard_exact_bytes_unchanged',old_guard==new_guard,'static exact code equality')
assert "raise ValueError('first output exists; use a distinct authorized round, never overwrite')" in new_text
assert "if scope.get('max_actual_cohort_inference_runs')!=1:" in new_text
assert "if target.name=='reference.jsonl' or '/04-calibration/' in str(target):raise PermissionError('reference/calibration prohibited')" in new_text
record('scope_one_run_whitelist_noGold_and_no_overwrite_guards_preserved',True,'static only; no execution scope produced')
ns={'copy':copy,'hashlib':hashlib,'DIMENSIONS':('S','E','Ec','I','F'),
    'cj':lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)}
node=ast.Module(body=[new_funcs['capture_exception_source_audit'],new_funcs['dimension_slots']],type_ignores=[])
exec(compile(ast.fix_missing_locations(node),str(NEW),'exec'),ns)
capture=ns['capture_exception_source_audit'];slots=ns['dimension_slots']
attrs=('source_requests','material_requests','source_view_events','source_relation_traces')
def fixture_view(label):
 request={'path':'synthetic_dependency','fixture_id':label,'status':'unresolved','necessary_dependency':True}
 return types.SimpleNamespace(source_requests=[dict(request,dependency_status='stopped')],material_requests=[request],
   source_view_events=[{'fixture_event':label}],source_relation_traces=[{'fixture_trace':label}])
def carried_error(label,empty=False):
 e=ValueError('synthetic error')
 for a in attrs:setattr(e,a,[] if empty else [{'fixture_'+a:label}])
 return e
v=fixture_view('VIEW_ONLY');e=ValueError('synthetic error');snap=capture(v,e,None,None,'not_started')
record('view_only_request_material_events_traces_retained',all(snap[a]==getattr(v,a) and snap['live_view_source_audit'][a]==getattr(v,a) for a in attrs),'synthetic stub, no policy text')
e=carried_error('ERROR_ONLY');snap=capture(None,e,None,None,'not_started')
record('exception_only_attributes_retained_and_origin_explicit',all(snap[a]==getattr(e,a) and snap['exception_source_audit'][a]==getattr(e,a) and snap['primary_source_audit_origin'][a]=='exception_attribute' for a in attrs),'synthetic stub')
v=fixture_view('LIVE');e=carried_error('EMPTY',True);snap=capture(v,e,None,None,'not_started')
record('empty_exception_attrs_never_overwrite_live_data',all(snap[a]==getattr(v,a) and snap['exception_source_audit'][a]==[] for a in attrs),'synthetic both-source stub')
v=fixture_view('LIVE');e=carried_error('CARRIED');snap=capture(v,e,None,None,'not_started')
record('both_nonempty_sources_preserved_separately',all(snap[a]==getattr(v,a) and snap['exception_source_audit'][a]==getattr(e,a) and snap['primary_source_audit_origin'][a]=='live_view' for a in attrs),'synthetic conflicting-source stub')
record('unproduced_log_check_remain_None_and_state_explicit',snap['uniform_source_reading_log'] is None and snap['uniform_source_protocol_check'] is None and snap['uniform_source_audit_state']['log']=='not_produced' and snap['uniform_source_audit_state']['check']=='not_produced','synthetic before-call stub')
mid=capture(v,e,None,None,'building')
record('call_failed_before_return_is_unknown_not_fake_generated_log',mid['uniform_source_audit_state']['log']=='not_returned_to_driver' and mid['uniform_source_audit_state']['check']=='not_returned_to_driver','synthetic unreturned-call stub')
# Execute only the exact retained guard, with synthetic decisions and source audit.
decisions={d:{'value':0,'needed_material':[],'details':{}} for d in ns['DIMENSIONS']}
source_log={'fixture_log':'produced','source_requests':copy.deepcopy(v.source_requests)}
source_check={'errors':[],'dependency_stop_reasons':['missing_required_source']}
try:
 exec(compile('\n'.join(l[12:] for l in new_guard.splitlines()),str(NEW)+':synthetic_guard','exec'),{'view':v,'decisions':decisions,'stops':source_check['dependency_stop_reasons']})
except ValueError as error:
 record('generated_log_check_then_unchanged_guard_raises',str(error)=='source dependency request was not retained in a decision stop or independent-positive audit','synthetic original guard, no judge')
 snap=capture(v,error,source_log,source_check,'returned')
else:raise AssertionError('unchanged guard did not fail')
record('returned_uniform_log_and_check_saved_exactly',snap['uniform_source_reading_log']==source_log and snap['uniform_source_protocol_check']==source_check and snap['uniform_source_audit_state']['log']=='available_returned_value','synthetic guard failure snapshot')
# Match only the revised exception assignment/saved consumption shape; no cohort loop.
start=new_text.index('            exception_audit = capture_exception_source_audit(')
end=new_text.index('\n        predictions.append(prediction)',start)
except_body='\n'.join(l[12:] for l in new_text[start:end].splitlines())
prediction={'id':'SYNTHETIC','labels':None,'decisions':None,'candidate_decisions_diagnostic_only':copy.deepcopy(decisions),'implementation_errors':[{'type':'ValueError','message':'synthetic guard'}]}
local={'capture_exception_source_audit':capture,'copy':copy,'view':v,'error':ValueError('synthetic guard'),
 'source_log':source_log,'source_check':source_check,'source_log_stage':'returned','prediction':prediction,
 'row':{'id':'SYNTHETIC'},'detail':{'type':'ValueError'},'consumption_logs':[]}
exec(compile(except_body,str(NEW)+':synthetic_exception_branch','exec'),local)
saved=local['consumption_logs'][0]
record('actual_exception_branch_preserves_live_and_uniform_audit',saved['material_requests']==v.material_requests and saved['source_requests']==v.source_requests and saved['uniform_source_reading_log']==source_log and saved['uniform_source_protocol_check']==source_check and saved['retained_error_source_requests']==[],'synthetic exact exception branch')
ss=slots([{'source_record':{'id':'SYNTHETIC'}}],[prediction],[])
record('diagnostic_five_zeros_not_promoted_failure_mask_unchanged',prediction['labels'] is None and prediction['decisions'] is None and len(ss)==5 and all(x['technical_failure'] and x['rule_value'] is None and not x['rules_null'] and not x['comparison_eligible'] for x in ss),'synthetic original dimension_slots')
null_pred={'id':'SYNTHETIC_NULL','labels':{d:None for d in ns['DIMENSIONS']},'decisions':{d:{'value':None} for d in ns['DIMENSIONS']},'implementation_errors':[]}
null_slots=slots([{'source_record':{'id':'SYNTHETIC_NULL'}}],[null_pred],[])
record('lawful_null_mask_not_changed',all(not x['technical_failure'] and x['rules_null'] and x['rule_value'] is None and x['comparison_eligible'] for x in null_slots),'synthetic original dimension_slots; not real3 reclassification')
before=copy.deepcopy(snap);v.material_requests[0]['fixture_id']='MUTATED';source_log['fixture_log']='MUTATED';source_check['dependency_stop_reasons'].append('MUTATED')
record('snapshots_deepcopied_not_live_aliases',snap==before,'synthetic mutation after snapshot')
for n in ['interface_common.py','algorithm-bindings.json','formal-manual-binding.json']:
 record('unchanged_support_copy_'+n,(HERE/n).read_bytes()==(OLD.parent/n).read_bytes(),'actual support-file bytes equality')
alg=json.loads((HERE/'algorithm-bindings.json').read_bytes())
for a in alg['modules']:
 b=Path(a['path']).read_bytes();assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256']
record('five_original_v17_module_paths_actual_SHA_bytes_match',len(alg['modules'])==5,'actual file integrity only; modules not imported or run')
formal=json.loads((HERE/'formal-manual-binding.json').read_bytes());mb=formal['manual'];p=Path(mb.get('path',mb.get('absolute_path')));b=p.read_bytes()
record('actual_1_3F_manual_binding_path_SHA_bytes_match',len(b)==mb['bytes'] and hashlib.sha256(b).hexdigest()==mb['sha256'],'actual file integrity only')
result={'control_scope':'finite synthetic exception-audit controls only','actual_cohort_or_algorithm_runs':0,'new_policy_source_text_opened':False,'new_labels_created':False,
 'controls_N':len(results),'all_passed':all(x['passed'] for x in results),'results':results,
 'original_guard_sha256':hashlib.sha256(old_guard.encode()).hexdigest(),'new_guard_sha256':hashlib.sha256(new_guard.encode()).hexdigest(),
 'original_dimension_slots_AST_unchanged':True,'unknown_unreturned_log_not_reconstructed':True}
(HERE/'control-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['controls_N','all_passed','actual_cohort_or_algorithm_runs','new_labels_created']},ensure_ascii=False))

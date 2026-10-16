"""Post-run identity/count audit only; never import or run a rule coder."""
from pathlib import Path
import datetime, hashlib, json, os
NEW = Path(__file__).resolve().parent
BASE = NEW.parents[1]
RUN = NEW / 'run77-first'
def bind(p):
    p=Path(p).resolve();raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def verify(b):
    a=bind(b['path'])
    assert all(a[k]==b[k] for k in ('path','sha256','bytes')),b['path']
    return a
scope=json.loads((NEW/'source-scope.json').read_bytes())
seal=json.loads((RUN/'seal.json').read_bytes())
execution=json.loads((RUN/'execution.json').read_bytes())
checks=seal['implementation_files']+seal['material_bindings']+seal['control_inputs']+seal['output_files']
verified=[verify(b) for b in checks]
for folder in (BASE,NEW):
    frozen=json.loads((folder/'pre-run-seal.json').read_bytes())
    for b in frozen['files']+frozen['implementation_files']+frozen['material_bindings']+frozen['other_frozen_bindings']:verify(b)
assert not (BASE/'root-go.json').exists() and not (BASE/'actual-launch-record.json').exists() and not (BASE/'run77-first').exists()
assert sum((p/'actual-launch-record.json').exists() for p in (BASE,NEW))==1
launch=json.loads((NEW/'actual-launch-result.json').read_bytes())
assert launch['actual_driver_process_launch_N']==1 and launch['retry_attempted'] is False and launch['exit_code']==0
for k in ('stdout_binding','stderr_binding','driver_output_seal_binding'):verify(launch[k])
assert (NEW/'driver-stderr.txt').stat().st_size==0
slots=[json.loads(line) for line in (RUN/'all-dimension-slots.jsonl').read_bytes().splitlines()]
predictions=[json.loads(line) for line in (RUN/'predictions.jsonl').read_bytes().splitlines()]
assert [p['id'] for p in predictions]==scope['approved_record_ids']
assert len(predictions)==77 and len(slots)==385
assert [[s['dimension'] for s in slots if s['id']==rid] for rid in scope['approved_record_ids']]==[['S','E','Ec','I','F']]*77
technical_failure_N=sum(s['technical_failure'] for s in slots)
null_N=sum(s['rules_null'] for s in slots)
retained_N=sum(isinstance(p.get('labels'),dict) for p in predictions)*5
assert (technical_failure_N,null_N,retained_N)==(execution['technical_failure_dimension_N'],execution['lawful_null_N'],execution['retained_decision_N'])==(0,0,385)
assert all(not p['implementation_errors'] for p in predictions)
allowed={Path(b['path']).resolve() for b in seal['implementation_files']+seal['material_bindings']+seal['control_inputs']}
stdlib=Path(os.__file__).resolve().parent
read_paths=execution['read_paths'];classified={'bound_dependency':[],'own_output':[],'python_stdlib':[]}
for name in read_paths:
    p=Path(name).resolve()
    assert '/04-calibration/' not in str(p) and p.name!='reference.jsonl'
    if p in allowed:classified['bound_dependency'].append(str(p))
    elif RUN in p.parents:classified['own_output'].append(str(p))
    elif stdlib in p.parents:classified['python_stdlib'].append(str(p))
    else:raise AssertionError('unexpected recorded source/dependency read '+str(p))
report={'status':'post_run_bindings_and_counts_verified_without_reference_comparison','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'algorithm_version':scope['algorithm_version'],'runtime_version':execution['runtime_version'],'run_output':str(RUN),'run_output_seal_binding':bind(RUN/'seal.json'),'verified_run_seal_binding_N':len(verified),'run_seal_output_binding_N':len(seal['output_files']),'implementation_binding_N':len(seal['implementation_files']),'material_binding_N':len(seal['material_bindings']),'actual_driver_process_launch_N':1,'actual_cohort_inference_runs':execution['actual_cohort_inference_runs'],'record_N':len(predictions),'dimension_N':len(slots),'retained_decision_N':retained_N,'technical_failure_dimension_N':technical_failure_N,'lawful_null_N':null_N,'implementation_error_N':len(execution['implementation_errors']),'driver_process_exit_code':launch['exit_code'],'stderr_bytes':(NEW/'driver-stderr.txt').stat().st_size,'retry_attempted':False,'v2_preparation_bindings_unchanged':True,'v2_actual_attempt_exists':False,'actual_record_ID_order_matches_frozen_v15':True,'recorded_read_path_N':len(read_paths),'recorded_read_path_classification_counts':{k:len(v) for k,v in classified.items()},'recorded_read_path_classification':classified,'python_stdlib_contract_root':str(stdlib),'forbidden_reference_path_N':0,'recorded_read_paths_all_bound_own_output_or_contract_stdlib':True,'accuracy_computed':False,'calibration_labels_already_disclosed':True,'blind_validation':False,'formal_validation_complete':False,'human_validation_complete':False,'independent_trace_quote_audit':'separate subagent in independent-output-audit; still pending','previous_post_run_audit_harness_failure_preserved':bind(NEW/'post-run-binding-count-check-attempt01-failure.json'),'script_binding':bind(__file__)}
with (NEW/'post-run-binding-and-count-check.json').open('x',encoding='utf8') as f:
    f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('status','verified_run_seal_binding_N','record_N','dimension_N','technical_failure_dimension_N','lawful_null_N','recorded_read_path_classification_counts')},ensure_ascii=False))

"""Guarded resume of the unchanged controller using dependency-complete Python."""
import datetime
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'06-coding/full4481-cli-fixed-batch-scheduler-v3-capacity13-root'
EXPECTED_RUNTIME=ROOT/'parallel-metrics/.venv/bin/python'
assert Path(sys.executable)==EXPECTED_RUNTIME

def bind(path):
    p=Path(path).resolve();raw=p.read_bytes()
    return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def exact(item):
    assert bind(item['path'])=={k:item[k]for k in ('path','bytes','sha256')},item['path']

def load(p):return json.loads(Path(p).read_text())

def save(p,v):
    with Path(p).open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

recovery=HERE/'ROOT-runtime-reception-recovery-01'
for item in load(recovery/'output-seal.json')['output_members']:exact(item)
assert load(recovery/'summary.json')['technically_valid_batch_N']==13
for item in load(HERE/'seal.json')['output_members']:exact(item)
config=load(HERE/'input-bindings.json')
for item in config['core_inputs']:exact(item)
runtime_spec=importlib.util.find_spec('jsonschema');assert runtime_spec and runtime_spec.origin
# Actually import the corrected validator in this runtime before a GO.
validator_spec=importlib.util.spec_from_file_location('runtime_gate_validator',config['corrected_validator']['path'])
validator=importlib.util.module_from_spec(validator_spec);validator_spec.loader.exec_module(validator)
controller_spec=importlib.util.spec_from_file_location('unchanged_controller_gate',HERE/'scheduler.py')
controller=importlib.util.module_from_spec(controller_spec);controller_spec.loader.exec_module(controller)
states={b:controller.batch_state(b,config)for b in range(4,505)}
assert controller.coverage(states)['not_inspected_batch_N']==0
assert states[67]['state']=='ready' and states[67]['attempt']==1
matched=[]
for line in subprocess.check_output(['ps','-axo','pid=,ppid=,command='],text=True).splitlines():
    cols=line.strip().split(None,2)
    if len(cols)!=3:continue
    try:argv=shlex.split(cols[2])
    except ValueError:continue
    if not argv:continue
    name=Path(argv[0]).name
    fresh=name=='codex' and len(argv)>1 and argv[1]=='exec'
    runner=name.startswith('python') and any(x.endswith('/run_one_cli_batch.py')for x in argv[1:])
    scheduler=name.startswith('python') and any(x.endswith('/scheduler.py')and'full4481-cli-fixed-batch-scheduler'in x for x in argv[1:])
    if fresh or runner or scheduler:matched.append({'pid':int(cols[0]),'ppid':int(cols[1]),'kind':'fresh_cli'if fresh else('runner'if runner else'controller')})
assert not matched,matched
out=HERE/'ROOT-runtime-GO-02';out.mkdir(exist_ok=False)
receipt={'artifact_type':'ROOT_nonsemantic_runtime_recovery_pre_dispatch_GO','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime_interpreter_requested':str(EXPECTED_RUNTIME),'resolved_interpreter':bind(sys.executable),'jsonschema_version':importlib.metadata.version('jsonschema'),'jsonschema_import_file':bind(runtime_spec.origin),'corrected_validator_imported_successfully':True,'unchanged_controller':bind(HERE/'scheduler.py'),'unchanged_config':bind(HERE/'input-bindings.json'),'all_core_inputs_verified_unchanged_N':len(config['core_inputs']),'old_terminal_and_recovery_summary':bind(recovery/'summary.json'),'all_requested_batch_states_preflight':controller.coverage(states),'fresh_coding_CLI_or_owned_runner_or_controller_N_before_GO':0,'process_gate_preceded_actual_dispatch':True,'app_servers_excluded_from_fresh_exec_count':True,'model_prompt_manual_material_label_criteria_unchanged':True,'max_concurrent_cli':13,'next_batch':67,'legal_NULL_and_three_technical_attempt_limit_unchanged':True,'receiver_or_validator_source_changes':False,'first_bytes_label_based_selection_or_model_retry_for_import_error':False,'actual_model_dispatch_N_at_receipt':0,'next_action':'exec same sealed controller using this dependency-complete interpreter','GO_issued':True,'launcher':bind(__file__)}
save(out/'pre-dispatch-runtime-GO.json',receipt)
save(out/'output-seal.json',{'output_members':[bind(out/'pre-dispatch-runtime-GO.json')],'self_excluded':True})
print(json.dumps({'status':'actual_pre_dispatch_runtime_GO','next_batch':67,'max_concurrent_cli':13,'receipt':str(out/'pre-dispatch-runtime-GO.json')},ensure_ascii=False),flush=True)
os.execv(str(EXPECTED_RUNTIME),[str(EXPECTED_RUNTIME),'-B',str(HERE/'scheduler.py'),'--start','4','--end','504','--root-go-no-other-cli-live'])

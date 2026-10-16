"""Receive existing terminal batches after local jsonschema import failure.

No model dispatch, prediction alteration, label comparison or model retry.
"""
import datetime
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / '06-coding/full4481-cli-fixed-batch-scheduler-v3-capacity13-root'
OLD_RUN = HERE / 'runs/20261010T153845Z-6ef4c40a'
CAMPAIGN = ROOT / '06-coding/native-full4481-v1-sol'
OUT = HERE / 'ROOT-runtime-reception-recovery-01'

def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def exact(item):
    assert bind(item['path']) == {k:item[k] for k in ('path','bytes','sha256')}, item['path']

def load(path):
    return json.loads(Path(path).read_text())

def save(path, value):
    with Path(path).open('x', encoding='utf8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')

def process_gate():
    rows=[]
    data=subprocess.check_output(['ps','-axo','pid=,ppid=,command='],text=True)
    for line in data.splitlines():
        fields=line.strip().split(None,2)
        if len(fields)!=3:continue
        pid,ppid,command=fields
        try:argv=shlex.split(command)
        except ValueError:continue
        if not argv:continue
        executable=Path(argv[0]).name
        is_cli=executable=='codex' and len(argv)>1 and argv[1]=='exec'
        is_runner=executable.startswith('python') and any(x.endswith('/run_one_cli_batch.py') for x in argv[1:])
        is_controller=executable.startswith('python') and any(x.endswith('/scheduler.py') and 'full4481-cli-fixed-batch-scheduler' in x for x in argv[1:])
        if is_cli or is_runner or is_controller:
            rows.append({'pid':int(pid),'ppid':int(ppid),'kind':'fresh_cli' if is_cli else ('runner' if is_runner else 'controller'),'executable':argv[0]})
    assert not rows, rows
    return {'status':'zero_fresh_coding_CLI_or_owned_runner_or_controller_observed','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'matching_process_N':0,'app_server_processes_not_counted_as_fresh_exec':True}

def selected_count():
    n=0;paths=sorted(CAMPAIGN.glob('batch-*/root-selection.json'))
    for path in paths:
        item=load(path);exact(item['technical_reception'])
        rec=load(item['technical_reception']['path'])
        assert rec['state']=='technical_valid_whole_batch'
        n+=rec['validation']['record_N']
    return {'selected_batch_N':len(paths),'technically_received_record_N':n,'prediction_records_parsed':False}

config=load(HERE/'input-bindings.json')
seal=load(HERE/'seal.json')
for item in seal['output_members']:exact(item)
for item in config['core_inputs']:exact(item)
old=load(OLD_RUN/'run-result.json')
assert old['status']=='stopped_ROOT_inspection_required' and old['live_owned_runner_N_at_return']==0
events=[json.loads(line)for line in(OLD_RUN/'events.jsonl').read_text().splitlines()]
starts=[e for e in events if e['event']=='runner_started']
assert [(e['batch'],e['attempt'])for e in starts]==[(b,1)for b in range(54,67)]
assert old['diagnostic_N']==13
before_gate=process_gate()
spec=importlib.util.find_spec('jsonschema');assert spec and spec.origin
runtime={'requested_interpreter':sys.executable,'resolved_interpreter':bind(sys.executable),'jsonschema_version':importlib.metadata.version('jsonschema'),'jsonschema_import_file':bind(spec.origin),'reason':'bundled Python receiver import failed before any reception was created; existing stats runtime has jsonschema','receiver_code_changed':False,'validator_code_changed':False}
pre=[]
for b in range(54,67):
    slot=CAMPAIGN/f'batch-{b:04d}'/'attempt-0001'
    completion=load(slot/'ROOT-cli-process-completion.json')
    assert completion['status']=='actual_cli_process_terminal' and completion['returncode']==0
    assert completion['logical_dispatch_label']==f'native_full4481v1_b{b:04d}_a01'
    for key in ('raw_cli_events','stderr'):exact(completion[key])
    terminal=load(OLD_RUN/f'batch-{b:04d}-attempt-0001-runner-terminal.json');assert terminal['exitcode']==0
    receiver_error=OLD_RUN/f'batch-{b:04d}-attempt-0001-receiver-stderr.txt'
    assert "ModuleNotFoundError: No module named 'jsonschema'" in receiver_error.read_text()
    directory=slot.parent
    assert not (directory/'root-attempt-reception-0001-v3.json').exists()
    assert not (directory/'root-selection.json').exists() and not (directory/'first.json').exists()
    pre.append({'batch':b,'first_before':bind(slot/'first.json'),'terminal_completion':bind(slot/'ROOT-cli-process-completion.json'),'old_receiver_error':bind(receiver_error)})
OUT.mkdir(exist_ok=False)
save(OUT/'pre-reception-runtime-recovery.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'process_gate':before_gate,'old_scheduler_terminal':bind(OLD_RUN/'run-result.json'),'runtime':runtime,'receiver':config['receiver'],'validator':config['corrected_validator'],'amendment':config['validator_amendment'],'before_counts':selected_count(),'batches':pre,'actual_new_model_dispatch_N':0,'actual_model_retry_N':0,'first_bytes_or_labels_changed':False})
results=[]
for item in pre:
    b=item['batch'];prefix=f'batch-{b:04d}-reception'
    args=[sys.executable,config['receiver']['path'],'--run',str(CAMPAIGN),'--validator-amendment',config['validator_amendment']['path'],'--batch',str(b),'--attempt','1','--actor-completed']
    with (OUT/(prefix+'-stdout.txt')).open('xb')as out,(OUT/(prefix+'-stderr.txt')).open('xb')as err:
        process=subprocess.run(args,stdout=out,stderr=err,cwd=OUT)
    result={'batch':b,'returncode':process.returncode,'stdout':bind(OUT/(prefix+'-stdout.txt')),'stderr':bind(OUT/(prefix+'-stderr.txt'))}
    save(OUT/(prefix+'-terminal.json'),result)
    assert process.returncode==0,result
    directory=CAMPAIGN/f'batch-{b:04d}'
    rec=load(directory/'root-attempt-reception-0001-v3.json')
    assert bind(directory/'attempt-0001/first.json')==item['first_before']
    assert rec['state'] in ('technical_valid_whole_batch','technical_invalid_whole_batch')
    result.update({'state':rec['state'],'receipt':bind(directory/'root-attempt-reception-0001-v3.json'),'model_retry_performed':False,'first_unchanged':True})
    if rec['state']=='technical_valid_whole_batch':
        result['selection']=bind(directory/'root-selection.json')
        result['record_N']=rec['validation']['record_N']
    else:result['technical_error']=rec.get('error')
    results.append(result)
summary={'status':'all13_existing_terminal_batches_technically_received','results':results,'received_batch_N':len(results),'technically_valid_batch_N':sum(x['state']=='technical_valid_whole_batch'for x in results),'after_counts':selected_count(),'after_process_gate':process_gate(),'actual_new_model_dispatch_N':0,'actual_model_retry_N':0,'prediction_or_reference_labels_compared':False,'first_bytes_preserved':True,'next_dispatch_requires_separate_RUNTIME_GO':True}
save(OUT/'summary.json',summary)
save(OUT/'output-seal.json',{'output_members':[bind(p)for p in sorted(OUT.iterdir())if p.is_file()],'recovery_script':bind(__file__),'self_excluded':True})
print(json.dumps({k:v for k,v in summary.items()if k!='results'},ensure_ascii=False))

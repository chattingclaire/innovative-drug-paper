"""One original whole batch, new v16 material. No dispatch without actual ROOT GO.

Preparation/preflight is read-only. Future execution writes only pre-reserved own
slots, uses the existing validated CLI, and never controls any pre-existing PID.
"""
import argparse, datetime, fcntl, hashlib, json, os, signal, subprocess, sys, types
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REMAINING=ROOT/'06-coding/native-full4481-transport-recovery-v2-sol/execution-runs/20261011T150825641847Z'

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):return json.loads(Path(p).read_bytes())
def binding(p):
    p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def exact(b):assert binding(b['path'])=={k:b[k] for k in ('path','bytes','sha256')},'Changed binding: '+b['path']
def save(p,x):
    with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def module(b):
    exact(b);m=types.ModuleType('frozen_receiver');m.__file__=b['path'];exec(compile(Path(b['path']).read_bytes(),b['path'],'exec'),m.__dict__);return m
def preflight():
    seal=load(HERE/'preparation-seal.json')
    for b in seal['files']:exact(b)
    m=load(HERE/'manifest.json')
    for k in ('runner','receiver','base_guard','validator','cli_launcher','instructions','transport_contract','presentation_helper','submit_helper','original_assignment','original_controller','original_capacity3','v16_material_seal'):exact(m[k])
    a=load(m['batches'][0]['assignment']['path']);assert a['source_ids']==['RECODE25-01402','RECODE25-01403','RECODE25-01404'] and a['expected_N']==3
    assert m['max_total_technical_attempts']==a['max_total_technical_attempts']==3 and m['actual_concurrency_cap']==1
    for k,v in a.items():
        if isinstance(v,dict) and {'path','bytes','sha256'}<=set(v):exact(v)
    for b in a['packets']+a['source_asset_bindings']:exact(b)
    return m,a
def check_go(path,m):
    go=load(path);assert go.get('author')=='ROOT' and go.get('execution_authorized') is True,'Actual ROOT execution GO absent'
    assert go['run_id']==m['run_id'] and go['authorized_entrypoint']==binding(__file__) and go['preparation_seal']==binding(HERE/'preparation-seal.json')
    assert Path(go['remaining_run_result']['path']).resolve()==REMAINING/'result.json','Old pilot is not remaining-run terminal evidence'
    exact(go['remaining_run_result']);r=load(go['remaining_run_result']['path']);assert r['all_terminal'] is True and len(r['results'])==207,'Actual remaining run not terminal'
    start=load(REMAINING/'start.json');assert start['mode']=='remaining' and len(start['batch_ids'])==207
    recovery=ROOT/'06-coding/native-full4481-transport-recovery-v2-sol'
    terminals=[];terminal_times=[]
    for started in recovery.glob('batch-*/attempt-*/dispatch-start.json'):
        p=started.parent/'process-completion.json';assert p.exists(),'Recovery child lacks terminal completion'
        rec=load(p);assert rec['actual_process_terminal'] is True and type(rec['pid']) is int
        exact(rec['events']);exact(rec['stderr']);terminals.append(binding(p));terminal_times.append(datetime.datetime.fromisoformat(rec['at_utc']))
    assert terminals and go['terminal_process_bindings']==sorted(terminals,key=lambda x:x['path']),'GO terminal inventory not exact current completion inventory'
    # No real live production/recovery/stability CLI or controller may share capacity.
    state=subprocess.run(['ps','-axo','pid=,command='],capture_output=True,text=True,check=True).stdout
    live=[]
    for line in state.splitlines():
        pid,_,cmd=line.strip().partition(' ')
        if pid and int(pid)!=os.getpid() and ('recover-native-whole-batches-v4-root.py' in cmd or ('codex' in cmd and ' exec ' in ' '+cmd+' ')):
            live.append({'pid':int(pid),'command':cmd})
    assert not live,'Production/recovery/controller or CLI still live; no competing runner allowed'
    assert go.get('live_cli_pids')==[] and go.get('single_transport_owner') is True
    assert datetime.datetime.fromisoformat(go['at_utc'])>=max([datetime.datetime.fromisoformat(r['at_utc']),*terminal_times]),'ROOT GO precedes actual remaining/child terminal evidence'
    assert go.get('native_v15_full_collection_seal') and Path(go['native_v15_full_collection_seal']['path']).resolve()!=HERE/'preparation-seal.json'
    exact(go['native_v15_full_collection_seal'])
    # Full parent is a future merge prerequisite, not an input to the coding actor.
    parent=Path(go['native_v15_full_collection_seal']['path']).parent;coverage=load(parent/'coverage.json')
    assert coverage['full_corpus_complete'] is True and coverage['selected_record_N']==4481 and coverage['selected_batch_N']==504
    return go
def prompt(m,a,route):
    core=(HERE/'dispatch-core.txt').read_text()
    return core.replace('{ASSIGNMENT}',str(Path(m['batches'][0]['assignment']['path']))).replace('{PRESENT_HELPER}',m['presentation_helper']['path']).replace('{SUBMIT_HELPER}',m['submit_helper']['path']).replace('{FIRST}',route['first_path']).replace('{REPORT}',route['report_path']).replace('{SEAL}',route['seal_path'])
def receive(m,a,route):
    slot=Path(route['output_directory']);rp=slot/'root-reception.json'
    if rp.exists():return load(rp)
    receipt={'at_utc':now(),'run_id':m['run_id'],'batch_id':a['batch_id'],'attempt':route['attempt_number'],'assignment':m['batches'][0]['assignment'],'receiver':m['receiver'],'semantic_correctness_checked':False,'reference_compared':False,'first_or_labels_modified':False}
    try:
        value=module(m['receiver']).verify(HERE/'manifest.json',Path(m['batches'][0]['assignment']['path']),Path(route['first_path']))
        receipt.update(state='technical_valid_whole_batch',first=value['first'],actor_seal=value['actor_seal'],validation=value)
    except Exception as e:receipt.update(state='technical_invalid_whole_batch',error={'type':type(e).__name__,'message':str(e)})
    save(rp,receipt);return receipt
def attempt(m,a,route,go_binding):
    slot=Path(route['output_directory']);assert not (slot/'dispatch-start.json').exists();text=prompt(m,a,route)
    with (slot/'dispatch-prompt.txt').open('x') as f:f.write(text)
    cmd=[m['cli_launcher']['path'],'exec','--ignore-user-config','--skip-git-repo-check','--ephemeral','--json','--color','never','-C',str(slot),'--model','gpt-6.1-sol','-c','model_reasoning_effort="ultra"','-c','approval_policy="never"','--sandbox','workspace-write','-c','features.multi_agent=false','-c','features.memories=false','-c','web_search="disabled"','-c','project_doc_max_bytes=0','--output-last-message',str(slot/'final-message.txt'),'-']
    save(slot/'dispatch-start.json',{'at_utc':now(),'argv':cmd,'run_id':m['run_id'],'batch_id':a['batch_id'],'attempt':route['attempt_number'],'assignment':m['batches'][0]['assignment'],'requested_model':'gpt-6.1-sol','requested_reasoning_effort':'ultra','ROOT_GO':go_binding,'prompt':binding(slot/'dispatch-prompt.txt'),'new_material_round_not_old_retry_or_stability':True})
    with (slot/'cli-events.jsonl').open('xb') as out,(slot/'stderr.txt').open('xb') as err:
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=out,stderr=err,cwd=slot,start_new_session=True)
        try:process.communicate(text.encode(),timeout=2400);timed=False
        except subprocess.TimeoutExpired:
            # Only this entrypoint's own future child process group is affected.
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=20)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            timed=True
    save(slot/'process-completion.json',{'at_utc':now(),'pid':process.pid,'returncode':process.returncode,'timed_out':timed,'actual_process_terminal':True,'events':binding(slot/'cli-events.jsonl'),'stderr':binding(slot/'stderr.txt'),'first_exists':Path(route['first_path']).exists()})
    return receive(m,a,route)
def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['preflight','run'],required=True);p.add_argument('--go');x=p.parse_args();m,a=preflight()
    if x.mode=='preflight':print(json.dumps({'state':'prepared_not_executed','run_id':m['run_id'],'record_N':3,'model_calls':0,'requires_future_ROOT_GO_and_actual_remaining_terminal':True}));return
    assert x.go,'No model dispatch without actual ROOT GO';go=check_go(x.go,m)
    with (HERE/'execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        selection=HERE/'batch-0216/root-selection.json'
        if selection.exists():print(json.dumps(load(selection),ensure_ascii=False));return
        routes=load(a['attempt_output_routing']['path'])['routes']
        for route in routes:
            slot=Path(route['output_directory']);rp=slot/'root-reception.json'
            if rp.exists():r=load(rp)
            elif (slot/'process-completion.json').exists():r=receive(m,a,route)
            else:
                assert not (slot/'dispatch-start.json').exists(),'Interrupted nonterminal attempt; stop for ROOT, do not double dispatch'
                check_go(x.go,m);r=attempt(m,a,route,binding(x.go))
            if r['state']=='technical_valid_whole_batch':
                save(selection,{'artifact_type':'earliest_valid_new_v16_material_whole_batch','at_utc':now(),'run_id':m['run_id'],'batch_id':a['batch_id'],'attempt':route['attempt_number'],'source_ids':a['source_ids'],'assignment':m['batches'][0]['assignment'],'first':r['first'],'reception':binding(rp),'actor_seal':r['actor_seal'],'semantic_scores_not_selection_criteria':True,'original_v15_results_never_overwritten':True,'independent_stability_repeat':False});print(json.dumps(load(selection),ensure_ascii=False));return
        result=HERE/'batch-0216/exhausted.json'
        if not result.exists():save(result,{'at_utc':now(),'state':'three_technical_attempts_exhausted','run_id':m['run_id'],'batch_id':a['batch_id'],'labels_fabricated':False})
        print(json.dumps(load(result),ensure_ascii=False))
if __name__=='__main__':main()

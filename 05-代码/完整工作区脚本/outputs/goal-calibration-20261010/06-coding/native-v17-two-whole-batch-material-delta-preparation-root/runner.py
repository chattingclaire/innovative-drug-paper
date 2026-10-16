"""Two original whole batches, new v17 material. No dispatch without actual ROOT capacity binding.

Preparation/preflight is read-only. Future execution writes only pre-reserved own
slots, uses the existing validated CLI, and never controls any pre-existing PID.
"""
import argparse, datetime, fcntl, hashlib, json, os, signal, subprocess, sys, types
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
if not __debug__:raise RuntimeError('Required binding assertions disabled')

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):return json.loads(Path(p).read_bytes())
def binding(p):
    p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def exact(b):assert binding(b['path'])=={k:b[k] for k in ('path','bytes','sha256')},'Changed binding: '+b['path']
def save(p,x):
    with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def module(b):
    exact(b);m=types.ModuleType('frozen_receiver');m.__file__=b['path'];exec(compile(Path(b['path']).read_bytes(),b['path'],'exec'),m.__dict__);return m
def assignment_binding(m,a):
    return next(b['assignment'] for b in m['batches'] if b['batch_id']==a['batch_id'])
def preflight(batch_id):
    for b in load(HERE/'preparation-seal.json')['files']:exact(b)
    m=load(HERE/'manifest.json')
    for k in ('runner','receiver','base_guard','validator','cli_launcher','instructions','transport_contract','presentation_helper','submit_helper','v17_material_seal','v17_material_manifest','parent_collection_seal'):exact(m[k])
    material=load(m['v17_material_manifest']['path'])
    closure={c['batch_id']:c for c in material['native_whole_batch_closures']}
    assert [b['batch_id'] for b in m['batches']]==['batch-0325','batch-0485']
    assert m['source_N']==24 and m['actual_concurrency_cap']==1
    selected=None
    for batch in m['batches']:
        exact(batch['assignment']);a=load(batch['assignment']['path']);c=closure[batch['batch_id']]
        assert a['batch_id']==batch['batch_id'] and a['run_id']==m['run_id']
        assert a['source_ids']==batch['source_ids']==c['source_ids'] and a['expected_N']==c['expected_N']==12
        assert a['packets']==c['new_packets'] and a['packet_bytes']==sum(p['bytes'] for p in a['packets'])<=c['original_packet_byte_limit']
        assert m['max_total_technical_attempts']==a['max_total_technical_attempts']==3
        for value in a.values():
            if isinstance(value,dict) and {'path','bytes','sha256'}<=set(value):exact(value)
        for b in a['packets']+a['source_asset_bindings']:exact(b)
        if batch['batch_id']==batch_id:selected=a
    assert selected is not None,'Only two bound whole batches are executable'
    return m,selected
def check_go(path,m):
    assert Path(path).resolve()==HERE/'ROOT-execution-binding.json','Use the actual ROOT binding, not the template'
    go=load(path)
    assert go.get('author')=='ROOT' and go.get('template_only') is False and go.get('execution_authorized') is True,'Actual ROOT execution binding absent'
    assert go['run_id']==m['run_id'] and go['authorized_entrypoint']==binding(__file__) and go['preparation_seal']==binding(HERE/'preparation-seal.json')
    assert go['batch_ids']==[b['batch_id'] for b in m['batches']] and go['native_additional_concurrency_cap']==1
    cap=go['capacity_reservation']
    assert cap['confirmed_by_ROOT'] is True and cap['stability_capacity_can_accommodate'] is True
    assert cap['reserved_additional_cli_slots']==1 and cap['reserved_for_run_id']==m['run_id']
    assert cap['existing_stability_configuration_unchanged'] is True and go['single_transport_owner'] is True
    # ROOT records a real current observation and reserves one additional slot.
    # Do not equate existing stability processes with forbidden global CLI activity.
    exact(cap['observed_capacity_evidence'])
    assert datetime.datetime.fromisoformat(cap['observed_at_utc'])<=datetime.datetime.fromisoformat(go['at_utc'])<=datetime.datetime.now(datetime.timezone.utc)
    assert go['parent_collection_seal']==m['parent_collection_seal'];exact(go['parent_collection_seal'])
    coverage=load(Path(go['parent_collection_seal']['path']).parent/'coverage.json')
    assert coverage['full_corpus_complete'] is True and coverage['selected_record_N']==4481 and coverage['selected_batch_N']==504
    return go
def prompt(m,a,route):
    core=(HERE/'dispatch-core.txt').read_text()
    return core.replace('{ASSIGNMENT}',str(Path(assignment_binding(m,a)['path']))).replace('{PRESENT_HELPER}',m['presentation_helper']['path']).replace('{SUBMIT_HELPER}',m['submit_helper']['path']).replace('{FIRST}',route['first_path']).replace('{REPORT}',route['report_path']).replace('{SEAL}',route['seal_path'])
def receive(m,a,route):
    slot=Path(route['output_directory']);rp=slot/'root-reception.json'
    if rp.exists():return load(rp)
    receipt={'at_utc':now(),'run_id':m['run_id'],'batch_id':a['batch_id'],'attempt':route['attempt_number'],'assignment':assignment_binding(m,a),'receiver':m['receiver'],'semantic_correctness_checked':False,'reference_compared':False,'first_or_labels_modified':False}
    try:
        value=module(m['receiver']).verify(HERE/'manifest.json',Path(assignment_binding(m,a)['path']),Path(route['first_path']))
        receipt.update(state='technical_valid_whole_batch',first=value['first'],actor_seal=value['actor_seal'],validation=value)
    except Exception as e:receipt.update(state='technical_invalid_whole_batch',error={'type':type(e).__name__,'message':str(e)})
    save(rp,receipt);return receipt
def attempt(m,a,route,go_binding):
    slot=Path(route['output_directory']);slot.mkdir(parents=True,exist_ok=True);assert not (slot/'dispatch-start.json').exists();text=prompt(m,a,route)
    with (slot/'dispatch-prompt.txt').open('x') as f:f.write(text)
    cmd=[m['cli_launcher']['path'],'exec','--ignore-user-config','--skip-git-repo-check','--ephemeral','--json','--color','never','-C',str(slot),'--model','gpt-6.1-sol','-c','model_reasoning_effort="ultra"','-c','approval_policy="never"','--sandbox','workspace-write','-c','features.multi_agent=false','-c','features.memories=false','-c','web_search="disabled"','-c','project_doc_max_bytes=0','--output-last-message',str(slot/'final-message.txt'),'-']
    save(slot/'dispatch-start.json',{'at_utc':now(),'argv':cmd,'run_id':m['run_id'],'batch_id':a['batch_id'],'attempt':route['attempt_number'],'assignment':assignment_binding(m,a),'requested_model':'gpt-6.1-sol','requested_reasoning_effort':'ultra','ROOT_GO':go_binding,'prompt':binding(slot/'dispatch-prompt.txt'),'new_material_round_not_old_retry_or_stability':True})
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
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['preflight','run'],required=True);p.add_argument('--batch-id',choices=['batch-0325','batch-0485'],required=True);p.add_argument('--go');x=p.parse_args();m,a=preflight(x.batch_id)
    if x.mode=='preflight':print(json.dumps({'state':'prepared_not_executed','run_id':m['run_id'],'batch_id':a['batch_id'],'record_N':12,'model_calls':0,'requires_actual_ROOT_capacity_binding':True}));return
    assert x.go,'No model dispatch without actual ROOT GO';go=check_go(x.go,m)
    with (HERE/'execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        selection=HERE/a['batch_id']/'root-selection.json'
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
                save(selection,{'artifact_type':'earliest_valid_new_v17_material_whole_batch','at_utc':now(),'run_id':m['run_id'],'batch_id':a['batch_id'],'attempt':route['attempt_number'],'source_ids':a['source_ids'],'assignment':assignment_binding(m,a),'first':r['first'],'reception':binding(rp),'actor_seal':r['actor_seal'],'semantic_scores_not_selection_criteria':True,'original_results_never_overwritten':True,'independent_stability_repeat':False});print(json.dumps(load(selection),ensure_ascii=False));return
        result=HERE/a['batch_id']/'exhausted.json'
        if not result.exists():save(result,{'at_utc':now(),'state':'three_technical_attempts_exhausted','run_id':m['run_id'],'batch_id':a['batch_id'],'labels_fabricated':False})
        print(json.dumps(load(result),ensure_ascii=False))
if __name__=='__main__':main()

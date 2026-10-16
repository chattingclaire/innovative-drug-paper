"""GO-only additive fix for three historically cancelled pilot children.

Preserves the sealed core runner, all scientific inputs and attempt machinery.
No process is killed. Unknown historic exit codes remain unknown.
"""
import datetime, hashlib, json, os, subprocess, types
from pathlib import Path
H=Path(__file__).resolve().parent
def load(p):return json.loads(Path(p).read_bytes())
def binding(p):
    p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def exact(b):assert binding(b['path'])=={k:b[k] for k in ('path','bytes','sha256')}
def main():
    profile=load(H/'terminal-sidecar-entry-binding.json')
    for k in ('core_runner','entrypoint','parent_preparation_seal','historical_stop_record','historical_runtime_repair'):exact(profile[k])
    assert profile['entrypoint']==binding(__file__)
    for b in load(H/'terminal-sidecar-entry-seal.json')['files']:exact(b)
    core=types.ModuleType('sealed_core_runner');core.__file__=profile['core_runner']['path'];exec(compile(Path(core.__file__).read_bytes(),core.__file__,'exec'),core.__dict__)
    core.check_go=lambda path,m:check_go(path,m,core,profile)
    core.main()

def check_go(path,m,core,profile):
    go=load(path);assert go.get('author')=='ROOT' and go.get('execution_authorized') is True,'Actual ROOT GO absent'
    assert go['run_id']==m['run_id'] and go['authorized_entrypoint']==binding(__file__)
    assert go['preparation_seal']==binding(H/'preparation-seal.json') and go['terminal_entry_seal']==binding(H/'terminal-sidecar-entry-seal.json')
    assert Path(go['remaining_run_result']['path']).resolve()==core.REMAINING/'result.json','Pilot result cannot substitute remaining terminal result'
    exact(go['remaining_run_result']);r=load(go['remaining_run_result']['path']);assert r['all_terminal'] is True and len(r['results'])==207
    start=load(core.REMAINING/'start.json');assert start['mode']=='remaining' and len(start['batch_ids'])==207
    recovery=core.ROOT/'06-coding/native-full4481-transport-recovery-v2-sol'
    terminals=[];missing=[];times=[datetime.datetime.fromisoformat(r['at_utc'])]
    for started in recovery.glob('batch-*/attempt-*/dispatch-start.json'):
        p=started.parent/'process-completion.json'
        if not p.exists():missing.append(binding(started));continue
        rec=load(p);assert rec['actual_process_terminal'] is True and type(rec['pid']) is int
        exact(rec['events']);exact(rec['stderr']);terminals.append(binding(p));times.append(datetime.datetime.fromisoformat(rec['at_utc']))
    assert go['terminal_process_bindings']==sorted(terminals,key=lambda b:b['path'])
    # This exact, frozen list is technical cancellation provenance, not a semantic ID selection.
    expected=profile['historical_cancelled_dispatch_bindings']
    for b in expected:exact(b)
    assert sorted(missing,key=lambda b:b['path'])==expected,'Unexplained unfinished dispatch; no GO'
    witness_binding=go['historic_cancelled_terminal_observation'];exact(witness_binding);w=load(witness_binding['path'])
    assert w['author']=='ROOT' and w['observation_is_actual'] is True and w['historical_exit_codes_known'] is False
    assert w['cancelled_dispatch_bindings']==expected and w['historical_stop_record']==profile['historical_stop_record']
    assert w['no_live_matching_cli_or_controller_observed'] is True and w['clean_completion_claimed'] is False
    exact(w['actual_ps_snapshot']);times.append(datetime.datetime.fromisoformat(w['observed_at_utc']))
    # Check the actual saved observation and an independent current process inventory.
    for state in (Path(w['actual_ps_snapshot']['path']).read_text(),subprocess.run(['ps','-axo','pid=,command='],capture_output=True,text=True,check=True).stdout):
        live=[]
        for line in state.splitlines():
            pid,_,cmd=line.strip().partition(' ')
            if pid and int(pid)!=os.getpid() and ('recover-native-whole-batches-v4-root.py' in cmd or ('codex' in cmd and ' exec ' in ' '+cmd+' ')):
                live.append(int(pid))
        assert not live,'Live production/recovery/controller or CLI; no competing runner'
    assert go['live_cli_pids']==[] and go['single_transport_owner'] is True
    assert datetime.datetime.fromisoformat(go['at_utc'])>=max(times),'ROOT GO predates real terminal observations'
    exact(go['native_v15_full_collection_seal']);parent=Path(go['native_v15_full_collection_seal']['path']).parent;c=load(parent/'coverage.json')
    assert c['full_corpus_complete'] is True and c['selected_record_N']==4481 and c['selected_batch_N']==504
    return go

if __name__=='__main__':main()

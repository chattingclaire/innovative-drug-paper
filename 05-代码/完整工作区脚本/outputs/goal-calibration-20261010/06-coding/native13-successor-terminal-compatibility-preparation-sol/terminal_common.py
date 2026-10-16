"""External terminal metadata only. No inference, signals, old-file edits or GO issuance."""
import datetime, hashlib, json, os, re, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
H = BASE / '06-coding/native-whole-capacity13-handoff-preparation-sol'
N = BASE / '06-coding/native-v16-batch0216-material-delta-preparation-sol'
ST = BASE / '06-coding/current-freeze-stability-capacity13-transport-sol'
ISOLATED = str(BASE / '06-coding/isolated-codex-cli-0.162.1-root')
RECOVERY = str(BASE / '06-coding/native-full4481-transport-recovery-v2-sol')

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p): return json.loads(Path(p).read_bytes())
def bind(p):
    p = Path(p).resolve(); raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
def exact(b):
    assert bind(b['path']) == {k:b[k] for k in ('path','bytes','sha256')}, 'Changed binding: ' + b['path']
def save(p, d):
    with Path(p).open('x', encoding='utf8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')
def assert_preparation():
    for b in load(HERE/'seal.json')['files']: exact(b)
    for b in load(HERE/'manifest.json')['immutable_input_bindings']: exact(b)
def ps_rows():
    raw = subprocess.run(['ps','-axo','pid=,ppid=,pgid=,stat=,lstart=,command='], capture_output=True, text=True, check=True).stdout
    rows = []
    for line in raw.splitlines():
        m = re.fullmatch(r'\s*(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(.{24})\s+(.*)', line)
        assert m, 'Unparsed actual ps line; no absence claim'
        pid,ppid,pgid,stat,lstart,cmd = m.groups()
        rows.append({'pid':int(pid),'ppid':int(ppid),'pgid':int(pgid),'stat':stat,'lstart':lstart,'command':cmd})
    assert rows, 'Empty ps is not absence evidence'
    return rows
def metadata(row):
    d = {k:row[k] for k in ('pid','ppid','pgid','stat','lstart')}
    d['command_sha256'] = hashlib.sha256(row['command'].encode()).hexdigest()
    return d
def same_identity(a,b): return a['pid']==b['pid'] and a['lstart']==b['lstart']
def owned(rows, known, pgids, lease_pids=()):
    """Conservative union; separate-PGID isolated hosts remain visible after reparenting."""
    found = set()
    for r in rows:
        cmd = r['command']
        if (any(same_identity(r,k) for k in known) or r['pgid'] in pgids or r['pid'] in lease_pids
            or 'recover-native-whole-batches-v4-root.py' in cmd
            or 'native-whole-capacity13-handoff-preparation-sol/runner.py --mode run' in cmd
            or ('codex' in cmd and ' exec ' in ' '+cmd+' ')
            or (ISOLATED in cmd and ('codex-code-mode-host' in cmd or (' exec ' in ' '+cmd+' ')))
            or (RECOVERY in cmd and 'codex' in cmd)):
            found.add(r['pid'])
    while True:
        nxt = found | {r['pid'] for r in rows if r['ppid'] in found}
        if nxt == found: break
        found = nxt
    return [r for r in rows if r['pid'] in found]
def leases():
    values = []
    for p in sorted((H/'runtime/leases').glob('*.json')):
        d = load(p)
        if d.get('actual_process_created') is True:
            assert type(d.get('pid')) is int and type(d.get('controller_pid')) is int
            values.append((bind(p),d))
    return values
def old_evidence():
    terminal = load(H/'observations/terminal-root-01/observation.json')
    assert terminal['stage']=='terminal' and terminal['old_controller_and_known_descendants_absent'] is True and terminal['owned_processes']==[]
    pause = load(H/'ROOT-pause-operation-01.json'); kill = load(H/'ROOT-terminate-operation-01.json')
    # Operator evidence remains literal: interruption is not clean completion.
    assert pause['actor']=='ROOT' and kill['actor']=='ROOT'
    assert kill['old_v4_execution_status']=='transport_interrupted_not_complete' and kill['old_dispatch_permanently_closed_by_termination'] is True
    assert pause['actual_signal']=='SIGSTOP' and kill['actual_signal']=='SIGKILL'
    assert same_identity(pause['controller_identity'],terminal['controller_identity']) and same_identity(kill['controller_identity'],terminal['controller_identity'])
    exact(kill['frozen_observation']); exact(kill['pause_operation'])
    assert kill['fresh_identity_and_T_state_verified_before_signal'] is True and kill['fresh_uncompleted_third_slot_N']==0
    for batch in terminal['slot_history']:
        for slot in batch['slots']:
            if slot.get('unknown_original_outcome'):
                assert slot['preserved_unknown_slot_files'], 'Unknown old slot lacks preserved literal bindings'
                for b in slot['preserved_unknown_slot_files']: exact(b)
                # Unknown old completion is not fabricated by this helper.
                assert not (Path(slot['path'])/'process-completion.json').exists()
    return terminal
def require_actual_request(p):
    d = load(p)
    assert d.get('issuer')=='ROOT' and d.get('template_only') is False and d.get('actual_terminal_certificate_authorized') is True, 'Actual ROOT certificate request absent'
    assert d['successor_preparation_seal']==bind(HERE/'seal.json')
    return d
def verify_certificate(b, fresh=False):
    exact(b); d = load(b['path'])
    assert d['issuer']=='ROOT' and d['template_only'] is False and d['status']=='actual_primary_and_recovery_all_terminal'
    assert d['successor_preparation_seal']==bind(HERE/'seal.json') and d['all_child_processes_terminal'] is True and d['active_model_process_N']==0
    for x in d['terminal_evidence_bindings']: exact(x)
    proof = load(d['terminal_evidence_bindings'][0]['path'])
    assert proof['all_primary_and_recovery_terminal'] is True and proof['old_v4_status']=='transport_interrupted_not_complete'
    for x in proof['binding_inventory']: exact(x)
    obs = load(proof['new13_terminal_observation']['path'])
    assert obs['stage']=='terminal' and obs['owned_processes']==[] and obs['new_controller_and_all_known_descendants_absent'] is True
    if fresh:
        active = owned(ps_rows(),obs['known_owned_process_identity_registry'],set(obs['tracked_pgids']),obs['all_lease_pids'])
        assert not active, 'Production/recovery/isolated CLI host is still present'
    return d
def create_certificate(request_path, output):
    assert_preparation(); req = require_actual_request(request_path)
    for key in ('native_full_collection_seal','new13_result','new13_terminal_observation','new13_controller_exit_evidence'): exact(req[key])
    assert Path(req['new13_result']['path']).resolve()==H/'runtime/result.json'
    assert req.get('production_and_recovery_dispatch_closed') is True
    old = old_evidence(); registry = load(H/'ROOT-actual-startup-process-registry-v2.json')
    result = load(req['new13_result']['path'])
    assert result['full_requested_continuation_complete'] is True and result['all_this_controller_futures_completed'] is True
    assert result['remaining_unselected_batch_ids']==[] and result['owned_controller_CLI_descendants_present']==[] and result['snapshot_owned_children_absent'] is True
    assert result['old_v4_remains_transport_interrupted_not_complete'] is True and result['budget_reset'] is False
    obs = load(req['new13_terminal_observation']['path'])
    assert obs['observer']==bind(HERE/'observe.py') and obs['successor_preparation_seal']==bind(HERE/'seal.json')
    assert obs['startup_registry']==bind(H/'ROOT-actual-startup-process-registry-v2.json') and obs['runtime_start']==bind(H/'runtime/start.json')
    assert obs['stage']=='terminal' and obs['owned_processes']==[] and obs['new_controller_and_all_known_descendants_absent'] is True
    assert obs['controller_identity']==registry['controller_identity'] and obs['runtime_result']==req['new13_result']
    actual_leases=leases(); assert obs['lease_bindings']==[b for b,_ in actual_leases]
    ex = load(req['new13_controller_exit_evidence']['path'])
    assert ex.get('issuer')=='ROOT' and ex.get('template_only') is False and ex.get('actual_controller_process_terminal') is True
    assert ex['actual_exec_session']==registry['actual_exec_session'] and ex['controller_identity']==registry['controller_identity']
    assert type(ex['actual_observed_returncode']) is int and ex.get('observation_basis')=='actual_exec_session_completion'
    active = owned(ps_rows(),obs['known_owned_process_identity_registry'],set(obs['tracked_pgids']),obs['all_lease_pids'])
    assert not active, 'Fresh actual process/independent host check failed'
    seal = load(req['native_full_collection_seal']['path']); parent=Path(req['native_full_collection_seal']['path']).parent
    for b in seal['files']: exact(b)
    cov=load(parent/'coverage.json')
    assert cov['full_corpus_complete'] is True and cov['selected_record_N']==4481 and cov['selected_batch_N']==504
    assert cov['missing_record_N']==0 and cov['pointer_quote_issue_N']==0 and cov['thin35_included'] is False and cov['first_values_changed'] is False and cov['selection_by_semantic_metric'] is False
    assert cov['recovery_manifest']==load(H/'runtime/start.json')['original_manifest']
    exact(cov['original_manifest'])
    original=load(cov['original_manifest']['path'])
    selected=load(parent/'selected-whole-batch-bindings.json')
    assert len(selected)==len(original['batches'])==504
    original_by_id={b['batch_id']:b for b in original['batches']}
    assert set(x['batch_id'] for x in selected)==set(original_by_id) and len(set(x['batch_id'] for x in selected))==504
    for x in selected: assert x['source_ids']==original_by_id[x['batch_id']]['source_ids'], 'Changed original whole-batch membership/order'
    assert sum(len(x['source_ids']) for x in selected)==4481
    assert datetime.datetime.fromisoformat(req['at_utc'])>=max(datetime.datetime.fromisoformat(x['at_utc']) for x in (result,obs,ex,cov))
    out=Path(output).resolve(); assert out.is_relative_to(HERE/'certificates') and not out.exists(); out.mkdir(parents=True)
    inventory=[bind(request_path), req['native_full_collection_seal'], req['new13_result'], req['new13_terminal_observation'],req['new13_controller_exit_evidence'],bind(H/'runtime/start.json'),bind(H/'ROOT-actual-startup-process-registry-v2.json'),bind(H/'observations/terminal-root-01/observation.json'),bind(H/'ROOT-pause-operation-01.json'),bind(H/'ROOT-terminate-operation-01.json')]
    proof={'at_utc':now(),'all_primary_and_recovery_terminal':True,'old_v4_status':'transport_interrupted_not_complete','old_remaining_result_not_required_or_fabricated':True,'new13_terminal_observation':req['new13_terminal_observation'],'binding_inventory':inventory,'full_original_record_N':4481,'full_original_batch_N':504,'old_unknown_historical_outcomes_disclosed':True,'no_clean_old_exit_claim':True,'model_calls':0,'signals_sent_N':0,'issuer_basis':'mechanical helper under explicit ROOT certificate request'}
    save(out/'terminal-proof.json',proof)
    pids=set(obs['all_lease_pids']) | {r['pid'] for r in obs['known_owned_process_identity_registry']} | {old['controller_identity']['pid']}
    certificate={'at_utc':now(),'issuer':'ROOT','status':'actual_primary_and_recovery_all_terminal','template_only':False,'all_child_processes_terminal':True,'active_model_process_N':0,'terminal_evidence_bindings':[bind(out/'terminal-proof.json')],'closed_controller_and_child_pids':sorted(pids),'successor_preparation_seal':bind(HERE/'seal.json'),'native_full_collection_seal':req['native_full_collection_seal'],'production_and_recovery_dispatch_closed':True,'old_v4_status':'transport_interrupted_not_complete','new13_status':'actual_complete_with_fresh_independent_host_absence','formal_validation_complete':False}
    save(out/'production-terminal-certificate.json',certificate)
    return bind(out/'production-terminal-certificate.json')

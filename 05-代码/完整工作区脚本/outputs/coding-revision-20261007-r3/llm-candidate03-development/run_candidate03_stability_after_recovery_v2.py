"""Separately authorized stability after transparent 221-request reconciliation."""
import datetime, itertools, json, os, pathlib, subprocess, sys
from candidate03_execution_audit_utils_v2 import audit, bind, dump, lines, read, sha
from run_and_audit_candidate03_stability import pair_metrics
H = pathlib.Path(__file__).resolve().parent
P = H / 'candidate03-stability-plan'
LOCK = P / 'stability_execution_v2.lock'
SUPPLEMENT = P / 'candidate03_stability_after_recovery_supplement_v2.json'
DIMS = ['S', 'E', 'Ec', 'I', 'F']
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def check_all(x):
    if isinstance(x, dict):
        if isinstance(x.get('path'), str) and isinstance(x.get('sha256'), str):
            if sha(x['path']) != x['sha256']: raise RuntimeError('Binding mismatch: ' + x['path'])
        for v in x.values(): check_all(v)
    elif isinstance(x, list):
        for v in x: check_all(v)

def main():
    if sys.flags.optimize != 0: raise RuntimeError('Python optimization must be zero.')
    supplement = read(SUPPLEMENT); check_all(supplement)
    authfile = P / 'root_stability_after_recovery_authorization_v2.json'; auth = read(authfile); check_all(auth)
    assert auth['status'] == 'passed_root_stability_after_recovery_review' and auth['plan_sha256'] == sha(SUPPLEMENT)
    assert auth['new_calls_authorized'] == 9 and auth['technical_max_attempts'] == 27
    plan = read(pathlib.Path(supplement['original_stability_plan']['path'])); check_all(plan)
    fullfile = pathlib.Path(supplement['required_reconciled_binding_path']); full = read(fullfile); check_all(full)
    assert auth['reconciled_full_binding'] == bind(fullfile)
    assert full['status'] == 'complete_actual_full_corpus_development_reconciled_QA_PASS'
    assert full['method_id'] == 'LLM-v32-candidate03-single-unit-reconciled-development'
    assert full['n'] == 4924 and full['batches'] == 221 and full['source_production_batches'] == 197 and full['original_terminal_failed_batches'] == [115]
    assert full['prompt']['sha256'] == plan['base_prompt']['sha256'] and full['source_input']['sha256'] == plan['source']['sha256']
    assert full['requested_model'] == 'gpt-5.6-sol' and full['reasoning_effort'] == 'medium'
    full_qa = read(pathlib.Path(full['technical_QA']['path']))
    assert full_qa['status'] == 'PASS' and full_qa['original_accepted_batches'] == 196 and full_qa['recovery_logical_single_unit_calls'] == 25
    recovery_state = read(pathlib.Path(supplement['required_recovery_state_path']))
    assert recovery_state['status'] == 'complete_recovery_and_transparent_reconciliation_QA_PASS'
    assert recovery_state['reconciled_binding'] == bind(fullfile)
    assert [b['production_batch'] for b in plan['batches']] == [13, 147, 47]
    assert all(b['production_batch'] != 115 for b in plan['batches'])
    for item in plan['planned_runs']: assert not pathlib.Path(item['run_directory']).exists(), 'No rerun or overwrite.'
    sample = lines(pathlib.Path(plan['sample']['path'])); ids = [r['id'] for r in sample]
    assert len(ids) == len(set(ids)) == 75
    base = {r['id']: r for r in lines(pathlib.Path(full['output']['path'])) if r['id'] in set(ids)}
    original = pathlib.Path(full['original_run'])
    for batch in plan['batches']:
        b = original / 'batches' / f"batch-{batch['production_batch']:04d}"
        assert sha(b / 'request.txt') == batch['base_request_sha256']
        selected = read(b / 'selection.json'); raw = read(original / selected['selected_relative_path'] / 'raw_output.json')
        assert [base[i] for i in batch['all_ids']] == raw['rows']
    state = {'status': 'running_after_reconciled_QA_and_new_authorization', 'started_at': now(), 'executor_pid': os.getpid(), 'actual_driver_command': [sys.executable, *sys.argv], 'lock': str(LOCK), 'plan': bind(SUPPLEMENT), 'authorization': bind(authfile), 'full_binding': bind(fullfile), 'python_optimize': 0, 'child_PYTHONOPTIMIZE_removed': True, 'conditions': []}
    dump(P / 'execution_state_v2.json', state)
    child_env = os.environ.copy(); child_env.pop('PYTHONOPTIMIZE', None)
    for item in plan['planned_runs']:
        if any(a in {'-O', '-OO'} for a in item['command']): raise RuntimeError('Optimization flags forbidden.')
        rec = {'condition': item['condition'], 'command': item['command'], 'started_at': now()}; state['conditions'].append(rec)
        dump(P / 'execution_state_v2.json', state); log = P / (item['condition'] + '.v2.stdout.log')
        print(json.dumps({'starting_condition': item['condition'], 'time': now()}), flush=True)
        with log.open('w') as f:
            proc = subprocess.Popen(item['command'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=child_env)
            rec['runner_pid'] = proc.pid; dump(P / 'execution_state_v2.json', state)
            for line in proc.stdout: f.write(line); f.flush(); print(line, end='', flush=True)
            rec['exit_code'] = proc.wait()
        rec['ended_at'] = now(); rec['stdout'] = bind(log); dump(P / 'execution_state_v2.json', state)
    if any(c['exit_code'] != 0 for c in state['conditions']):
        state['status'] = 'technical_incomplete_no_extra_calls'; dump(P / 'execution_state_v2.json', state)
        raise RuntimeError('Stability incomplete; no extension or substituted output.')
    by = {'base1-full-run': base}; qa_paths = []; qas = []
    for item in plan['planned_runs']:
        run = pathlib.Path(item['run_directory'])
        accepted, qa, _ = audit(run, 75, 25, item['input']['sha256'], item['prompt']['sha256'], [])
        assert [sha(run / 'batches' / f'batch-{i:04d}' / 'request.txt') for i in range(1, 4)] == [b['order_request_sha256' if item['condition'] == 'order-perturbation' else 'base_request_sha256'] for b in plan['batches']]
        by[item['condition']] = {r['id']: r for i in range(1, 4) for r in accepted[i]['raw']['rows']}
        qp = run / 'execution_binding_QA_v2.json'; dump(qp, qa); qa_paths.append(bind(qp)); qas.append(qa)
    identical = ['base1-full-run', 'base-repeat-2', 'base-repeat-3']
    pairs = [(a, b, 'identical_prompt') for a, b in itertools.combinations(identical, 2)] + [('order-perturbation', b, 'order_sensitivity') for b in identical]
    metrics = []; differences = []
    groups = [('overall75', ids)] + [(f"intact_batch_{b['production_batch']}_mixed_department", b['all_ids']) for b in plan['batches']]
    for left, right, kind in pairs:
        for group, gids in groups:
            for d in DIMS + ['pooled_5_labels']:
                metrics.append({'comparison_type': kind, 'left': left, 'right': right, 'group': group, 'dimension': d, **pair_metrics(by[left], by[right], gids, DIMS if d == 'pooled_5_labels' else [d])})
        for i in ids:
            dims = [d for d in DIMS if by[left][i]['labels'][d] != by[right][i]['labels'][d]]
            if dims: differences.append({'id': i, 'left_condition': left, 'right_condition': right, 'comparison_type': kind, 'dimensions': dims, 'frozen_input': next(r for r in sample if r['id'] == i), 'left_original_row': by[left][i], 'right_original_row': by[right][i]})
    all3 = {'n': 75, 'exact_five_dimension_rows': sum(all(by[c][i]['labels'] == base[i]['labels'] for c in identical[1:]) for i in ids), 'dimension_agreement_counts': {d: sum(len({by[c][i]['labels'][d] for c in identical}) == 1 for i in ids) for d in DIMS}}
    result = {'status': 'complete_actual_candidate03_stability_after_transparent_recovery', 'n': 75, 'new_logical_calls': 9, 'actual_new_attempts': sum(q['actual_attempts'] for q in qas), 'failed_attempts_preserved': sum(q['failed_attempts_preserved'] for q in qas), 'all_three_identical_prompt': all3, 'pairwise_metrics': metrics, 'scope': supplement['stability_scope'], 'formal_adoption': False, 'independent_validation': False}
    assert result['actual_new_attempts'] <= 27
    dump(P / 'stability_metrics_v2.json', result); dump(P / 'all_original_disagreements_v2.json', {'disagreements': differences})
    check_all(full)
    state['status'] = 'complete_all9_calls_and_execution_QA_PASS'; state['ended_at'] = now(); dump(P / 'execution_state_v2.json', state)
    binding = {'status': state['status'], 'plan': bind(SUPPLEMENT), 'authorization': bind(authfile), 'reconciled_full_binding': bind(fullfile), 'metrics': bind(P / 'stability_metrics_v2.json'), 'disagreements': bind(P / 'all_original_disagreements_v2.json'), 'execution_state': bind(P / 'execution_state_v2.json'), 'run_QAs': qa_paths, 'scope': supplement['stability_scope'], 'new_logical_calls': 9, 'actual_new_attempts': result['actual_new_attempts'], 'failed_attempts_preserved': result['failed_attempts_preserved'], 'full_run_rows_replaced': False}
    dump(P / 'stability_final_binding_v2.json', binding)
    print(json.dumps({'binding': bind(P / 'stability_final_binding_v2.json'), 'all_three': all3}, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    if sys.flags.optimize != 0: raise RuntimeError('Python optimization must be zero; no actions taken.')
    if len(sys.argv) != 1: raise RuntimeError('Single authorized execution only; no retry/audit mode.')
    fd = os.open(LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as lock:
        lock.write(json.dumps({'pid': os.getpid(), 'actual_command': [sys.executable, *sys.argv], 'plan_sha256': sha(SUPPLEMENT), 'time': now()}) + '\n'); lock.flush()
        try: main()
        except BaseException as e:
            lock.write(json.dumps({'status': 'stopped_no_automatic_cleanup', 'error': type(e).__name__, 'message': str(e)}) + '\n'); lock.flush(); raise
        else:
            lock.write(json.dumps({'status': 'completed_lock_retained', 'time': now()}) + '\n'); lock.flush()

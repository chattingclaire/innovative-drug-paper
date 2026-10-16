"""Execute only the authorized, frozen nine-call stability plan after full QA.

Never replace any full-run row or select a repeat by agreement. Run conditions
sequentially; the frozen runner permits at most three simultaneous model calls.
"""
import collections, datetime, hashlib, importlib.util, itertools, json, pathlib, subprocess, sys

H = pathlib.Path(__file__).resolve().parent
P = H / 'candidate03-stability-plan'
FULL = H / 'full-corpus-candidate03-material-v14-development'
DIMS = ['S', 'E', 'Ec', 'I', 'F']
PLAN_SHA = '123e5c2b8d372b30371d1be08690d6465e58e2b2e0e93a6c336bb4dcca8abdf2'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def lines(p): return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def dump(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')
def bind(p): return {'path': str(p), 'sha256': sha(p)}
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def check_binding(b): assert sha(pathlib.Path(b['path'])) == b['sha256'], b

def check_events(p):
    result = {'completed': 0, 'violations': [], 'turn_errors': [], 'observed_models': []}
    for i, line in enumerate(p.read_text().splitlines(), 1):
        if not line.strip(): continue
        try: e = json.loads(line)
        except ValueError: result['violations'].append({'line': i, 'kind': 'not_json'}); continue
        typ = e.get('type'); item = e.get('item')
        it = item.get('type') if isinstance(item, dict) else None
        if it is not None and it not in {'agent_message', 'reasoning'}:
            result['violations'].append({'line': i, 'kind': it})
        if isinstance(typ, str) and any(t in typ.lower() for t in ['tool_call', 'function_call', 'web_search', 'web_fetch', 'command_execution']):
            result['violations'].append({'line': i, 'kind': typ})
        if typ == 'turn.completed': result['completed'] += 1
        if typ in {'turn.failed', 'error'}: result['turn_errors'].append(e)
        for field in ['model', 'model_name']:
            if isinstance(e.get(field), str) and e[field] not in result['observed_models']:
                result['observed_models'].append(e[field])
    return result

def audit_run(item, frozen_plan):
    run = pathlib.Path(item['run_directory'])
    plan = read(run / 'run_plan.json'); summary = read(run / 'execution_summary.json')
    assert summary['status'] == 'complete_actual_calls_structurally_valid'
    assert plan['n'] == 75 and plan['batch_count'] == 3 and plan['batch_size'] == 25 and plan['max_attempts'] == 3
    assert plan['model'] == 'gpt-5.6-sol' and plan['reasoning_effort'] == 'medium'
    assert plan['prompt_sha256'] == item['prompt']['sha256'] == sha(run / 'frozen_prompt.txt')
    assert plan['input_sha256'] == item['input']['sha256'] == sha(run / 'frozen_input.jsonl')
    for key, file in [('schema', 'frozen_schema.json'), ('validator', 'frozen_validator.py'), ('runner', 'frozen_runner.py')]:
        assert plan[key + '_sha256'] == sha(run / file)
    assert plan['cli_binary_sha256'] == sha(pathlib.Path(plan['cli_path']))
    spec = importlib.util.spec_from_file_location('stability_validator', run / 'frozen_validator.py')
    validator = importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
    source = lines(run / 'frozen_input.jsonl'); prompt = (run / 'frozen_prompt.txt').read_text()
    output = []; issues = []; attempts_audit = []; provenance = []
    for bi in range(1, 4):
        b = run / 'batches' / f'batch-{bi:04d}'
        packet = read(b / 'input.json'); selection = read(b / 'selection.json')
        assert packet == {'rows': source[(bi - 1) * 25:bi * 25]}
        assert selection['ids'] == [r['id'] for r in packet['rows']]
        assert selection['status'] == 'accepted_first_valid_actual_attempt'
        request = prompt + '\n\n--- 本批冻结盲法输入 ---\n' + json.dumps(packet, ensure_ascii=False) + '\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
        assert (b / 'request.txt').read_text() == request
        condition_hash = 'order_request_sha256' if item['condition'] == 'order-perturbation' else 'base_request_sha256'
        assert sha(b / 'request.txt') == frozen_plan['batches'][bi - 1][condition_hash]
        attempts = sorted((b / 'attempts').glob('attempt-*'))
        assert 1 <= len(attempts) <= 3
        assert [a.name for a in attempts] == [f'attempt-{i:02d}' for i in range(1, len(attempts) + 1)]
        valid_attempts = []
        for ai, a in enumerate(attempts, 1):
            m = read(a / 'run_metadata.json'); saved = read(a / 'validation.json')
            assert read(a / 'input.json') == packet and (a / 'request.txt').read_text() == request
            for key, file in [('input', 'input.json'), ('request', 'request.txt'), ('events', 'events.jsonl'), ('stderr', 'raw_stderr.txt'), ('tool_event_audit', 'tool_event_audit.json'), ('validation', 'validation.json')]:
                assert m[key + '_sha256'] == sha(a / file)
            assert m['prompt_sha256'] == item['prompt']['sha256']
            assert m['requested_model'] == 'gpt-5.6-sol' and m['reasoning_effort'] == 'medium'
            assert m['cli_binary_sha256'] == plan['cli_binary_sha256'] and m['cli_version'] == plan['cli_version']
            c = m['command']
            assert c[0] == plan['cli_path'] and c[c.index('--model') + 1] == 'gpt-5.6-sol'
            assert 'model_reasoning_effort="medium"' in c and 'web_search="disabled"' in c
            assert all(flag in c for flag in ['--ignore-user-config', '--ignore-rules', '--ephemeral'])
            assert c[c.index('--sandbox') + 1] == 'read-only'
            ev = check_events(a / 'events.jsonl'); raw = a / 'raw_output.json'
            if raw.exists():
                assert sha(raw) == m['raw_output_sha256']
                try: errors = validator.validate(packet, read(raw))
                except Exception as e: errors = [f'{type(e).__name__}:{e}']
            else: errors = ['missing_raw_output']
            valid = m['exit_code'] == 0 and not errors and ev['completed'] == 1 and not ev['violations'] and not ev['turn_errors'] and all(z == 'gpt-5.6-sol' for z in ev['observed_models'])
            assert valid == saved['valid'] == (m['status'] == 'accepted_structural_literal_zero_tools')
            assert len(ev['violations']) == m['tool_event_count'] == read(a / 'tool_event_audit.json')['tool_or_unknown_item_event_count']
            assert selection['attempts'][ai - 1]['metadata_sha256'] == sha(a / 'run_metadata.json')
            attempts_audit.append({'batch': bi, 'attempt': ai, 'metadata': bind(a / 'run_metadata.json'), 'valid': valid, 'event_check': ev, 'validation_errors': errors, 'original_execution_errors': m['errors']})
            if valid: valid_attempts.append(a)
        assert valid_attempts and valid_attempts[0] == attempts[-1]
        a = valid_attempts[0]; m = read(a / 'run_metadata.json'); raw = read(a / 'raw_output.json')
        assert selection['selected_relative_path'] == str(a.relative_to(run)) and selection['selected_output_sha256'] == sha(a / 'raw_output.json')
        output.extend(raw['rows']); issues.extend(raw['issue_records'])
        for row in raw['rows']:
            provenance.append({'id': row['id'], 'condition': item['condition'], 'original_production_batch': frozen_plan['batches'][bi - 1]['production_batch'], 'local_batch': bi, 'selected_attempt': str(a), 'actual_prompt_sha256': item['prompt']['sha256'], 'actual_request_sha256': m['request_sha256'], 'raw_output_sha256': m['raw_output_sha256'], 'metadata_sha256': sha(a / 'run_metadata.json'), 'all_five_labels_from_one_intact_actual_row': True})
    aggregate = read(run / 'all_predictions.json')
    assert aggregate['rows'] == output == lines(run / 'all_predictions.jsonl') and aggregate['issue_records'] == issues
    assert not validator.validate({'rows': source}, aggregate)
    assert [r['id'] for r in output] == [r['id'] for r in source] and len(output) == 75
    assert summary['actual_attempt_count'] == len(attempts_audit) <= 9
    assert summary['accepted_batch_count'] == 3 and summary['source_unchanged_during_run']
    assert summary['output_sha256'] == sha(run / 'all_predictions.jsonl') and summary['plan_sha256'] == sha(run / 'run_plan.json')
    (run / 'row_provenance.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in provenance))
    qa = {'status': 'PASS', 'condition': item['condition'], 'n': 75, 'batches': 3, 'actual_attempts': len(attempts_audit), 'failed_attempts_preserved': sum(not a['valid'] for a in attempts_audit), 'first_valid_actual_attempt_selected': True, 'source': bind(run / 'frozen_input.jsonl'), 'prompt': bind(run / 'frozen_prompt.txt'), 'output': bind(run / 'all_predictions.jsonl'), 'row_provenance': bind(run / 'row_provenance.jsonl'), 'execution_summary': bind(run / 'execution_summary.json'), 'attempt_audits': attempts_audit}
    dump(run / 'execution_binding_QA.json', qa)
    return output, qa

def pair_metrics(left, right, ids, dims):
    cells = collections.Counter((left[i]['labels'][d], right[i]['labels'][d]) for i in ids for d in dims)
    n = len(ids) * len(dims); n00, n01, n10, n11 = (cells[(0, 0)], cells[(0, 1)], cells[(1, 0)], cells[(1, 1)])
    po = (n00 + n11) / n
    pe_num = (n00 + n01) * (n00 + n10) + (n10 + n11) * (n01 + n11)
    den = n * n - pe_num
    kappa = ((n00 + n11) * n - pe_num) / den if den else None
    return {'n': n, 'raw_cells': {'00': n00, '01': n01, '10': n10, '11': n11}, 'percent_agreement': po * 100, 'kappa': kappa, 'kappa_undefined_reason': 'zero_expected_disagreement' if not den else None, '0_to_1': n01, '1_to_0': n10}

def main():
    assert sha(P / 'candidate03_stability_preanalysis_freeze.json') == PLAN_SHA
    plan = read(P / 'candidate03_stability_preanalysis_freeze.json')
    authorization = read(P / 'root_plan_review_and_execution_authorization.json')
    assert authorization['status'] == 'passed_root_independent_plan_review' and authorization['plan_sha256'] == PLAN_SHA
    assert authorization['new_calls_authorized'] == 9 and authorization['technical_max_attempts'] == 27
    full_binding = read(FULL / 'full_development_binding.json')
    assert full_binding['status'] == 'complete_actual_full_corpus_development_comparison_QA_PASS'
    for k in ['output', 'execution_summary', 'run_plan', 'row_provenance', 'technical_QA']: check_binding(full_binding[k])
    assert read(pathlib.Path(full_binding['technical_QA']['path']))['status'] == 'PASS'
    for b in [plan['source'], plan['base_prompt'], plan['order_prompt'], plan['sample'], *plan['frozen_components'].values()]: check_binding(b)
    if '--audit-only' in sys.argv:
        state = read(P / 'execution_state.json')
        assert len(state['conditions']) == 3 and all('exit_code' in c for c in state['conditions'])
        assert [c['command'] for c in state['conditions']] == [c['command'] for c in plan['planned_runs']]
        check_binding(state['full_binding'])
    else:
        assert len(sys.argv) == 1
        for item in plan['planned_runs']: assert not pathlib.Path(item['run_directory']).exists(), 'No rerun or overwrite is allowed.'
        state = {'started_at': now(), 'execution_driver': bind(pathlib.Path(__file__).resolve()), 'plan': bind(P / 'candidate03_stability_preanalysis_freeze.json'), 'root_authorization': bind(P / 'root_plan_review_and_execution_authorization.json'), 'full_binding': bind(FULL / 'full_development_binding.json'), 'status': 'running_sequential_conditions_max3_concurrent', 'conditions': []}
        dump(P / 'execution_state.json', state)
        for item in plan['planned_runs']:
            record = {'condition': item['condition'], 'started_at': now(), 'command': item['command']}
            state['conditions'].append(record); dump(P / 'execution_state.json', state)
            logfile = P / (item['condition'] + '.stdout.log')
            print(json.dumps({'starting_condition': item['condition'], 'time': now()}, ensure_ascii=False), flush=True)
            with logfile.open('w') as log:
                proc = subprocess.Popen(item['command'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                record['runner_pid'] = proc.pid; dump(P / 'execution_state.json', state)
                for line in proc.stdout:
                    log.write(line); log.flush(); print(line, end='', flush=True)
                record['exit_code'] = proc.wait()
            record['ended_at'] = now(); record['stdout'] = bind(logfile); dump(P / 'execution_state.json', state)
        state['ended_at'] = now()
    if any(c['exit_code'] != 0 for c in state['conditions']):
        state['status'] = 'technical_incomplete_all_original_attempts_preserved'; dump(P / 'execution_state.json', state)
        raise RuntimeError('A stability condition was technically incomplete; no substitute, aggregate, or extra calls created.')
    by_condition = {}; qas = []
    for item in plan['planned_runs']:
        rows, qa = audit_run(item, plan); qas.append(qa)
        by_condition[item['condition']] = {r['id']: r for r in rows}
    sample = lines(pathlib.Path(plan['sample']['path'])); ids = [r['id'] for r in sample]
    full_rows = {r['id']: r for r in lines(pathlib.Path(full_binding['output']['path']))}
    by_condition['base1-full-run'] = {i: full_rows[i] for i in ids}
    # Request equality makes the full run the genuine first repeat for these batches.
    for b in plan['batches']:
        req = FULL / 'batches' / f"batch-{b['production_batch']:04d}" / 'request.txt'
        assert sha(req) == b['base_request_sha256']
    identical = ['base1-full-run', 'base-repeat-2', 'base-repeat-3']
    pairs = [(a, b, 'identical_prompt') for a, b in itertools.combinations(identical, 2)] + [('order-perturbation', b, 'order_sensitivity') for b in identical]
    groups = [('overall75', ids)] + [(f"intact_batch_{b['production_batch']}_mixed_department", b['all_ids']) for b in plan['batches']]
    metrics = []; disagreements = []
    for left, right, kind in pairs:
        for group, gids in groups:
            for d in DIMS + ['pooled_5_labels']:
                metrics.append({'comparison_type': kind, 'left': left, 'right': right, 'group': group, 'dimension': d, **pair_metrics(by_condition[left], by_condition[right], gids, DIMS if d == 'pooled_5_labels' else [d])})
        for i in ids:
            diff = [d for d in DIMS if by_condition[left][i]['labels'][d] != by_condition[right][i]['labels'][d]]
            if diff: disagreements.append({'comparison_type': kind, 'left_condition': left, 'right_condition': right, 'id': i, 'dimensions': diff, 'frozen_input': next(r for r in sample if r['id'] == i), 'left_original_row': by_condition[left][i], 'right_original_row': by_condition[right][i]})
    all_three = {'n': 75, 'exact_five_dimension_rows': sum(all(by_condition[c][i]['labels'] == by_condition[identical[0]][i]['labels'] for c in identical[1:]) for i in ids), 'dimension_agreement_counts': {d: sum(len({by_condition[c][i]['labels'][d] for c in identical}) == 1 for i in ids) for d in DIMS}}
    result = {'status': 'complete_actual_candidate03_development_stability', 'created_at': now(), 'plan': bind(P / 'candidate03_stability_preanalysis_freeze.json'), 'n': 75, 'new_logical_calls': 9, 'actual_new_attempts': sum(q['actual_attempts'] for q in qas), 'failed_attempts_preserved': sum(q['failed_attempts_preserved'] for q in qas), 'all_three_identical_prompt': all_three, 'pairwise_metrics': metrics, 'interpretation': 'Reproducibility on preselected mixed batches; no accuracy, independent validation, or adoption claim. All repeats retained; full-run output unchanged.', 'department_note': plan['sample_scope_caution']}
    assert result['actual_new_attempts'] <= 27
    dump(P / 'all_original_disagreements.json', {'all_disagreements_retained': True, 'disagreements': disagreements})
    dump(P / 'stability_metrics.json', result)
    check_binding(full_binding['output'])
    state['status'] = 'complete_all9_calls_and_execution_QA_PASS'; dump(P / 'execution_state.json', state)
    binding = {'status': state['status'], 'scope': plan['scope'], 'plan': state['plan'], 'root_authorization': state['root_authorization'], 'full_binding': state['full_binding'], 'metrics': bind(P / 'stability_metrics.json'), 'disagreements': bind(P / 'all_original_disagreements.json'), 'execution_state': bind(P / 'execution_state.json'), 'run_QAs': [bind(pathlib.Path(i['run_directory']) / 'execution_binding_QA.json') for i in plan['planned_runs']], 'new_logical_calls': 9, 'actual_new_attempts': result['actual_new_attempts'], 'failed_attempts_preserved': result['failed_attempts_preserved'], 'full_run_rows_replaced': False, 'independent_validation': False, 'formal_adoption': False}
    dump(P / 'stability_final_binding.json', binding)
    print(json.dumps({'status': binding['status'], 'binding': bind(P / 'stability_final_binding.json'), 'all_three': all_three, 'actual_new_attempts': result['actual_new_attempts']}, ensure_ascii=False), flush=True)

if __name__ == '__main__': main()

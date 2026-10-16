"""Finite, non-executing checks of a dependency-queue rebinding candidate."""
from pathlib import Path
import ast
import copy
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def tree_functions(path):
    return {n.name: n for n in ast.parse(path.read_text()).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def normalized(node):
    node = copy.deepcopy(node)
    if node.name == 'context':
        node.body = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)
                     and isinstance(s.value.func, ast.Name) and s.value.func.id in
                     ('validate_rebinding_configuration', 'validate_rebinding_chain'))]
    if node.name == 'watch':
        for item in ast.walk(node):
            if isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == 'lock':
                if isinstance(item.args[0], ast.Name) and item.args[0].id == 'SHARED_QUEUE_LOCK':
                    item.args[0] = ast.parse("HERE / 'queue.lock'", mode='eval').body
    if node.name == 'process_observation':
        for item in ast.walk(node):
            if isinstance(item, ast.For):
                item.body = [s for s in item.body if not (
                    isinstance(s, ast.If) and isinstance(s.test, ast.Call) and isinstance(s.test.func, ast.Name)
                    and s.test.func.id == 'own_queue_watcher') and not (
                    isinstance(s, ast.Assign) and isinstance(s.value, ast.BoolOp)
                    and any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                            and x.func.id == 'rebound_process_match' for x in s.value.values))]
    return ast.dump(node, include_attributes=False)


def verify():
    spec = importlib.util.spec_from_file_location('candidate_queue_no_main', HERE / 'supervisor.py')
    q = importlib.util.module_from_spec(spec); spec.loader.exec_module(q)
    cfg = q.load(HERE / 'config.json'); b = cfg['bindings']
    for item in b.values(): q.exact(item)
    original_path = Path(b['original_queue_supervisor']['path'])
    original = tree_functions(original_path); candidate = tree_functions(HERE / 'supervisor.py')
    changed = [name for name in original if ast.dump(original[name], include_attributes=False) != ast.dump(candidate[name], include_attributes=False)]
    assert set(changed) == {'context', 'process_observation', 'watch'}
    assert all(normalized(original[name]) == normalized(candidate[name]) for name in original)
    assert cfg['shared_queue_lock'] == str(q.SHARED_QUEUE_LOCK) == str(original_path.parent / 'queue.lock')
    cases = [{'case': 'all_original_functions_AST_unchanged_except_three_explicit_splices', 'passed': True},
             {'case': 'shared_original_queue_lock_fixed_not_new_directory_lock', 'passed': True}]
    # No live context, process observation, lock, wait, native freshness probe,
    # projection or original first-file read is called by these synthetic rows.
    argv = [cfg['python'], '-B', b['terminal_recovery_entry']['path'], '--mode', 'run', '--adoption', 'NONEXECUTING-TOY-adoption']
    start = {'argv': argv}; old = q.load(b['original_dependency_authorization']['path'])
    for command in q.launch_commands(argv, b):
        assert q.rebound_process_match(cfg, b, old, start, {'command': command})
    assert q.rebound_process_match(cfg, b, old, start, {'command': ' '.join(argv[:-1] + ['unexpected-adoption'])})
    assert q.rebound_process_match(cfg, b, old, start, {'command': ' '.join(old['actual_controller_argv'])})
    cases.append({'case': 'new_full_argv_all_bound_Python_spellings_and_legacy_wrapper_blocked', 'passed': True})
    own = [cfg['python'], '-B', str(HERE / 'supervisor.py'), '--mode', 'watch', '--authorization', cfg['conditional_authorization']]
    row = {'pid': 7001, 'pgid': 7001, 'command': ' '.join(own)}
    assert q.own_queue_watcher(cfg, b, row, 7001, 7001)
    for altered in [dict(row, pid=7002), dict(row, pgid=7002), dict(row, command=row['command'] + ' extra')]:
        assert not q.own_queue_watcher(cfg, b, altered, 7001, 7001)
    assert q.rebound_process_match(cfg, b, old, start, dict(row, pid=7002))
    cases.append({'case': 'self_exclusion_requires_exact_own_PID_PGID_full_argv_other_watcher_stays_blocking', 'passed': True})
    try: q.context()
    except ValueError as error:
        assert 'Candidate configuration' in str(error)
    else: raise AssertionError('Candidate must not open dependency context')
    cases.append({'case': 'candidate_observe_watch_context_fails_before_runtime_dependency_read', 'passed': True})
    baseline = q.load(b['original_queue_configuration']['path'])
    assert cfg['actual_GO'] == baseline['actual_GO'] and cfg['merged_output'] == baseline['merged_output']
    assert cfg['runtime_output'] != baseline['runtime_output'] and cfg['conditional_authorization'] != baseline['conditional_authorization']
    assert not Path(cfg['conditional_authorization']).exists()
    for item in b.values(): q.exact(item)
    cases.append({'case': 'single_native_GO_merge_targets_original_dependencies_unchanged_no_new_authority', 'passed': True})
    return {'candidate_only': True, 'case_N': len(cases), 'all_passed': True, 'cases': cases,
            'original_function_N': len(original), 'original_functions_changed_only_by_explicit_splices': changed,
            'full_terminal_gate_original_attempt_successful_wait_dependency_and_strict_merge_body_preserved': True,
            'new_functions': sorted(set(candidate) - set(original)), 'original_source_binding': q.binding(original_path),
            'candidate_source_binding': q.binding(HERE / 'supervisor.py'), 'candidate_configuration_binding': q.binding(HERE / 'config.json'),
            'fixed_input_binding_N': len(b), 'candidate_context_guard_called_and_rejected': True,
            'actual_dependency_context_admitted': False, 'live_process_observation_executed': False,
            'locks_opened': False, 'GO_or_authorization_written': False, 'projection_or_model_calls': 0,
            'actual_controller_start_terminal_or_stopped_generated': False}


if __name__ == '__main__':
    result = verify()
    with (HERE / 'verification.json').open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    print(json.dumps({'case_N': result['case_N'], 'all_passed': result['all_passed']}))

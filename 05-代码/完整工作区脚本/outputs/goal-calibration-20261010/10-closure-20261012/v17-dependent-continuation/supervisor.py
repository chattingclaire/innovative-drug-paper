"""Fixed dependency queue; observe is read-only, watch needs separate ROOT authority.

One fresh watcher only. No resume, new allowance, classifier, statistics, or old
controller restart. The frozen runner owns execution.lock while its child runs;
this queue holds queue.lock throughout and probes that same runner lock between
steps. It never holds the runner lock across Popen (which would block its owner).
"""
import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CONFIG = HERE / 'config.json'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate metadata key')
            result[key] = value
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique)


def binding(path):
    p = Path(path).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def exact(b):
    require(binding(b['path']) == b, 'Changed binding: ' + b['path'])


def module(b, name):
    exact(b)
    spec = importlib.util.spec_from_file_location(name, b['path'])
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


@contextlib.contextmanager
def lock(path):
    with Path(path).open('a+b') as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def context():
    require(__debug__, 'Frozen assertions must remain enabled')
    cfg = load(CONFIG)
    b = cfg['bindings']
    for item in b.values():
        exact(item)
    require(Path(sys.executable).resolve() == Path(cfg['python']).resolve(), 'Use frozen Python')
    require(cfg['batch_ids'] == ['batch-0325', 'batch-0485']
            and cfg['conditions'] == ['R1', 'R2', 'R3', 'W', 'H']
            and 5 <= cfg['quiet_seconds'] <= 60 and 5 <= cfg['poll_seconds'] <= 60, 'Changed fixed scope')
    old = load(b['dependency_authorization']['path'])
    start = load(b['controller_start']['path'])
    identity = load(b['controller_identity']['path'])
    sup = load(b['supervisor_start']['path'])
    require(old['issuer'] == 'ROOT' and old['template_only'] is False
            and old['same_campaign_continuation'] is True, 'Wrong original continuation')
    require(start['actual_Popen_started'] is True and identity['birth_observation_status'] == 'observed'
            and start['controller_pid'] == identity['pid'] == start['process_group_id']
            and start['argv'] == sup['argv'] == old['actual_controller_argv'], 'Original identity mismatch')
    require(sup['provenance']['ROOT_authorization'] == b['dependency_authorization']
            and old['campaign_manifest'] == b['campaign_manifest']
            and sup['provenance']['reused_wait_implementation'] == b['wait_helper']
            and sup['provenance']['self_runtime_executable_binding'] == b['python_process_image'], 'Original chain mismatch')
    wait = module(b['wait_helper'], 'bound_original_wait')
    ps = module(b['process_helper'], 'bound_original_ps')
    return cfg, b, old, start, identity, sup, wait, ps


def successful_wait(terminal, pid=None):
    require(terminal.get('provenance') == 'durable_supervisor_actual_Popen_wait'
            and terminal.get('actual_Popen_started') is True
            and terminal.get('actual_wait_returned') is True
            and terminal.get('actual_controller_terminal') is True
            and type(terminal.get('returncode')) is int and terminal['returncode'] == 0
            and terminal.get('returncode_status') == 'observed_by_parent_wait'
            and terminal.get('launch_or_supervision_error') is None, 'Actual successful parent wait absent')
    if pid is not None:
        require(terminal['controller_pid'] == pid, 'Parent wait PID differs')
    for name in ('stdout', 'stderr'):
        exact(terminal[name])


def dependency(ctx):
    """Cheap polling: no routes, original first files, projection, or writes."""
    cfg, b, old, start, identity, sup, wait, ps = ctx
    rows = ps.ps_rows()
    row = next((r for r in rows if r['pid'] == identity['pid']), None)
    if row is not None and row['lstart'] == identity['lstart']:
        commands = [exe + ' ' + ' '.join(start['argv'][1:]) for exe in
                    (start['argv'][0], b['python_launcher']['path'], b['python_process_image']['path'])]
        require(row['command'] in commands and row['pgid'] == start['process_group_id'],
                'Original controller birth exists but command/group differs')
        return {'state': 'waiting', 'at_utc': now(), 'reason': 'fixed_original_controller_live',
                'controller': row, 'GO_created': False, 'dispatch_started': False}
    terminal_path = Path(cfg['controller_terminal'])
    if not terminal_path.exists():
        return {'state': 'waiting_for_parent_receipt', 'at_utc': now(),
                'reason': 'No actual parent wait receipt; PID absence/reuse does not prove terminal',
                'GO_created': False, 'dispatch_started': False}
    terminal = load(terminal_path)
    successful_wait(terminal, start['controller_pid'])
    require(Path(terminal['stdout']['path']) == terminal_path.parent / 'controller-stdout.txt'
            and Path(terminal['stderr']['path']) == terminal_path.parent / 'controller-stderr.txt', 'Wrong parent output')
    require(ps.utc(terminal['at_utc']) >= ps.utc(start['at_utc']), 'Parent wait precedes start')
    return {'state': 'parent_terminal_requires_full_gate', 'at_utc': now(),
            'terminal': binding(terminal_path), 'GO_created': False, 'dispatch_started': False}


def original_attempt(ctx, manifest, route, receipt, orphan):
    """Check actual completion metadata; unknown orphan returncodes stay failures."""
    cfg, b, old, start, identity, sup, wait, ps = ctx
    key = tuple(route[k] for k in ('condition', 'batch_number', 'attempt_number'))
    slot = Path(route['output_directory'])
    dispatch_binding = binding(slot / 'ROOT-dispatch-start.json')
    dispatch = load(dispatch_binding['path'])
    require(tuple(dispatch.get(k) for k in ('condition', 'batch_number', 'attempt_number')) == key
            and dispatch['GO'] == old['unchanged_GO'] and dispatch['assignment'] == route['assignment']
            and dispatch['stdin'] == route['fixed_request']
            and dispatch['working_directory'] == route['working_directory'], 'Dispatch route differs')
    # Pure argv construction from the original bound implementation, not run_attempt.
    require(dispatch['argv'] == sys.modules['bound_original_runner'].command(manifest, route), 'Original argv differs')
    require(receipt['run_id'] == manifest['run_id'] and receipt['assignment'] == route['assignment']
            and tuple(receipt.get(k) for k in ('condition', 'batch_number', 'attempt_number')) == key,
            'Receipt route differs')
    exact(receipt['completion'])
    completion = load(receipt['completion']['path'])
    process_path = slot / 'ROOT-actual-process-start.json'
    actual = load(process_path) if process_path.exists() else None
    if orphan is not None:
        exact(orphan['technical_reception']); exact(orphan['terminal_certificate'])
        require(receipt['completion'] == orphan['terminal_certificate']
                and receipt['state'] == 'technical_invalid_whole_batch'
                and receipt.get('error', {}).get('type') == 'OrphanedControllerWaitReceiptUnavailable'
                and not any(k in receipt for k in ('first', 'validation', 'transport_seal', 'technical_proof'))
                and not (slot / 'ROOT-process-completion.json').exists(), 'Orphan failure history changed')
        require(completion.get('artifact_type') == 'ROOT_external_orphan_process_terminal_certificate'
                and completion.get('actual_process_terminal') is True and completion.get('failure_only') is True
                and completion.get('fixture_only') is False and completion.get('returncode') is None
                and completion.get('returncode_status') == 'unknown_parent_wait_unavailable'
                and completion.get('original_GO') == old['unchanged_GO']
                and tuple(completion.get(k) for k in ('condition', 'batch_number', 'attempt_number')) == key
                and completion.get('original_dispatch_start') == dispatch_binding
                and actual is not None and completion.get('original_actual_process_start') == binding(process_path),
                'Wrong external unknown-returncode certificate')
        require(completion['process_group_id'] == actual['process_group_id'], 'Orphan group differs')
        require(len(completion['observations']) == 2, 'Original two observations absent')
        observed = []
        for item in completion['observations']:
            exact(item)
            observation = load(item['path'])
            require(observation['fixture_only'] is False and not observation['blockers'], 'Original orphan observation blocked')
            observed.append(observation['finished_at'])
        require(ps.utc(observed[1]) > ps.utc(observed[0]), 'Original observation order differs')
        terminal_at = observed[1]  # Certificate has no at_utc and no recovered wait.
    else:
        require(receipt['completion'] == binding(slot / 'ROOT-process-completion.json')
                and completion.get('provenance') == 'ROOT_subprocess_Popen_wait_real_events_capture'
                and completion.get('fixture_only') is False and completion.get('actual_process_terminal') is True
                and completion.get('start') == dispatch_binding
                and tuple(completion.get(k) for k in ('condition', 'batch_number', 'attempt_number')) == key,
                'Original actual terminal missing')
        if completion.get('actual_CLI_process_started') is True:
            require(actual is not None and type(completion.get('returncode')) is int, 'Started CLI has unknown wait')
        else:
            require(completion.get('actual_CLI_process_started') is False and actual is None
                    and completion.get('pid') is None and completion.get('returncode') is None
                    and bool(completion.get('launch_or_transport_error'))
                    and receipt['state'] == 'technical_invalid_whole_batch', 'Unproven no-launch failure')
        terminal_at = completion['at_utc']
    require(ps.utc(terminal_at) >= ps.utc(dispatch['at_utc']), 'Completion precedes dispatch')
    if receipt['state'] == 'technical_valid_whole_batch':
        require(completion.get('returncode') == 0 and type(completion.get('returncode')) is int
                and completion.get('timed_out') is False and completion.get('launch_or_transport_error') is None,
                'Selected attempt lacks clean real completion')
    worker = None
    if actual is not None:
        require(actual['actual_CLI_process_started'] is True and actual['start'] == dispatch_binding
                and type(actual['pid']) is int and actual['pid'] > 0
                and actual['pid'] == actual['process_group_id'] == completion['pid']
                and ps.utc(dispatch['at_utc']) <= ps.utc(actual['at_utc']) <= ps.utc(terminal_at),
                'Actual worker identity differs')
        worker = {'pid': actual['pid'], 'pgid': actual['process_group_id'],
                  'started_at_utc': actual['at_utc'], 'terminal_at_utc': terminal_at,
                  'start': binding(process_path), 'dispatch': dispatch_binding, 'completion': receipt['completion']}
    return worker, terminal_at


def full_terminal_gate(ctx, terminal_binding, out):
    """Only called once, after actual parent wait; no production writes/statistics."""
    cfg, b, old, start, identity, sup, wait, ps = ctx
    exact(terminal_binding)
    terminal = load(terminal_binding['path'])
    returned = load(terminal['stdout']['path'])
    require(returned.get('all_terminal') is True, 'Controller did not report all terminal')
    exact(returned['result'])
    result = load(returned['result']['path'])
    campaign_dir = Path(b['campaign_manifest']['path']).parent
    require(Path(returned['result']['path']).parent.parent == campaign_dir / 'ROOT-controller-runs'
            and result.get('all_terminal') is True and result.get('all_five_conditions_terminal') is True
            and set(result['results']) == set(cfg['conditions']), 'Wrong controller epoch result')
    epoch_start = load(Path(returned['result']['path']).parent / 'start.json')
    require(epoch_start['GO'] == old['unchanged_GO'] and epoch_start['campaign_manifest'] == b['campaign_manifest']
            and ps.utc(start['at_utc']) <= ps.utc(epoch_start['at_utc']) <= ps.utc(result['at_utc'])
            <= ps.utc(terminal['at_utc']), 'Epoch does not belong to fixed controller')
    manifest = load(b['campaign_manifest']['path'])
    require(manifest['conditions'] == cfg['conditions'] and manifest['batch_N'] == 87 and manifest['record_N'] == 800,
            'Wrong original campaign scope')
    for item in manifest['implementation_bindings']:
        exact(item)
    sys.path.insert(0, str(Path(b['projection']['path']).parent))
    runner_binding = next(x for x in manifest['implementation_bindings'] if Path(x['path']).name == 'runner.py')
    sys.modules['bound_original_runner'] = module(runner_binding, 'bound_original_runner')
    routes = {(r['condition'], r['batch_number'], r['attempt_number']): r for r in manifest['routes']}
    expected = {(c, n, a) for c in cfg['conditions'] for n in range(1, 88) for a in (1, 2, 3)}
    require(len(routes) == len(manifest['routes']) == 1305 and set(routes) == expected, 'Original route grid differs')
    orphans = {(x['condition'], x['batch_number'], x['attempt_number']): x for x in old['closed_attempts']}
    require(len(orphans) == len(old['closed_attempts']) == 13, 'Wrong fixed orphan set')
    states, workers = [], []
    for condition in cfg['conditions']:
        epoch_rows = result['results'][condition]
        require(len(epoch_rows) == 87 and {x['batch_number'] for x in epoch_rows} == set(range(1, 88))
                and all(x['state'] in ('selected', 'already_selected', 'technical_exhausted') for x in epoch_rows),
                '435 actual terminal batches required; zero-call/unknown is not admitted')
        for n in range(1, 88):
            directory = Path(routes[condition, n, 1]['selection_directory'])
            selected = directory / 'root-selection.json'
            require(not (directory / 'root-zero-call-block.json').exists(), 'Zero-call batch is not actual terminal')
            selection = load(selected) if selected.exists() else None
            limit = selection['selected_attempt_number'] if selection else 3
            require(type(limit) is int and 1 <= limit <= 3, 'Invalid selected attempt')
            receipts = []
            for attempt in (1, 2, 3):
                route = routes[condition, n, attempt]
                slot = Path(route['output_directory'])
                receipt_path = directory / f'root-attempt-reception-{attempt:04d}.json'
                if attempt > limit:
                    require(not receipt_path.exists() and (not slot.exists() or not any(slot.iterdir())),
                            'Unexpected later slot after selected attempt')
                    continue
                receipt_binding = binding(receipt_path)
                receipt = load(receipt_path)
                expected_state = 'technical_valid_whole_batch' if selection and attempt == limit else 'technical_invalid_whole_batch'
                require(receipt['state'] == expected_state, 'Missing actual selected/exhausted route')
                orphan = orphans.get((condition, n, attempt))
                if orphan:
                    require(receipt_binding == orphan['technical_reception'], 'Original orphan reception changed')
                worker, terminal_at = original_attempt(ctx, manifest, route, receipt, orphan)
                require(ps.utc(terminal_at) <= ps.utc(terminal['at_utc']),
                        'Attempt terminal after parent terminal')
                if worker:
                    workers.append(worker)
                receipts.append(receipt_binding)
            states.append({'condition': condition, 'batch_number': n,
                           'state': 'selected' if selection else 'technical_fail', 'receipts': receipts,
                           'selection': binding(selected) if selection else None})
    projection = module(b['projection'], 'bound_original_projection').build_projection(campaign_dir)
    expected_ids = [sid for batch in manifest['batches'] for sid in batch['members']]
    require(len(expected_ids) == len(set(expected_ids)) == 800
            and projection['all_five_conditions_all_batches_terminal'] is True
            and set(projection['conditions']) == set(cfg['conditions']), 'Projection scope differs')
    for condition, rows in projection['conditions'].items():
        require([x['source_id'] for x in rows] == expected_ids
                and all(x['status'] in ('valid', 'technical_fail') for x in rows)
                and all(x['labels'] is None for x in rows if x['status'] == 'technical_fail'), 'Projection coverage differs')
    # Preserve only gate evidence here. No duplicate original labels/statistics file.
    gate = wait.save(out / 'dependency-terminal-gate.json', {
        'at_utc': now(), 'parent_terminal': terminal_binding, 'controller_result': returned['result'],
        'campaign_manifest': b['campaign_manifest'], 'actual_terminal_batch_N': len(states),
        'projection_called_once': True, 'projection_record_N_each': 800, 'statistics_computed': False,
        'unknown_orphan_returncodes_preserved_as_failures': True, 'states': states, 'workers': workers})
    return gate, workers, terminal


def process_observation(ctx, workers, terminal):
    cfg, b, old, start, identity, sup, wait, ps = ctx
    rows = ps.ps_rows()
    indexed = {r['pid']: r for r in rows}
    identities = workers + [
        {'pid': start['controller_pid'], 'pgid': start['process_group_id'],
         'terminal_at_utc': terminal['at_utc']},
        {'pid': sup['supervisor_pid'], 'pgid': sup['supervisor_sid'],
         'terminal_at_utc': terminal['at_utc']}]
    blockers, excluded_reuses = {}, []
    for row in rows:
        command = row['command']
        scoped = ((cfg['isolated_cli_directory'] in command
                   and (' exec ' in command or 'codex-code-mode-host' in command))
                  or (str(Path(b['campaign_manifest']['path']).parent) in command
                      and (' exec ' in command or 'controller.py' in command))
                  or (old['execution_wrapper']['path'] in command and '--original-entry' in command)
                  or (old['actual_supervisor_entrypoint']['path'] in command
                      and b['dependency_authorization']['path'] in command))
        if scoped:
            blockers[row['pid']] = row
        for historical in identities:
            cutoff = ps.utc(historical['terminal_at_utc'])
            same_pid = row['pid'] == historical['pid']
            same_group = row['pgid'] == historical['pgid']
            if not same_pid and not same_group:
                continue
            # A new group requires its new leader as evidence. A later-born child
            # in an old, leaderless group is NOT assumed to be numeric reuse.
            leader = indexed.get(row['pgid'])
            pid_reused = not same_pid or ps.birth(row) > cutoff
            group_reused = not same_group or (leader is not None and leader['pgid'] == leader['pid']
                                               and ps.birth(leader) > cutoff)
            if pid_reused and group_reused and not scoped:
                excluded_reuses.append({'current_pid': row['pid'], 'historical_pid': historical['pid'],
                                        'current_birth': row['lstart'], 'historical_terminal': historical['terminal_at_utc']})
            else:
                blockers[row['pid']] = row
    while True:
        additions = [r for r in rows if r['ppid'] in blockers and r['pid'] not in blockers]
        if not additions:
            break
        blockers.update({r['pid']: r for r in additions})
    return {'at_utc': now(), 'monotonic': time.monotonic(), 'method': 'bound ps_rows; scoped commands, PID/group birth, descendants',
            'blockers': list(blockers.values()), 'excluded_proven_numeric_reuses': excluded_reuses,
            'unrelated_generic_hosts_not_claimed': True, 'observed_process_N': len(rows)}


def authorization(cfg, b, path):
    require(Path(path).resolve() == Path(cfg['conditional_authorization']), 'Wrong conditional authority path')
    auth = load(path)
    for key, expected in cfg['authorization_required'].items():
        require(auth.get(key) == expected, 'ROOT conditional authorization required: ' + key)
    for key in cfg['authorization_exact_bindings']:
        expected = binding(__file__) if key == 'supervisor' else binding(CONFIG) if key == 'configuration' else b[key]
        require(auth.get(key) == expected, 'ROOT authorization binding differs: ' + key)
    for key in cfg['authorization_exact_paths']:
        require(auth.get(key) == cfg[key], 'ROOT authorized path differs: ' + key)
    require(auth.get('batch_ids') == cfg['batch_ids'], 'ROOT authorized batch scope differs')
    return binding(path)


def fresh_native(cfg, b):
    require(not Path(cfg['actual_GO']).exists() and not Path(cfg['merged_output']).exists(), 'Existing GO/output; no automatic recovery')
    manifest = load(b['native_manifest']['path'])
    for batch in manifest['batches']:
        fresh_batch(b, batch['batch_id'])


def fresh_batch(b, batch_id):
    directory = Path(b['runner']['path']).parent / batch_id
    require(not (directory / 'root-selection.json').exists() and not (directory / 'exhausted.json').exists(),
            'Native selection/exhaustion already exists; stop')
    batch = next(x for x in load(b['native_manifest']['path'])['batches'] if x['batch_id'] == batch_id)
    assignment = load(batch['assignment']['path'])
    for route in load(assignment['attempt_output_routing']['path'])['routes']:
        slot = Path(route['output_directory'])
        require(not slot.exists() or not any(slot.iterdir()), 'Existing native attempt/partial output; stop')


def watch(ctx, auth_path):
    cfg, b, old, start, identity, sup, wait, ps = ctx
    auth_binding = authorization(cfg, b, auth_path)
    require(os.getsid(0) == os.getpid(), 'Watcher must be detached with start_new_session=True')
    stdin = os.fstat(0)
    require(stat.S_ISCHR(stdin.st_mode) and stdin.st_rdev == os.stat('/dev/null').st_rdev, 'Watcher stdin must be DEVNULL')
    out = Path(cfg['runtime_output'])
    with lock(HERE / 'queue.lock'):
        fresh_native(cfg, b)
        out.mkdir(exist_ok=False)
        provenance = {'ROOT_conditional_authorization': auth_binding, 'supervisor': binding(__file__), 'configuration': binding(CONFIG)}
        wait.save(out / 'watcher-start.json', dict(at_utc=now(), pid=os.getpid(), sid=os.getsid(0), **provenance))
        try:
            absent_since = None
            while True:
                observed = dependency(ctx)
                if observed['state'] == 'parent_terminal_requires_full_gate':
                    break
                if observed['state'] == 'waiting_for_parent_receipt':
                    absent_since = absent_since or time.monotonic()
                    require(time.monotonic() - absent_since < 60, 'Controller absent but no real parent wait; ROOT attention required')
                else:
                    absent_since = None
                time.sleep(cfg['poll_seconds'])
            gate, workers, terminal = full_terminal_gate(ctx, observed['terminal'], out)
            first = process_observation(ctx, workers, terminal)
            # A live/ambiguous worker after parent termination is not auto-cleared.
            require(not first['blockers'], 'Original worker/group/host remains live or ambiguous')
            time.sleep(cfg['quiet_seconds'])
            second = process_observation(ctx, workers, terminal)
            require(not second['blockers'] and second['monotonic'] - first['monotonic'] >= 5, 'Capacity not twice empty')
            capacity = wait.save(out / 'capacity-evidence.json', {'at_utc': now(), 'dependency_gate': gate,
                'observations': [first, second], 'reserved_additional_cli_slots': 1,
                'original_all_435_batches_terminal': True, 'original_controller_workers_groups_scoped_hosts_absent': True,
                'ROOT_conditional_authorization': auth_binding, 'scope': cfg['scope']})
            for item in b.values():
                exact(item)
            exact(auth_binding); exact(provenance['supervisor']); exact(provenance['configuration'])
            fresh_native(cfg, b)
            native = Path(b['runner']['path']).parent
            # Original runner owns this same lock during each actual execution.
            with lock(native / 'execution.lock'):
                go = load(b['GO_template']['path'])
                go.update(template_only=False, execution_authorized=True, at_utc=now(),
                          preparation_seal=b['native_seal'], single_transport_owner=True,
                          note='Actual conditional ROOT authority, admitted by bound dependent supervisor.',
                          dependent_supervisor=provenance, dependency_terminal_gate=gate)
                go['capacity_reservation'].update(confirmed_by_ROOT=True, stability_capacity_can_accommodate=True,
                    observed_at_utc=second['at_utc'], observed_capacity_evidence=capacity)
                go_binding = wait.save(cfg['actual_GO'], go)
            merger = module(b['merger'], 'bound_original_merger')
            doc, collector = merger.profile()
            selections = []
            for batch_id in cfg['batch_ids']:
                exact(go_binding); exact(auth_binding)
                exact(provenance['supervisor']); exact(provenance['configuration'])
                with lock(native / 'execution.lock'):
                    fresh_batch(b, batch_id)
                    require(not process_observation(ctx, workers, terminal)['blockers'], 'Capacity changed before native dispatch')
                argv = [cfg['python'], '-B', b['runner']['path'], '--mode', 'run', '--batch-id', batch_id, '--go', cfg['actual_GO']]
                completed = wait.wait_and_seal(argv, out / batch_id, dict(provenance, actual_GO=go_binding))
                successful_wait(completed)
                with lock(native / 'execution.lock'):
                    selection = native / batch_id / 'root-selection.json'
                    require(selection.exists() and not (native / batch_id / 'exhausted.json').exists(),
                            'No valid selection (including three-attempt exhaustion); no recovery')
                    _, _, _, readback = merger.new_whole(selection, batch_id, collector, doc)
                    selections.append(binding(selection))
                    # Add the new runner's actual child groups before admitting
                    # the next serial batch. Generic hosts elsewhere are ignored.
                    completions = [readback['process_completion']] + [x['process_completion'] for x in readback['earlier_actual_technical_slots']]
                    for item in completions:
                        exact(item)
                        child = load(item['path'])
                        workers.append({'pid': child['pid'], 'pgid': child['pid'], 'terminal_at_utc': child['at_utc']})
                    released = process_observation(ctx, workers, terminal)
                    require(not released['blockers'], 'Native child/group/host capacity not released')
                    wait.save(out / batch_id / 'released-capacity.json', released)
            require(not Path(cfg['merged_output']).exists(), 'Existing or partial merge output; never overwrite')
            for selected in selections:
                exact(selected)
            argv = [cfg['python'], '-B', b['merger']['path'], '--mode', 'merge', '--parent', str(Path(b['parent_seal']['path']).parent)]
            for selected in selections:
                argv.extend(['--selection', selected['path']])
            argv.extend(['--output', cfg['merged_output']])
            completed = wait.wait_and_seal(argv, out / 'strict-merge', provenance)
            successful_wait(completed)
            merged = Path(cfg['merged_output'])
            seal = load(merged / 'seal.json')
            for item in seal['files']:
                exact(item)
            require(binding(merged / 'status.json') in seal['files'], 'Merge status not sealed')
            status = load(merged / 'status.json')
            require(status['actual_merge_performed'] is True and status['single_actual_merge_pass'] is True
                    and status['actual_record_N'] == 4481 and status['actual_new_inference_record_N'] == 24
                    and status['parent_raw_line_preserved_N'] == 4457 and status['new_whole_selections'] == selections,
                    'Strict merge completion differs')
            wait.save(out / 'completed.json', dict(at_utc=now(), actual_GO=go_binding, merged_seal=binding(merged / 'seal.json'),
                      automatic_restart=False, statistics_computed=False, **provenance))
        except BaseException as exc:
            wait.save(out / 'stopped.json', {'at_utc': now(), 'error': {'type': type(exc).__name__, 'message': str(exc)},
                      'partial_outputs_preserved': True, 'automatic_restart': False, 'ROOT_attention_required': True})
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['observe', 'watch'], required=True)
    parser.add_argument('--authorization')
    args = parser.parse_args()
    ctx = context()
    if args.mode == 'observe':
        print(json.dumps(dependency(ctx), ensure_ascii=False, indent=2))
    else:
        require(args.authorization is not None, 'Separate ROOT conditional authorization is required')
        watch(ctx, args.authorization)


if __name__ == '__main__':
    main()

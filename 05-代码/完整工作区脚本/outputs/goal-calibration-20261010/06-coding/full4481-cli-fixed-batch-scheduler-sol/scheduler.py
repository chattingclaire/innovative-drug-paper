#!/usr/bin/env python3
"""ROOT-gated fixed-order CLI scheduling; only frozen whole-batch technical states."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = ROOT / '06-coding/native-full4481-v1-sol'
stop_requested = False


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def exact(item):
    if binding(item['path']) != {k: item[k] for k in ('path', 'bytes', 'sha256')}:
        raise RuntimeError('Frozen binding changed: ' + item['path'])


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def spawn(argv, directory, prefix):
    """No policy/data construction here; caller registers child before receipt I/O."""
    stdout, stderr = directory / (prefix + '-stdout.txt'), directory / (prefix + '-stderr.txt')
    started = now()
    with stdout.open('xb') as out, stderr.open('xb') as err:
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                   cwd=directory, start_new_session=True)
    return {'process': process, 'pid': process.pid, 'argv': argv, 'started_at_utc': started,
            'stdout': stdout, 'stderr': stderr}


def start_receipt(job):
    return {k: job[k] for k in ('pid', 'argv', 'started_at_utc')}


def terminal_receipt(job):
    code = job['process'].poll()  # Actual waitpid observation of our owned child.
    if code is None:
        raise RuntimeError('Child still live; no terminal receipt permitted.')
    return {**start_receipt(job), 'status': 'owned_process_terminal_observed',
            'terminal_observed_at_utc': now(), 'exitcode': code,
            'stdout': binding(job['stdout']), 'stderr': binding(job['stderr'])}


def cli_completion(batch, attempt):
    slot = RUN / f'batch-{batch:04d}' / f'attempt-{attempt:04d}'
    path = slot / 'ROOT-cli-process-completion.json'
    item = load(path)
    if (item.get('status') != 'actual_cli_process_terminal'
            or type(item.get('returncode')) is not int
            or item.get('logical_dispatch_label') != f'native_full4481v1_b{batch:04d}_a{attempt:02d}'):
        raise RuntimeError('Missing or mismatched actual CLI process completion evidence.')
    for key, filename in (('raw_cli_events', 'ROOT-cli-events.jsonl'), ('stderr', 'ROOT-cli-stderr.txt')):
        if item[key]['path'] != str(slot / filename):
            raise RuntimeError('CLI completion artifact outside exact attempt slot.')
        exact(item[key])  # Byte hashes only; no event/label parsing.
    return path, item


def verified_reception(batch, attempt, config):
    directory = RUN / f'batch-{batch:04d}'
    path = directory / f'root-attempt-reception-{attempt:04d}-v3.json'
    item = load(path)
    scope = config['batches'][str(batch)]
    if (item.get('artifact_type') != 'ROOT_whole_batch_technical_reception'
            or item.get('run_id') != RUN.name or item.get('batch_id') != directory.name
            or item.get('attempt_number') != attempt
            or item.get('actor_completion_received_by_ROOT') is not True
            or item.get('assignment') != scope['assignment']
            or item.get('fixed_dispatch_request') != scope['original_fixed_core_dispatch_request']
            or item.get('validator') != config['corrected_validator']
            or item.get('nonsemantic_validator_amendment') != config['validator_amendment']
            or item.get('state') not in ('technical_valid_whole_batch', 'technical_invalid_whole_batch')):
        raise RuntimeError('Unverified whole-batch technical reception identity.')
    completion_path, _ = cli_completion(batch, attempt)
    retained = {x['path']: x for x in item['attempt_files']}
    if retained.get(str(completion_path)) != binding(completion_path):
        raise RuntimeError('Reception does not bind the actual CLI terminal receipt.')
    return path, item


def batch_state(batch, config):
    directory = RUN / f'batch-{batch:04d}'
    scope = config['batches'][str(batch)]
    exact(scope['assignment'])
    exact(scope['original_fixed_core_dispatch_request'])
    selected = directory / 'root-selection.json'
    if selected.exists():
        item = load(selected)
        attempt = item['selected_attempt_number']
        if type(attempt) is not int or not 1 <= attempt <= 3:
            raise RuntimeError('Invalid selected attempt identity.')
        receipt_path, receipt = verified_reception(batch, attempt, config)
        if (item.get('run_id') != RUN.name or item.get('batch_id') != directory.name
                or item.get('technical_reception') != binding(receipt_path)
                or receipt['state'] != 'technical_valid_whole_batch'
                or item.get('cross_attempt_record_combination') is not False
                or item.get('label_based_selection') is not False):
            raise RuntimeError('Selection is not a verified earliest whole-batch reception.')
        for earlier in range(1, attempt):
            _, prior = verified_reception(batch, earlier, config)
            if prior['state'] != 'technical_invalid_whole_batch':
                raise RuntimeError('Selection skipped an earlier valid attempt.')
        for later in range(attempt + 1, 4):
            later_slot = directory / f'attempt-{later:04d}'
            if ((directory / f'root-attempt-reception-{later:04d}-v3.json').exists()
                    or (later_slot.exists() and (not later_slot.is_dir() or any(later_slot.iterdir())))):
                raise RuntimeError('Artifacts after a selected first; ROOT must inspect; never rerun.')
        for key in ('original_whole_batch_first', 'canonical_whole_byte_mirror'):
            exact(item[key])  # Hash unchanged bytes; never parse prediction records.
        if (item['original_whole_batch_first']['path'] != str(directory / f'attempt-{attempt:04d}' / 'first.json')
                or item['canonical_whole_byte_mirror']['path'] != str(directory / 'first.json')
                or receipt['validation']['submission_sha256'] != item['original_whole_batch_first']['sha256']):
            raise RuntimeError('Selection differs from the technically validated whole first.')
        if item['original_whole_batch_first']['sha256'] != item['canonical_whole_byte_mirror']['sha256']:
            raise RuntimeError('Selected whole-batch mirror changed.')
        n = receipt['validation']['record_N']
        if type(n) is not int or n <= 0 or receipt['validation']['state'] != 'technical_valid_whole_batch_submission':
            raise RuntimeError('No verified technical reception count.')
        return {'state': 'selected', 'attempt': attempt, 'verified_record_N': n}
    if (directory / 'first.json').exists():
        raise RuntimeError('Canonical first without selection; ROOT must inspect.')
    for attempt in range(1, 4):
        receipt_path = directory / f'root-attempt-reception-{attempt:04d}-v3.json'
        slot = directory / f'attempt-{attempt:04d}'
        if receipt_path.exists():
            _, receipt = verified_reception(batch, attempt, config)
            if receipt['state'] != 'technical_invalid_whole_batch':
                raise RuntimeError('Valid receipt without complete selection; ROOT must inspect.')
            continue
        # Any nonempty unreceived slot is ambiguous, even if its PID looks dead.
        if slot.exists() and (not slot.is_dir() or any(slot.iterdir())):
            raise RuntimeError(f'Unreceived nonempty slot {slot}; ROOT must inspect; never restart.')
        for later in range(attempt + 1, 4):
            later_slot = directory / f'attempt-{later:04d}'
            if ((directory / f'root-attempt-reception-{later:04d}-v3.json').exists()
                    or (later_slot.exists() and (not later_slot.is_dir() or any(later_slot.iterdir())))):
                raise RuntimeError('Nonsequential attempt artifacts; ROOT must inspect.')
        return {'state': 'ready', 'attempt': attempt, 'verified_record_N': 0}
    return {'state': 'technical_attempts_exhausted', 'attempt': 3, 'verified_record_N': 0}


def coverage(states):
    return {'scope': 'requested scheduler batch range only; batches0001..0003 excluded',
            'requested_batch_N': len(states),
            'not_inspected_batch_N': sum(x['state'] == 'not_inspected' for x in states.values()),
            'verified_selected_batch_N': sum(x['state'] == 'selected' for x in states.values()),
            'verified_selected_record_N': sum(x['verified_record_N'] for x in states.values()),
            'technical_attempts_exhausted_batch_N': sum(x['state'] == 'technical_attempts_exhausted' for x in states.values()),
            'unselected_batch_N': sum(x['state'] != 'selected' for x in states.values())}


def request_stop(signum, frame):
    global stop_requested
    stop_requested = True  # Drain owned live processes naturally; never signal them.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', type=int, default=4)
    parser.add_argument('--end', type=int, default=504)
    parser.add_argument('--root-go-no-other-cli-live', action='store_true', required=True)
    args = parser.parse_args()
    if not 4 <= args.start <= args.end <= 504:
        parser.error('Only the frozen batch0004..0504 range is allowed.')
    # Lock is scheduler ownership, not a declaration of any external CLI liveness.
    lock = (HERE / 'scheduler.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError('Another scheduler owns the lock; no dispatch permitted.')
    sealed = load(HERE / 'seal.json')
    for path in (Path(__file__).resolve(), HERE / 'input-bindings.json'):
        exact(next(x for x in sealed['output_members'] if x['path'] == str(path)))
    config = load(HERE / 'input-bindings.json')
    for item in config['core_inputs']:
        exact(item)
    runlog = HERE / 'runs' / (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
    runlog.mkdir(parents=True, exist_ok=False)
    events = (runlog / 'events.jsonl').open('x', encoding='utf-8')
    active = {}
    states = {b: {'state': 'not_inspected', 'attempt': None, 'verified_record_N': 0}
              for b in range(args.start, args.end + 1)}
    diagnostics = []
    stopping = False

    def event(kind, **fields):
        events.write(json.dumps({'at_utc': now(), 'event': kind, **fields}, ensure_ascii=False) + '\n')
        events.flush()
        os.fsync(events.fileno())

    def diagnose(error, **fields):
        nonlocal stopping
        stopping = True
        record = {'at_utc': now(), 'type': type(error).__name__, 'message': str(error), **fields}
        diagnostics.append(record)
        save(runlog / f'diagnostic-{len(diagnostics):04d}.json', record)
        event('stop_new_dispatch_root_inspection_required', **record)

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    try:
        event('ROOT_GO_asserted', start=args.start, end=args.end,
              ROOT_asserts_no_other_cli_live=True, independently_checked_by_scheduler=False,
              max_concurrent_cli=2, input_bindings=binding(HERE / 'input-bindings.json'))
        # Also refuse uncertain nonempty slots outside a limited requested range.
        # A range flag must not conceal an already-live prior scheduler attempt.
        for batch in range(4, 505):
            current = batch_state(batch, config)
            if args.start <= batch <= args.end:
                states[batch] = current
        event('preflight_complete', coverage=coverage(states))
    except Exception as error:
        diagnose(error, stage='preflight_no_model_process_started')
    while active or (not stopping and not stop_requested and any(x['state'] == 'ready' for x in states.values())):
        try:
            if stop_requested and not stopping:
                stopping = True
                event('stop_requested_drain_existing_children')
            while not stopping and not stop_requested and len(active) < 2:
                ready = sorted(b for b, s in states.items() if s['state'] == 'ready')
                if not ready:
                    break
                batch = ready[0]
                current = batch_state(batch, config)  # Recheck exact slot before launch.
                if current != states[batch]:
                    raise RuntimeError('Batch changed after preflight; ROOT must inspect.')
                attempt = current['attempt']
                argv = [sys.executable, config['runner']['path'], '--batch', str(batch), '--attempt', str(attempt)]
                prefix = f'batch-{batch:04d}-attempt-{attempt:04d}-runner'
                job = spawn(argv, runlog, prefix)
                job.update({'batch': batch, 'attempt': attempt, 'prefix': prefix})
                active[batch] = job  # Retain ownership even if recording subsequently fails.
                states[batch] = {'state': 'running', 'attempt': attempt, 'verified_record_N': 0}
                save(runlog / (prefix + '-start.json'), {**start_receipt(job), 'batch': batch, 'attempt': attempt})
                event('runner_started', batch=batch, attempt=attempt, **start_receipt(job))
            for batch, job in list(active.items()):
                if job['process'].poll() is None:
                    continue
                # Drop owned terminal children before I/O: failed receipt writes
                # must stop dispatch, not loop or accidentally repeat reception.
                del active[batch]
                states[batch] = {'state': 'terminal_requires_ROOT_inspection',
                                 'attempt': job['attempt'], 'verified_record_N': 0}
                end = terminal_receipt(job)
                save(runlog / (job['prefix'] + '-terminal.json'), end)
                event('runner_terminal', batch=batch, attempt=job['attempt'], **end)
                if end['exitcode'] != 0:
                    raise RuntimeError(f'Runner failed for batch{batch:04d}; not a coding failure or retry.')
                completion_path, completion = cli_completion(batch, job['attempt'])
                event('CLI_terminal_evidence_verified', batch=batch, attempt=job['attempt'],
                      completion=binding(completion_path), actual_cli_exitcode=completion['returncode'])
                argv = [sys.executable, config['receiver']['path'], '--run', str(RUN),
                        '--validator-amendment', config['validator_amendment']['path'],
                        '--batch', str(batch), '--attempt', str(job['attempt']), '--actor-completed']
                receiver = spawn(argv, runlog, job['prefix'].replace('-runner', '-receiver'))
                # Receiver is local technical reception, not another coding CLI.
                receiver['process'].wait()
                receiver_end = terminal_receipt(receiver)
                save(runlog / (job['prefix'].replace('-runner', '-receiver') + '-terminal.json'), receiver_end)
                if receiver_end['exitcode'] != 0:
                    raise RuntimeError('Receiver process error; no automatic retry or receipt replacement.')
                states[batch] = batch_state(batch, config)
                event('technical_reception_verified', batch=batch, attempt=job['attempt'],
                      next_state=states[batch], coverage=coverage(states))
        except Exception as error:
            # Existing children keep running. No uncertain completion counts as invalid.
            try:
                diagnose(error, stage='dispatch_or_terminal_reception')
            except Exception:
                stopping = True
                print('Receipt I/O failed; new dispatch stopped; draining owned children.', file=sys.stderr)
        if active:
            time.sleep(0.5)
    final = {'at_utc': now(), 'status': ('stopped_ROOT_inspection_required' if diagnostics or (stopping and not stop_requested)
                                      else ('stopped_by_signal' if stop_requested else 'requested_range_terminal')),
             'start': args.start, 'end': args.end, 'coverage': coverage(states),
             'states': {f'batch-{b:04d}': s for b, s in states.items()},
             'diagnostic_N': len(diagnostics), 'prediction_or_reference_records_parsed': False,
             'label_based_retry_or_selection': False, 'live_owned_runner_N_at_return': len(active)}
    save(runlog / 'run-result.json', final)
    event('scheduler_terminal', result=binding(runlog / 'run-result.json'), coverage=final['coverage'])
    events.close()
    print(json.dumps({'runlog': str(runlog), 'status': final['status'], 'coverage': final['coverage']}, ensure_ascii=False))
    return 2 if stopping or stop_requested else 0


if __name__ == '__main__':
    sys.exit(main())

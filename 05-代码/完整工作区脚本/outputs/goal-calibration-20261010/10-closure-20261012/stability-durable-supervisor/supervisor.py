"""Candidate: one detached, durably observed wait for the unchanged controller."""
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
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CONFIG = HERE / 'config.json'
ROUTES = {(42, 3), (47, 2), (49, 3), *((n, 1) for n in range(51, 59)), (59, 2), (60, 1)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


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


def exact(value):
    require(binding(value['path']) == value, 'Changed binding: ' + value['path'])


def save(path, value):
    """Exclusive metadata, fsynced file and directory; never replace a prior record."""
    p = Path(path)
    with p.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(p.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return binding(p)


@contextlib.contextmanager
def exclusive():
    with (HERE / 'supervisor.lock').open('a+b') as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def metadata_gate(authorization_path):
    """Read metadata/hash raw captures only; never parse machine predictions."""
    cfg = load(CONFIG)
    require(Path(sys.executable).resolve() == Path(cfg['python']).resolve(), 'Wrong frozen Python runtime')
    for key in ('entry', 'entry_manifest', 'entry_seal', 'GO', 'original_adoption', 'diagnosis', 'campaign_manifest'):
        exact(cfg[key])
    auth_binding = binding(authorization_path)
    auth = load(authorization_path)
    require(auth.get('artifact_type') == 'ROOT_stability_orphan_recovery_and_durable_continuation_authorization'
            and auth.get('issuer') == 'ROOT' and auth.get('template_only') is False
            and auth.get('orphan_recovery_adopted') is True and auth.get('same_campaign_continuation') is True,
            'Actual ROOT recovery and continuation authorization required')
    for key, expected in {'supervisor': binding(__file__), 'configuration': binding(CONFIG),
                          'unchanged_entry': cfg['entry'], 'unchanged_GO': cfg['GO'],
                          'unchanged_adoption': cfg['original_adoption'], 'controller_exit_diagnosis': cfg['diagnosis'],
                          'campaign_manifest': cfg['campaign_manifest']}.items():
        require(auth.get(key) == expected, 'Authorization binding mismatch: ' + key)
    out = Path(auth['output_directory']).resolve()
    require(out.parent == Path(cfg['output_parent']).resolve() and not out.exists(), 'Unique new direct-child output directory required')
    diagnosis = load(cfg['diagnosis']['path'])
    original = diagnosis['unclosed_started_attempts']
    indexed = {(int(x['batch'].rsplit('-', 1)[1]), int(x['attempt'].rsplit('-', 1)[1])): x for x in original}
    require(len(original) == len(indexed) == 13 and set(indexed) == ROUTES, 'Wrong fixed orphan scope')
    rows = auth['closed_attempts']
    keys = [(x.get('batch_number'), x.get('attempt_number')) for x in rows]
    require(len(rows) == len(set(keys)) == 13 and set(keys) == ROUTES, 'Exactly 13 unique orphan closures required')
    campaign = load(cfg['campaign_manifest']['path'])
    for item in rows:
        key = (item['batch_number'], item['attempt_number'])
        old = indexed[key]
        require(item.get('condition') == 'R3', 'Wrong condition')
        for field in ('terminal_certificate', 'technical_reception'):
            exact(item[field])
        cert = load(item['terminal_certificate']['path'])
        receipt = load(item['technical_reception']['path'])
        route = ('R3', *key)
        require(tuple(cert.get(k) for k in ('condition', 'batch_number', 'attempt_number')) == route
                and tuple(receipt.get(k) for k in ('condition', 'batch_number', 'attempt_number')) == route, 'Closure route mismatch')
        require(cert.get('artifact_type') == 'ROOT_external_orphan_process_terminal_certificate'
                and cert.get('provenance') == 'ROOT_two_observation_external_process_identity_and_sealed_files'
                and cert.get('fixture_only') is False and cert.get('actual_process_terminal') is True
                and cert.get('returncode') is None and cert.get('returncode_status') == 'unknown_parent_wait_unavailable'
                and cert.get('timed_out') is None and cert.get('timeout_status') == 'unknown_parent_wait_unavailable',
                'Not an honest failure-only external terminal certificate')
        require(cert.get('original_actual_process_start') == old['start']
                and cert.get('original_dispatch_start') == old['dispatch_start']
                and cert.get('pid') == old['pid'] and cert.get('process_group_id') == old['pid'], 'Original orphan identity differs')
        exact(old['start']); exact(old['dispatch_start'])
        dispatch = load(old['dispatch_start']['path'])
        require(dispatch['GO'] == cfg['GO'], 'Original dispatch GO differs')
        require(receipt.get('state') == 'technical_invalid_whole_batch'
                and receipt.get('completion') == item['terminal_certificate']
                and receipt.get('error', {}).get('type') == 'OrphanedControllerWaitReceiptUnavailable'
                and receipt.get('run_id') == campaign['run_id']
                and not any(k in receipt for k in ('first', 'validation', 'transport_seal', 'technical_proof')), 'Not a failure-only reception')
        slot = Path(old['start']['path']).parent
        destination = slot.parent / f'root-attempt-reception-{key[1]:04d}.json'
        require(Path(item['technical_reception']['path']) == destination, 'Receipt was not installed in its original slot')
        require(not (slot / 'ROOT-process-completion.json').exists() and not (slot.parent / 'root-selection.json').exists(), 'Conflicting original completion/selection')
        for later in range(key[1] + 1, 4):
            require(not any((slot.parent / f'attempt-{later:04d}').iterdir()), 'Later attempt already occupied')
        require(len(cert.get('observations', [])) == 2, 'Two actual observations required')
        for observed in cert['observations']:
            exact(observed)
        for retained in cert['retained_actual_files']:
            require(Path(retained['path']).parent == slot, 'Retained file outside original attempt')
            exact(retained)
    exact(auth_binding)
    return cfg, auth_binding, out, diagnosis


def clear_process_gate(cfg, diagnosis):
    spec = importlib.util.spec_from_file_location('unchanged_PID_birth_entry', cfg['entry']['path'])
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)
    manifest, _, _ = entry.frozen_context()
    entry.require_adoption(cfg['original_adoption']['path'], cfg['GO']['path'], manifest)
    rows = entry.ps_rows()
    old = diagnosis['original_controller']
    pids = {x['pid'] for x in diagnosis['unclosed_started_attempts']}
    for row in rows:
        command = row['command']
        require(not (row['pid'] == old['pid'] and row['lstart'] == old['lstart']), 'Original controller still present')
        require(row['pgid'] not in pids and row['pid'] not in pids, 'Original orphan PID/group still present or ambiguous')
        require(not (manifest['campaign_directory'] in command and (' exec ' in command or 'controller.py' in command)), 'Campaign process still active')
        require(not (cfg['entry']['path'] in command and '--mode run' in command), 'Another PID-birth controller still active')
        require(not (manifest['unchanged_successor_entrypoint']['path'] in command), 'Successor controller still active')
        require(not (manifest['isolated_cli_directory'] in command and (' exec ' in command or 'codex-code-mode-host' in command)), 'Isolated CLI/host still active')
    return {'at_utc': now(), 'old_controller_and_orphan_PIDs_and_groups_absent': True,
            'active_campaign_CLI_and_host_count': 0, 'observation_method': 'unchanged_entry.ps_rows + fixed identity and command checks'}


def observe_birth(pid):
    result = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'lstart='], capture_output=True, text=True, check=False)
    value = result.stdout.strip()
    return {'pid': pid, 'lstart': value or None,
            'birth_observation_status': 'observed' if result.returncode == 0 and value else 'already_exited_or_observation_unavailable',
            'observation_returncode': result.returncode, 'at_utc': now()}


def wait_and_seal(argv, directory, provenance):
    """The only subprocess launcher. Public CLI supplies the fixed argv only."""
    out = Path(directory)
    out.mkdir(parents=True, exist_ok=False)
    save(out / 'supervisor-start.json', {'at_utc': now(), 'supervisor_pid': os.getpid(), 'supervisor_sid': os.getsid(0),
          'argv': argv, 'provenance': provenance, 'automatic_restart': False, 'statistics_computed': False})
    child = None
    waited = False
    returncode = None
    error = None
    with (out / 'controller-stdout.txt').open('xb') as stdout, (out / 'controller-stderr.txt').open('xb') as stderr:
        try:
            child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                     start_new_session=True, close_fds=True)
            save(out / 'controller-start.json', {'at_utc': now(), 'actual_Popen_started': True,
                 'controller_pid': child.pid, 'process_group_id': child.pid,
                 'argv': argv, 'returncode': None, 'returncode_status': 'not_yet_waited'})
            save(out / 'controller-identity.json', observe_birth(child.pid))
        except BaseException as exc:
            error = {'type': type(exc).__name__, 'message': str(exc)}
        finally:
            if child is not None:
                try:
                    returncode = child.wait()
                    waited = True
                except BaseException as exc:
                    error = {'type': type(exc).__name__, 'message': str(exc)}
            for stream in (stdout, stderr):
                stream.flush()
                os.fsync(stream.fileno())
    terminal = {'at_utc': now(), 'provenance': 'durable_supervisor_actual_Popen_wait',
                'actual_Popen_started': child is not None, 'controller_pid': None if child is None else child.pid,
                'actual_wait_returned': waited, 'actual_controller_terminal': waited,
                'returncode': returncode if waited else None,
                'returncode_status': 'observed_by_parent_wait' if waited else 'unknown_wait_not_completed',
                'launch_or_supervision_error': error,
                'stdout': binding(out / 'controller-stdout.txt'), 'stderr': binding(out / 'controller-stderr.txt'),
                'all_CLI_children_and_hosts_terminal_claimed': False,
                'all_five_conditions_terminal_claimed': False, 'statistics_computed': False,
                'automatic_restart': False}
    save(out / 'controller-terminal.json', terminal)
    return terminal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorization', required=True)
    args = parser.parse_args()
    require(os.getsid(0) == os.getpid(), 'Launch supervisor with start_new_session=True')
    stdin = os.fstat(0)
    require(stat.S_ISCHR(stdin.st_mode) and stdin.st_rdev == os.stat('/dev/null').st_rdev, 'Launch supervisor with stdin=DEVNULL')
    with exclusive():
        cfg, authorization, out, diagnosis = metadata_gate(args.authorization)
        observation = clear_process_gate(cfg, diagnosis)
        exact(authorization)
        argv = [cfg['python'], '-B', cfg['entry']['path'], '--mode', 'run', '--target', 'stability13',
                '--go', cfg['GO']['path'], '--adoption', cfg['original_adoption']['path']]
        result = wait_and_seal(argv, out, {'ROOT_authorization': authorization, 'configuration': binding(CONFIG),
                     'supervisor': binding(__file__), 'fresh_process_gate': observation})
        if not result['actual_wait_returned'] or result['launch_or_supervision_error'] is not None:
            raise SystemExit(1)
        raise SystemExit(result['returncode'] if result['returncode'] >= 0 else 128 - result['returncode'])


if __name__ == '__main__':
    main()

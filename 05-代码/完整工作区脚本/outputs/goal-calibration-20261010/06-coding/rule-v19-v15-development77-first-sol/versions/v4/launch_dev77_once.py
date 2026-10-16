"""Launch the sealed v4/v15 development77 process once, only after explicit ROOT GO."""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def verify(expected):
    actual = bind(expected['path'])
    if any(actual[key] != expected[key] for key in ('path', 'sha256', 'bytes')):
        raise ValueError('sealed dependency differs: ' + expected['path'])


def save(name, value):
    with (HERE / name).open('x', encoding='utf8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-go', required=True)
    args = parser.parse_args()
    go_path = Path(args.root_go).resolve()
    if go_path != HERE / 'root-go.json':
        raise ValueError('only this first-output directory ROOT release record is accepted')
    release = json.loads(go_path.read_bytes())
    preflight = json.loads((HERE / 'preflight.json').read_bytes())
    seal = json.loads((HERE / 'pre-run-seal.json').read_bytes())
    required = {
        'decision': 'GO', 'authorized_by': 'ROOT',
        'scope_sha256': preflight['scope_binding']['sha256'],
        'pre_run_seal_sha256': bind(HERE / 'pre-run-seal.json')['sha256'],
        'algorithm_version': preflight['algorithm_version'],
        'source_packet_sha256': preflight['source_packet']['sha256'],
        'candidate_manual_sha256': preflight['manual']['sha256'],
        'independent_controls_passed': True, 'independent_control_N': 43,
        'independent_control_passed_N': 43, 'max_actual_cohort_inference_runs': 1,
        'actual_cohort_inference_runs_before_release': 0}
    if any(release.get(key) != value for key, value in required.items()):
        raise ValueError('ROOT GO is missing or does not release this exact frozen attempt')
    if not isinstance(release.get('authorization_basis'), str) or not release['authorization_basis'].strip():
        raise ValueError('explicit ROOT GO message basis absent')
    verify(release['independent_control_binding'])
    for item in seal['files'] + seal['implementation_files'] + seal['material_bindings'] + seal['other_frozen_bindings']:
        verify(item)
    previous = Path(preflight['superseded_preparation_directory'])
    if (previous / 'actual-launch-record.json').exists() or (previous / 'run77-first').exists():
        raise ValueError('superseded prepared v2 has an actual attempt; new first77 launch rejected')
    argv = preflight['argv']
    out = Path(seal['first_output_directory'])
    if out.exists() or (HERE / 'actual-launch-record.json').exists():
        raise ValueError('the single actual attempt has already started; retry and overwrite prohibited')
    record = {
        'status': 'actual_v2_v15_driver_launch_committed', 'started_at_utc': now(), 'argv': argv,
        'launcher_binding': bind(__file__), 'scope_binding': preflight['scope_binding'],
        'pre_run_seal_binding': bind(HERE / 'pre-run-seal.json'), 'ROOT_GO_binding': bind(go_path),
        'independent_control_binding': release['independent_control_binding'],
        'independent_control_N': release['independent_control_N'],
        'independent_control_passed_N': release['independent_control_passed_N'],
        'source_packet_binding': preflight['source_packet'], 'manual_binding': preflight['manual'],
        'algorithm_version': preflight['algorithm_version'], 'driver_version': preflight['driver_version'],
        'purpose': 'disclosed_label_development77_regression', 'max_actual_cohort_inference_runs': 1,
        'calibration_labels_already_disclosed': True, 'blind_validation': False,
        'formal_validation_complete': False, 'human_validation_complete': False,
        'accuracy_computation_authorized': False, 'retry_authorized': False}
    save('actual-launch-record.json', record)
    environment = dict(os.environ)
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    try:
        with (HERE / 'driver-stdout.txt').open('xb') as stdout, (HERE / 'driver-stderr.txt').open('xb') as stderr:
            result = subprocess.run(argv, cwd=HERE, stdout=stdout, stderr=stderr,
                env=environment, check=False)
    except BaseException as error:
        save('actual-launch-process-error.json', {
            'status': 'launch_failed_preserved_no_retry', 'error_type': type(error).__name__,
            'message': str(error), 'finished_at_utc': now(),
            'actual_driver_process_launch_attempt_N': 1, 'retry_attempted': False})
        raise
    summary = {
        'status': 'driver_process_finished', 'exit_code': result.returncode, 'finished_at_utc': now(),
        'argv': argv, 'stdout_binding': bind(HERE / 'driver-stdout.txt'),
        'stderr_binding': bind(HERE / 'driver-stderr.txt'), 'actual_driver_process_launch_N': 1,
        'retry_attempted': False, 'execution_and_failure_outputs_preserved': True,
        'first_output_exists': out.exists(),
        'driver_output_seal_binding': bind(out / 'seal.json') if (out / 'seal.json').exists() else None,
        'algorithm_version': preflight['algorithm_version'], 'driver_version': preflight['driver_version'],
        'calibration_labels_already_disclosed': True, 'blind_validation': False,
        'formal_validation_complete': False, 'human_validation_complete': False}
    save('actual-launch-result.json', summary)
    print(json.dumps({key: summary[key] for key in ('status', 'exit_code', 'actual_driver_process_launch_N',
        'retry_attempted', 'first_output_exists', 'algorithm_version')}, ensure_ascii=False))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())

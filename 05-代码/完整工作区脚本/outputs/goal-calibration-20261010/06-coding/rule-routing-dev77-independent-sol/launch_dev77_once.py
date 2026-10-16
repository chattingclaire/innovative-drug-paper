"""Launch the sealed candidate argv once and preserve all process outcomes."""
import datetime, hashlib, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
def bind(p):
    p = Path(p).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
def save(name, value):
    with (HERE / name).open('x', encoding='utf8') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
preflight = json.loads((HERE / 'preflight.json').read_bytes())
sealed = json.loads((HERE / 'pre-run-seal.json').read_bytes())
for b in sealed['files'] + sealed['implementation_files'] + sealed['material_bindings']:
    if any(bind(b['path'])[k] != b[k] for k in ('path', 'sha256', 'bytes')):
        raise ValueError('sealed dependency differs: ' + b['path'])
if (HERE / 'actual-launch-record.json').exists() or Path(preflight['argv'][-1]).exists():
    raise ValueError('single attempt already started; no retry authorization')
record = {'status': 'actual_candidate_driver_launch_committed', 'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'argv': preflight['argv'], 'launcher_binding': bind(__file__), 'scope_binding': preflight['scope_binding'], 'pre_run_seal_binding': bind(HERE / 'pre-run-seal.json'), 'source_packet_binding': preflight['source_packet'], 'purpose': 'development77_independent_technical_regression', 'maximum_actual_cohort_inference_runs': 1, 'new_calibration_applied': False, 'human_independent_label_N': 0, 'formal_validation_complete': False, 'human_validation_complete': False}
save('actual-launch-record.json', record)
try:
    result = subprocess.run(preflight['argv'], cwd=HERE, capture_output=True, check=False)
except BaseException as err:
    save('actual-launch-process-error.json', {'status': 'launch_failed_preserved_no_retry', 'error_type': type(err).__name__, 'message': str(err), 'finished_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    raise
for name, raw in (('driver-stdout.txt', result.stdout), ('driver-stderr.txt', result.stderr)):
    with (HERE / name).open('xb') as f:
        f.write(raw)
summary = {'status': 'driver_process_finished', 'exit_code': result.returncode, 'finished_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'argv': preflight['argv'], 'stdout_binding': bind(HERE / 'driver-stdout.txt'), 'stderr_binding': bind(HERE / 'driver-stderr.txt'), 'actual_driver_process_launch_N': 1, 'retry_attempted': False, 'execution_and_failure_outputs_preserved': True}
save('actual-launch-result.json', summary)
print(result.stdout.decode('utf8', errors='replace'), end='')
if result.stderr:
    print(result.stderr.decode('utf8', errors='replace'), end='', file=sys.stderr)
raise SystemExit(result.returncode)

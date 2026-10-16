"""Reproduce the two authorized named regressions once with one frozen version."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent
SOURCE_SCOPE_SHA = '9bfafaca9a8231233ae8e9865f9fe5900ec9ba102479f331db88e36775470042'
SCOPE_NAMES = ('old41', 'old36')


def binding(path):
    p = Path(path).resolve()
    data = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def write(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pre-run-bindings', required=True)
    parser.add_argument('--pre-run-bindings-sha256', required=True)
    args = parser.parse_args()
    clearance = Path(args.pre_run_bindings).resolve()
    if clearance.parent != BASE or binding(clearance)['sha256'] != args.pre_run_bindings_sha256:
        raise ValueError('use the exact minimal-controls pre-run binding')
    check = json.loads(clearance.read_text())
    if check.get('status') != 'PASS_MINIMAL_CONTROLS_AND_FROZEN_BINDINGS_FOR_TWO_FIRST_RUNS':
        raise ValueError('minimal controls and implementation bindings are not frozen')
    if binding(BASE / 'source-scope-v12.json')['sha256'] != SOURCE_SCOPE_SHA:
        raise ValueError('finite source scope changed')
    code = [binding(BASE / n) for n in ('runner.py', 'source_packet.py', 'source_receipts.py', 'evidence.py', 'relations.py', 'dimensions.py')]
    audited = {i['path']: i for i in check['implementation_files']}
    if any(i['path'] not in audited or i['sha256'] != audited[i['path']]['sha256'] or i['bytes'] != audited[i['path']]['bytes'] for i in code):
        raise ValueError('inference code differs from exact pre-run clearance')
    manifest = json.loads((BASE / 'source-scope-v12.json').read_text())
    commands = []
    for name in SCOPE_NAMES:
        commands.append([sys.executable, '-B', str(BASE / 'runner.py'),
            '--scope-manifest', str(BASE / 'source-scope-v12.json'), '--scope-manifest-sha256', SOURCE_SCOPE_SHA,
            '--finite-declaration', str(BASE / 'finite-execution-scope-before-source.json'), '--scope', name,
            '--approved-output-root', str(BASE), '--out', str(BASE / ('run-' + name + '-01'))])
    repro = {'status': 'declared_before_two_actual_runs', 'implementation_files': code,
        'source_scope_manifest': binding(BASE / 'source-scope-v12.json'),
        'finite_scope_declaration': binding(BASE / 'finite-execution-scope-before-source.json'),
        'clearance': binding(clearance), 'material_bindings': manifest['bindings'],
        'scope_record_N': {n: len(manifest['scopes'][n]) for n in SCOPE_NAMES},
        'unique_record_N': 77, 'named_scope_attempt_N': 77,
        'commands': commands, 'new2_new4_reference_evaluation': False,
        'updated_ROOT_AI_development_reference_evaluation_authorized_after_all_actual_seals': True,
        'reference_evaluation_performed': False,
        'stop_after_two_actual_runs_postseal_updated_reference_comparison_and_delivery_report': True}
    write(BASE / 'reproduction-before-runs.json', repro)
    before = [binding(p) for p in sorted(BASE.rglob('*')) if p.is_file()]
    write(BASE / 'pre-run-tree-freeze.json', {'status': 'all_existing_version_files_bound_before_actual_runs', 'files': before})
    results = []
    for name, command in zip(SCOPE_NAMES, commands):
        if any(binding(c['path'])['sha256'] != c['sha256'] for c in code):
            raise ValueError('implementation changed between named scopes')
        with (BASE / ('actual-' + name + '-01-launch.txt')).open('x') as log:
            process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        seal_path = BASE / ('run-' + name + '-01') / 'seal.json'
        seal = json.loads(seal_path.read_text()) if seal_path.exists() else None
        result = {'scope': name, 'returncode': process.returncode, 'argv': command,
            'seal': binding(seal_path) if seal_path.exists() else None,
            'status': seal['status'] if seal else 'unsealed_launch_failure',
            'prediction_N': seal['prediction_n'] if seal else 0,
            'decision_N': seal['decision_n'] if seal else 0,
            'implementation_error_N': seal['implementation_error_n'] if seal else None,
            'rules_null_N': seal['rules_null_n'] if seal else None,
            'prediction_SHA': seal['prediction_sha256'] if seal else None}
        results.append(result)
        print(json.dumps({k: result[k] for k in ('scope', 'returncode', 'status', 'prediction_N', 'decision_N', 'implementation_error_N', 'rules_null_N', 'prediction_SHA')}, ensure_ascii=False), flush=True)
    write(BASE / 'actual-two-scopes-launch-bindings.json', {'results': results,
        'unique_record_N': 77, 'named_expected_record_attempt_N': 77,
        'actual_prediction_N': sum(r['prediction_N'] for r in results),
        'classification_code_unchanged_across_scopes': all(binding(c['path'])['sha256'] == c['sha256'] for c in code)})
    return 0 if all(r['returncode'] == 0 for r in results) else 2


if __name__ == '__main__':
    raise SystemExit(main())

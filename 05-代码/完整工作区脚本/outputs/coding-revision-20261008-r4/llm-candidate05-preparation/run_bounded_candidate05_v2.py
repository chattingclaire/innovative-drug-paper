"""Default: freeze/dry-plan only. Root may later choose --execute after review.

The two fixed runs contain 13 logical calls, at most 39 technical attempts.
No labels, dimensions, batches or semantic failures can be selectively rerun.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYTHON = Path('/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true', help='Only for root after reviewing the frozen scope. Default makes no model calls.')
    args = parser.parse_args()
    assert Path(sys.executable).resolve() == PYTHON.resolve(), 'Use the declared bundled Python.'
    package = json.loads((HERE / 'candidate05_package_manifest_v2.json').read_text())
    for bound in package['files']:
        assert sha(bound['path']) == bound['sha256'], f'Prepared package changed: {bound["path"]}'
    freeze = json.loads((HERE / 'candidate05_development_freeze_v2.json').read_text())
    assert freeze['model'] == 'gpt-5.6-sol' and freeze['reasoning_effort'] == 'medium'
    assert freeze['nominal_model_calls'] == 13 and freeze['technical_maximum_calls'] == 39
    for name in ['candidate05_prompt', 'exposed240_input', 'synthetic62_input', 'synthetic_expected_private', 'human_reserved_exclusion_metadata']:
        bound = freeze[name]
        assert sha(bound['path']) == bound['sha256'], f'Frozen binding changed: {name}'
    for bound in freeze['runtime'].values():
        assert sha(bound['path']) == bound['sha256']
    for bound in freeze['prior_artifacts_preserved'].values():
        assert sha(bound['path']) == bound['sha256']
    history = HERE / 'historical_comparison_freeze.json'
    assert history.exists(), 'Historical comparisons must be frozen before any execution.'
    historical = json.loads(history.read_text())
    for bound in historical['frozen_files'].values():
        assert sha(bound['path']) == bound['sha256']
    for run in freeze['planned_runs']:
        inp = freeze['exposed240_input'] if run['n'] == 240 else freeze['synthetic62_input']
        command = [str(PYTHON), str(HERE / 'runtime-v2/run_production_v32.py'),
                   '--input', inp['path'], '--expected-input-sha256', inp['sha256'],
                   '--prompt', freeze['candidate05_prompt']['path'], '--expected-n', str(run['n']),
                   '--run-name', run['name'], '--batch-size', str(run['batch_size']),
                   '--workers', str(run['workers']), '--max-attempts', '3',
                   '--purpose', 'One frozen candidate05 bounded development run; no independent-validation or production-adoption claim.']
        if not args.execute:
            command.append('--plan-only')
        print(json.dumps({'mode': 'actual_root_selected_execution' if args.execute else 'plan_only_no_model_calls',
                          'command': command}, ensure_ascii=False), flush=True)
        subprocess.run(command, check=True)


if __name__ == '__main__':
    main()

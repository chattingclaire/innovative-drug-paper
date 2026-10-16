"""Default: print the frozen plan only. Execution requires separate root authorization.

The runner receives only the proposed prompt and coding inputs, never private
mechanism notes, control expectations or other methods' predictions.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYTHON = Path('/Users/rainbow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--authorization-file', type=Path)
    args = parser.parse_args()
    assert Path(sys.executable).resolve() == PYTHON.resolve()
    freeze_path = HERE / 'design_freeze.json'
    freeze = json.loads(freeze_path.read_text())
    assert freeze['nominal_logical_requests'] == 15 and freeze['max_identical_technical_attempts'] == 45
    assert freeze['model'] == 'gpt-5.6-sol' and freeze['reasoning_effort'] == 'medium'
    for binding in freeze['files'] + freeze['source_bindings']:
        assert sha(binding['path']) == binding['sha256'], f'Frozen dependency changed: {binding["path"]}'
    plan = json.loads((HERE / 'candidate07_execution_plan_PROPOSED.json').read_text())
    assert [run['n'] for run in plan['runs']] == [240, 62, 24, 20]
    assert sum(run['logical_requests'] for run in plan['runs']) == 15
    if args.execute:
        assert args.authorization_file is not None, 'Separate root authorization required.'
        authorization = json.loads(args.authorization_file.read_text())
        assert authorization['authorized'] is True
        assert authorization['design_freeze_sha256'] == sha(freeze_path)
        assert authorization['scope'] == [240, 62, 24, 20]
        assert authorization['model'] == 'gpt-5.6-sol' and authorization['reasoning_effort'] == 'medium'
        assert authorization['max_logical_requests'] == 15 and authorization['max_technical_attempts'] == 45
        assert authorization['first_technically_valid_only'] is True
        assert freeze['independent_preflight_no_blocking_findings'] is True
        for run in plan['runs']:
            command = run['future_execution_command_after_separate_root_authorization_only']
            name = command[command.index('--run-name') + 1]
            assert not (HERE / 'runtime-unchanged-v2' / name).exists(), 'Only one fresh complete scope is authorized.'
    for run in plan['runs']:
        command = run['future_execution_command_after_separate_root_authorization_only']
        if not args.execute:
            print(json.dumps({'status': 'plan_only_no_cli_or_model_calls', 'n': run['n'],
                              'command': command + ['--plan-only']}, ensure_ascii=False), flush=True)
            continue
        print(json.dumps({'status': 'root_authorized_complete_development_run', 'n': run['n'], 'command': command}, ensure_ascii=False), flush=True)
        subprocess.run(command, check=True)


if __name__ == '__main__':
    main()

"""Execute only the complete frozen root-authorized candidate06 scope.

Without --execute this prints the predeclared plan and makes no CLI/model call.
The runner never reads the private mechanism ledger or control expectations.
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
    args = parser.parse_args()
    assert Path(sys.executable).resolve() == PYTHON.resolve()
    freeze = json.loads((HERE / 'design_freeze.json').read_text())
    assert freeze['nominal_logical_requests'] == 14
    assert freeze['max_identical_technical_attempts'] == 42
    assert freeze['model'] == 'gpt-5.6-sol' and freeze['reasoning_effort'] == 'medium'
    for bound in freeze['files'] + freeze['source_bindings']:
        assert sha(bound['path']) == bound['sha256'], f'Frozen dependency changed: {bound["path"]}'
    authorization = json.loads((HERE / 'root_execution_authorization.json').read_text())
    assert authorization['authorized'] is True and authorization['scope'] == [240, 62, 24]
    assert authorization['model'] == 'gpt-5.6-sol' and authorization['reasoning_effort'] == 'medium'
    assert freeze['independent_synthetic_preflight']['no_blocking_findings'] is True
    plans = json.loads((HERE / 'candidate06_execution_plan_PROPOSED.json').read_text())
    assert [run['n'] for run in plans['runs']] == [240, 62, 24]
    assert sum(run['logical_requests'] for run in plans['runs']) == 14
    if args.execute:
        for run in plans['runs']:
            command = run['future_execution_command_after_separate_root_authorization_only']
            name = command[command.index('--run-name') + 1]
            assert not (HERE / 'runtime-unchanged-v2' / name).exists(), 'This authorization is for one fresh complete scope, not a semantic rerun or resume.'
    for run in plans['runs']:
        command = run['future_execution_command_after_separate_root_authorization_only']
        if not args.execute:
            print(json.dumps({'status': 'plan_only_no_cli_or_model_calls', 'n': run['n'], 'command': command + ['--plan-only']}, ensure_ascii=False), flush=True)
            continue
        print(json.dumps({'status': 'root_authorized_complete_development_run', 'n': run['n'], 'command': command}, ensure_ascii=False), flush=True)
        subprocess.run(command, check=True)


if __name__ == '__main__':
    main()

"""One authorized phase at a time; default prints metadata without CLI calls."""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
from candidate08_support import (HERE, FREEZE, RUNTIME, PLAN, read, sha, binding,
    check_plan, verify_freeze, check_authorization, check_phase_gate)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--authorization-file', type=Path)
    parser.add_argument('--phase', choices=['new-controls','inherited-controls','exposed240'])
    args = parser.parse_args()
    plan = read(PLAN)
    check_plan(plan)
    if not args.execute:
        print(json.dumps({'status':'PLAN_ONLY_NO_CLI_OR_MODEL_CALLS','phases':plan['phases'],
            'run_keys':plan['scope_run_keys'],'n':plan['scope_sizes'],'logical_requests':17,
            'max_identical_technical_attempts':51,'requires_separate_root_authorization':True,
            'note':'Does not call runner --plan-only, which would invoke CLI --version.'},ensure_ascii=False))
        return
    assert Path(sys.executable).resolve() == Path('/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3').resolve()
    assert args.phase and args.authorization_file, 'Explicit phase and separate root authorization required.'
    _, plan = verify_freeze()
    check_authorization(read(args.authorization_file), sha(FREEZE), plan, args.phase)
    phase_index = [x['phase'] for x in plan['phases']].index(args.phase)
    for preceding in plan['phases'][:phase_index]:
        gate = HERE/'phase-gates'/f'{preceding["phase"]}.json'
        check_phase_gate(read(gate), preceding['phase'], sha(FREEZE), plan)
    phase = plan['phases'][phase_index]
    runs = [r for r in plan['runs'] if r['run_key'] in phase['run_keys']]
    for run in runs:
        assert not (RUNTIME/run['run_name']).exists(), 'No phase rerun/semantic replacement allowed.'
    claim = HERE/'execution-records'/f'{args.phase}.json'
    claim.parent.mkdir(exist_ok=True)
    record = {'status':'STARTED_ONE_AUTHORIZED_PHASE','phase':args.phase,
        'created_at_UTC':datetime.now(timezone.utc).isoformat(),'design_freeze':binding(FREEZE),
        'authorization':binding(args.authorization_file),'run_keys':phase['run_keys'],
        'remaining_run_keys_NOT_RUN_YET':[r['run_key'] for r in plan['runs'] if not (RUNTIME/r['run_name']).exists()],
        'first_technical_valid_only':True,'semantic_retries':False,'launched_run_keys':[],'runs':[]}
    with claim.open('x') as stream:
        json.dump(record,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    try:
        for run in runs:
            command = run['future_execution_command_after_separate_root_authorization_only']
            print(json.dumps({'status':'ROOT_AUTHORIZED_BOUNDED_PHASE','run_key':run['run_key'],'n':run['n']},ensure_ascii=False),flush=True)
            record['launched_run_keys'].append(run['run_key'])
            subprocess.run(command,check=True)
            summary = read(RUNTIME/run['run_name']/'execution_summary.json')
            assert summary['status'] == 'complete_actual_calls_structurally_valid', 'Stop after incomplete technical scope; preserve all attempts.'
            record['runs'].append({'run_key':run['run_key'],'execution_summary':binding(RUNTIME/run['run_name']/'execution_summary.json')})
        record['status']='PHASE_EXECUTED_TECHNICAL_AND_SEMANTIC_AUDIT_REQUIRED_BEFORE_CONTINUING'
    except BaseException:
        record['status']='STOPPED_TECHNICAL_FAILURE_NO_AUTOMATIC_RERUN'
        raise
    finally:
        states=[]
        for declared in plan['runs']:
            folder=RUNTIME/declared['run_name']
            summary_path=folder/'execution_summary.json'
            if summary_path.exists() and read(summary_path).get('status')=='complete_actual_calls_structurally_valid':
                state='COMPLETED_TECHNICAL_SEMANTIC_REVIEW_SEPARATE'
            elif folder.exists() or declared['run_key'] in record['launched_run_keys']:
                state='STARTED_TECHNICALLY_INCOMPLETE_OR_FAILED'
            else:
                state='NOT_RUN'
            states.append({'run_key':declared['run_key'],'n':declared['n'],'status':state})
        record['scope_run_states']=states
        record['remaining_run_keys_NOT_RUN_YET']=[r['run_key'] for r in states if r['status']=='NOT_RUN']
        claim.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':
    main()

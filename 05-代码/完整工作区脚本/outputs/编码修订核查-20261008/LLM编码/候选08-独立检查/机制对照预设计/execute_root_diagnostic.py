"""One authorized bounded execution; preserve attempts, never use semantic scores."""
import hashlib,json,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
BASE=Path(__file__).resolve().parent
PREP=BASE/'root_execution_preparation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def main():
    authp=PREP/'root_execution_authorization.json';auth=json.loads(authp.read_text())
    freeze=PREP/'preparation_freeze.json';assert sha(freeze)==auth['preparation_freeze_sha256']
    assert auth['status']=='AUTHORIZED_BOUNDED_FOUR_ARM_DIAGNOSTIC_ONLY'
    pf=Path(auth['independent_preflight']['path']);assert sha(pf)==auth['independent_preflight']['sha256']
    assert auth['independent_preflight_pass'] is True
    assert auth['maximum_logical_requests']==4 and auth['maximum_identical_technical_attempts']==12
    for b in json.loads(freeze.read_text())['files']:assert sha(Path(b['path']))==b['sha256'],b['path']
    plan=json.loads((PREP/'final_execution_plan.json').read_text())
    marker=PREP/'actual_execution_start.json'
    with marker.open('x') as f:json.dump({'started_at_UTC':datetime.now(timezone.utc).isoformat(),'authorization_sha256':sha(authp)},f)
    records=[];failed=False
    for arm in plan['arms']:
        if failed:
            records.append({'arm':arm['arm'],'status':'NOT_RUN_AFTER_TECHNICAL_EXHAUSTION'});continue
        run=PREP/'runtime'/arm['arm']
        assert not run.exists(),'do not restart an existing arm'
        cmd=[sys.executable,str(PREP/'runtime/run_production_v32.py'),*arm['runner_arguments']]
        start=time.time()
        with (PREP/(arm['arm']+'_runner_transcript.txt')).open('x') as transcript:
            proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
            for line in proc.stdout:
                transcript.write(line);transcript.flush();print(line,end='',flush=True)
            code=proc.wait()
        record={'arm':arm['arm'],'exit_code':code,'elapsed_seconds':round(time.time()-start,3),'command':cmd}
        sp=run/'execution_summary.json'
        if sp.exists():
            summary=json.loads(sp.read_text());record['summary']=summary;record['summary_sha256']=sha(sp)
        else:summary={}
        ok=code==0 and summary.get('status')=='complete_actual_calls_structurally_valid'
        record['status']='ACTUAL_COMPLETED_REQUIRES_SEMANTIC_REVIEW' if ok else 'TECHNICAL_FAILURE_PRESERVED'
        if ok:
            actual=run/'batches/batch-0001/request.txt'
            assert actual.read_bytes()==Path(arm['offline_request']['path']).read_bytes(),'actual request differs from predeclared bytes'
            record['actual_request_sha256']=sha(actual)
            record['offline_request_equal_actual']=True
        records.append(record);failed=not ok
        write(PREP/'actual_execution_progress.json',{'arms':records,'semantic_review_not_done':True})
    final={'status':'TECHNICALLY_INCOMPLETE_PRESERVED' if failed else 'ALL_FOUR_ACTUAL_REQUESTS_COMPLETE_SEMANTIC_REVIEW_PENDING',
           'finished_at_UTC':datetime.now(timezone.utc).isoformat(),'arms':records,
           'new_candidate_or_adoption':False,'original08_status':'FAIL_CONFIRMED_SEMANTIC_ERROR'}
    write(PREP/'actual_execution_completion.json',final)
    print(json.dumps({'status':final['status'],'arms_recorded':len(records)},ensure_ascii=False),flush=True)
    if failed:raise SystemExit(2)
if __name__=='__main__':main()

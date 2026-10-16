"""Bounded NONHUMAN controls. Never opens campaign captures or launches processes."""
import copy
import json
from pathlib import Path
import tempfile
import orphan_recovery as o

ABSENT = ' 100 1 100 S Mon Oct 12 16:00:00 2026 /NONHUMAN/unrelated\n'

def fixture(root):
    root=Path(root); root.mkdir(exist_ok=True)
    run=root/'campaign';run.mkdir()
    for name in ['go','adoption','diagnosis','implementation']:
        o.put(root/(name+'.json'),{'NONHUMAN':True,'name':name})
    entries=[]
    for batch,attempt in o.FIXED:
        selection=run/f'b{batch}'/'R3'; selection.mkdir(parents=True)
        slot=selection/f'attempt-{attempt:04d}';slot.mkdir()
        assignment=o.put(selection/'assignment.json',{'NONHUMAN':True})
        request=o.put(selection/'request.json',{'NONHUMAN':True})
        r=dict(condition='R3',batch_number=batch,attempt_number=attempt,batch_id=f'NONHUMAN-{batch}',
               output_directory=str(slot),selection_directory=str(selection),working_directory=str(selection),
               assignment=assignment,fixed_request=request)
        argv=['/NONHUMAN/cli','exec','--output-last-message',str(slot/'ROOT-cli-final-message.txt')]
        d=o.put(slot/'ROOT-dispatch-start.json',dict(GO=o.bind(root/'go.json'),assignment=assignment,
               stdin=request,argv=argv,working_directory=str(selection),condition='R3',batch_number=batch,attempt_number=attempt))
        started='2026-10-12T07:20:00+00:00';pid=1000+batch
        a=o.put(slot/'ROOT-actual-process-start.json',dict(start=d,actual_CLI_process_started=True,
                                                        pid=pid,process_group_id=pid,at_utc=started))
        for name in ['ROOT-cli-events.jsonl','ROOT-stderr.txt','ROOT-cli-final-message.txt']:
            (slot/name).write_text('NONHUMAN uninterpreted bytes; complete-looking final still cannot establish returncode.\n')
        for n in range(1,attempt):
            cp=o.put(selection/f'NONHUMAN-prior-{n}.json',{'actual_process_terminal':True,'NONHUMAN':True})
            o.put(selection/f'root-attempt-reception-{n:04d}.json',{'state':'technical_invalid_whole_batch','completion':cp})
        entries.append(dict(route=r,actual_start=a,dispatch_start=d,pid=pid,process_group_id=pid,
                            actual_started_at_utc=started,argv=argv,
                            receipt_destination=str(selection/f'root-attempt-reception-{attempt:04d}.json')))
    manifest=o.put(root/'manifest.json',{'routes':[e['route'] for e in entries]})
    s=dict(fixture_only=True,NONHUMAN=True,run_id='NONHUMAN',campaign_directory=str(run),
           max_total_attempts=3,original_timeout_seconds=3600,manifest=manifest,
           original_GO=o.bind(root/'go.json'),original_adoption=o.bind(root/'adoption.json'),
           diagnosis=o.bind(root/'diagnosis.json'),original_implementation={'x':o.bind(root/'implementation.json')},
           controller_identity={'pid':999,'lstart':'Mon Oct 12 06:48:58 2026'},
           isolated_cli_directory='/NONHUMAN/isolated-cli',entries=entries)
    sp=root/'scope.json';o.put(sp,s)
    return sp,s

def observations(root,sp,raw=ABSENT):
    return [o.observe(sp,root/f'obs{i}.json',synthetic=True,raw_ps=raw,at=f'2026-10-12T08:0{i}:00+00:00') for i in [1,2]]

def adoption(root,sp,s,plan):
    p=root/'adoption-new.json'
    o.put(p,dict(artifact_type='ROOT_failure_only_orphan_closure_adoption',issuer='ROOT',template_only=False,
                 fixture_only=True,adopted=True,plan=plan,scope=o.bind(sp),implementation=o.bind(o.__file__),
                 original_GO=s['original_GO'],original_adoption=s['original_adoption'],NONHUMAN_process_table=ABSENT))
    return p

def run():
    results=[]
    def test(name,fn):
        with tempfile.TemporaryDirectory(prefix='NONHUMAN-orphan-') as tmp:
            root=Path(tmp).resolve();sp,s=fixture(root)
            fn(root,sp,s)
        results.append({'name':name,'passed':True,'NONHUMAN':True})
    def reject(fn,part=''):
        try:fn()
        except (ValueError,FileExistsError,FileNotFoundError) as e:
            assert part in str(e),(part,str(e));return
        raise AssertionError('expected refusal')
    def positive(root,sp,s):
        obs=observations(root,sp)
        pb=o.prepare(sp,obs,[b for b,a in o.FIXED],root/'prepared',synthetic=True)
        p=o.load(pb['path']);assert len(p['entries'])==13
        for e in p['entries']:
            c=o.load(e['certificate']['path']);r=o.load(e['receipt_payload_binding']['path'])
            assert c['returncode'] is None and c['timed_out'] is None and c['failure_only']
            assert r['state']=='technical_invalid_whole_batch' and 'first' not in r
            assert e['remaining_original_attempts']==3-e['attempt_number']
            if e['attempt_number']==3:assert e['exhausted'] and e['remaining_original_attempts']==0
        auth=adoption(root,sp,s,pb)
        assert o.install(sp,pb,auth,synthetic=True)['installed_N']==13
        assert o.install(sp,pb,auth,synthetic=True)['installed_N']==13
        assert not any(Path(e['route']['output_directory']).joinpath('ROOT-process-completion.json').exists() for e in s['entries'])
        assert not any(Path(e['route']['output_directory']).joinpath('first.json').exists() for e in s['entries'])
    test('13 unknown + captured bytes -> invalid only; third exhausted; exact idempotent install',positive)
    def blocker(raw):
        return lambda root,sp,s:reject(lambda:o.prepare(sp,observations(root,sp,raw),[42],root/'p',synthetic=True),'process still live')
    test('root absent but original group child alive',blocker(' 333 1 1042 S Mon Oct 12 15:25:00 2026 /NONHUMAN/child\n'))
    test('isolated CLI host alive',blocker(' 334 1 334 S Mon Oct 12 15:25:00 2026 /NONHUMAN/isolated-cli/codex-code-mode-host\n'))
    test('original root identity remains',blocker(' 1042 1 1042 S Mon Oct 12 15:20:00 2026 /NONHUMAN/cli exec x\n'))
    def reuse(root,sp,s):
        raw=' 1042 1 777 S Mon Oct 12 16:00:00 2026 /NONHUMAN/unrelated\n'
        assert not o.process_blockers(s,o.ps_rows(raw))
        assert o.process_blockers(s,o.ps_rows(raw.replace(' 777 S',' 1042 S')))
    test('later birth distinguishes root PID reuse; reused numeric PGID remains conservative',reuse)
    def descendant(root,sp,s):
        prior=o.ps_rows(' 335 1 1042 S Mon Oct 12 15:25:00 2026 /NONHUMAN/child\n')
        current=o.ps_rows(' 335 1 900 S Mon Oct 12 15:25:00 2026 /NONHUMAN/child\n')
        assert o.process_blockers(s,current,prior)
    test('known descendant survives reparent and group change',descendant)
    test('malformed process birth rejected',lambda root,sp,s:reject(lambda:o.ps_rows('bad row'),'ambiguous'))
    def drift(root,sp,s):
        obs=observations(root,sp);Path(s['entries'][0]['route']['output_directory'],'ROOT-cli-events.jsonl').write_text('NONHUMAN changed')
        reject(lambda:o.prepare(sp,obs,[42],root/'p',synthetic=True),'capture bytes changed')
    test('raw event file drift rejected',drift)
    test('duplicate observation rejected',lambda root,sp,s:reject(lambda:o.prepare(sp,[(a:=observations(root,sp)[0]),a],[42],root/'p',synthetic=True),'two independent'))
    test('reverse observation order rejected',lambda root,sp,s:reject(lambda:o.prepare(sp,list(reversed(observations(root,sp))),[42],root/'p',synthetic=True),'times overlap'))
    def go(root,sp,s):
        Path(s['original_GO']['path']).write_text('NONHUMAN changed')
        reject(lambda:o.scope(sp,synthetic=True),'binding drift')
    test('original GO drift rejected',go)
    def route(root,sp,s):
        s['entries'][0]['route']['attempt_number']=2;sp.write_bytes(o.blob(s))
        reject(lambda:o.scope(sp,synthetic=True),'route mismatch')
    test('route/attempt mutation rejected',route)
    def conflict(root,sp,s):
        obs=observations(root,sp);Path(s['entries'][0]['receipt_destination']).write_text('{}')
        reject(lambda:o.prepare(sp,obs,[42],root/'p',synthetic=True),'receipt conflict')
    test('existing receipt cannot be overwritten',conflict)
    def later(root,sp,s):
        e=next(e for e in s['entries'] if key(e)==(51,1))
        d=Path(e['route']['selection_directory'])/'attempt-0002';d.mkdir();(d/'partial').write_text('NONHUMAN')
        reject(lambda:o.files_and_conflicts(s),'later attempt')
    key=o.key
    test('already used later attempt rejected',later)
    def completion(root,sp,s):
        (Path(s['entries'][0]['route']['output_directory'])/'ROOT-process-completion.json').write_text('{}')
        reject(lambda:o.files_and_conflicts(s),'completion appeared')
    test('genuine completion arrival requires separate reception',completion)
    def noauth(root,sp,s):
        pb=o.prepare(sp,observations(root,sp),[42],root/'p',synthetic=True)
        a=root/'empty-auth.json';o.put(a,{})
        reject(lambda:o.install(sp,pb,a,synthetic=True),'actual ROOT adoption')
    test('empty ROOT registration does not install',noauth)
    test('TOY cannot enter real branch',lambda root,sp,s:reject(lambda:o.scope(sp),'fixture/real'))
    test('subset outside 13 refused',lambda root,sp,s:reject(lambda:o.prepare(sp,observations(root,sp),[99],root/'p',synthetic=True),'outside fixed'))
    return dict(artifact_type='NONHUMAN_orphan_recovery_controls',real_campaign_reads=False,
                real_process_signals=0,real_launches=0,real_receipts_written=0,
                implementation=o.bind(o.__file__),N=len(results),passed_N=len(results),cases=results)

if __name__=='__main__':
    report=run()
    o.put(Path(__file__).parent/'controls.json',report)
    print(json.dumps({'N':report['N'],'passed_N':report['passed_N']}))

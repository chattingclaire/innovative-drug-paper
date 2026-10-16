"""ROOT may run this read-only process observer after reviewing its preparation seal."""
import argparse, json, time
from pathlib import Path
import terminal_common as c

def watch(output, interval):
    c.assert_preparation(); assert 0.2<=interval<=10
    out=Path(output).resolve(); assert out.is_relative_to(c.HERE/'observations') and not out.exists(); out.mkdir(parents=True)
    registry=c.load(c.H/'ROOT-actual-startup-process-registry-v2.json')
    known={(r['pid'],r['lstart']):r for r in registry['known_owned_process_identity_registry']}
    groups=set(registry['tracked_pgids']); sample_N=0
    # Startup registry is real observed history, not a substituted current live claim.
    old=c.old_evidence(); groups.update(old['tracked_pgids'])
    prior=c.load(old['prior_observation']['path'])
    for r in prior['owned_processes']:
        m=c.metadata(r) if 'command' in r else r
        known[(m['pid'],m['lstart'])]=m
    last_signature=None
    while True:
        actual_leases=c.leases(); lp={d['pid'] for _,d in actual_leases}
        assert all(d['controller_pid']==registry['controller_identity']['pid'] for _,d in actual_leases)
        groups.update(d['pgid'] for _,d in actual_leases)
        rows=c.ps_rows(); active=c.owned(rows,list(known.values()),groups,lp)
        for row in active:
            m=c.metadata(row); known[(m['pid'],m['lstart'])]=m; groups.add(m['pgid'])
        sample_N+=1; signature=([(r['pid'],r['lstart'],r['stat']) for r in active],len(actual_leases))
        doc={'at_utc':c.now(),'stage':'observing','observer':c.bind(__file__),'successor_preparation_seal':c.bind(c.HERE/'seal.json'),'startup_registry':c.bind(c.H/'ROOT-actual-startup-process-registry-v2.json'),'runtime_start':c.bind(c.H/'runtime/start.json'),'controller_identity':registry['controller_identity'],'owned_processes':[c.metadata(r) for r in active],'known_owned_process_identity_registry':sorted(known.values(),key=lambda x:(x['pid'],x['lstart'])),'tracked_pgids':sorted(groups),'all_lease_pids':sorted(lp),'lease_bindings':[b for b,_ in actual_leases],'sample_N':sample_N,'process_sampling_interval_seconds':interval,'independent_isolated_code_mode_host_path_seeded':True,'unrelated_desktop_host_excluded':True,'signals_sent_N':0,'model_calls':0,'new_controller_and_all_known_descendants_absent':not active,'historical_exit_codes_not_inferred':True,'sampling_scope':'stored ROOT startup identities + actual leases + observed descendant closure + exact isolated host/runtime path; no kernel omniscience claim'}
        if signature!=last_signature:
            c.save(out/f'observation-{sample_N:08d}.json',doc); last_signature=signature
        result_path=c.H/'runtime/result.json'
        if not active:
            # No result or an incomplete result is a real blocking state, not a timeout completion.
            assert result_path.exists(),'No runtime/result after all known processes absent; ROOT must review genuine run state'
            result=c.load(result_path)
            assert result.get('full_requested_continuation_complete') is True,'Actual new continuation is not complete'
            assert result.get('all_this_controller_futures_completed') is True and result['remaining_unselected_batch_ids']==[]
            doc.update(stage='terminal',runtime_result=c.bind(result_path))
            c.save(out/'observation.json',doc); return c.bind(out/'observation.json')
        time.sleep(interval)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True);p.add_argument('--interval',type=float,default=2)
    x=p.parse_args();print(json.dumps(watch(x.output,x.interval),ensure_ascii=False))

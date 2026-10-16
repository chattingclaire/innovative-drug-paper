"""Future read-only observations. ROOT alone performs separately authorized signals."""
import argparse
from common import *
def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['live','frozen','terminal'],required=True);p.add_argument('--prior');p.add_argument('--output',required=True);a=p.parse_args();doc=profile();manifest=verify_static(doc);prior=load(a.prior) if a.prior else None
 assert a.stage=='live' or prior,'Frozen/terminal observations require the preceding real observation'
 rows=processes();owned=relevant(rows,prior);controllers=[r for r in owned if 'recover-native-whole-batches-v4-root.py --mode remaining' in r['command']];state=history(manifest)
 out=Path(a.output).resolve();assert out.parent==H/'observations' and not out.exists();out.mkdir(parents=True)
 if a.stage=='live':assert len(controllers)==1,'Exactly one real original controller must be observed'
 if a.stage=='frozen':
  assert prior['stage']=='live' and len(controllers)==1 and controllers[0]['stat'].startswith('T'),'ROOT must first pause only the old controller; this entry never sends a signal'
  previous=prior['controller_identity'];assert all(controllers[0][k]==previous[k] for k in ('pid','lstart','command')),'Controller identity changed'
 final_slot_risk=last_slot_risk(state)
 if a.stage=='terminal':
  assert prior['stage']=='frozen' and prior['may_ROOT_terminate_frozen_controller'] is True,'Last-slot safety must have passed before ROOT termination'
  assert owned==[],'Old controller/CLI/known descendants or process groups still present; timeouts are not terminal evidence'
  assert not final_slot_risk,'Never migrate an uncompleted last technical slot'
  # Preserve real bytes at the only stable point, after all old writers are absent.
  for r in state:
   if r['selection']:exact(r['selection'])
   for s in r['slots']:
    if s['unknown_original_outcome']:s['preserved_unknown_slot_files']=[bind(p) for p in sorted(Path(s['path']).iterdir()) if p.is_file()]
 tracked=sorted(set((prior or {}).get('tracked_pgids',[]))|{r['pgid'] for r in owned})
 docout={'at_utc':now(),'stage':a.stage,'observer':bind(__file__),'prepared_seal':bind(H/'seal.json'),'campaign_manifest':bind(CAMPAIGN/'manifest.json'),'prior_observation':bind(a.prior) if a.prior else None,'controller_identity':controllers[0] if controllers else (prior or {}).get('controller_identity'),'owned_processes':owned,'tracked_pgids':tracked,'slot_history':state,'uncompleted_last_slot_batch_ids':final_slot_risk,'may_ROOT_terminate_frozen_controller':a.stage=='frozen' and not final_slot_risk,'resume_old_controller_and_wait_required':a.stage=='frozen' and bool(final_slot_risk),'old_controller_and_known_descendants_absent':a.stage=='terminal','historical_unknown_exit_codes_not_fabricated':True,'unknown_outcome_slots_consume_original_budget':True,'all_terminal_is_not_clean_exit_claim':True,'signals_sent_N':0,'model_calls_N':0}
 save(out/'observation.json',docout);print(json.dumps({'observation':bind(out/'observation.json'),'stage':a.stage,'controller':docout['controller_identity'],'last_slot_risk':final_slot_risk,'may_terminate':docout['may_ROOT_terminate_frozen_controller']},ensure_ascii=False))
if __name__=='__main__':main()

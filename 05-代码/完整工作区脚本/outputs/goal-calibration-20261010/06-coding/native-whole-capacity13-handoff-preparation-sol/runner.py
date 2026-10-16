"""Future capacity13 continuation, same v4 model request and finite existing slots."""
import argparse,concurrent.futures,os,threading,time
from common import *
STOP=threading.Event();WRITE=threading.Lock()
def authorize(path,doc):
 go=load(path);assert go['approval_actor']=='ROOT' and go['actual_execution_authorized'] is True and go['template_only'] is False
 assert go['prepared_seal']==bind(H/'seal.json') and go['capacity_sidecar']==bind(H/'capacity13-sidecar.json') and go['concurrency']==13
 terminal=go['terminal_observation'];exact(terminal);t=load(terminal['path']);assert t['stage']=='terminal' and t['old_controller_and_known_descendants_absent'] is True and t['owned_processes']==[] and t['uncompleted_last_slot_batch_ids']==[]
 frozen=load(t['prior_observation']['path']);exact(t['prior_observation']);assert frozen['stage']=='frozen' and frozen['may_ROOT_terminate_frozen_controller'] is True
 assert go['ROOT_attests_old_dispatch_permanently_closed'] is True and go['ROOT_attests_all_actual_old_children_terminal'] is True and go['unknown_historical_outcomes_not_clean_exits'] is True and go['same_recovery_budget_not_reset'] is True
 assert isinstance(go['actual_terminal_observation_and_operator_evidence'],list) and go['actual_terminal_observation_and_operator_evidence'] and go['capacity13_protocol_exception_acknowledged'] is True
 for evidence in go['actual_terminal_observation_and_operator_evidence']:exact(evidence)
 assert relevant(processes(),t)==[],'Old owned processes remain/restarted'
 current=history(load(CAMPAIGN/'manifest.json'));recorded=[dict(r,slots=[{k:v for k,v in s.items() if k!='preserved_unknown_slot_files'} for s in r['slots']]) for r in t['slot_history']];assert current==recorded,'Old artifact state changed after terminal observation'
 for r in t['slot_history']:
  for s in r['slots']:
   for b in s.get('preserved_unknown_slot_files',[]):exact(b)
 return go,t
def execute(go_path):
 doc=profile();manifest=verify_static(doc);go,t=authorize(go_path,doc)
 lock=(H/'execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 runtime=H/'runtime';assert not runtime.exists(),'This sealed handoff authorizes one actual continuation only';runtime.mkdir();(runtime/'receipts').mkdir();(runtime/'leases').mkdir()
 old=frozen_module(V4,'unchanged_frozen_v4_native_transport');guard=frozen_module(GUARD,'unchanged_frozen_native_strict_guard')
 old.CAPACITY=H/'capacity13-sidecar.json'
 def received(directory,number,unused_manifest):
  slot=directory/f'attempt-{number:04d}';rp=slot/'root-reception-v3.json';external=runtime/'receipts'/f'{directory.name}-a{number:02d}.json'
  receipt={'at_utc':now(),'run_id':manifest['run_id'],'batch_id':directory.name,'attempt':number,'assignment':bind(directory/'assignment.json'),'guard':bind(GUARD),'capacity_sidecar':bind(H/'capacity13-sidecar.json'),'transport_handoff_GO':bind(go_path),'reference_compared':False,'first_or_labels_modified':False}
  try:
   result=guard.verify(CAMPAIGN/'manifest.json',directory/'assignment.json',slot/'first.json');receipt.update(state='technical_valid_whole_batch',validation=result,first=result['first'],actor_seal=result['actor_seal'])
  except Exception as e:receipt.update(state='technical_invalid_whole_batch',error={'type':type(e).__name__,'message':str(e)})
  if rp.exists():
   original=load(rp)
   if original['state']=='technical_valid_whole_batch':assert receipt['state']=='technical_valid_whole_batch' and original['first']==receipt['first'] and original['actor_seal']==receipt['actor_seal'];return original,rp
   receipt['prior_original_receipt_preserved']=bind(rp);save(external,receipt);return receipt,external
  save(rp,receipt);return receipt,rp
 # Original attempt() calls this exact nonsemantic receiver; return shape retained.
 old.receive_completed=lambda d,n,m:received(d,n,m)[0]
 original_Popen=subprocess.Popen
 def tracked_Popen(argv,**kwargs):
  slot=Path(kwargs['cwd']);proc=original_Popen(argv,**kwargs)
  assert kwargs.get('start_new_session') is True
  save(runtime/'leases'/f'{slot.parent.name}-{slot.name}.json',{'at_utc':now(),'pid':proc.pid,'pgid':proc.pid,'pgid_basis':'actual Popen start_new_session=True; POSIX process group identity','slot':str(slot),'argv':argv,'actual_process_created':True,'controller_pid':os.getpid(),'same_original_v4_capture':True})
  return proc
 old.subprocess=types.SimpleNamespace(Popen=tracked_Popen,PIPE=subprocess.PIPE,TimeoutExpired=subprocess.TimeoutExpired)
 def batch(item):
  directory=Path(item['assignment']['path']).parent;selection=directory/'root-selection-v3.json'
  if selection.exists():return {'batch_id':directory.name,'state':'existing_selection_preserved','selection':bind(selection)}
  for n in range(1,4):
   if STOP.is_set() or old.STOP_NEW_DISPATCH.is_set() or (H/'STOP-NEW-DISPATCH').exists():return {'batch_id':directory.name,'state':'new_dispatch_stopped'}
   slot=directory/f'attempt-{n:04d}';files=list(slot.iterdir());completion=slot/'process-completion.json'
   if files and not completion.exists():continue # Real historical unknown/nonempty slot is consumed, never overwritten.
   if completion.exists():receipt,rp=received(directory,n,manifest)
   else:
    # Exclusive empty-slot claim remains external, then original dispatch/capture writes only this unused slot.
    save(runtime/'leases'/f'{directory.name}-a{n:02d}-claim.json',{'at_utc':now(),'batch_id':directory.name,'attempt':n,'slot':str(slot),'original_slot_was_empty':True,'same_three_attempt_budget':True})
    receipt=old.attempt(directory,n,manifest);rp=slot/'root-reception-v3.json'
    proc=load(completion);group=proc['pid'];residual=[r for r in processes() if r['pgid']==group]
    if residual:STOP.set();return {'batch_id':directory.name,'state':'owned_descendants_remain_after_leader_exit','processes':residual,'completion':bind(completion)}
   if receipt['state']=='technical_valid_whole_batch':
    chosen={'artifact_type':'earliest_technically_valid_whole_batch_transport_recovery','created_at_utc':now(),'batch_id':directory.name,'run_id':manifest['run_id'],'attempt':n,'assignment':item['assignment'],'first':receipt['first'],'reception':bind(rp),'scope':old.SCOPE,'original_valid_results_never_overwritten':True,'semantic_scores_not_selection_criteria':True,'cross_attempt_record_combination':False,'capacity13_handoff':bind(H/'capacity13-sidecar.json'),'same_recovery_budget_continued':True}
    save(selection,chosen);print(json.dumps({'batch':directory.name,'state':'accepted','record_N':len(item['source_ids']),'attempt':n}),flush=True);return chosen
  return {'batch_id':directory.name,'state':'three_original_recovery_slots_exhausted_no_fourth_attempt'}
 missing=[b for b in manifest['batches'] if not (Path(b['assignment']['path']).parent/'root-selection-v3.json').exists()]
 save(runtime/'start.json',{'at_utc':now(),'controller':bind(__file__),'parent_v4':bind(V4),'GO':bind(go_path),'terminal_observation':go['terminal_observation'],'capacity_sidecar':bind(H/'capacity13-sidecar.json'),'original_manifest':bind(CAMPAIGN/'manifest.json'),'actual_concurrency_cap':13,'missing_batch_ids':[b['batch_id'] for b in missing],'budget_reset':False,'model_prompt_argv_CWD_schema_unchanged':True})
 results=[];iterator=iter(missing)
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=13) as pool:
   active={}
   def fill():
    while len(active)<13 and not STOP.is_set() and not old.STOP_NEW_DISPATCH.is_set() and not (H/'STOP-NEW-DISPATCH').exists():
     b=next(iterator,None)
     if b is None:break
     active[pool.submit(batch,b)]=b
   fill()
   while active:
    done,_=concurrent.futures.wait(active,return_when=concurrent.futures.FIRST_COMPLETED)
    for future in done:
     b=active.pop(future)
     try:results.append(future.result())
     except Exception as e:STOP.set();results.append({'batch_id':b['batch_id'],'state':'controller_error_dispatch_stopped','error':repr(e)})
    fill()
 finally:
  # Snapshot is truthful even if dispatch stopped: it never hardcodes all_terminal from futures alone.
  tracked=dict(t,tracked_pgids=sorted(set(t['tracked_pgids'])|{load(p)['pgid'] for p in (runtime/'leases').glob('*.json') if 'pgid' in load(p)}));owned=relevant(processes(),tracked)
  remaining=[b['batch_id'] for b in manifest['batches'] if not (Path(b['assignment']['path']).parent/'root-selection-v3.json').exists()]
  save(runtime/'result.json',{'at_utc':now(),'results':results,'actual_concurrency_cap':13,'remaining_unselected_batch_ids':remaining,'owned_controller_CLI_descendants_present':owned,'tracked_pgids':tracked['tracked_pgids'],'all_this_controller_futures_completed':True,'snapshot_owned_children_absent':not owned,'full_requested_continuation_complete':not remaining and not owned,'old_v4_remains_transport_interrupted_not_complete':True,'budget_reset':False,'formal_validation_complete':False})
 return {'result':bind(runtime/'result.json'),'model_service_identity_independently_verified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['preflight','run'],required=True);p.add_argument('--go');a=p.parse_args()
 if a.mode=='preflight':doc=profile();m=verify_static(doc);print(json.dumps({'status':'prepared_not_started','original_batches':len(m['batches']),'original_records':m['source_N'],'future_capacity':13,'model_calls':0,'signals_sent':0}))
 else:assert a.go,'Actual ROOT GO required';print(json.dumps(execute(a.go),ensure_ascii=False))

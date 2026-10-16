"""Finalize only after all required actual original/replacement calls and provenance are complete."""
from pathlib import Path
import json,time,subprocess,sys
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent;OUT=HERE/'sealed-final-material-v3'
def main():
 plan=json.loads((OUT/'run_plan.json').read_text());old=Path(plan['original_v2_run_path']);part=Path(plan['affected_actual_run_path']);affected=set(plan['affected_original_batch_indices']);last=None
 while True:
  accepted=0;kept=0;replacement=0;complete_rows=0
  for e in plan['batch_sources']:
   sel=Path(e['actual_batch_path'])/'selection.json'
   if not sel.exists():continue
   d=json.loads(sel.read_text())
   if d['status']!='accepted_first_valid_actual_attempt':raise RuntimeError(f"Required actual batch exhausted retries: global {e['original_batch_index']}, actual {e['actual_batch_path']}; do not fill labels.")
   accepted+=1;complete_rows+=e['final_row_end_exclusive']-e['final_row_start0']
   if e['material_changed']:replacement+=1
   else:kept+=1
  progress={'status':'running_actual_selected_calls' if accepted<197 else 'actual_calls_complete_awaiting_seal','updated_at_UTC':datetime.now(timezone.utc).isoformat(),'source_material_version':'v3','selected_batch_count_complete':accepted,'expected_selected_batches':197,'preserved_v2_batches_complete':kept,'expected_preserved_v2_batches':195,'v3_whole_batch_replacements_complete':replacement,'expected_v3_whole_batch_replacements':2,'selected_row_count_complete':complete_rows,'expected_rows':4924,'all_4924_material_and_raw_reconstruction_not_declared_until_final_seal':True}
  (HERE/'actual_selected_progress_v3.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
  if accepted!=last:print(json.dumps({'final_v3_required_batches_complete':accepted,'expected':197}),flush=True);last=accepted
  os=old/'execution_summary.json';ps=part/'execution_summary.json'
  if os.exists() and ps.exists():
   od=json.loads(os.read_text());pd=json.loads(ps.read_text());assert pd['status']=='complete_actual_calls_structurally_valid','replacement calls incomplete'
   failed={json.loads(p.read_text())['batch'] for p in old.glob('batches/*/selection.json') if json.loads(p.read_text())['status']!='accepted_first_valid_actual_attempt'};assert failed<=affected,'unaffected original batch failed';assert accepted==197,'actual selected provenance is not complete';break
  time.sleep(15)
 subprocess.run([sys.executable,str(HERE/'verify_actual_execution_v30.py'),'--run',str(part)],check=True,capture_output=True,text=True)
 subprocess.run([sys.executable,str(HERE/'seal_composite_v3.py')],check=True)
 progress['status']='final_v3_actual_composite_and_bindings_complete';progress['updated_at_UTC']=datetime.now(timezone.utc).isoformat();(HERE/'actual_selected_progress_v3.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':'final_v3_actual_composite_and_bindings_complete'}),flush=True)
if __name__=='__main__':main()

"""Same-turn completion hook; waits for actual runs, never supplies missing outputs."""
from pathlib import Path
import json,time,subprocess,sys
HERE=Path(__file__).resolve().parent;RUN=HERE/'production-25-v30-v2'
def main():
 last=None
 while True:
  completed=RUN/'execution_summary.json'
  if completed.exists():
   d=json.loads(completed.read_text())
   if d['status']!='complete_actual_calls_structurally_valid':raise RuntimeError('Production is partial/failed: do not publish final labels or metrics.')
   break
  sels=[json.loads(p.read_text()) for p in RUN.glob('batches/*/selection.json')];bad=[s['batch'] for s in sels if s['status']!='accepted_first_valid_actual_attempt']
  if bad:raise RuntimeError(f'Batches exhausted identical-request retries, all attempts retained: {bad}')
  count=len(sels)
  if count!=last:print(json.dumps({'accepted_batches':count,'expected':197}),flush=True);last=count
  time.sleep(15)
 # New stability must complete before binding; no reuse of v29 results.
 while not (HERE/'stability_comparison_v30.json').exists():time.sleep(15)
 subprocess.run([sys.executable,str(HERE/'compare_stability_v30.py'),'--production',str(RUN/'all_predictions.jsonl')],check=True,capture_output=True,text=True)
 subprocess.run([sys.executable,str(HERE/'finalize_production_v30.py')],check=True)
 print(json.dumps({'status':'full_production_new_stability_and_final_bindings_complete'}),flush=True)
if __name__=='__main__':main()

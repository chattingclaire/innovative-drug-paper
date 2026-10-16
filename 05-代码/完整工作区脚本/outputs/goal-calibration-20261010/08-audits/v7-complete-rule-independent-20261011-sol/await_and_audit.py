"""Wait for both final execution and seal; no interim result is published."""
from pathlib import Path
import time,runpy,json
P=Path(__file__).resolve().parent;G=P.parents[1];RUN=G/'06-coding/rule-full4481-final-v7-root/run4481-first'
print(json.dumps({'status':'waiting_for_final_execution_and_seal','final_statistics_written':False}),flush=True)
while not ((RUN/'execution.json').exists() and (RUN/'seal.json').exists()):
 time.sleep(5)
print(json.dumps({'status':'complete_seal_detected_begin_independent_audit'}),flush=True)
runpy.run_path(str(P/'audit_complete.py'),run_name='__main__')

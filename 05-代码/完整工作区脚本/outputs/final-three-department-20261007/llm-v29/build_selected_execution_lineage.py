"""Bind every selected final row to actual raw model output and events."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE/'production-25-v29'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tool_count(p):
 n=0
 for line in p.read_text().splitlines():
  try:e=json.loads(line)
  except ValueError:continue
  s=json.dumps(e,ensure_ascii=False).lower()
  if any(x in s for x in ('web_search','web_fetch','tool_call','function_call')):n+=1
 return n
records=[]
for batch in sorted((RUN/'batches').glob('batch-*')):
 selected=batch/'no_retrieval_output.json' if (batch/'no_retrieval_output.json').exists() else batch/'repaired_output.json' if (batch/'repaired_output.json').exists() else batch/'raw_output.json'
 sources=[];kind='ordinary_first_raw'
 if selected.name=='no_retrieval_output.json':
  kind='whole_batch_no_retrieval_rerun';target=sha(selected);matches=[p for p in batch.glob('no-retrieval-rerun-*/raw_output.json') if sha(p)==target];assert len(matches)==1;raw=matches[0];base=raw.parent;sources=[{'role':'selected_whole_batch_raw','output':str(raw.relative_to(RUN)),'input':str((base/'input.json').relative_to(RUN)),'events':str((base/'events.jsonl').relative_to(RUN)),'metadata':str((base/'run_metadata.json').relative_to(RUN)),'output_sha256':sha(raw),'input_sha256':sha(base/'input.json'),'events_sha256':sha(base/'events.jsonl'),'tool_event_count':tool_count(base/'events.jsonl')}]
 elif selected.name=='repaired_output.json':
  rm=json.loads((batch/'repair_manifest.json').read_text())
  if rm['status']=='accepted_after_context_repair_model_rerun':
   kind='whole_batch_material_completion_rerun';base=batch/'repairs/full-batch-context-repair';sources=[{'role':'selected_whole_batch_raw','output':str((base/'raw_output.json').relative_to(RUN)),'input':str((base/'input.json').relative_to(RUN)),'events':str((base/'events.jsonl').relative_to(RUN)),'metadata':str((base/'run_metadata.json').relative_to(RUN)),'output_sha256':sha(base/'raw_output.json'),'input_sha256':sha(base/'input.json'),'events_sha256':sha(base/'events.jsonl'),'tool_event_count':tool_count(base/'events.jsonl')}]
  else:
   kind='first_raw_plus_isolated_model_row_reruns';sources=[{'role':'base_first_raw','output':str((batch/'raw_output.json').relative_to(RUN)),'input':str((batch/'input.json').relative_to(RUN)),'events':str((batch/'events.jsonl').relative_to(RUN)),'metadata':str((batch/'run_metadata.json').relative_to(RUN)),'output_sha256':sha(batch/'raw_output.json'),'input_sha256':sha(batch/'input.json'),'events_sha256':sha(batch/'events.jsonl'),'tool_event_count':tool_count(batch/'events.jsonl')}]
   for repair in sorted((batch/'repairs').glob('RECODE25-*')):
    meta=json.loads((repair/'run_metadata.json').read_text())
    if meta['status']=='accepted_repair_output':sources.append({'role':'selected_isolated_row_raw','id':meta['id'],'output':str((repair/'raw_output.json').relative_to(RUN)),'input':str((repair/'input.json').relative_to(RUN)),'events':str((repair/'events.jsonl').relative_to(RUN)),'metadata':str((repair/'run_metadata.json').relative_to(RUN)),'output_sha256':sha(repair/'raw_output.json'),'input_sha256':sha(repair/'input.json'),'events_sha256':sha(repair/'events.jsonl'),'tool_event_count':tool_count(repair/'events.jsonl')})
 else:
  sources=[{'role':'selected_first_raw','output':str((batch/'raw_output.json').relative_to(RUN)),'input':str((batch/'input.json').relative_to(RUN)),'events':str((batch/'events.jsonl').relative_to(RUN)),'metadata':str((batch/'run_metadata.json').relative_to(RUN)),'output_sha256':sha(batch/'raw_output.json'),'input_sha256':sha(batch/'input.json'),'events_sha256':sha(batch/'events.jsonl'),'tool_event_count':tool_count(batch/'events.jsonl')}]
 assert all(s['tool_event_count']==0 for s in sources),(batch.name,sources)
 records.append({'batch':batch.name,'selection_kind':kind,'selected_assembled_output':str(selected.relative_to(RUN)),'selected_assembled_output_sha256':sha(selected),'sources':sources,'excluded_history_preserved':(batch/'history-before-no-retrieval').exists()})
assert len(records)==197
out=RUN/'selected_execution_lineage.json';out.write_text(json.dumps({'status':'all_selected_rows_bound_to_actual_zero-tool-model_outputs','batch_count':197,'records':records},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'batches':197,'sha256':sha(out),'kinds':{k:sum(r['selection_kind']==k for r in records) for k in sorted({r['selection_kind'] for r in records})}},ensure_ascii=False))

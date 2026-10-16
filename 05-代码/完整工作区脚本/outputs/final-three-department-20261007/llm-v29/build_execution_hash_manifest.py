"""Hash every production first attempt and repair artifact for audit binding."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE/'production-25-v29'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for batch in sorted((RUN/'batches').glob('batch-*')):
 files={}
 for path in sorted(batch.rglob('*')):
  if path.is_file():files[str(path.relative_to(RUN))]=sha(path)
 meta=json.loads((batch/'run_metadata.json').read_text())
 selected='no_retrieval_output.json' if (batch/'no_retrieval_output.json').exists() else 'repaired_output.json' if (batch/'repaired_output.json').exists() else 'raw_output.json'
 records.append({'batch':batch.name,'first_attempt_status':meta['status'],'selected_output':selected,'repair_used':selected=='repaired_output.json','files':files})
assert len(records)==197
manifest={'status':'all_first_attempts_and_repairs_hashed','batch_count':197,'records':records}
out=RUN/'execution_artifact_hashes.json';out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
final=json.loads((RUN/'final_manifest.json').read_text());final['execution_artifact_hashes_sha256']=sha(out);final['stability_comparison_v2_sha256']=sha(HERE/'stability_comparison_v2.json');(RUN/'final_manifest.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n')
final=json.loads((RUN/'final_manifest.json').read_text());final['selected_execution_lineage_sha256']=sha(RUN/'selected_execution_lineage.json');(RUN/'final_manifest.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n')

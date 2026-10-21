import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE/'production-25-v29';IDS=['RECODE25-00932','RECODE25-01008','RECODE25-01241','RECODE25-01959','RECODE25-02158','RECODE25-02287','RECODE25-02914','RECODE25-04282'];BATCHES=[38,41,50,79,87,92,117,172]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=Path('/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区/原文补全/NHSA-2020用药办法-官方-正文.txt');records=[]
for rid,b in zip(IDS,BATCHES):
 batch=RUN/'batches'/f'batch-{b:04d}'
 if b==87:base=batch/'repairs/full-batch-context-repair'
 else:
  target=sha(batch/'no_retrieval_output.json');matches=[p.parent for p in batch.glob('no-retrieval-rerun-*/raw_output.json') if sha(p)==target];assert len(matches)==1;base=matches[0]
 records.append({'id':rid,'batch':b,'selected_input':str((base/'input.json').relative_to(RUN)),'selected_input_sha256':sha(base/'input.json'),'selected_output':str((base/'raw_output.json').relative_to(RUN)),'selected_output_sha256':sha(base/'raw_output.json'),'selected_events':str((base/'events.jsonl').relative_to(RUN)),'selected_events_sha256':sha(base/'events.jsonl')})
manifest={'status':'uniform_cross_reference_material_completion','source_path':str(source),'source_sha256':sha(source),'articles':[9,10],'override_ids':IDS,'records':records,'unit_texts_and_ids_unchanged':True,'labels_or_metrics_not_used_to_select_completion':True}
out=HERE/'material_completion_manifest.json';out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');final=json.loads((RUN/'final_manifest.json').read_text());final['material_completion_manifest_sha256']=sha(out);(RUN/'final_manifest.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n')

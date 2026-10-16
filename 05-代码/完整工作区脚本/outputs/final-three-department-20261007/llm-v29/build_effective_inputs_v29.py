"""Materialize the effective 4,924 inputs, including the one repair override."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE/'production-25-v29';BASE=HERE/'frozen_blind_inputs_v29.jsonl';SUP=HERE/'supplement_RECODE25-02158.json';OUT=HERE/'effective_blind_inputs_v29.jsonl'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
override_ids=['RECODE25-00932','RECODE25-01008','RECODE25-01241','RECODE25-01959','RECODE25-02158','RECODE25-02287','RECODE25-02914','RECODE25-04282']
template=json.loads(SUP.read_text());template['source_sha256']=sha(Path(template['source_path']));rows=[]
for row in map(json.loads,BASE.read_text().splitlines()):
 if row['id'] in override_ids:
  sup=json.loads(json.dumps(template,ensure_ascii=False));sup['id']=row['id'];row['contexts']['resolved_material_supplement']=sup
 rows.append(row)
OUT.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows));assert len(rows)==4924
prompt=HERE.parents[2]/'outputs/llm-v29-method-audit-20261005/完整系统提示词-v29.txt'
manifest={'status':'effective_full_input_materialized','n':4924,'base_input_sha256':sha(BASE),'effective_input_sha256':sha(OUT),'override_count':len(override_ids),'override_ids':override_ids,'override_source_path':template['source_path'],'override_source_sha256':template['source_sha256'],'override_template_payload_sha256':hashlib.sha256(json.dumps(template,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'system_prompt_changed_for_override':False,'system_prompt_sha256_before_override':sha(prompt),'system_prompt_sha256_after_override':sha(prompt),'production_batch_overrides':'Eight cross-reference units receive the same official Articles 9/10 context; affected batches were whole-batch model reruns, with first attempts preserved.'}
(HERE/'effective_input_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
final=json.loads((RUN/'final_manifest.json').read_text());final.pop('input_sha256',None);final['base_input_sha256']=sha(BASE);final['effective_input_sha256']=sha(OUT);final['effective_input_manifest_sha256']=sha(HERE/'effective_input_manifest.json');final['input_override_count']=len(override_ids);final['input_override_ids']=override_ids;final['system_prompt_sha256']=sha(prompt);(RUN/'final_manifest.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(manifest,ensure_ascii=False))

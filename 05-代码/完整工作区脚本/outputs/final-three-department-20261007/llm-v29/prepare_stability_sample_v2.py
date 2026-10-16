"""Freeze the valid 12x3 department sample from the frozen mapping."""
import datetime, hashlib, json, random
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
CLASS=ROOT/'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
INPUT=HERE/'frozen_blind_inputs_v29.jsonl'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
classification=json.loads(CLASS.read_text())
mapping={Path(row['original_file']).stem:row['analysis_group'] for row in classification['rows']}
groups={key:[] for key in ('NMPA','NHSA','NHC')}
for row in map(json.loads,INPUT.read_text().splitlines()):
 group=mapping[row['source_title']]
 if group in groups:groups[group].append(row)
rng=random.Random(20261007);selected=[];ids={}
for group,candidates in groups.items():
 picks=rng.sample(candidates,12);selected.extend(picks);ids[group]=[row['id'] for row in picks]
packet={'rows':selected};out=HERE/'stability_sample_36_v2.json';out.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
(HERE/'stability_sample_manifest_v2.json').write_text(json.dumps({'status':'frozen_valid_three_department_sample','frozen_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seed':20261007,'n_per_department':12,'n':36,'groups':['NMPA','NHSA','NHC'],'classification_path':str(CLASS),'classification_sha256':sha(CLASS),'input_sha256':sha(INPUT),'sample_sha256':sha(out),'selection_basis':'frozen analysis_group mapping only; labels/predictions/metrics not read','full_run_partial_outputs_used':False,'ids':ids},ensure_ascii=False,indent=2)+'\n')
(HERE/'stability_v1_exclusion.json').write_text(json.dumps({'status':'excluded_not_used','reason':'v1 grouped CDE as a separate prefix and omitted NHC; it does not satisfy 12x NMPA/NHSA/NHC design','preserve_raw_runs':True},ensure_ascii=False,indent=2)+'\n')

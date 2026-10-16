"""Second read-only output/NA audit, no statistics core import or CI recomputation."""
from pathlib import Path
from collections import Counter
import json,hashlib
D=Path(__file__).parent;C=D.parent/'rules-v36.2-development-complete-statistics';R=D.parents[1]
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=read(C/'output_freeze.json');assert all(sha(C/n)==h for n,h in freeze['files'].items())
records=read(C/'machine_reference_classification.json')['comparisons'];ac=read(C/'A_C_before_third_agreement.json')['comparisons'];att=read(C/'probability_attention_and_paired_department_differences.json')
rows=[]
def walk(obj,path):
 if isinstance(obj,dict):
  if {'low','high','defined_repetitions','undefined_repetitions'}<=obj.keys():
   a,b=obj['defined_repetitions'],obj['undefined_repetitions'];notrun='not_run_reason' in obj
   assert (a+b==0 if notrun else a+b==5000)
   assert (obj['low'] is None and obj['high'] is None) if a==0 else (obj['low'] is not None and obj['high'] is not None and obj['low']<=obj['high'])
   status='absent_sample_not_run' if notrun else 'all_undefined' if a==0 else 'partly_undefined' if b else 'all_defined'
   rows.append({'path':path,'status':status,'degenerate_defined_endpoints':a>0 and obj['low']==obj['high'],**obj})
  else:
   for k,v in obj.items():walk(v,path+'/'+k)
 elif isinstance(obj,list):
  for i,v in enumerate(obj):walk(v,path+'/'+str(i))
for name,obj in [('classification',records),('A_C',ac),('attention',att)]:walk(obj,'/'+name)
counts=dict(Counter(x['status'] for x in rows));deg=sum(x['degenerate_defined_endpoints'] for x in rows)
old=read(C/'complete_statistics_QA.json')['interval_audit'];assert len(rows)==old['checked_interval_n'];assert deg==old['defined_endpoint_degenerate_n'];assert counts['absent_sample_not_run']==old['absent_stratum_no_bootstrap_n']
assert sum(x['status']!='all_defined' for x in rows)==len(old['partly_or_wholly_undefined'])
pointNA=[]
for r in records+ac:
 for metric,item in r['metrics'].items():
  if item['estimate'] is None:pointNA.append({'component':r['component'],'group':r['group'],'weighting':r['weighting'],'method':r['method'],'reference':r['reference'],'dimension':r['dimension'],'metric':metric,'reason':r['undefined_point_reasons'][metric],'absent_sample':r.get('absent_stratum',False)})
# Original actual submission evidence and T-to-candidate lineage checks.
audit=read(D/'残余低值逐例审读.json');checked=0;Tn=0
for r in audit['cases']:
 for coder,item in r['A_C_T'].items():
  if 'original_submission' not in item:continue
  original=item['original_submission']
  if coder=='T':assert original['labels']==r['candidate']['labels'];Tn+=1
  def textleaves(obj):
   if isinstance(obj,str):yield obj
   elif isinstance(obj,dict):
    for value in obj.values():yield from textleaves(value)
   elif isinstance(obj,list):
    for value in obj:yield from textleaves(value)
  contexts=list(textleaves(r['material']['contexts']))
  for ev in original['evidence']:
   quote=ev['quote'];assert quote in r['material']['text'] if ev['source']=='unit' else any(quote in t for t in contexts),(r['id'],coder,ev)
   checked+=1
j={'all_checks_pass':True,'audit_scope':'independent output parsing and integer status recount only; no bootstrap rerun, no metric core import, no semantic adjudication','sealed_output_file_hash_count':len(freeze['files']),'sealed_output_files':freeze['files'],'frozen_complete_statistics_manifest':{'path':str(C/'output_freeze.json'),'sha256':sha(C/'output_freeze.json')},'interval_count':len(rows),'interval_status_counts':counts,'defined_endpoint_degenerate_count':deg,'point_NA_metric_count':len(pointNA),'point_NA_metric_count_excluding_absent_stratum':sum(not p['absent_sample'] for p in pointNA),'point_NA_comparison_row_n':len({tuple(p[k] for k in ['component','group','weighting','method','reference','dimension']) for p in pointNA}),'point_NA_records':pointNA,'interval_nonall_defined_records':[x for x in rows if x['status']!='all_defined'],'T_labels_match_actual_candidate_cases':Tn,'original_actual_evidence_literal_checks':checked,'count_match_sealed_internal_QA':True,'interpretation':'A degenerate interval or all-defined5000 replicates does not validate labels or remove development bias. NHC probability census factors1 and sparse/perfect classifications can yield zero width. Absent NHC challenge0/0 repeats denotes no attempted resampling, not5000 failures.'}
(D/'完整统计哈希与CI状态独立复核.json').write_text(json.dumps(j,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
(D/'output_freeze.json').write_text(json.dumps({'files':{p.name:sha(p) for p in D.iterdir() if p.is_file() and p.name!='output_freeze.json'}},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in j.items() if k not in ['sealed_output_files','point_NA_records','interval_nonall_defined_records']},ensure_ascii=False))

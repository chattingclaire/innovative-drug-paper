"""Compare frozen v2 stability runs without changing or selecting labels."""
import hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;DIMS=['S','E','Ec','I','F']
SAMPLE=HERE/'stability_sample_36_v2.json';PROD=HERE/'production-25-v29/all_predictions.jsonl';R1=HERE/'stability-v2/same-repeat/raw_output.json';R2=HERE/'stability-v2/same-repeat-2/raw_output.json';ORDER=HERE/'stability-v2/dimension-order-repeat/raw_output.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
 if p.suffix=='.jsonl':return {r['id']:r for r in map(json.loads,p.read_text().splitlines())}
 return {r['id']:r for r in json.loads(p.read_text())['rows']}
texts={r['id']:r['text'] for r in json.loads(SAMPLE.read_text())['rows']};ids=list(texts)
sources={'production_25_batch':rows(PROD),'same_repeat_1_36_batch':rows(R1),'same_repeat_2_36_batch':rows(R2),'dimension_order_repeat_36_batch':rows(ORDER)}
def kappa(a,b):
 n=len(a);po=sum(x==y for x,y in zip(a,b))/n;pa=sum(a)/n;pb=sum(b)/n;pe=pa*pb+(1-pa)*(1-pb)
 return None if pe==1 else (po-pe)/(1-pe)
def compare(left,right,identity):
 A=sources[left];B=sources[right];per={};dis=[]
 for d in DIMS:
  a=[A[i]['labels'][d] for i in ids];b=[B[i]['labels'][d] for i in ids];bad=[i for i,x,y in zip(ids,a,b) if x!=y]
  per[d]={'agreement':sum(x==y for x,y in zip(a,b))/len(ids),'kappa':kappa(a,b),'disagreement_ids':bad}
  for i in bad:dis.append({'id':i,'dimension':d,'left':A[i]['labels'][d],'right':B[i]['labels'][d],'text':texts[i]})
 return {'comparison_identity':identity,'left':left,'right':right,'n':len(ids),'per_dimension':per,'all_five_labels_exact_agreement':sum(A[i]['labels']==B[i]['labels'] for i in ids)/len(ids),'disagreements':dis}
result={'status':'descriptive_stability_complete_no_label_selection','sample_sha256':sha(SAMPLE),'n':36,'output_bindings':{k:sha(p) for k,p in {'production_25_batch':PROD,'same_repeat_1_36_batch':R1,'same_repeat_2_36_batch':R2,'dimension_order_repeat_36_batch':ORDER}.items()},'comparisons':[
 compare('same_repeat_1_36_batch','same_repeat_2_36_batch','strict_same_prompt_same_36_row_batch_repeat'),
 compare('same_repeat_1_36_batch','dimension_order_repeat_36_batch','equivalent_prompt_dimension_order_perturbation_same_36_row_batch'),
 compare('production_25_batch','same_repeat_1_36_batch','batch_composition_changed_recoding_difference_not_strict_repeat')],
 'interpretation_limits':['LLM repeat stability only; not human validity or inter-rater reliability.','No rerun was selected or discarded based on agreement.','Production comparison changes batch composition and is reported separately from strict repeat stability.']}
(HERE/'stability_comparison_v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

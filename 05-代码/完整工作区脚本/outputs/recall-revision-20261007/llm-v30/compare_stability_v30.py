"""Agreement of actual independent same-batch executions; no accuracy or human-validation claim."""
from pathlib import Path
import argparse,json,hashlib
HERE=Path(__file__).resolve().parent
DIMS=['S','E','Ec','I','F']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
def comparison(a,b,kind,inputs):
 assert [r['id'] for r in a]==[r['id'] for r in b]
 n=len(a);dims={};diff=[]
 for dim in DIMS:
  x=[r['labels'][dim] for r in a];y=[r['labels'][dim] for r in b];equal=sum(i==j for i,j in zip(x,y));po=equal/n;pa=sum(x)/n;pb=sum(y)/n;pe=pa*pb+(1-pa)*(1-pb);k=(po-pe)/(1-pe) if pe!=1 else None
  dims[dim]={'n':n,'agreement_n':equal,'agreement':po,'kappa':k,'kappa_undefined_reason':'both runs have no variation' if k is None else None,'first_positive_n':sum(x),'second_positive_n':sum(y),'four_table':{'both_one':sum(i==1 and j==1 for i,j in zip(x,y)),'first_one_second_zero':sum(i==1 and j==0 for i,j in zip(x,y)),'first_zero_second_one':sum(i==0 and j==1 for i,j in zip(x,y)),'both_zero':sum(i==0 and j==0 for i,j in zip(x,y))}}
  for r1,r2 in zip(a,b):
   if r1['labels'][dim]!=r2['labels'][dim]:diff.append({'id':r1['id'],'dimension':dim,'text':inputs[r1['id']]['text'],'first_label':r1['labels'][dim],'second_label':r2['labels'][dim],'first_reason':r1['dimension_reasons'][dim],'second_reason':r2['dimension_reasons'][dim],'not_adjudication':True})
 whole=sum(r1['labels']==r2['labels'] for r1,r2 in zip(a,b));return {'kind':kind,'n':n,'whole_five_label_agreement_n':whole,'whole_five_label_agreement':whole/n,'dimensions':dims,'disagreements':diff}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--production');a=ap.parse_args();sample=HERE/'stability-v30/same_batch_36.jsonl';inputs={r['id']:r for r in load(sample)};runs={name:HERE/f'stability-v30-{name}' for name in ['same-01','same-02','dimension-order-01']};pred={}
 for name,run in runs.items():
  summary=json.loads((run/'execution_summary.json').read_text());qa=json.loads((run/'actual_execution_reconstruction_QA.json').read_text());assert summary['status']=='complete_actual_calls_structurally_valid' and summary['n']==36 and summary['expected_batch_count']==1 and qa['status']=='passed_actual_execution_reconstruction';assert summary['input_sha256']==sha(sample);pred[name]=load(run/'all_predictions.jsonl');assert len(pred[name])==36
 p1=json.loads((runs['same-01']/'batches/batch-0001/selection.json').read_text());p2=json.loads((runs['same-02']/'batches/batch-0001/selection.json').read_text())
 m1=json.loads((runs['same-01']/p1['selected_relative_path']/'run_metadata.json').read_text());m2=json.loads((runs['same-02']/p2['selected_relative_path']/'run_metadata.json').read_text());assert m1['request_sha256']==m2['request_sha256'],'strict repeat requests differ'
 result={'status':'computed_from_new_actual_model_calls','method_version':'LLM-binary-v30','same_material_order_and_single_batch_of_36':True,'same_prompt_request_sha256_for_repeat':m1['request_sha256'],'same_repeat':comparison(pred['same-01'],pred['same-02'],'strict_same_prompt_same_material_same_order_same_single_batch',inputs),'dimension_order':comparison(pred['same-01'],pred['dimension-order-01'],'same_material_same_order_same_batch_only_dimension_evaluation_order_perturbed',inputs),'sources':{name:{'prediction_sha256':sha(run/'all_predictions.jsonl'),'plan_sha256':sha(run/'run_plan.json'),'execution_QA_sha256':sha(run/'actual_execution_reconstruction_QA.json')} for name,run in runs.items()},'not_accuracy_or_human_validation':True,'old_v29_results_not_used':True,'sample_size_limits':36,'model':'gpt-5.6-sol','reasoning_effort':'medium','temperature_provider_revision':'not_exposed'}
 if a.production:
  prod=Path(a.production);full={r['id']:r for r in load(prod)};sub=[full[r['id']] for r in pred['same-01']];result['production_batch_composition_changed']=comparison(pred['same-01'],sub,'NOT strict repeat: 25-row production batch composition differs from the 36-row stability batch',inputs);result['production_predictions_sha256']=sha(prod)
 # Compatibility fields preserve prior document-reader identities, using only new actual calls.
 def compatible(c,identity,left,right):
  per={d:{'agreement':c['dimensions'][d]['agreement'],'kappa':c['dimensions'][d]['kappa'],'disagreement_ids':[x['id'] for x in c['disagreements'] if x['dimension']==d],'four_table':c['dimensions'][d]['four_table']} for d in DIMS}
  return {'comparison_identity':identity,'left':left,'right':right,'n':c['n'],'per_dimension':per,'all_five_labels_exact_agreement':c['whole_five_label_agreement'],'disagreements':c['disagreements']}
 result['comparisons']=[compatible(result['same_repeat'],'strict_same_prompt_same_36_row_batch_repeat','same_repeat_1_36_batch','same_repeat_2_36_batch'),compatible(result['dimension_order'],'equivalent_prompt_dimension_order_perturbation_same_36_row_batch','same_repeat_1_36_batch','dimension_order_repeat_36_batch')]
 sourcekeys={'same-01':'same_repeat_1_36_batch','same-02':'same_repeat_2_36_batch','dimension-order-01':'dimension_order_repeat_36_batch'}
 result['actual_source_paths']={'sample':{'path':str(sample.resolve()),'sha256':sha(sample)}};result['output_bindings']={};result['sample_sha256']=sha(sample);result['n']=36
 for name,run in runs.items():
  selection=json.loads((run/'batches/batch-0001/selection.json').read_text());raw=run/selection['selected_relative_path']/'raw_output.json';key=sourcekeys[name]
  result['actual_source_paths'][key]={'predictions_path':str((run/'all_predictions.jsonl').resolve()),'predictions_sha256':sha(run/'all_predictions.jsonl'),'selected_actual_raw_output_path':str(raw.resolve()),'selected_actual_raw_output_sha256':sha(raw),'frozen_input_path':str((run/'frozen_input.jsonl').resolve()),'execution_QA_path':str((run/'actual_execution_reconstruction_QA.json').resolve()),'selected_attempt':selection['selected_relative_path']};result['output_bindings'][key]=sha(run/'all_predictions.jsonl')
 if a.production:
  result['comparisons'].append(compatible(comparison(sub,pred['same-01'],'NOT strict repeat: production batch composition differs',inputs),'batch_composition_changed_recoding_difference_not_strict_repeat','production_25_batch','same_repeat_1_36_batch'));result['actual_source_paths']['production_25_batch']={'predictions_path':str(prod.resolve()),'predictions_sha256':sha(prod)};result['output_bindings']['production_25_batch']=sha(prod)
 result['candidate']='03';result['interpretation_limits']=['LLM execution stability only; no human-validity or inter-rater-reliability claim.','No output selected or discarded based on agreement.','Undefined kappa from constant marginals is null, not 1.']
 (HERE/'stability_comparison_v30.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 out=HERE/'stability-v30/stability_comparison.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','same_repeat','dimension_order']},ensure_ascii=False))
if __name__=='__main__':main()

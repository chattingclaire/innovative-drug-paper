"""Read-only export of actual frozen statistics and all probability180 I/F disagreements.
No model, bootstrap, rule/label editing, adoption, or threshold-based selection.
"""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import hashlib,json,itertools
OUT=Path(__file__).resolve().parent;R=OUT.parents[1]
ST=R/'methods-20261008/rules-v36.2-plus-LLM03-reconciled-development-complete-statistics-v3'
FI=R/'methods-20261008/rules-v36.2-plus-LLM03-reconciled-development-findings-v3'
LLM='LLM-candidate03-single-unit-reconciled';RULE='rules-v36.2';DIMS=('S','E','Ec','I','F');METRICS=('kappa','precision','recall','f1')
bindings={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):
 p=Path(p).resolve();b={'path':str(p),'sha256':sha(p)};bindings[str(p)]=b;return b
def read(p):bind(p);return json.loads(Path(p).read_text())
def bound(b):assert sha(b['path'])==b['sha256'];return read(b['path'])
def rows(b):
 assert sha(b['path'])==b['sha256'];bind(b['path']);a=[json.loads(x) for x in Path(b['path']).read_text().splitlines() if x.strip()];assert len(a)==len({x['id'] for x in a});return {x['id']:x for x in a}
def save(n,x):
 p=OUT/n
 if p.exists():assert json.loads(p.read_text())==x;return
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def source_row(prov):
 b={'path':prov['result_path'],'sha256':prov['result_sha256']};obj=bound(b);hits=[x for x in obj['rows'] if x['id']==prov['blind_id']];assert len(hits)==1
 return {'binding':b,'blind_id':prov['blind_id'],'material_version':prov['material_version'],'actual_original_row':hits[0]}
def rank(z):
 vals={d:Fraction(str(z[d])) for d in DIMS};return [{'dimensions':[d for d in DIMS if vals[d]==v],'q':float(v)} for v in sorted(set(vals.values()),reverse=True)]
def fmt(x):return 'NA' if x is None else f'{x:.4f}'

def main():
 for directory in (ST,FI):
  seal=read(directory/'output_freeze.json')
  for name,digest in seal['files'].items():assert sha(directory/name)==digest
 dev=read(R/'methods-20261008/candidate03-reconciled-statistics-preparation-v3/actual-input-bindings-v3/rules-v36.2-plus-LLM03-reconciled-development-bindings-v3.json')
 manifest=bound(dev['reference_manifest']);design=bound(manifest['sampling_design']);sample={x['original_id']:x for x in design['sample']};prob={r for r,x in sample.items() if x['component']=='probability_canonical'};assert len(prob)==180
 stats=read(ST/'machine_reference_classification.json');AC=read(ST/'A_C_before_third_agreement.json');attention=read(ST/'probability_attention_and_paired_department_differences.json');find=read(FI/'完整定义构成核查.json');qa=read(ST/'complete_statistics_QA.json');NA=read(ST/'NA_and_interval_status.json')
 core=[x for x in stats['comparisons'] if x['component']=='probability_canonical' and x['group']=='ALL' and x['weighting']=='eligible_design_weighted'];assert len(core)==30
 ac=[x for x in AC['comparisons'] if x['component']=='probability_canonical' and x['group']=='ALL' and x['weighting']=='eligible_design_weighted'];assert len(ac)==5
 baseline=read(R/'statistics/final-v14/machine_reference_classification.json');keys=('component','group','weighting','reference','dimension')
 oldindex={(x['method'],)+tuple(x[k] for k in keys):x for x in baseline['comparisons']};changes=[]
 for row in stats['comparisons']:
  old_method='rules' if row['method']==RULE else 'LLM';old=oldindex.get((old_method,)+tuple(row[k] for k in keys))
  for metric in METRICS:
   newv=row['metrics'][metric]['estimate'];oldv=old['metrics'][metric]['estimate'] if old else None
   delta=None if old is None or oldv is None or newv is None else newv-oldv
   status=('no_comparable_baseline_row' if old is None else 'both_NA' if oldv is None and newv is None else 'baseline_NA_now_defined' if oldv is None else 'now_NA' if newv is None else 'unchanged' if abs(delta)<1e-12 else 'higher' if delta>0 else 'lower')
   changes.append({**{k:row[k] for k in keys},'method':row['method'],'baseline_method':'rules-v33' if old_method=='rules' else 'LLM-v32-candidate02','metric':metric,'baseline_estimate':oldv,'new_estimate':newv,'difference':delta,'numerical_change':status,'new_raw_confusion':row['raw_confusion'],'baseline_raw_confusion':old['raw_confusion'] if old else None})
 save('全部新旧点值差异.json',{'scope':'All360 current comparisons x4 metrics, same-v14 A/C/candidate baseline where original row exists; all higher/lower/unchanged/NA included. Numerical change is not a pass threshold.','rows':changes,'counts':dict(Counter(x['numerical_change'] for x in changes))})
 ranks=[]
 for x in attention['profiles']:
  if x['weighting']!='eligible_design_weighted':continue
  q={d:x['dimensions'][d]['attention_share'] for d in DIMS};ranks.append({'method':x['method'],'group':x['group'],'scope':'same180 remaining canonical frame; not full4481','n':x['complete_support_n'],'q':q,'rank':rank(q),'q_sum':sum(q.values())})
 full=[]
 for method,entry in find['primary_full4481'].items():
  for group,groupdata in entry['departments'].items():full.append({'method':method,'group':group,**groupdata['profile'],'Ec_F':next(x for x in groupdata['all10_pairs'] if (x['dimension_a'],x['dimension_b'])==('Ec','F'))})
 fullindex={(x['method'],x['group']):x for x in full};directions=[]
 for g1,g2 in itertools.combinations(('NMPA','NHSA','NHC'),2):
  for dim in DIMS:
   diffs={method:Fraction(int(fullindex[method,g1]['coding_count'][dim]),int(fullindex[method,g1]['five_dimension_coding_count']))-Fraction(int(fullindex[method,g2]['coding_count'][dim]),int(fullindex[method,g2]['five_dimension_coding_count'])) for method in (RULE,LLM)}
   signs={k:(v>0)-(v<0) for k,v in diffs.items()};directions.append({'department_one':g1,'department_two':g2,'dimension':dim,'exact_q_difference':{k:str(v) for k,v in diffs.items()},'signs':signs,'same_direction':signs[RULE]==signs[LLM]})
 flips=[]
 for kind in ('definition6','composition56'):
  for scenario in find[kind]:
   for method,entry in scenario['methods'].items():
    if kind=='definition6':entry=entry['full4481']
    for variable,item in entry['contrasts'].items():
     primary=find['primary_full4481'][method]['contrasts'][variable]['NHSA_minus_NHC'];actual=item['NHSA_minus_NHC']
     status='NA' if actual is None else 'same' if (actual>0)-(actual<0)==(primary>0)-(primary<0) else 'direction_change'
     if status!='same':flips.append({'kind':kind,'scenario':scenario['scenario'],'omitted_policy_entry':scenario.get('omitted_policy_entry'),'method':method,'variable':variable,'primary_NHSA_minus_NHC':primary,'actual_NHSA_minus_NHC':actual,'status':status})
 save('同180排序与全量敏感性摘要.json',{'same180_all_five_methods':ranks,'three_main_methods':['candidate',RULE,LLM],'full4481':full,'full15_direction_comparisons':directions,'full15_same_direction_n':sum(x['same_direction'] for x in directions),'all6_and56_direction_summary':find['summary'],'all_primary_direction_flips_or_NA':flips,'scope_note':'Candidate/rules/LLM same180 rankings are development diagnostics on a remaining canonical frame; A/C included without substitution. Full4481 sensitivities separate. Conditional proportions and OR are descriptive/marginal-rate dependent, not causal mechanisms.'})
 # All I/F disagreements against any of A/C/candidate, with exact rows and untouched reasons.
 refs={k:rows(manifest['references'][k]) for k in ('A','C')};refs['candidate']=rows(dev['existing_candidate_reference']);pred=rows(dev['methods'][LLM]['output']);source=rows(manifest['material']['llm_inputs']);audit=read(ST/'reference_binding_QA.json');T=audit['T']['provenance'];lineage=rows(bound(dev['methods'][LLM]['execution_adapter'])['row_provenance'])
 cases=[];summary=[]
 for dim in ('I','F'):
  for ref in ('A','C','candidate'):
   fn=sorted(r for r in prob if pred[r]['labels'][dim]==0 and refs[ref][r]['labels'][dim]==1);fp=sorted(r for r in prob if pred[r]['labels'][dim]==1 and refs[ref][r]['labels'][dim]==0)
   stat=next(x for x in core if x['method']==LLM and x['reference']==ref and x['dimension']==dim)
   assert len(fn)==stat['raw_confusion']['FN'] and len(fp)==stat['raw_confusion']['FP']
   summary.append({'dimension':dim,'reference':ref,'FN_ids':fn,'FP_ids':fp,'raw_confusion':stat['raw_confusion'],'design_weighted_metrics':{k:stat['metrics'][k] for k in METRICS}})
 selected=sorted({rid for x in summary for key in ('FN_ids','FP_ids') for rid in x[key]})
 for rid in selected:
  third=None
  if rid in T:third={'provenance':T[rid],'first_original_submission':source_row(T[rid]['first']),'effective_original_submission':source_row(T[rid]['effective'])}
  originals={coder:{'first':source_row(refs[coder][rid]['annotation_provenance']['first']),'effective':source_row(refs[coder][rid]['annotation_provenance']['effective'])} for coder in ('A','C')}
  cases.append({'id':rid,'sampling':sample[rid],'current_v14_original_text_and_complete_supplied_context':source[rid],'LLM_actual_full_five_dimension_row':pred[rid],'LLM_actual_execution_row_provenance':lineage[rid],'A_effective_full_row':refs['A'][rid],'C_effective_full_row':refs['C'][rid],'A_C_actual_original_submission_rows':originals,'T_original_submission':third,'T_status':'reviewed_original_and_effective_retained' if third else 'not_reviewed_NO_T_label_invented','candidate_reference_row':refs['candidate'][rid],'disagreement_flags':{dim:{ref:('FP' if pred[rid]['labels'][dim] else 'FN') if pred[rid]['labels'][dim]!=refs[ref][rid]['labels'][dim] else 'agree' for ref in ('A','C','candidate')} for dim in ('I','F')}})
 save('同180_LLM创新性公平性全部分歧原行.json',{'status':'ACTUAL_FULL_ROWS_EXPORTED_NO_RECODING','scope':'Union of I/F disagreements against any frozen A/C/candidate reference on same probability180; all such cases retained. T absent is null. Original first/effective submissions preserved.','reference_identity':'A/C/T are AI reviewers, including declared replacement sessions; no real-human validation claimed.','case_n':len(cases),'summaries':summary,'cases':cases})
 md=['# 同180 LLM 创新性/公平性分歧原行','','仅导出实际分歧，未修改原标签或以分数重选结果。完整五维原行、首次/有效 A/C/T 判读及全部给定语境见同名 JSON。T 未覆盖时保留未评审。','', '|维度|参照|TP/FP/FN/TN|设计加权κ|P|R|F1|','|---|---|---|---:|---:|---:|---:|']
 for x in summary:md.append('|'+ '|'.join([x['dimension'],x['reference'],'/'.join(str(x['raw_confusion'][k]) for k in ('TP','FP','FN','TN'))]+[fmt(x['design_weighted_metrics'][k]['estimate']) for k in METRICS])+'|')
 for x in cases:
  rid=x['id'];t=x['T_original_submission'];labs={k:x[k+'_effective_full_row']['labels'] for k in ('A','C')};labs['T']=t['effective_original_submission']['actual_original_row']['labels'] if t else None;labs['candidate']=x['candidate_reference_row']['labels'];labs['LLM03']=x['LLM_actual_full_five_dimension_row']['labels']
  md+=['',f"## {rid} · {x['sampling']['group']}",'',x['current_v14_original_text_and_complete_supplied_context']['text'],'','|判读|S|E|Ec|I|F|','|---|---:|---:|---:|---:|---:|']
  for k,z in labs.items():md.append('|'+k+'|'+'|'.join('未评审' if z is None else str(z[d]) for d in DIMS)+'|')
  md+=['','LLM 原理由（逐项原样，未重新解释）：',json.dumps({d:x['LLM_actual_full_five_dimension_row']['dimension_reasons'][d] for d in ('I','F')},ensure_ascii=False),'','给定语境：',json.dumps(x['current_v14_original_text_and_complete_supplied_context']['contexts'],ensure_ascii=False)]
 (OUT/'同180_LLM创新性公平性全部分歧原行.md').write_text('\n'.join(md)+'\n')
 save('实际统计交付摘要.json',{'status':'COMPLETE_ACTUAL_DEVELOPMENT_STATISTICS_AND_FINDINGS_QA_PASS','all240_exposed_development':True,'formal_adoption':False,'independent_human_validation':False,'bindings':list(bindings.values()),'counts':{k:v for k,v in qa.items() if k!='replication_factor_audits'},'core_probability180_designweighted_machine':core,'AC_before_third_probability180_designweighted':ac,'all_point_NA_rows':NA['point_NA'],'I_F_export_case_n':len(cases),'all_new_old_metric_change_counts':dict(Counter(x['numerical_change'] for x in changes)),'full15_direction_same_n':sum(x['same_direction'] for x in directions),'execution_failures_preserved':['v2 sealer dual-ID reader exit2','v3 initial bundled Python import jsonschema failure exit1; original Python3.14 rerun exit0'],'runtime':'Python3.14.4 / NumPy2.4.2 / jsonschema4.26.0; command and real failures retained in prep-v3 actual-execution-logs-v3','stability_note':'This statistical pipeline did not measure stability. A separately actually run03 stability binding is reported by execution agent and is not borrowed from02.'})
 save('output_freeze.json',{'source_binding_sha256':sha(R/'methods-20261008/candidate03-reconciled-statistics-preparation-v3/actual-input-bindings-v3/rules-v36.2-plus-LLM03-reconciled-development-bindings-v3.json'),'script':bind(__file__),'files':{p.name:sha(p) for p in OUT.iterdir() if p.is_file()}})
 print(json.dumps({'status':'DELIVERY_AND_ALL_IF_CASES_EXPORTED','case_n':len(cases),'I_F_by_ref':[{k:x[k] for k in ['dimension','reference','FN_ids','FP_ids']} for x in summary],'core_kappa':{m:{ref:{x['dimension']:x['metrics']['kappa']['estimate'] for x in core if x['method']==m and x['reference']==ref} for ref in ('A','C','candidate')} for m in (RULE,LLM)},'full15_same_direction_n':sum(x['same_direction'] for x in directions),'all_delta_counts':dict(Counter(x['numerical_change'] for x in changes)),'freeze':bind(OUT/'output_freeze.json')},ensure_ascii=False))
if __name__=='__main__':main()

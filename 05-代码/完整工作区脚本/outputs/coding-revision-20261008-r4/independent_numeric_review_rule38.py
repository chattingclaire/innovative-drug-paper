"""Reaggregate numeric machine findings without importing project statistics.

Only aggregate numbers are saved. Reserved IDs/text/per-unit predictions and
human reference files are never displayed. All transformations are analytical
views; this does not change any classifier output or manuscript.
"""
from pathlib import Path
from fractions import Fraction as Q
from itertools import combinations
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib,json,math
import numpy as np

ROOT=Path(__file__).resolve().parents[2];R3=ROOT/'outputs/coding-revision-20261007-r3';R4=Path(__file__).resolve().parent
AUTHOR=R4/'rules38-LLM03-synchronized-findings';OUT=R4/'rules38-findings-independent-numeric-review'
DIMS=('S','E','Ec','I','F');GROUPS=('NMPA','NHSA','NHC');PAIRS=list(combinations(DIMS,2));CELLS=('both_n','a_only_n','b_only_n','neither_n')
RULE='rules-v38-development';LLM='LLM-candidate03-single-unit-reconciled';B=5000;BASE_SEED=2026100731
checks=Counter();failures=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def jl(p):
 rows=[json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()];d={r['id']:r for r in rows};assert len(rows)==len(d)==4924;return d
def check(a,b,path,kind='field'):
 checks[kind]+=1
 if path.endswith(('.zero_a_clusters_excluded','.zero_b_clusters_excluded')) and isinstance(a,list) and isinstance(b,list):a,b=sorted(a),sorted(b)
 if isinstance(a,dict):
  good=isinstance(b,dict) and set(a)<=set(b)
  if good:
   for k,v in a.items():check(v,b[k],path+'.'+str(k),kind)
   return
 elif isinstance(a,list):
  good=isinstance(b,list) and len(a)==len(b)
  if good:
   for i,(v,w) in enumerate(zip(a,b)):check(v,w,path+'['+str(i)+']',kind)
   return
 elif a is None:good=b is None
 elif isinstance(a,(int,float,Q)) and not isinstance(a,bool):good=isinstance(b,(int,float)) and not isinstance(b,bool) and math.isclose(float(a),b,rel_tol=1e-12,abs_tol=1e-12)
 else:good=a==b
 if not good and len(failures)<100:failures.append({'path':path,'expected':float(a) if isinstance(a,Q) else a if not isinstance(a,(dict,list)) else '<shape>','actual':b if not isinstance(b,(dict,list)) else '<shape>'})
def div(a,b):return Q(a,b) if b else None
def avg(xs):return sum(xs,Q(0))/len(xs) if xs else None
def ranking(q):return {d:1+sum(float(v)>float(q[d])+1e-12 for v in q.values()) if q[d] is not None else None for d in DIMS}
def pair_from_cells(z,a,b,cell_type):
 n11,n10,n01,n00=z;n=sum(z);na=n11+n10;nb=n11+n01
 return {'dimension_a':a,'dimension_b':b,'cell_type':cell_type,**dict(zip(CELLS,z)),'n_or_probability_mass':n,'a_positive':na,'b_positive':nb,'p_b_given_a':div(n11,na),'p_a_given_b':div(n11,nb),'a_base':div(na,n),'b_base':div(nb,n),'p_b_given_non_a':div(n01,n01+n00),'p_a_given_non_b':div(n10,n10+n00),'OR':div(n11*n00,n10*n01),'OR_NA':not bool(n10*n01),'OR_exact':str(div(n11*n00,n10*n01)) if n10*n01 else None,'both_unit_fraction':div(n11,n)}
def raw_profile(labels,ids):
 total={d:sum(labels[r][j] for r in ids) for j,d in enumerate(DIMS)};den=sum(total.values());q={d:div(total[d],den) for d in DIMS}
 return {'unit_n':len(ids),'five_dimension_coding_count':den,'coding_count':total,'attention_share':q,'coverage':{d:div(total[d],len(ids)) for d in DIMS},'within_department_rank':ranking(q)}
def raw_pair(labels,ids,a,b):
 i,j=DIMS.index(a),DIMS.index(b);z=[0,0,0,0]
 for r in ids:z[2*(1-labels[r][i])+(1-labels[r][j])]+=1
 # Above order is11,10,01,00.
 return {**pair_from_cells(z,a,b,'raw_counts'),'unit_n':len(ids)}
def clusters(ids,key):
 out=defaultdict(list)
 for r in ids:out[stems[r] if key=='policy_file' else metadata[stems[r]]['policy_series']].append(r)
 return dict(out)
def profile(labels,ids,key=None):
 raw=raw_profile(labels,ids)
 if key is None:return raw
 cl=clusters(ids,key);p={n:raw_profile(labels,rs) for n,rs in cl.items()};defined={n:v for n,v in p.items() if v['five_dimension_coding_count']}
 q={d:avg([v['attention_share'][d] for v in defined.values()]) for d in DIMS}
 return {'unit_n':len(ids),'equal_cluster_n':len(cl),'defined_cluster_n':len(defined),'zero_hit_cluster_names_excluded_from_average':sorted(set(cl)-set(defined)),'attention_share':q,'within_department_rank':ranking(q),'coverage':{d:avg([v['coverage'][d] for v in p.values()]) for d in DIMS},'raw_unweighted_profile_for_audit':raw}
def pair(labels,ids,a,b,key=None):
 if key is None:return raw_pair(labels,ids,a,b)
 cl=clusters(ids,key);p={n:raw_pair(labels,rs,a,b) for n,rs in cl.items()};n=len(p)
 za=[v['p_b_given_a'] for v in p.values() if v['p_b_given_a'] is not None];zb=[v['p_a_given_b'] for v in p.values() if v['p_a_given_b'] is not None]
 mix=[avg([Q(v[k],v['unit_n']) for v in p.values()]) if n else Q(0) for k in CELLS];mixed=pair_from_cells(mix,a,b,'equal_cluster_mean_cell_probabilities')
 return {'dimension_a':a,'dimension_b':b,'unit_n':len(ids),'cell_type':'cluster_conditionals_mean; not pooled4cellOR','equal_cluster_n':n,'p_b_given_a':avg(za),'p_a_given_b':avg(zb),'defined_a_clusters':len(za),'defined_b_clusters':len(zb),'zero_a_clusters_excluded':sorted(n for n,v in p.items() if v['p_b_given_a'] is None),'zero_b_clusters_excluded':sorted(n for n,v in p.items() if v['p_a_given_b'] is None),'cluster_counts':p,'equal_cluster_cell_mixture':mixed,'OR':mixed['OR']}
def departments(labels,scope,key=None):return {g:{'profile':profile(labels,scope[g],key),'all10_pairs':[pair(labels,scope[g],a,b,key) for a,b in PAIRS]} for g in GROUPS}
def contrasts(deps):
 h,n=deps['NHSA'],deps['NHC'];hp=next(x for x in h['all10_pairs'] if (x['dimension_a'],x['dimension_b'])==('Ec','F'));npair=next(x for x in n['all10_pairs'] if (x['dimension_a'],x['dimension_b'])==('Ec','F'))
 vals={'P_F_given_Ec':(hp['p_b_given_a'],npair['p_b_given_a']),'P_Ec_given_F':(hp['p_a_given_b'],npair['p_a_given_b']),'OR':(hp['OR'],npair['OR'])}
 for kind in ('attention_share','coverage'):
  for d in DIMS:vals[kind+'_'+d]=(h['profile'][kind][d],n['profile'][kind][d])
 return {k:{'NHSA':a,'NHC':b,'NHSA_minus_NHC':a-b if a is not None and b is not None else None} for k,(a,b) in vals.items()}
def data(labels,scope,key=None):
 dep=departments(labels,scope,key);return {'departments':dep,'contrasts':contrasts(dep)}
def clean(x):
 if isinstance(x,Q):return {'fraction':str(x),'decimal':float(x)}
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
 if isinstance(x,list):return [clean(v) for v in x]
 return x
def point_compare(expected,target,path):check(expected,target,path)

def main():
 global stems,metadata
 assert not OUT.exists(),'Never overwrite an independent review'
 manifest_path=R3/'statistics/final_bindings_v14_CONFIRMED_r3.json';manifest=read(manifest_path)
 bindings={manifest_path:'46582af989d0473655b71ba38f174c2043794b8da9833bca9940aa0cf62c71cd'}
 for b in [manifest['material']['rule_inputs'],manifest['metadata'],manifest['sampling_design']]:bindings[Path(b['path'])]=b['sha256']
 rule_path=R4/'rules-v38-shadow-full-v14/all_predictions_material_v14_shadow.jsonl';llm_path=R3/'llm-candidate03-development/full-corpus-candidate03-material-v14-single-unit-reconciled-development/all_predictions.jsonl'
 old36=R3/'rules-v36.2-development/all_predictions_material_v14.jsonl';old37=R4/'rules-v37.2-shadow-full-v14/all_predictions_material_v14_shadow.jsonl'
 bindings.update({rule_path:'084143062fcb7fbf0e006c5618dbfc5e8b3a80f659760ff767a2c5645acc1cf6',llm_path:'29c36d745357872b05311f0456bd823842f312e00de892634a3e654bc318750e',old36:'105d10d7f441ed2c609911aa1f02bcaa4fc695acea35c6164750930a3021cc2b',old37:'9c699125ed10170dbf8f570ebb8e86a331a89737ac4c7022453afcfba2edaacf'})
 findings=read(AUTHOR/'完整定义构成核查.json');attention=read(AUTHOR/'全量注意力与配对文件构成区间.json')
 bindings[AUTHOR/'完整定义构成核查.json']='6d66e26bcc4a0bfd395fcf5ed2641d61738ac4dae759f53177f4defe00886dc1';bindings[AUTHOR/'全量注意力与配对文件构成区间.json']='a7f47f30bcaaf4d8431ef04903e45a38169c246d57d9b6e64a3e055296406c87'
 for code in findings['provenance']['statistical_code'].values():bindings[Path(code['path'])]=code['sha256']
 for p,h in bindings.items():check(h,sha(p),str(p),'binding')
 assert not failures,'Binding failure before computation'
 source=jl(manifest['material']['rule_inputs']['path']);metadata={Path(x['original_file']).stem:x for x in read(manifest['metadata']['path'])['rows']};stems={r:x['input']['original_file_stem'] for r,x in source.items()};groups={r:metadata[stems[r]]['analysis_group'] for r in source};sources={r:x['input'].get('unit_source') or x['input']['source'] for r,x in source.items()}
 check({'NMPA':1848,'NHSA':2100,'NHC':533,'GOV':443},dict(Counter(groups.values())),'group_sizes','scope')
 sample={r['original_id']:r for r in read(manifest['sampling_design']['path'])['sample']};check(240,len(sample),'old_sample_n','scope')
 allids={g:sorted(r for r in source if groups[r]==g) for g in GROUPS};pids={g:sorted(r for r,x in sample.items() if x['component']=='probability_canonical' and x['group']==g) for g in GROUPS}
 check([60,60,60],[len(pids[g]) for g in GROUPS],'same180_by_group','scope')
 rows={RULE:jl(rule_path),LLM:jl(llm_path)};labels={}
 for name,rs in rows.items():
  assert rs.keys()==source.keys();labels[name]={r:tuple(rs[r].get('prediction',rs[r])['labels'][d] for d in DIMS) for r in rs}
  for v in labels[name].values():check(True,all(type(z) is int and z in (0,1) for z in v),'label_shape/'+name,'label_shape')
 fields=('labels','innovation_subtypes','fairness_subtypes','safety_quality_basis','safety_subtypes','innovation_subtype_status','innovation_unclassified_evidence')
 old240={}
 for name,path in [('v36.2',old36),('v37.2',old37)]:
  previous=jl(path);n=sum(any(previous[r]['prediction'].get(f)!=rows[RULE][r]['prediction'].get(f) for f in fields) for r in sample)
  check(0,n,'old240_changes_vs_'+name,'old240');old240[name]={'n':240,'changed_machine_label_or_source_subtype_units':n,'fields':list(fields)}
 primary={};small={}
 for name,y in labels.items():
  primary[name]=data(y,allids);small[name]=data(y,pids)
  point_compare(primary[name],findings['primary_full4481'][name],'primary/'+name)
  point_compare(small[name],findings['same180_primary'][name],'same180_machine/'+name)
  short='rules' if name==RULE else 'LLM'
  for g in GROUPS:
   check({k:v for k,v in primary[name]['departments'][g]['profile'].items() if k in attention['primary'][short][g]},attention['primary'][short][g],'attention_primary/'+short+'/'+g)
 defs=('primary','exclude_quality_only_S','exclude_qualification_only_I','exclude_clinical_management_only_F','exclude_dimension_information_only_F','retain_access_affordability_F')
 check(list(defs),[x['scenario'] for x in findings['definition6']],'definition_names','scenario')
 computed_defs=[];removal_aggregate={}
 for sc,actual in zip(defs,findings['definition6']):
  current={}
  for name,rs in rows.items():
   derived={r:list(v) for r,v in labels[name].items()};removed=[]
   for r,row in rs.items():
    x=row.get('prediction',row);it=set(x.get('innovation_subtypes',[]));ft=set(x.get('fairness_subtypes',[]));drop=None
    if sc=='exclude_quality_only_S' and x.get('safety_quality_basis')=='quality_only':drop='S'
    elif sc=='exclude_qualification_only_I' and it=={'qualification_advantage'}:drop='I'
    elif sc=='exclude_clinical_management_only_F' and ft=={'clinical_management'}:drop='F'
    elif sc=='exclude_dimension_information_only_F' and ft=={'dimension_information'}:drop='F'
    elif sc=='retain_access_affordability_F' and not ft&{'access','affordability'}:drop='F'
    if drop and derived[r][DIMS.index(drop)]:derived[r][DIMS.index(drop)]=0;removed.append((r,drop))
   target=actual['methods'][name];count={g:{d:sum(groups[r]==g and dim==d for r,dim in removed) for d in DIMS} for g in GROUPS}
   check(count,target['removed_labels_by_group_dimension'],'definition/'+sc+'/'+name+'/removed_aggregate','definition')
   check(True,set(removed)=={(x['id'],x['dimension']) for x in target['removed_labels']},'definition/'+sc+'/'+name+'/removed_ID_set_mechanical_only','definition')
   full=data(derived,allids);sm=data(derived,pids);check(full,target['full4481'],'definition/'+sc+'/'+name+'/full');check(sm,target['same180'],'definition/'+sc+'/'+name+'/same180');current[name]=full
   removal_aggregate[sc+'/'+name]=count
  computed_defs.append(current)
 policy_stems=sorted({stems[r] for ids in allids.values() for r in ids});check(51,len(policy_stems),'policy_entry_n','scope')
 latest={}
 for st in policy_stems:
  m=metadata[st]
  if m['annual_series']:latest[m['policy_series']]=max(latest.get(m['policy_series'],m['year_in_filename']),m['year_in_filename'])
 scenario_names=manifest['robustness_scenarios'];cases=[(s,None) for s in scenario_names if s!='leave_one_policy_entry_out']+[('leave_one_policy_entry_out',st) for st in policy_stems]
 check(56,len(cases),'composition_n','scenario');computed_comps=[];scope_counts=[]
 check(cases,[(x['scenario'],x['omitted_policy_entry']) for x in findings['composition56']],'composition_identity','scenario')
 check(cases,[(x['scenario'],x['omitted_policy_entry']) for x in attention['robustness']],'attention_composition_identity','scenario')
 for i,(sc,omit) in enumerate(cases):
  chosen={g:[r for r in allids[g] if stems[r]!=omit and not(sc=='exclude_joint_publications' and metadata[stems[r]]['joint_publication']) and not(sc=='latest_annual_series_member' and metadata[stems[r]]['annual_series'] and metadata[stems[r]]['year_in_filename']!=latest[metadata[stems[r]]['policy_series']])] for g in GROUPS}
  target=findings['composition56'][i];check(True,all(set(chosen[g])==set(target['scope_ids'][g]) for g in GROUPS),'composition/'+str(i)+'/scope_ID_sets_mechanical_only','scope')
  key='policy_file' if sc=='policy_file_equal' else 'policy_series' if sc=='policy_series_equal' else None;current={}
  for name,y in labels.items():
   x=data(y,chosen,key);check(x,target['methods'][name],'composition/'+str(i)+'/'+name);current[name]=x
   short='rules' if name==RULE else 'LLM'
   for g in GROUPS:
    prof=x['departments'][g]['profile'];att=attention['robustness'][i]['methods'][short][g]
    check({k:v for k,v in prof.items() if k in att},att,'attention_composition/'+str(i)+'/'+short+'/'+g)
  computed_comps.append(current);scope_counts.append({'scenario':sc,'omitted_policy_entry':omit,'n_by_group':{g:len(v) for g,v in chosen.items()}})
 summary={}
 for name in rows:
  summary[name]={}
  for kind,records in [('definition6',computed_defs),('composition56',computed_comps)]:
   summary[name][kind]={}
   for metric in primary[name]['contrasts']:
    values=[x[name]['contrasts'][metric]['NHSA_minus_NHC'] for x in records];v=[x for x in values if x is not None];scale=1 if metric=='OR' else 100
    s={'scenario_n':len(values),'NHSA_higher_n':sum(float(x)>1e-12 for x in v),'NHC_higher_n':sum(float(x)<-1e-12 for x in v),'equal_n':sum(abs(float(x))<=1e-12 for x in v),'NA_n':len(values)-len(v),'NHSA_minus_NHC_range':[min(v)*scale,max(v)*scale] if v else None,'range_units':'OR units' if metric=='OR' else 'percentage points'}
    check(s,findings['summary'][name][kind][metric],'summary/'+name+'/'+kind+'/'+metric);summary[name][kind][metric]=s
 # Fresh5000 paired source-file replicates per department. This verifies
 # numerical endpoints and implementation, not frequentist coverage validity.
 bootstrap=[];clusters_summary=[]
 for g in GROUPS:
  ns=sorted({sources[r] for r in allids[g]});k=len(ns);seed=(BASE_SEED+int(hashlib.sha256(('full_corpus_paired_source_file/'+g).encode()).hexdigest()[:8],16))%2**32
  binding=next(x for x in attention['cluster_bindings'] if x['group']==g)
  check(ns,binding['source_names'],'bootstrap/'+g+'/source_names','bootstrap_binding');check(seed,binding['seed'],'bootstrap/'+g+'/seed','bootstrap_binding')
  mult=np.random.default_rng(seed).multinomial(k,np.repeat(1/k,k),size=B)
  q={};p={}
  for name,y in labels.items():
   arr=np.asarray([[sum(y[r][j] for r in allids[g] if sources[r]==n) for j in range(5)] for n in ns],float)
   hits=mult@arr;den=hits.sum(axis=1);q[name]=np.divide(hits,den[:,None],out=np.full_like(hits,np.nan),where=den[:,None]!=0);total=arr.sum(axis=0);p[name]=total/total.sum()
  for j,d in enumerate(DIMS):
   rep=100*(q[LLM][:,j]-q[RULE][:,j]);finite=rep[np.isfinite(rep)];end=np.quantile(finite,[.025,.975]) if len(finite) else [None,None]
   expected={'group':g,'dimension':d,'unit_n':len(allids[g]),'source_file_cluster_n':k,'difference_direction':'LLM_minus_rules','difference_percentage_points':100*(p[LLM][j]-p[RULE][j]),'ci95_source_file_conditional_percentage_points':{'low':float(end[0]) if end[0] is not None else None,'high':float(end[1]) if end[1] is not None else None,'defined_repetitions':len(finite),'undefined_repetitions':B-len(finite)}}
   actual=next(x for x in attention['paired_file_composition_sensitivity'] if x['group']==g and x['dimension']==d)
   check(expected,actual,'bootstrap/'+g+'/'+d,'bootstrap_endpoint');bootstrap.append(expected)
  clusters_summary.append({'group':g,'policy_entry_cluster_n':len({stems[r] for r in allids[g]}),'source_file_cluster_n':k,'replicates':B,'seed':seed,'paired_multiplicities_shared_by_both_methods':True})
 for p,h in bindings.items():check(h,sha(p),str(p)+'/read_only_after','read_only')
 result={'status':'PASS' if not failures else 'FAIL','review_utc':datetime.now(timezone.utc).isoformat(),'independent_method':'No project statistical functions imported/executed. Python integer counts/Fraction exact proportions, cluster means and contrasts; fresh numpy5000 paired source-file replicates; float tolerance1e-12. Aggregate-only outputs, no A/C or per-reserved-unit semantic reading.','scope_status':{'primary4481_two_methods_five_counts_denominators_shares_coverage_all10_pairs':'PASS' if not failures else 'SEE_FAILURES','same180_machine_only':'PASS' if not failures else 'SEE_FAILURES','old240_machine_labels_and_all_source_subtypes':'PASS' if not failures else 'SEE_FAILURES','definition6_full4481_same180_removed_scopes_and_direction':'PASS' if not failures else 'SEE_FAILURES','composition56_scopes_equal_cluster_estimands_and_direction':'PASS' if not failures else 'SEE_FAILURES','bootstrap_5000_seeds_clusters_pairing_point_and_endpoint_numeric_reproduction':'PASS' if not failures else 'SEE_FAILURES','bootstrap_frequentist_coverage_or_semantic_truth_uncertainty':'NOT_ESTABLISHED','human_reference_values_and_semantic_correctness':'NOT_REVIEWED'},'check_counts':dict(checks),'failures':failures,'sources':{str(p):{'expected':h,'actual':sha(p)} for p,h in bindings.items()},'old240':old240,'primary_exact_profiles_and_pairs':clean(primary),'definition_removed_aggregates':removal_aggregate,'composition_scope_counts':scope_counts,'exact_summary':clean(summary),'bootstrap_cluster_structure':clusters_summary,'independently_reproduced_15_paired_interval_records':bootstrap,'safety_notes':['180 probability and60 enriched challenge kept distinct; only probability60 perdepartment contributes same180.','Policy-entry51 clusters for composition checks differ from actual-source-file clusters21/39/18 for paired bootstrap; do not conflate these units.','No theoretical/empirical coverage proof follows from reproducing percentile endpoints.','Original findings and machine predictions were not modified.'],'script_sha256':sha(__file__)}
 OUT.mkdir();p=OUT/'independent_numeric_review.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'status':result['status'],'check_counts':dict(checks),'failure_n':len(failures),'first_failures':failures[:8],'report_path':str(p),'report_sha256':sha(p),'bootstrap_cluster_structure':clusters_summary},ensure_ascii=False))
 assert not failures

if __name__=='__main__':main()

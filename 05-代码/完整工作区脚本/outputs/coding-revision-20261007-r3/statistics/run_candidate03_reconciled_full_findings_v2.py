"""Explicit196+25 reconciled candidate03 full-corpus descriptive development sensitivity; no model calls.
Functions preserve frozen v36.2 scope/denominator rules; new actual outputs required.
Does not read or transplant candidate02 results or stability.
"""
from pathlib import Path
from fractions import Fraction as Q
import argparse,itertools,json,math,datetime,sys
import candidate03_reconciled_execution_profile_v2 as reconciled_v2
import statistical_core_r3 as c
import final_binding_io_r3 as io
from final_attention_r3 import full_summary,file_equal_summary
from definition_boundary_sensitivity_r3 import derive,SCENARIOS
from run_candidate03_reconciled_complete_statistics_v2 import verify_tree,load_methods
PAIRS=list(itertools.combinations(c.DIMS,2));CELL=['both_n','a_only_n','b_only_n','neither_n']

def from_cells(z,a,b,kind='raw_counts'):
 n11,n10,n01,n00=map(Q,z);n=n11+n10+n01+n00
 div=lambda a,b:float(a/b) if b else None
 return {'dimension_a':a,'dimension_b':b,'cell_type':kind,**dict(zip(CELL,map(float,z))),'n_or_probability_mass':float(n),'a_positive':float(n11+n10),'b_positive':float(n11+n01),'p_b_given_a':div(n11,n11+n10),'p_a_given_b':div(n11,n11+n01),'a_base':div(n11+n10,n),'b_base':div(n11+n01,n),'p_b_given_non_a':div(n01,n01+n00),'p_a_given_non_b':div(n10,n10+n00),'OR':div(n11*n00,n10*n01),'OR_NA':not(n10*n01),'OR_exact':str(n11*n00/(n10*n01)) if n10*n01 else None,'both_unit_fraction':div(n11,n)}

def pair(rows,ids,a,b):
 z=[0,0,0,0]
 for rid in ids:
  x,y=c.label(rows[rid],a),c.label(rows[rid],b);z[{(1,1):0,(1,0):1,(0,1):2,(0,0):3}[x,y]]+=1
 out=from_cells(z,a,b);out.update({'unit_n':len(ids),**dict(zip(CELL,z))});return out

def cluster_ids(ids,key):
 clusters={}
 for rid in ids:
  st=ctx['inputs'][rid]['input']['original_file_stem'];cl=st if key=='policy_file' else ctx['metadata'][st]['policy_series'];clusters.setdefault(cl,[]).append(rid)
 return clusters

def equalpair(rows,ids,a,b,key):
 clusters=cluster_ids(ids,key);records={name:pair(rows,members,a,b) for name,members in clusters.items()};G=len(records)
 keep1=[x['p_b_given_a'] for x in records.values() if x['p_b_given_a'] is not None];keep2=[x['p_a_given_b'] for x in records.values() if x['p_a_given_b'] is not None]
 z=[sum((Q(x[k],x['unit_n']) for x in records.values()),Q(0))/G for k in CELL] if G else [Q(0)]*4
 mixed=from_cells(z,a,b,'equal_cluster_mean_cell_probabilities')
 return {'dimension_a':a,'dimension_b':b,'unit_n':len(ids),'cell_type':'cluster_conditionals_mean; not pooled4cellOR','equal_cluster_n':G,'p_b_given_a':sum(keep1)/len(keep1) if keep1 else None,'p_a_given_b':sum(keep2)/len(keep2) if keep2 else None,'defined_a_clusters':len(keep1),'defined_b_clusters':len(keep2),'zero_a_clusters_excluded':[name for name,x in records.items() if x['p_b_given_a'] is None],'zero_b_clusters_excluded':[name for name,x in records.items() if x['p_a_given_b'] is None],'cluster_counts':records,'equal_cluster_cell_mixture':mixed,'OR':mixed['OR'],'OR_interpretation':'OR of equally averaged cell probabilities, NOT meanOR or file-adjusted association.'}

def profile(rows,ids,key=None):
 raw=full_summary(rows,ids);raw['coverage']={d:raw['coding_count'][d]/len(ids) if ids else None for d in c.DIMS}
 if key is None:return raw
 res=file_equal_summary(ctx,rows,ids,key);clusters=cluster_ids(ids,key);res['coverage']={d:sum(sum(c.label(rows[rid],d) for rid in members)/len(members) for members in clusters.values())/len(clusters) if clusters else None for d in c.DIMS};res['raw_unweighted_profile_for_audit']=raw
 res['coverage_estimand']='Mean within-cluster dimension coverage over ALL clusters; q is mean within-cluster attention excluding explicitlyzero-hitclusters. Different denominators retained.';return res

def data(rows,gids,key=None):
 return {g:{'profile':profile(rows,ids,key),'all10_pairs':[equalpair(rows,ids,a,b,key) if key else pair(rows,ids,a,b) for a,b in PAIRS]} for g,ids in gids.items()}

def getf(x):return next(z for z in x['all10_pairs'] if (z['dimension_a'],z['dimension_b'])==('Ec','F'))

def contrast(deps):
 h,n=deps['NHSA'],deps['NHC'];hp,np=getf(h),getf(n)
 vals={'P_F_given_Ec':(hp['p_b_given_a'],np['p_b_given_a']),'P_Ec_given_F':(hp['p_a_given_b'],np['p_a_given_b']),'OR':(hp['OR'],np['OR'])}
 for d in c.DIMS:
  for kind in ['attention_share','coverage']:vals[f'{kind}_{d}']=(h['profile'][kind][d],n['profile'][kind][d])
 return {key:{'NHSA':a,'NHC':b,'NHSA_minus_NHC':a-b if a is not None and b is not None else None,'difference_units':'OR units' if key=='OR' else 'fraction; multiply100forpercentagepoints'} for key,(a,b) in vals.items()}

def ids_for(g,sc,omit):
 ids=[]
 for rid in allids[g]:
  st=ctx['inputs'][rid]['input']['original_file_stem'];m=ctx['metadata'][st]
  if st==omit:continue
  if sc=='exclude_joint_publications' and m['joint_publication']:continue
  if sc=='latest_annual_series_member' and m['annual_series'] and m['year_in_filename']!=latest[m['policy_series']]:continue
  ids.append(rid)
 return ids


def main():
 global ctx,allids,latest
 p=argparse.ArgumentParser();p.add_argument('--bindings',type=Path,required=True);p.add_argument('--bindings-sha256',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 assert not a.out.exists(),'Never overwrite an earlier result'
 assert c.sha(a.bindings)==a.bindings_sha256
 dev=c.read(a.bindings)
 reconciled_v2.development_header(dev)
 assert dev['stage']=='development_only_all240_exposed' and dev['root_development_bindings_confirmed'] is True
 assert dev['independent_validation'] is False and dev['human_validation_completed'] is False
 leaves=verify_tree(dev);manifest=io.bound(dev['reference_manifest']);leaves+=verify_tree(manifest)
 ctx=io.context_from_manifest(manifest);refs,refaudit=io.final_references(manifest,ctx)
 saved=io.bound_jsonl(dev['existing_candidate_reference'])
 assert set(saved)==set(refs['candidate']) and all(c.label(saved[r],d)==c.label(refs['candidate'][r],d) for r in saved for d in c.DIMS)
 methods,methodaudit=load_methods(dev,manifest,ctx)
 assert set(methods)=={'rules-v36.2',reconciled_v2.STAT_KEY},'Explicit two-method development comparison only'
 allids={g:sorted(r for r in ctx['inputs'] if ctx['groups'][r]==g) for g in c.GROUPS}
 pids={g:sorted(r for r,x in ctx['sample'].items() if x['component']=='probability_canonical' and x['group']==g) for g in c.GROUPS}
 assert [len(allids[g]) for g in c.GROUPS]==[1848,2100,533] and all(len(x)==60 for x in pids.values())
 stems=sorted({ctx['inputs'][r]['input']['original_file_stem'] for g in c.GROUPS for r in allids[g]});assert len(stems)==51
 latest={}
 for st in stems:
  m=ctx['metadata'][st]
  if m['annual_series']:latest[m['policy_series']]=max(latest.get(m['policy_series'],m['year_in_filename']),m['year_in_filename'])
 scenarios=[(name,None) for name in manifest['robustness_scenarios'] if name!='leave_one_policy_entry_out']
 if 'leave_one_policy_entry_out' in manifest['robustness_scenarios']:scenarios.extend(('leave_one_policy_entry_out',st) for st in stems)
 assert len(scenarios)==56 and len(set(scenarios))==56
 compositions=[]
 for sc,omit in scenarios:
  gids={g:ids_for(g,sc,omit) for g in c.GROUPS};key='policy_file' if sc=='policy_file_equal' else 'policy_series' if sc=='policy_series_equal' else None
  obj={'scenario':sc,'omitted_policy_entry':omit,'scope_ids':gids,'methods':{}}
  for name,rows in methods.items():
   vals=data(rows,gids,key);obj['methods'][name]={'departments':vals,'contrasts':contrast(vals)}
  compositions.append(obj)
 definitions=[]
 for sc,explanation in SCENARIOS.items():
  obj={'scenario':sc,'explanation':explanation,'methods':{}}
  for name,rows in methods.items():
   derived,changes=derive(rows,sc);vals=data(derived,allids);small=data(derived,pids)
   obj['methods'][name]={'full4481':{'departments':vals,'contrasts':contrast(vals)},'same180':{'departments':small,'contrasts':contrast(small)},'removed_labels':changes,'removed_labels_by_group_dimension':{g:{d:sum(ctx['groups'][x['id']]==g and x['dimension']==d for x in changes) for d in c.DIMS} for g in c.GROUPS}}
  definitions.append(obj)
 assert len(definitions)==6
 primary={name:{'departments':data(rows,allids),'status':'post_exposure_development'} for name,rows in methods.items()}
 same180={name:{'departments':data(rows,pids),'status':'AIreference_not_human' if name in refs else 'post_exposure_development'} for name,rows in {**refs,**methods}.items()}
 for x in [*primary.values(),*same180.values()]:x['contrasts']=contrast(x['departments'])
 metrics=['P_F_given_Ec','P_Ec_given_F','OR']+[f'{s}_{d}' for s in ['attention_share','coverage'] for d in c.DIMS]
 summary={}
 for name in methods:
  summary[name]={}
  for kind,records in [('definition6',[x['methods'][name]['full4481'] for x in definitions]),('composition56',[x['methods'][name] for x in compositions])]:
   summary[name][kind]={}
   for metric in metrics:
    values=[x['contrasts'][metric]['NHSA_minus_NHC'] for x in records];valid=[x for x in values if x is not None];scale=1 if metric=='OR' else 100
    summary[name][kind][metric]={'scenario_n':len(values),'NHSA_higher_n':sum(x>1e-12 for x in valid),'NHC_higher_n':sum(x< -1e-12 for x in valid),'equal_n':sum(abs(x)<=1e-12 for x in valid),'NA_n':len(values)-len(valid),'NHSA_minus_NHC_range':[min(valid)*scale,max(valid)*scale] if valid else None,'range_units':'OR units' if metric=='OR' else 'percentage points'}
 # Check every retained pair, not a favorable subset.
 pair_n=0
 def verify_departments(deps):
  nonlocal pair_n
  for g,z in deps.items():
   assert len(z['all10_pairs'])==10 and {(x['dimension_a'],x['dimension_b']) for x in z['all10_pairs']}==set(PAIRS)
   for x in z['all10_pairs']:
    pair_n+=1
    if x['cell_type']=='raw_counts':
     assert all(type(x[k]) is int and x[k]>=0 for k in CELL) and sum(x[k] for k in CELL)==x['unit_n']
     assert x['a_positive']==z['profile']['coding_count'][x['dimension_a']] and x['b_positive']==z['profile']['coding_count'][x['dimension_b']]
    else:
     mix=x['equal_cluster_cell_mixture'];assert abs(sum(mix[k] for k in CELL)-1)<1e-12
     assert x['defined_a_clusters']+len(x['zero_a_clusters_excluded'])==x['equal_cluster_n']
     assert x['defined_b_clusters']+len(x['zero_b_clusters_excluded'])==x['equal_cluster_n']
 for obj in [*primary.values(),*same180.values()]:verify_departments(obj['departments'])
 for obj in compositions:
  for x in obj['methods'].values():verify_departments(x['departments'])
 for obj in definitions:
  for x in obj['methods'].values():
   verify_departments(x['full4481']['departments']);verify_departments(x['same180']['departments'])
 for b in leaves:assert c.sha(b['path'])==b['sha256']
 for item in dev['methods'].values():
  if item['kind']=='rules':verify_tree(io.bound(item['source_candidate_binding']))
  else:verify_tree(io.bound(item['execution_adapter']))
 prov={'stage':'post_exposure_development_descriptive_only','all240_exposed':True,'independent_validation':False,'human_validation_completed':False,'binding':{'path':str(a.bindings.resolve()),'sha256':a.bindings_sha256},'methods':dev['methods'],'material_version':'v14','script_sha256':c.sha(__file__),'code_bindings':dev['statistical_code'],'source_bindings':leaves,'no_model_calls':True,'no_old_LLM02_sensitivity_or_stability_reused':True,'all10_pairs_retained':True,'not_crossed_6x56':True,'no_new_significance_or_bootstrap_in_this_descriptive_driver':True,'scope':'Full4481fixedtexts, excludes GOV443. Same180 per-department canonical sample, frame947/760/60, separate from full corpus. Six definition scenarios and56 composition scenarios separately.','denominators':'Conditional proportions use dimension-positive units. Equal-cluster conditional proportions average only defined clusters and record excluded clusters; q averages nonzero-five-hit clusters; coverage averages all clusters. OR is descriptive marginal/mixed-cell diagnostic, not file-adjusted or causal; zero denominator NA, no0.5 correction.'}
 flat=[]
 for scope,values in [('full4481',primary),('same180_probability',same180)]:
  for name,obj in values.items():
   for g,x in obj['departments'].items():flat.extend({'scope':scope,'method':name,'department':g,**z} for z in x['all10_pairs'])
 qa={'all_checks_pass':True,'complete_actual_methods_required':True,'all_bound_inputs_unchanged':True,'full_unit_n':4481,'GOV_excluded':443,'same180_n':180,'definition_n':6,'composition_n':56,'all10_pair_record_n_checked':pair_n,'no_candidate02_sensitivity_substitution':True,'no_new_significance_orCI':True}
 a.out.mkdir(parents=True,exist_ok=False)
 c.write_json(a.out/'完整定义构成核查.json',{'provenance':prov,'primary_full4481':primary,'same180_primary':same180,'definition6':definitions,'composition56':compositions,'summary':summary})
 c.write_json(a.out/'完整十对主表.json',{'provenance':prov,'rows':flat})
 c.write_json(a.out/'full4481_attention.json',{'provenance':prov,'primary':{name:{g:x['profile'] for g,x in obj['departments'].items()} for name,obj in primary.items()}})
 c.write_json(a.out/'核查QA.json',qa)
 c.write_json(a.out/'source_execution_and_reference_QA.json',{'methods':methodaudit,'references':refaudit})
 lines=['# 规则v36.2与LLM03：完整开发描述统计','', '全部240条已暴露；这些是开发比较，尚未确定最终采用方法。六定义/56构成分开计算，保留所有10对；不等于336交叉场景，不做显著性筛选，不调用模型，不复制02敏感性或稳定性。','', '|方法|部门|Ec∩F/仅Ec/仅F/均无|P(F给定Ec)|P(Ec给定F)|Ec q|F q|','|---|---|---|---|---|---|---|']
 pct=lambda x:'NA' if x is None else f'{100*x:.2f}%'
 for name,obj in primary.items():
  for g,x in obj['departments'].items():
   z=getf(x);lines.append('|'+ '|'.join([name,g,'/'.join(str(z[k]) for k in CELL),pct(z['p_b_given_a']),pct(z['p_a_given_b']),pct(x['profile']['attention_share']['Ec']),pct(x['profile']['attention_share']['F'])])+'|')
 lines+=['','各情景完整四格、边际率、两个条件比例、OR与q/coverage及全部方向计数见JSON；不能从条件比例直接推断相对基率关联更强、患者获益或因果机制。实际采用需root独立语义及结果审阅。']
 (a.out/'完整开发描述表.md').write_text('\n'.join(lines)+'\n')
 c.write_json(a.out/'output_freeze.json',{'bindings_sha256':a.bindings_sha256,'files':{p.name:c.sha(p) for p in a.out.iterdir() if p.is_file()}})
 print(json.dumps({'status':'complete_candidate03_descriptive_development','out':str(a.out),'QA':qa},ensure_ascii=False))

if __name__=='__main__':
 try: main()
 except (reconciled_v2.ProfileGateError,AssertionError,KeyError,TypeError,ValueError,OSError) as exc:
  print(json.dumps({'status':'BLOCKED_NO_STATISTICS_RELEASED','error':str(exc)},ensure_ascii=False));sys.exit(2)

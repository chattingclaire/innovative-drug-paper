from pathlib import Path
from fractions import Fraction as Q
from collections import Counter
import sys,json,itertools,math,hashlib,datetime
R=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/coding-revision-20261007-r3');S=R/'statistics';D=Path(__file__).parent/'findings';D.mkdir(exist_ok=True);sys.path.insert(0,str(S))
import statistical_core_r3 as c,final_binding_io_r3 as io
from final_attention_r3 import full_summary,file_equal_summary
from definition_boundary_sensitivity_r3 import derive,SCENARIOS
manifest_path=S/'final_bindings_v14_CONFIRMED_r3.json';manifest=c.read(manifest_path);assert c.sha(manifest_path)=='46582af989d0473655b71ba38f174c2043794b8da9833bca9940aa0cf62c71cd'
ctx=io.context_from_manifest(manifest);refs,_=io.final_references(manifest,ctx)
sealed_path=R/'rules-v36.2-development/final_candidate_binding.json';sealed=c.read(sealed_path)
for key in ['prediction','input','run','QA','freeze']:assert c.sha(sealed[key]['path'])==sealed[key]['sha256']
assert c.read(sealed['QA']['path'])['all_checks_pass']
assert sealed['prediction']['sha256']=='105d10d7f441ed2c609911aa1f02bcaa4fc695acea35c6164750930a3021cc2b'
methods={'rules_v36.2_development':io.bound_jsonl(sealed['prediction']),'LLM02_formal':io.bound_jsonl(manifest['methods']['LLM']['output'])}
assert all(set(rows)==set(ctx['inputs']) for rows in methods.values())
full_path=S/'final-v14/full4481_machine_attention_and_file_composition_sensitivity.json';oldfull=c.read(full_path)
oldco=c.read(R/'insights-20261008/完整十对共现.json');oldstab=c.read(R/'insights-20261008/共现稳定性计算.json');oldOR=c.read(R/'methods-20261008/基率解释诊断_OR.json')
allids={g:sorted(r for r in ctx['inputs'] if ctx['groups'][r]==g) for g in c.GROUPS};pids={g:sorted(r for r,x in ctx['sample'].items() if x['component']=='probability_canonical' and x['group']==g) for g in c.GROUPS}
PAIRS=list(itertools.combinations(c.DIMS,2));CELL=['both_n','a_only_n','b_only_n','neither_n'];exactratio=lambda a,b:float(Q(a,b)) if b else None

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
stems=sorted({ctx['inputs'][r]['input']['original_file_stem'] for g in c.GROUPS for r in allids[g]});latest={}
for st in stems:
 m=ctx['metadata'][st]
 if m['annual_series']:latest[m['policy_series']]=max(latest.get(m['policy_series'],m['year_in_filename']),m['year_in_filename'])

def ids_for(g,sc,omit):
 ids=[]
 for rid in allids[g]:
  st=ctx['inputs'][rid]['input']['original_file_stem'];m=ctx['metadata'][st]
  if st==omit:continue
  if sc=='exclude_joint_publications' and m['joint_publication']:continue
  if sc=='latest_annual_series_member' and m['annual_series'] and m['year_in_filename']!=latest[m['policy_series']]:continue
  ids.append(rid)
 return ids
compositions=[]
for rec in oldfull['robustness']:
 sc,omit=rec['scenario'],rec['omitted_policy_entry'];gids={g:ids_for(g,sc,omit) for g in c.GROUPS};key='policy_file' if sc=='policy_file_equal' else 'policy_series' if sc=='policy_series_equal' else None
 obj={'scenario':sc,'omitted_policy_entry':omit,'scope_ids':gids,'methods':{}}
 for name,rows in methods.items():
  vals=data(rows,gids,key);obj['methods'][name]={'departments':vals,'contrasts':contrast(vals)}
 compositions.append(obj)
assert len(compositions)==56 and len(stems)==51

definitions=[]
for sc,explanation in SCENARIOS.items():
 obj={'scenario':sc,'explanation':explanation,'methods':{}}
 for name,rows in methods.items():
  derived,changes=derive(rows,sc);vals=data(derived,allids);small=data(derived,pids)
  obj['methods'][name]={'full4481':{'departments':vals,'contrasts':contrast(vals)},'same180':{'departments':small,'contrasts':contrast(small)},'removed_labels':changes,'removed_labels_by_group_dimension':{g:{d:sum(ctx['groups'][x['id']]==g and x['dimension']==d for x in changes) for d in c.DIMS} for g in c.GROUPS}}
 definitions.append(obj)
assert len(definitions)==6
primary={name:{'departments':data(rows,allids),'status':'development' if name.startswith('rules') else 'formal_baseline'} for name,rows in methods.items()}
same180={name:{'departments':data(rows,pids),'status':'AIreference;not human' if name in refs else 'development' if name.startswith('rules') else 'formal_baseline'} for name,rows in {**refs,**methods}.items()}
for x in [*primary.values(),*same180.values()]:x['contrasts']=contrast(x['departments'])

# Check unchanged LLM02 recomputation against three old independent frozen outputs.
checks=0
for rec in oldco['results']:
 if rec['method']!='LLM':continue
 scope=primary['LLM02_formal'] if rec['scope']=='full4481' else same180['LLM02_formal']
 for previous in rec['pairs']:
  current=next(x for x in scope['departments'][rec['department']]['all10_pairs'] if (x['dimension_a'],x['dimension_b'])==(previous['dimension_a'],previous['dimension_b']))
  for k in CELL+['p_b_given_a','p_a_given_b']:
   a,b=current[k],previous[k];assert (a is None and b is None) or a is not None and b is not None and math.isclose(a,b,abs_tol=1e-12),(k,a,b);checks+=1
for old,new in zip(oldstab['composition56'],compositions):
 assert (old['scenario'],old['omitted_policy_entry'])==(new['scenario'],new['omitted_policy_entry'])
 for g in c.GROUPS:
  bef=old['methods']['LLM'];aft=new['methods']['LLM02_formal'];a=bef['departments'][g]['p_b_given_a'];b=getf(aft['departments'][g])['p_a_given_b']
  assert (a is None and b is None) or a is not None and b is not None and math.isclose(a,b,abs_tol=1e-12);checks+=1
  for dim in c.DIMS:assert math.isclose(bef['attention_profiles'][g]['attention_share'][dim],aft['departments'][g]['profile']['attention_share'][dim],abs_tol=1e-12);checks+=1
for old,new in zip(oldstab['definition6'],definitions):
 assert old['scenario']==new['scenario']
 for g in c.GROUPS:
  bef=old['methods']['LLM']['full4481'];aft=new['methods']['LLM02_formal']['full4481'];a=bef['departments'][g]['p_b_given_a'];b=getf(aft['departments'][g])['p_a_given_b'];assert (a is None and b is None) or a is not None and b is not None and math.isclose(a,b,abs_tol=1e-12);checks+=1
for old,new in zip(oldOR['additive_and_reverse_conditional_diagnostic']['composition56'],compositions):
 for g in c.GROUPS:
  a=old['methods']['LLM']['departments'][g]['P_F_given_Ec'];b=getf(new['methods']['LLM02_formal']['departments'][g])['p_b_given_a'];assert (a is None and b is None) or a is not None and b is not None and math.isclose(a,b,abs_tol=1e-12);checks+=1
summary={}
metrics=['P_F_given_Ec','P_Ec_given_F','OR']+[f'{s}_{d}' for s in ['attention_share','coverage'] for d in c.DIMS]
for name in methods:
 summary[name]={}
 for group,records in [('definition6',[x['methods'][name]['full4481'] for x in definitions]),('composition56',[x['methods'][name] for x in compositions])]:
  summary[name][group]={}
  for metric in metrics:
   values=[x['contrasts'][metric]['NHSA_minus_NHC'] for x in records];valid=[v for v in values if v is not None];scale=1 if metric=='OR' else 100
   summary[name][group][metric]={'scenario_n':len(values),'NHSA_higher_n':sum(x>1e-12 for x in valid),'NHC_higher_n':sum(x< -1e-12 for x in valid),'equal_n':sum(abs(x)<=1e-12 for x in valid),'NA_n':len(values)-len(valid),'NHSA_minus_NHC_range':[min(valid)*scale,max(valid)*scale] if valid else None,'range_units':'OR units' if metric=='OR' else 'percentage points'}
paths=[manifest_path,sealed_path,Path(sealed['prediction']['path']),Path(sealed['QA']['path']),Path(manifest['methods']['LLM']['output']['path']),Path(manifest['material']['rule_inputs']['path']),Path(manifest['metadata']['path']),full_path,R/'insights-20261008/完整十对共现.json',R/'insights-20261008/共现稳定性计算.json',R/'methods-20261008/基率解释诊断_OR.json',S/'definition_boundary_sensitivity_r3.py',S/'final_attention_r3.py',S/'final_binding_io_r3.py',Path(__file__)]
for item in [sealed['prediction'],sealed['input'],sealed['run'],sealed['QA'],manifest['metadata'],manifest['methods']['LLM']['output']]:assert c.sha(item['path'])==item['sha256']
provenance={'stage':'exploratory_descriptive_development_rules_and_formalLLM02','new_rules_all240_exposed':True,'independent_validation':False,'human_validation_completed':False,'no_new_significance_orCI':True,'no_paper_or_label_changes':True,'all10_pairs_retained_for_each_scope_andscenario':True,'not_crossed_6x56':'Six definition cases and56 composition cases separately, not336 combined cases.','scope':'full4481fixedtexts excludesGOV443; same180onlyremainingcanonicalframes947/760/60, no challenge pooling.','composition_selection':'51leave-one-policy-entry-out +primary/fileequal/seriesequal/latestannual/excludejoint; same frozen metadata and scope code. Equalcluster conditional means exclude conditioningzero clusters with namedlists. q equalcluster means exclude all-zero5dimensionclusters; coverage usesallclusters.','OR':'zero denominator NA, no0.5correction;equalcluster OR uses cellmixture, not file adjustment or meanOR.','source_bindings':[{'path':str(p),'sha256':c.sha(p)} for p in paths]}
c.write_json(D/'完整定义构成核查.json',{'provenance':provenance,'primary_full4481':primary,'same180_primary':same180,'definition6':definitions,'composition56':compositions,'summary':summary})
c.write_json(D/'核查QA.json',{'all_checks_pass':True,'LLM02_previous_frozen_recomputation_checks':checks,'formal_outputs_unchanged':True,'raw4cell_check':'integerfullsamplepaircells fromactualbinaryoutput; each4cellssumunitn','new_rules_prediction_sha256':sealed['prediction']['sha256'],'all10_pairs_primary_and6and56':True,'composition56':len(compositions),'definition6':len(definitions),'bootstrap_run':False})
# All ten pair primary tables are compact additional access, no pair ranking.
flat=[]
for scope,values in [('full4481',primary),('same180_probability',same180)]:
 for name,obj in values.items():
  for group,x in obj['departments'].items():flat += [{'scope':scope,'method':name,'department':group,**z} for z in x['all10_pairs']]
c.write_json(D/'完整十对主表.json',{'provenance':provenance,'rows':flat})

pct=lambda x:'NA' if x is None else f'{x*100:.2f}%'
md=['# v36.2与正式LLM02：共现和注意力核查','', '规则v36.2为全部240条已暴露后的开发候选；LLM02为既有正式运行。两方法真实读取各自封存输出，本表没有更新论文、标签、样本或正式v33统计，没有新增显著性检验或置信区间。','', '|方法|部门|Ec∩F/仅Ec/仅F/均无|P(F给定Ec)|P(Ec给定F)|Ec覆盖率|F覆盖率|Ec注意力q|F注意力q|','|---|---|---|---:|---:|---:|---:|---:|---:|']
for name,obj in primary.items():
 for g in c.GROUPS:
  x=obj['departments'][g];z=getf(x);p=x['profile'];md.append('|'+ '|'.join([name,g,'/'.join(str(z[k]) for k in CELL),pct(z['p_b_given_a']),pct(z['p_a_given_b']),pct(p['coverage']['Ec']),pct(p['coverage']['F']),pct(p['attention_share']['Ec']),pct(p['attention_share']['F'])])+'|')
md+=['','P(F给定Ec)分母为本部门Ec阳性单元；反向P(Ec给定F)分母为F单元。coverage分母为全部单元（药监1848/医保2100/卫健533）；q分母为五维编码句次合计。它们是不同问题，不能相互替换。','', '|方法|情景组|指标|医保较高|卫健较高|相同|NA|医保−卫健范围|','|---|---|---|---:|---:|---:|---:|---|']
for name,sets in summary.items():
 for group,vals in sets.items():
  for metric in ['P_F_given_Ec','P_Ec_given_F','OR','attention_share_F','coverage_F','attention_share_Ec','coverage_Ec']:
   z=vals[metric];ran=z['NHSA_minus_NHC_range'];md.append('|'+ '|'.join([name,group,metric,str(z['NHSA_higher_n']),str(z['NHC_higher_n']),str(z['equal_n']),str(z['NA_n']),'NA' if ran is None else f'{ran[0]:.4f} 至 {ran[1]:.4f} '+z['range_units']])+'|')
md+=['','六个定义与56个构成情景分开计算，不是两者交叉的336情景；范围不是区间，也不是独立重复。原代码的所有10对均保留，未根据最大差值、OR或显著性选故事。','', '文件/系列等权时，条件比例是有对应条件阳性的簇内比例均值，零分母簇名单单列；q是有五维阳性的簇内q均值；coverage是所有簇内覆盖率的均值。原始四格、另一等权混合四格、逐簇OR均保留。等权混合OR不控制文件内混杂。','', '## 最窄可支持表述','']
for name in methods:
 x=primary[name]['departments'];a,b=getf(x['NHSA']),getf(x['NHC']);md.append(f"{name}：固定语料中，经济性单元同时含公平性的比例，医保为{a['both_n']}/{int(a['a_positive'])}（{pct(a['p_b_given_a'])}），卫健为{b['both_n']}/{int(b['a_positive'])}（{pct(b['p_b_given_a'])}）；反向条件医保为{pct(a['p_a_given_b'])}，卫健为{pct(b['p_a_given_b'])}。这些比例描述内容组合，不是实际患者公平程度、价值权重或因果机制。")
md+=['','方向是否在全部敏感性口径保持，须按上表分别陈述；不能将一种比例的稳健性移植给另一种比例或q。若要解释支付/供给/使用路径，应把对应原句和访谈与这一描述相连，不能从共现自身推定。','', '新规则的开发改善及跨方法方向一致不能替代新的真人句级/联合事件验证。正式LLM02在旧结果上的一致复算是算术QA，不是新增独立实证。']
(D/'新发现核查与最窄表述.md').write_text('\n'.join(md)+'\n')
c.write_json(D/'output_freeze.json',{'files':{p.name:c.sha(p) for p in D.iterdir() if p.is_file() and p.name!='output_freeze.json'}})
print(json.dumps({'status':'complete','dir':str(D),'LLM02_old_checks':checks,'primary10pairrows':len(flat),'primary':{name:primary[name]['contrasts'] for name in methods},'summary':{name:{scope:{metric:vals[metric] for metric in ['P_F_given_Ec','P_Ec_given_F','attention_share_F','coverage_F']} for scope,vals in sets.items()} for name,sets in summary.items()}},ensure_ascii=False,indent=2))

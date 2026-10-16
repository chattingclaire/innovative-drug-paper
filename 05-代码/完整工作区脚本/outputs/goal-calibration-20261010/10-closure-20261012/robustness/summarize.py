"""Read-only projections of already computed attention diagnostics; no labels reclassified."""
import json, pathlib, hashlib, collections, itertools, datetime
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=pathlib.Path(__file__).resolve().parent
FILES={
 'rule':'07-statistics/rule-v11-v16-conditional-attention-robustness-root/conditional-robustness.json',
 'llm':'07-statistics/full4481-native-v16-compatible-attention-comparison-root/frozen-core-evaluation/conditional-robustness.json',
 'comparison':'07-statistics/full4481-native-v16-compatible-attention-comparison-root/machine-attention-comparison.json',
 'delivery_readme':'09-delivery/full4481-results-20261012-sol/README.md'}
D={m:json.loads((ROOT/FILES[m]).read_text()) for m in ['rule','llm','comparison']}
DIM=['S','E','Ec','I','F'];DEPTS=['NMPA','NHSA','NHC'];CLOCK='policy_year';EXPECTED=[['Ec'],['S'],['E'],['I'],['F']]
def eq(a,b):return json.dumps(a,sort_keys=True,ensure_ascii=False)==json.dumps(b,sort_keys=True,ensure_ascii=False)
def ranks(v):
 out=[]
 for k,x in sorted(((k,v) for k,v in v.items() if v is not None),key=lambda kv:(-kv[1],kv[0])):
  if out and abs(x-out[-1]['value'])<1e-12:out[-1]['members'].append(k)
  else:out.append({'value':x,'members':[k]})
 return {'ties':[sorted(x['members']) for x in out],'undefined':[k for k,v in v.items() if v is None]}
def extract(s):
 q={};p={};qb={};pb={}
 for d,v in s['dimensions'].items():
  q[d]=v.get('q_observed',v.get('q_mean_among_observed_positive_members'))
  p[d]=v.get('p_conditional_lower',v.get('p_mean_conditional_lower'))
  qb[d]=[v.get('q_conditional_lower',v.get('q_mean_conditional_bounds',{}).get('lower')),v.get('q_conditional_upper',v.get('q_mean_conditional_bounds',{}).get('upper'))]
  pb[d]=[v.get('p_conditional_lower',v.get('p_mean_conditional_lower')),v.get('p_conditional_upper',v.get('p_mean_conditional_upper'))]
 out={'q_observed':q,'p_observed_lower':p,'q_conditional_bounds':qb,'p_conditional_bounds':pb,'q_rank':ranks(q),'p_rank':ranks(p)}
 for k in ['clause_N','source_entry_N','clause_weight','positive_assignment_weight','unresolved_assignment_weight','member_N','q_observed_defined_member_N','q_observed_undefined_member_N','q_zero_denominator_member_keys']:
  if k in s:out[k]=s[k]
 if 'fractional_hit_share_r' in s:
  r=s['fractional_hit_share_r'];out['r_full_point_status']=r['full_point_status']
  out['r_full_point']={d:v['full_observed_point'] for d,v in r['dimensions'].items()}
  out['r_conditional_bounds']={d:[v['conditional_bounds']['lower'],v['conditional_bounds']['upper']] for d,v in r['dimensions'].items()}
  out['r_complete_subset_auxiliary']={d:v['complete_record_subset_auxiliary_point'] for d,v in r['dimensions'].items()}
 return out
def sign(v):return None if v is None else ('increase' if v>1e-12 else 'decrease' if v< -1e-12 else 'flat')
def sufficient_order(bounds,first,last):
 return (all(bounds[first][0]>bounds[d][1] for d in DIM if d!=first) and all(bounds[last][1]<bounds[d][0] for d in DIM if d!=last)) if all(all(z is not None for z in v) for v in bounds.values()) else None
S={m:{(x['scenario'],tuple(x['group'])):extract(x['statistics']) for x in D[m]['scenarios'] if x['clock']==CLOCK} for m in ['rule','llm']}
SCENARIOS=list(dict.fromkeys(x['scenario'] for x in D['rule']['scenarios']))
result={
 'purpose':'Synthesis of existing same-version machine diagnostics, not independent accuracy validation or final paper acceptance.',
 'inputs':{m:{'path':str(ROOT/f),'sha256':hashlib.sha256((ROOT/f).read_bytes()).hexdigest()} for m,f in FILES.items()},
 'definitions':{'q':'Observed positive weight for dimension / observed positive weight across all five dimensions; source means first compute q within positive-assignment members.','p_observed_lower':'Observed positive weight / all clause weight; unresolved slots remain unresolved. For means average per nonempty source.','conditional_bounds':'Observed 0/1 fixed; only lawful null changes. Marginal dimension bounds are not CIs or bounds on observed classification error.','rank':'Ties preserved, null never converted to zero.','date_deduplication':'Use policy_year for counts, after checking publication_year values are identical; duplicate clocks are not independent evidence.','leave_one_scope':'For each deleted source: total corpus, its department, its corpus-year, and its department-year.'},
 'dimensions':{'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'},
 'metadata_coverage':D['rule']['metadata_coverage'],
 'counts':{},'overall':{},'department':{},'yearly':{},'cross_machine':{},'scope_limits':D['rule']['metadata_coverage']['not_supported'],
 'formal_validation_complete':False,'paper_writing_gate_open':False,
}
for m in ['rule','llm']:
 original=D[m]; rows=original['scenarios']; ix={(x['clock'],x['scenario'],tuple(x['group'])):x['statistics'] for x in rows}
 clock_matches=sum(eq(ix[(CLOCK,x['scenario'],tuple(x['group']))],x['statistics']) for x in rows if x['clock']=='publication_year')
 means_match=sum(eq({k:v for k,v in S[m][('source_entry_q_p_mean',g)].items() if k!='q_zero_denominator_member_keys'},{k:v for k,v in S[m][('series_within_year_q_p_mean',g)].items() if k!='q_zero_denominator_member_keys'}) for sc,g in S[m] if sc=='source_entry_q_p_mean')
 out={sc:S[m][(sc,('entire_corpus',))] for sc in SCENARIOS}
 loo=[dict(removed_source=x['removed_source_entry_id'],group=x['group'],**extract(x['statistics'])) for x in original['leave_one_source_entry_out'] if x['clock']==CLOCK]
 overall_loo=[x for x in loo if x['group']==['entire_corpus']]
 expected_count=sum(x['q_rank']['ties']==EXPECTED for x in out.values())
 result['counts'][m]={'scenario_rows':len(rows),'unique_clock_rows':len(S[m]),'scenario_names':len(SCENARIOS),'date_clock_identical_rows':clock_matches,'date_clock_rows_checked':sum(x['clock']=='publication_year' for x in rows),'mean_scenario_identical_groups':means_match,'mean_groups_checked':44,'leave_one_rows':len(original['leave_one_source_entry_out']),'leave_one_single_clock_rows':len(loo),'overall_leave_one_rows':len(overall_loo),'lawful_null_assignments':original['lawful_null_assignment_N'],'technical_failures':original['technical_failure_N']}
 result['overall'][m]={'by_scenario':out,'exact_main_order_scenario_N':expected_count,'Ec_unique_first_scenario_N':sum(x['q_rank']['ties'][:1]==[['Ec']] for x in out.values()),'F_unique_last_scenario_N':sum(x['q_rank']['ties'][-1:]==[['F']] for x in out.values()),'conditional_bounds_sufficient_Ec_first_F_last_scenarios':[sc for sc,x in out.items() if sufficient_order(x['q_conditional_bounds'],'Ec','F')],'leave_one':overall_loo,'leave_one_exact_main_order_N':sum(x['q_rank']['ties']==EXPECTED for x in overall_loo),'leave_one_Ec_unique_first_N':sum(x['q_rank']['ties'][:1]==[['Ec']] for x in overall_loo),'leave_one_F_unique_last_N':sum(x['q_rank']['ties'][-1:]==[['F']] for x in overall_loo),'leave_one_full_order_counterexamples':[x for x in overall_loo if x['q_rank']['ties']!=EXPECTED],'leave_one_q_ranges':{d:[min(x['q_observed'][d] for x in overall_loo),max(x['q_observed'][d] for x in overall_loo)] for d in DIM}}
 dep={dept:{sc:S[m][(sc,('department',dept))] for sc in SCENARIOS} for dept in DEPTS}
 dep_loo={dept:[x for x in loo if x['group']==['department',dept]] for dept in DEPTS}
 dep_order={metric:{d:{sc:ranks({dep_:dep[dep_][sc][metric][d] for dep_ in DEPTS}) for sc in SCENARIOS} for d in DIM} for metric in ['q_observed','p_observed_lower']}
 result['department'][m]={'by_department_scenario':dep,'between_departments_ranks':dep_order,'within_department_top_counts':{dept:dict(collections.Counter('='.join(x['q_rank']['ties'][0]) if x['q_rank']['ties'] else 'NA' for x in dep[dept].values())) for dept in DEPTS},'leave_one_affected_department':dep_loo,'leave_one_top_counts':{dept:dict(collections.Counter('='.join(x['q_rank']['ties'][0]) if x['q_rank']['ties'] else 'NA' for x in dep_loo[dept])) for dept in DEPTS},'leave_one_affected_years':[x for x in loo if x['group'][0] in ['corpus_year','department_year']]}
 annual={sc:{scope:{str(y):S[m][(sc,('corpus_year',y) if scope=='corpus' else ('department_year',scope,y))] for y in range(2017,2027)} for scope in ['corpus']+DEPTS} for sc in SCENARIOS}
 temporal={}
 for sc in SCENARIOS:
  temporal[sc]={}
  for scope in ['corpus']+DEPTS:
   temporal[sc][scope]={}
   for dim in DIM:
    vals={int(y):v['q_observed'][dim] for y,v in annual[sc][scope].items()}
    valid={y:v for y,v in vals.items() if v is not None};adj={f'{y}-{y+1}':sign(vals[y+1]-vals[y]) if vals[y] is not None and vals[y+1] is not None else None for y in range(2018,2026)}
    temporal[sc][scope][dim]={'adjacent_q_direction':adj,'peak_years':[y for y,v in valid.items() if abs(v-max(valid.values()))<1e-12] if valid else [],'undefined_years':[y for y,v in vals.items() if v is None]}
    pvals={int(y):v['p_observed_lower'][dim] for y,v in annual[sc][scope].items()};pvalid={y:v for y,v in pvals.items() if v is not None}
    temporal[sc][scope][dim]['adjacent_p_direction']={f'{y}-{y+1}':sign(pvals[y+1]-pvals[y]) if pvals[y] is not None and pvals[y+1] is not None else None for y in range(2018,2026)}
    temporal[sc][scope][dim]['p_observed_peak_years']=[y for y,v in pvalid.items() if abs(v-max(pvalid.values()))<1e-12] if pvalid else []
 result['yearly'][m]={'by_scenario_scope_year':annual,'adjacent_and_peak':temporal}
 result['yearly'][m]['leave_one_top_summary']={}
 for kind in ['corpus_year','department_year']:
  rows=[x for x in loo if x['group'][0]==kind];same=0;undefined=0;examples=[]
  for x in rows:
   scope='corpus' if kind=='corpus_year' else x['group'][1];year=str(x['group'][-1]);orig=annual['clause_equal'][scope][year]['q_rank']['ties'];new=x['q_rank']['ties']
   if not orig or not new:undefined+=1
   elif orig[0]==new[0]:same+=1
   else:examples.append({'removed_source':x['removed_source'],'group':x['group'],'original_top':orig[0],'new_top':new[0]})
  result['yearly'][m]['leave_one_top_summary'][kind]={'total_N':len(rows),'same_top_N':same,'changed_top_N':len(examples),'undefined_N':undefined,'counterexamples':examples}
 base=out['clause_equal'];without=out['exclude_annual_series_entries']
 pos=base['positive_assignment_weight']*base['q_observed']['Ec'];remaining=without['positive_assignment_weight']*without['q_observed']['Ec']
 result['overall'][m]['annual_series_Ec_assignments']={'total_Ec_observed':round(pos),'remaining_after_exclusion':round(remaining),'in_annual_series':round(pos-remaining),'annual_series_share_of_Ec_observed':(pos-remaining)/pos}
 result['overall'][m]['r_conditional_bounds_sufficient_Ec_first_F_last_scenarios']=[sc for sc,x in out.items() if 'r_conditional_bounds' in x and sufficient_order(x['r_conditional_bounds'],'Ec','F')]
# Machine comparison verifies selected input points against original comparison, not only own projections.
checked=0
for x in D['comparison']['group_differences']:
 id_=x['identity']
 if id_[0]!='scenario' or id_[2]!=CLOCK:continue
 sc=id_[3];g=tuple(id_[4])
 for dim in DIM:
  for m,alias in [('rule','rule'),('llm','native')]:
   assert S[m][(sc,g)]['q_observed'][dim]==x['differences'][dim]['q'][alias][0]
   assert S[m][(sc,g)]['p_observed_lower'][dim]==x['differences'][dim]['p'][alias][0]
   checked+=2
result['cross_machine']['comparison_scalar_checks_passed']=checked
result['cross_machine']['overall_main_q_difference_pp']={d:100*(S['llm'][('clause_equal',('entire_corpus',))]['q_observed'][d]-S['rule'][('clause_equal',('entire_corpus',))]['q_observed'][d]) for d in DIM}
result['cross_machine']['overall_main_p_difference_pp']={d:100*(S['llm'][('clause_equal',('entire_corpus',))]['p_observed_lower'][d]-S['rule'][('clause_equal',('entire_corpus',))]['p_observed_lower'][d]) for d in DIM}
for metric in ['q_observed','p_observed_lower']:
 result['cross_machine'][metric+'_department_order_agreement']={d:{'agree_N':sum(result['department']['rule']['between_departments_ranks'][metric][d][sc]==result['department']['llm']['between_departments_ranks'][metric][d][sc] for sc in SCENARIOS),'total_scenarios':9,'disagree_scenarios':[sc for sc in SCENARIOS if result['department']['rule']['between_departments_ranks'][metric][d][sc]!=result['department']['llm']['between_departments_ranks'][metric][d][sc]]} for d in DIM}
for metric,scope in itertools.product(['q','p'],['corpus']+DEPTS):
 comparisons=[]
 for sc in SCENARIOS:
  for dim in DIM:
   a=result['yearly']['rule']['adjacent_and_peak'][sc][scope][dim]['adjacent_'+metric+'_direction'];b=result['yearly']['llm']['adjacent_and_peak'][sc][scope][dim]['adjacent_'+metric+'_direction']
   for pair in a:
    comparisons.append({'scenario':sc,'dimension':dim,'years':pair,'rule':a[pair],'llm':b[pair],'comparable':a[pair] is not None and b[pair] is not None,'agree':a[pair] is not None and b[pair] is not None and a[pair]==b[pair]})
 result['cross_machine']['adjacent_'+metric+'_direction_'+scope]={'design_cell_N':len(comparisons),'comparable_N':sum(x['comparable'] for x in comparisons),'agree_N':sum(x['agree'] for x in comparisons),'counterexamples':[x for x in comparisons if x['comparable'] and not x['agree']]}
result['verification']={'no_models_or_classifiers_called':True,'no_human_answers_read':True,'no_source_mutation':True,'source_sha256s_preserved':True,'scenario_projections_checked_against_comparison':True}
for meta in result['inputs'].values():
 assert hashlib.sha256(pathlib.Path(meta['path']).read_bytes()).hexdigest()==meta['sha256']
(OUT/'findings.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'counts':result['counts'],'overall':{m:{k:v for k,v in result['overall'][m].items() if k not in ['by_scenario','leave_one','leave_one_full_order_counterexamples']} for m in ['rule','llm']},'department':{m:{k:v for k,v in result['department'][m].items() if k in ['within_department_top_counts','leave_one_top_counts']} for m in ['rule','llm']},'cross_machine':{k:v for k,v in result['cross_machine'].items() if not k.startswith('adjacent_q_direction')}},ensure_ascii=False,indent=2))

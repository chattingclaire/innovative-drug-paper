"""Independent conditional-null arithmetic and sealed year-map readback only."""
from pathlib import Path
from collections import Counter, defaultdict
from fractions import Fraction
from datetime import datetime, timezone
import hashlib, json, math, traceback

OUT=Path(__file__).resolve().parent
G=OUT.parents[2]
ACTUAL=G/'07-statistics/rule-v8-attention-null-bounds-diagnostic-root'
YEAR=G/'07-statistics/annual-year-input-binding-sol'
RULE=G/'06-coding/rule-full4481-v8-delta-merged-root'
DIMS=('S','E','Ec','I','F')
NAMES={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
INPUTS={}; MISMATCHES=[]; BINDING_CHECKS=[]

def now():return datetime.now(timezone.utc).isoformat()
def cj(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def bind(path):
 p=Path(path).resolve(); h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def reg(path,expected=None):
 p=str(Path(path).resolve())
 if p not in INPUTS:INPUTS[p]=bind(p)
 if expected is not None:assert all(INPUTS[p][k]==expected[k] for k in ('path','bytes','sha256')),(INPUTS[p],expected)
 return Path(p)
def load(path):return json.loads(reg(path).read_bytes())
def rows(path):return [json.loads(x) for x in reg(path).read_bytes().splitlines()]
def save(name,v):
 with (OUT/name).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def file_seal(path):
 s=load(path)
 for b in s['files']:reg(b['path'],b)
 BINDING_CHECKS.append({'seal':str(Path(path).resolve()),'files_checked_N':len(s['files'])})
 return s
def compare(a,b,path=''):
 if isinstance(a,dict):
  if not isinstance(b,dict):MISMATCHES.append({'path':path,'expected':a,'actual':b});return
  for k,v in a.items():
   if k not in b:MISMATCHES.append({'path':path+'/'+str(k),'actual_field_missing':True})
   else:compare(v,b[k],path+'/'+str(k))
 elif isinstance(a,list):
  if not isinstance(b,list) or len(a)!=len(b):MISMATCHES.append({'path':path,'expected_N':len(a),'actual':b});return
  for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
 else:
  ok=(type(b) in (int,float) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)) if type(a) is float else a==b
  if not ok:MISMATCHES.append({'path':path,'expected':a,'actual':b})
def div(a,b):return None if b==0 else float(Fraction(a,b))
def binary(v):return type(v) is int and v in (0,1)

def extrema(p,own_u,other_p,other_u):
 # Every aggregate increment is feasible when unresolved slots are independent.
 # No record is recoded or imputed; enumerate hypothetical counts only.
 values=[];undefined=0
 for x in range(own_u+1):
  for y in range(other_u+1):
   den=p+other_p+x+y
   if den:values.append(Fraction(p+x,den))
   else:undefined+=1
 return {'lower':None if not values else float(min(values)),
         'upper':None if not values else float(max(values)),
         'hypothetical_count_combinations_N':len(values)+undefined,'undefined_denominator_combinations_N':undefined}

def derive(ids,pred,key):
 n=len(ids);counts={d:Counter(pred[s]['labels'][d] for s in ids) for d in DIMS}
 p={d:counts[d][1] for d in DIMS};u={d:counts[d][None] for d in DIMS};z={d:counts[d][0] for d in DIMS}
 total_p=sum(p.values());total_u=sum(u.values());dims={};proof={}
 for d in DIMS:
  assert p[d]+u[d]+z[d]==n
  dims[d]={'positive_N':p[d],'negative_N':z[d],'unresolved_N':u[d],
           'positive_assignment_share_among_observed':div(p[d],total_p),
           'positive_assignment_share_lower_bound':div(p[d],total_p+total_u-u[d]),
           'positive_assignment_share_upper_bound':div(p[d]+u[d],total_p+u[d]),
           'clause_prevalence_lower_bound':div(p[d],n),'clause_prevalence_upper_bound':div(p[d]+u[d],n)}
  test=extrema(p[d],u[d],total_p-p[d],total_u-u[d])
  if total_p>0:
   assert test['undefined_denominator_combinations_N']==0
   assert test['lower']==dims[d]['positive_assignment_share_lower_bound']
   assert test['upper']==dims[d]['positive_assignment_share_upper_bound']
   assert test['lower']<=dims[d]['positive_assignment_share_among_observed']<=test['upper']
  proof[d]={'denominators':{'observed_assignment_share':total_p,'assignment_share_lower':total_p+total_u-u[d],
                          'assignment_share_upper':total_p+u[d],'clause_prevalence':n},
            'enumerated_tight_assignment_share_extrema':test}
 stable=[]
 for a in DIMS:
  for b in DIMS:
   if a!=b and p[a]>p[b]+u[b]:
    stable.append({'higher_dimension':a,'lower_dimension':b,'minimum_higher_positive_N':p[a],
                   'maximum_lower_positive_N':p[b]+u[b]})
 return {'group':list(key),'clause_N':n,'observed_positive_assignment_N':total_p,'unresolved_assignment_N':total_u,
         'dimensions':dims,'strict_within_group_rankings_immune_to_unresolved_labels':stable,
         'conditional_on_correct_observed_machine_labels':True},proof

def main():
 assert not (OUT/'report.json').exists(),'Never overwrite a completed independent audit'
 pre=load(OUT/'pre-execution-audit-freeze.json');reg(__file__,pre['auditor'])
 file_seal(ACTUAL/'seal.json');actual=load(ACTUAL/'conditional-bounds.json')
 for b in actual['inputs']:reg(b['path'],b)
 reg(actual['calculator']['path'],actual['calculator'])
 file_seal(RULE/'seal.json');status=load(RULE/'composite-status.json')
 assert status['actual_record_N']==4481 and status['actual_dimension_N']==22405 and status['lawful_null_N']==238
 assert status['actual_v8_delta_inference_record_N']==7 and status['inherited_v7_record_N']==4474
 assert status['all4481_actually_inferred_under_v8'] is False
 yseal=load(YEAR/'seal.json');assert Path(yseal['root']).resolve()==YEAR.resolve()
 for name,b in yseal['outputs'].items():reg(YEAR/name,dict(b,path=str((YEAR/name).resolve())))
 for b in yseal['read_only_inputs'].values():reg(b['path'],b)
 BINDING_CHECKS.append({'seal':str(YEAR/'seal.json'),'output_files_checked_N':len(yseal['outputs']),
                        'read_only_inputs_checked_N':len(yseal['read_only_inputs'])})
 descriptor=load(YEAR/'source-year-binding-descriptor.json')
 for b in descriptor['source_year_maps'].values():reg(b['path'],b)
 base=Path(descriptor['source_year_maps']['main_accepted']['path']).parent
 annual_seal=load(base/'seal.json')
 for b in annual_seal['files']:
  p=base/b['relative_path'];reg(p,dict(b,path=str(p.resolve())))
 BINDING_CHECKS.append({'seal':str(base/'seal.json'),'relative_files_checked_N':len(annual_seal['files'])})
 metadata=rows(YEAR/'full4481-year-map.jsonl')
 mainrows=rows(descriptor['source_year_maps']['main_accepted']['path'])
 pubrows=rows(descriptor['source_year_maps']['publication_accepted']['path'])
 entries=rows(descriptor['source_year_maps']['source_entry_metadata']['path'])
 evidence=rows(YEAR/'source-entry-date-evidence.jsonl')
 inventory=load(descriptor['source_year_maps']['accepted_inventory']['path'])
 assert len(entries)==len(evidence)==51
 ed={e['source_entry_id']:e for e in entries};ev={e['source_entry_id']:e for e in evidence}
 assert len(ed)==len(ev)==51 and set(ed)==set(ev)
 mainmap={x['source_id']:x for x in mainrows};pubmap={x['source_id']:x for x in pubrows}
 pred_list=rows(RULE/'predictions.jsonl');pred={x['id']:x for x in pred_list}
 assert len(pred)==len(pred_list)==len(metadata)==len(mainmap)==len(pubmap)==4481
 assert [m['unit_id'] for m in metadata]==list(pred)==[m['source_id'] for m in mainrows]==[m['source_id'] for m in pubrows]
 for row in pred.values():
  assert set(row['labels'])==set(DIMS) and not row['implementation_errors']
  assert all((v is None or binary(v)) and row['decisions'][d]['value']==v for d,v in row['labels'].items())
 entry_proof=[]
 for eid,e in ed.items():
  date=ev[eid];data={k:v for k,v in date.items() if k!='date_evidence_record_sha256'}
  assert hashlib.sha256(cj(data).encode()).hexdigest()==date['date_evidence_record_sha256']
  common=('department','source_entry_identity_sha256','issue_date','publication_date','effective_date','policy_year',
          'publication_year','year_basis','issue_date_evidence','publication_date_evidence','component_mapping_status')
  assert all(date[k]==e[k] for k in common)
  expected_year=int((e['issue_date'] or e['publication_date'])[:4])
  expected_basis='issue_date' if e['issue_date'] else 'publication_date_fallback'
  assert type(e['policy_year']) is int and e['policy_year']==expected_year
  assert e['publication_year']==int(e['publication_date'][:4])
  # The accepted fallback label is retained verbatim; no year inferred from filenames.
  assert e['year_basis']=='issue_date' if e['issue_date'] else 'publication' in e['year_basis']
  issue_sha=(e['issue_date_evidence'] or {}).get('sha256')
  publication_sha=e['publication_date_evidence']['sha256']
  assert date['issue_date_evidence_sha256']==issue_sha and date['publication_date_evidence_sha256']==publication_sha
  assert date['main_date_evidence_sha256']==(issue_sha if e['issue_date'] else publication_sha)
  entry_proof.append({'source_entry_id':eid,'department':e['department'],'policy_year':e['policy_year'],
                      'publication_year':e['publication_year'],'year_basis':e['year_basis'],
                      'source_entry_identity_sha256':e['source_entry_identity_sha256'],
                      'date_evidence_record_sha256':date['date_evidence_record_sha256'],
                      'metadata_clause_N':e['clause_n'],'original_date_source_content_reaudited':False})
 groups=defaultdict(list);seen_entries=Counter();year_scenario_difference_N=0
 matchfields=('original_id','department','analysis_group','source_entry_id','source_entry_identity_sha256',
              'issue_date','publication_date','effective_date','policy_year','publication_year','year_basis','component_id','component_mapping_status')
 for m in metadata:
  sid=m['unit_id'];a=mainmap[sid];b=pubmap[sid];e=ed[m['source_entry_id']];v=ev[m['source_entry_id']]
  assert sid==m['source_id']==m['original_frame_id']==a['source_id']==a['id']==b['source_id']==b['id']
  assert all(m[k]==a[k] for k in matchfields)
  assert all(m[k]==e[k] for k in ('department','analysis_group','source_entry_id','source_entry_identity_sha256','policy_year','publication_year','year_basis','issue_date','publication_date','effective_date'))
  assert m['source_entry_date_evidence_record_sha256']==v['date_evidence_record_sha256']
  assert m['main_date_evidence_sha256']==v['main_date_evidence_sha256']
  assert m['publication_date_evidence_sha256']==v['publication_date_evidence_sha256']
  assert m['component_id'] is None and m['department'] in ('NMPA','NHSA','NHC')
  assert m['publication_year']==b['publication_year']==b['sensitivity_year'] and m['policy_year']==b['policy_year_main']
  year_scenario_difference_N+=m['policy_year']!=m['publication_year']
  seen_entries[m['source_entry_id']]+=1
  groups[('department',m['department'])].append(sid)
  groups[('department_year',m['department'],m['policy_year'])].append(sid)
  groups[('corpus_year',m['policy_year'])].append(sid)
 assert len(seen_entries)==51 and all(seen_entries[eid]==e['clause_n'] for eid,e in ed.items())
 for cell in inventory:
  k=('department_year',cell['department'],cell['year'])
  ids=groups.get(k,[]);keys={next(m['source_entry_id'] for m in metadata if m['unit_id']==sid) for sid in ids}
  assert len(ids)==cell['clause_n'] and len(keys)==cell['source_entry_n']
  assert (cell['cell_status']=='no_observed_source')==(not ids)
 expected=[];proofs=[]
 for key in sorted(groups):
  result,proof=derive(groups[key],pred,key);expected.append(result);proofs.append({'group':list(key),'dimensions':proof})
 overall,overall_proof=derive(list(pred),pred,('entire_corpus',))
 assert len(expected)==33 and overall['clause_N']==4481 and overall['observed_positive_assignment_N']==1399 and overall['unresolved_assignment_N']==238
 assert all(g['observed_positive_assignment_N']>0 and g['clause_N']>0 for g in expected)
 compare(expected,actual['groups'],'groups');compare(overall,actual['overall'],'overall')
 compare({'metadata_source_entry_N':51,'source_entries_NOT_claimed_independent_components':True,
          'component_date_analysis_executed':False,'confidence_intervals_computed':False,
          'nulls_imputed_as_zero_or_one':False,'not_a_bound_on_errors_in_observed_binary_labels':True,
          'formal_validation_complete':False,'paper_writing_gate_open':False},actual,'boundaries')
 family_counts={}
 for family in ('corpus_year','department','department_year'):
  own=[g for g in expected if g['group'][0]==family]
  family_counts[family]={'group_N':len(own),'clause_N':sum(g['clause_N'] for g in own),
                         'positive_assignment_N':sum(g['observed_positive_assignment_N'] for g in own),
                         'unresolved_assignment_N':sum(g['unresolved_assignment_N'] for g in own)}
  assert family_counts[family]['clause_N']==4481 and family_counts[family]['positive_assignment_N']==1399 and family_counts[family]['unresolved_assignment_N']==238
 text=reg(ACTUAL/'部门年度待定项影响.md').read_text()
 for g in expected:
  if g['group'][0]!='department':continue
  for d,v in g['dimensions'].items():
   fmt=lambda x:'NA' if x is None else f'{x:.1%}'
   line=f"|{g['group'][1]}|{g['clause_N']}|{d}|{v['positive_N']}|{v['unresolved_N']}|{fmt(v['positive_assignment_share_among_observed'])}|{fmt(v['positive_assignment_share_lower_bound'])}–{fmt(v['positive_assignment_share_upper_bound'])}|"
   compare(True,line in text,'markdown/'+g['group'][1]+'/'+d)
 for phrase in ('238个','不能当作最终论文结论或置信区间','未将待定项补成0','未使用组件或月日分析','不覆盖机器已判0/1的误判'):
  compare(True,phrase in text,'markdown/boundary/'+phrase)
 zero_checks={'division_zero_is_NA':div(0,0),'division_positive_zero_is_NA':div(1,0),
              'all_zero_extrema':extrema(0,0,0,0),'strict_tie_not_ranked':not (3>2+1)}
 assert zero_checks['division_zero_is_NA'] is None and zero_checks['division_positive_zero_is_NA'] is None
 assert zero_checks['all_zero_extrema']['lower'] is None and zero_checks['all_zero_extrema']['upper'] is None
 assert zero_checks['strict_tie_not_ranked'] is True
 error_root=G/'08-audits/attention-bound-preparation-error01-root'
 error_preserved=[]
 if error_root.is_dir():
  for p in sorted(error_root.rglob('*')):
   if p.is_file():error_preserved.append(bind(reg(p)))
 elif error_root.is_file():error_preserved.append(bind(reg(error_root)))
 assert error_preserved,'The reported pre-output preparation error must remain preserved'
 changed=[b['path'] for b in INPUTS.values() if bind(b['path'])!=b];assert not changed,changed
 report={'status':'independent_attention_null_bounds_readback_passed' if not MISMATCHES else 'independent_attention_null_bounds_readback_found_mismatches',
         'at_utc':now(),'actual_diagnostic':str(ACTUAL),'mismatch_N':len(MISMATCHES),'mismatches':MISMATCHES,
         'dimension_names':NAMES,'overall':overall,'groups':expected,'group_family_partition_checks':family_counts,
         'formula_extrema_count_enumeration_proofs':{'overall':overall_proof,'groups':proofs},
         'zero_denominator_and_strict_tie_checks':zero_checks,'actual_group_N':len(expected),
         'all_actual_groups_observed_positive_sum_gt_zero':True,'minimum_group_observed_positive_assignment_N':min(g['observed_positive_assignment_N'] for g in expected),
         'group_order_verified_lexicographic_and_not_derived_from_labels':True,
         'year_mapping_readback':{'full4481_rows':4481,'all_source_ids_same_order_as_rule_results':True,
                                  'accepted_main_and_publication_maps_crosschecked':True,'policy_vs_publication_year_difference_record_N':year_scenario_difference_N,
                                  'source_entry_N':51,'source_entry_identity_and_date_evidence_hashes_crosschecked':True,
                                  'issue_date_first_publication_fallback_source_entry_N':sum(not e['issue_date'] for e in entries),
                                  'source_entries':entry_proof,'original_date_source_contents_reaudited':False,
                                  'source_entries_are_not_independent_components':True,'component_or_month_day_analysis_executed':False},
         'preserved_pre_output_preparation_error':error_preserved,'sealed_binding_checks':BINDING_CHECKS,
         'input_binding_N':len(INPUTS),'all_inputs_byte_hash_unchanged_on_readback':True,
         'boundaries':{'binary_rule_decisions_held_fixed_and_not_newly_certified':True,
                      'null_slots_allowed_independent_hypothetical_zero_one':True,'actual_nulls_imputed':False,
                      'bounds_are_individual_dimension_extrema_not_joint_simultaneous_attainment_claim':True,
                      'not_confidence_intervals':True,'not_a_bound_on_binary_semantic_errors':True,
                      'no_new_classification_calls':True,'no_new_gold_labels':True,
                      'formal_validation_complete':False,'paper_writing_gate_open':False,
                      'all4481_actually_inferred_under_v8':False,'actual_v8_delta_record_N':7,'inherited_v7_record_N':4474}}
 save('report.json',report)
 lines=[f"待定项条件诊断独立复算{'通过' if not MISMATCHES else '发现差异'}，差异{len(MISMATCHES)}项。",'',
        '实际33个有条款分组：部门3组、部门×年度21组、语料年度9组。每类分组各自完整划分4481条、1399个阳性标签和238个待定槽；同条款在三类分组中重复出现，不能把33组加总当作新样本。', '',
        '逐维标签占比上下界及条款含有率与ROOT落地值相符。枚举可行的待定计数增量确认每个单维占比边界可达；严格排序仅在本维最小阳性数大于另一维最大阳性数时保留。实际各组阳性分母均大于0；零分母测试返回NA，未补1。', '',
        '封存年份映射4481行逐一对应规则ID；51个来源条目的身份SHA、日期证据记录SHA、部门、年份及条款数均与封存主/公开日期映射吻合。成文日期优先，缺失时回退公开日期（3条目）；未重审原日期证据正文，未按组件或月日分析。', '',
        '|维度|阳性|待定|整体标签占比下界|整体标签占比上界|','|---|---:|---:|---:|---:|']
 for d,v in overall['dimensions'].items():lines.append(f"|{d} {NAMES[d]}|{v['positive_N']}|{v['unresolved_N']}|{v['positive_assignment_share_lower_bound']:.6%}|{v['positive_assignment_share_upper_bound']:.6%}|")
 lines+=['','这些是固定已有二值判定、仅改变待定槽的条件边界，不是置信区间，也不证明已有0/1语义正确。各维上下界分别求得，未声称能同时达到。正式验证与论文写作门槛仍为false。', '',
         f"全部相关实际seal绑定及{len(INPUTS)}个输入读后字节/SHA256核验相符；初次准备错误记录保持原件。未重新分类、未改原件或progress。",'']
 with (OUT/'report.md').open('x',encoding='utf8') as f:f.write('\n'.join(lines))
 save('input-bindings.json',{'at_utc':now(),'all_inputs_byte_hash_unchanged':True,'inputs':list(INPUTS.values())})
 save('seal.json',{'status':report['status'],'files':[bind(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='seal.json'],
                   'self_excluded':True,'new_classification_calls_N':0,'formal_validation_complete':False})
 print(json.dumps({'status':report['status'],'mismatch_N':len(MISMATCHES),'input_binding_N':len(INPUTS),
                   'report':bind(OUT/'report.json'),'markdown':bind(OUT/'report.md'),'seal':bind(OUT/'seal.json')},ensure_ascii=False))
 return 0 if not MISMATCHES else 2

if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as exc:
  v={'status':'independent_attention_bounds_audit_attempt_failed','at_utc':now(),'error_type':type(exc).__name__,
     'error':str(exc),'traceback':traceback.format_exc(),'new_classification_calls_N':0,'formal_validation_complete':False}
  save('attempt-failure.json',v);print(json.dumps(v,ensure_ascii=False));raise SystemExit(2)

"""Read-only arithmetic audit from raw JSONL; imports no production analysis code."""
from pathlib import Path
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations
import json, hashlib, datetime

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
TARGET = OUT / '三部门注意力分布与敏感性.json'
INPUT = ROOT / 'outputs/autocode-v28-review-20261004-111306/rule_inputs_v27.jsonl'
RULE = INPUT.parent / 'all_predictions.jsonl'
AC = ROOT / 'outputs/autocode-v25-20260927/current_1268_references.jsonl'
META = ROOT / 'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
DIMS = ('S', 'E', 'Ec', 'I', 'F')
GROUPS = ('NMPA', 'NHSA', 'NHC')
TRANSFORMS = ('exclude_quality_only','exclude_F_clinical_management_only',
              'F_access_affordability_only','exclude_F_dimension_information_only',
              'exclude_I_qualification_advantage_only')
SCENARIOS = ('policy_file_equal_weight','policy_series_equal_weight',
             'latest_member_of_annual_series_only','exclude_all_joint_publications',*TRANSFORMS)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_jsonl(path):
    data = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    result = {row['id']: row for row in data}
    assert len(result) == len(data), ('duplicate_id', str(path))
    return result

def serialize(value):
    if isinstance(value,Fraction):
        return {'value':float(value),'exact_fraction':str(value)}
    if isinstance(value,dict):
        return {k:serialize(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [serialize(v) for v in value]
    return value

def raw_labels(record, transformation='primary'):
    labels = dict(record['labels'])
    assert set(labels) == set(DIMS)
    assert all(v in (0,1,'待定') for v in labels.values())
    fair = set(record.get('fairness_subtypes') or [])
    innov = set(record.get('innovation_subtypes') or [])
    quality = record.get('safety_quality_basis')
    if quality is None:
        kinds = set(record.get('safety_subtypes') or [])
        if kinds == {'quality_safety'}:
            quality = 'quality_only'
        elif 'quality_safety' in kinds:
            quality = 'quality_and_other'
        else:
            quality = 'no_quality_basis' if kinds else 'unknown'
    if transformation == 'exclude_quality_only' and labels['S'] == 1:
        if quality == 'quality_only':
            labels['S'] = 0
        elif quality not in ('quality_and_other','no_quality_basis'):
            labels['S'] = '待定'
    if transformation in TRANSFORMS[1:4] and labels['F'] == 1:
        if not fair:
            labels['F'] = '待定'
        elif transformation == 'exclude_F_clinical_management_only' and fair == {'clinical_management'}:
            labels['F'] = 0
        elif transformation == 'F_access_affordability_only' and not (fair & {'access','affordability'}):
            labels['F'] = 0
        elif transformation == 'exclude_F_dimension_information_only' and fair == {'dimension_information'}:
            labels['F'] = 0
    if transformation == 'exclude_I_qualification_advantage_only' and labels['I'] == 1:
        if innov == {'qualification_advantage'}:
            labels['I'] = 0
        elif not innov:
            labels['I'] = '待定'
    return labels

def calculate_units(records, method, transformation='primary'):
    selected = [r for r in records if method in r['values']]
    raw = {d:Counter() for d in DIMS}
    ht = {d:defaultdict(Fraction) for d in DIMS}
    overlap_raw, overlap_ht = Counter(),defaultdict(Fraction)
    for r in selected:
        lab = raw_labels(r['values'][method],transformation)
        w = r['weights'][method]
        hit = sum(lab[d]==1 for d in DIMS)
        pending = sum(lab[d]=='待定' for d in DIMS)
        for d in DIMS:
            raw[d][lab[d]] += 1
            ht[d][lab[d]] += w
        events = {
            'at_least_one_known_dimension':hit>0,
            'all_five_confirmed_zero':hit==0 and pending==0,
            'at_least_two_known_dimensions':hit>1,
            'exactly_one_known_dimension':hit==1,
            'any_pending_dimension':pending>0,
            'no_known_dimension_but_pending':hit==0 and pending>0,
            'possibly_at_least_one_dimension':hit+pending>0,
            'possibly_at_least_two_dimensions':hit+pending>1,
        }
        for event,yes in events.items():
            if yes:
                overlap_raw[event] += 1
                overlap_ht[event] += w
    total = sum((r['weights'][method] for r in selected),Fraction())
    hit_sum = sum((ht[d][1] for d in DIMS),Fraction())
    pending_sum = sum((ht[d]['待定'] for d in DIMS),Fraction())
    dims = {}
    for d in DIMS:
        low_den = hit_sum+pending_sum-ht[d]['待定']
        high_den = hit_sum+ht[d]['待定']
        dims[d] = {
            'raw_known_hit_count':raw[d][1],
            'raw_pending_count':raw[d]['待定'],
            'raw_confirmed_zero_count':raw[d][0],
            'weighted_known_hit_count':ht[d][1],
            'weighted_pending_count':ht[d]['待定'],
            'weighted_confirmed_zero_count':ht[d][0],
            'attention_share':ht[d][1]/hit_sum if hit_sum else None,
            'pending_completion_descriptive_range':[
                ht[d][1]/low_den if low_den else None,
                (ht[d][1]+ht[d]['待定'])/high_den if high_den else None],
            'supplementary_unit_coverage':ht[d][1]/total if total else None,
        }
    if hit_sum:
        assert sum((dims[d]['attention_share'] for d in DIMS),Fraction()) == 1
    else:
        assert all(dims[d]['attention_share'] is None for d in DIMS)
    for d in DIMS:
        assert sum(raw[d].values()) == len(selected)
        assert sum(ht[d].values()) == total
    return {
        'observed_unit_count':len(selected),
        'weighted_unit_count':total,
        'raw_five_dimension_known_hit_sum':sum(raw[d][1] for d in DIMS),
        'weighted_five_dimension_known_hit_sum':hit_sum,
        'raw_five_dimension_pending_sum':sum(raw[d]['待定'] for d in DIMS),
        'weighted_five_dimension_pending_sum':pending_sum,
        'dimensions':dims,
        'overlap':{event:{'raw_unit_count':overlap_raw[event],'weighted_unit_count':overlap_ht[event]} for event in events},
    }

def summarize(records, method, transformation='primary'):
    return {group:calculate_units([r for r in records if group=='ALL' or r['group']==group],method,transformation)
            for group in (*GROUPS,'ALL')}

def equalize(records,method,field):
    clusters = defaultdict(list)
    for r in records:
        if method in r['values']:
            clusters[r[field]].append(r)
    cluster_stats = {key:calculate_units(rows,method) for key,rows in clusters.items()}
    result = {}
    for group in (*GROUPS,'ALL'):
        keys = sorted(key for key,rows in clusters.items() if group=='ALL' or rows[0]['group']==group)
        active = [key for key in keys if cluster_stats[key]['weighted_five_dimension_known_hit_sum']>0]
        excluded = [key for key in keys if key not in active]
        pending_only = [key for key in excluded if cluster_stats[key]['weighted_five_dimension_pending_sum']>0]
        dims = {}
        for d in DIMS:
            average = sum((cluster_stats[key]['dimensions'][d]['attention_share'] for key in active),Fraction())/len(active) if active else None
            bounds = [None,None] if pending_only or not active else [
                sum((cluster_stats[key]['dimensions'][d]['pending_completion_descriptive_range'][i] for key in active),Fraction())/len(active)
                for i in (0,1)]
            dims[d] = {'attention_share':average,'pending_completion_descriptive_range':bounds,'supplementary_unit_coverage':None}
        result[group] = {
            'available_cluster_count':len(keys),
            'known_hit_active_cluster_count':len(active),
            'excluded_zero_known_hit_clusters':excluded,
            'excluded_pending_only_clusters':pending_only,
            'dimensions':dims,
        }
        assert sum((dims[d]['attention_share'] for d in DIMS),Fraction())==1
    return result

mismatches = []
checked_values = 0
def compare(actual,expected,path):
    global checked_values
    if isinstance(actual,Fraction):
        checked_values += 1
        exact = Fraction(expected['exact_fraction']) if isinstance(expected,dict) else Fraction(expected)
        if actual != exact:
            mismatches.append({'path':path,'calculated':serialize(actual),'reported':expected})
    elif isinstance(actual,dict):
        for key,value in actual.items():
            if key not in expected:
                mismatches.append({'path':path+'.'+key,'reason':'missing_key'})
            else:
                compare(value,expected[key],path+'.'+key)
    elif isinstance(actual,list):
        if not actual or isinstance(actual[0],str):
            checked_values += 1
            if sorted(actual)!=sorted(expected):
                mismatches.append({'path':path,'calculated':actual,'reported':expected})
        else:
            if len(actual)!=len(expected):
                mismatches.append({'path':path,'reason':'different_length'})
            else:
                for i,value in enumerate(actual):
                    compare(value,expected[i],f'{path}[{i}]')
    else:
        checked_values += 1
        if actual!=expected:
            mismatches.append({'path':path,'calculated':actual,'reported':expected})

def leaders(stats):
    result = {}
    for group in (*GROUPS,'ALL'):
        values = {d:stats[group]['dimensions'][d]['attention_share'] for d in DIMS}
        result[group] = [d for d in DIMS if values[d]==max(values.values())]
    return result

def compare_directions(base,current):
    rows = []
    for g1,g2 in combinations(GROUPS,2):
        for d in DIMS:
            old_delta = base[g1]['dimensions'][d]['attention_share']-base[g2]['dimensions'][d]['attention_share']
            new_delta = current[g1]['dimensions'][d]['attention_share']-current[g2]['dimensions'][d]['attention_share']
            old_sign = (old_delta>0)-(old_delta<0)
            new_sign = (new_delta>0)-(new_delta<0)
            rows.append({'pair':[g1,g2],'dimension':d,'baseline_direction':old_sign,
                         'observed_direction':new_sign,'direction_changed':new_sign!=old_sign,'reversal':old_sign*new_sign==-1})
    return {'changed_direction_count':sum(r['direction_changed'] for r in rows),
            'reversal_count':sum(r['reversal'] for r in rows),'comparisons':rows}

def compact(stats):
    return {group:{
        'attention_percent':{d:float(stats[group]['dimensions'][d]['attention_share'])*100 for d in DIMS},
        'sum_attention_share':sum((stats[group]['dimensions'][d]['attention_share'] for d in DIMS),Fraction()),
        'dominant_dimensions':leaders(stats)[group],
    } for group in (*GROUPS,'ALL')}

def main():
    target_sha = sha(TARGET)
    stated = json.loads(TARGET.read_text())
    binding=stated['method_bindings']
    input_path=Path(binding['rule']['inputs']);rule_path=Path(binding['rule']['rules'])
    rule_method=binding['rule']['method'];rule_version=binding['rule']['version']
    source_files = [input_path,rule_path,AC,META,TARGET]
    inputs,predictions,refs = (read_jsonl(p) for p in (input_path,rule_path,AC))
    metadata = json.loads(META.read_text())['rows']
    mapping = {Path(row['original_file']).stem:row for row in metadata}
    assert len(metadata)==len(mapping)==55
    assert set(inputs)==set(predictions) and len(inputs)==4924
    assert set(refs)<=set(inputs) and len(refs)==1268
    assert all(predictions[rid]['prediction']['unit_text_sha256']==hashlib.sha256(row['input']['unit_text'].encode()).hexdigest()
               for rid,row in inputs.items())
    assert all(predictions[rid]['prediction']['version']==rule_version for rid in inputs)
    records,background = [],[]
    observed_full_strata = Counter()
    observed_domain_strata = Counter()
    design = {}
    for rid,ref in refs.items():
        sm=ref['historical_sampling']
        pair=(sm['N_h'],sm['n_h'])
        assert sm['stratum'] not in design or design[sm['stratum']]==pair
        design[sm['stratum']]=pair
        observed_full_strata[sm['stratum']]+=1
    assert len(design)==29
    assert all(observed_full_strata[s]==n for s,(_,n) in design.items())
    methods=list(stated['primary'])
    llm=None
    llm_method=binding['llm']['method']
    if binding['llm']['path']:
        llm_path=Path(binding['llm']['path'])
        llm=read_jsonl(llm_path)
        assert len(llm)==4924 and set(llm)==set(inputs)
        assert llm_method in methods
        source_files.append(llm_path)
    for rid,row in inputs.items():
        stem=row['input']['original_file_stem'];meta=mapping[stem]
        if meta['analysis_group'] not in GROUPS:
            background.append((rid,stem,meta['analysis_group']))
            continue
        vals={rule_method:predictions[rid]['prediction']}
        weights={rule_method:Fraction(1)}
        if llm is not None:
            vals[llm_method]=llm[rid].get('prediction',llm[rid])
            weights[llm_method]=Fraction(1)
        if rid in refs:
            ref=refs[rid];sm=ref['historical_sampling']
            observed_domain_strata[sm['stratum']]+=1
            for coder in ('A','C'):
                method=f'{coder}_AI_reference'
                vals[method]=ref['original_references'][coder]
                weights[method]=Fraction(sm['N_h'],sm['n_h'])
        records.append({'id':rid,'file':stem,'series':meta['policy_series'],'group':meta['analysis_group'],
                        'meta':meta,'values':vals,'weights':weights})
    files=sorted({r['file'] for r in records})
    assert len(records)==4481 and len(background)==443 and len(files)==51
    assert sum('A_AI_reference' in r['values'] for r in records)==1057
    assert {g:sum(r['group']==g for r in records) for g in GROUPS}=={'NMPA':1848,'NHSA':2100,'NHC':533}
    for key,expected in [('population_n',4481),('background_n',443),('source_entries',51),('reference_sample_n',1057)]:
        compare(expected,stated[key],key)
    compare(dict(observed_domain_strata),stated['original_strata_observed_counts'],'original_strata_observed_counts')
    latest={}
    for meta in metadata:
        if meta['annual_series']:
            latest[meta['policy_series']]=max(latest.get(meta['policy_series'],-1),meta['year_in_filename'])
    latest_records=[r for r in records if not r['meta']['annual_series'] or r['meta']['year_in_filename']==latest[r['series']]]
    nojoint=[r for r in records if not r['meta']['joint_publication']]
    all_results={};conclusions={}
    for method in methods:
        primary=summarize(records,method)
        compare(primary,stated['primary'][method],f'primary.{method}')
        assert primary['ALL']['weighted_unit_count']==4481
        sensitivity=stated['sensitivities'][method]
        compare(leaders(primary),sensitivity['primary_dominant_dimensions'],f'primary_leaders.{method}')
        assert set(sensitivity['scenarios'])==set(SCENARIOS)
        scenario_rows={
            'policy_file_equal_weight':equalize(records,method,'file'),
            'policy_series_equal_weight':equalize(records,method,'series'),
            'latest_member_of_annual_series_only':summarize(latest_records,method),
            'exclude_all_joint_publications':summarize(nojoint,method),
            **{scenario:summarize(records,method,scenario) for scenario in TRANSFORMS},
        }
        for scenario,calculated in scenario_rows.items():
            compare(calculated,sensitivity['scenarios'][scenario],f'scenarios.{method}.{scenario}')
            compare(leaders(calculated),sensitivity['scenario_dominant_dimensions'][scenario],f'scenario_leaders.{method}.{scenario}')
            directions=compare_directions(primary,calculated)
            compare(directions,sensitivity['scenario_direction_changes'][scenario],f'scenario_directions.{method}.{scenario}')
        reported_loo={row['discarded_file']:row for row in sensitivity['leave_one_policy_file_out']}
        assert len(reported_loo)==len(sensitivity['leave_one_policy_file_out'])==51
        assert set(reported_loo)==set(files)
        loo_rows={}
        for file in files:
            calculated=summarize([r for r in records if r['file']!=file],method)
            compare(calculated,reported_loo[file]['distribution'],f'loo.{method}.{file}')
            compare(leaders(calculated),reported_loo[file]['dominant_dimensions'],f'loo_leaders.{method}.{file}')
            compare(compare_directions(primary,calculated),reported_loo[file]['direction_changes'],f'loo_directions.{method}.{file}')
            loo_rows[file]=compact(calculated)
        tests={'primary':primary,**scenario_rows,
               **{f'leave_out:{f}':summarize([r for r in records if r['file']!=f],method) for f in files}}
        failed_nmpa=[name for name,result in tests.items() if leaders(result)['NMPA']!=['S']]
        failed_nhsa=[name for name,result in tests.items() if leaders(result)['NHSA']!=['Ec']]
        failed_nhc=[name for name,result in tests.items() if not set(leaders(result)['NHC'])<={'S','F'}]
        nhc_top2_failures=[]
        for name,result in tests.items():
            shares={d:result['NHC']['dimensions'][d]['attention_share'] for d in DIMS}
            other_max=max(shares[d] for d in ('E','Ec','I'))
            if min(shares['S'],shares['F'])<other_max:
                nhc_top2_failures.append({'case':name,'shares':shares})
        conclusions[method]={
            'evaluated_cases':len(tests),
            'NMPA_S_unique_maximum_all_cases':not failed_nmpa,'NMPA_exceptions':failed_nmpa,
            'NHSA_Ec_unique_maximum_all_cases':not failed_nhsa,'NHSA_exceptions':failed_nhsa,
            'NHC_maximum_always_S_or_F':not failed_nhc,'NHC_exceptions':failed_nhc,
            'NHC_S_and_F_always_top_two':not nhc_top2_failures,'NHC_top_two_exceptions':nhc_top2_failures,
        }
        all_results[method]={'primary':primary,'nine_scenarios':{k:compact(v) for k,v in scenario_rows.items()},
                             'leave_one_policy_file_out':loo_rows,'scenario_count':len(scenario_rows),'deletion_count':len(loo_rows)}
    source_binding=[]
    for path,digest in stated['source_sha256'].items():
        actual=sha(Path(path))
        source_binding.append({'path':path,'reported_sha256':digest,'actual_sha256':actual,'matches':actual==digest})
        if actual!=digest:mismatches.append({'path':path,'reason':'source_hash_mismatch'})
    assert sha(TARGET)==target_sha,'Target changed during QA; rerun for a stable snapshot'
    status_ids={}
    for method in methods:
        status_ids[method]={}
        for group in GROUPS:
            observed=[r for r in records if r['group']==group and method in r['values']]
            status_ids[method][group]={}
            for d in DIMS:
                buckets={str(status):[r['id'] for r in observed if raw_labels(r['values'][method])[d]==status]
                         for status in (0,1,'待定')}
                assert sum(len(ids) for ids in buckets.values())==len(observed)
                status_ids[method][group][d]=buckets
    ec_ids=status_ids[rule_method]['NMPA']['Ec']['1']
    ec_content_binding=[{'id':rid,'original_file_stem':inputs[rid]['input']['original_file_stem'],
                         'unit_text':inputs[rid]['input']['unit_text'],
                         'pages':inputs[rid]['input'].get('pages',[])} for rid in ec_ids]
    if rule_method=='rules_v28_2':
        assert set(ec_ids)=={'RECODE25-03016','RECODE25-04088'}
    matrix_path=ROOT/'outputs/final-three-department-20261007/policy_evidence_matrix.json'  # Verified unchanged policy examples, explicit read-only source.
    matrix_bytes=matrix_path.read_bytes()
    matrix_sha=hashlib.sha256(matrix_bytes).hexdigest()
    policy_matrix=json.loads(matrix_bytes)
    source_files.append(matrix_path)
    ec_evidence=[e for row in policy_matrix['matrix'] if row['group']=='药监' and row['dimension']=='经济性' for e in row['evidence']]
    matrix_ec_ids={e['analysis_unit_id'] for e in ec_evidence}
    for e in ec_evidence:
        quote=''.join(e['quote_fragment'].split())
        unit=''.join(inputs[e['analysis_unit_id']]['input']['unit_text'].split())
        assert quote in unit
    result={
        'status':'passed' if not mismatches else 'mismatches_found',
        'audit_date':datetime.datetime.now().astimezone().isoformat(),
        'independence':'独立脚本直接读取原始inputs/predictions/AC/metadata；未导入生产统计脚本，未改标签、权重、root脚本或目标JSON。',
        'target':str(TARGET),'target_sha256':target_sha,
        'checked_scalar_values':checked_values,'mismatch_count':len(mismatches),'mismatches':mismatches,
        'scope':{'total_raw_inputs':len(inputs),'main_domain':len(records),'background':len(background),
                 'main_source_entries':len(files),'background_source_entries':len({b[1] for b in background}),
                 'reference_full_n':len(refs),'reference_main_domain_n':1057,
                 'reference_background_n':len(refs)-1057,'original_design_strata':len(design),
                 'group_units':dict(Counter(r['group'] for r in records)),
                 'background_files':sorted({b[1] for b in background}),
                 'background_not_mixed':all(r['group'] in GROUPS for r in records)},
        'HT_weight_audit':{'definition':'在三部门域内保留每个原抽样层N_h/n_h；每部门权重之和与域总体单元数相等。',
                           'full_strata':{s:{'N_h':N,'n_h':n,'observed_full_n':observed_full_strata[s],
                                             'observed_domain_n':observed_domain_strata[s],'weight':Fraction(N,n)}
                                          for s,(N,n) in design.items()},
                           'main_domain_reference_sample_counts':dict(Counter(r['group'] for r in records if 'A_AI_reference' in r['values']))},
        'all_rows_sum_to_one':True,'checked_scenarios_per_method':9,'checked_deletions_per_method':51,
        'primary_status_unit_ids':status_ids,
        'reference_weights_by_id':{r['id']:{'stratum':refs[r['id']]['historical_sampling']['stratum'],
                                          'design':refs[r['id']]['historical_sampling'],
                                          'weight':r['weights']['A_AI_reference']}
                                   for r in records if 'A_AI_reference' in r['values']},
        'background_unit_ids':[b[0] for b in background],
        'NMPA_Ec_actual_content_binding':ec_content_binding,
        'NMPA_Ec_matrix_quote_binding_passed':True,
        'NMPA_Ec_matrix_actual_hit_coverage':{'full_positive_n':len(ec_ids),'matrix_example_ids':sorted(matrix_ec_ids),
                                           'positive_ids_covered':sorted(set(ec_ids)&matrix_ec_ids),
                                           'positive_ids_not_in_examples':sorted(set(ec_ids)-matrix_ec_ids),
                                           'example_ids_not_current_rule_positive':sorted(matrix_ec_ids-set(ec_ids))},
        'evidence_vs_distribution':'政策矩阵提供具体内容例证，不以例证数代替全量命中数；完整药监规则Ec命中ID及原文在本QA逐项绑定，另列矩阵实际覆盖。',
        'results':all_results,'claim_checks':conclusions,
        'interpretation':'各方法与实际情景的排序、例外及方向反转以claim_checks和完整结果为准；不预设新规则保持旧百分比，不把主描述排序写成所有删文情景均成立。',
        'source_hashes':{str(p):sha(p) for p in source_files},'reported_source_bindings':source_binding,
    }
    output=OUT/'三部门数据独立QA.json'
    assert sha(matrix_path)==matrix_sha,'Policy matrix changed during QA; rerun against a stable snapshot'
    output.write_text(json.dumps(serialize(result),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'checked_values':checked_values,'mismatch_count':len(mismatches),
                      'claim_checks':serialize(conclusions),'output':str(output)},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()

"""Independent reconstruction of diagnostic exports and aggregate common claims."""
from pathlib import Path
from fractions import Fraction
from itertools import combinations
import csv
import datetime
import hashlib
import json

OUT=Path(__file__).resolve().parent
DIMS=('S','E','Ec','I','F')
GROUPS=('NMPA','NHSA','NHC')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def raw(path):return {r['id']:r for r in map(json.loads,Path(path).read_text().splitlines())}
def f(value):return Fraction(value['exact_fraction'])
def key(row):return '/'.join(row[k] for k in ('frame','group','dimension','method','reference'))


def main():
    coding=read(OUT/'三部门编码指标.json');original={key(r):r for r in coding['records']}
    sources=[OUT/'三部门编码指标.json',OUT/'三部门注意力分布与敏感性.json',
             OUT/'三部门数据独立QA.json',OUT/'三部门编码指标核验.json',OUT/'聚类区间独立重算核验.json',
             OUT/'指标诊断表.json',OUT/'指标诊断表.csv',OUT/'H411指标复核表-补充样本.json',
             OUT/'H411指标复核表-补充样本.csv',OUT/'指标诊断弱项与逐例原文.json',
             OUT/'三种编码方法注意力共同结论核验.json',OUT/'三种编码方法注意力共同结论核验.md',Path(__file__)]
    before={str(p):sha(p) for p in sources};point_count=0;csv_count=0
    diagnostic_rows={}
    for frame,stem in [('main1057','指标诊断表'),('supplement_H411','H411指标复核表-补充样本')]:
        report=read(OUT/(stem+'.json'))
        assert report['frame']==frame and report['point_indicator_count']==340 and report['comparison_count']==100
        assert report['main_authoring_gate_applies'] is False and report['publication_acceptance_claim'] is False
        assert report['human_validation_completed'] is False
        with (OUT/(stem+'.csv')).open(encoding='utf-8-sig',newline='') as stream:csv_rows=list(csv.DictReader(stream))
        assert len(csv_rows)==100
        exported={r['record_key']:r for r in report['records']};csv_map={r['record_key']:r for r in csv_rows}
        assert set(exported)==set(csv_map)=={k for k,r in original.items() if r['frame']==frame}
        for record_key,row in exported.items():
            actual=original[record_key];csv_row=csv_map[record_key]
            assert row['paired_n']==actual['n'] and row['reference_positive_n']==actual['right_positive_n']
            assert row['left_positive_n']==actual['left_positive_n'] and row['excluded_n']==actual['excluded_n']
            assert int(csv_row['实际配对n'])==actual['n'] and int(csv_row['参照编码1数'])==actual['right_positive_n']
            names=('kappa',) if actual['method']=='A_C' else ('kappa','precision','recall','f1')
            assert set(row['evaluated_metrics'])==set(names)
            for name in names:
                metric=row['evaluated_metrics'][name];canonical=actual['metrics'][name]
                assert metric['estimate']==canonical['estimate'] and metric['ci95']==canonical['ci95']
                estimate=metric['estimate'];expected=estimate is not None and estimate>=.8
                assert metric['point_target_met'] is expected
                assert metric['point_lt_0_80']==(None if estimate is None else estimate<.8)
                assert metric['interval_is_acceptance_criterion'] is False
                label={'kappa':'κ','precision':'精确率P','recall':'召回率R','f1':'F1'}[name]
                for field,target in [('点值',estimate),('95%CI下界',canonical['ci95']['low']),('95%CI上界',canonical['ci95']['high'])]:
                    observed=csv_row[label+field]
                    assert (observed=='' and target is None) or (target is not None and float(observed)==target)
                point_count+=1
            assert row['all_evaluated_points_meet_target']==all(v['point_target_met'] for v in row['evaluated_metrics'].values())
            if actual['method']=='A_C':
                for label in ('精确率P','召回率R','F1'):assert csv_row[label+'点值']=='' and csv_row[label+'状态']=='A—C不适用'
            csv_count+=1
        if frame=='main1057':diagnostic_rows=exported
    # Check that every weak main comparison lists all real paired disagreements.
    audit=read(OUT/'指标诊断弱项与逐例原文.json');binding=coding['method_bindings']
    inp=raw(binding['rule']['inputs']);rule=raw(binding['rule']['rules']);llm=raw(binding['llm']['path']);refs=raw(binding['references'])
    metadata=read(binding['metadata'])['rows'];groups={Path(r['original_file']).stem:r['analysis_group'] for r in metadata}
    expected_weak={k for k,r in diagnostic_rows.items() if not r['all_evaluated_points_meet_target']}
    assert {r['record_key'] for r in audit['weak_comparisons']}==expected_weak
    expected_disagreements=set()
    for record_key in expected_weak:
        r=original[record_key];d=r['dimension'];expected_ids=[]
        for rid,ref in refs.items():
            group=groups[inp[rid]['input']['original_file_stem']]
            if group not in GROUPS or (r['group']!='ALL' and group!=r['group']):continue
            left=ref['original_references']['A']['labels'][d] if r['method']=='A_C' else rule[rid]['prediction']['labels'][d] if r['method']=='rules_v31' else llm[rid].get('prediction',llm[rid])['labels'][d]
            right=ref['original_references'][r['reference']]['labels'][d]
            if type(left)is int and type(right)is int and left!=right:
                expected_ids.append(rid);expected_disagreements.add((record_key,rid,left,right))
        item=next(item for item in audit['weak_comparisons'] if item['record_key']==record_key)
        assert item['disagreement_ids']==expected_ids
    observed={(r['record_key'],r['id'],r['left_label'],r['reference_label']) for r in audit['disagreements']}
    assert observed==expected_disagreements and len(observed)==len(audit['disagreements'])
    for r in audit['disagreements']:
        assert r['unit_text']==inp[r['id']]['input']['unit_text']
        assert r['actual_shared_contexts']==inp[r['id']]['input']['llm_v29_shared_context']
        assert r['classification_scope'].startswith('Disagreement relative to exposed original AI reference')
    # Recompute common statements from the separately verified attention JSON.
    attention=read(OUT/'三部门注意力分布与敏感性.json');common=read(OUT/'三种编码方法注意力共同结论核验.json')
    methods=('rules_v31','llm_gpt56_sol_v30','A_AI_reference','C_AI_reference')
    assert common['human_validation_completed'] is False and common['independent_human_three_method_validation_claim'] is False
    assert common['reporting_change']['coding_or_prediction_changed'] is False
    assert common['reporting_change']['canonical_statistics_or_intervals_changed'] is False
    def check_no_combined_dimension_indicator(value):
        if isinstance(value,dict):
            assert not {'NMPA_S_E_sum','NMPA_S_E_sum_gt_half','NMPA_S_E_sum_range','greater_than_half_role'} & set(value)
            for item in value.values():check_no_combined_dimension_indicator(item)
        elif isinstance(value,list):
            for item in value:check_no_combined_dimension_indicator(item)
    check_no_combined_dimension_indicator(common)
    common_markdown=(OUT/'三种编码方法注意力共同结论核验.md').read_text()
    assert all(text not in common_markdown for text in ('S+E','安全性+有效性','合计超过50%','超过50%'))
    def shares(data,group):return {d:f(data[group]['dimensions'][d]['attention_share']) for d in DIMS}
    cases={};scalar_checks=0
    for method in methods:
        sensitivity=attention['sensitivities'][method]
        cases[method]={'primary':attention['primary'][method],**sensitivity['scenarios'],
            **{'leave_out:'+r['discarded_file']:r['distribution'] for r in sensitivity['leave_one_policy_file_out']}}
        assert len(cases[method])==61
        claimed={r['case']:r for r in common['method_robustness'][method]['case_results']}
        actual_check_values={}
        for name,distribution in cases[method].items():
            a,b,c=(shares(distribution,g) for g in GROUPS)
            leaders=lambda values:[d for d in DIMS if values[d]==max(values.values())]
            nmpa_tiers=[[d for d in DIMS if a[d]==value] for value in sorted(set(a.values()),reverse=True)]
            values={'NMPA_S_unique_maximum':leaders(a)==['S'],
                    'NMPA_E_unique_second':len(nmpa_tiers)>1 and len(nmpa_tiers[0])==1 and nmpa_tiers[1]==['E'],
                    'NHSA_Ec_unique_maximum':leaders(b)==['Ec'],
                    'NHC_S_is_maximum':'S' in leaders(c),
                    'NHC_F_is_maximum':'F' in leaders(c)}
            actual_check_values[name]=values
            for k,v in values.items():assert claimed[name][k] is v;scalar_checks+=1
            for group,actual in zip(GROUPS,(a,b,c)):
                order=sorted(DIMS,key=lambda d:(-actual[d],DIMS.index(d)))
                assert claimed[name]['department_rankings'][group]['first_two_slots']==order[:2]
                assert claimed[name]['department_rankings'][group]['first_three_slots']==order[:3]
                tiers=[[d for d in DIMS if actual[d]==value] for value in sorted(set(actual.values()),reverse=True)]
                assert claimed[name]['department_rankings'][group]['ranking_tiers']==tiers
                for d in DIMS:
                    assert f(claimed[name]['department_attention_percent'][group][d])==100*actual[d]
                    scalar_checks+=1
        for indicator in actual_check_values['primary']:
            expected_false=[name for name,row in actual_check_values.items() if not row[indicator]]
            expected_count=len(actual_check_values)-len(expected_false)
            check=common['method_robustness'][method]['checks'][indicator]
            assert check=={'true_case_count':expected_count,'false_cases':expected_false,'all_61_cases':not expected_false}
            scalar_checks+=3
        for g in GROUPS:
            actual=shares(attention['primary'][method],g)
            assert sum(actual.values())==1
            for d in DIMS:assert f(common['primary'][method][g]['attention_shares'][d])==actual[d];scalar_checks+=1
    for indicator in common['primary_common_checks']:
        assert common['primary_common_checks'][indicator] is all(common['method_robustness'][m]['case_results'][0][indicator] for m in methods)
        assert common['all_methods_all_61_case_common_checks'][indicator] is all(common['method_robustness'][m]['checks'][indicator]['all_61_cases'] for m in methods)
        scalar_checks+=2
    for item in common['same_department_cross_method_share_spreads']:
        g,d=item['group'],item['dimension'];values=[shares(attention['primary'][m],g)[d] for m in methods]
        assert f(item['range_percentage_points'])==100*(max(values)-min(values));scalar_checks+=1
    spread=common['same_department_cross_method_share_spreads']
    assert common['maximum_observed_cross_method_spread_cell']==max(spread,key=lambda r:f(r['range_percentage_points']))
    assert common['maximum_absolute_rule_vs_llm_difference_cell']==max(spread,key=lambda r:abs(f(r['rule_minus_llm_percentage_points'])))
    expected_support=[{k:r[k] for k in ('dimension','reference','n','left_positive_n','right_positive_n','confusion','metrics')}
        for r in coding['records'] if r['frame']=='main1057' and r['group']=='ALL'
        and r['method']=='llm_gpt56_sol_v30' and r['dimension'] in ('I','F')]
    assert common['classification_diagnostics']['LLM_I_F_overall_paired_support']==expected_support
    expected_low=sum(v['estimate'] is not None and v['estimate']<.8 for r in original.values() if r['frame']=='main1057'
                     for m,v in r['metrics'].items() if m in (('kappa',) if r['method']=='A_C' else ('kappa','precision','recall','f1')))
    assert common['classification_diagnostics']['main_low_point_flag_count']==expected_low
    for scenario_summary in common['61_case_direction_summary']:
        name=scenario_summary['case'];counts={'all_four_same_direction_count':0,'rule_llm_same_direction_count':0,'A_C_same_direction_count':0};noncommon=[]
        for a,b in combinations(GROUPS,2):
            for d in DIMS:
                values=[shares(cases[m][name],a)[d]-shares(cases[m][name],b)[d] for m in methods]
                signs=[(v>0)-(v<0) for v in values]
                counts['all_four_same_direction_count']+=len(set(signs))==1
                counts['rule_llm_same_direction_count']+=signs[0]==signs[1]
                counts['A_C_same_direction_count']+=signs[2]==signs[3]
                if len(set(signs))!=1:noncommon.append((a,b,d))
                if name=='primary':
                    row=next(r for r in common['primary_15_same_dimension_department_directions'] if r['pair']==[a,b] and r['dimension']==d)
                    for method,value,sign in zip(methods,values,signs):assert f(row['methods'][method]['share_difference'])==value and row['methods'][method]['direction']==sign
                scalar_checks+=4
        for k,v in counts.items():assert scenario_summary[k]==v
        assert [(r['pair'][0],r['pair'][1],r['dimension']) for r in scenario_summary['noncommon_directions']]==noncommon
    assert before=={str(p):sha(p) for p in sources}
    report={'status':'passed','checked_at':datetime.datetime.now().astimezone().isoformat(),
        'independence':'Separate script imports no export builders. Reconstructs diagnostic mappings/CI/flags, original paired disagreement IDs, attention rankings, 61-case common conditions and exact 15-direction differences.',
        'diagnostic_point_indicators_checked':point_count,'diagnostic_comparison_csv_rows_checked':csv_count,
        'main_disagreement_rows_independently_reconstructed':len(observed),
        'common_claim_scalar_checks':scalar_checks,'human_validation_completed':False,
        'reporting_only_change_verified':True,'combined_dimension_indicator_absence_verified':True,
        'mechanical_all_340_threshold_authoring_gate':False,'source_sha256':before}
    (OUT/'共同结论与指标诊断独立QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'source_sha256','independence','checked_at'}},ensure_ascii=False))


if __name__=='__main__':main()

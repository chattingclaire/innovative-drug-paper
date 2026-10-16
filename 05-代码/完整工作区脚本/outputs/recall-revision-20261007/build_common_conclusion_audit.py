"""Compare actual attention conclusions across rules, LLM and two original AI references."""
from pathlib import Path
from itertools import combinations
from collections import Counter
from fractions import Fraction
import datetime
import hashlib
import json

OUT=Path(__file__).resolve().parent
DIMS=('S','E','Ec','I','F')
GROUPS=('NMPA','NHSA','NHC')
DIM_NAMES={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
GROUP_NAMES={'NMPA':'药监','NHSA':'医保','NHC':'卫健'}
METHOD_NAMES={'rules_v31':'自动规则','llm_gpt56_sol_v30':'LLM编码','A_AI_reference':'原AI参照A','C_AI_reference':'原AI参照C'}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def fraction(value):return Fraction(value['exact_fraction']) if isinstance(value,dict) else Fraction(value)
def serialize(value):
    if isinstance(value,Fraction):return {'value':float(value),'exact_fraction':str(value)}
    if isinstance(value,dict):return {k:serialize(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [serialize(v) for v in value]
    return value


def shares(distribution,group):
    result={d:fraction(distribution[group]['dimensions'][d]['attention_share']) for d in DIMS}
    assert sum(result.values())==1
    return result


def ranking(values):
    levels=sorted(set(values.values()),reverse=True)
    order=sorted(DIMS,key=lambda d:(-values[d],DIMS.index(d)))
    return {'ranking_tiers':[[d for d in DIMS if values[d]==v] for v in levels],
        'ordered_dimensions_with_canonical_tie_break':order,
        'highest_dimensions':[d for d in DIMS if values[d]==max(values.values())],
        'first_two_slots':order[:2],'first_three_slots':order[:3],
        'dimensions_at_or_above_second_value':[d for d in DIMS if values[d]>=values[order[1]]],
        'dimensions_at_or_above_third_value':[d for d in DIMS if values[d]>=values[order[2]]],
        'has_equal_shares':len(levels)<5}


def direction(distribution,a,b,d):
    difference=shares(distribution,a)[d]-shares(distribution,b)[d]
    return {'share_difference':difference,'percentage_point_difference':100*difference,
            'direction':1 if difference>0 else -1 if difference<0 else 0}


def main():
    data_path=OUT/'三部门注意力分布与敏感性.json';data=load(data_path)
    qa_path=OUT/'三部门数据独立QA.json';qa=load(qa_path)
    coding_path=OUT/'三部门编码指标.json';coding=load(coding_path)
    point_qa=load(OUT/'三部门编码指标核验.json');ci_qa=load(OUT/'聚类区间独立重算核验.json')
    assert qa['status']=='passed' and qa['target_sha256']==sha(data_path)
    assert point_qa['status']==ci_qa['status']=='passed'
    assert point_qa['target_sha256']==ci_qa['target_sha256']==sha(coding_path)
    assert ci_qa['intervals_independently_recomputed']==1280
    assert data['method_bindings']['llm']['source_material_version']=='v3'
    methods=('rules_v31','llm_gpt56_sol_v30','A_AI_reference','C_AI_reference')
    assert set(data['primary'])==set(methods)
    sources=[data_path,qa_path,coding_path,OUT/'三部门编码指标核验.json',OUT/'聚类区间独立重算核验.json',
             OUT/'指标诊断表.json',OUT/'指标诊断弱项与逐例原文.json',Path(__file__)]
    source_hashes={str(p):sha(p) for p in sources}
    primary={};cases={};method_robustness={}
    for method in methods:
        primary[method]={}
        for group in GROUPS:
            values=shares(data['primary'][method],group)
            primary[method][group]={'attention_shares':values,'attention_percent':{d:100*v for d,v in values.items()},
                'observed_units':data['primary'][method][group]['observed_unit_count'],
                'weighted_five_dimension_hit_sum':data['primary'][method][group]['weighted_five_dimension_known_hit_sum'],
                **ranking(values)}
        sensitivity=data['sensitivities'][method]
        cases[method]={'primary':data['primary'][method],**sensitivity['scenarios'],
            **{'leave_out:'+r['discarded_file']:r['distribution'] for r in sensitivity['leave_one_policy_file_out']}}
        assert len(cases[method])==61
        checks=[]
        for name,distribution in cases[method].items():
            nmpa,nhsa,nhc=(shares(distribution,g) for g in GROUPS)
            nmpa_rank=ranking(nmpa);nhsa_rank=ranking(nhsa);nhc_rank=ranking(nhc)
            checks.append({'case':name,
                'NMPA_S_unique_maximum':nmpa_rank['highest_dimensions']==['S'],
                'NMPA_E_unique_second':len(nmpa_rank['ranking_tiers'])>1 and len(nmpa_rank['ranking_tiers'][0])==1 and nmpa_rank['ranking_tiers'][1]==['E'],
                'NHSA_Ec_unique_maximum':nhsa_rank['highest_dimensions']==['Ec'],
                'department_rankings':{'NMPA':nmpa_rank,'NHSA':nhsa_rank,'NHC':nhc_rank},
                'department_attention_percent':{g:{d:100*v for d,v in values.items()} for g,values in zip(GROUPS,(nmpa,nhsa,nhc))},
                'NHC_S_is_maximum':'S' in nhc_rank['highest_dimensions'],
                'NHC_F_is_maximum':'F' in nhc_rank['highest_dimensions']})
        boolean_keys=('NMPA_S_unique_maximum','NMPA_E_unique_second',
                      'NHSA_Ec_unique_maximum','NHC_S_is_maximum','NHC_F_is_maximum')
        summary={key:{'true_case_count':sum(r[key] for r in checks),'false_cases':[r['case'] for r in checks if not r[key]],
                      'all_61_cases':all(r[key] for r in checks)} for key in boolean_keys}
        nhc_orders=Counter(tuple(tuple(tier) for tier in r['department_rankings']['NHC']['ranking_tiers']) for r in checks)
        method_robustness[method]={'evaluated_cases':61,'checks':summary,
            'NHC_ranking_tier_case_counts':[{'ranking_tiers':list(k),'case_count':v} for k,v in nhc_orders.items()],
            'case_results':checks}
    scenario_names=list(cases[methods[0]])
    assert all(set(cases[m])==set(scenario_names) for m in methods)
    direction_results=[];scenario_direction_results=[]
    for scenario in scenario_names:
        rows=[]
        for a,b in combinations(GROUPS,2):
            for dim in DIMS:
                by_method={m:direction(cases[m][scenario],a,b,dim) for m in methods}
                signs={m:r['direction'] for m,r in by_method.items()}
                rows.append({'pair':[a,b],'dimension':dim,'dimension_name':DIM_NAMES[dim],
                    'methods':by_method,'all_four_same_direction':len(set(signs.values()))==1,
                    'rule_and_llm_same_direction':signs[methods[0]]==signs[methods[1]],
                    'A_and_C_same_direction':signs[methods[2]]==signs[methods[3]]})
        assert len(rows)==15
        summary={'case':scenario,'all_four_same_direction_count':sum(r['all_four_same_direction'] for r in rows),
            'rule_llm_same_direction_count':sum(r['rule_and_llm_same_direction'] for r in rows),
            'A_C_same_direction_count':sum(r['A_and_C_same_direction'] for r in rows),
            'noncommon_directions':[r for r in rows if not r['all_four_same_direction']]}
        scenario_direction_results.append(summary)
        if scenario=='primary':direction_results=rows
    spread=[]
    for group in GROUPS:
        for dim in DIMS:
            values={m:primary[m][group]['attention_shares'][dim] for m in methods}
            maximum,minimum=max(values.values()),min(values.values())
            spread.append({'group':group,'dimension':dim,'dimension_name':DIM_NAMES[dim],
                'method_attention_percent':{m:100*v for m,v in values.items()},
                'minimum_percent':100*minimum,'maximum_percent':100*maximum,
                'range_percentage_points':100*(maximum-minimum),
                'highest_methods':[m for m,v in values.items() if v==maximum],
                'lowest_methods':[m for m,v in values.items() if v==minimum],
                'rule_minus_llm_percentage_points':100*(values[methods[0]]-values[methods[1]])})
    common_checks={key:all(method_robustness[m]['checks'][key]['all_61_cases'] for m in methods)
        for key in ('NMPA_S_unique_maximum','NMPA_E_unique_second',
                    'NHSA_Ec_unique_maximum','NHC_S_is_maximum','NHC_F_is_maximum')}
    primary_common={key:all(method_robustness[m]['case_results'][0][key] for m in methods)
                    for key in common_checks}
    diagnostic=load(OUT/'指标诊断表.json');diff=load(OUT/'指标诊断弱项与逐例原文.json')
    maximum_spread=max(spread,key=lambda r:r['range_percentage_points'])
    maximum_rule_llm=max(spread,key=lambda r:abs(r['rule_minus_llm_percentage_points']))
    low_flags=Counter((r['method'],'overall' if r['group']=='ALL' else 'department')
                     for r in diagnostic['records'] for value in r['evaluated_metrics'].values()
                     if value['point_lt_0_80'] is True)
    llm_I_F_support=[{k:r[k] for k in ('dimension','reference','n','left_positive_n','right_positive_n','confusion','metrics')}
        for r in coding['records'] if r['frame']=='main1057' and r['group']=='ALL'
        and r['method']=='llm_gpt56_sol_v30' and r['dimension'] in ('I','F')]
    report={'status':'actual_current_attention_common_conclusions_computed',
        'checked_at':datetime.datetime.now().astimezone().isoformat(),
        'method_families':{'自动规则':['rules_v31'],'LLM编码':['llm_gpt56_sol_v30'],
                          '双AI独立首次参照':['A_AI_reference','C_AI_reference']},
        'reference_identity':'A/C are original first independent AI-agent submissions and exposed development references; not completed real-human validation.',
        'human_validation_completed':False,'independent_human_three_method_validation_claim':False,
        'reporting_change':{'scope':'Presentation only: report all five dimensions separately by share and rank; no combined-dimension indicator.',
            'coding_or_prediction_changed':False,'canonical_statistics_or_intervals_changed':False},
        'definition':'同部门每维编码句次/五维编码句次合计；规则与LLM全量，A/C保留原抽样设计权重。跨维分别计次，同维至多一次；每行五维占比精确合计100%。',
        'population_n':4481,'main_reference_n':1057,'background_n_excluded':443,
        'primary':primary,'primary_common_checks':primary_common,
        'all_methods_all_61_case_common_checks':common_checks,'method_robustness':method_robustness,
        'primary_15_same_dimension_department_directions':direction_results,
        '15_direction_definition':'Three department pairs × five same dimensions: compare each dimension attention share across departments. This is not a claim that each department has the same complete five-dimension ranking in every method.',
        'primary_direction_summary':scenario_direction_results[0],
        '61_case_direction_summary':scenario_direction_results,
        'same_department_cross_method_share_spreads':spread,
        'maximum_observed_cross_method_spread_percentage_points':max(r['range_percentage_points'] for r in spread),
        'maximum_observed_cross_method_spread_cell':maximum_spread,
        'maximum_absolute_rule_vs_llm_difference_cell':maximum_rule_llm,
        'classification_diagnostics':{'source':str(OUT/'指标诊断表.json'),'threshold_role':'0.80 is a diagnostic marker after user goal clarification; no mechanical all340 threshold gate.',
            'summary':diagnostic['summary'],'weak_comparison_count':diff['weak_comparison_count'],
            'main_low_point_flag_count':sum(low_flags.values()),
            'main_low_point_flags_by_method_and_scope':[{'method':m,'scope':s,'point_count':n} for (m,s),n in low_flags.items()],
            'LLM_I_F_overall_paired_support':llm_I_F_support,
            'raw_disagreement_source':str(OUT/'指标诊断弱项与逐例原文.json'),
            'relative_to_AI_reference_only':True,'common_attention_direction_does_not_prove_each_label_correct':True},
        'interpretation_limits':{'share_spread_role':'All actual percentage-point differences disclosed; no assumption that differences are small.',
            'NHC_rank_role':'Report all actual ranks, ties and scenario changes; do not require S/F to remain top two.',
            'semantic_errors':'Substantive reasons require the original-text disagreement audit; a shared aggregate direction is not an excuse to ignore coding errors.'},
        'source_sha256':source_hashes}
    target=OUT/'三种编码方法注意力共同结论核验.json'
    target.write_text(json.dumps(serialize(report),ensure_ascii=False,indent=2)+'\n')
    lines=['# 三种编码方法注意力共同结论核验','',
        '依据本次v3共同材料与实际完成的规则/LLM编码，另列原AI参照A/C。A/C尚非已完成的真人验证，不能写成三条独立人工验证。','',
        '本次仅调整报告方式：五个维度分别展示占比和排序，不新增复合指标；编码、主统计数据及置信区间不变。','',
        report['definition'],'',
        '|方法|部门|安全性%|有效性%|经济性%|创新性%|公平性%|实际排序（=为同值）|','|---|---|---:|---:|---:|---:|---:|---|']
    for method in methods:
        for group in GROUPS:
            r=primary[method][group]
            order=' > '.join(' = '.join(DIM_NAMES[d] for d in tier) for tier in r['ranking_tiers'])
            lines.append('|'+ '|'.join([METHOD_NAMES[method],GROUP_NAMES[group]]+[f'{float(r["attention_percent"][d]):.4f}' for d in DIMS]+[order])+'|')
    lines+=['','共同主结论的实测条件：','',
        '|检验内容|主口径四组估计均成立|四组估计全部61口径均成立|','|---|---|---|']
    labels={'NMPA_S_unique_maximum':'药监安全性占比唯一最高',
        'NMPA_E_unique_second':'药监有效性占比单独居第二位',
        'NHSA_Ec_unique_maximum':'医保经济性占比唯一最高',
        'NHC_S_is_maximum':'卫健安全性占比最高（含并列）',
        'NHC_F_is_maximum':'卫健公平性占比最高（含并列）'}
    for key,label in labels.items():lines.append(f'|{label}|{primary_common[key]}|{common_checks[key]}|')
    lines+=['',
        '|方法|药监安全性唯一最高口径数/61|药监有效性单独第二口径数/61|医保经济性唯一最高口径数/61|卫健安全性最高或并列口径数/61|卫健公平性最高或并列口径数/61|','|---|---:|---:|---:|---:|---:|']
    for method in methods:
        checks=method_robustness[method]['checks'];keys=('NMPA_S_unique_maximum','NMPA_E_unique_second','NHSA_Ec_unique_maximum','NHC_S_is_maximum','NHC_F_is_maximum')
        lines.append('|'+ '|'.join([METHOD_NAMES[method]]+[str(checks[k]['true_case_count']) for k in keys])+'|')
    summary=scenario_direction_results[0]
    lines+=['',f'主口径15个同维部门比较中，四组估计同方向{summary["all_four_same_direction_count"]}/15，规则与LLM同方向{summary["rule_llm_same_direction_count"]}/15，A与C同方向{summary["A_C_same_direction_count"]}/15。这里指3个部门对×5个同维度的部门大小关系，不是各部门内部五维完整排序都一致。','',
        '|未共同同向的比较|规则方向及百分点差|LLM方向及百分点差|A方向及百分点差|C方向及百分点差|','|---|---:|---:|---:|---:|']
    for row in summary['noncommon_directions']:
        values=[f'{v["direction"]:+d}；{float(v["percentage_point_difference"]):+.4f}' for v in row['methods'].values()]
        lines.append('|'+ '|'.join([GROUP_NAMES[row['pair'][0]]+'−'+GROUP_NAMES[row['pair'][1]]+'：'+row['dimension_name']]+values)+'|')
    if not summary['noncommon_directions']:lines.append('|无|—|—|—|—|')
    lines+=['','同部门各维的跨方法数值差异逐项披露：','',
        '|部门|维度|最小占比%|最大占比%|差距（百分点）|规则−LLM（百分点）|','|---|---|---:|---:|---:|---:|']
    for row in spread:lines.append(f'|{GROUP_NAMES[row["group"]]}|{row["dimension_name"]}|{float(row["minimum_percent"]):.4f}|{float(row["maximum_percent"]):.4f}|{float(row["range_percentage_points"]):.4f}|{float(row["rule_minus_llm_percentage_points"]):+.4f}|')
    max_low='/'.join(METHOD_NAMES[m] for m in maximum_spread['lowest_methods'])
    max_high='/'.join(METHOD_NAMES[m] for m in maximum_spread['highest_methods'])
    lines+=['',f'最大跨方法差距出现在{GROUP_NAMES[maximum_spread["group"]]}的{maximum_spread["dimension"] and DIM_NAMES[maximum_spread["dimension"]]}：{max_high} {float(maximum_spread["maximum_percent"]):.4f}%，{max_low} {float(maximum_spread["minimum_percent"]):.4f}%，相差{float(maximum_spread["range_percentage_points"]):.4f}个百分点。',
        f'规则与LLM最大绝对差出现在{GROUP_NAMES[maximum_rule_llm["group"]]}的{DIM_NAMES[maximum_rule_llm["dimension"]]}：规则{float(maximum_rule_llm["method_attention_percent"][methods[0]]):.4f}%，LLM{float(maximum_rule_llm["method_attention_percent"][methods[1]]):.4f}%，相差{abs(float(maximum_rule_llm["rule_minus_llm_percentage_points"])):.4f}个百分点。',
        '', '主口径药监安全性居第一位，有效性居第二位；改为文件等权或系列等权后，LLM及A/C的创新性升至第二位，有效性降至第三位。安全性第一位在全部四组×61口径成立。',
        '', '卫健主口径的安全性、公平性位于前两位；排除联合发文后四组均转为公平性、经济性、有效性、安全性、创新性的排序。逐文件剔除《加强用药安全管理提升合理用药水平-2022》后，规则及A/C的经济性也超过安全性。LLM该删文口径仍保留安全性/公平性前两位。全部61口径的首位仍属于安全性/公平性。',
        '', '主1057的340个诊断点指标中，52个低于0.80：机器总体15个（均为LLM创新性/公平性），机器分部门36个（规则9、LLM27），A—C分部门1个。A—C总体5个κ均不低于0.80。0.80仅用于定位需要解释的比较，未设置全340过线门禁。',
        '', '|LLM维度—参照|实际配对n|LLM编码1数|参照编码1数|TP/FP/FN/TN|κ及95%区间|','|---|---:|---:|---:|---|---|']
    for r in llm_I_F_support:
        k=r['metrics']['kappa'];ci=k['ci95'];cells=r['confusion']
        lines.append(f'|{DIM_NAMES[r["dimension"]]}—{r["reference"]}|{r["n"]}|{r["left_positive_n"]}|{r["right_positive_n"]}|'+ '/'.join(str(cells[x]) for x in ('TP','FP','FN','TN'))+f'|{k["estimate"]:.6f} [{ci["low"]:.6f}, {ci["high"]:.6f}]|')
    lines+=['', '这些FP/FN只表示相对原AI参照的分歧，不是已经完成真人裁定的语义错误。逐项原文、完整实际共同语境、原理由和来源见“指标诊断弱项与逐例原文.json”。共同排序不能替代数值差异和实际编码问题的解释。',
        '', '本核验描述注意力配置的跨方法/跨口径一致性；不将相同宏观方向等同于每个编码都正确，也不据此声称真人信效度验证已经完成。']
    (OUT/'三种编码方法注意力共同结论核验.md').write_text('\n'.join(lines)+'\n')
    assert source_hashes=={str(p):sha(p) for p in sources}
    print(json.dumps(serialize({'primary_common':primary_common,'all_61_common':common_checks,
        'primary_directions':{k:v for k,v in summary.items() if k!='noncommon_directions'},
        'maximum_spread_pp':report['maximum_observed_cross_method_spread_percentage_points']}),ensure_ascii=False))


if __name__=='__main__':main()

"""A separate fixed n=600 comparison, never edits the earlier delivered plan.
Only frozen metadata/old prediction variables; no source text, human labels,
actual sample selection, new machine run, or result-driven sample expansion.
"""
from pathlib import Path
from collections import Counter,defaultdict
import json,math,hashlib
import numpy as np
import precision_plan as p

HERE=Path(__file__).resolve().parent
def layer(r):
    sig=p.signature(r)
    if sig!='0000':tag='IF'
    elif any(r['rules39'][d]!=r['LLM03'][d] for d in ['S','E','Ec']):tag='OTHER_DISAGREEMENT'
    elif any(r[m][d]==1 for m in p.METHODS for d in ['S','E','Ec']):tag='OTHER_AGREE_POS'
    else:tag='ALL_NEG'
    return '|'.join([r['department'],sig,tag])
def scene(rows,dim,T,signal):
    micro=Counter((layer(r),r['rules39'][dim],r['LLM03'][dim]) for r in rows)
    keys=sorted(micro);caps=[micro[k] for k in keys]
    ref=p.bounded_counts(caps,[signal**(k[1]+k[2]) for k in keys],T)
    output={m:defaultdict(lambda:[0,0,0,0]) for m in p.METHODS};joint=[]
    for (h,x,y),N,t in zip(keys,caps,ref):
        joint.append({'stratum':h,'rules39':x,'LLM03':y,'N':N,'reference_positive':int(t)})
        for m,pred in [('rules39',x),('LLM03',y)]:
            cells=output[m][h]
            if pred:cells[0]+=int(t);cells[1]+=int(N-t)
            else:cells[2]+=int(t);cells[3]+=int(N-t)
    return joint,output
def main():
    binding=json.loads((HERE/'source-bindings.json').read_text())
    projection=HERE/'inputs/metadata-and-fixed-labels.jsonl'
    assert p.sha(projection)==binding['projection']['sha256']
    rows=[r for r in map(json.loads,projection.open()) if r['exposure']=='remaining']
    assert len(rows)==1444
    counts=Counter(layer(r) for r in rows);st=[];ns={}
    for h,N in sorted(counts.items()):
        dept,sig,tag=h.split('|')
        if tag in ['IF','OTHER_DISAGREEMENT']:n=N
        elif tag=='OTHER_AGREE_POS':n=N if dept=='NHC' else (N+1)//2
        else:n={'NMPA':123,'NHSA':80,'NHC':38}[dept]
        assert 0<n<=N and (n>=2 or n==N)
        ns[h]=n
        st.append({'key':h,'department':dept,'IF_signature':sig,'tag':tag,
                   'N':N,'n':n,'pi':n/N,'weight':N/n,'census':n==N,
                   'same_stratum_pair_pi':None if N==1 else n*(n-1)/(N*(N-1))})
    assert sum(ns.values())==600 and len(st)==23
    assert {g:sum(h['n'] for h in st if h['department']==g) for g in p.ORDER}=={'NMPA':312,'NHSA':237,'NHC':51}
    scenarios=[]
    for dim in p.DIMS:
        for T in [14,43,72,144,289,722]:
            for signal in [.25,1.,20.]:
                joint,cells=scene(rows,dim,T,signal)
                Ts={h:sum(c[i] for i in [0,2]) for h,c in cells['rules39'].items()}
                result={m:p.summarize(cells[m],ns) for m in p.METHODS}
                tails={str(minimum):p.positive_count_tail([(h['N'],Ts[h['key']],h['n']) for h in st],minimum)
                       for minimum in [1,5,10,22,40,62,97]}
                scenarios.append({'dimension':dim,'reference_positive_total':T,
                                  'reference_odds_multiplier_per_auxiliary_positive':signal,
                                  'joint_counts':joint,'machine_results':result,
                                  'raw_reference_positive_shortfall_probability':tails})
    maxima={}
    for dim in p.DIMS:
        maxima[dim]={}
        for m in p.METHODS:
            maxima[dim][m]={}
            for metric in ['kappa','precision','recall','F1']:
                possible=[(s['machine_results'][m]['metrics'][metric]['linearized_95_halfwidth'],s)
                          for s in scenarios if s['dimension']==dim]
                value,s=max(((v,s) for v,s in possible if v is not None),key=lambda item:item[0])
                maxima[dim][m][metric]={'max_planning_halfwidth':value,
                                        'reference_positive_total':s['reference_positive_total'],
                                        'reference_odds_multiplier_per_auxiliary_positive':s['reference_odds_multiplier_per_auxiliary_positive'],
                                        'metric_point_in_that_scenario':s['machine_results'][m]['metrics'][metric]['point']}
    Nn=[(h['N'],h['n']) for h in st if not h['census']]
    zero=p.zero_error_upper(Nn,.025)
    rare=[]
    for h in st:
        if h['tag']!='ALL_NEG':continue
        N,n=h['N'],h['n']
        rare.append({'department':h['department'],'N':N,'n':n,
                     'all_reference_positives_missed_probability':{str(T):float(p.hypergeom.pmf(0,N,T,n)) for T in [1,2,5,10]}})
    human=p.human_scenarios(st,{'small600':ns})
    old_plan=json.loads((HERE/'strata-planning.json').read_text())
    result={
        'status':'fixed600_metadata_only_comparison__not_final_execution_freeze',
        'date':'2026-10-10','model':'GPT-6.1 Sol','reasoning_effort':'ultra',
        'source_bindings_sha256':p.sha(HERE/'source-bindings.json'),
        'projected_inputs_sha256':p.sha(projection),'script_sha256':p.sha(Path(__file__)),
        'earlier_plan_changed':False,'N':1444,'n':600,
        'scope':'Only frozen remaining1444 finite domain. Other3037 IDs have pi=0; no full4481 performance inference.',
        'stratum_rule':'department × historical joint I/F signature; 0000 split into S/E/Ec disagreement, other joint-positive agreement, and all-five both-machine negative.',
        'IF_signature_order':['rules39_I','LLM03_I','rules39_F','LLM03_F'],
        'strata':st,'department_n':{'NMPA':312,'NHSA':237,'NHC':51},
        'preanswer_allocation_logic':'Census141 historical I/F-positive and102 other disagreements; half of NMPA/NHSA jointly-agree other-positive106/114 (53/57), census6 NHC agree-positive; remaining241 negative slots fixed123/80/38. No actual validation answers or scores used.',
        'raw_sample_weighted_analysis_required':True,
        'workload':{'two_person_unit_readings':1200,'first_decision_dimension_entries':6000,'adjudication_unit_max':600},
        'department_old_auxiliary_positive_counts':{
            g:{m:{dim:sum(r[m][dim] for r in rows if r['department']==g) for dim in p.DIMS} for m in p.METHODS} for g in p.ORDER},
        'working_comparison_to_census':{'census_unit_readings':2888,'saved_unit_readings':1688,'units_not_selected_if_later_drawn':844,
                                       'reserve_families_guaranteed':False,'near_or_context_exposure_free_guaranteed':False},
        'project_goals':old_plan['project_targets'],
        'CI_halfwidth_gate_added':False,'CI_lower_bound_gate_added':False,
        'interval_contract':'Report actual raw/design weighted cells and marginal95 design-consistent intervals, unknown and zero-cell guards. No preclaimed .10 halfwidth adequacy guarantee. Census precision is a comparison, not a requirement.',
        'old_auxiliary_scenario_grid_maxima':maxima,
        'one_predeclared_zero_category_pooled_guard':zero,
        'single_stratum_rare_reference_miss_risks':rare,
        'human_initial_kappa_synthetic_scenarios':human,
        'machine_joint_synthetic_scenarios':scenarios,
        'limitations':[
            'Scenario intervals are anticipated linearization widths from synthetic finite counts, not actual human or machine accuracy.',
            'Old I/F precision has zero sampling error because all old predicted positives are in census strata, conditional on complete adjudication. It is not inherently narrow superpopulation/reference uncertainty.',
            'Both old machines can miss the same rare true positives in noncensus joint-negative layers; machine agreement is not independent truth.',
            'Future new-manual predictions may change all five positive margins, disagree in historical agreement layers, or produce NA; old-positive census and grid do not protect their precision or recall.',
            'Actual final machines can still be evaluated on this probability sample using frozen weights; stratification remains valid even if auxiliary signal weakens, precision may worsen.',
            'Small/zero reference-positive denominators can make Recall/kappa broad or NA. No sample expansion depending on passing .80.',
            'No unseen1444 body/context/human answer read, no final sample IDs/seed drawn, no new machine inference executed.',
            'Source-only metadata pool is the registered no-case-development-evidence remainder; original text and broader context may have been visible.',
        ]}
    p.save(HERE/'small-plan-comparison.json',result)
    render(result)
    print(json.dumps({'n':600,'strata':len(st),'department_n':result['department_n'],'maxima':maxima,'zero_guard':zero},ensure_ascii=False,indent=2))
def render(d):
    lines=[]
    def add(s=''):lines.append(s)
    add('# 总n=600的固定分层工作量—精度比较')
    add('\n2026-10-10；GPT-6.1 Sol / ultra。仅使用冻结元数据和rules39/LLM03历史标签规划；未读剩余1444正文/语境或真人答案，未抽最终ID，未运行新机器，未改已交付1444档。')
    add('\n**这是一档可事前固定的600条概率样本方案**：药监312、医保237、卫健51，两位真人1200次单位阅读、6000个五维首判项，裁定最多600条。比1444全核少844条、1688次双人阅读，精度随真实正类数及错误位置变化。Goal要求报告真实区间和信息充分性，没有必须抽样误差为0、CI半宽≤.10或下界≥.80的条件。此档不声称与全核精度相同，也不保证点值达标。')
    add('\n## 固定层、N、n与概率')
    add('\n四位签名为规则I、LLM I、规则F、LLM F。非0000的I/F辅助阳性141条全核；0000但其他S/E/Ec两机分歧102条也全核。这覆盖两机五维全部分歧，同时保留机器相同阳性的抽样和双方相同阴性的抽样，不能把分歧全核当作完整验证。其他共同阳性药监106取53、医保114取57、卫健6全取；双方五维全阴性536/348/91固定取123/80/38。共23个非空层全部pi>0。')
    add('\n| 部门 | I/F签名 | 类别 | N_h | 固定n_h | pi | w |\n|---|---|---|---:|---:|---:|---:|')
    order={'NMPA':0,'NHSA':1,'NHC':2};names={'NMPA':'药监','NHSA':'医保','NHC':'卫健'}
    tags={'IF':'I/F辅助阳性','OTHER_DISAGREEMENT':'其他维机器分歧','OTHER_AGREE_POS':'其他维共同阳性','ALL_NEG':'两机五维全阴性'}
    for h in sorted(d['strata'],key=lambda h:(order[h['department']],h['IF_signature'],h['tag'])):
        add(f"| {names[h['department']]} | {h['IF_signature']} | {tags[h['tag']]} | {h['N']} | {h['n']} | {h['pi']:.4f} | {h['weight']:.4f} |")
    add('| **合计** | | | **1444** | **600** | | |')
    add('\n非全取层内SRSWOR，层间独立；pi=n_h/N_h、w=N_h/n_h，同层二阶pi=n_h(n_h−1)/[N_h(N_h−1)]。至少2条的规定在实际非全取层满足；单例层全取。正式抽取前锁定seed、名单、版本与真实人安排。本次未选择seed或名单，也没有给任何实际ID分配伪参照。')
    add('\n## 预期区间：哪些可能较宽')
    add('\n使用已交付相同90场景网格：共同参照T=14/43/72/144/289/722，辅助信号倍率.25/1/20；保持实际旧两机联合容量和阳性边际，以一份共同整数参照生成两机四格。表列每维/方法在网格中的最大预期95%线性化半宽，单元之间最大值可能来自不同场景，不是某一可同时实现的误差表，也不是实际结果或覆盖保证。')
    add('\n| 维度 | 方法 | κ最大规划半宽 | P最大规划半宽 | R最大规划半宽 | F1最大规划半宽 |\n|---|---|---:|---:|---:|---:|')
    for dim in p.DIMS:
        for m in p.METHODS:
            x=d['old_auxiliary_scenario_grid_maxima'][dim][m]
            add(f"| {dim} | {m} | {x['kappa']['max_planning_halfwidth']:.3f} | {x['precision']['max_planning_halfwidth']:.3f} | {x['recall']['max_planning_halfwidth']:.3f} | {x['F1']['max_planning_halfwidth']:.3f} |")
    add('\n旧I/F阳性全部进入全核层，因此完整裁定后旧P的分母与TP可直接确定，设计抽样方差为0。这只适用于旧固定输出及当前有限池。S/E/Ec部分相同阳性只抽一半，P仍有抽样误差；所有维度R要识别低概率抽取阴性层里的漏判，尤其少量真实阳性时可宽。κ受两边边际和稀疏四格影响；人—人首判仍可能在历史机器一致阴性里分歧，因此不能用机器分歧全核保证人κ。')
    add('\n人A/B36个合法合成表中，等边际14/14、κ=.7836的600档规划半宽约'+f"{next(s for s in d['human_initial_kappa_synthetic_scenarios'] if s['A_positive']==14 and s['B_positive']==14 and s['nominal_kappa']==.8)['allocations']['small600']['linearized_95_halfwidth']:.3f}"+'；43/43、κ=.8082约'+f"{next(s for s in d['human_initial_kappa_synthetic_scenarios'] if s['A_positive']==43 and s['B_positive']==43 and s['nominal_kappa']==.8)['allocations']['small600']['linearized_95_halfwidth']:.3f}"+'。这些示例体现罕见维度的信息局限，不新增验收门槛。')
    add('\n部门分域更需报实际计数：卫健历史E/I两机阳性均为0，Ec为规则1/LLM0，F仅规则1/LLM3；药监Ec两机各1，医保I为规则11/LLM2。预测阳性0时旧P直接NA；参照是否有正类仍未知，不能预填R或κ。即使分域旧P因为阳性全核无抽样方差，一两条正例也不提供宽泛的构念或未来政策证据。分域R、人κ和最终新机器P可能宽或NA，不能因 pooled 指标较稳省略小部门。')
    add('\n### 零错误也有信息边界')
    zero=d['one_predeclared_zero_category_pooled_guard']
    add(f"\n若五个非全取层中一个事前指定类别确实全部观测为0，用未知错误在各层配置的最坏零事件概率反演，双侧95%上侧α=.025总隐藏类别上界为**{zero['maximum_unseen_count']}**（P0上界={zero['sup_zero_event_probability_at_upper']:.6f}，下一整数={zero['sup_zero_event_probability_at_next']:.6f}）。这是单一类别guard，不是四格/45指标联合区间。")
    add('\n在“已知TP来自全核、其余全部观测FN=0、未核层可能漏判”这个条件例中，TP=18时R下界18/(18+14)=.563；TP=32时为.696；TP=44时为.759；TP=1时为.067。它们是分母敏感性说明，不是对实际R的估计。普通bootstrap零错退化[1,1]不能替代有限总体guard；全表需保留四格/unknown约束和相应风险分配。')
    add('\n| 全辅助阴性部门层 | 唯一真实阳性全漏概率 | 2条同层全漏 | 5条同层全漏 |\n|---|---:|---:|---:|')
    for x in d['single_stratum_rare_reference_miss_risks']:
        r=x['all_reference_positives_missed_probability'];add(f"| {names[x['department']]} | {r['1']:.1%} | {r['2']:.1%} | {r['5']:.1%} |")
    add('\n这说明双方机器一致为0的罕见真阳性不能被辅助变量保证发现。脚本还卷积场景内各层Hypergeom(N_h,T_h,n_h)得到参照阳性原始观察数不足1/5/10/22/40/62/97的尾概率。T=14时Pr(阳性观察数<62)=1，不能把总n600误当600个Recall分母。该尾是计数风险，不能替代设计加权R方差。')
    add('\n## 估计、实际充分性与新手册变化')
    add('\n完整可判四格按HT估计：Ĉ=Σ_h(N_h/n_h)C_sample,h；保留原始格与加权格。正式协方差用实际样本s_h及有限总体校正，V̂=Σ_hN_h²(1−n_h/N_h)s_h/n_h；κ/P/R/F1是总体四格函数，用解析梯度。不能直接平均层κ、把过抽分歧层的原始分数说成总体分数，或用假有效二项分母取代主区间。按实际稀疏/零格补有限超几何边界，另报材料失败、unknown九格、加权未知率和全域上下界；比例无分母和Pe=1仍NA。')
    add('\n新手册/语境修正后，rules39/LLM03的旧阳性、分歧和参考概率关系可能失效：新机器可能在旧全阴性层新增阳性，旧P零方差及上述网格均不能沿用。冻结辅助分层和权重仍构成对1444正概率样本，**设计推断仍有效，预期效率会变化**。最终机器仅对固定样本或所需完整语料按冻结方案运行；标签不得回流修改手册/规则/提示。新结果应按真实四格与CI评价，不因旧辅助标签0假定新机器标签0。')
    add('\n保留用户逐维点值目标：真实两人独立首判Cohen κ≥.80；两个最终机器分别每维κ/P/R/F1≥.80。本档不保证这些点值、各维充分分母、窄区间、稀有漏判必检出，也不要求CI下限或半宽达某条额外线。报告中同时展示点值、真实95%区间和计数充分性，信息不足如实留存；不得看中期过线与否扩样、只补容易题或在600与1444间择分。')
    add('\n推断只代表1444剩余有限池。3037开发曝光项pi=0，不能权重补成全4481。抽取后844条未入选也不是已认证的844条未来独立留出：是否同正文族、材料语境被呈现或用于修订须重新核定；不能预先保证新版本重测容量。')
    add('\n## 交付与核查')
    add('\n[small-plan-comparison.json](small-plan-comparison.json)保存全部23层N/n/pi/二阶pi、90个共享参照整数场景、36个人κ场景、尾概率和guard；[small_plan.py](small_plan.py)可重复计算。运行`../.venv/bin/python small_plan.py`仅读取许可投影并覆盖本small档，不改1444档。另见[independent-review/small-plan-review.md](independent-review/small-plan-review.md)的独立Sol/ultra方法核查。')
    add('\n本档可供主对话在真实答案前按工作量选择；当前仅比较，不是最终抽样或真人执行冻结。已交付的1444档仍原样保留。')
    (HERE/'small-plan-comparison.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()

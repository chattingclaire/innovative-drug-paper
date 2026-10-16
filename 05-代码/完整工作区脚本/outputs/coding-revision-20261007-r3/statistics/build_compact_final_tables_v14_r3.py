"""Compact handoff tables derived from verified final JSON, never manuscript text."""
from pathlib import Path
import json
import statistical_core_r3 as c


def main():
    out=Path(__file__).parent;root=out/'final-v14'
    rows=c.read(root/'machine_reference_classification.json')['comparisons']
    ac=c.read(root/'A_C_final_before_third_agreement.json')['comparisons']
    full=c.read(root/'full4481_machine_attention_and_file_composition_sensitivity.json')['primary']
    prob=c.read(root/'probability_attention_and_paired_department_differences.json')['profiles']
    development=c.read(out/'v33-v34.1-v35.1-v14-development-diagnostic/comparisons.json')['comparisons']
    formats=[('probability_canonical','eligible_design_weighted','概率180，设计加权'),
             ('probability_canonical','unweighted','概率180，未加权'),
             ('enriched_challenge','unweighted','挑战60，单独描述')]
    lookup={(x['component'],x['group'],x['weighting'],x['method'],x['reference'],x['dimension']):x for x in rows}
    fmt=lambda x:'NA' if x is None else f'{x:.3f}'
    four=[('rules','A'),('rules','C'),('LLM','A'),('LLM','C')]
    summary={'source_output_freeze_sha256':c.sha(root/'output_freeze.json'),'four_comparison_tables':[],
             'candidate_performance':[],'full4481_attention':full,'probability180_candidate_attention':[],
             'v35_1_development_candidate_performance':[],'human_validation_completed':False}
    text=['五维终版紧凑表','','正式规则=v33；LLM=候选02语义基线+引文隔离技术恢复。A/C/T是AI参考，未做真人核验；补料复读由替代独立会话完成。v35.1全部r3样本已开发暴露，单列诊断。','']
    for component,weight,title in formats:
        text += [title+'：四比较κ','','|维度|规则–A|规则–C|LLM–A|LLM–C|','|---|---|---|---|---|']
        for d in c.DIMS:
            vals=[lookup[component,'ALL',weight,m,r,d]['metrics']['kappa']['estimate'] for m,r in four]
            text.append(f"|{d}|{'|'.join(fmt(v) for v in vals)}|")
            summary['four_comparison_tables'].append({'component':component,'weighting':weight,'dimension':d,
                'comparisons':{m+'-'+r:lookup[component,'ALL',weight,m,r,d]['metrics'] for m,r in four}})
        text += ['',title+'：候选参考下κ / P / R / F1','','|维度|规则v33 κ / P / R / F1|LLM κ / P / R / F1|','|---|---|---|']
        for d in c.DIMS:
            cells=[]
            for method in ('rules','LLM'):
                row=lookup[component,'ALL',weight,method,'candidate',d]
                cells.append(' / '.join(fmt(row['metrics'][x]['estimate']) for x in ('kappa','precision','recall','f1')))
                summary['candidate_performance'].append({k:row[k] for k in ('component','weighting','method','dimension','raw_confusion','metrics')})
            text.append(f"|{d}|{'|'.join(cells)}|")
        text.append('')
    text += ['全4481条三部门机器注意力（%）','','分母为各部门五维编码句次合计，允许一条多维命中；不是阳性句数占全部句数。','','|方法|部门|S|E|Ec|I|F|五维编码句次|','|---|---|---|---|---|---|---|---|']
    for method,groups in full.items():
        for g,row in groups.items():
            vals=[f'{100*row["attention_share"][d]:.2f}' for d in c.DIMS]
            text.append(f"|{method}|{g}|{'|'.join(vals)}|{int(row['five_dimension_coding_count'])}|")
    text += ['', '同180概率样本的候选参考注意力（每部门60；%）','','|部门|S|E|Ec|I|F|五维编码句次|','|---|---|---|---|---|---|---|']
    for row in prob:
        if row['method']=='candidate' and row['group'] in c.GROUPS:
            vals={d:row['dimensions'][d]['attention_share'] for d in c.DIMS}
            summary['probability180_candidate_attention'].append({'group':row['group'],'attention_share':vals,
                'coding_count':row['weighted_five_dimension_coding_count_on_support']})
            text.append(f"|{row['group']}|{'|'.join(f'{100*vals[d]:.2f}' for d in c.DIMS)}|{int(row['weighted_five_dimension_coding_count_on_support'])}|")
    text += ['', 'v35.1仅开发诊断：概率180设计加权，对候选参考','','|维度|κ|P|R|F1|','|---|---|---|---|---|']
    for row in development:
        if (row['component'],row['group'],row['weighting'],row['method'],row['reference'])==('probability_canonical','ALL','eligible_design_weighted','v35.1','candidate'):
            vals={k:row['metrics'][k]['estimate'] for k in ('kappa','precision','recall','f1')}
            summary['v35_1_development_candidate_performance'].append({'dimension':row['dimension'],**vals})
            text.append(f"|{row['dimension']}|{'|'.join(fmt(v) for v in vals.values())}|")
    text += ['', 'NA保留未定义。概率样本推断范围为剩余canonical抽样框947/760/60；挑战样本不合并推断总体。点值的0.80诊断目标不是普遍发表门槛，置信区间及NA分母见完整表。', '']
    for filename,obj in [('final-v14-compact-summary.json',summary)]:
        target=out/filename;assert not target.exists();c.write_json(target,obj)
    target=out/'final-v14-compact-summary.md';assert not target.exists();target.write_text('\n'.join(text))
    print(json.dumps({'status':'compact_tables_ready','json':str(out/'final-v14-compact-summary.json'),'markdown':str(target)},ensure_ascii=False))


if __name__=='__main__':main()

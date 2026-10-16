"""Refresh concise reporting tables directly from current statistical outputs."""
from pathlib import Path
from collections import Counter
import json
import hashlib

OUT=Path(__file__).resolve().parent
DIMS=('S','E','Ec','I','F')
GROUPS=('NMPA','NHSA','NHC')


def val(x):
    return x['value'] if isinstance(x,dict) and 'value' in x else x


def main():
    coding=json.loads((OUT/'三部门编码指标.json').read_text())
    attention=json.loads((OUT/'三部门注意力分布与敏感性.json').read_text())
    qa=json.loads((OUT/'三部门数据独立QA.json').read_text())
    audit=json.loads((OUT/'error_audit.json').read_text())
    assert qa['status']=='passed' and qa['target_sha256']==hashlib.sha256((OUT/'三部门注意力分布与敏感性.json').read_bytes()).hexdigest()
    rule=coding['method_bindings']['rule']['method']
    assert rule in attention['primary']
    overall=[r for r in coding['records'] if r['frame']=='main1057' and r['group']=='ALL']
    weak=[r for r in coding['records'] if r['group']!='ALL' and (r['metrics']['kappa']['estimate'] is None or r['metrics']['kappa']['estimate']<.8)]
    sensitivity={}
    for method,data in attention['sensitivities'].items():
        cases={'primary':attention['primary'][method],**data['scenarios'],**{'leave_out:'+r['discarded_file']:r['distribution'] for r in data['leave_one_policy_file_out']}}
        sensitivity[method]={'evaluated_cases':len(cases),'claim_checks':qa['claim_checks'][method],'groups':{}}
        for g in GROUPS:
            allshares={d:[val(v[g]['dimensions'][d]['attention_share']) for v in cases.values()] for d in DIMS}
            leaders=Counter()
            for case,stats in cases.items():
                shares={d:val(stats[g]['dimensions'][d]['attention_share']) for d in DIMS}
                known=[v for v in shares.values() if v is not None]
                top=tuple(d for d in DIMS if shares[d]==max(known)) if known else ()
                leaders[top]+=1
            sensitivity[method]['groups'][g]={'attention_share_ranges':{d:[min(v for v in values if v is not None),max(v for v in values if v is not None)] for d,values in allshares.items()},
                'dominant_dimension_case_counts':[{'dimensions':list(k),'case_count':v} for k,v in leaders.items()]}
    result={'rule_method':rule,'rule_version':coding['method_bindings']['rule']['version'],
            'llm_status':coding['latest_llm'],'main_overall_classification':overall,
            'department_low_or_undefined_kappa':weak,'main_class_counts':audit['main1057_class_counts'],
            'primary_attention':attention['primary'],'sensitivity_summary':sensitivity,
            'classification_qa':json.loads((OUT/'三部门编码指标核验.json').read_text()),
            'attention_qa':{'status':qa['status'],'checked_scalar_values':qa['checked_scalar_values'],'mismatch_count':qa['mismatch_count']},
            'method_bindings':coding['method_bindings'],
            'target_sha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest()
                              for name in ('三部门编码指标.json','三部门注意力分布与敏感性.json')}}
    ci_qa_path=OUT/'聚类区间独立重算核验.json'
    if ci_qa_path.exists():
        ci_qa=json.loads(ci_qa_path.read_text())
        assert ci_qa['status']=='passed' and ci_qa['target_sha256']==result['target_sha256']['三部门编码指标.json']
        result['cluster_ci_independent_qa']=ci_qa
    (OUT/'最终指标简表.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    lines=['# 三部门编码指标与复跑说明','',f'当前规则：{rule}；实际版本：{result["rule_version"]}。','',
        '三部门纳入4481个单元；原AI参照主框1057个，补充H框411个。A/C为按统一规范独立首次提交的AI agent判读，原标签未改；这些材料已用于方法诊断。分类指标在双方实际共同可判集合等权计算；A/C注意力占比另沿用原29层N_h/n_h设计权重。','',
        '## 主1057总体指标','', '|维度|比较|n|排除|κ及95%区间|一致率|Precision|Recall|F1|','|---|---|---:|---:|---|---:|---:|---:|---:|']
    for r in overall:
        def fmt(metric):
            x=r['metrics'].get(metric,{}).get('estimate');return '—' if x is None else f'{x:.6f}'
        k=r['metrics']['kappa']['ci95'];pair='A—C' if r['method']=='A_C' else r['method']+'—'+r['reference']
        lines.append(f'|{r["dimension"]}|{pair}|{r["n"]}|{r["excluded_n"]}|{fmt("kappa")} [{k["low"]:.6f}, {k["high"]:.6f}]|{fmt("agreement")}|{fmt("precision")}|{fmt("recall")}|{fmt("f1")}|')
    has_llm = bool(coding['method_bindings']['llm']['path'])
    count_header = '|部门|维度|A正类（待定）|C正类（待定）|规则正类|' + ('LLM正类|' if has_llm else '') + '最少正类数|'
    count_separator = '|---|---|---:|---:|---:|' + ('---:|' if has_llm else '') + '---:|'
    lines+=['','A—C只报告对称κ和一致率，不把任一编码员当作真值。机器对A和C分别报告正类P/R/F1，四格与每维待定排除ID见JSON/CSV。每个区间来自5000次来源文件聚类bootstrap；有效及未定义重复分别保留，分母为0的点指标记NA。','',
        '## 主1057分部门正类数','', count_header, count_separator]
    for r in audit['main1057_class_counts']:
        c=r['methods'];lines.append(f'|{r["group"]}|{r["dimension"]}|{c["A"]["positive"]}（{c["A"]["pending"]}）|{c["C"]["positive"]}（{c["C"]["pending"]}）|{c["rule"]["positive"]}|'+(f'{c["LLM"]["positive"]}|' if has_llm else '')+f'{r["min_positive_n"]}|')
    lines+=['','这是各自整框类数；每项指标的正类数以其实际共同可判集合为准。','',
        '## 分部门低κ与NA','', '|框|部门|维度|比较|n|四格|κ|','|---|---|---|---|---:|---|---:|']
    for r in weak:
        cells=r['confusion'] or r['cross_tab'];k=r['metrics']['kappa']['estimate']
        lines.append(f'|{r["frame"]}|{r["group"]}|{r["dimension"]}|{r["method"]}—{r["reference"]}|{r["n"]}|'+', '.join(f'{a}={b}' for a,b in cells.items())+'|'+('NA' if k is None else f'{k:.6f}')+'|')
    lines+=['','0.8仅用于列出审查项，不作为改标签目标。低正类数会放大个别边界判断；逐例原文、父条款、标签、规则证据与指标贡献见error_audit.json，无标签复核材料见blind_error_packet*.jsonl。全0配对可有观察一致率1而κ未定义，不能改为κ1。','',
        '## 主注意力分布','', '|方法|部门|分母句次|S%|E%|Ec%|I%|F%|','|---|---|---:|---:|---:|---:|---:|---:|']
    for method,distribution in attention['primary'].items():
        for g in GROUPS:
            r=distribution[g];lines.append('|'+ '|'.join([method,g,f'{val(r["weighted_five_dimension_known_hit_sum"]):.6f}']+[f'{100*val(r["dimensions"][d]["attention_share"]):.6f}' for d in DIMS])+'|')
    lines+=['','规则／实际LLM以全量编码句次归一化；A/C先估计五维句次再归一化。跨维共现分别计次，同维至多一次。待定补全范围是描述性范围，与bootstrap区间不同。','',
        '## 敏感性核验','']
    for method,s in sensitivity.items():
        checks=s['claim_checks'];lines.append(f'- {method}：核验{s["evaluated_cases"]}种主口径／情景／逐条目剔除组合；药监S始终唯一最大={checks["NMPA_S_unique_maximum_all_cases"]}，医保Ec始终唯一最大={checks["NHSA_Ec_unique_maximum_all_cases"]}，卫健最大维始终属于S/F={checks["NHC_maximum_always_S_or_F"]}。')
        for e in checks['NHC_top_two_exceptions']:
            lines.append('  - 卫健S/F未同时前两位：'+e['case']+'；'+', '.join(d+f'{100*val(e["shares"][d]):.4f}%' for d in DIMS))
    lines+=['','## 独立核验与刷新','',f'分类独立重建{result["classification_qa"]["records_independently_reconstructed"]}项比较通过；注意力独立核验{qa["checked_scalar_values"]}个值，差异{qa["mismatch_count"]}。Excel中点估计由四格公式计算，CI读实际输出，AI身份及源SHA保存在方法与来源页。','',
        '两统计脚本均支持--rules、--inputs、--rule-method、--rule-version及显式--llm。非默认规则文件必须给出方法名与真实版本；LLM不自动探测，只有完整4924行且ID闭合的最终文件可传入。当前实际绑定：','',
        '```text','--rules '+coding['method_bindings']['rule']['rules'],'--inputs '+coding['method_bindings']['rule']['inputs'],
        '--rule-method '+rule,'--rule-version '+coding['method_bindings']['rule']['version'],
        *(['--llm '+coding['method_bindings']['llm']['path']] if has_llm else []),'```','',
        '先运行两个recalculate脚本，再运行verify_three_department_coding_metrics.py、verify_cluster_bootstrap_intervals.py、independent_qa_three_departments.py、build_three_department_error_audit.py、verify_three_department_error_audit.py和本脚本，最后用bundled Node运行build_metrics_workbook.mjs并用verify_metrics_workbook.py核对导出缓存。后续覆盖同一xlsx，不另造版本。',
        '', 'LLM状态：'+coding['latest_llm']['status']+'；预期最终路径：'+coding['latest_llm']['path']]
    (OUT/'三部门编码指标说明.md').write_text('\n'.join(lines)+'\n')
    (OUT/'最终指标简表.md').write_text('\n'.join(lines[:lines.index('## 独立核验与刷新')])+'\n')
    print(json.dumps({'rule':rule,'main_overall_rows':len(overall),'weak_or_NA_comparisons':len(weak),'attention_qa':result['attention_qa']},ensure_ascii=False))


if __name__=='__main__':main()

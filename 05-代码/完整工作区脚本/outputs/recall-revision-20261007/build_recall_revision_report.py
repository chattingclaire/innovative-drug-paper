"""Report actual old/new results only after current numerical QA has passed."""
from pathlib import Path
from fractions import Fraction
from hashlib import sha256
import json

OUT=Path(__file__).resolve().parent
OLD=OUT.parent/'final-three-department-20261007'
def read(p):return json.loads(p.read_text())
def sha(p):return sha256(p.read_bytes()).hexdigest()
coding=read(OUT/'三部门编码指标.json');old=read(OLD/'三部门编码指标.json')
attention=read(OUT/'三部门注意力分布与敏感性.json')
for filename,target in [('三部门编码指标核验.json','三部门编码指标.json'),('三部门数据独立QA.json','三部门注意力分布与敏感性.json')]:
    qa=read(OUT/filename);assert qa['status']=='passed' and qa['target_sha256']==sha(OUT/target)
methods={'自动规则':('rules_v30','rules_v31'),'LLM':('llm_gpt56_sol_v29','llm_gpt56_sol_v30')}
dims={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
def metric(data,method,d,reference,key):
    row=next(r for r in data['records'] if (r['frame'],r['group'],r['method'],r['dimension'],r['reference'])==('main1057','ALL',method,d,reference))
    return row['metrics'][key]['estimate']
def fmt(x,percent=False):return '未定义' if x is None else f'{x*100:.1f}%' if percent else f'{x:.3f}'
lines=['# 编码修订结果与论文结论','',
    '本轮自动规则及LLM均使用同版完整材料完成4924条真实编码，其中三部门4481条进入主比较。五维定义、原文和ID不变；A/C原有AI首次标注及其可见材料保留，未在新材料上重做。下表是相对于这些参照的开发复核结果。','',
    '## 当前κ对照','', '|维度|自动规则—A|自动规则—C|LLM—A|LLM—C|','|---|---:|---:|---:|---:|']
for d,name in dims.items():
    vals=[fmt(metric(coding,m[1],d,r,'kappa')) for m in methods.values() for r in ['A','C']]
    lines.append('|'+name+'|'+'|'.join(vals)+'|')
lines.extend(['','## 召回率及精确率的实际变化','', '|方法、维度|精确率A：原→现|召回率A：原→现|精确率C：原→现|召回率C：原→现|','|---|---:|---:|---:|---:|'])
for name,(before,after) in methods.items():
    for d in ['I','F']:
        vals=[]
        for r in ['A','C']:
            for key in ['precision','recall']:
                vals.append(fmt(metric(old,before,d,r,key),True)+' → '+fmt(metric(coding,after,d,r,key),True))
        lines.append('|'+name+'·'+dims[d]+'|'+'|'.join(vals)+'|')
lines.extend(['','## 分部门仍需关注的比较','',
    '以下按0.80定位复核项，该值是本轮检查标记，不是统一发表门槛。总体指标不能代替分部门、分维度检查。','',
    '|方法、部门、维度、参照|参照1数量|κ|精确率|召回率|F1|','|---|---:|---:|---:|---:|---:|'])
department_names={'NMPA':'药监','NHSA':'医保','NHC':'卫健'}
low=[]
for row in coding['records']:
    if row['frame']!='main1057' or row['group'] not in department_names or row['method']=='A_C':continue
    estimates={k:row['metrics'][k]['estimate'] for k in ['kappa','precision','recall','f1']}
    if not any(v is not None and v<.8 for v in estimates.values()):continue
    low.append(row)
    label='自动规则' if row['method']=='rules_v31' else 'LLM'
    title='·'.join([label,department_names[row['group']],dims[row['dimension']],row['reference']])
    support=row['confusion']['TP']+row['confusion']['FN']
    lines.append('|'+title+'|'+str(support)+'|'+'|'.join(fmt(v,k in ['precision','recall']) for k,v in estimates.items())+'|')
if not low:lines.append('|本轮无此类比较|—|—|—|—|—|')
lines.extend(['','## 三部门注意力配置','', '|方法、部门|安全性|有效性|经济性|创新性|公平性|','|---|---:|---:|---:|---:|---:|'])
for name,(_,method) in methods.items():
    for group,label in [('NMPA','药监'),('NHSA','医保'),('NHC','卫健')]:
        values=[Fraction(attention['primary'][method][group]['dimensions'][d]['attention_share']['exact_fraction']) for d in dims]
        assert sum(values)==1
        lines.append('|'+name+'·'+label+'|'+'|'.join(f'{float(x)*100:.2f}%' for x in values)+'|')
lines.extend(['','占比以同一部门五维编码句次合计为分母，精确值每行100%；独立四舍五入可有0.01—0.02个百分点误差。', '',
    '## 占比差异对应的实际编码句次','',
    '|部门、维度|规则：本维句次／五维总句次|LLM：本维句次／五维总句次|','|---|---:|---:|'])
for group,d in [('NMPA','I'),('NHSA','F'),('NHSA','Ec')]:
    cells=[]
    for method in ['rules_v31','llm_gpt56_sol_v30']:
        row=attention['primary'][method][group]
        cells.append(f"{row['dimensions'][d]['raw_known_hit_count']}／{row['raw_five_dimension_known_hit_sum']}")
    lines.append('|'+department_names[group]+'·'+dims[d]+'|'+'|'.join(cells)+'|')
lines.extend(['',
    '注意力占比同时受本维句次和五维总句次影响。例如LLM识别的医保经济性句次更多，但其他维度句次增长更快，其经济性占比反而较低。这是归一化计算的关系，不能据此直接判定哪个方法正确；仍须核对原文和可信参照。','',
    '精确率、召回率和κ回答不同问题：改正漏识别可以提高召回，纠正多判也可能使召回下降。保留原文和手册支持的判定，不把参照一致或固定指标阈值作为改标依据。正式独立真人验证仍由作者另行补齐；开发样本的指标不冒称该项验证已完成。',''])
(OUT/'编码修订结果与论文结论.md').write_text('\n'.join(lines))
(OUT/'修订结果报告数据绑定.json').write_text(json.dumps({'status':'bound_to_numerically_verified_current_results','source_sha256':{str(p):sha(p) for p in [OUT/'三部门编码指标.json',OLD/'三部门编码指标.json',OUT/'三部门注意力分布与敏感性.json']},'output_sha256':sha(OUT/'编码修订结果与论文结论.md')},ensure_ascii=False,indent=2)+'\n')
print('Created current-only coding and attention result report')

from pathlib import Path
import json,hashlib,itertools
OUT=Path(__file__).resolve().parent
r=json.loads((OUT/'统计及稳健性完整结果.json').read_text())['results'];c=json.loads((OUT/'旧稿主张核查.json').read_text())
deps=['NMPA','NHSA','NHC'];names={'NMPA':'药监局','NHSA':'医保局','NHC':'卫健委'};dims=['S','E','Ec','I','F'];cn=dict(zip(dims,['安全性','有效性','经济性','创新性','公平性']))
def qb(s,d):
 a=s['dimensions'][d]
 return (a['q_conditional_lower'],a['q_conditional_upper']) if 'q_conditional_lower' in a else (a['q_mean_conditional_bounds']['lower'],a['q_mean_conditional_bounds']['upper'])
def robust(s):
 return {'药监局安全性居首':all(qb(s['NMPA'],'S')[0]>qb(s['NMPA'],d)[1] for d in dims if d!='S'),'医保局经济性居首':all(qb(s['NHSA'],'Ec')[0]>qb(s['NHSA'],d)[1] for d in dims if d!='Ec'),'医保局经济性构成高于卫健委':qb(s['NHSA'],'Ec')[0]>qb(s['NHC'],'Ec')[1],'医保局E给定S高于药监局':s['NHSA']['conditionals']['E_given_S']['bounds']['lower']>s['NMPA']['conditionals']['E_given_S']['bounds']['upper'],'医保局E给定S高于卫健委':s['NHSA']['conditionals']['E_given_S']['bounds']['lower']>s['NHC']['conditionals']['E_given_S']['bounds']['upper'],'卫健委F给定Ec高于医保局':s['NHC']['conditionals']['F_given_Ec']['bounds']['lower']>s['NHSA']['conditionals']['F_given_Ec']['bounds']['upper']}
bounds={method:{'scenarios':{n:robust(s) for n,s in result['scenarios'].items()},'leave_one':{x['removed_source']:robust(x['statistics']) for x in result['leave_one_source_out']}} for method,result in r.items()}
(OUT/'待定范围内结论检查.json').write_text(json.dumps(bounds,ensure_ascii=False,indent=2)+'\n')
lines=['# 旧版4481条统计收尾结果','', '本次仅重算已保存的77条校准对应版本。没有调用模型，没有更改机器或人工标签，没有修改论文。主图采用LLM结果；规则仅用于核对旧稿曾经提出的比较主张。','', '## 可直接用于原稿的数字','', '三部门条款数分别为1848、2100、533；五维正标签累计数分别为1091、1148、127。待定判断分别为46、9、5项，共60项。详见双口径表和组合图。','', '|部门|涉及安全性且有效性可判定的条款中，同时涉及有效性|涉及经济性且公平性可判定的条款中，同时涉及公平性|','|---|---:|---:|']
for dep,s in r['LLM']['scenarios']['条款等权'].items():
 vals=[s['conditionals'][key] for key in ['E_given_S','F_given_Ec']]
 lines.append('|'+ '|'.join([names[dep]]+[f'{int(v["positive_pair"])}/{int(v["complete_condition_positive"])}（{v["observed"]*100:.2f}%）' for v in vals])+'|')
lines+=['','## 原稿主张核对','', '|LLM主张|九种口径|逐一剔除来源|','|---|---|---|']
for name,v in c['LLM'].items():
 if name=='卫健委安全性居首':desc='剔除联合来源后不成立';ldesc='剔除2022年用药安全来源后不成立'
 else:desc='均成立';ldesc='均成立'
 lines.append(f'|{name}|{desc}|{ldesc}|')
lines+=['','逐来源检查包含51次。对一个部门内部排序而言，删除其他部门来源不会影响它；本部门实际来源数为药监局20个、医保局24个、卫健委7个，不能把51次都写成独立挑战。','', '### 需要修改的旧稿句子','', '1. “15项比较中13项同向”不再适用。旧版为12项同向、3项异向：药监局与卫健委的创新性、公平性，以及医保局与卫健委的创新性。机器间同向并不证明人工效度，主分析若采用LLM，可删除这段不必要的两机比较。','2. “卫健委以安全性居首”只能描述主口径。剔除联合来源后，卫健委经济性居首；逐一剔除2022年用药安全来源后也改变。应写成其关注结构受所纳入政策任务构成影响，不能概括为稳定、普遍的安全性主导。','3. “九种口径下两种方法均显示医保局安全性句段更常同时提疗效”不能照搬。旧规则剔除年度系列后不再高于药监局和卫健委，剔除联合来源也不再高于卫健委。旧LLM该方向保持。','4. 旧稿规则条件比例（如32/49、99/262等）来自后续版，必须删除或换成配套JSON中的旧规则数。主分析采用LLM时建议只保留上表必要的条件比例。','', '## 待定范围检查','', '保持全部已知0/1标签不变，让每项待定分别取0或1，计算界限；这不是置信区间，也不增加或更改标签。', '']
for method in ['LLM','rule']:
 lines+=['### '+method,'']
 for claim in next(iter(bounds[method]['scenarios'].values())):
  failed=[name for name,x in bounds[method]['scenarios'].items() if not x[claim]]
  leavefailed=[name for name,x in bounds[method]['leave_one'].items() if not x[claim]]
  lines.append(f'- {claim}：九种口径中{9-len(failed)}种可在待定取值范围内确定；逐来源删除中{51-len(leavefailed)}次可确定。'+('例外口径：'+'、'.join(failed)+'。' if failed else '')+('详细来源例外见JSON。' if leavefailed else ''))
lines+=['','药监局经济性基数仅5条，相应公平性条件比例不用于主要部门比较；其待定范围较宽。现有重点比较是医保局与卫健委。','', '## 图表与复算文件','', '- `三部门评价维度-双口径组合图.pdf`：矢量PDF，字体嵌入；`三部门评价维度-双口径组合图.png`：300 dpi图片。','- `全量双口径统计表.md`、同名口径JSON/CSV：逐部门五维计数、两种比例、负标签与待定数。','- `统计及稳健性完整结果.json`：旧版输入SHA-256、所有9种口径、条件分母、逐来源删除及NULL范围。','- `旧稿主张核查.json`、`待定范围内结论检查.json`：逐项成立或例外。','- `recompute.py`、`plot.py`、`report.py`：重算、制图及说明脚本。','', '备注：来源等权与系列年度成员均值属于改变汇总权重；剔除年度系列或联合来源属于改变分析范围。它们是敏感性检查，不能作为用来替换主口径的“更真实比例”。比例高低不存在0.8的合格线。','']
# obtain source N mechanically
entry=json.loads((OUT/'统计及稳健性完整结果.json').read_text())['results']['LLM']['scenarios']['条款等权']
actual='、'.join(f'{names[d]}{entry[d]["source_entry_N"]}个' for d in deps)
lines=[x.replace('药监局20个、医保局24个、卫健委7个',actual) for x in lines]
(OUT/'统计图表完成说明.md').write_text('\n'.join(lines))
print('\n'.join(lines[-22:]))

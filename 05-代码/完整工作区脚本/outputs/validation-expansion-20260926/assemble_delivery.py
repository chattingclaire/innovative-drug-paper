"""Assemble final navigation and conclusions only after both cohorts and QA exist."""
from pathlib import Path
import json, hashlib
R=Path(__file__).parent
DIMS=('S','E','Ec','I','F')
NAMES={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
def read(name): return json.loads((R/name).read_text())
def link(name): return f'[{name}]({R/name})'
def fmt(v): return 'NA' if v is None else f'{v:.3f}'
def pct(v): return 'NA' if v is None else f'{v:.1%}'
h=read('H600-正式统计.json'); c=read('R200-描述统计.json')
assert h['status']=='completed_frozen_ID_join_not_validation_pass'
assert c['status']=='completed_challenge_descriptive_ID_join_not_validation_pass' and c['sample_n']==200
for phase in ('H600','R200'):
 q=read(phase+'-工作簿交付核验.json'); v=read(phase+'-工作簿视觉核验.json')
 assert q['phase']==phase and v['status']=='workbook_export_data_and_sampled_visual_review_complete'
 for w in q['workbooks']:
  p=Path(w['path']); actual=hashlib.sha256(p.read_bytes()).hexdigest()
  assert w['sha256']==actual==v['files'][p.name]
sec=read('H600-SEC分歧事后复核.json')
# IF is checked and summarized from its issued readable report, not recoded here.
assert (R/'H600-IF分歧事后复核.md').exists()
lines=['# 扩充独立编码与论文修订交付说明','',
'本轮已按人工内容分析流程完成两份独立评审：A、C分别判读600条正式留出单元和200条补充挑战单元，使用同一CAL-5D-20260926-v1.3手册。执行者均为AI，不能写成真人专家、人工金标准或真人编码信度。','',
'18条适合暴露和讨论规则分歧，不能单独承担稳定的五维验证。本轮600条用于冻结版本的检验；200条按预先登记规则补充较少见的阳性及边界材料。两者用途不同，不合并成800条代表性样本，也不把两份答案算成1600条。原18条和开发60条不并入检验。','',
'**主要结论：两位AI较一致，但冻结词典与其未充分吻合。不能宣布自动编码验证通过，也不能据当前词典比例推断部门真实关注程度。**','',
'| 维度 | H600 A/C κ（95%区间） | 词典对A/C Recall | 词典对A/C F1 |','|---|---|---|---|']
for d in DIMS:
 a=h['comparisons']['A_vs_C']['dimensions'][d]; ci=a['marginal_95_intervals']['kappa_definite']
 v=[h['comparisons']['dictionary_vs_'+x]['dimensions'][d]['estimates']for x in ('A','C')]
 lines.append(f'| {NAMES[d]} | {fmt(a["estimates"]["kappa_definite"])}（{fmt(ci["lower"])}–{fmt(ci["upper"])}） | {pct(v[0]["recall_definite"])}/{pct(v[1]["recall_definite"])} | {fmt(v[0]["f1_definite"])}/{fmt(v[1]["f1_definite"])} |')
lines+=['','上表使用设计权重，仅在相应双方可判部分计算；待定保留。完整覆盖率、Precision、正负类一致率及区间见'+link('H600-独立AI验证报告.md')+'。H600仅推及排除已知开发及近重复后的U*=3655，不能直接推广到原4924条。创新性A/C阳性仅18/19条，κ区间仍宽；高总体一致率不能掩盖阳性少与共享AI错误。','',
'补充200条只作本集合描述：','',
'| 维度 | R200 A/C κ | 词典对A/C Recall | 词典对A/C F1 |','|---|---:|---|---|']
for d in DIMS:
 a=c['comparisons']['A_vs_C']['dimensions'][d]['descriptive_values']
 v=[c['comparisons']['dictionary_vs_'+x]['dimensions'][d]['descriptive_values']for x in ('A','C')]
 lines.append(f'| {NAMES[d]} | {fmt(a["kappa_definite"])} | {pct(v[0]["recall_definite"])}/{pct(v[1]["recall_definite"])} | {fmt(v[0]["f1_definite"])}/{fmt(v[1]["f1_definite"])} |')
lines+=['','完整挑战集构成、阳性数、可判覆盖和待定界见'+link('R200-补充挑战集报告.md')+'。该集合定向抽取，没有总体权重或总体置信区间，不用于挽救H600的检验结果。','',
'维度定义与正文两种编码如何衔接：共同手册统一了分析单元、五维定义、语境使用、排除规则、子类型及待定规则；词典和LLM提示词均按版本绑定。然而版本一致不等于实现一致。本轮已经发现词典的“用药错误”触发缺失、“仿制药/参比制剂”药物对象识别过窄，以及程序性“价格协商”的误识别。正文历史外部LLM尚未以本次相同输入和版本重新执行，不能说另一套LLM结果已经通过本轮验证。','',
'分歧并非全是机器错误：S/E/Ec复核中，0362“满足临床需求”、0444一般药品使用管理、0506笼统“药物反应数据”均保留了两位AI共同过度推断的疑问。事后诊断只帮助解释问题，不覆盖首次标签，不生成修正金标准或新的准确率。详见'+link('H600-SEC分歧事后复核.md')+'及'+link('H600-IF分歧事后复核.md')+'。','',
'I/F事后复核覆盖46个不同病例，39例有原文或所附语境支持，7例仍保留边界疑问。33个F分歧来自保障获取27例、患者可负担6例，没有仅临床管理难度的案例，因此低召回不能简单归因于F定义纳入了临床管理内容。这些是已知双方和机器结果后的解释性个数，不是机器错误率或第三份独立盲评。','',
'联动正文的处理：正式结果单列呈现；原词典部门表和图降为冻结词典诊断，撤回把占比作为可靠部门分布估计的推断。论文可保留五维框架、制度文本证据及可追溯方法的贡献，但不能把内容来源、评审一致性、分类效度和部门推断混为一项“全部通过”。后续若据本轮分歧修规则，必须另登记开发并使用新的独立材料验证；不反复扩样或调标追求预期结果。','',
'盲评的实际范围：评审看不到彼此标签与机器预测，材料保留政策来源标题和页码，因而不是来源机关盲。A在正式阶段使用新上下文，C延续开发上下文；两者可能共享模型偏差，未知历史原文暴露不能完全排除。补充阶段未收到H600比较结果或诊断反馈。','',
'交付表均保留原文、逐维标签、证据理由、待定及问题记录，并附同版手册。标签与完整语境已经逐字段核验，工作表代表区域已作视觉检查。','']
for name in ['正式盲评600-A-AI评审.xlsx','正式盲评600-C-AI评审.xlsx','补充挑战200-A-AI评审.xlsx','补充挑战200-C-AI评审.xlsx']:
 lines.append('- '+link(name))
lines+=['','首次统计归档：'+link('H600-正式统计.json')+'；'+link('R200-描述统计.json')+'。原始分歧及待定见'+link('H600-分歧与待定追溯.json')+'；'+link('R200-分歧与待定追溯.json')+'。']
dst=R/'扩充独立编码与论文修订-交付说明.md'
with dst.open('x')as f:f.write('\n'.join(lines)+'\n')
print(dst)

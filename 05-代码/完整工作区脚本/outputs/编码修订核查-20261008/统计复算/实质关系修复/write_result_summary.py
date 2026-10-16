"""Recheck reported point estimates and write the current readable work report."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
DIMS = ('S', 'E', 'Ec', 'I', 'F')
NAMES = dict(zip(DIMS, ('安全性', '有效性', '经济性', '创新性', '公平性')))
GROUPS = {'NMPA': '药监', 'NHSA': '医保', 'NHC': '卫健'}

def read(p): return json.loads(Path(p).read_text())
def div(a, b): return a / b if b else None
def fmt(x): return 'NA' if x is None else f'{x:.3f}'
def close(a, b): return a is None and b is None or a is not None and b is not None and abs(a-b)<1e-10

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ab-results', required=True)
    args = parser.parse_args()
    abpath = Path(args.ab_results).resolve()
    records = read(abpath)['records']
    assert len(records) == 175
    checks = []
    for r in records:
        cells = r['weighted_cells']
        a,b,c,d = (cells[k] for k in ('11','10','01','00'))
        n = a+b+c+d
        observed = div(a+d,n)
        chance = div((a+b)*(a+c)+(c+d)*(b+d), n*n)
        k = div(observed-chance,1-chance)
        if r['record_type'] == 'machine_vs_existing_reference':
            expected = {'kappa': k, 'precision': div(a,a+b), 'recall': div(a,a+c), 'f1': div(2*a,2*a+b+c)}
            passed = all(close(v,r['metrics'][name]['estimate']) for name,v in expected.items())
        else:
            expected = {'kappa': k, 'agreement': observed, 'A_positive_rate': div(a+b,n), 'B_positive_rate': div(a+c,n)}
            passed = close(k,r['kappa']['estimate']) and all(close(expected[name],r[name]) for name in ('agreement','A_positive_rate','B_positive_rate'))
        assert passed, (r['component'],r['group'],r['comparison'],r['dimension'])
        checks.append({'component':r['component'],'group':r['group'],'comparison':r['comparison'],'dimension':r['dimension'],'four_cell_point_estimates_match':passed})
    checkpath = HERE/'当前同材料结果/既有AB四格公式独立核对.json'
    assert not checkpath.exists()
    checkpath.write_text(json.dumps({'n':len(checks),'all_pass':all(x['four_cell_point_estimates_match'] for x in checks),'source':str(abpath),'source_sha256':hashlib.sha256(abpath.read_bytes()).hexdigest(),'confidence_intervals_not_independently_recomputed':True,'checks':checks},ensure_ascii=False,indent=2)+'\n')
    stats = read(HERE/'当前同材料结果/数据汇总独立核对.json')
    qa = read(HERE/'执行与字面核查.json')
    overall = stats['groups']['ALL']
    selected = [r for r in records if r['component']=='probability_canonical' and r['group']=='ALL']
    machine = [r for r in selected if r['record_type']=='machine_vs_existing_reference']
    def target_count(rs):
        v=[m['estimate'] for r in rs for m in r['metrics'].values()]
        return {'total':len(v),'met':sum(x is not None and x>=.8-1e-12 for x in v),'below':sum(x is not None and x<.8-1e-12 for x in v),'undefined':sum(x is None for x in v)}
    target = target_count(machine)
    target_all = target_count([r for r in records if r['component']=='probability_canonical' and r['record_type']=='machine_vs_existing_reference'])
    kindex={(r['comparison'],r['dimension']):r for r in selected}
    comparisons = ['final_rules_vs_existing_A','final_rules_vs_existing_B','final_LLM_vs_existing_A','final_LLM_vs_existing_B','existing_A_vs_existing_B']
    # Read the actual comparison names rather than silently accepting a new alias.
    assert all((c,d) in kindex for c in comparisons for d in DIMS), sorted({r['comparison'] for r in selected})
    lines=['# 编码重做结果与问题定位','',
        '本次已按统一手册实际重做自动规则编码与LLM编码，各完成4480条。完整目标框为4481条，另1条援引文件的历史适用版本尚无法核定，保留未知。规则进一步修复三个明确的关系识别问题后，已对同一4480条重新完整执行；LLM沿用同一手册及同一来源材料的冻结结果。A、B原始标签未改，B对应归档C。','',
        '## 现在可以从数据看到什么','',
        '两种方法共同呈现的主要部门侧重是：药监与卫健的安全性占比最高，医保的经济性占比最高。创新性、公平性的具体识别范围仍存在明显差异，不能把方法间差异一概解释成合理的技术特点，也不能据此宣称LLM整体更准确。','',
        '### 全量两方法一致性','',
        '|维度|κ|一致率|不同判断数|规则识别句次|LLM识别句次|','|---|---:|---:|---:|---:|---:|']
    for d in DIMS:
        m=overall['dimensions'][d]
        lines.append(f"|{NAMES[d]}|{fmt(m['kappa'])}|{m['agreement']*100:.2f}%|{m['discordant_n']}|{overall['methods']['rule']['counts'][d]}|{overall['methods']['llm']['counts'][d]}|")
    lines+=['','注：4480条相同单元、逐维0/1直接计算，两种机器方法均未被设为真值。大量共同判0可使一致率高而κ低；仍须检查实际分歧内容。此表是方法间一致性，不是人工效度检验。','',
        '### 部门五维注意力占比','',
        '|部门|方法|安全性|有效性|经济性|创新性|公平性|五维句次合计|','|---|---|---:|---:|---:|---:|---:|---:|']
    for group in ('NMPA','NHSA','NHC'):
        for method,title in [('rule','自动规则编码'),('llm','LLM编码')]:
            item=stats['groups'][group]['methods'][method]
            lines.append('|'+GROUPS[group]+'|'+title+'|'+'|'.join(f"{item['attention_percent'][d]:.2f}%" for d in DIMS)+f"|{item['five_dimension_total']}|")
    ni=stats['groups']['NMPA']['dimensions']['I']['attention_difference_llm_minus_rule_pp']
    nf=stats['groups']['NHC']['dimensions']['F']['attention_difference_llm_minus_rule_pp']
    lines+=['',
        '注：各维占比＝该部门该方法该维识别句次／该部门该方法五维识别句次合计。同条可涉及多维，同一维度只计一次。未四舍五入值每行合计100%；该比例不是全部政策条目的覆盖率，也不表示政府评审赋权。独立四舍五入可能造成显示合计相差0.01个百分点。',
        f'药监创新性相差{ni:.2f}个百分点，卫健公平性相差{nf:.2f}个百分点。相同的大体侧重与这些具体差异应分别报告。跨方法还须检查分子和分母：一种方法识别的某维句次增加，占比仍可能因其他维度识别更多而降低，不能直接解释为政策更少关注该维。','',
        '## 与既有A、B的对照','',
        '按原180条概率样本及原设计权重重新计算；60条有目的挑战材料另列。全部175组点估计已经用四格公式独立复核，5000次原设计重抽样区间另附。','',
        '|维度|规则—A κ|规则—B κ|LLM—A κ|LLM—B κ|A—B κ|','|---|---:|---:|---:|---:|---:|']
    for d in DIMS:
        values=[]
        for c in comparisons:
            r=kindex[c,d]
            values.append(fmt(r['kappa']['estimate'] if c=='existing_A_vs_existing_B' else r['metrics']['kappa']['estimate']))
        lines.append('|'+NAMES[d]+'|'+'|'.join(values)+'|')
    lines+=['',
        '|维度|方法|精确率 A/B|召回率 A/B|F1 A/B|','|---|---|---:|---:|---:|']
    for d in DIMS:
        for method,title in [('final_rules','自动规则编码'),('final_LLM','LLM编码')]:
            vals=[]
            for m in ('precision','recall','f1'):
                vals.append('/'.join(fmt(kindex[method+'_vs_existing_'+ref,d]['metrics'][m]['estimate']) for ref in ('A','B')))
            lines.append('|'+NAMES[d]+'|'+title+'|'+'|'.join(vals)+'|')
    lines+=['',
        '注：斜线前后分别以A、B为参照；A—B只报告对称一致性，不把任一编码员设为真值。用户已确认旧标签经真人复核；当前手册存在实质澄清，因此这些数值是旧参照对新方法的迁移诊断，不作为新手册下完成独立盲评的证明。原概率样本的正纳入概率仅覆盖1767个固定代表ID，不能外推为完整4481条目标框的验证。',
        f"按本项目0.80目标，总体{target['total']}个κ/P/R/F1数值中{target['met']}个达到、{target['below']}个低于；连同各部门共{target_all['total']}个数值，{target_all['met']}个达到、{target_all['below']}个低于、{target_all['undefined']}个未定义。未定义不视为达标。阈值使用未四舍五入点估计判断；0.80不是期刊统一发表线。",'',
        '## 本次实际修复与检查','',
        f"规则4480条全部完成，程序失败0条，部分待核{qa['n_undetermined']}条。相对修复前，{qa['changed_row_n']}条标签改变；各维变化次数为{qa['changed_dimension_counts']}。安全性、有效性、经济性没有意外改变。全部已输出证据的位置及完整当前引文已作字面核查；此检查不能代替语义准确性验证。",'',
        '- 创新性：识别“对创新价值进行量化和分级”的实质评价，以及明确面向创新研发的审评便利；不要求一定出现数值时限。真实句03710、02206的漏判已经修复。',
        '- 公平性：取消从一般基本供药目的直接赋值的入口。01090等一般供药句不再自动计入；02556“补齐保障短板—调整目录范围—参保人员用药需要”和03206患者承受能力的实际联系仍保留。',
        '- 否定与条件：保留“不能证明获益大于风险”“并不代表绝对无效”“终止之日起不再优先安排”等完整命题。维度1表示实质议题出现，不表示优势成立、措施仍在提供或政策效果为正。',
        '- 来源：此前已经统一修正流程图箭头与附件/编号等读取问题；本轮方法比较继续使用完全相同的当前材料。LLM只因已核定的单条图示来源改动补跑该条，未按分数挑选结果。','',
        '## 仍需处理的具体问题','',
        '独立设计的10条构造控制经完整入口复检，8条通过，2条仍暴露既有缺口：占位名称“X药”未被药物对象识别，以及跨句“该计划”未承接明确的创新研发计划。后者补齐实际源行定位后仍未确定，不能称为已解决否定句理解；当前输出也没有将其误述为仍提供支持。构造控制不是真人效度样本。',
        '真实分歧中，还须逐条区分行业创新背景与具体药品创新评价、一般保障目标与可指认的公平联系，以及纯维度名称和实质评价要求。两方法不一致并不能自动证明某一方错误。共同手册下的内容边界和机器实现问题应分别裁定，不能为了指标达标直接改旧A、B标签。',
        '后续按同一手册形成与开发用途分开的真人独立判断和裁定参照，再检验分类表现与部门注意力分布的稳健性。正式论文尚未采用本次候选数值，遵循先核验指标再更新正文的顺序。','',
        '## 方法依据','',
        'Mayring（2000）要求把理论类目落实为定义、例子与判定规则；Rasch（2020）的文档分析教程说明编码单位、手册、试用修订与正式编码的衔接。本次据此先检查判据和来源，再执行规则与LLM。[Mayring原文](https://www.qualitative-research.net/index.php/fqs/article/download/1089/2385?inline=1)；[MAXQDA教程](https://www.maxqda.com/blogpost/qualitative-document-analysis)。',
        'Frantz和Siddiki（2024）的制度语法手册区分否定的作用范围，本研究借鉴其阅读原则保留完整命题，没有增加一套制度语法一级变量。[手册](https://arxiv.org/pdf/2008.08937v5)。',
        'Pangakis和Wolken（2025）将共同编码标准、开发与人工验证分开，编码标准实质变化时需重新检查参照标签适用性；Artstein和Poesio（2008）区分一致性与有效性，不支持把单一分数当作所有用途的通用发表线。[Pangakis和Wolken原文](https://ojs.aaai.org/index.php/ICWSM/article/download/35883/38037/39951)；[Artstein和Poesio原文](https://aclanthology.org/J08-4004.pdf)。','',
        '## 可核对文件','',
        f'- [当前完整结果与来源绑定]({HERE}/当前同材料结果/同材料结果绑定.json)',
        f'- [部门占比与四格独立核对]({HERE}/当前同材料结果/数据汇总独立核对.json)',
        f'- [全部A、B对照、各部门结果及区间]({abpath})',
        f'- [本次逐条变动及原文]({HERE}/全量前后标签差异.md)',
        f'- [共用编码手册]({W}/定义溯源核查/测量与计数统一/共用编码手册.md)']
    destination=W/'编码重做结果与问题定位.md'
    assert not destination.exists(), 'Do not silently overwrite an existing report.'
    destination.write_text('\n'.join(lines)+'\n')
    print(json.dumps({'report':str(destination),'point_checks':len(checks),'all_point_checks_pass':True,'target_overall':target,'target_with_departments':target_all},ensure_ascii=False))

if __name__=='__main__': main()

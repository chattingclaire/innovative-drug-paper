"""Build a factual report from sealed metrics, without inferring human validity."""
from pathlib import Path
import json
from analyze_current_reruns import load_sealed_predictions

HERE=Path(__file__).resolve().parent
DEST=HERE.parent/'01a0dbb7-43f0-7a61-a367-7f0c814ee9d4/两方法重跑-20260927'
NAMES={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
METHODS={'rules_baseline':'旧自动版本','rules_v25':'重做自动编码','llm_gpt56_sol':'gpt-5.6-sol'}

def pct(v):return '未定义' if v is None else f'{v:.1%}'
def decimal(v):return '未定义' if v is None else f'{v:.3f}'

def main():
    _,_,_,seal=load_sealed_predictions()
    reports={s:json.loads((HERE/'rerun_comparisons'/s/'metrics.json').read_text()) for s in ('current1268','H427')}
    correction=json.loads((HERE/'rerun_comparisons/LLM更正影响/correction_audit.json').read_text())
    lines=['# 两条编码方法重跑：结果与使用说明','',
        '规则自动编码与 LLM 编码均已按 CAL-5D-20260926-v1.3 对 4,924 个完整分析单元重新执行。LLM 使用用户指定的 gpt-5.6-sol；本次结果不是旧 LLM 得分的改名。',
        '',
        '参照采用本轮已经重做的 A、C 首次编码：已观察及开发材料 1,268 条，新增剩余材料框 427 条，合计 1,695 个不同单元。A、C 均为独立执行语义判定的 AI 评审角色，不是真人编码员；本报告不把它们称为人类金标准。',
        '',
        '所有主分析使用首次完整输出。LLM 全量封存后才打开新增 427 条的参考标签并计算比较。自动规则在新增结果打开前冻结；没有用新增结果调整规则、提示词或定义。',
        '',
        '## 新增 427 条剩余框的比较','',
        '这一组是经暴露登记筛选后的剩余材料框全数评审，权重均为 1。它来自同一语料，不能当作原 4,924 条的代表性随机抽样或外部语料验证。',
        '以下每个 A/C 值分别以 A、C 为参考；每维和每位参考下，三种机器版本使用共同可判定的同一子集。精确率为 TP/(TP+FP)，召回率为 TP/(TP+FN)，F1 为 2TP/(2TP+FP+FN)。','']
    for scope,title in [('H427',None),('current1268','已观察的 1,268 条开发材料')]:
        r=reports[scope]['scenarios']['primary']
        if title:lines += ['## '+title,'','历史设计权重仅用于开发材料上的描述。由于这批材料已被观察和用于开发，不能用本表宣称独立验证通过。','']
        lines += ['|维度|方法|精确率 A/C|召回率 A/C|F1 A/C|共同可判 n A/C|',
                  '|---|---|---:|---:|---:|---:|']
        for d,name in NAMES.items():
            for m,mn in METHODS.items():
                def rates(key):return ' / '.join(pct(r['methods'][c][d]['by_method'][m]['common_units_weighted']['conditional_scores'][key]) for c in ('A','C'))
                n=' / '.join(str(r['methods'][c][d]['common_unit_n']) for c in ('A','C'))
                lines.append(f'|{name}|{mn}|{rates("precision")}|{rates("recall")}|{rates("f1")}|{n}|')
        lines += ['','可判定覆盖情况（各方法自身与参考均可判的比例，未把待定填成 0）：','',
                  '|维度|重做自动覆盖 A/C|LLM覆盖 A/C|参考阳性 n A/C（不加权）|',
                  '|---|---:|---:|---:|']
        for d,name in NAMES.items():
            def cov(m):return ' / '.join(pct(r['methods'][c][d]['by_method'][m]['all_units_unweighted']['joint_determinate_coverage']) for c in ('A','C'))
            pos=' / '.join(str(int(r['methods'][c][d]['by_method']['rules_v25']['all_units_unweighted']['known_reference_positive_n_or_weight'])) for c in ('A','C'))
            lines.append(f'|{name}|{cov("rules_v25")}|{cov("llm_gpt56_sol")}|{pos}|')
        lines += ['']
    lines += ['## 当前 A/C 自身的一致程度','','以下为共同可判条目上的不加权结果。高一致性不排除两个 AI 共享错误，稀少正类尤其应结合正类一致率和实际阳性数量理解。','',
              '|材料组|维度|总体一致率|正类一致率|负类一致率|κ|共同可判 n|',
              '|---|---|---:|---:|---:|---:|---:|']
    for scope in ('H427','current1268'):
        for d,name in NAMES.items():
            r=reports[scope]['scenarios']['primary']['reference_agreement'][d]['unweighted'];a=r['binary_agreement']
            lines.append(f'|{scope}|{name}|{pct(a["observed_agreement"])}|{pct(a["positive_agreement"])}|{pct(a["negative_agreement"])}|{decimal(a["kappa"])}|{int(r["joint_determinate_n_or_weight"])}|')
    lines += ['', '## 首次输出与更正','',
        f'493 批 LLM 首次输出中有 {seal["batches_with_QA_issues"]} 批存在结构、子类型、理由或引文校验问题；问题逐项留在原始 QA 文件与交付表中。主结果保留首次完整标签。',
        f'记录的更正涉及 {len(correction["correction_files"])} 批，{correction["changed_record_n"]} 条记录的字段发生变化，其中 {correction["label_changed_record_n"]} 条记录改变标签。',
        '更正影响按查看新参考结果前写定的规则统一采用每批最后编号的更正，作为次要敏感性分析，不按参考一致率挑选。这里的冻结和预登记均为内部执行记录，不是公开注册。结果见复核材料中的 rerun_comparisons/LLM更正影响/summary.md。',
        '', '## 与正文的衔接','',
        '正文保留已经重做的当前 v1.3 A/C R600+D668 参照主分析，核对其原冻结输入及抽样设计。新规则和新 LLM 的 4,924 条全量分布分别作为平行测量结果，不套用 A/C 的抽样区间，不按新结果的显著性切换主方法。新增 427 条不混入原总体估计。此衔接原则在新参考结果打开前写定。',
        '', '## 使用与复核','',
        '- 两份 AI 评审表各含 1,695 条首次结果及相同版本的规范；按编号可回查原文、理由和证据。',
        '- 对照表含两组统计、1,695 条逐条对照、4,924 条 LLM 全量判断及证据。共用输入和完整语境另存 JSONL，表格没有裁剪正文原文。',
        '- 完整复核包保留规则代码、模型执行规范、首次输出、更正、材料框审计、统计代码、子类型敏感性、待定完成界限及 SHA256 校验清单。',
        '- 待定完成界限表达未决标签的逻辑范围，不是置信区间。未定义指标表示分母为 0，不等于零分。',
        '- 本次符合程度只能相对当前 AI 参考解释；不能据此证明真人效度、构念效度、政策因果作用或实际部门评分权重。',
        '- 五维定义统一不等于每条执行都无误。自动规则与 LLM 的偏差需要分别看，不能用一条方法的成绩替代另一条。','']
    DEST.mkdir(parents=True,exist_ok=True)
    out=DEST/'本轮结论与使用说明.md';assert not out.exists()
    out.write_text('\n'.join(lines)+'\n')
    print(json.dumps({'report':str(out)},ensure_ascii=False))

if __name__=='__main__':main()

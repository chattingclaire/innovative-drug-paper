"""Render completed H600 statistics without selecting favorable comparisons."""
import argparse, json, hashlib
from pathlib import Path
DIMS=('S','E','Ec','I','F')
NAMES={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
def number(x):return 'NA' if x is None else f'{x:.3f}'
def pct(x):return 'NA' if x is None else f'{x*100:.1f}%'
def ci(row,key,percent=False):
    f=pct if percent else number;x=row['marginal_95_intervals'][key]
    if x['estimate'] is None:return 'NA（指标无定义）'
    if x['lower'] is None or x['upper'] is None:
        return '不稳定（无定义复制>10%）' if x['status']=='unstable_more_than_10_percent_undefined' else '不可估'
    suffix=f'；{x["undefined_fraction"]:.1%}复制无定义' if x['undefined_fraction'] else ''
    return f'{f(x["lower"])}—{f(x["upper"])}{suffix}'
def render(data, input_path, input_sha):
    assert data['status']=='completed_frozen_ID_join_not_validation_pass'
    meta=data['design_and_interval_metadata'];assert meta['sample_size_matches_H600_plan'] is True
    n=meta['sample_n'];N=meta['population_N_from_manifest'];arc=data['archive'];rows=arc['normalized_rows_without_generated_reference']
    assert n==len(rows)
    protocol=arc['freeze_manifest_original']['protocol_version']
    versions={data['comparisons'][f'dictionary_vs_{coder}']['dictionary_info']['version'] for coder in ('A','C')}
    assert len(versions)==1
    dictionary_version=next(iter(versions))
    complete=[r for r in rows if all(type(r[c][d]) is int for c in ('A','C') for d in DIMS)]
    exact=sum(r['A']==r['C'] for r in complete)
    out=['# 冻结后H600独立AI编码验证报告','',
         f'已完成同一{n}条的两份独立AI提交，每位{n*5}个维度判断。采用封存手册与语境，协议版本为{protocol}、词典版本为{dictionary_version}；先封存预测及原始评审，随后计算本报告。执行者按人工内容分析流程工作，身份是AI。','',
         f'样本来自排除已知开发及近重复后的固定池U*={N}，按{len(meta["strata"])}个部门×资料年份层无放回抽取；原18及新增60仍是开发资料，不并入本轮。A新会话，C延续开发会话；正式阶段互不读答案及机器判定。材料保留来源标题及页码，因此本轮对另一评审标签和机器预测盲，不对政策来源机关盲。历史原文暴露不能穷尽，同底座AI可能共享错误。','',
         '## 两位评审的原始一致性','',
         f'所有五维均双方可判的完整向量共{len(complete)}/{n}条，其中{exact}条五维相同。以下逐维结果保留其余记录的待定；“共同待定”不作为已完成判断的一致。κ、二元一致及正/负类一致均用设计权重并限于双方可判部分计算；覆盖率分母为全样本设计权重总和。原始阳性数分别统计各评审在全部{n}条中的已判阳性，含对方待定行，不限于双方可判部分；原始数不加权。','',
         '| 维度 | 原始双方可判 | A/C原始阳性 | 加权可判覆盖 | 加权二元一致 | κ（设计权重；95%区间） | 正类/负类一致 |',
         '|---|---:|---:|---:|---:|---|---:|']
    for d in DIMS:
        r=data['comparisons']['A_vs_C']['dimensions'][d];e=r['estimates'];t=r['raw_3x3_counts'];both=sum(t[i][j] for i in (0,1) for j in (0,1));posA=sum(t[1]);posC=sum(t[i][1] for i in range(3))
        out.append(f'| {NAMES[d]} {d} | {both}/{n} | {posA}/{posC} | {pct(e["coverage_both_definite"])} | {pct(e["agreement_definite"])} | {number(e["kappa_definite"])}（{ci(r,"kappa_definite")}） | {pct(e["positive_agreement_definite"])}/{pct(e["negative_agreement_definite"])} |')
    out += ['', '此处使用抽样设计权重估计二元Cohen κ，不是对有序标签设置误差权重的“加权κ”。','', '## 冻结词典分别对照A和C','',
            '两位分别作为明确标注的AI对照，不择优，也不合成为无误真值；两次对照共享同一批样本，不能当作双倍样本量。Precision/Recall/F1使用设计权重，仅在词典与该评审均可判部分计算。Precision的阳性分母来自词典，Recall的阳性分母来自该AI对照；二者都限于双方可判部分。覆盖率及全样本一致率待定补全界另列，PRF补全界及可能无定义标记见统计JSON。','',
            '| 对照 | 维度 | 加权可评覆盖 | Precision | Recall | F1（95%区间） |', '|---|---|---:|---:|---:|---|']
    for c in ('A','C'):
        for d in DIMS:
            r=data['comparisons'][f'dictionary_vs_{c}']['dimensions'][d];e=r['estimates']
            out.append(f'| 词典对{c} | {NAMES[d]} | {pct(e["coverage_both_definite"])} | {pct(e["precision_definite"])} | {pct(e["recall_definite"])} | {number(e["f1_definite"])}（{ci(r,"f1_definite")}） |')
    out += ['', '## 待定与分母边界','', '| 对照 | 维度 | 原始单方/双方待定 | 设计加权全样本一致率补全下界—上界 |', '|---|---|---:|---|']
    for name,title in (('A_vs_C','A与C'),('dictionary_vs_A','词典与A'),('dictionary_vs_C','词典与C')):
        for d in DIMS:
            r=data['comparisons'][name]['dimensions'][d];e=r['estimates'];t=r['raw_3x3_counts'];one=t[2][0]+t[2][1]+t[0][2]+t[1][2]
            out.append(f'| {title} | {d} | {one}/{t[2][2]} | {pct(e["agreement_all_lower"])}—{pct(e["agreement_all_upper"])} |')
    out += ['', '补全界仅表示固定本批样本已判标签与设计权重后、任意二元补全待定的可能范围，不包含抽样误差，不是总体置信区间、实际补标或对照真值。四格表、PRF补全界、补全后可能无定义标记及bootstrap无定义比例见统计JSON；PRF补全界只在指标有定义的补全中取值，NA不补为0。原始理由保存在JSON的原始提交归档中，独立工作簿呈现同一原始提交。','',
            '## 推断范围','',
            '95%区间采用预先固定的分层有限总体重缩放bootstrap，2000次、种子2026092603；为各维各指标的近似区间，不是五维同时95%覆盖。超过10%复制无定义则不提供稳定区间；未超过时仅用有定义复制求分位数，并保留无定义比例。指标本身无定义时显示NA。无定义比例低也不证明稀有阳性指标精确或区间覆盖可靠；高一致率不消除共享AI偏差、操作定义偏差或源文本错误。','',
            '本报告检验冻结版本在U*上的独立AI一致性及相对两位AI的符合程度，不代表原4924条或未来政策的普遍准确率，不构成真人专家金标准验证。历史外部LLM没有同版本重跑，其旧结果不并入本报告。分歧若用于后续改算法，本样本须登记为开发资料，不能仍用作更新版独立验证。','',
            '阳性较少维度的R200补充按已登记固定规则另行执行/报告，不与本表合算。原始A/C提交及首次统计不随讨论覆盖。','',
            f'统计输入：[{input_path.name}]({input_path.resolve()})；SHA-256 `{input_sha}`。']
    return '\n'.join(out)+'\n'

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise RuntimeError('Preserve previous issued report')
    raw=args.input.read_bytes();data=json.loads(raw)
    report=render(data,args.input,hashlib.sha256(raw).hexdigest())
    with args.output.open('x') as handle:handle.write(report)
    meta=data['design_and_interval_metadata'];rows=data['archive']['normalized_rows_without_generated_reference']
    complete=[r for r in rows if all(type(r[c][d]) is int for c in ('A','C') for d in DIMS)]
    print(json.dumps({'report':str(args.output),'n':meta['sample_n'],'population_N':meta['population_N_from_manifest'],'fully_definite_vectors':len(complete),'matching_vectors':sum(r['A']==r['C'] for r in complete)},ensure_ascii=False))
if __name__=='__main__':main()

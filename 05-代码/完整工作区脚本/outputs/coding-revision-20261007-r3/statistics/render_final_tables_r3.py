"""Render already validated final statistics as concise factual JSON/Markdown.

Does not write the manuscript, edit raw labels, or assert human validation.
"""
from pathlib import Path
import argparse
import json
import statistical_core_r3 as c


def f(value):return 'NA' if value is None else f'{value:.3f}'


def main():
    p=argparse.ArgumentParser();p.add_argument('--final-dir',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    assert not args.out.exists()
    freeze=c.read(args.final_dir/'output_freeze.json')
    assert all(c.sha(args.final_dir/name)==digest for name,digest in freeze['files'].items())
    provenance=c.read(args.final_dir/'provenance.json')
    classification=c.read(args.final_dir/'machine_reference_classification.json')['comparisons']
    ac=c.read(args.final_dir/'A_C_final_before_third_agreement.json')['comparisons']
    stability=c.read(args.final_dir/'LLM_identical_request_stability_and_order_sensitivity.json')
    full=c.read(args.final_dir/'full4481_machine_attention_and_file_composition_sensitivity.json')
    points=[{k:row[k] for k in ('component','group','weighting','method','reference','dimension','paired_n','raw_confusion')}
        | {'metrics':{name:row['metrics'][name] for name in ('kappa','precision','recall','f1')},
           'undefined_point_reasons':row['undefined_point_reasons']} for row in classification]
    lines=['五维编码核验：已绑定材料与实际执行的统计表', '',
        '参考为 AI agent A/C 与第三方候选参考；真人核验尚未完成。A/C 角色记录包含来源更新后的替代 agent 复读，不能称同一评审者全程完成。', '',
        '正式规则方法为冻结 v33；后续规则开发版本不进入本表。LLM 为候选02语义基线及明确记录的引文隔离技术恢复；不同实际提示和CLI版本见 provenance.json，不声称所有请求逐字相同。', '',
        '180条概率样本按部门各抽60；总体表按剩余 canonical 框 NMPA947 / NHSA760 / NHC60 设计加权，NHC是该框全查。60条富集挑战样本单列。二者不合并推断全4481条或新政策文档。', '',
        'κ后的括号为近似设计95%区间。NA是未定义，不能替换为1；区间条件于既定材料、标签与方法，不涵盖语义真值不确定性。0.80只作诊断目标，未设为普遍发表门槛。', '']
    for comp,weight,title in [('probability_canonical','eligible_design_weighted','概率180：抽样框设计加权'),
        ('probability_canonical','unweighted','概率180：等额样本构成'),
        ('enriched_challenge','unweighted','挑战60：描述统计')]:
        lines += [title,'','|方法|参考|维度|κ（95%区间）|P|R|F1|TP / FP / FN / TN|','|---|---|---|---|---|---|---|---|']
        for row in points:
            if (row['component'],row['group'],row['weighting'])!=(comp,'ALL',weight):continue
            m=row['metrics'];ci=m['kappa']['ci95_primary']
            vals=[f(m[k]['estimate']) for k in ('precision','recall','f1')]
            cells=' / '.join(str(x) for x in row['raw_confusion'].values())
            lines.append(f"|{row['method']}|{row['reference']}|{row['dimension']}|{f(m['kappa']['estimate'])} ({f(ci['low'])}, {f(ci['high'])})|{'|'.join(vals)}|{cells}|")
        lines.append('')
    lines += ['分部门：相对候选参考（概率样本，每部门60条）','','|方法|部门|维度|κ|P|R|F1|','|---|---|---|---|---|---|---|']
    for row in points:
        if row['component']=='probability_canonical' and row['group']!='ALL' and row['reference']=='candidate':
            vals=[f(row['metrics'][k]['estimate']) for k in ('kappa','precision','recall','f1')]
            lines.append(f"|{row['method']}|{row['group']}|{row['dimension']}|{'|'.join(vals)}|")
    lines += ['', 'A/C 角色记录的第三方介入前一致性','','|样本|部门/加权|维度|κ|一致率|','|---|---|---|---|---|']
    for row in ac:
        if row['group']=='ALL':lines.append(f"|{row['component']}|{row['weighting']}|{row['dimension']}|{f(row['metrics']['kappa']['estimate'])}|{f(row['metrics']['agreement']['estimate'])}|")
    st=next(r for r in stability['identical_prompt_three_runs']['records'] if r['group']=='THREE_DEPARTMENTS')
    order=next(r for r in stability['prompt_order_sensitivity']['records'] if r['group']=='THREE_DEPARTMENTS')
    lines += ['', '三次实际相同请求与一次顺序微扰（预选三整批，三部门72条；全部75条含GOV3条）', '',
        '以下只报告预选原始请求的重复性，不将结果外推为技术追加提示的稳定性，不选择最好一次替换主结果。', '',
        '|维度|三次标签变化条数|三次阳性数范围|顺序微扰κ|顺序微扰一致率|', '|---|---|---|---|---|']
    for d in c.DIMS:
        x=st['three_run_dimensions'][d];z=order['dimensions'][d]
        lines.append(f"|{d}|{x['label_varies_n']}|{'–'.join(map(str,x['positive_count_range']))}|{f(z['kappa'])}|{f(z['agreement'])}|")
    lines += ['', '全4481条的机器注意力、按政策文件/系列等权、逐文件剔除、年度系列最新成员及排除联合发文的敏感性均保存在原始JSON。该全库结果是机器描述统计，参考核验的抽样框范围保持不变。', '',
        '原始指标区间、NA原因、概率注意力与部门配对差异、全库文件构成敏感性及实际执行绑定均见同批统计产物；任何低值不做隐藏或补写。','']
    args.out.mkdir()
    c.write_json(args.out/'readable_metrics.json',{'provenance':provenance,'classification':points,
        'A_C_before_third':ac,'three_run72':st,'order_perturbation72':order,
        'source_statistics_freeze_sha256':c.sha(args.final_dir/'output_freeze.json'),
        'script_sha256':c.sha(Path(__file__))})
    (args.out/'统计核验表.md').write_text('\n'.join(lines))
    c.write_json(args.out/'output_freeze.json',{'files':{p.name:c.sha(p) for p in args.out.iterdir() if p.is_file()}})
    print(json.dumps({'status':'rendered_verified_final_tables','out':str(args.out)},ensure_ascii=False))


if __name__=='__main__':main()

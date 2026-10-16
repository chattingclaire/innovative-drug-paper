"""Display-only report from complete frozen V600 output; no model/statistic calls.

This presentation tool is separate from the frozen inferential programs. It does
not read raw working submissions or predictions, create reference labels, select
metrics by outcome, or calculate new intervals. All five dimensions, both AI
references, both versions and all five secondary scenarios are always displayed.
"""
from pathlib import Path
import argparse
import hashlib
import json

DIMS = ('S', 'E', 'Ec', 'I', 'F')
SCENARIOS = ('safety_without_quality_only', 'innovation_without_qualification_only',
             'fairness_without_management_only', 'fairness_without_information_only',
             'fairness_access_affordability_only')

def number(value, scale=1, digits=3):
    return '不可计算' if value is None else f'{value * scale:.{digits}f}'

def interval(item, scale=1, digits=3):
    point = number(item['estimate'], scale, digits)
    if item['lower'] is None or item['upper'] is None:
        return point + '；区间未给出（' + item['status'] + '）'
    return point + ' [' + number(item['lower'], scale, digits) + ', ' + number(item['upper'], scale, digits) + ']'

def table(lines, headers, rows):
    lines.extend(['', '| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---'] * len(headers)) + '|'])
    for row in rows:
        lines.append('| ' + ' | '.join(str(x).replace('|', '\\|').replace('\n', '<br>') for x in row) + ' |')
    lines.append('')

def delta_rows(stats):
    rows = []
    for c in ('A', 'C'):
        for d, obj in stats['paired_differences'][c]['dimensions'].items():
            counts = obj['baseline_common_subset']['raw_2x2_counts']
            positive = counts[0][1] + counts[1][1]
            delta = obj['candidate_minus_baseline']
            rows.append([c, d, obj['raw_jointly_definite_n'], positive,
                number(obj['weighted_joint_coverage'], 100, 1),
                obj['raw_baseline_only_assessable_n'], obj['raw_candidate_only_assessable_n'],
                interval(delta['recall_definite'], 100, 1), interval(delta['f1_definite'], 100, 1),
                f"{delta['recall_definite']['undefined_replicates']}/{delta['f1_definite']['undefined_replicates']}"])
    return rows

DELTA_HEADERS = ['参考AI', '维度', '共同可判n', '共同可判参考阳性n', '共同加权覆盖%',
                 '仅旧版可判n', '仅新版可判n', 'ΔRecall百分点 [95%区间]',
                 'ΔF1百分点 [95%区间]', '无定义复制数 R/F1']

def render(primary, secondary, provenance):
    assert primary['status'] == 'completed_frozen_paired_ID_join_not_validation_pass'
    assert primary['phase'] == 'V600'
    stats = primary['paired_statistics']; archive = primary['archive']
    assert secondary['status'] == 'alternative_operationalization_secondary'
    assert secondary['source_primary_sha256'] == provenance['primary']['sha256']
    assert secondary['freeze_manifest_sha256'] == archive['input_snapshot_hashes']['freeze']
    assert stats['reference_generated'] is False
    assert set(stats['comparisons']) == {'A_vs_C', 'baseline_vs_A', 'baseline_vs_C', 'candidate_vs_A', 'candidate_vs_C'}
    assert set(stats['paired_differences']) == {'A', 'C'}
    assert all(set(v['dimensions']) == set(DIMS) for v in stats['comparisons'].values())
    assert all(set(v['dimensions']) == set(DIMS) for v in stats['paired_differences'].values())
    assert set(secondary['scenarios']) == set(SCENARIOS)
    assert secondary['sample_n'] == stats['sample_n'] and secondary['population_N'] == stats['population_N']
    assert secondary['bootstrap_seed'] == stats['bootstrap']['seed']
    lines = ['# V600 独立AI编码与同输入版本比较', '',
        f"本报告展示同一概率样本的 {stats['sample_n']} 条原始独立判断，推断范围为最终排除已知暴露后的 {stats['population_N']} 条有限框。两位评审实际为AI，按人工内容分析流程判读；没有真人金标准或共识裁定。",
        '', f"比较版本：{stats['versions']['baseline']['version']} 与 {stats['versions']['candidate']['version']}。两版使用相同输入；旧实现不消费新增对象适用范围字段，须将这一实现差异纳入解释。",
        '', '下列数值全部来自完整封存结果。逐维差值方向为新版减旧版；不根据改善幅度筛选维度、参考评审或敏感性场景。区间为预定的分层有限总体bootstrap逐项近似95%区间，不是同时区间，不包含AI共同偏差或标签测量误差。',
        '', '## 两位AI的首次独立一致性', '',
        '阳性数及待定数是原始样本计数；覆盖、κ和正负一致性使用设计权重。原始3×3表包含待定，不将待定回填0。']
    rows = []; agreement_rows = []
    for d in DIMS:
        obj = stats['comparisons']['A_vs_C']['dimensions'][d]; t = obj['raw_3x3_counts']; e = obj['estimates']
        both = sum(t[i][j] for i in (0, 1) for j in (0, 1))
        rows.append([d, both, sum(t[1]), sum(r[1] for r in t), sum(t[2]), sum(r[2] for r in t),
            number(e['coverage_left'], 100, 1), number(e['coverage_right'], 100, 1), number(e['coverage_both_definite'], 100, 1)])
        ci = obj['marginal_95_intervals']
        agreement_rows.append([d, interval(ci['agreement_definite'], 100, 1), interval(ci['kappa_definite']),
            interval(ci['positive_agreement_definite'], 100, 1), interval(ci['negative_agreement_definite'], 100, 1)])
    table(lines, ['维度', '双方可判n', 'A阳性n', 'C阳性n', 'A待定n', 'C待定n', 'A加权可判%', 'C加权可判%', '双方加权覆盖%'], rows)
    table(lines, ['维度', '一致率% [95%区间]', 'κ [95%区间]', '正一致性% [95%区间]', '负一致性% [95%区间]'], agreement_rows)
    lines.extend(['## 两版分别相对A/C的符合程度', '',
        '每项PRF使用该版本与该评审双方明确二元的范围。各版本分母可能不同；下表的F1不能直接相减代替后面的成对差值。参考阳性n为该比较可判范围内的原始数量。'])
    rows = []; bounds = []
    for tag, label in [('baseline', '旧版'), ('candidate', '新版')]:
        for c in ('A', 'C'):
            for d in DIMS:
                obj = stats['comparisons'][tag + '_vs_' + c]['dimensions'][d]
                e = obj['estimates']; t = obj['raw_3x3_counts']; ci = obj['marginal_95_intervals']
                rows.append([label, c, d, sum(t[i][j] for i in (0, 1) for j in (0, 1)), t[0][1] + t[1][1],
                    number(e['coverage_both_definite'], 100, 1), sum(t[2]), sum(r[2] for r in t),
                    interval(ci['precision_definite'], 100, 1), interval(ci['recall_definite'], 100, 1), interval(ci['f1_definite'], 100, 1)])
                bounds.append([label, c, d] + [number(e[m + '_all_lower'], 100, 1) + '—' + number(e[m + '_all_upper'], 100, 1)
                    + ('；可无定义' if obj['completion_and_undefined_flags'][m + '_can_be_undefined'] else '') for m in ('precision', 'recall', 'f1')])
    table(lines, ['版本', '参考AI', '维度', '双方可判n', '参考阳性n', '加权覆盖%', '机器待定n', '参考待定n',
                  'Precision% [95%区间]', 'Recall% [95%区间]', 'F1% [95%区间]'], rows)
    lines.extend(['## 同样本成对版本差值', '',
        '只在两版与该评审共同可判范围计算。参考阳性数、共同覆盖及不对称弃判同时展示。Recall/F1无定义复制超过10%时不提供区间；无定义比例较低也不能证明稀有阳性充分。'])
    table(lines, DELTA_HEADERS, delta_rows(stats))
    lines.extend(['## 待定的全样本补全界', '',
        '这些范围枚举原始待定标签的可能补全，不是置信区间；不用于改写原始标签，也不是成对差值的界。'])
    table(lines, ['版本', '参考AI', '维度', 'Precision补全界%', 'Recall补全界%', 'F1补全界%'], bounds)
    lines.extend(['## 预定的五项次要敏感性', '',
        '每一列仅按自己的原始子类型改变操作化标签，全部单元、设计权重和原待定保留。参考阳性分母会重算。这些结果不替代主结果，不证明原4924条的部门排序。'])
    for scenario in SCENARIOS:
        item = secondary['scenarios'][scenario]
        lines.extend(['### ' + scenario, '', item['definition']['definition'], '', '状态：' + item['status'] + '。'])
        if item['status'] == 'not_calculable':
            assert item['statistics'] is None and not item['transformation_applied']
            lines.append('必要子类型缺失、未知或不一致；未删除问题记录后继续计算。完整逐ID问题清单保存在次要分析JSON。')
            table(lines, ['列', '维度', '字段', '原因'], [[i['column'], i['dimension'], i['field'], i['reason']] for i in item['issues']])
            continue
        assert item['status'] == 'completed'
        table(lines, ['编码列', '由1变0的条数', '变换后原始阳性n', '原始待定n'],
              [[c, len(item['actual_changed_ids_by_column'][c]), item['positive_and_denominator_counts']['columns'][c]['raw_positive_n'],
                item['positive_and_denominator_counts']['columns'][c]['raw_pending_n']] for c in ('A', 'C', 'baseline', 'candidate')])
        table(lines, DELTA_HEADERS, delta_rows(item['statistics']))
        srows = []
        for name, comp in item['statistics']['comparisons'].items():
            for d, obj in comp['dimensions'].items():
                e = obj['estimates']
                if name == 'A_vs_C':
                    srows.append([name, d, number(e['coverage_both_definite'], 100, 1), interval(obj['marginal_95_intervals']['kappa_definite']), '—', '—', '—'])
                else:
                    srows.append([name, d, number(e['coverage_both_definite'], 100, 1), '—'] +
                        [interval(obj['marginal_95_intervals'][m + '_definite'], 100, 1) for m in ('precision', 'recall', 'f1')])
        table(lines, ['比较', '维度', '双方加权覆盖%', 'κ [95%区间]', 'Precision% [95%区间]', 'Recall% [95%区间]', 'F1% [95%区间]'], srows)
    lines.extend(['## 证据边界和原始文件', '',
        '本报告不自动给出“验证通过”的结论。一致性、机器相对AI的符合程度与概念效度是不同证据。两个AI可能共享偏差；来源标题和页码可见。样本排除了已知开发暴露，不能将结果直接推广至原4924条、未来政策或真实部门价值排序。历史外部LLM未按本轮同输入重跑，不在本次验证范围内。', '',
        '原H600/R200结果保留；本轮使用不同候选框，不能把跨轮分数之差解释为模型改进。没有真人评议，不能据此写成人工金标准、专家效度、Delphi或CVI。', '',
        '完整原始3×3表、加权计数、复制无定义标记、各条原始提交及版本绑定均在完整JSON中保留。展示脚本只读取已完成结果并格式化，不重算区间或改标。'])
    for name, info in provenance.items():
        lines.append(f"\n- [{name}]({info['path']})，SHA-256：`{info['sha256']}`。")
    return '\n'.join(lines) + '\n'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--primary', type=Path, required=True); p.add_argument('--secondary', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); args = p.parse_args()
    assert not args.output.exists(), 'Never overwrite a released report'
    blobs = {name: path.read_bytes() for name, path in [('primary', args.primary), ('secondary', args.secondary)]}
    provenance = {name: {'path': str(path.resolve()), 'sha256': hashlib.sha256(blobs[name]).hexdigest()}
                  for name, path in [('primary', args.primary), ('secondary', args.secondary)]}
    result = render(json.loads(blobs['primary']), json.loads(blobs['secondary']), provenance)
    assert args.primary.read_bytes() == blobs['primary'] and args.secondary.read_bytes() == blobs['secondary']
    with args.output.open('x') as f: f.write(result)
    print(json.dumps({'status': 'display_only_report_written', 'output': str(args.output), 'statistics_recomputed': False}, ensure_ascii=False))

if __name__ == '__main__': main()

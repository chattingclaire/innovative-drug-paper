"""Readable, strictly descriptive R200 results after complete independent submissions."""
import argparse
import hashlib
import json
from pathlib import Path

DIMS = ('S', 'E', 'Ec', 'I', 'F')
NAMES = {'S': '安全性', 'E': '有效性', 'Ec': '经济性', 'I': '创新性', 'F': '公平性'}
BUCKETS = {'dictionary_positive': '词典阳性候选',
           'wide_search_dictionary_negative': '宽检索命中的词典阴性候选',
           'random_dictionary_negative': '剩余词典阴性随机候选',
           'dictionary_positive_fill': '词典阳性候选补足',
           'wide_search_dictionary_negative_fill': '宽检索词典阴性候选补足',
           'random_dictionary_negative_fill': '剩余词典阴性候选补足',
           'remaining_random_fill': '其余剩余池随机补足'}

def f(value, percentage=False):
    return 'NA' if value is None else f'{value:.1%}' if percentage else f'{value:.3f}'

def render(data, input_path, input_sha):
    assert data['status'] == 'completed_challenge_descriptive_ID_join_not_validation_pass'
    assert not data['population_inference'] and not data['population_weights_used']
    assert not data['confidence_intervals_computed'] and not data['reference_generated']
    n = data['sample_n']
    assert 0 < n <= 200
    plan = data['archive']['sampling_manifest_original']['plan']
    protocol = data['archive']['freeze_manifest_original']['protocol_version']
    versions = {data['comparisons'][f'dictionary_vs_{coder}']['dictionary_info']['version'] for coder in ('A', 'C')}
    assert len(versions) == 1
    dictionary_version = next(iter(versions))
    out = ['# R200补充挑战集独立AI编码结果', '',
           f'两位各自按封存共同协议{protocol}完成同一{n}条，提交后统一对照冻结词典{dictionary_version}，版本绑定见原始统计归档。本集合按H600结束前已登记的规则，在剩余U*中定向抽取。触发维度顺序为：{"、".join(plan["targets"])}。', '',
           '80条词典阳性候选、80条宽检索命中且词典阴性候选、40条剩余词典阴性候选构成预定预算；不足时依登记顺序补足。候选分组及机器标签未展示给评审。来源标题及页码保留，本轮不对政策来源机关盲。实际候选来源数量见下表。', '',
           '| 实际候选来源 | 条数 |', '|---|---:|']
    for bucket, count in plan['bucket_counts'].items():
        out.append(f'| {BUCKETS.get(bucket,bucket)} | {count} |')
    out += ['', '这是定向挑战集合的描述，不能代表U*或全部政策语料；不与H600合并总体κ、准确率或置信区间。每条只计一次，不因有两份独立提交而把样本数加倍。', '',
            '## 两位原始提交的一致性', '',
            f'所有计数均为本集合原始条数、不加权。κ为二元Cohen κ；κ、二元一致及正/负类一致仅在双方可判部分计算，可判覆盖的分母为全部{n}条。A/C阳性数分别统计各评审在全部{n}条中的已判阳性，含对方待定行。以下均为本集合点描述，不提供总体置信区间。', '',
            '| 维度 | 双方可判 | A/C阳性 | 可判覆盖 | 二元一致 | κ | 正类/负类一致 |',
            '|---|---:|---:|---:|---:|---:|---:|']
    for dim in DIMS:
        result = data['comparisons']['A_vs_C']['dimensions'][dim]
        v, table = result['descriptive_values'], result['raw_3x3_counts']
        definite = sum(table[i][j] for i in (0, 1) for j in (0, 1))
        positives = f'{sum(table[1])}/{sum(table[i][1] for i in range(3))}'
        out.append(f'| {NAMES[dim]} {dim} | {definite}/{n} | {positives} | {f(v["coverage_both_definite"],True)} | {f(v["agreement_definite"],True)} | {f(v["kappa_definite"])} | {f(v["positive_agreement_definite"],True)}/{f(v["negative_agreement_definite"],True)} |')
    out += ['', '## 词典分别对照A和C', '',
            'A、C均为独立AI对照，未生成裁定真值。以下分类比例只针对词典与该AI均可判部分：Precision的阳性分母来自词典，Recall的阳性分母来自该AI对照；覆盖率分母为全部样本。并列显示全样本一致率补全界，A/C一致率及PRF补全界与可能无定义标记见统计JSON。', '',
            '| 对照 | 维度 | 可判覆盖 | Precision | Recall | F1 | 全样本一致率待定补全界 |',
            '|---|---|---:|---:|---:|---:|---|']
    for coder in ('A', 'C'):
        for dim in DIMS:
            v = data['comparisons'][f'dictionary_vs_{coder}']['dimensions'][dim]['descriptive_values']
            out.append(f'| 词典对{coder} | {dim} | {f(v["coverage_both_definite"],True)} | {f(v["precision_definite"],True)} | {f(v["recall_definite"],True)} | {f(v["f1_definite"])} | {f(v["agreement_all_lower"],True)}—{f(v["agreement_all_upper"],True)} |')
    out += ['', '补全界是在已判标签固定后任意补全待定得到的可能范围，不含抽样误差，不是总体置信区间，也不是对待定的实际赋值。PRF补全界只在指标有定义的补全中取值，同时保留可能无定义标记。NA保持不可估，不替换成0或1。预算结束后阳性不足或分歧较多均照实保留，不再重抽以改善结果。', '',
            '本轮沿用同两位AI：A为正式阶段新会话，C延续开发会话。两者可能共享模型偏差，不能将其改称真人专家验证。H600与R200均未提供历史外部LLM同版本重跑的证据。若据这些分歧修改算法，须另登记后续开发并重新建立独立验证。', '',
            f'原始统计：[{input_path.name}]({input_path.resolve()})；SHA-256 `{input_sha}`。']
    return '\n'.join(out) + '\n'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Preserve existing report'
    raw = args.input.read_bytes()
    report = render(json.loads(raw), args.input, hashlib.sha256(raw).hexdigest())
    with args.output.open('x') as handle:
        handle.write(report)
    print(json.dumps({'report': str(args.output)}, ensure_ascii=False))

if __name__ == '__main__':
    main()

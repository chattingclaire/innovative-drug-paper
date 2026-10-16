"""Descriptive sensitivity audit of frozen 4,924-unit parallel measurements.

No labels or A/C primary estimates are edited. Census machine distributions are
not assigned sampling confidence intervals or statistical significance.
"""
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations
import hashlib
import json
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'outputs/autocode-v25-20260927'
CURRENT = ROOT / 'outputs/autocode-v28-review-20261004-111306'
CLASSIFICATION = ROOT / 'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
sys.path.insert(0, str(BASE))
from analyze_current_reruns import load_sealed_predictions, scenario_labels

DIMS = ('S', 'E', 'Ec', 'I', 'F')
GROUPS = ('NMPA', 'NHSA', 'NHC', 'GOV')
COMPARISON_GROUPS = ('NMPA', 'NHSA', 'NHC')
METHODS = ('rules_v28_2', 'llm_gpt56_sol_v13_original')
SCENARIOS = ('primary', 'exclude_quality_only',
    'exclude_F_clinical_management_only', 'F_access_affordability_only',
    'exclude_F_dimension_information_only', 'exclude_I_qualification_advantage_only')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def jsonl(path):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    mapping = {row['id']: row for row in rows}
    assert len(mapping) == len(rows), 'Duplicate ID'
    return mapping

def normalize(value):
    if value in (0, 1) and not isinstance(value, bool):
        return value
    if value == '待定':
        return value
    raise ValueError(f'Unrecognized label: {value!r}')

def summary(rows, method, scenario='primary'):
    result = {}
    for group in (*GROUPS, 'ALL'):
        selected = rows if group == 'ALL' else [r for r in rows if r['metadata']['analysis_group'] == group]
        counts = {d: Counter(normalize(r['scenarios'][method][scenario][d]) for r in selected) for d in DIMS}
        result[group] = {d: {
            'N': len(selected), 'positive_n': counts[d][1], 'negative_n': counts[d][0],
            'pending_n': counts[d]['待定'],
            'positive_proportion': counts[d][1] / len(selected) if selected else None,
            'completion_lower': counts[d][1] / len(selected) if selected else None,
            'completion_upper': (counts[d][1] + counts[d]['待定']) / len(selected) if selected else None,
        } for d in DIMS}
    return result

def equalized(rows, method, field):
    buckets = defaultdict(list)
    for row in rows:
        buckets[row['metadata'][field]].append(row)
    by_group = defaultdict(list)
    for key, values in buckets.items():
        group = values[0]['metadata']['analysis_group']
        assert all(v['metadata']['analysis_group'] == group for v in values), f'Cross-department cluster: {key}'
        by_group[group].append(summary(values, method)['ALL'])
    result = {}
    for group in (*GROUPS, 'ALL'):
        values = [x for chunks in by_group.values() for x in chunks] if group == 'ALL' else by_group[group]
        result[group] = {d: {
            'cluster_n': len(values),
            'positive_proportion': sum(v[d]['positive_proportion'] for v in values) / len(values) if values else None,
            'completion_lower': sum(v[d]['completion_lower'] for v in values) / len(values) if values else None,
            'completion_upper': sum(v[d]['completion_upper'] for v in values) / len(values) if values else None,
        } for d in DIMS}
    return result

def sign(value, tolerance=1e-12):
    return 1 if value > tolerance else -1 if value < -tolerance else 0

def comparisons(group_summary):
    result = []
    for g1, g2 in combinations(COMPARISON_GROUPS, 2):
        for dimension in DIMS:
            left, right = group_summary[g1][dimension], group_summary[g2][dimension]
            if left['positive_proportion'] is None or right['positive_proportion'] is None:
                result.append({'pair': [g1, g2], 'dimension': dimension, 'observed_direction': None,
                    'completion_lower_delta': None, 'completion_upper_delta': None, 'completion_robust_direction': None})
                continue
            delta = left['positive_proportion'] - right['positive_proportion']
            low = left['completion_lower'] - right['completion_upper']
            high = left['completion_upper'] - right['completion_lower']
            result.append({'pair': [g1, g2], 'dimension': dimension, 'observed_delta_pp': delta * 100,
                'observed_direction': sign(delta), 'completion_lower_delta': low,
                'completion_upper_delta': high,
                'completion_robust_direction': 1 if low > 0 else -1 if high < 0 else 0 if low == high == 0 else None})
    return result

def change_report(primary, sensitivity):
    baseline = {(tuple(c['pair']), c['dimension']): c for c in comparisons(primary)}
    current = comparisons(sensitivity)
    for c in current:
        b = baseline[(tuple(c['pair']), c['dimension'])]
        c['baseline_direction'] = b['observed_direction']
        c['reversal_from_primary'] = c['observed_direction'] is not None and b['observed_direction'] is not None and c['observed_direction'] * b['observed_direction'] == -1
        c['changed_direction_from_primary'] = c['observed_direction'] != b['observed_direction']
    return {'comparisons': current, 'reversal_n': sum(c['reversal_from_primary'] for c in current),
        'changed_direction_n': sum(c['changed_direction_from_primary'] for c in current)}

def main():
    # This helper verifies the frozen LLM prediction seal and all output bindings.
    _, llm, llm_inputs, seal = load_sealed_predictions()
    predictions = jsonl(CURRENT / 'all_predictions.jsonl')
    inputs = jsonl(CURRENT / 'rule_inputs_v27.jsonl')
    manifest = json.loads((CURRENT / 'release_manifest.json').read_text())
    for field, filename in [('output_bindings', 'all_predictions.jsonl'), ('code_and_input_bindings', 'rule_inputs_v27.jsonl')]:
        current_path = CURRENT / filename
        key = filename if field == 'output_bindings' else str(current_path)
        assert manifest[field][key] == sha(current_path)
    metadata = json.loads(CLASSIFICATION.read_text())
    frozen_rows = metadata['rows']
    classification = {Path(r['original_file']).stem: r for r in frozen_rows}
    assert len(classification) == len(frozen_rows) == 55
    assert set(predictions) == set(inputs) == set(llm) == set(llm_inputs)
    assert len(predictions) == 4924
    unmatched, used, rows = [], set(), []
    missing_subtypes = {m: Counter() for m in METHODS}
    for rid, item in inputs.items():
        original_stem = item['input']['original_file_stem']
        if original_stem not in classification:
            unmatched.append({'id': rid, 'original_file_stem': original_stem})
            continue
        meta = {**classification[original_stem], 'policy_file_stem': original_stem}
        used.add(original_stem)
        assert item['input']['unit_text'] == llm_inputs[rid]['text']
        rule = predictions[rid]['prediction']
        assert rule['version'] == 'v28.2-five-dimension-discrepancy-audit-20261004'
        assert rule['unit_text_sha256'] == hashlib.sha256(item['input']['unit_text'].encode()).hexdigest()
        records = {METHODS[0]: rule, METHODS[1]: llm[rid]}
        scenarios = {}
        for method, record in records.items():
            assert set(record['labels']) == set(DIMS)
            for d in DIMS:
                normalize(record['labels'][d])
            if record['labels']['I'] == 1 and not record.get('innovation_subtypes'):
                missing_subtypes[method]['I_positive_missing_subtype'] += 1
            if record['labels']['F'] == 1 and not record.get('fairness_subtypes'):
                missing_subtypes[method]['F_positive_missing_subtype'] += 1
            if record['labels']['S'] == 1 and record.get('safety_quality_basis') not in {'quality_only', 'quality_and_other', 'no_quality_basis'}:
                missing_subtypes[method]['S_positive_missing_quality_basis'] += 1
            scenarios[method] = {scenario: scenario_labels(record, scenario) for scenario in SCENARIOS}
        rows.append({'id': rid, 'metadata': meta, 'scenarios': scenarios})
    assert not unmatched
    assert len(used) == 55

    primary = {m: summary(rows, m) for m in METHODS}
    assert [primary[METHODS[0]]['ALL'][d]['positive_n'] for d in DIMS] == [420, 320, 645, 138, 313]
    old_parallel = json.loads((BASE / 'rerun_comparisons/full_corpus_parallel/parallel_full_corpus.json').read_text())
    for group in (*GROUPS, 'ALL'):
        for d in DIMS:
            old = old_parallel['methods']['llm_gpt56_sol']['primary'][group][d]
            for key in ('N', 'positive_n', 'negative_n', 'pending_n'):
                assert primary[METHODS[1]][group][d][key] == old[key], (group, d, key)

    latest_year = {}
    for meta in frozen_rows:
        if meta['annual_series']:
            latest_year[meta['policy_series']] = max(latest_year.get(meta['policy_series'], -1), meta['year_in_filename'])
    latest_rows = [r for r in rows if not r['metadata']['annual_series'] or
        r['metadata']['year_in_filename'] == latest_year[r['metadata']['policy_series']]]
    no_joint = [r for r in rows if not r['metadata']['joint_publication']]
    sensitivities = {}
    file_buckets = defaultdict(list)
    for row in rows:
        file_buckets[row['metadata']['policy_file_stem']].append(row)
    for method in METHODS:
        value = {
            'definition_boundaries': {s: summary(rows, method, s) for s in SCENARIOS if s != 'primary'},
            'policy_file_equal_weight': equalized(rows, method, 'policy_file_stem'),
            'policy_series_equal_weight': equalized(rows, method, 'policy_series'),
            'latest_member_of_annual_series_only': summary(latest_rows, method),
            'exclude_all_joint_publications': summary(no_joint, method),
        }
        value['scenario_direction_changes'] = {name: change_report(primary[method], res) for name, res in value.items() if name != 'definition_boundaries'}
        value['definition_direction_changes'] = {name: change_report(primary[method], res) for name, res in value['definition_boundaries'].items()}
        baseline_comps = {(tuple(c['pair']), c['dimension']): c for c in comparisons(primary[method])}
        loo = []
        for file_stem, discarded in file_buckets.items():
            retained = [r for r in rows if r['metadata']['policy_file_stem'] != file_stem]
            group_summary = summary(retained, method)
            changes = change_report(primary[method], group_summary)
            loo.append({'discarded_file': file_stem, 'discarded_unit_n': len(discarded),
                'discarded_group': discarded[0]['metadata']['analysis_group'],
                'distribution': group_summary, 'direction_changes': changes})
        value['leave_one_policy_file_out'] = loo
        value['leave_one_policy_file_summary'] = {
            'file_n': len(loo),
            'reversal_case_n': sum(x['direction_changes']['reversal_n'] for x in loo),
            'files_with_reversals': [x['discarded_file'] for x in loo if x['direction_changes']['reversal_n']],
            'reversed_pairs': [dict(c, discarded_file=x['discarded_file']) for x in loo for c in x['direction_changes']['comparisons'] if c['reversal_from_primary']],
            'proportion_ranges': {g: {d: {
                'minimum': min(x['distribution'][g][d]['positive_proportion'] for x in loo if x['distribution'][g][d]['positive_proportion'] is not None),
                'maximum': max(x['distribution'][g][d]['positive_proportion'] for x in loo if x['distribution'][g][d]['positive_proportion'] is not None),
            } for d in DIMS} for g in (*GROUPS, 'ALL')},
        }
        sensitivities[method] = value

    pairwise = []
    rule_comps, llm_comps = comparisons(primary[METHODS[0]]), comparisons(primary[METHODS[1]])
    for rule_cmp, llm_cmp in zip(rule_comps, llm_comps):
        assert (rule_cmp['pair'], rule_cmp['dimension']) == (llm_cmp['pair'], llm_cmp['dimension'])
        pairwise.append({'pair': rule_cmp['pair'], 'dimension': rule_cmp['dimension'],
            METHODS[0]: rule_cmp, METHODS[1]: llm_cmp,
            'observed_direction_agrees': rule_cmp['observed_direction'] == llm_cmp['observed_direction'],
            'both_robust_to_pending_and_agree': rule_cmp['completion_robust_direction'] is not None and rule_cmp['completion_robust_direction'] == llm_cmp['completion_robust_direction']})

    ac_primary_path = ROOT / 'outputs/validation-expansion-20260926/D668-原4924范围主统计.json'
    ac_sensitivity_path = ROOT / 'outputs/validation-expansion-20260926/D668-描述性敏感性统计.json'
    ac_plan_path = ROOT / 'outputs/validation-expansion-20260926/D668-前瞻统计方案.md'
    ac_primary = json.loads(ac_primary_path.read_text())
    ac_stats = ac_primary['statistics']
    assert ac_stats['design']['population_size'] == 4924
    assert ac_stats['design']['sample_size'] == 1268
    assert ac_stats['design']['department_sizes'] == {g: primary[METHODS[0]][g]['S']['N'] for g in GROUPS}
    ac_inventory = {
        'status': ac_primary['status'], 'method_version': ac_stats['metadata']['method_version'],
        'sample_units': ac_stats['metadata']['unique_sample_units'],
        'strata': len(ac_stats['design']['strata']), 'simultaneous_parameter_family_n': ac_stats['metadata']['family_size'],
        'department_status_estimate_row_n': len(ac_stats['department_status_estimates']),
        'overall_status_estimate_row_n': len(ac_stats['overall_status_estimates']),
        'coder_pairwise_difference_n': len(ac_stats['coder_pairwise_differences']),
        'common_direction_comparison_n': len(ac_stats['common_robust_directions']),
        'common_robust_direction_n': sum(r['common_robust_direction'] != 'not_orderable' for r in ac_stats['common_robust_directions']),
        'content_labels_and_statistics_changed': False,
        'scope': 'Existing frozen sources inspected and recorded; no new A/C coding, graph regeneration, or human validation.',
    }

    report = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'Fixed 4924-unit machine census, descriptive post-development sensitivity audit; not independent validation',
        'versions': {METHODS[0]: 'v28.2-five-dimension-discrepancy-audit-20261004', METHODS[1]: 'Original sealed CAL-5D-v1.3 gpt-5.6-sol September 27 run; no v29 model rerun'},
        'A_C_main_analysis': 'Unchanged original frozen R600+D668 weighted estimates; A/C are AI reference submissions, not completed human validation',
        'A_C_frozen_primary_inventory': ac_inventory,
        'mapping': {'classification_version': metadata['version'], 'policy_file_n': len(used),
            'all_unit_n': len(rows), 'unmatched': unmatched, 'unused_classification_rows': [k for k in classification if k not in used],
            'join_key': 'Current input.original_file_stem == Path(frozen original_file).stem exactly; unit_source not used to infer institution',
            'group_unit_counts': dict(Counter(r['metadata']['analysis_group'] for r in rows)),
            'group_policy_file_counts': dict(Counter(meta['analysis_group'] for meta in frozen_rows)),
            'annual_series_latest_year': latest_year,
            'policy_series_n': len(set(r['metadata']['policy_series'] for r in rows)),
            'no_joint_unit_n': len(no_joint), 'latest_member_unit_n': len(latest_rows)},
        'missing_subtype_metadata_for_positive_labels': {m: dict(c) for m, c in missing_subtypes.items()},
        'primary_distributions': primary,
        'sensitivity_estimands': {
            'primary': 'Each analysis unit weight 1, including pending units in the denominator.',
            'policy_file_equal_weight': 'Compute unit proportion within each of 55 frozen policy files, then average equally within each department; no artificial equalization by extraction/attachment path.',
            'policy_series_equal_weight': 'Pool units within each frozen policy series, then average the resulting series proportions equally within each department (39 clusters overall).',
            'latest_member_of_annual_series_only': 'For the 5 frozen annual series, retain every policy file with the largest frozen filename year (2026); retain all nonannual policies; units remain equally weighted (3526 units).',
            'exclude_all_joint_publications': 'Discard all policies flagged as joint in the frozen mapping, then retain unit weighting (3992 units). GOV remains separately displayed.',
            'leave_one_policy_file_out': 'Discard each of 55 frozen policy files once; recalculate unit-weighted distributions and the same 15 three-department directional comparisons each time.',
            'definition_boundaries': 'Apply the five previously recorded semantic boundary scenarios using each prediction version\'s own explicit subtypes; a positive without required metadata becomes pending, not zero.',
        },
        'between_method_department_directions': {'pair_n': len(pairwise), 'observed_direction_agrees_n': sum(x['observed_direction_agrees'] for x in pairwise),
            'pending_robust_and_agree_n': sum(x['both_robust_to_pending_and_agree'] for x in pairwise), 'rows': pairwise},
        'sensitivities': sensitivities,
        'limits': [
            'All distributions are descriptive finite-corpus proportions. Completion lower/upper bounds only show unresolved labels, not sampling confidence intervals or classification uncertainty.',
            'Primary unit-weighted, file-equal-weight and series-equal-weight statistics measure different quantities. Differences are disclosed as sensitivity, not substituted after looking at results.',
            'Leave-one-file and file/series equalization were run after development; no claim of preregistration or independent validation.',
            'Current rule inputs have additional documented context for 104 units relative to older input material. This is a versioned parallel measurement comparison, not a controlled test attributing all disagreement only to model type.',
            'Five definition sensitivities use each version\'s own recorded metadata; no old rule metadata copied into v28. Missing positive subtype metadata becomes pending in that scenario.',
            'Dimension-information sensitivity applies only to recorded F dimension_information subtype. Untagged all-dimension informational content is not inferred.',
            'This report does not recalculate or replace A/C weighted primary estimates, simultaneous uncertainty envelopes, reference kappa, or every manuscript figure.',
            'No model stability repetitions, new untouched-file validation, or actual human annotation was performed in this audit.',
        ],
        'source_bindings': {str(p): sha(p) for p in [Path(__file__), CURRENT/'all_predictions.jsonl', CURRENT/'rule_inputs_v27.jsonl',
            CLASSIFICATION, BASE/'current_llm_inputs.jsonl', BASE/'llm_runs/gpt56-sol-v13-native-1/all_predictions.jsonl',
            BASE/'llm_runs/gpt56-sol-v13-native-1/prediction_seal.json', BASE/'analyze_current_reruns.py', BASE/'正文主分析衔接计划.json',
            BASE/'rerun_comparisons/full_corpus_parallel/parallel_full_corpus.json', CURRENT/'release_manifest.json',
            ac_primary_path, ac_sensitivity_path, ac_plan_path]},
    }
    path = OUT / '敏感性复核.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    markdown = ['# 全量编码与敏感性复核', '', '本次只复核固定4924个政策单元。原文、编码、A/C主分析和冻结归属均未修改。', '',
        '新规则为v28.2，LLM仍为2026年9月27日已封存的gpt-5.6-sol结果；v29未实际重跑。', '',
        '55份政策映射全部精确连接，无未匹配条目。部门单元数为：NMPA 1848、NHSA 2100、NHC 533、GOV 443。', '',
        '|方法|来源组|N|S 阳性/待定%|E|Ec|I|F|', '|---|---|---:|---:|---:|---:|---:|---:|']
    for method in METHODS:
        for group in (*GROUPS, 'ALL'):
            values = primary[method][group]
            cells = ['{:.2f}/{:.2f}'.format(values[d]['positive_proportion'] * 100, values[d]['pending_n'] / values[d]['N'] * 100) for d in DIMS]
            markdown.append('|{}|{}|{}|{}|'.format(method, group, values['S']['N'], '|'.join(cells)))
    markdown += ['', '阳性比例以该来源组全部单元为分母；待定没有删去或填0。旧LLM仍有49条待定，五维均待定。', '',
        f"三部门15项两两方向比较中，机器两条方法{report['between_method_department_directions']['observed_direction_agrees_n']}项方向相同；考虑待定完成界限后，{report['between_method_department_directions']['pending_robust_and_agree_n']}项仍有共同方向。这里没有显著性检验。", '',
        '原A/C主分析来源已检查：1268个唯一单元、29层、580个参数的同时界、120行部门三状态比例和30行总体比例；60项编码员分别的部门差值及30项共同方向比较均已由原冻结文件保存。30项共同稳健方向仍为0项，不能用机器全量方向代换。这里只核查来源，没有重画原图或改写原主统计。', '',
        '|方法|定义敏感性|影响维度|主口径阳性|敏感性阳性|敏感性待定|', '|---|---|---|---:|---:|---:|']
    scenarios_dimension = {'exclude_quality_only': 'S', 'exclude_F_clinical_management_only': 'F',
        'F_access_affordability_only': 'F', 'exclude_F_dimension_information_only': 'F', 'exclude_I_qualification_advantage_only': 'I'}
    for method in METHODS:
        for scenario, dimension in scenarios_dimension.items():
            s = sensitivities[method]['definition_boundaries'][scenario]['ALL'][dimension]
            markdown.append('|{}|{}|{}|{}|{}|{}|'.format(method, scenario, dimension, primary[method]['ALL'][dimension]['positive_n'], s['positive_n'], s['pending_n']))
    markdown += ['', '子类型缺失情况：' + json.dumps(report['missing_subtype_metadata_for_positive_labels'], ensure_ascii=False) + '。', '',
        '|方法|组织口径|部门排序反向数/15|', '|---|---|---:|']
    for method in METHODS:
        for scenario, value in sensitivities[method]['scenario_direction_changes'].items():
            markdown.append('|{}|{}|{}|'.format(method, scenario, value['reversal_n']))
        loo = sensitivities[method]['leave_one_policy_file_summary']
        markdown.append('|{}|逐文件剔除55次（累计反向例次）|{}|'.format(method, loo['reversal_case_n']))
    markdown += ['', '逐文件剔除出现的反向比较：']
    for method in METHODS:
        markdown += ['', '- ' + method + '：' + json.dumps(sensitivities[method]['leave_one_policy_file_summary']['reversed_pairs'], ensure_ascii=False)]
    markdown += ['', '当前结果可描述两条机器测量的部门分布及其对文本权重和边界的敏感程度，不能单独证明真人信度、创新药实际质量或治理协调机制的因果效果。', '', '本次未执行事项：', '',
        '- LLM v29实际全量运行及重复运行稳定性。',
        '- 未参与调整的独立文件样本验证、真人编码实施。',
        '- A/C主分析及其图表数值更新：原冻结分析保持不变；不得称本报告已经更新所有图。', '',
        '完整计数、政策文件/系列等权、剔除联合发文、年度系列仅保留最新成员、55次逐文件剔除、定义边界及数据SHA-256均在同名JSON中。', '',
        '以上均为固定语料描述性核对，不报告“统计显著”“因果差异”或“全部可发表指标通过”。']
    (OUT / '敏感性复核.md').write_text('\n'.join(markdown) + '\n')
    print(json.dumps({'output': str(path), 'sha256': sha(path), 'join_n': len(rows),
        'primary': primary, 'direction_agrees_n': report['between_method_department_directions']['observed_direction_agrees_n'],
        'reversals': {m: sensitivities[m]['leave_one_policy_file_summary']['reversed_pairs'] for m in METHODS}}, ensure_ascii=False))

if __name__ == '__main__':
    main()

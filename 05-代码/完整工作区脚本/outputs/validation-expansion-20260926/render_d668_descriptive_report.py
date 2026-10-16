#!/usr/bin/env python3
"""Render the five predeclared D668 descriptive scenarios, without analysis.

Only the explicitly supplied sensitivity JSON is read. The primary SHA-256 is
supplied independently; no primary archive, original coding or material file is
opened. Self-test creates only explicit synthetic in-memory/temporary fixtures.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import tempfile


SCENARIOS = (
    ('S_without_quality_only', 'S', 'safety_quality_basis', 'S：排除仅质量安全依据'),
    ('I_without_qualification_only', 'I', 'innovation_subtypes', 'I：排除仅创新资格比较优势'),
    ('F_without_management_only', 'F', 'fairness_subtypes', 'F：排除仅临床管理'),
    ('F_without_information_only', 'F', 'fairness_subtypes', 'F：排除仅未细分信息要求'),
    ('F_access_or_affordability_only', 'F', 'fairness_subtypes', 'F：仅保留保障获取或患者可负担'),
)
CODERS = ('A', 'C')
GROUPS = ('NMPA', 'NHSA', 'NHC', 'GOV', 'overall')
N = {'NMPA': 1848, 'NHSA': 2100, 'NHC': 533, 'GOV': 443, 'overall': 4924}
SAMPLE_N = {'NMPA': 436, 'NHSA': 394, 'NHC': 227, 'GOV': 211, 'overall': 1268}
STATES = ('0', '1', 'pending')
COMPLETE = 'computed_descriptive_only'
UNAVAILABLE = 'not_computable_missing_or_invalid_own_metadata'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def is_hash(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def read_json(raw):
    def pairs(items):
        value = {}
        for k, v in items:
            require(k not in value, 'Duplicate JSON key')
            value[k] = v
        return value
    def bad(_):
        raise ValueError('Nonfinite JSON constant')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)
    encoded(value)  # Reject overflowed literals such as 1e999 too.
    require(isinstance(value, dict), 'A complete JSON object is required')
    return value


def literal_int(value, minimum=0):
    require(type(value) is int and value >= minimum, 'Literal nonnegative integer required')


def finite(value, low=None, high=None):
    require(type(value) in (int, float) and math.isfinite(value), 'Finite numeric source value required')
    require((low is None or low <= value) and (high is None or value <= high), 'Source numeric value out of range')


def exact_weight(value):
    # Validate syntax only; never turn the exact source fraction into a float.
    require(isinstance(value, str) and re.fullmatch(r'(?:0|[1-9]\d*)(?:/[1-9]\d*)?', value) is not None,
            'Exact nonnegative integer/fraction source string required')


def validate_result(result, expected_primary_sha256, synthetic_test=False):
    require(is_hash(expected_primary_sha256), 'Independent primary SHA-256 required')
    require(result.get('status') == 'completed_pre_D_judgment_descriptive_sensitivity_addendum',
            'Complete five-scenario sensitivity output required')
    require(result.get('synthetic_test', False) is synthetic_test, 'Synthetic/actual mode mismatch')
    require(result['unique_sample_units'] == 1268 and result['population_size'] == 4924
            and result['A_C_separate'] is True
            and result['no_original_changes_imputation_CI_pvalues_or_inferential_rank'] is True,
            'Fixed unit counts and descriptive-only separate-coder metadata required')
    require(isinstance(result.get('timing'), str) and result['timing'], 'Registration timing missing')
    require(isinstance(result.get('limits'), str) and result['limits'], 'Descriptive limits missing')
    provenance = result['provenance']
    require(provenance['primary_sha256'] == expected_primary_sha256, 'Primary source hash mismatch')
    require(isinstance(provenance['primary_path'], str) and Path(provenance['primary_path']).is_absolute(),
            'Absolute archived primary reference required')
    require(is_hash(provenance['program_sha256']) and isinstance(provenance['created_at'], str)
            and provenance['created_at'], 'Sensitivity program/date provenance missing')
    seal = provenance['addendum_seal_original']
    require(seal['status'] == 'pre_D_judgment_descriptive_sensitivity_addendum_frozen'
            and seal['no_primary_freeze_change'] is True and seal['five_scenarios_fixed'] is True
            and seal['point_estimates_only_no_new_CI_pvalues_or_inferential_rank'] is True,
            'Pre-D-judgment descriptive addendum seal missing')
    for field in ('plan_sha256', 'primary_freeze_sha256', 'ack_A_sha256', 'ack_C_sha256'):
        require(is_hash(seal[field]), 'Addendum source hash missing')
    for field in ('created_at', 'timing', 'plan_path'):
        require(isinstance(seal[field], str) and bool(seal[field]), 'Addendum timing/plan reference missing')
    # The actual supplementary seal writer uses UTF-8, indent=2, and a newline.
    require(sha(encoded(seal)) == provenance['addendum_seal_sha256'], 'Addendum seal encoding/hash mismatch')
    outputs = result['scenarios']
    require(isinstance(outputs, list) and len(outputs) == 5, 'All five scenarios must remain present')
    expected = {name: (dim, field) for name, dim, field, _ in SCENARIOS}
    by_name = {}
    for index, scenario in enumerate(outputs):
        name = scenario['scenario']
        require(name in expected and name not in by_name, 'Unknown or duplicate scenario')
        dim, field = expected[name]
        require(scenario['dimension'] == dim, 'Scenario dimension mismatch')
        status = scenario['status']
        require(status in (COMPLETE, UNAVAILABLE), 'Unrecognized scenario status')
        rows = {}
        if status == COMPLETE:
            require(scenario['no_CI_pvalues_or_inferential_rank'] is True
                    and scenario['other_four_dimensions'] == 'unchanged from original main coding',
                    'Parallel descriptive scenario contract missing')
            require(len(scenario['estimates']) == 10, 'All A/C x five scopes must be present')
            for j, row in enumerate(scenario['estimates']):
                key = (row['coder'], row['department'])
                require(key[0] in CODERS and key[1] in GROUPS and key not in rows, 'Duplicate/invalid scope row')
                require(row['dimension'] == dim and row['fixed_denominator'] == N[key[1]]
                        and row['sample_units'] == SAMPLE_N[key[1]], 'Fixed scope denominator/sample count mismatch')
                for pkey in ('main_proportions', 'scenario_proportions'):
                    require(set(row[pkey]) == set(STATES), 'All three states must be present')
                    for value in row[pkey].values():
                        finite(value, 0, 1)
                for wkey in ('main_weighted_totals_exact', 'scenario_weighted_totals_exact'):
                    require(set(row[wkey]) == set(STATES), 'Exact three-state weighted totals missing')
                    for value in row[wkey].values():
                        exact_weight(value)
                finite(row['positive_change_percentage_points'], -100, 0)
                literal_int(row['changed_sample_count'])
                require(row['changed_sample_count'] <= row['sample_units'], 'Affected count exceeds sample')
                exact_weight(row['changed_weight_exact'])
                ids = row['changed_unit_ids']
                require(isinstance(ids, list) and all(isinstance(v, str) and v for v in ids)
                        and len(ids) == len(set(ids)) == row['changed_sample_count'], 'Affected ID inventory differs')
                require(row['unrecodable_records'] == 0, 'Computed row has missing metadata')
                rows[key] = (row, f'/scenarios/{index}/estimates/{j}')
        else:
            require(scenario['no_imputation'] is True and 'estimates' not in scenario,
                    'Unavailable scenario must not contain invented estimates')
            literal_int(scenario['unrecodable_records'], 1)
            issues = scenario['issues']
            require(isinstance(issues, list) and len(issues) == scenario['unrecodable_records'],
                    'Unavailable scenario issue count mismatch')
            seen = set()
            for issue in issues:
                require(issue['coder'] in CODERS and issue['field'] == field
                        and isinstance(issue['unit_id'], str) and issue['unit_id']
                        and isinstance(issue['issue'], str) and issue['issue'], 'Missing issue metadata/reason')
                key = (issue['unit_id'], issue['coder'], issue['field'])
                require(key not in seen, 'Duplicate unavailable metadata record')
                seen.add(key)
        by_name[name] = (scenario, index, rows)
    require(set(by_name) == set(expected), 'Five scenarios incomplete')
    return by_name


def number(value):
    # A display format, never a recomputed decision or implied precision gain.
    return f'{value:.3g}' if value and abs(value) < .0005 else f'{value:.3f}'


def states(values):
    return ' / '.join(number(values[k] * 100) + '%' for k in STATES)


def cell(value):
    return html.escape(str(value), quote=False).replace('|', '\\|').replace('\r\n', '<br>').replace('\n', '<br>')


def render_result(result, source_sha256, source_reference, expected_primary_sha256, *, synthetic_test=False):
    require(is_hash(source_sha256), 'Sensitivity file SHA-256 required')
    scenarios = validate_result(result, expected_primary_sha256, synthetic_test)
    provenance = result['provenance']
    seal = provenance['addendum_seal_original']
    computable = sum(v[0]['status'] == COMPLETE for v in scenarios.values())
    lines = ['# D668 五项描述性敏感性结果', '']
    if synthetic_test:
        lines += ['**合成软件测试：不是实际研究结果，不得用于政策结论。**', '']
    lines += [f'预定五个情景全部保留：{computable}个可计算，{5 - computable}个因首次元数据缺失或非法而不可计算。'
              '每个情景分别相对原主口径，A/C独立列示，四个来源组和总体均保留；不串行叠加，也不选择变化较小的口径替代主结果。', '',
              f'补充方案登记时间为 `{cell(seal["created_at"])}`：在D668一次抽样之后、D材料阅读授权及判读之前。'
              '这是另存的判读前补充登记，未改变抽样前主冻结。', '',
              '样本为1268个唯一分析单元（R600+D668），不是文件篇数。两份AI判断不是2536个独立单元。'
              '沿用固定R25+D4权重及部门原分母：NMPA=1848、NHSA=2100、NHC=533、GOV=443，总体=4924。', '',
              '**本补充仅描述操作定义变化，不扩展主方案580项推断家族，不新增区间、p值、推断名次或共同稳健方向。**'
              '执行主体为AI，不是真人专家；这些变化不构成新的验证或效度证明。', '',
              f'数值来源：[完整描述性结果JSON](<{source_reference}>)；SHA-256：`{source_sha256}`。',
              f'绑定主归档：[完整主结果JSON](<{provenance["primary_path"]}>)；独立提供并核验的SHA-256：`{expected_primary_sha256}`。',
              f'补充时点封存SHA-256：`{provenance["addendum_seal_sha256"]}`；方案SHA-256：`{seal["plan_sha256"]}`。', '',
              '三态单元格按 **0 / 1 / 待定** 顺序显示。阳性变化直接复制来源中的百分点值；受影响权重保留原整数或分数字符串。'
              '显示小数位不代表更高精度，精确数值及受影响ID以源JSON为准。其他四维沿用主口径，未另算结果。', '']

    def table(headers, rows):
        lines.append('| ' + ' | '.join(headers) + ' |')
        lines.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        for row in rows:
            lines.append('| ' + ' | '.join(map(str, row)) + ' |')
        lines.append('')

    for name, dim, field, title in SCENARIOS:
        scenario, index, estimates = scenarios[name]
        lines += ['## ' + title, '', f'规则键：`{name}`。受影响维度：{dim}；使用各AI自己的首次 `{field}` 字段。', '']
        unavailable = scenario['status'] == UNAVAILABLE
        if unavailable:
            lines += [f'**不可计算。** 源结果报告 {scenario["unrecodable_records"]} 条单位×AI元数据缺失或非法记录，禁止推测补齐。'
                      '来源未提供部门级缺失分配；下列十个覆盖位置保留“不可计算”，不把情景总缺失数误报为各部门缺失数。'
                      '所列固定N和样本n来自已登记设计，不是新估计。', '']
        for coder in CODERS:
            lines += [f'### AI {coder}', '']
            rows = []
            for group in GROUPS:
                label = '总体' if group == 'overall' else group
                if unavailable:
                    rows.append([label, f'{N[group]} / {SAMPLE_N[group]}', '不可计算', '不可计算', '不可计算',
                                 '不可计算', '不可计算', f'`/scenarios/{index}`'])
                else:
                    row, pointer = estimates[coder, group]
                    rows.append([label, f'{row["fixed_denominator"]} / {row["sample_units"]}', states(row['main_proportions']),
                                 states(row['scenario_proportions']), number(row['positive_change_percentage_points']),
                                 row['changed_sample_count'], f'`{row["changed_weight_exact"]}`', f'`{pointer}`'])
            table(['来源组', '固定N / 样本n', '主口径 0 / 1 / 待定', '变体 0 / 1 / 待定',
                   '阳性变化（百分点）', '原始受影响数', '受影响权重（精确）', '源JSON Pointer'], rows)
        if unavailable:
            lines += ['缺失或非法记录与原始原因：', '']
            table(['AI', '分析单元ID', '缺失/非法字段', '来源原始原因', '源JSON Pointer'],
                  [[issue['coder'], cell(issue['unit_id']), cell(issue['field']), cell(issue['issue']), f'`/scenarios/{index}/issues/{j}`']
                   for j, issue in enumerate(scenario['issues'])])
    lines += ['以上只呈现描述性程序已保存的结果。呈现器没有读取主归档、首次判读、材料或机器预测文件，也未重新计算任何统计。'
              '主口径的推断结论仍仅依据原冻结同时界，不能从本表的点变化断言显著差异或稳健排序。', '']
    return '\n'.join(lines)


def write_report(input_path, output_path, expected_primary_sha256, *, synthetic_test=False):
    input_path, output_path = Path(input_path).absolute(), Path(output_path).absolute()
    partial = output_path.with_name(output_path.name + '.partial')
    require(input_path.is_file() and input_path != output_path, 'Distinct existing sensitivity input required')
    require(not output_path.exists() and not partial.exists(), 'Refusing to overwrite output/partial')
    raw = input_path.read_bytes()
    markdown = render_result(read_json(raw), sha(raw), str(input_path), expected_primary_sha256, synthetic_test=synthetic_test)
    require(input_path.read_bytes() == raw, 'Sensitivity input changed during rendering')
    with partial.open('xb') as stream:
        stream.write(markdown.encode('utf-8')); stream.flush(); os.fsync(stream.fileno())
    os.link(partial, output_path); partial.unlink()
    return {'status': 'synthetic_presentation_only' if synthetic_test else 'descriptive_presentation_complete',
            'output': str(output_path), 'source_sha256': sha(raw), 'output_sha256': sha(markdown.encode('utf-8')),
            'primary_sha256': expected_primary_sha256, 'statistics_recomputed': False, 'external_source_files_read': False}


def synthetic_fixture(missing=False):
    """Invented output records only, never a call to any analysis function."""
    seal = {'status': 'pre_D_judgment_descriptive_sensitivity_addendum_frozen', 'created_at': 'SYNTHETIC-TIME',
            'timing': 'SYNTHETIC after draw before D judgments', 'plan_path': '/SYNTHETIC_ONLY/plan.md',
            'plan_sha256': 'a' * 64, 'primary_freeze_sha256': 'b' * 64, 'no_primary_freeze_change': True,
            'five_scenarios_fixed': True, 'point_estimates_only_no_new_CI_pvalues_or_inferential_rank': True,
            'ack_A_sha256': 'c' * 64, 'ack_C_sha256': 'd' * 64}
    result = {'status': 'completed_pre_D_judgment_descriptive_sensitivity_addendum', 'synthetic_test': True,
              'timing': 'SYNTHETIC after draw before D judgments', 'unique_sample_units': 1268,
              'population_size': 4924, 'A_C_separate': True,
              'no_original_changes_imputation_CI_pvalues_or_inferential_rank': True,
              'limits': 'SYNTHETIC descriptive output fixture only', 'scenarios': [],
              'provenance': {'created_at': 'SYNTHETIC-TIME', 'primary_path': '/SYNTHETIC_ONLY/primary.json',
                             'primary_sha256': 'e' * 64, 'program_sha256': 'f' * 64,
                             'addendum_seal_original': seal, 'addendum_seal_sha256': sha(encoded(seal))}}
    for i, (name, dim, field, _) in enumerate(SCENARIOS):
        if missing and i == 2:
            result['scenarios'].append({'scenario': name, 'dimension': dim, 'status': UNAVAILABLE,
                'unrecodable_records': 2, 'issues': [{'unit_id': 'SYNTHETIC-A-UNIT', 'coder': 'A', 'field': field, 'issue': 'Invalid or missing subtype list'},
                                                     {'unit_id': 'SYNTHETIC-C-UNIT', 'coder': 'C', 'field': field, 'issue': 'Subtype/label inconsistency'}], 'no_imputation': True})
            continue
        estimates = []
        for coder in CODERS:
            for group in GROUPS:
                estimates.append({'coder': coder, 'department': group, 'dimension': dim, 'sample_units': SAMPLE_N[group],
                    'fixed_denominator': N[group], 'main_proportions': {'0': .6, '1': .3, 'pending': .1},
                    'scenario_proportions': {'0': .6, '1': .3, 'pending': .1},
                    'main_weighted_totals_exact': {'0': '0', '1': '0', 'pending': '0'},
                    'scenario_weighted_totals_exact': {'0': '0', '1': '0', 'pending': '0'},
                    'positive_change_percentage_points': 0.0, 'changed_sample_count': 0, 'changed_weight_exact': '0',
                    'changed_unit_ids': [], 'unrecodable_records': 0})
        # Nonzero literal fixture values test direct copying, not statistical computation.
        estimates[0].update(positive_change_percentage_points=-.0000004, changed_sample_count=1,
                            changed_weight_exact='123456789/987654321', changed_unit_ids=['SYNTHETIC-CHANGED'])
        result['scenarios'].append({'scenario': name, 'dimension': dim, 'status': COMPLETE, 'estimates': estimates,
            'other_four_dimensions': 'unchanged from original main coding', 'no_CI_pvalues_or_inferential_rank': True})
    return result


def self_test():
    checks = []
    for missing in (False, True):
        fixture = synthetic_fixture(missing)
        saved = copy.deepcopy(fixture)
        primary_hash = fixture['provenance']['primary_sha256']
        markdown = render_result(fixture, sha(encoded(fixture)), '/SYNTHETIC_ONLY/results.json', primary_hash, synthetic_test=True)
        require(fixture == saved, 'Pure renderer mutated its input')
        require('不是文件篇数' in markdown and '580项推断家族' in markdown, 'Required boundary missing')
        require('合成软件测试' in markdown and all(title in markdown for _, _, _, title in SCENARIOS), 'Scenario filtered out')
        for i, scenario in enumerate(fixture['scenarios']):
            if scenario['status'] == COMPLETE:
                for j, row in enumerate(scenario['estimates']):
                    label = '总体' if row['department'] == 'overall' else row['department']
                    expected_row = '| ' + ' | '.join(map(str, (
                        label, f'{row["fixed_denominator"]} / {row["sample_units"]}',
                        states(row['main_proportions']), states(row['scenario_proportions']),
                        number(row['positive_change_percentage_points']), row['changed_sample_count'],
                        f'`{row["changed_weight_exact"]}`', f'`/scenarios/{i}/estimates/{j}`'))) + ' |'
                    require(markdown.splitlines().count(expected_row) == 1, 'Complete source row/pointer differs or is duplicated')
            else:
                require(f'{scenario["unrecodable_records"]} 条' in markdown and markdown.count(f'`/scenarios/{i}`') == 10,
                        'Unavailable scenario coverage/count missing')
                for j, issue in enumerate(scenario['issues']):
                    require(issue['issue'] in markdown and f'`/scenarios/{i}/issues/{j}`' in markdown, 'Missing issue/reason')
        checks.append('all_50_computed_rows' if not missing else '40_computed_plus_10_unavailable_positions_and_all_issues')
    require(number(-.0000004) != '0.000' and '123456789/987654321' in markdown, 'Tiny value/exact weight changed')
    fixture = synthetic_fixture()
    corruptions = [lambda r: r['scenarios'].pop(), lambda r: r['scenarios'][0]['estimates'].pop(),
                   lambda r: r['provenance'].__setitem__('primary_sha256', '0' * 64),
                   lambda r: r['provenance'].__setitem__('addendum_seal_sha256', '0' * 64),
                   lambda r: r['provenance']['addendum_seal_original'].__setitem__('five_scenarios_fixed', False),
                   lambda r: r['scenarios'][0]['estimates'][0]['main_proportions'].pop('pending')]
    for change in corruptions:
        altered = copy.deepcopy(fixture); change(altered)
        try:
            render_result(altered, 'a' * 64, '/SYNTHETIC_ONLY/result.json', 'e' * 64, synthetic_test=True)
        except (ValueError, KeyError):
            pass
        else:
            raise AssertionError('Corrupt/incomplete fixture accepted')
    try:
        render_result(fixture, 'a' * 64, '/SYNTHETIC_ONLY/result.json', 'e' * 64)
    except ValueError:
        pass
    else:
        raise AssertionError('Synthetic input entered actual mode')
    checks.append('missing_state_or_scope_bad_primary_or_seal_hash_and_wrong_mode_rejected')
    with tempfile.TemporaryDirectory(prefix='D668-SYNTHETIC-descriptive-render-') as directory:
        source = Path(directory) / 'SYNTHETIC-result.json'
        output = Path(directory) / 'SYNTHETIC-report.md'
        raw = encoded(fixture); source.write_bytes(raw)
        outcome = write_report(source, output, 'e' * 64, synthetic_test=True)
        require(source.read_bytes() == raw and outcome['source_sha256'] == sha(raw), 'Original source bytes changed')
        try:
            write_report(source, output, 'e' * 64, synthetic_test=True)
        except ValueError:
            pass
        else:
            raise AssertionError('Output overwritten')
    checks += ['source_bytes_unchanged_and_output_exclusive', 'no_analysis_calls_or_external_source_reads']
    return {'status': 'passed_synthetic_descriptive_presentation_QA', 'checks': checks,
            'synthetic_only': True, 'real_D_materials_or_labels_read': False, 'actual_analysis_run': False,
            'actual_report_created': False, 'script_sha256': sha(Path(__file__).read_bytes()),
            'limits': 'Synthetic output-schema/rendering tests only; real sensitivity results were not opened. Exact values remain in the source JSON.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--expected-primary-sha256')
    parser.add_argument('--synthetic-test', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        require(not args.input and not args.output and not args.expected_primary_sha256 and not args.synthetic_test,
                'Self-test cannot receive study paths or hashes')
        print(json.dumps(self_test(), ensure_ascii=False, indent=2))
        return
    require(args.input and args.output and args.expected_primary_sha256, 'Explicit input, new output and expected primary SHA required')
    print(json.dumps(write_report(args.input, args.output, args.expected_primary_sha256,
                                  synthetic_test=args.synthetic_test), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

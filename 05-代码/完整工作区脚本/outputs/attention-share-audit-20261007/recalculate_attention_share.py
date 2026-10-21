"""Independent restoration of the original five-dimension attention-share ratio.

No coding, DOCX, or frozen main statistic is modified. A/C are existing AI
reference labels, not completed human validation. Uncertainty ranges below are
logical pending-completion ranges, not confidence intervals.
"""
from pathlib import Path
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'outputs/autocode-v25-20260927'
CURRENT = ROOT / 'outputs/autocode-v28-review-20261004-111306'
CLASSIFICATION = ROOT / 'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
AC_INPUT = BASE / 'current_1268_references.jsonl'
AC_FROZEN = ROOT / 'outputs/validation-expansion-20260926/D668-原4924范围主统计.json'
ROOT_NEW = ROOT / 'outputs/indicator-alignment-20261007/attention_share_bounds.json'
sys.path.insert(0, str(BASE))
from analyze_current_reruns import load_sealed_predictions, scenario_labels

DIMS = ('S', 'E', 'Ec', 'I', 'F')
GROUPS = ('NMPA', 'NHSA', 'NHC', 'GOV')
PROFESSIONAL = ('NMPA', 'NHSA', 'NHC')
METHODS = ('rules_v28_2', 'llm_gpt56_sol_v13_original', 'A_AI_reference', 'C_AI_reference')
SCENARIOS = ('primary', 'exclude_quality_only', 'exclude_F_clinical_management_only',
    'F_access_affordability_only', 'exclude_F_dimension_information_only',
    'exclude_I_qualification_advantage_only')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def jsonl(path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    result = {r['id']: r for r in rows}
    assert len(result) == len(rows)
    return result

def as_json(value):
    if isinstance(value, Fraction):
        return {'value': float(value), 'exact_fraction': f'{value.numerator}/{value.denominator}'}
    if isinstance(value, dict):
        return {k: as_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_json(v) for v in value]
    return value

def numeric(value):
    return None if value is None else float(value)

def sign(value):
    if value is None:
        return None
    return 1 if value > 0 else -1 if value < 0 else 0

def one_group(rows, method, scenario='primary'):
    selected = [r for r in rows if method in r['records']]
    counts = {d: Counter() for d in DIMS}
    weighted = {d: defaultdict(Fraction) for d in DIMS}
    overlap_raw = Counter()
    overlap_ht = defaultdict(Fraction)
    for row in selected:
        labels = scenario_labels(row['records'][method], scenario)
        assert set(labels) == set(DIMS)
        weight = row['weights'][method]
        hits = sum(labels[d] == 1 for d in DIMS)
        pending = sum(labels[d] == '待定' for d in DIMS)
        for d in DIMS:
            assert labels[d] in (0, 1, '待定')
            counts[d][labels[d]] += 1
            weighted[d][labels[d]] += weight
        events = {
            'at_least_one_known_dimension': hits >= 1,
            'all_five_confirmed_zero': hits == 0 and pending == 0,
            'at_least_two_known_dimensions': hits >= 2,
            'exactly_one_known_dimension': hits == 1,
            'any_pending_dimension': pending >= 1,
            'no_known_dimension_but_pending': hits == 0 and pending >= 1,
            'possibly_at_least_one_dimension': hits + pending >= 1,
            'possibly_at_least_two_dimensions': hits + pending >= 2,
        }
        for name, event in events.items():
            if event:
                overlap_raw[name] += 1
                overlap_ht[name] += weight
    denominator = sum((weighted[d][1] for d in DIMS), Fraction())
    all_pending = sum((weighted[d]['待定'] for d in DIMS), Fraction())
    unit_total = sum((r['weights'][method] for r in selected), Fraction())
    dims = {}
    for d in DIMS:
        hit = weighted[d][1]
        pending = weighted[d]['待定']
        # Extreme completions of each unknown binary dimension, holding the
        # observed labels/weights fixed. These are not sampling intervals.
        low_denom = denominator + all_pending - pending
        high_denom = denominator + pending
        dims[d] = {
            'raw_known_hit_count': counts[d][1],
            'raw_pending_count': counts[d]['待定'],
            'raw_confirmed_zero_count': counts[d][0],
            'weighted_known_hit_count': hit,
            'weighted_pending_count': pending,
            'weighted_confirmed_zero_count': weighted[d][0],
            'attention_share': hit / denominator if denominator else None,
            'pending_completion_descriptive_range': [
                hit / low_denom if low_denom else None,
                (hit + pending) / high_denom if high_denom else None],
            'supplementary_unit_coverage': hit / unit_total if unit_total else None,
        }
    assert sum(counts[d][1] + counts[d][0] + counts[d]['待定'] for d in DIMS) == 5 * len(selected)
    if denominator:
        assert sum((dims[d]['attention_share'] for d in DIMS), Fraction()) == 1
    return {
        'observed_unit_count': len(selected),
        'weighted_unit_count': unit_total,
        'raw_five_dimension_known_hit_sum': sum(counts[d][1] for d in DIMS),
        'weighted_five_dimension_known_hit_sum': denominator,
        'raw_five_dimension_pending_sum': sum(counts[d]['待定'] for d in DIMS),
        'weighted_five_dimension_pending_sum': all_pending,
        'dimensions': dims,
        'overlap': {k: {'raw_unit_count': overlap_raw[k], 'weighted_unit_count': overlap_ht[k]} for k in (
            'at_least_one_known_dimension', 'all_five_confirmed_zero',
            'at_least_two_known_dimensions', 'exactly_one_known_dimension',
            'any_pending_dimension', 'no_known_dimension_but_pending',
            'possibly_at_least_one_dimension', 'possibly_at_least_two_dimensions')},
    }

def summary(rows, method, scenario='primary'):
    return {g: one_group(rows if g == 'ALL' else [r for r in rows if r['metadata']['analysis_group'] == g], method, scenario)
        for g in (*GROUPS, 'ALL')}

def comparisons(data, metric='attention_share'):
    results = []
    for a, b in combinations(PROFESSIONAL, 2):
        for d in DIMS:
            x, y = data[a]['dimensions'][d], data[b]['dimensions'][d]
            delta = x[metric] - y[metric] if x[metric] is not None and y[metric] is not None else None
            low = x['pending_completion_descriptive_range'][0]
            high = x['pending_completion_descriptive_range'][1]
            otherlow = y['pending_completion_descriptive_range'][0]
            otherhigh = y['pending_completion_descriptive_range'][1]
            pending_bounds = [low - otherhigh, high - otherlow] if None not in (low, high, otherlow, otherhigh) else [None, None]
            results.append({'pair': [a, b], 'dimension': d, 'observed_difference': delta,
                'observed_direction': sign(delta),
                'pending_completion_descriptive_difference_range': pending_bounds,
                'direction_for_all_pending_completions': (1 if pending_bounds[0] > 0 else -1 if pending_bounds[1] < 0 else 0 if pending_bounds == [0, 0] else None) if pending_bounds[0] is not None else None})
    return results

def direction_changes(primary, current):
    baseline = {(tuple(x['pair']), x['dimension']): x for x in comparisons(primary)}
    now = comparisons(current)
    for x in now:
        b = baseline[(tuple(x['pair']), x['dimension'])]
        x['baseline_direction'] = b['observed_direction']
        x['reversal'] = x['observed_direction'] is not None and b['observed_direction'] is not None and x['observed_direction'] * b['observed_direction'] == -1
        x['direction_changed'] = x['observed_direction'] != b['observed_direction']
    return {'comparisons': now, 'reversal_count': sum(x['reversal'] for x in now),
        'changed_direction_count': sum(x['direction_changed'] for x in now)}

def dominant(data):
    result = {}
    for g in (*GROUPS, 'ALL'):
        dims = data[g]['dimensions']
        defined = {d: dims[d]['attention_share'] for d in DIMS if dims[d]['attention_share'] is not None}
        result[g] = [d for d, value in defined.items() if value == max(defined.values())] if defined else []
    return result

def equalized(rows, method, field):
    buckets = defaultdict(list)
    for r in rows:
        if method in r['records']:
            buckets[r['metadata'][field]].append(r)
    summaries = {key: one_group(values, method) for key, values in buckets.items()}
    group_of = {key: values[0]['metadata']['analysis_group'] for key, values in buckets.items()}
    assert all(len({r['metadata']['analysis_group'] for r in values}) == 1 for values in buckets.values())
    result = {}
    for g in (*GROUPS, 'ALL'):
        keys = [key for key in buckets if g == 'ALL' or group_of[key] == g]
        active = [key for key in keys if summaries[key]['weighted_five_dimension_known_hit_sum'] > 0]
        excluded = [key for key in keys if key not in active]
        pending_only = [key for key in excluded if summaries[key]['weighted_five_dimension_pending_sum'] > 0]
        dims = {}
        for d in DIMS:
            share = sum((summaries[k]['dimensions'][d]['attention_share'] for k in active), Fraction()) / len(active) if active else None
            ranges = None if pending_only or not active else [sum((summaries[k]['dimensions'][d]['pending_completion_descriptive_range'][i] for k in active), Fraction()) / len(active) for i in (0, 1)]
            dims[d] = {'attention_share': share,
                'pending_completion_descriptive_range': ranges or [None, None],
                'supplementary_unit_coverage': None}
        result[g] = {'available_cluster_count': len(keys), 'known_hit_active_cluster_count': len(active),
            'excluded_zero_known_hit_clusters': excluded, 'excluded_pending_only_clusters': pending_only,
            'dimensions': dims}
        if active:
            assert sum((dims[d]['attention_share'] for d in DIMS), Fraction()) == 1
    return result

def main():
    _, llm, llm_inputs, seal = load_sealed_predictions()
    predictions = jsonl(CURRENT / 'all_predictions.jsonl')
    inputs = jsonl(CURRENT / 'rule_inputs_v27.jsonl')
    references = jsonl(AC_INPUT)
    manifest = json.loads((CURRENT / 'release_manifest.json').read_text())
    for field, name in [('output_bindings', 'all_predictions.jsonl'), ('code_and_input_bindings', 'rule_inputs_v27.jsonl')]:
        path = CURRENT / name
        assert manifest[field][name if field == 'output_bindings' else str(path)] == sha(path)
    metadata = json.loads(CLASSIFICATION.read_text())['rows']
    classification = {Path(r['original_file']).stem: r for r in metadata}
    assert len(classification) == 55
    assert set(predictions) == set(inputs) == set(llm) == set(llm_inputs)
    assert len(predictions) == 4924 and len(references) == 1268
    assert set(references) <= set(inputs)
    rows, unmatched, strata = [], [], {}
    for rid, item in inputs.items():
        original_stem = item['input']['original_file_stem']
        if original_stem not in classification:
            unmatched.append({'id': rid, 'original_file_stem': original_stem})
            continue
        assert item['input']['unit_text'] == llm_inputs[rid]['text']
        rule = predictions[rid]['prediction']
        assert rule['version'] == 'v28.2-five-dimension-discrepancy-audit-20261004'
        assert rule['unit_text_sha256'] == hashlib.sha256(item['input']['unit_text'].encode()).hexdigest()
        records = {METHODS[0]: rule, METHODS[1]: llm[rid]}
        weights = {METHODS[0]: Fraction(1), METHODS[1]: Fraction(1)}
        if rid in references:
            ref = references[rid]
            sampling = ref['historical_sampling']
            prior = strata.setdefault(sampling['stratum'], (sampling['N_h'], sampling['n_h']))
            assert prior == (sampling['N_h'], sampling['n_h'])
            for coder in ('A', 'C'):
                method = f'{coder}_AI_reference'
                records[method] = ref['original_references'][coder]
                weights[method] = Fraction(sampling['N_h'], sampling['n_h'])
        rows.append({'id': rid, 'metadata': {**classification[original_stem], 'policy_file_stem': original_stem},
            'records': records, 'weights': weights})
    assert not unmatched
    observed_strata = Counter(references[rid]['historical_sampling']['stratum'] for rid in references)
    assert all(observed_strata[s] == n for s, (_, n) in strata.items())
    file_inventory = {}
    for method in METHODS:
        observed_files = {r['metadata']['policy_file_stem'] for r in rows if method in r['records']}
        file_inventory[method] = {'population_file_count': len(classification),
            'observed_file_count': len(observed_files),
            'population_files_without_observed_method_units': sorted(set(classification) - observed_files),
            'by_group': {g: {'population_file_count': sum(m['analysis_group'] == g for m in classification.values()),
                'observed_file_count': sum(classification[f]['analysis_group'] == g for f in observed_files),
                'population_files_without_observed_method_units': sorted(f for f, meta in classification.items() if meta['analysis_group'] == g and f not in observed_files)} for g in GROUPS}}
    primary = {m: summary(rows, m) for m in METHODS}
    assert [primary[METHODS[0]]['ALL']['dimensions'][d]['raw_known_hit_count'] for d in DIMS] == [420, 320, 645, 138, 313]
    assert [primary[METHODS[1]]['ALL']['dimensions'][d]['raw_known_hit_count'] for d in DIMS] == [560, 406, 827, 287, 694]
    for method in METHODS:
        assert primary[method]['ALL']['weighted_unit_count'] == 4924
    checks = []
    frozen = json.loads(AC_FROZEN.read_text())['statistics']
    for row in frozen['department_status_estimates']:
        method = f"{row['coder']}_AI_reference"
        name = {'1': 'weighted_known_hit_count', '0': 'weighted_confirmed_zero_count', 'pending': 'weighted_pending_count'}[row['measure']]
        independent = primary[method][row['department']]['dimensions'][row['dimension']][name]
        error = abs(float(independent) - row['ht_total'])
        assert error < 1e-9, (method, row, independent)
        checks.append({'source': 'frozen_AC_HT_counts', 'coder': row['coder'], 'group': row['department'], 'dimension': row['dimension'], 'measure': row['measure'], 'absolute_error': error})
    if ROOT_NEW.exists():
        for row in json.loads(ROOT_NEW.read_text())['rows']:
            independent = primary[f"{row['coder']}_AI_reference"][row['group']]['dimensions'][row['dimension']]
            for k1, k2 in [('weighted_coded_count', 'weighted_known_hit_count'), ('weighted_pending_count', 'weighted_pending_count'), ('attention_share', 'attention_share')]:
                error = abs(float(independent[k2]) - row[k1])
                assert error < 1e-9
                checks.append({'source': 'independent_parent_attention_share', 'coder': row['coder'], 'group': row['group'], 'dimension': row['dimension'], 'measure': k2, 'absolute_error': error})
            for a, b in zip(independent['pending_completion_descriptive_range'], row['pending_completion_descriptive_range']):
                assert abs(float(a) - b) < 1e-9
    denominator_drift = {}
    for method in METHODS:
        coverage = comparisons(primary[method], 'supplementary_unit_coverage')
        attention = comparisons(primary[method])
        changes = [{**a, 'coverage_direction': c['observed_direction'], 'coverage_difference': c['observed_difference']}
            for a, c in zip(attention, coverage) if a['observed_direction'] != c['observed_direction']]
        denominator_drift[method] = changes
    agreement = []
    rules, llmcomp = comparisons(primary[METHODS[0]]), comparisons(primary[METHODS[1]])
    for rule, old in zip(rules, llmcomp):
        agreement.append({'pair': rule['pair'], 'dimension': rule['dimension'],
            'rules': rule, 'old_LLM': old, 'same_observed_direction': rule['observed_direction'] == old['observed_direction'],
            'same_direction_for_all_pending_completions': rule['direction_for_all_pending_completions'] is not None and rule['direction_for_all_pending_completions'] == old['direction_for_all_pending_completions']})
    # Save primary output first. All completion bounds retain the fixed observed
    # material/design weights; no fixed-N confidence bounds are reused.
    report = {'estimand': '每维已判定命中句次 / 同一部门五维已判定命中句次合计；A/C各自以原N_h/n_h权重HT计数作比',
        'not_the_estimand': ['每维命中单元数/该部门全部单元数', '去重后至少涉及一维单元数作分母', '实际评审权重', 'A/C平均标签'],
        'provenance': {'A_C': '既有AI代理参考标注；尚非独立真人专家验证', 'LLM': '2026-09-27 gpt-5.6-sol v1.3已封存结果；未v29重跑', 'rules': 'v28.2完整4924条'},
        'primary': primary, 'denominator_drift_direction_changes': denominator_drift,
        'machine_attention_direction_agreement': agreement,
        'machine_attention_same_direction_count': sum(x['same_observed_direction'] for x in agreement),
        'machine_attention_same_direction_all_pending_completions_count': sum(x['same_direction_for_all_pending_completions'] for x in agreement),
        'independent_checks': checks, 'unmatched_join_rows': unmatched,
        'sampling_strata_count': len(strata),
        'method_file_inventory': file_inventory,
        'range_interpretation': '待定补全范围仅针对既定文本/既定HT权重逐维未知0/1补全的描述性界；不是抽样置信区间，不控制多重比较。没有直接移用旧固定N区间。',
        'source_sha256': {str(p): sha(p) for p in (CURRENT/'all_predictions.jsonl', CURRENT/'rule_inputs_v27.jsonl', CURRENT/'release_manifest.json', CLASSIFICATION, AC_INPUT, AC_FROZEN, BASE/'llm_runs/gpt56-sol-v13-native-1/all_predictions.jsonl', CURRENT/'protocol-v1.3.md',
            Path('/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914/00-论文最新稿/0925论文修订稿6-创新药评价的注意力配置差异-清洁版.docx'),
            ROOT/'0813论文终稿-制度视角下创新药多主体评价的认知分歧与协调路径-科学决策版式-已核查带批注.docx',
            Path('/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914/01-论文历史版本/稿6构建脚本/numbers_v3.py'), Path(__file__))},
        'sensitivity_status': 'pending_new_denominator_recalculation',
        'definition_evidence': [
            {'source': '/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914/00-论文最新稿/0925论文修订稿6-创新药评价的注意力配置差异-清洁版.docx',
                'paragraph_index_zero_based': 46,
                'quote': '同一句子可同时命中多个维度，命中同一维度的多个关键词仅计1次',
                'denominator_quote': '以某维度命中句次占该部门五维度命中句次合计的比重作为注意力占比'},
            {'source': '/PROJECT_ROOT/0813论文终稿-制度视角下创新药多主体评价的认知分歧与协调路径-科学决策版式-已核查带批注.docx',
                'paragraph_index_zero_based': 60,
                'denominator_quote': '各维度句次占该部门五维度句次合计的百分比'},
            {'source': '/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914/01-论文历史版本/稿6构建脚本/numbers_v3.py',
                'line': 20,
                'code': '100*c[d]/sum(c.values())'},
            {'source': str(CURRENT / 'protocol-v1.3.md'), 'line': 11,
                'quote': '每个分析单元分别填写S、E、Ec、I、F的0或1，可同时命中多个维度，也可全为0。'}]}
    output = OUT / '注意力占比-原定义重算.json'
    output.write_text(json.dumps(as_json(report), ensure_ascii=False, indent=2))
    latest = {}
    for meta in metadata:
        if meta['annual_series']:
            latest[meta['policy_series']] = max(latest.get(meta['policy_series'], -1), meta['year_in_filename'])
    latest_rows = [r for r in rows if not r['metadata']['annual_series'] or r['metadata']['year_in_filename'] == latest[r['metadata']['policy_series']]]
    no_joint = [r for r in rows if not r['metadata']['joint_publication']]
    files = sorted({r['metadata']['policy_file_stem'] for r in rows})
    sensitivities = {}
    for method in METHODS:
        value = {'definition_boundaries': {s: summary(rows, method, s) for s in SCENARIOS if s != 'primary'},
            'policy_file_equal_weight': equalized(rows, method, 'policy_file_stem'),
            'policy_series_equal_weight': equalized(rows, method, 'policy_series'),
            'latest_member_of_annual_series_only': summary(latest_rows, method),
            'exclude_all_joint_publications': summary(no_joint, method)}
        value['scenario_direction_changes'] = {name: direction_changes(primary[method], res) for name, res in value.items() if name != 'definition_boundaries'}
        value['definition_direction_changes'] = {name: direction_changes(primary[method], res) for name, res in value['definition_boundaries'].items()}
        value['primary_dominant_dimensions'] = dominant(primary[method])
        value['sensitivity_dominant_dimensions'] = {name: dominant(res) for name, res in value.items() if name in ('policy_file_equal_weight', 'policy_series_equal_weight', 'latest_member_of_annual_series_only', 'exclude_all_joint_publications')}
        loo = []
        for file in files:
            discarded = [r for r in rows if r['metadata']['policy_file_stem'] == file]
            retained = [r for r in rows if r['metadata']['policy_file_stem'] != file]
            now = summary(retained, method)
            changes = direction_changes(primary[method], now)
            loo.append({'discarded_file': file, 'discarded_population_unit_count': len(discarded),
                'discarded_observed_method_unit_count': sum(method in r['records'] for r in discarded),
                'discarded_group': discarded[0]['metadata']['analysis_group'],
                'distribution': now, 'direction_changes': changes, 'dominant_dimensions': dominant(now)})
        value['leave_one_policy_file_out'] = loo
        value['leave_one_policy_file_summary'] = {'file_count': len(loo),
            'reversal_case_count': sum(x['direction_changes']['reversal_count'] for x in loo),
            'files_with_reversals': [x['discarded_file'] for x in loo if x['direction_changes']['reversal_count']],
            'reversed_pairs': [{**c, 'discarded_file': x['discarded_file']} for x in loo for c in x['direction_changes']['comparisons'] if c['reversal']],
            'attention_share_ranges': {g: {d: {'minimum': min(x['distribution'][g]['dimensions'][d]['attention_share'] for x in loo if x['distribution'][g]['dimensions'][d]['attention_share'] is not None),
                'maximum': max(x['distribution'][g]['dimensions'][d]['attention_share'] for x in loo if x['distribution'][g]['dimensions'][d]['attention_share'] is not None)} for d in DIMS} for g in (*GROUPS, 'ALL')},
            'dominant_changes': [{'discarded_file': x['discarded_file'], 'group': g, 'primary': value['primary_dominant_dimensions'][g], 'after_exclusion': x['dominant_dimensions'][g]} for x in loo for g in GROUPS if x['dominant_dimensions'][g] != value['primary_dominant_dimensions'][g]]}
        sensitivities[method] = value
    report['sensitivity_status'] = 'completed_for_four_methods_using_original_ratio_denominator'
    report['sensitivities'] = sensitivities
    report['sensitivity_interpretation'] = '文件等权复现原代码：先算文件内5维构成，再对至少有一个已知维度命中的文件等权平均；零命中文件列明，若有待定后可能进入均值的文件，不声称已给出无条件待定补全界。系列等权同法为补充。A/C各文件/系列计数使用原设计权重，仅作既有样本的描述性敏感性，没有另算这些域的抽样区间。逐文件剔除、定义边界、年度系列和联合发文排除均重新计算分子与5维合计。'
    output.write_text(json.dumps(as_json(report), ensure_ascii=False, indent=2))
    lines = ['# 原注意力占比定义独立重算', '', report['estimand'], '',
        'A/C仍为既有AI参考标注，不是已完成真人验证；LLM仍为2026-09-27封存的gpt-5.6-sol结果。编码、论文和冻结主统计未改动。', '',
        '待定补全界为既定文本/权重下的描述性逻辑范围，不是置信区间。旧固定N同时区间未移用。', '',
        '|方法|部门|观测单元数|加权单元总数|S句次|E句次|Ec句次|I句次|F句次|五维合计|S%|E%|Ec%|I%|F%|',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for m in METHODS:
        for g in (*GROUPS, 'ALL'):
            v = primary[m][g]
            lines.append('|'+ '|'.join([m, g, str(v['observed_unit_count']), f"{float(v['weighted_unit_count']):.4f}"] + [f"{float(v['dimensions'][d]['weighted_known_hit_count']):.6f}" for d in DIMS]+[f"{float(v['weighted_five_dimension_known_hit_sum']):.6f}"]+[f"{float(v['dimensions'][d]['attention_share'])*100:.4f}" for d in DIMS])+'|')
    lines += ['', '## 覆盖与重叠补充', '', '以下计数按单元去重。A/C同时列原始样本数和HT加权数；待定单元不能直接算成无维。至少1维和多维只表示已知命中。', '',
        '|方法|部门|至少1维 原始/HT|全5维确定为0 原始/HT|多维 原始/HT|有待定 原始/HT|无已知维但待定 原始/HT|', '|---|---|---:|---:|---:|---:|---:|']
    for m in METHODS:
        for g in (*GROUPS, 'ALL'):
            o = primary[m][g]['overlap']
            cells = [f"{o[k]['raw_unit_count']}/{float(o[k]['weighted_unit_count']):.4f}" for k in ('at_least_one_known_dimension', 'all_five_confirmed_zero', 'at_least_two_known_dimensions', 'any_pending_dimension', 'no_known_dimension_but_pending')]
            lines.append('|'+ '|'.join([m,g]+cells)+'|')
    lines += ['', '## 分母漂移与方法比较', '', f"两机器三专业部门15项方向比较：{report['machine_attention_same_direction_count']}/15点估计同向，{report['machine_attention_same_direction_all_pending_completions_count']}/15在逐维待定全部补全时仍同向。这不是统计显著性。", '']
    for m, changes in denominator_drift.items():
        lines.append(f'- {m}：从单元覆盖率改回注意力占比有{len(changes)}项相对方向变化。'+ '; '.join(f"{x['pair'][0]}–{x['pair'][1]} {x['dimension']}，覆盖差{float(x['coverage_difference'])*100:.4f}个百分点→构成差{float(x['observed_difference'])*100:.4f}个百分点" for x in changes))
    for m in METHODS:
        v = sensitivities[m]
        lines += ['', f'## {m}敏感性', '', f"主分布最大维度：{v['primary_dominant_dimensions']}。55次逐文件剔除产生{v['leave_one_policy_file_summary']['reversal_case_count']}个跨部门方向反转（某文件×某比较计1次），涉及{len(v['leave_one_policy_file_summary']['files_with_reversals'])}个被剔文件。", '']
        for k, x in v['scenario_direction_changes'].items():
            lines.append(f"- {k}：{x['reversal_count']}项反转，{x['changed_direction_count']}项方向变化；最大维度{v['sensitivity_dominant_dimensions'][k]}。")
        for k, x in v['definition_direction_changes'].items():
            lines.append(f"- {k}：{x['reversal_count']}项反转，{x['changed_direction_count']}项方向变化。")
        for k in ('policy_file_equal_weight', 'policy_series_equal_weight'):
            for g in GROUPS:
                e = v[k][g]
                lines.append(f"- {k}/{g}：可得{e['available_cluster_count']}组，已知命中入均值{e['known_hit_active_cluster_count']}组；排除零命中{e['excluded_zero_known_hit_clusters']}；其中仅待定{e['excluded_pending_only_clusters']}。")
    lines += ['', '## 验证与限制', '', f'共{len(checks)}项原始HT计数/根代理独立新比率校验通过；冻结映射join未匹配0条。完整精确分数、逐维待定、各文件剔除与来源SHA256见同名JSON。', '', report['sensitivity_interpretation'], '',
        '该重算恢复原构念分母，不证明独立真人信度、抽样显著性或投稿合格。原固定N分析的共同稳健方向结果不能移用于新的构成比。']
    for m, inv in file_inventory.items():
        lines += ['', f"- {m}：总体55文件，可得该方法观测单元的文件{inv['observed_file_count']}；无观测单元的文件{inv['population_files_without_observed_method_units']}。"]
    lines += ['', '## 原定义直接证据', '',
        '稿6第46段：同一句可命中多维；“以某维度命中句次占该部门五维度命中句次合计的比重作为注意力占比”。更早0813稿第60段同样使用“五维度句次合计”的分母。稿6构建代码numbers_v3.py第20行使用100*c[d]/sum(c.values())；文件等权第29–33行先算文件内构成再等权平均。v1.3手册第11行仍允许多标签，没有将原注意力配置理论变量改为全部文本单元分母的依据。',
        '固定N覆盖率可以保留为补充，但其名称、分母、区间及部门比较不得冒用为原注意力构成占比或实际评审权重。']
    (OUT / '注意力占比-原定义重算.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'output': str(output), 'checks': len(checks), 'machine_same_direction': report['machine_attention_same_direction_count'], 'pending_robust_same_direction': report['machine_attention_same_direction_all_pending_completions_count'], 'denominator_drift_change_counts': {m: len(v) for m,v in denominator_drift.items()}, 'sensitivity_status': report['sensitivity_status']}, ensure_ascii=False))

if __name__ == '__main__':
    main()

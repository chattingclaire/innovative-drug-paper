#!/usr/bin/env python3
"""Presentation only: one explicit bridge-result JSON -> exclusive Chinese Markdown.

Never imports the statistical program, calls analyze, reads source directories,
or opens referenced files. Exact values remain in the linked source archive.
The expected freeze hash is mandatory and is never inferred from the result.
"""
from __future__ import annotations
import argparse
import hashlib
from itertools import combinations, product
import json
import math
import os
from pathlib import Path
import re

CODERS = ('A', 'C')
DIMS = ('S', 'E', 'Ec', 'I', 'F')
GROUPS = ('NMPA', 'NHSA', 'NHC', 'GOV')
GROUP_NAMES = {'NMPA': '国家药监局', 'NHSA': '国家医保局', 'NHC': '国家卫生健康委', 'GOV': '国务院'}
GROUP_N = {'NMPA': 1848, 'NHSA': 2100, 'NHC': 533, 'GOV': 443}
STATES = ('0', '1', 'pending')
POTENTIAL = 'positive_or_pending'
COUNTS = {'department_status_estimates': 120, 'department_potential_positive_estimates': 40,
          'overall_status_estimates': 30, 'overall_potential_positive_estimates': 10,
          'coder_pairwise_differences': 60, 'common_robust_directions': 30,
          'stratum_coder_dimension_counts': 290}
DESIGN_SIGNATURE = 'a49f6635df0d53db26d4b700b95e4cd380e022354ecea10c7dbff1daf8d4f62d'
DIRECTIONS = {'left_greater': '左方较高', 'left_less': '右方较高', 'not_orderable': '不可排序'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def original_encoding(value):
    # This is the actual frozen manifest writer's byte serialization contract.
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def digest(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def read_json(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            require(k not in out, 'Duplicate JSON key')
            out[k] = v
        return out
    def bad(_):
        raise ValueError('Nonfinite JSON constant')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)
    canonical(value)  # Also reject overflowed numeric literals such as 1e999.
    require(isinstance(value, dict), 'Result must be a JSON object')
    return value


def finite(value, low=None, high=None):
    require(type(value) in (int, float) and math.isfinite(value), 'Finite numeric result required')
    require((low is None or value >= low) and (high is None or value <= high), 'Numeric result out of range')


def check_interval(ci, denominator=None, difference=False):
    require(isinstance(ci, dict), 'Confidence interval missing')
    finite(ci['lower'], -1 if difference else 0, 1)
    finite(ci['upper'], -1 if difference else 0, 1)
    require(ci['lower'] <= ci['upper'], 'Reversed confidence interval')
    require(ci['nominal_coverage'] == .95, 'Unexpected nominal coverage')
    if denominator is not None:
        require(ci['fixed_denominator'] == denominator, 'Interval denominator differs')
    if difference:
        require(ci['direction'] in DIRECTIONS and type(ci['excludes_zero']) is bool,
                'Original difference decision missing')


def index_table(rows, keys, expected, label):
    indexed = {}
    for i, row in enumerate(rows):
        require(isinstance(row, dict), f'{label}: row object required')
        key = tuple(row[k] for k in keys)
        require(key not in indexed, f'{label}: duplicate row')
        indexed[key] = (row, f'/statistics/{label}/{i}')
    require(set(indexed) == expected, f'{label}: missing/extra row keys')
    return indexed


def source_pairs(statistics):
    """Retain the left/right orientation in the source, including test fixtures."""
    pairs = tuple((r['left_department'], r['right_department'])
                  for r in statistics['coder_pairwise_differences'] if r['coder'] == 'A' and r['dimension'] == 'S')
    require(len(pairs) == 6 and {frozenset(p) for p in pairs} == {frozenset(p) for p in combinations(GROUPS, 2)},
            'All six unordered department pairs required')
    return pairs


def validate_result(result, expected_freeze_sha256, synthetic_test=False):
    """Verify the self-contained bridge archive without opening linked sources."""
    require(digest(expected_freeze_sha256), 'Expected freeze SHA-256 is required')
    require(result.get('status') == 'completed_supplementary_AI_content_analysis_not_human_validation'
            and result.get('phase') == 'R600_plus_D668', 'Completed D668 bridge result required')
    require(result.get('synthetic_test', False) is synthetic_test, 'Synthetic result flag mismatch')
    st, ar = result['statistics'], result['archive']
    meta = st['metadata']
    expected_kind = 'SYNTHETIC_SOFTWARE_TEST_ONLY' if synthetic_test else 'OBSERVED_CODING_DESIGN_ANALYSIS'
    require(meta['analysis_kind'] == expected_kind, 'Analysis kind differs from rendering mode')
    require(meta['schema_version'] == 'd668-v1' and meta['method_version'] == 'D668-HT-exact-hypergeometric-bonferroni-v1',
            'Unrecognized frozen statistics schema/method')
    require(meta['alpha'] == .05 and meta['family_size'] == 580, 'Frozen alpha/family mismatch')
    require(meta['unique_sample_units'] == 1268 and meta['ai_codings_per_unit'] == 2
            and meta['ai_codings_are_not_independent_sample_units'] is True,
            '1268 unique units / two separate AI codings required')
    require(meta['output_row_counts'] == COUNTS, 'Output row count declaration mismatch')
    for table, n in COUNTS.items():
        require(isinstance(st[table], list) and len(st[table]) == n, f'{table}: incomplete output')
    design = st['design']
    sorted_design = {**design, 'strata': sorted(design['strata'], key=lambda h: h['stratum_id'])}
    require(sha(canonical(sorted_design)) == DESIGN_SIGNATURE, 'Frozen 29-stratum design differs')
    require(sha(canonical(design)) == meta['design_canonical_sha256'], 'Design hash mismatch')
    payload = ar['normalized_analysis_payload']
    require(payload['design'] == design and sha(canonical(payload)) == meta['input_canonical_sha256'],
            'Normalized analysis input hash mismatch')
    require(payload['data_kind'] == ('synthetic_test' if synthetic_test else 'observed_coding'), 'Input kind mismatch')
    require(len(payload['units']) == 1268 and len({r['unit_id'] for r in payload['units']}) == 1268,
            'Unique unit inventory mismatch')
    join = ar['ID_join_provenance']
    require(len(join) == 1268 and {r['review_id'] for r in join} == {r['unit_id'] for r in payload['units']},
            'Global ID provenance mismatch')
    require(sum(r['phase'] == 'R' for r in join) == 600 and sum(r['phase'] == 'D' for r in join) == 668,
            'R600/D668 provenance count mismatch')
    require(ar['no_machine_predictions_or_consensus_used'] is True, 'Original separate-coding declaration required')
    freeze, seal, rsource = ar['freeze_original'], ar['release_seal_original'], ar['R_source_manifest_original']
    require(sha(original_encoding(freeze)) == expected_freeze_sha256, 'Frozen manifest original-byte encoding/hash mismatch')
    require(freeze['status'] == 'frozen_for_D668_supplementary_AI_content_analysis' and freeze['phase'] == 'D668',
            'D668 freeze metadata missing')
    require(seal['freeze_manifest_sha256'] == expected_freeze_sha256, 'Release seal/freeze hash mismatch')
    require(seal['phase'] == 'D668' and seal['n'] == 668 and seal['N_star'] == 3393
            and seal['release_status'] == 'ready_for_blind_review', 'Released sample metadata mismatch')
    tracked = ar['input_snapshot_hashes']
    require(isinstance(tracked, dict) and all(Path(p).is_absolute() and digest(h) for p, h in tracked.items()),
            'Invalid input hash inventory')
    require(expected_freeze_sha256 in tracked.values(), 'Expected freeze absent from tracked input hashes')
    files = freeze['files']
    required_files = {'analysis_bridge', 'statistics', 'admin_receiver', 'r600_source_manifest',
                      'protocol', 'protocol_clarifications', 'v600_sampling_manifest'}
    require(isinstance(files, dict) and len(files) == 20 and required_files <= set(files), 'Frozen 20-file inventory incomplete')
    for entry in files.values():
        require(digest(entry['sha256']) and tracked.get(entry['path']) == entry['sha256'], 'Frozen input hash binding mismatch')
    require(seal['input_hashes'] == {k: v['sha256'] for k, v in files.items()}, 'Seal input hash inventory mismatch')
    runtime = ar['verified_runtime']
    require(all(runtime[k] == freeze['runtime'][k] for k in ('python_version', 'numpy', 'scipy')), 'Archived runtime/freeze mismatch')
    require(rsource['n'] == 600 and rsource['N_R'] == 1531 and rsource['protocol_version'] == freeze['protocol_version'],
            'R source population/manual mismatch')
    require(sha(original_encoding(rsource)) == files['r600_source_manifest']['sha256'], 'R source manifest hash mismatch')
    require(rsource['source_mapping']['sha256'] == files['v600_sampling_manifest']['sha256'], 'R mapping/frozen input mismatch')
    for key in ('source_original_freeze', 'source_release_seal', 'source_mapping'):
        entry = rsource[key]
        require(tracked.get(entry['path']) == entry['sha256'], 'R original source hash binding mismatch')
    require(sha(original_encoding(ar['R_mapping_original'])) == rsource['source_mapping']['sha256'], 'R mapping archive hash mismatch')
    dmap_digest = seal['output_files']['抽样清单-研究者.json']
    require(sha(original_encoding(ar['D_mapping_original'])) == dmap_digest, 'D mapping archive hash mismatch')
    for phase, n in (('R', 600), ('D', 668)):
        require(len(ar[f'{phase}_mapping_original']['rows']) == n, 'Original mapping row count mismatch')
    manifests, originals = ar['original_submission_manifest'], ar['raw_coder_submissions']
    require(set(manifests) == set(originals) == {'R', 'D'}, 'R/D source manifests required')
    for phase, batches in (('R', 24), ('D', 27)):
        expected = {f'agent-{c}/结果-{b:02d}.json' for c in CODERS for b in range(1, batches + 1)}
        require(set(manifests[phase]) == set(originals[phase]) == expected, '48 R / 54 D original file inventories required')
        if phase == 'R':
            require(set(rsource['raw_submissions']) == expected, 'R first-submission inventory mismatch')
        mapping_ids = {r['id'] for r in ar[f'{phase}_mapping_original']['rows']}
        require(len(mapping_ids) == (600 if phase == 'R' else 668), 'Original blind mapping IDs not unique')
        for coder in CODERS:
            ids = [r['id'] for name, doc in originals[phase].items() if name.startswith(f'agent-{coder}/') for r in doc['rows']]
            require(len(ids) == len(set(ids)) and set(ids) == mapping_ids, 'Original per-coder row ID inventory incomplete')
        for relative in expected:
            entry = manifests[phase][relative]
            require(digest(entry['sha256']) and type(entry['byte_count']) is int and entry['byte_count'] > 0,
                    'Original source digest/byte count invalid')
            require(originals[phase][relative]['coder'] == relative.split('/')[0][-1], 'Original source coder mismatch')
            if phase == 'R':
                for kind in ('first_receipt', 'original'):
                    original = rsource['raw_submissions'][relative][kind]
                    require(original['sha256'] == entry['sha256'] and tracked.get(original['path']) == entry['sha256'],
                            'R original/first-receipt hash binding mismatch')
            else:
                original_path = str(Path(freeze['release_directory']) / relative)
                require(tracked.get(original_path) == entry['sha256'], 'D original source hash binding mismatch')

    indexes = {}
    for name, departments, measures in (
            ('department_status_estimates', True, STATES),
            ('department_potential_positive_estimates', True, (POTENTIAL,)),
            ('overall_status_estimates', False, STATES),
            ('overall_potential_positive_estimates', False, (POTENTIAL,))):
        keys = ('coder', 'dimension', 'department', 'measure') if departments else ('coder', 'dimension', 'measure')
        expected = set(product(CODERS, DIMS, GROUPS, measures)) if departments else set(product(CODERS, DIMS, measures))
        indexes[name] = index_table(st[name], keys, expected, name)
        for row in st[name]:
            N = GROUP_N[row['department']] if departments else 4924
            require(row['fixed_denominator'] == N, 'Estimate fixed denominator mismatch')
            finite(row['proportion'], 0, 1)
            check_interval(row['confidence_interval'], N)
            if row['measure'] in ('1', POTENTIAL):
                check_interval(row['simultaneous_confidence_interval'], N)
                require(row['simultaneous_confidence_interval']['per_stratum_alpha'] == .05 / 580,
                        'Simultaneous family allocation mismatch')
    pairs = source_pairs(st)
    indexes['coder_pairwise_differences'] = index_table(st['coder_pairwise_differences'],
        ('coder', 'dimension', 'left_department', 'right_department'),
        {(c, d, g, h) for c, d, (g, h) in product(CODERS, DIMS, pairs)}, 'coder_pairwise_differences')
    for row in st['coder_pairwise_differences']:
        finite(row['positive_difference_estimate'], -1, 1)
        check_interval(row['positive_difference_simultaneous_interval'], difference=True)
        check_interval(row['worst_pending_completion_simultaneous_interval'], difference=True)
    indexes['common_robust_directions'] = index_table(st['common_robust_directions'],
        ('dimension', 'left_department', 'right_department'),
        {(d, g, h) for d, (g, h) in product(DIMS, pairs)}, 'common_robust_directions')
    for row in st['common_robust_directions']:
        require(row['common_robust_direction'] in DIRECTIONS and set(row['coder_directions']) == set(CODERS)
                and all(v in DIRECTIONS for v in row['coder_directions'].values())
                and type(row['robust_to_design_error_and_pending']) is bool, 'Original common-direction fields missing')
        require(row['robust_to_design_error_and_pending'] == (row['common_robust_direction'] != 'not_orderable'),
                'Original common-support fields inconsistent')
        for coder in CODERS:
            original = indexes['coder_pairwise_differences'][coder, row['dimension'], row['left_department'], row['right_department']][0]
            require(row['coder_directions'][coder] == original['worst_pending_completion_simultaneous_interval']['direction'],
                    'Original per-AI direction fields inconsistent')
    return indexes


def percentage(value):
    """Display only. A nonzero endpoint is never printed as 0.000%."""
    number = value * 100
    return f'{number:.3g}%' if number and abs(number) < .0005 else f'{number:.3f}%'


def interval(ci):
    return f'[{percentage(ci["lower"])}, {percentage(ci["upper"])}]'


def build_source_audit(result, source_sha256):
    """Separate QA mapping; never included in the reader-facing Markdown."""
    require(digest(source_sha256), 'Result file SHA-256 required')
    rows = {f'/statistics/{name}/{i}': row for name in COUNTS if name != 'stratum_coder_dimension_counts'
            for i, row in enumerate(result['statistics'][name])}
    return {'source_sha256': source_sha256, 'synthetic_test': result.get('synthetic_test', False),
            'source_rows': json.loads(json.dumps(rows, ensure_ascii=False, allow_nan=False))}


def render_result(result, source_sha256, source_reference, expected_freeze_sha256, *, synthetic_test=False):
    require(digest(source_sha256), 'Result file SHA-256 required')
    ix = validate_result(result, expected_freeze_sha256, synthetic_test)
    st = result['statistics']
    lines = ['# D668 补充 AI 内容分析报告', '']
    if synthetic_test:
        lines += ['**合成软件测试：本文件不是研究结果，禁止用于真实政策结论。**', '']
    common = st['common_robust_directions']
    supported = sum(r['robust_to_design_error_and_pending'] is True for r in common)
    lines += [f'完整结果包含两名 AI 各自的部门比较。在全部 30 个“维度×部门对”中，原统计结果标记 {supported} 个共同稳健方向，'
              f'其余 {30 - supported} 个不可按该规则排序；下文完整列出，不筛选某位 AI 或仅列出排除零的项目。', '']
    pending_summary = []
    for coder in CODERS:
        values = [r['proportion'] for r in st['department_status_estimates'] if r['coder'] == coder and r['measure'] == 'pending']
        pending_summary.append(f'AI {coder} 的 20 个部门×维度待定点估计范围为 {percentage(min(values))}—{percentage(max(values))}')
    lines += ['；'.join(pending_summary) + '。待定始终单列，潜在阳性表同时展示阳性至“阳性+待定”的估计范围与抽样误差界。', '',
              '总体固定为 4924 个分析单元；样本为 1268 个唯一分析单元（R600+D668），两名 AI 的编码不增加独立单元数。'
              '分析单元按既定规则从政策文献分割，不能当作文献篇数。部门固定分母为 NMPA=1848、NHSA=2100、NHC=533、GOV=443；总体按部门总体规模加权。', '',
              '来源组沿用冻结的制度系统单次归属。系统间内容分布差异不能全部归因于某一个机关的偏好；本阶段未执行新的联合发文敏感性分析。', '',
              '**执行主体是 AI，不是真人专家；这是补充内容分析，不是新的未见样本验证，也不构成人工效度验证。**', '',
              f'精确来源：[桥接结果 JSON](<{source_reference}>)；原文件 SHA-256：`{source_sha256}`。',
              f'独立提供并核验的冻结 SHA-256：`{expected_freeze_sha256}`。本呈现程序只读取该结果文件，未重新打开原提交、收条或机器预测目录。', '',
              '百分比只用于显示；方向与共同支持逐字采用原 JSON 字段，不根据舍入后的区间重新判断。'
              '每行标注 JSON Pointer，完整主JSON归档是精确数值来源。显示3位小数只为阅读，并不代表更高统计精度。差值百分比应读作百分点。', '']

    def table(headers, rows):
        lines.append('| ' + ' | '.join(headers) + ' |')
        lines.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        for row in rows:
            lines.append('| ' + ' | '.join(map(str, row)) + ' |')
        lines.append('')

    def state_table(coder, overall):
        name = 'overall_status_estimates' if overall else 'department_status_estimates'
        rows = []
        for group, dim in product((None,) if overall else GROUPS, DIMS):
            selected = [ix[name][(coder, dim, state) if overall else (coder, dim, group, state)] for state in STATES]
            cells = [dim] if overall else [f'{group}（N={GROUP_N[group]}）', dim]
            for row, _ in selected:
                cells += [percentage(row['proportion']), interval(row['confidence_interval'])]
            cells.append('<br>'.join('`' + ref + '`' for _, ref in selected))
            rows.append(cells)
        table((['维度'] if overall else ['部门', '维度']) + ['0 点估计', '0 边际95%CI', '1 点估计', '1 边际95%CI', '待定点估计', '待定边际95%CI', '精确来源'], rows)

    def potential_table(coder, overall):
        name = 'overall_potential_positive_estimates' if overall else 'department_potential_positive_estimates'
        state_name = 'overall_status_estimates' if overall else 'department_status_estimates'
        rows = []
        for group, dim in product((None,) if overall else GROUPS, DIMS):
            q, qref = ix[name][(coder, dim, POTENTIAL) if overall else (coder, dim, group, POTENTIAL)]
            p, pref = ix[state_name][(coder, dim, '1') if overall else (coder, dim, group, '1')]
            cells = [dim] if overall else [group, dim]
            cells += [f'[{percentage(p["proportion"])}, {percentage(q["proportion"])}]',
                      percentage(q['proportion']), interval(q['confidence_interval']),
                      interval(p['simultaneous_confidence_interval']), interval(q['simultaneous_confidence_interval']),
                      f'[{percentage(p["simultaneous_confidence_interval"]["lower"])}, {percentage(q["simultaneous_confidence_interval"]["upper"])}]',
                      f'`{pref}`<br>`{qref}`']
            rows.append(cells)
        table((['维度'] if overall else ['部门', '维度']) + ['待定识别范围估计 [p,q]', 'q 点估计', 'q 边际95%CI',
              'p 家族同时界', 'q 家族同时界', '抽样误差及待定包络', '精确来源'], rows)

    lines += ['## 全部部门三态估计', '', '0=未编码为该维度，1=编码为该维度，待定=保留未决。各状态区间是单指标边际区间，不能据此作多重排序。', '']
    for coder in CODERS:
        lines += [f'### AI {coder}', '']
        state_table(coder, False)
    lines += ['## 全部部门潜在阳性与同时界', '',
              'p 为阳性比例，q 为阳性+待定比例。[p̂,q̂] 是待定任意补全的范围估计，不单独构成置信区间；'
              '最后的 [L(p),U(q)] 直接取自预定家族界，兼容抽样误差与任意待定补全。家族固定为580项，整体同时覆盖至少95%。', '']
    for coder in CODERS:
        lines += [f'### AI {coder}', '']
        potential_table(coder, False)
    lines += ['## 全部总体三态与潜在阳性', '', '总体分母固定为4924，不按各部门实际样本数作简单平均。', '']
    for coder in CODERS:
        lines += [f'### AI {coder}', '']
        state_table(coder, True)
        potential_table(coder, True)
    lines += ['## 全部60组 AI 部门差值', '', '差值统一为左部门减右部门。两个区间均沿用580项家族同时界；待定补全界允许所有待定任意取0或1。', '']
    for coder in CODERS:
        lines += [f'### AI {coder}', '']
        rows = []
        for dim, (g, h) in product(DIMS, source_pairs(st)):
            row, ref = ix['coder_pairwise_differences'][coder, dim, g, h]
            pending = row['worst_pending_completion_simultaneous_interval']
            rows.append([dim, f'{g}−{h}', percentage(row['positive_difference_estimate']),
                         interval(row['positive_difference_simultaneous_interval']), interval(pending),
                         DIRECTIONS[pending['direction']], f'`{ref}`'])
        table(['维度', '左−右', '阳性差估计', '阳性差同时界', '待定任意补全同时界', '原AI方向字段', '精确来源'], rows)
    lines += ['## 全部30项共同方向判断', '', '“共同稳健方向”要求两名AI各自的待定补全同时界同方向严格排除0。以下仅复制已冻结统计程序的决定；不可排序不等于部门相同。', '']
    rows = []
    for dim, (g, h) in product(DIMS, source_pairs(st)):
        row, ref = ix['common_robust_directions'][dim, g, h]
        rows.append([dim, f'{g}−{h}', DIRECTIONS[row['coder_directions']['A']], DIRECTIONS[row['coder_directions']['C']],
                     DIRECTIONS[row['common_robust_direction']], '是' if row['robust_to_design_error_and_pending'] else '否', f'`{ref}`'])
    table(['维度', '左−右', 'AI A 原方向', 'AI C 原方向', '原共同方向', '原稳健支持字段', '精确来源'], rows)
    lines += ['## 方法边界与来源核验', '',
              '主区间采用分层等尾精确超几何反演及Bonferroni合并；部门按各自层数分配α，总体按29层分配。'
              '两端点、两AI、五维和29层构成固定580项家族，不因稀有类、零待定或普查缩减。辅助设计方差/SE保留在原JSON，本报告不改用Wald区间。', '',
              '覆盖保证以固定有限总体编码函数和声明的分层不放回简单随机抽样为条件。两AI标签可以相关；union bound无需AI独立。'
              '区间不涵盖AI随机运行误差、共同偏差、构念效度或相对真人判断的正确性。未检验年份效应、五维份额或p值，也不强制完整排名。', '',
              '已核验结果状态、120/40/30/10估计行、60差值、30共同方向、29层元数据、1268唯一ID、冻结哈希及20文件绑定、'
              'R48份/D54份原始来源清单和归档哈希关联。收条有效性依据桥接程序已验证的归档；本呈现程序没有重新读取或重新校验每份外部收条。', '',
              '精确未舍入数值、辅助方差和完整原始归档均见文首链接的主JSON；使用各表JSON Pointer定位对应来源行。'
              '本报告不另设数据版本，也不改变原统计结果。', '']
    return '\n'.join(lines)


def write_report(input_path, output_path, expected_freeze_sha256, *, synthetic_test=False):
    """Only input_path is read. Source bytes are checked again before publishing."""
    input_path, output_path = Path(input_path).absolute(), Path(output_path).absolute()
    require(input_path != output_path and input_path.is_file(), 'Distinct existing input file required')
    partial = output_path.with_name(output_path.name + '.partial')
    require(not output_path.exists() and not partial.exists(), 'Refusing to overwrite output/partial')
    raw = input_path.read_bytes()
    result = read_json(raw)
    markdown = render_result(result, sha(raw), str(input_path), expected_freeze_sha256, synthetic_test=synthetic_test)
    require(input_path.read_bytes() == raw, 'Input changed during presentation')
    with partial.open('xb') as out:
        out.write(markdown.encode('utf-8')); out.flush(); os.fsync(out.fileno())
    os.link(partial, output_path)
    partial.unlink()
    return {'status': 'synthetic_presentation_only' if synthetic_test else 'presentation_complete',
            'source_sha256': sha(raw), 'output': str(output_path), 'output_sha256': sha(markdown.encode('utf-8')),
            'statistics_recomputed': False, 'external_source_files_read': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--expected-freeze-sha256', required=True)
    parser.add_argument('--synthetic-test', action='store_true')
    args = parser.parse_args()
    print(json.dumps(write_report(args.input, args.output, args.expected_freeze_sha256,
                                  synthetic_test=args.synthetic_test), ensure_ascii=False, indent=2))

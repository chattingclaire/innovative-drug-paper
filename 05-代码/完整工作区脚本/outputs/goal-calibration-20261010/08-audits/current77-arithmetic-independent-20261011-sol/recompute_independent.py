#!/usr/bin/env python3
"""Read-only independent arithmetic audit. Writes only beside this new file.

Uses XLSX ZIP/XML parsing and exact rational count formulas, rather than the
audited script's workbook parser or metric implementation. Only the original
metric function is AST-extracted for isolated boundary demonstrations.
"""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction
from collections import Counter, defaultdict
import ast
import csv
import hashlib
import json
import math
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
DIAG = ROOT / '07-statistics/current-v5-rule-and-native-complete77-development-diagnostics-root'
REVIEW = ROOT / '09-delivery/agent-review-20261010/真人4项复核后-v2'
RULE = ROOT / '06-coding/rule-full4481-final-v5-receipt-recovery-root'
RECOVERY = ROOT / '06-coding/native-reference77-coverage-recovery-v1-sol'
SCRIPT = ROOT / '08-audits/calculate-v5-rule-native-partial77-root.py'
DIMS = ('S', 'E', 'Ec', 'I', 'F')
NAMES = {'S': '安全性', 'E': '有效性', 'Ec': '经济性', 'I': '创新性', 'F': '公平性'}
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RELNS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
inputs = {}

def binding(path):
    path = Path(path).resolve()
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': h.hexdigest()}

def register(path, expected=None):
    b = binding(path)
    if expected is not None:
        assert b['bytes'] == expected['bytes'] and b['sha256'] == expected['sha256'], b['path']
    if b['path'] in inputs:
        assert inputs[b['path']] == b
    inputs[b['path']] = b
    return Path(b['path'])

def read_json(path, expected=None):
    return json.loads(register(path, expected).read_text(encoding='utf-8'))

def valid(v):
    return type(v) is int and v in (0, 1)

def parse_csv_binary(v):
    assert v in ('0', '1', ''), repr(v)
    return None if v == '' else int(v)

def xlsx_reference(path):
    path = register(path)
    rows, locators, formulas = {}, {}, []
    with zipfile.ZipFile(path) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
            strings = [''.join(e.itertext()) for e in tree.findall('s:si', NS)]
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = {s.attrib['name']: s.attrib['{' + RELNS + '}id'] for s in wb.findall('s:sheets/s:sheet', NS)}
        rel = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        targets = {x.attrib['Id']: x.attrib['Target'] for x in rel}
        target = targets[sheets['编码表']]
        target = target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl', target))
        tree = ET.fromstring(z.read(target))
        grid = {}
        for row in tree.findall('s:sheetData/s:row', NS):
            values = {}
            for cell in row.findall('s:c', NS):
                addr = cell.attrib['r']
                col = re.match(r'[A-Z]+', addr).group()
                t = cell.attrib.get('t', 'n')
                ve = cell.find('s:v', NS)
                raw = None if ve is None else ve.text
                if t == 'inlineStr':
                    value = ''.join(cell.find('s:is', NS).itertext())
                elif t == 's':
                    value = strings[int(raw)]
                elif t == 'n' and raw is not None:
                    value = int(raw) if re.fullmatch(r'-?\d+', raw) else float(raw)
                elif t == 'b':
                    value = bool(int(raw))
                else:
                    value = raw
                values[col] = value
                if cell.find('s:f', NS) is not None:
                    formulas.append(addr)
            grid[int(row.attrib['r'])] = values
        headers = grid[6]
        ix = {value: col for col, value in headers.items()}
        for rn, cells in sorted(grid.items()):
            if rn < 7 or not any(v is not None and str(v).strip() for v in cells.values()):
                continue
            raw_id = cells[ix['条款编号']]
            if type(raw_id) is int:
                sid = f'RECODE25-{raw_id:05d}'
            else:
                sid = str(raw_id).strip()
                if not sid.startswith('RECODE25-'):
                    sid = 'RECODE25-' + sid.zfill(5)
            d = str(cells[ix['维度']]).split()[0]
            assert d in DIMS
            value = cells[ix['编码值']]
            assert valid(value), (path, rn, value, type(value).__name__)
            key = sid, d
            assert key not in rows, key
            rows[key] = value
            locators[key] = {'sheet': '编码表', 'row': rn, 'dimension_cell': ix['维度'] + str(rn), 'value_cell': ix['编码值'] + str(rn)}
        assert not any(loc['value_cell'] in formulas for loc in locators.values()), 'reference coding value formulas require separate cache audit'
    return rows, locators

def quotient(num, den):
    return None if den == 0 else float(Fraction(num, den))

def stats(pairs, scope_N):
    # Use count identities and rational numbers; no copied P/R-based F1 logic.
    assert all(valid(r) and valid(p) for r, p in pairs)
    c = Counter(pairs)
    tp, fp, fn, tn = c[1, 1], c[0, 1], c[1, 0], c[0, 0]
    n = sum(c.values())
    rp, pp = tp + fn, tp + fp
    rn, pn = tn + fp, tn + fn
    po = quotient(tp + tn, n)
    pe = quotient(rp * pp + rn * pn, n * n)
    # Equivalent Cohen kappa count formula, exact until final conversion.
    k_num = 2 * (tp * tn - fp * fn)
    k_den = pp * rn + rp * pn
    return {'eligible_N': n, 'reference_scope_N': scope_N, 'excluded_N': scope_N - n,
            'coverage': quotient(n, scope_N), 'reference_positive_N': rp,
            'reference_negative_N': rn, 'prediction_positive_N': pp,
            'prediction_negative_N': pn, 'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
            'observed_agreement': po, 'chance_agreement': pe, 'cohen_kappa': quotient(k_num, k_den),
            'precision': quotient(tp, pp), 'recall': quotient(tp, rp),
            'f1': quotient(2 * tp, 2 * tp + fp + fn),
            'specificity': quotient(tn, rn), 'negative_predictive_value': quotient(tn, pn),
            'positive_class_agreement': quotient(2 * tp, 2 * tp + fp + fn),
            'negative_class_agreement': quotient(2 * tn, 2 * tn + fp + fn),
            'metric_denominators': {'observed_agreement': n, 'chance_agreement': n*n,
                'cohen_kappa_count_formula': k_den, 'precision': pp, 'recall': rp,
                'f1': 2*tp + fp + fn, 'specificity': rn, 'negative_predictive_value': pn,
                'positive_class_agreement': 2*tp + fp + fn, 'negative_class_agreement': 2*tn + fp + fn}}

def grouped(rows, field, restrict=None):
    eligible = [r for r in rows if valid(r[field]) and (restrict is None or restrict(r))]
    all_ids = {r['source_id'] for r in rows}
    pd = {d: stats([(r['reference_A'], r[field]) for r in eligible if r['dimension'] == d], len(all_ids)) for d in DIMS}
    complete_ids = sorted(sid for sid in all_ids if sum(r['source_id'] == sid for r in eligible) == 5)
    return {'pooled_labels': stats([(r['reference_A'], r[field]) for r in eligible], len(rows)),
            'per_dimension': pd, 'complete_five_dimension_record_N': len(complete_ids),
            'complete_five_dimension_record_coverage': quotient(len(complete_ids), len(all_ids))}

def save_json(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')

def main():
    assert not (OUT / 'report.json').exists(), 'do not overwrite an existing audit report'
    timestamp = datetime.now(timezone.utc).isoformat()
    baseline = read_json(DIAG / 'metrics.json')
    ledger_path = register(DIAG / 'comparison-ledger.csv')
    a, loc_a = xlsx_reference(REVIEW / '编码复核表-A.xlsx')
    b, loc_b = xlsx_reference(REVIEW / '编码复核表-B.xlsx')
    assert set(a) == set(b) and a == b
    ids = {s for s, d in a}
    assert len(ids) == 77 and len(a) == 385
    assert all({d for s, d in a if s == sid} == set(DIMS) for sid in ids)
    rows, keys, flagged_mismatches = [], set(), []
    with ledger_path.open(newline='', encoding='utf-8-sig') as f:
        for raw in csv.DictReader(f):
            key = raw['source_id'], raw['dimension']
            assert key not in keys and key in a
            keys.add(key)
            row = {'source_id': key[0], 'dimension': key[1]}
            for col in ('reference_A', 'reference_B', 'rule_v5', 'native_existing'):
                row[col] = parse_csv_binary(raw[col])
            assert row['reference_A'] == a[key] and row['reference_B'] == b[key]
            for col, flag in (('rule_v5', 'rule_eligible'), ('native_existing', 'native_eligible')):
                assert raw[flag] in ('True', 'False')
                if (raw[flag] == 'True') != valid(row[col]):
                    flagged_mismatches.append({'key': key, 'flag': flag})
            rows.append(row)
    assert keys == set(a) and not flagged_mismatches

    rule_seal = read_json(RULE / 'seal.json')
    seal_members = {Path(m['path']).name: m for m in rule_seal['output_files']}
    rule_values, full_nulls = {}, 0
    path = register(RULE / 'recovered-predictions.jsonl', seal_members['recovered-predictions.jsonl'])
    with path.open(encoding='utf-8') as f:
        for line in f:
            x = json.loads(line)
            assert x['id'] not in rule_values and set(x['labels']) == set(DIMS)
            assert all(valid(v) or v is None for v in x['labels'].values())
            rule_values[x['id']] = x['labels']
            full_nulls += sum(v is None for v in x['labels'].values())
    assert len(rule_values) == 4481
    execution = read_json(RULE / 'execution.json')
    assert full_nulls == execution['lawful_null_N']
    slot_map, slot_counter, slot_keys = {}, Counter(), set()
    path = register(RULE / 'all-dimension-slots.jsonl', seal_members['all-dimension-slots.jsonl'])
    with path.open(encoding='utf-8') as f:
        for line in f:
            x = json.loads(line)
            key = x['id'], x['dimension']
            assert key not in slot_keys
            slot_keys.add(key)
            assert x['rule_value'] == rule_values[key[0]][key[1]]
            slot_counter[x['status']] += 1
            if key in a:
                slot_map[key] = x
    assert len(slot_keys) == 22405 and set(slot_map) == set(a)

    native_bindings = read_json(DIAG / 'native-selection-bindings.json')
    native_values, native_origin, selection_checks = {}, {}, []
    for item in native_bindings:
        if 'selected_first' in item:
            first = read_json(item['selected_first']['path'], item['selected_first'])
            selection = read_json(item['selection'])
            receiver = read_json(item['technical_reception']['path'], item['technical_reception'])
            assert selection['original_whole_batch_first'] == item['selected_first']
            assert selection['technical_reception'] == item['technical_reception']
            records = first['records']
            origin = 'original_selected_batch'
            selection_checks.append({'selection': item['selection'], 'first_hash_matches': True,
                'receipt_hash_matches': True, 'reported_receiver_state': receiver.get('state')})
        else:
            first = read_json(item['first']['path'], item['first'])
            assert first['source_id'] == item['coverage_recovery_source_id']
            records = [first]
            origin = 'coverage_recovery_35'
        for rec in records:
            sid = rec['source_id']
            assert sid not in native_values
            assert set(rec['dimensions']) == set(DIMS)
            vals = {d: rec['dimensions'][d]['value'] for d in DIMS}
            assert all(valid(v) or v is None for v in vals.values())
            native_values[sid] = vals
            native_origin[sid] = origin
    manifest = read_json(RECOVERY / 'manifest.json')
    reception = read_json(RECOVERY / 'technical-reception.json')
    recovery_ids = {sid for sid, origin in native_origin.items() if origin == 'coverage_recovery_35'}
    assert recovery_ids == set(manifest['source_ids']) and len(recovery_ids) == 35
    reception_by_id = {x['source_id']: x for x in reception['results']}
    assert len(reception_by_id) == len(reception['results']) == 35 and set(reception_by_id) == recovery_ids
    for item in native_bindings:
        if 'coverage_recovery_source_id' in item:
            assert reception_by_id[item['coverage_recovery_source_id']]['first'] == item['first']
    assert len(native_values) == 2167
    assert len({sid for sid in ids if native_origin[sid] == 'original_selected_batch'}) == 42
    assert recovery_ids.issubset(ids)

    excluded, errors = [], []
    for row in rows:
        key = row['source_id'], row['dimension']
        assert row['rule_v5'] == rule_values[key[0]][key[1]]
        assert row['native_existing'] == native_values[key[0]][key[1]]
        row['native_origin'] = native_origin[key[0]]
        if row['rule_v5'] is None:
            slot = slot_map[key]
            excluded.append({**row, 'slot_status': slot['status'], 'rules_null': slot['rules_null'],
                             'technical_failure': slot['technical_failure'],
                             'A_locator': loc_a[key], 'B_locator': loc_b[key]})
        for method in ('rule_v5', 'native_existing'):
            if valid(row[method]) and row[method] != row['reference_A']:
                errors.append({**row, 'method': method, 'error': 'FP' if row[method] == 1 else 'FN'})
    result = {'rule_v5': grouped(rows, 'rule_v5'),
              'native_complete_coverage_recovery': grouped(rows, 'native_existing')}
    comparison_checks = []
    fields = ('eligible_N', 'reference_positive_N', 'prediction_positive_N', 'TP', 'FP', 'FN', 'TN',
              'observed_agreement', 'chance_agreement', 'cohen_kappa', 'precision', 'recall', 'f1', 'coverage')
    for method, calc in result.items():
        for scope in ('pooled_labels', *DIMS):
            lhs = calc['pooled_labels'] if scope == 'pooled_labels' else calc['per_dimension'][scope]
            rhs = baseline['methods'][method]['pooled_labels'] if scope == 'pooled_labels' else baseline['methods'][method]['per_dimension'][scope]
            for field in fields:
                expected, found = lhs[field], rhs[field]
                match = expected == found if type(expected) is int or expected is None else math.isclose(expected, found, rel_tol=0, abs_tol=1e-12)
                comparison_checks.append({'method': method, 'scope': scope, 'field': field,
                                          'independent': expected, 'original': found, 'matches': match})
            assert calc['complete_five_dimension_record_N'] == baseline['methods'][method]['complete_five_dimension_record_N']
    assert all(c['matches'] for c in comparison_checks)

    script_path = register(SCRIPT)
    tree = ast.parse(script_path.read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'metric')
    namespace = {'math': math}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SCRIPT), 'exec'), namespace)
    original_metric = namespace['metric']
    fixtures = [
        ('empty', [], []), ('both_constant_zero', [0, 0], [0, 0]),
        ('both_constant_one', [1, 1], [1, 1]),
        ('all_wrong_mixed_positive_negative', [1, 0], [0, 1]),
        ('all_false_negative', [1], [0]), ('all_false_positive', [0], [1]),
        ('positive_exists_no_true_positive_with_true_negative', [1, 0], [0, 0])]
    boundaries = []
    for name, refs, preds in fixtures:
        independent = stats(list(zip(refs, preds)), len(refs))
        original = original_metric(refs, preds)
        boundaries.append({'name': name, 'reference': refs, 'prediction': preds,
                           'independent': independent, 'original_metric_function': original,
                           'f1_matches': original.get('f1') == independent['f1']})
    assert sum(not x['f1_matches'] for x in boundaries) == 4
    assert all(x['independent']['cohen_kappa'] is None for x in boundaries[:3])
    assert all(x['original_metric_function'].get('cohen_kappa') is None for x in boundaries[:3])
    null_fixture = [{'source_id': 'fixture', 'dimension': d, 'reference_A': 1,
                     'rule_v5': None, 'native_existing': None} for d in DIMS]
    null_result = grouped(null_fixture, 'rule_v5')
    assert null_result['pooled_labels']['eligible_N'] == 0
    assert null_result['pooled_labels']['coverage'] == 0
    assert all(null_result['pooled_labels'][f] is None for f in ('cohen_kappa', 'precision', 'recall', 'f1', 'observed_agreement'))

    supplemental = {
        'native_on_rule_binary_eligible_pairs': grouped(rows, 'native_existing', lambda r: valid(r['rule_v5'])),
        'native_original_selected_42_only': grouped(rows, 'native_existing', lambda r: r['native_origin'] == 'original_selected_batch'),
        'native_coverage_recovery_35_only': grouped(rows, 'native_existing', lambda r: r['native_origin'] == 'coverage_recovery_35')}
    after = [binding(x['path']) for x in inputs.values()]
    changed = [x for x in after if x != inputs[x['path']]]
    assert not changed
    report = {'artifact_type': 'independent_conditional_current77_arithmetic_audit',
              'generated_at_utc': timestamp, 'status': 'current_arithmetic_matches_original_with_F1_boundary_defect',
              'auditor_requested_model': 'gpt-6.1-sol', 'auditor_requested_reasoning_effort': 'ultra',
              'dimension_names': NAMES,
              'interpretation': {'arithmetic_conclusion': 'Conditional on the supplied post-hoc A/B values and selected machine values, all current reported numeric metrics and coverage counts are reproduced.',
                'process_compliance_conclusion': 'Not established by arithmetic. Re-running 35 missing records as separate cases cannot be guaranteed procedurally compliant from this arithmetic audit.',
                'formal_validation_complete': False, 'human_validation_complete': False,
                'population_interval_or_generalizable_accuracy_established': False,
                'inter_rater_reliability_established': False,
                'inference': 'No p values, population confidence intervals, significance stars or formal validation claims are calculated.',
                'reference': 'A/B labels are identical saved post-hoc development reference values, not evidence of independent blinded human double coding.',
                'pooled_labels': 'Pooling five heterogeneous dimensions is a descriptive micro summary. It is not a population performance estimate.',
                'undefined_policy': 'A zero denominator yields JSON null / display NA. It is never replaced with 1.',
                'f1_policy': 'F1 = 2TP/(2TP+FP+FN); if TP=0 and FP+FN>0 it equals 0 even when precision or recall is undefined.',
                'class_agreement_policy': 'Positive/negative class agreement are symmetric 2TP/(2TP+FP+FN) and 2TN/(2TN+FP+FN), respectively. Reference-conditioned positive/negative agreement correspond to recall/specificity.'},
              'input_integrity': {'all_used_files_unchanged_after_audit': True, 'input_file_N': len(inputs),
                'modified_original_file_N': 0, 'original_script_executed_as_program': False,
                'original_script_AST_metric_only_boundary_execution': True},
              'reference_check': {'record_N': len(ids), 'label_N': len(a), 'A_B_value_disagreement_N': 0,
                'A_B_ledger_value_difference_N': 0, 'ledger_duplicate_key_N': 0,
                'ledger_eligibility_flag_difference_N': 0,
                'full_reference_positive_N_by_dimension': dict(Counter(d for (sid, d), v in a.items() if v == 1)),
                'workbook_hashes_match_original_metrics': all(inputs[str((REVIEW / f'编码复核表-{letter}.xlsx').resolve())]['sha256'] == baseline['reference']['workbooks'][i]['sha256'] for i, letter in enumerate(('A', 'B')))},
              'source_value_check': {'rule_record_N': len(rule_values), 'rule_full_dimension_slot_N': len(slot_keys),
                'rule_full_null_N': full_nulls, 'rule_slots_status_counts': dict(slot_counter),
                'current77_rule_ledger_difference_N': 0, 'current77_native_ledger_difference_N': 0,
                'native_total_selected_or_recovery_record_N': len(native_values),
                'original_selected_batch_N': len(selection_checks), 'coverage_recovery_record_N': len(recovery_ids),
                'original_native_reference_record_N': 42, 'recovery_native_reference_record_N': 35,
                'native_values_sha256_checked': True,
                'hash_binding_and_value_checks_do_not_certify_procedural_or_semantic_compliance': True},
              'metrics': result, 'supplemental_conditioned_metrics': supplemental,
              'original_metric_comparison': {'comparison_N': len(comparison_checks), 'mismatch_N': 0, 'tolerance': 1e-12},
              'original_script_review': {'path': str(SCRIPT), 'metric_function_start_line': node.lineno,
                'NA_promoted_to_one_in_current_calculation': False,
                'degenerate_constant_kappa_returns_NA': True,
                'null_values_excluded_not_zero_filled': True,
                'eligibility_is_dimension_specific': True,
                'F1_boundary_defect': {'confirmed': True, 'affected_current_numeric_result_N': 0,
                    'failing_fixture_N': 4, 'cause': 'F1 is gated by undefined P/R or P+R=0 instead of the 2TP+FP+FN denominator.',
                    'recommended_future_formula': 'None if 2*TP+FP+FN == 0 else 2*TP/(2*TP+FP+FN)',
                    'original_script_modified': False},
                'interface_note': 'metric() itself assumes eligible binary lists; current caller filters prediction values per dimension and references are binary. This audit separately checks actual value types and key coverage.'},
              'rule_null_exclusions': excluded, 'binary_disagreements': errors,
              'boundary_checks': boundaries, 'all_null_coverage_fixture': null_result}
    save_json('report.json', report)
    save_json('metric-comparison.json', comparison_checks)
    save_json('native-selection-hash-readback.json', selection_checks)
    save_json('input-bindings.json', {'generated_at_utc': timestamp, 'members': sorted(inputs.values(), key=lambda x: x['path']), 'post_audit_unchanged': True})
    with (OUT / 'independently-reconstructed-pairs.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    md = ['# 当前 77 条机器诊断独立算术审计', '',
          '在给定事后 A/B 参照值、规则 v5 输出及当前选定原生输出的条件下，原报告的当前数值和覆盖率均可复算。独立复算使用 XLSX ZIP/XML 读取和计数恒等式，未调用原脚本计算当前指标。', '',
          'A/B 各 385 个值全部一致，账本为 77 条 × 5 维且无重复。逐项回查规则完整输出、维度槽位及原生输出后，账本值差异为 0。168 项原报告数值比较均在 1e-12 容差内一致。输入文件审计前后 SHA-256 未变。', '',
          'Ec 是经济性，I 是创新性。', '',
          '## 当前指标与分母', '',
          'κ、P、R、F1、Po 均在各方法各维实际二元可计分槽位集合上计算。P 的分母为 TP+FP，R 为 TP+FN，F1 为 2TP+FP+FN，Po 为 N；κ采用相应边际分布。下表中的 N/77 是覆盖数。null 不替换为 0 或 1。', '',
          '|方法|维度|N/77|TP|FP|FN|TN|κ|P|R|F1|Po|',
          '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    fmt = lambda v: 'NA' if v is None else f'{v:.6f}'
    for method, label in (('rule_v5', '规则 v5'), ('native_complete_coverage_recovery', '原生合并')):
        for d in DIMS:
            s = result[method]['per_dimension'][d]
            md.append('|'+ '|'.join([label, d+' '+NAMES[d], f"{s['eligible_N']}/77", *(str(s[x]) for x in ('TP','FP','FN','TN')), *(fmt(s[x]) for x in ('cohen_kappa','precision','recall','f1','observed_agreement'))])+'|')
    md += ['', '规则 pooled 仅为 379/385 个可计分标签，κ=0.873305、P=0.983607、R=0.821918、F1=0.895522、Po=0.963061。原生合并为 385/385，κ=0.976000、P=0.962500、R=1.000000、F1=0.980892、Po=0.992208。此 pooled 汇总跨五维，仅供描述。', '',
           '## 辅助指标', '',
           '|方法|维度|特异度|NPV|正类一致率|负类一致率|', '|---|---|---:|---:|---:|---:|']
    for method, label in (('rule_v5', '规则 v5'), ('native_complete_coverage_recovery', '原生合并')):
        for d in DIMS:
            s = result[method]['per_dimension'][d]
            md.append('|'+ '|'.join([label, d+' '+NAMES[d], *(fmt(s[x]) for x in ('specificity','negative_predictive_value','positive_class_agreement','negative_class_agreement'))])+'|')
    md += ['', '特异度=TN/(TN+FP)，NPV=TN/(TN+FN)。正/负类一致率采用对称定义 2TP/(2TP+FP+FN) 和 2TN/(2TN+FP+FN)。若使用参照条件下的正/负类一致率，则对应 R/特异度。每个指标的实际数量分母已保存于 report.json。', '',
           '## 空值与覆盖率', '',
           '规则法 6 个 null 分布于 3 条：00110/F、00118/F、01423/S、01423/E、01423/Ec、01423/F。槽位均标记为合法规则 null，technical_failure=false。被排除的参照标签中有 4 个正类、2 个负类。规则全五维完整为 74/77；原生为 77/77。', '',
           '完整参照各维正类数为 S=11、E=13、Ec=17、I=22、F=14。规则可计分正类数为 S=10、E=12、Ec=17、I=22、F=12。规则 F 的 R=1、F1=1 是 74 条可计分条件下的结果，未覆盖的 2 个 F 正类不能视为识别成功。不同方法的指标使用不同可计分集合，不能忽略覆盖率直接等同比较。report.json 另给出原生在规则同一 379 槽位上的条件性指标。', '',
           '当前原生 77 条由原整批选定输出覆盖的 42 条和另补跑的 35 条组成。42+35=77，210+175=385；原始 42 条单独覆盖 210/385，补跑后才达到 385/385。报告另列原 42 条和补跑 35 条的描述性结果。', '',
           '## 原脚本边界检查', '',
           f'原脚本 metric() 从第 {node.lineno} 行开始。通过 AST 仅取出该函数测试边界，未运行原脚本主流程。当前各维 TP>0，因此现有结果未触发下述 F1 缺陷。', '',
           'F1 应按 2TP/(2TP+FP+FN) 计算。TP=0 且 FP+FN>0 时，F1=0。原实现以 P/R 是否为空及 P+R=0 决定返回空值，使混合正负类全错、全假阴性、全假阳性及有真阴性但无真正例四种测试返回 NA。该缺陷需要在后续获准修改计算器时修复，本次没有改原脚本。', '',
           '空样本或仅同一常数类别的 κ 无定义时保留 NA，未写成 1。全 0 对全 0 的 Po=1 有定义，但 P、R、F1 为 NA。全 null 测试可计分 N=0、coverage=0，κ/P/R/F1/Po 均为 NA。', '',
           '## 结论范围', '',
           '本审计只支持给定输入下的算术一致性。35 条补跑流程的合规性无法从算术保证；哈希、数量和逐值一致也不证明盲法、无泄漏、冻结顺序、单次首跑、供应商实际服务模型或语义判读正确。原生 77 条是原整批输出与分案补跑的合并开发诊断。', '',
           'A/B 最终值一致不能证明独立真人双盲编码。本报告不声明 formal 验证、总体区间或可推广准确率已经成立，不计算 p 值、显著性或置信区间。', '']
    (OUT / 'report.md').write_text('\n'.join(md), encoding='utf-8')
    output_members = [binding(p) | {'relative_path': p.name} for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'seal.json']
    save_json('seal.json', {'artifact_type': 'independent_current77_arithmetic_audit_output_seal',
        'sealed_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'sealed',
        'inputs_unchanged': True, 'input_bindings_file': 'input-bindings.json', 'members': output_members,
        'only_new_audit_directory_written': True, 'formal_validation_complete': False,
        'coverage_recovery_process_compliance_established': False})
    print(json.dumps({'status': report['status'], 'out': str(OUT), 'comparison_N': len(comparison_checks),
                      'F1_failing_fixture_N': 4, 'input_file_N': len(inputs)}, ensure_ascii=False))

if __name__ == '__main__':
    main()

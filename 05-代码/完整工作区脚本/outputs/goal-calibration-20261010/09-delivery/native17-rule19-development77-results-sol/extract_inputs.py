from pathlib import Path
import hashlib
import json
import shutil
import openpyxl

ROOT = Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
OUT = ROOT / '09-delivery/native17-rule19-development77-results-sol'
STAT = ROOT / '07-statistics/native-v17-rule-v19-human-confirmed77-root'
DIMS = {'S': 'S 安全性', 'E': 'E 有效性', 'Ec': 'Ec 经济性', 'I': 'I 创新性', 'F': 'F 公平性'}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def jload(path):
    return json.loads(Path(path).read_text())

metrics = jload(STAT / 'metrics.json')
seal = jload(STAT / 'companion-report-seal.json')
derived = [json.loads(s) for s in (STAT / 'derived-native-predictions.jsonl').read_text().splitlines() if s]
rules_path = Path(metrics['rule_predictions']['path'])
rule_rows = [json.loads(s) for s in rules_path.read_text().splitlines() if s]
rules = {r['id']: (i + 1, r) for i, r in enumerate(rule_rows)}
assert len(derived) == 77 and len(rules) == 77

manifest = []
def capture(path, rel, expected=None):
    path = Path(path)
    actual = sha(path)
    if expected:
        assert actual == expected, (str(path), actual, expected)
    dest = OUT / 'inputs' / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, dest)
    assert sha(dest) == actual
    manifest.append({'original_path': str(path), 'archive_relative_path': 'inputs/' + str(rel), 'bytes': path.stat().st_size, 'sha256': actual})

for name in ['metrics.json', 'derived-native-predictions.jsonl', 'companion-report-seal.json', '当前结果与剩余事项.txt']:
    capture(STAT / name, Path('statistics') / name)
capture(rules_path, Path('rule') / 'predictions.jsonl', metrics['rule_predictions']['sha256'])

human = []
for n, binding in zip(['A', 'B'], metrics['reference_bindings']):
    path = Path(binding['path'])
    capture(path, Path('human') / path.name, binding['sha256'])
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = book['编码表']
    rows = {}
    for idx, vals in enumerate(sheet.iter_rows(values_only=True), 1):
        if vals and isinstance(vals[0], str) and vals[0].startswith('RECODE25-'):
            dim = vals[2].split()[0]
            key = (vals[0], dim)
            assert key not in rows and vals[3] in (0, 1)
            rows[key] = {'department': vals[1], 'label': vals[3], 'reason': vals[4], 'row': idx, 'cell': 'D' + str(idx), 'reason_cell': 'E' + str(idx), 'path': str(path), 'sheet': '编码表'}
    assert len(rows) == 385
    human.append(rows)
    book.close()

raw_files = {}
for item in derived:
    binding = item['original_whole_batch_submission']
    path = Path(binding['path'])
    if str(path) not in raw_files:
        raw_files[str(path)] = jload(path)
        capture(path, Path('native') / path.parent.parent.name / path.parent.name / path.name, binding['sha256'])

code_rows = []
diff_rows = []
for item in derived:
    rid = item['id']
    raw = raw_files[item['original_whole_batch_submission']['path']]
    index = int(item['record_pointer'].split('/')[-1])
    record = raw['records'][index]
    assert record['source_id'] == rid
    rline, rule = rules[rid]
    for dim, name in DIMS.items():
        a, b = human[0][rid, dim], human[1][rid, dim]
        llm = record['dimensions'][dim]
        assert llm['value'] == item['labels'][dim]
        rulevalue = rule['labels'][dim]
        assert a['department'] == b['department']
        llmpath = str(Path(item['original_whole_batch_submission']['path']).relative_to(ROOT))
        llmpointer = item['record_pointer'] + '/dimensions/' + dim
        rulepointer = str(rules_path.relative_to(ROOT)) + ':第' + str(rline) + '行 /decisions/' + dim
        asource = str(Path(a['path']).relative_to(ROOT)) + '#编码表!' + a['cell'] + ',' + a['reason_cell']
        bsource = str(Path(b['path']).relative_to(ROOT)) + '#编码表!' + b['cell'] + ',' + b['reason_cell']
        row = [rid, a['department'], name, a['label'], b['label'], llm['value'], rulevalue, llm['reason'], llmpath + '#' + llmpointer, rulepointer, asource, bsource]
        code_rows.append(row)
        if llm['value'] != a['label']:
            diff_rows.append({'id': rid, 'department': a['department'], 'dimension': name, 'dimension_code': dim, 'reference_A': a['label'], 'reference_B': b['label'], 'LLM': llm['value'], 'rule': rulevalue, 'relative_direction': '相对当前参照多判', 'LLM_reason': llm['reason'], 'rule_reason': rule['decisions'][dim]['reason'], 'A_reason': a['reason'], 'B_reason': b['reason'], 'LLM_source': row[8], 'rule_source': row[9], 'A_source': asource, 'B_source': bsource})

assert len(code_rows) == 385
assert {(r['id'], r['dimension_code']) for r in diff_rows} == {('RECODE25-04457', 'I'), ('RECODE25-00131', 'F')}
assert all(r['reference_A'] == r['reference_B'] == r['rule'] == 0 and r['LLM'] == 1 for r in diff_rows)
diff_rows.sort(key=lambda r: 0 if r['id'] == 'RECODE25-04457' else 1)

metric_rows = []
comparison_names = {'LLM_vs_confirmed_reference': 'LLM首答与当前参照', 'rule_vs_confirmed_reference': '规则首答与当前参照', 'saved_A_vs_B': '保存A与B'}
counts = ['assigned_N', 'saved_N', 'joint_binary_N', 'reference_positive_N', 'reference_negative_N', 'prediction_positive_N', 'prediction_negative_N']
met_keys = ['kappa', 'precision', 'recall', 'F1', 'Po', 'Pe', 'Ppos', 'Pneg', 'specificity', 'NPV']
for comp, title in comparison_names.items():
    for dim, name in DIMS.items():
        value = metrics['comparisons'][comp]['dimensions'][dim]
        row = [title, name] + [value[k] for k in counts] + [value['four_cells'][k] for k in ['TP', 'FP', 'FN', 'TN']] + [value['metrics'][k] if value['metrics'][k] is not None else 'NA' for k in met_keys] + [('达到' if value['point_targets'][k] else '未达到') if value['point_targets'][k] is not None else 'NA' for k in ['kappa', 'precision', 'recall', 'F1']] + ['NA' if value['CI95'] is None else json.dumps(value['CI95']), 'NA', '/comparisons/' + comp + '/dimensions/' + dim]
        assert len(row) == 30
        metric_rows.append(row)

payload = {'root': str(ROOT), 'out': str(OUT), 'metrics_created_at_utc': metrics['created_at_utc'], 'code_rows': code_rows, 'metric_rows': metric_rows, 'differences': diff_rows, 'input_manifest': manifest, 'reference_bindings': metrics['reference_bindings'], 'scope': {'assigned_records_N': metrics['assigned_records_N'], 'assigned_slots_N': metrics['assigned_slots_N'], 'LLM_binary_slots_N': metrics['LLM_binary_slots_N'], 'LLM_semantic_null_slots_N': metrics['LLM_semantic_null_slots_N'], 'LLM_terminal_failed_batches_N': metrics['LLM_terminal_failed_batches_N'], 'actual_actor_attempt_N': seal['actual_actor_attempt_N'], 'technical_invalid_attempt_N': seal['technical_invalid_attempt_N'], 'actual_assigned_record_attempt_N': seal['actual_assigned_record_attempt_N']}}
(OUT / 'inputs' / 'mechanical-workbook-input.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2))
(OUT / 'inputs' / 'input-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
print(json.dumps({'rows': len(code_rows), 'metric_rows': len(metric_rows), 'differences': [(r['id'], r['dimension_code']) for r in diff_rows], 'original_inputs_captured': len(manifest), 'max_LLM_reason_chars': max(len(r[7]) for r in code_rows)}, ensure_ascii=False))

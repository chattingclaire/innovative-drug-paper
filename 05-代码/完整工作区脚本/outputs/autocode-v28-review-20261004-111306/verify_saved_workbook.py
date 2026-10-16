"""Read saved OOXML independently of the workbook-authoring library."""
from pathlib import Path
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def read(name):
    return json.loads((ROOT / name).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def match(actual, expected):
    if expected is None:
        assert actual in (None, 'n.a.'), (actual, expected)
    elif isinstance(expected, (int, float)):
        assert abs(float(actual) - expected) < 1e-10, (actual, expected)
    else:
        assert actual == expected, (actual, expected)


data = read('audit_report_data.json')
extended = read('extended_metrics.json')
with zipfile.ZipFile(ROOT / '自动规则复核与κ对照-v28.xlsx') as archive:
    strings = [''.join(t.itertext()) for t in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
    def cells(number):
        tree = ET.fromstring(archive.read(f'xl/worksheets/sheet{number}.xml'))
        result = {}
        for cell in tree.findall('m:sheetData/m:row/m:c', NS):
            assert cell.get('t') != 'e', (number, cell.attrib)
            value = cell.find('m:v', NS)
            result[cell.get('r')] = (None if value is None else
                strings[int(value.text)] if cell.get('t') == 's' else value.text)
        return result

    sheets = [cells(i) for i in range(1, 7)]
    wb = ET.fromstring(archive.read('xl/workbook.xml'))
    assert [s.get('name') for s in wb.find('m:sheets', NS)] == [
        'κ与工作目标', '逐条复核', '规则调整', '全量编码', '完整指标与区间', 'A与C一致性']
    detail = sheets[3]
    for i, row in enumerate(data['all_rows'], 2):
        match(detail[f'A{i}'], row['id'])
        match(detail[f'C{i}'], row['text'])
        for col, dim in zip('DEFGH', ('S', 'E', 'Ec', 'I', 'F')):
            match(detail[f'{col}{i}'], row['after'][dim])
    assert len(data['all_rows']) == 4924
    for i, metric in enumerate(data['metrics'], 37):
        for col, key in zip('LMNO', ('kappa', 'precision', 'recall', 'f1')):
            match(sheets[0][f'{col}{i}'], metric[key])
        for col, key in zip('EFGH', ('TP', 'FP', 'FN', 'TN')):
            match(sheets[0][f'{col}{i}'], metric['confusion'][key])
    match(sheets[0]['B4'], .8)
    match(sheets[0]['B27'], data['summary']['rules_v28_at_target'])
    for i, row in enumerate(data['reviews'], 5):
        match(sheets[1][f'A{i}'], row['id'])
        match(sheets[1][f'E{i}'], row['text'])
        for col, key in zip('FGHIJ', ('old_rule', 'semantic_review', 'new_rule', 'A', 'C')):
            match(sheets[1].get(f'{col}{i}'), row[key])
    interval_row = 6
    ac_row = 6
    for record in extended['records']:
        for metric in record['metrics'].values():
            expected = [metric['estimate'], metric['ci95']['low'], metric['ci95']['high'],
                        metric['ci95']['defined_repetitions']]
            for col, value in zip('JKLM', expected):
                match(sheets[4].get(f'{col}{interval_row}'), value)
            interval_row += 1
        if record['method'] == 'A_C':
            expected = [record['n'], record['excluded_n'], record['prediction_positive_n'],
                        record['reference_positive_n'], record['metrics']['agreement']['estimate'],
                        record['metrics']['kappa']['estimate'], record['metrics']['kappa']['ci95']['low'],
                        record['metrics']['kappa']['ci95']['high']]
            for col, value in zip('CDEFGHIJ', expected):
                match(sheets[5].get(f'{col}{ac_row}'), value)
            ac_row += 1
    assert interval_row == 326 and ac_row == 16

release = read('release_manifest.json')
analysis = read('analysis_binding.json')
for name, expected in release['code_and_input_bindings'].items():
    assert digest(name) == expected, name
for name, expected in release['output_bindings'].items():
    assert digest(ROOT / name) == expected, name
for name, expected in analysis['reference_bindings'].items():
    assert digest(name) == expected, name
assert digest(ROOT / 'release_manifest.json') == analysis['release_manifest_sha256']
assert digest(ROOT / 'metrics.json') == analysis['metrics_sha256']
report = {
    'version': release['version'],
    'all_4924_exported_ids_and_original_texts_match': True,
    'all_24620_current_labels_match': True,
    'all_240_exported_formula_metric_caches_match': True,
    'all_320_interval_rows_and_10_AC_rows_match': True,
    'all_reviewed_labels_and_original_texts_match': True,
    'no_OOXML_error_cells_in_six_sheets': True,
    'frozen_code_inputs_outputs_and_original_references_unchanged': True,
    'artifact_bindings': {name: digest(ROOT / name) for name in (
        '自动规则复核与κ对照-v28.xlsx', 'build_workbook.mjs', 'extended_metrics.py',
        'extended_metrics.json', 'audit_report_data.json', '完整指标与95区间.csv',
        '全量编码-v28.csv', 'verify_saved_workbook.py')},
}
(ROOT / 'saved_workbook_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'artifact_bindings'}, ensure_ascii=False))

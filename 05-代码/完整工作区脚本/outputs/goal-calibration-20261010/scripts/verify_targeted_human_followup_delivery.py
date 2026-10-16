import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '09-delivery/agent-review-20261010'
BACKUP = ROOT / '00-baseline/20261010-pre-targeted-human-followup-edits'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def read(path, sheet):
    with zipfile.ZipFile(path) as z:
        shared = [''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', NS)] if 'xl/sharedStrings.xml' in z.namelist() else []
        tree = ET.fromstring(z.read(f'xl/worksheets/sheet{sheet}.xml'))
        cells, formulas = {}, {}
        for c in tree.findall('s:sheetData/s:row/s:c', NS):
            v = c.find('s:v', NS)
            value = v.text if v is not None else None
            if c.get('t') == 's':
                value = shared[int(value)]
            elif c.get('t') == 'inlineStr':
                value = ''.join(c.find('s:is', NS).itertext())
            elif value is not None and c.get('t') not in ['str', 'e']:
                value = float(value)
            cells[c.get('r')] = value
            f = c.find('s:f', NS)
            if f is not None:
                formulas[c.get('r')] = f.text
            assert c.get('t') != 'e', (path, c.get('r'), value)
        panes = [p.attrib for p in tree.findall('s:sheetViews/s:sheetView/s:pane', NS)]
        validations = [ET.tostring(p).decode() for p in tree.findall('s:dataValidations', NS)]
        return cells, formulas, panes, validations

event = json.loads((ROOT / 'logs/user-targeted-human-followup-received-20261010.json').read_text())
receipt = json.loads((ROOT / 'logs/targeted-human-followup-review-delivery/applied-targeted-human-followup-receipt.json').read_text())
evidence = {'role': 'Read-only verification of saved user-confirmed targeted human corrections', 'workbooks': [], 'metric_checks_N': 0, 'human_posthoc_review_received': True, 'independent_human_first_coding_proven': False}
for coder in ['A', 'B']:
    filename = f'编码复核表-{coder}.xlsx'
    old, old_f, old_panes, old_validations = read(BACKUP / filename, 1)
    current, f, panes, validations = read(OUT / filename, 1)
    expected_changes = {int(c['cell'][1:]): c for c in event['label_changes']}
    changes = []
    for row in range(7, 392):
        change = expected_changes.get(row)
        for col in 'ABCDEFGH':
            expected = old.get(f'{col}{row}')
            if change and col == 'D': expected = change['value']
            if change and col == 'E': expected = change['reason']
            if change and col == 'G': expected = '真人补充复核结论已应用 20261010'
            assert current.get(f'{col}{row}') == expected, (coder, row, col)
        if current[f'D{row}'] != old[f'D{row}']:
            changes.append({'id': current[f'A{row}'], 'cell': f'D{row}', 'before': old[f'D{row}'], 'after': current[f'D{row}']})
    assert len(changes) == 4
    assert current['D277'] == 1 and current['D367'] == 0
    assert panes == old_panes and validations == old_validations and f == old_f
    assert read(BACKUP / filename, 2) == read(OUT / filename, 2), 'Source cells/formulas/panes/validations changed'
    evidence['workbooks'].append({'file': filename, 'sha256': hashlib.sha256((OUT / filename).read_bytes()).hexdigest(), 'label_changes': changes, 'all_source_values_preserved': True, 'panes_and_validation_preserved': True, 'prior_two_corrections_preserved': True})

metrics = json.loads((ROOT / '07-statistics/human-targeted-followup-recompute-sol/metrics.json').read_text())
initial = json.loads((ROOT / '07-statistics/agent-blind-tables-current-recompute-sol/metrics-all-available.json').read_text())
addendum = json.loads((ROOT / '07-statistics/agent-modified-table-reference-recompute-sol/metrics-addendum.json').read_text())
old_metrics, old_formulas, old_panes, old_validations = read(BACKUP / '指标完整复算.xlsx', 2)
saved, saved_formulas, saved_panes, saved_validations = read(OUT / '指标完整复算.xlsx', 2)
assert saved_formulas == old_formulas and saved_panes == old_panes and saved_validations == old_validations
comparisons = []
for c in metrics['comparisons']:
    idx = next(i for i, x in enumerate(addendum['comparisons']) if x['name'] == c['name'])
    comparisons.append((77 + idx * 5, c))
idx = next(i for i, x in enumerate(initial['comparisons']) if x['name'] == metrics['A_B_comparison']['name'])
comparisons.append((7 + idx * 5, metrics['A_B_comparison']))
allowed_changed = set()
for start, comparison in comparisons:
    for i, dimension in enumerate(['S', 'E', 'Ec', 'I', 'F']):
        row = start + i
        x = comparison['dimensions'][dimension]
        for metric, col in {'Po': 'S', 'Pe': 'T', 'kappa': 'U', 'Ppos': 'V', 'Pneg': 'W', 'precision': 'X', 'recall': 'Y', 'F1': 'Z', 'specificity': 'AA', 'NPV': 'AB'}.items():
            if metric not in x['metrics']:
                continue
            expected, actual = x['metrics'][metric]['value'], saved[f'{col}{row}']
            assert (actual == 'NA') if expected is None else abs(actual - expected) < 1e-10, (comparison['name'], dimension, metric, expected, actual)
            evidence['metric_checks_N'] += 1
        for key, col in [('a', 'F'), ('b', 'G'), ('c', 'H'), ('d', 'I')]:
            assert saved[f'{col}{row}'] == x['four_cells'][key]
        for col in ['F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','AA','AB','AC','AE']:
            allowed_changed.add(f'{col}{row}')
for cell in set(saved) | set(old_metrics):
    if cell not in allowed_changed:
        assert saved.get(cell) == old_metrics.get(cell), ('Unrelated metric detail cell changed', cell)
evidence['workbooks'].append({'file': '指标完整复算.xlsx', 'sha256': hashlib.sha256((OUT / '指标完整复算.xlsx').read_bytes()).hexdigest(), 'all_saved_formulas_preserved': True, 'saved_metric_values_verified': True, 'unrelated_detail_cells_preserved': True})
for entry in receipt['output_files']:
    assert hashlib.sha256((OUT / entry['filename']).read_bytes()).hexdigest() == entry['sha256']
target = ROOT / 'logs/root-targeted-human-followup-delivery-verification-20261010.json'
target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'verified': True, 'metric_checks_N': evidence['metric_checks_N'], 'path': str(target)}, ensure_ascii=False))

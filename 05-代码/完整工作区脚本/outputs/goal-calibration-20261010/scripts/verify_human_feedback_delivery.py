import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '09-delivery/agent-review-20261010'
BACKUP = ROOT / '00-baseline/20261010-pre-human-feedback-edits'
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
            assert not (c.get('t') == 'e'), (path, c.get('r'), value)
        panes = [p.attrib for p in tree.findall('s:sheetViews/s:sheetView/s:pane', NS)]
        validations = [ET.tostring(p).decode() for p in tree.findall('s:dataValidations', NS)]
        return cells, formulas, panes, validations

receipt = json.loads((ROOT / 'logs/human-feedback-review-delivery/applied-human-feedback-receipt.json').read_text())
evidence = {'role': 'Read-only verification of actually saved delivery', 'workbooks': [], 'metric_checks_N': 0, 'human_independent_coding_completed': False}
for coder in ['A', 'B']:
    filename = f'编码复核表-{coder}.xlsx'
    old, _, old_panes, old_validations = read(BACKUP / filename, 1)
    current, _, panes, validations = read(OUT / filename, 1)
    changes = []
    for row in range(7, 392):
        for col in ['A', 'B', 'C', 'F']:
            assert current.get(f'{col}{row}') == old.get(f'{col}{row}')
        if current[f'D{row}'] != old[f'D{row}']:
            changes.append({'id': current[f'A{row}'], 'row': row, 'before': old[f'D{row}'], 'after': current[f'D{row}']})
    assert changes == [{'id': 'RECODE25-01423', 'row': 277, 'before': 0, 'after': 1}, {'id': 'RECODE25-04333', 'row': 367, 'before': 1, 'after': 0}]
    assert panes == old_panes
    assert validations == old_validations
    sources_old, _, _, _ = read(BACKUP / filename, 2)
    sources, _, _, _ = read(OUT / filename, 2)
    for row in range(7, 765):
        for col in 'ABCDEF':
            assert sources.get(f'{col}{row}') == sources_old.get(f'{col}{row}')
    groups = {}
    for row in range(765, 1000):
        if f'A{row}' not in sources:
            continue
        key = (sources[f'A{row}'], sources[f'B{row}'].split(' (')[0])
        groups[key] = groups.get(key, '') + sources[f'E{row}']
    supplement = json.loads((ROOT / '04-calibration/human-review-evidence-supplements-sol/supplements.json').read_text())
    for entry in supplement['append_rows']:
        assert groups[(entry['record_id'], entry['resource_id'])] == entry['full_text']
    for id_ in ['RECODE25-00036', 'RECODE25-00038', 'RECODE25-00045']:
        packet = json.loads((ROOT / f'06-coding/development77-native-inputs-v14/packets/{id_}.compact.json').read_text())
        for resource in packet['source_bundle']['source_full_text_resources']:
            assert groups[(id_, resource['source_resource_id'])] == resource['text']
    evidence['workbooks'].append({'file': filename, 'sha256': hashlib.sha256((OUT / filename).read_bytes()).hexdigest(), 'label_changes': changes, 'original_sources_preserved': True, 'complete_supplemental_groups_N': len(groups), 'panes_and_validation_preserved': True})
metrics = json.loads((ROOT / '07-statistics/human-feedback-current-recompute-sol/metrics.json').read_text())
old_metrics, old_formulas, old_panes, _ = read(BACKUP / '指标完整复算.xlsx', 2)
saved, saved_formulas, saved_panes, _ = read(OUT / '指标完整复算.xlsx', 2)
assert saved_formulas == old_formulas
assert saved_panes == old_panes
for idx, comparison in enumerate(metrics['comparisons']):
    for i, dimension in enumerate(['S', 'E', 'Ec', 'I', 'F']):
        row = 77 + 5 * idx + i
        x = comparison['dimensions'][dimension]
        for metric, col in {'Po': 'S', 'Pe': 'T', 'kappa': 'U', 'Ppos': 'V', 'Pneg': 'W', 'precision': 'X', 'recall': 'Y', 'F1': 'Z', 'specificity': 'AA', 'NPV': 'AB'}.items():
            expected, actual = x['metrics'][metric]['value'], saved[f'{col}{row}']
            assert (actual == 'NA') if expected is None else abs(actual - expected) < 1e-10, (comparison['name'], dimension, metric, expected, actual)
            evidence['metric_checks_N'] += 1
        for key, col in [('a', 'F'), ('b', 'G'), ('c', 'H'), ('d', 'I')]:
            assert saved[f'{col}{row}'] == x['four_cells'][key]
evidence['workbooks'].append({'file': '指标完整复算.xlsx', 'sha256': hashlib.sha256((OUT / '指标完整复算.xlsx').read_bytes()).hexdigest(), 'all_saved_formulas_preserved': True, 'saved_metric_values_verified': True})
for entry in receipt['output_files']:
    assert hashlib.sha256((OUT / entry['filename']).read_bytes()).hexdigest() == entry['sha256']
target = ROOT / 'logs/root-human-feedback-delivery-verification-20261010.json'
target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'verified': True, 'metric_checks_N': evidence['metric_checks_N'], 'path': str(target)}, ensure_ascii=False))

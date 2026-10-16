from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '真人复核'
SOURCE = ROOT.parent / 'goal-calibration-20261010/09-delivery/human200-independent-preparation-root'
NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rename_metadata(p, old, new):
    if old == new:
        return
    with zipfile.ZipFile(p) as z:
        infos = z.infolist()
        parts = {i.filename: z.read(i.filename) for i in infos}
    wb = ET.fromstring(parts['xl/workbook.xml'])
    sheets = wb.findall(f'{{{NS}}}sheets/{{{NS}}}sheet')
    assert len(sheets) == 1 and sheets[0].get('name') in (old, new)
    sheets[0].set('name', new)
    for n in wb.findall(f'{{{NS}}}definedNames/{{{NS}}}definedName'):
        if n.text:
            n.text = n.text.replace(f"'{old}'!", f"'{new}'!").replace(f'{old}!', f"'{new}'!")
    parts['xl/workbook.xml'] = ET.tostring(wb, encoding='utf-8', xml_declaration=True)
    if 'docProps/app.xml' in parts:
        app = ET.fromstring(parts['docProps/app.xml'])
        for n in app.iter():
            if n.text == old:
                n.text = new
        parts['docProps/app.xml'] = ET.tostring(app, encoding='utf-8', xml_declaration=True)
    tmp = p.with_suffix('.tmp.xlsx')
    with zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for i in infos:
            z.writestr(i, parts[i.filename])
    tmp.replace(p)


def symlink_if_missing(p, target):
    if not p.exists():
        p.symlink_to(target, target_is_directory=True)
    assert p.resolve() == target.resolve()


def main():
    spec = importlib.util.spec_from_file_location('helper', ROOT / '_build/verify_workbooks.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    versions = json.loads((OUT / '真人复核版本记录.json').read_text())
    manifest = json.loads((OUT / '录入记录.json').read_text())
    records = {(r['source_id'], r['dimension']): r for r in manifest['rows']}
    mappings = json.loads((SOURCE / 'coordinator-private/draw-and-mapping.json').read_text())['records']
    assert len(records) == 1000
    checks = []
    comparison = None
    for item in versions['outputs']:
        p, side = Path(item['path']), item['side']
        if item['key'] != 'summary':
            symlink_if_missing(p.parent / 'materials', SOURCE / f'coder-{side}/materials')
            symlink_if_missing(p.parent / 'shared-source', SOURCE / 'shared-source')
        rename_metadata(p, item['original_sheet_name'], item['sheet_name'])
        base = helper.inspect(ROOT / f'_build/frozen-coder-{side}.xlsx')
        book = helper.inspect(p)
        by_id = {r[f'{side}_blind_id']: r['source_id'] for r in mappings}
        actual = {}
        counts = collections.defaultdict(collections.Counter)
        for row in range(2, 1002):
            for col in 'ABC':
                assert base['values'].get(f'{col}{row}') == book['values'].get(f'{col}{row}'), (p, col, row)
            blind = book['values'][f'A{row}']
            dim = book['values'][f'C{row}']
            key = (by_id[blind], dim)
            expected = records[key]
            value = book['values'].get(f'D{row}')
            note = book['values'][f'E{row}']
            assert value == expected['human_value'], (p, key)
            assert note == expected['recorded_reason'], (p, key, 'reason')
            assert 'AI' not in note and 'AI填写' not in note
            assert note.startswith('待定：' if value is None else '真人复核')
            actual[key] = value
            counts[dim]['pending' if value is None else str(value)] += 1
        assert len(actual) == 1000
        if comparison is None:
            comparison = actual
        else:
            assert actual == comparison
        assert sum(c['pending'] for c in counts.values()) == 4
        assert sum(c['1'] for c in counts.values()) == 114
        assert sum(c['0'] for c in counts.values()) == 882
        assert book['values']['D1'] == '真人复核值\n（0/1）'
        assert book['values']['E1'] == '真人复核意见'
        for feature in ('links', 'validations', 'pane', 'formulas'):
            assert base[feature] == book[feature], (p, feature)
        assert all((p.parent / target).exists() for target in set(book['links'].values()))
        item['sha256'] = sha(p)
        checks.append({'path': str(p), 'key': item['key'], 'values_and_notes_verified': 1000, 'numeric': 996, 'pending': 4,
                       'dimensions': dict(counts), 'native_material_links_preserved': 1000, 'material_targets_exist': True,
                       'sha256': item['sha256']})
    original = json.loads((ROOT / '_build/workbook-verification.json').read_text())
    for check in original['checks']:
        p = ROOT / f'评审{check["side"]}' / f'AI独立盲评-{check["side"]}-200条.xlsx'
        assert sha(p) == check['workbook_sha256']
    versions['verified'] = True
    versions['original_AI_seals_unchanged'] = True
    versions['checks'] = checks
    (OUT / '真人复核版本记录.json').write_text(json.dumps(versions, ensure_ascii=False, indent=2))
    print(json.dumps({'status': 'passed', 'same_review_values_in_all_versions': True, 'checks': checks}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

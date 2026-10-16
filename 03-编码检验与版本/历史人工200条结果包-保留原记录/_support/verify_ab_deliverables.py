from pathlib import Path
import collections
import hashlib
import json
import posixpath
import re
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile

BASE = Path(__file__).resolve().parent.parent
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}


def workbook_rows(path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            shared = [''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        rels = {x.get('Id'): x.get('Target') for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheets = []
        for sh in wb.findall('s:sheets/s:sheet', NS):
            target = rels[sh.get('{'+REL+'}id')]
            location = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            xml = ET.fromstring(z.read(location))
            rows = []
            for row in xml.findall('s:sheetData/s:row', NS):
                values = {}
                for c in row:
                    value = c.find('s:v', NS)
                    inline = c.find('s:is', NS)
                    text = value.text if value is not None else ''.join(inline.itertext()) if inline is not None else ''
                    if c.get('t') == 's':
                        text = shared[int(text)]
                    values[re.sub(r'\d', '', c.get('r'))] = text
                rows.append((int(row.get('r')), values))
            relpath = posixpath.dirname(location)+'/_rels/'+posixpath.basename(location)+'.rels'
            links = {}
            if relpath in z.namelist():
                localrels = {x.get('Id'): x.get('Target') for x in ET.fromstring(z.read(relpath))}
                for link in xml.findall('s:hyperlinks/s:hyperlink', NS):
                    rid = link.get('{'+REL+'}id')
                    links[link.get('ref')] = localrels.get(rid, link.get('location'))
            sheets.append({'name': sh.get('name'), 'rows': rows, 'links': links})
        return sheets


data = json.loads((BASE/'真人核验结果.json').read_text())
labels = {x['A_id']: x['B_id'] for x in data['records']}
report = {'source': str(BASE/'真人核验结果.json'), 'files': {}, 'issues': []}
for side in 'AB':
    path = BASE/f'编码者{side}结果'/f'真人核验确认-{side}-200条.xlsx'
    if not path.exists():
        report['issues'].append(f'{side}: file missing')
        continue
    sheets = workbook_rows(path)
    issues = []
    main = next((s for s in sheets if sum(bool(re.fullmatch(side+r'-\d{3}', v.get('A', ''))) for _, v in s['rows']) >= 1000), None)
    if main is None:
        report['issues'].append(f'{side}: main sheet not found')
        continue
    rows = [(r,v) for r,v in main['rows'] if re.fullmatch(side+r'-\d{3}', v.get('A', ''))]
    expected = {(x[side+'_id'], d): j for x in data['records'] for d,j in x['judgments'].items()}
    seen = collections.Counter()
    positives = collections.Counter()
    links_checked = 0
    for rownum, row in rows:
        key = (row.get('A'), row.get('C'))
        seen[key] += 1
        if key not in expected:
            issues.append(f'unknown key {key}')
            continue
        item = expected[key]
        if row.get('D') != str(item['value']):
            issues.append(f'value mismatch {key}: {row.get("D")}')
        reason = item['reason']
        if side == 'B':
            reason = re.sub(r'A-\d{3}', lambda m: labels[m[0]], reason)
        if row.get('E') != reason:
            issues.append(f'reason mismatch {key}')
        if row.get('D') == '1':
            positives[row['C']] += 1
        link = main['links'].get('B'+str(rownum))
        if not link:
            issues.append(f'link absent {key}')
        else:
            resolved = path.parent/urllib.parse.unquote(link.split('#')[0])
            if not resolved.exists():
                issues.append(f'broken link {key}: {link}')
            elif resolved.stem != row['A']:
                issues.append(f'wrong material link {key}: {link}')
            links_checked += 1
    if set(seen) != set(expected) or len(rows) != 1000 or any(v != 1 for v in seen.values()):
        issues.append('1000 unique expected judgments not covered exactly once')
    if dict(positives) != data['positive_counts']:
        issues.append('positive counts mismatch')
    original = BASE.parent/'独立真人判读-200条-20261013'/f'发给编码者{side}'/f'独立判读-{side}-200条.xlsx'
    original_sheets = workbook_rows(original)
    original_main = next(s for s in original_sheets if sum(bool(re.fullmatch(side+r'-\d{3}', v.get('A', ''))) for _, v in s['rows']) >= 1000)
    original_sequence = [(v.get('A'), v.get('C')) for _,v in original_main['rows'] if re.fullmatch(side+r'-\d{3}', v.get('A', ''))]
    if [(v.get('A'),v.get('C')) for _,v in rows] != original_sequence:
        issues.append('original blind-ID/dimension row order changed')
    note = path.parent/'提交说明.txt'
    if not note.exists():
        issues.append('submission note missing')
    else:
        note_text = note.read_text()
        for phrase in ['用户本人', 'AI', '同一份', '两份不代表两位真人独立完成']:
            if phrase not in note_text:
                issues.append('submission note provenance missing '+phrase)
    alltext = '\n'.join(str(v) for s in sheets for _, r in s['rows'] for v in r.values())
    for phrase in ['真人', '用户本人', 'AI']:
        if phrase not in alltext:
            issues.append('provenance missing '+phrase)
    report['files'][side] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'sheets': [s['name'] for s in sheets], 'rows': len(rows), 'unique_judgments': len(seen), 'positive_counts': dict(positives), 'links_checked': links_checked, 'original_row_order_preserved': [(v.get('A'),v.get('C')) for _,v in rows] == original_sequence, 'submission_note_checked': note.exists(), 'issues': issues}
    report['issues'].extend(side+': '+i for i in issues)
pre = json.loads((BASE/'_support/A-B映射独立核验.json').read_text())
report['source_preservation'] = []
for p, before in pre['source_hashes'].items():
    path = Path(p)
    same = hashlib.sha256(path.read_bytes()).hexdigest() == before
    report['source_preservation'].append({'path': p, 'unchanged': same})
    if not same:
        report['issues'].append('source changed: '+p)
(BASE/'_support/A-B文件独立核验.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(bool(report['issues']))

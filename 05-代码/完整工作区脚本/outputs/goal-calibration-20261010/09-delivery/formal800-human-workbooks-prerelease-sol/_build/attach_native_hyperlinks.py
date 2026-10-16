"""Add the requested native hyperlink feature missing from the artifact calculation API."""
from pathlib import Path
import hashlib, json, zipfile, xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parents[1]
MAIN = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'
ET.register_namespace('', MAIN)
ET.register_namespace('r', REL)
manifest = json.loads((OUT / 'workbook-manifest.json').read_bytes())
pages = json.loads((OUT / 'material-pages-index.json').read_bytes())['pages']
for workbook in manifest['workbooks']:
    side = workbook['side']; target = Path(workbook['file']['absolute_path'])
    side_pages = [p for p in pages if p['side'] == side]
    assert len(side_pages) == 800
    with zipfile.ZipFile(target) as source:
        items = {name: source.read(name) for name in source.namelist()}
    sheet_path = 'xl/worksheets/sheet1.xml'
    rel_path = 'xl/worksheets/_rels/sheet1.xml.rels'
    sheet = ET.fromstring(items[sheet_path])
    relationships = ET.fromstring(items[rel_path]) if rel_path in items else ET.Element('{' + PKG + '}Relationships')
    previous = sheet.find('{' + MAIN + '}hyperlinks')
    if previous is not None:
        assert len(previous) == 4000
        sheet.remove(previous)
        for element in list(relationships):
            if element.attrib['Id'].startswith('rIdMaterial'): relationships.remove(element)
    used_ids = {r.attrib['Id'] for r in relationships}
    hyperlinks = ET.Element('{' + MAIN + '}hyperlinks')
    for n, page in enumerate(side_pages):
        blind = page['blind_id']; rid = 'rIdMaterial' + str(n + 1)
        assert rid not in used_ids
        ET.SubElement(relationships, '{' + PKG + '}Relationship', {
            'Id': rid, 'Type': REL + '/hyperlink',
            'Target': 'materials/' + blind + '.html', 'TargetMode': 'External'})
        for d in range(5):
            ET.SubElement(hyperlinks, '{' + MAIN + '}hyperlink', {'ref': 'A' + str(2 + n * 5 + d), '{' + REL + '}id': rid})
    after_links = {'printOptions', 'pageMargins', 'pageSetup', 'headerFooter', 'rowBreaks', 'colBreaks', 'customProperties', 'cellWatches', 'ignoredErrors', 'smartTags', 'drawing', 'legacyDrawing', 'legacyDrawingHF', 'picture', 'oleObjects', 'controls', 'webPublishItems', 'tableParts', 'extLst'}
    insert_at = next((i for i, element in enumerate(sheet) if element.tag.rsplit('}', 1)[-1] in after_links), len(sheet))
    sheet.insert(insert_at, hyperlinks)
    validations = sheet.find('{' + MAIN + '}dataValidations')
    assert validations is not None and len(validations) == 1
    validation = validations[0]
    assert validation.attrib['sqref'] == 'D2:D4001' and validation.attrib['type'] == 'list'
    validation.set('allowBlank', '1')
    validation.set('showErrorMessage', '1')
    validation.set('errorStyle', 'stop')
    validation.set('errorTitle', '仅填0或1')
    validation.set('error', '值仅能为0或1；证据不足请留空并填写理由。')
    items[sheet_path] = ET.tostring(sheet, encoding='utf-8', xml_declaration=True)
    items[rel_path] = ET.tostring(relationships, encoding='utf-8', xml_declaration=True)
    temporary = target.with_suffix('.hyperlink.tmp')
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as output:
        for name, raw in items.items(): output.writestr(name, raw)
    temporary.replace(target)
    raw = target.read_bytes()
    workbook['file'].update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    workbook['native_material_hyperlinks_N'] = 4000
(OUT / 'workbook-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print('Native material hyperlinks added: 2 workbooks, 4000 links each; source cells unchanged.')

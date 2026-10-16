"""Independent finite read-back of saved OOXML, literal HTML, source bytes and input seals."""
from pathlib import Path
from html.parser import HTMLParser
from collections import Counter
import hashlib, json, re, zipfile, xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[1]
SOURCE = ROOT / '05-validation/full800-common-v15-prerelease-sol'
MAIN = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = {'m': MAIN, 'r': REL}
DIMENSIONS = ['S', 'E', 'Ec', 'I', 'F']
H = lambda raw: hashlib.sha256(raw).hexdigest()
def parse(p): return json.loads(Path(p).read_bytes())
def bind(p):
    p = Path(p).resolve(); raw = p.read_bytes()
    return {'absolute_path': str(p), 'bytes': len(raw), 'sha256': H(raw)}
def strings(value, pointer=''):
    if isinstance(value, str): return {pointer: value}
    result = {}
    if isinstance(value, dict):
        for k, v in value.items(): result.update(strings(v, pointer + '/' + k.replace('~', '~0').replace('/', '~1')))
    elif isinstance(value, list):
        for i, v in enumerate(value): result.update(strings(v, pointer + '/' + str(i)))
    return result

class MaterialParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.literal = {}; self.special = {}; self.links = []; self.current = None; self.parts = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        assert tag not in {'script', 'iframe'}
        if tag == 'pre':
            self.current = ('pointer', attrs['data-json-pointer']) if 'data-json-pointer' in attrs else ('id', attrs.get('id'))
            self.parts = []
        if tag == 'a': self.links.append(attrs['href'])
        if tag == 'img': self.links.append(attrs['src'])
    def handle_data(self, data):
        if self.current is not None: self.parts.append(data)
    def handle_endtag(self, tag):
        if tag == 'pre':
            key_type, key = self.current; text = ''.join(self.parts)
            if key_type == 'pointer':
                assert key not in self.literal; self.literal[key] = text
            elif key is not None: self.special[key] = text
            self.current = None

source_seal = parse(SOURCE / 'seal.json')
manifest = parse(OUT / 'workbook-manifest.json')
assert bind(SOURCE / 'seal.json') == manifest['source_package_seal']
for entry in source_seal['members']:
    current = bind(entry['absolute_path'])
    assert current['sha256'] == entry['sha256'] and current['bytes'] == entry['bytes']
assert {e['path'] for e in source_seal['members']} == {str(p.relative_to(SOURCE)) for p in SOURCE.rglob('*') if p.is_file() and p.name != 'seal.json'}
for entry in manifest['input_bindings']: assert bind(entry['absolute_path']) == entry
asset_index = parse(OUT / 'shared-source/delivery-source-assets-index.json')
assert len(asset_index['files']) == 158
for entry in asset_index['files']:
    actual = bind(OUT / entry['prepared_relative_path'])
    assert actual['absolute_path'] == entry['prepared_absolute_path'] and actual['sha256'] == entry['sha256'] and actual['bytes'] == entry['bytes']
pages = parse(OUT / 'material-pages-index.json')['pages']
assert len(pages) == 1600 and len({(p['side'], p['blind_id']) for p in pages}) == 1600
checks = {'version': 'formal800-human-workbooks-v15-prerelease-1', 'workbook_N': 2,
    'source_seal_and_all_members_unchanged': True, 'source_members_unchanged_N': len(source_seal['members']),
    'bound_inputs_unchanged_N': len(manifest['input_bindings']), 'shared_assets_accessible_same_SHA_N': 158,
    'human_or_AI_labels_created_N': 0, 'human_review_columns_added_N': 0,
    'final_release_freeze_completed': False, 'native_Excel_click_test_performed': False, 'sides': []}
blank_slots = 0; pages_opened = 0; text_fields = 0; links_opened = 0
for wb in manifest['workbooks']:
    side = wb['side']; workbook_path = Path(wb['file']['absolute_path'])
    assert bind(workbook_path) == wb['file']
    packets = [json.loads(line) for line in (SOURCE / ('coder-' + side) / 'packet.jsonl').open('rb')]
    assert len(packets) == 800 and len({p['blind_id'] for p in packets}) == 800
    with zipfile.ZipFile(workbook_path) as z:
        root = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = root.find('m:sheets', NS)
        assert len(sheets) == 1 and sheets[0].attrib['name'] == '初判-pre-release'
        assert sheets[0].attrib.get('state', 'visible') == 'visible'
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            for si in ET.fromstring(z.read('xl/sharedStrings.xml')):
                shared.append(''.join(t.text or '' for t in si.iter('{' + MAIN + '}t')))
        sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        cells = {c.attrib['r']: c for c in sheet.findall('m:sheetData/m:row/m:c', NS)}
        assert all(re.match(r'^[A-E][0-9]+$', address) for address in cells)
        assert len(sheet.findall('m:sheetData/m:row', NS)) == 4001
        def cell_value(address):
            cell = cells.get(address)
            if cell is None: return None
            assert cell.find('m:f', NS) is None, 'No spreadsheet formulas or hidden predictions permitted'
            if cell.attrib.get('t') == 'inlineStr': return ''.join(t.text or '' for t in cell.iter('{' + MAIN + '}t'))
            value = cell.find('m:v', NS)
            if value is None or value.text is None: return None
            return shared[int(value.text)] if cell.attrib.get('t') == 's' else value.text
        assert [cell_value(c + '1') for c in 'ABCDE'] == ['盲号（打开完整材料）', '条款正文', '维度', '值（0/1）', '理由（待定原因/补材）']
        seen = Counter()
        for n, packet in enumerate(packets):
            for d, dimension in enumerate(DIMENSIONS):
                row = 2 + n * 5 + d
                assert cell_value('A' + str(row)) == packet['blind_id']
                assert cell_value('B' + str(row)) == packet['source_bundle']['source_record']['text']
                assert cell_value('C' + str(row)) == dimension
                assert cell_value('D' + str(row)) is None and cell_value('E' + str(row)) is None
                seen[packet['blind_id']] += 1; blank_slots += 1
        assert len(seen) == 800 and set(seen.values()) == {5}
        pane = sheet.find('m:sheetViews/m:sheetView/m:pane', NS)
        assert pane is not None and float(pane.attrib['ySplit']) == 1 and pane.attrib['state'] == 'frozen'
        assert pane.attrib['topLeftCell'] == 'B2'
        validations = sheet.find('m:dataValidations', NS)
        assert validations is not None and len(validations) == 1
        validation = validations[0]
        assert validation.attrib['sqref'] == 'D2:D4001' and validation.attrib['type'] == 'list'
        assert validation.find('m:formula1', NS).text == '"0,1"'
        assert validation.attrib['allowBlank'] == '1' and validation.attrib['showErrorMessage'] == '1' and validation.attrib['errorStyle'] == 'stop'
        relationships = {r.attrib['Id']: r.attrib for r in ET.fromstring(z.read('xl/worksheets/_rels/sheet1.xml.rels'))}
        hyperlinks = sheet.find('m:hyperlinks', NS)
        assert hyperlinks is not None and len(hyperlinks) == 4000
        assert {h.attrib['ref'] for h in hyperlinks} == {'A' + str(n) for n in range(2, 4002)}
        for link in hyperlinks:
            row = int(link.attrib['ref'][1:]); relationship = relationships[link.attrib['{' + REL + '}id']]
            expected = 'materials/' + packets[(row - 2) // 5]['blind_id'] + '.html'
            assert relationship['Target'] == expected and relationship['TargetMode'] == 'External'
            assert (workbook_path.parent / relationship['Target']).is_file()
    side_pages = [p for p in pages if p['side'] == side]
    assert [p['blind_id'] for p in side_pages] == [p['blind_id'] for p in packets]
    for record, packet in zip(side_pages, packets):
        raw = (OUT / record['json_relative_path']).read_bytes()
        assert H(raw) == packet['source_bundle_canonical_sha256'] and len(raw) == packet['source_bundle_canonical_UTF8_bytes']
        assert json.loads(raw) == packet['source_bundle']
        page = OUT / record['html_relative_path']; reader = MaterialParser(); reader.feed(page.read_text()); reader.close()
        assert reader.literal == strings(packet['source_bundle'])
        assert reader.special['current-body'] == packet['source_bundle']['source_record']['text']
        assert reader.special['bundle-original'].encode() == raw
        for relative in reader.links:
            assert not re.match(r'^[a-zA-Z]+:', relative)
            linked = (page.parent / relative).resolve()
            assert linked.is_file()
            with linked.open('rb') as handle: handle.read(1)
            links_opened += 1
        pages_opened += 1; text_fields += len(reader.literal)
    assert bind(OUT / ('coder-' + side) / 'manual.txt')['sha256'] == wb['manual']['sha256']
    checks['sides'].append({'side': side, 'rows_N': 4000, 'unique_blind_N': 800, 'five_dimensions_per_blind': True,
        'original_packet_order_and_blind_IDs_preserved': True, 'current_body_cell_bytes_exact': True,
        'D_E_all_genuinely_empty': True, 'native_material_hyperlinks_N': 4000, 'material_pages_opened_N': 800,
        'all_source_string_values_displayed_literal_without_deletion': True,
        'raw_source_JSON_SHA_and_bytes_exact': True, 'frozen_header_and_0_1_validation_verified_in_saved_OOXML': True,
        'additional_columns_N': 0, 'candidate_manual_bytes_exact': True})
assert blank_slots == 8000 and pages_opened == 1600
checks.update(blank_dimension_input_slots_N=blank_slots, blank_reason_slots_N=blank_slots,
    all_material_pages_opened_N=pages_opened, all_literal_source_string_fields_compared_N=text_fields,
    local_material_and_asset_links_opened_N=links_opened, release_status='pre_release_not_formally_distributed')
(OUT / 'mechanical-readback.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: checks[k] for k in ['workbook_N', 'blank_dimension_input_slots_N', 'blank_reason_slots_N',
    'all_material_pages_opened_N', 'all_literal_source_string_fields_compared_N', 'local_material_and_asset_links_opened_N',
    'source_members_unchanged_N', 'bound_inputs_unchanged_N', 'final_release_freeze_completed']}, ensure_ascii=False))

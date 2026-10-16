from pathlib import Path
from zipfile import ZipFile
from lxml import etree as ET
import hashlib
import json
import re

BASE = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
SOURCE = BASE / 'outputs/编码修订核查-20261008/本轮结果/创新药评价的注意力配置差异与协调路径.docx'
OUTDIR = Path(__file__).resolve().parent
OUTPUT = OUTDIR / '创新药评价的注意力配置差异与协调路径-原稿格式修订.docx'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
SOURCE_SHA = '2335ad123737735ea5ae32234de323d3c7ae1ac0c23136d4d2eb7a2742b15db6'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
with ZipFile(SOURCE) as z:
    infos = z.infolist()
    package = {i.filename: z.read(i.filename) for i in infos}
root = ET.fromstring(package['word/document.xml'])
paragraphs = root.findall('w:body/w:p', NS)
tables = root.findall('w:body/w:tbl', NS)
assert len(paragraphs) == 181 and len(tables) == 4

def text(element):
    return ''.join(element.xpath('.//w:t/text()', namespaces=NS))

original_paragraphs = [text(p) for p in paragraphs]
changes = []

def replace_exact(element, old, new):
    """Replace an exact span without flattening runs or touching run properties."""
    starts = [m.start() for m in re.finditer(re.escape(old), text(element))]
    for start in reversed(starts):
        end = start + len(old)
        nodes = element.xpath('.//w:t', namespaces=NS)
        cursor = 0
        parts = []
        for node in nodes:
            value = node.text or ''
            parts.append((node, cursor, cursor + len(value), value))
            cursor += len(value)
        affected = [(node, a, b, v) for node, a, b, v in parts if a < end and b > start]
        assert affected
        for j, (node, a, b, value) in enumerate(affected):
            left = value[:max(0, start-a)]
            right = value[max(0, end-a):] if end < b else ''
            node.text = left + (new if j == 0 else '') + right
            if node.text.startswith(' ') or node.text.endswith(' '):
                node.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

def patch(number, pairs, kind):
    element = paragraphs[number-1]
    before = text(element)
    for old, new in pairs:
        assert old in text(element), (number, old)
        replace_exact(element, old, new)
    changes.append({'location': f'P{number:03d}', 'kind': kind, 'before': before, 'after': text(element)})

agency = [('药监', '药监局'), ('医保', '医保局'), ('卫健', '卫健委')]
for number in [2, 48, 50, 61, 67, 72, 73, 76, 77, 83, 90, 106, 113]:
    patch(number, [(a, b) for a, b in agency if a in text(paragraphs[number-1])], '部门称谓')
patch(23, [('医保与卫健', '医保局与卫健委')], '部门称谓')
patch(44, [('药品监管、医保和卫生健康系统', '药品监管、医疗保障和卫生健康系统'),
           ('药监17、医保24、卫健10', '药监局17、医保局24、卫健委10')], '部门称谓')
patch(51, [('卫健层', '卫健委层')], '部门称谓')
patch(63, [('医保调研纪要', '医保局调研纪要'), ('药监环节', '药品监管环节')], '部门称谓')
patch(81, [('药监', '药监局')], '部门称谓')
patch(82, [('医保经济性内容', '医保局经济性内容'), ('卫健《管理指南》', '卫健委《管理指南》')], '部门称谓')
patch(86, [('医保申报要求', '医保局的申报要求'), ('医保调研纪要', '医保局调研纪要')], '部门称谓')
patch(87, [('医保《申报指南》', '医保局《申报指南》')], '部门称谓')
patch(88, [('药监的', '药监局的'), ('医保的', '医保局的'), ('卫健的', '卫健委的'), ('医保调研纪要', '医保局调研纪要')], '部门称谓')
patch(91, [('医保申报引用', '医保局的申报要求引用'), ('卫健将', '卫健委将')], '部门称谓')
patch(96, [('药监审评报告', '药监局审评报告')], '部门称谓')
patch(97, [('医保申报指南', '医保局申报指南'), ('医保部门', '医保局'), ('药监部门', '药监局')], '部门称谓')
patch(99, [('药监侧重', '药监局侧重'), ('医保侧重', '医保局侧重'), ('卫健侧重', '卫健委侧重')], '部门称谓')
patch(100, [('试点地区医保部门', '试点地区医疗保障部门')], '部门称谓')
patch(101, [('2026年医保官方解读', '2026年医保局官方解读')], '部门称谓')
patch(103, [('医保经济性注意力', '医保局经济性注意力'), ('卫健经济性单元', '卫健委经济性单元'),
            ('省级卫健部门', '省级卫生健康部门'), ('医保部门', '医疗保障部门')], '部门称谓')

for number, pairs in {
    17: [('王恩楠和朱铭来', '王恩楠等'), ('毛心仪和姚峥嵘', '毛心仪等')],
    20: [('Mountford和Cai', 'Mountford等')],
    27: [('Thornton和Ocasio', 'Thornton等')],
    28: [('陶鹏和初春', '陶鹏等')],
    47: [('Halterman和Keith', 'Halterman等')],
    52: [('Halterman和Keith', 'Halterman等')],
    57: [('[28,29]', '[28-29]')],
    80: [('[36,39,40]', '[36,39-40]')],
    88: [('[35,36,37]', '[35-37]')],
}.items():
    patch(number, pairs, '投稿模板引文格式')

# Move citation [46] next to Cohen while preserving its original superscript run.
p = paragraphs[50]
before = text(p)
runs = p.findall('w:r', NS)
assert text(runs[2]) == '，以Cohen的κ' and text(runs[3]) == '[46]'
assert runs[3].find('w:rPr/w:vertAlign', NS).get('{'+NS['w']+'}val') == 'superscript'
replace_exact(runs[2], '，以Cohen的κ', '，以Cohen')
first_text = runs[4].find('w:t', NS)
first_text.text = '的κ' + first_text.text
changes.append({'location': 'P051', 'kind': '编号紧随作者且保持上标', 'before': before, 'after': text(p)})

for table_index, table in enumerate(tables, 1):
    if table_index not in [3, 4]:
        continue
    for row_index, row in enumerate(table.findall('w:tr', NS), 1):
        for col_index, cell in enumerate(row.findall('w:tc', NS), 1):
            before = text(cell)
            mapping = dict(agency)
            if before in mapping:
                replace_exact(cell, before, mapping[before])
                changes.append({'location': f'T{table_index}R{row_index}C{col_index}', 'kind': '部门称谓', 'before': before, 'after': text(cell)})

# Correct only the four confirmed direct/inherited font-size discrepancies.
for number, half_points, prior in [(2, 21, '12 pt'), (7, 21, '12 pt'),
                                  (75, 24, 'inherited 10.5 pt'), (84, 24, 'inherited 10.5 pt')]:
    p = paragraphs[number-1]
    for run in p.findall('w:r', NS):
        if not text(run):
            continue
        props = run.find('w:rPr', NS)
        if props is None:
            props = ET.Element('{'+NS['w']+'}rPr')
            run.insert(0, props)
        for property_name in ['sz', 'szCs']:
            node = props.find('w:'+property_name, NS)
            if node is None:
                node = ET.SubElement(props, '{'+NS['w']+'}'+property_name)
            node.set('{'+NS['w']+'}val', str(half_points))
    changes.append({'location': f'P{number:03d}', 'kind': '投稿模板字号校准',
                    'before': prior, 'after': f'{half_points / 2:g} pt',
                    'paragraph_text_unchanged': True})

# Compact the short numeric rows slightly so the table note stays with Table 2.
for row_index, row in enumerate(tables[1].findall('w:tr', NS), 1):
    for p in row.findall('.//w:p', NS):
        props = p.find('w:pPr', NS)
        spacing = props.find('w:spacing', NS)
        assert spacing.get('{'+NS['w']+'}line') == '264'
        spacing.set('{'+NS['w']+'}line', '240')
        if row_index == 11:
            props.find('w:keepNext', NS).set('{'+NS['w']+'}val', '1')
changes.append({'location': '表2分页', 'kind': '保留字号，行距由1.1倍调为单倍，末行与表注同页', 'before': '264 auto', 'after': '240 auto; last row keepNext=1'})

# Replace the existing data plot only; no changes to its source values or dimensions.
figure = OUTDIR / 'figure2-department-names.png'
assert figure.exists()
figure_check = json.loads((OUTDIR / 'figure2-department-names.json').read_text())
package['word/media/image4.png'] = figure.read_bytes()
figure_inlines = root.xpath('.//wp:inline[.//a:blip[@r:embed="rId4"]]', namespaces=NS)
assert len(figure_inlines) == 1
for inline in figure_inlines:
    prop = inline.find('wp:docPr', NS)
    before = prop.get('descr')
    prop.set('descr', '三部门五维注意力占比对照图。上图为自动规则编码，下图为LLM编码。各部门分别显示安全性、有效性、经济性、创新性和公平性的注意力占比，与表3对应。')
    changes.append({'location': '图2替代文字', 'kind': '移除与原图不符的四来源及固定580项说明', 'before': before, 'after': prop.get('descr')})
    extent = inline.find('wp:extent', NS)
    old_extent = dict(extent.attrib)
    width, height = figure_check['dimensions_px']
    cy = str(round(int(extent.get('cx')) * height / width))
    extent.set('cy', cy)
    for image_extent in inline.xpath('.//a:xfrm/a:ext', namespaces=NS):
        image_extent.set('cy', cy)
    changes.append({'location': '图2画布', 'kind': '保持宽度和字号，减少图内纵向空隙以与前文同页', 'before': old_extent, 'after': dict(extent.attrib)})

changed_ids = {int(c['location'][1:]) for c in changes if re.fullmatch(r'P\d+', c['location'])}
for i, (old, p) in enumerate(zip(original_paragraphs, paragraphs), 1):
    if i not in changed_ids:
        assert old == text(p)
# Original references, theory figure, numeric content and all untouched package parts are preserved.
assert original_paragraphs[114:] == [text(p) for p in paragraphs[114:]]
def citation_numbers(s):
    values = []
    for group in re.findall(r'\[([\d,\-]+)\]', s):
        if not all(re.fullmatch(r'\d+(?:-\d+)?', piece) for piece in group.split(',')):
            continue  # Bibliography access dates such as [2026-07-21] are not citation groups.
        group_values = []
        for piece in group.split(','):
            if '-' in piece:
                a, b = map(int, piece.split('-')); group_values.extend(range(a, b+1))
            else: group_values.append(int(piece))
        values.append(group_values)
    return values
assert citation_numbers(''.join(original_paragraphs)) == citation_numbers(''.join(text(p) for p in paragraphs))
def noncitation_numbers(s):
    return re.findall(r'\d+(?:\.\d+)?', re.sub(r'\[[\d,\-]+\]', '', s))
assert noncitation_numbers(''.join(original_paragraphs)) == noncitation_numbers(''.join(text(p) for p in paragraphs))
package['word/document.xml'] = ET.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
with ZipFile(OUTPUT, 'w') as z:
    for info in infos:
        z.writestr(info, package[info.filename])
with ZipFile(SOURCE) as original, ZipFile(OUTPUT) as result:
    changed_parts = [name for name in original.namelist() if original.read(name) != result.read(name)]
    assert set(changed_parts) == {'word/document.xml', 'word/media/image4.png'}
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
record = {
    'source': str(SOURCE), 'source_sha256': SOURCE_SHA,
    'output': str(OUTPUT), 'output_sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    'status': 'working_copy_awaiting_visual_review_and_final_statistics',
    'source_original_preserved': True,
    'theoretical_argument_preserved': True,
    'all_66_original_references_preserved': True,
    'all_original_numerical_tokens_preserved': True,
    'original_figure1_preserved': True,
    'citation_years_not_added': True,
    'formal_validation_complete': False,
    'final_statistics_adopted': False,
    'changed_package_parts': changed_parts,
    'changes': changes,
}
(OUTDIR / 'local-format-edit-record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'output': str(OUTPUT), 'changes': len(changes), 'changed_parts': changed_parts}, ensure_ascii=False))

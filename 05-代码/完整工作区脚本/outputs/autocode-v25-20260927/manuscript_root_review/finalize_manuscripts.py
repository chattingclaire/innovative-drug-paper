"""Bounded final text and pagination edits; immutable pre-edit snapshots."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import datetime
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
WORK = Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区/重跑修订稿-20260927')
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'
BACKUP = HERE / '视觉收尾前快照'
BACKUP.mkdir(exist_ok=True)
replacements = {
    '但较高覆盖不能直接解释为更准确': '但较高阳性比例不能直接解释为更准确',
    'LLM按每批10条、共493批': 'LLM按每批最多10条、共493批',
}
records = []
for filename in ('论文修订稿-匿名审稿版.docx', '论文修订稿-署名版.docx'):
    source = WORK / filename
    snapshot = BACKUP / filename
    assert not snapshot.exists(), 'Do not overwrite the pre-edit snapshot'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    with ZipFile(source) as z:
        infos = z.infolist()
        entries = {info.filename: z.read(info.filename) for info in infos}
    root = etree.fromstring(entries['word/document.xml'])
    for old, new in replacements.items():
        matches = [node for node in root.findall('.//w:t', NS) if old in (node.text or '')]
        assert len(matches) == 1, (filename, old, len(matches))
        matches[0].text = matches[0].text.replace(old, new)
    table = root.findall('.//w:body/w:tbl', NS)[1]
    rows = table.findall('w:tr', NS)
    assert len(rows) == 11
    assert ''.join(rows[9].xpath('.//w:t/text()', namespaces=NS)).startswith('公平性规则')
    assert ''.join(rows[10].xpath('.//w:t/text()', namespaces=NS)).startswith('公平性LLM')
    for paragraph in rows[9].findall('.//w:p', NS):
        props = paragraph.find('w:pPr', NS)
        if props is None:
            props = etree.Element(W + 'pPr')
            paragraph.insert(0, props)
        keep = props.find('w:keepNext', NS)
        if keep is None:
            keep = etree.SubElement(props, W + 'keepNext')
        keep.set(W + 'val', '1')
    entries['word/document.xml'] = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
    shutil.copy2(source, snapshot)
    temp = source.with_suffix('.new.docx')
    with ZipFile(temp, 'w') as z:
        for info in infos:
            z.writestr(info, entries[info.filename])
    with ZipFile(snapshot) as old_zip, ZipFile(temp) as new_zip:
        changed = [name for name in old_zip.namelist() if old_zip.read(name) != new_zip.read(name)]
        assert changed == ['word/document.xml'], changed
    temp.replace(source)
    records.append({'path': str(source), 'snapshot': str(snapshot), 'before_sha256': before,
                    'after_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                    'changed_package_members': changed})
report = {'time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'text_replacements': replacements, 'pagination': 'Keep the paired fairness rows in Table 2 together',
          'outputs': records}
(HERE / '最终措辞与分页修订记录.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))

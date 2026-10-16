from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
from lxml import etree as E
import re, json, hashlib, shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = HERE.parent / 'journal-style-preparation'
SOURCE = BASE / '科学决策排版底稿.docx'
EXPECTED = '3a6781cf2be5ecdb7682400e0ba8530a6d83918e691087e8dcc7820562f6b545'
OUT = HERE / '创新药论文正文初稿-第一至三章.docx'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
assert not OUT.exists()
shutil.copyfile(SOURCE, HERE / 'retained-style-reference.docx')
shutil.copyfile(BASE / 'artifact.md', HERE / 'style-source-contract.md')
shutil.copyfile(SOURCE, OUT)
with ZipFile(SOURCE) as z:
    parts = {i.filename: z.read(i.filename) for i in z.infolist()}
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
def q(t): return '{' + W + '}' + t
def el(t, **kw): return E.Element(q(t), {q(k): str(v) for k,v in kw.items()})
root = E.fromstring(parts['word/document.xml'])
body = root.find(q('body'))
section = deepcopy(body.find(q('sectPr')))
table_source = deepcopy(body.find(q('tbl')))
styles = E.fromstring(parts['word/styles.xml'])
sty = {s.find(q('name')).get(q('val')): s.get(q('styleId')) for s in styles.findall(q('style')) if s.find(q('name')) is not None}
for child in list(body): body.remove(child)
source = (HERE / 'intro-framework.md').read_text() + '\n\n' + (HERE / 'methods.md').read_text()
source = re.sub(r'^## 3 ', '# 3 ', source, flags=re.M)
source = re.sub(r'^### (3\.)', r'## \1', source, flags=re.M)
rx = re.compile(r'\[((?:R\d{3})|(?:N-[A-Z0-9]+))\]')
keys = list(dict.fromkeys(rx.findall(source)))
numbers = {k:i+1 for i,k in enumerate(keys)}
refplan = json.loads((ROOT / 'parallel-manuscript/reference-plan/core-reference-coverage.json').read_text())
refs = {x['id']: x['source']['bibliography'] for group in ['core_references', 'conditional_references'] for x in refplan[group]}
assert all(k in refs for k in keys)

def paragraph(text, role='Normal', parent=body, cite=True):
    p = el('p'); pp=el('pPr'); pp.append(el('pStyle', val=sty[role])); p.append(pp)
    pieces = re.split(r'(\[(?:R\d{3}|N-[A-Z0-9]+)\])', text) if cite else [text]
    prev = ''
    for piece in pieces:
        if not piece: continue
        r=el('r'); m=rx.fullmatch(piece)
        if m:
            if not prev.endswith(('等','Cohen','Mossialos')):
                rp=el('rPr'); rp.append(el('vertAlign', val='superscript')); r.append(rp)
            piece='['+str(numbers[m.group(1)])+']'
        t=el('t'); t.text=piece; t.set('{http://www.w3.org/XML/1998/namespace}space','preserve'); r.append(t); p.append(r); prev=piece
    parent.append(p); return p

paragraph('创新药评价的注意力配置差异与协调路径','Title')
paragraph('正文初稿 第一至三章','中文作者单位')
lines = source.splitlines(); i=0
while i<len(lines):
    line=lines[i].strip(); i+=1
    if not line: continue
    if line.startswith('|'):
        rows=[line]
        while i<len(lines) and lines[i].strip().startswith('|'):
            rows.append(lines[i].strip());i+=1
        rows=[r for r in rows if not re.match(r'^\|\s*[-:]+',r)]
        table=deepcopy(table_source)
        source_rows=table.findall(q('tr'))
        for tr in source_rows:table.remove(tr)
        for j,row in enumerate(rows):
            tr=deepcopy(source_rows[0 if j==0 else 1]); cells=tr.findall(q('tc'))
            texts=[x.strip() for x in row.strip('|').split('|')]
            for k,(tc,text) in enumerate(zip(cells,texts)):
                for old in list(tc):
                    if old.tag!=q('tcPr'):tc.remove(old)
                paragraph(text,'三线表表头' if j==0 else ('三线表短项' if k==0 else '三线表内容'),tc)
            table.append(tr)
        body.append(table);continue
    if line.startswith('# '):paragraph(line[2:],'一级标题')
    elif line.startswith('## '):paragraph(line[3:],'二级标题')
    elif line.startswith('表1 '):paragraph(line,'三线表题')
    else:paragraph(line)
paragraph('参考文献','参考文献标题')
for key in keys:paragraph('['+str(numbers[key])+'] '+refs[key],'参考文献正文',cite=False)
body.append(section)
parts['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
    for name,data in parts.items():z.writestr(name,data)
with ZipFile(SOURCE) as a, ZipFile(OUT) as b:
    assert set(a.namelist())==set(b.namelist())
    changed=[n for n in a.namelist() if a.read(n)!=b.read(n)]
    assert changed==['word/document.xml'],changed
    ar=E.fromstring(a.read('word/document.xml'))
    br=E.fromstring(b.read('word/document.xml'))
    assert E.tostring(ar.find('w:body/w:sectPr',NS))==E.tostring(br.find('w:body/w:sectPr',NS))
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
numbered=rx.sub(lambda m:'['+str(numbers[m.group(1)])+']',source)
(HERE/'正文初稿-第一至三章.md').write_text('# 创新药评价的注意力配置差异与协调路径\n\n'+numbered+'\n\n# 参考文献\n\n'+'\n\n'.join('['+str(numbers[k])+'] '+refs[k] for k in keys)+'\n')
record={'status':'provisional_chapters_1_to_3_not_final_submission','reference_sha256':EXPECTED,'document_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'changed_package_parts':changed,'preserved_package_parts_count':len(parts)-1,'reference_count':len(keys),'citation_key_to_number':numbers,'chinese_character_count_without_references':len(re.findall(r'[\u4e00-\u9fff]',source)),'formal_validation_complete':False,'final_manuscript_complete':False,'render_verified':False}
(HERE/'build-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
(HERE/'artifact.md').write_text('''# 前三章正文初稿版式约定

参考为本目录 retained-style-reference.docx，SHA256 '''+EXPECTED+'''，原始来源为 ../journal-style-preparation/科学决策排版底稿.docx。该来源已完成2页逐页检查；页面、样式、字体、三线表及包清单详见同目录 style-source-contract.md。

本稿复用已审定期刊样式，仅替换 word/document.xml 的正文内容槽。保留一个A4节和全部页边距、主题、字体表、编号及样式包。保留 Title、正文、一级二级标题、三线表和参考文献角色；删除底稿示例及不适用于前三章初稿的作者、摘要、英文前言、结语槽，新增初稿范围副题。没有作者、基金、DOI虚构字段。表格沿用原三线表结构及尺寸。所有非正文包成员均须逐字相同。

正文范围为引言、文献与分析框架、研究设计。尚未完成的独立验证和稳定性在方法中标明状态。此稿不含发现、讨论、结语与最终摘要，不能作为完整投稿稿；已完成全量数据不重跑。原采用稿保持不动。

按首次引用重排来源编号，源键映射留在build-record.json。字体按宋体、黑体、Times New Roman设置，本机预览沿用已有render-fonts.conf替代；该限制与原版式底稿一致。交付前须检查全部页图，检查表格续页、标题孤立、缺字及裁切，并记录检查结果。
''')
print(json.dumps(record,ensure_ascii=False))

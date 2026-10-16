#!/usr/bin/env python3
"""Build only an editable journal style base from the retained official DOCX.

No manuscript, result, machine prediction, or reference-plan file is read.
The package is patched directly so preserve-only parts stay byte-identical.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
from pathlib import Path
from zipfile import ZipFile

from lxml import etree as E

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'official-current-template.docx'
SOURCE_SHA = '9d53ceb26f2f3b869edf09c4ce260af1ba1dd39971a543f21a565c3b8014a7e3'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
NS = {'w': W}
PRESERVE = ('word/fontTable.xml', 'word/numbering.xml', 'word/theme/theme1.xml')


def q(name):
    return '{' + W + '}' + name


def el(tag, **attrs):
    return E.Element(q(tag), {q(k): str(v) for k, v in attrs.items()})


def xml(root):
    return E.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)


def font(east='宋体', size=24, bold=False):
    rp = el('rPr')
    rp.append(el('rFonts', ascii='Times New Roman', hAnsi='Times New Roman',
                 eastAsia=east, cs='Times New Roman'))
    rp.append(el('b', val='1' if bold else '0'))
    rp.append(el('color', val='000000'))
    rp.append(el('sz', val=size))
    rp.append(el('szCs', val=size))
    rp.append(el('lang', val='en-US', eastAsia='zh-CN'))
    return rp


def pformat(align='left', first=0, left=0, before=0, after=0,
            line=360, keep=False, outline=None, hanging=0):
    pp = el('pPr')
    pp.append(el('keepNext', val='1' if keep else '0'))
    pp.append(el('keepLines', val='1'))
    pp.append(el('widowControl', val='1'))
    pp.append(el('snapToGrid', val='0'))
    pp.append(el('spacing', before=before, after=after, line=line, lineRule='auto'))
    ind = el('ind', left=left, right=0)
    if hanging:
        ind.set(q('hanging'), str(hanging))
    else:
        ind.set(q('firstLine'), str(first))
    pp.append(ind)
    pp.append(el('jc', val=align))
    if outline is not None:
        pp.append(el('outlineLvl', val=outline))
    return pp


def set_style(styles, name, east='宋体', size=24, bold=False, **fmt):
    st = next((x for x in styles.findall(q('style'))
               if x.find(q('name')) is not None and x.find(q('name')).get(q('val')) == name), None)
    if st is None:
        st = el('style', type='paragraph', customStyle=1, styleId='KSJ' + str(len(styles)))
        st.append(el('name', val=name))
        st.append(el('basedOn', val='1'))
        st.append(el('qFormat'))
        styles.append(st)
    for tag in ('pPr', 'rPr', 'link'):
        for node in list(st.findall(q(tag))):
            st.remove(node)
    st.append(pformat(**fmt))
    st.append(font(east, size, bold))
    return st.get(q('styleId'))


class Content:
    def __init__(self, body, roles):
        self.body, self.roles, self.next_id = body, roles, 1

    def paragraph(self, role, text, slot=None, page_break=False, parent=None):
        p = el('p')
        pp = el('pPr')
        pp.append(el('pStyle', val=self.roles[role]))
        if page_break:
            pp.append(el('pageBreakBefore'))
        p.append(pp)
        if slot:
            p.append(el('bookmarkStart', id=self.next_id, name='KSJ_' + slot))
        r = el('r')
        t = el('t')
        t.text = text
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        r.append(t)
        p.append(r)
        if slot:
            p.append(el('bookmarkEnd', id=self.next_id))
            self.next_id += 1
        (self.body if parent is None else parent).append(p)
        return p

    def table(self):
        table = el('tbl')
        pr = el('tblPr')
        pr.append(el('tblW', w=10466, type='dxa'))
        pr.append(el('jc', val='center'))
        borders = el('tblBorders')
        for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            borders.append(el(side, val='single' if side in ('top', 'bottom') else 'nil',
                              sz=8 if side in ('top', 'bottom') else 0, color='000000'))
        pr.append(borders)
        pr.append(el('tblLayout', type='fixed'))
        margins = el('tblCellMar')
        for side in ('top', 'left', 'bottom', 'right'):
            margins.append(el(side, w=70 if side in ('top', 'bottom') else 100, type='dxa'))
        pr.append(margins)
        table.append(pr)
        widths = (2000, 4053, 4413)
        grid = el('tblGrid')
        for width in widths:
            grid.append(el('gridCol', w=width))
        table.append(grid)
        rows = [
            ('样式示例', '字段示例', '排版示例说明'),
            ('文字项', '【填写字段名称】', '中文宋体五号，内容按需换行'),
            ('数值项', '【验收后填入数值】', '精度统一；此处不预填研究结果'),
            ('缺失说明', '【填入适用标记】', '在表下注明 NA 等标记的含义'),
        ]
        for i, row in enumerate(rows):
            tr = el('tr')
            trpr = el('trPr')
            trpr.append(el('cantSplit'))
            if i == 0:
                trpr.append(el('tblHeader'))
            tr.append(trpr)
            for j, text in enumerate(row):
                tc = el('tc')
                cp = el('tcPr')
                cp.append(el('tcW', w=widths[j], type='dxa'))
                cp.append(el('vAlign', val='center'))
                if i == 0:
                    cb = el('tcBorders')
                    cb.append(el('bottom', val='single', sz=4, color='000000'))
                    cp.append(cb)
                tc.append(cp)
                self.paragraph('table_head' if i == 0 else ('table_center' if j == 0 else 'table'), text, parent=tc)
                tr.append(tc)
            table.append(tr)
        self.body.append(table)


def build(output, replace=False):
    if output.resolve() == SOURCE.resolve():
        raise ValueError('Cannot overwrite the retained official template')
    if output.exists() and not replace:
        raise FileExistsError('Output exists; choose a new path or use --replace')
    original = SOURCE.read_bytes()
    assert hashlib.sha256(original).hexdigest() == SOURCE_SHA, 'Source template SHA mismatch'
    with ZipFile(SOURCE) as z:
        parts = {n: z.read(n) for n in z.namelist() if not n.endswith('/')}
    doc = E.fromstring(parts['word/document.xml'])
    body = doc.find(q('body'))
    section = deepcopy(body.find(q('sectPr')))
    geometry = {k: dict(section.find(q(k)).attrib) for k in ('pgSz', 'pgMar', 'cols')}
    for node in list(section):
        if E.QName(node).localname in ('headerReference', 'footerReference', 'titlePg', 'endnotePr'):
            section.remove(node)
    for node in list(body):
        body.remove(node)
    styles = E.fromstring(parts['word/styles.xml'])
    roles = {}
    roles['body'] = set_style(styles, 'Normal', first=480, align='both')
    roles['title'] = set_style(styles, 'Title', east='黑体', size=28, align='center', after=120, keep=True)
    # The retained journal's dedicated title style is also available for later reuse.
    set_style(styles, '中文标题', east='黑体', size=28, align='center', after=120, keep=True)
    roles['title_en'] = set_style(styles, '英文标题', size=28, bold=True, align='center', before=160, after=80, keep=True)
    roles['author'] = set_style(styles, '中文作者', east='仿宋', size=24, align='center', keep=True)
    roles['affiliation'] = set_style(styles, '中文作者单位', size=21, align='center', after=100, keep=True)
    roles['author_en'] = set_style(styles, '英文作者', size=21, align='center', keep=True)
    roles['affiliation_en'] = set_style(styles, '英文作者单位', size=21, align='center', after=80, keep=True)
    roles['abstract'] = set_style(styles, '中文摘要', size=21, after=40)
    roles['abstract_en'] = set_style(styles, '英文摘要', size=21, after=40)
    roles['keywords'] = set_style(styles, '中文关键词', size=21, after=40)
    roles['keywords_en'] = set_style(styles, '英文关键词', size=21, after=80)
    roles['meta'] = set_style(styles, '出版信息', size=21)
    for i, (name, east, size) in enumerate([('一级标题', '黑体', 24), ('二级标题', '黑体', 21), ('三级标题', '楷体_GB2312', 21), ('四级标题', '楷体_GB2312', 21)], 1):
        roles['h' + str(i)] = set_style(styles, name, east=east, size=size, left=size*10,
                                        before=120, after=60, keep=True, outline=i-1)
    roles['caption'] = set_style(styles, '三线表题', size=21, align='center', before=60, after=60, keep=True)
    roles['table'] = set_style(styles, '三线表内容', size=21, line=300)
    roles['table_center'] = set_style(styles, '三线表短项', size=21, line=300, align='center')
    roles['table_head'] = set_style(styles, '三线表表头', size=21, line=300, align='center', keep=True)
    roles['note'] = set_style(styles, '三线表注', size=21, before=60, after=60, line=300)
    roles['ref_heading'] = set_style(styles, '参考文献标题', east='黑体', size=24, before=120, after=60, keep=True)
    roles['ref'] = set_style(styles, '参考文献正文', size=21, left=420, hanging=420, line=300, after=40)
    c = Content(body, roles)
    c.paragraph('title', '科学决策排版底稿', 'title_zh')
    c.paragraph('author', '【作者姓名留空】', 'author_zh')
    c.paragraph('affiliation', '【单位名称、城市及邮编留空】', 'affiliation_zh')
    c.paragraph('abstract', '摘  要：【填写约 300 字中文摘要。依次说明研究问题、方法、主要结果及结论；仅在结果验收后填入真实内容。此处是编辑槽位。】', 'abstract_zh')
    c.paragraph('keywords', '关键词：【关键词一】；【关键词二】；【关键词三】', 'keywords_zh')
    c.paragraph('meta', '中图分类号：【待核定】    文献标识码：【待核定】    文章编号：', 'classification')
    c.paragraph('meta', 'DOI：', 'doi')
    c.paragraph('title_en', 'Scientific Decision Making Manuscript Style Base', 'title_en')
    c.paragraph('author_en', '[Author names to be supplied]', 'author_en')
    c.paragraph('affiliation_en', '[Affiliations, city and postal code to be supplied]', 'affiliation_en')
    c.paragraph('abstract_en', 'Abstract: [Insert the English abstract corresponding to the finalized Chinese abstract. This is an editable placeholder and contains no study findings.]', 'abstract_en')
    c.paragraph('keywords_en', 'Key words: [keyword one]; [keyword two]; [keyword three]', 'keywords_en')
    c.paragraph('h1', '1\u3000引言', 'intro')
    c.paragraph('body', '【在此替换引言正文。本段用于展示宋体小四、首行缩进两字符和 1.5 倍行距。保留段落样式后，可清空示例文字并粘贴已审定内容。】', 'intro_text')
    c.paragraph('h2', '1.1\u3000二级标题示例', 'heading2')
    c.paragraph('body', '【二级标题下的正文槽位，按实际论文结构增删。】', 'heading2_text')
    c.paragraph('h3', '1.1.1\u3000三级标题示例', 'heading3')
    c.paragraph('body', '【三级标题下的正文槽位。】', 'heading3_text')
    c.paragraph('h4', '1.1.1.1\u3000四级标题示例', 'heading4')
    c.paragraph('body', '【四级标题下的正文槽位；不需要的层级可直接删除。】', 'heading4_text')
    c.paragraph('h1', '2\u3000表格样式', 'table_section', page_break=True)
    c.paragraph('body', '表 1 展示三线表、表头和表注的可复用格式。所有单元格均为样式示例，不包含研究结果。正式表格应置于正文首次引用之后。', 'table_intro')
    c.paragraph('caption', '表 1\u3000三线表样式示例', 'table_caption')
    c.table()
    c.paragraph('note', '注：本表仅为样式示例。正式表注填写研究对象、n 或分母、统计口径、数据与方法来源；存在权重时写明权重，并解释 NA 或其他标记。概念表应说明不报告统计比例。', 'table_note')
    c.paragraph('h1', '3\u3000结语', 'conclusion')
    c.paragraph('body', '【填写与已确认结果相符的研究结论。本段只保留结语样式，不预设结论、建议或指标达标状态。】', 'conclusion_text')
    c.paragraph('h1', '附录 A\u3000附录标题', 'appendix')
    c.paragraph('body', '【附录置于结语之后、参考文献之前。附录正文沿用正文样式；相关表、图分别按表 A1、图 A1 编号。没有附录时删除本节。】', 'appendix_text')
    c.paragraph('ref_heading', '参考文献', 'references')
    c.paragraph('ref', '[1]【作者】.【文献题名】[J].【刊名】,【年】,【卷】(【期】):【起止页】.', 'ref1')
    c.paragraph('ref', '[2]【责任者】.【电子文献题名】[EB/OL].(【发表或更新日期】)[【引用日期】].【网址】.', 'ref2')
    body.append(section)
    parts['word/document.xml'] = xml(doc)
    parts['word/styles.xml'] = xml(styles)

    deleted = {n for n in parts if n.startswith(('customXml/', 'word/media/', 'word/embeddings/', 'word/header', 'word/footer'))}
    deleted |= {'docProps/custom.xml', 'word/footnotes.xml', 'word/endnotes.xml', 'word/_rels/settings.xml.rels'}
    for n in deleted:
        parts.pop(n, None)
    for relpath in ('word/_rels/document.xml.rels', '_rels/.rels'):
        rr = E.fromstring(parts[relpath])
        for node in list(rr):
            kind = node.get('Type').rsplit('/', 1)[-1]
            if kind in {'footer','header','footnotes','endnotes','image','oleObject','customXml','custom-properties','attachedTemplate'} or node.get('TargetMode') == 'External':
                rr.remove(node)
        parts[relpath] = xml(rr)
    types = E.fromstring(parts['[Content_Types].xml'])
    for node in list(types):
        if node.get('PartName', '').lstrip('/') in deleted or node.get('Extension') in ('wmf', 'bin', 'png'):
            types.remove(node)
    parts['[Content_Types].xml'] = xml(types)
    settings = E.fromstring(parts['word/settings.xml'])
    for tag in ('attachedTemplate', 'docVars', 'rsids', 'evenAndOddHeaders', 'footnotePr', 'endnotePr'):
        for node in list(settings.findall(q(tag))):
            settings.remove(node)
    # No surviving fields; privacy flags are still helpful for later authoring.
    for tag in ('removePersonalInformation', 'removeDateAndTime'):
        if settings.find(q(tag)) is None:
            settings.append(el(tag))
    parts['word/settings.xml'] = xml(settings)
    parts['docProps/core.xml'] = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Journal Style Base</dc:title><dc:creator></dc:creator><cp:lastModifiedBy></cp:lastModifiedBy></cp:coreProperties>'
    parts['docProps/app.xml'] = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>OOXML Style Base</Application><Company></Company></Properties>'
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(SOURCE) as src, ZipFile(output, 'w') as out:
        for info in src.infolist():
            if info.filename in parts:
                out.writestr(info, parts[info.filename])
    with ZipFile(SOURCE) as src, ZipFile(output) as out:
        for n in PRESERVE:
            assert src.read(n) == out.read(n), n
        final = E.fromstring(out.read('word/document.xml'))
        assert len(final.findall('.//w:sectPr', NS)) == 1
        for k, value in geometry.items():
            assert dict(final.find('w:body/w:sectPr/w:' + k, NS).attrib) == value, k
        assert not final.findall('.//w:fldChar', NS)
        assert len(final.findall('.//w:tbl', NS)) == 1
        assert all(b'TargetMode="External"' not in out.read(n) for n in out.namelist() if n.endswith('.rels'))
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
    print(str(output))
    print('sha256=' + hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE / '科学决策排版底稿.docx')
    parser.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    build(args.output, args.replace)

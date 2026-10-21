# -*- coding: utf-8 -*-
"""以 0914稿4 为版式模板生成 0916 稿5（清洁版）。"""
import os, re, copy, zipfile, sys, importlib.util
from xml.etree import ElementTree as ET

BASE = 'base.docx'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'draft5.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
w = lambda t: '{%s}%s' % (W, t)
XS = '{http://www.w3.org/XML/1998/namespace}space'
NS = {}
for ev, (pre, uri) in ET.iterparse(__import__('io').BytesIO(zipfile.ZipFile(BASE).read('word/document.xml')), events=['start-ns']):
    NS[pre] = uri
for pre, uri in NS.items():
    ET.register_namespace(pre, uri)

spec = importlib.util.spec_from_file_location('paper6', 'paper6.py')
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)

zin = zipfile.ZipFile(BASE)
root = ET.fromstring(zin.read('word/document.xml'))
body = root.find(w('body'))
old = list(body)
ptext = lambda e: ''.join(n.text or '' for n in e.iter(w('t')))

def first(pred):
    for e in old:
        if pred(e): return e
    raise KeyError
def style(e):
    ps = e.find(w('pPr'))
    s = ps.find(w('pStyle')) if ps is not None else None
    return s.get(w('val')) if s is not None else None

T_TITLE = old[0]; T_AUTH = old[1]; T_META = old[2]; T_DOI = old[4]; T_CLC = old[5]
T_H1 = first(lambda e: e.tag == w('p') and style(e) == '2')
T_H2 = first(lambda e: e.tag == w('p') and style(e) == '4')
T_P1 = old[8]; T_P = first(lambda e: e.tag == w('p') and style(e) == '3')
T_CAP = first(lambda e: e.tag == w('p') and style(e) == '60')
T_SRC = first(lambda e: e.tag == w('p') and style(e) == '62')
T_REF = first(lambda e: e.tag == w('p') and style(e) == '63')
FIGS = [e for e in old if e.tag == w('p') and e.find('.//' + w('drawing')) is not None]
T_TBL = [e for e in old if e.tag == w('tbl')][2]
SECT = old[-1]

# ── 原参考文献（按原编号） ──
oldrefs = {}
for e in old:
    if e.tag == w('p') and style(e) == '63':
        m = re.match(r'\[(\d+)\]\s*(.*)', ptext(e))
        if m: oldrefs['r' + m.group(1)] = m.group(2)
NEWREFS = {
 'lian2015': '练宏．注意力分配——基于跨学科视角的理论述评[J]．社会学研究，2015，30(4)：215-241，246．'
             'Lian H. Attention Allocation: A Theoretical Review from an Interdisciplinary Perspective [J]. Sociological Studies, 2015, 30(4): 215-241, 246.',
 'mohrss2017': '人力资源社会保障部．关于将36种药品纳入国家基本医疗保险、工伤保险和生育保险药品目录乙类范围的通知（人社部发〔2017〕54号）[Z]．2017．'
               'Ministry of Human Resources and Social Security. Notice on Including 36 Drugs in Category B of the National Drug Catalogue for Basic Medical Insurance, Work-Related Injury Insurance and Maternity Insurance (No. 54 [2017]) [Z]. 2017.',
 'carter2014': 'CARTER N, BRYANT-LUKOSIUS D, DICENSO A, et al. The Use of Triangulation in Qualitative Research[J]. Oncology Nursing Forum, 2014, 41(5): 545-547.',
 'nmpa2020': '国家药品监督管理局．国家药监局关于发布化学药品注册分类及申报资料要求的通告（2020年第44号）[Z]．2020．'
             'National Medical Products Administration. Announcement on Issuing the Registration Classification and Application Dossier Requirements for Chemical Drugs (No. 44 of 2020) [Z]. 2020.',
 'gbf2026': '国务院办公厅．关于健全药品价格形成机制的若干意见（国办发〔2026〕9号）[Z]．2026．'
            'General Office of the State Council. Several Opinions on Improving the Drug Price Formation Mechanism (No. 9 [2026]) [Z]. 2026.',
 'nhsa2026qa': '国家医疗保障局．国家基本医疗保险、生育保险和工伤保险药品目录及商业健康保险创新药品目录调整常用问答（2026年版）[Z]．2026．'
               'National Healthcare Security Administration. Frequently Asked Questions on the Adjustment of the National Drug Catalogue for Basic Medical Insurance, Maternity Insurance and Work-Related Injury Insurance and the Commercial Health Insurance Innovative Drug Catalogue (2026 Edition) [Z]. 2026.',
 'nhsa2026guide': '国家医疗保障局．2026年国家基本医疗保险、生育保险和工伤保险药品目录及商业健康保险创新药品目录调整申报指南[Z]．2026．'
                  'National Healthcare Security Administration. Application Guidelines for the 2026 Adjustment of the National Drug Catalogue for Basic Medical Insurance, Maternity Insurance and Work-Related Injury Insurance and the Commercial Health Insurance Innovative Drug Catalogue [Z]. 2026.',
 'nhsa2025': '国家医疗保障局，国家卫生健康委员会．支持创新药高质量发展的若干措施（医保发〔2025〕16号）[Z]．2025．'
             'National Healthcare Security Administration, National Health Commission. Several Measures to Support the High-Quality Development of Innovative Drugs (No. 16 [2025]) [Z]. 2025.',
}
REFTXT = dict(oldrefs); REFTXT.update(NEWREFS)

# ── 引文编号：按首次出现顺序 ──
order = []
def scan(s):
    for k in re.findall(r'\{(\w+)\}', s):
        if k not in order: order.append(k)
for kind, *rest in P.B:
    if kind in ('p', 'p1', 'src', 'cap', 'h1', 'h2'): scan(rest[0])
NUM = {k: i + 1 for i, k in enumerate(order)}
missing = [k for k in order if k not in REFTXT]
assert not missing, missing

# ── 构造段落 ──
def mkrun(text, sup=False, hl=False, bold=False, proto_rpr=None):
    r = ET.Element(w('r'))
    rp = copy.deepcopy(proto_rpr) if proto_rpr is not None else ET.Element(w('rPr'))
    for tag in ('vertAlign', 'highlight', 'b'):
        for x in rp.findall(w(tag)): rp.remove(x)
    if proto_rpr is None:
        f = ET.SubElement(rp, w('rFonts')); f.set(w('hint'), 'eastAsia')
    if bold: ET.SubElement(rp, w('b'))
    if hl: h = ET.SubElement(rp, w('highlight')); h.set(w('val'), 'yellow')
    if sup: v = ET.SubElement(rp, w('vertAlign')); v.set(w('val'), 'superscript')
    r.append(rp)
    t = ET.SubElement(r, w('t')); t.text = text; t.set(XS, 'preserve')
    return r

def runs(text, bold=False):
    out = []
    parts = re.split(r'(⟦|⟧)', text); hl = False
    for part in parts:
        if part == '⟦': hl = True; continue
        if part == '⟧': hl = False; continue
        for seg in re.split(r'(\{\w+\})', part):
            if not seg: continue
            m = re.fullmatch(r'\{(\w+)\}', seg)
            if m: out.append(mkrun('[%d]' % NUM[m.group(1)], sup=True, hl=hl))
            else: out.append(mkrun(seg, hl=hl, bold=bold))
    return out

def para(tmpl, text, bold_label=None):
    e = ET.Element(w('p'))
    pp = tmpl.find(w('pPr'))
    if pp is not None:
        pp = copy.deepcopy(pp)
        for x in pp.findall(w('rPr')): pp.remove(x)
        e.append(pp)
    if bold_label: e.append(mkrun(bold_label, bold=True))
    for r in runs(text): e.append(r)
    return e

def build_table(rows):
    t = ET.Element(w('tbl'))
    t.append(copy.deepcopy(T_TBL.find(w('tblPr'))))
    n = len(rows[0]); total = 8760; cw = total // n
    grid = ET.SubElement(t, w('tblGrid'))
    for _ in range(n):
        g = ET.SubElement(grid, w('gridCol')); g.set(w('w'), str(cw))
    cellp = T_TBL.find('.//' + w('tc')).find(w('p'))
    for i, row in enumerate(rows):
        tr = ET.SubElement(t, w('tr'))
        if i == 0:
            trp = ET.SubElement(tr, w('trPr')); ET.SubElement(trp, w('tblHeader'))
        for val in row:
            tc = ET.SubElement(tr, w('tc'))
            tcp = ET.SubElement(tc, w('tcPr')); tw = ET.SubElement(tcp, w('tcW')); tw.set(w('w'), str(cw)); tw.set(w('type'), 'dxa')
            tc.append(para(cellp, val))
    return t

# 表3（四口径稳健性）数据：读 numbers.json
import json as _json
_N = _json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'numbers.json'), encoding='utf-8'))
NAME = {'NMPA': '药监局', 'NHSA': '医保局', 'NHC': '卫健委'}
DIMS5 = ['安全性', '有效性', '经济性', '创新性', '公平性']
T4 = [list(P.T4[0])]
for dp in ['NMPA', 'NHSA', 'NHC']:
    for mi, (mk, mname) in enumerate([('dict', '词典编码'), ('llm', 'LLM编码')]):
        for ki, (kk, kname) in enumerate([('sent', '句次加总'), ('file', '文件等权')]):
            v = _N['spec']['%s_%s' % (mk, kk)][dp]
            T4.append([NAME[dp] if (mi == 0 and ki == 0) else '', mname if ki == 0 else '', kname]
                      + ['%.1f' % v[d] for d in DIMS5])

TABLES = {'T1': P.T1, 'T2': P.T2, 'T3': P.T3, 'T4': T4}

# ── 组装 ──
new = []
title = copy.deepcopy(T_TITLE)
keep = [r for r in title.findall(w('r')) if r.find(w('footnoteReference')) is not None]
for c in list(title):
    if c.tag != w('pPr'): title.remove(c)
title.append(mkrun(P.TITLE))
for r in keep: title.append(r)
new.append(title)
new.append(para(T_AUTH, P.AUTHORS))
new.append(para(T_META, P.ABSTRACT, bold_label='摘要：'))
new.append(para(T_META, P.KEYWORDS, bold_label='关键词：'))
new.append(copy.deepcopy(T_DOI)); new.append(copy.deepcopy(T_CLC))
new.append(para(T_META, P.AUTHOR_BIO, bold_label='作者简介：'))

tmpl = {'h1': T_H1, 'h2': T_H2, 'p1': T_P1, 'p': T_P, 'cap': T_CAP, 'src': T_SRC}
for kind, *rest in P.B:
    if kind in tmpl: new.append(para(tmpl[kind], rest[0]))
    elif kind == 'fig': new.append(copy.deepcopy(FIGS[rest[0] - 1]))
    elif kind == 'table': new.append(build_table(TABLES[rest[0]]))

new.append(para(T_H1, '参考文献'))
for k in order:
    new.append(para(T_REF, '[%d] %s' % (NUM[k], REFTXT[k])))

# 附录与英文部分
exec(open('appendix6.py', encoding='utf-8').read())
for kind, text in APPENDIX:
    new.append(para({'h1': T_H1, 'p1': T_P1, 'p': T_P, 'cap': T_CAP, 'auth': T_AUTH}[kind], text,
                    bold_label=(text.split(':')[0] + ': ') if kind == 'p' and text.startswith(('Abstract:', 'Key words:')) else None)
               if not (kind == 'p' and text.startswith(('Abstract:', 'Key words:')))
               else para(T_P, text.split(': ', 1)[1], bold_label=text.split(': ', 1)[0] + ': '))

for c in list(body): body.remove(c)
for e in new: body.append(e)
body.append(SECT)

# 去掉批注相关部件
drop = {'word/comments.xml', 'word/commentsExtended.xml', 'word/commentsIds.xml', 'word/commentsExtensible.xml'}
doc_xml = ET.tostring(root, encoding='UTF-8', xml_declaration=True)
zout = zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    if it.filename in drop: continue
    data = zin.read(it.filename)
    if it.filename == 'word/document.xml': data = doc_xml
    elif it.filename == '[Content_Types].xml':
        data = re.sub(rb'<Override[^>]*PartName="/word/comments[^"]*"[^>]*/>', b'', data)
    elif it.filename == 'word/_rels/document.xml.rels':
        data = re.sub(rb'<Relationship[^>]*Target="comments[^"]*"[^>]*/>', b'', data)
    zout.writestr(it, data)
zout.close()
print('生成 %s；引文 %d 篇（新增 %d）' % (OUT, len(order), sum(1 for k in order if k in NEWREFS)))
print('未被引用而删除的原文献：', [ '%s:%s' % (k, oldrefs[k][:14]) for k in sorted(oldrefs, key=lambda x: int(x[1:])) if k not in order])

# ── 替换图2（雷达图）为按 v3 口径重绘的版本 ──
NEWFIG = '/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914/05-图表/图2-注意力占比雷达图-v3.png'
if os.path.exists(NEWFIG):
    import shutil, tempfile
    src_zip = zipfile.ZipFile(OUT); tmp = OUT + '.tmp'
    zo = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED)
    img = open(NEWFIG, 'rb').read()
    for it in src_zip.infolist():
        zo.writestr(it, img if it.filename == 'word/media/image2.png' else src_zip.read(it.filename))
    zo.close(); src_zip.close(); shutil.move(tmp, OUT)
    print('图2 已替换为 v3 雷达图')

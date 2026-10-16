# -*- coding: utf-8 -*-
"""以 0914稿4（接受全部修订、去批注）为基准，对稿5生成词句级修订痕迹版。
相近段落逐字比对，只把改动的字句标为删除/插入；无法对应的段落整段标记。"""
import re, copy, zipfile, difflib, sys, io
from xml.etree import ElementTree as ET

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
w = lambda t: '{%s}%s' % (W, t)
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'
for ev, (pre, uri) in ET.iterparse(io.BytesIO(zipfile.ZipFile('base.docx').read('word/document.xml')), events=['start-ns']):
    ET.register_namespace(pre, uri)
AUTH, DATE = '陈海婷', '2026-09-18T12:00:00Z'
_id = [20000]
def nid():
    _id[0] += 1; return str(_id[0])
def mark(tag):
    e = ET.Element(w(tag)); e.set(w('id'), nid()); e.set(w('author'), AUTH); e.set(w('date'), DATE); return e

def parent_map(root): return {c: p for p in root.iter() for c in p}

def accept_all(root):
    pm = parent_map(root)
    for d in list(root.iter(w('del'))):
        if d in pm: pm[d].remove(d)
    pm = parent_map(root)
    for ins in list(root.iter(w('ins'))):
        par = pm.get(ins)
        if par is None: continue
        if par.tag == w('rPr'):
            par.remove(ins); continue
        i = list(par).index(ins)
        for k, c in enumerate(list(ins)): par.insert(i + k, c)
        par.remove(ins)
    pm = parent_map(root)
    for tag in ('commentRangeStart', 'commentRangeEnd'):
        for e in list(root.iter(w(tag))):
            if e in pm: pm[e].remove(e)
    pm = parent_map(root)
    for r in list(root.iter(w('r'))):
        if r.find(w('commentReference')) is not None and r in pm: pm[r].remove(r)
    return root

def ptext(e): return re.sub(r'\s', '', ''.join(t.text or '' for t in e.iter(w('t'))))
def has_drawing(e): return e.find('.//' + w('drawing')) is not None

def key(e):
    if e.tag == w('tbl'): return 'TBL:' + ptext(e)
    if e.tag == w('p'):
        if has_drawing(e): return 'FIG:' + str(len(ET.tostring(e)))
        return ptext(e)
    return 'OTHER:' + e.tag

# ── 整段标记 ──
def mark_para(p, kind):
    pp = p.find(w('pPr'))
    if pp is None: pp = ET.Element(w('pPr')); p.insert(0, pp)
    rp = pp.find(w('rPr'))
    if rp is None: rp = ET.SubElement(pp, w('rPr'))
    rp.append(mark(kind))
    kids = [c for c in list(p) if c.tag != w('pPr')]
    for c in kids: p.remove(c)
    holder = mark(kind)
    for c in kids:
        if kind == 'del':
            for t in list(c.iter(w('t'))): t.tag = w('delText')
        holder.append(c)
    p.append(holder)

def mark_tbl(t, kind):
    for tr in t.iter(w('tr')):
        trp = tr.find(w('trPr'))
        if trp is None: trp = ET.Element(w('trPr')); tr.insert(0, trp)
        trp.append(mark(kind))
        for p in tr.iter(w('p')): mark_para(p, kind)

# ── 逐字比对 ──
def flatten(p):
    """段落 → [(字符, rPr, 特殊元素)]；特殊元素（脚注引用、换行）占一个私用区字符。"""
    toks = []
    for r in p.iter(w('r')):
        rpr = r.find(w('rPr'))
        for c in r:
            if c.tag == w('t'):
                for ch in (c.text or ''): toks.append((ch, rpr, None))
            elif c.tag in (w('footnoteReference'), w('br'), w('tab')):
                toks.append(('' + c.tag, rpr, c))
    return toks

def rkey(rpr): return ET.tostring(rpr) if rpr is not None else b''

def make_runs(toks, deleted):
    runs, cur, curkey = [], None, None
    for ch, rpr, sp in toks:
        k = rkey(rpr)
        if sp is not None:
            r = ET.Element(w('r'))
            if rpr is not None: r.append(copy.deepcopy(rpr))
            r.append(copy.deepcopy(sp)); runs.append(r); cur = None; continue
        if cur is None or k != curkey:
            cur = ET.Element(w('r'))
            if rpr is not None: cur.append(copy.deepcopy(rpr))
            t = ET.SubElement(cur, w('delText' if deleted else 't')); t.set(XML_SPACE, 'preserve'); t.text = ''
            runs.append(cur); curkey = k
        cur[-1].text += ch
    return runs

def diff_ops(a, b):
    """字符级比对；长度不足 2 的相同片段夹在改动之间时并入改动，避免碎片化。"""
    ops = [list(o) for o in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()]
    out = []
    for k, (op, i1, i2, j1, j2) in enumerate(ops):
        if op == 'equal' and 0 < k < len(ops) - 1 and (i2 - i1) < 2:
            op = 'replace'
        if out and op != 'equal' and out[-1][0] != 'equal':
            out[-1] = ['replace', out[-1][1], i2, out[-1][3], j2]
        else:
            out.append([op, i1, i2, j1, j2])
    return out

def diff_para(old, new):
    """以新段落的段落属性为准，逐字标出删除与插入。"""
    ot, nt = flatten(old), flatten(new)
    a = [x[0] for x in ot]; b = [x[0] for x in nt]
    p = ET.Element(w('p'))
    pp = new.find(w('pPr'))
    if pp is not None: p.append(copy.deepcopy(pp))
    for op, i1, i2, j1, j2 in diff_ops(a, b):
        if op == 'equal':
            for r in make_runs(nt[j1:j2], False): p.append(r)
            continue
        if i2 > i1:
            d = mark('del')
            for r in make_runs(ot[i1:i2], True): d.append(r)
            p.append(d)
        if j2 > j1:
            n = mark('ins')
            for r in make_runs(nt[j1:j2], False): n.append(r)
            p.append(n)
    return p

def sim(a, b):
    if a.tag != b.tag or has_drawing(a) or has_drawing(b): return 0
    ka, kb = key(a), key(b)
    if not ka or not kb: return 1.0 if ka == kb else 0
    return difflib.SequenceMatcher(None, ka, kb, autojunk=False).ratio()

def align(olds, news, th=0.4):
    """单调对齐：在 replace 区段内，把相似度不低于阈值的旧段与新段配对。"""
    n, m = len(olds), len(news)
    S = [[sim(o, e) for e in news] for o in olds]
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best = max(D[i + 1][j], D[i][j + 1])
            if S[i][j] >= th: best = max(best, S[i][j] + D[i + 1][j + 1])
            D[i][j] = best
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        if S[i][j] >= th and abs(D[i][j] - (S[i][j] + D[i + 1][j + 1])) < 1e-9:
            pairs.append((i, j)); i += 1; j += 1
        elif abs(D[i][j] - D[i + 1][j]) < 1e-9: i += 1
        else: j += 1
    return pairs

def table_shape(t): return [len(tr.findall(w('tc'))) for tr in t.findall(w('tr'))]

def diff_table(old, new):
    if table_shape(old) != table_shape(new): return None
    t = copy.deepcopy(new)
    for otr, ntr in zip(old.findall(w('tr')), t.findall(w('tr'))):
        for otc, ntc in zip(otr.findall(w('tc')), ntr.findall(w('tc'))):
            ops, nps = otc.findall(w('p')), ntc.findall(w('p'))
            if len(ops) != len(nps): return None
            for op_, np_ in zip(ops, nps):
                if ptext(op_) != ptext(np_):
                    ntc.insert(list(ntc).index(np_), diff_para(op_, np_)); ntc.remove(np_)
    return t

stat = {'未改段落': 0, '段内修改': 0, '整段删除': 0, '整段插入': 0}
def whole(e, kind):
    e = copy.deepcopy(e)
    if has_drawing(e): return e
    (mark_tbl if e.tag == w('tbl') else mark_para)(e, kind)
    stat['整段删除' if kind == 'del' else '整段插入'] += 1
    return e

def elements(docx, accept):
    root = ET.fromstring(zipfile.ZipFile(docx).read('word/document.xml'))
    if accept: accept_all(root)
    body = root.find(w('body'))
    return root, body, [c for c in body if c.tag in (w('p'), w('tbl'))]

if __name__ == '__main__':
    _, _, old = elements('base.docx', True)
    root, body, new = elements(sys.argv[1], False)
    sect = body.find(w('sectPr'))
    ko, kn = [key(e) for e in old], [key(e) for e in new]
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ko, kn, autojunk=False).get_opcodes():
        if op == 'equal':
            out += new[j1:j2]; stat['未改段落'] += j2 - j1; continue
        olds, news = old[i1:i2], new[j1:j2]
        pairs = align(olds, news)
        oi = 0; nj = 0
        for (pi, pj) in pairs + [(len(olds), len(news))]:
            for e in olds[oi:pi]:
                if not has_drawing(e): out.append(whole(e, 'del'))
            for e in news[nj:pj]: out.append(whole(e, 'ins') if not has_drawing(e) else e)
            if pi < len(olds):
                o, e = olds[pi], news[pj]
                d = diff_table(o, e) if e.tag == w('tbl') else diff_para(o, e)
                if d is None:
                    out.append(whole(o, 'del')); out.append(whole(e, 'ins'))
                else:
                    out.append(d); stat['段内修改'] += 1
            oi, nj = pi + 1, pj + 1
    for c in list(body): body.remove(c)
    for e in out: body.append(e)
    body.append(sect)
    zin = zipfile.ZipFile(sys.argv[1]); zo = zipfile.ZipFile(sys.argv[2], 'w', zipfile.ZIP_DEFLATED)
    for it in zin.infolist():
        zo.writestr(it, ET.tostring(root, encoding='UTF-8', xml_declaration=True) if it.filename == 'word/document.xml' else zin.read(it.filename))
    zo.close()
    print('修订痕迹版：', stat)

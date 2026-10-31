import copy, re, sys, zipfile, datetime
from lxml import etree

sys.path.insert(0, sys.argv[1])
from rewrites import R
try:
    from rewrites import INS
except ImportError:
    INS = {}
try:
    from rewrites import INS2
except ImportError:
    INS2 = []
try:
    from rewrites import TBL
except ImportError:
    TBL = []

SRC, OUT_CLEAN, OUT_TRACK = sys.argv[2], sys.argv[3], sys.argv[4]
NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W = '{%s}' % NS
AUTHOR = '作者修订'
DATE = datetime.datetime(2026, 10, 30).strftime('%Y-%m-%dT%H:%M:%SZ')

def text_of(p):
    return ''.join(t.text or '' for t in p.iter(W + 't'))

def tokenize(s):
    s = s.replace('⁠', '')
    s = re.sub(r'(?<=\d) (?=\d{3}(?!\d))', ' ', s)
    out = []
    pat = re.compile(r'\{i:([^}]*)\}|\{sup:([^}]*)\}|(\[\d+(?:[，,–-]\d+)*\])|\{b:([^}]*)\}')
    pos = 0
    for m in pat.finditer(s):
        if m.start() > pos:
            out.append((s[pos:m.start()], ''))
        if m.group(1) is not None: out.append((m.group(1), 'i'))
        elif m.group(2) is not None: out.append((m.group(2), 'sup'))
        elif m.group(4) is not None: out.append((m.group(4), 'b'))
        else: out.append((m.group(3), 'sup'))
        pos = m.end()
    if pos < len(s): out.append((s[pos:], ''))
    return out

def base_rpr(p):
    def plain(rpr):
        b = rpr.find(W + 'b')
        return rpr.find(W + 'vertAlign') is None and rpr.find(W + 'i') is None and \
            (b is None or b.get(W + 'val') in ('0', 'false'))
    cands = [r.find(W + 'rPr') for r in p.iter(W + 'r') if r.find(W + 'rPr') is not None]
    for rpr in cands:
        f = rpr.find(W + 'rFonts')
        if plain(rpr) and f is not None and f.get(W + 'ascii') == 'Arial Unicode MS':
            return rpr
    for rpr in cands:
        if plain(rpr):
            return rpr
    return cands[0]

def bold_rpr(p):
    for r in p.iter(W + 'r'):
        rpr = r.find(W + 'rPr')
        if rpr is not None and rpr.find(W + 'b') is not None and rpr.find(W + 'b').get(W + 'val') not in ('0', 'false'):
            return rpr
    return None

def make_runs(p, new):
    base = base_rpr(p)
    runs = []
    bold = bold_rpr(p)
    for txt, kind in tokenize(new):
        r = etree.Element(W + 'r')
        rpr = copy.deepcopy(bold if kind == 'b' and bold is not None else base)
        if kind == 'i':
            f = rpr.find(W + 'rFonts')
            for a in ('ascii', 'hAnsi'): f.set(W + a, 'Times New Roman')
            etree.SubElement(rpr, W + 'i'); etree.SubElement(rpr, W + 'iCs')
        elif kind == 'sup':
            v = etree.SubElement(rpr, W + 'vertAlign'); v.set(W + 'val', 'superscript')
        r.append(rpr)
        t = etree.SubElement(r, W + 't'); t.text = txt
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        runs.append(r)
    return runs

def renumber_refs(body):
    from refs import NEW, FIX, REMOVED
    elems = list(body)
    def ptext(el): return ''.join(t.text or '' for t in el.iter(W + 't'))
    h = [i for i, el in enumerate(elems) if el.tag == W + 'p' and ptext(el).strip() == '参考文献'][0]
    old_ps, old_text = [], {}
    for el in elems[h + 1:]:
        m = re.match(r'^\[(\d+)\](.*)$', ptext(el))
        if el.tag != W + 'p' or not m: break
        old_ps.append(el); old_text[int(m.group(1))] = m.group(2)
    pat = re.compile(r'\[(\d+(?:[，,]\d+)*)\]')
    order = []
    for el in elems[:h]:
        for t in el.iter(W + 't'):
            for m in pat.finditer(t.text or ''):
                for n in re.split('[，,]', m.group(1)):
                    n = int(n)
                    if n not in order: order.append(n)
    assert not (set(order) & REMOVED), set(order) & REMOVED
    missing = [n for n in order if n not in old_text and n not in NEW]
    assert not missing, missing
    unused = sorted(set(old_text) - set(order) - REMOVED)
    assert not unused, ('cited nowhere', unused)
    mp = {o: i + 1 for i, o in enumerate(order)}
    for el in elems[:h]:
        for t in el.iter(W + 't'):
            if t.text and pat.search(t.text):
                t.text = pat.sub(lambda m: '[' + '，'.join(str(x) for x in sorted(mp[int(n)] for n in re.split('[，,]', m.group(1)))) + ']', t.text)
    tmpl = old_ps[0]
    for el in old_ps: body.remove(el)
    anchor = elems[h]
    for o in order:
        np_ = copy.deepcopy(tmpl)
        runs = np_.findall(W + 'r')
        for r in runs[2:]: np_.remove(r)
        runs[0].find(W + 't').text = '[%d]' % mp[o]
        txt = FIX.get(o) or NEW.get(o) or old_text[o]
        txt = re.sub(r'（(S?\d+)）', r'(\1)', txt)
        txt = re.sub(r'（(\d{4}-\d{2}-\d{2})）', r'(\1)', txt)
        txt = txt.replace('，', ', ').replace('：', ': ') if re.search(r'\[J\]', txt) and re.search(r'\d{4}，', txt) else txt
        runs[1].find(W + 't').text = txt
        anchor.addnext(np_); anchor = np_
    import json; json.dump({str(k): v for k, v in mp.items()}, open('/tmp/claude-0/-home-user-innovative-drug-paper/4a956f8c-2eb4-5d7e-917d-06b4aad75179/scratchpad/refmap.json', 'w'))
    return mp

def build(track):
    zin = zipfile.ZipFile(SRC)
    root = etree.fromstring(zin.read('word/document.xml'))
    body = root.find(W + 'body')
    ps = [el for el in body if el.tag == W + 'p']
    rid = 9000
    for i, new in R.items():
        p = ps[i]
        old_runs = p.findall(W + 'r')
        new_runs = make_runs(p, new)
        if track:
            d = etree.Element(W + 'del'); d.set(W + 'id', str(rid)); rid += 1
            d.set(W + 'author', AUTHOR); d.set(W + 'date', DATE)
            for r in old_runs:
                p.remove(r)
                for t in r.findall(W + 't'):
                    t.tag = W + 'delText'
                d.append(r)
            ins = etree.Element(W + 'ins'); ins.set(W + 'id', str(rid)); rid += 1
            ins.set(W + 'author', AUTHOR); ins.set(W + 'date', DATE)
            for r in new_runs: ins.append(r)
            p.append(d); p.append(ins)
        else:
            for r in old_runs: p.remove(r)
            for r in new_runs: p.append(r)
    # 新增段落：插入在 ps[k] 之后，沿用其段落格式
    for k, new in sorted(INS.items(), reverse=True):
        tmpl = ps[k]
        np_ = etree.Element(W + 'p')
        ppr = tmpl.find(W + 'pPr')
        if ppr is not None:
            ppr = copy.deepcopy(ppr); np_.append(ppr)
        runs = make_runs(tmpl, new)
        if track:
            if ppr is None:
                ppr = etree.SubElement(np_, W + 'pPr')
            rpr = ppr.find(W + 'rPr')
            if rpr is None:
                rpr = etree.SubElement(ppr, W + 'rPr')
            m = etree.SubElement(rpr, W + 'ins'); m.set(W + 'id', str(rid)); rid += 1
            m.set(W + 'author', AUTHOR); m.set(W + 'date', DATE)
            ins = etree.SubElement(np_, W + 'ins'); ins.set(W + 'id', str(rid)); rid += 1
            ins.set(W + 'author', AUTHOR); ins.set(W + 'date', DATE)
            for r in runs: ins.append(r)
        else:
            for r in runs: np_.append(r)
        tmpl.addnext(np_)
    # INS2：(锚点段号, 模板段号, 文本)，同一锚点按列表顺序依次插入
    last = {}
    for k, tk, new in INS2:
        anchor = last.get(k, ps[k]); tmpl = ps[tk]
        np_ = etree.Element(W + 'p')
        ppr = tmpl.find(W + 'pPr')
        if ppr is not None:
            ppr = copy.deepcopy(ppr); np_.append(ppr)
        runs = make_runs(tmpl, new)
        if track:
            if ppr is None: ppr = etree.SubElement(np_, W + 'pPr')
            rpr = ppr.find(W + 'rPr')
            if rpr is None: rpr = etree.SubElement(ppr, W + 'rPr')
            m = etree.SubElement(rpr, W + 'ins'); m.set(W + 'id', str(rid)); rid += 1
            m.set(W + 'author', AUTHOR); m.set(W + 'date', DATE)
            ins = etree.SubElement(np_, W + 'ins'); ins.set(W + 'id', str(rid)); rid += 1
            ins.set(W + 'author', AUTHOR); ins.set(W + 'date', DATE)
            for r in runs: ins.append(r)
        else:
            for r in runs: np_.append(r)
        anchor.addnext(np_); last[k] = np_
    # 中图分类号：改为G311；R197
    for r in ps[7].findall(W + 'r'):
        t = r.find(W + 't')
        if t is not None and t.text and t.text.startswith('R197'):
            if track:
                ins = etree.Element(W + 'ins'); ins.set(W + 'id', str(rid)); rid += 1
                ins.set(W + 'author', AUTHOR); ins.set(W + 'date', DATE)
                pre = copy.deepcopy(r); pre.find(W + 't').text = 'G311；'
                ins.append(pre)
                r.addprevious(ins)
            else:
                t.text = 'G311；' + t.text
            break
    for tbl in body.iter(W + 'tbl'):
        for t in tbl.iter(W + 't'):
            for a, b_ in TBL:
                if t.text and a in t.text: t.text = t.text.replace(a, b_)
    renumber_refs(body)
    return zin, etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)

for track, out in ((False, OUT_CLEAN), (True, OUT_TRACK)):
    zin, xml = build(track)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = xml if item.filename == 'word/document.xml' else zin.read(item.filename)
            zout.writestr(item, data)
print('ok')

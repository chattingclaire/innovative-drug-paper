import sys, json, re, math, difflib, copy, csv
sys.path.insert(0, '/tmp/claude-0/-home-user-innovative-drug-paper/4a956f8c-2eb4-5d7e-917d-06b4aad75179/scratchpad/supp')
from core import *
import numpy as np
from scipy.stats import chi2_contingency, fisher_exact
import docx
from docx.oxml.ns import qn
from lxml import etree

SRC, OUT = sys.argv[1], sys.argv[2]
REPO = '/home/user/innovative-drug-paper/'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
f2 = lambda x: f'{x:.2f}'
f3 = lambda x: f'{x:.3f}'
def tn(n):  # 千分位细空格
    s = f'{n:,}'
    return s.replace(',', ' ')

# ---------------- 计算 ----------------
meta = json.load(open(D + '政策来源与组件清单.json', encoding='utf-8'))
cnt = {}
for r in rows: cnt[r['source_entry_id']] = cnt.get(r['source_entry_id'], 0) + 1

def dedup_cond(rs, m, mode):
    norm = lambda t: re.sub(r'[\s\W_]+', '', t)
    if mode == 'none':
        kept = rs
    elif mode in ('exact', 'norm'):
        seen, kept = set(), []
        for r in rs:
            k = r['原文'] if mode == 'exact' else norm(r['原文'])
            if k in seen: continue
            seen.add(k); kept.append(r)
    else:
        base = [r for r in rs if lab(r, m, 'S') == 1 and lab(r, m, 'E') is not None]
        keys, kept = [], []
        for r in base:
            n = norm(r['原文'])
            if any(difflib.SequenceMatcher(None, n, o).ratio() >= 0.85 for o in keys): continue
            keys.append(n); kept.append(r)
    return cond(kept, m, 'E', 'S')

def dept_rows(dp): return [r for r in rows if r['部门'] == dp]

def labmat(rs, m):
    a = np.full((len(rs), 5), np.nan)
    for i, r in enumerate(rs):
        for j, d in enumerate(DIMS):
            v = lab(r, m, d)
            if v is not None: a[i, j] = v
    return a

rng = np.random.default_rng(20261030)
B = 5000
def boot_stats(a, idx):
    s = a[idx]
    pos = np.nansum(s == 1, axis=0) if False else np.sum(s == 1, axis=0)
    tot = pos.sum()
    sh = 100 * pos / tot if tot else np.full(5, np.nan)
    def cnd(t, g):
        gi, ti = DIMS.index(g), DIMS.index(t)
        den = (s[:, gi] == 1) & ~np.isnan(s[:, ti])
        return 100 * np.sum(s[den, ti] == 1) / den.sum() if den.sum() else np.nan
    return sh, {'E|S': cnd('E', 'S'), 'F|Ec': cnd('F', 'Ec'), 'Ec|F': cnd('Ec', 'F')}

COMPS = [
 ('经济性占比', 'share', 'Ec', 'NHSA', 'NMPA'), ('经济性占比', 'share', 'Ec', 'NHSA', 'NHC'),
 ('创新性占比', 'share', 'I', 'NMPA', 'NHSA'), ('创新性占比', 'share', 'I', 'NMPA', 'NHC'),
 ('卫健委占比', 'within', ('S', 'Ec'), 'NHC', None), ('药监局占比', 'within', ('S', 'E'), 'NMPA', None),
 ('E|S', 'cond', 'E|S', 'NHSA', 'NMPA'), ('E|S', 'cond', 'E|S', 'NHSA', 'NHC'), ('E|S', 'cond', 'E|S', 'NMPA', 'NHC'),
 ('F|Ec', 'cond', 'F|Ec', 'NHC', 'NHSA'), ('Ec|F', 'cond', 'Ec|F', 'NHSA', 'NHC'),
]
def boot_table(m):
    mats = {dp: labmat(dept_rows(dp), m) for dp in DEPTS}
    obs = {dp: boot_stats(mats[dp], np.arange(len(mats[dp]))) for dp in DEPTS}
    draws = {dp: [] for dp in DEPTS}
    for _ in range(B):
        for dp in DEPTS:
            n = len(mats[dp]); draws[dp].append(boot_stats(mats[dp], rng.integers(0, n, n)))
    out = []
    for name, kind, key, a, b in COMPS:
        def val(st, dp):
            sh, cd = st
            if kind == 'share': return sh[DIMS.index(key)]
            if kind == 'cond': return cd[key]
        if kind == 'within':
            x, y = key
            o = obs[a][0][DIMS.index(x)] - obs[a][0][DIMS.index(y)]
            ds = np.array([st[0][DIMS.index(x)] - st[0][DIMS.index(y)] for st in draws[a]])
            label = {'S': '安全性', 'E': '有效性', 'Ec': '经济性'}[x] + '−' + {'S': '安全性', 'E': '有效性', 'Ec': '经济性'}[y]
        else:
            o = val(obs[a], a) - val(obs[b], b)
            ds = np.array([val(sa, a) - val(sb, b) for sa, sb in zip(draws[a], draws[b])])
            label = CN[a] + '−' + CN[b]
        ds = ds[~np.isnan(ds)]
        lo, hi = np.percentile(ds, [2.5, 97.5])
        out.append((name, label, o, lo, hi, len(ds)))
    return out

# ---------------- 表格 XML ----------------
def cell_xml(text, w, top, bottom, align='center', bold=False):
    tc = etree.Element(W + 'tc')
    tcPr = etree.SubElement(tc, W + 'tcPr')
    e = etree.SubElement(tcPr, W + 'tcW'); e.set(W + 'type', 'dxa'); e.set(W + 'w', str(w))
    e = etree.SubElement(tcPr, W + 'vAlign'); e.set(W + 'val', 'center')
    bd = etree.SubElement(tcPr, W + 'tcBorders')
    for side, on in (('top', top), ('bottom', bottom), ('left', False), ('right', False)):
        e = etree.SubElement(bd, W + side); e.set(W + 'val', 'single' if on else 'nil'); e.set(W + 'sz', '8'); e.set(W + 'color', '000000')
    mar = etree.SubElement(tcPr, W + 'tcMar')
    for side, v in (('top', 30), ('bottom', 30), ('left', 75), ('right', 75)):
        e = etree.SubElement(mar, W + side); e.set(W + 'w', str(v)); e.set(W + 'type', 'dxa')
    p = etree.SubElement(tc, W + 'p'); pPr = etree.SubElement(p, W + 'pPr')
    e = etree.SubElement(pPr, W + 'spacing'); e.set(W + 'before', '0'); e.set(W + 'after', '0'); e.set(W + 'line', '240'); e.set(W + 'lineRule', 'auto')
    e = etree.SubElement(pPr, W + 'ind'); e.set(W + 'firstLine', '0')
    e = etree.SubElement(pPr, W + 'jc'); e.set(W + 'val', align)
    r = etree.SubElement(p, W + 'r'); rPr = etree.SubElement(r, W + 'rPr')
    e = etree.SubElement(rPr, W + 'rFonts'); e.set(W + 'ascii', 'Times New Roman'); e.set(W + 'hAnsi', 'Times New Roman'); e.set(W + 'eastAsia', '宋体')
    e = etree.SubElement(rPr, W + 'b'); e.set(W + 'val', '1' if bold else '0')
    e = etree.SubElement(rPr, W + 'sz'); e.set(W + 'val', '18' if len(str(text)) > 0 else '18')
    t = etree.SubElement(r, W + 't'); t.text = str(text); t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    return tc

def table_xml(header, body, widths, align=None):
    tbl = etree.Element(W + 'tbl')
    tblPr = etree.SubElement(tbl, W + 'tblPr')
    e = etree.SubElement(tblPr, W + 'tblW'); e.set(W + 'type', 'auto'); e.set(W + 'w', '0')
    e = etree.SubElement(tblPr, W + 'jc'); e.set(W + 'val', 'center')
    e = etree.SubElement(tblPr, W + 'tblLayout'); e.set(W + 'type', 'fixed')
    grid = etree.SubElement(tbl, W + 'tblGrid')
    for w in widths:
        e = etree.SubElement(grid, W + 'gridCol'); e.set(W + 'w', str(w))
    hrows = header if isinstance(header[0], list) else [header]
    for hi, h in enumerate(hrows):
        tr = etree.SubElement(tbl, W + 'tr'); trPr = etree.SubElement(tr, W + 'trPr')
        etree.SubElement(trPr, W + 'cantSplit'); etree.SubElement(trPr, W + 'tblHeader')
        for j, (txt, w) in enumerate(zip(h, widths)):
            tr.append(cell_xml(txt, w, top=(hi == 0), bottom=(hi == len(hrows) - 1)))
    for i, row in enumerate(body):
        tr = etree.SubElement(tbl, W + 'tr'); trPr = etree.SubElement(tr, W + 'trPr'); etree.SubElement(trPr, W + 'cantSplit')
        for j, (txt, w) in enumerate(zip(row, widths)):
            a = (align[j] if align else 'center')
            tr.append(cell_xml(txt, w, top=False, bottom=(i == len(body) - 1), align=a))
    return tbl

# ---------------- 文档编辑 ----------------
doc = docx.Document(SRC)
P = doc.paragraphs
def find(prefix):
    for p in doc.paragraphs:
        if p.text.startswith(prefix): return p
    raise KeyError(prefix)
def set_text(p, text):
    runs = p.runs
    runs[0].text = text
    for r in runs[1:]: r._r.getparent().remove(r._r)
def para_after(anchor_el, text, style):
    p = doc.add_paragraph(text, style=style)
    anchor_el.addnext(p._p); return p._p
def table_after(anchor_el, tbl):
    anchor_el.addnext(tbl); return tbl
class Cursor:
    def __init__(self, el): self.el = el
    def p(self, text, style='Body Text'): self.el = para_after(self.el, text, style); return self
    def cap(self, cn, en): self.p(cn, 'Caption2'); self.p(en, 'Caption2'); return self
    def t(self, header, body, widths, align=None): self.el = table_after(self.el, table_xml(header, body, widths, align)); return self
    def note(self, text): return self.p(text, 'SourceNote')

TOTW = 9000
def widths(fr): s = sum(fr); return [round(TOTW * x / s) for x in fr]

# 标题
title = P[0]
set_text(title, '创新药跨部门评价规则差异与协同治理')
br = title.runs[0]._r
brk = etree.SubElement(br, W + 'br'); t2 = etree.SubElement(br, W + 't'); t2.text = '补充材料'

# ---- A ----
set_text(find('补充材料A'), '补充材料A　编码规范与LLM运行设置')

# ---- B ----
set_text(find('三部门主语料共51个来源条目'), '三部门主语料共51个来源条目、4 481个分析单元。其中，药监局17个来源条目、1 848个单元，医保局24个来源条目、2 100个单元，卫健委10个来源条目、533个单元。另有4个中央来源条目、443个单元作为制度背景，不纳入三部门主比较。来源条目可以包括通知、方案、附件和官方问答，完整清单见表B1。')
pB = find('官方问答与正文分别标记')
set_text(pB, '官方问答与正文分别标记，重复附件只计一次。联合专业文件保留全部署名机关，并按既定制度系统归入一个部门。来源等权均值先求来源内部比例，再对分母非零的来源取均值；系列年度成员均值按固定系列和年份计算。')
order = {'NMPA': 0, 'NHSA': 1, 'NHC': 2}
ms = sorted(meta, key=lambda x: (order[x['department']], x['policy_year'], x['source_entry_id']))
body = []
for i, x in enumerate(ms, 1):
    name = re.sub(r'^(NMPA|NHSA|NHC|CDE)(-NHC)?-', '', x['source_entry_id'])
    name = re.sub(r'-(19|20)\d\d(-正式版|版)?$', '', name).replace('-正式版', '')
    if x['source_entry_id'].startswith('CDE-'): name = '（药审中心）' + name
    body.append([str(i), CN[x['department']], name, str(x['policy_year']), '是' if x['joint_publication'] else '否', str(cnt[x['source_entry_id']])])
assert sum(int(b[-1]) for b in body) == 4481
c = Cursor(pB._p).cap('表B1 三部门政策来源清单', 'Table B1 Policy Sources by Department')
c.t(['序号', '部门', '来源（简称）', '年份', '联合发文', '句段数'], body, widths([0.6, 0.9, 5.2, 0.8, 0.9, 0.8]), ['center', 'center', 'left', 'center', 'center', 'center'])
c.note('注：来源简称依据政策名称整理，年份为政策印发年份；“药审中心”指国家药品监督管理局药品审评中心，其来源归入药监局。联合发文按既定制度系统归入一个部门。句段数合计为4 481。')

# ---- C ----
ab = json.load(open(REPO + '03-编码检验与版本/466条人工独立编码-A-B原表-20261023/A-B一致性核算.json', encoding='utf-8'))
set_text(find('466条人工标注结果中'), '人工核验样本共466条。两名编码员（一名为参与编码手册设计的作者，另一名为未参与手册设计、编码前经统一培训的同课题组研究生）在不查看规则编码和LLM编码结果的情况下，对照原文及必要上下文，各自独立判读全部466条句段的五个维度，讨论、合并前各自保留结果（表C3）；分歧经讨论后形成最终人工标签，共2 330项。编码方案此前已以77条校准样本校准，校准样本不计入466条检验。最终人工标签中，安全性、有效性、经济性、创新性、公平性的正类数分别为133、94、110、33、48。表C1列示两种机器方法与最终人工标签的分类计数，表C2列示核验样本的构成，表C4列示LLM编码的复跑一致性。')
pC2note = find('注：抽取范围为主语料')
set_text(pC2note, pC2note.text.replace('表2按这466条的实际判断计数', '表C1按这466条的实际判断计数'))
mets = ab['metrics']
body = []
for d in DIMS:
    x = mets[d]
    body.append([x['dimension'], str(x['N']), f"{100*x['agreement']:.2f}", f3(x['cohen_kappa']), str(x['A_positive']), str(x['B_positive'])])
c = Cursor(pC2note._p).cap('表C3 两名编码员独立判读的一致性', 'Table C3 Inter-coder Agreement before Discussion')
c.t(['维度', '有效配对数', '一致率/%', 'κ', '编码员A正类数', '编码员B正类数'], body, widths([1, 1.1, 1.1, 0.9, 1.4, 1.4]))
c.note('注：按原始记录ID与维度对齐，使用讨论、合并前两名编码员各自的判读结果计算Cohen κ；2 330项中共58项不一致，涉及42条材料。该指标反映人工编码的可靠性，与机器编码对最终人工标签的比较（表C1）分别报告。')
rerun = [('安全性', 465, '0.960', '0.938'), ('有效性', 463, '0.967', '0.954'), ('经济性', 465, '0.940', '0.909'), ('创新性', 465, '1.000', '0.938'), ('公平性', 463, '0.926', '0.876'), ('五维合并', 2321, '0.958', '0.929')]
c.cap('表C4 LLM编码的复跑一致性', 'Table C4 Reproducibility of LLM Coding')
c.t(['维度', '两次运行有效配对数', '两次运行间κ', '复跑与最终人工标签κ'], [[a, str(b), x, y] for a, b, x, y in rerun], widths([1.2, 1.8, 1.5, 2]))
c.note('注：以同一模型、编码手册和逐条材料对466条样本重新运行一次，批次组成与并发设置不同于全量运行。两次运行中438条句段（93.99%）的五维判断完全一致；复跑结果与最终人工标签共2 322项有效二元判断、8项待定。κ仅使用双方均为0/1的配对计算。')

# ---- D ----
set_text(find('表D1列示九种统计口径'), '表D1列示九种统计口径及逐一剔除51个来源后的比较方向，表D2列示条件比例的有效分母与待定值上下界，表D3列示去除重复援引条款后的条件比例，表D4、表D5列示正文表7对应的规则编码结果。两种编码方法的完整九种统计口径结果、逐来源结果及五维待定上下界另附可复算统计文件。各表均先列LLM主分析，再列规则对照。')
pD2note = find('注：仅对待定维度枚举')
body = []
for dp in DEPTS:
    rs = dept_rows(dp)
    for m in ('LLM', '规则'):
        cells = [CN[dp], 'LLM' if m == 'LLM' else '规则']
        for mode in ('none', 'exact', 'norm', 'near'):
            n, dn = dedup_cond(rs, m, mode)
            cells.append(f'{n}/{dn}（{100*n/dn:.2f}）' if dn else '—')
        body.append(cells)
c = Cursor(pD2note._p).cap('表D3 去除重复援引条款后安全性句段中涉及有效性的比例（E|S）', 'Table D3 E|S after Removing Repeated Provisions')
c.t(['部门', '方法', '未去重', '完全相同文本', '规范化文本', '近似文本'], body, widths([0.9, 0.8, 1.5, 1.5, 1.5, 1.5]))
c.note('注：单元格为“共现句段数/有效条件分母（比例/%）”。“完全相同文本”与“规范化文本”在部门全部句段中去重，规范化指去除空白与标点后比较；“近似文本”在各方法判为安全性且有效性可判定的句段内，以序列相似度≥0.85判定重复。各方式均保留首次出现的句段。')
def subset_rows(m):
    out = []
    for dp in ('NMPA', 'NHSA'):
        for name, rs in subsets(dp):
            pos, tot, sh = shares(rs, m)
            out.append((dp, name, tot, sh))
    return out
sub = subset_rows('规则')
b4 = [[CN[dp], nm, str(tot)] + [f2(sh[d]) for d in DIMS] for dp, nm, tot, sh in sub if nm in ('全部来源', '专门来源', '其他来源')]
c.cap('表D4 专门针对创新药的来源拆分（规则编码）/%', 'Table D4 Attention Shares by Innovative-drug-specific Sources (Rule-based Coding) / %')
c.t(['部门', '子集', '五维标签合计', '安全性', '有效性', '经济性', '创新性', '公平性'], b4, widths([0.8, 1, 1.2, 0.9, 0.9, 0.9, 0.9, 0.9]))
c.note('注：口径同正文表7，分母为各子集规则编码五维标签合计，待定项不计入。专门来源的界定同正文表7注。两部门在规则编码下的主要关注维度与全部来源一致。')
b5 = [[CN[dp], str(len([r for r in dept_rows(dp) if '创新药' in r['原文']])), str(tot)] + [f2(sh[d]) for d in DIMS] for dp, nm, tot, sh in sub if nm.startswith('含')]
c.cap('表D5 含“创新药”一词的句段（规则编码）/%', 'Table D5 Attention Shares in Passages Mentioning “Innovative Drug” (Rule-based Coding) / %')
c.t(['部门', '句段数', '五维标签合计', '安全性', '有效性', '经济性', '创新性', '公平性'], b5, widths([0.8, 0.9, 1.2, 0.9, 0.9, 0.9, 0.9, 0.9]))
c.note('注：卫健委组文本未出现“创新药”一词，故未列示。此类句段样本量较小，相应占比仅作描述性参考。')

# ---- F ----
pRef = find('参考文献')
anchor = pRef._p.getprevious()
c = Cursor(anchor)
c.p('补充材料F　部门差异检验的完整结果', 'Heading 1')
c.p('表F1列示各维度内容覆盖比例的3×2卡方检验，表F2列示部门两两比较的Fisher确切概率检验，表F3列示正文表6各项比较在句段层面重抽样所得的95%置信区间。正文表6报告按政策来源重抽样的区间；由于同一来源的句段并非相互独立，句段重抽样区间通常更窄，仅作对照。各项检验均剔除待定项。', 'First Paragraph')
body = []
for m in ('LLM', '规则'):
    for d in DIMS:
        tab = [[sum(lab(r, m, d) == 1 for r in dept_rows(dp)), sum(lab(r, m, d) == 0 for r in dept_rows(dp))] for dp in DEPTS]
        chi, p, dof, _ = chi2_contingency(tab, correction=False)
        V = math.sqrt(chi / sum(map(sum, tab)))
        body.append(['LLM' if m == 'LLM' else '规则', {'S': '安全性', 'E': '有效性', 'Ec': '经济性', 'I': '创新性', 'F': '公平性'}[d],
                     ' / '.join(f'{a}/{a+b}' for a, b in tab), f2(chi), str(dof), '<0.001' if p < 0.001 else f3(p), f3(V)])
c.cap('表F1 五维内容覆盖比例的部门差异检验', 'Table F1 Chi-square Tests of Departmental Differences in Coverage')
c.t(['方法', '维度', '正类/有效句段（药监局/医保局/卫健委）', 'χ²', '自由度', 'P', 'Cramér’s V'], body, widths([0.7, 0.7, 3, 0.9, 0.7, 0.8, 1]))
c.note('注：3×2列联表中以0.10、0.30和0.50分别作为Cramér’s V小、中、大效应的参考值。')
body = []
pairs = [('NMPA', 'NHSA'), ('NMPA', 'NHC'), ('NHSA', 'NHC')]
for m in ('LLM', '规则'):
    for d in DIMS:
        for a, b in pairs:
            ra, rb = dept_rows(a), dept_rows(b)
            pa = sum(lab(r, m, d) == 1 for r in ra); na = sum(lab(r, m, d) is not None for r in ra)
            pb = sum(lab(r, m, d) == 1 for r in rb); nb = sum(lab(r, m, d) is not None for r in rb)
            p = fisher_exact([[pa, na - pa], [pb, nb - pb]])[1]
            padj = min(1, 3 * p)
            body.append(['LLM' if m == 'LLM' else '规则', {'S': '安全性', 'E': '有效性', 'Ec': '经济性', 'I': '创新性', 'F': '公平性'}[d],
                         CN[a] + '−' + CN[b], f2(100 * pa / na - 100 * pb / nb).replace('-', '−'), '<0.001' if padj < 0.001 else f3(padj)])
c.cap('表F2 五维内容覆盖比例的部门两两比较', 'Table F2 Pairwise Comparisons of Coverage between Departments')
c.t(['方法', '维度', '比较', '差值/百分点', '校正后P'], body, widths([0.9, 0.9, 1.8, 1.4, 1.2]))
c.note('注：采用双侧Fisher确切概率法，同一维度内按3次比较作Bonferroni校正。差值为前项减后项。')
body = []
for m in ('LLM', '规则'):
    for name, label, o, lo, hi, nv in boot_table(m):
        body.append(['LLM' if m == 'LLM' else '规则', name, label, f2(o), f'[{f2(lo)}, {f2(hi)}]'.replace('-', '−')])
c.cap('表F3 正文表6各项比较的句段重抽样置信区间', 'Table F3 Passage-level Bootstrap Confidence Intervals for Comparisons in Table 6')
c.t(['方法', '指标', '比较', '差值/百分点', '95%CI'], body, widths([0.9, 1.1, 1.8, 1.3, 1.9]))
c.note('注：在各部门内对句段有放回重抽样5 000次（随机数种子20261030），取差值的2.5%与97.5%分位数。注意力占比和条件比例的口径同正文。')

doc.save(OUT)
print('saved')

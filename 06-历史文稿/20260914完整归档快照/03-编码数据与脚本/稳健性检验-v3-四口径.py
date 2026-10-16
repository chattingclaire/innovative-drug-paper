# -*- coding: utf-8 -*-
"""四种测算口径（词典/LLM × 句次加总/文件等权）+ 逐一剔除单份文件，申报指南口径 v3。"""
import json, os
from collections import Counter, defaultdict
D = os.path.dirname(os.path.abspath(__file__))
DIMS = ['安全性', '有效性', '经济性', '创新性', '公平性']
dic = {x['id']: (x['dept'], x['file'], set(x['dims_v3'])) for x in json.load(open(os.path.join(D,'coding_v3_dict.json'), encoding='utf-8')) if not x['junk']}
llm = {x['id']: (x['dept'], x['file'], set(x['dims'])) for x in json.load(open(os.path.join(D,'coding_v3_llm.json'), encoding='utf-8'))}

def shares(data, mode, drop=None):
    if mode == '句次加总':
        h = defaultdict(Counter)
        for i,(dept,f,ds) in data.items():
            if f == drop: continue
            for d in ds: h[dept][d] += 1
        return {dp: {d: (100*c[d]/sum(c.values()) if sum(c.values()) else 0) for d in DIMS} for dp,c in h.items()}
    per = defaultdict(lambda: defaultdict(Counter))
    for i,(dept,f,ds) in data.items():
        if f == drop: continue
        for d in ds: per[dept][f][d] += 1
    out = {}
    for dp, files in per.items():
        acc = Counter(); n = 0
        for f, c in files.items():
            t = sum(c.values())
            if not t: continue
            n += 1
            for d in DIMS: acc[d] += 100*c[d]/t
        out[dp] = {d: acc[d]/n if n else 0 for d in DIMS}
    return out

print('==== 四种测算口径 ====')
rows = {}
for name, data in [('词典编码', dic), ('LLM编码', llm)]:
    for mode in ['句次加总', '文件等权']:
        s = shares(data, mode)
        rows[(name, mode)] = s
        print('\n-- %s · %s --' % (name, mode))
        for dp in ['NMPA','NHSA','NHC','GOV']:
            print('  %-5s ' % dp + '  '.join('%s %.1f' % (d, s[dp][d]) for d in DIMS))

print('\n==== 四口径下的结论检验 ====')
def rng(dp, d): return [rows[k][dp][d] for k in rows]
def chk(name, ok): print('  %-46s %s' % (name, '成立' if ok else '不成立'))
chk('医保局以经济性为主导', all(max(rows[k]['NHSA'], key=rows[k]['NHSA'].get)=='经济性' for k in rows))
print('    经济性占比区间 %.1f-%.1f' % (min(rng('NHSA','经济性')), max(rng('NHSA','经济性'))))
chk('药监局经济性占比最低', all(min(rows[k]['NMPA'], key=rows[k]['NMPA'].get)=='经济性' for k in rows))
print('    经济性占比区间 %.1f-%.1f' % (min(rng('NMPA','经济性')), max(rng('NMPA','经济性'))))
chk('医保局创新性高于其安全性与有效性', all(rows[k]['NHSA']['创新性']>rows[k]['NHSA']['安全性'] and rows[k]['NHSA']['创新性']>rows[k]['NHSA']['有效性'] for k in rows))
print('    创新性 %.1f-%.1f｜安全性 %.1f-%.1f｜有效性 %.1f-%.1f' % (min(rng('NHSA','创新性')),max(rng('NHSA','创新性')),min(rng('NHSA','安全性')),max(rng('NHSA','安全性')),min(rng('NHSA','有效性')),max(rng('NHSA','有效性'))))
chk('药监局以安全性、有效性、创新性为主', all(sorted(rows[k]['NMPA'],key=rows[k]['NMPA'].get,reverse=True)[:3].count('经济性')==0 for k in rows))
chk('卫健委以公平性为主导', all(max(rows[k]['NHC'], key=rows[k]['NHC'].get)=='公平性' for k in rows))
print('    卫健委公平性占比区间 %.1f-%.1f，安全性 %.1f-%.1f' % (min(rng('NHC','公平性')),max(rng('NHC','公平性')),min(rng('NHC','安全性')),max(rng('NHC','安全性'))))

print('\n==== 逐一剔除单份文件（主导维度是否改变）====')
for name, data in [('词典编码', dic), ('LLM编码', llm)]:
    files = sorted({f for _,f,_ in data.values()})
    base = shares(data, '句次加总')
    changed = []
    for f in files:
        s = shares(data, '句次加总', drop=f)
        for dp in ['NMPA','NHSA']:
            if dp in s and s[dp] and max(s[dp],key=s[dp].get) != max(base[dp],key=base[dp].get):
                changed.append((dp,f,max(s[dp],key=s[dp].get)))
    print('  %s：剔除任一文件后主导维度改变的情形 %d' % (name, len(changed)))
    for c in changed[:5]: print('   ', c)

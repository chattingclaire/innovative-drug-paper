# -*- coding: utf-8 -*-
"""编码结果稳健性检验：词典/LLM × 句次加总/文件等权 四种口径，以及逐一剔除单份文件。
输入：all_sentences.json（含词典 keyword_dims）、llm_all_results.json
运行：python3 稳健性检验-多口径.py"""
import json, os
from collections import defaultdict, Counter
BASE = os.path.dirname(os.path.abspath(__file__))
D = ['安全性', '有效性', '经济性', '创新性', '公平性']
NAME = {'NMPA': '药监局', 'NHSA': '医保局', 'NHC': '卫健委', 'GOV': '国务院'}
S = json.load(open(os.path.join(BASE, 'all_sentences.json'), encoding='utf-8'))
LLM = {r['id']: r.get('dims', []) for r in json.load(open(os.path.join(BASE, 'llm_all_results.json'), encoding='utf-8'))}
METHODS = [('词典', lambda s: s.get('keyword_dims', [])), ('LLM', lambda s: LLM.get(s['id'], []))]

def pct(c):
    t = sum(c[k] for k in D)
    return {k: 100 * c[k] / t for k in D} if t else None

for mname, get in METHODS:
    byfile = defaultdict(lambda: defaultdict(Counter))
    for s in S:
        for d in get(s):
            byfile[s['dept']][s['file']][d] += 1
    print('\n==== %s编码 ====' % mname)
    for dep in ['NMPA', 'NHSA', 'NHC', 'GOV']:
        tot = Counter()
        for c in byfile[dep].values():
            tot += c
        p = pct(tot)
        ps = [pct(c) for c in byfile[dep].values() if pct(c)]
        fe = {k: sum(x[k] for x in ps) / len(ps) for k in D}
        print('%s 句次加总：' % NAME[dep] + '  '.join('%s %.1f' % (k, p[k]) for k in D))
        print('%s 文件等权：' % NAME[dep] + '  '.join('%s %.1f' % (k, fe[k]) for k in D))
        if len(byfile[dep]) > 2:
            top = max(D, key=lambda k: tot[k]); changed = []; lo = {k: 100 for k in D}; hi = {k: 0 for k in D}
            for fn, c in byfile[dep].items():
                q = pct(tot - c)
                for k in D:
                    lo[k] = min(lo[k], q[k]); hi[k] = max(hi[k], q[k])
                if max(D, key=lambda k: q[k]) != top:
                    changed.append(fn)
            print('%s 逐一剔除单份文件：主导维度%s，改变主导维度的文件%s；占比区间 ' % (NAME[dep], top, changed or '无')
                  + '  '.join('%s %.1f-%.1f' % (k, lo[k], hi[k]) for k in D))

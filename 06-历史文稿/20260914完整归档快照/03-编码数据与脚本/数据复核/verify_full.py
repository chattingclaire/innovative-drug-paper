#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论文全量复核（2026-08-15）：用已恢复的原始词典重跑表2/表3/表4，逐个数字比对论文。
依赖：all_sentences.json、llm_all_results.json、论文构建档案-0813/编码脚本-已恢复/词典编码脚本-policy_coding_v2.py"""
import re, json, collections, os
os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')

src = open('词典编码脚本-policy_coding_v2.py', encoding='utf-8').read()
ns = {}
exec(src[src.index('DIMENSIONS = {'):src.index('DIM_PATTERNS = {}')], ns)
D = ns['DIMENSIONS']
DIMS = ['安全性', '有效性', '经济性', '创新性', '公平性']
PAT = {k: [re.compile(w) for w in v] for k, v in D.items()}
print('词典规模:', {k: len(v) for k, v in D.items()}, '合计', sum(len(v) for v in D.values()), '（论文：每维度17-21个，共96个）')

sents = json.load(open('all_sentences.json'))
llm = {r['id']: set(d for d in r.get('dims', []) if d in DIMS) for r in json.load(open('llm_all_results.json'))}
code = {s['id']: {d for d in DIMS if any(p.search(s['sent']) for p in PAT[d])} for s in sents}
dept = {s['id']: s['dept'] for s in sents}

tab = collections.defaultdict(collections.Counter)
for i, ds in code.items():
    for d in ds: tab[dept[i]][d] += 1

PUB3 = {'NMPA': [230,363,6,174,35], 'NHSA': [50,52,680,164,89], 'NHC': [63,20,13,6,78], 'GOV': [5,5,37,21,30]}
NAME = {'NMPA': '药监局', 'NHSA': '医保局', 'NHC': '卫健委', 'GOV': '国务院'}
print('\n== 表3 命中句次 ==')
allok = True
for k in ('NMPA', 'NHSA', 'NHC', 'GOV'):
    row = [tab[k][d] for d in DIMS]; ok = row == PUB3[k]; allok &= ok
    print(f'{NAME[k]:4} 重跑{row} 论文{PUB3[k]} {"✅" if ok else "❌"}')
col = [sum(tab[k][d] for k in PUB3) for d in DIMS]
print(f'列合计 {col} 论文[348, 440, 736, 365, 232] {"✅" if col == [348,440,736,365,232] else "❌"}')
n1701 = sum(1 for v in code.values() if v)
print(f'编码句 {n1701} 论文1701 {"✅" if n1701 == 1701 else "❌"}')

print('\n== 表4 注意力占比（%）==')
PUB4 = {'NMPA': [28.5,44.9,0.7,21.5,4.3], 'NHSA': [4.8,5.0,65.7,15.8,8.6], 'NHC': [35.0,11.1,7.2,3.3,43.3], 'GOV': [5.1,5.1,37.8,21.4,30.6]}
for k in ('NMPA', 'NHSA', 'NHC', 'GOV'):
    row = [tab[k][d] for d in DIMS]; t = sum(row)
    pct = [round(100*x/t, 1) for x in row]
    print(f'{NAME[k]:4} {pct} 论文{PUB4[k]} {"✅" if pct == PUB4[k] else "❌"}')

print('\n== 表2 Cohen\'s κ ==')
PUBK = {'安全性': (0.896,98.0,348,369), '有效性': (0.700,94.3,440,275), '经济性': (0.921,97.3,736,777),
        '创新性': (0.917,98.4,365,352), '公平性': (0.831,97.6,232,280)}
N = len(sents); A = B = C = E = 0
for d in DIMS:
    a = b = c = e = 0
    for s in sents:
        i = s['id']; x = d in code[i]; y = d in llm.get(i, set())
        if x and y: a += 1
        elif x: b += 1
        elif y: c += 1
        else: e += 1
    po = (a+e)/N; pe = ((a+b)*(a+c)+(b+e)*(c+e))/N**2; k = (po-pe)/(1-pe)
    pk, ppo, pd, pl = PUBK[d]
    ok = round(k,3) == pk and a+b == pd and a+c == pl and round(100*po,1) == ppo
    print(f'{d}: κ={k:.3f}(论文{pk}) 一致率={100*po:.1f}%(论文{ppo}) 词典{a+b}(论文{pd}) LLM{a+c}(论文{pl}) {"✅" if ok else "❌"}')
    A += a; B += b; C += c; E += e
po = (A+E)/(5*N); pe = ((A+B)*(A+C)+(B+E)*(C+E))/(5*N)**2
print(f'总体: κ={(po-pe)/(1-pe):.3f}(论文0.867) 一致率={100*po:.1f}%(论文97.1)')
diff = sum(1 for i in code if code[i] != llm.get(i, set()))
print(f'差异句 {diff} 论文456 {"✅" if diff == 456 else "❌"}')

print('\n== 5.2节 LLM口径稳健性检验 ==')
ld = collections.defaultdict(collections.Counter)
for i, ds in llm.items():
    for d in ds: ld[dept[i]][d] += 1
for k, note in (('NHSA','论文65.1'), ('NHC','论文44.1'), ('NMPA','论文 安全38.4/有效29.2')):
    t = sum(ld[k][d] for d in DIMS)
    print(NAME[k], {d: round(100*ld[k][d]/t, 1) for d in DIMS}, note)

print('\n== 4.2节 "非临床" 误配（论文：17句均药监局，44.9%→43.7%）==')
trap = [s for s in sents if '非临床' in s['sent']]
print(len(trap), collections.Counter(NAME[s['dept']] for s in trap), '剔除后 %.1f%%' % (100*(363-len(trap))/(808-len(trap))))

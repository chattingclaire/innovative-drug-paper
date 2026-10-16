#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论文数据复核脚本（2026-08-13）
复核《制度视角下创新药多主体评价的认知分歧与协调路径》中可由本地数据文件验证的全部数字。
数据文件：项目根目录 all_sentences.json（3387句语料）、llm_all_results.json（LLM逐句编码结果）。
注意：表2的κ值与表3的词典命中频次基于词典逐句编码结果计算，该中间文件未存档，无法在此复核；
本脚本验证LLM侧全部数字、语料规模、表3/表4的算术自洽性，以及否定语境（"非临床"）误配的规模。
"""
import json, re, collections, os
os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')
sents = json.load(open('all_sentences.json'))
llm = {r['id']: r.get('dims', []) for r in json.load(open('llm_all_results.json'))}
dims = ['安全性','有效性','经济性','创新性','公平性']

print('== 语料规模 ==')
print('句子数:', len(sents), '（论文: 3387）')
files = sorted({(s['file'], s['dept']) for s in sents})
dc = collections.Counter(d for _, d in files)
print('文件数:', len(files), dict(dc), '（论文: 55 = NMPA19/NHSA24/NHC10/GOV2）')

print('\n== LLM各维度命中句数（论文表2: 369/275/777/352/280）==')
cnt = collections.Counter()
dept_dim = collections.defaultdict(collections.Counter)
id2dept = {s['id']: s['dept'] for s in sents}
for i, ds in llm.items():
    for d in ds:
        if d in dims:
            cnt[d] += 1
            dept_dim[id2dept[i]][d] += 1
print([cnt[d] for d in dims])

print('\n== LLM口径各部门占比（论文5.2节: NHSA经济65.1 / NHC公平44.1 / NMPA安全38.4·有效29.2）==')
for dept in ('NMPA','NHSA','NHC','GOV'):
    tot = sum(dept_dim[dept][d] for d in dims)
    print(dept, {d: round(100*dept_dim[dept][d]/tot, 1) for d in dims})

print('\n== 表3/表4 算术自洽 ==')
t3 = {'NMPA':[230,363,6,174,35],'NHSA':[50,52,680,164,89],'NHC':[63,20,13,6,78],'GOV':[5,5,37,21,30]}
for k,v in t3.items():
    print(k,'行合计', sum(v))
cols = [sum(t3[k][j] for k in t3) for j in range(5)]
print('列合计', cols, '总计', sum(cols), '（论文: 348/440/736/365/232, 2121）')
shares = {k:[round(100*x/sum(v),1) for x in v] for k,v in t3.items()}
print('表4占比复算:', shares)
print('极差: 经济性 %.1f 创新性 %.1f 公平性 %.1f （论文: 65.0/18.2/39.0）' % (
    max(s[2] for s in shares.values())-min(s[2] for s in shares.values()),
    max(s[3] for s in shares.values())-min(s[3] for s in shares.values()),
    max(s[4] for s in shares.values())-min(s[4] for s in shares.values())))

print('\n== 否定语境（"非临床"）误配排查（论文4.2节: 17句均NMPA，剔除后44.9%→43.7%）==')
trap = [s for s in sents if '非临床' in s['sent']]
print('含"非临床"句子:', len(trap), collections.Counter(s['dept'] for s in trap))
print('全部剔除后NMPA有效性占比: %.1f%%' % (100*(363-len(trap))/(808-len(trap))))

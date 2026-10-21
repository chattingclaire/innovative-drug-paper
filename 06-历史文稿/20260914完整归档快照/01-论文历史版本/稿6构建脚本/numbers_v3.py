# -*- coding: utf-8 -*-
"""汇总稿6所需的全部数字（申报指南口径 v3），写入 numbers.json 供正文与表格引用。"""
import json, os, re
from collections import Counter, defaultdict

ARCH = '/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914/03-编码数据与脚本'
DIMS = ['安全性', '有效性', '经济性', '创新性', '公平性']
RAW = json.load(open(os.path.join(ARCH, 'coding_v3_dict.json'), encoding='utf-8'))
KEPT = [x for x in RAW if not x['junk']]
LLM = {x['id']: set(x['dims']) for x in json.load(open(os.path.join(ARCH, 'coding_v3_llm.json'), encoding='utf-8'))}
dic = {x['id']: (x['dept'], x['file'], set(x['dims_v3'])) for x in KEPT}
llm = {x['id']: (x['dept'], x['file'], LLM.get(x['id'], set())) for x in KEPT}

def shares(data, mode, drop=None):
    if mode == 'sent':
        h = defaultdict(Counter)
        for i, (dept, f, ds) in data.items():
            if f == drop: continue
            for d in ds: h[dept][d] += 1
        return {dp: {d: (100*c[d]/sum(c.values()) if sum(c.values()) else 0) for d in DIMS} for dp, c in h.items()}
    per = defaultdict(lambda: defaultdict(Counter))
    for i, (dept, f, ds) in data.items():
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

def kappa(a, b):
    n = len(a); po = sum(1 for x, y in zip(a, b) if x == y)/n
    p1, p2 = sum(a)/n, sum(b)/n; pe = p1*p2 + (1-p1)*(1-p2)
    return ((po-pe)/(1-pe) if pe < 1 else 1.0), po

N = {}
N['n_files'] = len({x['file'] for x in RAW})
N['n_raw'] = len(RAW)
N['n_junk'] = len(RAW) - len(KEPT)
N['n_kept'] = len(KEPT)
N['junk_pct'] = round(100*N['n_junk']/N['n_raw'], 1)
N['junk_kinds'] = dict(Counter(x['junk'] for x in RAW if x['junk']))
N['dept_sent'] = dict(Counter(x['dept'] for x in KEPT))
N['dept_files'] = {dp: len({x['file'] for x in KEPT if x['dept'] == dp}) for dp in ['NMPA','NHSA','NHC','GOV']}

hits = defaultdict(Counter)
for x in KEPT:
    for d in x['dims_v3']: hits[x['dept']][d] += 1
N['hits'] = {dp: dict(hits[dp]) for dp in hits}
N['hit_total'] = {dp: sum(hits[dp].values()) for dp in hits}
N['dict_nonzero'] = sum(1 for x in KEPT if x['dims_v3'])
N['dict_hits_all'] = sum(len(x['dims_v3']) for x in KEPT)
N['llm_nonzero'] = sum(1 for i in llm if llm[i][2])
N['llm_hits_all'] = sum(len(v[2]) for v in llm.values())

N['spec'] = {}
for nm, data in [('dict', dic), ('llm', llm)]:
    for mode in ['sent', 'file']:
        s = shares(data, mode)
        N['spec']['%s_%s' % (nm, mode)] = {dp: {d: round(s[dp][d], 1) for d in DIMS} for dp in ['NMPA','NHSA','NHC','GOV']}

ids = list(dic)
N['kappa'] = {}
ta, tb = [], []
for d in DIMS:
    a = [1 if d in dic[i][2] else 0 for i in ids]
    b = [1 if d in llm[i][2] else 0 for i in ids]
    k, po = kappa(a, b); ta += a; tb += b
    N['kappa'][d] = {'k': round(k, 3), 'agree': round(100*po, 1), 'dict': sum(a), 'llm': sum(b)}
k, po = kappa(ta, tb)
N['kappa']['总体'] = {'k': round(k, 3), 'agree': round(100*po, 1), 'dict': sum(ta), 'llm': sum(tb)}

# 逐一剔除单份文件
changed = 0
for nm, data in [('dict', dic), ('llm', llm)]:
    base = shares(data, 'sent')
    for f in {v[1] for v in data.values()}:
        s = shares(data, 'sent', drop=f)
        for dp in ['NMPA', 'NHSA']:
            if dp in s and s[dp] and max(s[dp], key=s[dp].get) != max(base[dp], key=base[dp].get):
                changed += 1
N['loo_changed'] = changed

# 医保局创新性来源集中度
inn = Counter(x['file'] for x in KEPT if x['dept'] == 'NHSA' and '创新性' in x['dims_v3'])
N['nhsa_inn_total'] = sum(inn.values())
N['nhsa_inn_top2'] = sum(c for _, c in inn.most_common(2))
N['nhsa_inn_top2_pct'] = round(100*N['nhsa_inn_top2']/N['nhsa_inn_total'], 1)
N['nhsa_inn_top2_files'] = [f for f, _ in inn.most_common(2)]

# 词频部门区分度
N['distinct'] = {}
for kw in ['临床试验', '支付', '处方']:
    c = Counter()
    for x in KEPT: c[x['dept']] += len(re.findall(kw, x['sent']))
    t = sum(c.values())
    top = c.most_common(1)[0]
    N['distinct'][kw] = {'dept': top[0], 'pct': round(100*top[1]/t, 1), 'total': t}

json.dump(N, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'numbers.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
if __name__ == '__main__':
    for k, v in N.items():
        print(k, ':', v if not isinstance(v, dict) else json.dumps(v, ensure_ascii=False)[:300])

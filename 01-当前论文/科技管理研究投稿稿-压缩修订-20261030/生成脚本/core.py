import csv, json, re
from collections import defaultdict
D = '/tmp/claude-0/-home-user-innovative-drug-paper/4a956f8c-2eb4-5d7e-917d-06b4aad75179/scratchpad/supp_data/复核数据/'
DIMS = ['S', 'E', 'Ec', 'I', 'F']
DEPTS = ['NMPA', 'NHSA', 'NHC']
CN = {'NMPA': '药监局', 'NHSA': '医保局', 'NHC': '卫健委'}
rows = list(csv.DictReader(open(D + '4481条全量编码.csv', encoding='utf-8-sig')))
def lab(r, m, d):
    v = r[f'{m}_{d}']
    return None if v == '' else int(v)
def shares(rs, m):
    pos = {d: sum(1 for r in rs if lab(r, m, d) == 1) for d in DIMS}
    tot = sum(pos.values())
    return pos, tot, {d: (100 * pos[d] / tot if tot else float('nan')) for d in DIMS}
def cond(rs, m, tgt, given):
    den = [r for r in rs if lab(r, m, given) == 1 and lab(r, m, tgt) is not None]
    num = sum(1 for r in den if lab(r, m, tgt) == 1)
    return num, len(den)
SPECIAL = {
 'NMPA': [s for s in {r['source_entry_id'] for r in rows if r['部门'] == 'NMPA'} if '创新药' in s],
 'NHSA': ['NHSA-NHC-支持创新药高质量发展的若干措施-2025', 'NHSA-目录调整工作方案-2025', 'NHSA-目录调整工作方案-2026-正式版',
          'NHSA-目录调整申报指南-2026-正式版', 'NHSA-常用问答-2026版'],
}
def subsets(dp):
    rs = [r for r in rows if r['部门'] == dp]
    sp = [r for r in rs if r['source_entry_id'] in SPECIAL[dp]]
    ot = [r for r in rs if r['source_entry_id'] not in SPECIAL[dp]]
    kw = [r for r in rs if '创新药' in r['原文']]
    return [('全部来源', rs), ('专门来源', sp), ('其他来源', ot), ('含“创新药”一词的句段', kw)]

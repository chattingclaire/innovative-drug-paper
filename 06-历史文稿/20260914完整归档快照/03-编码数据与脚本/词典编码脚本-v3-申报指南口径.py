#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""词典编码 v3（申报指南口径）

维度定义取自《2026年国家基本医疗保险、生育保险和工伤保险药品目录及商业健康保险
创新药品目录调整申报指南》附件"申报药品摘要幻灯片要求"（二）—（六），
2023、2024、2026 三版内容一致。

与 v2 的差别：
1. 关键词按申报指南各维度的内容界定重设，不再取自《药品临床综合评价管理指南》；
2. 程序性表述须与判据词共现才计入（谈判/竞价须涉及价格费用基金；临床试验须涉及疗效结论）；
3. 排除非药品语境（数据安全、行政收费、创新型国家等套话）；
4. 增加语料清洗：剔除标题、条目号、目录页、来源行与过短碎片。
"""
import json, os, re, sys
from collections import Counter, defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIMS = ['安全性', '有效性', '经济性', '创新性', '公平性']

# ── 一、语料清洗规则 ──
def is_junk(sent):
    t = re.sub(r'\s+', ' ', sent).strip()
    if len(t) < 12: return '过短碎片'
    if '......' in t or '．．．' in t: return '目录页'
    if re.match(r'^(#+|附件\s*\d|附\s*件)', t): return '标题行'
    if re.match(r'^[（(]?[一二三四五六七八九十]+[、）)]\s*\S{0,12}$', t): return '条目标题'
    if re.match(r'^\d+[、.]\s*\S{0,12}$', t): return '条目标题'
    if re.match(r'^第[一二三四五六七八九十百]+条\s*$', t): return '条号'
    if re.search(r'^来源[:：]|https?://', t) and len(t) < 80: return '来源行'
    return None

# ── 二、各维度关键词（判据词，单独出现即计入）──
CORE = {
    # 说明书收载的安全性信息；国内外不良反应发生情况；与同类药品安全性比较
    '安全性': ['不良反应', '不良事件', '安全性', '药品安全', '用药安全', '毒性', '禁忌',
               '药物警戒', '安全信号', '风险控制', '风险管理', '风险最小化', '风险评估',
               '获益.{0,4}风险', '风险.{0,4}获益', 'SAE', 'ADR', '副作用', '安全监测',
               '安全性数据', '安全性信息'],
    # 与对照药品疗效比较；指南/诊疗规范推荐；技术评审报告中有效性结论
    '有效性': ['有效性', '疗效', '临床价值', '临床获益', '治疗效果', '生存率', '生存期',
               '无进展生存', '客观缓解', '疾病控制率', '循证', '临床证据', '治疗价值',
               '临床优势', 'QALY', '生命质量', '健康效用', '指南推荐', '诊疗规范推荐',
               '技术评审报告'],
    # 销售金额；价格费用情况；对医保基金的影响
    '经济性': ['价格', '费用', '成本', '支付标准', '报销', '医保基金', '基金支出', '基金承受',
               '基金可持续', '预算影响', '基金支付能力', '销售金额', '销量', '药物经济',
               '经济性', '定价', '降价', '降幅', '日均.{0,2}费用', '疗程费用', '医疗费用',
               '药品费用', '成本效果', '成本效用'],
    # 主要创新点；创新带来的疗效或安全性优势；自主知识产权的创新药；药品注册分类
    '创新性': ['创新药', '创新性', '创新点', '自主知识产权', '原始创新', '自主研发',
               '新药研发', '重大新药创制', '突破性治疗', '优先审评', '附条件批准', '特别审批',
               '临床急需', '未满足', '填补.{0,4}空白', '首创', '新靶点', '新作用机制',
               '新化合物', '新分子实体', '注册分类', '改良型新药'],
    # 能否弥补药品目录短板；临床管理难度；目录外药品价格费用
    '公平性': ['公平', '目录短板', '保障空白', '保障尚不充分', '儿童用药', '儿科用药',
               '罕见病', '短缺', '供应保障', '断供', '可及', '可获得', '可负担',
               '临床管理难度', '基层用药', '保基本', '基本药物', '困难群众', '用药需求短板',
               '用药保障需求'],
}

# ── 三、共现规则：左侧词须与右侧任一词同现才计入 ──
CONTEXT = {
    '有效性': ([r'临床试验', r'临床研究', r'真实世界'],
               [r'疗效', r'有效性', r'获益', r'临床价值', r'终点', r'缓解', r'生存', r'证据']),
    '经济性': ([r'谈判', r'竞价', r'报价', r'集中带量采购', r'集采', r'支付意愿'],
               [r'价格', r'费用', r'标准', r'金额', r'基金', r'降幅', r'成本', r'预算', r'报价']),
}

# ── 四、排除语境 ──
EXCLUDE = {
    '安全性': [r'安全感', r'数据安全', r'生产安全', r'安全生产', r'网络安全', r'信息安全', r'食品安全'],
    '有效性': [r'有效期', r'有效账号', r'有效身份'],
    '经济性': [r'不收取任何费用'],
    '创新性': [r'创新型国家', r'创新驱动发展', r'产业创新发展', r'新质生产力', r'传承创新'],
    '公平性': [r'公平竞争'],
}

PAT = {d: [re.compile(k) for k in ks] for d, ks in CORE.items()}
CTX = {d: ([re.compile(x) for x in a], [re.compile(x) for x in b]) for d, (a, b) in CONTEXT.items()}
EXC = {d: [re.compile(x) for x in ks] for d, ks in EXCLUDE.items()}

def code_sentence(sent):
    """返回该句命中的维度集合。"""
    hit = set()
    for d in DIMS:
        # 先剔除排除语境，再判断
        masked = sent
        for e in EXC[d]:
            masked = e.sub('', masked)
        if any(p.search(masked) for p in PAT[d]):
            hit.add(d)
        elif d in CTX:
            a, b = CTX[d]
            if any(p.search(masked) for p in a) and any(p.search(masked) for p in b):
                hit.add(d)
    return hit

def main():
    S = json.load(open(os.path.join(SCRIPT_DIR, 'all_sentences.json'), encoding='utf-8'))
    out = []
    for x in S:
        j = is_junk(x['sent'])
        out.append({'id': x['id'], 'dept': x['dept'], 'file': x['file'], 'sent': x['sent'],
                    'junk': j, 'dims_v3': sorted(code_sentence(x['sent'])) if not j else []})
    json.dump(out, open(os.path.join(SCRIPT_DIR, 'coding_v3_dict.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)
    kept = [x for x in out if not x['junk']]
    print('原始句子 %d，清洗剔除 %d（%.1f%%），纳入分析 %d'
          % (len(out), len(out) - len(kept), 100 * (len(out) - len(kept)) / len(out), len(kept)))
    print('剔除构成：', dict(Counter(x['junk'] for x in out if x['junk'])))
    h = defaultdict(Counter); ns = Counter()
    for x in kept:
        ns[x['dept']] += 1
        for d in x['dims_v3']: h[x['dept']][d] += 1
    print('\n%-6s %-7s %s' % ('部门', '句数', ''.join('%-14s' % d for d in DIMS) + '命中句次'))
    for dp in ['NMPA', 'NHSA', 'NHC', 'GOV']:
        t = sum(h[dp].values())
        print('%-6s %-7d ' % (dp, ns[dp]) + ''.join(
            '%-14s' % ('%.1f%%(%d)' % (100 * h[dp][d] / t, h[dp][d])) for d in DIMS) + str(t))
    nz = sum(1 for x in kept if x['dims_v3'])
    print('\n命中至少一个维度 %d 句（%.1f%%），命中句次合计 %d'
          % (nz, 100 * nz / len(kept), sum(len(x['dims_v3']) for x in kept)))

if __name__ == '__main__':
    main()

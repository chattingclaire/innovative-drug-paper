"""Prepare review records; reads XLSX only. No label agreement is recalculated."""
import hashlib
import json
from pathlib import Path

ADMIN = Path(__file__).resolve().parent
CAL = ADMIN.parent
PROXY = CAL / '代理试填-20261010'
OUT = PROXY / '复核反馈处理-20261010'
ROOT = CAL.parents[3]
DIMS = ['S', 'E', 'Ec', 'I', 'F']
NAMES = dict(zip(DIMS, ['安全性', '有效性', '经济性', '创新性', '公平性']))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

OUT.mkdir(exist_ok=True)
payload = json.loads((ADMIN / '无答案校准内容.json').read_text())
materials = {u['material_id']: u for u in payload['units']}
feedback = {
    ('校准12', 'Ec'): {'direction': 0, 'kind': 'confirmed', 'reason': '原文只有价格协商流程和结果，不满足经济性实质内容门槛。'},
    ('校准35', 'Ec'): {'direction': 0, 'kind': 'leaning', 'reason': '仅规定协议有效期两年；未规定或核验价格、支付标准、费用或预算。相邻独立句不回传标签。'},
    ('校准32', 'I'): {'direction': 0, 'kind': 'leaning', 'reason': '一般适老化指导目的，不足以证明具体实质改良或实际创新研发支持。'},
    ('校准39', 'I'): {'direction': 0, 'kind': 'leaning', 'reason': '鼓励研究和创制新药的目的，尚不足以认定实际创新支持。'},
    ('校准39', 'F'): {'direction': 1, 'kind': 'leaning', 'reason': '临床急需短缺与优先审评有明确联系；仍需裁定该目的句的实质内容。'},
    ('校准06', 'F'): {'direction': None, 'kind': 'unresolved', 'reason': '特定药品境内未上市不能直接等同于境内无对应治疗选项；需补足公平保障关系。'},
    ('校准17', 'F'): {'direction': None, 'kind': 'unresolved', 'reason': '一般用药需求评估不自动等于公平保障；需识别当前措施与具体获取障碍的联系。'},
    ('校准25', 'F'): {'direction': None, 'kind': 'unresolved', 'reason': '须区分特定药品未上市、无对应获批治疗选项及现实供应不足；保留完整申请条件。'},
}
record = {
    'purpose': '接续用户复核意见的开发工作副本；非新的独立盲评或人工信度结果',
    'date': '2026-10-10',
    'feedback_provenance': '用户在本对话提供的复核意见；未新增或推定复核人身份及独立编码过程',
    'manual_sha256': payload['manual_sha256'],
    'feedback': [{'material_id': m, 'dimension': d, **v} for (m, d), v in feedback.items()],
    'workbooks': {},
    'preserved_inputs': {},
    'new_kappa_computed': False,
    'source_review': [
        {'title': 'WHO Health equity', 'url': 'https://www.who.int/health-topics/health-equity',
         'verification': '2026-10-10读取官方全文，Overview',
         'finding': '公平关注不合理且可避免或可补救的群体差异；不能将普通获取安排一律解释成公平关系。'},
        {'title': 'Levesque, Harris and Russell (2013)', 'url': 'https://link.springer.com/article/10.1186/1475-9276-12-18',
         'verification': '2026-10-10读取期刊原文，Abstract及概念框架',
         'finding': '可及性涉及识别需要、寻求、抵达、取得和使用服务等多个环节；该框架没有规定本研究的逐句公平性标签。'},
        {'title': '关于改革完善基层药品联动管理机制 扩大基层药品种类的意见政策解读',
         'url': 'https://www.nhc.gov.cn/yaozs/c100097/202411/c6ced0648ada4729ac63422acb25e98a.shtml',
         'verification': '2026-10-10读取卫健委官方全文；页面2024-11-22',
         'finding': '官方明确基层用药地区差异、转诊衔接和偏远地区配送障碍；应分别核定需求评估句与具体障碍的关系，而非向全篇回传F。'},
        {'title': '药品注册管理办法（2020）',
         'url': 'https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2023/art_3275cb2a929d4c34ac8c0421b2a9c257.html',
         'verification': '2026-10-10核查官方第59、70条内容；不将网页路径中的2023当成法规年份',
         'finding': '无有效防治手段与较既有治疗具有明显临床优势为不同条件；临床急需罕见病药品可获审评支持，但这不证明所有境内未上市药品都无可用治疗。'},
        {'title': '临床急需境外新药审评审批工作程序（2018年第79号），云南药监转发',
         'url': 'https://mpa.yn.gov.cn/sydw/ynsspypshcyzx/201811/t20181101_1229946.html',
         'verification': '2026-10-10官方域名检索摘录显示无有效治疗与明显临床优势分别列项；直接抓取超时，未当作完整新增判读材料',
         'finding': '不能据名单名称推定每个品种没有对应治疗；如拟援引具体遴选条款，应先获取完整条款并统一补入双方材料。'},
    ],
}
protected = [ADMIN / '无答案校准内容.json', CAL / '共用编码手册.md']
protected += [CAL / f'校准试填-{c}.xlsx' for c in ['A', 'B']]
protected += [PROXY / f'代理{c}独立判定.json' for c in ['A', 'B']]
protected += [PROXY / f'代理试填-{c}（供真人复核）.xlsx' for c in ['A', 'B']]
protected += [ROOT / 'outputs/编码修订核查-20261008/本轮结果/创新药评价的注意力配置差异与协调路径.docx']
for p in protected:
    if not p.is_file():
        raise ValueError(f'Protected input missing: {p}')
    record['preserved_inputs'][str(p)] = sha(p)

for coder in ['A', 'B']:
    original_path = PROXY / f'代理{coder}独立判定.json'
    revision_path = PROXY / f'复核理由-{coder}.json'
    original = json.loads(original_path.read_text())
    revision = json.loads(revision_path.read_text())
    originals = {u['material_id']: u for u in original['units']}
    revisions = {u['material_id']: u for u in revision['units']}
    if len(revisions) != 40 or set(revisions) != set(materials) or set(originals) != set(materials):
        raise ValueError('IDs are missing or duplicated')
    rows = []
    for material in payload['units']:
        mid = material['material_id']
        u = revisions[mid]
        if u['original_labels'] != originals[mid]['labels']:
            raise ValueError(f'Initial labels changed: {coder}/{mid}')
        for dim in DIMS:
            evs = u['evidence_records'][dim]
            if not evs or not u['revised_reasons'][dim].strip():
                raise ValueError('Missing reason/evidence')
            for ev in evs:
                if ev['scope'] == 'current':
                    text = material['current_text']
                    if ev.get('context_index') is not None:
                        raise ValueError('Current quote has context index')
                elif ev['scope'] == 'context':
                    idx = ev['context_index']
                    if type(idx) is not int or not 0 <= idx < len(material['contexts']):
                        raise ValueError('Invalid context index')
                    text = material['contexts'][idx]
                    if not ev.get('connection', '').strip():
                        raise ValueError('Missing context connection')
                else:
                    raise ValueError('Invalid scope')
                if not ev['quote'] or ev['quote'] not in text:
                    raise ValueError(f'Quote mismatch: {coder}/{mid}/{dim}')
            old = u['original_labels'][dim]
            issue = feedback.get((mid, dim))
            label = old
            direction = issue['direction'] if issue else None
            state = '保留代理判断，未作真人终判'
            # Only B12 was an unqualified correction. A12 already held 0.
            if issue and issue['kind'] == 'confirmed':
                label = 0
                state = '按用户明确复核改为0' if coder == 'B' else '原0与用户明确复核一致'
            elif issue and not (mid == '校准35' and coder == 'A'):
                label = None
                state = '依据尚不足，需补核后裁定' if issue['kind'] == 'unresolved' else '倾向意见，尚未最终裁定'
            elif issue:
                state = '原0与复核倾向一致，仍非终判'
            rows.append({
                'material_id': mid, 'dimension': dim, 'dimension_name': NAMES[dim],
                'original_label': old, 'user_direction': direction, 'working_label': label,
                'state': state, 'feedback_reason': issue['reason'] if issue else None,
                'reason': u['revised_reasons'][dim], 'evidence_records': evs,
                'agent_review_flag': u['review_flags'][dim],
            })
    record['workbooks'][coder] = {
        'original_source': str(original_path), 'reasons_source': str(revision_path),
        'reasons_sha256': sha(revision_path), 'rows': rows,
        'working_labels_filled': sum(r['working_label'] is not None for r in rows),
        'awaiting_adjudication': sum(r['working_label'] is None for r in rows),
        'confirmed_changes': sum(r['working_label'] is not None and r['working_label'] != r['original_label'] for r in rows),
        'reason_count': len(rows),
    }

(OUT / '复核处理记录.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({c: {k: v for k, v in d.items() if k != 'rows'} for c, d in record['workbooks'].items()}, ensure_ascii=False, indent=2))

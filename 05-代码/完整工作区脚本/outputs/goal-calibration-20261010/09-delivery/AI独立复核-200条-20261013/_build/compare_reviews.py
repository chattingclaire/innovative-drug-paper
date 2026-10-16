from pathlib import Path
import hashlib
import json
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DIMS = [('S', '安全性'), ('E', '有效性'), ('Ec', '经济性'), ('I', '创新性'), ('F', '公平性')]


def display(value):
    return '待定' if value is None else str(value)


def escaped(text):
    return str(text).replace('|', '\\|').replace('\n', '<br>')


def main():
    pairs = json.loads((ROOT / '_build/pairing.json').read_text())
    current = {who: json.loads((ROOT / f'_build/current-text-{who}.json').read_text()) for who in 'AB'}
    for pair in pairs:
        assert current['A'][pair['A']] == current['B'][pair['B']], f"Material pairing mismatch: {pair['A']} / {pair['B']}"
    submitted = {}
    for who in 'AB':
        records = json.loads((ROOT / f'AI复核者{who}/predictions.json').read_text())
        assert len(records) == 200
        submitted[who] = {r['blind_id']: r for r in records}
        assert len(submitted[who]) == 200
    summary = {}
    differences = []
    pending = []
    exact_complete = 0
    for dim, name in DIMS:
        summary[dim] = {'dimension': name, 'n': 200, 'A_1': 0, 'B_1': 0, 'A_pending': 0, 'B_pending': 0, 'both_determined': 0, 'agreement': 0, 'disagreement': 0, 'matrix': {'00': 0, '01': 0, '10': 0, '11': 0}}
    for pair in sorted(pairs, key=lambda p: p['A']):
        all_agree = True
        for dim, name in DIMS:
            a = submitted['A'][pair['A']]['judgments'][dim]
            b = submitted['B'][pair['B']]['judgments'][dim]
            stat = summary[dim]
            stat['A_1'] += a['value'] == 1
            stat['B_1'] += b['value'] == 1
            stat['A_pending'] += a['value'] is None
            stat['B_pending'] += b['value'] is None
            row = {'unit_id': pair['unit_id'], 'A_id': pair['A'], 'B_id': pair['B'], 'dimension': dim, 'dimension_name': name, 'A': a, 'B': b}
            if a['value'] is None or b['value'] is None:
                pending.append(row)
                all_agree = False
            else:
                stat['both_determined'] += 1
                stat['matrix'][f"{a['value']}{b['value']}"] += 1
                if a['value'] == b['value']:
                    stat['agreement'] += 1
                else:
                    stat['disagreement'] += 1
                    differences.append(row)
                    all_agree = False
        exact_complete += all_agree
    decided = sum(s['both_determined'] for s in summary.values())
    agreed = sum(s['agreement'] for s in summary.values())
    overall = {'units': 200, 'judgments_per_reviewer': 1000, 'both_determined': decided, 'agreements': agreed, 'disagreements': len(differences), 'pending_pairs': len(pending), 'agreement_rate': agreed / decided if decided else None, 'all_five_agreed_units': exact_complete}
    result = {'identity': 'AI versus AI, not human inter-rater reliability or full-corpus validation', 'overall': overall, 'by_dimension': summary, 'differences': differences, 'pending': pending}
    (ROOT / '_build/comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    now = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y年%m月%d日 %H:%M')
    rate = f'{agreed / decided:.1%}' if decided else '无法计算'
    lines = [
        '# 200 条 AI 独立复核对照', '', f'整理时间：{now}（北京时间）', '',
        '本文件供管理员在真人首次盲评提交后对照。两份结果由两个分别运行、未互看答案的 AI 复核过程产生；未招募真人专家，也不是两名真人的独立判读。真人纸质盲评仍单独进行。', '',
        '两组均使用原发放材料和同一冻结版共同编码手册，分别按各自盲号顺序判断 200 条 × 5 维。A/B 对应关系只在两组提交后用于对照。没有用两组协商结果替换独立首判。', '',
        '下列一致率仅描述这两次 AI 判读结果，不能作为真人编码信度、机器相对真人的效度，或 4,481 条全量材料的独立验证结果。', '',
        '## 结果概览', '',
        f'- 每组：200 条材料、1,000 个维度判断。',
        f'- 双方均给出 0/1 的判断：{decided} 个，其中一致 {agreed} 个，一致率 {rate}。',
        f'- 明确分歧：{len(differences)} 个维度判断，涉及 {len({r["A_id"] for r in differences})} 条材料；至少一方待定：{len(pending)} 个维度判断，涉及 {len({r["A_id"] for r in pending})} 条材料。',
        f'- 五维全部确定且一致：{exact_complete}/200 条。', '',
        '| 维度 | A 判 1 | B 判 1 | A 待定 | B 待定 | 双方确定 | 一致 | 分歧 | 一致率 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for dim, name in DIMS:
        s = summary[dim]
        pct = f"{s['agreement']/s['both_determined']:.1%}" if s['both_determined'] else '—'
        lines.append(f"| {name} {dim} | {s['A_1']} | {s['B_1']} | {s['A_pending']} | {s['B_pending']} | {s['both_determined']} | {s['agreement']} | {s['disagreement']} | {pct} |")
    lines += ['', '待定不等同于 0；双方待定也不计入已确定判断的一致数。', '', '## 两份完整结果', '']
    for who in 'AB':
        path = ROOT / f'AI复核者{who}/AI复核-{who}-200条.xlsx'
        lines.append(f'- [AI 复核者 {who}：完整 Excel]({path})。D 列为判断，E 列为理由与原文依据；材料文件夹与附件同置，B 列可打开原文。')
    lines += ['', '## 明确分歧', '']
    if not differences:
        lines.append('无。')
    else:
        lines += ['| A 盲号 | B 盲号 | 维度 | A | B |', '|---|---|---|---:|---:|']
        for r in differences:
            anchor = f"{r['A_id'].lower()}-{r['dimension'].lower()}"
            lines.append(f"| [{r['A_id']}](#{anchor}) | {r['B_id']} | {r['dimension_name']} {r['dimension']} | {r['A']['value']} | {r['B']['value']} |")
        for r in differences:
            original = current['A'][r['A_id']].replace('\n', '\n> ')
            link = ROOT / f"AI复核者A/材料/{r['A_id']}.html"
            lines += ['', f"<a id=\"{r['A_id'].lower()}-{r['dimension'].lower()}\"></a>", f"### {r['A_id']} / {r['B_id']} · {r['dimension_name']} {r['dimension']}", '', f"[当前原文及完整语境]({link})", '', f'> {original}', '', f"**A = {r['A']['value']}：** {r['A']['reason']}", '', f"**B = {r['B']['value']}：** {r['B']['reason']}"]
    lines += ['', '## 待定条目', '']
    if not pending:
        lines.append('无。')
    else:
        for r in pending:
            original = current['A'][r['A_id']].replace('\n', '\n> ')
            link = ROOT / f"AI复核者A/材料/{r['A_id']}.html"
            lines += [f"### {r['A_id']} / {r['B_id']} · {r['dimension_name']} {r['dimension']}", '', f"[当前原文及完整语境]({link})", '', f'> {original}', '', f"**A = {display(r['A']['value'])}：** {r['A']['reason']}", '', f"**B = {display(r['B']['value'])}：** {r['B']['reason']}", '']
    lines += ['', '## 核查与留存', '',
              '原始真人材料包和空白工作簿保留。AI 首次提交的原始判读数据及其文件校验值单独留存；本对照不裁决哪一方正确。若后续补材或修订，应另存新版本，保留首次结果。', '',
              '交付前检查包括 200 条盲号完整性、五维逐项覆盖、判断取值、理由非空、原文引文及语境编号核对、Excel 数据逐值比对、材料链接及页面预览。格式和引文检查不等同于全部分类判断已获真人确认。', '']
    (ROOT / 'AI复核对照说明.md').write_text('\n'.join(lines))
    print(json.dumps(overall, ensure_ascii=False))


if __name__ == '__main__':
    main()

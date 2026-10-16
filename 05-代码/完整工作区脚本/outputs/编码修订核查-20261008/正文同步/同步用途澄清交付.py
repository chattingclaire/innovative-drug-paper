from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / '本轮结果'

def binding(p):
    p = Path(p)
    return {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}

prior = ROOT / '澄清人工验证用途前记录' / '当前采用稿交付封存.json'
seal = json.loads(prior.read_text())
review = ROOT / '用途澄清独立核查' / '用途澄清_独立内容与来源核查.json'
assert binding(review)['sha256'] == 'ec8a7aa8f209e97a8abc6988c48a9b7cfc0a01b6ab769e986a86631462725403'
assert json.loads(review.read_text())['status'] == 'PASS_WITHIN_REQUESTED_CONTENT_AND_BYTE_IDENTITY_SCOPE'
visual = ROOT / '用途澄清实际页图核查.json'
assert binding(visual)['sha256'] == '486b7989b60efb3e81566808efbf67f7eb35b7a946e12ac579456b0cf85fce70'
v = json.loads(visual.read_text())
for record in v['documents']:
    assert binding(record['path']) == record

mutated = {'创新药评价的注意力配置差异与协调路径.docx', '创新药评价的注意力配置差异与协调路径.pdf', '编码复核说明与真人检验事项.docx', '编码复核说明与真人检验事项.pdf', '后续验证怎么做.md', '采用文件说明.txt'}
for f in seal['delivered_files']:
    if Path(f['path']).name not in mutated:
        assert binding(f['path']) == f
assert binding(seal['statistics_freeze']['path']) == seal['statistics_freeze']
assert binding(seal['adoption_record']['path']) == seal['adoption_record']

for name, folder in [('创新药评价的注意力配置差异与协调路径', '渲染用途澄清正文'), ('编码复核说明与真人检验事项', '渲染用途澄清说明')]:
    shutil.copy2(ROOT / folder / (name + '.pdf'), OUT / (name + '.pdf'))

index = OUT / '采用文件说明.txt'
text = index.read_text()
text += '\n人工验证用途已澄清：A/B用于抽样句段编码质量检验；同样本注意力分布仅用于辅助诊断误差影响。4481条全文注意力配置由两种机器方法的完整结果分别计算，不要求人工样本占比等于机器全量占比。正文仅3段、说明仅1段文字更新，所有表值、图片、66条参考和95处引用序列保持不变；新变化页已实际查看原图，其余页与此前实际审读图逐字节相同，当前PDF由对应DOCX重新渲染并同步。\n'
index.write_text(text)

seal['status'] = 'PASS_SYNCHRONIZED_ADOPTED_DOCUMENT_PURPOSE_CLARIFICATION_DELIVERY_QA'
seal['scope'] = '同源统计、数值、引用和排版不变核查，并澄清抽样人工编码检验与全语料注意力分布的分工；不是所有指标达标或期刊录用认证。'
seal['previous_delivery_seal'] = binding(prior)
seal['main_current_visual_coverage'] = v['groups'][0]['page_coverage']
seal['memo_current_visual_coverage'] = v['groups'][1]['page_coverage']
seal['memo_visual_report'] = binding(visual)
seal['source_reports'].extend([binding(review), binding(visual)])
delta = ROOT / '人工验证用途澄清记录.json'
seal['correction_records'].append(binding(delta))
changes = json.loads(delta.read_text())['changes']['创新药评价的注意力配置差异与协调路径.docx']
cjk = lambda s: len(re.findall(r'[\u4e00-\u9fff]', s))
seal['main_body_with_tables_CJK_characters'] += sum(cjk(c['new']) - cjk(c['old']) for c in changes if c['paragraph_index'] in (51, 57))
seal['delivered_files'] = [binding(p) for p in sorted(OUT.iterdir()) if p.is_file()]
seal['clarification_only_AB_labels_and_statistics_unchanged'] = True
dest = ROOT / '当前采用稿交付封存.json'
dest.write_text(json.dumps(seal, ensure_ascii=False, indent=2) + '\n')
assert all(binding(x['path']) == x for x in seal['delivered_files'])

plan = ROOT.parents[2] / 'plan.md'
old = plan.read_text()
start, sep, rest = old.partition('\n\n用户最新明确确认')
assert sep
new_start = '## 当前正文与核查状态 2026年10月8日\n\n本节覆盖下方历史交付及待回收描述。唯一当前正文为 `outputs/编码修订核查-20261008/本轮结果/创新药评价的注意力配置差异与协调路径.docx`，SHA256 `2335ad123737735ea5ae32234de323d3c7ae1ac0c23136d4d2eb7a2742b15db6`；说明为同目录 `编码复核说明与真人检验事项.docx`，SHA256 `11a01f77b5830c12f58b8bbc9ce446a273d9af206ea4e9ed2f6bcf8ea8604cbb`。本轮仅澄清主稿3段及说明1段的人工验证用途；数值、全部表格、图片、66参考及95引用序列原样保留，新增[49]仍为上标。正文21页变化8/9/17与说明3页变化2/3均实际审读原图，其他18+1页与此前已实际审读图逐字节相同；两PDF已同步。当前交付封存为 `outputs/编码修订核查-20261008/正文同步/当前采用稿交付封存.json`（SHA256 `' + binding(dest)['sha256'] + '`）。独立内容核查SHA为 `ec8a7aa8f209e97a8abc6988c48a9b7cfc0a01b6ab769e986a86631462725403`。完整规则39与原完整LLM03继续整套采用，07未采用或拼接。旧稿、真实FAIL及旧交付封存保存，交付QA不等于所有指标合格或录用认证。'
plan.write_text(new_start + sep + rest)
print(json.dumps({'delivery_seal': binding(dest), 'main_CJK': seal['main_body_with_tables_CJK_characters'], 'PDFs': [binding(OUT / (name + '.pdf')) for name in ['创新药评价的注意力配置差异与协调路径', '编码复核说明与真人检验事项']], 'all_project_080_targets_met': False}, ensure_ascii=False))

import hashlib
import json
import shutil
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
OUT = ROOT / '09-delivery/agent-review-20261010'
NOW = datetime.now(timezone.utc).isoformat()
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def load(p):
    return json.loads(Path(p).read_text())

def binding(p):
    p = Path(p)
    raw = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def check_file(expected):
    actual = binding(expected['path'])
    assert actual['sha256'] == expected['sha256'], actual['path']
    if expected.get('bytes') is not None:
        assert actual['bytes'] == expected['bytes'], actual['path']
    return actual

verified = []
for folder, expected in [
    ('07-statistics/agent-blind-tables-current-recompute-sol', 'b056803027157b597dd192c8b8ef0652ee513d6749963f38703ba1b87812eaa3'),
    ('07-statistics/agent-modified-table-reference-recompute-sol', 'c5b95c3982b7263b4673a5dce451918f693d8b0d3ba92f92aaf6435c0820d41f'),
]:
    seal_path = ROOT / folder / 'seal.json'
    assert binding(seal_path)['sha256'] == expected
    seal = load(seal_path)
    members = [check_file(x) for x in seal['files']]
    inputs = [check_file(x) for x in load(ROOT / folder / 'input-bindings.json')['inputs']]
    verified.append({'seal': binding(seal_path), 'members_checked': len(members), 'inputs_checked': len(inputs)})

review = load(ROOT / '07-statistics/agent-blind-tables-current-recompute-sol/review-rows.json')
add = load(ROOT / '07-statistics/agent-modified-table-reference-recompute-sol/metrics-addendum.json')
book_checks = []
for coder in ['A', 'B']:
    book = OUT / f'编码复核表-{coder}.xlsx'
    with zipfile.ZipFile(book) as z:
        sst = ET.fromstring(z.read('xl/sharedStrings.xml')) if 'xl/sharedStrings.xml' in z.namelist() else None
        strings = [''.join(x.itertext()) for x in sst] if sst is not None else []
        def values(xml_path):
            cells = {}
            for c in ET.fromstring(z.read(xml_path)).findall('.//s:c', NS):
                v = c.find('s:v', NS)
                if c.get('t') == 's':
                    val = strings[int(v.text)] if v is not None else ''
                elif c.get('t') == 'inlineStr':
                    val = ''.join(c.find('s:is', NS).itertext())
                elif v is not None:
                    val = float(v.text) if c.get('t') not in ('str', 'e', 'b') else v.text
                else:
                    val = ''
                assert c.get('t') != 'e', (book, c.get('r'), val)
                cells[c.get('r')] = val
            return cells
        main = values('xl/worksheets/sheet1.xml')
        source = values('xl/worksheets/sheet2.xml')
        assert not any('真人复核' in str(main.get(f'{c}6', '')) for c in 'ABCDEFGH')
        for i, row in enumerate(review['long_rows'], 7):
            expected = row[coder]['latest']['value']
            assert main[f'A{i}'] == row['id']
            assert main[f'D{i}'] == ('待定' if expected is None else expected)
            assert main[f'E{i}'] == row[coder]['latest']['evidence']['reason']
        # Every substantive original text must survive the XLSX export without truncation.
        by_block = {}
        for cell, val in source.items():
            if cell.startswith('A') and cell[1:].isdigit() and int(cell[1:]) >= 7:
                n = cell[1:]
                block = str(source[f'B{n}']).split(' (')[0]
                by_block.setdefault((val, block), []).append(source.get(f'E{n}', ''))
        for record in review['records']:
            assert ''.join(by_block[(record['id'], '当前条款')]) == record['source']['current_text']
            for ctx in record['source']['contexts']:
                if isinstance(ctx.get('text'), str):
                    assert ''.join(by_block[(record['id'], ctx['context_id'])]) == ctx['text']
        book_checks.append({'coder': coder, 'actual_labels_verified': 385, 'current_clause_texts_verified': 77, 'context_blocks_retained': 642, 'human_extra_columns': 0, 'file': binding(book)})

output_bindings = [binding(OUT / f) for f in ['编码复核表-A.xlsx', '编码复核表-B.xlsx', '指标完整复算.xlsx']]
receipt = {'received_at_utc': NOW, 'input_verification': verified, 'xlsx_export_checks': book_checks,
           'outputs': output_bindings, 'metric_comparisons': 20, 'dimension_comparisons': 100,
           'sklearn_crosschecks': 100, 'actual_modified_AB_used_as_primary_machine_reference': True,
           'root_AI_reference_v3_not_copied_into_A_B': True, 'human_review_executed': False,
           'formal_acceptance': False, 'codex_open_status': 'queued', 'system_default_open_command_exit': 0,
           'original_AI_firsts_changed': False}
(ROOT / 'logs/root-agent-review-delivery-reception-20261010.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2))

baseline = ROOT / '00-baseline/20261010-pre-agent-review-delivery-root-integration'
baseline.mkdir(exist_ok=False)
for name in ['progress.json', 'task_changes.json', '完整Goal指令.md', 'README.md']:
    shutil.copy2(ROOT / name, baseline / name)

p = load(ROOT / 'progress.json')
p['last_integration_at'] = NOW
p['current_user_execution_instruction'] = {
    'primary_request': '先按Agent实际修改A/B表复算全部可算指标，并交付两份可直接改值/理由的表供真人复核；无额外真人复核栏。',
    'final_goal_unchanged': True,
    'correctness_method': 'κ仅衡量一致性；用理论操作定义、完整原文、人工复核核定参照，并用未参与开发的材料检验两机器分类指标。相同κ不等于同样误判；同范围二者对参照κ=1时三者应逐项一致。',
    'cleanup': '只完成候选清单；16个未见绑定缓存共551534B，未删除或移动原过程文件。',
}
p['agent_modified_tables_current_recompute_actual'] = {
    'receipt': 'logs/root-agent-review-delivery-reception-20261010.json', 'outputs': output_bindings,
    'N_records': 77, 'N_dimension_rows_per_coder': 385, 'actual_later_rejudgments': 6,
    'historical_rows_without_new_rejudgment': 71, 'AB_kappa': {d: 1 for d in ['S', 'E', 'Ec', 'I', 'F']},
    'rule77_vs_actual_modified_A_S': add['comparisons'][0]['dimensions']['S']['metrics'],
    'human_review_executed': False, 'formal_acceptance': False, 'full_paper_started': False,
}
for step in p['steps']:
    if step['step'] == 5:
        step['status'] = 'actual_agent_modified_tables_recomputed_and_delivered_formal_validation_incomplete'
        for f in ['07-statistics/agent-blind-tables-current-recompute-sol/seal.json', '07-statistics/agent-modified-table-reference-recompute-sol/seal.json', 'logs/root-agent-review-delivery-reception-20261010.json']:
            if f not in step['completed_evidence']:
                step['completed_evidence'].append(f)
p['parallel_tasks_current_finite'] = {'agent_tables_metrics_and_cleanup': 'completed; root outputs received and verified', 'native_creation_bridge': 'technical report produced; no new policy coding executed'}
p['current_goal_turn_classification'] = {'classification': 'progress', 'evidence': '已有Agent表20组、100逐维比较完成算术复算和独立软件核对；3份真实XLSX已生成并完成导出值/原文与视觉检查。', 'formal_acceptance': False, 'human_review_executed': False, 'pending_finite_agents': 0}
(ROOT / 'progress.json').write_text(json.dumps(p, ensure_ascii=False, indent=2))
t = load(ROOT / 'task_changes.json')
t['changes'].append({'date': '2026-10-10', 'evidence': '用户要求先按Agent修改盲评表算所有指标，打开实际表；真人直接改对应值，不加真人复核栏；询问κ、一致性与效度、三者关系及过程文件清理。',
    'adjustment': '交付A/B实际77条、385维度行，原文/语境另页；保留原首件。机器主指标相对实际latest A/B，另行ROOT v3只作附表，不覆盖A/B。建立缓存候选清单，保留绑定材料。',
    'reason': '直接满足当前可复核交付，并解决参照版本改变会改变数值的口径问题。κ=1只说明保存值一致，未转成正式效度通过。',
    'invariants': ['最终完整论文目标及八步不变', '项目阈值不变', 'AI身份与实际真人复核分别报告', '原始首判、来源、失败和统计复现保留'],
    'unfinished': ['真人原文复核与同版可信参照', '冻结后独立检验和机器完整检验', '稳定性、区间及聚合稳健性', '指标合规后完整论文修订']})
(ROOT / 'task_changes.json').write_text(json.dumps(t, ensure_ascii=False, indent=2))
instruction = '\n\n当前执行补充（2026-10-10，用户最新要求）：先按照Agent实际修改后的A/B表完成全部可算指标，交付可直接编辑现有编码值和理由的A/B工作簿，不另加真人复核栏。保留修改前AI首件和版本；真人改完后另行保存实际复核版本并重算，不把事后复核写成独立真人首判。机器主比较使用这些实际A/B值，其他裁定参照只作明确标注的对照，不能复制其值来提高A/B一致性。κ=1只表示可判范围上的完全一致，相同κ数值不代表相同错误；正确性证据还需要理论定义、政策原文、可信人工参照及未参与开发材料上的分类检验。未达标与NA如实保留，最终阈值及完整八步论文目标不变。过程文件清理以不损害原始记录、统计复现和封存路径为前提；当前只列缓存候选。\n'
with (ROOT / '完整Goal指令.md').open('a') as f:
    f.write(instruction)
entry = '当前交付入口：09-delivery/agent-review-20261010。两份A/B表各含77条、385项编码，直接改D列编码值、E列理由；没有额外真人复核栏。指标完整复算.xlsx主视图按实际Agent修改A/B作参照，历史及ROOT v3结果另列；仍有未达标项，正式验收和全文写作未完成。全部原始AI首件和版本保留。\n\n'
readme = (ROOT / 'README.md').read_text()
(ROOT / 'README.md').write_text(entry + readme)
print(json.dumps({'verified_outputs': len(output_bindings), 'dimension_comparisons': 100, 'book_checks': book_checks, 'goal_status': 'active', 'formal_acceptance': False}, ensure_ascii=False))

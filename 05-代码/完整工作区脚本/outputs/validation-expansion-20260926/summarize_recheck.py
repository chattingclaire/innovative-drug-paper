"""Verify and describe supplemental development reviews; never merge into reliability."""
import hashlib, json
from pathlib import Path
from datetime import datetime

OUT = Path(__file__).parent
DIMS = ('S', 'E', 'Ec', 'I', 'F')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text())
original_hashes = {
    'A': 'ecb6e15a74135eca4587d2ee6b9361e6766dc750e7d249bfe6088d7ac7b54af1',
    'C': 'b04f35a825d13cae8d0a45c53c0351425462e57388eb8fb251924eb398522c9d',
}
packets = [OUT / f'agent-{c}/补充材料5-v2.json' for c in 'AC']
assert sha(packets[0]) == sha(packets[1])
source = {r['id']: r for r in load(packets[0])['rows']}
results, files = {}, {}
for c in 'AC':
    d = OUT / f'agent-{c}'
    assert sha(d / f'result-{c}.json') == original_hashes[c]
    path = d / f'补充复核5-v2-{c}.json'
    data = load(path)
    assert data['coder'] == c and data['protocol_acknowledged'] is True
    assert data['protocol_version'] == 'CAL-5D-20260926-v1.2'
    rows = {r['id']: r for r in data['rows']}
    assert len(rows) == len(data['rows']) == 5 and set(rows) == set(source)
    for k, r in rows.items():
        assert r['text'] == source[k]['text']
        assert set(r['labels']) == set(DIMS)
        assert all(type(v) is int and v in (0, 1) or v == '待定' for v in r['labels'].values())
        assert all(isinstance(r['dimension_reasons'].get(x), str) and r['dimension_reasons'][x].strip() for x in DIMS)
        assert r['evidence'].strip() and r['rationale'].strip()
        assert r['input_assessment']['basis'].strip()
        if r['input_assessment']['status'] != 'sufficient':
            assert all(v == '待定' for v in r['labels'].values())
        for dim, field in [('I', 'innovation_subtypes'), ('F', 'fairness_subtypes')]:
            assert bool(r[field]) == (r['labels'][dim] == 1)
    results[c] = rows
    files[c] = {'path': str(path), 'sha256': sha(path), 'completed_at': data['completed_at']}
rows = []
for k in sorted(source):
    a, c = results['A'][k], results['C'][k]
    rows.append({'id': k, 'A': a['labels'], 'C': c['labels'],
                 'labels_equal': a['labels'] == c['labels'],
                 'subtypes_equal': all(a[x] == c[x] for x in ('innovation_subtypes', 'fairness_subtypes', 'safety_quality_basis')),
                 'both_report_gap_resolved': all(r['input_assessment'].get('original_gap_resolved') is True for r in (a, c))})
report = {'status': 'completed_development_recheck_only', 'created_at': datetime.now().astimezone().isoformat(),
          'protocol_version': 'CAL-5D-20260926-v1.2', 'same_packet_sha256': sha(packets[0]),
          'files': files, 'original_raw_60_hashes_unchanged': original_hashes, 'rows': rows,
          'not_new_independent_reliability': True, 'do_not_merge_with_original_60_metrics': True,
          'interpretation': '两次提供材料及规则版本不同；5条复核不能回填原始盲评、不能计算商议后信度或冒充5条新样本。'}
dest = OUT / '补充5条开发复核-核验.json'
if dest.exists(): raise RuntimeError('Preserve issued report')
dest.write_text(json.dumps(report, ensure_ascii=False, indent=2))
md = ['# 5条补充材料后的开发复核', '',
      'A和C分别收到相同补充原文语境及v1.2协议，均独立完成。5条五维与来源子类型相同，均认为原材料缺口已消解。这是对原样本的开发复核，不是新增5条或新的独立信度验证；原60条JSON、工作簿和首轮统计保持原样。', '',
      '| 编号 | A：S/E/Ec/I/F | C：S/E/Ec/I/F | 补全内容 |', '|---|---|---|---|']
desc = {'DEV60-013': '同年A为纳入支付范围药品费用与预算的比值', 'DEV60-016': '左侧药品基本信息填写提示与右侧示例的区别',
        'DEV60-034': '组织评审引导句后四项另存单元及完整边界', 'DEV60-045': '创新性填写提示与右侧示例的区别',
        'DEV60-046': '同年A为基金实际支出与预算的比值'}
for r in rows:
    md.append('| ' + ' | '.join([r['id'], '/'.join(map(str, r['A'].values())), '/'.join(map(str, r['C'].values())), desc[r['id']]]) + ' |')
md += ['', 'DEV60-045的既往专项支持身份信息，两位均仅登记创新属性资料（attribute），未把本句当作新增研发支持安排。双方提出相同的子类型表述疑问，可在正式冻结前明确“既往支持身份信息”与“实际支持措施”的边界，原记录不改。', '',
       '原60条中的两处二元分歧（DEV60-030、032）仍保存在首轮记录中；v1.2虽已明确未来适用边界，不能据此把首轮一致率改成100%。', '',
       '来源、原文一致性、共同材料哈希和原始60条未改动证明见同目录“补充5条开发复核-核验.json”；逐维理由见两位评审各自“补充复核5-v2-A/C.json”。']
(OUT / '补充5条开发复核说明.md').write_text('\n'.join(md) + '\n')
print(json.dumps({'rows': len(rows), 'same': sum(r['labels_equal'] for r in rows), 'raw_60_preserved': True}, ensure_ascii=False))

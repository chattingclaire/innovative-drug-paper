"""Read-only audit of saved old4481 against existing human-confirmed material.

No inference, label revision, sampling, or manuscript edits. New200 is supplementary
independent human validation per user correction on 2026-10-14; original77 is calibration.
"""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / '旧版现有证据核查'
DIMS = ('S', 'E', 'Ec', 'I', 'F')
NAMES = dict(zip(DIMS, ('安全性', '有效性', '经济性', '创新性', '公平性')))
DEPTS = {'NMPA': '药监局', 'NHSA': '医保局', 'NHC': '卫健委'}

def read(p):
    return json.loads(Path(p).read_text())

def lines(p):
    return [json.loads(s) for s in Path(p).read_text().splitlines()]

def binding(p):
    p = Path(p).resolve()
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

def verify(b):
    assert binding(b['path']) == {k: b[k] for k in ('path', 'bytes', 'sha256')}, b['path']

def metrics(cells):
    a, b, c, t = map(Fraction, cells)
    n = a+b+c+t
    div = lambda x, y: x/y if y else None
    pe = div((a+b)*(a+c)+(c+t)*(b+t), n*n)
    result = {'kappa': None if not n else div((a+t)/n-pe, 1-pe),
              'precision': div(a, a+b), 'recall': div(a, a+c), 'F1': div(2*a, 2*a+b+c)}
    return {k: None if v is None else float(v) for k, v in result.items()}

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

cal = read(HERE/'原77条复算.json')
machines = {}
inputs = {'original77_recheck': binding(HERE/'原77条复算.json')}
for method in ('rule', 'LLM'):
    b = cal['source_bindings']['full4481_'+method]
    verify(b)
    rows = lines(b['path'])
    assert len(rows) == len({r['id'] for r in rows}) == 4481
    machines[method] = {r['id']: r for r in rows}
    inputs[method] = b
    for row in rows:
        assert set(row['labels']) == set(DIMS)
        for d, value in row['labels'].items():
            assert value is None or type(value) is int and value in (0, 1)
            assert row['decisions' if method == 'rule' else 'dimensions'][d]['value'] == value
        if method == 'rule':
            assert not row.get('implementation_errors')
assert machines['rule'].keys() == machines['LLM'].keys()

issued = ROOT/'09-delivery/独立真人判读-200条-20261013/管理员留存-勿发编码者'
human_dir = ROOT/'09-delivery/真人核验确认-200条-20261013'
freeze, draw = read(issued/'sampling-freeze.json'), read(issued/'draw.json')
verify(draw['sampling_freeze_binding'])
for b in [freeze['manual'], freeze['source_bindings'], freeze['inputs']['metadata_frame']]:
    verify(b)
human = read(human_dir/'真人核验结果.json')
correction = read(HERE/'人工独立检验记录更正-20261014.json')
assert correction['independent_human_validation'] is True
humans = {r['unit_id']: r for r in human['records']}
sample = {r['unit_id']: r for r in draw['records']}
assert len(humans) == len(sample) == 200 and humans.keys() == sample.keys()
assert sum(Fraction(r['sampling_weight_exact']) for r in sample.values()) == 1151
assert (human_dir/'共同编码手册.txt').read_bytes() == Path(freeze['manual']['path']).read_bytes()
meta = {r['source_id']: r for r in lines(freeze['inputs']['metadata_frame']['path'])}
assert set(meta) == set(machines['rule'])
assert not (set(sample) & set(freeze['excluded_source_ids']))
original77 = {r['id'] for r in lines(cal['source_bindings']['calibration_rule']['path'])}
assert not (set(sample) & original77)
for h in humans.values():
    assert set(h['judgments']) == set(DIMS)
    assert all(type(v['value']) is int and v['value'] in (0,1) for v in h['judgments'].values())

packets = {r['source_id']: r for r in read(freeze['source_bindings']['path'])}
packet_checks, texts = [], {}
for rid in sorted(sample):
    old = machines['LLM'][rid]['packet']
    new = {k: packets[rid][k] for k in ('path', 'bytes', 'sha256')}
    verify(old); verify(new)
    a, b = Path(old['path']).read_bytes(), Path(new['path']).read_bytes()
    packet_checks.append({'id': rid, 'old': old, 'reference_material': new, 'byte_equal': a == b})
    texts[rid] = read(old['path'])['source_bundle']['source_record']['text']
assert all(x['byte_equal'] for x in packet_checks)

inputs.update({'draw': binding(issued/'draw.json'), 'freeze': binding(issued/'sampling-freeze.json'),
               'reference': binding(human_dir/'真人核验结果.json'), 'reference_description': binding(human_dir/'提交说明.txt'),
               'manual': freeze['manual'], 'metadata': freeze['inputs']['metadata_frame'],
               'user_provenance_correction': binding(HERE/'人工独立检验记录更正-20261014.json'), 'script': binding(__file__)})
comparisons, differences = [], []
for method in machines:
    for d in DIMS:
        cells, wcells, nulls = [0]*4, [Fraction(0)]*4, []
        for rid, s in sample.items():
            m, h = machines[method][rid]['labels'][d], humans[rid]['judgments'][d]['value']
            w = Fraction(s['sampling_weight_exact'])
            if m is None:
                nulls.append(rid)
            else:
                i = {(1,1):0, (1,0):1, (0,1):2, (0,0):3}[m,h]
                cells[i] += 1; wcells[i] += w
            if m != h:
                decision = machines[method][rid]['decisions' if method == 'rule' else 'dimensions'][d]
                differences.append({'id': rid, 'A_id': humans[rid]['A_id'], 'department': s['department'],
                                    'method': method, 'dimension': d, 'machine_value': m, 'reference_value': h,
                                    'type_relative_to_reference': 'NULL' if m is None else 'FP' if m else 'FN',
                                    'weight': str(w), 'text': texts[rid], 'machine_decision': decision,
                                    'reference_judgment': humans[rid]['judgments'][d],
                                    'status': '待按共同标准核查；分歧不自动认定机器错误'})
        assert sum(cells)+len(nulls) == 200
        comparisons.append({'method': method, 'dimension': d, 'sample_N': 200, 'binary_N': sum(cells),
                            'null_ids': nulls, 'TP_FP_FN_TN': cells, 'raw_metrics': metrics(cells),
                            'design_weighted_cells_exact': list(map(str, wcells)),
                            'design_weighted_metrics': metrics(wcells)})

full = []
for method, data in machines.items():
    for dept in ('ALL', 'NMPA', 'NHSA', 'NHC'):
        ids = [rid for rid in data if dept == 'ALL' or meta[rid]['department'] == dept]
        counts = {d: sum(data[r]['labels'][d] == 1 for r in ids) for d in DIMS}
        nulls = {d: sum(data[r]['labels'][d] is None for r in ids) for d in DIMS}
        denom = sum(counts.values())
        full.append({'method': method, 'department': dept, 'N': len(ids), 'positive_counts': counts,
                     'null_counts': nulls, 'positive_label_total': denom,
                     'share_among_known_positive_labels': {d: counts[d]/denom for d in DIMS},
                     'rank': sorted(DIMS, key=lambda d: -counts[d])})

report = {'role': '旧版已保存输出与既有独立人工检验的对照；人工来源按用户2026-10-14纠正认定',
          'reference_process': correction, 'superseded_reference_process_record': human['confirmation'], 'scope': {'sample_N': 200, 'sampling_frame_N': 1151,
          'full_N': 4481, 'original77_overlap': 0, 'registered_exposed_overlap': 0,
          'material_byte_equal_N': 200, 'reference_independent_of_AI': True, 'independence_basis': 'user_correction_20261014',
          'retrospective_old_version_comparison': True, 'model_calls': 0, 'source_labels_modified': False},
          'source_bindings': inputs, 'comparisons': comparisons, 'full_descriptive_counts': full,
          'difference_dimension_slots': len(differences), 'difference_records': len({x['id'] for x in differences})}
OUT.mkdir(exist_ok=True)
save('核查结果.json', report)
save('逐项分歧.json', differences)
save('200条材料一致性.json', packet_checks)
fmt = lambda v: '—' if v is None else f'{v:.3f}'
md = ['# 旧版现有证据核查', '',
      '锁定77条校准后首次成功的4481条全量结果。本次仅读取保存文件并重算统计，模型调用0次，未修改机器标签、人工结果或论文。', '',
      '## 已确认的证据范围', '',
      '- 原77条校准结果保留；本批200条与77条没有记录重叠，也不在现有开发暴露登记的排除名单内。',
      '- 200条旧版LLM输入包与后来核验所用材料逐文件字节一致；共同编码手册一致。',
      '- 用户2026年10月14日明确纠正：本批为真人完成的独立检验，旧有AI辅助来源记录错误。本核查据此认定独立人工参照；不改任何人工标签，不据整合标签反推两位编码者的初始一致性。',
      '- 本次为回看旧版的补充诊断。200条来自1151条抽样框，不代表全部4481条；其余材料不由本次推算准确率。', '',
      '## 现成人工参照对照', '',
      '原始指标描述实际200条；设计加权指标对应原1151条抽样框。NULL单列，未改成0。这里的FP/FN均是相对人工核验参照的分歧，尚不等于逐条裁定后的错误。', '',
      '|方法|维度|可比/待定|TP/FP/FN/TN|原始κ|原始P|原始R|原始F1|加权κ|加权P|加权R|加权F1|',
      '|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in comparisons:
    md.append('|'+ '|'.join([x['method'], NAMES[x['dimension']], f"{x['binary_N']}/{len(x['null_ids'])}",
                            '/'.join(map(str,x['TP_FP_FN_TN'])),
                            *[fmt(x[k][m]) for k in ('raw_metrics','design_weighted_metrics') for m in ('kappa','precision','recall','F1')]])+'|')
md += ['', '## 旧版4481条全量描述', '',
       '下表为五维已识别正标签内部的分布，不是编码准确率；同一记录可有多个标签。机器待定另外保留。', '',
       '|方法|部门|记录数|安全性|有效性|经济性|创新性|公平性|五维排序|',
       '|---|---|---:|---:|---:|---:|---:|---:|---|']
for x in full:
    md.append('|'+ '|'.join([x['method'], DEPTS.get(x['department'],'全库'), str(x['N']),
                            *[f"{x['positive_counts'][d]}（{100*x['share_among_known_positive_labels'][d]:.2f}%）" for d in DIMS],
                            '>'.join(NAMES[d] for d in x['rank'])])+'|')
md += ['', f"共定位到{len(differences)}项机器—参照分歧，涉及{len({x['id'] for x in differences})}条记录；相同记录在两种方法中可能重复出现。逐项原文、机器理由、人工参照理由见逐项分歧.json。", '',
       '## 解释边界', '',
       '全量完成和部门排序接近，均不能替代人工准确性证据。旧版完整输出中的未决项需要保留；本次尚未逐项裁定分歧，也未声称完成误差纠正后的结论检验。', '',
       '后续应先按既有共同手册裁定影响核心结论的分歧，明确机器漏判、机器误判、参照待复核及材料不足；不能为了提高指标改判，也不能将同一手册执行失误写成两套标准。', '']
(OUT/'核查说明.md').write_text('\n'.join(md))
print(json.dumps({'comparisons': comparisons, 'full': full, 'difference_slots': len(differences),
                  'difference_records': len({x['id'] for x in differences}), 'out': str(OUT)}, ensure_ascii=False, indent=2))

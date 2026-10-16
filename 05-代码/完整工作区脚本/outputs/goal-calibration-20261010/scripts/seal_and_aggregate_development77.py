"""Verify actual submission seals and aggregate two development batches only."""
import hashlib
import importlib.util
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('exact_math', ROOT/'scripts/audit_pilot.py')
math = importlib.util.module_from_spec(spec)
spec.loader.exec_module(math)
DIMS = ('S', 'E', 'Ec', 'I', 'F')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load_rows = lambda p: [json.loads(s) for s in p.read_text().splitlines() if s.strip()]

def write_new(p, value):
    with p.open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def main():
    destination = ROOT/'04-calibration/development77-v11'
    destination.mkdir(exist_ok=True)
    assert not (destination/'aggregate.json').exists(), 'Do not overwrite a sealed audit'
    departments = {r['id']: r['analysis_group'] for r in load_rows(ROOT/'00-baseline/source-only-frame.jsonl')}
    combined = []
    seals = []
    manual_hashes = set()
    input_hashes = []
    for batch in ('pilot02', 'coverage01'):
        directory = ROOT/'04-calibration'/batch
        mapping = json.loads((directory/'admin/private_mapping.json').read_text())
        diagnostic = json.loads((directory/'admin/diagnostics.json').read_text())
        assert not diagnostic['quality_issues']
        by_coder = {}
        for coder in 'AB':
            p = directory/coder
            s = json.loads((p/'submission.json').read_text())
            identity = s['identity']
            assert identity == 'AI' or identity.get('type') == 'AI'
            output = s.get('output', {}).get('labels.jsonl', {})
            assert s.get('sealed') is True or output.get('sealed') is True
            stated = s.get('output_labels_sha256') or output.get('sha256')
            assert stated == sha(p/'labels.jsonl')
            for name, expected in s['input_sha256'].items():
                assert sha(p/name) == expected, (batch, coder, name)
            labels = load_rows(p/'labels.jsonl')
            assert len(labels) == s['record_count']
            assert 5*len(labels) == s['dimension_count']
            assert len({r['id'] for r in labels}) == len(labels)
            m = {r['blind_id']: r for r in mapping if r['coder'] == coder}
            assert set(m) == {r['id'] for r in labels}
            by_coder[coder] = {m[r['id']]['frame_id']: r for r in labels}
            manual_hashes.add(sha(p/'manual.md'))
            for name in ('manual.md','packet.jsonl','labels.jsonl','submission.json'):
                input_hashes.append({'path': str((p/name).relative_to(ROOT)), 'sha256': sha(p/name)})
            seals.append({'batch': batch, 'coder': coder, 'identity': 'AI',
                          'input_hashes_verified': True, 'output_seal_hash_verified': True,
                          'n': len(labels), 'submission_sha256': sha(p/'submission.json')})
        assert set(by_coder['A']) == set(by_coder['B'])
        for fid in sorted(by_coder['A']):
            combined.append({'frame_id': fid, 'batch': batch, 'department': departments[fid],
                             'A': by_coder['A'][fid]['labels'], 'B': by_coder['B'][fid]['labels']})
    assert len(manual_hashes) == 1
    assert len(combined) == 77 == len({r['frame_id'] for r in combined})
    groups = {'all77': combined}
    for batch in ('pilot02','coverage01'):
        groups[batch] = [r for r in combined if r['batch'] == batch]
    for department in ('NMPA','NHSA','NHC'):
        groups[department] = [r for r in combined if r['department'] == department]
        for batch in ('pilot02','coverage01'):
            groups[f'{batch}/{department}'] = [r for r in groups[department] if r['batch'] == batch]
    metrics = {}
    for name, rows in groups.items():
        metrics[name] = {}
        for dim in DIMS:
            cells = [0,0,0,0]
            nine = Counter()
            for r in rows:
                a, b = r['A'][dim], r['B'][dim]
                nine[f'{a if a is not None else "null"}|{b if b is not None else "null"}'] += 1
                if a is not None and b is not None:
                    cells[2*a+b] += 1
            m = math.statistics(*cells)
            m.update({'total_n': len(rows), 'pending_n': len(rows)-sum(cells),
                      'full_3x3': {f'{a}|{b}': nine[f'{a}|{b}'] for a in ('0','1','null') for b in ('0','1','null')},
                      'CI95': None, 'population_inference': False,
                      'undefined_kappa_reason': 'A/B both constant or empty' if m['kappa'] is None else None})
            metrics[name][dim] = m
    result = {'status': 'AI_development_only', 'n': 77, 'dimension_pairs': 385,
              'roles': {'pilot02': '41 prior calibration cases rejudged after discussion and material repair',
                        'coverage01': '36 other historically exposed cases, 12 per department, common manual first execution'},
              'manual_sha256': next(iter(manual_hashes)), 'identity': 'AI',
              'new_heldout_development_units': 0, 'human_independent_validation_completed': False,
              'machine_validity_completed': False, 'final_acceptance': False,
              'probability_sample': False, 'weights': None, 'metrics': metrics,
              'seals': seals, 'inputs': input_hashes,
              'created_at_utc': datetime.now(timezone.utc).isoformat()}
    write_new(destination/'aggregate.json', result)
    write_new(destination/'mapped-labels.json', combined)
    lines = ['# 77条共同手册开发执行诊断', '',
             '41条为讨论、补材和修复后重判；36条为另外的历史开发材料，每部门12条。双方均为AI，首判/讨论/重判分别归档。这一合表只检查开发执行，不是真人信度、冻结后检验或机器效度。', '',
             '|范围|n|S κ|E κ|Ec κ|I κ|F κ|', '|---|---:|---:|---:|---:|---:|---:|']
    fmt = lambda v: 'NA' if v is None else f'{v:.4f}'
    for name in ('all77','pilot02','coverage01','NMPA','NHSA','NHC'):
        lines.append('|'+name+'|'+str(len(groups[name]))+'|'+ '|'.join(fmt(metrics[name][d]['kappa']) for d in DIMS)+'|')
    lines += ['', '各维全部可判，没有分歧。合表正例为S=8、E=14、Ec=16、I=21、F=13；可判数均为77。36条覆盖批次的F全部为0，κ和正类一致性均为NA；不能填成1。部门/批次四格与各维未知九格见JSON。', '',
              '没有总体概率抽样，故不报告总体95%区间或设计权重。没有把开发一致性作为最终验收；后续须检查共同误判、机器实际运行及真实独立编码。']
    with (destination/'aggregate.md').open('x') as stream:
        stream.write('\n'.join(lines)+'\n')
    print(json.dumps({'n':77,'sealed_submissions':len(seals),
                      'all77': {d:{k:metrics['all77'][d][k] for k in ('A_1','B_1','kappa')} for d in DIMS}},ensure_ascii=False))

if __name__ == '__main__':
    main()

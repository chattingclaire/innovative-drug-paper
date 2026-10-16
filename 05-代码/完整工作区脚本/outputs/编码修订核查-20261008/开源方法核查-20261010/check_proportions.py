"""Read-only diagnostics of the frozen current predictions; never changes labels."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parent
BUNDLE = W / '统计复算/实质关系修复/当前同材料结果/同材料结果绑定.json'
DIMS = ('S', 'E', 'Ec', 'I', 'F')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_bound(record):
    assert sha(record['path']) == record['sha256'], record['path']
    rows = [json.loads(line) for line in Path(record['path']).read_text().splitlines()]
    result = {r['id']: r for r in rows}
    assert len(result) == len(rows)
    return result

def fractions(counts, n):
    total = sum(counts.values())
    return {
        'units_n': n, 'dimension_counts': dict(counts), 'dimension_count_total': total,
        'attention_share_percent': {d: 100 * counts[d] / total if total else None for d in DIMS},
        'unit_coverage_percent': {d: 100 * counts[d] / n if n else None for d in DIMS},
    }

binding = json.loads(BUNDLE.read_text())
frame = read_bound(binding['frame'])
rule = read_bound(binding['rule_output'])
llm = read_bound(binding['llm_output'])
assert set(rule) == set(llm)
assert set(frame) - set(rule) == set(binding['known_source_unknown_ids'])
assert len(rule) == binding['executed_n'] == 4480
out = {
    'date': '2026-10-10',
    'status': 'descriptive_source_composition_diagnostic_not_validation_or_adopted_results',
    'bundle': {'path': str(BUNDLE), 'sha256': sha(BUNDLE)},
    'script_sha256': sha(__file__),
    'target_n': len(frame), 'executed_n': len(rule),
    'unknown_ids': sorted(set(frame) - set(rule)),
    'grouping': 'frame.source_position.source_file; source-file groups, not asserted independent legal instruments',
    'notes': [
        'Attention shares use sum of five dimension counts, not all policy units.',
        'Each unit can count in multiple dimensions; each dimension counts once per unit.',
        'Source omission is a descriptive sensitivity calculation, not deletion from the study or a confidence interval.',
        'Corpus inclusion criteria and repeated annual versions still require substantive justification.',
        'No original inputs, labels, human references, codebook or manuscript are changed.',
    ], 'methods': {},
}
for name, predictions in [('rule', rule), ('llm', llm)]:
    departments = {}
    for dept in ('NMPA', 'NHSA', 'NHC'):
        ids = [i for i in predictions if frame[i]['analysis_group'] == dept]
        total = Counter({d: 0 for d in DIMS})
        groups = defaultdict(list)
        for i in ids:
            groups[frame[i]['source_position']['source_file']].append(i)
        records = []
        for source, group_ids in sorted(groups.items()):
            counts = Counter({d: 0 for d in DIMS})
            for i in group_ids:
                labels = predictions[i]['result']['labels'] if name == 'rule' else predictions[i]['labels']
                assert set(labels) == set(DIMS) and all(v in (0, 1) for v in labels.values())
                counts.update(labels)
            total.update(counts)
            records.append({'source_file': source, 'ids': group_ids, **fractions(counts, len(group_ids))})
        main = fractions(total, len(ids))
        assert abs(sum(main['attention_share_percent'].values()) - 100) < 1e-9
        for rec in records:
            remaining = {d: total[d] - rec['dimension_counts'][d] for d in DIMS}
            omitted = fractions(remaining, len(ids) - rec['units_n'])
            rec['after_omitting_this_source_group'] = omitted
            rec['share_of_department_dimension_counts_percent'] = {
                d: 100 * rec['dimension_counts'][d] / total[d] if total[d] else None for d in DIMS}
        departments[dept] = {**main, 'source_groups_n': len(records), 'source_groups': records}
    out['methods'][name] = departments

target = HERE / '占比分母与来源构成核查.json'
assert not target.exists(), 'Preserve the previous diagnostic; do not overwrite silently.'
target.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'written': str(target), 'sha256': sha(target)}, ensure_ascii=False))
for method, departments in out['methods'].items():
    for dept, values in departments.items():
        print(method, dept, values['units_n'], values['dimension_counts'], values['dimension_count_total'])
nhc = out['methods']['llm']['NHC']
top = max(nhc['source_groups'], key=lambda x: x['dimension_counts']['F'])
print(json.dumps({'NHC_F_largest_source': top['source_file'], 'F_count': top['dimension_counts']['F'],
                  'department_F_count': nhc['dimension_counts']['F'],
                  'share_before': nhc['attention_share_percent']['F'],
                  'share_after_omission': top['after_omitting_this_source_group']['attention_share_percent']['F']}, ensure_ascii=False))

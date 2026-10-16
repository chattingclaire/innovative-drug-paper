"""Descriptive developer diagnostics; never independent performance claims."""
import hashlib
import json
from pathlib import Path
import baseline_candidate17 as baseline
import policy_coding_v25 as candidate

HERE = Path(__file__).resolve().parent
DIMS = baseline.DIMENSIONS

def metrics(rows, coder, version, common=False):
    result = {}
    for d in DIMS:
        confusion = dict(TP=0, FP=0, FN=0, TN=0)
        weighted = dict(TP=0., FP=0., FN=0., TN=0.)
        pending_reference = pending_machine = 0
        for row in rows:
            y = row['original_references'][coder]['labels'][d]
            pred = row[version]['labels'][d]
            if type(y) is not int or y not in (0, 1):
                pending_reference += 1
                continue
            if common and any(type(row[v]['labels'][d]) is not int for v in ['baseline_frozen', 'v25']):
                pending_machine += 1
                continue
            if type(pred) is not int or pred not in (0, 1):
                pending_machine += 1
                continue
            cell = ('T' if y == pred else 'F') + ('P' if pred else 'N')
            confusion[cell] += 1
            h = row['historical_sampling']
            weighted[cell] += h['N_h']/h['n_h']
        def scores(count):
            tp, fp, fn, tn = (count[k] for k in ['TP', 'FP', 'FN', 'TN'])
            return {'precision': tp/(tp+fp) if tp+fp else None,
                    'recall': tp/(tp+fn) if tp+fn else None,
                    'f1': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
                    'n_or_weight_sum': tp+fp+fn+tn}
        result[d] = {'counts': confusion, 'unweighted': scores(confusion),
                     'historical_design_weighted_descriptive': scores(weighted),
                     'weighted_counts': weighted, 'reference_pending': pending_reference,
                     'machine_pending_with_known_reference': pending_machine}
    return result

def main():
    rows = [json.loads(s) for s in (HERE/'development_v600.jsonl').read_text().splitlines()]
    changes = []
    for r in rows:
        restored = baseline.code_unit(r['input'])
        assert restored['labels'] == r['baseline_frozen']['labels'], r['id']
        r['v25'] = candidate.code_unit(r['input'])
        for e in r['v25']['evidence']:
            assert r['input']['unit_text'][e['start']:e['end']] == e['text'], (r['id'], e)
        if r['v25']['labels'] != restored['labels']:
            changes.append({'id': r['id'], 'original_id': r['input']['review_id'],
                'text': r['input']['unit_text'], 'old': restored['labels'], 'new': r['v25']['labels'],
                'A_original': r['original_references']['A']['labels'],
                'C_original': r['original_references']['C']['labels'],
                'evidence': r['v25']['evidence'], 'suppressions': r['v25']['suppressions']})
    report = {'status': 'post_tuning_development_diagnostic_not_independent_validation',
              'n': len(rows), 'baseline_reproduction_all_600_labels_match': True,
              'candidate_version': candidate.VERSION, 'changed_units': len(changes),
              'manual_or_reference_labels_changed': False,
              'candidate_review_flags': [{'id':r['id'],'flags':r['v25']['review_flags']}
                                         for r in rows if r['v25']['review_flags']],
              'metrics': {c: {v: metrics(rows,c,v) for v in ['baseline_frozen','v25']} for c in ['A','C']},
              'paired_common_determinate_metrics': {c: {v: metrics(rows,c,v,True) for v in ['baseline_frozen','v25']} for c in ['A','C']},
              'limits': ['Observed examples influenced development; no new confidence intervals or validation pass.',
                         'Both AI references remain separate and may share mistakes.',
                         'Historical weights are descriptive after tuning, not unbiased generalization estimates.',
                         'Pending values and their coverage remain explicit; no accuracy gain by relabeling references.'],
              'code_hashes': {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'baseline_candidate17.py',HERE/'policy_coding_v25.py',HERE/'protocol-v1.3.md']}}
    (HERE/'development_diagnostics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (HERE/'development_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
    (HERE/'development_predictions.jsonl').write_text(''.join(json.dumps({'id':r['id'],'result':r['v25']},ensure_ascii=False)+'\n' for r in rows))
    md=['# v25既有样本开发诊断（不是独立验证）','',
        f'已观察V600的600条原输入；{len(changes)}条机器标签发生变化。原A/C标签、手册和原验证报告未修改。',
        '','下表为使用历史设计权重的开发描述，不能作为新版泛化性能。每维相对A/C分别报告；完整计数和待定覆盖见JSON。','',
        '|维度|旧召回 A/C|新召回 A/C|旧F1 A/C|新F1 A/C|','|---|---:|---:|---:|---:|']
    for d in DIMS:
        def vals(v,k):
            values=[report['paired_common_determinate_metrics'][c][v][d]['historical_design_weighted_descriptive'][k] for c in ['A','C']]
            return '/'.join('NA' if x is None else f'{x:.1%}' for x in values)
        md.append(f'|{d}|{vals("baseline_frozen","recall")}|{vals("v25","recall")}|{vals("baseline_frozen","f1")}|{vals("v25","f1")}|')
    md += ['', '这些是开发材料上的结果。无法由此宣布自动编码合格，也不据此改写论文部门排序。']
    (HERE/'development_diagnostics.md').write_text('\n'.join(md)+'\n')
    print(json.dumps({'n':len(rows),'changed_units':len(changes),'review_flags':len(report['candidate_review_flags']),
                      'status':report['status']},ensure_ascii=False))
    print('\n'.join(md[7:]))

if __name__ == '__main__':
    main()

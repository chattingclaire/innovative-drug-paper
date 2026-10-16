"""Independent arithmetic readback; no rule classifier imports or calls."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from fractions import Fraction
import argparse, csv, hashlib, json, math, runpy

OUT = Path(__file__).resolve().parent
AUDIT = OUT.parent
G = AUDIT.parents[1]
DIMS = ('S', 'E', 'Ec', 'I', 'F')
INPUTS = {}
CHECKED = []

def binding(p):
    p = Path(p).resolve()
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return dict(path=str(p), bytes=p.stat().st_size, sha256=h.hexdigest())

def register(p, expected=None):
    b = binding(p)
    if expected:
        assert all(b[k] == expected[k] for k in ('path', 'bytes', 'sha256')), b
    INPUTS[b['path']] = b
    return Path(b['path'])

def load(p):
    return json.loads(register(p).read_bytes())

def exact_seal(p):
    seal = load(p)
    for b in seal.get('files', seal.get('output_files', [])):
        register(b['path'], b)
    return seal

def save(name, value):
    with (OUT / name).open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def binary(v):
    return type(v) is int and v in (0, 1)

def rows(p):
    with register(p).open(encoding='utf8') as f:
        return [json.loads(line) for line in f]

def predictions(p):
    result = {}
    for r in rows(p):
        assert r['id'] not in result and set(r['labels']) == set(DIMS)
        assert all(v is None or binary(v) for v in r['labels'].values())
        result[r['id']] = r
    return result

def ratio(a, b):
    return None if b == 0 else float(Fraction(a, b))

def metrics(pairs):
    assert all(binary(a) and binary(b) for a, b in pairs)
    counts = Counter(pairs)
    tp, fp, fn, tn = (counts[1, 1], counts[0, 1], counts[1, 0], counts[0, 0])
    n = tp + fp + fn + tn
    rp, rn, pp, pn = tp + fn, tn + fp, tp + fp, tn + fn
    return dict(N=n, TP=tp, FP=fp, FN=fn, TN=tn,
                reference_positive_N=rp, reference_negative_N=rn,
                prediction_positive_N=pp, prediction_negative_N=pn,
                Po=ratio(tp + tn, n), Pe=ratio(rp * pp + rn * pn, n * n),
                kappa=ratio(2 * (tp * tn - fp * fn), pp * rn + rp * pn),
                Precision=ratio(tp, pp), Recall=ratio(tp, rp),
                F1=ratio(2 * tp, 2 * tp + fp + fn),
                positive_agreement=ratio(2 * tp, 2 * tp + fp + fn),
                negative_agreement=ratio(2 * tn, 2 * tn + fp + fn),
                specificity=ratio(tn, rn), NPV=ratio(tn, pn))

def equals(actual, expected, name):
    if isinstance(expected, dict):
        assert isinstance(actual, dict), name
        for key, value in expected.items():
            assert key in actual, name + '.' + key
            equals(actual[key], value, name + '.' + key)
    elif isinstance(expected, list):
        assert actual == expected, (name, actual, expected)
    elif isinstance(expected, float):
        assert type(actual) in (int, float) and math.isclose(actual, expected, abs_tol=1e-12, rel_tol=1e-12), (name, actual, expected)
    else:
        assert actual == expected, (name, actual, expected)
    CHECKED.append(name)

def directed(pred, reference):
    result = {}
    for d in DIMS:
        allocated = [(sid, v) for (sid, dim), v in reference.items() if dim == d]
        missing = [dict(id=sid, reference=v) for sid, v in allocated if sid not in pred]
        null = [dict(id=sid, reference=v) for sid, v in allocated if sid in pred and pred[sid]['labels'][d] is None]
        pairs = [(v, pred[sid]['labels'][d]) for sid, v in allocated if sid in pred and binary(pred[sid]['labels'][d])]
        m = metrics(pairs)
        m.update(allocated_N=len(allocated), allocated_reference_positive_N=sum(v for _, v in allocated),
                 allocated_reference_negative_N=sum(v == 0 for _, v in allocated),
                 missing_N=len(missing), lawful_null_N=len(null), binary_coverage=ratio(len(pairs), len(allocated)),
                 excluded_positive_N=sum(r['reference'] for r in missing + null),
                 excluded_negative_N=sum(r['reference'] == 0 for r in missing + null),
                 conditional_core_targets_passed=all(m[k] is not None and m[k] >= .8 for k in ('kappa', 'Precision', 'Recall', 'F1')),
                 formal_validation_complete=False)
        # ROOT preserves workbook order, so check exclusion contents independently of row order.
        m['missing'] = sorted(missing, key=lambda x: x['id'])
        m['lawful_null'] = sorted(null, key=lambda x: x['id'])
        result[d] = m
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root-statistics', required=True)
    args = parser.parse_args()
    assert not (OUT / 'report.json').exists(), 'never overwrite completed readback'
    pre = load(OUT / 'pre-readback-code-freeze.json')
    register(pre['calculator']['path'], pre['calculator'])
    rootdir = Path(args.root_statistics).resolve()
    exact_seal(rootdir / 'seal.json')
    report = load(rootdir / 'metrics.json')
    exact_seal(AUDIT / 'seal.json')
    audit = load(AUDIT / 'report.json')
    for key in ('rule_execution', 'rule_seal', 'native_snapshot_seal', 'old_v5_predictions', 'calculator'):
        register(report[key]['path'], report[key])
    for b in report['reference_bindings']:
        register(b['path'], b)
    run = Path(report['rule_execution']['path']).parent
    ex = load(run / 'execution.json')
    assert ex['status'] == 'completed' and ex['actual_record_N'] == 4481 and ex['actual_dimension_N'] == 22405 and ex['technical_failure_dimension_N'] == 0
    native_dir = Path(report['native_snapshot_seal']['path']).parent
    exact_seal(native_dir / 'seal.json')
    coverage = load(native_dir / 'coverage.json')
    assert not coverage['thin35_included'] and not coverage['selection_by_semantic_metric']
    rule = predictions(run / 'predictions.jsonl')
    native = predictions(native_dir / 'selected-records.jsonl')
    old = predictions(report['old_v5_predictions']['path'])
    assert len(rule) == len(old) == 4481 and set(rule) == set(old) and set(native) <= set(rule)
    ns = runpy.run_path(str(register(AUDIT / 'audit_complete.py')))
    refs = {}
    for side in ('A', 'B'):
        p = G / f'09-delivery/agent-review-20261010/真人4项复核后-v2/编码复核表-{side}.xlsx'
        register(p)
        refs[side], _ = ns['xlsx'](p)
    assert refs['A'] == refs['B']
    independent_rule = {side: directed(rule, ref) for side, ref in refs.items()}
    independent_native = {side: directed(native, ref) for side, ref in refs.items()}
    for side in ('A', 'B'):
        for d in DIMS:
            for method, own, key in (('rule', independent_rule, 'development77_rule_metrics'), ('native', independent_native, 'development77_native_metrics')):
                actual = dict(report[key][d])
                actual['missing'] = sorted(actual['missing'], key=lambda x: x['id'])
                actual['lawful_null'] = sorted(actual['lawful_null'], key=lambda x: x['id'])
                equals(actual, own[side][d], f'{side}.{method}.{d}')
    expected_counts = {d: dict(positive_N=sum(x['labels'][d] == 1 for x in rule.values()),
                               negative_N=sum(x['labels'][d] == 0 for x in rule.values()),
                               lawful_null_N=sum(x['labels'][d] is None for x in rule.values())) for d in DIMS}
    equals(report['rules_counts'], expected_counts, 'rules_counts')
    for d, v in expected_counts.items():
        ad = audit['full4481_comparison']['per_dimension'][d]
        assert (v['positive_N'], v['negative_N'], v['lawful_null_N']) == (ad['new_positive'], ad['new_negative'], ad['new_null'])
    binary_native = sum(binary(r['labels'][d]) for r in native.values() for d in DIMS)
    null_native = len(native) * 5 - binary_native
    equals(coverage, dict(allocated_record_N=4481, selected_record_N=len(native), missing_record_N=4481 - len(native),
                         binary_label_N=binary_native, lawful_null_label_N=null_native, missing_label_N=(4481 - len(native)) * 5,
                         record_output_coverage=ratio(len(native), 4481),
                         complete_binary_record_N=sum(all(binary(r['labels'][d]) for d in DIMS) for r in native.values()),
                         full_corpus_complete=len(native) == 4481), 'native_coverage')
    for d in DIMS:
        equals(coverage['per_dimension'][d], dict(positive_N=sum(x['labels'][d] == 1 for x in native.values()),
                                                negative_N=sum(x['labels'][d] == 0 for x in native.values()),
                                                lawful_null_N=sum(x['labels'][d] is None for x in native.values()), missing_N=4481 - len(native)), 'native_coverage.' + d)
        keys = [(sid, dim) for sid, dim in refs['A'] if dim == d and sid in native and binary(rule[sid]['labels'][d]) and binary(native[sid]['labels'][d])]
        same = dict(matched_binary_N=len(keys), rules=metrics([(refs['A'][k], rule[k[0]]['labels'][d]) for k in keys]),
                    native=metrics([(refs['A'][k], native[k[0]]['labels'][d]) for k in keys]))
        equals(report['development77_same_binary_slots'][d], same, 'matched77.' + d)
        pair = metrics([(rule[sid]['labels'][d], native[sid]['labels'][d]) for sid in native if binary(rule[sid]['labels'][d]) and binary(native[sid]['labels'][d])])
        expected = dict(binary_pair_N=pair['N'], native_output_N=len(native), native_missing_N=4481 - len(native),
                        both_1=pair['TP'], rule0_native1=pair['FP'], rule1_native0=pair['FN'], both_0=pair['TN'],
                        Po=pair['Po'], Pe=pair['Pe'], kappa=pair['kappa'], positive_agreement=pair['positive_agreement'],
                        negative_agreement=pair['negative_agreement'], is_accuracy=False)
        equals(report['machine_pair_agreement_not_accuracy'][d], expected, 'machine_pair.' + d)
    transitions = {d: Counter() for d in DIMS}
    changes = {}
    disagreements = {}
    for sid in rule:
        for d in DIMS:
            ov, nv = old[sid]['labels'][d], rule[sid]['labels'][d]
            transitions[d][f'{ov}_to_{nv}'] += 1
            if ov != nv:
                changes[sid, d] = (ov, nv)
            if sid in native and nv != native[sid]['labels'][d]:
                disagreements[sid, d] = (nv, native[sid]['labels'][d])
    equals(report['old_v5_to_v7_changed_label_N'], len(changes), 'old_v5_to_v7_changed_label_N')
    equals(report['old_v5_to_v7_transitions'], {d: dict(v) for d, v in transitions.items()}, 'old_v5_to_v7_transitions')
    equals(report['machine_disagreement_including_null_N'], len(disagreements), 'machine_disagreement_including_null_N')
    equals(audit['full4481_comparison']['changed_slots'], len(changes), 'audit_same_changed_slots')
    recorded = rows(rootdir / 'old-v5-to-v7-label-changes.jsonl')
    assert len(recorded) == len(changes) and len({(r['id'], r['dimension']) for r in recorded}) == len(changes)
    for r in recorded:
        sid, d = r['id'], r['dimension']
        assert (r['old'], r['new']) == changes[sid, d] and r['new_decision'] == rule[sid]['decisions'][d] and r['old_decision'] == old[sid]['decisions'][d]
    recorded = rows(rootdir / 'machine-pair-disagreements.jsonl')
    assert len(recorded) == len(disagreements) and len({(r['id'], r['dimension']) for r in recorded}) == len(disagreements)
    for r in recorded:
        sid, d = r['id'], r['dimension']
        assert (r['rule'], r['native']) == disagreements[sid, d] and r['rule_decision'] == rule[sid]['decisions'][d] and r['native_decision'] == native[sid]['dimensions'][d] and r['not_adjudicated_truth']
    with register(rootdir / 'development77-comparison.csv').open(encoding='utf-8-sig', newline='') as f:
        ledger = list(csv.DictReader(f))
    assert len(ledger) == 385 and len({(r['id'], r['dimension']) for r in ledger}) == 385
    for r in ledger:
        sid, d = r['id'], r['dimension']
        nv = native[sid]['labels'][d] if sid in native else None
        assert int(r['reference_A']) == refs['A'][sid, d] and int(r['reference_B']) == refs['B'][sid, d]
        assert r['rules_v7'] == ('' if rule[sid]['labels'][d] is None else str(rule[sid]['labels'][d]))
        assert r['native_original_whole_batch'] == ('' if nv is None else str(nv))
        assert r['native_state'] == ('missing_record' if sid not in native else 'lawful_null' if nv is None else 'binary')
    equals(report, dict(rules_full_corpus_completed=True, native_full_corpus_completed=coverage['full_corpus_complete'],
                        rules_allocated_N=4481, rules_technical_failure_N=0, rules_lawful_null_label_N=sum(v['lawful_null_N'] for v in expected_counts.values()),
                        formal_validation_complete=False, population_CI_computed_from_development=False, paper_writing_gate_open=False), 'flags')
    assert metrics([(0, 1), (1, 0)])['F1'] == 0
    assert metrics([(0, 0)])['kappa'] is None and metrics([(0, 0)])['F1'] is None
    assert metrics([(1, 0)])['Precision'] is None and metrics([(1, 0)])['F1'] == 0
    result = dict(at_utc=datetime.now(timezone.utc).isoformat(), status='root_statistics_independently_recomputed_and_matched',
                  root_statistics_path=str(rootdir), named_arithmetic_checks_N=len(CHECKED),
                  independent_reference_A=independent_rule['A'], independent_reference_B=independent_rule['B'],
                  independent_native_reference_A=independent_native['A'], independent_native_reference_B=independent_native['B'],
                  full4481_rule_counts=expected_counts, old_v5_to_v7_changed_label_N=len(changes),
                  native_selected_record_N=len(native), native_binary_label_N=binary_native, native_null_label_N=null_native,
                  native_partial=not coverage['full_corpus_complete'], native_coverage_binding=binding(native_dir / 'coverage.json'),
                  machine_pair_disagreement_including_null_N=len(disagreements),
                  formulas_independently_count_based=True, null_not_filled=True, zero_denominator_not_one=True,
                  all_wrong_positive_F1_zero=True, two_machines_not_gold_standards=True,
                  classifier_imports_or_calls_N=0, formal_validation_complete=False, paper_writing_gate_open=False)
    save('report.json', result)
    text = f"ROOT落地统计已独立复算并一致：规则4481条/22405槽，旧v5→v7变化{len(changes)}槽；A/B分别复算四格、核心/辅助指标及排除分母。LLM原整批快照覆盖{len(native)}/4481条、{null_native}个待定，是否全量完成：{coverage['full_corpus_complete']}。\n\nnull未填0或1，零分母指标为NA；全错阳性F1=0。同一可判集合和机器对比逐项一致，机器一致率不作正确率。77条仍为开发诊断，正式验证及全文写作门槛均未开放。本复算不重新分类或新增金标签。\n"
    with (OUT / 'report.md').open('x', encoding='utf8') as f:
        f.write(text)
    for b in INPUTS.values():
        assert binding(b['path']) == b
    save('input-bindings.json', dict(files=list(INPUTS.values()), all_after_readback_unchanged=True))
    save('seal.json', dict(files=[binding(p) for p in sorted(OUT.iterdir()) if p.is_file()], self_excluded=True))
    print(json.dumps(dict(status=result['status'], report=binding(OUT / 'report.json'), seal=binding(OUT / 'seal.json')), ensure_ascii=False))

if __name__ == '__main__':
    main()

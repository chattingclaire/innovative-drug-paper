"""Independent point-value audit; standard library and direct rational formulas only.

This role begins after final method outputs were frozen. It reads reference labels
solely to audit arithmetic and never modifies a prediction, prompt, or method.
No statistical_core or production metric implementation is imported.
"""
import argparse
import hashlib
import json
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path

DIMS = ('S', 'E', 'Ec', 'I', 'F')
GROUPS = ('NMPA', 'NHSA', 'NHC')
CELL_NAMES = ('TP', 'FP', 'FN', 'TN')
KEY_NAMES = ('component', 'group', 'weighting', 'method', 'reference', 'dimension')
EXPECTED_DESIGN = {'NMPA': 947, 'NHSA': 760, 'NHC': 60}
EXPECTED_CORPUS = {'NMPA': 1848, 'NHSA': 2100, 'NHC': 533, 'GOV': 443}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def jsonl(path):
    data = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    result = {row['id']: row for row in data}
    assert len(result) == len(data), 'Duplicate IDs'
    return result


def label(row, dimension):
    value = row.get('labels', row.get('prediction', {}).get('labels', {})).get(dimension)
    return value if type(value) is int and value in (0, 1) else None


def ratio(numerator, denominator):
    return float(numerator / denominator) if denominator else None


def direct_metrics(cells):
    tp, fp, fn, tn = (Fraction(x) for x in cells)
    n = tp + fp + fn + tn
    # Multiply through by n^2: kappa = (n * diagonal - marginal-product sum)
    # / (n^2 - marginal-product sum), avoiding floating marginal rounding.
    expected_n_squared = (tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)
    return {'kappa': ratio(n * (tp + tn) - expected_n_squared, n*n - expected_n_squared),
            'agreement': ratio(tp + tn, n),
            'precision': ratio(tp, tp + fp), 'recall': ratio(tp, tp + fn),
            'f1': ratio(2 * tp, 2 * tp + fp + fn),
            'left_positive_rate': ratio(tp + fp, n),
            'right_positive_rate': ratio(tp + fn, n)}


class Audit:
    def __init__(self):
        self.mismatches = []
        self.checks = 0
        self.na_checks = 0
        self.max_numeric_error = 0.0
        self.bound = {}

    def equal(self, location, expected, actual):
        self.checks += 1
        if expected is None:
            self.na_checks += 1
        if isinstance(expected, (int, float)) and not isinstance(expected, bool):
            ok = isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isfinite(actual)
            if ok:
                error = abs(float(expected) - float(actual))
                self.max_numeric_error = max(self.max_numeric_error, error)
                ok = error <= 1e-10
        else:
            ok = expected == actual
        if not ok:
            self.mismatches.append({'location': location, 'independent': expected, 'published': actual})

    def bind(self, path, expected_sha=None):
        path = Path(path).resolve()
        value = sha(path)
        if expected_sha:
            self.equal(str(path) + ':SHA256', expected_sha, value)
        self.bound[str(path)] = value
        return path


def subset(design, component, group):
    return sorted(rid for rid, row in design.items()
                  if row['component'] == component and (group == 'ALL' or row['group'] == group))


def weight(design, rid, kind):
    if kind == 'unweighted':
        return Fraction(1)
    assert kind == 'eligible_design_weighted'
    row = design[rid]
    assert row['component'] == 'probability_canonical'
    return Fraction(row['canonical_frame_N'], row['sample_n'])


def recalculate(design, left, right, dimension, ids, weighting):
    raw = [0, 0, 0, 0]
    weighted = [Fraction(0) for _ in range(4)]
    paired, excluded = [], []
    for rid in ids:
        x, y = label(left[rid], dimension), label(right[rid], dimension)
        if x is None or y is None:
            excluded.append(rid)
            continue
        paired.append(rid)
        cell = {(1, 1): 0, (1, 0): 1, (0, 1): 2, (0, 0): 3}[x, y]
        raw[cell] += 1
        weighted[cell] += weight(design, rid, weighting)
    return {'unit_frame_n': len(ids), 'paired_n': len(paired),
            'paired_ids': paired, 'excluded_ids': excluded, 'excluded_pending_n': len(excluded),
            'left_positive_n': raw[0] + raw[1], 'reference_positive_n': raw[0] + raw[2],
            'raw_confusion': dict(zip(CELL_NAMES, raw)),
            'weighted_confusion': dict(zip(CELL_NAMES, map(float, weighted))),
            'weighted_denominator': float(sum(weighted)),
            'metrics': direct_metrics(weighted)}


def expected_keys(method_names, reference_names, symmetric=False):
    cells = [('probability_canonical', 'ALL', 'unweighted'),
             ('probability_canonical', 'ALL', 'eligible_design_weighted')]
    cells += [('probability_canonical', group, 'unweighted') for group in GROUPS]
    cells += [('enriched_challenge', group, 'unweighted') for group in ('ALL', 'NMPA', 'NHSA')]
    return {(c, g, w, m, r, d) for c, g, w in cells
            for m in method_names for r in reference_names for d in DIMS}


def check_comparisons(audit, name, published, design, methods, references, selected_methods=None, symmetric=False):
    if selected_methods:
        published = [row for row in published if row['method'] in selected_methods]
    keys = [tuple(row[k] for k in KEY_NAMES) for row in published]
    wanted = expected_keys(('A_C',) if symmetric else selected_methods or tuple(methods),
                           ('symmetric A/C',) if symmetric else tuple(references))
    audit.equal(name + ':unique_comparison_keys', len(keys), len(set(keys)))
    audit.equal(name + ':complete_expected_grid', sorted(wanted), sorted(keys))
    results = []
    for row in published:
        key = '|'.join(str(row[k]) for k in KEY_NAMES)
        ids = subset(design, row['component'], row['group'])
        left = references['A'] if symmetric else methods[row['method']]
        right = references['C'] if symmetric else references[row['reference']]
        recomputed = recalculate(design, left, right, row['dimension'], ids, row['weighting'])
        for field in ('unit_frame_n', 'paired_n', 'excluded_pending_n', 'paired_ids', 'excluded_ids',
                      'left_positive_n', 'reference_positive_n'):
            audit.equal(f'{name}|{key}|{field}', recomputed[field], row[field])
        for field, actual_field in [('raw_confusion', 'symmetric_raw_cells' if symmetric else 'raw_confusion'),
                                    ('weighted_confusion', 'symmetric_weighted_cells' if symmetric else 'weighted_confusion')]:
            names = ('A1_C1', 'A1_C0', 'A0_C1', 'A0_C0') if symmetric else CELL_NAMES
            for one, two in zip(CELL_NAMES, names):
                audit.equal(f'{name}|{key}|{actual_field}.{two}', recomputed[field][one], row[actual_field][two])
        for metric, actual in row['metrics'].items():
            audit.equal(f'{name}|{key}|{metric}', recomputed['metrics'][metric], actual['estimate'])
        expected_denominator = sum(weight(design, rid, row['weighting']) for rid in recomputed['paired_ids'])
        audit.equal(f'{name}|{key}|weighted_cell_sum', float(expected_denominator),
                    sum(row['symmetric_weighted_cells' if symmetric else 'weighted_confusion'].values()))
        results.append({**{k: row[k] for k in KEY_NAMES},
                        **{k: v for k, v in recomputed.items() if k not in ('paired_ids', 'excluded_ids')}})
    return results


def attention(rows, ids, design=None, kind='unweighted'):
    counts = {dim: sum((Fraction(label(rows[rid], dim)) * (weight(design, rid, kind) if design else 1)
                        for rid in ids), Fraction(0)) for dim in DIMS}
    total = sum(counts.values())
    shares = {d: ratio(v, total) for d, v in counts.items()}
    ranks = {d: 1 + sum(v > counts[d] for v in counts.values()) if total else None for d in DIMS}
    return {'unit_n': len(ids), 'coding_count': {d: float(v) for d, v in counts.items()},
            'five_dimension_coding_count': float(total), 'attention_share': shares,
            'within_department_rank': ranks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bindings', type=Path, required=True)
    ap.add_argument('--bindings-sha256', required=True)
    ap.add_argument('--tables', type=Path, required=True)
    ap.add_argument('--development', type=Path, required=True)
    ap.add_argument('--readable', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists(), 'Preserve prior QA artifacts'
    audit = Audit()
    audit.bind(args.bindings, args.bindings_sha256)
    manifest = read(args.bindings)
    freeze = read(audit.bind(args.tables / 'output_freeze.json'))
    audit.equal('final_freeze_manifest', args.bindings_sha256, freeze['bindings_sha256'])
    for name, digest in freeze['files'].items():
        audit.bind(args.tables / name, digest)
    devfreeze = read(audit.bind(args.development / 'output_freeze.json'))
    for name, digest in devfreeze['files'].items():
        audit.bind(args.development / name, digest)
    def bound(entry):
        return audit.bind(entry['path'], entry['sha256'])
    design_data = read(bound(manifest['sampling_design']))
    design = {r['original_id']: r for r in design_data['sample']}
    audit.equal('sample_ID_uniqueness', 240, len(design))
    audit.equal('frame_sizes', EXPECTED_DESIGN, design_data['frame_N_by_group'])
    design_counts = Counter((r['component'], r['group']) for r in design.values())
    audit.equal('sample180_challenge60_separate_counts',
                sorted({('probability_canonical', g): 60 for g in GROUPS}.items()) +
                sorted({('enriched_challenge', g): 30 for g in ('NMPA', 'NHSA')}.items()),
                sorted((k, v) for k, v in design_counts.items() if k[0] == 'probability_canonical') +
                sorted((k, v) for k, v in design_counts.items() if k[0] == 'enriched_challenge'))
    for rid, row in design.items():
        if row['component'] == 'probability_canonical':
            audit.equal(rid + ':design_weight', float(weight(design, rid, 'eligible_design_weighted')), row['analysis_weight'])
            audit.equal(rid + ':inclusion_probability', row['sample_n'] / row['canonical_frame_N'], row['inclusion_probability'])
        else:
            audit.equal(rid + ':challenge_not_design_weighted', None, row['analysis_weight'])
    inputs = jsonl(bound(manifest['material']['rule_inputs']))
    metadata = {Path(r['original_file']).stem: r for r in read(bound(manifest['metadata']))['rows']}
    groups = {rid: metadata[row['input']['original_file_stem']]['analysis_group'] for rid, row in inputs.items()}
    audit.equal('full_corpus_department_sizes', EXPECTED_CORPUS, dict(Counter(groups.values())))
    for rid, row in design.items():
        audit.equal(rid + ':department', groups[rid], row['group'])
    references = {name: jsonl(bound(entry)) for name, entry in manifest['references'].items()}
    references['candidate'] = jsonl(args.tables / 'candidate_reference.jsonl')
    methods = {name: jsonl(bound(entry['output'])) for name, entry in manifest['methods'].items()}
    dev = read(args.development / 'comparisons.json')
    methods['v33'] = methods['rules']
    methods['v35.1'] = jsonl(bound(dev['provenance']['methods']['v35.1']['prediction']))
    for name, rows in references.items():
        audit.equal(name + ':reference_exact_sample_IDs', sorted(design), sorted(rows))
    for name, rows in methods.items():
        audit.equal(name + ':machine_exact_corpus_IDs', sorted(inputs), sorted(rows))
    for name, rows in {**references, **methods}.items():
        audit.equal(name + ':fully_binary_count', len(rows) * 5,
                    sum(label(row, d) is not None for row in rows.values() for d in DIMS))
    machine_table = read(args.tables / 'machine_reference_classification.json')['comparisons']
    ac_table = read(args.tables / 'A_C_final_before_third_agreement.json')['comparisons']
    final_points = check_comparisons(audit, 'formal_classification', machine_table, design, methods,
                                    references, ['rules', 'LLM'])
    ac_points = check_comparisons(audit, 'AC_before_third', ac_table, design, methods, references, symmetric=True)
    development_points = check_comparisons(audit, 'development_classification', dev['comparisons'], design,
                                          methods, references, ['v33', 'v35.1'])
    published_full = read(args.tables / 'full4481_machine_attention_and_file_composition_sensitivity.json')['primary']
    full = {}
    for name in ('rules', 'LLM', 'v35.1'):
        full[name] = {}
        for group in GROUPS:
            ids = [rid for rid in inputs if groups[rid] == group]
            value = attention(methods[name], ids)
            full[name][group] = value
            audit.equal(f'{name}|{group}|attention_sum', 1.0, sum(value['attention_share'].values()))
            if name in published_full:
                for field in ('unit_n', 'five_dimension_coding_count'):
                    audit.equal(f'{name}|{group}|{field}', value[field], published_full[name][group][field])
                for field in ('coding_count', 'attention_share', 'within_department_rank'):
                    for dim in DIMS:
                        audit.equal(f'{name}|{group}|{field}|{dim}', value[field][dim], published_full[name][group][field][dim])
    # Probability attention profiles are an additional denominator check, and
    # never admit the enriched challenge cases into an estimated population.
    profiles = read(args.tables / 'probability_attention_and_paired_department_differences.json')['profiles']
    for profile in profiles:
        ids = subset(design, profile['component'], profile['group'])
        rows = {**references, **methods}[profile['method']]
        value = attention(rows, ids, design, profile['weighting'])
        key = '|'.join(str(profile[k]) for k in ('component', 'group', 'weighting', 'method'))
        audit.equal(key + ':probability_support', ids, profile['complete_support_ids'])
        audit.equal(key + ':coding_denominator', value['five_dimension_coding_count'], profile['weighted_five_dimension_coding_count_on_support'])
        for dim in DIMS:
            audit.equal(key + ':' + dim + ':attention', value['attention_share'][dim], profile['dimensions'][dim]['attention_share'])
            audit.equal(key + ':' + dim + ':count', value['coding_count'][dim], profile['dimensions'][dim]['weighted_known_coding_count'])
    if args.readable:
        readable = read(audit.bind(args.readable))
        for key, original in [('classification', machine_table), ('A_C_before_third', ac_table)]:
            by_key = {tuple(row[k] for k in KEY_NAMES): row for row in original}
            for row in readable[key]:
                identity = tuple(row[k] for k in KEY_NAMES)
                for metric, value in row['metrics'].items():
                    audit.equal('readable|' + str(identity) + '|' + metric,
                                by_key[identity]['metrics'][metric]['estimate'], value['estimate'])
    for path, digest in audit.bound.items():
        audit.equal(path + ':unchanged_after_audit', digest, sha(path))
    result = {'status': 'PASS' if not audit.mismatches else 'FAIL',
              'all_checks_pass': not audit.mismatches, 'check_count': audit.checks,
              'NA_checks': audit.na_checks, 'max_absolute_numeric_error': audit.max_numeric_error,
              'mismatch_count': len(audit.mismatches), 'mismatches': audit.mismatches,
              'role_transition': 'Machine execution completed and frozen before independent arithmetic audit gained reference access; no method/prompt/output edits in this role.',
              'independence': {'statistical_core_imported': False, 'production_metric_functions_imported': False,
                               'formulas': 'Exact Fraction-weighted cells; kappa=(n*(TP+TN)-[(TP+FP)*(TP+FN)+(FN+TN)*(FP+TN)])/(n*n-[(TP+FP)*(TP+FN)+(FN+TN)*(FP+TN)]); P=TP/(TP+FP); R=TP/(TP+FN); F1=2TP/(2TP+FP+FN); attention=dimension hits/sum five-dimension hits.',
                               'zero_denominator_policy': 'None/NA, including degenerate kappa; never substitute 1',
                               'numeric_tolerance': 1e-10, 'bootstrap_intervals_recomputed': False},
              'scope': {'formal_machine_comparisons': len(final_points), 'AC_comparisons': len(ac_points),
                        'development_v33_v35_1_comparisons': len(development_points),
                        'probability_n': 180, 'challenge_n': 60, 'challenge_pooled_into_probability': False,
                        'eligible_frame_N': EXPECTED_DESIGN, 'full_corpus_department_n': EXPECTED_CORPUS,
                        'full_three_department_n': sum(EXPECTED_CORPUS[g] for g in GROUPS)},
              'full4481_attention_recomputed': full,
              'v35_1_attention_publication_comparison': 'Independent development-only recomputation; no v35.1 attention in formal rules33/LLM table.',
              'formal_machine_points_recomputed': final_points, 'AC_points_recomputed': ac_points,
              'development_points_recomputed': development_points,
              'input_and_published_table_bindings': [{'path': path, 'sha256': digest} for path, digest in audit.bound.items()],
              'audit_script_sha256': sha(Path(__file__))}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'check_count', 'NA_checks', 'max_absolute_numeric_error', 'mismatch_count', 'scope')}, ensure_ascii=False))
    raise SystemExit(0 if not audit.mismatches else 1)


if __name__ == '__main__':
    main()

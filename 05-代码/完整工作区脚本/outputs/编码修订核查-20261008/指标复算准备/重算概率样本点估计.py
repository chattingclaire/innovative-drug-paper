"""Exact fixed-design point calculations; no labels or manuscript are changed.

Candidate files are optional. This does not select, adopt, or validate a method.
Always reproduces the adopted 80 table values before computing supplied files.
Confidence intervals require the separately bound sampling implementation.
"""
from pathlib import Path
from fractions import Fraction
import argparse
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
R3 = ROOT / 'outputs/coding-revision-20261007-r3'
R4 = ROOT / 'outputs/coding-revision-20261008-r4'
DIMS = ('S', 'E', 'Ec', 'I', 'F')
METRICS = ('kappa', 'precision', 'recall', 'f1')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rules', type=Path)
    parser.add_argument('--llm', type=Path)
    parser.add_argument('--semantic-review', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Preserve every completed calculation.'
    if args.rules or args.llm:
        assert args.semantic_review and args.semantic_review.is_file(), 'Complete the semantic review first; no metric-led tuning.'
    engine_path = R4 / 'check_development_points.py'
    spec = importlib.util.spec_from_file_location('frozen_exact_point_engine', engine_path)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    binding_path = R3 / 'statistics/final_bindings_v14_CONFIRMED_r3.json'
    binding = read(binding_path)
    sources = [binding_path, engine_path, Path(__file__)]
    for value in [binding['sampling_design'], *binding['references'].values()]:
        assert sha(value['path']) == value['sha256'], value['path']
        sources.append(Path(value['path']))
    design = read(binding['sampling_design']['path'])
    sample = {r['original_id']: r for r in design['sample'] if r['component'] == 'probability_canonical'}
    assert len(sample) == 180
    assert all(sum(r['group'] == group for r in sample.values()) == 60 for group in ('NMPA', 'NHSA', 'NHC'))
    refs = {'A': engine.rows(binding['references']['A']['path']),
            'B': engine.rows(binding['references']['C']['path'])}
    baseline_paths = {'rules_adopted': R4 / 'rules-v38-shadow-full-v14/all_predictions_material_v14_shadow.jsonl',
                      'LLM_adopted': R3 / 'llm-candidate03-development/full-corpus-candidate03-material-v14-single-unit-reconciled-development/all_predictions.jsonl'}
    machines = {name: engine.rows(path) for name, path in baseline_paths.items()}
    sources.extend(baseline_paths.values())
    for name, path in [('rules_candidate', args.rules), ('LLM_candidate', args.llm)]:
        if path:
            machines[name] = engine.rows(path)
            sources.append(path.resolve())
    for name, rows in machines.items():
        assert set(sample) <= set(rows), name
        for rid in sample:
            assert all(type(engine.labels(rows[rid])[d]) is int and engine.labels(rows[rid])[d] in (0, 1) for d in DIMS), (name, rid)
    comparisons = []
    for group, weighting in [('ALL', 'design_weighted'), ('ALL', 'unweighted'),
                             ('NMPA', 'unweighted'), ('NHSA', 'unweighted'), ('NHC', 'unweighted')]:
        ids = [rid for rid, r in sample.items() if group == 'ALL' or r['group'] == group]
        weights = {rid: Fraction(sample[rid]['canonical_frame_N'], 60) if weighting == 'design_weighted' else Fraction(1) for rid in ids}
        for method, machine in machines.items():
            for refname, ref in refs.items():
                for dim in DIMS:
                    comparisons.append({'method': method, 'reference': refname, 'dimension': dim,
                                        'group': group, 'weighting': weighting,
                                        **engine.result(machine, ref, ids, dim, weights)})
        for dim in DIMS:
            comparisons.append({'method': 'A_vs_B', 'reference': 'B', 'dimension': dim,
                                'group': group, 'weighting': weighting,
                                **engine.result(refs['A'], refs['B'], ids, dim, weights)})
    table_path = R3 / 'manuscript-update-20261008/proxy-180-table2-binding-20261008/表2与五维κ_代理180权威绑定.json'
    table = read(table_path)
    crosschecks = 0
    for item in table['table2_values']:
        method = 'rules_adopted' if item['method_role'] == 'rules' else 'LLM_adopted'
        for refname, expected in item['values'].items():
            actual = next(r for r in comparisons if r['method'] == method and r['reference'] == refname
                          and r['dimension'] == item['dimension'] and r['group'] == 'ALL' and r['weighting'] == 'design_weighted')
            for metric in METRICS:
                assert Fraction(actual['metrics'][metric]['exact']) == Fraction(expected['metrics'][metric]['exact_fraction'])
                crosschecks += 1
    assert crosschecks == 80
    sources.append(table_path)
    if args.semantic_review:
        sources.append(args.semantic_review.resolve())
    targets = []
    for method in machines:
        for group, weighting in [('ALL', 'design_weighted'), ('NMPA', 'unweighted'), ('NHSA', 'unweighted'), ('NHC', 'unweighted')]:
            chosen = [r for r in comparisons if r['method'] == method and r['group'] == group and r['weighting'] == weighting]
            failed, undefined, passed = [], [], 0
            for row in chosen:
                for metric in METRICS:
                    value = row['metrics'][metric]['exact']
                    tag = {'reference': row['reference'], 'dimension': row['dimension'], 'metric': metric, 'estimate': row['metrics'][metric]['estimate']}
                    if value is None:
                        undefined.append(tag)
                    elif Fraction(value) < Fraction(4, 5):
                        failed.append(tag)
                    else:
                        passed += 1
            assert passed + len(failed) + len(undefined) == 40
            targets.append({'method': method, 'group': group, 'weighting': weighting, 'pass_n': passed,
                            'below_project_target_n': len(failed), 'undefined_n': len(undefined),
                            'below_project_target': failed, 'undefined': undefined})
    out = {'status': 'COMPLETE_EXACT_DEVELOPMENT_POINT_CALCULATION_NOT_ADOPTION',
           'baseline_table80_exact_crosschecks': crosschecks, 'original_probability_sample_n': 180,
           'original60_challenge_material_used': False, 'new_independent_human_validation': False,
           'reference_identity': 'Original AI A/B judgments with user-confirmed retrospective human review unchanged; B aliases historical C.',
           'original_references_modified': False, 'candidate_selection_or_adoption': False,
           'new_confidence_intervals': False, 'target': 'Project inspection target .80, not a universal publication cutoff. NA remains undefined.',
           'source_bindings': [{'path': str(p.resolve()), 'sha256': sha(p)} for p in sorted(set(sources))],
           'comparisons': comparisons, 'target_checks': targets}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'baseline_crosschecks': crosschecks,
                      'output': str(args.output.resolve()), 'sha256': sha(args.output)}, ensure_ascii=False))


if __name__ == '__main__':
    main()

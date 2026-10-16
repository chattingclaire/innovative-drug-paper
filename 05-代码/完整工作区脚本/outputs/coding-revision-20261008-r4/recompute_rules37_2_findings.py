"""Recompute all descriptive findings from intact 37.2 and actual LLM03 outputs.

Uses unchanged previously audited estimands and resampling code. No model calls,
label editing, new references, significance selection, or manuscript mutation.
"""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import sys, json, hashlib

BASE = Path(__file__).resolve().parents[2]
R3 = BASE / 'outputs/coding-revision-20261007-r3'
R4 = Path(__file__).resolve().parent
sys.path.insert(0, str(R3 / 'statistics'))
import statistical_core_r3 as c
import final_binding_io_r3 as io
import run_candidate03_reconciled_complete_statistics_v2 as old_stats
import run_candidate03_reconciled_full_findings_v2 as f
from final_attention_r3 import full_machine_attention
from definition_boundary_sensitivity_r3 import derive, SCENARIOS

OUT = R4 / 'rules37.2-LLM03-synchronized-findings'
OLD_BINDING = R3 / 'methods-20261008/candidate03-reconciled-statistics-preparation-v3/actual-input-bindings-v3/rules-v36.2-plus-LLM03-reconciled-development-bindings-v3.json'
NEW_OUTPUT = R4 / 'rules-v37.2-shadow-full-v14/all_predictions_material_v14_shadow.jsonl'
FREEZE = R4 / 'rules-v37.2-development/candidate_freeze.json'
OLD_FINDINGS = R3 / 'methods-20261008/rules-v36.2-plus-LLM03-reconciled-development-findings-v3/完整定义构成核查.json'
NEW_KEY = 'rules-v37.2-development'
LLM_KEY = 'LLM-candidate03-single-unit-reconciled'

def main():
    assert not OUT.exists(), 'Never overwrite previous results'
    assert c.sha(OLD_BINDING) == 'db2c557e4db56e9b0e4721c9a7f2348f462d8296b20f1a1b8bd8d3e2c8e8e895'
    assert c.sha(NEW_OUTPUT) == '9c699125ed10170dbf8f570ebb8e86a331a89737ac4c7022453afcfba2edaacf'
    assert c.sha(FREEZE) == '166d8d96781248b5f0f09edeb2433e8be3452c08aefa013ea2dacd500e3115ee'
    frozen = c.read(FREEZE)
    for group in ('production_code_sha256', 'controls_and_review_sha256', 'test_script_sha256'):
        for path, digest in frozen[group].items(): assert c.sha(path) == digest, path
    dev = c.read(OLD_BINDING)
    leaves = old_stats.verify_tree(dev)
    manifest = io.bound(dev['reference_manifest'])
    leaves += old_stats.verify_tree(manifest)
    ctx = io.context_from_manifest(manifest)
    refs, ref_audit = io.final_references(manifest, ctx)
    old, old_method_audit = old_stats.load_methods(dev, manifest, ctx)
    rows = io.bound_jsonl({'path': str(NEW_OUTPUT), 'sha256': c.sha(NEW_OUTPUT)})
    assert len(rows) == 4924 and set(rows) == set(ctx['inputs'])
    assert all(c.binary(c.label(row, dim)) for row in rows.values() for dim in c.DIMS)
    baseline = old['rules-v36.2']
    sample_ids = sorted(ctx['sample'])
    assert len(sample_ids) == 240
    label_changes = []
    subtype_changes = []
    for rid in rows:
        for dim in c.DIMS:
            if c.label(rows[rid], dim) != c.label(baseline[rid], dim):
                label_changes.append({'id': rid, 'dimension': dim, 'group': ctx['groups'][rid],
                                      'old': c.label(baseline[rid], dim), 'new': c.label(rows[rid], dim)})
        for field in ('innovation_subtypes', 'fairness_subtypes', 'safety_quality_basis'):
            if rows[rid]['prediction'].get(field) != baseline[rid]['prediction'].get(field):
                subtype_changes.append({'id': rid, 'field': field, 'group': ctx['groups'][rid]})
    assert len(label_changes) == 6
    assert not [x for x in label_changes + subtype_changes if x['id'] in sample_ids]
    methods = {NEW_KEY: rows, LLM_KEY: old[LLM_KEY]}
    allids = {g: sorted(r for r in ctx['inputs'] if ctx['groups'][r] == g) for g in c.GROUPS}
    pids = {g: sorted(r for r, x in ctx['sample'].items() if x['component'] == 'probability_canonical' and x['group'] == g) for g in c.GROUPS}
    assert [len(allids[g]) for g in c.GROUPS] == [1848, 2100, 533]
    stems = sorted({ctx['inputs'][rid]['input']['original_file_stem'] for ids in allids.values() for rid in ids})
    assert len(stems) == 51
    latest = {}
    for stem in stems:
        item = ctx['metadata'][stem]
        if item['annual_series']:
            latest[item['policy_series']] = max(latest.get(item['policy_series'], item['year_in_filename']), item['year_in_filename'])
    f.ctx, f.allids, f.latest = ctx, allids, latest
    scenarios = [(name, None) for name in manifest['robustness_scenarios'] if name != 'leave_one_policy_entry_out']
    if 'leave_one_policy_entry_out' in manifest['robustness_scenarios']:
        scenarios += [('leave_one_policy_entry_out', stem) for stem in stems]
    assert len(scenarios) == 56
    compositions = []
    for scenario, omit in scenarios:
        gids = {g: f.ids_for(g, scenario, omit) for g in c.GROUPS}
        key = 'policy_file' if scenario == 'policy_file_equal' else 'policy_series' if scenario == 'policy_series_equal' else None
        item = {'scenario': scenario, 'omitted_policy_entry': omit, 'scope_ids': gids, 'methods': {}}
        for name, data in methods.items():
            dep = f.data(data, gids, key)
            item['methods'][name] = {'departments': dep, 'contrasts': f.contrast(dep)}
        compositions.append(item)
    definitions = []
    for scenario, explanation in SCENARIOS.items():
        item = {'scenario': scenario, 'explanation': explanation, 'methods': {}}
        for name, data in methods.items():
            derived, changes = derive(data, scenario)
            full, small = f.data(derived, allids), f.data(derived, pids)
            item['methods'][name] = {
                'full4481': {'departments': full, 'contrasts': f.contrast(full)},
                'same180': {'departments': small, 'contrasts': f.contrast(small)},
                'removed_labels': changes,
                'removed_labels_by_group_dimension': {g: {d: sum(ctx['groups'][x['id']] == g and x['dimension'] == d for x in changes) for d in c.DIMS} for g in c.GROUPS}}
        definitions.append(item)
    primary, same180 = {}, {}
    for target, ids, source in ((primary, allids, methods), (same180, pids, {**refs, **methods})):
        for name, data in source.items():
            dep = f.data(data, ids)
            target[name] = {'departments': dep, 'contrasts': f.contrast(dep), 'status': 'existing_exposed_material_descriptive'}
    metrics = ['P_F_given_Ec', 'P_Ec_given_F', 'OR'] + [f'{kind}_{d}' for kind in ('attention_share', 'coverage') for d in c.DIMS]
    summary = {}
    for name in methods:
        summary[name] = {}
        for kind, records in [('definition6', [x['methods'][name]['full4481'] for x in definitions]), ('composition56', [x['methods'][name] for x in compositions])]:
            summary[name][kind] = {}
            for metric in metrics:
                values = [x['contrasts'][metric]['NHSA_minus_NHC'] for x in records]
                valid = [x for x in values if x is not None]
                scale = 1 if metric == 'OR' else 100
                summary[name][kind][metric] = {
                    'scenario_n': len(values), 'NHSA_higher_n': sum(x > 1e-12 for x in valid),
                    'NHC_higher_n': sum(x < -1e-12 for x in valid), 'equal_n': sum(abs(x) <= 1e-12 for x in valid),
                    'NA_n': len(values)-len(valid), 'NHSA_minus_NHC_range': [min(valid)*scale, max(valid)*scale] if valid else None,
                    'range_units': 'OR units' if metric == 'OR' else 'percentage points'}
    # LLM source and all estimands are unchanged; recomputed values must match.
    prior = c.read(OLD_FINDINGS)
    assert primary[LLM_KEY]['departments'] == prior['primary_full4481'][LLM_KEY]['departments']
    for current, previous in zip(compositions, prior['composition56']):
        assert current['methods'][LLM_KEY] == previous['methods'][LLM_KEY]
    for current, previous in zip(definitions, prior['definition6']):
        assert current['methods'][LLM_KEY] == previous['methods'][LLM_KEY]
    pair_n = 0
    for obj in [*primary.values(), *same180.values(), *[m for x in compositions for m in x['methods'].values()], *[m[scope] for x in definitions for m in x['methods'].values() for scope in ('full4481','same180')]]:
        for group, dep in obj['departments'].items():
            assert len(dep['all10_pairs']) == 10
            for pair in dep['all10_pairs']:
                pair_n += 1
                if pair['cell_type'] == 'raw_counts':
                    assert sum(pair[k] for k in f.CELL) == pair['unit_n']
                    assert pair['a_positive'] == dep['profile']['coding_count'][pair['dimension_a']]
                    assert pair['b_positive'] == dep['profile']['coding_count'][pair['dimension_b']]
    full = full_machine_attention(ctx, {'rules': rows, 'LLM': old[LLM_KEY]}, manifest['robustness_scenarios'])
    for name, key in [('rules', NEW_KEY), ('LLM', LLM_KEY)]:
        for group in c.GROUPS:
            assert full['primary'][name][group]['attention_share'] == primary[key]['departments'][group]['profile']['attention_share']
    for leaf in leaves: assert c.sha(leaf['path']) == leaf['sha256']
    for group in ('production_code_sha256', 'controls_and_review_sha256', 'test_script_sha256'):
        for path, digest in frozen[group].items(): assert c.sha(path) == digest
    provenance = {'status': 'recomputed_candidate_findings_not_yet_manuscript_adopted',
        'old_execution_binding': {'path': str(OLD_BINDING), 'sha256': c.sha(OLD_BINDING)},
        'new_rule_freeze': {'path': str(FREEZE), 'sha256': c.sha(FREEZE)},
        'new_rule_output': {'path': str(NEW_OUTPUT), 'sha256': c.sha(NEW_OUTPUT)},
        'script_sha256': c.sha(__file__), 'statistical_code': dev['statistical_code'],
        'old240_labels_and_subtypes_identical': True, 'no_model_calls': True, 'reference_labels_changed': False,
        'sampling_design_and_estimands_unchanged': True, 'independent_validation': False,
        'scope': '4481 three-department fixed units; GOV443 excluded. 6 definition and56 composition scenarios separately; no crossed336 scenarios.'}
    OUT.mkdir()
    c.write_json(OUT/'完整定义构成核查.json', {'provenance': provenance, 'primary_full4481': primary, 'same180_primary': same180, 'definition6': definitions, 'composition56': compositions, 'summary': summary})
    c.write_json(OUT/'全量注意力与配对文件构成区间.json', {'provenance': provenance, **full})
    c.write_json(OUT/'输入执行与原样本不变核查.json', {'provenance': provenance, 'rule_label_changes': label_changes, 'rule_subtype_changes': subtype_changes, 'old_method_execution_audit': old_method_audit, 'all240_unchanged': True, 'all10_pair_records_checked': pair_n,
        'classification_interval_reuse_basis': 'All240 labels and source subtypes are unchanged; reference, design, weights and conditional bootstrap seeds unchanged. Existing classification and same180 attention estimates/intervals apply numerically unchanged; full-corpus quantities recomputed, not reused.'})
    c.write_json(OUT/'output_freeze.json', {'files': {p.name: c.sha(p) for p in OUT.iterdir() if p.is_file()}})
    print(json.dumps({'out': str(OUT), 'label_changes': label_changes, 'subtype_change_n': len(subtype_changes), 'old240_unchanged': True, 'all10_pair_records_checked': pair_n, 'primary': full['primary'], 'summary': summary}, ensure_ascii=False))

if __name__ == '__main__': main()

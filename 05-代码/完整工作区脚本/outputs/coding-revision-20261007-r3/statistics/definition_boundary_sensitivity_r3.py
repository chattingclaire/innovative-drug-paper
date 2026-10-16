"""Declared construct-boundary sensitivity from actual current source subtypes.

These derived labels are analytical scenarios, never replacement raw judgments.
No legacy subtype sidecars, inferred subtypes, target scores or new gold labels.
"""
import argparse
import json
from pathlib import Path
import statistical_core_r3 as c
import statistical_extensions_r3 as e
import final_binding_io_r3 as io
from final_attention_r3 import full_summary

SCENARIOS = {
    'primary': '五维原定义',
    'exclude_quality_only_S': '仅删除只依据质量安全的S，保留另有用药损害依据的S',
    'exclude_qualification_only_I': '仅删除只依据创新资格比较优势的I，保留另有属性或研发支持依据的I',
    'exclude_clinical_management_only_F': '仅删除只依据临床管理难度的F',
    'exclude_dimension_information_only_F': '仅删除只要求未细分公平性资料的F',
    'retain_access_affordability_F': 'F只保留有保障获取或患者可负担独立依据的单元',
}


def derive(rows, scenario):
    out, changes = {}, []
    for rid, row in rows.items():
        original = row.get('prediction', row)
        labels = {d: c.label(row, d) for d in c.DIMS}
        assert all(c.binary(v) for v in labels.values())
        i_types = set(original.get('innovation_subtypes', []))
        f_types = set(original.get('fairness_subtypes', []))
        quality = original.get('safety_quality_basis')
        if labels['I']:
            assert i_types and i_types <= {'attribute', 'research_support', 'qualification_advantage'}
        if labels['F']:
            assert f_types and f_types <= {'access', 'affordability', 'clinical_management', 'dimension_information'}
        if labels['S']:
            assert quality in {'quality_only', 'quality_and_other', 'no_quality_basis'}
        drop = None
        if scenario == 'exclude_quality_only_S' and quality == 'quality_only': drop = 'S'
        if scenario == 'exclude_qualification_only_I' and i_types == {'qualification_advantage'}: drop = 'I'
        if scenario == 'exclude_clinical_management_only_F' and f_types == {'clinical_management'}: drop = 'F'
        if scenario == 'exclude_dimension_information_only_F' and f_types == {'dimension_information'}: drop = 'F'
        if scenario == 'retain_access_affordability_F' and not f_types & {'access', 'affordability'}: drop = 'F'
        if drop and labels[drop] == 1:
            labels[drop] = 0
            changes.append({'id': rid, 'dimension': drop, 'original': 1, 'derived': 0})
        out[rid] = {'id': rid, 'labels': labels}
    return out, changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bindings', type=Path, required=True)
    parser.add_argument('--bindings-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    assert c.sha(args.bindings) == args.bindings_sha256
    manifest = c.read(args.bindings)
    assert manifest['stage'] == 'final' and manifest['root_final_bindings_confirmed']
    ctx = io.context_from_manifest(manifest)
    refs, _ = io.final_references(manifest, ctx)
    machines = io.final_methods(manifest, ctx)
    original = {'A': refs['A'], 'C': refs['C'], **machines}
    results, cache = [], {}
    probability_ids = sorted(rid for rid, item in ctx['sample'].items()
                             if item['component'] == 'probability_canonical')
    for scenario, explanation in SCENARIOS.items():
        transformed, changed = {}, {}
        for name, rows in original.items():
            transformed[name], changed[name] = derive(rows, scenario)
        full = {name: {group: full_summary(rows, [rid for rid in rows if ctx['groups'][rid] == group])
                       for group in c.GROUPS} for name, rows in transformed.items() if name in machines}
        profiles = []
        for group, kind in c.groups_and_weights('probability_canonical'):
            ids = [rid for rid in probability_ids if group == 'ALL' or ctx['sample'][rid]['group'] == group]
            for name, rows in transformed.items():
                profiles.append(e.attention_profile(ctx, rows, ids, 'probability_canonical',
                                                    group, kind, name, cache))
        results.append({'scenario': scenario, 'definition': explanation,
                        'changes': changed, 'full4481_machine_profiles': full,
                        'same180_reference_and_machine_profiles': profiles})
    assert c.sha(args.bindings) == args.bindings_sha256
    c.write_json(args.output, {
        'material_version': ctx['material_version'], 'binding_manifest_sha256': args.bindings_sha256,
        'human_validation_completed': False,
        'attention_denominator': 'department total coding occurrences over exactly five dimensions',
        'raw_judgments_changed': False,
        'subtype_provenance': 'actual same-version A/C/machine outputs only; no legacy sidecars',
        'candidate_not_narrowed': 'A/C agreement alone does not establish agreement in source subtype; A and C reported separately',
        'scenarios': results, 'script_sha256': c.sha(Path(__file__))})
    print(json.dumps({'status': 'complete_definition_boundary_sensitivity',
                      'scenario_n': len(results), 'output': str(args.output)}, ensure_ascii=False))


if __name__ == '__main__':
    main()

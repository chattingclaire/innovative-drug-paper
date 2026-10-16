"""Five predeclared descriptive subtype scenarios; no tests, CIs or ranking.
Import has no I/O. Reads only a completed R600+D668 original-submission archive.
First labels are never edited. All scenarios are parallel copies of the main
coding; pending remains a distinct state and the fixed design weights remain.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

SCENARIOS = (
    ('S_without_quality_only', 'S', 'safety_quality_basis', 'quality_only'),
    ('I_without_qualification_only', 'I', 'innovation_subtypes', 'qualification_advantage'),
    ('F_without_management_only', 'F', 'fairness_subtypes', 'clinical_management'),
    ('F_without_information_only', 'F', 'fairness_subtypes', 'dimension_information'),
    ('F_access_or_affordability_only', 'F', 'fairness_subtypes', 'access_or_affordability'),
)
DEPARTMENTS = ('NMPA', 'NHSA', 'NHC', 'GOV')
CODERS = ('A', 'C')
DIMS = ('S', 'E', 'Ec', 'I', 'F')


def require(test, msg):
    if not test: raise ValueError(msg)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def normalized(labels):
    require(isinstance(labels, dict) and set(labels) == set(DIMS), 'Exact five raw labels required')
    require(all((type(v) is int and v in (0, 1)) or (type(v) is str and v == '待定') for v in labels.values()), 'Illegal raw label')
    return {k: 'pending' if v == '待定' else str(v) for k, v in labels.items()}


def remove_positive(row, dim, field, rule):
    """Return affected flag; validate metadata also on negatives/pending."""
    label = row['labels'][dim]
    value = row.get(field)
    if field == 'safety_quality_basis':
        expected = {'no_quality_basis'} if label == 0 else ({'undetermined'} if label == '待定' else {'quality_only', 'quality_and_other', 'no_quality_basis'})
        require(isinstance(value, str) and value in expected, 'Invalid or missing safety quality basis')
        return label == 1 and value == rule
    allowed = {'attribute', 'research_support', 'qualification_advantage'} if dim == 'I' else {'access', 'affordability', 'clinical_management', 'dimension_information'}
    require(isinstance(value, list) and all(isinstance(x, str) for x in value) and len(value) == len(set(value)) and set(value) <= allowed, 'Invalid or missing subtype list')
    require(bool(value) if label == 1 else not value, 'Subtype/label inconsistency')
    if label != 1: return False
    if rule == 'access_or_affordability': return not (set(value) & {'access', 'affordability'})
    return set(value) == {rule}


def analyze(primary):
    require(primary.get('status') == 'completed_supplementary_AI_content_analysis_not_human_validation', 'Completed actual primary archive required')
    archive = primary['archive']; payload = archive['normalized_analysis_payload']
    require(payload['data_kind'] == 'observed_coding' and len(payload['units']) == 1268, 'Complete observed 1268-unit archive required')
    design = payload['design']; require(design['population_size'] == 4924 and design['sample_size'] == 1268, 'Fixed design required')
    strata = {x['stratum_id']: x for x in design['strata']}; require(len(strata) == 29, '29 strata required')
    source_rows = {}
    for phase in ('R', 'D'):
        docs = archive['raw_coder_submissions'][phase]
        batches = 24 if phase == 'R' else 27
        require(set(docs) == {f'agent-{c}/结果-{b:02d}.json' for c in CODERS for b in range(1, batches+1)}, 'Complete original file inventory required')
        for rel, doc in docs.items():
            c = rel.split('/')[0][-1]; require(doc['coder'] == c, 'Coder mismatch')
            for row in doc['rows']:
                key = (phase, c, row['id']); require(key not in source_rows, 'Duplicate raw ID')
                source_rows[key] = row
    join = {x['review_id']: x for x in archive['ID_join_provenance']}
    units = {x['unit_id']: x for x in payload['units']}
    require(len(join) == len(units) == 1268 and set(join) == set(units), 'Complete unique ID mapping required')
    originals = {}
    for uid, unit in units.items():
        link = join[uid]; require(link['stratum_id'] == unit['stratum_id'], 'Join stratum mismatch')
        for c in CODERS:
            row = source_rows[(link['phase'], c, link['blind_id'])]
            require(normalized(row['labels']) == unit['labels'][c], 'Raw and normalized labels differ')
            originals[uid, c] = row
    require(len(source_rows) == 2536, 'Raw observations must be two codings on 1268 units')
    scopes = list(DEPARTMENTS) + ['overall']
    outputs = []
    for name, dim, field, rule in SCENARIOS:
        affected = {c: set() for c in CODERS}; issues = []
        for uid in units:
            for c in CODERS:
                try:
                    if remove_positive(originals[uid, c], dim, field, rule): affected[c].add(uid)
                except (ValueError, KeyError, TypeError) as exc:
                    issues.append({'unit_id': uid, 'coder': c, 'field': field, 'issue': str(exc)})
        if issues:
            outputs.append({'scenario': name, 'dimension': dim, 'status': 'not_computable_missing_or_invalid_own_metadata',
                            'unrecodable_records': len(issues), 'issues': issues, 'no_imputation': True})
            continue
        estimates = []
        for c in CODERS:
            for g in scopes:
                total = design['population_size'] if g == 'overall' else design['department_sizes'][g]
                before = {k: Fraction(0) for k in ('0', '1', 'pending')}; after = dict(before)
                changed_weight = Fraction(0); changed_ids = []; n = 0
                for uid, unit in units.items():
                    h = strata[unit['stratum_id']]
                    if g != 'overall' and h['department'] != g: continue
                    w = Fraction(h['N'], h['n']); old = unit['labels'][c][dim]
                    new = '0' if uid in affected[c] else old
                    before[old] += w; after[new] += w; n += 1
                    if old != new: changed_ids.append(uid); changed_weight += w
                require(sum(before.values()) == sum(after.values()) == total, 'Weights do not restore fixed denominator')
                require(before['pending'] == after['pending'], 'Pending was altered')
                require(before['1'] - after['1'] == changed_weight, 'Affected weight mismatch')
                estimates.append({'coder': c, 'department': g, 'dimension': dim, 'sample_units': n, 'fixed_denominator': total,
                                  'main_proportions': {k: float(v/total) for k, v in before.items()},
                                  'scenario_proportions': {k: float(v/total) for k, v in after.items()},
                                  'main_weighted_totals_exact': {k: str(v) for k, v in before.items()},
                                  'scenario_weighted_totals_exact': {k: str(v) for k, v in after.items()},
                                  'positive_change_percentage_points': float(100*(after['1']-before['1'])/total),
                                  'changed_sample_count': len(changed_ids), 'changed_weight_exact': str(changed_weight),
                                  'changed_unit_ids': sorted(changed_ids), 'unrecodable_records': 0})
        outputs.append({'scenario': name, 'dimension': dim, 'status': 'computed_descriptive_only', 'estimates': estimates,
                        'other_four_dimensions': 'unchanged from original main coding', 'no_CI_pvalues_or_inferential_rank': True})
    return {'status': 'completed_pre_D_judgment_descriptive_sensitivity_addendum', 'scenarios': outputs,
            'timing': 'Plan fixed after D draw, before D material-read authorization and first D labels; separate from primary freeze.',
            'unique_sample_units': 1268, 'population_size': 4924, 'A_C_separate': True,
            'no_original_changes_imputation_CI_pvalues_or_inferential_rank': True,
            'limits': 'Descriptive definition-boundary changes only; does not extend the primary 580-parameter family or demonstrate validity.'}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--primary', type=Path, required=True)
    parser.add_argument('--addendum-seal', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); require(not args.output.exists(), 'Output exists')
    raw = args.primary.read_bytes(); seal_raw = args.addendum_seal.read_bytes(); seal = json.loads(seal_raw)
    plan_path = Path(seal['plan_path']); plan_raw = plan_path.read_bytes()
    require(sha(plan_raw) == seal['plan_sha256'], 'Addendum plan changed')
    primary = json.loads(raw)
    require(primary['archive']['release_seal_original']['freeze_manifest_sha256'] == seal['primary_freeze_sha256'], 'Primary/addendum freeze mismatch')
    result = analyze(primary)
    result['provenance'] = {'created_at': datetime.now(timezone.utc).isoformat(), 'primary_path': str(args.primary.resolve()),
                            'primary_sha256': sha(raw), 'addendum_seal_original': seal, 'addendum_seal_sha256': sha(seal_raw),
                            'program_sha256': sha(Path(__file__).read_bytes())}
    require(args.primary.read_bytes() == raw and args.addendum_seal.read_bytes() == seal_raw and plan_path.read_bytes() == plan_raw, 'Input changed during execution')
    with args.output.open('x') as out: json.dump(result, out, ensure_ascii=False, indent=2, allow_nan=False); out.write('\n')
    print(json.dumps({'output': str(args.output.resolve()), 'sha256': sha(args.output.read_bytes()), 'scenarios': len(result['scenarios'])}))


if __name__ == '__main__': main()

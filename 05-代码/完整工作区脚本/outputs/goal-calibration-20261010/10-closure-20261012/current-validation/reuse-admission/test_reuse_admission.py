"""Finite synthetic controls only. Never reads human labels or production predictions."""
from copy import deepcopy
from collections import Counter
from pathlib import Path
from fractions import Fraction
import hashlib
import importlib.util
import json
import sys
import subprocess
import tempfile
sys.dont_write_bytecode = True
import numpy as np
import reuse_admission as ra

OUT = ra.HERE / 'controls'
FIX = OUT / 'synthetic-fixtures'


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    return ra.binding(path)


def make_fixture():
    FIX.mkdir(parents=True, exist_ok=True)
    evidence = save(FIX / 'NONHUMAN-control-evidence.json', {
        'synthetic_only': True, 'actual_human_identity_or_result': False,
        'purpose': 'Finite receipt metadata control, not an authentic event or submission'})
    targets, legacy = [], []
    for dep, c, r in [('NHC', 1, 4), ('NHSA', 2, 3), ('NMPA', 1, 5)]:
        for role, count in [('certainty', c), ('supplement', r)]:
            for j in range(count):
                uid = f'TOY-{dep}-{role}-{j}'
                targets.append({'unit_id': uid, 'department': dep, 'role': role})
                if role == 'certainty':
                    legacy.append({'unit_id': uid, 'A_blind_id': 'A-' + uid, 'B_blind_id': 'B-' + uid,
                                   'old_pi_exact': '1/4', 'old_weight_exact': '4'})
    # Include a historical sample unit outside the new target; it must not enter C.
    legacy.append({'unit_id': 'TOY-OLD-EXPOSED', 'A_blind_id': 'A-EX', 'B_blind_id': 'B-EX',
                   'old_pi_exact': '1/2', 'old_weight_exact': '2'})
    old = save(FIX / 'NONHUMAN-old-assignment.json', {'synthetic_only': True, 'records': legacy})
    view = {'synthetic_only': True, 'target': targets, 'legacy_assignment': legacy,
            'legacy_draw_binding': old, 'basis_frozen_at': '2030-01-02T09:00:00Z',
            'legacy_material_contract': {'manuals': {'A': evidence, 'B': evidence},
                                         'materials': evidence, 'compatibility_review': evidence},
            'model_frozen_at': '2030-01-02T08:00:00Z',
            'identity_bindings': {key: evidence for key in
                                  ('basis', 'machine', 'exposure', 'manual', 'materials',
                                   'statistical_core', 'statistics_contract')}}
    members, strata, drawrows = [], [], []
    certainty = [r['unit_id'] for r in targets if r['role'] == 'certainty']
    for dep in ('NHC', 'NHSA', 'NMPA'):
        for role in ('certainty', 'supplement'):
            pop = [r['unit_id'] for r in targets if (r['department'], r['role']) == (dep, role)]
            hid = dep + '|' + role
            n = len(pop) if role == 'certainty' else 2  # TOY ONLY, not a real allocation.
            strata.append({'id': hid, 'N': len(pop), 'n': n, 'department': dep, 'role': role})
            members += [{'unit_id': uid, 'stratum_id': hid} for uid in pop]
            drawrows += [{'unit_id': uid, 'stratum_id': hid,
                          'pi_exact': str(Fraction(n, len(pop))), 'weight_exact': str(Fraction(len(pop), n))}
                         for uid in pop[:n]]  # Fixed control IDs; no sampling is performed.
    design = {'frozen_at': '2030-01-02T10:00:00Z', 'kind': 'stratified_srswor',
              'sampling_unit': 'source_unit', 'seed': 123456,
              'certainty_ids': certainty, 'selection_basis': 'fixed_ID_membership_only',
              'human_results_used': False, 'membership': members, 'strata': strata}
    draw = {'completed_at': '2030-01-03T08:00:00Z', 'design_sha256': ra.canonical(design),
            'seed': design['seed'], 'redrawn_or_outcome_adaptive': False, 'human_results_used': False,
            'original_receipt_binding': evidence, 'sampler_code_binding': evidence, 'records': drawrows}
    human = {}
    newids = [r['unit_id'] for r in drawrows if r['unit_id'] not in certainty]
    for person in ('A', 'B'):
        cohorts = {}
        for group, ids in [('inherited', certainty), ('supplement', newids)]:
            raw = save(FIX / f'NONHUMAN-{person}-{group}-first.json', {
                'synthetic_only': True, 'contains_human_answers': False,
                'control_member_ids': [r['unit_id'] for r in legacy] if group == 'inherited' else ids})
            is_old = group == 'inherited'
            receipt = {'kind': 'synthetic_first_submission',
                       'started_interval': {'earliest': '2030-01-01T09:00:00Z' if is_old else '2030-01-03T10:00:00Z',
                                            'latest': '2030-01-01T11:00:00Z' if is_old else '2030-01-03T11:00:00Z',
                                            'precision': 'approximate'},
                       'received_at': '2030-01-04T12:00:00Z', 'locked_at': '2030-01-04T12:01:00Z',
                       'start_relation_to_new_design': 'before' if is_old else 'after', 'machine_answers_visible': False,
                       'discussed_or_received_judgments_before_lock': False, 'is_first_submission': True,
                       'raw_first_submission_binding': raw, 'execution_evidence_binding': evidence,
                       'material_usage': {'used_manual_binding': evidence, 'used_materials_binding': evidence,
                                          'actual_delivery_evidence_binding': evidence,
                                          'compatibility_review_binding': evidence if is_old else None},
                       'projection': {'source_raw_binding': raw, 'values_unchanged': True,
                                      'retain_missing_null_failed': True, 'review_evidence_binding': evidence,
                                      'rows': [{'unit_id': uid, 'original_blind_id': person + '-' + uid,
                                                'original_row_locator': f'fixture-metadata-row:{j + 1}'}
                                               for j, uid in enumerate(ids)]}}
            if is_old:
                receipt['legacy_draw_binding'] = old
            cohorts[group] = receipt
        human[person] = {'identity_code': 'TOY-HUMAN-' + person, 'identity_evidence_binding': evidence,
                         'cohorts': cohorts}
    request = {'schema': 'inherited-certainty-admission-v1', 'synthetic_only': True,
               'registration_id': 'TOY-ONLY-NOT-ROOT-REGISTERED', 'stage': 'human_first',
               'identity_bindings': view['identity_bindings'], 'statistical_settings': ra.STAT_SETTINGS,
               'design': design, 'draw': draw,
               'review': {'design_reviewed_at': '2030-01-02T12:00:00Z',
                          'review_kind': 'synthetic_control_review', 'evidence_binding': evidence},
               'feedback_review': {'reviewed_through_at': '2030-01-05T08:00:00Z',
                                   'used_in_current_machine': False, 'used_in_domain_or_certainty_selection': False,
                                   'used_in_new_allocation_or_draw': False, 'first_feedback_received_at': None,
                                   'no_earlier_feedback_confirmed': True, 'evidence_binding': evidence},
               'human_receipts': human}
    return request, view, evidence


def main():
    request, view, evidence = make_fixture()
    save(FIX / 'request-human-first.json', request)
    save(FIX / 'view.json', view)
    results = []

    def run(name, mutate=None, accepted=False, source=None):
        candidate = deepcopy(source or request)
        if mutate:
            mutate(candidate)
        try:
            receipt = ra.validate_metadata(candidate, view, synthetic=True)
        except (ra.AdmissionError, FileNotFoundError, KeyError, ValueError) as error:
            results.append({'case': name, 'expected': 'accept' if accepted else 'reject',
                            'actual': 'reject', 'passed': not accepted, 'reason': str(error)})
            return None
        results.append({'case': name, 'expected': 'accept' if accepted else 'reject',
                        'actual': 'accept', 'passed': accepted, 'statistical_execution_authorized': receipt['statistical_execution_authorized']})
        return receipt

    good = run('mixed_timing_inherited_started_before_model_design_and_new_cohort_after_draw', accepted=True)
    save(OUT / 'synthetic-component-receipt.json', good)
    after = deepcopy(request)
    after['human_receipts']['B']['cohorts']['inherited'].update(
        start_relation_to_new_design='after', started_interval={
            'earliest': '2030-01-03T09:00:00Z', 'latest': '2030-01-03T10:00:00Z', 'precision': 'approximate'})
    run('inherited_C_not_yet_started_at_design_also_allowed', accepted=True, source=after)
    overlap = deepcopy(request)
    overlap['human_receipts']['A']['cohorts']['inherited'].update(
        start_relation_to_new_design='overlaps', started_interval={
            'earliest': '2030-01-02T08:00:00Z', 'latest': '2030-01-02T12:00:00Z', 'precision': 'approximate'})
    run('inherited_honest_interval_overlaps_design_allowed', accepted=True, source=overlap)
    ref = deepcopy(request)
    ref['stage'] = 'machine_reference'
    ref['human_receipts']['reference'] = {
        'kind': 'synthetic_adjudication', 'identity_code': 'TOY-ADJUDICATOR',
        'machine_answers_visible': False, 'auto_agreement_or_AI_substitution': False,
        'identity_evidence_binding': evidence, 'raw_first_submission_binding': evidence,
        'execution_evidence_binding': evidence, 'unit_ids': [r['unit_id'] for r in ref['draw']['records']],
        'material_usage': {'used_manual_binding': evidence, 'used_materials_binding': evidence,
                           'actual_delivery_evidence_binding': evidence, 'compatibility_review_binding': None},
        'started_at': '2030-01-05T09:00:00Z', 'locked_at': '2030-01-05T11:00:00Z',
        'first_machine_comparison_at': '2030-01-05T12:00:00Z'}
    ref['feedback_review']['reviewed_through_at'] = '2030-01-05T12:00:00Z'
    save(FIX / 'request-machine-reference.json', ref)
    run('synthetic_machine_blind_reference_metadata_stage', accepted=True, source=ref)
    run('legacy_false_before_answers_flag', lambda x: x.update(design_before_answers=True))
    run('historical_arithmetic_alias', lambda x: x.update(historical_arithmetic=True))
    run('false_old_start_relation', lambda x: x['human_receipts']['A']['cohorts']['inherited'].update(start_relation_to_new_design='after'))
    run('new_cohort_judged_before_own_draw', lambda x: x['human_receipts']['A']['cohorts']['supplement']['started_interval'].update(earliest='2030-01-01T09:00:00Z'))
    run('new_draw_before_design_review', lambda x: x['review'].update(design_reviewed_at='2030-01-04T00:00:00Z'))
    run('new_design_before_machine_freeze', lambda x: x['design'].update(frozen_at='2030-01-01T00:00:00Z'))
    run('human_feedback_entered_machine_development', lambda x: x['feedback_review'].update(used_in_current_machine=True))
    run('human_feedback_used_in_allocation', lambda x: x['feedback_review'].update(used_in_new_allocation_or_draw=True))
    run('feedback_unknown_not_false', lambda x: x['feedback_review'].update(used_in_current_machine=None))
    run('earlier_feedback_before_new_draw', lambda x: x['feedback_review'].update(first_feedback_received_at='2030-01-02T11:00:00Z'))
    run('first_feedback_outside_review_period', lambda x: x['feedback_review'].update(first_feedback_received_at='2030-01-06T11:00:00Z'))
    run('blindness_unknown', lambda x: x['human_receipts']['A']['cohorts']['inherited'].update(machine_answers_visible=None))
    run('discussion_before_first_lock', lambda x: x['human_receipts']['B']['cohorts']['inherited'].update(discussed_or_received_judgments_before_lock=True))
    run('missing_certainty_draw_row', lambda x: x['draw']['records'].pop(0))
    run('missing_certainty_projection_row', lambda x: x['human_receipts']['A']['cohorts']['inherited']['projection']['rows'].pop(0))
    run('old_weight_reused_in_new_census', lambda x: x['draw']['records'][0].update(weight_exact='4'))
    run('unresolved_rows_not_retained', lambda x: x['human_receipts']['A']['cohorts']['inherited']['projection'].update(retain_missing_null_failed=False))
    run('changed_machine_identity', lambda x: x['identity_bindings'].update(machine=view['legacy_draw_binding']))
    run('inherited_material_compatibility_missing', lambda x: x['human_receipts']['A']['cohorts']['inherited']['material_usage'].update(compatibility_review_binding=None))
    run('supplement_different_manual', lambda x: x['human_receipts']['A']['cohorts']['supplement']['material_usage'].update(used_manual_binding=view['legacy_draw_binding']))
    run('supplement_different_materials', lambda x: x['human_receipts']['B']['cohorts']['supplement']['material_usage'].update(used_materials_binding=view['legacy_draw_binding']))
    run('missing_original_human_first_submission', lambda x: x['human_receipts']['A']['cohorts']['inherited'].update(raw_first_submission_binding=None))
    run('tampered_original_first_hash', lambda x: x['human_receipts']['A']['cohorts']['inherited']['raw_first_submission_binding'].update(sha256='0'*64))
    run('synthetic_claims_actual_human_first', lambda x: x['human_receipts']['A']['cohorts']['inherited'].update(kind='actual_locked_human_first_submission'))
    run('same_person_A_and_B', lambda x: x['human_receipts']['B'].update(identity_code=x['human_receipts']['A']['identity_code']))
    run('labels_instead_of_identity_projection', lambda x: x['human_receipts']['A']['cohorts']['inherited']['projection']['rows'][0].update(S=1))
    run('changed_replicate_count', lambda x: x['statistical_settings'].update(replicates=1000))
    run('changed_point_gate', lambda x: x['statistical_settings'].update(numeric_gate='lowered'))
    run('machine_visible_reference', lambda x: x['human_receipts']['reference'].update(machine_answers_visible=True), source=ref)
    run('automatic_reference_from_agreement', lambda x: x['human_receipts']['reference'].update(auto_agreement_or_AI_substitution=True), source=ref)
    run('reference_different_materials', lambda x: x['human_receipts']['reference']['material_usage'].update(used_materials_binding=view['legacy_draw_binding']), source=ref)
    run('review_does_not_cover_reference_lock', lambda x: x['feedback_review'].update(reviewed_through_at='2030-01-05T10:00:00Z'), source=ref)
    run('synthetic_request_marked_project', lambda x: x.update(synthetic_only=False))

    # Actual entry point, with the pinned empty registry, must refuse before any
    # human file or classifier output is opened.
    pending = {'schema': 'inherited-certainty-admission-v1', 'synthetic_only': False,
               'registration_id': 'UNREGISTERED-CURRENT-REUSE', 'stage': 'human_first'}
    save(ra.HERE / 'pending-real-input.json', pending)
    for name, path in [('actual_unregistered_and_unsubmitted_refused', ra.HERE / 'pending-real-input.json'),
                       ('synthetic_cannot_enter_real_route', FIX / 'request-human-first.json')]:
        try:
            ra.admit_real(path)
        except ra.AdmissionError as error:
            results.append({'case': name, 'expected': 'reject', 'actual': 'reject', 'passed': True, 'reason': str(error)})
        else:
            results.append({'case': name, 'expected': 'reject', 'actual': 'accept', 'passed': False})

    with tempfile.TemporaryDirectory(prefix='cli-control-', dir=OUT) as temporary:
        destination = Path(temporary) / 'receipt.json'
        command = [sys.executable, str(ra.HERE / 'reuse_admission.py'), '--request',
                   str(FIX / 'request-human-first.json'), '--synthetic-view', str(FIX / 'view.json')]
        execution = subprocess.run(command + ['--output', str(destination)], capture_output=True, text=True)
        results.append({'case': 'CLI_synthetic_new_output_only', 'expected': 'accept',
                        'actual': 'accept' if execution.returncode == 0 else 'reject',
                        'passed': execution.returncode == 0 and destination.exists()})
        existing_sha = ra.binding(destination)['sha256']
        execution = subprocess.run(command + ['--output', str(destination)], capture_output=True, text=True)
        results.append({'case': 'CLI_existing_receipt_never_overwritten', 'expected': 'reject_and_preserve',
                        'passed': execution.returncode != 0 and ra.binding(destination)['sha256'] == existing_sha})
        original_request = ra.binding(FIX / 'request-human-first.json')
        execution = subprocess.run(command + ['--output', original_request['path']], capture_output=True, text=True)
        results.append({'case': 'CLI_request_original_never_overwritten', 'expected': 'reject_and_preserve',
                        'passed': execution.returncode != 0 and ra.binding(original_request['path']) == original_request})
        no_output = Path(temporary) / 'actual-must-not-exist.json'
        execution = subprocess.run([sys.executable, str(ra.HERE / 'reuse_admission.py'), '--request',
                                    str(ra.HERE / 'pending-real-input.json'), '--output', str(no_output)],
                                   capture_output=True, text=True)
        results.append({'case': 'CLI_real_empty_registry_refusal_creates_no_output', 'expected': 'reject_no_output',
                        'passed': execution.returncode != 0 and not no_output.exists()})

    # Pure original functions, not analyze()/prepare()/review_eligibility().
    basis = ra.read_json(ra.HERE / 'current-basis.json')
    core_binding = basis['bindings']['statistical_core']
    core_path = ra.verify(core_binding)
    spec = importlib.util.spec_from_file_location('unchanged_frozen_math', core_path)
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    strata = {r['id']: {'N': r['N'], 'n': r['n']} for r in request['design']['strata']}
    ordered = request['draw']['records']
    prep = {'kind': 'stratified_srswor', 'strata': strata,
            'weights': np.array([float(Fraction(r['weight_exact'])) for r in ordered]),
            'stratum_ids': np.array([r['stratum_id'] for r in ordered])}
    W = core.rao_wu_weights(prep, replicates=5000, seed=20261010)
    C = np.array(['certainty' in r['stratum_id'] for r in ordered])
    X = np.eye(4)[np.arange(len(ordered)) % 4]  # Explicit synthetic category indicators.
    V = core.analytic_covariance(prep, X)
    manual_V = np.zeros((4, 4))
    for hid, h in strata.items():
        if h['N'] != h['n']:
            x = X[prep['stratum_ids'] == hid]
            manual_V += h['N']**2 * (1-h['n']/h['N']) * np.cov(x, rowvar=False, ddof=1) / h['n']
    checks = {
        'source_core_sha_unchanged': ra.binding(core_path) == core_binding,
        'replicate_shape_is_5000_by_all_assigned': W.shape == (5000, len(ordered)),
        'certainty_new_weights_and_all_replicates_are_one': bool(np.all(W[:, C] == 1)),
        'all_stratum_replicate_totals_equal_frozen_N': all(np.allclose(W[:, prep['stratum_ids'] == hid].sum(axis=1), h['N']) for hid, h in strata.items()),
        'core_covariance_equals_independent_stratified_formula': bool(np.allclose(V, manual_V)),
        'certainty_only_indicator_variance_is_zero': bool(np.all(core.analytic_covariance(prep, C.astype(float)) == 0)),
        'fixed_seed_reproduces_same_shared_W': bool(np.array_equal(W, core.rao_wu_weights(prep, 5000, 20261010))),
        'original_target_is_exact_4_over_5': core.TARGET == Fraction(4, 5),
        'old_probabilities_preserved_separately': all(v['weight_exact'] == '4' for v in good['legacy_weights_preserved_separately'].values()),
        'metadata_success_never_authorizes_statistics': good['statistical_execution_authorized'] is False,
        'helper_success_never_grants_ROOT_adoption': good['actual_ROOT_adoption'] is False,
    }
    current = ra.current_view()  # ID/binding metadata only, no actual answer or prediction read.
    counts = dict(Counter(r['role'] for r in current['target']))
    results.append({'case': 'current_real_metadata_basis_only', 'expected': '1261=91+1170',
                    'actual': counts, 'passed': counts == {'certainty': 91, 'supplement': 1170},
                    'actual_admission': False})
    report = {'schema': 'reuse-admission-finite-controls-v1',
              'synthetic_only_results': True, 'actual_human_answers_read_or_created': 0,
              'actual_draws': 0, 'actual_scope_registrations': 0,
              'statistical_execution_authorized': False,
              'cases': results, 'pure_original_math_checks': checks,
              'all_passed': all(r['passed'] for r in results) and all(checks.values()),
              'binding': {'admission': ra.binding(ra.HERE / 'reuse_admission.py'),
                          'test': ra.binding(Path(__file__)), 'core': core_binding},
              'controls_do_not_prove_actual_events': True,
              'pending_end_to_end_join': True}
    save(OUT / 'control-results.json', report)
    print(json.dumps({'cases': len(results), 'math_checks': len(checks), 'all_passed': report['all_passed'],
                      'actual_admission': False}, ensure_ascii=False))
    if not report['all_passed']:
        for r in results:
            if not r['passed']:
                print(r)
        sys.exit(1)


if __name__ == '__main__':
    main()

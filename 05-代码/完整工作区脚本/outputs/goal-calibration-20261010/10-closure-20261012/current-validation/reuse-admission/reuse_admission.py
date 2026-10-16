"""Metadata-only candidate for inherited certainty-unit admission.

No labels are parsed, no sample is drawn, and no statistics engine is called.
An accepted receipt is NOT a statistical execution authorization. The legacy
before_answers gates remain intact and are never supplied a substituted value.
Real authority is an independently pinned ROOT registry; it is currently empty.
"""
from collections import Counter
from datetime import datetime
from fractions import Fraction
from pathlib import Path
import argparse
import hashlib
import json

HERE = Path(__file__).resolve().parent
BASIS_SHA = 'a219a1d719f73d37bdd288647609fc896fc69110308ac1e9df7c839a3c6de133'
REGISTRY_SHA = 'e71bc69cf9761285ddb03ac301f0be75bd4bd5775933b8ce2fcf8e71cc0e7153'
STAT_SETTINGS = {'replicates': 5000, 'seed': 20261010,
                 'guard_mode': 'single_category', 'numeric_gate': 'unchanged_45_ALL_point_targets',
                 'new_CI_threshold': False, 'shared_W': True,
                 'null_and_failed_retained': True}


class AdmissionError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise AdmissionError(message)


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def binding(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
            size += len(block)
    return {'path': str(path), 'bytes': size, 'sha256': digest.hexdigest()}


def verify(value):
    require(isinstance(value, dict) and set(value) == {'path', 'bytes', 'sha256'},
            'Exact path/bytes/SHA binding required')
    require(Path(value['path']).is_absolute(), 'Binding path must be absolute')
    require(binding(value['path']) == value, 'Bound original changed or missing')
    return Path(value['path'])


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(AdmissionError('Nonfinite JSON')))


def evidence(value):
    """Hash original bytes only: a hash does not itself establish human truth."""
    return verify(value)


def time(value):
    require(isinstance(value, str), 'Actual timezone-aware time required; unknown is not false')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise AdmissionError('Invalid event time') from error
    require(result.tzinfo is not None, 'Event time must include timezone')
    return result


def rows_by_id(rows, key='unit_id'):
    require(isinstance(rows, list) and rows, 'Nonempty metadata rows required')
    ids = [row.get(key) for row in rows]
    require(all(isinstance(i, str) and i for i in ids) and len(ids) == len(set(ids)),
            'Unique nonempty metadata IDs required')
    return dict(zip(ids, rows))


def current_view():
    """Only read accepted exposure IDs, old design metadata, and freeze metadata."""
    path = HERE / 'current-basis.json'
    require(binding(path)['sha256'] == BASIS_SHA, 'Current basis external pin differs')
    basis = read_json(path)
    for value in basis['bindings'].values():
        verify(value)
    b = basis['bindings']
    frame = [json.loads(line) for line in Path(b['exposure_frame']['path']).read_text().splitlines()]
    old = read_json(b['legacy_draw']['path'])['records']
    oldby = rows_by_id(old, 'source_id')
    require(len(frame) == 4481 and len(oldby) == 200, 'Current original frame/count differs')
    require(len({r['source_id'] for r in frame}) == 4481, 'Duplicate current frame ID')
    target = [{'unit_id': r['source_id'], 'department': r['department'],
               'role': 'certainty' if r['source_id'] in oldby else 'supplement'}
              for r in frame if r['candidate_domain'] == 'remaining']
    require(len(target) == 1261 and sum(r['role'] == 'certainty' for r in target) == 91,
            'Current target or certainty set differs')
    machine = read_json(b['machine_freeze']['path'])
    adoption = read_json(b['current_adoption']['path'])
    compatibility = read_json(b['material_compatibility']['path'])
    old_materials = binding(compatibility['bindings']['materials_manifest']['path'])
    require(old_materials['sha256'] == compatibility['bindings']['materials_manifest']['sha256'],
            'Legacy material manifest differs from compatibility review')
    old_directory = Path(b['legacy_draw']['path']).parent.parent
    old_manuals = {person: binding(old_directory / ('coder-' + person) / 'manual.txt')
                   for person in ('A', 'B')}
    require(all(v['sha256'] == machine['inputs']['common_manual']['sha256'] for v in old_manuals.values()),
            'Inherited manuals no longer match reviewed current manual')
    legacy = [{'unit_id': r['source_id'], 'A_blind_id': r['A_blind_id'],
               'B_blind_id': r['B_blind_id'], 'old_pi_exact': r['pi_exact'],
               'old_weight_exact': r['weight_exact']} for r in old]
    return {'synthetic_only': False, 'target': target, 'legacy_assignment': legacy,
            'legacy_draw_binding': b['legacy_draw'],
            'legacy_material_contract': {'manuals': old_manuals, 'materials': old_materials,
                                         'compatibility_review': b['material_compatibility']},
            'basis_frozen_at': adoption['adopted_at_shanghai'],
            'model_frozen_at': machine['created_at_local'],
            'identity_bindings': {
                'basis': binding(path), 'machine': b['machine_freeze'],
                'exposure': b['exposure_frame'],
                'manual': machine['inputs']['common_manual'],
                'materials': machine['inputs']['current_packet_metadata'],
                'statistical_core': b['statistical_core'],
                'statistics_contract': b['statistics_contract']}}


def reject_legacy_temporal_aliases(value):
    if isinstance(value, dict):
        require(not any('before_answers' in key or key == 'historical_arithmetic' for key in value),
                'Legacy before_answers/historical_arithmetic aliases forbidden')
        for child in value.values():
            reject_legacy_temporal_aliases(child)
    elif isinstance(value, list):
        for child in value:
            reject_legacy_temporal_aliases(child)


def check_material_usage(receipt, view, *, inherited_person=None):
    usage = receipt.get('material_usage', {})
    if inherited_person is None:
        manual, materials = view['identity_bindings']['manual'], view['identity_bindings']['materials']
        require(usage.get('compatibility_review_binding') is None,
                'New/reference material use cannot substitute a legacy compatibility claim')
    else:
        contract = view['legacy_material_contract']
        manual, materials = contract['manuals'][inherited_person], contract['materials']
        require(usage.get('compatibility_review_binding') == contract['compatibility_review'],
                'Inherited material use needs exact accepted compatibility chain')
        evidence(contract['compatibility_review'])
    require(usage.get('used_manual_binding') == manual and usage.get('used_materials_binding') == materials,
            'Actual human cohort/reference used different manual or materials')
    evidence(manual)
    evidence(materials)
    evidence(usage.get('actual_delivery_evidence_binding'))


def validate_metadata(request, view, *, synthetic):
    """Independent metadata contract, NOT a bypass of the old engine gates.

    The real public entry point additionally checks a ROOT-pinned registration.
    Validation facts must be independently reviewed; these checks cannot infer
    events from hashes or self-asserted booleans.
    """
    reject_legacy_temporal_aliases(request)
    require(request.get('schema') == 'inherited-certainty-admission-v1', 'Wrong candidate schema')
    require(request.get('synthetic_only') is synthetic and view.get('synthetic_only') is synthetic,
            'Synthetic/project identities cannot be interchanged')
    require(request.get('stage') in ('human_first', 'machine_reference'), 'Unsupported stage')
    target = rows_by_id(view['target'])
    legacy = rows_by_id(view['legacy_assignment'])
    require(all(i.startswith('TOY-') == synthetic for i in set(target) | set(legacy)),
            'Synthetic fixtures may contain only TOY IDs; project may contain none')
    certainty = [i for i, row in target.items() if row['role'] == 'certainty']
    supplement = [i for i, row in target.items() if row['role'] == 'supplement']
    require(set(certainty) == set(target) & set(legacy) and certainty and supplement,
            'Certainty is exactly all legacy members in frozen target')
    require(request.get('identity_bindings') == view['identity_bindings'],
            'Machine, domain, manual, materials or mathematical identity changed')
    for value in request['identity_bindings'].values():
        evidence(value)
    require(request.get('statistical_settings') == STAT_SETTINGS, 'Statistical contract changed')

    design = request['design']
    draw = request['draw']
    approval = request['review']
    frozen = time(design.get('frozen_at'))
    drawn = time(draw.get('completed_at'))
    reviewed = time(approval.get('design_reviewed_at'))
    basis_at, model_at = time(view['basis_frozen_at']), time(view['model_frozen_at'])
    require(max(basis_at, model_at) <= frozen <= reviewed <= drawn,
            'Basis/model, design, independent design review and new draw are out of order')
    require(approval.get('review_kind') == ('synthetic_control_review' if synthetic else 'ROOT_actual_independent_reuse_design_review'),
            'Actual independent reuse design review missing')
    evidence(approval.get('evidence_binding'))
    require(design.get('kind') == 'stratified_srswor' and design.get('sampling_unit') == 'source_unit',
            'Only fixed one-stage source-unit SRSWOR supported')
    require(type(design.get('seed')) is int, 'Real registered seed is required, never chosen by receiver')
    require(design.get('certainty_ids') == certainty, 'All fixed certainty IDs/order must be retained')
    require(design.get('selection_basis') == 'fixed_ID_membership_only', 'Outcome-based certainty selection forbidden')
    require(design.get('human_results_used') is False, 'Design feedback unknown or used')
    members = rows_by_id(design['membership'])
    require(list(members) == list(target), 'Strata must cover entire frozen target in order')
    require(all(set(row) == {'unit_id', 'stratum_id'} for row in members.values()), 'Membership is ID metadata only')
    strata = rows_by_id(design['strata'], 'id')
    counts = Counter(row['stratum_id'] for row in members.values())
    require(set(counts) == set(strata), 'All and only nonempty strata must be registered')
    for hid, h in strata.items():
        require(set(h) == {'id', 'N', 'n', 'department', 'role'}, 'Unexpected stratum fields')
        require(type(h['N']) is int and type(h['n']) is int and h['N'] == counts[hid]
                and 1 <= h['n'] <= h['N'], 'Unregistered allocation or invalid layer N/n')
        require(h['n'] == h['N'] or h['n'] >= 2, 'Noncensus singleton has unidentified variance')
        for rid in (i for i, m in members.items() if m['stratum_id'] == hid):
            require((h['role'], h['department']) == (target[rid]['role'], target[rid]['department']),
                    'Stratum must be pure department and certainty/supplement role')
        require(h['role'] != 'certainty' or h['n'] == h['N'], 'Certainty layer cannot be subsampled')
    require(draw.get('design_sha256') == canonical(design) and draw.get('seed') == design['seed'],
            'Draw does not bind the exact registered design and seed')
    require(draw.get('redrawn_or_outcome_adaptive') is False and draw.get('human_results_used') is False,
            'Redraw/outcome-adaptive or unknown draw forbidden')
    evidence(draw.get('original_receipt_binding'))
    evidence(draw.get('sampler_code_binding'))
    assigned = rows_by_id(draw['records'])
    require(set(assigned) <= set(target), 'Out-of-frame or exposed ID in draw')
    require(set(certainty) <= set(assigned), 'Missing certainty row cannot be dropped')
    require(Counter(row['stratum_id'] for row in assigned.values()) ==
            {hid: h['n'] for hid, h in strata.items()}, 'Every registered draw n must be preserved')
    for rid, row in assigned.items():
        require(set(row) == {'unit_id', 'stratum_id', 'pi_exact', 'weight_exact'}, 'Unexpected draw row fields')
        hid = members[rid]['stratum_id']
        require(row['stratum_id'] == hid, 'Assigned unit stratum changed')
        h = strata[hid]
        require(isinstance(row['pi_exact'], str) and isinstance(row['weight_exact'], str), 'Exact rational strings required')
        require(Fraction(row['pi_exact']) == Fraction(h['n'], h['N']) and
                Fraction(row['weight_exact']) == Fraction(h['N'], h['n']), 'Wrong new design probability/weight')

    feedback = request['feedback_review']
    require(time(feedback.get('reviewed_through_at')) >= drawn, 'Feedback review must cover new draw')
    require(all(feedback.get(key) is False for key in
                ('used_in_current_machine', 'used_in_domain_or_certainty_selection', 'used_in_new_allocation_or_draw')),
            'Human feedback used in machine/design, or status unknown')
    first_feedback = feedback.get('first_feedback_received_at')
    require('first_feedback_received_at' in feedback, 'Explicit no-feedback/first-feedback fact required')
    require(first_feedback is None or time(first_feedback) >= drawn,
            'Human feedback reached decision makers before new design/draw freeze')
    require(first_feedback is None or time(first_feedback) <= time(feedback['reviewed_through_at']),
            'First feedback event lies outside the reviewed period')
    require(feedback.get('no_earlier_feedback_confirmed') is True,
            'Unknown earlier feedback cannot be treated as absent')
    evidence(feedback.get('evidence_binding'))

    people = request['human_receipts']
    require(set(people) == ({'A', 'B'} if request['stage'] == 'human_first' else {'A', 'B', 'reference'}),
            'Required actual human first submissions/reference missing')
    identities = []
    locks = []
    inherited_timing = {}
    new_ids = [i for i in assigned if i not in certainty]
    old_output = {i: {'pi_exact': legacy[i]['old_pi_exact'], 'weight_exact': legacy[i]['old_weight_exact']}
                  for i in certainty}
    for person in ('A', 'B'):
        p = people[person]
        identity = p.get('identity_code')
        require(isinstance(identity, str) and bool(identity) and identity.startswith('TOY-') == synthetic,
                'Actual/synthetic human identity mismatch')
        identities.append(identity)
        evidence(p.get('identity_evidence_binding'))
        require(set(p['cohorts']) == {'inherited', 'supplement'}, 'Both human cohort receipts required')
        for cohort, ids in [('inherited', certainty), ('supplement', new_ids)]:
            receipt = p['cohorts'][cohort]
            require(receipt.get('kind') == ('synthetic_first_submission' if synthetic else 'actual_locked_human_first_submission'),
                    'A real first submission cannot be synthesized')
            start = receipt['started_interval']
            earliest, latest = time(start.get('earliest')), time(start.get('latest'))
            received, locked = time(receipt.get('received_at')), time(receipt.get('locked_at'))
            require(earliest <= latest <= received <= locked, 'Human start/submission/lock times inconsistent')
            require(start.get('precision') in ('exact', 'day', 'approximate'), 'Honest start precision required')
            relation = 'before' if latest < frozen else 'after' if earliest >= frozen else 'overlaps'
            require(receipt.get('start_relation_to_new_design') == relation,
                    'Reported start relation must match actual/approximate interval')
            if cohort == 'inherited':
                inherited_timing[person] = {'relation': relation, 'started_interval': start}
                require(receipt.get('legacy_draw_binding') == view['legacy_draw_binding'], 'Original legacy assignment changed')
                evidence(receipt['legacy_draw_binding'])
                check_material_usage(receipt, view, inherited_person=person)
            else:
                require(drawn <= earliest,
                        'Supplement must be drawn before this cohort begins judgment')
                check_material_usage(receipt, view)
            require(receipt.get('machine_answers_visible') is False and
                    receipt.get('discussed_or_received_judgments_before_lock') is False,
                    'Human blinding/independent first judgment unknown or violated')
            require(receipt.get('is_first_submission') is True, 'Later revision cannot replace initial submission')
            evidence(receipt.get('raw_first_submission_binding'))
            evidence(receipt.get('execution_evidence_binding'))
            projection = receipt['projection']
            require(projection.get('source_raw_binding') == receipt['raw_first_submission_binding'],
                    'Projection does not bind original first-submission bytes')
            require(projection.get('values_unchanged') is True and projection.get('retain_missing_null_failed') is True,
                    'Projection must preserve values and all missing/null/failed rows')
            evidence(projection.get('review_evidence_binding'))
            projected = rows_by_id(projection['rows'])
            require(list(projected) == ids, 'Fixed cohort projection missing/extra/reordered IDs')
            for rid, row in projected.items():
                require(set(row) == {'unit_id', 'original_blind_id', 'original_row_locator'} and
                        isinstance(row['original_row_locator'], str) and row['original_row_locator'],
                        'Original row identity/locator required; labels not accepted here')
                if cohort == 'inherited':
                    require(row['original_blind_id'] == legacy[rid][person + '_blind_id'], 'Legacy blind ID changed')
            require(len({r['original_blind_id'] for r in projected.values()}) == len(ids), 'Duplicate blind identity')
            locks.append(locked)
    require(len(set(identities)) == 2, 'A/B must be distinct actual people')
    require(time(feedback['reviewed_through_at']) >= max(locks), 'Feedback/blinding review predates final first lock')
    if request['stage'] == 'machine_reference':
        ref = people['reference']
        require(ref.get('kind') == ('synthetic_adjudication' if synthetic else 'actual_human_adjudication'),
                'Actual human adjudication required')
        require(ref.get('machine_answers_visible') is False and ref.get('auto_agreement_or_AI_substitution') is False,
                'Reference must be actual machine-blind human adjudication')
        require(ref.get('identity_code', '').startswith('TOY-') == synthetic and bool(ref.get('identity_code')),
                'Reference identity required')
        evidence(ref.get('identity_evidence_binding'))
        evidence(ref.get('raw_first_submission_binding'))
        evidence(ref.get('execution_evidence_binding'))
        check_material_usage(ref, view)
        require(ref.get('unit_ids') == list(assigned), 'Reference must retain every assigned unit')
        require(time(ref.get('started_at')) >= max(locks) and
                time(ref.get('started_at')) <= time(ref.get('locked_at')) <= time(ref.get('first_machine_comparison_at')),
                'Human adjudication must follow locked initial judgments and precede machine comparison')
        require(time(feedback['reviewed_through_at']) >= time(ref['locked_at']),
                'Feedback review must cover actual reference lock')

    return {'schema': 'reuse-metadata-component-receipt-v1',
            'status': 'synthetic_metadata_control_passed' if synthetic else 'metadata_contract_checks_passed_only',
            'actual_ROOT_adoption': False,
            'synthetic_only': synthetic, 'metadata_component_only': True,
            'statistical_execution_authorized': False, 'formal_validation_complete': False,
            'legacy_before_answers_flag_created': False, 'stage': request['stage'],
            'target_N': len(target), 'certainty_N': len(certainty), 'supplement_frame_N': len(supplement),
            'supplement_assigned_N': len(new_ids), 'all_assigned_N': len(assigned),
            'new_design_sha256': canonical(design), 'request_sha256': canonical(request),
            'new_design_weights': [{'unit_id': i, 'pi_exact': r['pi_exact'], 'weight_exact': r['weight_exact']}
                                   for i, r in assigned.items()],
            'legacy_weights_preserved_separately': old_output,
            'inherited_start_timing': inherited_timing,
            'supplement_started_after_own_draw': True,
            'preserve_all_missing_null_failed': True,
            'next_stage_requires': 'separately reviewed complete label/source join and truthful replacement of all old temporal gates, including engine.review_eligibility'}


def admit_synthetic(request_path, view_path):
    return validate_metadata(read_json(request_path), read_json(view_path), synthetic=True)


def admit_real(request_path):
    registry_path = HERE / 'ROOT-registry.UNADOPTED.json'
    require(binding(registry_path)['sha256'] == REGISTRY_SHA, 'ROOT registry external pin differs')
    registry = read_json(registry_path)
    request = read_json(request_path)
    require(request.get('synthetic_only') is False, 'Synthetic input cannot impersonate project admission')
    entry = registry.get('registrations', {}).get(request.get('registration_id'))
    require(isinstance(entry, dict), 'No ROOT-adopted reuse registration; actual project admission refused')
    require(entry.get('request_binding') == binding(request_path), 'ROOT registration does not bind exact request')
    approval = read_json(verify(entry.get('ROOT_approval_binding')))
    require(approval.get('status') == 'ROOT_independently_reviewed_actual_reuse_receipts' and
            approval.get('control_or_synthetic') is False and approval.get('request_binding') == binding(request_path),
            'Actual external ROOT receipt review missing')
    result = validate_metadata(request, current_view(), synthetic=False)
    result.update(status='ROOT_registered_metadata_component_passed', actual_ROOT_adoption=True,
                  ROOT_registry_binding=binding(registry_path), ROOT_approval_binding=entry['ROOT_approval_binding'],
                  registered_request_binding=entry['request_binding'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True)
    parser.add_argument('--synthetic-view')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = admit_synthetic(args.request, args.synthetic_view) if args.synthetic_view else admit_real(args.request)
    # Never overwrite an existing receipt, request, original or source artifact.
    with Path(args.output).open('x') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()

"""One combined regression run after disjoint E/Ec/F composition.

The common 353 controls are loaded once. Fixed domain controls retain original
expectations and provenance. These are development checks, never human accuracy.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import sys
import traceback
from datetime import datetime, timezone

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
A14 = HERE.parent / 'rule-repair-v14'
VERSIONS = ROOT / '06-coding/rule-five-dimension-joint-root/versions'
BASE = VERSIONS / 'joint-v13b-clinical-safety-role-root'
RESIDUAL_BASE = VERSIONS / 'joint-v15-E-Ec-F-integrated-root'
CANDIDATE = VERSIONS / 'joint-v15b-complete-repair-root'
NAMES = ('evidence', 'source_packet', 'source_receipts', 'relations', 'dimensions')
DOMAIN_INDEXES = {'E': A14 / 'E-source/controls-index-corrected.json',
                  'Ec': A14 / 'Ec-source/controls-index-geometry.json',
                  'F': A14 / 'F-final/controls-index.json',
                  'S_residual': HERE / 'S-residual/controls-index.json',
                  'F_residual': HERE / 'F-residual/controls-index.json'}
DEFAULT_MUTABLE = {'E': ['E'], 'Ec': ['Ec'], 'F': ['F'],
                   'S_residual': ['S'], 'F_residual': ['F'], 'legacy': []}
NEW_DEPENDENCY_PATHS = {'E_explicit_content_scope', 'S_finite_standard_scope', 'E_finite_standard_scope',
                        'F_finite_standard_scope', 'price_arrangement', 'F_requested_qualification_scope'}


def read(path):
    return json.loads(path.read_text())


def binding(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def modules(directory):
    return {name: load_module(name, directory / (name + '.py')) for name in NAMES}


def cases_and_bindings():
    driver = load_module('frozen_F_controls', A14 / 'F/run_controls.py')
    cases, files = [], []
    for path in driver.input_files():
        if path.parent == A14 / 'F':
            continue
        files.append(path)
        data = read(path)
        for case in data.get('real_cases', []) + data.get('cases', []):
            if path.name == 'new20-fixed-before-execution.json' and case['name'] not in driver.PARENT_CONTROL_NAMES:
                continue
            cases.append(dict(copy.deepcopy(case), control_file=str(path), domain='legacy'))
    assert len(cases) == 353
    for domain, path in DOMAIN_INDEXES.items():
        files.append(path)
        for case in read(path)['cases']:
            assert 'control_file' in case
            cases.append(dict(copy.deepcopy(case), domain=domain))
    keys = [(case['domain'], case['control_file'], case['name']) for case in cases]
    assert len(keys) == len(set(keys)), 'Duplicated control identity'
    return cases, files


def context_ids(value):
    found = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'context_evidence' and isinstance(child, list):
                found.update(q['context_id'] for q in child if isinstance(q, dict) and q.get('context_id'))
            found.update(context_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(context_ids(child))
    return found


def source_preserved(before, after):
    for key in ('source_events', 'private_I_requests'):
        if before[key] != after[key]:
            return False
    for key in ('material_requests', 'source_requests'):
        old, new = before[key], after[key]
        cursor, added = 0, []
        for request in new:
            if cursor < len(old) and request == old[cursor]:
                cursor += 1
            else:
                added.append(request)
        if cursor != len(old):
            return False
        for request in added:
            proof = after['routing_proof'] or {}
            if not (request.get('path') in NEW_DEPENDENCY_PATHS
                    and request.get('dependency_status') == 'stopped'
                    and request.get('necessary_dependency', True) is True
                    and request in after['material_requests']
                    and request in after['source_requests']
                    and request.get('stop_reason') in proof.get('dependency_stop_reasons', [])
                    and proof.get('actual_driver_stop_guard_passed') is True
                    and any(route.get('request') == request and route.get('dimensions')
                            for route in proof.get('checked_material_routes', []))):
                return False
    return True


def main():
    run_name = sys.argv[1]
    assert run_name and Path(run_name).name == run_name and run_name not in ('.', '..')
    composition = read(HERE / 'composition-complete.json')
    for source in composition['output']:
        assert binding(Path(source['path'])) == source
    cases, files = cases_and_bindings()
    cross_path = HERE / 'cross-domain-preservation-contracts.json'
    cross_contract = read(cross_path)
    files.append(cross_path)
    assert binding(Path(cross_contract['original_E_index']['path'])) == cross_contract['original_E_index']
    cross_revisions = {}
    for item in cross_contract['contracts']:
        assert binding(Path(item['source_assessment']['path'])) == item['source_assessment']
        assert binding(Path(item['source_control_index']['path'])) == item['source_control_index']
        target = item['target']
        matches = [c for c in cases if all(c[k] == target[k] for k in ('domain', 'control_file', 'name'))]
        source_matches = [c for c in cases if c['domain'] == item['source_domain'] and c['name'] == item['source_case']]
        assert len(matches) == len(source_matches) == 1
        target_case, source_case = matches[0], source_matches[0]
        assert target_case['domain'] == 'E' and source_case['domain'] in ('S_residual', 'F_residual')
        assert source_case.get('hard_assertion', True)
        dim = 'S' if source_case['domain'] == 'S_residual' else 'F'
        assert item['additional_mutable_dimensions'] == [dim] and dim in source_case['expected']
        assert dim not in target_case['expected']
        assert target_case['packet_binding'] == source_case['packet_binding']
        key = tuple(target[k] for k in ('domain', 'control_file', 'name'))
        assert key not in cross_revisions
        cross_revisions[key] = (item, {dim: source_case['expected'][dim]})
    revisions = {}
    for case in cases:
        revision = case.get('preservation_contract_revision')
        if not revision:
            continue
        assert case['domain'] in ('E', 'Ec') and case['expected'] == {}
        bound = revision['contract_binding']
        assert binding(Path(bound['path'])) == bound
        flags = revision['superseded_flags']
        assert flags and set(flags) <= {'require_E_unchanged', 'must_preserve_Ec_complete_decision'}
        assert all(case.get(flag) is True for flag in flags)
        replacements = [q for q in cases if q['domain'] == case['domain'] and q['name'] == revision['replacement_case_name']]
        assert len(replacements) == 1
        replacement = replacements[0]
        assert replacement.get('hard_assertion', True) and replacement['expected']
        assert case['packet_binding']['path'] == replacement['packet_binding']['path']
        assert case['packet_binding']['sha256'] == replacement['packet_binding']['sha256']
        revisions[(case['domain'], case['control_file'], case['name'])] = (revision, replacement['expected'])
    prepared = []
    for case in cases:
        if 'packet_binding' in case:
            item = case['packet_binding']
            actual = binding(Path(item['path']))
            assert all(actual[key] == item[key] for key in ('path', 'bytes', 'sha256'))
            packet = read(Path(item['path']))
            bundle = packet['source_bundle']
            raw = json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            assert hashlib.sha256(raw).hexdigest() == packet['source_bundle_sha256']
            for key in ('output_id', 'source_id', 'source_bundle_sha256'):
                if key in item:
                    assert item[key] == packet[key]
            if 'source_bundle_utf8_bytes' in item:
                assert item['source_bundle_utf8_bytes'] == len(raw)
        else:
            bundle = case.get('synthetic_bundle')
        assert bundle is not None or 'semantic_input' in case
        prepared.append((case, bundle))
    out = HERE / run_name
    out.mkdir(exist_ok=False)
    save(out / 'pre-execution-seal.json', {
        'at_utc': datetime.now(timezone.utc).isoformat(),
        'driver': binding(Path(__file__)), 'composition': binding(HERE / 'composition-complete.json'),
        'controls': [binding(path) for path in files], 'case_N': len(cases),
        'baseline': [binding(BASE / (name + '.py')) for name in NAMES],
        'residual_control_baseline': [binding(RESIDUAL_BASE / (name + '.py')) for name in NAMES],
        'candidate': composition['output'], 'common353_loaded_once': True,
        'scope': 'development_regression_only', 'population_calls': 0, 'model_calls': 0,
    })
    old, residual_old, new = modules(BASE), modules(RESIDUAL_BASE), modules(CANDIDATE)
    route = load_module('integrated_routing_check', A14 / 'E-source/routing_checks.py')
    active, denied = [False], []

    def audit(event, args):
        if active[0] and event == 'open':
            denied.append(str(args[0]))
            raise RuntimeError('Classifier filesystem I/O denied')

    sys.addaudithook(audit)

    def run(loaded, unit, bundle, check_route):
        before = copy.deepcopy(unit)
        active[0] = True
        try:
            view = loaded['relations'].RelationView(copy.deepcopy(unit))
            decisions = loaded['dimensions'].judge(view)
            loaded['evidence'].validate_decisions(unit, decisions)
            assert view.unit == before
        finally:
            active[0] = False
        routing = None
        if check_route and bundle is not None and any(r.get('path') in NEW_DEPENDENCY_PATHS for r in view.material_requests):
            routing = route.check_actual_route(loaded, view, decisions, bundle)
        return {'decisions': decisions, 'values': {d: v['value'] for d, v in decisions.items()},
                'relations': view.traces(), 'material_requests': view.material_requests,
                'source_requests': view.source_requests, 'source_events': view.source_view_events,
                'private_I_requests': copy.deepcopy(getattr(view, 'v11_protected_data_requests', [])),
                'routing_proof': routing}

    results = []
    for case, bundle in prepared:
        row = {key: value for key, value in case.items() if key not in ('semantic_input', 'synthetic_bundle')}
        try:
            unit = new['source_packet'].semantic_unit(bundle) if bundle is not None else case['semantic_input']
            comparison = residual_old if case['domain'] in ('S_residual', 'F_residual') else old
            baseline, candidate = run(comparison, unit, bundle, False), run(new, unit, bundle, True)
            mutable = set(case.get('mutable_dimensions', DEFAULT_MUTABLE[case['domain']]))
            original_mutable = set(mutable)
            cross_info = cross_revisions.get((case['domain'], case['control_file'], case['name']))
            if cross_info:
                mutable.update(cross_info[0]['additional_mutable_dimensions'])
            assert mutable <= {'S', 'E', 'Ec', 'F'}
            assert 'S' not in mutable or case['domain'] in ('E', 'S_residual')
            assert case['domain'] != 'legacy' or not mutable
            protected = {'S', 'E', 'Ec', 'I', 'F'} - mutable
            checks = {
                'fixed_expected_values': all(candidate['values'][d] == value for d, value in case['expected'].items()),
                'protected_complete_decisions': all(baseline['decisions'][d] == candidate['decisions'][d] for d in protected),
                'source_contract': source_preserved(baseline, candidate),
            }
            row['comparison_baseline'] = str(RESIDUAL_BASE if comparison is residual_old else BASE)
            if cross_info:
                checks['same_packet_residual_expected'] = all(candidate['values'][d] == value for d, value in cross_info[1].items())
                row['versioned_cross_domain_preservation'] = {
                    'contract': cross_info[0], 'replacement_expected': cross_info[1],
                    'original_E_only_protection_unchanged': all(baseline['decisions'][d] == candidate['decisions'][d]
                        for d in {'S', 'E', 'Ec', 'I', 'F'} - original_mutable)}
            new_F_relations = [q for q in candidate['relations']
                if q.get('details', {}).get('v9_semantic_path') == 'current_form_suitability_gap_qualification']
            if new_F_relations:
                read_contexts = {q.get('resource_id') for q in candidate['source_events']
                    if q.get('view') == 'text' and q.get('event_kind') == 'actual_structured_json_scan'}
                used_contexts = context_ids(new_F_relations)
                checks['new_F_evidence_actual_read'] = bool(used_contexts) and used_contexts <= read_contexts
            revision_info = revisions.get((case['domain'], case['control_file'], case['name']))
            superseded = set(revision_info[0]['superseded_flags']) if revision_info else set()
            old_preservation = {}
            if case.get('require_E_unchanged'):
                value = baseline['decisions']['E'] == candidate['decisions']['E']
                (old_preservation if 'require_E_unchanged' in superseded else checks)['reserved_E_decision'] = value
            if case.get('require_Ec_unchanged') or case.get('must_preserve_Ec_complete_decision'):
                value = baseline['decisions']['Ec'] == candidate['decisions']['Ec']
                (old_preservation if 'must_preserve_Ec_complete_decision' in superseded else checks)['reserved_Ec_decision'] = value
            if revision_info:
                checks['new_same_material_contract'] = all(candidate['values'][d] == value for d, value in revision_info[1].items())
                row['superseded_preservation_observation'] = {'original_checks': old_preservation,
                    'explicit_contract': revision_info[0], 'replacement_expected': revision_info[1]}
            assertion = case.get('source_consumption_assertions')
            if assertion:
                consumed = context_ids(candidate['decisions'][assertion['dimension']])
                checks['forbidden_contexts_absent'] = not (consumed & set(assertion.get('forbidden_final_context_ids', [])))
                checks['required_contexts_consumed'] = set(assertion.get('required_final_context_ids', [])) <= consumed
            for version in ('v10', 'v11'):
                if case.get('must_not_add_' + version + '_positive'):
                    kind = version + ('_protected_data_I_relationship' if version == 'v11' else '_IF_relationship')
                    checks['no_unproved_' + version] = not any(q['kind'] == kind for q in candidate['relations'])
            if case.get('must_not_add_unproved_whole_programme_positive'):
                decision = candidate['decisions'][case['pending_dimensions'][0]]
                checks['restricted_mother_no_new_positive'] = not (decision['value'] == 1 and decision['basis_path'].startswith(('v9_', 'v10_', 'v11_')))
            row.update(baseline=baseline, candidate=candidate, checks=checks,
                       baseline_expected_match=all(baseline['values'][d] == value for d, value in case['expected'].items()),
                       changed_dimensions=[d for d in baseline['decisions'] if baseline['decisions'][d] != candidate['decisions'][d]],
                       passed=all(checks.values()))
        except Exception as exc:
            row.update(passed=False, error={'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()})
        results.append(row)
    hard = [row for row in results if row.get('hard_assertion', True)]
    summary = {
        'at_utc': datetime.now(timezone.utc).isoformat(), 'case_N': len(results),
        'domain_counts': {domain: sum(row['domain'] == domain for row in results) for domain in ('legacy', *DOMAIN_INDEXES)},
        'hard_N': len(hard), 'hard_passed_N': sum(row['passed'] for row in hard),
        'hard_failed': [{key: row.get(key) for key in ('domain', 'name', 'expected', 'checks', 'baseline_expected_match', 'error')} for row in hard if not row['passed']],
        'pending_N': len(results) - len(hard),
        'pending': [{'domain': row['domain'], 'name': row['name'], 'candidate_values': row.get('candidate', {}).get('values'), 'checks': row.get('checks')} for row in results if not row.get('hard_assertion', True)],
        'protected_decision_failures': [row['name'] for row in results if row.get('checks', {}).get('protected_complete_decisions') is False],
        'source_contract_failures': [row['name'] for row in results if row.get('checks', {}).get('source_contract') is False],
        'technical_errors': [row['name'] for row in results if row.get('error')],
        'explicitly_superseded_preservation_observations': [
            {'name': row['name'], **row['superseded_preservation_observation']}
            for row in results if row.get('superseded_preservation_observation')],
        'versioned_cross_domain_preservations': [
            {'name': row['name'], **row['versioned_cross_domain_preservation']}
            for row in results if row.get('versioned_cross_domain_preservation')],
        'classifier_filesystem_attempts': denied,
        'original_expectations_retained': True, 'formal_accuracy_claimed': False,
        'population_calls': 0, 'model_calls': 0, 'production_adopted': False,
    }
    save(out / 'results.json', results)
    save(out / 'summary.json', summary)
    save(out / 'output-seal.json', {'files': [binding(path) for path in sorted(out.iterdir()) if path.is_file()], 'self_excluded': True})
    print(json.dumps({key: value for key, value in summary.items() if key != 'pending'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

"""Bounded development regression checks against the frozen v13b baseline; Ec may change, S/E/I/F must remain byte-identical.

No production execution, output replacement, accuracy estimate or sample draw.
Run once per changed candidate: python -B run_controls.py <unique-run-name>.
"""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import importlib.util
import json
import sys
import traceback

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VERSIONS = ROOT / '06-coding/rule-five-dimension-joint-root/versions'
BASE = VERSIONS / 'joint-v13b-clinical-safety-role-root'
CANDIDATE = VERSIONS / 'joint-v14ec-economic-proposition-root'
OLD_HERE = ROOT / '10-closure-20261012/rule-repair-v12'
NAMES = ('evidence', 'source_packet', 'source_receipts', 'relations', 'dimensions')
PARENT_CONTROL_NAMES = {'safety_parent_wrong_target', 'safety_parent_other_component_reused_pid',
                        'effect_indicator_not_safety_sibling', 'pure_structure_closed_list_stays_zero'}


def read(path):
    return json.loads(path.read_text())


def binding(path):
    b = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def modules(directory):
    result = {}
    for name in NAMES:
        spec = importlib.util.spec_from_file_location(name, directory / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        result[name] = module
    return result


def input_files():
    design = ROOT / '08-audits/v9-generic-relationship-repair-design-sol/revision02-bidirectional-before-implementation'
    paths = [design / 'real-controls-fixed-before-edit.json', design / 'synthetic-controls-fixed-before-edit.json']
    paths += [VERSIONS / 'joint-v9-generic-relationship-sol' / n for n in (
        'supplemental-controls-before-attempt02.json', 'supplemental-controls-b-before-attempt02.json',
        'supplemental-controls-before-attempt04.json', 'supplemental-controls-before-attempt06.json')]
    paths += [ROOT / '08-audits' / n for n in (
        'v10-generic-relationship-repair-sol/new-controls-fixed-before-edit.json',
        'v10-generic-relationship-repair-sol/additional-counter-controls-fixed-before-attempt02.json',
        'e-complete-response-coverage-repair-sol/targeted24-fixed-before-second-edit.json',
        'v11-protected-data-role-repair-sol/new-role-controls-fixed-before-edit.json')]
    paths.append(ROOT / '08-audits/SE-Ec-v2-independent-controls-sol/new20-fixed-before-execution.json')
    return paths + [OLD_HERE / n for n in ('real-controls.json', 'safety-controls-revision03.json',
                                     'fairness-controls.json', 'fairness-service-supplement-controls.json',
                                     'safety-field-content-additional-controls.json',
                                     'fairness-current-role-supplement-controls.json',
                                     'current-material-supplement-controls.json')] + [ROOT / '10-closure-20261012/rule-repair-v13' / n for n in ('clinical-safety-controls-fixed-before-edit.json', 'clinical-safety-role-six-fixed-before-attempt02.json')] + [HERE / 'controls-fixed-before-edit.json']


def main():
    name = sys.argv[1]
    assert name and Path(name).name == name and name not in ('.', '..')
    out = HERE / name
    out.mkdir(exist_ok=False)
    snapshot = out / 'code-snapshot'
    snapshot.mkdir()
    plan = read(HERE / 'preparation.json')
    for source in plan['base_files']:
        assert binding(Path(source['path'])) == source, source['path']
    for n in NAMES:
        (snapshot / (n + '.py')).write_bytes((CANDIDATE / (n + '.py')).read_bytes())
    for n in ('evidence', 'source_packet', 'source_receipts'):
        assert (BASE / (n + '.py')).read_bytes() == (snapshot / (n + '.py')).read_bytes()
    cases = []
    files = input_files()
    for path in files:
        data = read(path)
        for case in data.get('real_cases', []) + data.get('cases', []):
            if path.name == 'new20-fixed-before-execution.json' and case['name'] not in PARENT_CONTROL_NAMES:
                continue
            case = copy.deepcopy(case)
            case['control_file'] = str(path)
            case['control_role'] = 'new_v14ec' if path.parent == HERE else 'prior353_regression'
            cases.append(case)
    assert sum(c['control_role'] == 'prior353_regression' for c in cases) == 353
    assert len({(c['control_file'], c['name']) for c in cases}) == len(cases)
    prepared = []
    for case in cases:
        if 'packet_binding' in case:
            source = case['packet_binding']
            assert binding(Path(source['path'])) == source
            prepared.append((case, read(Path(source['path']))['source_bundle']))
        elif 'synthetic_bundle' in case:
            prepared.append((case, case['synthetic_bundle']))
        else:
            prepared.append((case, None))
    save(out / 'pre-execution-seal.json', {
        'at_utc': datetime.now(timezone.utc).isoformat(),
        'baseline': [binding(BASE / (n + '.py')) for n in NAMES],
        'candidate': [binding(snapshot / (n + '.py')) for n in NAMES],
        'driver': binding(Path(__file__)), 'controls': [binding(p) for p in files],
        'additional_prior_parent_control_selection': sorted(PARENT_CONTROL_NAMES),
        'control_revision_history': [binding(OLD_HERE / n) for n in (
            'safety-controls.json', 'safety-controls-revision02.json', 'control-expectation-review.json')],
        'case_N': len(cases), 'scope': 'exposed development controls, never independent accuracy',
        'production_calls': 0, 'model_calls': 0,
    })
    old = modules(BASE)
    new = modules(snapshot)
    active = [False]
    denied = []

    def audit(event, args):
        if active[0] and event == 'open':
            denied.append(str(args[0]))
            raise RuntimeError('Classifier filesystem I/O denied')

    sys.addaudithook(audit)

    def run(loaded, unit):
        original = copy.deepcopy(unit)
        active[0] = True
        try:
            view = loaded['relations'].RelationView(copy.deepcopy(unit))
            decisions = loaded['dimensions'].judge(view)
            loaded['evidence'].validate_decisions(unit, decisions)
            assert view.unit == original, 'Classifier changed the semantic input'
            return {'decisions': decisions, 'values': {d: x['value'] for d, x in decisions.items()},
                    'relations': view.traces(), 'material_requests': view.material_requests,
                    'source_requests': view.source_requests, 'source_events': view.source_view_events,
                    'private_I_requests': copy.deepcopy(getattr(view, 'v11_protected_data_requests', []))}
        finally:
            active[0] = False

    results = []
    for case, bundle in prepared:
        row = {k: v for k, v in case.items() if k not in ('semantic_input', 'synthetic_bundle')}
        try:
            unit = new['source_packet'].semantic_unit(bundle) if bundle is not None else case['semantic_input']
            baseline, candidate = run(old, unit), run(new, unit)
            row.update(baseline=baseline, candidate=candidate,
                       baseline_expected_match=all(baseline['values'][d] == value for d, value in case['expected'].items()),
                       expected_match=all(candidate['values'][d] == value for d, value in case['expected'].items()),
                       unchanged_S_E_I_F=all(baseline['decisions'][d] == candidate['decisions'][d] for d in ('S', 'E', 'I', 'F')),
                       source_state_equal=all(baseline[k] == candidate[k] for k in ('material_requests', 'source_requests', 'source_events', 'private_I_requests')),
                       changed_dimensions=[d for d in baseline['decisions'] if baseline['decisions'][d] != candidate['decisions'][d]])
            extra = {}
            source_assertions = case.get('source_consumption_assertions')
            if source_assertions:
                consumed = set()

                def collect_contexts(value):
                    if isinstance(value, dict):
                        for key, child in value.items():
                            if key == 'context_evidence' and isinstance(child, list):
                                consumed.update(q['context_id'] for q in child if isinstance(q, dict) and q.get('context_id'))
                            collect_contexts(child)
                    elif isinstance(value, list):
                        for child in value:
                            collect_contexts(child)

                collect_contexts(candidate['decisions'][source_assertions['dimension']])
                extra['forbidden_final_contexts_absent'] = not (consumed & set(source_assertions.get('forbidden_final_context_ids', [])))
                extra['required_final_contexts_present'] = set(source_assertions.get('required_final_context_ids', [])) <= consumed
                row['consumed_context_ids_in_asserted_dimension'] = sorted(consumed)
            for version in ('v10', 'v11'):
                if case.get('must_not_add_' + version + '_positive'):
                    kind = version + ('_protected_data_I_relationship' if version == 'v11' else '_IF_relationship')
                    extra['no_unproved_' + version + '_positive'] = not any(x['kind'] == kind for x in candidate['relations'])
            if case.get('must_not_add_unproved_whole_programme_positive'):
                dim = case['pending_dimensions'][0]
                decision = candidate['decisions'][dim]
                extra['restricted_mother_no_new_positive'] = not (decision['value'] == 1 and decision['basis_path'].startswith(('v9_', 'v10_', 'v11_')))
            if case.get('must_preserve_Ec_complete_decision'):
                extra['reserved_Ec_complete_decision_unchanged'] = baseline['decisions']['Ec'] == candidate['decisions']['Ec']
            row['extra_checks'] = extra
            row['pass'] = row['expected_match'] and row['unchanged_S_E_I_F'] and row['source_state_equal'] and all(extra.values())
        except Exception as exc:
            row.update({'pass': False, 'error': {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}})
        results.append(row)
    hard = [row for row in results if row.get('hard_assertion', True)]
    summary = {
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'case_N': len(results), 'legacy_N': 353,
        'hard_N': len(hard), 'hard_passed_N': sum(row['pass'] for row in hard),
        'hard_failed': [{k: row.get(k) for k in ('name', 'control_role', 'expected', 'error', 'baseline_expected_match', 'expected_match', 'unchanged_S_E_I_F', 'source_state_equal', 'extra_checks')} for row in hard if not row['pass']],
        'pending_N': len(results) - len(hard),
        'pending': [{'name': row['name'], 'expected': row['expected'], 'candidate_values': row.get('candidate', {}).get('values'), 'pass': row['pass']} for row in results if not row.get('hard_assertion', True)],
        'protected_dimension_changes': [row['name'] for row in results if row.get('unchanged_S_E_I_F') is False],
        'source_state_changes': [row['name'] for row in results if row.get('source_state_equal') is False],
        'changed_cases': [{'name': row['name'], 'dimensions': row.get('changed_dimensions'), 'before': row.get('baseline', {}).get('values'), 'after': row.get('candidate', {}).get('values')} for row in results if row.get('changed_dimensions')],
        'filesystem_access_attempts': denied, 'all_cases_retained': True,
        'formal_validation': False, 'production_outputs_modified': False, 'model_calls': 0,
    }
    save(out / 'results.json', results)
    save(out / 'summary.json', summary)
    save(out / 'output-seal.json', {'files': [binding(p) for p in sorted(out.rglob('*')) if p.is_file()], 'self_excluded': True})
    print(json.dumps({k: v for k, v in summary.items() if k not in ('changed_cases', 'pending')},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

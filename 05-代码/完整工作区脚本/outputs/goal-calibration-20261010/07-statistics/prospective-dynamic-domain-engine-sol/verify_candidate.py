"""Read-back and structural preservation checks; no actual label inputs."""
import ast
import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = __import__('importlib.util', fromlist=['util']).spec_from_file_location('candidate_admission_verify', HERE / 'scope_admission.py')
a = __import__('importlib.util', fromlist=['util']).module_from_spec(spec)
spec.loader.exec_module(a)


def write(name, value):
    with (HERE / name).open('x') as out:
        json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write('\n')


def main():
    base = (HERE / 'frozen_year_core.py').read_text()
    candidate = (HERE / 'metrics_engine.py').read_text()
    base_tree, new_tree = ast.parse(base), ast.parse(candidate)
    base_funcs = {n.name: ast.dump(n, include_attributes=False) for n in base_tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    new_funcs = {n.name: ast.dump(n, include_attributes=False) for n in new_tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    changed = [name for name, value in base_funcs.items() if new_funcs.get(name) != value]
    a.require(changed == ['prepare', 'review_eligibility', 'analyze'], 'Unexpected mathematical or annual function alteration')
    a.require(set(new_funcs) - set(base_funcs) == {'_admit_registered_scope'}, 'Unexpected added statistical function')
    a.require(a.binding(HERE / 'frozen_year_core.py')['sha256'] == a.FROZEN_STATISTICAL_CORE_SHA256, 'Year core copied bytes changed')
    admission_sha = a.binding(HERE / 'scope_admission.py')['sha256']
    a.require("_ADMISSION_SHA256='" + admission_sha + "'" in candidate, 'Engine admission code pin differs')
    a.require(a.binding(a.REGISTRY_PATH)['sha256'] == a.REGISTRY_SHA256, 'ROOT empty registry pin differs')
    registry = a.strict_json(a.REGISTRY_PATH.read_text())
    a.require(registry['registrations'] == {} and registry['actual_registered_scope_N'] == 0, 'Current actual scope adopted unexpectedly')
    guarded = (
        "if named_domains and meta.get('scope',{}).get('kind')=='full_4481_audit' and domain_N!={'remaining':1444,'exposed':3037}:\n        raise DataError('Named full_4481_audit requires remaining1444 and exposed3037')",
        "if named_domains and meta.get('scope',{}).get('kind')=='remaining_1444' and domain_N!={'remaining':1444}:\n        raise DataError('Named remaining_1444 scope requires only remaining1444')",
    )
    a.require(all(g in base and g in candidate for g in guarded), 'Historical domain guard source changed')
    base_constants = {n.targets[0].id: ast.dump(n.value, include_attributes=False) for n in base_tree.body if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}
    new_constants = {n.targets[0].id: ast.dump(n.value, include_attributes=False) for n in new_tree.body if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}
    a.require(all(new_constants.get(k) == v for k, v in base_constants.items()), 'Frozen statistical constant changed')
    inputs = a.strict_json((HERE / 'input-bindings.json').read_text())
    inputs_equal = {k: a.binding(v['path']) == v for k, v in inputs['frozen_inputs'].items()}
    a.require(all(inputs_equal.values()), 'Previously frozen input changed')
    old200_seal = a.load(inputs['frozen_inputs']['old200_adapter_seal'])
    members = old200_seal.get('output_members', old200_seal.get('members', []))
    if isinstance(members, dict):
        members = list(members.values())
    a.require(bool(members), 'Old200 seal member list absent')
    old200_equal = [a.binding(v['path']) == v for v in members]
    a.require(all(old200_equal), 'Previously sealed human200 preparation changed')
    plan = a.strict_json((HERE / 'controls-fixed-before-execution.json').read_text())
    final = a.strict_json((HERE / 'control-results-final.json').read_text())
    a.require(final['cases_N'] == 29 and final['passed_N'] == 29 and final['failed_N'] == 0, 'Finite controls not passed')
    a.require(final['engine_binding'] == a.binding(HERE / 'metrics_engine.py') and final['admission_binding'] == a.binding(HERE / 'scope_admission.py'), 'Final finite control execution did not bind final code')
    controls_equal = [a.binding(c['input_binding']['path']) == c['input_binding'] for c in plan['cases']]
    a.require(all(controls_equal), 'Pre-fixed control input changed')
    wrapper = a.strict_json((HERE / 'wrapper-control-result.json').read_text())
    a.require(wrapper['passed'] is True and wrapper['candidate_admission_binding'] == a.binding(HERE / 'scope_admission.py'), 'Standalone wrapper control not bound to final code')
    stage = a.strict_json((HERE / 'stage-helper-control-results.json').read_text())
    a.require(stage['passed_N'] == 2 and stage['failed_N'] == 0 and stage['admission_code_binding'] == a.binding(HERE / 'scope_admission.py'), 'ROOT-added stage helper controls not bound to final code')
    cli_results = []
    # Same two pre-fixed negative cases, repeated at the CLI entry; no new cases.
    for cid in ('empty_ROOT_registry_actual_scope', 'synthetic_fixture_to_real_project'):
        case = next(c for c in plan['cases'] if c['case_id'] == cid)
        output = HERE / 'cases' / (cid + '.FORBIDDEN-CLI-output.json')
        a.require(not output.exists(), 'Negative CLI output already exists')
        command = [sys.executable, str(HERE / 'metrics_engine.py'), '--input', case['input_binding']['path'], '--output', str(output)]
        proc = subprocess.run(command, capture_output=True, text=True)
        a.require(proc.returncode != 0 and not output.exists(), 'Unapproved real scope produced a CLI metric output')
        cli_results.append({'case_id': cid, 'input_binding': case['input_binding'], 'command': command,
                            'returncode': proc.returncode, 'stderr': proc.stderr, 'stdout': proc.stdout,
                            'output_created': output.exists(), 'actual_statistics_N': 0,
                            'scope': 'repeat_of_fixed_negative_at_CLI_entry'})
    write('cli-negative-results.json', {'same_fixed_cases_repeated_N': 2, 'both_rejected_before_output': True, 'results': cli_results, 'actual_statistics_N': 0})
    diff = ''.join(difflib.unified_diff(base.splitlines(True), candidate.splitlines(True), fromfile='frozen_year_core.py:f6b33491', tofile='metrics_engine.py:dynamic-candidate'))
    with (HERE / 'candidate-engine.patch').open('x') as out:
        out.write(diff)
    write('structural-preservation-and-input-readback.json', {
        'status': 'byte_and_AST_checks_passed', 'code_binding': a.binding(__file__),
        'engine_binding': a.binding(HERE / 'metrics_engine.py'), 'admission_binding': a.binding(HERE / 'scope_admission.py'),
        'frozen_year_copy_binding': a.binding(HERE / 'frozen_year_core.py'),
        'unchanged_original_functions': [k for k in base_funcs if k not in changed],
        'changed_original_functions': changed, 'added_admission_only_function': ['_admit_registered_scope'],
        'statistical_constants_AST_identical': True, 'legacy1444_3037_guards_text_identical': True,
        'new_mathematical_estimator_N': 0, 'new_CI_gate_N': 0,
        'input_readback_equal': inputs_equal, 'sealed_old200_member_N': len(members), 'sealed_old200_all_members_unchanged': all(old200_equal),
        'fixed29_case_inputs_equal': controls_equal, 'original_scope_unique_controls_N': 30,
        'ROOT_additional_pure_stage_helper_controls_N': 2, 'total_unique_controls_N': 32,
        'pure_stage_helper_not_actual_human_first_or_ROOT_admission': True,
        'actual_ROOT_registration_N': 0, 'actual_draw_N': 0, 'actual_human_or_reference_N': 0,
        'partial_LLM_labels_read_N': 0, 'actual_statistics_N': 0,
    })
    print(json.dumps({'original_scope_controls': 30, 'ROOT_additional_stage_helpers': 2, 'passed_total': 32, 'unchanged_functions': len(base_funcs) - len(changed), 'old200_unchanged_members': len(members), 'actual_statistics': 0}))


if __name__ == '__main__':
    main()

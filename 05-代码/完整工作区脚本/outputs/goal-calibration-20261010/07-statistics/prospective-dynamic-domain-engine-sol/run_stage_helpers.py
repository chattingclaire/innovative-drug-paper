"""ROOT-authorized pure helper checks; not a project admission or statistics."""
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('stage_control_admission', HERE / 'scope_admission.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def main():
    path = HERE / 'stage-helper-controls-fixed-before-execution.json'
    plan = a.strict_json(path.read_text())
    results = []
    for case in plan['cases']:
        item = {'case_id': case['case_id'], 'input_metadata': case['metadata'], 'expected': case['expected']}
        try:
            receipt = a.validate_stage_attestations(case['metadata'])
            passed = case['expected'].startswith('accept') and receipt['ROOT_scope_or_human_admission'] is False
            item.update(observed='pure_helper_contract_accepted', passed=passed, helper_receipt=receipt)
        except ValueError as error:
            item.update(observed='pure_helper_contract_rejected',
                        passed=case['expected'].startswith('reject') and 'reference_before_machine_comparison' in str(error),
                        error={'type': type(error).__name__, 'message': str(error)})
        results.append(item)
    report = {'status': 'ROOT_additional_two_pure_stage_helper_controls_executed_once',
              'fixed_plan_binding': a.binding(path), 'execution_code_binding': a.binding(__file__),
              'admission_code_binding': a.binding(HERE / 'scope_admission.py'), 'cases': results,
              'passed_N': sum(x['passed'] for x in results), 'failed_N': sum(not x['passed'] for x in results),
              'actual_ROOT_scope_admission_N': 0, 'actual_human_first_execution_N': 0,
              'actual_labels_read_N': 0, 'actual_statistics_N': 0,
              'scope': 'Only stage flag dependencies; does not bypass empty ROOT registry, original-byte, actual-human or version gates'}
    with (HERE / 'stage-helper-control-results.json').open('x') as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
        out.write('\n')
    print(json.dumps({'helper_controls': 2, 'passed': report['passed_N'], 'actual_statistics': 0}))


if __name__ == '__main__':
    main()

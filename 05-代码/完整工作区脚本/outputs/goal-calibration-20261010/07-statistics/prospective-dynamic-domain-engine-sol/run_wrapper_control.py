"""Fixed self-consistent but unapproved wrapper control; no label input."""
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('wrapper_control_admission', HERE / 'scope_admission.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def main():
    plan_path = HERE / 'wrapper-control-fixed-before-execution.json'
    case = a.strict_json(plan_path.read_text())
    result = {'case_id': case['case_id'], 'pre_fixed_control_binding': a.binding(plan_path),
              'execution_code_binding': a.binding(__file__),
              'candidate_admission_binding': a.binding(HERE / 'scope_admission.py'),
              'synthetic_only': True, 'expected': case['expected']}
    try:
        wrapper = a.load(case['fixture_binding'])
        a.validate_original_frame_identity(case['fixture_binding'], wrapper['approved_record_ids'])
        result.update(passed=False, observed='unexpected_acceptance')
    except ValueError as error:
        result.update(passed=True, observed='rejected_unapproved_wrapper',
                      error={'type': type(error).__name__, 'message': str(error)})
    original = a.load(a.ORIGINAL_FRAME_IDS_BINDING)
    a.validate_original_frame_identity(a.ORIGINAL_FRAME_IDS_BINDING, original['approved_record_ids'])
    result.update(approved_original_metadata_only_verified=True, actual_results_or_statistics_N=0)
    with (HERE / 'wrapper-control-result.json').open('x') as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
        out.write('\n')
    print(json.dumps({'wrapper_control_passed': result['passed'], 'actual_statistics_N': 0}))


if __name__ == '__main__':
    main()

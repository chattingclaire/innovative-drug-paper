"""Four finite constructed input kinds and one actual all-blank v2 readback."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PACKAGE = ROOT / '09-delivery/formal800-human-final-release-v2-20261010-sol'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


adapter = load('_finite_null_adapter', HERE / 'adapter.py')
driver = load('_finite_null_human_first_driver', HERE / 'human_first_driver.py')
cases = []


def cell(address, value=None, kind=None):
    return {'address': address, 'present': value is not None, 'cell_type': kind,
            'raw_v': value if kind == 'n' else None, 'text': value if kind == 'inlineStr' else None,
            'formula': None, 'style_index': None, 'resolved_value': value}


def assert_case(kind, d, e, expected):
    d_before, e_before = copy.deepcopy(d), copy.deepcopy(e)
    actual = adapter.normalize(d, e)
    assert actual[:2] == expected, (kind, actual, expected)
    assert d == d_before and e == e_before, 'original cell must never be normalized in place'
    cases.append({'kind': kind, 'expected': list(expected), 'actual': list(actual),
                  'original_D': d, 'original_E': e, 'constructed_only': True})


assert_case('blank_or_incomplete', cell('D2'), cell('E2'), (None, 'unfilled'))
assert_case('blank_or_incomplete', cell('D2'), cell('E2', '请补材料', 'inlineStr'), (None, 'incomplete'))
assert_case('blank_or_incomplete', cell('D2'), cell('E2', '待定：  ', 'inlineStr'), (None, 'incomplete'))
for prefix in ('待定：', '待定:'):
    assert_case('lawful_null', cell('D2'), cell('E2', prefix + '缺同版程序第3页表2所指药物对象，需补该页原件。', 'inlineStr'), (None, 'lawful_null'))
assert_case('binary', cell('D2', '0', 'n'), cell('E2', '构造输入理由，非真人首判。', 'inlineStr'), (0, 'filled'))
assert_case('binary', cell('D2', '1', 'inlineStr'), cell('E2', '构造输入理由，非真人首判。', 'inlineStr'), (1, 'filled'))
for value in ('0', '1'):
    assert_case('contradictory', cell('D2', value, 'n'), cell('E2', '待定：缺上述页。', 'inlineStr'), (int(value), 'invalid'))

release_path = PACKAGE / 'release.json'
args = argparse.Namespace(command='dry-run', xlsx_a=str(PACKAGE / 'coder-A/formal800-A-frozen.xlsx'),
                          xlsx_b=str(PACKAGE / 'coder-B/formal800-B-frozen.xlsx'),
                          out=str(HERE / 'checks/actual-v2-blank'), release=str(release_path),
                          release_sha256=adapter.file_binding(release_path)['sha256'],
                          declaration_a=None, declaration_b=None)
report = adapter.run(args)
assert all(report['sides'][s]['counts'] == {'unfilled': 4000} and report['sides'][s]['issues'] == []
           and not report['sides'][s]['fully_completed'] for s in 'AB')
readback = driver.blank_mechanical_readback(args.out)
assert readback['all_blank_null_preserved'] and readback['independent_slots'] == 8000

# One explicit null control in a disposable in-memory copy of the actual blank
# ledger proves the projection route. It creates no research submission/output.
rows, design, management = driver.bridge.load_management()
ledger = [json.loads(x) for x in (Path(args.out) / 'derived-A.jsonl').read_text().splitlines()]
ledger[0].update(completion_status='lawful_null', finished_judgment=True, value=None,
                 reason='待定：构造缺同版程序第3页对象定位，仅测试投影。')
outputs, statuses = driver.bridge.project_xlsx_derived_cells(ledger, 'A', rows)
slot = next(x for x in statuses if x['unit_id'] == rows[0]['source_id'] and x['dimension'] == 'S') if ledger[0]['blind_id'] == rows[0]['A_blind_id'] else next(x for x in statuses if x['xlsx_completion_status'] == 'lawful_null')
assert slot['state'] == 'semantic_null' and slot['value'] is None
assert sum(x['state'] == 'semantic_null' for x in statuses) == 1
assert sum(x['state'] == 'blank' for x in statuses) == 3999

request = argparse.Namespace(upstream_reception=Path(args.out), coverage_only=False, calculate=False,
                             convert=True, statistics_metadata=None, statistics_metadata_sha256=None,
                             output_dir=HERE / 'checks/never-create-numerical-output')
try:
    driver.execute(request)
    raise AssertionError('actual blank dry-run cannot enter statistics conversion')
except driver.ReceptionError as error:
    rejection = str(error)
    assert 'dry-run' in rejection
assert not request._engine_analyze_called and not request.output_dir.exists()

for b in json.loads((HERE / 'supplement-bindings.json').read_text())['dependencies'].values():
    assert adapter.file_binding(b['path']) == b
result = {'status': 'passed', 'constructed_kinds_N': 4, 'constructed_cell_cases_N': len(cases),
          'constructed_case_results': cases, 'actual_blank_readback': readback,
          'one_disposable_null_projection': {'state': slot['state'], 'value': slot['value'], 'actual_human_result': False},
          'blank_numerical_entry_rejection': rejection, 'engine_analyze_called': False,
          'original_dependencies_unchanged': True, 'actual_human_submissions_N': 0,
          'old_16_tests_rerun': False, 'large_simulation_performed': False}
adapter.write_json(HERE / 'finite-checks.json', result)
print(json.dumps({'status': 'passed', 'constructed_kinds_N': 4, 'actual_blank_unfilled_N': 8000,
                  'lawful_null_projection': 'semantic_null', 'engine_analyze_called': False,
                  'actual_human_submissions_N': 0}))

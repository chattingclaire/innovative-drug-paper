"""Finite tests against four disposable copies; no human/machine research labels."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_adapter', HERE / 'adapter.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
fixture = HERE / 'checks/constructed-fixtures'
checks = []


def check(name, ok, evidence=None):
    checks.append({'name': name, 'passed': bool(ok), 'evidence': evidence})
    if not ok:
        raise AssertionError(name)


def args(command, left, right, name):
    return argparse.Namespace(command=command, xlsx_a=str(left), xlsx_b=str(right), out=str(HERE / 'checks' / name),
                              release=None, release_sha256=None, declaration_a=None, declaration_b=None)


_, mapping, data = adapter.preflight()
before = {key: adapter.file_binding(value['path']) for key, value in adapter.BIND['inputs'].items()}
blank = json.loads((HERE / 'checks/blank-dry-run/report.json').read_text())
check('actual blank A/B: 8000 unfilled, no content error, no actual reception',
      sum(blank['sides'][s]['counts'].get('unfilled', 0) for s in 'AB') == 8000 and
      all(not blank['sides'][s]['issues'] and not blank['sides'][s]['qualification']['content_reception_complete'] for s in 'AB'))
sparse_args = args('receive', fixture / 'A-sparse.xlsx', fixture / 'B-sparse.xlsx', 'sparse-content-pending')
sparse = adapter.run(sparse_args)
check('numeric and exact Excel text 0/1 normalize; six total filled',
      all(sparse['sides'][s]['content_valid'] and sparse['sides'][s]['counts'] == {'filled': 3, 'unfilled': 3997} for s in 'AB'))
left = [json.loads(x) for x in (Path(sparse_args.out) / 'derived-A.jsonl').read_text().splitlines()]
check('numeric/text original cell type and normalization retained',
      left[0]['value_cell']['cell_type'] == 'n' and left[0]['normalization'] == 'numeric_0_1' and
      left[1]['value_cell']['cell_type'] in ('s', 'inlineStr', 'str') and left[1]['normalization'] == 'exact_excel_text_0_1')
check('partial and missing release/human declarations stay pending',
      all(not sparse['sides'][s]['qualification']['eligible_for_downstream_content_handoff'] and
          'actual_release_not_supplied' in sparse['sides'][s]['qualification']['pending'] and
          'actual_human_independence_declaration_not_supplied' in sparse['sides'][s]['qualification']['pending'] for s in 'AB'))
diff = [json.loads(x) for x in (Path(sparse_args.out) / 'coordinator-private/disagreements.jsonl').read_text().splitlines()]
check('different A/B presentation order aligns by private source ID, independent values retained',
      len(diff) == 1 and diff[0]['A']['row'] == 2 and diff[0]['B']['row'] == 2417 and diff[0]['A']['value'] == 0 and diff[0]['B']['value'] == 1,
      {'A_row': 2, 'B_row': 2417, 'disagreements': len(diff)})
todo = [json.loads(x) for x in (Path(sparse_args.out) / 'coordinator-private/adjudication-todo.jsonl').read_text().splitlines()]
check('todo contains disagreement/pending only; no adjudication auto-fill',
      len(todo) == 3998 and all(x['status'] in ('pending', 'disagreement') and x['adjudicated_value'] is None and x['adjudication_reason'] is None for x in todo))
bad_args = args('receive', fixture / 'A-invalid.xlsx', fixture / 'B-invalid.xlsx', 'invalid-rejected')
bad = adapter.run(bad_args)
check('same wrong blind and duplicate blind/dimension rejected on both sides',
      all(any(x['code'] == 'unknown_blind_id' and x['cell'] == 'A2' for x in bad['sides'][s]['issues']) and
          any(x['code'] == 'duplicate_blind_dimension' and x['cell'] == 'A3' and x['first_cell'] == 'A2' for x in bad['sides'][s]['issues']) for s in 'AB'))
check('wrong dimension reports exact C4 on both sides', all(any(x['code'] == 'unknown_dimension' and x['cell'] == 'C4' for x in bad['sides'][s]['issues']) for s in 'AB'))
errors = bad['sides']['A']['issues']
check('formula D5 and boolean D6 rejected', all(any(x['code'] == 'invalid_value' and x['cell'] == addr for x in errors) for addr in ('D5', 'D6')))
check('0/1 reason missing reports E7', any(x['code'] == 'missing_reason' and x['cell'] == 'E7' for x in errors))
check('ambiguous text values never guessed', all(any(x['code'] == 'invalid_value' and x['cell'] == addr for x in errors) for addr in ('D8', 'D9')))
check('invalid sides cannot supply aligned metric/adjudication inputs', bad['status'] == 'content_rejected' and bad['alignment_rows'] == 0 and bad['alignment_withheld_due_to_content_errors'])
# An actual issued A/C swap, only in reader memory, checks strict original row ordering.
raw = (fixture / 'A-sparse.xlsx').read_bytes()
original_reader = adapter.read_xlsx
parsed = original_reader(raw)
cells = parsed['初判-pre-release']['cells']
cells['A2'], cells['A7'] = cells['A7'], cells['A2']
adapter.read_xlsx = lambda _: parsed
try:
    changed, _ = adapter.inspect('A', raw, data['A'])
finally:
    adapter.read_xlsx = original_reader
check('edited within-side blind sequence rejected at A2/A7', not changed['content_valid'] and all(any(x['code'] == 'template_binding_changed' and x['cell'] == addr for x in changed['issues']) for addr in ('A2', 'A7')))
try:
    adapter.run(sparse_args)
    overwritten = True
except ValueError as e:
    overwritten = False
    message = str(e)
check('first reception cannot be overwritten', not overwritten and 'never overwrite' in message)
check('original byte copies and SHA retained for sparse/invalid submissions', all(json.loads((Path(a.out) / 'seal.json').read_text())['original_byte_copies_verified'] for a in (sparse_args, bad_args)))
check('all 15 bound original inputs unchanged, including real blank templates', all(adapter.file_binding(value['path']) == before[key] for key, value in adapter.BIND['inputs'].items()))
result = {'status': 'passed', 'checks_N': len(checks), 'checks': checks,
          'constructed_workbook_N': 4, 'constructed_filled_values_N': 6, 'actual_human_submissions_N': 0,
          'source_body_semantic_reads_N': 0, 'statistics_calculated': False,
          'input_bindings_before_after_equal': True}
adapter.write_json(HERE / 'finite-checks.json', result)
print(json.dumps({'status': result['status'], 'checks_N': len(checks), 'actual_human_submissions_N': 0}))

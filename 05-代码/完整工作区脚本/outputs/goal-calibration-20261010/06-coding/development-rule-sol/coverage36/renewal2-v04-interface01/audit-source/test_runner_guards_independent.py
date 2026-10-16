"""Independent artificial source-interface controls; no actual inference."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RUNNER = HERE.parent / 'runner.py'
RESULTS = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def extracted_namespace(payload):
    tree = ast.parse(payload, filename=str(RUNNER))
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in ('digest', 'technical_diagnostics'):
            nodes.append(copy.deepcopy(node))
        elif isinstance(node, ast.FunctionDef) and node.name == 'main':
            part = copy.deepcopy(node)
            body = []
            for statement in part.body:
                if isinstance(statement, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'code' for target in statement.targets):
                    break
                body.append(statement)
            assert not any('load_frozen_coders' in ast.unparse(node) for node in body)
            part.body = body + [ast.Return(value=ast.Constant(value='pre_coder_guards_pass'))]
            nodes.append(part)
    namespace = {'Path': Path, 'argparse': argparse, 'hashlib': hashlib, 'json': json,
                 '__file__': str(RUNNER), '__doc__': 'synthetic pre-coder controls',
                 'DIMENSIONS': ('S','E','Ec','I','F'), 'EXPECTED_N': 2}
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, str(HERE / 'extracted_guard_only'), 'exec'), namespace)
    return namespace


def fixture(case):
    base = HERE / 'synthetic-runner-guards-run01' / case
    base.mkdir(parents=True, exist_ok=False)
    source, manual, resource = [base/name for name in ('source.jsonl', 'manual.md', 'resource.json')]
    snapshot, source_seal, manifest = [base/name for name in ('source.pdf', 'source-only-seal.json', 'design.json')]
    source.write_text('{"id":"SYNTHETIC-A","text":"source only"}\n{"id":"SYNTHETIC-B","text":"source only"}\n')
    manual.write_text('synthetic manual content')
    snapshot.write_bytes(b'%PDF-synthetic-integrity-control')
    source_seal.write_text('{"status":"synthetic_source_only_seal"}')
    dump(resource, {'snapshot': str(snapshot), 'snapshot_sha256': sha(snapshot)})
    assets = []
    for page in range(1, 10):
        path = base / ('asset%02d.png' % page)
        path.write_bytes(('synthetic page bytes %d' % page).encode())
        assets.append({'path': str(path), 'sha256': sha(path), 'physical_page': page, 'source_pdf_sha256': sha(snapshot)})
    design = {'n': 2, 'dimension_n': 10,
              'source': {'path': str(source), 'sha256': sha(source)},
              'manual': {'path': str(manual), 'sha256': sha(manual)},
              'resource': {'path': str(resource), 'sha256': sha(resource)},
              'source_seal': str(source_seal), 'source_page_assets': assets}
    root = base / 'output-root'
    root.mkdir()
    return base, design, manifest, source, manual, root


def guard_control(namespace, case, expected):
    base, design, manifest, source, manual, root = fixture(case)
    source_arg, manual_arg, out = source, manual, root/'new-attempt'
    source_sha = design['source']['sha256']
    if case == 'wrong_manual_path':
        manual_arg = base/'same-bytes-other-manual.md'; manual_arg.write_bytes(manual.read_bytes())
    elif case == 'wrong_source_path':
        source_arg = base/'same-bytes-other-source.jsonl'; source_arg.write_bytes(source.read_bytes())
    elif case == 'wrong_design_n':
        design['n'] = 1
    elif case == 'changed_manual':
        manual.write_text('changed')
    elif case == 'changed_source':
        source.write_text('changed')
    elif case == 'changed_resource':
        Path(design['resource']['path']).write_text('{"changed":true}')
    elif case == 'wrong_scope_argument_sha':
        source_sha = '0'*64
    elif case == 'changed_snapshot':
        (base/'source.pdf').write_bytes(b'changed')
    elif case == 'changed_page_asset':
        Path(design['source_page_assets'][0]['path']).write_bytes(b'changed')
    elif case == 'duplicate_material_path':
        design['source_page_assets'][1] = dict(design['source_page_assets'][0])
    elif case == 'existing_output':
        out.mkdir()
    elif case == 'output_equal_root':
        out = root
    dump(manifest, design)
    namespace['AUTHORIZED_DESIGN_SHA256'] = '0'*64 if case == 'wrong_design_sha' else sha(manifest)
    namespace['AUTHORIZED_SOURCE_BY_N'] = {2: design['source']['sha256']}
    old_argv = sys.argv
    sys.argv = ['guard-only', '--source', str(source_arg), '--manual', str(manual_arg), '--manifest', str(manifest), '--source-sha256', source_sha, '--expected-n', '2', '--approved-output-root', str(root), '--out', str(out)]
    try:
        try:
            actual = namespace['main']()
            error = None
        except (ValueError, FileNotFoundError) as exc:
            actual, error = 'reject', str(exc)
        RESULTS.append({'name': case, 'passed': actual == expected, 'expected': expected, 'actual': actual, 'error': error,
                        'coder_loaded': False, 'attempt_output_created': out.exists() and case not in ('existing_output', 'output_equal_root')})
    finally:
        sys.argv = old_argv


def records():
    dims = ('S','E','Ec','I','F')
    rows = [{'id':'SYNTHETIC-A', 'text':'artificial raw A', 'contexts':[]},
            {'id':'SYNTHETIC-B', 'text':'artificial raw B', 'contexts':[]}]
    predictions = [{'id': row['id'], 'decisions': {dim:{'value': 0} for dim in dims}, 'implementation_errors':[]} for row in rows]
    return rows, predictions


def ledger_control(namespace, case):
    rows, predictions = records()
    errors = []
    if case == 'global_failure_all10':
        errors = [{'type':'SyntheticGlobalFailure', 'message':'artificial failure'}]
        for prediction in predictions:
            prediction['decisions'] = None
    elif case == 'record_failure5_rule_null_retained':
        predictions[0]['implementation_errors'] = [{'id':rows[0]['id'], 'type':'SyntheticRecordFailure'}]
        predictions[0]['decisions'] = None
        predictions[1]['decisions']['S']['value'] = None
    elif case == 'one_missing_decision':
        del predictions[0]['decisions']['S']
    elif case == 'duplicate_source_ids':
        rows[1]['id'] = rows[0]['id']
    elif case == 'prediction_id_order_mismatch':
        predictions.reverse()
    elif case == 'pre_adapter_full_loader_failure_gap':
        rows, predictions = [], []
        errors = [{'type':'SyntheticSchemaFailure'}]
    actual = namespace['technical_diagnostics'](rows, predictions, errors)
    if case == 'global_failure_all10':
        passed = len(actual) == 10 and all(slot['technical_failure'] and slot['retained_rule_decision'] is None and not slot['rules_null'] and not slot['comparison_eligible'] for slot in actual)
    elif case == 'record_failure5_rule_null_retained':
        passed = len(actual) == 10 and sum(slot['technical_failure'] for slot in actual) == 5 and sum(slot['rules_null'] for slot in actual) == 1
    elif case == 'one_missing_decision':
        passed = len(actual) == 10 and sum(slot['technical_failure'] for slot in actual) == 1
    else:
        passed = actual is None
    RESULTS.append({'name': case, 'passed': passed, 'actual_slot_n': len(actual) if actual is not None else None,
                    'actual_technical_failure_n': sum(slot['technical_failure'] for slot in actual) if actual is not None else None,
                    'actual_rule_null_n': sum(slot['rules_null'] for slot in actual) if actual is not None else None,
                    'known_requirement_gap': case == 'pre_adapter_full_loader_failure_gap',
                    'actual_materials_used': False})


def main():
    predeclared_path = HERE/'runner-controls-predeclared-run01.json'
    controls = json.loads(predeclared_path.read_text())['cases']
    payload = RUNNER.read_bytes()
    namespace = extracted_namespace(payload)
    for item in controls[:14]:
        guard_control(namespace, item['name'], item['expected'])
    for item in controls[14:]:
        namespace['EXPECTED_N'] = 2
        ledger_control(namespace, item['name'])
    report = {'status':'independent_synthetic_only_runner_guards_and_ledger', 'runner_path':str(RUNNER), 'runner_sha256':hashlib.sha256(payload).hexdigest(),
              'test_script_sha256': sha(__file__), 'predeclared_sha256': sha(predeclared_path),
              'test_n':len(RESULTS), 'pass_n':sum(item['passed'] for item in RESULTS), 'fail_n':sum(not item['passed'] for item in RESULTS),
              'known_requirement_gap_n':sum(item.get('known_requirement_gap', False) for item in RESULTS),
              'cases':RESULTS, 'actual_source_main_called':False, 'semantic_coder_imported':False,
              'interpretation':'Control outcomes include the known incomplete-loader ledger gap, not a claim that the initial runner retains 10 slots for every failure.'}
    with (HERE/'runner-controls-result-run01.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({k:report[k] for k in ('runner_sha256','test_n','pass_n','fail_n','known_requirement_gap_n')}))


if __name__ == '__main__':
    main()

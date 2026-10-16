"""Pure helper controls. Never calls runner main or reads actual source."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def main():
    run_tag = sys.argv[1] if len(sys.argv) > 1 else 'run01'
    runner = HERE.parent/'runner.py'
    payload = runner.read_bytes()
    tree = ast.parse(payload)
    functions = [copy.deepcopy(node) for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('digest','raw_failure_diagnostics')]
    namespace = {'Path': Path, 'json':json, 'hashlib':hashlib, 'EXPECTED_N':2, 'DIMENSIONS':('S','E','Ec','I','F')}
    exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])), 'isolated_fallback_helper', 'exec'), namespace)
    predeclared = HERE/'fallback-controls-predeclared-run01.json'
    cases = json.loads(predeclared.read_text())['cases']
    directory = HERE/('synthetic-fallback-'+run_tag)
    directory.mkdir(exist_ok=False)
    results = []
    for item in cases:
        name = item['name']
        rows = [{'id':'SYNTHETIC-A','text':'artificial source A','contexts':[{'raw_structure':True}],'source_ref':{'sha256':'synthetic'},'source_attachments':[{'original_raw':'retained'}],'source_references':[{'source_field':'literal-original-value'}]},
                {'id':'SYNTHETIC-B','text':'artificial source B','contexts':[],'unknown_raw_field':{'kept':'technical diagnostic only'}}]
        original = copy.deepcopy(rows)
        path = directory/(name+'.jsonl')
        path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        expected_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        namespace['AUTHORIZED_SOURCE_BY_N'] = {2:expected_sha}
        if name == 'duplicate_ids_rejected':
            rows[1]['id'] = rows[0]['id']
        elif name == 'wrong_n_rejected':
            rows.pop()
        elif name == 'nonstring_id_rejected':
            rows[1]['id'] = 9
        elif name == 'nondict_row_rejected':
            rows[1] = 'not a source dictionary'
        elif name == 'changed_after_freeze_rejected':
            rows[0]['id'] = 'ALTERED-AFTER-SYNTHETIC-FREEZE'
        path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        # Only the change-after-freeze case keeps the older frozen digest.
        if name != 'changed_after_freeze_rejected':
            namespace['AUTHORIZED_SOURCE_BY_N'][2] = hashlib.sha256(path.read_bytes()).hexdigest()
        errors = [{'type':'SyntheticLoaderFailure','message':'artificial schema rejection'}]
        actual, error = None, None
        try:
            actual = namespace['raw_failure_diagnostics'](path, errors)
        except Exception as exc:
            error = str(exc)
        if name == 'full10_raw_fields_retained':
            passed = error is None and len(actual) == 10 and all(slot['source_record'] == original[index//5] and slot['technical_failure'] and slot['rule_not_executed'] and not slot['rules_null'] and slot['rule_value'] is None and slot['retained_rule_decision'] is None and not slot['comparison_eligible'] for index,slot in enumerate(actual))
        else:
            passed = error is not None
        results.append({'name':name,'passed':passed,'actual_slot_n':len(actual) if actual is not None else None,'error':error,'expected':item['expected'],'changed_source_id_reconstructed':bool(actual and actual[0]['id'].startswith('ALTERED'))})
    report = {'status':'independent_artificial_only_raw_failure_helper_controls','runner_sha256':hashlib.sha256(payload).hexdigest(),'predeclared_sha256':hashlib.sha256(predeclared.read_bytes()).hexdigest(),'test_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'test_n':len(results),'pass_n':sum(row['passed'] for row in results),'fail_n':sum(not row['passed'] for row in results),'cases':results,'actual_source_used':False,'semantic_coders_loaded':False}
    with (HERE/('fallback-controls-result-'+run_tag+'.json')).open('x',encoding='utf-8') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({key:report[key] for key in ('runner_sha256','test_n','pass_n','fail_n')}))


if __name__ == '__main__':
    main()

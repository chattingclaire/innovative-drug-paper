"""Exactly four predeclared synthetic predicate/nominal contrasts."""
import hashlib
import json
from pathlib import Path
import sys
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from evidence import validate_decisions
from relations import RelationView
from dimensions import judge, _payment_route_only


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    tag = sys.argv[1]
    controls_path = HERE / 'payment-predicate-controls-before-tests.json'
    declaration = json.loads(controls_path.read_text(encoding='utf-8'))
    assert len(declaration['cases']) == 4
    results = []
    for case in declaration['cases']:
        unit = {'text': case['source'], 'pages': [], 'contexts': [],
                'attachments': [], 'source_image_attachments': []}
        try:
            view = RelationView(unit)
            decisions = judge(view)
            validate_decisions(unit, decisions)
            actual = decisions['Ec']['value']
            route = _payment_route_only(case['source'])
            result = {'name': case['name'], 'source': case['source'],
                      'expected_Ec': case['expected_Ec'], 'actual_Ec': actual,
                      'expected_payment_route_only': case['expected_payment_route_only'],
                      'actual_payment_route_only': route,
                      'passed': actual == case['expected_Ec'] and route == case['expected_payment_route_only'],
                      'ec_decision': decisions['Ec'], 'technical_failure': None}
        except Exception as error:
            result = {'name': case['name'], 'source': case['source'],
                      'expected_Ec': case['expected_Ec'], 'actual_Ec': None, 'passed': False,
                      'technical_failure': {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}}
        results.append(result)
        print(json.dumps({'name':result['name'], 'expected_Ec':result['expected_Ec'],
                          'actual_Ec':result['actual_Ec'], 'route_only':result.get('actual_payment_route_only'),
                          'passed':result['passed']},ensure_ascii=False))
    report = {'status': 'four_predeclared_synthetic_controls_only', 'tag': tag,
              'dimensions_sha256': sha(HERE/'dimensions.py'), 'tests_sha256':sha(__file__),
              'declaration_sha256':sha(controls_path), 'test_n':len(results),
              'pass_n':sum(result['passed'] for result in results),
              'fail_n':sum(not result['passed'] for result in results),
              'technical_failure_n':sum(result['technical_failure'] is not None for result in results),
              'cases':results, 'actual_fixture_executed':False,
              'reference_AB_native_v12_read':False}
    with (HERE/('payment-predicate-tests-'+tag+'.json')).open('x',encoding='utf-8') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write('\n')
    print(json.dumps({key:report[key] for key in ('dimensions_sha256','test_n','pass_n','fail_n','technical_failure_n')}))
    return 0 if report['fail_n']==0 else 1


if __name__=='__main__':
    raise SystemExit(main())

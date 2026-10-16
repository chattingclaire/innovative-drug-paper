"""Run existing boundary suites against one unchanged classifier snapshot."""
from pathlib import Path
import concurrent.futures, hashlib, json, subprocess, sys

P = Path(__file__).resolve().parent
FILES = ['dimensions_tests.py','relations_tests.py','review_guard_tests.py','rights_review_recheck.py',
         'round2_dimensions_tests.py','round2_nested_standard_tests.py','round2_relations_tests.py',
         'round3_local_review_tests.py','round3_local_tests.py','round3_rights_tests.py',
         'round4_relations_tests.py','round4_safety_review_tests.py','round4_safety_tests.py',
         'round5_local_support_tests.py','round5_pilot_assessment_tests.py','round5_relations_tests.py',
         'round5_statutory_review_probe.py','round5_local_support_independent_review.py',
         'round5_pilot_assessment_review.py','round6_dimensions_tests.py','round6_relations_tests.py',
         'round6_independent_review_probe.py','round6_dimensions_independent_review.py']

def hashes():
    return {f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (P/'code').glob('*.py')}

def run(filename):
    r = subprocess.run([sys.executable, str(P/filename)], capture_output=True, text=True)
    (P/(filename+'.log')).write_text(r.stdout+r.stderr)
    return {'test':filename, 'exit_code':r.returncode,
            'output_tail':(r.stdout+r.stderr)[-1500:] if r.returncode else 'Completed; full output saved in corresponding log'}

before = hashes()
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(run, FILES))
assert before == hashes(), 'Code changed during checks'
checks = []
for c in json.loads((P/'round5-statutory-review-probes.json').read_text()):
    n = c['name']
    if n.startswith('original_'):
        ok = c['labels']['I'] == c['labels']['F'] == 1 and c['relation_count'] == 1
    elif n == 'both_technical_services_denied':
        ok = (c['labels']['I'] == c['labels']['F'] == 1 and c['relation_count'] == 1
              and all(d.get('direction') == 'restricted' and d.get('positive_delivery') is False for d in c['relation_direction_fields'])
              and all('限制' in c['decision_reasons'][d] for d in ['I','F']))
    else:
        ok = c['relation_count'] == 0
    checks.append({'name':n,'passed':ok})
reviews = []
for name in ['round5-local-support-independent-review.json','round5-pilot-assessment-review.json']:
    data = json.loads((P/name).read_text())
    reviews.append({'file':name,'passed':data['passed'],'total':data['total'],
                    'all_passed':data['passed'] == data['total'],
                    'code_matches':all(before[k] == v for k,v in data['code_sha256'].items())})
# Re-run saved independent cases against this exact final snapshot.
reference = json.loads((P/'round6-relations-review-closure.json').read_text())['tests']
actual = json.loads((P/'round6-independent-review-probes.json').read_text())
expected = {x['name']:x for x in reference}
relations_ok = len(actual) == len(expected) and all(
    x['name'] in expected and x['labels'] == expected[x['name']]['labels']
    and x['relations'] == expected[x['name']]['relations'] for x in actual)
reviews.append({'file':'round6-independent-review-probes.json',
                'all_passed':relations_ok,'code_matches':True,'total':len(actual),
                'verification':'Saved independently accepted labels and relation types; execution within unchanged code snapshot'})
data = json.loads((P/'round6-dimensions-independent-review.json').read_text())
reviews.append({'file':'round6-dimensions-independent-review.json',
                'passed':data['passed'],'total':data['total'],
                'all_passed':data['passed']==data['total'] and all(x['passed'] for x in data['cases']),
                'code_matches':data['dimensions_sha256']==before['dimensions.py']})
report = {'code_sha256':before,'code_unchanged':True,'suites':results,
          'statutory_final_code_checks':checks,
          'independent_reviews':reviews,
          'all_passed':all(x['exit_code'] == 0 for x in results) and all(x['passed'] for x in checks)
                       and all(x['all_passed'] and x['code_matches'] for x in reviews)}
(P/'全部回归检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'suites':len(results),'all_passed':report['all_passed'],
                  'failures':[x for x in results if x['exit_code']]},ensure_ascii=False))
if not report['all_passed']:
    raise SystemExit(1)

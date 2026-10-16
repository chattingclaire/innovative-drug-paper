"""Frozen constructed controls and disclosed developer cases; not validation."""
import copy
import hashlib
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
P = R.parents[2]
sys.path.insert(0, str(R/'runtime'))
from rules_repair_v37 import revise
from rule_support import rebuild
from policy_coding_v27 import code_unit

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(t): return hashlib.sha256(t.encode()).hexdigest()
def fresh(): return {'judgement_status': 'determined', 'evidence': [], 'suppressions': []}

freeze = json.loads((R/'preimplementation_controls_v37_freeze.json').read_text())
assert sha(freeze['path']) == freeze['sha256']
controls = json.loads(Path(freeze['path']).read_text())['rows']
fixtures = R/'constructed_source_fixtures'
fixtures.mkdir(exist_ok=True)
scope_text = ('药物临床试验期间，用于防治严重疾病的创新药或者改良型新药，'
              '申请人可以申请适用突破性治疗药物程序。')

def constructed_record(row):
    text = row['constructed_text']
    record = {'unit_text': text}
    if row['innovation_scope_fixture']:
        source = fixtures/(row['name']+'.txt')
        candidate = fixtures/(row['name']+'.json')
        source.write_text(scope_text+'\n'+text+'\n')
        candidate.write_text(json.dumps({'paragraphs': [{'id': 'scope', 'text': scope_text, 'pages': []}],
                                        'unit_candidates': [{'id': 'unit', 'text': text}]}, ensure_ascii=False))
        record.update(unit_source=str(source.resolve()), unit_source_sha256=sha(source),
                      candidate_file=str(candidate.resolve()), candidate_sha256=sha(candidate), unit_id='unit')
        record['verified_innovation_scope_v27'] = {
            'text': scope_text, 'text_sha256': digest(scope_text),
            'source_sha256': sha(source), 'original_unit_sha256': digest(text),
            'component': '突破性治疗程序', 'verified': True,
            'locator': {'source_lines': [1], 'paragraph_id': 'scope'},
            'component_binding': {'unit_id': 'unit', 'candidate_sha256': sha(candidate)}}
    return record

def seeded(text, seeds):
    out = fresh()
    for dim, rule, quote, subtype in seeds:
        a = text.index(quote)
        out['evidence'].append({'dimension': dim, 'rule': rule, 'text': quote,
                                'matching_text': quote, 'start': a, 'end': a+len(quote), 'subtype': subtype})
    return out

def literal_checks(text, result):
    for e in result['evidence'] + result['suppressions']:
        if 'start' in e:
            assert text[e['start']:e['end']] == e['text']

results = []
for row in controls:
    record = constructed_record(row)
    actual = rebuild(revise(record, seeded(record['unit_text'], row['seed_evidence'])))
    dimensions = sorted(d for d, value in actual['labels'].items() if value)
    assert dimensions == sorted(row['expected_new_dimensions']), (row['name'], dimensions, row, actual)
    literal_checks(record['unit_text'], actual)
    changed_metadata = copy.deepcopy(record)
    changed_metadata.update(review_id='arbitrary', original_id='arbitrary', department='arbitrary',
                            original_file_stem='arbitrary', reference_labels={'I': 1})
    second = rebuild(revise(changed_metadata, seeded(record['unit_text'], row['seed_evidence'])))
    assert actual['labels'] == second['labels'] and actual['evidence'] == second['evidence']
    results.append({'name': row['name'], 'constructed_text': row['constructed_text'],
                    'actual': actual, 'expected_new_dimensions': row['expected_new_dimensions'], 'pass': True,
                    'metadata_invariance': True})

# Authentication checks mutate source/unit/candidate/text/locator bindings,
# not any answer. A bare or forged innovation scope cannot enable guidance.
guide = next(row for row in controls if row['name'] == 'guide-real-personnel-and-advice')
valid = constructed_record(guide)
checks = {}
no_scope = copy.deepcopy(valid)
no_scope.pop('verified_innovation_scope_v27')
checks['no_scope_no_guidance'] = not rebuild(revise(no_scope, fresh()))['labels']['I']
for name, mutation in [
    ('scope_text_sha', lambda r: r['verified_innovation_scope_v27'].update(text_sha256='0'*64)),
    ('scope_source_sha', lambda r: r['verified_innovation_scope_v27'].update(source_sha256='0'*64)),
    ('scope_unit_sha', lambda r: r['verified_innovation_scope_v27'].update(original_unit_sha256='0'*64)),
    ('scope_candidate_sha', lambda r: r['verified_innovation_scope_v27']['component_binding'].update(candidate_sha256='0'*64)),
    ('scope_false_locator', lambda r: r['verified_innovation_scope_v27']['locator'].update(paragraph_id='absent')),
    ('actual_candidate_sha', lambda r: r.update(candidate_sha256='0'*64)),
]:
    altered = copy.deepcopy(valid)
    mutation(altered)
    rejected = False
    try:
        revise(altered, fresh())
    except (AssertionError, ValueError):
        rejected = True
    checks[name+'_rejected'] = rejected
assert all(checks.values()), checks

# The six supplied cases are already disclosed development cases. 01353 was
# in a reserved family before the prior ten-case audit exposed it; this test
# reads the same disclosed audit only, never another member of that family.
audit_path = P/'outputs/final-three-department-20261008-human-validation-template/method-difference-audit/当前两方法具体差异审计.json'
audit = json.loads(audit_path.read_text())
expected = {'RECODE25-00741': ('Ec', 1), 'RECODE25-01353': ('S', 1),
            'RECODE25-03574': ('I', 1), 'RECODE25-01388': ('I', 1),
            'RECODE25-01378': ('I', 0), 'RECODE25-00035': ('I', 1)}
actual_record = None
source_input = P/'outputs/coding-revision-20261007-r3/rule_inputs_shared_v14.jsonl'
with source_input.open() as stream:
    for line in stream:
        if 'RECODE25-00035' in line:
            row = json.loads(line)
            if row['id'] == 'RECODE25-00035':
                actual_record = row['input']
                break
assert actual_record is not None
targets = []
for case in audit['cases']:
    if case['id'] not in expected:
        continue
    record = actual_record if case['id'] == 'RECODE25-00035' else {'unit_text': case['text']}
    result = code_unit(record)
    dim, value = expected[case['id']]
    assert result['labels'][dim] == value, (case['id'], result)
    assert all(result['labels'][d] == case['actual_rules_row']['prediction']['labels'][d]
               for d in result['labels'] if d != dim), (case['id'], result)
    literal_checks(record['unit_text'], result)
    targets.append({'id': case['id'], 'dimension': dim,
                    'baseline_labels': case['actual_rules_row']['prediction']['labels'],
                    'candidate': result, 'pass': True, 'scope': 'already exposed developer case'})
assert len(targets) == 6

report = {'all_checks_pass': True, 'constructed_n': len(results), 'source_binding_n': len(checks),
          'developer_targets_n': len(targets), 'not_independent_validation': True,
          'preimplementation_controls_sha256': freeze['sha256'], 'script_sha256': sha(__file__),
          'reserved_member_manual_review_exclusion': 267,
          'known_previous_audit_exposure': ['RECODE25-01353', 'RECODE25-01361'],
          'expectation_interpretation': 'expected_new_dimensions checks only evidence emitted by this deliberately narrow repair module (plus explicitly seeded evidence). Empty sets are not whole-unit gold labels or new manual exclusions. In particular, staffing alone or scientific advice without the exact study-basis/next-plan grammar may still substantively satisfy I1; that is a coverage limit of this new branch.',
          'scientific_guidance_grammar_is_not_manual_necessary_condition': True,
          'constructed_rows': results, 'source_binding_checks': checks, 'developer_targets': targets}
(R/'repair_controls_results_v37.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k: report[k] for k in ('all_checks_pass', 'constructed_n', 'source_binding_n', 'developer_targets_n')}, ensure_ascii=False))

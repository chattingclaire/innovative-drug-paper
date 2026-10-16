"""Predeclared constructed cases through real, unseeded code_unit only."""
import json
import hashlib
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R/'runtime'))
from policy_coding_v27 import code_unit

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(t): return hashlib.sha256(t.encode()).hexdigest()
freeze = json.loads((R/'preimplementation_end_to_end_controls_v37_2_freeze.json').read_text())
assert sha(freeze['path']) == freeze['sha256']
cases = json.loads(Path(freeze['path']).read_text())['rows']
fixtures = R/'complete_object_constructed_source_fixtures'
fixtures.mkdir(exist_ok=True)
scope_text = ('药物临床试验期间，用于防治严重疾病的创新药或者改良型新药，'
              '申请人可以申请适用突破性治疗药物程序。')
rows = []
for case in cases:
    text = case['constructed_text']
    record = {'unit_text': text}
    if case['scope_fixture']:
        source = fixtures/(case['name']+'.txt')
        candidate = fixtures/(case['name']+'.json')
        source.write_text(scope_text+'\n'+text+'\n')
        candidate.write_text(json.dumps({'paragraphs': [{'id': 'scope', 'text': scope_text, 'pages': []}],
                                        'unit_candidates': [{'id': 'unit', 'text': text}]}, ensure_ascii=False))
        record.update(unit_source=str(source.resolve()), unit_source_sha256=sha(source),
                      candidate_file=str(candidate.resolve()), candidate_sha256=sha(candidate), unit_id='unit')
        record['verified_innovation_scope_v27'] = {
            'text': scope_text, 'text_sha256': digest(scope_text), 'source_sha256': sha(source),
            'original_unit_sha256': digest(text), 'component': '突破性治疗程序', 'verified': True,
            'locator': {'source_lines': [1], 'paragraph_id': 'scope'},
            'component_binding': {'unit_id': 'unit', 'candidate_sha256': sha(candidate)}}
    result = code_unit(record)
    # For an incomplete by-price phrase, check only that the new price
    # branch abstains; do not declare a whole-unit true Ec=0.
    branch_only = case.get('assertion_scope', '').startswith('new price branch')
    if branch_only:
        assert not any(e['rule'] == 'V37_Ec_current_drug_procurement_price_selection' for e in result['evidence'])
    else:
        assert result['labels'][case['expected_dimension']] == case['expected_value'], (case, result)
    independent_right_expected = case['name'] in (
        'independent-publication_explicit_right_scope', 'independent-publication_independent_right',
        'right-grant-with-publication', 'right-scope-expansion-inverse')
    if independent_right_expected:
        assert any(e['rule'] == 'V371_I_current_explicit_drug_data_right' for e in result['evidence']), (case, result)
    for e in result['evidence']+result['suppressions']:
        if 'start' in e:
            assert text[e['start']:e['end']] == e['text']
    rows.append({**case, 'assertion_scope': 'new branch abstention only; no whole-unit gold0' if branch_only else 'stated constructed target dimension only',
                 'full_result': result, 'independent_right_evidence_required': independent_right_expected,
                 'seed_evidence_used': False, 'pass': True})
report = {'all_checks_pass': True, 'n': len(rows), 'full_unseeded_pipeline': True,
          'constructed_only_not_independent_validation': True, 'new_human_results_read': False,
          'no_new_human_submission_paths_labels_or_scores_loaded': True,
          'frozen_controls_sha256': freeze['sha256'], 'script_sha256': sha(__file__),
          'branch_only_empty_evidence_not_whole_unit_gold0': True, 'rows': rows}
(R/'end_to_end_controls_results_v37_2.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k: report[k] for k in ('all_checks_pass', 'n', 'full_unseeded_pipeline', 'new_human_results_read')}, ensure_ascii=False))

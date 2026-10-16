"""Reproduce current rule outputs and isolate implementation defects.

Diagnostic sentences below are constructed probes, never policy quotations or
independent validation data. This script does not modify any source or labels.
"""
import datetime
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'autocode-v25-20260927'
sys.path.insert(0, str(BASE))
import policy_coding_v25 as engine

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

PROBES = [
    ('I', '支持创新药研发。', 1, 'explicit_drug_innovation_support'),
    ('I', '支持创新药的研发。', 1, 'same_meaning_function_word'),
    ('I', '对创新药研发予以支持。', 1, 'same_meaning_word_order'),
    ('F', '药品用于尚无有效治疗手段的患者。', 1, 'explicit_unmet_treatment'),
    ('F', '药品用于缺乏有效标准治疗手段的患者。', 1, 'modifier_between_anchor_words'),
    ('I', '药品申报工作采用创新性的信息管理系统。', 0, 'innovation_of_system_not_drug'),
    ('F', '药品申报管理中的数据可及性需要提升。', 0, 'data_access_not_treatment_access'),
    ('I', '支持创新药的研发，并建设信息管理系统。', 1, 'mixed_unit_preserve_drug_claim'),
    ('F', '药品申报管理中的数据可及性需要提升，同时改善患者药品可及性。', 1, 'mixed_unit_preserve_patient_claim'),
    ('E', '该药物的疗效尚不确定。', 1, 'negative_result_still_dimension_content'),
]

def main():
    rows = [json.loads(s) for s in (BASE/'current_rule_inputs.jsonl').read_text().splitlines()]
    saved = {r['id']: r['candidate'] for r in map(json.loads, (BASE/'rule_runs/v25-candidate-3/all_predictions.jsonl').read_text().splitlines())}
    assert len(rows) == len(saved) == 4924
    failures = []
    evidence_n = suppression_n = pending_n = 0
    for row in rows:
        record = row['input']
        result = engine.code_unit(record)
        old = saved[row['id']]
        if result != old:
            failures.append({'id':row['id'], 'issue':'rerun_record_differs',
                             'fields':[k for k in set(result)|set(old) if result.get(k)!=old.get(k)]})
        text = record['unit_text']
        for name in ('evidence', 'suppressions'):
            for span in result.get(name, []):
                if not (0 <= span['start'] < span['end'] <= len(text) and text[span['start']:span['end']] == span['text']):
                    failures.append({'id':row['id'],'issue':'span_not_literal_source','kind':name,'span':span})
        evidence_n += len(result.get('evidence', []))
        suppression_n += len(result.get('suppressions', []))
        if result['judgement_status'] == 'undetermined':
            pending_n += 1
            assert all(v is None for v in result['labels'].values())
        else:
            rebuilt = {d:int(any(e['dimension']==d for e in result['evidence'])) for d in engine.DIMENSIONS}
            if rebuilt != result['labels']:
                failures.append({'id':row['id'],'issue':'label_evidence_mismatch'})
    probes = []
    for dim, text, expected, mechanism in PROBES:
        result = engine.code_unit({'unit_text':text, 'input_assessment':{'status':'sufficient', 'basis':'Root-created diagnostic probe, not a policy source.'}})
        probes.append({'dimension':dim,'constructed_text':text,'expected_under_manual':expected,
                       'observed':result['labels'][dim], 'matches_expectation':result['labels'][dim]==expected,
                       'mechanism':mechanism, 'evidence':[e for e in result['evidence'] if e['dimension']==dim]})
    report = {
        'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope':'Mechanical reproduction plus constructed diagnostic probes; not accuracy validation.',
        'input_bindings':{str(p):sha(p) for p in [BASE/'current_rule_inputs.jsonl', BASE/'policy_coding_v25.py', BASE/'baseline_candidate17.py', BASE/'rule_runs/v25-candidate-3/all_predictions.jsonl', BASE/'protocol-v1.3.md']},
        'corpus_check':{'n':len(rows), 'pending_n':pending_n, 'evidence_spans_checked':evidence_n,
                        'suppression_spans_checked':suppression_n,'failures':failures},
        'constructed_probes':probes,
        'interpretation':[
            'Passing source-span checks means quoted matches can be traced; it does not establish semantic correctness.',
            'Probe failures identify reproducible gaps in wording coverage and object binding; their frequency is not a corpus error rate.',
            'Negation of a drug result is not a reason to remove a dimension; the construct measures discussion, not favorable results.'
        ]}
    (HERE/'current-implementation-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'corpus_check':report['corpus_check'], 'probes':[{k:p[k] for k in ('dimension','constructed_text','expected_under_manual','observed')} for p in probes]},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()

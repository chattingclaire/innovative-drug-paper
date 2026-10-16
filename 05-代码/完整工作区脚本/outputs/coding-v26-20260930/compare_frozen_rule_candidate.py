"""One descriptive run of a frozen candidate on already-exposed material.

Does not alter reference labels, repair contexts, or claim new validation.
"""
import datetime
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'autocode-v25-20260927'
CANDIDATE = HERE / 'rules_candidate' / 'policy_coding_v26.py'
OUT = HERE / 'rule_comparison'
sys.path.insert(0, str(BASE))
from analyze_current_reruns import load_sealed_predictions, load_reference_units, normalize_rule_record
from comparison_statistics import agreement, DIMS

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')

def main():
    assert CANDIDATE.exists(), 'Candidate is not ready'
    OUT.mkdir(exist_ok=False)
    paths = [*sorted(CANDIDATE.parent.glob('*.py')), BASE/'policy_coding_v25.py',
             BASE/'baseline_candidate17.py', BASE/'protocol-v1.3.md',
             BASE/'current_rule_inputs.jsonl', Path(__file__).resolve()]
    freeze = {'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status':'frozen_before_single_comparison',
              'bindings':{str(p):sha(p) for p in paths}}
    dump(OUT/'candidate_freeze.json', freeze)
    spec = importlib.util.spec_from_file_location('candidate_v26_frozen', CANDIDATE)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    rules, llm, inputs, seal = load_sealed_predictions()
    rows = [json.loads(s) for s in (BASE/'current_rule_inputs.jsonl').read_text().splitlines()]
    new = {}
    changed = []
    with (OUT/'all_predictions.jsonl').open('w') as f:
        for row in rows:
            result = engine.code_unit(row['input'])
            old = rules[row['id']]['candidate']
            normalized = normalize_rule_record(result)
            for d in ('S','E','Ec'):
                assert normalized['labels'][d] == old['labels'][d], (row['id'], d, 'Out-of-scope change')
            assert (result['judgement_status']=='undetermined') == (old['judgement_status']=='undetermined')
            for e in result['evidence']:
                assert row['input']['unit_text'][e['start']:e['end']] == e['text'], (row['id'], 'Nonliteral evidence')
            new[row['id']] = normalized
            f.write(json.dumps({'id':row['id'], 'original_id':row['original_id'], 'prediction':result}, ensure_ascii=False)+'\n')
            dims = [d for d in DIMS if normalized['labels'][d] != old['labels'][d]]
            if dims:
                changed.append({'id':row['id'], 'dimensions':dims, 'text':row['input']['unit_text'],
                                'old_labels':old['labels'],'new_labels':normalized['labels'],
                                'new_evidence':result['evidence'], 'suppressions':result['suppressions']})
    assert len(new)==4924
    methods = ('rules_v25','rules_v26','llm_gpt56_sol')
    reports = {}
    reference_bindings = {}
    for scope in ('current1268','H427'):
        units, bindings = load_reference_units(scope, rules, llm, inputs)
        reference_bindings.update(bindings)
        reports[scope] = {'n':len(units), 'references':{}}
        for u in units:
            u['predictions']['rules_v26'] = new[u['id']]
        for ref in ('A','C'):
            reports[scope]['references'][ref] = {}
            for dim in DIMS:
                common = [u for u in units if u['references'][ref]['labels'][dim] in (0,1)
                          and all(u['predictions'][m]['labels'][dim] in (0,1) for m in methods)]
                comparisons = {}
                for method in methods:
                    comparisons[method] = {}
                    for title, selected, weighted in [('all_unweighted',units,False), ('common_unweighted',common,False), ('common_weighted',common,True)]:
                        pairs = [(u['predictions'][method]['labels'][dim],u['references'][ref]['labels'][dim], u['weight'] if weighted else 1) for u in selected]
                        comparisons[method][title] = agreement(pairs)
                reports[scope]['references'][ref][dim] = {'common_n':len(common),'methods':comparisons}
    for path, digest in freeze['bindings'].items():
        assert sha(Path(path)) == digest, 'Candidate/input changed during comparison'
    report = {'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status':'descriptive_development_comparison_not_independent_validation',
              'reference_identity':'Preserved AI A/C first submissions, not human gold standard',
              'scope_notes':{'current1268':'Already exposed development material; historical weights descriptive only',
                             'H427':'Previously sealed remaining-frame census, now exposed development material; not representative of full corpus'},
              'unchanged':['manual definitions','input text and context','reference labels','LLM labels','rule S/E/Ec','pending inputs'],
              'changed_units':len(changed), 'changed_decisions_by_dimension':dict(Counter(d for r in changed for d in r['dimensions'])),
              'reference_bindings':reference_bindings,
              'output_sha256':sha(OUT/'all_predictions.jsonl'), 'results':reports}
    dump(OUT/'metrics.json', report)
    dump(OUT/'changed_records.json', changed)
    brief = []
    for ref in ('A','C'):
        for dim in ('I','F'):
            item = reports['H427']['references'][ref][dim]
            for method in methods:
                s = item['methods'][method]['common_unweighted']
                brief.append({'reference':ref,'dimension':dim,'method':method,'n':item['common_n'],
                              'kappa':s['binary_agreement']['kappa'],**s['conditional_scores'],
                              'confusion':s['confusion_on_joint_determinate']})
    print(json.dumps({'changed_units':len(changed),'changed_dimensions':report['changed_decisions_by_dimension'],'H427':brief},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()

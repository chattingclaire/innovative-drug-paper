"""Audit the requested four-column table from saved, hash-bound predictions.

No prediction, reference, or manuscript is changed. The latest rule candidate
is compared with the last actually executed LLM, not the unexecuted new prompt.
"""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import datetime
import hashlib
import json
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'autocode-v25-20260927'
sys.path.insert(0,str(BASE))
from analyze_current_reruns import load_sealed_predictions, load_reference_units, normalize_rule_record
from comparison_statistics import agreement, DIMS

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def checked(pairs):
    counts=Counter(pairs)
    n=len(pairs)
    margins=sum(sum(counts[x,y] for y in (0,1))*sum(counts[y,x] for y in (0,1)) for x in (0,1))
    denominator=n*n-margins
    kappa=float(Fraction(n*(counts[0,0]+counts[1,1])-margins,denominator)) if denominator else None
    full=agreement([(x,y,1) for x,y in pairs])
    assert kappa is None or abs(kappa-full['binary_agreement']['kappa'])<1e-12
    return {'n':n,'kappa':kappa,'confusion':full['confusion_on_joint_determinate'],
            'precision_recall_f1':full['conditional_scores']}

def main():
    old_rules,llm,inputs,_=load_sealed_predictions()
    prediction_path=HERE/'title_scope_verification/all_predictions.jsonl'
    verification=json.loads((HERE/'title_scope_verification/verification.json').read_text())
    assert sha(prediction_path)==verification['output_sha256']
    rows=[json.loads(s) for s in prediction_path.read_text().splitlines()]
    rules={r['id']:normalize_rule_record(r['prediction']) for r in rows}
    assert len(rules)==len(rows)==4924 and set(rules)==set(llm)
    prior=json.loads((HERE/'rule_comparison/metrics.json').read_text())
    scopes={}
    for scope in ('H427','current1268'):
        units,bindings=load_reference_units(scope,old_rules,llm,inputs)
        dimensions={}
        for dim in DIMS:
            by_reference={}
            for ref in ('A','C'):
                common=[u for u in units if u['references'][ref]['labels'][dim] in (0,1)
                        and rules[u['id']]['labels'][dim] in (0,1)
                        and llm[u['id']]['labels'][dim] in (0,1)
                        and old_rules[u['id']]['candidate']['labels'][dim] in (0,1)]
                methods={}
                for name,pred in [('automatic_rules_v26_2',rules),('LLM_last_executed_gpt56_sol',llm)]:
                    result=checked([(pred[u['id']]['labels'][dim],u['references'][ref]['labels'][dim]) for u in common])
                    previous_name='rules_v26' if name=='automatic_rules_v26_2' else 'llm_gpt56_sol'
                    expected=prior['results'][scope]['references'][ref][dim]['methods'][previous_name]['common_unweighted']['binary_agreement']['kappa']
                    assert result['kappa'] is None or abs(result['kappa']-expected)<1e-12
                    methods[name]=result
                by_reference[ref]=methods
            dimensions[dim]=by_reference
        scopes[scope]={'total_n':len(units),'unweighted_four_column_table':dimensions,'reference_bindings':bindings}
    report={'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'rule_version':'v26-candidate-2-if-relation-generalization-title-scope-fix',
            'LLM_version':'gpt56-sol-v13-native-1; prior executed prompt; v26 prompt has NOT been run',
            'reference_identity':'Original AI A/C first submissions, not human gold standard',
            'comparison_policy':'Within each reference, both methods use the same jointly determinate subset; A and C subsets can differ. Pending labels are not filled with zero.',
            'validation_status':'Descriptive comparison on exposed development material, not a new independent validation.',
            'prediction_binding':{'path':str(prediction_path),'sha256':sha(prediction_path)},
            'scopes':scopes}
    (HERE/'latest-kappa-table-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for scope,data in scopes.items():
        print(scope, 'dimension | Rule-A | Rule-C | LLM-A | LLM-C | nA/nC')
        for dim,r in data['unweighted_four_column_table'].items():
            vals=[r[c][m]['kappa'] for m in ('automatic_rules_v26_2','LLM_last_executed_gpt56_sol') for c in ('A','C')]
            print(dim, ' | '.join(f'{v:.6f}' if v is not None else 'undefined' for v in vals),
                  r['A']['automatic_rules_v26_2']['n'],r['C']['automatic_rules_v26_2']['n'])

if __name__=='__main__':
    main()

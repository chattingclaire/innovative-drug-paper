"""Post-run descriptive error review; never updates frozen predictions or rules."""
from pathlib import Path
import json
from analyze_current_reruns import HERE,load_sealed_predictions,load_reference_units
from comparison_statistics import DIMS,label

def main():
    rules,llm,inputs,_=load_sealed_predictions()
    units,_=load_reference_units('H427',rules,llm,inputs)
    units.sort(key=lambda u:u['id'])
    selected={};groups=[]
    for d in DIMS:
        for m in ('rules_v25','llm_gpt56_sol'):
            for kind,reference,prediction in [('FN_against_both_AI',1,0),('FP_against_both_AI',0,1)]:
                matches=[u for u in units if all(label(u['references'][c]['labels'][d])==reference for c in ('A','C'))
                         and label(u['predictions'][m]['labels'][d])==prediction]
                chosen=matches[:2]
                groups.append({'dimension':d,'method':m,'kind':kind,'total_matching_n':len(matches),'selected_ids':[u['id'] for u in chosen]})
                for u in chosen:
                    selected.setdefault(u['id'],{'id':u['id'],'input':inputs[u['id']],
                        'references':u['references'],'predictions':{k:u['predictions'][k] for k in ('rules_v25','llm_gpt56_sol')},'selection_reasons':[]})
                    selected[u['id']]['selection_reasons'].append({'dimension':d,'method':m,'kind':kind})
    result={'purpose':'Post-run descriptive diagnostic cases; AI-reference agreement is not adjudicated truth',
        'selection':'First two by stable ID in every dimension, new method, and binary error direction where current A/C agree',
        'excluded_from_selection':'Reference disagreements and pending records are excluded from this diagnostic subset only, not from primary analysis',
        'not_for':'No rule/prompt tuning or performance recalculation; cases do not estimate a representative mechanism frequency',
        'groups':groups,'cases':[selected[k] for k in sorted(selected)]}
    out=HERE/'rerun_comparisons/diagnostic_cases.json';assert not out.exists()
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'path':str(out),'case_n':len(selected)},ensure_ascii=False))

if __name__=='__main__':main()

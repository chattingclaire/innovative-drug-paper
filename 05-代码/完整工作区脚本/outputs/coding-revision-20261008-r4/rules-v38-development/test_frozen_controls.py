"""Run preimplementation frozen semantic controls, not validation data."""
from pathlib import Path
import json,hashlib,sys
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'runtime'))
from rules_bounded_v36_2 import renewal_predicate,current_renewal_condition,revise
from rule_support import rebuild,RuleView
f=json.loads((R/'preimplementation_controls_freeze.json').read_text())
assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256']
cases=json.loads(Path(f['path']).read_text());out=[]
for row in cases['F_cases']:
    v=RuleView({'unit_text':row['text']},{'evidence':[]})
    actual=bool(renewal_predicate(row['parent']) and current_renewal_condition(v.text))
    assert actual==row['expected_new_F'],(row,actual)
    out.append({**row,'actual':actual,'pass':True,'test_scope':'semantic predicate/list relation only; source authentication checked separately'})
for row in cases['S_cases']:
    r=rebuild(revise({'unit_text':row['text']},{'judgement_status':'determined','evidence':[],'suppressions':[]}))
    actual=bool(r['labels']['S']);assert actual==row['expected_new_S'],(row,r)
    assert not any(r['labels'][d] for d in ['E','Ec','I','F'])
    for e in r['evidence']:assert row['text'][e['start']:e['end']]==e['text']
    out.append({**row,'actual':actual,'pass':True,'test_scope':'module-level current drug-treatment/safety relation'})
(R/'constructed_controls_results.json').write_text(json.dumps({'all_checks_pass':True,'n':len(out),'controls_sha256':f['sha256'],'not_independent_validation':True,'rows':out},ensure_ascii=False,indent=2)+'\n')
print(len(out),'preimplementation frozen controls passed')

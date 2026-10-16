"""Only predeclared synthetic controls; no actual corpus, answers or scores."""
from pathlib import Path
import copy, hashlib, json, sys
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'runtime'))
from policy_coding_v27 import code_unit
from rules_supply_membership_v38 import revise, RULE
from rule_support import rebuild
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fresh(): return {'judgement_status':'determined','evidence':[],'suppressions':[]}
freeze=json.loads((R/'preimplementation_freeze_v38.json').read_text())
assert not freeze['production_runtime_present_at_freeze']
for item in (freeze['design'],freeze['controls']): assert sha(item['path'])==item['sha256']
supplement=json.loads((R/'static_review_supplement_freeze_v38.json').read_text())
assert sha(supplement['path'])==supplement['sha256']
cases=json.loads(Path(freeze['controls']['path']).read_text())['rows']
cases+=json.loads(Path(supplement['path']).read_text())['rows']
rows=[]
for case in cases:
    record={'unit_text':case['constructed_text']}
    branch=rebuild(revise(record,fresh()))
    actual=code_unit(record)
    assertions={
        'branch_F_matches_frozen_semantics':branch['labels']['F']==case['expected_new_branch_F'],
        'full_unseeded_F_matches_frozen_semantics':actual['labels']['F']==case['expected_F'],
        'branch_changes_only_F':not any(branch['labels'][d] for d in ('S','E','Ec','I')),
        'access_subtype_for_new_positive':not case['expected_F'] or branch['fairness_subtypes']==['access'],
        'new_evidence_present_exactly_when_expected':any(e['rule']==RULE for e in actual['evidence'])==case['expected_new_branch_F'],
        'literal_evidence':all(record['unit_text'][e['start']:e['end']]==e['text'] for e in actual['evidence']+actual['suppressions'] if 'start' in e)}
    extra={**record,'id':'arbitrary-unrelated','review_id':'arbitrary','department':'arbitrary','original_file_stem':'arbitrary'}
    varied=rebuild(revise(extra,fresh()))
    assertions['metadata_invariance']=varied['labels']==branch['labels'] and varied['evidence']==branch['evidence']
    undetermined={'judgement_status':'undetermined','evidence':[],'suppressions':[]}
    assertions['undetermined_preserved']=revise(record,copy.deepcopy(undetermined))==undetermined
    rows.append({**case,'checks':assertions,'pass':all(assertions.values()),'branch_result':branch,'full_unseeded_result':actual})
report={'all_checks_pass':all(x['pass'] for x in rows),'n':len(rows),'positive_n':sum(x['expected_F']==1 for x in rows),
 'negative_n':sum(x['expected_F']==0 for x in rows),'preimplementation_freeze_sha256':sha(R/'preimplementation_freeze_v38.json'),
 'control_sha256':freeze['controls']['sha256'],'static_review_supplement_sha256':supplement['sha256'],'test_sha256':sha(__file__),
 'scope':'only predeclared constructed pairs, branch and unseeded production code_unit; no actual corpus rows',
 'not_independent_validation':True,'human_or_machine_reference_labels_or_performance_read':False,'rows':rows}
(R/'new38_constructed_controls_results_v38.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
failed=[{'name':r['name'],'failed':[k for k,v in r['checks'].items() if not v],'actual_F':r['full_unseeded_result']['labels']['F'],'branch_F':r['branch_result']['labels']['F']} for r in rows if not r['pass']]
print(json.dumps({'all_checks_pass':report['all_checks_pass'],'n':len(rows),'failed':failed},ensure_ascii=False))
assert report['all_checks_pass']

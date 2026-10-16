"""Only semantically corrected v2 predeclared synthetic controls."""
from pathlib import Path
import copy,hashlib,json,sys
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'runtime'))
from policy_coding_v27 import code_unit
from rules_supply_membership_v38 import revise,RULE
from rule_support import rebuild
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fresh():return {'judgement_status':'determined','evidence':[],'suppressions':[]}
freeze=json.loads((R/'preimplementation_freeze_v38_v2.json').read_text())
assert freeze['no_v2_code_or_control_run_at_freeze']
for item in (freeze['design'],freeze['controls'],freeze['semantic_reassessment']):assert sha(item['path'])==item['sha256']
rows=[]
for case in json.loads(Path(freeze['controls']['path']).read_text())['rows']:
 record={'unit_text':case['constructed_text']};branch=rebuild(revise(record,fresh()));actual=code_unit(record)
 checks={'branch_F_matches_v2_frozen_semantics':branch['labels']['F']==case['expected_new_branch_F'],
 'full_unseeded_F_matches_v2_frozen_semantics':actual['labels']['F']==case['expected_F'],
 'branch_changes_only_F':not any(branch['labels'][d] for d in ('S','E','Ec','I')),
 'access_subtype_for_new_positive':not case['expected_F'] or branch['fairness_subtypes']==['access'],
 'new_evidence_present_exactly_when_expected':any(e['rule']==RULE for e in actual['evidence'])==case['expected_new_branch_F'],
 'literal_evidence':all(record['unit_text'][e['start']:e['end']]==e['text'] for e in actual['evidence']+actual['suppressions'] if 'start' in e)}
 extra={**record,'id':'arbitrary-unrelated','review_id':'arbitrary','department':'arbitrary','original_file_stem':'arbitrary'}
 varied=rebuild(revise(extra,fresh()));checks['metadata_invariance']=varied['labels']==branch['labels'] and varied['evidence']==branch['evidence']
 undetermined={'judgement_status':'undetermined','evidence':[],'suppressions':[]}
 checks['undetermined_preserved']=revise(record,copy.deepcopy(undetermined))==undetermined
 rows.append({**case,'checks':checks,'pass':all(checks.values()),'branch_result':branch,'full_unseeded_result':actual})
report={'all_checks_pass':all(x['pass'] for x in rows),'n':len(rows),'positive_n':sum(x['expected_F']==1 for x in rows),'negative_n':sum(x['expected_F']==0 for x in rows),
 'semantic_revision':'v2-root-construct-correction','preimplementation_freeze_sha256':sha(R/'preimplementation_freeze_v38_v2.json'),'control_sha256':freeze['controls']['sha256'],'test_sha256':sha(__file__),
 'scope':'only v2 frozen constructed controls, branch and unseeded production code_unit; actual corpus rows=0','not_independent_validation':True,'human_or_machine_reference_labels_or_performance_read':False,'rows':rows}
(R/'new42_constructed_controls_results_v38_v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
failed=[{'name':r['name'],'failed':[k for k,v in r['checks'].items() if not v],'actual_F':r['full_unseeded_result']['labels']['F'],'branch_F':r['branch_result']['labels']['F']} for r in rows if not r['pass']]
print(json.dumps({'all_checks_pass':report['all_checks_pass'],'n':len(rows),'failed':failed},ensure_ascii=False))
assert report['all_checks_pass']

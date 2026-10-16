"""Exposed integration checks, not independent reference validation."""
import copy,hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent;B=R.parent
sys.path.insert(0,str(R/'runtime'))
from policy_coding_v27 import code_unit
from rules_bounded_v36_2 import revise,renewal_predicate
from rule_support import rebuild
record=next(r['input'] for r in map(json.loads,(B/'rule_inputs_shared_v14.jsonl').read_text().splitlines()) if r['id']=='RECODE25-01562')
def fresh():return {'judgement_status':'determined','evidence':[],'suppressions':[]}
checks={}
checks['actual_source_bound_parent_and_spaced_duration_consumed']=any(e['rule']=='V362_F_verified_actual_renewal_condition' for e in code_unit(record)['evidence'])
checks['parent_duration_whitespace_semantics']=bool(renewal_predicate('符合以下条件的药品，可以简易续约，续约有效期 3 年。'))
x=copy.deepcopy(record);x.pop('verified_parent_context')
checks['missing_parent_adds_no_F']=rebuild(revise(x,fresh()))['labels']['F']==0
x=copy.deepcopy(record)
for p in x['verified_parent_context']:p.pop('repair_version',None)
checks['bare_parent_without_source_certificate_adds_no_F']=rebuild(revise(x,fresh()))['labels']['F']==0
for name,mutate in [
 ('tampered_text',lambda p:p.update(text=p['text'].replace('2 年','9 年'))),
 ('tampered_source_sha',lambda p:p.update(source_sha256='0'*64)),
 ('tampered_target_sha',lambda p:p.update(original_unit_sha256='0'*64)),
 ('tampered_parent_id',lambda p:p.update(paragraph_id='not_a_source_paragraph')),
]:
 x=copy.deepcopy(record);mutate(x['verified_parent_context'][0]);rejected=False
 try:code_unit(x)
 except ValueError:rejected=True
 checks[name+'_rejected']=rejected
x=copy.deepcopy(record);x.update(review_id='arbitrary_review',original_file_stem='arbitrary_file',department='arbitrary_department')
a=rebuild(revise(record,fresh()));b=rebuild(revise(x,fresh()))
checks['metadata_not_semantic_features']=a['labels']==b['labels'] and a['evidence']==b['evidence']
assert all(checks.values()),checks
(R/'source_binding_controls.json').write_text(json.dumps({'all_checks_pass':True,'n':len(checks),'checks':checks,'exposed_development_record':True,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
print(len(checks),'source binding controls passed')

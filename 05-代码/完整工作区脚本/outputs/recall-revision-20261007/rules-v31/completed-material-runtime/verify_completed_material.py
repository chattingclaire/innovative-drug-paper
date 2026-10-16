from pathlib import Path
import json,hashlib,collections
R=Path(__file__).resolve().parent.parent
P=R.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
run=json.loads((R/'all_predictions_completed_material.run.json').read_text())
qa=json.loads((P/'source_context_completion_final_QA.json').read_text())
assert qa['status']=='passed_for_source_structure_and_shared_material_freeze'
assert run['input_sha256']==sha(P/'rule_inputs_v31_shared.jsonl')==qa['actual_input_hashes']['rule_inputs_v31_shared.jsonl']=='40346a9b15020e866cf86474d560ff40bb6bcb6cfa855b1357d8ec3a44b2b400'
assert run['prediction_sha256']==sha(R/'all_predictions_completed_material.jsonl')
for p,h in run['runtime_code_sha256'].items():assert sha(p)==h,p
rows=[json.loads(x) for x in (P/'rule_inputs_v31_shared.jsonl').read_text().splitlines()]
original=[json.loads(x) for x in (P.parent/'final-three-department-20261007/rules-v30/rule_inputs_v30_shared.jsonl').read_text().splitlines()]
out=[json.loads(x) for x in (R/'all_predictions_completed_material.jsonl').read_text().splitlines()]
old=[json.loads(x) for x in (R/'all_predictions.jsonl').read_text().splitlines()]
assert len(rows)==len(original)==len(out)==len(old)==4924
assert [r['id'] for r in rows]==[r['id'] for r in original]==[r['id'] for r in out]==[r['id'] for r in old]
manifest=json.loads((P/'uniform_context_completion_manifest.json').read_text())
changed={x['id'] for x in manifest['changes']}
c=collections.Counter()
for r,b,p,o in zip(rows,original,out,old):
 t=r['input']['unit_text'];q=p['prediction'];assert t==b['input']['unit_text']
 assert q['unit_text_sha256']==hashlib.sha256(t.encode()).hexdigest()
 assert all(type(v)is int and v in [0,1] for v in q['labels'].values())
 assert q['judgement_status']!='undetermined'
 for e in q['evidence']:assert t[e['start']:e['end']]==e['text'];c['evidence_spans']+=1
 for e in q.get('suppressions',[]):
  if all(k in e for k in ['start','end','text']):assert t[e['start']:e['end']]==e['text'];c['suppression_spans']+=1
 for d in q['labels']:
  if q['labels'][d]!=o['prediction']['labels'][d]:
   assert r['id'] in changed;rkey=d+':'+str(o['prediction']['labels'][d])+'->'+str(q['labels'][d]);c[rkey]+=1
assert c['Ec:0->1']==3 and c['F:0->1']==1 and c['F:1->0']==1
assert not any(k in c for k in ['S:0->1','S:1->0','E:0->1','E:1->0','I:0->1','I:1->0'])
assert run['reference_labels_loaded'] is False
classification=json.loads((R/'completed-material-runtime/classification_code_identity_check.json').read_text())
assert classification['all_classification_code_identical'] is True
for x in classification['checks']:
 assert sha(R/'completed-material-runtime'/x['name'])==x['new_sha256']
 if x['name']!='context_validation.py':assert x['old_sha256']==x['new_sha256']
oldrelease=json.loads((R/'release_manifest.json').read_text())
for path,h in oldrelease['artifacts'].items():assert sha(R/path)==h,('old release overwritten',path)
report={'status':'passed_structure_provenance_material_effect_separation','scope':'Does not certify all semantic labels or independent human validity',
 'n':4924,'labels':24620,'pending':0,'original_unit_texts_unchanged':4924,
 'prediction_sha256':sha(R/'all_predictions_completed_material.jsonl'),'input_sha256':sha(P/'rule_inputs_v31_shared.jsonl'),
 'all_runtime_hashes_matched':True,'classification_code_identical':True,'only_validator_extended':True,
 'source_QA_sha256':sha(P/'source_context_completion_final_QA.json'),
 'new_parent_certificates':294,'table_header_certificates':40,'context_certificate_test_methods_passed':10,
 'material_changed_units':len(changed),'material_effect_counts':dict(c),
 'old_code_effect_prediction_unchanged':sha(R/'all_predictions.jsonl'),'old_release_manifest_unchanged':sha(R/'release_manifest.json'),
 'reference_labels_loaded':False,
 'semantic_review_flag':'RECODE25-02077 F rises after generic drug-object completion; actual existing-coverage/category scope requires source-specific semantic review.'}
(R/'completed_material_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))

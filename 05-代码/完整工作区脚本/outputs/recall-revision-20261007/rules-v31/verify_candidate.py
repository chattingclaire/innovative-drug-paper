from pathlib import Path
import json,hashlib,collections
R=Path(__file__).resolve().parent
B=R.parents[1]/'final-three-department-20261007'/'rules-v30'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
run=json.loads((R/'all_predictions.run.json').read_text());inp=Path(run['input_path'])
assert run['input_sha256']==sha(inp)=='062e48e188cefe13ee761bb8719a292172d9ba6b48a03076b1afbbf215f722ac'
assert run['prediction_sha256']==sha(R/'all_predictions.jsonl')
for p,h in run['runtime_code_sha256'].items():assert sha(p)==h,p
rows=[json.loads(x) for x in inp.read_text().splitlines()]
out=[json.loads(x) for x in (R/'all_predictions.jsonl').read_text().splitlines()]
old=[json.loads(x) for x in (B/'all_predictions.jsonl').read_text().splitlines()]
assert len(out)==len(rows)==len(old)==4924
assert [r['id'] for r in rows]==[r['id'] for r in out]==[r['id'] for r in old]
c=collections.Counter()
for r,p,b in zip(rows,out,old):
 q=p['prediction'];t=r['input']['unit_text']
 assert q['unit_text_sha256']==hashlib.sha256(t.encode()).hexdigest()
 assert all(type(v)is int and v in [0,1] for v in q['labels'].values())
 assert q['judgement_status']!='undetermined'
 for d in ['S','E','Ec']:assert q['labels'][d]==b['prediction']['labels'][d]
 for e in q['evidence']:assert t[e['start']:e['end']]==e['text'];c['evidence_spans']+=1
 for e in q.get('suppressions',[]):
  if all(k in e for k in ['start','end','text']):assert t[e['start']:e['end']]==e['text'];c['suppression_spans']+=1
 for d in q['labels']:
  if q['labels'][d]!=b['prediction']['labels'][d]:c['changed_'+d]+=1
assert c['changed_I']==5 and c['changed_F']==17
assert run['reference_labels_loaded'] is False
runtime=(R/'rules_recall_v31.py').read_text()
assert 'RECODE25-' not in runtime
assert not any(s in runtime for s in ['weak_case_audit','all_weak_metrics','reference_labels','kappa','recall_score','0.8'])
report={'status':'passed','scope':'structure_provenance_literal_evidence_regression; semantic validity is not guaranteed by these checks',
 'prediction_sha256':sha(R/'all_predictions.jsonl'),'input_sha256':sha(inp),
 'n':4924,'labels':24620,'pending':0,'unchanged_dimensions':['S','E','Ec'],
 'counts':dict(c),'all_runtime_hashes_matched':True,'id_department_reference_metric_targets_not_used':True,
 'reference_labels_loaded':False,'old_frozen_prediction_sha256':sha(B/'all_predictions.jsonl'),
 'old_frozen_input_sha256':sha(B/'rule_inputs_v30_shared.jsonl')}
(R/'candidate_independent_structure_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))

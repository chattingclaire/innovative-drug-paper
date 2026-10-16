"""Freeze the completed v2 batch and separate code/material effects."""
from pathlib import Path
from collections import Counter
from hashlib import sha256
import json,datetime,difflib

HERE=Path(__file__).resolve().parent
R=HERE.parent;P=R.parent
def sha(p):return sha256(Path(p).read_bytes()).hexdigest()
def rows(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def predictions(p):return {r['id']:r['prediction'] for r in rows(p)}
def changes(a,b,ins):
 out=[]
 for i in a:
  for d in a[i]['labels']:
   if a[i]['labels'][d]==b[i]['labels'][d]:continue
   r=ins[i]
   out.append({'id':i,'dimension':d,'before':a[i]['labels'][d],'after':b[i]['labels'][d],
    'unit_text':r['unit_text'],'source':r.get('unit_source') or r.get('source'),
    'unit_id':r.get('unit_id'),'source_sha256':r.get('unit_source_sha256') or r.get('source_sha256'),
    'candidate_file':r.get('candidate_file'),'candidate_sha256':r.get('candidate_sha256'),
    'verified_parent_context':r.get('verified_parent_context',[]),
    'paragraph_context':r.get('paragraph_context',[]),
    'old_dimension_evidence':[e for e in a[i]['evidence'] if e['dimension']==d],
    'new_dimension_evidence':[e for e in b[i]['evidence'] if e['dimension']==d],
    'new_dimension_suppressions':[e for e in b[i].get('suppressions',[]) if d in e.get('dimensions',[])]})
 return out
def summary(cs):return dict(Counter(f"{x['dimension']}:{x['before']}->{x['after']}" for x in cs))

def main():
 names={'old_code_old_material':'all_predictions_completed_material.jsonl',
  'new_code_old_material':'all_predictions_material_v1_classifier_v2_control.jsonl',
  'old_code_new_material':'all_predictions_material_v2_classifier_v1_control.jsonl',
  'new_code_new_material':'all_predictions_completed_material_v2.jsonl'}
 inputs_v1={r['id']:r['input'] for r in rows(P/'rule_inputs_v31_shared.jsonl')}
 inputs_v2={r['id']:r['input'] for r in rows(P/'rule_inputs_v31_shared_v2.jsonl')}
 original={r['id']:r['input'] for r in rows(P.parent/'final-three-department-20261007/rules-v30/rule_inputs_v30_shared.jsonl')}
 llm=rows(P/'effective_blind_inputs_v30_v2.jsonl')
 assert len(inputs_v1)==len(inputs_v2)==len(original)==len(llm)==4924
 assert list(inputs_v1)==list(inputs_v2)==list(original)==[x['id'] for x in llm]
 assert sha(P/'rule_inputs_v31_shared_v2.jsonl')=='0d4e6358807c5ed38311b9a306dd539de7278e2c57de94b7a0f7730b2e06258a'
 assert sha(P/'effective_blind_inputs_v30_v2.jsonl')=='0c05b1dbd43a74943bb1deafd26b1dbb1963bef0505dda501d83cdf1bfed9955'
 for l in llm:
  r=inputs_v2[l['id']]
  assert r['unit_text']==l['text']==inputs_v1[l['id']]['unit_text']==original[l['id']]['unit_text']
  assert r['llm_v29_shared_context']==l['contexts']
 sourceqa=json.loads((P/'source_object_scope_v2_independent_QA.json').read_text());assert sourceqa['status']=='passed'
 source_files={}
 for r in inputs_v2.values():
  for c in r.get('verified_parent_context',[]):
   if c.get('repair_version') not in {'v31-source-list-predicate','v31-source-object-scope'}:continue
   for p,h in [(c['source_path'],c['source_sha256']),(c['candidate_path'],c['candidate_sha256'])]:
    assert p not in source_files or source_files[p]==h
    source_files[p]=h
 for p,h in source_files.items():assert sha(p)==h,('bound source changed',p)
 data={k:predictions(R/n) for k,n in names.items()}
 for k,n in names.items():
  assert list(data[k])==list(inputs_v2)
  run=json.loads((R/n).with_suffix('.run.json').read_text())
  assert run['prediction_sha256']==sha(R/n)
  assert sha(run['input_path'])==run['input_sha256']
  assert run['reference_labels_loaded'] is False and run['pending_n']==0 and run['n']==4924
  for p,h in run['runtime_code_sha256'].items():assert sha(p)==h,(k,p)
 final=data['new_code_new_material'];spans=Counter()
 for i,r in inputs_v2.items():
  q=final[i];t=r['unit_text']
  assert q['unit_text_sha256']==sha256(t.encode()).hexdigest()
  assert q['judgement_status']!='undetermined'
  assert set(q['labels'])=={'S','E','Ec','I','F'}
  assert all(type(v)is int and v in [0,1] for v in q['labels'].values())
  for e in q['evidence']:assert t[e['start']:e['end']]==e['text'];spans['evidence']+=1
  for e in q.get('suppressions',[]):
   if all(k in e for k in ['start','end','text']):assert t[e['start']:e['end']]==e['text'];spans['suppressions']+=1
 pairs=[('old_code_old_material','new_code_old_material','code_only_at_v1'),
        ('old_code_old_material','old_code_new_material','material_only_at_old_code'),
        ('new_code_old_material','new_code_new_material','material_at_new_code'),
        ('old_code_new_material','new_code_new_material','code_at_v2'),
        ('old_code_old_material','new_code_new_material','joint_v1_to_v2')]
 factorial={'status':'2x2 factorial diagnostic; no reference labels used','stages':{},'comparisons':{}}
 for k,n in names.items():factorial['stages'][k]={'path':str((R/n).resolve()),'sha256':sha(R/n),
  'run_manifest':str((R/n).with_suffix('.run.json').resolve()),'run_manifest_sha256':sha((R/n).with_suffix('.run.json'))}
 for a,b,label in pairs:
  cs=changes(data[a],data[b],inputs_v2)
  factorial['comparisons'][label]={'label_changes':len(cs),'counts':summary(cs),'changes':cs}
 assert factorial['comparisons']['code_only_at_v1']['label_changes']==0
 assert factorial['comparisons']['material_only_at_old_code']['counts']=={'Ec:0->1':2}
 assert factorial['comparisons']['code_at_v2']['counts']=={'F:1->0':1}
 assert factorial['comparisons']['joint_v1_to_v2']['counts']=={'Ec:0->1':2,'F:1->0':1}
 for x in factorial['comparisons']['joint_v1_to_v2']['changes']:
  x['semantic_reason']=('新增的原文对象证书明确协议期内谈判药品，当前计算下调比例并形成支付标准是药品支付安排，支持经济性；未从父条复制经济标签。'
   if x['dimension']=='Ec' else
   '真实总则明确谈判药品(含续约药品)协议到期后的处理规则；当前只规定列入乙类管理。协议到期对象与协议期内对象按相同通用关系识别，既有覆盖的管理类别不新增公平性。')
 write(R/'completed_material_v2_factorial_effects.json',factorial)
 write(R/'completed_material_v2_changes_vs_v1.json',factorial['comparisons']['joint_v1_to_v2'])
 v30=predictions(P.parent/'final-three-department-20261007/rules-v30/all_predictions.jsonl')
 pure=predictions(R/'all_predictions.jsonl')
 allchanges=changes(v30,final,inputs_v2);materialnet=changes(pure,final,inputs_v2)
 write(R/'completed_material_v2_changes_vs_frozen_v30.json',{'n':len(allchanges),'counts':summary(allchanges),'changes':allchanges})
 write(R/'completed_material_v2_changes_vs_pure_v31.json',{'n':len(materialnet),'counts':summary(materialnet),'changes':materialnet})
 # Preserve original code and v1 releases, not just their prediction files.
 frozen_hashes={'all_predictions.jsonl':'be8da51fe8b3dfb887dc13664543cf13ef6e02d75a7086e10c7ccf59948a7b1a',
  'release_manifest.json':'56ff469115740eecd7cfad63871764dc4aaa781a3d85a2e6869ccec506d9b313',
  'all_predictions_completed_material.jsonl':'e9c0ec1085008f2b81a0afd4ec83bdc2c088bc48a9367865da5af42a3406a961',
  'release_completed_material_v1.json':'e432c36d7c1cbc1cf4c9c733687e15ebe0850ce43e64590a35badd44193d8879'}
 for n,h in frozen_hashes.items():assert sha(R/n)==h,(n,'frozen hash changed')
 for name in ['release_manifest.json','release_completed_material_v1.json']:
  release=json.loads((R/name).read_text())
  for p,h in release['artifacts'].items():assert sha(R/p)==h,(name,p,'frozen artifact changed')
 codechecks=[]
 for item in json.loads((HERE/'copied_runtime_provenance.json').read_text()):
  a=Path(item['source']);b=Path(item['copy']);assert sha(a)==item['sha256']
  codechecks.append({'name':b.name,'old_sha256':sha(a),'new_sha256':sha(b),'changed':sha(a)!=sha(b)})
  if sha(a)!=sha(b):
   (HERE/(b.name+'.patch')).write_text(''.join(difflib.unified_diff(a.read_text().splitlines(True),b.read_text().splitlines(True),fromfile=str(a),tofile=str(b))))
 assert {x['name'] for x in codechecks if x['changed']}=={'context_validation.py','policy_coding_v27.py','rules_recall_v31.py'}
 write(HERE/'classification_code_changes_vs_v1.json',{'checks':codechecks,'semantic_change':'Generic already-covered negotiated-medicine agreement expiry/term-completion synonyms; current text or source-validated parent only.','validator_change':'Validate source-object-scope certificates identically to source-list-predicate certificates.','wrapper_change':'Version metadata only.'})
 ctl=R/'material-v2-classification-v1-control'
 assert all(sha(ctl/x['name'])==x['old_sha256'] for x in codechecks if x['name']!='context_validation.py')
 assert sha(ctl/'context_validation.py')==sha(HERE/'context_validation.py')
 tests=json.loads((HERE/'semantic_test_results.json').read_text());assert all(x['successful'] for x in tests['groups'].values())
 assert sum(x['tests'] for x in tests['groups'].values())==207
 chain=[]
 reasons={3378:'当前支付标准支持经济性；真实条件2链确认已有覆盖谈判药品的常规管理归属，不新增公平性。',
 3379:'当前下调比例由直接支付标准父谓词绑定，支持经济性。',
 3380:'当前明确年均药品费用及支付标准下调幅度，独立支持经济性。',
 3381:'当前支付标准最终下调比例取两种算法高值；两输入条件已由真实源父条补齐。',
 3382:'当前市场变化下重新确定支付标准支持经济性；已有覆盖的转类管理不独立支持公平性。'}
 for n in range(3378,3383):
  i='RECODE25-'+str(n).zfill(5)
  chain.append({'id':i,'unit_text':inputs_v2[i]['unit_text'],'v30_labels':v30[i]['labels'],
   'pure_code_v31_labels':pure[i]['labels'],'completed_v1_labels':data['old_code_old_material'][i]['labels'],
   'completed_v2_labels':final[i]['labels'],'reason':reasons[n],
   'parents':inputs_v2[i].get('verified_parent_context',[]),'evidence':final[i]['evidence'],
   'F_suppressions':[s for s in final[i].get('suppressions',[]) if 'F' in s.get('dimensions',[])]})
 assert all(x['completed_v2_labels']['Ec']==1 and x['completed_v2_labels']['F']==0 for x in chain)
 write(R/'completed_condition2_chain_review_v2.json',{'manual':'CAL-5D-20260926-v1.3','status':'Source-bound semantic diagnostic; not human validation','rows':chain})
 qa={'status':'passed_provenance_structure_freeze_and_factorial_effect_separation',
  'scope':'Confirms source bindings, reproducibility, binary completeness and controlled effects; does not certify independent human reliability or every semantic decision.',
  'n':4924,'labels':24620,'pending_n':0,'unit_text_and_id_unchanged_n':4924,'two_methods_same_material_n':4924,
  'input_sha256':sha(P/'rule_inputs_v31_shared_v2.jsonl'),'llm_material_sha256':sha(P/'effective_blind_inputs_v30_v2.jsonl'),
  'prediction_sha256':sha(R/names['new_code_new_material']),'run_manifest_sha256':sha((R/names['new_code_new_material']).with_suffix('.run.json')),
  'source_QA_sha256':sha(P/'source_object_scope_v2_independent_QA.json'),
  'literal_spans':dict(spans),'new_v2_object_certificates':434,'inherited_v1_list_predicate_certificates':294,'table_headers':40,
  'tests_methods_passed':207,'superseded_preexisting_assumption':tests['superseded_preexisting_assumption'],
  'factorial_effect_counts':{k:v['counts'] for k,v in factorial['comparisons'].items()},
  'net_changes_vs_frozen_v30':summary(allchanges),'net_changes_vs_pure_code_v31':summary(materialnet),
  'frozen_prediction_and_releases_verified':frozen_hashes,'frozen_release_all_artifact_hashes_verified':True,
  'runtime_code_hashes_verified':True,'reference_labels_loaded_by_batch':False,'reference_labels_changed':False,
  'all_bound_source_candidate_files_rehashed':len(source_files),
  'resolved_v1_object_gap':'02077: actual 2022 renewal preface supplied uniformly; generic current/parent agreement-expiry object grammar yields F0.',
  'remaining_construct_disagreements_unchanged':['01385 generic purpose I0','03090 generic medical claims definition Ec0'],
  'created_at':datetime.datetime.now().astimezone().isoformat()}
 write(R/'completed_material_v2_QA.json',qa)
 paths=[R/n for n in names.values()]+[(R/n).with_suffix('.run.json') for n in names.values()]
 paths += [R/'completed_material_v2_QA.json',R/'completed_material_v2_factorial_effects.json',R/'completed_material_v2_changes_vs_v1.json',
  R/'completed_material_v2_changes_vs_frozen_v30.json',R/'completed_material_v2_changes_vs_pure_v31.json',R/'completed_condition2_chain_review_v2.json',
  P/'source_object_scope_v2_independent_QA.json',P/'renewal_object_scope_v2_manifest.json',
  P/'rule_inputs_v31_shared_v2.jsonl',P/'effective_blind_inputs_v30_v2.jsonl']
 paths += [R/'自动规则v31材料补全与最终核查说明.md']
 paths += [p for folder in [HERE,ctl] for p in folder.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
 release={'version':'v31-coverage-object-synonyms-20261007','stage':'source_completed_material_v2_with_generic_object_synonyms',
  'status':'source_and_structure_verified_development_revision','manual':'CAL-5D-20260926-v1.3',
  'n':4924,'pending_n':0,'prediction_sha256':qa['prediction_sha256'],'input_sha256':qa['input_sha256'],
  'method_validation_status':'Development reference comparison; A/C remain AI proxies and are not certified human verification.',
  'effect_separation':'2x2 code × material controls saved independently. No classifier thresholds or labels optimized against A/C.',
  'frozen_previous_versions_preserved':True,'created_at':datetime.datetime.now().astimezone().isoformat(),
  'artifacts':{str(p.resolve()):sha(p) for p in paths}}
 write(R/'release_completed_material_v2.json',release)
 print(json.dumps({'status':qa['status'],'prediction_sha256':qa['prediction_sha256'],
  'release_sha256':sha(R/'release_completed_material_v2.json'),'net_changes_vs_v30':qa['net_changes_vs_frozen_v30'],
  'test_methods':207,'artifacts':len(release['artifacts'])},ensure_ascii=False))

if __name__=='__main__':main()

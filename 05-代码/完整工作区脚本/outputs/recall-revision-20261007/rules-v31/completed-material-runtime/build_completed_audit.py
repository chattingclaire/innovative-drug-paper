from pathlib import Path
import json,hashlib,datetime
R=Path(__file__).resolve().parent.parent
P=R.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows={r['id']:r['input'] for r in map(json.loads,(P/'rule_inputs_v31_shared.jsonl').read_text().splitlines())}
new={r['id']:r['prediction'] for r in map(json.loads,(R/'all_predictions_completed_material.jsonl').read_text().splitlines())}
old={r['id']:r['prediction'] for r in map(json.loads,(R/'all_predictions.jsonl').read_text().splitlines())}
reasons={
 '03378':'当前支付标准要求支持Ec；补齐父条后确认是已覆盖谈判药品的常规管理归属，不新增F。',
 '03379':'下调比例的对象由直接父条支付标准消解，当前规则比例内容支持Ec；原来已为1，保持。',
 '03380':'当前直接写年均实际药品费用及支付标准下调幅度，独立支持Ec，不复制父条其他维度。',
 '03381':'当前支付标准最终下调比例取两方法高值，新增两个方法的真原文补齐公式引用；原Ec1保持。',
 '03382':'当前实述市场变化条件下重新确定支付标准的经济安排；既有覆盖的常规管理身份不独立生成F。'}
chain=[]
for n in range(3378,3383):
 rid='RECODE25-'+str(n).zfill(5)
 chain.append({'id':rid,'unit_text':rows[rid]['unit_text'],'old_v31_labels':old[rid]['labels'],'completed_labels':new[rid]['labels'],
 'reason':reasons[str(n).zfill(5)],'parents':rows[rid].get('verified_parent_context',[]),'evidence':new[rid]['evidence'],
 'F_suppressions':[e for e in new[rid].get('suppressions',[]) if 'F' in e.get('dimensions',[])]})
(R/'completed_condition2_chain_review.json').write_text(json.dumps({'status':'AI semantic diagnostic; no reference relabeling','manual':'CAL-5D-20260926-v1.3','prediction_sha256':sha(R/'all_predictions_completed_material.jsonl'),'rows':chain},ensure_ascii=False,indent=2)+'\n')
paths=[R/'all_predictions_completed_material.jsonl',R/'all_predictions_completed_material.run.json',R/'completed_material_QA.json',
 R/'material_effect_changes_by_id_dimension.json',R/'completed_changes_vs_frozen_v30.json',R/'completed_condition2_chain_review.json',
 P/'source_context_completion_final_QA.json',P/'uniform_context_completion_manifest.json']
paths += [p for p in (R/'completed-material-runtime').rglob('*') if p.is_file() and '__pycache__' not in str(p)]
release={'version':'v31-recall-boundary-review-20261007','stage':'source_completed_material_v1_same_classification_code',
 'status':'structurally_verified_candidate_with_flagged_category_object_gap','created_at':datetime.datetime.now().astimezone().isoformat(),
 'n':4924,'pending_n':0,'prediction_sha256':sha(R/'all_predictions_completed_material.jsonl'),
 'input_sha256':sha(P/'rule_inputs_v31_shared.jsonl'),
 'pure_code_effect_prediction_sha256':sha(R/'all_predictions.jsonl'),
 'material_effect_counts':{'Ec_0_to_1':3,'F_0_to_1':1,'F_1_to_0':1},
 'classification_code_unchanged_vs_v31':True,'context_validator_extended':True,
 'reference_labels_changed':False,'tests_context_methods_passed':10,
 'flag':'02077: current restored parent names generic drugs only; source-verified 2022 negotiation-agreement object to be supplied uniformly in a new material version before resolving management-category semantics.',
 'artifacts':{str(p.resolve()):sha(p) for p in paths}}
(R/'release_completed_material_v1.json').write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'prediction_sha256':release['prediction_sha256'],'release_sha256':sha(R/'release_completed_material_v1.json'),'artifact_n':len(paths)},ensure_ascii=False))

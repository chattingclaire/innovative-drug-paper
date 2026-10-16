"""Seal candidate38 v2 bytes for root review; no corpus/model execution."""
from pathlib import Path
from datetime import datetime,timezone
import ast,difflib,hashlib,json
R=Path(__file__).resolve().parent;P=R.parent/'rules-v37.2-development'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,x):
 p=R/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');return p
parent=json.loads((P/'candidate_freeze.json').read_text())
parent_matches={p:sha(p)==v for p,v in parent['production_code_sha256'].items()}
assert all(parent_matches.values())
changed=[];patch=[]
for path in sorted((R/'runtime').glob('*.py')):
 old=P/'runtime'/path.name
 if not old.exists() or path.read_bytes()!=old.read_bytes():
  changed.append(path.name)
  patch.extend(difflib.unified_diff(old.read_text().splitlines(keepends=True) if old.exists() else [],path.read_text().splitlines(keepends=True),fromfile='v37.2/runtime/'+path.name if old.exists() else '/dev/null',tofile='v38-v2/runtime/'+path.name))
assert changed==['policy_coding_v27.py','rules_supply_membership_v38.py'],changed
(R/'source_changes_vs_v37_2_v38_v2.patch').write_text(''.join(patch))
module=(R/'runtime/rules_supply_membership_v38.py').read_text();tree=ast.parse(module)
keys=[n.slice.value for n in ast.walk(tree) if isinstance(n,ast.Subscript) and isinstance(n.slice,ast.Constant)]
assert not set(keys)&{'id','department','source','unit_source','original_file_stem','reference_labels','labels'}
assert 'RECODE25' not in module
reports=['new42_constructed_controls_results_v38_v2.json','inherited_stability_results_v38.json','end_to_end_controls_results_v37_1.json','end_to_end_controls_results_v37_2.json','inherited_v37_constructed_only_results.json','constructed_controls_results.json','legacy_v35_controls.json','inherited67_controls.json','patch_overlay_controls_results_v37.json']
checks={n:json.loads((R/n).read_text())['all_checks_pass'] for n in reports}
assert all(checks.values())
new=json.loads((R/'new42_constructed_controls_results_v38_v2.json').read_text())
stable=json.loads((R/'inherited_stability_results_v38.json').read_text())
pre=json.loads((R/'preimplementation_freeze_v38_v2.json').read_text())
for k in ['design','controls','semantic_reassessment']:assert sha(pre[k]['path'])==pre[k]['sha256']
review={
 'candidate':'v38-institution-routine-drug-supply-membership-development','semantic_revision':'v2-root-construct-correction',
 'status':'code_and_constructed_controls_complete_sealed_for_root_semantic_review_not_final_adoption',
 'review_utc':datetime.now(timezone.utc).isoformat(),
 'result':'v2构造控制通过；旧构造例中新增分支未引入变化，50次继承完整流水线检查仅version变化。待root独立审读后决定是否执行实际语料。',
 'implementation':{'new_module':'runtime/rules_supply_membership_v38.py','entry_change_only':'导入、尾部调用、版本字符串','new_evidence_dimension':'F','new_evidence_subtype':'access','drops_existing_evidence':False,'manual_or_schema_changed':False,'matching_features':'当前分句明确药品、实质纳入/退出谓词及机构用药配备/供应范围。拟/建议等语气不一律排除。','source_authentication_and_completeness_gate':'完整保留37.2入口及依赖；待定直接返回，不新增F。'},
 'semantic_correction':'v1把两条实质拟议/建议误设F0，原件和失败语义的试跑记录保留；v2另封控制后修正，当前采纳依据仅v2。',
 'controls':{'new_v2_constructed_n':new['n'],'positive_n':new['positive_n'],'negative_n':new['negative_n'],'new_control_branch_and_full_unseeded_pipeline_pass':new['all_checks_pass'],'inherited_v38_branch_abstention_n':stable['v38_branch_abstention_inherited_n'],'inherited_full_pipeline_comparison_n':stable['full_unseeded_pipeline_comparison_n'],'parent_module_controls':'33、19、67、59条及7项合成来源认证检查另有记录；不同检查口径重复，不相加当独立样本。','all_tests_constructed_only':True},
 'read_scope':{'known_exposed_target':'RECODE25-01361','already_exposed_development_flag_retained':True,'known_target_actual_text_read':True,'known_target_actual_prediction_run':False,'other_reserved_units_text_or_prediction_or_labels_read_this_task':False,'human_A_C_or_kappa_or_performance_read':False,'actual_corpus_units_run':0,'models_called':0,'manuscript_changed':False,'v37_2_production_24_files_unchanged':all(parent_matches.values())},
 'limitations':['构造控制不是独立算法效度验证；01361已经暴露，不能据本轮开发恢复独立性。','词法/局部语法门禁是分支覆盖界限，不是手册F=0的充分依据。未解析的上下文或不同语序可能仍实质涉及F。','不覆盖所有医保/供应语法，仅补机构常规药品供应范围的明确局部关系。','尚未对实际01361或全量语料运行；最终采纳和实际执行等root复核。'],
 'test_sha256':{str(p.resolve()):sha(p) for p in sorted(R.glob('test_*.py')) if p.name!='test_predeclared_v38.py'},
 'result_sha256':{str((R/n).resolve()):sha(R/n) for n in reports},
 'parent_runtime_hash_checks':parent_matches,'production_code_changed_vs_parent':changed,
 'code_static_feature_check':{'no_case_id_literal':True,'no_identifier_department_source_reference_label_or_result_labels_subscript_in_new_module':True,'only_current_unit_text_through_RuleView':True}}
rp=write('implementation_review_v38_v2.json',review)
md='''# candidate38 v2 待根审说明

本候选只补充实际药品纳入/退出机构常规用药配备、供应范围的明确局部关系，新增 F 的 access 证据，保留其他维度与原有证据。37.2 的 24 份生产代码原件哈希均未改变；新副本仅新增关系模块，修改入口导入、调用和版本。

F 测量是否实质讨论保障获取内容，不要求安排已经实施。v1 将两条明确范围和条件的拟议/建议误设为 F=0，根审已指出。原冻结、代码快照及试跑结果保留，v2 在改代码前另行冻结：原两句转正类补充，反例改为只组织后续研究/讨论的职责。不能用 v1 的通过记录证明语义正确。

v2 的 42 条合成控制（23 正、19 负）均通过新分支及完整、未预置证据的 code_unit 检查。覆盖实际纳入/退出与负向条件、拟议/建议、倒装、目录名宾语；反例涉及资料/企业中心词、档案目录、申请路线、纯后续研究职责、价格上限及目录身份仅作事务前提。

另用新分支检查 182 次继承合成例，均未误添证据；50 次继承完整流水线结果与 37.2 相比，标签、证据及其他内容不变，仅候选版本字符串变化。不同检查使用重复构造材料，不能加总为独立样本量。

已暴露 01361 的原句用于设计，继续保留开发暴露标记。本轮未运行该实际单元，也未运行全量；未读取其他保留成员的文本/预测/标签，未参考 A/C、κ或性能，未改主稿。代码已按哈希封存供根审，尚未作最终采纳冻结。

局部语法未匹配仅表示分支覆盖有限，不能据此新增人工 F=0 边界。构造控制通过也不能替代独立效度检验。
'''
(R/'candidate38_v2_待根审说明.md').write_text(md)
manifest=write('candidate_review_manifest_v2.json',{
 'candidate':review['candidate'],'semantic_revision':review['semantic_revision'],'status':review['status'],'sealed_utc':datetime.now(timezone.utc).isoformat(),
 'parent_candidate_freeze':{'path':str((P/'candidate_freeze.json').resolve()),'sha256':sha(P/'candidate_freeze.json')},
 'preimplementation_v2_freeze':{'path':str((R/'preimplementation_freeze_v38_v2.json').resolve()),'sha256':sha(R/'preimplementation_freeze_v38_v2.json')},
 'production_code_sha256':{str(p.resolve()):sha(p) for p in sorted((R/'runtime').glob('*.py'))},
 'review_sha256':{str(rp.resolve()):sha(rp),str((R/'candidate38_v2_待根审说明.md').resolve()):sha(R/'candidate38_v2_待根审说明.md'),str((R/'source_changes_vs_v37_2_v38_v2.patch').resolve()):sha(R/'source_changes_vs_v37_2_v38_v2.patch')},
 'test_sha256':review['test_sha256'],'result_sha256':review['result_sha256'],
 'builder_sha256':sha(__file__),'actual_corpus_units_run':0,'model_calls':0,'known_exposed_01361_flag_retained':True,'root_final_adoption_review_pending':True})
print(json.dumps({'review_manifest':str(manifest),'review_manifest_sha256':sha(manifest),'new_module_sha256':sha(R/'runtime/rules_supply_membership_v38.py'),'entry_sha256':sha(R/'runtime/policy_coding_v27.py'),'implementation_review_sha256':sha(rp),'new_controls_result_sha256':sha(R/'new42_constructed_controls_results_v38_v2.json'),'stability_result_sha256':sha(R/'inherited_stability_results_v38.json')},ensure_ascii=False))

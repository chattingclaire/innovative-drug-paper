"""Complete read-only audit narrative after the independent mechanical check."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,re
BASE=Path(__file__).resolve().parent
OUT=BASE/'rules-v38-shadow-independent-comparison'
RUN=BASE/'rules-v38-shadow-full-v14'
INPUT=BASE.parent/'coding-revision-20261007-r3/rule_inputs_shared_v14.jsonl'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,x):
 p=OUT/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');return p
s=json.loads((OUT/'mechanical_comparison_summary.json').read_text());ex=json.loads((OUT/'previously_exposed_01361_flagged_check.json').read_text())
assert s['nonreserved_projection_n']==0 and s['counts_by_group']['reserved267_aggregate_only']['any_nonversion_changed_units']==1
assert ex['labels_before_v37_2']=={'S':1,'E':0,'Ec':0,'I':0,'F':0}
assert ex['labels_after_v38']=={'S':1,'E':0,'Ec':0,'I':0,'F':1}
assert ex['fairness_subtypes_after']==['access']
assert len(ex['new_evidence'])==1 and ex['new_evidence'][0]['rule']=='V38_F_current_institution_routine_drug_supply_membership'
first=json.loads((RUN/'actual_command.json').read_text());second=json.loads((RUN/'attempt2_command.json').read_text())
assert first[1:]==second[1:] and first[0]!=second[0]
assert (RUN/'actual_exit_code.txt').read_text().strip()=='1' and (RUN/'attempt2_exit_code.txt').read_text().strip()=='0'
run=json.loads((RUN/'all_predictions_material_v14_shadow.run.json').read_text())
assert second[0]==run['python_executable']=='/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
primary=Counter()
for line in INPUT.read_text().splitlines():
 if not line.strip():continue
 x=json.loads(line)['input'];p=x.get('unit_source') or x.get('source');h=x.get('unit_source_sha256') if x.get('unit_source') else x.get('source_sha256')
 primary['unit_source_selected' if x.get('unit_source') else 'source_fallback_selected']+=1
 assert h==run['actual_source_and_candidate_sha256'][str(Path(p).resolve())]
 primary['declared_primary_sha_matches_actual_bound_source']+=1
 primary['legacy_source_differs_from_primary']+=x.get('source')!=p
result={'status':'complete_no_mechanical_or_single_exposed_case_semantic_blocker_found','review_utc':datetime.now(timezone.utc).isoformat(),'reviewer':'/root/validation_state_oct8; candidate38 author, separate mechanical checker from root batch executor','review_scope':'Fresh read-only comparison against37.2 shadow, all4924 IDs/hashes/labels/subtypes/evidence; only explicit exposed01361 exception reviewed semantically; no claim of an independent validity test.',
 'mechanical_summary':{'path':str((OUT/'mechanical_comparison_summary.json').resolve()),'sha256':sha(OUT/'mechanical_comparison_summary.json')},
 'conclusion':{'only_nonversion_changed_unit_is_known_exposed01361':True,'all_other_4923_units_identical_except_version':True,'S_E_Ec_I_all4924_unchanged':True,'F_changed_cells':1,'F_direction':'0->1','F_access_subtype_added':True,'nonreserved_changed_units':0,'nonreserved_semantic_review_required_n':0,'no_unreviewed_nonreserved_changes':True,'evidence_span_counts_old_new':[4195,4196],'suppression_span_counts_old_new':[2625,2625]},
 'single_exposed_case_semantic_review':{'id':'RECODE25-01361','retains_exposed_development_flag':True,'manual_basis':'v1.4 公平性F第1项：实际药物给付、配备/供应范围以及纳入退出和具体条件；不要求范围扩大。v1.3 F=1为关注内容而非政策效果。','reason':'当前原句直接规定因不良反应和安全隐患将实际药品清退出本机构用药供应目录；药品、清退谓词及实际机构供应范围均在本句，支持F的access。档案保存是另一个命题，不能遮蔽独立的退出安排。','S_preserved':True,'no_other_dimension_or_subtype_reinterpreted':True,'not_independent_validation':True,'evidence_record_path':str((OUT/'previously_exposed_01361_flagged_check.json').resolve()),'evidence_record_sha256':sha(OUT/'previously_exposed_01361_flagged_check.json')},
 'source_display_binding_check':dict(primary),
 'privacy':{'reserved_members_n':267,'other_reserved_predictions_reported_only_in_aggregate':True,'individual_exception_only':'RECODE25-01361','nonreserved_projection_is_empty':True,'redaction_strategy':'Prior exact full-unit replacement plus normalized full-unit filter and conservative24-character context overlap omission; no context was exported because there were no nonreserved changes.','old_reserved_package_unchanged':True,'human_A_C_or_reference_or_kappa_loaded':False},
 'execution_audit':{'first_exit':1,'first_failure_module':re.findall(r"No module named ['\"]([^'\"]+)", (RUN/'actual_stderr.log').read_text()),'second_exit':0,'parameters_identical_except_python_executable':True,'accepted_bundled_python':run['python_executable'],'code_or_definition_changed_for_retry':False,'first_logs_retained':True,'second_logs_separate':True,'prediction_sha256':s['shadow_predictions_sha256'],'run_manifest_sha256':s['new_run_manifest_sha256'],'candidate_freeze_sha256':s['candidate_freeze_sha256'],'prediction_recomputed_by_auditor':False,'stderr_not_evidence_of_semantic_correctness':True,'trace_limit':'run.json preloop runtime map lists24 modules and omits late-import source_family_v14.py; freeze binds all25 production files, root runner checks all25 before execution, independent current hashes all25 match. This records the map limit without changing code or rerunning.'},
 'audit_script_technical_note':'First checker invocation wrongly required judgement_status=determined; inspected aggregate status counts showed both stages use rule_prediction for all4924, corrected the auditor assertion and reran only the comparison. No classifier was rerun and no first audit output existed.',
 'no_classifier_candidate_repair_no_manual_no_A_C_no_manuscript_changes':True,'script_sha256':sha(__file__)}
rp=write('independent_full_run_review.json',result)
md='''# 规则38全量运行独立机械复核

以37.2 shadow为基线，4924条ID、original_id、逐条原文SHA、严格五维0/1、证据重建标签、F/I/S子类型及质量安全标记均通过核对。两版共用输入SHA、源文件与候选文件绑定相同，冻结生产代码当前哈希匹配。

唯一非版本变化为已登记暴露的01361：F从0变1，增加access子类型及一条逐字证据。其余4923条除version外完全相同，全部4924条的S/E/Ec/I不变。非预留变化投影为空，因此没有待审的非预留变化。267预留成员其他逐条判断和原文没有展示。

01361当前条款直接规定因不良反应和安全隐患清退实际药品、退出本机构用药供应目录，符合v1.4 F第1项。新增证据局部绑定药品对象、清退谓词和机构供应范围，S保留。该例已经用于开发，继续保留暴露标记，不能作为独立效度检验。

文字证据从4195处增为4196处，抑制证据均为2625处，逐字偏移检查通过。全部4924条来源展示均优先unit_source，其声明SHA与实际绑定源一致；874条legacy source与实际unit_source不同，不能据旧source字段展示实际原件。

首次调用因Python环境缺pypdf而退出1，未产生预测；同参数换回既有bundledPython技术重试退出0，原日志及第二次日志分别保留，规则和定义未变。运行清单的启动前模块表记录24份、未列后续导入source_family_v14；冻结清单绑定25份，执行前与本次独立读取时的25份哈希全部匹配。此为留痕范围说明，不是语义通过的依据。

复核者参与过candidate38实现，本次使用另写比较脚本核对root执行结果；未再次执行分类器或模型，未读取A/C或性能，未改手册、编码或正文。机械一致性与构造控制均不能替代独立效度检验。
'''
(OUT/'规则38全量运行独立复核.md').write_text(md)
seal=write('complete_independent_review_seal.json',{'sealed_utc':datetime.now(timezone.utc).isoformat(),'files':{str(p.resolve()):sha(p) for p in sorted(OUT.iterdir()) if p.is_file()},'builder':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)}})
print(json.dumps({'review_path':str(rp),'review_sha256':sha(rp),'markdown_sha256':sha(OUT/'规则38全量运行独立复核.md'),'complete_seal_sha256':sha(seal)},ensure_ascii=False))

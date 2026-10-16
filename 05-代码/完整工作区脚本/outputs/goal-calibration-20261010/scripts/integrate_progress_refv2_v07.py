"""Integrate actual sealed evidence; retain historical versions and acceptance gates."""
from pathlib import Path
import json
from datetime import datetime
from zoneinfo import ZoneInfo

root = Path(__file__).resolve().parents[1]
stamp = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def read(rel):
    return json.loads((root / rel).read_text())
def save(rel, obj):
    (root / rel).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

native_path = '06-coding/root-machine-review/native36-v12-first-arithmetic-v2/arithmetic-crosscheck.json'
rule_path = '06-coding/root-machine-review/rule-v07-unique77-first/arithmetic/arithmetic-crosscheck.json'
native = read(native_path)
rule = read(rule_path)
p = read('progress.json')
p['last_integration_at'] = stamp
p['steps'][0]['remaining'] = [
    'v13仅同源第三/五条原文补充及全4481字段/字节画像正在封存；旧正文和CTX不变',
    '00064确指指南版本仍未决，相关来源依赖保留未知，不反复搜索',
    '共同手册/材料/两机器/预算/抽样统计方案最终联合freeze尚未完成']
p['steps'][2]['status'] = 'reference_v2_adjudicated_manual_v13_clarified_development_joint_freeze_pending'
p['steps'][2]['remaining'] = [
    '共同手册v1.3澄清既有完整分支、宗旨/措施、申请分类/支付行为边界；开发候选非最终freeze',
    '原生36对新版参照有3处真实误判：01423 S漏判，00720/03818 Ec误报',
    '规则v08首次回归报告修复原两症状，但01729 I新增漏判；等待封存后root核验及通用修正',
    'v13同源补充接入、实际完整共同输入运行与最终联合freeze仍待完成']
p['steps'][4]['status'] = 'v07_actual_source_execution_and_refv2_arithmetic_completed_development_repairs_pending'
p['steps'][4]['remaining'] = [
    'v07实际83记录执行/77唯一记录，415执行槽与385唯一比较槽分别报告；新版参照1处S误报',
    'v08已报告首次77条开发回归1处新I漏判，未root验收；v13材料消费另版进行',
    '正式独立真人首判/可信裁定参照、两机器效度及R1/R2/R3/W/H稳定性尚未执行',
    '合格全量结果、正式指标验收及整篇正文待完成']
evidence = {
  2: ['03-manual/common-manual-v1.3-development.md',
      '03-manual/manual-v1.3-clarification-change-log.json',
      '04-calibration/source-impact4-v12/admin/root-adjudication-native36-v2.json',
      '06-coding/development-reference77-v12-root-adjudicated-v2/reference.jsonl'],
  4: [native_path, rule_path,
      '06-coding/root-machine-review/native36-v12-first-arithmetic-v2/sklearn-independent-verification.json',
      '06-coding/root-machine-review/rule-v07-unique77-first/arithmetic/sklearn-independent-verification.json',
      '06-coding/root-machine-review/rule-v06-v07-source-quality-sol/seal-v2.json']}
for i, items in evidence.items():
    for item in items:
        if item not in p['steps'][i]['completed_evidence']:
            p['steps'][i]['completed_evidence'].append(item)
p['reference_v2_actual'] = {
  'identity': 'nonblind root-adjudicated AI development reference, not human gold',
  'reference77_sha256': rule['reference_sha256'],
  'reference36_sha256': native['reference_sha256'],
  'only_label_change': {'id':'RECODE25-04333', 'dimension':'S', 'old':1, 'new':0},
  'reason': 'pure document enactment purpose has no current substantive safety evaluation/evidence/control under existing manual',
  '01423_S':1, '00720_Ec':0, '03818_Ec':0,
  'old_references_firsts_and_reasons_preserved': True,
  'semantic_definitions_or_threshold_changes':False,
  'formal_acceptance':False}
p['native36_v12_development']['reference_v2_current'] = {
  'n':native['n'], 'disagreements':native['binary_disagreements'],
  'per_dimension':native['per_dimension'],
  'arithmetic':native_path, 'independent_sklearn_verification':True,
  'first_prediction_bytes_changed':False, 'formal_acceptance':False}
p['native36_v12_development']['old_reference_comparison_preserved'] = True
p['rule_development_v07_actual'] = {
  'actual_record_executions':83, 'unique_records':77,
  'retained_execution_slots':415, 'unique_comparison_slots':385,
  'semantic_null_slots':0, 'technical_failure_slots':0,
  'v06_failed_execution_slots_preserved':15,
  'source_QA_binding_checks':2136, 'source_QA_distinct_files':280,
  'source_QA_v2_seal_sha256':'f95b04cbc25c1c4a18793fd2b7db65309409700b661b8ddd1011a8f7dc37c8b8',
  'actual_program_pixel_reads':0,
  'remaining_false_necessary_list_request':'00652 以下简称; retained in v07 and generic repair pending root acceptance',
  'per_dimension':rule['per_dimension'], 'disagreements':rule['binary_disagreements'],
  'arithmetic':rule_path, 'independent_sklearn_verification':True,
  'formal_acceptance':False}
p['manual_clarification_v13'] = {
  'path':'03-manual/common-manual-v1.3-development.md',
  'sha256':'a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f',
  'parent_old_text_byte_preservation_verified':True,
  'existing_definitions_and_thresholds_unchanged':True,
  'joint_final_freeze':False}
p['source01423_material_envelope_actual'] = {
  'path':'04-calibration/source-impact01423-addendum-v12/preparation/material-envelope.json',
  'sha256':'14190c73a6638f240f00ba69840d8451c53a4328e2a8f28ca50b1bb7f2aa3b84',
  'old_ten_roots_exact_preserved':True, 'original_paragraphs_n':9,
  'root_three_actual_roles_equal':True,
  'actual_judgments_using_envelope':False, 'formal_packet_schema_integrated':False}
p['source_v13_pending'] = {
  'owner':'/root/validation_design_sol',
  'directory':'01-review/context-projection-sol/source-interface-v13-addendum',
  'scope':'same document third/fifth original nine paragraphs in two neutral resource arrays; all4481 shape/bytes/frame order',
  'source_document_affected_record_n_reported':59,
  'sealed_and_root_verified':False,
  'source_only_not_labels':True}
p['llm_full_input_protocol']['v3_integration'] = {
  'status':'finite_dependency_plan_completed_waiting_source_v13_seal',
  'all4481_profile_required':True, 'actual_RWH_runs':0, 'final_budget_bound':False}
for task in p['parallel_tasks_current']:
    if task.get('directory') == '06-coding/development-rule-sol':
        task['status']='v07_root_verified_v08_first_regression_reported_with_new_error_pending_root_review'
    if task.get('directory') == '06-coding/native-llm36-v12-sol/first-run':
        task['status']='first_actual_sealed_root_quality_and_refv2_arithmetic_completed'
    if task.get('directory') == '06-coding/llm-protocol-final-input-sol':
        task['status']='v2_sealed_root_verified_v3_dependency_plan_complete_waiting_source_v13'
p['final_acceptance']=False
save('progress.json',p)
t=read('task_changes.json')
t['changes'].append({'date':stamp,
 'change':'旧04333参照依原文/既有手册纠正S1→0；v1.3通用边界澄清；实际原生36与规则v07按新版AI开发参照独立复算',
 'reason':'旧共识也会错；先源文裁定后算术，不据分数改定义。材料身份读取与语义正确分别核查。',
 'effects':{'reference_label_changes_n':1,'old_raws_preserved':True,
   'native36_remaining_errors_n':3,'rule_v07_unique77_errors_n':1,
   'rule_v07_actual_executions':83,'rule_v07_execution_slots':415,
   'rule_v07_unique_comparison_slots':385,'v06_technical_failure_slots_preserved':15,
   'v08_first_regression_report':'original symptoms repaired, new01729 I FN; root review pending',
   'manual_definition_thresholds_changed':False,'v13_neutral_source_in_progress':True,
   'new_unseen_holdout_consumed':0,'new_real_human_execution':0,
   'formal_acceptance':False,'whole_paper_writing':'not started'},
 'evidence':[native_path,rule_path,'03-manual/manual-v1.3-clarification-change-log.json',
   'logs/root-material-envelope-and-v13-manual-binding-20261010.json',
   '06-coding/root-machine-review/rule-v06-v07-source-quality-sol/seal-v2.json']})
save('task_changes.json',t)
rp=root/'README.md'
text=rp.read_text()
a=text.index('截至2026年10月10日05:38：')
b=text.index('2026年10月10日已建立12份',a)
current=f'''截至{stamp[:16].replace('T',' ')}：三处源文/既有手册复核完成。04333仅说明制定处方审核规范的宗旨，旧AI开发参照的S=1已另版纠正为0，原标签、理由及各方首判保留；00720/03818属于申请类别选择，Ec=0保持不变。01423完整表行包含6年基础保护和4年例外，原参照S=1保留，旧过宽理由已纠正。参照身份仍是非盲AI开发裁定，不是真人gold。

原生LLM36条180项首判保持原字节，对新参照有3处误判：01423安全性漏判，00720/03818经济性误报。安全性κ=.654、Recall=.500、F1=.667，经济性κ=.721、Precision=.600、F1=.750；公平性全阴性，κ/P/R/F1为NA。四格与逐维指标已用scikit-learn1.8.0独立核对，未达到全部目标。

规则v07已实际完成83次记录执行、415个判断槽，去重后77条/385项参与比较；旧v06三条记录的15个技术失败槽全部保留。来源机械核查完成2136次绑定检查，涉及280文件；不把来源读入收据当成语义正确证明。对新参照v07有04333安全性误报，κ=.926、Precision=.875，其他维度点指标为1；这仍是开发诊断。v08首次回归报告已修复04333及“以下简称”误报警，另出现01729创新性漏判，等待封存后的主任务核验与通用修正。

共同手册v1.3只澄清既有完整分支、宗旨与实质措施、申请分类与支付行为三条边界，旧定义文本已逆替换验证逐字节保留。01423旧10根键与9段同源补充的组合材料已核验，三个角色实际读取字节相同；全4481的v13纯来源接口、字段形状/字节画像正在另版封存，未参与实际编码。必要读取协议v2已核验，v3接入计划等待新来源seal；预算、正式R1/R2/R3/W/H、真人独立编码及最终联合freeze仍未执行。

完整正文继续等待正式指标验收。下面保留先前过程与其当时版本，不将历史开发一致性充作本次验收。

'''
rp.write_text(text[:a]+current+text[b:])
print(json.dumps({'updated':stamp,'files':['progress.json','task_changes.json','README.md'],'goal_status':'active'},ensure_ascii=False))

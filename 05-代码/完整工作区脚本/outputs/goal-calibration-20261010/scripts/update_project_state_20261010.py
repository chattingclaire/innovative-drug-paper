"""Integrate completed parallel evidence into the existing goal state."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'progress.json'
state=json.loads(path.read_text())
by_step={x['step']:x for x in state['steps']}
def evidence(step,*files):
    a=by_step[step].setdefault('completed_evidence',[])
    for f in files:
        assert (ROOT/f).exists(), f
        if f not in a:a.append(f)
evidence(1,'parallel-manuscript/interview-audit/interview-evidence.json','parallel-manuscript/interview-audit/source_manifest.json','parallel-manuscript/interview-audit/audit_validation.json')
by_step[1]['remaining']=['00064援引的同时期版本未核明；维持材料问题，不回填标签','共同材料最后源图/转写修复及新补材逐条绑定']
evidence(3,'04-calibration/pilot01/A/discussion01.json','04-calibration/pilot01/B/discussion01.json','03-manual/common-manual-v1.1-development.md','03-manual/manual-v1.1-change-log.json','04-calibration/coverage01/admin/selection.json','01-review/context-projection-sol/projection-audit.json')
by_step[3]['status']='v11_general_rules_recorded_source_repair_and_second_development_execution_pending'
by_step[3]['remaining']=['共同材料新版修复：图3条件2误转为条件7、原PDF核明','新包41条补材重判及36条三部门开发覆盖','据真实分歧复核后冻结，保持首判不变']
evidence(4,'parallel-metrics/prospective-design/strata-planning.json','parallel-metrics/prospective-design/precision-planning.md','parallel-metrics/prospective-design/planning-QA.json')
by_step[4]['status']='prospective_planning_completed_selection_and_execution_pending'
by_step[4]['remaining']=['比较1444全核及600以内方案后事前锁定实际工作量/精度方案','最终共同手册、机器方法和纯来源材料冻结','真人首判来源/人员安排待回复；先准备完整盲包','独立协商前封存与可信裁定']
evidence(6,'parallel-manuscript/interview-audit/interview-evidence.md')
state['last_integration_at']=datetime.now().isoformat(timespec='seconds')
state['development_trial02_plan']={'n':77,'prior41_rejudgment':41,'new_cross_department_development':36,'new_cross_department_counts':{'NMPA':12,'NHSA':12,'NHC':12},'new_final_holdout_consumed':0,'identity':'AI','first_trial_preserved':True,'labels_completed':False}
state['writing_requirements_checked']={'journal':'科学决策','template_requirements':'parallel-manuscript/期刊要求.json','reference_current_n':66,'reference_journal_max_found':False,'pruning_rule':'必要方法、理论、结果和制度证据优先；38–42只是编辑预算建议，不是期刊上限','interviews_actual_scope':'两份专家主题纪要及三场会议事件材料，不补人数/未执行程序','anonymous_public_use_author_confirmation_received':True,'full_prose_revision_started':False}
state['parallel_tasks_current']=[
    {'role':'AI开发判读A','owner':'/root/pilot01_a_sol','directory':'04-calibration/pilot01/A'},
    {'role':'AI开发判读B','thread_id':'01a121c0-ea65-7f43-9de2-46b9305297fe','directory':'04-calibration/pilot01/B'},
    {'role':'来源与结构投影','owner':'/root/validation_design_sol','directory':'01-review/context-projection-sol'},
    {'role':'指标与事前精度设计','thread_id':'01a121b3-35ac-7200-af26-cfc3840c5de8','directory':'parallel-metrics'},
    {'role':'期刊结构、引用与访谈审查','thread_id':'01a121b3-3cc9-7020-bca6-5aaa1b8fd301','directory':'parallel-manuscript'},
    {'role':'共同手册与规则代码对照','thread_id':'01a121dd-b07e-7292-89c6-c5c7fca869fd','directory':'06-coding/development-rule-sol'},
]
path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
changes_path=ROOT/'task_changes.json'
changes=json.loads(changes_path.read_text())
entry={'date':'2026-10-10','change':'v1.1通用边界决策与77条开发方案','reason':'四处真实分歧、两处确指补材及源结构/图转写错误，第一轮卫健仅1条不足以检验共同执行','effects':{'original_AI_first_submissions':'preserved','new_final_holdout_consumed':0,'human_results':'not_fabricated','final_thresholds':'unchanged','full_manuscript_writing':'after acceptance'},'evidence':['03-manual/manual-v1.1-change-log.json','04-calibration/coverage01/admin/selection.json','parallel-manuscript/interview-audit/interview-evidence.json']}
if not any(x.get('change')==entry['change'] for x in changes['changes']): changes['changes'].append(entry)
changes_path.write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
print('Integrated steps 1–4, 6–7 and current parallel ownership; final_acceptance remains false.')

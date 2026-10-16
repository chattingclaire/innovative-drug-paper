"""Receive actual first-run evidence and update the eight-step working instruction.

This does not run coders, score labels, release blind packets, or edit sealed inputs.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_bytes())


def bind(path):
    path = Path(path)
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def write(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    stamp = datetime.now(timezone.utc).isoformat()
    review_name = "06-coding/frozen-rule800-technical-request-review-sol/report.json"
    review = read(review_name)
    review_binding = bind(ROOT / review_name)
    assert review_binding["sha256"] == "71919cb0d4adade074e16116e6c46c58299eec9aeed46a6158895cf6e2782d37"
    checked = []
    for item in review["input_bindings"]:
        actual = bind(item["path"])
        assert actual == item, item["path"]
        checked.append(actual)
    receipt_name = "logs/root-rule800-technical-request-review-reception-20261010.json"
    assert not (ROOT / receipt_name).exists()
    write(receipt_name, {
        "created_at_utc": stamp, "report": review_binding,
        "actual_input_SHA_bytes_verified_N": len(checked), "inputs": checked,
        "received_conclusion": review["conclusion"],
        "actual_policy_body_or_semantic_judgment_by_ROOT": False,
        "source_actual_availability_or_affected_dimensions": "unknown",
        "future_patch_authorized_scope": "mechanical exception audit preservation only; retain all guards and failure masks",
        "semantic_routing_fix_or_actual_cohort_rerun_authorized": False,
        "old_first_attempt_failure_and_null_states_preserved": True,
    })
    actual = read("logs/root-rule800-actual-first-reception-20261010.json")
    registration = read("logs/root-rule800-scope-reception-and-execution-registration-20261010.json")
    assert (actual["record_N"], actual["dimension_N"], actual["retained_binary_decision_N"],
            actual["lawful_null_dimension_N"], actual["technical_failure_dimension_N"]) == (800, 4000, 3987, 3, 10)
    assert actual["formal_acceptance"] is False
    backup = ROOT / "00-baseline/20261010-pre-rule800-actual-first-root-integration"
    backup.mkdir()
    for name in ("progress.json", "task_changes.json", "完整Goal指令.md", "README.md"):
        shutil.copyfile(ROOT / name, backup / name)

    p = read("progress.json")
    p["previous_goal_turn_audit"] = p["current_goal_turn_classification"]
    f = p["frozen_rule800_candidate_first"]
    f.update({
        "state": "actual_once800_first_sealed_failed_execution_attempt_partial_decisions_retained",
        "actual_execution_result_pending": False,
        "actual_execution_status": actual["run_status"], "actual_driver_exit": actual["actual_driver_exit"],
        "actual_cohort_inference_runs": 1, "actual_record_N": 800, "actual_dimension_N": 4000,
        "actual_retained_record_N": 798, "actual_retained_binary_dimension_N": 3987,
        "actual_lawful_null_dimension_N": 3, "actual_technical_failure_dimension_N": 10,
        "actual_technical_failure_records": actual["technical_failure_records"],
        "actual_seal": actual["actual_seal"], "actual_seal_members_ROOT_verified_N": 17,
        "per_dimension_raw_prediction_counts_not_accuracy_or_population_attention": actual["per_dimension_raw_prediction_counts"],
        "actual_reception": "logs/root-rule800-actual-first-reception-20261010.json",
        "technical_failure_review": review_name, "technical_failure_review_ROOT_receipt": receipt_name,
        "mechanical_audit_preservation_patch": "finite agent task running; no real-cohort rerun or semantic repair authorized",
        "actual_human_independent_first_N": 0, "actual_human_or_AI_adjudicated_reference_N": 0,
        "actual_model_calls": 0, "actual_scoring_or_confidence_intervals": False,
        "formal_validation_completed": False, "no_retry_or_backfill": True,
        "registered_before_actual_driver_start": True,
        "actual_ROOT_execution_registration_time": registration["created_at_utc"],
    })
    p["parallel_tasks_current_finite"]["pilot01_a_sol"] = "once800 first completed/sealed/ROOT received; stopped; no retry"
    p["parallel_tasks_current_finite"]["validation_design_sol"] = "failure attribution complete/ROOT received; only mechanical exception audit preservation patch and finite stub controls running"
    p["current_goal_turn_classification"] = {
        "classification": "progress",
        "actual_actions": [
            "Private frozen-rule800 actual once execution completed;17-member actual seal and original800/4000 order ROOT verified",
            "3987 binary decisions plus3 lawful null retained;2 records/10 technical failure slots preserved without promoting diagnostic zeros",
            "Bounded actual failure attribution completed;12 input SHA/bytes independently verified",
            "Necessary exception-audit preservation patch assigned in a separate version; no semantic routing or rerun authorized",
        ],
        "formal_metrics_accepted": False, "real_human_independent_execution_N": 0,
        "credible_adjudicated_reference_N": 0, "complete_manuscript_started": False,
        "agents_pending_output_N": 1,
        "scope": "Actual machine prediction is distinct from independent human labels and adjudicated reference; all eight steps remain required",
    }
    step5 = next(x for x in p["steps"] if x["step"] == 5)
    step5["status"] = "actual_once800_rule_first_received_partial_predictions_technical_failures_formal_validation_pending"
    for name in ("06-coding/frozen-rule800-candidate-first-sol/actual-seal.json",
                 "logs/root-rule800-actual-first-reception-20261010.json", receipt_name):
        if name not in step5["completed_evidence"]:
            step5["completed_evidence"].append(name)
    step5["remaining"] = [x for x in step5["remaining"] if "实际800 source build" not in x]
    step5["remaining"].append("实际规则800首件已有3987二元+3合法null+10技术失败；未评分、未重跑。真人独立标签及可信裁定参照仍为0；原生800新执行和真实重复稳定性尚未完成。")
    p["full800_actual_preparation"]["separate_rule_machine_first_result"] = "06-coding/frozen-rule800-candidate-first-sol/actual-report.md; A/B blank packets and identity/submission status unchanged"
    p["last_integration_at"] = stamp
    p["status"] = "active"
    write("progress.json", p)

    t = read("task_changes.json")
    change = t["changes"][-1]
    assert change["operation"] == "冻结规则800样本预测的独立先行计算"
    change.update({
        "actual_inference_result": "once800/4000 sealed:3987binary+3lawfulnull+10technical_failure; exit2; no score/retry",
        "actual_result_received_at": stamp,
        "actual_execution_registration_time_from_sealed_registration": registration["created_at_utc"],
        "recorded_ROOT_execution_registration_at_is_progress_log_update_time": True,
        "actual_result_receipt": "logs/root-rule800-actual-first-reception-20261010.json",
        "formal_metrics_accepted": False,
    })
    t["changes"].append({
        "at": stamp, "operation": "实际规则800失败归因及异常审计保存有限修复",
        "reason": "两目标依赖请求未进入维度stop/audit，guard正确阻止未审计0；异常consumption只从普通ValueError取附加字段，丢失当时live view及已生成log/check的留痕",
        "actual_completed": "once800 first and bounded attribution received;12 actual input SHA/byte bindings verified",
        "in_progress": "new version mechanical exception audit preservation only; finite constructed controls",
        "not_authorized": "TOPICS/判据/依赖维语义改动、旧first回填、删除guard、800或4481重跑、参照生成、评分或LLM调用",
        "old_10_technical_failure_and3_lawful_null_preserved": True,
        "final_goal_and_point_criteria_unchanged": True,
        "independence_impact": "private frozen machine output remains hidden from human independent coders; no source case was semantically reviewed or used to tune labels by this attribution",
        "manuscript_impact": "full writing remains after credible-reference comparison and formal acceptance",
        "remaining": "actual human independent firsts, credible adjudicated reference, two-machine validation, stability and later full-paper delivery",
    })
    write("task_changes.json", t)

    goal = ROOT / "完整Goal指令.md"
    with goal.open("a", encoding="utf-8") as stream:
        stream.write("\n\n2026年10月10日完整八步执行调整：第5步的固定800样本规则首件已实际一次运行并封存，800条/4000维中保留3987二元判断、3合法待定与10技术失败（2条记录）；这不是正式指标验收或4481全量重编码。第4步独立真人首判和可信裁定参照仍为0，机器首件继续对人工遮蔽。κ、Precision、Recall、F1、区间及稳健性尚未据该首件计算。两失败仅经机械接口归因：依赖请求未进入维度stop/独立正判audit，现guard正确拒绝候选0；请求的实际必要性和受影响维度未作语义裁定。仅在新目录准备异常日志保全修复，保存当时已有的view、request与uniform log/check，不改判据、不指定受影响维、不删guard、不回填或重跑旧first；原10失败与3待定保留。完成修复后仍按完整八步依赖推进，不能增加零技术错误或区间下限验收门槛，也不能把有限接口控制当作真实800运行通过。用户要求Agent修订盲表作为实际编码结果保留，执行身份如实记AI辅助编码／修订；实际真人事后审阅与真人独立首判分别登记，不将Agent伪记为真人专家。最终全文、0.80项目点标准和先指标合规后写作保持不变。\n")

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    start = text.index("## 当前接收状态")
    end = text.index("## 既有开发接收状态", start)
    current = """## 当前接收状态（2026-10-10，规则800实际首件接收后）

共同手册v1.3F及规则、人类提交、原生LLM接口已冻结。固定800样本的规则程序已实际运行一次：800条、4000维中保留3987二元判断和3合法待定，另有两条记录共10维技术失败；原首件、失败与封存均保留。ROOT核验17成员及原抽样/维度顺序。见[实际规则800报告](./06-coding/frozen-rule800-candidate-first-sol/actual-report.md)。

两条失败源于依赖请求未进入维度审计字段，现守卫正确拒绝未审计的候选0。异常日志保全正在新目录作有限修复；不改判据、不回填旧first、不重跑800，也不追加零技术错误门槛。来源实际必要性和受影响维度尚未判定。

机器预测没有生成真人首判或裁定参照。A/B仍为空白待提交，可信参照为0；该首件没有评分，正式指标尚未验收。800预测由ROOT保留，对独立人工编码方遮蔽；原生LLM800执行与实际稳定性未完成。完整八步Goal保持active，0.80项目点标准保持，完整正文须待指标合规后修订。Agent改表作为实际AI辅助编码／修订结果保留，真人独立首判另列。

"""
    readme.write_text(text[:start] + current + text[end:], encoding="utf-8")
    print(json.dumps({"state": "actual_once800_result_and_review_integrated_patch_pending",
                      "technical_review_inputs_verified_N": len(checked),
                      "backup": str(backup), "formal_acceptance": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()

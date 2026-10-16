"""Summarize the retained first pass. Reads results only; calls no binder/coder."""
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        if isinstance(value, str):
            stream.write(value)
        else:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def run():
    summary = json.loads((HERE / "execution_summary01.json").read_text())
    qa = json.loads((HERE / "disk_QA01.json").read_text())
    process_completion = json.loads((HERE / "process_completion01.json").read_text())
    constructs = json.loads((HERE / "constructed_execution01.json").read_text())
    frozen = json.loads((HERE / "frozen_adapter_identity01.json").read_text())
    gaps, strategies, candidate_only = defaultdict(list), Counter(), Counter()
    with (HERE / "per_leaf_results01.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            result = json.loads(line)
            plan = result.get("plan") or {}
            strategy = plan.get("source_locator_basis", "<no_plan>")
            strategies[strategy] += 1
            axes = (result.get("binding") or {}).get("axes") or {}
            if result["status"] not in {"bound_literal", "bound_native_grid_image_bytes_only"}:
                if axes.get("candidate_position_bound") is True:
                    candidate_only[result["status"]] += 1
                for reason in result["reasons"]:
                    gaps[result["status"] + "::" + reason].append({
                        "occurrence_index_one_based": result["occurrence_index_one_based"],
                        "record_index_one_based": result["record_index_one_based"],
                        "id": result["id"],
                        "raw_pointer": result["raw_pointer"],
                        "text_sha256": result["text_sha256"],
                    })
    gap_index = {
        "schema": "first-real-locator-gap-location-index01-v1",
        "meaning": "Exact occurrence keys only; source/candidate pairs, native locators, binder reasons and tools remain in the referenced immutable per-leaf result. Reason occurrences can overlap.",
        "per_leaf_results_path": str(HERE / "per_leaf_results01.jsonl"),
        "per_leaf_results_sha256": sha(HERE / "per_leaf_results01.jsonl"),
        "by_status_and_reason": dict(gaps),
        "no_raw_policy_text_or_labels": True,
        "formal_model_input_ready": False,
    }
    write_new(HERE / "gap_reason_location_index01.json", gap_index)
    counts = summary["counts"]
    categories = qa["by_material_occurrence_kind"]
    status_order = ["bound_literal", "bound_native_grid_image_bytes_only", "binder_unbound", "adapter_unsupported", "adapter_exception"]
    body = [
        "# 首次真实来源定位接入交付\n",
        f"本轮已对 {summary['distinct_records_processed']:,} 条记录中的 {counts['processed_occurrence_n']:,} 个已声明非空文本发生位置完成一次冻结执行。其中 28,130 项来自既有 leaf 索引，66 项为另存的未投影标量边界。进程实际退出码为 {process_completion['exit_code']}。各项首次结果、未绑定原因和定位信息均已保留；未修改来源、候选、输入、标签或论文。\n",
        "本轮结论是来源定位接口的实际支持范围与缺口盘点，不是编码效度、信度、精确率或召回率检验。正式模型输入就绪状态始终为 false；未调用 LLM 或自动编码规则，未读人工标签。\n",
        "## 实际结果\n",
        "| 状态 | 项数 | 含义 |\n|---|---:|---|",
    ]
    meanings = {
        "bound_literal": "实际候选位置与来源字面/原生 grid 位置通过固定 03 模块绑定；具体表示类型逐项保存。",
        "bound_native_grid_image_bytes_only": "原生表格位置与关联图像字节绑定；图像像素转录未经重新视觉核验。",
        "binder_unbound": "已调用固定 03，但来源字面或其他必要证据未满足。",
        "adapter_unsupported": "未能在本轮声明支持范围内建立无歧义请求，未调用 03。",
        "adapter_exception": "异常原样归入首次结果，未吞掉或重试。",
    }
    for status in status_order:
        body.append(f"| `{status}` | {counts.get(status, 0):,} | {meanings[status]} |")
    body += [
        f"\n固定 03 模块实际调用 {counts.get('binder_call_n', 0):,} 次。不能把 bytes-only 项写成已完成图像转录认证，也不能把未绑定项写成已认证。\n",
        "| 材料类别 | 字面/原生 grid 绑定 | 图像字节表格绑定 | 03 未绑定 | 接口不支持 | 接口异常 |\n|---|---:|---:|---:|---:|---:|",
    ]
    for category, values in categories.items():
        body.append("| " + category + " | " + " | ".join(f"{values.get(k, 0):,}" for k in status_order) + " |")
    body += [
        "\n## 首次未绑定及不支持原因\n",
        "下表按首次结果中的实际原因计数；同一项有多个原因时可重复计入。每项精确记录号、原始 JSON 指针和文本 hash 另存原因定位索引，完整来源对、候选对、候选位置、来源 locator 和工具身份保留在逐项结果。\n",
        "| 状态及原因 | 发生项数 |\n|---|---:|",
    ]
    for reason, n in sorted(summary["reason_counts"].items(), key=lambda item: (-item[1], item[0])):
        body.append(f"| `{reason}` | {n:,} |")
    body += [
        "\n## 支持边界与证据\n",
        "候选定位仅接受唯一的 current 单段 unit、明确 paragraph ID，或候选中唯一的完整段落精确相等关系；错误 ID 不回退，重复出现不按邻近位置猜选。表格只接受实际来源原生 JSON grid 与候选 grid 对应，行列位置逐项保存；确定性的 ` | ` 行表示不冒称自然原句。\n",
        "来源路径与 SHA 必须成对。继承的半对或身份问题保留为不支持；无明确来源位置时，仅由固定 03 自身执行唯一字面匹配。PDF 只传明确单页，不跨页。本轮没有放宽空白、标点或近似匹配；未知结构、多段 current、直接图片及缺少显式格式配置的无后缀来源保留为不支持。\n",
        "前序投影中的 716 项空白/非法内容问题和 341 项未映射嵌套容器问题继续保存在前序 issues01.jsonl；这些是问题发生次数，未被伪造为非空 leaf。66 项非空标量边界全部另列尝试，其结果在上述类别和逐项文件中可追溯。\n",
        f"实现前构造 {constructs['n']} 项，实际通过 {constructs['passed_n']} 项。构造涉及真实临时 TXT 和原生 JSON grid；一项 PDF 单页参数控制仅核定位计划，未宣称临时 PDF 来源认证。\n",
        f"执行后逐项磁盘序列化核对：{'通过' if qa['passed'] else '未通过'}；结果条数 {qa['result_n']:,}，首次失败子集精确一致为 {qa['failed_subset_exact']}，输入 SHA 保持为 {qa['input_hashes_preserved']}，冻结实现保持为 {qa['frozen_implementation_preserved']}。该核对由实施者执行，只验证序列化、身份及保留完整性，不替代独立来源复核。\n",
        "## 交付文件\n",
        "- `per_leaf_results01.jsonl`：全部发生位置的首次完整结果。",
        "- `unsupported_and_failures01.jsonl`：全部首次未绑定、不支持及异常的精确子集。",
        "- `gap_reason_location_index01.json`：按实际原因分组的精确记录号、指针、文本 hash。",
        "- `progress01.jsonl`：100 项及其后每 500 项的实际进度。",
        "- `execution_summary01.json`：一次执行的总计、来源后缀分类和输入 SHA 保持。",
        "- `disk_QA01.json`：实施者磁盘核对及成功来源抽取工具的 SHA 身份。",
        "- `implementation_execution_contract01.json`、`constructed_design01.json`、`constructed_execution01.json`、`frozen_adapter_identity01.json`：先存契约、构造、实际结果及冻结身份。\n",
        "本轮已停改。后续若需适配，应根据首次实际原因另存设计和实现，并保留本轮；不得把失败项过滤后称整体通过。\n",
    ]
    write_new(HERE / "交付报告01.md", "\n".join(body) + "\n")
    artifact_names = [
        "source_locator_adapter01.py", "run_real_locator_pass01.py", "check_adapter_constructs01.py",
        "implementation_execution_contract01.json", "constructed_design01.json", "constructed_execution01.json",
        "frozen_adapter_identity01.json", "per_leaf_results01.jsonl", "unsupported_and_failures01.jsonl",
        "progress01.jsonl", "execution_summary01.json", "process_completion01.json", "check_real_pass_disk01.py", "disk_QA01.json",
        "gap_reason_location_index01.json", "交付报告01.md", "write_delivery_report01.py",
    ]
    manifest = {
        "schema": "first-real-source-locator-delivery01-v1",
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "First real pass retained; implementation stopped; not a formal coding packet.",
        "records": summary["distinct_records_processed"],
        "declared_nonblank_occurrences": counts["processed_occurrence_n"],
        "counts": counts,
        "disk_qa_passed": qa["passed"],
        "process_exit_code": process_completion["exit_code"],
        "reason_counts": summary["reason_counts"],
        "candidate_bound_but_not_source_bound_counts": dict(candidate_only),
        "source_locator_strategy_counts": dict(strategies),
        "frozen_implementation_manifest_sha256": sha(HERE / "frozen_adapter_identity01.json"),
        "files": {name: {"path": str(HERE / name), "sha256": sha(HERE / name)} for name in artifact_names},
        "jsonl_line_counts": {name: sum(1 for _ in (HERE / name).open(encoding="utf-8")) for name in artifact_names if name.endswith(".jsonl")},
        "successful_source_extractor_tool_identities": qa["successful_extractor_tool_identities"],
        "formal_model_input_ready": False,
        "model_or_rule_called": False,
        "gold_labels_read": False,
        "independent_source_review_claim": False,
        "self_hash_embedded": False,
    }
    write_new(HERE / "delivery_manifest01.json", manifest)
    print(json.dumps({"report_sha256": sha(HERE / "交付报告01.md"), "delivery_manifest_sha256": sha(HERE / "delivery_manifest01.json"), "counts": counts, "disk_qa_passed": qa["passed"]}, ensure_ascii=False))


if __name__ == "__main__":
    run()

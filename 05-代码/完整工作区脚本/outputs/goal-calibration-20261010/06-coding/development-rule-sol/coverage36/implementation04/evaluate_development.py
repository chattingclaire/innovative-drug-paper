"""Independent, post-seal comparison with the authorized 41/36-case AI development reference.

This program never imports a coder. A sealed prediction file is immutable input.
The reference is opened only after its run seal and prediction digest are checked.
All records and five decisions per record remain visible, including abstentions.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
from typing import Any


DIMENSIONS = ("S", "E", "Ec", "I", "F")
EXPECTED_RECORDS = None
RUNTIME_VERSION = "development-rule-sol-implementation04"
INFERENCE_FILES = {"runner.py", "source_packet.py", "evidence.py", "relations.py", "dimensions.py"}
REQUIRED_SEAL_FIELDS = {
    "status", "sealed_at_utc", "prediction_path", "prediction_sha256", "prediction_n", "decision_n",
    "runtime_version", "implementation_files", "source_path", "source_sha256", "manual_path",
    "manual_sha256", "fixture_manifest_path", "fixture_manifest_sha256", "freeze_sha256",
    "execution_sha256", "no_reference_read", "complete", "implementation_error_n", "comparison_eligible",
    "technical_diagnostics_path", "technical_diagnostics_sha256", "technical_diagnostics_n",
    "technical_failure_dimension_n",
}
EVALUATION_SCOPE = (
    "AI consensus development comparison; not a human reliability estimate, "
    "not independent final validation, and not final acceptance."
)


class EvaluationError(ValueError):
    """Fail closed on an unsealed, changed, malformed, or incomplete input."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationError(message)


def sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def read_jsonl_bytes(payload: bytes, description: str) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(payload.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        require(isinstance(value, dict), f"{description} line {number} is not an object")
        rows.append(value)
    return rows


def seal_value(seal: dict[str, Any], field: str) -> Any:
    """Support explicit flat bindings or a nested prediction binding."""
    if field in seal:
        return seal[field]
    if field.startswith("prediction_"):
        item = seal.get("prediction") or seal.get("predictions")
        if isinstance(item, dict):
            return item.get(field.removeprefix("prediction_"))
    return None


def valid_digest(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def verify_seal(seal_path: Path, predictions: Path) -> tuple[dict[str, Any], bytes, bytes]:
    require(EXPECTED_RECORDS in {41, 36}, "Evaluator requires an explicitly configured authorized record count")
    require(seal_path.is_file(), "Run seal does not exist; reference access is forbidden")
    seal_bytes = seal_path.read_bytes()
    seal = json.loads(seal_bytes.decode("utf-8"))
    require(isinstance(seal, dict), "Run seal is not an object")
    status = seal.get("status")
    require(status in {"sealed_development_predictions", "sealed_failed_development_attempt"},
            "Run seal status is not a sealed development attempt")
    successful = status == "sealed_development_predictions"
    require(REQUIRED_SEAL_FIELDS.issubset(seal),
            "Run seal lacks mandatory protocol fields: " + ", ".join(sorted(REQUIRED_SEAL_FIELDS - set(seal))))
    require(seal_path.name == "seal.json" and seal_path.parent == predictions.parent,
            "Run seal must be seal.json in the sealed prediction directory")
    require(seal["runtime_version"] == RUNTIME_VERSION, "Run seal runtime version differs from implementation04")
    require(isinstance(seal["sealed_at_utc"], str) and bool(seal["sealed_at_utc"]), "Run seal has no sealing timestamp")
    require(seal["complete"] is successful and seal["comparison_eligible"] is successful,
            "Run seal completeness and metric eligibility disagree with attempt status")
    require(seal["no_reference_read"] is True, "Run seal does not affirm no runtime reference access")
    require(type(seal["implementation_error_n"]) is int
            and (seal["implementation_error_n"] == 0 if successful else seal["implementation_error_n"] > 0),
            "Run seal implementation error count disagrees with attempt status")
    require(type(seal["prediction_n"]) is int and 0 <= seal["prediction_n"] <= EXPECTED_RECORDS,
            "Run seal prediction count exceeds fixed scope")
    require(type(seal["decision_n"]) is int and 0 <= seal["decision_n"] <= EXPECTED_RECORDS * len(DIMENSIONS),
            "Run seal decision count exceeds fixed scope")
    if successful:
        require(seal["prediction_n"] == EXPECTED_RECORDS and seal["decision_n"] == EXPECTED_RECORDS * len(DIMENSIONS),
                "Successful run seal must retain all authorized records and all five decisions each")
    require(type(seal["technical_diagnostics_n"]) is int
            and 0 <= seal["technical_diagnostics_n"] <= EXPECTED_RECORDS * len(DIMENSIONS)
            and type(seal["technical_failure_dimension_n"]) is int
            and 0 <= seal["technical_failure_dimension_n"] <= seal["technical_diagnostics_n"],
            "Technical diagnostic counts are invalid")
    if seal["technical_diagnostics_n"]:
        require(not successful and isinstance(seal["technical_diagnostics_path"], str)
                and Path(seal["technical_diagnostics_path"]).resolve() == seal_path.parent / "technical-diagnostics.jsonl"
                and valid_digest(seal["technical_diagnostics_sha256"]), "Technical diagnostic binding is invalid")
        technical_payload = Path(seal["technical_diagnostics_path"]).read_bytes()
        require(sha_bytes(technical_payload) == seal["technical_diagnostics_sha256"], "Technical diagnostics changed after sealing")
        technical_rows = read_jsonl_bytes(technical_payload, "technical diagnostics")
        require(len(technical_rows) == seal["technical_diagnostics_n"], "Technical diagnostic count differs from seal")
        require(sum(item.get("technical_failure") is True for item in technical_rows) == seal["technical_failure_dimension_n"],
                "Technical failure slot count differs from seal")
        for item in technical_rows:
            require(item.get("dimension") in DIMENSIONS and type(item.get("technical_failure")) is bool
                    and item.get("comparison_eligible") is False,
                    "Technical diagnostic row lacks explicit failed-attempt status")
        require(len({(row_id(item), item["dimension"]) for item in technical_rows}) == len(technical_rows),
                "Duplicate technical diagnostic slot")
    else:
        require(seal["technical_diagnostics_path"] is None and seal["technical_diagnostics_sha256"] is None
                and seal["technical_failure_dimension_n"] == 0, "Empty technical diagnostics have nonempty binding")
    for prefix in ("prediction", "source", "manual", "fixture_manifest"):
        require(isinstance(seal[prefix + "_path"], str) and Path(seal[prefix + "_path"]).is_absolute(),
                f"Run {prefix} binding must be an absolute path")
        require(valid_digest(seal[prefix + "_sha256"]), f"Run {prefix} SHA-256 is invalid")
    files = seal["implementation_files"]
    require(isinstance(files, list) and len(files) == len(INFERENCE_FILES), "Run executable dependency bindings are incomplete")
    require(all(isinstance(item, dict) and isinstance(item.get("path"), str)
                and Path(item["path"]).is_absolute() and valid_digest(item.get("sha256")) for item in files),
            "Run executable dependency binding is invalid")
    require({Path(item["path"]).name for item in files} == INFERENCE_FILES
            and len({str(Path(item["path"]).parent) for item in files}) == 1,
            "Run executable dependency identities differ")
    bound_path = seal_value(seal, "prediction_path")
    bound_sha = seal_value(seal, "prediction_sha256")
    require(isinstance(bound_path, str) and Path(bound_path).resolve() == predictions,
            "Prediction path differs from the sealed run")
    require(predictions.is_file(), "Sealed prediction file does not exist")
    payload = predictions.read_bytes()
    require(sha_bytes(payload) == bound_sha, "Predictions changed after sealing")
    for flag in ("reference_labels_loaded", "reference_loaded"):
        if flag in seal:
            require(seal[flag] is False, "Run seal declares that the runtime loaded reference labels")
    documents = {}
    for name in ("freeze", "execution"):
        require(valid_digest(seal[name + "_sha256"]), f"Run {name} SHA-256 is invalid")
        document_bytes = (seal_path.parent / (name + ".json")).read_bytes()
        require(sha_bytes(document_bytes) == seal[name + "_sha256"], f"Sealed {name} changed")
        documents[name] = json.loads(document_bytes.decode("utf-8"))
        require(isinstance(documents[name], dict), f"Sealed {name} is not an object")
    freeze, execution = documents["freeze"], documents["execution"]
    require(freeze.get("status") == "frozen_before_coder_import_and_inference"
            and freeze.get("expected_n") == EXPECTED_RECORDS
            and freeze.get("reference_input") is None
            and freeze.get("no_legacy_runtime_import") is True,
            "Run freeze does not certify the pre-import fixed scope")
    for field in ("runtime_version", "implementation_files", "source_path", "source_sha256", "manual_path",
                  "manual_sha256", "fixture_manifest_path", "fixture_manifest_sha256"):
        require(freeze.get(field) == seal[field], f"Freeze and seal disagree on {field}")
    require(execution.get("status") == ("completed" if successful else "failed_development_attempt")
            and execution.get("runtime_version") == RUNTIME_VERSION
            and type(execution.get("attempted_record_n")) is int
            and 0 <= execution["attempted_record_n"] <= EXPECTED_RECORDS
            and execution.get("output_record_n") == seal["prediction_n"]
            and isinstance(execution.get("implementation_errors"), list)
            and len(execution["implementation_errors"]) == seal["implementation_error_n"]
            and execution.get("reference_was_input") is False
            and execution.get("comparison_eligible") is successful,
            "Execution does not certify the sealed fixed-scope attempt")
    if successful:
        require(execution["attempted_record_n"] == EXPECTED_RECORDS, "Successful execution does not attempt all records")
    require(not any(Path(p).name == "reference.jsonl" for p in execution.get("read_paths", [])),
            "Execution declares a reference read")
    for field in ("technical_diagnostics_path", "technical_diagnostics_sha256", "technical_diagnostics_n", "technical_failure_dimension_n"):
        require(execution.get(field) == seal[field], f"Execution and seal disagree on {field}")
    for item in files:
        require(sha_file(Path(item["path"])) == item["sha256"], "Frozen inference code changed: " + item["path"])
    require(seal_path.read_bytes() == seal_bytes, "Run seal changed during initial validation")
    return seal, payload, seal_bytes


def fixture_bindings(fixture: Path, seal: dict[str, Any]) -> dict[str, Any]:
    manifest_path = fixture / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("n") == EXPECTED_RECORDS, "Fixture is not the complete authorized development set")
    require(manifest.get("dimension_judgments") == EXPECTED_RECORDS * len(DIMENSIONS),
            "Fixture manifest does not declare all authorized decisions")
    outputs = manifest.get("outputs", [])
    require(isinstance(outputs, list), "Fixture output bindings are absent")
    bindings = {}
    for name in ("source.jsonl", "manual.md", "reference.jsonl"):
        path = (fixture / name).resolve()
        items = [item for item in outputs if isinstance(item, dict)
                 and Path(item.get("path", "")).resolve() == path]
        require(len(items) == 1, f"Fixture manifest does not uniquely bind {name}")
        digest = items[0].get("sha256")
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
                f"Fixture {name} has no valid SHA-256")
        bindings[name] = {"path": path, "sha256": digest}
    for prefix, name in (("source", "source.jsonl"), ("manual", "manual.md")):
        path_key, hash_key = prefix + "_path", prefix + "_sha256"
        require(Path(seal[path_key]).resolve() == bindings[name]["path"],
                f"Run {prefix} path differs from the independent fixture")
        require(seal[hash_key] == bindings[name]["sha256"],
                f"Run {prefix} SHA differs from the independent fixture")
    require(Path(seal["fixture_manifest_path"]).resolve() == manifest_path.resolve(),
            "Run fixture manifest path differs")
    require(seal["fixture_manifest_sha256"] == sha_file(manifest_path), "Run fixture manifest changed")
    bindings["manifest.json"] = {"path": manifest_path.resolve(), "sha256": sha_file(manifest_path)}
    return bindings


def row_id(row: dict[str, Any]) -> str:
    value = row.get("id", row.get("unit_id"))
    require(isinstance(value, str) and bool(value.strip()), "Record identifier is absent")
    return value


def index_rows(rows: list[dict[str, Any]], description: str, *, complete: bool = True) -> dict[str, dict[str, Any]]:
    indexed = {}
    for row in rows:
        identifier = row_id(row)
        require(identifier not in indexed, f"Duplicate {description} identifier: {identifier}")
        indexed[identifier] = row
    require(len(indexed) == EXPECTED_RECORDS if complete else len(indexed) <= EXPECTED_RECORDS,
            f"{description} record count differs from fixed {EXPECTED_RECORDS}-record scope")
    return indexed


def decision_map(row: dict[str, Any]) -> dict[str, Any]:
    """Adapt label/decision shapes at evaluation time without consulting a coder."""
    candidates = [row]
    for key in ("prediction", "reference", "consensus"):
        if isinstance(row.get(key), dict):
            candidates.append(row[key])
    for candidate in candidates:
        for key in ("decisions", "labels", "consensus_labels"):
            value = candidate.get(key)
            if isinstance(value, dict) and set(DIMENSIONS).issubset(value):
                return {dimension: value[dimension] for dimension in DIMENSIONS}
            if isinstance(value, list):
                mapped = {item.get("dimension"): item for item in value if isinstance(item, dict)}
                if set(DIMENSIONS).issubset(mapped):
                    return {dimension: mapped[dimension] for dimension in DIMENSIONS}
        if set(DIMENSIONS).issubset(candidate):
            return {dimension: candidate[dimension] for dimension in DIMENSIONS}
    raise EvaluationError("Unknown decision shape: expected five labels or five dimension decisions")


def label_value(value: Any) -> int | None:
    if isinstance(value, dict):
        for key in ("label", "value", "decision"):
            if key in value:
                value = value[key]
                break
        else:
            raise EvaluationError("Dimension decision has no label/value/decision")
    require(value is None or (type(value) is int and value in (0, 1)),
            f"Invalid binary-or-null decision: {value!r}")
    return value


def explicit_state(value: Any) -> tuple[int | None, str]:
    """Keep explicit NA/unknown separate from absent technical judgments."""
    if isinstance(value, dict):
        for key in ("label", "value", "decision"):
            if key in value:
                value = value[key]
                break
        else:
            raise EvaluationError("Dimension decision has no label/value/decision")
    if isinstance(value, str):
        if value.strip().casefold() in {"na", "n/a", "not_applicable"}:
            return None, "NA"
        if value.strip().casefold() in {"unknown", "undetermined"}:
            return None, "unknown"
    result = label_value(value)
    return result, "unknown" if result is None else "binary"


def extract_reason(row: dict[str, Any], dimension: str, decision: Any) -> Any:
    if "evidence_A" in row or "evidence_B" in row:
        return {name: (row.get(name, {}).get(dimension, {}).get("reason")
                       if isinstance(row.get(name), dict) and isinstance(row[name].get(dimension), dict) else None)
                for name in ("evidence_A", "evidence_B")}
    if isinstance(decision, dict):
        for key in ("reason", "reasons", "rationale"):
            if key in decision:
                return decision[key]
    for candidate in (row, row.get("prediction", {}), row.get("reference", {}), row.get("consensus", {})):
        if not isinstance(candidate, dict):
            continue
        for key in ("reasons", "rationales"):
            if isinstance(candidate.get(key), dict):
                return candidate[key].get(dimension)
    return None


def reference_decision(row: dict[str, Any], dimension: str, decision: Any) -> Any:
    """Keep both AI evidence records under their original A/B labels."""
    if "evidence_A" not in row and "evidence_B" not in row:
        return decision
    return {"value": explicit_state(decision)[0], "label_decision": decision,
            "reference_role": row.get("reference_role"),
            **{name: row.get(name, {}).get(dimension) if isinstance(row.get(name), dict) else None
               for name in ("evidence_A", "evidence_B")}}


def divide(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def binary_metrics(counts: Counter[str], total: int) -> dict[str, Any]:
    tp, fp, fn, tn = (counts[key] for key in ("TP", "FP", "FN", "TN"))
    determined = tp + fp + fn + tn
    precision = divide(tp, tp + fp)
    recall = divide(tp, tp + fn)
    specificity = divide(tn, tn + fp)
    f1 = divide(2 * tp, 2 * tp + fp + fn)
    balanced = (recall + specificity) / 2 if recall is not None and specificity is not None else None
    observed = divide(tp + tn, determined)
    expected = divide((tp + fp) * (tp + fn) + (tn + fn) * (tn + fp), determined * determined)
    kappa = (observed - expected) / (1 - expected) if observed is not None and expected != 1 else None
    return {
        "confusion_determined": {key: counts[key] for key in ("TP", "FP", "FN", "TN")},
        "all_source_denominator": total,
        "determined_denominator": determined,
        "prediction_null_n": counts["prediction_null"],
        "reference_null_n": counts["reference_null"],
        "prediction_unknown_n": counts["prediction_unknown"],
        "reference_unknown_n": counts["reference_unknown"],
        "prediction_NA_n": counts["prediction_NA"],
        "reference_NA_n": counts["reference_NA"],
        "technical_failure_n": counts["technical_failure"],
        "misprediction_n": fp + fn,
        "technical_failure_reference_positive_n": counts["technical_positive"],
        "technical_failure_reference_negative_n": counts["technical_negative"],
        "null_prediction_reference_positive_n": counts["null_positive"],
        "null_prediction_reference_negative_n": counts["null_negative"],
        "null_coverage": divide(total - counts["prediction_null"] - counts["technical_failure"], total),
        "coverage": divide(total - counts["prediction_null"] - counts["technical_failure"] - counts["prediction_NA"], total),
        "prediction_null_rate": divide(counts["prediction_null"], total),
        "paired_determined_coverage": divide(determined, total),
        "precision": precision, "recall": recall, "specificity": specificity,
        "F1": f1, "balanced_accuracy": balanced,
        "determined_accuracy": observed,
        "all_source_correct_rate": divide(tp + tn, total),
        "all_source_unresolved_or_error_n": total - tp - tn,
        "recall_all_reference_positives_with_null_unresolved": divide(tp, tp + fn + counts["null_positive"] + counts["technical_positive"] + counts["NA_positive"]),
        "specificity_all_reference_negatives_with_null_unresolved": divide(tn, tn + fp + counts["null_negative"] + counts["technical_negative"] + counts["NA_negative"]),
        "cohens_kappa": kappa,
        "kappa_identity": "Agreement with AI consensus development labels; not human inter-coder reliability",
        "metric_denominator_note": (
            "TP/FP/FN/TN and conventional precision/recall/specificity/F1/balanced accuracy/kappa use "
            "binary predictions paired with binary references. All-source correctness, errors and "
            "coverage retain every case. Rule null/unknown, explicit NA, and technical failure are distinct "
            "unresolved states; none becomes zero or disappears. Technical failure is never FP/FN. "
            "Metrics from a failed attempt are descriptive diagnostic arithmetic, not valid run metrics. "
            "Undefined denominators, n=0, or kappa expected agreement=1 produce null."
        ),
    }


def count_pair(counts: Counter[str], predicted: int | None, reference: int | None) -> str:
    if predicted is None:
        counts["prediction_null"] += 1
    if reference is None:
        counts["reference_null"] += 1
    if predicted is None or reference is None:
        if predicted is None and reference is not None:
            counts["null_positive" if reference else "null_negative"] += 1
        return "null_unresolved"
    category = { (1, 1): "TP", (1, 0): "FP", (0, 1): "FN", (0, 0): "TN" }[(predicted, reference)]
    counts[category] += 1
    return category


def count_states(counts: Counter[str], predicted: int | None, reference: int | None,
                 prediction_state: str, reference_state: str) -> str:
    if reference_state == "NA":
        counts["reference_NA"] += 1
    elif reference_state == "unknown":
        counts["reference_unknown"] += 1
    if prediction_state == "technical_failure":
        counts["technical_failure"] += 1
        if reference is not None:
            counts["technical_positive" if reference else "technical_negative"] += 1
        if reference_state == "unknown":
            counts["reference_null"] += 1
        return "technical_failure"
    if prediction_state == "NA":
        counts["prediction_NA"] += 1
        if reference is not None:
            counts["NA_positive" if reference else "NA_negative"] += 1
        if reference_state == "unknown":
            counts["reference_null"] += 1
        return "NA_unresolved"
    if prediction_state == "unknown":
        counts["prediction_unknown"] += 1
    if reference_state == "NA":
        if prediction_state == "unknown":
            counts["prediction_null"] += 1
        return "NA_unresolved"
    return count_pair(counts, predicted, reference)


def diagnostic_candidates(dimension: str, source: dict[str, Any], predicted: int | None) -> list[dict[str, str]]:
    """Manual-based review prompts, not automatic replacement labels or tuning."""
    text = source.get("text", "")
    text = text if isinstance(text, str) else ""
    contexts = source.get("contexts", [])
    text += "\n" + "\n".join(item["text"] for item in contexts
                                if isinstance(item, dict) and isinstance(item.get("text"), str))
    candidates = []
    def add(category: str, clause: str, question: str) -> None:
        candidates.append({"category": category, "manual_clause": clause, "review_prompt": question})
    if predicted is None:
        add("MATERIAL_OR_IMPLEMENTATION_ABSTENTION", "§2材料问题与规则争议分开", "核实缺失的是必要来源还是未覆盖语法；保留原未定，不把未知改0。")
    if dimension == "Ec":
        if re.search(r"确认|核验|核对|字段|格式|签章|协议", text):
            add("EC_SUBSTANTIVE_INFORMATION_VS_FORMALITY", "§1资料证据共同门槛；§5经济性边界", "当前核验哪项价格/标准/范围实质内容，还是只处理非空、格式或签约手续？已有信息不因未改变被排除。")
        if re.search(r"支付范围|支付标准|支付责任", text):
            add("EC_CONDITION_AND_PAYMENT_CONSEQUENCE", "§5支付内容的条件与形式操作", "当前与直接父谓词是否组成指定支付内容的授权、限制或条件后果，而非普通目录身份？")
        add("EC_DRUG_TREATMENT_RESOURCE_OBJECT", "§5定义、纳入、排除", "核明费用/资源的药品治疗或支付对象，不借科研、行政、设备费用赋Ec。")
    elif dimension == "F":
        if "公平" in text:
            add("F_GENERAL_EQUITY_EVALUATION", "§7第一类公平评价/信息", "是否当前要求实质公平评价/信息，还是栏目、形式或竞争公平？不补造具体障碍。")
        if re.search(r"价格|自付|承担|支付|负担", text):
            add("F_AFFORDABILITY_VS_FEE_LIABILITY", "§7患者可负担性", "是否表达患者能否负担及支付能力关系，还是只有费用责任、比例或基金承受？")
        if re.search(r"未满足|短缺|尚无|未获批|未上市|优先|申请", text):
            add("F_NEED_GAP_AND_TARGETED_OPPORTUNITY", "§7上游按需机会", "区分无有效选项、境内无对应获批、实际供药不足；缺口是否直接连接按需申请/优先/资源机会？")
        add("F_CONCRETE_EQUITY_VS_GENERAL_ACCESS", "§7具体公平关系及排除", "获取/持续/负担对象与可指认获取差异、按需保障或支付能力是否同时成立？普通渠道、名单、供药或管理便利本身不足。")
    elif dimension == "I":
        add("I_ATTRIBUTE_MODIFICATION_SUPPORT_OR_QUALIFICATION", "§6 I1/I2/I3/I4", "分别核明新颖/实质改良内容、对象—可用研发支持—直接联系或资格—实质待遇；身份/普遍规范不得替代。")
    elif dimension == "S":
        add("S_DRUG_HARM_AND_EVIDENCE_RELATION", "§3安全性", "风险/损害或证据是否属于药物及用药，而非数据、基金、疾病严重程度或一般质量？")
    elif dimension == "E":
        add("E_DRUG_EFFECT_CONTENT_AND_EVIDENCE", "§4有效性", "是否有药物防治效果/健康收益或效果证据，还是用途、行政有效、一般方法或未满足需要？")
    if contexts or re.search(r"下列|以下|第.+条|上述|按照|本办法", text):
        add("LIMITED_CONTEXT_PARENT_OR_REFERENCE_SCOPE", "§2必要语境、记录单元与计数", "实际使用了哪些同版本确指片段？父谓词是否直接承接当前，是否误继承兄弟/全文标签或漏完整标准？")
    if re.search(r"不|未|无|不得|仅|除外|或者|或|如果|符合|终止", text):
        add("NEGATION_CONDITION_OR_BRANCH_SCOPE", "§2否定、条件与例外", "保存完整否定/条件/或分支及后果；议题在场不表示正面属性、现实条件已满足或所有条件失败。")
    return candidates


def json_bytes(value: Any, *, lines: bool = False) -> bytes:
    if lines:
        return ("".join(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n" for item in value)).encode("utf-8")
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def evaluate(fixture: Path, predictions: Path, seal_path: Path, output_dir: Path) -> dict[str, Any]:
    fixture, predictions, seal_path, output_dir = (path.resolve() for path in (fixture, predictions, seal_path, output_dir))
    require(Path(__file__).resolve().parent in output_dir.parents,
            "Evaluation output must remain under the authorized implementation04 artifact directory")
    require(all(output_dir != protected and protected not in output_dir.parents
                for protected in (fixture, predictions.parent, seal_path.parent)),
            "Write evaluation outside the fixture and sealed run directories, including their descendants")
    # This is the reference access gate. Do not move reference reads above it.
    seal, prediction_bytes, seal_bytes = verify_seal(seal_path, predictions)
    successful = seal["status"] == "sealed_development_predictions"
    bindings = fixture_bindings(fixture, seal)
    source_payload = bindings["source.jsonl"]["path"].read_bytes()
    manual_payload = bindings["manual.md"]["path"].read_bytes()
    require(sha_bytes(source_payload) == bindings["source.jsonl"]["sha256"], "Independent source SHA mismatch")
    require(sha_bytes(manual_payload) == bindings["manual.md"]["sha256"], "Independent manual SHA mismatch")
    manual_text = manual_payload.decode("utf-8")
    require(bool(manual_text.strip()), "Independent manual is empty")
    source_rows = read_jsonl_bytes(source_payload, "source")
    sources = index_rows(source_rows, "source")
    prediction_rows = read_jsonl_bytes(prediction_bytes, "prediction")
    predicted = index_rows(prediction_rows, "prediction", complete=successful)
    require(set(predicted).issubset(sources), "Prediction IDs escape the fixed source fixture")
    require(len(predicted) == seal["prediction_n"], "Prediction rows differ from sealed count")
    require(sum(len(row["labels"]) for row in prediction_rows if isinstance(row.get("labels"), dict)) == seal["decision_n"],
            "Prediction label slot count differs from seal")
    execution = json.loads((seal_path.parent / "execution.json").read_bytes())
    global_errors = [item for item in execution["implementation_errors"] if "id" not in item]
    technical = {}
    if seal["technical_diagnostics_n"]:
        technical_rows = read_jsonl_bytes(Path(seal["technical_diagnostics_path"]).read_bytes(), "technical diagnostics")
        technical = {(row_id(item), item["dimension"]): item for item in technical_rows}
        require(all(identifier in sources for identifier, dimension in technical), "Technical diagnostic IDs escape source fixture")
    if successful:
        for prediction in prediction_rows:
            require(prediction.get("implementation_errors") == [], "Successful prediction contains implementation errors")
            pmap = decision_map(prediction)
            require(isinstance(prediction.get("labels"), dict) and set(prediction["labels"]) == set(DIMENSIONS),
                    "Successful prediction has no complete five-label vector")
            require({d: explicit_state(prediction["labels"][d]) for d in DIMENSIONS}
                    == {d: explicit_state(pmap[d]) for d in DIMENSIONS}, "Sealed prediction labels and decisions disagree")
    # Only validated sealed attempts reach this first reference read. A failed
    # attempt remains diagnostic-only; missing decisions below are never labels.
    reference_payload = bindings["reference.jsonl"]["path"].read_bytes()
    require(sha_bytes(reference_payload) == bindings["reference.jsonl"]["sha256"], "Independent reference SHA mismatch")
    references = index_rows(read_jsonl_bytes(reference_payload, "reference"), "reference")
    require(set(sources) == set(references), "Source/reference IDs differ; reference subsets are forbidden")
    per_dimension = {dimension: Counter() for dimension in DIMENSIONS}
    comparison, errors = [], []
    complete_records = exact_records = known_error_records = unresolved_records = technical_records = 0
    source_order = [row_id(row) for row in source_rows]
    for identifier in source_order:
        source, prediction, reference = sources[identifier], predicted.get(identifier), references[identifier]
        rmap = decision_map(reference)
        rstates = {dimension: explicit_state(rmap[dimension]) for dimension in DIMENSIONS}
        record_errors = prediction.get("implementation_errors", []) if prediction is not None else []
        pmap, pshape_error = {}, None
        if prediction is not None and isinstance(prediction.get("decisions"), dict):
            try:
                pmap = decision_map(prediction)
            except EvaluationError as error:
                pshape_error = str(error)
        pstates = {}
        for dimension in DIMENSIONS:
            diagnostic = technical.get((identifier, dimension))
            failed = prediction is None or bool(global_errors or record_errors or pshape_error) or dimension not in pmap
            if diagnostic is not None:
                require(diagnostic["technical_failure"] is failed,
                        "Technical diagnostic state disagrees with sealed prediction/errors")
            if failed:
                pstates[dimension] = (None, "technical_failure")
            else:
                pstates[dimension] = explicit_state(pmap[dimension])
        pvalues = {d: pstates[d][0] for d in DIMENSIONS}
        rvalues = {d: rstates[d][0] for d in DIMENSIONS}
        binary_complete = all(pstates[d][1] == rstates[d][1] == "binary" for d in DIMENSIONS)
        complete_records += int(binary_complete)
        exact_records += int(binary_complete and pvalues == rvalues)
        known_error_records += int(any(pvalues[d] is not None and rvalues[d] is not None and pvalues[d] != rvalues[d] for d in DIMENSIONS))
        unresolved_records += int(not binary_complete)
        technical_records += int(any(pstates[d][1] == "technical_failure" for d in DIMENSIONS))
        for dimension in DIMENSIONS:
            category = count_states(per_dimension[dimension], pvalues[dimension], rvalues[dimension],
                                    pstates[dimension][1], rstates[dimension][1])
            correct = category in {"TP", "TN"}
            row = {
                "id": identifier, "dimension": dimension,
                "source_text": source.get("text", ""),
                "prediction": pvalues[dimension], "reference": rvalues[dimension],
                "prediction_state": pstates[dimension][1], "reference_state": rstates[dimension][1],
                "technical_failure": pstates[dimension][1] == "technical_failure",
                "comparison": category, "correct_binary_pair": correct,
                "prediction_decision": pmap.get(dimension),
                "prediction_reason": extract_reason(prediction or {}, dimension, pmap.get(dimension)),
                "reference_decision": reference_decision(reference, dimension, rmap[dimension]),
                "reference_reason": extract_reason(reference, dimension, rmap[dimension]),
                "reference_record": reference,
                "source_record": source,
                "source_contexts": source.get("contexts", []),
                "source_page_attachments": source.get("source_page_attachments", []),
                "source_image_attachments": source.get("source_image_attachments", []),
                "prediction_record": prediction,
                "prediction_relation_traces": prediction.get("relation_traces", []) if prediction is not None else [],
                "prediction_implementation_errors": record_errors,
                "global_implementation_errors": global_errors,
                "prediction_shape_error": pshape_error,
                "technical_diagnostic": technical.get((identifier, dimension)),
            }
            comparison.append(row)
            if not correct:
                errors.append({**row, "diagnostic_category_candidates": diagnostic_candidates(dimension, source, pvalues[dimension]),
                               "diagnostic_status": "manual_and_source_review_candidates_not_new_adjudication"})
    require(len(comparison) == EXPECTED_RECORDS * len(DIMENSIONS), "Comparison must retain all authorized decisions")
    pooled = Counter()
    for counts in per_dimension.values():
        pooled.update(counts)
    metrics = {
        "scope": EVALUATION_SCOPE, "source_records": EXPECTED_RECORDS, "dimension_decisions": len(comparison),
        "sealed_attempt_status": seal["status"], "comparison_eligible": successful,
        "metrics_valid_for_complete_rule_run": successful,
        "all_records": {
            "n": EXPECTED_RECORDS, "exact_complete_vector_n": exact_records,
            "error_or_unresolved_record_n": EXPECTED_RECORDS - exact_records,
            "known_disagreement_record_n": known_error_records, "unresolved_record_n": unresolved_records,
            "technical_failure_record_n": technical_records,
            "determined_record_denominator": complete_records,
            "exact_complete_vector_rate_all_records": divide(exact_records, EXPECTED_RECORDS),
            "exact_vector_rate_determined": divide(exact_records, complete_records),
            "note": "Known disagreements and unresolved record counts can overlap. Every null remains in all_records.",
        },
        "all_decisions": binary_metrics(pooled, len(comparison)),
        "per_dimension": {dimension: binary_metrics(per_dimension[dimension], EXPECTED_RECORDS) for dimension in DIMENSIONS},
        "no_metric_based_version_selection": True, "human_reliability_claim": False, "final_acceptance": False,
    }
    outputs = {"comparison.jsonl": json_bytes(comparison, lines=True),
               "mispredictions.jsonl": json_bytes([row for row in comparison if row["comparison"] in {"FP", "FN"}], lines=True),
               "unresolved.jsonl": json_bytes([row for row in comparison if row["comparison"] not in {"TP", "FP", "FN", "TN"}], lines=True),
               "errors.jsonl": json_bytes(errors, lines=True), "metrics.json": json_bytes(metrics)}
    require(all(not (output_dir / name).exists() for name in (*outputs, "evaluation-manifest.json")),
            "Evaluation outputs already exist; never overwrite an evaluation")
    require(seal_path.read_bytes() == seal_bytes, "Run seal changed during evaluation")
    require(sha_file(predictions) == seal_value(seal, "prediction_sha256"), "Prediction input changed during evaluation")
    require(all(sha_file(item["path"]) == item["sha256"] for item in bindings.values()), "Fixture input changed during evaluation")
    require(all(sha_file(Path(item["path"])) == item["sha256"] for item in seal["implementation_files"]),
            "Frozen inference code changed during evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in outputs.items():
        with (output_dir / name).open("xb") as handle:
            handle.write(payload)
    require(seal_path.read_bytes() == seal_bytes, "Run seal changed before evaluation completion")
    manifest = {
        "status": "completed_ai_development_comparison_not_final_validation" if successful else "completed_failed_attempt_diagnostic_not_valid_rule_metrics",
        "completed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "scope": EVALUATION_SCOPE,
        "prediction_seal": {"path": str(seal_path), "sha256": sha_bytes(seal_bytes)},
        "prediction": {"path": str(predictions), "sha256": sha_bytes(prediction_bytes), "records": len(predicted)},
        "fixture_inputs": {name: {"path": str(item["path"]), "sha256": item["sha256"]} for name, item in bindings.items()},
        "evaluator": {"path": str(Path(__file__).resolve()), "sha256": sha_file(Path(__file__))},
        "outputs": [{"path": str(output_dir / name), "sha256": sha_bytes(payload)} for name, payload in outputs.items()],
        "reference_read_after_seal_validation": True, "predictions_modified": False,
        "sealed_attempt_status": seal["status"], "comparison_eligible": successful,
        "all_inputs_unchanged": True, "complete_records_retained": EXPECTED_RECORDS,
        "complete_dimension_decisions_retained": len(comparison), "diagnostics_n": len(errors),
        "human_execution_completed": False, "final_acceptance": False,
    }
    with (output_dir / "evaluation-manifest.json").open("xb") as handle:
        handle.write(json_bytes(manifest))
    return metrics


def main() -> None:
    global EXPECTED_RECORDS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expected-n", required=True, type=int, choices=(41, 36))
    args = parser.parse_args()
    EXPECTED_RECORDS = args.expected_n
    try:
        metrics = evaluate(args.fixture, args.predictions, args.seal, args.output_dir)
    except (EvaluationError, OSError, json.JSONDecodeError, UnicodeError) as error:
        parser.exit(2, f"Evaluation refused: {error}\n")
    print(json.dumps({"status": "completed", "scope": EVALUATION_SCOPE, "all_records": metrics["all_records"],
                      "output_dir": str(args.output_dir.resolve())}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
